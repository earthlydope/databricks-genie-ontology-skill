---
name: databricks-genie-ontology
description: Build, verify and harden a governed Genie ontology foundation on Databricks (Unity Catalog tables with PK/FK and comments, metric views, domains, Pages, certification, a Genie agent) for ANY industry, using a spec-driven builder plus browser automation for the UI-only parts. Ships 11 industry packs (retail, CPG/FMCG, banking, insurance, healthcare provider, pharma/life sciences, manufacturing, telecom, energy/utilities, supply chain/logistics, education). Use when asked to set up Genie Ontology, UC business semantics, metric views, a Genie agent/space, domains/pages/certification, data-quality monitoring for those tables, or an industry Genie demo.
---

# Databricks Genie ontology foundation (any industry)

You are building the **governed semantic foundation** that Genie answers from: well-commented tables with keys,
certified **metric views**, business **domains**, definition **Pages**, and a **Genie agent** attached to the metric views.
The builder and the runbook were exercised on a real workspace (see `references/09-verification-and-critic.md` for exactly what was and was not verified); anything unverified says so.

> **Product accuracy.** Databricks positions "Genie Ontology" as a *learned* context layer (gated preview) that sits on top of
> this governed foundation (Unity Catalog Business Semantics: metric views, Pages, domains, certification). Release status changes: check current docs.
> You are building the foundation. Never tell the user the learned layer is live because of this work. See `references/01-concepts-and-architecture.md`.

## 1. Decide the path (ask only what you cannot infer)

| Situation | Path |
|---|---|
| User names an industry or wants a demo | **Pack**: copy `industries/<pack>.yaml`, rename catalog/schema, build. |
| Industry not covered, or custom model | **Author a spec**: start from `templates/spec_template.yaml`; read `references/03-spec-format.md` and `industries/README.md`. |
| User has real tables already | **Do not generate data.** Write a spec whose tables describe the real ones, or hand-write the metric views; use only phases 5-10. Never copy real PII/PHI into a demo. |

Ask for: industry/pack, target catalog+schema names (default from the pack), how the user will sign in (they must do it), and whether
other people need access (that is theirs to grant; see `references/08-safety-permissions-privacy.md`).

## 2. Prerequisites and environment truths

- Workspace with **Unity Catalog** and **serverless** compute or a SQL warehouse. `CREATE CATALOG` must be allowed (else pass an existing catalog).
- **You cannot sign in for the user.** Open the login page in the browser pane and ask them to sign in; never type passwords or create tokens without consent.
- The console shows an "automated browser control detected" banner saying automation is not supported. Tell the user about it once and let them decide whether to continue; in our runs nothing was blocked by it. Cookie-authenticated REST calls from the page return **401**; do not try to bypass. UI is the default path; a PAT (created by the user, with explicit consent) enables REST/SDK as an optional speed-up.
- Pages cannot open new tabs/popups from your input (Genie One launch, "Configure for schema" links). Navigate to the URL instead, or ask the user to click.
- Local Python (3.9+) with `pandas numpy pyyaml` for `check`/`notebook` (`pip install pandas numpy pyyaml`).
- Set `SKILL` to this skill's directory (for example `~/.claude/skills/databricks-genie-ontology`) and run the commands below **from your project folder**, where `spec.yaml` lives.

## 3. Runbook (details: `references/02-runbook.md`)

| # | Phase | How | Done when |
|---|---|---|---|
| 0 | Project folder | Copy `templates/PROJECT_CLAUDE.md` + `templates/STATE.md`; keep STATE.md current after every step | STATE.md exists |
| 1 | Spec | `cp $SKILL/industries/<pack>.yaml spec.yaml`; edit; `python3 $SKILL/scripts/genie_onto.py validate spec.yaml` then `check` | 0 errors, 0 warnings, data checks pass |
| 2 | Sign-in + recon | Browser: user signs in; list catalogs/workspace folders; look for earlier attempts | login confirmed, host + ids in STATE |
| 3 | Build SQL layer | `notebook spec.yaml out/build.cell.py --cell`, create a notebook, paste, run (`references/04`) | `Done. 0 error(s)` + all `PASS` |
| 4 | Verify metric views | `SELECT ..., MEASURE(x) FROM mv GROUP BY ALL`; reconcile to a raw-table query | numbers match |
| 5 | Domains (UI) | Discover > Create > Create domain (Source: New tag), publish each | all domains listed |
| 6 | Tags | Set the notebook widget `domains_created_<industry>` to `yes` and re-run (this re-run only re-applies tags; it does not rebuild data) | domain counts match the spec |
| 7 | Genie agent (UI) | `docs spec.yaml out/` writes agent.md; create, attach metric views only, certify, add to domain, rename | agent answers a sample question |
| 8 | Pages (UI) | Create + publish each Page from `outdir/pages/*.md`, link related assets | pages listed under their domains |
| 9 | Test questions | Ask every sample question; cross-check against SQL; ask one "definition" question per Page | answers + sources correct |
| 10 | Harden (optional) | DQ monitoring (schema Details > Advanced), constraints/clustering already in build, Genie Code enrichment (`references/06`, `07`) | monitoring Enabled |
| 11 | Handoff | Update STATE.md; list what was not done and why | user has a clear summary |

