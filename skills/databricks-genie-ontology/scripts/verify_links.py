#!/usr/bin/env python3
"""Verify every URL in the markdown files under a directory.

    python3 scripts/verify_links.py [dir]            # default: the skill directory

GitHub repo URLs are checked with `gh api repos/OWNER/REPO` when `gh` is installed (reports archived, license, last push);
everything else is checked with a HEAD/GET request. Prints one line per URL and exits 1 if any failed.
Run before publishing and occasionally afterwards: repositories get renamed, archived or deleted.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
urls = {}
for d, _, files in os.walk(root):
    for f in files:
        if f.endswith(".md"):
            for u in re.findall(r"https?://[^\s)>\]`|\"']+", open(os.path.join(d, f), encoding="utf-8").read()):
                urls.setdefault(u.rstrip(".,;:"), set()).add(os.path.relpath(os.path.join(d, f), root))

gh = shutil.which("gh")
bad = 0
for u in sorted(urls):
    if re.search(r"//(127\.0\.0\.1|localhost)\b|PORT|<|>", u):  # placeholders and local examples
        continue
    m = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?", u)
    if m and gh and m.group(1) not in ("topics", "orgs", "features", "marketplace"):
        r = subprocess.run([gh, "api", f"repos/{m.group(1)}/{m.group(2)}"], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAIL  {u}  ({r.stderr.strip()[:80]})")
            bad += 1
            continue
        j = json.loads(r.stdout)
        tag = "ARCHIVED" if j.get("archived") else "ok"
        lic = (j.get("license") or {}).get("spdx_id") or "no-license"
        print(f"{'WARN' if j.get('archived') else 'ok  '}  {u}  [{tag}, {lic}, pushed {j['pushed_at'][:10]}, {j['stargazers_count']} stars]")
        bad += 1 if j.get("archived") else 0
        continue
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "link-check"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"ok    {u}  [{resp.status}]")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  {u}  ({str(e)[:80]})")
        bad += 1
print(f"\n{len(urls)} urls, {bad} problem(s)")
sys.exit(1 if bad else 0)
