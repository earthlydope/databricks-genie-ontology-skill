# Contributing

Thanks for improving this skill. The fastest useful contributions are new industry packs, realism fixes to existing packs, and gotchas learned on a real workspace.

## Set up
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install pandas numpy pyyaml
python3 -m unittest discover -s tests       # all green before you start
python3 tools/check_docs.py                  # "docs OK"
```

## Add or change an industry pack
1. Copy `skills/databricks-genie-ontology/templates/spec_template.yaml` to `skills/databricks-genie-ontology/industries/<name>.yaml` (snake_case name) and follow the [industry guide](skills/databricks-genie-ontology/appendix/B-industry-guide.md#adding-a-new-industry-30-60-min) and the [spec format](skills/databricks-genie-ontology/references/03-spec-format.md).
2. `genie_onto.py validate` must print 0 errors **and 0 warnings**; `check` must pass. Make ratios non-degenerate (skewed generators, `lookup` + `derived` for consistency).
3. Add a row to the table in `industries/README.md` with status `Local only` (a pack earns `Live` only after a real workspace build, recorded in appendix G).
4. Add the pack to the industry guide appendix. The pack count is stated in several places (README, `SKILL.md` description, `industries/README.md`, decision log, INDEX front matter): run `python3 tools/check_docs.py` and update every place it reports, then `--write`. Past CHANGELOG entries keep their historical counts.
5. Update the pinned SQL digests (`tests/golden_sql.json`) with `python3 tests/update_golden.py` and say why in the pull request.

## Change the builder
- Keep `genie_onto.py` a single file with no Spark import at module level (it is embedded in notebooks). Python 3.9+.
- One regression test per defect, named for the defect. Security-relevant checks go in `tests/test_security.py`.
- If generated SQL changes the golden digests, treat live evidence as stale: re-run at least `retail` on a throwaway schema and record it in appendix G. Otherwise say "not re-run live" in the CHANGELOG.
- Bump `__version__` and add a CHANGELOG entry together (the doc checker compares them).

## Documentation conventions (enforced by `tools/check_docs.py`)
- Files in `references/` are named `NN-slug.md`, are core and short (under 170 lines); files in `appendix/` carry a letter prefix (A, B, C, ...) and are extras. Both need front matter: `title`, `kind`, `summary`, `read_when`.
- Link instead of repeating: verification claims live in appendix G and the pack table only.
- Use inline markdown links with anchors, never bare numbers like "see 04" and never HTML or reference-style links. Anchors follow GitHub's slug rules and the checker verifies them; keep linked headings short and unique in their file, because renaming one breaks links (the checker will say where).
- Docs inside the skill folder must not link outside it: only that folder is installed. Mention repo-root files (CONTRIBUTING.md, CHANGELOG.md) as plain text.
- After adding, moving or retitling a document, run `python3 tools/check_docs.py --write` and commit the refreshed catalog in `INDEX.md`.

## Before opening a pull request
- [ ] tests and `tools/check_docs.py` are green
- [ ] packs validate with 0 errors and 0 warnings
- [ ] redaction scan is clean (`scripts/redaction_scan.sh . <your-private-terms>`)
- [ ] CHANGELOG entry says whether live evidence still applies
- [ ] you did not add real data, credentials, workspace hosts or ids

Security issues (for example a way for a crafted spec to run code): please report them privately to the repository owner rather than in a public issue.
