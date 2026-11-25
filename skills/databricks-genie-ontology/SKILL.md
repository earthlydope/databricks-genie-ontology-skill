---
name: databricks-genie-ontology
description: Build, verify and harden a governed Genie ontology foundation on Databricks (Unity Catalog tables with PK/FK and comments, metric views, domains, Pages, certification, a Genie agent) for ANY industry, using a spec-driven builder plus browser automation for the UI-only parts. Ships 11 industry packs (retail, CPG/FMCG, banking, insurance, healthcare provider, pharma/life sciences, manufacturing, telecom, energy/utilities, supply chain/logistics, education). Use when asked to set up Genie Ontology, UC business semantics, metric views, a Genie agent/space, domains/pages/certification, data-quality monitoring for those tables, or an industry Genie demo.
---

# Databricks Genie ontology foundation (any industry)

You build the **governed semantic foundation** Genie answers from: well-commented tables with keys, certified **metric views**, business **domains**, definition **Pages**, and a **Genie agent** on the metric views.
This file is a router. Find any detail through **[INDEX.md](INDEX.md)** (by task, symptom, spec key or command) instead of reading every reference.
What is proven and what is not: [appendix G](appendix/G-verification-evidence.md). Anything unverified says so.

> **Product accuracy.** "Genie Ontology" as a *learned* context layer is a gated preview that sits on top of this foundation (Unity Catalog Business Semantics). Release status changes: check current docs.
> You build the foundation. Never tell the user the learned layer is live because of this work ([concepts](references/01-concepts-and-architecture.md)).

## 1. Decide the path
Ask only what you cannot infer.

| Situation | Path |
|---|---|
| User names an industry or wants a demo | **Pack**: copy `industries/<pack>.yaml` to `spec.yaml` in the project folder, rename catalog/schema, build. Pack status: [industries/README.md](industries/README.md) |
| Industry not covered, or a custom model | **Author a spec** from `templates/spec_template.yaml`; read [spec format](references/03-spec-format.md) and the [industry guide](appendix/B-industry-guide.md) |
| User has real tables already | **Do not generate data.** Write a spec that describes the real tables, or hand-write the metric views, then use phases 5-10 only. Never copy real PII/PHI into a demo |

Ask for: industry/pack, catalog and schema names (default from the pack), how the user will sign in (they must), and whether other people need access (theirs to grant: [safety](references/08-safety-permissions-privacy.md)).

### Quick path (example: an insurance demo)
```bash
SKILL=~/.claude/skills/databricks-genie-ontology            # where the skill is installed
mkdir my-insurance-demo && cd my-insurance-demo             # your PROJECT folder, not the skill folder
cp $SKILL/templates/PROJECT_CLAUDE.md CLAUDE.md && cp $SKILL/templates/STATE.md STATE.md
cp $SKILL/industries/bfsi_insurance.yaml spec.yaml          # edit catalog, schema and names
python3 $SKILL/scripts/genie_onto.py validate spec.yaml     # 0 errors, 0 warnings
python3 $SKILL/scripts/genie_onto.py check spec.yaml        # synthetic data + integrity checks
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell   # one pasteable cell
python3 $SKILL/scripts/genie_onto.py docs spec.yaml out/    # agent.md, pages/*.md, ui-checklist.md
```
Then the user signs in, you paste and run the cell (phase 3 below), and continue with phases 4-11. **Tell the user the pack's status first**: `bfsi_insurance` is "Local only" (never built on a live workspace), so build it on a throwaway schema ([pack status](industries/README.md)).

