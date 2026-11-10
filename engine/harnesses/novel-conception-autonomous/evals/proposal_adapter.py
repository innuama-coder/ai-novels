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
from typing import Any, Callable, Mapping
from pathlib import Path

runtime = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
storyline_quality = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_quality"
)
c1 = importlib.import_module(
    "skills.novel-character-system-designer.scripts.run_v2"
)
q1 = importlib.import_module(
    "skills.novel-conception-reviewer.scripts.run_v2"
)

ROLES = (
    ("background", "setup"),
    ("trigger",),
    ("development",),
    ("turn_or_crisis",),
    ("result", "aftermath"),
)
_WORLD_TIME_BASE = 100
_WORLD_TIME_MAX = 999999


class ProposalEvidenceError(ValueError):
    """The sealed upstream artifacts cannot support a required proposal fact."""


def _event_role_groups(transition_count: int) -> list[tuple[str, ...]]:
    """Assign the five ordered responsibility groups to state transitions."""

    if transition_count < 1:
        raise ProposalEvidenceError(
            "T1_PROPOSAL_STATE_TRANSITION_REQUIRED"
        )
    if transition_count >= len(ROLES):
        middle_count = transition_count - 3
        development_count = (middle_count + 1) // 2
        turn_count = middle_count - development_count
        return [
            ROLES[0],
            ROLES[1],
            *([ROLES[2]] * development_count),
            *([ROLES[3]] * turn_count),
            ROLES[4],
        ]
    assigned: list[tuple[str, ...]] = []
    for index in range(transition_count):
        start = index * len(ROLES) // transition_count
        end = (index + 1) * len(ROLES) // transition_count
        assigned.append(
            tuple(
                role
                for group in ROLES[start:end]
                for role in group
            )
        )
    return assigned


def _graph_derived_world_times(
    event_ids: list[str],
    causal_edges: list[Mapping[str, Any]],
) -> dict[str, str]:
    """Assign deterministic ticks from the complete causal DAG.

    Longest-path ranks preserve concurrency between independent roots while
    making every causal successor strictly later than all of its predecessors.
    """

    if len(event_ids) != len(set(event_ids)):
        raise ProposalEvidenceError(
            "T1_PROPOSAL_EVENT_ID_DUPLICATE: event IDs must be unique"
        )
    nodes = set(event_ids)
    incoming = {event_id: 0 for event_id in nodes}
    successors = {event_id: set() for event_id in nodes}
    edge_ids: set[str] = set()
    edge_pairs: set[tuple[str, str]] = set()
    for edge in causal_edges:
        left = str(edge.get("from_event_id", ""))
        right = str(edge.get("to_event_id", ""))
        edge_id = str(edge.get("id", f"{left}->{right}"))
        if edge_id in edge_ids:
            raise ProposalEvidenceError(
                f"T1_PROPOSAL_CAUSAL_EDGE_ID_DUPLICATE: {edge_id}"
            )
        edge_ids.add(edge_id)
        if left not in nodes or right not in nodes:
            raise ProposalEvidenceError(
                f"T1_PROPOSAL_CAUSAL_DANGLING: {edge_id}"
            )
        if left == right:
            raise ProposalEvidenceError(
                f"T1_PROPOSAL_CAUSAL_SELF_LOOP: {edge_id}"
            )
        pair = (left, right)
        if pair in edge_pairs:
            raise ProposalEvidenceError(
                "T1_PROPOSAL_CAUSAL_ENDPOINT_PAIR_DUPLICATE: "
                f"{left}->{right}"
            )
        edge_pairs.add(pair)
        successors[left].add(right)
        incoming[right] += 1

    ranks = {event_id: 0 for event_id in nodes}
    ready = sorted(
        event_id for event_id, count in incoming.items() if count == 0
    )
    visited = 0
    while ready:
        current = ready.pop(0)
        visited += 1
        for target in sorted(successors[current]):
            ranks[target] = max(ranks[target], ranks[current] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
                ready.sort()
    if visited != len(nodes):
        raise ProposalEvidenceError(
            "T1_PROPOSAL_CAUSAL_CYCLE: causal graph is not acyclic"
        )

    if ranks and _WORLD_TIME_BASE + max(ranks.values()) > _WORLD_TIME_MAX:
        raise ProposalEvidenceError(
            "T1_PROPOSAL_WORLD_TIME_OVERFLOW: six-digit ticks exhausted"
        )
    world_times = {
        event_id: f"[WT:{_WORLD_TIME_BASE + ranks[event_id]:06d}]"
        for event_id in sorted(nodes)
    }
    if any(
        world_times[left] >= world_times[right]
        for left, right in edge_pairs
    ):
        raise ProposalEvidenceError(
            "T1_PROPOSAL_CAUSAL_TIME_CONTRADICTION: "
            "graph-derived ticks are not strictly monotonic"
        )
    return world_times


def _select_information_evidence(
    timeline: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any], Mapping[str, Any] | None]:
    """Select evidence without inventing an unbound information transition."""

    changes = sorted(
        timeline.get("information_changes", []),
        key=lambda item: str(item["id"]),
    )
    if changes:
        return "explicit_information_change", changes[0], None

    events = {
        str(item["id"]): item for item in timeline.get("major_events", [])
    }
    for edge in sorted(
        timeline.get("causal_edges", []), key=lambda item: str(item["id"])
    ):
        event = events.get(str(edge.get("to_event_id")))
        if event is not None and event.get("participant_slot_ids"):
            return "causal_event_state", event, edge

    for event in sorted(
        events.values(),
        key=lambda item: (str(item.get("world_time", "")), str(item["id"])),
    ):
        before = event.get("before_state")
        after = event.get("after_state")
        if (
            event.get("participant_slot_ids")
            and isinstance(before, Mapping)
            and isinstance(after, Mapping)
            and before.keys() == after.keys()
            and any(before[key] != after[key] for key in before)
        ):
            return "event_state", event, None

    raise ProposalEvidenceError(
        "C1_PROPOSAL_INFORMATION_EVIDENCE_MISSING: sealed T1 has no explicit "
        "information change, causal event state, or observable event transition"
    )


_Q1_STAGE_CANONICAL = {
    "B0": "author-control-baseline.json",
    "S1": "storyline-architecture.json",
    "W1": "world-model.json",
    "E1": "environment-system.json",
    "T1": "event-timeline.json",
    "C1": "character-system.json",
}
_Q1_KIND_PREFIXES = {
    "S1": {"SLD-": "storyline-demand", "SLC-": "storyline-connection", "SL-": "storyline"},
    "W1": {"WR-": "world-requirement", "WF-": "world-fact", "WS-": "world-system"},
    "E1": {"END-": "environment-demand", "ENV-": "environment", "ZONE-": "environment-zone"},
    "T1": {"EVD-": "event-demand", "EV-": "event"},
    "C1": {
        "DEV-": "development-freedom",
        "CHD-": "character-demand",
        "SLOT-": "character-slot",
        "CHR-": "character",
        "REL-": "relationship",
    },
}


def _eval_object_kind(stage: str, identifier: str) -> str:
    if stage == "B0":
        return "author-control"
    for prefix, kind in _Q1_KIND_PREFIXES[stage].items():
        if identifier.startswith(prefix):
            return kind
    return "governance"


def _eval_index_objects(
    value: Any,
    *,
    stage: str,
    output: dict[tuple[str, str], dict[str, Any]],
) -> None:
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            key = (stage, identifier)
            if key in output:
                raise ProposalEvidenceError(
                    f"Q1_PROPOSAL_OBJECT_AMBIGUOUS: {stage}:{identifier}"
                )
            output[key] = {
                "id": identifier,
                "stage": stage,
                "kind": _eval_object_kind(stage, identifier),
                "value": copy.deepcopy(dict(value)),
                "value_sha256": runtime.canonical_sha256(value),
            }
        for child in value.values():
            _eval_index_objects(child, stage=stage, output=output)
    elif isinstance(value, list):
        for child in value:
            _eval_index_objects(child, stage=stage, output=output)


def _eval_story_object_index(
    frozen_inputs: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    roots = frozen_inputs.get("package_roots")
    if not isinstance(roots, Mapping):
        raise ProposalEvidenceError("Q1_PROPOSAL_PACKAGE_ROOTS_MISSING")
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for stage, canonical in _Q1_STAGE_CANONICAL.items():
        value = json.loads(
            (Path(roots[stage]) / canonical).read_text(encoding="utf-8")
        )
        _eval_index_objects(value, stage=stage, output=output)
    return output


def _definition_ids(value: Any, *, path: str = "$") -> list[tuple[str, str]]:
    """Return every explicit ``{"id": ...}`` definition and its JSON path."""

    found: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            found.append((identifier, path))
        for key, child in value.items():
            found.extend(
                _definition_ids(child, path=f"{path}.{key}")
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(
                _definition_ids(child, path=f"{path}[{index}]")
            )
    return found


class IdRegistry:
    """Fail-closed ID/authority preflight for fixture-authored proposals."""

    AUTHORITY_CLASSES = (
        "author_locked",
        "autonomous_owned",
        "downstream_freedom",
        "author_open",
    )

    def __init__(self, reserved_definition_ids: list[str]) -> None:
        self.reserved = set(reserved_definition_ids)
        if len(self.reserved) != len(reserved_definition_ids):
            raise ValueError(
                "ID_PREFLIGHT_RESERVED_DUPLICATE: "
                + runtime.canonical_json(reserved_definition_ids)
            )
        self.definitions_by_stage: dict[str, list[str]] = {}
        self.authority = {name: set() for name in self.AUTHORITY_CLASSES}

    def register(self, model: Mapping[str, Any]) -> None:
        stage = str(model.get("stage", "UNKNOWN"))
        definitions = _definition_ids(model)
        seen: dict[str, str] = {}
        duplicates: dict[str, list[str]] = {}
        for identifier, path in definitions:
            if identifier in seen:
                duplicates.setdefault(identifier, [seen[identifier]]).append(path)
            else:
                seen[identifier] = path
        reserved_collisions = sorted(set(seen) & self.reserved)
        authority = model.get("authority_partition")
        if not isinstance(authority, Mapping):
            raise ValueError(
                f"ID_PREFLIGHT_AUTHORITY_MISSING: {stage}"
            )
        local = {}
        for name in self.AUTHORITY_CLASSES:
            values = authority.get(name)
            if not isinstance(values, list) or any(
                not isinstance(value, str) for value in values
            ):
                raise ValueError(
                    f"ID_PREFLIGHT_AUTHORITY_INVALID: {stage}:{name}"
                )
            if len(values) != len(set(values)):
                raise ValueError(
                    f"ID_PREFLIGHT_AUTHORITY_DUPLICATE: {stage}:{name}"
                )
            local[name] = set(values)
        local_conflicts = {
            f"{left}/{right}": sorted(local[left] & local[right])
            for index, left in enumerate(self.AUTHORITY_CLASSES)
            for right in self.AUTHORITY_CLASSES[index + 1 :]
            if local[left] & local[right]
        }
        if duplicates or reserved_collisions or local_conflicts:
            evidence = {
                "stage": stage,
                "duplicate_definitions": duplicates,
                "generated_reserved_collisions": reserved_collisions,
                "authority_conflicts": local_conflicts,
            }
            raise ValueError(
                "ID_PREFLIGHT_COLLISION: "
                + runtime.canonical_json(evidence)
            )
        self.definitions_by_stage[stage] = sorted(seen)
        for name, values in local.items():
            self.authority[name].update(values)

    def evidence(self) -> dict[str, Any]:
        conflicts = {
            f"{left}/{right}": sorted(
                self.authority[left] & self.authority[right]
            )
            for index, left in enumerate(self.AUTHORITY_CLASSES)
            for right in self.AUTHORITY_CLASSES[index + 1 :]
            if self.authority[left] & self.authority[right]
        }
        if conflicts:
            raise ValueError(
                "ID_PREFLIGHT_GLOBAL_AUTHORITY_COLLISION: "
                + runtime.canonical_json(conflicts)
            )
        return {
            "status": "ready",
            "reserved_definition_ids": sorted(self.reserved),
            "definitions_by_stage": copy.deepcopy(self.definitions_by_stage),
            "authority_partition": {
                name: sorted(values)
                for name, values in self.authority.items()
            },
        }


def _eval_pointer_value(value: Any, pointer: str) -> Any:
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit():
            current = current[int(token)]
        else:
            raise ProposalEvidenceError(
                f"Q1_PROPOSAL_POINTER_INVALID: {pointer}"
            )
    return current


def _eval_paths(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    output: list[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            path = f"{prefix}/{token}"
            if key != "id":
                output.append((path, child))
            output.extend(_eval_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}/{index}"
            output.append((path, child))
            output.extend(_eval_paths(child, path))
    return output


def _eval_contains_id(value: Any, identifier: str) -> bool:
    if value == identifier:
        return True
    if isinstance(value, Mapping):
        return any(_eval_contains_id(child, identifier) for child in value.values())
    if isinstance(value, list):
        return any(_eval_contains_id(child, identifier) for child in value)
    return False


def _eval_exact_id_paths(
    value: Mapping[str, Any], identifier: str
) -> list[str]:
    """Return only fields that carry ``identifier`` as an exact ID value.

    Narrative strings that merely mention an identifier are intentionally not
    relations.  A relation must be represented by either a scalar ID field or
    a flat ID array in the frozen canonical object.
    """

    output = []
    for path, projected in _eval_paths(value):
        if projected == identifier:
            output.append(path)
        elif isinstance(projected, list) and identifier in projected:
            output.append(path)
    return output


def _eval_story_path(value: Mapping[str, Any]) -> str:
    for path, projected in _eval_paths(value):
        if isinstance(projected, str):
            normalized = " ".join(projected.split())
            if len(normalized) >= 12 and not normalized.startswith(
                ("CHK-", "HANDOFF-")
            ):
                return path
    raise ProposalEvidenceError("Q1_PROPOSAL_STORY_PROJECTION_MISSING")


def _eval_causal_story_path(value: Mapping[str, Any]) -> str:
    """Select only an explicit causal narrative field, never an ID field."""

    preferred_paths = (
        "/source_anchor/state",
        "/mechanism",
    )
    for path in preferred_paths:
        try:
            projected = _eval_pointer_value(value, path)
        except ProposalEvidenceError:
            continue
        if not isinstance(projected, str):
            continue
        normalized = " ".join(projected.split())
        if (
            len(normalized) >= 12
            and " " in normalized
            and not normalized.startswith(("CHK-", "HANDOFF-"))
        ):
            return path
    raise ProposalEvidenceError(
        "Q1_PROPOSAL_CAUSAL_STORY_PROJECTION_MISSING"
    )


def _eval_typed_story_path(
    value: Mapping[str, Any],
    *,
    paths: tuple[str, ...],
    error_code: str,
) -> str:
    for path in paths:
        try:
            projected = _eval_pointer_value(value, path)
        except ProposalEvidenceError:
            continue
        if not isinstance(projected, str):
            continue
        normalized = " ".join(projected.split())
        if (
            len(normalized) >= 12
            and " " in normalized
            and not normalized.startswith(("CHK-", "HANDOFF-"))
        ):
            return path
    raise ProposalEvidenceError(error_code)


def _eval_t1_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/mechanism", "/necessary_condition"),
        error_code="Q1_PROPOSAL_T1_STORY_PROJECTION_MISSING",
    )


def _eval_c1_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/chosen_action", "/cost"),
        error_code="Q1_PROPOSAL_C1_STORY_PROJECTION_MISSING",
    )


def _eval_coverage_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/evidence", "/responsibility"),
        error_code="Q1_PROPOSAL_COVERAGE_STORY_PROJECTION_MISSING",
    )


def _eval_easy_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/selection", "/statement"),
        error_code="Q1_PROPOSAL_EASY_STORY_PROJECTION_MISSING",
    )


