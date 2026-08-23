import ast
import copy
import importlib
import inspect
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Mapping
from unittest import mock

from jsonschema import Draft202012Validator


runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime"
)
s1 = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
s1_test = importlib.import_module(
    "skills.novel-storyline-architecture-designer.tests.test_v2_runtime"
)
w1 = importlib.import_module(
    "skills.novel-world-model-designer.scripts.run_v2"
)
w1_test = importlib.import_module(
    "skills.novel-world-model-designer.tests.test_v2_runtime"
)
e1 = importlib.import_module(
    "skills.novel-environment-system-designer.scripts.run_v2"
)
baseline_test = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_baseline"
)
production = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
production_store = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


def agent_environment_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    baseline: dict[str, object],
    storyline: dict[str, object],
    world: dict[str, object],
    environment_specs: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """A test Agent's authored E1 model; production never synthesizes it."""

    demands = copy.deepcopy(world["environment_demands"])
    environment_specs = environment_specs or {}
    storyline_environment_requirements = copy.deepcopy(
        storyline["environment_requirements"]
    )
    lines = {item["id"]: item for item in storyline["storylines"]}
    world_requirements = {
        item["id"]: item for item in world["storyline_requirements"]
    }
    world_entities = {
        item["id"]: item
        for field in (
            "world_facts",
            "history_pressures",
            "institutions",
            "systems",
            "resource_flows",
            "authority_flows",
            "information_flows",
            "rule_conflict_matrix",
            "storyline_support_ledger",
        )
        for item in world[field]
    }
    event_by_line = {}
    for requirement in storyline["event_requirements"]:
        line_id = next(item for item in requirement["source_ids"] if item in lines)
        event_by_line[line_id] = requirement
    environment_requirement_by_line = {}
    for requirement in storyline_environment_requirements:
        line_id = next(item for item in requirement["source_ids"] if item in lines)
        environment_requirement_by_line[line_id] = requirement

    decisions = []
    environments = []
    zones = []
    assignments = []
    channels = []
    hazards = []
    hosting = []
    affordances = []
    transitions = []
    derivations = []
    owned_ids = []
    environment_meta = []

    for index, demand in enumerate(demands, 1):
        spec = environment_specs.get(demand["id"], {})
        world_requirement_id = next(
            item for item in demand["source_ids"] if item in world_requirements
        )
        world_requirement = world_requirements[world_requirement_id]
        line_id = next(
            item for item in world_requirement["source_ids"] if item in lines
        )
        event_requirement = event_by_line[line_id]
        storyline_environment_requirement = environment_requirement_by_line[line_id]
        support_ids = [
            item for item in demand["source_ids"] if item in world_entities
        ]
        marker = demand["responsibility"]
        storyline_marker = storyline_environment_requirement["responsibility"]
        environment_id = f"ENV-{index:03d}"
        zone_id = f"ZONE-{index:03d}"
        decision_id = f"DEC-E1-{index:03d}"
        assignment_id = f"ACCESS-{index:03d}"
        channel_id = f"CHANNEL-{index:03d}"
        hazard_id = f"HAZ-{index:03d}"
        hosting_id = f"COV-E1-{index:03d}"
        affordance_id = f"AFF-{index:03d}"
        transition_id = f"TRANS-{index:03d}"
        action = str(
            spec.get(
                "action",
                f"Perform the bounded capability declared by {demand['id']}.",
            )
        )
        from_state = str(
            spec.get("from_state", f"available for {demand['id']}")
        )
        to_state = str(
            spec.get(
                "to_state",
                f"restricted after an attempted action for {demand['id']}",
            )
        )

        decisions.append(
            {
                "id": decision_id,
                "gap": str(
                    spec.get(
                        "decision_gap",
                        f"Choose a reusable environment duty for {marker}.",
                    )
                ),
                "options": copy.deepcopy(
                    spec.get(
                        "decision_options",
                        [
                            f"Create a controlled host for {marker}.",
                            f"Use an incidental one-use location for {marker}.",
                        ],
                    )
                ),
                "selection": str(
                    spec.get(
                        "decision_selection",
                        f"Create a controlled host for {marker}.",
                    )
                ),
                "owner": "E1",
                "authority_basis": f"E1 owns concrete carrying conditions for {demand['id']}.",
                "compatibility": f"Expands W1 without changing its rule: {marker}",
                "impact_ids": [environment_id, zone_id],
                "cost": f"The environment preserves access costs for {marker}.",
                "reversibility": "costly",
                "downstream_freedom": "T1 may select an event that uses the interface.",
                "projection_ids": [environment_id, zone_id],
            }
        )
        environment = {
            "id": environment_id,
            "scope": str(
                spec.get(
                    "scope", f"A bounded operational environment for line {line_id}."
                )
            ),
            "narrative_responsibility": str(
                spec.get(
                    "narrative_responsibility",
                    f"Own the reusable interface {environment_id}.",
                )
            ),
            "features": copy.deepcopy(
                spec.get(
                    "features",
                    [
                        f"Control surfaces expose the bounded interface for {demand['id']}.",
                        "Boundaries make local operating limits observable.",
                    ],
                )
            ),
            "sensory_conditions": copy.deepcopy(
                spec.get(
                    "sensory_conditions",
                    ["Actors can perceive access status and resource pressure."],
                )
            ),
            "access_rules": copy.deepcopy(
                spec.get(
                    "access_rules",
                    [f"Only {assignment_id} may authorize this bounded interface."],
                )
            ),
            "resources": copy.deepcopy(
                spec.get(
                    "resources",
                    [f"Resources explicitly support the interface for {demand['id']}."],
                )
            ),
            "allowed_actions": list(
                dict.fromkeys(
                    [action, *[str(item) for item in spec.get("additional_actions", [])]]
                )
            ),
            "hazards": copy.deepcopy(
                spec.get(
                    "environment_hazards",
                    [f"{hazard_id} can block or worsen the local action."],
                )
            ),
            "zone_ids": [zone_id],
            "connections": [],
            "blockers": copy.deepcopy(
                spec.get(
                    "blockers",
                    ["Failed permission or exhausted resources block the action."],
                )
            ),
            "state_vocabulary": [from_state, to_state],
            "allowed_transitions": [transition_id],
            "storyline_stage_ids": [
                line_id,
                demand["id"],
                storyline_environment_requirement["id"],
            ],
        }
        environments.append(environment)
        zones.append(
            {
                "id": zone_id,
                "environment_id": environment_id,
                "responsibility": str(
                    spec.get(
                        "zone_responsibility",
                        f"Expose the action interface for {marker} and {storyline_marker}.",
                    )
                ),
                "features": copy.deepcopy(
                    spec.get(
                        "zone_features",
                        [f"Observable controls support {marker} and {storyline_marker}."],
                    )
                ),
                "access_rules": [
                    *copy.deepcopy(demand["constraints"]),
                    *copy.deepcopy(
                        storyline_environment_requirement["constraints"]
                    ),
                ],
                "resources": copy.deepcopy(
                    spec.get(
                        "zone_resources", [f"Bounded resource access for {marker}."]
                    )
                ),
                "constraints": copy.deepcopy(
                    spec.get(
                        "zone_constraints",
                        [f"The zone cannot decide an event result for {marker}."],
                    )
                ),
            }
        )
        assignments.append(
            {
                "id": assignment_id,
                "subject_id": environment_id,
                "responsibility": (
                    f"Authorize bounded access for {marker} and "
                    f"{storyline_marker}."
                ),
                "evidence_ids": support_ids,
                "constraints": [
                    *copy.deepcopy(demand["constraints"]),
                    *copy.deepcopy(
                        storyline_environment_requirement["constraints"]
                    ),
                ],
            }
        )
        channels.append(
            {
                "id": channel_id,
                "from_id": environment_id,
                "to_id": zone_id,
                "relation": (
                    f"[DEMAND:{demand['id']}] supplies resource and "
                    f"observable information for {marker} and {storyline_marker}"
                ),
                "mechanism": (
                    f"[MARKER_SHA256:{runtime.canonical_sha256(marker)}] "
                    f"[ACTION_SHA256:{runtime.canonical_sha256(action)}] "
                    f"bounded operational channel for {marker} and "
                    f"{storyline_marker}"
                ),
                "constraints": [
                    *copy.deepcopy(demand["constraints"]),
                    *copy.deepcopy(
                        storyline_environment_requirement["constraints"]
                    ),
                    *[
                        f"[SUPPORT:{support_id}] remains mandatory for {marker}."
                        for support_id in support_ids
                    ],
                ],
            }
        )
        hazards.append(
            {
                "id": hazard_id,
                "environment_id": environment_id,
                "trigger": str(
                    spec.get(
                        "hazard_trigger",
                        "Permission, resource, or information failure during "
                        f"{marker} or {storyline_marker}.",
                    )
                ),
                "effect": str(
                    spec.get(
                        "hazard_effect",
                        "The attempted action is blocked or becomes costlier for "
                        f"{marker} and {storyline_marker}.",
                    )
                ),
                "mitigation_limits": copy.deepcopy(
                    spec.get(
                        "mitigation_limits",
                        [f"Mitigation cannot remove W1 constraints for {marker}."],
                    )
                ),
            }
        )
        source_bindings = [
            e1._hosting_source_binding(
                demand,
                source_kind="world_environment_demand",
                storyline_id=line_id,
            ),
            e1._hosting_source_binding(
                storyline_environment_requirement,
                source_kind="storyline_environment_requirement",
                storyline_id=line_id,
            ),
        ]
        local_projections = []
        projection_clauses = list(spec.get("projection_clauses", []))
        for binding in source_bindings:
            tokens = [
                ("responsibility", binding["responsibility_sha256"]),
                *[
                    ("constraint", constraint_sha256)
                    for constraint_sha256 in binding["constraint_sha256s"]
                ],
            ]
            for token_index, (token_kind, token_sha256) in enumerate(tokens, 1):
                if projection_clauses:
                    projection_index = len(local_projections)
                    clause_count = len(projection_clauses)
                    primary = str(projection_clauses[projection_index % clause_count])
                    secondary = str(
                        projection_clauses[
                            (projection_index + projection_index // clause_count + 1)
                            % clause_count
                        ]
                    )
                    projection_value = f"{primary}；同时，{secondary}"
                else:
                    projection_value = (
                        f"Local {token_kind} clause {token_index} for {binding['source_id']}."
                    )
                environment["features"].append(projection_value)
                pointer = f"/features/{len(environment['features']) - 1}"
                projected_value = e1._resolve_hosting_projection(
                    environment, pointer
                )
                local_projections.append(
                    {
                        "source_id": binding["source_id"],
                        "token_kind": token_kind,
                        "token_sha256": token_sha256,
                        "environment_pointer": pointer,
                        "projection_sha256": runtime.canonical_sha256(
                            projected_value
                        ),
                        "rationale": (
                            f"{pointer} is the local executable projection of "
                            f"this {token_kind} token."
                        ),
                    }
                )
        hosting.append(
            {
                "id": hosting_id,
                "source_ids": [
                    demand["id"],
                    storyline_environment_requirement["id"],
                ],
                "realization_ids": [environment_id],
                "status": "covered",
                "evidence": {
                    "source_bindings": source_bindings,
                    "realization_bindings": [
                        {
                            "environment_id": environment_id,
                            "local_projections": local_projections,
                        }
                    ],
                },
            }
        )
        affordance = {
            "id": affordance_id,
            "environment_id": environment_id,
            "event_requirement_ids": [event_requirement["id"]],
            "allowed_actions": [action],
            "prerequisites": [
                f"{assignment_id} grants access and required resources exist for {marker}."
            ],
            "constraints": [
                *copy.deepcopy(demand["constraints"]),
                *copy.deepcopy(storyline_environment_requirement["constraints"]),
            ],
        }
        affordances.append(affordance)
        transition = {
            "id": transition_id,
            "subject_id": environment_id,
            "from_state": from_state,
            "trigger_ids": [affordance_id],
            "trigger_bindings": [
                {
                    "trigger_id": affordance_id,
                    "source_environment_id": environment_id,
                    "source_storyline_id": line_id,
                    "source_state_index": 0,
                    "target_storyline_id": line_id,
                    "target_state_index": 0,
                    "causal_evidence_ids": [],
                    "topology_path_ids": [],
                    "transport_capability": "local",
                }
            ],
            "to_state": to_state,
            "allowed_by_ids": [assignment_id, *support_ids],
            "consequence": (
                "The environment changes availability without deciding an "
                f"event result for {marker} or {storyline_marker}."
            ),
        }
        transitions.append(transition)
        derivations.extend(
            [
                {
                    "id": f"DRV-E1-ENV-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(environment),
                    "source_ids": [
                        demand["id"],
                        storyline_environment_requirement["id"],
                        *support_ids,
                    ],
                    "decision_ids": [decision_id],
                    "projection_ids": [environment_id],
                },
                {
                    "id": f"DRV-E1-AFF-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(affordance),
                    "source_ids": [
                        demand["id"],
                        storyline_environment_requirement["id"],
                        event_requirement["id"],
                    ],
                    "decision_ids": [decision_id],
                    "projection_ids": [affordance_id],
                },
            ]
        )
        owned_ids.extend(
            [
                decision_id,
                environment_id,
                zone_id,
                assignment_id,
                channel_id,
                hazard_id,
                hosting_id,
                affordance_id,
                transition_id,
            ]
        )
        environment_meta.append((environment_id, marker))

    topology = []
    for index in range(len(environment_meta) - 1):
        left_id, left_marker = environment_meta[index]
        right_id, right_marker = environment_meta[index + 1]
        edge_id = f"TOP-{index+1:03d}"
        topology.append(
            {
                "id": edge_id,
                "from_id": left_id,
                "to_id": right_id,
                "relation": f"controlled transition between {left_marker} and {right_marker}",
                "mechanism": "permission-aware physical or secure logical passage",
                "constraints": [
                    f"Transition preserves constraints for {left_marker}.",
                    f"Transition preserves constraints for {right_marker}.",
                ],
                "directionality": "bidirectional",
                "transfer_capabilities": ["story-causality-transfer"],
            }
        )
        next(item for item in environments if item["id"] == left_id)[
            "connections"
        ].append(edge_id)
        next(item for item in environments if item["id"] == right_id)[
            "connections"
        ].append(edge_id)
        owned_ids.append(edge_id)

    # E1 2.4 capability/readiness contract.  This remains authored test input:
    # production validates it but never synthesizes these choices.
    environment_by_line = {
        line_id: next(
            item for item in environments if line_id in item["storyline_stage_ids"]
        )
        for line_id in lines
    }
    affordance_by_line = {
        line_id: next(
            item
            for item in affordances
            if event_by_line[line_id]["id"] in item["event_requirement_ids"]
        )
        for line_id in lines
    }
    assignment_by_environment = {
        item["subject_id"]: item for item in assignments
    }
    facts = []
    steps = []
    actor_bindings = []
    occurrences = []
    initial_anchors = []
    transition_support = []
    option_by_line = {}
    step_by_line = {}
    root_fact_by_line = {}
    output_fact_by_line = {}
    occurrence_by_line = {}
    transition_support_by_key = {}
    s1_source_artifact = {
        "stage": "S1",
        **next(
            item
            for item in source_artifacts
            if item["path"] == "sources/S1/storyline-architecture.json"
        ),
    }
    storyline_index = {
        item["id"]: index for index, item in enumerate(storyline["storylines"])
    }
    for line_index, line_id in enumerate(sorted(lines), 1):
        line = lines[line_id]
        environment = environment_by_line[line_id]
        affordance = affordance_by_line[line_id]
        assignment = assignment_by_environment[environment["id"]]
        step_id = f"CSTEP-{line_index:03d}"
        root_fact_id = f"CF-ROOT-{line_index:03d}"
        output_fact_id = f"CF-OUT-{line_index:03d}"
        actor_binding_id = f"AAB-{line_index:03d}"
        occurrence_id = f"COR-{line_index:03d}"
        # A storyline participant is not automatically the holder of every
        # real-world permission exposed by its environment.  Formal authored
        # proposals may therefore name the exact functional actor and the
        # exact W1 authority sources for this bounded capability.  The legacy
        # defaults remain unchanged for the generic contract fixtures.
        spec = environment_specs.get(
            next(
                demand["id"]
                for demand in demands
                if demand["id"] in environment["storyline_stage_ids"]
            ),
            {},
        )
        actor_slot_id = str(
            spec.get("capability_actor_slot_id", line["actor_slot_ids"][0])
        )
        authority_source_ids = copy.deepcopy(
            spec.get("capability_authority_source_ids", assignment["evidence_ids"])
        )
        capability_constraints = [
            str(item) for item in spec.get("capability_constraints", [])
        ]
        capability_modes = [
            str(item)
            for item in spec.get(
                "capability_supported_modes",
                ["enact", "observe", "communicate", "constrain"],
            )
        ]
        capability_repeatability = str(
            spec.get("capability_repeatability", "repeatable")
        )
        facts.extend(
            [
                {
                    "id": root_fact_id,
                    "kind": "story_state_anchor",
                    "statement": line["start_state"],
                    "statement_sha256": runtime.canonical_sha256(
                        line["start_state"]
                    ),
                    "source_anchor": {
                        "source_kind": "s1_story_state",
                        "source_artifact": copy.deepcopy(s1_source_artifact),
                        "source_pointer": f"/storylines/{storyline_index[line_id]}/start_state",
                        "value_sha256": runtime.canonical_sha256(
                            line["start_state"]
                        ),
                        "storyline_id": line_id,
                        "state_index": 0,
                        "state_sha256": runtime.canonical_sha256(
                            line["start_state"]
                        ),
                    },
                    "root_policy": "root_allowed",
                    "producer_semantics": "none",
                    "producer_step_ids": [],
                    "producer_transition_keys": [],
                    "consumer_step_ids": [step_id],
                    "cross_line_dependency": None,
                    "constraints": ["This is sealed initial context, not an event."],
                },
                {
                    "id": output_fact_id,
                    "kind": "capability_output",
                    "statement": f"The bounded interface for {line_id} can emit a local capability output.",
                    "statement_sha256": runtime.canonical_sha256(
                        f"The bounded interface for {line_id} can emit a local capability output."
                    ),
                    "source_anchor": {
                        "source_kind": "s1_story_state",
                        "source_artifact": copy.deepcopy(s1_source_artifact),
                        "source_pointer": f"/storylines/{storyline_index[line_id]}/start_state",
                        "value_sha256": runtime.canonical_sha256(line["start_state"]),
                        "storyline_id": line_id,
                        "state_index": 0,
                        "state_sha256": runtime.canonical_sha256(line["start_state"]),
                    },
                    "root_policy": "producer_required",
                    "producer_semantics": "exactly_one",
                    "producer_step_ids": [step_id],
                    "producer_transition_keys": [],
                    "consumer_step_ids": [],
                    "cross_line_dependency": None,
                    "constraints": ["T1 must choose whether and when the output occurs."],
                },
            ]
        )
        actor_claim_id = "CLAIM-E1-AUTH-" + runtime.canonical_sha256(
            [actor_binding_id, authority_source_ids, affordance["allowed_actions"]]
        )[:20]
        actor_bindings.append(
            {
                "id": actor_binding_id,
                "actor_slot_id": actor_slot_id,
                "world_authority_source_ids": authority_source_ids,
                "semantic_review_claim_id": actor_claim_id,
                "e1_access_assignment_id": assignment["id"],
                "environment_id": environment["id"],
                "permitted_actions": copy.deepcopy(affordance["allowed_actions"]),
                "requires_token_fact_ids": [],
                "produces_token_fact_ids": [],
                "forbidden_token_kinds": [],
                "scope_constraints": [
                    *copy.deepcopy(assignment["constraints"]),
                    *capability_constraints,
                ],
            }
        )
        steps.append(
            {
                "id": step_id,
                "environment_id": environment["id"],
                "zone_id": environment["zone_ids"][0],
                "affordance_id": affordance["id"],
                "action": affordance["allowed_actions"][0],
                "actor_slot_ids": [actor_slot_id],
                "actor_authority_binding_ids": [actor_binding_id],
                "requires_fact_ids": [root_fact_id],
                "produces_fact_ids": [output_fact_id],
                "requires_token_kinds": [],
                "produces_token_kinds": [],
                "forbidden_token_kinds": [],
                "supported_modes": capability_modes,
                "repeatability": capability_repeatability,
                "source_ids": [line_id, event_by_line[line_id]["id"]],
                "constraints": [
                    *copy.deepcopy(affordance["constraints"]),
                    *capability_constraints,
                ],
            }
        )
        occurrences.append(
            {
                "id": occurrence_id,
                "step_id": step_id,
                "minimum_occurrences": 1,
                "maximum_occurrences": None,
                "distinct_group_id": f"GROUP-{line_index:03d}",
                "share_policy": "shareable",
                "allowed_shared_requirement_ids": [],
                "source_ids": [event_by_line[line_id]["id"]],
                "objective_atomicity_basis": "One local interface may support successive transitions; T1 must instantiate each required occurrence.",
                "semantic_review_claim_id": "CLAIM-E1-OCC-"
                + runtime.canonical_sha256([occurrence_id, line_id])[:20],
            }
        )
        descriptor = {
            "support_kind": "process_host",
            "environment_ids": [environment["id"]],
            "required_modes": [capability_modes[0]],
            "required_fact_kinds": ["story_state_anchor"],
            "topology_requirement": "none",
            "authority_required": True,
            "resource_constraints": copy.deepcopy(environment["resources"]),
            "boundary_constraints": [
                "The option exposes capacity only; it does not classify or schedule an event."
            ],
        }
        source_ids = [line_id, event_by_line[line_id]["id"]]
        option_id, demand_id, option_claim_id = e1._v24_initial_option_ids(
            storyline_id=line_id,
            descriptor=descriptor,
            source_ids=source_ids,
        )
        initial_anchors.append(
            {
                "storyline_id": line_id,
                "state_index": 0,
                "state": line["start_state"],
                "state_sha256": runtime.canonical_sha256(line["start_state"]),
                "support_options": [
                    {
                        "support_option_id": option_id,
                        "capability_demand_id": demand_id,
                        "capability_descriptor": descriptor,
                        "source_ids": source_ids,
                        "semantic_review_claim_id": option_claim_id,
                    }
                ],
                "source_ids": [line_id],
            }
        )
        option_by_line[line_id] = (option_id, demand_id, option_claim_id, descriptor)
        step_by_line[line_id] = step_id
        root_fact_by_line[line_id] = root_fact_id
        output_fact_by_line[line_id] = output_fact_id
        occurrence_by_line[line_id] = occurrence_id
        states = e1._storyline_states(line)
        for state_index, (left, right) in enumerate(zip(states, states[1:])):
            transition_id_v24 = f"TRS-{line_index:03d}-{state_index:03d}"
            key = e1._transition_key(line_id, state_index)
            transition_support.append(
                {
                    "id": transition_id_v24,
                    "storyline_id": line_id,
                    "from_state_index": state_index,
                    "to_state_index": state_index + 1,
                    "from_state": left,
                    "to_state": right,
                    "event_requirement_ids": [event_by_line[line_id]["id"]],
                    "support_claims": [
                        {
                            "step_id": step_id,
                            "support_mode": capability_modes[0],
                            "source_ids": [line_id, event_by_line[line_id]["id"]],
                            "boundary": "The step can enact a bounded change but does not assert that the story transition occurs.",
                        }
                    ],
                    "required_fact_ids": [root_fact_id],
                    "occurrence_requirement_ids": [occurrence_id],
                    "ambient_context_host_ids": [],
                    "semantic_review_claim_ids": [
                        "CLAIM-E1-TRS-" + runtime.canonical_sha256(key)[:20]
                    ],
                }
            )
            transition_support_by_key[(line_id, state_index)] = transition_id_v24

    def anchor_support_id(anchor: Mapping[str, object]) -> str:
        line_id = str(anchor["storyline_id"])
        state_index = int(anchor["state_index"])
        return (
            option_by_line[line_id][0]
            if state_index == 0
            else transition_support_by_key[(line_id, state_index - 1)]
        )

    connection_readiness = []
    for connection_index, connection in enumerate(storyline["connections"], 1):
        source_line = connection["from_storyline_id"]
        target_line = connection["to_storyline_id"]
        source_env = environment_by_line[source_line]["id"]
        target_env = environment_by_line[target_line]["id"]
        causal = connection["relation"] == "causal"
        source_endpoint_step_id = step_by_line[source_line]
        source_occurrence_id = occurrence_by_line[source_line]
        target_endpoint_step_id = step_by_line[target_line]
        target_occurrence_id = occurrence_by_line[target_line]
        transfer_fact_id = None
        if causal:
            base_source_step = next(
                item for item in steps if item["id"] == step_by_line[source_line]
            )
            source_endpoint_step_id = f"CSTEP-CONN-SRC-{connection_index:03d}"
            transfer_fact_id = f"CF-CONN-{connection_index:03d}"
            source_step = copy.deepcopy(base_source_step)
            source_step["id"] = source_endpoint_step_id
            source_step["produces_fact_ids"] = [transfer_fact_id]
            source_step["source_ids"] = [connection["id"], source_line]
            source_step["constraints"] = [
                *base_source_step["constraints"],
                "This producer is available only at the declared causal source anchor.",
            ]
            steps.append(source_step)
            source_line_record = next(
                item for item in storyline["storylines"] if item["id"] == source_line
            )
            source_states = e1._storyline_states(source_line_record)
            source_state_index = connection["from_state_index"]
            source_pointer = (
                f"/storylines/{storyline_index[source_line]}/start_state"
                if source_state_index == 0
                else f"/storylines/{storyline_index[source_line]}/end_state"
                if source_state_index == len(source_states) - 1
                else f"/storylines/{storyline_index[source_line]}/state_changes/{source_state_index - 1}"
            )
            source_transition_key = (
                None
                if source_state_index == 0
                else e1._transition_key(source_line, source_state_index - 1)
            )
            target_transition_key = (
                None
                if connection["to_state_index"] == 0
                else e1._transition_key(
                    target_line, connection["to_state_index"] - 1
                )
            )
            facts.append(
                {
                    "id": transfer_fact_id,
                    "kind": "capability_output",
                    "statement": f"The source endpoint for {connection['id']} can emit its bounded transfer.",
                    "statement_sha256": runtime.canonical_sha256(
                        f"The source endpoint for {connection['id']} can emit its bounded transfer."
                    ),
                    "source_anchor": {
                        "source_kind": "s1_story_state",
                        "source_artifact": copy.deepcopy(s1_source_artifact),
                        "source_pointer": source_pointer,
                        "value_sha256": runtime.canonical_sha256(
                            source_states[source_state_index]
                        ),
                        "storyline_id": source_line,
                        "state_index": source_state_index,
                        "state_sha256": runtime.canonical_sha256(
                            source_states[source_state_index]
                        ),
                    },
                    "root_policy": (
                        "producer_required"
                        if source_state_index == 0
                        else "t1_predecessor_required"
                    ),
                    "producer_semantics": "exactly_one",
                    "producer_step_ids": [source_endpoint_step_id],
                    "producer_transition_keys": (
                        [] if source_transition_key is None else [source_transition_key]
                    ),
                    "consumer_step_ids": [],
                    "cross_line_dependency": (
                        {
                            "source_transition_key": source_transition_key,
                            "consumer_transition_key": target_transition_key,
                            "precedence_status": "structurally_precedes",
                            "s1_precedence_edge_ids": [connection["id"]],
                        }
                        if source_transition_key is not None
                        and target_transition_key is not None
                        else None
                    ),
                    "constraints": [
                        "T1 must instantiate the source occurrence before the target can consume the transfer."
                    ],
                }
            )
            for fact_id in source_step["requires_fact_ids"]:
                required_fact = next(item for item in facts if item["id"] == fact_id)
                if source_endpoint_step_id not in required_fact["consumer_step_ids"]:
                    required_fact["consumer_step_ids"].append(source_endpoint_step_id)
            if source_state_index > 0:
                source_transition = next(
                    item
                    for item in transition_support
                    if item["storyline_id"] == source_line
                    and item["from_state_index"] == source_state_index - 1
                )
                source_transition["support_claims"].append(
                    {
                        "step_id": source_endpoint_step_id,
                        "support_mode": (
                            "communicate"
                            if "communicate" in source_step["supported_modes"]
                            else source_step["supported_modes"][0]
                        ),
                        "source_ids": [connection["id"], source_line],
                        "boundary": "This endpoint exposes only the declared source-anchor transfer.",
                    }
                )
            source_occurrence_id = f"COR-CONN-SRC-{connection_index:03d}"
            occurrences.append(
                {
                    "id": source_occurrence_id,
                    "step_id": source_endpoint_step_id,
                    "minimum_occurrences": 1,
                    "maximum_occurrences": 1,
                    "distinct_group_id": f"GROUP-CONN-SRC-{connection_index:03d}",
                    "share_policy": "exclusive",
                    "allowed_shared_requirement_ids": [],
                    "source_ids": [connection["id"], source_line],
                    "objective_atomicity_basis": "The causal transfer has one declared source occurrence.",
                    "semantic_review_claim_id": "CLAIM-E1-OCC-CONN-SRC-"
                    + runtime.canonical_sha256(connection["id"])[:20],
                }
            )
            base_target_step = next(
                item for item in steps if item["id"] == step_by_line[target_line]
            )
            target_endpoint_step_id = f"CSTEP-CONN-TGT-{connection_index:03d}"
            target_step = copy.deepcopy(base_target_step)
            target_step["id"] = target_endpoint_step_id
            target_step["requires_fact_ids"] = list(
                dict.fromkeys(
                    [*base_target_step["requires_fact_ids"], transfer_fact_id]
                )
            )
            target_step["produces_fact_ids"] = []
            target_step["source_ids"] = [connection["id"], target_line]
            target_step["constraints"] = [
                *base_target_step["constraints"],
                "This endpoint step is used only when the causal connection reaches its target anchor.",
            ]
            steps.append(target_step)
            if connection["to_state_index"] > 0:
                target_transition_id = transition_support_by_key[
                    (target_line, connection["to_state_index"] - 1)
                ]
                target_transition = next(
                    item
                    for item in transition_support
                    if item["id"] == target_transition_id
                )
                target_transition["support_claims"].append(
                    {
                        "step_id": target_endpoint_step_id,
                        "support_mode": (
                            "enact"
                            if "enact" in target_step["supported_modes"]
                            else target_step["supported_modes"][0]
                        ),
                        "source_ids": [connection["id"], target_line],
                        "boundary": "This endpoint can enact only the target-anchor-local handoff; it does not establish earlier target-line states.",
                    }
                )
                if transfer_fact_id not in target_transition["required_fact_ids"]:
                    target_transition["required_fact_ids"].append(transfer_fact_id)
            for fact_id in target_step["requires_fact_ids"]:
                required_fact = next(item for item in facts if item["id"] == fact_id)
                if target_endpoint_step_id not in required_fact["consumer_step_ids"]:
                    required_fact["consumer_step_ids"].append(target_endpoint_step_id)
            transfer_fact = next(item for item in facts if item["id"] == transfer_fact_id)
            if target_endpoint_step_id not in transfer_fact["consumer_step_ids"]:
                transfer_fact["consumer_step_ids"].append(target_endpoint_step_id)
            target_occurrence_id = f"COR-CONN-TGT-{connection_index:03d}"
            occurrences.append(
                {
                    "id": target_occurrence_id,
                    "step_id": target_endpoint_step_id,
                    "minimum_occurrences": 1,
                    "maximum_occurrences": 1,
                    "distinct_group_id": f"GROUP-CONN-TGT-{connection_index:03d}",
                    "share_policy": "exclusive",
                    "allowed_shared_requirement_ids": [],
                    "source_ids": [connection["id"], target_line],
                    "objective_atomicity_basis": "This occurrence exists only for the connection target endpoint and cannot stand in for the line's earlier transitions.",
                    "semantic_review_claim_id": "CLAIM-E1-OCC-CONN-"
                    + runtime.canonical_sha256(connection["id"])[:20],
                }
            )
        connection_readiness.append(
            {
                "connection_id": connection["id"],
                "relation": connection["relation"],
                "source_endpoint_step_ids": [source_endpoint_step_id],
                "target_endpoint_step_ids": [target_endpoint_step_id],
                "transfer_fact_id": transfer_fact_id,
                "transport_step_ids": [],
                "topology_path_ids": (
                    topology_path(
                        {"environment_topology": topology}, source_env, target_env
                    )
                    if causal and source_env != target_env
                    else []
                ),
                "occurrence_requirement_ids": (
                    [source_occurrence_id, target_occurrence_id]
                    if causal
                    else []
                ),
                "semantic_review_claim_ids": [
                    "CLAIM-E1-CONN-"
                    + runtime.canonical_sha256(connection["id"])[:20]
                ],
            }
        )
    milestone_readiness = []
    for milestone in storyline["temporal_architecture"]["milestones"]:
        support_ids = [anchor_support_id(item) for item in milestone["state_refs"]]
        milestone_readiness.append(
            {
                "milestone_id": milestone["id"],
                "order": milestone["order"],
                "phase_id": milestone["phase_id"],
                "storyline_ids": copy.deepcopy(milestone["storyline_ids"]),
                "state_refs": copy.deepcopy(milestone["state_refs"]),
                "connection_ids": copy.deepcopy(milestone["connection_ids"]),
                "transition_support_ids": [
                    item for item in support_ids if item.startswith("TRS-")
                ],
                "initial_support_option_ids": [
                    item for item in support_ids if item.startswith("IAO-")
                ],
                "connection_readiness_ids": copy.deepcopy(
                    milestone["connection_ids"]
                ),
                "occurrence_requirement_ids": sorted(
                    {
                        occurrence_by_line[item["storyline_id"]]
                        for item in milestone["state_refs"]
                        if item["state_index"] > 0
                    }
                ),
            }
        )
    obligation_readiness = []
    obligation_occurrence_bindings = []
    for obligation in storyline["story_obligation_register"]:
        antecedents = [anchor_support_id(item) for item in obligation["antecedent_anchors"]]
        consequent = anchor_support_id(obligation["consequent_anchor"])
        line_id = obligation["consequent_anchor"]["storyline_id"]
        step_id = step_by_line[line_id]
        occurrence_id = "COR-OBL-" + runtime.canonical_sha256(
            [obligation["id"], step_id]
        )[:20]
        occurrences.append(
            {
                "id": occurrence_id,
                "step_id": step_id,
                "minimum_occurrences": 1,
                "maximum_occurrences": 1,
                "distinct_group_id": "GROUP-OBL-" + runtime.canonical_sha256(
                    obligation["id"]
                )[:16],
                "share_policy": "exclusive",
                "allowed_shared_requirement_ids": [],
                "source_ids": [obligation["id"]],
                "objective_atomicity_basis": "This obligation owns one bounded path occurrence even when its local step is shared.",
                "semantic_review_claim_id": "CLAIM-E1-OCC-OBL-"
                + runtime.canonical_sha256(obligation["id"])[:20],
            }
        )
        obligation_readiness.append(
            {
                "obligation_id": obligation["id"],
                "kind": obligation["kind"],
                "antecedent_support_ids": antecedents,
                "consequent_support_ids": [consequent],
                "required_fact_ids": [
                    root_fact_by_line[line_id], output_fact_by_line[line_id]
                ],
                "required_step_ids": [step_id],
                "occurrence_requirement_ids": [occurrence_id],
                "allowed_disclosure_fact_ids": [],
                "forbidden_disclosure_fact_ids": [],
                "readiness_mode": "direct_path",
                "semantic_review_claim_ids": [
                    "CLAIM-E1-OBL-"
                    + runtime.canonical_sha256(obligation["id"])[:20]
                ],
            }
        )
        binding_id = e1._v24_obligation_occurrence_binding_id(
            obligation_id=obligation["id"],
            occurrence_id=occurrence_id,
            step_id=step_id,
            support_id=consequent,
        )
        obligation_occurrence_bindings.append(
            {
                "id": binding_id,
                "obligation_id": obligation["id"],
                "occurrence_requirement_id": occurrence_id,
                "step_id": step_id,
                "support_id": consequent,
            }
        )
    initial_realizations = []
    for line_id, (option_id, demand_id, claim_id, descriptor) in option_by_line.items():
        environment = environment_by_line[line_id]
        realization_id = "IAR-" + runtime.canonical_sha256(option_id)[:20]
        initial_connection_steps = {
            step_id
            for connection, readiness in zip(
                storyline["connections"], connection_readiness
            )
            for step_id in (
                readiness["source_endpoint_step_ids"]
                if connection["from_storyline_id"] == line_id
                and connection["from_state_index"] == 0
                else readiness["target_endpoint_step_ids"]
                if connection["to_storyline_id"] == line_id
                and connection["to_state_index"] == 0
                else []
            )
        }
        initial_step_ids = sorted(
            {step_by_line[line_id], *initial_connection_steps}
        )
        initial_realizations.append(
            {
                "id": realization_id,
                "storyline_id": line_id,
                "state_index": 0,
                "support_option_id": option_id,
                "capability_demand_id": demand_id,
                "descriptor_sha256": runtime.canonical_sha256(descriptor),
                "capability_fact_ids": sorted(
                    {
                        fact_id
                        for step in steps
                        if step["id"] in initial_step_ids
                        for fact_id in step["requires_fact_ids"]
                    }
                ),
                "capability_step_ids": initial_step_ids,
                "ambient_context_host_ids": [],
                "topology_path_ids": [],
                "realized_environment_ids": [environment["id"]],
                "semantic_review_claim_id": claim_id,
                "status": "ready",
            }
        )
    for transition in transition_support:
        support_step_ids = {
            claim["step_id"] for claim in transition["support_claims"]
        }
        transition["required_fact_ids"] = sorted(
            {
                fact_id
                for step in steps
                if step["id"] in support_step_ids
                for fact_id in step["requires_fact_ids"]
            }
        )
    for fact in facts:
        fact["producer_transition_keys"] = sorted(
            {
                e1._transition_key(
                    transition["storyline_id"], transition["from_state_index"]
                )
                for transition in transition_support
                if any(
                    fact["id"] in step["produces_fact_ids"]
                    for step in steps
                    if step["id"]
                    in {claim["step_id"] for claim in transition["support_claims"]}
                )
            }
        )
    owned_ids.extend(
        [
            *[item["id"] for item in facts],
            *[item["id"] for item in steps],
            *[item["id"] for item in actor_bindings],
            *[item["id"] for item in occurrences],
            *[item["id"] for item in obligation_occurrence_bindings],
            *[item["id"] for item in transition_support],
            *[item["id"] for item in initial_realizations],
            *[option[0] for option in option_by_line.values()],
            *[option[1] for option in option_by_line.values()],
        ]
    )

    projection_objects = {
        **{item["id"]: item for item in environments},
        **{item["id"]: item for item in affordances},
    }
    for claim in derivations:
        claim["value_sha256"] = runtime.canonical_sha256(
            projection_objects[claim["projection_ids"][0]]
        )

    locked = [
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    ]
    open_controls = [
        item
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    ]
    model = {
        "schema_version": "2.4",
        "skill": "novel-environment-system-designer",
        "stage": "E1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": owned_ids,
            "downstream_freedom": [
                item["id"] for item in storyline["event_requirements"]
            ],
            "author_open": [item["id"] for item in open_controls],
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "environment_demands": demands,
        "storyline_environment_requirements": storyline_environment_requirements,
        "environments": environments,
        "functional_zones": zones,
        "environment_topology": topology,
        "access_and_authority": assignments,
        "resource_and_information_channels": channels,
        "hazards_and_failure_modes": hazards,
        "storyline_hosting_ledger": hosting,
        "event_affordance_catalog": affordances,
        "transition_contracts": transitions,
        "initial_anchor_support": initial_anchors,
        "capability_fact_registry": facts,
        "capability_step_registry": steps,
        "ambient_context_hosts": [],
        "actor_authority_bindings": actor_bindings,
        "capability_occurrence_requirements": occurrences,
        "story_transition_support": transition_support,
        "connection_path_readiness": connection_readiness,
        "milestone_capability_readiness": milestone_readiness,
        "obligation_capability_readiness": obligation_readiness,
        "obligation_occurrence_bindings": obligation_occurrence_bindings,
        "initial_anchor_option_realization_ledger": initial_realizations,
        "open_items": [
            {
                "id": f"OPEN-E1-{index:03d}",
                "question": f"Preserve author-open control {item['id']}.",
                "source_ids": [item["id"]],
                "status": "author_open",
            }
            for index, item in enumerate(open_controls, 1)
        ],
    }
    model.update(e1._v24_expected_universe_digests(model, storyline))
    return model


def topology_path(
    model: dict[str, object], source_id: str, target_id: str
) -> list[str]:
    pending = [(source_id, [])]
    visited = set()
    while pending:
        current, path = pending.pop(0)
        if current == target_id:
            return path
        if current in visited:
            continue
        visited.add(current)
        for edge in model["environment_topology"]:
            if current not in (edge["from_id"], edge["to_id"]):
                continue
            next_id = (
                edge["to_id"] if edge["from_id"] == current else edge["from_id"]
            )
            if next_id not in visited:
                pending.append((next_id, [*path, edge["id"]]))
    raise AssertionError(f"no topology path from {source_id} to {target_id}")


class TriggerBindingRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storyline = {
            "storylines": [
                {
                    "id": line_id,
                    "type": line_type,
                    "start_state": "start",
                    "state_changes": ["middle"],
                    "end_state": "end",
                }
                for line_id, line_type in (
                    ("SL-A", "supporting"),
                    ("SL-B", "supporting"),
                    ("SL-C", "main"),
                )
            ],
            "connections": [
                {
                    "id": "SLC-A-C",
                    "relation": "causal",
                    "from_storyline_id": "SL-A",
                    "from_state_index": 0,
                    "to_storyline_id": "SL-C",
                    "to_state_index": 1,
                },
                {
                    "id": "SLC-A-C-2",
                    "relation": "causal",
                    "from_storyline_id": "SL-A",
                    "from_state_index": 1,
                    "to_storyline_id": "SL-C",
                    "to_state_index": 2,
                },
                {
                    "id": "SLC-B-C-ASSOC",
                    "relation": "associative",
                    "from_storyline_id": "SL-B",
                    "from_state_index": 0,
                    "to_storyline_id": "SL-C",
                    "to_state_index": 1,
                },
            ],
            "story_obligation_register": [
                {
                    "id": "SOB-ALL-C",
                    "kind": "requires_all",
                    "antecedent_anchors": [
                        {"storyline_id": "SL-A", "state_index": 0},
                        {"storyline_id": "SL-B", "state_index": 0},
                    ],
                    "consequent_anchor": {
                        "storyline_id": "SL-C",
                        "state_index": 1,
                    },
                }
            ],
        }
        self.environments = {
            "ENV-A": {"id": "ENV-A", "storyline_stage_ids": ["SL-A"]},
            "ENV-B": {"id": "ENV-B", "storyline_stage_ids": ["SL-B"]},
            "ENV-C": {"id": "ENV-C", "storyline_stage_ids": ["SL-C"]},
        }
        self.topology = {
            "TOP-A-B": {
                "id": "TOP-A-B", "from_id": "ENV-A", "to_id": "ENV-B",
                "directionality": "forward", "transfer_capabilities": ["signal"],
            },
            "TOP-B-C": {
                "id": "TOP-B-C", "from_id": "ENV-B", "to_id": "ENV-C",
                "directionality": "forward", "transfer_capabilities": ["signal"],
            },
        }
        self.assignments = {
            f"ACCESS-{suffix}": {"id": f"ACCESS-{suffix}", "subject_id": f"ENV-{suffix}"}
            for suffix in ("A", "B", "C")
        }
        self.affordances = {
            line_id.replace("SL", "AFF"): {
                "id": line_id.replace("SL", "AFF"),
                "environment_id": line_id.replace("SL", "ENV"),
                "event_requirement_ids": [line_id.replace("SL", "EVD")],
            }
            for line_id in ("SL-A", "SL-B", "SL-C")
        }
        self.event_lines = {
            "EVD-A": "SL-A",
            "EVD-B": "SL-B",
            "EVD-C": "SL-C",
        }
        self.transition = {
            "id": "TRANS-C",
            "subject_id": "ENV-C",
            "trigger_ids": ["AFF-A"],
            "allowed_by_ids": ["ACCESS-A", "ACCESS-C"],
            "trigger_bindings": [
                {
                    "trigger_id": "AFF-A",
                    "source_environment_id": "ENV-A",
                    "source_storyline_id": "SL-A",
                    "source_state_index": 0,
                    "target_storyline_id": "SL-C",
                    "target_state_index": 1,
                    "causal_evidence_ids": ["SLC-A-C"],
                    "topology_path_ids": ["TOP-A-B", "TOP-B-C"],
                    "transport_capability": "signal",
                }
            ],
        }

    def validate(self, transition=None, *, final=True, storyline=None) -> None:
        e1._validate_transition_trigger_bindings(
            [transition or self.transition],
            environments=self.environments,
            topology=self.topology,
            assignments=self.assignments,
            affordances=self.affordances if final else None,
            storyline=storyline or self.storyline,
            event_requirement_line=self.event_lines if final else None,
        )

    def test_cross_environment_multihop_causal_binding_passes(self) -> None:
        self.validate()

    def test_forward_trigger_is_allowed_in_phase3_but_must_resolve_finally(self) -> None:
        transition = copy.deepcopy(self.transition)
        transition["trigger_ids"] = ["AFF-FORWARD"]
        transition["trigger_bindings"][0]["trigger_id"] = "AFF-FORWARD"
        self.validate(transition, final=False)
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition)
        self.assertEqual("E1_TRANSITION_TRIGGER_INVALID", caught.exception.code)

    def test_trigger_set_and_binding_set_must_match(self) -> None:
        transition = copy.deepcopy(self.transition)
        transition["trigger_ids"] = ["AFF-B"]
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition, final=False)
        self.assertEqual(
            "E1_TRANSITION_TRIGGER_BINDING_MISMATCH", caught.exception.code
        )

    def test_not_before_does_not_invent_a_strict_precedence_edge(self) -> None:
        storyline = copy.deepcopy(self.storyline)
        storyline["story_obligation_register"].append(
            {
                "id": "SOB-NOT-BEFORE-SAME-TICK",
                "kind": "not_before",
                "antecedent_anchors": [
                    {"storyline_id": "SL-A", "state_index": 1}
                ],
                "consequent_anchor": {
                    "storyline_id": "SL-B", "state_index": 1
                },
            }
        )
        _transitions, edges, adjacency = e1._s1_structural_precedence(storyline)
        self.assertNotIn("SOB-NOT-BEFORE-SAME-TICK#0", edges)
        self.assertFalse(
            e1._s1_reachable("SL-A:0->1", "SL-B:0->1", adjacency)
        )

    def test_state_zero_endpoint_uses_all_initial_option_realizations_order_independently(self) -> None:
        realizations = [
            {
                "storyline_id": "SL-A",
                "capability_step_ids": ["CSTEP-BASE"],
            },
            {
                "storyline_id": "SL-A",
                "capability_step_ids": ["CSTEP-STATE0-ENDPOINT"],
            },
            {
                "storyline_id": "SL-B",
                "capability_step_ids": ["CSTEP-FOREIGN"],
            },
        ]
        expected = {"CSTEP-BASE", "CSTEP-STATE0-ENDPOINT"}
        self.assertEqual(
            e1._v24_initial_realization_step_ids(
                realizations, storyline_id="SL-A"
            ),
            expected,
        )
        self.assertEqual(
            e1._v24_initial_realization_step_ids(
                list(reversed(realizations)), storyline_id="SL-A"
            ),
            expected,
        )

    def test_cross_environment_path_is_explicit_continuous_and_acyclic(self) -> None:
        for path in ([], ["TOP-B-C"], ["TOP-A-B", "TOP-A-B", "TOP-B-C"]):
            transition = copy.deepcopy(self.transition)
            transition["trigger_bindings"][0]["topology_path_ids"] = path
            with self.subTest(path=path), self.assertRaises(e1.E1Error) as caught:
                self.validate(transition, final=False)
            self.assertEqual("E1_TRIGGER_TOPOLOGY_PATH_INVALID", caught.exception.code)

    def test_topology_path_enforces_direction_and_exact_capability(self) -> None:
        reverse = copy.deepcopy(self.transition)
        binding = reverse["trigger_bindings"][0]
        reverse["subject_id"] = "ENV-A"
        reverse["allowed_by_ids"] = ["ACCESS-A", "ACCESS-C"]
        binding.update(
            {
                "source_environment_id": "ENV-C",
                "source_storyline_id": "SL-C",
                "source_state_index": 1,
                "target_storyline_id": "SL-A",
                "target_state_index": 0,
                "causal_evidence_ids": [],
                "topology_path_ids": ["TOP-B-C", "TOP-A-B"],
            }
        )
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(reverse, final=False)
        self.assertEqual("E1_TRIGGER_TOPOLOGY_PATH_INVALID", caught.exception.code)

        bidirectional_topology = copy.deepcopy(self.topology)
        for edge in bidirectional_topology.values():
            edge["directionality"] = "bidirectional"
        e1._validate_topology_path(
            ["TOP-B-C", "TOP-A-B"],
            source_environment_id="ENV-C",
            target_environment_id="ENV-A",
            transport_capability="signal",
            topology=bidirectional_topology,
            transition_id="TRANS-REVERSE",
        )
        wrong_capability = copy.deepcopy(self.transition)
        wrong_capability["trigger_bindings"][0]["transport_capability"] = "cargo"
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(wrong_capability, final=False)
        self.assertEqual("E1_TRIGGER_TOPOLOGY_PATH_INVALID", caught.exception.code)

    def test_binding_permissions_cover_source_and_target_environments(self) -> None:
        for allowed in (
            ["ACCESS-C"],
            ["ACCESS-A"],
            ["ACCESS-B"],
        ):
            transition = copy.deepcopy(self.transition)
            transition["allowed_by_ids"] = allowed
            with self.subTest(allowed=allowed), self.assertRaises(e1.E1Error) as caught:
                self.validate(transition, final=False)
            self.assertEqual(
                "E1_TRIGGER_PERMISSION_COVERAGE_INVALID", caught.exception.code
            )

    def test_local_binding_uses_one_local_permission(self) -> None:
        transition = {
            "id": "TRANS-C-LOCAL-PASS",
            "subject_id": "ENV-C",
            "trigger_ids": ["AFF-C"],
            "allowed_by_ids": ["ACCESS-C"],
            "trigger_bindings": [
                {
                    "trigger_id": "AFF-C",
                    "source_environment_id": "ENV-C",
                    "source_storyline_id": "SL-C",
                    "source_state_index": 0,
                    "target_storyline_id": "SL-C",
                    "target_state_index": 1,
                    "causal_evidence_ids": [],
                    "topology_path_ids": [],
                    "transport_capability": "local",
                }
            ],
        }
        self.validate(transition)

    def test_associative_connection_is_not_causal_evidence(self) -> None:
        transition = copy.deepcopy(self.transition)
        binding = transition["trigger_bindings"][0]
        binding.update(
            {
                "trigger_id": "AFF-B",
                "source_environment_id": "ENV-B",
                "source_storyline_id": "SL-B",
                "causal_evidence_ids": ["SLC-B-C-ASSOC"],
                "topology_path_ids": ["TOP-B-C"],
            }
        )
        transition["trigger_ids"] = ["AFF-B"]
        transition["allowed_by_ids"] = ["ACCESS-B", "ACCESS-C"]
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition, final=False)
        self.assertEqual("E1_TRIGGER_CAUSAL_EVIDENCE_INVALID", caught.exception.code)

    def test_requires_all_needs_every_antecedent(self) -> None:
        transition = copy.deepcopy(self.transition)
        first = transition["trigger_bindings"][0]
        first["causal_evidence_ids"] = ["SOB-ALL-C"]
        second = {
            "trigger_id": "AFF-B",
            "source_environment_id": "ENV-B",
            "source_storyline_id": "SL-B",
            "source_state_index": 0,
            "target_storyline_id": "SL-C",
            "target_state_index": 1,
            "causal_evidence_ids": ["SOB-ALL-C"],
            "topology_path_ids": ["TOP-B-C"],
            "transport_capability": "signal",
        }
        transition["trigger_ids"] = ["AFF-A", "AFF-B"]
        transition["allowed_by_ids"] = ["ACCESS-A", "ACCESS-B", "ACCESS-C"]
        transition["trigger_bindings"].append(second)
        self.validate(transition)
        transition["trigger_ids"] = ["AFF-A"]
        transition["trigger_bindings"] = [first]
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition, final=False)
        self.assertEqual("E1_TRIGGER_REQUIRES_ALL_INCOMPLETE", caught.exception.code)

    def test_optional_source_cannot_drive_non_optional_target(self) -> None:
        storyline = copy.deepcopy(self.storyline)
        storyline["storylines"][0]["type"] = "optional_melody"
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(final=False, storyline=storyline)
        self.assertEqual("E1_OPTIONAL_TRIGGER_ESCALATION", caught.exception.code)

    def test_same_trigger_allows_multiple_states_but_not_mixed_environments(self) -> None:
        transition = copy.deepcopy(self.transition)
        second = copy.deepcopy(transition["trigger_bindings"][0])
        second.update(
            {
                "source_state_index": 1,
                "target_state_index": 2,
                "causal_evidence_ids": ["SLC-A-C-2"],
            }
        )
        transition["trigger_bindings"].append(second)
        self.validate(transition)
        second["source_environment_id"] = "ENV-B"
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition, final=False)
        self.assertEqual(
            "E1_TRANSITION_TRIGGER_BINDING_MISMATCH", caught.exception.code
        )

    def test_same_line_binding_cannot_run_backward(self) -> None:
        transition = {
            "id": "TRANS-C-LOCAL",
            "subject_id": "ENV-C",
            "trigger_ids": ["AFF-C"],
            "trigger_bindings": [
                {
                    "trigger_id": "AFF-C",
                    "source_environment_id": "ENV-C",
                    "source_storyline_id": "SL-C",
                    "source_state_index": 1,
                    "target_storyline_id": "SL-C",
                    "target_state_index": 0,
                    "causal_evidence_ids": [],
                    "topology_path_ids": [],
                    "transport_capability": "local",
                }
            ],
            "allowed_by_ids": ["ACCESS-C"],
        }
        with self.assertRaises(e1.E1Error) as caught:
            self.validate(transition, final=False)
        self.assertEqual("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", caught.exception.code)

    def test_legacy_schema_cannot_be_generated(self) -> None:
        with self.assertRaises(e1.E1Error) as caught:
            e1._require_generation_schema({"schema_version": "2.0"})
        self.assertEqual("E1_LEGACY_GENERATION_FORBIDDEN", caught.exception.code)


class EnvironmentSchemaCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        contract_runtime = runtime.ContractRuntime()
        root = contract_runtime.load_schema("environment-system.schema.json")
        contract_runtime.check_all_schemas()
        cls.validator = Draft202012Validator(
            {
                "$schema": root["$schema"],
                "$id": root["$id"],
                "type": "object",
                "required": [
                    "schema_version", "storyline_hosting_ledger",
                    "environment_topology", "transition_contracts"
                ],
                "properties": {
                    "schema_version": root["properties"]["schema_version"],
                    "storyline_hosting_ledger": {"type": "array", "minItems": 1},
                    "environment_topology": {"type": "array"},
                    "transition_contracts": {"type": "array", "minItems": 1},
                },
                "allOf": root["allOf"],
                "$defs": root["$defs"],
            },
            registry=contract_runtime._registry,
        )

    @staticmethod
    def legacy() -> dict[str, object]:
        return {
            "schema_version": "2.0",
            "storyline_hosting_ledger": [
                {
                    "id": "COV-E1-A", "source_ids": ["END-W", "END-S"],
                    "realization_ids": ["ENV-A"], "status": "covered",
                    "evidence": "legacy literal evidence",
                }
            ],
            "environment_topology": [
                {
                    "id": "TOP-A-B", "from_id": "ENV-A", "to_id": "ENV-B",
                    "relation": "passage", "mechanism": "door",
                    "constraints": ["permission required"],
                }
            ],
            "transition_contracts": [
                {
                    "id": "TRANS-A", "subject_id": "ENV-A",
                    "from_state": "open", "trigger_ids": ["AFF-A"],
                    "to_state": "closed", "allowed_by_ids": ["ACCESS-A"],
                    "consequence": "access changes",
                }
            ],
        }

    @staticmethod
    def previous_current() -> dict[str, object]:
        model = EnvironmentSchemaCompatibilityTests.legacy()
        model["schema_version"] = "2.1"
        model["environment_topology"][0].update(
            {
                "directionality": "forward",
                "transfer_capabilities": ["signal"],
            }
        )
        model["transition_contracts"][0]["trigger_bindings"] = [
            {
                "trigger_id": "AFF-A",
                "source_environment_id": "ENV-A",
                "source_storyline_id": "SL-A",
                "source_state_index": 0,
                "target_storyline_id": "SL-A",
                "target_state_index": 0,
                "causal_evidence_ids": [],
                "topology_path_ids": [],
                "transport_capability": "local",
            }
        ]
        return model

    @staticmethod
    def current() -> dict[str, object]:
        model = EnvironmentSchemaCompatibilityTests.previous_current()
        model["schema_version"] = "2.3"
        model["storyline_hosting_ledger"][0]["evidence"] = {
            "source_bindings": [
                {
                    "source_id": "END-W",
                    "source_kind": "world_environment_demand",
                    "storyline_id": "SL-A",
                    "responsibility_sha256": "a" * 64,
                    "constraint_sha256s": ["b" * 64],
                },
                {
                    "source_id": "END-S",
                    "source_kind": "storyline_environment_requirement",
                    "storyline_id": "SL-A",
                    "responsibility_sha256": "c" * 64,
                    "constraint_sha256s": ["d" * 64],
                },
            ],
            "realization_bindings": [
                {
                    "environment_id": "ENV-A",
                    "local_projections": [
                        {
                            "source_id": "END-W",
                            "token_kind": "responsibility",
                            "token_sha256": "a" * 64,
                            "environment_pointer": "/scope",
                            "projection_sha256": "e" * 64,
                            "rationale": "local projection",
                        }
                    ],
                }
            ],
        }
        return model

    def test_legacy_2_0_2_1_2_2_and_2_3_shapes_are_valid(self) -> None:
        self.assertEqual([], list(self.validator.iter_errors(self.legacy())))
        self.assertEqual(
            [], list(self.validator.iter_errors(self.previous_current()))
        )
        structured_legacy = self.current()
        structured_legacy["schema_version"] = "2.2"
        self.assertEqual([], list(self.validator.iter_errors(structured_legacy)))
        self.assertEqual([], list(self.validator.iter_errors(self.current())))

    def test_versions_cannot_mix_transition_topology_or_hosting_shapes(self) -> None:
        legacy_with_new = self.current()
        legacy_with_new["schema_version"] = "2.0"
        current_with_old = self.legacy()
        current_with_old["schema_version"] = "2.3"
        previous_with_new_hosting = self.current()
        previous_with_new_hosting["schema_version"] = "2.1"
        self.assertTrue(list(self.validator.iter_errors(legacy_with_new)))
        self.assertTrue(list(self.validator.iter_errors(current_with_old)))
        self.assertTrue(list(self.validator.iter_errors(previous_with_new_hosting)))


