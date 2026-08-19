from __future__ import annotations

import unittest
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))
from runtime import hq2_stage_runtime as hq2  # noqa: E402


class HQ2StorylineCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.units = [{"id": "LWK-01", "storyline_ids": ["SL-A", "SL-B"], "chapter_shell_ids": ["HCH-01"]}]
        self.handoff = {
            "storyline_dispositions": [
                {"storyline_id": "SL-A", "disposition": "placed", "work_unit_ids": ["LWK-01"], "absence_reason": None},
                {"storyline_id": "SL-B", "disposition": "background-carried", "work_unit_ids": ["LWK-01"], "absence_reason": None},
                {"storyline_id": "SL-OPEN", "disposition": "preserved-open", "work_unit_ids": [], "absence_reason": "open"},
            ],
            "work_unit_time_windows": [
                {"work_unit_id": "LWK-01", "source_unit_ids": ["HNU-01"], "elapsed_start_day": 0, "elapsed_end_day": 7, "label": "第一周"},
            ],
            "chapter_designs": [{
                "id":"HCH-01","source_design_id":"HCD-01","chapter_number":1,"working_title":"第一章",
                "source_unit_id":"HNU-01","work_unit_id":"LWK-01","core_content":"冲突开始。",
                "chapter_end_change":"人物无法回到原点。","primary_storyline_id":"SL-A",
                "supporting_storyline_ids":[],"background_storyline_ids":["SL-B"],
                "preserved_open_storyline_ids":["SL-OPEN"],"content_obligations":["推进冲突"],
                "prohibitions":[],"source_value_sha256":"a"*64,
            }],
        }

    def test_complete_inventory_keeps_open_storyline_identity(self) -> None:
        self.assertEqual(hq2._consumer_storyline_ids(self.handoff, self.units, {"LWK-01"}), {"SL-A", "SL-B", "SL-OPEN"})

    def test_missing_background_storyline_fails(self) -> None:
        self.units[0]["storyline_ids"].remove("SL-B")
        with self.assertRaisesRegex(hq2.CandidateError, "active/background"):
            hq2._consumer_storyline_ids(self.handoff, self.units, {"LWK-01"})

    def test_missing_time_window_fails(self) -> None:
        self.handoff["work_unit_time_windows"] = []
        with self.assertRaisesRegex(hq2.CandidateError, "time windows"):
            hq2._consumer_storyline_ids(self.handoff, self.units, {"LWK-01"})

    def test_chapter_design_closes_downstream_guesswork(self) -> None:
        story_ids=hq2._consumer_storyline_ids(self.handoff,self.units,{"LWK-01"})
        self.assertEqual(hq2._consumer_chapter_ids(self.handoff,self.units,story_ids),{"HCH-01"})

    def test_chapter_design_must_cover_every_shell(self) -> None:
        self.handoff["chapter_designs"]=[]
        with self.assertRaisesRegex(hq2.CandidateError,"lacks chapter-level design"):
            hq2._consumer_chapter_ids(self.handoff,self.units,{"SL-A","SL-B","SL-OPEN"})

    def test_chapter_storyline_must_match_its_work_unit(self) -> None:
        self.handoff["chapter_designs"][0]["primary_storyline_id"]="SL-OPEN"
        with self.assertRaisesRegex(hq2.CandidateError,"storyline/work-unit mismatch"):
            hq2._consumer_chapter_ids(self.handoff,self.units,{"SL-A","SL-B","SL-OPEN"})


if __name__ == "__main__":
    unittest.main()
