#!/usr/bin/env python3
"""genie_onto - spec-driven builder for a Databricks Genie ontology foundation.

One YAML/JSON spec (see ../industries/*.yaml) drives:
  validate  - static checks of the spec (no dependencies beyond PyYAML for YAML files)
  check     - validate + generate synthetic data locally + integrity checks (needs pandas, numpy)
  sql       - print every SQL statement the deploy would run (DDL, constraints, metric views, tags)
  docs      - write agent.md, pages/*.md, ui-checklist.md for the UI-only objects
  notebook  - build a ready-to-import Databricks notebook (library + spec + run cells)
  --version - print the builder version

The same file is embedded in the generated notebook, where `deploy(spark, spec)` runs the build.
Pure python: no Spark import at module level, so it runs locally for validation and dry-runs.
"""
import ast
import copy
import datetime as dt
import json
import os
import re
import sys

try:
    import yaml  # optional
except ImportError:  # pragma: no cover
    yaml = None

__version__ = "1.1.0"   # keep in sync with CHANGELOG.md (tools/check_docs.py enforces it)
SIMPLE_TYPES = {"int", "bigint", "string", "date", "boolean", "double", "timestamp"}
GENS = {"seq", "template", "choice", "map", "uniform", "lognormal", "beta", "poisson", "bool", "fk", "date_key",
        "date", "lookup", "date_key_after", "date_key_before", "derived", "calendar"}
CAL_COLS = {
    "date_key": ("int", "Surrogate key, YYYYMMDD integer", True),
    "calendar_date": ("date", "Calendar date", False),
    "year": ("int", "Calendar year", False),
    "quarter": ("int", "Calendar quarter (1-4)", False),
    "month": ("int", "Calendar month number (1-12)", False),
    "month_name": ("string", "Month name, e.g. January", False),
    "day_of_week": ("string", "Day of week name, e.g. Monday", False),
    "is_weekend": ("boolean", "True if the date falls on Saturday or Sunday", False),
}
FORMATS = {
    "currency": "type: currency\n      currency_code: {cur}\n      decimal_places:\n        type: exact\n        places: 2",
    "integer": "type: number\n      decimal_places:\n        type: exact\n        places: 0",
    "decimal": "type: number\n      decimal_places:\n        type: exact\n        places: 2",
    "rate": "type: number\n      decimal_places:\n        type: exact\n        places: 4",
}
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"

# ----------------------------------------------------------------------------- expression safety
# A spec is *code*: `derived.expr`, `check`, `checks` and `where` strings are evaluated locally with pandas and
# `check`/`checks` are also pasted into DDL. Only run specs you trust. On top of that these strings must pass two
# gates: (1) a character whitelist (no `@`, brackets, backslashes, attribute dots, `__`, `;`, comments) and
# (2) an AST whitelist (names, numbers, strings, + - * / %, comparisons, and/or/not, abs()). Names must be columns.
_EXPR_OK = re.compile(r"[A-Za-z0-9_ .+\-*/%()<>=!,]*")
_EXPR_LITERAL = re.compile(r"'[A-Za-z0-9 _.\-]*'|\"[A-Za-z0-9 _.\-]*\"")
_TEMPLATE_FIELD = re.compile(r"\{i(:[0-9]*d)?\}")
_AST_OK = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
           ast.UnaryOp, ast.USub, ast.UAdd, ast.Not, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
           ast.Name, ast.Load, ast.Constant, ast.Call)


def _ast_unsafe(py, names=None):
    try:
        tree = ast.parse(py.strip(), mode="eval")
    except SyntaxError:
        return "is not a valid expression"
    for n in ast.walk(tree):
        if not isinstance(n, _AST_OK):
            return f"{type(n).__name__} is not allowed"
        if isinstance(n, ast.Call) and not (isinstance(n.func, ast.Name) and n.func.id == "abs"
                                            and len(n.args) == 1 and not n.keywords):
            return "only abs(x) may be called"
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float, str, bool)):
            return "unsupported constant"
        if isinstance(n, ast.Name) and names is not None and n.id != "abs" and n.id not in names:
            return f"unknown name '{n.id}'"
    return None


def unsafe_expr(expr, names=None, sql_prefix=None):
    """Return why `expr` is not a plain arithmetic/comparison expression, or None when it is.
    sql_prefix: the column name when `expr` is a column CHECK suffix such as '> 0'; `expr` is then SQL-subset."""
    if not isinstance(expr, str):
        return "must be a string"
    if len(expr) > 300:
        return "longer than 300 characters"
    bare = _EXPR_LITERAL.sub("_", expr)                      # string literals: harmless content only
    if not _EXPR_OK.fullmatch(bare):
        return "contains characters other than letters, digits, spaces, + - * / % ( ) < > = ! , . and simple 'quoted' literals"
    if "__" in bare or "--" in bare:
        return "'__' and '--' are not allowed"
    if re.search(r"[A-Za-z_]\s*\.|\.\s*[A-Za-z_]", bare):
        return "attribute access is not allowed"
    if bare.count("(") != bare.count(")"):
        return "unbalanced parentheses"
    py = expr if sql_prefix is None else _py_check_expr(f"{sql_prefix} {expr}")
    return _ast_unsafe(py, names)


def unsafe_template(tpl):
    """Return why a `gen: template` string is unsafe (only {i} / {i:04d} fields are allowed), or None."""
    if not isinstance(tpl, str):
        return "must be a string"
    rest = tpl.replace("{{", "").replace("}}", "")
    rest = _TEMPLATE_FIELD.sub("", rest)
    return "only {i} or {i:04d} style fields are allowed" if ("{" in rest or "}" in rest) else None


def spec_expression_errors(spec, strict_names=True):
    """All unsafe expression/template strings in a spec, as 'where: reason' strings (empty = clean).
    strict_names=False leaves unknown-name reporting to validate_spec's friendlier messages."""
    out = []
    tables = spec.get("tables") or {}
    for tname, t in tables.items():
        cols = t.get("columns") or {}
        mine = set(cols) if strict_names else None
        for cname, c in cols.items():
            if c.get("gen") == "derived" and (why := unsafe_expr(str(c.get("expr")), mine)):
                out.append(f"{tname}.{cname}.expr: {why}")
            if c.get("check") is not None and (why := unsafe_expr(str(c["check"]), mine, sql_prefix=cname)):
                out.append(f"{tname}.{cname}.check: {why}")
            if c.get("where") is not None:
                ptab = str(c.get("fk", "")).split(".")[0]
                pnames = set((tables.get(ptab, {}).get("columns") or {})) if strict_names else None
                if why := unsafe_expr(str(c["where"]), pnames):
                    out.append(f"{tname}.{cname}.where: {why}")
            if c.get("gen") == "template" and (why := unsafe_template(c.get("template"))):
                out.append(f"{tname}.{cname}.template: {why}")
        for cn, expr in (t.get("checks") or {}).items():
            if why := unsafe_expr(expr, mine, sql_prefix=""):
                out.append(f"{tname}.checks.{cn}: {why}")
    return out


