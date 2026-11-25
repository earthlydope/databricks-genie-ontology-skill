---
title: Concepts and architecture
kind: reference
summary: What Genie ontology, metric views, domains, Pages and certification are, which layer this skill builds, and how Genie was observed to answer.
read_when: You need the vocabulary, or must tell a user what is GA or preview and what this skill does and does not deliver.
---
# 01 - Concepts and architecture

## The layers

> Release status (GA vs preview) of each piece changes. Databricks' own readiness repo describes the learned layer as gated preview built on a foundation that is "largely GA" (as of 2026-11-20, per that repo). Treat that as a pointer, not a guarantee: check the current docs for domains, Pages and Genie One in the user's workspace before promising anything.

```
Genie One / Genie agents (chat)            <- what users talk to
        |  answers using
Genie Ontology (learned context)           <- gated preview: inferred from usage, metadata, freshness
        |  is fed by
Unity Catalog Business Semantics           <- what THIS skill builds
   metric views | domains | Pages | certification | tags | comments | PK/FK
        |
Unity Catalog tables (Delta) + governance (permissions, lineage, data quality)
```

- **Metric view**: a Unity Catalog view defined in YAML (`CREATE VIEW ... WITH METRICS LANGUAGE YAML`). Defines dimensions and measures once;
  queried with `SELECT dim, MEASURE(measure) FROM mv GROUP BY ALL`. Works from SQL, notebooks, dashboards, Genie. Spec version used here: `1.1`.
- **Domain**: a browsing/grouping layer backed by a *governed tag* whose key is the domain name (key-only, empty value). Assets are placed in domains by tagging.
  Created in the UI (Discover > Create > Create domain, Source = New tag); a domain is a Draft until published.
- **Page**: a governed business definition (name, owner, domain, synonyms, description, rich-text body, related assets). Genie reads published Pages as authoritative context.
  Genie still labels Pages "not certified" in answers (treats them as guidance) - observed; certifying Pages was not tested.
- **Certification**: tag `system.certification_status = certified|deprecated` on tables/views/dashboards/agents...; certified assets rank higher and show a badge.
  Genie agents are certified in the UI (agent kebab > Assign certification).
- **Genie agent (space)**: a configured chat surface: description, general instructions, sample questions, data sources (tables/metric views/SQL functions), SQL examples.
- **Genie One**: the full-screen chat across agents, dashboards, metric views, Pages. Its launch uses a popup that the browser pane blocks; a user click is needed.
  A domain page's "Ask Genie" opens a domain-scoped Genie chat in a side panel and works for testing Pages.

## How answers were observed to work

1. A question about a metric ("revenue last quarter by category") is answered from the attached **metric view** via generated SQL ("1 source").
2. A *definition* question ("what does total revenue mean?") makes the domain chat **read the Page** (`Finance.Total Revenue`) and cite it, with a caveat that Pages are not certified.
3. A **cross-fact ratio** (return rate) is computed on the fly from two measures when the agent instruction spells out the formula; the answer states it is not a stored measure.
4. If a dimension is missing from one view (returns had no region), the agent says it cannot answer and proposes alternatives. Add the dimension and an instruction on which one to use.

## Design principles the skill encodes

- **Star schema + informational PK/FK.** UC PK/FK are not enforced but let Genie/BI infer joins. `CHECK` and `NOT NULL` *are* enforced.
- **Comments everywhere.** Table and column comments are the "inferred context" Genie reads first.
- **Measures defined once, with synonyms** in the language users speak (GMV, ARPU, NPA).
- **Metric views over raw tables** for the agent. Attach raw tables only if you deliberately want ad hoc joins.
- **Flat joins.** Each metric-view join references only `source` and its own alias. Denormalize keys into the fact table.
- **Cross-fact metrics live in Pages + agent instructions.**
- **Synthetic data only in demos.** Tag direct identifiers `pii`; never load real PHI/PII into a demo workspace.

## Non-goals

- Granting access, row filters, column masks, ABAC policies (security; user's call; see [safety](08-safety-permissions-privacy.md)).
- The learned ontology layer. Check Databricks' current docs/availability and do not claim it.
- Replacing a lakehouse pipeline: the synthetic generator is for demos and tests.
