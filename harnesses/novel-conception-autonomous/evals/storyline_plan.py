"""Read-only contracts for evaluation-owned S1 storyline proposal plans.

The loader deliberately does not discover a plan beside a fixture.  One
explicit case manifest binds the fixture, plan, and authoritative plan schema
by repository-relative path and exact byte hash.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVALS_ROOT = Path(__file__).resolve().parent
MANIFEST_SCHEMA_PATH = (
    EVALS_ROOT / "schemas" / "eval-case-manifest.v1.schema.json"
)
PLAN_SCHEMA_REPOSITORY_PATH = "schemas/storyline-plan.v1.schema.json"
TRUSTED_SCHEMA_SHA256 = {
    "eval-case-manifest.v1.schema.json": (
        "45d8e313249e1b1b3f5ef83946ea1eccce4cae808994ae65dd6c0499f8ce3783"
    ),
    "storyline-plan.v1.schema.json": (
        "737982217abc975f9a0dac5cb36b41bdff24d13d1af06956c19ceedc653d0983"
    ),
}
EXPECTED_OWNERSHIP = {
    "owner": "eval_harness",
    "authority": "eval_owned_autonomous_proposal",
    "author_authority": False,
    "usage": "S1_phase_payload_only",
}
CONSISTENCY_DIMENSIONS = frozenset(
    {"time", "causality", "information", "authority", "state", "theme"}
)
DOWNSTREAM_STAGES = ("W1", "E1", "T1", "C1")


class StorylinePlanError(ValueError):
    """A manifest, fixture binding, or storyline relation is invalid."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class ValidatedStorylineCase:
    """A hash-verified evaluation case; mappings are defensive copies."""

    manifest_path: Path
    manifest_schema_path: Path
    manifest_sha256: str
    manifest_schema_sha256: str
    manifest: dict[str, Any]
    fixture_path: Path
    fixture: dict[str, Any]
    plan_path: Path
    plan: dict[str, Any]
    plan_schema_path: Path
    validation: dict[str, Any]


@dataclass(frozen=True)
class JsonObjectSnapshot:
    """One exact read used for identity, strict parsing, and validation."""

    path: Path
    sha256: str
    value: dict[str, Any]


class _DuplicateJsonKey(ValueError):
    pass


def _fail(code: str, message: str) -> None:
    raise StorylinePlanError(code, message)


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        _fail(code, message)


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise _DuplicateJsonKey(key)
        output[key] = value
    return output


def _parse_object_bytes(
    raw: bytes,
    path: Path,
    code: str,
) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_pairs,
        )
    except (UnicodeError, json.JSONDecodeError, _DuplicateJsonKey) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path}: JSON root must be an object")
    return value


def _read_json_snapshot(
    path: Path,
    code: str,
    *,
    expected_sha256: str | None = None,
    hash_code: str = "STORYLINE_PLAN_REFERENCE_INVALID",
) -> JsonObjectSnapshot:
    """Read once, then hash and parse only those captured bytes."""

    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(code, f"{path}: {error}")
    actual = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        _fail(
            hash_code,
            (
                f"{path}: expected {expected_sha256}, got {actual}"
            ),
        )
    return JsonObjectSnapshot(
        path=path,
        sha256=actual,
        value=_parse_object_bytes(raw, path, code),
    )


def _read_object(path: Path, code: str) -> dict[str, Any]:
    return _read_json_snapshot(path, code).value


def _validate_schema(
    value: Mapping[str, Any],
    schema_path: Path,
    *,
    expected_id: str,
    code: str,
    schema_snapshot: Mapping[str, Any] | None = None,
) -> None:
    schema = (
        dict(schema_snapshot)
        if schema_snapshot is not None
        else _read_object(schema_path, f"{code}_SCHEMA_UNREADABLE")
    )
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("$id") != expected_id
    ):
        _fail(code, f"{schema_path}: unexpected Draft or $id")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        _fail(code, f"{schema_path}: invalid schema: {error.message}")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: (
            tuple(str(part) for part in item.absolute_path),
            item.message,
        ),
    )
    if errors:
        first = errors[0]
        location = "$" + "".join(
            f"[{part!r}]" for part in first.absolute_path
        )
        _fail(code, f"{location}: {first.message}")


def _inside(path: Path, root: Path, code: str) -> Path:
    lexical_root = Path(root).absolute()
    lexical_path = Path(path).absolute()
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError as error:
        raise StorylinePlanError(code, str(lexical_path)) from error
    current = lexical_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            _fail(code, f"symbolic links are not accepted: {current}")
    try:
        resolved_root = lexical_root.resolve(strict=True)
        resolved = lexical_path.resolve(strict=True)
    except OSError as error:
        raise StorylinePlanError(code, str(lexical_path)) from error
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise StorylinePlanError(code, str(resolved)) from error
    return resolved


