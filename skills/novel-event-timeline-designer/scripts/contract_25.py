"""Typed lifecycle and causal-closure contract for production T1 schema 2.5.

This contract deliberately reasons only over authored identifiers, lifecycle
states, token instances, typed edges, and world occurrence time.  Narrative
presentation and disclosure order are separate concerns and are never scanned
to infer lifecycle state.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping

from . import contract_24 as _v24


Contract25Error = _v24.Contract24Error

LIFECYCLE_STATES = ("NOT_STARTED", "ACTIVE", "SHUTDOWN")
LIFECYCLE_EDGE_KINDS = frozenset(
    {"narrative_causal", "capability_dependency", "token_dependency"}
)


def _fail(code: str, message: str) -> None:
    raise Contract25Error(code, message)


def _reaches(
    source_id: str, target_id: str, pairs: set[tuple[str, str]]
) -> bool:
    frontier = [source_id]
    visited = {source_id}
    while frontier:
        current = frontier.pop()
        for left, right in pairs:
            if left != current or right in visited:
                continue
            if right == target_id:
                return True
            visited.add(right)
            frontier.append(right)
    return False


def _effective_precedes(
    source_id: str,
    target_id: str,
    *,
    events: Mapping[str, Mapping[str, Any]],
    all_pairs: set[tuple[str, str]],
) -> bool:
    """Compare occurrence time first and use the event DAG only for ties."""

    source_time = _v24._v22._world_time_value(
        events[source_id]["world_time_slot"], source_id
    )
    target_time = _v24._v22._world_time_value(
        events[target_id]["world_time_slot"], target_id
    )
    return source_time < target_time or (
        source_time == target_time
        and _reaches(source_id, target_id, all_pairs)
    )


def _collect_ids(value: Any, output: set[str]) -> None:
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            output.add(identifier)
        for child in value.values():
            _collect_ids(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_ids(child, output)


def validate_explicit_token_consumption(
    plan: Mapping[str, Any], events: Mapping[str, Mapping[str, Any]]
) -> None:
    """Close token-ledger consumers to explicit event consumption claims."""

    instances = {
        item["token_instance_id"]: item
        for item in plan["authority_token_instance_ledger"]
    }
    if len(instances) != len(plan["authority_token_instance_ledger"]):
        _fail("T1_TOKEN_INSTANCE_DUPLICATE", "authority token ledger")
    consumed_by_event: dict[str, set[str]] = {
        event_id: set(event["consumes_token_instance_ids"])
        for event_id, event in events.items()
    }
    for event_id, event in events.items():
        consumes = event["consumes_token_instance_ids"]
        if len(consumes) != len(set(consumes)):
            _fail("T1_TOKEN_INSTANCE_CONSUMPTION_DUPLICATE", event_id)
        if not set(consumes).issubset(event["requires_token_instance_ids"]):
            _fail("T1_TOKEN_INSTANCE_CONSUMPTION_WITHOUT_REQUIREMENT", event_id)
        if not set(consumes).issubset(instances):
            _fail("T1_TOKEN_INSTANCE_CONSUMPTION_DANGLING", event_id)

    ledger_consumers: dict[str, set[str]] = defaultdict(set)
    for token_id, instance in instances.items():
        consumers = instance["consumer_occurrences"]
        ledger_consumers[token_id].update(
            item["event_id"] for item in consumers
        )
        explicit_consumers = {
            event_id
            for event_id, token_ids in consumed_by_event.items()
            if token_id in token_ids
        }
        if instance["consumption_policy"] == "non_consumable":
            if consumers or explicit_consumers:
                _fail("T1_TOKEN_INSTANCE_NONCONSUMABLE_VIOLATION", token_id)
            continue
        if explicit_consumers != ledger_consumers[token_id]:
            _fail("T1_TOKEN_INSTANCE_CONSUMPTION_INVERSE_MISMATCH", token_id)
        if instance["consumption_policy"] == "single_use" and (
            len(consumers) != 1 or len(explicit_consumers) != 1
        ):
            _fail("T1_TOKEN_INSTANCE_SINGLE_USE_VIOLATION", token_id)


def validate_lifecycle_closure(
    plan: Mapping[str, Any],
    environment: Mapping[str, Any],
    storyline: Mapping[str, Any] | None = None,
) -> None:
    """Validate typed NOT_STARTED -> ACTIVE -> SHUTDOWN lifecycles."""

    events = _v24._v22._unique(
        plan["planned_event_registry"], "T1_PLANNED_EVENT_DUPLICATE"
    )
    edges = _v24._v22._unique(
        plan["planned_causal_edges"], "T1_PLANNED_CAUSAL_EDGE_DUPLICATE"
    )
    propositions = _v24._v22._unique(
        plan["planned_proposition_registry"],
        "T1_PLANNED_PROPOSITION_DUPLICATE",
    )
    process_subjects = _v24._v22._unique(
        plan["process_state_subject_registry"],
        "T1_PROCESS_SUBJECT_DUPLICATE",
    )
    token_instances = {
        item["token_instance_id"]: item
        for item in plan["authority_token_instance_ledger"]
    }
    token_facts = {
        item["id"]: item
        for item in environment["capability_fact_registry"]
        if item.get("kind") == "authority_token"
    }
    contracts = _v24._v22._unique(
        plan["lifecycle_contract_registry"],
        "T1_LIFECYCLE_CONTRACT_DUPLICATE",
    )
    storyline_ids: set[str] = set()
    environment_ids: set[str] = set()
    _collect_ids(storyline or {}, storyline_ids)
    _collect_ids(environment, environment_ids)
    scope = plan["lifecycle_scope"]
    if set(scope["lifecycle_contract_ids"]) != set(contracts):
        _fail("T1_LIFECYCLE_SCOPE_INVERSE_MISMATCH", scope["id"])
    if scope["applicability"] == "not_applicable":
        if contracts or any(
            event["lifecycle_effects"] for event in events.values()
        ):
            _fail("T1_LIFECYCLE_NOT_APPLICABLE_CONFLICT", scope["id"])
        validate_explicit_token_consumption(plan, events)
        return
    if not contracts:
        _fail("T1_LIFECYCLE_CONTRACT_MISSING", scope["id"])
    contract_source_ids = {
        source_id
        for contract in contracts.values()
        for source_id in contract["source_ids"]
    }
    if set(scope["source_ids"]) != contract_source_ids:
        _fail("T1_LIFECYCLE_SCOPE_SOURCE_INVERSE_MISMATCH", scope["id"])

    all_pairs: set[tuple[str, str]] = set()
    lifecycle_pairs: set[tuple[str, str]] = set()
    for edge in edges.values():
        pair = (edge["from_event_id"], edge["to_event_id"])
        all_pairs.add(pair)
        if edge["edge_kind"] in LIFECYCLE_EDGE_KINDS:
            lifecycle_pairs.add(pair)

    effects_by_contract: dict[str, list[tuple[str, Mapping[str, Any]]]] = (
        defaultdict(list)
    )
    for event_id, event in events.items():
        effects = event["lifecycle_effects"]
        signatures = {
            (item["lifecycle_contract_id"], item["transition_kind"])
            for item in effects
        }
        if len(signatures) != len(effects):
            _fail("T1_LIFECYCLE_EFFECT_DUPLICATE", event_id)
        for effect in effects:
            lifecycle_id = effect["lifecycle_contract_id"]
            if lifecycle_id not in contracts:
                _fail("T1_LIFECYCLE_EFFECT_DANGLING", event_id)
            effects_by_contract[lifecycle_id].append((event_id, effect))

    for lifecycle_id, contract in contracts.items():
        source_ids = set(contract["source_ids"])
        if storyline is not None and (
            not source_ids.intersection(storyline_ids)
            or not source_ids.intersection(environment_ids)
            or not source_ids.issubset(storyline_ids | environment_ids)
        ):
            _fail("T1_LIFECYCLE_SOURCE_BINDING_INVALID", lifecycle_id)
        if (
            contract["initial_state"],
            contract["active_state"],
            contract["terminal_state"],
        ) != LIFECYCLE_STATES:
            _fail("T1_LIFECYCLE_STATE_VOCABULARY_INVALID", lifecycle_id)
        subject_id = contract["subject_id"]
        subject = process_subjects.get(subject_id)
        if (
            subject is None
            or subject["state_vocabulary"] != list(LIFECYCLE_STATES)
            or subject["allowed_transitions"]
            != [
                {"from": "NOT_STARTED", "to": "ACTIVE"},
                {"from": "ACTIVE", "to": "SHUTDOWN"},
            ]
        ):
            _fail("T1_LIFECYCLE_PROCESS_SUBJECT_MISMATCH", lifecycle_id)

        acceptance_id = contract["acceptance_event_id"]
        producer_id = contract["permit_producer_event_id"]
        startup_id = contract["startup_event_id"]
        shutdown_id = contract["shutdown_event_id"]
        role_ids = [acceptance_id, producer_id, startup_id, shutdown_id]
        if len(set(role_ids)) != len(role_ids) or any(
            event_id not in events for event_id in role_ids
        ):
            _fail("T1_LIFECYCLE_EVENT_BINDING_INVALID", lifecycle_id)

        proposition_id = contract["acceptance_proposition_id"]
        proposition = propositions.get(proposition_id)
        if (
            proposition is None
            or proposition["initially_true"]
            or proposition["producer_event_ids"] != [acceptance_id]
            or proposition_id
            not in events[acceptance_id]["produces_proposition_ids"]
            or proposition_id
            not in events[producer_id]["requires_proposition_ids"]
        ):
            _fail("T1_LIFECYCLE_ACCEPTANCE_BINDING_INVALID", lifecycle_id)

        token_id = contract["permit_token_instance_id"]
        instance = token_instances.get(token_id)
        fact = (
            token_facts.get(instance["token_fact_id"])
            if instance is not None
            else None
        )
        consumers = instance["consumer_occurrences"] if instance else []
        if (
            instance is None
            or fact is None
            or instance["consumption_policy"] != "single_use"
            or instance["origin"].get("kind") != "t1_produced"
            or instance["origin"].get("producer_event_id") != producer_id
            or token_id
            not in events[producer_id]["produces_token_instance_ids"]
            or token_id not in events[startup_id]["requires_token_instance_ids"]
            or token_id not in events[startup_id]["consumes_token_instance_ids"]
            or len(consumers) != 1
            or consumers[0]["event_id"] != startup_id
        ):
            _fail("T1_LIFECYCLE_PERMIT_BINDING_INVALID", lifecycle_id)

        if not _reaches(acceptance_id, producer_id, lifecycle_pairs):
            _fail("T1_LIFECYCLE_ACCEPTANCE_CAUSAL_PATH_MISSING", lifecycle_id)
        if not _reaches(producer_id, startup_id, lifecycle_pairs):
            _fail("T1_LIFECYCLE_STARTUP_CAUSAL_PATH_MISSING", lifecycle_id)
        if not _effective_precedes(
            acceptance_id, startup_id, events=events, all_pairs=all_pairs
        ):
            _fail("T1_LIFECYCLE_ACCEPTANCE_AFTER_STARTUP", lifecycle_id)
        if not _effective_precedes(
            startup_id, shutdown_id, events=events, all_pairs=all_pairs
        ):
            _fail("T1_LIFECYCLE_SHUTDOWN_ORDER_INVALID", lifecycle_id)

        observed_effects = effects_by_contract[lifecycle_id]
        expected_effects = {
            (
                startup_id,
                "startup",
                "NOT_STARTED",
                "ACTIVE",
            ),
            (shutdown_id, "shutdown", "ACTIVE", "SHUTDOWN"),
        }
        actual_effects = {
            (
                event_id,
                effect["transition_kind"],
                effect["from_state"],
                effect["to_state"],
            )
            for event_id, effect in observed_effects
        }
        if actual_effects != expected_effects:
            _fail("T1_LIFECYCLE_EFFECT_COVERAGE_MISMATCH", lifecycle_id)

        for event_id, before, after in (
            (startup_id, "NOT_STARTED", "ACTIVE"),
            (shutdown_id, "ACTIVE", "SHUTDOWN"),
        ):
            changed = events[event_id]["changed_subject"]
            if (
                changed["subject_id"] != subject_id
                or changed["before"] != before
                or changed["after"] != after
            ):
                _fail("T1_LIFECYCLE_STATE_PROJECTION_MISMATCH", event_id)

        for event_id, event in events.items():
            changed = event["changed_subject"]
            if changed["subject_id"] != subject_id:
                continue
            if (
                event_id != startup_id
                and changed["after"] == "NOT_STARTED"
                and _effective_precedes(
                    startup_id, event_id, events=events, all_pairs=all_pairs
                )
            ):
                _fail("T1_LIFECYCLE_STATE_ROLLBACK", event_id)
            if event_id not in {startup_id, shutdown_id}:
                _fail("T1_LIFECYCLE_UNDECLARED_STATE_CHANGE", event_id)

    validate_explicit_token_consumption(plan, events)


def validate_p2_plan(
    plan: Mapping[str, Any],
    storyline: Mapping[str, Any],
    environment: Mapping[str, Any],
    canonical_sha256: Callable[[Any], str],
    sealed_value: Callable[[Mapping[str, Any]], Any] | None = None,
) -> None:
    # Preserve the fail-before-review proposition contract without delegating
    # graph ordering to historical validators (2.5 permits DAG-ordered ties).
    for event in plan["planned_event_registry"]:
        event_id = event.get("id")
        if not event["produces_proposition_ids"]:
            _fail(
                "T1_PLANNED_EVENT_PROPOSITION_OUTPUT_MISSING",
                f"{event_id}.produces_proposition_ids",
            )
        for field in (
            "requires_proposition_ids",
            "produces_proposition_ids",
            "discloses_proposition_ids",
        ):
            values = event[field]
            if len(values) != len(set(values)):
                _fail(
                    "T1_PLANNED_EVENT_PROPOSITION_REFERENCE_DUPLICATE",
                    f"{event_id}.{field}",
                )
    _v24.validate_p2_plan(
        plan, storyline, environment, canonical_sha256, sealed_value
    )
    validate_lifecycle_closure(plan, environment, storyline)


def validate_p3_exact(plan: Mapping[str, Any], model: Mapping[str, Any]) -> None:
    _v24.validate_p3_exact(plan, model)
    planned = _v24._v22._unique(
        plan["planned_event_registry"], "T1_PLANNED_EVENT_DUPLICATE"
    )
    events = _v24._v22._unique(model["major_events"], "T1_EVENT_DUPLICATE")
    for event_id, source in planned.items():
        target = events[event_id]
        for field in (
            "consumes_token_instance_ids",
            "lifecycle_effects",
        ):
            if source[field] != target[field]:
                _fail("T1_P3_EVENT_PROJECTION_MISMATCH", f"{event_id}.{field}")


def semantic_claim_records(
    plan: Mapping[str, Any], canonical_sha256: Callable[[Any], str]
) -> list[dict[str, str]]:
    records = list(_v24.semantic_claim_records(plan, canonical_sha256))
    values = [
        ("/lifecycle_scope", plan["lifecycle_scope"]),
        *(
            (f"/lifecycle_contract_registry/{index}", item)
            for index, item in enumerate(plan["lifecycle_contract_registry"])
        ),
    ]
    for pointer, item in values:
        records.append(
            {
                "claim_id": item["semantic_review_claim_id"],
                "claim_kind": "typed_lifecycle_causal_closure",
                "candidate_pointer": pointer,
                "candidate_value_sha256": canonical_sha256(item),
            }
        )
    identities = [item["claim_id"] for item in records]
    if len(identities) != len(set(identities)):
        _fail("T1_PLAN_REVIEW_CLAIM_DUPLICATE", "semantic claim universe")
    return sorted(records, key=lambda item: item["claim_id"])


def semantic_claim_universe(
    plan: Mapping[str, Any], canonical_sha256: Callable[[Any], str]
) -> list[str]:
    return [
        item["claim_id"]
        for item in semantic_claim_records(plan, canonical_sha256)
    ]


validate_p1_digests = _v24.validate_p1_digests
validate_information_projection = _v24.validate_information_projection
expected_e1_digests = _v24.expected_e1_digests


__all__ = [
    "Contract25Error",
    "LIFECYCLE_EDGE_KINDS",
    "LIFECYCLE_STATES",
    "expected_e1_digests",
    "semantic_claim_records",
    "semantic_claim_universe",
    "validate_explicit_token_consumption",
    "validate_information_projection",
    "validate_lifecycle_closure",
    "validate_p1_digests",
    "validate_p2_plan",
    "validate_p3_exact",
]
