# AGENTS.md - instructions for AI agents in this repository

Two different jobs bring an agent here. Pick yours first.

## Job A: build an ontology for a user (use the skill)
1. Read [skills/databricks-genie-ontology/SKILL.md](skills/databricks-genie-ontology/SKILL.md) It is a short router.
2. Find anything else through [INDEX.md](skills/databricks-genie-ontology/INDEX.md): task table, symptom table, spec-key finder, commands.
3. Work in the **user's project folder**, not in this repo. Copy `templates/PROJECT_CLAUDE.md` and `templates/STATE.md` there first and keep STATE.md current.
4. Hard limits (full text: [safety](skills/databricks-genie-ontology/references/08-safety-permissions-privacy.md)): the user signs in; never create tokens; never grant access or set policies, masks or row filters; synthetic data only; confirm destructive steps; a spec is code, run only specs you read.

## Job B: change this repository
Layout and rules:
| Where | Rule |
|---|---|
| `skills/databricks-genie-ontology/scripts/genie_onto.py` | One file, embedded verbatim in generated notebooks: no Spark import at module level, Python 3.9+ syntax only. Bump `__version__` and the CHANGELOG together |
| `industries/*.yaml` | Must pass `validate` with 0 errors and 0 warnings and `check`. Generated SQL is pinned by `tests/golden_sql.json`: changing it is deliberate, then re-run a pack live and record it in [appendix G](skills/databricks-genie-ontology/appendix/G-verification-evidence.md) |
| `references/` (core, files named `NN-slug.md`) | Short, task-shaped, front matter required. Anything not needed to build goes to `appendix/` (files named by letter) |
| One home per fact | Verification status lives in appendix G and the pack table; link, never restate. Pack counts, generator names, subcommands and the version are checked against the code |
| Privacy | No emails, hosts, workspace or object ids, usernames. `STATE.md` and `config.env` stay local and untracked |

Definition of done for any change (all from the repo root):
```bash
python3 -m unittest discover -s tests          # needs pandas numpy pyyaml
python3 tools/check_docs.py --write            # refreshes the INDEX catalog, then must print "docs OK"
python3 skills/databricks-genie-ontology/scripts/genie_onto.py validate skills/databricks-genie-ontology/industries/*.yaml
bash skills/databricks-genie-ontology/scripts/redaction_scan.sh . <your-private-terms>
```
Then add a CHANGELOG entry that says whether live evidence still applies. Before publishing, run an independent critic ([Gate 6](skills/databricks-genie-ontology/references/09-verification-and-critic.md#gate-6---independent-critic)); template prompt: `skills/databricks-genie-ontology/templates/critic_prompt.md`.
Details for humans: [CONTRIBUTING.md](CONTRIBUTING.md).
