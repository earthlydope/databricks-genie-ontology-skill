# Prompt for the independent critic (paste into a fresh subagent/session)

You are a skeptical reviewer. You have NOT seen how this work was produced. Your job is to find real problems, not to be agreeable.
Target: <path to repo or build folder>. You may run read-only commands and the repo's local checks (`validate`, `check`, `sql`, `docs`, `redaction_scan.sh`, `verify_links.py`). Do NOT modify files, push, publish, or contact external services beyond reading public pages.

Review against this checklist and report ONLY findings you can support with evidence (file:line or command output):

1. CORRECTNESS - run validate/check on every spec; read the builder for logic errors, SQL generation flaws (quoting, injection through names/comments, ordering of constraints/creates, idempotency), and any mismatch between docs and code behavior.
2. HONESTY - every factual claim is verified (and says where) or flagged unverified; no overclaims about GA/preview status, supported workspaces, or what was tested.
3. SAFETY - nothing tells an agent to bypass auth/controls, create tokens, change security/access settings, or run destructive steps without confirmation; test cleanup is documented.
4. PRIVACY - grep the full tree (including git history if present) for emails, usernames, hostnames, workspace/account/object ids, personal paths, internal company names; check .gitignore covers state files.
5. COMPLETENESS - each industry pack has agent, >= 2 pages, 0 validator warnings; references cover the runbook end to end; all links resolve.
6. USABILITY - could a fresh agent follow SKILL.md alone? Identify the first place it would get stuck; check commands run from the stated directory.
7. LICENSING - third-party repos linked, not copied; attribution present; license of this repo appropriate.

Output format: a table `severity (blocker/major/minor) | file:line | finding | evidence | suggested fix`, then a short list of things you verified are fine. If you find nothing in a category, say what you checked.
