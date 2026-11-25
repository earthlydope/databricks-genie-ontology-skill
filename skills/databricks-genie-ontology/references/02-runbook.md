---
title: Runbook with acceptance criteria
kind: reference
summary: Phases 0-11 from project folder to handoff, each with an acceptance test, plus rebuild and reset rules.
read_when: You are executing a build, or resuming one from STATE.md.
---
# 02 - Runbook with acceptance criteria

Reference timings from the original build: SQL layer (tables, data, metric views, constraints, tags, audit) about 5 minutes of
compute; the UI-only objects (4 domains, agent, 3 Pages) about 40 minutes of browser time. Plan the user's expectations accordingly.

## Phase 0: Project folder
*Time: 2 min.*
Create a working folder. Copy `templates/PROJECT_CLAUDE.md` -> `CLAUDE.md` and `templates/STATE.md` -> `STATE.md`.
Update STATE.md after **every** step with: workspace URL (kept local, never published), object ids (notebook ids, agent id, page ids), what is done, what is not.
A future session (or another Claude) resumes from STATE.md without re-deriving anything.

## Phase 1: Spec
*Time: 5-15 min.*
1. Copy the pack into your project folder: `cp $SKILL/industries/<pack>.yaml spec.yaml` (`SKILL` = the skill directory). Change `catalog`/`schema` (a pack's default catalog is new; use an existing catalog if `CREATE CATALOG` is not allowed).
2. `validate` -> fix every error; aim for **0 warnings** (a warning means a missing comment or synonym, which hurts Genie).
3. `check` -> data integrity (PK unique, FK resolves, NOT NULL, CHECKs, no constant boolean/numeric columns).
4. Read the pack's `agent.instructions` and `pages`; adapt wording to the customer's language.
Acceptance: validate 0/0, check OK.

## Phase 2: Sign-in and recon
*Time: 5 min.*
1. Open the login page; ask the user to sign in (SSO or email). Do not type credentials. Confirm by reading the tab title/URL.
2. Record the workspace host and workspace id (`?o=` in the URL) in STATE.md only.
3. Recon before creating anything: Catalog Explorer (existing catalogs/schemas), Workspace folders (earlier attempts or imported repos), Genie Agents list. Reuse, do not duplicate.
Acceptance: logged in; no name collisions.

## Phase 3: Build the SQL layer
*Time: 5-10 min.*
1. From the project folder: `python3 $SKILL/scripts/genie_onto.py notebook spec.yaml out/build.cell.py --cell`.
2. Create a Python notebook in the workspace (Create > Notebook, or navigate to `/editor/notebooks/create?parentId=<folder id>`).
3. Paste the cell with the synthetic paste helper; run with Shift+Enter (see [the browser playbook](04-browser-automation-playbook.md)).
4. Read the output from the DOM (`read_cell_output.js`): expect `LOAD` lines, `OK` statements, `PASS` audits, final `Done. 0 error(s).`
   `WARN` lines are soft and do not count as errors: on re-runs they are benign (e.g. constraint already absent), but on a first run read each one, because clustering, change data feed, statistics, tags, comments and `format:` are soft steps.
5. If a metric view fails, the builder retries without `format:` blocks automatically; read why before accepting (see [gotchas](05-gotchas-and-fixes.md#build--sql)).
Acceptance: 0 errors; every audit PASS; no unexplained `WARN`; tables + metric views visible in Catalog Explorer.

## Phase 4: Verify metric views
*Time: 5 min.*
In a new cell run `SELECT <dim>, MEASURE(<m>) FROM <mv> GROUP BY ALL` for each metric view and **recompute one measure from the fact table independently**
(e.g. OEE from sums). They must match. Also check magnitudes are plausible (a ratio of exactly 0 or 1 means a degenerate dataset - fix the data generator, not the view).

## Phase 5: Domains
*Time: UI, ~2 min each.*
Discover > Create > **Create domain**; Source stays "New tag"; Name = the domain exactly as in the spec; Create; then **Publish** (the page shows a Draft badge until published).
The name is the tag key, so it must match the spec character for character.

## Phase 6: Tags
Set the notebook widget to `yes` and re-run (its name is `domains_created_` plus the spec's `industry` value, for example `domains_created_bfsi_insurance`; the case does not matter; this flow was exercised live only on the original build, see [appendix F](../appendix/F-known-limitations.md)): the generated cell then runs **only** the tag step (certification + each domain tag set/unset), so it cannot wipe UI edits or change numbers. (Equivalent: `deploy(spark, spec, steps=["tags"], domains=True)`.)
Check: Discover shows each domain with the expected asset count (tables + metric views per the spec).
Replacing a metric view (`CREATE OR REPLACE VIEW`) may drop its tags (not conclusively verified); re-run the tag step after any rebuild.

## Phase 7: Genie agent
*Time: UI, ~10 min.*
1. `python3 $SKILL/scripts/genie_onto.py docs spec.yaml out/` -> `out/agent.md`.
2. Genie Agents > New > **Select tables manually** > filter **Metric views** > tick the agent's sources > **Create manually**.
3. Configure > About: edit Description; edit **Common questions** (type, Enter, repeat) and Save. Instructions tab: paste the instruction text; Save.
   (Examples tab is for SQL examples, not sample questions.)
4. Kebab > **Assign certification** > Certified > Save.
5. Rename: the agent page cannot rename; use Workspace home > right-click the agent row > Rename.
6. Domain page (e.g. Sales) > kebab > **Add to domain** > pick the agent.
Acceptance: agent shows the certified badge, sources listed, and answers a sample question with "1 source".

## Phase 8: Pages
*Time: UI, ~6 min each.*
Discover > Create > **Create page** (`/discover/pages/new`). Close the Genie Code side panel first (it opens late and shifts layout).
Click the title text and type the name; Domain dropdown (wait 2 s, then pick); Synonyms (`+`, type, Enter, repeat); Description; Body; **Add related asset** (type the name, take the first hit); **Publish**.
Body quirk: the template shows "Definition" and "Business use" headings; text typed after clicking lands in the last block. Keep definition + business use in one block if needed; the content still reads correctly.
Acceptance: each Page is published and shows under its domain on Discover.

## Phase 9: Test questions
*Time: 10 min.*
For every `agent.questions`: ask in the agent chat; verify the SQL/answer against your own query. Then, in a **domain-scoped** chat (Discover > domain > Ask Genie), ask "What does <term> mean?" per Page and confirm it reads the Page.
Record failures as findings: missing dimension, ambiguous synonym, wrong default time range -> fix the spec/instructions and rebuild (rebuild is safe: tables are `CREATE OR REPLACE`, data is overwritten).

## Phase 10: Harden
*Time: optional, 15-30 min.*
See [data quality](06-data-quality-and-features.md) and [Genie Code enrichment](07-genie-code-enrichment.md): enable schema-level Data Quality Monitoring; the build already added NOT NULL/CHECK/clustering/stats/tags; use Genie Code (draft-only) to add comments or enriched views; certify and attach them.

## Phase 11: Handoff
STATE.md final: what exists (with counts), what was verified (questions + results), what was not done (policies, sharing, Genie One, certification of Pages) and why. Offer next steps; do not start them unasked.

## Rebuild and reset
A **full** re-run of the build is repeatable (tables are `CREATE OR REPLACE` and reloaded; the data window moves with today's date unless the spec sets `as_of: YYYY-MM-DD`). Partial steps: `tags` alone is safe; `constraints` alone is not (PK/FK are added without a drop).
The build refuses to replace an existing table that lacks the `genie_onto.managed` property (not created by this tool) unless `force=True`.
To remove what was built: `cleanup(spark, spec, confirm="DELETE")` drops **only the spec's own** metric views and tables, then the schema if it is then empty; other objects in the schema are left alone. Domains, the agent and Pages are UI objects: delete by hand.
