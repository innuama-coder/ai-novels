from __future__ import annotations

import copy
import importlib
import unittest


coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)
routing = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.return_routing"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
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
    completion = {
        "schema_version": "2.0",
        "run_id": data["run_id"],
        "stage": stage,
        "status": "ready",
        "manifest": artifact(f"{stage}/package-manifest.json"),
        "validation": artifact(f"{stage}/validation.json"),
        "input_gate": gate.reference,
        "state_before": data["run_state"],
        "previous_stage_completions": copy.deepcopy(data["upstream_completions"]),
        "return_binding": copy.deepcopy(data["return_binding"]),
    }
    if stage in {"S1", "W1", "E1", "T1", "C1", "Q1", "H1"}:
        completion["session_id"] = f"SESSION-{stage}"
    return coordinator.seal_stage_document(
        completion, stage, f"{stage}/stage-completion.json"
    )


class CoordinatorFixture(unittest.TestCase):
    def new_coordinator(self) -> coordinator.AutonomousCoordinator:
        return coordinator.AutonomousCoordinator.initialize(
            run_id="RUN-001",
            source_interview_state=artifact("interview/run-state.json"),
            state_path="state/revision-000.json",
        )

    def advance(
        self,
        subject: coordinator.AutonomousCoordinator,
        stage: str,
    ) -> coordinator.SealedDocument:
        gate = subject.build_input_gate(stage, f"{stage}/input-gate.json")
        completion = completion_for(gate)
        h1_workspace = (
            artifact("H1/h1-workspace-state.json") if stage == "H1" else None
        )
        subject.accept_stage_completion(
            gate=gate,
            completion=completion,
            next_state_path=f"state/revision-{subject.state['revision'] + 1:03d}.json",
            h1_workspace=h1_workspace,
        )
        return completion

    def advance_through(
        self,
        subject: coordinator.AutonomousCoordinator,
        final_stage: str,
    ) -> dict[str, coordinator.SealedDocument]:
        completed: dict[str, coordinator.SealedDocument] = {}
        for stage in coordinator.STAGE_ORDER:
            completed[stage] = self.advance(subject, stage)
            if stage == final_stage:
                break
        return completed


