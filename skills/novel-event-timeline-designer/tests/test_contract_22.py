from __future__ import annotations

import copy
import hashlib
import importlib
import json
import unittest

contract_22 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_22"
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def occurrence(event_id: str, step_id: str, ordinal: int = 1) -> dict[str, object]:
    return {
        "occurrence_id": "CSO-" + digest([event_id, step_id, ordinal])[:24],
        "step_id": step_id,
        "ordinal": ordinal,
    }


def base_case() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    storyline = {
        "storylines": [
            {
                "id": "SL-A",
                "start_state": "before",
                "state_changes": [],
                "end_state": "after",
            }
        ],
        "connections": [],
        "story_obligation_register": [],
        "temporal_architecture": {
            "milestones": [
                {
                    "id": "MS-1",
                    "order": 1,
                    "phase_id": "PH-1",
                    "storyline_ids": ["SL-A"],
                    "state_refs": [{"storyline_id": "SL-A", "state_index": 1}],
                    "connection_ids": [],
                }
            ]
        },
    }
    option = {
        "support_option_id": "OPT-A",
        "capability_demand_id": "DEM-A",
        "capability_descriptor": {"support_kind": "static_context_host"},
    }
    environment = {
        "story_transition_universe_digest": {"x": 1},
        "milestone_universe_digest": {"x": 2},
        "connection_universe_digest": {"x": 3},
        "obligation_universe_digest": {"x": 4},
        "initial_anchor_support": [
            {
                "storyline_id": "SL-A",
                "state_index": 0,
                "support_options": [option],
            }
        ],
        "initial_anchor_option_realization_ledger": [
            {
                "id": "IAR-A",
                "support_option_id": "OPT-A",
                "capability_demand_id": "DEM-A",
                "storyline_id": "SL-A",
                "state_index": 0,
                "descriptor_sha256": digest(option["capability_descriptor"]),
                "status": "ready",
            }
        ],
        "story_transition_support": [
            {
                "id": "TRS-A",
                "storyline_id": "SL-A",
                "from_state_index": 0,
                "to_state_index": 1,
            }
        ],
        "connection_path_readiness": [],
        "capability_occurrence_requirements": [],
        "capability_fact_registry": [],
        "capability_step_registry": [
            {
                "id": "CSTEP-A",
                "environment_id": "ENV-A",
                "affordance_id": "AFF-A",
                "action": "perform A",
                "requires_fact_ids": [],
                "produces_fact_ids": [],
            }
        ],
        "actor_authority_bindings": [],
    }
    event_id = "EV-A"
    event = {
        "id": event_id,
        "kind": "story_transition",
        "milestone_id": "MS-1",
        "world_time_slot": "[WT:000001]",
        "storyline_ids": ["SL-A"],
        "changed_subject": {
            "subject_id": "SL-A",
            "before": "before",
            "after": "after",
            "subject_kind": "storyline_state",
        },
        "environment_id": "ENV-A",
        "affordance_ids": ["AFF-A"],
        "initiating_action": "perform A",
        "e1_capability_step_ids": ["CSTEP-A"],
        "capability_step_occurrences": [occurrence(event_id, "CSTEP-A")],
        "requires_capability_fact_ids": [],
        "produces_capability_fact_ids": [],
        "requires_token_instance_ids": [],
        "produces_token_instance_ids": [],
        "requires_proposition_ids": ["PROP-INITIAL"],
        "produces_proposition_ids": ["PROP-AFTER"],
        "discloses_proposition_ids": [],
        "initial_anchor_refs": [],
        "predecessor_event_ids": [],
        "preconditions": ["initial state is present"],
        "direct_result": "the formal state changes",
        "next_pressure": "the result must be absorbed",
        "source_ids": ["SL-A"],
        "atomicity_reason": "one formal subject changes",
    }
    propositions = [
        {
            "id": "PROP-INITIAL",
            "statement": "the initial state exists",
            "source_ids": ["SL-A"],
            "audience": None,
            "initially_true": True,
            "terminality": "ordinary",
            "initial_anchor_refs": [{"storyline_id": "SL-A", "state_index": 0}],
            "producer_event_ids": [],
        },
        {
            "id": "PROP-AFTER",
            "statement": "the target state exists",
            "source_ids": ["SL-A"],
            "audience": None,
            "initially_true": False,
            "terminality": "unique_terminal",
            "initial_anchor_refs": [],
            "producer_event_ids": [event_id],
        },
    ]
    plan = {
        "narrative_timing_constraints": [
            {
                "id": "TIME-A",
                "event_ids": [event_id],
                "constraint": "the event occupies the only world-time slot",
                "story_effect": "the state change is directly observable",
            }
        ],
        "initial_condition_registry": [
            {
                "storyline_id": "SL-A",
                "state_index": 0,
                "state": "before",
                "atomic_proposition_ids": ["PROP-INITIAL"],
                "atomic_components": [
                    {
                        "component_id": "ICOMP-A",
                        "proposition_ids": ["PROP-INITIAL"],
                        "classification": "static_context",
                        "planned_event_ids": [],
                        "e1_support_option_ids": ["OPT-A"],
                    }
                ],
                "classification_summary": "static_context",
                "classification_source_ids": ["SL-A"],
                "semantic_review_claim_id": "CLAIM-INITIAL-A",
                "planned_event_ids": [],
            }
        ],
        "initial_anchor_option_selection_ledger": [
            {
                "storyline_id": "SL-A",
                "state_index": 0,
                "component_id": "ICOMP-A",
                "support_option_id": "OPT-A",
                "capability_demand_id": "DEM-A",
                "realization_record_id": "IAR-A",
            }
        ],
        "planned_event_registry": [event],
        "process_state_subject_registry": [],
        "planned_proposition_registry": propositions,
        "planned_causal_edges": [],
        "transition_event_cover": [
            {
                "storyline_id": "SL-A",
                "from_state_index": 0,
                "to_state_index": 1,
                "event_id": event_id,
                "transition_support_id": "TRS-A",
            }
        ],
        "milestone_event_buckets": [
            {
                "milestone_id": "MS-1",
                "order": 1,
                "phase_id": "PH-1",
                "storyline_ids": ["SL-A"],
                "state_refs": [{"storyline_id": "SL-A", "state_index": 1}],
                "connection_ids": [],
                "event_ids": [event_id],
            }
        ],
        "connection_event_paths": [],
        "obligation_event_plan": [],
        "capability_occurrence_event_cover": [],
        "authority_token_instance_ledger": [],
    }
    return storyline, environment, plan


