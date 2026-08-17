from __future__ import annotations

import copy
import importlib
import json
import shutil
import types
import unittest
from pathlib import Path


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
legacy = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)


class GateAuthoritativeInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = legacy.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.doCleanups()
        self.fixture.tearDown()

    def _advance(self, through: tuple[str, ...]):
        context = self.fixture._context()
        orders = {}
        for revision, stage in enumerate(through, 1):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            orders[stage] = order
            sealed = prod._sealed_executor_inputs(order)

            def execute(coordinator, gate, bindings, *, _stage=stage, _revision=revision):
                self.assertEqual(bindings, sealed)
                return self.fixture._fake_executor(_stage, _revision)(coordinator, gate)

            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=execute,
                input_bindings=sealed,
            )
        return context, orders

    def test_mixed_attempt_beats_superseded_flat_and_actor_mappings(self):
        context, _ = self._advance(("B0", "S1", "W1", "E1", "T1", "C1", "Q1"))
        stale = self.root / "B0"
        stale.mkdir(exist_ok=True)
        (stale / "stage-completion.json").write_text("{}", encoding="utf-8")
        _, p1_order = prod.issue_stage_work(context, action="P1", inputs={})
        inputs = prod._sealed_executor_inputs(p1_order)
        for stage in ("B0", "S1", "W1", "E1", "T1", "C1", "Q1"):
            self.assertEqual(
                context.store.resolve_physical_path(
                    inputs[prod.PACKAGE_INPUT_FIELDS[stage]]
                ),
                (self.root / stage / f"attempt-{('B0','S1','W1','E1','T1','C1','Q1').index(stage)+1:03d}").resolve(),
            )
        self.assertEqual(prod.ACTION_PACKAGE_INPUT_STAGES["E1"], ("B0", "S1", "W1"))
        self.assertEqual(prod.ACTION_PACKAGE_INPUT_STAGES["T1"], ("B0", "S1", "W1", "E1"))
        self.assertEqual(prod.ACTION_PACKAGE_INPUT_STAGES["C1"][-1], "T1")
        self.assertEqual(prod.ACTION_PACKAGE_INPUT_STAGES["Q1"][-1], "C1")
        self.assertEqual(prod.ACTION_PACKAGE_INPUT_STAGES["P1"][-1], "Q1")
        self.assertNotIn("H1-A", prod.ACTION_PACKAGE_INPUT_STAGES)

    def test_override_and_executor_mismatch_are_zero_write(self):
        context, _ = self._advance(("B0",))
        before = context.store.latest_state()
        with self.assertRaisesRegex(prod.ProductionOrchestratorError, "PROD_WORK_INPUT_OVERRIDE"):
            prod.issue_stage_work(context, action="S1", inputs={"baseline_package": "B0"})
        self.assertEqual(context.store.latest_state(), before)
        _, order = prod.issue_stage_work(context, action="S1", inputs={})
        called = False

        def execute(*_args):
            nonlocal called
            called = True

        with self.assertRaisesRegex(
            prod.ProductionOrchestratorError, "PROD_EXECUTOR_INPUT_BINDINGS_MISMATCH"
        ):
            prod.execute_stage_work(
                context, work_order=order, actor=prod.ACTION_CONTRACT["S1"][1], executor=execute,
                input_bindings={"baseline_package": "foreign"},
            )
        self.assertFalse(called)
        self.assertEqual(context.store.latest_state(), before)
        self.assertIsNone(context.store._load_commit_intent(order))

    def test_missing_tampered_escape_and_ambiguous_fail_before_order(self):
        context, _ = self._advance(("B0",))
        completion = context.state.data["current_stage_completions"]["B0"]
        package = self.root / "B0" / "attempt-001"
        original = (package / "validation.json").read_bytes()
        (package / "validation.json").unlink()
        with self.assertRaisesRegex(prod.ProductionOrchestratorError, "PROD_DOCUMENT_STALE"):
            prod.issue_stage_work(context, action="S1", inputs={})
        self.assertIsNone(context.store.pending_work_order())
        (package / "validation.json").write_bytes(original + b" ")
        with self.assertRaisesRegex(prod.ProductionOrchestratorError, "PROD_DOCUMENT_STALE"):
            prod.issue_stage_work(context, action="S1", inputs={})
        self.assertIsNone(context.store.pending_work_order())
        (package / "validation.json").write_bytes(original)
        shadow = self.root / "workspaces" / "B0-attempt-001" / "package"
        shutil.copytree(package, shadow)
        with self.assertRaisesRegex(prod.ProductionOrchestratorError, "PROD_DOCUMENT_ROOT_AMBIGUOUS"):
            prod.issue_stage_work(context, action="S1", inputs={})
        self.assertIsNone(context.store.pending_work_order())
        with self.assertRaisesRegex(Exception, "PROD_PACKAGE_PROVENANCE_INVALID|PROD_PATH"):
            context.store.resolve_completion_package_root(
                {**completion, "stage": "S1", "path": "../stage-completion.json"},
                expected_stage="B0",
            )

    def test_flat_legacy_root_succeeds(self):
        context = self.fixture._context()
        root = self.root / "B0"
        root.mkdir(exist_ok=True)
        validation = {"stage": "B0", "verdict": "ready"}
        validation_path = root / "validation.json"
        validation_path.write_text(rt.canonical_json(validation), encoding="utf-8")
        manifest = {"stage": "B0", "verdict": "ready"}
        manifest_path = root / "package-manifest.json"
        manifest_path.write_text(rt.canonical_json(manifest), encoding="utf-8")
        completion = {
            "stage": "B0", "status": "ready",
            "manifest": {"path": "B0/package-manifest.json", "sha256": rt.sha256_file(manifest_path)},
            "validation": {"path": "B0/validation.json", "sha256": rt.sha256_file(validation_path)},
        }
        completion_path = root / "stage-completion.json"
        completion_path.write_text(rt.canonical_json(completion), encoding="utf-8")
        reference = {"stage": "B0", "path": "B0/stage-completion.json", "sha256": rt.sha256_file(completion_path)}
        self.assertEqual(
            context.store.resolve_physical_path(
                context.store.resolve_completion_package_root(reference, expected_stage="B0")
            ),
            root.resolve(),
        )

    def test_stage_return_reissues_p1_with_corrected_roots(self):
        context, _ = self._advance(("B0", "S1", "W1", "E1", "T1", "C1", "Q1"))
        _, pending = prod.issue_stage_work(context, action="P1", inputs={})
        request = rt.seal_document(
            rt.route_return(
                run_id="RUN-PROD-1", return_id="RET-P1-PACKAGE-REISSUE",
                origin_kind="stage", origin_stage="P1", issue_kind="package_assembly",
                problem="P1 package input roots require current sealed bindings.",
                evidence_ids=["P1_INPUT_ROOT_BINDING"],
                violated_contract="P1 sealed input binding",
                required_revision="Reissue P1 with gate-authoritative roots.",
                author_decision=None, has_current_author_decision=False,
                has_current_conception_completion=False,
            ),
            "returns/RET-P1-PACKAGE-REISSUE/return-request.json",
        )
        _, returned, _, replacement = prod.apply_stage_return(
            context, work_order=pending, request=request,
            actor=prod.ACTION_CONTRACT["P1"][1], inputs={},
        )
        self.assertEqual("P1", replacement.data["action"])
        sealed = prod._sealed_executor_inputs(replacement)
        self.assertEqual(set(sealed), set(prod.PACKAGE_INPUT_FIELDS.values()))
        for stage, field in prod.PACKAGE_INPUT_FIELDS.items():
            self.assertEqual(
                returned.store.resolve_physical_path(sealed[field]),
                (self.root / stage / f"attempt-{('B0','S1','W1','E1','T1','C1','Q1').index(stage)+1:03d}").resolve(),
            )
        rejected = self.root / "orchestration" / "work-orders" / f"{pending.data['work_id']}.rejected.json"
        self.assertTrue(rejected.is_file())
        self.assertEqual(replacement.reference, returned.store.pending_work_order().reference)
