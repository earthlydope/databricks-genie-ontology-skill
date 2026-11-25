"""Security and safety regression tests (found by the second independent code review).
Run:  python3 -m unittest discover -s tests -v"""
import copy
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join(ROOT, "skills", "databricks-genie-ontology")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import genie_onto as G  # noqa: E402


def spec(name="retail"):
    return G.load_spec(os.path.join(SKILL, "industries", name + ".yaml"))


def errs(s):
    return G.validate_spec(G.normalize(s))[0]


def first_fact(s):
    return next(t for t, d in s["tables"].items() if d.get("kind") == "fact")


class TestExpressionSafety(unittest.TestCase):
    """Spec strings reach pandas eval/query and DDL: only plain arithmetic/comparisons may pass."""

    EVIL = [
        "a_id > 0 or '\\'' == @pd.io.common.os.system(\"echo RCE > /tmp/pwn\") + '\\''",
        ">= 0 or @df.to_csv(\"/tmp/pwn.csv\") is None",
        "> 0 ) OR (1=1",
        "x.__class__",
        "pd.eval('1')",
        "x[0]",
        "x; DROP TABLE t",
        "x -- comment",
        "open('f')",
    ]

    def test_evil_strings_are_rejected(self):
        for e in self.EVIL:
            self.assertIsNotNone(G.unsafe_expr(e, {"x", "a_id"}), e)
            self.assertIsNotNone(G.unsafe_expr(e, {"x", "a_id", "c"}, sql_prefix="c"), e)

    def test_plain_expressions_pass(self):
        for e in ("(x + 1) * 2 > 3 and x != 0", "abs(x) + 1", "(status == 'Settled') * x"):
            self.assertIsNone(G.unsafe_expr(e, {"x", "status"}), e)
        for e in (">= 0", "> 0", "= price * qty", "<> 0"):
            self.assertIsNone(G.unsafe_expr(e, {"price", "qty", "c"}, sql_prefix="c"), e)

    def test_unknown_name_rejected_when_strict(self):
        self.assertIn("unknown name", G.unsafe_expr("os + 1", {"x"}))

    def _poisoned(self, where, key, value):
        s = spec()
        t = first_fact(s)
        col = next(c for c, d in s["tables"][t]["columns"].items() if d.get("gen") == "derived") if where == "derived" else None
        if where == "check":
            s["tables"][t]["columns"][next(c for c, d in s["tables"][t]["columns"].items() if d.get("type") in ("int", "double"))]["check"] = value
        elif where == "checks":
            s["tables"][t].setdefault("checks", {})["bad"] = value
        elif where == "derived":
            s["tables"][t]["columns"][col]["expr"] = value
        return G.normalize(s)

    def test_validate_flags_poisoned_check_checks_derived(self):
        for where, value in (("check", ">= 0 or @df.to_csv('/tmp/x') is None"),
                             ("checks", "1 = 1) OR (1 = 1"),
                             ("derived", "@pd.io.common.os.system('id')")):
            try:
                s = self._poisoned(where, "x", value)
            except StopIteration:
                continue                                   # pack has no derived column in its first fact
            self.assertTrue(any("unsafe expression" in e for e in G.validate_spec(s)[0]), where)

    def test_generation_and_sql_refuse_unsafe_specs_even_without_validate(self):
        s = self._poisoned("checks", "x", "@pd.io.common.os.system('id') == 0")
        with self.assertRaises(ValueError):
            G.generate_data(s)
        with self.assertRaises(ValueError):
            G.sql_constraints(s)

    def test_template_format_injection_rejected(self):
        s = spec()
        dim = next(t for t, d in s["tables"].items() if d.get("kind") == "dimension" and any(c.get("gen") == "template" for c in d["columns"].values()))
        col = next(c for c, d in s["tables"][dim]["columns"].items() if d.get("gen") == "template")
        s["tables"][dim]["columns"][col]["template"] = "{i.__class__}"
        self.assertTrue(any("template" in e for e in errs(s)))
        self.assertIsNone(G.unsafe_template("SKU-{i:04d}"))
        self.assertIsNone(G.unsafe_template("{{literal}} {i}"))
        self.assertIsNotNone(G.unsafe_template("{0.__class__}"))

    def test_join_name_and_dollar_dollar_validated(self):
        s = spec()
        mv = next(iter(s["metric_views"].values()))
        mv["joins"][0]["name"] = "p: x"
        self.assertTrue(any("snake_case" in e for e in errs(s)))
        s = spec()
        mv = next(iter(s["metric_views"].values()))
        mv["joins"][0]["on"] = mv["joins"][0]["on"] + " OR '$$' = ''"
        self.assertTrue(any("$$" in e for e in errs(s)))