def _eval_consistency_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/to_state", "/responsibility", "/statement"),
        error_code="Q1_PROPOSAL_CONSISTENCY_STORY_PROJECTION_MISSING",
    )


def _eval_handoff_event_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=(
            "/from_state",
            "/to_state",
            "/consequence",
            "/responsibility",
        ),
        error_code="Q1_PROPOSAL_HANDOFF_EVENT_STORY_PROJECTION_MISSING",
    )


def _eval_handoff_choice_story_path(value: Mapping[str, Any]) -> str:
    return _eval_typed_story_path(
        value,
        paths=("/chosen_action", "/cost", "/responsibility"),
        error_code="Q1_PROPOSAL_HANDOFF_CHOICE_STORY_PROJECTION_MISSING",
    )


def _eval_cross_story_path(value: Mapping[str, Any]) -> str:
    """Select the explicit cross-stage narrative, never its ID ledgers."""

    for path in ("/evidence", "/responsibility"):
        try:
            projected = _eval_pointer_value(value, path)
        except ProposalEvidenceError:
            continue
        if not isinstance(projected, str):
            continue
        normalized = " ".join(projected.split())
        if (
            len(normalized) >= 12
            and " " in normalized
            and not normalized.startswith(("CHK-", "HANDOFF-"))
        ):
            return path
    raise ProposalEvidenceError(
        "Q1_PROPOSAL_CROSS_STORY_PROJECTION_MISSING"
    )


def _eval_allowed_relation_path(
    value: Mapping[str, Any],
    identifier: str,
    *,
    paths: tuple[str, ...],
) -> str | None:
    for path in paths:
        try:
            projected = _eval_pointer_value(value, path)
        except ProposalEvidenceError:
            continue
        if _eval_contains_id(projected, identifier):
            return path
    return None


def _storyline_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    controls: list[dict[str, object]],
) -> dict[str, object]:
    """A test Agent's authored proposal; production code never synthesizes it."""

    demands = []
    storylines = []
    decisions = []
    coverage = []
    line_by_control = {}
    for index, control in enumerate(controls, 1):
        control_id = str(control["id"])
        value = (
            control["value"]
            if isinstance(control["value"], str)
            else runtime.canonical_json(control["value"])
        )
        line_id = "SL-MAIN" if index == 1 else f"SL-{index:03d}"
        demand_id = f"SLD-{index:03d}"
        decision_id = f"DEC-{index:03d}"
        line_by_control[control_id] = line_id
        demands.append(
            {
                "id": demand_id,
                "source_ids": [control_id],
                "obligation": (
                    f"Agent interpretation of {control['heading']}. "
                    f"Source meaning (verbatim): {value}"
                ),
                "disposition": "merged" if index == 1 else "independent_line",
            }
        )
        decisions.append(
            {
                "id": decision_id,
                "gap": f"Choose dramatic ownership for {control_id}.",
                "options": ["Merge into main line.", "Create a connected line."],
                "selection": (
                    "Merge into main line."
                    if index == 1
                    else "Create a connected line."
                ),
                "owner": "S1",
                "authority_basis": f"S1 owns storyline projection of {control_id}.",
                "compatibility": f"Preserves the source meaning: {value}",
                "impact_ids": [line_id],
                "cost": "Creates one explicit dramatic responsibility.",
                "reversibility": "costly",
                "downstream_freedom": "Concrete realization remains downstream.",
                "projection_ids": [line_id],
            }
        )
        storylines.append(
            {
                "id": line_id,
                "type": "main" if index == 1 else "supporting",
                "responsibility": f"Carry {control_id}: {value}",
                "actor_slot_ids": [f"SLOT-{index:03d}"],
                "goal": f"Make this meaning actionable without changing it: {value}",
                "pressure": f"Ignoring this meaning leaves the story incomplete: {value}",
                "start_state": f"The obligation is latent: {value}",
                "state_changes": [
                    f"Pressure exposes the obligation: {value}",
                    f"A choice changes its consequences: {value}",
                ],
                "end_state": f"The obligation has a visible consequence: {value}",
                "connection_ids": [],
                "source_decision_ids": [decision_id],
                "downstream_freedom": "World, place, event, actor identity and prose are open.",
            }
        )
        coverage.append(
            {
                "id": f"COV-{index:03d}",
                "source_ids": [demand_id],
                "realization_ids": [line_id],
                "status": "covered",
                "evidence": f"{demand_id} is assigned once to {line_id}.",
            }
        )
    main = storylines[0]
    connections = []
    for index, line in enumerate(storylines[1:], 1):
        connection_id = f"SLC-{index:03d}"
        connections.append(
            {
                "id": connection_id,
                "type": "collision",
                "relation": "causal",
                "from_storyline_id": line["id"],
                "to_storyline_id": "SL-MAIN",
                "from_state": line["end_state"],
                "from_state_index": len(line["state_changes"]) + 1,
                "to_state": main["state_changes"][-1],
                "to_state_index": len(main["state_changes"]),
            }
        )
        line["connection_ids"].append(connection_id)
        main["connection_ids"].append(connection_id)
    demand_by_line = {
        line_by_control[str(control["id"])]: f"SLD-{index:03d}"
        for index, control in enumerate(controls, 1)
    }
    requirements = {}
    for field, prefix, stage in (
        ("world_requirements", "WR", "W1"),
        ("environment_requirements", "END", "E1"),
        ("event_requirements", "EVD", "T1"),
        ("character_requirements", "CHD", "C1"),
    ):
        requirements[field] = []
        for index, line in enumerate(storylines, 1):
            requirements[field].append(
                {
                    "id": f"{prefix}-{index:03d}",
                    "target_stage": stage,
                    "responsibility": f"Realize {line['responsibility']}",
                    "source_ids": [line["id"], demand_by_line[line["id"]]],
                    "required_capability": (
                        f"Support {line['start_state']} through {line['end_state']}"
                    ),
                    "constraints": [line["goal"], line["pressure"]],
                    "acceptance_checks": [
                        f"The result cites {line['id']}.",
                        f"The result preserves {line['end_state']}.",
                    ],
                    "downstream_freedom": line["downstream_freedom"],
                }
            )
    architecture = {
        "subject": "All approved obligations form one connected causal whole.",
        "opening_condition": main["start_state"],
        "development_logic": "Each line changes state before joining the main trunk.",
        "turning_logic": "Every connection changes the pressure on the main trunk.",
        "resolution_condition": main["end_state"],
        "theme_test": "The ending answers locked controls and preserves open controls.",
        "line_order": [
            *[line["id"] for line in storylines[1:]],
            main["id"],
        ],
    }
    model = {
        "schema_version": "2.0",
        "skill": "novel-storyline-architecture-designer",
        "stage": "S1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": [
                str(item["id"])
                for item in controls
                if item["hardness"] == "author_locked"
            ],
            "autonomous_owned": [
                *[item["id"] for item in decisions],
                *[item["id"] for item in storylines],
            ],
            "downstream_freedom": [
                item["id"] for values in requirements.values() for item in values
            ],
            "author_open": [
                str(item["id"])
                for item in controls
                if item["hardness"] == "author_open"
            ],
        },
        "design_decisions": decisions,
        "derivation_claims": [
            {
                "id": f"DRV-{index:03d}",
                "value_sha256": runtime.canonical_sha256(line),
                "source_ids": [str(controls[index - 1]["id"])],
                "decision_ids": [f"DEC-{index:03d}"],
                "projection_ids": [line["id"]],
            }
            for index, line in enumerate(storylines, 1)
        ]
        + [
            {
                "id": "DRV-ARCHITECTURE",
                "value_sha256": runtime.canonical_sha256(architecture),
                "source_ids": [str(item["id"]) for item in controls],
                "decision_ids": [item["id"] for item in decisions],
                "projection_ids": [item["id"] for item in storylines],
            }
        ],
        "storyline_demands": demands,
        "storylines": storylines,
        "connections": connections,
        "architecture": architecture,
        "cross_line_consistency": [
            {
                "id": f"SLCHECK-{dimension.upper()}",
                "dimension": dimension,
                "witness_ids": [line["id"] for line in storylines],
                "claim": (
                    f"Every storyline has a declared {dimension} relation "
                    "that remains consistent with the complete architecture."
                ),
                "failure_condition": (
                    f"The {dimension} relation fails if any declared "
                    "storyline contradicts another line or the architecture."
                ),
            }
            for dimension in (
                "time",
                "causality",
                "information",
                "authority",
                "state",
                "theme",
            )
        ],
        **requirements,
        "coverage_ledger": coverage,
        "open_items": [
            {
                "id": f"OPEN-{index:03d}",
                "question": (
                    f"Preserve {control['heading']}: "
                    f"{control['value']}"
                ),
                "source_ids": [str(control["id"])],
                "status": "author_open",
            }
            for index, control in enumerate(
                [item for item in controls if item["hardness"] == "author_open"],
                1,
            )
        ],
    }
    return model