Order matters: tags need the domains to exist; the agent needs the metric views; Pages need the assets and domains.

## 4. Rules that save hours

1. **Spec first, UI last.** Everything expressible as SQL is generated and re-runnable; only Domains, the agent, certification of the agent, and Pages need the UI.
2. **Never type code into the notebook editor.** Auto-indent/auto-close corrupts it. Paste via a synthetic paste event (`scripts/browser/paste_into_monaco.js`).
3. **Prefer one notebook per spec.** Widget names carry the pack name so a reused notebook cannot inherit another pack's schema, but a clean notebook per spec is easier to audit. The build refuses to replace an existing table that this tool did not create.
4. **Verify, do not assume.** Every build ends with the audit; every metric view with a `MEASURE()` reconciliation; every agent with real questions.
5. **Cross-fact ratios are Pages + agent instructions**, not measures (return rate, loss ratio, churn rate, SAIDI). A measure can only aggregate its own source plus flat-joined dimensions.
6. **Join dimensions flat.** Denormalize the foreign key into the fact (the generator's `lookup` does this) so every metric-view join is `source.k = alias.k`. Chained joins are rejected by the validator.
7. **Screenshots lag one action.** Wait 2 s before trusting one; prefer `get_page_text`/JS reads; scale screenshots to 0.5-0.6.
8. **Security settings are the user's.** Do not grant access, set row filters/column masks/ABAC policies, or add users. Explain and hand over the SQL/steps (`references/08`).
9. **Redact before sharing.** No emails, workspace hosts, workspace/org/object ids, usernames in anything you publish.
10. **Run an independent critic** on the finished build before declaring victory (`references/09-verification-and-critic.md`).

## 5. Commands

```bash
SKILL=~/.claude/skills/databricks-genie-ontology            # or the path of this directory
cp $SKILL/industries/bfsi_banking.yaml spec.yaml             # in your project folder; edit catalog/schema/names
python3 $SKILL/scripts/genie_onto.py validate spec.yaml      # static checks (accepts several files)
python3 $SKILL/scripts/genie_onto.py check spec.yaml         # + synthetic data + integrity checks
python3 $SKILL/scripts/genie_onto.py sql spec.yaml           # every statement the build runs
python3 $SKILL/scripts/genie_onto.py docs spec.yaml out/     # agent.md, pages/*.md, ui-checklist.md
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.py            # importable notebook (creates out/)
python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell # one pasteable cell
```

## 6. Reference map

| Need | Read |
|---|---|
| Concepts, what is GA vs preview, how Genie ranks sources | `references/01-concepts-and-architecture.md` |
| Step-by-step with acceptance criteria | `references/02-runbook.md` |
| Writing or editing a spec | `references/03-spec-format.md`, `templates/spec_template.yaml` |
| Driving the Databricks UI reliably | `references/04-browser-automation-playbook.md` + `scripts/browser/` |
| Something broke | `references/05-gotchas-and-fixes.md` |
| Data quality, clustering, tags, monitoring | `references/06-data-quality-and-features.md` |
| Using Genie Code to enrich metadata/data safely | `references/07-genie-code-enrichment.md` |
| What not to do / privacy / redaction | `references/08-safety-permissions-privacy.md` |
| Proving it works, critic review | `references/09-verification-and-critic.md` |
| Public repos and docs | `references/10-public-repos-and-docs.md` |
| Per-industry KPIs, Pages, regulation notes | `references/11-industry-guide.md`, `industries/README.md` |
