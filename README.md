# Databricks Genie Ontology skill

A skill for AI coding agents (built for Claude Code) that builds, verifies and hardens a **governed Genie ontology foundation on Databricks** for any industry:
well-commented Unity Catalog tables with keys, certified **metric views**, business **domains**, definition **Pages**, and a **Genie agent** that answers from them.
It combines a spec-driven builder (everything expressible as SQL is generated and re-runnable) with a battle-tested browser-automation playbook for the parts that exist only in the UI.

It was extracted from a real end-to-end build and then generalized. It ships **11 industry packs** and a verification discipline (audits, `MEASURE()` reconciliation, an independent critic).

> Not affiliated with or endorsed by Databricks. "Genie Ontology" as a *learned* context layer is a gated preview; this repo builds the governed Unity Catalog Business Semantics foundation it depends on (see `references/01-concepts-and-architecture.md`).

## Install as a Claude Code skill

```bash
git clone <this repo> && cd databricks-genie-ontology-skill
mkdir -p ~/.claude/skills && cp -R skills/databricks-genie-ontology ~/.claude/skills/
pip install pandas numpy pyyaml       # for local validate/check/notebook generation
```
Then ask your agent, for example: *"Set up a Genie ontology demo for insurance on my Databricks workspace"* - it will follow `SKILL.md`.
Works for any agent that can read files and drive a browser: start from `skills/databricks-genie-ontology/SKILL.md`.

## What is inside

```
skills/databricks-genie-ontology/
  SKILL.md                      entry point: decision table, runbook, rules
  references/01..11             concepts, runbook, spec format, browser playbook, gotchas, data quality,
                                Genie Code enrichment, safety/privacy, verification + critic, public repos, industry guide
  industries/*.yaml             11 packs: retail, cpg_fmcg, bfsi_banking, bfsi_insurance, hls_provider,
                                hls_pharma_lifesciences, manufacturing, telecom, energy_utilities,
                                supply_chain_logistics, education
  scripts/genie_onto.py         validate | check | sql | docs | notebook  (+ deploy() inside Databricks)
  scripts/browser/              paste_into_monaco.js, read_cell_output.js, coords.js, serve_files.py
  scripts/redaction_scan.sh     pre-publish privacy scan;  scripts/verify_links.py  link/repo checker
  templates/                    spec template, project CLAUDE.md, STATE.md, critic prompt
ci/validate.yml.example         GitHub Actions workflow (copy to .github/workflows/validate.yml to enable CI)
tests/                          43 tests: all packs validate clean, data integrity + realism, SQL rendering,
                                one regression test per defect found, hardened-server and .gitignore checks
```

## 60-second tour

```bash
cd skills/databricks-genie-ontology
python3 scripts/genie_onto.py validate industries/*.yaml            # 11 packs, 0 errors, 0 warnings
python3 scripts/genie_onto.py check industries/manufacturing.yaml   # + synthetic data + integrity checks
# in your own project folder (spec.yaml = an edited copy of a pack; SKILL = this skill's directory):
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell
# paste the cell into a Databricks notebook (scripts/browser/paste_into_monaco.js), run, then:
#   Domains (UI) -> tags -> Genie agent (UI) -> Pages (UI) -> ask the sample questions
python3 -m unittest discover -s ../../tests -v
```

## What was verified (and what was not)

**On a real Databricks workspace** (final builder): the builds for `retail`, `telecom` and `hls_provider` finished with **0 errors and every audit check PASS**
(tables, data, constraints, metric views, tags, apostrophe-safe comments, new generators); `MEASURE()` queries returned the designed numbers; the new `cleanup()` worked.
`bfsi_banking` and `manufacturing` were built live with an earlier builder revision (OEE matched an independent recomputation exactly).
An earlier hand-built retail version of the same idea was exercised through a live Genie agent (measure questions, a derived return rate with disclosure, a Page-backed definition,
cross-view questions, an enriched view, data-quality monitoring enabled).
**Defects found and fixed by testing and by two independent reviewers:** a YAML `on:` key parsed as boolean, a degenerate 0% NPA dataset, chained joins, a `.gitignore` rule that hid a template,
SQL string escaping, unguarded `CREATE OR REPLACE`/`DROP SCHEMA`, unrealistic data in six packs, a too-permissive local file server, widget values leaking between packs, and several overclaims in the docs. Each has a regression test.
**Locally verified for all 11 packs:** validation, deterministic data generation, referential integrity, realism checks, SQL/YAML rendering, notebook compilation.
**Not verified:** the other six packs on a live workspace (cpg_fmcg, bfsi_insurance, hls_pharma_lifesciences, energy_utilities, supply_chain_logistics, education); Genie One (full screen); certification of Pages;
nested (snowflake) metric-view joins; REST/SDK automation (needs a user-created token).
Details: `skills/databricks-genie-ontology/references/09-verification-and-critic.md` and `05-gotchas-and-fixes.md`.

## Safety posture

The skill tells agents to: let the human sign in; never create tokens or change access/security settings (grants, masks, row filters, ABAC, sharing); use synthetic data; confirm destructive actions; redact before publishing.
See `references/08-safety-permissions-privacy.md`.

## Credits and further reading

The overall idea (a retail star schema + metric views + domains + Pages + a Genie agent) was inspired by the community "Northwind Retail" Genie Ontology demo by `databeli`, which publishes no license:
no text or code from it is included - the retail pack, agent wording and Pages here are independently written. Databricks' public semantics/Genie repositories are **linked, not copied** in
`references/10-public-repos-and-docs.md` (every link verified; repos without a license are marked †). Contributions of new industry packs welcome (`references/11-industry-guide.md`, "Adding a new industry").

License: MIT (see `LICENSE`). Third-party repositories keep their own licenses.
