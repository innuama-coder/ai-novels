from __future__ import annotations

import copy
import importlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


runtime = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
t1 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.run_v2"
)
e1 = importlib.import_module(
    "skills.novel-environment-system-designer.scripts.run_v2"
)
e1_test = importlib.import_module(
    "skills.novel-environment-system-designer.tests.test_v2_runtime"
)
contract_22_test = importlib.import_module(
    "skills.novel-event-timeline-designer.tests.test_contract_22"
)
production = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
production_store = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


ROLES = (
    ("background", "setup"),
    ("trigger",),
    ("development",),
    ("turn_or_crisis",),
    ("result", "aftermath"),
)


def agent_event_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    baseline: dict[str, object],
    storyline: dict[str, object],
    world: dict[str, object],
    environment: dict[str, object],
) -> dict[str, object]:
    """A test Agent's authored event model; production Python never authors it."""

    lines = list(storyline["storylines"])
    requirements = list(storyline["event_requirements"])
    requirement_by_line = {
        next(source for source in item["source_ids"] if str(source).startswith("SL-")): item
        for item in requirements
    }
    affordances = list(environment["event_affordance_catalog"])
    affordance_by_line = {}
    for affordance in affordances:
        for requirement_id in affordance["event_requirement_ids"]:
            requirement = next(item for item in requirements if item["id"] == requirement_id)
            line_id = next(
                source for source in requirement["source_ids"]
                if str(source).startswith("SL-")
            )
            affordance_by_line[line_id] = affordance
    resource_ids = [item["id"] for item in world["resource_flows"]]
    authority_ids = [item["id"] for item in environment["access_and_authority"]]
    access_by_environment = {
        item["subject_id"]: item["id"]
        for item in environment["access_and_authority"]
    }

    events = []
    placements = []
    ledgers = []
    sequences = []
    coverage = []
    causal_edges = []
    timing = []
    event_by_line_role = {}
    for line_index, line in enumerate(lines):
        line_id = line["id"]
        is_main = line_id == "SL-MAIN"
        base = 100 if is_main else (line_index + 1) * 10
        event_ids = []
        states = [
            line["start_state"],
            *line["state_changes"],
            line["end_state"],
        ]
        transition_count = len(states) - 1
        if transition_count > len(ROLES):
            raise AssertionError(
                "test Agent needs more responsibility events"
            )
        transition_positions = (
            [len(ROLES) - 1]
            if transition_count == 1
            else [
                round(
                    index
                    * (len(ROLES) - 1)
                    / (transition_count - 1)
                )
                for index in range(transition_count)
            ]
        )
        transition_by_position = {
            position: index
            for index, position in enumerate(transition_positions)
        }
        non_transition_index = 0
        affordance = affordance_by_line[line_id]
        environment_id = affordance["environment_id"]
        for role_index, roles in enumerate(ROLES):
            event_id = f"EV-{line_id[3:]}-{role_index + 1:02d}"
            event_ids.append(event_id)
            event_by_line_role[(line_id, roles[0])] = event_id
            if role_index in transition_by_position:
                transition_index = transition_by_position[role_index]
                subject_id = line_id
                before = states[transition_index]
                after = states[transition_index + 1]
                kind = "state"
            elif non_transition_index % 2 == 0:
                subject_id = resource_ids[line_index % len(resource_ids)]
                before = f"{subject_id}:available"
                after = f"{subject_id}:committed"
                kind = "resource"
                non_transition_index += 1
            else:
                subject_id = authority_ids[line_index % len(authority_ids)]
                before = f"{subject_id}:withheld"
                after = f"{subject_id}:granted"
                kind = "authority"
                non_transition_index += 1
            predecessors = [] if role_index == 0 else [event_ids[-2]]
            result_proposition_id = f"PROP-{event_id[3:]}-RESULT"
            role_text = "".join(f"[RESP:{role}]" for role in roles)
            event = {
                "id": event_id,
                "responsibility": (
                    f"{role_text} Agent event for {requirement_by_line[line_id]['responsibility']}"
                ),
                "world_time": f"[WT:{base + role_index:06d}]",
                "storyline_ids": [line_id],
                "environment_id": environment_id,
                "participant_slot_ids": list(line["actor_slot_ids"]),
                "initiator_slot_id": line["actor_slot_ids"][0],
                "counter_slot_ids": [],
                "preconditions": list(affordance["prerequisites"]),
                "initiating_action": affordance["allowed_actions"][0],
                "complication": "[NO_COUNTER:systemic constraint is the opposing force]",
                "decisive_change": f"{subject_id} changes from {before} to {after}.",
                "direct_result": f"{event_id} produces a concrete downstream condition.",
                "before_state": {subject_id: before},
                "after_state": {subject_id: after},
                "next_pressure": f"{event_id} leaves the next responsibility unresolved.",
                "requires_proposition_ids": [
                    f"PROP-{item[3:]}-RESULT" for item in predecessors
                ],
                "produces_proposition_ids": [result_proposition_id],
                "discloses_proposition_ids": [],
                "information_changes": [],
                "predecessor_event_ids": predecessors,
            }
            events.append(event)
            placements.append(
                {
                    "event_id": event_id,
                    "environment_id": environment_id,
                    "affordance_ids": [affordance["id"]],
                    "fit_evidence": (
                        f"{affordance['id']} permits {event['initiating_action']} "
                        f"for {line_id} in {environment_id}."
                    ),
                }
            )
            ledgers.append(
                {
                    "id": f"ST-{event_id[3:]}",
                    "subject_id": subject_id,
                    "from_state": before,
                    "trigger_ids": [event_id],
                    "to_state": after,
                    "allowed_by_ids": [access_by_environment[environment_id]],
                    "consequence": f"[KIND:{kind}] {event['direct_result']}",
                }
            )
            if predecessors:
                causal_edges.append(
                    {
                        "id": f"CE-{predecessors[0][3:]}-{event_id[3:]}",
                        "from_event_id": predecessors[0],
                        "to_event_id": event_id,
                        "mechanism": (
                            "[CAUSE_RESULT_SHA256:"
                            f"{runtime.canonical_sha256(events[-2]['direct_result'])}]"
                            "[CAUSE_PRESSURE_SHA256:"
                            f"{runtime.canonical_sha256(events[-2]['next_pressure'])}] "
                            f"{events[-2]['next_pressure']} causes {event_id}."
                        ),
                        "necessary_condition": (
                            "[PRECONDITION_SHA256:"
                            f"{runtime.canonical_sha256(event['preconditions'][0])}] "
                            f"{event['preconditions'][0]} is required."
                        ),
                    }
                )
        sequences.append(
            {
                "id": f"SEQ-{line_id[3:]}",
                "storyline_id": line_id,
                "event_ids": event_ids,
                "entry_state": line["start_state"],
                "exit_state": line["end_state"],
                "status": "complete",
            }
        )
        coverage.append(
            {
                "id": f"COV-EVD-{line_id[3:]}",
                "source_ids": [requirement_by_line[line_id]["id"]],
                "realization_ids": event_ids,
                "status": "covered",
                "evidence": (
                    f"{requirement_by_line[line_id]['responsibility']} is realized "
                    f"from background through aftermath."
                ),
            }
        )
        timing.append(
            {
                "id": f"TIME-ROOT-{line_id[3:]}",
                "event_ids": [event_ids[0]],
                "constraint": "[REL:independent-root] This line begins from an existing condition.",
                "story_effect": "The root is explicit and can run concurrently with other roots.",
            }
        )

    event_index = {item["id"]: item for item in events}
    final_event_ids = {
        item["event_ids"][-1] for item in sequences
    }
    propositions = [
        {
            "id": f"PROP-{event['id'][3:]}-RESULT",
            "statement": event["direct_result"],
            "source_ids": list(event["storyline_ids"]),
            "audience": None,
            "initially_true": False,
            "terminality": (
                "unique_terminal"
                if event["id"] in final_event_ids
                else "ordinary"
            ),
        }
        for event in events
    ]
    proposition_index = {item["id"]: item for item in propositions}
    transition_ledgers_by_line = {
        line["id"]: [
            ledger
            for event_id in next(
                sequence["event_ids"]
                for sequence in sequences
                if sequence["storyline_id"] == line["id"]
            )
            for ledger in ledgers
            if ledger["subject_id"] == line["id"]
            and ledger["trigger_ids"] == [event_id]
        ]
        for line in lines
    }

    def anchor(line_id: str, state_index: int) -> dict[str, object]:
        line = next(item for item in lines if item["id"] == line_id)
        states = [
            line["start_state"],
            *line["state_changes"],
            line["end_state"],
        ]
        transition_ledgers = transition_ledgers_by_line[line_id]
        if state_index == 0:
            return {
                "event_id": transition_ledgers[0]["trigger_ids"][0],
                "storyline_id": line_id,
                "state_index": 0,
                "state": states[0],
                "side": "before",
            }
        return {
            "event_id": transition_ledgers[state_index - 1][
                "trigger_ids"
            ][0],
            "storyline_id": line_id,
            "state_index": state_index,
            "state": states[state_index],
            "side": "after",
        }

    connection_records = []
    for connection in storyline["connections"]:
        source_id = connection["from_storyline_id"]
        target_id = connection["to_storyline_id"]
        source_anchor = anchor(
            source_id, connection["from_state_index"]
        )
        target_anchor = anchor(
            target_id, connection["to_state_index"]
        )
        source_event = source_anchor["event_id"]
        target_event = target_anchor["event_id"]
        edge_ids = []
        timing_relation = (
            "convergence"
            if connection["relation"] == "causal"
            else "association"
        )
        if connection["relation"] == "causal":
            edge_id = f"CE-SLC-{connection['id'][4:]}"
            edge_ids = [edge_id]
            event_index[target_event][
                "predecessor_event_ids"
            ].append(source_event)
            causal_edges.append(
                {
                    "id": edge_id,
                    "from_event_id": source_event,
                    "to_event_id": target_event,
                    "mechanism": (
                        "[CAUSE_RESULT_SHA256:"
                        f"{runtime.canonical_sha256(event_index[source_event]['direct_result'])}]"
                        "[CAUSE_PRESSURE_SHA256:"
                        f"{runtime.canonical_sha256(event_index[source_event]['next_pressure'])}] "
                        f"{connection['id']} transfers its consequence."
                    ),
                    "necessary_condition": (
                        "[PRECONDITION_SHA256:"
                        f"{runtime.canonical_sha256(event_index[target_event]['preconditions'][0])}] "
                        f"{event_index[target_event]['preconditions'][0]} is required."
                    ),
                }
            )
        timing_id = f"TIME-SLC-{connection['id'][4:]}"
        connection_records.append(
            {
                "id": f"CR-{connection['id'][4:]}",
                "connection_id": connection["id"],
                "relation": connection["relation"],
                "realization_kind": (
                    "causal_handoff"
                    if connection["relation"] == "causal"
                    else "associative_alignment"
                ),
                "source_anchor": source_anchor,
                "target_anchor": target_anchor,
                "causal_edge_ids": edge_ids,
                "timing_constraint_ids": [timing_id],
            }
        )
        timing.append(
            {
                "id": timing_id,
                "event_ids": [source_event, target_event],
                "constraint": (
                    f"[REL:{timing_relation}] "
                    + (
                        "Source resolves before target changes."
                        if connection["relation"] == "causal"
                        else "The two anchored states are compared without causal transfer."
                    )
                ),
                "story_effect": (
                    "The supporting line changes the main-line pressure."
                    if connection["relation"] == "causal"
                    else "The lines resonate without entering the causal DAG."
                ),
            }
        )

    def anchor_proposition(
        anchored: dict[str, object], obligation_id: str
    ) -> str:
        if anchored["side"] == "after":
            proposition_id = f"PROP-{str(anchored['event_id'])[3:]}-RESULT"
        else:
            proposition_id = (
                f"PROP-INITIAL-{str(anchored['storyline_id'])[3:]}"
            )
            if proposition_id not in proposition_index:
                item = {
                    "id": proposition_id,
                    "statement": str(anchored["state"]),
                    "source_ids": [str(anchored["storyline_id"])],
                    "audience": None,
                    "initially_true": True,
                    "terminality": "ordinary",
                }
                propositions.append(item)
                proposition_index[proposition_id] = item
                event_index[str(anchored["event_id"])][
                    "requires_proposition_ids"
                ].append(proposition_id)
        proposition_index[proposition_id]["source_ids"] = list(
            dict.fromkeys(
                [
                    *proposition_index[proposition_id]["source_ids"],
                    obligation_id,
                ]
            )
        )
        return proposition_id

    obligation_realizations = []
    for obligation in storyline.get("story_obligation_register", []):
        antecedent_anchors = [
            anchor(item["storyline_id"], item["state_index"])
            for item in obligation["antecedent_anchors"]
        ]
        consequent_anchor = anchor(
            obligation["consequent_anchor"]["storyline_id"],
            obligation["consequent_anchor"]["state_index"],
        )
        antecedent_props = [
            anchor_proposition(item, obligation["id"])
            for item in antecedent_anchors
        ]
        if obligation["kind"] in {
            "first_disclosure",
            "must_remain_unknown",
        }:
            consequent_prop = obligation["proposition_id"]
            if consequent_prop not in proposition_index:
                if obligation["kind"] == "first_disclosure":
                    origin = antecedent_anchors[0]
                    initially_true = origin["side"] == "before"
                    if initially_true:
                        event_index[origin["event_id"]][
                            "requires_proposition_ids"
                        ].append(consequent_prop)
                    else:
                        event_index[origin["event_id"]][
                            "produces_proposition_ids"
                        ].append(consequent_prop)
                else:
                    initially_true = True
                    event_index[consequent_anchor["event_id"]][
                        "requires_proposition_ids"
                    ].append(consequent_prop)
                item = {
                    "id": consequent_prop,
                    "statement": obligation["rationale"],
                    "source_ids": [obligation["id"]],
                    "audience": obligation["audience"],
                    "initially_true": initially_true,
                    "terminality": "ordinary",
                }
                propositions.append(item)
                proposition_index[consequent_prop] = item
            else:
                proposition_index[consequent_prop]["source_ids"] = list(
                    dict.fromkeys(
                        [
                            *proposition_index[consequent_prop]["source_ids"],
                            obligation["id"],
                        ]
                    )
                )
            if obligation["kind"] == "first_disclosure":
                event_index[consequent_anchor["event_id"]][
                    "discloses_proposition_ids"
                ].append(consequent_prop)
        else:
            consequent_prop = anchor_proposition(
                consequent_anchor, obligation["id"]
            )
        if obligation["kind"] in {"causes", "requires_all"}:
            event_index[consequent_anchor["event_id"]][
                "requires_proposition_ids"
            ].extend(antecedent_props)
        witness_events = list(
            dict.fromkeys(
                [item["event_id"] for item in antecedent_anchors]
                + [consequent_anchor["event_id"]]
            )
        )
        obligation_realizations.append(
            {
                "id": f"OBR-{obligation['id'][4:]}",
                "obligation_id": obligation["id"],
                "kind": obligation["kind"],
                "antecedent_proposition_ids": antecedent_props,
                "consequent_proposition_id": consequent_prop,
                "event_ids": witness_events,
                "evidence": obligation["acceptance_check"],
            }
        )

    for event in events:
        for field in (
            "requires_proposition_ids",
            "produces_proposition_ids",
            "discloses_proposition_ids",
        ):
            event[field] = list(dict.fromkeys(event[field]))

    decisions = [
        {
            "id": "DEC-T1-001",
            "gap": "Choose a world-time scale for event ordering.",
            "options": ["Abstract monotonic ticks.", "Calendar dates."],
            "selection": "Abstract monotonic ticks.",
            "owner": "T1",
            "authority_basis": "T1 owns event-level timing control.",
            "compatibility": "Preserves all S1 states and E1 affordances.",
            "impact_ids": [events[0]["id"]],
            "cost": "Exact calendar dates remain downstream.",
            "reversibility": "reversible",
            "downstream_freedom": "Scene duration and prose pacing remain open.",
            "projection_ids": [events[0]["id"]],
        }
    ]
    owned = [
        *[item["id"] for item in propositions],
        *[item["id"] for item in events],
        *[item["id"] for item in causal_edges],
        *[item["id"] for item in sequences],
        *[item["id"] for item in timing],
        *[item["id"] for item in ledgers],
        *[item["id"] for item in connection_records],
        *[item["id"] for item in obligation_realizations],
        *[item["id"] for item in coverage],
        *[item["id"] for item in decisions],
    ]
    claims = []
    for index, item in enumerate([*events, *sequences], 1):
        claims.append(
            {
                "id": f"DRV-T1-{index:03d}",
                "value_sha256": runtime.canonical_sha256(item),
                "source_ids": [
                    item["storyline_ids"][0]
                    if "storyline_ids" in item
                    else item["storyline_id"]
                ],
                "decision_ids": ["DEC-T1-001"],
                "projection_ids": [item["id"]],
            }
        )
    locked = [
        item["id"] for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    ]
    author_open = [
        item["id"] for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    ]
    semantic_marker = runtime.canonical_sha256(
        [item["responsibility"] for item in requirements]
    )
    model = {
        "schema_version": "2.1",
        "skill": "novel-event-timeline-designer",
        "stage": "T1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": owned,
            "downstream_freedom": sorted(
                {
                    slot
                    for line in lines
                    for slot in line["actor_slot_ids"]
                }
            ),
            "author_open": author_open,
        },
        "design_decisions": decisions,
        "derivation_claims": claims,
        "event_demands": copy.deepcopy(requirements),
        "event_span": {
            "start": min(item["world_time"] for item in events),
            "end": max(item["world_time"] for item in events),
            "granularity": f"abstract tick; upstream-semantics={semantic_marker}",
            "calendar_rules": ["Ticks are monotonic within causal edges."],
        },
        "timeline_axes": {
            "world_time_basis": f"Abstract world ticks; upstream-semantics={semantic_marker}",
            "narrative_time_strategy": "Disclosure order is independently constrained.",
            "axes": [
                "world_time",
                "background_time",
                "event_time",
                "narrative_disclosure",
            ],
        },
        "proposition_registry": propositions,
        "major_events": events,
        "causal_edges": causal_edges,
        "storyline_event_sequences": sequences,
        "connection_realization": connection_records,
        "obligation_realizations": obligation_realizations,
        "environment_placement": placements,
        "state_ledger": ledgers,
        "information_changes": [],
        "event_coverage_ledger": coverage,
        "narrative_timing_constraints": timing,
        "open_items": [
            {
                "id": f"OPEN-T1-{index:03d}",
                "question": f"Preserve author-open control {control['id']}.",
                "source_ids": [control["id"]],
                "status": "author_open",
            }
            for index, control in enumerate(
                [
                    item for item in baseline["control_registry"]
                    if item["hardness"] == "author_open"
                ],
                1,
            )
        ],
    }
    return _upgrade_agent_event_proposal_22(
        model=model,
        storyline=storyline,
        environment=environment,
    )


