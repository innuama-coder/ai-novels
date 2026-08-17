from __future__ import annotations

import copy
import importlib
import unittest
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
prod_coord = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_coordinator"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)
fixtures = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)


class SameOwnerActiveStageReturnRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    @staticmethod
    def _request(stage: str, return_id: str):
        issue_kind = {
            "B0": "baseline_packaging",
            "P1": "package_assembly",
        }[stage]
        data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id=return_id,
            origin_kind="stage",
            origin_stage=stage,
            issue_kind=issue_kind,
            problem=f"The pending {stage} order predates the current owner runtime.",
            evidence_ids=[f"{stage}-OWNER-RUNTIME-STALE"],
            violated_contract=f"{stage} package-bound implementation",
            required_revision=f"Reissue {stage} against current sealed inputs.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        return rt.seal_document(
            data, f"returns/{return_id}/return-request.json"
        )

    def _active(self, stage: str):
        context = self.fixture._context()
        if stage == "P1":
            upstream = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1")
            for revision, owner in enumerate(upstream, 1):
                _, order = prod.issue_stage_work(context, action=owner, inputs={})
                _, context = prod.execute_stage_work(
                    context,
                    work_order=order,
                    actor=prod.ACTION_CONTRACT[owner][1],
                    executor=self.fixture._fake_executor(owner, revision),
                )
        _, pending = prod.issue_stage_work(context, action=stage, inputs={})
        first = self._request(stage, f"RET-{stage}-FIRST")
        _, active, _, old_order = prod.apply_stage_return(
            context,
            work_order=pending,
            request=first,
            actor=prod.ACTION_CONTRACT[stage][1],
            inputs={},
        )
        return active, first, old_order

    def test_p1_same_owner_refresh_reissues_current_authoritative_inputs(self):
        active, old, old_order = self._active("P1")
        self.assertIs(type(active.coordinator), prod_coord.ProductionCoordinator)
        shared = (
            prod._REPO_ROOT
            / "harnesses/novel-conception-autonomous/runtime/coordinator.py"
        )
        self.assertEqual(
            rt.sha256_file(shared),
            "e4ea4e3a1c70978a2d625b42300fe4c48c324042559f0289a2d097b0ddf962ae",
        )
        self.assertFalse(any(
            path.name == "production_coordinator.py"
            and "implementation" in path.parts
            for path in self.root.rglob("production_coordinator.py")
        ))
        upstream_before = copy.deepcopy(
            active.state.data["current_stage_completions"]
        )
        request = self._request("P1", "RET-P1-SECOND")
        receipt, refreshed, gate, order = prod.refresh_active_stage_return(
            active,
            request=request,
            actor="production-orchestrator",
            inputs={},
        )
        self.assertEqual(
            "active_stage_return_refresh", receipt.data["transition_mode"]
        )
        self.assertEqual(old.reference, receipt.data["superseded_return"])
        self.assertIs(type(refreshed.coordinator), prod_coord.ProductionCoordinator)
        self.assertEqual(upstream_before, refreshed.state.data["current_stage_completions"])
        self.assertEqual(request.reference, refreshed.active_return.reference)
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual("P1", order.data["action"])
        expected = prod._authoritative_package_inputs(
            refreshed, action="P1", gate=gate
        )
        self.assertEqual(expected, prod._sealed_executor_inputs(order))
        self.assertTrue(
            (self.root / "orchestration/work-orders" /
             f"{old_order.data['work_id']}.rejected.json").is_file()
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)

    def test_wrong_target_no_active_and_wrong_order_are_zero_write(self):
        inactive = self.fixture._context()
        request = self._request("B0", "RET-B0-NO-ACTIVE")
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError, "PROD_ACTIVE_STAGE_RETURN_REQUIRED"
        ):
            prod.refresh_active_stage_return(
                inactive, request=request, actor="production-orchestrator", inputs={}
            )
        self.assertEqual(before, self.fixture._run_inventory())

        self.fixture.tearDown()
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        active, old, pending = self._active("B0")
        wrong = rt.route_return(
            run_id="RUN-PROD-1", return_id="RET-B0-WRONG-TARGET",
            origin_kind="stage", origin_stage="B0", issue_kind="storyline",
            problem="wrong target", evidence_ids=["S1-WRONG"],
            violated_contract="same owner", required_revision="reject",
            author_decision=None, has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        wrong_request = rt.seal_document(
            wrong, "returns/RET-B0-WRONG-TARGET/return-request.json"
        )
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError,
            "PROD_ACTIVE_STAGE_RETURN_ROUTE_INVALID",
        ):
            prod.refresh_active_stage_return(
                active, request=wrong_request,
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual(before, self.fixture._run_inventory())

        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {"schema_version": "2.0", "work_order": {
                "path": "orchestration/work-orders/missing.json",
                "sha256": "f" * 64,
            }},
        )
        before = self.fixture._run_inventory()
        with self.assertRaises(store_module.ProductionStoreError):
            prod.refresh_active_stage_return(
                active, request=self._request("B0", "RET-B0-WRONG-ORDER"),
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual(before, self.fixture._run_inventory())

    def test_prepared_mid_and_complete_pointer_gap_recover_exactly(self):
        for boundary in ("prepared", "mid", "complete"):
            with self.subTest(boundary=boundary):
                if boundary != "prepared":
                    self.fixture.tearDown()
                    self.fixture = fixtures.ProductionOrchestratorTests(
                        methodName="runTest"
                    )
                    self.fixture.setUp()
                    self.root = self.fixture.root
                active, _, _ = self._active("B0")
                request = self._request("B0", f"RET-B0-REFRESH-{boundary.upper()}")
                with mock.patch.object(
                    active.store, "persist_state",
                    side_effect=RuntimeError("refresh prepared crash"),
                ):
                    with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                        prod.refresh_active_stage_return(
                            active, request=request,
                            actor="production-orchestrator", inputs={},
                        )
                plan_path = next(
                    path for path in (
                        self.root / "orchestration/contract-upgrades"
                    ).glob("*.prepared.json")
                    if not path.with_name(
                        path.name.replace(".prepared.json", ".complete.json")
                    ).exists()
                )
                plan = active.store.load_document({
                    "path": plan_path.relative_to(self.root).as_posix(),
                    "sha256": rt.sha256_file(plan_path),
                })
                successor = rt.SealedDocument(
                    copy.deepcopy(plan.data["successor_snapshot"]),
                    dict(plan.data["successor_state"]),
                )
                receipt, derived = active.store.build_contract_upgrade_completion(
                    plan, successor=successor
                )
                if boundary in {"mid", "complete"}:
                    active.store.persist_state(successor)
                    for document in (
                        derived[: max(1, len(derived) // 2)]
                        if boundary == "mid" else derived
                    ):
                        active.store.persist_document(document)
                if boundary == "complete":
                    active.store.persist_document(receipt)
                resumed = prod.resume_production_run(self.root)
                self.assertEqual(successor.reference, resumed.state.reference)
                self.assertEqual(request.reference, resumed.active_return.reference)
                self.assertEqual(
                    receipt.reference,
                    resumed.store.current_contract_upgrade().reference,
                )

    def test_collision_fails_before_transaction_writes(self):
        active, _, _ = self._active("B0")
        request = self._request("B0", "RET-B0-COLLISION")
        collision = self.root / request.reference["path"]
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text(rt.canonical_json({"conflict": True}), encoding="utf-8")
        before = self.fixture._run_inventory()
        with self.assertRaisesRegex(
            store_module.ProductionStoreError, "PROD_IMMUTABLE_CONFLICT"
        ):
            prod.refresh_active_stage_return(
                active, request=request, actor="production-orchestrator", inputs={}
            )
        self.assertEqual(before, self.fixture._run_inventory())
