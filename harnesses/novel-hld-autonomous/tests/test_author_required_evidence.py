from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.design_stage_runtime import AuthorityConflictRequired, AuthorRequired  # noqa: E402


class AuthorRequiredEvidenceTests(unittest.TestCase):
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
        self.assertIn("Affected HLD obligations: HTS-001, HTS-002", error.required_action)
        self.assertIn("must not invent a local interpretation", error.required_action)

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


if __name__ == "__main__":
    unittest.main()