def _upgrade_agent_event_proposal_22(
    *,
    model: dict[str, object],
    storyline: dict[str, object],
    environment: dict[str, object],
) -> dict[str, object]:
    """Upgrade the test Agent's authored proposal to the current T1 contract.

    The fixture derives every identifier and projection from the supplied S1/E1
    objects.  It deliberately contains no run-specific IDs or expected counts.
    """

    digest = runtime.canonical_sha256
    lines = {item["id"]: item for item in storyline["storylines"]}
    steps = {item["id"]: item for item in environment["capability_step_registry"]}
    facts = {item["id"]: item for item in environment["capability_fact_registry"]}
    supports = {
        (item["storyline_id"], item["from_state_index"], item["to_state_index"]): item
        for item in environment["story_transition_support"]
    }
    readiness = {
        item["connection_id"]: item
        for item in environment["connection_path_readiness"]
    }
    milestones = sorted(
        storyline["temporal_architecture"]["milestones"],
        key=lambda item: (item["order"], item["id"]),
    )
    milestone_by_id = {item["id"]: item for item in milestones}
    milestone_order = {item["id"]: item["order"] for item in milestones}
    first_arrival = {}
    first_line_milestone = {}
    for milestone in milestones:
        for line_id in milestone["storyline_ids"]:
            first_line_milestone.setdefault(line_id, milestone["id"])
        for ref in milestone["state_refs"]:
            if ref["state_index"] > 0:
                first_arrival.setdefault(
                    (ref["storyline_id"], ref["state_index"]), milestone["id"]
                )

    event_by_id = {item["id"]: item for item in model["major_events"]}
    placement_by_event = {
        item["event_id"]: item for item in model["environment_placement"]
    }
    ledger_by_event = {
        item["trigger_ids"][0]: item for item in model["state_ledger"]
    }
    sequence_by_line = {
        item["storyline_id"]: item for item in model["storyline_event_sequences"]
    }
    coverage_by_line = {}
    requirement_by_id = {item["id"]: item for item in storyline["event_requirements"]}
    for record in model["event_coverage_ledger"]:
        requirement = requirement_by_id[record["source_ids"][0]]
        line_id = next(source for source in requirement["source_ids"] if source in lines)
        coverage_by_line[line_id] = record

    step_by_line = {}
    for line_id in lines:
        realization = next(
            item
            for item in environment["initial_anchor_option_realization_ledger"]
            if item["storyline_id"] == line_id and item["state_index"] == 0
        )
        candidate_steps = [steps[item] for item in realization["capability_step_ids"]]
        if len(candidate_steps) != 1:
            raise AssertionError(f"expected one initial E1 capability step for {line_id}")
        step_by_line[line_id] = candidate_steps[0]

    initial_registry = []
    selection_ledger = []
    process_subjects = []
    initial_event_ids = {}
    initial_prop_ids = {}
    process_event_ids_by_line = {}
    for line_id, line in lines.items():
        sequence = sequence_by_line[line_id]
        first_old = event_by_id[sequence["event_ids"][0]]
        step = step_by_line[line_id]
        option = environment["initial_anchor_support"][
            next(
                index
                for index, anchor in enumerate(environment["initial_anchor_support"])
                if anchor["storyline_id"] == line_id and anchor["state_index"] == 0
            )
        ]["support_options"][0]
        realization = next(
            item
            for item in environment["initial_anchor_option_realization_ledger"]
            if item["support_option_id"] == option["support_option_id"]
        )
        component_id = "ICOMP-" + digest([line_id, option["support_option_id"]])[:20]
        initial_event_id = "EV-INIT-" + digest(line_id)[:16]
        obligation_anchor_prop_id = f"PROP-INITIAL-{line_id[3:]}"
        initial_prop_id = (
            obligation_anchor_prop_id
            if any(
                item["id"] == obligation_anchor_prop_id
                for item in model["proposition_registry"]
            )
            else "PROP-INIT-" + digest(line_id)[:16]
        )
        initial_event_ids[line_id] = initial_event_id
        initial_prop_ids[line_id] = initial_prop_id
        initial_milestone = first_line_milestone[line_id]
        pss_id = "PSS-" + digest([line_id, "process-record"])[:20]
        before = "process:not_started"
        after = "process:initial_context_established"
        occurrence_id = "CSO-" + digest([initial_event_id, step["id"], 1])[:24]
        initial_event = {
            "id": initial_event_id,
            "responsibility": (
                "[RESP:background] Establish the active initial condition for " + line_id
            ),
            "world_time": "[WT:000000]",
            "storyline_ids": [line_id],
            "environment_id": step["environment_id"],
            "participant_slot_ids": list(line["actor_slot_ids"]),
            "initiator_slot_id": line["actor_slot_ids"][0],
            "counter_slot_ids": [],
            "preconditions": list(first_old["preconditions"]),
            "initiating_action": step["action"],
            "complication": "[NO_COUNTER:systemic constraint is the opposing force]",
            "decisive_change": f"{pss_id} changes from {before} to {after}.",
            "direct_result": f"The active initial condition for {line_id} becomes available.",
            "before_state": {pss_id: before},
            "after_state": {pss_id: after},
            "next_pressure": f"{line_id} must now enact its first bounded responsibility.",
            "requires_proposition_ids": [],
            "produces_proposition_ids": [initial_prop_id],
            "discloses_proposition_ids": [],
            "information_changes": [],
            "predecessor_event_ids": [],
            "event_kind": "process",
            "milestone_id": initial_milestone,
            "subject_id": pss_id,
            "subject_kind": "t1_process_record",
            "affordance_ids": [step["affordance_id"]],
            "e1_capability_step_ids": [step["id"]],
            "capability_step_occurrences": [
                {"occurrence_id": occurrence_id, "step_id": step["id"], "ordinal": 1}
            ],
            "requires_capability_fact_ids": list(step["requires_fact_ids"]),
            "produces_capability_fact_ids": list(step["produces_fact_ids"]),
            "requires_token_instance_ids": [],
            "produces_token_instance_ids": [],
            "initial_anchor_refs": [
                {"storyline_id": line_id, "state_index": 0, "component_id": component_id}
            ],
            "source_ids": [line_id, option["support_option_id"]],
            "atomicity_reason": "One T1-owned process record changes once.",
        }
        event_by_id[initial_event_id] = initial_event
        model["major_events"].insert(0, initial_event)
        sequence["event_ids"] = [
            initial_event_id,
            *[item for item in sequence["event_ids"] if item != initial_event_id],
        ]
        coverage_by_line[line_id]["realization_ids"] = [
            initial_event_id,
            *[
                item
                for item in coverage_by_line[line_id]["realization_ids"]
                if item != initial_event_id
            ],
        ]
        model["environment_placement"].append(
            {
                "event_id": initial_event_id,
                "environment_id": step["environment_id"],
                "affordance_ids": [step["affordance_id"]],
                "fit_evidence": f"{step['id']} locally realizes the active initial process.",
            }
        )
        access_id = next(
            item["id"]
            for item in environment["access_and_authority"]
            if item["subject_id"] == step["environment_id"]
        )
        model["state_ledger"].append(
            {
                "id": "ST-" + initial_event_id[3:],
                "subject_id": pss_id,
                "from_state": before,
                "trigger_ids": [initial_event_id],
                "to_state": after,
                "allowed_by_ids": [access_id],
                "consequence": "[KIND:state] Active initial context is established.",
            }
        )
        process_event_ids_by_line[line_id] = [initial_event_id]
        process_subjects.append(
            {
                "id": pss_id,
                "subject_kind": "t1_process_record",
                "owner_stage": "T1",
                "source_object_id": line_id,
                "source_state_vocabulary_hash": "",
                "state_vocabulary": [],
                "allowed_transitions": [],
                "scope_constraints": [f"The process record is local to {line_id}."],
                "semantic_review_claim_id": "T1PSS-" + digest([line_id, pss_id])[:24],
            }
        )
        initial_registry.append(
            {
                "storyline_id": line_id,
                "state_index": 0,
                "state": line["start_state"],
                "atomic_proposition_ids": [initial_prop_id],
                "atomic_components": [
                    {
                        "component_id": component_id,
                        "proposition_ids": [initial_prop_id],
                        "classification": "active_process",
                        "planned_event_ids": [initial_event_id],
                        "e1_support_option_ids": [option["support_option_id"]],
                    }
                ],
                "classification_summary": "active_process",
                "classification_source_ids": list(option["source_ids"]),
                "semantic_review_claim_id": "T1INIT-" + digest([line_id, option])[:24],
                "planned_event_ids": [initial_event_id],
            }
        )
        selection_ledger.append(
            {
                "storyline_id": line_id,
                "state_index": 0,
                "component_id": component_id,
                "support_option_id": option["support_option_id"],
                "capability_demand_id": option["capability_demand_id"],
                "realization_record_id": realization["id"],
            }
        )
        existing_initial = next(
            (
                item
                for item in model["proposition_registry"]
                if item["id"] == initial_prop_id
            ),
            None,
        )
        if existing_initial is None:
            model["proposition_registry"].append(
                {
                    "id": initial_prop_id,
                    "statement": line["start_state"],
                    "source_ids": [line_id],
                    "audience": None,
                    "initially_true": False,
                    "terminality": "ordinary",
                    "initial_anchor_refs": [
                        {"storyline_id": line_id, "state_index": 0}
                    ],
                    "producer_event_ids": [initial_event_id],
                }
            )
        else:
            existing_initial["initially_true"] = False
            existing_initial["initial_anchor_refs"] = [
                {"storyline_id": line_id, "state_index": 0}
            ]
            existing_initial["producer_event_ids"] = [initial_event_id]

    # Project E1 capabilities and convert every non-story transition into a
    # continuous T1-owned process record.
    transition_cover = []
    for line_id, sequence in sequence_by_line.items():
        line = lines[line_id]
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        step = step_by_line[line_id]
        pss = next(item for item in process_subjects if item["source_object_id"] == line_id)
        process_index = 1
        transition_milestones = []
        for event_id in (
            item
            for item in sequence["event_ids"]
            if item not in set(initial_event_ids.values())
        ):
            event = event_by_id[event_id]
            subject_id = next(iter(event["before_state"]))
            if subject_id == line_id:
                pair = (event["before_state"][line_id], event["after_state"][line_id])
                transition_index = next(
                    index for index, value in enumerate(zip(states, states[1:])) if value == pair
                )
                milestone_id = first_arrival.get((line_id, transition_index + 1))
                if milestone_id is None:
                    candidates = [
                        milestone
                        for milestone in milestones
                        if any(
                            ref["storyline_id"] == line_id
                            and ref["state_index"] >= transition_index + 1
                            for ref in milestone["state_refs"]
                        )
                    ]
                    milestone_id = (
                        candidates[0]["id"]
                        if candidates
                        else next(
                            milestone["id"]
                            for milestone in reversed(milestones)
                            if line_id in milestone["storyline_ids"]
                        )
                    )
                transition_milestones.append((event_id, milestone_id))
                event_kind = "story_transition"
                subject_kind = "storyline_state"
                transition_cover.append(
                    {
                        "storyline_id": line_id,
                        "from_state_index": transition_index,
                        "to_state_index": transition_index + 1,
                        "event_ids": [event_id],
                        "transition_support_id": supports[(line_id, transition_index, transition_index + 1)]["id"],
                    }
                )
            elif any(
                marker in ledger_by_event[event_id]["consequence"]
                for marker in ("[KIND:resource]", "[KIND:authority]")
            ):
                # These are upstream-owned formal resource/authority states,
                # not T1-local process records.  The frozen P2 kind vocabulary
                # has one non-process carrier for such external state changes;
                # subject_kind and the P4 ledger retain the exact distinction.
                event_kind = "authority_transition"
                subject_kind = (
                    "resource_state"
                    if "[KIND:resource]" in ledger_by_event[event_id]["consequence"]
                    else "authority_state"
                )
            else:
                previous_event = event_by_id[
                    process_event_ids_by_line[line_id][-1]
                ]
                previous = previous_event["after_state"][pss["id"]]
                current = f"process:step_{process_index:03d}"
                process_index += 1
                event["before_state"] = {pss["id"]: previous}
                event["after_state"] = {pss["id"]: current}
                event["decisive_change"] = f"{pss['id']} changes from {previous} to {current}."
                ledger = ledger_by_event[event_id]
                ledger["subject_id"] = pss["id"]
                ledger["from_state"] = previous
                ledger["to_state"] = current
                ledger["consequence"] = "[KIND:state] " + event["direct_result"]
                process_event_ids_by_line[line_id].append(event_id)
                event_kind = "process"
                subject_kind = "t1_process_record"
            event["event_kind"] = event_kind
            event["subject_id"] = next(iter(event["before_state"]))
            event["subject_kind"] = subject_kind
            event["affordance_ids"] = [step["affordance_id"]]
            event["e1_capability_step_ids"] = [step["id"]]
            ordinal = sequence["event_ids"].index(event_id) + 1
            event["capability_step_occurrences"] = [
                {
                    "occurrence_id": "CSO-" + digest([event_id, step["id"], ordinal])[:24],
                    "step_id": step["id"],
                    "ordinal": ordinal,
                }
            ]
            event["requires_capability_fact_ids"] = list(step["requires_fact_ids"])
            event["produces_capability_fact_ids"] = list(step["produces_fact_ids"])
            event["requires_token_instance_ids"] = []
            event["produces_token_instance_ids"] = []
            event["initial_anchor_refs"] = []
            event["source_ids"] = [line_id]
            event["atomicity_reason"] = "One formal subject changes once."
        # Assign filler process events to the next transition milestone.
        next_milestone = transition_milestones[-1][1]
        transition_milestone_by_event = dict(transition_milestones)
        for event_id in reversed(sequence["event_ids"]):
            if event_id in transition_milestone_by_event:
                next_milestone = transition_milestone_by_event[event_id]
            event_by_id[event_id]["milestone_id"] = next_milestone
        vocabulary = ["process:not_started", "process:initial_context_established"]
        for event_id in process_event_ids_by_line[line_id][1:]:
            vocabulary.append(event_by_id[event_id]["after_state"][pss["id"]])
        pss["state_vocabulary"] = vocabulary
        pss["allowed_transitions"] = [
            {"from": left, "to": right} for left, right in zip(vocabulary, vocabulary[1:])
        ]
        pss["source_state_vocabulary_hash"] = digest(vocabulary)

    # Rebuild the causal graph from exact sequence adjacency and one owned
    # cross-line entry edge for each causal S1 connection.
    edge_pairs = []
    connection_entry_pair = {}
    for line_id, sequence in sequence_by_line.items():
        for left, right in zip(sequence["event_ids"], sequence["event_ids"][1:]):
            edge_pairs.append((left, right, None))
    anchors = {}
    for cover in transition_cover:
        anchors.setdefault(
            (cover["storyline_id"], cover["from_state_index"]),
            (cover["event_ids"][0], "before"),
        )
        anchors[(cover["storyline_id"], cover["to_state_index"])] = (
            cover["event_ids"][-1], "after"
        )
    # A causal connection exposes dedicated source and target endpoint steps.
    # Bind each endpoint only to its exact story anchor: the source produces
    # the transfer fact and the target consumes it.  Earlier target-line
    # events retain the line's base step and cannot acquire a false
    # predecessor.
    def bind_endpoint_steps(event, endpoint_step_ids):
        combined_step_ids = list(
            dict.fromkeys([*event["e1_capability_step_ids"], *endpoint_step_ids])
        )
        event["e1_capability_step_ids"] = combined_step_ids
        event["affordance_ids"] = list(
            dict.fromkeys(steps[item]["affordance_id"] for item in combined_step_ids)
        )
        event["requires_capability_fact_ids"] = sorted(
            {
                fact_id
                for step_id in combined_step_ids
                for fact_id in steps[step_id]["requires_fact_ids"]
            }
        )
        event["produces_capability_fact_ids"] = sorted(
            {
                fact_id
                for step_id in combined_step_ids
                for fact_id in steps[step_id]["produces_fact_ids"]
            }
        )
        existing_occurrence_steps = {
            item["step_id"] for item in event["capability_step_occurrences"]
        }
        for step_id in combined_step_ids:
            if step_id in existing_occurrence_steps:
                continue
            ordinal = max(
                (
                    item["ordinal"]
                    for item in event["capability_step_occurrences"]
                ),
                default=0,
            ) + 1
            event["capability_step_occurrences"].append(
                {
                    "occurrence_id": "CSO-"
                    + digest([event["id"], step_id, ordinal])[:24],
                    "step_id": step_id,
                    "ordinal": ordinal,
                }
            )
            existing_occurrence_steps.add(step_id)

    for connection in storyline["connections"]:
        if connection["relation"] != "causal":
            continue
        ready = readiness[connection["id"]]
        source_event = event_by_id[
            anchors[(connection["from_storyline_id"], connection["from_state_index"])][0]
        ]
        target_event = event_by_id[
            anchors[(connection["to_storyline_id"], connection["to_state_index"])][0]
        ]
        bind_endpoint_steps(source_event, ready["source_endpoint_step_ids"])
        bind_endpoint_steps(target_event, ready["target_endpoint_step_ids"])
    for connection in storyline["connections"]:
        if connection["relation"] != "causal":
            continue
        source_event = anchors[(connection["from_storyline_id"], connection["from_state_index"])][0]
        target_event = anchors[
            (connection["to_storyline_id"], connection["to_state_index"])
        ][0]
        edge_pairs.append((source_event, target_event, connection["id"]))
        connection_entry_pair[connection["id"]] = (source_event, target_event)
    unique_pairs = []
    seen_pairs = set()
    for item in edge_pairs:
        pair = item[:2]
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique_pairs.append(item)
    edge_by_pair = {}
    model["causal_edges"] = []
    for index, (left, right, owner) in enumerate(unique_pairs, 1):
        edge_id = "CE-22-" + digest([left, right, owner])[:20]
        left_event = event_by_id[left]
        right_event = event_by_id[right]
        edge = {
            "id": edge_id,
            "from_event_id": left,
            "to_event_id": right,
            "edge_kind": (
                "narrative_causal"
                if isinstance(owner, str) and owner.startswith("SLC-")
                else "sequencing"
            ),
            "payload_ids": [],
            "mechanism": (
                f"[CAUSE_RESULT_SHA256:{digest(left_event['direct_result'])}]"
                f"[CAUSE_PRESSURE_SHA256:{digest(left_event['next_pressure'])}] "
                "The preceding bounded result enables the next event."
            ),
            "necessary_condition": (
                f"[PRECONDITION_SHA256:{digest(right_event['preconditions'][0])}] "
                "The target event's declared precondition must hold."
            ),
        }
        model["causal_edges"].append(edge)
        edge_by_pair[(left, right)] = edge
    for event in event_by_id.values():
        event["predecessor_event_ids"] = sorted(
            left for left, right, _owner in unique_pairs if right == event["id"]
        )
    for line_id, initial_event_id in initial_event_ids.items():
        first_old_id = sequence_by_line[line_id]["event_ids"][1]
        event_by_id[first_old_id]["requires_proposition_ids"] = list(
            dict.fromkeys(
                [*event_by_id[first_old_id]["requires_proposition_ids"], initial_prop_ids[line_id]]
            )
        )

    # Assign globally monotonic slots using milestone order followed by a
    # topological order within each bucket.
    pending = set(event_by_id)
    emitted = []
    while pending:
        ready_ids = [
            event_id
            for event_id in pending
            if set(event_by_id[event_id]["predecessor_event_ids"]).isdisjoint(pending)
        ]
        if not ready_ids:
            cycle_edges = [
                (left, right, owner)
                for left, right, owner in unique_pairs
                if left in pending and right in pending
            ]
            raise AssertionError(
                "test Agent authored a causal cycle: "
                + repr({"pending": sorted(pending), "edges": cycle_edges})
            )
        ready_ids.sort(
            key=lambda event_id: (
                milestone_order[event_by_id[event_id]["milestone_id"]],
                event_by_id[event_id]["storyline_ids"][0],
                sequence_by_line[event_by_id[event_id]["storyline_ids"][0]]["event_ids"].index(event_id),
            )
        )
        chosen = ready_ids[0]
        emitted.append(chosen)
        pending.remove(chosen)
    observed_orders = [milestone_order[event_by_id[event_id]["milestone_id"]] for event_id in emitted]
    if observed_orders != sorted(observed_orders):
        raise AssertionError("S1 milestone order conflicts with the authored causal graph")
    for tick, event_id in enumerate(emitted, 1):
        slot = f"[WT:{tick:06d}]"
        event_by_id[event_id]["world_time"] = slot

    # Exact capability occurrence projection is built after the obligation
    # support map exists; every E1 requirement receives its own T1 occurrence.
    occurrence_cover = []
    milestone_buckets = [
        {
            "milestone_id": milestone["id"],
            "order": milestone["order"],
            "phase_id": milestone["phase_id"],
            "storyline_ids": list(milestone["storyline_ids"]),
            "state_refs": copy.deepcopy(milestone["state_refs"]),
            "connection_ids": list(milestone["connection_ids"]),
            "event_ids": [
                event_id
                for event_id in emitted
                if event_by_id[event_id]["milestone_id"] == milestone["id"]
            ],
        }
        for milestone in milestones
    ]

    # Rebuild connection projections over the same explicit predecessor paths.
    connection_paths = []
    realization_by_connection = {
        item["connection_id"]: item for item in model["connection_realization"]
    }
    timing_by_id = {item["id"]: item for item in model["narrative_timing_constraints"]}
    for connection in storyline["connections"]:
        record = realization_by_connection[connection["id"]]
        source_event = anchors[(connection["from_storyline_id"], connection["from_state_index"])][0]
        target_event = anchors[(connection["to_storyline_id"], connection["to_state_index"])][0]
        ready = readiness[connection["id"]]
        if connection["relation"] == "causal":
            event_path = [source_event, target_event]
            path_edges = [edge_by_pair[pair] for pair in zip(event_path, event_path[1:])]
            record["causal_edge_ids"] = [item["id"] for item in path_edges]
            timing_by_id[record["timing_constraint_ids"][0]]["event_ids"] = event_path
        else:
            event_path = []
            record["causal_edge_ids"] = []
        connection_paths.append(
            {
                "connection_id": connection["id"],
                "relation": connection["relation"],
                "source_event_id": source_event,
                "target_event_id": target_event,
                "bridge_event_ids": [],
                "source_endpoint_step_ids": list(ready["source_endpoint_step_ids"]) if connection["relation"] == "causal" else [],
                "target_endpoint_step_ids": list(ready["target_endpoint_step_ids"]) if connection["relation"] == "causal" else [],
                "transfer_fact_id": ready["transfer_fact_id"] if connection["relation"] == "causal" else None,
                "topology_path_ids": list(ready["topology_path_ids"]) if connection["relation"] == "causal" else [],
                "predecessor_path_event_ids": event_path,
                "timing_constraint_ids": list(record["timing_constraint_ids"]),
            }
        )

    # Add current proposition inverse fields after all obligation edits are done.
    producer_map = {}
    for event in model["major_events"]:
        for proposition_id in event["produces_proposition_ids"]:
            producer_map.setdefault(proposition_id, []).append(event["id"])
    for proposition in model["proposition_registry"]:
        proposition.setdefault("initial_anchor_refs", [])
        proposition["producer_event_ids"] = sorted(producer_map.get(proposition["id"], []))

    obligation_by_id = {
        item["id"]: item for item in storyline["story_obligation_register"]
    }
    obligation_plan = []
    for realization in model["obligation_realizations"]:
        obligation = obligation_by_id[realization["obligation_id"]]
        antecedent_events = [
            anchors[(item["storyline_id"], item["state_index"])][0]
            for item in obligation["antecedent_anchors"]
        ]
        consequent_event = anchors[
            (
                obligation["consequent_anchor"]["storyline_id"],
                obligation["consequent_anchor"]["state_index"],
            )
        ][0]
        obligation_plan.append(
            {
                "obligation_id": obligation["id"],
                "kind": obligation["kind"],
                "antecedent_event_ids": antecedent_events,
                "consequent_event_id": consequent_event,
                "antecedent_proposition_ids": list(realization["antecedent_proposition_ids"]),
                "consequent_proposition_id": realization["consequent_proposition_id"],
                "audience": obligation["audience"],
                "timing_rule": obligation["acceptance_check"],
                "disclosure_rule": obligation["rationale"],
            }
        )

    transition_events_by_support = {
        item["transition_support_id"]: list(item["event_ids"])
        for item in transition_cover
    }
    initial_events_by_option = {
        option_id: list(component["planned_event_ids"])
        for initial in initial_registry
        for component in initial["atomic_components"]
        for option_id in component["e1_support_option_ids"]
    }
    connection_events_by_support = {
        item["connection_id"]: [
            item["source_event_id"],
            *item["bridge_event_ids"],
            item["target_event_id"],
        ]
        for item in connection_paths
    }
    obligation_binding_by_requirement = {
        item["occurrence_requirement_id"]: item
        for item in environment.get("obligation_occurrence_bindings", [])
    }
    emitted_order = {event_id: index for index, event_id in enumerate(emitted)}
    group_events_used = {}
    exclusive_groups = {
        item["distinct_group_id"]
        for item in environment["capability_occurrence_requirements"]
        if item["share_policy"] == "exclusive"
    }
    for requirement in environment["capability_occurrence_requirements"]:
        binding = obligation_binding_by_requirement.get(requirement["id"])
        if binding is not None:
            support_id = binding["support_id"]
            candidate_ids = (
                transition_events_by_support[support_id]
                if support_id in transition_events_by_support
                else initial_events_by_option.get(
                    support_id, connection_events_by_support.get(support_id, [])
                )
            )
        else:
            candidate_ids = list(event_by_id)
        candidates = sorted(
            {
                event_id
                for event_id in candidate_ids
                if requirement["step_id"]
                in event_by_id[event_id]["e1_capability_step_ids"]
            },
            key=emitted_order.__getitem__,
        )
        selected_ids = []
        for occurrence_index in range(requirement["minimum_occurrences"]):
            used_in_group = group_events_used.setdefault(
                requirement["distinct_group_id"], set()
            )
            available = [
                event_id
                for event_id in candidates
                if requirement["distinct_group_id"] not in exclusive_groups
                or event_id not in used_in_group
            ]
            if not available:
                raise AssertionError(
                    "test Agent cannot allocate distinct E1 occurrence "
                    + requirement["id"]
                )
            event_id = available[0]
            event = event_by_id[event_id]
            ordinal = max(
                (
                    item["ordinal"]
                    for item in event["capability_step_occurrences"]
                ),
                default=0,
            ) + 1
            occurrence_id = "CSO-" + digest(
                [event_id, requirement["step_id"], ordinal]
            )[:24]
            event["capability_step_occurrences"].append(
                {
                    "occurrence_id": occurrence_id,
                    "step_id": requirement["step_id"],
                    "ordinal": ordinal,
                }
            )
            used_in_group.add(event_id)
            selected_ids.append(occurrence_id)
        occurrence_cover.append(
            {"requirement_id": requirement["id"], "occurrence_ids": selected_ids}
        )

    # Current 2.5 information changes are authored from the exact disclosure
    # event, proposition, communication-capable E1 occurrence and (when
    # applicable) the S1/E1 first-disclosure obligation binding.
    cover_by_requirement = {
        item["requirement_id"]: set(item["occurrence_ids"])
        for item in occurrence_cover
    }
    bindings_by_obligation = {}
    for binding in environment.get("obligation_occurrence_bindings", []):
        bindings_by_obligation.setdefault(binding["obligation_id"], []).append(
            binding
        )
    information_changes = []
    subject_state = {}
    for event_id in emitted:
        event = event_by_id[event_id]
        occurrence_by_id = {
            item["occurrence_id"]: item
            for item in event["capability_step_occurrences"]
        }
        for proposition_id in sorted(event["discloses_proposition_ids"]):
            first_obligation_ids = sorted(
                item["obligation_id"]
                for item in obligation_plan
                if item["kind"] == "first_disclosure"
                and item["consequent_event_id"] == event_id
                and item["consequent_proposition_id"] == proposition_id
            )
            source_occurrence_id = None
            for obligation_id in first_obligation_ids:
                for binding in bindings_by_obligation.get(obligation_id, []):
                    candidates = sorted(
                        cover_by_requirement.get(
                            binding["occurrence_requirement_id"], set()
                        )
                        & set(occurrence_by_id)
                    )
                    if candidates:
                        source_occurrence_id = candidates[0]
                        break
                if source_occurrence_id is not None:
                    break
            if source_occurrence_id is None:
                source_occurrence_id = next(
                    (
                        occurrence_id
                        for occurrence_id, occurrence in occurrence_by_id.items()
                        if "communicate"
                        in steps[occurrence["step_id"]]["supported_modes"]
                    ),
                    None,
                )
            if source_occurrence_id is None:
                raise AssertionError(
                    f"disclosure {event_id}/{proposition_id} lacks a communication occurrence"
                )
            source_step = steps[
                occurrence_by_id[source_occurrence_id]["step_id"]
            ]
            visibility_ids = sorted(
                set(event["participant_slot_ids"])
                & set(source_step["actor_slot_ids"])
            )
            if not visibility_ids:
                raise AssertionError(
                    f"disclosure {event_id}/{proposition_id} lacks a visible participant"
                )
            subject_id = visibility_ids[0]
            before = subject_state.get(
                subject_id,
                f"{subject_id} has not learned {proposition_id}.",
            )
            after = f"{subject_id} has learned {proposition_id} at {event_id}."
            info_id = "INFO-" + digest(
                [event_id, proposition_id, source_occurrence_id, subject_id]
            )[:24]
            information_changes.append(
                {
                    "id": info_id,
                    "subject_id": subject_id,
                    "proposition_id": proposition_id,
                    "before": before,
                    "after": after,
                    "event_ids": [event_id],
                    "source_occurrence_id": source_occurrence_id,
                    "source_obligation_ids": first_obligation_ids,
                    "visibility_ids": visibility_ids,
                }
            )
            event["information_changes"].append(info_id)
            subject_state[subject_id] = after
    model["information_changes"] = information_changes

    for event in model["major_events"]:
        event["consumes_token_instance_ids"] = []
        event["lifecycle_effects"] = []

    # Planned objects are exact P3 sources; canonical events project them field
    # for field, while preserving the legacy human-facing fields.
    planned_events = []
    for event in model["major_events"]:
        planned_events.append(
            {
                "id": event["id"],
                "kind": event["event_kind"],
                "milestone_id": event["milestone_id"],
                "world_time_slot": event["world_time"],
                "storyline_ids": list(event["storyline_ids"]),
                "changed_subject": {
                    "subject_id": event["subject_id"],
                    "before": event["before_state"][event["subject_id"]],
                    "after": event["after_state"][event["subject_id"]],
                    "subject_kind": event["subject_kind"],
                },
                "environment_id": event["environment_id"],
                "affordance_ids": list(event["affordance_ids"]),
                "initiating_action": event["initiating_action"],
                "e1_capability_step_ids": list(event["e1_capability_step_ids"]),
                "capability_step_occurrences": copy.deepcopy(event["capability_step_occurrences"]),
                "requires_capability_fact_ids": list(event["requires_capability_fact_ids"]),
                "produces_capability_fact_ids": list(event["produces_capability_fact_ids"]),
                "requires_token_instance_ids": list(event["requires_token_instance_ids"]),
                "consumes_token_instance_ids": list(event["consumes_token_instance_ids"]),
                "produces_token_instance_ids": list(event["produces_token_instance_ids"]),
                "lifecycle_effects": copy.deepcopy(event["lifecycle_effects"]),
                "requires_proposition_ids": list(event["requires_proposition_ids"]),
                "produces_proposition_ids": list(event["produces_proposition_ids"]),
                "discloses_proposition_ids": list(event["discloses_proposition_ids"]),
                "initial_anchor_refs": copy.deepcopy(event["initial_anchor_refs"]),
                "predecessor_event_ids": list(event["predecessor_event_ids"]),
                "preconditions": list(event["preconditions"]),
                "direct_result": event["direct_result"],
                "next_pressure": event["next_pressure"],
                "source_ids": list(event["source_ids"]),
                "atomicity_reason": event["atomicity_reason"],
            }
        )

    e1_source = next(
        item
        for item in model["source_artifacts"]
        if PurePosixPath(item["path"]).parts[:2] == ("sources", "E1")
        and PurePosixPath(item["path"]).name == "environment-system.json"
    )
    model.update(
        t1.t1_contract_23.expected_e1_digests(
            environment,
            source_path=e1_source["path"],
            source_sha256=e1_source["sha256"],
            canonical_sha256=digest,
        )
    )
    model.update(
        {
            "schema_version": "2.5",
            "initial_condition_registry": initial_registry,
            "initial_anchor_option_selection_ledger": selection_ledger,
            "planned_event_registry": planned_events,
            "process_state_subject_registry": process_subjects,
            "planned_proposition_registry": copy.deepcopy(model["proposition_registry"]),
            "planned_causal_edges": copy.deepcopy(model["causal_edges"]),
            "transition_event_cover": transition_cover,
            "milestone_event_buckets": milestone_buckets,
            "connection_event_paths": connection_paths,
            "obligation_event_plan": obligation_plan,
            "capability_occurrence_event_cover": occurrence_cover,
            "authority_token_instance_ledger": [],
            "lifecycle_scope": {
                "id": "LFS-NOT-APPLICABLE",
                "applicability": "not_applicable",
                "source_ids": ["SL-A"],
                "lifecycle_contract_ids": [],
                "semantic_review_claim_id": "T1LFS-NOT-APPLICABLE",
            },
            "lifecycle_contract_registry": [],
        }
    )
    model["event_span"]["start"] = event_by_id[emitted[0]]["world_time"]
    model["event_span"]["end"] = event_by_id[emitted[-1]]["world_time"]
    for record in model["narrative_timing_constraints"]:
        if record["id"].startswith("TIME-ROOT-"):
            line_suffix = record["id"][len("TIME-ROOT-") :]
            line_id = next(item for item in lines if item[3:] == line_suffix)
            record["event_ids"] = [initial_event_ids[line_id]]

    # Recompute exact ownership and derivation evidence after adding PSS objects.
    owned_entities = [
        *[item["id"] for item in model["proposition_registry"]],
        *[item["id"] for item in model["major_events"]],
        *[item["id"] for item in model["causal_edges"]],
        *[item["id"] for item in model["storyline_event_sequences"]],
        *[item["id"] for item in model["narrative_timing_constraints"]],
        *[item["id"] for item in model["state_ledger"]],
        *[item["id"] for item in model["connection_realization"]],
        *[item["id"] for item in model["obligation_realizations"]],
        *[item["id"] for item in model["event_coverage_ledger"]],
        *[item["id"] for item in model["information_changes"]],
        *[item["id"] for item in process_subjects],
        model["lifecycle_scope"]["id"],
        *[item["token_instance_id"] for item in model["authority_token_instance_ledger"]],
        *[item["id"] for item in model["design_decisions"]],
    ]
    model["authority_partition"]["autonomous_owned"] = owned_entities
    model["design_decisions"][0]["impact_ids"] = [emitted[0]]
    model["design_decisions"][0]["projection_ids"] = [emitted[0]]
    claims = []
    for index, item in enumerate(
        [*model["major_events"], *model["storyline_event_sequences"]], 1
    ):
        claims.append(
            {
                "id": f"DRV-T1-{index:03d}",
                "value_sha256": digest(item),
                "source_ids": [
                    item["storyline_ids"][0]
                    if "storyline_ids" in item
                    else item["storyline_id"]
                ],
                "decision_ids": [model["design_decisions"][0]["id"]],
                "projection_ids": [item["id"]],
            }
        )
    model["derivation_claims"] = claims
    return model


