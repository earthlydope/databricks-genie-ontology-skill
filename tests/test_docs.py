"""Documentation tests: the repo's own docs pass tools/check_docs.py, and the checker really catches breakage."""
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_docs  # noqa: E402

SKILL_REL = os.path.join("skills", "databricks-genie-ontology")


def copy_repo():
    dst = tempfile.mkdtemp()
    ignore = shutil.ignore_patterns(".git", "__pycache__", "venv", ".venv", "*.pyc")
    shutil.copytree(ROOT, os.path.join(dst, "r"), ignore=ignore)
    return dst, os.path.join(dst, "r")


class TestRepoDocs(unittest.TestCase):
    def test_docs_are_clean(self):
        self.assertEqual(check_docs.run(ROOT), [])

    def test_slug_matches_github_rules(self):
        self.assertEqual(check_docs.slugify("Build / SQL"), "build--sql")
        self.assertEqual(check_docs.slugify("Notebooks (the workhorse)"), "notebooks-the-workhorse")
        self.assertEqual(check_docs.slugify("Gate 6 - Independent critic"), "gate-6---independent-critic")
        self.assertEqual(check_docs.slugify("Phase 3: Build the SQL layer"), "phase-3-build-the-sql-layer")


class TestCheckerCatchesBreakage(unittest.TestCase):
    def setUp(self):
        self.tmp, self.repo = copy_repo()
        self.skill = os.path.join(self.repo, SKILL_REL)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit(self, rel, fn):
        path = os.path.join(self.repo, rel)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn(text))

    def problems(self):
        return check_docs.run(self.repo)

    def test_baseline_copy_is_clean(self):
        self.assertEqual(self.problems(), [])

    def test_broken_link_and_anchor(self):
        self.edit(os.path.join(SKILL_REL, "references", "02-runbook.md"), lambda t: t + "\nSee [x](nope.md) and [y](03-spec-format.md#no-such-heading).\n")
        found = " ".join(self.problems())
        self.assertIn("broken link (or wrong letter case) -> nope.md", found)
        self.assertIn("anchor '#no-such-heading' not found", found)

    def test_missing_front_matter_key_and_wrong_kind(self):
        self.edit(os.path.join(SKILL_REL, "references", "05-gotchas-and-fixes.md"), lambda t: t.replace("read_when:", "when:", 1))
        self.edit(os.path.join(SKILL_REL, "appendix", "C-glossary.md"), lambda t: t.replace("kind: appendix", "kind: reference", 1))
        found = " ".join(self.problems())
        self.assertIn("front matter missing 'read_when'", found)
        self.assertIn("kind is 'reference', expected 'appendix'", found)

    def test_stale_catalog_is_detected_and_write_fixes_it(self):
        self.edit(os.path.join(SKILL_REL, "references", "05-gotchas-and-fixes.md"), lambda t: t.replace("summary: Symptom", "summary: Changed symptom", 1))
        self.assertTrue(any("catalog is stale" in p for p in self.problems()))
        self.assertTrue(check_docs.write_catalog(self.repo))
        self.assertEqual(self.problems(), [])

    def test_missing_path_bare_number_stale_name_unknown_command(self):
        self.edit(os.path.join(SKILL_REL, "references", "06-data-quality-and-features.md"),
                  lambda t: t + "\nSee `scripts/nothing.py`, `04`, 10-public-repos-and-docs and `genie_onto.py frobnicate x.yaml`.\n")
        found = " ".join(self.problems())
        self.assertIn("path `scripts/nothing.py` does not exist", found)
        self.assertIn("bare doc number `04`", found)
        self.assertIn("removed document '10-public-repos-and-docs'", found)
        self.assertIn("unknown genie_onto subcommand 'frobnicate'", found)

    def test_undocumented_generator_wrong_pack_count_and_version(self):
        self.edit(os.path.join(SKILL_REL, "references", "03-spec-format.md"), lambda t: t.replace("`lognormal`", "lognormal"))
        self.edit(os.path.join(SKILL_REL, "references", "01-concepts-and-architecture.md"), lambda t: t + "\nWe ship 99 packs.\n")
        self.edit("CHANGELOG.md", lambda t: t.replace("## 1.1.0", "## 9.9.9", 1))
        found = " ".join(self.problems())
        self.assertIn("generator `lognormal` is not documented", found)
        self.assertIn("says 99 packs", found)
        self.assertIn("CHANGELOG.md: newest version '9.9.9'", found)

    def test_pack_without_status_row(self):
        self.edit(os.path.join(SKILL_REL, "industries", "README.md"), lambda t: t.replace("| `retail.yaml` | Live 1.0.0 |", "| `retail.yaml` | Maybe |"))
        self.assertTrue(any("pack 'retail' status" in p for p in self.problems()))

    def test_link_leaving_skill_folder_duplicate_heading_and_wrong_case(self):
        self.edit(os.path.join(SKILL_REL, "INDEX.md"), lambda t: t.replace("## 5. Files", "## 5. Files\nSee [c](../../CONTRIBUTING.md).\n", 1))
        self.edit(os.path.join(SKILL_REL, "references", "02-runbook.md"), lambda t: t + "\n## Phase 5: Domains\nSee [r](02-RUNBOOK.md).\n")
        found = " ".join(self.problems())
        self.assertIn("link leaves the skill folder", found)
        self.assertIn("duplicate heading slug 'phase-5-domains'", found)
        self.assertIn("wrong letter case", found)

    def test_fenced_command_typos_are_caught(self):
        self.edit(os.path.join(SKILL_REL, "INDEX.md"), lambda t: t.replace("```bash\nSKILL=", "```bash\npython3 $SKILL/scripts/genie_onto.py validat spec.yaml\npython3 $SKILL/scripts/genie_onto.py notebook a b --cellz\nSKILL=", 1))
        found = " ".join(self.problems())
        self.assertIn("unknown genie_onto subcommand 'validat' in a code block", found)
        self.assertIn("unknown genie_onto flag '--cellz'", found)

    def test_live_status_needs_evidence_and_version_needs_a_row(self):
        self.edit(os.path.join(SKILL_REL, "industries", "README.md"), lambda t: t.replace("| `cpg_fmcg.yaml` | Local only |", "| `cpg_fmcg.yaml` | Live 1.0.0 |"))
        self.edit(os.path.join(SKILL_REL, "appendix", "G-verification-evidence.md"), lambda t: t.replace("| 1.1.0 |", "| 1.1.x |"))
        found = " ".join(self.problems())
        self.assertIn("pack 'cpg_fmcg' is marked Live but appendix G has no evidence", found)
        self.assertIn("no row for builder version 1.1.0", found)

    def test_status_must_match_exactly_and_front_matter_must_be_single_line(self):
        self.edit(os.path.join(SKILL_REL, "industries", "README.md"), lambda t: t.replace("| `retail.yaml` | Live 1.0.0 |", "| `retail.yaml` | Live 1.0.0 kind of |"))
        self.edit(os.path.join(SKILL_REL, "appendix", "C-glossary.md"), lambda t: re.sub(r"^summary:.*$", "summary: >", t, count=1, flags=re.M))
        found = " ".join(self.problems())
        self.assertIn("must be exactly one of", found)
        self.assertIn("must be a single-line value", found)

    def test_size_limit(self):
        self.edit(os.path.join(SKILL_REL, "SKILL.md"), lambda t: t + "\nx\n" * 200)
        self.assertTrue(any("exceeds the" in p and "SKILL.md" in p for p in self.problems()))


if __name__ == "__main__":
    unittest.main()
