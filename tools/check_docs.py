#!/usr/bin/env python3
"""Documentation linter for this repository (stdlib only).

    python3 tools/check_docs.py            # exit 1 and print problems
    python3 tools/check_docs.py --write    # also regenerate the catalog block in skills/*/INDEX.md

What it enforces (so another Claude session can trust the docs):
  links       every relative markdown link resolves, including #anchors (GitHub heading slugs)
  paths       every backticked repo path (references/..., scripts/..., tools/...) exists; no bare "`04`" doc numbers
  front       references/, appendix/, INDEX.md, industries/README.md carry title/kind/summary/read_when; kind matches the folder
  names       references are NN-slug.md contiguous from 01; appendix files are L-slug.md contiguous from A
  catalog     the generated catalog in INDEX.md is current
  size        router and docs stay short enough to read in one go
  code-sync   `genie_onto.py <cmd>` mentions use real subcommands; every generator in GENS is documented in the spec format;
              "N packs" claims equal the number of packs; the pack table lists every pack with a valid status;
              CHANGELOG's newest version equals genie_onto.__version__
  stale       names of removed documents do not reappear
  shipping    docs inside the skill folder never link outside it (only the skill folder is installed)
  headings    no duplicate heading slugs in one document (a later insert would silently re-point links)
  case        link and path targets match the real file-name case (macOS is case-insensitive, Linux is not)
  evidence    a pack marked "Live ..." must appear in appendix G; the newest CHANGELOG version must have a row in appendix G
"""
import glob
import importlib.util
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = {"references": "reference", "appendix": "appendix"}
REQUIRED_FM = ("title", "kind", "summary", "read_when")
LIMITS = {"SKILL.md": 110, "INDEX.md": 200, "README.md": 110, "AGENTS.md": 90, "CLAUDE.md": 40, "CONTRIBUTING.md": 110}
DOC_LIMIT = 170
SUBCOMMANDS = {"validate", "check", "sql", "docs", "notebook", "--version"}
FLAGS = {"--cell", "--version"}
STATUSES = ("Live 1.0.0", "Live earlier", "Local only")
STALE = ("10-public-repos-and-docs", "11-industry-guide", "references/10", "references/11")
GENERATED_NAMES = {"agent.md", "ui-checklist.md"}          # files the builder writes into a user's project, not in this repo
PATH_ROOTS = ("references", "appendix", "industries", "templates", "scripts", "tests", "ci", "tools", "skills")
TEMPLATE_INFO = {
    "PROJECT_CLAUDE.md": ("Project instructions to copy next to your spec as CLAUDE.md.", "Phase 0 of the runbook."),
    "STATE.md": ("Progress, ids and definition-of-done checklist to copy as STATE.md (local only, never publish).", "Phase 0 of the runbook; update after every step."),
    "critic_prompt.md": ("Self-contained prompt and checklist for the independent critic.", "Gate 6 of the verification gates, before publishing or handover."),
}
SKIP_PARTS = {".git", "__pycache__", "venv", ".venv", "node_modules"}


# ----------------------------------------------------------------------------- helpers
def slugify(heading):
    h = re.sub(r"`", "", heading).strip().lower()
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")


