---
title: Spec format
kind: reference
summary: Every key of the YAML spec (tables, columns, generators, metric views, agent, pages), the expression-safety rules and an authoring checklist.
read_when: You are writing, editing or debugging a spec, or validate/check reports an error.
---
# 03 - Spec format (spec_version 1)

One YAML (or JSON) file describes a whole ontology foundation. `scripts/genie_onto.py validate` enforces everything below.
Start from `templates/spec_template.yaml`. YAML gotcha: a bare `on:` key parses as boolean `true` in YAML 1.1; the loader repairs it, but quote values like `yes`/`no`/`on`/`off` and avoid them as choice values.

## Top level

| Key | Meaning |
|---|---|
| `industry`, `title`, `description` | Identity. `industry` is snake_case. |
| `catalog`, `schema` | Defaults (override at deploy with widgets). |
| `seed`, `history_days`, `as_of` | Deterministic data. The history window ends today (rolling) unless `as_of: YYYY-MM-DD` pins it. |
| `currency` | Used by `format: currency` (default USD). |
| `domains` | List of domain names (letters, digits, space, `_`, `-`). Each becomes a governed tag key. |
| `tables`, `metric_views`, `agent`, `pages` | See below. |

## Tables

`kind` dimension|fact (default by name prefix), `rows` (a **cap** when a column draws a `unique` fk from a smaller pool), `comment` (required), `domains` (list), `cluster_by` (columns; facts), `checks` (`{name: "sql expr"}`),
`generator: calendar` (for `dim_date`, columns are injected).

### Columns
| Key | Meaning |
|---|---|
| `type` | `int bigint string date boolean double timestamp decimal(p,s)` |
| `gen` | generator, see below |
| `comment` | Column comment (required unless `hidden`) |
| `pk: true` | Primary key; must not be nullable. (A composite pk is allowed, but no foreign key may reference it.) |
| `fk: table.col` | Informational foreign key; the target must be the **whole** (single-column) primary key of its table and have the same type. `gen: date_key` adds `fk: dim_date.date_key` automatically. `where: "<pandas query on the parent>"` limits which parent rows a `gen: fk` may pick (e.g. `where: churned`). |
| `nullable: true` | Allow nulls (default false -> NOT NULL) |
| `check: "> 0"` | Column CHECK suffix (SQL and pandas compatible; no `IN`/`BETWEEN`) |
| `allowed: [..]` | CHECK `col IN (...)`; auto-filled from `choice` values; `false` disables |
| `pii: true` | Tags column `pii=true`, `data_classification=personal` |
| `classification: internal` | Column tag `data_classification` |
| `hidden: true` | Helper column used by `derived`/`lookup`; not created in the table |

### Generators
`seq` (start) | `template` ("SKU-{i:04d}") | `choice` (values, weights) | `map` (from, mapping: value->list) | `uniform` (min,max; int types give integers)
| `lognormal` (mean,sigma,min,max; right-skewed amounts) | `beta` (a,b,min,max; bounded and skewed, e.g. grades) | `poisson` (lam,min) | `bool` (p) | `fk` (fk, `unique`, `skew` for zipf-like popularity)
| `date_key` (random day in history) | `date` (`start_offset_days`, `end_offset_days`) | `lookup` (via=fk column of this table, column=parent column; denormalizes)
| `calendar` (a *table-level* `generator: calendar`, not a column generator: injects the date columns) | `date_key_after` (via, column=parent date_key, `max_days`, optional `min_days`; event after parent; clipped at the as-of date) | `date_key_before` (via, column=parent int date_key that caps the day; e.g. usage never after disconnection) | `derived` (`expr` over this table's columns; pandas-eval arithmetic, comparisons and string equality such as `(status == 'Settled')`; bool x number works; rounds to the decimal scale). Columns are generated in dependency order (`via`/`from`), derived ones last.

Rules of thumb: model skew (`skew`, `lognormal`, `poisson`) so ratios are non-degenerate; use `lookup` + `derived` to make child rows consistent with parents
(refund <= revenue, claim date >= policy date); patterns that make ratios meaningful: condition numeric columns on a category with `derived` (`(encounter_type == 'Inpatient') * stay_days`); make 'late' or 'bad' events a rare boolean times a count; never rely on `uniform` alone for tail events (a `poisson(lam=6)` days-past-due never reaches 90, so NPA was 0 - found by testing on a real workspace).

## Metric views
Names must start with `mv_`.

```yaml
mv_sales:
  source: fact_sales            # a table
  comment: "..."                # COMMENT ON TABLE after creation
  domains: [Sales]
  joins:                        # FLAT only: on-clause may reference only `source` and the join's own name
    - {name: date, table: dim_date, on: "source.date_key = date.date_key"}
  dimensions:
    - {name: order_date, expr: date.calendar_date, display_name: "Order Date", synonyms: [sale date]}
  measures:
    - {name: total_revenue, expr: "SUM(source.revenue)", display_name: "Total Revenue",
       format: currency, comment: "...", synonyms: [revenue, sales]}
```
`format`: `currency` | `integer` | `decimal` (2 places) | `rate` (4 places; use for ratios such as 0.0207). Measures must aggregate (`SUM/AVG/COUNT/MIN/MAX`); ratios of aggregates within **one** fact are fine
(`SUM(a)/COUNT(DISTINCT b)`, OEE as a product of three ratios). Boolean fact columns: `AVG(CASE WHEN source.flag THEN 1.0 ELSE 0.0 END)`.
Expressions are validated: `alias.column` must exist in the aliased table.

## Agent
`name`, `domain`, `description`, `sources` (metric views or tables), `instructions_intro`, `instructions` (list), `questions` (list).
Write instructions that (a) prefer metric views, (b) spell out every cross-fact formula, (c) fix the time-range default, (d) forbid names/PII, (e) say which dimension to use when two views disagree.

## Pages
`name`, `domain` (must be declared), `synonyms`, `description` (one line), `definition`, `business_use`, `related` (assets, metric views, the agent name).
Every cross-fact metric should have a Page with the exact formula.

## Expression safety
A spec is code, not data: **only run specs you trust.** `derived.expr`, `check`, `checks` and `where` strings are evaluated locally with pandas, and `check`/`checks` are also pasted into `ALTER TABLE ... ADD CONSTRAINT ... CHECK (...)`.
Since v1.1.0 they must pass two gates, enforced by `validate` and again inside `generate_data`, `sql_constraints` and `deploy` (so a hand-built or JSON spec cannot skip them):
1. **Characters**: letters, digits, space and `+ - * / % ( ) < > = ! , .`, plus simple `'quoted'` literals. No `@`, brackets, backslashes, `;`, `--`, `__`, or attribute access (`x.y`).
2. **AST**: only names (which must be columns of the table, or of the parent table for `where`), numbers, strings, arithmetic, comparisons, `and/or/not`, and `abs(x)`. No other calls.
`gen: template` accepts only `{i}` or `{i:04d}` style fields. Join names must be snake_case; `$$` is rejected anywhere it would end the metric-view body.
Metric-view `expr` and `on` strings are *not* evaluated locally; they are SQL that Databricks runs under your own permissions, so review them like any SQL you paste.

## Authoring checklist
1. Grain sentence in every fact `comment`. 2. Synonyms in users' words. 3. One Page per cross-fact KPI. 4. Domains = business areas (3-5), not tables.
5. Pack passes `validate` with 0 warnings and `check`. 6. Sample questions cover a measure, a ratio, a cross-view question, and a definition.