class CapabilityAffordanceLineUnitTests(unittest.TestCase):
    def test_step_affordance_lines_are_exact_not_environment_hosting(self) -> None:
        steps = {
            "CSTEP-PUBLIC-VERIFY": {
                "affordance_id": "AFF-BASE-GOVERNANCE"
            }
        }
        affordances = {
            "AFF-BASE-GOVERNANCE": {
                "event_requirement_ids": ["EVD-INSTITUTIONAL"]
            }
        }
        requirement_lines = {
            "EVD-INSTITUTIONAL": "SL-INSTITUTIONAL",
            "EVD-EVIDENCE": "SL-EVIDENCE",
        }
        self.assertEqual(
            {"SL-INSTITUTIONAL"},
            e1._v24_step_affordance_lines(
                "CSTEP-PUBLIC-VERIFY",
                steps=steps,
                affordances=affordances,
                event_requirement_line=requirement_lines,
            ),
        )
        self.assertNotIn(
            "SL-EVIDENCE",
            e1._v24_step_affordance_lines(
                "CSTEP-PUBLIC-VERIFY",
                steps=steps,
                affordances=affordances,
                event_requirement_line=requirement_lines,
            ),
        )
        affordances["AFF-BASE-GOVERNANCE"]["event_requirement_ids"].append(
            "EVD-EVIDENCE"
        )
        self.assertEqual(
            {"SL-INSTITUTIONAL", "SL-EVIDENCE"},
            e1._v24_step_affordance_lines(
                "CSTEP-PUBLIC-VERIFY",
                steps=steps,
                affordances=affordances,
                event_requirement_line=requirement_lines,
            ),
        )


