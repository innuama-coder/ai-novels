"""Deterministic P1 machine-conception package assembler."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
stage_identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"

STAGES = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1")
UPSTREAM_STAGES = ("S1", "W1", "E1", "T1", "C1", "Q1")
CANONICAL_NAMES = {
    "B0": "author-control-baseline.json",
    "S1": "storyline-architecture.json",
    "W1": "world-model.json",
    "E1": "environment-system.json",
    "T1": "event-timeline.json",
    "C1": "character-system.json",
    "Q1": "conception-review.json",
}
_MODEL_STAGES = ("S1", "W1", "E1", "T1", "C1")
_PARTITIONS = (
    "author_locked",
    "autonomous_owned",
    "downstream_freedom",
    "author_open",
)
_SOURCE_ID = re.compile(
    r"^(INT|SUB|WLD|CHR|CAU|NAR|SLD|SL|SLC|WR|WF|WS|END|ENV|ZONE|"
    r"EVD|EV|CHD|SLOT|REL|FND|DEV)-[A-Za-z0-9._-]+$"
)
_REFERENCE_KEYS = {
    "source_ids",
    "evidence_ids",
    "realization_ids",
    "projection_ids",
    "decision_ids",
    "impact_ids",
    "trigger_ids",
    "allowed_by_ids",
    "event_ids",
    "storyline_ids",
    "environment_ids",
    "participant_slot_ids",
    "counter_slot_ids",
    "visibility_ids",
    "change_event_ids",
    "pressure_event_ids",
    "choice_event_ids",
    "relationship_ids",
}
_TECHNICAL_ID_FIELDS = {
    "run_id",
    "source_run_id",
    "session_id",
    "task_id",
    "thread_id",
    "return_id",
}
_ROOT_FILES = {
    "input-gate.json",
    "novel-conception-package.json",
    "author-control-baseline.json",
    "authoritative-design-index.json",
    "novel-conception-spec.md",
    "cross-model-index.json",
    "traceability-matrix.md",
    "development-handoff.json",
    "assembly-execution.json",
    "validation.json",
    "package-manifest.json",
    "stage-completion.json",
}
_ROOT_PREFIXES = (
    "authoritative-design-artifacts/",
    "canonical-models/",
    "review/",
    "source-packages/",
    "implementation/",
)
QUALITY_COVERAGE_BASIS = (
    "all-id-bearing-objects-in-S1-and-T1-canonical-models"
)


class P1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class P1RunReceipt:
    package_root: Path
    conception_package: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any
    replayed: bool = False


def _fail(code: str, message: str) -> None:
    raise P1Error(code, message)


def _read(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path} root must be an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


def _logical(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        _fail("P1_PATH_INVALID", value)
    return value


def _package_roots(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
    review_package: str | Path,
) -> dict[str, Path]:
    return {
        "B0": Path(baseline_package).resolve(),
        "S1": Path(storyline_package).resolve(),
        "W1": Path(world_package).resolve(),
        "E1": Path(environment_package).resolve(),
        "T1": Path(event_package).resolve(),
        "C1": Path(character_package).resolve(),
        "Q1": Path(review_package).resolve(),
    }


def _validator(stage: str):
    if stage == "B0":
        return rt.validate_baseline_package
    module_names = {
        "S1": "skills.novel-storyline-architecture-designer.scripts.run_v2",
        "W1": "skills.novel-world-model-designer.scripts.run_v2",
        "E1": "skills.novel-environment-system-designer.scripts.run_v2",
        "T1": "skills.novel-event-timeline-designer.scripts.run_v2",
        "C1": "skills.novel-character-system-designer.scripts.run_v2",
        "Q1": "skills.novel-conception-reviewer.scripts.run_v2",
    }
    function_names = {
        "S1": "validate_s1_package",
        "W1": "validate_w1_package",
        "E1": "validate_e1_package",
        "T1": "validate_t1_package",
        "C1": "validate_c1_package",
        "Q1": "validate_q1_package",
    }
    return getattr(importlib.import_module(module_names[stage]), function_names[stage])


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    root = root.resolve()
    return [
        {"path": relative, "sha256": _long_sha256(path)}
        for path, relative in _iter_files(root)
    ]


def _long_name(path: Path) -> str:
    value = str(path.resolve())
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        return "\\\\?\\" + value
    return value


def _long_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_name(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path):
    root = root.resolve()
    walk_root = _long_name(root)
    records: list[tuple[Path, str]] = []
    for directory, directories, filenames in os.walk(walk_root):
        directories.sort()
        for filename in sorted(filenames):
            native = os.path.join(directory, filename)
            relative = os.path.relpath(native, walk_root).replace("\\", "/")
            records.append((root / PurePosixPath(relative), relative))
    return records


def _verify_manifest_long(manifest: Mapping[str, Any], *, root: Path) -> None:
    files = manifest.get("files")
    if not isinstance(files, list):
        _fail("P1_MANIFEST_INVALID", "files are missing")
    for reference in files:
        if not isinstance(reference, Mapping):
            _fail("P1_MANIFEST_INVALID", "file reference is invalid")
        relative = reference.get("path")
        if not isinstance(relative, str) or not relative:
            _fail("P1_MANIFEST_INVALID", "file path is invalid")
        path = root / PurePosixPath(relative)
        if _long_sha256(path) != reference.get("sha256"):
            _fail("P1_MANIFEST_INVALID", relative)


def _stage_reference(
    root: Path, stage: str, expected: Mapping[str, str]
) -> dict[str, str]:
    completion = _read(
        root / "stage-completion.json", f"P1_{stage}_COMPLETION_INVALID"
    )
    actual_sha256 = _long_sha256(root / "stage-completion.json")
    logical = PurePosixPath(str(expected.get("path", "")))
    if (
        completion.get("stage") != stage
        or completion.get("status") != "ready"
        or expected.get("stage") not in {None, stage}
        or logical.name != "stage-completion.json"
        or expected.get("sha256") != actual_sha256
    ):
        _fail(f"P1_{stage}_COMPLETION_INVALID", "not a ready V2 completion")
    for field, filename in (
        ("manifest", "package-manifest.json"),
        ("validation", "validation.json"),
    ):
        reference = completion.get(field)
        if not isinstance(reference, Mapping):
            _fail(f"P1_{stage}_COMPLETION_INVALID", f"missing {field}")
        sibling = PurePosixPath(str(reference.get("path", "")))
        if sibling.name != filename or sibling.parent != logical.parent:
            _fail(
                f"P1_{stage}_COMPLETION_INVALID",
                f"{field} is not the logical completion sibling",
            )
        sibling_path = root / filename
        if (
            not sibling_path.is_file()
            or reference.get("sha256") != _long_sha256(sibling_path)
        ):
            _fail(
                f"P1_{stage}_COMPLETION_INVALID",
                f"{field} physical sibling differs",
            )
    return copy.deepcopy(dict(expected))


def _gate_stage_references(input_gate: Any) -> dict[str, Mapping[str, str]]:
    values: dict[str, Mapping[str, str]] = {}
    baseline = input_gate.data.get("baseline_completion")
    if isinstance(baseline, Mapping):
        values["B0"] = baseline
    upstream = input_gate.data.get("upstream_completions")
    if not isinstance(upstream, list):
        _fail("P1_GATE_INVALID", "upstream completions missing")
    for reference in upstream:
        if not isinstance(reference, Mapping) or not isinstance(
            reference.get("stage"), str
        ):
            _fail("P1_GATE_INVALID", "upstream completion invalid")
        stage = str(reference["stage"])
        if stage in values:
            _fail("P1_GATE_INVALID", f"duplicate {stage} completion")
        values[stage] = reference
    if set(values) != set(STAGES):
        _fail("P1_GATE_INVALID", "gate does not bind exactly B0/S1-Q1")
    return values


def _implementation_paths() -> dict[str, Path]:
    runtime_dir = _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    values = {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/package-contract.md": _SKILL / "references" / "package-contract.md",
    }
    for name in (
        "canonical.py",
        "contracts.py",
        "coordinator.py",
        "stage_implementation_identity.py",
    ):
        values[f"runtime/{name}"] = runtime_dir / name
    for name in (
        "common-defs.schema.json",
        "canonical-common.schema.json",
        "novel-conception-package.schema.json",
        "development-handoff.schema.json",
        "package-manifest.schema.json",
        "stage-completion.schema.json",
        "input-gate.schema.json",
    ):
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


_T1_EVENT_PROJECTION_MAP = {
    "kind": "event_kind", "milestone_id": "milestone_id",
    "world_time_slot": "world_time", "storyline_ids": "storyline_ids",
    "environment_id": "environment_id", "affordance_ids": "affordance_ids",
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
    "preconditions": "preconditions", "direct_result": "direct_result",
    "next_pressure": "next_pressure", "source_ids": "source_ids",
    "atomicity_reason": "atomicity_reason",
}
_T1_EVENT_PROJECTION_MAP_25 = {
    "consumes_token_instance_ids": "consumes_token_instance_ids",
    "lifecycle_effects": "lifecycle_effects",
}
_T1_PROPOSITION_PROJECTION_FIELDS = (
    "id", "statement", "source_ids", "audience", "initially_true",
    "terminality", "initial_anchor_refs", "producer_event_ids",
)
_T1_PROJECTION_PAIRS = (
    ("planned_event_registry", "major_events", "event"),
    ("planned_proposition_registry", "proposition_registry", "proposition"),
    ("planned_causal_edges", "causal_edges", "edge"),
)


def _collect_quality_objects(value: Any, *, stage: str) -> list[dict[str, str]]:
    """Legacy 2.0/2.1 ID traversal retained byte-for-byte in semantics."""
    output: list[dict[str, str]] = []
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            output.append(
                {
                    "stage": stage,
                    "id": identifier,
                    "classification": (
                        "s1_obligation"
                        if stage == "S1"
                        else "t1_realization"
                    ),
                    "value_sha256": rt.canonical_sha256(value),
                }
            )
        for child in value.values():
            output.extend(_collect_quality_objects(child, stage=stage))
    elif isinstance(value, list):
        for child in value:
            output.extend(_collect_quality_objects(child, stage=stage))
    return output


def _quality_projection_fail(detail: str) -> None:
    _fail("P1_Q1_QUALITY_COVERAGE_INVALID", detail)


def _quality_registry(model: Mapping[str, Any], field: str) -> dict[str, Mapping[str, Any]]:
    values = model.get(field)
    if not isinstance(values, list):
        _quality_projection_fail(f"T1.{field} missing")
    output: dict[str, Mapping[str, Any]] = {}
    for index, value in enumerate(values):
        if not isinstance(value, Mapping) or not isinstance(value.get("id"), str):
            _quality_projection_fail(f"T1.{field}[{index}]")
        identifier = value["id"]
        if identifier in output:
            _quality_projection_fail(f"T1:{identifier} ambiguous registry ID")
        output[identifier] = value
    return output


def _quality_validate_event_projection(
    identifier: str,
    planned: Mapping[str, Any],
    canonical: Mapping[str, Any],
    *,
    schema_version: Any,
) -> None:
    projection_map = dict(_T1_EVENT_PROJECTION_MAP)
    if schema_version == "2.5":
        projection_map.update(_T1_EVENT_PROJECTION_MAP_25)
    for source_field, target_field in projection_map.items():
        if source_field not in planned or planned[source_field] != canonical.get(target_field):
            _quality_projection_fail(f"T1:{identifier}.{source_field}")
    changed = planned.get("changed_subject")
    if not isinstance(changed, Mapping):
        _quality_projection_fail(f"T1:{identifier}.changed_subject")
    subject = changed.get("subject_id")
    if (
        not isinstance(subject, str)
        or canonical.get("subject_id") != subject
        or canonical.get("subject_kind") != changed.get("subject_kind")
        or canonical.get("before_state") != {subject: changed.get("before")}
        or canonical.get("after_state") != {subject: changed.get("after")}
    ):
        _quality_projection_fail(f"T1:{identifier}.changed_subject")


def _quality_add(
    output: dict[str, Mapping[str, Any]], identifier: str,
    value: Mapping[str, Any], *, protected: set[str]
) -> None:
    existing = output.get(identifier)
    if existing is None:
        output[identifier] = value
    elif identifier in protected:
        _quality_projection_fail(f"T1:{identifier} has a third projection source")
    elif rt.canonical_sha256(existing) != rt.canonical_sha256(value):
        _quality_projection_fail(f"T1:{identifier} conflicting duplicate")


def _quality_recursive_index(
    value: Any, output: dict[str, Mapping[str, Any]], *, protected: set[str],
    excluded_top_level: set[str] | None = None, top_level: bool = True,
) -> None:
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            _quality_add(output, identifier, value, protected=protected)
        for field, child in value.items():
            if top_level and excluded_top_level and field in excluded_top_level:
                continue
            _quality_recursive_index(
                child, output, protected=protected,
                excluded_top_level=excluded_top_level, top_level=False,
            )
    elif isinstance(value, list):
        for child in value:
            _quality_recursive_index(
                child, output, protected=protected,
                excluded_top_level=excluded_top_level, top_level=False,
            )


def _collect_t1_projection_quality_objects(
    model: Mapping[str, Any],
) -> list[dict[str, str]]:
    output: dict[str, Mapping[str, Any]] = {}
    protected: set[str] = set()
    for planned_field, canonical_field, kind in _T1_PROJECTION_PAIRS:
        planned = _quality_registry(model, planned_field)
        canonical = _quality_registry(model, canonical_field)
        if set(planned) != set(canonical):
            _quality_projection_fail(f"T1.{planned_field}/{canonical_field} ID sets differ")
        for identifier in sorted(canonical):
            source, target = planned[identifier], canonical[identifier]
            if kind == "event":
                _quality_validate_event_projection(
                    identifier,
                    source,
                    target,
                    schema_version=model.get("schema_version"),
                )
            elif kind == "proposition":
                try:
                    source_projection = {
                        field: source[field] for field in _T1_PROPOSITION_PROJECTION_FIELDS
                    }
                    target_projection = {
                        field: target[field] for field in _T1_PROPOSITION_PROJECTION_FIELDS
                    }
                except KeyError as error:
                    _quality_projection_fail(f"T1:{identifier}.{error.args[0]}")
                if source_projection != target_projection:
                    _quality_projection_fail(f"T1:{identifier} proposition projection")
            elif source != target:
                _quality_projection_fail(f"T1:{identifier} edge projection")
            if identifier in output or identifier in protected:
                _quality_projection_fail(f"T1:{identifier} ambiguous projection")
            output[identifier] = target
            protected.add(identifier)
    excluded = {field for pair in _T1_PROJECTION_PAIRS for field in pair[:2]}
    _quality_recursive_index(
        model, output, protected=protected, excluded_top_level=excluded
    )
    return [
        {
            "stage": "T1", "id": identifier,
            "classification": "t1_realization",
            "value_sha256": rt.canonical_sha256(value),
        }
        for identifier, value in output.items()
    ]


def _expected_quality_objects(
    models: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    output = []
    output.extend(_collect_quality_objects(models["S1"], stage="S1"))
    t1 = models["T1"]
    if t1.get("schema_version") in {"2.2", "2.3", "2.4", "2.5"}:
        output.extend(_collect_t1_projection_quality_objects(t1))
    else:
        output.extend(_collect_quality_objects(t1, stage="T1"))
    keys = [(item["stage"], item["id"]) for item in output]
    if len(keys) != len(set(keys)):
        _fail(
            "P1_Q1_QUALITY_COVERAGE_INVALID",
            "S1/T1 contains ambiguous same-stage quality object IDs",
        )
    return sorted(
        output,
        key=lambda item: (
            0 if item["stage"] == "S1" else 1,
            item["id"],
        ),
    )


def _require_q1_quality_admission(
    review: Mapping[str, Any], models: Mapping[str, Mapping[str, Any]]
) -> None:
    certificate = review.get("quality_coverage")
    if not isinstance(certificate, Mapping):
        _fail("P1_Q1_QUALITY_COVERAGE_INVALID", "Q1 certificate missing")
    expected = _expected_quality_objects(models)
    required = certificate.get("required_objects")
    covered = certificate.get("covered_objects")
    covered_projection = [
        {
            key: item.get(key)
            for key in ("stage", "id", "classification", "value_sha256")
        }
        for item in covered
    ] if isinstance(covered, list) else None
    if (
        certificate.get("coverage_basis") != QUALITY_COVERAGE_BASIS
        or required != expected
        or covered_projection != expected
        or certificate.get("unresolved_blocking_quality_record_ids") != []
        or certificate.get("result") != "complete"
    ):
        _fail(
            "P1_Q1_QUALITY_COVERAGE_INVALID",
            "Q1 did not fully cover current S1 obligations and T1 realizations",
        )


def _quality_admission(
    review: Mapping[str, Any], review_ref: Mapping[str, str]
) -> dict[str, Any]:
    certificate = review["quality_coverage"]
    return {
        "review": copy.deepcopy(dict(review_ref)),
        "coverage_basis": certificate["coverage_basis"],
        "required_object_count": len(certificate["required_objects"]),
        "covered_object_count": len(certificate["covered_objects"]),
        "unresolved_blocking_quality_record_ids": copy.deepcopy(
            certificate["unresolved_blocking_quality_record_ids"]
        ),
        "result": "admitted",
    }


def _context(
    roots: Mapping[str, Path],
    *,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    if set(roots) != set(STAGES):
        _fail("P1_INPUT_SET_INVALID", "packages must be exactly B0/S1-C1/Q1")
    before = {stage: _tree_inventory(root) for stage, root in roots.items()}
    if full_validation:
        for stage in STAGES:
            try:
                _validator(stage)(roots[stage], runtime=runtime)
            except Exception as error:
                _fail(f"P1_{stage}_INVALID", str(error))
    models = {
        stage: _read(
            roots[stage] / CANONICAL_NAMES[stage],
            f"P1_{stage}_CANONICAL_INVALID",
        )
        for stage in STAGES
    }
    manifests = {
        stage: _read(
            roots[stage] / "package-manifest.json",
            f"P1_{stage}_MANIFEST_INVALID",
        )
        for stage in STAGES
    }
    completions = {
        stage: _read(
            roots[stage] / "stage-completion.json",
            f"P1_{stage}_COMPLETION_INVALID",
        )
        for stage in STAGES
    }
    for stage in STAGES:
        manifest_files = manifests[stage].get("files")
        if not isinstance(manifest_files, list):
            _fail(f"P1_{stage}_MANIFEST_INVALID", "files are missing")
        declared = {
            item.get("path"): item
            for item in manifest_files
            if isinstance(item, Mapping)
        }
        actual = {
            item["path"]: item
            for item in _tree_inventory(roots[stage])
            if item["path"]
            not in {"package-manifest.json", "stage-completion.json"}
        }
        if (
            len(declared) != len(manifest_files)
            or declared != actual
        ):
            _fail(
                f"P1_{stage}_PACKAGE_BOUNDARY_INVALID",
                "physical files differ from the formal manifest",
            )
    if before != {stage: _tree_inventory(root) for stage, root in roots.items()}:
        _fail("P1_INPUT_MUTATED", "read-only validation changed an input package")
    run_ids = {model.get("run_id") for model in models.values()}
    if len(run_ids) != 1 or None in run_ids:
        _fail("P1_RUN_ID_MISMATCH", "input packages belong to different runs")
    run_id = models["B0"]["run_id"]
    for stage in STAGES:
        if (
            manifests[stage].get("run_id") != run_id
            or manifests[stage].get("stage") != stage
            or manifests[stage].get("verdict") != "ready"
            or completions[stage].get("run_id") != run_id
            or completions[stage].get("stage") != stage
            or completions[stage].get("status") != "ready"
        ):
            _fail(f"P1_{stage}_LINEAGE_INVALID", "run/stage/ready mismatch")
    review = models["Q1"]
    if (
        review.get("skill") != "novel-conception-reviewer"
        or review.get("stage") != "Q1"
        or review.get("status") != "ready"
        or review.get("verdict") != "ready"
        or review.get("return_request") is not None
        or any(
            item.get("severity") != "note"
            for item in review.get("findings", [])
            if isinstance(item, Mapping)
        )
    ):
        _fail("P1_Q1_NOT_READY", "Q1 did not release a clean ready review")
    _require_q1_quality_admission(review, models)
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("P1_GATE_INVALID", str(error))
    gate_references = _gate_stage_references(input_gate)
    refs = {
        stage: _stage_reference(roots[stage], stage, gate_references[stage])
        for stage in STAGES
    }
    gate = input_gate.data
    if (
        gate.get("target_stage") != "P1"
        or gate.get("run_id") != run_id
        or gate.get("baseline_completion") != refs["B0"]
        or gate.get("upstream_completions")
        != [refs[stage] for stage in UPSTREAM_STAGES]
        # Production input gates are immutable coordinator artifacts under
        # orchestration/input-gates/<revision>-P1/input-gate.json.  The stage
        # copies that sealed document into its package, but must not pretend
        # the source reference already lives at P1/input-gate.json.
        or not str(input_gate.reference.get("path", "")).endswith(
            "/input-gate.json"
        )
        or rt.canonical_sha256(gate) != input_gate.reference.get("sha256")
    ):
        _fail("P1_GATE_INVALID", "gate is not exact B0/[S1..Q1] topology")
    if gate.get("entry_mode") == "forward":
        if gate.get("active_return") is not None or gate.get("return_binding") is not None:
            _fail("P1_GATE_INVALID", "forward gate carries a return")
    elif gate.get("entry_mode") == "return_resolution":
        binding = gate.get("return_binding")
        if (
            not isinstance(binding, Mapping)
            or binding.get("resume_stage") != "P1"
            or binding.get("resume_point") != "P1"
            or gate.get("active_return") is None
        ):
            _fail("P1_GATE_INVALID", "return is not a P1-only resolution")
    else:
        _fail("P1_GATE_INVALID", "unknown entry mode")
    q1_gate = _read(roots["Q1"] / "input-gate.json", "P1_Q1_GATE_INVALID")
    if q1_gate.get("upstream_completions") != [
        refs[stage] for stage in ("S1", "W1", "E1", "T1", "C1")
    ]:
        _fail("P1_Q1_LINEAGE_INVALID", "Q1 does not bind current S1-C1")
    return models, manifests, completions


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _walk(value: Any, pointer: str = ""):
    yield pointer or "/", value
    if isinstance(value, Mapping):
        for key in sorted(value):
            yield from _walk(value[key], f"{pointer}/{_escape_pointer(str(key))}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{pointer}/{index}")


def _kind(pointer: str) -> str:
    parts = [part for part in pointer.split("/") if part]
    return parts[-2] if len(parts) >= 2 and parts[-1].isdigit() else "object"


# Cross-model identity is a schema contract, not a naming convention.  These
# are the only object collections whose ``id`` field is a story identity.
_IDENTITY_COLLECTIONS = {
    "B0": {"control_registry", "fact_dependencies", "objects"},
    "S1": {
        "character_requirements", "connections", "coverage_ledger",
        "cross_line_consistency", "derivation_claims", "design_decisions",
        "environment_requirements", "event_requirements", "open_items",
        "source_sequence_realizations", "story_claim_atoms",
        "story_claim_units", "story_obligation_coverage",
        "story_obligation_register", "storyline_demands", "storylines",
        "world_requirements", "objects",
    },
    "W1": {
        "authority_flows", "derivation_claims", "design_decisions",
        "environment_demands", "history_pressures", "information_flows",
        "institutions", "open_items", "reality_claims", "resource_flows",
        "rule_conflict_matrix", "storyline_requirements",
        "storyline_support_ledger", "systems", "world_facts", "objects",
    },
    "E1": {
        "access_and_authority", "actor_authority_bindings",
        "ambient_context_hosts", "capability_fact_registry",
        "capability_occurrence_requirements", "capability_step_registry",
        "derivation_claims", "design_decisions", "environment_demands",
        "environment_topology", "environments", "event_affordance_catalog",
        "functional_zones", "hazards_and_failure_modes",
        "initial_anchor_option_realization_ledger",
        "obligation_occurrence_bindings", "open_items",
        "resource_and_information_channels", "story_transition_support",
        "storyline_environment_requirements", "storyline_hosting_ledger",
        "transition_contracts", "objects",
    },
    "T1": {
        "causal_edges", "connection_realization", "derivation_claims",
        "design_decisions", "event_coverage_ledger", "event_demands",
        "information_changes", "major_events", "narrative_timing_constraints",
        "obligation_realizations", "open_items", "planned_causal_edges",
        "planned_event_registry", "planned_proposition_registry",
        "process_state_subject_registry", "proposition_registry",
        "state_ledger", "storyline_event_sequences", "objects",
    },
    "C1": {
        "aftermath_responsibility", "agency_matrix", "character_arcs",
        "character_demands", "derivation_claims", "design_decisions",
        "development_freedoms", "event_cast_coverage", "information_matrix",
        "open_items", "profiles", "relationships", "responsibility_matrix",
        "storyline_cast_coverage", "objects",
    },
}


def _normalized_pointer(pointer: str) -> str:
    return re.sub(r"/[0-9]+(?=/|$)", "/*", pointer)


def _identity_descriptor(stage: str, pointer: str, value: Any) -> tuple[str, str] | None:
    parts = [part for part in pointer.split("/") if part]
    if (
        len(parts) == 2 and parts[1].isdigit()
        and parts[0] in _IDENTITY_COLLECTIONS.get(stage, set())
        and isinstance(value, Mapping) and isinstance(value.get("id"), str)
    ):
        return value["id"], parts[0]
    if (
        stage == "S1" and len(parts) == 2
        and parts[0] == "line_claim_authority" and parts[1].isdigit()
        and isinstance(value, Mapping) and isinstance(value.get("claim_id"), str)
    ):
        return value["claim_id"], "line_claim_authority"
    if _is_c1_slot_resolution(stage, pointer, value):
        return value["slot_id"], "slot_resolution"
    if (
        stage == "T1" and isinstance(value, Mapping)
        and isinstance(value.get("occurrence_id"), str)
        and re.fullmatch(r"/major_events/[0-9]+/capability_step_occurrences/[0-9]+", pointer)
    ):
        return value["occurrence_id"], "capability_occurrence"
    if (
        stage == "T1" and isinstance(value, Mapping)
        and isinstance(value.get("occurrence_id"), str)
        and re.fullmatch(
            r"/planned_event_registry/[0-9]+/capability_step_occurrences/[0-9]+",
            pointer,
        )
    ):
        return value["occurrence_id"], "planned_capability_occurrence"
    return None


def _capability_occurrence_registry(
    model: Mapping[str, Any], field: str,
) -> dict[str, tuple[str, Mapping[str, Any]]]:
    output: dict[str, tuple[str, Mapping[str, Any]]] = {}
    events = model.get(field)
    if not isinstance(events, list):
        _fail("P1_CROSS_REFERENCE_PROJECTION_INVALID", f"T1.{field} missing")
    for event_index, event in enumerate(events):
        if not isinstance(event, Mapping):
            _fail(
                "P1_CROSS_REFERENCE_PROJECTION_INVALID",
                f"T1.{field}[{event_index}] invalid",
            )
        occurrences = event.get("capability_step_occurrences")
        if not isinstance(occurrences, list):
            _fail(
                "P1_CROSS_REFERENCE_PROJECTION_INVALID",
                f"T1.{field}[{event_index}].capability_step_occurrences missing",
            )
        for occurrence_index, occurrence in enumerate(occurrences):
            pointer = (
                f"/{field}/{event_index}/capability_step_occurrences/"
                f"{occurrence_index}"
            )
            if (
                not isinstance(occurrence, Mapping)
                or not isinstance(occurrence.get("occurrence_id"), str)
            ):
                _fail("P1_CROSS_REFERENCE_PROJECTION_INVALID", f"T1:{pointer}")
            identifier = occurrence["occurrence_id"]
            if identifier in output:
                _fail(
                    "P1_CROSS_REFERENCE_AMBIGUOUS",
                    f"T1:{field}:capability_occurrence:{identifier}",
                )
            output[identifier] = (pointer, occurrence)
    return output


def _validate_capability_occurrence_projection(model: Mapping[str, Any]) -> None:
    planned = _capability_occurrence_registry(model, "planned_event_registry")
    canonical = _capability_occurrence_registry(model, "major_events")
    if set(planned) != set(canonical):
        _fail(
            "P1_CROSS_REFERENCE_PROJECTION_INVALID",
            "T1 planned/canonical capability occurrence ID sets differ",
        )
    for identifier in sorted(canonical):
        if planned[identifier][1] != canonical[identifier][1]:
            _fail(
                "P1_CROSS_REFERENCE_PROJECTION_INVALID",
                f"T1:{identifier} capability occurrence projection",
            )


_REF_DESCRIPTORS: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    # Character slots are resolved only by C1; E1 operational actors are a
    # different identity domain even when four labels happen to overlap.
    ("S1", r"/storylines/\*/actor_slot_ids/\*", (("C1", "slot_resolution"),)),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/(?:participant_slot_ids|counter_slot_ids)/\*", (("C1", "slot_resolution"),)),
    ("T1", r"/major_events/\*/initiator_slot_id", (("C1", "slot_resolution"),)),
    ("C1", r"/development_freedoms/\*/subject_ids/\*", (("C1", "profiles"),)),
    ("C1", r"/development_freedoms/\*/source_ids/\*", (("B0", "control_registry"), ("C1", "profiles"), ("C1", "relationships"))),
    ("S1", r"/objects/\*/actor_slot_ids/\*", (("C1", "slot_resolution"),)),
    ("T1", r"/objects/\*/(?:participant_slot_ids|counter_slot_ids)/\*", (("C1", "slot_resolution"),)),
    ("T1", r"/objects/\*/initiator_slot_id", (("C1", "slot_resolution"),)),
    ("S1", r"/objects/\*/development_freedom_ids/\*", (("C1", "development_freedoms"),)),
    ("E1", r"/actor_authority_bindings/\*/actor_slot_id", (("E1", "e1_operational_slot"),)),
    ("E1", r"/ambient_context_hosts/\*/subject_or_actor_slot_ids/\*", (("E1", "e1_operational_slot"),)),
    ("E1", r"/capability_fact_registry/\*/(?:consumer_scope|issuer_scope)/actor_slot_ids/\*", (("E1", "e1_operational_slot"),)),
    ("E1", r"/capability_step_registry/\*/actor_slot_ids/\*", (("E1", "e1_operational_slot"),)),
    # Baseline controls and facts.
    ("B0", r"/design_artifacts/\*/control_ids/\*", (("B0", "control_registry"),)),
    ("S1", r"/(?:story_claim_atoms|story_claim_units|story_obligation_coverage)/\*/(?:control_id|source_control_ids/\*)", (("B0", "control_registry"),)),
    ("W1", r"/reality_claims/\*/fact_dependency_id", (("B0", "fact_dependencies"),)),
    # Core S1 topology consumed downstream.
    ("W1", r"/(?:history_pressures|institutions|rule_conflict_matrix|systems)/\*/storyline_ids/\*", (("S1", "storylines"),)),
    ("E1", r"/(?:ambient_context_hosts|initial_anchor_option_realization_ledger|initial_anchor_support|story_transition_support)/\*/storyline_id", (("S1", "storylines"),)),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/storyline_ids/\*", (("S1", "storylines"),)),
    ("T1", r"/storyline_event_sequences/\*/storyline_id", (("S1", "storylines"),)),
    # Environment capabilities, facts and occurrences.
    ("T1", r"/(?:major_events|planned_event_registry)/\*/e1_capability_step_ids/\*", (("E1", "capability_step_registry"),)),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/(?:requires_capability_fact_ids|produces_capability_fact_ids)/\*", (("E1", "capability_fact_registry"),)),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/capability_step_occurrences/\*/step_id", (("E1", "capability_step_registry"),)),
    ("T1", r"/information_changes/\*/source_occurrence_id", (("T1", "capability_occurrence"),)),
    # Events, propositions and token-instance ledgers.
    ("T1", r"/(?:causal_edges|planned_causal_edges)/\*/(?:from_event_id|to_event_id)", (("T1", "major_events"), ("T1", "planned_event_registry"))),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/predecessor_event_ids/\*", (("T1", "major_events"), ("T1", "planned_event_registry"))),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/(?:requires_proposition_ids|produces_proposition_ids|discloses_proposition_ids)/\*", (("T1", "proposition_registry"), ("T1", "planned_proposition_registry"))),
    ("T1", r"/(?:major_events|planned_event_registry)/\*/(?:requires_token_instance_ids|produces_token_instance_ids)/\*", (("T1", "authority_token_instance"),)),
    ("T1", r"/authority_token_instance_ledger/\*/(?:token_fact_id)", (("E1", "capability_fact_registry"),)),
    ("T1", r"/authority_token_instance_ledger/\*/origin/producer_event_id", (("T1", "major_events"),)),
    ("T1", r"/authority_token_instance_ledger/\*/origin/producer_occurrence_id", (("T1", "capability_occurrence"),)),
    ("T1", r"/authority_token_instance_ledger/\*/consumer_occurrences/\*/event_id", (("T1", "major_events"),)),
    ("T1", r"/state_ledger/\*/trigger_ids/\*", (("T1", "major_events"),)),
    # C1 consumes canonical T1 events and character identities.
    ("C1", r"/(?:agency_matrix|character_arcs|slot_resolution)/\*/(?:event_ids|choice_event_ids|pressure_event_ids)/\*", (("T1", "major_events"), ("T1", "objects"))),
    ("C1", r"/(?:agency_matrix|character_arcs|information_matrix|slot_resolution)/\*/character_id", (("C1", "profiles"),)),
)


def _reference_descriptor(stage: str, pointer: str) -> tuple[tuple[str, str], ...] | None:
    normalized = _normalized_pointer(pointer)
    for source_stage, pattern, targets in _REF_DESCRIPTORS:
        if stage == source_stage and re.fullmatch(pattern, normalized):
            return targets
    return None


def _is_c1_slot_resolution(
    stage: str,
    pointer: str,
    value: Any,
) -> bool:
    parts = [part for part in pointer.split("/") if part]
    return (
        stage == "C1"
        and len(parts) == 2
        and parts[0] == "slot_resolution"
        and parts[1].isdigit()
        and isinstance(value, Mapping)
        and isinstance(value.get("slot_id"), str)
    )


def _typed_reference_targets(
    identifier: str,
    occurrences: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    targets = copy.deepcopy(list(occurrences))
    if identifier.startswith("SLOT-"):
        return [
            item
            for item in targets
            if item.get("stage") == "C1"
            and item.get("kind") == "slot_resolution"
            and re.fullmatch(
                r"/slot_resolution/[0-9]+",
                item.get("json_pointer", ""),
            )
        ]
    if identifier.startswith("DEV-"):
        return [
            item
            for item in targets
            if item.get("stage") == "C1"
            and item.get("kind") == "development_freedoms"
            and re.fullmatch(
                r"/development_freedoms/[0-9]+",
                item.get("json_pointer", ""),
            )
        ]
    return targets


def _cross_model_index(
    run_id: str,
    baseline: Mapping[str, Any],
    models: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    _validate_capability_occurrence_projection(models["T1"])
    definitions: list[dict[str, Any]] = []
    definition_map: dict[str, list[dict[str, str]]] = {}
    definition_fields: set[tuple[str, str]] = set()
    synthetic_seen: set[tuple[str, str]] = set()
    sources: list[tuple[str, Any]] = [("B0", baseline)]
    sources.extend((stage, models[stage]) for stage in _MODEL_STAGES)
    for stage, model in sources:
        for pointer, value in _walk(model):
            descriptor = _identity_descriptor(stage, pointer, value)
            if descriptor is not None:
                identifier, kind = descriptor
                occurrence = {
                    "stage": stage,
                    "json_pointer": pointer,
                    "kind": kind,
                    "value_sha256": rt.canonical_sha256(value),
                }
                definitions.append({"id": identifier, **occurrence})
                definition_map.setdefault(identifier, []).append(occurrence)
                field = "claim_id" if kind == "line_claim_authority" else (
                    "slot_id" if kind == "slot_resolution" else (
                        "occurrence_id"
                        if kind in {
                            "capability_occurrence",
                            "planned_capability_occurrence",
                        }
                        else "id"
                    )
                )
                definition_fields.add((stage, f"{pointer}/{field}"))
            # E1 operational actor identities are deliberately isolated from
            # C1 character slots. Repeated uses merge into one canonical first
            # binding rather than manufacturing 51 missing characters.
            if (
                stage == "E1" and isinstance(value, Mapping)
                and re.fullmatch(r"/actor_authority_bindings/[0-9]+", pointer)
                and isinstance(value.get("actor_slot_id"), str)
            ):
                slot_id = value["actor_slot_id"]
                key = ("e1_operational_slot", slot_id)
                if key not in synthetic_seen:
                    occurrence = {
                        "stage": "E1", "json_pointer": pointer,
                        "kind": "e1_operational_slot",
                        "value_sha256": rt.canonical_sha256(
                            {"slot_id": slot_id, "kind": "e1_operational_slot"}
                        ),
                    }
                    definitions.append({"id": slot_id, **occurrence})
                    definition_map.setdefault(slot_id, []).append(occurrence)
                    synthetic_seen.add(key)
                definition_fields.add((stage, f"{pointer}/actor_slot_id"))
            if (
                stage == "T1" and isinstance(value, Mapping)
                and re.fullmatch(r"/authority_token_instance_ledger/[0-9]+", pointer)
                and isinstance(value.get("token_instance_id"), str)
            ):
                token_id = value["token_instance_id"]
                occurrence = {
                    "stage": "T1",
                    "json_pointer": pointer,
                    "kind": "authority_token_instance",
                    "value_sha256": rt.canonical_sha256(value),
                }
                definitions.append({"id": token_id, **occurrence})
                definition_map.setdefault(token_id, []).append(occurrence)
                definition_fields.add((stage, f"{pointer}/token_instance_id"))
            allowed_identity = _reference_descriptor(stage, pointer)
            if (
                stage == "E1" and isinstance(value, str)
                and allowed_identity == (("E1", "e1_operational_slot"),)
            ):
                key = ("e1_operational_slot", value)
                if key not in synthetic_seen:
                    occurrence = {
                        "stage": "E1", "json_pointer": pointer,
                        "kind": "e1_operational_slot",
                        "value_sha256": rt.canonical_sha256(
                            {"slot_id": value, "kind": "e1_operational_slot"}
                        ),
                    }
                    definitions.append({"id": value, **occurrence})
                    definition_map.setdefault(value, []).append(occurrence)
                    synthetic_seen.add(key)
    unique_definitions: set[tuple[str, str, str]] = set()
    for item in definitions:
        key = (item["stage"], item["kind"], item["id"])
        if key in unique_definitions:
            _fail(
                "P1_CROSS_REFERENCE_AMBIGUOUS",
                f"{item['stage']}:{item['kind']}:{item['id']}",
            )
        unique_definitions.add(key)
    definitions.sort(key=lambda item: (item["id"], item["stage"], item["json_pointer"]))
    references: list[dict[str, Any]] = []
    for stage, model in sources:
        for pointer, value in _walk(model):
            if not pointer or "/" not in pointer:
                continue
            if (stage, pointer) in definition_fields:
                continue
            allowed = _reference_descriptor(stage, pointer)
            if allowed is None or not isinstance(value, str):
                continue
            field = pointer.rsplit("/", 2)[-2] if pointer.rsplit("/", 1)[-1].isdigit() else pointer.rsplit("/", 1)[-1]
            identifier = value
            target_occurrences = [
                item for item in definition_map.get(identifier, [])
                if (item["stage"], item["kind"]) in allowed
            ]
            if not target_occurrences:
                _fail(
                    "P1_CROSS_REFERENCE_UNRESOLVED",
                    f"{stage}:{pointer} -> {identifier}",
                )
            references.append(
                {
                    "stage": stage,
                    "json_pointer": pointer,
                    "field": field,
                    "target_id": identifier,
                    "target_occurrences": target_occurrences,
                }
            )
    references.sort(
        key=lambda item: (item["stage"], item["json_pointer"], item["target_id"])
    )
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "definitions": definitions,
        "references": references,
    }


def _terminal_development_freedom_ids(
    character_model: Mapping[str, Any],
    index: Mapping[str, Any],
    partition: Mapping[str, Sequence[str]],
) -> list[str]:
    """Validate and return the only freedoms exposed to novel development."""

    freedoms = character_model.get("development_freedoms")
    if not isinstance(freedoms, list) or not freedoms:
        _fail(
            "P1_TERMINAL_FREEDOM_INVALID",
            "C1.development_freedoms must be a non-empty list",
        )
    terminal_ids: list[str] = []
    for position, freedom in enumerate(freedoms):
        if not isinstance(freedom, Mapping):
            _fail(
                "P1_TERMINAL_FREEDOM_INVALID",
                f"C1.development_freedoms/{position} must be an object",
            )
        identifier = freedom.get("id")
        if (
            not isinstance(identifier, str)
            or not identifier.startswith("DEV-")
            or _SOURCE_ID.fullmatch(identifier) is None
        ):
            _fail(
                "P1_TERMINAL_FREEDOM_INVALID",
                f"C1.development_freedoms/{position}.id must be DEV-*",
            )
        terminal_ids.append(identifier)
    if len(set(terminal_ids)) != len(terminal_ids):
        _fail(
            "P1_TERMINAL_FREEDOM_INVALID",
            "C1 development freedom IDs must be unique",
        )
    c1_partition = character_model.get("authority_partition")
    c1_downstream = (
        c1_partition.get("downstream_freedom")
        if isinstance(c1_partition, Mapping)
        else None
    )
    if (
        not isinstance(c1_downstream, list)
        or len(c1_downstream) != len(set(c1_downstream))
        or set(c1_downstream) != set(terminal_ids)
    ):
        _fail(
            "P1_TERMINAL_FREEDOM_INVALID",
            "C1 downstream_freedom must equal C1 development_freedoms IDs",
        )
    if not set(terminal_ids) <= set(partition["downstream_freedom"]):
        _fail(
            "P1_TERMINAL_FREEDOM_INVALID",
            "terminal DEV IDs are absent from the historical authority union",
        )

    definitions_by_id: dict[str, list[Mapping[str, Any]]] = {}
    for definition in index.get("definitions", []):
        if isinstance(definition, Mapping) and isinstance(
            definition.get("id"), str
        ):
            definitions_by_id.setdefault(definition["id"], []).append(definition)
    references_by_pointer = {
        (reference.get("stage"), reference.get("json_pointer")): reference
        for reference in index.get("references", [])
        if isinstance(reference, Mapping)
    }
    for position, freedom in enumerate(freedoms):
        identifier = freedom["id"]
        expected_pointer = f"/development_freedoms/{position}"
        definitions = [
            definition
            for definition in definitions_by_id.get(identifier, [])
            if definition.get("stage") == "C1"
            and definition.get("kind") == "development_freedoms"
            and re.fullmatch(
                r"/development_freedoms/[0-9]+",
                definition.get("json_pointer", ""),
            )
        ]
        if len(definitions) != 1:
            _fail(
                "P1_TERMINAL_FREEDOM_INVALID",
                f"{identifier} must have exactly one typed definition",
            )
        definition = definitions[0]
        if (
            definition.get("stage") != "C1"
            or definition.get("kind") != "development_freedoms"
            or definition.get("json_pointer") != expected_pointer
            or definition.get("value_sha256") != rt.canonical_sha256(freedom)
        ):
            _fail(
                "P1_TERMINAL_FREEDOM_INVALID",
                f"{identifier} is not bound to its exact C1 freedom object",
            )
        subject_ids = freedom.get("subject_ids")
        source_ids = freedom.get("source_ids")
        if (
            not isinstance(subject_ids, list)
            or not subject_ids
            or not all(isinstance(item, str) for item in subject_ids)
            or not isinstance(source_ids, list)
            or not source_ids
            or not all(isinstance(item, str) for item in source_ids)
        ):
            _fail(
                "P1_DEV_REFERENCE_INVALID",
                f"{identifier} requires non-empty subject_ids and source_ids",
            )
        for subject_position, subject_id in enumerate(subject_ids):
            reference = references_by_pointer.get(
                (
                    "C1",
                    f"{expected_pointer}/subject_ids/{subject_position}",
                )
            )
            targets = (
                reference.get("target_occurrences", [])
                if isinstance(reference, Mapping)
                else []
            )
            profile_targets = [
                target
                for target in targets
                if target.get("stage") == "C1"
                and target.get("kind") == "profiles"
                and re.fullmatch(
                    r"/profiles/[0-9]+",
                    target.get("json_pointer", ""),
                )
                is not None
            ]
            if (
                len(profile_targets) != 1
                or reference.get("target_id") != subject_id
            ):
                _fail(
                    "P1_DEV_REFERENCE_INVALID",
                    f"{identifier}.subject_ids/{subject_position} "
                    "must target a C1 profile",
                )
        for source_position, source_id in enumerate(source_ids):
            reference = references_by_pointer.get(
                (
                    "C1",
                    f"{expected_pointer}/source_ids/{source_position}",
                )
            )
            if (
                not isinstance(reference, Mapping)
                or reference.get("target_id") != source_id
                or not reference.get("target_occurrences")
            ):
                _fail(
                    "P1_DEV_REFERENCE_INVALID",
                    f"{identifier}.source_ids/{source_position} is unresolved",
                )
    return sorted(terminal_ids)


def _authority_and_open(
    baseline: Mapping[str, Any],
    models: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    partition: dict[str, set[str]] = {name: set() for name in _PARTITIONS}
    for item in baseline["control_registry"]:
        partition[item["hardness"]].add(item["id"])
    for stage in _MODEL_STAGES:
        source = models[stage].get("authority_partition")
        if not isinstance(source, Mapping):
            _fail("P1_AUTHORITY_INVALID", f"{stage} partition missing")
        for name in _PARTITIONS:
            values = source.get(name)
            if not isinstance(values, list):
                _fail("P1_AUTHORITY_INVALID", f"{stage}.{name}")
            partition[name].update(values)
    for left_index, left in enumerate(_PARTITIONS):
        for right in _PARTITIONS[left_index + 1 :]:
            overlap = partition[left] & partition[right]
            if overlap:
                _fail(
                    "P1_AUTHORITY_CONFLICT",
                    f"{left}/{right}: {sorted(overlap)}",
                )
    open_occurrences: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for stage in _MODEL_STAGES:
        values = models[stage].get("open_items")
        if not isinstance(values, list):
            _fail("P1_OPEN_ITEMS_INVALID", f"{stage} open_items")
        stage_ids: set[str] = set()
        for item in values:
            if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
                _fail("P1_OPEN_ITEMS_INVALID", stage)
            body = copy.deepcopy(dict(item))
            identifier = body["id"]
            if identifier in stage_ids:
                _fail("P1_OPEN_ITEM_CONFLICT", f"{stage}:{identifier}")
            stage_ids.add(identifier)
            open_occurrences.setdefault(identifier, []).append((stage, body))

    baseline_controls: dict[str, Mapping[str, Any]] = {}
    for control in baseline["control_registry"]:
        identifier = control.get("id") if isinstance(control, Mapping) else None
        if not isinstance(identifier, str):
            continue
        if identifier in baseline_controls:
            _fail("P1_OPEN_ITEM_PROJECTION_INVALID", f"B0:{identifier}")
        baseline_controls[identifier] = control

    quality = models["Q1"].get("quality_coverage")
    if not isinstance(quality, Mapping):
        _fail("P1_OPEN_ITEM_PROJECTION_INVALID", "Q1 quality_coverage")
    required = quality.get("required_objects")
    covered_objects = quality.get("covered_objects")
    if not isinstance(required, list) or not isinstance(covered_objects, list):
        _fail("P1_OPEN_ITEM_PROJECTION_INVALID", "Q1 quality objects")

    def require_q1_projection(
        identifier: str, stage: str, body: Mapping[str, Any]
    ) -> None:
        classification = {
            "S1": "s1_obligation",
            "T1": "t1_realization",
        }[stage]
        expected_sha = rt.canonical_sha256(body)
        for label, values in (("required", required), ("covered", covered_objects)):
            matches = [
                value
                for value in values
                if isinstance(value, Mapping)
                and value.get("id") == identifier
                and value.get("stage") == stage
            ]
            if (
                len(matches) != 1
                or matches[0].get("classification") != classification
                or matches[0].get("value_sha256") != expected_sha
            ):
                _fail(
                    "P1_OPEN_ITEM_PROJECTION_INVALID",
                    f"Q1 {label} {stage}:{identifier}",
                )

    open_by_id: dict[str, dict[str, Any]] = {}
    for identifier, occurrences in open_occurrences.items():
        if len(occurrences) == 1:
            open_by_id[identifier] = occurrences[0][1]
            continue
        by_stage = {stage: body for stage, body in occurrences}
        if len(by_stage) != len(occurrences) or set(by_stage) != {"S1", "T1"}:
            _fail("P1_OPEN_ITEM_CONFLICT", identifier)
        s1_body = by_stage["S1"]
        t1_body = by_stage["T1"]
        s1_sources = s1_body.get("source_ids")
        t1_sources = t1_body.get("source_ids")
        if (
            s1_body.get("status") != "author_open"
            or t1_body.get("status") != "author_open"
            or not isinstance(s1_sources, list)
            or not s1_sources
            or s1_sources != t1_sources
            or not all(isinstance(source_id, str) for source_id in s1_sources)
            or len(set(s1_sources)) != len(s1_sources)
            or t1_body.get("question") != "Preserved author-open item."
        ):
            _fail("P1_OPEN_ITEM_PROJECTION_INVALID", identifier)
        for source_id in s1_sources:
            control = baseline_controls.get(source_id)
            if control is None or control.get("hardness") != "author_open":
                _fail(
                    "P1_OPEN_ITEM_PROJECTION_INVALID",
                    f"B0 author-open source {source_id}",
                )
        require_q1_projection(identifier, "S1", s1_body)
        require_q1_projection(identifier, "T1", t1_body)
        open_by_id[identifier] = copy.deepcopy(s1_body)
    covered = {
        source_id
        for item in open_by_id.values()
        for source_id in item.get("source_ids", [])
    }
    missing = set(baseline["open_items"]) - covered
    if missing:
        _fail(
            "P1_OPEN_ITEM_COVERAGE_MISSING",
            f"Q1 allowed author-open controls to disappear: {sorted(missing)}",
        )
    return (
        {name: sorted(partition[name]) for name in _PARTITIONS},
        [open_by_id[key] for key in sorted(open_by_id)],
    )


def _handoff(
    run_id: str,
    *,
    baseline_ref: Mapping[str, str],
    conception_ref: Mapping[str, str],
    partition: Mapping[str, Sequence[str]],
    open_items: Sequence[Mapping[str, Any]],
    terminal_development_freedom_ids: Sequence[str],
) -> dict[str, Any]:
    source_ids = lambda values: sorted(
        {value for value in values if _SOURCE_ID.fullmatch(value)}
    )
    mandatory = source_ids(
        [*partition["author_locked"], *partition["autonomous_owned"]]
    )
    freedoms = sorted(set(terminal_development_freedom_ids))
    if (
        len(freedoms) != len(terminal_development_freedom_ids)
        or any(
            not value.startswith("DEV-")
            or _SOURCE_ID.fullmatch(value) is None
            for value in freedoms
        )
        or not set(freedoms) <= set(partition["downstream_freedom"])
    ):
        _fail(
            "P1_TERMINAL_FREEDOM_INVALID",
            "handoff freedoms must be unique terminal DEV IDs",
        )
    must_ask = source_ids(partition["author_open"])
    open_sources = source_ids(
        [
            source_id
            for item in open_items
            for source_id in item.get("source_ids", [])
        ]
    )
    if not mandatory:
        _fail("P1_HANDOFF_MANDATORY_EMPTY", "no mandatory source control")
    if set(mandatory) & (set(freedoms) | set(must_ask)) or set(freedoms) & set(must_ask):
        _fail("P1_HANDOFF_PARTITION_CONFLICT", "handoff sets overlap")
    if not set(must_ask) <= set(open_sources):
        _fail("P1_HANDOFF_OPEN_MISMATCH", "must_ask is not open")
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "status": "ready",
        "author_control_baseline": copy.deepcopy(dict(baseline_ref)),
        "conception_package": copy.deepcopy(dict(conception_ref)),
        "mandatory_controls": mandatory,
        "development_freedoms": freedoms,
        "must_ask": must_ask,
        "open_items": open_sources,
        "development_entrypoint": {
            "next_stage": "novel-development",
            "instruction": (
                "Read the exact packaged baseline and canonical models; obey "
                "mandatory controls, keep declared freedoms open, and ask before "
                "resolving any must_ask item."
            ),
        },
    }


def _spec(
    baseline: Mapping[str, Any],
    models: Mapping[str, Mapping[str, Any]],
    review: Mapping[str, Any],
    index: Mapping[str, Any],
    partition: Mapping[str, Any],
    open_items: Sequence[Mapping[str, Any]],
) -> str:
    sections: list[tuple[str, Any]] = [("Author control baseline", baseline)]
    sections.extend((f"{stage} canonical model", models[stage]) for stage in _MODEL_STAGES)
    sections.extend(
        (
            ("Q1 independent review", review),
            ("Cross-model index", index),
            ("Authority partition", partition),
            ("Open items", list(open_items)),
        )
    )
    chunks = ["# Novel conception specification", ""]
    for title, value in sections:
        chunks.extend((f"## {title}", "", "```json", rt.canonical_json(value), "```", ""))
    return "\n".join(chunks)


def _traceability(index: Mapping[str, Any]) -> str:
    lines = [
        "# Traceability matrix",
        "",
        "## Definitions",
        "",
        "| ID | Stage | JSON pointer | Kind | Value SHA-256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in index["definitions"]:
        lines.append(
            f"| `{item['id']}` | {item['stage']} | `{item['json_pointer']}` | "
            f"{item['kind']} | `{item['value_sha256']}` |"
        )
    lines.extend(
        (
            "",
            "## References",
            "",
            "| Stage | JSON pointer | Field | Target ID | Target occurrences |",
            "| --- | --- | --- | --- | --- |",
        )
    )
    for item in index["references"]:
        targets = ", ".join(
            f"{entry['stage']}:{entry['json_pointer']}"
            for entry in item["target_occurrences"]
        )
        lines.append(
            f"| {item['stage']} | `{item['json_pointer']}` | {item['field']} | "
            f"`{item['target_id']}` | {targets} |"
        )
    return "\n".join(lines) + "\n"


def _validation(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "P1",
        "verdict": "ready",
        "checks": [
            "exact-B0-S1-W1-E1-T1-C1-Q1-ready-lineage",
            "q1-full-quality-coverage-and-zero-unresolved-blockers",
            "lossless-baseline-six-artifacts-five-models-review",
            "cross-model-index-recalculation",
            "authority-and-open-item-preservation",
            "acyclic-package-handoff-binding",
            "deterministic-spec-and-traceability",
            "manifest-implementation-completion-binding",
        ],
        "errors": [],
    }


def _check_boundary(root: Path) -> None:
    for _, relative in _iter_files(root):
        if relative in _ROOT_FILES or any(
            relative.startswith(prefix) for prefix in _ROOT_PREFIXES
        ):
            continue
        _fail("P1_PACKAGE_BOUNDARY_INVALID", relative)


def _check_source_snapshot_boundary(root: Path) -> None:
    source_root = root / "source-packages"
    if not source_root.is_dir():
        _fail(
            "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID",
            "source-packages directory is missing",
        )
    root_files = {
        item.relative_to(root).as_posix()
        for item in source_root.iterdir()
        if item.is_file()
    }
    stage_directories = {
        item.name for item in source_root.iterdir() if item.is_dir()
    }
    if root_files or stage_directories != set(STAGES):
        _fail(
            "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID",
            "source-packages must contain exactly the seven stage directories",
        )
    expected_paths = {
        f"source-packages/{stage}/{relative}"
        for stage in STAGES
        for _, relative in _iter_files(source_root / stage)
    }
    actual_paths = {
        f"source-packages/{relative}"
        for _, relative in _iter_files(source_root)
    }
    if actual_paths != expected_paths:
        _fail(
            "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID",
            "source snapshot files are not the exact seven-stage union",
        )


def _copy_exact(source: Path, target: Path) -> None:
    os.makedirs(_long_name(target.parent), exist_ok=True)
    shutil.copyfile(_long_name(source), _long_name(target))
    if _long_sha256(source) != _long_sha256(target):
        _fail("P1_COPY_DRIFT", str(source))


def _copytree_exact(source: Path, target: Path) -> None:
    for path, relative in _iter_files(source):
        _copy_exact(path, target / PurePosixPath(relative))


def _expected_materialized(
    root: Path,
    source_roots: Mapping[str, Path],
    models: Mapping[str, Mapping[str, Any]],
) -> tuple[
    dict[str, str],
    list[dict[str, Any]],
    dict[str, dict[str, str]],
    dict[str, str],
]:
    baseline_ref = rt.artifact_reference(
        root / "author-control-baseline.json", root=root
    )
    design_index = _read(
        root / "authoritative-design-index.json", "P1_DESIGN_INDEX_INVALID"
    )
    design_refs = {
        item["domain"]: item["materialized"] for item in design_index["artifacts"]
    }
    canonical_refs = {
        stage: rt.artifact_reference(
            root / "canonical-models" / CANONICAL_NAMES[stage], root=root
        )
        for stage in _MODEL_STAGES
    }
    review_ref = rt.artifact_reference(
        root / "review" / CANONICAL_NAMES["Q1"], root=root
    )
    return baseline_ref, design_index["artifacts"], canonical_refs, review_ref


def validate_p1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_boundary(root)
    _check_source_snapshot_boundary(root)
    source_roots = {stage: root / "source-packages" / stage for stage in STAGES}
    gate_data = _read(root / "input-gate.json", "P1_GATE_INVALID")
    gate_ref = {
        "path": "P1/input-gate.json",
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    gate = rt.SealedDocument(data=gate_data, reference=gate_ref)
    models, _, _ = _context(
        source_roots,
        input_gate=gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    package = _read(
        root / "novel-conception-package.json", "P1_PACKAGE_INVALID"
    )
    handoff = _read(
        root / "development-handoff.json", "P1_HANDOFF_INVALID"
    )
    manifest = _read(root / "package-manifest.json", "P1_MANIFEST_INVALID")
    stored_validation = _read(
        root / "validation.json", "P1_VALIDATION_INVALID"
    )
    try:
        contract_runtime.validate(package, "novel-conception-package.schema.json")
        contract_runtime.validate(handoff, "development-handoff.schema.json")
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        _verify_manifest_long(manifest, root=root)
    except Exception as error:
        _fail("P1_SCHEMA_OR_MANIFEST_INVALID", str(error))
    published_gate_ref = package.get("input_gate")
    if (
        not isinstance(published_gate_ref, Mapping)
        or published_gate_ref.get("sha256") != gate_ref["sha256"]
        or not str(published_gate_ref.get("path", "")).endswith(
            "/input-gate.json"
        )
    ):
        _fail("P1_GATE_INVALID", "package gate binding")
    if (root / "author-control-baseline.json").read_bytes() != (
        source_roots["B0"] / CANONICAL_NAMES["B0"]
    ).read_bytes():
        _fail("P1_BASELINE_DRIFT", "top-level baseline is not byte-exact")
    baseline = models["B0"]
    design_index = _read(
        root / "authoritative-design-index.json", "P1_DESIGN_INDEX_INVALID"
    )
    expected_design_entries = []
    for entry in sorted(baseline["design_artifacts"], key=lambda item: item["domain"]):
        source = rt.verify_artifact_reference(entry["artifact"], root=source_roots["B0"])
        target = root / "authoritative-design-artifacts" / (
            f"{entry['domain']}-{source.name}"
        )
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            _fail("P1_DESIGN_ARTIFACT_DRIFT", entry["domain"])
        expected_design_entries.append(
            {
                "domain": entry["domain"],
                "baseline_artifact": copy.deepcopy(entry["artifact"]),
                "materialized": rt.artifact_reference(target, root=root),
            }
        )
    if design_index != {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "artifacts": expected_design_entries,
    }:
        _fail("P1_DESIGN_INDEX_INVALID", "not an exact six-artifact index")
    design_paths = {
        item["materialized"]["path"] for item in expected_design_entries
    }
    actual_design_paths = {
        path.relative_to(root).as_posix()
        for path, _ in _iter_files(root / "authoritative-design-artifacts")
    }
    if actual_design_paths != design_paths:
        _fail(
            "P1_PACKAGE_BOUNDARY_INVALID",
            "authoritative design artifacts are not exact",
        )
    for stage in _MODEL_STAGES:
        if (
            root / "canonical-models" / CANONICAL_NAMES[stage]
        ).read_bytes() != (
            source_roots[stage] / CANONICAL_NAMES[stage]
        ).read_bytes():
            _fail("P1_CANONICAL_DRIFT", stage)
    expected_canonical_paths = {
        f"canonical-models/{CANONICAL_NAMES[stage]}"
        for stage in _MODEL_STAGES
    }
    actual_canonical_paths = {
        path.relative_to(root).as_posix()
        for path, _ in _iter_files(root / "canonical-models")
    }
    if actual_canonical_paths != expected_canonical_paths:
        _fail(
            "P1_PACKAGE_BOUNDARY_INVALID",
            "canonical model materialization is not exact",
        )
    if (root / "review" / CANONICAL_NAMES["Q1"]).read_bytes() != (
        source_roots["Q1"] / CANONICAL_NAMES["Q1"]
    ).read_bytes():
        _fail("P1_REVIEW_DRIFT", "Q1 review changed")
    actual_review_paths = {
        path.relative_to(root).as_posix()
        for path, _ in _iter_files(root / "review")
    }
    if actual_review_paths != {f"review/{CANONICAL_NAMES['Q1']}"}:
        _fail(
            "P1_PACKAGE_BOUNDARY_INVALID",
            "review materialization is not exact",
        )
    index = _cross_model_index(
        baseline["run_id"], baseline, models
    )
    stored_index = _read(
        root / "cross-model-index.json", "P1_CROSS_INDEX_INVALID"
    )
    if stored_index != index:
        _fail("P1_CROSS_INDEX_INVALID", "index is not reproducible")
    partition, open_items = _authority_and_open(baseline, models)
    terminal_development_freedom_ids = _terminal_development_freedom_ids(
        models["C1"], index, partition
    )
    baseline_ref, design_entries, canonical_refs, review_ref = _expected_materialized(
        root, source_roots, models
    )
    expected_package = {
        "schema_version": "2.0",
        "skill": "novel-conception-deliverable-assembler",
        "stage": "P1",
        "run_id": baseline["run_id"],
        "status": "ready",
        "input_gate": published_gate_ref,
        "author_control_baseline": baseline_ref,
        "authoritative_design_artifacts": [
            item["materialized"] for item in design_entries
        ],
        "canonical_models": canonical_refs,
        "review": review_ref,
        "quality_admission": _quality_admission(models["Q1"], review_ref),
        "cross_model_index": index,
        "authority_partition": partition,
        "open_items": open_items,
        "development_handoff": {"path": "development-handoff.json"},
    }
    if package != expected_package:
        _fail("P1_PACKAGE_DRIFT", "canonical package is not deterministic")
    expected_handoff = _handoff(
        baseline["run_id"],
        baseline_ref=baseline_ref,
        conception_ref=rt.artifact_reference(
            root / "novel-conception-package.json", root=root
        ),
        partition=partition,
        open_items=open_items,
        terminal_development_freedom_ids=terminal_development_freedom_ids,
    )
    if handoff != expected_handoff:
        _fail("P1_HANDOFF_DRIFT", "handoff is not deterministic")
    if (root / "novel-conception-spec.md").read_text(encoding="utf-8") != _spec(
        baseline, models, models["Q1"], index, partition, open_items
    ):
        _fail("P1_SPEC_DRIFT", "spec differs from canonical inputs")
    if (root / "traceability-matrix.md").read_text(encoding="utf-8") != _traceability(index):
        _fail("P1_TRACEABILITY_DRIFT", "traceability differs from index")
    execution = _read(
        root / "assembly-execution.json", "P1_EXECUTION_INVALID"
    )
    expected_outputs = {
        name: rt.artifact_reference(root / name, root=root)
        for name in (
            "novel-conception-package.json",
            "author-control-baseline.json",
            "authoritative-design-index.json",
            "novel-conception-spec.md",
            "cross-model-index.json",
            "traceability-matrix.md",
            "development-handoff.json",
        )
    }
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping)
    }
    try:
        _, catalog = stage_identity.validate_stage_catalog(
            stage="P1",
            records=execution.get("implementation_catalog"),
            package_root=root,
            current_paths=_implementation_paths(),
            verify_artifact_reference=rt.verify_artifact_reference,
            sha256_file=rt.sha256_file,
        )
    except stage_identity.StageImplementationIdentityError as error:
        _fail("P1_IMPLEMENTATION_STALE", str(error))
    implementation_refs = [catalog[key] for key in sorted(catalog)]
    actual_implementation_paths = {
        path.relative_to(root).as_posix()
        for path, _ in _iter_files(root / "implementation")
    }
    if actual_implementation_paths != {
        reference["path"] for reference in implementation_refs
    }:
        _fail(
            "P1_PACKAGE_BOUNDARY_INVALID",
            "implementation snapshot is not exact",
        )
    expected_execution = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "P1",
        "operation": "deterministic-p1-assembly",
        "input_gate": published_gate_ref,
        "baseline_completion": gate_data["baseline_completion"],
        "upstream_completions": gate_data["upstream_completions"],
        "source_packages": {
            stage: {
                "canonical": rt.artifact_reference(
                    source_roots[stage] / CANONICAL_NAMES[stage], root=root
                ),
                "manifest": rt.artifact_reference(
                    source_roots[stage] / "package-manifest.json", root=root
                ),
                "completion": rt.artifact_reference(
                    source_roots[stage] / "stage-completion.json", root=root
                ),
            }
            for stage in STAGES
        },
        "outputs": expected_outputs,
        "implementation": implementation_refs,
        "implementation_catalog": [
            {"identity": identity, "artifact": catalog[identity]}
            for identity in sorted(catalog)
        ],
    }
    if execution != expected_execution:
        _fail("P1_EXECUTION_INVALID", "execution is not an exact binding")
    if stored_validation != _validation(baseline["run_id"]):
        _fail("P1_VALIDATION_STALE", "validation is not reproducible")
    roles = manifest.get("artifact_roles", {})
    expected_roles = {
        "conception_package": expected_outputs["novel-conception-package.json"],
        "author_control_baseline": expected_outputs["author-control-baseline.json"],
        "authoritative_design_index": expected_outputs["authoritative-design-index.json"],
        "spec": expected_outputs["novel-conception-spec.md"],
        "cross_model_index": expected_outputs["cross-model-index.json"],
        "traceability": expected_outputs["traceability-matrix.md"],
        "development_handoff": expected_outputs["development-handoff.json"],
        "execution_record": rt.artifact_reference(
            root / "assembly-execution.json", root=root
        ),
    }
    if (
        manifest.get("run_id") != baseline["run_id"]
        or manifest.get("stage") != "P1"
        or manifest.get("package_profile") != "conception-package"
        or manifest.get("verdict") != "ready"
        or roles != expected_roles
        or manifest.get("validation")
        != rt.artifact_reference(root / "validation.json", root=root)
        or manifest.get("implementation") != implementation_refs
    ):
        _fail("P1_MANIFEST_INVALID", "profile/roles/validation")
    actual_files = {
        ref["path"]: ref
        for ref in _tree_inventory(root)
        if ref["path"] not in {"package-manifest.json", "stage-completion.json"}
    }
    if {item["path"]: item for item in manifest["files"]} != actual_files:
        _fail("P1_MANIFEST_INVALID", "files are not exact")
    if require_completion:
        completion = _read(
            root / "stage-completion.json", "P1_COMPLETION_INVALID"
        )
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("P1_COMPLETION_INVALID", str(error))
        completion_gate = completion.get("input_gate")
        if (
            not isinstance(completion_gate, Mapping)
            or completion_gate != published_gate_ref
            or not str(completion_gate.get("path", "")).endswith(
                "/input-gate.json"
            )
        ):
            _fail("P1_COMPLETION_INVALID", "input gate binding")
        if completion != {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "P1",
            "status": "ready",
            "manifest": {
                "path": "P1/package-manifest.json",
                "sha256": rt.sha256_file(root / "package-manifest.json"),
            },
            "validation": {
                "path": "P1/validation.json",
                "sha256": rt.sha256_file(root / "validation.json"),
            },
            "input_gate": completion_gate,
            "state_before": gate_data["run_state"],
            "previous_stage_completions": gate_data["upstream_completions"],
            "return_binding": gate_data["return_binding"],
        }:
            _fail("P1_COMPLETION_INVALID", "completion binding")
    return copy.deepcopy(stored_validation)


def _require_current_p1_gate(
    *,
    coordinator: Any,
    input_gate: Any,
    active_return_request: Any | None,
) -> None:
    try:
        expected = coordinator.build_input_gate(
            "P1",
            input_gate.reference["path"],
            active_return_request=active_return_request,
        )
        if not isinstance(expected, rt.SealedDocument):
            raise TypeError(
                "coordinator.build_input_gate did not return SealedDocument"
            )
    except rt.CoordinatorError:
        raise
    except Exception as error:
        _fail("P1_GATE_INVALID", f"current coordinator gate: {error}")
    if expected.data != input_gate.data or expected.reference != input_gate.reference:
        _fail(
            "P1_GATE_INVALID",
            "input gate is not the exact current coordinator P1 gate",
        )


def _is_exact_p1_successor(
    *,
    coordinator: Any,
    input_gate: Any,
    completion: Any,
    next_state_path: str,
) -> bool:
    """Recognize the persisted successor supported by coordinator replay."""
    if not isinstance(coordinator, rt.AutonomousCoordinator):
        return False
    state = coordinator.state
    state_reference = coordinator.state_reference
    return (
        state.get("previous_state") == input_gate.data.get("run_state")
        and state.get("current_stage_completions", {}).get("P1")
        == completion.reference
        and state_reference.get("path") == next_state_path
    )


def _require_unchanged_inventory(
    roots: Mapping[str, Path],
    expected: Mapping[str, list[dict[str, str]]],
) -> None:
    current = {
        stage: _tree_inventory(root)
        for stage, root in roots.items()
    }
    if current != expected:
        _fail("P1_INPUT_MUTATED", "input package inventory changed")


def _recover_existing_p1(
    destination: Path,
    *,
    roots: Mapping[str, Path],
    original_inventory: Mapping[str, list[dict[str, str]]],
    coordinator: Any,
    input_gate: Any,
    next_state_path: str,
    active_return_request: Any | None,
    runtime: Any,
) -> P1RunReceipt:
    before = _tree_inventory(destination)
    validate_p1_package(destination, runtime=runtime)
    gate_data = _read(
        destination / "input-gate.json",
        "P1_RECOVERY_GATE_MISMATCH",
    )
    gate_reference = {
        "path": "P1/input-gate.json",
        "sha256": rt.sha256_file(destination / "input-gate.json"),
    }
    if (
        gate_data != input_gate.data
        or gate_reference["sha256"] != input_gate.reference.get("sha256")
        or not str(input_gate.reference.get("path", "")).endswith(
            "/input-gate.json"
        )
    ):
        _fail(
            "P1_RECOVERY_GATE_MISMATCH",
            "existing P1 does not bind the current sealed input gate",
        )
    for stage, source in roots.items():
        embedded = destination / "source-packages" / stage
        if _tree_inventory(embedded) != _tree_inventory(source):
            _fail(
                "P1_RECOVERY_SOURCE_MISMATCH",
                f"existing P1 source snapshot differs from current {stage}",
            )
    completion_data = _read(
        destination / "stage-completion.json",
        "P1_COMPLETION_INVALID",
    )
    completion = rt.seal_stage_document(
        completion_data,
        "P1",
        "P1/stage-completion.json",
    )
    if completion.reference["sha256"] != rt.sha256_file(
        destination / "stage-completion.json"
    ):
        _fail(
            "P1_COMPLETION_INVALID",
            "existing completion is not the canonical sealed document",
        )
    if not _is_exact_p1_successor(
        coordinator=coordinator,
        input_gate=input_gate,
        completion=completion,
        next_state_path=next_state_path,
    ):
        _require_current_p1_gate(
            coordinator=coordinator,
            input_gate=input_gate,
            active_return_request=active_return_request,
        )
    conception_package = _read(
        destination / "novel-conception-package.json",
        "P1_PACKAGE_INVALID",
    )
    manifest = _read(
        destination / "package-manifest.json",
        "P1_MANIFEST_INVALID",
    )
    if before != _tree_inventory(destination):
        _fail(
            "P1_RECOVERY_OUTPUT_MUTATED",
            "existing P1 changed during recovery validation",
        )
    _require_unchanged_inventory(roots, original_inventory)
    transition = coordinator.accept_stage_completion(
        gate=input_gate,
        completion=completion,
        next_state_path=next_state_path,
        active_return_request=active_return_request,
    )
    return P1RunReceipt(
        package_root=destination,
        conception_package=copy.deepcopy(conception_package),
        manifest=copy.deepcopy(manifest),
        completion=completion,
        transition=transition,
        replayed=True,
    )


def run_p1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
    review_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    logical_package_path: str = "P1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> P1RunReceipt:
    destination = Path(package_root).resolve()
    if logical_package_path != "P1":
        _fail(
            "P1_PATH_INVALID",
            "the formal stage logical_package_path must be exactly P1",
        )
    contract_runtime = runtime or rt.ContractRuntime()
    gate_data = input_gate.data
    if gate_data.get("entry_mode") == "forward":
        if active_return_request is not None:
            _fail(
                "P1_GATE_INVALID",
                "forward entry cannot carry an active return body",
            )
    elif gate_data.get("entry_mode") == "return_resolution":
        binding = gate_data.get("return_binding")
        if (
            active_return_request is None
            or not isinstance(binding, Mapping)
            or active_return_request.reference
            != gate_data.get("active_return")
            or active_return_request.reference
            != binding.get("return_request")
            or active_return_request.data.get("return_id")
            != binding.get("return_id")
        ):
            _fail(
                "P1_GATE_INVALID",
                "active return body does not match the sealed gate binding",
            )
    roots = _package_roots(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        character_package=character_package,
        review_package=review_package,
    )
    original_inventory = {
        stage: _tree_inventory(root) for stage, root in roots.items()
    }
    if destination.exists():
        return _recover_existing_p1(
            destination,
            roots=roots,
            original_inventory=original_inventory,
            coordinator=coordinator,
            input_gate=input_gate,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
            runtime=contract_runtime,
        )
    models, _, _ = _context(
        roots, input_gate=input_gate, runtime=contract_runtime
    )
    baseline = models["B0"]
    _require_current_p1_gate(
        coordinator=coordinator,
        input_gate=input_gate,
        active_return_request=active_return_request,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        for stage, source in roots.items():
            if _tree_inventory(source) != original_inventory[stage]:
                _fail("P1_INPUT_MUTATED", f"{stage} changed before snapshot")
            _copytree_exact(source, staging / "source-packages" / stage)
            if _tree_inventory(source) != original_inventory[stage]:
                _fail("P1_INPUT_MUTATED", f"{stage} changed during snapshot")
        _check_source_snapshot_boundary(staging)
        _write(staging / "input-gate.json", input_gate.data)
        _copy_exact(
            roots["B0"] / CANONICAL_NAMES["B0"],
            staging / "author-control-baseline.json",
        )
        design_entries = []
        for entry in sorted(
            baseline["design_artifacts"], key=lambda item: item["domain"]
        ):
            source = rt.verify_artifact_reference(entry["artifact"], root=roots["B0"])
            target = staging / "authoritative-design-artifacts" / (
                f"{entry['domain']}-{source.name}"
            )
            _copy_exact(source, target)
            design_entries.append(
                {
                    "domain": entry["domain"],
                    "baseline_artifact": copy.deepcopy(entry["artifact"]),
                    "materialized": rt.artifact_reference(target, root=staging),
                }
            )
        _write(
            staging / "authoritative-design-index.json",
            {
                "schema_version": "2.0",
                "run_id": baseline["run_id"],
                "artifacts": design_entries,
            },
        )
        canonical_refs = {}
        for stage in _MODEL_STAGES:
            target = staging / "canonical-models" / CANONICAL_NAMES[stage]
            _copy_exact(roots[stage] / CANONICAL_NAMES[stage], target)
            canonical_refs[stage] = rt.artifact_reference(target, root=staging)
        review_target = staging / "review" / CANONICAL_NAMES["Q1"]
        _copy_exact(roots["Q1"] / CANONICAL_NAMES["Q1"], review_target)
        review_ref = rt.artifact_reference(review_target, root=staging)
        baseline_ref = rt.artifact_reference(
            staging / "author-control-baseline.json", root=staging
        )
        index = _cross_model_index(baseline["run_id"], baseline, models)
        partition, open_items = _authority_and_open(baseline, models)
        terminal_development_freedom_ids = _terminal_development_freedom_ids(
            models["C1"], index, partition
        )
        _write(staging / "cross-model-index.json", index)
        package = {
            "schema_version": "2.0",
            "skill": "novel-conception-deliverable-assembler",
            "stage": "P1",
            "run_id": baseline["run_id"],
            "status": "ready",
            "input_gate": copy.deepcopy(input_gate.reference),
            "author_control_baseline": baseline_ref,
            "authoritative_design_artifacts": [
                item["materialized"] for item in design_entries
            ],
            "canonical_models": canonical_refs,
            "review": review_ref,
            "quality_admission": _quality_admission(
                models["Q1"], review_ref
            ),
            "cross_model_index": index,
            "authority_partition": partition,
            "open_items": open_items,
            "development_handoff": {"path": "development-handoff.json"},
        }
        contract_runtime.validate(
            package, "novel-conception-package.schema.json"
        )
        _write(staging / "novel-conception-package.json", package)
        handoff = _handoff(
            baseline["run_id"],
            baseline_ref=baseline_ref,
            conception_ref=rt.artifact_reference(
                staging / "novel-conception-package.json", root=staging
            ),
            partition=partition,
            open_items=open_items,
            terminal_development_freedom_ids=terminal_development_freedom_ids,
        )
        contract_runtime.validate(handoff, "development-handoff.schema.json")
        _write(staging / "development-handoff.json", handoff)
        (staging / "novel-conception-spec.md").write_text(
            _spec(baseline, models, models["Q1"], index, partition, open_items),
            encoding="utf-8",
            newline="",
        )
        (staging / "traceability-matrix.md").write_text(
            _traceability(index), encoding="utf-8", newline=""
        )
        implementation_refs = []
        implementation_catalog = []
        for identity, source in sorted(_implementation_paths().items()):
            target = staging / "implementation" / identity
            _copy_exact(source, target)
            ref = rt.artifact_reference(target, root=staging)
            implementation_refs.append(ref)
            implementation_catalog.append({"identity": identity, "artifact": ref})
        outputs = {
            name: rt.artifact_reference(staging / name, root=staging)
            for name in (
                "novel-conception-package.json",
                "author-control-baseline.json",
                "authoritative-design-index.json",
                "novel-conception-spec.md",
                "cross-model-index.json",
                "traceability-matrix.md",
                "development-handoff.json",
            )
        }
        execution = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "P1",
            "operation": "deterministic-p1-assembly",
            "input_gate": copy.deepcopy(input_gate.reference),
            "baseline_completion": copy.deepcopy(
                input_gate.data["baseline_completion"]
            ),
            "upstream_completions": copy.deepcopy(
                input_gate.data["upstream_completions"]
            ),
            "source_packages": {
                stage: {
                    "canonical": rt.artifact_reference(
                        staging / "source-packages" / stage / CANONICAL_NAMES[stage],
                        root=staging,
                    ),
                    "manifest": rt.artifact_reference(
                        staging / "source-packages" / stage / "package-manifest.json",
                        root=staging,
                    ),
                    "completion": rt.artifact_reference(
                        staging / "source-packages" / stage / "stage-completion.json",
                        root=staging,
                    ),
                }
                for stage in STAGES
            },
            "outputs": outputs,
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
        }
        _write(staging / "assembly-execution.json", execution)
        _write(staging / "validation.json", _validation(baseline["run_id"]))
        files = [
            ref
            for ref in _tree_inventory(staging)
            if ref["path"] not in {"package-manifest.json", "stage-completion.json"}
        ]
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "P1",
            "package_profile": "conception-package",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "conception_package": by_path["novel-conception-package.json"],
                "author_control_baseline": by_path["author-control-baseline.json"],
                "authoritative_design_index": by_path[
                    "authoritative-design-index.json"
                ],
                "spec": by_path["novel-conception-spec.md"],
                "cross_model_index": by_path["cross-model-index.json"],
                "traceability": by_path["traceability-matrix.md"],
                "development_handoff": by_path["development-handoff.json"],
                "execution_record": by_path["assembly-execution.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        _verify_manifest_long(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_p1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "P1",
            "status": "ready",
            "manifest": {
                "path": _logical(logical_package_path, "package-manifest.json"),
                "sha256": rt.sha256_file(staging / "package-manifest.json"),
            },
            "validation": {
                "path": _logical(logical_package_path, "validation.json"),
                "sha256": rt.sha256_file(staging / "validation.json"),
            },
            "input_gate": copy.deepcopy(input_gate.reference),
            "state_before": copy.deepcopy(input_gate.data["run_state"]),
            "previous_stage_completions": copy.deepcopy(
                input_gate.data["upstream_completions"]
            ),
            "return_binding": copy.deepcopy(input_gate.data["return_binding"]),
        }
        contract_runtime.validate(
            completion_data, "stage-completion.schema.json"
        )
        sealed = rt.seal_stage_document(
            completion_data,
            "P1",
            _logical(logical_package_path, "stage-completion.json"),
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_p1_package(staging, runtime=contract_runtime)
        if original_inventory != {
            stage: _tree_inventory(root) for stage, root in roots.items()
        }:
            _fail("P1_INPUT_MUTATED", "assembly changed an input package")
        try:
            staging.replace(destination)
        except OSError:
            if not destination.exists():
                raise
            shutil.rmtree(temp_parent, ignore_errors=True)
            return _recover_existing_p1(
                destination,
                roots=roots,
                original_inventory=original_inventory,
                coordinator=coordinator,
                input_gate=input_gate,
                next_state_path=next_state_path,
                active_return_request=active_return_request,
                runtime=contract_runtime,
            )
        published_inventory = _tree_inventory(destination)
        validate_p1_package(destination, runtime=contract_runtime)
        if published_inventory != _tree_inventory(destination):
            _fail(
                "P1_RECOVERY_OUTPUT_MUTATED",
                "published P1 changed during destination validation",
            )
        _require_unchanged_inventory(roots, original_inventory)
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=sealed,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
        )
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return P1RunReceipt(
        package_root=destination,
        conception_package=copy.deepcopy(package),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
        replayed=False,
    )


__all__ = [
    "STAGES",
    "UPSTREAM_STAGES",
    "CANONICAL_NAMES",
    "P1Error",
    "P1RunReceipt",
    "run_p1",
    "validate_p1_package",
]