class TestValidateAgreesWithTheGate(unittest.TestCase):
    """validate green must mean generate_data/sql_constraints/deploy will not raise the safety ValueError."""

    CHECKS = [">= 0", ">= nosuchcol", ">= 0 or @x", "> 0 ) OR (1=1", "<> 0", "= 1 ** 2", ">= round(x)", "in (1, 2)"]

    def test_validate_and_gate_agree_for_column_checks(self):
        for chk in self.CHECKS:
            s = spec()
            tab = first_fact(s)
            col = next(c for c, d in s["tables"][tab]["columns"].items() if d.get("type") in ("int", "double") and d.get("gen") != "fk")
            s["tables"][tab]["columns"][col]["check"] = chk
            n = G.normalize(s)
            flagged = any("unsafe" in e or "unknown names" in e for e in G.validate_spec(n)[0])
            try:
                G.assert_safe_spec(n)
                raised = False
            except ValueError:
                raised = True
            self.assertEqual(flagged, raised, f"validate and the gate disagree for check {chk!r}")

    def test_typo_in_a_check_gets_a_friendly_message_once(self):
        s = spec()
        tab = first_fact(s)
        col = next(c for c, d in s["tables"][tab]["columns"].items() if d.get("type") in ("int", "double") and d.get("gen") != "fk")
        s["tables"][tab]["columns"][col]["check"] = ">= nosuchcol"
        msgs = [e for e in G.validate_spec(G.normalize(s))[0] if "nosuchcol" in e]
        self.assertEqual(len(msgs), 1, msgs)


class TestGenerationRobustness(unittest.TestCase):
    def test_derived_columns_may_depend_on_later_derived_columns(self):
        s = {"industry": "t", "seed": 1, "history_days": 30, "domains": [], "tables": {
            "dim_k": {"kind": "dimension", "rows": 5, "comment": "k", "columns": {
                "k_id": {"type": "int", "gen": "seq", "pk": True, "comment": "id"}}},
            "fact_f": {"kind": "fact", "rows": 20, "comment": "f", "columns": {
                "k_id": {"type": "int", "gen": "fk", "fk": "dim_k.k_id", "comment": "k"},
                "z2": {"type": "int", "gen": "derived", "expr": "z1 + 1", "comment": "z2"},
                "z1": {"type": "int", "gen": "derived", "expr": "k_id + 1", "comment": "z1"}}}}}
        data = G.generate_data(G.normalize(s))
        self.assertTrue((data["fact_f"]["z2"] == data["fact_f"]["k_id"] + 2).all())

    def test_empty_unique_fk_pool_is_an_error(self):
        s = {"industry": "t", "seed": 1, "history_days": 30, "domains": [], "tables": {
            "dim_k": {"kind": "dimension", "rows": 5, "comment": "k", "columns": {
                "k_id": {"type": "int", "gen": "seq", "pk": True, "comment": "id"}}},
            "fact_f": {"kind": "fact", "rows": 20, "comment": "f", "columns": {
                "k_id": {"type": "int", "gen": "fk", "fk": "dim_k.k_id", "unique": True, "where": "k_id > 99", "comment": "k"}}}}}
        with self.assertRaises(ValueError):
            G.generate_data(G.normalize(s))

    def test_date_key_before_creates_calendar(self):
        s = spec()
        n = G.normalize({k: v for k, v in s.items()})
        self.assertIn("dim_date", n["tables"])
        only = {"industry": "t", "tables": {"dim_k": {"kind": "dimension", "comment": "k", "columns": {
            "k_id": {"type": "int", "gen": "seq", "pk": True, "comment": "i"}, "cap": {"type": "int", "gen": "uniform", "min": 20250101, "max": 20250110, "comment": "c"}}},
            "fact_f": {"kind": "fact", "comment": "f", "columns": {
                "k_id": {"type": "int", "gen": "fk", "fk": "dim_k.k_id", "comment": "k"},
                "d": {"type": "int", "gen": "date_key_before", "via": "k_id", "column": "cap", "comment": "d"}}}}}
        self.assertIn("dim_date", G.normalize(only)["tables"])


class FakeRows(list):
    def count(self):
        return len(self)

    def collect(self):
        return list(self)


class FakeSpark:
    """Just enough of a SparkSession for deploy()/cleanup() guard tests."""

    def __init__(self, tables, managed):
        self.tables, self.managed, self.stmts = set(tables), set(managed), []
        self.catalog = self

    def tableExists(self, full):
        return full in self.tables

    def sql(self, stmt):
        self.stmts.append(stmt)
        up = stmt.strip()
        if up.startswith("SHOW TBLPROPERTIES"):
            full = up.split()[2]
            return FakeRows([("genie_onto.managed", "true")] if full in self.managed else [("other", "x")])
        if up.startswith("SHOW TABLES"):
            return FakeRows([])
        return FakeRows([])


