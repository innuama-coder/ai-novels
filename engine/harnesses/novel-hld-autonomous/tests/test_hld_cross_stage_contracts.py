from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
HARNESS = REPO / "harnesses" / "novel-hld-autonomous"
sys.path.insert(0, str(HARNESS))


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ha1 = load("cross_stage_ha1", "skills/novel-hld-narrative-architect/scripts/run_skill.py")
hs1 = load("cross_stage_hs1", "skills/novel-hld-storyline-choreographer/scripts/run_skill.py")
hr1 = load("cross_stage_hr1", "skills/novel-hld-rhythm-continuity-architect/scripts/run_skill.py")


def causal(prior: list[str], before: str, after: str, *, needed: bool = False, independent: bool = False) -> dict:
    return {
        "requires_prior_unit_ids": prior,
        "reality_action_status_before": before,
        "reality_action_status_after": after,
        "new_information_needed_for_reality_action": needed,
        "personal_choice_independent_of_reality_action": independent,
    }


class NarrativeCausalityAndThreatTests(unittest.TestCase):
    def model(self) -> dict:
        units = [
            {"id": "HNU-06", "parent_phase_id": "HST-P", "order": 0, "purpose": "verify", "entry_state_ref": "before", "required_change": "become ready", "exit_state_ref": "ready", "source_anchors": ["EV-1"], "causal_contract": causal([], "not_ready", "execution_ready")},
            {"id": "HNU-07", "parent_phase_id": "HST-P", "order": 1, "purpose": "choose", "entry_state_ref": "ready", "required_change": "make a personal choice", "exit_state_ref": "chosen", "source_anchors": ["EV-2"], "causal_contract": causal(["HNU-06"], "execution_ready", "execution_ready", independent=True)},
        ]
        return {
            "structural_phases": [{"id": "HST-P"}], "narrative_units": units,
            "chapter_shells": [{"id": "HCH-1", "parent_unit_id": "HNU-06", "order": 0}],
            "turning_point_anchors": [{"unit_id": "HNU-07"}],
            "entry_exit_state_contracts": [{"unit_id": item["id"]} for item in units],
            "world_setting_architecture": {
                "cities": [{"city_id": "HST-CITY-PHYSICAL"}, {"city_id": "HST-CITY-POLITICAL"}],
                "threat_mechanism": {"physical_target_city_id": "HST-CITY-PHYSICAL", "political_pressure_city_id": "HST-CITY-POLITICAL"},
            },
        }

    def test_valid_ready_then_independent_choice_passes(self) -> None:
        ha1.validate_stage_model(self.model(), {})

    def test_late_required_information_after_execution_ready_fails(self) -> None:
        model = self.model()
        model["narrative_units"][1]["causal_contract"]["new_information_needed_for_reality_action"] = True
        with self.assertRaisesRegex(ha1.CandidateError, "execution-ready"):
            ha1.validate_stage_model(model, {})

    def test_unknown_physical_target_city_fails(self) -> None:
        model = self.model()
        model["world_setting_architecture"]["threat_mechanism"]["physical_target_city_id"] = "HST-CITY-MISSING"
        with self.assertRaisesRegex(ha1.CandidateError, "unknown city"):
            ha1.validate_stage_model(model, {})


class StorylineCarrierTests(unittest.TestCase):
    def model(self) -> dict:
        return {
            "semantic_storyline_register": [
                {"source_storyline_id": "SL-MAIN"},
                {"source_storyline_id": "SL-BG"},
                {"source_storyline_id": "SL-OPEN"},
            ],
            "activation_disposition": [
                {"source_storyline_id": "SL-MAIN", "disposition": "placed"},
                {"source_storyline_id": "SL-BG", "disposition": "background-carried"},
                {"source_storyline_id": "SL-OPEN", "disposition": "preserved-open"},
            ],
            "storyline_segments": [
                {"id": "HTS-MAIN", "source_storyline_id": "SL-MAIN", "chapter_shell_ids": ["HCH-01-01"]},
                {"id": "HTS-BG", "source_storyline_id": "SL-BG", "chapter_shell_ids": ["HCH-01-01"]},
            ],
            "chapter_storyline_plan": [
                {
                    "id": "HCD-01-01",
                    "chapter_id": "HCH-01-01",
                    "chapter_number": 1,
                    "primary_storyline_id": "SL-MAIN",
                    "supporting_storyline_ids": [],
                    "background_storyline_ids": ["SL-BG"],
                    "preserved_open_storyline_ids": ["SL-OPEN"],
                }
            ],
            "storyline_connections": [], "convergence_and_split_points": [],
            "subject_reconstruction_test": {"verdict": "pass"},
        }

    def test_background_carrier_and_open_identity_pass(self) -> None:
        hs1.validate_stage_model(self.model(), {})

    def test_background_without_carrier_fails(self) -> None:
        model = self.model(); model["storyline_segments"] = []
        with self.assertRaisesRegex(hs1.CandidateError, "carrier segment"):
            hs1.validate_stage_model(model, {})

    def test_preserved_open_cannot_masquerade_as_placed(self) -> None:
        model = self.model()
        model["storyline_segments"].append(
            {"id": "HTS-OPEN", "source_storyline_id": "SL-OPEN", "chapter_shell_ids": ["HCH-01-01"]}
        )
        with self.assertRaisesRegex(hs1.CandidateError, "masquerade"):
            hs1.validate_stage_model(model, {})


class RelativeTimeBandTests(unittest.TestCase):
    def model(self) -> dict:
        return {
            "story_time_model": {"elapsed_day_span": {"start_day": 0, "end_day": 42}},
            "narrative_order_map": [
                {"unit_id": "HNU-01", "narrative_position": 0}, {"unit_id": "HNU-02", "narrative_position": 1},
            ],
            "unit_duration_density": [
                {"id": "HTM-D1", "unit_id": "HNU-01", "story_duration_class": "short", "discourse_density": "balanced", "elapsed_start_day": 0, "elapsed_end_day": 7},
                {"id": "HTM-D2", "unit_id": "HNU-02", "story_duration_class": "long", "discourse_density": "expanded", "elapsed_start_day": 8, "elapsed_end_day": 42},
            ],
            "space_transition_map": [], "parallel_synchronization": [],
            "pacing_curve": [{"unit_id": "HNU-01"}, {"unit_id": "HNU-02"}],
            "tension_curve": [{"unit_id": "HNU-01", "level": "low"}, {"unit_id": "HNU-02", "level": "high"}],
            "recovery_windows": [{"after_unit_ids": ["HNU-02"]}],
            "continuity_ledger": [{"unit_id": "HNU-01"}, {"unit_id": "HNU-02"}],
        }

    def test_six_week_relative_bands_pass(self) -> None:
        hr1.validate_stage_model(self.model(), {})

    def test_overlapping_time_bands_fail(self) -> None:
        model = self.model(); model["unit_duration_density"][1]["elapsed_start_day"] = 7
        with self.assertRaisesRegex(hr1.CandidateError, "strictly ordered"):
            hr1.validate_stage_model(model, {})


if __name__ == "__main__":
    unittest.main()
