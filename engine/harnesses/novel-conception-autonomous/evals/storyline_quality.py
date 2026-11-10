"""Accountable, evaluation-only quality gate for storyline proposal plans.

The gate is deliberately smaller than Q1.  It first delegates all structural,
lineage, graph, and authority validation to ``storyline_plan.load_eval_case``.
It then verifies one explicitly supplied, non-authoritative review record.
It does not publish a stage package, completion, or author decision.
"""

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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
storyline_plan = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_plan"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVALS_ROOT = Path(__file__).resolve().parent
QUALITY_SCHEMA_REPOSITORY_PATH = (
    "schemas/storyline-proposal-quality-gate.v1.schema.json"
)
TRUSTED_QUALITY_SCHEMA_SHA256 = (
    "56fe7cdcfe33945ab4778d01f972d6e5efaf55991640ae1e3bdb3594323072de"
)
EXPECTED_OWNERSHIP = {
    "owner": "eval_harness",
    "authority": "non_authoritative_quality_evidence",
    "artifact_role": "not_completion",
}
REQUIRED_CHECKS = (
    "authority_preservation",
    "main_arc_completeness",
    "causal_topology",
    "role_clustering",
    "open_preservation",
    "optional_non_load_bearing",
    "non_placeholder_evidence",
    "downstream_usefulness",
)
_PLACEHOLDER = re.compile(
    r"(?i)(?:\b(?:tbd|todo|placeholder|lorem\s+ipsum|xxx)\b|"
    r"待定|未定义|占位)"
)


