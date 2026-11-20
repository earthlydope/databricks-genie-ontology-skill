#!/usr/bin/env bash
# Scan a directory for personal / environment identifiers before publishing anything.
#   scripts/redaction_scan.sh <dir> [extra-term ...]
# Extra terms are literal, case-insensitive strings you must never publish (your username, your company, a workspace id...).
# Exit 0 = clean, 1 = hits (printed). Read every hit; a clean scan is necessary, not sufficient.
set -u
dir="${1:-.}"; shift || true
status=0
scan() {  # label, extended-regex
  local out
  out=$(grep -rIniE --exclude-dir=.git --exclude-dir=__pycache__ --exclude=redaction_scan.sh -e "$2" "$dir" 2>/dev/null | grep -viE 'example\.(com|org)|noreply@|<[a-z -]*>|@types/|user@host|you@' || true)
  if [ -n "$out" ]; then echo "== $1"; echo "$out" | head -40; status=1; fi
}
scan "email addresses"                    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
scan "databricks hosts"                   '(dbc-[0-9a-f]{8}-[0-9a-f]{4}|adb-[0-9]{6,}|[a-z0-9-]+\.cloud\.databricks\.com|[a-z0-9-]+\.azuredatabricks\.net)'
scan "workspace/org query ids (?o=)"      '[?&]o=[0-9]{8,}'
scan "long numeric object ids"            '(^|[^0-9])[0-9]{15,}([^0-9]|$)'
scan "32-hex ids (agents/rooms)"          '(^|[^0-9a-f])[0-9a-f]{32}([^0-9a-f]|$)'
scan "uuids"                              '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
scan "personal home paths"                '/(Users|home)/[A-Za-z0-9._-]+/'
scan "secret-looking tokens"              '(dapi[0-9a-f]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|xox[abp]-[A-Za-z0-9-]{10,})'
for term in "$@"; do scan "term: $term" "$(printf '%s' "$term" | sed 's/[][\.*^$(){}?+|/]/\\&/g')"; done
[ $status -eq 0 ] && echo "redaction scan clean ($dir)"
exit $status
