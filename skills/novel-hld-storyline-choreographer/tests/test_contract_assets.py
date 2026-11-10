from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
DIMS = {
    "scope_fidelity",
    "input_gate_obedience",
    "output_contract_correctness",
    "semantic_or_deterministic_correctness",
    "boundary_discipline",
    "parent_consumability",
}


class ContractAssetTests(unittest.TestCase):
    def test_chapter_plan_is_a_closed_first_class_contract(self):
        schema = json.loads((ROOT / "schemas" / "hs1-canonical.schema.json").read_text(encoding="utf-8"))
        self.assertIn("chapter_storyline_plan", schema["required"])
        self.assertEqual(schema["properties"]["chapter_storyline_plan"]["items"]["$ref"], "#/$defs/chapterDesign")
        self.assertFalse(schema["$defs"]["chapterDesign"]["additionalProperties"])
        self.assertIn("reader_name", schema["$defs"]["register"]["required"])
        self.assertIn("chapter_storyline_plan", CONTRACT["model_required"])
        self.assertEqual(CONTRACT["object_arrays"]["chapter_storyline_plan"], "HCD-")

    def test_independent_research_has_ten_or_more_sources(self):
        text = (ROOT / "references" / "sources.md").read_text(encoding="utf-8")
        urls = re.findall(r"https://[^\s|]+", text)
        self.assertGreaterEqual(len(set(urls)), 10)
        self.assertGreaterEqual(text.count("Absorbed point"), 1)

    def test_eval_cases_have_frozen_sections(self):
        for suffix in ("P01", "N01", "B01"):
            path = ROOT / "evals" / "cases" / f"{CONTRACT['stage']}-{suffix}.md"
            text = path.read_text(encoding="utf-8")
            for heading in ("## Prompt", "## Expected Behavior", "## Forbidden Behavior", "## Scoring Rule", "## Pass Bar"):
                self.assertIn(heading, text, f"{path}: missing {heading}")
            for dimension in DIMS:
                self.assertIn(dimension, text)

    def test_fixture_manifest_is_sealed_and_current(self):
        root = ROOT / "tests" / "fixtures"
        manifest = json.loads((root / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["sealed_before_execution"])
        self.assertEqual(len(manifest["fixtures"]), 3)
        for item in manifest["fixtures"]:
            path = root / item["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            fixture = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(fixture["sealed_before_execution"])
            self.assertEqual(fixture["single_defect_injection"], item["single_defect_injection"])

    def test_acceptance_evidence_has_six_by_two_for_every_case(self):
        evidence = json.loads((ROOT / "tests" / "acceptance-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(set(evidence["cases"]), {f"{CONTRACT['stage']}-P01", f"{CONTRACT['stage']}-N01", f"{CONTRACT['stage']}-B01"})
        for case in evidence["cases"].values():
            self.assertEqual(set(case["scores"]), DIMS)
            self.assertTrue(all(score == 2 for score in case["scores"].values()))
            self.assertTrue(case["deterministic_evidence"])
            self.assertTrue(case["semantic_evidence"])


if __name__ == "__main__":
    unittest.main()
