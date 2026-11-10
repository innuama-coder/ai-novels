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

import importlib
import copy
import json
import shutil
import tempfile
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from pathlib import Path, PurePosixPath


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


class ProductionOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="prod-orchestrator-")
        self.root = Path(self.temporary.name)
        self.public_replay = mock.patch.object(
            prod, "_validate_stage_public_package", return_value=None
        )
        self.public_replay_mock = self.public_replay.start()
        self.addCleanup(self.public_replay.stop)

    def tearDown(self) -> None:
        if prod.os.name == "nt":
            shutil.rmtree(
                Path("\\\\?\\" + str(self.root.absolute())),
                ignore_errors=True,
            )
        self.temporary.cleanup()

    def _context(self):
        return prod.initialize_production_run(
            self.root,
            run_id="RUN-PROD-1",
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": "1" * 64,
            },
        )

    def _fake_executor(
        self, stage: str, revision: int, *, model_version: str | None = None
    ):
        def execute(coordinator, gate):
            base_rel = f"{stage}/attempt-{revision:03d}"
            canonical_path = self.root / base_rel / "canonical.json"
            manifest_path = self.root / base_rel / "package-manifest.json"
            validation_path = self.root / base_rel / "validation.json"
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            canonical = {
                "schema_version": (
                    model_version or prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                        "model_schema_version"
                    ]
                    if stage in {"E1", "T1"}
                    else "2.0"
                ),
                "stage": stage,
            }
            canonical_path.write_text(rt.canonical_json(canonical), encoding="utf-8")
            canonical_ref = {
                "path": f"{base_rel}/canonical.json",
                "sha256": rt.sha256_file(canonical_path),
            }
            validation_path.write_text(
                rt.canonical_json({"schema_version": "2.0", "status": "ready"}),
                encoding="utf-8",
            )
            validation_ref = {
                "path": f"{base_rel}/validation.json",
                "sha256": rt.sha256_file(validation_path),
            }
            artifact_roles = {"canonical": canonical_ref}
            manifest = {
                "schema_version": "2.0",
                "stage": stage,
                "verdict": "ready",
                "artifact_roles": artifact_roles,
                "validation": validation_ref,
            }
            if stage in {"E1", "T1"}:
                implementation_catalog = []
                for kind in ("runtime", "schema", "protocol"):
                    identity, source_rel = prod._STAGE_IDENTITY_SOURCES[stage][kind]
                    source = prod._REPO_ROOT / source_rel
                    target = self.root / base_rel / "implementation" / identity
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
                    implementation_catalog.append(
                        {
                            "identity": identity,
                            "artifact": {
                                "path": target.relative_to(self.root).as_posix(),
                                "sha256": rt.sha256_file(target),
                            },
                        }
                    )
                execution_path = self.root / base_rel / "execution-record.json"
                execution_path.write_text(
                    rt.canonical_json(
                        {"implementation_catalog": implementation_catalog}
                    ),
                    encoding="utf-8",
                )
                session = {"stage": stage, "session_id": f"SESSION-{stage}"}
                protocols = prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                    "semantic_review_protocols"
                ]
                if stage == "E1":
                    session.update(
                        {
                            "authority_review_protocol": protocols[0],
                            "hosting_review_protocol": protocols[1],
                        }
                    )
                else:
                    session["plan_review_protocol"] = protocols[0]
                session_path = self.root / base_rel / "generation-session.json"
                session_path.write_text(rt.canonical_json(session), encoding="utf-8")
                artifact_roles.update(
                    {
                        "execution_record": {
                            "path": execution_path.relative_to(self.root).as_posix(),
                            "sha256": rt.sha256_file(execution_path),
                        },
                        "generation_session": {
                            "path": session_path.relative_to(self.root).as_posix(),
                            "sha256": rt.sha256_file(session_path),
                        },
                    }
                )
            manifest_path.write_text(rt.canonical_json(manifest), encoding="utf-8")
            completion_data = {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": stage,
                "status": "ready",
                "manifest": {
                    "path": f"{base_rel}/package-manifest.json",
                    "sha256": rt.sha256_file(manifest_path),
                },
                "validation": validation_ref,
                "input_gate": gate.reference,
                "state_before": gate.data["run_state"],
                "previous_stage_completions": gate.data[
                    "upstream_completions"
                ],
                "return_binding": gate.data["return_binding"],
            }
            if stage in {"S1", "W1", "E1", "T1", "C1", "Q1", "H1"}:
                completion_data["session_id"] = f"SESSION-{stage}"
            completion = rt.seal_stage_document(
                completion_data,
                stage,
                f"{base_rel}/stage-completion.json",
            )
            transition = coordinator.accept_stage_completion(
                gate=gate,
                completion=completion,
                next_state_path=f"state/revision-{revision:03d}.json",
            )
            return types.SimpleNamespace(
                transition=transition, completion=completion
            )

        return execute

    def _active_e1_contract_return(self):
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(
                    stage,
                    revision,
                    model_version="2.3" if stage == "E1" else None,
                ),
            )
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-E1-ACTIVE",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="environment",
            problem="The sealed E1 package uses the predecessor contract.",
            evidence_ids=["E1-CONTRACT-ACTIVE"],
            violated_contract="E1 production identity",
            required_revision="Regenerate E1 under the current contract.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data,
            "returns/RET-CONTRACT-UPGRADE-E1-ACTIVE.json",
        )
        receipt, active = prod.apply_contract_upgrade(
            context,
            request=request,
            old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        )
        return receipt, active, request

    def _refreshed_contract(self, marker: str):
        contract = copy.deepcopy(prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT)
        contract["E1"]["identity_bindings"]["runtime"]["sha256"] = marker * 64
        return contract, rt.canonical_sha256(contract)

    def _escalation_request(
        self,
        old_request,
        *,
        target: str = "B0",
        return_id: str = "RET-ESCALATE-B0-001",
    ):
        issue_kind = {
            "B0": "baseline_packaging",
            "S1": "storyline",
            "W1": "world",
            "E1": "environment",
            "T1": "event_timeline",
        }[target]
        data = rt.route_return(
            run_id="RUN-PROD-1", return_id=return_id,
            origin_kind="stage", origin_stage=old_request.data["resume_stage"],
            issue_kind=issue_kind,
            problem=f"{target} implementation identity is stale.",
            evidence_ids=[f"{target}-IMPLEMENTATION-STALE"],
            violated_contract=f"{target} implementation identity",
            required_revision=f"Regenerate {target} under the current implementation.",
            author_decision=None, has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        return rt.seal_document(data, f"returns/{return_id}.json")

    def _prepared_only_escalation(self):
        prior, active, old_request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        request = self._escalation_request(old_request)
        with mock.patch.object(
            active.store,
            "persist_state",
            side_effect=RuntimeError("escalation prepared-only crash"),
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared-only crash"):
                prod.apply_active_return_escalation(
                    active, request=request,
                    actor="production-orchestrator", inputs={"recovery": True},
                )
        prepared_path = next(
            path
            for path in (self.root / "orchestration/contract-upgrades").glob(
                "*.prepared.json"
            )
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
        )
        plan = active.store.load_document(
            {
                "path": prepared_path.relative_to(self.root).as_posix(),
                "sha256": rt.sha256_file(prepared_path),
            }
        )
        successor = rt.SealedDocument(
            copy.deepcopy(plan.data["successor_snapshot"]),
            dict(plan.data["successor_state"]),
        )
        return prior, active, old_request, request, pending, plan, successor

    def _active_c1_return(self):
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context, work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        request_data = rt.route_return(
            run_id="RUN-PROD-1", return_id="RET-C1-ACTIVE-ESCALATION",
            origin_kind="stage", origin_stage="Q1", issue_kind="character",
            problem="C1 must be regenerated.", evidence_ids=["C1-STALE"],
            violated_contract="C1 implementation", required_revision="Revise C1.",
            author_decision=None, has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data, "returns/RET-C1-ACTIVE-ESCALATION.json"
        )
        context.store.persist_document(request)
        transition = context.coordinator.apply_return_request(
            request=request,
            next_state_path=(
                f"state/revision-{context.state.data['revision'] + 1:03d}.json"
            ),
        )
        successor = rt.SealedDocument(transition.snapshot, transition.reference)
        context.store.persist_state(successor)
        active = prod.ProductionContext(
            context.store, context.coordinator, successor, request
        )
        return context.store.current_contract_upgrade(), active, request

    def _pending_c1_stage_return(self):
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1", "T1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        _, pending = prod.issue_stage_work(
            context, action="C1", inputs={"candidate": "hard-admission"}
        )
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-C1-T1-HARD-ADMISSION",
            origin_kind="stage",
            origin_stage="C1",
            issue_kind="event_timeline",
            problem="T1 contains no information change for C1 admission.",
            evidence_ids=["C1_INFORMATION_INPUT_EMPTY"],
            violated_contract="C1 hard admission requires T1 information movement.",
            required_revision="Revise T1 with a real information change.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data,
            "returns/RET-C1-T1-HARD-ADMISSION/return-request.json",
        )
        return context, pending, request

    def _prepared_only_stage_return(self):
        context, pending, request = self._pending_c1_stage_return()
        with mock.patch.object(
            context.store,
            "persist_state",
            side_effect=RuntimeError("stage-return prepared-only crash"),
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared-only crash"):
                prod.apply_stage_return(
                    context,
                    work_order=pending,
                    request=request,
                    actor=prod.ACTION_CONTRACT["C1"][1],
                    inputs={"reason": "repair T1 information flow"},
                )
        prepared_path = next(
            path
            for path in (self.root / "orchestration/contract-upgrades").glob(
                "*.prepared.json"
            )
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
        )
        plan = context.store.load_document(
            {
                "path": prepared_path.relative_to(self.root).as_posix(),
                "sha256": rt.sha256_file(prepared_path),
            }
        )
        successor = rt.SealedDocument(
            copy.deepcopy(plan.data["successor_snapshot"]),
            dict(plan.data["successor_state"]),
        )
        return context, pending, request, plan, successor

    def _prepared_qualified_escalation(self, target: str):
        prior, active, old_request = self._active_c1_return()
        _, pending = prod.issue_stage_work(active, action="C1", inputs={})
        request = self._escalation_request(
            old_request, target=target,
            return_id=f"RET-ESCALATE-{target}-QUALIFIED",
        )
        with mock.patch.object(
            active.store, "persist_state",
            side_effect=RuntimeError("qualified escalation prepared crash"),
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared crash"):
                prod.apply_active_return_escalation(
                    active, request=request, actor="production-orchestrator",
                    inputs={"qualified": target},
                )
        prepared_path = next(
            path for path in (
                self.root / "orchestration/contract-upgrades"
            ).glob("*.prepared.json")
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
        )
        plan = active.store.load_document({
            "path": prepared_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(prepared_path),
        })
        return prior, active, old_request, request, pending, plan

    def _published_generation1_legacy_refresh(self):
        first, active, request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        session_path = self.root / "E1/legacy-refresh/generation-session.json"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        session_path.write_text(
            rt.canonical_json({
                "schema_version": "1.0", "stage": "E1",
                "session_id": "SESSION-E1-LEGACY-REFRESH",
            }),
            encoding="utf-8",
        )
        contract, digest = self._refreshed_contract("7")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            receipt, refreshed = prod.apply_contract_upgrade(
                active, request=request,
                old_contract_digest=first.data["new_contract_digest"],
            )
        plan_path = self.root / receipt.data["plan"]["path"]
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        for field in (
            "superseded_return",
            "post_upgrade_documents",
            "post_upgrade_work_order",
            "post_upgrade_inputs",
        ):
            plan_data.pop(field)
        plan_path.write_text(rt.canonical_json(plan_data), encoding="utf-8")
        plan_reference = {
            "path": receipt.data["plan"]["path"],
            "sha256": rt.sha256_file(plan_path),
        }
        receipt_path = self.root / receipt.reference["path"]
        receipt_data = copy.deepcopy(receipt.data)
        for field in (
            "superseded_return",
            "post_upgrade_documents",
            "post_upgrade_work_order",
        ):
            receipt_data.pop(field)
        receipt_data["plan"] = plan_reference
        receipt_path.write_text(rt.canonical_json(receipt_data), encoding="utf-8")
        receipt_reference = {
            "path": receipt.reference["path"],
            "sha256": rt.sha256_file(receipt_path),
        }
        refreshed.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": receipt_reference},
        )
        return {
            "contract": contract, "digest": digest,
            "first": first, "context": refreshed, "request": request,
            "pending": pending, "plan_path": plan_path,
            "receipt_path": receipt_path,
            "plan_reference": plan_reference,
            "receipt_reference": receipt_reference,
        }

    def _active_e1_contract_return_with_processed_markers(self):
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(
                    stage,
                    revision,
                    model_version="2.3" if stage == "E1" else None,
                ),
            )
        gate = context.coordinator.build_input_gate(
            "T1", "orchestration/input-gates/processed-marker/input-gate.json"
        )
        context.store.persist_document(gate)
        pending = context.store.issue_work_order(
            run_id=context.state.data["run_id"],
            action="T1",
            state=context.state,
            input_gate=gate,
            h1_workspace=None,
            required_actor=prod.ACTION_CONTRACT["T1"][1],
            inputs={},
        )
        session_path = self.root / "T1/processed-marker/generation-session.json"
        session_path.parent.mkdir(parents=True)
        session_path.write_text(
            rt.canonical_json(
                {
                    "schema_version": "1.0",
                    "stage": "T1",
                    "session_id": "SESSION-T1-PROCESSED-MARKER",
                }
            ),
            encoding="utf-8",
        )
        session = {
            "path": session_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(session_path),
        }
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-E1-PROCESSED-MARKER",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="environment",
            problem="The E1 contract is stale.",
            evidence_ids=["E1-PROCESSED-MARKER"],
            violated_contract="E1 production identity",
            required_revision="Regenerate E1.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data, "returns/RET-E1-PROCESSED-MARKER.json"
        )
        receipt, active = prod.apply_contract_upgrade(
            context,
            request=request,
            old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            session_references=(session,),
        )
        return receipt, active, request, pending, session

    def _run_inventory(self):
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and path.name != "run.lock"
        }

    def _prepared_only_active_refresh(self, marker: str = "0"):
        first_receipt, active, request = self._active_e1_contract_return()
        contract, digest = self._refreshed_contract(marker)
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ), mock.patch.object(
            active.store,
            "persist_state",
            side_effect=RuntimeError("prepared-only crash"),
        ):
            with self.assertRaisesRegex(RuntimeError, "prepared-only crash"):
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=first_receipt.data["new_contract_digest"],
                )
        prepared_path = next(
            path
            for path in (self.root / "orchestration/contract-upgrades").glob(
                "*.prepared.json"
            )
            if not path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            ).exists()
        )
        return (
            first_receipt,
            active,
            request,
            contract,
            digest,
            prepared_path,
        )

    def test_state_is_durable_and_work_order_is_one_shot(self) -> None:
        context = self._context()
        self.assertTrue((self.root / "state" / "revision-000.json").is_file())
        gate, order = prod.issue_stage_work(
            context,
            action="B0",
            inputs={"source_root": "interview"},
        )
        self.assertTrue((self.root / gate.reference["path"]).is_file())
        _, successor = prod.execute_stage_work(
            context,
            work_order=order,
            actor="baseline-controller",
            executor=self._fake_executor("B0", 1),
        )
        self.assertEqual(1, successor.state.data["revision"])
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(successor.state.reference, resumed.state.reference)
        self.assertIn("B0", resumed.state.data["current_stage_completions"])
        with self.assertRaises(store_module.ProductionStoreError):
            prod.execute_stage_work(
                resumed,
                work_order=order,
                actor="baseline-controller",
                executor=self._fake_executor("B0", 2),
            )

    def test_latest_state_rejects_hash_chain_tampering(self) -> None:
        context = self._context()
        _, order = prod.issue_stage_work(
            context,
            action="B0",
            inputs={},
        )
        prod.execute_stage_work(
            context,
            work_order=order,
            actor="baseline-controller",
            executor=self._fake_executor("B0", 1),
        )
        path = self.root / "state" / "revision-001.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["status"] = "rejected"
        path.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaises(store_module.ProductionStoreError):
            prod.resume_production_run(self.root)

    def test_pending_order_blocks_competing_order_and_actor_is_fixed(self) -> None:
        context = self._context()
        _, order = prod.issue_stage_work(
            context, action="B0", inputs={"candidate": 1}
        )
        self.assertEqual("baseline-controller", order.data["required_actor"])
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.issue_stage_work(
                context, action="B0", inputs={"candidate": 2}
            )
        self.assertEqual("PROD_PENDING_WORK_EXISTS", caught.exception.code)
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.issue_stage_work(context, action="legacy-D1", inputs={})

    def test_contract_upgrade_appends_state_and_rejects_bound_work(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(
                    stage,
                    revision,
                    model_version="2.3" if stage == "E1" else None,
                ),
            )
        stale_gate = context.coordinator.build_input_gate(
            "T1", "orchestration/input-gates/stale-t1/input-gate.json"
        )
        context.store.persist_document(stale_gate)
        pending_t1 = context.store.issue_work_order(
            run_id=context.state.data["run_id"],
            action="T1",
            state=context.state,
            input_gate=stale_gate,
            h1_workspace=None,
            required_actor=prod.ACTION_CONTRACT["T1"][1],
            inputs={"candidate": "old-contract"},
        )
        session_path = self.root / "T1/attempt-old/generation-session.json"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        session_path.write_text(
            json.dumps({"schema_version": "1.0", "stage": "T1"}),
            encoding="utf-8",
        )
        session_reference = {
            "path": "T1/attempt-old/generation-session.json",
            "sha256": rt.sha256_file(session_path),
        }
        superseded_session_path = (
            self.root / "orchestration" / "superseded-packages" / "T1"
            / "historical" / "generation-session.json"
        )
        superseded_session_path.parent.mkdir(parents=True)
        superseded_session_path.write_text(
            json.dumps({"schema_version": "1.0", "stage": "T1"}),
            encoding="utf-8",
        )
        historical_e1_session = self.root / (
            "E1/attempt-superseded/generation-session.json"
        )
        historical_e1_session.parent.mkdir(parents=True)
        historical_e1_session.write_text(
            json.dumps({
                "schema_version": "1.0",
                "stage": "E1",
                "session_id": "E1-SUPERSEDED-SESSION",
            }),
            encoding="utf-8",
        )
        archived_completion = self.root / (
            "orchestration/superseded-packages/E1/"
            + "a" * 64
            + "/stage-completion.json"
        )
        archived_completion.parent.mkdir(parents=True)
        archived_completion.write_text(
            json.dumps({
                "stage": "E1",
                "session_id": "E1-SUPERSEDED-SESSION",
            }),
            encoding="utf-8",
        )
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-E1-001",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="environment",
            problem="E1 capability-readiness contract changed.",
            evidence_ids=["E1-CONTRACT-UPGRADE"],
            violated_contract="E1 2.4 capability readiness",
            required_revision=(
                "Use contract "
                + prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            ),
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data, "returns/RET-CONTRACT-UPGRADE-E1-001.json"
        )
        fake_target_data = copy.deepcopy(request_data)
        fake_target_data["target_stage"] = "T1"
        fake_target_data["resume_stage"] = "T1"
        fake_target_data["resume_point"] = "T1"
        fake_target_data["invalidated_stages"] = [
            "T1", "C1", "Q1", "P1", "H1"
        ]
        fake_target = rt.seal_document(
            fake_target_data, "returns/RET-CONTRACT-UPGRADE-FAKE-T1.json"
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_contract_upgrade(
                context,
                request=fake_target,
                old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
                session_references=(session_reference,),
            )
        self.assertEqual(
            "PROD_CONTRACT_UPGRADE_TARGET_MISMATCH", caught.exception.code
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_contract_upgrade(
                context,
                request=request,
                old_contract_digest="8" * 64,
                session_references=(session_reference,),
            )
        self.assertEqual("PROD_CONTRACT_DIGEST_UNBOUND", caught.exception.code)
        forged_session = dict(session_reference)
        forged_session["sha256"] = "9" * 64
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_contract_upgrade(
                context,
                request=request,
                old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
                session_references=(forged_session,),
            )
        self.assertEqual(
            "PROD_CONTRACT_SESSION_INVENTORY_MISMATCH", caught.exception.code
        )
        receipt, migrated = prod.apply_contract_upgrade(
            context,
            request=request,
            old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            session_references=(session_reference,),
        )
        self.assertEqual("complete", receipt.data["status"])
        self.assertEqual(
            ["E1", "T1", "C1", "Q1", "P1", "H1"],
            receipt.data["invalidated_stages"],
        )
        self.assertEqual({"B0", "S1", "W1"}, set(migrated.state.data[
            "current_stage_completions"
        ]))
        self.assertEqual(request.reference, migrated.state.data["active_return"])
        self.assertIsNone(migrated.store.pending_work_order())
        rejected = (
            self.root / "orchestration" / "work-orders"
            / f"{pending_t1.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejected.is_file())
        session_receipt = (
            self.root / "orchestration" / "session-invalidations"
            / f"{rt.canonical_sha256(session_reference)[:24]}.json"
        )
        self.assertTrue(session_receipt.is_file())
        executor = mock.Mock()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.execute_stage_work(
                migrated,
                work_order=pending_t1,
                actor=prod.ACTION_CONTRACT["T1"][1],
                executor=executor,
            )
        self.assertEqual("PROD_WORK_ORDER_REJECTED", caught.exception.code)
        executor.assert_not_called()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(migrated.state.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)

        # Regenerate E1 under the current contract, then seal a stale T1 and
        # migrate again. Previously invalidated sessions/orders must not be
        # re-invalidated or collide with their immutable receipts.
        _, e1_order = prod.issue_stage_work(resumed, action="E1", inputs={})
        _, resumed = prod.execute_stage_work(
            resumed,
            work_order=e1_order,
            actor=prod.ACTION_CONTRACT["E1"][1],
            executor=self._fake_executor("E1", 6),
        )
        _, t1_order = prod.issue_stage_work(resumed, action="T1", inputs={})
        _, resumed = prod.execute_stage_work(
            resumed,
            work_order=t1_order,
            actor=prod.ACTION_CONTRACT["T1"][1],
            executor=self._fake_executor("T1", 7, model_version="2.1"),
        )
        second_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-T1-SECOND",
            origin_kind="stage",
            origin_stage="C1",
            issue_kind="event_timeline",
            problem="The sealed T1 canonical uses a stale production contract.",
            evidence_ids=["T1-STALE-CONTRACT"],
            violated_contract="T1 production qualification",
            required_revision="Regenerate T1 under the current contract.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        second_request = rt.seal_document(
            second_data, "returns/RET-CONTRACT-UPGRADE-T1-SECOND.json"
        )
        second_receipt, second = prod.apply_contract_upgrade(
            resumed,
            request=second_request,
            old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        )
        self.assertNotEqual(receipt.reference, second_receipt.reference)
        self.assertEqual(
            ["T1", "C1", "Q1", "P1", "H1"],
            second_receipt.data["invalidated_stages"],
        )
        self.assertEqual(
            [], second_receipt.data["session_invalidation_receipts"]
        )
        self.assertEqual(
            {"B0", "S1", "W1", "E1"},
            set(second.state.data["current_stage_completions"]),
        )

    def test_active_contract_return_refresh_is_append_only_and_rejects_old_work(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        old_state_path = self.root / active.state.reference["path"]
        old_receipt_path = self.root / first_receipt.reference["path"]
        old_return_path = self.root / request.reference["path"]
        immutable_bodies = {
            old_state_path: old_state_path.read_bytes(),
            old_receipt_path: old_receipt_path.read_bytes(),
            old_return_path: old_return_path.read_bytes(),
        }
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        session_path = self.root / "E1/attempt-refresh/generation-session.json"
        session_path.parent.mkdir(parents=True)
        session_path.write_text(
            rt.canonical_json(
                {
                    "schema_version": "1.0",
                    "stage": "E1",
                    "session_id": "SESSION-E1-REFRESH",
                }
            ),
            encoding="utf-8",
        )
        session_ref = {
            "path": session_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(session_path),
        }
        contract, digest = self._refreshed_contract("a")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with self.assertRaises(prod.ProductionOrchestratorError) as caught:
                prod.resume_production_run(self.root)
            self.assertEqual(
                "PROD_CONTRACT_QUALIFICATION_STALE", caught.exception.code
            )
            migration = prod.resume_production_run_for_contract_upgrade(self.root)
            receipt, refreshed = prod.apply_contract_upgrade(
                migration,
                request=request,
                old_contract_digest=first_receipt.data["new_contract_digest"],
                session_references=(session_ref,),
            )

        self.assertEqual("active_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(1, receipt.data["refresh_generation"])
        self.assertEqual("E1", receipt.data["target_stage"])
        self.assertEqual(first_receipt.reference, receipt.data["prior_qualification"])
        self.assertEqual(request.reference, refreshed.state.data["active_return"])
        self.assertEqual(active.state.reference, refreshed.state.data["previous_state"])
        self.assertEqual(active.state.data["revision"] + 1, refreshed.state.data["revision"])
        self.assertEqual(
            active.state.data["current_stage_completions"],
            refreshed.state.data["current_stage_completions"],
        )
        rejected = (
            self.root
            / "orchestration/work-orders"
            / f"{pending.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejected.is_file())
        self.assertEqual(1, len(receipt.data["session_invalidation_receipts"]))
        for path, body in immutable_bodies.items():
            self.assertEqual(body, path.read_bytes())

    def test_active_contract_return_supports_three_refresh_generations(self) -> None:
        prior_receipt, context, request = self._active_e1_contract_return()
        references = [prior_receipt.reference]
        for generation, marker in enumerate(("a", "b", "c"), 1):
            contract, digest = self._refreshed_contract(marker)
            with mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
            ), mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
            ):
                receipt, context = prod.apply_contract_upgrade(
                    context,
                    request=request,
                    old_contract_digest=prior_receipt.data["new_contract_digest"],
                )
            self.assertEqual(generation, receipt.data["refresh_generation"])
            self.assertEqual(references[-1], receipt.data["prior_qualification"])
            self.assertEqual(request.reference, context.active_return.reference)
            references.append(receipt.reference)
            prior_receipt = receipt
        self.assertEqual(4, len({item["sha256"] for item in references}))

    def test_active_contract_refresh_recovers_prepared_successor(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        contract, digest = self._refreshed_contract("d")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with mock.patch.object(
                active.store,
                "complete_contract_upgrade",
                side_effect=RuntimeError("refresh crash after state write"),
            ):
                with self.assertRaisesRegex(RuntimeError, "refresh crash"):
                    prod.apply_contract_upgrade(
                        active,
                        request=request,
                        old_contract_digest=first_receipt.data["new_contract_digest"],
                    )
            resumed = prod.resume_production_run(self.root)
            recovered = resumed.store.current_contract_upgrade()
            resumed.store._replace(
                self.root / "orchestration/current-contract-upgrade.json",
                {"schema_version": "1.0", "receipt": first_receipt.reference},
            )
            replayed = prod.resume_production_run(self.root)
        self.assertEqual(active.state.data["revision"] + 1, resumed.state.data["revision"])
        self.assertEqual("active_return_refresh", recovered.data["transition_mode"])
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(
            recovered.reference,
            replayed.store.current_contract_upgrade().reference,
        )

    def test_published_generation1_legacy_refresh_resumes_without_rewrite(self) -> None:
        fixture = self._published_generation1_legacy_refresh()
        before = self._run_inventory()
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", fixture["contract"]
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", fixture["digest"]
        ):
            resumed = prod.resume_production_run(self.root)
        self.assertEqual(fixture["context"].state.reference, resumed.state.reference)
        self.assertEqual(fixture["request"].reference, resumed.active_return.reference)
        self.assertEqual(
            fixture["receipt_reference"],
            resumed.store.current_contract_upgrade().reference,
        )
        self.assertEqual(before, self._run_inventory())

    def test_published_generation1_legacy_refresh_rejects_transaction_drift(self) -> None:
        mutants = (
            "migration", "mode", "generation", "prior", "old_digest",
            "new_digest", "inventory", "successor", "request", "markers",
            "plan_unknown", "receipt_unknown",
        )
        for mutant in mutants:
            with self.subTest(mutant=mutant):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-legacy-refresh-{mutant}-"
                )
                self.root = Path(self.temporary.name)
                fixture = self._published_generation1_legacy_refresh()
                plan_data = json.loads(
                    fixture["plan_path"].read_text(encoding="utf-8")
                )
                receipt_data = json.loads(
                    fixture["receipt_path"].read_text(encoding="utf-8")
                )
                if mutant == "migration":
                    plan_data["migration_id"] = "f" * 24
                    receipt_data["migration_id"] = "f" * 24
                elif mutant == "mode":
                    plan_data["transition_mode"] = "new_return"
                    receipt_data["transition_mode"] = "new_return"
                    plan_data["refresh_generation"] = 0
                    receipt_data["refresh_generation"] = 0
                elif mutant == "generation":
                    plan_data["refresh_generation"] = 2
                    receipt_data["refresh_generation"] = 2
                elif mutant == "prior":
                    foreign = {
                        "path": "orchestration/contract-upgrades/foreign.complete.json",
                        "sha256": "f" * 64,
                    }
                    plan_data["prior_qualification"] = foreign
                    receipt_data["prior_qualification"] = foreign
                elif mutant == "old_digest":
                    plan_data["old_contract_digest"] = "f" * 64
                    receipt_data["old_contract_digest"] = "f" * 64
                elif mutant == "new_digest":
                    plan_data["new_contract_digest"] = "f" * 64
                    receipt_data["new_contract_digest"] = "f" * 64
                elif mutant == "inventory":
                    plan_data["inventory_sha256"] = "f" * 64
                    receipt_data["inventory_sha256"] = "f" * 64
                elif mutant == "successor":
                    plan_data["successor_snapshot"]["revision"] += 1
                    successor = {
                        "path": plan_data["successor_state"]["path"],
                        "sha256": rt.canonical_sha256(
                            plan_data["successor_snapshot"]
                        ),
                    }
                    plan_data["successor_state"] = successor
                    receipt_data["successor_state"] = successor
                elif mutant == "request":
                    foreign = {
                        "path": "returns/RET-FOREIGN/return-request.json",
                        "sha256": "f" * 64,
                    }
                    plan_data["return_request"] = foreign
                    receipt_data["return_request"] = foreign
                elif mutant == "markers":
                    receipt_data["session_invalidation_receipts"][0]["sha256"] = (
                        "f" * 64
                    )
                elif mutant == "plan_unknown":
                    plan_data["unexpected"] = True
                elif mutant == "receipt_unknown":
                    receipt_data["unexpected"] = True

                fixture["plan_path"].write_text(
                    rt.canonical_json(plan_data), encoding="utf-8"
                )
                plan_reference = {
                    "path": fixture["plan_reference"]["path"],
                    "sha256": rt.sha256_file(fixture["plan_path"]),
                }
                receipt_data["plan"] = plan_reference
                fixture["receipt_path"].write_text(
                    rt.canonical_json(receipt_data), encoding="utf-8"
                )
                receipt_reference = {
                    "path": fixture["receipt_reference"]["path"],
                    "sha256": rt.sha256_file(fixture["receipt_path"]),
                }
                fixture["context"].store._replace(
                    self.root / "orchestration/current-contract-upgrade.json",
                    {"schema_version": "1.0", "receipt": receipt_reference},
                )
                before = self._run_inventory()
                with mock.patch.object(
                    prod,
                    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT",
                    fixture["contract"],
                ), mock.patch.object(
                    prod,
                    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256",
                    fixture["digest"],
                ):
                    with self.assertRaises(
                        store_module.ProductionStoreError
                    ) as caught:
                        prod.resume_production_run(self.root)
                self.assertEqual(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    caught.exception.code,
                )
                self.assertEqual(before, self._run_inventory())

    def test_active_contract_refresh_rejects_forgery_before_any_write(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        contract, digest = self._refreshed_contract("e")
        before_state = active.store.latest_state()
        before_files = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and path.name != "run.lock"
        }
        fake_target_data = copy.deepcopy(request.data)
        fake_target_data.update(
            {
                "target_stage": "T1",
                "resume_stage": "T1",
                "resume_point": "T1",
                "invalidated_stages": ["T1", "C1", "Q1", "P1", "H1"],
            }
        )
        fake_target = rt.seal_document(
            fake_target_data, "returns/RET-CONTRACT-UPGRADE-FAKE-TARGET.json"
        )
        competing_data = copy.deepcopy(request.data)
        competing_data["return_id"] = "RET-CONTRACT-UPGRADE-COMPETING"
        competing = rt.seal_document(
            competing_data, "returns/RET-CONTRACT-UPGRADE-COMPETING.json"
        )
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            cases = (
                (fake_target, first_receipt.data["new_contract_digest"], "PROD_CONTRACT_UPGRADE_TARGET_MISMATCH"),
                (request, "f" * 64, "PROD_CONTRACT_DIGEST_UNBOUND"),
                (competing, first_receipt.data["new_contract_digest"], "PROD_CONTRACT_UPGRADE_ACTIVE_RETURN_MISMATCH"),
            )
            for candidate, old_digest, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    with self.assertRaises(prod.ProductionOrchestratorError) as caught:
                        prod.apply_contract_upgrade(
                            active,
                            request=candidate,
                            old_contract_digest=old_digest,
                        )
                    self.assertEqual(expected_code, caught.exception.code)
        self.assertEqual(before_state.reference, active.store.latest_state().reference)
        after_files = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and path.name != "run.lock"
        }
        self.assertEqual(before_files, after_files)
        self.assertFalse((self.root / competing.reference["path"]).exists())

    def test_active_refresh_session_receipt_conflict_is_atomic_before_prepared_state(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        session_path = self.root / "E1/attempt-late-conflict/generation-session.json"
        session_path.parent.mkdir(parents=True)
        session_path.write_text(
            rt.canonical_json(
                {
                    "schema_version": "1.0",
                    "stage": "E1",
                    "session_id": "SESSION-E1-LATE-CONFLICT",
                }
            ),
            encoding="utf-8",
        )
        session_ref = {
            "path": session_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(session_path),
        }
        conflict_path = (
            self.root
            / "orchestration/session-invalidations"
            / f"{rt.canonical_sha256(session_ref)[:24]}.json"
        )
        conflict_path.parent.mkdir(parents=True)
        # Valid JSON deliberately lacking `session`, so inventory still sees
        # the active session and the late immutable path remains conflicting.
        conflict_path.write_text(
            rt.canonical_json({"preexisting": "conflict"}), encoding="utf-8"
        )
        before = self._run_inventory()
        state_before = active.store.latest_state()
        coordinator_before = (
            copy.deepcopy(active.coordinator.state),
            copy.deepcopy(active.coordinator.state_reference),
        )
        contract, digest = self._refreshed_contract("9")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with self.assertRaises(store_module.ProductionStoreError) as caught:
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=first_receipt.data["new_contract_digest"],
                    session_references=(session_ref,),
                )
        self.assertEqual("PROD_UNTRUSTED_PROCESSED_MARKER", caught.exception.code)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(state_before.reference, active.store.latest_state().reference)
        self.assertEqual(coordinator_before[0], active.coordinator.state)
        self.assertEqual(coordinator_before[1], active.coordinator.state_reference)

    def test_upgrade_preflight_covers_all_late_immutable_conflict_classes(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        evidence = rt.seal_document(
            {"schema_version": "1.0", "evidence": "preflight-only"},
            "E1/preflight-only/evidence.json",
        )
        active.store.persist_document(evidence)
        active.store._persist_commit_intent(
            pending,
            successor=active.state,
            successor_kind="state",
            evidence=evidence,
        )
        session_path = self.root / "E1/preflight-only/generation-session.json"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        session_path.write_text(
            rt.canonical_json(
                {
                    "schema_version": "1.0",
                    "stage": "E1",
                    "session_id": "SESSION-E1-PREFLIGHT-ONLY",
                }
            ),
            encoding="utf-8",
        )
        session_ref = {
            "path": session_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(session_path),
        }
        captured = {}

        def capture_preflight(**arguments):
            captured.update(arguments)
            raise RuntimeError("captured-before-first-write")

        contract, digest = self._refreshed_contract("8")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ), mock.patch.object(
            active.store,
            "preflight_contract_upgrade_transaction",
            side_effect=capture_preflight,
        ):
            with self.assertRaisesRegex(RuntimeError, "captured-before-first-write"):
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=first_receipt.data["new_contract_digest"],
                    session_references=(session_ref,),
                )

        plan_data = copy.deepcopy(captured["plan"].data)
        completion_reference = active.state.data["current_stage_completions"]["B0"]
        plan_data["completion_references"] = [
            {"stage": "B0", "completion": completion_reference}
        ]
        inventory = {
            key: plan_data[key]
            for key in (
                "session_references",
                "work_order_references",
                "completion_references",
                "pending_work_order",
                "pending_commit_intent",
            )
        }
        plan_data["inventory_sha256"] = rt.canonical_sha256(inventory)
        plan = active.store.build_contract_upgrade_plan(plan_data)
        receipt, derived = active.store.build_contract_upgrade_completion(
            plan, successor=captured["successor"]
        )
        conflict_documents = {
            "order_rejection": next(
                item for item in derived if item.reference["path"].endswith(".rejected.json")
            ),
            "intent_abandonment": next(
                item for item in derived if item.reference["path"].endswith(".abandoned.json")
            ),
            "session_invalidation": next(
                item for item in derived if "session-invalidations" in item.reference["path"]
            ),
            "completion_invalidation": next(
                item for item in derived if "completion-invalidations" in item.reference["path"]
            ),
            "complete_receipt": receipt,
        }
        state_before = active.store.latest_state()
        coordinator_before = (
            copy.deepcopy(active.coordinator.state),
            copy.deepcopy(active.coordinator.state_reference),
        )
        for label, document in conflict_documents.items():
            with self.subTest(conflict=label):
                path = self.root / document.reference["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    rt.canonical_json({"late_conflict": label}), encoding="utf-8"
                )
                before = self._run_inventory()
                with self.assertRaises(store_module.ProductionStoreError) as caught:
                    active.store.preflight_contract_upgrade_transaction(
                        request=request,
                        plan=plan,
                        successor=captured["successor"],
                    )
                self.assertEqual("PROD_IMMUTABLE_CONFLICT", caught.exception.code)
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_before.reference, active.store.latest_state().reference
                )
                self.assertEqual(coordinator_before[0], active.coordinator.state)
                self.assertEqual(
                    coordinator_before[1], active.coordinator.state_reference
                )
                path.unlink()

    def test_full_apply_rejects_untrusted_processed_marker_variants_atomically(self) -> None:
        original_root = self.root
        for kind in ("order", "session"):
            for variant in ("malformed", "unbound", "foreign", "drift"):
                with self.subTest(kind=kind, variant=variant), tempfile.TemporaryDirectory(
                    prefix=f"prod-marker-{kind}-{variant}-"
                ) as temporary:
                    self.root = Path(temporary)
                    first_receipt, active, request = self._active_e1_contract_return()
                    _, pending = prod.issue_stage_work(active, action="E1", inputs={})
                    if kind == "order":
                        marker = (
                            self.root
                            / "orchestration/work-orders"
                            / f"{pending.data['work_id']}.rejected.json"
                        )
                        target = dict(pending.reference)
                    else:
                        session_path = self.root / (
                            f"E1/marker-{variant}/generation-session.json"
                        )
                        session_path.parent.mkdir(parents=True)
                        session_path.write_text(
                            rt.canonical_json(
                                {
                                    "schema_version": "1.0",
                                    "stage": "E1",
                                    "session_id": f"SESSION-E1-{variant.upper()}",
                                }
                            ),
                            encoding="utf-8",
                        )
                        target = {
                            "path": session_path.relative_to(self.root).as_posix(),
                            "sha256": rt.sha256_file(session_path),
                        }
                        marker = (
                            self.root
                            / "orchestration/session-invalidations"
                            / f"{rt.canonical_sha256(target)[:24]}.json"
                        )
                    marker.parent.mkdir(parents=True, exist_ok=True)
                    if variant == "malformed":
                        marker.write_bytes(b"{not-json")
                    else:
                        marker_target = target
                        if variant == "foreign":
                            marker_target = {
                                "path": "foreign/target.json",
                                "sha256": "f" * 64,
                            }
                        marker.write_text(
                            rt.canonical_json(
                                {
                                    "schema_version": "1.0",
                                    "migration_id": "UNBOUND-MIGRATION",
                                    (
                                        "work_order" if kind == "order" else "session"
                                    ): marker_target,
                                    "reason": "contract_upgrade",
                                    "successor_state": {
                                        "path": "state/revision-999.json",
                                        "sha256": (
                                            "d" * 64 if variant == "drift" else "e" * 64
                                        ),
                                    },
                                    "status": (
                                        "rejected" if kind == "order" else "invalidated"
                                    ),
                                }
                            ),
                            encoding="utf-8",
                        )
                    before = self._run_inventory()
                    state_before = active.store.latest_state()
                    qualification_before = (
                        self.root
                        / "orchestration/current-contract-upgrade.json"
                    ).read_bytes()
                    coordinator_before = (
                        copy.deepcopy(active.coordinator.state),
                        copy.deepcopy(active.coordinator.state_reference),
                    )
                    contract, digest = self._refreshed_contract("7")
                    with mock.patch.object(
                        prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                    ), mock.patch.object(
                        prod,
                        "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256",
                        digest,
                    ):
                        with self.assertRaises(
                            store_module.ProductionStoreError
                        ) as caught:
                            prod.apply_contract_upgrade(
                                active,
                                request=request,
                                old_contract_digest=first_receipt.data[
                                    "new_contract_digest"
                                ],
                            )
                    self.assertEqual(
                        "PROD_UNTRUSTED_PROCESSED_MARKER", caught.exception.code
                    )
                    self.assertEqual(before, self._run_inventory())
                    self.assertEqual(
                        state_before.reference, active.store.latest_state().reference
                    )
                    self.assertEqual(
                        qualification_before,
                        (
                            self.root
                            / "orchestration/current-contract-upgrade.json"
                        ).read_bytes(),
                    )
                    self.assertEqual(coordinator_before[0], active.coordinator.state)
                    self.assertEqual(
                        coordinator_before[1], active.coordinator.state_reference
                    )
        self.root = original_root

    def test_full_apply_rejects_untrusted_completion_and_intent_markers(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        evidence = rt.seal_document(
            {"schema_version": "1.0", "evidence": "intent-marker"},
            "E1/intent-marker/evidence.json",
        )
        active.store.persist_document(evidence)
        intent = active.store._persist_commit_intent(
            pending,
            successor=active.state,
            successor_kind="state",
            evidence=evidence,
        )
        completion = active.state.data["current_stage_completions"]["B0"]
        markers = (
            self.root
            / "orchestration/completion-invalidations"
            / f"{rt.canonical_sha256(['B0', completion])[:24]}.json",
            self.root
            / "orchestration/commit-intents"
            / f"{Path(intent.reference['path']).stem}.abandoned.json",
        )
        for marker in markers:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                rt.canonical_json({"unbound_processed_marker": marker.name}),
                encoding="utf-8",
            )
            before = self._run_inventory()
            state_before = active.store.latest_state()
            qualification_before = (
                self.root / "orchestration/current-contract-upgrade.json"
            ).read_bytes()
            coordinator_before = copy.deepcopy(active.coordinator.state)
            contract, digest = self._refreshed_contract("6")
            with mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
            ), mock.patch.object(
                prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
            ):
                with self.assertRaises(store_module.ProductionStoreError) as caught:
                    prod.apply_contract_upgrade(
                        active,
                        request=request,
                        old_contract_digest=first_receipt.data["new_contract_digest"],
                    )
            self.assertEqual("PROD_UNTRUSTED_PROCESSED_MARKER", caught.exception.code)
            self.assertEqual(before, self._run_inventory())
            self.assertEqual(state_before.reference, active.store.latest_state().reference)
            self.assertEqual(
                qualification_before,
                (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
            )
            self.assertEqual(coordinator_before, active.coordinator.state)
            marker.unlink()

    def test_full_apply_rejects_drifted_trusted_order_and_session_markers(self) -> None:
        original_root = self.root
        for kind in ("order", "session"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(
                prefix=f"prod-trusted-drift-{kind}-"
            ) as temporary:
                self.root = Path(temporary)
                receipt, active, request, pending, session = (
                    self._active_e1_contract_return_with_processed_markers()
                )
                trusted = active.store.trusted_contract_upgrade_markers()
                if kind == "order":
                    marker = (
                        self.root
                        / "orchestration/work-orders"
                        / f"{pending.data['work_id']}.rejected.json"
                    )
                    self.assertIn(
                        marker.relative_to(self.root).as_posix(),
                        trusted["work_order_rejections"],
                    )
                else:
                    marker = (
                        self.root
                        / "orchestration/session-invalidations"
                        / f"{rt.canonical_sha256(session)[:24]}.json"
                    )
                    self.assertIn(
                        marker.relative_to(self.root).as_posix(),
                        trusted["session_invalidations"],
                    )
                marker.write_bytes(marker.read_bytes() + b"\n")
                before = self._run_inventory()
                state_before = active.store.latest_state()
                qualification_before = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                coordinator_before = copy.deepcopy(active.coordinator.state)
                contract, digest = self._refreshed_contract("5")
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    with self.assertRaises(store_module.ProductionStoreError):
                        prod.apply_contract_upgrade(
                            active,
                            request=request,
                            old_contract_digest=receipt.data["new_contract_digest"],
                        )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_before.reference, active.store.latest_state().reference
                )
                self.assertEqual(
                    qualification_before,
                    (
                        self.root / "orchestration/current-contract-upgrade.json"
                    ).read_bytes(),
                )
                self.assertEqual(coordinator_before, active.coordinator.state)
        self.root = original_root

    def test_legacy_complete_upgrade_receipt_remains_trusted(self) -> None:
        receipt, active, request, pending, session = (
            self._active_e1_contract_return_with_processed_markers()
        )
        plan_reference = receipt.data["plan"]
        plan_path = self.root / plan_reference["path"]
        legacy_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        for field in (
            "transition_mode",
            "refresh_generation",
            "prior_qualification",
            "target_stage",
            "stale_identity",
            "production_contract",
            "inventory_sha256",
            "superseded_return",
            "post_upgrade_documents",
            "post_upgrade_work_order",
            "post_upgrade_inputs",
        ):
            legacy_plan.pop(field, None)
        plan_path.write_text(rt.canonical_json(legacy_plan), encoding="utf-8")
        legacy_plan_reference = {
            "path": plan_reference["path"],
            "sha256": rt.sha256_file(plan_path),
        }
        legacy = copy.deepcopy(receipt.data)
        for field in (
            "transition_mode",
            "refresh_generation",
            "prior_qualification",
            "target_stage",
            "stale_identity",
            "production_contract",
            "inventory_sha256",
            "commit_intent_abandonment_receipts",
            "superseded_return",
            "post_upgrade_documents",
            "post_upgrade_work_order",
        ):
            legacy.pop(field, None)
        legacy["plan"] = legacy_plan_reference
        receipt_path = self.root / receipt.reference["path"]
        receipt_path.write_text(rt.canonical_json(legacy), encoding="utf-8")
        legacy_reference = {
            "path": receipt.reference["path"],
            "sha256": rt.sha256_file(receipt_path),
        }
        active.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": legacy_reference},
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(active.state.reference, resumed.state.reference)
        trusted = resumed.store.trusted_contract_upgrade_markers()
        self.assertIn(
            (
                self.root
                / "orchestration/work-orders"
                / f"{pending.data['work_id']}.rejected.json"
            ).relative_to(self.root).as_posix(),
            trusted["work_order_rejections"],
        )
        self.assertIn(
            (
                self.root
                / "orchestration/session-invalidations"
                / f"{rt.canonical_sha256(session)[:24]}.json"
            ).relative_to(self.root).as_posix(),
            trusted["session_invalidations"],
        )

    def test_full_apply_rejects_state_bound_self_consistent_orphan_complete(self) -> None:
        first_receipt, active, request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        session_path = self.root / "E1/orphan-complete/generation-session.json"
        session_path.parent.mkdir(parents=True)
        session_path.write_text(
            rt.canonical_json(
                {
                    "schema_version": "1.0",
                    "stage": "E1",
                    "session_id": "SESSION-E1-ORPHAN-COMPLETE",
                }
            ),
            encoding="utf-8",
        )
        session = {
            "path": session_path.relative_to(self.root).as_posix(),
            "sha256": rt.sha256_file(session_path),
        }
        captured = {}

        def capture(**arguments):
            captured.update(arguments)
            raise RuntimeError("capture-orphan-plan")

        contract, digest = self._refreshed_contract("4")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ), mock.patch.object(
            active.store,
            "preflight_contract_upgrade_transaction",
            side_effect=capture,
        ):
            with self.assertRaisesRegex(RuntimeError, "capture-orphan-plan"):
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=first_receipt.data["new_contract_digest"],
                    session_references=(session,),
                )
        orphan_data = copy.deepcopy(captured["plan"].data)
        orphan_data["migration_id"] = "ORPHAN-SELF-CONSISTENT"
        orphan_data["successor_state"] = dict(active.state.reference)
        orphan_data["successor_snapshot"] = copy.deepcopy(active.state.data)
        orphan_plan = active.store.build_contract_upgrade_plan(orphan_data)
        orphan_receipt, derived = active.store.build_contract_upgrade_completion(
            orphan_plan, successor=active.state
        )
        active.store.persist_document(orphan_plan)
        for document in derived:
            active.store.persist_document(document)
        active.store.persist_document(orphan_receipt)
        before = self._run_inventory()
        state_before = active.store.latest_state()
        qualification_before = (
            self.root / "orchestration/current-contract-upgrade.json"
        ).read_bytes()
        coordinator_before = copy.deepcopy(active.coordinator.state)
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with self.assertRaises(store_module.ProductionStoreError) as caught:
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=first_receipt.data["new_contract_digest"],
                )
        self.assertEqual("PROD_UNTRUSTED_PROCESSED_MARKER", caught.exception.code)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(state_before.reference, active.store.latest_state().reference)
        self.assertEqual(
            qualification_before,
            (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
        )
        self.assertEqual(coordinator_before, active.coordinator.state)

    def test_full_apply_rejects_missing_drifted_and_cyclic_prior_chain(self) -> None:
        original_root = self.root
        for variant in ("missing", "hash_drift", "cycle"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(
                prefix=f"prod-prior-{variant}-"
            ) as temporary:
                self.root = Path(temporary)
                receipt, active, request = self._active_e1_contract_return()
                receipt_path = self.root / receipt.reference["path"]
                mutated = copy.deepcopy(receipt.data)
                bootstrap = mutated["prior_qualification"]
                if variant == "missing":
                    mutated["prior_qualification"] = {
                        "path": "orchestration/contract-upgrades/missing.complete.json",
                        "sha256": "1" * 64,
                    }
                elif variant == "hash_drift":
                    mutated["prior_qualification"] = {
                        **bootstrap,
                        "sha256": "2" * 64,
                    }
                else:
                    # A content-addressed physical cycle cannot have a valid
                    # fixed-point hash; this self-edge therefore fails closed
                    # as the only representable cyclic-chain mutation.
                    mutated["prior_qualification"] = dict(receipt.reference)
                receipt_path.write_text(rt.canonical_json(mutated), encoding="utf-8")
                mutated_reference = {
                    "path": receipt.reference["path"],
                    "sha256": rt.sha256_file(receipt_path),
                }
                active.store._replace(
                    self.root / "orchestration/current-contract-upgrade.json",
                    {"schema_version": "1.0", "receipt": mutated_reference},
                )
                before = self._run_inventory()
                state_before = active.store.latest_state()
                pointer_before = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                coordinator_before = copy.deepcopy(active.coordinator.state)
                contract, digest = self._refreshed_contract("3")
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    with self.assertRaises(store_module.ProductionStoreError) as caught:
                        prod.apply_contract_upgrade(
                            active,
                            request=request,
                            old_contract_digest=mutated["new_contract_digest"],
                        )
                self.assertEqual(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    caught.exception.code,
                )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_before.reference, active.store.latest_state().reference
                )
                self.assertEqual(
                    pointer_before,
                    (
                        self.root / "orchestration/current-contract-upgrade.json"
                    ).read_bytes(),
                )
                self.assertEqual(coordinator_before, active.coordinator.state)
        self.root = original_root

    def test_modern_upgrade_cannot_terminate_without_prior_bootstrap(self) -> None:
        receipt, active, request = self._active_e1_contract_return()
        plan_path = self.root / receipt.data["plan"]["path"]
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        plan_data["prior_qualification"] = None
        plan = active.store.build_contract_upgrade_plan(plan_data)
        successor = active.store.load_document(plan.data["successor_state"])
        modern_receipt, _derived = active.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        plan_path.write_text(rt.canonical_json(plan.data), encoding="utf-8")
        receipt_path = self.root / receipt.reference["path"]
        receipt_path.write_text(
            rt.canonical_json(modern_receipt.data), encoding="utf-8"
        )
        active.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": modern_receipt.reference},
        )
        before = self._run_inventory()
        state_before = active.store.latest_state()
        pointer_before = (
            self.root / "orchestration/current-contract-upgrade.json"
        ).read_bytes()
        coordinator_before = copy.deepcopy(active.coordinator.state)
        contract, digest = self._refreshed_contract("2")
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with self.assertRaises(store_module.ProductionStoreError) as caught:
                prod.apply_contract_upgrade(
                    active,
                    request=request,
                    old_contract_digest=receipt.data["new_contract_digest"],
                )
        self.assertEqual(
            "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", caught.exception.code
        )
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(state_before.reference, active.store.latest_state().reference)
        self.assertEqual(
            pointer_before,
            (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
        )
        self.assertEqual(coordinator_before, active.coordinator.state)

    def test_modern_upgrade_replay_rejects_fake_request_equal_state_and_migration_id(self) -> None:
        original_root = self.root
        for variant in ("fake_request", "predecessor_equals_successor", "migration_id"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(
                prefix=f"prod-replay-{variant}-"
            ) as temporary:
                self.root = Path(temporary)
                receipt, active, request = self._active_e1_contract_return()
                original_plan = active.store.load_document(receipt.data["plan"])
                fake_request_data = copy.deepcopy(request.data)
                fake_request_data["return_id"] = f"RET-FAKE-{variant.upper()}"
                fake_request = rt.seal_document(
                    fake_request_data, f"returns/RET-FAKE-{variant.upper()}.json"
                )
                active.store.persist_document(fake_request)
                plan_data = copy.deepcopy(original_plan.data)
                plan_data["return_request"] = fake_request.reference
                plan_data.update(
                    {
                        "session_references": [],
                        "work_order_references": [],
                        "completion_references": [],
                        "pending_work_order": None,
                        "pending_commit_intent": None,
                    }
                )
                plan_data["inventory_sha256"] = rt.canonical_sha256(
                    {
                        key: plan_data[key]
                        for key in (
                            "session_references",
                            "work_order_references",
                            "completion_references",
                            "pending_work_order",
                            "pending_commit_intent",
                        )
                    }
                )
                if variant == "predecessor_equals_successor":
                    plan_data["predecessor_state"] = active.state.reference
                    plan_data["successor_state"] = active.state.reference
                    plan_data["successor_snapshot"] = copy.deepcopy(active.state.data)
                    plan_data["transition_mode"] = "active_return_refresh"
                    plan_data["refresh_generation"] = 1
                migration_id = rt.canonical_sha256(
                    [
                        plan_data["predecessor_state"],
                        fake_request.reference,
                        plan_data["old_contract_digest"],
                        plan_data["new_contract_digest"],
                    ]
                )[:24]
                plan_data["migration_id"] = (
                    "WRONG-MIGRATION-ID" if variant == "migration_id" else migration_id
                )
                fake_plan = active.store.build_contract_upgrade_plan(plan_data)
                fake_successor = active.store.load_document(
                    fake_plan.data["successor_state"]
                )
                fake_receipt, derived = active.store.build_contract_upgrade_completion(
                    fake_plan, successor=fake_successor
                )
                active.store.persist_document(fake_plan)
                for document in derived:
                    active.store.persist_document(document)
                active.store.persist_document(fake_receipt)
                active.store._replace(
                    self.root / "orchestration/current-contract-upgrade.json",
                    {"schema_version": "1.0", "receipt": fake_receipt.reference},
                )
                before = self._run_inventory()
                state_before = active.store.latest_state()
                pointer_before = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                coordinator_before = copy.deepcopy(active.coordinator.state)
                contract, digest = self._refreshed_contract("1")
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    with self.assertRaises(store_module.ProductionStoreError) as caught:
                        prod.apply_contract_upgrade(
                            active,
                            request=request,
                            old_contract_digest=fake_receipt.data[
                                "new_contract_digest"
                            ],
                        )
                self.assertEqual(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    caught.exception.code,
                )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_before.reference, active.store.latest_state().reference
                )
                self.assertEqual(
                    pointer_before,
                    (
                        self.root / "orchestration/current-contract-upgrade.json"
                    ).read_bytes(),
                )
                self.assertEqual(coordinator_before, active.coordinator.state)
        self.root = original_root

    def test_bootstrap_shape_identity_and_digest_are_strict(self) -> None:
        original_root = self.root
        for variant in ("extra", "missing", "digest_drift"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(
                prefix=f"prod-bootstrap-{variant}-"
            ) as temporary:
                self.root = Path(temporary)
                context = self._context()
                bootstrap = context.store.current_contract_upgrade()
                data = copy.deepcopy(bootstrap.data)
                if variant == "extra":
                    data["unexpected"] = True
                elif variant == "missing":
                    data.pop("invalidated_stages")
                else:
                    data["old_contract_digest"] = "0" * 64
                path = self.root / bootstrap.reference["path"]
                path.write_text(rt.canonical_json(data), encoding="utf-8")
                reference = {
                    "path": bootstrap.reference["path"],
                    "sha256": rt.sha256_file(path),
                }
                context.store._replace(
                    self.root / "orchestration/current-contract-upgrade.json",
                    {"schema_version": "1.0", "receipt": reference},
                )
                before = self._run_inventory()
                pointer_before = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                with self.assertRaises(store_module.ProductionStoreError) as caught:
                    prod.resume_production_run(self.root)
                self.assertEqual(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    caught.exception.code,
                )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    pointer_before,
                    (
                        self.root / "orchestration/current-contract-upgrade.json"
                    ).read_bytes(),
                )
                self.assertEqual(0, context.coordinator.state["revision"])
        self.root = original_root

    def test_bootstrap_qualification_seals_complete_production_contract(self) -> None:
        context = self._context()
        qualification = context.store.current_contract_upgrade()
        self.assertEqual(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT,
            qualification.data["production_contract"],
        )
        self.assertEqual(
            qualification.data["new_contract_digest"],
            rt.canonical_sha256(qualification.data["production_contract"]),
        )

        data = copy.deepcopy(qualification.data)
        data["production_contract"]["T1"]["identity_bindings"]["runtime"][
            "sha256"
        ] = "f" * 64
        path = self.root / qualification.reference["path"]
        path.write_text(rt.canonical_json(data), encoding="utf-8")
        reference = {
            "path": qualification.reference["path"],
            "sha256": rt.sha256_file(path),
        }
        context.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": reference},
        )
        before = self._run_inventory()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.resume_production_run(self.root)
        self.assertEqual(
            "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", caught.exception.code
        )
        self.assertEqual(before, self._run_inventory())

    def test_prepared_only_recovery_replays_successor_request_and_identity(self) -> None:
        original_root = self.root
        variants = (
            "active_return",
            "revision",
            "previous_state",
            "successor_path",
            "fake_request",
            "migration_id",
            "prior_null",
            "prior_fork",
            "source_identity",
        )
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(
                prefix=f"prod-prepared-{variant}-"
            ) as temporary:
                self.root = Path(temporary)
                (
                    first_receipt,
                    active,
                    request,
                    contract,
                    digest,
                    prepared_path,
                ) = self._prepared_only_active_refresh("0")
                data = json.loads(prepared_path.read_text(encoding="utf-8"))
                if variant in {"active_return", "revision", "previous_state", "successor_path"}:
                    snapshot = copy.deepcopy(data["successor_snapshot"])
                    if variant == "active_return":
                        snapshot["active_return"] = {
                            "path": "returns/foreign.json", "sha256": "a" * 64
                        }
                    elif variant == "revision":
                        snapshot["revision"] += 1
                    elif variant == "previous_state":
                        snapshot["previous_state"] = {
                            "path": "state/revision-999.json", "sha256": "b" * 64
                        }
                    data["successor_snapshot"] = snapshot
                    successor_path = data["successor_state"]["path"]
                    if variant == "successor_path":
                        successor_path = "state/revision-999.json"
                    data["successor_state"] = {
                        "path": successor_path,
                        "sha256": rt.canonical_sha256(snapshot),
                    }
                elif variant == "fake_request":
                    fake_data = copy.deepcopy(request.data)
                    fake_data["return_id"] = "RET-PREPARED-FAKE"
                    fake = rt.seal_document(
                        fake_data, "returns/RET-PREPARED-FAKE.json"
                    )
                    active.store.persist_document(fake)
                    data["return_request"] = fake.reference
                elif variant == "migration_id":
                    data["migration_id"] = "WRONG-PREPARED-ID"
                elif variant == "prior_null":
                    data["prior_qualification"] = None
                elif variant == "prior_fork":
                    data["prior_qualification"] = {
                        "path": "orchestration/contract-upgrades/fork.complete.json",
                        "sha256": "c" * 64,
                    }
                else:
                    data["stale_identity"] = {
                        **data["stale_identity"], "identity_error": "DRIFTED"
                    }
                data["successor_snapshot"] = data.get(
                    "successor_snapshot", {}
                )
                prepared_path.write_text(rt.canonical_json(data), encoding="utf-8")
                before = self._run_inventory()
                state_pointer_before = (
                    self.root / "orchestration/current-state.json"
                ).read_bytes()
                qualification_pointer_before = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                coordinator_before = copy.deepcopy(active.coordinator.state)
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    with self.assertRaises(
                        (store_module.ProductionStoreError, prod.ProductionOrchestratorError)
                    ):
                        prod.resume_production_run(self.root)
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_pointer_before,
                    (self.root / "orchestration/current-state.json").read_bytes(),
                )
                self.assertEqual(
                    qualification_pointer_before,
                    (
                        self.root / "orchestration/current-contract-upgrade.json"
                    ).read_bytes(),
                )
                self.assertEqual(coordinator_before, active.coordinator.state)
        self.root = original_root

    def test_multiple_prepared_one_bad_commits_nothing(self) -> None:
        (
            first_receipt,
            active,
            request,
            contract,
            digest,
            first_path,
        ) = self._prepared_only_active_refresh("f")
        first_data = json.loads(first_path.read_text(encoding="utf-8"))
        bad = copy.deepcopy(first_data)
        bad["migration_id"] = "BAD-FORK-PREPARED"
        bad_path = (
            self.root
            / "orchestration/contract-upgrades/BAD-FORK-PREPARED.prepared.json"
        )
        bad_path.write_text(rt.canonical_json(bad), encoding="utf-8")
        before = self._run_inventory()
        state_pointer_before = (
            self.root / "orchestration/current-state.json"
        ).read_bytes()
        qualification_pointer_before = (
            self.root / "orchestration/current-contract-upgrade.json"
        ).read_bytes()
        coordinator_before = copy.deepcopy(active.coordinator.state)
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            with self.assertRaises(store_module.ProductionStoreError):
                prod.resume_production_run(self.root)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(
            state_pointer_before,
            (self.root / "orchestration/current-state.json").read_bytes(),
        )
        self.assertEqual(
            qualification_pointer_before,
            (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
        )
        self.assertEqual(coordinator_before, active.coordinator.state)

    def test_recovery_accepts_all_derived_and_complete_with_old_pointer(self) -> None:
        receipt, active, request, pending, session = (
            self._active_e1_contract_return_with_processed_markers()
        )
        prior = receipt.data["prior_qualification"]
        active.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": prior},
        )
        immutable_before = {
            path: path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
            and path.name != "run.lock"
            and path.name not in {
                "current-state.json", "current-contract-upgrade.json"
            }
        }
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(active.state.reference, resumed.state.reference)
        self.assertEqual(
            receipt.reference,
            resumed.store.current_contract_upgrade().reference,
        )
        for path, body in immutable_before.items():
            self.assertEqual(body, path.read_bytes())

    def test_recovery_accepts_exact_mid_derived_prefix_without_complete(self) -> None:
        receipt, active, request, pending, session = (
            self._active_e1_contract_return_with_processed_markers()
        )
        prior = receipt.data["prior_qualification"]
        active.store._replace(
            self.root / "orchestration/current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": prior},
        )
        complete_path = self.root / receipt.reference["path"]
        complete_path.unlink()
        all_derived = (
            receipt.data["work_order_invalidation_receipts"]
            + receipt.data["session_invalidation_receipts"]
            + receipt.data["completion_invalidation_receipts"]
            + receipt.data.get("commit_intent_abandonment_receipts", [])
        )
        # Preserve a deterministic non-empty prefix and remove the suffix.
        self.assertGreaterEqual(len(all_derived), 2)
        for reference in all_derived[1:]:
            (self.root / reference["path"]).unlink()
        prefix_path = self.root / all_derived[0]["path"]
        prefix_body = prefix_path.read_bytes()
        state_pointer_before = (
            self.root / "orchestration/current-state.json"
        ).read_bytes()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(active.state.reference, resumed.state.reference)
        self.assertEqual(state_pointer_before, (
            self.root / "orchestration/current-state.json"
        ).read_bytes())
        self.assertEqual(prefix_body, prefix_path.read_bytes())
        self.assertTrue(complete_path.is_file())
        self.assertEqual(
            receipt.reference,
            resumed.store.current_contract_upgrade().reference,
        )
        for reference in all_derived:
            self.assertTrue((self.root / reference["path"]).is_file())

    def test_first_stage_return_atomically_rejects_c1_and_issues_t1(self) -> None:
        context, pending, request = self._pending_c1_stage_return()
        prior = context.store.current_contract_upgrade()
        receipt, returned, gate, order = prod.apply_stage_return(
            context,
            work_order=pending,
            request=request,
            actor=prod.ACTION_CONTRACT["C1"][1],
            inputs={"reason": "repair T1 information flow"},
        )

        self.assertEqual("stage_return", receipt.data["transition_mode"])
        self.assertEqual(prior.reference, receipt.data["prior_qualification"])
        self.assertEqual("T1", receipt.data["target_stage"])
        self.assertEqual(request.reference, returned.state.data["active_return"])
        self.assertEqual(
            {"B0", "S1", "W1", "E1"},
            set(returned.state.data["current_stage_completions"]),
        )
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual("T1", order.data["action"])
        self.assertEqual(returned.state.reference, order.data["state"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        self.assertEqual(
            prior.reference,
            order.data["inputs"]["_contract_qualification"][
                "contract_upgrade_receipt"
            ],
        )
        rejected = (
            self.root
            / "orchestration/work-orders"
            / f"{pending.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejected.is_file())
        self.assertIn(
            rejected.relative_to(self.root).as_posix(),
            returned.store.trusted_contract_upgrade_markers()[
                "work_order_rejections"
            ],
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(returned.state.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)

        _, completed = prod.execute_stage_work(
            resumed,
            work_order=order,
            actor=prod.ACTION_CONTRACT["T1"][1],
            executor=self._fake_executor(
                "T1", resumed.state.data["revision"] + 1
            ),
        )
        self.assertIsNone(completed.active_return)
        self.assertIn("T1", completed.state.data["current_stage_completions"])

    def test_first_stage_return_rejects_bad_actor_and_late_collision_without_writes(self) -> None:
        context, pending, request = self._pending_c1_stage_return()
        before = self._run_inventory()
        coordinator_before = copy.deepcopy(context.coordinator.state)
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_stage_return(
                context,
                work_order=pending,
                request=request,
                actor="not-c1-owner",
                inputs={},
            )
        self.assertEqual("PROD_WORK_ACTOR_MISMATCH", caught.exception.code)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(coordinator_before, context.coordinator.state)

        conflict = (
            self.root
            / "orchestration/input-gates"
            / f"revision-{context.state.data['revision'] + 1:03d}-T1"
            / "input-gate.json"
        )
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_text(rt.canonical_json({"conflict": True}), encoding="utf-8")
        before = self._run_inventory()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.apply_stage_return(
                context,
                work_order=pending,
                request=request,
                actor=prod.ACTION_CONTRACT["C1"][1],
                inputs={},
            )
        self.assertEqual("PROD_IMMUTABLE_CONFLICT", caught.exception.code)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(coordinator_before, context.coordinator.state)

    def test_first_stage_return_recovers_prepared_and_mid_derived_prefix(self) -> None:
        context, pending, request, plan, successor = (
            self._prepared_only_stage_return()
        )
        resumed = prod.resume_production_run(self.root)
        qualification = resumed.store.current_contract_upgrade()
        self.assertEqual("stage_return", qualification.data["transition_mode"])
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(
            plan.data["post_upgrade_work_order"],
            resumed.store.pending_work_order().reference,
        )
        self.assertTrue(
            (
                self.root
                / "orchestration/work-orders"
                / f"{pending.data['work_id']}.rejected.json"
            ).is_file()
        )

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory(
            prefix="prod-stage-return-prefix-"
        )
        self.root = Path(self.temporary.name)
        context, _, request, plan, successor = self._prepared_only_stage_return()
        receipt, derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.persist_state(successor)
        for document in derived[:-1]:
            context.store.persist_document(document)
        prefix_inventory = self._run_inventory()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(
            receipt.reference,
            resumed.store.current_contract_upgrade().reference,
        )
        for path, body in prefix_inventory.items():
            if path not in {
                "orchestration/current-state.json",
                "orchestration/current-contract-upgrade.json",
                "orchestration/current-work-order.json",
            }:
                self.assertEqual(body, (self.root / path).read_bytes())

    def test_first_stage_return_recovers_complete_receipt_pointer_gap(self) -> None:
        context, _, request, plan, successor = self._prepared_only_stage_return()
        prior = context.store.current_contract_upgrade()
        receipt, derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.persist_state(successor)
        for document in derived:
            context.store.persist_document(document)
        context.store.persist_document(receipt)
        context.store._replace(
            self.root / "orchestration/current-work-order.json",
            {
                "schema_version": "2.0",
                "work_order": plan.data["post_upgrade_work_order"],
            },
        )
        self.assertEqual(
            prior.reference, context.store.current_contract_upgrade().reference
        )
        before = self._run_inventory()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(
            receipt.reference,
            resumed.store.current_contract_upgrade().reference,
        )
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        for path, body in before.items():
            if path != "orchestration/current-contract-upgrade.json":
                self.assertEqual(body, (self.root / path).read_bytes())

    def test_active_e1_return_escalates_atomically_to_b0_and_issues_exact_order(self) -> None:
        prior_receipt, active, old_request = self._active_e1_contract_return()
        _, old_order = prod.issue_stage_work(active, action="E1", inputs={})
        intent_evidence = rt.seal_document(
            {"schema_version": "1.0", "evidence": "escalation-intent"},
            "E1/escalation/intent-evidence.json",
        )
        active.store.persist_document(intent_evidence)
        old_intent = active.store._persist_commit_intent(
            old_order, successor=active.state, successor_kind="state",
            evidence=intent_evidence,
        )
        for stage in ("B0", "S1", "W1", "E1", "T1"):
            session_path = self.root / stage / "escalation/generation-session.json"
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session_path.write_text(
                rt.canonical_json(
                    {"stage": stage, "session_id": f"ACTIVE-{stage}-ESCALATION"}
                ), encoding="utf-8"
            )
        old_bytes = {
            self.root / old_request.reference["path"]:
                (self.root / old_request.reference["path"]).read_bytes(),
            self.root / prior_receipt.reference["path"]:
                (self.root / prior_receipt.reference["path"]).read_bytes(),
            self.root / active.state.reference["path"]:
                (self.root / active.state.reference["path"]).read_bytes(),
        }
        new_request = self._escalation_request(old_request)
        receipt, escalated, gate, order = prod.apply_active_return_escalation(
            active, request=new_request, actor="production-orchestrator",
            inputs={"reason": "B0 implementation stale"},
        )
        self.assertEqual("active_return_escalation", receipt.data["transition_mode"])
        self.assertEqual(old_request.reference, receipt.data["superseded_return"])
        self.assertEqual("B0", receipt.data["target_stage"])
        self.assertEqual(new_request.reference, escalated.state.data["active_return"])
        self.assertEqual({}, escalated.state.data["current_stage_completions"])
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual("B0", order.data["action"])
        self.assertEqual(escalated.state.reference, order.data["state"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        rejected = (
            self.root / "orchestration/work-orders"
            / f"{old_order.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejected.is_file())
        self.assertEqual(5, len(receipt.data["session_invalidation_receipts"]))
        self.assertEqual(3, len(receipt.data["completion_invalidation_receipts"]))
        self.assertEqual(1, len(receipt.data["commit_intent_abandonment_receipts"]))
        self.assertTrue(
            (self.root / "orchestration/commit-intents"
             / f"{Path(old_intent.reference['path']).stem}.abandoned.json").is_file()
        )
        plan = escalated.store.load_document(receipt.data["plan"])
        self.assertEqual(list(prod.STAGE_ORDER), plan.data["invalidated_stages"])
        self.assertEqual(
            {"B0", "S1", "W1"},
            {item["stage"] for item in plan.data["completion_references"]},
        )
        for path, body in old_bytes.items():
            self.assertEqual(body, path.read_bytes())
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(escalated.state.reference, resumed.state.reference)
        self.assertEqual(new_request.reference, resumed.active_return.reference)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)

    def test_active_return_escalation_rejects_invalid_routes_without_side_effects(self) -> None:
        _, active, old_request = self._active_e1_contract_return()
        prod.issue_stage_work(active, action="E1", inputs={})
        valid = self._escalation_request(old_request)
        wrong_origin_data = copy.deepcopy(valid.data)
        wrong_origin_data["origin_stage"] = "T1"
        wrong_origin = rt.seal_document(
            wrong_origin_data, "returns/RET-ESCALATE-WRONG-ORIGIN.json"
        )
        wrong_issue_data = copy.deepcopy(valid.data)
        wrong_issue_data["owner_basis"] = wrong_issue_data["owner_basis"].replace(
            "baseline_packaging", "storyline"
        )
        wrong_issue = rt.seal_document(
            wrong_issue_data, "returns/RET-ESCALATE-WRONG-ISSUE.json"
        )
        wrong_suffix_data = copy.deepcopy(valid.data)
        wrong_suffix_data["invalidated_stages"] = list(prod.STAGE_ORDER[:-1])
        wrong_suffix = rt.seal_document(
            wrong_suffix_data, "returns/RET-ESCALATE-WRONG-SUFFIX.json"
        )
        tampered_data = copy.deepcopy(valid.data)
        tampered_data["problem"] = "tampered after sealing"
        tampered = rt.SealedDocument(tampered_data, valid.reference)
        same = self._escalation_request(
            old_request, target="E1", return_id="RET-ESCALATE-SAME"
        )
        later = self._escalation_request(
            old_request, target="T1", return_id="RET-ESCALATE-LATER"
        )
        before = self._run_inventory()
        coordinator_before = copy.deepcopy(active.coordinator.state)
        cases = (
            (valid, "not-production-orchestrator"),
            (wrong_origin, "production-orchestrator"),
            (wrong_issue, "production-orchestrator"),
            (wrong_suffix, "production-orchestrator"),
            (tampered, "production-orchestrator"),
            (same, "production-orchestrator"),
            (later, "production-orchestrator"),
        )
        for candidate, actor in cases:
            with self.subTest(return_id=candidate.data.get("return_id"), actor=actor):
                with self.assertRaises((
                    prod.ProductionOrchestratorError,
                    rt.CoordinatorError,
                    store_module.ProductionStoreError,
                )):
                    prod.apply_active_return_escalation(
                        active, request=candidate, actor=actor, inputs={}
                    )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(coordinator_before, active.coordinator.state)

    def test_active_return_escalation_rejects_stale_context_order_and_path_atomically(self) -> None:
        _, active, old_request = self._active_e1_contract_return()
        _, pending = prod.issue_stage_work(active, action="E1", inputs={})
        request = self._escalation_request(old_request)
        state_before = active.store.load_document(active.state.data["previous_state"])
        stale_context = prod.ProductionContext(
            active.store, active.coordinator, state_before, old_request
        )
        before = self._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_active_return_escalation(
                stale_context, request=request,
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual("PROD_CONTEXT_STALE", caught.exception.code)
        self.assertEqual(before, self._run_inventory())

        stale_data = copy.deepcopy(pending.data)
        stale_data["state"] = state_before.reference
        stale_data.pop("work_id")
        stale_id = rt.canonical_sha256(stale_data)[:24]
        stale_data["work_id"] = stale_id
        stale_order = rt.SealedDocument(
            stale_data,
            {
                "path": f"orchestration/work-orders/{stale_id}.json",
                "sha256": rt.canonical_sha256(stale_data),
            },
        )
        active.store.persist_document(stale_order)
        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {"schema_version": "2.0", "work_order": stale_order.reference},
        )
        before = self._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_active_return_escalation(
                active, request=request,
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual(
            "PROD_ACTIVE_RETURN_ESCALATION_PENDING_ORDER_INVALID",
            caught.exception.code,
        )
        self.assertEqual(before, self._run_inventory())

        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {"schema_version": "2.0", "work_order": pending.reference},
        )
        genuine_gate = active.store.load_document(pending.data["input_gate"])
        forged_gate_data = copy.deepcopy(genuine_gate.data)
        forged_gate_data["return_binding"]["return_id"] = "RET-FOREIGN-GATE"
        forged_gate = rt.seal_document(
            forged_gate_data,
            "orchestration/input-gates/forged-escalation/input-gate.json",
        )
        active.store.persist_document(forged_gate)
        forged_order_core = {
            key: copy.deepcopy(value)
            for key, value in pending.data.items()
            if key != "work_id"
        }
        forged_order_core["input_gate"] = forged_gate.reference
        forged_work_id = rt.canonical_sha256(forged_order_core)[:24]
        forged_order_data = {**forged_order_core, "work_id": forged_work_id}
        forged_order = rt.SealedDocument(
            forged_order_data,
            {
                "path": f"orchestration/work-orders/{forged_work_id}.json",
                "sha256": rt.canonical_sha256(forged_order_data),
            },
        )
        active.store.persist_document(forged_order)
        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {"schema_version": "2.0", "work_order": forged_order.reference},
        )
        before = self._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_active_return_escalation(
                active, request=request,
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual(
            "PROD_ACTIVE_RETURN_ESCALATION_PENDING_GATE_INVALID",
            caught.exception.code,
        )
        self.assertEqual(before, self._run_inventory())

        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {"schema_version": "2.0", "work_order": pending.reference},
        )
        conflict = self.root / request.reference["path"]
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_text(rt.canonical_json({"conflict": True}), encoding="utf-8")
        before = self._run_inventory()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.apply_active_return_escalation(
                active, request=request,
                actor="production-orchestrator", inputs={},
            )
        self.assertEqual("PROD_IMMUTABLE_CONFLICT", caught.exception.code)
        self.assertEqual(before, self._run_inventory())

    def test_active_return_escalation_recovers_prepared_and_mid_derived_prefix(self) -> None:
        _, active, _, request, pending, plan, successor = (
            self._prepared_only_escalation()
        )
        prepared_inventory = self._run_inventory()
        resumed = prod.resume_production_run(self.root)
        qualification = resumed.store.current_contract_upgrade()
        self.assertEqual("active_return_escalation", qualification.data["transition_mode"])
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        work = resumed.store.pending_work_order()
        self.assertEqual("B0", work.data["action"])
        self.assertEqual(plan.data["post_upgrade_work_order"], work.reference)
        self.assertTrue(
            (self.root / "orchestration/work-orders"
             / f"{pending.data['work_id']}.rejected.json").is_file()
        )
        for item in plan.data["post_upgrade_documents"]:
            self.assertTrue((self.root / item["reference"]["path"]).is_file())
        self.assertTrue(set(prepared_inventory).issubset(self._run_inventory()))

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory(prefix="prod-escalation-prefix-")
        self.root = Path(self.temporary.name)
        _, active, _, request, _, plan, successor = self._prepared_only_escalation()
        receipt, derived = active.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        active.store.persist_state(successor)
        for document in derived[:-1]:
            active.store.persist_document(document)
        prefix_inventory = self._run_inventory()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(receipt.reference, resumed.store.current_contract_upgrade().reference)
        self.assertEqual(plan.data["post_upgrade_work_order"],
                         resumed.store.pending_work_order().reference)
        mutable_pointers = {
            "orchestration/current-state.json",
            "orchestration/current-contract-upgrade.json",
            "orchestration/current-work-order.json",
        }
        for path, body in prefix_inventory.items():
            if path not in mutable_pointers:
                self.assertEqual(body, (self.root / path).read_bytes())

    def test_active_return_escalation_recovers_complete_receipt_pointer_gap(self) -> None:
        prior, active, _, request, _, plan, successor = (
            self._prepared_only_escalation()
        )
        receipt, derived = active.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        active.store.persist_state(successor)
        for document in derived:
            active.store.persist_document(document)
        active.store.persist_document(receipt)
        active.store._replace(
            self.root / "orchestration/current-work-order.json",
            {
                "schema_version": "2.0",
                "work_order": plan.data["post_upgrade_work_order"],
            },
        )
        self.assertEqual(prior.reference, active.store.current_contract_upgrade().reference)
        before = self._run_inventory()
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(receipt.reference, resumed.store.current_contract_upgrade().reference)
        self.assertEqual(successor.reference, resumed.state.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertEqual(plan.data["post_upgrade_work_order"],
                         resumed.store.pending_work_order().reference)
        for path, body in before.items():
            if path != "orchestration/current-contract-upgrade.json":
                self.assertEqual(body, (self.root / path).read_bytes())

    def test_active_return_escalation_supports_consecutive_earlier_owners(self) -> None:
        prior, active, old_request = self._active_e1_contract_return()
        prod.issue_stage_work(active, action="E1", inputs={})
        s1_request = self._escalation_request(
            old_request, target="S1", return_id="RET-ESCALATE-S1-FIRST"
        )
        first, active, _, s1_order = prod.apply_active_return_escalation(
            active, request=s1_request, actor="production-orchestrator", inputs={}
        )
        b0_request = self._escalation_request(
            s1_request, target="B0", return_id="RET-ESCALATE-B0-SECOND"
        )
        second, active, gate, b0_order = prod.apply_active_return_escalation(
            active, request=b0_request, actor="production-orchestrator", inputs={}
        )
        self.assertEqual(prior.reference, first.data["prior_qualification"])
        self.assertEqual(first.reference, second.data["prior_qualification"])
        self.assertEqual(first.data["refresh_generation"] + 1,
                         second.data["refresh_generation"])
        self.assertEqual(s1_request.reference, second.data["superseded_return"])
        self.assertEqual(b0_request.reference, active.active_return.reference)
        self.assertEqual("B0", gate.data["target_stage"])
        self.assertEqual("B0", b0_order.data["action"])
        self.assertTrue(
            (self.root / "orchestration/work-orders"
             / f"{s1_order.data['work_id']}.rejected.json").is_file()
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(second.reference, resumed.store.current_contract_upgrade().reference)
        self.assertEqual(b0_order.reference, resumed.store.pending_work_order().reference)

    def test_active_return_escalation_prepared_forks_and_tampering_are_atomic(self) -> None:
        for mutant in (
            "prior_null", "prior_fork", "digest_drift",
            "generation_drift", "successor_active_return", "request_body",
            "post_order_actor",
        ):
            with self.subTest(mutant=mutant):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-escalation-mutant-{mutant}-"
                )
                self.root = Path(self.temporary.name)
                _, active, old_request, request, _, plan, _ = (
                    self._prepared_only_escalation()
                )
                plan_path = self.root / plan.reference["path"]
                data = copy.deepcopy(plan.data)
                if mutant == "prior_null":
                    data["prior_qualification"] = None
                elif mutant == "prior_fork":
                    data["prior_qualification"] = {
                        "path": "orchestration/contract-upgrades/fork.complete.json",
                        "sha256": "f" * 64,
                    }
                elif mutant == "digest_drift":
                    data["old_contract_digest"] = "f" * 64
                elif mutant == "generation_drift":
                    data["refresh_generation"] += 7
                elif mutant == "successor_active_return":
                    data["successor_snapshot"]["active_return"] = old_request.reference
                    data["successor_state"]["sha256"] = rt.canonical_sha256(
                        data["successor_snapshot"]
                    )
                elif mutant == "request_body":
                    request_path = self.root / request.reference["path"]
                    body = copy.deepcopy(request.data)
                    body["problem"] = "tampered prepared request"
                    request_path.write_text(rt.canonical_json(body), encoding="utf-8")
                elif mutant == "post_order_actor":
                    order = next(
                        item for item in data["post_upgrade_documents"]
                        if item["reference"] == data["post_upgrade_work_order"]
                    )
                    order["data"]["required_actor"] = "foreign-actor"
                    core = {
                        key: value for key, value in order["data"].items()
                        if key != "work_id"
                    }
                    order["data"]["work_id"] = rt.canonical_sha256(core)[:24]
                    order["reference"] = {
                        "path": (
                            "orchestration/work-orders/"
                            f"{order['data']['work_id']}.json"
                        ),
                        "sha256": rt.canonical_sha256(order["data"]),
                    }
                    data["post_upgrade_work_order"] = order["reference"]
                if mutant != "request_body":
                    plan_path.write_text(rt.canonical_json(data), encoding="utf-8")
                before = self._run_inventory()
                state_pointer = (
                    self.root / "orchestration/current-state.json"
                ).read_bytes()
                qualification_pointer = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                with self.assertRaises(store_module.ProductionStoreError):
                    prod.resume_production_run(self.root)
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_pointer,
                    (self.root / "orchestration/current-state.json").read_bytes(),
                )
                self.assertEqual(
                    qualification_pointer,
                    (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
                )

    def test_active_return_escalation_orphan_receipt_is_not_trusted(self) -> None:
        _, active, _, _, _, plan, successor = self._prepared_only_escalation()
        receipt, derived = active.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        for document in (*derived, receipt):
            active.store.persist_document(document)
        (self.root / plan.reference["path"]).unlink()
        before = self._run_inventory()
        state_pointer = (
            self.root / "orchestration/current-state.json"
        ).read_bytes()
        qualification_pointer = (
            self.root / "orchestration/current-contract-upgrade.json"
        ).read_bytes()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.resume_production_run(self.root)
        self.assertEqual("PROD_UNTRUSTED_PROCESSED_MARKER", caught.exception.code)
        self.assertEqual(before, self._run_inventory())
        self.assertEqual(
            state_pointer,
            (self.root / "orchestration/current-state.json").read_bytes(),
        )
        self.assertEqual(
            qualification_pointer,
            (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
        )

    def test_active_return_escalation_late_gate_order_and_rejection_conflicts_are_atomic(self) -> None:
        for conflict_kind in ("gate", "order", "old_order_rejection"):
            with self.subTest(conflict_kind=conflict_kind):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-escalation-conflict-{conflict_kind}-"
                )
                self.root = Path(self.temporary.name)
                _, active, old_request = self._active_e1_contract_return()
                _, pending = prod.issue_stage_work(active, action="E1", inputs={})
                request = self._escalation_request(old_request)
                fresh = rt.AutonomousCoordinator.from_snapshot(
                    copy.deepcopy(active.state.data), active.state.reference,
                    active_return_request=old_request,
                    runtime=active.store.runtime,
                )
                transition = fresh.supersede_active_return(
                    request=request,
                    next_state_path=(
                        f"state/revision-{active.state.data['revision'] + 1:03d}.json"
                    ),
                )
                successor = rt.SealedDocument(
                    transition.snapshot, transition.reference
                )
                gate_path = (
                    "orchestration/input-gates/"
                    f"revision-{successor.data['revision']:03d}-B0/input-gate.json"
                )
                gate = fresh.build_input_gate(
                    "B0", gate_path, active_return_request=request
                )
                order_core = {
                    "schema_version": "2.0", "run_id": successor.data["run_id"],
                    "action": "B0", "state": successor.reference,
                    "input_gate": gate.reference, "h1_workspace": None,
                    "required_actor": prod.ACTION_CONTRACT["B0"][1],
                    "inputs": {}, "status": "pending",
                }
                work_id = rt.canonical_sha256(order_core)[:24]
                paths = {
                    "gate": self.root / gate_path,
                    "order": (
                        self.root / "orchestration/work-orders" / f"{work_id}.json"
                    ),
                    "old_order_rejection": (
                        self.root / "orchestration/work-orders"
                        / f"{pending.data['work_id']}.rejected.json"
                    ),
                }
                conflict_path = paths[conflict_kind]
                conflict_path.parent.mkdir(parents=True, exist_ok=True)
                conflict_path.write_text(
                    rt.canonical_json({"late_conflict": conflict_kind}),
                    encoding="utf-8",
                )
                before = self._run_inventory()
                coordinator_before = copy.deepcopy(active.coordinator.state)
                with self.assertRaises(store_module.ProductionStoreError) as caught:
                    prod.apply_active_return_escalation(
                        active, request=request, actor="production-orchestrator",
                        inputs={},
                    )
                self.assertEqual(
                    (
                        "PROD_UNTRUSTED_PROCESSED_MARKER"
                        if conflict_kind == "old_order_rejection"
                        else "PROD_IMMUTABLE_CONFLICT"
                    ),
                    caught.exception.code,
                )
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(coordinator_before, active.coordinator.state)

    def test_c1_return_escalates_to_qualified_e1_and_t1_orders(self) -> None:
        for target in ("E1", "T1"):
            with self.subTest(target=target):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-qualified-escalation-{target}-"
                )
                self.root = Path(self.temporary.name)
                prior, active, old_request = self._active_c1_return()
                prod.issue_stage_work(active, action="C1", inputs={})
                request = self._escalation_request(
                    old_request, target=target,
                    return_id=f"RET-C1-TO-{target}-QUALIFIED",
                )
                receipt, escalated, _, order = prod.apply_active_return_escalation(
                    active, request=request, actor="production-orchestrator",
                    inputs={"qualified": target},
                )
                expected = {
                    "contract_upgrade_receipt": prior.reference,
                    "contract_digest": prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
                    "owner_stage": target,
                    "owner_schema_version": (
                        prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT[target][
                            "model_schema_version"
                        ]
                    ),
                    "upstream_schema_versions": (
                        {
                            "E1": prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT["E1"][
                                "model_schema_version"
                            ]
                        }
                        if target == "T1" else {}
                    ),
                }
                self.assertEqual(
                    expected, order.data["inputs"]["_contract_qualification"]
                )
                self.assertEqual(
                    {"qualified": target},
                    escalated.store.load_document(receipt.data["plan"]).data[
                        "post_upgrade_inputs"
                    ],
                )
                _, completed = prod.execute_stage_work(
                    escalated, work_order=order,
                    actor=prod.ACTION_CONTRACT[target][1],
                    executor=self._fake_executor(
                        target, escalated.state.data["revision"] + 1
                    ),
                )
                self.assertIsNone(completed.active_return)
                self.assertIn(target, completed.state.data["current_stage_completions"])

    def test_escalation_rejects_reserved_contract_qualification_without_writes(self) -> None:
        _, active, old_request = self._active_c1_return()
        prod.issue_stage_work(active, action="C1", inputs={})
        request = self._escalation_request(old_request, target="E1")
        before = self._run_inventory()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.apply_active_return_escalation(
                active, request=request, actor="production-orchestrator",
                inputs={"_contract_qualification": {"forged": True}},
            )
        self.assertEqual("PROD_CONTRACT_QUALIFICATION_RESERVED", caught.exception.code)
        self.assertEqual(before, self._run_inventory())

    def test_qualified_escalation_recovery_rejects_every_qualification_drift(self) -> None:
        mutants = (
            "missing", "receipt", "digest", "owner", "owner_version",
            "upstream_version",
        )
        for mutant in mutants:
            with self.subTest(mutant=mutant):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-qualified-mutant-{mutant}-"
                )
                self.root = Path(self.temporary.name)
                _, active, _, _, _, plan = self._prepared_qualified_escalation("T1")
                plan_path = self.root / plan.reference["path"]
                data = copy.deepcopy(plan.data)
                order = next(
                    item for item in data["post_upgrade_documents"]
                    if item["reference"] == data["post_upgrade_work_order"]
                )
                qualified = order["data"]["inputs"].get("_contract_qualification")
                if mutant == "missing":
                    order["data"]["inputs"].pop("_contract_qualification")
                elif mutant == "receipt":
                    qualified["contract_upgrade_receipt"] = {
                        "path": "orchestration/contract-upgrades/foreign.complete.json",
                        "sha256": "f" * 64,
                    }
                elif mutant == "digest":
                    qualified["contract_digest"] = "f" * 64
                elif mutant == "owner":
                    qualified["owner_stage"] = "E1"
                elif mutant == "owner_version":
                    qualified["owner_schema_version"] = "0.0"
                elif mutant == "upstream_version":
                    qualified["upstream_schema_versions"]["E1"] = "0.0"
                order["reference"]["sha256"] = rt.canonical_sha256(order["data"])
                data["post_upgrade_work_order"] = order["reference"]
                plan_path.write_text(rt.canonical_json(data), encoding="utf-8")
                before = self._run_inventory()
                state_pointer = (
                    self.root / "orchestration/current-state.json"
                ).read_bytes()
                qualification_pointer = (
                    self.root / "orchestration/current-contract-upgrade.json"
                ).read_bytes()
                with self.assertRaises(store_module.ProductionStoreError):
                    prod.resume_production_run(self.root)
                self.assertEqual(before, self._run_inventory())
                self.assertEqual(
                    state_pointer,
                    (self.root / "orchestration/current-state.json").read_bytes(),
                )
                self.assertEqual(
                    qualification_pointer,
                    (self.root / "orchestration/current-contract-upgrade.json").read_bytes(),
                )

    def test_qualified_t1_escalation_prepared_recovery_preserves_executable_order(self) -> None:
        prior, _, _, request, _, plan = self._prepared_qualified_escalation("T1")
        resumed = prod.resume_production_run(self.root)
        order = resumed.store.pending_work_order()
        qualification = order.data["inputs"]["_contract_qualification"]
        self.assertEqual(prior.reference, qualification["contract_upgrade_receipt"])
        self.assertEqual(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            qualification["contract_digest"],
        )
        self.assertEqual("T1", qualification["owner_stage"])
        self.assertEqual(
            {
                "E1": prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT["E1"][
                    "model_schema_version"
                ]
            },
            qualification["upstream_schema_versions"],
        )
        self.assertEqual(plan.data["post_upgrade_work_order"], order.reference)
        self.assertEqual(request.reference, resumed.active_return.reference)
        _, completed = prod.execute_stage_work(
            resumed, work_order=order,
            actor=prod.ACTION_CONTRACT["T1"][1],
            executor=self._fake_executor(
                "T1", resumed.state.data["revision"] + 1
            ),
        )
        self.assertIsNone(completed.active_return)

    def test_current_stage_identity_replays_full_package_and_rejects_every_drift(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        completion_reference = context.state.data["current_stage_completions"]["E1"]
        identity = prod._completion_contract_identity(
            context.store, completion_reference
        )
        self.assertTrue(prod._identity_matches_current_profile("E1", identity))
        package_root = self.root / Path(completion_reference["path"]).parent
        self.public_replay_mock.assert_called_with("E1", package_root)

        drift_paths = {
            "runtime": package_root / "implementation/skill/run_v2.py",
            "schema": package_root
            / "implementation/schemas/environment-system.schema.json",
            "protocol": package_root
            / "implementation/skill/runtime-contract.md",
            "manifest": package_root / "package-manifest.json",
            "completion": package_root / "stage-completion.json",
            "canonical": package_root / "canonical.json",
        }
        qualification = context.store.current_contract_upgrade()
        for label, path in drift_paths.items():
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            try:
                with self.subTest(drift=label):
                    target, observed = prod._actual_contract_upgrade_target(
                        context.store, context.state, qualification
                    )
                    self.assertEqual("E1", target)
                    self.assertEqual("E1", observed["stage"])
                    with self.assertRaises(
                        (prod.ProductionOrchestratorError, store_module.ProductionStoreError)
                    ):
                        prod.resume_production_run(self.root)
                    with self.assertRaises(
                        (prod.ProductionOrchestratorError, store_module.ProductionStoreError)
                    ):
                        prod.issue_stage_work(context, action="T1", inputs={})
            finally:
                path.write_bytes(original)

        # A fully resealed package with the current model-version label but an
        # old runtime must still classify E1 as the next upgrade target.
        execution_path = package_root / "execution-record.json"
        chain_paths = [
            drift_paths["runtime"],
            execution_path,
            drift_paths["manifest"],
            drift_paths["completion"],
        ]
        originals = {path: path.read_bytes() for path in chain_paths}
        try:
            drift_paths["runtime"].write_text(
                "# preserved stale E1 runtime\n", encoding="utf-8"
            )
            execution = json.loads(execution_path.read_text(encoding="utf-8"))
            runtime_item = next(
                item
                for item in execution["implementation_catalog"]
                if item["identity"] == "skill/run_v2.py"
            )
            runtime_item["artifact"]["sha256"] = rt.sha256_file(
                drift_paths["runtime"]
            )
            execution_path.write_text(rt.canonical_json(execution), encoding="utf-8")
            manifest = json.loads(
                drift_paths["manifest"].read_text(encoding="utf-8")
            )
            manifest["artifact_roles"]["execution_record"]["sha256"] = (
                rt.sha256_file(execution_path)
            )
            drift_paths["manifest"].write_text(
                rt.canonical_json(manifest), encoding="utf-8"
            )
            completion = json.loads(
                drift_paths["completion"].read_text(encoding="utf-8")
            )
            completion["manifest"]["sha256"] = rt.sha256_file(
                drift_paths["manifest"]
            )
            drift_paths["completion"].write_text(
                rt.canonical_json(completion), encoding="utf-8"
            )
            resealed_reference = {
                **completion_reference,
                "sha256": rt.sha256_file(drift_paths["completion"]),
            }
            resealed_identity = prod._completion_contract_identity(
                context.store, resealed_reference
            )
            self.assertFalse(
                prod._identity_matches_current_profile("E1", resealed_identity)
            )
            resealed_state_data = copy.deepcopy(context.state.data)
            resealed_state_data["current_stage_completions"]["E1"] = (
                resealed_reference
            )
            resealed_state = rt.SealedDocument(
                data=resealed_state_data, reference=context.state.reference
            )
            target, _observed = prod._actual_contract_upgrade_target(
                context.store, resealed_state, qualification
            )
            self.assertEqual("E1", target)
        finally:
            for path, body in originals.items():
                path.write_bytes(body)

        _, order = prod.issue_stage_work(context, action="T1", inputs={})
        runtime_path = drift_paths["runtime"]
        original_runtime = runtime_path.read_bytes()
        runtime_path.write_bytes(original_runtime + b"\n")
        try:
            with self.assertRaises(prod.ProductionOrchestratorError):
                prod.execute_stage_work(
                    context,
                    work_order=order,
                    actor=prod.ACTION_CONTRACT["T1"][1],
                    executor=self._fake_executor("T1", 5),
                )
        finally:
            runtime_path.write_bytes(original_runtime)

    def _move_e1_to_attempt_workspace(self, context):
        reference = context.state.data["current_stage_completions"]["E1"]
        logical_root = self.root / Path(reference["path"]).parent
        attempt = Path(reference["path"]).parts[1]
        physical_root = self.root / "workspaces" / f"E1-{attempt}" / "package"
        physical_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(logical_root), str(physical_root))
        logical_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            physical_root / "stage-completion.json",
            logical_root / "stage-completion.json",
        )
        return reference, logical_root, physical_root

    def test_attempt_workspace_completion_resumes_and_issues_t1(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context, work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        reference, _logical_root, physical_root = (
            self._move_e1_to_attempt_workspace(context)
        )

        resumed = prod.resume_production_run(self.root)
        self.assertEqual(
            physical_root / "stage-completion.json",
            resumed.store.resolve_document_path(reference),
        )
        gate, order = prod.issue_stage_work(resumed, action="T1", inputs={})
        self.assertEqual("T1", gate.data["target_stage"])
        self.assertEqual("T1", order.data["action"])

    def test_attempt_workspace_provenance_failures_precede_writes(self) -> None:
        mutations = ("missing", "ambiguous", "tampered", "foreign")
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.temporary.cleanup()
                self.temporary = tempfile.TemporaryDirectory(
                    prefix=f"prod-attempt-root-{mutation}-"
                )
                self.root = Path(self.temporary.name)
                context = self._context()
                for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
                    _, order = prod.issue_stage_work(context, action=stage, inputs={})
                    _, context = prod.execute_stage_work(
                        context, work_order=order,
                        actor=prod.ACTION_CONTRACT[stage][1],
                        executor=self._fake_executor(stage, revision),
                    )
                reference, logical_root, physical_root = (
                    self._move_e1_to_attempt_workspace(context)
                )
                if mutation == "missing":
                    shutil.move(
                        str(physical_root), str(physical_root.with_name("detached"))
                    )
                elif mutation == "ambiguous":
                    shutil.copytree(physical_root, logical_root, dirs_exist_ok=True)
                elif mutation == "tampered":
                    completion = physical_root / "stage-completion.json"
                    completion.write_bytes(completion.read_bytes() + b"\n")
                before = self._run_inventory()
                if mutation == "foreign":
                    with self.assertRaises(store_module.ProductionStoreError) as caught:
                        context.store.resolve_document_path(
                            {**reference, "stage": "T1"}
                        )
                    self.assertEqual(
                        "PROD_PACKAGE_PROVENANCE_INVALID", caught.exception.code
                    )
                else:
                    with self.assertRaises(
                        (prod.ProductionOrchestratorError,
                         store_module.ProductionStoreError)
                    ):
                        prod.resume_production_run(self.root)
                self.assertEqual(before, self._run_inventory())

    def test_legacy_in_place_completion_root_remains_supported(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context, work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        reference = context.state.data["current_stage_completions"]["E1"]
        self.assertEqual(
            self.root / Path(reference["path"]),
            context.store.resolve_document_path(reference),
        )
        resumed = prod.resume_production_run(self.root)
        gate, order = prod.issue_stage_work(resumed, action="T1", inputs={})
        self.assertEqual("T1", gate.data["target_stage"])
        self.assertEqual("T1", order.data["action"])

    def _long_attempt_document_chain(self, suffix: str):
        store = store_module.ProductionRunStore(self.root)
        attempt = "attempt-" + suffix + "a" * 155
        logical_root = PurePosixPath("E1", attempt)
        package_root = (
            self.root / "workspaces" / f"E1-{attempt}" / "package"
        )

        def write_json(path, value):
            physical = store.physical_path(path)
            physical.parent.mkdir(parents=True, exist_ok=True)
            physical.write_text(rt.canonical_json(value), encoding="utf-8")

        canonical_rel = PurePosixPath(
            "deep", "b" * 90, "environment-system.json"
        )
        canonical_path = package_root / Path(*canonical_rel.parts)
        canonical = {"schema_version": "2.4", "stage": "E1"}
        write_json(canonical_path, canonical)
        canonical_ref = {
            "path": canonical_rel.as_posix(),
            "sha256": store.physical_sha256(canonical_path),
        }
        validation_path = package_root / "validation.json"
        validation = {"schema_version": "2.0", "status": "ready"}
        write_json(validation_path, validation)
        validation_ref = {
            "path": f"{logical_root.as_posix()}/validation.json",
            "sha256": store.physical_sha256(validation_path),
        }
        manifest_path = package_root / "package-manifest.json"
        manifest = {
            "schema_version": "2.0", "stage": "E1", "verdict": "ready",
            "artifact_roles": {"canonical": canonical_ref},
            "validation": {"path": "validation.json",
                           "sha256": validation_ref["sha256"]},
        }
        write_json(manifest_path, manifest)
        manifest_ref = {
            "path": f"{logical_root.as_posix()}/package-manifest.json",
            "sha256": store.physical_sha256(manifest_path),
        }
        completion_path = package_root / "stage-completion.json"
        completion = {
            "stage": "E1", "status": "ready", "manifest": manifest_ref,
            "validation": validation_ref,
        }
        write_json(completion_path, completion)
        completion_ref = {
            "stage": "E1",
            "path": f"{logical_root.as_posix()}/stage-completion.json",
            "sha256": store.physical_sha256(completion_path),
        }
        mirror = store._path(completion_ref["path"])
        write_json(mirror, completion)
        self.assertGreater(len(str(completion_path)), 260)
        self.assertGreater(len(str(canonical_path)), 260)
        return {
            "store": store, "logical_root": logical_root,
            "package_root": package_root, "completion": completion,
            "completion_ref": completion_ref, "manifest": manifest,
            "manifest_ref": manifest_ref, "validation": validation,
            "validation_ref": validation_ref, "canonical_ref": canonical_ref,
            "canonical_path": canonical_path, "mirror": mirror,
        }

    def test_long_attempt_workspace_resolves_entire_document_chain(self) -> None:
        chain = self._long_attempt_document_chain("success")
        store = chain["store"]
        completion = store.load_document(chain["completion_ref"])
        manifest = store.load_document(completion.data["manifest"])
        validation = store.load_document(completion.data["validation"])
        canonical = prod._load_package_json_document(
            store, chain["package_root"], chain["logical_root"],
            manifest.data["artifact_roles"]["canonical"],
        )
        self.assertEqual("ready", validation.data["status"])
        self.assertEqual("2.4", canonical.data["schema_version"])

    def test_long_attempt_workspace_failures_are_closed(self) -> None:
        for mutation in ("tampered", "missing", "ambiguous"):
            with self.subTest(mutation=mutation):
                chain = self._long_attempt_document_chain(mutation)
                store = chain["store"]
                if mutation == "tampered":
                    completion = store.physical_path(
                        chain["package_root"] / "stage-completion.json"
                    )
                    completion.write_bytes(completion.read_bytes() + b"\n")
                elif mutation == "missing":
                    store.physical_path(
                        chain["package_root"] / "package-manifest.json"
                    ).unlink()
                else:
                    direct_root = chain["mirror"].parent
                    for name, value in (
                        ("package-manifest.json", chain["manifest"]),
                        ("validation.json", chain["validation"]),
                    ):
                        physical = store.physical_path(direct_root / name)
                        physical.write_text(
                            rt.canonical_json(value), encoding="utf-8"
                        )
                with self.assertRaises(store_module.ProductionStoreError):
                    store.load_document(chain["completion_ref"])

    def test_t1_identity_drift_targets_t1_after_current_e1(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1", "T1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        t1_reference = context.state.data["current_stage_completions"]["T1"]
        runtime_path = (
            self.root
            / Path(t1_reference["path"]).parent
            / "implementation/skill/run_v2.py"
        )
        original = runtime_path.read_bytes()
        runtime_path.write_bytes(original + b"\n")
        try:
            target, observed = prod._actual_contract_upgrade_target(
                context.store,
                context.state,
                context.store.current_contract_upgrade(),
            )
            self.assertEqual("T1", target)
            self.assertEqual("T1", observed["stage"])
        finally:
            runtime_path.write_bytes(original)

    def test_no_active_return_contract_diff_targets_earliest_changed_owner(self) -> None:
        context = self._context()
        qualification = context.store.current_contract_upgrade()
        baseline = copy.deepcopy(prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT)
        cases = (
            ("E1", ("E1",), "a"),
            ("T1", ("T1",), "b"),
            ("E1", ("E1", "T1"), "c"),
        )
        for expected, changed, marker in cases:
            with self.subTest(changed=changed):
                contract = copy.deepcopy(baseline)
                for stage in changed:
                    contract[stage]["identity_bindings"]["runtime"][
                        "sha256"
                    ] = marker * 64
                digest = rt.canonical_sha256(contract)
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    target, observed = prod._actual_contract_upgrade_target(
                        context.store, context.state, qualification
                    )
                self.assertEqual(expected, target)
                self.assertEqual(expected, observed["stage"])
                self.assertEqual(list(changed), observed["changed_owner_stages"])
                self.assertEqual(
                    qualification.data["production_versions"],
                    {
                        stage: contract[stage]["model_schema_version"]
                        for stage in ("E1", "T1")
                    },
                )

    def test_stale_qualification_escalates_active_t1_return_atomically_to_e1(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context, work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        preserved = copy.deepcopy(
            context.state.data["current_stage_completions"]
        )
        first_contract = copy.deepcopy(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT
        )
        first_contract["T1"]["identity_bindings"]["runtime"][
            "sha256"
        ] = "a" * 64
        first_digest = rt.canonical_sha256(first_contract)
        first_request = rt.seal_document(
            rt.route_return(
                run_id="RUN-PROD-1", return_id="RET-ACTIVE-T1-STALE-QUAL",
                origin_kind="stage", origin_stage="T1",
                issue_kind="event_timeline",
                problem="T1 owner identity changed.",
                evidence_ids=["T1-OWNER-DRIFT"],
                violated_contract="T1 production identity",
                required_revision="Regenerate T1.", author_decision=None,
                has_current_author_decision=False,
                has_current_conception_completion=False,
            ),
            "returns/RET-ACTIVE-T1-STALE-QUAL.json",
        )
        prior = context.store.current_contract_upgrade()
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", first_contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", first_digest
        ):
            first_receipt, active = prod.apply_contract_upgrade(
                context, request=first_request,
                old_contract_digest=prior.data["new_contract_digest"],
            )
            _, pending_t1 = prod.issue_stage_work(
                active, action="T1", inputs={"candidate": "stale"}
            )

        for stage in ("E1", "T1"):
            path = self.root / stage / "unfinished" / "generation-session.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                rt.canonical_json({
                    "schema_version": "1.0", "stage": stage,
                    "session_id": f"UNFINISHED-{stage}",
                }),
                encoding="utf-8",
            )

        current_contract = copy.deepcopy(first_contract)
        current_contract["E1"]["identity_bindings"]["runtime"][
            "sha256"
        ] = "b" * 64
        current_contract["E1"]["model_schema_version"] = "2.5"
        current_digest = rt.canonical_sha256(current_contract)
        e1_request = self._escalation_request(
            first_request, target="E1",
            return_id="RET-STALE-QUAL-ESCALATE-E1",
        )
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", current_contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", current_digest
        ):
            receipt, escalated, gate, order = (
                prod.apply_active_return_escalation(
                    active, request=e1_request,
                    actor="production-orchestrator",
                    inputs={"reason": "earliest changed owner is E1"},
                )
            )
            resumed = prod.resume_production_run(self.root)

        self.assertEqual("active_return_escalation", receipt.data["transition_mode"])
        self.assertEqual(first_digest, receipt.data["old_contract_digest"])
        self.assertEqual(current_digest, receipt.data["new_contract_digest"])
        self.assertEqual("E1", receipt.data["target_stage"])
        self.assertEqual(first_request.reference, receipt.data["superseded_return"])
        self.assertEqual(
            {stage: preserved[stage] for stage in ("B0", "S1", "W1")},
            escalated.state.data["current_stage_completions"],
        )
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual("E1", order.data["action"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        self.assertEqual(
            first_receipt.reference,
            order.data["inputs"]["_contract_qualification"][
                "contract_upgrade_receipt"
            ],
        )
        self.assertEqual(
            current_digest,
            order.data["inputs"]["_contract_qualification"]["contract_digest"],
        )
        self.assertEqual(
            "2.5",
            order.data["inputs"]["_contract_qualification"][
                "owner_schema_version"
            ],
        )
        self.assertEqual("2.5", receipt.data["production_versions"]["E1"])
        self.assertEqual(2, len(receipt.data["session_invalidation_receipts"]))
        self.assertEqual(1, len(receipt.data["completion_invalidation_receipts"]))
        self.assertTrue((
            self.root / "orchestration/work-orders"
            / f"{pending_t1.data['work_id']}.rejected.json"
        ).is_file())
        self.assertEqual(receipt.reference, resumed.store.current_contract_upgrade().reference)
        self.assertEqual(order.reference, resumed.store.pending_work_order().reference)

    def test_stale_qualification_escalation_wrong_target_is_zero_write(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context, work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        first_contract = copy.deepcopy(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT
        )
        first_contract["T1"]["identity_bindings"]["runtime"]["sha256"] = "c" * 64
        first_digest = rt.canonical_sha256(first_contract)
        first_request = rt.seal_document(
            rt.route_return(
                run_id="RUN-PROD-1", return_id="RET-ZERO-WRITE-T1",
                origin_kind="stage", origin_stage="T1",
                issue_kind="event_timeline", problem="T1 drift.",
                evidence_ids=["T1-DRIFT"], violated_contract="T1 identity",
                required_revision="Regenerate T1.", author_decision=None,
                has_current_author_decision=False,
                has_current_conception_completion=False,
            ), "returns/RET-ZERO-WRITE-T1.json",
        )
        prior = context.store.current_contract_upgrade()
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", first_contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", first_digest
        ):
            _, active = prod.apply_contract_upgrade(
                context, request=first_request,
                old_contract_digest=prior.data["new_contract_digest"],
            )
            prod.issue_stage_work(active, action="T1", inputs={})
        current_contract = copy.deepcopy(first_contract)
        current_contract["E1"]["identity_bindings"]["runtime"]["sha256"] = "d" * 64
        current_digest = rt.canonical_sha256(current_contract)
        wrong = self._escalation_request(
            first_request, target="W1", return_id="RET-WRONG-EARLIEST-W1"
        )
        before = self._run_inventory()
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", current_contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", current_digest
        ):
            with self.assertRaises(prod.ProductionOrchestratorError) as caught:
                prod.apply_active_return_escalation(
                    active, request=wrong, actor="production-orchestrator",
                    inputs={},
                )
        self.assertEqual("PROD_CONTRACT_UPGRADE_TARGET_MISMATCH", caught.exception.code)
        self.assertEqual(before, self._run_inventory())

    def test_escalation_plan_rejects_forged_owner_version_without_writes(self) -> None:
        _, active, _, _, _, plan = self._prepared_qualified_escalation("E1")
        forged = copy.deepcopy(plan.data)
        forged["production_versions"]["E1"] = "9.9"
        before = self._run_inventory()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            active.store.build_contract_upgrade_plan(forged)
        self.assertEqual("PROD_CONTRACT_UPGRADE_PLAN_INVALID", caught.exception.code)
        self.assertEqual(before, self._run_inventory())

    def test_unowned_contract_diff_fails_closed_before_any_write(self) -> None:
        original_root = self.root
        variants = ("schema_version", "unknown_owner")
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(
                prefix=f"prod-unowned-contract-{variant}-"
            ) as temporary:
                self.root = Path(temporary)
                context = self._context()
                qualification = context.store.current_contract_upgrade()
                contract = copy.deepcopy(
                    prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT
                )
                if variant == "schema_version":
                    contract["schema_version"] = "1.1"
                else:
                    contract["C1"] = {"identity_bindings": {}}
                digest = rt.canonical_sha256(contract)
                request_data = rt.route_return(
                    run_id="RUN-PROD-1",
                    return_id=f"RET-UNOWNED-{variant.upper()}",
                    origin_kind="stage",
                    origin_stage="T1",
                    issue_kind="environment",
                    problem="The production contract drift has no known owner.",
                    evidence_ids=[f"UNOWNED-{variant.upper()}"],
                    violated_contract="production contract ownership",
                    required_revision="Reject an unowned contract migration.",
                    author_decision=None,
                    has_current_author_decision=False,
                    has_current_conception_completion=False,
                )
                request = rt.seal_document(
                    request_data, f"returns/RET-UNOWNED-{variant.upper()}.json"
                )
                before = self._run_inventory()
                with mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
                ), mock.patch.object(
                    prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
                ):
                    with self.assertRaises(
                        prod.ProductionOrchestratorError
                    ) as caught:
                        prod.apply_contract_upgrade(
                            context,
                            request=request,
                            old_contract_digest=qualification.data[
                                "new_contract_digest"
                            ],
                        )
                self.assertEqual(
                    "PROD_CONTRACT_UPGRADE_BASIS_INVALID", caught.exception.code
                )
                self.assertEqual(before, self._run_inventory())
        self.root = original_root

    def test_formal_t1_owner_upgrade_preserves_prefix_and_rejects_pending_t1(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        preserved = copy.deepcopy(context.state.data["current_stage_completions"])
        _, pending_t1 = prod.issue_stage_work(
            context, action="T1", inputs={"candidate": "pre-upgrade"}
        )
        qualification = context.store.current_contract_upgrade()
        contract = copy.deepcopy(prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT)
        contract["T1"]["identity_bindings"]["runtime"]["sha256"] = "d" * 64
        digest = rt.canonical_sha256(contract)
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-T1-OWNER-DIFF",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="event_timeline",
            problem="The T1 implementation identity changed.",
            evidence_ids=["T1-OWNER-DIFF"],
            violated_contract="T1 production identity",
            required_revision="Regenerate T1 under its current owner contract.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data,
            "returns/RET-CONTRACT-UPGRADE-T1-OWNER-DIFF.json",
        )
        with mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT", contract
        ), mock.patch.object(
            prod, "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256", digest
        ):
            receipt, migrated = prod.apply_contract_upgrade(
                context,
                request=request,
                old_contract_digest=qualification.data["new_contract_digest"],
            )
        self.assertEqual("T1", receipt.data["target_stage"])
        self.assertEqual(
            ["T1", "C1", "Q1", "P1", "H1"],
            receipt.data["invalidated_stages"],
        )
        self.assertEqual(
            preserved, migrated.state.data["current_stage_completions"]
        )
        self.assertEqual({"B0", "S1", "W1", "E1"}, set(preserved))
        self.assertIsNone(migrated.store.pending_work_order())
        rejection = (
            self.root
            / "orchestration/work-orders"
            / f"{pending_t1.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejection.is_file())
        executor = mock.Mock()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.execute_stage_work(
                migrated,
                work_order=pending_t1,
                actor=prod.ACTION_CONTRACT["T1"][1],
                executor=executor,
            )
        self.assertEqual("PROD_WORK_ORDER_REJECTED", caught.exception.code)
        executor.assert_not_called()

    def test_contract_upgrade_recovery_finishes_prepared_receipts(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(
                    stage,
                    revision,
                    model_version="2.3" if stage == "E1" else None,
                ),
            )
        stale_gate = context.coordinator.build_input_gate(
            "T1", "orchestration/input-gates/stale-recovery-t1/input-gate.json"
        )
        context.store.persist_document(stale_gate)
        pending_t1 = context.store.issue_work_order(
            run_id=context.state.data["run_id"],
            action="T1",
            state=context.state,
            input_gate=stale_gate,
            h1_workspace=None,
            required_actor=prod.ACTION_CONTRACT["T1"][1],
            inputs={},
        )
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-RECOVERY-001",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="environment",
            problem="Recover an interrupted qualification migration.",
            evidence_ids=["E1-CONTRACT-UPGRADE-RECOVERY"],
            violated_contract="E1 2.4 capability readiness",
            required_revision=(
                "Use contract "
                + prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            ),
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data, "returns/RET-CONTRACT-UPGRADE-RECOVERY-001.json"
        )
        with mock.patch.object(
            context.store,
            "complete_contract_upgrade",
            side_effect=RuntimeError("simulated process death after state write"),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated process death"):
                prod.apply_contract_upgrade(
                    context,
                    request=request,
                    old_contract_digest=prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
                )
        self.assertFalse(
            (
                self.root / "orchestration" / "work-orders"
                / f"{pending_t1.data['work_id']}.rejected.json"
            ).exists()
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(request.reference, resumed.active_return.reference)
        self.assertTrue(
            (
                self.root / "orchestration" / "work-orders"
                / f"{pending_t1.data['work_id']}.rejected.json"
            ).is_file()
        )
        upgrade = resumed.store.current_contract_upgrade()
        self.assertIsNotNone(upgrade)
        self.assertEqual("complete", upgrade.data["status"])

    def test_stale_run_without_qualification_has_migration_only_resume(self) -> None:
        context = self._context()
        for revision, stage in enumerate(("B0", "S1", "W1", "E1"), 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(
                    stage,
                    revision,
                    model_version="2.3" if stage == "E1" else None,
                ),
            )
        (self.root / "orchestration/current-contract-upgrade.json").unlink()
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.resume_production_run(self.root)
        stale = prod.resume_production_run_for_contract_upgrade(self.root)
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.issue_stage_work(stale, action="T1", inputs={})
        request_data = rt.route_return(
            run_id="RUN-PROD-1",
            return_id="RET-CONTRACT-UPGRADE-NO-QUALIFICATION",
            origin_kind="stage",
            origin_stage="T1",
            issue_kind="environment",
            problem="Sealed E1 uses a stale production contract.",
            evidence_ids=["E1-STALE-CONTRACT"],
            violated_contract="E1 production qualification",
            required_revision="Migrate the sealed stale E1 contract.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
        )
        request = rt.seal_document(
            request_data,
            "returns/RET-CONTRACT-UPGRADE-NO-QUALIFICATION.json",
        )
        e1_reference = stale.state.data["current_stage_completions"]["E1"]
        old_digest = rt.canonical_sha256(
            prod._completion_contract_identity(stale.store, e1_reference)
        )
        receipt, migrated = prod.apply_contract_upgrade(
            stale,
            request=request,
            old_contract_digest=old_digest,
        )
        self.assertEqual("complete", receipt.data["status"])
        self.assertEqual(
            prod.CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            migrated.store.current_contract_upgrade().data["new_contract_digest"],
        )

    def test_wrong_actor_is_rejected_before_executor_and_keeps_order_pending(self) -> None:
        context = self._context()
        _, order = prod.issue_stage_work(context, action="B0", inputs={})
        executor = mock.Mock(side_effect=self._fake_executor("B0", 1))
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.execute_stage_work(
                context,
                work_order=order,
                actor="novel-development-map-designer",
                executor=executor,
            )
        self.assertEqual("PROD_WORK_ACTOR_MISMATCH", caught.exception.code)
        executor.assert_not_called()
        self.assertEqual(0, context.store.latest_state().data["revision"])
        _, successor = prod.execute_stage_work(
            context,
            work_order=order,
            actor="baseline-controller",
            executor=self._fake_executor("B0", 1),
        )
        self.assertEqual(1, successor.state.data["revision"])

    def test_resume_reconciles_state_successor_before_consumed_marker(self) -> None:
        context = self._context()
        gate, order = prod.issue_stage_work(context, action="B0", inputs={})
        receipt = self._fake_executor("B0", 1)(context.coordinator, gate)
        successor = rt.SealedDocument(
            receipt.transition.snapshot, receipt.transition.reference
        )
        prod._prepare_state_commit(
            context, order, successor, receipt.completion
        )
        context.store.persist_state(successor)

        resumed = prod.resume_production_run(self.root)
        self.assertEqual(1, resumed.state.data["revision"])
        _, next_order = prod.issue_stage_work(
            resumed, action="S1", inputs={}
        )
        self.assertEqual("S1", next_order.data["action"])

    def test_resume_rejects_unjournaled_direct_state_successor(self) -> None:
        context = self._context()
        gate, _order = prod.issue_stage_work(context, action="B0", inputs={})
        receipt = self._fake_executor("B0", 1)(context.coordinator, gate)
        successor = rt.SealedDocument(
            receipt.transition.snapshot, receipt.transition.reference
        )
        context.store.persist_state(successor)
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.resume_production_run(self.root)
        self.assertEqual("PROD_UNJOURNALED_SUCCESSOR", caught.exception.code)

    def test_commit_prepare_rejects_extra_stage_and_store_cannot_self_sign(self) -> None:
        context = self._context()
        gate, order = prod.issue_stage_work(context, action="B0", inputs={})
        receipt = self._fake_executor("B0", 1)(context.coordinator, gate)
        forged = dict(receipt.transition.snapshot)
        forged["current_stage_completions"] = {
            **forged["current_stage_completions"],
            "S1": {
                "stage": "S1",
                "path": "S1/stage-completion.json",
                "sha256": "6" * 64,
            },
        }
        forged_successor = rt.seal_document(
            forged, "state/revision-001.json"
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod._prepare_state_commit(
                context, order, forged_successor, receipt.completion
            )
        self.assertEqual("PROD_COMMIT_DELTA_INVALID", caught.exception.code)
        self.assertFalse(hasattr(context.store, "persist_commit_intent"))

    def test_commit_prepare_rejects_early_approved_ready_control_state(self) -> None:
        context = self._context()
        gate, order = prod.issue_stage_work(context, action="B0", inputs={})
        receipt = self._fake_executor("B0", 1)(context.coordinator, gate)
        forged = dict(receipt.transition.snapshot)
        forged["status"] = "approved"
        forged["development_status"] = "ready"
        forged["author_decision"] = {
            "path": "author/forged-decision.json",
            "sha256": "7" * 64,
        }
        forged_successor = rt.seal_document(
            forged, "state/revision-001.json"
        )
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod._prepare_state_commit(
                context, order, forged_successor, receipt.completion
            )
        self.assertEqual("PROD_COMMIT_DELTA_INVALID", caught.exception.code)

    def test_prepared_intent_without_successor_remains_pending(self) -> None:
        context = self._context()
        gate, order = prod.issue_stage_work(context, action="B0", inputs={})
        receipt = self._fake_executor("B0", 1)(context.coordinator, gate)
        successor = rt.SealedDocument(
            receipt.transition.snapshot, receipt.transition.reference
        )
        prod._prepare_state_commit(
            context, order, successor, receipt.completion
        )
        resumed = prod.resume_production_run(self.root)
        self.assertEqual(0, resumed.state.data["revision"])
        self.assertEqual(
            order.reference, resumed.store.pending_work_order().reference
        )

    def test_forged_work_order_object_is_rejected(self) -> None:
        context = self._context()
        _, order = prod.issue_stage_work(context, action="B0", inputs={})
        forged = rt.SealedDocument(
            data={**order.data, "inputs": {"forged": True}},
            reference=order.reference,
        )
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            prod.execute_stage_work(
                context,
                work_order=forged,
                actor="baseline-controller",
                executor=self._fake_executor("B0", 1),
            )
        self.assertEqual("PROD_WORK_ORDER_FORGED", caught.exception.code)

    def test_initialize_existing_run_fails_and_workspace_recovers(self) -> None:
        context = self._context()
        with self.assertRaises(store_module.ProductionStoreError) as caught:
            self._context()
        self.assertEqual("PROD_RUN_EXISTS", caught.exception.code)
        workspace = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": "H1-SESSION",
                "state": "initialized",
                "p1_completion": {
                    "stage": "P1",
                    "path": "P1/stage-completion.json",
                    "sha256": "2" * 64,
                },
                "previous_state_sha256": None,
                "artifacts": {},
            },
            "H1/H1-SESSION/workspace-initialized.json",
        )
        context.store.persist_workspace(workspace)
        self.assertEqual(
            workspace.reference, context.store.latest_workspace().reference
        )

    def test_h1_workspace_initialization_is_idempotent_but_not_replaceable(self) -> None:
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        workspace = prod.initialize_h1_workspace(
            context, session_id="H1-SESSION-1"
        )
        replay = prod.initialize_h1_workspace(
            context, session_id="H1-SESSION-1"
        )
        self.assertEqual(workspace.reference, replay.reference)
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.initialize_h1_workspace(context, session_id="H1-SESSION-2")
        self.assertEqual("PROD_H1_SESSION_EXISTS", caught.exception.code)

    def test_h1_work_order_binds_workspace_and_resume_reconciles_successor(self) -> None:
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        initialized = prod.initialize_h1_workspace(
            context, session_id="H1-BOUND"
        )
        _, order = prod.issue_stage_work(
            context, action="H1-A-plan", inputs={}
        )
        self.assertEqual(initialized.reference, order.data["h1_workspace"])
        item = {"path": "H1/H1-BOUND/plan/item.json", "sha256": "5" * 64}
        manifest = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "package_profile": "h1-plan",
                "verdict": "ready",
                "files": [item],
                "artifact_roles": {
                    "source_inventory": item,
                    "review_plan": item,
                    "fragment_briefs": item,
                    "generation_session": item,
                    "generation_evidence_index": item,
                    "execution_record": item,
                },
                "validation": item,
                "implementation": [item],
                "parent_state_sha256": initialized.reference["sha256"],
                "session_id": "H1-BOUND",
            },
            "H1/H1-BOUND/plan/package-manifest.json",
        )
        planned = rt.seal_document(
            {
                **initialized.data,
                "state": "planned",
                "previous_state_sha256": initialized.reference["sha256"],
                "artifacts": {"plan_manifest": manifest.reference},
            },
            "H1/H1-BOUND/workspace-planned.json",
        )
        prod._prepare_h1_commit(
            context,
            order,
            bound=initialized,
            successor=planned,
            manifest=manifest,
        )
        context.store.persist_workspace(planned)

        resumed = prod.resume_production_run(self.root)
        _, next_order = prod.issue_stage_work(
            resumed, action="H1-B", inputs={}
        )
        self.assertEqual(planned.reference, next_order.data["h1_workspace"])

    def test_resume_rejects_unjournaled_h1_workspace_successor(self) -> None:
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        initialized = prod.initialize_h1_workspace(
            context, session_id="H1-UNJOURNALED"
        )
        prod.issue_stage_work(context, action="H1-A-plan", inputs={})
        planned = rt.seal_document(
            {
                **initialized.data,
                "state": "planned",
                "previous_state_sha256": initialized.reference["sha256"],
                "artifacts": {
                    "plan_manifest": {
                        "path": "H1/H1-UNJOURNALED/plan/package-manifest.json",
                        "sha256": "4" * 64,
                    }
                },
            },
            "H1/H1-UNJOURNALED/workspace-planned.json",
        )
        context.store.persist_workspace(planned)
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.resume_production_run(self.root)
        self.assertEqual("PROD_UNJOURNALED_SUCCESSOR", caught.exception.code)

    def test_h1_commit_rejects_workspace_pointer_divergence_before_executor(self) -> None:
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        initialized = prod.initialize_h1_workspace(
            context, session_id="H1-ORIGINAL"
        )
        _, order = prod.issue_stage_work(
            context, action="H1-A-plan", inputs={}
        )
        foreign = rt.seal_document(
            {**initialized.data, "session_id": "H1-FOREIGN"},
            "H1/H1-FOREIGN/workspace-initialized.json",
        )
        context.store.persist_workspace(foreign)
        executor = mock.Mock()
        with self.assertRaises(prod.ProductionOrchestratorError) as caught:
            prod.commit_h1_workspace(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT["H1-A-plan"][1],
                executor=executor,
            )
        self.assertEqual("PROD_H1_WORKSPACE_STALE", caught.exception.code)
        executor.assert_not_called()

    def test_concurrent_pending_publication_has_one_winner(self) -> None:
        context = self._context()

        def issue(candidate):
            try:
                return prod.issue_stage_work(
                    context, action="B0", inputs={"candidate": candidate}
                )[1].data["work_id"]
            except store_module.ProductionStoreError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(issue, (1, 2)))
        self.assertEqual(1, results.count("PROD_PENDING_WORK_EXISTS"))
        self.assertEqual(1, sum(value != "PROD_PENDING_WORK_EXISTS" for value in results))

    def _waiting_author_context(self):
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(
                context, action=stage, inputs={}
            )
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        workspace = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": "H1-READY",
                "state": "rendered",
                "p1_completion": context.state.data[
                    "current_stage_completions"
                ]["P1"],
                "previous_state_sha256": "3" * 64,
                "artifacts": {
                    "plan_manifest": {"path": "H1/plan.json", "sha256": "4" * 64},
                    "fragment_manifest": {"path": "H1/fragments.json", "sha256": "5" * 64},
                    "assembly_manifest": {"path": "H1/assembly.json", "sha256": "6" * 64},
                    "html_manifest": {"path": "H1/html.json", "sha256": "7" * 64},
                },
            },
            "H1/H1-READY/workspace-rendered.json",
        )
        context.store.persist_workspace(workspace)
        _, order = prod.issue_stage_work(
            context, action="H1-publish", inputs={}
        )
        gate = context.store.load_document(order.data["input_gate"])
        completion = rt.seal_stage_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "status": "ready",
                "manifest": {"path": "H1/stage/package-manifest.json", "sha256": "8" * 64},
                "validation": {"path": "H1/stage/validation.json", "sha256": "9" * 64},
                "input_gate": gate.reference,
                "state_before": gate.data["run_state"],
                "previous_stage_completions": gate.data["upstream_completions"],
                "return_binding": None,
                "session_id": "H1-READY",
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
        return prod.resume_production_run(self.root)

    def test_h1_publish_uses_exact_work_order_gate_and_rejects_override(self):
        context = self._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, stage_order = prod.issue_stage_work(
                context, action=stage, inputs={}
            )
            _, context = prod.execute_stage_work(
                context,
                work_order=stage_order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self._fake_executor(stage, revision),
            )
        rendered = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": "H1-PUBLISH-GATE",
                "state": "rendered",
                "p1_completion": context.state.data[
                    "current_stage_completions"
                ]["P1"],
                "previous_state_sha256": "3" * 64,
                "artifacts": {
                    "plan_manifest": {"path": "H1/plan.json", "sha256": "4" * 64},
                    "fragment_manifest": {"path": "H1/fragments.json", "sha256": "5" * 64},
                    "assembly_manifest": {"path": "H1/assembly.json", "sha256": "6" * 64},
                    "html_manifest": {"path": "H1/html.json", "sha256": "7" * 64},
                },
            },
            "H1/H1-PUBLISH-GATE/workspace-rendered.json",
        )
        context.store.persist_workspace(rendered)
        _, order = prod.issue_stage_work(
            context, action="H1-publish", inputs={}
        )
        work_gate = context.store.load_document(order.data["input_gate"])
        wrong_gate = rt.seal_document(
            copy.deepcopy(work_gate.data),
            "orchestration/input-gates/foreign-H1-publish/input-gate.json",
        )
        publisher = mock.Mock()
        before = context.store.latest_state()
        with mock.patch.object(prod, "publish_h1_completion", publisher), self.assertRaises(
            prod.ProductionOrchestratorError
        ) as caught:
            prod.publish_h1_transaction(
                context,
                self.root / "H1/stage",
                work_order=order,
                rendered_workspace=rendered,
                plan_input_gate=work_gate,
                admission_input_gate=wrong_gate,
            )
        self.assertEqual("PROD_H1_ADMISSION_GATE_MISMATCH", caught.exception.code)
        publisher.assert_not_called()
        self.assertEqual(before, context.store.latest_state())

        with (
            mock.patch.object(prod, "publish_h1_completion", publisher),
            self.assertRaises(prod.ProductionOrchestratorError) as caught,
        ):
            prod.publish_h1_transaction(
                context,
                self.root / "H1/stage",
                work_order=order,
                rendered_workspace=rendered,
                plan_input_gate=work_gate,
            )
        self.assertEqual(
            "PROD_H1_READABILITY_REVIEW_REQUIRED", caught.exception.code
        )
        publisher.assert_not_called()

        with (
            mock.patch.object(prod, "publish_h1_completion", publisher),
            self.assertRaises(prod.ProductionOrchestratorError) as caught,
        ):
            prod.publish_h1_transaction(
                context,
                self.root / "H1/stage-attempt-02",
                work_order=order,
                rendered_workspace=rendered,
                plan_input_gate=work_gate,
            )
        self.assertEqual(
            "PROD_H1_OUTPUT_PATH_MISMATCH", caught.exception.code
        )
        publisher.assert_not_called()

        with (
            mock.patch.object(prod, "publish_h1_completion", publisher),
            self.assertRaises(prod.ProductionOrchestratorError) as caught,
        ):
            prod.publish_h1_transaction(
                context,
                self.root / "H1/stage-attempt-02",
                work_order=order,
                rendered_workspace=rendered,
                plan_input_gate=work_gate,
                logical_package_path="H1/stage-attempt-02",
            )
        self.assertEqual(
            "PROD_H1_READABILITY_REVIEW_REQUIRED", caught.exception.code
        )
        publisher.assert_not_called()

        completion = rt.seal_stage_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "status": "ready",
                "manifest": {"path": "H1/stage/package-manifest.json", "sha256": "8" * 64},
                "validation": {"path": "H1/stage/validation.json", "sha256": "9" * 64},
                "input_gate": work_gate.reference,
                "state_before": work_gate.data["run_state"],
                "previous_stage_completions": work_gate.data["upstream_completions"],
                "return_binding": work_gate.data["return_binding"],
                "session_id": rendered.data["session_id"],
            },
            "H1",
            "H1/stage/stage-completion.json",
        )
        fresh = prod.ProductionCoordinator.from_snapshot(
            copy.deepcopy(context.state.data),
            copy.deepcopy(context.state.reference),
            active_return_request=context.active_return,
            runtime=context.store.runtime,
        )
        transition = fresh.accept_stage_completion(
            gate=work_gate,
            completion=completion,
            h1_workspace=rendered.reference,
            next_state_path="state/revision-009.json",
            active_return_request=context.active_return,
        )

        def fake_publish(_root, **kwargs):
            self.assertEqual(work_gate, kwargs["admission_input_gate"])
            self.assertEqual(readability_review, kwargs["human_readability_review"])
            return types.SimpleNamespace(
                transition=transition, completion=completion
            )

        readability_review = rt.seal_document(
            {"review_id": "H1-READABILITY-TEST"},
            "reviews/h1-human-readability/H1-READABILITY-TEST.json",
        )
        context.store.persist_document(readability_review)
        for code in (
            "H1_READABILITY_REVIEW_NOT_PASS",
            "H1_READABILITY_REVIEW_STALE",
        ):
            with (
                mock.patch.object(prod, "publish_h1_completion", publisher),
                mock.patch.object(
                    prod,
                    "h1_readability_prepublish_contract",
                    return_value=(
                        {"bound": True},
                        [{"task_id": "producer", "thread_id": "producer-thread"}],
                    ),
                ),
                mock.patch.object(
                    prod,
                    "validate_h1_readability_review",
                    side_effect=prod.H1ReadabilityError(code, "rejected"),
                ),
                self.assertRaises(prod.ProductionOrchestratorError),
            ):
                prod.publish_h1_transaction(
                    context,
                    self.root / "H1/stage",
                    work_order=order,
                    rendered_workspace=rendered,
                    plan_input_gate=work_gate,
                    human_readability_review=readability_review,
                    plan_package=self.root / "H1/plan",
                    fragment_package=self.root / "H1/fragments",
                    assembly_package=self.root / "H1/assembly",
                    html_package=self.root / "H1/html",
                )
            publisher.assert_not_called()
        with (
            mock.patch.object(prod, "publish_h1_completion", fake_publish),
            mock.patch.object(
                prod,
                "h1_readability_prepublish_contract",
                return_value=({"bound": True}, [{"task_id": "producer", "thread_id": "producer-thread"}]),
            ),
            mock.patch.object(prod, "validate_h1_readability_review"),
        ):
            _, successor = prod.publish_h1_transaction(
                context,
                self.root / "H1/stage",
                work_order=order,
                rendered_workspace=rendered,
                plan_input_gate=work_gate,
                human_readability_review=readability_review,
                plan_package=self.root / "H1/plan",
                fragment_package=self.root / "H1/fragments",
                assembly_package=self.root / "H1/assembly",
                html_package=self.root / "H1/html",
            )
        self.assertEqual("waiting_author", successor.state.data["status"])

    def test_waiting_author_and_approved_final_transactions_resume(self) -> None:
        waiting = self._waiting_author_context()
        self.assertEqual("waiting_author", waiting.state.data["status"])
        _, author_order = prod.issue_stage_work(
            waiting, action="author-decision", inputs={"external": True}
        )
        event = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "approval_scope": "conception",
                "decision": "approved",
                "machine_package": {
                    "completion_path": "P1/stage-completion.json",
                    "completion_sha256": "a" * 64,
                    "manifest_path": "P1/package-manifest.json",
                    "manifest_sha256": "b" * 64,
                },
                "human_review_package": {
                    "completion_path": "H1/stage/stage-completion.json",
                    "completion_sha256": "c" * 64,
                    "manifest_path": "H1/stage/package-manifest.json",
                    "manifest_sha256": "d" * 64,
                    "html_path": "H1/html/report.html",
                    "html_sha256": "e" * 64,
                },
                "approval_record": {"event_seq": 1, "text": "approved"},
                "unresolved_items": [],
            },
            "author/decision.json",
        )
        _, approved = prod.record_author_transaction(
            waiting, work_order=author_order, event=event
        )
        approved = prod.resume_production_run(self.root)
        self.assertEqual("approved", approved.state.data["status"])
        _, final_order = prod.issue_stage_work(
            approved, action="final", inputs={}
        )

        def fake_final(_root, *, coordinator, next_state_path, **_kwargs):
            completion = rt.seal_document(
                {
                    "schema_version": "2.0",
                    "run_id": "RUN-PROD-1",
                    "status": "ready",
                    "run_state": coordinator.state_reference,
                    "stage_completions": coordinator.state["current_stage_completions"],
                    "p1_manifest": {"path": "P1/package-manifest.json", "sha256": "1" * 64},
                    "h1_html_manifest": {"path": "H1/html/package-manifest.json", "sha256": "2" * 64},
                    "author_decision": event.reference,
                    "development_handoff": {"path": "P1/development-handoff.json", "sha256": "3" * 64},
                    "validation": {"path": "completion/validation.json", "sha256": "4" * 64},
                },
                "completion/conception-completion.json",
            )
            transition = coordinator.accept_final_completion(
                completion=completion, next_state_path=next_state_path
            )
            return types.SimpleNamespace(
                transition=transition, completion=completion
            )

        with mock.patch.object(prod, "publish_final_completion", fake_final):
            _, final = prod.publish_final_transaction(
                approved,
                self.root / "completion",
                work_order=final_order,
            )
        final = prod.resume_production_run(self.root)
        self.assertEqual("ready", final.state.data["development_status"])

    def test_revise_uses_revisioned_gate_without_overwriting_forward_gate(self) -> None:
        waiting = self._waiting_author_context()
        _, author_order = prod.issue_stage_work(
            waiting, action="author-decision", inputs={"external": True}
        )
        event = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "approval_scope": "conception",
                "decision": "revise",
                "machine_package": {
                    "completion_path": "P1/stage-completion.json",
                    "completion_sha256": "a" * 64,
                    "manifest_path": "P1/package-manifest.json",
                    "manifest_sha256": "b" * 64,
                },
                "human_review_package": {
                    "completion_path": "H1/stage/stage-completion.json",
                    "completion_sha256": "c" * 64,
                    "manifest_path": "H1/stage/package-manifest.json",
                    "manifest_sha256": "d" * 64,
                    "html_path": "H1/html/report.html",
                    "html_sha256": "e" * 64,
                },
                "revision_record": {
                    "event_seq": 2,
                    "text": "Revise the approved intent baseline.",
                },
                "revision_targets": [
                    {
                        "target_scope": "conception",
                        "visible_element_ids": [],
                        "source_ids": ["INT-001"],
                        "requested_change": "Revise the intent baseline.",
                    }
                ],
            },
            "author/revise-decision.json",
        )
        _, revised = prod.record_author_transaction(
            waiting,
            work_order=author_order,
            event=event,
            return_id="RET-PRODUCTION-ROUND-1",
        )
        revised = prod.resume_production_run(self.root)
        self.assertEqual("revise", revised.state.data["status"])
        self.assertEqual(
            "RET-PRODUCTION-ROUND-1",
            revised.active_return.data["return_id"],
        )
        forward_gate = self.root / "orchestration/input-gates/revision-000-B0/input-gate.json"
        self.assertTrue(forward_gate.is_file())
        gate, order = prod.issue_stage_work(
            revised, action="B0", inputs={"return": True}
        )
        self.assertNotEqual(
            "orchestration/input-gates/revision-000-B0/input-gate.json",
            gate.reference["path"],
        )
        self.assertEqual("B0", order.data["action"])


if __name__ == "__main__":
    unittest.main()