def _stable_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _formal_storyline_proposal(
    validated_case: Any,
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    controls: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    """Project one admitted eval plan into the closed production S1 dialect."""

    structural = validated_case.structural_case
    fixture = structural.fixture
    plan = structural.plan
    if run_id != fixture["run_id"]:
        raise ProposalEvidenceError(
            "S1_EVAL_RUN_ID_MISMATCH: live run differs from the admitted case"
        )
    expected_controls = {
        str(item["control_id"]): item for item in fixture["interviews"]
    }
    live_controls = {str(item["id"]): item for item in controls}
    if set(live_controls) != set(expected_controls):
        raise ProposalEvidenceError(
            "S1_EVAL_LIVE_CONTROL_SET_MISMATCH"
        )
    for control_id, expected in expected_controls.items():
        live = live_controls[control_id]
        expected_heading = (
            f"[{control_id}][{expected['hardness']}] "
            f"{expected['heading']}"
        )
        for field, expected_value in (
            ("hardness", expected["hardness"]),
            ("heading", expected_heading),
            ("domain", expected["stage"]),
        ):
            if live.get(field) != expected_value:
                raise ProposalEvidenceError(
                    f"S1_EVAL_LIVE_CONTROL_MISMATCH: {control_id}.{field}"
                )
        if runtime.canonical_sha256(live.get("value")) != runtime.canonical_sha256(
            expected.get("value")
        ):
            raise ProposalEvidenceError(
                f"S1_EVAL_LIVE_CONTROL_MISMATCH: {control_id}.value"
            )

    def live_control_binding(control_id: str) -> str:
        live = live_controls[control_id]
        value = (
            live["value"]
            if isinstance(live["value"], str)
            else runtime.canonical_json(live["value"])
        )
        return (
            f"{live['heading']}. Source meaning (verbatim): {value}"
        )

    demands = []
    for item in plan["demands"]:
        binding = live_control_binding(item["source_control_id"])
        obligation = item["obligation"]
        if binding not in obligation:
            obligation = f"{obligation} Live B0 control: {binding}"
        demands.append(
            {
                "id": item["id"],
                "source_ids": [item["source_control_id"]],
                "obligation": obligation,
                "disposition": item["disposition"],
            }
        )
    demand_by_id = {
        item["id"]: item for item in plan["demands"]
    }
    state_index: dict[str, tuple[str, int, str]] = {}
    lines: list[dict[str, object]] = []
    for item in plan["lines"]:
        states = item["states"]
        for index, state in enumerate(states):
            if state["id"] in state_index:
                raise ProposalEvidenceError(
                    f"S1_EVAL_STATE_ID_DUPLICATE: {state['id']}"
                )
            state_index[state["id"]] = (
                item["id"],
                index,
                state["description"],
            )
        line_bindings = [
            live_control_binding(
                demand_by_id[demand_id]["source_control_id"]
            )
            for demand_id in item["demand_ids"]
        ]
        responsibility = item["responsibility"]
        for binding in line_bindings:
            if binding not in responsibility:
                responsibility += f" Bound source: {binding}"
        lines.append(
            {
                "id": item["id"],
                "type": item["type"],
                "responsibility": responsibility,
                "actor_slot_ids": copy.deepcopy(item["actor_slot_ids"]),
                "goal": item["goal"],
                "pressure": item["pressure"],
                "start_state": states[0]["description"],
                "state_changes": [
                    state["description"] for state in states[1:-1]
                ],
                "end_state": states[-1]["description"],
                "connection_ids": copy.deepcopy(item["connection_ids"]),
                "source_decision_ids": copy.deepcopy(item["decision_ids"]),
                "downstream_freedom": item["downstream_freedom"],
            }
        )
    line_by_id = {item["id"]: item for item in lines}
    plan_line_by_id = {item["id"]: item for item in plan["lines"]}
    connections: list[dict[str, object]] = []
    for item in plan["connections"]:
        source = state_index.get(item["from_state_id"])
        target = state_index.get(item["to_state_id"])
        if (
            source is None
            or target is None
            or source[0] != item["from_line_id"]
            or target[0] != item["to_line_id"]
        ):
            raise ProposalEvidenceError(
                f"S1_EVAL_CONNECTION_STATE_INVALID: {item['id']}"
            )
        connections.append(
            {
                "id": item["id"],
                "type": item["type"],
                "relation": item["relation"],
                "from_storyline_id": item["from_line_id"],
                "to_storyline_id": item["to_line_id"],
                "from_state": source[2],
                "from_state_index": source[1],
                "to_state": target[2],
                "to_state_index": target[1],
            }
        )
    connection_by_id = {
        item["id"]: item for item in connections
    }
    architecture = {
        field: copy.deepcopy(plan["architecture"][field])
        for field in (
            "subject",
            "opening_condition",
            "development_logic",
            "turning_logic",
            "resolution_condition",
            "theme_test",
            "line_order",
        )
    }

    anchors = {
        item["anchor_id"]: item
        for item in fixture["semantic_assertions"]
    }
    decisions: list[dict[str, object]] = []
    decision_source_controls: dict[str, list[str]] = {}
    for item in plan["design_decisions"]:
        sources = list(item["source_control_ids"])
        for anchor_id in item["source_anchor_ids"]:
            sources.extend(anchors[anchor_id]["required_source_ids"])
        sources = sorted(set(sources))
        decision_source_controls[item["id"]] = sources
        downstream = _stable_unique(
            [
                plan_line_by_id[target_id]["downstream_freedom"]
                for target_id in item["projection_ids"]
                if target_id in plan_line_by_id
            ]
        )
        decision = {
            "id": item["id"],
            "gap": item["gap"],
            "options": copy.deepcopy(item["options"]),
            "selection": item["selection"],
            "owner": "S1",
            "authority_basis": item["authority_basis"],
            "compatibility": (
                "Validated plan sources: " + ", ".join(sources)
            ),
            "impact_ids": copy.deepcopy(item["projection_ids"]),
            "cost": (
                "Plan-declared reversibility: " + item["reversibility"]
            ),
            "reversibility": item["reversibility"],
            "downstream_freedom": (
                " ".join(downstream)
                or "No downstream story fact is selected by this decision."
            ),
            "projection_ids": copy.deepcopy(item["projection_ids"]),
        }
        if len(item["options"]) == 1:
            decision["single_option_exclusion_evidence"] = (
                "The admitted plan records one reviewed option."
            )
        decisions.append(decision)
    decision_by_id = {item["id"]: item for item in decisions}

    open_control_ids = {
        control_id
        for control_id, item in expected_controls.items()
        if item["hardness"] == "author_open"
    }
    for decision_id, sources in decision_source_controls.items():
        if open_control_ids & set(sources):
            raise ProposalEvidenceError(
                f"S1_EVAL_OPEN_DECISION_FORBIDDEN: {decision_id}"
            )

    realization_by_demand = {
        item["id"]: list(item["realization_line_ids"])
        for item in plan["demands"]
    }
    target_objects: dict[str, tuple[str, Any]] = {}
    for item in plan["lines"]:
        target_objects[item["id"]] = ("line", item)
        for state in item["states"]:
            target_objects[state["id"]] = ("state", state)
    for field, kind in (
        ("demands", "demand"),
        ("connections", "connection"),
        ("design_decisions", "decision"),
        ("anchor_bindings", "anchor"),
        ("open_control_treatments", "open"),
    ):
        for item in plan[field]:
            target_objects[item["id"]] = (kind, item)
    target_objects[plan["architecture"]["id"]] = (
        "architecture",
        plan["architecture"],
    )

    production_allowed = {
        "time": {"line", "connection"},
        "causality": {"line", "connection"},
        "information": {"line", "connection", "demand"},
        "authority": {"line", "decision", "demand"},
        "state": {"line", "connection"},
        "theme": {"line", "connection", "demand", "decision"},
    }

    def map_witness(
        witness_id: str,
        dimension: str,
        seen: frozenset[str] = frozenset(),
    ) -> list[str]:
        if witness_id in seen:
            return []
        found = target_objects.get(witness_id)
        if found is None:
            raise ProposalEvidenceError(
                f"S1_EVAL_WITNESS_UNKNOWN: {witness_id}"
            )
        kind, item = found
        if kind == "line":
            return [witness_id]
        if kind == "state":
            return [state_index[witness_id][0]]
        if kind == "connection":
            if (
                dimension != "causality"
                and "connection" in production_allowed[dimension]
            ) or (
                dimension == "causality"
                and item["relation"] == "causal"
            ):
                return [witness_id]
            return _stable_unique(
                [
                    item["from_line_id"],
                    item["to_line_id"],
                ]
            )
        if kind == "demand":
            if "demand" in production_allowed[dimension]:
                return [witness_id]
            return realization_by_demand[witness_id]
        if kind == "decision":
            if "decision" in production_allowed[dimension]:
                return [witness_id]
            nested: list[str] = []
            for target_id in item["projection_ids"]:
                nested.extend(
                    map_witness(
                        target_id,
                        dimension,
                        seen | {witness_id},
                    )
                )
            return _stable_unique(nested)
        if kind == "architecture":
            return list(architecture["line_order"])
        if kind in {"anchor", "open"}:
            nested = []
            for target_id in item["target_ids"]:
                nested.extend(
                    map_witness(
                        target_id,
                        dimension,
                        seen | {witness_id},
                    )
                )
            return _stable_unique(nested)
        raise ProposalEvidenceError(
            f"S1_EVAL_WITNESS_UNPROJECTABLE: {witness_id}"
        )

    consistency: list[dict[str, object]] = []
    consistency_projection: dict[str, dict[str, list[str]]] = {}
    all_line_ids = list(architecture["line_order"])

    def projected_kind(identifier: str) -> str | None:
        matches = [
            kind
            for kind, registry in (
                ("line", line_by_id),
                ("connection", connection_by_id),
                ("demand", demand_by_id),
                ("decision", decision_by_id),
            )
            if identifier in registry
        ]
        if len(matches) > 1:
            raise ProposalEvidenceError(
                f"S1_EVAL_PROJECTED_ID_AMBIGUOUS: {identifier}"
            )
        return matches[0] if matches else None

    for item in plan["consistency_evidence"]:
        mapped: list[str] = []
        source_mapping: dict[str, list[str]] = {}
        for witness_id in item["witness_ids"]:
            projected = map_witness(witness_id, item["dimension"])
            if not projected:
                raise ProposalEvidenceError(
                    f"S1_EVAL_WITNESS_UNPROJECTABLE: {witness_id}"
                )
            source_mapping[witness_id] = projected
            mapped.extend(projected)
        mapped = _stable_unique([*all_line_ids, *mapped])
        invalid = [
            identifier
            for identifier in mapped
            if projected_kind(identifier)
            not in production_allowed[item["dimension"]]
        ]
        if invalid:
            raise ProposalEvidenceError(
                "S1_EVAL_WITNESS_PROJECTION_INVALID: "
                + ",".join(invalid)
            )
        if item["dimension"] == "causality":
            associative = [
                identifier
                for identifier in mapped
                if identifier in connection_by_id
                and connection_by_id[identifier]["relation"]
                == "associative"
            ]
            if associative:
                raise ProposalEvidenceError(
                    "S1_EVAL_ASSOCIATIVE_CAUSAL_WITNESS: "
                    + ",".join(associative)
                )
        consistency_projection[item["id"]] = source_mapping
        consistency.append(
            {
                "id": item["id"],
                "dimension": item["dimension"],
                "witness_ids": mapped,
                "claim": item["claim"],
                "failure_condition": item["failure_condition"],
            }
        )

    requirements: dict[str, list[dict[str, object]]] = {}
    for stage, field in (
        ("W1", "world_requirements"),
        ("E1", "environment_requirements"),
        ("T1", "event_requirements"),
        ("C1", "character_requirements"),
    ):
        requirements[field] = [
            {
                "id": item["id"],
                "target_stage": item["target_stage"],
                "responsibility": item["responsibility"],
                "source_ids": [
                    item["line_id"],
                    *item["demand_ids"],
                ],
                "required_capability": item["required_capability"],
                "constraints": _stable_unique(
                    [
                        *copy.deepcopy(item["constraints"]),
                        *[
                            "Preserve live B0 control: "
                            + live_control_binding(
                                demand_by_id[demand_id][
                                    "source_control_id"
                                ]
                            )
                            for demand_id in item["demand_ids"]
                        ],
                    ]
                ),
                "acceptance_checks": copy.deepcopy(
                    item["acceptance_checks"]
                ),
                "downstream_freedom": item["downstream_freedom"],
            }
            for item in plan["downstream_requirements"][stage]
        ]

    occupied_ids = {
        str(item["control_id"]) for item in fixture["interviews"]
    } | {
        str(item["anchor_id"])
        for item in fixture["semantic_assertions"]
    } | set(target_objects)
    coverage: list[dict[str, object]] = []
    coverage_ids: set[str] = set()
    for item in plan["demands"]:
        coverage_id = "COV-S1-" + item["id"].removeprefix("SLD-")
        if coverage_id in occupied_ids or coverage_id in coverage_ids:
            raise ProposalEvidenceError(
                f"S1_EVAL_DERIVED_ID_COLLISION: {coverage_id}"
            )
        coverage_ids.add(coverage_id)
        coverage.append(
            {
                "id": coverage_id,
                "source_ids": [item["id"]],
                "realization_ids": copy.deepcopy(
                    item["realization_line_ids"]
                ),
                "status": "covered",
                "evidence": (
                    f"{item['id']} is realized by "
                    + ",".join(item["realization_line_ids"])
                    + "."
                ),
            }
        )

    demand_ids_by_line = {
        line_id: [
            item["id"]
            for item in plan["demands"]
            if line_id in item["realization_line_ids"]
        ]
        for line_id in line_by_id
    }
    derivations: list[dict[str, object]] = []
    derivation_ids: set[str] = set()
    for line in lines:
        line_id = str(line["id"])
        source_ids = {
            demand_by_id[demand_id]["source_control_id"]
            for demand_id in demand_ids_by_line[line_id]
        }
        line_decisions = list(line["source_decision_ids"])
        for decision_id in line_decisions:
            source_ids.update(decision_source_controls[decision_id])
        if source_ids & open_control_ids and line_decisions:
            raise ProposalEvidenceError(
                f"S1_EVAL_OPEN_LINE_DECISION_FORBIDDEN: {line_id}"
            )
        derivation_id = "DRV-S1-" + line_id.removeprefix("SL-")
        if (
            derivation_id in occupied_ids
            or derivation_id in coverage_ids
            or derivation_id in derivation_ids
        ):
            raise ProposalEvidenceError(
                f"S1_EVAL_DERIVED_ID_COLLISION: {derivation_id}"
            )
        derivation_ids.add(derivation_id)
        derivations.append(
            {
                "id": derivation_id,
                "value_sha256": runtime.canonical_sha256(line),
                "source_ids": sorted(source_ids),
                "decision_ids": line_decisions,
                "projection_ids": [line_id],
            }
        )
    if (
        "DRV-ARCHITECTURE" in occupied_ids
        or "DRV-ARCHITECTURE" in coverage_ids
        or "DRV-ARCHITECTURE" in derivation_ids
    ):
        raise ProposalEvidenceError(
            "S1_EVAL_DERIVED_ID_COLLISION: DRV-ARCHITECTURE"
        )
    derivations.append(
        {
            "id": "DRV-ARCHITECTURE",
            "value_sha256": runtime.canonical_sha256(architecture),
            "source_ids": sorted(
                set(expected_controls) - open_control_ids
            ),
            "decision_ids": [item["id"] for item in decisions],
            "projection_ids": copy.deepcopy(architecture["line_order"]),
        }
    )
    downstream_ids = [
        item["id"]
        for field in requirements.values()
        for item in field
    ]
    model = {
        "schema_version": "2.0",
        "skill": "novel-storyline-architecture-designer",
        "stage": "S1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": sorted(
                control_id
                for control_id, item in live_controls.items()
                if item["hardness"] == "author_locked"
            ),
            "autonomous_owned": [
                *[item["id"] for item in decisions],
                *[item["id"] for item in lines],
            ],
            "downstream_freedom": downstream_ids,
            "author_open": sorted(open_control_ids),
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "storyline_demands": demands,
        "storylines": lines,
        "connections": connections,
        "architecture": architecture,
        "cross_line_consistency": consistency,
        **requirements,
        "coverage_ledger": coverage,
        "open_items": [
            {
                "id": item["id"],
                "question": item["question"],
                "source_ids": [item["source_control_id"]],
                "status": "author_open",
            }
            for item in plan["open_control_treatments"]
        ],
    }
    evidence = {
        "schema_version": "1.0",
        "status": "ready",
        "manifest_id": structural.manifest["manifest_id"],
        "fixture_id": fixture["fixture_id"],
        "plan_id": plan["plan_id"],
        "quality_gate_id": validated_case.gate["gate_id"],
        "structural_validation_sha256": runtime.canonical_sha256(
            structural.validation
        ),
        "quality_validation_sha256": runtime.canonical_sha256(
            validated_case.validation
        ),
        "model_sha256": runtime.canonical_sha256(model),
        "state_projection": {
            state_id: {
                "line_id": owner,
                "index": index,
                "description_sha256": runtime.canonical_sha256(
                    description
                ),
            }
            for state_id, (owner, index, description) in sorted(
                state_index.items()
            )
        },
        "consistency_projection": consistency_projection,
    }
    return model, evidence

def _world_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    baseline: dict[str, object],
    storyline: dict[str, object],
) -> dict[str, object]:
    """A test Agent's authored world model; production never synthesizes it."""

    requirements = copy.deepcopy(storyline["world_requirements"])
    lines = {item["id"]: item for item in storyline["storylines"]}
    decisions = []
    facts = []
    history = []
    institutions = []
    systems = []
    resource_flows = []
    authority_flows = []
    information_flows = []
    conflicts = []
    support = []
    environment_demands = []
    derivations = []
    owned_ids = []
    all_markers = " | ".join(item["responsibility"] for item in requirements)

    for index, requirement in enumerate(requirements, 1):
        line_id = next(item for item in requirement["source_ids"] if item in lines)
        line = lines[line_id]
        marker = requirement["responsibility"]
        decision_id = f"DEC-W1-{index:03d}"
        fact_id = f"WF-RULE-{index:03d}"
        history_id = f"HIS-{index:03d}"
        institution_id = f"INST-{index:03d}"
        system_id = f"WS-{index:03d}"
        resource_id = f"RF-{index:03d}"
        authority_id = f"AF-{index:03d}"
        information_id = f"IF-{index:03d}"
        conflict_id = f"WRC-{index:03d}"
        support_id = f"COV-W1-{index:03d}"
        environment_id = f"END-W1-{index:03d}"

        decisions.append(
            {
                "id": decision_id,
                "gap": f"Choose world pressure for {requirement['id']}: {marker}",
                "options": [
                    f"Use a costly regulated system for {marker}.",
                    f"Use an unrestricted system for {marker}.",
                ],
                "selection": f"Use a costly regulated system for {marker}.",
                "owner": "W1",
                "authority_basis": f"W1 owns world realization of {requirement['id']}.",
                "compatibility": f"Preserves the S1 responsibility: {marker}",
                "impact_ids": [fact_id, system_id],
                "cost": f"The rule makes {marker} possible but never free.",
                "reversibility": "costly",
                "downstream_freedom": "E1 may choose concrete places within the rule.",
                "projection_ids": [fact_id, system_id],
            }
        )
        fact = {
            "id": fact_id,
            "kind": "rule",
            "statement": f"The world permits and pressures this obligation: {marker}",
            "applies_to_ids": [line_id],
            "constraints": [
                f"Scope: applies wherever {marker} must be realized.",
                f"Exception: no actor may bypass the rule merely to achieve {marker}.",
                f"Cost: using the capability consumes scarce capacity for {marker}.",
                f"Constraint: authority must be verified before pursuing {marker}.",
            ],
            "consequences": [
                f"Success leaves an observable cost while supporting {marker}.",
                f"Failure blocks or worsens {marker}.",
            ],
            "source_ids": [requirement["id"], decision_id],
        }
        facts.append(fact)
        history.append(
            {
                "id": history_id,
                "origin": f"Earlier misuse created regulation around {marker}.",
                "current_pressure": f"Institutions now ration access needed for {marker}.",
                "storyline_ids": [line_id],
                "constraints": [f"Past damage cannot be erased to simplify {marker}."],
            }
        )
        institutions.append(
            {
                "id": institution_id,
                "responsibility": f"Govern the capability required by {marker}.",
                "authority": [f"Authorize bounded access for {marker}."],
                "resources": [f"Maintain scarce capacity used by {marker}."],
                "constraints": [f"Must record every authorization affecting {marker}."],
                "failure_modes": [f"Delay or capture can prevent {marker}."],
                "storyline_ids": [line_id],
            }
        )
        system = {
            "id": system_id,
            "input_conditions": [
                f"A verified request exists for {marker}.",
                f"The originating storyline is in state: {line['start_state']}",
            ],
            "actor_slot_ids": copy.deepcopy(line["actor_slot_ids"]),
            "resources": [f"Scarce capacity allocated to {marker}."],
            "authorities": [f"Recorded permission governing {marker}."],
            "transformation_rules": [
                f"Scope: transform only verified inputs related to {marker}.",
                f"Exception: refuse inputs that would bypass the conflict in {marker}.",
            ],
            "observable_outputs": [f"An auditable output advances or blocks {marker}."],
            "costs": [f"Capacity and trust are spent whenever {marker} proceeds."],
            "limits": [f"No operation may remove the core pressure in {marker}."],
            "failure_modes": [f"Denial, delay, or corrupted input can defeat {marker}."],
            "state_changes": [
                f"The world moves from latent capacity to accountable consequence for {marker}."
            ],
            "storyline_ids": [line_id],
        }
        systems.append(system)
        resource_flows.append(
            {
                "id": resource_id,
                "from_id": system_id,
                "to_id": institution_id,
                "relation": f"accounts for capacity used by {marker}",
                "mechanism": f"usage ledger for {marker}",
                "constraints": [f"No unrecorded resource transfer for {marker}."],
            }
        )
        authority_flows.append(
            {
                "id": authority_id,
                "from_id": institution_id,
                "to_id": system_id,
                "relation": f"grants bounded permission for {marker}",
                "mechanism": f"revocable authorization for {marker}",
                "constraints": [f"Permission cannot erase the cost of {marker}."],
            }
        )
        information_flows.append(
            {
                "id": information_id,
                "from_id": system_id,
                "to_id": institution_id,
                "relation": f"reports observable consequences of {marker}",
                "mechanism": f"auditable report for {marker}",
                "constraints": [f"Visibility remains bounded while preserving {marker}."],
            }
        )
        conflicts.append(
            {
                "id": conflict_id,
                "rule_ids": [fact_id, system_id],
                "tension": f"Capability and restriction pull against each other in {marker}.",
                "resolution_rule": f"Cost and authorization remain active whichever side wins {marker}.",
                "storyline_ids": [line_id],
            }
        )
        realization_ids = [fact_id, system_id, history_id, institution_id]
        support.append(
            {
                "id": support_id,
                "source_ids": [requirement["id"]],
                "realization_ids": realization_ids,
                "status": "covered",
                "evidence": f"{marker} is carried by a rule, system, history pressure, and institution.",
            }
        )
        environment_demands.append(
            {
                "id": environment_id,
                "target_stage": "E1",
                "responsibility": f"Provide concrete carrying conditions for {marker}.",
                "source_ids": [requirement["id"], *realization_ids],
                "required_capability": f"Expose access, cost, limits, and failure for {marker}.",
                "constraints": [
                    f"Do not bypass {fact_id} while carrying {marker}.",
                    f"Make {system_id} inputs and outputs observable for {marker}.",
                ],
                "acceptance_checks": [
                    f"A concrete environment can carry success and failure for {marker}.",
                    f"The environment cites the exact W1 support set for {marker}.",
                ],
                "downstream_freedom": "E1 chooses topology and functional zones.",
            }
        )
        derivations.extend(
            [
                {
                    "id": f"DRV-W1-RULE-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(fact),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [fact_id],
                },
                {
                    "id": f"DRV-W1-SYSTEM-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(system),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [system_id],
                },
            ]
        )
        owned_ids.extend(
            [
                decision_id,
                fact_id,
                history_id,
                institution_id,
                system_id,
                resource_id,
                authority_id,
                information_id,
                conflict_id,
                support_id,
            ]
        )

    reality_claims = []
    for index, dependency in enumerate(baseline["fact_dependencies"], 1):
        handling = {
            "adopted": "adopted",
            "open": "preserve_open",
            "not_applicable": "fiction_boundary",
        }[dependency["status"]]
        details = dependency["claim"]
        if dependency["status"] == "adopted":
            details += (
                f" Allowed use: {dependency['allowed_use']}."
                f" Fiction boundary: {dependency['fiction_boundary']}."
            )
        claim_id = f"WF-REALITY-{index:03d}"
        reality_claims.append(
            {
                "id": claim_id,
                "fact_dependency_id": dependency["id"],
                "handling": handling,
                "claim": details,
            }
        )
        owned_ids.append(claim_id)

    facets = {
        name: [f"{name} domain constrains the complete requirement set: {all_markers}"]
        for name in (
            "physical",
            "technology",
            "social",
            "political",
            "economic",
            "legal_and_ethical",
            "information",
            "historical",
        )
    }
    locked = [
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    ]
    author_open_controls = [
        item
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    ]
    model = {
        "schema_version": "2.0",
        "skill": "novel-world-model-designer",
        "stage": "W1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": owned_ids,
            "downstream_freedom": [item["id"] for item in environment_demands],
            "author_open": [item["id"] for item in author_open_controls],
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "storyline_requirements": requirements,
        "world_definition": {
            "premise": f"One regulated world carries all approved obligations: {all_markers}",
            "scope": f"The designed world covers only story-relevant operations: {all_markers}",
            "period": f"A period shaped by accumulated institutional pressure: {all_markers}",
            "reality_relation": f"Reality claims are bounded by B0 while fiction carries: {all_markers}",
            "operating_logic": f"Capability always meets authority, scarcity, and failure: {all_markers}",
            "boundaries": [
                f"No convenient world mechanism may bypass: {all_markers}",
                "Concrete environments, events, and character profiles remain downstream.",
            ],
            "story_relevance": f"Every rule exists to carry an S1 obligation: {all_markers}",
        },
        "world_facts": facts,
        "reality_claims": reality_claims,
        "world_facets": facets,
        "history_pressures": history,
        "institutions": institutions,
        "systems": systems,
        "resource_flows": resource_flows,
        "authority_flows": authority_flows,
        "information_flows": information_flows,
        "rule_conflict_matrix": conflicts,
        "storyline_support_ledger": support,
        "environment_demands": environment_demands,
        "open_items": [
            {
                "id": f"OPEN-W1-{index:03d}",
                "question": f"Preserve author-open control {item['id']}.",
                "source_ids": [item["id"]],
                "status": "author_open",
            }
            for index, item in enumerate(author_open_controls, 1)
        ],
    }
    return model

