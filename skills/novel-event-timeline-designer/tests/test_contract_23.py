from __future__ import annotations

import copy
import importlib
import unittest

v22_test = importlib.import_module(
    "skills.novel-event-timeline-designer.tests.test_contract_22"
)
contract_23 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_23"
)
runtime = importlib.import_module("harnesses.novel-conception-autonomous.runtime")


def span_case():
    storyline, environment, plan = v22_test.base_case()
    disclosure = copy.deepcopy(plan["planned_event_registry"][0])
    disclosure["id"] = "EV-DISCLOSE"
    disclosure["kind"] = "process"
    disclosure["world_time_slot"] = "[WT:000001]"
    disclosure["changed_subject"] = {
        "subject_id": "PSS-DISCLOSE",
        "before": "sealed",
        "after": "disclosed",
        "subject_kind": "t1_process_record",
    }
    disclosure["e1_capability_step_ids"] = ["CSTEP-D"]
    disclosure["capability_step_occurrences"] = [
        v22_test.occurrence("EV-DISCLOSE", "CSTEP-D")
    ]
    disclosure["requires_proposition_ids"] = ["PROP-INITIAL"]
    disclosure["produces_proposition_ids"] = ["PROP-DISCLOSED"]
    disclosure["discloses_proposition_ids"] = ["PROP-DISCLOSED"]
    disclosure["predecessor_event_ids"] = []
    disclosure["direct_result"] = "the sealed fact becomes observable"
    disclosure["next_pressure"] = "the operator must commit the state"
    final = plan["planned_event_registry"][0]
    final["id"] = "EV-COMMIT"
    final["world_time_slot"] = "[WT:000002]"
    final["predecessor_event_ids"] = ["EV-DISCLOSE"]
    final["requires_proposition_ids"] = ["PROP-DISCLOSED"]
    final["produces_proposition_ids"] = ["PROP-AFTER"]
    final["capability_step_occurrences"] = [
        v22_test.occurrence("EV-COMMIT", "CSTEP-A")
    ]
    environment["capability_step_registry"].append(
        {
            "id": "CSTEP-D",
            "environment_id": "ENV-A",
            "affordance_id": "AFF-A",
            "action": "perform A",
            "requires_fact_ids": [],
            "produces_fact_ids": [],
        }
    )
    plan["planned_event_registry"] = [disclosure, final]
    plan["process_state_subject_registry"] = [
        {
            "id": "PSS-DISCLOSE",
            "subject_kind": "t1_process_record",
            "owner_stage": "T1",
            "source_object_id": "SOB-DISCLOSE",
            "source_state_vocabulary_hash": v22_test.digest(["sealed", "disclosed"]),
            "state_vocabulary": ["sealed", "disclosed"],
            "allowed_transitions": [{"from": "sealed", "to": "disclosed"}],
            "scope_constraints": ["one transition span"],
            "semantic_review_claim_id": "CLAIM-PSS-DISCLOSE",
        }
    ]
    plan["planned_proposition_registry"].append(
        {
            "id": "PROP-DISCLOSED",
            "statement": "the sealed fact has been disclosed",
            "source_ids": ["SOB-DISCLOSE"],
            "audience": "reader",
            "initially_true": False,
            "terminality": "ordinary",
            "initial_anchor_refs": [],
            "producer_event_ids": ["EV-DISCLOSE"],
        }
    )
    plan["planned_proposition_registry"][1]["producer_event_ids"] = ["EV-COMMIT"]
    plan["planned_causal_edges"] = [
        {
            "id": "CE-SPAN",
            "from_event_id": "EV-DISCLOSE",
            "to_event_id": "EV-COMMIT",
            "mechanism": (
                "[CAUSE_RESULT_SHA256:"
                + v22_test.digest(disclosure["direct_result"])
                + "][CAUSE_PRESSURE_SHA256:"
                + v22_test.digest(disclosure["next_pressure"])
                + "] disclosure compels the operator commit"
            ),
            "necessary_condition": (
                "[PRECONDITION_SHA256:"
                + v22_test.digest(final["preconditions"][0])
                + "] the operator receives the disclosed fact"
            ),
        }
    ]
    plan["transition_event_cover"][0].pop("event_id")
    plan["transition_event_cover"][0]["event_ids"] = ["EV-DISCLOSE", "EV-COMMIT"]
    plan["milestone_event_buckets"][0]["event_ids"] = ["EV-DISCLOSE", "EV-COMMIT"]
    plan["narrative_timing_constraints"][0]["event_ids"] = ["EV-DISCLOSE", "EV-COMMIT"]
    storyline["story_obligation_register"] = [
        {
            "id": "SOB-DISCLOSE",
            "kind": "first_disclosure",
            "antecedent_anchors": [],
            "consequent_anchor": {
                "storyline_id": "SL-A",
                "state_index": 1,
                "state": "after",
            },
            "proposition_id": "PROP-DISCLOSED",
            "audience": "reader",
        }
    ]
    plan["obligation_event_plan"] = [
        {
            "obligation_id": "SOB-DISCLOSE",
            "kind": "first_disclosure",
            "antecedent_event_ids": [],
            "consequent_event_id": "EV-DISCLOSE",
            "antecedent_proposition_ids": [],
            "consequent_proposition_id": "PROP-DISCLOSED",
            "audience": "reader",
            "timing_rule": "first in the arrival span",
            "disclosure_rule": "unique earliest disclosure",
        }
    ]
    return storyline, environment, plan


