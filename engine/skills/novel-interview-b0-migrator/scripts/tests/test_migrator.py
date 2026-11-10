from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from migration_lib import (  # noqa: E402
    MigrationError,
    STAGES,
    build_candidate,
    finalize_candidate,
    sha256,
    validate_candidate_dir,
    validate_final_dir,
)


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(owner: Path, target: Path) -> dict[str, str]:
    import os
    return {"path": Path(os.path.relpath(target, owner.parent)).as_posix(), "sha256": sha256(target)}


class MigratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self._make_chain()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _make_chain(self) -> Path:
        run_id = "fixture-run"
        completions: dict[str, Path] = {}
        prefixes = {"I0": "INT", "I1": "SUB", "I2": "WLD", "I3": "CHR", "I4": "CAU", "I5": "NAR"}
        stage_plans = []
        for stage in STAGES:
            folder = self.root / "source" / stage
            design = folder / "design.md"
            design.parent.mkdir(parents=True, exist_ok=True)
            design.write_text(f"# Fixture\n\n## 元信息\n\nlegacy metadata\n\n## Control {stage}\n\nExact value for {stage}.\n", encoding="utf-8")
            completion = folder / "stage-completion.json"
            dump(completion, {
                "harness": "novel-conception-interview", "run_id": run_id, "stage": stage,
                "session_id": f"fixture-{stage}", "status": "ready", "design_artifact": "design.md",
                "design_artifact_sha256": sha256(design), "input_completions": [],
            })
            completions[stage] = completion
            stage_plans.append({"stage": stage, "sections": [{"control_id": f"{prefixes[stage]}-CONTROL", "hardness": "author_locked", "heading": f"Control {stage}"}]})

        state = self.root / "source" / "state.json"
        dump(state, {"harness": "novel-conception-interview", "run_id": run_id, "status": "ready"})
        v1_folder = self.root / "source" / "V1"
        v1_design = v1_folder / "design.md"
        v1_design.parent.mkdir(parents=True, exist_ok=True)
        v1_design.write_text("# V1\n\nready\n", encoding="utf-8")
        v1 = v1_folder / "stage-completion.json"
        dump(v1, {
            "harness": "novel-conception-interview", "run_id": run_id, "stage": "V1", "session_id": "v1",
            "status": "ready", "design_artifact": "design.md", "design_artifact_sha256": sha256(v1_design),
            "input_completions": [ref(v1, completions[stage]) for stage in STAGES],
        })
        v2_folder = self.root / "source" / "V2"
        brief = v2_folder / "brief.html"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text("<!doctype html><title>Approved brief</title>", encoding="utf-8")
        v2 = v2_folder / "stage-completion.json"
        dump(v2, {
            "harness": "novel-conception-interview", "run_id": run_id, "stage": "V2", "session_id": "v2",
            "status": "ready", "design_artifact": "brief.html", "design_artifact_sha256": sha256(brief),
            "input_completions": [ref(v2, v1)], "run_state": ref(v2, state),
        })
        approval = v2_folder / "author-approval.json"
        dump(approval, {
            "harness": "novel-conception-interview", "run_id": run_id, "approval_scope": "V2",
            "decision": "approved", "review_brief": ref(approval, brief),
        })
        plan_path = self.root / "projection-plan.json"
        dump(plan_path, {
            "schema_version": "1.0", "migration_id": "fixture-migration", "run_id": run_id,
            "inputs": {**{stage: str(completions[stage]) for stage in STAGES}, "V1": str(v1), "V2": str(v2), "approval": str(approval)},
            "stage_projections": stage_plans,
            "fact_candidates": [{"id": "FACT-NONE", "proposed_status": "not_applicable", "claim": "No adopted external fact.", "rationale": "Compatibility projection only."}],
        })
        return plan_path

    def _candidate(self) -> tuple[Path, dict]:
        target = self.root / "candidate"
        build_candidate(self.plan, target)
        return target, validate_candidate_dir(target)

    def _decision(self, candidate: dict, path: Path, omit_control: bool = False, stale: bool = False) -> Path:
        controls = candidate["control_ids"][:-1] if omit_control else candidate["control_ids"]
        dump(path, {
            "schema_version": "1.0", "kind": "interview-b0-migration-author-decision",
            "migration_id": candidate["manifest"]["migration_id"], "source_run_id": candidate["manifest"]["source_run_id"],
            "candidate_manifest_sha256": "0" * 64 if stale else sha256(candidate["manifest_path"]),
            "decision": "approved", "author_role": "author",
            "control_decisions": [{"id": item, "decision": "accept"} for item in controls],
            "fact_decisions": [{"id": item, "decision": "accept"} for item in candidate["fact_ids"]],
        })
        return path

    def test_candidate_is_waiting_author_and_has_no_generated_handoff(self) -> None:
        target, candidate = self._candidate()
        self.assertEqual(candidate["manifest"]["status"], "waiting_author")
        self.assertEqual(len(candidate["control_ids"]), 6)
        self.assertFalse((target / "handoff.json").exists())
        self.assertFalse((target / "author-decision.json").exists())
        for path in candidate["control_paths"].values():
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["status"], "waiting_author")

    def test_finalize_requires_exact_fresh_decision_and_is_self_contained(self) -> None:
        target, candidate = self._candidate()
        decision = self._decision(candidate, self.root / "author-decision.json")
        final = self.root / "final"
        finalize_candidate(target, decision, final)
        manifest = validate_final_dir(final)
        self.assertEqual(manifest["status"], "finalized")
        self.assertTrue((final / "candidate" / "migration-review.html").is_file())
        self.assertFalse((final / "handoff.json").exists())
        self.assertFalse((final / "author-approval.json").exists())

    def test_partial_and_stale_author_decisions_are_rejected(self) -> None:
        target, candidate = self._candidate()
        partial = self._decision(candidate, self.root / "partial.json", omit_control=True)
        with self.assertRaises(MigrationError):
            finalize_candidate(target, partial, self.root / "partial-final")
        stale = self._decision(candidate, self.root / "stale.json", stale=True)
        with self.assertRaises(MigrationError):
            finalize_candidate(target, stale, self.root / "stale-final")

    def test_metadata_selection_is_rejected(self) -> None:
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        plan["stage_projections"][0]["sections"][0]["heading"] = "元信息"
        bad = self.root / "metadata-plan.json"
        dump(bad, plan)
        with self.assertRaises(MigrationError):
            build_candidate(bad, self.root / "bad-candidate")

    def test_tampered_embedded_candidate_is_rejected(self) -> None:
        target, candidate = self._candidate()
        decision = self._decision(candidate, self.root / "author-decision.json")
        final = self.root / "final"
        finalize_candidate(target, decision, final)
        embedded_review = final / "candidate" / "migration-review.html"
        embedded_review.write_text(embedded_review.read_text(encoding="utf-8") + "tamper", encoding="utf-8")
        with self.assertRaises(MigrationError):
            validate_final_dir(final)


if __name__ == "__main__":
    unittest.main()
