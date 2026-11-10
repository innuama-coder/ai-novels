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
from pathlib import Path
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)
plan_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_internal_h1_plan_return"
)
fragment_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_internal_h1_fragment_return"
)
refresh_acceptance = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests."
    "test_compatible_qualification_refresh_acceptance"
)


_RefreshHelpers = (
    refresh_acceptance.CompatibleQualificationRefreshAcceptanceTests
)


class CompatibleRefreshFragmentReturnAcceptanceTests(unittest.TestCase):
    """Cross-transaction acceptance for a consumed H1-B predecessor bridge."""

    _migration = _RefreshHelpers._migration
    _validator_patch_targets = staticmethod(
        _RefreshHelpers._validator_patch_targets
    )
    _migration_environment = _RefreshHelpers._migration_environment

    def setUp(self) -> None:
        self.fixture = plan_tests.InternalH1PlanReturnTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def _reset_fixture(self) -> None:
        self.fixture.tearDown()
        self.fixture = plan_tests.InternalH1PlanReturnTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def _inventory(self):
        return self.fixture.fixture._run_inventory()

    def _refreshed_consumed_h1_b(self):
        context, _planned, ready, _assemble = (
            self.fixture._ready_with_pending_assemble()
        )
        candidate, plan_failure, plan_review_completion = (
            self.fixture._candidate_and_failure(context, ready)
        )
        plan_request = self.fixture._request(plan_failure)
        _receipt, returned, initialized, _gate, plan_order = (
            prod.apply_internal_h1_plan_return(
                context,
                fidelity_failure=plan_failure,
                candidate_report=candidate,
                review_completion=plan_review_completion,
                request=plan_request,
                actor="production-orchestrator",
            )
        )
        _helper, planned, fragments_ready, consumed_h1_b, fragment_manifest = (
            self.fixture._advance_returned_h1(returned, initialized, plan_order)
        )
        _assemble_gate, stale_assemble = prod.issue_stage_work(
            returned, action="H1-A-assemble", inputs={}
        )
        migration = self._migration(returned)
        predecessor = returned.state
        old_return = returned.active_return
        with self._migration_environment(migration):
            qualification, refreshed, refreshed_gate, refreshed_assemble = (
                prod.apply_compatible_qualification_refresh(
                    returned, actor="production-orchestrator"
                )
            )
        self.assertEqual(predecessor.reference, refreshed.state.data["previous_state"])
        self.assertEqual(
            predecessor.reference, consumed_h1_b.data["state"]
        )
        self.assertEqual(old_return.reference, refreshed.active_return.reference)
        self.assertEqual(fragments_ready.reference, refreshed.store.latest_workspace().reference)
        return {
            "context": refreshed,
            "migration": migration,
            "qualification": qualification,
            "predecessor": predecessor,
            "planned": planned,
            "workspace": fragments_ready,
            "consumed": consumed_h1_b,
            "manifest": fragment_manifest,
            "old_return": old_return,
            "stale_assemble": stale_assemble,
            "refreshed_gate": refreshed_gate,
            "refreshed_assemble": refreshed_assemble,
        }

    def _review_evidence(self, fixture, *, marker="post-refresh"):
        helper = object.__new__(fragment_tests.InternalH1FragmentReturnTests)
        helper.root = self.root
        failure = helper._failure_document(
            fixture["context"],
            fixture["workspace"],
            fixture["consumed"],
            fixture["manifest"],
            marker,
        )
        with self._migration_environment(fixture["migration"]):
            assignment = prod.assign_internal_h1_fragment_fidelity_review(
                fixture["context"],
                consumed_work_order=fixture["consumed"],
                fragment_manifest=fixture["manifest"],
                reviewer=failure.data["reviewer"],
                actor="production-orchestrator",
            )
            completion = prod.record_internal_h1_fragment_fidelity_failure(
                fixture["context"],
                assignment=assignment,
                consumed_work_order=fixture["consumed"],
                fragment_manifest=fixture["manifest"],
                fidelity_failure=failure,
                actor="novel-conception-presentation-fidelity-reviewer",
            )
        request = helper._request(failure)
        return failure, assignment, completion, request

    def _apply_fragment_return(self, fixture, evidence):
        failure, _assignment, completion, request = evidence
        with self._migration_environment(fixture["migration"]):
            return prod.apply_internal_h1_fragment_return(
                fixture["context"],
                consumed_work_order=fixture["consumed"],
                fidelity_failure=failure,
                review_completion=completion,
                request=request,
                actor="production-orchestrator",
                inputs={},
            )

    def _assert_fragment_return(self, fixture, evidence, result):
        receipt, returned, gate, order = result
        failure, assignment, completion, request = evidence
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(fixture["old_return"].reference, receipt.data["superseded_return"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual(fixture["planned"].reference, returned.store.latest_workspace().reference)
        self.assertEqual("H1-B", order.data["action"])
        self.assertEqual(fixture["planned"].reference, order.data["h1_workspace"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual(returned.state.reference, gate.data["run_state"])
        self.assertEqual(fixture["context"].state.reference, assignment.data["state"])
        self.assertEqual(fixture["context"].state.reference, completion.data["state"])
        self.assertEqual(fixture["predecessor"].reference, fixture["consumed"].data["state"])
        self.assertEqual(failure.reference, completion.data["review"])
        self.assertTrue(
            (
                self.root
                / "orchestration"
                / "work-orders"
                / f"{fixture['refreshed_assemble'].data['work_id']}.rejected.json"
            ).is_file()
        )

    def _forged_consumed_order(self, fixture, *, state, marker):
        body = {
            key: copy.deepcopy(value)
            for key, value in fixture["consumed"].data.items()
            if key != "work_id"
        }
        body["state"] = copy.deepcopy(state)
        work_id = rt.canonical_sha256(body)[:24]
        data = {**body, "work_id": work_id}
        order = rt.SealedDocument(
            data=data,
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": rt.canonical_sha256(data),
            },
        )
        fixture["context"].store.persist_document(order)
        consumed_body = {
            "schema_version": "2.0",
            "work_order": dict(order.reference),
            "successor": dict(fixture["workspace"].reference),
            "status": "consumed",
        }
        marker_path = (
            self.root
            / "orchestration"
            / "work-orders"
            / f"{work_id}.consumed.json"
        )
        marker_path.write_text(rt.canonical_json(consumed_body), encoding="utf-8")
        return order

    def _install_intervening_state(self, fixture, *, semantic: bool):
        predecessor = fixture["context"].state
        data = copy.deepcopy(predecessor.data)
        data["revision"] += 1
        data["previous_state"] = dict(predecessor.reference)
        if semantic:
            data["development_status"] = (
                "ready"
                if data.get("development_status") != "ready"
                else "blocked"
            )
        document = rt.SealedDocument(
            data=data,
            reference={
                "path": f"state/revision-{data['revision']:03d}.json",
                "sha256": rt.canonical_sha256(data),
            },
        )
        fixture["context"].store.persist_document(document)
        fixture["context"].store._replace(
            self.root / "orchestration" / "current-state.json",
            {"schema_version": "2.0", "state": document.reference},
        )
        fixture["context"] = prod.ProductionContext(
            fixture["context"].store,
            fixture["context"].coordinator,
            document,
            fixture["context"].active_return,
        )

    def test_direct_compatible_successor_admits_review_and_local_h1_b_return(self):
        fixture = self._refreshed_consumed_h1_b()
        completions = copy.deepcopy(
            fixture["context"].state.data["current_stage_completions"]
        )
        workspace_bytes = (
            self.root / fixture["workspace"].reference["path"]
        ).read_bytes()
        evidence = self._review_evidence(fixture)
        result = self._apply_fragment_return(fixture, evidence)
        self._assert_fragment_return(fixture, evidence, result)
        receipt, returned, _gate, order = result
        self.assertEqual(completions, returned.state.data["current_stage_completions"])
        self.assertEqual(
            workspace_bytes,
            (self.root / fixture["workspace"].reference["path"]).read_bytes(),
        )
        self.assertEqual(
            fixture["qualification"].reference, receipt.data["prior_qualification"]
        )
        with self._migration_environment(fixture["migration"]):
            resumed = prod.resume_production_run(self.root)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        self.assertEqual(fixture["planned"].reference, resumed.store.latest_workspace().reference)

    def test_prepared_fragment_return_replays_after_compatible_refresh(self):
        fixture = self._refreshed_consumed_h1_b()
        evidence = self._review_evidence(fixture, marker="post-refresh-crash")
        with self._migration_environment(fixture["migration"]):
            with mock.patch.object(
                fixture["context"].store,
                "persist_state",
                side_effect=RuntimeError("fragment return prepared crash"),
            ):
                with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                    self._apply_fragment_return(fixture, evidence)
        prepared = next(
            path
            for path in (
                self.root / "orchestration" / "contract-upgrades"
            ).glob("*.prepared.json")
            if json.loads(path.read_text(encoding="utf-8")).get(
                "transition_mode"
            )
            == "active_stage_return_refresh"
            and json.loads(path.read_text(encoding="utf-8")).get(
                "target_stage"
            )
            == "H1"
            and json.loads(path.read_text(encoding="utf-8")).get(
                "stale_identity", {}
            ).get("origin_action")
            == "H1-B"
        )
        self.assertTrue(prepared.is_file())
        with self._migration_environment(fixture["migration"]):
            resumed = prod.resume_production_run(self.root)
        receipt = resumed.store.current_contract_upgrade()
        result = (
            receipt,
            resumed,
            resumed.store.load_document(
                resumed.store.pending_work_order().data["input_gate"]
            ),
            resumed.store.pending_work_order(),
        )
        self._assert_fragment_return(fixture, evidence, result)

    def test_tampered_foreign_nondirect_and_intervening_state_fail_closed(self):
        variants = ("tampered", "foreign", "non_direct", "intervening_semantic")
        for index, variant in enumerate(variants):
            with self.subTest(variant=variant):
                if index:
                    self._reset_fixture()
                fixture = self._refreshed_consumed_h1_b()
                consumed = fixture["consumed"]
                if variant == "tampered":
                    plan_path = self.root / fixture["qualification"].data["plan"]["path"]
                    plan = json.loads(plan_path.read_text(encoding="utf-8"))
                    plan["stale_identity"]["current_workspace"]["sha256"] = "f" * 64
                    plan_path.write_text(rt.canonical_json(plan), encoding="utf-8")
                elif variant == "foreign":
                    foreign_data = copy.deepcopy(fixture["predecessor"].data)
                    foreign_data["run_id"] = "RUN-FOREIGN"
                    foreign = rt.SealedDocument(
                        data=foreign_data,
                        reference={
                            "path": "state/foreign-fragment-order-state.json",
                            "sha256": rt.canonical_sha256(foreign_data),
                        },
                    )
                    fixture["context"].store.persist_document(foreign)
                    consumed = self._forged_consumed_order(
                        fixture, state=foreign.reference, marker=variant
                    )
                elif variant == "non_direct":
                    older = fixture["context"].store.load_document(
                        fixture["predecessor"].data["previous_state"]
                    )
                    consumed = self._forged_consumed_order(
                        fixture, state=older.reference, marker=variant
                    )
                else:
                    self._install_intervening_state(fixture, semantic=True)
                helper = object.__new__(
                    fragment_tests.InternalH1FragmentReturnTests
                )
                helper.root = self.root
                failure = helper._failure_document(
                    fixture["context"],
                    fixture["workspace"],
                    consumed,
                    fixture["manifest"],
                    f"reject-{variant}",
                )
                before = self._inventory()
                with self._migration_environment(fixture["migration"]):
                    with self.assertRaises(
                        (store_module.ProductionStoreError,
                         prod.ProductionOrchestratorError)
                    ):
                        prod.assign_internal_h1_fragment_fidelity_review(
                            fixture["context"],
                            consumed_work_order=consumed,
                            fragment_manifest=fixture["manifest"],
                            reviewer=failure.data["reviewer"],
                            actor="production-orchestrator",
                        )
                self.assertEqual(before, self._inventory())

    def test_compatible_refresh_does_not_hide_prior_active_h1_reviewer(self):
        fixture = self._refreshed_consumed_h1_b()
        compatible = fixture["context"].store.current_contract_upgrade()
        prior = fixture["context"].store.load_document(
            compatible.data["prior_qualification"]
        )
        prior_assignment = fixture["context"].store.load_document(
            prior.data["stale_identity"]["review_assignment"]
        )
        prior_reviewer = prior_assignment.data["reviewer"]
        helper = object.__new__(fragment_tests.InternalH1FragmentReturnTests)
        helper.root = self.root
        for field in ("task_id", "thread_id"):
            with self.subTest(reused=field):
                reviewer = {
                    "task_id": f"/root/new-fragment-review-{field}",
                    "thread_id": f"THREAD-NEW-FRAGMENT-{field}",
                    "independence_basis": "separate-task-no-producer-context",
                }
                reviewer[field] = prior_reviewer[field]
                failure = helper._failure_document(
                    fixture["context"],
                    fixture["workspace"],
                    fixture["consumed"],
                    fixture["manifest"],
                    f"reused-{field}",
                    reviewer=reviewer,
                )
                before = self._inventory()
                with self._migration_environment(fixture["migration"]):
                    with self.assertRaisesRegex(
                        prod.ProductionOrchestratorError,
                        "PROD_H1_FRAGMENT_FIDELITY_REVIEW_NOT_INDEPENDENT",
                    ):
                        prod.assign_internal_h1_fragment_fidelity_review(
                            fixture["context"],
                            consumed_work_order=fixture["consumed"],
                            fragment_manifest=fixture["manifest"],
                            reviewer=failure.data["reviewer"],
                            actor="production-orchestrator",
                        )
                self.assertEqual(before, self._inventory())


del _RefreshHelpers


if __name__ == "__main__":
    unittest.main()
