# Databricks Genie Ontology skill

A skill for AI coding agents (built for Claude Code) that builds, verifies and hardens a **governed Genie ontology foundation on Databricks** for any industry:
well-commented Unity Catalog tables with keys, certified **metric views**, business **domains**, definition **Pages**, and a **Genie agent** that answers from them.
A spec-driven builder generates everything expressible as SQL (re-runnable); a battle-tested browser-automation playbook covers the parts that exist only in the UI.
It ships 11 industry packs and a verification discipline (audits, `MEASURE()` reconciliation, an independent critic).

> Not affiliated with or endorsed by Databricks. "Genie Ontology" as a *learned* context layer is a gated preview; this repo builds the governed Unity Catalog Business Semantics foundation it depends on
> ([concepts](skills/databricks-genie-ontology/references/01-concepts-and-architecture.md)).

## Which file do I open?
| You are | Open |
|---|---|
| An AI agent asked to build an ontology | [skills/databricks-genie-ontology/SKILL.md](skills/databricks-genie-ontology/SKILL.md), then find details through [INDEX.md](skills/databricks-genie-ontology/INDEX.md) |
| An AI agent asked to change this repo | [AGENTS.md](AGENTS.md) |
| A human contributor | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Checking what is proven | [verification evidence](skills/databricks-genie-ontology/appendix/G-verification-evidence.md), [pack status](skills/databricks-genie-ontology/industries/README.md) |

## Install as a Claude Code skill
```bash
git clone <this repo> && cd databricks-genie-ontology-skill
mkdir -p ~/.claude/skills && cp -R skills/databricks-genie-ontology ~/.claude/skills/
pip install pandas numpy pyyaml      # for local validate / check / notebook generation
```
Then ask, for example: *"Set up a Genie ontology demo for insurance on my Databricks workspace."* The agent follows `SKILL.md`. Any agent that can read files and drive a browser can start from the same file.

## Repository map
```
skills/databricks-genie-ontology/   the shippable skill (copy this folder)
  SKILL.md        router: decision table, runbook phases, rules
  INDEX.md        retrieval index: task, symptom, spec key, command, generated catalog
  references/     core docs 01-09 (concepts, runbook, spec format, browser playbook, gotchas, data quality,
                  Genie Code enrichment, safety, verification)
  appendix/       extras A-G (public repos, industry guide, glossary, decision log, case study,
                  known limitations, verification evidence)
  industries/     11 packs + status table      scripts/   builder, browser helpers, redaction scan, link checker
  templates/      spec, project CLAUDE.md, STATE.md, critic prompt
tests/            unit, security and documentation tests      tools/check_docs.py   documentation linter
ci/validate.yml.example   GitHub Actions workflow to copy into .github/workflows/
AGENTS.md  CLAUDE.md  CONTRIBUTING.md  CHANGELOG.md  LICENSE
```

## 60-second tour
```bash
cd skills/databricks-genie-ontology
python3 scripts/genie_onto.py validate industries/*.yaml            # every pack: 0 errors, 0 warnings
python3 scripts/genie_onto.py check industries/manufacturing.yaml   # + synthetic data + integrity checks
# in your own project folder (spec.yaml = an edited copy of a pack; SKILL = this skill's directory):
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell
# paste the cell into a Databricks notebook, run, then: Domains (UI) -> tags -> Genie agent (UI) -> Pages (UI) -> sample questions
cd ../.. && python3 -m unittest discover -s tests && python3 tools/check_docs.py
```

## What is verified, and what is not
Short version: builder 1.0.0 was built live on a real Databricks workspace for `retail`, `telecom` and `hls_provider` (0 errors, every audit PASS), and earlier revisions for `bfsi_banking` and `manufacturing`;
all 11 packs pass local validation and data-integrity checks, and realism checks on the ratios they test (known date-ordering gaps in some packs are listed in appendix F). Builder 1.1.0 (security hardening, wider guards, documentation restructure) is covered by tests but **has not been re-run live**.
Never verified: Genie One full screen, certification of Pages, nested metric-view joins, REST/SDK automation. Full record and review history: [appendix G](skills/databricks-genie-ontology/appendix/G-verification-evidence.md); open issues: [appendix F](skills/databricks-genie-ontology/appendix/F-known-limitations.md).

## Safety posture
The skill tells agents to let the human sign in; never create tokens or change access or security settings (grants, masks, row filters, ABAC, sharing); use synthetic data; confirm destructive actions; treat a spec as code; redact before publishing.
Details: [safety](skills/databricks-genie-ontology/references/08-safety-permissions-privacy.md).

## Credits and licence
The overall idea (a retail star schema with metric views, domains, Pages and a Genie agent) was inspired by the community "Northwind Retail" Genie Ontology demo by `databeli`, which publishes no licence: no text or code from it is included, and the retail pack, agent wording and Pages here are independently written.
Databricks' public semantics and Genie repositories are **linked, not copied** in [appendix A](skills/databricks-genie-ontology/appendix/A-public-repos.md). Contributions of new industry packs are welcome ([CONTRIBUTING.md](CONTRIBUTING.md)).
MIT licence, see [LICENSE](LICENSE). Third-party repositories keep their own licences.