def exists_exact(path):
    """os.path.exists, but every path component must match the on-disk name case."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return False
    head, tail = os.path.split(path)
    while tail:
        if tail not in os.listdir(head or "."):
            return False
        head, tail = os.path.split(head)
    return True


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def lines_outside_fences(text):
    """Yield (lineno, line) for lines that are not inside a ``` fenced block."""
    fenced = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced:
            yield i, line


def duplicate_headings(text):
    seen, dup = set(), []
    for _, line in lines_outside_fences(text):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slugify(m.group(2))
            if s in seen:
                dup.append(s)
            else:
                seen.add(s)
    return dup


def headings(text):
    seen, out = {}, set()
    for _, line in lines_outside_fences(text):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slugify(m.group(2))
            n = seen.get(s, 0)
            seen[s] = n + 1
            out.add(s if n == 0 else f"{s}-{n}")
    return out


def front_matter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            fm[k.strip()] = v.strip()
    return fm


def all_markdown(repo):
    out = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        out += [os.path.join(root, f) for f in files if f.endswith(".md")]
    return sorted(out)


def skill_dir(repo):
    found = glob.glob(os.path.join(repo, "skills", "*", "SKILL.md"))
    return os.path.dirname(found[0]) if found else None


def load_builder(skill):
    spec = importlib.util.spec_from_file_location("genie_onto_for_docs", os.path.join(skill, "scripts", "genie_onto.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------- catalog
def catalog_rows(skill):
    rows = []
    def add(rel, kind, summary, when):
        esc = lambda s: s.replace("|", "\\|")
        rows.append(f"| [{rel}]({rel}) | {kind} | {esc(summary)} | {esc(when)} |")
    order = ["SKILL.md"] + sorted(os.path.relpath(p, skill) for p in glob.glob(os.path.join(skill, "references", "*.md"))) \
        + sorted(os.path.relpath(p, skill) for p in glob.glob(os.path.join(skill, "appendix", "*.md"))) + ["industries/README.md"]
    for rel in order:
        path = os.path.join(skill, rel)
        if not os.path.exists(path):
            continue
        fm = front_matter(read(path)) or {}
        if rel == "SKILL.md":
            add(rel, "router", "Entry point: decision table, runbook phases, rules.", "Always first.")
        else:
            add(rel, fm.get("kind", "?"), fm.get("summary", ""), fm.get("read_when", ""))
    for path in sorted(glob.glob(os.path.join(skill, "templates", "*.md"))):
        base = os.path.basename(path)
        summary, when = TEMPLATE_INFO.get(base, ("Template to copy into a project.", "When the runbook says so."))
        add(os.path.relpath(path, skill), "template", summary, when)
    return ["| Document | Kind | Summary | Read when |", "|---|---|---|---|"] + rows


def render_catalog_block(skill):
    return "<!-- CATALOG:BEGIN -->\n" + "\n".join(catalog_rows(skill)) + "\n<!-- CATALOG:END -->"


def write_catalog(repo):
    skill = skill_dir(repo)
    path = os.path.join(skill, "INDEX.md")
    text = read(path)
    new = re.sub(r"<!-- CATALOG:BEGIN -->.*?<!-- CATALOG:END -->", lambda m: render_catalog_block(skill), text, flags=re.S)
    if new != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
    return new != text


# ----------------------------------------------------------------------------- the checks
def run(repo=REPO):
    P = []
    skill = skill_dir(repo)
    if not skill:
        return ["skills/*/SKILL.md not found"]
    rel = lambda p: os.path.relpath(p, repo)
    docs = all_markdown(repo)
    texts = {p: read(p) for p in docs}
    head_cache = {p: headings(t) for p, t in texts.items()}
    basenames = {os.path.basename(p) for p in docs} | {os.path.basename(p) for p in glob.glob(os.path.join(repo, "**", "*"), recursive=True)}

    # required root files
    for name in ("README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE"):
        if not os.path.exists(os.path.join(repo, name)):
            P.append(f"{name}: missing")

    # front matter, folders, names, sizes
    for p in docs:
        r = rel(p)
        inside = os.path.relpath(p, skill) if p.startswith(skill + os.sep) else None
        t = texts[p]
        nlines = len(t.splitlines())
        base = os.path.basename(p)
        limit = LIMITS.get(base) if (inside is None or base in ("SKILL.md", "INDEX.md")) else None
        if inside and (inside.startswith("references" + os.sep) or inside.startswith("appendix" + os.sep)):
            limit = DOC_LIMIT
        if limit and nlines > limit:
            P.append(f"{r}: {nlines} lines exceeds the {limit}-line limit; split or move detail to the appendix")
        if not inside:
            continue
        folder = inside.split(os.sep)[0]
        fm = front_matter(t)
        if base == "SKILL.md":
            if not fm or not fm.get("name") or not fm.get("description"):
                P.append(f"{r}: SKILL.md needs front matter with name and description")
            continue
        wants_fm = folder in KINDS or inside in ("INDEX.md", os.path.join("industries", "README.md"))
        if not wants_fm:
            continue
        if fm is None:
            P.append(f"{r}: missing front matter ({', '.join(REQUIRED_FM)})")
            continue
        for k in REQUIRED_FM:
            if not fm.get(k):
                P.append(f"{r}: front matter missing '{k}'")
        expect = KINDS.get(folder) or ("index" if inside == "INDEX.md" else "catalog")
        if fm.get("kind") != expect:
            P.append(f"{r}: kind is '{fm.get('kind')}', expected '{expect}'")
        for k in REQUIRED_FM:
            if fm.get(k, "") in (">", "|", ">-", "|-"):
                P.append(f"{r}: front matter '{k}' must be a single-line value")
        if len(fm.get("summary", "")) > 260:
            P.append(f"{r}: summary longer than 260 characters")

    for folder, pattern, first in (("references", r"^(\d{2})-[a-z0-9-]+\.md$", None), ("appendix", r"^([A-Z])-[a-z0-9-]+\.md$", None)):
        names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(skill, folder, "*.md")))
        keys = []
        for n in names:
            m = re.match(pattern, n)
            if not m:
                P.append(f"{folder}/{n}: file name must match {pattern}")
            else:
                keys.append(m.group(1))
        want = [f"{i:02d}" for i in range(1, len(keys) + 1)] if folder == "references" else [chr(65 + i) for i in range(len(keys))]
        if keys and keys != want:
            P.append(f"{folder}: numbering must be contiguous, found {keys}")

    for p, t in texts.items():
        for s in sorted(set(duplicate_headings(t))):
            P.append(f"{rel(p)}: duplicate heading slug '{s}' (links to it become ambiguous)")
    # fenced blocks: genie_onto subcommands and flags
    for p, t in texts.items():
        fenced = False
        for n, line in enumerate(t.splitlines(), 1):
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
                continue
            if fenced and "genie_onto.py" in line:
                after = line.split("genie_onto.py", 1)[1].split("#", 1)[0].split()
                if after and not after[0].startswith(("<", "$", ".", "\\", "(")):
                    if not all(w in SUBCOMMANDS for w in after[0].split("|")):
                        P.append(f"{rel(p)}:{n}: unknown genie_onto subcommand '{after[0]}' in a code block")
                    for w in after[1:]:
                        if w.startswith("--") and w not in FLAGS:
                            P.append(f"{rel(p)}:{n}: unknown genie_onto flag '{w}' in a code block")
    # links, backticked paths, stale names, commands, bare numbers
    cmd_re = re.compile(r"genie_onto\.py\s+([^\s`]+)")
    link_re = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
    for p, t in texts.items():
        r = rel(p)
        here = os.path.dirname(p)
        for n, line in lines_outside_fences(t):
            if re.search(r"<a\s+href|\]\[[^\]]+\]", line):
                P.append(f"{r}:{n}: use inline markdown links [text](path); HTML and reference-style links are not checked")
            for m in link_re.finditer(line):
                target = m.group(1)
                if re.match(r"^(https?:|mailto:)", target):
                    continue
                path_part, _, frag = target.partition("#")
                dest = p if not path_part else os.path.normpath(os.path.join(here, path_part))
                if not exists_exact(dest):
                    P.append(f"{r}:{n}: broken link (or wrong letter case) -> {target}")
                    continue
                if p.startswith(skill + os.sep) and not (dest == skill or dest.startswith(skill + os.sep)):
                    P.append(f"{r}:{n}: link leaves the skill folder (not shipped when the skill is installed) -> {target}")
                if frag and dest.endswith(".md"):
                    heads = head_cache.get(dest) or headings(read(dest))
                    if frag not in heads:
                        P.append(f"{r}:{n}: anchor '#{frag}' not found in {rel(dest)}")
            for m in re.finditer(r"`([^`\n]+)`", line):
                tok = m.group(1).strip()
                if re.fullmatch(r"\d{2}", tok):
                    P.append(f"{r}:{n}: bare doc number `{tok}`; link the document instead")
                    continue
                tk = tok[len("$SKILL/"):] if tok.startswith("$SKILL/") else tok
                if re.search(r"[<>*{}$]|\.\.|\bNN\b", tk) or " " in tk:
                    continue
                if re.fullmatch(r"(%s)/[A-Za-z0-9_./-]+" % "|".join(PATH_ROOTS), tk):
                    bases = [here, repo, skill, os.path.join(repo, "skills")]
                    if not any(exists_exact(os.path.join(b, tk.rstrip("/"))) for b in bases):
                        P.append(f"{r}:{n}: path `{tok}` does not exist")
                elif re.fullmatch(r"[A-Za-z0-9_.-]+\.md", tk) and tk not in GENERATED_NAMES and tk not in basenames:
                    P.append(f"{r}:{n}: document `{tok}` does not exist")
            for m in cmd_re.finditer(line):
                word = m.group(1)
                if word.startswith(("<", "$", ".", "\\", "(")) or word in ("…", "..."):
                    continue
                if not all(w in SUBCOMMANDS for w in word.split("|")):
                    P.append(f"{r}:{n}: unknown genie_onto subcommand '{word}'")
        for s in STALE:
            if s in t:
                P.append(f"{r}: refers to removed document '{s}'")

    # catalog freshness
    idx = os.path.join(skill, "INDEX.md")
    if os.path.exists(idx):
        m = re.search(r"<!-- CATALOG:BEGIN -->.*?<!-- CATALOG:END -->", texts[idx], re.S)
        if not m:
            P.append("INDEX.md: catalog markers missing")
        elif m.group(0) != render_catalog_block(skill):
            P.append("INDEX.md: catalog is stale; run `python3 tools/check_docs.py --write`")

    # code sync
    try:
        onto = load_builder(skill)
    except Exception as e:  # noqa: BLE001
        return P + [f"cannot import genie_onto.py: {e}"]
    spec_doc = os.path.join(skill, "references", "03-spec-format.md")
    if os.path.exists(spec_doc):
        for g in sorted(onto.GENS):
            if f"`{g}`" not in texts[spec_doc]:
                P.append(f"references/03-spec-format.md: generator `{g}` is not documented")
    packs = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(skill, "industries", "*.yaml")))
    for p, t in texts.items():
        if os.path.basename(p) == "CHANGELOG.md":
            continue                                           # history legitimately mentions older counts
        for n, line in lines_outside_fences(t):
            if re.search(r"\b(eleven|twelve|thirteen|fourteen|fifteen|sixteen|twenty)\s+(?:industry(?:-specific)?\s+)?(?:packs|industries)\b", line, re.I):
                P.append(f"{rel(p)}:{n}: write the pack count as a numeral so it can be checked")
            for m in re.finditer(r"\b(\d+)\s+(?:industry(?:-specific)?\s+)?(?:packs|industries)\b", line):
                if int(m.group(1)) != len(packs):
                    P.append(f"{rel(p)}:{n}: says {m.group(1)} packs but there are {len(packs)}")
    cat = os.path.join(skill, "industries", "README.md")
    if os.path.exists(cat):
        ct = texts[cat]
        for pk in packs:
            row = re.search(r"^\| `%s\.yaml` \| ([^|]+) \|" % re.escape(pk), ct, re.M)
            if not row:
                P.append(f"industries/README.md: pack '{pk}' has no table row")
            elif row.group(1).strip() not in STATUSES:
                P.append(f"industries/README.md: pack '{pk}' status '{row.group(1).strip()}' must be exactly one of {STATUSES}")
            elif row.group(1).strip().startswith("Live"):
                g = os.path.join(skill, "appendix", "G-verification-evidence.md")
                if not os.path.exists(g) or pk not in read(g):
                    P.append(f"industries/README.md: pack '{pk}' is marked Live but appendix G has no evidence for it")
    ver = re.search(r'^__version__\s*=\s*"([^"]+)"', read(os.path.join(skill, "scripts", "genie_onto.py")), re.M)
    chg = os.path.join(repo, "CHANGELOG.md")
    if ver and os.path.exists(chg):
        top = re.search(r"^## \[?(\d+\.\d+\.\d+)", read(chg), re.M)
        if not top or top.group(1) != ver.group(1):
            P.append(f"CHANGELOG.md: newest version '{top.group(1) if top else None}' != genie_onto.__version__ '{ver.group(1)}'")
        g = os.path.join(skill, "appendix", "G-verification-evidence.md")
        if os.path.exists(g) and f"| {ver.group(1)} |" not in read(g):
            P.append(f"appendix/G-verification-evidence.md: no row for builder version {ver.group(1)} (state whether it was verified live)")
    return P


def main(argv):
    if "--write" in argv:
        changed = write_catalog(REPO)
        print("catalog " + ("updated" if changed else "already current"))
    problems = run(REPO)
    for p in problems:
        print("DOC  " + p)
    print(f"{len(problems)} problem(s)" if problems else "docs OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
