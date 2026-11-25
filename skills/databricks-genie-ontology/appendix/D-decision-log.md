---
title: Decision log
kind: appendix
summary: The design decisions behind the skill, why each was made, the evidence, and what would justify revisiting it.
read_when: You are tempted to change an approach (flat joins, paste-not-type, marker guard, spec-first) and want to know why it is the way it is.
---
# Appendix D - Decision log

Format: decision, why, evidence, revisit when. Newest last.

| # | Decision | Why | Evidence | Revisit when |
|---|---|---|---|---|
| 1 | **Spec-first**: one YAML generates tables, data, metric views, tags, agent text and Pages text | Re-runnable, reviewable, one place to fix a defect for all industries | A fix in `genie_onto.py` propagated to every pack; 11 packs from one engine | Never for SQL-expressible objects |
| 2 | **UI only for what has no SQL**: Domains, agent, agent certification, Pages | No public SQL path was found for these; browser automation is slower and fragile | [Case study](E-case-study-retail-build.md): about 5 min of SQL vs about 40 min of UI | A supported API/SQL for Domains, agents or Pages exists |
| 3 | **Flat joins only** in metric views | Chained (snowflake) joins were unverified; a `lookup` generator denormalises the key into the fact | Validator rejects chains; every pack builds | A chained join is verified live |
| 4 | **Cross-fact KPIs live in Pages + agent instructions** | A measure can aggregate only its own source plus flat-joined dimensions | Return rate answered correctly with a disclosure line | Metric views support multi-source measures |
| 5 | **Paste, never type, into the notebook editor** | Monaco auto-indent/auto-close corrupts typed code | Typed attempts were mangled; synthetic paste worked at 72 KB (larger cells: verify after pasting) | The editor stops auto-formatting |
| 6 | **Browser first, token optional** | Cookie-authenticated REST returned 401; a token must be created by the user | Probed once, boundary respected | The user consents to a PAT |
| 7 | **Managed marker + refuse to replace unmarked tables** | `CREATE OR REPLACE` on a user's table is data loss | Review finding; guard covers `tables`, `load`, `constraints` since v1.1.0 | Marker should become spec-specific (see [F](F-known-limitations.md)) |
| 8 | **Widget names carry the pack name** | Databricks keeps widget values per name, so a reused notebook inherited another pack's schema | Seen live | Never |
| 9 | **Tag re-run runs only the tag step** | A full re-run would reload data and could wipe UI edits | Phase 6 of the [runbook](../references/02-runbook.md#phase-6-tags) | Never |
| 10 | **Hardened throwaway file server** (127.0.0.1, one origin, token path, no listing, no symlinks, no secret names) | Large cells must reach the page; a permissive server leaks local files to any site | Two review rounds; behaviour tests in `tests/test_security.py` | A safer transport exists |
| 11 | **`format: rate` (4 places) for ratio measures** | Two decimals turned 0.0207 into 0.02 | Live check | Never |
| 12 | **Retail pack independently written**; the community demo is linked, not copied | The demo publishes no licence | 8-word overlap scan found only short functional phrases | The demo adds a licence |
| 13 | **CI shipped as `ci/validate.yml.example`** | The push token lacked the `workflow` scope | Push rejected once | The owner copies it into `.github/workflows/` |
| 14 | **Spec strings are restricted (characters + AST) and re-checked before eval/DDL** (v1.1.0) | A spec is code; `@pd...` reached `os.system` through pandas eval in review | Reproduced by the reviewer; blocked by tests | A sandboxed evaluator replaces pandas eval |
| 15 | **Docs are a router, an index and an appendix** (v1.1.0) | A fresh agent should read about 200 lines to get going and find any detail by symptom, task or spec key | `tools/check_docs.py` enforces links, anchors, front matter, size limits, catalog freshness | Retrieval stays slow in practice |
| 16 | **One canonical home per fact**: verification status in [appendix G](G-verification-evidence.md) and `industries/README.md`; everything else links | Counts and claims drifted between three documents | Checker compares pack counts and the CHANGELOG version with the code | Never |
