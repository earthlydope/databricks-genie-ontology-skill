---
title: Browser automation playbook
kind: reference
summary: How to drive the Databricks UI reliably: paste instead of type, coordinates, timing, DOM reads, notebooks, Catalog Explorer, Domains, Pages, Genie agents.
read_when: You must do a UI-only step, or a click, paste or read misbehaves.
---
# 04 - Browser automation playbook (Databricks UI)

Learned by driving a real workspace with a Chromium-based browser pane (works the same with a Chrome extension toolset).
Principle: **read with DOM/JS, act with real input events, verify by reading again.**

## Session and auth
- The user signs in. You cannot, and must not, type credentials. Login page: `https://login.databricks.com/` (Free/trial) or the workspace host. After sign-in the URL carries `?o=<workspace id>`.
- A banner says "Automated browser control detected ... does not support automated browser control". Mention it to the user and let them decide; in our runs nothing was blocked by it.
- Cookie-authenticated `fetch('/api/2.0/...')` from the page returns **401 "Credential was not sent"**. That is a deliberate boundary: do not look for ways around it.
  A personal access token, created by the user (never by you without consent), enables REST/SDK; it is optional and this skill does not depend on it.
- Pages cannot open popups/new tabs from your clicks (e.g. "Try Genie One", "Configure for schema"). Navigate to the target URL yourself, or ask the user to click.
- Some tools show an "OS clipboard was written" notice when page scripts copy: mention it to the user if it happens.

## Coordinates and timing
- Screenshot frame vs CSS viewport differ (e.g. 800x600 frame for a 1024x768 viewport). Convert: `frame = css * (800 / window.innerWidth)`.
  Get a precise click target with `getBoundingClientRect()` (`scripts/browser/coords.js`), then click by frame coordinates. Or click by `ref` from `find`/`read_page`.
- A screenshot taken immediately after an action often shows the **previous** state. `wait 2` first. If clicks seem to do nothing, take a fresh screenshot before the next coordinate click (the tool refuses stale coordinates after layout changes).
- Use `get_page_text` / `read_page` / JS `innerText` for verification; keep screenshots at scale 0.5-0.6.
- Batch independent steps with `browser_batch`, but add waits after menus and dialogs.

## Notebooks (the workhorse)
- Create: `/editor/notebooks/create?parentId=<folder id>&o=<ws>` opens a new Python notebook with an empty focused cell. (Or Workspace > Create > Notebook.)
- **Never type code** into the cell: Monaco auto-indents, auto-closes brackets/quotes and pops suggestions (Enter accepts a suggestion). Paste instead:
  `scripts/browser/paste_into_monaco.js` dispatches a `paste` event with a `DataTransfer` on the editor's hidden textarea. Pasted successfully at 72 KB (the largest cell tested in the original build). Generated cells are now about 72-80 KB (`notebook` prints a note above 72,000 characters): after pasting, read the cell back and compare its length, or import the notebook file instead of pasting.
- Large payloads from your machine: serve them from the hardened throwaway server `scripts/browser/serve_files.py <dir> <port> <workspace-origin>` (127.0.0.1 only, CORS limited to that one origin, random path token, no directory listing, refuses folders holding `config.env`/`STATE.md`/`.git`)
  and fetch from the page (`fetch('http://127.0.0.1:PORT/<token>/file',{credentials:'omit'})`). Script-tag loading is blocked by the page. Copy only the generated files into a fresh folder, and stop the server afterwards (`pkill -f serve_files.py`).
  Native Cmd+V from synthetic key events does **not** paste, and `navigator.clipboard.readText()` is permission-denied.
- Run: focus the cell textarea (JS `.focus()`), press `shift+Return`. Run all: toolbar play button. Insert a cell below: `Escape`, `b`, `Return`.
  Make sure focus is in the editor first (a stray key once opened the account menu: close with Escape; never click "Log out").
