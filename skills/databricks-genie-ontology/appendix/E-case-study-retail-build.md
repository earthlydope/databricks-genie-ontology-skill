---
title: Case study - the original retail build
kind: appendix
summary: What the first end-to-end build on a real workspace contained, how long each part took, what went wrong, and how it was fixed; the source of most gotchas.
read_when: You want a concrete picture of a finished build, realistic timings, or the story behind a rule.
---
# Appendix E - Case study: the original retail build

The skill was extracted from one hand-driven build of a Northwind-style retail demo on a personal Databricks workspace (2026-11-20). Object ids and the workspace host were kept only in a local `STATE.md` and are not published.
The published `retail` pack is an independent re-authoring of the same idea; it is not the build described here.

## What existed at the end
| Layer | Objects |
|---|---|
| Tables | 7 in one schema: 3 facts (sales, returns, inventory) and 4 dimensions (date, product, store, customer); about 9,400 synthetic rows in total |
| Metric views | 3 (sales performance, customer returns, inventory health) |
| Enriched views | 2, drafted by Genie Code, reviewed, run by hand: a customer view (tenure, lifetime revenue and returns, return rate, value tier) and a product view (average price, margin, price band) |
| Governance | 4 domains (Sales, Customer, Supply Chain, Finance), certification tags, domain tags, `COMMENT`s on the metric views, 17 `CHECK` constraints, liquid clustering on 3 facts, change data feed and statistics on all 7 tables |
| UI objects | 1 Genie agent (5 sources, certified, in the Sales domain), 3 Pages, schema-level Data Quality Monitoring (anomaly detection on, alerts off) |

## Timeline
Only two durations were recorded in the original build; the rest was not timed.
| Part | Time | Notes |
|---|---|---|
| SQL layer (tables, data, metric views, constraints, tags, audit) | about 5 min of compute | Notebook cells were pasted, never typed |
| 4 Domains, the agent and 3 Pages | about 40 min of browser time | The slowest part; most gotchas live here |
| Sign-in, recon, data quality, enrichment | not timed | The user signs in; an "automated control detected" banner appeared and was harmless; Genie Code drafted the enrichment SQL, a human reviewed and ran it |

## What Genie did with it (observed)
1. A revenue question was answered from the metric view ("1 source").
2. A definition question in a domain-scoped chat read the Page and cited it, with a note that Pages are not certified.
3. A cross-fact return rate was computed from two measures and disclosed as derived, because the agent instructions spelled out the formula.
4. A region question failed first: returns had no region dimension. Adding `customer_region` and an instruction on which region to use fixed it.
5. After the enriched views were attached, a question by customer value tier was answered with figures equal to the direct SQL.

## Findings that became rules
| Finding | Became |
|---|---|
| Typed code in the notebook was mangled | [Paste, never type](../references/04-browser-automation-playbook.md#notebooks-the-workhorse) |
| A cross-region question exposed a missing dimension | Spell out which dimension to use when two views disagree ([spec format](../references/03-spec-format.md#agent)) |
| Genie labels Pages "not certified" | Tell the user; certifying Pages is untested ([concepts](../references/01-concepts-and-architecture.md)) |
| A stray key press opened the account menu | Focus the editor first; never click Log out ([gotchas](../references/05-gotchas-and-fixes.md#ui--automation)) |
| Cookie REST returned 401 | A boundary, not a puzzle ([safety](../references/08-safety-permissions-privacy.md)) |
| Policies, masks and sharing are security settings | Left to the user and handed over as statements ([safety](../references/08-safety-permissions-privacy.md)) |

## Not done in the original build (and why)
Row filters, masks and ABAC policies (security, the owner's decision); per-table data profiling (it creates monitor tables inside the schema); full-screen Genie One (opens a popup the browser pane blocks); granting access to a second account (declined).
