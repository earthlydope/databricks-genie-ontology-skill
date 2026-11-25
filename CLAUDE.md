# CLAUDE.md

@AGENTS.md

Quick start for Claude Code sessions in this repo:
- Building an ontology for a user: use the skill at `skills/databricks-genie-ontology/SKILL.md`; find details via its `INDEX.md`.
- Changing the repo: follow "Job B" in AGENTS.md. The three green checks are `python3 -m unittest discover -s tests`, `python3 tools/check_docs.py`, and the pack `validate` command.
- Never commit `STATE.md`, `config.env` or anything with workspace hosts, ids or personal details.
