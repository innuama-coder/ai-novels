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
import json
import unittest
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
fragment_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_internal_h1_fragment_return"
)


class InternalH1PlanReturnTests(unittest.TestCase):
    """Black-box contract for a fidelity-rejected H1-A plan."""

    _manifest = fragment_tests.InternalH1FragmentReturnTests._manifest
    _advance_h1 = fragment_tests.InternalH1FragmentReturnTests._advance_h1

    def setUp(self) -> None:
        parent = fragment_tests.InternalH1FragmentReturnTests(methodName="runTest")
        parent.setUp()
        self.fixture = parent.fixture
        self.root = parent.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _candidate_and_failure(self, context, ready, *, marker="001"):
        candidate = rt.seal_document(
            {
                "schema_version": "2.0",
                "id": "MOD-WORLD",
                "title": "World",
                "summary": "The candidate invents unsupported city names.",
            },
            f"H1/{ready.data['session_id']}/fidelity-candidate-{marker}.json",
        )
        plan_manifest = ready.data["artifacts"]["plan_manifest"]
        fragment_manifest = ready.data["artifacts"]["fragment_manifest"]
        body = {
            "schema_version": "2.0",
            "skill": "novel-conception-presentation-fidelity-reviewer",
            "run_id": context.state.data["run_id"],
            "h1_session_id": ready.data["session_id"],
            "reviewer": {
                "task_id": f"/root/fresh-fidelity-review-{marker}",
                "thread_id": f"THREAD-{marker}",
                "independence_basis": "separate-task-no-producer-context",
            },
            "inputs": {
                "p1_completion": {
                    "path": ready.data["p1_completion"]["path"],
                    "sha256": ready.data["p1_completion"]["sha256"],
                },
                "plan_manifest": plan_manifest,
                "fragment_manifest": fragment_manifest,
                "report_sha256": candidate.reference["sha256"],
            },
            "dimensions": [
                {
                    "id": dimension,
                    "verdict": "revise" if dimension == "world_story_character_fidelity" else "pass",
                    "evidence_element_ids": ["MOD-WORLD"],
                    "finding": (
                        "The world module adds city names unsupported by P1."
                        if dimension == "world_story_character_fidelity"
                        else "No additional defect was found in this dimension."
                    ),
                }
                for dimension in (
                    "author_control_fidelity",
                    "world_story_character_fidelity",
                    "omission_and_emphasis_fidelity",
                    "fragment_authority_boundary",
                    "review_decision_integrity",
                )
            ],
            "element_reviews": [{
                "element_id": "MOD-WORLD",
                "content_sha256": rt.canonical_sha256(candidate.data),
                "source_anchor_ids": ["SRC-WORLD"],
                "verdict": "revise",
                "semantic_assertion": "The city names have no support in the source package.",
                "evidence_quotes": ["unsupported city names"],
                "no_material_omission": True,
                "no_contradiction": False,
                "no_authority_escalation": False,
            }],
            "blockers": [],
            "verdict": "revise",
        }
        failure = rt.seal_document(
            body,
            f"reviews/h1-presentation-fidelity/{marker}.json",
        )
        context.store.persist_document(candidate)
        assignment = prod.assign_internal_h1_plan_fidelity_review(
            context,
            candidate_report=candidate,
            reviewer=body["reviewer"],
            actor="production-orchestrator",
        )
        completion = prod.record_internal_h1_plan_fidelity_failure(
            context,
            assignment=assignment,
            candidate_report=candidate,
            fidelity_failure=failure,
            actor="novel-conception-presentation-fidelity-reviewer",
        )
        return candidate, failure, completion

    def _request(self, failure):
        body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id=f"RET-H1-A-PLAN-{failure.reference['sha256'][:24]}",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_plan",
            problem="Independent fidelity review rejected unsupported city specificity.",
            evidence_ids=[failure.reference["sha256"]],
            violated_contract="H1-A may only present specificity supported by P1.",
            required_revision="Re-plan H1-A from the preserved P1 completion.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        return rt.seal_document(
            body, f"returns/{body['return_id']}/return-request.json"
        )

    def _ready_with_pending_assemble(self):
        context, planned, ready, _consumed, _manifest = self._advance_h1()
        _, assemble = prod.issue_stage_work(context, action="H1-A-assemble", inputs={})
        return context, planned, ready, assemble

    def _advance_returned_h1(self, context, initialized, plan_order):
        helper = object.__new__(fragment_tests.InternalH1FragmentReturnTests)
        helper.root = self.root
        plan_manifest = helper._manifest(
            context,
            initialized,
            "h1-plan",
            (
                "source_inventory", "review_plan", "fragment_briefs",
                "generation_session", "generation_evidence_index", "execution_record",
            ),
        )
        planned_transition = context.coordinator.accept_h1_workspace_transition(
            current_workspace=initialized,
            package_manifest=plan_manifest,
            expected_next_state="planned",
            active_return_request=context.active_return,
        )
        planned = planned_transition.workspace
        prod._prepare_h1_commit(
            context, plan_order, bound=initialized, successor=planned,
            manifest=plan_manifest,
        )
        context.store.persist_workspace(planned)
        context.store.mark_work_order_consumed(plan_order, successor=planned)
        _, fragment_order = prod.issue_stage_work(context, action="H1-B", inputs={})
        fragment_manifest = helper._manifest(
            context,
            planned,
            "h1-fragments",
            (
                "fragment_package", "fragments", "generation_session",
                "session_workspace_completion", "generation_evidence_index",
                "execution_record",
            ),
        )
        ready_transition = context.coordinator.accept_h1_workspace_transition(
            current_workspace=planned,
            package_manifest=fragment_manifest,
            expected_next_state="fragments_ready",
            active_return_request=context.active_return,
        )
        ready = ready_transition.workspace
        prod._prepare_h1_commit(
            context, fragment_order, bound=planned, successor=ready,
            manifest=fragment_manifest,
        )
        context.store.persist_workspace(ready)
        context.store.mark_work_order_consumed(fragment_order, successor=ready)
        return helper, planned, ready, fragment_order, fragment_manifest

    def _active_fragment_return_for_plan_escalation(self, *, marker):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker=f"{marker}-parent-plan"
        )
        parent_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=parent_request,
            actor="production-orchestrator",
        )
        helper, planned, reviewed_ready, fragment_order, fragment_manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        prod.issue_stage_work(returned, action="H1-A-assemble", inputs={})
        fragment_failure, fragment_completion = helper._failure(
            returned,
            reviewed_ready,
            fragment_order,
            fragment_manifest,
            marker,
        )
        fragment_request = helper._request(fragment_failure)
        _, narrowed, _, current_fragment_order = (
            prod.apply_internal_h1_fragment_return(
                returned,
                consumed_work_order=fragment_order,
                fidelity_failure=fragment_failure,
                review_completion=fragment_completion,
                request=fragment_request,
                actor="production-orchestrator",
                inputs={},
            )
        )
        return (
            narrowed,
            planned,
            reviewed_ready,
            current_fragment_order,
            fragment_request,
            fragment_failure,
        )

    def _direct_active_fragment_return_for_plan_escalation(self, *, marker):
        context, planned, reviewed_ready, fragment_order, fragment_manifest = (
            self._advance_h1()
        )
        helper = object.__new__(fragment_tests.InternalH1FragmentReturnTests)
        helper.root = self.root
        fragment_failure, fragment_completion = helper._failure(
            context,
            reviewed_ready,
            fragment_order,
            fragment_manifest,
            marker,
        )
        fragment_request = helper._request(fragment_failure)
        _, narrowed, _, current_fragment_order = (
            prod.apply_internal_h1_fragment_return(
                context,
                consumed_work_order=fragment_order,
                fidelity_failure=fragment_failure,
                review_completion=fragment_completion,
                request=fragment_request,
                actor="production-orchestrator",
                inputs={},
            )
        )
        return narrowed, planned, reviewed_ready, current_fragment_order

    def test_revise_returns_to_fresh_plan_and_invalidates_assemble(self):
        context, _planned, ready, assemble = self._ready_with_pending_assemble()
        candidate, failure, review_completion = self._candidate_and_failure(context, ready)
        request = self._request(failure)
        upstream = copy.deepcopy(context.state.data["current_stage_completions"])

        receipt, returned, initialized, gate, order = (
            prod.apply_internal_h1_plan_return(
                context,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=review_completion,
                request=request,
                actor="production-orchestrator",
            )
        )

        self.assertEqual("internal_h1_plan_return", receipt.data["transition_mode"])
        self.assertEqual(upstream, returned.state.data["current_stage_completions"])
        self.assertEqual("initialized", initialized.data["state"])
        self.assertNotEqual(ready.data["session_id"], initialized.data["session_id"])
        self.assertEqual("H1-A-plan", order.data["action"])
        self.assertEqual(initialized.reference, order.data["h1_workspace"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertTrue((self.root / ready.reference["path"]).is_file())
        self.assertTrue((self.root / assemble.reference["path"]).is_file())
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        with self.assertRaises(Exception):
            resumed.store.require_current_work_order(assemble, state=resumed.state)

    def test_missing_tampered_or_fake_review_is_atomic(self):
        context, _planned, ready, assemble = self._ready_with_pending_assemble()
        candidate, failure, review_completion = self._candidate_and_failure(context, ready)
        request = self._request(failure)
        before_state = context.store.latest_state().reference
        before_workspace = context.store.latest_workspace().reference
        before_order = context.store.pending_work_order().reference

        cases = []
        cases.append(("missing", None, candidate, review_completion, request))
        tampered_body = copy.deepcopy(failure.data)
        tampered_body["dimensions"][1]["finding"] = "Tampered after sealing."
        cases.append((
            "tampered",
            rt.SealedDocument(data=tampered_body, reference=failure.reference),
            candidate,
            review_completion,
            request,
        ))
        fake_body = copy.deepcopy(failure.data)
        fake_body["reviewer"]["task_id"] = "/root/h1-a-producer"
        fake = rt.seal_document(fake_body, "reviews/h1-presentation-fidelity/fake.json")
        cases.append(("fake-attribution", fake, candidate, review_completion, self._request(fake)))
        invented_body = copy.deepcopy(failure.data)
        invented_body["reviewer"] = {
            "task_id": "/root/invented-independent-reviewer",
            "thread_id": "THREAD-INVENTED-INDEPENDENT-REVIEWER",
            "independence_basis": "separate-task-no-producer-context",
        }
        invented = rt.seal_document(
            invented_body,
            "reviews/h1-presentation-fidelity/invented-not-persisted.json",
        )
        with self.assertRaises(Exception):
            context.store.persist_document(invented)
        wrong_body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-WRONG-H1-B",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_fragment",
            problem="Wrong internal owner.",
            evidence_ids=[failure.reference["sha256"]],
            violated_contract="The plan return may not cross to H1-B.",
            required_revision="Do not cross the internal owner boundary.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        wrong_request = rt.seal_document(
            wrong_body, "returns/RET-WRONG-H1-B/return-request.json"
        )
        cases.append(("cross-owner", failure, candidate, review_completion, wrong_request))

        for label, submitted_failure, submitted_candidate, submitted_completion, submitted_request in cases:
            with self.subTest(label=label):
                with self.assertRaises(prod.ProductionOrchestratorError):
                    prod.apply_internal_h1_plan_return(
                        context,
                        fidelity_failure=submitted_failure,
                        candidate_report=submitted_candidate,
                        review_completion=submitted_completion,
                        request=submitted_request,
                        actor="production-orchestrator",
                    )
                self.assertEqual(before_state, context.store.latest_state().reference)
                self.assertEqual(before_workspace, context.store.latest_workspace().reference)
                self.assertEqual(before_order, context.store.pending_work_order().reference)
                self.assertEqual(assemble.reference, before_order)

    def test_wrong_actor_and_repeat_are_rejected(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, review_completion = self._candidate_and_failure(context, ready, marker="repeat")
        request = self._request(failure)
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_internal_h1_plan_return(
                context,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=review_completion,
                request=request,
                actor="novel-conception-human-review-assembler",
            )
        self.assertEqual("PROD_WORK_ACTOR_MISMATCH", caught.exception.code)

        _receipt, returned, _initialized, _gate, _order = (
            prod.apply_internal_h1_plan_return(
                context,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=review_completion,
                request=request,
                actor="production-orchestrator",
            )
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as repeated:
            prod.apply_internal_h1_plan_return(
                returned,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=review_completion,
                request=request,
                actor="production-orchestrator",
            )
        self.assertEqual("PROD_H1_PLAN_RETURN_STATE_INVALID", repeated.exception.code)

    def test_prepared_crash_recovers_same_plan_return(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, review_completion = self._candidate_and_failure(
            context, ready, marker="prepared"
        )
        request = self._request(failure)
        with mock.patch.object(
            context.store,
            "persist_state",
            side_effect=RuntimeError("prepared crash"),
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                prod.apply_internal_h1_plan_return(
                    context,
                    fidelity_failure=failure,
                    candidate_report=candidate,
                    review_completion=review_completion,
                    request=request,
                    actor="production-orchestrator",
                )
        plan_path = next(
            path
            for path in (
                self.root / "orchestration" / "contract-upgrades"
            ).glob("*.prepared.json")
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
        )
        plan = context.store.load_document({
            "path": plan_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(plan_path),
        })
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(plan.data["successor_state"], resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(
            "initialized", resumed.store.latest_workspace().data["state"]
        )
        self.assertEqual(
            "H1-A-plan", resumed.store.pending_work_order().data["action"]
        )

    def test_active_plan_return_can_refresh_to_a_fresh_plan_return(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker="first-plan"
        )
        first_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=first_request,
            actor="production-orchestrator",
        )
        _, _planned2, ready2, _fragment_order, _manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        _, assemble2 = prod.issue_stage_work(
            returned, action="H1-A-assemble", inputs={}
        )
        candidate2, failure2, completion2 = self._candidate_and_failure(
            returned, ready2, marker="second-plan"
        )
        second_request = self._request(failure2)
        receipt, refreshed, initialized2, _, order2 = (
            prod.apply_internal_h1_plan_return(
                returned,
                fidelity_failure=failure2,
                candidate_report=candidate2,
                review_completion=completion2,
                request=second_request,
                actor="production-orchestrator",
            )
        )
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(first_request.reference, receipt.data["superseded_return"])
        self.assertEqual(second_request.reference, refreshed.active_return.reference)
        self.assertEqual("initialized", initialized2.data["state"])
        self.assertEqual("H1-A-plan", order2.data["action"])
        self.assertTrue((self.root / assemble2.reference["path"]).is_file())
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(second_request.reference, resumed.active_return.reference)
        self.assertEqual(initialized2.reference, resumed.store.latest_workspace().reference)

    def test_active_plan_return_can_narrow_to_fresh_fragment_return(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker="parent-plan"
        )
        first_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=first_request,
            actor="production-orchestrator",
        )
        helper, planned2, ready2, fragment_order, fragment_manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        _, assemble2 = prod.issue_stage_work(
            returned, action="H1-A-assemble", inputs={}
        )
        fragment_failure, fragment_completion = helper._failure(
            returned,
            ready2,
            fragment_order,
            fragment_manifest,
            "nested-fragment",
        )
        fragment_request = helper._request(fragment_failure)
        receipt, narrowed, _, order = prod.apply_internal_h1_fragment_return(
            returned,
            consumed_work_order=fragment_order,
            fidelity_failure=fragment_failure,
            review_completion=fragment_completion,
            request=fragment_request,
            actor="production-orchestrator",
            inputs={},
        )
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(first_request.reference, receipt.data["superseded_return"])
        self.assertEqual(fragment_request.reference, narrowed.active_return.reference)
        self.assertEqual("H1-B", order.data["action"])
        self.assertEqual(planned2.reference, order.data["h1_workspace"])
        self.assertTrue((self.root / ready2.reference["path"]).is_file())
        self.assertTrue((self.root / assemble2.reference["path"]).is_file())
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(fragment_request.reference, resumed.active_return.reference)
        self.assertEqual(planned2.reference, resumed.store.latest_workspace().reference)

    def test_active_fragment_return_can_escalate_to_fresh_protected_plan(self):
        (
            narrowed,
            planned,
            reviewed_ready,
            current_fragment_order,
            fragment_request,
            _fragment_failure,
        ) = self._active_fragment_return_for_plan_escalation(
            marker="subowner-escalation"
        )
        candidate, failure, completion = self._candidate_and_failure(
            narrowed, reviewed_ready, marker="subowner-plan-failure"
        )
        request = self._request(failure)
        fragment_qualification = narrowed.store.current_contract_upgrade()
        inherited_invalidation_refs = list(
            fragment_qualification.data["session_invalidation_receipts"]
        )
        inherited_invalidation_bytes = {
            item["path"]: (self.root / item["path"]).read_bytes()
            for item in inherited_invalidation_refs
        }
        receipt, escalated, initialized, gate, order = (
            prod.apply_internal_h1_plan_return(
                narrowed,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=completion,
                request=request,
                actor="production-orchestrator",
            )
        )
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(fragment_request.reference, receipt.data["superseded_return"])
        self.assertEqual(request.reference, escalated.active_return.reference)
        self.assertEqual("initialized", initialized.data["state"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual("H1-A-plan", order.data["action"])
        self.assertEqual(initialized.reference, order.data["h1_workspace"])
        plan = escalated.store.load_document(receipt.data["plan"])
        self.assertEqual(1, len(plan.data["session_references"]))
        self.assertEqual(
            inherited_invalidation_refs[0],
            plan.data["stale_identity"]["prior_fragment_session_invalidation"],
        )
        self.assertEqual(
            inherited_invalidation_bytes,
            {
                path: (self.root / path).read_bytes()
                for path in inherited_invalidation_bytes
            },
        )
        self.assertTrue((self.root / planned.reference["path"]).is_file())
        self.assertTrue((self.root / reviewed_ready.reference["path"]).is_file())
        self.assertTrue((self.root / current_fragment_order.reference["path"]).is_file())
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(initialized.reference, resumed.store.latest_workspace().reference)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        with self.assertRaises(Exception):
            resumed.store.require_current_work_order(
                current_fragment_order, state=resumed.state
            )

    def test_direct_active_fragment_return_can_escalate_through_same_protected_chain(self):
        narrowed, _planned, reviewed_ready, old_order = (
            self._direct_active_fragment_return_for_plan_escalation(
                marker="direct-subowner-escalation"
            )
        )
        candidate, failure, completion = self._candidate_and_failure(
            narrowed, reviewed_ready, marker="direct-subowner-plan-failure"
        )
        request = self._request(failure)
        receipt, escalated, initialized, _, order = prod.apply_internal_h1_plan_return(
            narrowed,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
        )
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(request.reference, escalated.active_return.reference)
        self.assertEqual(initialized.reference, order.data["h1_workspace"])
        self.assertEqual("H1-A-plan", order.data["action"])
        with self.assertRaises(Exception):
            escalated.store.require_current_work_order(old_order, state=escalated.state)

    def test_active_fragment_plan_escalation_requires_fresh_reviewer_and_exact_ancestry(self):
        (
            narrowed,
            _planned,
            reviewed_ready,
            _current_fragment_order,
            _fragment_request,
            fragment_failure,
        ) = self._active_fragment_return_for_plan_escalation(
            marker="subowner-review-guards"
        )
        candidate = rt.seal_document(
            {
                "schema_version": "2.0",
                "id": "MOD-WORLD",
                "title": "World",
                "summary": "The candidate exposes an internal stage marker.",
            },
            f"H1/{reviewed_ready.data['session_id']}/guard-candidate.json",
        )
        narrowed.store.persist_document(candidate)
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError,
            "PROD_H1_PLAN_FIDELITY_REVIEW_NOT_INDEPENDENT",
        ):
            prod.assign_internal_h1_plan_fidelity_review(
                narrowed,
                candidate_report=candidate,
                reviewer=fragment_failure.data["reviewer"],
                actor="production-orchestrator",
            )
        self.assertEqual(before, self.fixture._run_inventory())

        forged_active = rt.SealedDocument(
            data={
                **copy.deepcopy(narrowed.active_return.data),
                "calculated_owner": "H1-C",
            },
            reference=copy.deepcopy(narrowed.active_return.reference),
        )
        forged_context = prod.ProductionContext(
            narrowed.store, narrowed.coordinator, narrowed.state, forged_active
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as foreign:
            prod.assign_internal_h1_plan_fidelity_review(
                forged_context,
                candidate_report=candidate,
                reviewer={
                    "task_id": "/root/fresh-subowner-plan-review",
                    "thread_id": "THREAD-FRESH-SUBOWNER-PLAN-REVIEW",
                    "independence_basis": "separate-task-no-producer-context",
                },
                actor="production-orchestrator",
            )
        self.assertEqual("PROD_H1_PLAN_RETURN_STATE_INVALID", foreign.exception.code)
        self.assertEqual(before, self.fixture._run_inventory())

        generic_request = self._request(fragment_failure)
        with self.assertRaises(prod.ProductionOrchestratorError) as generic_refresh:
            prod.refresh_active_stage_return(
                narrowed,
                request=generic_request,
                actor="production-orchestrator",
                inputs={},
            )
        self.assertEqual(
            "PROD_ACTIVE_STAGE_RETURN_ROUTE_INVALID", generic_refresh.exception.code
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as generic_escalation:
            prod.apply_active_return_escalation(
                narrowed,
                request=generic_request,
                actor="production-orchestrator",
                inputs={},
            )
        self.assertEqual(
            "PROD_ACTIVE_RETURN_ESCALATION_NOT_EARLIER",
            generic_escalation.exception.code,
        )
        self.assertEqual(before, self.fixture._run_inventory())

        stale_state = narrowed.store.load_document(
            narrowed.state.data["previous_state"]
        )
        stale_context = prod.ProductionContext(
            narrowed.store,
            narrowed.coordinator,
            stale_state,
            narrowed.active_return,
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as stale:
            prod.assign_internal_h1_plan_fidelity_review(
                stale_context,
                candidate_report=candidate,
                reviewer={
                    "task_id": "/root/fresh-stale-plan-review",
                    "thread_id": "THREAD-FRESH-STALE-PLAN-REVIEW",
                    "independence_basis": "separate-task-no-producer-context",
                },
                actor="production-orchestrator",
            )
        self.assertEqual("PROD_CONTEXT_STALE", stale.exception.code)
        self.assertEqual(before, self.fixture._run_inventory())

    def test_active_fragment_plan_escalation_prepared_crash_recovers_and_replay_rejects(self):
        (
            narrowed,
            _planned,
            reviewed_ready,
            _current_fragment_order,
            fragment_request,
            _fragment_failure,
        ) = self._active_fragment_return_for_plan_escalation(
            marker="subowner-recovery"
        )
        candidate, failure, completion = self._candidate_and_failure(
            narrowed, reviewed_ready, marker="subowner-recovery-plan"
        )
        request = self._request(failure)
        with mock.patch.object(
            narrowed.store, "persist_state", side_effect=RuntimeError("prepared crash")
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                prod.apply_internal_h1_plan_return(
                    narrowed,
                    fidelity_failure=failure,
                    candidate_report=candidate,
                    review_completion=completion,
                    request=request,
                    actor="production-orchestrator",
                )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual("H1-A-plan", resumed.store.pending_work_order().data["action"])
        complete = resumed.store.current_contract_upgrade()
        self.assertEqual(fragment_request.reference, complete.data["superseded_return"])
        with self.assertRaises(prod.ProductionOrchestratorError) as repeated:
            prod.apply_internal_h1_plan_return(
                resumed,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=completion,
                request=request,
                actor="production-orchestrator",
            )
        self.assertIn(
            repeated.exception.code,
            {"PROD_H1_PLAN_RETURN_STATE_INVALID", "PROD_H1_PLAN_FIDELITY_FAILURE_REUSED"},
        )

    def test_active_plan_return_rejects_fragment_producer_as_reviewer(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker="parent-before-producer-attack"
        )
        first_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=first_request,
            actor="production-orchestrator",
        )
        helper, _planned2, ready2, fragment_order, fragment_manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        reviewer = {
                "task_id": "/root/h1-b-producer",
                "thread_id": "THREAD-H1-B-PRODUCER",
                "independence_basis": "separate-task-no-producer-context",
        }
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError,
            "PROD_H1_FRAGMENT_FIDELITY_REVIEW_NOT_INDEPENDENT",
        ):
            prod.assign_internal_h1_fragment_fidelity_review(
                returned,
                consumed_work_order=fragment_order,
                fragment_manifest=fragment_manifest,
                reviewer=reviewer,
                actor="production-orchestrator",
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_nested_fragment_return_recovers_from_prepared_crash(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker="recovery-parent"
        )
        first_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=first_request,
            actor="production-orchestrator",
        )
        helper, planned2, ready2, fragment_order, fragment_manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        prod.issue_stage_work(returned, action="H1-A-assemble", inputs={})
        fragment_failure, fragment_completion = helper._failure(
            returned,
            ready2,
            fragment_order,
            fragment_manifest,
            "recovery-fragment",
        )
        fragment_request = helper._request(fragment_failure)
        with mock.patch.object(
            returned.store, "persist_state", side_effect=RuntimeError("prepared crash")
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                prod.apply_internal_h1_fragment_return(
                    returned,
                    consumed_work_order=fragment_order,
                    fidelity_failure=fragment_failure,
                    review_completion=fragment_completion,
                    request=fragment_request,
                    actor="production-orchestrator",
                    inputs={},
                )
        prepared = next(
            returned.store.load_document({
                "path": path.relative_to(self.root).as_posix(),
                "sha256": rt.sha256_file(path),
            })
            for path in (
                self.root / "orchestration" / "contract-upgrades"
            ).glob("*.prepared.json")
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
            and json.loads(path.read_text(encoding="utf-8")).get(
                "return_request"
            ) == fragment_request.reference
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(prepared.data["successor_state"], resumed.state.reference)
        self.assertEqual(fragment_request.reference, resumed.active_return.reference)
        self.assertEqual(planned2.reference, resumed.store.latest_workspace().reference)
        self.assertEqual("H1-B", resumed.store.pending_work_order().data["action"])

    def test_foreign_active_return_cannot_authorize_nested_fragment_return(self):
        context, _planned, ready, _assemble = self._ready_with_pending_assemble()
        candidate, failure, completion = self._candidate_and_failure(
            context, ready, marker="foreign-parent"
        )
        first_request = self._request(failure)
        _, returned, initialized, _, plan_order = prod.apply_internal_h1_plan_return(
            context,
            fidelity_failure=failure,
            candidate_report=candidate,
            review_completion=completion,
            request=first_request,
            actor="production-orchestrator",
        )
        helper, _planned2, ready2, fragment_order, fragment_manifest = (
            self._advance_returned_h1(returned, initialized, plan_order)
        )
        prod.issue_stage_work(returned, action="H1-A-assemble", inputs={})
        fragment_failure, fragment_completion = helper._failure(
            returned,
            ready2,
            fragment_order,
            fragment_manifest,
            "foreign-fragment",
        )
        fragment_request = helper._request(fragment_failure)
        forged_active = rt.SealedDocument(
            data={**copy.deepcopy(first_request.data), "calculated_owner": "H1-C"},
            reference=copy.deepcopy(first_request.reference),
        )
        forged_context = prod.ProductionContext(
            returned.store, returned.coordinator, returned.state, forged_active
        )
        before = self.fixture._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_internal_h1_fragment_return(
                forged_context,
                consumed_work_order=fragment_order,
                fidelity_failure=fragment_failure,
                review_completion=fragment_completion,
                request=fragment_request,
                actor="production-orchestrator",
                inputs={},
            )
        self.assertEqual("PROD_H1_FRAGMENT_RETURN_STATE_INVALID", caught.exception.code)
        self.assertEqual(before, self.fixture._run_inventory())
