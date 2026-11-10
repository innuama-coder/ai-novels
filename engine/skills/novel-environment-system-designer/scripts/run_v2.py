"""Production E1 runner for autonomous novel-conception V2."""

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
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_S1_SKILL = _REPO / "skills" / "novel-storyline-architecture-designer"
_W1_SKILL = _REPO / "skills" / "novel-world-model-designer"
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"

PHASES = (
    "environment-demand-scan",
    "environment-architecture",
    "zones-and-topology",
    "storyline-hosting-test",
    "final-environment-model",
)
PHASE_FIELDS = {
    "environment-demand-scan": (
        "environment_demands",
        "storyline_environment_requirements",
        "story_transition_universe_digest",
        "milestone_universe_digest",
        "connection_universe_digest",
        "obligation_universe_digest",
    ),
    "environment-architecture": (
        "design_decisions",
        "environments",
        "initial_anchor_support",
    ),
    "zones-and-topology": (
        "functional_zones",
        "environment_topology",
        "access_and_authority",
        "resource_and_information_channels",
        "hazards_and_failure_modes",
        "transition_contracts",
        "event_affordance_catalog",
        "capability_fact_registry",
        "capability_step_registry",
        "ambient_context_hosts",
        "actor_authority_bindings",
        "capability_occurrence_requirements",
    ),
    "storyline-hosting-test": (
        "storyline_hosting_ledger",
        "story_transition_support",
        "connection_path_readiness",
        "milestone_capability_readiness",
        "obligation_capability_readiness",
        "obligation_occurrence_bindings",
        "initial_anchor_option_realization_ledger",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-environment-model": ("model",),
}
LEGACY_PHASE_FIELDS = {
    "environment-demand-scan": (
        "environment_demands",
        "storyline_environment_requirements",
    ),
    "environment-architecture": ("design_decisions", "environments"),
    "zones-and-topology": (
        "functional_zones",
        "environment_topology",
        "access_and_authority",
        "resource_and_information_channels",
        "hazards_and_failure_modes",
        "transition_contracts",
    ),
    "storyline-hosting-test": (
        "storyline_hosting_ledger",
        "event_affordance_catalog",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-environment-model": ("model",),
}
PHASE_FIELDS_BY_VERSION = {
    # The historical releases happen to freeze the same root fields, but each
    # version owns an explicit table so public replay never infers phase
    # ownership from an untrusted payload.
    "2.0": dict(LEGACY_PHASE_FIELDS),
    "2.1": dict(LEGACY_PHASE_FIELDS),
    "2.2": dict(LEGACY_PHASE_FIELDS),
    "2.3": dict(LEGACY_PHASE_FIELDS),
    "2.4": dict(PHASE_FIELDS),
}
SEMANTIC_PROFILE_BY_VERSION = {
    "2.0": "legacy-common",
    "2.1": "legacy-trigger-binding",
    "2.2": "legacy-structured-hosting-exact-once",
    "2.3": "legacy-structured-hosting-multi-affordance",
    "2.4": "capability-readiness",
}
_FORBIDDEN_MODEL_KEYS = {
    "storylines",
    "events",
    "event_timeline",
    "event_results",
    "characters",
    "character_profiles",
    "scenes",
    "scene_text",
    "prose",
}
_FORBIDDEN_NESTED_KEYS = {
    "outcome",
    "result",
    "initiator",
    "scheduled_time",
    "scene_text",
    "dialogue",
    "camera",
}
_ALLOWED_ROOT_FILES = {
    "input-gate.json",
    "environment-system.json",
    "generation-session.json",
    "generation-evidence-index.json",
    "execution-record.json",
    "environment-preview.md",
    "validation.json",
    "package-manifest.json",
    "stage-completion.json",
}
_ALLOWED_SOURCE_PREFIXES = (
    "sources/B0/",
    "sources/S1/",
    "sources/W1/",
)
CURRENT_MODEL_SCHEMA_VERSION = "2.4"
LEGACY_MODEL_SCHEMA_VERSIONS = frozenset({"2.0", "2.1", "2.2", "2.3"})
AUTHORITY_REVIEW_PROTOCOL = "e1-authority-capability-semantics-v1"
HOSTING_REVIEW_PROTOCOL = "e1-transition-support-semantics-v1"
LEGACY_HOSTING_REVIEW_PROTOCOL = "e1-hosting-semantics-v1"
_TRUSTED_LEGACY_IMPLEMENTATION_PAIRS = {
    "2.0": frozenset(
        {
            (
                "db7cbeecef75822f5fae43af78d13986ccc31b58de82394cfcf22818163fdf27",
                "be167a00922ea1d6c930610382e9c00cf236d9794ad7d3a05a41a5dd773ba6d3",
            )
        }
    ),
    # No schema-2.1 E1 package was released; structural reading remains
    # implemented, but public package verification grants no provenance by
    # version label alone.
    "2.1": frozenset(),
    # Schema 2.2 was the last structured-hosting production contract.  Its
    # exact runtime/schema pair remains verifiable as history, never generative.
    "2.2": frozenset(
        {
            (
                "d5c2198540c12c6bf57f093e1d3532ddf32ffe5dc506fb1b7e6d73072cdeef57",
                "d597ee0e9ed3df3e974d2e49ad73cb45738ab9c00baa5dae0304ffe9bcf96bde",
            )
        }
    ),
    "2.3": frozenset(
        {
            (
                "83c114392eae16736aa8ad9c97c3913cc023d90424b827ad296d6e1c1a15ee7c",
                "68e30162129f79469d02caf27f524f34dbaab224da78b091ff59008c4db25942",
            )
        }
    ),
}
_TRUSTED_LEGACY_PACKAGE_IDENTITIES = {
    "2.0": frozenset(
        {
            (
                "c3081c28f88cd825609229ee624321c751ea67aca626573cb4439fb8d0fb3d16",
                "6c44750e71e1a6013d1e27e87f2666bc7a6863e61cfa0823e2f45130bd3a4ea9",
                "92df6bd368e9a8d6b0cfab1f9f6a6fd20f7ccd4d333c2015e2b3fa9d1064ddd5",
            )
        }
    ),
    "2.1": frozenset(),
    "2.2": frozenset(
        {
            (
                "bc86ca010fe27b447be697146a986d5ce914c2856077ac78ee53505917294696",
                "4a1f1ce1f99d1ac1e0aff6f1b8eb7b737b2313d029f77691811015d3981bbd7d",
                "bedae14d280e504ee372130dd7f5e67de411735887164baee8026846137fd2fe",
            )
        }
    ),
    "2.3": frozenset(
        {
            (
                "8e99df49c1abea79c22b4e10b8223580f2e953f1bcace39892086ebfcf19fcd0",
                "380dcb36ceb536b0837345dea9b2ac500fe78fe72cbbf006289e176dc41247cd",
                "d40226c1c610b1a54d65994a19645f107481a9f235090f93f15694c8f4ec93ca",
            )
        }
    ),
}


class E1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class E1RunReceipt:
    package_root: Path
    model: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any


def _fail(code: str, message: str) -> None:
    raise E1Error(code, message)


def _validate_authority_disjoint(partition: Mapping[str, Any]) -> None:
    names = (
        "author_locked",
        "autonomous_owned",
        "downstream_freedom",
        "author_open",
    )
    values = {name: set(partition[name]) for name in names}
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = sorted(values[left] & values[right])
            if overlap:
                _fail(
                    "E1_AUTHORITY_PARTITION_OVERLAP",
                    f"{left}/{right}: {overlap}",
                )


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


def _is_current_model(model: Mapping[str, Any]) -> bool:
    version = model.get("schema_version")
    if version == CURRENT_MODEL_SCHEMA_VERSION:
        return True
    if version in LEGACY_MODEL_SCHEMA_VERSIONS:
        return False
    _fail("E1_MODEL_SCHEMA_VERSION_UNSUPPORTED", str(version))


def _phase_fields_for_version(
    model_schema_version: str, phase: str
) -> tuple[str, ...]:
    table = PHASE_FIELDS_BY_VERSION.get(model_schema_version)
    if table is None or phase not in table:
        _fail(
            "E1_MODEL_SCHEMA_VERSION_UNSUPPORTED",
            f"{model_schema_version}:{phase}",
        )
    return tuple(table[phase])


def _semantic_profile(model_schema_version: str) -> str:
    profile = SEMANTIC_PROFILE_BY_VERSION.get(model_schema_version)
    if profile is None:
        _fail("E1_MODEL_SCHEMA_VERSION_UNSUPPORTED", model_schema_version)
    return profile


def _validate_legacy_package_provenance(
    model: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, str]],
) -> None:
    version = model.get("schema_version")
    runtime_ref = catalog.get("skill/run_v2.py")
    schema_ref = catalog.get("schemas/environment-system.schema.json")
    pair = (
        runtime_ref.get("sha256") if isinstance(runtime_ref, Mapping) else None,
        schema_ref.get("sha256") if isinstance(schema_ref, Mapping) else None,
    )
    if pair not in _TRUSTED_LEGACY_IMPLEMENTATION_PAIRS.get(version, frozenset()):
        _fail("E1_LEGACY_PROVENANCE_UNTRUSTED", f"{version}: {pair}")


def _validate_legacy_package_identity(
    root: Path, model: Mapping[str, Any]
) -> None:
    identity = (
        rt.sha256_file(root / "package-manifest.json"),
        rt.sha256_file(root / "stage-completion.json"),
        rt.sha256_file(root / "environment-system.json"),
    )
    if identity not in _TRUSTED_LEGACY_PACKAGE_IDENTITIES.get(
        model.get("schema_version"), frozenset()
    ):
        _fail(
            "E1_LEGACY_PACKAGE_IDENTITY_UNTRUSTED",
            f"{model.get('schema_version')}: {identity}",
        )


def _validate_legacy_upstream_snapshot(
    root: Path,
    *,
    stage: str,
    canonical_name: str,
    runtime: Any,
) -> None:
    manifest = _read(root / "package-manifest.json", f"E1_{stage}_INVALID")
    completion = _read(root / "stage-completion.json", f"E1_{stage}_INVALID")
    try:
        runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail(f"E1_{stage}_INVALID", str(error))
    canonical = rt.artifact_reference(root / canonical_name, root=root)
    canonical_entries = [
        item
        for item in manifest.get("files", [])
        if isinstance(item, Mapping) and item.get("path") == canonical_name
    ]
    legacy_role = manifest.get("artifact_roles", {}).get("canonical")
    if (
        canonical_entries != [canonical]
        or (legacy_role is not None and legacy_role != canonical)
        or completion.get("stage") != stage
        or completion.get("status") != "ready"
        or completion.get("manifest", {}).get("sha256")
        != rt.sha256_file(root / "package-manifest.json")
    ):
        _fail(f"E1_{stage}_INVALID", "legacy upstream snapshot is unbound")


def _logical(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        _fail("E1_PATH_INVALID", value)
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
        "environment-system.schema.json",
        "canonical-common.schema.json",
        "common-defs.schema.json",
        "input-gate.schema.json",
        "package-manifest.schema.json",
        "stage-completion.schema.json",
    ):
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


def _implementation_bindings() -> list[dict[str, str]]:
    return [
        {"identity": identity, "sha256": rt.sha256_file(path)}
        for identity, path in sorted(_implementation_paths().items())
    ]


