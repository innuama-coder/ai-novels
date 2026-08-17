from __future__ import annotations

import copy
import importlib
import json
import unittest


p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)
store_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


def _small_models():
    occurrence = {"occurrence_id": "CSO-A", "step_id": "CSTEP-A", "ordinal": 1}
    return {
        "B0": {"run_id": "RUN", "control_registry": [{"id": "INT-A"}], "fact_dependencies": []},
        "S1": {
            "storylines": [{"id": "SL-A", "actor_slot_ids": ["SLOT-A"]}],
            "line_claim_authority": [{"claim_id": "LCA-A"}],
            "objects": [],
        },
        "W1": {"systems": [], "objects": []},
        "E1": {
            "actor_authority_bindings": [{"id": "AAB-A", "actor_slot_id": "SLOT-OPS"}],
            "ambient_context_hosts": [{"id": "ACH-A", "subject_or_actor_slot_ids": ["SLOT-OPS"]}],
            "capability_step_registry": [{"id": "CSTEP-A", "actor_slot_ids": ["SLOT-OPS"]}],
            "capability_fact_registry": [{"id": "CF-A"}],
            "objects": [],
        },
        "T1": {
            "major_events": [{
                "id": "EV-A", "participant_slot_ids": ["SLOT-A"],
                "initiator_slot_id": "SLOT-A", "counter_slot_ids": [],
                "e1_capability_step_ids": ["CSTEP-A"],
                "capability_step_occurrences": [occurrence],
                "requires_capability_fact_ids": ["CF-A"],
                "produces_capability_fact_ids": [], "predecessor_event_ids": [],
                "requires_proposition_ids": [], "produces_proposition_ids": [],
                "discloses_proposition_ids": [],
                "requires_token_instance_ids": [],
                "produces_token_instance_ids": ["ATI-A"],
            }],
            "planned_event_registry": [{
                "id": "EV-A", "capability_step_occurrences": [copy.deepcopy(occurrence)]
            }], "proposition_registry": [],
            "planned_proposition_registry": [], "causal_edges": [],
            "planned_causal_edges": [],
            "authority_token_instance_ledger": [{
                "token_instance_id": "ATI-A", "token_fact_id": "CF-A",
                "semantic_review_claim_id": "T1TOK-TECHNICAL",
                "origin": {"producer_event_id": "EV-A", "producer_occurrence_id": "CSO-A"},
                "consumer_occurrences": [],
            }],
            "information_changes": [{"id": "INFO-A", "source_occurrence_id": "CSO-A"}],
            "objects": [],
        },
        "C1": {
            "profiles": [{"id": "CHR-A"}],
            "slot_resolution": [{"slot_id": "SLOT-A", "character_id": "CHR-A"}],
            "development_freedoms": [{"id": "DEV-A", "subject_ids": ["CHR-A"], "source_ids": ["INT-A"]}],
            "objects": [],
        },
    }


