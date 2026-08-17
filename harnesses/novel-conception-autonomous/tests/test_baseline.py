from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


baseline = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.baseline"
)
completion = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.b0_completion"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)


DOMAINS = ("I0", "I1", "I2", "I3", "I4", "I5")
PREFIXES = {
    "I0": "INT",
    "I1": "SUB",
    "I2": "WLD",
    "I3": "CHR",
    "I4": "CAU",
    "I5": "NAR",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical.canonical_json(value), encoding="utf-8", newline="")


def reference(owner: Path, target: Path, *, verdict: str | None = None) -> dict[str, str]:
    value = {
        "path": Path(
            os.path.relpath(target.resolve(), owner.parent.resolve())
        ).as_posix(),
        "sha256": canonical.sha256_file(target),
    }
    if verdict is not None:
        value["verdict"] = verdict
    return value


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SourceFixture:
    def __init__(self, root: Path):
        self.root = root
        self.run_id = "RUN-B0-001"
        self.completions: dict[str, Path] = {}
        self.projections: dict[str, Path] = {}
        for domain in DOMAINS:
            directory = root / "interviews" / domain
            state_path = directory / "run-state.input.json"
            write_json(
                state_path,
                {
                    "harness": "novel-conception-interview",
                    "run_id": self.run_id,
                    "active_return": None,
                    "current_interview_completions": {
                        item: reference(state_path, self.completions[item])
                        for item in DOMAINS[: DOMAINS.index(domain)]
                    },
                    "resolved_returns": [],
                },
            )
            artifact = directory / "design.md"
            hardness = "author_open" if domain == "I5" else "author_locked"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(
                f"# {domain}\n\n"
                f"## [{PREFIXES[domain]}-001][{hardness}] {domain} exact control\n\n"
                f"{domain} verbatim authoritative value.\n",
                encoding="utf-8",
                newline="",
            )
            report_path = directory / "report.md"
            report_path.write_text(
                f"# {domain} complete interview report\n",
                encoding="utf-8",
                newline="",
            )
            projection_path = directory / "control-projection.json"
            marked_heading = (
                f"[{PREFIXES[domain]}-001][{hardness}] {domain} exact control"
            )
            write_json(
                projection_path,
                {
                    "schema_version": "1.0",
                    "harness": "novel-conception-interview",
                    "run_id": self.run_id,
                    "stage": domain,
                    "session_id": f"SESSION-{domain}",
                    "status": "ready",
                    "source_artifact": reference(projection_path, artifact),
                    "controls": [
                        {
                            "id": f"{PREFIXES[domain]}-001",
                            "hardness": hardness,
                            "heading": f"{domain} exact control",
                            "value": f"{domain} verbatim authoritative value.",
                        }
                    ],
                    "evidence_bindings": [
                        {
                            "control_id": f"{PREFIXES[domain]}-001",
                            "ranges": [
                                {
                                    "start_line": 3,
                                    "end_line": 5,
                                    "text_sha256": text_sha256(
                                        f"## {marked_heading}\n\n"
                                        f"{domain} verbatim authoritative value."
                                    ),
                                }
                            ],
                        }
                    ],
                },
            )
            self.projections[domain] = projection_path
            validation_path = directory / "validation.json"
            write_json(
                validation_path,
                {"run_id": self.run_id, "verdict": "ready", "errors": []},
            )
            completion_path = directory / "stage-completion.json"
            write_json(
                completion_path,
                {
                    "contract_version": "2.0",
                    "harness": "novel-conception-interview",
                    "run_id": self.run_id,
                    "stage": domain,
                    "session_id": f"SESSION-{domain}",
                    "status": "ready",
                    "design_artifact": "design.md",
                    "design_artifact_sha256": canonical.sha256_file(artifact),
                    "report": reference(completion_path, report_path),
                    "control_projection": reference(
                        completion_path, projection_path
                    ),
                    "validation": reference(
                        completion_path, validation_path, verdict="ready"
                    ),
                    "input_completions": [
                        reference(completion_path, self.completions[item])
                        for item in DOMAINS[: DOMAINS.index(domain)]
                    ],
                    "run_state": reference(completion_path, state_path),
                },
            )
            self.completions[domain] = completion_path

        self.state = root / "interviews" / "V1" / "run-state.input.json"
        write_json(
            self.state,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "active_return": None,
                "current_interview_completions": {
                    domain: reference(self.state, self.completions[domain])
                    for domain in DOMAINS
                },
                "resolved_returns": [],
            },
        )

        self.fact_register = (
            root / "interviews" / "V1" / "fact-dependency-register.json"
        )
        write_json(
            self.fact_register,
            {
                "schema_version": "1.0",
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V1",
                "status": "ready",
                "fact_dependencies": [
                    {
                        "id": "FACT-001",
                        "status": "not_applicable",
                        "claim": "The conception has no external factual dependency.",
                        "rationale": "All relevant rules are explicitly fictional.",
                    }
                ],
            },
        )
        v1_validation = root / "interviews" / "V1" / "validation.json"
        write_json(
            v1_validation,
            {"run_id": self.run_id, "verdict": "ready", "errors": []},
        )
        v1_artifact = root / "interviews" / "V1" / "integrity-report.md"
        v1_artifact.write_text("# Complete integrity audit\n", encoding="utf-8")
        semantic = root / "interviews" / "V1" / "semantic-review.json"
        semantic_areas = {
            "intent": "I0",
            "subject": "I1",
            "world": "I2",
            "character": "I3",
            "causality": "I4",
            "narrative": "I5",
        }
        write_json(
            semantic,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V1",
                "verdict": "pass",
                "reviewer_role": "integrity_auditor",
                "return_package": None,
                "evidence": [
                    {
                        "control_area": area,
                        "owner_stage": stage,
                        "artifact": "design.md",
                        "finding": f"{area} has current evidence.",
                    }
                    for area, stage in semantic_areas.items()
                ],
            },
        )
        self.v1 = root / "interviews" / "V1" / "stage-completion.json"
        write_json(
            self.v1,
            {
                "contract_version": "2.0",
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V1",
                "session_id": "SESSION-V1",
                "status": "ready",
                "design_artifact": "integrity-report.md",
                "design_artifact_sha256": canonical.sha256_file(v1_artifact),
                "validation": reference(self.v1, v1_validation, verdict="ready"),
                "input_completions": [
                    reference(self.v1, self.completions[domain])
                    for domain in DOMAINS
                ],
                "fact_dependency_register": reference(
                    self.v1, self.fact_register
                ),
                "semantic_review": reference(self.v1, semantic),
                "run_state": reference(self.v1, self.state),
            },
        )

        v2_directory = root / "interviews" / "V2"
        self.brief = v2_directory / "review-brief.html"
        self.brief.parent.mkdir(parents=True, exist_ok=True)
        self.brief.write_text("<h1>Approved review brief</h1>", encoding="utf-8")
        v2_validation = v2_directory / "validation.json"
        write_json(
            v2_validation,
            {"run_id": self.run_id, "verdict": "ready", "errors": []},
        )
        self.v2 = v2_directory / "stage-completion.json"
        write_json(
            self.v2,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V2",
                "session_id": "SESSION-V2",
                "status": "ready",
                "design_artifact": "review-brief.html",
                "design_artifact_sha256": canonical.sha256_file(self.brief),
                "validation": reference(self.v2, v2_validation, verdict="ready"),
                "input_completions": [reference(self.v2, self.v1)],
                "run_state": reference(self.v2, self.state),
            },
        )
        self.approval = v2_directory / "author-approval.json"
        write_json(
            self.approval,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "approval_scope": "V2",
                "decision": "approved",
                "record_assurance": "self_recorded",
                "review_brief": reference(self.approval, self.brief),
                "approval_record": {
                    "event_seq": 1,
                    "text": "Approve this V2 review brief.",
                },
            },
        )

    def build_args(
        self,
        package_root: Path,
        gate: coordinator.SealedDocument,
    ) -> dict[str, object]:
        return {
            "package_root": package_root,
            "run_id": self.run_id,
            "input_gate": gate,
            "source_root": self.root,
            "source_interview_state": self.state,
            "design_completions": self.completions,
            "v1_completion": self.v1,
            "v2_completion": self.v2,
            "v2_author_approval": self.approval,
            "fact_dependency_register": self.fact_register,
        }


class BaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.sources = SourceFixture(self.work / "sources")
        source_state_reference = {
            "path": "interview/interview-state.json",
            "sha256": canonical.sha256_file(self.sources.state),
        }
        self.coordinator = coordinator.AutonomousCoordinator.initialize(
            run_id=self.sources.run_id,
            source_interview_state=source_state_reference,
            state_path="state/revision-000.json",
        )
        self.gate = self.coordinator.build_input_gate(
            "B0", "B0/input-gate.json"
        )
        self.package = self.work / "run" / "B0"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self) -> baseline.BaselineBuild:
        return baseline.build_baseline_package(
            **self.sources.build_args(self.package, self.gate)
        )

    def test_approved_sources_build_lossless_package_and_advance_run_state(self) -> None:
        result = self.build()

        self.assertEqual("ready", result.validation["verdict"])
        self.assertEqual(6, len(result.baseline["design_artifacts"]))
        self.assertEqual(
            {f"{PREFIXES[domain]}-001" for domain in DOMAINS},
            {item["id"] for item in result.baseline["control_registry"]},
        )
        self.assertEqual(["NAR-001"], result.baseline["open_items"])
        for entry in result.baseline["design_artifacts"]:
            self.assertIn(entry["artifact"], result.manifest["files"])
        baseline.validate_baseline_package(self.package)

        receipt = completion.complete_b0(
            self.package,
            coordinator=self.coordinator,
            input_gate=self.gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )

        self.assertEqual("B0", receipt.completion.data["stage"])
        self.assertEqual(1, receipt.transition.snapshot["revision"])
        self.assertEqual(
            receipt.completion.reference,
            receipt.transition.snapshot["current_stage_completions"]["B0"],
        )
        self.assertTrue((self.package / "stage-completion.json").is_file())

    def test_unapproved_source_is_blocked_without_candidate_package(self) -> None:
        approval = json.loads(self.sources.approval.read_text(encoding="utf-8"))
        approval["decision"] = "revise"
        write_json(self.sources.approval, approval)

        with self.assertRaises(baseline.BaselineError) as caught:
            self.build()

        self.assertEqual("B0_SOURCE_NOT_APPROVED", caught.exception.code)
        self.assertFalse(self.package.exists())
        self.assertEqual(0, self.coordinator.state["revision"])

    def test_forged_approval_and_incomplete_formal_completion_are_blocked(self) -> None:
        approval = json.loads(self.sources.approval.read_text(encoding="utf-8"))
        approval.pop("record_assurance")
        write_json(self.sources.approval, approval)
        with self.assertRaises(baseline.BaselineError) as forged:
            self.build()
        self.assertEqual("B0_SOURCE_NOT_APPROVED", forged.exception.code)
        self.assertFalse(self.package.exists())

        self._reset_fixture()
        i3 = self.sources.completions["I3"]
        packet = json.loads(i3.read_text(encoding="utf-8"))
        packet.pop("session_id")
        write_json(i3, packet)
        self._refresh_state_and_v1_references()
        with self.assertRaises(baseline.BaselineError) as incomplete:
            self.build()
        self.assertEqual("B0_SOURCE_COMPLETION_INVALID", incomplete.exception.code)
        self.assertFalse(self.package.exists())

    def test_duplicate_control_conflict_is_blocked(self) -> None:
        projection_path = self.sources.projections["I0"]
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        duplicate = copy.deepcopy(projection["controls"][0])
        duplicate["value"] = "Conflicting second value."
        projection["controls"].append(duplicate)
        projection["evidence_bindings"].append(
            copy.deepcopy(projection["evidence_bindings"][0])
        )
        write_json(projection_path, projection)
        self._refresh_projection_completion("I0")

        with self.assertRaises(baseline.BaselineError) as extraction:
            baseline.extract_controls(projection_path, "I0")
        self.assertEqual("B0_CONTROL_CONFLICT", extraction.exception.code)

        with self.assertRaises(baseline.BaselineError) as caught:
            self.build()

        self.assertEqual("B0_SOURCE_COMPLETION_INVALID", caught.exception.code)
        self.assertFalse(self.package.exists())

    def test_missing_control_evidence_and_missing_fact_register_are_hard_failures(self) -> None:
        projection_path = self.sources.projections["I2"]
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        projection["controls"][0]["value"] = ""
        write_json(projection_path, projection)
        self._refresh_projection_completion("I2")
        with self.assertRaises(baseline.BaselineError) as extraction:
            baseline.extract_controls(projection_path, "I2")
        self.assertEqual("B0_CONTROL_EVIDENCE_MISSING", extraction.exception.code)
        with self.assertRaises(baseline.BaselineError) as missing_evidence:
            self.build()
        self.assertEqual(
            "B0_SOURCE_COMPLETION_INVALID", missing_evidence.exception.code
        )
        self.assertFalse(self.package.exists())

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.sources = SourceFixture(self.work / "sources")
        self.coordinator = coordinator.AutonomousCoordinator.initialize(
            run_id=self.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": canonical.sha256_file(self.sources.state),
            },
            state_path="state/revision-000.json",
        )
        self.gate = self.coordinator.build_input_gate("B0", "B0/input-gate.json")
        self.package = self.work / "run" / "B0"
        self.sources.fact_register.unlink()
        with self.assertRaises(baseline.BaselineError) as missing_register:
            self.build()
        self.assertEqual("B0_SOURCE_MISSING", missing_register.exception.code)
        self.assertFalse(self.package.exists())

    def test_structural_unadopted_fact_is_blocked(self) -> None:
        register = json.loads(self.sources.fact_register.read_text(encoding="utf-8"))
        register["fact_dependencies"] = [
            {
                "id": "FACT-STRUCTURAL",
                "status": "open",
                "claim": "A structural real-world claim.",
                "blocking": True,
                "allowed_handling": "preserve_open",
                "rationale": "Research and author adoption are absent.",
            }
        ]
        write_json(self.sources.fact_register, register)
        self._refresh_v1_register_reference()

        with self.assertRaises(baseline.BaselineError) as caught:
            self.build()

        self.assertEqual("B0_SOURCE_COMPLETION_INVALID", caught.exception.code)
        self.assertFalse(self.package.exists())

    def test_tamper_blocks_completion_and_does_not_advance_coordinator(self) -> None:
        self.build()
        copied_artifact = next(
            path
            for path in (self.package / "sources").rglob("design.md")
            if "I0" in path.parts
        )
        copied_artifact.write_text("tampered", encoding="utf-8")

        with self.assertRaises(baseline.BaselineError) as caught:
            completion.complete_b0(
                self.package,
                coordinator=self.coordinator,
                input_gate=self.gate,
                logical_package_path="B0",
                next_state_path="state/revision-001.json",
            )

        self.assertEqual("B0_PACKAGE_INTEGRITY_FAILED", caught.exception.code)
        self.assertEqual(0, self.coordinator.state["revision"])
        self.assertFalse((self.package / "stage-completion.json").exists())

    def test_files_and_hashes_cannot_replace_semantic_completion(self) -> None:
        self.build()
        baseline_path = self.package / "author-control-baseline.json"
        model = json.loads(baseline_path.read_text(encoding="utf-8"))
        model["control_registry"][0]["value_sha256"] = "0" * 64
        write_json(baseline_path, model)
        self._refresh_manifest_file("author-control-baseline.json")

        with self.assertRaises(baseline.BaselineError) as caught:
            completion.complete_b0(
                self.package,
                coordinator=self.coordinator,
                input_gate=self.gate,
                logical_package_path="B0",
                next_state_path="state/revision-001.json",
            )

        self.assertEqual("B0_CONTROL_SET_MISMATCH", caught.exception.code)
        self.assertEqual(0, self.coordinator.state["revision"])
        self.assertFalse((self.package / "stage-completion.json").exists())

    def test_resealed_fact_or_implementation_drift_cannot_pass(self) -> None:
        self.build()
        baseline_path = self.package / "author-control-baseline.json"
        model = json.loads(baseline_path.read_text(encoding="utf-8"))
        model["fact_dependencies"][0]["claim"] = "A substituted claim."
        write_json(baseline_path, model)
        self._refresh_manifest_file("author-control-baseline.json")
        with self.assertRaises(baseline.BaselineError) as fact:
            baseline.validate_baseline_package(self.package)
        self.assertEqual("B0_FACT_REGISTER_MISMATCH", fact.exception.code)

        self._reset_fixture()
        self.build()
        copied_runtime = (
            self.package / "implementation" / "runtime" / "canonical.py"
        )
        copied_runtime.write_text(
            copied_runtime.read_text(encoding="utf-8") + "\n# drift\n",
            encoding="utf-8",
            newline="",
        )
        self._refresh_manifest_file("implementation/runtime/canonical.py")
        with self.assertRaises(baseline.BaselineError) as implementation:
            baseline.validate_baseline_package(self.package)
        self.assertEqual("B0_IMPLEMENTATION_STALE", implementation.exception.code)

    def test_stage_scoped_schema_dependencies_ignore_downstream_but_bind_b0(self) -> None:
        self.build()
        schema_copy = self.work / "schema-mutants"
        shutil.copytree(baseline.ContractRuntime().schema_dir, schema_copy)

        downstream = schema_copy / "world-model.schema.json"
        downstream.write_text(
            downstream.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
            newline="",
        )
        baseline.validate_baseline_package(
            self.package,
            runtime=baseline.ContractRuntime(schema_copy),
        )

        owned = schema_copy / "author-control-baseline.schema.json"
        owned.write_text(
            owned.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
            newline="",
        )
        with self.assertRaises(baseline.BaselineError) as caught:
            baseline.validate_baseline_package(
                self.package,
                runtime=baseline.ContractRuntime(schema_copy),
            )
        self.assertEqual("B0_IMPLEMENTATION_STALE", caught.exception.code)

    def test_current_b0_validator_digest_mutant_is_rejected(self) -> None:
        self.build()
        real_sha256_file = canonical.sha256_file
        validator_path = Path(baseline.__file__).resolve()

        def mutated_validator_hash(path: str | Path) -> str:
            if Path(path).resolve() == validator_path:
                return "0" * 64
            return real_sha256_file(path)

        with mock.patch.object(
            baseline, "sha256_file", side_effect=mutated_validator_hash
        ):
            with self.assertRaises(baseline.BaselineError) as caught:
                baseline.validate_baseline_package(self.package)
        self.assertEqual("B0_IMPLEMENTATION_STALE", caught.exception.code)

    def _reset_fixture(self) -> None:
        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.sources = SourceFixture(self.work / "sources")
        self.coordinator = coordinator.AutonomousCoordinator.initialize(
            run_id=self.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": canonical.sha256_file(self.sources.state),
            },
            state_path="state/revision-000.json",
        )
        self.gate = self.coordinator.build_input_gate("B0", "B0/input-gate.json")
        self.package = self.work / "run" / "B0"

    def _refresh_design_completion(self, domain: str) -> None:
        path = self.sources.completions[domain]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["design_artifact_sha256"] = canonical.sha256_file(
            path.parent / data["design_artifact"]
        )
        write_json(path, data)
        self._refresh_state_and_v1_references()

    def _refresh_projection_completion(self, domain: str) -> None:
        completion_path = self.sources.completions[domain]
        packet = json.loads(completion_path.read_text(encoding="utf-8"))
        packet["control_projection"] = reference(
            completion_path, self.sources.projections[domain]
        )
        write_json(completion_path, packet)
        self._refresh_state_and_v1_references()

    def _refresh_state_and_v1_references(self) -> None:
        for index, domain in enumerate(DOMAINS):
            path = self.sources.completions[domain]
            state_path = path.parent / "run-state.input.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_interview_completions"] = {
                prior: reference(state_path, self.sources.completions[prior])
                for prior in DOMAINS[:index]
            }
            write_json(state_path, state)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["input_completions"] = [
                reference(path, self.sources.completions[prior])
                for prior in DOMAINS[:index]
            ]
            data["run_state"] = reference(path, state_path)
            write_json(path, data)
        state = json.loads(self.sources.state.read_text(encoding="utf-8"))
        state["current_interview_completions"] = {
            domain: reference(self.sources.state, self.sources.completions[domain])
            for domain in DOMAINS
        }
        write_json(self.sources.state, state)
        v1 = json.loads(self.sources.v1.read_text(encoding="utf-8"))
        v1["input_completions"] = [
            reference(self.sources.v1, self.sources.completions[domain])
            for domain in DOMAINS
        ]
        v1["run_state"] = reference(self.sources.v1, self.sources.state)
        write_json(self.sources.v1, v1)
        v2 = json.loads(self.sources.v2.read_text(encoding="utf-8"))
        v2["input_completions"] = [reference(self.sources.v2, self.sources.v1)]
        v2["run_state"] = reference(self.sources.v2, self.sources.state)
        write_json(self.sources.v2, v2)

    def _refresh_v1_register_reference(self) -> None:
        v1 = json.loads(self.sources.v1.read_text(encoding="utf-8"))
        v1["fact_dependency_register"] = reference(
            self.sources.v1, self.sources.fact_register
        )
        write_json(self.sources.v1, v1)
        v2 = json.loads(self.sources.v2.read_text(encoding="utf-8"))
        v2["input_completions"] = [reference(self.sources.v2, self.sources.v1)]
        write_json(self.sources.v2, v2)

    def _refresh_manifest_file(self, relative_path: str) -> None:
        manifest_path = self.package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        new_reference = canonical.artifact_reference(
            self.package / relative_path, root=self.package
        )
        manifest["files"] = [
            new_reference if item["path"] == relative_path else item
            for item in manifest["files"]
        ]
        for role, item in list(manifest["artifact_roles"].items()):
            if item["path"] == relative_path:
                manifest["artifact_roles"][role] = copy.deepcopy(new_reference)
        manifest["implementation"] = [
            new_reference if item["path"] == relative_path else item
            for item in manifest["implementation"]
        ]
        write_json(manifest_path, manifest)


if __name__ == "__main__":
    unittest.main()
