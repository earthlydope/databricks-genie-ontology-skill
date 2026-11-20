# 05 - Gotchas and fixes (symptom -> cause -> fix)

Each row was hit for real unless marked *(precaution)*.

## Build / SQL

| Symptom | Cause | Fix |
|---|---|---|
| `NameError: name 'name' is not defined` when running a cell that creates a metric view | The YAML sits inside a Python `f"""..."""`; `{name: ...}` is read as an f-string expression | Double the braces `{{...}}` or build the YAML with concatenation (the builder does) |
| Every join in a metric view fails / `on` missing | PyYAML (YAML 1.1) parses bare `on:` as boolean `True` | Loader repairs it; quote or use `join.on` via the spec loader; never hand-load specs with plain `yaml.safe_load` |
| Question like "which region has the highest revenue but also high returns" answers "returns have no region" | The returns metric view had no region dimension; the sales view's `region` meant *store* region and returns have no store | Add `customer_region` to both views; add an agent instruction: "for region comparisons across revenue and returns use customer_region in both" |
| Ratio measure is always 0 (e.g. NPA 0%) | Synthetic tail event never occurs (Poisson days-past-due never > 90) | Use a long-tailed generator (`lognormal`); the checker now fails constant boolean/numeric columns |
| Cross-fact KPI (return rate, loss ratio, churn rate, SAIDI) cannot be a measure | A measure aggregates only its own source + joined dimensions | Page with the exact formula + an agent instruction; Genie combines two measures and says it did |
| A comment containing `'` or `\` breaks the DDL | Spark SQL string literals use backslash escapes | The builder emits `\'` and `\\` and flattens newlines (live-verified with an apostrophe in a table comment) |
| Build refuses with "already exists and was not created by genie_onto" | Safety guard: tables carry the `genie_onto.managed` property and unmanaged ones are never replaced | Use a new schema, or `force=True` only if you really mean to replace |
| JSON-embedded spec behaves differently from the YAML one | JSON turns non-string `map` keys into strings | Fixed: `normalize()` stringifies map keys; a test covers it |
| Metric view `CREATE` fails on a `format:` block | `format` keys vary by release | Builder retries without `format`; add formatting later in the metric view YAML editor in Catalog Explorer |
| Chained join `account.customer_key = customer.customer_key` | Snowflake joins need nested joins in metric views (flat chaining unverified) | Denormalize the key into the fact (`gen: lookup`); the validator rejects chained joins |
| `CREATE OR REPLACE TABLE` on a parent fails when children reference it | FK constraints on children | Drop child FKs first (the builder does, quietly, only when the table exists) |
| Tags missing after rebuilding a metric view *(precaution)* | `CREATE OR REPLACE VIEW` may reset tags; not conclusively verified | Re-run the tag step after any view rebuild |
| `ADD CONSTRAINT ... CHECK` fails | Existing rows violate the rule | That is the point: the ERROR line is a data-quality finding; fix data or rule |
| Primary key add fails | Column nullable | Columns are created `NOT NULL`; make sure data has no nulls |
| First run prints `TABLE_OR_VIEW_NOT_FOUND` warnings on drop-constraint | Nothing to drop yet | Fixed: builder checks `tableExists` first |
| Re-using one notebook for a second pack built into the first pack's schema (seen live) | Databricks keeps widget values per widget name | Fixed: generated widget names carry the pack name (`schema_name_<industry>`); still prefer one notebook per spec |

## UI / automation

| Symptom | Cause | Fix |
|---|---|---|
| Pasted/typed code is mangled (extra indents, doubled quotes) | Monaco auto-indent/auto-close | Paste with a synthetic paste event; never type code |
| Cmd+V does nothing; `clipboard.readText` denied | Synthetic key events do not paste; clipboard read needs permission | Use the synthetic paste event with `DataTransfer` |
| `Failed to fetch` loading a local file from the page | CORS/private-network preflight on first attempts | Server with `Access-Control-Allow-Origin: *` and `Access-Control-Allow-Private-Network: true`, `credentials:'omit'`; retry once. Script tags are blocked |
| Output not found by `innerText` | Notebook output is virtualized | Scroll `.notebook-scrollable-container` in steps (`read_cell_output.js`) |
| "Exception" found in output but run was fine | The cell **source** contains the word | Match anchored lines `^ERROR ` / `Done\. \d+ error` |
| Clicks land in the wrong place | Screenshot frame != CSS viewport | `coords.js`; click by ref when possible |
| Screenshot shows old state | Lag of one action | wait 2 s, re-screenshot |
| Form text went to the wrong field | A side panel (Genie Code) opened late and shifted layout | Close panels first; screenshot after each section |
| Page body text appears in an unexpected block | Page editor appends at the last block | Accept single block, or add a short heading line; content still reads correctly |
| Domain dropdown selects the wrong option | Dropdown opened/closed twice by a batched click | Open, wait 2 s, click once, screenshot |
| Agent page title cannot be edited | Rename lives in the Workspace listing | Right-click row > Rename |
| Notebook title mangled after renaming from the tab | `Cmd+A` did not select the input | Rename from the folder listing |
| New tab/popup requested by the page does nothing | Pane blocks popups from synthetic input | `navigate` to the URL, or ask the user to click |
| A stray key opened the account menu | Focus was not in the editor | Focus the editor via JS before keys; Escape to close; never press Log out |
| Genie chat input rejects typing | Focus in the wrong panel | Click the input first; use the suggested-question rows to submit |

## Genie behavior

| Observation | Meaning | Action |
|---|---|---|
| Answer cites "glossary page that isn't marked as certified" | Pages are guidance; agents/views are certifiable | Say so to the user; certifying Pages was not tested |
| Agent says it cannot compute X | Missing dimension or measure | Add to the metric view; re-test; update instructions if two views disagree |
| Agent invents a time range | Instruction missing | Add "default to the trailing 12 months and state the range used" |
| Return-rate style answers include a disclosure line | Instruction asked for it | Keep: it is the audit trail for derived ratios |
