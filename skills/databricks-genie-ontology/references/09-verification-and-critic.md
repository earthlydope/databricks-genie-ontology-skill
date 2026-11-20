# 09 - Verification and the internal critic

"Built" is not "verified". Use these gates in order. Do not announce completion until every applicable gate has a recorded result.

## Gate 1 - Spec
`validate` 0 errors **and 0 warnings**; `check` passes (PK/FK/NOT NULL/CHECK, no constant boolean/numeric columns).
Look at the data: a few rows per table, and the headline ratios (return rate, NPA, OEE, churn) must be plausible (0.5%-60%, never exactly 0 or 1).

## Gate 2 - SQL layer on the real workspace
`Done. 0 error(s).`, all `PASS` audits, expected row counts in `LOAD` lines, metric views visible. Run a **throwaway test schema** for any change to the builder itself, then drop it.
Evidence (2026-11-20): first library revision, banking and manufacturing built with 0 errors and 14/14 audit PASS each; `MEASURE()` returned plausible numbers; the OEE measure equalled an independent recomputation exactly; a 0% NPA ratio exposed a data-generator bug that local checks missed.
After two independent reviews and a fix pass, the **final** library was built live for `retail` (map, exact-decimal table CHECK, `date_key_after`, unique FK, apostrophe escaping: 17/17 PASS), `telecom` (`date_key_before`, `fk where`: all audits PASS) and `hls_provider` (string-literal derived columns, derived booleans: 15/15 PASS), each with 0 errors; `MEASURE()` queries and the new `cleanup()` were exercised too. Not built live on the final library: the other eight packs (education, cpg_fmcg, insurance, energy, supply chain, pharma, banking, manufacturing re-run) - they share the same code paths and pass local checks.

## Gate 3 - Metric views
`SELECT dim, MEASURE(m) FROM mv GROUP BY ALL` for every view; recompute at least one non-trivial measure from the fact table; compare.

## Gate 4 - Governance
Domain asset counts equal the spec; certification tags present; the agent is certified and in its domain; Pages published under the right domains with related assets.

## Gate 5 - Genie behavior
Ask every sample question. For each: (a) correct source ("1 source" or the expected metric view), (b) numbers equal your SQL, (c) disclosed assumptions (time range, derived ratios). Ask one definition question per Page in a domain-scoped chat and confirm the Page is read and cited.
File failures as findings with the fix (dimension missing, synonym ambiguity, instruction gap); fix, rebuild, re-ask.

## Gate 6 - Independent critic (required before publishing a skill/repo or handing over a build)
Spawn a **fresh** reviewer with no access to your reasoning, only the artifacts. It must try to break the work. Give it the checklist below and require evidence (file:line, command output) for each finding. Fix every confirmed finding; re-run the gates they touch; then ask the critic to re-check the fixed points.

### Critic checklist
1. **Correctness**: run `validate`/`check` on every pack; read `genie_onto.py` for logic errors, unsafe SQL generation (injection via names/comments), idempotency, and mismatches between docs and code.
2. **Honesty**: every factual claim in docs is either verified (say where) or marked unverified. Flag overclaims ("works on any workspace", "GA").
3. **Safety**: nothing instructs the agent to bypass auth/permissions, create tokens, or change security settings; destructive steps require confirmation; test cleanup present.
4. **Privacy**: grep the whole tree for emails, hostnames, ids, usernames, company-internal strings; confirm `.gitignore` covers state files.
5. **Completeness**: every industry pack has agent, >= 2 pages, a cross-fact page where relevant, 0 warnings; references cover the runbook end to end; every link resolves.
6. **Usability for another Claude**: can a fresh agent follow SKILL.md alone? Where would it get stuck? Are commands copy-pastable and correct from the stated working directory?
7. **Licensing/attribution**: referenced third-party repos are linked, not copied; credits present.

### How to run it
Use a subagent (or separate session) and give it: the repo path, the checklist, permission to run read-only commands and the local checks, and an instruction to report only confirmed findings with evidence and a severity. Do not let it modify files.

## Definition of done (copy into STATE.md)
```
[ ] validate 0/0, check OK        [ ] build 0 errors, audits PASS     [ ] MEASURE() reconciled
[ ] domains + tags counts match   [ ] agent certified + in domain      [ ] pages published
[ ] sample questions verified     [ ] critic findings fixed            [ ] redaction scan clean
[ ] not-done list + reasons written
```