class TestDestructiveGuards(unittest.TestCase):
    def test_cleanup_keeps_tables_it_did_not_create(self):
        s = spec()
        cat, sch = s["catalog"], s["schema"]
        names = list(s["tables"])
        mine = f"{cat}.{sch}.{names[0]}"
        theirs = f"{cat}.{sch}.{names[1]}"
        sp = FakeSpark(tables={mine, theirs}, managed={mine})
        G.cleanup(sp, G.normalize(s), confirm="DELETE")
        drops = [x for x in sp.stmts if x.startswith("DROP TABLE")]
        self.assertTrue(any(mine in d for d in drops))
        self.assertFalse(any(theirs in d for d in drops), "an unmanaged table must never be dropped")

    def test_cleanup_without_confirmation_drops_nothing(self):
        s = G.normalize(spec())
        sp = FakeSpark(tables=set(), managed=set())
        G.cleanup(sp, s, confirm="yes")
        self.assertEqual([x for x in sp.stmts if x.startswith("DROP")], [])

    def test_deploy_load_and_constraints_steps_also_refuse_unmanaged_tables(self):
        s = G.normalize(spec())
        cat, sch = s["catalog"], s["schema"]
        foreign = f"{cat}.{sch}.{next(iter(s['tables']))}"
        for step in ("tables", "load", "constraints"):
            sp = FakeSpark(tables={foreign}, managed=set())
            with self.assertRaises(RuntimeError, msg=step):
                G.deploy(sp, s, steps=[step])


def _free_port():
    with socket.socket() as k:
        k.bind(("127.0.0.1", 0))
        return k.getsockname()[1]


class TestFileServer(unittest.TestCase):
    script = os.path.join(SKILL, "scripts", "browser", "serve_files.py")

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.srv = os.path.join(self.tmp, "srv")
        os.makedirs(os.path.join(self.srv, "sub"))
        outside = os.path.join(self.tmp, "outside.txt")
        open(outside, "w").write("SECRET")
        open(os.path.join(self.srv, "a.txt"), "w").write("ok")
        os.symlink(outside, os.path.join(self.srv, "link.txt"))
        self.port = _free_port()
        self.proc = subprocess.Popen([sys.executable, self.script, self.srv, str(self.port), "https://example.org"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        line = self.proc.stdout.readline()
        self.token = line.split(f":{self.port}/")[1].split("/")[0]
        time.sleep(0.2)

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait(timeout=5)
        self.proc.stdout.close()
        self.proc.stderr.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def get(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, ""

    def test_serves_allowed_file_with_token(self):
        self.assertEqual(self.get(f"/{self.token}/a.txt"), (200, "ok"))

    def test_refuses_without_token_listing_symlink_and_traversal(self):
        self.assertEqual(self.get("/a.txt")[0], 404)
        self.assertEqual(self.get(f"/{self.token}/")[0], 404)
        self.assertEqual(self.get(f"/{self.token}/link.txt")[0], 404)
        self.assertEqual(self.get(f"/{self.token}/..%2foutside.txt")[0], 404)
        self.assertEqual(self.get(f"/{self.token}/%2e%2e/outside.txt")[0], 404)

    def test_startup_refused_when_secret_named_file_is_nested(self):
        open(os.path.join(self.srv, "sub", "STATE.md"), "w").write("x")
        p = subprocess.run([sys.executable, self.script, self.srv, str(_free_port()), "https://example.org"],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 2)
        self.assertIn("sensitive", p.stderr)


class TestRedactionScan(unittest.TestCase):
    script = os.path.join(SKILL, "scripts", "redaction_scan.sh")

    def scan(self, text, *terms):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "t.md"), "w").write(text)
            p = subprocess.run(["bash", self.script, d, *terms], capture_output=True, text=True)
            return p.returncode, p.stdout

    def test_harmless_token_on_a_line_cannot_hide_a_real_hit(self):
        # fixtures are assembled at runtime so this file itself passes the scan it tests
        email = "real.person" + "@" + "acme-corp.io"
        host = "dbc-1a2b" + "3c4d-5e6f" + ".cloud." + "databricks.com"
        oid = "?o=" + "12345678" + "90123456"
        rc, out = self.scan(f"owner: {email} see <your host>\n")
        self.assertEqual(rc, 1)
        self.assertIn(email, out)
        rc, out = self.scan(f"https://{host}/{oid} example.com\n")
        self.assertEqual(rc, 1)

    def test_placeholders_are_allowed(self):
        rc, _ = self.scan("contact a@example.com or noreply@users.noreply.github.com; host https://<your-workspace-host>\n")
        self.assertEqual(rc, 0)

    def test_extra_terms(self):
        rc, _ = self.scan("the codename is Falcon\n", "falcon")
        self.assertEqual(rc, 1)


class TestGitignoreBehaviour(unittest.TestCase):
    def test_secret_patterns_are_ignored_at_any_depth_but_templates_are_tracked(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(os.path.join(ROOT, ".gitignore"), d)
            subprocess.run(["git", "init", "-q", d], check=True)

            def ignored(path):
                full = os.path.join(d, path)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                open(full, "w").write("x")
                return subprocess.run(["git", "-C", d, "check-ignore", "-q", path]).returncode == 0

            self.assertTrue(ignored("STATE.md"))
            self.assertTrue(ignored("sub/STATE.md"))
            self.assertTrue(ignored("config.env"))
            self.assertTrue(ignored("skills/x/config.env"))
            self.assertTrue(ignored(".env"))
            self.assertTrue(ignored(".env.production"))
            self.assertTrue(ignored(".databrickscfg"))
            self.assertTrue(ignored("proj/out/agent.md"))
            self.assertFalse(ignored("skills/x/templates/STATE.md"))


if __name__ == "__main__":
    unittest.main()
