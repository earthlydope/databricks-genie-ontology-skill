---
title: Verification gates and the independent critic
kind: reference
summary: Six ordered gates from spec to Genie behaviour, the critic checklist and the definition of done.
read_when: You are about to declare a build, a pack or the repo finished.
---
# 09 - Verification and the internal critic

"Built" is not "verified". Use these gates in order. Do not announce completion until every applicable gate has a recorded result.

## Gate 1 - Spec
`validate` 0 errors **and 0 warnings**; `check` passes (PK/FK/NOT NULL/CHECK, no constant boolean/numeric columns).
Look at the data: a few rows per table, and the headline ratios (return rate, NPA, OEE, churn) must be plausible (0.5%-60%, never exactly 0 or 1).

## Gate 2 - SQL layer on the real workspace
`Done. 0 error(s).`, all `PASS` audits, expected row counts in `LOAD` lines, metric views visible, and every `WARN` line read (soft steps never count as errors). Run a **throwaway test schema** for any change to the builder itself, then drop it.
What has actually been verified live, per builder version, is recorded **once** in [appendix G](../appendix/G-verification-evidence.md); the per-pack status table is in [industries/README.md](../industries/README.md). Do not restate *status* claims (which packs or builder versions were verified) elsewhere: link to them.
A change to `genie_onto.py` invalidates the live evidence for the touched code paths: say so in the CHANGELOG and re-run a pack live if the change reaches generated SQL.

## Gate 3 - Metric views
`SELECT dim, MEASURE(m) FROM mv GROUP BY ALL` for every view; recompute at least one non-trivial measure from the fact table; compare.

## Gate 4 - Governance
Domain asset counts equal the spec; certification tags present; the agent is certified and in its domain; Pages published under the right domains with related assets.

## Gate 5 - Genie behavior
Ask every sample question. For each: (a) correct source ("1 source" or the expected metric view), (b) numbers equal your SQL, (c) disclosed assumptions (time range, derived ratios). Ask one definition question per Page in a domain-scoped chat and confirm the Page is read and cited.
File failures as findings with the fix (dimension missing, synonym ambiguity, instruction gap); fix, rebuild, re-ask.

## Gate 6 - Independent critic
Required before publishing a skill or repo, or handing over a build. Spawn a **fresh** reviewer (subagent or separate session) that has not seen your reasoning, only the artifacts.
It must try to break the work and report only findings it can support with evidence (file:line or command output), with a severity. It never modifies files.

The checklist and the output format live in one place: [templates/critic_prompt.md](../templates/critic_prompt.md). It is self-contained, so hand it to the reviewer unchanged and fill in the target path.
Its seven areas: correctness, honesty, safety, privacy (including git history), completeness, usability for another Claude (a retrieval test: ask the reviewer to answer ten realistic questions starting from SKILL.md only), licensing.
Fix every confirmed finding, re-run the gates they touch, then ask the reviewer to re-check the fixed points.

## Definition of done (copy into STATE.md)
For a repo change (full checkout only): `python3 -m unittest discover -s tests` and `python3 tools/check_docs.py` are green, packs validate and check clean, the redaction scan is clean, and the CHANGELOG says whether live evidence still applies.
For a workspace build:
```
[ ] validate 0/0, check OK        [ ] build 0 errors, audits PASS     [ ] MEASURE() reconciled
[ ] domains + tags counts match   [ ] agent certified + in domain      [ ] pages published
[ ] sample questions verified     [ ] critic findings fixed            [ ] redaction scan clean
[ ] not-done list + reasons written
```
