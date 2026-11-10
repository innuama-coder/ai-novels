from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .test_baseline import DOMAINS, SourceFixture, write_json


baseline = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.baseline"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)
contracts = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.contracts"
)
completion_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.b0_completion"
)
revision_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.conception_revision"
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
                                "control_id": control["id"],
                                "hardness": control["hardness"],
                                "heading": (
                                    f"[{control['id']}][{control['hardness']}] "
                                    f"{control['heading']}"
                                ),
                            }
                            for control in baseline.extract_controls(
                                self.sources.projections[domain], domain
                            )
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
                    {"id": control["id"], "decision": "accept"}
                    for domain in DOMAINS
                    for control in baseline.extract_controls(
                        self.sources.projections[domain], domain
                    )
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
        self.assertEqual("compatibility_migration", result.baseline["source_kind"])
        self.assertNotIn("authority_revision_finalization", result.baseline)
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


class MigrationParentAuthorityRevisionTests(MigrationHandoffTests):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="migration-authority-b0-")
        self.root = Path(self.temporary.name)
        self.sources = SourceFixture(
            self.root / "legacy",
            authority_revision_controls=True,
            authority_revision_non_target_controls=19,
        )
        self.candidate = self.root / "candidate"
        self.finalized = self.root / "finalized"
        self.finalization = self.finalized / "migration-finalization.json"
        self.production_run_id = "RUN-MIGRATION-PARENT-001"
        self._build_finalized_migration()
        self.parent_b0 = self.root / "parent-production" / "B0"
        parent_owner = coordinator.AutonomousCoordinator.initialize(
            run_id=self.production_run_id,
            source_interview_state={
                "path": "source-interview-state.json",
                "sha256": canonical.sha256_file(self.sources.state),
            },
            state_path="state/revision-000.json",
        )
        parent_gate = parent_owner.build_input_gate("B0", "B0/input-gate.json")
        baseline.build_baseline_from_handoff(
            self.parent_b0,
            production_run_id=self.production_run_id,
            input_gate=parent_gate,
            migration_finalization=self.finalization,
        )
        completion_runtime.complete_b0(
            self.parent_b0,
            coordinator=parent_owner,
            input_gate=parent_gate,
            next_state_path="state/revision-001.json",
        )
        self._downgrade_parent_to_legacy_source_kind_shape()
        self.revision_run_id = "RUN-AUTHORITY-OVER-MIGRATION-001"
        self.revision_root = self.root / "revision-run"
        self._build_revision_fork()

    def _downgrade_parent_to_legacy_source_kind_shape(self) -> None:
        baseline_path = self.parent_b0 / "author-control-baseline.json"
        manifest_path = self.parent_b0 / "package-manifest.json"
        completion_path = self.parent_b0 / "stage-completion.json"
        model = json.loads(baseline_path.read_text(encoding="utf-8"))
        model.pop("source_kind")
        write_json(baseline_path, model)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = canonical.sha256_file(baseline_path)
        for item in manifest["files"]:
            if item["path"] == "author-control-baseline.json":
                item["sha256"] = digest
        manifest["artifact_roles"]["baseline"]["sha256"] = digest
        write_json(manifest_path, manifest)
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion.pop("source_kind", None)
        completion["manifest"]["sha256"] = canonical.sha256_file(manifest_path)
        write_json(completion_path, completion)

    def _build_revision_fork(self) -> None:
        handoff = handoff_runtime.validate_finalized_migration_handoff(self.finalization)
        evidence_parent = self.root / "parent-evidence"
        evidence_hld = self.root / "hld-evidence"
        evidence_parent.mkdir()
        evidence_hld.mkdir()
        roots = {"parent": evidence_parent, "hld": evidence_hld, "base": self.parent_b0}
        bindings = {}
        for label in sorted(revision_runtime.REQUIRED_EVIDENCE_LABELS):
            if label == "parent_state":
                parent_baseline = json.loads(
                    (self.parent_b0 / "author-control-baseline.json").read_text(
                        encoding="utf-8"
                    )
                )
                bindings[label] = {
                    "root": "base",
                    "artifact": parent_baseline["run_state"],
                }
                continue
            root_name = "parent" if label.startswith("parent_") else "hld"
            path = roots[root_name] / f"{label}.json"
            write_json(path, {"label": label})
            bindings[label] = {
                "root": root_name,
                "artifact": {"path": path.name, "sha256": canonical.sha256_file(path)},
            }
        edits = []
        for domain in ("I3", "I4", "I5"):
            path = handoff.control_projections[domain]
            data = path.read_bytes()
            parent_ref = {
                "path": path.relative_to(handoff.package_root).as_posix(),
                "sha256": canonical.sha256_file(path),
            }
            for index, control in enumerate(baseline.extract_controls(path, domain)):
                if control["id"] not in revision_runtime.AUTHORITY_REVISION_ALLOWSET:
                    continue
                old_text = str(control["value"])
                new_text = f"revised-{control['id']}"
                start = data.index(old_text.encode("utf-8"))
                edits.append(
                    {
                        "source_id": control["id"],
                        "domain": domain,
                        "hardness": control["hardness"],
                        "title": control["heading"],
                        "control_index": index,
                        "parent_artifact": parent_ref,
                        "parent_value_sha256": canonical.canonical_sha256(old_text),
                        "effective_value_sha256": canonical.canonical_sha256(new_text),
                        "start_byte": start,
                        "end_byte": start + len(old_text.encode("utf-8")),
                        "old_text": old_text,
                        "old_text_sha256": hashlib.sha256(old_text.encode("utf-8")).hexdigest(),
                        "new_text": new_text,
                        "new_text_sha256": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                        "directive_clause_refs": ["DIR-001"],
                    }
                )
        producer = {
            "actor_id": "migration-revision-producer",
            "session_id": "migration-revision-producer-session",
            "implementation_sha256": "1" * 64,
        }
        clauses = [{
            "clause_id": "DIR-001",
            "text": "只修订七项控制，其余父基线保持不变。",
            "evidence_labels": ["author_event", "hld_answer", "hld_resolution"],
        }]
        material = revision_runtime.build_authority_revision_review_material(
            run_id=self.revision_run_id,
            evidence_bindings=bindings,
            author_text="修订七项构思定义。",
            directive_clauses=clauses,
            text_edits=edits,
            producer_identity=producer,
        )
        review_root = self.root / "independent-review"
        review_path = review_root / "semantic-review.json"
        review = {
            "schema_version": "1.0",
            "kind": "authority-revision-semantic-review",
            "review_id": "migration-parent-review",
            "transaction_id": material["candidate_material_sha256"][:24],
            "run_id": self.revision_run_id,
            "candidate_material_sha256": material["candidate_material_sha256"],
            "reviewer": {
                "actor_id": "migration-revision-reviewer",
                "session_id": "migration-revision-review-session",
                "implementation_sha256": "2" * 64,
            },
            "producer": producer,
            "covered_ids": sorted(revision_runtime.AUTHORITY_REVISION_ALLOWSET),
            "item_reviews": [
                {"source_id": item, "verdict": "pass", "findings": []}
                for item in sorted(revision_runtime.AUTHORITY_REVISION_ALLOWSET)
            ],
            "reviewer_produced_patch": False,
            "verdict": "pass",
            "status": "sealed",
        }
        write_json(review_path, review)
        self.revision_arguments = {
            "run_id": self.revision_run_id,
            "source_root": handoff.package_root,
            "evidence_roots": roots,
            "evidence_bindings": bindings,
            "author_text": "修订七项构思定义。",
            "directive_clauses": clauses,
            "text_edits": edits,
            "producer_identity": producer,
            "semantic_review_root": review_root,
            "semantic_review": {
                "path": review_path.name,
                "sha256": canonical.sha256_file(review_path),
            },
        }
        self.revision = revision_runtime.initialize_conception_revision_run(
            evidence_parent,
            self.revision_root,
            **self.revision_arguments,
        )

    def _new_gate(self):
        owner = coordinator.AutonomousCoordinator.from_snapshot(
            self.revision.production.state.data,
            self.revision.production.state.reference,
        )
        return owner, owner.build_input_gate("B0", "B0/input-gate.json")

    def test_migration_parent_builds_current_authority_revision_b0(self) -> None:
        owner, gate = self._new_gate()
        package = self.root / "revision-production" / "B0"
        result = baseline.build_baseline_from_authority_revision(
            package,
            authority_revision_finalization=(
                self.revision_root / "authority-revision" / "finalization.json"
            ),
            authority_source_run_id=self.sources.run_id,
            authority_parent_b0_root=self.parent_b0,
            run_id=self.revision_run_id,
            input_gate=gate,
        )
        self.assertEqual("authority_revision", result.baseline["source_kind"])
        finalization = json.loads(
            (
                self.revision_root
                / "authority-revision"
                / "finalization.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(finalization["parent_run"], result.baseline["run_state"])
        parent_baseline_state = json.loads(
            (self.parent_b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )["run_state"]
        self.assertNotEqual(parent_baseline_state, result.baseline["run_state"])
        self.assertEqual(
            "compatibility_migration", result.baseline["base_source_kind"]
        )
        self.assertNotIn("migration_finalization", result.baseline)
        self.assertEqual("authority_revision", result.manifest["source_kind"])
        self.assertEqual(
            "compatibility_migration", result.manifest["base_source_kind"]
        )
        base_controls = []
        effective_controls = []
        parent_baseline = json.loads(
            (self.parent_b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        for domain in ("I3", "I4", "I5"):
            parent_artifact_ref = next(
                item["artifact"]
                for item in parent_baseline["design_artifacts"]
                if item["domain"] == domain
            )
            base_controls.extend(
                baseline.extract_controls(
                    self.parent_b0 / parent_artifact_ref["path"], domain
                )
            )
            artifact_ref = next(
                item["artifact"]
                for item in result.baseline["design_artifacts"]
                if item["domain"] == domain
            )
            effective_controls.extend(
                baseline.extract_controls(
                    package / artifact_ref["path"], domain
                )
            )
        self.assertEqual(26, len(base_controls))
        self.assertEqual(26, len(effective_controls))
        before = {item["id"]: item for item in base_controls}
        after = {item["id"]: item for item in effective_controls}
        self.assertEqual(set(before), set(after))
        changed = {
            source_id
            for source_id in before
            if before[source_id] != after[source_id]
        }
        self.assertEqual(revision_runtime.AUTHORITY_REVISION_ALLOWSET, changed)
        for source_id in set(before) - changed:
            self.assertEqual(before[source_id], after[source_id])
        for field in (
            "base_migration_finalization",
            "parent_b0_baseline",
            "parent_b0_completion",
            "parent_b0_manifest",
        ):
            self.assertEqual(result.baseline[field], result.manifest[field])
        self.assertEqual("ready", baseline.validate_baseline_package(package)["verdict"])
        if os.name == "nt":
            extended_package = Path("\\\\?\\" + str(package.resolve()))
            self.assertEqual(
                "ready",
                baseline.validate_baseline_package(extended_package)["verdict"],
            )
        receipt = completion_runtime.complete_b0(
            package,
            coordinator=owner,
            input_gate=gate,
            next_state_path="state/revision-001.json",
        )
        self.assertEqual("authority_revision", receipt.completion.data["source_kind"])
        self.assertEqual(
            "compatibility_migration",
            receipt.completion.data["base_source_kind"],
        )
        for field in (
            "base_migration_finalization",
            "parent_b0_baseline",
            "parent_b0_completion",
            "parent_b0_manifest",
        ):
            self.assertEqual(
                result.baseline[field], receipt.completion.data[field]
            )
        mixed = copy.deepcopy(result.baseline)
        mixed["migration_finalization"] = mixed["base_migration_finalization"]
        with self.assertRaises(contracts.ContractValidationError):
            contracts.ContractRuntime().validate(
                mixed, "author-control-baseline.schema.json"
            )

    def test_wrong_parent_chain_and_mixed_inputs_fail_closed(self) -> None:
        cases = ("baseline", "completion", "manifest", "migration")
        for case in cases:
            with self.subTest(case=case):
                parent = self.root / f"parent-{case}"
                shutil.copytree(self.parent_b0, parent)
                if case == "baseline":
                    path = parent / "author-control-baseline.json"
                elif case == "completion":
                    path = parent / "stage-completion.json"
                elif case == "manifest":
                    path = parent / "package-manifest.json"
                else:
                    model = json.loads(
                        (parent / "author-control-baseline.json").read_text(encoding="utf-8")
                    )
                    path = parent / model["migration_finalization"]["path"]
                path.write_bytes(path.read_bytes() + b" ")
                _, gate = self._new_gate()
                destination = self.root / f"bad-{case}-B0"
                with self.assertRaises(baseline.BaselineError):
                    baseline.build_baseline_from_authority_revision(
                        destination,
                        authority_revision_finalization=(
                            self.revision_root / "authority-revision" / "finalization.json"
                        ),
                        authority_source_run_id=self.sources.run_id,
                        authority_parent_b0_root=parent,
                        run_id=self.revision_run_id,
                        input_gate=gate,
                    )
                self.assertFalse(destination.exists())
        _, gate = self._new_gate()
        with self.assertRaisesRegex(baseline.BaselineError, "B0_SOURCE_KIND_CONFLICT"):
            baseline.build_baseline_from_authority_revision(
                self.root / "mixed-B0",
                authority_revision_finalization=(
                    self.revision_root / "authority-revision" / "finalization.json"
                ),
                authority_source_run_id=self.sources.run_id,
                authority_parent_b0_root=self.parent_b0,
                run_id=self.revision_run_id,
                input_gate=gate,
                source_root=self.parent_b0,
            )

    def test_wrong_current_parent_state_and_bootstrap_gate_fail_closed(self) -> None:
        parent_baseline = json.loads(
            (self.parent_b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        wrong_owner = coordinator.AutonomousCoordinator.initialize(
            run_id=self.revision_run_id,
            source_interview_state=parent_baseline["run_state"],
            state_path="state/revision-000.json",
        )
        wrong_gate = wrong_owner.build_input_gate("B0", "B0/input-gate.json")
        wrong_gate_destination = self.root / "wrong-bootstrap-gate-B0"
        with self.assertRaisesRegex(
            baseline.BaselineError, "B0_SOURCE_STATE_MISMATCH"
        ):
            baseline.build_baseline_from_authority_revision(
                wrong_gate_destination,
                authority_revision_finalization=(
                    self.revision_root / "authority-revision" / "finalization.json"
                ),
                authority_source_run_id=self.sources.run_id,
                authority_parent_b0_root=self.parent_b0,
                run_id=self.revision_run_id,
                input_gate=wrong_gate,
            )
        self.assertFalse(wrong_gate_destination.exists())

        tampered_revision = self.root / "revision-parent-state-tampered"
        shutil.copytree(self.revision_root, tampered_revision)
        finalization_path = (
            tampered_revision / "authority-revision" / "finalization.json"
        )
        finalization = json.loads(finalization_path.read_text(encoding="utf-8"))
        parent_state_path = tampered_revision / finalization["parent_run"]["path"]
        parent_state_path.write_bytes(parent_state_path.read_bytes() + b" ")
        _, gate = self._new_gate()
        tampered_destination = self.root / "wrong-parent-state-hash-B0"
        with self.assertRaises(baseline.BaselineError):
            baseline.build_baseline_from_authority_revision(
                tampered_destination,
                authority_revision_finalization=finalization_path,
                authority_source_run_id=self.sources.run_id,
                authority_parent_b0_root=self.parent_b0,
                run_id=self.revision_run_id,
                input_gate=gate,
            )
        self.assertFalse(tampered_destination.exists())

    def test_completion_rejects_same_hash_under_wrong_parent_state_path(self) -> None:
        owner, gate = self._new_gate()
        package = self.root / "completion-state-path-B0"
        baseline.build_baseline_from_authority_revision(
            package,
            authority_revision_finalization=(
                self.revision_root / "authority-revision" / "finalization.json"
            ),
            authority_source_run_id=self.sources.run_id,
            authority_parent_b0_root=self.parent_b0,
            run_id=self.revision_run_id,
            input_gate=gate,
        )
        wrong_source = copy.deepcopy(
            self.revision.production.state.data["source_interview_state"]
        )
        wrong_source["path"] = "foreign/parent-state.json"
        wrong_owner = coordinator.AutonomousCoordinator.initialize(
            run_id=self.revision_run_id,
            source_interview_state=wrong_source,
            state_path="state/revision-000.json",
        )
        with self.assertRaisesRegex(
            baseline.BaselineError, "B0_SOURCE_STATE_MISMATCH"
        ):
            completion_runtime.complete_b0(
                package,
                coordinator=wrong_owner,
                input_gate=gate,
                next_state_path="state/revision-001.json",
            )
        self.assertFalse((package / "stage-completion.json").exists())

    def test_missing_extra_edits_and_non_target_drift_fail_closed(self) -> None:
        for case in ("missing", "extra"):
            with self.subTest(case=case):
                arguments = copy.deepcopy(self.revision_arguments)
                edits = copy.deepcopy(arguments["text_edits"])
                if case == "missing":
                    edits.pop()
                else:
                    outside = copy.deepcopy(edits[0])
                    outside["source_id"] = "CAU-OUTSIDE-ALLOWSET"
                    edits.append(outside)
                arguments["text_edits"] = edits
                target = self.root / f"revision-{case}"
                with self.assertRaisesRegex(
                    revision_runtime.ConceptionRevisionError,
                    "REV_PATCH_ALLOWSET_INVALID",
                ):
                    revision_runtime.initialize_conception_revision_run(
                        self.root / "parent-evidence", target, **arguments
                    )
                self.assertFalse(target.exists())

        patch = self.revision.patch_plan.data
        artifact = next(item for item in patch["artifacts"] if item["domain"] == "I3")
        effective = self.revision_root / artifact["effective_artifact"]["path"]
        model = json.loads(effective.read_text(encoding="utf-8"))
        model["controls"].append({
            "id": "CHR-NON-TARGET-DRIFT",
            "hardness": "author_locked",
            "heading": "非目标漂移",
            "value": "不允许",
        })
        write_json(effective, model)
        _, gate = self._new_gate()
        destination = self.root / "non-target-drift-B0"
        with self.assertRaises(baseline.BaselineError):
            baseline.build_baseline_from_authority_revision(
                destination,
                authority_revision_finalization=(
                    self.revision_root / "authority-revision" / "finalization.json"
                ),
                authority_source_run_id=self.sources.run_id,
                authority_parent_b0_root=self.parent_b0,
                run_id=self.revision_run_id,
                input_gate=gate,
            )
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
