#!/usr/bin/env bash
# Scan a directory for personal / environment identifiers before publishing anything.
#   scripts/redaction_scan.sh [--history] <dir> [extra-term ...]
# Extra terms are literal, case-insensitive strings you must never publish (your username, your company, a workspace id...).
# Exit 0 = clean, 1 = hits (printed). Read every hit; a clean scan is necessary, not sufficient.
# --history also scans every commit of the git history (git log --all -p) in <dir>, where deleted files and old messages still live.
set -u
history=0
[ "${1:-}" = "--history" ] && { history=1; shift; }
dir="${1:-.}"; shift || true
status=0
targets=("$dir")
if [ "$history" = 1 ]; then
  histfile=$(mktemp); trap 'rm -f "$histfile"' EXIT
  git -C "$dir" log --all -p > "$histfile" 2>/dev/null || { echo "no git history readable in $dir" >&2; }
  targets+=("$histfile")
fi
# Allow-list is applied to the MATCHED TEXT only (never to the whole line), so a harmless token on a line cannot hide a real hit.
# Only exact placeholders pass: example domains, GitHub's no-reply addresses, scoped npm names, user@host, you@host.
ALLOW='(@example\.(com|org)$|^noreply@(users\.noreply\.github|anthropic)\.com$|^[0-9]+\+[A-Za-z0-9-]+@users\.noreply\.github\.com$|^@types/|^user@host$|^you@host$)'
scan() {  # label, extended-regex
  local out="" line m
  while IFS= read -r line; do
    m="${line#*:*:}"                       # grep -n -o prints  path:lineno:match
    printf '%s' "$m" | grep -qiE "$ALLOW" && continue
    out="$out$line"$'\n'
  done < <(grep -rIinoE --exclude-dir=.git --exclude-dir=__pycache__ --exclude=redaction_scan.sh -e "$2" "${targets[@]}" 2>/dev/null || true)
  if [ -n "$out" ]; then echo "== $1"; printf '%s' "$out" | head -40; status=1; fi
}
scan "email addresses"                    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
scan "databricks hosts"                   '(dbc-[0-9a-f]{8}-[0-9a-f]{4}|adb-[0-9]{6,}|[a-z0-9-]+\.cloud\.databricks\.com|[a-z0-9-]+\.azuredatabricks\.net|[a-z0-9-]+\.gcp\.databricks\.com)'
scan "workspace/org query ids (?o=)"      '[?&]o=[0-9]{8,}'
scan "long numeric object ids"            '(^|[^0-9])[0-9]{15,}([^0-9]|$)'
scan "32-hex ids (agents/rooms)"          '(^|[^0-9a-f])[0-9a-f]{32}([^0-9a-f]|$)'
scan "uuids"                              '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
scan "personal home paths"                '/(Users|home)/[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9._-]+'
scan "secret-looking tokens"              '(dapi[0-9a-f]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|xox[abp]-[A-Za-z0-9-]{10,})'
for term in "$@"; do scan "term: $term" "$(printf '%s' "$term" | sed 's/[][\.*^$(){}?+|/]/\\&/g')"; done
[ $status -eq 0 ] && echo "redaction scan clean (${targets[*]})"
exit $status
