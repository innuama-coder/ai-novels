"""Deterministic semantic contract for production T1 schema 2.2.

This module validates Agent-authored plans.  It never authors story events.
"""

from __future__ import annotations

import copy
import re
from collections import defaultdict, deque
from typing import Any, Callable, Mapping, Sequence


_HEX = re.compile(r"^[0-9a-f]{64}$")
_CAUSE = re.compile(
    r"^\[CAUSE_RESULT_SHA256:([0-9a-f]{64})\]"
    r"\[CAUSE_PRESSURE_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_PRECONDITION = re.compile(
    r"^\[PRECONDITION_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_WORLD_TIME = re.compile(r"^\[WT:(\d{6})\]$")


class Contract22Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise Contract22Error(code, message)


def _unique(values: Sequence[Mapping[str, Any]], code: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in values:
        identity = item.get("id")
        if not isinstance(identity, str) or identity in result:
            _fail(code, str(identity))
        result[identity] = item
    return result


def _is_acyclic(nodes: set[str], edges: set[tuple[str, str]]) -> bool:
    incoming = {node: 0 for node in nodes}
    adjacent = {node: set() for node in nodes}
    for left, right in edges:
        if left not in nodes or right not in nodes or left == right:
            return False
        if right not in adjacent[left]:
            adjacent[left].add(right)
            incoming[right] += 1
    queue = deque(node for node, count in incoming.items() if count == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in adjacent[node]:
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    return visited == len(nodes)


def _ancestors(nodes: set[str], edges: set[tuple[str, str]]) -> dict[str, set[str]]:
    parents: dict[str, set[str]] = {node: set() for node in nodes}
    for left, right in edges:
        parents[right].add(left)
    result: dict[str, set[str]] = {}
    for node in nodes:
        found: set[str] = set()
        frontier = list(parents[node])
        while frontier:
            current = frontier.pop()
            if current in found:
                continue
            found.add(current)
            frontier.extend(parents[current] - found)
        result[node] = found
    return result


def adjacent_story_transitions(storyline: Mapping[str, Any], canonical_sha256: Callable[[Any], str]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in storyline["storylines"]:
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        for index, (before, after) in enumerate(zip(states, states[1:])):
            values.append(
                {
                    "storyline_id": line["id"],
                    "from_state_index": index,
                    "to_state_index": index + 1,
                    "from_state_sha256": canonical_sha256(before),
                    "to_state_sha256": canonical_sha256(after),
                }
            )
    return sorted(values, key=lambda item: (item["storyline_id"], item["from_state_index"]))


def milestone_universe(storyline: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = ("id", "order", "phase_id", "storyline_ids", "state_refs", "connection_ids")
    values = []
    for source in storyline["temporal_architecture"]["milestones"]:
        item = {field: copy.deepcopy(source[field]) for field in fields}
        for field in ("storyline_ids", "state_refs", "connection_ids"):
            item[field] = sorted(item[field], key=lambda value: str(value))
        values.append(item)
    return sorted(values, key=lambda item: (item["order"], item["id"]))


def _digest_object(
    *, source_path: str, source_sha256: str, pointers: list[str], value: Any,
    canonical_sha256: Callable[[Any], str],
) -> dict[str, Any]:
    return {
        "algorithm": "v2-canonical-json-sha256",
        "source_artifact": {"stage": "E1", "path": source_path, "sha256": source_sha256},
        "source_pointers": pointers,
        "canonical_items_sha256": canonical_sha256(value),
    }


def expected_e1_digests(
    environment: Mapping[str, Any], *, source_path: str, source_sha256: str,
    canonical_sha256: Callable[[Any], str],
) -> dict[str, dict[str, Any]]:
    universe_pointers = [
        "/story_transition_universe_digest",
        "/milestone_universe_digest",
        "/connection_universe_digest",
        "/obligation_universe_digest",
    ]
    graph_pointers = [
        "/capability_fact_registry",
        "/capability_step_registry",
        "/actor_authority_bindings",
    ]
    occurrence_pointers = ["/capability_occurrence_requirements"]
    universe = [environment[pointer[1:]] for pointer in universe_pointers]
    graph = [
        sorted(environment[pointer[1:]], key=lambda item: item["id"])
        for pointer in graph_pointers
    ]
    occurrences = sorted(
        environment["capability_occurrence_requirements"], key=lambda item: item["id"]
    )
    return {
        "e1_universe_digest_bundle": _digest_object(
            source_path=source_path, source_sha256=source_sha256,
            pointers=universe_pointers, value=universe, canonical_sha256=canonical_sha256,
        ),
        "e1_capability_graph_digest": _digest_object(
            source_path=source_path, source_sha256=source_sha256,
            pointers=graph_pointers, value=graph, canonical_sha256=canonical_sha256,
        ),
        "e1_occurrence_requirement_digest": _digest_object(
            source_path=source_path, source_sha256=source_sha256,
            pointers=occurrence_pointers, value=occurrences, canonical_sha256=canonical_sha256,
        ),
    }


def validate_p1_digests(
    payload: Mapping[str, Any], environment: Mapping[str, Any], *, source_path: str,
    source_sha256: str, canonical_sha256: Callable[[Any], str],
) -> None:
    expected = expected_e1_digests(
        environment, source_path=source_path, source_sha256=source_sha256,
        canonical_sha256=canonical_sha256,
    )
    for key, value in expected.items():
        if payload.get(key) != value:
            _fail("T1_E1_DIGEST_MISMATCH", key)


def _anchor_key(value: Mapping[str, Any]) -> tuple[str, int]:
    return value["storyline_id"], value["state_index"]


def _transition_key(value: Mapping[str, Any]) -> tuple[str, int, int]:
    return value["storyline_id"], value["from_state_index"], value["to_state_index"]


def _classification_summary(values: set[str]) -> str:
    return next(iter(values)) if len(values) == 1 else "mixed"


def _world_time_value(value: str, identity: str) -> int:
    match = _WORLD_TIME.fullmatch(value)
    if match is None:
        _fail("T1_PLANNED_WORLD_TIME_INVALID", identity)
    return int(match.group(1))


def validate_initial_conditions(
    plan: Mapping[str, Any], storyline: Mapping[str, Any], environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
) -> None:
    records = plan["initial_condition_registry"]
    observed: dict[tuple[str, int], Mapping[str, Any]] = {}
    for item in records:
        key = _anchor_key(item)
        if key in observed:
            _fail("T1_INITIAL_ANCHOR_DUPLICATE", str(key))
        observed[key] = item
    expected = {
        (line["id"], 0): line["start_state"] for line in storyline["storylines"]
    }
    if set(observed) != set(expected):
        _fail("T1_INITIAL_ANCHOR_COVERAGE_MISMATCH", "state-0 anchors")

    propositions = _unique(plan["planned_proposition_registry"], "T1_PLANNED_PROPOSITION_DUPLICATE")
    support: dict[tuple[str, int], dict[str, Mapping[str, Any]]] = {}
    for anchor in environment["initial_anchor_support"]:
        key = _anchor_key(anchor)
        support[key] = {item["support_option_id"]: item for item in anchor["support_options"]}
    realizations = {
        item["support_option_id"]: item
        for item in environment["initial_anchor_option_realization_ledger"]
    }
    selected_pairs: set[tuple[tuple[str, int], str, str]] = set()
    selection_records: dict[tuple[tuple[str, int], str, str], Mapping[str, Any]] = {}
    for item in plan["initial_anchor_option_selection_ledger"]:
        key = (item["storyline_id"], item["state_index"])
        signature = (key, item["component_id"], item["support_option_id"])
        if signature in selected_pairs:
            _fail("T1_INITIAL_OPTION_SELECTION_DUPLICATE", str(signature))
        selected_pairs.add(signature)
        selection_records[signature] = item

    inverse_anchor_refs: dict[str, set[tuple[str, int]]] = defaultdict(set)
    for proposition_id, proposition in propositions.items():
        for ref in proposition["initial_anchor_refs"]:
            inverse_anchor_refs[proposition_id].add(_anchor_key(ref))

    expected_selections: set[tuple[tuple[str, int], str, str]] = set()
    semantic_claim_ids: set[str] = set()
    kind_map = {
        "static_context": "static_context_host",
        "active_process": "process_host",
        "connection_entry": "connection_entry_host",
    }
    for key, item in observed.items():
        if item["semantic_review_claim_id"] in semantic_claim_ids:
            _fail("T1_INITIAL_REVIEW_CLAIM_DUPLICATE", item["semantic_review_claim_id"])
        semantic_claim_ids.add(item["semantic_review_claim_id"])
        if item["state_index"] != 0 or item["state"] != expected[key]:
            _fail("T1_INITIAL_ANCHOR_MISMATCH", str(key))
        atomic_ids = item["atomic_proposition_ids"]
        if len(set(atomic_ids)) != len(atomic_ids) or not atomic_ids:
            _fail("T1_INITIAL_PROPOSITION_COVERAGE_MISMATCH", str(key))
        component_ids: set[str] = set()
        component_propositions: list[str] = []
        planned_union: set[str] = set()
        classifications: set[str] = set()
        for component in item["atomic_components"]:
            component_id = component["component_id"]
            if component_id in component_ids:
                _fail("T1_INITIAL_COMPONENT_DUPLICATE", component_id)
            component_ids.add(component_id)
            component_propositions.extend(component["proposition_ids"])
            classifications.add(component["classification"])
            planned_union.update(component["planned_event_ids"])
            option_ids = component["e1_support_option_ids"]
            if not option_ids or len(set(option_ids)) != len(option_ids):
                _fail("T1_INITIAL_OPTION_SELECTION_MISMATCH", component_id)
            for option_id in option_ids:
                option = support.get(key, {}).get(option_id)
                realization = realizations.get(option_id)
                if (
                    option is None or realization is None or realization.get("status") != "ready"
                    or option["capability_descriptor"]["support_kind"] != kind_map[component["classification"]]
                    or realization.get("capability_demand_id") != option["capability_demand_id"]
                    or realization.get("storyline_id") != key[0]
                    or realization.get("state_index") != key[1]
                    or realization.get("support_option_id") != option_id
                    or realization.get("descriptor_sha256")
                    != canonical_sha256(option["capability_descriptor"])
                ):
                    _fail("T1_INITIAL_OPTION_INCOMPATIBLE", f"{component_id}/{option_id}")
                selection = selection_records.get((key, component_id, option_id))
                if (
                    selection is None
                    or selection["capability_demand_id"] != option["capability_demand_id"]
                    or selection["realization_record_id"] != realization["id"]
                ):
                    _fail("T1_INITIAL_OPTION_SELECTION_MISMATCH", f"{component_id}/{option_id}")
                expected_selections.add((key, component_id, option_id))
            if component["classification"] == "static_context":
                if component["planned_event_ids"]:
                    _fail("T1_STATIC_INITIAL_EVENT_FORBIDDEN", component_id)
                for proposition_id in component["proposition_ids"]:
                    proposition = propositions.get(proposition_id)
                    if proposition is None or not proposition["initially_true"] or proposition["producer_event_ids"]:
                        _fail("T1_STATIC_INITIAL_PRODUCER_CONFLICT", proposition_id)
            else:
                if not component["planned_event_ids"]:
                    _fail("T1_ACTIVE_INITIAL_PRODUCER_MISSING", component_id)
        if sorted(component_propositions) != sorted(atomic_ids) or len(component_propositions) != len(set(component_propositions)):
            _fail("T1_INITIAL_PROPOSITION_COVERAGE_MISMATCH", str(key))
        if set(item["planned_event_ids"]) != planned_union:
            _fail("T1_INITIAL_EVENT_UNION_MISMATCH", str(key))
        if item["classification_summary"] != _classification_summary(classifications):
            _fail("T1_INITIAL_CLASSIFICATION_SUMMARY_MISMATCH", str(key))
        for proposition_id in atomic_ids:
            if proposition_id not in propositions or key not in inverse_anchor_refs[proposition_id]:
                _fail("T1_INITIAL_PROPOSITION_INVERSE_MISMATCH", proposition_id)
    if selected_pairs != expected_selections:
        _fail("T1_INITIAL_OPTION_SELECTION_MISMATCH", "selection ledger")

    forward_refs: dict[str, set[tuple[str, int]]] = defaultdict(set)
    for key, item in observed.items():
        for proposition_id in item["atomic_proposition_ids"]:
            forward_refs[proposition_id].add(key)
    if {key: value for key, value in inverse_anchor_refs.items() if value} != dict(forward_refs):
        _fail("T1_INITIAL_PROPOSITION_INVERSE_MISMATCH", "registry")


def validate_planned_graph(
    plan: Mapping[str, Any], environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str]
) -> tuple[dict[str, Mapping[str, Any]], set[tuple[str, str]], dict[str, set[str]]]:
    events = _unique(plan["planned_event_registry"], "T1_PLANNED_EVENT_DUPLICATE")
    process_subjects = _unique(plan["process_state_subject_registry"], "T1_PROCESS_SUBJECT_DUPLICATE")
    propositions = _unique(plan["planned_proposition_registry"], "T1_PLANNED_PROPOSITION_DUPLICATE")
    edges = _unique(plan["planned_causal_edges"], "T1_PLANNED_CAUSAL_EDGE_DUPLICATE")
    pairs: set[tuple[str, str]] = set()
    produced_by_event: dict[str, set[str]] = defaultdict(set)
    required_by_event: dict[str, set[str]] = defaultdict(set)
    initial_service: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    occurrence_ids: set[str] = set()
    capability_facts = _unique(
        environment["capability_fact_registry"], "T1_E1_CAPABILITY_FACT_DUPLICATE"
    )
    capability_steps = _unique(
        environment["capability_step_registry"], "T1_E1_CAPABILITY_STEP_DUPLICATE"
    )
    for event_id, event in events.items():
        _world_time_value(event["world_time_slot"], event_id)
        subject = event["changed_subject"]
        if subject["before"] == subject["after"]:
            _fail("T1_PLANNED_EVENT_DOMINANT_CHANGE_INVALID", event_id)
        if event["kind"] == "process" and subject["subject_id"] not in process_subjects:
            _fail("T1_PROCESS_SUBJECT_DANGLING", event_id)
        step_ids = set(event["e1_capability_step_ids"])
        if not step_ids.issubset(capability_steps):
            _fail("T1_CAPABILITY_STEP_DANGLING", event_id)
        occurrences = event["capability_step_occurrences"]
        if {item["step_id"] for item in occurrences} != step_ids:
            _fail("T1_CAPABILITY_OCCURRENCE_STEP_MISMATCH", event_id)
        for occurrence in occurrences:
            expected = "CSO-" + canonical_sha256(
                [event_id, occurrence["step_id"], occurrence["ordinal"]]
            )[:24]
            if occurrence["occurrence_id"] != expected or occurrence["occurrence_id"] in occurrence_ids:
                _fail("T1_CAPABILITY_OCCURRENCE_ID_INVALID", occurrence["occurrence_id"])
            occurrence_ids.add(occurrence["occurrence_id"])
        required_facts = set(event["requires_capability_fact_ids"])
        produced_facts = set(event["produces_capability_fact_ids"])
        if not (required_facts | produced_facts).issubset(capability_facts):
            _fail("T1_CAPABILITY_FACT_DANGLING", event_id)
        expected_required = {
            fact_id
            for step_id in step_ids
            for fact_id in capability_steps[step_id]["requires_fact_ids"]
        }
        expected_produced = {
            fact_id
            for step_id in step_ids
            for fact_id in capability_steps[step_id]["produces_fact_ids"]
        }
        if required_facts != expected_required or produced_facts != expected_produced:
            _fail("T1_CAPABILITY_STEP_FACT_PROJECTION_MISMATCH", event_id)
        for step_id in step_ids:
            step = capability_steps[step_id]
            if (
                step["environment_id"] != event["environment_id"]
                or step["affordance_id"] not in event["affordance_ids"]
                or step["action"] != event["initiating_action"]
            ):
                _fail("T1_CAPABILITY_STEP_LOCALITY_MISMATCH", f"{event_id}/{step_id}")
        for proposition_id in event["produces_proposition_ids"]:
            produced_by_event[event_id].add(proposition_id)
        for proposition_id in event["requires_proposition_ids"]:
            required_by_event[event_id].add(proposition_id)
        for ref in event["initial_anchor_refs"]:
            initial_service[(ref["storyline_id"], ref["state_index"], ref["component_id"])].add(event_id)

    for edge_id, edge in edges.items():
        left, right = edge["from_event_id"], edge["to_event_id"]
        if left not in events or right not in events or left == right or (left, right) in pairs:
            _fail("T1_PLANNED_CAUSAL_EDGE_INVALID", edge_id)
        mechanism = _CAUSE.fullmatch(edge["mechanism"])
        condition = _PRECONDITION.fullmatch(edge["necessary_condition"])
        if (
            mechanism is None or condition is None
            or mechanism.group(1) != canonical_sha256(events[left]["direct_result"])
            or mechanism.group(2) != canonical_sha256(events[left]["next_pressure"])
            or condition.group(1) not in {canonical_sha256(value) for value in events[right]["preconditions"]}
            or not mechanism.group(3).strip() or not condition.group(2).strip()
        ):
            _fail("T1_PLANNED_CAUSAL_EDGE_BINDING_INVALID", edge_id)
        pairs.add((left, right))
    if not _is_acyclic(set(events), pairs):
        _fail("T1_PLANNED_CAUSAL_CYCLE", "planned event graph")
    for event_id, event in events.items():
        incoming = {left for left, right in pairs if right == event_id}
        if set(event["predecessor_event_ids"]) != incoming:
            _fail("T1_PLANNED_PREDECESSOR_MISMATCH", event_id)
    ancestors = _ancestors(set(events), pairs)

    producers: dict[str, set[str]] = defaultdict(set)
    for event_id, values in produced_by_event.items():
        for proposition_id in values:
            producers[proposition_id].add(event_id)
    for proposition_id, proposition in propositions.items():
        if set(proposition["producer_event_ids"]) != producers[proposition_id]:
            _fail("T1_PLANNED_PROPOSITION_INVERSE_MISMATCH", proposition_id)
        if proposition["initially_true"] and producers[proposition_id]:
            _fail("T1_PLANNED_PROPOSITION_ORIGIN_CONFLICT", proposition_id)
        if not proposition["initially_true"] and not producers[proposition_id]:
            _fail("T1_PLANNED_PROPOSITION_PRODUCER_MISSING", proposition_id)
    for event_id, event in events.items():
        all_refs = set(event["requires_proposition_ids"]) | set(event["produces_proposition_ids"]) | set(event["discloses_proposition_ids"])
        if not all_refs.issubset(propositions):
            _fail("T1_PLANNED_PROPOSITION_DANGLING", event_id)
        for proposition_id in event["requires_proposition_ids"]:
            if propositions[proposition_id]["initially_true"]:
                continue
            if not (producers[proposition_id] & ancestors[event_id]):
                _fail("T1_PLANNED_PROPOSITION_ANCESTRY_MISSING", f"{event_id}/{proposition_id}")

    facts = defaultdict(set)
    for event_id, event in events.items():
        for fact_id in event["produces_capability_fact_ids"]:
            facts[fact_id].add(event_id)
    for event_id, event in events.items():
        for fact_id in event["requires_capability_fact_ids"]:
            fact = capability_facts[fact_id]
            if fact["root_policy"] == "root_allowed":
                continue
            if not (facts[fact_id] & ancestors[event_id]):
                _fail("T1_CAPABILITY_FACT_ANCESTRY_MISSING", f"{event_id}/{fact_id}")
    return events, pairs, ancestors


def validate_transition_cover(
    plan: Mapping[str, Any], storyline: Mapping[str, Any], environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]], canonical_sha256: Callable[[Any], str],
) -> None:
    supports = {_transition_key(item): item for item in environment["story_transition_support"]}
    expected_values = adjacent_story_transitions(storyline, canonical_sha256)
    expected = {
        (item["storyline_id"], item["from_state_index"], item["to_state_index"]): item
        for item in expected_values
    }
    records: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    event_claims: set[str] = set()
    line_by_id = {item["id"]: item for item in storyline["storylines"]}
    for record in plan["transition_event_cover"]:
        key = _transition_key(record)
        if key in records or record["event_id"] in event_claims:
            _fail("T1_TRANSITION_EVENT_COVER_DUPLICATE", str(key))
        event = events.get(record["event_id"])
        line = line_by_id.get(key[0])
        if event is None or line is None or event["kind"] != "story_transition":
            _fail("T1_TRANSITION_EVENT_COVER_MISMATCH", str(key))
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        subject = event["changed_subject"]
        if (
            key not in expected or key not in supports
            or record["transition_support_id"] != supports[key]["id"]
            or subject["subject_id"] != key[0]
            or subject["before"] != states[key[1]] or subject["after"] != states[key[2]]
        ):
            _fail("T1_TRANSITION_EVENT_COVER_MISMATCH", str(key))
        records[key] = record
        event_claims.add(record["event_id"])
    if set(records) != set(expected):
        _fail("T1_TRANSITION_EVENT_COVER_MISMATCH", "transition universe")


def validate_milestone_buckets(
    plan: Mapping[str, Any], storyline: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]], environment: Mapping[str, Any] | None = None,
) -> None:
    milestones = {item["id"]: item for item in storyline["temporal_architecture"]["milestones"]}
    records = {item["milestone_id"]: item for item in plan["milestone_event_buckets"]}
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
        has_required_occurrence = bool(
            readiness.get(milestone["id"], {}).get("occurrence_requirement_ids", [])
        )
        if not record["event_ids"] and (
            has_first_arrival or milestone["connection_ids"] or has_required_occurrence
        ):
            _fail("T1_MILESTONE_EMPTY_BUCKET_FORBIDDEN", milestone["id"])
        bucket_times: list[int] = []
        for event_id in record["event_ids"]:
            if event_id not in events or event_id in event_owners or events[event_id]["milestone_id"] != milestone["id"]:
                _fail("T1_MILESTONE_EVENT_OWNERSHIP_MISMATCH", event_id)
            event_owners[event_id] = milestone["id"]
            bucket_times.append(_world_time_value(events[event_id]["world_time_slot"], event_id))
        if bucket_times and previous_bucket_max is not None and min(bucket_times) < previous_bucket_max:
            _fail("T1_MILESTONE_WORLD_TIME_NONMONOTONIC", milestone["id"])
        if bucket_times:
            previous_bucket_max = max(bucket_times)
    if set(event_owners) != set(events):
        _fail("T1_MILESTONE_EVENT_OWNERSHIP_MISMATCH", "planned events")
    for cover in plan["transition_event_cover"]:
        key = (cover["storyline_id"], cover["to_state_index"])
        expected_milestone = first_arrival.get(key)
        # Milestones are selected temporal anchors, not an exhaustive copy of
        # every adjacent storyline state.  Enforce exact first arrival only
        # where S1 actually declares that state in a milestone.
        if (
            expected_milestone is not None
            and events[cover["event_id"]]["milestone_id"] != expected_milestone
        ):
            _fail("T1_MILESTONE_FIRST_ARRIVAL_MISMATCH", str(key))