def assert_safe_spec(spec):
    """Raise ValueError if any spec string could do more than arithmetic. Called before any eval or DDL."""
    bad = spec_expression_errors(spec)
    if bad:
        raise ValueError("unsafe expression(s) in spec: " + "; ".join(bad))


# ----------------------------------------------------------------------------- loading
def load_spec(src):
    """Load a spec from a file path or a YAML/JSON string, then normalize it."""
    if os.path.exists(src):
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = src
    stripped = text.lstrip()
    if stripped.startswith("{"):
        raw = json.loads(text)
    else:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML specs (pip install pyyaml) or supply JSON")
        raw = yaml.safe_load(text)
    return normalize(raw)


def normalize(spec):
    """Fill defaults and inject calendar columns. Returns a deep copy."""
    s = copy.deepcopy(spec)
    s.setdefault("schema", "demo")
    s.setdefault("catalog", "genie_ontology_" + re.sub(r"\W+", "_", str(s.get("industry", "demo"))).lower())
    s.setdefault("seed", 42)
    s.setdefault("history_days", 730)
    s.setdefault("currency", "USD")
    s.setdefault("domains", [])
    s.setdefault("metric_views", {})
    s.setdefault("pages", [])
    tables = s.setdefault("tables", {})
    needs_cal = any(c.get("gen") in ("date_key", "date_key_after", "date_key_before") for t in tables.values()
                    for c in (t.get("columns") or {}).values())
    if needs_cal and "dim_date" not in tables:
        tables["dim_date"] = {"kind": "dimension", "generator": "calendar",
                              "comment": "Date dimension, one row per calendar day, shared by all fact tables."}
    for m in s["metric_views"].values():
        for j in m.get("joins", []):
            if True in j:  # YAML 1.1 parses a bare `on:` key as boolean True
                j["on"] = j.pop(True)
    for tname, t in tables.items():
        t.setdefault("kind", "fact" if tname.startswith("fact") else "dimension")
        t.setdefault("rows", 1000 if t["kind"] == "fact" else 100)
        t.setdefault("domains", [])
        if t.get("generator") == "calendar":
            t["columns"] = {c: {"type": ty, "gen": "calendar", "comment": cm, **({"pk": True} if pk else {})}
                            for c, (ty, cm, pk) in CAL_COLS.items()}
        for cname, c in (t.get("columns") or {}).items():
            c.setdefault("nullable", False)
            if c.get("gen") == "date_key" and "fk" not in c:
                c["fk"] = "dim_date.date_key"
            if c.get("gen") == "choice" and "allowed" not in c:
                c["allowed"] = list(c.get("values", []))
            if c.get("gen") == "map" and isinstance(c.get("mapping"), dict):
                c["mapping"] = {str(k): v for k, v in c["mapping"].items()}  # JSON round-trips keys as strings
    return s


# ----------------------------------------------------------------------------- validation
def _col_type_ok(ty):
    return ty in SIMPLE_TYPES or bool(re.fullmatch(r"decimal\(\d+,\s*\d+\)", ty or ""))


