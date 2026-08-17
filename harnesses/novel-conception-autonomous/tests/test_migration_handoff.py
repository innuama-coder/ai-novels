from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .test_baseline import DOMAINS, PREFIXES, SourceFixture, write_json


baseline = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.baseline"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)
handoff_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.migration_handoff"
)


MIGRATOR = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "novel-interview-b0-migrator"
    / "scripts"
)


class MigrationHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.sources = SourceFixture(self.root / "legacy")
        self.candidate = self.root / "candidate"
        self.finalized = self.root / "finalized"
        self.finalization = self.finalized / "migration-finalization.json"
        self.production_run_id = "RUN-PRODUCTION-NEW-001"
        self._build_finalized_migration()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, script: str, *args: Path) -> None:
        process = subprocess.run(
            [sys.executable, str(MIGRATOR / script), *(str(arg) for arg in args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        if process.returncode != 0:
            self.fail(f"{script} failed: {process.stdout}\n{process.stderr}")

    def _build_finalized_migration(self) -> None:
        plan = self.root / "projection-plan.json"
        write_json(
            plan,
            {
                "schema_version": "1.0",
                "migration_id": "MIG-TEST-001",
                "run_id": self.sources.run_id,
                "inputs": {
                    **{
                        domain: str(self.sources.completions[domain])
                        for domain in DOMAINS
                    },
                    "V1": str(self.sources.v1),
                    "V2": str(self.sources.v2),
                    "approval": str(self.sources.approval),
                },
                "stage_projections": [
                    {
                        "stage": domain,
                        "sections": [
                            {
                                "control_id": f"{PREFIXES[domain]}-001",
                                "hardness": (
                                    "author_open" if domain == "I5" else "author_locked"
                                ),
                                "heading": (
                                    f"[{PREFIXES[domain]}-001]"
                                    f"[{'author_open' if domain == 'I5' else 'author_locked'}] "
                                    f"{domain} exact control"
                                ),
                            }
                        ],
                    }
                    for domain in DOMAINS
                ],
                "fact_candidates": [
                    {
                        "id": "FACT-001",
                        "proposed_status": "not_applicable",
                        "claim": "The conception has no external factual dependency.",
                        "rationale": "All relevant rules are explicitly fictional.",
                    }
                ],
            },
        )
        self._run("build_candidate.py", plan, self.candidate)
        candidate_manifest = self.candidate / "candidate-manifest.json"
        decision = self.root / "author-decision.json"
        write_json(
            decision,
            {
                "schema_version": "1.0",
                "kind": "interview-b0-migration-author-decision",
                "migration_id": "MIG-TEST-001",
                "source_run_id": self.sources.run_id,
                "candidate_manifest_sha256": canonical.sha256_file(candidate_manifest),
                "decision": "approved",
                "author_role": "author",
                "control_decisions": [
                    {"id": f"{PREFIXES[domain]}-001", "decision": "accept"}
                    for domain in DOMAINS
                ],
                "fact_decisions": [{"id": "FACT-001", "decision": "accept"}],
            },
        )
        self._run("finalize_migration.py", self.candidate, decision, self.finalized)

    def _gate(self):
        controller = coordinator.AutonomousCoordinator.initialize(
            run_id=self.production_run_id,
            source_interview_state={"path": "migration-finalization.json", "sha256": canonical.sha256_file(self.finalization)},
            state_path="state/revision-000.json",
        )
        return controller.build_input_gate("B0", "B0/input-gate.json")

    def test_finalized_handoff_builds_cross_run_baseline(self) -> None:
        admitted = handoff_runtime.validate_finalized_migration_handoff(
            self.finalization
        )
        self.assertEqual(self.sources.run_id, admitted.source_run_id)

        package = self.root / "production" / "B0"
        result = baseline.build_baseline_from_handoff(
            package,
            production_run_id=self.production_run_id,
            input_gate=self._gate(),
            migration_finalization=self.finalization,
        )

        self.assertEqual(self.production_run_id, result.baseline["run_id"])
        self.assertEqual(self.sources.run_id, result.baseline["source_run_id"])
        self.assertIn("migration_finalization", result.baseline)
        baseline.validate_baseline_package(package)

    def test_waiting_author_candidate_and_tampered_decision_fail_closed(self) -> None:
        with self.assertRaises(handoff_runtime.MigrationHandoffError):
            handoff_runtime.validate_finalized_migration_handoff(
                self.candidate / "candidate-manifest.json"
            )

        decision_path = self.finalized / "compatibility-decision.json"
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        decision["control_decisions"] = decision["control_decisions"][:-1]
        write_json(decision_path, decision)
        finalization = json.loads(self.finalization.read_text(encoding="utf-8"))
        finalization["compatibility_decision"]["sha256"] = canonical.sha256_file(decision_path)
        write_json(self.finalization, finalization)
        with self.assertRaises(handoff_runtime.MigrationHandoffError) as caught:
            handoff_runtime.validate_finalized_migration_handoff(self.finalization)
        self.assertIn(
            caught.exception.code,
            {"B0_MIGRATION_APPROVAL_INCOMPLETE", "B0_MIGRATION_APPROVAL_INVALID"},
        )


if __name__ == "__main__":
    unittest.main()
