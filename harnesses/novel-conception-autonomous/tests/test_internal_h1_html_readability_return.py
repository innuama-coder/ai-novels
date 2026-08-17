from __future__ import annotations

import copy
import importlib
import json
import unittest
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
fixtures = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)
readability_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_internal_h1_readability_return"
)
readability = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_readability"
)
production_coordinator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_coordinator"
)


class InternalH1HtmlReadabilityReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        self.readability_fixture = readability_tests.InternalH1ReadabilityReturnTests(
            methodName="runTest"
        )
        self.readability_fixture.fixture = self.fixture
        self.readability_fixture.root = self.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _active_rendered(self):
        context, _legacy, _completion, _h1_manifest, prepublish = (
            self.readability_fixture._waiting_author()
        )
        old_body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-H1-PLAN-OLD",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_plan",
            problem="Earlier broad H1 review return.",
            evidence_ids=["OLD-READABILITY-FAILURE"],
            violated_contract="Author-facing output must be readable.",
            required_revision="Rebuild H1 from the plan.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        old = rt.seal_document(
            old_body, f"returns/{old_body['return_id']}/return-request.json"
        )
        transition = context.coordinator.apply_return_request(
            request=old,
            next_state_path="state/revision-010.json",
        )
        revised = rt.SealedDocument(transition.snapshot, transition.reference)
        context.store.persist_document(old)
        context.store.persist_state(revised)

        artifacts = copy.deepcopy(_legacy.data["artifacts"])
        session_id = "H1-HTML-READABILITY-OLD"
        assembled = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": session_id,
                "state": "assembled",
                "p1_completion": revised.data["current_stage_completions"]["P1"],
                "previous_state_sha256": "2" * 64,
                "artifacts": {
                    "plan_manifest": artifacts["plan_manifest"],
                    "fragment_manifest": artifacts["fragment_manifest"],
                    "assembly_manifest": artifacts["assembly_manifest"],
                },
            },
            f"H1/{session_id}/workspace-assembled.json",
        )
        rendered = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": session_id,
                "state": "rendered",
                "p1_completion": revised.data["current_stage_completions"]["P1"],
                "previous_state_sha256": assembled.reference["sha256"],
                "artifacts": artifacts,
            },
            f"H1/{session_id}/workspace-rendered.json",
        )
        context.store.persist_workspace(assembled)
        context.store.persist_workspace(rendered)
        coordinator = production_coordinator.ProductionCoordinator.from_snapshot(
            revised.data,
            revised.reference,
            active_return_request=old,
            runtime=context.store.runtime,
        )
        current = prod.ProductionContext(context.store, coordinator, revised, old)
        return current, old, assembled, rendered, prepublish

    def _failure_and_request(self, *, prepublish, suffix="001"):
        dimensions = [
            {"id": name, "verdict": "pass", "finding": "independently checked"}
            for name in readability.DIMENSIONS
        ]
        dimensions[-1]["verdict"] = "fail"
        failure = readability.seal_review(
            {
                "schema_version": "1.0",
                "review_id": f"H1-READABILITY-HTML-FAIL-{suffix}",
                "run_id": "RUN-PROD-1",
                "session_id": "H1-HTML-READABILITY-OLD",
                "phase": "prepublish",
                "reviewer": {
                    "task_id": "independent-html-reviewer",
                    "thread_id": "independent-html-thread",
                    "independence_basis": "separate-task-no-producer-context",
                },
                "inputs": prepublish,
                "dimensions": dimensions,
                "findings": [
                    {
                        "finding_id": f"H1-READABILITY-FINDING-HTML-{suffix}",
                        "dimension": "excludes_internal_ids_and_audit_jargon",
                        "artifact_kind": "report",
                        "artifact_id": "human-review-report",
                        "evidence": "审计规格",
                        "explanation": "The rendered page exposes internal review wording.",
                    }
                ],
                "verdict": "fail",
            }
        )
        body = rt.route_return(
            run_id="RUN-PROD-1",
            return_id=f"RET-H1-HTML-READABILITY-{suffix}",
            origin_kind="stage",
            origin_stage="H1",
            issue_kind="h1_html",
            problem="Independent reviewer rejected the rendered reader surface.",
            evidence_ids=[failure.data["review_id"]],
            violated_contract="The HTML must be natural author-facing Chinese.",
            required_revision="Regenerate only H1-C from the accepted assembly.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        return failure, rt.seal_document(
            body, f"returns/{body['return_id']}/return-request.json"
        )

    @staticmethod
    def _producer_identities():
        return [{"task_id": "plan-producer", "thread_id": "plan-thread"}]

    def _html_manifest(self, context, assembled, *, attempt="attempt-02"):
        artifact = lambda path, digest: {"path": path, "sha256": digest}
        data = {
            "schema_version": "2.0",
            "run_id": assembled.data["run_id"],
            "stage": "H1",
            "package_profile": "h1-html",
            "verdict": "ready",
            "session_id": assembled.data["session_id"],
            "parent_state_sha256": assembled.reference["sha256"],
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
        manifest = rt.SealedDocument(
            data=data,
            reference={
                "path": f"H1/html-{attempt}/package-manifest.json",
                "sha256": rt.canonical_sha256(data),
            },
        )
        context.store.persist_document(manifest)
        return manifest

    def _legacy_html_intent(self):
        _context, _old, assembled, old_rendered, _failure, _request, result = (
            self._apply()
        )
        _receipt, returned, restored, _gate, order = result
        self.assertEqual(assembled, restored)
        manifest = self._html_manifest(returned, assembled)
        data = {
            **copy.deepcopy(assembled.data),
            "state": "rendered",
            "previous_state_sha256": assembled.reference["sha256"],
            "artifacts": {
                **copy.deepcopy(assembled.data["artifacts"]),
                "html_manifest": manifest.reference,
            },
        }
        legacy = rt.seal_document(
            data,
            f"H1/{assembled.data['session_id']}/workspace-rendered.json",
        )
        prod._prepare_h1_commit(
            returned,
            order,
            bound=assembled,
            successor=legacy,
            manifest=manifest,
        )
        return returned, assembled, old_rendered, order, manifest, legacy

    def _apply(self, *, complete_side_effect=None):
        context, old, assembled, rendered, prepublish = self._active_rendered()
        failure, request = self._failure_and_request(prepublish=prepublish)
        patches = [
            mock.patch.object(
                prod,
                "h1_readability_prepublish_contract",
                return_value=(prepublish, self._producer_identities()),
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
                result = prod.apply_internal_h1_html_readability_return(
                    context,
                    readability_failure=failure,
                    request=request,
                    actor="production-orchestrator",
                )
            else:
                with patches[1]:
                    result = prod.apply_internal_h1_html_readability_return(
                        context,
                        readability_failure=failure,
                        request=request,
                        actor="production-orchestrator",
                    )
        return context, old, assembled, rendered, failure, request, result

    def test_success_preserves_accepted_h1_prefix_and_reissues_h1_c(self):
        _context, old, assembled, rendered, failure, request, result = self._apply()
        receipt, returned, restored, gate, order = result
        self.assertEqual("complete", receipt.data["status"])
        self.assertEqual(old.reference, receipt.data["superseded_return"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual("revise", returned.state.data["status"])
        self.assertEqual(assembled.reference, restored.reference)
        self.assertEqual("H1-C", order.data["action"])
        self.assertEqual(assembled.reference, order.data["h1_workspace"])
        self.assertEqual({"assembly_package": str(self.root / "H1" / "assembly")}, order.data["inputs"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        replay = prod.resume_production_run(self.root)
        self.assertEqual(returned.state.reference, replay.state.reference)
        self.assertEqual(order.reference, replay.store.pending_work_order().reference)
        self.assertEqual(assembled.reference, replay.store.latest_workspace().reference)
        markers = list((self.root / "orchestration" / "h1-artifact-invalidations").glob("*.json"))
        marker_value = json.loads(markers[-1].read_text(encoding="utf-8"))
        self.assertEqual(rendered.reference, marker_value["h1_workspace"])
        self.assertEqual(failure.reference, marker_value["fidelity_failure"])
        self.assertEqual(assembled.reference, marker_value["restored_workspace"])

    def test_completed_h1_c_retry_can_refresh_with_new_failure(self):
        _context, _old, assembled, rendered, first_failure, first_request, result = (
            self._apply()
        )
        _receipt, returned, _restored, _gate, first_order = result
        retried_rendered = rt.seal_document(
            copy.deepcopy(rendered.data),
            (
                f"H1/{rendered.data['session_id']}/"
                "workspace-rendered-retry.json"
            ),
        )
        returned.store.persist_workspace(retried_rendered)
        current_order = returned.store.root / "orchestration/current-work-order.json"
        if current_order.exists():
            current_order.unlink()
        refreshed_coordinator = production_coordinator.ProductionCoordinator.from_snapshot(
            returned.state.data,
            returned.state.reference,
            active_return_request=first_request,
            runtime=returned.store.runtime,
        )
        current = prod.ProductionContext(
            returned.store,
            refreshed_coordinator,
            returned.state,
            first_request,
        )
        prepublish = copy.deepcopy(first_failure.data["inputs"])
        failure, request = self._failure_and_request(
            prepublish=prepublish, suffix="002"
        )
        with mock.patch.object(
            prod,
            "h1_readability_prepublish_contract",
            return_value=(prepublish, self._producer_identities()),
        ):
            receipt, refreshed, restored, _gate, order = (
                prod.apply_internal_h1_html_readability_return(
                    current,
                    readability_failure=failure,
                    request=request,
                    actor="production-orchestrator",
                )
            )

        self.assertEqual(first_request.reference, receipt.data["superseded_return"])
        self.assertEqual(request.reference, refreshed.active_return.reference)
        self.assertEqual(assembled.reference, restored.reference)
        self.assertEqual("H1-C", order.data["action"])
        self.assertNotEqual(first_order.reference, order.reference)

    def test_future_rendered_successor_is_manifest_qualified(self):
        _context, _old, assembled, _rendered, _failure, _request, result = self._apply()
        _receipt, returned, _restored, _gate, _order = result
        manifest = self._html_manifest(returned, assembled, attempt="future")
        transition = returned.coordinator.accept_h1_workspace_transition(
            current_workspace=assembled,
            package_manifest=manifest,
            expected_next_state="rendered",
            active_return_request=returned.active_return,
        )
        self.assertEqual(
            (
                f"H1/{assembled.data['session_id']}/workspace-rendered-"
                f"{manifest.reference['sha256'][:24]}.json"
            ),
            transition.workspace.reference["path"],
        )
        replay = returned.coordinator.accept_h1_workspace_transition(
            current_workspace=assembled,
            package_manifest=manifest,
            expected_next_state="rendered",
            active_return_request=returned.active_return,
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(transition.workspace, replay.workspace)

    def test_legacy_prepared_html_intent_relocates_without_overwrite(self):
        returned, _assembled, old_rendered, order, manifest, legacy = (
            self._legacy_html_intent()
        )
        resumed = prod.resume_production_run(self.root)
        effective = resumed.store.latest_workspace()
        self.assertEqual(legacy.reference["sha256"], effective.reference["sha256"])
        self.assertEqual(
            (
                f"H1/{effective.data['session_id']}/workspace-rendered-"
                f"{manifest.reference['sha256'][:24]}.json"
            ),
            effective.reference["path"],
        )
        self.assertEqual(
            old_rendered.reference["sha256"],
            rt.sha256_file(self.root / old_rendered.reference["path"]),
        )
        receipts = list(
            (self.root / "orchestration/h1-workspace-relocations").glob("*.json")
        )
        self.assertEqual(1, len(receipts))
        value = json.loads(receipts[0].read_text(encoding="utf-8"))
        self.assertEqual("h1-rendered-manifest-sha256-prefix-v1", value["algorithm"])
        self.assertEqual(legacy.reference, value["original_successor"])
        self.assertEqual(effective.reference, value["effective_successor"])
        self.assertTrue(
            (
                self.root / "orchestration/work-orders"
                / f"{order.data['work_id']}.consumed.json"
            ).is_file()
        )

    def test_legacy_html_relocation_pointer_gap_replays(self):
        returned, _assembled, _old_rendered, order, _manifest, _legacy = (
            self._legacy_html_intent()
        )
        intent = returned.store._load_commit_intent(order)
        effective, receipt = prod._relocate_legacy_h1_successor(
            returned.store,
            state=returned.state,
            order=order,
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
                / f"{order.data['work_id']}.consumed.json"
            ).is_file()
        )

    def test_legacy_html_effective_collision_keeps_assembled_pointer(self):
        returned, assembled, _old_rendered, order, manifest, _legacy = (
            self._legacy_html_intent()
        )
        path = (
            self.root / f"H1/{assembled.data['session_id']}/workspace-rendered-"
            f"{manifest.reference['sha256'][:24]}.json"
        )
        path.write_text('{"collision":true}', encoding="utf-8")
        with self.assertRaises(rt.ProductionStoreError) as caught:
            prod.resume_production_run(self.root)
        self.assertEqual("PROD_IMMUTABLE_CONFLICT", caught.exception.code)
        self.assertEqual(assembled.reference, returned.store.latest_workspace().reference)
        self.assertFalse(
            (
                self.root / "orchestration/work-orders"
                / f"{order.data['work_id']}.consumed.json"
            ).exists()
        )

    def test_forged_relocation_collision_and_path_cannot_be_consumed(self):
        returned, _assembled, _old_rendered, order, _manifest, _legacy = (
            self._legacy_html_intent()
        )
        intent = returned.store._load_commit_intent(order)
        effective, receipt = prod._relocate_legacy_h1_successor(
            returned.store,
            state=returned.state,
            order=order,
            intent=intent,
            bound=returned.store.latest_workspace(),
        )
        returned.store.persist_workspace(effective)
        forged_data = copy.deepcopy(receipt.data)
        forged_data["collision"]["sha256"] = "f" * 64
        forged = rt.SealedDocument(
            data=forged_data,
            reference={
                "path": (
                    "orchestration/h1-workspace-relocations/"
                    "forged-collision-binding.json"
                ),
                "sha256": rt.canonical_sha256(forged_data),
            },
        )
        returned.store.persist_document(forged)
        with self.assertRaises(rt.ProductionStoreError) as caught:
            returned.store.mark_work_order_consumed(
                order,
                successor=effective,
                successor_relocation=forged,
            )
        self.assertEqual("PROD_COMMIT_INTENT_MISSING", caught.exception.code)
        self.assertFalse(
            (
                self.root / "orchestration/work-orders"
                / f"{order.data['work_id']}.consumed.json"
            ).exists()
        )

    def test_nonexact_supersession_marker_cannot_authorize_consumption(self):
        returned, _assembled, _old_rendered, order, _manifest, _legacy = (
            self._legacy_html_intent()
        )
        intent = returned.store._load_commit_intent(order)
        effective, receipt = prod._relocate_legacy_h1_successor(
            returned.store,
            state=returned.state,
            order=order,
            intent=intent,
            bound=returned.store.latest_workspace(),
        )
        marker_paths = list(
            (self.root / "orchestration/h1-artifact-invalidations").glob("*.json")
        )
        self.assertEqual(1, len(marker_paths))
        marker_body = json.loads(marker_paths[0].read_text(encoding="utf-8"))
        marker_body["untrusted_extra_field"] = True
        marker_paths[0].write_text(
            rt.canonical_json(marker_body), encoding="utf-8", newline=""
        )
        returned.store.persist_workspace(effective)
        returned.store.persist_document(receipt)
        with self.assertRaises(rt.ProductionStoreError) as caught:
            returned.store.mark_work_order_consumed(
                order,
                successor=effective,
                successor_relocation=receipt,
            )
        self.assertEqual("PROD_COMMIT_INTENT_MISSING", caught.exception.code)
        self.assertFalse(
            (
                self.root / "orchestration/work-orders"
                / f"{order.data['work_id']}.consumed.json"
            ).exists()
        )

    def test_wrong_actor_and_route_fail_before_state_write(self):
        context, _old, _assembled, _rendered, prepublish = self._active_rendered()
        failure, request = self._failure_and_request(prepublish=prepublish)
        before = context.store.latest_state()
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.apply_internal_h1_html_readability_return(
                context,
                readability_failure=failure,
                request=request,
                actor="novel-conception-review-html-generator",
            )
        self.assertEqual(before, context.store.latest_state())

        wrong = copy.deepcopy(request.data)
        wrong["resume_point"] = "H1-A-assemble"
        forged = rt.seal_document(
            wrong, "returns/RET-H1-HTML-WRONG/return-request.json"
        )
        with (
            mock.patch.object(
                prod,
                "h1_readability_prepublish_contract",
                return_value=(prepublish, self._producer_identities()),
            ),
            self.assertRaises(prod.ProductionOrchestratorError),
        ):
            prod.apply_internal_h1_html_readability_return(
                context,
                readability_failure=failure,
                request=forged,
                actor="production-orchestrator",
            )
        self.assertEqual(before, context.store.latest_state())

    def test_complete_receipt_repairs_workspace_and_order_pointer_gap(self):
        _context, _old, assembled, rendered, failure, request, result = self._apply()
        receipt, returned, _restored, _gate, order = result
        returned.store._replace(
            returned.store.root / "orchestration" / "current-h1-workspace.json",
            {"schema_version": "2.0", "workspace": rendered.reference},
        )
        (returned.store.root / "orchestration" / "current-work-order.json").unlink()
        returned.store._replace(
            returned.store.root
            / "orchestration"
            / "current-contract-upgrade.json",
            {
                "schema_version": "1.0",
                "receipt": receipt.data["prior_qualification"],
            },
        )
        with mock.patch.object(
            prod,
            "h1_readability_prepublish_contract",
            return_value=(failure.data["inputs"], self._producer_identities()),
        ):
            replay = prod.resume_production_run(self.root)
        self.assertEqual(request.reference, replay.active_return.reference)
        self.assertEqual(assembled.reference, replay.store.latest_workspace().reference)
        self.assertEqual(order.reference, replay.store.pending_work_order().reference)

    def test_prepared_and_mid_derived_recovery(self):
        for mode in ("prepared", "mid-derived"):
            with self.subTest(mode=mode):
                captured = {}

                def interrupt(plan, *, successor):
                    captured["plan"] = plan
                    if mode == "mid-derived":
                        _receipt, derived = context.store.build_contract_upgrade_completion(
                            plan, successor=successor
                        )
                        context.store.persist_document(derived[0])
                    raise RuntimeError("simulated crash")

                context, _old, assembled, _rendered, prepublish = self._active_rendered()
                failure, request = self._failure_and_request(prepublish=prepublish)
                with (
                    mock.patch.object(
                        prod,
                        "h1_readability_prepublish_contract",
                        return_value=(prepublish, self._producer_identities()),
                    ),
                    mock.patch.object(
                        context.store,
                        "complete_contract_upgrade",
                        side_effect=interrupt,
                    ),
                    self.assertRaisesRegex(RuntimeError, "simulated crash"),
                ):
                    prod.apply_internal_h1_html_readability_return(
                        context,
                        readability_failure=failure,
                        request=request,
                        actor="production-orchestrator",
                    )
                with mock.patch.object(
                    prod,
                    "h1_readability_prepublish_contract",
                    return_value=(prepublish, self._producer_identities()),
                ):
                    resumed = prod.resume_production_run(self.root)
                self.assertEqual(request.reference, resumed.active_return.reference)
                self.assertEqual("H1-C", resumed.store.pending_work_order().data["action"])
                self.assertEqual(assembled.reference, resumed.store.latest_workspace().reference)
                self.fixture.tearDown()
                self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
                self.fixture.setUp()
                self.root = self.fixture.root
                self.readability_fixture.fixture = self.fixture
                self.readability_fixture.root = self.root


if __name__ == "__main__":
    unittest.main()