class AffordanceCatalogContractTests(unittest.TestCase):
    def test_one_evd_is_usable_in_two_same_line_hosting_environments(self) -> None:
        environments = {
            "ENV-FIELD": {
                "id": "ENV-FIELD",
                "allowed_actions": ["secure source", "leave field"],
            },
            "ENV-MEMORY": {
                "id": "ENV-MEMORY",
                "allowed_actions": ["attempt read", "seal failed read"],
            },
        }
        catalog = [
            {
                "id": "AFF-FIELD-EVD-A",
                "environment_id": "ENV-FIELD",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["secure source", "leave field"],
                "prerequisites": ["field custody is active"],
                "constraints": ["preserve evidence"],
            },
            {
                "id": "AFF-MEMORY-EVD-A",
                "environment_id": "ENV-MEMORY",
                "event_requirement_ids": ["EVD-A"],
                "allowed_actions": ["attempt read", "seal failed read"],
                "prerequisites": ["read authorization is active"],
                "constraints": ["preserve evidence"],
            },
        ]
        result = e1._validate_affordance_catalog(
            catalog,
            environments=environments,
            event_requirements={"EVD-A": {"id": "EVD-A"}},
            event_requirement_line={"EVD-A": "SL-A"},
            hosted_lines_by_environment={
                "ENV-FIELD": {"SL-A"},
                "ENV-MEMORY": {"SL-A"},
            },
            model_version="2.3",
        )
        self.assertEqual({"AFF-FIELD-EVD-A", "AFF-MEMORY-EVD-A"}, set(result))

    def test_current_contract_rejects_foreign_wrong_line_and_zero_coverage(
        self,
    ) -> None:
        base = {
            "id": "AFF-A",
            "environment_id": "ENV-A",
            "event_requirement_ids": ["EVD-A"],
            "allowed_actions": ["local action"],
            "prerequisites": ["local prerequisite"],
            "constraints": ["local constraint"],
        }
        kwargs = {
            "environments": {
                "ENV-A": {"id": "ENV-A", "allowed_actions": ["local action"]}
            },
            "event_requirements": {
                "EVD-A": {"id": "EVD-A"},
                "EVD-B": {"id": "EVD-B"},
            },
            "event_requirement_line": {"EVD-A": "SL-A", "EVD-B": "SL-B"},
            "hosted_lines_by_environment": {"ENV-A": {"SL-A"}},
            "model_version": "2.3",
        }
        foreign = copy.deepcopy(base)
        foreign["allowed_actions"].append("foreign action")
        wrong_line = copy.deepcopy(base)
        wrong_line["id"] = "AFF-WRONG-LINE"
        wrong_line["event_requirement_ids"] = ["EVD-B"]
        for candidate, code in (
            ([foreign, {**base, "id": "AFF-B", "event_requirement_ids": ["EVD-B"]}], "E1_ACTION_INTERFACE_FOREIGN"),
            ([wrong_line, base], "E1_AFFORDANCE_LINE_MISMATCH"),
            ([base], "E1_ACTION_INTERFACE_MISSING"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(e1.E1Error) as caught:
                    e1._validate_affordance_catalog(candidate, **kwargs)
                self.assertEqual(code, caught.exception.code)


class HostingClosureUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.demand = {
            "id": "END-W1-A",
            "responsibility": "Carry the governed operation.",
            "constraints": ["Authorized staff only.", "Keep the late key sealed."],
        }
        self.requirement = {
            "id": "END-S1-A",
            "responsibility": "Carry the complete storyline movement.",
            "constraints": ["Do not disclose the hidden choice."],
        }
        self.environments = {
            "ENV-EARLY": {
                "id": "ENV-EARLY",
                "scope": "An early controlled room.",
                "narrative_responsibility": "Own the initial local interface.",
                "features": ["A local intake surface."],
                "sensory_conditions": ["Access status is visible."],
                "access_rules": ["Authorized staff only."],
                "resources": ["An intake console."],
                "allowed_actions": ["Record an intake."],
                "hazards": ["A failed check blocks intake."],
                "blockers": ["No verified credential."],
                "state_vocabulary": ["open", "closed"],
            },
            "ENV-FINAL": {
                "id": "ENV-FINAL",
                "scope": "A final controlled room.",
                "narrative_responsibility": "Own the terminal local interface.",
                "features": ["A bounded confirmation surface."],
                "sensory_conditions": ["Confirmation state is visible."],
                "access_rules": ["A second authorization is required."],
                "resources": ["A confirmation console."],
                "allowed_actions": ["Confirm a bounded operation."],
                "hazards": ["Keep the late key sealed."],
                "blockers": ["Do not disclose the hidden choice."],
                "state_vocabulary": ["pending", "confirmed"],
            },
        }
        source_bindings = [
            e1._hosting_source_binding(
                self.demand,
                source_kind="world_environment_demand",
                storyline_id="SL-A",
            ),
            e1._hosting_source_binding(
                self.requirement,
                source_kind="storyline_environment_requirement",
                storyline_id="SL-A",
            ),
        ]
        locations = {
            (self.demand["id"], "responsibility"): ("ENV-EARLY", "/features/0"),
            (
                self.demand["id"],
                runtime.canonical_sha256("Authorized staff only."),
            ): ("ENV-EARLY", "/access_rules/0"),
            (
                self.demand["id"],
                runtime.canonical_sha256("Keep the late key sealed."),
            ): ("ENV-FINAL", "/hazards/0"),
            (self.requirement["id"], "responsibility"): (
                "ENV-FINAL",
                "/features/0",
            ),
            (
                self.requirement["id"],
                runtime.canonical_sha256("Do not disclose the hidden choice."),
            ): ("ENV-FINAL", "/blockers/0"),
        }
        realization_projections = {"ENV-EARLY": [], "ENV-FINAL": []}
        for binding in source_bindings:
            tokens = [
                ("responsibility", binding["responsibility_sha256"]),
                *[("constraint", value) for value in binding["constraint_sha256s"]],
            ]
            for kind, token_sha256 in tokens:
                lookup = (
                    binding["source_id"],
                    "responsibility" if kind == "responsibility" else token_sha256,
                )
                environment_id, pointer = locations[lookup]
                local_value = e1._resolve_hosting_projection(
                    self.environments[environment_id], pointer
                )
                realization_projections[environment_id].append(
                    {
                        "source_id": binding["source_id"],
                        "token_kind": kind,
                        "token_sha256": token_sha256,
                        "environment_pointer": pointer,
                        "projection_sha256": runtime.canonical_sha256(local_value),
                        "rationale": "This local value operationalizes the exact token.",
                    }
                )
        self.record = {
            "id": "COV-E1-A",
            "source_ids": [self.demand["id"], self.requirement["id"]],
            "realization_ids": ["ENV-EARLY", "ENV-FINAL"],
            "status": "covered",
            "evidence": {
                "source_bindings": source_bindings,
                "realization_bindings": [
                    {
                        "environment_id": environment_id,
                        "local_projections": realization_projections[environment_id],
                    }
                    for environment_id in ("ENV-EARLY", "ENV-FINAL")
                ],
            },
        }

    def validate(self, record=None, environments=None) -> None:
        e1._validate_structured_hosting_evidence(
            record or self.record,
            demand=self.demand,
            storyline_requirement=self.requirement,
            storyline_id="SL-A",
            environments=environments or self.environments,
        )

    def test_hosting_validator_keeps_full_closure_in_one_function_body(self) -> None:
        tree = ast.parse(inspect.getsource(e1._validate_structured_hosting_evidence))
        function = tree.body[0]
        self.assertIsInstance(function, ast.FunctionDef)
        nested_functions = [
            node
            for node in ast.walk(function)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node is not function
        ]
        self.assertEqual([], nested_functions)
        calls = {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("_hosting_source_binding", calls)
        self.assertIn("_resolve_hosting_projection", calls)

    def test_clean_multi_realization_closure_passes_and_late_constraint_is_local(self) -> None:
        e1._validate_environment_source_text_clean(
            self.environments, [self.demand, self.requirement]
        )
        self.validate()
        self.assertNotIn(
            "Keep the late key sealed.",
            runtime.canonical_json(self.environments["ENV-EARLY"]),
        )
        self.assertIn(
            "Keep the late key sealed.",
            self.environments["ENV-FINAL"]["hazards"],
        )

    def test_missing_or_changed_constraint_token_is_rejected(self) -> None:
        missing = copy.deepcopy(self.record)
        final = missing["evidence"]["realization_bindings"][1]["local_projections"]
        final.pop()
        with self.assertRaisesRegex(e1.E1Error, "E1_SOURCE_MEANING_UNBOUND"):
            self.validate(missing)
        changed = copy.deepcopy(self.record)
        changed["evidence"]["source_bindings"][0]["constraint_sha256s"][0] = "0" * 64
        with self.assertRaisesRegex(e1.E1Error, "E1_SOURCE_MEANING_UNBOUND"):
            self.validate(changed)

    def test_wrong_realization_or_pointer_is_rejected(self) -> None:
        dangling = copy.deepcopy(self.record)
        dangling["realization_ids"][0] = "ENV-MISSING"
        dangling["evidence"]["realization_bindings"][0]["environment_id"] = "ENV-MISSING"
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_ENVIRONMENT_DANGLING"):
            self.validate(dangling)
        wrong_pointer = copy.deepcopy(self.record)
        projection = wrong_pointer["evidence"]["realization_bindings"][0]["local_projections"][0]
        projection["environment_pointer"] = "/features/999"
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_LOCAL_PROJECTION_INVALID"):
            self.validate(wrong_pointer)

    def test_field_sensitive_pollution_gate_is_strict_but_not_overstrict(self) -> None:
        # An exact short constraint is a legitimate local access rule.
        e1._validate_environment_source_text_clean(
            self.environments, [self.demand, self.requirement]
        )
        responsibility_dump = copy.deepcopy(self.environments)
        responsibility_dump["ENV-EARLY"]["features"].append(
            self.demand["responsibility"]
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION"):
            e1._validate_environment_source_text_clean(
                responsibility_dump, [self.demand, self.requirement]
            )
        descriptive_constraint_dump = copy.deepcopy(self.environments)
        descriptive_constraint_dump["ENV-EARLY"]["features"].append(
            self.requirement["constraints"][0]
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION"):
            e1._validate_environment_source_text_clean(
                descriptive_constraint_dump, [self.demand, self.requirement]
            )
        wrapped_constraint_dump = copy.deepcopy(self.environments)
        wrapped_constraint_dump["ENV-EARLY"]["features"].append(
            "Copied upstream text: "
            + self.requirement["constraints"][0]
            + " End copy."
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION"):
            e1._validate_environment_source_text_clean(
                wrapped_constraint_dump, [self.demand, self.requirement]
            )
        foreign_dump = copy.deepcopy(self.environments)
        foreign_dump["ENV-EARLY"]["scope"] += " " + self.requirement["responsibility"]
        with self.assertRaisesRegex(e1.E1Error, "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION"):
            e1._validate_environment_source_text_clean(
                foreign_dump, [self.demand, self.requirement]
            )
        action_trace_dump = copy.deepcopy(self.environments)
        action_trace_dump["ENV-EARLY"]["features"].append(
            "[ACTION_SHA256:" + ("a" * 64) + "]"
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION"):
            e1._validate_environment_source_text_clean(
                action_trace_dump, [self.demand, self.requirement]
            )

    def test_review_envelope_rejects_same_thread_duplicate_and_failed_generic_mapping(self) -> None:
        request = {
            "review_protocol": e1.LEGACY_HOSTING_REVIEW_PROTOCOL,
            "producer_thread_id": "producer",
            "run_id": "run",
            "session_id": "session",
            "candidate_sha256": "a" * 64,
            "claims": [{"id": "HSC-A"}, {"id": "HSC-B"}],
            "records": [{"id": "COV-E1-A"}],
        }
        passing = {
            "claim_verdicts": [
                {"claim_id": item, "verdict": "pass", "rationale": "Concrete local projection."}
                for item in ("HSC-A", "HSC-B")
            ],
            "record_verdicts": [
                {
                    "record_id": "COV-E1-A",
                    "checks": {name: "pass" for name in e1._HOSTING_RECORD_REVIEW_CHECKS},
                    "rationale": "The complete record is coherent and non-generic.",
                }
            ],
        }
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_REVIEW_THREAD_INVALID"):
            e1._normalize_hosting_review(
                root=Path.cwd(),
                request=request,
                reviewer_thread_id="producer",
                review=passing,
                request_reference={"path": "request.json", "sha256": "b" * 64},
            )
        duplicate = copy.deepcopy(passing)
        duplicate["claim_verdicts"][1]["claim_id"] = "HSC-A"
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_REVIEW_COVERAGE_MISMATCH"):
            e1._normalize_hosting_review(
                root=Path.cwd(),
                request=request,
                reviewer_thread_id="reviewer",
                review=duplicate,
                request_reference={"path": "request.json", "sha256": "b" * 64},
            )
        generic_fail = copy.deepcopy(passing)
        generic_fail["record_verdicts"][0]["checks"]["pointer_reuse_coherence"] = "fail"
        record = e1._normalize_hosting_review(
            root=Path.cwd(),
            request=request,
            reviewer_thread_id="reviewer",
            review=generic_fail,
            request_reference={"path": "request.json", "sha256": "b" * 64},
        )
        self.assertEqual("fail", record["verdict"])


class HistoricalPackageCompatibilityTests(unittest.TestCase):
    package = (
        Path(__file__).resolve().parents[3]
        / "projects"
        / "duanxian"
        / "conception-runs"
        / "duanxian-conception-v2-20260803-04"
        / "E1"
    )
    package_2_3 = (
        Path(__file__).resolve().parents[3]
        / "projects"
        / "duanxian"
        / "conception-runs"
        / "duanxian-conception-v2-20260811-18"
        / "E1"
    )

    @unittest.skipUnless(package.is_dir(), "historical 2.0 package unavailable")
    def test_trusted_historical_2_0_package_remains_read_only_valid(self) -> None:
        self.assertEqual("ready", e1.validate_e1_package(self.package)["verdict"])

    @unittest.skipUnless(package_2_3.is_dir(), "historical 2.3 package unavailable")
    def test_trusted_historical_2_3_package_remains_read_only_valid(self) -> None:
        self.assertEqual("ready", e1.validate_e1_package(self.package_2_3)["verdict"])

    @unittest.skipUnless(package_2_3.is_dir(), "historical 2.3 package unavailable")
    def test_preserved_old_implementation_cannot_authorize_resealed_2_3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            mutant = Path(directory) / "E1"
            shutil.copytree(self.package_2_3, mutant)
            model_path = mutant / "environment-system.json"
            model = json.loads(model_path.read_text(encoding="utf-8"))
            model["run_id"] += "-resealed"
            model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
            manifest_path = mutant / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            replacement = runtime.artifact_reference(model_path, root=mutant)
            manifest["files"] = [
                replacement if item["path"] == "environment-system.json" else item
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
            with self.assertRaises(e1.E1Error) as caught:
                e1.validate_e1_package(mutant)
            self.assertEqual(
                "E1_LEGACY_PACKAGE_IDENTITY_UNTRUSTED", caught.exception.code
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
        self.run_id = "run-rebuilt-upstream-paths"

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
        before = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            b0_ref,
            e1._sealed_upstream_reference(
                b0_root,
                b0_ref,
                stage="B0",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.runtime,
            ),
        )
        self.assertEqual(
            s1_ref,
            e1._sealed_upstream_reference(
                s1_root,
                s1_ref,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.runtime,
            ),
        )
        physical_w1_root = w1_root
        if os.name == "nt":
            physical_w1_root = Path("\\\\?\\" + str(w1_root.resolve()))
        self.assertEqual(
            w1_ref,
            e1._sealed_upstream_reference(
                physical_w1_root,
                w1_ref,
                stage="W1",
                run_id=self.run_id,
                previous_stage_completions=[s1_ref],
                runtime=self.runtime,
            ),
        )
        after = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_foreign_sibling_stale_hash_and_previous_chain_fail_closed(self) -> None:
        s1_root, s1_ref = self._package(
            "S1", "workspaces/S1-attempt-03/package", []
        )
        foreign = copy.deepcopy(s1_ref)
        foreign["path"] = "foreign/S1/stage-completion.json"
        with self.assertRaises(e1.E1Error) as caught:
            e1._sealed_upstream_reference(
                s1_root,
                foreign,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.runtime,
            )
        self.assertEqual("E1_S1_INVALID", caught.exception.code)

        stale = copy.deepcopy(s1_ref)
        stale["sha256"] = "0" * 64
        with self.assertRaises(e1.E1Error) as caught:
            e1._sealed_upstream_reference(
                s1_root,
                stale,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.runtime,
            )
        self.assertEqual("E1_S1_INVALID", caught.exception.code)

        with self.assertRaises(e1.E1Error) as caught:
            e1._sealed_upstream_reference(
                s1_root,
                s1_ref,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[s1_ref],
                runtime=self.runtime,
            )
        self.assertEqual("E1_S1_INVALID", caught.exception.code)


class E1RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shared_temporary = tempfile.TemporaryDirectory()
        cls.shared = Path(cls.shared_temporary.name)
        cls.sources = baseline_test.SourceFixture(cls.shared / "sources")
        coordinator = runtime.AutonomousCoordinator.initialize(
            run_id=cls.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": runtime.sha256_file(cls.sources.state),
            },
            state_path="state/revision-000.json",
        )
        b0_gate = coordinator.build_input_gate("B0", "B0/input-gate.json")
        cls.shared_b0 = cls.shared / "run" / "B0"
        runtime.build_baseline_package(
            **cls.sources.build_args(cls.shared_b0, b0_gate)
        )
        runtime.complete_b0(
            cls.shared_b0,
            coordinator=coordinator,
            input_gate=b0_gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )
        baseline = json.loads(
            (cls.shared_b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )

        s1_gate = coordinator.build_input_gate("S1", "S1/input-gate.json")
        cls.shared_s1 = cls.shared / "run" / "S1"
        s1_workspace = cls.shared / "workspace" / "S1"
        controls = s1._controls(cls.shared_b0, baseline)
        s1_sources = [
            {
                "path": f"sources/B0/{name}",
                "sha256": runtime.sha256_file(cls.shared_b0 / name),
            }
            for name in (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ]
        s1_model = s1_test.agent_proposal(
            run_id=cls.sources.run_id,
            gate_reference=s1_gate.reference,
            source_artifacts=s1_sources,
            controls=controls,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-shared-s1"}, clear=False
        ):
            s1.start_s1_session(
                s1_workspace,
                baseline_package=cls.shared_b0,
                input_gate=s1_gate,
            )
            cls._submit(
                s1,
                s1_workspace,
                cls.shared_b0,
                None,
                None,
                s1_gate,
                s1_model,
                "final-storyline-model",
            )
            s1.run_s1(
                cls.shared_s1,
                baseline_package=cls.shared_b0,
                coordinator=coordinator,
                input_gate=s1_gate,
                controlled_workspace=s1_workspace,
                logical_package_path="S1",
                next_state_path="state/revision-002.json",
            )

        storyline = json.loads(
            (cls.shared_s1 / "storyline-architecture.json").read_text(
                encoding="utf-8"
            )
        )
        w1_gate = coordinator.build_input_gate("W1", "W1/input-gate.json")
        cls.shared_w1 = cls.shared / "run" / "W1"
        w1_workspace = cls.shared / "workspace" / "W1"
        w1_sources = [
            *[
                {
                    "path": f"sources/B0/{name}",
                    "sha256": runtime.sha256_file(cls.shared_b0 / name),
                }
                for name in (
                    "author-control-baseline.json",
                    "package-manifest.json",
                    "stage-completion.json",
                )
            ],
            *[
                {
                    "path": f"sources/S1/{name}",
                    "sha256": runtime.sha256_file(cls.shared_s1 / name),
                }
                for name in (
                    "storyline-architecture.json",
                    "package-manifest.json",
                    "stage-completion.json",
                )
            ],
        ]
        w1_model = w1_test.agent_world_proposal(
            run_id=cls.sources.run_id,
            gate_reference=w1_gate.reference,
            source_artifacts=w1_sources,
            baseline=baseline,
            storyline=storyline,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-shared-w1"}, clear=False
        ):
            w1.start_w1_session(
                w1_workspace,
                baseline_package=cls.shared_b0,
                storyline_package=cls.shared_s1,
                input_gate=w1_gate,
            )
            cls._submit(
                w1,
                w1_workspace,
                cls.shared_b0,
                cls.shared_s1,
                None,
                w1_gate,
                w1_model,
                "final-world-model",
            )
            w1.run_w1(
                cls.shared_w1,
                baseline_package=cls.shared_b0,
                storyline_package=cls.shared_s1,
                coordinator=coordinator,
                input_gate=w1_gate,
                controlled_workspace=w1_workspace,
                logical_package_path="W1",
                next_state_path="state/revision-003.json",
            )
        cls.coordinator_state = coordinator.state
        cls.coordinator_reference = coordinator.state_reference

    @classmethod
    def _submit(
        cls,
        module,
        workspace,
        b0,
        s1_package,
        w1_package,
        gate,
        model,
        final_phase,
    ) -> None:
        for phase in module.PHASES:
            payload = (
                {"model": model}
                if phase == final_phase
                else {
                    field: model[field] for field in module.PHASE_FIELDS[phase]
                }
            )
            kwargs = {
                "baseline_package": b0,
                "input_gate": gate,
                "phase": phase,
                "payload": payload,
            }
            if s1_package is not None:
                kwargs["storyline_package"] = s1_package
            if w1_package is not None:
                kwargs["world_package"] = w1_package
            getattr(module, f"submit_{module.__name__.split('.')[-3].split('-')[0]}_phase", None)
            if module is s1:
                if phase == "line-design":
                    request = s1.start_s1_line_claim_review(
                        workspace,
                        baseline_package=b0,
                        input_gate=gate,
                        payload=payload,
                    )
                    review = {
                        "claim_verdicts": [
                            {
                                "claim_id": claim_id,
                                "verdict": "pass",
                                "rationale": "Fixture claim matches its declared source authority.",
                            }
                            for claim_id in request["claim_ids"]
                        ],
                        "source_sequence_verdicts": [
                            {
                                "realization_id": item["id"],
                                "source_unit_id": item["source_unit_id"],
                                "verdict": "pass",
                                "rationale": "Fixture realization preserves its declared ordered source.",
                            }
                            for item in request["candidate"]["source_sequence_realizations"]
                        ],
                    }
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-e1-fixture-line-review"},
                        clear=False,
                    ):
                        s1.submit_s1_line_claim_review(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review=review,
                        )
                if phase == "topology-and-consistency":
                    request = s1.start_s1_topology_semantic_review(
                        workspace,
                        baseline_package=b0,
                        input_gate=gate,
                        payload=payload,
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-e1-fixture-topology-review"},
                        clear=False,
                    ):
                        s1.submit_s1_topology_semantic_review(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            verdicts=s1_test.passing_topology_verdicts(request),
                        )
                module.submit_s1_phase(workspace, **kwargs)
            elif module is w1:
                module.submit_w1_phase(workspace, **kwargs)
            else:
                if phase == "zones-and-topology":
                    request = e1.start_e1_authority_semantic_review(
                        workspace,
                        baseline_package=b0,
                        storyline_package=s1_package,
                        world_package=w1_package,
                        input_gate=gate,
                        payload=payload,
                    )
                    review = {
                        "claim_verdicts": [
                            {
                                "claim_id": item["id"],
                                "verdict": "pass",
                                "rationale": "The sealed upstream pointers support this bounded capability interpretation.",
                            }
                            for item in request["claims"]
                        ],
                        "reviewer_task_receipt": {
                            "task_id": "fixture-authority-review",
                            "output_sha256": runtime.canonical_sha256(request),
                        },
                    }
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-e1-authority-reviewer"},
                        clear=False,
                    ):
                        review["reviewer_task_receipt"] = (
                            e1.seal_e1_review_task_output(
                                workspace,
                                candidate_sha256=request["candidate_sha256"],
                                review_kind=request["review_kind"],
                                task_id="fixture-authority-review",
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
                if phase == "storyline-hosting-test":
                    request = e1.start_e1_hosting_semantic_review(
                        workspace,
                        baseline_package=b0,
                        storyline_package=s1_package,
                        world_package=w1_package,
                        input_gate=gate,
                        payload=payload,
                    )
                    review = {
                        "claim_verdicts": [
                            {
                                "claim_id": item["id"],
                                "verdict": "pass",
                                "rationale": (
                                    "The local value is a concrete, bounded "
                                    "projection of this exact source token."
                                ),
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
                                "rationale": (
                                    "The pair is same-line, locally coherent, "
                                    "non-generic, and uses pointers coherently."
                                ),
                            }
                            for item in request["records"]
                        ],
                        "reviewer_task_receipt": {
                            "task_id": "fixture-transition-review",
                            "output_sha256": runtime.canonical_sha256(request),
                        },
                    }
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-e1-hosting-reviewer"},
                        clear=False,
                    ):
                        review["reviewer_task_receipt"] = (
                            e1.seal_e1_review_task_output(
                                workspace,
                                candidate_sha256=request["candidate_sha256"],
                                review_kind=request["review_kind"],
                                task_id="fixture-transition-review",
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
                module.submit_e1_phase(workspace, **kwargs)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.shared_temporary.cleanup()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.b0 = self.work / "run" / "B0"
        self.s1 = self.work / "run" / "S1"
        self.w1 = self.work / "run" / "W1"
        shutil.copytree(self.shared_b0, self.b0)
        shutil.copytree(self.shared_s1, self.s1)
        shutil.copytree(self.shared_w1, self.w1)
        self.coordinator = runtime.AutonomousCoordinator.from_snapshot(
            self.coordinator_state, self.coordinator_reference
        )
        self.gate = self.coordinator.build_input_gate(
            "E1", "E1/input-gate.json"
        )
        self.package = self.work / "run" / "E1"
        self.workspace = self.work / "workspace" / "E1"
        self.baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        self.storyline = json.loads(
            (self.s1 / "storyline-architecture.json").read_text(encoding="utf-8")
        )
        self.world = json.loads(
            (self.w1 / "world-model.json").read_text(encoding="utf-8")
        )
        sources = e1._source_artifacts(self.b0, self.s1, self.w1)
        self.proposal = agent_environment_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=self.storyline,
            world=self.world,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-e1"}, clear=False
        ):
            e1.start_e1_session(
                self.workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
            )
            self._submit(
                e1,
                self.workspace,
                self.b0,
                self.s1,
                self.w1,
                self.gate,
                self.proposal,
                "final-environment-model",
            )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_e1(self) -> e1.E1RunReceipt:
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-e1"}, clear=False
        ):
            return e1.run_e1(
                self.package,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="E1",
                next_state_path="state/revision-004.json",
            )

    def _start_workspace(self, name: str) -> Path:
        workspace = self.work / "gate-workspaces" / name
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": f"thread-{name}"}, clear=False
        ):
            e1.start_e1_session(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
            )
        return workspace

    def _submit_current_phase(
        self,
        workspace: Path,
        phase: str,
        payload: Mapping[str, object],
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
            clear=False,
        ):
            e1.submit_e1_phase(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
                phase=phase,
                payload=payload,
            )

    def _seal_prefix(self, workspace: Path, count: int) -> None:
        for phase in e1.PHASES[:count]:
            payload = (
                {"model": copy.deepcopy(self.proposal)}
                if phase == "final-environment-model"
                else {
                    field: copy.deepcopy(self.proposal[field])
                    for field in e1.PHASE_FIELDS[phase]
                }
            )
            if phase == "storyline-hosting-test":
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
                    clear=False,
                ):
                    request = e1.start_e1_hosting_semantic_review(
                        workspace,
                        baseline_package=self.b0,
                        storyline_package=self.s1,
                        world_package=self.w1,
                        input_gate=self.gate,
                        payload=payload,
                    )
                review = {
                    "claim_verdicts": [
                        {
                            "claim_id": item["id"],
                            "verdict": "pass",
                            "rationale": "The bounded local projection matches this token.",
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
                            "rationale": "The pair is local, coherent, and non-generic.",
                        }
                        for item in request["records"]
                    ],
                    "reviewer_task_receipt": {
                        "task_id": f"transition-review-{workspace.name}",
                        "output_sha256": runtime.canonical_sha256(request),
                    },
                }
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": f"reviewer-{workspace.name}"},
                    clear=False,
                ):
                    review["reviewer_task_receipt"] = (
                        e1.seal_e1_review_task_output(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review_kind=request["review_kind"],
                            task_id=f"transition-review-{workspace.name}",
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
            if phase == "zones-and-topology":
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
                    clear=False,
                ):
                    request = e1.start_e1_authority_semantic_review(
                        workspace,
                        baseline_package=self.b0,
                        storyline_package=self.s1,
                        world_package=self.w1,
                        input_gate=self.gate,
                        payload=payload,
                    )
                review = {
                    "claim_verdicts": [
                        {
                            "claim_id": item["id"],
                            "verdict": "pass",
                            "rationale": "Sealed source meaning supports the bounded capability.",
                        }
                        for item in request["claims"]
                    ],
                    "reviewer_task_receipt": {
                        "task_id": f"authority-review-{workspace.name}",
                        "output_sha256": runtime.canonical_sha256(request),
                    },
                }
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": f"reviewer-authority-{workspace.name}"},
                    clear=False,
                ):
                    review["reviewer_task_receipt"] = (
                        e1.seal_e1_review_task_output(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review_kind=request["review_kind"],
                            task_id=f"authority-review-{workspace.name}",
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
            self._submit_current_phase(workspace, phase, payload)

    def _seal_custom_p3(
        self, workspace: Path, model: Mapping[str, object]
    ) -> None:
        for phase in e1.PHASES[:2]:
            self._submit_current_phase(
                workspace,
                phase,
                {
                    field: copy.deepcopy(model[field])
                    for field in e1.PHASE_FIELDS[phase]
                },
            )
        payload = {
            field: copy.deepcopy(model[field])
            for field in e1.PHASE_FIELDS["zones-and-topology"]
        }
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
            clear=False,
        ):
            request = e1.start_e1_authority_semantic_review(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
                payload=payload,
            )
        verdicts = [
            {
                "claim_id": item["id"],
                "verdict": "pass",
                "rationale": "The exact sealed source supports this bounded claim.",
            }
            for item in request["claims"]
        ]
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"reviewer-{workspace.name}"},
            clear=False,
        ):
            receipt = e1.seal_e1_review_task_output(
                workspace,
                candidate_sha256=request["candidate_sha256"],
                review_kind=request["review_kind"],
                task_id=f"authority-review-{workspace.name}",
                verdict_payload={"claim_verdicts": verdicts},
            )
            e1.submit_e1_authority_semantic_review(
                workspace,
                candidate_sha256=request["candidate_sha256"],
                review={
                    "claim_verdicts": verdicts,
                    "reviewer_task_receipt": receipt,
                },
            )
        self._submit_current_phase(workspace, "zones-and-topology", payload)

    def _model_with_ambient_option_source(
        self,
        *,
        option_line_index: int = 0,
        host_line_index: int | None = None,
        host_environment_line_index: int | None = None,
        source_mode: str = "icd",
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        model = copy.deepcopy(self.proposal)
        option_anchor = model["initial_anchor_support"][option_line_index]
        option = option_anchor["support_options"][0]
        host_anchor = model["initial_anchor_support"][
            option_line_index if host_line_index is None else host_line_index
        ]
        environment_anchor = model["initial_anchor_support"][
            (
                option_line_index if host_line_index is None else host_line_index
            )
            if host_environment_line_index is None
            else host_environment_line_index
        ]
        host_option = environment_anchor["support_options"][0]
        host_environment_id = host_option["capability_descriptor"][
            "environment_ids"
        ][0]
        host_environment = next(
            item
            for item in model["environments"]
            if item["id"] == host_environment_id
        )
        if host_anchor["storyline_id"] not in host_environment["storyline_stage_ids"]:
            host_environment["storyline_stage_ids"].append(
                host_anchor["storyline_id"]
            )
            environment_claim = next(
                item
                for item in model["derivation_claims"]
                if item["projection_ids"] == [host_environment_id]
            )
            environment_claim["value_sha256"] = runtime.canonical_sha256(
                host_environment
            )
        root_fact = next(
            item
            for item in model["capability_fact_registry"]
            if item["root_policy"] == "root_allowed"
            and item["source_anchor"].get("storyline_id")
            == host_anchor["storyline_id"]
        )
        actor = next(
            item
            for item in model["actor_authority_bindings"]
            if item["environment_id"] == host_environment_id
        )
        source_id = (
            option["support_option_id"]
            if source_mode == "iao"
            else "ICD-MISSING-FROM-P2"
            if source_mode == "missing"
            else option["capability_demand_id"]
        )
        source_ids = [option_anchor["storyline_id"], source_id]
        if source_mode == "duplicate-alias":
            source_ids.append(option["support_option_id"])
        host = {
            "id": "ACH-OPTION-SOURCE-"
            + runtime.canonical_sha256(
                [
                    option["support_option_id"],
                    host_anchor["storyline_id"],
                    host_environment_id,
                    source_mode,
                ]
            )[:16],
            "environment_id": host_environment_id,
            "zone_id": host_environment["zone_ids"][0],
            "storyline_id": host_anchor["storyline_id"],
            "host_kind": "bounded_internal_context",
            "subject_or_actor_slot_ids": [actor["actor_slot_id"]],
            "support_basis_fact_ids": [root_fact["id"]],
            "source_ids": source_ids,
            "constraints": [
                "The host exposes bounded initial capacity without asserting occurrence."
            ],
            "semantic_review_claim_id": "CLAIM-E1-AMBIENT-"
            + runtime.canonical_sha256(source_ids)[:20],
        }
        model["ambient_context_hosts"].append(host)
        model["authority_partition"]["autonomous_owned"].append(host["id"])
        return model, option, host

    def test_transition_review_binds_initial_option_sources_exactly(self) -> None:
        workspace = self._start_workspace("transition-review-option-source")
        model, option, host = self._model_with_ambient_option_source()
        self._seal_custom_p3(workspace, model)
        payload = {
            field: copy.deepcopy(model[field])
            for field in e1.PHASE_FIELDS["storyline-hosting-test"]
        }
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
            clear=False,
        ):
            request = e1.start_e1_hosting_semantic_review(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
                payload=payload,
            )
        claim = next(
            item for item in request["claims"] if item["record_id"] == host["id"]
        )
        binding = next(
            item
            for item in claim["source_bindings"]
            if item["source_id"] == option["capability_demand_id"]
        )
        phase2_path = (
            workspace
            / "generation-evidence/02-environment-architecture.json"
        )
        phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
        anchor_index = next(
            index
            for index, item in enumerate(
                phase2["payload"]["initial_anchor_support"]
            )
            if option in item["support_options"]
        )
        option_pointer = (
            f"/payload/initial_anchor_support/{anchor_index}/support_options/0"
        )
        self.assertEqual(option_pointer, binding["json_pointer"])
        self.assertEqual(runtime.canonical_sha256(option), binding["value_sha256"])
        self.assertEqual(
            runtime.artifact_reference(phase2_path, root=workspace),
            binding["source_artifact"],
        )

        # A stored request cannot drift either pointer or value hash away from
        # the deterministic request reconstructed from the sealed evidence.
        _candidate_path, request_path, _review_path = e1._semantic_review_paths(
            workspace,
            kind="transition",
            candidate_sha256=request["candidate_sha256"],
        )
        drifted = copy.deepcopy(request)
        drifted_binding = next(
            source
            for item in drifted["claims"]
            if item["record_id"] == host["id"]
            for source in item["source_bindings"]
            if source["source_id"] == option["capability_demand_id"]
        )
        drifted_binding["json_pointer"] += "/capability_demand_id"
        drifted_binding["value_sha256"] = "0" * 64
        e1._write(request_path, drifted)
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
            clear=False,
        ):
            with self.assertRaisesRegex(
                e1.E1Error, "E1_HOSTING_REVIEW_INVALID"
            ):
                e1.start_e1_hosting_semantic_review(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    world_package=self.w1,
                    input_gate=self.gate,
                    payload=payload,
                )

    def test_transition_review_rejects_invalid_ambient_option_sources_before_request(
        self,
    ) -> None:
        cases = (
            (
                "missing",
                {"source_mode": "missing"},
                "E1_TRANSITION_REVIEW_SOURCE_UNBOUND",
            ),
            (
                "foreign-storyline",
                {"host_line_index": 1},
                "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_INVALID",
            ),
            (
                "foreign-environment",
                {"host_environment_line_index": 1},
                "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_INVALID",
            ),
            (
                "duplicate-alias",
                {"source_mode": "duplicate-alias"},
                "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_DUPLICATE",
            ),
        )
        for name, parameters, expected_code in cases:
            with self.subTest(name=name):
                workspace = self._start_workspace(
                    f"transition-review-option-source-{name}"
                )
                model, _option, _host = self._model_with_ambient_option_source(
                    **parameters
                )
                self._seal_custom_p3(workspace, model)
                payload = {
                    field: copy.deepcopy(model[field])
                    for field in e1.PHASE_FIELDS["storyline-hosting-test"]
                }
                candidate_sha256 = runtime.canonical_sha256(payload)
                _candidate_path, request_path, _review_path = (
                    e1._semantic_review_paths(
                        workspace,
                        kind="transition",
                        candidate_sha256=candidate_sha256,
                    )
                )
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": f"thread-{workspace.name}"},
                    clear=False,
                ):
                    with self.assertRaises(e1.E1Error) as caught:
                        e1.start_e1_hosting_semantic_review(
                            workspace,
                            baseline_package=self.b0,
                            storyline_package=self.s1,
                            world_package=self.w1,
                            input_gate=self.gate,
                            payload=payload,
                        )
                self.assertEqual(expected_code, caught.exception.code)
                self.assertFalse(request_path.exists())

    def test_transition_review_rejects_initial_option_source_collision(self) -> None:
        workspace = self._start_workspace("transition-review-option-collision")
        model, _option, _host = self._model_with_ambient_option_source()
        self._seal_custom_p3(workspace, model)
        phase2_path = (
            workspace
            / "generation-evidence/02-environment-architecture.json"
        )
        phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
        anchors = phase2["payload"]["initial_anchor_support"]
        anchors[1]["support_options"][0]["capability_demand_id"] = anchors[0][
            "support_options"
        ][0]["capability_demand_id"]
        phase2["payload_sha256"] = runtime.canonical_sha256(phase2["payload"])
        e1._write(phase2_path, phase2)
        payload = {
            field: copy.deepcopy(model[field])
            for field in e1.PHASE_FIELDS["storyline-hosting-test"]
        }
        candidate_sha256 = runtime.canonical_sha256(payload)
        _candidate_path, request_path, _review_path = e1._semantic_review_paths(
            workspace,
            kind="transition",
            candidate_sha256=candidate_sha256,
        )
        session = json.loads(
            (workspace / "generation-session.json").read_text(encoding="utf-8")
        )
        with self.assertRaises(e1.E1Error) as caught:
            e1._expected_hosting_review_request(
                workspace,
                session=session,
                payload=payload,
                storyline=self.storyline,
                world=self.world,
            )
        self.assertEqual(
            "E1_TRANSITION_REVIEW_SOURCE_COLLISION", caught.exception.code
        )
        self.assertFalse(request_path.exists())

    def _install_passing_review_without_start(
        self,
        workspace: Path,
        payload: Mapping[str, object],
        *,
        storyline: Mapping[str, object] | None = None,
    ) -> None:
        session = json.loads(
            (workspace / "generation-session.json").read_text(encoding="utf-8")
        )
        candidate_sha256 = runtime.canonical_sha256(payload)
        candidate_path, request_path, review_path = e1._semantic_review_paths(
            workspace,
            kind="transition",
            candidate_sha256=candidate_sha256,
        )
        # The production request binds an on-disk candidate artifact.  This
        # helper intentionally bypasses only the public start API so phase
        # writer mutants can install a passing review for an invalid P4
        # candidate; it must still reproduce the real artifact ordering.
        e1._write(candidate_path, payload)
        request = e1._expected_hosting_review_request(
            workspace,
            session=session,
            payload=payload,
            storyline=storyline or self.storyline,
            world=self.world,
        )
        self.assertEqual(candidate_sha256, request["candidate_sha256"])
        e1._write(request_path, request)
        review_body = {
            "claim_verdicts": [
                {
                    "claim_id": item["id"],
                    "verdict": "pass",
                    "rationale": "The bounded local claim was reviewed.",
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
                    "rationale": "The transition-support record was reviewed as bounded and local.",
                }
                for item in request["records"]
            ],
            "reviewer_task_receipt": {
                "task_id": f"transition-review-{workspace.name}",
                "output_sha256": runtime.canonical_sha256(request),
            },
        }
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": f"independent-{workspace.name}"},
            clear=False,
        ):
            review_body["reviewer_task_receipt"] = (
                e1.seal_e1_review_task_output(
                    workspace,
                    candidate_sha256=request["candidate_sha256"],
                    review_kind=request["review_kind"],
                    task_id=f"transition-review-{workspace.name}",
                    verdict_payload={
                        "claim_verdicts": review_body["claim_verdicts"],
                        "record_verdicts": review_body["record_verdicts"],
                    },
                )
            )
            review = e1._normalize_hosting_review(
                root=workspace,
                request=request,
                reviewer_thread_id=f"independent-{workspace.name}",
                review=review_body,
                request_reference=runtime.artifact_reference(
                    request_path, root=workspace
                ),
            )
        e1._write(review_path, review)
        e1._seal_semantic_review_package(
            root=workspace,
            request=request,
            candidate_path=candidate_path,
            request_path=request_path,
            review_path=review_path,
        )

    def _validate(self, model: dict[str, object]) -> None:
        self._validate_with_storyline(model, self.storyline)

    def _validate_with_storyline(
        self, model: dict[str, object], storyline: dict[str, object]
    ) -> None:
        e1._validate_model(
            model,
            self.baseline,
            storyline,
            self.world,
            e1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=self.proposal["source_artifacts"],
        )

    def _cross_line_model(self) -> tuple[dict[str, object], dict[str, object]]:
        model = copy.deepcopy(self.proposal)
        connection = next(
            item
            for item in self.storyline["connections"]
            if item["relation"] == "causal"
        )
        lines = {item["id"] for item in self.storyline["storylines"]}
        event_line = {
            item["id"]: next(source for source in item["source_ids"] if source in lines)
            for item in self.storyline["event_requirements"]
        }
        environment_by_line = {
            line_id: environment
            for environment in model["environments"]
            for line_id in environment["storyline_stage_ids"]
            if line_id in lines
        }
        affordance_by_line = {
            event_line[requirement_id]: affordance
            for affordance in model["event_affordance_catalog"]
            for requirement_id in affordance["event_requirement_ids"]
        }
        source_environment = environment_by_line[connection["from_storyline_id"]]
        target_environment = environment_by_line[connection["to_storyline_id"]]
        source_affordance = affordance_by_line[connection["from_storyline_id"]]
        transition = next(
            item
            for item in model["transition_contracts"]
            if item["subject_id"] == target_environment["id"]
        )
        transition["trigger_ids"] = [source_affordance["id"]]
        source_access_id = next(
            item["id"]
            for item in model["access_and_authority"]
            if item["subject_id"] == source_environment["id"]
        )
        if source_access_id not in transition["allowed_by_ids"]:
            transition["allowed_by_ids"].append(source_access_id)
        transition["trigger_bindings"] = [
            {
                "trigger_id": source_affordance["id"],
                "source_environment_id": source_environment["id"],
                "source_storyline_id": connection["from_storyline_id"],
                "source_state_index": connection["from_state_index"],
                "target_storyline_id": connection["to_storyline_id"],
                "target_state_index": connection["to_state_index"],
                "causal_evidence_ids": [connection["id"]],
                "topology_path_ids": topology_path(
                    model, source_environment["id"], target_environment["id"]
                ),
                "transport_capability": (
                    "local"
                    if source_environment["id"] == target_environment["id"]
                    else "story-causality-transfer"
                ),
            }
        ]
        return model, transition

    def _legacy_model(self, version: str = "2.0") -> dict[str, object]:
        """Project the current fixture into the historical, intentionally noisy shape."""
        legacy = copy.deepcopy(self.proposal)
        legacy["schema_version"] = version
        for demand in legacy["environment_demands"]:
            demand.pop("environment_dimensions", None)
        demands = {item["id"]: item for item in legacy["environment_demands"]}
        requirements = {
            item["id"]: item
            for item in legacy["storyline_environment_requirements"]
        }
        environments = {item["id"]: item for item in legacy["environments"]}
        for record in legacy["storyline_hosting_ledger"]:
            demand = next(item for item in record["source_ids"] if item in demands)
            requirement = next(
                item for item in record["source_ids"] if item in requirements
            )
            source_items = (demands[demand], requirements[requirement])
            source_text = [item["responsibility"] for item in source_items]
            record["evidence"] = " | ".join(source_text)
            for environment_id in record["realization_ids"]:
                environment = environments[environment_id]
                for source in source_items:
                    for value in [source["responsibility"], *source["constraints"]]:
                        if value not in environment["access_rules"]:
                            environment["access_rules"].append(value)
        if version == "2.0":
            for edge in legacy["environment_topology"]:
                edge.pop("directionality", None)
                edge.pop("transfer_capabilities", None)
            for transition in legacy["transition_contracts"]:
                transition.pop("trigger_bindings", None)
        owned = {
            item["id"]: item
            for field in (
                "environments",
                "functional_zones",
                "environment_topology",
                "access_and_authority",
                "resource_and_information_channels",
                "hazards_and_failure_modes",
                "storyline_hosting_ledger",
                "event_affordance_catalog",
                "transition_contracts",
            )
            for item in legacy[field]
        }
        for claim in legacy["derivation_claims"]:
            if len(claim["projection_ids"]) == 1:
                claim["value_sha256"] = runtime.canonical_sha256(
                    owned[claim["projection_ids"][0]]
                )
        return legacy

    def test_authority_partition_rejects_overlap_before_deep_validation(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["downstream_freedom"].append(
            model["authority_partition"]["autonomous_owned"][0]
        )
        with self.assertRaisesRegex(
            e1.E1Error, "E1_AUTHORITY_PARTITION_OVERLAP"
        ):
            self._validate(model)

    def test_authority_partition_requires_all_four_exact_sets(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["autonomous_owned"].remove(
            model["event_affordance_catalog"][0]["id"]
        )
        with self.assertRaisesRegex(
            e1.E1Error, "E1_AUTHORITY_PARTITION_MISMATCH"
        ):
            self._validate(model)

    def test_storyline_environment_projection_and_joint_hosting_are_exact(
        self,
    ) -> None:
        self.assertEqual(
            self.storyline["environment_requirements"],
            self.proposal["storyline_environment_requirements"],
        )
        demand_ids = {item["id"] for item in self.world["environment_demands"]}
        requirement_ids = {
            item["id"] for item in self.storyline["environment_requirements"]
        }
        hosted_demands = []
        hosted_requirements = []
        for record in self.proposal["storyline_hosting_ledger"]:
            hosted_demands.extend(set(record["source_ids"]) & demand_ids)
            hosted_requirements.extend(set(record["source_ids"]) & requirement_ids)
        self.assertCountEqual(hosted_demands, demand_ids)
        self.assertCountEqual(hosted_requirements, requirement_ids)

        missing = copy.deepcopy(self.proposal)
        missing["storyline_hosting_ledger"][0]["source_ids"].remove(
            next(
                item
                for item in missing["storyline_hosting_ledger"][0]["source_ids"]
                if item in requirement_ids
            )
        )
        with self.assertRaisesRegex(
            e1.E1Error, "E1_HOSTING_COVERAGE_MISMATCH"
        ):
            self._validate(missing)

        wrong_line = copy.deepcopy(self.proposal)
        first, second = wrong_line["storyline_hosting_ledger"][:2]
        first_requirement = next(
            item for item in first["source_ids"] if item in requirement_ids
        )
        second_requirement = next(
            item for item in second["source_ids"] if item in requirement_ids
        )
        first["source_ids"].remove(first_requirement)
        second["source_ids"].remove(second_requirement)
        first["source_ids"].append(second_requirement)
        second["source_ids"].append(first_requirement)
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_LINE_MISMATCH"):
            self._validate(wrong_line)

    def test_storyline_environment_projection_is_lossless_and_session_bound(
        self,
    ) -> None:
        changed = copy.deepcopy(self.proposal)
        changed["storyline_environment_requirements"][0][
            "responsibility"
        ] += " changed"
        with self.assertRaisesRegex(
            e1.E1Error, "E1_STORYLINE_ENVIRONMENT_PROJECTION_MISMATCH"
        ):
            self._validate(changed)

        session = json.loads(
            (self.workspace / "generation-session.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("storyline_environment_requirement_bindings", session)
        session["storyline_environment_requirement_bindings"][0][
            "value_sha256"
        ] = "0" * 64
        (self.workspace / "generation-session.json").write_text(
            runtime.canonical_json(session), encoding="utf-8"
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-e1"}, clear=False
        ):
            with self.assertRaisesRegex(e1.E1Error, "E1_SESSION_INVALID"):
                e1._validated_session(
                    self.workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    world_package=self.w1,
                    input_gate=self.gate,
                    runtime=runtime.ContractRuntime(),
                )

    def test_ready_environment_system_advances_and_covers_inputs(self) -> None:
        receipt = self.run_e1()
        model = receipt.model
        demand_ids = {item["id"] for item in model["environment_demands"]}
        self.assertEqual(
            demand_ids,
            {
                item["source_ids"][0]
                for item in model["storyline_hosting_ledger"]
            },
        )
        self.assertEqual(
            {item["id"] for item in self.storyline["event_requirements"]},
            {
                requirement_id
                for item in model["event_affordance_catalog"]
                for requirement_id in item["event_requirement_ids"]
            },
        )
        self.assertEqual("E1", receipt.completion.data["stage"])
        self.assertEqual(4, receipt.transition.snapshot["revision"])
        self.assertEqual(
            "ready", e1.validate_e1_package(self.package)["verdict"]
        )
        store = production_store.ProductionRunStore(self.package.parent)
        identity = production._completion_contract_identity(
            store, receipt.completion.reference
        )
        self.assertTrue(
            production._identity_matches_current_profile("E1", identity)
        )

    def test_e1_initial_source_anchor_is_exact_and_not_self_reported(self) -> None:
        workspace = self._start_workspace("e1-initial-source-anchor")
        self._seal_prefix(workspace, 2)
        phase2_path = (
            workspace / "generation-evidence/02-environment-architecture.json"
        )
        phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
        environment = phase2["payload"]["environments"][0]
        value = environment["access_rules"][0]
        pointer = "/payload/environments/0/access_rules/0"
        anchor = {
            "source_kind": "e1_initial_state",
            "source_artifact": {
                "stage": "E1",
                **runtime.artifact_reference(phase2_path, root=workspace),
            },
            "source_pointer": pointer,
            "value_sha256": runtime.canonical_sha256(value),
            "environment_id": environment["id"],
            "subject_kind": "authority",
            "subject_id": "E1SRC-"
            + runtime.canonical_sha256(
                [environment["id"], "authority", pointer, value]
            )[:20],
            "state": value,
        }
        model = copy.deepcopy(self.proposal)
        fact = model["capability_fact_registry"][0]
        fact["source_anchor"] = anchor
        fact["root_policy"] = "root_allowed"
        e1._validate_v24_e1_source_anchors(model, root=workspace)

        mutants = []
        wrong_artifact = copy.deepcopy(model)
        wrong_artifact["capability_fact_registry"][0]["source_anchor"][
            "source_artifact"
        ]["sha256"] = "0" * 64
        mutants.append(wrong_artifact)
        wrong_pointer = copy.deepcopy(model)
        wrong_pointer["capability_fact_registry"][0]["source_anchor"][
            "source_pointer"
        ] = "/payload/environments/0/resources/0"
        mutants.append(wrong_pointer)
        wrong_value = copy.deepcopy(model)
        wrong_value["capability_fact_registry"][0]["source_anchor"][
            "value_sha256"
        ] = "0" * 64
        mutants.append(wrong_value)
        wrong_subject = copy.deepcopy(model)
        wrong_subject["capability_fact_registry"][0]["source_anchor"][
            "subject_id"
        ] = "E1SRC-FORGED"
        mutants.append(wrong_subject)
        wrong_kind = copy.deepcopy(model)
        wrong_kind["capability_fact_registry"][0]["source_anchor"][
            "subject_kind"
        ] = "resource"
        mutants.append(wrong_kind)
        for mutant in mutants:
            with self.assertRaisesRegex(
                e1.E1Error, "E1_CAPABILITY_FACT_SOURCE_INVALID"
            ):
                e1._validate_v24_e1_source_anchors(mutant, root=workspace)

    def test_one_evd_may_expose_multiple_distinct_local_affordances(self) -> None:
        model = copy.deepcopy(self.proposal)
        environment = model["environments"][0]
        original = model["event_affordance_catalog"][0]
        action = "Perform a second bounded local operation for this EVD."
        environment["allowed_actions"].append(action)
        alternate = copy.deepcopy(original)
        alternate["id"] = "AFF-ALTERNATE-LOCAL"
        alternate["allowed_actions"] = [action]
        alternate["prerequisites"] = [
            "The alternate local control surface is enabled."
        ]
        model["event_affordance_catalog"].append(alternate)
        model["authority_partition"]["autonomous_owned"].append(alternate["id"])
        environment_claim = next(
            item
            for item in model["derivation_claims"]
            if item["projection_ids"] == [environment["id"]]
        )
        environment_claim["value_sha256"] = runtime.canonical_sha256(environment)
        model["derivation_claims"].append(
            {
                "id": "DRV-E1-AFF-ALTERNATE-LOCAL",
                "value_sha256": runtime.canonical_sha256(alternate),
                "source_ids": copy.deepcopy(alternate["event_requirement_ids"]),
                "decision_ids": [model["design_decisions"][0]["id"]],
                "projection_ids": [alternate["id"]],
            }
        )
        e1._validate_model(
            model,
            self.baseline,
            self.storyline,
            self.world,
            e1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=e1._source_artifacts(self.b0, self.s1, self.w1),
        )

    def test_causal_target_endpoint_cannot_pollute_preanchor_transition(self) -> None:
        model = copy.deepcopy(self.proposal)
        connection = next(
            item for item in self.storyline["connections"]
            if item["relation"] == "causal" and item["to_state_index"] > 0
        )
        record = next(
            item
            for item in model["connection_path_readiness"]
            if item["connection_id"] == connection["id"]
        )
        preanchor = next(
            item
            for item in model["story_transition_support"]
            if item["storyline_id"] == connection["to_storyline_id"]
            and item["from_state_index"] < connection["to_state_index"]
        )
        generic_step_id = preanchor["support_claims"][0]["step_id"]
        transfer_fact_id = record["transfer_fact_id"]
        generic_step = next(
            item
            for item in model["capability_step_registry"]
            if item["id"] == generic_step_id
        )
        if transfer_fact_id not in generic_step["requires_fact_ids"]:
            generic_step["requires_fact_ids"].append(transfer_fact_id)
        transfer_fact = next(
            item
            for item in model["capability_fact_registry"]
            if item["id"] == transfer_fact_id
        )
        if generic_step_id not in transfer_fact["consumer_step_ids"]:
            transfer_fact["consumer_step_ids"].append(generic_step_id)
        record["target_endpoint_step_ids"] = [generic_step_id]
        steps = {
            item["id"]: item for item in model["capability_step_registry"]
        }
        for transition in model["story_transition_support"]:
            transition["required_fact_ids"] = sorted(
                {
                    fact_id
                    for claim in transition["support_claims"]
                    for fact_id in steps[claim["step_id"]]["requires_fact_ids"]
                }
            )
        with self.assertRaisesRegex(
            e1.E1Error,
            "E1_CONNECTION_(ENDPOINT_ANCHOR_MISMATCH|TARGET_ENDPOINT_PREANCHOR_REUSE)",
        ):
            self._validate(model)

    def test_every_phase_fails_before_writing_invalid_evidence(self) -> None:
        phase1 = self._start_workspace("phase1-invalid")
        bad_p1 = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["environment-demand-scan"]
        }
        bad_p1["environment_demands"][0]["responsibility"] += " forged"
        with self.assertRaisesRegex(e1.E1Error, "E1_DEMAND_PROJECTION_MISMATCH"):
            self._submit_current_phase(
                phase1, "environment-demand-scan", bad_p1
            )
        self.assertFalse(
            (phase1 / "generation-evidence/01-environment-demand-scan.json").exists()
        )

        bad_digest = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["environment-demand-scan"]
        }
        bad_digest["story_transition_universe_digest"][
            "canonical_items_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(e1.E1Error, "E1_UNIVERSE_DIGEST_MISMATCH"):
            self._submit_current_phase(
                phase1, "environment-demand-scan", bad_digest
            )
        self.assertFalse(
            (phase1 / "generation-evidence/01-environment-demand-scan.json").exists()
        )

        phase2 = self._start_workspace("phase2-invalid")
        self._seal_prefix(phase2, 1)
        p1_sha = runtime.sha256_file(
            phase2 / "generation-evidence/01-environment-demand-scan.json"
        )
        bad_p2 = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["environment-architecture"]
        }
        bad_p2["environments"][0].pop("scope")
        with self.assertRaisesRegex(e1.E1Error, "E1_PHASE2_DEFINITION_INVALID"):
            self._submit_current_phase(phase2, "environment-architecture", bad_p2)
        self.assertFalse(
            (phase2 / "generation-evidence/02-environment-architecture.json").exists()
        )
        self.assertEqual(
            p1_sha,
            runtime.sha256_file(
                phase2 / "generation-evidence/01-environment-demand-scan.json"
            ),
        )
        bad_option = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["environment-architecture"]
        }
        bad_option["initial_anchor_support"][0]["support_options"][0][
            "support_option_id"
        ] = "IAO-FORGED"
        with self.assertRaisesRegex(e1.E1Error, "E1_INITIAL_OPTION_ID_INVALID"):
            self._submit_current_phase(
                phase2, "environment-architecture", bad_option
            )
        self.assertFalse(
            (phase2 / "generation-evidence/02-environment-architecture.json").exists()
        )
        self.assertEqual(
            p1_sha,
            runtime.sha256_file(
                phase2 / "generation-evidence/01-environment-demand-scan.json"
            ),
        )

        phase3 = self._start_workspace("phase3-invalid")
        self._seal_prefix(phase3, 2)
        p2_sha = runtime.sha256_file(
            phase3 / "generation-evidence/02-environment-architecture.json"
        )
        base_p3 = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["zones-and-topology"]
        }
        invalid_p3_payloads = []
        bad_channel = copy.deepcopy(base_p3)
        bad_channel["resource_and_information_channels"][0]["mechanism"] = "placeholder"
        bad_channel["resource_and_information_channels"][0]["constraints"] = [
            "nonempty but unbound"
        ]
        invalid_p3_payloads.append(
            ("channel", bad_channel, "E1_CHANNEL_SEMANTICS_INCOMPLETE")
        )
        foreign_action = copy.deepcopy(base_p3)
        foreign_action["event_affordance_catalog"][0]["allowed_actions"].append(
            "E1_ACTION_INTERFACE_FOREIGN"
        )
        invalid_p3_payloads.append(
            ("foreign-action", foreign_action, "E1_ACTION_INTERFACE_FOREIGN")
        )
        cyclic_capability = copy.deepcopy(base_p3)
        first_step = cyclic_capability["capability_step_registry"][0]
        produced_id = first_step["produces_fact_ids"][0]
        first_step["requires_fact_ids"].append(produced_id)
        produced_fact = next(
            item
            for item in cyclic_capability["capability_fact_registry"]
            if item["id"] == produced_id
        )
        produced_fact["consumer_step_ids"].append(first_step["id"])
        invalid_p3_payloads.append(
            ("capability-cycle", cyclic_capability, "E1_CAPABILITY_GRAPH_CYCLE")
        )
        for name, bad_p3, expected_code in invalid_p3_payloads:
            with self.subTest(phase3_field=name):
                with self.assertRaises(e1.E1Error) as caught:
                    self._submit_current_phase(phase3, "zones-and-topology", bad_p3)
                self.assertEqual(expected_code, caught.exception.code)
                self.assertFalse(
                    (phase3 / "generation-evidence/03-zones-and-topology.json").exists()
                )
                self.assertEqual(
                    p2_sha,
                    runtime.sha256_file(
                        phase3 / "generation-evidence/02-environment-architecture.json"
                    ),
                )

        phase3_reject = self._start_workspace("phase3-authority-review-rejected")
        self._seal_prefix(phase3_reject, 2)
        p2_reject_sha = runtime.sha256_file(
            phase3_reject / "generation-evidence/02-environment-architecture.json"
        )
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "thread-phase3-authority-review-rejected"},
            clear=False,
        ):
            authority_request = e1.start_e1_authority_semantic_review(
                phase3_reject,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
                payload=base_p3,
            )
        authority_review = {
            "claim_verdicts": [
                {
                    "claim_id": item["id"],
                    "verdict": "fail" if index == 0 else "pass",
                    "rationale": "The cited sealed source does not justify this authority claim."
                    if index == 0
                    else "The bounded claim is supported by its sealed source.",
                }
                for index, item in enumerate(authority_request["claims"])
            ],
            "reviewer_task_receipt": {
                "task_id": "phase3-negative-authority-review",
                "output_sha256": runtime.canonical_sha256(authority_request),
            },
        }
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "thread-independent-authority-reviewer"},
            clear=False,
        ):
            authority_review["reviewer_task_receipt"] = (
                e1.seal_e1_review_task_output(
                    phase3_reject,
                    candidate_sha256=authority_request["candidate_sha256"],
                    review_kind=authority_request["review_kind"],
                    task_id="phase3-negative-authority-review",
                    verdict_payload={
                        "claim_verdicts": authority_review["claim_verdicts"]
                    },
                )
            )
            e1.submit_e1_authority_semantic_review(
                phase3_reject,
                candidate_sha256=authority_request["candidate_sha256"],
                review=authority_review,
            )
        with self.assertRaisesRegex(e1.E1Error, "E1_AUTHORITY_REVIEW_REJECTED"):
            self._submit_current_phase(
                phase3_reject, "zones-and-topology", base_p3
            )
        self.assertFalse(
            (
                phase3_reject
                / "generation-evidence/03-zones-and-topology.json"
            ).exists()
        )
        self.assertEqual(
            p2_reject_sha,
            runtime.sha256_file(
                phase3_reject / "generation-evidence/02-environment-architecture.json"
            ),
        )

        phase4 = self._start_workspace("phase4-invalid")
        self._seal_prefix(phase4, 3)
        p3_sha = runtime.sha256_file(
            phase4 / "generation-evidence/03-zones-and-topology.json"
        )
        p4_payload = {
            field: copy.deepcopy(self.proposal[field])
            for field in e1.PHASE_FIELDS["storyline-hosting-test"]
        }
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_REVIEW_MISSING"):
            self._submit_current_phase(
                phase4, "storyline-hosting-test", p4_payload
            )
        self.assertFalse(
            (phase4 / "generation-evidence/04-storyline-hosting-test.json").exists()
        )
        self.assertEqual(
            p3_sha,
            runtime.sha256_file(
                phase4 / "generation-evidence/03-zones-and-topology.json"
            ),
        )

        phase4_reject = self._start_workspace("phase4-review-rejected")
        self._seal_prefix(phase4_reject, 3)
        p3_reject_sha = runtime.sha256_file(
            phase4_reject / "generation-evidence/03-zones-and-topology.json"
        )
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "thread-phase4-review-rejected"},
            clear=False,
        ):
            request = e1.start_e1_hosting_semantic_review(
                phase4_reject,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
                payload=p4_payload,
            )
        failed_review = {
            "claim_verdicts": [
                {
                    "claim_id": item["id"],
                    "verdict": "pass",
                    "rationale": "The local claim itself can be inspected.",
                }
                for item in request["claims"]
            ],
            "record_verdicts": [
                {
                    "record_id": item["id"],
                    "checks": {
                        check: (
                            "fail" if check == "support_mode_sufficient" else "pass"
                        )
                        for check in e1._TRANSITION_RECORD_REVIEW_CHECKS
                    },
                    "rationale": "The selected mode does not establish this bounded support claim.",
                }
                for item in request["records"]
            ],
            "reviewer_task_receipt": {
                "task_id": "phase4-negative-transition-review",
                "output_sha256": runtime.canonical_sha256(request),
            },
        }
        with mock.patch.dict(
            os.environ,
            {"CODEX_THREAD_ID": "thread-independent-reject-reviewer"},
            clear=False,
        ):
            failed_review["reviewer_task_receipt"] = (
                e1.seal_e1_review_task_output(
                    phase4_reject,
                    candidate_sha256=request["candidate_sha256"],
                    review_kind=request["review_kind"],
                    task_id="phase4-negative-transition-review",
                    verdict_payload={
                        "claim_verdicts": failed_review["claim_verdicts"],
                        "record_verdicts": failed_review["record_verdicts"],
                    },
                )
            )
            e1.submit_e1_hosting_semantic_review(
                phase4_reject,
                candidate_sha256=request["candidate_sha256"],
                review=failed_review,
            )
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_REVIEW_REJECTED"):
            self._submit_current_phase(
                phase4_reject, "storyline-hosting-test", p4_payload
            )
        self.assertFalse(
            (
                phase4_reject
                / "generation-evidence/04-storyline-hosting-test.json"
            ).exists()
        )
        self.assertEqual(
            p3_reject_sha,
            runtime.sha256_file(
                phase4_reject / "generation-evidence/03-zones-and-topology.json"
            ),
        )

        phase4_fields = self._start_workspace("phase4-fields-invalid")
        self._seal_prefix(phase4_fields, 3)
        p3_fields_sha = runtime.sha256_file(
            phase4_fields / "generation-evidence/03-zones-and-topology.json"
        )
        invalid_payloads = []
        authority_overlap = copy.deepcopy(p4_payload)
        authority_overlap["authority_partition"]["downstream_freedom"].append(
            authority_overlap["authority_partition"]["autonomous_owned"][0]
        )
        invalid_payloads.append(
            ("authority-overlap", authority_overlap, "E1_AUTHORITY_PARTITION_OVERLAP")
        )
        missing_transition = copy.deepcopy(p4_payload)
        missing_transition["story_transition_support"].pop()
        invalid_payloads.append(
            (
                "missing-transition-support",
                missing_transition,
                "E1_STORY_TRANSITION_COVERAGE_MISMATCH",
            )
        )
        missing_initial_option = copy.deepcopy(p4_payload)
        missing_initial_option["initial_anchor_option_realization_ledger"].pop()
        invalid_payloads.append(
            (
                "missing-initial-option",
                missing_initial_option,
                "E1_INITIAL_OPTION_REALIZATION_COVERAGE_MISMATCH",
            )
        )
        missing_obligation_occurrence = copy.deepcopy(p4_payload)
        removed_binding = missing_obligation_occurrence[
            "obligation_occurrence_bindings"
        ].pop()
        missing_obligation_occurrence["authority_partition"][
            "autonomous_owned"
        ].remove(removed_binding["id"])
        invalid_payloads.append(
            (
                "missing-obligation-occurrence-binding",
                missing_obligation_occurrence,
                "E1_OBLIGATION_DIRECT_OCCURRENCE_MISMATCH",
            )
        )
        stale_derivation = copy.deepcopy(p4_payload)
        stale_derivation["derivation_claims"][0]["value_sha256"] = "0" * 64
        invalid_payloads.append(
            ("stale-derivation", stale_derivation, "E1_DERIVATION_STALE")
        )
        for name, invalid_payload, expected_code in invalid_payloads:
            with self.subTest(phase4_field=name):
                self._install_passing_review_without_start(
                    phase4_fields, invalid_payload
                )
                with self.assertRaises(e1.E1Error) as caught:
                    self._submit_current_phase(
                        phase4_fields,
                        "storyline-hosting-test",
                        invalid_payload,
                    )
                self.assertEqual(expected_code, caught.exception.code)
                self.assertFalse(
                    (
                        phase4_fields
                        / "generation-evidence/04-storyline-hosting-test.json"
                    ).exists()
                )
                self.assertEqual(
                    p3_fields_sha,
                    runtime.sha256_file(
                        phase4_fields
                        / "generation-evidence/03-zones-and-topology.json"
                    ),
                )

        phase5 = self._start_workspace("phase5-invalid")
        self._seal_prefix(phase5, 4)
        p4_sha = runtime.sha256_file(
            phase5 / "generation-evidence/04-storyline-hosting-test.json"
        )
        bad_model = copy.deepcopy(self.proposal)
        bad_model["environments"][0]["features"].append(
            "A feature that was not sealed in phase 2."
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_EVIDENCE_MODEL_MISMATCH"):
            self._submit_current_phase(
                phase5, "final-environment-model", {"model": bad_model}
            )
        self.assertFalse(
            (phase5 / "generation-evidence/05-final-environment-model.json").exists()
        )
        self.assertEqual(
            p4_sha,
            runtime.sha256_file(
                phase5 / "generation-evidence/04-storyline-hosting-test.json"
            ),
        )

    def test_historical_2_0_model_remains_read_only_valid(self) -> None:
        legacy = self._legacy_model()
        legacy_world = copy.deepcopy(self.world)
        for demand in legacy_world["environment_demands"]:
            demand.pop("environment_dimensions", None)
        e1._validate_model(
            legacy,
            self.baseline,
            self.storyline,
            legacy_world,
            e1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=self.proposal["source_artifacts"],
        )

        foreign = copy.deepcopy(legacy)
        foreign["transition_contracts"][0]["trigger_ids"] = [
            foreign["event_affordance_catalog"][1]["id"]
        ]
        with self.assertRaises(e1.E1Error) as caught:
            e1._validate_model(
                foreign,
                self.baseline,
                self.storyline,
                legacy_world,
                e1._controls(self.b0, self.baseline),
                runtime.ContractRuntime(),
                expected_gate=self.gate.reference,
                expected_sources=self.proposal["source_artifacts"],
            )
        self.assertEqual("E1_TRANSITION_ENVIRONMENT_MISMATCH", caught.exception.code)

    def test_final_submission_rejects_historical_2_0_generation(self) -> None:
        legacy = self._legacy_model()
        with self.assertRaises(e1.E1Error) as caught:
            e1._require_generation_schema(legacy)
        self.assertEqual("E1_LEGACY_GENERATION_FORBIDDEN", caught.exception.code)

    def test_changed_w1_demand_changes_every_agent_phase(self) -> None:
        left_world = copy.deepcopy(self.world)
        right_world = copy.deepcopy(self.world)
        left_world["environment_demands"][0]["responsibility"] = (
            "Host a controlled interior interface."
        )
        right_world["environment_demands"][0]["responsibility"] = (
            "Host an exposed border interface."
        )
        sources = copy.deepcopy(self.proposal["source_artifacts"])
        left = agent_environment_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=self.storyline,
            world=left_world,
        )
        right = agent_environment_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=self.storyline,
            world=right_world,
        )
        for phase in e1.PHASES:
            left_payload = (
                {"model": left}
                if phase == "final-environment-model"
                else {field: left[field] for field in e1.PHASE_FIELDS[phase]}
            )
            right_payload = (
                {"model": right}
                if phase == "final-environment-model"
                else {field: right[field] for field in e1.PHASE_FIELDS[phase]}
            )
            self.assertNotEqual(
                runtime.canonical_sha256(left_payload),
                runtime.canonical_sha256(right_payload),
                phase,
            )

    def test_changed_s1_environment_requirement_changes_source_bound_phases(
        self,
    ) -> None:
        left_storyline = copy.deepcopy(self.storyline)
        right_storyline = copy.deepcopy(self.storyline)
        left_storyline["environment_requirements"][0]["responsibility"] = (
            "Host a controlled interior obligation."
        )
        right_storyline["environment_requirements"][0]["responsibility"] = (
            "Host an exposed border obligation."
        )
        sources = copy.deepcopy(self.proposal["source_artifacts"])
        left = agent_environment_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=left_storyline,
            world=self.world,
        )
        right = agent_environment_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=right_storyline,
            world=self.world,
        )
        payloads = {}
        for phase in (
            "environment-demand-scan",
            "storyline-hosting-test",
            "final-environment-model",
        ):
            left_payload = (
                {"model": left}
                if phase == "final-environment-model"
                else {field: left[field] for field in e1.PHASE_FIELDS[phase]}
            )
            right_payload = (
                {"model": right}
                if phase == "final-environment-model"
                else {field: right[field] for field in e1.PHASE_FIELDS[phase]}
            )
            payloads[phase] = (left_payload, right_payload)
            self.assertNotEqual(
                runtime.canonical_sha256(left_payload),
                runtime.canonical_sha256(right_payload),
                phase,
            )
        for model, source_text in (
            (left, left_storyline["environment_requirements"][0]["responsibility"]),
            (right, right_storyline["environment_requirements"][0]["responsibility"]),
        ):
            environment_architecture = {
                field: model[field]
                for field in e1.PHASE_FIELDS["environment-architecture"]
            }
            self.assertNotIn(
                source_text, runtime.canonical_json(environment_architecture)
            )
            e1._validate_environment_source_text_clean(
                {item["id"]: item for item in model["environments"]},
                [
                    *model["storyline_environment_requirements"],
                    *model["environment_demands"],
                ],
            )
        source_id = left_storyline["environment_requirements"][0]["id"]
        for model, storyline_model in (
            (left, left_storyline),
            (right, right_storyline),
        ):
            binding = next(
                source_binding
                for record in model["storyline_hosting_ledger"]
                for source_binding in record["evidence"]["source_bindings"]
                if source_binding["source_id"] == source_id
            )
            responsibility = storyline_model["environment_requirements"][0][
                "responsibility"
            ]
            self.assertEqual(
                runtime.canonical_sha256(responsibility),
                binding["responsibility_sha256"],
            )
        session = json.loads(
            (self.workspace / "generation-session.json").read_text(
                encoding="utf-8"
            )
        )
        left_p4, right_p4 = payloads["storyline-hosting-test"]
        left_request = e1._expected_hosting_review_request(
            self.workspace,
            session=session,
            payload=left_p4,
            storyline=left_storyline,
            world=self.world,
        )
        right_request = e1._expected_hosting_review_request(
            self.workspace,
            session=session,
            payload=right_p4,
            storyline=right_storyline,
            world=self.world,
        )
        self.assertNotEqual(
            left_request["candidate_sha256"], right_request["candidate_sha256"]
        )
        left_claim = next(
            item
            for item in left_request["claims"]
            if item["source_id"] == source_id
            and item["token_kind"] == "responsibility"
        )
        right_claim = next(
            item
            for item in right_request["claims"]
            if item["source_id"] == source_id
            and item["token_kind"] == "responsibility"
        )
        self.assertNotEqual(left_claim["source_sha256"], right_claim["source_sha256"])
        self.assertNotEqual(left_claim["source_text"], right_claim["source_text"])
        self._install_passing_review_without_start(
            self.workspace, left_p4, storyline=left_storyline
        )
        with self.assertRaisesRegex(e1.E1Error, "E1_HOSTING_REVIEW_MISSING"):
            e1._validated_hosting_review(
                self.workspace,
                session=session,
                payload=right_p4,
                storyline=right_storyline,
                world=self.world,
            )

    def test_resealed_failures_remain_blocked(self) -> None:
        self.run_e1()
        original = self._read_model(self.package)
        cases = []

        deleted_hosting = copy.deepcopy(original)
        removed = deleted_hosting["storyline_hosting_ledger"].pop()
        deleted_hosting["authority_partition"]["autonomous_owned"].remove(
            removed["id"]
        )
        cases.append(
            ("deleted-hosting", deleted_hosting, "E1_HOSTING_COVERAGE_MISMATCH")
        )

        unreachable = copy.deepcopy(original)
        unreachable["environment_topology"].pop(len(unreachable["environment_topology"]) // 2)
        cases.append(("unreachable", unreachable, "E1_TOPOLOGY_UNREACHABLE"))

        missing_action = copy.deepcopy(original)
        missing_action["event_affordance_catalog"][0]["allowed_actions"] = [
            "An action not exposed by the environment."
        ]
        cases.append(
            ("missing-action", missing_action, "E1_ACTION_INTERFACE_FOREIGN")
        )

        mixed_foreign_action = copy.deepcopy(original)
        mixed_foreign_action["event_affordance_catalog"][0][
            "allowed_actions"
        ].append("A foreign action not exposed by this environment.")
        cases.append(
            (
                "mixed-foreign-action",
                mixed_foreign_action,
                "E1_ACTION_INTERFACE_FOREIGN",
            )
        )

        duplicate_id = copy.deepcopy(original)
        duplicate_id["event_affordance_catalog"].append(
            copy.deepcopy(duplicate_id["event_affordance_catalog"][0])
        )
        cases.append(("duplicate-affordance-id", duplicate_id, "E1_ID_DUPLICATE"))

        duplicate_semantics = copy.deepcopy(original)
        copied = copy.deepcopy(duplicate_semantics["event_affordance_catalog"][0])
        copied["id"] = "AFF-SEMANTIC-COPY"
        duplicate_semantics["event_affordance_catalog"].append(copied)
        cases.append(
            (
                "duplicate-affordance-semantics",
                duplicate_semantics,
                "E1_AFFORDANCE_SEMANTIC_DUPLICATE",
            )
        )

        zero_coverage = copy.deepcopy(original)
        zero_coverage["event_affordance_catalog"].pop()
        cases.append(
            ("zero-evd-affordance", zero_coverage, "E1_ACTION_INTERFACE_MISSING")
        )

        rule_conflict = copy.deepcopy(original)
        rule_conflict["storyline_hosting_ledger"][0]["evidence"][
            "source_bindings"
        ][0]["constraint_sha256s"][0] = "0" * 64
        cases.append(("rule-conflict", rule_conflict, "E1_SOURCE_MEANING_UNBOUND"))

        storyline_rule_conflict = copy.deepcopy(original)
        storyline_rule_conflict["storyline_hosting_ledger"][0]["evidence"][
            "source_bindings"
        ][1]["constraint_sha256s"][0] = "0" * 64
        cases.append(
            (
                "storyline-rule-conflict",
                storyline_rule_conflict,
                "E1_SOURCE_MEANING_UNBOUND",
            )
        )

        forged_gate = copy.deepcopy(original)
        forged_gate["input_gate"]["sha256"] = "0" * 64
        cases.append(
            ("forged-gate", forged_gate, "E1_GATE_REFERENCE_MISMATCH")
        )

        for name, model, expected in cases:
            with self.subTest(name=name):
                mutant = self.work / "mutants" / name
                shutil.copytree(self.package, mutant)
                self._reseal_model(mutant, model, gate=model["input_gate"])
                with self.assertRaises(e1.E1Error) as caught:
                    e1.validate_e1_package(mutant)
                self.assertEqual(expected, caught.exception.code)

        missing_completion = self.work / "mutants" / "missing-completion"
        shutil.copytree(self.package, missing_completion)
        (missing_completion / "stage-completion.json").unlink()
        with self.assertRaises(e1.E1Error) as caught:
            e1.validate_e1_package(missing_completion)
        self.assertEqual("E1_COMPLETION_MISSING", caught.exception.code)

        boundary = self.work / "mutants" / "boundary"
        shutil.copytree(self.package, boundary)
        (boundary / "event-timeline.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(e1.E1Error) as caught:
            e1.validate_e1_package(boundary)
        self.assertEqual("E1_BOUNDARY_VIOLATION", caught.exception.code)

    def test_cross_object_semantic_mismatches_are_rejected(self) -> None:
        self.run_e1()
        original = self._read_model(self.package)

        swapped_affordances = copy.deepcopy(original)
        first_affordance, second_affordance = (
            swapped_affordances["event_affordance_catalog"][:2]
        )
        (
            first_affordance["event_requirement_ids"],
            second_affordance["event_requirement_ids"],
        ) = (
            second_affordance["event_requirement_ids"],
            first_affordance["event_requirement_ids"],
        )

        foreign_transition = copy.deepcopy(original)
        foreign_transition["transition_contracts"][0]["trigger_ids"] = [
            foreign_transition["event_affordance_catalog"][1]["id"]
        ]

        placeholder_channels = copy.deepcopy(original)
        for channel in placeholder_channels["resource_and_information_channels"]:
            channel["relation"] = "generic channel"
            channel["mechanism"] = "placeholder"
            channel["constraints"] = ["nonempty but unbound"]

        cases = (
            (
                "swapped-affordances",
                swapped_affordances,
                "E1_AFFORDANCE_LINE_MISMATCH",
            ),
            (
                "foreign-transition-trigger",
                foreign_transition,
                "E1_TRANSITION_TRIGGER_BINDING_MISMATCH",
            ),
            (
                "placeholder-channels",
                placeholder_channels,
                "E1_CHANNEL_SEMANTICS_INCOMPLETE",
            ),
        )
        for name, model, expected in cases:
            with self.subTest(name=name):
                mutant = self.work / "semantic-mutants" / name
                shutil.copytree(self.package, mutant)
                self._reseal_model(mutant, model, gate=model["input_gate"])
                with self.assertRaises(e1.E1Error) as caught:
                    e1.validate_e1_package(mutant)
                self.assertEqual(expected, caught.exception.code)

    def test_cross_environment_trigger_requires_explicit_causal_path(self) -> None:
        model, transition = self._cross_line_model()
        self._validate(model)
        observed = [
            requirement_id
            for affordance in model["event_affordance_catalog"]
            for requirement_id in affordance["event_requirement_ids"]
        ]
        self.assertEqual(len(observed), len(set(observed)))

        cases = []
        missing_path = copy.deepcopy(model)
        next(
            item
            for item in missing_path["transition_contracts"]
            if item["id"] == transition["id"]
        )["trigger_bindings"][0]["topology_path_ids"] = []
        cases.append(
            (missing_path, "E1_TRIGGER_TOPOLOGY_PATH_INVALID")
        )

        wrong_evidence = copy.deepcopy(model)
        associative = next(
            item
            for item in self.storyline["connections"]
            if item["relation"] == "associative"
        )
        next(
            item
            for item in wrong_evidence["transition_contracts"]
            if item["id"] == transition["id"]
        )["trigger_bindings"][0]["causal_evidence_ids"] = [associative["id"]]
        cases.append(
            (wrong_evidence, "E1_TRIGGER_CAUSAL_EVIDENCE_INVALID")
        )

        bad_prefix = copy.deepcopy(model)
        next(
            item
            for item in bad_prefix["transition_contracts"]
            if item["id"] == transition["id"]
        )["trigger_bindings"][0]["topology_path_ids"] = ["TOPO-LEGACY"]
        cases.append((bad_prefix, "E1_MODEL_SCHEMA_INVALID"))

        for mutant, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(e1.E1Error) as caught:
                    self._validate(mutant)
                self.assertEqual(expected, caught.exception.code)

    def test_v24_cross_line_dag_obligation_modes_and_receipts_are_hard(self) -> None:
        _transitions, precedence_edges, _adjacency = e1._s1_structural_precedence(
            self.storyline
        )
        _precedence_edge_id, (earlier, later) = next(
            (edge_id, (left, right))
            for edge_id, (left, right) in precedence_edges.items()
            if left.split(":", 1)[0] != right.split(":", 1)[0]
        )
        projection = copy.deepcopy(self.proposal)
        projected_fact = next(
            item for item in projection["capability_fact_registry"]
            if item["producer_transition_keys"]
        )
        projected_fact["producer_transition_keys"] = []
        with self.assertRaisesRegex(
            e1.E1Error, "E1_CAPABILITY_FACT_TRANSITION_PROJECTION_MISMATCH"
        ):
            self._validate(projection)

        future = copy.deepcopy(self.proposal)
        later_record = next(
            item
            for item in future["story_transition_support"]
            if e1._transition_key(
                item["storyline_id"], item["from_state_index"]
            )
            == later
        )
        later_step_ids = {
            claim["step_id"] for claim in later_record["support_claims"]
        }
        fact = next(
            fact
            for fact in future["capability_fact_registry"]
            if later in fact["producer_transition_keys"]
            and any(
                fact["id"] in step["produces_fact_ids"]
                for step in future["capability_step_registry"]
                if step["id"] in later_step_ids
            )
        )
        earlier_record = next(
            item
            for item in future["story_transition_support"]
            if e1._transition_key(
                item["storyline_id"], item["from_state_index"]
            )
            == earlier
        )
        consumer_step_id = earlier_record["support_claims"][0]["step_id"]
        consumer_step = next(
            item
            for item in future["capability_step_registry"]
            if item["id"] == consumer_step_id
        )
        if fact["id"] not in consumer_step["requires_fact_ids"]:
            consumer_step["requires_fact_ids"].append(fact["id"])
        if consumer_step_id not in fact["consumer_step_ids"]:
            fact["consumer_step_ids"].append(consumer_step_id)
        steps_by_id = {
            item["id"]: item for item in future["capability_step_registry"]
        }
        for transition in future["story_transition_support"]:
            transition["required_fact_ids"] = sorted(
                {
                    fact_id
                    for claim in transition["support_claims"]
                    for fact_id in steps_by_id[claim["step_id"]][
                        "requires_fact_ids"
                    ]
                }
            )
        fact["cross_line_dependency"] = {
            "source_transition_key": later,
            "consumer_transition_key": earlier,
            "precedence_status": "incomparable_dependency_candidate",
            "s1_precedence_edge_ids": [],
        }
        with self.assertRaisesRegex(e1.E1Error, "E1_CROSS_LINE_FUTURE_DEPENDENCY"):
            self._validate(future)

        disclosure = copy.deepcopy(self.proposal)
        obligation = disclosure["obligation_capability_readiness"][0]
        disclosed = disclosure["capability_fact_registry"][0]["id"]
        obligation["allowed_disclosure_fact_ids"] = [disclosed]
        obligation["forbidden_disclosure_fact_ids"] = [disclosed]
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_DISCLOSURE_CONTRADICTION"
        ):
            self._validate(disclosure)

        inherited = copy.deepcopy(self.proposal)
        obligation = inherited["obligation_capability_readiness"][0]
        obligation["readiness_mode"] = "inherited_anchor_path"
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_INHERITED_PATH_HAS_EXTRAS"
        ):
            self._validate(inherited)

        empty_direct = copy.deepcopy(self.proposal)
        direct = empty_direct["obligation_capability_readiness"][0]
        direct["required_fact_ids"] = []
        direct["occurrence_requirement_ids"] = []
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_DIRECT_PATH_EMPTY"
        ):
            self._validate(empty_direct)

        shared_positive = copy.deepcopy(self.proposal)
        first_record, second_record = shared_positive[
            "obligation_capability_readiness"
        ][:2]
        shared_step_id = first_record["required_step_ids"][0]
        shared_step = next(
            item
            for item in shared_positive["capability_step_registry"]
            if item["id"] == shared_step_id
        )
        second_record["required_step_ids"] = [shared_step_id]
        second_record["required_fact_ids"] = sorted(
            {
                *shared_step["requires_fact_ids"],
                *shared_step["produces_fact_ids"],
            }
        )
        second_binding = next(
            item
            for item in shared_positive["obligation_occurrence_bindings"]
            if item["obligation_id"] == second_record["obligation_id"]
        )
        second_occurrence = next(
            item
            for item in shared_positive["capability_occurrence_requirements"]
            if item["id"] == second_binding["occurrence_requirement_id"]
        )
        second_occurrence["step_id"] = shared_step_id
        old_binding_id = second_binding["id"]
        second_binding["step_id"] = shared_step_id
        second_binding["id"] = e1._v24_obligation_occurrence_binding_id(
            obligation_id=second_binding["obligation_id"],
            occurrence_id=second_binding["occurrence_requirement_id"],
            step_id=shared_step_id,
            support_id=second_binding["support_id"],
        )
        shared_positive["authority_partition"]["autonomous_owned"] = [
            second_binding["id"] if item == old_binding_id else item
            for item in shared_positive["authority_partition"]["autonomous_owned"]
        ]
        self._validate(shared_positive)
        first_binding = next(
            item
            for item in shared_positive["obligation_occurrence_bindings"]
            if item["obligation_id"] == first_record["obligation_id"]
        )
        self.assertEqual(first_binding["step_id"], second_binding["step_id"])
        self.assertNotEqual(
            first_binding["occurrence_requirement_id"],
            second_binding["occurrence_requirement_id"],
        )

        missing_owned = copy.deepcopy(self.proposal)
        missing_owned["obligation_occurrence_bindings"].pop(0)
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_DIRECT_OCCURRENCE_MISMATCH"
        ):
            self._validate(missing_owned)

        wrong_step = copy.deepcopy(self.proposal)
        bad_binding = wrong_step["obligation_occurrence_bindings"][0]
        foreign_step = next(
            item["id"]
            for item in wrong_step["capability_step_registry"]
            if item["id"] != bad_binding["step_id"]
        )
        bad_binding["step_id"] = foreign_step
        bad_binding["id"] = e1._v24_obligation_occurrence_binding_id(
            obligation_id=bad_binding["obligation_id"],
            occurrence_id=bad_binding["occurrence_requirement_id"],
            step_id=foreign_step,
            support_id=bad_binding["support_id"],
        )
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_OCCURRENCE_BINDING_INVALID"
        ):
            self._validate(wrong_step)

        cross_obligation = copy.deepcopy(self.proposal)
        first, second = cross_obligation["obligation_occurrence_bindings"][:2]
        first["obligation_id"] = second["obligation_id"]
        first["support_id"] = second["support_id"]
        first["id"] = e1._v24_obligation_occurrence_binding_id(
            obligation_id=first["obligation_id"],
            occurrence_id=first["occurrence_requirement_id"],
            step_id=first["step_id"],
            support_id=first["support_id"],
        )
        with self.assertRaisesRegex(
            e1.E1Error,
            "E1_OBLIGATION_(DIRECT_OCCURRENCE_MISMATCH|OCCURRENCE_BINDING_COVERAGE_MISMATCH)",
        ):
            self._validate(cross_obligation)

        wrong_support = copy.deepcopy(self.proposal)
        bad_support_binding = wrong_support["obligation_occurrence_bindings"][0]
        foreign_support = next(
            item["support_id"]
            for item in wrong_support["obligation_occurrence_bindings"][1:]
            if item["support_id"] != bad_support_binding["support_id"]
        )
        bad_support_binding["support_id"] = foreign_support
        bad_support_binding["id"] = e1._v24_obligation_occurrence_binding_id(
            obligation_id=bad_support_binding["obligation_id"],
            occurrence_id=bad_support_binding["occurrence_requirement_id"],
            step_id=bad_support_binding["step_id"],
            support_id=foreign_support,
        )
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_DIRECT_OCCURRENCE_MISMATCH"
        ):
            self._validate(wrong_support)

        surplus = copy.deepcopy(self.proposal)
        source_binding = surplus["obligation_occurrence_bindings"][0]
        source_occurrence = next(
            item
            for item in surplus["capability_occurrence_requirements"]
            if item["id"] == source_binding["occurrence_requirement_id"]
        )
        surplus_occurrence = copy.deepcopy(source_occurrence)
        surplus_occurrence["id"] = "COR-SURPLUS-OBLIGATION"
        surplus_occurrence["semantic_review_claim_id"] = (
            "CLAIM-E1-OCC-SURPLUS-OBLIGATION"
        )
        surplus["capability_occurrence_requirements"].append(surplus_occurrence)
        surplus_binding = {
            **source_binding,
            "occurrence_requirement_id": surplus_occurrence["id"],
        }
        surplus_binding["id"] = e1._v24_obligation_occurrence_binding_id(
            obligation_id=surplus_binding["obligation_id"],
            occurrence_id=surplus_binding["occurrence_requirement_id"],
            step_id=surplus_binding["step_id"],
            support_id=surplus_binding["support_id"],
        )
        surplus["obligation_occurrence_bindings"].append(surplus_binding)
        with self.assertRaisesRegex(
            e1.E1Error, "E1_OBLIGATION_DIRECT_OCCURRENCE_MISMATCH"
        ):
            self._validate(surplus)

        request = {
            "schema_version": "1.0",
            "stage": "E1",
            "review_kind": "authority-capability-semantics",
            "review_protocol": e1.AUTHORITY_REVIEW_PROTOCOL,
            "run_id": "RUN",
            "session_id": "SESSION",
            "producer_thread_id": "producer",
            "candidate_sha256": "a" * 64,
            "claims": [{"id": "CLAIM-A"}],
        }
        with self.assertRaisesRegex(e1.E1Error, "E1_REVIEW_TASK_RECEIPT_INVALID"):
            e1._normalize_claim_review(
                root=self.work,
                request=request,
                reviewer_thread_id="reviewer",
                review={
                    "claim_verdicts": [
                        {
                            "claim_id": "CLAIM-A",
                            "verdict": "pass",
                            "rationale": "bounded",
                        }
                    ],
                    "reviewer_task_receipt": {
                        "task_id": "TASK",
                        "producer_thread_id": "producer",
                        "reviewer_thread_id": "reviewer",
                        "output_artifact": {
                            "path": "fake.json",
                            "sha256": "b" * 64,
                        },
                        "output_sha256": "0" * 64,
                    },
                },
                request_reference={"path": "request.json", "sha256": "c" * 64},
            )

    def test_one_trigger_may_bind_multiple_story_states(self) -> None:
        model = copy.deepcopy(self.proposal)
        transition = model["transition_contracts"][0]
        second = copy.deepcopy(transition["trigger_bindings"][0])
        second["source_state_index"] = 1
        second["target_state_index"] = 1
        transition["trigger_bindings"].append(second)
        self._validate(model)

    def test_one_trigger_cannot_claim_multiple_source_environments(self) -> None:
        model = copy.deepcopy(self.proposal)
        transition = model["transition_contracts"][0]
        second = copy.deepcopy(transition["trigger_bindings"][0])
        second["source_environment_id"] = model["environments"][1]["id"]
        transition["trigger_bindings"].append(second)
        with self.assertRaises(e1.E1Error) as caught:
            self._validate(model)
        self.assertEqual(
            "E1_TRANSITION_TRIGGER_BINDING_MISMATCH", caught.exception.code
        )

    def test_same_line_binding_cannot_reverse_story_state_order(self) -> None:
        model = copy.deepcopy(self.proposal)
        binding = model["transition_contracts"][0]["trigger_bindings"][0]
        binding["source_state_index"] = 1
        binding["target_state_index"] = 0
        with self.assertRaises(e1.E1Error) as caught:
            self._validate(model)
        self.assertEqual("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", caught.exception.code)

    def test_topology_binding_path_allows_multihop_but_rejects_cycles(self) -> None:
        topology = {
            "TOP-A-B": {
                "from_id": "ENV-A", "to_id": "ENV-B",
                "directionality": "forward", "transfer_capabilities": ["signal"],
            },
            "TOP-B-C": {
                "from_id": "ENV-B", "to_id": "ENV-C",
                "directionality": "forward", "transfer_capabilities": ["signal"],
            },
        }
        e1._validate_topology_path(
            ["TOP-A-B", "TOP-B-C"],
            source_environment_id="ENV-A",
            target_environment_id="ENV-C",
            transport_capability="signal",
            topology=topology,
            transition_id="TRANS-MULTIHOP",
        )
        with self.assertRaises(e1.E1Error) as caught:
            e1._validate_topology_path(
                ["TOP-A-B", "TOP-A-B", "TOP-B-C"],
                source_environment_id="ENV-A",
                target_environment_id="ENV-C",
                transport_capability="signal",
                topology=topology,
                transition_id="TRANS-CYCLE",
            )
        self.assertEqual("E1_TRIGGER_TOPOLOGY_PATH_INVALID", caught.exception.code)

    def test_optional_source_cannot_drive_required_target(self) -> None:
        model, transition = self._cross_line_model()
        storyline = copy.deepcopy(self.storyline)
        source_id = transition["trigger_bindings"][0]["source_storyline_id"]
        next(
            item for item in storyline["storylines"] if item["id"] == source_id
        )["type"] = "optional_melody"
        with self.assertRaises(e1.E1Error) as caught:
            self._validate_with_storyline(model, storyline)
        self.assertEqual("E1_OPTIONAL_TRIGGER_ESCALATION", caught.exception.code)

    def test_requires_all_obligation_needs_every_antecedent_binding(self) -> None:
        model = copy.deepcopy(self.proposal)
        storyline = copy.deepcopy(self.storyline)
        required_lines = [
            item for item in storyline["storylines"]
            if item["type"] != "optional_melody"
        ]
        target_line = next(item for item in required_lines if item["type"] == "main")
        source_lines = [item for item in required_lines if item["id"] != target_line["id"]][:2]
        self.assertEqual(2, len(source_lines))
        obligation = copy.deepcopy(storyline["story_obligation_register"][0])
        obligation.update(
            {
                "id": "SOB-E1-REQUIRES-ALL",
                "kind": "requires_all",
                "antecedent_anchors": [
                    {"storyline_id": item["id"], "state_index": 0, "state": item["start_state"]}
                    for item in source_lines
                ],
                "consequent_anchor": {
                    "storyline_id": target_line["id"],
                    "state_index": 0,
                    "state": target_line["start_state"],
                },
            }
        )
        storyline["story_obligation_register"].append(obligation)
        line_ids = {item["id"] for item in storyline["storylines"]}
        event_line = {
            item["id"]: next(source for source in item["source_ids"] if source in line_ids)
            for item in storyline["event_requirements"]
        }
        environments = {
            line_id: environment
            for environment in model["environments"]
            for line_id in environment["storyline_stage_ids"]
            if line_id in line_ids
        }
        affordances = {
            event_line[requirement_id]: affordance
            for affordance in model["event_affordance_catalog"]
            for requirement_id in affordance["event_requirement_ids"]
        }
        target_environment = environments[target_line["id"]]
        transition = next(
            item for item in model["transition_contracts"]
            if item["subject_id"] == target_environment["id"]
        )
        transition["trigger_ids"] = [affordances[item["id"]]["id"] for item in source_lines]
        transition["trigger_bindings"] = [
            {
                "trigger_id": affordances[item["id"]]["id"],
                "source_environment_id": environments[item["id"]]["id"],
                "source_storyline_id": item["id"],
                "source_state_index": 0,
                "target_storyline_id": target_line["id"],
                "target_state_index": 0,
                "causal_evidence_ids": [obligation["id"]],
                "topology_path_ids": topology_path(
                    model,
                    environments[item["id"]]["id"],
                    target_environment["id"],
                ),
                "transport_capability": (
                    "local"
                    if environments[item["id"]]["id"] == target_environment["id"]
                    else "story-causality-transfer"
                ),
            }
            for item in source_lines
        ]
        transition["allowed_by_ids"] = list(
            dict.fromkeys(
                [
                    *transition["allowed_by_ids"],
                    *[
                        assignment["id"]
                        for assignment in model["access_and_authority"]
                        if assignment["subject_id"]
                        in {
                            target_environment["id"],
                            *[environments[item["id"]]["id"] for item in source_lines],
                        }
                    ],
                ]
            )
        )
        self._validate_with_storyline(model, storyline)

        transition["trigger_ids"] = transition["trigger_ids"][:1]
        transition["trigger_bindings"] = transition["trigger_bindings"][:1]
        with self.assertRaises(e1.E1Error) as caught:
            self._validate_with_storyline(model, storyline)
        self.assertEqual("E1_TRIGGER_REQUIRES_ALL_INCOMPLETE", caught.exception.code)

    def test_phase3_rejects_unresolved_forward_affordance_before_evidence(self) -> None:
        workspace = self.work / "phase3-forward-workspace"
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-phase3-forward"}, clear=False
        ):
            e1.start_e1_session(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                world_package=self.w1,
                input_gate=self.gate,
            )
            for phase in e1.PHASES[:2]:
                e1.submit_e1_phase(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    world_package=self.w1,
                    input_gate=self.gate,
                    phase=phase,
                    payload={field: self.proposal[field] for field in e1.PHASE_FIELDS[phase]},
                )
            payload = {
                field: copy.deepcopy(self.proposal[field])
                for field in e1.PHASE_FIELDS["zones-and-topology"]
            }
            transition = payload["transition_contracts"][0]
            transition["trigger_ids"] = ["AFF-FORWARD-ONLY"]
            transition["trigger_bindings"][0]["trigger_id"] = "AFF-FORWARD-ONLY"
            with self.assertRaises(e1.E1Error) as caught:
                e1.submit_e1_phase(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    world_package=self.w1,
                    input_gate=self.gate,
                    phase="zones-and-topology",
                    payload=payload,
                )
        self.assertEqual("E1_TRANSITION_TRIGGER_INVALID", caught.exception.code)
        self.assertFalse(
            (workspace / "generation-evidence/03-zones-and-topology.json").exists()
        )
        self.assertIn(
            "event_affordance_catalog", e1.PHASE_FIELDS["zones-and-topology"]
        )

    def test_resealed_prose_artifact_is_a_boundary_violation(self) -> None:
        self.run_e1()
        for filename in (
            "chapterDraft.md",
            "draft.md",
            "generation-evidence/draft.md",
            "implementation/draft.md",
        ):
            with self.subTest(filename=filename):
                mutant = (
                    self.work
                    / "path-mutants"
                    / filename.replace(".", "-").replace("/", "-")
                )
                shutil.copytree(self.package, mutant)
                extra = mutant / filename
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text(
                    "# Unauthorized extra artifact\n", encoding="utf-8"
                )
                manifest_path = mutant / "package-manifest.json"
                manifest = json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )
                manifest["files"].append(
                    runtime.artifact_reference(extra, root=mutant)
                )
                manifest_path.write_text(
                    runtime.canonical_json(manifest), encoding="utf-8"
                )
                completion_path = mutant / "stage-completion.json"
                completion = json.loads(
                    completion_path.read_text(encoding="utf-8")
                )
                completion["manifest"]["sha256"] = runtime.sha256_file(
                    manifest_path
                )
                completion_path.write_text(
                    runtime.canonical_json(completion), encoding="utf-8"
                )

                with self.assertRaises(e1.E1Error) as caught:
                    e1.validate_e1_package(mutant)

                self.assertEqual(
                    "E1_BOUNDARY_VIOLATION", caught.exception.code
                )

    def test_package_allows_only_the_sealed_candidate_review_pair(self) -> None:
        self.run_e1()
        mutant = self.work / "review-boundary-mutant"
        shutil.copytree(self.package, mutant)
        extra = mutant / "hosting-semantic-reviews" / ("0" * 64) / "review.json"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("{}", encoding="utf-8")
        manifest_path = mutant / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(runtime.artifact_reference(extra, root=mutant))
        manifest_path.write_text(runtime.canonical_json(manifest), encoding="utf-8")
        completion_path = mutant / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        with self.assertRaises(e1.E1Error) as caught:
            e1.validate_e1_package(mutant)
        self.assertEqual("E1_BOUNDARY_VIOLATION", caught.exception.code)

    def test_fully_resealed_schema_downgrade_cannot_claim_legacy_trust(self) -> None:
        self.run_e1()
        mutant = self.work / "legacy-downgrade-mutant"
        shutil.copytree(self.package, mutant)
        self._reseal_as_legacy_disguise(mutant, self._legacy_model("2.1"))
        with self.assertRaises(e1.E1Error) as caught:
            e1.validate_e1_package(mutant)
        self.assertEqual("E1_LEGACY_PROVENANCE_UNTRUSTED", caught.exception.code)

    @staticmethod
    def _read_model(package: Path) -> dict[str, object]:
        return json.loads(
            (package / "environment-system.json").read_text(encoding="utf-8")
        )

    @staticmethod
    def _reseal_model(
        package: Path,
        model: dict[str, object],
        *,
        gate: dict[str, str],
    ) -> None:
        model_path = package / "environment-system.json"
        model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
        execution_path = package / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["output_sha256"] = runtime.canonical_sha256(model)
        execution["input_gate"] = copy.deepcopy(gate)
        execution_path.write_text(
            runtime.canonical_json(execution), encoding="utf-8"
        )
        manifest_path = package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        replacements = {
            "environment-system.json": runtime.artifact_reference(
                model_path, root=package
            ),
            "execution-record.json": runtime.artifact_reference(
                execution_path, root=package
            ),
        }
        manifest["files"] = [
            replacements.get(item["path"], item) for item in manifest["files"]
        ]
        manifest["artifact_roles"]["canonical"] = replacements[
            "environment-system.json"
        ]
        manifest["artifact_roles"]["execution_record"] = replacements[
            "execution-record.json"
        ]
        manifest_path.write_text(
            runtime.canonical_json(manifest), encoding="utf-8"
        )
        completion_path = package / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        completion["input_gate"] = copy.deepcopy(gate)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )

    @staticmethod
    def _reseal_as_legacy_disguise(
        package: Path, legacy_model: dict[str, object]
    ) -> None:
        session_path = package / "generation-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session.pop("implementation_bindings", None)
        session.pop("hosting_review_protocol", None)
        session.pop("authority_review_protocol", None)
        session.pop("review_source_bindings", None)
        session_path.write_text(runtime.canonical_json(session), encoding="utf-8")

        previous = None
        evidence_paths = []
        shared = (
            "run_id",
            "session_id",
            "thread_id",
            "input_gate",
            "state_before",
            "baseline_completion",
            "upstream_completions",
            "source_artifacts",
            "control_bindings",
            "storyline_bindings",
            "storyline_environment_requirement_bindings",
            "event_requirement_bindings",
            "world_rule_bindings",
            "environment_demand_bindings",
        )
        for index, phase in enumerate(e1.PHASES, 1):
            path = package / "generation-evidence" / f"{index:02d}-{phase}.json"
            payload = (
                {"model": copy.deepcopy(legacy_model)}
                if phase == "final-environment-model"
                else {
                    field: copy.deepcopy(legacy_model[field])
                    for field in e1.LEGACY_PHASE_FIELDS[phase]
                }
            )
            evidence = {
                "schema_version": "2.0",
                **{key: copy.deepcopy(session[key]) for key in shared},
                "stage": "E1",
                "phase": phase,
                "sequence": index,
                "previous_evidence_sha256": previous,
                "payload": payload,
                "payload_sha256": runtime.canonical_sha256(payload),
            }
            path.write_text(runtime.canonical_json(evidence), encoding="utf-8")
            previous = runtime.sha256_file(path)
            evidence_paths.append(path)

        model_path = package / "environment-system.json"
        model_path.write_text(
            runtime.canonical_json(legacy_model), encoding="utf-8"
        )
        index_path = package / "generation-evidence-index.json"
        evidence_index = json.loads(index_path.read_text(encoding="utf-8"))
        evidence_index["evidence"] = [
            runtime.artifact_reference(path, root=package)
            for path in evidence_paths
        ]
        index_path.write_text(
            runtime.canonical_json(evidence_index), encoding="utf-8"
        )
        execution_path = package / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["output_sha256"] = runtime.canonical_sha256(legacy_model)
        execution_path.write_text(
            runtime.canonical_json(execution), encoding="utf-8"
        )

        for review_root in (
            package / "hosting-semantic-reviews",
            package / "authority-semantic-reviews",
        ):
            if review_root.exists():
                shutil.rmtree(review_root)

        manifest_path = package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        changed = {
            path.relative_to(package).as_posix()
            for path in [
                model_path,
                session_path,
                index_path,
                execution_path,
                *evidence_paths,
            ]
        }
        manifest["files"] = [
            runtime.artifact_reference(package / item["path"], root=package)
            if item["path"] in changed
            else item
            for item in manifest["files"]
            if not item["path"].startswith("hosting-semantic-reviews/")
            and not item["path"].startswith("authority-semantic-reviews/")
        ]
        roles = manifest["artifact_roles"]
        roles["canonical"] = runtime.artifact_reference(model_path, root=package)
        roles["generation_session"] = runtime.artifact_reference(
            session_path, root=package
        )
        roles["generation_evidence_index"] = runtime.artifact_reference(
            index_path, root=package
        )
        roles["execution_record"] = runtime.artifact_reference(
            execution_path, root=package
        )
        manifest_path.write_text(runtime.canonical_json(manifest), encoding="utf-8")
        completion_path = package / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )


if __name__ == "__main__":
    unittest.main()
