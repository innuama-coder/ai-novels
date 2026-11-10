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
from contextlib import ExitStack, contextmanager
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


class CompatibleQualificationRefreshAcceptanceTests(unittest.TestCase):
    """Tester-owned integration acceptance for the qualification-only edge."""

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

    def _active_h1_return(self):
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
        _helper, _planned, current, _fragment_order, _fragment_manifest = (
            self.fixture._advance_returned_h1(returned, initialized, plan_order)
        )
        gate, pending = prod.issue_stage_work(
            returned, action="H1-A-assemble", inputs={}
        )
        return returned, current, gate, pending

    def _migration(self, context, *, current_sha: str = "a" * 64):
        completion = context.state.data["current_stage_completions"]["E1"]
        identity = prod._completion_contract_identity(context.store, completion)
        qualified_contract = copy.deepcopy(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT
        )
        old_sha = qualified_contract["E1"]["identity_bindings"]["runtime"][
            "sha256"
        ]
        current_contract = copy.deepcopy(qualified_contract)
        current_contract["E1"]["identity_bindings"]["runtime"]["sha256"] = (
            current_sha
        )
        authority = copy.deepcopy(prod.TRUSTED_LEGACY_CATALOGS)
        authority["E1"] = {
            "canonical_digest": identity["implementation_catalog_sha256"],
            "removed_identities": frozenset(),
            "approved_mismatches": {
                qualified_contract["E1"]["identity_bindings"]["runtime"][
                    "identity"
                ]: (old_sha, current_sha)
            },
        }
        return {
            "contract": current_contract,
            "digest": rt.canonical_sha256(current_contract),
            "authority": authority,
            "registry_digest": "9" * 64,
        }

    @staticmethod
    def _validator_patch_targets():
        targets = {}
        baseline = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime.baseline"
        )
        targets["B0"] = (baseline, "validate_baseline_package")
        for stage, (module_name, function_name) in (
            prod._STAGE_PUBLIC_VALIDATORS.items()
        ):
            if stage != "B0":
                targets[stage] = (importlib.import_module(module_name), function_name)
        return targets

    @contextmanager
    def _migration_environment(self, migration, *, failing_stage: str | None = None):
        """Use the real replay chain with deterministic outer validators."""

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    prod,
                    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT",
                    migration["contract"],
                )
            )
            stack.enter_context(
                mock.patch.object(
                    prod,
                    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256",
                    migration["digest"],
                )
            )
            stack.enter_context(
                mock.patch.object(
                    prod, "TRUSTED_LEGACY_CATALOGS", migration["authority"]
                )
            )
            stack.enter_context(
                mock.patch.object(
                    prod,
                    "migration_registry_digest",
                    return_value=migration["registry_digest"],
                )
            )
            for stage, (module, function_name) in self._validator_patch_targets().items():
                if stage == failing_stage:
                    replacement = mock.Mock(
                        side_effect=ValueError(f"{stage} tester validator failure")
                    )
                else:
                    def replacement(package_root, *, _stage=stage):
                        root = Path(package_root)
                        completion = root / "stage-completion.json"
                        manifest = root / "package-manifest.json"
                        validation = root / "validation.json"
                        if not all(path.is_file() for path in (completion, manifest, validation)):
                            raise ValueError(f"{_stage} package is incomplete")
                        return {
                            "status": "ready",
                            "stage": _stage,
                            "completion_sha256": rt.sha256_file(completion),
                            "manifest_sha256": rt.sha256_file(manifest),
                            "validation_sha256": rt.sha256_file(validation),
                        }

                stack.enter_context(mock.patch.object(module, function_name, replacement))
            yield

    def _inventory(self):
        return self.fixture.fixture._run_inventory()

    def _package_inventory(self, context):
        inventory = {}
        for stage, reference in context.state.data[
            "current_stage_completions"
        ].items():
            root = self.root / Path(reference["path"]).parent
            inventory[stage] = {
                path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
        return inventory

    def _prepared_refresh(self):
        context, workspace, old_gate, pending = self._active_h1_return()
        migration = self._migration(context)
        with self._migration_environment(migration):
            with mock.patch.object(
                context.store,
                "persist_state",
                side_effect=RuntimeError("tester prepared crash"),
            ):
                with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                    prod.apply_compatible_qualification_refresh(
                        context, actor="production-orchestrator"
                    )
        prepared_path = next(
            path
            for path in (
                self.root / "orchestration" / "contract-upgrades"
            ).glob("*.prepared.json")
            if json.loads(path.read_text(encoding="utf-8")).get(
                "transition_mode"
            )
            == "compatible_qualification_refresh"
        )
        plan = context.store.load_document(
            {
                "path": prepared_path.relative_to(self.root).as_posix(),
                "sha256": rt.sha256_file(prepared_path),
            }
        )
        successor = rt.SealedDocument(
            data=copy.deepcopy(plan.data["successor_snapshot"]),
            reference=copy.deepcopy(plan.data["successor_state"]),
        )
        return context, workspace, old_gate, pending, migration, plan, successor

    def _assert_recovered(self, resumed, workspace, pending, plan):
        order = resumed.store.pending_work_order()
        self.assertEqual(plan.data["successor_state"], resumed.state.reference)
        self.assertEqual("compatible_qualification_refresh", (
            resumed.store.current_contract_upgrade().data["transition_mode"]
        ))
        self.assertEqual(workspace.reference, resumed.store.latest_workspace().reference)
        self.assertEqual(workspace.reference, order.data["h1_workspace"])
        self.assertEqual(pending.data["action"], order.data["action"])
        self.assertEqual(pending.data["inputs"], order.data["inputs"])
        self.assertEqual(plan.data["post_upgrade_work_order"], order.reference)

    def test_positive_refresh_is_qualification_only_append_only_and_exact(self):
        context, workspace, old_gate, pending = self._active_h1_return()
        migration = self._migration(context)
        completions = copy.deepcopy(context.state.data["current_stage_completions"])
        semantic_state = {
            key: copy.deepcopy(value)
            for key, value in context.state.data.items()
            if key not in {"revision", "previous_state"}
        }
        active_return = copy.deepcopy(context.state.data["active_return"])
        workspace_bytes = (self.root / workspace.reference["path"]).read_bytes()
        package_bytes = self._package_inventory(context)
        old_order_bytes = (self.root / pending.reference["path"]).read_bytes()
        old_qualification = context.store.current_contract_upgrade()
        old_qualification_bytes = (
            self.root / old_qualification.reference["path"]
        ).read_bytes()
        upgrade_root = self.root / "orchestration" / "contract-upgrades"
        old_upgrade_files = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in upgrade_root.glob("*.json")
        }

        with self._migration_environment(migration):
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

        self.assertEqual(active_return, refreshed.state.data["active_return"])
        self.assertEqual(completions, refreshed.state.data["current_stage_completions"])
        self.assertEqual(
            semantic_state,
            {
                key: value
                for key, value in refreshed.state.data.items()
                if key not in {"revision", "previous_state"}
            },
        )
        self.assertEqual(package_bytes, self._package_inventory(refreshed))
        self.assertEqual(workspace_bytes, (self.root / workspace.reference["path"]).read_bytes())
        self.assertEqual(workspace.reference, refreshed.store.latest_workspace().reference)
        self.assertEqual(pending.data["action"], order.data["action"])
        self.assertEqual(pending.data["inputs"], order.data["inputs"])
        self.assertEqual(pending.data["required_actor"], order.data["required_actor"])
        self.assertEqual(workspace.reference, order.data["h1_workspace"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        self.assertEqual(
            {key: value for key, value in old_gate.data.items() if key != "run_state"},
            {key: value for key, value in gate.data.items() if key != "run_state"},
        )
        self.assertEqual(old_order_bytes, (self.root / pending.reference["path"]).read_bytes())
        self.assertTrue(
            (
                self.root
                / "orchestration"
                / "work-orders"
                / f"{pending.data['work_id']}.rejected.json"
            ).is_file()
        )
        self.assertEqual(old_qualification.reference, receipt.data["prior_qualification"])
        self.assertEqual(
            old_qualification_bytes,
            (self.root / old_qualification.reference["path"]).read_bytes(),
        )
        for logical, body in old_upgrade_files.items():
            self.assertEqual(body, (self.root / logical).read_bytes())
        self.assertTrue((self.root / receipt.reference["path"]).is_file())
        self.assertTrue((self.root / receipt.data["plan"]["path"]).is_file())
        self.assertEqual([], receipt.data["invalidated_stages"])
        self.assertEqual("H1", receipt.data["target_stage"])
        self.assertEqual(
            migration["registry_digest"],
            receipt.data["stale_identity"][
                "implementation_migration_registry_sha256"
            ],
        )
        self.assertEqual(list(rt.STAGE_ORDER[:-1]), [
            item["stage"] for item in receipt.data["stale_identity"]["public_replays"]
        ])
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)
        self.assertEqual(workspace.reference, resumed.store.latest_workspace().reference)

    def test_schema_protocol_owner_version_and_unapproved_code_route_to_e1(self):
        for index, variant in enumerate(
            ("schema_binding", "review_protocol", "owner_version", "unapproved")
        ):
            with self.subTest(variant=variant):
                if index:
                    self._reset_fixture()
                context, _workspace, _old_gate, _pending = self._active_h1_return()
                migration = self._migration(context)
                if variant == "schema_binding":
                    migration["contract"]["E1"]["identity_bindings"]["schema"][
                        "sha256"
                    ] = "b" * 64
                elif variant == "review_protocol":
                    migration["contract"]["E1"]["semantic_review_protocols"] = [
                        "unapproved-review-protocol"
                    ]
                elif variant == "owner_version":
                    migration["contract"]["E1"]["model_schema_version"] = "99.0"
                else:
                    migration["authority"]["E1"]["approved_mismatches"] = {}
                migration["digest"] = rt.canonical_sha256(migration["contract"])
                before = self._inventory()
                with self._migration_environment(migration):
                    target, evidence = prod._actual_contract_upgrade_target(
                        context.store,
                        context.state,
                        context.store.current_contract_upgrade(),
                    )
                    self.assertEqual("E1", target)
                    self.assertEqual("E1", evidence.get("stage"))
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
                self.assertEqual(before, self._inventory())

    def test_tamper_missing_and_public_validator_failure_expose_real_owner(self):
        cases = (("tamper", "B0"), ("missing", "P1"), ("validator", "W1"))
        for index, (variant, expected_owner) in enumerate(cases):
            with self.subTest(variant=variant):
                if index:
                    self._reset_fixture()
                context, _workspace, _old_gate, _pending = self._active_h1_return()
                migration = self._migration(context)
                if variant == "tamper":
                    reference = context.state.data["current_stage_completions"][
                        expected_owner
                    ]
                    completion = context.store.load_document(reference)
                    path = self.root / completion.data["validation"]["path"]
                    path.write_bytes(path.read_bytes() + b"\n")
                elif variant == "missing":
                    reference = context.state.data["current_stage_completions"][
                        expected_owner
                    ]
                    completion = context.store.load_document(reference)
                    (self.root / completion.data["validation"]["path"]).unlink()
                before = self._inventory()
                failing_stage = expected_owner if variant == "validator" else None
                with self._migration_environment(
                    migration, failing_stage=failing_stage
                ):
                    target, evidence = prod._actual_contract_upgrade_target(
                        context.store,
                        context.state,
                        context.store.current_contract_upgrade(),
                    )
                    self.assertEqual(expected_owner, target)
                    self.assertEqual(expected_owner, evidence["stage"])
                    self.assertEqual(
                        "PROD_COMPLETION_PUBLIC_REPLAY_FAILED",
                        evidence["identity_error"],
                    )
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
                self.assertEqual(before, self._inventory())

    def test_prepared_mid_prefix_and_complete_pointer_gap_replay_exactly(self):
        for index, phase in enumerate(("prepared", "mid", "complete")):
            with self.subTest(phase=phase):
                if index:
                    self._reset_fixture()
                (
                    context,
                    workspace,
                    _old_gate,
                    pending,
                    migration,
                    plan,
                    successor,
                ) = self._prepared_refresh()
                receipt, derived = context.store.build_contract_upgrade_completion(
                    plan, successor=successor
                )
                if phase in {"mid", "complete"}:
                    context.store.persist_state(successor)
                if phase == "mid":
                    for document in derived[:-1]:
                        context.store.persist_document(document)
                elif phase == "complete":
                    for document in derived:
                        context.store.persist_document(document)
                    context.store.persist_document(receipt)
                    context.store._replace(
                        self.root / "orchestration" / "current-work-order.json",
                        {
                            "schema_version": "2.0",
                            "work_order": plan.data["post_upgrade_work_order"],
                        },
                    )
                before = self._inventory()
                with self._migration_environment(migration):
                    resumed = prod.resume_production_run(self.root)
                self._assert_recovered(resumed, workspace, pending, plan)
                for logical, body in before.items():
                    if logical not in {
                        "orchestration/current-state.json",
                        "orchestration/current-contract-upgrade.json",
                        "orchestration/current-work-order.json",
                    }:
                        self.assertEqual(body, (self.root / logical).read_bytes())

    def test_forged_prepared_identity_order_workspace_and_registry_fail_closed(self):
        for index, variant in enumerate(("identity", "order", "workspace", "registry")):
            with self.subTest(variant=variant):
                if index:
                    self._reset_fixture()
                (
                    _context,
                    _workspace,
                    _old_gate,
                    _pending,
                    migration,
                    plan,
                    _successor,
                ) = self._prepared_refresh()
                path = self.root / plan.reference["path"]
                data = json.loads(path.read_text(encoding="utf-8"))
                if variant == "identity":
                    data["stale_identity"]["classification"] = "forged-compatible"
                elif variant == "registry":
                    data["stale_identity"][
                        "implementation_migration_registry_sha256"
                    ] = "f" * 64
                elif variant == "workspace":
                    forged = copy.deepcopy(data["stale_identity"]["current_workspace"])
                    forged["sha256"] = "f" * 64
                    data["stale_identity"]["current_workspace"] = forged
                    order = next(
                        item
                        for item in data["post_upgrade_documents"]
                        if item["reference"] == data["post_upgrade_work_order"]
                    )
                    order["data"]["h1_workspace"] = forged
                    order["reference"]["sha256"] = rt.canonical_sha256(order["data"])
                    data["post_upgrade_work_order"] = order["reference"]
                else:
                    order = next(
                        item
                        for item in data["post_upgrade_documents"]
                        if item["reference"] == data["post_upgrade_work_order"]
                    )
                    data["post_upgrade_inputs"]["forged"] = True
                    order["data"]["inputs"]["forged"] = True
                    order["reference"]["sha256"] = rt.canonical_sha256(order["data"])
                    data["post_upgrade_work_order"] = order["reference"]
                path.write_text(rt.canonical_json(data), encoding="utf-8")
                before = self._inventory()
                with self._migration_environment(migration):
                    with self.assertRaises(
                        (store_module.ProductionStoreError, prod.ProductionOrchestratorError)
                    ):
                        prod.resume_production_run(self.root)
                self.assertEqual(before, self._inventory())


if __name__ == "__main__":
    unittest.main()