class Contract23AtomicSpanTests(unittest.TestCase):
    def test_schema_requires_nonempty_unique_event_ids(self):
        validator = runtime.ContractRuntime()
        valid = {
            "storyline_id": "SL-A", "from_state_index": 0,
            "to_state_index": 1, "event_ids": ["EV-A", "EV-B"],
            "transition_support_id": "TRS-A",
        }
        validator.validate_definition(
            valid, "event-timeline.schema.json", "transitionCover23"
        )
        for event_ids in ([], ["EV-A", "EV-A"]):
            with self.subTest(event_ids=event_ids), self.assertRaises(
                runtime.ContractValidationError
            ):
                validator.validate_definition(
                    {**valid, "event_ids": event_ids},
                    "event-timeline.schema.json", "transitionCover23",
                )

    def test_disclosure_then_operator_commit_span_passes(self):
        storyline, environment, plan = span_case()
        contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)

    def test_singleton_span_preserves_semantics(self):
        storyline, environment, plan = v22_test.base_case()
        plan["transition_event_cover"][0]["event_ids"] = [
            plan["transition_event_cover"][0].pop("event_id")
        ]
        contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)

    def test_span_requires_direct_continuous_causal_edges(self):
        storyline, environment, plan = span_case()
        plan["planned_causal_edges"] = []
        plan["planned_event_registry"][1]["predecessor_event_ids"] = []
        plan["planned_event_registry"][1]["requires_proposition_ids"] = ["PROP-INITIAL"]
        with self.assertRaisesRegex(contract_23.Contract23Error, "T1_TRANSITION_EVENT_SPAN_INVALID"):
            contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)

    def test_only_final_event_may_commit_storyline_state(self):
        storyline, environment, plan = span_case()
        plan["planned_event_registry"][0]["changed_subject"] = {
            "subject_id": "SL-A", "before": "before", "after": "premature",
            "subject_kind": "storyline_state",
        }
        plan["planned_event_registry"][0]["kind"] = "authority_transition"
        with self.assertRaisesRegex(contract_23.Contract23Error, "T1_TRANSITION_EVENT_SPAN_INVALID"):
            contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)

    def test_story_transition_must_be_last_and_unique(self):
        storyline, environment, plan = span_case()
        plan["planned_event_registry"][0]["kind"] = "story_transition"
        with self.assertRaisesRegex(contract_23.Contract23Error, "T1_TRANSITION_EVENT_SPAN_INVALID"):
            contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)

    def test_span_must_have_one_storyline_membership(self):
        storyline, environment, plan = span_case()
        plan["planned_event_registry"][0]["storyline_ids"] = ["SL-X"]
        with self.assertRaisesRegex(contract_23.Contract23Error, "T1_TRANSITION_EVENT_SPAN_INVALID"):
            contract_23.validate_p2_plan(plan, storyline, environment, v22_test.digest)


