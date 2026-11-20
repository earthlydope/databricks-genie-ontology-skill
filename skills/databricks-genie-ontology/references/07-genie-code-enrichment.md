# 07 - Enriching tables and metadata with Genie Code (draft, review, run)

Genie Code is Databricks' in-product coding assistant (side panel, sparkle icon in the top bar). It can inspect tables and write SQL.
Use it as an **author**, not as an unsupervised operator: you keep control of what executes.

## Pattern (proven)
1. **Prompt for a script, not for actions.** Start with "Do not run or change anything yet. ... write SQL only, one script, one code block." Say what must never happen ("Never alter or drop existing tables"; "CREATE OR REPLACE VIEW only").
2. **Name the target precisely** (`catalog.schema`), the objects to describe, and the columns/measures you want (tenure, lifetime value, return rate, value tier...).
3. **Let it inspect** (it runs read-only metadata queries first; this takes 1-3 minutes).
4. **Extract the script** with JS: the longest `pre, code` element's `innerText`. Store it (e.g. `sessionStorage`) so it survives navigation.
5. **Review before running**: no `DROP`/`DELETE`/`ALTER ... DROP`, no writes to existing tables, correct join grain (pre-aggregate facts before joining to avoid fan-out), division by zero handled (`try_divide`, `NULLIF`).
6. **Run it yourself** in a notebook: split statements on `;\n`, execute each with `spark.sql`, print `OK`/`ERROR`.
7. **Reconcile** the outputs to source (totals equal, row counts equal, tiers split as expected).
8. **Productionize**: certify and domain-tag the new views, attach them to the agent (Configure > Resources > Add > Table), re-test a question that needs them, save the SQL in the repo.

## What worked
- Metric view descriptions via `COMMENT ON TABLE <mv> IS '...'` (all three succeeded).
- Enriched dimension **views** (not tables) with per-column `COMMENT`s: customer tenure/tenure band, lifetime revenue/returns, return rate, `NTILE(3)` value tier; product average selling price, margin %, price band, units, revenue, return rate. Totals matched the fact table exactly.
- After attaching the views to the agent, "lifetime revenue and return rate by customer value tier" was answered from the enriched view with the same figures as the direct SQL check.

## Guardrails
- New objects only; never mutate existing tables with generated SQL.
- Enrichment of *data* belongs in views or new tables with a stated grain; keep the SQL next to the spec (for example `out/enrichment.sql`) so the build is reproducible.
- Do not enrich with external data about people. Derived metrics only.
- Treat the draft as untrusted code: you are responsible for what runs.

## Metadata enrichment ideas (no data change)
- Table/column comments for every asset lacking one; synonyms in metric views; Page definitions for every cross-fact KPI; domain descriptions.
- Public helpers: `genie-ontology-readiness` (assess readiness pillars), `databricks-genie-workbench` and `genie-best-practices-agent` (score/optimize an agent) - see `10-public-repos-and-docs.md`.
