---
title: Glossary
kind: appendix
summary: One-line definitions of every term and tool name used in this skill, each pointing to the document that covers it.
read_when: A term in another doc is unclear, or you need to explain a term to the user in one sentence.
---
# Appendix C - Glossary

| Term | Meaning | More |
|---|---|---|
| **Unity Catalog (UC)** | Databricks' governance layer: catalogs, schemas, tables, views, tags, permissions, lineage | [concepts](../references/01-concepts-and-architecture.md) |
| **UC Business Semantics** | Metric views, domains, Pages and certification: the governed foundation this skill builds | [concepts](../references/01-concepts-and-architecture.md#the-layers) |
| **Genie Ontology (learned)** | Databricks' inferred context layer on top of the foundation; gated preview, **not** built by this skill | [concepts](../references/01-concepts-and-architecture.md#non-goals) |
| **Metric view** | A UC view defined in YAML (`WITH METRICS`): dimensions and measures defined once, queried with `MEASURE()` | [spec format](../references/03-spec-format.md#metric-views) |
| **Measure / dimension** | Aggregated value (`SUM(revenue)`) / attribute to slice by (`region`) inside a metric view | [spec format](../references/03-spec-format.md#metric-views) |
| **Flat join** | A metric-view join whose `on` references only `source` and its own alias; chained joins are rejected | [decision log](D-decision-log.md) |
| **Cross-fact KPI** | A ratio that needs two facts (return rate, loss ratio, churn, SAIDI); cannot be one measure, so it lives in a Page plus agent instructions | [spec format](../references/03-spec-format.md#pages) |
| **Domain** | Business area; implemented as a governed, key-only tag whose key is the domain name; created in the UI | [runbook](../references/02-runbook.md#phase-5-domains) |
| **Page** | A governed business definition (name, synonyms, body, related assets) that Genie reads as guidance | [runbook](../references/02-runbook.md#phase-8-pages) |
| **Certification** | Tag `system.certification_status=certified`; certified assets rank higher and carry a badge | [concepts](../references/01-concepts-and-architecture.md#the-layers) |
| **Genie agent (space)** | The configured chat surface: sources, instructions, sample questions | [runbook](../references/02-runbook.md#phase-7-genie-agent) |
| **Genie One** | Full-screen Genie chat across agents, dashboards, metric views and Pages | [gotchas](../references/05-gotchas-and-fixes.md#ui--automation) |
| **Genie Code** | Databricks' in-product coding assistant (side panel); used as a draft-only author | [enrichment](../references/07-genie-code-enrichment.md) |
| **Pack** | A complete industry spec (`industries/<name>.yaml`) | [industries](../industries/README.md) |
| **Spec** | The one YAML file that describes tables, data generators, metric views, agent and Pages | [spec format](../references/03-spec-format.md) |
| **Generator (`gen`)** | A rule that produces synthetic column data (`seq`, `fk`, `lognormal`, `derived`, ...) | [spec format](../references/03-spec-format.md#generators) |
| **Managed marker** | Table property `genie_onto.managed`; tables without it are never replaced or dropped by the builder | [safety](../references/08-safety-permissions-privacy.md) |
| **Informational constraint** | A UC primary/foreign key that is recorded but not enforced; `CHECK` and `NOT NULL` are enforced | [data quality](../references/06-data-quality-and-features.md) |
| **Liquid clustering / CDF** | `CLUSTER BY` layout for facts / `delta.enableChangeDataFeed` | [data quality](../references/06-data-quality-and-features.md) |
| **Data Quality Monitoring** | Schema-level anomaly detection (freshness, completeness), enabled in the UI | [data quality](../references/06-data-quality-and-features.md#data-quality-monitoring-schema-level-ui) |
| **Throwaway schema** | A scratch schema used to test builder changes, dropped afterwards | [verification](../references/09-verification-and-critic.md) |
| **Critic** | A fresh reviewer (subagent or session) that tries to break the work and must give evidence | [verification](../references/09-verification-and-critic.md#gate-6---independent-critic) |
| **STATE.md** | The local, untracked progress file in a project folder: ids, what is done, what is not | [runbook](../references/02-runbook.md#phase-0-project-folder) |
| **PAT** | Personal access token; created only by the user, optional | [safety](../references/08-safety-permissions-privacy.md) |
| **Redaction scan** | `scripts/redaction_scan.sh`: pre-publish grep for emails, hosts, ids and user-supplied terms | [safety](../references/08-safety-permissions-privacy.md#privacy-and-redaction) |
