from __future__ import annotations

import copy
import importlib
import shutil
import types
import unittest
from pathlib import Path
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
readability_tests = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests."
    "test_internal_h1_readability_return"
)
readability = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_readability"
)
h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)


class InternalH1ImplementationRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = readability_tests.InternalH1ReadabilityReturnTests(
            methodName="runTest"
        )
        self.base.setUp()
        self.root = self.base.root

    def tearDown(self) -> None:
        self.base.tearDown()

    def _persist_package(
        self,
        context,
        *,
        logical_root: str,
        session_id: str,
        stale_implementation: bool,
    ):
        package_root = self.root / Path(*logical_root.split("/"))
        package_root.mkdir(parents=True, exist_ok=True)
        session = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": context.state.data["run_id"],
                "stage": "H1",
                "session_id": session_id,
            },
            f"{logical_root}/generation-session.json",
        )
        context.store.persist_document(session)
        implementation_paths: list[str] = []
        if stale_implementation:
            for identity, source in sorted(h1a._implementation_paths().items()):
                target = package_root / "implementation" / Path(*identity.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                if identity == "skill/run_v2.py":
                    target.write_bytes(Path(source).read_bytes() + b"\n# sealed-old\n")
                else:
                    shutil.copyfile(source, target)
                implementation_paths.append(f"implementation/{identity}")
            profile = "h1-plan"
            role_paths = {
                "source_inventory": "source-inventory.json",
                "review_plan": "review-plan.json",
                "fragment_briefs": "fragment-briefs.json",
                "generation_session": "generation-session.json",
                "generation_evidence_index": "generation-evidence-index.json",
                "execution_record": "execution-record.json",
            }
        else:
            implementation_target = package_root / "implementation/writer.py"
            implementation_target.parent.mkdir(parents=True, exist_ok=True)
            implementation_target.write_text("# writer fixture\n", encoding="utf-8")
            implementation_paths.append("implementation/writer.py")
            profile = "h1-fragments"
            role_paths = {
                "execution_record": "execution-record.json",
                "fragment_package": "fragment-package.json",
                "fragments": "fragments.md",
                "generation_evidence_index": "generation-evidence-index.json",
                "generation_session": "generation-session.json",
                "session_workspace_completion": "session-workspace-completion.json",
            }
        for relative in sorted(set(role_paths.values()) | {"validation.json"}):
            target = package_root / relative
            if target.exists():
                continue
            if target.suffix == ".md":
                target.write_text("fixture\n", encoding="utf-8", newline="")
            else:
                target.write_text(
                    rt.canonical_json({"fixture": relative}),
                    encoding="utf-8",
                    newline="",
                )
        files = [
            rt.artifact_reference(path, root=package_root)
            for path in sorted(package_root.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        ]
        by_path = {item["path"]: item for item in files}
        manifest = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": context.state.data["run_id"],
                "stage": "H1",
                "package_profile": profile,
                "verdict": "ready",
                "files": files,
                "artifact_roles": {
                    role: by_path[path] for role, path in role_paths.items()
                },
                "validation": by_path["validation.json"],
                "implementation": [by_path[path] for path in implementation_paths],
                "parent_state_sha256": context.store.latest_workspace().reference[
                    "sha256"
                ],
                "session_id": session_id,
            },
            f"{logical_root}/package-manifest.json",
        )
        context.store.persist_document(manifest)
        return manifest

    def _commit_workspace(self, context, order, manifest, next_state: str):
        current = context.store.latest_workspace()

        def execute(coordinator, _gate):
            transition = coordinator.accept_h1_workspace_transition(
                current_workspace=current,
                package_manifest=manifest,
                expected_next_state=next_state,
                active_return_request=context.active_return,
            )
            return types.SimpleNamespace(
                manifest=copy.deepcopy(manifest.data), transition=transition
            )

        _receipt, workspace = prod.commit_h1_workspace(
            context,
            work_order=order,
            actor=order.data["required_actor"],
            executor=execute,
        )
        return workspace

    def _active_h1_assemble(self):
        context, _old, completion, manifest, prepublish = self.base._waiting_author()
        failure, request = self.base._failure_and_request(
            context, prepublish, completion, manifest
        )
        with mock.patch.object(
            prod,
            "h1_readability_prepublish_contract",
            return_value=(
                prepublish,
                [{"task_id": "plan-producer", "thread_id": "plan-thread"}],
            ),
        ):
            _receipt, context, initialized, _gate, plan_order = (
                prod.apply_internal_h1_readability_return(
                    context,
                    readability_failure=failure,
                    request=request,
                    actor="production-orchestrator",
                )
            )
        plan_manifest = self._persist_package(
            context,
            logical_root="H1/plan-stale-implementation",
            session_id=initialized.data["session_id"],
            stale_implementation=True,
        )
        self._commit_workspace(context, plan_order, plan_manifest, "planned")
        context = prod.resume_production_run(self.root)
        _gate, fragment_order = prod.issue_stage_work(
            context, action="H1-B", inputs={}
        )
        fragment_manifest = self._persist_package(
            context,
            logical_root="H1/fragments-stale-implementation",
            session_id=initialized.data["session_id"],
            stale_implementation=False,
        )
        self._commit_workspace(
            context, fragment_order, fragment_manifest, "fragments_ready"
        )
        context = prod.resume_production_run(self.root)
        _gate, assemble_order = prod.issue_stage_work(
            context, action="H1-A-assemble", inputs={}
        )
        return context, request, assemble_order, plan_manifest, fragment_manifest

    def test_success_invalidates_stale_h1_and_reissues_plan(self):
        context, old_request, old_order, plan_manifest, fragment_manifest = (
            self._active_h1_assemble()
        )
        upstream = copy.deepcopy(context.state.data["current_stage_completions"])
        receipt, refreshed, failure, request, gate, order = (
            prod.apply_internal_h1_implementation_refresh(
                context, actor="production-orchestrator"
            )
        )
        self.assertEqual("complete", receipt.data["status"])
        self.assertEqual("active_stage_return_refresh", receipt.data["transition_mode"])
        self.assertEqual(old_request.reference, receipt.data["superseded_return"])
        self.assertEqual(request.reference, refreshed.state.data["active_return"])
        self.assertEqual(upstream, refreshed.state.data["current_stage_completions"])
        self.assertEqual("H1A_IMPLEMENTATION_STALE", failure.data["code"])
        self.assertEqual(plan_manifest.reference, failure.data["plan_manifest"])
        self.assertEqual(fragment_manifest.reference, failure.data["fragment_manifest"])
        self.assertEqual("H1-A-plan", order.data["action"])
        self.assertEqual(gate.reference, order.data["input_gate"])
        initialized = refreshed.store.load_document(order.data["h1_workspace"])
        self.assertEqual("initialized", initialized.data["state"])
        self.assertEqual(initialized.reference, refreshed.store.latest_workspace().reference)
        rejected = self.root / "orchestration/work-orders" / (
            f"{old_order.data['work_id']}.rejected.json"
        )
        self.assertTrue(rejected.is_file())
        replay = prod.resume_production_run(self.root)
        self.assertEqual(refreshed.state.reference, replay.state.reference)
        self.assertEqual(order.reference, replay.store.pending_work_order().reference)

    def test_wrong_actor_is_zero_state_write(self):
        context, _old, _order, _plan, _fragment = self._active_h1_assemble()
        before = context.store.latest_state()
        with self.assertRaises(prod.ProductionOrchestratorError):
            prod.apply_internal_h1_implementation_refresh(
                context, actor="novel-conception-human-review-assembler"
            )
        self.assertEqual(before, context.store.latest_state())

    def test_prepared_recovery_replays_exact_h1_workspace(self):
        context, _old, _order, _plan, _fragment = self._active_h1_assemble()
        captured = {}

        def interrupt(prepared, *, successor):
            captured["plan"] = prepared
            captured["successor"] = successor
            raise RuntimeError(f"simulated crash:{successor.reference['sha256']}")

        with (
            mock.patch.object(
                context.store,
                "complete_contract_upgrade",
                side_effect=interrupt,
            ),
            self.assertRaisesRegex(RuntimeError, "simulated crash"),
        ):
            prod.apply_internal_h1_implementation_refresh(
                context, actor="production-orchestrator"
            )
        prepared = captured["plan"]
        successor = captured["successor"]
        predecessor = context.store.load_document(prepared.data["predecessor_state"])
        request = context.store.load_document(prepared.data["return_request"])
        failure = context.store.load_document(
            prepared.data["stale_identity"]["implementation_failure"]
        )
        post = [
            rt.SealedDocument(dict(item["data"]), dict(item["reference"]))
            for item in prepared.data["post_upgrade_documents"]
        ]
        initialized = next(
            item
            for item in post
            if item.reference
            == prepared.data["stale_identity"]["initialized_workspace"]
        )
        order = next(
            item
            for item in post
            if item.reference == prepared.data["post_upgrade_work_order"]
        )
        stale = prepared.data["stale_identity"]
        old_workspace = context.store.load_document(stale["current_workspace"])
        plan_manifest = context.store.load_document(stale["plan_manifest"])
        fragment_manifest = context.store.load_document(stale["fragment_manifest"])
        qualification = context.store.current_contract_upgrade()
        expected_p1 = str(
            context.store.resolve_completion_package_root(
                successor.data["current_stage_completions"]["P1"],
                expected_stage="P1",
            )
        )
        checks = {
            "predecessor_status": predecessor.data["status"] == "revise",
            "predecessor_active": predecessor.data["active_return"]
            == prepared.data["superseded_return"],
            "successor_active": successor.data["active_return"] == request.reference,
            "request_evidence": request.data["evidence_ids"]
            == [failure.data["failure_id"]],
            "initialized_p1": initialized.data["p1_completion"]
            == successor.data["current_stage_completions"]["P1"],
            "order_action": order.data["action"] == "H1-A-plan",
            "order_workspace": order.data["h1_workspace"] == initialized.reference,
            "post_count": len(post) == 3,
            "author_null": predecessor.data["author_decision"] is None,
            "request_origin": request.data["origin_stage"] == "H1",
            "request_owner": request.data["calculated_owner"] == "H1-A",
            "request_resume": request.data["resume_point"] == "H1-A-plan",
            "request_invalidates": request.data["invalidated_h1_artifacts"]
            == ["plan", "fragments", "assembly", "html", "completion"],
            "old_workspace_state": old_workspace.data["state"]
            == "fragments_ready",
            "old_workspace_artifacts": old_workspace.data["artifacts"]
            == {
                "plan_manifest": plan_manifest.reference,
                "fragment_manifest": fragment_manifest.reference,
            },
            "initialized_shape": initialized.data["previous_state_sha256"] is None
            and initialized.data["artifacts"] == {},
            "old_digest": prepared.data["old_contract_digest"]
            == qualification.data["new_contract_digest"],
            "prior_qualification": prepared.data["prior_qualification"]
            == qualification.reference,
            "generation": prepared.data["refresh_generation"]
            == qualification.data.get("refresh_generation", 0) + 1,
            "order_inputs": order.data["inputs"]
            == prepared.data["post_upgrade_inputs"],
            "p1_input": prepared.data["post_upgrade_inputs"]["p1_package"]
            == expected_p1,
        }
        self.assertTrue(all(checks.values()), checks)
        recovered = prod.resume_production_run(self.root)
        order = recovered.store.pending_work_order()
        self.assertEqual("H1-A-plan", order.data["action"])
        self.assertEqual(
            order.data["h1_workspace"], recovered.store.latest_workspace().reference
        )


if __name__ == "__main__":
    unittest.main()
