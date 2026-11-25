---
title: Verification evidence
kind: appendix
summary: The single record of what was verified live, on which builder version and date, what the independent reviews found, and what is only locally tested.
read_when: You need to state precisely what is proven, or decide whether a change needs a live re-run.
---
# Appendix G - Verification evidence

This is the **only** place that states what was proven live. README, INDEX and the pack table link here. Per-pack status: [industries/README.md](../industries/README.md). Open gaps: [appendix F](F-known-limitations.md).

## Builder versions
| Version | Date | Live-verified | Notes |
|---|---|---|---|
| earlier revision (pre-review) | 2026-11-20 | `bfsi_banking`, `manufacturing`: 0 errors, 14 of 14 audits PASS each; the OEE measure equalled an independent recomputation | A 0% NPA ratio exposed a data-generator bug that local checks missed |
| 1.0.0 (first publish) | 2026-11-20 | `retail` 17 of 17 audits PASS; `telecom` all audits PASS; `hls_provider` 15 of 15 PASS; each 0 errors; `MEASURE()` queries and `cleanup()` exercised | Covered by the hard steps: PK uniqueness and FK orphan audits, enforced CHECKs (including an exact-decimal table CHECK), the map, `date_key_after`, `date_key_before`, unique-FK and `fk where` generators, string-literal derived columns, apostrophe escaping. The soft steps (clustering, change data feed, statistics, tags, comments, `format:`) print `WARN` rather than errors; `WARN` lines were not tabulated per run |
| 1.1.0 | 2026-11-24 | **Not re-run live** | Expression-safety gates (validate and generation share one strict check), wider destructive guards, `cleanup()` ownership check, ordering/empty-pool fixes, hardened file server and redaction scan, doc restructure. Generated SQL, audit queries and agent/page text are byte-identical to 1.0.0 (pinned in `tests/golden_sql.json`); data was compared once. Tested locally, including a fake Spark session for the guards |

If a change alters generated SQL (not just validation or guards), re-run at least `retail` on a throwaway schema and record it here.

## Original hand-built retail build (not the generated pack)
Exercised through a live Genie agent: measure questions, a derived return rate with disclosure, a Page-backed definition, cross-view questions, enriched views, schema-level data-quality monitoring. Details: [case study](E-case-study-retail-build.md).

## Independent reviews
| Review | Scope | Outcome |
|---|---|---|
| A, B (2026-11-20) | Whole repo, then packs and builder | Fixed: YAML `on:` key parsed as boolean, degenerate 0% NPA data, chained joins, a `.gitignore` rule that hid a template, SQL escaping, unguarded `CREATE OR REPLACE` and `DROP SCHEMA`, unrealistic data in six packs, a too-permissive file server, widget leakage between packs, several doc overclaims. Each has a regression test |
| C (completed 2026-11-24) | Code re-check | Critical: spec strings reached pandas `eval`, so `@pd...` could run shell commands (proved with files written to a temp folder); column `check` was unvalidated; the redaction scan let a harmless token hide a real hit; the file server followed symlinks and missed nested secret names; `cleanup()` and the overwrite guard were too narrow. All fixed in 1.1.0 with tests. Remaining items are in [appendix F](F-known-limitations.md) |
| D (2026-11-25) | Docs: a fresh reviewer answered ten retrieval questions starting from `SKILL.md`, audited claims against code, and tried to break the doc checker | No high-severity finding. Fixed: `validate` accepted specs that `check` rejected, contradictory CORS advice, links that leave the shipped folder, soft-step WARN lines not mentioned in the acceptance test, a golden pin weaker than claimed, understated data-realism gaps, checker blind spots. Remaining items are in [appendix F](F-known-limitations.md) |

## Local checks (every release)
Tests (`python3 -m unittest discover -s tests`): packs validate with 0 errors and 0 warnings, data integrity and realism, SQL and YAML rendering, notebook compilation, one regression test per defect, security behaviour (expression gates, guards with a fake Spark, live file-server requests, redaction scan evasions, `git check-ignore`), and the documentation checks (`python3 tools/check_docs.py`).

## Never verified
Genie One (full screen); certification of Pages; nested metric-view joins; REST/SDK automation (needs a user-created token); the learned Genie Ontology layer. See [appendix F](F-known-limitations.md).