- Read results: output is virtualized. Scroll `.notebook-scrollable-container` stepwise and match `document.body.innerText` (`scripts/browser/read_cell_output.js`).
  Key off sentinels: `Done. N error(s).`, `PASS`/`FAIL`, `OK`/`ERROR`/`WARN`. Words like `Exception` also appear in the *source* of the cell: match anchored lines (`^ERROR `).
- The code cell is Python: an `f"""..."""` containing YAML braces `{...}` must double them (`{{...}}`) or it raises `NameError: name 'x' is not defined`.
- Rename a notebook from the **workspace folder listing** (right-click row > Rename; the text is preselected, just type, then OK). Renaming from the notebook tab title mangles the name.
- Move to Trash asks for confirmation naming the item: read the dialog before confirming; Trash is recoverable for 30 days.
- A "Parameters (Widgets) moved to a side panel" banner appears: ignore.

## Catalog Explorer
- URL pattern: `/explore/data/<catalog>/<schema>/<table>?o=<ws>`. Table page tabs: Overview, Sample Data, Details, Permissions, Policies, History, Lineage, Insights, Quality.
- Schema page Details tab > Advanced: **Data Quality Monitoring** (Enable), Predictive Optimization (often inherited Enabled). Enabling opens a dialog with an Anomaly detection toggle; Alerts is separate (leave off unless asked, it notifies people). Save.
- The table's "Quality > Enable" link opens a new tab (blocked); use the schema Details route.
- Table page shows tags (domain, Certified, custom), column masks and row filters (security: do not set).

## Discover: domains and pages
- Domains: `/search/discover` > Create (top right) > Create domain. Dialog: Source "New tag" (default), Name, optional subtitle/description/contacts. Create, then **Publish**.
  Domain page > kebab > **Add to domain** (Workspace tab lists recents such as the agent) assigns non-table objects. Tables/views are tagged by SQL.
- Pages: Create > Create page (`/discover/pages/new`). The Genie Code panel opens a few seconds late and squeezes the form: close it (X) before editing.
  Click the title text to edit; **Domain** is a combobox (open, wait, pick); **Synonyms**: click `+`, type, Enter, and the `+` moves right after each chip;
  **Description** is a plain textarea; **Body** has template headings (Definition / Business use) and typed text lands in the last block;
  **Add related asset** opens a search popup (type the name, first hit). Publish top-right. A new page gets an id in the URL: record it.
- Typed text can silently land in the wrong field if a layout shift happens mid-batch. After each form section, screenshot (after waiting) before continuing.

## Genie agents
- Genie Agents > **New** > "Select tables manually" > filter **Metric views** > hover/click rows to tick > **Create manually**. The agent opens with an auto-generated name.
- Configure panel tabs: About (Description pencil; **Common questions** pencil: type + Enter per question, Save), Resources (Knowledge: **Add** > Table | Metric View | SQL Function), Instructions (textarea; Save), Examples (SQL examples).
- Instructions textarea: select all (`cmd+a` inside it) and retype the **whole** text; partial inserts at the caret land mid-bullet.
- Kebab (top right): Export to metric view, Clone, **Assign certification**, Move to trash, Send feedback. Certification success toast confirms.
- The agent page title is not editable; rename in the Workspace listing. Config panels persist across navigations: close them (X) or they squeeze the next page.
- Sidebar sparkle icon toggles the Genie Code panel; it persists across pages.

## Genie Code panel
Use it to draft; extract the answer with JS (`[...document.querySelectorAll('pre, code')]` longest), review it, then run it yourself in a notebook ([enrichment pattern](07-genie-code-enrichment.md)).

## Quick recipes
- Wait for completion without polling the screenshot: `wait 10` in a batch of 3-6, then one JS read.
- Find a row's click point: `getBoundingClientRect` on the `<a>` with that text, multiply by `800/innerWidth`.
- Dialog stuck? `Escape`, re-screenshot, retry once; if still stuck, report and ask rather than clicking around.