def validate_spec(spec):
    """Return (errors, warnings) lists of strings."""
    E, W = [], []
    s = spec
    for k in ("industry", "tables"):
        if not s.get(k):
            E.append(f"missing top-level '{k}'")
    if E:
        return E, W
    tables = s["tables"]
    domains = set(s.get("domains", []))
    gate = []                                          # same strict gate as generate_data/sql_constraints/deploy: validate green == they will not raise
    for m in spec_expression_errors(s, strict_names=True):
        loc = m.split(":")[0]
        key = loc.rsplit(".", 1)[0] if loc.rsplit(".", 1)[-1] in ("expr", "check", "where", "template") else loc
        gate.append((key, m))
    gate_msgs = gate                                   # resolved after the per-column checks below, to avoid double-reporting unknown names
    for ident in ("catalog", "schema"):
        if s.get(ident) is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(s[ident])):
            E.append(f"{ident} '{s[ident]}': letters, digits and underscore only")
    if s.get("as_of") is not None:
        try:
            dt.date.fromisoformat(str(s["as_of"]))
        except ValueError:
            E.append("as_of must be an ISO date (YYYY-MM-DD)")
    for d in domains:
        if not re.fullmatch(r"[A-Za-z0-9 _-]+", d):
            E.append(f"domain '{d}': use only letters, digits, space, _ and - (it becomes a tag key)")
    for tname, t in tables.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", tname):
            E.append(f"table '{tname}': use snake_case")
        if t.get("kind") not in ("dimension", "fact"):
            E.append(f"{tname}: kind must be dimension|fact")
        cols = t.get("columns") or {}
        if not cols:
            E.append(f"{tname}: no columns")
        pks = [c for c, d in cols.items() if d.get("pk")]
        if not pks:
            E.append(f"{tname}: needs at least one pk column")
        for pcn in pks:
            if cols[pcn].get("nullable"):
                E.append(f"{tname}.{pcn}: a primary key column cannot be nullable")
        if not t.get("comment"):
            W.append(f"{tname}: no table comment (Genie reads comments)")
        for dm in t.get("domains", []):
            if dm not in domains:
                E.append(f"{tname}: domain '{dm}' not in top-level domains")
        names = set(cols)
        for cname, c in cols.items():
            where = f"{tname}.{cname}"
            if not re.fullmatch(r"[a-z][a-z0-9_]*", cname):
                E.append(f"{where}: use snake_case")
            if not _col_type_ok(c.get("type")):
                E.append(f"{where}: bad type '{c.get('type')}'")
            g = c.get("gen")
            if g not in GENS:
                E.append(f"{where}: unknown gen '{g}'")
                continue
            if not c.get("comment") and not c.get("hidden"):
                W.append(f"{where}: no column comment")
            req = {"template": ["template"], "choice": ["values"], "map": ["from", "mapping"],
                   "uniform": ["min", "max"], "lognormal": ["mean", "sigma"], "beta": ["a", "b", "min", "max"], "poisson": ["lam"],
                   "fk": ["fk"], "lookup": ["via", "column"], "date_key_after": ["via", "column", "max_days"],
                   "date_key_before": ["via", "column"], "derived": ["expr"]}.get(g, [])
            for r in req:
                if r not in c:
                    E.append(f"{where}: gen '{g}' needs '{r}'")
            if "fk" in c:
                m = re.fullmatch(r"([a-z0-9_]+)\.([a-z0-9_]+)", str(c["fk"]))
                if not m or m.group(1) not in tables or m.group(2) not in (tables[m.group(1)].get("columns") or {}):
                    E.append(f"{where}: fk '{c['fk']}' does not resolve to table.column")
                elif not tables[m.group(1)]["columns"][m.group(2)].get("pk"):
                    E.append(f"{where}: fk target {c['fk']} is not a pk column")
                else:
                    ptab_cols = tables[m.group(1)]["columns"]
                    if sum(1 for d in ptab_cols.values() if d.get("pk")) > 1:
                        E.append(f"{where}: fk target {c['fk']} is part of a composite pk (Unity Catalog FKs must reference the whole pk)")
                    if ptab_cols[m.group(2)].get("type") != c.get("type"):
                        E.append(f"{where}: type {c.get('type')} differs from referenced pk type {ptab_cols[m.group(2)].get('type')}")
                    if c.get("where"):
                        for w in set(re.findall(IDENT, re.sub(r"'[^']*'|\"[^\"]*\"", "", str(c["where"])))):
                            if w not in ptab_cols and w not in ("and", "or", "not", "True", "False"):
                                E.append(f"{where}: where '{c['where']}' uses unknown parent column '{w}'")
            if g in ("lookup", "date_key_after", "date_key_before"):
                via = c.get("via")
                if via not in cols or "fk" not in cols.get(via, {}):
                    E.append(f"{where}: via '{via}' must be an fk column of the same table")
                else:
                    ptab = cols[via]["fk"].split(".")[0]
                    if c.get("column") not in (tables.get(ptab, {}).get("columns") or {}):
                        E.append(f"{where}: column '{c.get('column')}' not in parent {ptab}")
            if g == "derived":
                bare = re.sub(r"'[^']*'|\"[^\"]*\"", "", c.get("expr", ""))   # ignore string literals
                unknown = [w for w in re.findall(IDENT, bare)
                           if w not in names and w not in ("and", "or", "not", "abs", "True", "False")]
                if unknown:
                    E.append(f"{where}: derived expr uses unknown names {sorted(set(unknown))}")
            if c.get("check") is not None and not unsafe_expr(str(c["check"]), None, sql_prefix=cname):
                bare = re.sub(r"'[^']*'", "", str(c["check"]))
                unk = [w for w in re.findall(IDENT, bare) if w.lower() not in ("and", "or", "not", "abs", "true", "false") and w not in names]
                if unk:
                    E.append(f"{where}: check '{c['check']}' uses unknown names {sorted(set(unk))}")
            if g == "map":
                if c.get("from") not in cols:
                    E.append(f"{where}: map.from '{c.get('from')}' is not a column")
                if not all(isinstance(v, list) and v for v in (c.get("mapping") or {}).values()):
                    E.append(f"{where}: every mapping value must be a non-empty list")
            if g == "choice" and c.get("weights") and len(c["weights"]) != len(c["values"]):
                E.append(f"{where}: weights length != values length")
            if c.get("pii") and c.get("type") != "string" and c.get("type") != "date":
                W.append(f"{where}: pii on non-string/date column")
        for cl in t.get("cluster_by", []) or []:
            if cl not in names:
                E.append(f"{tname}: cluster_by '{cl}' unknown column")
        for cn, expr in (t.get("checks") or {}).items():
            if re.search(r"\b(in|between)\b", expr, re.I):
                E.append(f"{tname}.checks.{cn}: IN/BETWEEN are not supported in checks; use column `allowed:` or `check:`")
            for w in re.findall(IDENT, re.sub(r"'[^']*'", "", expr)):
                if w.lower() not in ("and", "or", "not") and w not in names:
                    E.append(f"{tname}.checks.{cn}: unknown name '{w}'")
    for key, m in gate_msgs:
        if "unknown name" in m and any(e.startswith(key + ":") and "unknown" in e for e in E):
            continue                                   # the friendlier message above already covers it
        E.append(f"unsafe expression {m}")
    # metric views
    for mv, m in s.get("metric_views", {}).items():
        if not re.fullmatch(r"mv_[a-z0-9_]+", mv):
            E.append(f"metric view '{mv}': name must start with mv_")
        src = m.get("source")
        if src not in tables:
            E.append(f"{mv}: source '{src}' is not a table")
            continue
        aliases = {"source": src}
        for j in m.get("joins", []):
            if j.get("table") not in tables:
                E.append(f"{mv}: join table '{j.get('table')}' unknown")
            else:
                aliases[j["name"]] = j["table"]
            if not j.get("on"):
                E.append(f"{mv}: join '{j.get('name')}' has no 'on' condition")
            else:
                used = set(re.findall(r"\b([a-z_][a-z0-9_]*)\.[a-z_][a-z0-9_]*\b", j["on"]))
                if used - {"source", j.get("name")}:
                    E.append(f"{mv}: join '{j.get('name')}' is chained ({sorted(used - {'source', j.get('name')})}); "
                             f"flatten the key into the fact table or use a nested join")
            if j.get("name") in ("source",):
                E.append(f"{mv}: join name 'source' is reserved")
            if not re.fullmatch(r"[a-z][a-z0-9_]*", str(j.get("name", ""))):
                E.append(f"{mv}: join name '{j.get('name')}' must be snake_case")
            for key in ("on", "table"):
                if "$$" in str(j.get(key, "")):
                    E.append(f"{mv}: '$$' is not allowed in join {key} (it terminates the SQL body)")
        seen = set()
        for kind in ("dimensions", "measures"):
            for item in m.get(kind, []):
                where = f"{mv}.{item.get('name')}"
                for r in ("name", "expr", "display_name"):
                    if r not in item:
                        E.append(f"{where}: missing '{r}'")
                if "$$" in json.dumps(item):
                    E.append(f"{where}: '$$' is not allowed (it terminates the SQL body)")
                if item.get("name") and not re.fullmatch(r"[a-z][a-z0-9_]*", str(item["name"])):
                    E.append(f"{where}: name must be snake_case")
                if item.get("name") in seen:
                    E.append(f"{where}: duplicate name")
                seen.add(item.get("name"))
                for a, col in re.findall(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", item.get("expr", "")):
                    if a in aliases and col not in tables[aliases[a]]["columns"]:
                        E.append(f"{where}: {a}.{col} is not a column of {aliases[a]}")
                if kind == "measures" and not re.search(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(", item.get("expr", ""), re.I):
                    W.append(f"{where}: measure expr has no aggregate")
                if kind == "measures" and item.get("format") not in (None, *FORMATS):
                    E.append(f"{where}: format must be one of {sorted(FORMATS)}")
                if not item.get("synonyms"):
                    W.append(f"{where}: no synonyms (helps Genie match business language)")
        for dm in m.get("domains", []):
            if dm not in domains:
                E.append(f"{mv}: domain '{dm}' not declared")
        if not m.get("measures"):
            E.append(f"{mv}: no measures")
    # agent + pages
    ag = s.get("agent")
    if ag:
        for src in ag.get("sources", []):
            if src not in s.get("metric_views", {}) and src not in tables:
                E.append(f"agent.sources: '{src}' is neither a metric view nor a table")
        if not ag.get("questions"):
            W.append("agent: no sample questions")
    else:
        W.append("no agent block")
    known = set(s.get("metric_views", {})) | set(tables) | ({ag["name"]} if ag else set())
    for p in s.get("pages", []):
        for k in ("name", "domain", "description", "definition"):
            if not p.get(k):
                E.append(f"page '{p.get('name')}': missing '{k}'")
        if p.get("domain") and p["domain"] not in domains:
            E.append(f"page '{p.get('name')}': domain '{p['domain']}' not declared")
        for r in p.get("related", []):
            if r not in known:
                W.append(f"page '{p.get('name')}': related '{r}' is not a known asset")
    return E, W


# ----------------------------------------------------------------------------- data generation
def _topo(tables):
    deps = {}
    for t, d in tables.items():
        deps[t] = {c["fk"].split(".")[0] for c in d["columns"].values() if "fk" in c} - {t}
    order, done = [], set()
    while len(order) < len(tables):
        ready = [t for t in tables if t not in done and deps[t] <= done]
        if not ready:
            raise ValueError("circular foreign keys: " + ", ".join(sorted(set(tables) - done)))
        for t in ready:
            order.append(t)
            done.add(t)
    return order


def _scale(ty):
    m = re.fullmatch(r"decimal\(\d+,\s*(\d+)\)", ty or "")
    return int(m.group(1)) if m else None


def generate_data(spec, today=None):
    """Generate synthetic data as {table: pandas.DataFrame}. Deterministic for a given seed and date."""
    import numpy as np
    import pandas as pd
    assert_safe_spec(spec)
    s = spec
    rng = np.random.default_rng(int(s["seed"]))
    today = today or (dt.date.fromisoformat(str(s["as_of"])) if s.get("as_of") else dt.date.today())
    start = today - dt.timedelta(days=int(s["history_days"]) - 1)
    out = {}
    for tname in _topo(s["tables"]):
        t = s["tables"][tname]
        cols = t["columns"]
        n = int(t["rows"])
        for c0 in cols.values():                      # `rows` is a cap when a unique fk draws from a smaller pool
            if c0.get("gen") == "fk" and c0.get("unique"):
                p0, k0 = c0["fk"].split(".")
                pool0 = out[p0].query(c0["where"]) if c0.get("where") else out[p0]
                if len(pool0[k0]) == 0:
                    raise ValueError(f"{tname}: unique fk {c0['fk']} has an empty parent pool (check its `where`)")
                n = min(n, len(pool0[k0]))
        df = pd.DataFrame(index=range(n))
        if t.get("generator") == "calendar":
            days = pd.date_range(start, today, freq="D")
            cal = pd.DataFrame({"calendar_date": days})
            df = pd.DataFrame({
                "date_key": cal.calendar_date.dt.strftime("%Y%m%d").astype(int),
                "calendar_date": cal.calendar_date.dt.date,
                "year": cal.calendar_date.dt.year, "quarter": cal.calendar_date.dt.quarter,
                "month": cal.calendar_date.dt.month, "month_name": cal.calendar_date.dt.month_name(),
                "day_of_week": cal.calendar_date.dt.day_name(),
                "is_weekend": cal.calendar_date.dt.dayofweek >= 5})
            out[tname] = df
            continue
        order, pending = [], [c for c, d in cols.items() if d["gen"] != "derived"]
        while pending:                                # generate a column after the columns it depends on (via / from)
            ready = [c for c in pending if all(cols[c].get(k) not in pending for k in ("via", "from"))]
            if not ready:
                raise ValueError(f"{tname}: circular via/from dependency among {pending}")
            order += ready
            pending = [c for c in pending if c not in ready]
        derived = [c for c, d in cols.items() if d["gen"] == "derived"]
        while derived:                                # derived columns may use other derived columns: dependencies first
            ready = [c for c in derived if not (set(re.findall(IDENT, cols[c]["expr"])) & (set(derived) - {c}))]
            if not ready:
                raise ValueError(f"{tname}: circular dependency among derived columns {derived}")
            order += ready
            derived = [c for c in derived if c not in ready]
        for cname in order:
            c = cols[cname]
            g, ty = c["gen"], c["type"]
            sc = _scale(ty)
            if g == "seq":
                v = np.arange(int(c.get("start", 1)), int(c.get("start", 1)) + n)
            elif g == "template":
                v = [c["template"].format(i=i + 1) for i in range(n)]
            elif g == "choice":
                p = c.get("weights")
                p = None if not p else (np.array(p, dtype=float) / float(sum(p)))
                v = rng.choice(np.array(c["values"], dtype=object), size=n, p=p)
            elif g == "map":
                src = df[c["from"]].tolist()
                v = [rng.choice(c["mapping"][str(x)]) if str(x) in c["mapping"] else None for x in src]
            elif g == "uniform":
                if ty in ("int", "bigint"):
                    v = rng.integers(int(c["min"]), int(c["max"]) + 1, size=n)
                else:
                    v = np.round(rng.uniform(float(c["min"]), float(c["max"]), size=n), sc if sc is not None else 2)
            elif g == "lognormal":
                v = rng.lognormal(float(c["mean"]), float(c["sigma"]), size=n)
                v = np.clip(v, c.get("min", 0), c.get("max", np.inf))
                v = np.round(v, sc if sc is not None else 2)
            elif g == "beta":
                v = np.round(float(c["min"]) + (float(c["max"]) - float(c["min"])) * rng.beta(float(c["a"]), float(c["b"]), size=n),
                             sc if sc is not None else 2)
            elif g == "poisson":
                v = np.maximum(rng.poisson(float(c["lam"]), size=n), int(c.get("min", 0)))
            elif g == "bool":
                v = rng.random(n) < float(c.get("p", 0.5))
            elif g == "fk":
                ptab, pcol = c["fk"].split(".")
                pool = (out[ptab].query(c["where"]) if c.get("where") else out[ptab])[pcol].to_numpy()
                if c.get("unique"):
                    v = rng.choice(pool, size=n, replace=False)
                elif c.get("skew"):
                    w = 1.0 / (np.arange(1, len(pool) + 1) ** float(c["skew"]))
                    v = rng.choice(pool, size=n, p=w / w.sum())
                else:
                    v = rng.choice(pool, size=n)
            elif g == "date_key":
                pool = out["dim_date"]["date_key"].to_numpy()
                v = rng.choice(pool, size=n)
            elif g == "date":
                lo = today + dt.timedelta(days=int(c.get("start_offset_days", -(int(s["history_days"]) - 1))))
                hi = today + dt.timedelta(days=int(c.get("end_offset_days", 0)))
                span = (hi - lo).days
                v = [lo + dt.timedelta(days=int(x)) for x in rng.integers(0, span + 1, size=n)]
            elif g in ("lookup", "date_key_after"):
                via = cols[c["via"]]["fk"]
                ptab, pcol = via.split(".")
                parent = out[ptab].set_index(pcol)
                base = parent[c["column"]].reindex(df[c["via"]].to_numpy()).to_numpy()
                if g == "lookup":
                    v = base
                else:
                    d0 = pd.to_datetime(pd.Series(base).astype(str), format="%Y%m%d")
                    add = rng.integers(int(c.get("min_days", 0)), int(c["max_days"]) + 1, size=n)
                    d1 = (d0 + pd.to_timedelta(add, unit="D")).clip(upper=pd.Timestamp(today))
                    v = d1.dt.strftime("%Y%m%d").astype(int).to_numpy()
            elif g == "date_key_before":
                ptab, pcol = cols[c["via"]]["fk"].split(".")
                cap = out[ptab].set_index(pcol)[c["column"]].reindex(df[c["via"]].to_numpy()).to_numpy()
                pool = np.sort(out["dim_date"]["date_key"].to_numpy())
                cnt = np.maximum(np.searchsorted(pool, cap, side="right"), 1)   # calendar days on or before the cap
                v = pool[(rng.random(n) * cnt).astype(int)]
            elif g == "derived":
                v = df.eval(c["expr"], engine="python").to_numpy()
                if sc is not None:
                    v = np.round(v.astype(float), sc)
            else:  # pragma: no cover
                raise ValueError(f"{tname}.{cname}: unsupported gen {g}")
            ser = pd.Series(v)
            if ty in ("int", "bigint"):
                ser = ser.astype("int64")
            elif sc is not None:
                ser = ser.astype(float).round(sc)
            elif ty == "string":
                ser = ser.astype(object)
            df[cname] = ser.to_numpy() if ty != "string" else ser.tolist()
        out[tname] = df
    # drop hidden helper columns
    for tname, df in out.items():
        hidden = [c for c, d in s["tables"][tname]["columns"].items() if d.get("hidden")]
        if hidden:
            out[tname] = df.drop(columns=hidden)
    return out


def _py_check_expr(expr):
    """Translate the SQL check subset to pandas eval. A lone `a = b` becomes a 0.005 tolerance test
    (floats vs exact decimals); the real SQL CHECK stays exact."""
    m = re.fullmatch(r"\s*([^=<>!]+?)\s*=\s*([^=<>!]+?)\s*", expr)
    if m:
        return f"abs(({m.group(1)}) - ({m.group(2)})) < 0.005"
    e = re.sub(r"(?<![<>!=])=(?![=])", "==", expr)
    e = re.sub(r"<>", "!=", e)
    e = re.sub(r"\bAND\b", "and", e, flags=re.I)
    e = re.sub(r"\bOR\b", "or", e, flags=re.I)
    return e


def check_data(spec, data):
    """Integrity checks on generated data. Returns list of failure strings (empty = pass)."""
    fails = []
    for tname, t in spec["tables"].items():
        df = data[tname]
        cols = {c: d for c, d in t["columns"].items() if not d.get("hidden")}
        pks = [c for c, d in cols.items() if d.get("pk")]
        if df.duplicated(subset=pks).any():
            fails.append(f"{tname}: duplicate primary key {pks}")
        for c, d in cols.items():
            if not d.get("nullable") and df[c].isna().any():
                fails.append(f"{tname}.{c}: nulls in NOT NULL column")
            if "fk" in d:
                ptab, pcol = d["fk"].split(".")
                miss = ~df[c].isin(data[ptab][pcol])
                if miss.any():
                    fails.append(f"{tname}.{c}: {int(miss.sum())} orphan fk values -> {d['fk']}")
            if d.get("check"):
                ok = df.eval(f"{c} {d['check']}", engine="python")
                if not ok.all():
                    fails.append(f"{tname}.{c}: {int((~ok).sum())} rows violate '{d['check']}'")
            if d.get("allowed") and d.get("allowed") is not False and not df[c].isin(d["allowed"]).all():
                fails.append(f"{tname}.{c}: values outside allowed list")
            if d.get("type") == "boolean" and df[c].nunique() < 2 and len(df) > 20:
                fails.append(f"{tname}.{c}: boolean column is constant ({df[c].iloc[0]}); every ratio built on it would be 0 or 1")
            if d.get("type") in ("int", "bigint") or _scale(d.get("type")) is not None:
                if len(df) > 20 and df[c].nunique() < 2 and not d.get("pk"):
                    fails.append(f"{tname}.{c}: numeric column is constant ({df[c].iloc[0]})")
        for cn, expr in (t.get("checks") or {}).items():
            ok = df.eval(_py_check_expr(expr), engine="python")
            if not ok.all():
                fails.append(f"{tname}.checks.{cn}: {int((~ok).sum())} rows violate '{expr}'")
    return fails


# ----------------------------------------------------------------------------- SQL rendering
def q(text):
    """Spark SQL string literal: backslash-escape backslashes and quotes; newlines become spaces."""
    t = str(text).replace("\\", "\\\\").replace("'", "\\'").replace("\r", " ").replace("\n", " ")
    return "'" + t + "'"


def fq(spec, name, catalog=None, schema=None):
    return f"{catalog or spec['catalog']}.{schema or spec['schema']}.{name}"


def sql_schema(spec, catalog=None, schema=None):
    cat, sch = catalog or spec["catalog"], schema or spec["schema"]
    return [f"CREATE CATALOG IF NOT EXISTS {cat} COMMENT {q(spec.get('title', spec['industry']) + ' - Genie ontology demo catalog')}",
            f"CREATE SCHEMA IF NOT EXISTS {cat}.{sch} COMMENT {q(spec.get('description', spec.get('title', '')))}"]


def sql_create_table(spec, tname, catalog=None, schema=None):
    t = spec["tables"][tname]
    lines = []
    for c, d in t["columns"].items():
        if d.get("hidden"):
            continue
        nn = "" if d.get("nullable") else " NOT NULL"
        lines.append(f"  {c} {d['type']}{nn} COMMENT {q(d.get('comment', ''))}")
    return (f"CREATE OR REPLACE TABLE {fq(spec, tname, catalog, schema)} (\n" + ",\n".join(lines) +
            f"\n) COMMENT {q(t.get('comment', ''))} TBLPROPERTIES ('{MANAGED_PROP}' = 'true')")


def sql_constraints(spec, catalog=None, schema=None, drop_first=True):
    """PK, FK and CHECK constraints. FK/PK are informational in Unity Catalog; CHECK is enforced."""
    assert_safe_spec(spec)
    pk, fk, ck = [], [], []
    for tname, t in spec["tables"].items():
        full = fq(spec, tname, catalog, schema)
        cols = {c: d for c, d in t["columns"].items() if not d.get("hidden")}
        pcols = [c for c, d in cols.items() if d.get("pk")]
        pk.append(f"ALTER TABLE {full} ADD CONSTRAINT pk_{tname} PRIMARY KEY ({', '.join(pcols)})")
        for c, d in cols.items():
            if "fk" in d:
                ptab, pcol = d["fk"].split(".")
                fk.append(f"ALTER TABLE {full} ADD CONSTRAINT fk_{tname}_{c} FOREIGN KEY ({c}) "
                          f"REFERENCES {fq(spec, ptab, catalog, schema)} ({pcol})")
            if d.get("check"):
                ck.append((full, f"chk_{tname}_{c}", f"{c} {d['check']}"))
            if d.get("allowed") and d["allowed"] is not False and d.get("gen") == "choice":
                vals = ", ".join(q(x) for x in d["allowed"])
                ck.append((full, f"chk_{tname}_{c}_allowed", f"{c} IN ({vals})"))
        for cn, expr in (t.get("checks") or {}).items():
            ck.append((full, f"chk_{tname}_{cn}", expr))
    ck_sql = []
    for full, name, expr in ck:
        if drop_first:
            ck_sql.append(f"ALTER TABLE {full} DROP CONSTRAINT IF EXISTS {name}")
        ck_sql.append(f"ALTER TABLE {full} ADD CONSTRAINT {name} CHECK ({expr})")
    return pk, fk, ck_sql


def sql_drop_fks(spec, catalog=None, schema=None):
    out = []
    for tname, t in spec["tables"].items():
        for c, d in t["columns"].items():
            if "fk" in d:
                out.append(f"ALTER TABLE {fq(spec, tname, catalog, schema)} DROP CONSTRAINT IF EXISTS fk_{tname}_{c}")
    return out


def metric_view_yaml(spec, mv, catalog=None, schema=None, with_format=True):
    m = spec["metric_views"][mv]
    y = ["version: 1.1", f"source: {fq(spec, m['source'], catalog, schema)}"]
    if m.get("joins"):
        y.append("joins:")
        for j in m["joins"]:
            y += [f"  - name: {j['name']}", f"    source: {fq(spec, j['table'], catalog, schema)}", f"    on: {json.dumps(j['on'])}"]
    y.append("dimensions:")
    for d in m.get("dimensions", []):
        y += [f"  - name: {d['name']}", f"    expr: {json.dumps(d['expr'])}", f"    display_name: {json.dumps(d['display_name'])}"]
        if d.get("synonyms"):
            y.append(f"    synonyms: {json.dumps(d['synonyms'])}")
    y.append("measures:")
    for ms in m["measures"]:
        y += [f"  - name: {ms['name']}", f"    expr: {json.dumps(ms['expr'])}", f"    display_name: {json.dumps(ms['display_name'])}"]
        if ms.get("comment"):
            y.append(f"    comment: {json.dumps(ms['comment'])}")
        if ms.get("synonyms"):
            y.append(f"    synonyms: {json.dumps(ms['synonyms'])}")
        if with_format and ms.get("format"):
            y.append("    format:\n      " + FORMATS[ms["format"]].format(cur=spec.get("currency", "USD")))
    return "\n".join(y)


def sql_metric_view(spec, mv, catalog=None, schema=None, with_format=True):
    body = metric_view_yaml(spec, mv, catalog, schema, with_format)
    return (f"CREATE OR REPLACE VIEW {fq(spec, mv, catalog, schema)}\nWITH METRICS\nLANGUAGE YAML\nAS $$\n{body}\n$$")


def sql_metric_view_comment(spec, mv, catalog=None, schema=None):
    m = spec["metric_views"][mv]
    return f"COMMENT ON TABLE {fq(spec, mv, catalog, schema)} IS {q(m.get('comment', ''))}"


def sql_tags(spec, catalog=None, schema=None, domains=False):
    """Certification, governance tags, PII column tags and (optionally) domain tags."""
    out = []
    all_domains = spec.get("domains", [])
    for tname, t in spec["tables"].items():
        full = fq(spec, tname, catalog, schema)
        out.append(f"ALTER TABLE {full} SET TAGS ('table_type' = '{t['kind']}', 'layer' = 'gold', "
                   f"'system.certification_status' = 'certified')")
        for c, d in t["columns"].items():
            if d.get("pii"):
                out.append(f"ALTER TABLE {full} ALTER COLUMN {c} SET TAGS ('pii' = 'true', 'data_classification' = 'personal')")
            elif d.get("classification"):
                out.append(f"ALTER TABLE {full} ALTER COLUMN {c} SET TAGS ('data_classification' = {q(d['classification'])})")
        if domains:
            for dm in all_domains:
                out.append(f"{'SET' if dm in t['domains'] else 'UNSET'} TAG ON TABLE {full} `{dm}`")
    for mv, m in spec["metric_views"].items():
        full = fq(spec, mv, catalog, schema)
        out.append(f"ALTER VIEW {full} SET TAGS ('system.certification_status' = 'certified')")
        if domains:
            for dm in all_domains:
                out.append(f"{'SET' if dm in m.get('domains', []) else 'UNSET'} TAG ON VIEW {full} `{dm}`")
    return out


def sql_features(spec, catalog=None, schema=None):
    out = []
    for tname, t in spec["tables"].items():
        full = fq(spec, tname, catalog, schema)
        if t.get("cluster_by"):
            out.append(f"ALTER TABLE {full} CLUSTER BY ({', '.join(t['cluster_by'])})")
            out.append(f"OPTIMIZE {full}")
        out.append(f"ALTER TABLE {full} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
        out.append(f"ANALYZE TABLE {full} COMPUTE STATISTICS FOR ALL COLUMNS")
    return out


def audit_queries(spec, catalog=None, schema=None):
    """(name, sql) pairs, each returning a count where 0 means pass."""
    qs = []
    for tname, t in spec["tables"].items():
        full = fq(spec, tname, catalog, schema)
        cols = {c: d for c, d in t["columns"].items() if not d.get("hidden")}
        pk = [c for c, d in cols.items() if d.get("pk")]
        if len(pk) == 1:
            dup = f"SELECT COUNT(*) - COUNT(DISTINCT {pk[0]}) FROM {full}"
        else:
            dup = (f"SELECT (SELECT COUNT(*) FROM {full}) - COUNT(*) "
                   f"FROM (SELECT {', '.join(pk)} FROM {full} GROUP BY {', '.join(pk)})")
        qs.append((f"duplicate pk {tname}", dup))
        for c, d in cols.items():
            if "fk" in d:
                ptab, pcol = d["fk"].split(".")
                qs.append((f"orphan {tname}.{c} -> {d['fk']}",
                           f"SELECT COUNT(*) FROM {full} f LEFT ANTI JOIN {fq(spec, ptab, catalog, schema)} p ON f.{c} = p.{pcol}"))
    return qs


# ----------------------------------------------------------------------------- Databricks deploy
MANAGED_PROP = "genie_onto.managed"
DEFAULT_STEPS = ["schema", "tables", "load", "constraints", "metric_views", "features", "tags", "audit"]


def _managed(spark, full):
    """True if the table carries this tool's marker property (so it is safe to CREATE OR REPLACE)."""
    try:
        rows = spark.sql(f"SHOW TBLPROPERTIES {full}").collect()
    except Exception:  # noqa: BLE001
        return False
    return any(r[0] == MANAGED_PROP for r in rows)


def deploy(spark, spec, catalog=None, schema=None, steps=None, with_format=True, domains=False, today=None, force=False):
    """Run the build on Databricks. Prints OK/ERROR per statement. Returns {'errors': [...], 'audit': {...}}.

    steps: subset of DEFAULT_STEPS. Use domains=True (after the Domains exist in the UI) to apply domain tags.
    Re-runs: a full run is idempotent (tables are CREATE OR REPLACE and reloaded). `steps=["tags"]` alone is also safe.
    `constraints` alone is NOT repeatable (PK/FK are added without a drop); it belongs after a fresh `tables`/`load`.
    The build refuses to replace an existing table that lacks the `genie_onto.managed` property (it was not created by this
    tool) unless force=True. Data is generated relative to today unless the spec sets `as_of: YYYY-MM-DD`.
    """
    steps = steps or DEFAULT_STEPS
    assert_safe_spec(spec)
    errors = []
    report = {"errors": errors, "audit": {}}

    def run(stmt, soft=False):
        try:
            spark.sql(stmt)
            print("OK    " + " ".join(stmt.split())[:150])
            return True
        except Exception as e:  # noqa: BLE001
            msg = str(e).replace("\n", " ")[:220]
            print(("WARN  " if soft else "ERROR ") + " ".join(stmt.split())[:110] + " -> " + msg)
            if not soft:
                errors.append((stmt[:110], msg))
            return False

    cat, sch = catalog or spec["catalog"], schema or spec["schema"]
    for ident in (cat, sch):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(ident)):
            raise ValueError(f"unsafe catalog/schema name: {ident!r}")
    order = _topo(spec["tables"])
    if "schema" in steps:
        for st in sql_schema(spec, cat, sch):
            run(st)
        spark.sql(f"USE CATALOG {cat}")
        spark.sql(f"USE SCHEMA {sch}")
    if not force and {"tables", "load", "constraints"} & set(steps):   # every step that overwrites or alters table data/keys
        for t in order:
            full = fq(spec, t, cat, sch)
            if spark.catalog.tableExists(full) and not _managed(spark, full):
                raise RuntimeError(f"{full} already exists and was not created by genie_onto; refusing to replace it "
                                   f"(use a new schema, or deploy(..., force=True) if you really mean it)")
    if "tables" in steps:
        for st in sql_drop_fks(spec, cat, sch):
            tbl = st.split()[2]
            if spark.catalog.tableExists(tbl):  # first run: nothing to drop, stay quiet
                run(st, soft=True)
        for t in order:
            run(sql_create_table(spec, t, cat, sch))
    if "load" in steps:
        from pyspark.sql import functions as F
        data = generate_data(spec, today=today)
        bad = check_data(spec, data)
        if bad:
            raise RuntimeError("generated data failed local checks: " + "; ".join(bad))
        for t in order:
            df = data[t]
            sdf = spark.createDataFrame(df)
            sel = []
            for c, d in spec["tables"][t]["columns"].items():
                if not d.get("hidden"):
                    sel.append(F.col(c).cast(d["type"]).alias(c))
            sdf.select(*sel).write.mode("overwrite").insertInto(fq(spec, t, cat, sch))
            print(f"LOAD  {len(df):>6} rows -> {fq(spec, t, cat, sch)}")
    if "constraints" in steps:
        pk, fk, ck = sql_constraints(spec, cat, sch)
        for st in pk + fk + ck:
            ok = run(st, soft=st.startswith("ALTER TABLE") and "DROP CONSTRAINT" in st)
    if "metric_views" in steps:
        for mv in spec["metric_views"]:
            if not run(sql_metric_view(spec, mv, cat, sch, with_format), soft=with_format):
                if with_format:
                    print("      retrying without format blocks")
                    run(sql_metric_view(spec, mv, cat, sch, False))
            run(sql_metric_view_comment(spec, mv, cat, sch), soft=True)
    if "features" in steps:
        for st in sql_features(spec, cat, sch):
            run(st, soft=True)
    if "tags" in steps:
        for st in sql_tags(spec, cat, sch, domains=domains):
            run(st, soft=True)
    if "audit" in steps:
        for name, st in audit_queries(spec, cat, sch):
            try:
                v = spark.sql(st).first()[0]
            except Exception as e:  # noqa: BLE001
                v = f"ERR {str(e)[:80]}"
            report["audit"][name] = v
            print(f"{'PASS' if v == 0 else 'FAIL'}  {name}: {v}")
    print(f"\nDone. {len(errors)} error(s).")
    return report


def cleanup(spark, spec, confirm, catalog=None, schema=None):
    """Drop ONLY the objects this spec defines (metric views, then tables children-first), then the schema if it is empty.
    Anything else in the schema is left alone. Domains, the Genie agent and Pages are UI objects: delete by hand."""
    if confirm != "DELETE":
        print("Aborted: set confirm='DELETE'. Nothing was dropped.")
        return
    cat, sch = catalog or spec["catalog"], schema or spec["schema"]
    for ident in (cat, sch):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(ident)):
            raise ValueError(f"unsafe catalog/schema name: {ident!r}")
    problems = []
    for mv in spec["metric_views"]:      # views carry no marker: dropped by name, so keep one spec per schema
        try:
            spark.sql(f"DROP VIEW IF EXISTS {fq(spec, mv, cat, sch)}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{mv}: {str(e)[:160]}")
    for t in reversed(_topo(spec["tables"])):
        full = fq(spec, t, cat, sch)
        try:
            if spark.catalog.tableExists(full) and not _managed(spark, full):
                problems.append(f"{t}: kept (it was not created by genie_onto)")
                continue
            spark.sql(f"DROP TABLE IF EXISTS {full}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"{t}: {str(e)[:160]}")
    for p in problems:
        print("WARN  cleanup " + p)
    left = spark.sql(f"SHOW TABLES IN {cat}.{sch}").count()
    if left == 0:
        spark.sql(f"DROP SCHEMA IF EXISTS {cat}.{sch}")
        print("Dropped spec objects and the now-empty schema.")
    else:
        print(f"Dropped spec objects. The schema still holds {left} other object(s) and was kept.")
    print("Remember to delete the Genie agent, Domains and Pages in the UI if no longer wanted.")


# ----------------------------------------------------------------------------- docs rendering
def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def render_docs(spec, outdir):
    os.makedirs(os.path.join(outdir, "pages"), exist_ok=True)
    ag = spec.get("agent") or {}
    files = {}
    if ag:
        qs = "\n".join(f"- {x}" for x in ag.get("questions", []))
        ins = "\n".join(f"- {x}" for x in ag.get("instructions", []))
        files["agent.md"] = (f"# Genie agent: {ag['name']}  (UI-only)\n\n## Name\n{ag['name']}\n\n## Description\n"
                             f"{ag.get('description', '')}\n\n## Data sources (metric views / enriched views, NOT raw tables)\n"
                             f"{', '.join(ag.get('sources', []))}\n\n## Instructions\n{ag.get('instructions_intro', '')}\n\n{ins}\n\n"
                             f"## Sample questions (Configure > About > Common questions)\n{qs}\n\n"
                             f"## After create\nKebab > Assign certification > Certified; add the agent to domain "
                             f"'{ag.get('domain', '')}' (Domain page > kebab > Add to domain).\n")
    for p in spec.get("pages", []):
        files[f"pages/{slug(p['name'])}.md"] = (
            f"# Page: {p['name']}\n\n- Domain: {p['domain']}\n- Synonyms: {', '.join(p.get('synonyms', []))}\n"
            f"- Related assets: {', '.join(p.get('related', []))}\n\n## Description\n{p['description']}\n\n## Body\n"
            f"Definition\n{p['definition']}\n\nBusiness use\n{p.get('business_use', '')}\n")
    dom = "\n".join(f"- [ ] {d}" for d in spec.get("domains", []))
    files["ui-checklist.md"] = (
        f"# UI checklist - {spec.get('title', spec['industry'])}\n\n1. Run the notebook (tables, metric views, certification).\n"
        f"2. Create + publish these Domains (Discover > Create > Create domain; Source = New tag; name must match exactly):\n{dom}\n"
        f"3. Re-run the tagging step with domains=True.\n4. Create the Genie agent from agent.md, attach the sources, certify it, add it to its domain.\n"
        f"5. Create + publish each Page in pages/ (Discover > Create > Create page), link related assets.\n"
        f"6. Ask the sample questions and compare answers with SQL.\n")
    for rel, text in files.items():
        with open(os.path.join(outdir, rel), "w", encoding="utf-8") as fh:
            fh.write(text)
    return sorted(files)


# ----------------------------------------------------------------------------- notebook builder
def build_notebook(spec_path, as_cell=False):
    """Return Databricks notebook source (or one pasteable cell) embedding this library + the spec as JSON."""
    spec = load_spec(spec_path)
    lib = open(__file__, encoding="utf-8").read()
    lib = lib.split('\nif __name__ == "__main__":')[0].rstrip() + "\n"  # never run the CLI inside a notebook
    spec_json = json.dumps(spec, indent=1)
    ind = re.sub(r"\W+", "_", str(spec["industry"])).lower()   # widget names carry the pack name: a notebook reused for another pack cannot inherit stale values
    run = ('import json\nspec = normalize(json.loads(SPEC_JSON))\n'
           f'W_CAT, W_SCH, W_DOM = "catalog_name_{ind}", "schema_name_{ind}", "domains_created_{ind}"\n'
           'dbutils.widgets.text(W_CAT, spec["catalog"], "Catalog")\n'
           'dbutils.widgets.text(W_SCH, spec["schema"], "Schema")\n'
           'dbutils.widgets.text(W_DOM, "no", "Domains created in UI? (yes/no)")\n'
           'domains_done = dbutils.widgets.get(W_DOM).strip().lower() == "yes"\n'
           '# once the Domains exist, only re-apply tags: do NOT rebuild tables/data/views (that would wipe UI edits)\n'
           'report = deploy(spark, spec, catalog=dbutils.widgets.get(W_CAT), schema=dbutils.widgets.get(W_SCH),\n'
           '                steps=["tags"] if domains_done else None, domains=domains_done)\n')
    spec_lit = f"SPEC_JSON = {spec_json!r}\n"   # repr(): safe for any quotes/newlines inside the spec text
    body = f"{lib}\n\n{spec_lit}\n{run}"
    if as_cell:
        return body
    sep = "\n# COMMAND ----------\n\n"
    return ("# Databricks notebook source\n# MAGIC %md\n# MAGIC # " + spec.get("title", spec["industry"]) +
            " - Genie ontology foundation\n# MAGIC Generated by genie_onto.py. Run all. After creating the Domains in the UI, set the "
            "`domains_created_<industry>` widget to `yes` and re-run (that re-run only re-applies tags).\n" + sep + lib + sep + spec_lit + sep + run)


# ----------------------------------------------------------------------------- CLI
def all_sql(spec):
    """Every statement the build runs, in order (the `sql` command, and the golden-digest test that pins generated SQL)."""
    stm = sql_schema(spec) + [sql_create_table(spec, t) for t in _topo(spec["tables"])]
    pk, fk, ck = sql_constraints(spec)
    stm += ["-- (data is loaded by deploy() with generate_data())"] + pk + fk + ck
    for mv in spec["metric_views"]:
        stm += [sql_metric_view(spec, mv), sql_metric_view_comment(spec, mv)]
    return stm + sql_features(spec) + sql_tags(spec, domains=True)


def _cli(argv):
    if len(argv) == 2 and argv[1] == "--version":
        print(__version__)
        return 0
    if len(argv) < 3 or argv[1] not in ("validate", "check", "sql", "docs", "notebook"):
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    rc = 0
    if cmd == "docs":
        spec = load_spec(args[0])
        print("wrote", render_docs(spec, args[1]))
        return 0
    if cmd == "notebook":
        out = args[1]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        as_cell_flag = "--cell" in args
        text = build_notebook(args[0], as_cell=as_cell_flag)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {out} ({len(text)} chars)")
        if as_cell_flag and len(text) > 72000:
            print("note: larger than the 72 KB cell that was pasted successfully in testing; after pasting, read the cell back and compare its length "
                  "(references/04-browser-automation-playbook.md), or import the notebook file instead")
        return 0
    for path in args:
        spec = load_spec(path)
        E, W = validate_spec(spec)
        for w in W:
            print(f"WARN  {os.path.basename(path)}: {w}") if cmd == "validate" else None
        for e in E:
            print(f"ERROR {os.path.basename(path)}: {e}")
        if E:
            rc = 1
            continue
        if cmd == "validate":
            print(f"OK    {os.path.basename(path)}: {len(spec['tables'])} tables, {len(spec['metric_views'])} metric views, "
                  f"{len(spec.get('pages', []))} pages, {len(W)} warning(s)")
        elif cmd == "check":
            data = generate_data(spec)
            bad = check_data(spec, data)
            for b in bad:
                print(f"FAIL  {os.path.basename(path)}: {b}")
            rc |= 1 if bad else 0
            if not bad:
                print(f"OK    {os.path.basename(path)}: data checks pass " + ", ".join(f"{t}={len(d)}" for t, d in data.items()))
        elif cmd == "sql":
            print(";\n".join(all_sql(spec)) + ";")
    return rc


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