class StorylineQualityError(ValueError):
    """Stable fail-closed quality-gate error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class FormalValidatedStorylineQualityCase:
    """A complete manifest-only quality admission for formal S1 use."""

    structural_case: Any
    gate_path: Path
    gate_schema_path: Path
    gate_sha256: str
    gate_schema_sha256: str
    gate: dict[str, Any]
    validation: dict[str, Any]


@dataclass(frozen=True)
class CompatibilityValidatedStorylineQualityCase:
    """A path-checked compatibility result that is never formal evidence."""

    structural_case: Any
    gate_path: Path
    gate_schema_path: Path
    gate_sha256: str
    gate_schema_sha256: str
    gate: dict[str, Any]
    validation: dict[str, Any]


class _DuplicateJsonKey(ValueError):
    pass


def _fail(code: str, message: str) -> None:
    raise StorylineQualityError(code, message)


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


def _read_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_pairs,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJsonKey) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path}: JSON root must be an object")
    return value


def _inside(path: Path, root: Path, code: str) -> Path:
    lexical_root = Path(root).absolute()
    lexical_path = Path(path).absolute()
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError as error:
        raise StorylineQualityError(code, str(lexical_path)) from error
    current = lexical_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            _fail(code, f"symbolic links are not accepted: {current}")
    try:
        resolved_root = lexical_root.resolve(strict=True)
        resolved = lexical_path.resolve(strict=True)
    except OSError as error:
        raise StorylineQualityError(code, str(lexical_path)) from error
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise StorylineQualityError(code, str(resolved)) from error
    return resolved


def _validate_schema(
    value: Mapping[str, Any],
    schema_path: Path,
    *,
    schema_snapshot: Mapping[str, Any] | None = None,
) -> None:
    schema = (
        dict(schema_snapshot)
        if schema_snapshot is not None
        else _read_object(
            schema_path, "STORYLINE_QUALITY_SCHEMA_UNREADABLE"
        )
    )
    if (
        schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
        or schema.get("$id") != schema_path.name
    ):
        _fail(
            "STORYLINE_QUALITY_SCHEMA_INVALID",
            f"{schema_path}: unexpected Draft or $id",
        )
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        _fail(
            "STORYLINE_QUALITY_SCHEMA_INVALID",
            f"{schema_path}: {error.message}",
        )
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
        _fail(
            "STORYLINE_QUALITY_GATE_SCHEMA_INVALID",
            f"{location}: {first.message}",
        )


def _validate_trusted_gate_schema(
    value: Any,
    *,
    trusted_snapshot: Any | None = None,
) -> None:
    """Apply the code-pinned gate schema at every public validation entry."""

    schema_path = _inside(
        EVALS_ROOT.joinpath(*QUALITY_SCHEMA_REPOSITORY_PATH.split("/")),
        EVALS_ROOT,
        "STORYLINE_QUALITY_SCHEMA_INVALID",
    )
    snapshot = trusted_snapshot
    if snapshot is None:
        snapshot = storyline_plan._read_json_snapshot(
            schema_path,
            "STORYLINE_QUALITY_SCHEMA_UNREADABLE",
            expected_sha256=TRUSTED_QUALITY_SCHEMA_SHA256,
            hash_code="STORYLINE_QUALITY_SCHEMA_UNTRUSTED",
        )
    _require(
        snapshot.path.name == Path(QUALITY_SCHEMA_REPOSITORY_PATH).name
        and snapshot.sha256 == TRUSTED_QUALITY_SCHEMA_SHA256,
        "STORYLINE_QUALITY_SCHEMA_UNTRUSTED",
        "quality schema snapshot is not the fixed code-pinned artifact",
    )
    _validate_schema(
        value,
        snapshot.path,
        schema_snapshot=snapshot.value,
    )


def _quality_snapshot(
    path: Path,
    code: str,
    *,
    expected_sha256: str | None = None,
    hash_code: str = "STORYLINE_QUALITY_REFERENCE_INVALID",
) -> Any:
    try:
        return storyline_plan._read_json_snapshot(
            path,
            code,
            expected_sha256=expected_sha256,
            hash_code=hash_code,
        )
    except storyline_plan.StorylinePlanError as error:
        _fail(error.code, str(error).split(": ", 1)[-1])


def _register(
    registry: dict[str, str],
    identifier: Any,
    kind: str,
) -> None:
    if not isinstance(identifier, str) or not identifier:
        _fail("STORYLINE_QUALITY_TARGET_REGISTRY_INVALID", f"{kind}: {identifier!r}")
    if identifier in registry:
        _fail(
            "STORYLINE_QUALITY_TARGET_REGISTRY_INVALID",
            f"duplicate {identifier}: {registry[identifier]}/{kind}",
        )
    registry[identifier] = kind


def target_registry(structural_case: Any) -> dict[str, str]:
    """Return every fixture/plan object ID accepted as review evidence."""

    fixture = structural_case.fixture
    plan = structural_case.plan
    registry: dict[str, str] = {}
    _register(registry, fixture["fixture_id"], "fixture")
    for control in fixture["interviews"]:
        _register(registry, control["control_id"], "control")
    for anchor in fixture["semantic_assertions"]:
        _register(registry, anchor["anchor_id"], "semantic_anchor")
    _register(registry, plan["plan_id"], "plan")
    for field, kind in (
        ("design_decisions", "design_decision"),
        ("demands", "demand"),
        ("lines", "line"),
        ("connections", "connection"),
        ("anchor_bindings", "anchor_binding"),
        ("consistency_evidence", "consistency_evidence"),
        ("open_control_treatments", "open_control_treatment"),
    ):
        for item in plan[field]:
            _register(registry, item["id"], kind)
            if field == "lines":
                for state in item["states"]:
                    _register(registry, state["id"], "line_state")
    _register(registry, plan["architecture"]["id"], "architecture")
    for stage, requirements in plan["downstream_requirements"].items():
        for requirement in requirements:
            _register(registry, requirement["id"], f"{stage}_requirement")
    return registry


def _normalized_anchor_assurance(structural_case: Any) -> dict[str, str]:
    return {
        item["anchor_id"]: item["assurance"]
        for item in storyline_plan.anchor_inventory(
            structural_case.fixture
        )
    }


def expected_check_targets(
    structural_case: Any,
) -> dict[str, list[str]]:
    """Compute exact deterministic evidence coverage for all eight checks."""

    fixture = structural_case.fixture
    plan = structural_case.plan
    registry = target_registry(structural_case)
    controls = sorted(
        str(item["control_id"]) for item in fixture["interviews"]
    )
    anchors = sorted(
        str(item["anchor_id"]) for item in fixture["semantic_assertions"]
    )
    line_ids = sorted(str(item["id"]) for item in plan["lines"])
    connection_ids = sorted(
        str(item["id"]) for item in plan["connections"]
    )
    architecture_id = str(plan["architecture"]["id"])
    main_line_id = str(plan["architecture"]["main_line_id"])
    assurance = _normalized_anchor_assurance(structural_case)
    open_controls = {
        str(item["control_id"])
        for item in fixture["interviews"]
        if item["hardness"] == "author_open"
    }
    open_anchors = {
        anchor_id
        for anchor_id, value in assurance.items()
        if value == "author_open"
    }
    open_targets = sorted(open_controls | open_anchors)
    if not open_targets:
        open_targets = [str(plan["plan_id"])]
    optional_lines = {
        str(item["id"])
        for item in plan["lines"]
        if item["type"] == "optional_melody"
    }
    optional_connections = {
        str(item["id"])
        for item in plan["connections"]
        if item["from_line_id"] in optional_lines
        or item["to_line_id"] in optional_lines
    }
    optional_targets = sorted(optional_lines | optional_connections)
    if not optional_targets:
        optional_targets = [str(plan["plan_id"])]
    c1_requirements = sorted(
        str(item["id"])
        for item in plan["downstream_requirements"]["C1"]
    )
    downstream = sorted(
        str(item["id"])
        for requirements in plan["downstream_requirements"].values()
        for item in requirements
    )
    return {
        "authority_preservation": sorted(controls + anchors),
        "main_arc_completeness": sorted(
            {architecture_id, main_line_id}
        ),
        "causal_topology": sorted(
            {architecture_id, *line_ids, *connection_ids}
        ),
        "role_clustering": sorted({*line_ids, *c1_requirements}),
        "open_preservation": open_targets,
        "optional_non_load_bearing": optional_targets,
        "non_placeholder_evidence": sorted(registry),
        "downstream_usefulness": downstream,
    }


def _iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for nested in value:
            yield from _iter_strings(nested)


def _contains_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER.search(" ".join(value.split())))


def _subject(structural_case: Any) -> dict[str, Any]:
    manifest = structural_case.manifest
    fixture = structural_case.fixture
    plan = structural_case.plan
    return {
        "manifest_id": manifest["manifest_id"],
        "fixture": copy.deepcopy(manifest["fixture"]),
        "storyline_plan": copy.deepcopy(manifest["storyline_plan"]),
        "storyline_plan_schema": copy.deepcopy(
            manifest["storyline_plan_schema"]
        ),
        "fixture_id": fixture["fixture_id"],
        "run_id": fixture["run_id"],
        "plan_id": plan["plan_id"],
        "structural_validation_sha256": rt.canonical_sha256(
            structural_case.validation
        ),
    }


def validate_storyline_quality_gate(
    structural_case: Any,
    gate: Mapping[str, Any],
    *,
    trusted_schema_snapshot: Any | None = None,
) -> dict[str, Any]:
    """Validate accountable review evidence against one structural case."""

    _validate_trusted_gate_schema(
        gate,
        trusted_snapshot=trusted_schema_snapshot,
    )
    structural_validation = getattr(
        structural_case, "validation", None
    )
    _require(
        isinstance(structural_validation, Mapping),
        "STORYLINE_QUALITY_STRUCTURAL_VALIDATION_INVALID",
        "structural validation must be a mapping",
    )
    _require(
        structural_validation.get("status") == "ready",
        "STORYLINE_QUALITY_STRUCTURAL_NOT_READY",
        "structural validation must have status=ready",
    )
    _require(
        structural_validation.get("plan_id")
        == structural_case.plan.get("plan_id")
        and structural_validation.get("fixture_id")
        == structural_case.fixture.get("fixture_id")
        and structural_validation.get("run_id")
        == structural_case.fixture.get("run_id"),
        "STORYLINE_QUALITY_STRUCTURAL_IDENTITY_MISMATCH",
        "structural validation plan, fixture, or run identity changed",
    )
    _require(
        gate.get("ownership") == EXPECTED_OWNERSHIP,
        "STORYLINE_QUALITY_AUTHORITY_INVALID",
        "quality evidence is eval-owned, non-authoritative, and not a completion",
    )
    _require(
        gate.get("subject") == _subject(structural_case),
        "STORYLINE_QUALITY_SUBJECT_MISMATCH",
        "fixture, plan, schema, or structural validation changed",
    )
    producer = gate.get("producer", {})
    reviewer = gate.get("reviewer", {})
    _require(
        producer.get("task_id") != reviewer.get("task_id")
        and producer.get("thread_id") != reviewer.get("thread_id"),
        "STORYLINE_QUALITY_REVIEW_NOT_INDEPENDENT",
        "producer and reviewer task/thread identities must both differ",
    )
    registry = target_registry(structural_case)
    expected_targets = expected_check_targets(structural_case)
    checks = gate.get("checks")
    _require(
        isinstance(checks, list),
        "STORYLINE_QUALITY_CHECK_SET_INVALID",
        "checks must be an array",
    )
    indexed: dict[str, Mapping[str, Any]] = {}
    for check in checks:
        if not isinstance(check, Mapping):
            _fail(
                "STORYLINE_QUALITY_CHECK_SET_INVALID",
                "check is not an object",
            )
        check_id = check.get("id")
        if not isinstance(check_id, str) or check_id in indexed:
            _fail(
                "STORYLINE_QUALITY_CHECK_SET_INVALID",
                f"invalid or duplicate check: {check_id!r}",
            )
        indexed[check_id] = check
    _require(
        set(indexed) == set(REQUIRED_CHECKS)
        and len(indexed) == len(REQUIRED_CHECKS),
        "STORYLINE_QUALITY_CHECK_SET_INVALID",
        f"expected exactly {list(REQUIRED_CHECKS)}",
    )
    evidence_values: set[str] = set()
    failure_values: set[str] = set()
    for check_id in REQUIRED_CHECKS:
        check = indexed[check_id]
        _require(
            check.get("status") == "pass",
            "STORYLINE_QUALITY_CHECK_NOT_PASS",
            check_id,
        )
        target_ids = check.get("target_ids")
        _require(
            isinstance(target_ids, list)
            and target_ids == expected_targets[check_id],
            "STORYLINE_QUALITY_CHECK_COVERAGE_INVALID",
            (
                f"{check_id}: expected {expected_targets[check_id]}, "
                f"got {target_ids}"
            ),
        )
        unknown = [
            target_id
            for target_id in target_ids
            if target_id not in registry
        ]
        _require(
            not unknown,
            "STORYLINE_QUALITY_TARGET_UNKNOWN",
            f"{check_id}: {unknown}",
        )
        evidence = " ".join(str(check.get("evidence", "")).split())
        failure = " ".join(
            str(check.get("failure_condition", "")).split()
        )
        _require(
            any(target_id in evidence for target_id in target_ids)
            and any(target_id in failure for target_id in target_ids),
            "STORYLINE_QUALITY_EVIDENCE_NOT_CONCRETE",
            f"{check_id}: evidence and failure condition must cite a target",
        )
        _require(
            not _contains_placeholder(evidence)
            and not _contains_placeholder(failure),
            "STORYLINE_QUALITY_PLACEHOLDER_EVIDENCE",
            check_id,
        )
        _require(
            evidence not in evidence_values
            and failure not in failure_values
            and evidence != failure,
            "STORYLINE_QUALITY_TEMPLATE_EVIDENCE",
            check_id,
        )
        evidence_values.add(evidence)
        failure_values.add(failure)
    for finding in gate.get("findings", []):
        unknown = [
            target_id
            for target_id in finding.get("target_ids", [])
            if target_id not in registry
        ]
        _require(
            not unknown,
            "STORYLINE_QUALITY_TARGET_UNKNOWN",
            f"finding {finding.get('id')}: {unknown}",
        )
    placeholder_subjects = [
        value
        for value in _iter_strings(
            [structural_case.fixture, structural_case.plan]
        )
        if _contains_placeholder(value)
    ]
    _require(
        not placeholder_subjects,
        "STORYLINE_QUALITY_SUBJECT_PLACEHOLDER",
        repr(placeholder_subjects[:3]),
    )
    _require(
        gate.get("verdict") == "ready"
        and gate.get("findings") == [],
        "STORYLINE_QUALITY_NOT_READY",
        "admission requires verdict=ready and findings=[]",
    )
    assurance = _normalized_anchor_assurance(structural_case)
    derived_anchors = {
        anchor_id
        for anchor_id, value in assurance.items()
        if value == "derived_unsealed"
    }
    derived_controls = {
        str(control_id)
        for anchor in structural_case.fixture["semantic_assertions"]
        if anchor["anchor_id"] in derived_anchors
        for control_id in anchor["required_source_ids"]
    }
    authority_targets = set(
        indexed["authority_preservation"]["target_ids"]
    )
    _require(
        authority_targets
        & (derived_anchors | derived_controls)
        == derived_anchors | derived_controls,
        "STORYLINE_QUALITY_DERIVED_COVERAGE_INVALID",
        "derived anchors and their source controls are not exactly covered",
    )
    return {
        "schema_version": "1.0",
        "status": "ready",
        "gate_id": gate["gate_id"],
        "manifest_id": structural_case.manifest["manifest_id"],
        "fixture_id": structural_case.fixture["fixture_id"],
        "plan_id": structural_case.plan["plan_id"],
        "reviewer_task_id": reviewer["task_id"],
        "reviewer_thread_id": reviewer["thread_id"],
        "check_count": len(indexed),
        "target_count": len(registry),
        "open_target_count": len(
            expected_targets["open_preservation"]
        ),
        "optional_target_count": len(
            expected_targets["optional_non_load_bearing"]
        ),
        "derived_anchor_count": len(derived_anchors),
    }


def load_storyline_quality_gate(
    manifest_path: str | Path,
    gate_path: str | Path,
    *,
    repository_root: str | Path = REPOSITORY_ROOT,
    evals_root: str | Path = EVALS_ROOT,
) -> CompatibilityValidatedStorylineQualityCase:
    """Compatibility loader; the explicit path must equal the manifest ref."""

    repository = Path(repository_root).resolve(strict=True)
    evals = _inside(
        Path(evals_root),
        repository,
        "STORYLINE_QUALITY_EVALS_OUTSIDE_REPOSITORY",
    )
    structural_case = storyline_plan.load_eval_case(
        manifest_path,
        repository_root=repository,
        evals_root=evals,
    )
    gate_file = _inside(
        Path(gate_path),
        evals,
        "STORYLINE_QUALITY_GATE_OUTSIDE_EVALS",
    )
    declared_gate_file = _inside(
        rt.resolve_artifact_path(
            structural_case.manifest["storyline_quality_gate"]["path"],
            root=evals,
        ),
        evals,
        "STORYLINE_QUALITY_GATE_OUTSIDE_EVALS",
    )
    _require(
        gate_file == declared_gate_file,
        "STORYLINE_QUALITY_GATE_PATH_NOT_DECLARED",
        "compatibility gate path must equal the manifest-declared path",
    )
    schema_path = _inside(
        evals.joinpath(*QUALITY_SCHEMA_REPOSITORY_PATH.split("/")),
        evals,
        "STORYLINE_QUALITY_SCHEMA_INVALID",
    )
    schema_snapshot = _quality_snapshot(
        schema_path,
        "STORYLINE_QUALITY_SCHEMA_UNREADABLE",
        expected_sha256=TRUSTED_QUALITY_SCHEMA_SHA256,
        hash_code="STORYLINE_QUALITY_SCHEMA_UNTRUSTED",
    )
    gate_snapshot = _quality_snapshot(
        gate_file, "STORYLINE_QUALITY_GATE_UNREADABLE"
    )
    gate = gate_snapshot.value
    _validate_schema(
        gate,
        schema_path,
        schema_snapshot=schema_snapshot.value,
    )
    validation = validate_storyline_quality_gate(
        structural_case,
        gate,
        trusted_schema_snapshot=schema_snapshot,
    )
    return CompatibilityValidatedStorylineQualityCase(
        structural_case=structural_case,
        gate_path=gate_file,
        gate_schema_path=schema_path,
        gate_sha256=gate_snapshot.sha256,
        gate_schema_sha256=schema_snapshot.sha256,
        gate=copy.deepcopy(gate),
        validation=copy.deepcopy(validation),
    )


def load_ready_eval_case(
    manifest_path: str | Path,
    *,
    repository_root: str | Path = REPOSITORY_ROOT,
    evals_root: str | Path = EVALS_ROOT,
) -> FormalValidatedStorylineQualityCase:
    """Load the sole formal eval case declared by one manifest.

    The quality-gate path is never inferred from a fixture and cannot be
    supplied independently by a formal caller.
    """

    repository = Path(repository_root).resolve(strict=True)
    evals = _inside(
        Path(evals_root),
        repository,
        "STORYLINE_QUALITY_EVALS_OUTSIDE_REPOSITORY",
    )
    structural_case = storyline_plan.load_eval_case(
        manifest_path,
        repository_root=repository,
        evals_root=evals,
    )
    gate_reference = structural_case.manifest[
        "storyline_quality_gate"
    ]
    schema_reference = structural_case.manifest[
        "storyline_quality_gate_schema"
    ]
    _require(
        schema_reference["path"] == QUALITY_SCHEMA_REPOSITORY_PATH
        and schema_reference["sha256"] == TRUSTED_QUALITY_SCHEMA_SHA256,
        "STORYLINE_QUALITY_SCHEMA_REFERENCE_INVALID",
        "manifest must bind the fixed code-pinned quality schema",
    )
    gate_snapshot = storyline_plan._verified_reference_snapshot(
        gate_reference,
        evals_root=evals,
        repository_root=repository,
        label="storyline_quality_gate",
    )
    schema_snapshot = storyline_plan._verified_reference_snapshot(
        schema_reference,
        evals_root=evals,
        repository_root=repository,
        label="storyline_quality_gate_schema",
    )
    gate = gate_snapshot.value
    _validate_schema(
        gate,
        schema_snapshot.path,
        schema_snapshot=schema_snapshot.value,
    )
    validation = validate_storyline_quality_gate(
        structural_case,
        gate,
        trusted_schema_snapshot=schema_snapshot,
    )
    return FormalValidatedStorylineQualityCase(
        structural_case=structural_case,
        gate_path=gate_snapshot.path,
        gate_schema_path=schema_snapshot.path,
        gate_sha256=gate_snapshot.sha256,
        gate_schema_sha256=schema_snapshot.sha256,
        gate=copy.deepcopy(gate),
        validation=copy.deepcopy(validation),
    )


__all__ = [
    "EXPECTED_OWNERSHIP",
    "CompatibilityValidatedStorylineQualityCase",
    "FormalValidatedStorylineQualityCase",
    "QUALITY_SCHEMA_REPOSITORY_PATH",
    "REQUIRED_CHECKS",
    "StorylineQualityError",
    "expected_check_targets",
    "load_ready_eval_case",
    "load_storyline_quality_gate",
    "target_registry",
    "validate_storyline_quality_gate",
]
