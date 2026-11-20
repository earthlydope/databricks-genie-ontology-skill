// Read build output from a Databricks notebook page. Output is virtualized, so scroll the notebook container
// stepwise and search document.body.innerText. Returns a compact JSON summary.
// Sentinels printed by genie_onto.deploy(): OK / ERROR / WARN / LOAD / PASS / FAIL / "Done. N error(s)."
(async () => {
  const sc = document.querySelector('.notebook-scrollable-container');
  const lines = new Set();
  for (let y = sc.scrollHeight; y >= 0; y -= 250) {
    sc.scrollTop = y;
    await new Promise(r => setTimeout(r, 300));
    for (const l of document.body.innerText.split('\n')) {
      if (/^(OK|LOAD|ERROR|WARN|PASS|FAIL|Done)\b/.test(l)) lines.add(l);   // anchored: the cell SOURCE also contains words like "Exception"
    }
  }
  const all = [...lines];
  const pick = p => all.filter(l => l.startsWith(p)).map(l => l.slice(0, 220));
  return JSON.stringify({
    total: all.length,
    ok: pick('OK').length, loads: pick('LOAD'),
    errors: pick('ERROR').slice(0, 8), warnings: pick('WARN').slice(0, 5),
    pass: pick('PASS').length, fails: pick('FAIL'),
    done: pick('Done'),
  });
})();
