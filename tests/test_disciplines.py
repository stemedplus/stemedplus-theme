"""The master STEMEd+ discipline list is valid and follows its own rules."""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import check_humeta_terms  # noqa: E402

PATH = Path(__file__).resolve().parent.parent / "stemedplus_disciplines.json"


class DisciplineListTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(PATH.read_text(encoding="utf-8"))
        self.disciplines = self.doc["disciplines"]

    def test_ids_and_labels_are_unique_and_sorted_by_label(self):
        ids = [d["id"] for d in self.disciplines]
        labels = [d["label"] for d in self.disciplines]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(labels, sorted(labels, key=str.lower))
        for d in self.disciplines:
            self.assertRegex(d["id"], r"^[a-z][a-z0-9_]*$")
            self.assertIn(d.get("scope", "education"), ("education", "field"))

    def test_patterns_compile_and_map_to_anzsrc(self):
        for d in self.disciplines:
            re.compile(r"\b(?:" + d["match"]["terms"] + r")\b", re.IGNORECASE)
            for a in d["match"].get("acronyms", []):
                self.assertRegex(a, r"^[A-Z][A-Z0-9]*$")
            self.assertTrue(d["humeta_disciplines"], d["id"])
            for code in d["humeta_disciplines"]:
                self.assertRegex(code, r"^anzsrc_\d{2,4}$")

    def test_astronomy_environment_and_computing_have_their_own_disciplines(self):
        by_id = {d["id"]: d for d in self.disciplines}
        self.assertEqual(by_id["astronomy_space"]["humeta_disciplines"], ["anzsrc_5101", "anzsrc_5109"])
        self.assertEqual(by_id["environmental_science"]["humeta_disciplines"], ["anzsrc_41"])
        self.assertEqual(by_id["computing"]["humeta_disciplines"], ["anzsrc_46"])
        self.assertGreaterEqual(self.doc["version"], 7)


class HumetaTermCheckTests(unittest.TestCase):
    """check_humeta_terms.py runs against humeta-profile in the workflow; here it gets a small
    vocabulary so the tests need no network."""

    def vocab(self, *terms):
        return {"vocabularies": {"discipline": {"terms": list(terms)}}}

    def test_missing_and_deprecated_terms_are_reported(self):
        doc = {"disciplines": [{"id": "physics", "humeta_disciplines": ["anzsrc_51", "anzsrc_02", "anzsrc_99"]}]}
        found = check_humeta_terms.problems(doc, self.vocab({"id": "anzsrc_51"}, {"id": "anzsrc_02", "deprecated": True}))
        self.assertEqual(found, ["physics: anzsrc_02 is deprecated in HuMeta",
                                 "physics: anzsrc_99 is not a HuMeta discipline term"])

    def test_current_terms_pass(self):
        doc = json.loads(PATH.read_text(encoding="utf-8"))
        codes = {c for d in doc["disciplines"] for c in d["humeta_disciplines"]}
        self.assertEqual(check_humeta_terms.problems(doc, self.vocab(*({"id": c} for c in codes))), [])


if __name__ == "__main__":
    unittest.main()
