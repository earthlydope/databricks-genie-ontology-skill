"""One regression test per defect found by live testing or by the independent reviews.
Run:  python3 -m unittest discover -s tests -v"""
import datetime as dt
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


def spec(name="retail"):
    return G.load_spec(os.path.join(SKILL, "industries", name + ".yaml"))


def errs(s):
    return G.validate_spec(G.normalize(s))[0]


class TestValidatorRules(unittest.TestCase):
    def test_pk_cannot_be_nullable(self):
        s = spec(); s["tables"]["dim_store"]["columns"]["store_key"]["nullable"] = True
        self.assertTrue(any("cannot be nullable" in e for e in errs(s)))

    def test_fk_must_match_pk_type(self):
        s = spec(); s["tables"]["fact_sales"]["columns"]["product_key"]["type"] = "bigint"
        self.assertTrue(any("differs from referenced pk type" in e for e in errs(s)))

    def test_fk_cannot_target_composite_pk(self):
        s = spec(); s["tables"]["dim_store"]["columns"]["store_name"]["pk"] = True
        self.assertTrue(any("composite pk" in e for e in errs(s)))

    def test_in_between_rejected_in_checks(self):
        s = spec(); s["tables"]["fact_sales"]["checks"]["bad"] = "quantity IN (1, 2)"
        self.assertTrue(any("IN/BETWEEN" in e for e in errs(s)))

    def test_dollar_dollar_rejected(self):
        s = spec(); next(iter(s["metric_views"].values()))["measures"][0]["expr"] = "SUM(source.revenue) -- $$"
        self.assertTrue(any("$$" in e for e in errs(s)))

    def test_unsafe_catalog_rejected(self):
        s = spec(); s["catalog"] = "x; DROP SCHEMA y"
        self.assertTrue(any("letters, digits" in e for e in errs(s)))

    def test_date_key_after_needs_max_days(self):
        s = spec(); del s["tables"]["fact_returns"]["columns"]["date_key"]["max_days"]
        self.assertTrue(any("max_days" in e for e in errs(s)))

    def test_map_values_must_be_lists(self):
        s = spec(); s["tables"]["dim_product"]["columns"]["product_name"]["mapping"]["Beauty"] = "Perfume"
        self.assertTrue(any("non-empty list" in e for e in errs(s)))


class TestGeneratorAndBuilder(unittest.TestCase):
    def test_json_roundtrip_keeps_data_identical(self):
        for p in PACKS:
            s = G.load_spec(p)
            s2 = G.normalize(json.loads(json.dumps(s)))
            a, b = G.generate_data(s, today=dt.date(2026, 1, 1)), G.generate_data(s2, today=dt.date(2026, 1, 1))
            for t in a:
                self.assertTrue(a[t].equals(b[t]), (os.path.basename(p), t))

    def test_int_keyed_map_survives_json(self):
        s = spec()
        t = s["tables"]["dim_product"]["columns"]
        t["product_name"]["from"] = "bucket"
        t["product_name"]["mapping"] = {1: ["a"], 2: ["b"]}
        t["bucket"] = {"type": "int", "gen": "uniform", "min": 1, "max": 2, "comment": "x"}
        s2 = G.normalize(json.loads(json.dumps(s)))
        self.assertEqual(G.check_data(s2, G.generate_data(s2)), [])

    def test_column_order_independent(self):
        s = spec()
        cols = s["tables"]["fact_returns"]["columns"]
        s["tables"]["fact_returns"]["columns"] = {k: cols[k] for k in reversed(list(cols))}   # children listed before parents
        self.assertEqual(G.check_data(s, G.generate_data(s)), [])

    def test_unique_fk_rows_are_capped(self):
        s = spec(); s["tables"]["fact_returns"]["rows"] = 10 ** 6
        self.assertEqual(len(G.generate_data(s)["fact_returns"]), s["tables"]["fact_sales"]["rows"])

    def test_triple_quotes_in_spec_do_not_break_notebook(self):
        with tempfile.TemporaryDirectory() as d:
            s = spec(); s["description"] = "has ''' triple quotes and a \\ backslash"
            path = os.path.join(d, "s.json")
            json.dump(s, open(path, "w"))
            compile(G.build_notebook(path, as_cell=True), "nb", "exec")

    def test_notebook_command_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "new", "dir", "build.py")
            r = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "genie_onto.py"), "notebook",
                                os.path.join(SKILL, "industries", "retail.yaml"), out], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(out))

    def test_managed_marker_in_ddl(self):
        self.assertIn("genie_onto.managed", G.sql_create_table(spec(), "dim_store"))

    def test_metric_view_text_is_quoted(self):
        s = spec(); mv = next(iter(s["metric_views"]))
        s["metric_views"][mv]["measures"][0]["expr"] = "SUM(CASE WHEN source.quantity > 0 THEN source.revenue ELSE 0 END)"
        self.assertIn('expr: "SUM(CASE WHEN', G.metric_view_yaml(G.normalize(s), mv))

    def test_notebook_reruns_only_tags_after_domains(self):
        text = G.build_notebook(os.path.join(SKILL, "industries", "retail.yaml"), as_cell=True)
        self.assertIn('steps=["tags"] if domains_done else None', text)


