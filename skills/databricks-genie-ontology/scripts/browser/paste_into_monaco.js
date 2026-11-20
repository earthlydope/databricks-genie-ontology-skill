// Paste text into the last (or a chosen) notebook cell WITHOUT typing, so Monaco cannot auto-indent / auto-close.
// Run inside the Databricks notebook page (javascript_tool). Then focus the cell and press shift+Return to run.
//
// Usage A (small text inline):   set CODE below.
// Usage B (large file):          serve it from a throwaway local server with CORS and set URL
//                                 (python3 -m http.server + a handler adding Access-Control-Allow-Origin: *),
//                                 fetch with credentials:'omit'. Stop the server afterwards.
(async () => {
  const CODE = null;                       // e.g. "print('hello')"
  const URL = null;                        // e.g. "http://127.0.0.1:8765/build.cell.py"
  const CELL_INDEX = -1;                   // -1 = last cell, else index into the list of editors
  const text = CODE ?? (await (await fetch(URL, { credentials: 'omit' })).text());
  const editors = [...document.querySelectorAll('.monaco-editor')];
  const ed = editors.at(CELL_INDEX);
  ed.scrollIntoView({ block: 'center' });
  const ta = ed.querySelector('textarea');
  ta.focus();
  const dt = new DataTransfer();
  dt.setData('text/plain', text);
  ta.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 1500));
  return JSON.stringify({ pasted: text.length, editors: editors.length });
})();