def _review_source_bindings(s1_root: Path, w1_root: Path) -> dict[str, Any]:
    """Return the explicit sealed sources consumed by both semantic reviews."""

    return {
        "upstream_artifacts": [
            {
                "stage": stage,
                "completion": {
                    "path": f"sources/{stage}/stage-completion.json",
                    "sha256": rt.sha256_file(root / "stage-completion.json"),
                },
                "manifest": {
                    "path": f"sources/{stage}/package-manifest.json",
                    "sha256": rt.sha256_file(root / "package-manifest.json"),
                },
            }
            for stage, root in (("S1", s1_root), ("W1", w1_root))
        ],
        "contract_bindings": {
            "schema_sha256": rt.sha256_file(
                _SCHEMAS / "environment-system.schema.json"
            ),
            "authority_review_protocol_sha256": rt.canonical_sha256(
                AUTHORITY_REVIEW_PROTOCOL
            ),
            "hosting_review_protocol_sha256": rt.canonical_sha256(
                HOSTING_REVIEW_PROTOCOL
            ),
        },
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
    """Prove that a gate-selected completion belongs to ``package_root``.

    Rebuilt stages live below immutable attempt workspaces.  Their coordinator
    gate therefore owns the logical completion path; the physical directory
    supplied to E1 is not required to be named after the stage.  The logical
    completion, manifest, and validation paths must still be canonical
    siblings, while their hashes and bodies must bind the actual package root.
    """

    code = f"E1_{stage}_INVALID"
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
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
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


def _source_artifacts(
    b0_root: Path, s1_root: Path, w1_root: Path
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
) -> str:
    return "E1-" + rt.canonical_sha256([thread_id, gate, b0, s1, w1])[:20]


def _session_context(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    Path,
    Path,
    Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    b0_root = Path(baseline_package).resolve()
    s1_root = Path(storyline_package).resolve()
    w1_root = Path(world_package).resolve()
    if full_validation:
        try:
            rt.validate_baseline_package(b0_root, runtime=runtime)
        except Exception as error:
            _fail("E1_B0_INVALID", str(error))
        try:
            s1_runtime.validate_s1_package(s1_root, runtime=runtime)
        except Exception as error:
            _fail("E1_S1_INVALID", str(error))
        try:
            w1_runtime.validate_w1_package(w1_root, runtime=runtime)
        except Exception as error:
            _fail("E1_W1_INVALID", str(error))
    baseline = _read(
        b0_root / "author-control-baseline.json", "E1_B0_INVALID"
    )
    storyline = _read(
        s1_root / "storyline-architecture.json", "E1_S1_INVALID"
    )
    world = _read(w1_root / "world-model.json", "E1_W1_INVALID")
    if {baseline["run_id"], storyline["run_id"], world["run_id"]} != {
        baseline["run_id"]
    }:
        _fail("E1_RUN_ID_MISMATCH", "B0/S1/W1 runs differ")
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("E1_GATE_INVALID", str(error))
    if rt.canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("E1_GATE_INVALID", "gate reference does not bind its body")
    sealed_b0 = input_gate.data.get("baseline_completion")
    sealed_upstreams = input_gate.data.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 2
        or any(not isinstance(item, Mapping) for item in sealed_upstreams)
    ):
        _fail("E1_GATE_INVALID", "gate does not select exactly B0, S1, and W1")
    b0_ref = _sealed_upstream_reference(
        b0_root,
        sealed_b0,
        stage="B0",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    s1_ref = _sealed_upstream_reference(
        s1_root,
        sealed_upstreams[0],
        stage="S1",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    w1_ref = _sealed_upstream_reference(
        w1_root,
        sealed_upstreams[1],
        stage="W1",
        run_id=baseline["run_id"],
        previous_stage_completions=[s1_ref],
        runtime=runtime,
    )
    try:
        _require_embedded_completion(
            s1_root / "sources" / "B0" / "stage-completion.json",
            b0_ref,
            code="E1_UPSTREAM_LINEAGE_MISMATCH",
        )
        _require_embedded_completion(
            w1_root / "sources" / "B0" / "stage-completion.json",
            b0_ref,
            code="E1_UPSTREAM_LINEAGE_MISMATCH",
        )
        _require_embedded_completion(
            w1_root / "sources" / "S1" / "stage-completion.json",
            s1_ref,
            code="E1_UPSTREAM_LINEAGE_MISMATCH",
        )
    except E1Error:
        raise
    except (OSError, KeyError) as error:
        _fail("E1_UPSTREAM_LINEAGE_MISMATCH", str(error))
    if (
        input_gate.data.get("target_stage") != "E1"
        or input_gate.data.get("run_id") != baseline["run_id"]
        or input_gate.data.get("baseline_completion") != b0_ref
        or input_gate.data.get("upstream_completions") != [s1_ref, w1_ref]
        or rt.canonical_sha256(input_gate.data)
        != input_gate.reference.get("sha256")
    ):
        _fail("E1_GATE_INVALID", "gate is not the exact E1/B0/S1/W1 gate")
    return (
        b0_root,
        s1_root,
        w1_root,
        baseline,
        storyline,
        world,
        _controls(b0_root, baseline),
        b0_ref,
        s1_ref,
        w1_ref,
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
        _fail("E1_BOUNDARY_VIOLATION", f"forbidden top-level fields: {forbidden}")
    nested = _nested_forbidden(model)
    if nested is not None:
        _fail("E1_BOUNDARY_VIOLATION", f"forbidden event/prose field: {nested}")


def _reachable(environment_ids: set[str], edges: Sequence[Mapping[str, Any]]) -> bool:
    if not environment_ids:
        return False
    adjacency = {item: set() for item in environment_ids}
    for edge in edges:
        left, right = edge["from_id"], edge["to_id"]
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    stack = [next(iter(environment_ids))]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stack.extend(adjacency[current] - visited)
    return visited == environment_ids


def _channel_tokens(value: Mapping[str, Any], kind: str) -> set[str]:
    pattern = re.compile(rf"\[{re.escape(kind)}:([^\[\]]+)\]")
    return set(pattern.findall(rt.canonical_json(value)))


def _storyline_states(line: Mapping[str, Any]) -> list[str]:
    return [line["start_state"], *line["state_changes"], line["end_state"]]


def _validate_topology_path(
    path_ids: Sequence[str],
    *,
    source_environment_id: str,
    target_environment_id: str,
    transport_capability: str,
    topology: Mapping[str, Mapping[str, Any]],
    transition_id: str,
) -> None:
    if source_environment_id == target_environment_id:
        if path_ids or transport_capability != "local":
            _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
        return
    if not path_ids or transport_capability == "local":
        _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
    current = source_environment_id
    visited = {current}
    for edge_id in path_ids:
        edge = topology.get(edge_id)
        if edge is None or transport_capability not in edge["transfer_capabilities"]:
            _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
        if edge["from_id"] == current:
            next_environment = edge["to_id"]
        elif edge["to_id"] == current and edge["directionality"] == "bidirectional":
            next_environment = edge["from_id"]
        else:
            _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
        if next_environment in visited:
            _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
        visited.add(next_environment)
        current = next_environment
    if current != target_environment_id:
        _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)


def _validate_transition_trigger_bindings(
    transitions: Sequence[Mapping[str, Any]],
    *,
    environments: Mapping[str, Mapping[str, Any]],
    topology: Mapping[str, Mapping[str, Any]],
    assignments: Mapping[str, Mapping[str, Any]],
    affordances: Mapping[str, Mapping[str, Any]] | None,
    storyline: Mapping[str, Any],
    event_requirement_line: Mapping[str, str] | None,
) -> None:
    lines = {item["id"]: item for item in storyline["storylines"]}
    connections = {item["id"]: item for item in storyline["connections"]}
    obligations = {
        item["id"]: item for item in storyline["story_obligation_register"]
    }
    binding_fields = {
        "trigger_id",
        "source_environment_id",
        "source_storyline_id",
        "source_state_index",
        "target_storyline_id",
        "target_state_index",
        "causal_evidence_ids",
        "topology_path_ids",
        "transport_capability",
    }
    for transition in transitions:
        transition_id = transition.get("id", "transition")
        target_environment = environments.get(transition.get("subject_id"))
        if target_environment is None:
            _fail("E1_TRANSITION_SUBJECT_DANGLING", transition_id)
        bindings = transition.get("trigger_bindings")
        if not isinstance(bindings, list) or not bindings:
            _fail("E1_TRANSITION_TRIGGER_BINDING_INVALID", transition_id)
        trigger_ids = transition.get("trigger_ids")
        if (
            not isinstance(trigger_ids, list)
            or len(trigger_ids) != len(set(trigger_ids))
            or set(trigger_ids) != {
            binding.get("trigger_id")
            for binding in bindings
            if isinstance(binding, Mapping)
            }
        ):
            _fail("E1_TRANSITION_TRIGGER_BINDING_MISMATCH", transition_id)
        if len({rt.canonical_json(item) for item in bindings}) != len(bindings):
            _fail("E1_TRANSITION_TRIGGER_BINDING_INVALID", transition_id)

        trigger_source_environments: dict[str, str] = {}
        for binding in bindings:
            if not isinstance(binding, Mapping) or set(binding) != binding_fields:
                _fail("E1_TRANSITION_TRIGGER_BINDING_INVALID", transition_id)
            trigger_id = binding.get("trigger_id")
            if not isinstance(trigger_id, str) or re.fullmatch(
                r"AFF-[A-Za-z0-9._-]+", trigger_id
            ) is None:
                _fail("E1_TRANSITION_TRIGGER_BINDING_INVALID", transition_id)
            source_environment_id = binding.get("source_environment_id")
            prior_source_environment = trigger_source_environments.setdefault(
                trigger_id, source_environment_id
            )
            if prior_source_environment != source_environment_id:
                _fail("E1_TRANSITION_TRIGGER_BINDING_MISMATCH", transition_id)
            source_environment = environments.get(source_environment_id)
            source_line_id = binding.get("source_storyline_id")
            target_line_id = binding.get("target_storyline_id")
            source_line = lines.get(source_line_id)
            target_line = lines.get(target_line_id)
            if source_environment is None or source_line is None or target_line is None:
                _fail("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", transition_id)
            if (
                source_line_id not in source_environment["storyline_stage_ids"]
                or target_line_id not in target_environment["storyline_stage_ids"]
            ):
                _fail("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", transition_id)
            if affordances is not None and event_requirement_line is not None:
                affordance = affordances.get(trigger_id)
                if affordance is None:
                    _fail("E1_TRANSITION_TRIGGER_INVALID", transition_id)
                if source_environment_id != affordance["environment_id"]:
                    _fail("E1_TRANSITION_TRIGGER_BINDING_MISMATCH", transition_id)
                affordance_lines = {
                    event_requirement_line.get(requirement_id)
                    for requirement_id in affordance["event_requirement_ids"]
                }
                if source_line_id not in affordance_lines:
                    _fail("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", transition_id)
            source_index = binding.get("source_state_index")
            target_index = binding.get("target_state_index")
            if (
                not isinstance(source_index, int)
                or isinstance(source_index, bool)
                or not 0 <= source_index < len(_storyline_states(source_line))
                or not isinstance(target_index, int)
                or isinstance(target_index, bool)
                or not 0 <= target_index < len(_storyline_states(target_line))
                or (
                    source_line_id == target_line_id
                    and source_index > target_index
                )
            ):
                _fail("E1_TRANSITION_TRIGGER_ANCHOR_INVALID", transition_id)
            if (
                source_line["type"] == "optional_melody"
                and target_line["type"] != "optional_melody"
            ):
                _fail("E1_OPTIONAL_TRIGGER_ESCALATION", transition_id)

            topology_path_ids = binding.get("topology_path_ids")
            transport_capability = binding.get("transport_capability")
            if not isinstance(topology_path_ids, list) or not isinstance(
                transport_capability, str
            ):
                _fail("E1_TRIGGER_TOPOLOGY_PATH_INVALID", transition_id)
            _validate_topology_path(
                topology_path_ids,
                source_environment_id=source_environment_id,
                target_environment_id=target_environment["id"],
                transport_capability=transport_capability,
                topology=topology,
                transition_id=transition_id,
            )

            permission_environment_ids = {
                assignments[assignment_id]["subject_id"]
                for assignment_id in transition.get("allowed_by_ids", [])
                if assignment_id in assignments
            }
            if not {
                source_environment_id,
                target_environment["id"],
            }.issubset(permission_environment_ids):
                _fail("E1_TRIGGER_PERMISSION_COVERAGE_INVALID", transition_id)

            evidence_ids = binding.get("causal_evidence_ids")
            if not isinstance(evidence_ids, list) or (
                source_line_id != target_line_id and not evidence_ids
            ) or len(evidence_ids) != len(set(evidence_ids)):
                _fail("E1_TRIGGER_CAUSAL_EVIDENCE_INVALID", transition_id)
            source_anchor = (source_line_id, source_index)
            target_anchor = (target_line_id, target_index)
            for evidence_id in evidence_ids:
                if evidence_id in connections:
                    connection = connections[evidence_id]
                    valid = (
                        connection["relation"] == "causal"
                        and (
                            connection["from_storyline_id"],
                            connection["from_state_index"],
                        )
                        == source_anchor
                        and (
                            connection["to_storyline_id"],
                            connection["to_state_index"],
                        )
                        == target_anchor
                    )
                elif evidence_id in obligations:
                    obligation = obligations[evidence_id]
                    antecedents = {
                        (item["storyline_id"], item["state_index"])
                        for item in obligation["antecedent_anchors"]
                    }
                    consequent = obligation["consequent_anchor"]
                    valid = (
                        obligation["kind"] in {"causes", "requires_all"}
                        and source_anchor in antecedents
                        and (
                            consequent["storyline_id"],
                            consequent["state_index"],
                        )
                        == target_anchor
                    )
                else:
                    valid = False
                if not valid:
                    _fail("E1_TRIGGER_CAUSAL_EVIDENCE_INVALID", transition_id)

        for obligation_id, obligation in obligations.items():
            if obligation["kind"] != "requires_all" or not any(
                obligation_id in binding["causal_evidence_ids"]
                for binding in bindings
            ):
                continue
            consequent = obligation["consequent_anchor"]
            target_anchor = (
                consequent["storyline_id"],
                consequent["state_index"],
            )
            required = {
                (item["storyline_id"], item["state_index"])
                for item in obligation["antecedent_anchors"]
            }
            covered = {
                (binding["source_storyline_id"], binding["source_state_index"])
                for binding in bindings
                if obligation_id in binding["causal_evidence_ids"]
                and (
                    binding["target_storyline_id"],
                    binding["target_state_index"],
                )
                == target_anchor
            }
            if covered != required:
                _fail("E1_TRIGGER_REQUIRES_ALL_INCOMPLETE", transition_id)


_HOSTING_SCALAR_POINTER_FIELDS = {
    "scope",
    "narrative_responsibility",
}
_HOSTING_LIST_POINTER_FIELDS = {
    "features",
    "sensory_conditions",
    "access_rules",
    "resources",
    "allowed_actions",
    "hazards",
    "blockers",
    "state_vocabulary",
}


def _resolve_hosting_projection(
    environment: Mapping[str, Any], pointer: str
) -> str:
    if not isinstance(pointer, str):
        _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", "pointer is not a string")
    parts = pointer.split("/")
    if len(parts) == 2 and parts[0] == "" and parts[1] in (
        _HOSTING_SCALAR_POINTER_FIELDS
    ):
        value = environment.get(parts[1])
    elif (
        len(parts) == 3
        and parts[0] == ""
        and parts[1] in _HOSTING_LIST_POINTER_FIELDS
        and parts[2].isdigit()
    ):
        values = environment.get(parts[1])
        index = int(parts[2])
        value = (
            values[index]
            if isinstance(values, list) and 0 <= index < len(values)
            else None
        )
    else:
        value = None
    if not isinstance(value, str) or not value.strip():
        _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", pointer)
    return value


def _hosting_source_binding(
    source: Mapping[str, Any], *, source_kind: str, storyline_id: str
) -> dict[str, Any]:
    return {
        "source_id": source["id"],
        "source_kind": source_kind,
        "storyline_id": storyline_id,
        "responsibility_sha256": rt.canonical_sha256(source["responsibility"]),
        "constraint_sha256s": [
            rt.canonical_sha256(item) for item in source["constraints"]
        ],
    }


def _contains_verbatim_source_text(value: Any, source_text: str) -> bool:
    if isinstance(value, str):
        return source_text in value
    if isinstance(value, Mapping):
        return any(
            _contains_verbatim_source_text(child, source_text)
            for child in value.values()
        )
    if isinstance(value, list):
        return any(
            _contains_verbatim_source_text(child, source_text) for child in value
        )
    return False


def _validate_environment_source_text_clean(
    environments: Mapping[str, Mapping[str, Any]],
    sources: Sequence[Mapping[str, Any]],
) -> None:
    responsibilities = {
        source["id"]: source["responsibility"] for source in sources
    }
    constraints = {
        constraint for source in sources for constraint in source["constraints"]
    }
    operational_constraint_fields = {"access_rules", "blockers", "hazards"}
    for environment_id, environment in environments.items():
        polluted_responsibility = next(
            (
                source_id
                for source_id, responsibility in responsibilities.items()
                if _contains_verbatim_source_text(environment, responsibility)
            ),
            None,
        )
        if polluted_responsibility is not None:
            _fail(
                "E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION",
                f"{environment_id} copies {polluted_responsibility}.responsibility",
            )
        non_operational = {
            key: value
            for key, value in environment.items()
            if key not in operational_constraint_fields
        }
        if any(
            _contains_verbatim_source_text(non_operational, constraint)
            for constraint in constraints
        ):
            _fail("E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION", environment_id)
        if any(
            marker in rt.canonical_json(environment)
            for marker in (
                "[DEMAND:",
                "[SUPPORT:",
                "[MARKER_SHA256:",
                "[ACTION_SHA256:",
                '"responsibility":',
                '"constraints":',
            )
        ):
            _fail("E1_ENVIRONMENT_SOURCE_TEXT_POLLUTION", environment_id)


def _validate_structured_hosting_evidence(
    record: Mapping[str, Any],
    *,
    demand: Mapping[str, Any],
    storyline_requirement: Mapping[str, Any],
    storyline_id: str,
    environments: Mapping[str, Mapping[str, Any]],
) -> None:
    evidence = record.get("evidence")
    if not isinstance(evidence, Mapping) or set(evidence) != {
        "source_bindings",
        "realization_bindings",
    }:
        _fail("E1_SOURCE_MEANING_UNBOUND", record["id"])
    expected_bindings = [
        _hosting_source_binding(
            demand,
            source_kind="world_environment_demand",
            storyline_id=storyline_id,
        ),
        _hosting_source_binding(
            storyline_requirement,
            source_kind="storyline_environment_requirement",
            storyline_id=storyline_id,
        ),
    ]
    if (
        record["source_ids"] != [demand["id"], storyline_requirement["id"]]
        or evidence.get("source_bindings") != expected_bindings
    ):
        _fail("E1_SOURCE_MEANING_UNBOUND", record["id"])

    realization_bindings = evidence.get("realization_bindings")
    if not isinstance(realization_bindings, list) or not realization_bindings:
        _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", record["id"])
    if record["realization_ids"] != [
        item.get("environment_id")
        for item in realization_bindings
        if isinstance(item, Mapping)
    ]:
        _fail("E1_HOSTING_COVERAGE_MISMATCH", record["id"])

    expected_tokens = {
        (
            binding["source_id"],
            "responsibility",
            binding["responsibility_sha256"],
        )
        for binding in expected_bindings
    } | {
        (binding["source_id"], "constraint", constraint_sha256)
        for binding in expected_bindings
        for constraint_sha256 in binding["constraint_sha256s"]
    }
    observed_tokens: list[tuple[str, str, str]] = []
    for realization in realization_bindings:
        if not isinstance(realization, Mapping) or set(realization) != {
            "environment_id",
            "local_projections",
        }:
            _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", record["id"])
        environment_id = realization.get("environment_id")
        environment = environments.get(environment_id)
        if environment is None:
            _fail("E1_HOSTING_ENVIRONMENT_DANGLING", record["id"])
        projections = realization.get("local_projections")
        if not isinstance(projections, list) or not projections:
            _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", environment_id)
        for projection in projections:
            if not isinstance(projection, Mapping) or set(projection) != {
                "source_id",
                "token_kind",
                "token_sha256",
                "environment_pointer",
                "projection_sha256",
                "rationale",
            }:
                _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", environment_id)
            token = (
                projection.get("source_id"),
                projection.get("token_kind"),
                projection.get("token_sha256"),
            )
            value = _resolve_hosting_projection(
                environment, projection.get("environment_pointer", "")
            )
            if (
                token not in expected_tokens
                or projection.get("projection_sha256")
                != rt.canonical_sha256(value)
                or not isinstance(projection.get("rationale"), str)
                or not projection["rationale"].strip()
            ):
                _fail("E1_HOSTING_LOCAL_PROJECTION_INVALID", environment_id)
            observed_tokens.append(token)
    if (
        set(observed_tokens) != expected_tokens
        or len(observed_tokens) != len(expected_tokens)
    ):
        _fail("E1_SOURCE_MEANING_UNBOUND", record["id"])


def _validate_affordance_catalog(
    catalog: Sequence[Mapping[str, Any]],
    *,
    environments: Mapping[str, Mapping[str, Any]],
    event_requirements: Mapping[str, Mapping[str, Any]],
    event_requirement_line: Mapping[str, str],
    hosted_lines_by_environment: Mapping[str, set[str]],
    model_version: str,
) -> dict[str, Mapping[str, Any]]:
    profile = _semantic_profile(model_version)
    multi_affordance = profile in {
        "legacy-structured-hosting-multi-affordance",
        "capability-readiness",
    }
    affordances = {item["id"]: item for item in catalog}
    if len(affordances) != len(catalog):
        _fail("E1_ID_DUPLICATE", "affordance IDs repeat")
    observed_event_requirements: list[str] = []
    semantic_signatures: dict[str, str] = {}
    for affordance in affordances.values():
        environment = environments.get(affordance["environment_id"])
        if environment is None:
            _fail("E1_AFFORDANCE_ENVIRONMENT_DANGLING", affordance["id"])
        if not affordance["allowed_actions"]:
            _fail("E1_ACTION_INTERFACE_MISSING", affordance["id"])
        local_actions = set(environment["allowed_actions"])
        if multi_affordance and not set(
            affordance["allowed_actions"]
        ).issubset(local_actions):
            _fail("E1_ACTION_INTERFACE_FOREIGN", affordance["id"])
        if not multi_affordance and not any(
            action in local_actions for action in affordance["allowed_actions"]
        ):
            _fail("E1_ACTION_INTERFACE_MISSING", affordance["id"])
        if multi_affordance:
            signature = rt.canonical_sha256(
                {
                    "environment_id": affordance["environment_id"],
                    "event_requirement_ids": sorted(
                        affordance["event_requirement_ids"]
                    ),
                    "allowed_actions": sorted(affordance["allowed_actions"]),
                    "prerequisites": sorted(affordance["prerequisites"]),
                    "constraints": sorted(affordance["constraints"]),
                }
            )
            prior_id = semantic_signatures.setdefault(signature, affordance["id"])
            if prior_id != affordance["id"]:
                _fail(
                    "E1_AFFORDANCE_SEMANTIC_DUPLICATE",
                    f"{prior_id}/{affordance['id']}",
                )
        for requirement_id in affordance["event_requirement_ids"]:
            if requirement_id not in event_requirements:
                _fail("E1_EVENT_REQUIREMENT_DANGLING", affordance["id"])
            if event_requirement_line[requirement_id] not in (
                hosted_lines_by_environment[environment["id"]]
            ):
                _fail("E1_AFFORDANCE_LINE_MISMATCH", affordance["id"])
            observed_event_requirements.append(requirement_id)
    coverage_incomplete = set(observed_event_requirements) != set(
        event_requirements
    )
    legacy_coverage_repeats = not multi_affordance and (
        len(observed_event_requirements) != len(set(observed_event_requirements))
    )
    if coverage_incomplete or legacy_coverage_repeats:
        _fail(
            "E1_ACTION_INTERFACE_MISSING",
            "every S1 event requirement needs at least one affordance",
        )
    return affordances


def _transition_key(storyline_id: str, from_index: int) -> str:
    return f"{storyline_id}:{from_index}->{from_index + 1}"


def _anchor_transition_key(anchor: Mapping[str, Any]) -> str | None:
    """Return the transition that establishes an S1 state anchor.

    State zero is an initial truth and therefore deliberately has no producer
    transition.  Keeping this distinction explicit prevents an initial anchor
    from being treated as a story event.
    """
    index = anchor["state_index"]
    return None if index == 0 else _transition_key(anchor["storyline_id"], index - 1)


def _s1_structural_precedence(
    storyline: Mapping[str, Any],
) -> tuple[set[str], dict[str, tuple[str, str]], dict[str, set[str]]]:
    """Build the sealed S1 transition partial order, never a T1 time order."""
    transitions = {
        _transition_key(item["storyline_id"], item["from_state_index"])
        for item in _v24_transition_universe(storyline)
    }
    edges: dict[str, tuple[str, str]] = {}

    def add(edge_id: str, source: str | None, target: str | None) -> None:
        if source is None or target is None:
            return
        if source not in transitions or target not in transitions or source == target:
            return
        projected = (source, target)
        if edge_id in edges and edges[edge_id] != projected:
            _fail("E1_S1_PRECEDENCE_EDGE_AMBIGUOUS", edge_id)
        edges[edge_id] = projected

    for line in storyline["storylines"]:
        count = len(_storyline_states(line)) - 1
        for index in range(count - 1):
            add(
                f"S1-ORDER:{line['id']}:{index}>{index + 1}",
                _transition_key(line["id"], index),
                _transition_key(line["id"], index + 1),
            )
    for connection in storyline["connections"]:
        if connection["relation"] == "causal":
            add(
                connection["id"],
                _anchor_transition_key(
                    {
                        "storyline_id": connection["from_storyline_id"],
                        "state_index": connection["from_state_index"],
                    }
                ),
                _anchor_transition_key(
                    {
                        "storyline_id": connection["to_storyline_id"],
                        "state_index": connection["to_state_index"],
                    }
                ),
            )
    for obligation in storyline["story_obligation_register"]:
        # ``not_before`` allows equality at the anchor and therefore is not a
        # strict precedence edge.  Treating it as one invents order and can
        # create a false cycle in otherwise valid simultaneous milestones.
        if obligation["kind"] not in {"causes", "strict_before"}:
            continue
        target = _anchor_transition_key(obligation["consequent_anchor"])
        for ordinal, anchor in enumerate(obligation["antecedent_anchors"]):
            add(
                f"{obligation['id']}#{ordinal}",
                _anchor_transition_key(anchor),
                target,
            )
    adjacency = {key: set() for key in transitions}
    for source, target in edges.values():
        adjacency[source].add(target)
    return transitions, edges, adjacency


def _s1_reachable(
    source: str, target: str, adjacency: Mapping[str, set[str]]
) -> bool:
    pending = [source]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(adjacency.get(current, set()) - visited)
    return False


def _validate_s1_precedence_path(
    *,
    source: str,
    target: str,
    edge_ids: Sequence[str],
    edges: Mapping[str, tuple[str, str]],
) -> None:
    """Require a continuous, exact source-to-target S1 edge path."""
    if not edge_ids:
        _fail("E1_CROSS_LINE_PRECEDENCE_PATH_MISSING", f"{source}->{target}")
    current = source
    seen: set[str] = set()
    for edge_id in edge_ids:
        if edge_id in seen or edge_id not in edges:
            _fail("E1_CROSS_LINE_PRECEDENCE_EDGE_INVALID", edge_id)
        seen.add(edge_id)
        left, right = edges[edge_id]
        if left != current:
            _fail("E1_CROSS_LINE_PRECEDENCE_PATH_BROKEN", edge_id)
        current = right
    if current != target:
        _fail("E1_CROSS_LINE_PRECEDENCE_PATH_BROKEN", f"{source}->{target}")


def _validate_acyclic_graph(
    graph: Mapping[str, set[str]], *, label: str
) -> None:
    indegree = {node: 0 for node in graph}
    for targets in graph.values():
        for target in targets:
            if target not in indegree:
                _fail("E1_CAPABILITY_GRAPH_DANGLING", target)
            indegree[target] += 1
    pending = [node for node, degree in indegree.items() if degree == 0]
    visited = 0
    while pending:
        node = pending.pop()
        visited += 1
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                pending.append(target)
    if visited != len(graph):
        _fail("E1_CAPABILITY_GRAPH_CYCLE", label)


def _v24_transition_universe(
    storyline: Mapping[str, Any],
) -> list[dict[str, Any]]:
    universe: list[dict[str, Any]] = []
    for line in sorted(storyline["storylines"], key=lambda item: item["id"]):
        states = _storyline_states(line)
        for index, (left, right) in enumerate(zip(states, states[1:])):
            universe.append(
                {
                    "storyline_id": line["id"],
                    "from_state_index": index,
                    "to_state_index": index + 1,
                    "from_state_sha256": rt.canonical_sha256(left),
                    "to_state_sha256": rt.canonical_sha256(right),
                }
            )
    return universe


def _v24_milestone_universe(
    storyline: Mapping[str, Any],
) -> list[dict[str, Any]]:
    values = []
    for item in storyline["temporal_architecture"]["milestones"]:
        values.append(
            {
                "id": item["id"],
                "order": item["order"],
                "phase_id": item["phase_id"],
                "storyline_ids": sorted(item["storyline_ids"]),
                "state_refs": sorted(
                    copy.deepcopy(item["state_refs"]),
                    key=lambda value: (
                        value["storyline_id"], value["state_index"]
                    ),
                ),
                "connection_ids": sorted(item["connection_ids"]),
            }
        )
    return sorted(values, key=lambda item: (item["order"], item["id"]))


def _v24_source_artifact(model: Mapping[str, Any]) -> dict[str, str]:
    matches = [
        item
        for item in model["source_artifacts"]
        if item.get("path") == "sources/S1/storyline-architecture.json"
    ]
    if len(matches) != 1:
        _fail("E1_UNIVERSE_SOURCE_INVALID", "sealed S1 canonical source missing")
    return {"stage": "S1", **copy.deepcopy(matches[0])}


def _v24_stage_source_artifact(
    model: Mapping[str, Any], *, stage: str, canonical_name: str
) -> dict[str, str]:
    expected_path = f"sources/{stage}/{canonical_name}"
    matches = [
        item for item in model["source_artifacts"] if item.get("path") == expected_path
    ]
    if len(matches) != 1:
        _fail("E1_CAPABILITY_SOURCE_ARTIFACT_INVALID", expected_path)
    return {"stage": stage, **copy.deepcopy(matches[0])}


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        _fail("E1_CAPABILITY_SOURCE_POINTER_INVALID", str(pointer))
    current = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            _fail("E1_CAPABILITY_SOURCE_POINTER_INVALID", pointer)
    return current


def _v24_expected_universe_digests(
    model: Mapping[str, Any], storyline: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    source = _v24_source_artifact(model)
    definitions = {
        "story_transition_universe_digest": (
            "/storylines",
            _v24_transition_universe(storyline),
        ),
        "milestone_universe_digest": (
            "/temporal_architecture/milestones",
            _v24_milestone_universe(storyline),
        ),
        "connection_universe_digest": (
            "/connections",
            sorted(copy.deepcopy(storyline["connections"]), key=lambda item: item["id"]),
        ),
        "obligation_universe_digest": (
            "/story_obligation_register",
            sorted(
                copy.deepcopy(storyline["story_obligation_register"]),
                key=lambda item: item["id"],
            ),
        ),
    }
    return {
        name: {
            "algorithm": "v2-canonical-json-sha256",
            "source_artifact": source,
            "source_pointer": pointer,
            "item_count": len(items),
            "canonical_items_sha256": rt.canonical_sha256(items),
        }
        for name, (pointer, items) in definitions.items()
    }


def _v24_initial_option_ids(
    *, storyline_id: str, descriptor: Mapping[str, Any], source_ids: Sequence[str]
) -> tuple[str, str, str]:
    descriptor_sha = rt.canonical_sha256(descriptor)
    option_id = "IAO-" + rt.canonical_sha256(
        [storyline_id, 0, descriptor_sha]
    )[:20]
    demand_id = "ICD-" + rt.canonical_sha256(
        [storyline_id, 0, descriptor["support_kind"], sorted(source_ids)]
    )[:20]
    claim_id = "CLAIM-E1-IA-" + rt.canonical_sha256(
        [option_id, demand_id, descriptor_sha]
    )[:20]
    return option_id, demand_id, claim_id


def _v24_index(
    values: Sequence[Mapping[str, Any]], *, label: str, key: str = "id"
) -> dict[str, Mapping[str, Any]]:
    indexed = {item[key]: item for item in values}
    if len(indexed) != len(values):
        _fail("E1_V24_ID_DUPLICATE", label)
    return indexed


def _v24_initial_realization_step_ids(
    realizations: Sequence[Mapping[str, Any]], *, storyline_id: str
) -> set[str]:
    """Project every realized initial-anchor option for one storyline.

    A storyline may have several valid state-zero support options.  Endpoint
    readiness therefore consumes their union; array order must not select a
    single (last) option.
    """
    return {
        step_id
        for realization in realizations
        if realization["storyline_id"] == storyline_id
        for step_id in realization["capability_step_ids"]
    }


def _v24_obligation_occurrence_binding_id(
    *, obligation_id: str, occurrence_id: str, step_id: str, support_id: str
) -> str:
    return "OOB-" + rt.canonical_sha256(
        [obligation_id, occurrence_id, step_id, support_id]
    )[:20]


def _v24_action_triple(
    step: Mapping[str, Any],
) -> tuple[str, str, str]:
    return (step["environment_id"], step["affordance_id"], step["action"])


def _v24_scope_triples(scope: Mapping[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (item["environment_id"], item["affordance_id"], item["action"])
        for item in scope["action_bindings"]
    }


def _v24_step_affordance_lines(
    step_id: str,
    *,
    steps: Mapping[str, Mapping[str, Any]],
    affordances: Mapping[str, Mapping[str, Any]],
    event_requirement_line: Mapping[str, str],
) -> set[str]:
    step = steps.get(step_id)
    affordance = affordances.get(step["affordance_id"]) if step else None
    if affordance is None:
        return set()
    return {
        event_requirement_line[requirement_id]
        for requirement_id in affordance["event_requirement_ids"]
        if requirement_id in event_requirement_line
    }


def _v24_validate_capability_model(
    model: Mapping[str, Any],
    *,
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environments: Mapping[str, Mapping[str, Any]],
    zones: Mapping[str, Mapping[str, Any]],
    affordances: Mapping[str, Mapping[str, Any]],
    assignments: Mapping[str, Mapping[str, Any]],
    topology: Mapping[str, Mapping[str, Any]],
    event_requirement_line: Mapping[str, str],
    through_phase: int = 4,
) -> None:
    expected_digests = _v24_expected_universe_digests(model, storyline)
    for name, expected in expected_digests.items():
        if model[name] != expected:
            _fail("E1_UNIVERSE_DIGEST_MISMATCH", name)

    lines = {item["id"]: item for item in storyline["storylines"]}
    anchors = {
        item["storyline_id"]: item for item in model["initial_anchor_support"]
    }
    if len(anchors) != len(model["initial_anchor_support"]) or set(anchors) != set(lines):
        _fail("E1_INITIAL_ANCHOR_COVERAGE_MISMATCH", "state-0 anchors")
    option_records: dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    option_claims: set[str] = set()
    for line_id, anchor in anchors.items():
        line = lines[line_id]
        if (
            anchor["state_index"] != 0
            or anchor["state"] != line["start_state"]
            or anchor["state_sha256"] != rt.canonical_sha256(line["start_state"])
            or line_id not in anchor["source_ids"]
        ):
            _fail("E1_INITIAL_ANCHOR_PROJECTION_MISMATCH", line_id)
        for option in anchor["support_options"]:
            expected_ids = _v24_initial_option_ids(
                storyline_id=line_id,
                descriptor=option["capability_descriptor"],
                source_ids=option["source_ids"],
            )
            if tuple(
                option[name]
                for name in (
                    "support_option_id",
                    "capability_demand_id",
                    "semantic_review_claim_id",
                )
            ) != expected_ids:
                _fail("E1_INITIAL_OPTION_ID_INVALID", line_id)
            option_id = option["support_option_id"]
            if option_id in option_records or option["semantic_review_claim_id"] in option_claims:
                _fail("E1_INITIAL_OPTION_DUPLICATE", option_id)
            if not set(option["capability_descriptor"]["environment_ids"]).issubset(environments):
                _fail("E1_INITIAL_OPTION_ENVIRONMENT_DANGLING", option_id)
            option_records[option_id] = (anchor, option)
            option_claims.add(option["semantic_review_claim_id"])

    facts = _v24_index(model["capability_fact_registry"], label="facts")
    steps = _v24_index(model["capability_step_registry"], label="steps")
    actors = _v24_index(model["actor_authority_bindings"], label="actor bindings")
    ambient = _v24_index(model["ambient_context_hosts"], label="ambient hosts")
    occurrences = _v24_index(
        model["capability_occurrence_requirements"], label="occurrences"
    )
    transition_universe, precedence_edges, precedence_adjacency = (
        _s1_structural_precedence(storyline)
    )

    world_entities = {
        item["id"]
        for field in (
            "world_facts", "history_pressures", "institutions", "systems",
            "resource_flows", "authority_flows", "information_flows",
            "rule_conflict_matrix", "storyline_support_ledger",
        )
        for item in world[field]
    }
    world_entity_values = {
        item["id"]: item
        for field in (
            "world_facts", "history_pressures", "institutions", "systems",
            "resource_flows", "authority_flows", "information_flows",
            "rule_conflict_matrix", "storyline_support_ledger",
        )
        for item in world[field]
    }
    for binding in actors.values():
        if (
            binding["environment_id"] not in environments
            or binding["e1_access_assignment_id"] not in assignments
            or assignments[binding["e1_access_assignment_id"]]["subject_id"]
            not in {binding["environment_id"], *environments[binding["environment_id"]]["zone_ids"]}
            or not set(binding["world_authority_source_ids"]).issubset(world_entities)
            or not set(binding["permitted_actions"]).issubset(
                environments[binding["environment_id"]]["allowed_actions"]
            )
            or not set(binding["requires_token_fact_ids"]).issubset(facts)
            or not set(binding["produces_token_fact_ids"]).issubset(facts)
            or any(
                facts[item]["kind"] != "authority_token"
                for item in [
                    *binding["requires_token_fact_ids"],
                    *binding["produces_token_fact_ids"],
                ]
            )
        ):
            _fail("E1_ACTOR_AUTHORITY_INVALID", binding["id"])

    for fact in facts.values():
        if fact["statement_sha256"] != rt.canonical_sha256(fact["statement"]):
            _fail("E1_CAPABILITY_FACT_HASH_MISMATCH", fact["id"])
        anchor = fact["source_anchor"]
        source_kind = anchor["source_kind"]
        if source_kind == "s1_story_state":
            line = lines.get(anchor["storyline_id"])
            if line is None:
                _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])
            states = _storyline_states(line)
            index = anchor["state_index"]
            expected_artifact = _v24_stage_source_artifact(
                model,
                stage="S1",
                canonical_name="storyline-architecture.json",
            )
            value = _resolve_json_pointer(storyline, anchor["source_pointer"])
            line_index = next(
                index
                for index, item in enumerate(storyline["storylines"])
                if item["id"] == anchor["storyline_id"]
            )
            expected_pointer = (
                f"/storylines/{line_index}/start_state"
                if index == 0
                else f"/storylines/{line_index}/end_state"
                if index == len(states) - 1
                else f"/storylines/{line_index}/state_changes/{index - 1}"
            )
            if (
                anchor["source_artifact"] != expected_artifact
                or anchor["source_pointer"] != expected_pointer
                or index >= len(states)
                or value != states[index]
                or anchor["value_sha256"] != rt.canonical_sha256(value)
                or anchor["state_sha256"] != rt.canonical_sha256(states[index])
            ):
                _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])
            if index == 0:
                if fact["root_policy"] not in {
                    "root_allowed",
                    "producer_required",
                }:
                    _fail("E1_CAPABILITY_FACT_ROOT_INVALID", fact["id"])
            elif (
                fact["root_policy"] != "t1_predecessor_required"
                or set(fact["producer_transition_keys"])
                != {_transition_key(anchor["storyline_id"], index - 1)}
            ):
                _fail("E1_CAPABILITY_FACT_ROOT_INVALID", fact["id"])
        elif source_kind == "w1_system_output":
            expected_artifact = _v24_stage_source_artifact(
                model, stage="W1", canonical_name="world-model.json"
            )
            value = _resolve_json_pointer(world, anchor["source_pointer"])
            cited = world_entity_values.get(anchor["system_or_flow_id"])
            source_prefix = next(
                (
                    f"/{field}/{index}"
                    for field in (
                        "world_facts", "history_pressures", "institutions", "systems",
                        "resource_flows", "authority_flows", "information_flows",
                        "rule_conflict_matrix", "storyline_support_ledger",
                    )
                    for index, item in enumerate(world[field])
                    if item["id"] == anchor["system_or_flow_id"]
                ),
                None,
            )
            pointer_tokens = anchor["source_pointer"].split("/")
            if (
                anchor["source_artifact"] != expected_artifact
                or cited is None
                or source_prefix is None
                or not anchor["source_pointer"].startswith(source_prefix + "/")
                or not pointer_tokens[-1].isdigit()
                or int(pointer_tokens[-1]) != anchor["output_index"]
                or anchor["value_sha256"] != rt.canonical_sha256(value)
                or anchor["output_index"] < 0
            ):
                _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])
        elif source_kind == "e1_initial_state":
            # The sealed phase-2 pointer is the authority for an E1-local
            # initial value.  Its exact environment/resource/authority
            # projection is replayed once phase evidence is available.
            if anchor["environment_id"] not in environments:
                _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])
        else:
            _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])
        if not set(fact["producer_step_ids"]).issubset(steps) or not set(
            fact["consumer_step_ids"]
        ).issubset(steps):
            _fail("E1_CAPABILITY_FACT_STEP_DANGLING", fact["id"])
        semantics = fact["producer_semantics"]
        producers = fact["producer_step_ids"]
        if semantics == "none" and producers:
            _fail("E1_CAPABILITY_PRODUCER_SEMANTICS_INVALID", fact["id"])
        if semantics in {"all_of", "any_of", "exactly_one"} and not producers:
            _fail("E1_CAPABILITY_PRODUCER_SEMANTICS_INVALID", fact["id"])
        if fact["root_policy"] == "producer_required" and not producers:
            _fail("E1_CAPABILITY_PRODUCER_MISSING", fact["id"])
        if fact["kind"] == "authority_token":
            for scope_name in ("issuer_scope", "consumer_scope"):
                scope = fact[scope_name]
                for triple in _v24_scope_triples(scope):
                    env_id, affordance_id, action = triple
                    affordance = affordances.get(affordance_id)
                    if (
                        affordance is None
                        or affordance["environment_id"] != env_id
                        or action not in affordance["allowed_actions"]
                        or action not in environments[env_id]["allowed_actions"]
                    ):
                        _fail("E1_AUTHORITY_SCOPE_ACTION_INVALID", fact["id"])

    graph: dict[str, set[str]] = {
        **{f"F:{item}": set() for item in facts},
        **{f"S:{item}": set() for item in steps},
    }
    for step in steps.values():
        environment = environments.get(step["environment_id"])
        affordance = affordances.get(step["affordance_id"])
        zone = zones.get(step["zone_id"])
        if (
            environment is None
            or affordance is None
            or affordance["environment_id"] != step["environment_id"]
            or zone is None
            or zone["environment_id"] != step["environment_id"]
            or step["action"] not in affordance["allowed_actions"]
            or step["action"] not in environment["allowed_actions"]
            or not set(step["actor_authority_binding_ids"]).issubset(actors)
            or not set(step["requires_fact_ids"]).issubset(facts)
            or not set(step["produces_fact_ids"]).issubset(facts)
        ):
            _fail("E1_CAPABILITY_STEP_INVALID", step["id"])
        step_bindings = [actors[item] for item in step["actor_authority_binding_ids"]]
        if not set(step["actor_slot_ids"]).issubset(
            {item["actor_slot_id"] for item in step_bindings}
        ) or any(
            item["environment_id"] != step["environment_id"]
            or step["action"] not in item["permitted_actions"]
            for item in step_bindings
        ):
            _fail("E1_CAPABILITY_STEP_AUTHORITY_INVALID", step["id"])
        required_token_kinds = {
            facts[item]["token_kind"]
            for item in step["requires_fact_ids"]
            if facts[item]["kind"] == "authority_token"
        }
        produced_token_kinds = {
            facts[item]["token_kind"]
            for item in step["produces_fact_ids"]
            if facts[item]["kind"] == "authority_token"
        }
        forbidden_token_kinds = {
            token
            for item in step_bindings
            for token in item["forbidden_token_kinds"]
        }
        if (
            set(step["requires_token_kinds"]) != required_token_kinds
            or set(step["produces_token_kinds"]) != produced_token_kinds
            or set(step["forbidden_token_kinds"]) != forbidden_token_kinds
            or produced_token_kinds & forbidden_token_kinds
        ):
            _fail("E1_AUTHORITY_TOKEN_PROJECTION_MISMATCH", step["id"])
        triple = _v24_action_triple(step)
        for fact_id in step["requires_fact_ids"]:
            fact = facts[fact_id]
            if fact["kind"] != "authority_token":
                continue
            scope = fact["consumer_scope"]
            if (
                triple not in _v24_scope_triples(scope)
                or not set(step["actor_slot_ids"]).issubset(
                    scope["actor_slot_ids"]
                )
                or (
                    scope.get("capability_step_ids")
                    and step["id"] not in scope["capability_step_ids"]
                )
            ):
                _fail("E1_AUTHORITY_TOKEN_CONSUMER_SCOPE_INVALID", fact_id)
        for fact_id in step["produces_fact_ids"]:
            fact = facts[fact_id]
            if fact["kind"] != "authority_token":
                continue
            scope = fact["issuer_scope"]
            if (
                triple not in _v24_scope_triples(scope)
                or not set(step["actor_slot_ids"]).issubset(
                    scope["actor_slot_ids"]
                )
                or (
                    scope.get("capability_step_ids")
                    and step["id"] not in scope["capability_step_ids"]
                )
            ):
                _fail("E1_AUTHORITY_TOKEN_ISSUER_SCOPE_INVALID", fact_id)
        for fact_id in step["requires_fact_ids"]:
            graph[f"F:{fact_id}"].add(f"S:{step['id']}")
        for fact_id in step["produces_fact_ids"]:
            graph[f"S:{step['id']}"].add(f"F:{fact_id}")

    for fact in facts.values():
        expected_producers = {
            step["id"] for step in steps.values() if fact["id"] in step["produces_fact_ids"]
        }
        expected_consumers = {
            step["id"] for step in steps.values() if fact["id"] in step["requires_fact_ids"]
        }
        if set(fact["producer_step_ids"]) != expected_producers or set(
            fact["consumer_step_ids"]
        ) != expected_consumers:
            _fail("E1_CAPABILITY_FACT_STEP_INVERSE_MISMATCH", fact["id"])
    for binding in actors.values():
        linked_steps = [
            step
            for step in steps.values()
            if binding["id"] in step["actor_authority_binding_ids"]
        ]
        expected_required = {
            fact_id
            for step in linked_steps
            for fact_id in step["requires_fact_ids"]
            if facts[fact_id]["kind"] == "authority_token"
        }
        expected_produced = {
            fact_id
            for step in linked_steps
            for fact_id in step["produces_fact_ids"]
            if facts[fact_id]["kind"] == "authority_token"
        }
        if (
            set(binding["requires_token_fact_ids"]) != expected_required
            or set(binding["produces_token_fact_ids"]) != expected_produced
        ):
            _fail("E1_ACTOR_TOKEN_FACT_PROJECTION_MISMATCH", binding["id"])

    _validate_acyclic_graph(graph, label="fact-step graph")

    for host in ambient.values():
        if (
            host["environment_id"] not in environments
            or host["zone_id"] not in zones
            or zones[host["zone_id"]]["environment_id"] != host["environment_id"]
            or host["storyline_id"] not in lines
            or not set(host["support_basis_fact_ids"]).issubset(facts)
            or host["storyline_id"] not in environments[host["environment_id"]]["storyline_stage_ids"]
        ):
            _fail("E1_AMBIENT_CONTEXT_INVALID", host["id"])

    for occurrence in occurrences.values():
        if occurrence["step_id"] not in steps:
            _fail("E1_OCCURRENCE_STEP_DANGLING", occurrence["id"])
        maximum = occurrence["maximum_occurrences"]
        if maximum is not None and maximum < occurrence["minimum_occurrences"]:
            _fail("E1_OCCURRENCE_CARDINALITY_INVALID", occurrence["id"])
        if occurrence["share_policy"] == "exclusive" and occurrence["allowed_shared_requirement_ids"]:
            _fail("E1_OCCURRENCE_SHARE_INVALID", occurrence["id"])
        if not set(occurrence["allowed_shared_requirement_ids"]).issubset(occurrences):
            _fail("E1_OCCURRENCE_SHARE_DANGLING", occurrence["id"])
        if (
            occurrence["share_policy"] == "allow_list"
            and not occurrence["allowed_shared_requirement_ids"]
        ) or (
            occurrence["share_policy"] == "shareable"
            and occurrence["allowed_shared_requirement_ids"]
        ):
            _fail("E1_OCCURRENCE_SHARE_INVALID", occurrence["id"])
    for occurrence in occurrences.values():
        if occurrence["share_policy"] != "allow_list":
            continue
        for peer_id in occurrence["allowed_shared_requirement_ids"]:
            peer = occurrences[peer_id]
            if (
                peer["share_policy"] != "allow_list"
                or occurrence["id"] not in peer["allowed_shared_requirement_ids"]
            ):
                _fail("E1_OCCURRENCE_SHARE_ASYMMETRIC", occurrence["id"])

    # P3 owns the complete capability graph.  Its writer must validate that
    # graph before evidence is sealed, while the P4 readiness ledgers do not
    # exist yet.  P4/public validation continue below and re-run the same graph
    # checks before validating every readiness universe.
    if through_phase < 4:
        return

    transition_records = {
        _transition_key(item["storyline_id"], item["from_state_index"]): item
        for item in model["story_transition_support"]
    }
    expected_transitions = {
        _transition_key(item["storyline_id"], item["from_state_index"]): item
        for item in _v24_transition_universe(storyline)
    }
    if len(transition_records) != len(model["story_transition_support"]) or set(
        transition_records
    ) != set(expected_transitions):
        _fail("E1_STORY_TRANSITION_COVERAGE_MISMATCH", "transition universe")
    event_requirements = {item["id"]: item for item in storyline["event_requirements"]}

    def step_affordance_lines(step_id: str) -> set[str]:
        return _v24_step_affordance_lines(
            step_id,
            steps=steps,
            affordances=affordances,
            event_requirement_line=event_requirement_line,
        )

    for key, record in transition_records.items():
        expected = expected_transitions[key]
        line = lines[record["storyline_id"]]
        states = _storyline_states(line)
        if (
            record["to_state_index"] != record["from_state_index"] + 1
            or record["from_state"] != states[record["from_state_index"]]
            or record["to_state"] != states[record["to_state_index"]]
            or not set(record["event_requirement_ids"]).issubset(event_requirements)
            or any(
                event_requirement_line[item] != record["storyline_id"]
                for item in record["event_requirement_ids"]
            )
            or not set(record["required_fact_ids"]).issubset(facts)
            or not set(record["occurrence_requirement_ids"]).issubset(occurrences)
            or not set(record["ambient_context_host_ids"]).issubset(ambient)
        ):
            _fail("E1_STORY_TRANSITION_SUPPORT_INVALID", key)
        modes = []
        for claim in record["support_claims"]:
            step = steps.get(claim["step_id"])
            if step is None or claim["support_mode"] not in step["supported_modes"]:
                _fail("E1_SUPPORT_MODE_INVALID", key)
            if record["storyline_id"] not in environments[step["environment_id"]]["storyline_stage_ids"]:
                _fail("E1_SUPPORT_LINE_MISMATCH", key)
            if record["storyline_id"] not in step_affordance_lines(claim["step_id"]):
                _fail(
                    "E1_TRANSITION_STEP_AFFORDANCE_LINE_MISMATCH",
                    f"{record['id']}/{claim['step_id']}",
                )
            modes.append(claim["support_mode"])
        if not set(modes) & {"enact", "observe", "communicate"}:
            if not record["ambient_context_host_ids"]:
                _fail("E1_CONSTRAIN_ONLY_UNSUPPORTED", key)
            if any(
                ambient[item]["storyline_id"] != record["storyline_id"]
                for item in record["ambient_context_host_ids"]
            ):
                _fail("E1_AMBIENT_CONTEXT_INVALID", key)

    transition_step_ids = {
        key: {claim["step_id"] for claim in record["support_claims"]}
        for key, record in transition_records.items()
    }
    for key, record in transition_records.items():
        projected_required_facts = {
            fact_id
            for step_id in transition_step_ids[key]
            for fact_id in steps[step_id]["requires_fact_ids"]
        }
        if set(record["required_fact_ids"]) != projected_required_facts:
            _fail("E1_TRANSITION_REQUIRED_FACT_PROJECTION_MISMATCH", key)

    projected_producer_transitions = {fact_id: set() for fact_id in facts}
    for key, step_ids in transition_step_ids.items():
        for step_id in step_ids:
            for fact_id in steps[step_id]["produces_fact_ids"]:
                projected_producer_transitions[fact_id].add(key)

    transition_graph: dict[str, set[str]] = {
        node: set(targets) for node, targets in graph.items()
    }
    transition_graph.update({f"T:{key}": set() for key in transition_universe})
    for source, target in precedence_edges.values():
        transition_graph[f"T:{source}"].add(f"T:{target}")
    for fact in facts.values():
        expected_producers = projected_producer_transitions[fact["id"]]
        if set(fact["producer_transition_keys"]) != expected_producers:
            _fail("E1_CAPABILITY_FACT_TRANSITION_PROJECTION_MISMATCH", fact["id"])
        for transition_key in expected_producers:
            transition_graph[f"T:{transition_key}"].add(f"F:{fact['id']}")
        consuming_transitions = {
            key
            for key, record in transition_records.items()
            if fact["id"] in record["required_fact_ids"]
        }
        for transition_key in consuming_transitions:
            transition_graph[f"F:{fact['id']}"].add(f"T:{transition_key}")

        dependency = fact["cross_line_dependency"]
        if dependency is None:
            continue
        source_key = dependency["source_transition_key"]
        consumer_key = dependency["consumer_transition_key"]
        if (
            source_key not in expected_producers
            or consumer_key not in consuming_transitions
            or source_key not in transition_universe
            or consumer_key not in transition_universe
            or source_key.split(":", 1)[0] == consumer_key.split(":", 1)[0]
        ):
            _fail("E1_CROSS_LINE_DEPENDENCY_INVALID", fact["id"])
        source_before_target = _s1_reachable(
            source_key, consumer_key, precedence_adjacency
        )
        target_before_source = _s1_reachable(
            consumer_key, source_key, precedence_adjacency
        )
        if target_before_source:
            _fail("E1_CROSS_LINE_FUTURE_DEPENDENCY", fact["id"])
        if dependency["precedence_status"] == "structurally_precedes":
            if not source_before_target:
                _fail("E1_CROSS_LINE_PRECEDENCE_UNPROVEN", fact["id"])
            _validate_s1_precedence_path(
                source=source_key,
                target=consumer_key,
                edge_ids=dependency["s1_precedence_edge_ids"],
                edges=precedence_edges,
            )
        elif (
            source_before_target
            or target_before_source
            or dependency["s1_precedence_edge_ids"]
        ):
            _fail("E1_CROSS_LINE_INCOMPARABLE_INVALID", fact["id"])
    _validate_acyclic_graph(
        transition_graph, label="transition-fact-step graph"
    )

    connection_records = _v24_index(
        model["connection_path_readiness"], label="connection readiness", key="connection_id"
    )
    def exact_anchor_step_ids(storyline_id: str, state_index: int) -> set[str]:
        if state_index == 0:
            return _v24_initial_realization_step_ids(
                model["initial_anchor_option_realization_ledger"],
                storyline_id=storyline_id,
            )
        transition = transition_records.get(
            _transition_key(storyline_id, state_index - 1)
        )
        return (
            {item["step_id"] for item in transition["support_claims"]}
            if transition is not None
            else set()
        )
    source_connections = {item["id"]: item for item in storyline["connections"]}
    if set(connection_records) != set(source_connections):
        _fail("E1_CONNECTION_READINESS_COVERAGE_MISMATCH", "connections")
    for connection_id, record in connection_records.items():
        source = source_connections[connection_id]
        source_steps = [steps[item] for item in record["source_endpoint_step_ids"] if item in steps]
        target_steps = [steps[item] for item in record["target_endpoint_step_ids"] if item in steps]
        if (
            record["relation"] != source["relation"]
            or not set(record["source_endpoint_step_ids"]).issubset(steps)
            or not set(record["target_endpoint_step_ids"]).issubset(steps)
            or not set(record["transport_step_ids"]).issubset(steps)
            or not set(record["topology_path_ids"]).issubset(topology)
            or not set(record["occurrence_requirement_ids"]).issubset(occurrences)
        ):
            _fail("E1_CONNECTION_READINESS_INVALID", connection_id)
        if (
            any(
                source["from_storyline_id"]
                not in environments[item["environment_id"]]["storyline_stage_ids"]
                for item in source_steps
            )
            or any(
                source["to_storyline_id"]
                not in environments[item["environment_id"]]["storyline_stage_ids"]
                for item in target_steps
            )
        ):
            _fail("E1_CONNECTION_ENDPOINT_LINE_MISMATCH", connection_id)
        if any(
            source["from_storyline_id"] not in step_affordance_lines(item["id"])
            for item in source_steps
        ) or any(
            source["to_storyline_id"] not in step_affordance_lines(item["id"])
            for item in target_steps
        ) or any(
            not (
                {
                    source["from_storyline_id"],
                    source["to_storyline_id"],
                }
                & step_affordance_lines(step_id)
            )
            for step_id in record["transport_step_ids"]
        ):
            _fail(
                "E1_CONNECTION_STEP_AFFORDANCE_LINE_MISMATCH",
                connection_id,
            )
        exact_source_steps = exact_anchor_step_ids(
            source["from_storyline_id"], source["from_state_index"]
        )
        exact_target_steps = exact_anchor_step_ids(
            source["to_storyline_id"], source["to_state_index"]
        )
        if (
            not record["source_endpoint_step_ids"]
            or not record["target_endpoint_step_ids"]
            or not set(record["source_endpoint_step_ids"]).issubset(
                exact_source_steps
            )
            or not set(record["target_endpoint_step_ids"]).issubset(
                exact_target_steps
            )
        ):
            _fail("E1_CONNECTION_ENDPOINT_ANCHOR_MISMATCH", connection_id)
        if source["relation"] == "associative":
            if record["transfer_fact_id"] is not None or record["transport_step_ids"] or record["topology_path_ids"]:
                _fail("E1_ASSOCIATIVE_CONNECTION_CAUSALIZED", connection_id)
        else:
            transfer_fact_id = record["transfer_fact_id"]
            if transfer_fact_id not in facts:
                _fail("E1_CONNECTION_TRANSFER_FACT_MISSING", connection_id)
            producers = set(facts[transfer_fact_id]["producer_step_ids"])
            consumers = set(facts[transfer_fact_id]["consumer_step_ids"])
            if (
                not producers
                & (set(record["source_endpoint_step_ids"]) | set(record["transport_step_ids"]))
                or not consumers & set(record["target_endpoint_step_ids"])
            ):
                _fail("E1_CONNECTION_TRANSFER_FACT_PATH_INVALID", connection_id)
            # A causal transfer cannot be injected into a generic target-line
            # step that is also claimed to support transitions before the
            # connection's target anchor.  That would silently make those
            # earlier events depend on the source line and can create a T1
            # event-DAG cycle.  Reuse at/after the target anchor remains
            # available when the structured S1 order and semantic review
            # support it; E1 does not require artificial step uniqueness.
            target_endpoint_ids = set(record["target_endpoint_step_ids"])
            if any(
                claim["step_id"] in target_endpoint_ids
                and transition["storyline_id"] == source["to_storyline_id"]
                and transition["to_state_index"] < source["to_state_index"]
                for transition in transition_records.values()
                for claim in transition["support_claims"]
            ):
                _fail(
                    "E1_CONNECTION_TARGET_ENDPOINT_PREANCHOR_REUSE",
                    connection_id,
                )
            source_environment_id = source_steps[0]["environment_id"]
            target_environment_id = target_steps[0]["environment_id"]
            _validate_topology_path(
                record["topology_path_ids"],
                source_environment_id=source_environment_id,
                target_environment_id=target_environment_id,
                transport_capability=(
                    "local"
                    if source_environment_id == target_environment_id
                    else "story-causality-transfer"
                ),
                topology=topology,
                transition_id=connection_id,
            )

    milestone_records = _v24_index(
        model["milestone_capability_readiness"], label="milestones", key="milestone_id"
    )
    source_milestones = {
        item["id"]: item for item in storyline["temporal_architecture"]["milestones"]
    }
    if set(milestone_records) != set(source_milestones):
        _fail("E1_MILESTONE_READINESS_COVERAGE_MISMATCH", "milestones")
    for milestone_id, record in milestone_records.items():
        source = source_milestones[milestone_id]
        if any(
            record[name] != source[name]
            for name in ("order", "phase_id", "storyline_ids", "state_refs", "connection_ids")
        ) or not set(record["transition_support_ids"]).issubset(
            {item["id"] for item in transition_records.values()}
        ) or not set(record["initial_support_option_ids"]).issubset(option_records) or not set(
            record["connection_readiness_ids"]
        ).issubset(connection_records) or not set(record["occurrence_requirement_ids"]).issubset(occurrences):
            _fail("E1_MILESTONE_READINESS_INVALID", milestone_id)
        expected_transition_support: set[str] = set()
        expected_initial_lines: set[str] = set()
        for state_ref in source["state_refs"]:
            if state_ref["state_index"] == 0:
                expected_initial_lines.add(state_ref["storyline_id"])
            else:
                transition = transition_records.get(
                    _transition_key(
                        state_ref["storyline_id"], state_ref["state_index"] - 1
                    )
                )
                if transition is None:
                    _fail("E1_MILESTONE_READINESS_INVALID", milestone_id)
                expected_transition_support.add(transition["id"])
        observed_initial_lines = {
            option_records[item][0]["storyline_id"]
            for item in record["initial_support_option_ids"]
        }
        if (
            set(record["transition_support_ids"])
            != expected_transition_support
            or observed_initial_lines != expected_initial_lines
            or set(record["connection_readiness_ids"])
            != set(source["connection_ids"])
        ):
            _fail("E1_MILESTONE_READINESS_INCOMPLETE", milestone_id)

    obligation_records = _v24_index(
        model["obligation_capability_readiness"], label="obligations", key="obligation_id"
    )
    source_obligations = {
        item["id"]: item for item in storyline["story_obligation_register"]
    }
    if set(obligation_records) != set(source_obligations):
        _fail("E1_OBLIGATION_READINESS_COVERAGE_MISMATCH", "obligations")
    obligation_occurrence_bindings = _v24_index(
        model["obligation_occurrence_bindings"],
        label="obligation occurrence bindings",
    )
    occurrence_binding_owner: dict[str, str] = {}
    bindings_by_obligation: dict[str, list[Mapping[str, Any]]] = {}
    for binding_id, binding in obligation_occurrence_bindings.items():
        expected_id = _v24_obligation_occurrence_binding_id(
            obligation_id=binding["obligation_id"],
            occurrence_id=binding["occurrence_requirement_id"],
            step_id=binding["step_id"],
            support_id=binding["support_id"],
        )
        if binding_id != expected_id:
            _fail("E1_OBLIGATION_OCCURRENCE_BINDING_ID_MISMATCH", binding_id)
        if binding["obligation_id"] not in source_obligations:
            _fail("E1_OBLIGATION_OCCURRENCE_BINDING_INVALID", binding_id)
        occurrence = occurrences.get(binding["occurrence_requirement_id"])
        if occurrence is None or occurrence["step_id"] != binding["step_id"]:
            _fail("E1_OBLIGATION_OCCURRENCE_BINDING_INVALID", binding_id)
        if binding["occurrence_requirement_id"] in occurrence_binding_owner:
            _fail(
                "E1_OBLIGATION_OCCURRENCE_BINDING_DUPLICATE",
                binding["occurrence_requirement_id"],
            )
        occurrence_binding_owner[binding["occurrence_requirement_id"]] = binding_id
        bindings_by_obligation.setdefault(binding["obligation_id"], []).append(
            binding
        )
    support_ids = {item["id"] for item in transition_records.values()} | set(connection_records) | set(option_records)
    support_lines = {
        **{
            item["id"]: {item["storyline_id"]}
            for item in transition_records.values()
        },
        **{
            connection_id: {
                source_connections[connection_id]["from_storyline_id"],
                source_connections[connection_id]["to_storyline_id"],
            }
            for connection_id in connection_records
        },
        **{
            option_id: {anchor["storyline_id"]}
            for option_id, (anchor, _option) in option_records.items()
        },
    }
    def anchor_support_candidates(anchor: Mapping[str, Any]) -> set[str]:
        if anchor["state_index"] == 0:
            return {
                option_id
                for option_id, (initial, _option) in option_records.items()
                if initial["storyline_id"] == anchor["storyline_id"]
            }
        transition = transition_records.get(
            _transition_key(anchor["storyline_id"], anchor["state_index"] - 1)
        )
        return {transition["id"]} if transition is not None else set()
    for obligation_id, record in obligation_records.items():
        if (
            record["kind"] != source_obligations[obligation_id]["kind"]
            or not set(record["antecedent_support_ids"]).issubset(support_ids)
            or not set(record["consequent_support_ids"]).issubset(support_ids)
            or not set(record["required_fact_ids"]).issubset(facts)
            or not set(record["required_step_ids"]).issubset(steps)
            or not set(record["occurrence_requirement_ids"]).issubset(occurrences)
            or not set(record["allowed_disclosure_fact_ids"]).issubset(facts)
            or not set(record["forbidden_disclosure_fact_ids"]).issubset(facts)
        ):
            _fail("E1_OBLIGATION_READINESS_INVALID", obligation_id)
        source = source_obligations[obligation_id]
        antecedent_candidates = [
            anchor_support_candidates(item) for item in source["antecedent_anchors"]
        ]
        consequent_candidates = anchor_support_candidates(source["consequent_anchor"])
        observed_antecedents = set(record["antecedent_support_ids"])
        observed_consequents = set(record["consequent_support_ids"])
        selected_antecedents = {
            next(iter(candidates & observed_antecedents))
            for candidates in antecedent_candidates
            if len(candidates & observed_antecedents) == 1
        }
        if (
            any(
                len(candidates & observed_antecedents) != 1
                for candidates in antecedent_candidates
            )
            or observed_antecedents != selected_antecedents
            or len(consequent_candidates & observed_consequents) != 1
            or observed_consequents != consequent_candidates & observed_consequents
        ):
            _fail("E1_OBLIGATION_READINESS_INCOMPLETE", obligation_id)
        allowed = set(record["allowed_disclosure_fact_ids"])
        forbidden = set(record["forbidden_disclosure_fact_ids"])
        if allowed & forbidden:
            _fail("E1_OBLIGATION_DISCLOSURE_CONTRADICTION", obligation_id)
        if record["readiness_mode"] == "inherited_anchor_path":
            if (
                record["required_fact_ids"]
                or record["required_step_ids"]
                or record["occurrence_requirement_ids"]
                or bindings_by_obligation.get(obligation_id)
            ):
                _fail("E1_OBLIGATION_INHERITED_PATH_HAS_EXTRAS", obligation_id)
        elif record["readiness_mode"] == "direct_path":
            required_steps = set(record["required_step_ids"])
            required_facts = set(record["required_fact_ids"])
            required_occurrences = set(record["occurrence_requirement_ids"])
            if not required_steps or not required_facts or not required_occurrences:
                _fail("E1_OBLIGATION_DIRECT_PATH_EMPTY", obligation_id)
            selected_support_ids = observed_antecedents | observed_consequents
            owned_bindings = bindings_by_obligation.get(obligation_id, [])
            projected_occurrences = {
                item["occurrence_requirement_id"] for item in owned_bindings
            }
            if (
                required_occurrences != projected_occurrences
                or any(item["step_id"] not in required_steps for item in owned_bindings)
                or any(
                    item["support_id"] not in selected_support_ids
                    for item in owned_bindings
                )
                or {item["step_id"] for item in owned_bindings} != required_steps
            ):
                _fail("E1_OBLIGATION_DIRECT_OCCURRENCE_MISMATCH", obligation_id)
            if any(
                not (
                    step_affordance_lines(item["step_id"])
                    & support_lines.get(item["support_id"], set())
                )
                for item in owned_bindings
            ):
                _fail(
                    "E1_OBLIGATION_STEP_AFFORDANCE_LINE_MISMATCH",
                    obligation_id,
                )
            projected_facts = {
                fact_id
                for step_id in required_steps
                for fact_id in (
                    *steps[step_id]["requires_fact_ids"],
                    *steps[step_id]["produces_fact_ids"],
                )
            }
            if required_facts != projected_facts:
                _fail("E1_OBLIGATION_DIRECT_FACT_MISMATCH", obligation_id)
    direct_obligation_ids = {
        obligation_id
        for obligation_id, record in obligation_records.items()
        if record["readiness_mode"] == "direct_path"
    }
    if set(bindings_by_obligation) != direct_obligation_ids:
        _fail("E1_OBLIGATION_OCCURRENCE_BINDING_COVERAGE_MISMATCH", "obligations")

    realizations = _v24_index(
        model["initial_anchor_option_realization_ledger"],
        label="initial option realizations",
        key="support_option_id",
    )
    if set(realizations) != set(option_records):
        _fail("E1_INITIAL_OPTION_REALIZATION_COVERAGE_MISMATCH", "options")
    for option_id, record in realizations.items():
        anchor, option = option_records[option_id]
        descriptor = option["capability_descriptor"]
        if (
            record["storyline_id"] != anchor["storyline_id"]
            or record["state_index"] != 0
            or record["capability_demand_id"] != option["capability_demand_id"]
            or record["descriptor_sha256"] != rt.canonical_sha256(descriptor)
            or record["semantic_review_claim_id"] != option["semantic_review_claim_id"]
            or not set(record["capability_fact_ids"]).issubset(facts)
            or not set(record["capability_step_ids"]).issubset(steps)
            or not set(record["ambient_context_host_ids"]).issubset(ambient)
            or not set(record["topology_path_ids"]).issubset(topology)
            or not set(record["realized_environment_ids"]).issubset(environments)
            or set(record["realized_environment_ids"])
            != set(descriptor["environment_ids"])
        ):
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        kind = descriptor["support_kind"]
        if kind == "static_context_host":
            roots = [
                facts[item]
                for item in record["capability_fact_ids"]
                if facts[item]["root_policy"] == "root_allowed"
            ]
            if not roots and not record["ambient_context_host_ids"]:
                _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        elif kind == "process_host":
            realized_modes = {
                mode
                for item in record["capability_step_ids"]
                for mode in steps[item]["supported_modes"]
            }
            if not record["capability_step_ids"] or not set(
                descriptor["required_modes"]
            ).issubset(realized_modes):
                _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        elif not record["capability_step_ids"]:
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        if descriptor["topology_requirement"] == "cross_environment_path" and not record[
            "topology_path_ids"
        ]:
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        if any(
            steps[item]["environment_id"] not in record["realized_environment_ids"]
            for item in record["capability_step_ids"]
        ) or any(
            ambient[item]["environment_id"] not in record["realized_environment_ids"]
            for item in record["ambient_context_host_ids"]
        ):
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        if any(
            record["storyline_id"] not in step_affordance_lines(step_id)
            for step_id in record["capability_step_ids"]
        ):
            _fail(
                "E1_INITIAL_OPTION_STEP_AFFORDANCE_LINE_MISMATCH",
                option_id,
            )
        realized_fact_kinds = {
            facts[item]["kind"] for item in record["capability_fact_ids"]
        }
        if not set(descriptor["required_fact_kinds"]).issubset(
            realized_fact_kinds
        ):
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)
        if descriptor["authority_required"] and not any(
            actors[binding_id]["environment_id"]
            in record["realized_environment_ids"]
            for step_id in record["capability_step_ids"]
            for binding_id in steps[step_id]["actor_authority_binding_ids"]
        ):
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", option_id)