class TestPackRealism(unittest.TestCase):
    """Data defects reviewers found by measuring the generated data."""
    def test_telecom_no_usage_after_churn(self):
        d = G.generate_data(spec("telecom"))
        u = d["fact_usage"].merge(d["fact_churn"][["subscriber_key", "date_key"]], on="subscriber_key", suffixes=("", "_c"))
        self.assertEqual(int((u.date_key > u.date_key_c).sum()), 0)
        self.assertEqual(len(d["fact_churn"]), int(d["dim_subscriber"].churned.sum()))

    def test_insurance_paid_only_when_settled(self):
        c = G.generate_data(spec("bfsi_insurance"))["fact_claims"]
        self.assertEqual(float(c[c.status != "Settled"].paid_amount.sum()), 0.0)

    def test_provider_outpatient_has_no_stay(self):
        e = G.generate_data(spec("hls_provider"))["fact_encounters"]
        self.assertEqual(float(e[e.encounter_type == "Outpatient"].length_of_stay_days.sum()), 0.0)
        self.assertGreater(e[e.encounter_type == "Inpatient"].length_of_stay_days.mean(), 2.0)

    def test_banking_has_a_real_npa_tail(self):
        d = G.generate_data(spec("bfsi_banking"))["fact_loan_snapshots"]
        self.assertTrue(0.01 < d.npa_flag.mean() < 0.2)

    def test_supply_chain_mostly_on_time(self):
        self.assertGreater(G.generate_data(spec("supply_chain_logistics"))["fact_shipments"].on_time.mean(), 0.8)

    def test_education_pass_rate_is_plausible(self):
        en = G.generate_data(spec("education"))["fact_enrollment"]
        ok = en[~en.dropped]
        self.assertTrue(0.7 < (ok.grade_points >= 2).mean() < 0.97)
        self.assertEqual(float(en[en.dropped].grade_points.max()), 0.0)


class TestServeFilesHardening(unittest.TestCase):
    script = os.path.join(SKILL, "scripts", "browser", "serve_files.py")

    def test_refuses_sensitive_directory(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "config.env"), "w").write("x")
            r = subprocess.run([sys.executable, self.script, d, "8799", "https://example.invalid"],
                               capture_output=True, text=True, timeout=20)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("refus", (r.stdout + r.stderr).lower())

    def test_requires_all_arguments(self):
        r = subprocess.run([sys.executable, self.script], capture_output=True, text=True, timeout=20)
        self.assertNotEqual(r.returncode, 0)


class TestGitignore(unittest.TestCase):
    def test_template_state_file_is_not_ignored(self):
        # behaviour is tested with `git check-ignore` in tests/test_security.py; here: the negation that keeps the template tracked must exist
        root = os.path.dirname(HERE)
        text = open(os.path.join(root, ".gitignore")).read().splitlines()
        self.assertIn("STATE.md", text)
        self.assertIn("!**/templates/STATE.md", text)


if __name__ == "__main__":
    unittest.main()