class Contract23PropositionClosureTests(unittest.TestCase):
    def test_every_planned_event_requires_a_proposition_output(self):
        storyline, environment, plan = v22_test.base_case()
        plan["planned_event_registry"][0]["produces_proposition_ids"] = []
        with self.assertRaisesRegex(
            contract_23.Contract23Error,
            "T1_PLANNED_EVENT_PROPOSITION_OUTPUT_MISSING: "
            "EV-A\\.produces_proposition_ids",
        ):
            contract_23.validate_p2_plan(
                plan, storyline, environment, v22_test.digest
            )

    def test_each_planned_event_proposition_reference_list_is_unique(self):
        mutations = (
            ("requires_proposition_ids", "PROP-INITIAL"),
            ("produces_proposition_ids", "PROP-AFTER"),
            ("discloses_proposition_ids", "PROP-AFTER"),
        )
        for field, proposition_id in mutations:
            storyline, environment, plan = v22_test.base_case()
            plan["planned_event_registry"][0][field] = [
                proposition_id,
                proposition_id,
            ]
            with self.subTest(field=field), self.assertRaisesRegex(
                contract_23.Contract23Error,
                "T1_PLANNED_EVENT_PROPOSITION_REFERENCE_DUPLICATE: "
                f"EV-A\\.{field}",
            ):
                contract_23.validate_p2_plan(
                    plan, storyline, environment, v22_test.digest
                )

    def test_contract_22_historical_semantics_remain_set_based(self):
        storyline, environment, plan = v22_test.base_case()
        plan["planned_event_registry"][0]["produces_proposition_ids"] = [
            "PROP-AFTER",
            "PROP-AFTER",
        ]
        v22_test.contract_22.validate_p2_plan(
            plan, storyline, environment, v22_test.digest
        )


class Contract23AffordanceStorylineTests(unittest.TestCase):
    def _case(self):
        storyline, environment, plan = v22_test.base_case()
        storyline["storylines"].append(
            {
                "id": "SL-X",
                "start_state": "x-before",
                "state_changes": [],
                "end_state": "x-after",
            }
        )
        storyline["event_requirements"] = [
            {"id": "EVD-A", "source_ids": ["SL-A"]},
            {"id": "EVD-X", "source_ids": ["SL-X"]},
        ]
        environment["event_affordance_catalog"] = [
            {
                "id": "AFF-A",
                "event_requirement_ids": ["EVD-A"],
            },
            {
                "id": "AFF-X",
                "event_requirement_ids": ["EVD-X"],
            },
        ]
        plan["planned_event_registry"][0]["affordance_ids"] = ["AFF-A"]
        return storyline, environment, plan

    def test_event_affordance_must_serve_a_declared_event_storyline(self):
        storyline, environment, plan = self._case()
        plan["planned_event_registry"][0]["affordance_ids"] = ["AFF-X"]
        with self.assertRaisesRegex(
            contract_23.Contract23Error,
            "T1_PLANNED_EVENT_AFFORDANCE_STORYLINE_MISMATCH",
        ):
            contract_23.validate_planned_graph(
                plan, environment, v22_test.digest, storyline
            )

    def test_dual_line_event_accepts_each_served_affordance(self):
        storyline, environment, plan = self._case()
        event = plan["planned_event_registry"][0]
        event["storyline_ids"] = ["SL-A", "SL-X"]
        event["affordance_ids"] = ["AFF-A", "AFF-X"]
        contract_23.validate_planned_graph(
            plan, environment, v22_test.digest, storyline
        )


if __name__ == "__main__":
    unittest.main()
