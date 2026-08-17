from __future__ import annotations

import copy
import hashlib
import importlib
import json
import unittest
from pathlib import Path
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
fixtures = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)
readability = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_readability"
)


class InternalH1ReadabilityReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _persist(self, context, body: dict, path: str):
        document = rt.seal_document(body, path)
        context.store.persist_document(document)
        return document

    def _waiting_author(self):
        context = self.fixture._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self.fixture._fake_executor(stage, revision),
            )
        manifests = {
            key: self._persist(
                context,
                {"profile": key, "verdict": "ready"},
                f"H1/{path}/package-manifest.json",
            )
            for key, path in (
                ("plan", "plan"),
                ("fragment", "fragments-attempt-readability"),
                ("assembly", "assembly"),
                ("html", "html"),
            )
        }
        fragment_root = self.root / "H1" / "fragments-attempt-readability"
        fragment_root.mkdir(parents=True, exist_ok=True)
        fragment_text = "她只看到一行文字，随后把问题写下来。"
        (fragment_root / "fragment-package.json").write_text(
            rt.canonical_json(
                {"fragments": [{"id": "FRAG-01", "text": fragment_text}]}
            ),
            encoding="utf-8",
            newline="",
        )
        assembly_root = self.root / "H1" / "assembly"
        assembly_root.mkdir(parents=True, exist_ok=True)
        (assembly_root / "human-review-report.json").write_text(
            "人物说明像审计规格，而不是可读故事。", encoding="utf-8", newline=""
        )
        workspace = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": "H1-READABILITY-OLD",
                "state": "rendered",
                "p1_completion": context.state.data["current_stage_completions"]["P1"],
                "previous_state_sha256": "3" * 64,
                "artifacts": {
                    "plan_manifest": manifests["plan"].reference,
                    "fragment_manifest": manifests["fragment"].reference,
                    "assembly_manifest": manifests["assembly"].reference,
                    "html_manifest": manifests["html"].reference,
                },
            },
            "H1/H1-READABILITY-OLD/workspace-rendered.json",
        )
        context.store.persist_workspace(workspace)
        _, order = prod.issue_stage_work(context, action="H1-publish", inputs={})
        gate = context.store.load_document(order.data["input_gate"])
        h1_manifest = self._persist(
            context,
            {"profile": "h1-stage", "verdict": "ready"},
            "H1/stage/package-manifest.json",
        )
        completion = rt.seal_stage_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "status": "ready",
                "manifest": h1_manifest.reference,
                "validation": {"path": "H1/stage/validation.json", "sha256": "9" * 64},
                "input_gate": gate.reference,
                "state_before": gate.data["run_state"],
                "previous_stage_completions": gate.data["upstream_completions"],
                "return_binding": None,
                "session_id": workspace.data["session_id"],
            },
            "H1",
            "H1/stage/stage-completion.json",
        )
        transition = context.coordinator.accept_stage_completion(
            gate=gate,
            completion=completion,
            h1_workspace=workspace.reference,
            next_state_path="state/revision-009.json",
        )
        waiting = rt.SealedDocument(transition.snapshot, transition.reference)
        prod._prepare_state_commit(context, order, waiting, completion)
        context.store.persist_state(waiting)
        context.store.mark_work_order_consumed(order, successor=waiting)
        context = prod.resume_production_run(self.root)
        prepublish_inputs = {
            "h1_completion": None,
            "h1_manifest": None,
            "html": {"path": "H1/html/human-review-report.html", "sha256": "1" * 64},
            "report": {
                "path": "H1/assembly/human-review-report.json",
                "sha256": rt.sha256_file(assembly_root / "human-review-report.json"),
            },
            "fragment_manifest": manifests["fragment"].reference,
            "fragment_package": {
                "path": "H1/fragments-attempt-readability/fragment-package.json",
                "sha256": rt.sha256_file(fragment_root / "fragment-package.json"),
            },
            "fragments": [{
                "fragment_id": "FRAG-01",
                "text_sha256": hashlib.sha256(fragment_text.encode()).hexdigest(),
            }],
        }
        return context, workspace, completion, h1_manifest, prepublish_inputs

    def _failure_and_request(self, context, prepublish, completion, manifest):
        inputs = copy.deepcopy(prepublish)
        inputs["h1_completion"] = completion.reference
        inputs["h1_manifest"] = manifest.reference
        dimensions = [
            {"id": name, "verdict": "pass", "finding": "independently checked"}
            for name in readability.DIMENSIONS
        ]
        dimensions[3]["verdict"] = "fail"
        failure = readability.seal_review({
            "schema_version": "1.0",
            "review_id": "H1-READABILITY-RETURN-001",
            "run_id": "RUN-PROD-1",
            "session_id": "H1-READABILITY-OLD",
            "phase": "postpublish_failure",
            "reviewer": {
                "task_id": "independent-reviewer",
                "thread_id": "independent-thread",
                "independence_basis": "separate-task-no-producer-context",
            },
            "inputs": inputs,
            "dimensions": dimensions,
            "findings": [{
                "finding_id": "H1-READABILITY-FINDING-001",
                "dimension": "scene_not_spec",
                "artifact_kind": "report",
                "artifact_id": "human-review-report",
                "evidence": "审计规格",
                "explanation": "The author-facing prose reads as a specification.",
            }],
            "verdict": "fail",
        })
        body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-H1-READABILITY-001",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_plan",
            problem="Independent readability review rejected the author-facing package.",
            evidence_ids=[failure.data["review_id"]],
            violated_contract="Author-facing H1 output must be readable fictive language.",
            required_revision="Rebuild H1 from plan through rendered output.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            body, f"returns/{body['return_id']}/return-request.json"
        )
        return failure, request

    def test_success_preserves_upstream_and_reissues_fresh_h1_a_plan(self):
        context, old_workspace, completion, manifest, prepublish = self._waiting_author()
        failure, request = self._failure_and_request(
            context, prepublish, completion, manifest
        )
        upstream = copy.deepcopy(context.state.data["current_stage_completions"])
        with mock.patch.object(
            prod,
            "h1_readability_prepublish_contract",
            return_value=(
                prepublish,
                [{"task_id": "plan-producer", "thread_id": "plan-thread"}],
            ),
        ):
            receipt, returned, initialized, gate, order = (
                prod.apply_internal_h1_readability_return(
                    context,
                    readability_failure=failure,
                    request=request,
                    actor="production-orchestrator",
                )
            )
        self.assertEqual("complete", receipt.data["status"])
        self.assertEqual("revise", returned.state.data["status"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual(upstream["P1"], returned.state.data["current_stage_completions"]["P1"])
        self.assertNotIn("H1", returned.state.data["current_stage_completions"])
        self.assertEqual("initialized", initialized.data["state"])
        self.assertNotEqual(old_workspace.data["session_id"], initialized.data["session_id"])
        self.assertEqual("H1-A-plan", order.data["action"])
        self.assertEqual(initialized.reference, order.data["h1_workspace"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        replay = prod.resume_production_run(self.root)
        self.assertEqual(returned.state.reference, replay.state.reference)
        self.assertEqual(order.reference, replay.store.pending_work_order().reference)

    def test_wrong_waiting_author_state_is_zero_write(self):
        context, _old, completion, manifest, prepublish = self._waiting_author()
        failure, request = self._failure_and_request(
            context, prepublish, completion, manifest
        )
        changed = copy.deepcopy(context.state.data)
        changed["author_decision"] = {"path": "author/decision.json", "sha256": "a" * 64}
        bad = prod.ProductionContext(
            context.store,
            context.coordinator,
            rt.SealedDocument(changed, context.state.reference),
            None,
        )
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.apply_internal_h1_readability_return(
                bad,
                readability_failure=failure,
                request=request,
                actor="production-orchestrator",
            )
        self.assertEqual(
            before,
            sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")),
        )

    def _apply_once(self, *, complete_side_effect=None):
        context, _old, completion, manifest, prepublish = self._waiting_author()
        failure, request = self._failure_and_request(
            context, prepublish, completion, manifest
        )
        patches = [
            mock.patch.object(
                prod,
                "h1_readability_prepublish_contract",
                return_value=(
                    prepublish,
                    [{"task_id": "plan-producer", "thread_id": "plan-thread"}],
                ),
            )
        ]
        if complete_side_effect is not None:
            patches.append(
                mock.patch.object(
                    context.store,
                    "complete_contract_upgrade",
                    side_effect=complete_side_effect,
                )
            )
        with patches[0]:
            if len(patches) == 1:
                result = prod.apply_internal_h1_readability_return(
                    context,
                    readability_failure=failure,
                    request=request,
                    actor="production-orchestrator",
                )
            else:
                with patches[1]:
                    result = prod.apply_internal_h1_readability_return(
                        context,
                        readability_failure=failure,
                        request=request,
                        actor="production-orchestrator",
                    )
        return context, failure, request, result

    def test_prepared_and_mid_derived_recovery_are_trusted(self):
        for mode in ("prepared", "mid-derived"):
            with self.subTest(mode=mode):
                captured = {}

                def interrupt(plan, *, successor):
                    captured["plan"] = plan
                    if mode == "mid-derived":
                        _receipt, derived = self.fixture._context().store.build_contract_upgrade_completion(
                            plan, successor=successor
                        )
                        # This branch is replaced below with the owning store;
                        # retaining the closure shape keeps the crash point exact.
                        captured["derived"] = derived
                    raise RuntimeError("simulated crash")

                context, _old, completion, manifest, prepublish = self._waiting_author()
                failure, request = self._failure_and_request(
                    context, prepublish, completion, manifest
                )

                def owned_interrupt(plan, *, successor):
                    captured["plan"] = plan
                    if mode == "mid-derived":
                        _receipt, derived = context.store.build_contract_upgrade_completion(
                            plan, successor=successor
                        )
                        context.store.persist_document(derived[0])
                    raise RuntimeError("simulated crash")

                with (
                    mock.patch.object(
                        prod,
                        "h1_readability_prepublish_contract",
                        return_value=(
                            prepublish,
                            [{"task_id": "plan-producer", "thread_id": "plan-thread"}],
                        ),
                    ),
                    mock.patch.object(
                        context.store,
                        "complete_contract_upgrade",
                        side_effect=owned_interrupt,
                    ),
                    self.assertRaisesRegex(RuntimeError, "simulated crash"),
                ):
                    prod.apply_internal_h1_readability_return(
                        context,
                        readability_failure=failure,
                        request=request,
                        actor="production-orchestrator",
                    )
                recovered = prod.resume_production_run(self.root)
                self.assertEqual("revise", recovered.state.data["status"])
                self.assertEqual(request.reference, recovered.state.data["active_return"])
                self.assertEqual(
                    "H1-A-plan", recovered.store.pending_work_order().data["action"]
                )
                self.fixture.tearDown()
                self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
                self.fixture.setUp()
                self.root = self.fixture.root

    def test_collision_and_duplicate_are_zero_write(self):
        context, _old, completion, manifest, prepublish = self._waiting_author()
        failure, request = self._failure_and_request(
            context, prepublish, completion, manifest
        )
        session_id = f"H1-READABILITY-{rt.canonical_sha256(request.reference)[:20]}"
        collision = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": session_id,
                "state": "initialized",
                "p1_completion": context.state.data["current_stage_completions"]["P1"],
                "previous_state_sha256": None,
                "artifacts": {"foreign": True},
            },
            f"H1/{session_id}/workspace-initialized.json",
        )
        context.store.persist_document(collision)
        before_state = context.store.latest_state()
        with (
            mock.patch.object(
                prod,
                "h1_readability_prepublish_contract",
                return_value=(
                    prepublish,
                    [{"task_id": "plan-producer", "thread_id": "plan-thread"}],
                ),
            ),
            self.assertRaises(Exception),
        ):
            prod.apply_internal_h1_readability_return(
                context,
                readability_failure=failure,
                request=request,
                actor="production-orchestrator",
            )
        self.assertEqual(before_state, context.store.latest_state())

    def test_complete_receipt_tamper_replay_fails_without_state_write(self):
        _context, _failure, _request, result = self._apply_once()
        receipt, returned, _initialized, _gate, _order = result
        receipt_path = returned.store.resolve_document_path(receipt.reference)
        changed = copy.deepcopy(receipt.data)
        changed["refresh_generation"] += 1
        receipt_path.write_text(rt.canonical_json(changed), encoding="utf-8", newline="")
        before = returned.store.latest_state()
        with self.assertRaises(Exception):
            prod.resume_production_run(self.root)
        self.assertEqual(before, returned.store.latest_state())


if __name__ == "__main__":
    unittest.main()