def _environment_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    baseline: dict[str, object],
    storyline: dict[str, object],
    world: dict[str, object],
) -> dict[str, object]:
    """A test Agent's authored E1 model; production never synthesizes it."""

    demands = copy.deepcopy(world["environment_demands"])
    storyline_environment_requirements = copy.deepcopy(
        storyline["environment_requirements"]
    )
    lines = {item["id"]: item for item in storyline["storylines"]}
    environment_requirement_by_line = {}
    for requirement in storyline_environment_requirements:
        line_id = next(
            item for item in requirement["source_ids"] if item in lines
        )
        environment_requirement_by_line[line_id] = requirement
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
        world_requirement_id = next(
            item for item in demand["source_ids"] if item in world_requirements
        )
        world_requirement = world_requirements[world_requirement_id]
        line_id = next(
            item for item in world_requirement["source_ids"] if item in lines
        )
        environment_requirement = environment_requirement_by_line[line_id]
        event_requirement = event_by_line[line_id]
        support_ids = [
            item for item in demand["source_ids"] if item in world_entities
        ]
        marker = demand["responsibility"]
        environment_marker = environment_requirement["responsibility"]
        combined_constraints = list(
            dict.fromkeys(
                [
                    *copy.deepcopy(demand["constraints"]),
                    *copy.deepcopy(environment_requirement["constraints"]),
                ]
            )
        )
        environment_id = f"ENV-{index:03d}"
        zone_id = f"ZONE-{index:03d}"
        decision_id = f"DEC-E1-{index:03d}"
        assignment_id = f"ACCESS-{index:03d}"
        channel_id = f"CHANNEL-{index:03d}"
        hazard_id = f"HAZ-{index:03d}"
        hosting_id = f"COV-E1-{index:03d}"
        affordance_id = f"AFF-{index:03d}"
        transition_id = f"TRANS-{index:03d}"
        action = f"Perform a bounded action required by {marker}."
        from_state = f"available for {marker}"
        to_state = f"restricted after an attempted action for {marker}"

        decisions.append(
            {
                "id": decision_id,
                "gap": f"Choose a reusable environment duty for {marker}.",
                "options": [
                    f"Create a controlled host for {marker}.",
                    f"Use an incidental one-use location for {marker}.",
                ],
                "selection": f"Create a controlled host for {marker}.",
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
            "scope": f"A bounded operational environment for {marker}.",
            "narrative_responsibility": (
                f"Uniquely host W1 demand {demand['id']} ({marker}) and "
                f"S1 requirement {environment_requirement['id']} "
                f"({environment_marker})."
            ),
            "features": [
                f"Control surfaces expose the capability needed by {marker}.",
                (
                    "The same surfaces realize the S1 capability: "
                    f"{environment_requirement['required_capability']}"
                ),
                f"Boundaries make the limits of {marker} observable.",
            ],
            "sensory_conditions": [
                f"Actors can perceive access status and resource pressure for {marker}."
            ],
            "access_rules": [
                *copy.deepcopy(combined_constraints),
                f"Access must cite W1 support {', '.join(support_ids)} for {marker}.",
            ],
            "resources": [
                f"Resources explicitly support {demand['required_capability']}",
                (
                    "Resources also support the S1 environment capability: "
                    f"{environment_requirement['required_capability']}"
                ),
            ],
            "allowed_actions": [action],
            "hazards": [f"{hazard_id} can block or worsen {marker}."],
            "zone_ids": [zone_id],
            "connections": [],
            "blockers": [f"Failed permission or exhausted resources block {marker}."],
            "state_vocabulary": [from_state, to_state],
            "allowed_transitions": [transition_id],
            "storyline_stage_ids": [
                line_id,
                demand["id"],
                environment_requirement["id"],
            ],
        }
        environments.append(environment)
        zones.append(
            {
                "id": zone_id,
                "environment_id": environment_id,
                "responsibility": f"Expose the action interface for {marker}.",
                "features": [f"Observable controls support {marker}."],
                "access_rules": copy.deepcopy(combined_constraints),
                "resources": [f"Bounded resource access for {marker}."],
                "constraints": [f"The zone cannot decide an event result for {marker}."],
            }
        )
        assignments.append(
            {
                "id": assignment_id,
                "subject_id": environment_id,
                "responsibility": f"Authorize bounded access for {marker}.",
                "evidence_ids": support_ids,
                "constraints": copy.deepcopy(combined_constraints),
            }
        )
        channels.append(
            {
                "id": channel_id,
                "from_id": environment_id,
                "to_id": zone_id,
                "relation": (
                    f"[DEMAND:{demand['id']}] supplies resource and "
                    f"observable information for {marker}"
                ),
                "mechanism": (
                    f"[MARKER_SHA256:{runtime.canonical_sha256(marker)}] "
                    f"[ACTION_SHA256:{runtime.canonical_sha256(action)}] "
                    f"bounded operational channel for {marker}"
                ),
                "constraints": [
                    *copy.deepcopy(combined_constraints),
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
                "trigger": f"Permission, resource, or information failure during {marker}.",
                "effect": f"The attempted action is blocked or becomes costlier for {marker}.",
                "mitigation_limits": [
                    f"Mitigation cannot remove W1 constraints for {marker}."
                ],
            }
        )
        hosting.append(
            {
                "id": hosting_id,
                "source_ids": [
                    demand["id"],
                    environment_requirement["id"],
                ],
                "realization_ids": [environment_id],
                "status": "covered",
                "evidence": (
                    f"{environment_id} concretely hosts W1 responsibility "
                    f"{marker} and S1 responsibility {environment_marker}."
                ),
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
            "constraints": copy.deepcopy(combined_constraints),
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
            "consequence": f"The environment changes availability without deciding an event result for {marker}.",
        }
        transitions.append(transition)
        derivations.extend(
            [
                {
                    "id": f"DRV-E1-ENV-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(environment),
                    "source_ids": [
                        demand["id"],
                        environment_requirement["id"],
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
                        environment_requirement["id"],
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
    return {
        "schema_version": "2.1",
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
        "storyline_environment_requirements": (
            storyline_environment_requirements
        ),
        "environments": environments,
        "functional_zones": zones,
        "environment_topology": topology,
        "access_and_authority": assignments,
        "resource_and_information_channels": channels,
        "hazards_and_failure_modes": hazards,
        "storyline_hosting_ledger": hosting,
        "event_affordance_catalog": affordances,
        "transition_contracts": transitions,
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

def _event_proposal(
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
    state_anchors: dict[tuple[str, int], dict[str, object]] = {}
    for line in lines:
        line_id = line["id"]
        event_ids = []
        states = [
            line["start_state"],
            *line["state_changes"],
            line["end_state"],
        ]
        role_groups = _event_role_groups(len(states) - 1)
        affordance = affordance_by_line[line_id]
        environment_id = affordance["environment_id"]
        for role_index, roles in enumerate(role_groups):
            event_id = f"EV-{line_id[3:]}-{role_index + 1:02d}"
            event_ids.append(event_id)
            subject_id = line_id
            before = states[role_index]
            after = states[role_index + 1]
            predecessors = [] if role_index == 0 else [event_ids[-2]]
            role_text = "".join(f"[RESP:{role}]" for role in roles)
            event = {
                "id": event_id,
                "responsibility": (
                    f"{role_text} Agent event for {requirement_by_line[line_id]['responsibility']}"
                ),
                "world_time": "[WT:000000]",
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
                    "consequence": f"[KIND:state] {event['direct_result']}",
                }
            )
            if role_index == 0:
                state_anchors[(line_id, 0)] = {
                    "event_id": event_id,
                    "storyline_id": line_id,
                    "state_index": 0,
                    "state": before,
                    "side": "before",
                }
            state_anchors[(line_id, role_index + 1)] = {
                "event_id": event_id,
                "storyline_id": line_id,
                "state_index": role_index + 1,
                "state": after,
                "side": "after",
            }
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
    connection_records = []
    for connection in storyline["connections"]:
        required_fields = {
            "id",
            "relation",
            "from_storyline_id",
            "to_storyline_id",
            "from_state",
            "from_state_index",
            "to_state",
            "to_state_index",
        }
        missing = sorted(required_fields - set(connection))
        if missing:
            raise ProposalEvidenceError(
                "T1_PROPOSAL_CONNECTION_CONTRACT_MISSING: "
                f"{connection.get('id', '<unknown>')} {missing}"
            )
        if connection["relation"] not in {"causal", "associative"}:
            raise ProposalEvidenceError(
                "T1_PROPOSAL_CONNECTION_RELATION_INVALID: "
                f"{connection['id']}"
            )
        source_id = connection["from_storyline_id"]
        target_id = connection["to_storyline_id"]
        anchors: dict[str, dict[str, object]] = {}
        for endpoint, line_id in (
            ("from", source_id),
            ("to", target_id),
        ):
            state_index = connection[f"{endpoint}_state_index"]
            if (
                isinstance(state_index, bool)
                or not isinstance(state_index, int)
            ):
                raise ProposalEvidenceError(
                    "T1_PROPOSAL_CONNECTION_STATE_INDEX_INVALID: "
                    f"{connection['id']}.{endpoint}"
                )
            anchor = state_anchors.get((line_id, state_index))
            if (
                anchor is None
                or anchor["state"] != connection[f"{endpoint}_state"]
            ):
                raise ProposalEvidenceError(
                    "T1_PROPOSAL_CONNECTION_STATE_INVALID: "
                    f"{connection['id']}.{endpoint}"
                )
            anchors[endpoint] = copy.deepcopy(anchor)
        source_event = str(anchors["from"]["event_id"])
        target_event = str(anchors["to"]["event_id"])
        causal_edge_ids: list[str] = []
        if connection["relation"] == "causal":
            edge_id = f"CE-SLC-{connection['id'][4:]}"
            event_index[target_event]["predecessor_event_ids"].append(
                source_event
            )
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
            causal_edge_ids = [edge_id]
            realization_kind = "causal_handoff"
            timing_relation = "convergence"
            timing_effect = (
                "The source state changes the target-line pressure."
            )
        else:
            realization_kind = "associative_alignment"
            timing_relation = "association"
            timing_effect = (
                "The states align thematically without creating causal order."
            )
        timing_id = f"TIME-SLC-{connection['id'][4:]}"
        connection_records.append(
            {
                "id": f"CR-{connection['id'][4:]}",
                "connection_id": connection["id"],
                "relation": connection["relation"],
                "realization_kind": realization_kind,
                "source_anchor": anchors["from"],
                "target_anchor": anchors["to"],
                "causal_edge_ids": causal_edge_ids,
                "timing_constraint_ids": [timing_id],
            }
        )
        timing.append(
            {
                "id": timing_id,
                "event_ids": [source_event, target_event],
                "constraint": (
                    f"[REL:{timing_relation}] "
                    f"{connection['from_state']} aligns with "
                    f"{connection['to_state']}."
                ),
                "story_effect": timing_effect,
            }
        )

    graph_world_times = _graph_derived_world_times(
        [event["id"] for event in events],
        causal_edges,
    )
    for event in events:
        event["world_time"] = graph_world_times[event["id"]]

    evidence_kind, evidence_event, evidence_edge = _select_information_evidence(
        {
            "information_changes": [],
            "major_events": events,
            "causal_edges": causal_edges,
        }
    )
    changed_subjects = [
        subject_id
        for subject_id in evidence_event["before_state"]
        if evidence_event["before_state"][subject_id]
        != evidence_event["after_state"][subject_id]
    ]
    if len(changed_subjects) != 1:
        raise ProposalEvidenceError(
            "T1_PROPOSAL_INFORMATION_EVIDENCE_AMBIGUOUS: selected event must "
            "have exactly one state transition"
        )
    information_change = {
        "id": "INFO-T1-001",
        "subject_id": changed_subjects[0],
        "before": (
            f"[{evidence_kind}] Before {evidence_event['id']}: "
            f"{evidence_event['before_state'][changed_subjects[0]]}"
        ),
        "after": (
            f"[{evidence_kind}] After {evidence_event['id']}: "
            f"{evidence_event['after_state'][changed_subjects[0]]}"
        ),
        "event_ids": [evidence_event["id"]],
        "visibility_ids": [evidence_event["participant_slot_ids"][0]],
    }
    if evidence_edge is not None:
        information_change["after"] += (
            f"; causal evidence {evidence_edge['id']} reaches this event"
        )
    evidence_event["information_changes"] = [information_change["id"]]
    information_changes = [information_change]

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
        *[item["id"] for item in events],
        *[item["id"] for item in causal_edges],
        *[item["id"] for item in sequences],
        *[item["id"] for item in timing],
        *[item["id"] for item in ledgers],
        *[item["id"] for item in connection_records],
        *[item["id"] for item in coverage],
        *[item["id"] for item in information_changes],
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
    return {
        "schema_version": "2.0",
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
        "major_events": events,
        "causal_edges": causal_edges,
        "storyline_event_sequences": sequences,
        "connection_realization": connection_records,
        "environment_placement": placements,
        "state_ledger": ledgers,
        "information_changes": information_changes,
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

def _character_proposal(
    *,
    run_id,
    gate_reference,
    source_artifacts,
    baseline,
    storyline,
    world,
    environment,
    timeline,
):
    """Test-only Agent authors character semantics; production Python never does."""
    maps = c1._c1_maps(storyline, world, environment, timeline)
    slots = sorted(maps["required_slots"])
    slot_to_char = {
        slot: f"CHR-C1-{index:03d}" for index, slot in enumerate(slots, 1)
    }
    resolutions = [
        {
            "slot_id": slot,
            "character_id": slot_to_char[slot],
            "demand_ids": sorted(maps["slot_demands"][slot]),
            "event_ids": sorted(maps["slot_events"][slot]),
            "rationale": (
                "".join(
                    f"[DEMAND:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
                    f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + f" {slot} remains distinct because these duties are compatible."
            ),
        }
        for slot in slots
    ]
    main_line = next(
        line
        for line in storyline["storylines"]
        if line["type"] == "main"
    )
    main_sequence = next(
        sequence
        for sequence in timeline["storyline_event_sequences"]
        if sequence["storyline_id"] == main_line["id"]
    )
    event_by_id = {
        event["id"]: event for event in timeline["major_events"]
    }
    first_event = main_sequence["event_ids"][0]
    core = slot_to_char[event_by_id[first_event]["initiator_slot_id"]]
    extras = ["CHR-NET-1", "CHR-NET-2", "CHR-NET-3"]
    all_chars = [*slot_to_char.values(), *extras]
    relations = [
        {
            "id": f"REL-{index}",
            "from_character_id": left,
            "to_character_id": right,
            "function": f"[FUNCTION:{kind}] Maintains a distinct pressure path.",
            "start_state": f"{left} cannot yet rely on {right}.",
            "change_event_ids": [first_event],
            "end_state": f"{left} must account for {right}.",
            "boundaries": ["The relationship cannot erase either party's agency."],
        }
        for index, (left, right, kind) in enumerate(
            (
                (core, extras[0], "direct"),
                (extras[0], extras[1], "institutional"),
                (extras[1], extras[2], "contextual"),
            ),
            1,
        )
    ]
    incident = {character_id: [] for character_id in all_chars}
    for relation in relations:
        for endpoint in ("from_character_id", "to_character_id"):
            character_id = relation[endpoint]
            incident[character_id].append(
                f"[REL:{relation['id']}] The relationship changes available support."
            )
    initiated = {character_id: [] for character_id in all_chars}
    participated = {character_id: [] for character_id in all_chars}
    providers = {character_id: set() for character_id in all_chars}
    capabilities = {character_id: set() for character_id in all_chars}
    for event in timeline["major_events"]:
        event_id = event["id"]
        initiator = slot_to_char[event["initiator_slot_id"]]
        initiated[initiator].append(event_id)
        providers[initiator].update(maps["ledger_providers"].get(event_id, set()))
        capabilities[initiator].add(
            f"[ACTION_SHA256:{runtime.canonical_sha256(event['initiating_action'])}] "
            f"Can initiate {event_id} without changing its result."
        )
        for slot in event["participant_slot_ids"]:
            character_id = slot_to_char[slot]
            participated[character_id].append(event_id)
            capabilities[character_id].add(
                f"[ENV_ACCESS:{event['environment_id']}] Can function in {event['environment_id']}."
            )
        for slot in event["counter_slot_ids"]:
            capabilities[slot_to_char[slot]].add(
                f"[COUNTER_EVENT:{event_id}] Can execute the recorded counter-pressure."
            )
    evidence_kind, evidence_item, _ = _select_information_evidence(timeline)
    if evidence_kind != "explicit_information_change":
        raise ProposalEvidenceError(
            "C1_PROPOSAL_INFORMATION_CHANGE_REQUIRED: sealed T1 contains "
            f"{evidence_kind} evidence but no T1-owned information change; "
            "C1 must not manufacture one"
        )
    info_change = evidence_item
    visible_char = slot_to_char[info_change["visibility_ids"][0]]
    info_event = info_change["event_ids"][0]
    known = (
        f"[KNOWN_AFTER:{info_change['id']}:{info_event}]"
        f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
        f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
        f"After {info_event}, the character knows the recorded change."
    )
    unknown = (
        f"[UNKNOWN_BEFORE:{info_change['id']}:{info_event}]"
        f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
        f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
        f"Before {info_event}, the character does not know the recorded change."
    )
    profiles = []
    for index, character_id in enumerate(all_chars, 1):
        is_core = character_id == core
        character_slots = {
            slot for slot, resolved in slot_to_char.items()
            if resolved == character_id
        }
        character_demands = sorted(
            {
                demand_id
                for slot in character_slots
                for demand_id in maps["slot_demands"][slot]
            }
        )
        demand_blocks = "".join(
            f"[DEMAND:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
            f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
            for demand_id in character_demands
        )
        demand_goals = [
            f"[DEMAND_EFFECT:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}:goal] "
            f"Fulfil {maps['demands'][demand_id]['responsibility']} through owned choices."
            for demand_id in character_demands
        ]
        demand_boundaries = [
            f"[TYPE:hard-boundary] [DEMAND_EFFECT:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}:boundary] "
            f"Will not violate the constraints of {maps['demands'][demand_id]['responsibility']}."
            for demand_id in character_demands
        ]
        profile_unknown = unknown if character_id == visible_char else (
            f"[UNKNOWN_BEFORE:{info_change['id']}:{info_event}]"
            f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
            f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
            "This character is outside the visibility change."
        )
        profiles.append(
            {
                "id": character_id,
                "name": f"[CLASS:{'core' if is_core else 'support'}] Test Person {index}",
                "story_responsibility": (
                    demand_blocks + " Carries the exact event and relationship duties."
                    if character_id in slot_to_char.values()
                    else "Extends the core network through an irreplaceable relationship function."
                ),
                "goals": (
                    demand_goals
                    if demand_goals
                    else [f"Preserve the consequence assigned to {character_id}."]
                ),
                "values": ["Choices must remain accountable to affected people."],
                "boundaries": [
                    "[TYPE:blind-spot] Under pressure, misses one indirect consequence.",
                    *(
                        demand_boundaries
                        if demand_boundaries
                        else ["[TYPE:hard-boundary] Will not erase another person's agency."]
                    ),
                ],
                "capabilities": sorted(capabilities[character_id]),
                "authorities": sorted(providers[character_id]),
                "information_limits": [profile_unknown],
                "pressure_behavior": "Narrows options, then makes an owned choice.",
                "agency_choices": ["Act now.", "Delay and absorb a larger cost."],
                "non_delegable_choices": ["Accept the consequence of the final decision."],
                "relationship_levers": incident[character_id],
                "arc_direction": "Pressure clarifies the value the character will protect.",
                "forbidden_portrayals": ["Do not replace motive with plot convenience."],
            }
        )
    profile_by_id = {item["id"]: item for item in profiles}
    obligations = c1._c1_obligations(maps, timeline)
    responsibilities = []
    ordered_obligations = sorted(
        obligations.items(), key=c1._c1_obligation_sort_key
    )
    for index, (_, obligation) in enumerate(ordered_obligations, 1):
        character_id = slot_to_char[obligation["slot_id"]]
        evidence = [
            item
            for item in (
                obligation.get("event_id"),
                obligation.get("storyline_id"),
                obligation.get("information_id"),
            )
            if item
        ]
        constraints = [
            f"[DEMAND_SHA256:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
            for demand_id in sorted(
                maps["slot_demands"][obligation["slot_id"]]
            )
        ]
        constraints.append("Must preserve all frozen upstream outcomes.")
        if obligation["kind"] == "decision":
            constraints.extend(
                [
                f"[GOAL_SHA256:{runtime.canonical_sha256(profile_by_id[character_id]['goals'])}]",
                f"[VALUE_SHA256:{runtime.canonical_sha256(profile_by_id[character_id]['values'])}]",
                ]
            )
        responsibilities.append(
            {
                "id": f"ASG-C1-{index:03d}",
                "subject_id": character_id,
                "responsibility": (
                    f"[KIND:{obligation['kind']}][SLOT:{obligation['slot_id']}] "
                    "Own this structural duty without changing the event."
                ),
                "evidence_ids": evidence,
                "constraints": constraints,
            }
        )
    agencies = []
    for index, (character_id, event_ids) in enumerate(
        ((key, value) for key, value in initiated.items() if value), 1
    ):
        duty_digest = runtime.canonical_sha256(
            profile_by_id[character_id]["story_responsibility"]
        )
        chosen = (
            "".join(
                f"[INIT_ACTION:{event_id}:"
                f"{runtime.canonical_sha256(maps['events'][event_id]['initiating_action'])}]"
                for event_id in event_ids
            )
            + f"[DUTY_SHA256:{duty_digest}] "
            + f"Execute the recorded initiating actions for {','.join(event_ids)}."
        )
        agencies.append(
            {
                "id": f"AGY-C1-{index:03d}",
                "character_id": character_id,
                "event_ids": event_ids,
                "available_choices": [chosen, "Refuse and accept the explicit downstream cost."],
                "chosen_action": chosen,
                "cost": (
                    f"[DUTY_SHA256:{duty_digest}] The choice creates an "
                    "accountable personal and relational cost."
                ),
            }
        )
    information = [
        {
            "id": "INFO-C1-001",
            "character_id": visible_char,
            "knows": [known],
            "does_not_know": [unknown],
            "misreads": [],
            "change_event_ids": list(info_change["event_ids"]),
        }
    ]
    profile_by_id[visible_char]["information_limits"] = [unknown]
    arcs = [
        {
            "id": f"ARC-C1-{index:03d}",
            "character_id": agency["character_id"],
            "start_state": "The cost of choosing is not yet personally owned.",
            "pressure_event_ids": list(agency["event_ids"]),
            "choice_event_ids": list(agency["event_ids"]),
            "end_state": "The character owns the consequence without losing the core value.",
            "theme_effect": (
                f"[DUTY_SHA256:{runtime.canonical_sha256(profile_by_id[agency['character_id']]['story_responsibility'])}] "
                "Agency is proved by accountable choice under constraint."
            ),
        }
        for index, agency in enumerate(agencies, 1)
    ]
    storyline_coverage = [
        {
            "id": f"COV-C1-SL-{index:03d}",
            "source_ids": [line_id],
            "realization_ids": sorted(slot_to_char[slot] for slot in maps["line_slots"][line_id]),
            "status": "covered",
            "evidence": (
                "".join(
                    f"[CHAIN:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}:"
                    f"{slot}:{slot_to_char[slot]}:{line_id}]"
                    for slot in sorted(maps["line_slots"][line_id])
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + " Every storyline demand, slot and character is closed."
            ),
        }
        for index, line_id in enumerate(sorted(maps["lines"]), 1)
    ]
    event_coverage = [
        {
            "id": f"COV-C1-EV-{index:03d}",
            "source_ids": [event_id],
            "realization_ids": sorted(slot_to_char[slot] for slot in maps["event_slots"][event_id]),
            "status": "covered",
            "evidence": (
                "".join(
                    f"[CHAIN:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}:"
                    f"{slot}:{slot_to_char[slot]}:{event_id}]"
                    for slot in sorted(maps["event_slots"][event_id])
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + " Every event demand, slot and character is closed."
            ),
        }
        for index, event_id in enumerate(sorted(maps["events"]), 1)
    ]
    terminal = {
        item["event_ids"][-1] for item in timeline["storyline_event_sequences"]
    }
    aftermath = [
        {
            "id": f"ASG-C1-AF-{index:03d}",
            "subject_id": slot_to_char[maps["events"][event_id]["initiator_slot_id"]],
            "responsibility": "[KIND:aftermath] Own the terminal consequence.",
            "evidence_ids": [event_id],
            "constraints": ["Do not erase the recorded aftermath."],
        }
        for index, event_id in enumerate(sorted(terminal), 1)
    ]
    core_digest = runtime.canonical_sha256([core])
    decisions = [
        {
            "id": "DEC-C1-CORE",
            "gap": "Select the smallest core set that carries the main-line choices.",
            "options": [
                f"[CORE_EVIDENCE_SHA256:{core_digest}] Select {core}.",
                "Select every participant as core.",
            ],
            "selection": f"[CORE_EVIDENCE_SHA256:{core_digest}] Select {core}.",
            "owner": "C1",
            "authority_basis": "C1 owns character centrality and network design.",
            "compatibility": "The selected character initiates a true main-line event.",
            "impact_ids": [core],
            "cost": "Supporting characters remain non-core while keeping agency.",
            "reversibility": "costly",
            "downstream_freedom": "Scene emphasis remains open.",
            "projection_ids": [core],
        }
    ]
    development_freedoms = [
        {
            "id": f"DEV-C1-{index:03d}",
            "subject_ids": [profile["id"]],
            "scope": (
                f"Development may vary scene-level expression for "
                f"{profile['name']} while preserving the frozen character duty."
            ),
            "allowed_variations": [
                "Vary gesture, pacing, and non-binding surface detail.",
                "Choose scene emphasis that preserves the assigned story responsibility.",
            ],
            "forbidden_changes": [
                "Do not change the character's frozen story responsibility.",
                "Do not reverse agency, information limits, or relationship boundaries.",
            ],
            "acceptance_checks": [
                f"The developed material still identifies {profile['id']} as the acting subject.",
                "Every developed choice remains compatible with the profile goals and boundaries.",
            ],
            "source_ids": [profile["id"]],
        }
        for index, profile in enumerate(profiles, 1)
    ]
    generated = [
        *[item["id"] for item in decisions],
        *[item["id"] for item in profiles],
        *[item["id"] for item in responsibilities],
        *[item["id"] for item in agencies],
        *[item["id"] for item in information],
        *[item["id"] for item in arcs],
        *[item["id"] for item in relations],
        *[item["id"] for item in storyline_coverage],
        *[item["id"] for item in event_coverage],
        *[item["id"] for item in aftermath],
    ]
    derivations = [
        {
            "id": f"DRV-C1-{index:03d}",
            "value_sha256": runtime.canonical_sha256(item),
            "source_ids": (
                sorted(
                    {
                        demand_id
                        for slot, resolved in slot_to_char.items()
                        if resolved == item["id"]
                        for demand_id in maps["slot_demands"][slot]
                    }
                )
                if item["id"] in profile_by_id
                and item["id"] in slot_to_char.values()
                else [first_event]
            ),
            "decision_ids": ["DEC-C1-CORE"],
            "projection_ids": [item["id"]],
        }
        for index, item in enumerate([*profiles, *arcs, *relations], 1)
    ]
    locked = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"]
    opened = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"]
    return {
        "schema_version": "2.0",
        "skill": "novel-character-system-designer",
        "stage": "C1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": generated,
            "downstream_freedom": [
                item["id"] for item in development_freedoms
            ],
            "author_open": opened,
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "character_demands": copy.deepcopy(storyline["character_requirements"]),
        "slot_resolution": resolutions,
        "profiles": profiles,
        "responsibility_matrix": responsibilities,
        "agency_matrix": agencies,
        "information_matrix": information,
        "character_arcs": arcs,
        "relationships": relations,
        "three_layer_networks": [
            {
                "core_character_id": core,
                "layer_1_direct": [extras[0]],
                "layer_2_institutional": [extras[1]],
                "layer_3_contextual": [extras[2]],
                "relationship_ids": [item["id"] for item in relations],
                "story_function": "Extends direct pressure into institutional and contextual consequences.",
            }
        ],
        "storyline_cast_coverage": storyline_coverage,
        "event_cast_coverage": event_coverage,
        "aftermath_responsibility": aftermath,
        "development_freedoms": development_freedoms,
        "open_items": [
            {
                "id": f"OPEN-C1-{index:03d}",
                "question": f"Preserve author-open control {control_id}.",
                "source_ids": [control_id],
                "status": "author_open",
            }
            for index, control_id in enumerate(opened, 1)
        ],
    }

class DeclarativeProposalAdapter:
    """Bind eval-authored proposals to one declarative fixture and live lineage.

    Direct construction is retained only for legacy unit/downstream tests.
    Formal S1 evidence must use :meth:`from_manifest` with a manifest path.
    External loaded-case objects are never accepted as formal input.
    """

    def __init__(self, fixture: Mapping[str, Any]) -> None:
        self._validated_case = None
        self._storyline_projection_evidence = None
        self.fixture = copy.deepcopy(dict(fixture))
        controls = self.fixture.get("interviews")
        anchors = self.fixture.get("semantic_assertions")
        if not isinstance(controls, list) or not controls:
            raise ValueError("fixture interviews are required")
        if not isinstance(anchors, list) or not anchors:
            raise ValueError("fixture semantic_assertions are required")
        control_ids = {str(item["control_id"]) for item in controls}
        for anchor in anchors:
            missing = set(anchor.get("required_source_ids", [])) - control_ids
            if missing:
                raise ValueError(
                    f"anchor {anchor.get('anchor_id')} has unknown controls: "
                    f"{sorted(missing)}"
                )

    @classmethod
    def from_manifest(
        cls,
        manifest_path: str | Path,
        *,
        repository_root: str | Path = storyline_quality.REPOSITORY_ROOT,
        evals_root: str | Path = storyline_quality.EVALS_ROOT,
    ) -> "DeclarativeProposalAdapter":
        """Load and snapshot the sole formal case from one manifest path."""

        if not isinstance(manifest_path, (str, Path)):
            raise ProposalEvidenceError(
                "S1_EVAL_MANIFEST_PATH_REQUIRED: externally loaded cases, "
                "raw fixtures, and structural cases are not formal input"
            )
        admitted = storyline_quality.load_ready_eval_case(
            manifest_path,
            repository_root=repository_root,
            evals_root=evals_root,
        )
        if not isinstance(
            admitted,
            storyline_quality.FormalValidatedStorylineQualityCase,
        ):
            raise ProposalEvidenceError(
                "S1_EVAL_FORMAL_ADMISSION_TYPE_INVALID"
            )
        validated_case = copy.deepcopy(admitted)
        self = cls.__new__(cls)
        self._validated_case = validated_case
        self._storyline_projection_evidence = None
        self.fixture = copy.deepcopy(
            validated_case.structural_case.fixture
        )
        controls = self.fixture.get("interviews")
        anchors = self.fixture.get("semantic_assertions")
        if not isinstance(controls, list) or not controls:
            raise ProposalEvidenceError(
                "S1_EVAL_FIXTURE_CONTROLS_REQUIRED"
            )
        if not isinstance(anchors, list) or not anchors:
            raise ProposalEvidenceError(
                "S1_EVAL_FIXTURE_ANCHORS_REQUIRED"
            )
        return self

    @property
    def is_formal(self) -> bool:
        return self._validated_case is not None

    @property
    def formal_case_snapshot(self) -> Any:
        if self._validated_case is None:
            raise ProposalEvidenceError(
                "S1_EVAL_FORMAL_CASE_UNAVAILABLE"
            )
        return copy.deepcopy(self._validated_case)

    @property
    def storyline_projection_evidence(self) -> dict[str, Any]:
        if self._storyline_projection_evidence is None:
            raise ProposalEvidenceError(
                "S1_EVAL_PROJECTION_EVIDENCE_UNAVAILABLE"
            )
        return copy.deepcopy(self._storyline_projection_evidence)

    def storyline(self, **kwargs: Any) -> dict[str, Any]:
        expected = {
            str(item["control_id"]) for item in self.fixture["interviews"]
        }
        actual = {str(item["id"]) for item in kwargs["controls"]}
        if actual != expected:
            raise ValueError("live baseline controls do not match fixture controls")
        if self._validated_case is not None:
            model, evidence = _formal_storyline_proposal(
                self._validated_case,
                **kwargs,
            )
            self._storyline_projection_evidence = evidence
            return model
        return _storyline_proposal(**kwargs)

    def world(self, **kwargs: Any) -> dict[str, Any]:
        return _world_proposal(**kwargs)

    def environment(self, **kwargs: Any) -> dict[str, Any]:
        return _environment_proposal(**kwargs)

    def event(self, **kwargs: Any) -> dict[str, Any]:
        return _event_proposal(**kwargs)

    def character(self, **kwargs: Any) -> dict[str, Any]:
        return _character_proposal(**kwargs)

    def preflight(
        self, *, baseline: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Dry-author every proposal and reject ID/authority collisions.

        B0 is the accepted input boundary.  This preflight must run before S1
        is submitted to any production stage runtime.
        """

        expected = [
            str(item["control_id"]) for item in self.fixture["interviews"]
        ]
        actual = [
            str(item["id"]) for item in baseline.get("control_registry", [])
        ]
        if set(actual) != set(expected) or len(actual) != len(expected):
            raise ValueError(
                "ID_PREFLIGHT_BASELINE_DEFINITIONS_MISMATCH: "
                + runtime.canonical_json(
                    {"expected": sorted(expected), "actual": sorted(actual)}
                )
            )
        if self._validated_case is not None:
            registry = {
                str(item["id"]): item
                for item in baseline.get("control_registry", [])
            }
            fixture_controls = {
                str(item["control_id"]): item
                for item in self.fixture["interviews"]
            }
            for control_id, expected_control in fixture_controls.items():
                current = registry[control_id]
                expected_heading = (
                    f"[{control_id}]"
                    f"[{expected_control['hardness']}] "
                    f"{expected_control['heading']}"
                )
                if (
                    current.get("hardness")
                    != expected_control.get("hardness")
                    or current.get("heading")
                    != expected_heading
                    or current.get("domain")
                    != expected_control.get("stage")
                    or current.get("value_sha256")
                    != runtime.canonical_sha256(
                        expected_control.get("value")
                    )
                ):
                    raise ProposalEvidenceError(
                        "S1_EVAL_BASELINE_CONTROL_MISMATCH: "
                        + control_id
                    )
            return {
                "schema_version": "1.0",
                "status": "ready",
                "mode": "formal-manifest-quality-gated-s1",
                "manifest_id": self._validated_case.structural_case.manifest[
                    "manifest_id"
                ],
                "plan_id": self._validated_case.structural_case.plan[
                    "plan_id"
                ],
                "quality_gate_id": self._validated_case.gate["gate_id"],
                "baseline_definition_ids": sorted(actual),
                "structural_validation_sha256": runtime.canonical_sha256(
                    self._validated_case.structural_case.validation
                ),
                "quality_validation_sha256": runtime.canonical_sha256(
                    self._validated_case.validation
                ),
            }
        gate = {"path": "preflight/input-gate.json", "sha256": "0" * 64}
        common = {
            "run_id": str(baseline["run_id"]),
            "gate_reference": gate,
            "source_artifacts": [],
            "baseline": copy.deepcopy(dict(baseline)),
        }
        controls = [
            {
                "id": str(item["control_id"]),
                "hardness": str(item["hardness"]),
                "heading": str(item["heading"]),
                "value": copy.deepcopy(item["value"]),
            }
            for item in self.fixture["interviews"]
        ]
        storyline = self.storyline(
            run_id=common["run_id"],
            gate_reference=gate,
            source_artifacts=[],
            controls=controls,
        )
        world = self.world(**common, storyline=storyline)
        environment = self.environment(
            **common, storyline=storyline, world=world
        )
        timeline = self.event(
            **common,
            storyline=storyline,
            world=world,
            environment=environment,
        )
        character = self.character(
            **common,
            storyline=storyline,
            world=world,
            environment=environment,
            timeline=timeline,
        )
        registry = IdRegistry(expected)
        for model in (
            storyline,
            world,
            environment,
            timeline,
            character,
        ):
            registry.register(model)
        evidence = registry.evidence()
        evidence["baseline_definition_ids"] = sorted(actual)
        evidence["fixture_provenance_sha256"] = runtime.canonical_sha256(
            self.fixture
        )
        return evidence

    def assert_authority_partitions(
        self, models: list[Mapping[str, Any]]
    ) -> dict[str, list[str]]:
        partitions = {
            "author_locked": {
                str(item["control_id"])
                for item in self.fixture["interviews"]
                if item["hardness"] == "author_locked"
            },
            "autonomous_owned": set(),
            "downstream_freedom": set(),
            "author_open": {
                str(item["control_id"])
                for item in self.fixture["interviews"]
                if item["hardness"] == "author_open"
            },
        }
        for model in models:
            authority = model.get("authority_partition")
            if not isinstance(authority, Mapping):
                raise ValueError("model authority_partition is required")
            for name in partitions:
                values = authority.get(name)
                if not isinstance(values, list):
                    raise ValueError(f"authority_partition.{name} must be an array")
                partitions[name].update(str(value) for value in values)
        names = list(partitions)
        conflicts = {
            f"{left}/{right}": sorted(partitions[left] & partitions[right])
            for index, left in enumerate(names)
            for right in names[index + 1 :]
            if partitions[left] & partitions[right]
        }
        if conflicts:
            raise ValueError(f"authority partition conflict: {conflicts}")
        return {name: sorted(values) for name, values in partitions.items()}


class Q1ProposalAdapter:
    """Author story-bound Q1 payloads from the frozen production object index."""

    def __init__(self, frozen_inputs: Mapping[str, Any]) -> None:
        self.frozen = copy.deepcopy(dict(frozen_inputs))
        self.index = _eval_story_object_index(self.frozen)
        self.by_stage = {
            stage: sorted(
                (
                    record
                    for record in self.index.values()
                    if record["stage"] == stage
                ),
                key=lambda record: (record["id"], record["kind"]),
            )
            for stage in q1.STAGE_CANONICAL
        }
        missing = [stage for stage, records in self.by_stage.items() if not records]
        if missing:
            raise ProposalEvidenceError(
                f"Q1_PROPOSAL_STAGE_OBJECTS_MISSING: {missing}"
            )

    def _record(
        self,
        stage: str,
        *,
        kind: str | None = None,
        story_path_selector: Callable[[Mapping[str, Any]], str]
        | None = None,
    ) -> Mapping[str, Any]:
        select_story_path = story_path_selector or _eval_story_path
        for record in self.by_stage[stage]:
            if kind is not None and record["kind"] != kind:
                continue
            try:
                select_story_path(record["value"])
            except ProposalEvidenceError:
                continue
            return record
        raise ProposalEvidenceError(
            f"Q1_PROPOSAL_STAGE_STORY_OBJECT_MISSING: {stage}"
        )

    @staticmethod
    def _check(identifier: str, scope: str) -> dict[str, Any]:
        return {
            "id": identifier,
            "scope": scope,
            "checked_contract": f"{scope} story contract",
            "method": "pending-story-assertion-binding",
            "evidence_ids": [],
            "conclusion": f"{identifier} pending bound conclusion",
            "result": "pass",
        }

    def _bind(
        self,
        check: dict[str, Any],
        *,
        stages: list[str],
        predicate: str,
        operator: str,
        target_stage: str | None = None,
        cross_stage: bool = False,
        source_kind: str | None = None,
        story_path_selector: Callable[[Mapping[str, Any]], str]
        | None = None,
        relation_path_selector: Callable[
            [Mapping[str, Any], str], str | None
        ]
        | None = None,
    ) -> dict[str, Any]:
        select_story_path = story_path_selector or _eval_story_path
        relation_path = None
        if target_stage is None:
            records = [
                self._record(
                    stages[0],
                    kind=source_kind,
                    story_path_selector=select_story_path,
                )
            ]
        else:
            records = []
            for target in self.by_stage[target_stage]:
                for stage in stages:
                    for subject in self.by_stage[stage]:
                        if subject["id"] == target["id"]:
                            continue
                        if cross_stage and subject["stage"] == target["stage"]:
                            continue
                        if relation_path_selector is None:
                            matching_paths = [
                                path
                                for path, value in _eval_paths(
                                    subject["value"]
                                )
                                if _eval_contains_id(value, target["id"])
                            ]
                        else:
                            selected_path = relation_path_selector(
                                subject["value"], target["id"]
                            )
                            matching_paths = (
                                [selected_path]
                                if selected_path is not None
                                else []
                            )
                        if matching_paths:
                            try:
                                select_story_path(subject["value"])
                                select_story_path(target["value"])
                            except ProposalEvidenceError:
                                continue
                            records = [subject, target]
                            relation_path = matching_paths[0]
                            break
                    if records:
                        break
                if records:
                    break
            if not records:
                raise ProposalEvidenceError(
                    "Q1_PROPOSAL_RELATION_MISSING: "
                    f"{stages}->{target_stage}"
                )
        evidence_ids = [record["id"] for record in records]
        check["evidence_ids"] = evidence_ids
        selected = []
        for position, record in enumerate(records):
            paths = [select_story_path(record["value"])]
            if position == 0 and relation_path is not None:
                paths.append(relation_path)
            paths = list(dict.fromkeys(paths))
            selected.append(
                {
                    "id": record["id"],
                    "stage": record["stage"],
                    "kind": record["kind"],
                    "value_sha256": record["value_sha256"],
                    "projections": [
                        {
                            "path": path,
                            "value_sha256": runtime.canonical_sha256(
                                _eval_pointer_value(record["value"], path)
                            ),
                        }
                        for path in paths
                    ],
                }
            )
        target_id = records[1]["id"] if target_stage is not None else None
        check["conclusion"] = (
            f"{check['id']}: "
            f"{_eval_pointer_value(records[0]['value'], select_story_path(records[0]['value']))}"
        )
        binding = {
            "check_id": check["id"],
            "scope": check["scope"],
            "evidence_objects": selected,
            "assertion": {
                "predicate": predicate,
                "subject_id": evidence_ids[0],
                "target_id": target_id,
                "challenge_operator": operator,
                "result": check["result"],
            },
        }
        digest = runtime.canonical_sha256(binding)
        binding["assertion_sha256"] = digest
        check["method"] = f"story-assertion:{digest}"
        return binding

    def _bind_chain(
        self,
        check: dict[str, Any],
        *,
        stage_path: tuple[str, str, str],
        predicate: str,
        operator: str,
        preferred_target_kind: str | None = None,
        story_path_selector: Callable[[Mapping[str, Any]], str]
        | None = None,
    ) -> dict[str, Any]:
        """Bind one explicit two-hop lineage from frozen canonical IDs.

        This intentionally is not a general graph search.  The consistency
        contract has one admitted lineage: a T1 state transition is authorized
        by an E1 access assignment, whose evidence IDs cite a W1 object.
        Keeping the stage path explicit prevents same-stage shadows and
        unrelated narrative mentions from becoming review evidence.
        """

        source_stage, bridge_stage, target_stage = stage_path
        if stage_path != ("T1", "E1", "W1"):
            raise ProposalEvidenceError(
                f"Q1_PROPOSAL_CHAIN_STAGE_PATH_INVALID: {stage_path}"
            )
        for stage in stage_path:
            if stage not in self.by_stage:
                raise ProposalEvidenceError(
                    f"Q1_PROPOSAL_CHAIN_STAGE_MISSING: {stage}"
                )

        targets = list(self.by_stage[target_stage])
        if preferred_target_kind is not None:
            targets.sort(
                key=lambda record: (
                    record["kind"] != preferred_target_kind,
                    record["id"],
                    record["kind"],
                )
            )
        select_story_path = (
            story_path_selector or _eval_consistency_story_path
        )
        selected_records: list[Mapping[str, Any]] = []
        relation_paths: list[str] = []
        for target in targets:
            for bridge in self.by_stage[bridge_stage]:
                if bridge["id"] == target["id"]:
                    continue
                bridge_path = _eval_allowed_relation_path(
                    bridge["value"],
                    target["id"],
                    paths=("/evidence_ids",),
                )
                bridge_paths = [bridge_path] if bridge_path else []
                if not bridge_paths:
                    continue
                for source in self.by_stage[source_stage]:
                    if len({source["id"], bridge["id"], target["id"]}) != 3:
                        continue
                    source_path = _eval_allowed_relation_path(
                        source["value"],
                        bridge["id"],
                        paths=("/allowed_by_ids",),
                    )
                    source_paths = [source_path] if source_path else []
                    if not source_paths:
                        continue
                    try:
                        for record in (source, bridge, target):
                            select_story_path(record["value"])
                    except ProposalEvidenceError:
                        continue
                    selected_records = [source, bridge, target]
                    relation_paths = [source_paths[0], bridge_paths[0]]
                    break
                if selected_records:
                    break
            if selected_records:
                break
        if not selected_records:
            raise ProposalEvidenceError(
                "Q1_PROPOSAL_CHAIN_MISSING: T1->E1->W1"
            )

        evidence_ids = [record["id"] for record in selected_records]
        check["evidence_ids"] = evidence_ids
        evidence_objects = []
        for position, record in enumerate(selected_records):
            paths = [select_story_path(record["value"])]
            if position < len(relation_paths):
                paths.append(relation_paths[position])
            paths = list(dict.fromkeys(paths))
            evidence_objects.append(
                {
                    "id": record["id"],
                    "stage": record["stage"],
                    "kind": record["kind"],
                    "value_sha256": record["value_sha256"],
                    "projections": [
                        {
                            "path": path,
                            "value_sha256": runtime.canonical_sha256(
                                _eval_pointer_value(record["value"], path)
                            ),
                        }
                        for path in paths
                    ],
                }
            )
        check["conclusion"] = (
            f"{check['id']}: "
            f"{_eval_pointer_value(selected_records[0]['value'], select_story_path(selected_records[0]['value']))}"
        )
        binding = {
            "check_id": check["id"],
            "scope": check["scope"],
            "evidence_objects": evidence_objects,
            "assertion": {
                "predicate": predicate,
                "subject_id": evidence_ids[0],
                "target_id": evidence_ids[-1],
                "challenge_operator": operator,
                "result": check["result"],
            },
        }
        digest = runtime.canonical_sha256(binding)
        binding["assertion_sha256"] = digest
        check["method"] = f"story-assertion:{digest}"
        return binding

    def semantic_payloads(self) -> dict[str, dict[str, Any]]:
        plan = {
            "review_plan": {
                "domain_scopes": list(q1.UPSTREAM_STAGES),
                "cross_domain_dimensions": [
                    "coverage",
                    "causality",
                    "information",
                    "authority",
                ],
                "evidence_strategy": "fingerprint frozen story objects",
                "challenge_strategy": "break one concrete dependency at a time",
                "object_fingerprints": [
                    {
                        "id": self._record(stage)["id"],
                        "stage": stage,
                        "value_sha256": self._record(stage)["value_sha256"],
                    }
                    for stage in q1.STAGE_CANONICAL
                ],
            }
        }
        domain = {
            "domain_reviews": [
                self._check(f"CHK-{stage}", stage)
                for stage in q1.UPSTREAM_STAGES
            ],
            "reality_claim_review": [
                self._check("CHK-REALITY", "reality")
            ],
            "coverage_recalculation": [
                self._check("CHK-COVERAGE", "coverage")
            ],
            "causal_challenges": [
                self._check("CHK-CAUSE", "causality")
            ],
            "easy_solution_challenges": [
                self._check("CHK-EASY", "easy-solution")
            ],
        }
        domain_bindings = []
        for check in domain["domain_reviews"]:
            selector = {
                "T1": _eval_t1_story_path,
                "C1": _eval_c1_story_path,
            }.get(check["scope"])
            domain_bindings.append(
                self._bind(
                    check,
                    stages=[check["scope"]],
                    predicate="domain-contract",
                    operator="challenge-domain",
                    story_path_selector=selector,
                )
            )
        domain_bindings.extend(
            [
                self._bind(
                    domain["reality_claim_review"][0],
                    stages=["W1"],
                    predicate="reality-claim",
                    operator="verify-reality",
                ),
                self._bind(
                    domain["coverage_recalculation"][0],
                    stages=["T1"],
                    predicate="covers",
                    operator="recompute-coverage",
                    target_stage="S1",
                    story_path_selector=_eval_coverage_story_path,
                    relation_path_selector=lambda value, identifier: (
                        _eval_allowed_relation_path(
                            value,
                            identifier,
                            paths=("/source_ids",),
                        )
                    ),
                ),
                self._bind(
                    domain["causal_challenges"][0],
                    stages=["T1", "C1"],
                    predicate="causal-dependency",
                    operator="break-cause",
                    target_stage="T1",
                    story_path_selector=_eval_causal_story_path,
                ),
                self._bind(
                    domain["easy_solution_challenges"][0],
                    stages=["W1"],
                    predicate="counterfactual-pressure",
                    operator="remove-convenience",
                    target_stage="W1",
                    story_path_selector=_eval_easy_story_path,
                    relation_path_selector=lambda value, identifier: (
                        _eval_allowed_relation_path(
                            value,
                            identifier,
                            paths=("/impact_ids",),
                        )
                    ),
                ),
            ]
        )
        domain["assertion_bindings"] = domain_bindings

        cross = {
            "cross_domain_checks": [
                self._check("CHK-CROSS", "cross-domain")
            ],
            "consistency_matrix": [
                self._check("CHK-CONSISTENCY", "consistency")
            ],
        }
        cross["assertion_bindings"] = [
            self._bind(
                cross["cross_domain_checks"][0],
                stages=["T1"],
                predicate="cross-domain-reference",
                operator="compare-domains",
                target_stage="S1",
                cross_stage=True,
                story_path_selector=_eval_cross_story_path,
                relation_path_selector=lambda value, identifier: (
                    _eval_allowed_relation_path(
                        value,
                        identifier,
                        paths=("/source_ids",),
                    )
                ),
            ),
            self._bind_chain(
                cross["consistency_matrix"][0],
                stage_path=("T1", "E1", "W1"),
                predicate="consistent-with",
                operator="compare-semantics",
                preferred_target_kind="world-fact",
                story_path_selector=_eval_consistency_story_path,
            ),
        ]
        return {
            "review-plan": plan,
            "domain-challenges": domain,
            "cross-domain-challenges": cross,
        }

    def handoff_payload(
        self,
        *,
        allowlist: list[dict[str, str]],
    ) -> dict[str, Any]:
        specs = [
            ("HANDOFF-SUBJECT", "story_subject", ["B0"], "story-subject", "reconstruct-subject", None, None),
            ("HANDOFF-TRACE", "storyline_trace", ["T1"], "storyline-event-trace", "trace-development", "S1", None),
            ("HANDOFF-EVENT", "event_conditions", ["T1"], "event-condition", "locate-preconditions", "E1", None),
            ("HANDOFF-CHOICE", "character_choices", ["C1"], "character-choice", "explain-choice", "T1", None),
            ("HANDOFF-FREEDOM", "development_freedoms", ["C1"], "development-boundary", "locate-freedom", None, "development-freedom"),
        ]
        checks = [self._check(identifier, scope) for identifier, scope, *_ in specs]
        typed = {
            "storyline_trace": (
                _eval_coverage_story_path,
                lambda value, identifier: _eval_allowed_relation_path(
                    value, identifier, paths=("/source_ids",)
                ),
            ),
            "event_conditions": (
                _eval_handoff_event_story_path,
                lambda value, identifier: _eval_allowed_relation_path(
                    value, identifier, paths=("/allowed_by_ids",)
                ),
            ),
            "character_choices": (
                _eval_handoff_choice_story_path,
                lambda value, identifier: _eval_allowed_relation_path(
                    value, identifier, paths=("/event_ids",)
                ),
            ),
        }
        bindings = []
        for check, (
            _,
            scope,
            stages,
            predicate,
            operator,
            target,
            source_kind,
        ) in zip(checks, specs):
            story_selector, relation_selector = typed.get(
                scope, (None, None)
            )
            bindings.append(
                self._bind(
                check,
                stages=stages,
                predicate=predicate,
                operator=operator,
                target_stage=target,
                source_kind=source_kind,
                cross_stage=scope
                in {"storyline_trace", "event_conditions", "character_choices"},
                    story_path_selector=story_selector,
                    relation_path_selector=relation_selector,
                )
            )
        evidence_ids = list(
            dict.fromkeys(
                evidence_id
                for check in checks
                for evidence_id in check["evidence_ids"]
            )
        )
        return {
            "development_usability_test": {
                "id": "HANDOFF-1",
                "tested_tasks": [
                    "restatement",
                    "storyline trace",
                    "event condition lookup",
                    "character choice explanation",
                    "development freedom identification",
                ],
                "evidence_ids": evidence_ids,
                "conclusion": "All five development tasks resolve through frozen story objects.",
                "result": "pass",
            },
            "read_set": [item["path"] for item in allowlist],
            "responses": {
                "story_subject": "The frozen B0 control defines the subject.",
                "storyline_trace": "S1 responsibility is traceable to a T1 event.",
                "event_conditions": "W1 rules constrain the selected T1 event.",
                "character_choices": "The T1 event is assigned to a C1 agent.",
                "development_freedoms": "C1 DEV contracts preserve explicit development choices.",
            },
            "handoff_checks": checks,
            "assertion_bindings": bindings,
        }

    def final_review(
        self,
        *,
        run_id: str,
        input_gate: Mapping[str, str],
        semantic_payloads: Mapping[str, Mapping[str, Any]],
        development_usability_test: Mapping[str, Any],
        handoff_evidence: Mapping[str, str],
        semantic_task_id: str,
        handoff_task_id: str,
        handoff_allowlist: list[dict[str, str]],
    ) -> dict[str, Any]:
        domain = semantic_payloads["domain-challenges"]
        cross = semantic_payloads["cross-domain-challenges"]
        return {
            "schema_version": "2.0",
            "skill": "novel-conception-reviewer",
            "stage": "Q1",
            "run_id": run_id,
            "status": "ready",
            "input_gate": copy.deepcopy(dict(input_gate)),
            **{
                key: copy.deepcopy(value)
                for key, value in domain.items()
                if key != "assertion_bindings"
            },
            **{
                key: copy.deepcopy(value)
                for key, value in cross.items()
                if key != "assertion_bindings"
            },
            "development_usability_test": copy.deepcopy(
                dict(development_usability_test)
            ),
            "handoff_test_evidence": copy.deepcopy(dict(handoff_evidence)),
            "task_isolation": {
                "semantic_task_id": semantic_task_id,
                "handoff_task_id": handoff_task_id,
                "handoff_allowlist": copy.deepcopy(handoff_allowlist),
                "forbidden_reads": list(q1.FORBIDDEN_HANDOFF_READS),
            },
            "findings": [],
            "return_request": None,
            "verdict": "ready",
        }