def _anchor_event_sides(
    plan: Mapping[str, Any], storyline: Mapping[str, Any]
) -> dict[tuple[str, int], tuple[str, str]]:
    lines = {item["id"]: item for item in storyline["storylines"]}
    found: dict[tuple[str, int], tuple[str, str]] = {}
    for record in plan["transition_event_cover"]:
        line_id = record["storyline_id"]
        found.setdefault((line_id, record["from_state_index"]), (record["event_id"], "before"))
        found[(line_id, record["to_state_index"])] = (record["event_id"], "after")
    expected = {
        (line_id, index)
        for line_id, line in lines.items()
        for index in range(len(line["state_changes"]) + 2)
    }
    if set(found) != expected:
        _fail("T1_STORY_ANCHOR_EVENT_MAPPING_MISMATCH", "storyline anchors")
    return found


def validate_connections_and_obligations(
    plan: Mapping[str, Any], storyline: Mapping[str, Any], environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]], edges: set[tuple[str, str]], ancestors: Mapping[str, set[str]],
) -> None:
    anchor_events = _anchor_event_sides(plan, storyline)
    timing_constraints = _unique(
        plan["narrative_timing_constraints"], "T1_TIMING_CONSTRAINT_DUPLICATE"
    )
    for constraint_id, constraint in timing_constraints.items():
        if not set(constraint["event_ids"]).issubset(events):
            _fail("T1_TIMING_CONSTRAINT_EVENT_DANGLING", constraint_id)
    connections = {item["id"]: item for item in storyline["connections"]}
    readiness = {item["connection_id"]: item for item in environment["connection_path_readiness"]}
    paths = {item["connection_id"]: item for item in plan["connection_event_paths"]}
    if len(paths) != len(plan["connection_event_paths"]) or set(paths) != set(connections) or set(readiness) != set(connections):
        _fail("T1_CONNECTION_EVENT_PATH_COVERAGE_MISMATCH", "connections")
    for connection_id, connection in connections.items():
        record = paths[connection_id]
        ready = readiness[connection_id]
        source = events.get(record["source_event_id"])
        target = events.get(record["target_event_id"])
        expected_source = anchor_events.get(
            (connection["from_storyline_id"], connection["from_state_index"])
        )
        expected_target = anchor_events.get(
            (connection["to_storyline_id"], connection["to_state_index"])
        )
        if (
            record["relation"] != connection["relation"] or source is None or target is None
            or ready["relation"] != connection["relation"]
            or expected_source is None or expected_source[0] != record["source_event_id"]
            or expected_target is None or expected_target[0] != record["target_event_id"]
            or connection["from_storyline_id"] not in source["storyline_ids"]
            or connection["to_storyline_id"] not in target["storyline_ids"]
        ):
            _fail("T1_CONNECTION_EVENT_PATH_MISMATCH", connection_id)
        if (
            not set(record["timing_constraint_ids"]).issubset(timing_constraints)
            or not any(
                {record["source_event_id"], record["target_event_id"]}.issubset(
                    timing_constraints[constraint_id]["event_ids"]
                )
                for constraint_id in record["timing_constraint_ids"]
            )
        ):
            _fail("T1_CONNECTION_TIMING_CONSTRAINT_MISMATCH", connection_id)
        if connection["relation"] == "associative":
            if (
                record["bridge_event_ids"] or record["source_endpoint_step_ids"]
                or record["target_endpoint_step_ids"] or record["transfer_fact_id"] is not None
                or record["topology_path_ids"] or record["predecessor_path_event_ids"]
                or record["target_event_id"] in ancestors[record["source_event_id"]]
                or record["source_event_id"] in ancestors[record["target_event_id"]]
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
        if set(ready["transport_step_ids"]) != {
            step_id for event in bridge_events for step_id in event["e1_capability_step_ids"]
        }:
            _fail("T1_CONNECTION_TRANSPORT_STEP_MISMATCH", connection_id)
        event_path = record["predecessor_path_event_ids"]
        if (
            not event_path
            or event_path[0] != record["source_event_id"]
            or event_path[-1] != record["target_event_id"]
            or not set(record["bridge_event_ids"]).issubset(event_path[1:-1])
            or any(
            (left, right) not in edges for left, right in zip(event_path, event_path[1:])
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

    obligations = {item["id"]: item for item in storyline["story_obligation_register"]}
    obligation_plans = {item["obligation_id"]: item for item in plan["obligation_event_plan"]}
    if len(obligation_plans) != len(plan["obligation_event_plan"]) or set(obligation_plans) != set(obligations):
        _fail("T1_OBLIGATION_EVENT_PLAN_COVERAGE_MISMATCH", "obligations")
    propositions = {item["id"]: item for item in plan["planned_proposition_registry"]}
    event_times = {
        event_id: _world_time_value(event["world_time_slot"], event_id)
        for event_id, event in events.items()
    }
    disclosures: dict[str, set[str]] = defaultdict(set)
    for event_id, event in events.items():
        for proposition_id in event["discloses_proposition_ids"]:
            disclosures[proposition_id].add(event_id)
    for obligation_id, obligation in obligations.items():
        record = obligation_plans[obligation_id]
        antecedent_events = record["antecedent_event_ids"]
        consequent = record["consequent_event_id"]
        antecedent_sides = [
            anchor_events.get((anchor["storyline_id"], anchor["state_index"]))
            for anchor in obligation["antecedent_anchors"]
        ]
        consequent_side = anchor_events.get(
            (
                obligation["consequent_anchor"]["storyline_id"],
                obligation["consequent_anchor"]["state_index"],
            )
        )
        expected_antecedent_events = [item[0] for item in antecedent_sides if item is not None]
        if (
            record["kind"] != obligation["kind"] or consequent not in events
            or any(item not in events for item in antecedent_events)
            or any(item is None for item in antecedent_sides) or consequent_side is None
            or antecedent_events != expected_antecedent_events
            or consequent != consequent_side[0]
            or record["consequent_proposition_id"] not in propositions
            or not set(record["antecedent_proposition_ids"]).issubset(propositions)
            or record["audience"] != obligation["audience"]
        ):
            _fail("T1_OBLIGATION_EVENT_PLAN_MISMATCH", obligation_id)
        if len(record["antecedent_proposition_ids"]) != len(antecedent_sides):
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        for proposition_id in [
            *record["antecedent_proposition_ids"], record["consequent_proposition_id"]
        ]:
            if obligation_id not in propositions[proposition_id]["source_ids"]:
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        kind = obligation["kind"]
        if kind in {"first_disclosure", "must_remain_unknown"}:
            proposition_id = record["consequent_proposition_id"]
            if (
                proposition_id != obligation["proposition_id"]
                or propositions[proposition_id]["audience"] != obligation["audience"]
            ):
                _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        elif obligation["proposition_id"] is not None:
            _fail("T1_OBLIGATION_PROPOSITION_MISMATCH", obligation_id)
        for side, proposition_id in zip(
            antecedent_sides, record["antecedent_proposition_ids"]
        ):
            assert side is not None
            field = "requires_proposition_ids" if side[1] == "before" else "produces_proposition_ids"
            if proposition_id not in events[side[0]][field]:
                _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)
        if kind not in {"first_disclosure", "must_remain_unknown"}:
            field = (
                "requires_proposition_ids"
                if consequent_side[1] == "before"
                else "produces_proposition_ids"
            )
            if record["consequent_proposition_id"] not in events[consequent][field]:
                _fail("T1_OBLIGATION_ANCHOR_PROPOSITION_MISMATCH", obligation_id)
        if kind in {"causes", "requires_all"}:
            if not set(record["antecedent_proposition_ids"]).issubset(
                events[consequent]["requires_proposition_ids"]
            ):
                _fail("T1_OBLIGATION_PROPOSITION_REQUIREMENT_MISSING", obligation_id)
            for source, side in zip(antecedent_events, antecedent_sides):
                local = source == consequent and side[1] == "before" and consequent_side[1] == "after"
                if not local and source not in ancestors[consequent]:
                    _fail("T1_OBLIGATION_CAUSAL_ANCESTRY_MISSING", obligation_id)
        if kind == "strict_before" and any(
            event_times[source] >= event_times[consequent] for source in antecedent_events
        ):
            _fail("T1_OBLIGATION_STRICT_BEFORE_VIOLATION", obligation_id)
        if kind == "not_before" and any(
            event_times[source] > event_times[consequent] for source in antecedent_events
        ):
            _fail("T1_OBLIGATION_NOT_BEFORE_VIOLATION", obligation_id)
        if kind == "first_disclosure":
            proposition_id = record["consequent_proposition_id"]
            disclosure_events = disclosures[proposition_id]
            if consequent not in disclosure_events or any(
                other != consequent and event_times[other] <= event_times[consequent]
                for other in disclosure_events
            ):
                _fail("T1_OBLIGATION_FIRST_DISCLOSURE_VIOLATION", obligation_id)
        if kind == "must_remain_unknown" and any(
            event_times[event_id] <= event_times[consequent]
            for event_id in disclosures[record["consequent_proposition_id"]]
        ):
            _fail("T1_OBLIGATION_PREMATURE_DISCLOSURE", obligation_id)


def validate_occurrence_cover(
    plan: Mapping[str, Any], environment: Mapping[str, Any], events: Mapping[str, Mapping[str, Any]]
) -> None:
    requirements = _unique(environment["capability_occurrence_requirements"], "T1_E1_OCCURRENCE_DUPLICATE")
    records = {item["requirement_id"]: item for item in plan["capability_occurrence_event_cover"]}
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
        record = records[requirement_id]
        ids = record["occurrence_ids"]
        if len(ids) < requirement["minimum_occurrences"] or (
            requirement["maximum_occurrences"] is not None and len(ids) > requirement["maximum_occurrences"]
        ):
            _fail("T1_CAPABILITY_OCCURRENCE_CARDINALITY", requirement_id)
        for occurrence_id in ids:
            observed = occurrences.get(occurrence_id)
            if observed is None or observed[1] != requirement["step_id"]:
                _fail("T1_CAPABILITY_OCCURRENCE_COVER_MISMATCH", requirement_id)
            group_events[requirement["distinct_group_id"]].append(observed[0])
            occurrence_requirements[occurrence_id].add(requirement_id)
    for group, event_ids in group_events.items():
        # Distinct groups encode event-level injectivity.  Sharing policy only
        # governs whether multiple requirements may cite the same occurrence;
        # it never weakens the requirement that members of one distinct group
        # be realized by different atomic events.
        if len(event_ids) != len(set(event_ids)):
            _fail("T1_CAPABILITY_OCCURRENCE_DISTINCT_VIOLATION", group)
    for occurrence_id, requirement_ids in occurrence_requirements.items():
        if len(requirement_ids) < 2:
            continue
        for requirement_id in requirement_ids:
            requirement = requirements[requirement_id]
            if requirement["share_policy"] == "exclusive" or (
                requirement["share_policy"] == "allow_list"
                and not (requirement_ids - {requirement_id}).issubset(
                    set(requirement["allowed_shared_requirement_ids"])
                )
            ):
                _fail("T1_CAPABILITY_OCCURRENCE_SHARE_VIOLATION", occurrence_id)

    # E1 2.4 may reserve occurrence requirements for a direct obligation and
    # identify the exact transition, initial option, or connection support on
    # which that occurrence must happen.  T1 realizes that ownership; it may
    # not satisfy the requirement with another event that happens to use the
    # same capability step.
    transition_events = {
        item["transition_support_id"]: {item["event_id"]}
        for item in plan["transition_event_cover"]
    }
    initial_events: dict[str, set[str]] = defaultdict(set)
    for initial in plan["initial_condition_registry"]:
        for component in initial["atomic_components"]:
            for option_id in component["e1_support_option_ids"]:
                initial_events[option_id].update(component["planned_event_ids"])
    connection_events = {
        item["connection_id"]: {
            item["source_event_id"],
            *item["bridge_event_ids"],
            item["target_event_id"],
        }
        for item in plan["connection_event_paths"]
    }
    obligation_ids = {item["obligation_id"] for item in plan["obligation_event_plan"]}
    seen_bound_requirements: set[str] = set()
    for binding in environment.get("obligation_occurrence_bindings", []):
        requirement_id = binding["occurrence_requirement_id"]
        if requirement_id in seen_bound_requirements:
            _fail("T1_OBLIGATION_OCCURRENCE_BINDING_DUPLICATE", requirement_id)
        seen_bound_requirements.add(requirement_id)
        requirement = requirements.get(requirement_id)
        record = records.get(requirement_id)
        support_id = binding["support_id"]
        support_events = (
            transition_events.get(support_id)
            or initial_events.get(support_id)
            or connection_events.get(support_id)
        )
        if (
            binding["obligation_id"] not in obligation_ids
            or requirement is None
            or record is None
            or requirement["step_id"] != binding["step_id"]
            or not support_events
            or any(
                occurrences[occurrence_id][0] not in support_events
                for occurrence_id in record["occurrence_ids"]
            )
        ):
            _fail("T1_OBLIGATION_OCCURRENCE_BINDING_MISMATCH", requirement_id)


def _step_action(step: Mapping[str, Any]) -> tuple[str, str, str]:
    return step["environment_id"], step["affordance_id"], step["action"]


def validate_authority_token_instances(
    plan: Mapping[str, Any], environment: Mapping[str, Any], events: Mapping[str, Mapping[str, Any]],
    canonical_sha256: Callable[[Any], str], sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
) -> None:
    facts = {item["id"]: item for item in environment["capability_fact_registry"]}
    steps = {item["id"]: item for item in environment["capability_step_registry"]}
    instances = plan["authority_token_instance_ledger"]
    by_id: dict[str, Mapping[str, Any]] = {}
    pair_to_instance: dict[tuple[str, str], str] = {}
    event_by_occurrence = {
        occurrence["occurrence_id"]: (event_id, occurrence["step_id"])
        for event_id, event in events.items()
        for occurrence in event["capability_step_occurrences"]
    }
    event_requires = {event_id: set(item["requires_token_instance_ids"]) for event_id, item in events.items()}
    event_produces = {event_id: set(item["produces_token_instance_ids"]) for event_id, item in events.items()}
    ledger_requires: dict[str, set[str]] = defaultdict(set)
    ledger_produces: dict[str, set[str]] = defaultdict(set)
    observed_consumer_pairs: set[tuple[str, str]] = set()
    for instance in instances:
        identity = instance["token_instance_id"]
        if identity in by_id:
            _fail("T1_TOKEN_INSTANCE_DUPLICATE", identity)
        by_id[identity] = instance
        fact = facts.get(instance["token_fact_id"])
        if fact is None or fact.get("kind") != "authority_token" or any(
            instance[key] != fact[key] for key in ("token_kind", "consumption_policy")
        ):
            _fail("T1_TOKEN_INSTANCE_FACT_MISMATCH", identity)
        origin = instance["origin"]
        if origin["kind"] == "t1_produced":
            occurrence_id = origin["producer_occurrence_id"]
            pair = (fact["id"], occurrence_id)
            expected_id = "ATI-" + canonical_sha256(list(pair))[:24]
            observed = event_by_occurrence.get(occurrence_id)
            event = events.get(origin["producer_event_id"])
            if (
                identity != expected_id or pair in pair_to_instance
                or observed != (origin["producer_event_id"], origin["producer_step_id"])
                or event is None or origin["producer_step_id"] not in fact["producer_step_ids"]
                or fact["id"] not in event["produces_capability_fact_ids"]
                or _step_action(steps[origin["producer_step_id"]]) not in {
                    (item["environment_id"], item["affordance_id"], item["action"])
                    for item in fact["issuer_scope"]["action_bindings"]
                }
            ):
                _fail("T1_TOKEN_INSTANCE_PRODUCER_MISMATCH", identity)
            pair_to_instance[pair] = identity
            ledger_produces[origin["producer_event_id"]].add(identity)
        elif origin["kind"] == "upstream_sealed_initial":
            expected_id = "ATI-" + canonical_sha256(
                [fact["id"], origin["source_artifact"]["sha256"], origin["source_pointer"], origin["value_sha256"]]
            )[:24]
            if fact["root_policy"] != "root_allowed" or identity != expected_id:
                _fail("T1_TOKEN_INSTANCE_INITIAL_ORIGIN_INVALID", identity)
            anchor = fact.get("source_anchor", {})
            if (
                not isinstance(anchor, Mapping)
                or anchor.get("source_artifact") != origin["source_artifact"]
                or anchor.get("source_pointer") != origin["source_pointer"]
                or anchor.get("value_sha256") != origin["value_sha256"]
            ):
                _fail("T1_TOKEN_INSTANCE_INITIAL_ORIGIN_INVALID", identity)
            if sealed_value is not None:
                value = sealed_value(origin)
                if canonical_sha256(value) != origin["value_sha256"]:
                    _fail("T1_TOKEN_INSTANCE_INITIAL_SOURCE_STALE", identity)
        else:
            _fail("T1_TOKEN_INSTANCE_ORIGIN_INVALID", identity)
        consumers = instance["consumer_occurrences"]
        expected_claim = "T1TOK-" + canonical_sha256(
            [fact["id"], origin, consumers]
        )[:24]
        if instance["semantic_review_claim_id"] != expected_claim:
            _fail("T1_TOKEN_INSTANCE_CLAIM_INVALID", identity)
        if fact["consumption_policy"] == "single_use" and len(consumers) > 1:
            _fail("T1_TOKEN_INSTANCE_SINGLE_USE_VIOLATION", identity)
        if fact["consumption_policy"] == "non_consumable" and consumers:
            _fail("T1_TOKEN_INSTANCE_NONCONSUMABLE_VIOLATION", identity)
        seen_consumers: set[str] = set()
        for consumer in consumers:
            occurrence_id = consumer["occurrence_id"]
            event = events.get(consumer["event_id"])
            observed = event_by_occurrence.get(occurrence_id)
            if (
                occurrence_id in seen_consumers or event is None
                or observed != (consumer["event_id"], consumer["step_id"])
                or consumer["step_id"] not in fact["consumer_step_ids"]
                or fact["id"] not in event["requires_capability_fact_ids"]
                or _step_action(steps[consumer["step_id"]]) not in {
                    (item["environment_id"], item["affordance_id"], item["action"])
                    for item in fact["consumer_scope"]["action_bindings"]
                }
            ):
                _fail("T1_TOKEN_INSTANCE_CONSUMER_MISMATCH", identity)
            seen_consumers.add(occurrence_id)
            observed_consumer_pairs.add((fact["id"], occurrence_id))
            ledger_requires[consumer["event_id"]].add(identity)
    if event_requires != {key: ledger_requires[key] for key in events} or event_produces != {key: ledger_produces[key] for key in events}:
        _fail("T1_TOKEN_INSTANCE_EVENT_INVERSE_MISMATCH", "events/ledger")
    expected_producer_pairs: set[tuple[str, str]] = set()
    expected_consumer_pairs: set[tuple[str, str]] = set()
    authority_facts = {
        fact_id: fact for fact_id, fact in facts.items()
        if fact.get("kind") == "authority_token"
    }
    for event_id, event in events.items():
        for occurrence in event["capability_step_occurrences"]:
            for fact_id, fact in authority_facts.items():
                if (
                    occurrence["step_id"] in fact["producer_step_ids"]
                    and fact_id in event["produces_capability_fact_ids"]
                ):
                    expected_producer_pairs.add((fact_id, occurrence["occurrence_id"]))
                if (
                    fact["consumption_policy"] != "non_consumable"
                    and occurrence["step_id"] in fact["consumer_step_ids"]
                    and fact_id in event["requires_capability_fact_ids"]
                ):
                    expected_consumer_pairs.add((fact_id, occurrence["occurrence_id"]))
    if set(pair_to_instance) != expected_producer_pairs:
        _fail("T1_TOKEN_INSTANCE_PRODUCER_COVERAGE_MISMATCH", "producer occurrences")
    if observed_consumer_pairs != expected_consumer_pairs:
        _fail("T1_TOKEN_INSTANCE_CONSUMER_COVERAGE_MISMATCH", "consumer occurrences")


def validate_p2_plan(
    plan: Mapping[str, Any], storyline: Mapping[str, Any], environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str], sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
) -> None:
    validate_initial_conditions(plan, storyline, environment, canonical_sha256)
    events, pairs, ancestors_map = validate_planned_graph(
        plan, environment, canonical_sha256
    )
    validate_transition_cover(plan, storyline, environment, events, canonical_sha256)
    validate_milestone_buckets(plan, storyline, events, environment)
    validate_connections_and_obligations(
        plan, storyline, environment, events, pairs, ancestors_map
    )
    validate_occurrence_cover(plan, environment, events)
    validate_authority_token_instances(plan, environment, events, canonical_sha256, sealed_value)

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
                    if event is None or not (
                        set(event["produces_proposition_ids"]) & proposition_ids
                        or event["produces_capability_fact_ids"]
                    ):
                        _fail("T1_ACTIVE_INITIAL_PRODUCER_MISSING", event_id)
                for proposition_id in proposition_ids:
                    proposition = next(
                        item for item in plan["planned_proposition_registry"]
                        if item["id"] == proposition_id
                    )
                    if (
                        proposition["initially_true"]
                        or not proposition["producer_event_ids"]
                        or not set(proposition["producer_event_ids"]).issubset(
                            component["planned_event_ids"]
                        )
                    ):
                        _fail("T1_INITIAL_PRODUCER_COMPONENT_MISMATCH", proposition_id)
            if component["classification"] == "active_process" and not any(
                events[event_id]["kind"] == "process"
                for event_id in component["planned_event_ids"]
            ):
                _fail("T1_ACTIVE_INITIAL_PROCESS_EVENT_MISSING", component["component_id"])
            if component["classification"] == "connection_entry":
                connection_events = {
                    path_event
                    for path in plan["connection_event_paths"]
                    for path_event in [
                        path["source_event_id"], *path["bridge_event_ids"], path["target_event_id"]
                    ]
                }
                if not set(component["planned_event_ids"]).issubset(connection_events):
                    _fail("T1_CONNECTION_INITIAL_PATH_MISMATCH", component["component_id"])

    for subject in plan["process_state_subject_registry"]:
        vocabulary = set(subject["state_vocabulary"])
        allowed = {(item["from"], item["to"]) for item in subject["allowed_transitions"]}
        if (
            subject["source_state_vocabulary_hash"]
            != canonical_sha256(subject["state_vocabulary"])
            or any(left not in vocabulary or right not in vocabulary for left, right in allowed)
        ):
            _fail("T1_PROCESS_SUBJECT_VOCABULARY_INVALID", subject["id"])
        subject_events = sorted(
            (
                event for event in events.values()
                if event["kind"] == "process"
                and event["changed_subject"]["subject_id"] == subject["id"]
            ),
            key=lambda event: (_world_time_value(event["world_time_slot"], event["id"]), event["id"]),
        )
        if not subject_events:
            _fail("T1_PROCESS_SUBJECT_UNUSED", subject["id"])
        for event in subject_events:
            pair = (event["changed_subject"]["before"], event["changed_subject"]["after"])
            if pair not in allowed:
                _fail("T1_PROCESS_SUBJECT_TRANSITION_INVALID", event["id"])
        for previous, current in zip(subject_events, subject_events[1:]):
            if (
                previous["changed_subject"]["after"] != current["changed_subject"]["before"]
                or previous["id"] not in ancestors_map[current["id"]]
            ):
                _fail("T1_PROCESS_SUBJECT_CONTINUITY_INVALID", subject["id"])
    process_event_subjects = {
        event["changed_subject"]["subject_id"]
        for event in events.values()
        if event["kind"] == "process"
    }
    if process_event_subjects != {
        subject["id"] for subject in plan["process_state_subject_registry"]
    }:
        _fail("T1_PROCESS_SUBJECT_INVERSE_MISMATCH", "process events/subjects")


_EVENT_MAP = {
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


def validate_p3_exact(plan: Mapping[str, Any], model: Mapping[str, Any]) -> None:
    planned = _unique(plan["planned_event_registry"], "T1_PLANNED_EVENT_DUPLICATE")
    events = _unique(model["major_events"], "T1_EVENT_DUPLICATE")
    if set(planned) != set(events):
        _fail("T1_P3_EVENT_SET_MISMATCH", "planned/canonical")
    for event_id, source in planned.items():
        target = events[event_id]
        for source_field, target_field in _EVENT_MAP.items():
            if source[source_field] != target[target_field]:
                _fail("T1_P3_EVENT_PROJECTION_MISMATCH", f"{event_id}.{source_field}")
        subject = source["changed_subject"]
        if (
            target["subject_id"] != subject["subject_id"]
            or target["subject_kind"] != subject["subject_kind"]
            or target["before_state"] != {subject["subject_id"]: subject["before"]}
            or target["after_state"] != {subject["subject_id"]: subject["after"]}
        ):
            _fail("T1_P3_EVENT_SUBJECT_MISMATCH", event_id)
    proposition_fields = (
        "id", "statement", "source_ids", "audience", "initially_true", "terminality",
        "initial_anchor_refs", "producer_event_ids",
    )
    planned_props = sorted(
        [{field: item[field] for field in proposition_fields} for item in plan["planned_proposition_registry"]],
        key=lambda item: item["id"],
    )
    canonical_props = sorted(
        [{field: item[field] for field in proposition_fields} for item in model["proposition_registry"]],
        key=lambda item: item["id"],
    )
    if planned_props != canonical_props:
        _fail("T1_P3_PROPOSITION_PROJECTION_MISMATCH", "registry")
    if sorted(plan["planned_causal_edges"], key=lambda item: item["id"]) != sorted(model["causal_edges"], key=lambda item: item["id"]):
        _fail("T1_P3_CAUSAL_EDGE_PROJECTION_MISMATCH", "edges")


def semantic_claim_records(
    plan: Mapping[str, Any], canonical_sha256: Callable[[Any], str]
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []

    def add(claim_id: str, kind: str, pointer: str, value: Any) -> None:
        records.append(
            {
                "claim_id": claim_id,
                "claim_kind": kind,
                "candidate_pointer": pointer,
                "candidate_value_sha256": canonical_sha256(value),
            }
        )

    for anchor_index, item in enumerate(plan["initial_condition_registry"]):
        add(
            item["semantic_review_claim_id"], "initial_anchor",
            f"/initial_condition_registry/{anchor_index}", item,
        )
        for component_index, component in enumerate(item["atomic_components"]):
            add(
                "T1PLAN-" + canonical_sha256(
                    ["component", item["storyline_id"], item["state_index"], component]
                )[:24],
                "initial_component",
                f"/initial_condition_registry/{anchor_index}/atomic_components/{component_index}",
                component,
            )
    fields = (
        "narrative_timing_constraints",
        "initial_anchor_option_selection_ledger",
        "planned_event_registry",
        "planned_proposition_registry",
        "planned_causal_edges",
        "transition_event_cover",
        "milestone_event_buckets",
        "connection_event_paths",
        "obligation_event_plan",
        "capability_occurrence_event_cover",
        "process_state_subject_registry",
        "authority_token_instance_ledger",
    )
    own_claim_fields = {"process_state_subject_registry", "authority_token_instance_ledger"}
    for field in fields:
        for index, item in enumerate(plan[field]):
            claim_id = (
                item["semantic_review_claim_id"]
                if field in own_claim_fields
                else "T1PLAN-" + canonical_sha256([field, item])[:24]
            )
            add(claim_id, field, f"/{field}/{index}", item)
    identities = [item["claim_id"] for item in records]
    if len(identities) != len(set(identities)):
        _fail("T1_PLAN_REVIEW_CLAIM_DUPLICATE", "semantic claim universe")
    return sorted(records, key=lambda item: item["claim_id"])


def semantic_claim_universe(plan: Mapping[str, Any], canonical_sha256: Callable[[Any], str]) -> list[str]:
    return [item["claim_id"] for item in semantic_claim_records(plan, canonical_sha256)]


__all__ = [
    "Contract22Error", "adjacent_story_transitions", "expected_e1_digests",
    "milestone_universe", "semantic_claim_records", "semantic_claim_universe",
    "validate_authority_token_instances",
    "validate_initial_conditions", "validate_milestone_buckets", "validate_occurrence_cover",
    "validate_connections_and_obligations",
    "validate_p1_digests", "validate_p2_plan", "validate_p3_exact", "validate_planned_graph",
    "validate_transition_cover",
]
