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


def chapter_plan(chapter_number: int, chapter_id: str, primary: str = "SL-MAIN",
                 background: list[str] | None = None, preserved: list[str] | None = None) -> dict:
    return {
        "id": f"HCD-{chapter_number:03d}",
        "chapter_id": chapter_id,
        "chapter_number": chapter_number,
        "working_title": f"第{chapter_number}章",
        "core_content": "推进被授权的核心冲突。",
        "chapter_end_change": "状态发生不可撤回的变化。",
        "primary_storyline_id": primary,
        "supporting_storyline_ids": [],
        "background_storyline_ids": list(background or []),
        "preserved_open_storyline_ids": list(preserved or []),
        "content_obligations": ["落实已授权的场景义务"],
        "prohibitions": ["不得越界写成分场"],
    }


def model() -> dict:
    return {
        "semantic_storyline_register": [
            {"source_storyline_id": "SL-MAIN", "reader_name": "追查真相的主线"},
            {"source_storyline_id": "SL-OPEN", "reader_name": "保持开放的暗线"},
        ],
        "activation_disposition": [
            {"source_storyline_id": "SL-MAIN", "disposition": "placed"},
            {"source_storyline_id": "SL-OPEN", "disposition": "preserved-open"},
        ],
        "storyline_segments": [
            {
                "id": "HTS-SEG-MAIN",
                "source_storyline_id": "SL-MAIN",
                "chapter_shell_ids": ["HCH-01", "HCH-02"],
            }
        ],
        "unit_storyline_matrix": [
            {"id": "HTS-MAT-001", "unit_id": "HNU-001", "segment_ids": ["HTS-SEG-MAIN"]},
        ],
        "storyline_connections": [
            {"id": "HTC-001", "connection_type": "causal", "from_segment_id": "HTS-SEG-MAIN", "to_segment_id": "HTS-SEG-MAIN"},
        ],
        "convergence_and_split_points": [
            {"id": "HTC-POINT-001", "connection_ids": ["HTC-001"], "unit_id": "HNU-001", "point_type": "convergence"},
        ],
        "subject_reconstruction_test": {"verdict": "pass"},
        "chapter_storyline_plan": [
            chapter_plan(1, "HCH-01"),
            chapter_plan(2, "HCH-02", preserved=["SL-OPEN"]),
        ],
    }


class ChapterPlanSemanticTests(unittest.TestCase):
    def test_valid_exact_chapter_plan(self):
        MODULE.validate_stage_model(copy.deepcopy(model()), {})

    def test_rejects_active_line_without_chapter_carrier(self):
        broken = model()
        broken["storyline_segments"] = []
        with self.assertRaisesRegex(MODULE.CandidateError, "no auditable carrier segment"):
            MODULE.validate_stage_model(broken, {})

    def test_rejects_missing_carried_chapter(self):
        broken = model()
        broken["chapter_storyline_plan"] = [chapter_plan(1, "HCH-01")]
        with self.assertRaisesRegex(MODULE.CandidateError, "must exactly cover every active chapter shell"):
            MODULE.validate_stage_model(broken, {})

    def test_rejects_noncontiguous_order(self):
        broken = model()
        broken["chapter_storyline_plan"] = [chapter_plan(1, "HCH-01"), chapter_plan(3, "HCH-02")]
        with self.assertRaisesRegex(MODULE.CandidateError, "contiguous and ordered from one"):
            MODULE.validate_stage_model(broken, {})

    def test_rejects_open_line_masquerading_as_placed(self):
        broken = model()
        broken["storyline_segments"].append({
            "id": "HTS-SEG-OPEN",
            "source_storyline_id": "SL-OPEN",
            "chapter_shell_ids": ["HCH-01"],
        })
        with self.assertRaisesRegex(MODULE.CandidateError, "cannot masquerade as a placed segment"):
            MODULE.validate_stage_model(broken, {})


if __name__ == "__main__":
    unittest.main()
