from __future__ import annotations

import copy
import importlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
contracts = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.contracts"
)
coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)
routing = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.return_routing"
)
author_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.author_decision"
)
h1_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_completion"
)
final_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.final_completion"
)


ZERO_HASH = "0" * 64


def artifact(path: str, digest: str = ZERO_HASH) -> dict[str, str]:
    return {"path": path, "sha256": digest}


def stage_artifact(
    stage: str, path: str, digest: str = ZERO_HASH
) -> dict[str, str]:
    return {"stage": stage, "path": path, "sha256": digest}


def completion_for(gate: coordinator.SealedDocument) -> coordinator.SealedDocument:
    data = gate.data
    stage = data["target_stage"]
    body = {
        "schema_version": "2.0",
        "run_id": data["run_id"],
        "stage": stage,
        "status": "ready",
        "manifest": artifact(
            f"{stage}/package-manifest.json",
            canonical.canonical_sha256({"stage": stage, "kind": "manifest"}),
        ),
        "validation": artifact(
            f"{stage}/validation.json",
            canonical.canonical_sha256({"stage": stage, "kind": "validation"}),
        ),
        "input_gate": copy.deepcopy(gate.reference),
        "state_before": copy.deepcopy(data["run_state"]),
        "previous_stage_completions": copy.deepcopy(
            data["upstream_completions"]
        ),
        "return_binding": copy.deepcopy(data["return_binding"]),
    }
    if stage in {"S1", "W1", "E1", "T1", "C1", "Q1", "H1"}:
        body["session_id"] = f"SESSION-{stage}"
    return coordinator.seal_stage_document(
        body, stage, f"{stage}/stage-completion.json"
    )


def advance_to_waiting_author(
    subject: coordinator.AutonomousCoordinator,
) -> dict[str, coordinator.SealedDocument]:
    completed: dict[str, coordinator.SealedDocument] = {}
    for stage in coordinator.STAGE_ORDER:
        gate = subject.build_input_gate(stage, f"{stage}/input-gate.json")
        completion = completion_for(gate)
        subject.accept_stage_completion(
            gate=gate,
            completion=completion,
            next_state_path=(
                f"state/revision-{subject.state['revision'] + 1:03d}.json"
            ),
            h1_workspace=(
                artifact(
                    "H1/workspace-rendered.json",
                    canonical.canonical_sha256(
                        {"stage": "H1", "state": "rendered"}
                    ),
                )
                if stage == "H1"
                else None
            ),
        )
        completed[stage] = completion
    return completed


def advance_through_p1(
    subject: coordinator.AutonomousCoordinator,
) -> dict[str, coordinator.SealedDocument]:
    completed: dict[str, coordinator.SealedDocument] = {}
    for stage in coordinator.STAGE_ORDER:
        if stage == "H1":
            break
        gate = subject.build_input_gate(stage, f"{stage}/input-gate.json")
        completion = completion_for(gate)
        subject.accept_stage_completion(
            gate=gate,
            completion=completion,
            next_state_path=(
                f"state/revision-{subject.state['revision'] + 1:03d}.json"
            ),
        )
        completed[stage] = completion
    return completed


def package_bindings() -> tuple[dict[str, str], dict[str, str]]:
    return (
        {
            "completion_path": "P1/stage-completion.json",
            "completion_sha256": "1" * 64,
            "manifest_path": "P1/package-manifest.json",
            "manifest_sha256": "2" * 64,
        },
        {
            "completion_path": "H1/stage-completion.json",
            "completion_sha256": "3" * 64,
            "manifest_path": "H1/package-manifest.json",
            "manifest_sha256": "4" * 64,
            "html_path": "H1/html/human-review-report.html",
            "html_sha256": "5" * 64,
        },
    )


def author_decision(
    branch: str, *, event_seq: int = 1, text: str | None = None
) -> coordinator.SealedDocument:
    machine, human = package_bindings()
    body = {
        "schema_version": "2.0",
        "run_id": "RUN-014",
        "approval_scope": "conception",
        "decision": branch,
        "machine_package": machine,
        "human_review_package": human,
    }
    if branch == "approved":
        body["approval_record"] = {
            "event_seq": event_seq,
            "text": text or "批准当前构思",
        }
        body["unresolved_items"] = []
    elif branch == "rejected":
        body["rejection_record"] = {
            "event_seq": event_seq,
            "text": text or "拒绝当前构思",
        }
    elif branch == "revise":
        body["revision_record"] = {
            "event_seq": event_seq,
            "text": text or "请修订意图目标",
        }
        body["revision_targets"] = [
            {
                "target_scope": "conception",
                "visible_element_ids": [],
                "source_ids": ["INT-001"],
                "requested_change": "修订意图目标",
            }
        ]
    else:
        raise AssertionError(branch)
    return coordinator.seal_document(
        body, f"author/{branch}-decision.json"
    )


PROFILE_ROLES = {
    "baseline": ("baseline", "control_coverage", "execution_record"),
    "generated-model": (
        "canonical",
        "generation_session",
        "generation_evidence_index",
        "execution_record",
        "preview",
    ),
    "independent-review": (
        "canonical",
        "generation_session",
        "generation_evidence_index",
        "execution_record",
        "preview",
        "handoff_evidence",
    ),
    "conception-package": (
        "conception_package",
        "author_control_baseline",
        "authoritative_design_index",
        "spec",
        "cross_model_index",
        "traceability",
        "development_handoff",
        "execution_record",
    ),
    "h1-plan": (
        "source_inventory",
        "review_plan",
        "fragment_briefs",
        "generation_session",
        "generation_evidence_index",
        "execution_record",
    ),
    "h1-fragments": (
        "fragment_package",
        "fragments",
        "generation_session",
        "session_workspace_completion",
        "generation_evidence_index",
        "execution_record",
    ),
    "h1-assembly": (
        "human_review_report_json",
        "human_review_report_md",
        "presentation_fidelity_review",
        "execution_record",
    ),
    "h1-html": ("html", "render_record"),
    "h1-stage": (
        "plan_manifest",
        "fragment_manifest",
        "assembly_manifest",
        "html_manifest",
    ),
}


def write_formal_package(
    root: Path,
    *,
    profile: str,
    stage: str | None = None,
    run_id: str = "RUN-014",
    session_id: str = "H1-SESSION-014",
    parent_state_sha256: str = ZERO_HASH,
) -> Path:
    root.mkdir(parents=True)
    roles: dict[str, dict[str, str]] = {}
    for index, role in enumerate(PROFILE_ROLES[profile], start=1):
        suffix = ".html" if role == "html" else ".json"
        path = root / "artifacts" / f"{index:02d}-{role}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".html":
            path.write_text("<!doctype html><title>review</title>", encoding="utf-8")
        else:
            path.write_text(
                canonical.canonical_json(
                    {"schema_version": "2.0", "role": role}
                ),
                encoding="utf-8",
                newline="",
            )
        roles[role] = artifact(
            path.relative_to(root).as_posix(),
            canonical.sha256_file(path),
        )
    validation_path = root / "validation.json"
    validation_path.write_text(
        canonical.canonical_json({"verdict": "ready"}),
        encoding="utf-8",
        newline="",
    )
    implementation_path = root / "implementation" / "fixture.py"
    implementation_path.parent.mkdir(parents=True)
    implementation_path.write_text("# controlled fixture\n", encoding="utf-8")
    files = [
        artifact(
            path.relative_to(root).as_posix(),
            canonical.sha256_file(path),
        )
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]
    manifest = {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": stage
        or ("P1" if profile == "conception-package" else "H1"),
        "package_profile": profile,
        "verdict": "ready",
        "files": files,
        "artifact_roles": roles,
        "validation": artifact(
            "validation.json", canonical.sha256_file(validation_path)
        ),
        "implementation": [
            artifact(
                "implementation/fixture.py",
                canonical.sha256_file(implementation_path),
            )
        ],
    }
    if manifest["stage"] == "H1":
        manifest["session_id"] = session_id
        manifest["parent_state_sha256"] = parent_state_sha256
    (root / "package-manifest.json").write_text(
        canonical.canonical_json(manifest),
        encoding="utf-8",
        newline="",
    )
    return root


def rewrite_manifest(
    root: Path,
    *,
    role_updates: dict[str, dict[str, str]] | None = None,
) -> dict:
    manifest_path = root / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if role_updates:
        manifest["artifact_roles"].update(role_updates)
    manifest["files"] = [
        artifact(
            path.relative_to(root).as_posix(),
            canonical.sha256_file(path),
        )
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
        and path.name not in {
            "package-manifest.json",
            "stage-completion.json",
        }
    ]
    manifest_path.write_text(
        canonical.canonical_json(manifest),
        encoding="utf-8",
        newline="",
    )
    return manifest


class AuthorRevisionContractTests(unittest.TestCase):
    """The public contract must represent the workflow's author→I0 route."""

    def test_author_locked_intent_revision_routes_to_i0_and_validates(self):
        runtime = contracts.ContractRuntime()

        request = routing.route_return(
            run_id="RUN-014",
            return_id="RET-AUTHOR-I0-001",
            origin_kind="author",
            origin_stage=None,
            issue_kind="author_locked",
            problem="作者要求修正意图卡中的目标定义",
            evidence_ids=["INT-001"],
            violated_contract="§14.1 author-locked source ownership",
            required_revision="由 I0 修订该作者锁定事实并重跑全部自主阶段",
            author_decision=artifact(
                "author/author-decision.json", "1" * 64
            ),
            has_current_author_decision=True,
            has_current_conception_completion=False,
            runtime=runtime,
        )

        runtime.validate(request, "return-request.schema.json")
        self.assertEqual("I0", request["calculated_owner"])
        self.assertEqual("I0", request["target_stage"])
        self.assertEqual("B0", request["resume_stage"])
        self.assertEqual("B0", request["resume_point"])
        self.assertEqual(
            ["B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"],
            request["invalidated_stages"],
        )
        self.assertTrue(request["invalidate_author_decision"])
        self.assertTrue(request["invalidate_conception_completion"])

    def test_mixed_author_locked_owners_are_rejected_fail_closed(self):
        with self.assertRaises(routing.ReturnRoutingError) as caught:
            routing.route_return(
                run_id="RUN-014",
                return_id="RET-AUTHOR-MIXED-001",
                origin_kind="author",
                origin_stage=None,
                issue_kind="author_locked",
                problem="一次决定混合修改意图和世界事实",
                evidence_ids=["INT-001", "WLD-001"],
                violated_contract="§14.1 single deterministic owner",
                required_revision="拆分为两个独立作者决定",
                author_decision=artifact(
                    "author/author-decision.json", "1" * 64
                ),
                has_current_author_decision=True,
                has_current_conception_completion=False,
                runtime=contracts.ContractRuntime(),
            )
        self.assertEqual("ROUTE_AMBIGUOUS_OWNER", caught.exception.code)

    def test_author_decision_one_of_branches_are_exclusive(self):
        runtime = contracts.ContractRuntime()
        for branch in ("approved", "revise", "rejected"):
            runtime.validate(
                author_decision(branch).data,
                "author-decision.schema.json",
            )

        smuggled = copy.deepcopy(author_decision("approved").data)
        smuggled["rejection_record"] = {
            "event_seq": 1,
            "text": "跨分支字段不得被接纳",
        }
        with self.assertRaises(contracts.ContractValidationError):
            runtime.validate(smuggled, "author-decision.schema.json")


class AuthorDecisionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.subject = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-014",
            source_interview_state=artifact(
                "interview/run-state.json", "2" * 64
            ),
            state_path="state/revision-000.json",
        )
        self.completed = advance_to_waiting_author(self.subject)

    def test_approved_decision_preserves_all_nine_current_stages(self):
        decision = author_decision(
            "approved", event_seq=41, text="作者明确批准当前构思"
        )

        transition = self.subject.accept_author_decision(
            decision=decision,
            next_state_path="state/revision-010.json",
        )

        self.assertEqual("approved", transition.snapshot["status"])
        self.assertEqual(
            list(coordinator.STAGE_ORDER),
            list(transition.snapshot["current_stage_completions"]),
        )
        self.assertEqual(
            decision.reference, transition.snapshot["author_decision"]
        )
        self.assertIsNone(transition.snapshot["active_return"])
        self.assertEqual(
            "not_ready", transition.snapshot["development_status"]
        )

    def test_rejected_decision_is_terminal_but_not_development_ready(self):
        decision = author_decision(
            "rejected", event_seq=42, text="作者明确拒绝当前构思"
        )

        transition = self.subject.accept_author_decision(
            decision=decision,
            next_state_path="state/revision-010.json",
        )

        self.assertEqual("rejected", transition.snapshot["status"])
        self.assertEqual(
            decision.reference, transition.snapshot["author_decision"]
        )
        self.assertEqual(
            "not_ready", transition.snapshot["development_status"]
        )

    def test_decision_rejects_cross_run_and_stale_replay(self):
        wrong_run = author_decision("approved")
        wrong_data = copy.deepcopy(wrong_run.data)
        wrong_data["run_id"] = "RUN-OTHER"
        wrong_run = coordinator.seal_document(
            wrong_data, "author/cross-run-decision.json"
        )
        with self.assertRaises(coordinator.CoordinatorError):
            self.subject.accept_author_decision(
                decision=wrong_run,
                next_state_path="state/revision-010.json",
            )

        accepted = author_decision("approved", event_seq=9)
        self.subject.accept_author_decision(
            decision=accepted,
            next_state_path="state/revision-010.json",
        )
        conflicting = author_decision(
            "rejected", event_seq=9, text="同一序号的冲突裁决"
        )
        with self.assertRaises(coordinator.CoordinatorError):
            self.subject.accept_author_decision(
                decision=conflicting,
                next_state_path="state/revision-011.json",
            )

    def test_exact_decision_replay_is_idempotent(self):
        decision = author_decision("approved", event_seq=15)
        first = self.subject.accept_author_decision(
            decision=decision,
            next_state_path="state/revision-010.json",
        )
        second = self.subject.accept_author_decision(
            decision=decision,
            next_state_path="state/revision-010.json",
        )

        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.reference, second.reference)
        self.assertEqual(first.snapshot, second.snapshot)

    def test_revise_cannot_bypass_atomic_return_routing(self):
        with self.assertRaises(coordinator.CoordinatorError) as caught:
            self.subject.accept_author_decision(
                decision=author_decision("revise"),
                next_state_path="state/revision-010.json",
            )
        self.assertEqual(
            "COORD_AUTHOR_REVISE_REQUIRES_RETURN", caught.exception.code
        )
        self.assertEqual("waiting_author", self.subject.state["status"])
        self.assertIsNone(self.subject.state["author_decision"])
        self.assertIsNone(self.subject.state["active_return"])


class AuthorDecisionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.subject = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-014",
            source_interview_state=artifact(
                "interview/run-state.json", "2" * 64
            ),
            state_path="state/revision-000.json",
        )
        advance_to_waiting_author(self.subject)

    def test_external_approved_event_is_preserved_byte_for_value(self):
        event = author_decision(
            "approved",
            event_seq=91,
            text="这是作者明确提交的批准，不得改写或推断",
        )
        receipt = author_runtime.record_author_decision(
            event=event,
            coordinator=self.subject,
            next_state_path="state/revision-010.json",
        )

        self.assertIs(receipt.decision, event)
        self.assertEqual("approved", receipt.branch)
        self.assertIsNone(receipt.return_request)
        self.assertEqual(
            {
                "event_seq": 91,
                "text": "这是作者明确提交的批准，不得改写或推断",
            },
            receipt.decision.data["approval_record"],
        )
        self.assertEqual("approved", receipt.transition.snapshot["status"])

    def test_external_rejected_event_is_terminal_without_completion(self):
        event = author_decision(
            "rejected", event_seq=92, text="作者明确拒绝当前构思"
        )
        receipt = author_runtime.record_author_decision(
            event=event,
            coordinator=self.subject,
            next_state_path="state/revision-010.json",
        )

        self.assertIs(receipt.decision, event)
        self.assertEqual("rejected", receipt.branch)
        self.assertIsNone(receipt.return_request)
        self.assertEqual("rejected", receipt.transition.snapshot["status"])
        self.assertEqual(
            "not_ready", receipt.transition.snapshot["development_status"]
        )

    def test_revise_event_atomically_routes_i0_and_invalidates_all_stages(self):
        event = author_decision(
            "revise", event_seq=93, text="修订意图目标"
        )
        receipt = author_runtime.record_author_decision(
            event=event,
            coordinator=self.subject,
            next_state_path="state/revision-010.json",
            return_id="RET-AUTHOR-I0-093",
        )

        self.assertEqual("revise", receipt.branch)
        self.assertIs(receipt.decision, event)
        self.assertIsNotNone(receipt.return_request)
        request = receipt.return_request.data
        self.assertEqual("I0", request["calculated_owner"])
        self.assertEqual("B0", request["resume_stage"])
        self.assertEqual(list(coordinator.STAGE_ORDER), request["invalidated_stages"])
        self.assertEqual("revise", receipt.transition.snapshot["status"])
        self.assertEqual({}, receipt.transition.snapshot["current_stage_completions"])
        self.assertEqual(
            receipt.return_request.reference,
            receipt.transition.snapshot["active_return"],
        )
        self.assertIsNone(receipt.transition.snapshot["author_decision"])
        self.assertEqual(
            "stale_input", receipt.transition.snapshot["development_status"]
        )

    def test_cross_owner_revision_targets_are_rejected_without_state_change(self):
        event = author_decision("revise", event_seq=94)
        event_data = copy.deepcopy(event.data)
        event_data["revision_targets"].append(
            {
                "target_scope": "conception",
                "visible_element_ids": [],
                "source_ids": ["WLD-001"],
                "requested_change": "同时修订世界规则",
            }
        )
        event = coordinator.seal_document(
            event_data, "author/cross-owner-revise.json"
        )
        before = self.subject.state

        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.record_author_decision(
                event=event,
                coordinator=self.subject,
                next_state_path="state/revision-010.json",
            )
        self.assertEqual(
            "AUTHOR_DECISION_CROSS_OWNER_REVISION", caught.exception.code
        )
        self.assertEqual(before, self.subject.state)

    def test_stale_or_cross_run_external_event_is_rejected(self):
        event = author_decision("approved", event_seq=95)
        stale = coordinator.SealedDocument(
            data=copy.deepcopy(event.data),
            reference=artifact(event.reference["path"], "f" * 64),
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as stale_error:
            author_runtime.record_author_decision(
                event=stale,
                coordinator=self.subject,
                next_state_path="state/revision-010.json",
            )
        self.assertEqual(
            "AUTHOR_DECISION_STALE_EVENT", stale_error.exception.code
        )

        other_data = copy.deepcopy(event.data)
        other_data["run_id"] = "RUN-OTHER"
        other = coordinator.seal_document(
            other_data, "author/cross-run-approved.json"
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as cross_run:
            author_runtime.record_author_decision(
                event=other,
                coordinator=self.subject,
                next_state_path="state/revision-010.json",
            )
        self.assertEqual(
            "AUTHOR_DECISION_NOT_CURRENT", cross_run.exception.code
        )


class H1CompletionPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = contracts.ContractRuntime()
        self.subject = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-014",
            source_interview_state=artifact(
                "interview/run-state.json", "2" * 64
            ),
            state_path="state/revision-000.json",
            runtime=self.runtime,
        )
        self.completed = advance_through_p1(self.subject)
        self.gate = self.subject.build_input_gate(
            "H1", "H1/input-gate.json"
        )
        self.packages = {
            "p1": write_formal_package(
                self.root / "P1", profile="conception-package"
            ),
            "plan": write_formal_package(
                self.root / "H1" / "plan", profile="h1-plan"
            ),
            "fragment": write_formal_package(
                self.root / "H1" / "fragments", profile="h1-fragments"
            ),
            "assembly": write_formal_package(
                self.root / "H1" / "assembly", profile="h1-assembly"
            ),
            "html": write_formal_package(
                self.root / "H1" / "html", profile="h1-html"
            ),
        }
        manifest_refs = {
            "plan_manifest": artifact(
                "H1/plan/package-manifest.json",
                canonical.sha256_file(
                    self.packages["plan"] / "package-manifest.json"
                ),
            ),
            "fragment_manifest": artifact(
                "H1/fragments/package-manifest.json",
                canonical.sha256_file(
                    self.packages["fragment"] / "package-manifest.json"
                ),
            ),
            "assembly_manifest": artifact(
                "H1/assembly/package-manifest.json",
                canonical.sha256_file(
                    self.packages["assembly"] / "package-manifest.json"
                ),
            ),
            "html_manifest": artifact(
                "H1/html/package-manifest.json",
                canonical.sha256_file(
                    self.packages["html"] / "package-manifest.json"
                ),
            ),
        }
        rendered_data = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "stage": "H1",
            "session_id": "H1-SESSION-014",
            "state": "rendered",
            "p1_completion": copy.deepcopy(
                self.completed["P1"].reference
            ),
            "previous_state_sha256": "c" * 64,
            "artifacts": manifest_refs,
        }
        self.rendered = coordinator.seal_document(
            rendered_data, "H1/workspace-rendered.json"
        )
        dummy_workspace = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "stage": "H1",
            "session_id": "H1-SESSION-014",
        }
        self.plan_workspace = coordinator.seal_document(
            dummy_workspace, "H1/workspace-plan-fixture.json"
        )
        self.fragment_workspace = coordinator.seal_document(
            dummy_workspace, "H1/workspace-fragment-fixture.json"
        )
        self.assembly_workspace = coordinator.seal_document(
            dummy_workspace, "H1/workspace-assembly-fixture.json"
        )
        self.formal = mock.Mock()
        self.formal.validate_html_package.return_value = {
            "verdict": "ready"
        }

    def tearDown(self):
        self.temporary.cleanup()

    def _publish(
        self,
        name: str = "h1-stage",
        coordinator_value=None,
        next_state_path: str = "state/revision-009.json",
        logical_package_path: str = "H1/stage",
        admission_input_gate=None,
        active_return_request=None,
        plan_package=None,
        fragment_package=None,
        assembly_package=None,
        html_package=None,
        rendered_workspace=None,
    ):
        output = self.root / name
        with mock.patch.object(
            h1_runtime, "_html_validator", return_value=self.formal
        ):
            receipt = h1_runtime.publish_h1_completion(
                output,
                p1_package=self.packages["p1"],
                plan_package=plan_package or self.packages["plan"],
                plan_input_gate=self.gate,
                plan_workspace_state=self.plan_workspace,
                fragment_package=fragment_package or self.packages["fragment"],
                fragment_workspace_state=self.fragment_workspace,
                assembly_package=assembly_package or self.packages["assembly"],
                assembly_workspace_state=self.assembly_workspace,
                html_package=html_package or self.packages["html"],
                rendered_workspace=rendered_workspace or self.rendered,
                coordinator=coordinator_value or self.subject,
                next_state_path=next_state_path,
                logical_package_path=logical_package_path,
                admission_input_gate=admission_input_gate,
                active_return_request=active_return_request,
                runtime=self.runtime,
            )
        return output, receipt

    def test_all_attempt_qualified_h1_manifests_follow_rendered_workspace(self):
        roots = {}
        paths = {
            "plan": "H1/plan-attempt-03/package-manifest.json",
            "fragment": "H1/fragments-attempt-04/package-manifest.json",
            "assembly": "H1/assembly-attempt-03/package-manifest.json",
            "html": "H1/html-attempt-04/package-manifest.json",
        }
        for key, logical in paths.items():
            root = self.root.joinpath(*PurePosixPath(logical).parts[:-1])
            shutil.copytree(self.packages[key], root)
            roots[key] = root
        data = copy.deepcopy(self.rendered.data)
        for key, field in (
            ("plan", "plan_manifest"),
            ("fragment", "fragment_manifest"),
            ("assembly", "assembly_manifest"),
            ("html", "html_manifest"),
        ):
            data["artifacts"][field] = artifact(
                paths[key],
                canonical.sha256_file(roots[key] / "package-manifest.json"),
            )
        rendered = coordinator.seal_document(
            data, "H1/H1-SESSION-014/workspace-rendered-all-attempts.json"
        )

        _, receipt = self._publish(
            "all-attempt-qualified",
            plan_package=roots["plan"],
            fragment_package=roots["fragment"],
            assembly_package=roots["assembly"],
            html_package=roots["html"],
            rendered_workspace=rendered,
        )

        call = self.formal.validate_html_package.call_args
        self.assertEqual("H1/plan-attempt-03", call.kwargs["plan_logical_package_path"])
        self.assertEqual(
            "H1/fragments-attempt-04",
            call.kwargs["fragment_logical_package_path"],
        )
        self.assertEqual(
            "H1/assembly-attempt-03",
            call.kwargs["assembly_logical_package_path"],
        )
        self.assertEqual("waiting_author", receipt.transition.snapshot["status"])

    def _rendered_with_fragment(self, logical_path: str, fragment_root: Path):
        data = copy.deepcopy(self.rendered.data)
        data["artifacts"]["fragment_manifest"] = artifact(
            logical_path,
            canonical.sha256_file(fragment_root / "package-manifest.json"),
        )
        return coordinator.seal_document(
            data, "H1/H1-SESSION-014/workspace-rendered-fragment-relocation.json"
        )

    def test_fragment_manifest_uses_exact_attempt_qualified_workspace_path(self):
        nested = self.root / "H1" / "fragments-attempt-02"
        shutil.copytree(self.packages["fragment"], nested)
        rendered = self._rendered_with_fragment(
            "H1/fragments-attempt-02/package-manifest.json", nested
        )
        output, receipt = self._publish(
            "attempt-qualified-fragment",
            fragment_package=nested,
            rendered_workspace=rendered,
        )
        self.assertEqual(
            "H1/fragments-attempt-02",
            self.formal.validate_html_package.call_args.kwargs[
                "fragment_logical_package_path"
            ],
        )
        self.assertEqual("waiting_author", receipt.transition.snapshot["status"])
        copied = json.loads(
            (output / "sources/fragment-package-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            json.loads((nested / "package-manifest.json").read_text(encoding="utf-8")),
            copied,
        )

    def test_fragment_manifest_accepts_exact_nested_workspace_path(self):
        nested = self.root / "H1" / "H1-SESSION-014" / "h1-fragments-attempt-03"
        shutil.copytree(self.packages["fragment"], nested)
        rendered = self._rendered_with_fragment(
            "H1/H1-SESSION-014/h1-fragments-attempt-03/package-manifest.json",
            nested,
        )
        _, receipt = self._publish(
            "nested-fragment",
            fragment_package=nested,
            rendered_workspace=rendered,
        )
        self.assertEqual(
            "H1/H1-SESSION-014/h1-fragments-attempt-03",
            self.formal.validate_html_package.call_args.kwargs[
                "fragment_logical_package_path"
            ],
        )
        self.assertEqual("waiting_author", receipt.transition.snapshot["status"])

    def test_fragment_manifest_wrong_path_hash_and_parent_fail_before_output(self):
        cases = []
        wrong_path = self._rendered_with_fragment(
            "H1/fragments-attempt-99/package-manifest.json",
            self.packages["fragment"],
        )
        cases.append(("fragment-wrong-path", self.packages["fragment"], wrong_path))

        wrong_hash_data = copy.deepcopy(self.rendered.data)
        wrong_hash_data["artifacts"]["fragment_manifest"]["sha256"] = "f" * 64
        wrong_hash = coordinator.seal_document(
            wrong_hash_data, "H1/H1-SESSION-014/workspace-rendered-wrong-hash.json"
        )
        cases.append(("fragment-wrong-hash", self.packages["fragment"], wrong_hash))

        foreign = self.root / "foreign" / "fragments"
        shutil.copytree(self.packages["fragment"], foreign)
        foreign_rendered = self._rendered_with_fragment(
            "H1/fragments/package-manifest.json", foreign
        )
        cases.append(("fragment-foreign-parent", foreign, foreign_rendered))

        for name, package, rendered in cases:
            before = self.subject.state
            with self.assertRaises(h1_runtime.H1CompletionError) as caught:
                self._publish(
                    name,
                    fragment_package=package,
                    rendered_workspace=rendered,
                )
            self.assertEqual(
                "H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
                caught.exception.code,
            )
            self.assertEqual(before, self.subject.state)
            self.assertFalse((self.root / name).exists())

    def test_noncanonical_fragment_reference_fails_before_output(self):
        for marker, logical_path in (
            ("backslash", "H1\\fragments\\package-manifest.json"),
            ("escape", "H1/../fragments/package-manifest.json"),
        ):
            rendered = self._rendered_with_fragment(
                logical_path, self.packages["fragment"]
            )
            with self.assertRaises(h1_runtime.H1CompletionError):
                self._publish(
                    f"fragment-{marker}", rendered_workspace=rendered
                )
            self.assertFalse((self.root / f"fragment-{marker}").exists())

    def _activate_h1_return(self, marker: str = "REBIND"):
        request_data = routing.route_return(
            run_id="RUN-014",
            return_id=f"RET-H1-{marker}",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_fragment",
            problem="Independent H1 fidelity review requires local repair.",
            evidence_ids=[f"H1-EVIDENCE-{marker}"],
            violated_contract="H1 fragments must preserve source fidelity.",
            required_revision="Repair H1 without rewriting the sealed plan.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
            runtime=self.runtime,
        )
        request = coordinator.seal_document(
            request_data,
            f"returns/{request_data['return_id']}/return-request.json",
        )
        self.subject.apply_return_request(
            request=request,
            next_state_path="state/revision-009.json",
        )
        admission = self.subject.build_input_gate(
            "H1",
            "orchestration/input-gates/revision-009-H1-publish/input-gate.json",
            active_return_request=request,
        )
        return request, admission

    def test_normal_publish_records_plan_and_admission_gate(self):
        output, receipt = self._publish("normal-gate-binding")
        execution = json.loads(
            (output / "execution-record.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.gate.reference, execution["plan_input_gate"])
        self.assertEqual(self.gate.reference, execution["admission_input_gate"])
        self.assertEqual(self.gate.reference, receipt.completion.data["input_gate"])

    def test_internal_return_rebinds_admission_without_rewriting_plan(self):
        request, admission = self._activate_h1_return()
        output, receipt = self._publish(
            "return-gate-binding",
            admission_input_gate=admission,
            active_return_request=request,
            next_state_path="state/revision-010.json",
        )
        execution = json.loads(
            (output / "execution-record.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.gate.reference, execution["plan_input_gate"])
        self.assertEqual(admission.reference, execution["admission_input_gate"])
        self.assertEqual(admission.reference, receipt.completion.data["input_gate"])
        self.assertEqual(
            admission.data["return_binding"],
            receipt.completion.data["return_binding"],
        )
        self.assertIsNone(receipt.transition.snapshot["active_return"])
        self.assertEqual(
            request.data["return_id"],
            receipt.transition.snapshot["resolved_returns"][-1][
                "return_binding"
            ]["return_id"],
        )

    def test_rebinding_rejects_wrong_plan_and_stale_plan_without_output(self):
        request, admission = self._activate_h1_return("WRONG-PLAN")
        for name, field, value in (
            ("wrong-plan-target", "target_stage", "P1"),
            (
                "stale-plan-topology",
                "upstream_completions",
                [stage_artifact("P1", "P1/stale.json", "f" * 64)],
            ),
        ):
            data = copy.deepcopy(self.gate.data)
            data[field] = value
            wrong = coordinator.seal_document(data, f"H1/{name}.json")
            before = self.subject.state
            with self.assertRaises(h1_runtime.H1CompletionError) as caught:
                original = self.gate
                self.gate = wrong
                try:
                    self._publish(
                        name,
                        admission_input_gate=admission,
                        active_return_request=request,
                        next_state_path="state/revision-010.json",
                    )
                finally:
                    self.gate = original
            self.assertEqual(
                "H1_COMPLETION_GATE_REBINDING_INVALID", caught.exception.code
            )
            self.assertEqual(before, self.subject.state)
            self.assertFalse((self.root / name).exists())

    def test_rebinding_rejects_wrong_current_gate_and_return_without_output(self):
        request, admission = self._activate_h1_return("WRONG-CURRENT")
        wrong_gate_data = copy.deepcopy(admission.data)
        wrong_gate_data["run_state"] = artifact(
            "state/revision-stale.json", "e" * 64
        )
        wrong_gate = coordinator.seal_document(
            wrong_gate_data,
            "orchestration/input-gates/wrong-H1-publish/input-gate.json",
        )
        before = self.subject.state
        with self.assertRaises(h1_runtime.H1CompletionError) as gate_error:
            self._publish(
                "wrong-current-gate",
                admission_input_gate=wrong_gate,
                active_return_request=request,
                next_state_path="state/revision-010.json",
            )
        self.assertEqual("H1_COMPLETION_GATE_INVALID", gate_error.exception.code)
        self.assertEqual(before, self.subject.state)
        self.assertFalse((self.root / "wrong-current-gate").exists())

        other_data = copy.deepcopy(request.data)
        other_data["return_id"] = "RET-H1-FOREIGN"
        other = coordinator.seal_document(
            other_data, "returns/RET-H1-FOREIGN/return-request.json"
        )
        with self.assertRaises(coordinator.CoordinatorError) as return_error:
            self._publish(
                "wrong-current-return",
                admission_input_gate=admission,
                active_return_request=other,
                next_state_path="state/revision-010.json",
            )
        self.assertEqual(
            "COORD_ACTIVE_RETURN_REFERENCE_MISMATCH", return_error.exception.code
        )
        self.assertEqual(before, self.subject.state)
        self.assertFalse((self.root / "wrong-current-return").exists())

    def test_return_recovery_reuses_exact_package_and_resolves_once(self):
        request, admission = self._activate_h1_return("RECOVERY")
        name = "return-recovery"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                name,
                admission_input_gate=admission,
                active_return_request=request,
                next_state_path="../invalid-return-state.json",
            )
        before = h1_runtime._tree_inventory(self.root / name)
        _, receipt = self._publish(
            name,
            admission_input_gate=admission,
            active_return_request=request,
            next_state_path="state/revision-010.json",
        )
        self.assertTrue(receipt.replayed)
        self.assertEqual(before, h1_runtime._tree_inventory(self.root / name))
        self.assertEqual("waiting_author", self.subject.state["status"])

    def test_publish_calls_formal_h1c_and_advances_waiting_author_once(self):
        output, receipt = self._publish()

        self.assertGreaterEqual(
            self.formal.validate_html_package.call_count, 1
        )
        call = self.formal.validate_html_package.call_args
        self.assertIs(call.kwargs["runtime"], self.runtime)
        self.assertEqual(
            self.packages["html"].resolve(), Path(call.args[0]).resolve()
        )
        self.assertTrue((output / "stage-completion.json").is_file())
        self.assertTrue((output / "package-manifest.json").is_file())
        self.assertEqual("H1", receipt.completion.data["stage"])
        self.assertEqual(
            [self.completed["P1"].reference],
            receipt.completion.data["previous_stage_completions"],
        )
        self.assertEqual("waiting_author", receipt.transition.snapshot["status"])
        self.assertEqual(
            list(coordinator.STAGE_ORDER),
            list(receipt.transition.snapshot["current_stage_completions"]),
        )
        self.assertEqual(
            self.rendered.reference,
            receipt.transition.snapshot["h1_workspace"],
        )
        self.assertFalse(receipt.replayed)
        self.assertFalse(receipt.transition.replayed)

    def test_attempt_qualified_h1_completion_publishes_and_recovers_exactly(self):
        logical_root = "H1/stage-attempt-02"
        output, first = self._publish(
            "h1-stage-attempt-02",
            logical_package_path=logical_root,
            next_state_path="state/revision-attempt-02.json",
        )

        self.assertEqual(
            f"{logical_root}/stage-completion.json",
            first.completion.reference["path"],
        )
        self.assertEqual(
            f"{logical_root}/package-manifest.json",
            first.completion.data["manifest"]["path"],
        )
        before = h1_runtime._tree_inventory(output)
        reconstructed = coordinator.AutonomousCoordinator.from_snapshot(
            first.transition.snapshot,
            first.transition.reference,
            runtime=self.runtime,
        )
        _, replay = self._publish(
            "h1-stage-attempt-02",
            coordinator_value=reconstructed,
            logical_package_path=logical_root,
            next_state_path="state/revision-attempt-02.json",
        )

        self.assertTrue(replay.replayed)
        self.assertTrue(replay.transition.replayed)
        self.assertEqual(first.completion, replay.completion)
        self.assertEqual(before, h1_runtime._tree_inventory(output))

    def test_noncanonical_logical_package_path_fails_before_output(self):
        for name, logical_path in (
            ("different-logical-path", "H1/alternate"),
            ("zero-attempt", "H1/stage-attempt-0"),
            ("backslash-attempt", "H1\\stage-attempt-02"),
            ("escape-attempt", "H1/stage/../stage-attempt-02"),
        ):
            before = self.subject.state
            with self.assertRaises(h1_runtime.H1CompletionError) as caught:
                self._publish(name, logical_package_path=logical_path)
            self.assertEqual(
                "H1_COMPLETION_PATH_INVALID", caught.exception.code
            )
            self.assertEqual(before, self.subject.state)
            self.assertFalse((self.root / name).exists())

    def test_exact_orphan_recovery_reuses_package_then_advances_once(self):
        output = self.root / "recover-orphan"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                "recover-orphan",
                next_state_path="../invalid-state.json",
            )
        before = h1_runtime._tree_inventory(output)

        _, receipt = self._publish(
            "recover-orphan",
            next_state_path="state/recovered-h1.json",
        )

        self.assertTrue(receipt.replayed)
        self.assertFalse(receipt.transition.replayed)
        self.assertEqual("waiting_author", self.subject.state["status"])
        self.assertEqual(before, h1_runtime._tree_inventory(output))

    def test_waiting_author_persistent_forward_replay_is_idempotent(self):
        output, first = self._publish(
            "persistent-replay",
            next_state_path="state/persistent-h1.json",
        )
        reconstructed = coordinator.AutonomousCoordinator.from_snapshot(
            first.transition.snapshot,
            first.transition.reference,
            runtime=self.runtime,
        )
        before = h1_runtime._tree_inventory(output)

        _, replay = self._publish(
            "persistent-replay",
            coordinator_value=reconstructed,
            next_state_path="state/persistent-h1.json",
        )

        self.assertTrue(replay.replayed)
        self.assertTrue(replay.transition.replayed)
        self.assertEqual(first.transition.snapshot, replay.transition.snapshot)
        self.assertEqual(before, h1_runtime._tree_inventory(output))

    def test_atomic_publish_race_recovers_the_exact_winner(self):
        winner_coordinator = coordinator.AutonomousCoordinator.from_snapshot(
            self.subject.state,
            self.subject.state_reference,
            runtime=self.runtime,
        )
        winner_root, winner = self._publish(
            "independent-race-winner",
            coordinator_value=winner_coordinator,
            next_state_path="state/race-h1.json",
        )
        self.assertFalse(winner.replayed)
        winner_inventory = h1_runtime._tree_inventory(winner_root)
        raced = False

        def install_independent_winner(source, target):
            nonlocal raced
            self.assertNotEqual(source.resolve(), winner_root.resolve())
            shutil.copytree(winner_root, target)
            raced = True
            raise OSError("destination won publish race")

        revision_before = self.subject.state["revision"]
        with mock.patch.object(
            Path,
            "replace",
            autospec=True,
            side_effect=install_independent_winner,
        ):
            output, receipt = self._publish(
                "race-winner",
                next_state_path="state/race-h1.json",
            )

        self.assertTrue(raced)
        self.assertTrue(receipt.replayed)
        self.assertFalse(receipt.transition.replayed)
        self.assertTrue((output / "stage-completion.json").is_file())
        self.assertEqual("waiting_author", self.subject.state["status"])
        self.assertEqual(
            revision_before + 1, self.subject.state["revision"]
        )
        self.assertEqual(
            winner_inventory, h1_runtime._tree_inventory(output)
        )

    def test_existing_output_mutation_during_input_recheck_blocks_admission(self):
        output = self.root / "existing-output-toctou"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                "existing-output-toctou",
                next_state_path="../invalid-existing-toctou.json",
            )
        target = output / "validation.json"
        original = target.read_bytes()
        real_check = h1_runtime._require_unchanged_inputs

        def check_inputs_then_mutate(upstream):
            real_check(upstream)
            target.write_bytes(original + b"OUTPUT-RACE")

        before = self.subject.state
        with mock.patch.object(
            h1_runtime,
            "_require_unchanged_inputs",
            side_effect=check_inputs_then_mutate,
        ), self.assertRaises(h1_runtime.H1CompletionError) as caught:
            self._publish(
                "existing-output-toctou",
                next_state_path="state/existing-toctou.json",
            )

        self.assertEqual(
            "H1_COMPLETION_OUTPUT_MUTATED", caught.exception.code
        )
        self.assertEqual(before, self.subject.state)
        self.assertEqual(original + b"OUTPUT-RACE", target.read_bytes())

    def test_fresh_output_mutation_during_final_input_recheck_blocks_admission(
        self,
    ):
        output = self.root / "fresh-output-toctou"
        target = output / "validation.json"
        real_check = h1_runtime._require_unchanged_inputs
        mutated = False

        def check_inputs_then_mutate(upstream):
            nonlocal mutated
            real_check(upstream)
            if output.exists():
                target.write_bytes(target.read_bytes() + b"OUTPUT-RACE")
                mutated = True

        before = self.subject.state
        with mock.patch.object(
            h1_runtime,
            "_require_unchanged_inputs",
            side_effect=check_inputs_then_mutate,
        ), self.assertRaises(h1_runtime.H1CompletionError) as caught:
            self._publish(
                "fresh-output-toctou",
                next_state_path="state/fresh-toctou.json",
            )

        self.assertTrue(mutated)
        self.assertEqual(
            "H1_COMPLETION_OUTPUT_MUTATED", caught.exception.code
        )
        self.assertEqual(before, self.subject.state)
        self.assertTrue(target.read_bytes().endswith(b"OUTPUT-RACE"))

    def test_existing_partial_or_tampered_package_fails_without_overwrite(self):
        partial = self.root / "partial-existing"
        partial.mkdir()
        marker = partial / "forensic.txt"
        marker.write_text("preserve", encoding="utf-8")
        with self.assertRaises(h1_runtime.H1CompletionError):
            self._publish("partial-existing")
        self.assertEqual("preserve", marker.read_text(encoding="utf-8"))

        output = self.root / "tampered-existing"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                "tampered-existing",
                next_state_path="../invalid-tamper-state.json",
            )
        validation = output / "validation.json"
        validation.write_bytes(validation.read_bytes() + b" ")
        before = h1_runtime._tree_inventory(output)
        with self.assertRaises(h1_runtime.H1CompletionError):
            self._publish(
                "tampered-existing",
                next_state_path="state/tamper-recovery.json",
            )
        self.assertEqual(before, h1_runtime._tree_inventory(output))
        self.assertNotIn(
            "H1", self.subject.state["current_stage_completions"]
        )

        hidden = self.root / "hidden-extra-existing"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                "hidden-extra-existing",
                next_state_path="../invalid-hidden-state.json",
            )
        extra = hidden / "forensics" / "stage-completion.json"
        extra.parent.mkdir()
        extra.write_text("{}", encoding="utf-8")
        hidden_before = h1_runtime._tree_inventory(hidden)
        with self.assertRaises(h1_runtime.H1CompletionError):
            self._publish(
                "hidden-extra-existing",
                next_state_path="state/hidden-extra.json",
            )
        self.assertEqual(hidden_before, h1_runtime._tree_inventory(hidden))

    def test_existing_package_rejects_different_gate_and_current_source(self):
        output = self.root / "binding-existing"
        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(
                "binding-existing",
                next_state_path="../invalid-binding-state.json",
            )
        before = h1_runtime._tree_inventory(output)
        different_gate = coordinator.seal_document(
            self.gate.data,
            "H1/different-input-gate.json",
        )
        original_gate = self.gate
        self.gate = different_gate
        try:
            with self.assertRaises(h1_runtime.H1CompletionError):
                self._publish(
                    "binding-existing",
                    next_state_path="state/different-gate.json",
                )
        finally:
            self.gate = original_gate
        self.assertEqual(before, h1_runtime._tree_inventory(output))

        source = next(
            item
            for item in self.packages["plan"].rglob("*")
            if item.is_file()
            and item.name not in {
                "package-manifest.json",
                "validation.json",
            }
        )
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaises(h1_runtime.H1CompletionError):
            self._publish(
                "binding-existing",
                next_state_path="state/source-drift.json",
            )
        self.assertEqual(before, h1_runtime._tree_inventory(output))

    def test_persistent_recovery_rejects_foreign_state_and_different_path(self):
        output, first = self._publish(
            "persistent-conflict",
            next_state_path="state/exact-successor.json",
        )
        different_path = coordinator.AutonomousCoordinator.from_snapshot(
            first.transition.snapshot,
            first.transition.reference,
            runtime=self.runtime,
        )
        with self.assertRaises(coordinator.CoordinatorError) as path_error:
            self._publish(
                "persistent-conflict",
                coordinator_value=different_path,
                next_state_path="state/different-successor.json",
            )
        self.assertEqual(
            "COORD_ILLEGAL_STAGE_TRANSITION", path_error.exception.code
        )

        foreign = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-FOREIGN",
            source_interview_state=artifact(
                "interview/foreign-run-state.json", "3" * 64
            ),
            state_path="state/foreign-revision-000.json",
            runtime=self.runtime,
        )
        advance_through_p1(foreign)
        with self.assertRaises(h1_runtime.H1CompletionError) as foreign_error:
            self._publish(
                "persistent-conflict",
                coordinator_value=foreign,
                next_state_path="state/foreign-h1.json",
            )
        self.assertEqual(
            "H1_COMPLETION_GATE_INVALID", foreign_error.exception.code
        )
        self.assertTrue((output / "package-manifest.json").is_file())

    def test_formal_h1c_failure_propagates_before_publish_or_state_change(self):
        self.formal.validate_html_package.side_effect = RuntimeError(
            "FORMAL_H1C_REJECTED"
        )
        before = self.subject.state

        with self.assertRaisesRegex(RuntimeError, "FORMAL_H1C_REJECTED"):
            self._publish("formal-rejected")
        self.assertFalse((self.root / "formal-rejected").exists())
        self.assertEqual(before, self.subject.state)

    def test_non_rendered_or_stale_p1_workspace_is_rejected(self):
        bad_data = copy.deepcopy(self.rendered.data)
        bad_data["state"] = "assembled"
        bad_data["artifacts"].pop("html_manifest")
        bad = coordinator.seal_document(
            bad_data, "H1/workspace-not-rendered.json"
        )
        with mock.patch.object(
            h1_runtime, "_html_validator", return_value=self.formal
        ), self.assertRaises(h1_runtime.H1CompletionError) as caught:
            h1_runtime.publish_h1_completion(
                self.root / "not-rendered",
                p1_package=self.packages["p1"],
                plan_package=self.packages["plan"],
                plan_input_gate=self.gate,
                plan_workspace_state=self.plan_workspace,
                fragment_package=self.packages["fragment"],
                fragment_workspace_state=self.fragment_workspace,
                assembly_package=self.packages["assembly"],
                assembly_workspace_state=self.assembly_workspace,
                html_package=self.packages["html"],
                rendered_workspace=bad,
                coordinator=self.subject,
                next_state_path="state/revision-009.json",
                runtime=self.runtime,
            )
        self.assertEqual(
            "H1_COMPLETION_WORKSPACE_INVALID", caught.exception.code
        )
        self.assertFalse((self.root / "not-rendered").exists())

    def test_upstream_toctou_is_rejected_before_publish(self):
        real_write = h1_runtime._write
        mutated = False

        def write_then_mutate(path, value):
            nonlocal mutated
            real_write(path, value)
            if not mutated and Path(path).name == "execution-record.json":
                mutated = True
                source = next(
                    item
                    for item in self.packages["p1"].rglob("*")
                    if item.is_file()
                    and item.name not in {
                        "package-manifest.json",
                        "validation.json",
                    }
                )
                source.write_bytes(source.read_bytes() + b" ")

        before = self.subject.state
        with mock.patch.object(
            h1_runtime, "_html_validator", return_value=self.formal
        ), mock.patch.object(
            h1_runtime, "_write", side_effect=write_then_mutate
        ), self.assertRaises(h1_runtime.H1CompletionError) as caught:
            h1_runtime.publish_h1_completion(
                self.root / "toctou",
                p1_package=self.packages["p1"],
                plan_package=self.packages["plan"],
                plan_input_gate=self.gate,
                plan_workspace_state=self.plan_workspace,
                fragment_package=self.packages["fragment"],
                fragment_workspace_state=self.fragment_workspace,
                assembly_package=self.packages["assembly"],
                assembly_workspace_state=self.assembly_workspace,
                html_package=self.packages["html"],
                rendered_workspace=self.rendered,
                coordinator=self.subject,
                next_state_path="state/revision-009.json",
                runtime=self.runtime,
            )
        self.assertIn(
            caught.exception.code,
            {"H1_COMPLETION_P1_INVALID", "H1_COMPLETION_INPUT_MUTATED"},
        )
        self.assertFalse((self.root / "toctou").exists())
        self.assertEqual(before, self.subject.state)

    def test_atomic_replace_failure_does_not_advance_coordinator(self):
        before = self.subject.state
        with mock.patch.object(
            h1_runtime, "_html_validator", return_value=self.formal
        ), mock.patch.object(
            Path, "replace", side_effect=OSError("ATOMIC_REPLACE_FAILED")
        ), self.assertRaisesRegex(OSError, "ATOMIC_REPLACE_FAILED"):
            h1_runtime.publish_h1_completion(
                self.root / "replace-failed",
                p1_package=self.packages["p1"],
                plan_package=self.packages["plan"],
                plan_input_gate=self.gate,
                plan_workspace_state=self.plan_workspace,
                fragment_package=self.packages["fragment"],
                fragment_workspace_state=self.fragment_workspace,
                assembly_package=self.packages["assembly"],
                assembly_workspace_state=self.assembly_workspace,
                html_package=self.packages["html"],
                rendered_workspace=self.rendered,
                coordinator=self.subject,
                next_state_path="state/revision-009.json",
                runtime=self.runtime,
            )
        self.assertFalse((self.root / "replace-failed").exists())
        self.assertEqual(before, self.subject.state)

    def test_real_coordinator_rejection_leaves_only_valid_orphan_package(self):
        output = self.root / "coordinator-rejected"

        with self.assertRaises(coordinator.CoordinatorError) as caught:
            self._publish(
                "coordinator-rejected",
                next_state_path="../outside-run-state.json",
            )
        self.assertEqual("COORD_REFERENCE_INVALID", caught.exception.code)
        self.assertTrue((output / "stage-completion.json").is_file())
        self.assertNotIn(
            "H1", self.subject.state["current_stage_completions"]
        )
        self.assertEqual("running", self.subject.state["status"])
        with mock.patch.object(
            h1_runtime, "_html_validator", return_value=self.formal
        ):
            validation = h1_runtime.validate_h1_completion_package(
                output,
                p1_package=self.packages["p1"],
                plan_package=self.packages["plan"],
                plan_input_gate=self.gate,
                plan_workspace_state=self.plan_workspace,
                fragment_package=self.packages["fragment"],
                fragment_workspace_state=self.fragment_workspace,
                assembly_package=self.packages["assembly"],
                assembly_workspace_state=self.assembly_workspace,
                html_package=self.packages["html"],
                rendered_workspace=self.rendered,
                runtime=self.runtime,
            )
        self.assertEqual("ready", validation["verdict"])


class FinalCompletionPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = contracts.ContractRuntime()
        self.subject = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-014",
            source_interview_state=artifact(
                "interview/run-state.json", "2" * 64
            ),
            state_path="state/revision-000.json",
            runtime=self.runtime,
        )
        self.stage_packages: dict[str, Path] = {}
        self.html_package = write_formal_package(
            self.root / "html", profile="h1-html"
        )
        html_document = self.html_package / "human-review-report.html"
        html_document.write_text(
            (
                "<!doctype html><title>formal author review</title>"
                '<section data-element-id="NODE-001">review node</section>'
                "<p>NODE-TEXT-ONLY</p>"
            ),
            encoding="utf-8",
        )
        rewrite_manifest(self.html_package)

        profiles = {
            "B0": "baseline",
            "S1": "generated-model",
            "W1": "generated-model",
            "E1": "generated-model",
            "T1": "generated-model",
            "C1": "generated-model",
            "Q1": "independent-review",
            "P1": "conception-package",
            "H1": "h1-stage",
        }
        for stage in coordinator.STAGE_ORDER:
            package = write_formal_package(
                self.root / stage.lower(),
                profile=profiles[stage],
                stage=stage,
            )
            if stage == "P1":
                decoy = package / "ordinary-object.json"
                decoy.write_text(
                    canonical.canonical_json(
                        {
                            "object_id": "INT-DECOY",
                            "description": (
                                "looks like a source ID but is not registered "
                                "in an authoritative source field"
                            ),
                        }
                    ),
                    encoding="utf-8",
                    newline="",
                )
                handoff = package / "development-handoff.json"
                handoff.write_text(
                    canonical.canonical_json(
                        {
                            "schema_version": "2.0",
                            "run_id": "RUN-014",
                            "status": "ready",
                            "author_control_baseline": artifact(
                                "author-control-baseline.json", "1" * 64
                            ),
                            "conception_package": artifact(
                                "novel-conception-package.json", "2" * 64
                            ),
                            "mandatory_controls": ["INT-001"],
                            "development_freedoms": ["DEV-SCENE-001"],
                            "must_ask": [],
                            "open_items": [],
                            "development_entrypoint": {
                                "next_stage": "novel-development",
                                "instruction": "仅在已批准构思边界内进入开发",
                            },
                        }
                    ),
                    encoding="utf-8",
                    newline="",
                )
                rewrite_manifest(
                    package,
                    role_updates={
                        "development_handoff": artifact(
                            "development-handoff.json",
                            canonical.sha256_file(handoff),
                        )
                    },
                )
                self.handoff = handoff
            if stage == "H1":
                copied_html_manifest = (
                    package / "sources" / "html-package-manifest.json"
                )
                copied_html_manifest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(
                    self.html_package / "package-manifest.json",
                    copied_html_manifest,
                )
                execution = package / "execution-record.json"
                execution.write_text(
                    canonical.canonical_json(
                        {
                            "workspace_artifacts": {
                                "html_manifest": artifact(
                                    "H1/html/package-manifest.json",
                                    canonical.sha256_file(
                                        self.html_package
                                        / "package-manifest.json"
                                    ),
                                )
                            }
                        }
                    ),
                    encoding="utf-8",
                    newline="",
                )
                rewrite_manifest(package)

            gate = self.subject.build_input_gate(
                stage, f"{stage}/input-gate.json"
            )
            manifest_path = package / "package-manifest.json"
            validation_path = package / "validation.json"
            logical_root = "H1/stage" if stage == "H1" else stage
            body = {
                "schema_version": "2.0",
                "run_id": "RUN-014",
                "stage": stage,
                "status": "ready",
                "manifest": artifact(
                    f"{logical_root}/package-manifest.json",
                    canonical.sha256_file(manifest_path),
                ),
                "validation": artifact(
                    f"{logical_root}/validation.json",
                    canonical.sha256_file(validation_path),
                ),
                "input_gate": copy.deepcopy(gate.reference),
                "state_before": copy.deepcopy(gate.data["run_state"]),
                "previous_stage_completions": copy.deepcopy(
                    gate.data["upstream_completions"]
                ),
                "return_binding": copy.deepcopy(gate.data["return_binding"]),
            }
            if stage in {"S1", "W1", "E1", "T1", "C1", "Q1", "H1"}:
                body["session_id"] = (
                    "H1-SESSION-014" if stage == "H1" else f"SESSION-{stage}"
                )
            sealed = coordinator.seal_stage_document(
                body, stage, f"{logical_root}/stage-completion.json"
            )
            (package / "stage-completion.json").write_text(
                canonical.canonical_json(sealed.data),
                encoding="utf-8",
                newline="",
            )
            self.subject.accept_stage_completion(
                gate=gate,
                completion=sealed,
                next_state_path=(
                    f"state/revision-{self.subject.state['revision'] + 1:03d}.json"
                ),
                h1_workspace=(
                    artifact(
                        "H1/workspace-rendered.json",
                        canonical.canonical_sha256(
                            {"stage": "H1", "state": "rendered"}
                        ),
                    )
                    if stage == "H1"
                    else None
                ),
            )
            self.stage_packages[stage] = package

        machine = {
            "completion_path": "P1/stage-completion.json",
            "completion_sha256": canonical.sha256_file(
                self.stage_packages["P1"] / "stage-completion.json"
            ),
            "manifest_path": "P1/package-manifest.json",
            "manifest_sha256": canonical.sha256_file(
                self.stage_packages["P1"] / "package-manifest.json"
            ),
        }
        human = {
            "completion_path": "H1/stage/stage-completion.json",
            "completion_sha256": canonical.sha256_file(
                self.stage_packages["H1"] / "stage-completion.json"
            ),
            "manifest_path": "H1/stage/package-manifest.json",
            "manifest_sha256": canonical.sha256_file(
                self.stage_packages["H1"] / "package-manifest.json"
            ),
            "html_path": "H1/html/human-review-report.html",
            "html_sha256": canonical.sha256_file(html_document),
        }
        event_data = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "approval_scope": "conception",
            "decision": "approved",
            "machine_package": machine,
            "human_review_package": human,
            "approval_record": {
                "event_seq": 201,
                "text": "作者批准正式机器包与人审包",
            },
            "unresolved_items": [],
        }
        self.decision = coordinator.seal_document(
            event_data, "author/approved-decision.json"
        )
        self.waiting_state = coordinator.SealedDocument(
            data=self.subject.state,
            reference=self.subject.state_reference,
        )
        author_runtime.record_author_decision(
            event=self.decision,
            coordinator=self.subject,
            next_state_path="state/revision-010.json",
            p1_package=self.stage_packages["P1"],
            h1_package=self.stage_packages["H1"],
            html_package=self.html_package,
            runtime=self.runtime,
        )
        self.run_state = coordinator.SealedDocument(
            data=self.subject.state,
            reference=self.subject.state_reference,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def _publish(
        self,
        name: str = "completion",
        *,
        next_state_path: str = "state/revision-011.json",
        **overrides,
    ):
        arguments = {
            "run_state": self.run_state,
            "stage_packages": self.stage_packages,
            "p1_package": self.stage_packages["P1"],
            "h1_package": self.stage_packages["H1"],
            "html_package": self.html_package,
            "author_decision": self.decision,
            "development_handoff": self.handoff,
            "coordinator": self.subject,
            "next_state_path": next_state_path,
            "runtime": self.runtime,
        }
        arguments.update(overrides)
        return final_runtime.publish_final_completion(
            self.root / name, **arguments
        )

    def _waiting_subject(self):
        return coordinator.AutonomousCoordinator.from_snapshot(
            self.waiting_state.data,
            self.waiting_state.reference,
            runtime=self.runtime,
        )

    def test_author_decision_binds_attempt_qualified_h1_and_html_paths(self):
        html_root = self.root / "html-attempt-04"
        h1_root = self.root / "h1-stage-attempt-02"
        shutil.copytree(self.html_package, html_root)
        shutil.copytree(self.stage_packages["H1"], h1_root)

        execution_path = h1_root / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["workspace_artifacts"]["html_manifest"] = artifact(
            "H1/html-attempt-04/package-manifest.json",
            canonical.sha256_file(html_root / "package-manifest.json"),
        )
        execution_path.write_text(
            canonical.canonical_json(execution), encoding="utf-8", newline=""
        )
        rewrite_manifest(h1_root)

        completion_path = h1_root / "stage-completion.json"
        completion_data = json.loads(completion_path.read_text(encoding="utf-8"))
        completion_data["manifest"] = artifact(
            "H1/stage-attempt-02/package-manifest.json",
            canonical.sha256_file(h1_root / "package-manifest.json"),
        )
        completion_data["validation"] = artifact(
            "H1/stage-attempt-02/validation.json",
            canonical.sha256_file(h1_root / "validation.json"),
        )
        h1_completion = coordinator.seal_stage_document(
            completion_data,
            "H1",
            "H1/stage-attempt-02/stage-completion.json",
        )
        completion_path.write_text(
            canonical.canonical_json(h1_completion.data),
            encoding="utf-8",
            newline="",
        )

        state = copy.deepcopy(self.waiting_state.data)
        state["current_stage_completions"]["H1"] = h1_completion.reference
        state_ref = artifact(
            "state/revision-attempt-qualified.json",
            canonical.canonical_sha256(state),
        )
        subject = coordinator.AutonomousCoordinator.from_snapshot(
            state, state_ref, runtime=self.runtime
        )
        event_data = copy.deepcopy(self.decision.data)
        event_data["human_review_package"].update(
            {
                "completion_path": h1_completion.reference["path"],
                "completion_sha256": h1_completion.reference["sha256"],
                "manifest_path": "H1/stage-attempt-02/package-manifest.json",
                "manifest_sha256": canonical.sha256_file(
                    h1_root / "package-manifest.json"
                ),
                "html_path": "H1/html-attempt-04/human-review-report.html",
                "html_sha256": canonical.sha256_file(
                    html_root / "human-review-report.html"
                ),
            }
        )
        event = coordinator.seal_document(
            event_data, "author/attempt-qualified-approved.json"
        )

        branch = author_runtime.validate_author_decision_event(
            event,
            coordinator=subject,
            p1_package=self.stage_packages["P1"],
            h1_package=h1_root,
            html_package=html_root,
            runtime=self.runtime,
        )
        self.assertEqual("approved", branch)

        stale_data = copy.deepcopy(event.data)
        stale_data["human_review_package"]["html_path"] = (
            "H1/html/human-review-report.html"
        )
        stale = coordinator.seal_document(
            stale_data, "author/attempt-qualified-stale-html.json"
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.validate_author_decision_event(
                stale,
                coordinator=subject,
                p1_package=self.stage_packages["P1"],
                h1_package=h1_root,
                html_package=html_root,
                runtime=self.runtime,
            )
        self.assertEqual("AUTHOR_DECISION_HTML_MISMATCH", caught.exception.code)

        author_runtime.record_author_decision(
            event=event,
            coordinator=subject,
            next_state_path="state/revision-attempt-qualified-approved.json",
            p1_package=self.stage_packages["P1"],
            h1_package=h1_root,
            html_package=html_root,
            runtime=self.runtime,
        )
        approved = coordinator.SealedDocument(
            data=subject.state,
            reference=subject.state_reference,
        )
        stage_packages = {**self.stage_packages, "H1": h1_root}
        final = final_runtime.publish_final_completion(
            self.root / "attempt-qualified-final",
            run_state=approved,
            stage_packages=stage_packages,
            p1_package=stage_packages["P1"],
            h1_package=h1_root,
            html_package=html_root,
            author_decision=event,
            development_handoff=self.handoff,
            coordinator=subject,
            next_state_path="state/revision-attempt-qualified-final.json",
            runtime=self.runtime,
        )
        self.assertEqual(
            {
                "path": "H1/html-attempt-04/package-manifest.json",
                "sha256": canonical.sha256_file(
                    html_root / "package-manifest.json"
                ),
            },
            final.completion.data["h1_html_manifest"],
        )

    def _revise_event(
        self,
        *,
        scope: str,
        source_ids: list[str],
        visible_ids: list[str],
        event_seq: int,
    ):
        data = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "approval_scope": "conception",
            "decision": "revise",
            "machine_package": copy.deepcopy(
                self.decision.data["machine_package"]
            ),
            "human_review_package": copy.deepcopy(
                self.decision.data["human_review_package"]
            ),
            "revision_record": {
                "event_seq": event_seq,
                "text": "作者明确提交定向修订",
            },
            "revision_targets": [
                {
                    "target_scope": scope,
                    "visible_element_ids": visible_ids,
                    "source_ids": source_ids,
                    "requested_change": "定向修订当前可见控制信息",
                }
            ],
        }
        return coordinator.seal_document(
            data, f"author/revise-{event_seq}.json"
        )

    def test_only_approved_current_nine_stage_run_publishes_completion(self):
        receipt = self._publish()

        self.assertFalse(receipt.replayed)
        self.runtime.validate(
            receipt.completion.data, "conception-completion.schema.json"
        )
        self.assertEqual(
            list(coordinator.STAGE_ORDER),
            list(receipt.completion.data["stage_completions"]),
        )
        self.assertEqual(
            self.run_state.reference, receipt.completion.data["run_state"]
        )
        self.assertEqual(
            self.decision.reference,
            receipt.completion.data["author_decision"],
        )
        self.assertEqual("ready", receipt.transition.snapshot["development_status"])
        self.assertTrue(
            (self.root / "completion" / "conception-completion.json").is_file()
        )

    def test_missing_or_stale_stage_package_is_rejected(self):
        missing = dict(self.stage_packages)
        missing.pop("W1")
        with self.assertRaises(final_runtime.FinalCompletionError) as absent:
            self._publish("missing-stage", stage_packages=missing)
        self.assertEqual("FINAL_STAGE_SET_INVALID", absent.exception.code)

        stale = dict(self.stage_packages)
        stale["W1"] = self.stage_packages["E1"]
        with self.assertRaises(final_runtime.FinalCompletionError):
            self._publish("stale-stage", stage_packages=stale)
        self.assertFalse((self.root / "stale-stage").exists())

    def test_rejected_or_revise_state_cannot_publish(self):
        for status in ("rejected", "revise"):
            bad_data = copy.deepcopy(self.run_state.data)
            bad_data["status"] = status
            if status == "revise":
                bad_data["active_return"] = artifact(
                    "returns/active.json", "a" * 64
                )
            bad = coordinator.SealedDocument(
                data=bad_data,
                reference=artifact(
                    f"state/{status}.json",
                    canonical.canonical_sha256(bad_data),
                ),
            )
            with self.assertRaises(final_runtime.FinalCompletionError):
                self._publish(f"{status}-state", run_state=bad)
            self.assertFalse((self.root / f"{status}-state").exists())

    def test_decision_html_and_handoff_drift_each_fail_closed(self):
        wrong_decision = author_decision("approved", event_seq=202)
        with self.assertRaises(final_runtime.FinalCompletionError):
            self._publish(
                "wrong-decision", author_decision=wrong_decision
            )

        html = self.html_package / "human-review-report.html"
        html.write_bytes(html.read_bytes() + b" ")
        with self.assertRaises(final_runtime.FinalCompletionError):
            self._publish("html-drift")
        html.write_text(
            (
                "<!doctype html><title>formal author review</title>"
                '<section data-element-id="NODE-001">review node</section>'
                "<p>NODE-TEXT-ONLY</p>"
            ),
            encoding="utf-8",
        )

        other_handoff = self.root / "other-handoff.json"
        other_handoff.write_bytes(self.handoff.read_bytes())
        with self.assertRaises(final_runtime.FinalCompletionError):
            self._publish(
                "handoff-drift", development_handoff=other_handoff
            )

    def test_exact_replay_is_idempotent_and_conflict_is_rejected(self):
        first = self._publish()
        replay = self._publish()
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertTrue(replay.transition.replayed)
        self.assertEqual(first.completion, replay.completion)

        with self.assertRaises(coordinator.CoordinatorError):
            self._publish(next_state_path="state/different-successor.json")

    def test_atomic_replace_failure_does_not_admit_development(self):
        before = self.subject.state
        with mock.patch.object(
            Path, "replace", side_effect=OSError("FINAL_REPLACE_FAILED")
        ), self.assertRaisesRegex(OSError, "FINAL_REPLACE_FAILED"):
            self._publish("replace-failed")
        self.assertFalse((self.root / "replace-failed").exists())
        self.assertEqual(before, self.subject.state)

    def test_coordinator_rejection_leaves_valid_unreferenced_completion(self):
        output = self.root / "coordinator-rejected-final"
        with self.assertRaises(coordinator.CoordinatorError) as caught:
            self._publish(
                "coordinator-rejected-final",
                next_state_path="../outside-final-state.json",
            )
        self.assertEqual("COORD_REFERENCE_INVALID", caught.exception.code)
        self.assertTrue((output / "conception-completion.json").is_file())
        self.assertEqual(
            "not_ready", self.subject.state["development_status"]
        )
        validation = final_runtime.validate_final_completion_package(
            output,
            run_state=self.run_state,
            stage_packages=self.stage_packages,
            p1_package=self.stage_packages["P1"],
            h1_package=self.stage_packages["H1"],
            html_package=self.html_package,
            author_decision=self.decision,
            development_handoff=self.handoff,
            coordinator=self.subject,
            runtime=self.runtime,
        )
        self.assertEqual("ready", validation["verdict"])

    def test_input_toctou_is_rejected_without_publish_or_admission(self):
        real_write = final_runtime._write
        mutated = False

        def write_then_mutate(path, value):
            nonlocal mutated
            real_write(path, value)
            if not mutated and Path(path).name == "validation.json":
                mutated = True
                source = self.stage_packages["B0"] / "validation.json"
                source.write_bytes(source.read_bytes() + b" ")

        before = self.subject.state
        with mock.patch.object(
            final_runtime, "_write", side_effect=write_then_mutate
        ), self.assertRaises(final_runtime.FinalCompletionError):
            self._publish("input-toctou")
        self.assertFalse((self.root / "input-toctou").exists())
        self.assertEqual(before, self.subject.state)

    def test_active_return_argument_blocks_before_any_output(self):
        forged = coordinator.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-014",
                "return_id": "RET-ACTIVE",
            },
            "returns/RET-ACTIVE.json",
        )
        with self.assertRaises(final_runtime.FinalCompletionError) as caught:
            self._publish("active-return", active_return_request=forged)
        self.assertEqual("FINAL_ACTIVE_RETURN", caught.exception.code)
        self.assertFalse((self.root / "active-return").exists())

    def test_revision_makes_old_final_completion_stale(self):
        receipt = self._publish()
        decision_reference = copy.deepcopy(
            self.subject.state["author_decision"]
        )
        request_data = routing.route_return(
            run_id="RUN-014",
            return_id="RET-AFTER-FINAL-I0",
            origin_kind="author",
            origin_stage=None,
            issue_kind="author_locked",
            problem="作者在最终批准后修订意图",
            evidence_ids=["INT-001"],
            violated_contract="§14 author revision",
            required_revision="重跑全部自主阶段",
            author_decision=decision_reference,
            has_current_author_decision=True,
            has_current_conception_completion=True,
            runtime=self.runtime,
        )
        request = coordinator.seal_document(
            request_data, "returns/RET-AFTER-FINAL-I0.json"
        )
        self.subject.apply_return_request(
            request=request,
            next_state_path="state/revision-012.json",
            conception_completion_current=True,
        )

        self.assertEqual("revise", self.subject.state["status"])
        self.assertEqual(
            "stale_input", self.subject.state["development_status"]
        )
        self.assertEqual({}, self.subject.state["current_stage_completions"])
        self.assertIsNone(self.subject.state["author_decision"])
        with self.assertRaises(final_runtime.FinalCompletionError) as caught:
            final_runtime.validate_final_completion_package(
                receipt.package_root,
                run_state=self.run_state,
                stage_packages=self.stage_packages,
                p1_package=self.stage_packages["P1"],
                h1_package=self.stage_packages["H1"],
                html_package=self.html_package,
                author_decision=self.decision,
                development_handoff=self.handoff,
                coordinator=self.subject,
                runtime=self.runtime,
            )
        self.assertEqual("FINAL_STATE_NOT_CURRENT", caught.exception.code)

    def test_revision_source_id_must_exist_in_current_p1_package(self):
        valid_subject = self._waiting_subject()
        valid = self._revise_event(
            scope="conception",
            source_ids=["INT-001"],
            visible_ids=[],
            event_seq=301,
        )
        receipt = author_runtime.record_author_decision(
            event=valid,
            coordinator=valid_subject,
            next_state_path="state/revision-010-source.json",
            p1_package=self.stage_packages["P1"],
            h1_package=self.stage_packages["H1"],
            html_package=self.html_package,
            runtime=self.runtime,
        )
        self.assertEqual("I0", receipt.return_request.data["calculated_owner"])

        invalid_subject = self._waiting_subject()
        invalid = self._revise_event(
            scope="conception",
            source_ids=["INT-NOT-IN-CURRENT-P1"],
            visible_ids=[],
            event_seq=302,
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.record_author_decision(
                event=invalid,
                coordinator=invalid_subject,
                next_state_path="state/revision-010-missing-source.json",
                p1_package=self.stage_packages["P1"],
                h1_package=self.stage_packages["H1"],
                html_package=self.html_package,
                runtime=self.runtime,
            )
        self.assertEqual(
            "AUTHOR_DECISION_SOURCE_ID_INVALID", caught.exception.code
        )
        self.assertEqual(
            "waiting_author", invalid_subject.state["status"]
        )

        decoy_subject = self._waiting_subject()
        decoy = self._revise_event(
            scope="conception",
            source_ids=["INT-DECOY"],
            visible_ids=[],
            event_seq=305,
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.record_author_decision(
                event=decoy,
                coordinator=decoy_subject,
                next_state_path="state/revision-010-decoy-source.json",
                p1_package=self.stage_packages["P1"],
                h1_package=self.stage_packages["H1"],
                html_package=self.html_package,
                runtime=self.runtime,
            )
        self.assertEqual(
            "AUTHOR_DECISION_SOURCE_ID_INVALID", caught.exception.code
        )
        self.assertEqual("waiting_author", decoy_subject.state["status"])

    def test_revision_terminal_dev_routes_to_character_owner(self):
        subject = self._waiting_subject()
        event = self._revise_event(
            scope="conception",
            source_ids=["DEV-SCENE-001"],
            visible_ids=[],
            event_seq=306,
        )
        receipt = author_runtime.record_author_decision(
            event=event,
            coordinator=subject,
            next_state_path="state/revision-010-dev-source.json",
            p1_package=self.stage_packages["P1"],
            h1_package=self.stage_packages["H1"],
            html_package=self.html_package,
            runtime=self.runtime,
        )
        self.assertEqual("C1", receipt.return_request.data["calculated_owner"])

    def test_revision_visible_id_must_exist_in_current_html(self):
        valid_subject = self._waiting_subject()
        valid = self._revise_event(
            scope="report",
            source_ids=[],
            visible_ids=["NODE-001"],
            event_seq=303,
        )
        receipt = author_runtime.record_author_decision(
            event=valid,
            coordinator=valid_subject,
            next_state_path="state/revision-010-visible.json",
            p1_package=self.stage_packages["P1"],
            h1_package=self.stage_packages["H1"],
            html_package=self.html_package,
            runtime=self.runtime,
        )
        self.assertEqual(
            "H1-A", receipt.return_request.data["calculated_owner"]
        )

        invalid_subject = self._waiting_subject()
        invalid = self._revise_event(
            scope="report",
            source_ids=[],
            visible_ids=["NODE-NOT-IN-CURRENT-HTML"],
            event_seq=304,
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.record_author_decision(
                event=invalid,
                coordinator=invalid_subject,
                next_state_path="state/revision-010-missing-visible.json",
                p1_package=self.stage_packages["P1"],
                h1_package=self.stage_packages["H1"],
                html_package=self.html_package,
                runtime=self.runtime,
            )
        self.assertEqual(
            "AUTHOR_DECISION_VISIBLE_ID_INVALID", caught.exception.code
        )
        self.assertEqual(
            "waiting_author", invalid_subject.state["status"]
        )

        text_only_subject = self._waiting_subject()
        text_only = self._revise_event(
            scope="report",
            source_ids=[],
            visible_ids=["NODE-TEXT-ONLY"],
            event_seq=306,
        )
        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            author_runtime.record_author_decision(
                event=text_only,
                coordinator=text_only_subject,
                next_state_path="state/revision-010-text-only-visible.json",
                p1_package=self.stage_packages["P1"],
                h1_package=self.stage_packages["H1"],
                html_package=self.html_package,
                runtime=self.runtime,
            )
        self.assertEqual(
            "AUTHOR_DECISION_VISIBLE_ID_INVALID", caught.exception.code
        )
        self.assertEqual(
            "waiting_author", text_only_subject.state["status"]
        )


class H1WorkspaceTransitionContractTests(unittest.TestCase):
    """Exercise the production ContractRuntime and coordinator boundary."""

    def setUp(self):
        self.runtime = contracts.ContractRuntime()
        self.subject = coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-014",
            source_interview_state=artifact(
                "interview/run-state.json", "2" * 64
            ),
            state_path="state/revision-000.json",
            runtime=self.runtime,
        )
        self.completed = advance_through_p1(self.subject)
        self.p1_completion = copy.deepcopy(
            self.completed["P1"].reference
        )
        assembled_data = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "stage": "H1",
            "session_id": "H1-SESSION-014",
            "state": "assembled",
            "p1_completion": copy.deepcopy(self.p1_completion),
            "previous_state_sha256": "4" * 64,
            "artifacts": {
                "plan_manifest": artifact(
                    "H1/plan/package-manifest.json", "5" * 64
                ),
                "fragment_manifest": artifact(
                    "H1/fragments/package-manifest.json", "6" * 64
                ),
                "assembly_manifest": artifact(
                    "H1/assembly/package-manifest.json", "7" * 64
                ),
            },
        }
        self.assembled = coordinator.seal_document(
            assembled_data, "H1/workspace-assembled.json"
        )
        manifest_data = {
            "schema_version": "2.0",
            "run_id": "RUN-014",
            "stage": "H1",
            "package_profile": "h1-html",
            "verdict": "ready",
            "session_id": "H1-SESSION-014",
            "parent_state_sha256": self.assembled.reference["sha256"],
            "files": [
                artifact("human-review-report.html", "8" * 64),
                artifact("render-record.json", "9" * 64),
                artifact("validation.json", "a" * 64),
                artifact("implementation/run_v2.py", "b" * 64),
            ],
            "artifact_roles": {
                "html": artifact("human-review-report.html", "8" * 64),
                "render_record": artifact("render-record.json", "9" * 64),
            },
            "validation": artifact("validation.json", "a" * 64),
            "implementation": [
                artifact("implementation/run_v2.py", "b" * 64)
            ],
        }
        self.html_manifest = coordinator.SealedDocument(
            data=manifest_data,
            reference=artifact(
                "H1/html/package-manifest.json",
                canonical.canonical_sha256(manifest_data),
            ),
        )

    @staticmethod
    def _workspace_from_transition(transition):
        for name in ("workspace", "document", "sealed_workspace"):
            value = getattr(transition, name, None)
            if value is not None:
                return value
        if isinstance(transition, coordinator.SealedDocument):
            return transition
        raise AssertionError(
            "H1WorkspaceTransition must expose its sealed workspace"
        )

    def test_real_coordinator_accepts_exact_assembled_to_rendered_transition(self):
        transition = self.subject.accept_h1_workspace_transition(
            current_workspace=self.assembled,
            package_manifest=self.html_manifest,
            expected_next_state="rendered",
            active_return_request=None,
        )
        rendered = self._workspace_from_transition(transition)

        self.runtime.validate(
            rendered.data, "h1-workspace-state.schema.json"
        )
        self.assertEqual("rendered", rendered.data["state"])
        self.assertEqual(
            self.assembled.reference["sha256"],
            rendered.data["previous_state_sha256"],
        )
        self.assertEqual(
            self.html_manifest.reference,
            rendered.data["artifacts"]["html_manifest"],
        )
        self.assertEqual(
            self.p1_completion, rendered.data["p1_completion"]
        )
        self.assertEqual("RUN-014", rendered.data["run_id"])
        self.assertEqual("H1-SESSION-014", rendered.data["session_id"])

    def test_workspace_transition_rejects_wrong_parent_without_mutation(self):
        original_state = self.subject.state
        bad_data = copy.deepcopy(self.html_manifest.data)
        bad_data["parent_state_sha256"] = "f" * 64
        bad_manifest = coordinator.SealedDocument(
            data=bad_data,
            reference=artifact(
                "H1/html/package-manifest.json",
                canonical.canonical_sha256(bad_data),
            ),
        )

        with self.assertRaises(coordinator.CoordinatorError):
            self.subject.accept_h1_workspace_transition(
                current_workspace=self.assembled,
                package_manifest=bad_manifest,
                expected_next_state="rendered",
                active_return_request=None,
            )
        self.assertEqual(original_state, self.subject.state)

    def test_workspace_transition_exact_replay_is_idempotent(self):
        first = self.subject.accept_h1_workspace_transition(
            current_workspace=self.assembled,
            package_manifest=self.html_manifest,
            expected_next_state="rendered",
        )
        second = self.subject.accept_h1_workspace_transition(
            current_workspace=self.assembled,
            package_manifest=self.html_manifest,
            expected_next_state="rendered",
        )

        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.workspace, second.workspace)

    def test_workspace_transition_conflicting_replay_is_rejected(self):
        self.subject.accept_h1_workspace_transition(
            current_workspace=self.assembled,
            package_manifest=self.html_manifest,
            expected_next_state="rendered",
        )
        other_data = copy.deepcopy(self.html_manifest.data)
        other_data["files"][0]["sha256"] = "c" * 64
        other_data["artifact_roles"]["html"]["sha256"] = "c" * 64
        conflicting = coordinator.SealedDocument(
            data=other_data,
            reference=artifact(
                "H1/html/package-manifest.json",
                canonical.canonical_sha256(other_data),
            ),
        )

        with self.assertRaises(coordinator.CoordinatorError) as caught:
            self.subject.accept_h1_workspace_transition(
                current_workspace=self.assembled,
                package_manifest=conflicting,
                expected_next_state="rendered",
            )
        self.assertEqual("COORD_TRANSITION_CONFLICT", caught.exception.code)

    def test_workspace_transition_rejects_cross_session_manifest(self):
        wrong_data = copy.deepcopy(self.html_manifest.data)
        wrong_data["session_id"] = "H1-OTHER-SESSION"
        wrong = coordinator.SealedDocument(
            data=wrong_data,
            reference=artifact(
                "H1/html/package-manifest.json",
                canonical.canonical_sha256(wrong_data),
            ),
        )

        with self.assertRaises(coordinator.CoordinatorError) as caught:
            self.subject.accept_h1_workspace_transition(
                current_workspace=self.assembled,
                package_manifest=wrong,
                expected_next_state="rendered",
            )
        self.assertEqual(
            "COORD_H1_MANIFEST_LINEAGE_MISMATCH", caught.exception.code
        )


if __name__ == "__main__":
    unittest.main()
