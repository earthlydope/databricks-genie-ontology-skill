---
title: Known limitations and backlog
kind: appendix
summary: Understood defects and unverified areas that are deliberately not fixed yet, each with evidence, workaround and a suggested fix.
read_when: A pack looks unrealistic, a constraint is missing, or you are choosing what to improve next.
---
# Appendix F - Known limitations and backlog

Source: the second independent code review (completed 2026-11-24) plus earlier notes. Items fixed in v1.1.0 are in CHANGELOG.md at the repository root, not here.
Severity: M = affects correctness or data realism, L = cosmetic or edge case.

## Builder (`scripts/genie_onto.py`)
| # | Sev | Limitation | Evidence | Workaround | Suggested fix |
|---|---|---|---|---|---|
| F1 | M | `date_key_after` and `date_key_before` columns get no automatic foreign key to `dim_date`, so no FK constraint and no orphan audit, although metric views join `dim_date` on them (for example claims, billing and returns facts) | Review of `bfsi_insurance`, `hls_provider`, `retail` | Add `fk: dim_date.date_key` by hand (`date_key_after` values are already clipped at the as-of date, so they stay inside the calendar) | Add both generators to the automatic FK rule |
| F2 | M | `date_key_before`: if the parent's cap date falls before the calendar start, the first calendar day is returned (after the cap) and `check` still passes | Reviewer's fixture with caps in 2020 and `as_of` 2025 | Keep caps inside the history window | Flag such rows in `check_data` |
| F3 | L | The managed marker is not spec-specific: two packs deployed into one schema can replace each other's same-named tables. Metric views carry no marker: the `metric_views` step runs `CREATE OR REPLACE VIEW` on any existing view with the same name, and `cleanup()` drops them by name | Code reading (reviews 2026-11-24) | One schema per spec | Put the industry in the marker value; verify a marker for metric views live |
| F4 | L | `features` and `tags` steps alter tables without a marker check (deliberate, so the real-tables path works) | Code reading | Use them only on objects you own | Optional guard flag |
| F5 | L | A few malformed specs crash with a Python error instead of a validation message: a self-referencing fk, a hidden primary key, `history_days: 0`, `date_key_before` whose `column` is the via table's pk | Reviewer's fixtures | Run `validate` first and read errors | Add validator rules |

## Packs (data realism)
Demo-data issues of one class: a child row dated before its parent's start date, or a repeated pair. Measures still compute, but a careful reviewer will spot them. Reproduced 2026-11-25 with `as_of` 2026-11-24.
| # | Sev | Pack | Limitation | Rows affected |
|---|---|---|---|---|
| F6 | M | `telecom` | Usage rows precede the subscriber's `activation_date`; churn events precede it too | 1,457 of 8,000 usage rows; 21 of 128 churn rows |
| F7 | M | `education` | The same student-course pair is enrolled more than once, unlabelled | 1,327 of 7,000 enrollments |
| F14 | M | `retail` (a Live pack) | Sales and returns dated before the customer's `signup_date` | 1,275 of 5,000 sales; 99 of 400 returns |
| F15 | M | `bfsi_banking` (a Live pack) | Transactions and loan snapshots dated before the customer's `onboarding_date` | 1,329 of 9,000 transactions; 370 of 2,500 snapshots |

Fix pattern: use the parent's start date as a lower bound for child dates (a `date_key_after` from a parent date key; the customer start columns are currently plain dates, so the parent needs a date-key column), or draw the parents' start dates earlier than the history window. Changing any of these alters generated data and SQL digests: re-run the pack live afterwards ([appendix G](G-verification-evidence.md)).
Other packs have not been scanned for this class systematically.

## Verification gaps
| # | Area | Status |
|---|---|---|
| F8 | Six packs (`cpg_fmcg`, `bfsi_insurance`, `hls_pharma_lifesciences`, `energy_utilities`, `supply_chain_logistics`, `education`) | Local checks only; never built on a workspace |
| F9 | Builder v1.1.0 | Guards and validation are covered by tests with a fake Spark session; not re-run on a live workspace ([appendix G](G-verification-evidence.md)) |
| F10 | Genie One (full screen), certification of Pages, nested (snowflake) metric-view joins, REST/SDK automation | Not exercised |
| F11 | `CREATE OR REPLACE VIEW` possibly resetting tags | Precaution only; re-run the tag step after any view rebuild |
| F12 | The learned Genie Ontology layer | Gated preview; not built or tested here |
| F13 | Notebook re-run behaviour (`domains_created_<industry>`) | The generated text is tested; the widget flow was exercised live only on the original build |
