from __future__ import annotations

import copy
import importlib
import json
import unittest
from pathlib import PurePosixPath
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)
fixtures = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)


class InternalH1FragmentReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _manifest(
        self,
        context,
        workspace,
        profile,
        artifact_roles,
        *,
        manifest_mutator=None,
        fragment_package_mutator=None,
    ):
        if profile == "h1-fragments":
            logical_root = f"H1/{workspace.data['session_id']}/{profile}"

            def persist_json(name, body):
                document = rt.seal_document(body, f"{logical_root}/{name}")
                context.store.persist_document(document)
                return {"path": name, "sha256": document.reference["sha256"]}

            fragment_package_body = {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "h1_session_id": workspace.data["session_id"],
                "p1_completion": {
                    "path": workspace.data["p1_completion"]["path"],
                    "sha256": workspace.data["p1_completion"]["sha256"],
                },
                "plan_manifest": workspace.data["artifacts"]["plan_manifest"],
                "authority_status": "non_authoritative_sample",
                "fragments": [],
            }
            if fragment_package_mutator is not None:
                fragment_package_mutator(fragment_package_body)
            fragment_package = persist_json(
                "fragment-package.json", fragment_package_body
            )
            generation_session = persist_json(
                "generation-session.json",
                {
                    "schema_version": "1.0",
                    "kind": "generation-session",
                    "identity": {
                        "task_id": "/root/h1-b-producer",
                        "thread_id": "THREAD-H1-B-PRODUCER",
                        "independence_basis": "assigned-stage-owner",
                    },
                },
            )
            workspace_completion = persist_json(
                "session-workspace-completion.json",
                {"schema_version": "1.0", "kind": "workspace-completion"},
            )
            evidence_index = persist_json(
                "generation-evidence-index.json",
                {"schema_version": "1.0", "kind": "evidence-index"},
            )
            execution = persist_json(
                "execution-record.json",
                {"schema_version": "1.0", "kind": "execution-record"},
            )
            validation = persist_json(
                "validation.json",
                {"schema_version": "1.0", "verdict": "ready"},
            )
            fragments_path = self.root / logical_root / "fragments.md"
            fragments_path.parent.mkdir(parents=True, exist_ok=True)
            fragments_path.write_text("# Fragment fixture\n", encoding="utf-8")
            fragments = {
                "path": "fragments.md",
                "sha256": rt.sha256_file(fragments_path),
            }
            pretty_schema_path = self.root / logical_root / "implementation/schema.json"
            pretty_schema_path.parent.mkdir(parents=True, exist_ok=True)
            pretty_schema_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "type": "object",
                    },
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            pretty_schema = {
                "path": "implementation/schema.json",
                "sha256": rt.sha256_file(pretty_schema_path),
            }
            roles = {
                "fragment_package": fragment_package,
                "fragments": fragments,
                "generation_session": generation_session,
                "session_workspace_completion": workspace_completion,
                "generation_evidence_index": evidence_index,
                "execution_record": execution,
            }
            files = sorted(
                [*roles.values(), validation, pretty_schema],
                key=lambda item: item["path"],
            )
            body = {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "package_profile": profile,
                "verdict": "ready",
                "files": files,
                "artifact_roles": roles,
                "validation": validation,
                "implementation": [execution, pretty_schema],
                "parent_state_sha256": workspace.reference["sha256"],
                "session_id": workspace.data["session_id"],
            }
            if manifest_mutator is not None:
                manifest_mutator(body)
            return rt.seal_document(
                body, f"{logical_root}/package-manifest.json"
            )

        item = rt.seal_document(
            {
                "schema_version": "1.0",
                "kind": profile,
                "identity": {
                    "task_id": "/root/h1-a-producer",
                    "thread_id": "THREAD-H1-A-PRODUCER",
                    "independence_basis": "assigned-stage-owner",
                },
            },
            f"H1/{workspace.data['session_id']}/{profile}/artifact.json",
        )
        context.store.persist_document(item)
        roles = {name: item.reference for name in artifact_roles}
        manifest = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "package_profile": profile,
                "verdict": "ready",
                "files": [item.reference],
                "artifact_roles": roles,
                "validation": item.reference,
                "implementation": [item.reference],
                "parent_state_sha256": workspace.reference["sha256"],
                "session_id": workspace.data["session_id"],
            },
            f"H1/{workspace.data['session_id']}/{profile}/package-manifest.json",
        )
        return manifest

    def _advance_h1(
        self, *, fragment_manifest_mutator=None, fragment_package_mutator=None,
        legacy_fragment_path=False,
    ):
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
        initialized = prod.initialize_h1_workspace(context, session_id="H1-RETURN")
        _, plan_order = prod.issue_stage_work(context, action="H1-A-plan", inputs={})
        plan_manifest = self._manifest(
            context,
            initialized,
            "h1-plan",
            (
                "source_inventory", "review_plan", "fragment_briefs",
                "generation_session", "generation_evidence_index", "execution_record",
            ),
        )
        plan_transition = context.coordinator.accept_h1_workspace_transition(
            current_workspace=initialized,
            package_manifest=plan_manifest,
            expected_next_state="planned",
        )
        planned = plan_transition.workspace
        prod._prepare_h1_commit(
            context,
            plan_order,
            bound=initialized,
            successor=planned,
            manifest=plan_manifest,
        )
        context.store.persist_workspace(planned)
        context.store.mark_work_order_consumed(plan_order, successor=planned)

        _, fragment_order = prod.issue_stage_work(
            context,
            action="H1-B",
            inputs={
                "p1_package": str(self.root / "P1" / "attempt-008"),
                "plan_package": str(self.root / "H1" / "plan"),
            },
        )
        fragment_manifest = self._manifest(
            context,
            planned,
            "h1-fragments",
            (
                "fragment_package", "fragments", "generation_session",
                "session_workspace_completion", "generation_evidence_index",
                "execution_record",
            ),
            manifest_mutator=fragment_manifest_mutator,
            fragment_package_mutator=fragment_package_mutator,
        )
        fragment_coordinator = context.coordinator
        if legacy_fragment_path:
            coordinator_module = importlib.import_module(
                "harnesses.novel-conception-autonomous.runtime.coordinator"
            )
            fragment_coordinator = coordinator_module.AutonomousCoordinator.from_snapshot(
                context.state.data,
                context.state.reference,
                active_return_request=context.active_return,
                runtime=context.store.runtime,
            )
        fragment_transition = fragment_coordinator.accept_h1_workspace_transition(
            current_workspace=planned,
            package_manifest=fragment_manifest,
            expected_next_state="fragments_ready",
        )
        ready = fragment_transition.workspace
        prod._prepare_h1_commit(
            context,
            fragment_order,
            bound=planned,
            successor=ready,
            manifest=fragment_manifest,
        )
        context.store.persist_workspace(ready)
        context.store.mark_work_order_consumed(fragment_order, successor=ready)
        return context, planned, ready, fragment_order, fragment_manifest

    def _failure_document(
        self, context, ready, consumed, manifest, marker="001", *, reviewer=None
    ):
        body = {
            "schema_version": "1.0",
            "kind": "internal-h1-fragment-fidelity-failure",
            "run_id": "RUN-PROD-1",
            "h1_session_id": ready.data["session_id"],
            "review_id": f"H1-B-FIDELITY-{marker}",
            "reviewer": reviewer or {
                "task_id": "/root/independent-review",
                "thread_id": f"THREAD-{marker}",
                "independence_basis": "separate-task-no-producer-context",
            },
            "fragment_manifest": manifest.reference,
            "findings": [{
                "id": f"FINDING-{marker}",
                "fragment_id": "FRAG-01",
                "projection_id": "PROJ-01",
                "source_anchor_id": "SRC-01",
                "source_value_sha256": "a" * 64,
                "evidence_quote": "The quote is not faithful.",
                "problem": "The cited sentence does not preserve the source field.",
            }],
            "verdict": "fail",
            "status": "sealed",
        }
        failure = rt.seal_document(
            body, f"reviews/h1-fragment-fidelity/{body['review_id']}.json"
        )
        return failure

    def _failure(
        self, context, ready, consumed, manifest, marker="001", *, reviewer=None
    ):
        failure = self._failure_document(
            context,
            ready,
            consumed,
            manifest,
            marker,
            reviewer=reviewer,
        )
        assignment = prod.assign_internal_h1_fragment_fidelity_review(
            context,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            reviewer=failure.data["reviewer"],
            actor="production-orchestrator",
        )
        completion = prod.record_internal_h1_fragment_fidelity_failure(
            context,
            assignment=assignment,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            fidelity_failure=failure,
            actor="novel-conception-presentation-fidelity-reviewer",
        )
        return failure, completion

    def _request(self, failure):
        body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id=f"RET-{failure.data['review_id']}",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_fragment",
            problem="Independent fidelity review rejected the accepted fragment evidence.",
            evidence_ids=[failure.data["review_id"]],
            violated_contract="Every H1-B projection quote must preserve its P1 source.",
            required_revision="Regenerate H1-B from the preserved plan.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        return rt.seal_document(
            body, f"returns/{body['return_id']}/return-request.json"
        )

    def test_success_preserves_upstream_and_reissues_h1_b(self):
        context, planned, ready, consumed, manifest = self._advance_h1()
        self.assertEqual(
            (
                f"H1/{ready.data['session_id']}/workspace-fragments_ready-"
                f"{manifest.reference['sha256'][:24]}.json"
            ),
            ready.reference["path"],
        )
        failure, completion = self._failure(context, ready, consumed, manifest)
        request = self._request(failure)
        upstream = copy.deepcopy(context.state.data["current_stage_completions"])
        receipt, returned, gate, order = prod.apply_internal_h1_fragment_return(
            context,
            consumed_work_order=consumed,
            fidelity_failure=failure,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        self.assertEqual("internal_h1_fragment_return", receipt.data["transition_mode"])
        self.assertEqual(upstream, returned.state.data["current_stage_completions"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual(planned.reference, returned.store.latest_workspace().reference)
        self.assertEqual("H1-B", order.data["action"])
        self.assertEqual(planned.reference, order.data["h1_workspace"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual(
            prod._internal_h1_fragment_inputs(returned, planned_workspace=planned),
            order.data["inputs"],
        )
        markers = list(
            (self.root / "orchestration/h1-artifact-invalidations").glob("*.json")
        )
        self.assertEqual(1, len(markers))
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        self.assertEqual(planned.reference, resumed.store.latest_workspace().reference)

    def test_fragment_producer_cannot_review_its_own_first_return(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
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
                context,
                consumed_work_order=consumed,
                fragment_manifest=manifest,
                reviewer=reviewer,
                actor="production-orchestrator",
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_authority_apis_are_public_and_direct_writes_are_blocked(self):
        self.assertIs(
            rt.assign_internal_h1_fragment_fidelity_review,
            prod.assign_internal_h1_fragment_fidelity_review,
        )
        self.assertIs(
            rt.record_internal_h1_fragment_fidelity_failure,
            prod.record_internal_h1_fragment_fidelity_failure,
        )
        for logical in (
            "reviews/h1-fragment-fidelity/FORGED.json",
            "orchestration/h1-fragment-fidelity-review-assignments/FORGED.json",
            "orchestration/h1-fragment-fidelity-review-completions/FORGED.json",
        ):
            with self.subTest(path=logical):
                forged = rt.seal_document(
                    {"schema_version": "1.0", "kind": "forged-review"},
                    logical,
                )
                before = self.fixture._run_inventory()
                with self.assertRaisesRegex(
                    store_module.ProductionStoreError,
                    "PROD_REVIEW_AUTHORITY_REQUIRED",
                ):
                    store_module.ProductionRunStore(self.root).persist_document(
                        forged
                    )
                self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_record_rejects_reviewer_drift_without_write(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
        reviewer = {
            "task_id": "/root/independent-review",
            "thread_id": "THREAD-ASSIGNED",
            "independence_basis": "separate-task-no-producer-context",
        }
        assignment = prod.assign_internal_h1_fragment_fidelity_review(
            context,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            reviewer=reviewer,
            actor="production-orchestrator",
        )
        failure = self._failure_document(
            context,
            ready,
            consumed,
            manifest,
            "reviewer-drift",
            reviewer={**reviewer, "thread_id": "THREAD-FOREIGN"},
        )
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError,
            "PROD_H1_FRAGMENT_FIDELITY_ASSIGNMENT_INVALID",
        ):
            prod.record_internal_h1_fragment_fidelity_failure(
                context,
                assignment=assignment,
                consumed_work_order=consumed,
                fragment_manifest=manifest,
                fidelity_failure=failure,
                actor="novel-conception-presentation-fidelity-reviewer",
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_record_second_write_exception_rolls_back_pair(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
        failure = self._failure_document(
            context, ready, consumed, manifest, "pair-rollback"
        )
        assignment = prod.assign_internal_h1_fragment_fidelity_review(
            context,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            reviewer=failure.data["reviewer"],
            actor="production-orchestrator",
        )
        original = context.store._persist_h1_fidelity_authority_document
        calls = 0

        def fail_second(document):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("second authority write crashed")
            return original(document)

        before = self.fixture._run_inventory()
        with mock.patch.object(
            context.store,
            "_persist_h1_fidelity_authority_document",
            side_effect=fail_second,
        ):
            with self.assertRaisesRegex(RuntimeError, "second authority write"):
                prod.record_internal_h1_fragment_fidelity_failure(
                    context,
                    assignment=assignment,
                    consumed_work_order=consumed,
                    fragment_manifest=manifest,
                    fidelity_failure=failure,
                    actor="novel-conception-presentation-fidelity-reviewer",
                )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_record_postwrite_exception_rolls_back_full_write_set(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
        failure = self._failure_document(
            context, ready, consumed, manifest, "pair-postwrite-rollback"
        )
        assignment = prod.assign_internal_h1_fragment_fidelity_review(
            context,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            reviewer=failure.data["reviewer"],
            actor="production-orchestrator",
        )
        original = context.store._persist_h1_fidelity_authority_document
        calls = 0

        def fail_after_second(document):
            nonlocal calls
            calls += 1
            path = original(document)
            if calls == 2:
                raise RuntimeError("second authority write returned late")
            return path

        before = self.fixture._run_inventory()
        with mock.patch.object(
            context.store,
            "_persist_h1_fidelity_authority_document",
            side_effect=fail_after_second,
        ):
            with self.assertRaisesRegex(RuntimeError, "returned late"):
                prod.record_internal_h1_fragment_fidelity_failure(
                    context,
                    assignment=assignment,
                    consumed_work_order=consumed,
                    fragment_manifest=manifest,
                    fidelity_failure=failure,
                    actor="novel-conception-presentation-fidelity-reviewer",
                )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_record_process_interrupt_recovers_pair_on_resume(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
        failure = self._failure_document(
            context, ready, consumed, manifest, "pair-recovery"
        )
        assignment = prod.assign_internal_h1_fragment_fidelity_review(
            context,
            consumed_work_order=consumed,
            fragment_manifest=manifest,
            reviewer=failure.data["reviewer"],
            actor="production-orchestrator",
        )
        original = context.store._persist_h1_fidelity_authority_document
        calls = 0

        def interrupt_second(document):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt("simulated process loss")
            return original(document)

        with mock.patch.object(
            context.store,
            "_persist_h1_fidelity_authority_document",
            side_effect=interrupt_second,
        ):
            with self.assertRaisesRegex(KeyboardInterrupt, "simulated process"):
                prod.record_internal_h1_fragment_fidelity_failure(
                    context,
                    assignment=assignment,
                    consumed_work_order=consumed,
                    fragment_manifest=manifest,
                    fidelity_failure=failure,
                    actor="novel-conception-presentation-fidelity-reviewer",
                )
        self.assertTrue((self.root / failure.reference["path"]).is_file())
        self.assertFalse(list((
            self.root
            / "orchestration"
            / "h1-fragment-fidelity-review-completions"
        ).glob("*.json")))
        resumed = prod.resume_production_run(self.root)
        completion_path = next((
            self.root
            / "orchestration"
            / "h1-fragment-fidelity-review-completions"
        ).glob("*.json"))
        completion = resumed.store.load_document({
            "path": completion_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(completion_path),
        })
        request = self._request(failure)
        receipt, _, _, _ = prod.apply_internal_h1_fragment_return(
            resumed,
            consumed_work_order=consumed,
            fidelity_failure=failure,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        self.assertEqual(
            "internal_h1_fragment_return", receipt.data["transition_mode"]
        )

    def test_fragment_apply_requires_exact_protected_completion(self):
        context, _planned, ready, consumed, manifest = self._advance_h1()
        failure, completion = self._failure(context, ready, consumed, manifest)
        request = self._request(failure)
        forged = rt.SealedDocument(
            data={**copy.deepcopy(completion.data), "status": "forged"},
            reference=copy.deepcopy(completion.reference),
        )
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError,
            "PROD_H1_FRAGMENT_FIDELITY_AUTHORITY_INVALID",
        ):
            prod.apply_internal_h1_fragment_return(
                context,
                consumed_work_order=consumed,
                fidelity_failure=failure,
                review_completion=forged,
                request=request,
                actor="production-orchestrator",
                inputs={},
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def _returned_fragment_attempt(self):
        context, planned, old_ready, consumed, old_manifest = self._advance_h1()
        failure, completion = self._failure(
            context, old_ready, consumed, old_manifest, "fresh-path"
        )
        request = self._request(failure)
        _, returned, _, replacement = prod.apply_internal_h1_fragment_return(
            context,
            consumed_work_order=consumed,
            fidelity_failure=failure,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        body = copy.deepcopy(old_manifest.data)
        body["files"][0]["sha256"] = "e" * 64
        corrected = rt.seal_document(
            body,
            f"H1/{planned.data['session_id']}/h1-fragments-attempt-02/package-manifest.json",
        )
        returned.store.persist_document(corrected)
        return returned, planned, old_ready, replacement, corrected

    def test_fragment_return_uses_fresh_manifest_bound_successor_and_assemble_binds_it(self):
        returned, planned, old_ready, replacement, corrected = (
            self._returned_fragment_attempt()
        )
        transition = returned.coordinator.accept_h1_workspace_transition(
            current_workspace=planned,
            package_manifest=corrected,
            expected_next_state="fragments_ready",
            active_return_request=returned.active_return,
        )
        fresh = transition.workspace
        self.assertNotEqual(old_ready.reference["path"], fresh.reference["path"])
        self.assertEqual(
            (
                f"H1/{planned.data['session_id']}/workspace-fragments_ready-"
                f"{corrected.reference['sha256'][:24]}.json"
            ),
            fresh.reference["path"],
        )
        replay = returned.coordinator.accept_h1_workspace_transition(
            current_workspace=planned,
            package_manifest=corrected,
            expected_next_state="fragments_ready",
            active_return_request=returned.active_return,
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(fresh, replay.workspace)
        prod._prepare_h1_commit(
            returned,
            replacement,
            bound=planned,
            successor=fresh,
            manifest=corrected,
        )
        returned.store.persist_workspace(fresh)
        returned.store.mark_work_order_consumed(replacement, successor=fresh)
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(fresh.reference, resumed.store.latest_workspace().reference)
        self.assertTrue((self.root / old_ready.reference["path"]).is_file())
        _, assemble = prod.issue_stage_work(
            resumed, action="H1-A-assemble", inputs={}
        )
        self.assertEqual(fresh.reference, assemble.data["h1_workspace"])

    def test_fragment_successor_collision_fails_without_pointer_change(self):
        returned, planned, _, _, corrected = self._returned_fragment_attempt()
        transition = returned.coordinator.accept_h1_workspace_transition(
            current_workspace=planned,
            package_manifest=corrected,
            expected_next_state="fragments_ready",
            active_return_request=returned.active_return,
        )
        collision = self.root / transition.workspace.reference["path"]
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text('{"conflict":true}', encoding="utf-8")
        before = returned.store.latest_workspace().reference
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            returned.store.persist_workspace(transition.workspace)
        self.assertEqual("PROD_IMMUTABLE_CONFLICT", caught.exception.code)
        self.assertEqual(before, returned.store.latest_workspace().reference)

    def test_fragment_orphan_recovery_persists_manifest_bound_successor(self):
        returned, planned, old_ready, replacement, corrected = (
            self._returned_fragment_attempt()
        )
        recovered = prod.recover_h1_workspace(
            returned,
            work_order=replacement,
            actor="novel-conception-fragment-writer",
            current_workspace=planned,
            package_manifest=corrected,
            expected_next_state="fragments_ready",
        )
        self.assertNotEqual(old_ready.reference["path"], recovered.reference["path"])
        self.assertTrue(recovered.reference["path"].endswith(
            f"-{corrected.reference['sha256'][:24]}.json"
        ))
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(recovered.reference, resumed.store.latest_workspace().reference)
        self.assertTrue(
            (
                self.root / "orchestration/work-orders"
                / f"{replacement.data['work_id']}.consumed.json"
            ).is_file()
        )

    def _legacy_fragment_intent(self):
        context, planned, old_ready, consumed, old_manifest = self._advance_h1(
            legacy_fragment_path=True
        )
        failure, completion = self._failure(
            context, old_ready, consumed, old_manifest, "legacy-path"
        )
        request = self._request(failure)
        _, returned, _, replacement = prod.apply_internal_h1_fragment_return(
            context,
            consumed_work_order=consumed,
            fidelity_failure=failure,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        body = copy.deepcopy(old_manifest.data)
        body["files"][0]["sha256"] = "e" * 64
        corrected = rt.seal_document(
            body,
            f"H1/{planned.data['session_id']}/h1-fragments-attempt-02/package-manifest.json",
        )
        returned.store.persist_document(corrected)
        data = {
            **copy.deepcopy(planned.data),
            "state": "fragments_ready",
            "previous_state_sha256": planned.reference["sha256"],
            "artifacts": {
                **copy.deepcopy(planned.data["artifacts"]),
                "fragment_manifest": corrected.reference,
            },
        }
        legacy = rt.seal_document(
            data,
            f"H1/{planned.data['session_id']}/workspace-fragments_ready.json",
        )
        prod._prepare_h1_commit(
            returned,
            replacement,
            bound=planned,
            successor=legacy,
            manifest=corrected,
        )
        return returned, planned, old_ready, replacement, corrected, legacy

    def test_legacy_prepared_fragment_intent_relocates_without_overwrite(self):
        returned, _, old_ready, replacement, corrected, legacy = (
            self._legacy_fragment_intent()
        )
        resumed = prod.resume_production_run(self.root)
        effective = resumed.store.latest_workspace()
        self.assertEqual(legacy.reference["sha256"], effective.reference["sha256"])
        self.assertTrue(effective.reference["path"].endswith(
            f"-{corrected.reference['sha256'][:24]}.json"
        ))
        self.assertEqual(
            old_ready.reference["sha256"],
            rt.sha256_file(self.root / old_ready.reference["path"]),
        )
        receipt_paths = list(
            (self.root / "orchestration/h1-workspace-relocations").glob("*.json")
        )
        self.assertEqual(1, len(receipt_paths))
        receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
        self.assertEqual(legacy.reference, receipt["original_successor"])
        self.assertEqual(effective.reference, receipt["effective_successor"])
        self.assertTrue(
            (
                self.root / "orchestration/work-orders"
                / f"{replacement.data['work_id']}.consumed.json"
            ).is_file()
        )

    def test_legacy_relocation_pointer_gap_replays(self):
        returned, _, _, replacement, _, _ = self._legacy_fragment_intent()
        intent = returned.store._load_commit_intent(replacement)
        effective, receipt = prod._relocate_legacy_h1_fragment_successor(
            returned.store,
            state=returned.state,
            order=replacement,
            intent=intent,
            bound=returned.store.latest_workspace(),
        )
        returned.store.persist_workspace(effective)
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(effective.reference, resumed.store.latest_workspace().reference)
        self.assertTrue((self.root / receipt.reference["path"]).is_file())
        self.assertTrue(
            (
                self.root / "orchestration/work-orders"
                / f"{replacement.data['work_id']}.consumed.json"
            ).is_file()
        )

    def test_fragment_sibling_reference_mutants_fail_before_write(self):
        def replace_session_reference(body, replacement):
            original = body["artifact_roles"]["generation_session"]
            body["artifact_roles"]["generation_session"] = replacement
            body["files"] = [
                replacement if item == original else item for item in body["files"]
            ]

        def wrong_hash(body):
            reference = dict(body["artifact_roles"]["generation_session"])
            reference["sha256"] = "b" * 64
            replace_session_reference(body, reference)

        def wrong_path(body):
            reference = dict(body["artifact_roles"]["generation_session"])
            reference["path"] = "missing-generation-session.json"
            replace_session_reference(body, reference)

        def backslash(body):
            reference = dict(body["artifact_roles"]["generation_session"])
            reference["path"] = "generation\\session.json"
            replace_session_reference(body, reference)

        def parent_mismatch(body):
            reference = dict(body["artifact_roles"]["generation_session"])
            reference["path"] = "H1/H1-FOREIGN/h1-fragments/generation-session.json"
            replace_session_reference(body, reference)

        def noncanonical_json(body):
            path = (
                self.root / "H1/H1-RETURN/h1-fragments/generation-session.json"
            )
            path.write_text(
                json.dumps(
                    {"schema_version": "1.0", "kind": "generation-session"},
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            reference = dict(body["artifact_roles"]["generation_session"])
            reference["sha256"] = rt.sha256_file(path)
            replace_session_reference(body, reference)

        def implementation_wrong_hash(body):
            original = body["implementation"][-1]
            replacement = {**original, "sha256": "c" * 64}
            body["implementation"][-1] = replacement
            body["files"] = [
                replacement if item == original else item for item in body["files"]
            ]

        cases = {
            "wrong-hash": wrong_hash,
            "wrong-path": wrong_path,
            "backslash": backslash,
            "parent-mismatch": parent_mismatch,
            "raw-canonical-mismatch": noncanonical_json,
            "implementation-raw-hash": implementation_wrong_hash,
        }
        for index, (name, mutator) in enumerate(cases.items()):
            with self.subTest(case=name):
                if index:
                    self.fixture.tearDown()
                    self.fixture = fixtures.ProductionOrchestratorTests(
                        methodName="runTest"
                    )
                    self.fixture.setUp()
                    self.root = self.fixture.root
                context, _, ready, consumed, manifest = self._advance_h1(
                    fragment_manifest_mutator=mutator
                )
                before = self.fixture._run_inventory()
                with self.assertRaises(prod.ProductionOrchestratorError) as caught:
                    prod.assign_internal_h1_fragment_fidelity_review(
                        context,
                        consumed_work_order=consumed,
                        fragment_manifest=manifest,
                        reviewer={
                            "task_id": "/root/independent-review",
                            "thread_id": f"THREAD-{name}",
                            "independence_basis": "separate-task-no-producer-context",
                        },
                        actor="production-orchestrator",
                    )
                self.assertEqual(
                    "PROD_H1_FRAGMENT_PACKAGE_INVALID", caught.exception.code
                )
                self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_sibling_escape_rejected_without_write(self):
        context, _, _, _, manifest = self._advance_h1()
        manifest_path = context.store.resolve_document_path(manifest.reference)
        before = self.fixture._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod._resolve_internal_h1_fragment_sibling(
                context.store,
                package_root=manifest_path.parent,
                logical_package_root=PurePosixPath(
                    manifest.reference["path"]
                ).parent,
                reference={"path": "../generation-session.json", "sha256": "a" * 64},
            )
        self.assertEqual("PROD_H1_FRAGMENT_PACKAGE_INVALID", caught.exception.code)
        self.assertEqual(before, self.fixture._run_inventory())

    def test_fragment_p1_binding_mutants_fail_before_write(self):
        def wrong_stage(body):
            body["p1_completion"]["stage"] = "P2"

        def wrong_path(body):
            body["p1_completion"]["path"] = "P1/foreign-stage-completion.json"

        def wrong_hash(body):
            body["p1_completion"]["sha256"] = "d" * 64

        def extra_field(body):
            body["p1_completion"]["unexpected"] = True

        for index, (name, mutator) in enumerate({
            "wrong-stage": wrong_stage,
            "wrong-path": wrong_path,
            "wrong-hash": wrong_hash,
            "extra-field": extra_field,
        }.items()):
            with self.subTest(case=name):
                if index:
                    self.fixture.tearDown()
                    self.fixture = fixtures.ProductionOrchestratorTests(
                        methodName="runTest"
                    )
                    self.fixture.setUp()
                    self.root = self.fixture.root
                context, _, ready, consumed, manifest = self._advance_h1(
                    fragment_package_mutator=mutator
                )
                before = self.fixture._run_inventory()
                with self.assertRaises(prod.ProductionOrchestratorError) as caught:
                    prod.assign_internal_h1_fragment_fidelity_review(
                        context,
                        consumed_work_order=consumed,
                        fragment_manifest=manifest,
                        reviewer={
                            "task_id": "/root/independent-review",
                            "thread_id": f"THREAD-{name}",
                            "independence_basis": "separate-task-no-producer-context",
                        },
                        actor="production-orchestrator",
                    )
                self.assertEqual(
                    "PROD_H1_FRAGMENT_PACKAGE_INVALID", caught.exception.code
                )
                self.assertEqual(before, self.fixture._run_inventory())

    def test_wrong_actor_route_state_and_collision_are_zero_write(self):
        context, _, ready, consumed, manifest = self._advance_h1()
        failure, completion = self._failure(context, ready, consumed, manifest)
        request = self._request(failure)
        cases = [
            {"actor": "novel-conception-fragment-writer", "request": request},
            {
                "actor": "production-orchestrator",
                "request": rt.seal_document(
                    {**request.data, "resume_point": "H1-A-assemble"},
                    "returns/RET-WRONG/return-request.json",
                ),
            },
        ]
        for values in cases:
            before = self.fixture._run_inventory()
            with self.assertRaises(prod.ProductionOrchestratorError):
                prod.apply_internal_h1_fragment_return(
                    context,
                    consumed_work_order=consumed,
                    fidelity_failure=failure,
                    review_completion=completion,
                    request=values["request"],
                    actor=values["actor"],
                    inputs={},
                )
            self.assertEqual(before, self.fixture._run_inventory())

        collision = self.root / request.reference["path"]
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text(rt.canonical_json({"conflict": True}), encoding="utf-8")
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            (prod.ProductionOrchestratorError, store_module.ProductionStoreError),
            "PROD_",
        ):
            prod.apply_internal_h1_fragment_return(
                context,
                consumed_work_order=consumed,
                fidelity_failure=failure,
                review_completion=completion,
                request=request,
                actor="production-orchestrator",
                inputs={},
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_pending_assemble_is_rejected_in_same_transaction(self):
        context, _, ready, consumed, manifest = self._advance_h1()
        _, downstream = prod.issue_stage_work(
            context, action="H1-A-assemble", inputs={}
        )
        failure, completion = self._failure(
            context, ready, consumed, manifest, "downstream"
        )
        request = self._request(failure)
        _, returned, _, replacement = prod.apply_internal_h1_fragment_return(
            context,
            consumed_work_order=consumed,
            fidelity_failure=failure,
            review_completion=completion,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        self.assertTrue(
            (
                self.root / "orchestration/work-orders"
                / f"{downstream.data['work_id']}.rejected.json"
            ).is_file()
        )
        self.assertEqual(
            replacement.reference, returned.store.pending_work_order().reference
        )

    def test_prepared_and_complete_pointer_gap_recover(self):
        for boundary in ("prepared", "mid", "complete"):
            with self.subTest(boundary=boundary):
                if boundary != "prepared":
                    self.fixture.tearDown()
                    self.fixture = fixtures.ProductionOrchestratorTests(
                        methodName="runTest"
                    )
                    self.fixture.setUp()
                    self.root = self.fixture.root
                context, planned, ready, consumed, manifest = self._advance_h1()
                failure, completion = self._failure(
                    context, ready, consumed, manifest, boundary
                )
                request = self._request(failure)
                with mock.patch.object(
                    context.store,
                    "persist_state",
                    side_effect=RuntimeError("prepared crash"),
                ):
                    with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                        prod.apply_internal_h1_fragment_return(
                            context,
                            consumed_work_order=consumed,
                            fidelity_failure=failure,
                            review_completion=completion,
                            request=request,
                            actor="production-orchestrator",
                            inputs={},
                        )
                plan_path = next(
                    path for path in (
                        self.root / "orchestration/contract-upgrades"
                    ).glob("*.prepared.json")
                    if not path.with_name(
                        path.name.replace(".prepared.json", ".complete.json")
                    ).exists()
                )
                plan = context.store.load_document({
                    "path": plan_path.relative_to(self.root).as_posix(),
                    "sha256": rt.sha256_file(plan_path),
                })
                successor = rt.SealedDocument(
                    copy.deepcopy(plan.data["successor_snapshot"]),
                    dict(plan.data["successor_state"]),
                )
                if boundary in {"mid", "complete"}:
                    context.store.persist_state(successor)
                    receipt, derived = context.store.build_contract_upgrade_completion(
                        plan, successor=successor
                    )
                    selected = (
                        derived[: max(1, len(derived) // 2)]
                        if boundary == "mid"
                        else derived
                    )
                    for document in selected:
                        context.store.persist_document(document)
                    if boundary == "complete":
                        context.store.persist_document(receipt)
                resumed = prod.resume_production_run(self.root)
                self.assertEqual(successor.reference, resumed.state.reference)
                self.assertEqual(planned.reference, resumed.store.latest_workspace().reference)
                self.assertEqual(request.reference, resumed.active_return.reference)


if __name__ == "__main__":
    unittest.main()
