from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import unittest


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")


DIMENSIONS = (
    "author_control_fidelity",
    "world_story_character_fidelity",
    "omission_and_emphasis_fidelity",
    "fragment_authority_boundary",
    "review_decision_integrity",
)


def blocked_review() -> dict:
    ref = {"path": "P1/stage-completion.json", "sha256": "1" * 64}
    return {
        "schema_version": "2.0",
        "skill": "novel-conception-presentation-fidelity-reviewer",
        "run_id": "RUN-1",
        "h1_session_id": "H1-1",
        "reviewer": {
            "task_id": "review-task",
            "thread_id": "review-thread",
            "independence_basis": "separate-task-no-producer-context",
        },
        "inputs": {
            "p1_completion": ref,
            "plan_manifest": {"path": "H1/plan/package-manifest.json", "sha256": "2" * 64},
            "fragment_manifest": {"path": "H1/fragments/package-manifest.json", "sha256": "3" * 64},
            "report_sha256": "4" * 64,
        },
        "dimensions": [
            {
                "id": item,
                "verdict": "blocked",
                "evidence_element_ids": [],
                "finding": "Independent task identity cannot be established.",
            }
            for item in DIMENSIONS
        ],
        "element_reviews": [],
        "blockers": ["Independent task identity is unavailable."],
        "verdict": "blocked",
    }


class PresentationFidelityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = rt.ContractRuntime()

    def test_blocked_review_is_a_valid_auditable_output(self) -> None:
        self.runtime.validate(
            blocked_review(), "presentation-fidelity-review.schema.json"
        )

    def test_pass_cannot_retain_blockers(self) -> None:
        candidate = copy.deepcopy(blocked_review())
        candidate["verdict"] = "pass"
        with self.assertRaises(rt.ContractValidationError):
            self.runtime.validate(
                candidate, "presentation-fidelity-review.schema.json"
            )


if __name__ == "__main__":
    unittest.main()