class ForwardTopologyTests(CoordinatorFixture):
    def test_all_nine_stages_advance_in_exact_order(self) -> None:
        subject = self.new_coordinator()
        original = copy.deepcopy(subject.state)

        completed = self.advance_through(subject, "H1")

        self.assertEqual(list(coordinator.STAGE_ORDER), list(completed))
        self.assertEqual(list(coordinator.STAGE_ORDER), list(subject.state["current_stage_completions"]))
        self.assertEqual(9, subject.state["revision"])
        self.assertEqual("waiting_author", subject.state["status"])
        self.assertEqual(
            artifact("H1/h1-workspace-state.json"),
            subject.state["h1_workspace"],
        )
        self.assertEqual({}, original["current_stage_completions"])
        self.assertEqual(0, original["revision"])

    def test_illegal_skip_and_wrong_upstream_order_are_rejected(self) -> None:
        subject = self.new_coordinator()
        with self.assertRaises(coordinator.CoordinatorError) as skipped:
            subject.build_input_gate("W1", "W1/input-gate.json")
        self.assertEqual("COORD_ILLEGAL_STAGE_TRANSITION", skipped.exception.code)

        self.advance_through(subject, "W1")
        gate = subject.build_input_gate("E1", "E1/input-gate.json")
        bad = copy.deepcopy(gate.data)
        bad["upstream_completions"].reverse()
        bad_gate = coordinator.SealedDocument(
            data=bad,
            reference=artifact(
                "E1/input-gate.json", canonical.canonical_sha256(bad)
            ),
        )
        with self.assertRaises(coordinator.CoordinatorError) as wrong_order:
            subject.accept_stage_completion(
                gate=bad_gate,
                completion=completion_for(bad_gate),
                next_state_path="state/revision-004.json",
            )
        self.assertEqual("COORD_INPUT_GATE_SCHEMA_INVALID", wrong_order.exception.code)

    def test_non_ready_checkpoint_is_not_a_completion(self) -> None:
        subject = self.new_coordinator()
        gate = subject.build_input_gate("B0", "B0/input-gate.json")
        data = completion_for(gate).data
        data["status"] = "revise"
        bad = coordinator.SealedDocument(
            data=data,
            reference=stage_artifact(
                "B0",
                "B0/stage-completion.json",
                canonical.canonical_sha256(data),
            ),
        )

        with self.assertRaises(coordinator.CoordinatorError) as caught:
            subject.accept_stage_completion(
                gate=gate,
                completion=bad,
                next_state_path="state/revision-001.json",
            )
        self.assertEqual("COORD_COMPLETION_NOT_READY", caught.exception.code)
        self.assertEqual(0, subject.state["revision"])

    def test_stale_state_reference_and_conflicting_replay_are_rejected(self) -> None:
        subject = self.new_coordinator()
        gate = subject.build_input_gate("B0", "B0/input-gate.json")
        accepted = completion_for(gate)
        first = subject.accept_stage_completion(
            gate=gate,
            completion=accepted,
            next_state_path="state/revision-001.json",
        )

        replay = subject.accept_stage_completion(
            gate=gate,
            completion=accepted,
            next_state_path="state/revision-001.json",
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(first.snapshot, replay.snapshot)
        self.assertEqual(first.reference, replay.reference)

        conflicting_data = copy.deepcopy(accepted.data)
        conflicting_data["manifest"] = artifact("B0/other-manifest.json")
        conflicting = coordinator.seal_stage_document(
            conflicting_data, "B0", "B0/other-completion.json"
        )
        with self.assertRaises(coordinator.CoordinatorError) as conflict:
            subject.accept_stage_completion(
                gate=gate,
                completion=conflicting,
                next_state_path="state/revision-001.json",
            )
        self.assertEqual("COORD_TRANSITION_CONFLICT", conflict.exception.code)

        stale_state = copy.deepcopy(subject.state)
        stale_reference = copy.deepcopy(subject.state_reference)
        stale_reference["sha256"] = ZERO_HASH
        with self.assertRaises(coordinator.CoordinatorError) as stale:
            coordinator.AutonomousCoordinator.from_snapshot(
                stale_state, stale_reference
            )
        self.assertEqual("COORD_STALE_REFERENCE", stale.exception.code)


class ReturnRoutingTests(CoordinatorFixture):
    def test_router_calculates_owner_suffix_and_h1_resume_point(self) -> None:
        request = routing.route_return(
            run_id="RUN-001",
            return_id="RET-001",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_fragment",
            problem="片段与 brief 不一致",
            evidence_ids=["fragment-01"],
            violated_contract="§14.1 H1-B",
            required_revision="重写受影响片段",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )

        self.assertEqual("H1-B", request["calculated_owner"])
        self.assertEqual("H1", request["target_stage"])
        self.assertEqual("H1", request["resume_stage"])
        self.assertEqual("H1-B", request["resume_point"])
        self.assertEqual(["H1"], request["invalidated_stages"])
        self.assertEqual(
            ["fragments", "assembly", "html", "completion"],
            request["invalidated_h1_artifacts"],
        )
        routing.validate_return_request(request)

    def test_router_rejects_unknown_or_ambiguous_owner(self) -> None:
        common = {
            "run_id": "RUN-001",
            "return_id": "RET-002",
            "origin_kind": "stage",
            "origin_stage": "Q1",
            "problem": "无法归属",
            "evidence_ids": ["X-001"],
            "violated_contract": "unknown",
            "required_revision": "unknown",
            "author_decision": None,
            "has_current_author_decision": False,
            "has_current_conception_completion": False,
        }
        with self.assertRaises(routing.ReturnRoutingError) as unknown:
            routing.route_return(issue_kind="unknown", **common)
        self.assertEqual("ROUTE_NO_RESOLVER", unknown.exception.code)

        with self.assertRaises(routing.ReturnRoutingError) as ambiguous:
            routing.route_return(
                issue_kind="author_locked",
                **{**common, "evidence_ids": ["INT-001", "WLD-001"]},
            )
        self.assertEqual("ROUTE_AMBIGUOUS_OWNER", ambiguous.exception.code)


class ReturnResolutionTests(CoordinatorFixture):
    def test_return_invalidates_suffix_and_resolves_once(self) -> None:
        subject = self.new_coordinator()
        old = self.advance_through(subject, "C1")
        pre_return_state = copy.deepcopy(subject.state)

        request_data = routing.route_return(
            run_id="RUN-001",
            return_id="RET-S1-001",
            origin_kind="stage",
            origin_stage="C1",
            issue_kind="storyline",
            problem="主干连接缺失",
            evidence_ids=["SL-001"],
            violated_contract="§14.1 故事线连接",
            required_revision="补足主干连接",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = coordinator.seal_document(
            request_data, "returns/RET-S1-001/return-request.json"
        )
        applied = subject.apply_return_request(
            request=request,
            next_state_path="state/revision-007.json",
        )

        self.assertEqual(["B0"], list(subject.state["current_stage_completions"]))
        self.assertEqual(
            ["S1", "W1", "E1", "T1", "C1"],
            [item["stage"] for item in subject.state["superseded_completions"]],
        )
        self.assertEqual(request.reference, subject.state["active_return"])
        self.assertEqual("revise", subject.state["status"])
        self.assertEqual(7, subject.state["revision"])
        self.assertEqual(6, pre_return_state["revision"])
        self.assertFalse(applied.replayed)

        with self.assertRaises(coordinator.CoordinatorError) as blocked:
            subject.build_input_gate("W1", "W1/return-input-gate.json")
        self.assertEqual("COORD_ACTIVE_RETURN_BLOCKS_STAGE", blocked.exception.code)

        gate = subject.build_input_gate(
            "S1",
            "S1/return-input-gate.json",
            active_return_request=request,
        )
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        new_s1 = completion_for(gate)
        subject.accept_stage_completion(
            gate=gate,
            completion=new_s1,
            next_state_path="state/revision-008.json",
            active_return_request=request,
        )

        self.assertIsNone(subject.state["active_return"])
        self.assertEqual(["B0", "S1"], list(subject.state["current_stage_completions"]))
        self.assertEqual(1, len(subject.state["resolved_returns"]))
        resolved = subject.state["resolved_returns"][0]
        self.assertEqual("RET-S1-001", resolved["return_binding"]["return_id"])
        self.assertEqual(new_s1.reference, resolved["resolving_completion"])
        self.assertEqual(applied.reference, resolved["pre_resolution_state"])
        self.assertNotEqual(old["S1"].reference, new_s1.reference)

        with self.assertRaises(coordinator.CoordinatorError) as repeated:
            subject.accept_stage_completion(
                gate=gate,
                completion=new_s1,
                next_state_path="state/revision-008.json",
                active_return_request=request,
            )
        self.assertEqual("COORD_RETURN_ALREADY_RESOLVED", repeated.exception.code)

    def test_missing_active_return_body_and_binding_tamper_fail_without_mutation(self) -> None:
        subject = self.new_coordinator()
        self.advance_through(subject, "W1")
        request_data = routing.route_return(
            run_id="RUN-001",
            return_id="RET-W1-001",
            origin_kind="stage",
            origin_stage="W1",
            issue_kind="world",
            problem="资源流冲突",
            evidence_ids=["WS-001"],
            violated_contract="§14.1 世界系统",
            required_revision="修正资源流",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = coordinator.seal_document(
            request_data, "returns/RET-W1-001/return-request.json"
        )
        subject.apply_return_request(
            request=request,
            next_state_path="state/revision-003.json",
        )
        active_snapshot = copy.deepcopy(subject.state)
        active_reference = copy.deepcopy(subject.state_reference)

        with self.assertRaises(coordinator.CoordinatorError) as missing:
            coordinator.AutonomousCoordinator.from_snapshot(
                active_snapshot, active_reference
            )
        self.assertEqual("COORD_ACTIVE_RETURN_BODY_REQUIRED", missing.exception.code)

        gate = subject.build_input_gate(
            "W1",
            "W1/return-input-gate.json",
            active_return_request=request,
        )
        completion = completion_for(gate)
        tampered = copy.deepcopy(completion.data)
        tampered["return_binding"]["return_id"] = "RET-OTHER"
        tampered_completion = coordinator.seal_stage_document(
            tampered, "W1", "W1/tampered-completion.json"
        )

        before = copy.deepcopy(subject.state)
        with self.assertRaises(coordinator.CoordinatorError) as mismatch:
            subject.accept_stage_completion(
                gate=gate,
                completion=tampered_completion,
                next_state_path="state/revision-004.json",
                active_return_request=request,
            )
        self.assertEqual("COORD_RETURN_BINDING_MISMATCH", mismatch.exception.code)
        self.assertEqual(before, subject.state)

    def test_return_application_is_idempotent_but_conflicting_body_is_rejected(self) -> None:
        subject = self.new_coordinator()
        self.advance_through(subject, "S1")
        request_data = routing.route_return(
            run_id="RUN-001",
            return_id="RET-S1-002",
            origin_kind="stage",
            origin_stage="S1",
            issue_kind="storyline",
            problem="职责重叠",
            evidence_ids=["SL-002"],
            violated_contract="§14.1 故事线职责",
            required_revision="去除重叠",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = coordinator.seal_document(
            request_data, "returns/RET-S1-002/return-request.json"
        )
        first = subject.apply_return_request(
            request=request,
            next_state_path="state/revision-002.json",
        )
        replay = subject.apply_return_request(
            request=request,
            next_state_path="state/revision-002.json",
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(first.snapshot, replay.snapshot)

        conflict_data = copy.deepcopy(request_data)
        conflict_data["problem"] = "不同问题"
        conflicting = coordinator.seal_document(
            conflict_data, "returns/RET-S1-002/conflict.json"
        )
        with self.assertRaises(coordinator.CoordinatorError) as conflict:
            subject.apply_return_request(
                request=conflicting,
                next_state_path="state/revision-002.json",
            )
        self.assertEqual("COORD_TRANSITION_CONFLICT", conflict.exception.code)

    def test_active_return_refresh_appends_revision_without_replacing_return(self) -> None:
        subject = self.new_coordinator()
        self.advance_through(subject, "S1")
        request_data = routing.route_return(
            run_id="RUN-001",
            return_id="RET-S1-REFRESH",
            origin_kind="stage",
            origin_stage="S1",
            issue_kind="storyline",
            problem="The active owner contract changed again.",
            evidence_ids=["SL-CONTRACT-REFRESH"],
            violated_contract="storyline runtime identity",
            required_revision="Regenerate under the refreshed contract.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = coordinator.seal_document(
            request_data, "returns/RET-S1-REFRESH/return-request.json"
        )
        first = subject.apply_return_request(
            request=request,
            next_state_path="state/revision-003.json",
        )
        before = copy.deepcopy(first.snapshot)
        refreshed = subject.refresh_active_return(
            request=request,
            next_state_path="state/revision-004.json",
        )

        self.assertEqual(first.snapshot["revision"] + 1, refreshed.snapshot["revision"])
        self.assertEqual(first.reference, refreshed.snapshot["previous_state"])
        self.assertEqual(request.reference, refreshed.snapshot["active_return"])
        for field in (
            "current_stage_completions",
            "resolved_returns",
            "superseded_completions",
            "status",
        ):
            self.assertEqual(before[field], refreshed.snapshot[field])

        competing_data = copy.deepcopy(request_data)
        competing_data["return_id"] = "RET-S1-COMPETING"
        competing = coordinator.seal_document(
            competing_data, "returns/RET-S1-COMPETING/return-request.json"
        )
        with self.assertRaises(coordinator.CoordinatorError) as caught:
            subject.refresh_active_return(
                request=competing,
                next_state_path="state/revision-005.json",
            )
        self.assertEqual(
            "COORD_ACTIVE_RETURN_REFERENCE_MISMATCH", caught.exception.code
        )

    def test_active_return_escalation_replaces_owner_and_invalidates_earlier_suffix(self) -> None:
        subject = self.new_coordinator()
        self.advance_through(subject, "C1")
        old_data = routing.route_return(
            run_id="RUN-001", return_id="RET-E1-ACTIVE",
            origin_kind="stage", origin_stage="C1", issue_kind="environment",
            problem="E1 must be regenerated.", evidence_ids=["E1-STALE"],
            violated_contract="E1 implementation", required_revision="Revise E1.",
            author_decision=None, has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        old = coordinator.seal_document(old_data, "returns/RET-E1-ACTIVE.json")
        subject.apply_return_request(
            request=old, next_state_path="state/revision-007.json"
        )
        old_body = copy.deepcopy(old.data)
        before = copy.deepcopy(subject.state)
        for target, issue in (("E1", "environment"), ("T1", "event_timeline")):
            candidate_data = routing.route_return(
                run_id="RUN-001", return_id=f"RET-{target}-NOT-EARLIER",
                origin_kind="stage", origin_stage="E1", issue_kind=issue,
                problem="Not an earlier owner.", evidence_ids=[f"{target}-LATE"],
                violated_contract=f"{target} implementation",
                required_revision=f"Revise {target}.", author_decision=None,
                has_current_author_decision=False,
                has_current_conception_completion=False,
            )
            candidate = coordinator.seal_document(
                candidate_data, f"returns/RET-{target}-NOT-EARLIER.json"
            )
            with self.assertRaises(coordinator.CoordinatorError) as caught:
                subject.supersede_active_return(
                    request=candidate, next_state_path="state/revision-008.json"
                )
            self.assertEqual("COORD_RETURN_ESCALATION_NOT_EARLIER", caught.exception.code)
            self.assertEqual(before, subject.state)

        new_data = routing.route_return(
            run_id="RUN-001", return_id="RET-B0-ESCALATED",
            origin_kind="stage", origin_stage="E1", issue_kind="baseline_packaging",
            problem="B0 is stale.", evidence_ids=["B0-STALE"],
            violated_contract="B0 implementation", required_revision="Revise B0.",
            author_decision=None, has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        new = coordinator.seal_document(new_data, "returns/RET-B0-ESCALATED.json")
        transition = subject.supersede_active_return(
            request=new, next_state_path="state/revision-008.json"
        )
        self.assertEqual(8, transition.snapshot["revision"])
        self.assertEqual(new.reference, transition.snapshot["active_return"])
        self.assertEqual({}, transition.snapshot["current_stage_completions"])
        self.assertEqual([], transition.snapshot["resolved_returns"])
        self.assertEqual(old_body, old.data)
        self.assertEqual(
            ["E1", "T1", "C1", "B0", "S1", "W1"],
            [item["stage"] for item in transition.snapshot["superseded_completions"]],
        )


if __name__ == "__main__":
    unittest.main()
