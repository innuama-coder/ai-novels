"""Deterministic semantic contract for production T1 schema 2.3.

T1 2.3 extends the frozen 2.2 contract with ordered atomic event spans for
one adjacent storyline transition.  It deliberately imports, rather than
changes, the 2.2 implementation so sealed 2.2 packages keep their own replay
semantics.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping, Sequence

from . import contract_22 as _v22


Contract23Error = _v22.Contract22Error


def _fail(code: str, message: str) -> None:
    raise Contract23Error(code, message)


def _transition_key(value: Mapping[str, Any]) -> tuple[str, int, int]:
    return value["storyline_id"], value["from_state_index"], value["to_state_index"]


def _transition_spans(
    plan: Mapping[str, Any],
) -> dict[tuple[str, int, int], tuple[str, ...]]:
    return {
        _transition_key(record): tuple(record["event_ids"])
        for record in plan["transition_event_cover"]
    }


def _anchor_event_sides(
    plan: Mapping[str, Any], storyline: Mapping[str, Any]
) -> dict[tuple[str, int], tuple[str, str]]:
    lines = {item["id"]: item for item in storyline["storylines"]}
    found: dict[tuple[str, int], tuple[str, str]] = {}
    for record in plan["transition_event_cover"]:
        line_id = record["storyline_id"]
        event_ids = record["event_ids"]
        found.setdefault(
            (line_id, record["from_state_index"]), (event_ids[0], "before")
        )
        found[(line_id, record["to_state_index"])] = (event_ids[-1], "after")
    expected = {
        (line_id, index)
        for line_id, line in lines.items()
        for index in range(len(line["state_changes"]) + 2)
    }
    if set(found) != expected:
        _fail("T1_STORY_ANCHOR_EVENT_MAPPING_MISMATCH", "storyline anchors")
    return found


def _arrival_span(
    plan: Mapping[str, Any], anchor: Mapping[str, Any]
) -> tuple[str, ...]:
    line_id = anchor["storyline_id"]
    state_index = anchor["state_index"]
    if state_index == 0:
        for record in plan["transition_event_cover"]:
            if record["storyline_id"] == line_id and record["from_state_index"] == 0:
                return (record["event_ids"][0],)
    else:
        for record in plan["transition_event_cover"]:
            if (
                record["storyline_id"] == line_id
                and record["to_state_index"] == state_index
            ):
                return tuple(record["event_ids"])
    _fail("T1_STORY_ANCHOR_EVENT_MAPPING_MISMATCH", f"{line_id}/{state_index}")


def validate_transition_cover(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
    canonical_sha256: Callable[[Any], str],
) -> None:
    supports = {
        _transition_key(item): item
        for item in environment["story_transition_support"]
    }
    expected_values = _v22.adjacent_story_transitions(storyline, canonical_sha256)
    expected = {
        _transition_key(item): item
        for item in expected_values
    }
    edges = {
        (item["from_event_id"], item["to_event_id"])
        for item in plan["planned_causal_edges"]
    }
    line_by_id = {item["id"]: item for item in storyline["storylines"]}
    records: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    claimed_events: set[str] = set()
    for record in plan["transition_event_cover"]:
        key = _transition_key(record)
        event_ids = record["event_ids"]
        if (
            key in records
            or not event_ids
            or len(event_ids) != len(set(event_ids))
            or claimed_events.intersection(event_ids)
        ):
            _fail("T1_TRANSITION_EVENT_COVER_DUPLICATE", str(key))
        line = line_by_id.get(key[0])
        span = [events.get(event_id) for event_id in event_ids]
        if line is None or any(event is None for event in span):
            _fail("T1_TRANSITION_EVENT_COVER_MISMATCH", str(key))
        typed_span = [event for event in span if event is not None]
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        final = typed_span[-1]
        final_subject = final["changed_subject"]
        if (
            key not in expected
            or key not in supports
            or record["transition_support_id"] != supports[key]["id"]
            or any(key[0] not in event["storyline_ids"] for event in typed_span)
            or any(
                (left, right) not in edges
                for left, right in zip(event_ids, event_ids[1:])
            )
            or any(
                _v22._world_time_value(left["world_time_slot"], left["id"])
                >= _v22._world_time_value(right["world_time_slot"], right["id"])
                for left, right in zip(typed_span, typed_span[1:])
            )
            or sum(event["kind"] == "story_transition" for event in typed_span) != 1
            or final["kind"] != "story_transition"
            or final_subject["subject_id"] != key[0]
            or final_subject["before"] != states[key[1]]
            or final_subject["after"] != states[key[2]]
            or any(
                event["kind"] == "story_transition"
                or event["changed_subject"]["subject_id"] == key[0]
                for event in typed_span[:-1]
            )
        ):
            _fail("T1_TRANSITION_EVENT_SPAN_INVALID", str(key))
        records[key] = record
        claimed_events.update(event_ids)
    if set(records) != set(expected):
        _fail("T1_TRANSITION_EVENT_COVER_MISMATCH", "transition universe")


def validate_milestone_buckets(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
    environment: Mapping[str, Any] | None = None,
) -> None:
    milestones = {
        item["id"]: item
        for item in storyline["temporal_architecture"]["milestones"]
    }
    records = {
        item["milestone_id"]: item for item in plan["milestone_event_buckets"]
    }
    if len(records) != len(plan["milestone_event_buckets"]) or set(records) != set(milestones):
        _fail("T1_MILESTONE_BUCKET_COVERAGE_MISMATCH", "milestones")
    event_owners: dict[str, str] = {}
    previous_bucket_max: int | None = None
    first_arrival: dict[tuple[str, int], str] = {}
    for milestone in sorted(milestones.values(), key=lambda item: (item["order"], item["id"])):
        for ref in milestone["state_refs"]:
            key = (ref["storyline_id"], ref["state_index"])
            if ref["state_index"] > 0 and key not in first_arrival:
                first_arrival[key] = milestone["id"]
    readiness = {
        item["milestone_id"]: item
        for item in (environment or {}).get("milestone_capability_readiness", [])
    }
    for milestone in sorted(milestones.values(), key=lambda item: (item["order"], item["id"])):
        record = records[milestone["id"]]
        for field in ("order", "phase_id", "storyline_ids", "state_refs", "connection_ids"):
            if record[field] != milestone[field]:
                _fail("T1_MILESTONE_BUCKET_PROJECTION_MISMATCH", milestone["id"])
        has_first_arrival = any(
            ref["state_index"] > 0
            and first_arrival[(ref["storyline_id"], ref["state_index"])] == milestone["id"]
            for ref in milestone["state_refs"]
        )
        if not record["event_ids"] and (
            has_first_arrival
            or milestone["connection_ids"]
            or readiness.get(milestone["id"], {}).get("occurrence_requirement_ids", [])
        ):
            _fail("T1_MILESTONE_EMPTY_BUCKET_FORBIDDEN", milestone["id"])
        bucket_times: list[int] = []
        for event_id in record["event_ids"]:
            if event_id not in events or event_id in event_owners or events[event_id]["milestone_id"] != milestone["id"]:
                _fail("T1_MILESTONE_EVENT_OWNERSHIP_MISMATCH", event_id)
            event_owners[event_id] = milestone["id"]
            bucket_times.append(_v22._world_time_value(events[event_id]["world_time_slot"], event_id))
        if bucket_times and previous_bucket_max is not None and min(bucket_times) < previous_bucket_max:
            _fail("T1_MILESTONE_WORLD_TIME_NONMONOTONIC", milestone["id"])
        if bucket_times:
            previous_bucket_max = max(bucket_times)
    if set(event_owners) != set(events):
        _fail("T1_MILESTONE_EVENT_OWNERSHIP_MISMATCH", "planned events")
    for cover in plan["transition_event_cover"]:
        expected_milestone = first_arrival.get(
            (cover["storyline_id"], cover["to_state_index"])
        )
        if expected_milestone is not None and events[cover["event_ids"][-1]]["milestone_id"] != expected_milestone:
            _fail("T1_MILESTONE_FIRST_ARRIVAL_MISMATCH", str(_transition_key(cover)))


def validate_connections_and_obligations(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
    edges: set[tuple[str, str]],
    ancestors: Mapping[str, set[str]],
    *,
    connection_edges: set[tuple[str, str]] | None = None,
    association_ancestors: Mapping[str, set[str]] | None = None,
) -> None:
    connection_edges = edges if connection_edges is None else connection_edges
    association_ancestors = (
        ancestors if association_ancestors is None else association_ancestors
    )
    anchor_events = _anchor_event_sides(plan, storyline)
    timing_constraints = _v22._unique(
        plan["narrative_timing_constraints"], "T1_TIMING_CONSTRAINT_DUPLICATE"
    )
    for constraint_id, constraint in timing_constraints.items():
        if not set(constraint["event_ids"]).issubset(events):
            _fail("T1_TIMING_CONSTRAINT_EVENT_DANGLING", constraint_id)
    connections = {item["id"]: item for item in storyline["connections"]}
    readiness = {
        item["connection_id"]: item
        for item in environment["connection_path_readiness"]
    }
    paths = {item["connection_id"]: item for item in plan["connection_event_paths"]}
    requirement_lines = {
        requirement["id"]: next(
            source_id
            for source_id in requirement["source_ids"]
            if source_id in {line["id"] for line in storyline["storylines"]}
        )
        for requirement in storyline.get("event_requirements", [])
    }
    affordances = {
        item["id"]: item
        for item in environment.get("event_affordance_catalog", [])
    }
    steps = {item["id"]: item for item in environment["capability_step_registry"]}
    if len(paths) != len(plan["connection_event_paths"]) or set(paths) != set(connections) or set(readiness) != set(connections):
        _fail("T1_CONNECTION_EVENT_PATH_COVERAGE_MISMATCH", "connections")
    for connection_id, connection in connections.items():
        record = paths[connection_id]
        ready = readiness[connection_id]
        source = events.get(record["source_event_id"])
        target = events.get(record["target_event_id"])
        expected_source = anchor_events.get((connection["from_storyline_id"], connection["from_state_index"]))
        expected_target = anchor_events.get((connection["to_storyline_id"], connection["to_state_index"]))
        if (
            record["relation"] != connection["relation"]
            or source is None
            or target is None
            or ready["relation"] != connection["relation"]
            or expected_source is None
            or expected_source[0] != record["source_event_id"]
            or expected_target is None
            or expected_target[0] != record["target_event_id"]
            or connection["from_storyline_id"] not in source["storyline_ids"]
            or connection["to_storyline_id"] not in target["storyline_ids"]
        ):
            _fail("T1_CONNECTION_EVENT_PATH_MISMATCH", connection_id)
        if not set(record["timing_constraint_ids"]).issubset(timing_constraints) or not any(
            {record["source_event_id"], record["target_event_id"]}.issubset(timing_constraints[item]["event_ids"])
            for item in record["timing_constraint_ids"]
        ):
            _fail("T1_CONNECTION_TIMING_CONSTRAINT_MISMATCH", connection_id)
        if connection["relation"] == "associative":
            if (
                record["bridge_event_ids"]
                or record["source_endpoint_step_ids"]
                or record["target_endpoint_step_ids"]
                or record["transfer_fact_id"] is not None
                or record["topology_path_ids"]
                or record["predecessor_path_event_ids"]
                or record["target_event_id"]
                in association_ancestors[record["source_event_id"]]
                or record["source_event_id"]
                in association_ancestors[record["target_event_id"]]
            ):
                _fail("T1_ASSOCIATIVE_CONNECTION_CAUSAL_PATH_FORBIDDEN", connection_id)
            continue
        if (
            set(record["source_endpoint_step_ids"]) != set(ready["source_endpoint_step_ids"])
            or set(record["target_endpoint_step_ids"]) != set(ready["target_endpoint_step_ids"])
            or record["transfer_fact_id"] != ready["transfer_fact_id"]
            or record["topology_path_ids"] != ready["topology_path_ids"]
            or not set(record["source_endpoint_step_ids"]).issubset(source["e1_capability_step_ids"])
            or not set(record["target_endpoint_step_ids"]).issubset(target["e1_capability_step_ids"])
        ):
            _fail("T1_CONNECTION_E1_PATH_MISMATCH", connection_id)
        bridge_events = [events.get(event_id) for event_id in record["bridge_event_ids"]]
        if any(event is None or event["kind"] != "connection_bridge" for event in bridge_events):
            _fail("T1_CONNECTION_BRIDGE_EVENT_INVALID", connection_id)
        endpoint_lines = {
            connection["from_storyline_id"], connection["to_storyline_id"]
        }
        transport_step_ids = set(ready["transport_step_ids"])
        for bridge in bridge_events if affordances and requirement_lines else ():
            assert bridge is not None
            actual_transport_steps = (
                set(bridge["e1_capability_step_ids"]) & transport_step_ids
            )
            served_endpoint_lines = {
                requirement_lines[requirement_id]
                for step_id in actual_transport_steps
                for requirement_id in affordances[
                    steps[step_id]["affordance_id"]
                ]["event_requirement_ids"]
                if requirement_id in requirement_lines
            } & endpoint_lines
            if not served_endpoint_lines.issubset(bridge["storyline_ids"]):
                _fail(
                    "T1_CONNECTION_BRIDGE_STORYLINE_MISMATCH",
                    f"{connection_id}/{bridge['id']}",
                )
        if set(ready["transport_step_ids"]) != {
            step_id for event in bridge_events if event is not None
            for step_id in event["e1_capability_step_ids"]
        }:
            _fail("T1_CONNECTION_TRANSPORT_STEP_MISMATCH", connection_id)
        event_path = record["predecessor_path_event_ids"]
        if (
            not event_path
            or event_path[0] != record["source_event_id"]
            or event_path[-1] != record["target_event_id"]
            or not set(record["bridge_event_ids"]).issubset(event_path[1:-1])
            or any(
                (left, right) not in connection_edges
                for left, right in zip(event_path, event_path[1:])
            )
        ):
            _fail("T1_CONNECTION_PREDECESSOR_PATH_MISMATCH", connection_id)
        fact_id = record["transfer_fact_id"]
        if fact_id is None or not any(
            fact_id in events[event_id]["produces_capability_fact_ids"]
            for event_id in event_path[:-1]
        ) or not any(
            fact_id in events[event_id]["requires_capability_fact_ids"]
            for event_id in event_path[1:]
        ):
            _fail("T1_CONNECTION_TRANSFER_FACT_MISMATCH", connection_id)

    obligations = {
        item["id"]: item for item in storyline["story_obligation_register"]
    }
    obligation_plans = {
        item["obligation_id"]: item for item in plan["obligation_event_plan"]
    }
    if len(obligation_plans) != len(plan["obligation_event_plan"]) or set(obligation_plans) != set(obligations):
        _fail("T1_OBLIGATION_EVENT_PLAN_COVERAGE_MISMATCH", "obligations")
    propositions = {item["id"]: item for item in plan["planned_proposition_registry"]}
    event_times = {
        event_id: _v22._world_time_value(event["world_time_slot"], event_id)
        for event_id, event in events.items()
    }
    disclosures: dict[str, set[str]] = defaultdict(set)
    for event_id, event in events.items():
        for proposition_id in event["discloses_proposition_ids"]:
            disclosures[proposition_id].add(event_id)
    for obligation_id, obligation in obligations.items():
        record = obligation_plans[obligation_id]
        antecedent_sides = [
            anchor_events.get((anchor["storyline_id"], anchor["state_index"]))
            for anchor in obligation["antecedent_anchors"]
        ]
        consequent_side = anchor_events.get((
            obligation["consequent_anchor"]["storyline_id"],
            obligation["consequent_anchor"]["state_index"],
        ))
        if any(item is None for item in antecedent_sides) or consequent_side is None:
            _fail("T1_OBLIGATION_EVENT_PLAN_MISMATCH", obligation_id)
        expected_antecedents = [item[0] for item in antecedent_sides if item is not None]
        kind = obligation["kind"]
        allowed_consequents = (
            set(_arrival_span(plan, obligation["consequent_anchor"]))
            if kind in {"first_disclosure", "must_remain_unknown"}
            else {consequent_side[0]}
        )
        consequent = record["consequent_event_id"]
        if (
            record["kind"] != kind
            or record["antecedent_event_ids"] != expected_antecedents
            or consequent not in allowed_consequents
            or record["consequent_proposition_id"] not in propositions
            or not set(record["antecedent_proposition_ids"]).issubset(propositions)
            or record["audience"] != obligation["audience"]
        ):
            _fail("T1_OBLIGATION_EVENT_PLAN_MISMATCH", obligation_id)
        if len(record["antecedent_proposition_ids"]) != len(antecedent_sides):
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        for proposition_id in [*record["antecedent_proposition_ids"], record["consequent_proposition_id"]]:
            if obligation_id not in propositions[proposition_id]["source_ids"]:
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        proposition_id = record["consequent_proposition_id"]
        if kind in {"first_disclosure", "must_remain_unknown"}:
            if proposition_id != obligation["proposition_id"] or propositions[proposition_id]["audience"] != obligation["audience"]:
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        elif obligation["proposition_id"] is not None:
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        for side, antecedent_prop in zip(antecedent_sides, record["antecedent_proposition_ids"]):
            assert side is not None
            field = "requires_proposition_ids" if side[1] == "before" else "produces_proposition_ids"
            if antecedent_prop not in events[side[0]][field]:
                _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)
        if kind not in {"first_disclosure", "must_remain_unknown"}:
            field = "requires_proposition_ids" if consequent_side[1] == "before" else "produces_proposition_ids"
            if proposition_id not in events[consequent][field]:
                _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)
        if kind in {"causes", "requires_all"}:
            if not set(record["antecedent_proposition_ids"]).issubset(events[consequent]["requires_proposition_ids"]):
                _fail("T1_OBLIGATION_PROPOSITION_REQUIREMENT_MISSING", obligation_id)
            for source, side in zip(expected_antecedents, antecedent_sides):
                assert side is not None
                local = source == consequent and side[1] == "before" and consequent_side[1] == "after"
                if not local and source not in ancestors[consequent]:
                    _fail("T1_OBLIGATION_CAUSAL_ANCESTRY_MISSING", obligation_id)
        if kind == "strict_before" and any(event_times[source] >= event_times[consequent] for source in expected_antecedents):
            _fail("T1_OBLIGATION_STRICT_BEFORE_VIOLATION", obligation_id)
        if kind == "not_before" and any(event_times[source] > event_times[consequent] for source in expected_antecedents):
            _fail("T1_OBLIGATION_NOT_BEFORE_VIOLATION", obligation_id)
        if kind == "first_disclosure":
            disclosure_events = disclosures[proposition_id]
            if consequent not in disclosure_events or any(
                other != consequent and event_times[other] <= event_times[consequent]
                for other in disclosure_events
            ):
                _fail("T1_OBLIGATION_FIRST_DISCLOSURE_VIOLATION", obligation_id)
        if kind == "must_remain_unknown" and any(
            event_times[event_id] <= event_times[consequent]
            for event_id in disclosures[proposition_id]
        ):
            _fail("T1_OBLIGATION_PREMATURE_DISCLOSURE", obligation_id)


def validate_occurrence_cover(
    plan: Mapping[str, Any],
    environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
) -> None:
    requirements = _v22._unique(
        environment["capability_occurrence_requirements"], "T1_E1_OCCURRENCE_DUPLICATE"
    )
    records = {
        item["requirement_id"]: item
        for item in plan["capability_occurrence_event_cover"]
    }
    if len(records) != len(plan["capability_occurrence_event_cover"]) or set(records) != set(requirements):
        _fail("T1_CAPABILITY_OCCURRENCE_COVER_MISMATCH", "requirements")
    occurrence_items = [
        (occurrence["occurrence_id"], event_id, occurrence["step_id"])
        for event_id, event in events.items()
        for occurrence in event["capability_step_occurrences"]
    ]
    occurrences = {
        occurrence_id: (event_id, step_id)
        for occurrence_id, event_id, step_id in occurrence_items
    }
    if len(occurrences) != len(occurrence_items):
        _fail("T1_CAPABILITY_OCCURRENCE_DUPLICATE", "occurrence ids")
    group_events: dict[str, list[str]] = defaultdict(list)
    occurrence_requirements: dict[str, set[str]] = defaultdict(set)
    for requirement_id, requirement in requirements.items():
        ids = records[requirement_id]["occurrence_ids"]
        if len(ids) < requirement["minimum_occurrences"] or (
            requirement["maximum_occurrences"] is not None
            and len(ids) > requirement["maximum_occurrences"]
        ):
            _fail("T1_CAPABILITY_OCCURRENCE_CARDINALITY", requirement_id)
        for occurrence_id in ids:
            observed = occurrences.get(occurrence_id)
            if observed is None or observed[1] != requirement["step_id"]:
                _fail("T1_CAPABILITY_OCCURRENCE_COVER_MISMATCH", requirement_id)
            group_events[requirement["distinct_group_id"]].append(observed[0])
            occurrence_requirements[occurrence_id].add(requirement_id)
    for group, event_ids in group_events.items():
        if len(event_ids) != len(set(event_ids)):
            _fail("T1_CAPABILITY_OCCURRENCE_DISTINCT_VIOLATION", group)
    for occurrence_id, requirement_ids in occurrence_requirements.items():
        if len(requirement_ids) < 2:
            continue
        for requirement_id in requirement_ids:
            requirement = requirements[requirement_id]
            if requirement["share_policy"] == "exclusive" or (
                requirement["share_policy"] == "allow_list"
                and not (requirement_ids - {requirement_id}).issubset(set(requirement["allowed_shared_requirement_ids"]))
            ):
                _fail("T1_CAPABILITY_OCCURRENCE_SHARE_VIOLATION", occurrence_id)
    transition_events = {
        item["transition_support_id"]: set(item["event_ids"])
        for item in plan["transition_event_cover"]
    }
    initial_events: dict[str, set[str]] = defaultdict(set)
    for initial in plan["initial_condition_registry"]:
        for component in initial["atomic_components"]:
            for option_id in component["e1_support_option_ids"]:
                initial_events[option_id].update(component["planned_event_ids"])
    connection_events = {
        item["connection_id"]: {
            item["source_event_id"], *item["bridge_event_ids"], item["target_event_id"]
        }
        for item in plan["connection_event_paths"]
    }
    obligation_plans = {
        item["obligation_id"]: item for item in plan["obligation_event_plan"]
    }
    seen_bound_requirements: set[str] = set()
    for binding in environment.get("obligation_occurrence_bindings", []):
        requirement_id = binding["occurrence_requirement_id"]
        if requirement_id in seen_bound_requirements:
            _fail("T1_OBLIGATION_OCCURRENCE_BINDING_DUPLICATE", requirement_id)
        seen_bound_requirements.add(requirement_id)
        requirement = requirements.get(requirement_id)
        record = records.get(requirement_id)
        obligation_plan = obligation_plans.get(binding["obligation_id"])
        support_events = (
            transition_events.get(binding["support_id"])
            or initial_events.get(binding["support_id"])
            or connection_events.get(binding["support_id"])
        )
        occurrence_event_ids = [
            occurrences[occurrence_id][0]
            for occurrence_id in record["occurrence_ids"]
        ] if record is not None else []
        if (
            obligation_plan is None
            or requirement is None
            or record is None
            or requirement["step_id"] != binding["step_id"]
            or not support_events
            or any(event_id not in support_events for event_id in occurrence_event_ids)
        ):
            _fail("T1_OBLIGATION_OCCURRENCE_BINDING_MISMATCH", requirement_id)
        if obligation_plan["kind"] in {"first_disclosure", "must_remain_unknown"}:
            witness = obligation_plan["consequent_event_id"]
            if occurrence_event_ids.count(witness) != 1:
                _fail("T1_OBLIGATION_OCCURRENCE_WITNESS_MISMATCH", requirement_id)
            if obligation_plan["kind"] == "first_disclosure" and obligation_plan["consequent_proposition_id"] not in events[witness]["discloses_proposition_ids"]:
                _fail("T1_OBLIGATION_OCCURRENCE_WITNESS_MISMATCH", requirement_id)


def validate_planned_graph(
    plan: Mapping[str, Any],
    environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
    storyline: Mapping[str, Any] | None = None,
) -> tuple[
    dict[str, Mapping[str, Any]],
    set[tuple[str, str]],
    dict[str, set[str]],
]:
    """Validate 2.3 proposition references before 2.2 set projection.

    The 2.2 implementation intentionally remains frozen for historical replay.
    Its set-based proposition checks cannot observe duplicate references, so the
    current contract closes that gap on the raw Agent-authored lists before
    delegating the remainder of graph validation to 2.2.
    """

    fields = (
        "requires_proposition_ids",
        "produces_proposition_ids",
        "discloses_proposition_ids",
    )
    affordances = _v22._unique(
        environment.get("event_affordance_catalog", []),
        "T1_AFFORDANCE_DUPLICATE",
    )
    has_storyline_demands = (
        storyline is not None and "event_requirements" in storyline
    )
    line_ids = {
        line["id"] for line in storyline["storylines"]
    } if has_storyline_demands else set()
    requirement_lines = {
        requirement["id"]: next(
            source_id for source_id in requirement["source_ids"]
            if source_id in line_ids
        )
        for requirement in storyline["event_requirements"]
    } if has_storyline_demands else {}
    for event in plan["planned_event_registry"]:
        event_id = event.get("id")
        if not event["produces_proposition_ids"]:
            _fail(
                "T1_PLANNED_EVENT_PROPOSITION_OUTPUT_MISSING",
                f"{event_id}.produces_proposition_ids",
            )
        for field in fields:
            values = event[field]
            if len(values) != len(set(values)):
                _fail(
                    "T1_PLANNED_EVENT_PROPOSITION_REFERENCE_DUPLICATE",
                    f"{event_id}.{field}",
                )
        event_lines = set(event["storyline_ids"])
        for affordance_id in event["affordance_ids"] if affordances and has_storyline_demands else ():
            affordance = affordances.get(affordance_id)
            served_lines = {
                requirement_lines[requirement_id]
                for requirement_id in affordance["event_requirement_ids"]
                if affordance is not None and requirement_id in requirement_lines
            } if affordance is not None else set()
            if not event_lines & served_lines:
                _fail(
                    "T1_PLANNED_EVENT_AFFORDANCE_STORYLINE_MISMATCH",
                    f"{event_id}/{affordance_id}",
                )
    return _v22.validate_planned_graph(plan, environment, canonical_sha256)


def validate_p2_plan(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
    sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
    *,
    _validated_graph: tuple[
        dict[str, Mapping[str, Any]],
        set[tuple[str, str]],
        dict[str, set[str]],
    ] | None = None,
    _connection_edges: set[tuple[str, str]] | None = None,
    _association_ancestors: Mapping[str, set[str]] | None = None,
) -> None:
    _v22.validate_initial_conditions(plan, storyline, environment, canonical_sha256)
    events, pairs, ancestors = (
        validate_planned_graph(plan, environment, canonical_sha256, storyline)
        if _validated_graph is None
        else _validated_graph
    )
    validate_transition_cover(plan, storyline, environment, events, canonical_sha256)
    validate_milestone_buckets(plan, storyline, events, environment)
    validate_connections_and_obligations(
        plan,
        storyline,
        environment,
        events,
        pairs,
        ancestors,
        connection_edges=_connection_edges,
        association_ancestors=_association_ancestors,
    )
    validate_occurrence_cover(plan, environment, events)
    _v22.validate_authority_token_instances(plan, environment, events, canonical_sha256, sealed_value)

    component_events: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    for event_id, event in events.items():
        for ref in event["initial_anchor_refs"]:
            component_events[(ref["storyline_id"], ref["state_index"], ref["component_id"])].add(event_id)
    declared_components = {
        (anchor["storyline_id"], anchor["state_index"], component["component_id"])
        for anchor in plan["initial_condition_registry"]
        for component in anchor["atomic_components"]
    }
    if not set(component_events).issubset(declared_components):
        _fail("T1_INITIAL_EVENT_INVERSE_MISMATCH", "dangling event anchor ref")
    for anchor in plan["initial_condition_registry"]:
        for component in anchor["atomic_components"]:
            key = (anchor["storyline_id"], anchor["state_index"], component["component_id"])
            if component_events[key] != set(component["planned_event_ids"]):
                _fail("T1_INITIAL_EVENT_INVERSE_MISMATCH", str(key))
            if component["classification"] != "static_context":
                proposition_ids = set(component["proposition_ids"])
                for event_id in component["planned_event_ids"]:
                    event = events.get(event_id)
                    if event is None or not (set(event["produces_proposition_ids"]) & proposition_ids or event["produces_capability_fact_ids"]):
                        _fail("T1_ACTIVE_INITIAL_PRODUCER_MISSING", event_id)
                for proposition_id in proposition_ids:
                    proposition = next(item for item in plan["planned_proposition_registry"] if item["id"] == proposition_id)
                    if proposition["initially_true"] or not proposition["producer_event_ids"] or not set(proposition["producer_event_ids"]).issubset(component["planned_event_ids"]):
                        _fail("T1_INITIAL_PRODUCER_COMPONENT_MISMATCH", proposition_id)
            if component["classification"] == "active_process" and not any(events[event_id]["kind"] == "process" for event_id in component["planned_event_ids"]):
                _fail("T1_ACTIVE_INITIAL_PROCESS_EVENT_MISSING", component["component_id"])
            if component["classification"] == "connection_entry":
                connection_event_ids = {
                    event_id
                    for path in plan["connection_event_paths"]
                    for event_id in [path["source_event_id"], *path["bridge_event_ids"], path["target_event_id"]]
                }
                if not set(component["planned_event_ids"]).issubset(connection_event_ids):
                    _fail("T1_CONNECTION_INITIAL_PATH_MISMATCH", component["component_id"])

    for subject in plan["process_state_subject_registry"]:
        vocabulary = set(subject["state_vocabulary"])
        allowed = {(item["from"], item["to"]) for item in subject["allowed_transitions"]}
        if subject["source_state_vocabulary_hash"] != canonical_sha256(subject["state_vocabulary"]) or any(left not in vocabulary or right not in vocabulary for left, right in allowed):
            _fail("T1_PROCESS_SUBJECT_VOCABULARY_INVALID", subject["id"])
        subject_events = sorted(
            (
                event for event in events.values()
                if event["kind"] == "process" and event["changed_subject"]["subject_id"] == subject["id"]
            ),
            key=lambda event: (_v22._world_time_value(event["world_time_slot"], event["id"]), event["id"]),
        )
        if not subject_events:
            _fail("T1_PROCESS_SUBJECT_UNUSED", subject["id"])
        for event in subject_events:
            if (event["changed_subject"]["before"], event["changed_subject"]["after"]) not in allowed:
                _fail("T1_PROCESS_SUBJECT_TRANSITION_INVALID", event["id"])
        for previous, current in zip(subject_events, subject_events[1:]):
            if previous["changed_subject"]["after"] != current["changed_subject"]["before"] or previous["id"] not in ancestors[current["id"]]:
                _fail("T1_PROCESS_SUBJECT_CONTINUITY_INVALID", subject["id"])
    process_event_subjects = {
        event["changed_subject"]["subject_id"]
        for event in events.values() if event["kind"] == "process"
    }
    if process_event_subjects != {subject["id"] for subject in plan["process_state_subject_registry"]}:
        _fail("T1_PROCESS_SUBJECT_INVERSE_MISMATCH", "process events/subjects")


adjacent_story_transitions = _v22.adjacent_story_transitions
expected_e1_digests = _v22.expected_e1_digests
milestone_universe = _v22.milestone_universe
semantic_claim_records = _v22.semantic_claim_records
semantic_claim_universe = _v22.semantic_claim_universe
validate_authority_token_instances = _v22.validate_authority_token_instances
validate_initial_conditions = _v22.validate_initial_conditions
validate_p1_digests = _v22.validate_p1_digests
validate_p3_exact = _v22.validate_p3_exact


__all__ = [
    "Contract23Error", "adjacent_story_transitions", "expected_e1_digests",
    "milestone_universe", "semantic_claim_records", "semantic_claim_universe",
    "validate_authority_token_instances", "validate_initial_conditions",
    "validate_milestone_buckets", "validate_occurrence_cover",
    "validate_connections_and_obligations", "validate_p1_digests",
    "validate_p2_plan", "validate_p3_exact", "validate_planned_graph",
    "validate_transition_cover",
]
