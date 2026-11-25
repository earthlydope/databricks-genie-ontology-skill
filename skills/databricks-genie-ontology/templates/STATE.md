# STATE (update after every step; LOCAL ONLY)

Workspace: <host>  (workspace id: <id>)         Signed in: <yes/no, who confirmed>
Catalog.schema: <catalog>.<schema>              Spec: spec.yaml (<pack> v<date>)
Build notebook: <id/url>                         Agent: <id/url>

## Checklist
- [ ] spec validate 0/0, check OK
- [ ] build: Done. 0 error(s); audits PASS; row counts: <...>
- [ ] metric views reconciled with SQL (<which measure, result>)
- [ ] domains created + published: <list>
- [ ] tags applied (widget domains_created_<industry> = yes); domain counts match
- [ ] agent created, sources attached, certified, in domain, renamed
- [ ] pages published: <names + ids>
- [ ] sample questions verified: <q -> result>
- [ ] DQ monitoring enabled (schema Details > Advanced)
- [ ] critic review done; findings fixed
- [ ] redaction scan clean (if publishing)

## Findings / decisions
- <date> <what, why, fix>

## Not done (and why)
- Policies/masks/ABAC (security: user's call). Sharing/access (user's call). Genie One full-screen (popup blocked). Certification of Pages (untested).
