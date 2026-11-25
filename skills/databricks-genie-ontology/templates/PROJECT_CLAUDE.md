# <Project> - Genie ontology on Databricks

Goal: build and verify a governed Genie ontology foundation for <industry> using the `databricks-genie-ontology` skill.
Read `STATE.md` first; it says what is done and what is next. Update it after every step.

## Layout
- `spec.yaml`   the whole design (copy of an industry pack, edited)
- `STATE.md`    progress, ids, findings (LOCAL ONLY - contains workspace host/ids; never publish)
- `out/`        generated notebook cell, agent.md, pages/*.md, ui-checklist.md (run the skill's scripts from this folder: `python3 $SKILL/scripts/genie_onto.py ... spec.yaml`)
- `config.env`  optional token/host if the user consented to a PAT (LOCAL ONLY, never cat/echo)

## Rules
1. Spec first: `validate` (0/0) and `check` before touching the workspace.
2. Never type code into the notebook editor; paste (skill: references/04-browser-automation-playbook.md).
3. Prefer one notebook per spec. Build -> verify with MEASURE() -> domains (UI) -> tags -> agent (UI) -> pages (UI) -> questions.
4. Do not grant access, set policies, create tokens, or add users. Hand those over (skill: references/08-safety-permissions-privacy.md).
5. Redact before sharing anything outside this folder (scripts/redaction_scan.sh).
6. Report what was NOT done and why.
