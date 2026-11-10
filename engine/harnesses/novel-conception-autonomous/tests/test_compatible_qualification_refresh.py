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
import unittest
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
plan_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_internal_h1_plan_return"
)


class CompatibleQualificationRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = plan_tests.InternalH1PlanReturnTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _active_fragments_ready_full(self):
        context, _planned, ready, _assemble = (
            self.fixture._ready_with_pending_assemble()
        )
        candidate, failure, review_completion = self.fixture._candidate_and_failure(
            context, ready
        )
        request = self.fixture._request(failure)
        _receipt, returned, initialized, _gate, plan_order = (
            prod.apply_internal_h1_plan_return(
                context,
                fidelity_failure=failure,
                candidate_report=candidate,
                review_completion=review_completion,
                request=request,
                actor="production-orchestrator",
            )
        )
        helper, planned, current, fragment_order, fragment_manifest = (
            self.fixture._advance_returned_h1(returned, initialized, plan_order)
        )
        _, assemble = prod.issue_stage_work(
            returned, action="H1-A-assemble", inputs={}
        )
        return (
            returned,
            current,
            assemble,
            helper,
            planned,
            fragment_order,
            fragment_manifest,
        )

    def _active_fragments_ready(self):
        context, current, assemble, *_material = self._active_fragments_ready_full()
        return context, current, assemble

    def _migration(self, context, *, current_sha="a" * 64):
        completion = context.state.data["current_stage_completions"]["E1"]
        identity = prod._completion_contract_identity(context.store, completion)
        old_contract = copy.deepcopy(prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT)
        old_sha = old_contract["E1"]["identity_bindings"]["runtime"]["sha256"]
        current_contract = copy.deepcopy(old_contract)
        current_contract["E1"]["identity_bindings"]["runtime"]["sha256"] = (
            current_sha
        )
        authority = copy.deepcopy(prod.TRUSTED_LEGACY_CATALOGS)
        authority["E1"] = {
            "canonical_digest": identity["implementation_catalog_sha256"],
            "removed_identities": frozenset(),
            "approved_mismatches": {
                old_contract["E1"]["identity_bindings"]["runtime"]["identity"]: (
                    old_sha,
                    current_sha,
                )
            },
        }
        public = [
            {
                "stage": stage,
                "completion": copy.deepcopy(
                    context.state.data["current_stage_completions"][stage]
                ),
                "validation_sha256": str(index + 1) * 64,
            }
            for index, stage in enumerate(rt.STAGE_ORDER[:-1])
        ]
        return (
            current_contract,
            rt.canonical_sha256(current_contract),
            authority,
            public,
        )

    def _patches(self, migration):
        contract, digest, authority, public = migration
        return (
            mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
            ),
            mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
            ),
            mock.patch.object(prod, "TRUSTED_LEGACY_CATALOGS", authority),
            mock.patch.object(
                prod,
                "_validate_public_completion_chain",
                return_value=(public, None),
            ),
        )

    def test_refresh_preserves_packages_and_workspace_and_reissues_same_h1_action(self):
        context, workspace, pending = self._active_fragments_ready()
        migration = self._migration(context)
        completions = copy.deepcopy(context.state.data["current_stage_completions"])
        state_semantics = {
            key: copy.deepcopy(value)
            for key, value in context.state.data.items()
            if key not in {"revision", "previous_state"}
        }
        workspace_bytes = (self.root / workspace.reference["path"]).read_bytes()
        patches = self._patches(migration)
        with patches[0], patches[1], patches[2], patches[3]:
            target, evidence = prod._actual_contract_upgrade_target(
                context.store,
                context.state,
                context.store.current_contract_upgrade(),
            )
            self.assertEqual("H1", target)
            self.assertEqual(
                "migration-approved-compatible-qualification-refresh",
                evidence["classification"],
            )
            receipt, refreshed, gate, order = (
                prod.apply_compatible_qualification_refresh(
                    context, actor="production-orchestrator"
                )
            )
            resumed = prod.resume_production_run(self.root)

        self.assertEqual("compatible_qualification_refresh", receipt.data["transition_mode"])
        self.assertEqual([], receipt.data["invalidated_stages"])
        self.assertEqual(completions, refreshed.state.data["current_stage_completions"])
        self.assertEqual(
            state_semantics,
            {
                key: value
                for key, value in refreshed.state.data.items()
                if key not in {"revision", "previous_state"}
            },
        )
        self.assertEqual(workspace.reference, order.data["h1_workspace"])
        self.assertEqual(workspace.reference, resumed.store.latest_workspace().reference)
        self.assertEqual(
            workspace_bytes, (self.root / workspace.reference["path"]).read_bytes()
        )
        self.assertEqual(pending.data["action"], order.data["action"])
        self.assertEqual(pending.data["inputs"], order.data["inputs"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        self.assertTrue(
            (
                self.root
                / "orchestration/work-orders"
                / f"{pending.data['work_id']}.rejected.json"
            ).is_file()
        )

    def test_refresh_rebases_consumed_fragment_material_for_fresh_local_return(self):
        (
            context,
            workspace,
            _pending,
            helper,
            planned,
            consumed_fragment_order,
            fragment_manifest,
        ) = self._active_fragments_ready_full()
        migration = self._migration(context)
        patches = self._patches(migration)
        with patches[0], patches[1], patches[2], patches[3]:
            _receipt, refreshed, _gate, assemble = (
                prod.apply_compatible_qualification_refresh(
                    context, actor="production-orchestrator"
                )
            )
            failure = helper._failure_document(
                refreshed,
                workspace,
                consumed_fragment_order,
                fragment_manifest,
                marker="compatible-refresh",
            )
            assignment = prod.assign_internal_h1_fragment_fidelity_review(
                refreshed,
                consumed_work_order=consumed_fragment_order,
                fragment_manifest=fragment_manifest,
                reviewer=failure.data["reviewer"],
                actor="production-orchestrator",
            )
            review_completion = prod.record_internal_h1_fragment_fidelity_failure(
                refreshed,
                assignment=assignment,
                consumed_work_order=consumed_fragment_order,
                fragment_manifest=fragment_manifest,
                fidelity_failure=failure,
                actor="novel-conception-presentation-fidelity-reviewer",
            )
            request = helper._request(failure)
            receipt, returned, gate, order = prod.apply_internal_h1_fragment_return(
                refreshed,
                consumed_work_order=consumed_fragment_order,
                fidelity_failure=failure,
                review_completion=review_completion,
                request=request,
                actor="production-orchestrator",
                inputs={},
            )
            resumed = prod.resume_production_run(self.root)

        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual("H1-B", order.data["action"])
        self.assertEqual(planned.reference, order.data["h1_workspace"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        self.assertTrue(
            (
                self.root
                / "orchestration/work-orders"
                / f"{assemble.data['work_id']}.rejected.json"
            ).is_file()
        )

    def test_refresh_does_not_erase_active_return_reviewer_freshness(self):
        (
            context,
            workspace,
            _pending,
            helper,
            _planned,
            consumed_fragment_order,
            fragment_manifest,
        ) = self._active_fragments_ready_full()
        migration = self._migration(context)
        patches = self._patches(migration)
        with patches[0], patches[1], patches[2], patches[3]:
            _receipt, refreshed, _gate, _assemble = (
                prod.apply_compatible_qualification_refresh(
                    context, actor="production-orchestrator"
                )
            )
            reused = {
                "task_id": "/root/fresh-fidelity-review-001",
                "thread_id": "THREAD-001",
                "independence_basis": "separate-task-no-producer-context",
            }
            failure = helper._failure_document(
                refreshed,
                workspace,
                consumed_fragment_order,
                fragment_manifest,
                marker="compatible-reused-reviewer",
                reviewer=reused,
            )
            before = self.fixture.fixture._run_inventory()
            with self.assertRaisesRegex(
                prod.ProductionOrchestratorError,
                "PROD_H1_FRAGMENT_FIDELITY_REVIEW_NOT_INDEPENDENT",
            ):
                prod.assign_internal_h1_fragment_fidelity_review(
                    refreshed,
                    consumed_work_order=consumed_fragment_order,
                    fragment_manifest=fragment_manifest,
                    reviewer=failure.data["reviewer"],
                    actor="production-orchestrator",
                )
        self.assertEqual(before, self.fixture.fixture._run_inventory())

    def test_schema_protocol_unapproved_code_and_public_failure_remain_real_targets(self):
        variants = ("schema", "protocol", "unapproved", "public")
        for variant in variants:
            with self.subTest(variant=variant):
                if variant != "schema":
                    self.fixture.tearDown()
                    self.fixture = plan_tests.InternalH1PlanReturnTests(
                        methodName="runTest"
                    )
                    self.fixture.setUp()
                    self.root = self.fixture.root
                context, _workspace, _pending = self._active_fragments_ready()
                contract, digest, authority, public = self._migration(context)
                if variant == "schema":
                    contract["E1"]["model_schema_version"] = "9.9"
                    digest = rt.canonical_sha256(contract)
                elif variant == "protocol":
                    contract["E1"]["semantic_review_protocols"] = ["forged"]
                    digest = rt.canonical_sha256(contract)
                elif variant == "unapproved":
                    authority["E1"]["approved_mismatches"] = {}
                before = self.fixture.fixture._run_inventory()
                public_result = (
                    (public[:3], ("W1", {"stage": "W1", "identity_error": "fail"}))
                    if variant == "public"
                    else (public, None)
                )
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ), mock.patch.object(
                    prod, "TRUSTED_LEGACY_CATALOGS", authority
                ), mock.patch.object(
                    prod, "_validate_public_completion_chain", return_value=public_result
                ):
                    target, _evidence = prod._actual_contract_upgrade_target(
                        context.store,
                        context.state,
                        context.store.current_contract_upgrade(),
                    )
                    self.assertNotEqual("H1", target)
                    with self.assertRaises(
                        prod.ProductionOrchestratorError
                    ) as caught:
                        prod.apply_compatible_qualification_refresh(
                            context, actor="production-orchestrator"
                        )
                self.assertEqual(
                    "PROD_COMPATIBLE_QUALIFICATION_REFRESH_NOT_ADMISSIBLE",
                    caught.exception.code,
                )
                self.assertEqual(before, self.fixture.fixture._run_inventory())

    def test_prepared_crash_replays_exact_gate_order_and_workspace(self):
        context, workspace, pending = self._active_fragments_ready()
        migration = self._migration(context)
        patches = self._patches(migration)
        with patches[0], patches[1], patches[2], patches[3]:
            with mock.patch.object(
                context.store,
                "persist_state",
                side_effect=RuntimeError("compatible refresh prepared crash"),
            ):
                with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                    prod.apply_compatible_qualification_refresh(
                        context, actor="production-orchestrator"
                    )
            resumed = prod.resume_production_run(self.root)
            order = resumed.store.pending_work_order()
            qualification = resumed.store.current_contract_upgrade()
        self.assertEqual("compatible_qualification_refresh", qualification.data["transition_mode"])
        self.assertEqual(workspace.reference, resumed.store.latest_workspace().reference)
        self.assertEqual(workspace.reference, order.data["h1_workspace"])
        self.assertEqual(pending.data["action"], order.data["action"])
        self.assertEqual(pending.data["inputs"], order.data["inputs"])


if __name__ == "__main__":
    unittest.main()