class T1PureContractTests(unittest.TestCase):
    @staticmethod
    def _information_case() -> dict[str, object]:
        events = {
            "EV-DISCLOSE-A": {
                "participant_slot_ids": ["SLOT-SENDER", "SLOT-RECEIVER"],
                "discloses_proposition_ids": ["PROP-A"],
                "capability_step_occurrences": [
                    {
                        "occurrence_id": "CSO-DISCLOSE-A",
                        "step_id": "CSTEP-DISCLOSE-A",
                        "ordinal": 1,
                    }
                ],
            },
            "EV-DISCLOSE-B": {
                "participant_slot_ids": ["SLOT-SENDER", "SLOT-RECEIVER"],
                "discloses_proposition_ids": ["PROP-B"],
                "capability_step_occurrences": [
                    {
                        "occurrence_id": "CSO-DISCLOSE-B",
                        "step_id": "CSTEP-DISCLOSE-B",
                        "ordinal": 1,
                    }
                ],
            },
        }
        model = {
            "information_changes": [
                {
                    "id": "INFO-DISCLOSE-A",
                    "subject_id": "SLOT-RECEIVER",
                    "proposition_id": "PROP-A",
                    "before": "Receiver knows neither proposition.",
                    "after": "Receiver knows proposition A only.",
                    "event_ids": ["EV-DISCLOSE-A"],
                    "source_occurrence_id": "CSO-DISCLOSE-A",
                    "source_obligation_ids": ["SOB-FIRST-A"],
                    "visibility_ids": ["SLOT-RECEIVER"],
                },
                {
                    "id": "INFO-DISCLOSE-B",
                    "subject_id": "SLOT-RECEIVER",
                    "proposition_id": "PROP-B",
                    "before": "Receiver knows proposition A only.",
                    "after": "Receiver knows propositions A and B.",
                    "event_ids": ["EV-DISCLOSE-B"],
                    "source_occurrence_id": "CSO-DISCLOSE-B",
                    "source_obligation_ids": ["SOB-FIRST-B"],
                    "visibility_ids": ["SLOT-RECEIVER"],
                },
            ],
            "capability_occurrence_event_cover": [
                {
                    "requirement_id": "COR-DISCLOSE-A",
                    "occurrence_ids": ["CSO-DISCLOSE-A"],
                },
                {
                    "requirement_id": "COR-DISCLOSE-B",
                    "occurrence_ids": ["CSO-DISCLOSE-B"],
                },
            ],
            "obligation_event_plan": [
                {
                    "obligation_id": "SOB-FIRST-A",
                    "kind": "first_disclosure",
                    "consequent_event_id": "EV-DISCLOSE-A",
                    "consequent_proposition_id": "PROP-A",
                },
                {
                    "obligation_id": "SOB-FIRST-B",
                    "kind": "first_disclosure",
                    "consequent_event_id": "EV-DISCLOSE-B",
                    "consequent_proposition_id": "PROP-B",
                },
            ],
        }
        storyline = {
            "story_obligation_register": [
                {
                    "id": "SOB-FIRST-A",
                    "kind": "first_disclosure",
                    "proposition_id": "PROP-A",
                },
                {
                    "id": "SOB-FIRST-B",
                    "kind": "first_disclosure",
                    "proposition_id": "PROP-B",
                },
            ]
        }
        environment = {
            "capability_step_registry": [
                {
                    "id": "CSTEP-DISCLOSE-A",
                    "actor_slot_ids": ["SLOT-RECEIVER"],
                    "supported_modes": ["communicate"],
                },
                {
                    "id": "CSTEP-DISCLOSE-B",
                    "actor_slot_ids": ["SLOT-RECEIVER"],
                    "supported_modes": ["observe", "communicate"],
                },
            ],
            "obligation_occurrence_bindings": [
                {
                    "obligation_id": "SOB-FIRST-A",
                    "occurrence_requirement_id": "COR-DISCLOSE-A",
                    "step_id": "CSTEP-DISCLOSE-A",
                },
                {
                    "obligation_id": "SOB-FIRST-B",
                    "occurrence_requirement_id": "COR-DISCLOSE-B",
                    "step_id": "CSTEP-DISCLOSE-B",
                },
            ],
        }
        return {
            "model": model,
            "storyline": storyline,
            "environment": environment,
            "events": events,
        }

    def _validate_information_case(self, case: dict[str, object]) -> None:
        t1.t1_contract_24.validate_information_projection(
            case["model"],
            case["storyline"],
            case["environment"],
            case["events"],
        )

    def test_two_disclosures_have_exact_information_projection(self) -> None:
        self._validate_information_case(self._information_case())

    def test_disclosures_cannot_leave_information_ledger_empty(self) -> None:
        case = self._information_case()
        case["model"]["information_changes"] = []
        with self.assertRaisesRegex(
            t1.t1_contract_24.Contract24Error,
            "T1_INFORMATION_DISCLOSURE_COVERAGE_MISSING",
        ):
            self._validate_information_case(case)

    def test_information_projection_rejects_dangling_and_mismatched_refs(self) -> None:
        mutations = (
            ("event_ids", ["EV-MISSING"], "T1_INFORMATION_EVENT_MISMATCH"),
            ("proposition_id", "PROP-B", "T1_INFORMATION_PROPOSITION_MISMATCH"),
            (
                "source_occurrence_id",
                "CSO-MISSING",
                "T1_INFORMATION_SOURCE_OCCURRENCE_MISMATCH",
            ),
        )
        for field, value, code in mutations:
            with self.subTest(field=field):
                case = self._information_case()
                case["model"]["information_changes"][0][field] = value
                with self.assertRaisesRegex(t1.t1_contract_24.Contract24Error, code):
                    self._validate_information_case(case)

    def test_information_projection_rejects_visibility_subject_and_source(self) -> None:
        case = self._information_case()
        case["model"]["information_changes"][0]["visibility_ids"] = [
            "SLOT-SENDER"
        ]
        with self.assertRaisesRegex(
            t1.t1_contract_24.Contract24Error,
            "T1_INFORMATION_VISIBILITY_MISMATCH",
        ):
            self._validate_information_case(case)

        case = self._information_case()
        case["model"]["information_changes"][0]["subject_id"] = "SLOT-SENDER"
        with self.assertRaisesRegex(
            t1.t1_contract_24.Contract24Error,
            "T1_INFORMATION_SUBJECT_MISMATCH",
        ):
            self._validate_information_case(case)

        case = self._information_case()
        case["model"]["information_changes"][0]["source_obligation_ids"] = []
        with self.assertRaisesRegex(
            t1.t1_contract_24.Contract24Error,
            "T1_INFORMATION_FIRST_DISCLOSURE_COVERAGE_MISSING",
        ):
            self._validate_information_case(case)

    def test_one_evd_realizes_two_events_through_two_local_affordances(self) -> None:
        events = {
            "EV-FIELD": {
                "environment_id": "ENV-FIELD",
                "initiating_action": "secure source",
                "preconditions": ["field custody active"],
            },
            "EV-MEMORY": {
                "environment_id": "ENV-MEMORY",
                "initiating_action": "attempt read",
                "preconditions": ["read authorization active"],
            },
        }
        affordances = {
            "AFF-FIELD": {
                "id": "AFF-FIELD",
                "environment_id": "ENV-FIELD",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["secure source"],
                "prerequisites": ["field custody active"],
            },
            "AFF-MEMORY": {
                "id": "AFF-MEMORY",
                "environment_id": "ENV-MEMORY",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["attempt read"],
                "prerequisites": ["read authorization active"],
            },
        }
        t1._validate_event_affordance_realizations(
            events=events,
            placements={
                "EV-FIELD": {
                    "affordance_ids": ["AFF-FIELD"],
                },
                "EV-MEMORY": {
                    "affordance_ids": ["AFF-MEMORY"],
                },
            },
            affordances=affordances,
            coverage_by_requirement={
                "EVD-A": {
                    "realization_ids": ["EV-FIELD", "EV-MEMORY"],
                }
            },
        )

    def test_exact_evd_affordance_binding_rejects_proxy_and_unused_interfaces(
        self,
    ) -> None:
        event = {
            "EV-A": {
                "environment_id": "ENV-A",
                "initiating_action": "act",
                "preconditions": ["ready"],
            }
        }
        affordances = {
            "AFF-A": {
                "id": "AFF-A",
                "environment_id": "ENV-A",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["act"],
                "prerequisites": ["ready"],
            },
            "AFF-SAME-LINE-WRONG-EVD": {
                "id": "AFF-SAME-LINE-WRONG-EVD",
                "environment_id": "ENV-A",
                "event_requirement_ids": ["EVD-B"],
                "allowed_actions": ["act"],
                "prerequisites": ["ready"],
            },
            "AFF-WRONG-ACTION": {
                "id": "AFF-WRONG-ACTION",
                "environment_id": "ENV-A",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["different action"],
                "prerequisites": ["ready"],
            },
        }
        coverage = {"EVD-A": {"realization_ids": ["EV-A"]}}
        for placed in (
            ["AFF-SAME-LINE-WRONG-EVD"],
            ["AFF-WRONG-ACTION"],
            ["AFF-A", "AFF-SAME-LINE-WRONG-EVD"],
        ):
            with self.subTest(placed=placed):
                with self.assertRaises(t1.T1Error) as caught:
                    t1._validate_event_affordance_realizations(
                        events=event,
                        placements={"EV-A": {"affordance_ids": placed}},
                        affordances=affordances,
                        coverage_by_requirement=coverage,
                    )
                self.assertEqual(
                    "T1_AFFORDANCE_REQUIREMENT_MISMATCH",
                    caught.exception.code,
                )

    """Low-cost production-validator attacks with no upstream package build."""

    @staticmethod
    def _anchors() -> dict[tuple[str, int], dict[str, object]]:
        output = {}
        output.update(
            t1._state_anchors_for_line(
                "SL-A",
                ["repeat", "middle", "repeat"],
                [
                    {"trigger_ids": ["EV-A0"]},
                    {"trigger_ids": ["EV-A1"]},
                ],
            )
        )
        output.update(
            t1._state_anchors_for_line(
                "SL-B",
                ["b0", "b1", "b2"],
                [
                    {"trigger_ids": ["EV-B0"]},
                    {"trigger_ids": ["EV-B1"]},
                ],
            )
        )
        return output

    @classmethod
    def _causal_case(cls) -> dict[str, object]:
        anchors = cls._anchors()
        events = {
            "EV-A0": {"storyline_ids": ["SL-A"]},
            "EV-A1": {"storyline_ids": ["SL-A"]},
            "EV-B0": {"storyline_ids": ["SL-B"]},
            "EV-B1": {"storyline_ids": ["SL-B"]},
        }
        edge = {
            "id": "CE-AB",
            "from_event_id": "EV-A1",
            "to_event_id": "EV-B1",
        }
        return {
            "realizations": [
                {
                    "id": "CR-AB",
                    "connection_id": "SLC-AB",
                    "relation": "causal",
                    "realization_kind": "causal_handoff",
                    "source_anchor": copy.deepcopy(
                        anchors[("SL-A", 2)]
                    ),
                    "target_anchor": copy.deepcopy(
                        anchors[("SL-B", 2)]
                    ),
                    "causal_edge_ids": ["CE-AB"],
                    "timing_constraint_ids": ["TIME-AB"],
                }
            ],
            "connections": {
                "SLC-AB": {
                    "id": "SLC-AB",
                    "relation": "causal",
                    "from_storyline_id": "SL-A",
                    "from_state_index": 2,
                    "from_state": "repeat",
                    "to_storyline_id": "SL-B",
                    "to_state_index": 2,
                    "to_state": "b2",
                }
            },
            "anchors": anchors,
            "events": events,
            "edges": {"CE-AB": edge},
            "edge_pairs": {("EV-A1", "EV-B1")},
            "timing": {
                "TIME-AB": {
                    "id": "TIME-AB",
                    "event_ids": ["EV-A1", "EV-B1"],
                }
            },
            "timing_relations": {"TIME-AB": "convergence"},
        }

    @classmethod
    def _associative_case(cls) -> dict[str, object]:
        case = cls._causal_case()
        case["connections"]["SLC-AB"]["relation"] = "associative"
        case["realizations"][0].update(
            {
                "relation": "associative",
                "realization_kind": "associative_alignment",
                "causal_edge_ids": [],
            }
        )
        case["edges"] = {}
        case["edge_pairs"] = set()
        case["timing_relations"]["TIME-AB"] = "association"
        return case

    def _validate_case(self, case: dict[str, object]) -> None:
        t1._validate_connection_realizations(
            case["realizations"],
            case["connections"],
            case["anchors"],
            case["events"],
            case["edges"],
            case["edge_pairs"],
            case["timing"],
            case["timing_relations"],
        )

    @classmethod
    def _proposition_case(cls) -> dict[str, object]:
        anchors = cls._anchors()
        events = {
            "EV-A0": {
                "world_time": "[WT:000010]",
                "requires_proposition_ids": ["PROP-A0"],
                "produces_proposition_ids": ["PROP-A1", "PROP-SECRET"],
                "discloses_proposition_ids": [],
            },
            "EV-A1": {
                "world_time": "[WT:000020]",
                "requires_proposition_ids": ["PROP-A1"],
                "produces_proposition_ids": ["PROP-A2"],
                "discloses_proposition_ids": [],
            },
            "EV-B0": {
                "world_time": "[WT:000010]",
                "requires_proposition_ids": ["PROP-B0"],
                "produces_proposition_ids": ["PROP-B1"],
                "discloses_proposition_ids": [],
            },
            "EV-B1": {
                "world_time": "[WT:000030]",
                "requires_proposition_ids": [
                    "PROP-B1",
                    "PROP-A2",
                ],
                "produces_proposition_ids": ["PROP-B2"],
                "discloses_proposition_ids": ["PROP-SECRET"],
            },
        }
        obligation_specs = [
            ("SOB-CAUSE", "causes", [("SL-A", 2)], ("SL-B", 2), None, None),
            ("SOB-STRICT", "strict_before", [("SL-A", 1)], ("SL-B", 2), None, None),
            ("SOB-NOT-BEFORE", "not_before", [("SL-A", 1)], ("SL-B", 2), None, None),
            ("SOB-ALL", "requires_all", [("SL-A", 2), ("SL-B", 1)], ("SL-B", 2), None, None),
            ("SOB-FIRST", "first_disclosure", [("SL-A", 1)], ("SL-B", 2), "PROP-SECRET", "reader"),
            ("SOB-UNKNOWN", "must_remain_unknown", [], ("SL-B", 2), "PROP-HIDDEN", "reader"),
        ]

        def source_anchor(line_id: str, state_index: int) -> dict[str, object]:
            return {
                "storyline_id": line_id,
                "state_index": state_index,
                "state": anchors[(line_id, state_index)]["state"],
            }

        obligations = []
        realizations = []
        proposition_sources = {
            "PROP-A0": set(), "PROP-A1": set(), "PROP-A2": set(),
            "PROP-B0": set(), "PROP-B1": set(), "PROP-B2": set(),
            "PROP-SECRET": set(), "PROP-HIDDEN": set(),
        }
        anchor_props = {
            ("SL-A", 0): "PROP-A0", ("SL-A", 1): "PROP-A1",
            ("SL-A", 2): "PROP-A2", ("SL-B", 0): "PROP-B0",
            ("SL-B", 1): "PROP-B1", ("SL-B", 2): "PROP-B2",
        }
        for obligation_id, kind, antecedents, consequent, proposition_id, audience in obligation_specs:
            antecedent_anchors = [source_anchor(*item) for item in antecedents]
            consequent_anchor = source_anchor(*consequent)
            obligation = {
                "id": obligation_id,
                "kind": kind,
                "source_control_ids": ["CTRL-001"],
                "source_locators": [],
                "antecedent_anchors": antecedent_anchors,
                "consequent_anchor": consequent_anchor,
                "proposition_id": proposition_id,
                "audience": audience,
                "rationale": f"Exercise {kind}.",
                "acceptance_check": f"Validator recomputes {kind}.",
            }
            obligations.append(obligation)
            antecedent_props = [anchor_props[item] for item in antecedents]
            consequent_prop = proposition_id or anchor_props[consequent]
            for item in [*antecedent_props, consequent_prop]:
                proposition_sources[item].add(obligation_id)
            witness_events = list(dict.fromkeys(
                [anchors[item]["event_id"] for item in antecedents]
                + [anchors[consequent]["event_id"]]
            ))
            realizations.append({
                "id": f"OBR-{obligation_id[4:]}",
                "obligation_id": obligation_id,
                "kind": kind,
                "antecedent_proposition_ids": antecedent_props,
                "consequent_proposition_id": consequent_prop,
                "event_ids": witness_events,
                "evidence": f"Exact {kind} witnesses.",
            })
        proposition_sources["PROP-A0"].add("SL-A")
        proposition_sources["PROP-B0"].add("SL-B")
        propositions = []
        for proposition_id, sources in proposition_sources.items():
            propositions.append({
                "id": proposition_id,
                "statement": f"Truth represented by {proposition_id}.",
                "source_ids": sorted(sources),
                "audience": (
                    "reader" if proposition_id in {"PROP-SECRET", "PROP-HIDDEN"}
                    else None
                ),
                "initially_true": proposition_id in {"PROP-A0", "PROP-B0", "PROP-HIDDEN"},
                "terminality": (
                    "unique_terminal" if proposition_id in {"PROP-A2", "PROP-B2"}
                    else "ordinary"
                ),
            })
        model = {
            "proposition_registry": propositions,
            "obligation_realizations": realizations,
            "storyline_event_sequences": [
                {"storyline_id": "SL-A", "event_ids": ["EV-A0", "EV-A1"]},
                {"storyline_id": "SL-B", "event_ids": ["EV-B0", "EV-B1"]},
            ],
        }
        storyline = {"story_obligation_register": obligations}
        return {
            "model": model,
            "storyline": storyline,
            "events": events,
            "event_times": {
                item: t1._world_time(value["world_time"], item)
                for item, value in events.items()
            },
            "edge_pairs": {
                ("EV-A0", "EV-A1"),
                ("EV-B0", "EV-B1"),
                ("EV-A1", "EV-B1"),
            },
            "anchors": anchors,
        }

    @staticmethod
    def _validate_proposition_case(case: dict[str, object]) -> None:
        t1._validate_proposition_contract(
            case["model"],
            case["storyline"],
            case["events"],
            case["event_times"],
            case["edge_pairs"],
            case["anchors"],
        )

    @staticmethod
    def _append_atomic_obligation(
        case: dict[str, object],
        *,
        obligation_id: str,
        kind: str,
        antecedents: list[tuple[str, int]],
        consequent: tuple[str, int],
        proposition_id: str | None = None,
        audience: str | None = None,
        source_control_id: str = "CTRL-SHARED",
    ) -> None:
        anchors = case["anchors"]
        anchor_props = {
            ("SL-A", 0): "PROP-A0",
            ("SL-A", 1): "PROP-A1",
            ("SL-A", 2): "PROP-A2",
            ("SL-B", 0): "PROP-B0",
            ("SL-B", 1): "PROP-B1",
            ("SL-B", 2): "PROP-B2",
        }

        def state_ref(key: tuple[str, int]) -> dict[str, object]:
            return {
                "storyline_id": key[0],
                "state_index": key[1],
                "state": anchors[key]["state"],
            }

        consequent_prop = proposition_id or anchor_props[consequent]
        antecedent_props = [anchor_props[item] for item in antecedents]
        obligation = {
            "id": obligation_id,
            "kind": kind,
            "source_control_ids": [source_control_id],
            "source_claim_atom_ids": [f"SCA-{obligation_id[4:]}"],
            "source_locators": [],
            "antecedent_anchors": [state_ref(item) for item in antecedents],
            "consequent_anchor": state_ref(consequent),
            "proposition_id": proposition_id,
            "audience": audience,
            "rationale": f"Atomic obligation {obligation_id}.",
            "acceptance_check": f"Recompute {obligation_id} independently.",
        }
        case["storyline"]["story_obligation_register"].append(obligation)
        witness_events = list(
            dict.fromkeys(
                [anchors[item]["event_id"] for item in antecedents]
                + [anchors[consequent]["event_id"]]
            )
        )
        case["model"]["obligation_realizations"].append(
            {
                "id": f"OBR-{obligation_id[4:]}",
                "obligation_id": obligation_id,
                "kind": kind,
                "antecedent_proposition_ids": antecedent_props,
                "consequent_proposition_id": consequent_prop,
                "event_ids": witness_events,
                "evidence": f"Exact witnesses for {obligation_id}.",
            }
        )
        proposition_index = {
            item["id"]: item
            for item in case["model"]["proposition_registry"]
        }
        for item in [*antecedent_props, consequent_prop]:
            proposition_index[item]["source_ids"] = list(
                dict.fromkeys(
                    [*proposition_index[item]["source_ids"], obligation_id]
                )
            )
        consequent_event = anchors[consequent]["event_id"]
        if kind in {"causes", "requires_all"}:
            case["events"][consequent_event][
                "requires_proposition_ids"
            ].extend(antecedent_props)
            case["events"][consequent_event][
                "requires_proposition_ids"
            ] = list(
                dict.fromkeys(
                    case["events"][consequent_event][
                        "requires_proposition_ids"
                    ]
                )
            )
        if kind == "first_disclosure":
            case["events"][consequent_event][
                "discloses_proposition_ids"
            ].append(consequent_prop)
            case["events"][consequent_event][
                "discloses_proposition_ids"
            ] = list(
                dict.fromkeys(
                    case["events"][consequent_event][
                        "discloses_proposition_ids"
                    ]
                )
            )

    def test_proposition_and_all_six_obligation_kinds_pass(self) -> None:
        self._validate_proposition_case(self._proposition_case())

    def test_same_control_supports_two_atomic_chain_realizations(self) -> None:
        case = self._proposition_case()
        self._append_atomic_obligation(
            case,
            obligation_id="SOB-CHAIN-A-B",
            kind="causes",
            antecedents=[("SL-A", 1)],
            consequent=("SL-A", 2),
        )
        self._append_atomic_obligation(
            case,
            obligation_id="SOB-CHAIN-B-C",
            kind="causes",
            antecedents=[("SL-A", 2)],
            consequent=("SL-B", 2),
        )
        self._validate_proposition_case(case)

    def test_same_control_multibranch_requires_each_atomic_realization(self) -> None:
        case = self._proposition_case()
        self._append_atomic_obligation(
            case,
            obligation_id="SOB-BRANCH-LEFT",
            kind="causes",
            antecedents=[("SL-A", 1)],
            consequent=("SL-A", 2),
        )
        self._append_atomic_obligation(
            case,
            obligation_id="SOB-BRANCH-RIGHT",
            kind="causes",
            antecedents=[("SL-A", 1)],
            consequent=("SL-B", 2),
        )
        self._validate_proposition_case(case)
        case["model"]["obligation_realizations"] = [
            item
            for item in case["model"]["obligation_realizations"]
            if item["obligation_id"] != "SOB-BRANCH-RIGHT"
        ]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_OBLIGATION_REALIZATION_MISMATCH"
        ):
            self._validate_proposition_case(case)

    def test_first_disclosure_and_unknown_cutoff_share_one_control(self) -> None:
        case = self._proposition_case()
        first = next(
            item
            for item in case["storyline"]["story_obligation_register"]
            if item["id"] == "SOB-FIRST"
        )
        first["source_control_ids"] = ["CTRL-DISCLOSURE"]
        first["source_claim_atom_ids"] = ["SCA-DISCLOSURE-WINDOW"]
        self._append_atomic_obligation(
            case,
            obligation_id="SOB-SECRET-UNKNOWN-UNTIL-B",
            kind="must_remain_unknown",
            antecedents=[],
            consequent=("SL-B", 1),
            proposition_id="PROP-SECRET",
            audience="reader",
            source_control_id="CTRL-DISCLOSURE",
        )
        self._validate_proposition_case(case)

        unknown = next(
            item
            for item in case["storyline"]["story_obligation_register"]
            if item["id"] == "SOB-SECRET-UNKNOWN-UNTIL-B"
        )
        unknown["consequent_anchor"] = {
            "storyline_id": "SL-B",
            "state_index": 2,
            "state": case["anchors"][("SL-B", 2)]["state"],
        }
        realization = next(
            item
            for item in case["model"]["obligation_realizations"]
            if item["obligation_id"] == "SOB-SECRET-UNKNOWN-UNTIL-B"
        )
        realization["event_ids"] = ["EV-B1"]
        with self.assertRaisesRegex(t1.T1Error, "T1_PREMATURE_DISCLOSURE"):
            self._validate_proposition_case(case)

    def test_proposition_contract_recomputes_hard_semantics(self) -> None:
        attacks = []

        unreachable = self._proposition_case()
        unreachable["edge_pairs"].remove(("EV-A1", "EV-B1"))
        attacks.append((unreachable, "T1_REQUIRED_PROPOSITION_UNREACHABLE"))

        strict = self._proposition_case()
        strict_obligation = next(
            item for item in strict["storyline"]["story_obligation_register"]
            if item["id"] == "SOB-STRICT"
        )
        strict_obligation["consequent_anchor"] = {
            "storyline_id": "SL-B",
            "state_index": 1,
            "state": strict["anchors"][("SL-B", 1)]["state"],
        }
        strict_realization = next(
            item for item in strict["model"]["obligation_realizations"]
            if item["obligation_id"] == "SOB-STRICT"
        )
        strict_realization["consequent_proposition_id"] = "PROP-B1"
        strict_realization["event_ids"] = ["EV-A0", "EV-B0"]
        next(
            item for item in strict["model"]["proposition_registry"]
            if item["id"] == "PROP-B1"
        )["source_ids"].append("SOB-STRICT")
        attacks.append((strict, "T1_STRICT_BEFORE_VIOLATION"))

        missing_all = self._proposition_case()
        missing_all["events"]["EV-B1"]["requires_proposition_ids"].remove("PROP-B1")
        attacks.append((missing_all, "T1_REQUIRES_ALL_VIOLATION"))

        early = self._proposition_case()
        early["events"]["EV-A0"]["discloses_proposition_ids"].append("PROP-SECRET")
        attacks.append((early, "T1_FIRST_DISCLOSURE_VIOLATION"))

        unknown = self._proposition_case()
        unknown["events"]["EV-B0"]["discloses_proposition_ids"].append("PROP-HIDDEN")
        attacks.append((unknown, "T1_PREMATURE_DISCLOSURE"))

        terminal = self._proposition_case()
        terminal["events"]["EV-B0"]["produces_proposition_ids"].append("PROP-B2")
        attacks.append((terminal, "T1_UNIQUE_TERMINAL_VIOLATION"))

        duplicate_statement = self._proposition_case()
        duplicate_statement["model"]["proposition_registry"][1]["statement"] = (
            duplicate_statement["model"]["proposition_registry"][0]["statement"]
        )
        attacks.append((duplicate_statement, "T1_PROPOSITION_STATEMENT_DUPLICATE"))

        missing_line_terminal = self._proposition_case()
        next(
            item
            for item in missing_line_terminal["model"]["proposition_registry"]
            if item["id"] == "PROP-A2"
        )["terminality"] = "ordinary"
        attacks.append((
            missing_line_terminal,
            "T1_STORYLINE_TERMINAL_PROPOSITION_MISSING",
        ))

        missing_realization = self._proposition_case()
        missing_realization["model"]["obligation_realizations"].pop()
        attacks.append((missing_realization, "T1_OBLIGATION_REALIZATION_MISMATCH"))

        for case, code in attacks:
            with self.subTest(code=code), self.assertRaisesRegex(t1.T1Error, code):
                self._validate_proposition_case(case)

    def test_state_anchor_index_contract_is_exact(self) -> None:
        two = t1._state_anchors_for_line(
            "SL-TWO",
            ["same", "same"],
            [{"trigger_ids": ["EV-TWO"]}],
        )
        self.assertEqual(
            ("EV-TWO", 0, "same", "before"),
            tuple(
                two[("SL-TWO", 0)][field]
                for field in ("event_id", "state_index", "state", "side")
            ),
        )
        self.assertEqual(
            ("EV-TWO", 1, "same", "after"),
            tuple(
                two[("SL-TWO", 1)][field]
                for field in ("event_id", "state_index", "state", "side")
            ),
        )
        multi = self._anchors()
        self.assertEqual("EV-A0", multi[("SL-A", 0)]["event_id"])
        self.assertEqual("EV-A0", multi[("SL-A", 1)]["event_id"])
        self.assertEqual("EV-A1", multi[("SL-A", 2)]["event_id"])
        self.assertNotEqual(
            multi[("SL-A", 0)],
            multi[("SL-A", 2)],
        )

    def test_responsibility_progression_and_terminal_event(self) -> None:
        event_ids = [f"EV-LONG-{index:02d}" for index in range(1, 11)]
        roles = {
            event_ids[0]: ["background", "setup"],
            event_ids[1]: ["setup"],
            event_ids[2]: ["trigger"],
            event_ids[3]: ["trigger"],
            event_ids[4]: ["development"],
            event_ids[5]: ["development"],
            event_ids[6]: ["turn_or_crisis"],
            event_ids[7]: ["turn_or_crisis"],
            event_ids[8]: ["result"],
            event_ids[9]: ["result", "aftermath"],
        }
        t1._validate_storyline_responsibility_progression(
            "SL-LONG", event_ids, roles
        )
        broken = copy.deepcopy(roles)
        broken[event_ids[9]] = ["result", "setup", "aftermath"]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_STORYLINE_CHAIN_INCOMPLETE"
        ):
            t1._validate_storyline_responsibility_progression(
                "SL-LONG", event_ids, broken
            )
        ledgers = [
            {"trigger_ids": [event_ids[2]]},
            {"trigger_ids": [event_ids[-1]]},
        ]
        t1._validate_terminal_state_event(
            "SL-LONG", "main", ledgers, event_ids
        )
        with self.assertRaisesRegex(
            t1.T1Error,
            "T1_STORYLINE_TERMINAL_STATE_EVENT_MISMATCH",
        ):
            t1._validate_terminal_state_event(
                "SL-LONG",
                "main",
                ledgers[:-1],
                event_ids,
            )
        t1._validate_terminal_state_event(
            "SL-LONG",
            "optional_melody",
            ledgers[:-1],
            event_ids,
        )

    @staticmethod
    def _terminal_send_tail_case() -> dict[str, object]:
        line_id = "SL-SOURCE"

        def event(
            event_id: str,
            *,
            kind: str,
            subject_id: str,
            subject_kind: str,
            storyline_ids: list[str],
            step_ids: list[str],
        ) -> dict[str, object]:
            return {
                "id": event_id,
                "event_kind": kind,
                "subject_id": subject_id,
                "subject_kind": subject_kind,
                "storyline_ids": storyline_ids,
                "e1_capability_step_ids": step_ids,
                "lifecycle_effects": [],
                "world_time": "[WT:000100]",
            }

        events = {
            "EV-PRE": event(
                "EV-PRE",
                kind="process",
                subject_id="PSS-PRE",
                subject_kind="process",
                storyline_ids=[line_id],
                step_ids=["CSTEP-PRE"],
            ),
            "EV-END": event(
                "EV-END",
                kind="story_transition",
                subject_id=line_id,
                subject_kind="state",
                storyline_ids=[line_id],
                step_ids=["CSTEP-END"],
            ),
            **{
                f"EV-SEND-{index}": event(
                    f"EV-SEND-{index}",
                    kind="connection_bridge",
                    subject_id=f"RF-SEND-{index}",
                    subject_kind="resource",
                    storyline_ids=[line_id],
                    step_ids=[f"CSTEP-SEND-{index}"],
                )
                for index in range(1, 5)
            },
            **{
                f"EV-TARGET-{index}": event(
                    f"EV-TARGET-{index}",
                    kind="story_transition",
                    subject_id=f"SL-TARGET-{index}",
                    subject_kind="state",
                    storyline_ids=[f"SL-TARGET-{index}"],
                    step_ids=[f"CSTEP-TARGET-{index}"],
                )
                for index in range(1, 4)
            },
        }
        connections = {
            "SLC-ONE": {
                "id": "SLC-ONE",
                "relation": "causal",
                "from_storyline_id": line_id,
                "from_state_index": 1,
            },
            "SLC-TWO": {
                "id": "SLC-TWO",
                "relation": "causal",
                "from_storyline_id": line_id,
                "from_state_index": 1,
            },
            "SLC-THREE": {
                "id": "SLC-THREE",
                "relation": "causal",
                "from_storyline_id": line_id,
                "from_state_index": 1,
            },
        }
        paths = [
            {
                "connection_id": "SLC-ONE",
                "relation": "causal",
                "source_event_id": "EV-END",
                "target_event_id": "EV-TARGET-1",
                "bridge_event_ids": ["EV-SEND-1", "EV-SEND-2"],
                "predecessor_path_event_ids": [
                    "EV-END",
                    "EV-SEND-1",
                    "EV-SEND-2",
                    "EV-TARGET-1",
                ],
            },
            {
                "connection_id": "SLC-TWO",
                "relation": "causal",
                "source_event_id": "EV-END",
                "target_event_id": "EV-TARGET-2",
                "bridge_event_ids": ["EV-SEND-3"],
                "predecessor_path_event_ids": [
                    "EV-END", "EV-SEND-3", "EV-TARGET-2"
                ],
            },
            {
                "connection_id": "SLC-THREE",
                "relation": "causal",
                "source_event_id": "EV-END",
                "target_event_id": "EV-TARGET-3",
                "bridge_event_ids": ["EV-SEND-4"],
                "predecessor_path_event_ids": [
                    "EV-END", "EV-SEND-4", "EV-TARGET-3"
                ],
            },
        ]
        readiness = [
            {
                "connection_id": "SLC-ONE",
                "relation": "causal",
                "transport_step_ids": ["CSTEP-SEND-1", "CSTEP-SEND-2"],
            },
            {
                "connection_id": "SLC-TWO",
                "relation": "causal",
                "transport_step_ids": ["CSTEP-SEND-3"],
            },
            {
                "connection_id": "SLC-THREE",
                "relation": "causal",
                "transport_step_ids": ["CSTEP-SEND-4"],
            },
        ]
        edge_pairs = {
            (left, right)
            for path in paths
            for left, right in zip(
                path["predecessor_path_event_ids"],
                path["predecessor_path_event_ids"][1:],
            )
        } | {
            ("EV-SEND-2", "EV-SEND-3"),
            ("EV-SEND-3", "EV-SEND-4"),
        }
        return {
            "line_id": line_id,
            "line_type": "main",
            "transition_ledgers": [{"trigger_ids": ["EV-END"]}],
            "event_ids": [
                "EV-PRE",
                "EV-END",
                "EV-SEND-1",
                "EV-SEND-2",
                "EV-SEND-3",
                "EV-SEND-4",
            ],
            "current_schema": True,
            "transition_spans": [["EV-PRE", "EV-END"]],
            "events": events,
            "connections": connections,
            "connection_event_paths": paths,
            "connection_path_readiness": readiness,
            "edge_pairs": edge_pairs,
        }

    def test_terminal_send_tail_accepts_four_bridges_multihop_and_same_tick(
        self,
    ) -> None:
        case = self._terminal_send_tail_case()
        self.assertEqual(
            {"[WT:000100]"},
            {
                case["events"][event_id]["world_time"]
                for event_id in case["event_ids"]
                if event_id.startswith("EV-SEND-")
            },
        )
        t1._validate_terminal_state_event(**case)

    def test_terminal_send_tail_rejects_closed_boundary_attacks(self) -> None:
        attacks = []

        post_state = self._terminal_send_tail_case()
        post_state["events"]["EV-SEND-1"]["subject_id"] = "SL-SOURCE"
        attacks.append((post_state, "T1_POST_TERMINAL_STATE_CHANGE"))

        lifecycle = self._terminal_send_tail_case()
        lifecycle["events"]["EV-SEND-1"]["lifecycle_effects"] = [
            {"transition_kind": "shutdown"}
        ]
        attacks.append((lifecycle, "T1_POST_TERMINAL_STATE_CHANGE"))

        nonbridge = self._terminal_send_tail_case()
        nonbridge["events"]["EV-SEND-1"]["event_kind"] = "process"
        attacks.append((nonbridge, "T1_POST_TERMINAL_STATE_CHANGE"))

        wrong_readiness = self._terminal_send_tail_case()
        wrong_readiness["connection_path_readiness"][0][
            "transport_step_ids"
        ] = ["CSTEP-SEND-1"]
        attacks.append(
            (
                wrong_readiness,
                "T1_POST_TERMINAL_CONNECTION_READINESS_MISMATCH",
            )
        )

        duplicate_transport = self._terminal_send_tail_case()
        duplicate_transport["events"]["EV-SEND-2"][
            "e1_capability_step_ids"
        ] = ["CSTEP-SEND-1"]
        duplicate_transport["connection_path_readiness"][0][
            "transport_step_ids"
        ] = ["CSTEP-SEND-1"]
        attacks.append(
            (
                duplicate_transport,
                "T1_POST_TERMINAL_CONNECTION_READINESS_MISMATCH",
            )
        )

        wrong_line = self._terminal_send_tail_case()
        wrong_line["events"]["EV-SEND-1"]["storyline_ids"] = [
            "SL-TARGET-1"
        ]
        attacks.append(
            (wrong_line, "T1_POST_TERMINAL_CONNECTION_PATH_INVALID")
        )

        wrong_connection_line = self._terminal_send_tail_case()
        wrong_connection_line["connections"]["SLC-ONE"][
            "from_storyline_id"
        ] = "SL-FOREIGN"
        attacks.append(
            (wrong_connection_line, "T1_POST_TERMINAL_EVENT_INVALID")
        )

        bridge_before_anchor = self._terminal_send_tail_case()
        bridge_before_anchor["event_ids"] = [
            "EV-PRE",
            "EV-SEND-1",
            "EV-END",
            "EV-SEND-2",
            "EV-SEND-3",
            "EV-SEND-4",
        ]
        attacks.append((bridge_before_anchor, "T1_POST_TERMINAL_EVENT_INVALID"))

        bridge_after_target = self._terminal_send_tail_case()
        bridge_after_target["connection_event_paths"][0][
            "predecessor_path_event_ids"
        ] = ["EV-END", "EV-SEND-1", "EV-TARGET-1", "EV-SEND-2"]
        attacks.append(
            (
                bridge_after_target,
                "T1_POST_TERMINAL_CONNECTION_PATH_INVALID",
            )
        )

        bypass = self._terminal_send_tail_case()
        bypass["connection_event_paths"][0][
            "predecessor_path_event_ids"
        ] = ["EV-END", "EV-TARGET-1"]
        attacks.append((bypass, "T1_POST_TERMINAL_CONNECTION_PATH_INVALID"))

        trailing_action = self._terminal_send_tail_case()
        trailing_action["events"]["EV-TRAIL"] = copy.deepcopy(
            trailing_action["events"]["EV-PRE"]
        )
        trailing_action["events"]["EV-TRAIL"]["id"] = "EV-TRAIL"
        trailing_action["event_ids"].append("EV-TRAIL")
        attacks.append((trailing_action, "T1_POST_TERMINAL_EVENT_INVALID"))

        duplicate = self._terminal_send_tail_case()
        duplicate["event_ids"].append("EV-SEND-1")
        attacks.append((duplicate, "T1_POST_TERMINAL_EVENT_DUPLICATE"))

        for case, code in attacks:
            with self.subTest(code=code), self.assertRaisesRegex(
                t1.T1Error, code
            ):
                t1._validate_terminal_state_event(**case)

    def test_terminal_send_tail_preserves_empty_optional_and_legacy_rules(
        self,
    ) -> None:
        case = self._terminal_send_tail_case()
        case["event_ids"] = ["EV-PRE", "EV-END"]
        t1._validate_terminal_state_event(**case)
        t1._validate_terminal_state_event(
            "SL-OPTIONAL", "optional_melody", [], []
        )
        with self.assertRaisesRegex(
            t1.T1Error, "T1_STORYLINE_TERMINAL_STATE_EVENT_MISMATCH"
        ):
            t1._validate_terminal_state_event(
                "SL-LEGACY",
                "main",
                [{"trigger_ids": ["EV-END"]}],
                ["EV-END", "EV-TRAIL"],
            )

    def test_causal_connection_happy_path(self) -> None:
        self._validate_case(self._causal_case())

    def test_connection_realization_schema_branches_are_hard(self) -> None:
        from jsonschema import Draft202012Validator

        contract = json.loads(
            Path(
                "docs/ai-novel-workflow/contracts/autonomous-v2/"
                "event-timeline.schema.json"
            ).read_text(encoding="utf-8")
        )
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": "#/$defs/connectionRealization",
            "$defs": contract["$defs"],
        }
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        causal = self._causal_case()["realizations"][0]
        self.assertFalse(list(validator.iter_errors(causal)))
        causal["causal_edge_ids"] = []
        self.assertTrue(list(validator.iter_errors(causal)))
        associative = self._associative_case()["realizations"][0]
        self.assertFalse(list(validator.iter_errors(associative)))
        associative["causal_edge_ids"] = ["CE-AB"]
        self.assertTrue(list(validator.iter_errors(associative)))

    def test_relation_and_anchor_attacks(self) -> None:
        relation = self._causal_case()
        relation["realizations"][0]["relation"] = "associative"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_RELATION_MISMATCH"
        ):
            self._validate_case(relation)
        for field, value in (
            ("event_id", "EV-A0"),
            ("state_index", 1),
            ("side", "before"),
        ):
            case = self._causal_case()
            case["realizations"][0]["source_anchor"][field] = value
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(
                    t1.T1Error,
                    "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH",
                ),
            ):
                self._validate_case(case)
        target = self._causal_case()
        target["realizations"][0]["target_anchor"]["event_id"] = "EV-B0"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_TARGET_ANCHOR_MISMATCH"
        ):
            self._validate_case(target)

    def test_causal_edge_path_and_timing_attacks(self) -> None:
        missing = self._causal_case()
        missing["realizations"][0]["causal_edge_ids"] = []
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_CAUSAL_PATH_MISMATCH"
        ):
            self._validate_case(missing)
        dangling = self._causal_case()
        dangling["realizations"][0]["causal_edge_ids"] = ["CE-MISSING"]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_CAUSAL_EDGE_MISMATCH"
        ):
            self._validate_case(dangling)
        wrong_path = self._causal_case()
        wrong_path["edges"]["CE-WRONG"] = {
            "id": "CE-WRONG",
            "from_event_id": "EV-A0",
            "to_event_id": "EV-B1",
        }
        wrong_path["edge_pairs"].add(("EV-A0", "EV-B1"))
        wrong_path["realizations"][0]["causal_edge_ids"] = ["CE-WRONG"]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_CAUSAL_PATH_MISMATCH"
        ):
            self._validate_case(wrong_path)
        for mutation in ("missing", "relation", "anchor"):
            case = self._causal_case()
            if mutation == "missing":
                case["realizations"][0]["timing_constraint_ids"] = []
            elif mutation == "relation":
                case["timing_relations"]["TIME-AB"] = "association"
            else:
                case["timing"]["TIME-AB"]["event_ids"] = ["EV-A1"]
            with (
                self.subTest(timing=mutation),
                self.assertRaisesRegex(
                    t1.T1Error, "T1_CONNECTION_TIMING_MISMATCH"
                ),
            ):
                self._validate_case(case)

    def test_associative_contract_and_dag_attacks(self) -> None:
        self._validate_case(self._associative_case())
        claimed = self._associative_case()
        claimed["realizations"][0]["causal_edge_ids"] = ["CE-AB"]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_ASSOCIATIVE_CAUSAL_CLAIM"
        ):
            self._validate_case(claimed)
        predecessor = self._associative_case()
        predecessor["edge_pairs"].add(("EV-A1", "EV-B1"))
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_ASSOCIATIVE_PREDECESSOR"
        ):
            self._validate_case(predecessor)
        indirect = self._associative_case()
        indirect["events"]["EV-X"] = {"storyline_ids": ["SL-A"]}
        indirect["edge_pairs"].update(
            {("EV-A1", "EV-X"), ("EV-X", "EV-B1")}
        )
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_ASSOCIATIVE_PREDECESSOR"
        ):
            self._validate_case(indirect)
        timing = self._associative_case()
        timing["timing_relations"]["TIME-AB"] = "convergence"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_TIMING_MISMATCH"
        ):
            self._validate_case(timing)

    def test_cross_line_edges_have_exactly_one_owner(self) -> None:
        unowned = self._causal_case()
        unowned["edges"]["CE-HIDDEN"] = {
            "id": "CE-HIDDEN",
            "from_event_id": "EV-A0",
            "to_event_id": "EV-B0",
        }
        unowned["edge_pairs"].add(("EV-A0", "EV-B0"))
        with self.assertRaisesRegex(
            t1.T1Error,
            "T1_CROSS_LINE_CAUSAL_EDGE_OWNERSHIP_MISMATCH",
        ):
            self._validate_case(unowned)
        missing = self._causal_case()
        missing["realizations"] = []
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_REALIZATION_MISMATCH"
        ):
            self._validate_case(missing)


