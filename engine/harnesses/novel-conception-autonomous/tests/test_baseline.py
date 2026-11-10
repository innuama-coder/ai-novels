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
revision_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.conception_revision"
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
    def __init__(
        self,
        root: Path,
        *,
        authority_revision_controls: bool = False,
        authority_revision_non_target_controls: int = 0,
    ):
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
            authority_specs = {
                "I3": (
                    ("CHR-GU-HENG-MEMORY", "author_locked", "顾衡的记忆"),
                    ("CHR-ROLE-TIERS", "author_locked", "角色层级"),
                ),
                "I4": (
                    ("CAU-AUDIT-BOUNDARY", "author_locked", "审计边界"),
                    ("CAU-GLOBAL-SPINE", "author_locked", "全局主线"),
                    ("CAU-MAJOR-NODES", "author_locked", "主要节点"),
                ),
                "I5": (
                    ("NAR-FAIRNESS", "author_locked", "叙事公平"),
                    ("NAR-POV-ARCHITECTURE", "author_locked", "视角结构"),
                ),
            }
            if authority_revision_controls and authority_revision_non_target_controls:
                distribution = {"I3": 7, "I4": 6, "I5": 6}
                if authority_revision_non_target_controls != sum(distribution.values()):
                    raise ValueError(
                        "authority revision fixture supports exactly 19 non-target controls"
                    )
                authority_specs = {
                    item_domain: item_specs
                    + tuple(
                        (
                            f"{PREFIXES[item_domain]}-NON-TARGET-{index + 1:02d}",
                            "author_locked",
                            f"{item_domain} non-target {index + 1:02d}",
                        )
                        for index in range(distribution[item_domain])
                    )
                    for item_domain, item_specs in authority_specs.items()
                }
            specs = (
                authority_specs[domain]
                if authority_revision_controls and domain in authority_specs
                else ((f"{PREFIXES[domain]}-001", hardness, f"{domain} exact control"),)
            )
            values = {
                source_id: (
                    f"old-{source_id}"
                    if authority_revision_controls and domain in authority_specs
                    else f"{domain} verbatim authoritative value."
                )
                for source_id, _, _ in specs
            }
            artifact.parent.mkdir(parents=True, exist_ok=True)
            sections = [
                f"## [{source_id}][{item_hardness}] {title}\n\n{values[source_id]}"
                for source_id, item_hardness, title in specs
            ]
            artifact.write_text(
                f"# {domain}\n\n" + "\n\n".join(sections) + "\n",
                encoding="utf-8", newline="",
            )
            report_path = directory / "report.md"
            report_path.write_text(
                f"# {domain} complete interview report\n",
                encoding="utf-8",
                newline="",
            )
            projection_path = directory / "control-projection.json"
            controls = []
            evidence_bindings = []
            for index, (source_id, item_hardness, title) in enumerate(specs):
                marked_heading = f"[{source_id}][{item_hardness}] {title}"
                controls.append(
                    {
                        "id": source_id,
                        "hardness": item_hardness,
                        "heading": title,
                        "value": values[source_id],
                    }
                )
                evidence_bindings.append(
                    {
                        "control_id": source_id,
                        "ranges": [
                            {
                                "start_line": 3 + index * 4,
                                "end_line": (
                                    6 + index * 4
                                    if index < len(specs) - 1
                                    else 5 + index * 4
                                ),
                                "text_sha256": text_sha256(
                                    f"## {marked_heading}\n\n{values[source_id]}"
                                    + ("\n" if index < len(specs) - 1 else "")
                                ),
                            }
                        ],
                    }
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
                    "controls": controls,
                    "evidence_bindings": evidence_bindings,
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
        self.assertEqual("native", result.baseline["source_kind"])
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


class AuthorityRevisionBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="b0-authority-revision-")
        self.work = Path(self.temporary.name)
        self.sources = SourceFixture(
            self.work / "sources", authority_revision_controls=True
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_completed_revision_fork_builds_mutually_exclusive_b0(self) -> None:
        parent = self.work / "parent-run"
        parent.mkdir()
        hld = self.work / "hld"
        hld.mkdir()
        roots = {"source": self.sources.root, "parent": parent, "hld": hld}
        bindings = {}
        for label in sorted(revision_runtime.REQUIRED_EVIDENCE_LABELS):
            if label == "parent_state":
                bindings[label] = {
                    "root": "source",
                    "artifact": {
                        "path": self.sources.state.relative_to(self.sources.root).as_posix(),
                        "sha256": canonical.sha256_file(self.sources.state),
                    },
                }
                continue
            root_name = "parent" if label.startswith("parent_") else "hld"
            path = roots[root_name] / f"{label}.json"
            write_json(path, {"label": label})
            bindings[label] = {
                "root": root_name,
                "artifact": {"path": path.name, "sha256": canonical.sha256_file(path)},
            }
        title_by_id = {
            "CHR-GU-HENG-MEMORY": "顾衡的记忆",
            "CHR-ROLE-TIERS": "角色层级",
            "CAU-AUDIT-BOUNDARY": "审计边界",
            "CAU-GLOBAL-SPINE": "全局主线",
            "CAU-MAJOR-NODES": "主要节点",
            "NAR-FAIRNESS": "叙事公平",
            "NAR-POV-ARCHITECTURE": "视角结构",
        }
        edits = []
        for domain in ("I3", "I4", "I5"):
            projection = self.sources.projections[domain]
            data = projection.read_bytes()
            controls = baseline.extract_controls(projection, domain)
            parent_ref = {
                "path": projection.relative_to(self.sources.root).as_posix(),
                "sha256": canonical.sha256_file(projection),
            }
            for index, control in enumerate(controls):
                source_id = control["id"]
                old_text = f"old-{source_id}"
                new_text = f"new-{source_id}"
                start = data.index(old_text.encode("utf-8"))
                edits.append(
                    {
                        "source_id": source_id,
                        "domain": domain,
                        "hardness": control["hardness"],
                        "title": title_by_id[source_id],
                        "control_index": index,
                        "parent_artifact": parent_ref,
                        "parent_value_sha256": canonical.canonical_sha256(old_text),
                        "effective_value_sha256": canonical.canonical_sha256(new_text),
                        "start_byte": start,
                        "end_byte": start + len(old_text.encode("utf-8")),
                        "old_text": old_text,
                        "old_text_sha256": text_sha256(old_text),
                        "new_text": new_text,
                        "new_text_sha256": text_sha256(new_text),
                        "directive_clause_refs": ["DIR-001"],
                    }
                )
        run_id = "RUN-B0-AUTHORITY-REVISION-001"
        revision_root = self.work / "revision-run"
        producer = {
            "actor_id": "producer",
            "session_id": "producer-session",
            "implementation_sha256": "1" * 64,
        }
        clauses = [
            {
                "clause_id": "DIR-001",
                "text": "修正七项，其他构思保持不变。",
                "evidence_labels": ["author_event", "hld_answer", "hld_resolution"],
            }
        ]
        author_text = "只修正指定的七项构思定义。"
        review_material = revision_runtime.build_authority_revision_review_material(
            run_id=run_id,
            evidence_bindings=bindings,
            author_text=author_text,
            directive_clauses=clauses,
            text_edits=edits,
            producer_identity=producer,
        )
        review_root = self.work / "independent-review"
        review_path = review_root / "semantic-review.json"
        write_json(
            review_path,
            {
                "schema_version": "1.0",
                "kind": "authority-revision-semantic-review",
                "review_id": "baseline-independent-review",
                "transaction_id": review_material["candidate_material_sha256"][:24],
                "run_id": run_id,
                "candidate_material_sha256": review_material["candidate_material_sha256"],
                "reviewer": {
                    "actor_id": "reviewer",
                    "session_id": "reviewer-session",
                    "implementation_sha256": "2" * 64,
                },
                "producer": producer,
                "covered_ids": sorted(revision_runtime.AUTHORITY_REVISION_ALLOWSET),
                "item_reviews": [
                    {"source_id": source_id, "verdict": "pass", "findings": []}
                    for source_id in sorted(revision_runtime.AUTHORITY_REVISION_ALLOWSET)
                ],
                "reviewer_produced_patch": False,
                "verdict": "pass",
                "status": "sealed",
            },
        )
        revision = revision_runtime.initialize_conception_revision_run(
            parent,
            revision_root,
            run_id=run_id,
            source_root=self.sources.root,
            evidence_roots=roots,
            evidence_bindings=bindings,
            author_text=author_text,
            directive_clauses=clauses,
            text_edits=edits,
            producer_identity=producer,
            semantic_review_root=review_root,
            semantic_review={
                "path": review_path.name,
                "sha256": canonical.sha256_file(review_path),
            },
        )
        owner = coordinator.AutonomousCoordinator.from_snapshot(
            revision.production.state.data,
            revision.production.state.reference,
        )
        gate = owner.build_input_gate("B0", "B0/input-gate.json")
        build_args = self.sources.build_args(self.work / "B0", gate)
        package_root = build_args.pop("package_root")
        build_args.update(
            {
                "run_id": run_id,
            }
        )
        result = baseline.build_baseline_from_authority_revision(
            package_root,
            authority_revision_finalization=(
                revision_root / "authority-revision" / "finalization.json"
            ),
            authority_source_run_id=self.sources.run_id,
            **build_args,
        )
        self.assertEqual("authority_revision", result.baseline["source_kind"])
        finalization = json.loads(
            (revision_root / "authority-revision" / "finalization.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(finalization["parent_run"], result.baseline["run_state"])
        self.assertIn("authority_revision_finalization", result.baseline)
        self.assertNotIn("migration_finalization", result.baseline)
        execution = json.loads(
            (result.package_root / "baseline-execution.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            "runtime/conception_revision.py",
            {
                record["identity"]
                for record in execution["implementation_catalog"]
            },
        )
        self.assertEqual("ready", baseline.validate_baseline_package(result.package_root)["verdict"])
        receipt = completion.complete_b0(
            result.package_root,
            coordinator=owner,
            input_gate=gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )
        self.assertEqual("authority_revision", receipt.completion.data["source_kind"])
        self.assertEqual(
            result.baseline["authority_revision_finalization"],
            receipt.completion.data["authority_revision"],
        )


class BaselineRemainingTests(BaselineTests):
    test_approved_sources_build_lossless_package_and_advance_run_state = None

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

    def test_b0_identity_excludes_export_aggregator_but_keeps_runtime_exact(self) -> None:
        result = self.build()
        execution = json.loads(
            (result.package_root / "baseline-execution.json").read_text(
                encoding="utf-8"
            )
        )
        identities = {
            item["identity"] for item in execution["implementation_catalog"]
        }
        self.assertNotIn("runtime/__init__.py", identities)
        self.assertEqual(
            {f"runtime/{name}" for name in baseline.B0_REQUIRED_RUNTIME_FILES},
            {identity for identity in identities if identity.startswith("runtime/")},
        )

        harness_manifest = json.loads(
            (
                Path(baseline.__file__).resolve().parents[1] / "manifest.yaml"
            ).read_text(encoding="utf-8")
        )
        contract = harness_manifest["b0_implementation_identity_contract"]
        self.assertEqual(
            sorted(f"runtime/{name}" for name in baseline.B0_REQUIRED_RUNTIME_FILES),
            sorted(contract["required_runtime_files"]),
        )
        self.assertEqual(
            list(baseline.B0_LEGACY_AGGREGATE_EXPORT_IDENTITIES),
            contract["legacy_stored_extras"],
        )
        self.assertEqual(
            sorted(baseline.TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256),
            sorted(contract["trusted_legacy_catalog_sha256"]),
        )
        self.assertEqual(
            sorted(baseline.TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES),
            sorted(contract["trusted_legacy_missing_current_identities"]),
        )
        self.assertEqual(
            baseline.TRUSTED_LEGACY_MISMATCH_BINDINGS,
            contract["trusted_legacy_mismatch_bindings"],
        )

    def test_legacy_stored_export_aggregator_is_a_compatible_extra(self) -> None:
        self.build()
        aggregate_source = Path(baseline.__file__).resolve().parent / "__init__.py"
        aggregate_copy = self.package / "implementation/runtime/__init__.py"
        aggregate_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(aggregate_source, aggregate_copy)
        aggregate_reference = canonical.artifact_reference(
            aggregate_copy, root=self.package
        )

        execution_path = self.package / "baseline-execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["implementation"].append(copy.deepcopy(aggregate_reference))
        execution["implementation"].sort(key=lambda item: item["path"])
        execution["implementation_catalog"].append(
            {
                "identity": "runtime/__init__.py",
                "artifact": copy.deepcopy(aggregate_reference),
            }
        )
        execution["implementation_catalog"].sort(
            key=lambda item: item["identity"]
        )
        write_json(execution_path, execution)

        manifest_path = self.package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(copy.deepcopy(aggregate_reference))
        manifest["files"].sort(key=lambda item: item["path"])
        manifest["implementation"].append(copy.deepcopy(aggregate_reference))
        manifest["implementation"].sort(key=lambda item: item["path"])
        write_json(manifest_path, manifest)
        self._refresh_manifest_file("baseline-execution.json")

        with mock.patch.object(
            baseline,
            "sha256_file",
            wraps=baseline.sha256_file,
        ) as digest:
            self.assertEqual(
                "ready", baseline.validate_baseline_package(self.package)["verdict"]
            )
        current_aggregate = aggregate_source.resolve()
        self.assertFalse(
            any(
                Path(call.args[0]).resolve() == current_aggregate
                for call in digest.call_args_list
            )
        )

        identity = "runtime/b0_implementation_identity.py"
        identity_copy = self.package / "implementation/runtime/b0_implementation_identity.py"
        identity_reference = next(
            item["artifact"]
            for item in execution["implementation_catalog"]
            if item["identity"] == identity
        )
        execution["implementation_catalog"] = [
            item
            for item in execution["implementation_catalog"]
            if item["identity"] != identity
        ]
        execution["implementation"] = [
            item
            for item in execution["implementation"]
            if item["path"] != identity_reference["path"]
        ]
        write_json(execution_path, execution)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = [
            item
            for item in manifest["files"]
            if item["path"] != identity_reference["path"]
        ]
        manifest["implementation"] = [
            item
            for item in manifest["implementation"]
            if item["path"] != identity_reference["path"]
        ]
        write_json(manifest_path, manifest)
        self._refresh_manifest_file("baseline-execution.json")
        identity_copy.unlink()

        legacy_catalog = {
            item["identity"]: item["artifact"]["sha256"]
            for item in execution["implementation_catalog"]
        }
        legacy_digest = canonical.canonical_sha256(legacy_catalog)
        current_baseline = Path(baseline.__file__).resolve()
        real_sha256_file = canonical.sha256_file

        def later_validator_hash(path: str | Path) -> str:
            if Path(path).resolve() == current_baseline:
                return "0" * 64
            return real_sha256_file(path)

        simulated_mismatch_binding = {
            "runtime/baseline.py": {
                "stored_sha256": legacy_catalog["runtime/baseline.py"],
                "approved_current_sha256": "0" * 64,
            }
        }

        with mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256",
            frozenset({legacy_digest}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES",
            frozenset({identity}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISMATCH_BINDINGS",
            simulated_mismatch_binding,
        ), mock.patch.object(
            baseline, "sha256_file", side_effect=later_validator_hash
        ):
            self.assertEqual(
                "ready", baseline.validate_baseline_package(self.package)["verdict"]
            )

        with mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256",
            frozenset({legacy_digest}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES",
            frozenset({identity}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISMATCH_BINDINGS",
            {
                "runtime/baseline.py": {
                    **simulated_mismatch_binding["runtime/baseline.py"],
                    "approved_current_sha256": "f" * 64,
                }
            },
        ), mock.patch.object(
            baseline, "sha256_file", side_effect=later_validator_hash
        ):
            with self.assertRaises(baseline.BaselineError) as future_validator:
                baseline.validate_baseline_package(self.package)
        self.assertEqual(
            "B0_IMPLEMENTATION_STALE", future_validator.exception.code
        )

        schema_copy = self.work / "legacy-schema-mutants"
        shutil.copytree(baseline.ContractRuntime().schema_dir, schema_copy)
        owned_schema = schema_copy / "author-control-baseline.schema.json"
        owned_schema.write_text(
            owned_schema.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
            newline="",
        )
        with mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256",
            frozenset({legacy_digest}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES",
            frozenset({identity}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISMATCH_BINDINGS",
            simulated_mismatch_binding,
        ), mock.patch.object(
            baseline, "sha256_file", side_effect=later_validator_hash
        ):
            with self.assertRaises(baseline.BaselineError) as schema_drift:
                baseline.validate_baseline_package(
                    self.package,
                    runtime=baseline.ContractRuntime(schema_copy),
                )
        self.assertEqual("B0_IMPLEMENTATION_STALE", schema_drift.exception.code)

        execution["implementation_catalog"] = [
            item
            for item in execution["implementation_catalog"]
            if item["identity"] != "runtime/__init__.py"
        ]
        write_json(execution_path, execution)
        self._refresh_manifest_file("baseline-execution.json")
        with mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256",
            frozenset({legacy_digest}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES",
            frozenset({identity}),
        ), mock.patch.object(
            baseline,
            "TRUSTED_LEGACY_MISMATCH_BINDINGS",
            simulated_mismatch_binding,
        ), mock.patch.object(
            baseline, "sha256_file", side_effect=later_validator_hash
        ):
            with self.assertRaises(baseline.BaselineError) as caught:
                baseline.validate_baseline_package(self.package)
        self.assertEqual("B0_IMPLEMENTATION_STALE", caught.exception.code)

    def test_missing_required_runtime_binding_still_fails_closed(self) -> None:
        self.build()
        execution_path = self.package / "baseline-execution.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["implementation_catalog"] = [
            item
            for item in execution["implementation_catalog"]
            if item["identity"] != "runtime/canonical.py"
        ]
        write_json(execution_path, execution)
        self._refresh_manifest_file("baseline-execution.json")

        with self.assertRaises(baseline.BaselineError) as caught:
            baseline.validate_baseline_package(self.package)
        self.assertEqual("B0_IMPLEMENTATION_STALE", caught.exception.code)

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
