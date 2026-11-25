"""Generated SQL is pinned: a change must be deliberate (python3 tests/update_golden.py) and re-verified live."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import update_golden  # noqa: E402


class TestGoldenSql(unittest.TestCase):
    def test_generated_sql_matches_pinned_digests(self):
        with open(os.path.join(HERE, "golden_sql.json"), encoding="utf-8") as fh:
            want = json.load(fh)
        got = update_golden.digests()
        self.assertEqual(sorted(want), sorted(got), "pack added or removed: refresh golden_sql.json")
        changed = [k for k in want if want[k] != got[k]]
        self.assertEqual(changed, [], f"generated SQL changed for {changed}: if intended, run tests/update_golden.py, "
                                      "re-run a pack live and record it in appendix G, and note it in the CHANGELOG")


class TestPinIsSensitive(unittest.TestCase):
    """The digest must move when an audit query or generated doc text changes (reviewer's mutation test)."""

    def test_audit_query_and_docs_changes_alter_the_digest(self):
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "skills", "databricks-genie-ontology", "scripts"))
        import genie_onto as G
        spec = G.load_spec(os.path.join(os.path.dirname(HERE), "skills", "databricks-genie-ontology", "industries", "retail.yaml"))
        base = update_golden.material(spec)
        original = G.audit_queries
        try:
            G.audit_queries = lambda s, *a, **k: [(n, "SELECT 0") for n, _ in original(s, *a, **k)]
            self.assertNotEqual(base, update_golden.material(spec))
        finally:
            G.audit_queries = original
        spec2 = G.load_spec(os.path.join(os.path.dirname(HERE), "skills", "databricks-genie-ontology", "industries", "retail.yaml"))
        spec2["agent"]["instructions"].append("an extra instruction")
        self.assertNotEqual(base, update_golden.material(spec2))


if __name__ == "__main__":
    unittest.main()
