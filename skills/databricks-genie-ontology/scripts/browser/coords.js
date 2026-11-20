// Convert a DOM element to screenshot-frame click coordinates.
// The screenshot frame (e.g. 800 wide) differs from the CSS viewport (window.innerWidth), so
//   frame = css * (FRAME_WIDTH / window.innerWidth)
// Usage: set TEXT to the visible text of a link/button, run, then click the returned (x, y) with the computer tool.
(async () => {
  const TEXT = 'Create';          // visible text to find
  const SELECTOR = 'a,button,[role=tab],[role=menuitem]';
  const FRAME_WIDTH = 800;        // width reported with your last screenshot
  const el = [...document.querySelectorAll(SELECTOR)].find(e => e.textContent.trim().startsWith(TEXT));
  if (!el) return 'not found';
  el.scrollIntoView({ block: 'center' });
  await new Promise(r => setTimeout(r, 400));
  const r = el.getBoundingClientRect(), s = FRAME_WIDTH / window.innerWidth;
  return JSON.stringify({ text: el.textContent.trim().slice(0, 40), x: Math.round((r.x + r.width / 2) * s), y: Math.round((r.y + r.height / 2) * s) });
})();