def _validate_model(
    model: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
    *,
    expected_gate: Mapping[str, str] | None = None,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
) -> None:
    _boundary_check(model)
    semantic_profile = _semantic_profile(model.get("schema_version"))
    try:
        runtime.validate(model, "environment-system.schema.json")
    except Exception as error:
        _fail("E1_MODEL_SCHEMA_INVALID", str(error))
    partition = model["authority_partition"]
    _validate_authority_disjoint(partition)
    if model["run_id"] != baseline["run_id"]:
        _fail("E1_RUN_ID_MISMATCH", "model belongs to another run")
    if (
        model["storyline_environment_requirements"]
        != storyline["environment_requirements"]
    ):
        _fail(
            "E1_STORYLINE_ENVIRONMENT_PROJECTION_MISMATCH",
            "E1 must consume exact S1 environment requirements",
        )
    if model["environment_demands"] != world["environment_demands"]:
        _fail(
            "E1_DEMAND_PROJECTION_MISMATCH",
            "E1 must consume exact W1 environment demands",
        )

    demands = model["environment_demands"]
    demands_by_id = {item["id"]: item for item in demands}
    if len(demands_by_id) != len(demands):
        _fail("E1_DEMAND_DUPLICATE", "environment demand IDs repeat")
    lines = {item["id"]: item for item in storyline["storylines"]}
    storyline_environment_requirements = model[
        "storyline_environment_requirements"
    ]
    storyline_environment_requirements_by_id = {
        item["id"]: item for item in storyline_environment_requirements
    }
    if len(storyline_environment_requirements_by_id) != len(
        storyline_environment_requirements
    ):
        _fail(
            "E1_STORYLINE_ENVIRONMENT_REQUIREMENT_DUPLICATE",
            "S1 environment requirement IDs repeat",
        )
    storyline_environment_requirement_line: dict[str, str] = {}
    for requirement_id, requirement in (
        storyline_environment_requirements_by_id.items()
    ):
        line_ids = [item for item in requirement["source_ids"] if item in lines]
        if len(line_ids) != 1:
            _fail("E1_STORYLINE_ENVIRONMENT_REQUIREMENT_DANGLING", requirement_id)
        storyline_environment_requirement_line[requirement_id] = line_ids[0]
    if set(storyline_environment_requirement_line.values()) != set(lines):
        _fail(
            "E1_STORYLINE_COVERAGE_MISMATCH",
            "S1 environment requirements do not cover every storyline",
        )
    event_requirements = {
        item["id"]: item for item in storyline["event_requirements"]
    }
    event_requirement_line: dict[str, str] = {}
    for requirement_id, requirement in event_requirements.items():
        line_ids = [item for item in requirement["source_ids"] if item in lines]
        if len(line_ids) != 1:
            _fail("E1_EVENT_REQUIREMENT_DANGLING", requirement_id)
        event_requirement_line[requirement_id] = line_ids[0]
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
    demand_line: dict[str, str] = {}
    demand_support: dict[str, list[str]] = {}
    for demand in demands:
        world_requirement_ids = {
            item["id"] for item in world["storyline_requirements"]
        }
        requirement_ids = [
            item for item in demand["source_ids"] if item in world_requirement_ids
        ]
        support_ids = [
            item for item in demand["source_ids"] if item in world_entities
        ]
        if len(requirement_ids) != 1 or not support_ids:
            _fail("E1_DEMAND_SOURCE_INVALID", demand["id"])
        world_requirement = next(
            item
            for item in world["storyline_requirements"]
            if item["id"] == requirement_ids[0]
        )
        line_ids = [item for item in world_requirement["source_ids"] if item in lines]
        if len(line_ids) != 1:
            _fail("E1_STORYLINE_ID_DANGLING", demand["id"])
        demand_line[demand["id"]] = line_ids[0]
        demand_support[demand["id"]] = support_ids
    if set(demand_line.values()) != set(lines):
        _fail(
            "E1_STORYLINE_COVERAGE_MISMATCH",
            "W1 demands do not cover every S1 storyline",
        )

    environments = {item["id"]: item for item in model["environments"]}
    zones = {item["id"]: item for item in model["functional_zones"]}
    if len(environments) != len(model["environments"]) or len(zones) != len(
        model["functional_zones"]
    ):
        _fail("E1_ID_DUPLICATE", "environment or zone IDs repeat")
    responsibilities = [
        item["narrative_responsibility"] for item in environments.values()
    ]
    if len(responsibilities) != len(set(responsibilities)):
        _fail(
            "E1_ENVIRONMENT_NOT_DISTINCT",
            "each environment needs a non-equivalent narrative responsibility",
        )
    for zone in zones.values():
        if zone["environment_id"] not in environments:
            _fail("E1_ZONE_DANGLING", zone["id"])
    for environment in environments.values():
        actual_zones = {
            zone["id"]
            for zone in zones.values()
            if zone["environment_id"] == environment["id"]
        }
        if set(environment["zone_ids"]) != actual_zones or not actual_zones:
            _fail("E1_ZONE_COVERAGE_MISMATCH", environment["id"])
        allowed_stage_ids = (
            set(lines)
            | set(demands_by_id)
            | set(storyline_environment_requirements_by_id)
        )
        if (
            not set(environment["storyline_stage_ids"]).issubset(allowed_stage_ids)
            or not set(environment["storyline_stage_ids"]) & set(demands_by_id)
            or not set(environment["storyline_stage_ids"])
            & set(storyline_environment_requirements_by_id)
        ):
            _fail("E1_NEW_STORYLINE_FORBIDDEN", environment["id"])
        if (
            not environment["allowed_actions"]
            or not environment["sensory_conditions"]
            or not environment["access_rules"]
            or not environment["resources"]
            or not environment["blockers"]
            or not environment["hazards"]
        ):
            _fail("E1_ENVIRONMENT_CAPABILITY_INCOMPLETE", environment["id"])
    if semantic_profile in {
        "legacy-structured-hosting-exact-once",
        "legacy-structured-hosting-multi-affordance",
        "capability-readiness",
    }:
        _validate_environment_source_text_clean(
            environments,
            [*demands, *storyline_environment_requirements],
        )

    topology = {item["id"]: item for item in model["environment_topology"]}
    if len(topology) != len(model["environment_topology"]):
        _fail("E1_ID_DUPLICATE", "topology IDs repeat")
    for edge in topology.values():
        if edge["from_id"] not in environments or edge["to_id"] not in environments:
            _fail("E1_TOPOLOGY_DANGLING", edge["id"])
    if not _reachable(set(environments), list(topology.values())):
        _fail("E1_TOPOLOGY_UNREACHABLE", "environment graph is disconnected")
    for environment in environments.values():
        expected_connections = {
            edge["id"]
            for edge in topology.values()
            if environment["id"] in (edge["from_id"], edge["to_id"])
        }
        if set(environment["connections"]) != expected_connections:
            _fail("E1_TOPOLOGY_CONNECTION_MISMATCH", environment["id"])

    assignments = {
        item["id"]: item for item in model["access_and_authority"]
    }
    channels = {
        item["id"]: item
        for item in model["resource_and_information_channels"]
    }
    hazards = {item["id"]: item for item in model["hazards_and_failure_modes"]}
    if any(
        len(values) != len(source)
        for values, source in (
            (assignments, model["access_and_authority"]),
            (channels, model["resource_and_information_channels"]),
            (hazards, model["hazards_and_failure_modes"]),
        )
    ):
        _fail("E1_ID_DUPLICATE", "environment interface IDs repeat")
    environment_or_zone = set(environments) | set(zones)
    for assignment in assignments.values():
        if assignment["subject_id"] not in environment_or_zone:
            _fail("E1_AUTHORITY_DANGLING", assignment["id"])
        if not set(assignment["evidence_ids"]).issubset(world_entities):
            _fail("E1_WORLD_RULE_CONFLICT", assignment["id"])
    for channel in channels.values():
        if (
            channel["from_id"] not in environment_or_zone
            or channel["to_id"] not in environment_or_zone
        ):
            _fail("E1_CHANNEL_DANGLING", channel["id"])
    for hazard in hazards.values():
        if hazard["environment_id"] not in environments:
            _fail("E1_HAZARD_DANGLING", hazard["id"])
    for environment_id in environments:
        if not any(
            assignment["subject_id"] == environment_id
            for assignment in assignments.values()
        ):
            _fail("E1_AUTHORITY_COVERAGE_MISMATCH", environment_id)
        if not any(
            environment_id in (channel["from_id"], channel["to_id"])
            for channel in channels.values()
        ):
            _fail("E1_CHANNEL_COVERAGE_MISMATCH", environment_id)
        if not any(
            hazard["environment_id"] == environment_id
            for hazard in hazards.values()
        ):
            _fail("E1_HAZARD_COVERAGE_MISMATCH", environment_id)

    hosting_by_demand: dict[str, Mapping[str, Any]] = {}
    hosting_by_storyline_requirement: dict[str, Mapping[str, Any]] = {}
    for record in model["storyline_hosting_ledger"]:
        source_ids = set(record["source_ids"])
        demand_ids = source_ids & set(demands_by_id)
        storyline_requirement_ids = (
            source_ids & set(storyline_environment_requirements_by_id)
        )
        if len(demand_ids) != 1 or len(storyline_requirement_ids) != 1:
            _fail("E1_HOSTING_COVERAGE_MISMATCH", record["id"])
        demand_id = next(iter(demand_ids))
        storyline_requirement_id = next(iter(storyline_requirement_ids))
        if source_ids != {demand_id, storyline_requirement_id}:
            _fail("E1_HOSTING_COVERAGE_MISMATCH", record["id"])
        if (
            demand_id in hosting_by_demand
            or storyline_requirement_id in hosting_by_storyline_requirement
        ):
            _fail("E1_HOSTING_COVERAGE_MISMATCH", demand_id)
        if (
            demand_line[demand_id]
            != storyline_environment_requirement_line[storyline_requirement_id]
        ):
            _fail("E1_HOSTING_LINE_MISMATCH", record["id"])
        if not set(record["realization_ids"]).issubset(environments):
            _fail("E1_HOSTING_ENVIRONMENT_DANGLING", record["id"])
        demand = demands_by_id[demand_id]
        storyline_requirement = storyline_environment_requirements_by_id[
            storyline_requirement_id
        ]
        if semantic_profile in {
            "legacy-structured-hosting-exact-once",
            "legacy-structured-hosting-multi-affordance",
            "capability-readiness",
        }:
            _validate_structured_hosting_evidence(
                record,
                demand=demand,
                storyline_requirement=storyline_requirement,
                storyline_id=demand_line[demand_id],
                environments=environments,
            )
        else:
            marker = demand["responsibility"]
            storyline_marker = storyline_requirement["responsibility"]
            hosted_text = rt.canonical_json(
                [environments[item] for item in record["realization_ids"]]
            )
            if (
                marker not in hosted_text
                or marker not in record["evidence"]
                or storyline_marker not in hosted_text
                or storyline_marker not in record["evidence"]
            ):
                _fail("E1_SOURCE_MEANING_UNBOUND", demand_id)
        for environment_id in record["realization_ids"]:
            environment = environments[environment_id]
            required_stage_ids = {
                demand_line[demand_id],
                demand_id,
                storyline_requirement_id,
            }
            if not required_stage_ids.issubset(environment["storyline_stage_ids"]):
                _fail("E1_HOSTING_COVERAGE_MISMATCH", demand_id)
            if semantic_profile in {"legacy-common", "legacy-trigger-binding"} and not all(
                constraint in environment["access_rules"]
                for constraint in {
                    *demand["constraints"],
                    *storyline_requirement["constraints"],
                }
            ):
                _fail("E1_WORLD_RULE_CONFLICT", environment_id)
            relevant_assignments = [
                item
                for item in assignments.values()
                if item["subject_id"] == environment_id
            ]
            if not any(
                set(demand_support[demand_id]).issubset(item["evidence_ids"])
                for item in relevant_assignments
            ):
                _fail("E1_WORLD_RULE_CONFLICT", environment_id)
        hosting_by_demand[demand_id] = record
        hosting_by_storyline_requirement[storyline_requirement_id] = record
    if set(hosting_by_demand) != set(demands_by_id):
        _fail(
            "E1_HOSTING_COVERAGE_MISMATCH",
            "every W1 environment demand must be hosted exactly once",
        )
    if set(hosting_by_storyline_requirement) != set(
        storyline_environment_requirements_by_id
    ):
        _fail(
            "E1_HOSTING_COVERAGE_MISMATCH",
            "every S1 environment requirement must be hosted exactly once",
        )
    hosted_demands_by_environment: dict[str, set[str]] = {
        environment_id: set() for environment_id in environments
    }
    for demand_id, record in hosting_by_demand.items():
        for environment_id in record["realization_ids"]:
            hosted_demands_by_environment[environment_id].add(demand_id)
    hosted_lines_by_environment = {
        environment_id: {
            demand_line[demand_id] for demand_id in hosted_demand_ids
        }
        for environment_id, hosted_demand_ids in hosted_demands_by_environment.items()
    }

    world_rule_ids = {
        item["id"] for item in world["world_facts"] if item["kind"] == "rule"
    }
    world_system_ids = {item["id"] for item in world["systems"]}
    world_institution_ids = {item["id"] for item in world["institutions"]}
    for channel in channels.values():
        environment_endpoints = [
            item
            for item in (channel["from_id"], channel["to_id"])
            if item in environments
        ]
        zone_endpoints = [
            item
            for item in (channel["from_id"], channel["to_id"])
            if item in zones
        ]
        if (
            len(environment_endpoints) != 1
            or len(zone_endpoints) != 1
            or zones[zone_endpoints[0]]["environment_id"]
            != environment_endpoints[0]
        ):
            _fail("E1_CHANNEL_SEMANTICS_INCOMPLETE", channel["id"])
        environment_id = environment_endpoints[0]
        hosted_demand_ids = hosted_demands_by_environment[environment_id]
        if not hosted_demand_ids:
            _fail("E1_CHANNEL_SEMANTICS_INCOMPLETE", channel["id"])
        demand_tokens = _channel_tokens(channel, "DEMAND")
        support_tokens = _channel_tokens(channel, "SUPPORT")
        marker_tokens = _channel_tokens(channel, "MARKER_SHA256")
        action_tokens = _channel_tokens(channel, "ACTION_SHA256")
        expected_support_ids = {
            support_id
            for demand_id in hosted_demand_ids
            for support_id in demand_support[demand_id]
        }
        expected_marker_hashes = {
            rt.canonical_sha256(demands_by_id[demand_id]["responsibility"])
            for demand_id in hosted_demand_ids
        }
        expected_action_hashes = {
            rt.canonical_sha256(action)
            for action in environments[environment_id]["allowed_actions"]
        }
        if (
            demand_tokens != hosted_demand_ids
            or support_tokens != expected_support_ids
            or marker_tokens != expected_marker_hashes
            or not action_tokens
            or not action_tokens.issubset(expected_action_hashes)
            or not expected_support_ids & world_rule_ids
            or not expected_support_ids & world_system_ids
            or not expected_support_ids & world_institution_ids
        ):
            _fail("E1_CHANNEL_SEMANTICS_INCOMPLETE", channel["id"])

    affordances = _validate_affordance_catalog(
        model["event_affordance_catalog"],
        environments=environments,
        event_requirements=event_requirements,
        event_requirement_line=event_requirement_line,
        hosted_lines_by_environment=hosted_lines_by_environment,
        model_version=model["schema_version"],
    )
    for affordance in affordances.values():
        environment = environments[affordance["environment_id"]]
        demand_ids = set(environment["storyline_stage_ids"]) & set(demands_by_id)
        storyline_requirement_ids = set(
            environment["storyline_stage_ids"]
        ) & set(storyline_environment_requirements_by_id)
        if semantic_profile in {
            "legacy-structured-hosting-multi-affordance",
            "capability-readiness",
        }:
            affordance_lines = {
                event_requirement_line[requirement_id]
                for requirement_id in affordance["event_requirement_ids"]
            }
            demand_ids = {
                demand_id
                for demand_id in demand_ids
                if demand_line[demand_id] in affordance_lines
            }
            storyline_requirement_ids = {
                requirement_id
                for requirement_id in storyline_requirement_ids
                if storyline_environment_requirement_line[requirement_id]
                in affordance_lines
            }
        required_constraints = {
            constraint
            for demand_id in demand_ids
            for constraint in demands_by_id[demand_id]["constraints"]
        } | {
            constraint
            for requirement_id in storyline_requirement_ids
            for constraint in storyline_environment_requirements_by_id[
                requirement_id
            ]["constraints"]
        }
        if not required_constraints.issubset(affordance["constraints"]):
            _fail("E1_WORLD_RULE_CONFLICT", affordance["id"])
    transitions = {
        item["id"]: item for item in model["transition_contracts"]
    }
    if len(transitions) != len(model["transition_contracts"]):
        _fail("E1_ID_DUPLICATE", "transition IDs repeat")
    if semantic_profile != "legacy-common":
        _validate_transition_trigger_bindings(
            model["transition_contracts"],
            environments=environments,
            topology=topology,
            assignments=assignments,
            affordances=affordances,
            storyline=storyline,
            event_requirement_line=event_requirement_line,
        )
    for transition in transitions.values():
        environment = environments.get(transition["subject_id"])
        if environment is None:
            _fail("E1_TRANSITION_SUBJECT_DANGLING", transition["id"])
        if (
            transition["from_state"] not in environment["state_vocabulary"]
            or transition["to_state"] not in environment["state_vocabulary"]
        ):
            _fail("E1_TRANSITION_STATE_INVALID", transition["id"])
        if not set(transition["trigger_ids"]).issubset(affordances):
            _fail("E1_TRANSITION_TRIGGER_INVALID", transition["id"])
        if semantic_profile == "legacy-common" and any(
            affordances[trigger_id]["environment_id"] != transition["subject_id"]
            for trigger_id in transition["trigger_ids"]
        ):
            _fail("E1_TRANSITION_ENVIRONMENT_MISMATCH", transition["id"])
        allowed = set(assignments) | set(world_entities)
        if not set(transition["allowed_by_ids"]).issubset(allowed):
            _fail("E1_WORLD_RULE_CONFLICT", transition["id"])
    for environment in environments.values():
        expected_transitions = {
            item["id"]
            for item in transitions.values()
            if item["subject_id"] == environment["id"]
        }
        if (
            set(environment["allowed_transitions"]) != expected_transitions
            or not expected_transitions
        ):
            _fail("E1_TRANSITION_COVERAGE_MISMATCH", environment["id"])

    if semantic_profile == "capability-readiness":
        _v24_validate_capability_model(
            model,
            storyline=storyline,
            world=world,
            environments=environments,
            zones=zones,
            affordances=affordances,
            assignments=assignments,
            topology=topology,
            event_requirement_line=event_requirement_line,
        )

    locked = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    }
    author_open = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    }
    owned_entities: dict[str, Mapping[str, Any]] = {
        **environments,
        **zones,
        **topology,
        **assignments,
        **channels,
        **hazards,
        **{
            item["id"]: item for item in model["storyline_hosting_ledger"]
        },
        **affordances,
        **transitions,
    }
    if semantic_profile == "capability-readiness":
        owned_entities.update(
            {
                **{item["id"]: item for item in model["capability_fact_registry"]},
                **{item["id"]: item for item in model["capability_step_registry"]},
                **{item["id"]: item for item in model["ambient_context_hosts"]},
                **{item["id"]: item for item in model["actor_authority_bindings"]},
                **{
                    item["id"]: item
                    for item in model["capability_occurrence_requirements"]
                },
                **{
                    item["id"]: item
                    for item in model["obligation_occurrence_bindings"]
                },
                **{item["id"]: item for item in model["story_transition_support"]},
                **{
                    item["id"]: item
                    for item in model["initial_anchor_option_realization_ledger"]
                },
                **{
                    option["support_option_id"]: option
                    for anchor in model["initial_anchor_support"]
                    for option in anchor["support_options"]
                },
                **{
                    option["capability_demand_id"]: option
                    for anchor in model["initial_anchor_support"]
                    for option in anchor["support_options"]
                },
            }
        )
    decisions = {item["id"]: item for item in model["design_decisions"]}
    if set(partition["author_locked"]) != locked:
        _fail("E1_AUTHORITY_PARTITION_MISMATCH", "author_locked differs from B0")
    if set(partition["author_open"]) != author_open:
        _fail("E1_AUTHORITY_PARTITION_MISMATCH", "author_open differs from B0")
    if set(partition["autonomous_owned"]) != set(owned_entities) | set(decisions):
        _fail("E1_AUTHORITY_PARTITION_MISMATCH", "E1 owned set is not exact")
    if set(partition["downstream_freedom"]) != set(event_requirements):
        _fail("E1_AUTHORITY_PARTITION_MISMATCH", "T1 handoff set is not exact")
    for decision in decisions.values():
        if (
            decision["owner"] != "E1"
            or decision["selection"] not in decision["options"]
            or not set(decision["projection_ids"]).issubset(owned_entities)
        ):
            _fail("E1_DECISION_INVALID", decision["id"])
    for claim in model["derivation_claims"]:
        if len(claim["projection_ids"]) == 1:
            projection = owned_entities.get(claim["projection_ids"][0])
            if projection is None or claim["value_sha256"] != rt.canonical_sha256(
                projection
            ):
                _fail("E1_DERIVATION_STALE", claim["id"])
    claimed = {
        item["projection_ids"][0]
        for item in model["derivation_claims"]
        if len(item["projection_ids"]) == 1
    }
    if not set(environments).issubset(claimed) or not set(affordances).issubset(
        claimed
    ):
        _fail(
            "E1_DERIVATION_INCOMPLETE",
            "each environment and action interface needs derivation evidence",
        )
    actual_open = {
        source_id
        for item in model["open_items"]
        for source_id in item["source_ids"]
    }
    if actual_open != author_open:
        _fail("E1_OPEN_ITEMS_MISMATCH", "author-open controls changed")
    if expected_gate is not None and model["input_gate"] != expected_gate:
        _fail("E1_GATE_REFERENCE_MISMATCH", "model gate is not stored gate")
    if expected_sources is not None and model["source_artifacts"] != list(
        expected_sources
    ):
        _fail(
            "E1_SOURCE_ARTIFACT_MISMATCH",
            "model does not bind exact B0/S1/W1 sources",
        )