def _verified_reference(
    reference: Mapping[str, Any],
    *,
    evals_root: Path,
    repository_root: Path,
    label: str,
) -> Path:
    return _verified_reference_snapshot(
        reference,
        evals_root=evals_root,
        repository_root=repository_root,
        label=label,
    ).path


def _verified_reference_snapshot(
    reference: Mapping[str, Any],
    *,
    evals_root: Path,
    repository_root: Path,
    label: str,
) -> JsonObjectSnapshot:
    if set(reference) != {"path", "sha256"}:
        _fail(
            "STORYLINE_PLAN_REFERENCE_INVALID",
            f"{label}: reference must contain exactly path and sha256",
        )
    reference_path = reference.get("path")
    expected_sha256 = reference.get("sha256")
    if (
        not isinstance(reference_path, str)
        or not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
    ):
        _fail(
            "STORYLINE_PLAN_REFERENCE_INVALID",
            f"{label}: malformed path or sha256",
        )
    _inside(
        evals_root.joinpath(*reference_path.split("/")),
        evals_root,
        "STORYLINE_PLAN_REFERENCE_SYMLINK_INVALID",
    )
    try:
        path = rt.resolve_artifact_path(reference_path, root=evals_root)
    except Exception as error:
        _fail("STORYLINE_PLAN_REFERENCE_INVALID", f"{label}: {error}")
    path = _inside(
        path,
        evals_root,
        "STORYLINE_PLAN_REFERENCE_SYMLINK_INVALID",
    )
    _inside(path, repository_root, "STORYLINE_PLAN_PATH_OUTSIDE_REPOSITORY")
    if not path.is_file():
        _fail(
            "STORYLINE_PLAN_REFERENCE_INVALID",
            f"{label}: referenced artifact is missing",
        )
    return _read_json_snapshot(
        path,
        f"STORYLINE_PLAN_{label.upper()}_UNREADABLE",
        expected_sha256=expected_sha256,
    )


def _control_authority(control: Mapping[str, Any]) -> str:
    authority = control.get("authority")
    if isinstance(authority, str) and authority:
        return authority
    return (
        "author_open"
        if control.get("hardness") == "author_open"
        else "author_locked"
    )


def _anchor_assurance(
    anchor: Mapping[str, Any],
    controls: Mapping[str, Mapping[str, Any]],
) -> str:
    assurance = anchor.get("assurance")
    if isinstance(assurance, str) and assurance:
        return assurance
    required_status = anchor.get("required_status")
    if required_status == "author_open":
        return "author_open"
    source_ids = anchor.get("required_source_ids", [])
    authorities = {
        _control_authority(controls[source_id])
        for source_id in source_ids
        if source_id in controls
    }
    if "author_open" in authorities:
        return "author_open"
    if "author_locked_correction" in authorities:
        return "author_locked_correction"
    return "author_locked"


