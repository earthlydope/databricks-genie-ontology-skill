# Changelog

Newest first. Each entry says whether live (real workspace) evidence still applies; the evidence itself is recorded in [appendix G](skills/databricks-genie-ontology/appendix/G-verification-evidence.md).

## 1.1.0 - 2026-11-24
Live evidence: **not re-run**. For all 11 packs the generated SQL, audit queries and agent/page text are byte-identical to 1.0.0 and are now pinned by `tests/golden_sql.json` (a mutation test proves the pin moves when an audit query or doc text changes), and the synthetic data was compared against 1.0.0 once on 2026-11-24 (identical; data is not pinned because random streams can change with numpy versions). The live results for `retail`, `telecom` and `hls_provider` therefore still describe what is generated; only the notebook cell text differs (widget handling, safety gate code).

### Security (found by the second independent code review)
- Spec strings (`derived.expr`, `check`, `checks`, `where`, `template`) are now limited to plain arithmetic and comparisons by a character whitelist plus an AST whitelist, enforced in `validate` and again inside `generate_data`, `sql_constraints` and `deploy`. Before, a crafted spec could run shell commands through pandas `eval` (`@pd...`).
- `deploy()` refuses to overwrite or alter unmarked tables in the `tables`, `load` and `constraints` steps (was `tables` only); `cleanup()` drops a table only if it carries the `genie_onto.managed` marker and reports problems instead of aborting.
- `serve_files.py` rejects symlinks that leave the folder and secret-named files at any depth; `redaction_scan.sh` filters each match instead of each line, so a harmless token can no longer hide a real hit; `.gitignore` ignores `config.env` and `.env` at any depth.
- Validation: join names must be snake_case, `$$` is rejected in join `on` and `table`.

### Review follow-ups (docs review, 2026-11-25)
- `validate` now runs the same strict gate as `check`, `sql` and `deploy` (before, a column-name typo in a `check:` passed `validate` and then raised a misleading "unsafe expression" error); a typo gets one friendly message. A test proves validate and the gate always agree.
- Docs: removed the wildcard-CORS advice (only `serve_files.py` with one allowed origin); no doc inside the skill folder links outside it; the critic checklist now lives only in `templates/critic_prompt.md` (with a retrieval test and `--history` scan); soft build steps (clustering, change data feed, statistics, tags, comments, formats) are documented as WARN-only; the real tag-widget name is documented; new "Quick path" block in `SKILL.md`; paste-size caveat (cells are now about 72-80 KB; `notebook` prints a note above 72,000 characters).
- Known limitations: date-ordering gaps in `retail` and `bfsi_banking` (both Live packs) and a churn gap in `telecom` were reproduced and listed (appendix F), as was the metric-view overwrite gap in `deploy`.
- `redaction_scan.sh`: exact-placeholder allow-list only (an address at a real domain is no longer hidden just because it starts with `you@` or `noreply@`), `--history` scans every commit, GCP hosts and Windows home paths added. `.gitignore`: `STATE.md` at any depth (template stays tracked), `.env.*`, `.databrickscfg`, `out/` at any depth.
- `tools/check_docs.py` now also catches: links leaving the skill folder, duplicate heading slugs, wrong letter case in links and paths, typos in `genie_onto.py` commands and flags inside code blocks, "Live" packs without evidence in appendix G, a version without a row in appendix G, HTML or reference-style links, pack counts written as words, multi-line front matter values; the pack-count rule skips the CHANGELOG.

### Fixes
- Derived columns may depend on other derived columns (dependency order); an empty parent pool for a unique foreign key is an error; `date_key_before` creates the calendar dimension; the domains widget answer is case-insensitive and the notebook text names the right widget.
- Added `genie_onto.py --version`.

### Documentation
- New structure: `SKILL.md` as a router, `INDEX.md` retrieval index (task, symptom, spec key, command, generated catalog), core `references/` (01 to 09), `appendix/` (A to G: public repos, industry guide, glossary, decision log, case study, known limitations, verification evidence), `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`.
- `tools/check_docs.py` and tests enforce links, anchors, front matter, size limits, catalog freshness, and sync with the code (generators, subcommands, pack counts, version).
- Verification claims now live in one place (appendix G and the pack table).

## 1.0.0 - 2026-11-20
First public release: spec-driven builder, 11 industry packs, browser-automation playbook, verification gates. Built live on a real workspace for `retail`, `telecom` and `hls_provider` (0 errors, every audit PASS); `bfsi_banking` and `manufacturing` with an earlier revision.
