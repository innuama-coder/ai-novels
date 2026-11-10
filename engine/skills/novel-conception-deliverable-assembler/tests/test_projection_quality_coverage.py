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


p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)
q1_projection_tests = importlib.import_module(
    "skills.novel-conception-reviewer.tests.test_projection_object_index"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


class ProjectionAwareQualityCoverageTests(unittest.TestCase):
    def _models(self, version="2.5"):
        return {
            "S1": {"schema_version": "2.0", "items": [{"id": "SOR-A"}]},
            "T1": q1_projection_tests._model(version),
        }

    def test_projection_representatives_and_exact_generic_duplicates(self):
        models = self._models()
        self.assertEqual(models["T1"]["schema_version"], "2.5")
        models["T1"]["other"].append(copy.deepcopy(models["T1"]["other"][0]))
        targets = p1._expected_quality_objects(models)
        self.assertEqual(
            [(item["stage"], item["id"]) for item in targets],
            [("S1", "SOR-A"), ("T1", "CE-A"), ("T1", "EV-A"),
             ("T1", "EVD-A"), ("T1", "PROP-A")],
        )
        canonical = models["T1"]["major_events"][0]
        event = next(item for item in targets if item["id"] == "EV-A")
        self.assertEqual(event["value_sha256"], p1.rt.canonical_sha256(canonical))

    def test_projection_mutants_fail_closed(self):
        mutants = []
        duplicate = self._models()
        duplicate["T1"]["major_events"].append(
            copy.deepcopy(duplicate["T1"]["major_events"][0])
        )
        mutants.append(duplicate)
        missing = self._models()
        missing["T1"]["causal_edges"] = []
        mutants.append(missing)
        event = self._models()
        event["T1"]["planned_event_registry"][0]["changed_subject"]["after"] = "drift"
        mutants.append(event)
        consumes = self._models()
        consumes["T1"]["planned_event_registry"][0][
            "consumes_token_instance_ids"
        ] = ["ATI-DRIFT"]
        mutants.append(consumes)
        lifecycle = self._models()
        lifecycle["T1"]["planned_event_registry"][0]["lifecycle_effects"] = [
            {"drift": True}
        ]
        mutants.append(lifecycle)
        proposition = self._models()
        proposition["T1"]["planned_proposition_registry"][0]["statement"] = "drift"
        mutants.append(proposition)
        edge = self._models()
        edge["T1"]["planned_causal_edges"][0]["mechanism"] = "drift"
        mutants.append(edge)
        third = self._models()
        third["T1"]["other"].append(copy.deepcopy(third["T1"]["major_events"][0]))
        mutants.append(third)
        conflict = self._models()
        conflict["T1"]["other"].append({"id": "EVD-A", "value": "drift"})
        mutants.append(conflict)
        for model in mutants:
            with self.subTest(index=mutants.index(model)):
                with self.assertRaisesRegex(
                    p1.P1Error, "P1_Q1_QUALITY_COVERAGE_INVALID"
                ):
                    p1._expected_quality_objects(model)

    def test_t1_24_remains_projection_aware(self):
        models = self._models("2.4")
        targets = p1._expected_quality_objects(models)
        self.assertEqual(
            [(item["stage"], item["id"]) for item in targets],
            [("S1", "SOR-A"), ("T1", "CE-A"), ("T1", "EV-A"),
             ("T1", "EVD-A"), ("T1", "PROP-A")],
        )
        ignored_25_fields = copy.deepcopy(models)
        ignored_25_fields["T1"]["planned_event_registry"][0][
            "consumes_token_instance_ids"
        ] = ["ATI-IGNORED"]
        ignored_25_fields["T1"]["planned_event_registry"][0][
            "lifecycle_effects"
        ] = [{"legacy": "ignored"}]
        self.assertEqual(
            p1._expected_quality_objects(ignored_25_fields),
            targets,
        )
        planned = copy.deepcopy(models)
        planned["T1"]["planned_causal_edges"][0]["mechanism"] = "drift"
        with self.assertRaisesRegex(
            p1.P1Error, "P1_Q1_QUALITY_COVERAGE_INVALID"
        ):
            p1._expected_quality_objects(planned)

    def test_certificate_is_exact_and_legacy_remains_unprojected(self):
        models = self._models()
        expected = p1._expected_quality_objects(models)
        review = {
            "quality_coverage": {
                "coverage_basis": p1.QUALITY_COVERAGE_BASIS,
                "required_objects": copy.deepcopy(expected),
                "covered_objects": [
                    {**item, "handoff_check_ids": ["CHK-A"]} for item in expected
                ],
                "unresolved_blocking_quality_record_ids": [],
                "result": "complete",
            }
        }
        p1._require_q1_quality_admission(review, models)
        for field in ("required_objects", "covered_objects"):
            drift = copy.deepcopy(review)
            drift["quality_coverage"][field][0]["value_sha256"] = "0" * 64
            with self.assertRaisesRegex(p1.P1Error, "P1_Q1_QUALITY_COVERAGE_INVALID"):
                p1._require_q1_quality_admission(drift, models)
        legacy = {
            "S1": models["S1"],
            "T1": {"schema_version": "2.1", "events": [{"id": "EV-LEGACY"}]},
        }
        self.assertEqual(
            [(item["stage"], item["id"]) for item in p1._expected_quality_objects(legacy)],
            [("S1", "SOR-A"), ("T1", "EV-LEGACY")],
        )

    def test_current_run_counts_and_rev025_context_admission(self):
        root = (
            p1._REPO / "projects" / "duanxian" / "conception-runs"
            / "duanxian-conception-v2-20260811-18"
        )
        store = store_module.ProductionRunStore(root)
        state = json.loads((root / "state" / "revision-025.json").read_text(encoding="utf-8"))
        roots = {
            stage: store.resolve_completion_package_root(
                state["current_stage_completions"][stage], expected_stage=stage
            )
            for stage in p1.STAGES
        }
        models = {
            stage: json.loads(
                (roots[stage] / p1.CANONICAL_NAMES[stage]).read_text(encoding="utf-8")
            )
            for stage in ("S1", "T1")
        }
        targets = p1._expected_quality_objects(models)
        self.assertEqual(sum(item["stage"] == "S1" for item in targets), 1022)
        self.assertEqual(sum(item["stage"] == "T1" for item in targets), 1127)
        gate = store.load_document(
            {
                "path": "orchestration/input-gates/revision-025-P1/input-gate.json",
                "sha256": p1.rt.sha256_file(
                    root / "orchestration/input-gates/revision-025-P1/input-gate.json"
                ),
            }
        )
        loaded, _, _ = p1._context(
            roots, input_gate=gate, runtime=p1.rt.ContractRuntime(),
            full_validation=False,
        )
        self.assertEqual(set(loaded), set(p1.STAGES))
