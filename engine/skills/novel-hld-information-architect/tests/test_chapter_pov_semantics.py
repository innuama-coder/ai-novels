from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hi1_run", ROOT / "scripts/run_skill.py")
assert SPEC and SPEC.loader
HI1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HI1)


def owned(identifier: str, **extra: object) -> dict:
    value = {
        "id": identifier,
        "source_refs": ["SRC-001"],
        "source_authority_refs": [],
        "ownership_class": "hld_owned",
        "resolution_ref": None,
    }
    value.update(extra)
    return value


class ChapterPovSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        HI1._WORKSPACE = self.workspace
        (self.workspace / "HA1.json").write_text(json.dumps({
            "narrative_units": [{"id": "HNU-01"}, {"id": "HNU-02"}],
            "chapter_shells": [
                {"id": "HCH-01", "parent_unit_id": "HNU-01"},
                {"id": "HCH-02", "parent_unit_id": "HNU-01"},
                {"id": "HCH-03", "parent_unit_id": "HNU-02"},
            ],
        }), encoding="utf-8")
        (self.workspace / "HC1.json").write_text(json.dumps({
            "character_participation_register": [
                {"id": "HAS-PART-A", "character_id": "CHR-A"},
                {"id": "HAS-PART-B", "character_id": "CHR-B"},
            ],
            "chapter_agency_contracts": [
                {"id": "HAS-AGENCY-01", "chapter_id": "HCH-01", "parent_unit_id": "HNU-01", "focal_character_ids": ["CHR-A"], "information_paths": [{"character_id": "CHR-A", "acquisition_modes": ["perceived"], "limit": "只能知道亲自感知的事实"}]},
                {"id": "HAS-AGENCY-02", "chapter_id": "HCH-02", "parent_unit_id": "HNU-01", "focal_character_ids": ["CHR-B"], "information_paths": [{"character_id": "CHR-B", "acquisition_modes": ["documented"], "limit": "只能知道记录明确提供的事实"}]},
                {"id": "HAS-AGENCY-03", "chapter_id": "HCH-03", "parent_unit_id": "HNU-02", "focal_character_ids": ["CHR-B"], "information_paths": [{"character_id": "CHR-B", "acquisition_modes": ["told"], "limit": "只能知道依法转告的事实"}]},
            ],
        }), encoding="utf-8")
        unit = lambda identifier, unit_id, character: owned(
            identifier, unit_id=unit_id, pov_character_id=character,
            focalization_mode="第三人称限知", perception_limits=["只能知道合法获得的信息"],
        )
        chapter = lambda number, chapter_id, parent, agency, character, modes, limit: owned(
            f"HPV-CH-{number}", chapter_id=chapter_id, parent_unit_id=parent,
            hc1_agency_contract_id=agency,
            pov_character_id=character, focalization_mode="第三人称限知",
            knowledge_acquisition_modes=modes, perception_limits=[limit],
        )
        self.model = {
            "source_artifacts": [
                {"role": "upstream::HA1::main", "path": "HA1.json"},
                {"role": "upstream::HC1::main", "path": "HC1.json"},
            ],
            "unit_pov_assignments": [unit("HPV-U1", "HNU-01", "CHR-A"), unit("HPV-U2", "HNU-02", "CHR-B")],
            "chapter_pov_assignments": [
                chapter(1, "HCH-01", "HNU-01", "HAS-AGENCY-01", "CHR-A", ["perceived"], "只能知道亲自感知的事实"),
                chapter(2, "HCH-02", "HNU-01", "HAS-AGENCY-02", "CHR-B", ["documented"], "只能知道记录明确提供的事实"),
                chapter(3, "HCH-03", "HNU-02", "HAS-AGENCY-03", "CHR-B", ["told"], "只能知道依法转告的事实"),
            ],
            "information_nodes": [{
                "id": "HIN-01", "source_information_id": "SRC-001", "knower_ids": ["CHR-A"],
                "reader_state": "known", "acquisition_mode": "perceived",
                "earliest_legal_unit_id": "HNU-01", "forbidden_leak_unit_ids": [], "resolution_ref": None,
            }],
            "knowledge_states": [{"information_node_ids": ["HIN-01"]}],
            "reader_information_states": [{"information_node_ids": ["HIN-01"]}],
            "suspense_chains": [{"id": "HSP-01", "setup_node_ids": ["HIN-01"], "payoff_node_ids": ["HIN-01"], "authorized_open_terminal": None}],
            "reveal_payoff_matrix": [{"id": "HIN-RPM-01", "information_node_ids": ["HIN-01"], "setup_unit_ids": ["HNU-01"], "terminal_unit_id": "HNU-02"}],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_unit_and_chapter_coverage_passes(self) -> None:
        HI1.validate_stage_model(self.model, {})

    def test_missing_chapter_assignment_fails(self) -> None:
        self.model["chapter_pov_assignments"].pop()
        with self.assertRaisesRegex(HI1.CandidateError, "one ordered POV assignment per HA1 chapter"):
            HI1.validate_stage_model(self.model, {})

    def test_wrong_chapter_parent_fails(self) -> None:
        self.model["chapter_pov_assignments"][1]["parent_unit_id"] = "HNU-02"
        with self.assertRaisesRegex(HI1.CandidateError, "parent unit does not match"):
            HI1.validate_stage_model(self.model, {})

    def test_unknown_chapter_focal_character_fails(self) -> None:
        self.model["chapter_pov_assignments"][1]["pov_character_id"] = "CHR-UNKNOWN"
        with self.assertRaisesRegex(HI1.CandidateError, "unknown to HC1"):
            HI1.validate_stage_model(self.model, {})

    def test_unavailable_chapter_focal_character_fails(self) -> None:
        item = self.model["chapter_pov_assignments"][1]
        item["pov_character_id"] = "CHR-A"
        with self.assertRaisesRegex(HI1.CandidateError, "unavailable or unauthorized"):
            HI1.validate_stage_model(self.model, {})

    def test_stale_agency_or_information_path_fails(self) -> None:
        item = self.model["chapter_pov_assignments"][1]
        item["hc1_agency_contract_id"] = "HAS-AGENCY-01"
        with self.assertRaisesRegex(HI1.CandidateError, "exact HC1 agency"):
            HI1.validate_stage_model(self.model, {})
        item["hc1_agency_contract_id"] = "HAS-AGENCY-02"
        item["knowledge_acquisition_modes"] = ["perceived"]
        with self.assertRaisesRegex(HI1.CandidateError, "knowledge acquisition"):
            HI1.validate_stage_model(self.model, {})

    def test_missing_hc1_chapter_agency_is_an_upstream_defect(self) -> None:
        hc1 = json.loads((self.workspace / "HC1.json").read_text(encoding="utf-8"))
        del hc1["chapter_agency_contracts"]
        (self.workspace / "HC1.json").write_text(json.dumps(hc1), encoding="utf-8")
        with self.assertRaisesRegex(HI1.UpstreamDefect, "HC1 chapter agency contracts"):
            HI1.validate_stage_model(self.model, {})


if __name__ == "__main__":
    unittest.main()
