"""Tests for genie_onto and the industry packs. Run:  python3 -m unittest discover -s tests -v
Needs: pandas, numpy, pyyaml."""
import copy
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(HERE), "skills", "databricks-genie-ontology")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import genie_onto as G  # noqa: E402

PACKS = sorted(glob.glob(os.path.join(SKILL, "industries", "*.yaml")))
TEMPLATE = os.path.join(SKILL, "templates", "spec_template.yaml")
RETAIL = os.path.join(SKILL, "industries", "retail.yaml")
BANK = os.path.join(SKILL, "industries", "bfsi_banking.yaml")


class TestPacks(unittest.TestCase):
    def test_all_packs_present(self):
        self.assertGreaterEqual(len(PACKS), 11)

    def test_packs_validate_clean(self):
        for p in PACKS + [TEMPLATE]:
            with self.subTest(pack=os.path.basename(p)):
                E, W = G.validate_spec(G.load_spec(p))
                self.assertEqual(E, [], E)
                self.assertEqual(W, [], W)

    def test_packs_generate_valid_data(self):
        for p in PACKS + [TEMPLATE]:
            with self.subTest(pack=os.path.basename(p)):
                spec = G.load_spec(p)
                data = G.generate_data(spec)
                self.assertEqual(G.check_data(spec, data), [])

    def test_generation_is_deterministic(self):
        import datetime as dt
        spec = G.load_spec(RETAIL)
        a = G.generate_data(spec, today=dt.date(2026, 1, 1))
        b = G.generate_data(spec, today=dt.date(2026, 1, 1))
        for t in a:
            self.assertTrue(a[t].equals(b[t]), t)

    def test_every_pack_has_agent_pages_and_domains(self):
        for p in PACKS:
            with self.subTest(pack=os.path.basename(p)):
                s = G.load_spec(p)
                self.assertTrue(s["agent"]["sources"])
                self.assertGreaterEqual(len(s["pages"]), 2)
                self.assertGreaterEqual(len(s["domains"]), 3)
                self.assertTrue(all(mv.startswith("mv_") for mv in s["metric_views"]))

    def test_sql_rendering(self):
        for p in PACKS:
            with self.subTest(pack=os.path.basename(p)):
                s = G.load_spec(p)
                for t in s["tables"]:
                    self.assertIn("CREATE OR REPLACE TABLE", G.sql_create_table(s, t))
                for mv in s["metric_views"]:
                    sql = G.sql_metric_view(s, mv)
                    self.assertIn("WITH METRICS", sql)
                    self.assertIn("version: 1.1", sql)
                    self.assertNotIn(" on: True", sql)
                pk, fk, ck = G.sql_constraints(s)
                self.assertEqual(len(pk), len(s["tables"]))
                self.assertTrue(G.audit_queries(s))

    def test_comments_are_escaped(self):
        s = G.load_spec(TEMPLATE)
        s["tables"]["dim_thing"]["comment"] = "it's a test"
        self.assertIn("COMMENT 'it\\'s a test'", G.sql_create_table(s, "dim_thing"))
        s["tables"]["dim_thing"]["comment"] = "path C:\\new and\nnewline"
        self.assertIn("C:\\\\new and newline", G.sql_create_table(s, "dim_thing"))   # backslash doubled, newline flattened

    def test_docs_and_notebook_build(self):
        s_path = BANK
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(G.render_docs(G.load_spec(s_path), d))
            self.assertTrue(os.path.exists(os.path.join(d, "agent.md")))
            for as_cell in (False, True):
                text = G.build_notebook(s_path, as_cell=as_cell)
                compile(text.replace("# MAGIC ", "# "), "nb", "exec")          # valid python
                self.assertNotIn('\nif __name__ == "__main__":\n    sys.exit', text)   # CLI must not run in a notebook
                self.assertIn("SPEC_JSON", text)

    def test_cli_runs(self):
        r = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "genie_onto.py"), "validate", RETAIL],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestValidatorCatchesMistakes(unittest.TestCase):
    def base(self):
        return G.load_spec(RETAIL)

    def errors(self, s):
        return G.validate_spec(G.normalize(s))[0]

    def test_chained_join_rejected(self):
        s = self.base()
        mv = next(iter(s["metric_views"].values()))
        mv["joins"][1]["on"] = "date.date_key = product.product_key"
        self.assertTrue(any("chained" in e for e in self.errors(s)))

    def test_unknown_column_in_expression(self):
        s = self.base()
        next(iter(s["metric_views"].values()))["measures"][0]["expr"] = "SUM(source.nonexistent)"
        self.assertTrue(any("nonexistent" in e for e in self.errors(s)))

    def test_bad_fk_target(self):
        s = self.base()
        s["tables"]["fact_sales"]["columns"]["product_key"]["fk"] = "dim_product.sku"
        self.assertTrue(any("not a pk" in e for e in self.errors(s)))

    def test_undeclared_domain(self):
        s = self.base()
        s["tables"]["fact_sales"]["domains"] = ["Nope"]
        self.assertTrue(any("Nope" in e for e in self.errors(s)))

    def test_yaml_on_key_repaired(self):
        text = "industry: x\ntables: {}\nmetric_views: {mv_a: {source: t, joins: [{name: d, table: t, on: 'source.a = d.a'}]}}"
        s = G.load_spec(text)
        self.assertIn("on", s["metric_views"]["mv_a"]["joins"][0])

    def test_constant_boolean_detected(self):
        s = self.base()
        spec = copy.deepcopy(s)
        data = G.generate_data(spec)
        spec["tables"]["fact_sales"]["columns"]["flag"] = {"type": "boolean", "gen": "bool", "p": 0.5, "comment": "x"}
        data["fact_sales"]["flag"] = True          # a degenerate column: every ratio on it would be 0 or 1
        self.assertTrue(any("constant" in f for f in G.check_data(spec, data)))

    def test_orphan_fk_detected(self):
        spec = self.base()
        data = G.generate_data(spec)
        data["fact_sales"].loc[0, "product_key"] = 999999
        self.assertTrue(any("orphan" in f for f in G.check_data(spec, data)))


class TestRedactionScript(unittest.TestCase):
    def test_scan_flags_and_passes(self):
        script = os.path.join(SKILL, "scripts", "redaction_scan.sh")
        with tempfile.TemporaryDirectory() as d:
            fake = "contact someone" + "@real-domain.io or host d" + "bc-12345678-abcd" + ".cloud.databricks.com ?" + "o=1234567890123\n"  # assembled so this file stays scan-clean
            open(os.path.join(d, "a.md"), "w").write(fake)
            r = subprocess.run(["bash", script, d, "secretterm"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("email", r.stdout)
            self.assertIn("databricks hosts", r.stdout)
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "a.md"), "w").write("nothing sensitive here\n")
            r = subprocess.run(["bash", script, d], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