class HistoricalPackageCompatibilityTests(unittest.TestCase):
    package = (
        Path(__file__).resolve().parents[3]
        / "projects"
        / "duanxian"
        / "conception-runs"
        / "duanxian-conception-v2-20260803-04"
        / "T1"
    )

    @unittest.skipUnless(package.is_dir(), "historical 2.0 package unavailable")
    def test_trusted_historical_2_0_package_remains_read_only_valid(self) -> None:
        self.assertEqual("ready", t1.validate_t1_package(self.package)["verdict"])

    def test_2_1_inventory_is_explicitly_empty_and_generation_is_forbidden(self) -> None:
        self.assertEqual(frozenset(), t1._TRUSTED_LEGACY_IMPLEMENTATION_PAIRS["2.1"])
        self.assertEqual(frozenset(), t1._TRUSTED_LEGACY_PACKAGE_IDENTITIES["2.1"])
        with self.assertRaisesRegex(t1.T1Error, "T1_LEGACY_GENERATION_FORBIDDEN"):
            t1._require_generation_schema({"schema_version": "2.1"})

    @staticmethod
    def _trusted_2_3_catalog() -> dict[str, dict[str, str]]:
        binding_sets = t1._TRUSTED_LEGACY_IMPLEMENTATION_BINDING_SETS["2.3"]
        bindings = next(iter(binding_sets))
        return {
            identity: {"path": f"implementation/{identity}", "sha256": sha256}
            for identity, sha256 in bindings
        }

    def test_2_3_exact_full_implementation_snapshot_is_trusted(self) -> None:
        expected_pair = (
            "21c94ef28a13a5273772dd1bf48ffdb5bd9aa852504960d478180663d1d9c45f",
            "4c0074e9e19eb57a717d03527f7dcd23e36185e632cb6e5966b58c19b8cae8b8",
        )
        self.assertEqual(
            frozenset({expected_pair}),
            t1._TRUSTED_LEGACY_IMPLEMENTATION_PAIRS["2.3"],
        )
        catalog = self._trusted_2_3_catalog()
        self.assertEqual(27, len(catalog))
        self.assertEqual(
            "f51992278650876b36d28eb7de0b3874563748c75b90c3ec2733874442c55ba3",
            catalog["skill/runtime-contract.md"]["sha256"],
        )
        t1._validate_legacy_package_provenance(
            {"schema_version": "2.3"}, catalog
        )

    def test_2_3_tampered_or_incomplete_implementation_snapshot_is_rejected(self) -> None:
        for mutation in ("tampered", "missing"):
            with self.subTest(mutation=mutation):
                catalog = self._trusted_2_3_catalog()
                if mutation == "tampered":
                    catalog["skill/runtime-contract.md"]["sha256"] = "0" * 64
                else:
                    catalog.pop("upstream/W1-runtime-contract.md")
                with self.assertRaisesRegex(
                    t1.T1Error, "T1_LEGACY_PROVENANCE_UNTRUSTED"
                ):
                    t1._validate_legacy_package_provenance(
                        {"schema_version": "2.3"}, catalog
                    )

    def test_2_3_has_no_released_package_identity_and_replay_stays_closed(self) -> None:
        self.assertEqual(
            frozenset(), t1._TRUSTED_LEGACY_PACKAGE_IDENTITIES["2.3"]
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "package-manifest.json",
                "stage-completion.json",
                "event-timeline.json",
            ):
                (root / name).write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                t1.T1Error, "T1_LEGACY_PACKAGE_IDENTITY_UNTRUSTED"
            ):
                t1._validate_trusted_legacy_model_schema(
                    root,
                    {"schema_version": "2.3"},
                    self._trusted_2_3_catalog(),
                )

    def test_2_2_policy_and_current_2_5_profile_are_unchanged(self) -> None:
        self.assertEqual(
            frozenset(
                {
                    (
                        "39b8d29b1860476e0e4653a35716a76ce5ddf9d5ec006a5c6f92b0935fe98487",
                        "6aa9eebadb677b7054b521bc54a47f554783c0064759617d505f75fd82956dc2",
                    )
                }
            ),
            t1._TRUSTED_LEGACY_IMPLEMENTATION_PAIRS["2.2"],
        )
        self.assertEqual(
            frozenset(), t1._TRUSTED_LEGACY_PACKAGE_IDENTITIES["2.2"]
        )
        self.assertNotIn("2.2", t1._TRUSTED_LEGACY_IMPLEMENTATION_BINDING_SETS)
        self.assertEqual("2.5", t1.CURRENT_MODEL_SCHEMA_VERSION)
        self.assertEqual(
            "t1-initial-event-plan-semantics-v5", t1.T1_PLAN_REVIEW_PROTOCOL
        )
        self.assertEqual(
            frozenset(), t1._TRUSTED_LEGACY_PACKAGE_IDENTITIES["2.4"]
        )
        self.assertEqual(
            frozenset(), t1._TRUSTED_LEGACY_IMPLEMENTATION_PAIRS["2.4"]
        )
        self.assertNotIn("2.5", t1._TRUSTED_LEGACY_IMPLEMENTATION_PAIRS)

    @unittest.skipUnless(package.is_dir(), "historical 2.0 package unavailable")
    def test_preserved_old_implementation_cannot_authorize_resealed_2_0(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mutant = Path(directory) / "T1"
            shutil.copytree(self.package, mutant)
            model_path = mutant / "event-timeline.json"
            model = json.loads(model_path.read_text(encoding="utf-8"))
            model["run_id"] += "-resealed"
            model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
            manifest_path = mutant / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            replacement = runtime.artifact_reference(model_path, root=mutant)
            manifest["files"] = [
                replacement if item["path"] == "event-timeline.json" else item
                for item in manifest["files"]
            ]
            manifest["artifact_roles"]["canonical"] = replacement
            manifest_path.write_text(runtime.canonical_json(manifest), encoding="utf-8")
            completion_path = mutant / "stage-completion.json"
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
            completion_path.write_text(
                runtime.canonical_json(completion), encoding="utf-8"
            )
            with self.assertRaises(t1.T1Error) as caught:
                t1.validate_t1_package(mutant)
            self.assertEqual(
                "T1_LEGACY_PACKAGE_IDENTITY_UNTRUSTED", caught.exception.code
            )


class RebuiltUpstreamCompletionPathTests(unittest.TestCase):
    class _SchemaRuntime:
        @staticmethod
        def validate(value, schema_name):
            return None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = self._SchemaRuntime()
        self.run_id = "run-t1-rebuilt-upstream-paths"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _package(
        self,
        stage: str,
        logical_root: str,
        previous: list[dict[str, str]],
    ) -> tuple[Path, dict[str, str]]:
        root = self.root / f"physical-{stage}"
        root.mkdir()
        manifest = {"stage": stage, "kind": "manifest"}
        validation = {"stage": stage, "verdict": "ready"}
        (root / "package-manifest.json").write_text(
            runtime.canonical_json(manifest), encoding="utf-8"
        )
        (root / "validation.json").write_text(
            runtime.canonical_json(validation), encoding="utf-8"
        )
        completion = {
            "schema_version": "2.0",
            "run_id": self.run_id,
            "stage": stage,
            "status": "ready",
            "manifest": {
                "path": f"{logical_root}/package-manifest.json",
                "sha256": runtime.sha256_file(root / "package-manifest.json"),
            },
            "validation": {
                "path": f"{logical_root}/validation.json",
                "sha256": runtime.sha256_file(root / "validation.json"),
            },
            "previous_stage_completions": copy.deepcopy(previous),
        }
        (root / "stage-completion.json").write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        reference = {
            "stage": stage,
            "path": f"{logical_root}/stage-completion.json",
            "sha256": runtime.sha256_file(root / "stage-completion.json"),
        }
        return root, reference

    def test_gate_selected_rebuilt_attempt_paths_are_authoritative(self) -> None:
        b0_root, b0_ref = self._package(
            "B0", "workspaces/B0-attempt-01/package", []
        )
        s1_root, s1_ref = self._package(
            "S1", "workspaces/S1-attempt-03/package", []
        )
        w1_root, w1_ref = self._package(
            "W1", "workspaces/W1-attempt-04/package", [s1_ref]
        )
        e1_root, e1_ref = self._package(
            "E1", "workspaces/E1-attempt-11/package", [s1_ref, w1_ref]
        )
        before = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        cases = (
            (b0_root, b0_ref, "B0", []),
            (s1_root, s1_ref, "S1", []),
            (w1_root, w1_ref, "W1", [s1_ref]),
            (e1_root, e1_ref, "E1", [s1_ref, w1_ref]),
        )
        for package_root, reference, stage, previous in cases:
            physical_root = package_root
            if os.name == "nt" and stage in {"W1", "E1"}:
                physical_root = Path("\\\\?\\" + str(package_root.resolve()))
            with self.subTest(stage=stage):
                self.assertEqual(
                    reference,
                    t1._sealed_upstream_reference(
                        physical_root,
                        reference,
                        stage=stage,
                        run_id=self.run_id,
                        previous_stage_completions=previous,
                        runtime=self.runtime,
                    ),
                )
        after = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_foreign_stale_tampered_and_previous_chain_fail_closed(self) -> None:
        s1_root, s1_ref = self._package(
            "S1", "workspaces/S1-attempt-03/package", []
        )
        before = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        foreign = copy.deepcopy(s1_ref)
        foreign["path"] = "foreign/S1/stage-completion.json"
        stale = copy.deepcopy(s1_ref)
        stale["sha256"] = "0" * 64
        for name, reference, previous in (
            ("foreign", foreign, []),
            ("stale", stale, []),
            ("previous-chain", s1_ref, [s1_ref]),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                t1.T1Error, "T1_S1_INVALID"
            ):
                t1._sealed_upstream_reference(
                    s1_root,
                    reference,
                    stage="S1",
                    run_id=self.run_id,
                    previous_stage_completions=previous,
                    runtime=self.runtime,
                )
        completion_path = s1_root / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["run_id"] = "foreign-run"
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        with self.assertRaisesRegex(t1.T1Error, "T1_S1_INVALID"):
            t1._sealed_upstream_reference(
                s1_root,
                s1_ref,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.runtime,
            )
        after = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def _start_fixture(
        self, name: str
    ) -> tuple[dict[str, Path], dict[str, object]]:
        fixture = self.root / name
        fixture.mkdir()
        logical_roots = {
            "B0": "workspaces/B0-attempt-01/package",
            "S1": "workspaces/S1-attempt-03/package",
            "W1": "workspaces/W1-attempt-04/package",
            "E1": "workspaces/E1-attempt-11/package",
        }
        roots: dict[str, Path] = {}
        references: dict[str, dict[str, str]] = {}
        for stage in ("B0", "S1", "W1", "E1"):
            root = fixture / f"physical-{stage}"
            root.mkdir()
            roots[stage] = root
            manifest = {"stage": stage, "kind": "manifest"}
            validation = {"stage": stage, "verdict": "ready"}
            (root / "package-manifest.json").write_text(
                runtime.canonical_json(manifest), encoding="utf-8"
            )
            (root / "validation.json").write_text(
                runtime.canonical_json(validation), encoding="utf-8"
            )
            previous = (
                []
                if stage in {"B0", "S1"}
                else [references["S1"]]
                if stage == "W1"
                else [references["S1"], references["W1"]]
            )
            completion = {
                "schema_version": "2.0",
                "run_id": self.run_id,
                "stage": stage,
                "status": "ready",
                "manifest": {
                    "path": f"{logical_roots[stage]}/package-manifest.json",
                    "sha256": runtime.sha256_file(root / "package-manifest.json"),
                },
                "validation": {
                    "path": f"{logical_roots[stage]}/validation.json",
                    "sha256": runtime.sha256_file(root / "validation.json"),
                },
                "previous_stage_completions": copy.deepcopy(previous),
            }
            (root / "stage-completion.json").write_text(
                runtime.canonical_json(completion), encoding="utf-8"
            )
            references[stage] = {
                "stage": stage,
                "path": f"{logical_roots[stage]}/stage-completion.json",
                "sha256": runtime.sha256_file(root / "stage-completion.json"),
            }
        canonical = {
            "B0": ("author-control-baseline.json", {"run_id": self.run_id}),
            "S1": ("storyline-architecture.json", {"run_id": self.run_id}),
            "W1": ("world-model.json", {"run_id": self.run_id}),
            "E1": (
                "environment-system.json",
                {
                    "run_id": self.run_id,
                    "schema_version": e1.CURRENT_MODEL_SCHEMA_VERSION,
                },
            ),
        }
        for stage, (filename, value) in canonical.items():
            (roots[stage] / filename).write_text(
                runtime.canonical_json(value), encoding="utf-8"
            )
        for owner, stages in (
            ("S1", ("B0",)),
            ("W1", ("B0", "S1")),
            ("E1", ("B0", "S1", "W1")),
        ):
            for stage in stages:
                target = roots[owner] / "sources" / stage / "stage-completion.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(roots[stage] / "stage-completion.json", target)
        gate_data = {
            "target_stage": "T1",
            "run_id": self.run_id,
            "baseline_completion": copy.deepcopy(references["B0"]),
            "upstream_completions": [
                copy.deepcopy(references[stage]) for stage in ("S1", "W1", "E1")
            ],
        }
        return roots, gate_data

    def _assert_start_fails_before_write(
        self,
        roots: dict[str, Path],
        gate_data: dict[str, object],
        workspace: Path,
        expected_code: str,
    ) -> None:
        gate = mock.Mock(
            data=gate_data,
            reference={
                "path": "T1/input-gate.json",
                "sha256": runtime.canonical_sha256(gate_data),
            },
        )
        with (
            mock.patch.object(t1.rt, "validate_baseline_package"),
            mock.patch.object(t1.s1_runtime, "validate_s1_package"),
            mock.patch.object(t1.w1_runtime, "validate_w1_package"),
            mock.patch.object(t1.e1_runtime, "validate_e1_package"),
            mock.patch.dict(
                os.environ,
                {"CODEX_THREAD_ID": "thread-t1-upstream-attack"},
                clear=False,
            ),
            self.assertRaisesRegex(t1.T1Error, expected_code),
        ):
            t1.start_t1_session(
                workspace,
                baseline_package=roots["B0"],
                storyline_package=roots["S1"],
                world_package=roots["W1"],
                environment_package=roots["E1"],
                input_gate=gate,
                runtime=self.runtime,
            )
        self.assertFalse(workspace.exists())

    def test_start_rejects_gate_completion_attacks_before_write(self) -> None:
        roots, gate = self._start_fixture("foreign")
        gate["upstream_completions"][2]["path"] = (
            "foreign/E1/stage-completion.json"
        )
        self._assert_start_fails_before_write(
            roots, gate, self.root / "workspace-foreign", "T1_E1_INVALID"
        )

        roots, gate = self._start_fixture("stale")
        gate["upstream_completions"][1]["sha256"] = "0" * 64
        self._assert_start_fails_before_write(
            roots, gate, self.root / "workspace-stale", "T1_W1_INVALID"
        )

        roots, gate = self._start_fixture("tampered")
        completion_path = roots["B0"] / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["run_id"] = "foreign-run"
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        self._assert_start_fails_before_write(
            roots, gate, self.root / "workspace-tampered", "T1_B0_INVALID"
        )

        roots, gate = self._start_fixture("previous-chain")
        completion_path = roots["E1"] / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["previous_stage_completions"] = [
            copy.deepcopy(gate["upstream_completions"][0])
        ]
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        gate["upstream_completions"][2]["sha256"] = runtime.sha256_file(
            completion_path
        )
        self._assert_start_fails_before_write(
            roots,
            gate,
            self.root / "workspace-previous-chain",
            "T1_E1_INVALID",
        )


class T1PlanReviewReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        _storyline, _environment, self.payload = contract_22_test.base_case()
        for event in self.payload["planned_event_registry"]:
            event["consumes_token_instance_ids"] = []
            event["lifecycle_effects"] = []
        self.payload.update(
            {
                "lifecycle_scope": {
                    "id": "LFS-NOT-APPLICABLE",
                    "applicability": "not_applicable",
                    "source_ids": ["SL-A"],
                    "lifecycle_contract_ids": [],
                    "semantic_review_claim_id": "T1LFS-NOT-APPLICABLE",
                },
                "lifecycle_contract_registry": [],
            }
        )
        self.session = {
            "run_id": "review-run",
            "session_id": "review-session",
            "thread_id": "producer-thread",
            "input_gate": {"path": "T1/input-gate.json", "sha256": "1" * 64},
            "upstream_package_bindings": [
                {
                    "stage": "S1",
                    "manifest": {"path": "sources/S1/package-manifest.json", "sha256": "2" * 64},
                    "completion": {"path": "sources/S1/stage-completion.json", "sha256": "3" * 64},
                }
            ],
            "e1_semantic_review_bindings": [
                {
                    "review_protocol": "e1-authority-capability-semantics-v1",
                    "manifest": {"path": "sources/E1/review/manifest.json", "sha256": "4" * 64},
                }
            ],
            "implementation_bindings": [
                {"identity": "skill/run_v2.py", "sha256": "5" * 64},
                {"identity": "schemas/event-timeline.schema.json", "sha256": "6" * 64},
                {"identity": "skill/runtime-contract.md", "sha256": "7" * 64},
            ],
        }
        t1._write(self.root / "generation-session.json", self.session)
        t1._write(
            self.root / "generation-evidence" / "01-event-demand-scan.json",
            {"phase": "event-demand-scan", "payload": {"sealed": True}},
        )
        self.request = t1._expected_plan_review_request(
            self.root, session=self.session, payload=self.payload
        )
        candidate_path, request_path, _task_output_path, _review_path, _validation_path, _manifest_path = (
            t1._plan_review_paths(self.root, self.request["candidate_sha256"])
        )
        t1._write(candidate_path, self.payload)
        t1._write(request_path, self.request)
        review = {
            "claim_verdicts": [
                {
                    "claim_id": claim_id,
                    "verdict": "pass",
                    "rationale": "The exact bounded plan claim is semantically supported.",
                }
                for claim_id in self.request["planned_claim_ids"]
            ],
            "findings": [],
        }
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "reviewer-thread"}, clear=False
        ):
            receipt = t1.seal_t1_review_task_output(
                self.root,
                candidate_sha256=self.request["candidate_sha256"],
                task_id="task-t1-plan-review",
                verdict_payload=review,
            )
            t1.submit_t1_plan_semantic_review(
                self.root,
                candidate_sha256=self.request["candidate_sha256"],
                review={**review, "reviewer_task_receipt": receipt},
            )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_review_package_validates_and_binds_planned_propositions(self) -> None:
        reference = t1._validated_plan_review(
            self.root, session=self.session, payload=self.payload
        )
        self.assertTrue(reference["path"].endswith("package-manifest.json"))
        claim_kinds = {item["claim_kind"] for item in self.request["claims"]}
        self.assertIn("planned_proposition_registry", claim_kinds)
        self.assertEqual(
            len(self.request["planned_claim_ids"]),
            len(set(self.request["planned_claim_ids"])),
        )

    def test_review_replay_rejects_every_bound_dependency(self) -> None:
        mutations = []
        changed_gate = copy.deepcopy(self.session)
        changed_gate["input_gate"]["sha256"] = "8" * 64
        mutations.append(changed_gate)
        changed_upstream = copy.deepcopy(self.session)
        changed_upstream["upstream_package_bindings"][0]["manifest"]["sha256"] = "9" * 64
        mutations.append(changed_upstream)
        changed_e1_review = copy.deepcopy(self.session)
        changed_e1_review["e1_semantic_review_bindings"][0]["manifest"]["sha256"] = "a" * 64
        mutations.append(changed_e1_review)
        changed_runtime = copy.deepcopy(self.session)
        changed_runtime["implementation_bindings"][0]["sha256"] = "b" * 64
        mutations.append(changed_runtime)
        for changed in mutations:
            with self.subTest(changed=changed), self.assertRaisesRegex(
                t1.T1Error, "T1_PLAN_REVIEW_STALE"
            ):
                t1._validated_plan_review(
                    self.root, session=changed, payload=self.payload
                )

        p1 = self.root / "generation-evidence" / "01-event-demand-scan.json"
        original = p1.read_text(encoding="utf-8")
        t1._write(p1, {"phase": "event-demand-scan", "payload": {"sealed": False}})
        with self.assertRaisesRegex(t1.T1Error, "T1_PLAN_REVIEW_STALE"):
            t1._validated_plan_review(
                self.root, session=self.session, payload=self.payload
            )
        p1.write_text(original, encoding="utf-8", newline="")

        changed_payload = copy.deepcopy(self.payload)
        changed_payload["planned_event_registry"][0]["atomicity_reason"] = "changed"
        with self.assertRaisesRegex(t1.T1Error, "T1_PLAN_REVIEW_MISSING"):
            t1._validated_plan_review(
                self.root, session=self.session, payload=changed_payload
            )

    def test_review_replay_rejects_task_identity_and_output_drift(self) -> None:
        candidate_path, request_path, task_output, review_path, _validation, _manifest = (
            t1._plan_review_paths(self.root, self.request["candidate_sha256"])
        )
        original_review = t1._read(review_path, "test")
        original_output = t1._read(task_output, "test")
        receipt_mutations = (
            ("producer_thread_id", "forged-producer"),
            ("reviewer_thread_id", "forged-reviewer"),
            ("task_id", "forged-task"),
            ("output_sha256", "0" * 64),
            ("candidate_sha256", "f" * 64),
            ("review_kind", "forged-review-kind"),
            ("review_protocol", "forged-review-protocol"),
            ("candidate", runtime.artifact_reference(request_path, root=self.root)),
            ("request", runtime.artifact_reference(candidate_path, root=self.root)),
            ("output_artifact", runtime.artifact_reference(candidate_path, root=self.root)),
        )
        for field, value in receipt_mutations:
            changed = copy.deepcopy(original_review)
            changed["reviewer_task_receipt"][field] = value
            t1._write(review_path, changed)
            with self.subTest(field=field), self.assertRaisesRegex(
                t1.T1Error, "T1_REVIEW_TASK_RECEIPT_INVALID"
            ):
                t1._validated_plan_review(
                    self.root, session=self.session, payload=self.payload
                )
            self.assertFalse(
                (self.root / "generation-evidence" / "02-global-timeline.json").exists()
            )
        t1._write(review_path, original_review)
        changed_output = copy.deepcopy(original_output)
        changed_output["verdict_payload"]["findings"] = [
            {
                "id": "forged-finding",
                "severity": "advisory",
                "claim_ids": [],
                "message": "drift",
            }
        ]
        t1._write(task_output, changed_output)
        with self.assertRaisesRegex(t1.T1Error, "T1_REVIEW_TASK_RECEIPT_INVALID"):
            t1._validated_plan_review(
                self.root, session=self.session, payload=self.payload
            )
        self.assertFalse(
            (self.root / "generation-evidence" / "02-global-timeline.json").exists()
        )

        t1._write(task_output, original_output)
        changed_review = copy.deepcopy(original_review)
        changed_review["claim_verdicts"][0]["rationale"] = "forged verdict drift"
        t1._write(review_path, changed_review)
        with self.assertRaisesRegex(t1.T1Error, "T1_REVIEW_TASK_RECEIPT_INVALID"):
            t1._validated_plan_review(
                self.root, session=self.session, payload=self.payload
            )
        self.assertFalse(
            (self.root / "generation-evidence" / "02-global-timeline.json").exists()
        )


