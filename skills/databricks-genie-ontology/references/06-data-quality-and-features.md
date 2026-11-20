# 06 - Data quality, table features and governance metadata

## What the builder applies (live-verified on real workspaces: NOT NULL, PK/FK, `check:`/`allowed:`/table `checks:` incl. an exact-decimal equality, clustering, change data feed, statistics, tags, audit)
- `NOT NULL` on every non-nullable column; informational **PK/FK** constraints; enforced **CHECK** constraints from `check:`, `allowed:` (auto for `choice`) and table `checks:`.
- `ALTER TABLE ... CLUSTER BY (...)` + `OPTIMIZE` for facts with `cluster_by` (liquid clustering), `delta.enableChangeDataFeed = true`, `ANALYZE TABLE ... COMPUTE STATISTICS FOR ALL COLUMNS`.
- Table tags `table_type`, `layer=gold`, `system.certification_status=certified`; column tags `pii=true` + `data_classification=personal` for `pii` columns, `data_classification=<x>` for `classification`.
- An audit that prints `PASS/FAIL` per check: duplicate primary keys and orphan foreign keys for every table.
Seconds-to-minutes: constraint statements are the slow part (about 2 s each); budget 3-5 minutes for 7 tables.

## Data Quality Monitoring (schema level, UI)
Catalog Explorer > the schema > **Details** tab > Advanced > **Data Quality Monitoring: Enable**. In the dialog turn **Anomaly detection** on (freshness and completeness for all tables in the schema), leave **Alerts** off unless the user wants notifications, **Save**.
Result: tables show Quality "Training" while baselines are learned; the table page "Quality" tab and About panel then show Freshness/Completeness. "Predictive Optimization" is separate and was already Enabled (inherited).
Optional: *Monitor by slice (Beta)* to watch anomalies per value of a column; *Data profiling* (per table) creates metric tables inside your schema (it clutters a Genie-facing schema: use a separate output schema, or skip).

## Audit and rules authoring
- Put every business rule you can state in one line into `check:` / `checks:`; the failing rows tell you about real data problems on real tables.
- Keep table-level `checks:` in the subset understood by both Spark SQL and pandas (comparisons, `+ - * /`, `AND/OR`); `IN`/`BETWEEN` are rejected by the validator (use `allowed:` for value lists and `check:` for ranges). A lone `a = b` is tested with a 0.005 tolerance locally and exactly in SQL.
- Add reconciliation rules beyond keys: refunds never exceed order revenue; events never precede their parent; counts of children never exceed parents. Prove them in `audit`.

## Governance metadata worth adding
- Certification (`system.certification_status`) on every asset the agent may use.
- Domains as business areas, assets in more than one domain are fine (conformed dimensions often belong to several).
- `pii` tags on direct identifiers. Tags are metadata, not enforcement: enforcement (masks/filters/ABAC) is a security decision for the user.

## What to hand the user instead of doing it (security)
Row filters, column masks, attribute-based policies, grants, sharing, adding users. Provide the exact statements and pointers (`08`) and the public tooling that automates them
(`genierails`, `uc-declarative-abac` in `10-public-repos-and-docs.md`).

## Maintenance
Rolling date window: `history_days` ends "today" at build time; re-running shifts the window (dates change, keys do not). Re-run audits after any rebuild. After a rebuild of a metric view, re-apply tags.
