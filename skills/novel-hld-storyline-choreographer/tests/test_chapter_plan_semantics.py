from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hs1_run_skill", ROOT / "scripts" / "run_skill.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def model() -> dict:
    return {
        "semantic_storyline_register": [
            {"source_storyline_id": "SL-MAIN"},
            {"source_storyline_id": "SL-OPEN"},
        ],
        "activation_disposition": [
            {"source_storyline_id": "SL-MAIN", "disposition": "placed"},
            {"source_storyline_id": "SL-OPEN", "disposition": "preserved-open"},
        ],
        "storyline_segments": [
            {
                "id": "HTS-SEG-MAIN",
                "source_storyline_id": "SL-MAIN",
                "chapter_shell_ids": ["HCH-01-01", "HCH-01-02"],
            }
        ],
        "chapter_storyline_plan": [
            {
                "id": "HCD-01-01",
                "chapter_id": "HCH-01-01",
                "chapter_number": 1,
                "primary_storyline_id": "SL-MAIN",
                "supporting_storyline_ids": [],
                "background_storyline_ids": [],
                "preserved_open_storyline_ids": ["SL-OPEN"],
            },
            {
                "id": "HCD-01-02",
                "chapter_id": "HCH-01-02",
                "chapter_number": 2,
                "primary_storyline_id": "SL-MAIN",
                "supporting_storyline_ids": [],
                "background_storyline_ids": [],
                "preserved_open_storyline_ids": ["SL-OPEN"],
            },
        ],
        "storyline_connections": [],
        "convergence_and_split_points": [],
        "subject_reconstruction_test": {"verdict": "pass"},
    }


class ChapterPlanSemanticTests(unittest.TestCase):
    def test_valid_exact_chapter_plan(self):
        MODULE.validate_stage_model(model(), {})

    def test_rejects_missing_carried_chapter(self):
        value = model()
        value["chapter_storyline_plan"].pop()
        with self.assertRaisesRegex(Exception, "exactly cover"):
            MODULE.validate_stage_model(value, {})

    def test_rejects_noncontiguous_order(self):
        value = model()
        value["chapter_storyline_plan"][1]["chapter_number"] = 3
        with self.assertRaisesRegex(Exception, "contiguous"):
            MODULE.validate_stage_model(value, {})

    def test_rejects_active_line_without_chapter_carrier(self):
        value = copy.deepcopy(model())
        value["semantic_storyline_register"].append({"source_storyline_id": "SL-SUPPORT"})
        value["activation_disposition"].append({"source_storyline_id": "SL-SUPPORT", "disposition": "placed"})
        value["storyline_segments"].append(
            {"id": "HTS-SEG-SUPPORT", "source_storyline_id": "SL-SUPPORT", "chapter_shell_ids": ["HCH-01-02"]}
        )
        value["chapter_storyline_plan"][0]["supporting_storyline_ids"] = ["SL-SUPPORT"]
        with self.assertRaisesRegex(Exception, "lacks chapter carrier"):
            MODULE.validate_stage_model(value, {})


if __name__ == "__main__":
    unittest.main()