class Contract22Tests(unittest.TestCase):
    def test_complete_generic_plan_passes(self) -> None:
        storyline, environment, plan = base_case()
        contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_transition_omission_and_duplication_fail(self) -> None:
        storyline, environment, plan = base_case()
        plan["transition_event_cover"] = []
        with self.assertRaisesRegex(contract_22.Contract22Error, "T1_TRANSITION_EVENT_COVER_MISMATCH"):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_unanchored_intermediate_transition_does_not_invent_milestone(self) -> None:
        storyline, environment, plan = base_case()
        storyline["storylines"][0]["state_changes"] = ["middle"]
        terminal_ref = {"storyline_id": "SL-A", "state_index": 2, "state": "after"}
        storyline["temporal_architecture"]["milestones"][0]["state_refs"] = [terminal_ref]
        plan["milestone_event_buckets"][0]["state_refs"] = [terminal_ref]
        environment["story_transition_support"] = [
            {
                "id": "TRS-A-0",
                "storyline_id": "SL-A",
                "from_state_index": 0,
                "to_state_index": 1,
            },
            {
                "id": "TRS-A-1",
                "storyline_id": "SL-A",
                "from_state_index": 1,
                "to_state_index": 2,
            },
        ]
        plan["planned_event_registry"][0]["changed_subject"]["after"] = "middle"
        plan["transition_event_cover"] = [
            {
                "storyline_id": "SL-A",
                "from_state_index": 0,
                "to_state_index": 1,
                "event_id": "EV-A",
                "transition_support_id": "TRS-A-0",
            }
        ]
        # The focused check is milestone placement: state 1 is intentionally
        # absent from S1 milestones and therefore has no invented first-arrival.
        contract_22.validate_milestone_buckets(
            plan,
            storyline,
            {"EV-A": plan["planned_event_registry"][0]},
            environment,
        )

    def test_declared_first_arrival_milestone_cannot_be_empty(self) -> None:
        storyline, environment, plan = base_case()
        plan["milestone_event_buckets"][0]["event_ids"] = []
        with self.assertRaisesRegex(
            contract_22.Contract22Error, "T1_MILESTONE_EMPTY_BUCKET_FORBIDDEN"
        ):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_non_root_capability_fact_requires_strict_producer_ancestor(self) -> None:
        storyline, environment, plan = base_case()
        environment["capability_fact_registry"] = [
            {
                "id": "CF-NEEDS-PRODUCER",
                "root_policy": "producer_required",
            }
        ]
        environment["capability_step_registry"][0]["requires_fact_ids"] = [
            "CF-NEEDS-PRODUCER"
        ]
        plan["planned_event_registry"][0]["requires_capability_fact_ids"] = [
            "CF-NEEDS-PRODUCER"
        ]
        with self.assertRaisesRegex(
            contract_22.Contract22Error, "T1_CAPABILITY_FACT_ANCESTRY_MISSING"
        ):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_distinct_exclusive_step_occurrences_may_share_one_atomic_event(self) -> None:
        _storyline, environment, plan = base_case()
        event = plan["planned_event_registry"][0]
        environment["capability_step_registry"].append(
            {
                "id": "CSTEP-B",
                "environment_id": "ENV-A",
                "affordance_id": "AFF-A",
                "action": "perform A",
                "requires_fact_ids": [],
                "produces_fact_ids": [],
            }
        )
        event["e1_capability_step_ids"].append("CSTEP-B")
        event["capability_step_occurrences"].append(occurrence("EV-A", "CSTEP-B", 2))
        environment["capability_occurrence_requirements"] = [
            {
                "id": "COR-A",
                "step_id": "CSTEP-A",
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-A",
                "share_policy": "exclusive",
                "allowed_shared_requirement_ids": [],
            },
            {
                "id": "COR-B",
                "step_id": "CSTEP-B",
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-B",
                "share_policy": "exclusive",
                "allowed_shared_requirement_ids": [],
            },
        ]
        plan["capability_occurrence_event_cover"] = [
            {
                "requirement_id": "COR-A",
                "occurrence_ids": [event["capability_step_occurrences"][0]["occurrence_id"]],
            },
            {
                "requirement_id": "COR-B",
                "occurrence_ids": [event["capability_step_occurrences"][1]["occurrence_id"]],
            },
        ]
        contract_22.validate_occurrence_cover(
            plan, environment, {event["id"]: event}
        )
        storyline, environment, plan = base_case()
        plan["transition_event_cover"].append(copy.deepcopy(plan["transition_event_cover"][0]))
        with self.assertRaisesRegex(contract_22.Contract22Error, "T1_TRANSITION_EVENT_COVER_DUPLICATE"):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_distinct_group_is_event_injective_for_every_share_policy(self) -> None:
        for policy in ("shareable", "allow_list"):
            with self.subTest(policy=policy):
                _storyline, environment, plan = base_case()
                event = plan["planned_event_registry"][0]
                second = occurrence(event["id"], "CSTEP-A", 2)
                event["capability_step_occurrences"].append(second)
                environment["capability_occurrence_requirements"] = [
                    {
                        "id": "COR-A",
                        "step_id": "CSTEP-A",
                        "minimum_occurrences": 1,
                        "maximum_occurrences": 1,
                        "distinct_group_id": "GROUP-SAME",
                        "share_policy": policy,
                        "allowed_shared_requirement_ids": ["COR-B"] if policy == "allow_list" else [],
                    },
                    {
                        "id": "COR-B",
                        "step_id": "CSTEP-A",
                        "minimum_occurrences": 1,
                        "maximum_occurrences": 1,
                        "distinct_group_id": "GROUP-SAME",
                        "share_policy": policy,
                        "allowed_shared_requirement_ids": ["COR-A"] if policy == "allow_list" else [],
                    },
                ]
                plan["capability_occurrence_event_cover"] = [
                    {
                        "requirement_id": "COR-A",
                        "occurrence_ids": [event["capability_step_occurrences"][0]["occurrence_id"]],
                    },
                    {"requirement_id": "COR-B", "occurrence_ids": [second["occurrence_id"]]},
                ]
                with self.assertRaisesRegex(
                    contract_22.Contract22Error,
                    "T1_CAPABILITY_OCCURRENCE_DISTINCT_VIOLATION",
                ):
                    contract_22.validate_occurrence_cover(
                        plan, environment, {event["id"]: event}
                    )

    def test_occurrence_sharing_is_independent_of_distinct_group_injectivity(self) -> None:
        _storyline, environment, plan = base_case()
        event = plan["planned_event_registry"][0]
        occurrence_id = event["capability_step_occurrences"][0]["occurrence_id"]
        environment["capability_occurrence_requirements"] = [
            {
                "id": "COR-A",
                "step_id": "CSTEP-A",
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-A",
                "share_policy": "shareable",
                "allowed_shared_requirement_ids": [],
            },
            {
                "id": "COR-B",
                "step_id": "CSTEP-A",
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-B",
                "share_policy": "shareable",
                "allowed_shared_requirement_ids": [],
            },
        ]
        plan["capability_occurrence_event_cover"] = [
            {"requirement_id": "COR-A", "occurrence_ids": [occurrence_id]},
            {"requirement_id": "COR-B", "occurrence_ids": [occurrence_id]},
        ]
        contract_22.validate_occurrence_cover(
            plan, environment, {event["id"]: event}
        )

        second_event = copy.deepcopy(event)
        second_event["id"] = "EV-B"
        second_event["capability_step_occurrences"] = [occurrence("EV-B", "CSTEP-A", 1)]
        environment["capability_occurrence_requirements"][1]["distinct_group_id"] = "GROUP-A"
        plan["capability_occurrence_event_cover"][1]["occurrence_ids"] = [
            second_event["capability_step_occurrences"][0]["occurrence_id"]
        ]
        contract_22.validate_occurrence_cover(
            plan,
            environment,
            {event["id"]: event, second_event["id"]: second_event},
        )

    def test_obligation_owned_occurrence_stays_on_its_exact_support(self) -> None:
        _storyline, environment, plan = base_case()
        event = plan["planned_event_registry"][0]
        occurrence_id = event["capability_step_occurrences"][0]["occurrence_id"]
        environment["capability_occurrence_requirements"] = [
            {
                "id": "COR-OBL-A",
                "step_id": "CSTEP-A",
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-OBL-A",
                "share_policy": "exclusive",
                "allowed_shared_requirement_ids": [],
            }
        ]
        environment["obligation_occurrence_bindings"] = [
            {
                "id": "OOB-A",
                "obligation_id": "SOB-A",
                "occurrence_requirement_id": "COR-OBL-A",
                "step_id": "CSTEP-A",
                "support_id": "TRS-A",
            }
        ]
        plan["obligation_event_plan"] = [{"obligation_id": "SOB-A"}]
        plan["capability_occurrence_event_cover"] = [
            {"requirement_id": "COR-OBL-A", "occurrence_ids": [occurrence_id]}
        ]
        events = {event["id"]: event}
        contract_22.validate_occurrence_cover(plan, environment, events)

        mutant = copy.deepcopy(environment)
        mutant["obligation_occurrence_bindings"][0]["support_id"] = "TRS-FOREIGN"
        with self.assertRaisesRegex(
            contract_22.Contract22Error,
            "T1_OBLIGATION_OCCURRENCE_BINDING_MISMATCH",
        ):
            contract_22.validate_occurrence_cover(plan, mutant, events)

    def test_static_initial_cannot_have_event_or_producer(self) -> None:
        storyline, environment, plan = base_case()
        plan["initial_condition_registry"][0]["atomic_components"][0]["planned_event_ids"] = ["EV-A"]
        plan["initial_condition_registry"][0]["planned_event_ids"] = ["EV-A"]
        with self.assertRaisesRegex(contract_22.Contract22Error, "T1_STATIC_INITIAL_EVENT_FORBIDDEN"):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_cross_anchor_and_kind_mismatch_fail(self) -> None:
        storyline, environment, plan = base_case()
        environment["initial_anchor_support"][0]["support_options"][0]["capability_descriptor"]["support_kind"] = "process_host"
        with self.assertRaisesRegex(contract_22.Contract22Error, "T1_INITIAL_OPTION_INCOMPATIBLE"):
            contract_22.validate_p2_plan(plan, storyline, environment, digest)

    def test_p3_full_mapping_rejects_any_drift(self) -> None:
        _storyline, _environment, plan = base_case()
        event = plan["planned_event_registry"][0]
        subject = event["changed_subject"]
        canonical_event = {
            **copy.deepcopy(event),
            "event_kind": event["kind"],
            "world_time": event["world_time_slot"],
            "subject_id": subject["subject_id"],
            "subject_kind": subject["subject_kind"],
            "before_state": {subject["subject_id"]: subject["before"]},
            "after_state": {subject["subject_id"]: subject["after"]},
        }
        canonical_event.pop("kind")
        canonical_event.pop("world_time_slot")
        canonical_event.pop("changed_subject")
        model = {
            **copy.deepcopy(plan),
            "major_events": [canonical_event],
            "proposition_registry": copy.deepcopy(plan["planned_proposition_registry"]),
            "causal_edges": [],
        }
        contract_22.validate_p3_exact(plan, model)
        event_map = {
            "kind": "event_kind",
            "milestone_id": "milestone_id",
            "world_time_slot": "world_time",
            "storyline_ids": "storyline_ids",
            "environment_id": "environment_id",
            "affordance_ids": "affordance_ids",
            "initiating_action": "initiating_action",
            "e1_capability_step_ids": "e1_capability_step_ids",
            "capability_step_occurrences": "capability_step_occurrences",
            "requires_capability_fact_ids": "requires_capability_fact_ids",
            "produces_capability_fact_ids": "produces_capability_fact_ids",
            "requires_token_instance_ids": "requires_token_instance_ids",
            "produces_token_instance_ids": "produces_token_instance_ids",
            "requires_proposition_ids": "requires_proposition_ids",
            "produces_proposition_ids": "produces_proposition_ids",
            "discloses_proposition_ids": "discloses_proposition_ids",
            "initial_anchor_refs": "initial_anchor_refs",
            "predecessor_event_ids": "predecessor_event_ids",
            "preconditions": "preconditions",
            "direct_result": "direct_result",
            "next_pressure": "next_pressure",
            "source_ids": "source_ids",
            "atomicity_reason": "atomicity_reason",
        }
        for source_field, target_field in event_map.items():
            mutant = copy.deepcopy(model)
            value = mutant["major_events"][0][target_field]
            if isinstance(value, str):
                mutant["major_events"][0][target_field] = value + "-drift"
            else:
                mutant["major_events"][0][target_field] = [*value, {"drift": True}]
            with self.subTest(field=source_field), self.assertRaisesRegex(
                contract_22.Contract22Error, "T1_P3_EVENT_PROJECTION_MISMATCH"
            ):
                contract_22.validate_p3_exact(plan, mutant)
        for field in ("subject_id", "subject_kind", "before_state", "after_state"):
            mutant = copy.deepcopy(model)
            mutant["major_events"][0][field] = "drift" if field.endswith("id") or field.endswith("kind") else {"drift": "state"}
            with self.subTest(field=field), self.assertRaisesRegex(
                contract_22.Contract22Error, "T1_P3_EVENT_SUBJECT_MISMATCH"
            ):
                contract_22.validate_p3_exact(plan, mutant)

    def test_digest_is_recomputed_from_e1_roots(self) -> None:
        _storyline, environment, _plan = base_case()
        expected = contract_22.expected_e1_digests(
            environment,
            source_path="sources/E1/environment-system.json",
            source_sha256="a" * 64,
            canonical_sha256=digest,
        )
        contract_22.validate_p1_digests(
            expected,
            environment,
            source_path="sources/E1/environment-system.json",
            source_sha256="a" * 64,
            canonical_sha256=digest,
        )
        expected["e1_capability_graph_digest"]["canonical_items_sha256"] = "0" * 64
        with self.assertRaisesRegex(contract_22.Contract22Error, "T1_E1_DIGEST_MISMATCH"):
            contract_22.validate_p1_digests(
                expected,
                environment,
                source_path="sources/E1/environment-system.json",
                source_sha256="a" * 64,
                canonical_sha256=digest,
            )

    @staticmethod
    def _token_case() -> tuple[dict[str, object], dict[str, object]]:
        producer_step = {
            "id": "CSTEP-ISSUE",
            "environment_id": "ENV-GOV",
            "affordance_id": "AFF-ISSUE",
            "action": "issue token",
            "requires_fact_ids": [],
            "produces_fact_ids": ["CF-TOKEN"],
        }
        consumer_step = {
            "id": "CSTEP-USE",
            "environment_id": "ENV-OPS",
            "affordance_id": "AFF-USE",
            "action": "use token",
            "requires_fact_ids": ["CF-TOKEN"],
            "produces_fact_ids": [],
        }
        fact = {
            "id": "CF-TOKEN",
            "kind": "authority_token",
            "token_kind": "execution_permit",
            "root_policy": "producer_required",
            "producer_step_ids": ["CSTEP-ISSUE"],
            "consumer_step_ids": ["CSTEP-USE"],
            "consumption_policy": "single_use",
            "issuer_scope": {
                "action_bindings": [
                    {"environment_id": "ENV-GOV", "affordance_id": "AFF-ISSUE", "action": "issue token"}
                ]
            },
            "consumer_scope": {
                "action_bindings": [
                    {"environment_id": "ENV-OPS", "affordance_id": "AFF-USE", "action": "use token"}
                ]
            },
        }
        events = {}
        instances = []
        for ordinal in (1, 2):
            producer_id = f"EV-ISSUE-{ordinal}"
            consumer_id = f"EV-USE-{ordinal}"
            producer_occurrence = occurrence(producer_id, "CSTEP-ISSUE")
            consumer_occurrence = occurrence(consumer_id, "CSTEP-USE")
            instance_id = "ATI-" + digest(["CF-TOKEN", producer_occurrence["occurrence_id"]])[:24]
            events[producer_id] = {
                "capability_step_occurrences": [producer_occurrence],
                "requires_capability_fact_ids": [],
                "produces_capability_fact_ids": ["CF-TOKEN"],
                "requires_token_instance_ids": [],
                "produces_token_instance_ids": [instance_id],
            }
            events[consumer_id] = {
                "capability_step_occurrences": [consumer_occurrence],
                "requires_capability_fact_ids": ["CF-TOKEN"],
                "produces_capability_fact_ids": [],
                "requires_token_instance_ids": [instance_id],
                "produces_token_instance_ids": [],
            }
            origin = {
                "kind": "t1_produced",
                "producer_event_id": producer_id,
                "producer_step_id": "CSTEP-ISSUE",
                "producer_occurrence_id": producer_occurrence["occurrence_id"],
            }
            consumers = [
                {
                    "event_id": consumer_id,
                    "step_id": "CSTEP-USE",
                    "occurrence_id": consumer_occurrence["occurrence_id"],
                }
            ]
            instances.append(
                {
                    "token_instance_id": instance_id,
                    "token_fact_id": "CF-TOKEN",
                    "token_kind": "execution_permit",
                    "consumption_policy": "single_use",
                    "origin": origin,
                    "consumer_occurrences": consumers,
                    "semantic_review_claim_id": "T1TOK-" + digest(["CF-TOKEN", origin, consumers])[:24],
                }
            )
        environment = {
            "capability_fact_registry": [fact],
            "capability_step_registry": [producer_step, consumer_step],
        }
        return {"authority_token_instance_ledger": instances}, {"environment": environment, "events": events}

    def test_two_single_use_instances_of_same_fact_pass(self) -> None:
        plan, values = self._token_case()
        contract_22.validate_authority_token_instances(
            plan, values["environment"], values["events"], digest
        )

    def test_token_instance_core_mutants_fail(self) -> None:
        mutations = []
        plan, values = self._token_case()
        values["environment"]["capability_fact_registry"][0]["producer_step_ids"] = []
        mutations.append((plan, values, "T1_TOKEN_INSTANCE_PRODUCER_MISMATCH"))

        plan, values = self._token_case()
        values["events"]["EV-USE-1"]["requires_capability_fact_ids"] = []
        mutations.append((plan, values, "T1_TOKEN_INSTANCE_CONSUMER_MISMATCH"))

        plan, values = self._token_case()
        duplicate = copy.deepcopy(plan["authority_token_instance_ledger"][0])
        duplicate["token_instance_id"] = "ATI-" + "f" * 24
        plan["authority_token_instance_ledger"].append(duplicate)
        mutations.append((plan, values, "T1_TOKEN_INSTANCE_PRODUCER_MISMATCH"))

        plan, values = self._token_case()
        values["environment"]["capability_fact_registry"][0]["consumer_scope"]["action_bindings"][0]["action"] = "foreign"
        mutations.append((plan, values, "T1_TOKEN_INSTANCE_CONSUMER_MISMATCH"))

        plan, values = self._token_case()
        plan["authority_token_instance_ledger"][0]["consumer_occurrences"].append(
            copy.deepcopy(plan["authority_token_instance_ledger"][1]["consumer_occurrences"][0])
        )
        token = plan["authority_token_instance_ledger"][0]
        token["semantic_review_claim_id"] = "T1TOK-" + digest(
            [token["token_fact_id"], token["origin"], token["consumer_occurrences"]]
        )[:24]
        mutations.append((plan, values, "T1_TOKEN_INSTANCE_SINGLE_USE_VIOLATION"))

        for plan, values, code in mutations:
            with self.subTest(code=code), self.assertRaisesRegex(contract_22.Contract22Error, code):
                contract_22.validate_authority_token_instances(
                    plan, values["environment"], values["events"], digest
                )

    @staticmethod
    def _sealed_initial_token_case() -> tuple[dict[str, object], dict[str, object], object]:
        source_value = {"authority": "available"}
        source_artifact = {
            "stage": "W1",
            "path": "sources/W1/world-model.json",
            "sha256": "a" * 64,
        }
        source_pointer = "/authority_flows/0"
        value_sha256 = digest(source_value)
        fact = {
            "id": "CF-ROOT-TOKEN",
            "kind": "authority_token",
            "token_kind": "standing_authority",
            "root_policy": "root_allowed",
            "producer_step_ids": [],
            "consumer_step_ids": ["CSTEP-ROOT-USE"],
            "consumption_policy": "single_use",
            "source_anchor": {
                "source_kind": "w1_system_output",
                "source_artifact": source_artifact,
                "source_pointer": source_pointer,
                "value_sha256": value_sha256,
                "system_or_flow_id": "AUTH-FLOW",
                "output_index": 0,
            },
            "issuer_scope": {"action_bindings": []},
            "consumer_scope": {
                "action_bindings": [
                    {
                        "environment_id": "ENV-ROOT",
                        "affordance_id": "AFF-ROOT",
                        "action": "use standing authority",
                    }
                ]
            },
        }
        step = {
            "id": "CSTEP-ROOT-USE",
            "environment_id": "ENV-ROOT",
            "affordance_id": "AFF-ROOT",
            "action": "use standing authority",
        }
        event_id = "EV-ROOT-USE"
        use_occurrence = occurrence(event_id, step["id"])
        instance_id = "ATI-" + digest(
            [fact["id"], source_artifact["sha256"], source_pointer, value_sha256]
        )[:24]
        event = {
            "capability_step_occurrences": [use_occurrence],
            "requires_capability_fact_ids": [fact["id"]],
            "produces_capability_fact_ids": [],
            "requires_token_instance_ids": [instance_id],
            "produces_token_instance_ids": [],
        }
        origin = {
            "kind": "upstream_sealed_initial",
            "source_artifact": source_artifact,
            "source_pointer": source_pointer,
            "value_sha256": value_sha256,
        }
        consumers = [
            {
                "event_id": event_id,
                "step_id": step["id"],
                "occurrence_id": use_occurrence["occurrence_id"],
            }
        ]
        plan = {
            "authority_token_instance_ledger": [
                {
                    "token_instance_id": instance_id,
                    "token_fact_id": fact["id"],
                    "token_kind": fact["token_kind"],
                    "consumption_policy": fact["consumption_policy"],
                    "origin": origin,
                    "consumer_occurrences": consumers,
                    "semantic_review_claim_id": "T1TOK-"
                    + digest([fact["id"], origin, consumers])[:24],
                }
            ]
        }
        environment = {
            "capability_fact_registry": [fact],
            "capability_step_registry": [step],
        }
        return plan, {"environment": environment, "events": {event_id: event}}, source_value

    def test_sealed_initial_authority_instance_and_source_mutants(self) -> None:
        plan, values, source_value = self._sealed_initial_token_case()
        contract_22.validate_authority_token_instances(
            plan,
            values["environment"],
            values["events"],
            digest,
            sealed_value=lambda _origin: source_value,
        )
        drift = copy.deepcopy(plan)
        drift["authority_token_instance_ledger"][0]["origin"]["source_pointer"] = "/other"
        with self.assertRaisesRegex(
            contract_22.Contract22Error, "T1_TOKEN_INSTANCE_INITIAL_ORIGIN_INVALID"
        ):
            contract_22.validate_authority_token_instances(
                drift, values["environment"], values["events"], digest,
                sealed_value=lambda _origin: source_value,
            )
        with self.assertRaisesRegex(
            contract_22.Contract22Error, "T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE"
        ):
            contract_22.validate_authority_token_instances(
                plan, values["environment"], values["events"], digest,
                sealed_value=lambda _origin: {"authority": "changed"},
            )


if __name__ == "__main__":
    unittest.main()
