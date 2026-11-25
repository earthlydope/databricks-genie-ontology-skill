#!/usr/bin/env python3
"""Regenerate tests/golden_sql.json: a sha256 digest per pack of everything the build RUNS or PASTES that is deterministic:
the full SQL (`genie_onto.py sql`), the audit queries, and the generated agent.md / pages / ui-checklist.
(Synthetic data is not pinned: random streams may change with numpy versions; it was compared against 1.0.0 once, see the CHANGELOG.)
Run only when you changed generated output ON PURPOSE; then re-run a pack live and record it in appendix G."""
import glob
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(HERE), "skills", "databricks-genie-ontology")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import genie_onto as G  # noqa: E402


def material(spec, mod=None):
    """The deterministic text that the build runs or pastes for one spec."""
    mod = mod or G
    parts = list(mod.all_sql(spec) if hasattr(mod, "all_sql") else [])
    parts += [f"{name}\n{sql}" for name, sql in mod.audit_queries(spec)]
    with tempfile.TemporaryDirectory() as out:
        for rel in mod.render_docs(spec, out):
            with open(os.path.join(out, rel), encoding="utf-8") as fh:
                parts.append(f"== {rel}\n" + fh.read())
    return "\n;;\n".join(parts)


def digests():
    out = {}
    for path in sorted(glob.glob(os.path.join(SKILL, "industries", "*.yaml"))):
        hexd = hashlib.sha256(material(G.load_spec(path)).encode("utf-8")).hexdigest()
        out[os.path.basename(path)] = "-".join(hexd[i:i + 8] for i in range(0, 64, 8))   # grouped so the redaction scan never reads a digest as an id
    return out


if __name__ == "__main__":
    with open(os.path.join(HERE, "golden_sql.json"), "w", encoding="utf-8") as fh:
        json.dump(digests(), fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote tests/golden_sql.json")
