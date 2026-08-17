"""Deterministic semantic contract for production T1 schema 2.4.

T1 2.4 separates narrative causality from execution dependencies.  The full
typed graph still establishes predecessor, reachability, proposition, fact,
and token ancestry.  Only ``narrative_causal`` edges may realize an S1 causal
connection or violate an S1 associative connection.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping, Sequence

from . import contract_22 as _v22
from . import contract_23 as _v23


Contract24Error = _v22.Contract22Error

EDGE_KINDS = frozenset(
    {
        "narrative_causal",
        "capability_dependency",
        "proposition_dependency",
        "token_dependency",
        "sequencing",
    }
)
DEPENDENCY_FIELDS = {
    "capability_dependency": (
        "produces_capability_fact_ids",
        "requires_capability_fact_ids",
    ),
    "proposition_dependency": (
        "produces_proposition_ids",
        "requires_proposition_ids",
    ),
    "token_dependency": (
        "produces_token_instance_ids",
        "requires_token_instance_ids",
    ),
}


def _fail(code: str, message: str) -> None:
    raise Contract24Error(code, message)


def _typed_graph(
    plan: Mapping[str, Any],
    environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
) -> tuple[
    dict[str, Mapping[str, Any]],
    set[tuple[str, str]],
    dict[str, set[str]],
    set[tuple[str, str]],
    dict[str, set[str]],
]:
    events = _v22._unique(
        plan["planned_event_registry"], "T1_PLANNED_EVENT_DUPLICATE"
    )
    edges = _v22._unique(
        plan["planned_causal_edges"], "T1_PLANNED_CAUSAL_EDGE_DUPLICATE"
    )
    typed_keys: set[tuple[str, str, str]] = set()
    all_pairs: set[tuple[str, str]] = set()
    narrative_pairs: set[tuple[str, str]] = set()
    for edge_id, edge in edges.items():
        left = edge["from_event_id"]
        right = edge["to_event_id"]
        kind = edge["edge_kind"]
        if (
            kind not in EDGE_KINDS
            or left not in events
            or right not in events
            or left == right
            or (left, right, kind) in typed_keys
        ):
            _fail("T1_PLANNED_TYPED_EDGE_INVALID", edge_id)
        typed_keys.add((left, right, kind))
        all_pairs.add((left, right))
        if kind == "narrative_causal":
            narrative_pairs.add((left, right))
        expected_payload: set[str] = set()
        if kind in DEPENDENCY_FIELDS:
            produced_field, required_field = DEPENDENCY_FIELDS[kind]
            expected_payload = set(events[left][produced_field]) & set(
                events[right][required_field]
            )
        if set(edge["payload_ids"]) != expected_payload:
            _fail("T1_EDGE_DEPENDENCY_PAYLOAD_MISMATCH", edge_id)

    # Reuse the frozen 2.2 event/fact/proposition contract over a pair-deduped
    # compatibility projection.  The projection is validation-only and never
    # changes the authored 2.4 model or its review hashes.
    legacy_plan = dict(plan)
    legacy_edges: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for edge in plan["planned_causal_edges"]:
        pair = (edge["from_event_id"], edge["to_event_id"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        legacy_edges.append(
            {
                key: edge[key]
                for key in (
                    "id",
                    "from_event_id",
                    "to_event_id",
                    "mechanism",
                    "necessary_condition",
                )
            }
        )
    legacy_plan["planned_causal_edges"] = legacy_edges
    validated_events, validated_pairs, ancestors = _v22.validate_planned_graph(
        legacy_plan, environment, canonical_sha256
    )
    if validated_pairs != all_pairs:
        _fail("T1_PLANNED_TYPED_EDGE_PROJECTION_MISMATCH", "all edge pairs")

    narrative_ancestors = _v22._ancestors(set(events), narrative_pairs)

    token_producers: dict[str, set[str]] = defaultdict(set)
    for event_id, event in events.items():
        for token_id in event["produces_token_instance_ids"]:
            token_producers[token_id].add(event_id)
    for event_id, event in events.items():
        for token_id in event["requires_token_instance_ids"]:
            producers = token_producers[token_id]
            if producers and not producers.intersection(ancestors[event_id]):
                _fail(
                    "T1_TOKEN_INSTANCE_ANCESTRY_MISSING",
                    f"{event_id}/{token_id}",
                )
    return (
        validated_events,
        validated_pairs,
        ancestors,
        narrative_pairs,
        narrative_ancestors,
    )


def validate_p2_plan(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
    sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
) -> None:
    events, pairs, ancestors, narrative_pairs, narrative_ancestors = _typed_graph(
        plan, environment, canonical_sha256
    )
    _v23.validate_p2_plan(
        plan,
        storyline,
        environment,
        canonical_sha256,
        sealed_value,
        _validated_graph=(events, pairs, ancestors),
        _connection_edges=narrative_pairs,
        _association_ancestors=narrative_ancestors,
    )


def validate_information_projection(
    model: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    events: Mapping[str, Mapping[str, Any]],
) -> None:
    """Close every authored disclosure to one sourced knowledge-state change.

    An information record is atomic in current 2.4: one event, one disclosed
    proposition and one E1 capability occurrence.  The occurrence must use a
    communication-capable step, while the subject and visible recipients must
    be participating actor slots admitted by that step.  S1 first-disclosure
    obligations additionally bind through the exact E1 obligation occurrence.
    """

    information = _v22._unique(
        model["information_changes"], "T1_INFORMATION_DUPLICATE"
    )
    steps = _v22._unique(
        environment["capability_step_registry"],
        "T1_E1_CAPABILITY_STEP_DUPLICATE",
    )
    occurrences: dict[str, tuple[str, str]] = {}
    for event_id, event in events.items():
        for occurrence in event["capability_step_occurrences"]:
            occurrence_id = occurrence["occurrence_id"]
            if occurrence_id in occurrences:
                _fail("T1_CAPABILITY_OCCURRENCE_DUPLICATE", occurrence_id)
            occurrences[occurrence_id] = (event_id, occurrence["step_id"])

    covers = {
        item["requirement_id"]: set(item["occurrence_ids"])
        for item in model["capability_occurrence_event_cover"]
    }
    if len(covers) != len(model["capability_occurrence_event_cover"]):
        _fail("T1_CAPABILITY_OCCURRENCE_COVER_DUPLICATE", "requirement")
    obligations = _v22._unique(
        storyline["story_obligation_register"],
        "T1_STORY_OBLIGATION_DUPLICATE",
    )
    plans = {
        item["obligation_id"]: item
        for item in model["obligation_event_plan"]
    }
    bindings_by_obligation: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for binding in environment.get("obligation_occurrence_bindings", []):
        bindings_by_obligation[binding["obligation_id"]].append(binding)

    covered_disclosures: set[tuple[str, str]] = set()
    covered_first_obligations: set[str] = set()
    for info_id, change in information.items():
        event_ids: Sequence[str] = change["event_ids"]
        if len(event_ids) != 1 or event_ids[0] not in events:
            _fail("T1_INFORMATION_EVENT_MISMATCH", info_id)
        event_id = event_ids[0]
        event = events[event_id]
        proposition_id = change["proposition_id"]
        if proposition_id not in event["discloses_proposition_ids"]:
            _fail("T1_INFORMATION_PROPOSITION_MISMATCH", info_id)

        occurrence_id = change["source_occurrence_id"]
        occurrence = occurrences.get(occurrence_id)
        if occurrence is None or occurrence[0] != event_id:
            _fail("T1_INFORMATION_SOURCE_OCCURRENCE_MISMATCH", info_id)
        step = steps.get(occurrence[1])
        if step is None or "communicate" not in step["supported_modes"]:
            _fail("T1_INFORMATION_SOURCE_OCCURRENCE_MISMATCH", info_id)

        visibility = set(change["visibility_ids"])
        if (
            not visibility
            or not visibility.issubset(event["participant_slot_ids"])
            or not visibility.issubset(step["actor_slot_ids"])
        ):
            _fail("T1_INFORMATION_VISIBILITY_MISMATCH", info_id)
        if change["subject_id"] not in visibility:
            _fail("T1_INFORMATION_SUBJECT_MISMATCH", info_id)

        for obligation_id in change["source_obligation_ids"]:
            obligation = obligations.get(obligation_id)
            plan = plans.get(obligation_id)
            if (
                obligation is None
                or plan is None
                or obligation["kind"] != "first_disclosure"
                or obligation["proposition_id"] != proposition_id
                or plan["kind"] != "first_disclosure"
                or plan["consequent_proposition_id"] != proposition_id
                or plan["consequent_event_id"] != event_id
            ):
                _fail("T1_INFORMATION_OBLIGATION_MISMATCH", info_id)
            valid_source = any(
                binding["step_id"] == occurrence[1]
                and occurrence_id
                in covers.get(binding["occurrence_requirement_id"], set())
                for binding in bindings_by_obligation.get(obligation_id, [])
            )
            if not valid_source:
                _fail("T1_INFORMATION_OBLIGATION_MISMATCH", info_id)
            covered_first_obligations.add(obligation_id)
        covered_disclosures.add((event_id, proposition_id))

    expected_disclosures = {
        (event_id, proposition_id)
        for event_id, event in events.items()
        for proposition_id in event["discloses_proposition_ids"]
    }
    if covered_disclosures != expected_disclosures:
        missing = sorted(expected_disclosures - covered_disclosures)
        _fail("T1_INFORMATION_DISCLOSURE_COVERAGE_MISSING", repr(missing))

    expected_first_obligations = {
        obligation_id
        for obligation_id, obligation in obligations.items()
        if obligation["kind"] == "first_disclosure"
    }
    if covered_first_obligations != expected_first_obligations:
        missing = sorted(expected_first_obligations - covered_first_obligations)
        _fail("T1_INFORMATION_FIRST_DISCLOSURE_COVERAGE_MISSING", repr(missing))


validate_p1_digests = _v23.validate_p1_digests
validate_p3_exact = _v23.validate_p3_exact
expected_e1_digests = _v23.expected_e1_digests
semantic_claim_records = _v23.semantic_claim_records
semantic_claim_universe = _v23.semantic_claim_universe


__all__ = [
    "Contract24Error",
    "DEPENDENCY_FIELDS",
    "EDGE_KINDS",
    "expected_e1_digests",
    "semantic_claim_records",
    "semantic_claim_universe",
    "validate_p1_digests",
    "validate_p2_plan",
    "validate_p3_exact",
    "validate_information_projection",
]