class T1FailBeforeEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.storyline, self.environment, self.plan = contract_22_test.base_case()
        for event in self.plan["planned_event_registry"]:
            event["consumes_token_instance_ids"] = []
            event["lifecycle_effects"] = []
        self.plan.update(
            {
                "lifecycle_scope": {
                    "id": "LFS-NOT-APPLICABLE",
                    "applicability": "not_applicable",
                    "source_ids": ["SL-A"],
                    "lifecycle_contract_ids": [],
                    "semantic_review_claim_id": "T1LFS-NOT-APPLICABLE",
                },
                "lifecycle_contract_registry": [],
            }
        )
        self.session = {
            "run_id": "fail-before-evidence",
            "input_gate": {"path": "T1/input-gate.json", "sha256": "1" * 64},
            "source_artifacts": [
                {
                    "path": "sources/E1/environment-system.json",
                    "sha256": "2" * 64,
                }
            ],
        }
        self.context = (
            self.session,
            {"run_id": "fail-before-evidence"},
            self.storyline,
            {},
            self.environment,
            [],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _seal_stub(self, sequence: int, phase: str, payload: dict[str, object]) -> Path:
        path = self.root / "generation-evidence" / f"{sequence:02d}-{phase}.json"
        t1._write(
            path,
            {
                "phase": phase,
                "payload": payload,
                "payload_sha256": runtime.canonical_sha256(payload),
            },
        )
        return path

    def _p2_payload(self) -> dict[str, object]:
        payload = copy.deepcopy(self.plan)
        payload.update(
            {"design_decisions": [], "event_span": {}, "timeline_axes": {}}
        )
        return payload

    def test_p2_proposition_closure_fails_before_review_write(self) -> None:
        session = {
            **self.session,
            "session_id": "fail-before-review",
            "thread_id": "producer-thread",
            "plan_review_protocol": t1.T1_PLAN_REVIEW_PROTOCOL,
            "source_artifacts": [
                {
                    "path": "sources/E1/environment-system.json",
                    "sha256": "2" * 64,
                }
            ],
        }
        p1 = {
            "event_demands": [],
            **t1.t1_contract_23.expected_e1_digests(
                self.environment,
                source_path="sources/E1/environment-system.json",
                source_sha256="2" * 64,
                canonical_sha256=runtime.canonical_sha256,
            ),
        }
        self._seal_stub(1, t1.PHASES[0], p1)
        payload = self._p2_payload()
        payload["planned_event_registry"][0]["produces_proposition_ids"] = []
        candidate_sha256 = runtime.canonical_sha256(payload)
        candidate_path, request_path, *_rest = t1._plan_review_paths(
            self.root, candidate_sha256
        )
        context = (
            session,
            {"run_id": "fail-before-evidence"},
            self.storyline,
            {},
            self.environment,
            [],
        )
        with (
            mock.patch.object(t1, "_validated_session", return_value=context),
            self.assertRaisesRegex(
                t1.T1Error, "T1_PLANNED_EVENT_PROPOSITION_OUTPUT_MISSING"
            ),
        ):
            t1.start_t1_plan_semantic_review(
                self.root,
                baseline_package="B0",
                storyline_package="S1",
                world_package="W1",
                environment_package="E1",
                input_gate=mock.Mock(reference=self.session["input_gate"]),
                payload=payload,
            )
        self.assertFalse(candidate_path.exists())
        self.assertFalse(request_path.exists())

    def test_p2_proposition_closure_fails_before_phase_evidence_write(self) -> None:
        p1 = self._seal_stub(1, t1.PHASES[0], {"sealed": "P1"})
        p1_sha256 = runtime.sha256_file(p1)
        payload = self._p2_payload()
        payload["planned_event_registry"][0]["requires_proposition_ids"] = [
            "PROP-INITIAL",
            "PROP-INITIAL",
        ]
        with (
            mock.patch.object(t1, "_validated_session", return_value=self.context),
            self.assertRaisesRegex(
                t1.T1Error,
                "T1_PLANNED_EVENT_PROPOSITION_REFERENCE_DUPLICATE",
            ),
        ):
            t1.submit_t1_phase(
                self.root,
                baseline_package="B0",
                storyline_package="S1",
                world_package="W1",
                environment_package="E1",
                input_gate=mock.Mock(reference=self.session["input_gate"]),
                phase=t1.PHASES[1],
                payload=payload,
            )
        self.assertFalse(
            (self.root / "generation-evidence" / "02-global-timeline.json").exists()
        )
        self.assertEqual(p1_sha256, runtime.sha256_file(p1))

    def test_p2_p3_p4_fail_without_evidence_or_prefix_mutation(self) -> None:
        p1 = self._seal_stub(1, t1.PHASES[0], {"sealed": "P1"})
        p1_hash = runtime.sha256_file(p1)
        p2 = copy.deepcopy(self.plan)
        p2.update(
            {
                "design_decisions": [],
                "event_span": {},
                "timeline_axes": {},
            }
        )
        p2["transition_event_cover"] = []
        with mock.patch.object(t1, "_validated_session", return_value=self.context):
            with self.assertRaisesRegex(t1.T1Error, "T1_TRANSITION_EVENT_COVER_MISMATCH"):
                t1.submit_t1_phase(
                    self.root,
                    baseline_package="B0",
                    storyline_package="S1",
                    world_package="W1",
                    environment_package="E1",
                    input_gate=mock.Mock(reference=self.session["input_gate"]),
                    phase=t1.PHASES[1],
                    payload=p2,
                )
        self.assertFalse((self.root / "generation-evidence" / "02-global-timeline.json").exists())
        self.assertEqual(p1_hash, runtime.sha256_file(p1))

        valid_p2 = copy.deepcopy(self.plan)
        valid_p2.update({"design_decisions": [], "event_span": {}, "timeline_axes": {}})
        p2_path = self._seal_stub(2, t1.PHASES[1], valid_p2)
        prefix = [runtime.sha256_file(p1), runtime.sha256_file(p2_path)]
        p3 = {
            "proposition_registry": [],
            "major_events": [],
            "causal_edges": [],
            "environment_placement": [],
        }
        with mock.patch.object(t1, "_validated_session", return_value=self.context):
            with self.assertRaisesRegex(t1.T1Error, "T1_P3_EVENT_SET_MISMATCH"):
                t1.submit_t1_phase(
                    self.root,
                    baseline_package="B0",
                    storyline_package="S1",
                    world_package="W1",
                    environment_package="E1",
                    input_gate=mock.Mock(reference=self.session["input_gate"]),
                    phase=t1.PHASES[2],
                    payload=p3,
                )
        self.assertFalse((self.root / "generation-evidence" / "03-event-and-causality-model.json").exists())
        self.assertEqual(prefix, [runtime.sha256_file(p1), runtime.sha256_file(p2_path)])

        p3_path = self._seal_stub(3, t1.PHASES[2], p3)
        prefix = [runtime.sha256_file(path) for path in (p1, p2_path, p3_path)]
        p4 = {field: [] for field in t1.PHASE_FIELDS[t1.PHASES[3]]}
        p4["authority_partition"] = {}
        with (
            mock.patch.object(t1, "_validated_session", return_value=self.context),
            mock.patch.object(t1, "_validate_phase_chain", return_value=[]),
            mock.patch.object(
                t1,
                "_validate_model",
                side_effect=t1.T1Error("T1_PROVISIONAL_REPLAY_FAILED", "mutant"),
            ),
        ):
            with self.assertRaisesRegex(t1.T1Error, "T1_PROVISIONAL_REPLAY_FAILED"):
                t1.submit_t1_phase(
                    self.root,
                    baseline_package="B0",
                    storyline_package="S1",
                    world_package="W1",
                    environment_package="E1",
                    input_gate=mock.Mock(reference=self.session["input_gate"]),
                    phase=t1.PHASES[3],
                    payload=p4,
                )
        self.assertFalse((self.root / "generation-evidence" / "04-cross-line-state-test.json").exists())
        self.assertEqual(prefix, [runtime.sha256_file(path) for path in (p1, p2_path, p3_path)])


class T1RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        e1_test.E1RuntimeTests.setUpClass()
        upstream = e1_test.E1RuntimeTests
        cls.shared = upstream.shared
        cls.b0 = upstream.shared_b0
        cls.s1 = upstream.shared_s1
        cls.w1 = upstream.shared_w1
        cls.coordinator = runtime.AutonomousCoordinator.from_snapshot(
            upstream.coordinator_state, upstream.coordinator_reference
        )
        cls.e1 = cls.shared / "run" / "E1-for-T1"
        workspace = cls.shared / "workspace" / "E1-for-T1"
        gate = cls.coordinator.build_input_gate("E1", "E1/input-gate.json")
        baseline = cls._read(cls.b0 / "author-control-baseline.json")
        storyline = cls._read(cls.s1 / "storyline-architecture.json")
        world = cls._read(cls.w1 / "world-model.json")
        proposal = e1_test.agent_environment_proposal(
            run_id=baseline["run_id"],
            gate_reference=gate.reference,
            source_artifacts=e1._source_artifacts(cls.b0, cls.s1, cls.w1),
            baseline=baseline,
            storyline=storyline,
            world=world,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-shared-e1-for-t1"}, clear=False
        ):
            e1.start_e1_session(
                workspace,
                baseline_package=cls.b0,
                storyline_package=cls.s1,
                world_package=cls.w1,
                input_gate=gate,
            )
            cls._submit_module(
                e1,
                workspace,
                gate,
                proposal,
                {
                    "baseline_package": cls.b0,
                    "storyline_package": cls.s1,
                    "world_package": cls.w1,
                },
            )
            e1.run_e1(
                cls.e1,
                baseline_package=cls.b0,
                storyline_package=cls.s1,
                world_package=cls.w1,
                coordinator=cls.coordinator,
                input_gate=gate,
                controlled_workspace=workspace,
                logical_package_path="E1",
                next_state_path="state/revision-004.json",
            )
        cls.coordinator_state = cls.coordinator.state
        cls.coordinator_reference = cls.coordinator.state_reference

    @classmethod
    def tearDownClass(cls) -> None:
        e1_test.E1RuntimeTests.tearDownClass()

    @staticmethod
    def _read(path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _submit_module(module, workspace, gate, model, inputs, phases=None) -> None:
        for phase in phases or module.PHASES:
            payload = (
                {"model": model}
                if phase == module.PHASES[-1]
                else {
                    field: model[field]
                    for field in module.PHASE_FIELDS[phase]
                }
            )
            submit = module.submit_e1_phase if module is e1 else module.submit_t1_phase
            if module is e1 and phase == "zones-and-topology":
                request = e1.start_e1_authority_semantic_review(
                    workspace,
                    baseline_package=inputs["baseline_package"],
                    storyline_package=inputs["storyline_package"],
                    world_package=inputs["world_package"],
                    input_gate=gate,
                    payload=payload,
                )
                review = {
                    "claim_verdicts": [
                        {
                            "claim_id": item["id"],
                            "verdict": "pass",
                            "rationale": "The sealed sources support this bounded authority claim.",
                        }
                        for item in request["claims"]
                    ],
                    "reviewer_task_receipt": {
                        "task_id": "t1-fixture-authority-review",
                        "output_sha256": runtime.canonical_sha256(request),
                    },
                }
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": "thread-t1-fixture-e1-authority-reviewer"},
                    clear=False,
                ):
                    review["reviewer_task_receipt"] = (
                        e1.seal_e1_review_task_output(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review_kind=request["review_kind"],
                            task_id="t1-fixture-authority-review",
                            verdict_payload={
                                "claim_verdicts": review["claim_verdicts"]
                            },
                        )
                    )
                    e1.submit_e1_authority_semantic_review(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        review=review,
                    )
            if module is e1 and phase == "storyline-hosting-test":
                request = e1.start_e1_hosting_semantic_review(
                    workspace,
                    baseline_package=inputs["baseline_package"],
                    storyline_package=inputs["storyline_package"],
                    world_package=inputs["world_package"],
                    input_gate=gate,
                    payload=payload,
                )
                review = {
                    "claim_verdicts": [
                        {
                            "claim_id": item["id"],
                            "verdict": "pass",
                            "rationale": "The bounded local value realizes this exact source token.",
                        }
                        for item in request["claims"]
                    ],
                    "record_verdicts": [
                        {
                            "record_id": item["id"],
                            "checks": {
                                check: "pass"
                                for check in e1._TRANSITION_RECORD_REVIEW_CHECKS
                            },
                            "rationale": "The same-line pair is local, coherent, and non-generic.",
                        }
                        for item in request["records"]
                    ],
                    "reviewer_task_receipt": {
                        "task_id": "t1-fixture-transition-review",
                        "output_sha256": runtime.canonical_sha256(request),
                    },
                }
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": "thread-t1-fixture-e1-reviewer"},
                    clear=False,
                ):
                    review["reviewer_task_receipt"] = (
                        e1.seal_e1_review_task_output(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review_kind=request["review_kind"],
                            task_id="t1-fixture-transition-review",
                            verdict_payload={
                                "claim_verdicts": review["claim_verdicts"],
                                "record_verdicts": review["record_verdicts"],
                            },
                        )
                    )
                    e1.submit_e1_hosting_semantic_review(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        review=review,
                    )
            if module is t1 and phase == "global-timeline":
                request = t1.start_t1_plan_semantic_review(
                    workspace,
                    baseline_package=inputs["baseline_package"],
                    storyline_package=inputs["storyline_package"],
                    world_package=inputs["world_package"],
                    environment_package=inputs["environment_package"],
                    input_gate=gate,
                    payload=payload,
                )
                review = {
                    "claim_verdicts": [
                        {
                            "claim_id": claim_id,
                            "verdict": "pass",
                            "rationale": "The complete planned claim is bounded and semantically supported.",
                        }
                        for claim_id in request["planned_claim_ids"]
                    ],
                    "findings": [],
                }
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": "thread-t1-fixture-plan-reviewer"},
                    clear=False,
                ):
                    receipt = t1.seal_t1_review_task_output(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        task_id="task-t1-fixture-plan-review",
                        verdict_payload=review,
                    )
                    t1.submit_t1_plan_semantic_review(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        review={**review, "reviewer_task_receipt": receipt},
                    )
            submit(
                workspace,
                **inputs,
                input_gate=gate,
                phase=phase,
                payload=payload,
            )

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.input_roots = {}
        for stage, source in (
            ("B0", self.b0),
            ("S1", self.s1),
            ("W1", self.w1),
            ("E1", self.e1),
        ):
            target = self.work / "run" / stage
            shutil.copytree(source, target)
            self.input_roots[stage] = target
        self.coordinator = runtime.AutonomousCoordinator.from_snapshot(
            self.coordinator_state, self.coordinator_reference
        )
        self.gate = self.coordinator.build_input_gate("T1", "T1/input-gate.json")
        self.package = self.work / "run" / "T1"
        self.workspace = self.work / "workspace" / "T1"
        self.baseline = self._read(
            self.input_roots["B0"] / "author-control-baseline.json"
        )
        self.storyline = self._read(
            self.input_roots["S1"] / "storyline-architecture.json"
        )
        self.world = self._read(self.input_roots["W1"] / "world-model.json")
        self.environment = self._read(
            self.input_roots["E1"] / "environment-system.json"
        )
        self.inputs = {
            "baseline_package": self.input_roots["B0"],
            "storyline_package": self.input_roots["S1"],
            "world_package": self.input_roots["W1"],
            "environment_package": self.input_roots["E1"],
        }
        self.proposal = agent_event_proposal(
            run_id=self.baseline["run_id"],
            gate_reference=self.gate.reference,
            source_artifacts=t1._source_artifacts(
                self.input_roots["B0"],
                self.input_roots["S1"],
                self.input_roots["W1"],
                self.input_roots["E1"],
            ),
            baseline=self.baseline,
            storyline=self.storyline,
            world=self.world,
            environment=self.environment,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _validate(self, model=None, *, storyline=None) -> None:
        t1._validate_model(
            model or self.proposal,
            self.baseline,
            storyline or self.storyline,
            self.world,
            self.environment,
            t1._controls(self.input_roots["B0"], self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=t1._source_artifacts(
                self.input_roots["B0"],
                self.input_roots["S1"],
                self.input_roots["W1"],
                self.input_roots["E1"],
            ),
        )

    @staticmethod
    def _append_causal_edge(
        model: dict[str, object],
        *,
        edge_id: str,
        from_event_id: str,
        to_event_id: str,
        edge_kind: str = "narrative_causal",
        payload_ids: list[str] | None = None,
    ) -> None:
        events = {
            item["id"]: item for item in model["major_events"]
        }
        source = events[from_event_id]
        target = events[to_event_id]
        target["predecessor_event_ids"].append(from_event_id)
        edge = {
                "id": edge_id,
                "from_event_id": from_event_id,
                "to_event_id": to_event_id,
                "edge_kind": edge_kind,
                "payload_ids": list(payload_ids or []),
                "mechanism": (
                    "[CAUSE_RESULT_SHA256:"
                    f"{runtime.canonical_sha256(source['direct_result'])}]"
                    "[CAUSE_PRESSURE_SHA256:"
                    f"{runtime.canonical_sha256(source['next_pressure'])}] "
                    "The source result creates this tested dependency."
                ),
                "necessary_condition": (
                    "[PRECONDITION_SHA256:"
                    f"{runtime.canonical_sha256(target['preconditions'][0])}] "
                    f"{target['preconditions'][0]} remains necessary."
                ),
            }
        model["causal_edges"].append(edge)
        planned_events = {
            item["id"]: item for item in model["planned_event_registry"]
        }
        planned_events[to_event_id]["predecessor_event_ids"].append(from_event_id)
        model["planned_causal_edges"].append(copy.deepcopy(edge))

    def _connection_record(
        self,
        relation: str,
        *,
        model: dict[str, object] | None = None,
        storyline: dict[str, object] | None = None,
    ) -> tuple[dict[str, object], dict[str, object]]:
        candidate = model or self.proposal
        source_storyline = storyline or self.storyline
        connection = next(
            item
            for item in source_storyline["connections"]
            if item["relation"] == relation
        )
        record = next(
            item
            for item in candidate["connection_realization"]
            if item["connection_id"] == connection["id"]
        )
        return connection, record

    def _associative_case(
        self,
    ) -> tuple[dict[str, object], dict[str, object]]:
        storyline = copy.deepcopy(self.storyline)
        model = copy.deepcopy(self.proposal)
        connection = storyline["connections"][0]
        connection["relation"] = "associative"
        record = next(
            item
            for item in model["connection_realization"]
            if item["connection_id"] == connection["id"]
        )
        edge_ids = set(record["causal_edge_ids"])
        self.assertTrue(
            edge_ids,
            "associative fixture requires a causal connection to convert",
        )
        removed_edges = [
            item
            for item in model["causal_edges"]
            if item["id"] in edge_ids
        ]
        self.assertEqual(
            edge_ids,
            {item["id"] for item in removed_edges},
            "every claimed causal edge must exist exactly once",
        )
        model["causal_edges"] = [
            item
            for item in model["causal_edges"]
            if item["id"] not in edge_ids
        ]
        changed_targets = {}
        for edge in removed_edges:
            targets = [
                item
                for item in model["major_events"]
                if item["id"] == edge["to_event_id"]
            ]
            self.assertEqual(
                1,
                len(targets),
                "each removed edge must have exactly one target event",
            )
            target = targets[0]
            self.assertEqual(
                1,
                target["predecessor_event_ids"].count(
                    edge["from_event_id"]
                ),
                "the removed edge must have exactly one predecessor projection",
            )
            target["predecessor_event_ids"].remove(
                edge["from_event_id"]
            )
            changed_targets[target["id"]] = target
        owned = model["authority_partition"]["autonomous_owned"]
        for edge_id in sorted(edge_ids):
            self.assertEqual(
                1,
                owned.count(edge_id),
                "each removed edge must have exactly one authority entry",
            )
        model["authority_partition"]["autonomous_owned"] = [
            item for item in owned if item not in edge_ids
        ]
        for event_id, target in changed_targets.items():
            claims = [
                item
                for item in model["derivation_claims"]
                if item["projection_ids"] == [event_id]
            ]
            self.assertEqual(
                1,
                len(claims),
                "each changed target event must have one derivation claim",
            )
            claims[0]["value_sha256"] = runtime.canonical_sha256(target)
        record.update(
            {
                "relation": "associative",
                "realization_kind": "associative_alignment",
                "causal_edge_ids": [],
            }
        )
        timing = next(
            item
            for item in model["narrative_timing_constraints"]
            if item["id"] == record["timing_constraint_ids"][0]
        )
        timing["constraint"] = (
            "[REL:association] The anchors align without causal order."
        )
        return storyline, model

    def test_state_anchor_index_contract_handles_two_multi_and_repeated(
        self,
    ) -> None:
        two = t1._state_anchors_for_line(
            "SL-TWO",
            ["same", "same"],
            [{"trigger_ids": ["EV-TWO-01"]}],
        )
        self.assertEqual(
            ("EV-TWO-01", "before", 0, "same"),
            (
                two[("SL-TWO", 0)]["event_id"],
                two[("SL-TWO", 0)]["side"],
                two[("SL-TWO", 0)]["state_index"],
                two[("SL-TWO", 0)]["state"],
            ),
        )
        self.assertEqual(
            ("EV-TWO-01", "after", 1, "same"),
            (
                two[("SL-TWO", 1)]["event_id"],
                two[("SL-TWO", 1)]["side"],
                two[("SL-TWO", 1)]["state_index"],
                two[("SL-TWO", 1)]["state"],
            ),
        )
        multi = t1._state_anchors_for_line(
            "SL-MULTI",
            ["repeat", "middle", "repeat", "end"],
            [
                {"trigger_ids": ["EV-MULTI-01"]},
                {"trigger_ids": ["EV-MULTI-02"]},
                {"trigger_ids": ["EV-MULTI-03"]},
            ],
        )
        self.assertEqual(
            ["before", "after", "after", "after"],
            [
                multi[("SL-MULTI", index)]["side"]
                for index in range(4)
            ],
        )
        self.assertEqual(
            ["EV-MULTI-01", "EV-MULTI-01", "EV-MULTI-02", "EV-MULTI-03"],
            [
                multi[("SL-MULTI", index)]["event_id"]
                for index in range(4)
            ],
        )
        self.assertNotEqual(
            multi[("SL-MULTI", 0)],
            multi[("SL-MULTI", 2)],
        )

    def test_long_responsibility_chain_is_monotonic_and_terminal(
        self,
    ) -> None:
        event_ids = [
            "EV-LONG-01",
            "EV-LONG-02",
            *[f"EV-LONG-{index:02d}" for index in range(3, 12)],
            "EV-LONG-12",
            "EV-LONG-13",
        ]
        roles = {
            event_ids[0]: ["background", "setup"],
            event_ids[1]: ["trigger"],
            **{
                event_id: ["development"]
                for event_id in event_ids[2:-2]
            },
            event_ids[-2]: ["turn_or_crisis"],
            event_ids[-1]: ["result", "aftermath"],
        }
        t1._validate_storyline_responsibility_progression(
            "SL-LONG", event_ids, roles
        )
        looped = copy.deepcopy(roles)
        looped[event_ids[-1]] = ["result", "aftermath"]
        looped[event_ids[-2]] = ["result"]
        looped[event_ids[-1]] = ["background", "result", "aftermath"]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_STORYLINE_CHAIN_INCOMPLETE"
        ):
            t1._validate_storyline_responsibility_progression(
                "SL-LONG", event_ids, looped
            )

        terminal = copy.deepcopy(self.proposal)
        sequence = terminal["storyline_event_sequences"][0]
        final_event_id = sequence["event_ids"][-1]
        prior_event_id = sequence["event_ids"][-2]
        final_line_ledger = next(
            item
            for item in terminal["state_ledger"]
            if item["subject_id"] == sequence["storyline_id"]
            and item["trigger_ids"] == [final_event_id]
        )
        prior_ledger = next(
            item
            for item in terminal["state_ledger"]
            if item["trigger_ids"] == [prior_event_id]
        )
        final_line_ledger["trigger_ids"] = [prior_event_id]
        prior_ledger["trigger_ids"] = [final_event_id]
        event_by_id = {
            item["id"]: item for item in terminal["major_events"]
        }
        for field in ("before_state", "after_state"):
            (
                event_by_id[final_event_id][field],
                event_by_id[prior_event_id][field],
            ) = (
                event_by_id[prior_event_id][field],
                event_by_id[final_event_id][field],
            )
        with self.assertRaisesRegex(
            t1.T1Error,
            "T1_P3_EVENT_SUBJECT_MISMATCH",
        ):
            self._validate(terminal)

    def test_connection_anchor_relation_and_causal_contract_fail_closed(
        self,
    ) -> None:
        for field, value, code in (
            ("state_index", 999, "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH"),
            ("side", "before", "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH"),
            ("event_id", "EV-NOT-THE-ANCHOR", "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH"),
        ):
            model = copy.deepcopy(self.proposal)
            _, record = self._connection_record("causal", model=model)
            record["source_anchor"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                t1.T1Error, code
            ):
                self._validate(model)

        relation = copy.deepcopy(self.proposal)
        _, record = self._connection_record("causal", model=relation)
        record.update(
            {
                "relation": "associative",
                "realization_kind": "associative_alignment",
                "causal_edge_ids": [],
            }
        )
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_RELATION_MISMATCH"
        ):
            self._validate(relation)

        missing_edge = copy.deepcopy(self.proposal)
        _, record = self._connection_record(
            "causal", model=missing_edge
        )
        record["causal_edge_ids"] = []
        with self.assertRaisesRegex(
            t1.T1Error, "T1_MODEL_SCHEMA_INVALID"
        ):
            self._validate(missing_edge)

        wrong_path = copy.deepcopy(self.proposal)
        _, record = self._connection_record(
            "causal", model=wrong_path
        )
        record["causal_edge_ids"] = [
            next(
                edge["id"]
                for edge in wrong_path["causal_edges"]
                if edge["id"] not in record["causal_edge_ids"]
            )
        ]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_CAUSAL_EDGE_MISMATCH"
        ):
            self._validate(wrong_path)

        wrong_timing = copy.deepcopy(self.proposal)
        _, record = self._connection_record(
            "causal", model=wrong_timing
        )
        record["timing_constraint_ids"] = [
            next(
                item["id"]
                for item in wrong_timing[
                    "narrative_timing_constraints"
                ]
                if "[REL:independent-root]" in item["constraint"]
            )
        ]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_TIMING_MISMATCH"
        ):
            self._validate(wrong_timing)

        missing_predecessor = copy.deepcopy(self.proposal)
        _, record = self._connection_record(
            "causal", model=missing_predecessor
        )
        edge_id = record["causal_edge_ids"][0]
        edge = next(
            item
            for item in missing_predecessor["causal_edges"]
            if item["id"] == edge_id
        )
        target = next(
            item
            for item in missing_predecessor["major_events"]
            if item["id"] == edge["to_event_id"]
        )
        target["predecessor_event_ids"].remove(
            edge["from_event_id"]
        )
        planned_target = next(
            item
            for item in missing_predecessor["planned_event_registry"]
            if item["id"] == edge["to_event_id"]
        )
        planned_target["predecessor_event_ids"].remove(edge["from_event_id"])
        with self.assertRaisesRegex(
            t1.T1Error, "T1_PLANNED_PREDECESSOR_MISMATCH"
        ):
            self._validate(missing_predecessor)

    def test_associative_and_cross_line_edge_ownership_fail_closed(
        self,
    ) -> None:
        relation_attack = copy.deepcopy(self.proposal)
        relation_attack["connection_event_paths"][0]["relation"] = "associative"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_EVENT_PATH_MISMATCH"
        ):
            self._validate(relation_attack)

        hidden = copy.deepcopy(self.proposal)
        lines = {}
        for event in hidden["major_events"]:
            lines.setdefault(
                event["storyline_ids"][0], []
            ).append(event)
        ordered_lines = sorted(
            lines,
            key=lambda line_id: min(
                int(event["world_time"][4:10])
                for event in lines[line_id]
            ),
        )
        source = min(
            lines[ordered_lines[0]],
            key=lambda item: item["world_time"],
        )
        target = max(
            lines[ordered_lines[-1]],
            key=lambda item: item["world_time"],
        )
        self._append_causal_edge(
            hidden,
            edge_id="CE-HIDDEN-CROSS-LINE",
            from_event_id=source["id"],
            to_event_id=target["id"],
        )
        with self.assertRaisesRegex(
            t1.T1Error,
            "T1_CROSS_LINE_CAUSAL_EDGE_OWNERSHIP_MISMATCH",
        ):
            self._validate(hidden)

    def test_authority_partition_rejects_overlap_before_deep_validation(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["downstream_freedom"].append(
            model["authority_partition"]["autonomous_owned"][0]
        )
        with self.assertRaisesRegex(
            t1.T1Error, "T1_AUTHORITY_PARTITION_OVERLAP"
        ):
            self._validate(model)

    def test_authority_partition_requires_all_four_exact_sets(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["autonomous_owned"].pop()
        with self.assertRaisesRegex(
            t1.T1Error, "T1_AUTHORITY_PARTITION_MISMATCH"
        ):
            self._validate(model)

    def _seal_workspace(self) -> None:
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-t1-runtime"}, clear=False
        ):
            t1.start_t1_session(
                self.workspace, **self.inputs, input_gate=self.gate
            )
            self._submit_module(
                t1, self.workspace, self.gate, self.proposal, self.inputs
            )

    def _run_package(self):
        self._seal_workspace()
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-t1-runtime"}, clear=False
        ):
            return t1.run_t1(
                self.package,
                **self.inputs,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="T1",
                next_state_path="state/revision-005.json",
            )

    def test_happy_path_and_exact_package(self) -> None:
        receipt = self._run_package()
        result = t1.validate_t1_package(self.package)
        self.assertEqual(result["verdict"], "ready")
        store = production_store.ProductionRunStore(self.package.parent)
        identity = production._completion_contract_identity(
            store, receipt.completion.reference
        )
        expected_contract = production.CURRENT_CONCEPTION_PRODUCTION_CONTRACT["T1"]
        expected_profile = {
            "stage": "T1",
            "model_schema_version": expected_contract["model_schema_version"],
            "identity_bindings": expected_contract["identity_bindings"],
            "semantic_review_protocols": expected_contract[
                "semantic_review_protocols"
            ],
        }
        observed_profile = {
            "stage": identity["stage"],
            "model_schema_version": identity["model_schema_version"],
            "identity_bindings": {
                kind: {
                    "identity": value["identity"],
                    "sha256": (
                        value["artifact"]["sha256"]
                        if value["artifact"] is not None
                        else None
                    ),
                }
                for kind, value in identity["identity_bindings"].items()
            },
            "semantic_review_protocols": identity["semantic_review_protocols"],
        }
        self.assertEqual(expected_profile, observed_profile)
        self.assertTrue(
            production._identity_matches_current_profile("T1", identity)
        )
        self.assertTrue(
            any("[KIND:resource]" in item["consequence"] for item in self.proposal["state_ledger"])
        )
        self.assertTrue(
            any("[KIND:authority]" in item["consequence"] for item in self.proposal["state_ledger"])
        )

    def test_phase4_provider_failure_writes_no_evidence_and_preserves_prefix(
        self,
    ) -> None:
        candidate = copy.deepcopy(self.proposal)
        candidate["state_ledger"][0]["allowed_by_ids"] = ["RULE-FOREIGN"]
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-t1-runtime"}, clear=False
        ):
            t1.start_t1_session(
                self.workspace, **self.inputs, input_gate=self.gate
            )
            self._submit_module(
                t1,
                self.workspace,
                self.gate,
                candidate,
                self.inputs,
                phases=t1.PHASES[:3],
            )
            prefix = [
                runtime.sha256_file(
                    self.workspace
                    / "generation-evidence"
                    / f"{index:02d}-{phase}.json"
                )
                for index, phase in enumerate(t1.PHASES[:3], 1)
            ]
            with self.assertRaisesRegex(
                t1.T1Error, "T1_LEDGER_PROVIDER_INVALID"
            ):
                t1.submit_t1_phase(
                    self.workspace,
                    **self.inputs,
                    input_gate=self.gate,
                    phase="cross-line-state-test",
                    payload={
                        field: copy.deepcopy(candidate[field])
                        for field in t1.PHASE_FIELDS["cross-line-state-test"]
                    },
                )
        self.assertFalse(
            (
                self.workspace
                / "generation-evidence/04-cross-line-state-test.json"
            ).exists()
        )
        self.assertEqual(
            prefix,
            [
                runtime.sha256_file(
                    self.workspace
                    / "generation-evidence"
                    / f"{index:02d}-{phase}.json"
                )
                for index, phase in enumerate(t1.PHASES[:3], 1)
            ],
        )

    def test_phase4_same_line_wrong_evd_proxy_writes_no_evidence(self) -> None:
        candidate = copy.deepcopy(self.proposal)
        storyline = copy.deepcopy(self.storyline)
        requirements = storyline["event_requirements"]
        first = requirements[0]
        proxy_requirement = copy.deepcopy(first)
        proxy_requirement["id"] = f"{first['id']}-PROXY"
        proxy_requirement["responsibility"] += " A distinct same-line obligation."
        requirements.append(proxy_requirement)
        candidate["event_demands"] = copy.deepcopy(requirements)
        environment = copy.deepcopy(self.environment)
        source_affordance = next(
            item
            for item in environment["event_affordance_catalog"]
            if first["id"] in item["event_requirement_ids"]
        )
        proxy_affordance = copy.deepcopy(source_affordance)
        proxy_affordance["id"] = f"{source_affordance['id']}-PROXY"
        proxy_affordance["event_requirement_ids"] = [proxy_requirement["id"]]
        environment["event_affordance_catalog"].append(proxy_affordance)
        first_coverage = next(
            item
            for item in candidate["event_coverage_ledger"]
            if item["source_ids"] == [first["id"]]
        )
        event_id = first_coverage["realization_ids"][0]
        proxy_coverage = copy.deepcopy(first_coverage)
        proxy_coverage["id"] = f"{first_coverage['id']}-PROXY"
        proxy_coverage["source_ids"] = [proxy_requirement["id"]]
        proxy_coverage["realization_ids"] = [event_id]
        candidate["event_coverage_ledger"].append(proxy_coverage)
        candidate["authority_partition"]["autonomous_owned"].append(
            proxy_coverage["id"]
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-t1-runtime"}, clear=False
        ):
            t1.start_t1_session(
                self.workspace, **self.inputs, input_gate=self.gate
            )
            validated = t1._validated_session(
                self.workspace,
                **self.inputs,
                input_gate=self.gate,
                runtime=runtime.ContractRuntime(),
                full_validation=False,
            )
            session, baseline, _, world, _, controls = validated
            with mock.patch.object(
                t1,
                "_validated_session",
                return_value=(
                    session,
                    baseline,
                    storyline,
                    world,
                    environment,
                    controls,
                ),
            ):
                self._submit_module(
                    t1,
                    self.workspace,
                    self.gate,
                    candidate,
                    self.inputs,
                    phases=t1.PHASES[:3],
                )
                prefix = [
                    runtime.sha256_file(
                        self.workspace
                        / "generation-evidence"
                        / f"{index:02d}-{phase}.json"
                    )
                    for index, phase in enumerate(t1.PHASES[:3], 1)
                ]
                with self.assertRaises(t1.T1Error) as caught:
                    t1.submit_t1_phase(
                        self.workspace,
                        **self.inputs,
                        input_gate=self.gate,
                        phase="cross-line-state-test",
                        payload={
                            field: copy.deepcopy(candidate[field])
                            for field in t1.PHASE_FIELDS["cross-line-state-test"]
                        },
                    )
        self.assertEqual("T1_AFFORDANCE_REQUIREMENT_MISMATCH", caught.exception.code)
        self.assertFalse(
            (
                self.workspace
                / "generation-evidence/04-cross-line-state-test.json"
            ).exists()
        )
        self.assertEqual(
            prefix,
            [
                runtime.sha256_file(
                    self.workspace
                    / "generation-evidence"
                    / f"{index:02d}-{phase}.json"
                )
                for index, phase in enumerate(t1.PHASES[:3], 1)
            ],
        )

    def test_causal_break_cycle_and_time_contradiction(self) -> None:
        broken = copy.deepcopy(self.proposal)
        broken["causal_edges"].pop()
        with self.assertRaises(t1.T1Error):
            self._validate(broken)
        cyclic = copy.deepcopy(self.proposal)
        same_line_sequence = cyclic["storyline_event_sequences"][0]["event_ids"]
        root = same_line_sequence[0]
        end = same_line_sequence[-1]
        cyclic["major_events"][0]["predecessor_event_ids"].append(end)
        event_index = {item["id"]: item for item in cyclic["major_events"]}
        cyclic["causal_edges"].append(
            {
                "id": "CE-CYCLE",
                "from_event_id": end,
                "to_event_id": root,
                "edge_kind": "sequencing",
                "payload_ids": [],
                "mechanism": (
                    "[CAUSE_RESULT_SHA256:"
                    f"{runtime.canonical_sha256(event_index[end]['direct_result'])}]"
                    "[CAUSE_PRESSURE_SHA256:"
                    f"{runtime.canonical_sha256(event_index[end]['next_pressure'])}] "
                    "The final pressure incorrectly loops to the root."
                ),
                "necessary_condition": (
                    "[PRECONDITION_SHA256:"
                    f"{runtime.canonical_sha256(event_index[root]['preconditions'][0])}] "
                    "The root precondition is incorrectly reused."
                ),
            }
        )
        planned_event_index = {
            item["id"]: item for item in cyclic["planned_event_registry"]
        }
        planned_event_index[root]["predecessor_event_ids"].append(end)
        cyclic["planned_causal_edges"].append(
            copy.deepcopy(cyclic["causal_edges"][-1])
        )
        with self.assertRaisesRegex(t1.T1Error, "T1_PLANNED_CAUSAL_CYCLE"):
            self._validate(cyclic)
        reversed_time = copy.deepcopy(self.proposal)
        reversed_time["major_events"][1]["world_time"] = "[WT:000001]"
        with self.assertRaises(t1.T1Error):
            self._validate(reversed_time)

    def test_environment_affordance_and_no_consequence(self) -> None:
        mismatch = copy.deepcopy(self.proposal)
        placement = mismatch["environment_placement"][0]
        placement["affordance_ids"] = [
            next(
                item["id"] for item in self.environment["event_affordance_catalog"]
                if item["environment_id"] != placement["environment_id"]
            )
        ]
        with self.assertRaisesRegex(t1.T1Error, "T1_AFFORDANCE_ENVIRONMENT_MISMATCH"):
            self._validate(mismatch)
        empty = copy.deepcopy(self.proposal)
        empty["major_events"][0]["direct_result"] = "none"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_P3_EVENT_PROJECTION_MISMATCH"
        ):
            self._validate(empty)

    def test_slc_state_information_resource_and_authority_failures(self) -> None:
        missing_slc = copy.deepcopy(self.proposal)
        missing_slc["connection_realization"].pop()
        with self.assertRaisesRegex(t1.T1Error, "T1_CONNECTION_REALIZATION_MISMATCH"):
            self._validate(missing_slc)
        state_break = copy.deepcopy(self.proposal)
        line_ledger = next(
            item for item in state_break["state_ledger"]
            if item["subject_id"].startswith("SL-")
        )
        line_ledger["to_state"] = "broken"
        with self.assertRaises(t1.T1Error):
            self._validate(state_break)
        resource_missing = copy.deepcopy(self.proposal)
        resource_event = next(
            event for event in resource_missing["major_events"]
            if next(iter(event["before_state"])) in {
                item["id"] for item in self.world["resource_flows"]
            }
        )
        resource_missing["state_ledger"] = [
            item for item in resource_missing["state_ledger"]
            if item["trigger_ids"] != [resource_event["id"]]
        ]
        with self.assertRaisesRegex(t1.T1Error, "T1_EVENT_LEDGER_BIDIRECTIONAL_MISMATCH"):
            self._validate(resource_missing)
        authority_bad = copy.deepcopy(self.proposal)
        authority_ledger = next(
            item for item in authority_bad["state_ledger"]
            if "[KIND:authority]" in item["consequence"]
        )
        authority_ledger["consequence"] = authority_ledger["consequence"].replace(
            "[KIND:authority]", "[KIND:state]"
        )
        with self.assertRaisesRegex(t1.T1Error, "T1_LEDGER_KIND_INVALID"):
            self._validate(authority_bad)
        information_bad = copy.deepcopy(self.proposal)
        event = information_bad["major_events"][0]
        event["information_changes"] = ["INFO-001"]
        with self.assertRaisesRegex(t1.T1Error, "T1_INFORMATION_BIDIRECTIONAL_MISMATCH"):
            self._validate(information_bad)

    def test_slc_causal_and_provider_semantic_bridges(self) -> None:
        slc_without_state = copy.deepcopy(self.proposal)
        connection = self.storyline["connections"][0]
        record = next(
            item for item in slc_without_state["connection_realization"]
            if item["connection_id"] == connection["id"]
        )
        original_event_id = record["source_anchor"]["event_id"]
        replacement_event_ids = sorted(
            event["id"]
            for event in slc_without_state["major_events"]
            if connection["from_storyline_id"]
            in event["storyline_ids"]
            and event["id"] != original_event_id
        )
        self.assertTrue(
            replacement_event_ids,
            "source-anchor fixture requires another real event on the source line",
        )
        replacement_event_id = replacement_event_ids[0]
        self.assertNotEqual(
            original_event_id,
            replacement_event_id,
            "source-anchor attack must change the event id",
        )
        record["source_anchor"]["event_id"] = replacement_event_id
        with self.assertRaisesRegex(
            t1.T1Error, "T1_CONNECTION_SOURCE_ANCHOR_MISMATCH"
        ):
            self._validate(slc_without_state)

        causal_junk = copy.deepcopy(self.proposal)
        causal_junk["causal_edges"][0]["mechanism"] = "arbitrary junk"
        with self.assertRaisesRegex(
            t1.T1Error, "T1_P3_CAUSAL_EDGE_PROJECTION_MISMATCH"
        ):
            self._validate(causal_junk)
        wrong_condition = copy.deepcopy(self.proposal)
        wrong_condition["causal_edges"][0]["necessary_condition"] = (
            "[PRECONDITION_SHA256:" + "0" * 64 + "] readable but wrong binding"
        )
        with self.assertRaisesRegex(
            t1.T1Error, "T1_P3_CAUSAL_EDGE_PROJECTION_MISMATCH"
        ):
            self._validate(wrong_condition)

        slot_provider = copy.deepcopy(self.proposal)
        slot_provider["state_ledger"][0]["allowed_by_ids"] = [
            slot_provider["major_events"][0]["initiator_slot_id"]
        ]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_LEDGER_PROVIDER_INVALID"
        ):
            self._validate(slot_provider)
        foreign_provider = copy.deepcopy(self.proposal)
        foreign_ledger = foreign_provider["state_ledger"][0]
        ledger_event = next(
            item
            for item in foreign_provider["major_events"]
            if item["id"] == foreign_ledger["trigger_ids"][0]
        )
        foreign_ledger["allowed_by_ids"] = [
            next(
                item["id"]
                for item in self.environment["access_and_authority"]
                if item["subject_id"] != ledger_event["environment_id"]
            )
        ]
        with self.assertRaisesRegex(
            t1.T1Error, "T1_LEDGER_PROVIDER_INVALID"
        ):
            self._validate(foreign_provider)

    def test_fake_gate_missing_completion_and_boundary_prose(self) -> None:
        fake_gate = copy.deepcopy(self.proposal)
        fake_gate["input_gate"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(t1.T1Error, "T1_GATE_REFERENCE_MISMATCH"):
            self._validate(fake_gate)
        self._run_package()
        (self.package / "stage-completion.json").unlink()
        with self.assertRaises(t1.T1Error):
            t1.validate_t1_package(self.package)
        (self.package / "scene-draft.md").write_text("forbidden prose", encoding="utf-8")
        with self.assertRaisesRegex(t1.T1Error, "T1_BOUNDARY_VIOLATION"):
            t1.validate_t1_package(self.package)

    def test_opposite_upstream_semantics_change_all_five_phase_payloads(self) -> None:
        changed_storyline = copy.deepcopy(self.storyline)
        changed_storyline["event_requirements"][0]["responsibility"] = (
            "Opposite approved upstream responsibility."
        )
        changed = agent_event_proposal(
            run_id=self.baseline["run_id"],
            gate_reference=self.gate.reference,
            source_artifacts=self.proposal["source_artifacts"],
            baseline=self.baseline,
            storyline=changed_storyline,
            world=self.world,
            environment=self.environment,
        )
        for phase in t1.PHASES:
            left = (
                {"model": self.proposal}
                if phase == t1.PHASES[-1]
                else {field: self.proposal[field] for field in t1.PHASE_FIELDS[phase]}
            )
            right = (
                {"model": changed}
                if phase == t1.PHASES[-1]
                else {field: changed[field] for field in t1.PHASE_FIELDS[phase]}
            )
            self.assertNotEqual(
                runtime.canonical_sha256(left),
                runtime.canonical_sha256(right),
                phase,
            )


if __name__ == "__main__":
    unittest.main()