class CrossModelDescriptorTests(unittest.TestCase):
    def _index(self, models):
        return p1._cross_model_index("RUN", models["B0"], models)

    def test_path_typed_domains_and_technical_ids(self):
        index = self._index(_small_models())
        refs = {(item["json_pointer"], item["target_id"]): item for item in index["references"]}
        self.assertEqual(
            {item["kind"] for item in refs[("/storylines/0/actor_slot_ids/0", "SLOT-A")]["target_occurrences"]},
            {"slot_resolution"},
        )
        self.assertEqual(
            {item["kind"] for item in refs[("/ambient_context_hosts/0/subject_or_actor_slot_ids/0", "SLOT-OPS")]["target_occurrences"]},
            {"e1_operational_slot"},
        )
        self.assertIn(("/information_changes/0/source_occurrence_id", "CSO-A"), refs)
        source_targets = refs[("/information_changes/0/source_occurrence_id", "CSO-A")]["target_occurrences"]
        self.assertEqual({item["kind"] for item in source_targets}, {"capability_occurrence"})
        self.assertIn(("/major_events/0/produces_token_instance_ids/0", "ATI-A"), refs)
        all_ids = {item["id"] for item in index["definitions"]}
        all_targets = {item["target_id"] for item in index["references"]}
        self.assertNotIn("T1TOK-TECHNICAL", all_ids | all_targets)

    def test_planned_capability_occurrence_projection_policy(self):
        index = self._index(_small_models())
        definitions = [item for item in index["definitions"] if item["id"] == "CSO-A"]
        self.assertEqual(
            {item["kind"] for item in definitions},
            {"capability_occurrence", "planned_capability_occurrence"},
        )
        missing = _small_models()
        missing["T1"]["planned_event_registry"][0]["capability_step_occurrences"] = []
        mismatch = _small_models()
        mismatch["T1"]["planned_event_registry"][0]["capability_step_occurrences"][0]["ordinal"] = 2
        shadow = _small_models()
        shadow["T1"]["planned_event_registry"][0]["capability_step_occurrences"].append(
            copy.deepcopy(shadow["T1"]["planned_event_registry"][0]["capability_step_occurrences"][0])
        )
        for model in (missing, mismatch, shadow):
            with self.subTest(model=model):
                with self.assertRaisesRegex(
                    p1.P1Error,
                    "P1_CROSS_REFERENCE_(?:PROJECTION_INVALID|AMBIGUOUS)",
                ):
                    self._index(model)

    def test_missing_wrong_stage_path_kind_and_duplicate_fail(self):
        mutants = []
        missing = _small_models(); missing["C1"]["slot_resolution"] = []; mutants.append(missing)
        wrong_stage = _small_models(); wrong_stage["C1"]["slot_resolution"] = []; wrong_stage["E1"]["actor_authority_bindings"].append({"id": "AAB-B", "actor_slot_id": "SLOT-A"}); mutants.append(wrong_stage)
        wrong_kind = _small_models(); wrong_kind["C1"]["slot_resolution"] = []; wrong_kind["C1"]["objects"].append({"id": "SLOT-A"}); mutants.append(wrong_kind)
        wrong_path = _small_models(); wrong_path["S1"]["objects"].append({"id": "USE-A", "unknown_slot_ids": ["SLOT-MISSING"]});
        # An undeclared path is intentionally technical/local and not inferred.
        self._index(wrong_path)
        duplicate = _small_models(); duplicate["C1"]["slot_resolution"].append(copy.deepcopy(duplicate["C1"]["slot_resolution"][0])); mutants.append(duplicate)
        lca_duplicate = _small_models(); lca_duplicate["S1"]["line_claim_authority"].append({"claim_id": "LCA-A"}); mutants.append(lca_duplicate)
        for model in mutants:
            with self.subTest(index=mutants.index(model)):
                with self.assertRaisesRegex(
                    p1.P1Error, "P1_CROSS_REFERENCE_(?:UNRESOLVED|AMBIGUOUS)"
                ):
                    self._index(model)

    def test_current_lca_operational_slots_and_light_context(self):
        root = p1._REPO / "projects/duanxian/conception-runs/duanxian-conception-v2-20260811-18"
        store = store_module.ProductionRunStore(root)
        state = json.loads((root / "state/revision-026.json").read_text(encoding="utf-8"))
        roots = {stage: store.resolve_completion_package_root(state["current_stage_completions"][stage], expected_stage=stage) for stage in p1.STAGES}
        models = {stage: json.loads((roots[stage] / p1.CANONICAL_NAMES[stage]).read_text(encoding="utf-8")) for stage in p1.STAGES}
        index = p1._cross_model_index(models["B0"]["run_id"], models["B0"], models)
        self.assertEqual(len(index["definitions"]), 5821)
        self.assertEqual(len(index["references"]), 6979)
        planned_occurrences = {
            item["id"]: item for item in index["definitions"]
            if item["kind"] == "planned_capability_occurrence"
        }
        canonical_occurrences = {
            item["id"]: item for item in index["definitions"]
            if item["kind"] == "capability_occurrence"
        }
        self.assertEqual(len(planned_occurrences), 242)
        self.assertEqual(len(canonical_occurrences), 242)
        self.assertEqual(set(planned_occurrences), set(canonical_occurrences))
        planned_objects = {
            occurrence["occurrence_id"]: occurrence
            for event in models["T1"]["planned_event_registry"]
            for occurrence in event["capability_step_occurrences"]
        }
        canonical_objects = {
            occurrence["occurrence_id"]: occurrence
            for event in models["T1"]["major_events"]
            for occurrence in event["capability_step_occurrences"]
        }
        self.assertEqual(planned_objects, canonical_objects)
        self.assertEqual(sum(item["kind"] == "line_claim_authority" for item in index["definitions"]), 727)
        lca = {item["claim_id"] for item in models["S1"]["line_claim_authority"]}
        self.assertTrue(lca.issubset(set(models["S1"]["authority_partition"]["autonomous_owned"])))
        c1_slots = {item["id"] for item in index["definitions"] if item["kind"] == "slot_resolution"}
        operational = {item["id"] for item in index["definitions"] if item["kind"] == "e1_operational_slot"}
        self.assertEqual(len(operational - c1_slots), 51)
        gate = store.load_document({
            "path": "orchestration/input-gates/revision-026-P1/input-gate.json",
            "sha256": p1.rt.sha256_file(root / "orchestration/input-gates/revision-026-P1/input-gate.json"),
        })
        loaded, _, _ = p1._context(roots, input_gate=gate, runtime=p1.rt.ContractRuntime(), full_validation=False)
        self.assertEqual(set(loaded), set(p1.STAGES))