## 2. Prerequisites and environment truths
- Workspace with **Unity Catalog** and serverless compute or a SQL warehouse; `CREATE CATALOG` allowed (else pass an existing catalog).
- **You cannot sign in for the user.** Open the login page and ask them to sign in; never type passwords or create tokens without consent.
- The console shows an "automated browser control detected" banner. Tell the user once; in our runs nothing was blocked by it. Cookie-authenticated REST from the page returns **401**: a boundary, do not bypass. The UI is the default path; a user-created PAT is an optional speed-up.
- Pages cannot open popups or new tabs from your input (Genie One launch, "Configure for schema"): navigate to the URL, or ask the user to click.
- Local Python 3.9+ with `pandas numpy pyyaml`. Set `SKILL` to this directory and run commands **from your project folder** (commands: [INDEX](INDEX.md#4-commands)).
- A spec is code: only run specs you trust ([expression safety](references/03-spec-format.md#expression-safety)).

## 3. Runbook
Phase details and acceptance criteria: [references/02-runbook.md](references/02-runbook.md). Order matters: tags need the domains; the agent needs the metric views; Pages need assets and domains.

| # | Phase | Done when |
|---|---|---|
| 0 | [Project folder](references/02-runbook.md#phase-0-project-folder): copy `templates/PROJECT_CLAUDE.md` and `templates/STATE.md`; update STATE.md after every step | STATE.md exists |
| 1 | [Spec](references/02-runbook.md#phase-1-spec): copy a pack, edit, `validate`, `check` | 0 errors, 0 warnings, data checks pass |
| 2 | [Sign-in and recon](references/02-runbook.md#phase-2-sign-in-and-recon) | logged in, no name collisions |
| 3 | [Build the SQL layer](references/02-runbook.md#phase-3-build-the-sql-layer): generate the cell, paste ([playbook](references/04-browser-automation-playbook.md#notebooks-the-workhorse)), run | `Done. 0 error(s)` and all `PASS` |
| 4 | [Verify metric views](references/02-runbook.md#phase-4-verify-metric-views) with `MEASURE()` | numbers match raw SQL |
| 5 | [Domains (UI)](references/02-runbook.md#phase-5-domains), publish each | all domains listed |
| 6 | [Tags](references/02-runbook.md#phase-6-tags): set `domains_created_<industry>` to `yes`, re-run | domain counts match the spec |
| 7 | [Genie agent (UI)](references/02-runbook.md#phase-7-genie-agent): `docs` writes `agent.md`; attach metric views, certify, add to domain | agent answers a sample question |
| 8 | [Pages (UI)](references/02-runbook.md#phase-8-pages) from `out/pages/*.md` | pages listed under their domains |
| 9 | [Test questions](references/02-runbook.md#phase-9-test-questions) incl. one definition question per Page | answers and sources correct |
| 10 | [Harden](references/02-runbook.md#phase-10-harden) (optional): [data quality](references/06-data-quality-and-features.md), [Genie Code enrichment](references/07-genie-code-enrichment.md) | monitoring Enabled |
| 11 | [Handoff](references/02-runbook.md#phase-11-handoff): list what was not done and why | user has a clear summary |

## 4. Rules that save hours
1. **Spec first, UI last.** Everything expressible as SQL is generated and re-runnable; only Domains, the agent (and its certification) and Pages need the UI.
2. **Never type code into the notebook editor.** Auto-indent and auto-close corrupt it; paste with `scripts/browser/paste_into_monaco.js`.
3. **One notebook per spec.** Widget names carry the pack name, and the build refuses to replace a table it did not create, but a clean notebook is easier to audit.
4. **Verify, do not assume.** Every build ends with the audit, every metric view with a `MEASURE()` reconciliation, every agent with real questions ([gates](references/09-verification-and-critic.md)).
5. **Cross-fact ratios are Pages plus agent instructions**, not measures (return rate, loss ratio, churn, SAIDI).
6. **Join dimensions flat.** Denormalise keys into the fact (`gen: lookup`); chained joins are rejected.
7. **Screenshots lag one action.** Wait 2 s; prefer `get_page_text` or JS reads; scale screenshots to 0.5-0.6.
8. **Security settings are the user's.** No grants, row filters, column masks, ABAC policies or new users: explain and hand over the statements.
9. **Redact before sharing.** No emails, hosts, workspace/object ids or usernames in anything published; run `scripts/redaction_scan.sh`.
10. **Run an independent critic** before declaring victory ([Gate 6](references/09-verification-and-critic.md#gate-6---independent-critic)).

## 5. Where things are
- Find by task, symptom, spec key or command: **[INDEX.md](INDEX.md)**.
- Core references (`references/`, files 01 to 09): concepts, runbook, spec format, browser playbook, gotchas, data quality, Genie Code enrichment, safety, verification.
- Appendix (`appendix/`, files A to G, never required to build): public repos, industry guide, glossary, decision log, case study, known limitations, verification evidence.