def start_e1_session(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    if root.exists():
        _fail("E1_SESSION_EXISTS", str(root))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("E1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    (
        b0_root,
        s1_root,
        w1_root,
        baseline,
        storyline,
        world,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    session = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "E1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_ref, s1_ref, w1_ref
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref],
        "source_artifacts": _source_artifacts(b0_root, s1_root, w1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "storyline_environment_requirement_bindings": _object_bindings(
            storyline["environment_requirements"], extra="target_stage"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "world_rule_bindings": _object_bindings(world["world_facts"], extra="kind"),
        "environment_demand_bindings": _object_bindings(
            world["environment_demands"], extra="target_stage"
        ),
        "implementation_bindings": _implementation_bindings(),
        "review_source_bindings": _review_source_bindings(s1_root, w1_root),
        "authority_review_protocol": AUTHORITY_REVIEW_PROTOCOL,
        "hosting_review_protocol": HOSTING_REVIEW_PROTOCOL,
        "phases": list(PHASES),
    }
    root.mkdir(parents=True)
    _write(root / "generation-session.json", session)
    return copy.deepcopy(session)


def _validated_session(
    workspace: Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    session = _read(workspace / "generation-session.json", "E1_SESSION_INVALID")
    (
        b0_root,
        s1_root,
        w1_root,
        baseline,
        storyline,
        world,
        controls,
        b0_ref,
        s1_ref,
        w1_ref,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        input_gate=input_gate,
        runtime=runtime,
        full_validation=full_validation,
    )
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    expected = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "E1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_ref, s1_ref, w1_ref
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref],
        "source_artifacts": _source_artifacts(b0_root, s1_root, w1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "storyline_environment_requirement_bindings": _object_bindings(
            storyline["environment_requirements"], extra="target_stage"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "world_rule_bindings": _object_bindings(world["world_facts"], extra="kind"),
        "environment_demand_bindings": _object_bindings(
            world["environment_demands"], extra="target_stage"
        ),
        "implementation_bindings": _implementation_bindings(),
        "review_source_bindings": _review_source_bindings(s1_root, w1_root),
        "authority_review_protocol": AUTHORITY_REVIEW_PROTOCOL,
        "hosting_review_protocol": HOSTING_REVIEW_PROTOCOL,
        "phases": list(PHASES),
    }
    if not thread_id or session != expected:
        _fail("E1_SESSION_INVALID", "session no longer binds B0/S1/W1/gate/thread")
    return session, baseline, storyline, world, controls


def _require_generation_schema(model: Mapping[str, Any]) -> None:
    if model.get("schema_version") != CURRENT_MODEL_SCHEMA_VERSION:
        _fail(
            "E1_LEGACY_GENERATION_FORBIDDEN",
            "E1 schemas 2.0/2.1/2.2/2.3 are accepted only by read-only package validation",
        )


def _validate_phase3_trigger_contract(
    root: Path,
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
) -> None:
    architecture_evidence = _read(
        root / "generation-evidence" / "02-environment-architecture.json",
        "E1_EVIDENCE_MISSING",
    )
    architecture_payload = architecture_evidence.get("payload")
    if (
        not isinstance(architecture_payload, Mapping)
        or architecture_evidence.get("phase") != "environment-architecture"
        or architecture_evidence.get("payload_sha256")
        != rt.canonical_sha256(architecture_payload)
    ):
        _fail("E1_EVIDENCE_INVALID", "environment-architecture")
    try:
        environments = {
            item["id"]: item for item in architecture_payload["environments"]
        }
        topology = {item["id"]: item for item in payload["environment_topology"]}
        assignments = {
            item["id"]: item for item in payload["access_and_authority"]
        }
        if (
            len(environments) != len(architecture_payload["environments"])
            or len(topology) != len(payload["environment_topology"])
            or len(assignments) != len(payload["access_and_authority"])
        ):
            _fail("E1_ID_DUPLICATE", "phase-3 trigger inputs repeat")
        _validate_transition_trigger_bindings(
            payload["transition_contracts"],
            environments=environments,
            topology=topology,
            assignments=assignments,
            affordances=None,
            storyline=storyline,
            event_requirement_line=None,
        )
    except E1Error:
        raise
    except (KeyError, TypeError, ValueError) as error:
        _fail("E1_PHASE_PAYLOAD_INVALID", f"invalid phase-3 trigger contract: {error}")


def _sealed_phase_payload(
    root: Path, *, sequence: int, phase: str
) -> Mapping[str, Any]:
    evidence = _read(
        root / "generation-evidence" / f"{sequence:02d}-{phase}.json",
        "E1_EVIDENCE_MISSING",
    )
    payload = evidence.get("payload")
    if (
        not isinstance(payload, Mapping)
        or evidence.get("phase") != phase
        or evidence.get("payload_sha256") != rt.canonical_sha256(payload)
    ):
        _fail("E1_EVIDENCE_INVALID", phase)
    return payload


def _validate_definition(
    runtime: Any,
    value: Any,
    *,
    schema_name: str,
    definition_name: str,
    code: str,
) -> None:
    try:
        runtime.validate_definition(value, schema_name, definition_name)
    except Exception as error:
        _fail(code, str(error))


def _validate_phase1_projection_contract(
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    *,
    source_artifacts: Sequence[Mapping[str, str]] | None = None,
) -> None:
    if (
        payload.get("storyline_environment_requirements")
        != storyline["environment_requirements"]
        or payload.get("environment_demands") != world["environment_demands"]
    ):
        _fail("E1_DEMAND_PROJECTION_MISMATCH", "phase 1 must be exact")
    lines = {item["id"] for item in storyline["storylines"]}
    world_requirements = {
        item["id"]: item for item in world["storyline_requirements"]
    }
    requirement_lines: list[str] = []
    for requirement in payload["storyline_environment_requirements"]:
        source_lines = [item for item in requirement["source_ids"] if item in lines]
        if len(source_lines) != 1:
            _fail("E1_STORYLINE_ENVIRONMENT_REQUIREMENT_DANGLING", requirement["id"])
        requirement_lines.append(source_lines[0])
    demand_lines: list[str] = []
    for demand in payload["environment_demands"]:
        requirement_ids = [
            item for item in demand["source_ids"] if item in world_requirements
        ]
        if len(requirement_ids) != 1:
            _fail("E1_DEMAND_SOURCE_INVALID", demand["id"])
        source_lines = [
            item
            for item in world_requirements[requirement_ids[0]]["source_ids"]
            if item in lines
        ]
        if len(source_lines) != 1:
            _fail("E1_STORYLINE_ID_DANGLING", demand["id"])
        demand_lines.append(source_lines[0])
    if (
        set(requirement_lines) != lines
        or set(demand_lines) != lines
        or sorted(requirement_lines) != sorted(demand_lines)
    ):
        _fail("E1_HOSTING_LINE_MISMATCH", "phase-1 source pairing differs")
    digest_fields = set(PHASE_FIELDS["environment-demand-scan"]) - {
        "environment_demands",
        "storyline_environment_requirements",
    }
    if source_artifacts is None:
        if any(name in payload for name in digest_fields):
            _fail("E1_UNIVERSE_SOURCE_INVALID", "sealed S1 source is unavailable")
        return
    expected = _v24_expected_universe_digests(
        {"source_artifacts": list(source_artifacts)}, storyline
    )
    for name in digest_fields:
        if payload.get(name) != expected[name]:
            _fail("E1_UNIVERSE_DIGEST_MISMATCH", name)


def _validate_phase2_initial_anchor_contract(
    payload: Mapping[str, Any],
    *,
    storyline: Mapping[str, Any],
    environments: Mapping[str, Mapping[str, Any]],
    runtime: Any,
) -> None:
    anchors = payload.get("initial_anchor_support")
    if not isinstance(anchors, list) or not anchors:
        _fail("E1_INITIAL_ANCHOR_COVERAGE_MISMATCH", "anchors missing")
    for anchor in anchors:
        _validate_definition(
            runtime,
            anchor,
            schema_name="environment-system.schema.json",
            definition_name="initialAnchorSupport",
            code="E1_PHASE2_DEFINITION_INVALID",
        )
    lines = {item["id"]: item for item in storyline["storylines"]}
    by_line = {item["storyline_id"]: item for item in anchors}
    if len(by_line) != len(anchors) or set(by_line) != set(lines):
        _fail("E1_INITIAL_ANCHOR_COVERAGE_MISMATCH", "state-0 universe")
    option_ids: set[str] = set()
    demand_ids: set[str] = set()
    claim_ids: set[str] = set()
    for line_id, anchor in by_line.items():
        line = lines[line_id]
        if (
            anchor["state_index"] != 0
            or anchor["state"] != line["start_state"]
            or anchor["state_sha256"] != rt.canonical_sha256(line["start_state"])
            or line_id not in anchor["source_ids"]
        ):
            _fail("E1_INITIAL_ANCHOR_PROJECTION_MISMATCH", line_id)
        for option in anchor["support_options"]:
            expected = _v24_initial_option_ids(
                storyline_id=line_id,
                descriptor=option["capability_descriptor"],
                source_ids=option["source_ids"],
            )
            observed = (
                option["support_option_id"],
                option["capability_demand_id"],
                option["semantic_review_claim_id"],
            )
            if observed != expected:
                _fail("E1_INITIAL_OPTION_ID_INVALID", line_id)
            descriptor = option["capability_descriptor"]
            if not set(descriptor["environment_ids"]).issubset(environments):
                _fail("E1_INITIAL_OPTION_ENVIRONMENT_DANGLING", observed[0])
            if (
                observed[0] in option_ids
                or observed[1] in demand_ids
                or observed[2] in claim_ids
            ):
                _fail("E1_INITIAL_OPTION_DUPLICATE", observed[0])
            option_ids.add(observed[0])
            demand_ids.add(observed[1])
            claim_ids.add(observed[2])


def _validate_phase2_architecture_contract(
    root: Path,
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    runtime: Any,
) -> None:
    phase1 = _sealed_phase_payload(
        root, sequence=1, phase="environment-demand-scan"
    )
    session = _read(root / "generation-session.json", "E1_SESSION_INVALID")
    _validate_phase1_projection_contract(
        phase1,
        storyline,
        world,
        source_artifacts=session.get("source_artifacts"),
    )
    decisions = payload.get("design_decisions")
    environments_list = payload.get("environments")
    if not isinstance(decisions, list) or not decisions or not isinstance(
        environments_list, list
    ) or not environments_list:
        _fail("E1_PHASE_PAYLOAD_INVALID", "phase-2 definitions missing")
    for item in decisions:
        _validate_definition(
            runtime,
            item,
            schema_name="canonical-common.schema.json",
            definition_name="designDecision",
            code="E1_PHASE2_DEFINITION_INVALID",
        )
    for item in environments_list:
        _validate_definition(
            runtime,
            item,
            schema_name="environment-system.schema.json",
            definition_name="environment",
            code="E1_PHASE2_DEFINITION_INVALID",
        )
    environments = {item["id"]: item for item in environments_list}
    if len(environments) != len(environments_list) or len(
        {item["id"] for item in decisions}
    ) != len(decisions):
        _fail("E1_ID_DUPLICATE", "phase-2 IDs repeat")
    responsibilities = [item["narrative_responsibility"] for item in environments_list]
    if len(responsibilities) != len(set(responsibilities)):
        _fail("E1_ENVIRONMENT_NOT_DISTINCT", "phase-2 responsibilities repeat")
    lines = {item["id"] for item in storyline["storylines"]}
    demands = {item["id"] for item in world["environment_demands"]}
    requirements = {item["id"] for item in storyline["environment_requirements"]}
    for environment in environments_list:
        stage_ids = set(environment["storyline_stage_ids"])
        if (
            not stage_ids.issubset(lines | demands | requirements)
            or not stage_ids & lines
            or not stage_ids & demands
            or not stage_ids & requirements
        ):
            _fail("E1_NEW_STORYLINE_FORBIDDEN", environment["id"])
    _validate_environment_source_text_clean(
        environments,
        [*world["environment_demands"], *storyline["environment_requirements"]],
    )
    for decision in decisions:
        if (
            decision["owner"] != "E1"
            or decision["selection"] not in decision["options"]
            or not set(decision["projection_ids"]) & set(environments)
        ):
            _fail("E1_DECISION_INVALID", decision["id"])
    _validate_phase2_initial_anchor_contract(
        payload,
        storyline=storyline,
        environments=environments,
        runtime=runtime,
    )


def _validate_phase3_definition_contract(
    root: Path,
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    runtime: Any,
) -> None:
    architecture = _sealed_phase_payload(
        root, sequence=2, phase="environment-architecture"
    )
    _validate_phase2_architecture_contract(
        root, architecture, storyline, world, runtime
    )
    definitions = (
        ("functional_zones", "zone"),
        ("environment_topology", "environmentTopologyEdge"),
        ("access_and_authority", "assignment"),
        ("resource_and_information_channels", "relationEdge"),
        ("hazards_and_failure_modes", "failureMode"),
        ("transition_contracts", "environmentStateTransition"),
        ("event_affordance_catalog", "affordance"),
        ("capability_fact_registry", "capabilityFact"),
        ("capability_step_registry", "capabilityStep"),
        ("ambient_context_hosts", "ambientContextHost"),
        ("actor_authority_bindings", "actorAuthorityBinding"),
        (
            "capability_occurrence_requirements",
            "capabilityOccurrenceRequirement",
        ),
    )
    optional_empty_fields = {
        "ambient_context_hosts",
        "capability_occurrence_requirements",
    }
    for field, definition in definitions:
        values = payload.get(field)
        if not isinstance(values, list) or (
            not values and field not in optional_empty_fields
        ):
            _fail("E1_PHASE3_DEFINITION_INVALID", field)
        schema_name = (
            "environment-system.schema.json"
            if definition
            in {
                "zone",
                "environmentTopologyEdge",
                "failureMode",
                "environmentStateTransition",
                "affordance",
                "capabilityFact",
                "capabilityStep",
                "ambientContextHost",
                "actorAuthorityBinding",
                "capabilityOccurrenceRequirement",
            }
            else "canonical-common.schema.json"
        )
        for item in values:
            _validate_definition(
                runtime,
                item,
                schema_name=schema_name,
                definition_name=definition,
                code="E1_PHASE3_DEFINITION_INVALID",
            )
    environments = {item["id"]: item for item in architecture["environments"]}
    zones = {item["id"]: item for item in payload["functional_zones"]}
    topology = {item["id"]: item for item in payload["environment_topology"]}
    assignments = {item["id"]: item for item in payload["access_and_authority"]}
    channels = {
        item["id"]: item for item in payload["resource_and_information_channels"]
    }
    hazards = {item["id"]: item for item in payload["hazards_and_failure_modes"]}
    transitions = {item["id"]: item for item in payload["transition_contracts"]}
    for values, source in (
        (zones, payload["functional_zones"]),
        (topology, payload["environment_topology"]),
        (assignments, payload["access_and_authority"]),
        (channels, payload["resource_and_information_channels"]),
        (hazards, payload["hazards_and_failure_modes"]),
        (transitions, payload["transition_contracts"]),
    ):
        if len(values) != len(source):
            _fail("E1_ID_DUPLICATE", "phase-3 IDs repeat")
    if len(set().union(*[set(values) for values in (
        zones, topology, assignments, channels, hazards, transitions
    )])) != sum(len(values) for values in (
        zones, topology, assignments, channels, hazards, transitions
    )):
        _fail("E1_ID_DUPLICATE", "phase-3 IDs collide")
    environment_or_zone = set(environments) | set(zones)
    world_entity_map = {
        item["id"]: item
        for field in (
            "world_facts", "history_pressures", "institutions", "systems",
            "resource_flows", "authority_flows", "information_flows",
            "rule_conflict_matrix", "storyline_support_ledger",
        )
        for item in world[field]
    }
    world_entities = set(world_entity_map)
    for zone in zones.values():
        if zone["environment_id"] not in environments:
            _fail("E1_ZONE_DANGLING", zone["id"])
    for environment in environments.values():
        expected_zones = {
            item["id"] for item in zones.values()
            if item["environment_id"] == environment["id"]
        }
        if set(environment["zone_ids"]) != expected_zones or not expected_zones:
            _fail("E1_ZONE_COVERAGE_MISMATCH", environment["id"])
    for edge in topology.values():
        if edge["from_id"] not in environments or edge["to_id"] not in environments:
            _fail("E1_TOPOLOGY_DANGLING", edge["id"])
    if not _reachable(set(environments), list(topology.values())):
        _fail("E1_TOPOLOGY_UNREACHABLE", "phase-3 graph")
    for environment in environments.values():
        incident = {
            edge["id"] for edge in topology.values()
            if environment["id"] in (edge["from_id"], edge["to_id"])
        }
        if set(environment["connections"]) != incident:
            _fail("E1_TOPOLOGY_CONNECTION_MISMATCH", environment["id"])
    for assignment in assignments.values():
        if assignment["subject_id"] not in environment_or_zone:
            _fail("E1_AUTHORITY_DANGLING", assignment["id"])
        if not set(assignment["evidence_ids"]).issubset(world_entities):
            _fail("E1_WORLD_RULE_CONFLICT", assignment["id"])
    for channel in channels.values():
        if channel["from_id"] not in environment_or_zone or channel["to_id"] not in environment_or_zone:
            _fail("E1_CHANNEL_DANGLING", channel["id"])
    for hazard in hazards.values():
        if hazard["environment_id"] not in environments:
            _fail("E1_HAZARD_DANGLING", hazard["id"])
    for transition in transitions.values():
        environment = environments.get(transition["subject_id"])
        if environment is None:
            _fail("E1_TRANSITION_SUBJECT_DANGLING", transition["id"])
        if transition["from_state"] not in environment["state_vocabulary"] or transition["to_state"] not in environment["state_vocabulary"]:
            _fail("E1_TRANSITION_STATE_INVALID", transition["id"])
        if not set(transition["allowed_by_ids"]).issubset(set(assignments) | world_entities):
            _fail("E1_WORLD_RULE_CONFLICT", transition["id"])
    for environment_id, environment in environments.items():
        expected_transitions = {
            item["id"] for item in transitions.values()
            if item["subject_id"] == environment_id
        }
        if set(environment["allowed_transitions"]) != expected_transitions or not expected_transitions:
            _fail("E1_TRANSITION_COVERAGE_MISMATCH", environment_id)
        if not any(item["subject_id"] == environment_id for item in assignments.values()):
            _fail("E1_AUTHORITY_COVERAGE_MISMATCH", environment_id)
        if not any(environment_id in (item["from_id"], item["to_id"]) for item in channels.values()):
            _fail("E1_CHANNEL_COVERAGE_MISMATCH", environment_id)
        if not any(item["environment_id"] == environment_id for item in hazards.values()):
            _fail("E1_HAZARD_COVERAGE_MISMATCH", environment_id)
    demands = {item["id"]: item for item in world["environment_demands"]}
    demand_support = {
        demand_id: {
            source_id for source_id in demand["source_ids"]
            if source_id in world_entities
        }
        for demand_id, demand in demands.items()
    }
    world_rule_ids = {
        item["id"] for item in world["world_facts"] if item["kind"] == "rule"
    }
    world_system_ids = {item["id"] for item in world["systems"]}
    world_institution_ids = {item["id"] for item in world["institutions"]}
    for environment_id, environment in environments.items():
        hosted_demand_ids = set(environment["storyline_stage_ids"]) & set(demands)
        if not hosted_demand_ids:
            _fail("E1_DEMAND_SOURCE_INVALID", environment_id)
        relevant_assignments = [
            item for item in assignments.values()
            if item["subject_id"] == environment_id
        ]
        for demand_id in hosted_demand_ids:
            if not any(
                demand_support[demand_id].issubset(set(item["evidence_ids"]))
                for item in relevant_assignments
            ):
                _fail("E1_WORLD_RULE_CONFLICT", environment_id)
        environment_channels = [
            item for item in channels.values()
            if environment_id in (item["from_id"], item["to_id"])
        ]
        for channel in environment_channels:
            environment_endpoints = [
                item for item in (channel["from_id"], channel["to_id"])
                if item in environments
            ]
            zone_endpoints = [
                item for item in (channel["from_id"], channel["to_id"])
                if item in zones
            ]
            expected_support_ids = {
                support_id
                for demand_id in hosted_demand_ids
                for support_id in demand_support[demand_id]
            }
            if (
                len(environment_endpoints) != 1
                or len(zone_endpoints) != 1
                or zones[zone_endpoints[0]]["environment_id"] != environment_id
                or _channel_tokens(channel, "DEMAND") != hosted_demand_ids
                or _channel_tokens(channel, "SUPPORT") != expected_support_ids
                or _channel_tokens(channel, "MARKER_SHA256")
                != {
                    rt.canonical_sha256(demands[demand_id]["responsibility"])
                    for demand_id in hosted_demand_ids
                }
                or not _channel_tokens(channel, "ACTION_SHA256")
                or not _channel_tokens(channel, "ACTION_SHA256").issubset(
                    {
                        rt.canonical_sha256(action)
                        for action in environment["allowed_actions"]
                    }
                )
                or not expected_support_ids & world_rule_ids
                or not expected_support_ids & world_system_ids
                or not expected_support_ids & world_institution_ids
            ):
                _fail("E1_CHANNEL_SEMANTICS_INCOMPLETE", channel["id"])

    phase1 = _sealed_phase_payload(
        root, sequence=1, phase="environment-demand-scan"
    )
    session = _read(root / "generation-session.json", "E1_SESSION_INVALID")
    provisional = {
        "schema_version": CURRENT_MODEL_SCHEMA_VERSION,
        "source_artifacts": copy.deepcopy(session["source_artifacts"]),
        **copy.deepcopy(phase1),
        **copy.deepcopy(architecture),
        **copy.deepcopy(dict(payload)),
    }
    event_requirements = {
        item["id"]: item for item in storyline["event_requirements"]
    }
    event_requirement_line = {
        requirement_id: next(
            source_id
            for source_id in requirement["source_ids"]
            if source_id in {line["id"] for line in storyline["storylines"]}
        )
        for requirement_id, requirement in event_requirements.items()
    }
    hosted_lines_by_environment = {
        environment_id: set(environment["storyline_stage_ids"])
        & {line["id"] for line in storyline["storylines"]}
        for environment_id, environment in environments.items()
    }
    affordances = _validate_affordance_catalog(
        payload["event_affordance_catalog"],
        environments=environments,
        event_requirements=event_requirements,
        event_requirement_line=event_requirement_line,
        hosted_lines_by_environment=hosted_lines_by_environment,
        model_version=CURRENT_MODEL_SCHEMA_VERSION,
    )
    _v24_validate_capability_model(
        provisional,
        storyline=storyline,
        world=world,
        environments=environments,
        zones=zones,
        affordances=affordances,
        assignments=assignments,
        topology=topology,
        event_requirement_line=event_requirement_line,
        through_phase=3,
    )
    _validate_v24_e1_source_anchors(provisional, root=root)


def _validate_v24_e1_source_anchors(
    model: Mapping[str, Any], *, root: Path
) -> None:
    phase2_path = root / "generation-evidence" / "02-environment-architecture.json"
    phase2 = _read(phase2_path, "E1_EVIDENCE_MISSING")
    artifact = rt.artifact_reference(phase2_path, root=root)
    payload = phase2.get("payload")
    if not isinstance(payload, Mapping):
        _fail("E1_EVIDENCE_INVALID", "phase-2 payload")
    environments = {
        item["id"]: item for item in payload.get("environments", [])
    }
    environment_indexes = {
        item["id"]: index for index, item in enumerate(payload.get("environments", []))
    }
    for fact in model.get("capability_fact_registry", []):
        anchor = fact.get("source_anchor", {})
        if anchor.get("source_kind") != "e1_initial_state":
            continue
        value = _resolve_json_pointer(phase2, anchor["source_pointer"])
        environment = environments.get(anchor["environment_id"])
        environment_index = environment_indexes.get(anchor["environment_id"])
        field_by_kind = {
            "environment": "state_vocabulary",
            "resource": "resources",
            "authority": "access_rules",
        }
        source_field = field_by_kind.get(anchor["subject_kind"])
        allowed_values = environment.get(source_field, []) if environment else []
        value_indexes = [
            index for index, item in enumerate(allowed_values) if item == value
        ]
        expected_pointer = (
            f"/payload/environments/{environment_index}/{source_field}/{value_indexes[0]}"
            if environment_index is not None
            and source_field is not None
            and len(value_indexes) == 1
            else None
        )
        expected_subject_id = (
            "E1SRC-"
            + rt.canonical_sha256(
                [
                    anchor["environment_id"],
                    anchor["subject_kind"],
                    expected_pointer,
                    value,
                ]
            )[:20]
            if expected_pointer is not None
            else None
        )
        if (
            anchor["source_artifact"] != {"stage": "E1", **artifact}
            or environment is None
            or expected_pointer is None
            or anchor["source_pointer"] != expected_pointer
            or anchor["value_sha256"] != rt.canonical_sha256(value)
            or anchor["state"] != value
            or anchor["subject_id"] != expected_subject_id
            or fact["root_policy"] not in {"root_allowed", "producer_required"}
        ):
            _fail("E1_CAPABILITY_FACT_SOURCE_INVALID", fact["id"])


def _validate_phase4_hosting_contract(
    root: Path,
    payload: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    session: Mapping[str, Any],
    runtime: Any,
) -> None:
    architecture = _sealed_phase_payload(
        root, sequence=2, phase="environment-architecture"
    )
    topology = _sealed_phase_payload(
        root, sequence=3, phase="zones-and-topology"
    )
    _validate_phase3_definition_contract(root, topology, storyline, world, runtime)
    _validate_phase3_trigger_contract(root, topology, storyline)
    try:
        environments = {item["id"]: item for item in architecture["environments"]}
        assignments = {
            item["id"]: item for item in topology["access_and_authority"]
        }
        records = payload["storyline_hosting_ledger"]
        if (
            len(environments) != len(architecture["environments"])
            or len(assignments) != len(topology["access_and_authority"])
            or not isinstance(records, list)
            or not records
        ):
            _fail("E1_PHASE_PAYLOAD_INVALID", "phase-4 hosting inputs repeat")
        lines = {item["id"]: item for item in storyline["storylines"]}
        requirements = {
            item["id"]: item for item in storyline["environment_requirements"]
        }
        requirement_line = {
            requirement_id: next(
                source_id
                for source_id in requirement["source_ids"]
                if source_id in lines
            )
            for requirement_id, requirement in requirements.items()
        }
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
        demands = {item["id"]: item for item in world["environment_demands"]}
        demand_line: dict[str, str] = {}
        demand_support: dict[str, set[str]] = {}
        for demand_id, demand in demands.items():
            world_requirement_id = next(
                source_id
                for source_id in demand["source_ids"]
                if source_id in world_requirements
            )
            demand_line[demand_id] = next(
                source_id
                for source_id in world_requirements[world_requirement_id][
                    "source_ids"
                ]
                if source_id in lines
            )
            demand_support[demand_id] = {
                source_id
                for source_id in demand["source_ids"]
                if source_id in world_entities
            }

        seen_demands: set[str] = set()
        seen_requirements: set[str] = set()
        for record in records:
            if not isinstance(record, Mapping):
                _fail("E1_PHASE_PAYLOAD_INVALID", "hosting record is not an object")
            source_ids = set(record.get("source_ids", []))
            demand_ids = source_ids & set(demands)
            requirement_ids = source_ids & set(requirements)
            if (
                len(demand_ids) != 1
                or len(requirement_ids) != 1
                or source_ids != demand_ids | requirement_ids
            ):
                _fail("E1_HOSTING_COVERAGE_MISMATCH", record.get("id", "record"))
            demand_id = next(iter(demand_ids))
            requirement_id = next(iter(requirement_ids))
            if demand_id in seen_demands or requirement_id in seen_requirements:
                _fail("E1_HOSTING_COVERAGE_MISMATCH", record.get("id", "record"))
            if demand_line[demand_id] != requirement_line[requirement_id]:
                _fail("E1_HOSTING_LINE_MISMATCH", record.get("id", "record"))
            realization_ids = record.get("realization_ids")
            if not isinstance(realization_ids, list) or not set(
                realization_ids
            ).issubset(environments):
                _fail(
                    "E1_HOSTING_ENVIRONMENT_DANGLING", record.get("id", "record")
                )
            _validate_structured_hosting_evidence(
                record,
                demand=demands[demand_id],
                storyline_requirement=requirements[requirement_id],
                storyline_id=demand_line[demand_id],
                environments=environments,
            )
            for environment_id in realization_ids:
                environment = environments[environment_id]
                if not {
                    demand_line[demand_id],
                    demand_id,
                    requirement_id,
                }.issubset(environment["storyline_stage_ids"]):
                    _fail("E1_HOSTING_COVERAGE_MISMATCH", environment_id)
                relevant = [
                    assignment
                    for assignment in assignments.values()
                    if assignment["subject_id"] == environment_id
                ]
                if not any(
                    demand_support[demand_id].issubset(
                        set(assignment["evidence_ids"])
                    )
                    for assignment in relevant
                ):
                    _fail("E1_WORLD_RULE_CONFLICT", environment_id)
            seen_demands.add(demand_id)
            seen_requirements.add(requirement_id)
        if seen_demands != set(demands) or seen_requirements != set(requirements):
            _fail(
                "E1_HOSTING_COVERAGE_MISMATCH",
                "phase 4 must cover both source universes exactly once",
            )
        phase1 = _sealed_phase_payload(
            root, sequence=1, phase="environment-demand-scan"
        )
        provisional_model = {
            "schema_version": CURRENT_MODEL_SCHEMA_VERSION,
            "skill": "novel-environment-system-designer",
            "stage": "E1",
            "run_id": session["run_id"],
            "status": "ready",
            "input_gate": copy.deepcopy(session["input_gate"]),
            "source_artifacts": copy.deepcopy(session["source_artifacts"]),
            **copy.deepcopy(phase1),
            **copy.deepcopy(architecture),
            **copy.deepcopy(topology),
            **copy.deepcopy(dict(payload)),
        }
        _validate_model(
            provisional_model,
            baseline,
            storyline,
            world,
            controls,
            runtime,
            expected_gate=session["input_gate"],
            expected_sources=session["source_artifacts"],
        )
        _validate_v24_e1_source_anchors(provisional_model, root=root)
    except E1Error:
        raise
    except (KeyError, StopIteration, TypeError, ValueError) as error:
        _fail("E1_PHASE_PAYLOAD_INVALID", f"invalid phase-4 hosting contract: {error}")


_HOSTING_RECORD_REVIEW_CHECKS = (
    "same_line_pair",
    "responsibility_semantics",
    "constraint_semantics",
    "merged_realization_coherence",
    "no_generic_dump",
    "pointer_reuse_coherence",
)

_TRANSITION_RECORD_REVIEW_CHECKS = (
    "support_mode_sufficient",
    "source_binding_exact",
    "boundary_preserved",
    "no_story_outcome_claimed",
    "occurrence_basis_objective",
)


def _semantic_review_paths(
    root: Path, *, kind: str, candidate_sha256: str
) -> tuple[Path, Path, Path]:
    if kind == "authority":
        review_root = root / "authority-semantic-reviews" / candidate_sha256
    elif kind == "transition":
        review_root = root / "hosting-semantic-reviews" / candidate_sha256
    else:
        _fail("E1_SEMANTIC_REVIEW_INVALID", kind)
    return (
        review_root / "candidate.json",
        review_root / "request.json",
        review_root / "review.json",
    )


def _semantic_review_package_paths(review_path: Path) -> tuple[Path, Path]:
    return review_path.parent / "validation.json", review_path.parent / "manifest.json"


def _review_task_output_path(review_path: Path) -> Path:
    return review_path.parent / "review-task-output.json"


def seal_e1_review_task_output(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    review_kind: str,
    task_id: str,
    verdict_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal the independently produced review-task output before submission."""
    root = Path(workspace).resolve()
    kind = "authority" if review_kind == "authority-capability-semantics" else (
        "transition" if review_kind == "transition-support-semantics" else ""
    )
    if not kind or not isinstance(task_id, str) or not task_id.strip():
        _fail("E1_REVIEW_TASK_OUTPUT_INVALID", str(review_kind))
    _candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind=kind, candidate_sha256=candidate_sha256
    )
    request = _read(request_path, "E1_REVIEW_TASK_OUTPUT_INVALID")
    reviewer_thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if (
        not reviewer_thread_id
        or reviewer_thread_id == request.get("producer_thread_id")
        or request.get("candidate_sha256") != candidate_sha256
        or request.get("review_kind") != review_kind
    ):
        _fail("E1_REVIEW_TASK_OUTPUT_INVALID", "review identity mismatch")
    allowed = (
        {"claim_verdicts"}
        if kind == "authority"
        else {"claim_verdicts", "record_verdicts"}
    )
    if set(verdict_payload) != allowed:
        _fail("E1_REVIEW_TASK_OUTPUT_INVALID", "verdict payload differs")
    output = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": review_kind,
        "task_id": task_id,
        "producer_thread_id": request["producer_thread_id"],
        "reviewer_thread_id": reviewer_thread_id,
        "candidate_sha256": candidate_sha256,
        "request": rt.artifact_reference(request_path, root=root),
        "verdict_payload": copy.deepcopy(dict(verdict_payload)),
    }
    output_path = _review_task_output_path(review_path)
    if output_path.exists():
        _fail("E1_REVIEW_TASK_OUTPUT_EXISTS", str(output_path))
    _write(output_path, output)
    output_reference = rt.artifact_reference(output_path, root=root)
    return {
        "task_id": task_id,
        "producer_thread_id": request["producer_thread_id"],
        "reviewer_thread_id": reviewer_thread_id,
        "output_artifact": output_reference,
        "output_sha256": rt.canonical_sha256(output),
    }


def _validate_reviewer_task_receipt(
    *,
    root: Path,
    request: Mapping[str, Any],
    reviewer_thread_id: str,
    receipt: Any,
    verdict_payload: Mapping[str, Any],
    request_reference: Mapping[str, str],
) -> None:
    required = {
        "task_id", "producer_thread_id", "reviewer_thread_id",
        "output_artifact", "output_sha256",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != required:
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", "receipt fields differ")
    if (
        not isinstance(receipt["task_id"], str)
        or not receipt["task_id"].strip()
        or receipt["producer_thread_id"] != request["producer_thread_id"]
        or receipt["reviewer_thread_id"] != reviewer_thread_id
        or not isinstance(receipt["output_sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", receipt["output_sha256"]) is None
        or receipt["output_sha256"] == "0" * 64
    ):
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", "receipt identity invalid")
    output_ref = receipt["output_artifact"]
    if not isinstance(output_ref, Mapping):
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", "output artifact missing")
    try:
        output_path = rt.verify_artifact_reference(output_ref, root=root)
    except Exception as exc:
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", str(exc))
    output = _read(output_path, "E1_REVIEW_TASK_RECEIPT_INVALID")
    expected = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "task_id": receipt["task_id"],
        "producer_thread_id": request["producer_thread_id"],
        "reviewer_thread_id": reviewer_thread_id,
        "candidate_sha256": request["candidate_sha256"],
        "request": copy.deepcopy(dict(request_reference)),
        "verdict_payload": copy.deepcopy(dict(verdict_payload)),
    }
    try:
        request_path = rt.verify_artifact_reference(expected["request"], root=root)
    except Exception as exc:
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", str(exc))
    if _read(request_path, "E1_REVIEW_TASK_RECEIPT_INVALID") != request:
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", "task request differs")
    if output != expected or receipt["output_sha256"] != rt.canonical_sha256(output):
        _fail("E1_REVIEW_TASK_RECEIPT_INVALID", "task output differs")


def _seal_semantic_review_package(
    *,
    root: Path,
    request: Mapping[str, Any],
    candidate_path: Path,
    request_path: Path,
    review_path: Path,
) -> dict[str, str]:
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    task_output_path = _review_task_output_path(review_path)
    if not task_output_path.is_file():
        _fail("E1_SEMANTIC_REVIEW_PACKAGE_INVALID", "task output missing")
    validation = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "candidate_sha256": request["candidate_sha256"],
        "verdict": "ready",
        "candidate": rt.artifact_reference(candidate_path, root=root),
        "request": rt.artifact_reference(request_path, root=root),
        "review": rt.artifact_reference(review_path, root=root),
        "review_task_output": rt.artifact_reference(task_output_path, root=root),
    }
    _write(validation_path, validation)
    manifest = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "candidate_sha256": request["candidate_sha256"],
        "artifacts": [
            rt.artifact_reference(path, root=root)
            for path in (
                candidate_path, request_path, task_output_path,
                review_path, validation_path,
            )
        ],
    }
    _write(manifest_path, manifest)
    return rt.artifact_reference(manifest_path, root=root)


def _validated_semantic_review_package(
    *,
    root: Path,
    request: Mapping[str, Any],
    candidate_path: Path,
    request_path: Path,
    review_path: Path,
) -> dict[str, str]:
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    task_output_path = _review_task_output_path(review_path)
    expected_validation = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "candidate_sha256": request["candidate_sha256"],
        "verdict": "ready",
        "candidate": rt.artifact_reference(candidate_path, root=root),
        "request": rt.artifact_reference(request_path, root=root),
        "review": rt.artifact_reference(review_path, root=root),
        "review_task_output": rt.artifact_reference(task_output_path, root=root),
    }
    if _read(validation_path, "E1_SEMANTIC_REVIEW_PACKAGE_INVALID") != expected_validation:
        _fail("E1_SEMANTIC_REVIEW_PACKAGE_INVALID", "validation differs")
    expected_manifest = {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "candidate_sha256": request["candidate_sha256"],
        "artifacts": [
            rt.artifact_reference(path, root=root)
            for path in (
                candidate_path, request_path, task_output_path,
                review_path, validation_path,
            )
        ],
    }
    if _read(manifest_path, "E1_SEMANTIC_REVIEW_PACKAGE_INVALID") != expected_manifest:
        _fail("E1_SEMANTIC_REVIEW_PACKAGE_INVALID", "manifest differs")
    return rt.artifact_reference(manifest_path, root=root)


def _review_chain_bindings(
    root: Path,
    *,
    session: Mapping[str, Any],
    through: int,
    candidate_path: Path,
    authority_review: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    result = {
        "generation_session": rt.artifact_reference(
            root / "generation-session.json", root=root
        ),
        "input_gate": copy.deepcopy(session["input_gate"]),
        "prior_phase_evidence": [
            rt.artifact_reference(
                root / "generation-evidence" / f"{index:02d}-{phase}.json",
                root=root,
            )
            for index, phase in enumerate(PHASES[:through], 1)
        ],
        "upstream_artifacts": copy.deepcopy(
            session["review_source_bindings"]["upstream_artifacts"]
        ),
        "implementation_bindings": copy.deepcopy(
            session["implementation_bindings"]
        ),
        "contract_bindings": copy.deepcopy(
            session["review_source_bindings"]["contract_bindings"]
        ),
        "candidate": rt.artifact_reference(candidate_path, root=root),
    }
    if authority_review is not None:
        result["authority_semantic_review"] = copy.deepcopy(dict(authority_review))
    return result


def _json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _upstream_object_bindings(
    *,
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for stage, document, fields in (
        (
            "S1",
            storyline,
            (
                "storylines",
                "connections",
                "environment_requirements",
                "event_requirements",
                "story_obligation_register",
            ),
        ),
        (
            "W1",
            world,
            (
                "world_facts",
                "history_pressures",
                "institutions",
                "systems",
                "resource_flows",
                "authority_flows",
                "information_flows",
                "rule_conflict_matrix",
                "storyline_support_ledger",
                "environment_demands",
            ),
        ),
    ):
        for field in fields:
            for index, item in enumerate(document.get(field, [])):
                item_id = item.get("id")
                if isinstance(item_id, str):
                    result[item_id] = {
                        "stage": stage,
                        "source_id": item_id,
                        "json_pointer": f"/{_json_pointer_token(field)}/{index}",
                        "value_sha256": rt.canonical_sha256(item),
                    }
    return result


def _expected_authority_review_request(
    root: Path,
    *,
    session: Mapping[str, Any],
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    candidate_path: Path,
) -> dict[str, Any]:
    candidate_sha256 = rt.canonical_sha256(payload)
    upstream = _upstream_object_bindings(storyline=storyline, world=world)
    phase2 = _sealed_phase_payload(
        root, sequence=2, phase="environment-architecture"
    )
    phase2_path = root / "generation-evidence" / "02-environment-architecture.json"
    for index, environment in enumerate(phase2["environments"]):
        upstream[environment["id"]] = {
            "stage": "E1",
            "source_id": environment["id"],
            "source_artifact": rt.artifact_reference(phase2_path, root=root),
            "json_pointer": f"/payload/environments/{index}",
            "value_sha256": rt.canonical_sha256(environment),
        }
    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()

    def append_claim(
        claim_id: str,
        *,
        candidate_pointer: str,
        candidate_value: Mapping[str, Any],
        source_ids: Sequence[str],
        claim_kind: str,
    ) -> None:
        if claim_id in claim_ids:
            _fail("E1_AUTHORITY_REVIEW_COVERAGE_MISMATCH", claim_id)
        bindings = [upstream[item] for item in source_ids if item in upstream]
        if not bindings:
            _fail("E1_AUTHORITY_REVIEW_SOURCE_UNBOUND", claim_id)
        claim_ids.add(claim_id)
        claims.append(
            {
                "id": claim_id,
                "claim_kind": claim_kind,
                "candidate_pointer": candidate_pointer,
                "candidate_value_sha256": rt.canonical_sha256(candidate_value),
                "source_bindings": bindings,
            }
        )

    for field in (
        "capability_fact_registry",
        "capability_step_registry",
        "actor_authority_bindings",
    ):
        for index, item in enumerate(payload[field]):
            if field == "actor_authority_bindings":
                claim_id = item["semantic_review_claim_id"]
                source_ids = item["world_authority_source_ids"]
                claim_kind = "actor_authority"
            elif field == "capability_fact_registry":
                claim_id = "CLAIM-E1-FACT-" + rt.canonical_sha256(
                    [item["id"], item["source_anchor"]]
                )[:20]
                anchor = item["source_anchor"]
                source_ids = (
                    [anchor["storyline_id"]]
                    if anchor["source_kind"] == "s1_story_state"
                    else [anchor["system_or_flow_id"]]
                    if anchor["source_kind"] == "w1_system_output"
                    else [anchor["environment_id"]]
                )
                claim_kind = "capability_fact_source"
            else:
                claim_id = "CLAIM-E1-STEP-" + rt.canonical_sha256(
                    [item["id"], item["source_ids"]]
                )[:20]
                source_ids = item["source_ids"]
                claim_kind = "capability_step_source"
            append_claim(
                claim_id,
                candidate_pointer=f"/{field}/{index}",
                candidate_value=item,
                source_ids=source_ids,
                claim_kind=claim_kind,
            )
    claims.sort(key=lambda item: item["id"])
    return {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": "authority-capability-semantics",
        "review_protocol": AUTHORITY_REVIEW_PROTOCOL,
        "run_id": session["run_id"],
        "session_id": session["session_id"],
        "producer_thread_id": session["thread_id"],
        "candidate_sha256": candidate_sha256,
        "bindings": _review_chain_bindings(
            root,
            session=session,
            through=2,
            candidate_path=candidate_path,
        ),
        "claims": claims,
        "review_contract": {
            "coverage": "Every generated claim must receive exactly one verdict.",
            "meaning": "Each structured capability and authority claim must be supported by every sealed upstream pointer and value hash it cites.",
            "boundary": "The review may validate interpretation; it may not add story events, outcomes, environments, or actions.",
        },
    }


def _normalize_claim_review(
    *,
    root: Path,
    request: Mapping[str, Any],
    reviewer_thread_id: str,
    review: Mapping[str, Any],
    request_reference: Mapping[str, str],
    task_verdict_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not reviewer_thread_id or reviewer_thread_id == request.get(
        "producer_thread_id"
    ):
        _fail("E1_SEMANTIC_REVIEW_THREAD_INVALID", reviewer_thread_id)
    if set(review) != {"claim_verdicts", "reviewer_task_receipt"}:
        _fail("E1_SEMANTIC_REVIEW_INVALID", "review envelope fields differ")
    receipt = review.get("reviewer_task_receipt")
    _validate_reviewer_task_receipt(
        root=root,
        request=request,
        reviewer_thread_id=reviewer_thread_id,
        receipt=receipt,
        verdict_payload=(
            task_verdict_payload
            if task_verdict_payload is not None
            else {"claim_verdicts": review.get("claim_verdicts")}
        ),
        request_reference=request_reference,
    )
    verdicts = review.get("claim_verdicts")
    if not isinstance(verdicts, list):
        _fail("E1_SEMANTIC_REVIEW_INVALID", "claim verdicts missing")
    expected_ids = [item["id"] for item in request["claims"]]
    observed: list[str] = []
    for item in verdicts:
        if not isinstance(item, Mapping) or set(item) != {
            "claim_id",
            "verdict",
            "rationale",
        }:
            _fail("E1_SEMANTIC_REVIEW_INVALID", "claim verdict malformed")
        if (
            item["verdict"] not in {"pass", "fail"}
            or not isinstance(item["rationale"], str)
            or not item["rationale"].strip()
        ):
            _fail("E1_SEMANTIC_REVIEW_INVALID", item.get("claim_id", "claim"))
        observed.append(item["claim_id"])
    if len(observed) != len(expected_ids) or set(observed) != set(expected_ids):
        _fail("E1_SEMANTIC_REVIEW_COVERAGE_MISMATCH", "claim verdicts")
    return {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "run_id": request["run_id"],
        "session_id": request["session_id"],
        "candidate_sha256": request["candidate_sha256"],
        "request": copy.deepcopy(dict(request_reference)),
        "reviewer_thread_id": reviewer_thread_id,
        "reviewer_task_receipt": copy.deepcopy(dict(receipt)),
        "claim_verdicts": copy.deepcopy(list(verdicts)),
        "verdict": (
            "pass"
            if all(item["verdict"] == "pass" for item in verdicts)
            else "fail"
        ),
    }


def start_e1_authority_semantic_review(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, _baseline, storyline, world, _controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS["zones-and-topology"]):
        _fail("E1_PHASE_PAYLOAD_INVALID", "invalid phase-3 review candidate")
    if not all(
        (root / "generation-evidence" / f"{index:02d}-{phase}.json").is_file()
        for index, phase in enumerate(PHASES[:2], 1)
    ) or (root / "generation-evidence" / "03-zones-and-topology.json").exists():
        _fail("E1_PHASE_ORDER_INVALID", "review requires sealed P1-P2 and open P3")
    _validate_phase3_definition_contract(
        root, body, storyline, world, contract_runtime
    )
    _validate_phase3_trigger_contract(root, body, storyline)
    candidate_sha256 = rt.canonical_sha256(body)
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="authority", candidate_sha256=candidate_sha256
    )
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    if review_path.exists() or validation_path.exists() or manifest_path.exists():
        _fail("E1_AUTHORITY_REVIEW_EXISTS", str(review_path))
    if candidate_path.exists() and _read(
        candidate_path, "E1_AUTHORITY_REVIEW_INVALID"
    ) != body:
        _fail("E1_AUTHORITY_REVIEW_STALE", candidate_sha256)
    if not candidate_path.exists():
        _write(candidate_path, body)
    request = _expected_authority_review_request(
        root,
        session=session,
        payload=body,
        storyline=storyline,
        world=world,
        candidate_path=candidate_path,
    )
    if request_path.exists() and _read(
        request_path, "E1_AUTHORITY_REVIEW_INVALID"
    ) != request:
        _fail("E1_AUTHORITY_REVIEW_STALE", candidate_sha256)
    if not request_path.exists():
        _write(request_path, request)
    return copy.deepcopy(request)


def submit_e1_authority_semantic_review(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    review: Mapping[str, Any],
) -> dict[str, str]:
    root = Path(workspace).resolve()
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="authority", candidate_sha256=candidate_sha256
    )
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    if review_path.exists() or validation_path.exists() or manifest_path.exists():
        _fail("E1_AUTHORITY_REVIEW_EXISTS", str(review_path))
    request = _read(request_path, "E1_AUTHORITY_REVIEW_INVALID")
    if request.get("candidate_sha256") != candidate_sha256:
        _fail("E1_AUTHORITY_REVIEW_INVALID", "candidate hash differs")
    record = _normalize_claim_review(
        root=root,
        request=request,
        reviewer_thread_id=os.environ.get("CODEX_THREAD_ID", "").strip(),
        review=review,
        request_reference=rt.artifact_reference(request_path, root=root),
    )
    _write(review_path, record)
    return _seal_semantic_review_package(
        root=root,
        request=request,
        candidate_path=candidate_path,
        request_path=request_path,
        review_path=review_path,
    )


def _validated_authority_review(
    root: Path,
    *,
    session: Mapping[str, Any],
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
) -> dict[str, str]:
    candidate_sha256 = rt.canonical_sha256(payload)
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="authority", candidate_sha256=candidate_sha256
    )
    if _read(candidate_path, "E1_AUTHORITY_REVIEW_MISSING") != payload:
        _fail("E1_AUTHORITY_REVIEW_STALE", candidate_sha256)
    expected_request = _expected_authority_review_request(
        root,
        session=session,
        payload=payload,
        storyline=storyline,
        world=world,
        candidate_path=candidate_path,
    )
    request = _read(request_path, "E1_AUTHORITY_REVIEW_MISSING")
    if request != expected_request:
        _fail("E1_AUTHORITY_REVIEW_STALE", candidate_sha256)
    record = _read(review_path, "E1_AUTHORITY_REVIEW_MISSING")
    expected_record = _normalize_claim_review(
        root=root,
        request=request,
        reviewer_thread_id=record.get("reviewer_thread_id", ""),
        review={
            "claim_verdicts": record.get("claim_verdicts"),
            "reviewer_task_receipt": record.get("reviewer_task_receipt"),
        },
        request_reference=rt.artifact_reference(request_path, root=root),
    )
    if record != expected_record:
        _fail("E1_AUTHORITY_REVIEW_INVALID", "review record differs")
    if record["verdict"] != "pass":
        _fail("E1_AUTHORITY_REVIEW_REJECTED", candidate_sha256)
    return _validated_semantic_review_package(
        root=root,
        request=request,
        candidate_path=candidate_path,
        request_path=request_path,
        review_path=review_path,
    )


def _hosting_review_paths(root: Path, candidate_sha256: str) -> tuple[Path, Path]:
    review_root = root / "hosting-semantic-reviews" / candidate_sha256
    return review_root / "request.json", review_root / "review.json"


def _source_token_text(
    source: Mapping[str, Any], *, token_kind: str, token_sha256: str
) -> str:
    candidates = (
        [source["responsibility"]]
        if token_kind == "responsibility"
        else list(source["constraints"])
    )
    matches = [
        value
        for value in candidates
        if rt.canonical_sha256(value) == token_sha256
    ]
    if len(matches) != 1:
        _fail("E1_SOURCE_MEANING_UNBOUND", source["id"])
    return matches[0]


def _expected_transition_review_request_v24(
    root: Path,
    *,
    session: Mapping[str, Any],
    payload: Mapping[str, Any],
    candidate_path: Path,
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_sha256 = rt.canonical_sha256(payload)
    phase2 = _sealed_phase_payload(
        root, sequence=2, phase="environment-architecture"
    )
    phase3_evidence = _read(
        root / "generation-evidence" / "03-zones-and-topology.json",
        "E1_EVIDENCE_MISSING",
    )
    authority_review = phase3_evidence.get("semantic_review")
    if not isinstance(authority_review, Mapping):
        _fail("E1_AUTHORITY_REVIEW_MISSING", "phase-3 review reference")

    source_registry = _upstream_object_bindings(
        storyline=storyline, world=world
    )
    artifacts_by_stage = {
        "S1": next(
            item for item in session["source_artifacts"]
            if item["path"] == "sources/S1/storyline-architecture.json"
        ),
        "W1": next(
            item for item in session["source_artifacts"]
            if item["path"] == "sources/W1/world-model.json"
        ),
    }
    for binding in source_registry.values():
        binding["source_artifact"] = {
            "stage": binding["stage"], **copy.deepcopy(
                artifacts_by_stage[binding["stage"]]
            )
        }
    s1_artifact = {"stage": "S1", **copy.deepcopy(artifacts_by_stage["S1"])}
    for index, item in enumerate(storyline["temporal_architecture"]["milestones"]):
        source_registry[item["id"]] = {
            "stage": "S1",
            "source_id": item["id"],
            "source_artifact": s1_artifact,
            "json_pointer": f"/temporal_architecture/milestones/{index}",
            "value_sha256": rt.canonical_sha256(item),
        }
    phase2_path = (
        root / "generation-evidence" / "02-environment-architecture.json"
    )
    phase2_document = _read(phase2_path, "E1_EVIDENCE_MISSING")
    phase2_ref = rt.artifact_reference(phase2_path, root=root)
    for field in ("environments", "initial_anchor_support"):
        for index, item in enumerate(phase2[field]):
            source_id = item.get("id", item.get("storyline_id"))
            source_registry.setdefault(source_id, {
                "stage": "E1",
                "source_id": source_id,
                "source_artifact": phase2_ref,
                "json_pointer": f"/payload/{field}/{index}",
                "value_sha256": rt.canonical_sha256(item),
            })

    # Initial-option demands are E1-owned source objects in their own right.
    # Ambient hosts may cite an ICD (or its IAO alias), so bind both names to
    # the exact sealed P2 support-option object instead of relying on the
    # enclosing storyline anchor or on a later P4 realization.
    initial_option_sources: dict[str, dict[str, Any]] = {}
    for anchor_index, anchor in enumerate(phase2["initial_anchor_support"]):
        for option_index, option in enumerate(anchor["support_options"]):
            option_pointer = (
                f"/payload/initial_anchor_support/{anchor_index}"
                f"/support_options/{option_index}"
            )
            resolved_option = _resolve_json_pointer(
                phase2_document, option_pointer
            )
            if (
                resolved_option != option
                or rt.canonical_sha256(resolved_option)
                != rt.canonical_sha256(option)
            ):
                _fail(
                    "E1_TRANSITION_REVIEW_SOURCE_DRIFT",
                    option.get("support_option_id", option_pointer),
                )
            option_metadata = {
                "support_option_id": option["support_option_id"],
                "capability_demand_id": option["capability_demand_id"],
                "storyline_id": anchor["storyline_id"],
                "environment_ids": tuple(
                    option["capability_descriptor"]["environment_ids"]
                ),
            }
            for source_id in (
                option["capability_demand_id"],
                option["support_option_id"],
            ):
                if source_id in source_registry or source_id in initial_option_sources:
                    _fail(
                        "E1_TRANSITION_REVIEW_SOURCE_COLLISION", source_id
                    )
                source_registry[source_id] = {
                    "stage": "E1",
                    "source_id": source_id,
                    "source_artifact": copy.deepcopy(phase2_ref),
                    "json_pointer": option_pointer,
                    "value_sha256": rt.canonical_sha256(option),
                }
                initial_option_sources[source_id] = option_metadata
    phase3_ref = rt.artifact_reference(
        root / "generation-evidence" / "03-zones-and-topology.json",
        root=root,
    )
    for field, values in phase3_evidence["payload"].items():
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values):
            if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
                continue
            source_registry.setdefault(item["id"], {
                "stage": "E1",
                "source_id": item["id"],
                "source_artifact": phase3_ref,
                "json_pointer": f"/payload/{field}/{index}",
                "value_sha256": rt.canonical_sha256(item),
            })

    # Validate every declared initial-option source before any review record is
    # assembled.  This keeps an ambient claim from borrowing a same-shaped ICD
    # from another line/environment, and rejects the ICD+IAO double-alias of a
    # single option as duplicate semantic evidence.
    for item in phase3_evidence["payload"]["ambient_context_hosts"]:
        source_ids = item["source_ids"]
        if len(source_ids) != len(set(source_ids)):
            _fail(
                "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_DUPLICATE", item["id"]
            )
        seen_options: set[str] = set()
        for source_id in source_ids:
            if not source_id.startswith(("ICD-", "IAO-")):
                continue
            option_metadata = initial_option_sources.get(source_id)
            if option_metadata is None:
                _fail(
                    "E1_TRANSITION_REVIEW_SOURCE_UNBOUND",
                    f"{item['semantic_review_claim_id']}:{source_id}",
                )
            option_id = option_metadata["support_option_id"]
            if option_id in seen_options:
                _fail(
                    "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_DUPLICATE",
                    f"{item['id']}:{option_id}",
                )
            seen_options.add(option_id)
            if option_metadata["storyline_id"] != item["storyline_id"]:
                _fail(
                    "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_INVALID",
                    f"{item['id']}:{source_id}:storyline",
                )
            if item["environment_id"] not in option_metadata["environment_ids"]:
                _fail(
                    "E1_TRANSITION_REVIEW_AMBIENT_SOURCE_INVALID",
                    f"{item['id']}:{source_id}:environment",
                )

    claims: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    seen_claims: set[str] = set()

    def add_record(
        *,
        record_id: str,
        record_kind: str,
        pointer: str,
        value: Mapping[str, Any],
        claim_ids: Sequence[str],
        source_ids: Sequence[str],
    ) -> None:
        if not claim_ids or len(set(claim_ids)) != len(claim_ids):
            _fail("E1_TRANSITION_REVIEW_COVERAGE_MISMATCH", record_id)
        for claim_id in claim_ids:
            if claim_id in seen_claims:
                _fail("E1_TRANSITION_REVIEW_CLAIM_REUSED", claim_id)
            seen_claims.add(claim_id)
            missing_sources = sorted(set(source_ids) - set(source_registry))
            if missing_sources:
                _fail(
                    "E1_TRANSITION_REVIEW_SOURCE_UNBOUND",
                    f"{claim_id}:{','.join(missing_sources)}",
                )
            claims.append(
                {
                    "id": claim_id,
                    "record_id": record_id,
                    "record_kind": record_kind,
                    "candidate_pointer": pointer,
                    "candidate_value_sha256": rt.canonical_sha256(value),
                    "source_bindings": [
                        copy.deepcopy(source_registry[item])
                        for item in sorted(set(source_ids))
                    ],
                }
            )
        records.append(
            {
                "id": record_id,
                "record_kind": record_kind,
                "candidate_pointer": pointer,
                "candidate_value_sha256": rt.canonical_sha256(value),
                "claim_ids": list(claim_ids),
            }
        )

    field_specs = (
        ("story_transition_support", "story_transition", "id"),
        ("connection_path_readiness", "connection", "connection_id"),
        ("obligation_capability_readiness", "obligation", "obligation_id"),
    )
    for field, kind, id_field in field_specs:
        for index, item in enumerate(payload[field]):
            source_ids: list[str] = []
            if field == "story_transition_support":
                source_ids = [
                    *item["event_requirement_ids"],
                    *[
                        source_id
                        for claim in item["support_claims"]
                        for source_id in claim["source_ids"]
                    ],
                ]
            elif field == "connection_path_readiness":
                source_ids = [item["connection_id"]]
            else:
                source_ids = [item["obligation_id"]]
            add_record(
                record_id=item[id_field],
                record_kind=kind,
                pointer=f"/{field}/{index}",
                value=item,
                claim_ids=item["semantic_review_claim_ids"],
                source_ids=source_ids,
            )

    for index, item in enumerate(payload["milestone_capability_readiness"]):
        claim_id = "CLAIM-E1-MS-" + rt.canonical_sha256(
            [item["milestone_id"], item]
        )[:20]
        add_record(
            record_id=item["milestone_id"],
            record_kind="milestone",
            pointer=f"/milestone_capability_readiness/{index}",
            value=item,
            claim_ids=[claim_id],
            source_ids=[item["milestone_id"], *item["storyline_ids"]],
        )

    for index, item in enumerate(
        phase3_evidence["payload"]["capability_occurrence_requirements"]
    ):
        add_record(
            record_id=item["id"],
            record_kind="occurrence_requirement",
            pointer=f"/capability_occurrence_requirements/{index}",
            value=item,
            claim_ids=[item["semantic_review_claim_id"]],
            source_ids=item["source_ids"],
        )
    for index, item in enumerate(phase3_evidence["payload"]["ambient_context_hosts"]):
        add_record(
            record_id=item["id"],
            record_kind="ambient_context_host",
            pointer=f"/ambient_context_hosts/{index}",
            value=item,
            claim_ids=[item["semantic_review_claim_id"]],
            source_ids=item["source_ids"],
        )

    options = {
        option["support_option_id"]: option
        for anchor in phase2["initial_anchor_support"]
        for option in anchor["support_options"]
    }
    for index, item in enumerate(payload["initial_anchor_option_realization_ledger"]):
        option = options.get(item["support_option_id"])
        if option is None or item["semantic_review_claim_id"] != option[
            "semantic_review_claim_id"
        ]:
            _fail("E1_INITIAL_OPTION_REALIZATION_INVALID", item["id"])
        add_record(
            record_id=item["id"],
            record_kind="initial_anchor_option",
            pointer=f"/initial_anchor_option_realization_ledger/{index}",
            value=item,
            claim_ids=[option["semantic_review_claim_id"]],
            source_ids=option["source_ids"],
        )
    claims.sort(key=lambda item: item["id"])
    records.sort(key=lambda item: (item["record_kind"], item["id"]))
    return {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": "transition-support-semantics",
        "review_protocol": HOSTING_REVIEW_PROTOCOL,
        "run_id": session["run_id"],
        "session_id": session["session_id"],
        "producer_thread_id": session["thread_id"],
        "candidate_sha256": candidate_sha256,
        "bindings": _review_chain_bindings(
            root,
            session=session,
            through=3,
            candidate_path=candidate_path,
            authority_review=authority_review,
        ),
        "claims": claims,
        "records": records,
        "review_contract": {
            "claim_verdicts": "Every transition, connection, milestone, obligation, occurrence, ambient-host, and sealed initial-option claim must be reviewed exactly once.",
            "record_checks": list(_TRANSITION_RECORD_REVIEW_CHECKS),
            "acceptance": "All claim verdicts and all record checks pass; no record may claim that a story outcome already occurred.",
        },
    }


def _expected_hosting_review_request(
    root: Path,
    *,
    session: Mapping[str, Any],
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_sha256 = rt.canonical_sha256(payload)
    if session.get("authority_review_protocol") == AUTHORITY_REVIEW_PROTOCOL:
        candidate_path, _request_path, _review_path = _semantic_review_paths(
            root, kind="transition", candidate_sha256=candidate_sha256
        )
        return _expected_transition_review_request_v24(
            root,
            session=session,
            payload=payload,
            candidate_path=candidate_path,
            storyline=storyline,
            world=world,
        )
    environments = {
        item["id"]: item
        for item in _sealed_phase_payload(
            root, sequence=2, phase="environment-architecture"
        )["environments"]
    }
    sources = {
        item["id"]: item
        for item in [
            *storyline["environment_requirements"],
            *world["environment_demands"],
        ]
    }
    claims: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for record in payload["storyline_hosting_ledger"]:
        source_binding_by_id = {
            item["source_id"]: item for item in record["evidence"]["source_bindings"]
        }
        record_claim_ids: list[str] = []
        pointer_claims: dict[str, list[str]] = {}
        storyline_ids = {
            item["storyline_id"] for item in source_binding_by_id.values()
        }
        for realization in record["evidence"]["realization_bindings"]:
            environment_id = realization["environment_id"]
            environment = environments[environment_id]
            for projection in realization["local_projections"]:
                source = sources[projection["source_id"]]
                source_text = _source_token_text(
                    source,
                    token_kind=projection["token_kind"],
                    token_sha256=projection["token_sha256"],
                )
                local_value = _resolve_hosting_projection(
                    environment, projection["environment_pointer"]
                )
                claim_id = "HSC-" + rt.canonical_sha256(
                    [
                        record["id"],
                        projection["source_id"],
                        projection["token_kind"],
                        projection["token_sha256"],
                    ]
                )[:24]
                claim = {
                    "id": claim_id,
                    "record_id": record["id"],
                    "source_id": projection["source_id"],
                    "source_kind": source_binding_by_id[projection["source_id"]][
                        "source_kind"
                    ],
                    "token_kind": projection["token_kind"],
                    "source_text": source_text,
                    "source_sha256": projection["token_sha256"],
                    "environment_id": environment_id,
                    "environment_pointer": projection["environment_pointer"],
                    "local_value": local_value,
                    "local_value_sha256": projection["projection_sha256"],
                    "author_rationale": projection["rationale"],
                }
                claims.append(claim)
                record_claim_ids.append(claim_id)
                pointer_key = f"{environment_id}{projection['environment_pointer']}"
                pointer_claims.setdefault(pointer_key, []).append(claim_id)
        records.append(
            {
                "id": record["id"],
                "source_ids": record["source_ids"],
                "storyline_ids": sorted(storyline_ids),
                "realization_ids": record["realization_ids"],
                "claim_ids": record_claim_ids,
                "pointer_claims": [
                    {"pointer": pointer, "claim_ids": claim_ids}
                    for pointer, claim_ids in sorted(pointer_claims.items())
                ],
            }
        )
    claims.sort(key=lambda item: item["id"])
    records.sort(key=lambda item: item["id"])
    phase2_path = root / "generation-evidence" / "02-environment-architecture.json"
    phase3_path = root / "generation-evidence" / "03-zones-and-topology.json"
    return {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": "storyline-hosting-semantics",
        "review_protocol": LEGACY_HOSTING_REVIEW_PROTOCOL,
        "run_id": session["run_id"],
        "session_id": session["session_id"],
        "producer_thread_id": session["thread_id"],
        "candidate_sha256": candidate_sha256,
        "input_gate": copy.deepcopy(session["input_gate"]),
        "baseline_completion": copy.deepcopy(session["baseline_completion"]),
        "upstream_completions": copy.deepcopy(session["upstream_completions"]),
        "phase2_evidence": rt.artifact_reference(phase2_path, root=root),
        "phase3_evidence": rt.artifact_reference(phase3_path, root=root),
        "claims": claims,
        "records": records,
        "review_contract": {
            "claim_verdicts": "Every claim must be reviewed against its exact source text, local value, pointer, hashes, and rationale.",
            "record_checks": list(_HOSTING_RECORD_REVIEW_CHECKS),
            "acceptance": "Every claim verdict and every record check must pass; generic dumping or incoherent pointer reuse must fail.",
        },
    }


def start_e1_hosting_semantic_review(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, storyline, world, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    if session.get("hosting_review_protocol") != HOSTING_REVIEW_PROTOCOL:
        _fail("E1_HOSTING_REVIEW_INVALID", "session has no current review protocol")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS["storyline-hosting-test"]):
        _fail("E1_PHASE_PAYLOAD_INVALID", "invalid phase-4 review candidate")
    if not all(
        (
            root
            / "generation-evidence"
            / f"{index:02d}-{phase}.json"
        ).is_file()
        for index, phase in enumerate(PHASES[:3], 1)
    ) or (
        root / "generation-evidence" / "04-storyline-hosting-test.json"
    ).exists():
        _fail("E1_PHASE_ORDER_INVALID", "review requires sealed P1-P3 and open P4")
    _validate_phase4_hosting_contract(
        root,
        body,
        baseline,
        storyline,
        world,
        controls,
        session,
        contract_runtime,
    )
    candidate_sha256 = rt.canonical_sha256(body)
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="transition", candidate_sha256=candidate_sha256
    )
    if candidate_path.exists() and _read(
        candidate_path, "E1_HOSTING_REVIEW_INVALID"
    ) != body:
        _fail("E1_HOSTING_REVIEW_STALE", candidate_sha256)
    if not candidate_path.exists():
        _write(candidate_path, body)
    request = _expected_hosting_review_request(
        root,
        session=session,
        payload=body,
        storyline=storyline,
        world=world,
    )
    if session.get("authority_review_protocol") != AUTHORITY_REVIEW_PROTOCOL:
        request_path, review_path = _hosting_review_paths(
            root, request["candidate_sha256"]
        )
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    if review_path.exists() or (
        candidate_path.exists()
        and (validation_path.exists() or manifest_path.exists())
    ):
        _fail("E1_HOSTING_REVIEW_EXISTS", str(review_path))
    if request_path.exists():
        if _read(request_path, "E1_HOSTING_REVIEW_INVALID") != request:
            _fail("E1_HOSTING_REVIEW_INVALID", "stored request differs")
    else:
        _write(request_path, request)
    return copy.deepcopy(request)


def _normalize_hosting_review(
    *,
    root: Path,
    request: Mapping[str, Any],
    reviewer_thread_id: str,
    review: Mapping[str, Any],
    request_reference: Mapping[str, str],
) -> dict[str, Any]:
    if request.get("review_kind") == "transition-support-semantics":
        if set(review) != {
            "claim_verdicts",
            "record_verdicts",
            "reviewer_task_receipt",
        }:
            _fail("E1_HOSTING_REVIEW_INVALID", "review envelope fields differ")
        base = _normalize_claim_review(
            root=root,
            request=request,
            reviewer_thread_id=reviewer_thread_id,
            review={
                "claim_verdicts": review.get("claim_verdicts"),
                "reviewer_task_receipt": review.get("reviewer_task_receipt"),
            },
            request_reference=request_reference,
            task_verdict_payload={
                "claim_verdicts": review.get("claim_verdicts"),
                "record_verdicts": review.get("record_verdicts"),
            },
        )
        record_ids = [item["id"] for item in request["records"]]
        verdicts = review.get("record_verdicts")
        if not isinstance(verdicts, list):
            _fail("E1_HOSTING_REVIEW_INVALID", "record verdicts missing")
        observed: list[str] = []
        for item in verdicts:
            if (
                not isinstance(item, Mapping)
                or set(item) != {"record_id", "checks", "rationale"}
                or not isinstance(item.get("checks"), Mapping)
                or set(item["checks"]) != set(_TRANSITION_RECORD_REVIEW_CHECKS)
                or any(
                    value not in {"pass", "fail"}
                    for value in item["checks"].values()
                )
                or not isinstance(item.get("rationale"), str)
                or not item["rationale"].strip()
            ):
                _fail("E1_HOSTING_REVIEW_INVALID", "record verdict malformed")
            observed.append(item["record_id"])
        if len(observed) != len(record_ids) or set(observed) != set(record_ids):
            _fail("E1_HOSTING_REVIEW_COVERAGE_MISMATCH", "record verdicts")
        base["record_verdicts"] = copy.deepcopy(list(verdicts))
        if any(
            value != "pass"
            for item in verdicts
            for value in item["checks"].values()
        ):
            base["verdict"] = "fail"
        return base
    if (
        not reviewer_thread_id
        or reviewer_thread_id == request.get("producer_thread_id")
    ):
        _fail("E1_HOSTING_REVIEW_THREAD_INVALID", reviewer_thread_id)
    if set(review) != {"claim_verdicts", "record_verdicts"}:
        _fail("E1_HOSTING_REVIEW_INVALID", "review envelope fields differ")
    claim_ids = [item["id"] for item in request["claims"]]
    claim_verdicts = review.get("claim_verdicts")
    if not isinstance(claim_verdicts, list):
        _fail("E1_HOSTING_REVIEW_INVALID", "claim verdicts missing")
    observed_claim_ids: list[str] = []
    for item in claim_verdicts:
        if not isinstance(item, Mapping) or set(item) != {
            "claim_id",
            "verdict",
            "rationale",
        }:
            _fail("E1_HOSTING_REVIEW_INVALID", "claim verdict malformed")
        if (
            item["verdict"] not in {"pass", "fail"}
            or not isinstance(item["rationale"], str)
            or not item["rationale"].strip()
        ):
            _fail("E1_HOSTING_REVIEW_INVALID", item.get("claim_id", "claim"))
        observed_claim_ids.append(item["claim_id"])
    if (
        set(observed_claim_ids) != set(claim_ids)
        or len(observed_claim_ids) != len(claim_ids)
    ):
        _fail("E1_HOSTING_REVIEW_COVERAGE_MISMATCH", "claim verdicts")

    record_ids = [item["id"] for item in request["records"]]
    record_verdicts = review.get("record_verdicts")
    if not isinstance(record_verdicts, list):
        _fail("E1_HOSTING_REVIEW_INVALID", "record verdicts missing")
    observed_record_ids: list[str] = []
    for item in record_verdicts:
        if not isinstance(item, Mapping) or set(item) != {
            "record_id",
            "checks",
            "rationale",
        } or not isinstance(item.get("checks"), Mapping):
            _fail("E1_HOSTING_REVIEW_INVALID", "record verdict malformed")
        if (
            set(item["checks"]) != set(_HOSTING_RECORD_REVIEW_CHECKS)
            or any(value not in {"pass", "fail"} for value in item["checks"].values())
            or not isinstance(item["rationale"], str)
            or not item["rationale"].strip()
        ):
            _fail("E1_HOSTING_REVIEW_INVALID", item.get("record_id", "record"))
        observed_record_ids.append(item["record_id"])
    if (
        set(observed_record_ids) != set(record_ids)
        or len(observed_record_ids) != len(record_ids)
    ):
        _fail("E1_HOSTING_REVIEW_COVERAGE_MISMATCH", "record verdicts")
    overall = "pass"
    if any(item["verdict"] != "pass" for item in claim_verdicts) or any(
        value != "pass"
        for item in record_verdicts
        for value in item["checks"].values()
    ):
        overall = "fail"
    return {
        "schema_version": "1.0",
        "stage": "E1",
        "review_kind": "storyline-hosting-semantics",
        "review_protocol": request["review_protocol"],
        "run_id": request["run_id"],
        "session_id": request["session_id"],
        "candidate_sha256": request["candidate_sha256"],
        "request": copy.deepcopy(dict(request_reference)),
        "reviewer_thread_id": reviewer_thread_id,
        "claim_verdicts": copy.deepcopy(list(claim_verdicts)),
        "record_verdicts": copy.deepcopy(list(record_verdicts)),
        "verdict": overall,
    }


def submit_e1_hosting_semantic_review(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    review: Mapping[str, Any],
) -> dict[str, str]:
    root = Path(workspace).resolve()
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="transition", candidate_sha256=candidate_sha256
    )
    if not candidate_path.exists():
        # Historical review packages predate sealed candidate artifacts.
        request_path, review_path = _hosting_review_paths(root, candidate_sha256)
    validation_path, manifest_path = _semantic_review_package_paths(review_path)
    if review_path.exists() or (
        candidate_path.exists()
        and (validation_path.exists() or manifest_path.exists())
    ):
        _fail("E1_HOSTING_REVIEW_EXISTS", str(review_path))
    request = _read(request_path, "E1_HOSTING_REVIEW_INVALID")
    if request.get("candidate_sha256") != candidate_sha256:
        _fail("E1_HOSTING_REVIEW_INVALID", "candidate hash differs")
    reviewer_thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    record = _normalize_hosting_review(
        root=root,
        request=request,
        reviewer_thread_id=reviewer_thread_id,
        review=review,
        request_reference=rt.artifact_reference(request_path, root=root),
    )
    _write(review_path, record)
    if candidate_path.exists():
        return _seal_semantic_review_package(
            root=root,
            request=request,
            candidate_path=candidate_path,
            request_path=request_path,
            review_path=review_path,
        )
    return rt.artifact_reference(review_path, root=root)


def _validated_hosting_review(
    root: Path,
    *,
    session: Mapping[str, Any],
    payload: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
) -> dict[str, str]:
    candidate_sha256 = rt.canonical_sha256(payload)
    candidate_path, request_path, review_path = _semantic_review_paths(
        root, kind="transition", candidate_sha256=candidate_sha256
    )
    current_review = session.get("authority_review_protocol") == AUTHORITY_REVIEW_PROTOCOL
    if current_review:
        if _read(candidate_path, "E1_HOSTING_REVIEW_MISSING") != payload:
            _fail("E1_HOSTING_REVIEW_STALE", candidate_sha256)
    expected_request = _expected_hosting_review_request(
        root,
        session=session,
        payload=payload,
        storyline=storyline,
        world=world,
    )
    if not current_review:
        request_path, review_path = _hosting_review_paths(
            root, expected_request["candidate_sha256"]
        )
    request = _read(request_path, "E1_HOSTING_REVIEW_MISSING")
    if request != expected_request:
        _fail("E1_HOSTING_REVIEW_STALE", expected_request["candidate_sha256"])
    review_record = _read(review_path, "E1_HOSTING_REVIEW_MISSING")
    review_body = {
        "claim_verdicts": review_record.get("claim_verdicts"),
        "record_verdicts": review_record.get("record_verdicts"),
    }
    if current_review:
        review_body["reviewer_task_receipt"] = review_record.get(
            "reviewer_task_receipt"
        )
    expected_review = _normalize_hosting_review(
        root=root,
        request=request,
        reviewer_thread_id=review_record.get("reviewer_thread_id", ""),
        review=review_body,
        request_reference=rt.artifact_reference(request_path, root=root),
    )
    if review_record != expected_review:
        _fail("E1_HOSTING_REVIEW_INVALID", "review record differs")
    if review_record["verdict"] != "pass":
        _fail("E1_HOSTING_REVIEW_REJECTED", expected_request["candidate_sha256"])
    if current_review:
        return _validated_semantic_review_package(
            root=root,
            request=request,
            candidate_path=candidate_path,
            request_path=request_path,
            review_path=review_path,
        )
    return rt.artifact_reference(review_path, root=root)


def submit_e1_phase(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    input_gate: Any,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, storyline, world, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
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
        _fail("E1_PHASE_ORDER_INVALID", "all phases already sealed")
    if phase not in PHASES or phase != PHASES[len(completed)]:
        _fail("E1_PHASE_ORDER_INVALID", f"next phase is {PHASES[len(completed)]}")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS[phase]):
        _fail(
            "E1_PHASE_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(PHASE_FIELDS[phase])}",
        )
    if phase == "environment-demand-scan":
        _validate_phase1_projection_contract(
            body,
            storyline,
            world,
            source_artifacts=session["source_artifacts"],
        )
    if phase == "environment-architecture":
        _validate_phase2_architecture_contract(
            root, body, storyline, world, contract_runtime
        )
    if phase == "zones-and-topology":
        _validate_phase3_definition_contract(
            root, body, storyline, world, contract_runtime
        )
        _validate_phase3_trigger_contract(root, body, storyline)
    authority_review_reference = None
    if phase == "zones-and-topology":
        authority_review_reference = _validated_authority_review(
            root,
            session=session,
            payload=body,
            storyline=storyline,
            world=world,
        )
    hosting_review_reference = None
    if phase == "storyline-hosting-test":
        _validate_phase4_hosting_contract(
            root,
            body,
            baseline,
            storyline,
            world,
            controls,
            session,
            contract_runtime,
        )
        hosting_review_reference = _validated_hosting_review(
            root,
            session=session,
            payload=body,
            storyline=storyline,
            world=world,
        )
    if phase == "final-environment-model":
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("E1_PHASE_PAYLOAD_INVALID", "final model missing")
        _require_generation_schema(model)
        _validate_phase_chain(
            root / "generation-evidence",
            session=session,
            model=model,
            storyline=storyline,
            world=world,
            through=4,
        )
        _validate_model(
            model,
            baseline,
            storyline,
            world,
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
                "storyline_environment_requirement_bindings",
                "event_requirement_bindings",
                "world_rule_bindings",
                "environment_demand_bindings",
                "implementation_bindings",
                "review_source_bindings",
                "authority_review_protocol",
                "hosting_review_protocol",
            )
        },
        "stage": "E1",
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "payload": body,
        "payload_sha256": rt.canonical_sha256(body),
    }
    if authority_review_reference is not None:
        evidence["semantic_review"] = authority_review_reference
    if hosting_review_reference is not None:
        evidence["semantic_review"] = hosting_review_reference
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
    storyline: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    through: int | None = None,
) -> list[Path]:
    paths: list[Path] = []
    previous = None
    shared = [
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
    ]
    model_version = model.get("schema_version")
    semantic_profile = _semantic_profile(model_version)
    current_hosting_review_protocol = (
        semantic_profile == "capability-readiness"
        and
        session.get("hosting_review_protocol") == HOSTING_REVIEW_PROTOCOL
    )
    legacy_hosting_review_protocol = (
        semantic_profile in {
            "legacy-structured-hosting-exact-once",
            "legacy-structured-hosting-multi-affordance",
        }
        and
        session.get("hosting_review_protocol") == LEGACY_HOSTING_REVIEW_PROTOCOL
    )
    hosting_review_protocol = (
        current_hosting_review_protocol or legacy_hosting_review_protocol
    )
    current_review_protocol = (
        current_hosting_review_protocol
        and session.get("authority_review_protocol") == AUTHORITY_REVIEW_PROTOCOL
    )
    if current_review_protocol:
        shared.extend(
            (
                "implementation_bindings",
                "review_source_bindings",
                "authority_review_protocol",
                "hosting_review_protocol",
            )
        )
    elif hosting_review_protocol:
        # Structured historical E1 2.2/2.3 evidence has only the original
        # hosting review protocol and must never inherit 2.4 phase semantics.
        shared.extend(("implementation_bindings", "hosting_review_protocol"))
    phase_sequence = PHASES if through is None else PHASES[:through]
    for index, phase in enumerate(phase_sequence, 1):
        path = evidence_root / f"{index:02d}-{phase}.json"
        evidence = _read(path, "E1_EVIDENCE_MISSING")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("E1_EVIDENCE_INVALID", phase)
        expected_fields = _phase_fields_for_version(model_version, phase)
        expected = {
            "schema_version": "2.0",
            **{key: copy.deepcopy(session[key]) for key in shared},
            "stage": "E1",
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        if phase == "zones-and-topology" and current_review_protocol:
            if storyline is None or world is None:
                _fail("E1_AUTHORITY_REVIEW_INVALID", "review sources unavailable")
            expected["semantic_review"] = _validated_authority_review(
                evidence_root.parent,
                session=session,
                payload=payload,
                storyline=storyline,
                world=world,
            )
        if phase == "storyline-hosting-test" and hosting_review_protocol:
            if storyline is None or world is None:
                _fail("E1_HOSTING_REVIEW_INVALID", "review sources unavailable")
            expected["semantic_review"] = _validated_hosting_review(
                evidence_root.parent,
                session=session,
                payload=payload,
                storyline=storyline,
                world=world,
            )
        if evidence != expected or set(payload) != set(expected_fields):
            _fail("E1_EVIDENCE_INVALID", phase)
        if phase == "final-environment-model":
            if payload["model"] != model:
                _fail("E1_EVIDENCE_MODEL_MISMATCH", phase)
        else:
            for field in expected_fields:
                if field not in model:
                    _fail("E1_EVIDENCE_MODEL_MISMATCH", f"{phase}.{field}")
                if payload[field] != model[field]:
                    _fail("E1_EVIDENCE_MODEL_MISMATCH", f"{phase}.{field}")
        previous = rt.sha256_file(path)
        paths.append(path)
    if semantic_profile == "capability-readiness" and len(
        phase_sequence
    ) >= 3:
        _validate_v24_e1_source_anchors(model, root=evidence_root.parent)
    return paths


def _validation(
    run_id: str,
    *,
    model_schema_version: str = CURRENT_MODEL_SCHEMA_VERSION,
) -> dict[str, Any]:
    checks = [
        "schema",
        "B0/S1/W1/gate-lineage",
        "environment-demand-exact-projection",
        "hosting-exact-cover",
        "zone-and-topology-closure",
        "access-resource-information-closure",
        "affordance-and-transition-closure",
    ]
    # A trusted legacy package is replayed against the semantics and the
    # validation receipt shape that were sealed at its release.  Requiring a
    # current-2.4 check list from a byte-identical historical package would be
    # an implicit rewrite, while accepting an arbitrary stored receipt would
    # weaken the exact package identity branch.
    if model_schema_version == CURRENT_MODEL_SCHEMA_VERSION:
        checks.extend(
            [
                "s1-universe-digest-exactness",
                "initial-anchor-option-exact-realization",
                "capability-fact-step-authority-dag",
                "occurrence-cardinality-and-sharing",
                "transition-connection-milestone-obligation-readiness",
                "authority-semantic-review-package",
                "transition-support-semantic-review-package",
            ]
        )
    checks.extend(
        [
            "world-rule-consistency",
            "downstream-boundary",
            "completion-binding",
        ]
    )
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "E1",
        "verdict": "ready",
        "checks": checks,
        "errors": [],
    }


def _check_package_boundary(root: Path) -> None:
    allowed_evidence = {
        f"generation-evidence/{index:02d}-{phase}.json"
        for index, phase in enumerate(PHASES, 1)
    }
    execution = _read(root / "execution-record.json", "E1_EXECUTION_INVALID")
    allowed_implementation = {
        f"implementation/{item['identity']}"
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping) and isinstance(item.get("identity"), str)
    }
    allowed_reviews: set[str] = set()
    phase3_path = root / "generation-evidence" / "03-zones-and-topology.json"
    if phase3_path.is_file():
        phase3 = _read(phase3_path, "E1_EVIDENCE_INVALID")
        candidate_sha256 = phase3.get("payload_sha256")
        if isinstance(candidate_sha256, str) and re.fullmatch(
            r"[a-f0-9]{64}", candidate_sha256
        ):
            allowed_reviews.update(
                {
                    f"authority-semantic-reviews/{candidate_sha256}/candidate.json",
                    f"authority-semantic-reviews/{candidate_sha256}/request.json",
                    f"authority-semantic-reviews/{candidate_sha256}/review.json",
                    f"authority-semantic-reviews/{candidate_sha256}/review-task-output.json",
                    f"authority-semantic-reviews/{candidate_sha256}/validation.json",
                    f"authority-semantic-reviews/{candidate_sha256}/manifest.json",
                }
            )
    phase4_path = root / "generation-evidence" / "04-storyline-hosting-test.json"
    if phase4_path.is_file():
        phase4 = _read(phase4_path, "E1_EVIDENCE_INVALID")
        candidate_sha256 = phase4.get("payload_sha256")
        if isinstance(candidate_sha256, str) and re.fullmatch(
            r"[a-f0-9]{64}", candidate_sha256
        ):
            allowed_reviews.update(
                {
                    f"hosting-semantic-reviews/{candidate_sha256}/candidate.json",
                    f"hosting-semantic-reviews/{candidate_sha256}/request.json",
                    f"hosting-semantic-reviews/{candidate_sha256}/review.json",
                    f"hosting-semantic-reviews/{candidate_sha256}/review-task-output.json",
                    f"hosting-semantic-reviews/{candidate_sha256}/validation.json",
                    f"hosting-semantic-reviews/{candidate_sha256}/manifest.json",
                }
            )
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ALLOWED_ROOT_FILES:
            continue
        if relative in allowed_evidence or relative in allowed_implementation:
            continue
        if relative in allowed_reviews:
            continue
        if any(relative.startswith(prefix) for prefix in _ALLOWED_SOURCE_PREFIXES):
            continue
        _fail("E1_BOUNDARY_VIOLATION", relative)


def validate_e1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_package_boundary(root)
    model = _read(root / "environment-system.json", "E1_MODEL_MISSING")
    manifest = _read(root / "package-manifest.json", "E1_MANIFEST_INVALID")
    stored = _read(root / "validation.json", "E1_VALIDATION_MISSING")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("E1_MANIFEST_INVALID", str(error))
    current_model = _is_current_model(model)
    execution = _read(root / "execution-record.json", "E1_EXECUTION_INVALID")
    session = _read(root / "generation-session.json", "E1_SESSION_INVALID")
    catalog = {
        item["identity"]: item["artifact"]
        for item in execution.get("implementation_catalog", [])
    }
    identity_mode = "pre-versioned-model"
    if current_model:
        try:
            identity_mode, catalog = stage_identity.validate_stage_catalog(
                stage="E1",
                records=execution.get("implementation_catalog"),
                package_root=root,
                current_paths=_implementation_paths(),
                verify_artifact_reference=rt.verify_artifact_reference,
                sha256_file=rt.sha256_file,
            )
        except stage_identity.StageImplementationIdentityError as error:
            _fail("E1_IMPLEMENTATION_STALE", str(error))
    if not current_model:
        for identity, reference in catalog.items():
            try:
                rt.verify_artifact_reference(reference, root=root)
            except Exception as error:
                _fail("E1_LEGACY_PROVENANCE_UNTRUSTED", f"{identity}: {error}")
        _validate_legacy_package_provenance(model, catalog)
        _validate_legacy_package_identity(root, model)
    b0 = root / "sources" / "B0"
    s1 = root / "sources" / "S1"
    w1 = root / "sources" / "W1"
    if current_model:
        try:
            rt.validate_baseline_package(b0, runtime=contract_runtime)
            s1_runtime.validate_s1_package(s1, runtime=contract_runtime)
            w1_runtime.validate_w1_package(w1, runtime=contract_runtime)
        except Exception as error:
            _fail("E1_UPSTREAM_INVALID", str(error))
    else:
        _validate_legacy_upstream_snapshot(
            b0,
            stage="B0",
            canonical_name="author-control-baseline.json",
            runtime=contract_runtime,
        )
        _validate_legacy_upstream_snapshot(
            s1,
            stage="S1",
            canonical_name="storyline-architecture.json",
            runtime=contract_runtime,
        )
        _validate_legacy_upstream_snapshot(
            w1,
            stage="W1",
            canonical_name="world-model.json",
            runtime=contract_runtime,
        )
    baseline = _read(b0 / "author-control-baseline.json", "E1_B0_INVALID")
    storyline = _read(s1 / "storyline-architecture.json", "E1_S1_INVALID")
    world = _read(w1 / "world-model.json", "E1_W1_INVALID")
    controls = _controls(b0, baseline)
    gate = _read(root / "input-gate.json", "E1_GATE_MISSING")
    try:
        contract_runtime.validate(gate, "input-gate.schema.json")
    except Exception as error:
        _fail("E1_GATE_INVALID", str(error))
    if rt.canonical_sha256(gate) != rt.sha256_file(root / "input-gate.json"):
        _fail("E1_GATE_INVALID", "stored gate is not canonical")
    gate_ref = {
        "path": model["input_gate"]["path"],
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    if not gate_ref["path"].endswith("/input-gate.json"):
        _fail("E1_GATE_REFERENCE_MISMATCH", "gate path not package-qualified")
    sealed_b0 = gate.get("baseline_completion")
    sealed_upstreams = gate.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 2
        or any(not isinstance(item, Mapping) for item in sealed_upstreams)
    ):
        _fail("E1_GATE_INVALID", "gate does not select exactly B0, S1, and W1")
    b0_ref = _sealed_upstream_reference(
        b0,
        sealed_b0,
        stage="B0",
        run_id=model["run_id"],
        previous_stage_completions=[],
        runtime=contract_runtime,
    )
    s1_ref = _sealed_upstream_reference(
        s1,
        sealed_upstreams[0],
        stage="S1",
        run_id=model["run_id"],
        previous_stage_completions=[],
        runtime=contract_runtime,
    )
    w1_ref = _sealed_upstream_reference(
        w1,
        sealed_upstreams[1],
        stage="W1",
        run_id=model["run_id"],
        previous_stage_completions=[s1_ref],
        runtime=contract_runtime,
    )
    _require_embedded_completion(
        s1 / "sources" / "B0" / "stage-completion.json",
        b0_ref,
        code="E1_UPSTREAM_LINEAGE_MISMATCH",
    )
    _require_embedded_completion(
        w1 / "sources" / "B0" / "stage-completion.json",
        b0_ref,
        code="E1_UPSTREAM_LINEAGE_MISMATCH",
    )
    _require_embedded_completion(
        w1 / "sources" / "S1" / "stage-completion.json",
        s1_ref,
        code="E1_UPSTREAM_LINEAGE_MISMATCH",
    )
    if (
        gate.get("target_stage") != "E1"
        or gate.get("run_id") != model["run_id"]
        or gate.get("baseline_completion") != b0_ref
        or gate.get("upstream_completions") != [s1_ref, w1_ref]
    ):
        _fail("E1_GATE_INVALID", "stored E1 topology is invalid")
    expected_sources = _source_artifacts(b0, s1, w1)
    _validate_model(
        model,
        baseline,
        storyline,
        world,
        controls,
        contract_runtime,
        expected_gate=gate_ref,
        expected_sources=expected_sources,
    )
    if manifest["artifact_roles"]["canonical"] != rt.artifact_reference(
        root / "environment-system.json", root=root
    ):
        _fail("E1_MANIFEST_INVALID", "canonical role is stale")
    if (
        execution.get("input_gate") != gate_ref
        or execution.get("baseline_completion") != b0_ref
        or execution.get("upstream_completions") != [s1_ref, w1_ref]
        or execution.get("output_sha256") != rt.canonical_sha256(model)
    ):
        _fail("E1_EXECUTION_INVALID", "execution lineage is stale")
    thread = session.get("thread_id")
    if not isinstance(thread, str) or not thread.strip():
        _fail("E1_SESSION_INVALID", "thread is missing")
    expected_session = {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "E1",
        "session_id": _session_id(thread, gate_ref, b0_ref, s1_ref, w1_ref),
        "thread_id": thread,
        "input_gate": gate_ref,
        "state_before": gate.get("run_state"),
        "baseline_completion": b0_ref,
        "upstream_completions": [s1_ref, w1_ref],
        "source_artifacts": expected_sources,
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _object_bindings(
            storyline["storylines"], extra="type"
        ),
        "storyline_environment_requirement_bindings": _object_bindings(
            storyline["environment_requirements"], extra="target_stage"
        ),
        "event_requirement_bindings": _object_bindings(
            storyline["event_requirements"], extra="target_stage"
        ),
        "world_rule_bindings": _object_bindings(world["world_facts"], extra="kind"),
        "environment_demand_bindings": _object_bindings(
            world["environment_demands"], extra="target_stage"
        ),
        "phases": list(PHASES),
    }
    structured_legacy = model.get("schema_version") in {"2.2", "2.3"}
    if current_model:
        expected_session.update(
            {
                "implementation_bindings": (
                    _implementation_bindings()
                    if identity_mode
                    == stage_identity.STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION
                    else [
                        {"identity": identity, "sha256": reference["sha256"]}
                        for identity, reference in sorted(catalog.items())
                    ]
                ),
                "review_source_bindings": _review_source_bindings(s1, w1),
                "authority_review_protocol": AUTHORITY_REVIEW_PROTOCOL,
                "hosting_review_protocol": HOSTING_REVIEW_PROTOCOL,
            }
        )
    elif structured_legacy:
        expected_session.update(
            {
                "implementation_bindings": [
                    {
                        "identity": identity,
                        "sha256": reference["sha256"],
                    }
                    for identity, reference in sorted(catalog.items())
                ],
                "hosting_review_protocol": LEGACY_HOSTING_REVIEW_PROTOCOL,
            }
        )
    if session != expected_session:
        _fail("E1_SESSION_INVALID", "session differs from current inputs")
    if execution.get("session_id") != session["session_id"]:
        _fail("E1_SESSION_INVALID", "execution session differs")
    evidence_paths = _validate_phase_chain(
        root / "generation-evidence",
        session=session,
        model=model,
        storyline=storyline if current_model or structured_legacy else None,
        world=world if current_model or structured_legacy else None,
    )
    evidence_index = _read(
        root / "generation-evidence-index.json", "E1_EVIDENCE_INVALID"
    )
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "E1",
        "session_id": session["session_id"],
        "phases": list(PHASES),
        "evidence": [
            rt.artifact_reference(path, root=root) for path in evidence_paths
        ],
    }:
        _fail("E1_EVIDENCE_INVALID", "evidence index is stale")
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
            "E1_IMPLEMENTATION_STALE",
            "implementation files, catalog, execution, and manifest differ",
        )
    if not current_model:
        _validate_legacy_package_provenance(model, catalog)
    if require_completion:
        completion = _read(
            root / "stage-completion.json", "E1_COMPLETION_MISSING"
        )
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("E1_COMPLETION_INVALID", str(error))
        manifest_ref = completion.get("manifest")
        manifest_path = (
            manifest_ref.get("path") if isinstance(manifest_ref, Mapping) else ""
        )
        prefix = PurePosixPath(manifest_path).parent.as_posix()
        if (
            not (prefix == "E1" or prefix.startswith("E1/"))
            or completion.get("run_id") != model["run_id"]
            or completion.get("stage") != "E1"
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
            or completion.get("previous_stage_completions") != [s1_ref, w1_ref]
            or completion.get("return_binding") != gate.get("return_binding")
        ):
            _fail("E1_COMPLETION_BINDING_MISMATCH", "completion lineage is stale")
    expected_validation = _validation(
        model["run_id"], model_schema_version=model["schema_version"]
    )
    if stored != expected_validation:
        _fail("E1_VALIDATION_STALE", "stored validation differs")
    return expected_validation


def run_e1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controlled_workspace: str | Path,
    logical_package_path: str = "E1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> E1RunReceipt:
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("E1_OUTPUT_EXISTS", str(destination))
    if not os.environ.get("CODEX_THREAD_ID", "").strip():
        _fail("E1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    workspace = Path(controlled_workspace).resolve()
    session, baseline, storyline, world, controls = _validated_session(
        workspace,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    final = _read(
        workspace
        / "generation-evidence"
        / f"{len(PHASES):02d}-{PHASES[-1]}.json",
        "E1_EVIDENCE_MISSING",
    )
    payload = final.get("payload")
    if not isinstance(payload, Mapping) or not isinstance(
        payload.get("model"), Mapping
    ):
        _fail("E1_EVIDENCE_INVALID", "final model missing")
    model = copy.deepcopy(dict(payload["model"]))
    _require_generation_schema(model)
    _validate_phase_chain(
        workspace / "generation-evidence",
        session=session,
        model=model,
        storyline=storyline,
        world=world,
    )
    _validate_model(
        model,
        baseline,
        storyline,
        world,
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
        ):
            shutil.copytree(source, staging / "sources" / stage)
        _write(staging / "input-gate.json", input_gate.data)
        if _source_artifacts(
            staging / "sources" / "B0",
            staging / "sources" / "S1",
            staging / "sources" / "W1",
        ) != session["source_artifacts"]:
            _fail("E1_SOURCE_ARTIFACT_MISMATCH", "staged inputs changed")
        _write(staging / "environment-system.json", model)
        phase3_payload = {
            field: model[field] for field in PHASE_FIELDS["zones-and-topology"]
        }
        authority_candidate_sha256 = rt.canonical_sha256(phase3_payload)
        authority_source_root = (
            workspace
            / "authority-semantic-reviews"
            / authority_candidate_sha256
        )
        authority_target_root = (
            staging
            / "authority-semantic-reviews"
            / authority_candidate_sha256
        )
        authority_target_root.mkdir(parents=True)
        for name in (
            "candidate.json",
            "request.json",
            "review-task-output.json",
            "review.json",
            "validation.json",
            "manifest.json",
        ):
            shutil.copyfile(
                authority_source_root / name, authority_target_root / name
            )
        phase4_payload = {
            field: model[field]
            for field in PHASE_FIELDS["storyline-hosting-test"]
        }
        hosting_candidate_sha256 = rt.canonical_sha256(phase4_payload)
        review_source_root = (
            workspace / "hosting-semantic-reviews" / hosting_candidate_sha256
        )
        review_target_root = (
            staging / "hosting-semantic-reviews" / hosting_candidate_sha256
        )
        review_target_root.mkdir(parents=True)
        for name in (
            "candidate.json",
            "request.json",
            "review-task-output.json",
            "review.json",
            "validation.json",
            "manifest.json",
        ):
            shutil.copyfile(review_source_root / name, review_target_root / name)
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
                "stage": "E1",
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
            "stage": "E1",
            "operation": "controlled-environment-system-generation",
            "session_id": session["session_id"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "baseline_completion": session["baseline_completion"],
            "upstream_completions": session["upstream_completions"],
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "output_sha256": rt.canonical_sha256(model),
        }
        _write(staging / "execution-record.json", execution)
        (staging / "environment-preview.md").write_text(
            "# Environment system\n\n"
            + "\n".join(
                f"- **{item['id']}**: {item['narrative_responsibility']}"
                for item in model["environments"]
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
            "stage": "E1",
            "package_profile": "generated-model",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "canonical": by_path["environment-system.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
                "preview": by_path["environment-preview.md"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_e1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "E1",
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
            "E1",
            _logical(logical_package_path, "stage-completion.json"),
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_e1_package(staging, runtime=contract_runtime)
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
    return E1RunReceipt(
        package_root=destination,
        model=copy.deepcopy(model),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
    )


__all__ = [
    "PHASES",
    "PHASE_FIELDS",
    "CURRENT_MODEL_SCHEMA_VERSION",
    "LEGACY_MODEL_SCHEMA_VERSIONS",
    "AUTHORITY_REVIEW_PROTOCOL",
    "HOSTING_REVIEW_PROTOCOL",
    "LEGACY_HOSTING_REVIEW_PROTOCOL",
    "E1Error",
    "E1RunReceipt",
    "run_e1",
    "start_e1_session",
    "start_e1_authority_semantic_review",
    "submit_e1_authority_semantic_review",
    "start_e1_hosting_semantic_review",
    "submit_e1_hosting_semantic_review",
    "submit_e1_phase",
    "validate_e1_package",
]
