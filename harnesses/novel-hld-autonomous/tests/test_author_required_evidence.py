from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.design_stage_runtime import (  # noqa: E402
    AuthorityConflictRequired,
    AuthorRequired,
    UpstreamDefect,
    _author_required_gate,
)
from runtime.schema_catalog import SchemaCatalog  # noqa: E402


class AuthorRequiredEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schemas = ROOT / "schemas"
        cls.catalog = SchemaCatalog.from_documents(
            {
                name: json.loads((schemas / name).read_text(encoding="utf-8"))
                for name in ("common.schema.json", "design-gate-data.schema.json")
            }
        )

    def test_preserves_actionable_assessment_evidence_and_affected_obligations(self) -> None:
        error = AuthorRequired(
            [
                {
                    "id": "HDD-002",
                    "source_id": "SRC-B",
                    "affected_obligation_ids": ["HTS-002"],
                    "rationale_anchor": "locked B conflicts with event order",
                    "downstream_effect": "author must choose the authoritative ordering",
                },
                {
                    "id": "HDD-001",
                    "source_id": "SRC-A",
                    "affected_obligation_ids": ["HTS-001", "HTS-002"],
                    "rationale_anchor": "locked A conflicts with timestamp",
                    "downstream_effect": "HLD cannot place the unit without a source amendment",
                },
            ]
        )

        self.assertEqual(error.affected_ids, ["SRC-A", "SRC-B"])
        self.assertEqual(error.affected_obligation_ids, ["HTS-001", "HTS-002"])
        self.assertIn("SRC-A: locked A conflicts with timestamp", str(error))
        self.assertIn("SRC-B: locked B conflicts with event order", str(error))
        self.assertIn("affected obligations: HTS-001, HTS-002", str(error))
        self.assertIn("SRC-A, SRC-B", error.required_action)
        self.assertIn("受影响的设计内容：HTS-001, HTS-002", error.required_action)
        self.assertIn("后续设计不能替你猜测", error.required_action)

    def test_authority_conflict_keeps_source_routing_separate_from_hld_obligations(self) -> None:
        error = AuthorityConflictRequired(
            [
                {
                    "id": "HAC-CAUSAL-001",
                    "source_ids": ["EV-A", "CAU-B"],
                    "affected_obligation_ids": ["HTS-001"],
                    "conflict_statement": "EV-A occurs before the cause locked by CAU-B",
                    "author_choice_required": "move EV-A or amend CAU-B",
                    "downstream_effect": "HS1 cannot produce a causal placement",
                }
            ]
        )

        self.assertEqual(error.affected_ids, ["CAU-B", "EV-A"])
        self.assertEqual(error.affected_obligation_ids, ["HTS-001"])
        self.assertIn("affected obligations: HTS-001", str(error))
        self.assertIn("move EV-A or amend CAU-B", error.required_action)
        self.assertIn("CAU-B, EV-A", error.required_action)
        self.assertIn("受影响的设计内容：HTS-001", error.required_action)

    def test_empty_obligation_fallback_is_natural_chinese(self) -> None:
        error = AuthorRequired(
            [
                {
                    "id": "HDD-SOURCE-ONLY",
                    "source_id": "INT-OPEN",
                    "affected_obligation_ids": [],
                    "rationale_anchor": "构思资料需要作者澄清",
                    "downstream_effect": "后续设计必须等待",
                }
            ]
        )

        self.assertIn("无（仅需澄清构思来源）", error.required_action)
        self.assertNotIn("none", error.required_action.lower())

    def test_upstream_defect_preserves_stable_targets_and_action(self) -> None:
        error = UpstreamDefect(
            "unit POV cannot cover a chapter after the focal character loses consciousness",
            ["HPV-UNIT-01", "HPV-UNIT-01"],
            "return to HI1 and define effective chapter POV assignments",
        )

        self.assertEqual(error.affected_ids, ["HPV-UNIT-01"])
        self.assertIn("loses consciousness", str(error))
        self.assertEqual(error.required_action, "return to HI1 and define effective chapter POV assignments")

    def test_author_required_primary_source_is_deterministic(self) -> None:
        error = AuthorityConflictRequired(
            [
                {
                    "id": "HAC-STARTUP-001",
                    "source_ids": ["EV-TR-LATE", "EV-STEP-EARLY"],
                    "affected_obligation_ids": ["HST-ANCHOR-STARTUP"],
                    "conflict_statement": "the later state says the instance is not started",
                    "author_choice_required": "repair and reseal the conception event timeline",
                    "downstream_effect": "HLD cannot order acceptance and startup",
                }
            ]
        )

        self.assertEqual(error.affected_ids, ["EV-STEP-EARLY", "EV-TR-LATE"])
        self.assertTrue(error.required_action.startswith("已确认的构思资料彼此矛盾"))

    def test_author_required_gate_requires_routable_source_and_question(self) -> None:
        gate = {
            "schema_version": "1.0",
            "hld_run_id": "hld-fixture",
            "stage": "HA1",
            "failed_gate": "AUTHOR_REQUIRED",
            "evidence": "sealed event order is contradictory",
            "affected_ids": ["EV-STEP-EARLY", "EV-TR-LATE"],
            "source_control_id": "EV-STEP-EARLY",
            "question_text": "Repair and reseal the conception event timeline.",
        }
        self.catalog.validate(gate, "design-gate-data.schema.json")
        for missing in ("source_control_id", "question_text"):
            invalid = dict(gate)
            invalid.pop(missing)
            with self.assertRaises(Exception):
                self.catalog.validate(invalid, "design-gate-data.schema.json")

    def test_public_gate_builder_preserves_all_conflicts_and_routes_primary_source(self) -> None:
        error = AuthorityConflictRequired(
            [
                {
                    "id": "HAC-STARTUP-001",
                    "source_ids": ["EV-TR-LATE", "EV-STEP-EARLY"],
                    "affected_obligation_ids": ["HST-ANCHOR-STARTUP"],
                    "conflict_statement": "world-time order reverses the locked state",
                    "author_choice_required": "repair and reseal the event timeline",
                    "downstream_effect": "HA1 cannot provide an unambiguous startup anchor",
                }
            ]
        )
        context = SimpleNamespace(
            work_order={"hld_run_id": "hld-fixture"},
            contract={"stage": "HA1"},
        )
        gate = _author_required_gate(context, error)

        self.catalog.validate(gate, "design-gate-data.schema.json")
        self.assertEqual(gate["source_control_id"], "EV-STEP-EARLY")
        self.assertEqual(gate["affected_ids"], ["EV-STEP-EARLY", "EV-TR-LATE"])
        self.assertEqual(gate["question_text"], error.required_action)
        for value in ("EV-STEP-EARLY", "EV-TR-LATE", "HST-ANCHOR-STARTUP"):
            self.assertIn(value, gate["question_text"])

    def test_upstream_defect_gate_remains_valid_without_author_routing_fields(self) -> None:
        gate = {
            "schema_version": "1.0",
            "hld_run_id": "hld-fixture",
            "stage": "HA1",
            "failed_gate": "UPSTREAM_DEFECT",
            "evidence": "an upstream HLD object must change",
            "affected_ids": ["HST-ANCHOR-STARTUP"],
        }
        self.catalog.validate(gate, "design-gate-data.schema.json")


if __name__ == "__main__":
    unittest.main()
