---
title: Index
kind: index
summary: Retrieval index for the whole skill - which document answers which task, symptom, spec key or command, plus a generated catalog of every document.
read_when: You know what you need but not where it is. Open this after SKILL.md, find the row, follow one link.
---
# Index

Read order for a new session: [SKILL.md](SKILL.md) (the router) then the one row below that matches your task. Do not read the references front to back.
Layout: `references/` = core (read as needed), `appendix/` = extras (never required to build), `industries/` = packs, `scripts/` = tools, `templates/` = files to copy into a project.

## 1. Task to document
| I need to | Read | Then |
|---|---|---|
| Build an ontology for an industry | [SKILL.md](SKILL.md#1-decide-the-path), [pack table](industries/README.md) | [runbook](references/02-runbook.md#phase-0-project-folder) |
| Resume a half-finished build | the project's `STATE.md` | the [runbook](references/02-runbook.md) phase after the last one done |
| Write or change a spec | [spec format](references/03-spec-format.md) | `templates/spec_template.yaml`, then `validate` and `check` |
| Add a new industry pack | [industry guide](appendix/B-industry-guide.md#adding-a-new-industry-30-60-min) | [spec format checklist](references/03-spec-format.md#authoring-checklist), CONTRIBUTING.md in the repository root (not part of the installed skill) |
| Create Domains, the agent or Pages (UI) | runbook phases [5](references/02-runbook.md#phase-5-domains), [7](references/02-runbook.md#phase-7-genie-agent), [8](references/02-runbook.md#phase-8-pages) | [browser playbook](references/04-browser-automation-playbook.md) |
| Get a generated cell into a notebook | [playbook: notebooks](references/04-browser-automation-playbook.md#notebooks-the-workhorse) | `scripts/browser/paste_into_monaco.js` |
| Prove a build works | [verification gates](references/09-verification-and-critic.md) | [metric-view check](references/02-runbook.md#phase-4-verify-metric-views) |
| Add data quality, clustering, monitoring | [data quality](references/06-data-quality-and-features.md) | |
| Enrich metadata or add derived views | [Genie Code enrichment](references/07-genie-code-enrichment.md) | |
| Share access, set policies, masks, tokens | [safety](references/08-safety-permissions-privacy.md) (hand over, do not do) | |
| Publish anything outside the project folder | [safety: privacy](references/08-safety-permissions-privacy.md#privacy-and-redaction) | `scripts/redaction_scan.sh`, [critic](references/09-verification-and-critic.md#gate-6---independent-critic) |
| Explain GA vs preview, or what Genie reads | [concepts](references/01-concepts-and-architecture.md) | |
| Something failed | symptom table below, then [gotchas](references/05-gotchas-and-fixes.md) | |
| Know what is actually proven | [appendix G](appendix/G-verification-evidence.md) | [known limitations](appendix/F-known-limitations.md) |
| Know why it is designed this way | [appendix D](appendix/D-decision-log.md) | |
| Look up a term | [glossary](appendix/C-glossary.md) | |
| Find official docs or prior art | [appendix A](appendix/A-public-repos.md) | |
| See a finished build end to end | [appendix E](appendix/E-case-study-retail-build.md) | |

## 2. Symptom to fix
| You see | Do this | Detail |
|---|---|---|
| `unsafe expression ... table.column.field: <reason>` from `validate`, or the same as a `ValueError` | The message names the field and reason: fix a typo in a column name, or rewrite the string using only column names, numbers, `+ - * / %`, comparisons, `and/or/not`, `abs()` (no `**`, `//`, `in`, `if/else`, `round()`) | [spec format](references/03-spec-format.md#expression-safety) |
| `already exists and was not created by genie_onto` | Use a new schema; `force=True` only if you mean to replace | [gotchas](references/05-gotchas-and-fixes.md#build--sql) |
| `WARN cleanup <table>: kept` | The table has no `genie_onto.managed` marker; drop it by hand if intended | [gotchas](references/05-gotchas-and-fixes.md#build--sql) |
| Every metric-view join fails, `on` missing | PyYAML read `on:` as a boolean; load specs with `genie_onto` only | [gotchas](references/05-gotchas-and-fixes.md#build--sql) |
| `NameError: name 'x' is not defined` in a notebook cell | YAML braces inside an f-string need doubling | [gotchas](references/05-gotchas-and-fixes.md#build--sql) |
| A ratio measure is always 0 or 1 | The synthetic tail never occurs; use a skewed generator | [spec format](references/03-spec-format.md#generators) |
| `chained` join rejected | Denormalise the key into the fact with `gen: lookup` | [gotchas](references/05-gotchas-and-fixes.md#build--sql) |
| Pasted or typed code is mangled | Paste with the synthetic event, never type | [playbook](references/04-browser-automation-playbook.md#notebooks-the-workhorse) |
| Clicks land in the wrong place | Convert screenshot to CSS coordinates, or click by ref | [playbook](references/04-browser-automation-playbook.md#coordinates-and-timing) |
| Notebook output not found | It is virtualised; scroll and read from the DOM | [gotchas](references/05-gotchas-and-fixes.md#ui--automation) |
| Page or agent form text went to the wrong field | Close the Genie Code panel, wait, screenshot after each section | [gotchas](references/05-gotchas-and-fixes.md#ui--automation) |
| 401 on a page REST call, or a popup is blocked | A boundary: use the UI or ask the user | [safety](references/08-safety-permissions-privacy.md) |
| Agent says it cannot answer (missing dimension) | Add the dimension to the view, state which one to use in the instructions | [gotchas](references/05-gotchas-and-fixes.md#genie-behavior) |
| Domain counts or tags wrong after a rebuild | Re-run the tag step (`domains_created_<industry>` = `yes`) | [runbook](references/02-runbook.md#phase-6-tags) |
| Data looks unrealistic (events dated before a customer's start, repeat enrollments) in `retail`, `bfsi_banking`, `telecom`, `education` | Known and listed per pack; demo data only | [appendix F](appendix/F-known-limitations.md#packs-data-realism) |

## 3. Spec key finder
| Key | Where |
|---|---|
| `catalog` `schema` `seed` `history_days` `as_of` `currency` `domains` | [Top level](references/03-spec-format.md#top-level) |
| `kind` `rows` `cluster_by` `checks` `generator: calendar` | [Tables](references/03-spec-format.md#tables) |
| `type` `gen` `pk` `fk` `where` `nullable` `check` `allowed` `pii` `classification` `hidden` | [Columns](references/03-spec-format.md#columns) |
| `seq` `template` `choice` `map` `uniform` `lognormal` `beta` `poisson` `bool` `fk` `date_key` `date` `lookup` `date_key_after` `date_key_before` `derived` | [Generators](references/03-spec-format.md#generators) |
| `source` `joins` `dimensions` `measures` `format` `synonyms` | [Metric views](references/03-spec-format.md#metric-views) |
| `agent.name` `sources` `instructions` `questions` | [Agent](references/03-spec-format.md#agent) |
| `pages` `definition` `business_use` `related` | [Pages](references/03-spec-format.md#pages) |
| allowed characters in `derived`, `check`, `where`, `template` | [Expression safety](references/03-spec-format.md#expression-safety) |

## 4. Commands
Run from your **project folder**; `SKILL` is this skill's directory.
```bash
SKILL=~/.claude/skills/databricks-genie-ontology
python3 $SKILL/scripts/genie_onto.py --version                      # builder version
python3 $SKILL/scripts/genie_onto.py validate spec.yaml             # static checks (several files allowed)
python3 $SKILL/scripts/genie_onto.py check spec.yaml                # + synthetic data + integrity checks
python3 $SKILL/scripts/genie_onto.py sql spec.yaml                  # every statement the build runs
python3 $SKILL/scripts/genie_onto.py docs spec.yaml out/            # agent.md, pages/*.md, ui-checklist.md
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell   # one pasteable cell
bash $SKILL/scripts/redaction_scan.sh . <term> ...                  # before publishing
python3 $SKILL/scripts/verify_links.py                              # external link and repo checker
```
Repository maintenance (only in a full checkout of the repo, not in an installed skill; run from the repo root): `python3 -m unittest discover -s tests`, `python3 tools/check_docs.py`, `python3 tools/check_docs.py --write` (refreshes the catalog below).

## 5. Files
| Path | Purpose |
|---|---|
| `scripts/genie_onto.py` | The builder: validate, check, sql, docs, notebook; `deploy()` and `cleanup()` inside Databricks |
| `scripts/browser/` | `paste_into_monaco.js`, `read_cell_output.js`, `coords.js`, `serve_files.py` (hardened throwaway server) |
| `scripts/redaction_scan.sh`, `scripts/verify_links.py` | Pre-publish privacy scan; link and repo checker |
| `templates/` | `spec_template.yaml`, `PROJECT_CLAUDE.md`, `STATE.md`, `critic_prompt.md` |
| `industries/*.yaml` | The packs; status table in [industries/README.md](industries/README.md) |

## 6. Document catalog
Generated by `python3 tools/check_docs.py --write` (repo checkout only); do not edit by hand.

<!-- CATALOG:BEGIN -->
| Document | Kind | Summary | Read when |
|---|---|---|---|
| [SKILL.md](SKILL.md) | router | Entry point: decision table, runbook phases, rules. | Always first. |
| [references/01-concepts-and-architecture.md](references/01-concepts-and-architecture.md) | reference | What Genie ontology, metric views, domains, Pages and certification are, which layer this skill builds, and how Genie was observed to answer. | You need the vocabulary, or must tell a user what is GA or preview and what this skill does and does not deliver. |
| [references/02-runbook.md](references/02-runbook.md) | reference | Phases 0-11 from project folder to handoff, each with an acceptance test, plus rebuild and reset rules. | You are executing a build, or resuming one from STATE.md. |
| [references/03-spec-format.md](references/03-spec-format.md) | reference | Every key of the YAML spec (tables, columns, generators, metric views, agent, pages), the expression-safety rules and an authoring checklist. | You are writing, editing or debugging a spec, or validate/check reports an error. |
| [references/04-browser-automation-playbook.md](references/04-browser-automation-playbook.md) | reference | How to drive the Databricks UI reliably: paste instead of type, coordinates, timing, DOM reads, notebooks, Catalog Explorer, Domains, Pages, Genie agents. | You must do a UI-only step, or a click, paste or read misbehaves. |
| [references/05-gotchas-and-fixes.md](references/05-gotchas-and-fixes.md) | reference | Symptom, cause and fix tables for build/SQL, UI automation and Genie behaviour problems that were hit for real. | Something failed or behaved unexpectedly. |
| [references/06-data-quality-and-features.md](references/06-data-quality-and-features.md) | reference | What the builder applies (constraints, clustering, CDF, stats, tags, audit), schema-level Data Quality Monitoring, and governance metadata. | You are hardening the tables or enabling monitoring. |
| [references/07-genie-code-enrichment.md](references/07-genie-code-enrichment.md) | reference | The draft, review, run pattern for using Genie Code to add comments and enriched views safely. | You want richer metadata or derived columns without hand-writing all the SQL. |
| [references/08-safety-permissions-privacy.md](references/08-safety-permissions-privacy.md) | reference | What the agent never does on its own (credentials, grants, policies, destructive SQL), consent rules, redaction and regulated-data reminders. | Before any outward-facing, destructive or access-related step, and before publishing anything. |
| [references/09-verification-and-critic.md](references/09-verification-and-critic.md) | reference | Six ordered gates from spec to Genie behaviour, the critic checklist and the definition of done. | You are about to declare a build, a pack or the repo finished. |
| [appendix/A-public-repos.md](appendix/A-public-repos.md) | appendix | Verified links to official Databricks docs, the example this skill generalizes, and public semantics/Genie/governance repos with licence notes. | You want prior art, accelerators or official documentation. |
| [appendix/B-industry-guide.md](appendix/B-industry-guide.md) | appendix | Per-industry KPIs, cross-fact Pages, data-protection notes and extension ideas, plus how to add a new industry pack. | You are choosing, adapting or authoring an industry pack. |
| [appendix/C-glossary.md](appendix/C-glossary.md) | appendix | One-line definitions of every term and tool name used in this skill, each pointing to the document that covers it. | A term in another doc is unclear, or you need to explain a term to the user in one sentence. |
| [appendix/D-decision-log.md](appendix/D-decision-log.md) | appendix | The design decisions behind the skill, why each was made, the evidence, and what would justify revisiting it. | You are tempted to change an approach (flat joins, paste-not-type, marker guard, spec-first) and want to know why it is the way it is. |
| [appendix/E-case-study-retail-build.md](appendix/E-case-study-retail-build.md) | appendix | What the first end-to-end build on a real workspace contained, how long each part took, what went wrong, and how it was fixed; the source of most gotchas. | You want a concrete picture of a finished build, realistic timings, or the story behind a rule. |
| [appendix/F-known-limitations.md](appendix/F-known-limitations.md) | appendix | Understood defects and unverified areas that are deliberately not fixed yet, each with evidence, workaround and a suggested fix. | A pack looks unrealistic, a constraint is missing, or you are choosing what to improve next. |
| [appendix/G-verification-evidence.md](appendix/G-verification-evidence.md) | appendix | The single record of what was verified live, on which builder version and date, what the independent reviews found, and what is only locally tested. | You need to state precisely what is proven, or decide whether a change needs a live re-run. |
| [industries/README.md](industries/README.md) | catalog | The 11 industry packs with their domains, metric views, cross-fact Pages and the canonical live-verification status of each. | You are choosing a pack or need to know how far a pack has been proven. |
| [templates/PROJECT_CLAUDE.md](templates/PROJECT_CLAUDE.md) | template | Project instructions to copy next to your spec as CLAUDE.md. | Phase 0 of the runbook. |
| [templates/STATE.md](templates/STATE.md) | template | Progress, ids and definition-of-done checklist to copy as STATE.md (local only, never publish). | Phase 0 of the runbook; update after every step. |
| [templates/critic_prompt.md](templates/critic_prompt.md) | template | Self-contained prompt and checklist for the independent critic. | Gate 6 of the verification gates, before publishing or handover. |
<!-- CATALOG:END -->