def control_inventory(fixture: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return the canonical control inventory bound by a plan."""

    interviews = fixture.get("interviews")
    if not isinstance(interviews, list) or not interviews:
        _fail("STORYLINE_PLAN_FIXTURE_INVALID", "interviews are required")
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in interviews:
        if not isinstance(item, Mapping):
            _fail("STORYLINE_PLAN_FIXTURE_INVALID", "interview is not an object")
        control_id = item.get("control_id")
        hardness = item.get("hardness")
        heading = item.get("heading")
        if (
            not isinstance(control_id, str)
            or not control_id
            or control_id in seen
            or hardness not in {"author_locked", "author_open"}
            or not isinstance(heading, str)
            or not heading
            or "value" not in item
        ):
            _fail(
                "STORYLINE_PLAN_FIXTURE_INVALID",
                f"invalid or duplicate control: {control_id!r}",
            )
        authority = _control_authority(item)
        if (
            hardness == "author_open"
            and authority != "author_open"
        ) or (
            hardness == "author_locked"
            and authority
            not in {"author_locked", "author_locked_correction"}
        ):
            _fail(
                "STORYLINE_PLAN_FIXTURE_AUTHORITY_INVALID",
                f"{control_id}: {hardness}/{authority}",
            )
        seen.add(control_id)
        output.append(
            {
                "control_id": control_id,
                "hardness": hardness,
                "authority": authority,
                "heading_sha256": rt.canonical_sha256(heading),
                "value_sha256": rt.canonical_sha256(item["value"]),
            }
        )
    output.sort(key=lambda item: item["control_id"])
    return output


def anchor_inventory(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return normalized semantic-anchor identity and assurance bindings."""

    controls_list = fixture.get("interviews")
    anchors = fixture.get("semantic_assertions")
    if not isinstance(controls_list, list) or not isinstance(anchors, list) or not anchors:
        _fail(
            "STORYLINE_PLAN_FIXTURE_INVALID",
            "interviews and semantic_assertions are required",
        )
    controls = {
        str(item.get("control_id")): item
        for item in controls_list
        if isinstance(item, Mapping)
    }
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for anchor in anchors:
        if not isinstance(anchor, Mapping):
            _fail("STORYLINE_PLAN_FIXTURE_INVALID", "anchor is not an object")
        anchor_id = anchor.get("anchor_id")
        sources = anchor.get("required_source_ids")
        terms = anchor.get("required_terms", [])
        if (
            not isinstance(anchor_id, str)
            or not anchor_id
            or anchor_id in seen
            or not isinstance(sources, list)
            or not sources
            or any(not isinstance(item, str) or item not in controls for item in sources)
            or len(sources) != len(set(sources))
            or not isinstance(terms, list)
            or any(not isinstance(item, str) or not item for item in terms)
        ):
            _fail(
                "STORYLINE_PLAN_FIXTURE_INVALID",
                f"invalid or duplicate anchor: {anchor_id!r}",
            )
        assurance = _anchor_assurance(anchor, controls)
        source_authorities = {
            _control_authority(controls[source_id])
            for source_id in sources
        }
        if (
            "author_open" in source_authorities
            and assurance != "author_open"
        ) or (
            assurance == "author_open"
            and "author_open" not in source_authorities
        ) or (
            "author_locked_correction" in source_authorities
            and assurance
            not in {"author_locked_correction", "derived_unsealed"}
        ):
            _fail(
                "STORYLINE_PLAN_FIXTURE_AUTHORITY_INVALID",
                f"{anchor_id}: {assurance}/{sorted(source_authorities)}",
            )
        seen.add(anchor_id)
        output.append(
            {
                "anchor_id": anchor_id,
                "required_source_ids": sorted(sources),
                "assurance": assurance,
                "required_terms_sha256": rt.canonical_sha256(terms),
            }
        )
    output.sort(key=lambda item: item["anchor_id"])
    return output


def _unique_by_id(
    values: Sequence[Mapping[str, Any]],
    *,
    label: str,
) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for item in values:
        identifier = item["id"]
        if identifier in output:
            _fail("STORYLINE_PLAN_ID_DUPLICATE", f"{label}: {identifier}")
        output[identifier] = item
    return output


def _register_ids(
    registry: dict[str, tuple[str, Mapping[str, Any]]],
    values: Sequence[Mapping[str, Any]],
    *,
    label: str,
) -> None:
    for item in values:
        identifier = item["id"]
        if identifier in registry:
            _fail(
                "STORYLINE_PLAN_ID_DUPLICATE",
                f"{identifier}: {registry[identifier][0]}/{label}",
            )
        registry[identifier] = (label, item)


def _register_identifier(
    registry: dict[str, tuple[str, Mapping[str, Any]]],
    identifier: str,
    value: Mapping[str, Any],
    *,
    label: str,
) -> None:
    if identifier in registry:
        _fail(
            "STORYLINE_PLAN_ID_DUPLICATE",
            f"{identifier}: {registry[identifier][0]}/{label}",
        )
    registry[identifier] = (label, value)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else rt.canonical_json(value)


def validate_storyline_plan(
    plan: Mapping[str, Any],
    fixture: Mapping[str, Any],
    *,
    fixture_reference: Mapping[str, str],
) -> dict[str, Any]:
    """Validate every cross-object and authority relation in a plan."""

    controls_inventory = control_inventory(fixture)
    anchors_inventory = anchor_inventory(fixture)
    controls = {
        str(item["control_id"]): item
        for item in fixture["interviews"]
    }
    anchors = {
        str(item["anchor_id"]): item
        for item in fixture["semantic_assertions"]
    }
    binding = plan["fixture_binding"]
    expected_binding = {
        "fixture": dict(fixture_reference),
        "fixture_id": fixture.get("fixture_id"),
        "run_id": fixture.get("run_id"),
        "control_inventory_sha256": rt.canonical_sha256(controls_inventory),
        "anchor_inventory_sha256": rt.canonical_sha256(anchors_inventory),
    }
    _require(
        binding == expected_binding,
        "STORYLINE_PLAN_FIXTURE_BINDING_MISMATCH",
        "fixture identity or normalized inventories differ",
    )
    _require(
        plan["ownership"] == EXPECTED_OWNERSHIP,
        "STORYLINE_PLAN_OWNERSHIP_INVALID",
        "ownership must remain evaluation-owned and non-authoritative",
    )

    decisions = _unique_by_id(plan["design_decisions"], label="decision")
    demands = _unique_by_id(plan["demands"], label="demand")
    lines = _unique_by_id(plan["lines"], label="line")
    connections = _unique_by_id(plan["connections"], label="connection")
    anchor_bindings = _unique_by_id(
        plan["anchor_bindings"], label="anchor binding"
    )
    consistency = _unique_by_id(
        plan["consistency_evidence"], label="consistency"
    )
    open_treatments = _unique_by_id(
        plan["open_control_treatments"], label="open treatment"
    )
    states: dict[str, Mapping[str, Any]] = {}
    state_owner: dict[str, str] = {}
    for line in lines.values():
        for state in line["states"]:
            state_id = state["id"]
            if state_id in states:
                _fail("STORYLINE_PLAN_ID_DUPLICATE", f"state: {state_id}")
            states[state_id] = state
            state_owner[state_id] = line["id"]

    registry: dict[str, tuple[str, Mapping[str, Any]]] = {}
    _register_identifier(
        registry, plan["plan_id"], plan, label="plan"
    )
    _register_ids(registry, list(decisions.values()), label="decision")
    _register_ids(registry, list(demands.values()), label="demand")
    _register_ids(registry, list(lines.values()), label="line")
    _register_ids(registry, list(states.values()), label="state")
    _register_ids(registry, list(connections.values()), label="connection")
    _register_ids(registry, [plan["architecture"]], label="architecture")
    _register_ids(
        registry, list(anchor_bindings.values()), label="anchor binding"
    )
    _register_ids(registry, list(consistency.values()), label="consistency")
    _register_ids(
        registry, list(open_treatments.values()), label="open treatment"
    )
    downstream_by_stage: dict[str, dict[str, Mapping[str, Any]]] = {}
    for stage in DOWNSTREAM_STAGES:
        indexed = _unique_by_id(
            plan["downstream_requirements"][stage],
            label=f"{stage} requirement",
        )
        downstream_by_stage[stage] = indexed
        _register_ids(
            registry, list(indexed.values()), label=f"{stage} requirement"
        )
    fixture_ids = {str(fixture["fixture_id"])}
    collisions = sorted(
        set(registry) & (fixture_ids | set(controls) | set(anchors))
    )
    _require(
        not collisions,
        "STORYLINE_PLAN_ID_COLLISION",
        f"plan IDs collide with fixture/control/anchor IDs: {collisions}",
    )

    demand_sources = [item["source_control_id"] for item in demands.values()]
    _require(
        set(demand_sources) == set(controls)
        and len(demand_sources) == len(set(demand_sources)),
        "STORYLINE_PLAN_DEMAND_COVERAGE_MISMATCH",
        "fixture controls and demands must be one-to-one",
    )
    for demand in demands.values():
        if demand["disposition"] == "not_applicable":
            _fail(
                "STORYLINE_PLAN_NOT_APPLICABLE_UNSUPPORTED",
                demand["id"],
            )
        _require(
            len(demand["realization_line_ids"]) == 1
            and demand["realization_line_ids"][0] in lines,
            "STORYLINE_PLAN_DEMAND_REALIZATION_INVALID",
            demand["id"],
        )
        source = controls[demand["source_control_id"]]
        _require(
            source["heading"] in demand["obligation"]
            and _text(source["value"]) in demand["obligation"],
            "STORYLINE_PLAN_CONTROL_MEANING_UNBOUND",
            demand["id"],
        )

    realized: list[str] = []
    for line in lines.values():
        phases = [state["phase"] for state in line["states"]]
        _require(
            phases[0] == "start"
            and phases[-1] == "end"
            and all(phase == "change" for phase in phases[1:-1]),
            "STORYLINE_PLAN_STATE_SEQUENCE_INVALID",
            line["id"],
        )
        for demand_id in line["demand_ids"]:
            _require(
                demand_id in demands,
                "STORYLINE_PLAN_LINE_DEMAND_INVALID",
                f"{line['id']}: {demand_id}",
            )
            realized.append(demand_id)
            demand = demands[demand_id]
            _require(
                demand["realization_line_ids"] == [line["id"]],
                "STORYLINE_PLAN_DEMAND_REALIZATION_INVALID",
                demand_id,
            )
            disposition = demand["disposition"]
            if disposition == "independent_line":
                _require(
                    line["type"] != "main" and len(line["demand_ids"]) == 1,
                    "STORYLINE_PLAN_DISPOSITION_MISMATCH",
                    demand_id,
                )
            elif disposition == "merged":
                _require(
                    len(line["demand_ids"]) >= 2,
                    "STORYLINE_PLAN_DISPOSITION_MISMATCH",
                    demand_id,
                )
            elif disposition == "background_pressure":
                _require(
                    line["type"] == "background",
                    "STORYLINE_PLAN_DISPOSITION_MISMATCH",
                    demand_id,
                )
            elif disposition == "optional_melody":
                _require(
                    line["type"] == "optional_melody",
                    "STORYLINE_PLAN_DISPOSITION_MISMATCH",
                    demand_id,
                )
        for decision_id in line["decision_ids"]:
            _require(
                decision_id in decisions,
                "STORYLINE_PLAN_DECISION_REFERENCE_INVALID",
                f"{line['id']}: {decision_id}",
            )
    _require(
        set(realized) == set(demands) and len(realized) == len(set(realized)),
        "STORYLINE_PLAN_DEMAND_COVERAGE_MISMATCH",
        "every demand must be assigned to exactly one line",
    )

    mains = [item["id"] for item in lines.values() if item["type"] == "main"]
    _require(
        len(mains) == 1,
        "STORYLINE_PLAN_MAIN_INVALID",
        f"expected one main line, got {mains}",
    )
    structural_ids = {
        line_id
        for line_id, line in lines.items()
        if line["type"] != "optional_melody"
    }
    incident: dict[str, set[str]] = {line_id: set() for line_id in lines}
    causal_outgoing: dict[str, set[str]] = {
        line_id: set() for line_id in structural_ids
    }
    causal_incoming: dict[str, set[str]] = {
        line_id: set() for line_id in structural_ids
    }
    for connection in connections.values():
        source_id = connection["from_line_id"]
        target_id = connection["to_line_id"]
        _require(
            source_id in lines and target_id in lines and source_id != target_id,
            "STORYLINE_PLAN_CONNECTION_DANGLING",
            connection["id"],
        )
        _require(
            state_owner.get(connection["from_state_id"]) == source_id
            and state_owner.get(connection["to_state_id"]) == target_id,
            "STORYLINE_PLAN_CONNECTION_STATE_INVALID",
            connection["id"],
        )
        incident[source_id].add(connection["id"])
        incident[target_id].add(connection["id"])
        if connection["relation"] == "causal":
            _require(
                source_id in structural_ids and target_id in structural_ids,
                "STORYLINE_PLAN_OPTIONAL_CAUSAL_LINK_FORBIDDEN",
                connection["id"],
            )
            causal_outgoing[source_id].add(target_id)
            causal_incoming[target_id].add(source_id)
    for line_id, line in lines.items():
        _require(
            set(line["connection_ids"]) == incident[line_id],
            "STORYLINE_PLAN_CONNECTION_RECIPROCAL_MISMATCH",
            line_id,
        )
        if line["type"] == "optional_melody":
            _require(
                any(
                    connection["id"] in incident[line_id]
                    and connection["relation"] == "associative"
                    and (
                        connection["from_line_id"] in structural_ids
                        or connection["to_line_id"] in structural_ids
                    )
                    for connection in connections.values()
                ),
                "STORYLINE_PLAN_OPTIONAL_ASSOCIATION_MISSING",
                line_id,
            )
        elif line_id != mains[0]:
            frontier = [line_id]
            visited: set[str] = set()
            while frontier:
                current = frontier.pop()
                if current in visited:
                    continue
                visited.add(current)
                frontier.extend(
                    sorted(causal_outgoing[current] - visited)
                )
            _require(
                mains[0] in visited,
                "STORYLINE_PLAN_STRUCTURAL_CAUSAL_CLOSURE_MISSING",
                line_id,
            )

    architecture = plan["architecture"]
    _require(
        architecture["main_line_id"] == mains[0],
        "STORYLINE_PLAN_ARCHITECTURE_INVALID",
        "main_line_id differs from the main line",
    )
    _require(
        set(architecture["line_order"]) == set(lines)
        and len(architecture["line_order"]) == len(lines),
        "STORYLINE_PLAN_ARCHITECTURE_INVALID",
        "line_order must contain every line exactly once",
    )
    line_positions = {
        line_id: index
        for index, line_id in enumerate(architecture["line_order"])
    }
    for connection in connections.values():
        if connection["relation"] == "causal":
            _require(
                line_positions[connection["from_line_id"]]
                < line_positions[connection["to_line_id"]],
                "STORYLINE_PLAN_ARCHITECTURE_INVALID",
                (
                    "line_order is not topological for causal connection "
                    f"{connection['id']}"
                ),
            )
    for line_id in architecture["entry_line_ids"]:
        _require(
            line_id in structural_ids and not causal_incoming[line_id],
            "STORYLINE_PLAN_ARCHITECTURE_INVALID",
            f"entry line has an incoming connection: {line_id}",
        )
    for line_id in architecture["terminal_line_ids"]:
        _require(
            line_id in structural_ids and not causal_outgoing[line_id],
            "STORYLINE_PLAN_ARCHITECTURE_INVALID",
            f"terminal line has an outgoing connection: {line_id}",
        )
    _require(
        set(architecture["entry_line_ids"])
        == {
            line_id
            for line_id in structural_ids
            if not causal_incoming[line_id]
        }
        and set(architecture["terminal_line_ids"])
        == {
            line_id
            for line_id in structural_ids
            if not causal_outgoing[line_id]
        },
        "STORYLINE_PLAN_ARCHITECTURE_INVALID",
        (
            "entry and terminal sets must exactly match structural causal "
            "roots and leaves"
        ),
    )

    semantic_targets = {
        identifier: value
        for identifier, (kind, value) in registry.items()
        if kind
        not in {"anchor binding", "consistency"}
    }
    anchor_sources = [
        item["semantic_anchor_id"] for item in anchor_bindings.values()
    ]
    _require(
        set(anchor_sources) == set(anchors)
        and len(anchor_sources) == len(set(anchor_sources)),
        "STORYLINE_PLAN_ANCHOR_COVERAGE_MISMATCH",
        "fixture anchors and bindings must be one-to-one",
    )
    controls_by_id = controls
    open_control_ids = {
        control_id
        for control_id, control in controls.items()
        if control["hardness"] == "author_open"
    }
    observed_open = [
        item["source_control_id"] for item in open_treatments.values()
    ]
    _require(
        set(observed_open) == open_control_ids
        and len(observed_open) == len(set(observed_open)),
        "STORYLINE_PLAN_OPEN_CONTROL_MISMATCH",
        "author-open controls must be preserved exactly once",
    )
    open_treatment_by_control = {
        item["source_control_id"]: item["id"]
        for item in open_treatments.values()
    }
    demand_by_control = {
        item["source_control_id"]: item for item in demands.values()
    }
    for control_id in open_control_ids:
        demand = demand_by_control[control_id]
        line_id = demand["realization_line_ids"][0]
        if lines[line_id]["type"] != "optional_melody":
            continue
        _require(
            not any(
                connection["relation"] == "causal"
                and connection["id"] in incident[line_id]
                for connection in connections.values()
            ),
            "STORYLINE_PLAN_AUTHOR_OPEN_OPTIONAL_CAUSAL",
            line_id,
        )
    for treatment in open_treatments.values():
        control = controls[treatment["source_control_id"]]
        _require(
            _text(control["value"]) in treatment["question"],
            "STORYLINE_PLAN_OPEN_CONTROL_RESOLVED",
            treatment["id"],
        )
        _require(
            all(
                target_id in semantic_targets
                for target_id in treatment["target_ids"]
            ),
            "STORYLINE_PLAN_OPEN_TARGET_INVALID",
            treatment["id"],
        )
    open_treatment_ids = set(open_treatments)
    assurance_by_anchor: dict[str, str] = {}
    for binding_item in anchor_bindings.values():
        anchor = anchors[binding_item["semantic_anchor_id"]]
        expected_sources = set(anchor["required_source_ids"])
        expected_assurance = _anchor_assurance(anchor, controls_by_id)
        assurance_by_anchor[binding_item["semantic_anchor_id"]] = (
            expected_assurance
        )
        _require(
            set(binding_item["source_control_ids"]) == expected_sources,
            "STORYLINE_PLAN_ANCHOR_SOURCE_MISMATCH",
            binding_item["id"],
        )
        _require(
            binding_item["assurance"] == expected_assurance,
            "STORYLINE_PLAN_ANCHOR_ASSURANCE_MISMATCH",
            binding_item["id"],
        )
        expected_treatment = {
            "author_locked": "locked_constraint",
            "author_locked_correction": "locked_constraint",
            "author_open": "preserved_open",
            "derived_unsealed": "reversible_hypothesis",
        }[expected_assurance]
        _require(
            binding_item["treatment"] == expected_treatment,
            "STORYLINE_PLAN_ANCHOR_AUTHORITY_VIOLATION",
            binding_item["id"],
        )
        expected_open_treatments = {
            open_treatment_by_control[source_id]
            for source_id in expected_sources
            if source_id in open_control_ids
        }
        targeted_open_treatments = (
            set(binding_item["target_ids"]) & open_treatment_ids
        )
        _require(
            targeted_open_treatments == expected_open_treatments,
            "STORYLINE_PLAN_ANCHOR_OPEN_TREATMENT_MISMATCH",
            (
                f"{binding_item['id']}: expected "
                f"{sorted(expected_open_treatments)}, got "
                f"{sorted(targeted_open_treatments)}"
            ),
        )
        _require(
            all(target_id in semantic_targets for target_id in binding_item["target_ids"]),
            "STORYLINE_PLAN_ANCHOR_TARGET_INVALID",
            binding_item["id"],
        )
        target_text = rt.canonical_json(
            [semantic_targets[target_id] for target_id in binding_item["target_ids"]]
        )
        for term in anchor.get("required_terms", []):
            _require(
                term in target_text,
                "STORYLINE_PLAN_ANCHOR_TERM_UNBOUND",
                f"{binding_item['id']}: {term}",
            )

    for decision in decisions.values():
        _require(
            decision["selection"] in decision["options"],
            "STORYLINE_PLAN_DECISION_SELECTION_INVALID",
            f"{decision['id']}: selection must be one declared option",
        )
        _require(
            set(decision["source_control_ids"]) <= set(controls),
            "STORYLINE_PLAN_DECISION_SOURCE_INVALID",
            decision["id"],
        )
        _require(
            not (
                set(decision["source_control_ids"]) & open_control_ids
            ),
            "STORYLINE_PLAN_OPEN_CONTROL_RESOLVED",
            decision["id"],
        )
        _require(
            set(decision["source_anchor_ids"]) <= set(anchors),
            "STORYLINE_PLAN_DECISION_SOURCE_INVALID",
            decision["id"],
        )
        _require(
            not any(
                assurance_by_anchor[anchor_id] == "author_open"
                for anchor_id in decision["source_anchor_ids"]
            ),
            "STORYLINE_PLAN_OPEN_CONTROL_RESOLVED",
            decision["id"],
        )
        _require(
            all(target_id in semantic_targets for target_id in decision["projection_ids"]),
            "STORYLINE_PLAN_DECISION_PROJECTION_INVALID",
            decision["id"],
        )
    for binding_item in anchor_bindings.values():
        if binding_item["assurance"] != "derived_unsealed":
            continue
        related = [
            decision
            for decision in decisions.values()
            if binding_item["semantic_anchor_id"] in decision["source_anchor_ids"]
            or bool(
                set(binding_item["target_ids"])
                & set(decision["projection_ids"])
            )
        ]
        _require(
            bool(related)
            and all(item["reversibility"] == "reversible" for item in related),
            "STORYLINE_PLAN_DERIVED_AUTHORITY_VIOLATION",
            binding_item["id"],
        )

    dimensions = [item["dimension"] for item in consistency.values()]
    _require(
        set(dimensions) == CONSISTENCY_DIMENSIONS
        and len(dimensions) == len(set(dimensions)),
        "STORYLINE_PLAN_CONSISTENCY_DIMENSIONS_MISMATCH",
        str(sorted(dimensions)),
    )
    line_ids = set(lines)
    anchor_binding_ids = set(anchor_bindings)
    allowed_witnesses = {
        "time": set(states) | set(connections) | line_ids,
        "causality": set(demands)
        | {
            connection_id
            for connection_id, connection in connections.items()
            if connection["relation"] == "causal"
        }
        | set(decisions)
        | line_ids,
        "information": set(states) | set(connections) | anchor_binding_ids,
        "authority": set(decisions) | anchor_binding_ids | open_treatment_ids,
        "state": set(states) | set(connections) | line_ids,
        "theme": set(demands) | {architecture["id"]} | anchor_binding_ids,
    }
    for evidence in consistency.values():
        _require(
            set(evidence["line_ids"]) == line_ids,
            "STORYLINE_PLAN_CONSISTENCY_LINE_COVERAGE_MISMATCH",
            evidence["id"],
        )
        _require(
            set(evidence["witness_ids"])
            <= allowed_witnesses[evidence["dimension"]],
            "STORYLINE_PLAN_CONSISTENCY_WITNESS_INVALID",
            evidence["id"],
        )

    prefix_by_stage = {
        "W1": "WR-",
        "E1": "END-",
        "T1": "EVD-",
        "C1": "CHD-",
    }
    for stage, requirements in downstream_by_stage.items():
        requirement_lines = [item["line_id"] for item in requirements.values()]
        _require(
            set(requirement_lines) == line_ids
            and len(requirement_lines) == len(set(requirement_lines)),
            "STORYLINE_PLAN_DOWNSTREAM_COVERAGE_MISMATCH",
            stage,
        )
        for requirement in requirements.values():
            line = lines[requirement["line_id"]]
            _require(
                requirement["target_stage"] == stage
                and requirement["id"].startswith(prefix_by_stage[stage])
                and requirement["demand_ids"] == line["demand_ids"],
                "STORYLINE_PLAN_DOWNSTREAM_BINDING_MISMATCH",
                requirement["id"],
            )

    return {
        "schema_version": "1.0",
        "status": "ready",
        "plan_id": plan["plan_id"],
        "fixture_id": fixture["fixture_id"],
        "run_id": fixture["run_id"],
        "control_count": len(controls),
        "anchor_count": len(anchors),
        "demand_count": len(demands),
        "line_count": len(lines),
        "connection_count": len(connections),
        "consistency_dimensions": sorted(CONSISTENCY_DIMENSIONS),
        "downstream_stages": list(DOWNSTREAM_STAGES),
    }


def load_eval_case(
    manifest_path: str | Path,
    *,
    repository_root: str | Path = REPOSITORY_ROOT,
    evals_root: str | Path = EVALS_ROOT,
) -> ValidatedStorylineCase:
    """Load one explicitly declared case without writing or sidecar discovery."""

    repository = Path(repository_root).resolve(strict=True)
    evals = _inside(
        Path(evals_root),
        repository,
        "STORYLINE_PLAN_EVALS_OUTSIDE_REPOSITORY",
    )
    manifest_file = _inside(
        Path(manifest_path),
        evals,
        "STORYLINE_PLAN_MANIFEST_OUTSIDE_EVALS",
    )
    manifest_snapshot = _read_json_snapshot(
        manifest_file, "STORYLINE_PLAN_MANIFEST_UNREADABLE"
    )
    manifest = manifest_snapshot.value
    manifest_schema = evals / "schemas" / MANIFEST_SCHEMA_PATH.name
    manifest_schema = _inside(
        manifest_schema,
        evals,
        "STORYLINE_PLAN_MANIFEST_SCHEMA_INVALID",
    )
    manifest_schema_snapshot = _read_json_snapshot(
        manifest_schema,
        "STORYLINE_PLAN_MANIFEST_SCHEMA_UNREADABLE",
        expected_sha256=TRUSTED_SCHEMA_SHA256[MANIFEST_SCHEMA_PATH.name],
        hash_code="STORYLINE_PLAN_MANIFEST_SCHEMA_UNTRUSTED",
    )
    _validate_schema(
        manifest,
        manifest_schema,
        expected_id=MANIFEST_SCHEMA_PATH.name,
        code="STORYLINE_PLAN_MANIFEST_SCHEMA_INVALID",
        schema_snapshot=manifest_schema_snapshot.value,
    )
    _require(
        manifest["storyline_plan_schema"]["path"]
        == PLAN_SCHEMA_REPOSITORY_PATH,
        "STORYLINE_PLAN_SCHEMA_REFERENCE_INVALID",
        "manifest must bind the authoritative v1 plan schema path",
    )
    _require(
        manifest["storyline_plan_schema"]["sha256"]
        == TRUSTED_SCHEMA_SHA256[Path(PLAN_SCHEMA_REPOSITORY_PATH).name],
        "STORYLINE_PLAN_SCHEMA_REFERENCE_INVALID",
        "manifest plan-schema hash must match the code-pinned identity",
    )
    fixture_snapshot = _verified_reference_snapshot(
        manifest["fixture"],
        evals_root=evals,
        repository_root=repository,
        label="fixture",
    )
    plan_snapshot = _verified_reference_snapshot(
        manifest["storyline_plan"],
        evals_root=evals,
        repository_root=repository,
        label="storyline_plan",
    )
    plan_schema_snapshot = _verified_reference_snapshot(
        manifest["storyline_plan_schema"],
        evals_root=evals,
        repository_root=repository,
        label="storyline_plan_schema",
    )
    fixture = fixture_snapshot.value
    plan = plan_snapshot.value
    _validate_schema(
        plan,
        plan_schema_snapshot.path,
        expected_id=Path(PLAN_SCHEMA_REPOSITORY_PATH).name,
        code="STORYLINE_PLAN_SCHEMA_INVALID",
        schema_snapshot=plan_schema_snapshot.value,
    )
    validation = validate_storyline_plan(
        plan,
        fixture,
        fixture_reference=manifest["fixture"],
    )
    return ValidatedStorylineCase(
        manifest_path=manifest_file,
        manifest_schema_path=manifest_schema,
        manifest_sha256=manifest_snapshot.sha256,
        manifest_schema_sha256=manifest_schema_snapshot.sha256,
        manifest=copy.deepcopy(manifest),
        fixture_path=fixture_snapshot.path,
        fixture=copy.deepcopy(fixture),
        plan_path=plan_snapshot.path,
        plan=copy.deepcopy(plan),
        plan_schema_path=plan_schema_snapshot.path,
        validation=copy.deepcopy(validation),
    )


__all__ = [
    "CONSISTENCY_DIMENSIONS",
    "DOWNSTREAM_STAGES",
    "StorylinePlanError",
    "ValidatedStorylineCase",
    "anchor_inventory",
    "control_inventory",
    "load_eval_case",
    "validate_storyline_plan",
]
