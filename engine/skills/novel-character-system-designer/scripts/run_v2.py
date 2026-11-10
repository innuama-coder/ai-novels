"""Production C1 runner for autonomous novel-conception V2."""

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
import os
import re
import shutil
import tempfile
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
stage_identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)
s1_runtime = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
w1_runtime = importlib.import_module(
    "skills.novel-world-model-designer.scripts.run_v2"
)
e1_runtime = importlib.import_module(
    "skills.novel-environment-system-designer.scripts.run_v2"
)
t1_runtime = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.run_v2"
)
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_S1_SKILL = _REPO / "skills" / "novel-storyline-architecture-designer"
_W1_SKILL = _REPO / "skills" / "novel-world-model-designer"
_E1_SKILL = _REPO / "skills" / "novel-environment-system-designer"
_T1_SKILL = _REPO / "skills" / "novel-event-timeline-designer"
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"

PHASES = (
    "character-demand-scan",
    "slot-resolution-and-profiles",
    "agency-and-relationships",
    "cross-model-cast-test",
    "final-character-model",
)
PHASE_FIELDS = {
    "character-demand-scan": ("character_demands",),
    "slot-resolution-and-profiles": (
        "design_decisions",
        "slot_resolution",
        "profiles",
    ),
    "agency-and-relationships": (
        "responsibility_matrix",
        "agency_matrix",
        "information_matrix",
        "character_arcs",
        "relationships",
        "three_layer_networks",
    ),
    "cross-model-cast-test": (
        "storyline_cast_coverage",
        "event_cast_coverage",
        "aftermath_responsibility",
        "development_freedoms",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-character-model": ("model",),
}
_FORBIDDEN_MODEL_KEYS = {
    "storylines",
    "world_model",
    "environment_system",
    "event_timeline",
    "major_events",
    "causal_edges",
    "scenes",
    "scene_text",
    "prose",
    "biographies",
}
_FORBIDDEN_NESTED_KEYS = {
    "biography",
    "backstory_prose",
    "inner_monologue",
    "scene_text",
    "dialogue",
    "camera",
    "chapter",
    "chapter_plan",
}
_ALLOWED_ROOT_FILES = {
    "input-gate.json",
    "character-system.json",
    "generation-session.json",
    "generation-evidence-index.json",
    "execution-record.json",
    "character-preview.md",
    "validation.json",
    "package-manifest.json",
    "stage-completion.json",
}
_ALLOWED_SOURCE_PREFIXES = (
    "sources/B0/",
    "sources/S1/",
    "sources/W1/",
    "sources/E1/",
    "sources/T1/",
)
_CLASS_TOKEN = re.compile(r"^\[CLASS:(core|support)\]\s+(.+)$")
_BOUNDARY_TOKEN = re.compile(r"^\[TYPE:(blind-spot|hard-boundary)\]\s+(.+)$")
_DEMAND_KIND_TOKEN = re.compile(
    r"^\[KIND:(decision|information|capability|counteraction|"
    r"relationship-pressure|action|aftermath)\]"
)
_SLOT_TOKEN = re.compile(r"\[SLOT:(SLOT-[A-Za-z0-9._-]+)\]")
_EVENT_ROLE_TOKEN = re.compile(r"\[EVENT_ROLE:(participant|initiator|counter)\]")
_ACTION_TOKEN = re.compile(r"^\[ACTION_SHA256:([0-9a-f]{64})\]\s+(.+)$")
_COUNTER_TOKEN = re.compile(r"^\[COUNTER_EVENT:(EV-[A-Za-z0-9._-]+)\]\s+(.+)$")
_AGENCY_INIT_TOKEN = re.compile(
    r"\[INIT_ACTION:(EV-[A-Za-z0-9._-]+):([0-9a-f]{64})\]"
)
_AGENCY_COUNTER_TOKEN = re.compile(
    r"\[COUNTER_PRESSURE:(EV-[A-Za-z0-9._-]+):([0-9a-f]{64})\]"
)
_PROVIDER_TOKEN = re.compile(r"^\[PROVIDER:([A-Za-z0-9._-]+)\]\s+(.+)$")
_ENV_TOKEN = re.compile(r"^\[ENV_ACCESS:(ENV-[A-Za-z0-9._-]+)\]\s+(.+)$")
_KNOWN_TOKEN = re.compile(
    r"^\[KNOWN_AFTER:([A-Za-z0-9._-]+):(EV-[A-Za-z0-9._-]+)\]"
    r"\[BEFORE_SHA256:([0-9a-f]{64})\]\[AFTER_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_UNKNOWN_TOKEN = re.compile(
    r"^\[UNKNOWN_BEFORE:([A-Za-z0-9._-]+):(EV-[A-Za-z0-9._-]+)\]"
    r"\[BEFORE_SHA256:([0-9a-f]{64})\]\[AFTER_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_REL_LEVER_TOKEN = re.compile(r"^\[REL:(REL-[A-Za-z0-9._-]+)\]\s+(.+)$")
_REL_FUNCTION_TOKEN = re.compile(
    r"^\[FUNCTION:(direct|institutional|contextual|aftermath)\]\s+(.+)$"
)
_GOAL_HASH_TOKEN = re.compile(r"^\[GOAL_SHA256:([0-9a-f]{64})\]$")
_VALUE_HASH_TOKEN = re.compile(r"^\[VALUE_SHA256:([0-9a-f]{64})\]$")
_CORE_EVIDENCE_TOKEN = re.compile(
    r"^\[CORE_EVIDENCE_SHA256:([0-9a-f]{64})\]\s+(.+)$"
)
_MERGE_TOKEN = re.compile(r"\[MERGE_SLOTS_SHA256:([0-9a-f]{64})\]")
_DEMAND_BLOCK_TOKEN = re.compile(
    r"\[DEMAND:(CHD-[A-Za-z0-9._-]+):([0-9a-f]{64})\]"
    r"(.*?)\[/DEMAND\]",
    re.DOTALL,
)
_DEMAND_EFFECT_TOKEN = re.compile(
    r"\[DEMAND_EFFECT:(CHD-[A-Za-z0-9._-]+):([0-9a-f]{64}):"
    r"(goal|boundary)\]\s+(.+)"
)
_DEMAND_BINDING_TOKEN = re.compile(
    r"^\[DEMAND_SHA256:(CHD-[A-Za-z0-9._-]+):([0-9a-f]{64})\]$"
)
_DUTY_BINDING_TOKEN = re.compile(r"\[DUTY_SHA256:([0-9a-f]{64})\]")
_CAST_CHAIN_TOKEN = re.compile(
    r"\[CHAIN:(CHD-[A-Za-z0-9._-]+):([0-9a-f]{64}):"
    r"(SLOT-[A-Za-z0-9._-]+):(CHR-[A-Za-z0-9._-]+):"
    r"((?:SL|EV)-[A-Za-z0-9._-]+)\]"
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class C1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class C1RunReceipt:
    package_root: Path
    model: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any


def _fail(code: str, message: str) -> None:
    raise C1Error(code, message)


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
        _fail("C1_PATH_INVALID", value)
    return value


def _implementation_paths() -> dict[str, Path]:
    runtime_dir = _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    values = {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/runtime-contract.md": _SKILL / "references" / "runtime-contract.md",
    }
    for name in (
        "canonical.py",
        "contracts.py",
        "coordinator.py",
        "stage_implementation_identity.py",
    ):
        values[f"runtime/{name}"] = runtime_dir / name
    for name in (
        "character-system.schema.json",
        "canonical-common.schema.json",
        "common-defs.schema.json",
        "input-gate.schema.json",
        "package-manifest.schema.json",
        "stage-completion.schema.json",
    ):
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


def _stage_reference(root: Path, stage: str) -> dict[str, str]:
    path = root / "stage-completion.json"
    _read(path, f"C1_{stage}_INVALID")
    return {
        "stage": stage,
        "path": f"{stage}/stage-completion.json",
        "sha256": rt.sha256_file(path),
    }


def _sealed_upstream_reference(
    package_root: Path,
    sealed_reference: Mapping[str, Any],
    *,
    stage: str,
    run_id: str,
    previous_stage_completions: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> dict[str, str]:
    """Prove a gate-selected logical completion belongs to ``package_root``.

    The coordinator owns the immutable logical reference.  Its path may be a
    legacy flat stage path or an attempt-qualified path, while ``package_root``
    may be any physical (including Windows extended-length) directory.
    """

    code = f"C1_{stage}_INVALID"
    completion_path = package_root / "stage-completion.json"
    completion = _read(completion_path, code)
    reference = copy.deepcopy(dict(sealed_reference))
    try:
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail(code, str(error))
    if set(reference) != {"stage", "path", "sha256"}:
        _fail(code, f"sealed {stage} reference has an invalid shape")
    path = reference.get("path")
    digest = reference.get("sha256")
    if (
        reference.get("stage") != stage
        or not isinstance(path, str)
        or not isinstance(digest, str)
        or _HEX64.fullmatch(digest) is None
    ):
        _fail(code, f"sealed {stage} reference identity is invalid")
    logical_path = PurePosixPath(path)
    if (
        "\\" in path
        or logical_path.is_absolute()
        or logical_path.as_posix() != path
        or any(part in {"", ".", ".."} for part in logical_path.parts)
        or logical_path.name != "stage-completion.json"
        or len(logical_path.parts) < 2
    ):
        _fail(code, f"sealed {stage} completion path is not canonical")
    if (
        rt.sha256_file(completion_path) != digest
        or rt.canonical_sha256(completion) != digest
    ):
        _fail(code, f"sealed {stage} completion body or hash differs")
    if (
        completion.get("stage") != stage
        or completion.get("status") != "ready"
        or completion.get("run_id") != run_id
        or completion.get("previous_stage_completions")
        != list(previous_stage_completions)
    ):
        _fail(code, f"sealed completion is not this run's ready {stage}")
    logical_root = logical_path.parent
    if (
        completion.get("manifest")
        != {
            "path": (logical_root / "package-manifest.json").as_posix(),
            "sha256": rt.sha256_file(package_root / "package-manifest.json"),
        }
        or completion.get("validation")
        != {
            "path": (logical_root / "validation.json").as_posix(),
            "sha256": rt.sha256_file(package_root / "validation.json"),
        }
    ):
        _fail(
            code,
            f"sealed {stage} path is foreign to the completion's package lineage",
        )
    return reference


def _require_embedded_completion(
    path: Path, expected: Mapping[str, Any], *, code: str
) -> None:
    if (
        not path.is_file()
        or rt.sha256_file(path) != expected["sha256"]
        or rt.canonical_sha256(_read(path, code)) != expected["sha256"]
    ):
        _fail(code, f"{path} does not bind the gate-selected completion")


def _gate_selected_upstream_references(
    roots: Mapping[str, Path],
    gate: Mapping[str, Any],
    *,
    run_id: str,
    runtime: Any,
) -> tuple[dict[str, str], ...]:
    sealed_b0 = gate.get("baseline_completion")
    sealed_upstreams = gate.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 4
        or any(not isinstance(item, Mapping) for item in sealed_upstreams)
    ):
        _fail(
            "C1_GATE_INVALID",
            "gate does not select exactly B0, S1, W1, E1, and T1",
        )
    references: dict[str, dict[str, str]] = {}
    sealed = {
        "B0": sealed_b0,
        **dict(zip(("S1", "W1", "E1", "T1"), sealed_upstreams)),
    }
    previous = {
        "B0": (),
        "S1": (),
        "W1": ("S1",),
        "E1": ("S1", "W1"),
        "T1": ("S1", "W1", "E1"),
    }
    for stage in ("B0", "S1", "W1", "E1", "T1"):
        references[stage] = _sealed_upstream_reference(
            roots[stage],
            sealed[stage],
            stage=stage,
            run_id=run_id,
            previous_stage_completions=[
                references[item] for item in previous[stage]
            ],
            runtime=runtime,
        )
    try:
        for owner, ancestors in (
            ("S1", ("B0",)),
            ("W1", ("B0", "S1")),
            ("E1", ("B0", "S1", "W1")),
            ("T1", ("B0", "S1", "W1", "E1")),
        ):
            for ancestor in ancestors:
                _require_embedded_completion(
                    roots[owner]
                    / "sources"
                    / ancestor
                    / "stage-completion.json",
                    references[ancestor],
                    code="C1_UPSTREAM_LINEAGE_MISMATCH",
                )
    except C1Error:
        raise
    except (OSError, KeyError) as error:
        _fail("C1_UPSTREAM_LINEAGE_MISMATCH", str(error))
    return tuple(
        references[stage] for stage in ("B0", "S1", "W1", "E1", "T1")
    )


def _source_artifacts(
    b0_root: Path,
    s1_root: Path,
    w1_root: Path,
    e1_root: Path,
    t1_root: Path,
) -> list[dict[str, str]]:
    selected = {
        "B0": (
            b0_root,
            (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "S1": (
            s1_root,
            (
                "storyline-architecture.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "W1": (
            w1_root,
            (
                "world-model.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "E1": (
            e1_root,
            (
                "environment-system.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
        "T1": (
            t1_root,
            (
                "event-timeline.json",
                "package-manifest.json",
                "stage-completion.json",
            ),
        ),
    }
    return [
        {
            "path": f"sources/{stage}/{name}",
            "sha256": rt.sha256_file(root / name),
        }
        for stage, (root, names) in selected.items()
        for name in names
    ]


def _controls(
    b0_root: Path, baseline: Mapping[str, Any]
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for entry in baseline["design_artifacts"]:
        source = rt.verify_artifact_reference(entry["artifact"], root=b0_root)
        for value in rt.extract_controls(source, entry["domain"]):
            found.append({**value, "domain": entry["domain"]})
    found.sort(key=lambda item: item["id"])
    return found


def _object_bindings(
    values: Sequence[Mapping[str, Any]], *, extra: str | None = None
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            **({extra: str(item[extra])} if extra is not None else {}),
            "value_sha256": rt.canonical_sha256(item),
        }
        for item in values
    ]


def _control_bindings(
    controls: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            "domain": item["domain"],
            "heading": item["heading"],
            "value_sha256": rt.canonical_sha256(item["value"]),
        }
        for item in controls
    ]


def _session_id(
    thread_id: str,
    gate: Mapping[str, str],
    b0: Mapping[str, str],
    s1: Mapping[str, str],
    w1: Mapping[str, str],
    e1: Mapping[str, str],
    t1: Mapping[str, str],
) -> str:
    return "C1-" + rt.canonical_sha256(
        [thread_id, gate, b0, s1, w1, e1, t1]
    )[:20]


def _session_context(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    Path,
    Path,
    Path,
    Path,
    Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    b0_root = Path(baseline_package).resolve()
    s1_root = Path(storyline_package).resolve()
    w1_root = Path(world_package).resolve()
    e1_root = Path(environment_package).resolve()
    t1_root = Path(event_package).resolve()
    if full_validation:
        try:
            rt.validate_baseline_package(b0_root, runtime=runtime)
        except Exception as error:
            _fail("C1_B0_INVALID", str(error))
        try:
            s1_runtime.validate_s1_package(s1_root, runtime=runtime)
        except Exception as error:
            _fail("C1_S1_INVALID", str(error))
        try:
            w1_runtime.validate_w1_package(w1_root, runtime=runtime)
        except Exception as error:
            _fail("C1_W1_INVALID", str(error))
        try:
            e1_runtime.validate_e1_package(e1_root, runtime=runtime)
        except Exception as error:
            _fail("C1_E1_INVALID", str(error))
        try:
            t1_runtime.validate_t1_package(t1_root, runtime=runtime)
        except Exception as error:
            _fail("C1_T1_INVALID", str(error))
    baseline = _read(
        b0_root / "author-control-baseline.json", "C1_B0_INVALID"
    )
    storyline = _read(
        s1_root / "storyline-architecture.json", "C1_S1_INVALID"
    )
    world = _read(w1_root / "world-model.json", "C1_W1_INVALID")
    environment = _read(
        e1_root / "environment-system.json", "C1_E1_INVALID"
    )
    event_model = _read(t1_root / "event-timeline.json", "C1_T1_INVALID")
    if {
        baseline["run_id"],
        storyline["run_id"],
        world["run_id"],
        environment["run_id"],
        event_model["run_id"],
    } != {
        baseline["run_id"]
    }:
        _fail("C1_RUN_ID_MISMATCH", "B0/S1/W1/E1/T1 runs differ")
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("C1_GATE_INVALID", str(error))
    if rt.canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("C1_GATE_INVALID", "gate reference does not bind its body")
    b0_ref, s1_ref, w1_ref, e1_ref, t1_ref = (
        _gate_selected_upstream_references(
            {
                "B0": b0_root,
                "S1": s1_root,
                "W1": w1_root,
                "E1": e1_root,
                "T1": t1_root,
            },
            input_gate.data,
            run_id=baseline["run_id"],
            runtime=runtime,
        )
    )
    if (
        input_gate.data.get("target_stage") != "C1"
        or input_gate.data.get("run_id") != baseline["run_id"]
        or input_gate.data.get("baseline_completion") != b0_ref
        or input_gate.data.get("upstream_completions")
        != [s1_ref, w1_ref, e1_ref, t1_ref]
        or rt.canonical_sha256(input_gate.data)
        != input_gate.reference.get("sha256")
    ):
        _fail(
            "C1_GATE_INVALID",
            "gate is not the exact C1/B0/S1/W1/E1/T1 gate",
        )
    return (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        t1_root,
        baseline,
        storyline,
        world,
        environment,
        event_model,
        _controls(b0_root, baseline),
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
        t1_ref,
    )


def _nested_forbidden(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_NESTED_KEYS:
                return key
            found = _nested_forbidden(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _nested_forbidden(child)
            if found is not None:
                return found
    return None


def _boundary_check(model: Mapping[str, Any]) -> None:
    forbidden = sorted(set(model) & _FORBIDDEN_MODEL_KEYS)
    if forbidden:
        _fail("C1_BOUNDARY_VIOLATION", f"forbidden top-level fields: {forbidden}")
    nested = _nested_forbidden(model)
    if nested is not None:
        _fail("C1_BOUNDARY_VIOLATION", f"forbidden event/prose field: {nested}")


def _unique_by_id(values: Sequence[Mapping[str, Any]], code: str) -> dict[str, Mapping[str, Any]]:
    indexed = {item["id"]: item for item in values}
    if len(indexed) != len(values):
        _fail(code, "IDs repeat")
    return indexed


def _non_placeholder(value: str) -> bool:
    return isinstance(value, str) and value.strip().lower() not in {
        "none",
        "n/a",
        "na",
        "unknown",
        "tbd",
        "placeholder",
        "无",
        "未知",
        "待定",
    }


def _collect_defined_ids(value: Any, output: set[str]) -> None:
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            output.add(identifier)
        slot_id = value.get("slot_id")
        if isinstance(slot_id, str):
            output.add(slot_id)
        for child in value.values():
            _collect_defined_ids(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_defined_ids(child, output)


def _validate_authority_disjoint(partition: Mapping[str, Sequence[str]]) -> None:
    names = (
        "author_locked",
        "autonomous_owned",
        "downstream_freedom",
        "author_open",
    )
    groups = {name: set(partition[name]) for name in names}
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = groups[left] & groups[right]
            if overlap:
                _fail(
                    "C1_AUTHORITY_CONFLICT",
                    f"{left}/{right}: {sorted(overlap)}",
                )


def _validate_development_freedoms(
    values: Sequence[Mapping[str, Any]],
    *,
    profile_ids: set[str],
    defined_source_ids: set[str],
) -> dict[str, Mapping[str, Any]]:
    freedoms = _c1_index(values, "id", "C1_DEV_ID_DUPLICATE")
    freedom_subjects: set[str] = set()
    for freedom_id, freedom in freedoms.items():
        subjects = set(freedom["subject_ids"])
        if not subjects <= profile_ids:
            _fail("C1_DEV_SUBJECT_DANGLING", freedom_id)
        freedom_subjects.update(subjects)
        if not set(freedom["source_ids"]) <= defined_source_ids:
            _fail("C1_DEV_SOURCE_DANGLING", freedom_id)
        texts = [
            freedom["scope"],
            *freedom["allowed_variations"],
            *freedom["forbidden_changes"],
            *freedom["acceptance_checks"],
        ]
        if any(not _non_placeholder(value) for value in texts):
            _fail("C1_DEV_PLACEHOLDER", freedom_id)
    if freedom_subjects != profile_ids:
        _fail(
            "C1_DEV_PROFILE_COVERAGE_MISMATCH",
            "development freedom subjects must cover every profile exactly",
        )
    return freedoms


def _c1_index(values: Sequence[Mapping[str, Any]], key: str, code: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in values:
        identity = item.get(key)
        if not isinstance(identity, str) or not identity or identity in result:
            _fail(code, f"invalid or repeated {key}: {identity!r}")
        result[identity] = item
    return result


def _c1_maps(
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environment: Mapping[str, Any],
    timeline: Mapping[str, Any],
) -> dict[str, Any]:
    lines = _c1_index(storyline["storylines"], "id", "C1_STORYLINE_DUPLICATE")
    demands = _c1_index(storyline["character_requirements"], "id", "C1_DEMAND_DUPLICATE")
    events = _c1_index(timeline["major_events"], "id", "C1_EVENT_DUPLICATE")
    line_slots = {key: set(value["actor_slot_ids"]) for key, value in lines.items()}
    event_slots: dict[str, set[str]] = {}
    slot_events: dict[str, set[str]] = defaultdict(set)
    for event_id, event in events.items():
        slots = set(event["participant_slot_ids"])
        if event["initiator_slot_id"] not in slots or not set(event["counter_slot_ids"]) <= slots:
            _fail("C1_EVENT_SLOT_INVALID", event_id)
        event_slots[event_id] = slots
        for slot in slots:
            slot_events[slot].add(event_id)
    required_slots = {slot for slots in line_slots.values() for slot in slots}
    if required_slots != set(slot_events):
        missing = sorted(required_slots - set(slot_events))
        if missing:
            _fail("C1_SLOT_WITHOUT_EVENT", ",".join(missing))
        _fail("C1_EVENT_SLOT_DANGLING", ",".join(sorted(set(slot_events) - required_slots)))
    slot_demands: dict[str, set[str]] = defaultdict(set)
    for demand_id, demand in demands.items():
        sources = set(demand["source_ids"])
        projected = {item for item in sources if item in required_slots}
        for line_id in sources & set(lines):
            projected.update(line_slots[line_id])
        if not projected:
            _fail("C1_DEMAND_SLOT_UNRESOLVED", demand_id)
        for slot in projected:
            slot_demands[slot].add(demand_id)
    providers: set[str] = set()
    for field in ("systems", "institutions", "authority_flows"):
        providers.update(item["id"] for item in world[field])
    providers.update(item["id"] for item in environment["access_and_authority"])
    ledger_providers: dict[str, set[str]] = defaultdict(set)
    for item in timeline["state_ledger"]:
        for event_id in item["trigger_ids"]:
            ledger_providers[event_id].update(item["allowed_by_ids"])
    return {
        "lines": lines,
        "demands": demands,
        "events": events,
        "line_slots": line_slots,
        "event_slots": event_slots,
        "slot_events": dict(slot_events),
        "required_slots": required_slots,
        "slot_demands": dict(slot_demands),
        "providers": providers,
        "ledger_providers": dict(ledger_providers),
    }


def _c1_demand_digest(demand: Mapping[str, Any]) -> str:
    return rt.canonical_sha256(
        {
            key: demand[key]
            for key in (
                "responsibility",
                "source_ids",
                "required_capability",
                "constraints",
                "acceptance_checks",
                "downstream_freedom",
            )
        }
    )


def _c1_demand_blocks(
    text: str,
) -> set[tuple[str, str, str]]:
    return {
        (demand_id, digest, explanation.strip())
        for demand_id, digest, explanation in _DEMAND_BLOCK_TOKEN.findall(text)
    }


def _c1_obligations(maps: Mapping[str, Any], timeline: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    obligations: dict[str, dict[str, Any]] = {}
    for event_id in sorted(maps["events"]):
        event = maps["events"][event_id]
        for slot in sorted(maps["event_slots"][event_id]):
            kinds = {"capability"}
            role = "participant"
            if slot == event["initiator_slot_id"]:
                kinds.update({"decision", "action"})
                role = "initiator"
            if slot in event["counter_slot_ids"]:
                kinds.add("counteraction")
                role = "counter"
            for kind in sorted(kinds):
                key = f"{kind}:{event_id}:{slot}"
                obligations[key] = {"kind": kind, "event_id": event_id, "slot_id": slot, "role": role}
    for change in timeline["information_changes"]:
        for slot in sorted(change["visibility_ids"]):
            for event_id in change["event_ids"]:
                key = f"information:{event_id}:{slot}:{change['id']}"
                obligations[key] = {
                    "kind": "information", "event_id": event_id, "slot_id": slot,
                    "role": "participant", "information_id": change["id"],
                }
    for line_id in sorted(maps["lines"]):
        line = maps["lines"][line_id]
        for slot in sorted(line["actor_slot_ids"]):
            key = f"relationship-pressure:{line['id']}:{slot}"
            obligations[key] = {
                "kind": "relationship-pressure", "event_id": None,
                "slot_id": slot, "role": "participant", "storyline_id": line["id"],
            }
    terminal = {item["event_ids"][-1] for item in timeline["storyline_event_sequences"]}
    for event_id in sorted(terminal):
        slot = maps["events"][event_id]["initiator_slot_id"]
        key = f"aftermath:{event_id}:{slot}"
        obligations[key] = {"kind": "aftermath", "event_id": event_id, "slot_id": slot, "role": "initiator"}
    return obligations


def _c1_obligation_sort_key(
    item: tuple[str, Mapping[str, Any]],
) -> tuple[str, str, str, str, str, str, str]:
    """Return the stable total order used before assigning ordinal IDs."""

    key, obligation = item
    return (
        str(obligation["kind"]),
        str(obligation.get("event_id") or ""),
        str(obligation.get("storyline_id") or ""),
        str(obligation.get("information_id") or ""),
        str(obligation["slot_id"]),
        str(obligation["role"]),
        key,
    )


def _c1_distance(core: str, adjacency: Mapping[str, set[str]]) -> dict[str, int]:
    distances = {core: 0}
    queue = deque([core])
    while queue:
        current = queue.popleft()
        for target in sorted(adjacency.get(current, set())):
            if target not in distances:
                distances[target] = distances[current] + 1
                queue.append(target)
    return distances


def _validate_model(
    model: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environment: Mapping[str, Any],
    timeline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
    *,
    expected_gate: Mapping[str, str] | None = None,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
) -> None:
    del controls
    _boundary_check(model)
    try:
        runtime.validate(model, "character-system.schema.json")
    except Exception as error:
        _fail("C1_MODEL_SCHEMA_INVALID", str(error))
    if (
        model["skill"] != "novel-character-system-designer"
        or model["stage"] != "C1"
        or model["status"] != "ready"
        or model["run_id"] != baseline["run_id"]
    ):
        _fail("C1_MODEL_IDENTITY_INVALID", "skill/stage/status/run")
    _validate_authority_disjoint(model["authority_partition"])
    if expected_gate is not None and model["input_gate"] != dict(expected_gate):
        _fail("C1_GATE_REFERENCE_MISMATCH", "model gate differs")
    if expected_sources is not None and model["source_artifacts"] != list(expected_sources):
        _fail("C1_SOURCE_ARTIFACT_MISMATCH", "model sources differ")
    if model["character_demands"] != storyline["character_requirements"]:
        _fail("C1_DEMAND_PROJECTION_MISMATCH", "S1 character requirements must be exact")
    if not timeline["information_changes"]:
        _fail("C1_INFORMATION_INPUT_EMPTY", "T1 must define at least one information change")

    maps = _c1_maps(storyline, world, environment, timeline)
    resolutions = _c1_index(model["slot_resolution"], "slot_id", "C1_SLOT_RESOLUTION_DUPLICATE")
    if set(resolutions) != maps["required_slots"]:
        _fail("C1_SLOT_RESOLUTION_MISMATCH", "slot universe differs")
    slot_to_char: dict[str, str] = {}
    char_slots: dict[str, set[str]] = defaultdict(set)
    for slot, item in resolutions.items():
        if set(item["event_ids"]) != maps["slot_events"][slot]:
            _fail("C1_SLOT_EVENT_MISMATCH", slot)
        if set(item["demand_ids"]) != maps["slot_demands"].get(slot, set()):
            _fail("C1_SLOT_DEMAND_MISMATCH", slot)
        expected_blocks = {
            (
                demand_id,
                _c1_demand_digest(maps["demands"][demand_id]),
                maps["demands"][demand_id]["responsibility"],
            )
            for demand_id in maps["slot_demands"].get(slot, set())
        }
        if (
            not _non_placeholder(item["rationale"])
            or _c1_demand_blocks(item["rationale"]) != expected_blocks
        ):
            _fail("C1_SLOT_RATIONALE_MISSING", slot)
        slot_to_char[slot] = item["character_id"]
        char_slots[item["character_id"]].add(slot)
    decisions = _c1_index(model["design_decisions"], "id", "C1_DECISION_DUPLICATE")
    for character_id, slots in char_slots.items():
        if len(slots) > 1:
            digest = rt.canonical_sha256(sorted(slots))
            if not any(_MERGE_TOKEN.search(text) and _MERGE_TOKEN.search(text).group(1) == digest
                       for decision in decisions.values()
                       for text in (decision["selection"], decision["compatibility"])):
                _fail("C1_SLOT_MERGE_UNJUSTIFIED", character_id)
            for event_id, event_slots in maps["event_slots"].items():
                event = maps["events"][event_id]
                if event["initiator_slot_id"] in slots and set(event["counter_slot_ids"]) & slots:
                    _fail("C1_SLOT_MERGE_CONFLICT", event_id)

    profiles = _c1_index(model["profiles"], "id", "C1_PROFILE_DUPLICATE")
    relation_endpoints = {
        item[field] for item in model["relationships"]
        for field in ("from_character_id", "to_character_id")
    }
    if set(profiles) != set(char_slots) | relation_endpoints:
        _fail("C1_PROFILE_SET_MISMATCH", "profile set differs from resolved/related cast")
    names: set[str] = set()
    for character_id, profile in profiles.items():
        match = _CLASS_TOKEN.fullmatch(profile["name"])
        if match is None or not _non_placeholder(match.group(2)):
            _fail("C1_PROFILE_CLASS_MISSING", character_id)
        folded = match.group(2).casefold()
        if folded in names:
            _fail("C1_DUPLICATE_IDENTITY", character_id)
        names.add(folded)
        story_position = profile["story_position"]
        expected_level = match.group(1)
        if story_position["narrative_level"] != expected_level:
            _fail("C1_STORY_POSITION_CLASS_MISMATCH", character_id)
        for field in ("entry_function", "ongoing_function", "ending_function"):
            if not _non_placeholder(story_position[field]):
                _fail("C1_STORY_POSITION_INCOMPLETE", f"{character_id}.{field}")

        activity = profile["activity_participation"]
        resolved_slots = char_slots.get(character_id, set())
        expected_event_ids = {
            event_id
            for slot in resolved_slots
            for event_id in maps["slot_events"].get(slot, set())
        }
        expected_storyline_ids = {
            storyline_id
            for event_id in expected_event_ids
            for storyline_id in maps["events"][event_id]["storyline_ids"]
        }
        expected_environment_ids = {
            maps["events"][event_id]["environment_id"]
            for event_id in expected_event_ids
        }
        if (
            set(activity["event_ids"]) != expected_event_ids
            or set(activity["storyline_ids"]) != expected_storyline_ids
            or set(activity["environment_ids"]) != expected_environment_ids
        ):
            _fail("C1_ACTIVITY_PROJECTION_MISMATCH", character_id)
        for field in ("activity_summary", "causal_contribution"):
            if not _non_placeholder(activity[field]):
                _fail("C1_ACTIVITY_DEFINITION_INCOMPLETE", f"{character_id}.{field}")

        individual = profile["individual_definition"]
        for field in (
            "appearance",
            "personality",
            "life_background",
            "occupation_and_daily_life",
            "social_circle",
            "embodied_or_interface_constraints",
        ):
            if not _non_placeholder(individual[field]):
                _fail("C1_INDIVIDUAL_DEFINITION_INCOMPLETE", f"{character_id}.{field}")
        boundary_types = {
            match.group(1) for value in profile["boundaries"]
            if (match := _BOUNDARY_TOKEN.fullmatch(value))
        }
        if boundary_types != {"blind-spot", "hard-boundary"}:
            _fail("C1_BOUNDARY_TYPES_INCOMPLETE", character_id)
        for field in ("story_responsibility", "pressure_behavior", "arc_direction"):
            if not _non_placeholder(profile[field]):
                _fail("C1_PROFILE_INCOMPLETE", f"{character_id}.{field}")
        for field in ("goals", "values", "boundaries", "information_limits",
                      "agency_choices", "non_delegable_choices"):
            if not profile[field]:
                _fail("C1_PROFILE_INCOMPLETE", f"{character_id}.{field}")
        character_demands = {
            demand_id
            for slot in char_slots.get(character_id, set())
            for demand_id in maps["slot_demands"].get(slot, set())
        }
        expected_blocks = {
            (
                demand_id,
                _c1_demand_digest(maps["demands"][demand_id]),
                maps["demands"][demand_id]["responsibility"],
            )
            for demand_id in character_demands
        }
        if _c1_demand_blocks(profile["story_responsibility"]) != expected_blocks:
            _fail("C1_PROFILE_DEMAND_MISMATCH", character_id)
        expected_goal_effects = {
            (demand_id, _c1_demand_digest(maps["demands"][demand_id]), "goal")
            for demand_id in character_demands
        }
        actual_goal_effects = {
            match.groups()[:3]
            for value in profile["goals"]
            if (match := _DEMAND_EFFECT_TOKEN.fullmatch(value))
        }
        expected_boundary_effects = {
            (
                demand_id,
                _c1_demand_digest(maps["demands"][demand_id]),
                "boundary",
            )
            for demand_id in character_demands
        }
        actual_boundary_effects = {
            match.groups()[:3]
            for value in profile["boundaries"]
            if (boundary := _BOUNDARY_TOKEN.fullmatch(value))
            and boundary.group(1) == "hard-boundary"
            and (match := _DEMAND_EFFECT_TOKEN.fullmatch(boundary.group(2)))
        }
        if (
            actual_goal_effects != expected_goal_effects
            or actual_boundary_effects != expected_boundary_effects
        ):
            _fail("C1_PROFILE_DEMAND_EFFECT_MISMATCH", character_id)

    obligations = _c1_obligations(maps, timeline)
    assignments = _c1_index(model["responsibility_matrix"], "id", "C1_RESPONSIBILITY_DUPLICATE")
    seen: dict[str, str] = {}
    for assignment in assignments.values():
        character_id = assignment["subject_id"]
        if character_id not in profiles:
            _fail("C1_RESPONSIBILITY_DANGLING", assignment["id"])
        kind_match = _DEMAND_KIND_TOKEN.match(assignment["responsibility"])
        slot_match = _SLOT_TOKEN.search(assignment["responsibility"])
        if kind_match is None or slot_match is None:
            _fail("C1_RESPONSIBILITY_TOKEN_MISSING", assignment["id"])
        candidates = [
            key for key, value in obligations.items()
            if value["kind"] == kind_match.group(1)
            and value["slot_id"] == slot_match.group(1)
            and (value["event_id"] is None or value["event_id"] in assignment["evidence_ids"])
            and (value.get("storyline_id") is None or value["storyline_id"] in assignment["evidence_ids"])
            and (value.get("information_id") is None or value["information_id"] in assignment["evidence_ids"])
        ]
        if len(candidates) != 1 or candidates[0] in seen:
            _fail("C1_RESPONSIBILITY_BINDING_INVALID", assignment["id"])
        if slot_to_char[slot_match.group(1)] != character_id:
            _fail("C1_RESPONSIBILITY_CHARACTER_MISMATCH", assignment["id"])
        expected_demand_bindings = {
            (
                demand_id,
                _c1_demand_digest(maps["demands"][demand_id]),
            )
            for demand_id in maps["slot_demands"].get(
                slot_match.group(1), set()
            )
        }
        actual_demand_bindings = {
            match.groups()
            for constraint in assignment["constraints"]
            if (match := _DEMAND_BINDING_TOKEN.fullmatch(constraint))
        }
        if actual_demand_bindings != expected_demand_bindings:
            _fail("C1_RESPONSIBILITY_DEMAND_MISMATCH", assignment["id"])
        if obligations[candidates[0]]["kind"] == "decision":
            profile = profiles[character_id]
            required = {
                f"[GOAL_SHA256:{rt.canonical_sha256(profile['goals'])}]",
                f"[VALUE_SHA256:{rt.canonical_sha256(profile['values'])}]",
            }
            if not required <= set(assignment["constraints"]):
                _fail("C1_DECISION_MOTIVE_UNBOUND", assignment["id"])
        seen[candidates[0]] = assignment["id"]
    if set(seen) != set(obligations):
        _fail("C1_RESPONSIBILITY_COVERAGE", f"missing {sorted(set(obligations)-set(seen))[:3]}")

    agencies = _c1_index(model["agency_matrix"], "id", "C1_AGENCY_DUPLICATE")
    agency_events: dict[str, set[str]] = defaultdict(set)
    bound_roles: set[tuple[str, str, str]] = set()
    for item in agencies.values():
        if item["character_id"] not in profiles or not set(item["event_ids"]) <= set(maps["events"]):
            _fail("C1_AGENCY_DANGLING", item["id"])
        if len(item["available_choices"]) < 2 or item["chosen_action"] not in item["available_choices"]:
            _fail("C1_AGENCY_NO_REAL_CHOICE", item["id"])
        if not _non_placeholder(item["cost"]):
            _fail("C1_AGENCY_COST_MISSING", item["id"])
        character_id = item["character_id"]
        expected_init: set[tuple[str, str]] = set()
        expected_counter: set[tuple[str, str]] = set()
        for event_id in item["event_ids"]:
            event = maps["events"][event_id]
            if slot_to_char[event["initiator_slot_id"]] == character_id:
                expected_init.add(
                    (event_id, rt.canonical_sha256(event["initiating_action"]))
                )
            if any(
                slot_to_char[slot] == character_id
                for slot in event["counter_slot_ids"]
            ):
                expected_counter.add(
                    (event_id, rt.canonical_sha256(event["complication"]))
                )
            if (
                (event_id, rt.canonical_sha256(event["initiating_action"]))
                not in expected_init
                and (event_id, rt.canonical_sha256(event["complication"]))
                not in expected_counter
            ):
                _fail("C1_AGENCY_ROLE_DANGLING", f"{item['id']}:{event_id}")
        actual_init = set(_AGENCY_INIT_TOKEN.findall(item["chosen_action"]))
        actual_counter = set(_AGENCY_COUNTER_TOKEN.findall(item["chosen_action"]))
        if actual_init != expected_init or actual_counter != expected_counter:
            _fail("C1_AGENCY_ACTION_BINDING_MISMATCH", item["id"])
        readable = _AGENCY_COUNTER_TOKEN.sub(
            "", _AGENCY_INIT_TOKEN.sub("", item["chosen_action"])
        ).strip()
        expected_duty = rt.canonical_sha256(
            profiles[character_id]["story_responsibility"]
        )
        if (
            set(_DUTY_BINDING_TOKEN.findall(item["chosen_action"]))
            != {expected_duty}
            or set(_DUTY_BINDING_TOKEN.findall(item["cost"]))
            != {expected_duty}
        ):
            _fail("C1_AGENCY_DUTY_BINDING_MISMATCH", item["id"])
        readable = _DUTY_BINDING_TOKEN.sub("", readable).strip()
        if not _non_placeholder(readable):
            _fail("C1_AGENCY_ACTION_TEXT_MISSING", item["id"])
        for event_id, _ in expected_init:
            role = (event_id, character_id, "initiator")
            if role in bound_roles:
                _fail("C1_AGENCY_ROLE_DUPLICATE", f"{event_id}:{character_id}")
            bound_roles.add(role)
        for event_id, _ in expected_counter:
            role = (event_id, character_id, "counter")
            if role in bound_roles:
                _fail("C1_AGENCY_ROLE_DUPLICATE", f"{event_id}:{character_id}")
            bound_roles.add(role)
        agency_events[character_id].update(item["event_ids"])
    for event_id, event in maps["events"].items():
        expected_roles = {
            (event_id, slot_to_char[event["initiator_slot_id"]], "initiator"),
            *{
                (event_id, slot_to_char[slot], "counter")
                for slot in event["counter_slot_ids"]
            },
        }
        if not expected_roles <= bound_roles:
            _fail("C1_EVENT_AGENCY_MISSING", event_id)
        initiator = profiles[slot_to_char[event["initiator_slot_id"]]]
        if not any(
            (match := _ACTION_TOKEN.fullmatch(value))
            and match.group(1) == rt.canonical_sha256(event["initiating_action"])
            for value in initiator["capabilities"]
        ):
            _fail("C1_ACTION_CAPABILITY_MISSING", event_id)
        for slot in event["participant_slot_ids"]:
            profile = profiles[slot_to_char[slot]]
            if not any(
                (match := _ENV_TOKEN.fullmatch(value))
                and match.group(1) == event["environment_id"]
                for value in profile["capabilities"]
            ):
                _fail("C1_ENVIRONMENT_ACCESS_MISSING", f"{event_id}:{slot}")
        for provider in maps["ledger_providers"].get(event_id, set()):
            if provider not in initiator["authorities"]:
                _fail("C1_PROVIDER_AUTHORITY_MISSING", f"{event_id}:{provider}")

    expected_info_chars = {
        slot_to_char[slot]
        for change in timeline["information_changes"]
        for slot in change["visibility_ids"]
    }
    information = _c1_index(model["information_matrix"], "character_id", "C1_INFORMATION_DUPLICATE")
    if set(information) != expected_info_chars:
        _fail("C1_INFORMATION_COVERAGE", "matrix must cover exactly changed-visibility characters")
    for character_id, state in information.items():
        relevant_changes = [
            change for change in timeline["information_changes"]
            if character_id in {
                slot_to_char[slot] for slot in change["visibility_ids"]
            }
        ]
        expected_info_bindings = {
            (
                change["id"],
                event_id,
                rt.canonical_sha256(change["before"]),
                rt.canonical_sha256(change["after"]),
            )
            for change in relevant_changes
            for event_id in change["event_ids"]
        }
        if set(state["change_event_ids"]) != {
            event_id for _, event_id, _, _ in expected_info_bindings
        }:
            _fail("C1_INFORMATION_EVENT_MISMATCH", character_id)
        if set(state["knows"]) & set(state["does_not_know"]) or set(state["knows"]) & set(state["misreads"]):
            _fail("C1_INFORMATION_CONTRADICTION", character_id)
        actual_known = {
            match.groups()[:4] for value in state["knows"]
            if (match := _KNOWN_TOKEN.fullmatch(value))
        }
        actual_unknown = {
            match.groups()[:4] for value in state["does_not_know"]
            if (match := _UNKNOWN_TOKEN.fullmatch(value))
        }
        if (
            len(actual_known) != len(state["knows"])
            or actual_known != expected_info_bindings
        ):
            _fail("C1_INFORMATION_KNOWN_BINDING_MISMATCH", character_id)
        if (
            len(actual_unknown) != len(state["does_not_know"])
            or actual_unknown != expected_info_bindings
        ):
            _fail("C1_INFORMATION_UNKNOWN_BINDING_MISMATCH", character_id)
        if not set(state["does_not_know"]) <= set(profiles[character_id]["information_limits"]):
            _fail("C1_INFORMATION_LIMIT_MISMATCH", character_id)

    arcs = _c1_index(model["character_arcs"], "character_id", "C1_ARC_DUPLICATE")
    if not set(agency_events) <= set(arcs):
        _fail("C1_ARC_COVERAGE", "all choosing characters need arcs")
    for character_id, arc in arcs.items():
        if character_id not in profiles or not set(arc["choice_event_ids"]) <= agency_events.get(character_id, set()):
            _fail("C1_ARC_CHOICE_MISMATCH", arc["id"])
        related_events = {
            event_id
            for relation in model["relationships"]
            if character_id in {
                relation["from_character_id"], relation["to_character_id"]
            }
            for event_id in relation["change_event_ids"]
        }
        responsibility_events = {
            evidence_id
            for assignment in assignments.values()
            if assignment["subject_id"] == character_id
            for evidence_id in assignment["evidence_ids"]
            if evidence_id in maps["events"]
        }
        participation_events = {
            event_id for slot in char_slots.get(character_id, set())
            for event_id in maps["slot_events"][slot]
        }
        relevant_events = (
            related_events | responsibility_events | participation_events
        )
        if not set(arc["pressure_event_ids"]) <= relevant_events:
            _fail("C1_ARC_PRESSURE_MISMATCH", arc["id"])
        expected_duty = rt.canonical_sha256(
            profiles[character_id]["story_responsibility"]
        )
        if set(_DUTY_BINDING_TOKEN.findall(arc["theme_effect"])) != {
            expected_duty
        }:
            _fail("C1_ARC_DUTY_BINDING_MISMATCH", arc["id"])

    relationships = _c1_index(model["relationships"], "id", "C1_RELATIONSHIP_DUPLICATE")
    adjacency: dict[str, set[str]] = defaultdict(set)
    incident: dict[str, set[str]] = defaultdict(set)
    for relation_id, relation in relationships.items():
        left, right = relation["from_character_id"], relation["to_character_id"]
        if left == right or left not in profiles or right not in profiles:
            _fail("C1_RELATIONSHIP_DANGLING", relation_id)
        if not set(relation["change_event_ids"]) <= set(maps["events"]):
            _fail("C1_RELATIONSHIP_EVENT_DANGLING", relation_id)
        if not _REL_FUNCTION_TOKEN.match(relation["function"]):
            _fail("C1_RELATIONSHIP_FUNCTION_MISSING", relation_id)
        adjacency[left].add(right); adjacency[right].add(left)
        incident[left].add(relation_id); incident[right].add(relation_id)
    for character_id, profile in profiles.items():
        declared = {
            match.group(1) for value in profile["relationship_levers"]
            if (match := _REL_LEVER_TOKEN.fullmatch(value))
        }
        if declared != incident.get(character_id, set()):
            _fail("C1_RELATIONSHIP_LEVER_MISMATCH", character_id)

    core_decision = decisions.get("DEC-C1-CORE")
    if core_decision is None:
        _fail("C1_CORE_DECISION_MISSING", "DEC-C1-CORE")
    networks = _c1_index(model["three_layer_networks"], "core_character_id", "C1_NETWORK_DUPLICATE")
    selected_cores = set(core_decision["impact_ids"])
    if set(networks) != selected_cores or not selected_cores <= set(profiles):
        _fail("C1_CORE_NETWORK_MISMATCH", "selected core set differs")
    main_lines = {key for key, value in maps["lines"].items() if value["type"] == "main"}
    main_core_candidates = {
        slot_to_char[maps["events"][event_id]["initiator_slot_id"]]
        for event_id, event in maps["events"].items()
        if set(event["storyline_ids"]) & main_lines
    }
    if not selected_cores & main_core_candidates:
        _fail("C1_CORE_EVIDENCE_WEAK", "no main-line initiator selected")
    expected_core_digest = rt.canonical_sha256(sorted(selected_cores))
    if not any(
        (match := _CORE_EVIDENCE_TOKEN.fullmatch(text))
        and match.group(1) == expected_core_digest
        for text in (core_decision["selection"], core_decision["compatibility"])
    ):
        _fail("C1_CORE_EVIDENCE_STALE", "core evidence digest")
    for core, network in networks.items():
        layers = [
            set(network["layer_1_direct"]),
            set(network["layer_2_institutional"]),
            set(network["layer_3_contextual"]),
        ]
        if any(not layer for layer in layers) or any(core in layer for layer in layers):
            _fail("C1_NETWORK_LAYER_INVALID", core)
        if layers[0] & layers[1] or layers[0] & layers[2] or layers[1] & layers[2]:
            _fail("C1_NETWORK_LAYER_OVERLAP", core)
        distance = _c1_distance(core, adjacency)
        for depth, layer in enumerate(layers, 1):
            exact_layer = {
                character_id for character_id in profiles
                if distance.get(character_id) == depth
            }
            if layer != exact_layer:
                _fail("C1_NETWORK_DISTANCE_MISMATCH", f"{core}:L{depth}")
        nodes = {core} | set().union(*layers)
        exact_relations = {
            relation_id for relation_id, relation in relationships.items()
            if relation["from_character_id"] in nodes and relation["to_character_id"] in nodes
        }
        if set(network["relationship_ids"]) != exact_relations:
            _fail("C1_NETWORK_RELATION_MISMATCH", core)

    def coverage(
        values: Sequence[Mapping[str, Any]],
        expected: Mapping[str, set[str]],
        expected_chains: Mapping[str, set[tuple[str, str, str, str, str]]],
        code: str,
    ) -> None:
        indexed: dict[str, Mapping[str, Any]] = {}
        for item in values:
            if len(item["source_ids"]) != 1 or item["source_ids"][0] in indexed:
                _fail(code, item["id"])
            indexed[item["source_ids"][0]] = item
        if set(indexed) != set(expected):
            _fail(code, "source set differs")
        for source_id, cast in expected.items():
            if set(indexed[source_id]["realization_ids"]) != cast:
                _fail(code, source_id)
            actual_chains = set(
                _CAST_CHAIN_TOKEN.findall(indexed[source_id]["evidence"])
            )
            if actual_chains != expected_chains[source_id]:
                _fail(f"{code}_CHAIN", source_id)
    coverage(
        model["storyline_cast_coverage"],
        {line_id: {slot_to_char[slot] for slot in slots} for line_id, slots in maps["line_slots"].items()},
        {
            line_id: {
                (
                    demand_id,
                    _c1_demand_digest(maps["demands"][demand_id]),
                    slot,
                    slot_to_char[slot],
                    line_id,
                )
                for slot in slots
                for demand_id in maps["slot_demands"].get(slot, set())
            }
            for line_id, slots in maps["line_slots"].items()
        },
        "C1_STORYLINE_CAST_MISMATCH",
    )
    coverage(
        model["event_cast_coverage"],
        {event_id: {slot_to_char[slot] for slot in slots} for event_id, slots in maps["event_slots"].items()},
        {
            event_id: {
                (
                    demand_id,
                    _c1_demand_digest(maps["demands"][demand_id]),
                    slot,
                    slot_to_char[slot],
                    event_id,
                )
                for slot in slots
                for demand_id in maps["slot_demands"].get(slot, set())
            }
            for event_id, slots in maps["event_slots"].items()
        },
        "C1_EVENT_CAST_MISMATCH",
    )
    terminal = {item["event_ids"][-1] for item in timeline["storyline_event_sequences"]}
    aftermath_by_event: dict[str, str] = {}
    for item in model["aftermath_responsibility"]:
        for event_id in set(item["evidence_ids"]) & terminal:
            if event_id in aftermath_by_event:
                _fail("C1_AFTERMATH_DUPLICATE", event_id)
            aftermath_by_event[event_id] = item["subject_id"]
    if set(aftermath_by_event) != terminal or any(
        aftermath_by_event[event_id] != slot_to_char[maps["events"][event_id]["initiator_slot_id"]]
        for event_id in sorted(terminal)
    ):
        _fail("C1_AFTERMATH_COVERAGE_MISMATCH", "terminal initiators")

    structurally_used = set(char_slots) | relation_endpoints | set(aftermath_by_event.values())
    if set(profiles) != structurally_used:
        _fail("C1_ORPHAN_CHARACTER", ",".join(sorted(set(profiles)-structurally_used)))

    defined_sources: set[str] = set()
    for source in (baseline, storyline, world, environment, timeline):
        _collect_defined_ids(source, defined_sources)
    _collect_defined_ids(
        {
            key: value
            for key, value in model.items()
            if key != "development_freedoms"
        },
        defined_sources,
    )
    freedoms = _validate_development_freedoms(
        model["development_freedoms"],
        profile_ids=set(profiles),
        defined_source_ids=defined_sources,
    )

    locked = {item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"}
    opened = {item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"}
    generated = {
        item["id"] for field in (
            "design_decisions", "profiles", "responsibility_matrix", "agency_matrix",
            "information_matrix", "character_arcs", "relationships",
            "storyline_cast_coverage", "event_cast_coverage", "aftermath_responsibility",
        ) for item in model[field]
    }
    # A canonical character profile may deliberately preserve an author-locked
    # B0 identifier.  Such an object is governed by C1, but its identifier does
    # not become C1-owned: the author authority remains authoritative.  The
    # locally owned set is therefore the generated identifier universe minus
    # both B0 authority sets.
    locally_owned = generated - locked - opened
    partition = model["authority_partition"]
    if set(partition["author_locked"]) != locked or set(partition["author_open"]) != opened:
        _fail("C1_AUTHORITY_PARTITION_MISMATCH", "B0 controls changed")
    if set(partition["autonomous_owned"]) != locally_owned:
        _fail("C1_AUTHORITY_PARTITION_MISMATCH", "C1 owned set differs")
    if set(partition["downstream_freedom"]) != set(freedoms):
        _fail(
            "C1_AUTHORITY_PARTITION_MISMATCH",
            "terminal development freedom set differs",
        )
    if any(item["owner"] != "C1" or item["selection"] not in item["options"] for item in decisions.values()):
        _fail("C1_DECISION_INVALID", "owner/selection")
    projections = {
        item["id"]: item for field in ("profiles", "character_arcs", "relationships")
        for item in model[field]
    }
    claims = _c1_index(model["derivation_claims"], "id", "C1_DERIVATION_DUPLICATE")
    claimed: set[str] = set()
    claim_by_projection: dict[str, Mapping[str, Any]] = {}
    for claim in claims.values():
        if len(claim["projection_ids"]) == 1 and claim["projection_ids"][0] in projections:
            projection_id = claim["projection_ids"][0]
            if claim["value_sha256"] != rt.canonical_sha256(projections[projection_id]):
                _fail("C1_DERIVATION_STALE", claim["id"])
            claimed.add(projection_id)
            claim_by_projection[projection_id] = claim
    if set(projections) != claimed:
        _fail("C1_DERIVATION_COVERAGE", "profiles/arcs/relationships must be claimed")
    all_demand_ids = set(maps["demands"])
    for character_id in profiles:
        expected_demands = {
            demand_id
            for slot in char_slots.get(character_id, set())
            for demand_id in maps["slot_demands"].get(slot, set())
        }
        if (
            set(claim_by_projection[character_id]["source_ids"])
            & all_demand_ids
        ) != expected_demands:
            _fail("C1_PROFILE_DERIVATION_DEMAND_MISMATCH", character_id)
    actual_open = {source for item in model["open_items"] for source in item["source_ids"]}
    if actual_open != opened:
        _fail("C1_OPEN_ITEMS_MISMATCH", "author-open controls changed")


def _session_document(
    *,
    thread_id: str,
    gate: Mapping[str, str],
    state_before: Mapping[str, Any],
    roots: Sequence[Path],
    models: Sequence[Mapping[str, Any]],
    controls: Sequence[Mapping[str, Any]],
    references: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    b0_root, s1_root, w1_root, e1_root, t1_root = roots
    baseline, storyline, world, environment, timeline = models
    b0_ref, s1_ref, w1_ref, e1_ref, t1_ref = references
    return {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "C1",
        "session_id": _session_id(
            thread_id, gate, b0_ref, s1_ref, w1_ref, e1_ref, t1_ref
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(gate),
        "state_before": copy.deepcopy(state_before),
        "baseline_completion": copy.deepcopy(b0_ref),
        "upstream_completions": copy.deepcopy([s1_ref, w1_ref, e1_ref, t1_ref]),
        "source_artifacts": _source_artifacts(
            b0_root, s1_root, w1_root, e1_root, t1_root
        ),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(storyline["storylines"], extra="type"),
        "character_requirement_bindings": _object_bindings(
            storyline["character_requirements"], extra="target_stage"
        ),
        "storyline_slot_bindings": [
            {
                "id": item["id"],
                "value_sha256": rt.canonical_sha256(item["actor_slot_ids"]),
            }
            for item in storyline["storylines"]
        ],
        "world_character_bindings": _object_bindings(
            [
                *world["systems"],
                *world["institutions"],
                *world["history_pressures"],
                *world["authority_flows"],
                *world["information_flows"],
            ]
        ),
        "environment_bindings": _object_bindings(environment["environments"]),
        "environment_access_bindings": _object_bindings(
            environment["access_and_authority"]
        ),
        "event_bindings": _object_bindings(timeline["major_events"], extra="world_time"),
        "event_slot_bindings": [
            {
                "id": item["id"],
                "value_sha256": rt.canonical_sha256(
                    {
                        "participants": item["participant_slot_ids"],
                        "initiator": item["initiator_slot_id"],
                        "counters": item["counter_slot_ids"],
                    }
                ),
            }
            for item in timeline["major_events"]
        ],
        "information_change_bindings": _object_bindings(
            timeline["information_changes"]
        ),
        "phases": list(PHASES),
    }


def start_c1_session(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    if root.exists():
        _fail("C1_SESSION_EXISTS", str(root))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("C1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        t1_root,
        baseline,
        storyline,
        world,
        environment,
        timeline,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
        t1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    session = _session_document(
        thread_id=thread_id,
        gate=input_gate.reference,
        state_before=input_gate.data["run_state"],
        roots=(b0_root, s1_root, w1_root, e1_root, t1_root),
        models=(baseline, storyline, world, environment, timeline),
        controls=controls,
        references=(b0_ref, s1_ref, w1_ref, e1_ref, t1_ref),
    )
    root.mkdir(parents=True)
    _write(root / "generation-session.json", session)
    return copy.deepcopy(session)


def _validated_session(
    workspace: Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    session = _read(workspace / "generation-session.json", "C1_SESSION_INVALID")
    (
        b0_root,
        s1_root,
        w1_root,
        e1_root,
        t1_root,
        baseline,
        storyline,
        world,
        environment,
        timeline,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
        e1_ref,
        t1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        input_gate=input_gate,
        runtime=runtime,
        full_validation=full_validation,
    )
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    expected = _session_document(
        thread_id=thread_id,
        gate=input_gate.reference,
        state_before=input_gate.data["run_state"],
        roots=(b0_root, s1_root, w1_root, e1_root, t1_root),
        models=(baseline, storyline, world, environment, timeline),
        controls=controls,
        references=(b0_ref, s1_ref, w1_ref, e1_ref, t1_ref),
    )
    if not thread_id or session != expected:
        _fail(
            "C1_SESSION_INVALID",
            "session no longer binds B0/S1/W1/E1/T1/gate/thread",
        )
    return session, baseline, storyline, world, environment, timeline, controls


def submit_c1_phase(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    input_gate: Any,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, storyline, world, environment, timeline, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    completed: list[str] = []
    for index, item in enumerate(PHASES, 1):
        if (
            root / "generation-evidence" / f"{index:02d}-{item}.json"
        ).is_file():
            completed.append(item)
        else:
            break
    if len(completed) >= len(PHASES):
        _fail("C1_PHASE_ORDER_INVALID", "all phases already sealed")
    if phase not in PHASES or phase != PHASES[len(completed)]:
        _fail("C1_PHASE_ORDER_INVALID", f"next phase is {PHASES[len(completed)]}")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS[phase]):
        _fail(
            "C1_PHASE_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(PHASE_FIELDS[phase])}",
        )
    if phase == "final-character-model":
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("C1_PHASE_PAYLOAD_INVALID", "final model missing")
        _validate_model(
            model,
            baseline,
            storyline,
            world,
            environment,
            timeline,
            controls,
            contract_runtime,
            expected_gate=input_gate.reference,
            expected_sources=session["source_artifacts"],
        )
    previous = None
    if completed:
        previous = rt.sha256_file(
            root
            / "generation-evidence"
            / f"{len(completed):02d}-{completed[-1]}.json"
        )
    evidence = {
        "schema_version": "2.0",
        **{
            key: copy.deepcopy(session[key])
            for key in (
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
                "character_requirement_bindings",
                "storyline_slot_bindings",
                "world_character_bindings",
                "environment_bindings",
                "environment_access_bindings",
                "event_bindings",
                "event_slot_bindings",
                "information_change_bindings",
            )
        },
        "stage": "C1",
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "payload": body,
        "payload_sha256": rt.canonical_sha256(body),
    }
    path = (
        root
        / "generation-evidence"
        / f"{len(completed)+1:02d}-{phase}.json"
    )
    _write(path, evidence)
    return rt.artifact_reference(path, root=root)


def _validate_phase_chain(
    evidence_root: Path,
    *,
    session: Mapping[str, Any],
    model: Mapping[str, Any],
) -> list[Path]:
    paths: list[Path] = []
    previous = None
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
        "character_requirement_bindings",
        "storyline_slot_bindings",
        "world_character_bindings",
        "environment_bindings",
        "environment_access_bindings",
        "event_bindings",
        "event_slot_bindings",
        "information_change_bindings",
    )
    for index, phase in enumerate(PHASES, 1):
        path = evidence_root / f"{index:02d}-{phase}.json"
        evidence = _read(path, "C1_EVIDENCE_MISSING")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("C1_EVIDENCE_INVALID", phase)
        expected = {
            "schema_version": "2.0",
            **{key: copy.deepcopy(session[key]) for key in shared},
            "stage": "C1",
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        if evidence != expected or set(payload) != set(PHASE_FIELDS[phase]):
            _fail("C1_EVIDENCE_INVALID", phase)
        if phase == "final-character-model":
            if payload["model"] != model:
                _fail("C1_EVIDENCE_MODEL_MISMATCH", phase)
        else:
            for field in PHASE_FIELDS[phase]:
                if payload[field] != model[field]:
                    _fail("C1_EVIDENCE_MODEL_MISMATCH", f"{phase}.{field}")
        previous = rt.sha256_file(path)
        paths.append(path)
    return paths


def _validation(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "C1",
        "verdict": "ready",
        "checks": [
            "schema",
            "B0/S1/W1/E1/T1/gate-lineage",
            "character-demand-and-slot-exact-projection",
            "seven-duty-responsibility-closure",
            "agency-capability-authority-access-closure",
            "information-and-character-arc-closure",
            "relationship-and-three-layer-BFS-closure",
            "storyline-event-aftermath-cast-closure",
            "governance-derivation-and-boundary",
            "completion-binding",
        ],
        "errors": [],
    }


def _check_package_boundary(root: Path) -> None:
    allowed_evidence = {
        f"generation-evidence/{index:02d}-{phase}.json"
        for index, phase in enumerate(PHASES, 1)
    }
    execution = _read(root / "execution-record.json", "C1_EXECUTION_INVALID")
    allowed_implementation = {
        f"implementation/{item['identity']}"
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping) and isinstance(item.get("identity"), str)
    }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ALLOWED_ROOT_FILES:
            continue
        if relative in allowed_evidence or relative in allowed_implementation:
            continue
        if any(relative.startswith(prefix) for prefix in _ALLOWED_SOURCE_PREFIXES):
            continue
        _fail("C1_BOUNDARY_VIOLATION", relative)


def validate_c1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_package_boundary(root)
    model = _read(root / "character-system.json", "C1_MODEL_MISSING")
    manifest = _read(root / "package-manifest.json", "C1_MANIFEST_INVALID")
    stored = _read(root / "validation.json", "C1_VALIDATION_MISSING")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("C1_MANIFEST_INVALID", str(error))
    b0 = root / "sources" / "B0"
    s1 = root / "sources" / "S1"
    w1 = root / "sources" / "W1"
    e1 = root / "sources" / "E1"
    t1 = root / "sources" / "T1"
    try:
        rt.validate_baseline_package(b0, runtime=contract_runtime)
        s1_runtime.validate_s1_package(s1, runtime=contract_runtime)
        w1_runtime.validate_w1_package(w1, runtime=contract_runtime)
        e1_runtime.validate_e1_package(e1, runtime=contract_runtime)
        t1_runtime.validate_t1_package(t1, runtime=contract_runtime)
    except Exception as error:
        _fail("C1_UPSTREAM_INVALID", str(error))
    baseline = _read(b0 / "author-control-baseline.json", "C1_B0_INVALID")
    storyline = _read(s1 / "storyline-architecture.json", "C1_S1_INVALID")
    world = _read(w1 / "world-model.json", "C1_W1_INVALID")
    environment = _read(e1 / "environment-system.json", "C1_E1_INVALID")
    timeline = _read(t1 / "event-timeline.json", "C1_T1_INVALID")
    controls = _controls(b0, baseline)
    gate = _read(root / "input-gate.json", "C1_GATE_MISSING")
    try:
        contract_runtime.validate(gate, "input-gate.schema.json")
    except Exception as error:
        _fail("C1_GATE_INVALID", str(error))
    if rt.canonical_sha256(gate) != rt.sha256_file(root / "input-gate.json"):
        _fail("C1_GATE_INVALID", "stored gate is not canonical")
    gate_ref = {
        "path": model["input_gate"]["path"],
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    if not gate_ref["path"].endswith("/input-gate.json"):
        _fail("C1_GATE_REFERENCE_MISMATCH", "gate path not package-qualified")
    b0_ref, s1_ref, w1_ref, e1_ref, t1_ref = (
        _gate_selected_upstream_references(
            {"B0": b0, "S1": s1, "W1": w1, "E1": e1, "T1": t1},
            gate,
            run_id=model["run_id"],
            runtime=contract_runtime,
        )
    )
    if (
        gate.get("target_stage") != "C1"
        or gate.get("run_id") != model["run_id"]
        or gate.get("baseline_completion") != b0_ref
        or gate.get("upstream_completions") != [s1_ref, w1_ref, e1_ref, t1_ref]
    ):
        _fail("C1_GATE_INVALID", "stored C1 topology is invalid")
    expected_sources = _source_artifacts(b0, s1, w1, e1, t1)
    _validate_model(
        model,
        baseline,
        storyline,
        world,
        environment,
        timeline,
        controls,
        contract_runtime,
        expected_gate=gate_ref,
        expected_sources=expected_sources,
    )
    if manifest["artifact_roles"]["canonical"] != rt.artifact_reference(
        root / "character-system.json", root=root
    ):
        _fail("C1_MANIFEST_INVALID", "canonical role is stale")
    execution = _read(root / "execution-record.json", "C1_EXECUTION_INVALID")
    if (
        execution.get("input_gate") != gate_ref
        or execution.get("baseline_completion") != b0_ref
        or execution.get("upstream_completions") != [s1_ref, w1_ref, e1_ref, t1_ref]
        or execution.get("output_sha256") != rt.canonical_sha256(model)
    ):
        _fail("C1_EXECUTION_INVALID", "execution lineage is stale")
    session = _read(root / "generation-session.json", "C1_SESSION_INVALID")
    thread = session.get("thread_id")
    if not isinstance(thread, str) or not thread.strip():
        _fail("C1_SESSION_INVALID", "thread is missing")
    expected_session = _session_document(
        thread_id=thread,
        gate=gate_ref,
        state_before=gate.get("run_state"),
        roots=(b0, s1, w1, e1, t1),
        models=(baseline, storyline, world, environment, timeline),
        controls=controls,
        references=(b0_ref, s1_ref, w1_ref, e1_ref, t1_ref),
    )
    if session != expected_session:
        _fail("C1_SESSION_INVALID", "session differs from current inputs")
    if execution.get("session_id") != session["session_id"]:
        _fail("C1_SESSION_INVALID", "execution session differs")
    evidence_paths = _validate_phase_chain(
        root / "generation-evidence", session=session, model=model
    )
    evidence_index = _read(
        root / "generation-evidence-index.json", "C1_EVIDENCE_INVALID"
    )
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "C1",
        "session_id": session["session_id"],
        "phases": list(PHASES),
        "evidence": [
            rt.artifact_reference(path, root=root) for path in evidence_paths
        ],
    }:
        _fail("C1_EVIDENCE_INVALID", "evidence index is stale")
    catalog = {
        item["identity"]: item["artifact"]
        for item in execution.get("implementation_catalog", [])
    }
    try:
        _, catalog = stage_identity.validate_stage_catalog(
            stage="C1",
            records=execution.get("implementation_catalog"),
            package_root=root,
            current_paths=_implementation_paths(),
            verify_artifact_reference=rt.verify_artifact_reference,
            sha256_file=rt.sha256_file,
        )
    except stage_identity.StageImplementationIdentityError as error:
        _fail("C1_IMPLEMENTATION_STALE", str(error))
    expected_implementation_refs = {
        rt.canonical_json(
            rt.artifact_reference(
                root / "implementation" / identity,
                root=root,
            )
        )
        for identity in catalog
    }
    if (
        {
            rt.canonical_json(item)
            for item in execution.get("implementation", [])
        }
        != expected_implementation_refs
        or {
            rt.canonical_json(item) for item in manifest.get("implementation", [])
        }
        != expected_implementation_refs
        or {
            rt.canonical_json(item) for item in catalog.values()
        }
        != expected_implementation_refs
    ):
        _fail(
            "C1_IMPLEMENTATION_STALE",
            "implementation files, catalog, execution, and manifest differ",
        )
    if require_completion:
        completion = _read(
            root / "stage-completion.json", "C1_COMPLETION_MISSING"
        )
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("C1_COMPLETION_INVALID", str(error))
        manifest_ref = completion.get("manifest")
        manifest_path = (
            manifest_ref.get("path") if isinstance(manifest_ref, Mapping) else ""
        )
        prefix = PurePosixPath(manifest_path).parent.as_posix()
        if (
            not (prefix == "C1" or prefix.startswith("C1/"))
            or completion.get("run_id") != model["run_id"]
            or completion.get("stage") != "C1"
            or completion.get("status") != "ready"
            or completion.get("session_id") != session["session_id"]
            or completion.get("manifest")
            != {
                "path": _logical(prefix, "package-manifest.json"),
                "sha256": rt.sha256_file(root / "package-manifest.json"),
            }
            or completion.get("validation")
            != {
                "path": _logical(prefix, "validation.json"),
                "sha256": rt.sha256_file(root / "validation.json"),
            }
            or completion.get("input_gate") != gate_ref
            or completion.get("state_before") != gate.get("run_state")
            or completion.get("previous_stage_completions")
            != [s1_ref, w1_ref, e1_ref, t1_ref]
            or completion.get("return_binding") != gate.get("return_binding")
        ):
            _fail("C1_COMPLETION_BINDING_MISMATCH", "completion lineage is stale")
    expected_validation = _validation(model["run_id"])
    if stored != expected_validation:
        _fail("C1_VALIDATION_STALE", "stored validation differs")
    return expected_validation


def run_c1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controlled_workspace: str | Path,
    logical_package_path: str = "C1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> C1RunReceipt:
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("C1_OUTPUT_EXISTS", str(destination))
    if not os.environ.get("CODEX_THREAD_ID", "").strip():
        _fail("C1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    workspace = Path(controlled_workspace).resolve()
    session, baseline, storyline, world, environment, timeline, controls = _validated_session(
        workspace,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    final = _read(
        workspace
        / "generation-evidence"
        / f"{len(PHASES):02d}-{PHASES[-1]}.json",
        "C1_EVIDENCE_MISSING",
    )
    payload = final.get("payload")
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("model"), Mapping
    ):
        _fail("C1_EVIDENCE_INVALID", "final model missing")
    model = copy.deepcopy(dict(payload["model"]))
    _validate_phase_chain(
        workspace / "generation-evidence", session=session, model=model
    )
    _validate_model(
        model,
        baseline,
        storyline,
        world,
        environment,
        timeline,
        controls,
        contract_runtime,
        expected_gate=input_gate.reference,
        expected_sources=session["source_artifacts"],
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        for stage, source in (
            ("B0", Path(baseline_package).resolve()),
            ("S1", Path(storyline_package).resolve()),
            ("W1", Path(world_package).resolve()),
            ("E1", Path(environment_package).resolve()),
            ("T1", Path(event_package).resolve()),
        ):
            shutil.copytree(source, staging / "sources" / stage)
        _write(staging / "input-gate.json", input_gate.data)
        if _source_artifacts(
            staging / "sources" / "B0",
            staging / "sources" / "S1",
            staging / "sources" / "W1",
            staging / "sources" / "E1",
            staging / "sources" / "T1",
        ) != session["source_artifacts"]:
            _fail("C1_SOURCE_ARTIFACT_MISMATCH", "staged inputs changed")
        _write(staging / "character-system.json", model)
        evidence_refs = []
        for index, phase in enumerate(PHASES, 1):
            source = (
                workspace / "generation-evidence" / f"{index:02d}-{phase}.json"
            )
            target = staging / "generation-evidence" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            evidence_refs.append(rt.artifact_reference(target, root=staging))
        _write(
            staging / "generation-evidence-index.json",
            {
                "schema_version": "2.0",
                "run_id": baseline["run_id"],
                "stage": "C1",
                "session_id": session["session_id"],
                "phases": list(PHASES),
                "evidence": evidence_refs,
            },
        )
        _write(staging / "generation-session.json", session)
        implementation_refs = []
        implementation_catalog = []
        for identity, source in sorted(_implementation_paths().items()):
            target = staging / "implementation" / identity
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            reference = rt.artifact_reference(target, root=staging)
            implementation_refs.append(reference)
            implementation_catalog.append(
                {"identity": identity, "artifact": reference}
            )
        execution = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "C1",
            "operation": "controlled-character-system-generation",
            "session_id": session["session_id"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "baseline_completion": session["baseline_completion"],
            "upstream_completions": session["upstream_completions"],
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "output_sha256": rt.canonical_sha256(model),
        }
        _write(staging / "execution-record.json", execution)
        (staging / "character-preview.md").write_text(
            "# Character system\n\n"
            + "\n".join(
                f"- **{item['id']}** {item['name']}: "
                f"{item['story_responsibility']}"
                for item in model["profiles"]
            )
            + "\n",
            encoding="utf-8",
            newline="",
        )
        validation = _validation(baseline["run_id"])
        _write(staging / "validation.json", validation)
        files = [
            rt.artifact_reference(path, root=staging)
            for path in sorted(staging.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        ]
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "C1",
            "package_profile": "generated-model",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "canonical": by_path["character-system.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
                "preview": by_path["character-preview.md"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_c1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "C1",
            "status": "ready",
            "session_id": session["session_id"],
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
            "C1",
            _logical(logical_package_path, "stage-completion.json"),
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_c1_package(staging, runtime=contract_runtime)
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=sealed,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
        )
        staging.replace(destination)
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return C1RunReceipt(
        package_root=destination,
        model=copy.deepcopy(model),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
    )


__all__ = [
    "PHASES",
    "PHASE_FIELDS",
    "C1Error",
    "C1RunReceipt",
    "run_c1",
    "start_c1_session",
    "submit_c1_phase",
    "validate_c1_package",
]
