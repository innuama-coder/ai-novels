"""Production W1 runner for autonomous novel-conception V2."""

from __future__ import annotations

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
s1_runtime = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_S1_SKILL = _REPO / "skills" / "novel-storyline-architecture-designer"
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"

PHASES = (
    "requirement-projection",
    "world-rules-and-history",
    "systems-and-flows",
    "cross-line-world-test",
    "final-world-model",
)
PHASE_FIELDS = {
    "requirement-projection": ("storyline_requirements",),
    "world-rules-and-history": (
        "design_decisions",
        "world_definition",
        "world_facts",
        "reality_claims",
        "world_facets",
        "history_pressures",
    ),
    "systems-and-flows": (
        "institutions",
        "systems",
        "resource_flows",
        "authority_flows",
        "information_flows",
    ),
    "cross-line-world-test": (
        "rule_conflict_matrix",
        "storyline_support_ledger",
        "environment_demands",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-world-model": ("model",),
}
_FORBIDDEN_MODEL_KEYS = {
    "environments",
    "locations",
    "functional_zones",
    "scenes",
    "events",
    "event_timeline",
    "characters",
    "character_profiles",
}
_FORBIDDEN_PACKAGE_NAMES = {
    "environment-system.json",
    "event-timeline.json",
    "character-system.json",
}
_RULE_TAGS = ("Scope:", "Exception:", "Cost:", "Constraint:")
CURRENT_CONTRACT_REVISION = "2026-08-11"
CURRENT_MODEL_SCHEMA_VERSION = "2.1"
LEGACY_MODEL_SCHEMA_VERSION = "2.0"
_TRUSTED_LEGACY_IMPLEMENTATION_PAIRS = frozenset(
    {
        (
            "4b02e32bd9e31f414e21ffe711021c4561d602434ec92bac683da5ddf85b2a1a",
            "efd4b99f3b7279ae061e4a7ae41068bbdf35af4d1c3a5e82a9189869c2bbbe01",
        ),
        (
            "74b575b3d32dd5f019d71057afa49be744641a16746cddfbcbc7be784ee1fea7",
            "efd4b99f3b7279ae061e4a7ae41068bbdf35af4d1c3a5e82a9189869c2bbbe01",
        ),
    }
)


class W1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class W1RunReceipt:
    package_root: Path
    model: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any


def _fail(code: str, message: str) -> None:
    raise W1Error(code, message)


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
                    "W1_AUTHORITY_PARTITION_OVERLAP",
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


def _logical(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        _fail("W1_PATH_INVALID", value)
    return value


def _path_lexists(path: Path) -> bool:
    """Return true for every occupied target, including dangling symlinks."""

    return os.path.lexists(os.fspath(path))


def _create_package_staging(destination: Path) -> Path:
    """Create a short, same-volume directory for atomic publication.

    W1 copies the complete ready S1 package, including immutable review
    directories whose names are SHA-256 values. Even a short temporary name
    beside a deeply nested destination can exceed the legacy Windows path
    limit. Prefer the process temporary directory when it is on the same
    filesystem as the destination, so the staging tree has a short absolute
    path while publication remains one same-volume atomic rename. Fall back to
    the destination parent on filesystems where the process temporary
    directory is on another volume.
    """

    parent = destination.parent.resolve()
    if _path_lexists(destination):
        _fail("W1_OUTPUT_EXISTS", str(destination))

    parent_device = os.stat(parent).st_dev
    process_temp = Path(tempfile.gettempdir()).resolve()
    staging_parent = parent
    try:
        if process_temp.is_dir() and os.stat(process_temp).st_dev == parent_device:
            staging_parent = process_temp
    except OSError:
        # The destination-parent fallback is still same-volume by construction.
        staging_parent = parent

    temporary = Path(tempfile.mkdtemp(prefix=".w1-", dir=staging_parent))
    try:
        resolved = temporary.resolve(strict=True)
        if resolved.parent != staging_parent:
            _fail("W1_STAGING_INVALID", str(resolved))
        if os.stat(resolved).st_dev != parent_device:
            _fail("W1_STAGING_CROSS_VOLUME", str(resolved))
        return resolved
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _publish_package_staging(staging: Path, destination: Path) -> None:
    """Publish one complete package without replacing an occupied target."""

    if _path_lexists(destination):
        _fail("W1_OUTPUT_EXISTS", str(destination))
    try:
        staging.rename(destination)
    except FileExistsError:
        _fail("W1_OUTPUT_EXISTS", str(destination))


W1_RUNTIME_DEPENDENCIES = (
    "canonical.py",
    "contracts.py",
    "coordinator.py",
    "baseline.py",
)

W1_SCHEMA_DEPENDENCIES = (
    "world-model.schema.json",
    "storyline-architecture.schema.json",
    "author-control-baseline.schema.json",
    "canonical-common.schema.json",
    "common-defs.schema.json",
    "input-gate.schema.json",
    "package-manifest.schema.json",
    "stage-completion.schema.json",
)


def _implementation_paths() -> dict[str, Path]:
    runtime_dir = _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    values = {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/runtime-contract.md": _SKILL / "references" / "runtime-contract.md",
        "upstream/S1-run_v2.py": _S1_SKILL / "scripts" / "run_v2.py",
        "upstream/S1-SKILL.md": _S1_SKILL / "SKILL.md",
        "upstream/S1-runtime-contract.md": (
            _S1_SKILL / "references" / "runtime-contract.md"
        ),
    }
    for name in W1_RUNTIME_DEPENDENCIES:
        values[f"runtime/{name}"] = runtime_dir / name
    for name in W1_SCHEMA_DEPENDENCIES:
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


def _sealed_upstream_reference(
    package_root: Path,
    sealed_reference: Mapping[str, Any],
    *,
    stage: str,
    run_id: str,
    previous_stage_completions: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> dict[str, str]:
    """Prove that a gate-selected completion belongs to the supplied package.

    Upstream packages may live below immutable attempt workspaces, so the
    coordinator gate -- not a stage-name directory convention -- owns their
    logical paths.  The logical completion, manifest, and validation paths must
    nevertheless be canonical siblings and must bind the files in the actual
    package root supplied to W1.
    """

    code = f"W1_{stage}_INVALID"
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


def _source_artifacts(b0_root: Path, s1_root: Path) -> list[dict[str, str]]:
    return [
        *[
            {
                "path": f"sources/B0/{name}",
                "sha256": rt.sha256_file(b0_root / name),
            }
            for name in (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ],
        *[
            {
                "path": f"sources/S1/{name}",
                "sha256": rt.sha256_file(s1_root / name),
            }
            for name in (
                "storyline-architecture.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ],
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


def _storyline_bindings(
    storyline: Mapping[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "id": line["id"],
            "type": line["type"],
            "value_sha256": rt.canonical_sha256(line),
        }
        for line in storyline["storylines"]
    ]


def _requirement_bindings(
    storyline: Mapping[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            "target_stage": item["target_stage"],
            "value_sha256": rt.canonical_sha256(item),
        }
        for item in storyline["world_requirements"]
    ]


def _fact_dependency_bindings(
    baseline: Mapping[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "id": item["id"],
            "status": item["status"],
            "value_sha256": rt.canonical_sha256(item),
        }
        for item in baseline["fact_dependencies"]
    ]


def _session_id(
    thread_id: str,
    gate_reference: Mapping[str, str],
    b0_reference: Mapping[str, str],
    s1_reference: Mapping[str, str],
) -> str:
    return "W1-" + rt.canonical_sha256(
        [thread_id, gate_reference, b0_reference, s1_reference]
    )[:20]


def _session_context(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[
    Path,
    Path,
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, str],
    dict[str, str],
]:
    b0_root = Path(baseline_package).resolve()
    s1_root = Path(storyline_package).resolve()
    if full_validation:
        try:
            rt.validate_baseline_package(b0_root, runtime=runtime)
        except Exception as error:
            _fail("W1_B0_INVALID", str(error))
        try:
            s1_runtime.validate_s1_package(s1_root, runtime=runtime)
        except Exception as error:
            _fail("W1_S1_INVALID", str(error))
    baseline = _read(
        b0_root / "author-control-baseline.json", "W1_B0_INVALID"
    )
    storyline = _read(
        s1_root / "storyline-architecture.json", "W1_S1_INVALID"
    )
    if baseline["run_id"] != storyline["run_id"]:
        _fail("W1_RUN_ID_MISMATCH", "B0 and S1 belong to different runs")
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("W1_GATE_INVALID", str(error))
    if rt.canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("W1_GATE_INVALID", "gate reference does not bind its body")
    sealed_b0 = input_gate.data.get("baseline_completion")
    sealed_upstreams = input_gate.data.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 1
        or not isinstance(sealed_upstreams[0], Mapping)
    ):
        _fail("W1_GATE_INVALID", "gate does not select exactly one B0 and S1")
    b0_reference = _sealed_upstream_reference(
        b0_root,
        sealed_b0,
        stage="B0",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    s1_reference = _sealed_upstream_reference(
        s1_root,
        sealed_upstreams[0],
        stage="S1",
        run_id=baseline["run_id"],
        previous_stage_completions=[],
        runtime=runtime,
    )
    copied_b0_completion = s1_root / "sources" / "B0" / "stage-completion.json"
    if (
        not copied_b0_completion.is_file()
        or rt.sha256_file(copied_b0_completion) != b0_reference["sha256"]
        or rt.canonical_sha256(
            _read(copied_b0_completion, "W1_BASELINE_MISMATCH")
        )
        != b0_reference["sha256"]
    ):
        _fail("W1_BASELINE_MISMATCH", "S1 does not bind the supplied B0")
    if (
        input_gate.data.get("target_stage") != "W1"
        or input_gate.data.get("run_id") != baseline["run_id"]
        or input_gate.data.get("baseline_completion") != b0_reference
        or input_gate.data.get("upstream_completions") != [s1_reference]
    ):
        _fail("W1_GATE_INVALID", "gate is not the exact W1/B0/S1 gate")
    return (
        b0_root,
        s1_root,
        baseline,
        storyline,
        _controls(b0_root, baseline),
        b0_reference,
        s1_reference,
    )


def _boundary_check(model: Mapping[str, Any]) -> None:
    forbidden = sorted(set(model) & _FORBIDDEN_MODEL_KEYS)
    if forbidden:
        _fail(
            "W1_BOUNDARY_VIOLATION",
            f"W1 cannot deliver downstream artifacts: {forbidden}",
        )


def _requirement_marker(requirement: Mapping[str, Any]) -> str:
    return requirement["responsibility"]


def _is_current_contract(model: Mapping[str, Any]) -> bool:
    revision = model.get("contract_revision")
    if revision is None:
        if model.get("schema_version") != LEGACY_MODEL_SCHEMA_VERSION:
            _fail(
                "W1_LEGACY_SCHEMA_VERSION_INVALID",
                str(model.get("schema_version")),
            )
        return False
    if revision != CURRENT_CONTRACT_REVISION:
        _fail("W1_CONTRACT_REVISION_UNSUPPORTED", str(revision))
    if model.get("schema_version") != CURRENT_MODEL_SCHEMA_VERSION:
        _fail(
            "W1_CURRENT_SCHEMA_VERSION_INVALID",
            str(model.get("schema_version")),
        )
    return True


def _validate_legacy_package_provenance(
    model: Mapping[str, Any],
    session: Mapping[str, Any],
    evidence_paths: Sequence[Path],
    catalog: Mapping[str, Mapping[str, str]],
) -> None:
    if (
        model.get("schema_version") != LEGACY_MODEL_SCHEMA_VERSION
        or "contract_revision" in model
        or session.get("schema_version") != LEGACY_MODEL_SCHEMA_VERSION
        or "contract_revision" in session
    ):
        _fail("W1_LEGACY_PROVENANCE_UNTRUSTED", "model/session marker mismatch")
    for path in evidence_paths:
        evidence = _read(path, "W1_EVIDENCE_INVALID")
        if (
            evidence.get("schema_version") != LEGACY_MODEL_SCHEMA_VERSION
            or "contract_revision" in evidence
        ):
            _fail(
                "W1_LEGACY_PROVENANCE_UNTRUSTED",
                f"current marker in {path.name}",
            )
    runtime_ref = catalog.get("skill/run_v2.py")
    schema_ref = catalog.get("schemas/world-model.schema.json")
    pair = (
        runtime_ref.get("sha256") if isinstance(runtime_ref, Mapping) else None,
        schema_ref.get("sha256") if isinstance(schema_ref, Mapping) else None,
    )
    if pair not in _TRUSTED_LEGACY_IMPLEMENTATION_PAIRS:
        _fail("W1_LEGACY_PROVENANCE_UNTRUSTED", f"implementation pair {pair}")


def _resolve_pointer(document: Any, pointer: str, *, code: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        _fail(code, f"invalid JSON pointer: {pointer!r}")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        try:
            if isinstance(value, list):
                value = value[int(token)]
            elif isinstance(value, Mapping):
                value = value[token]
            else:
                raise KeyError(token)
        except (KeyError, IndexError, TypeError, ValueError):
            _fail(code, f"unresolvable JSON pointer: {pointer}")
    return value


def _requirement_claim_pointers(requirement: Mapping[str, Any]) -> set[str]:
    return {
        "/required_capability",
        *{
            f"/constraints/{index}"
            for index in range(len(requirement["constraints"]))
        },
        *{
            f"/acceptance_checks/{index}"
            for index in range(len(requirement["acceptance_checks"]))
        },
        "/downstream_freedom",
    }


def _expected_claim_disposition(pointer: str) -> str:
    if pointer == "/required_capability":
        return "realized"
    if pointer.startswith("/constraints/"):
        return "constrained"
    if pointer.startswith("/acceptance_checks/"):
        return "tested"
    if pointer == "/downstream_freedom":
        return "deferred_to_downstream"
    _fail("W1_SUPPORT_SOURCE_POINTER_INVALID", pointer)


def _validate_author_open_exclusion(
    *,
    author_open: set[str],
    decisions: Sequence[Mapping[str, Any]] = (),
    facts: Sequence[Mapping[str, Any]] = (),
    supports: Sequence[Mapping[str, Any]] = (),
    derivations: Sequence[Mapping[str, Any]] = (),
) -> None:
    implemented: set[str] = set()
    for decision in decisions:
        implemented.update(decision.get("impact_ids", ()))
        implemented.update(decision.get("projection_ids", ()))
    for fact in facts:
        implemented.update(fact.get("source_ids", ()))
    for support in supports:
        implemented.update(support.get("source_ids", ()))
        implemented.update(support.get("realization_ids", ()))
        implemented.update(
            item.get("realization_id")
            for item in support.get("claim_coverage", ())
            if item.get("realization_id") is not None
        )
    for derivation in derivations:
        implemented.update(derivation.get("source_ids", ()))
        implemented.update(derivation.get("projection_ids", ()))
    forbidden = implemented & author_open
    if forbidden:
        _fail("W1_AUTHOR_OPEN_IMPLEMENTED", str(sorted(forbidden)))


def _entity_pointer_index(model: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in (
        "world_facts",
        "reality_claims",
        "history_pressures",
        "institutions",
        "systems",
        "resource_flows",
        "authority_flows",
        "information_flows",
        "rule_conflict_matrix",
        "storyline_support_ledger",
        "environment_demands",
        "design_decisions",
        "open_items",
    ):
        for index, item in enumerate(model[field]):
            values[item["id"]] = f"/{field}/{index}"
    return values


def _validate_global_id_registry(model: Mapping[str, Any]) -> None:
    seen: dict[str, str] = {}
    for field in (
        "world_facts",
        "reality_claims",
        "history_pressures",
        "institutions",
        "systems",
        "resource_flows",
        "authority_flows",
        "information_flows",
        "rule_conflict_matrix",
        "storyline_support_ledger",
        "environment_demands",
        "design_decisions",
        "open_items",
    ):
        for item in model[field]:
            item_id = item["id"]
            if item_id in seen:
                _fail(
                    "W1_GLOBAL_ID_COLLISION",
                    f"{item_id}: {seen[item_id]} and {field}",
                )
            seen[item_id] = field


def _validate_claim_coverage(
    record: Mapping[str, Any],
    requirement: Mapping[str, Any],
    model: Mapping[str, Any],
    owned_entities: Mapping[str, Mapping[str, Any]],
) -> None:
    coverage = record.get("claim_coverage")
    if not isinstance(coverage, list) or not coverage:
        _fail("W1_SUPPORT_CLAIM_COVERAGE_MISSING", record["id"])
    pointers = [item.get("source_pointer") for item in coverage]
    expected = _requirement_claim_pointers(requirement)
    if len(pointers) != len(set(pointers)) or set(pointers) != expected:
        _fail("W1_SUPPORT_CLAIM_COVERAGE_MISMATCH", record["id"])
    entity_pointers = _entity_pointer_index(model)
    realization_ids = set(record["realization_ids"])
    for item in coverage:
        source_pointer = item["source_pointer"]
        source_value = _resolve_pointer(
            requirement, source_pointer, code="W1_SUPPORT_SOURCE_POINTER_INVALID"
        )
        if item["source_sha256"] != rt.canonical_sha256(source_value):
            _fail("W1_SUPPORT_SOURCE_HASH_MISMATCH", record["id"])
        expected_disposition = _expected_claim_disposition(source_pointer)
        if item.get("disposition") != expected_disposition:
            _fail(
                "W1_SUPPORT_DISPOSITION_MISMATCH",
                f"{record['id']}:{source_pointer}",
            )
        realization_id = item["realization_id"]
        if realization_id not in realization_ids or realization_id not in owned_entities:
            _fail("W1_SUPPORT_REALIZATION_MISMATCH", record["id"])
        expected_prefix = entity_pointers.get(realization_id)
        pointer = item["realization_pointer"]
        if expected_prefix is None or not (
            pointer == expected_prefix or pointer.startswith(expected_prefix + "/")
        ):
            _fail("W1_SUPPORT_REALIZATION_POINTER_INVALID", record["id"])
        _resolve_pointer(
            model, pointer, code="W1_SUPPORT_REALIZATION_POINTER_INVALID"
        )
        if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            _fail("W1_SUPPORT_RATIONALE_MISSING", record["id"])


def _validate_model(
    model: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
    *,
    expected_gate: Mapping[str, str] | None = None,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
) -> None:
    _boundary_check(model)
    current_contract = _is_current_contract(model)
    try:
        runtime.validate(model, "world-model.schema.json")
    except Exception as error:
        _fail("W1_MODEL_SCHEMA_INVALID", str(error))
    author_open = {
        item["id"] for item in controls if item["hardness"] == "author_open"
    }
    if current_contract:
        _validate_author_open_exclusion(
            author_open=author_open,
            decisions=model["design_decisions"],
            facts=model["world_facts"],
            supports=model["storyline_support_ledger"],
            derivations=model["derivation_claims"],
        )
    partition = model["authority_partition"]
    _validate_authority_disjoint(partition)
    if model["run_id"] != baseline["run_id"]:
        _fail("W1_RUN_ID_MISMATCH", "model belongs to another run")
    if model["storyline_requirements"] != storyline["world_requirements"]:
        _fail(
            "W1_REQUIREMENT_PROJECTION_MISMATCH",
            "W1 must consume the exact S1 world requirement objects",
        )
    requirements = model["storyline_requirements"]
    requirement_ids = [item["id"] for item in requirements]
    if len(requirement_ids) != len(set(requirement_ids)):
        _fail("W1_REQUIREMENT_DUPLICATE", "S1 world requirements are duplicated")
    requirements_by_id = {item["id"]: item for item in requirements}
    lines = {item["id"]: item for item in storyline["storylines"]}
    demand_ids = {item["id"] for item in storyline["storyline_demands"]}
    requirement_line: dict[str, str] = {}
    for requirement in requirements:
        line_ids = [item for item in requirement["source_ids"] if item in lines]
        referenced_demands = [
            item for item in requirement["source_ids"] if item in demand_ids
        ]
        if len(line_ids) != 1 or not referenced_demands:
            _fail(
                "W1_REQUIREMENT_SOURCE_INVALID",
                f"{requirement['id']} does not bind one storyline and its demands",
            )
        requirement_line[requirement["id"]] = line_ids[0]
    if set(requirement_line.values()) != set(lines):
        _fail(
            "W1_STORYLINE_COVERAGE_MISMATCH",
            "S1 world requirements do not cover every storyline",
        )

    if current_contract:
        _validate_global_id_registry(model)

    if not current_contract:
        world_definition_text = rt.canonical_json(model["world_definition"])
        for requirement in requirements:
            if _requirement_marker(requirement) not in world_definition_text:
                _fail(
                    "W1_SOURCE_MEANING_UNBOUND",
                    f"{requirement['id']} does not participate in world_definition",
                )

    facts = {item["id"]: item for item in model["world_facts"]}
    history = {item["id"]: item for item in model["history_pressures"]}
    institutions = {item["id"]: item for item in model["institutions"]}
    systems = {item["id"]: item for item in model["systems"]}
    if any(
        len(values) != len(source)
        for values, source in (
            (facts, model["world_facts"]),
            (history, model["history_pressures"]),
            (institutions, model["institutions"]),
            (systems, model["systems"]),
        )
    ):
        _fail("W1_ID_DUPLICATE", "world entity IDs must be unique")
    rules = {
        item_id: item for item_id, item in facts.items() if item["kind"] == "rule"
    }
    if not rules:
        _fail("W1_RULE_MISSING", "at least one world rule is required")
    known_source_ids = {
        *requirement_ids,
        *[item["id"] for item in controls],
        *[item["id"] for item in model["design_decisions"]],
    }
    for fact in facts.values():
        if not set(fact["source_ids"]).issubset(known_source_ids):
            _fail("W1_SOURCE_ID_DANGLING", fact["id"])
        if not set(fact["applies_to_ids"]).issubset(lines):
            _fail("W1_STORYLINE_ID_DANGLING", fact["id"])
    for rule in rules.values():
        rule_text = rt.canonical_json(rule)
        for tag in _RULE_TAGS:
            if tag not in rule_text:
                _fail(
                    "W1_RULE_SEMANTICS_INCOMPLETE",
                    f"{rule['id']} is missing {tag}",
                )

    if current_contract:
        rule_requirement_coverage: set[str] = set()
        for rule in rules.values():
            carried = set(rule["source_ids"]) & set(requirement_ids)
            if not carried:
                _fail("W1_RULE_REQUIREMENT_SOURCE_MISSING", rule["id"])
            rule_requirement_coverage.update(carried)
        if rule_requirement_coverage != set(requirement_ids):
            _fail(
                "W1_RULE_REQUIREMENT_COVERAGE_MISMATCH",
                "every requirement needs at least one rule",
            )

    if current_contract:
        facet_requirements: set[str] = set()
        facet_rules: set[str] = set()
        for facet, entries in model["world_facets"].items():
            if not entries or not all(isinstance(item, Mapping) for item in entries):
                _fail("W1_FACET_UNBOUND", f"{facet} needs structured entries")
            for entry in entries:
                if not set(entry["requirement_ids"]).issubset(requirement_ids):
                    _fail("W1_FACET_UNBOUND", f"{facet} requirement reference")
                if not set(entry["rule_ids"]).issubset(rules):
                    _fail("W1_FACET_UNBOUND", f"{facet} rule reference")
                facet_requirements.update(entry["requirement_ids"])
                facet_rules.update(entry["rule_ids"])
        if facet_requirements != set(requirement_ids) or facet_rules != set(rules):
            _fail("W1_FACET_COVERAGE_MISMATCH", "facets must cover all requirements and rules")
    else:
        requirement_markers = [
            _requirement_marker(requirement) for requirement in requirements
        ]
        for facet, entries in model["world_facets"].items():
            facet_text = rt.canonical_json(entries)
            if not any(marker in facet_text for marker in requirement_markers):
                _fail(
                    "W1_FACET_UNBOUND",
                    f"{facet} does not carry any approved S1 world requirement",
                )

    actor_slots = {
        actor
        for line in lines.values()
        for actor in line["actor_slot_ids"]
    }
    system_requirement_coverage: set[str] = set()
    for system in systems.values():
        if not set(system["storyline_ids"]).issubset(lines):
            _fail("W1_STORYLINE_ID_DANGLING", system["id"])
        if (
            not system["actor_slot_ids"]
            or not set(system["actor_slot_ids"]).issubset(actor_slots)
        ):
            _fail("W1_ACTOR_SLOT_DANGLING", system["id"])
        if not system["resources"] or not system["authorities"]:
            _fail(
                "W1_SYSTEM_NOT_CLOSED",
                f"{system['id']} lacks resources or authorities",
            )
        transformation_text = rt.canonical_json(system["transformation_rules"])
        if "Scope:" not in transformation_text or "Exception:" not in transformation_text:
            _fail(
                "W1_SYSTEM_NOT_CLOSED",
                f"{system['id']} lacks scope or exception",
            )
        if current_contract:
            source_requirement_ids = system.get("source_requirement_ids")
            if (
                not isinstance(source_requirement_ids, list)
                or not source_requirement_ids
                or not set(source_requirement_ids).issubset(requirement_ids)
            ):
                _fail("W1_SYSTEM_REQUIREMENT_SOURCE_INVALID", system["id"])
            system_requirement_coverage.update(source_requirement_ids)

    if current_contract and system_requirement_coverage != set(requirement_ids):
        _fail(
            "W1_SYSTEM_REQUIREMENT_COVERAGE_MISMATCH",
            "every requirement needs at least one system",
        )

    if current_contract:
        required_institution_fields = (
            "source_requirement_ids",
            "world_position",
            "interests",
            "intervention_scope",
        )
        dependency_targets = set(facts) | set(history) | set(institutions) | set(systems)
        for institution in institutions.values():
            for field in required_institution_fields:
                value = institution.get(field)
                if value is None or value == "" or value == []:
                    _fail("W1_INSTITUTION_FIELDS_INCOMPLETE", f"{institution['id']}.{field}")
            for field in ("dependencies", "conflicts"):
                if field not in institution or not isinstance(institution[field], list):
                    _fail("W1_INSTITUTION_FIELDS_INCOMPLETE", f"{institution['id']}.{field}")
            if not institution["dependencies"] and not institution["conflicts"]:
                _fail("W1_INSTITUTION_RELATION_MISSING", institution["id"])
            if not set(institution["source_requirement_ids"]).issubset(requirement_ids):
                _fail("W1_INSTITUTION_REQUIREMENT_SOURCE_INVALID", institution["id"])
            if not set(institution["dependencies"]).issubset(dependency_targets):
                _fail("W1_INSTITUTION_DEPENDENCY_DANGLING", institution["id"])

    owned_entities: dict[str, Mapping[str, Any]] = {
        **facts,
        **history,
        **institutions,
        **systems,
    }
    flows_by_field: dict[str, dict[str, Mapping[str, Any]]] = {}
    flow_endpoints = set(owned_entities)
    for field in ("resource_flows", "authority_flows", "information_flows"):
        values = model[field]
        if not values:
            _fail("W1_FLOW_MISSING", field)
        edges = {item["id"]: item for item in values}
        if len(edges) != len(values):
            _fail("W1_ID_DUPLICATE", field)
        for edge in edges.values():
            if (
                edge["from_id"] not in flow_endpoints
                or edge["to_id"] not in flow_endpoints
            ):
                _fail("W1_FLOW_DANGLING", edge["id"])
        signatures = [
            (
                item["from_id"],
                item["to_id"],
                item["relation"],
                item["mechanism"],
            )
            for item in values
        ]
        if len(signatures) != len(set(signatures)):
            _fail("W1_FLOW_DUPLICATE_EDGE", field)
        flows_by_field[field] = edges
        owned_entities.update(edges)
    authority_targets = [item["to_id"] for item in model["authority_flows"]]
    if len(authority_targets) != len(set(authority_targets)):
        _fail("W1_DOUBLE_OWNERSHIP", "authority_flows")
    for system_id in systems:
        for field, edges in flows_by_field.items():
            if not any(
                system_id in (edge["from_id"], edge["to_id"])
                for edge in edges.values()
            ):
                _fail(
                    "W1_SYSTEM_NOT_CLOSED",
                    f"{system_id} is absent from {field}",
                )

    coverage_collections = [
        (history.values(), "history"),
        (systems.values(), "system"),
    ]
    if not current_contract:
        coverage_collections.insert(1, (institutions.values(), "institution"))
    for collection, label in coverage_collections:
        covered_lines = {
            line_id for item in collection for line_id in item["storyline_ids"]
        }
        if covered_lines != set(lines):
            _fail(
                "W1_STORYLINE_COVERAGE_MISMATCH",
                f"{label} coverage differs from storylines",
            )

    reality_by_dependency: dict[str, Mapping[str, Any]] = {}
    for claim in model["reality_claims"]:
        dependency_id = claim["fact_dependency_id"]
        if dependency_id in reality_by_dependency:
            _fail("W1_REALITY_CLAIM_MISMATCH", dependency_id)
        reality_by_dependency[dependency_id] = claim
    dependencies = {item["id"]: item for item in baseline["fact_dependencies"]}
    if set(reality_by_dependency) != set(dependencies):
        _fail(
            "W1_REALITY_CLAIM_MISMATCH",
            "every B0 fact dependency must have exactly one W1 disposition",
        )
    handling_by_status = {
        "adopted": "adopted",
        "open": "preserve_open",
        "not_applicable": "fiction_boundary",
    }
    for dependency_id, dependency in dependencies.items():
        claim = reality_by_dependency[dependency_id]
        if (
            claim["handling"] != handling_by_status[dependency["status"]]
            or dependency["claim"] not in claim["claim"]
        ):
            _fail("W1_REALITY_CLAIM_MISMATCH", dependency_id)
        if dependency["status"] == "adopted" and (
            dependency["allowed_use"] not in claim["claim"]
            or dependency["fiction_boundary"] not in claim["claim"]
        ):
            _fail("W1_REALITY_CLAIM_MISMATCH", dependency_id)
        owned_entities[claim["id"]] = claim

    support_by_requirement: dict[str, Mapping[str, Any]] = {}
    for record in model["storyline_support_ledger"]:
        if len(record["source_ids"]) != 1:
            _fail("W1_SUPPORT_COVERAGE_MISMATCH", record["id"])
        requirement_id = record["source_ids"][0]
        if requirement_id in support_by_requirement:
            _fail("W1_SUPPORT_COVERAGE_MISMATCH", requirement_id)
        if requirement_id not in requirements_by_id:
            _fail("W1_SOURCE_ID_DANGLING", requirement_id)
        realization_ids = record["realization_ids"]
        if not set(realization_ids).issubset(owned_entities):
            _fail("W1_SUPPORT_ID_DANGLING", record["id"])
        if current_contract:
            matching_rules = [item for item in realization_ids if item in rules]
            matching_systems = [item for item in realization_ids if item in systems]
            if not matching_rules or not matching_systems:
                _fail(
                    "W1_SUPPORT_COVERAGE_MISMATCH",
                    f"{requirement_id} needs a rule and a system",
                )
            if not any(
                requirement_id in rules[item]["source_ids"]
                for item in matching_rules
            ) or not any(
                requirement_id in systems[item]["source_requirement_ids"]
                for item in matching_systems
            ):
                _fail("W1_SUPPORT_REQUIREMENT_BINDING_MISMATCH", requirement_id)
            for institution_id in (
                item for item in realization_ids if item in institutions
            ):
                if requirement_id not in institutions[institution_id]["source_requirement_ids"]:
                    _fail("W1_SUPPORT_REQUIREMENT_BINDING_MISMATCH", requirement_id)
            _validate_claim_coverage(
                record,
                requirements_by_id[requirement_id],
                model,
                owned_entities,
            )
        else:
            if (
                not any(item in rules for item in realization_ids)
                or not any(item in systems for item in realization_ids)
                or not any(item in institutions for item in realization_ids)
            ):
                _fail(
                    "W1_SUPPORT_COVERAGE_MISMATCH",
                    f"{requirement_id} needs a rule, a system, and an institution",
                )
            marker = _requirement_marker(requirements_by_id[requirement_id])
            realization_text = rt.canonical_json(
                [owned_entities[item] for item in realization_ids]
            )
            if marker not in realization_text or marker not in record["evidence"]:
                _fail("W1_SOURCE_MEANING_UNBOUND", requirement_id)
        support_by_requirement[requirement_id] = record
        owned_entities[record["id"]] = record
    if set(support_by_requirement) != set(requirements_by_id):
        _fail(
            "W1_SUPPORT_COVERAGE_MISMATCH",
            "support ledger must cover every S1 world requirement exactly once",
        )

    conflict_line_ids: set[str] = set()
    known_rule_ids = set(rules) | set(systems)
    for conflict in model["rule_conflict_matrix"]:
        if not set(conflict["rule_ids"]).issubset(known_rule_ids):
            _fail("W1_CONFLICT_RULE_DANGLING", conflict["id"])
        if not set(conflict["storyline_ids"]).issubset(lines):
            _fail("W1_STORYLINE_ID_DANGLING", conflict["id"])
        conflict_line_ids.update(conflict["storyline_ids"])
        owned_entities[conflict["id"]] = conflict
    if conflict_line_ids != set(lines):
        _fail(
            "W1_CONFLICT_COVERAGE_MISMATCH",
            "conflict matrix must test every storyline",
        )

    environment_by_requirement: dict[str, Mapping[str, Any]] = {}
    for demand in model["environment_demands"]:
        if demand["target_stage"] != "E1":
            _fail("W1_ENVIRONMENT_TARGET_MISMATCH", demand["id"])
        matching = [
            requirement_id
            for requirement_id in demand["source_ids"]
            if requirement_id in requirements_by_id
        ]
        if len(matching) != 1:
            _fail("W1_ENVIRONMENT_COVERAGE_MISMATCH", demand["id"])
        requirement_id = matching[0]
        support = support_by_requirement[requirement_id]
        expected_demand_sources = [requirement_id, *support["realization_ids"]]
        if demand["source_ids"] != expected_demand_sources:
            _fail(
                "W1_ENVIRONMENT_COVERAGE_MISMATCH",
                f"{demand['id']} does not bind the exact W1 support set",
            )
        if requirement_id in environment_by_requirement:
            _fail("W1_ENVIRONMENT_COVERAGE_MISMATCH", requirement_id)
        if current_contract:
            dimensions = demand.get("environment_dimensions")
            required_dimensions = {
                "macro_geography",
                "institution_facility",
                "spatial_relations",
                "plot_carriers",
            }
            if (
                not isinstance(dimensions, Mapping)
                or set(dimensions) != required_dimensions
                or any(not isinstance(dimensions[name], list) or not dimensions[name] for name in required_dimensions)
            ):
                _fail("W1_ENVIRONMENT_DIMENSIONS_INCOMPLETE", demand["id"])
        elif _requirement_marker(requirements_by_id[requirement_id]) not in rt.canonical_json(demand):
            _fail("W1_SOURCE_MEANING_UNBOUND", demand["id"])
        environment_by_requirement[requirement_id] = demand
    if set(environment_by_requirement) != set(requirements_by_id):
        _fail(
            "W1_ENVIRONMENT_COVERAGE_MISMATCH",
            "environment demands must cover every S1 world requirement once",
        )

    locked = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    }
    if set(partition["author_locked"]) != locked:
        _fail("W1_AUTHORITY_PARTITION_MISMATCH", "author_locked differs from B0")
    if set(partition["author_open"]) != author_open:
        _fail("W1_AUTHORITY_PARTITION_MISMATCH", "author_open differs from B0")
    if set(partition["downstream_freedom"]) != {
        item["id"] for item in model["environment_demands"]
    }:
        _fail(
            "W1_AUTHORITY_PARTITION_MISMATCH",
            "downstream freedom differs from E1 demands",
        )
    expected_owned = {
        *[item["id"] for item in model["design_decisions"]],
        *owned_entities,
    }
    if set(partition["autonomous_owned"]) != expected_owned:
        _fail(
            "W1_AUTHORITY_PARTITION_MISMATCH",
            "autonomous ownership is not exact",
        )

    decision_ids = {item["id"] for item in model["design_decisions"]}
    for decision in model["design_decisions"]:
        if (
            decision["owner"] != "W1"
            or decision["selection"] not in decision["options"]
            or not set(decision["projection_ids"]).issubset(expected_owned)
        ):
            _fail("W1_DECISION_INVALID", decision["id"])
    for claim in model["derivation_claims"]:
        if not set(claim["decision_ids"]).issubset(decision_ids):
            _fail("W1_DERIVATION_INVALID", claim["id"])
        if len(claim["projection_ids"]) == 1:
            projection_id = claim["projection_ids"][0]
            projection = owned_entities.get(projection_id)
            if projection is None or claim["value_sha256"] != rt.canonical_sha256(
                projection
            ):
                _fail("W1_DERIVATION_STALE", claim["id"])
    claimed = {
        claim["projection_ids"][0]
        for claim in model["derivation_claims"]
        if len(claim["projection_ids"]) == 1
    }
    required_derivations = set(rules) | set(systems)
    if current_contract:
        required_derivations.update(item["id"] for item in model["storyline_support_ledger"])
    if not required_derivations.issubset(claimed):
        _fail(
            "W1_DERIVATION_INCOMPLETE",
            "every rule, system, and current support needs a derivation claim",
        )

    actual_open = {
        source_id
        for item in model["open_items"]
        for source_id in item["source_ids"]
    }
    if actual_open != author_open:
        _fail("W1_OPEN_ITEMS_MISMATCH", "author-open controls changed")
    if expected_gate is not None and model["input_gate"] != expected_gate:
        _fail("W1_GATE_REFERENCE_MISMATCH", "model gate is not the stored gate")
    if expected_sources is not None and model["source_artifacts"] != list(
        expected_sources
    ):
        _fail(
            "W1_SOURCE_ARTIFACT_MISMATCH",
            "model does not bind the exact B0/S1 source set",
        )


def start_w1_session(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze B0, S1, gate, state, and thread before semantic generation."""

    root = Path(workspace).resolve()
    if root.exists():
        _fail("W1_SESSION_EXISTS", str(root))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("W1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    (
        b0_root,
        s1_root,
        baseline,
        storyline,
        controls,
        b0_reference,
        s1_reference,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    session = {
        "schema_version": "2.0",
        "contract_revision": CURRENT_CONTRACT_REVISION,
        "run_id": baseline["run_id"],
        "stage": "W1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_reference, s1_reference
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_reference,
        "upstream_completions": [s1_reference],
        "source_artifacts": _source_artifacts(b0_root, s1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _storyline_bindings(storyline),
        "requirement_bindings": _requirement_bindings(storyline),
        "fact_dependency_bindings": _fact_dependency_bindings(baseline),
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
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    session = _read(
        workspace / "generation-session.json", "W1_SESSION_INVALID"
    )
    (
        b0_root,
        s1_root,
        baseline,
        storyline,
        controls,
        b0_reference,
        s1_reference,
    ) = _session_context(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        input_gate=input_gate,
        runtime=runtime,
        full_validation=full_validation,
    )
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    expected = {
        "schema_version": "2.0",
        "contract_revision": CURRENT_CONTRACT_REVISION,
        "run_id": baseline["run_id"],
        "stage": "W1",
        "session_id": _session_id(
            thread_id, input_gate.reference, b0_reference, s1_reference
        ),
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": b0_reference,
        "upstream_completions": [s1_reference],
        "source_artifacts": _source_artifacts(b0_root, s1_root),
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _storyline_bindings(storyline),
        "requirement_bindings": _requirement_bindings(storyline),
        "fact_dependency_bindings": _fact_dependency_bindings(baseline),
        "phases": list(PHASES),
    }
    if not thread_id or session != expected:
        _fail("W1_SESSION_INVALID", "session no longer binds B0/S1/gate/thread")
    return session, baseline, storyline, controls


def _validate_definition(
    runtime: Any, value: Any, schema: str, definition: str, label: str
) -> None:
    try:
        runtime.validate_definition(value, schema, definition)
    except Exception as error:
        _fail("W1_PHASE_SCHEMA_INVALID", f"{label}: {error}")


def _sealed_phase_payloads(
    root: Path, session: Mapping[str, Any], completed: Sequence[str]
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    previous = None
    common_keys = (
        *(("contract_revision",) if "contract_revision" in session else ()),
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
        "requirement_bindings",
        "fact_dependency_bindings",
    )
    for index, phase in enumerate(completed, 1):
        path = root / "generation-evidence" / f"{index:02d}-{phase}.json"
        evidence = _read(path, "W1_EVIDENCE_INVALID")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("W1_EVIDENCE_INVALID", f"{phase} payload missing")
        expected = {
            "schema_version": "2.0",
            **{key: copy.deepcopy(session[key]) for key in common_keys},
            "stage": "W1",
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        if evidence != expected or set(payload) != set(PHASE_FIELDS[phase]):
            _fail("W1_EVIDENCE_INVALID", f"{phase} evidence binding invalid")
        payloads.append(copy.deepcopy(dict(payload)))
        previous = rt.sha256_file(path)
    return payloads


def _assemble_current_model(
    session: Mapping[str, Any], payloads: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    model: dict[str, Any] = {
        "schema_version": CURRENT_MODEL_SCHEMA_VERSION,
        "skill": "novel-world-model-designer",
        "stage": "W1",
        "run_id": session["run_id"],
        "status": "ready",
        "contract_revision": session["contract_revision"],
        "input_gate": copy.deepcopy(session["input_gate"]),
        "source_artifacts": copy.deepcopy(session["source_artifacts"]),
    }
    for payload in payloads:
        model.update(copy.deepcopy(dict(payload)))
    return model


def _validate_phase1_current(
    payload: Mapping[str, Any], storyline: Mapping[str, Any], runtime: Any
) -> None:
    _validate_definition(
        runtime,
        payload["storyline_requirements"],
        "canonical-common.schema.json",
        "worldRequirements",
        "storyline_requirements",
    )
    if payload["storyline_requirements"] != storyline["world_requirements"]:
        _fail("W1_REQUIREMENT_PROJECTION_MISMATCH", "Phase1 differs from S1")


def _validate_phase2_current(
    payloads: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> None:
    phase1, phase2 = payloads
    _validate_phase1_current(phase1, storyline, runtime)
    _validate_definition(runtime, phase2["design_decisions"], "canonical-common.schema.json", "designDecisions", "design_decisions")
    _validate_definition(runtime, phase2["world_definition"], "world-model.schema.json", "worldDefinition", "world_definition")
    _validate_definition(runtime, phase2["world_facets"], "world-model.schema.json", "worldFacets", "world_facets")
    for field, definition in (
        ("world_facts", "worldFact"),
        ("reality_claims", "realityClaim"),
        ("history_pressures", "historyPressure"),
    ):
        for index, item in enumerate(phase2[field]):
            _validate_definition(runtime, item, "world-model.schema.json", definition, f"{field}[{index}]")
    requirements = {item["id"]: item for item in phase1["storyline_requirements"]}
    lines = {item["id"] for item in storyline["storylines"]}
    decisions = {item["id"] for item in phase2["design_decisions"]}
    known_sources = set(requirements) | {item["id"] for item in controls} | decisions
    author_open = {
        item["id"] for item in controls if item["hardness"] == "author_open"
    }
    _validate_author_open_exclusion(
        author_open=author_open,
        decisions=phase2["design_decisions"],
        facts=phase2["world_facts"],
    )
    phase2_ids: set[str] = set()
    for field in ("design_decisions", "world_facts", "reality_claims", "history_pressures"):
        for item in phase2[field]:
            if item["id"] in phase2_ids:
                _fail("W1_GLOBAL_ID_COLLISION", item["id"])
            phase2_ids.add(item["id"])
    rules: dict[str, Mapping[str, Any]] = {}
    for fact in phase2["world_facts"]:
        if not set(fact["source_ids"]).issubset(known_sources):
            _fail("W1_SOURCE_ID_DANGLING", fact["id"])
        if not set(fact["applies_to_ids"]).issubset(lines):
            _fail("W1_STORYLINE_ID_DANGLING", fact["id"])
        if fact["kind"] == "rule":
            rules[fact["id"]] = fact
            if not (set(fact["source_ids"]) & set(requirements)):
                _fail("W1_RULE_REQUIREMENT_SOURCE_MISSING", fact["id"])
            for tag in _RULE_TAGS:
                if tag not in rt.canonical_json(fact):
                    _fail("W1_RULE_SEMANTICS_INCOMPLETE", f"{fact['id']} missing {tag}")
    if {
        requirement_id
        for rule in rules.values()
        for requirement_id in set(rule["source_ids"]) & set(requirements)
    } != set(requirements):
        _fail("W1_RULE_REQUIREMENT_COVERAGE_MISMATCH", "Phase2 rule coverage")
    facet_requirements: set[str] = set()
    facet_rules: set[str] = set()
    for name, entries in phase2["world_facets"].items():
        if not entries or not all(isinstance(item, Mapping) for item in entries):
            _fail("W1_FACET_UNBOUND", name)
        for entry in entries:
            if not set(entry["requirement_ids"]).issubset(requirements) or not set(entry["rule_ids"]).issubset(rules):
                _fail("W1_FACET_UNBOUND", name)
            facet_requirements.update(entry["requirement_ids"])
            facet_rules.update(entry["rule_ids"])
    if facet_requirements != set(requirements) or facet_rules != set(rules):
        _fail("W1_FACET_COVERAGE_MISMATCH", "Phase2 facet coverage")
    if {
        line for item in phase2["history_pressures"] for line in item["storyline_ids"]
    } != lines:
        _fail("W1_STORYLINE_COVERAGE_MISMATCH", "history coverage")
    if any(
        not set(item["storyline_ids"]).issubset(lines)
        for item in phase2["history_pressures"]
    ):
        _fail("W1_STORYLINE_ID_DANGLING", "history pressure")
    dependencies = {item["id"]: item for item in baseline["fact_dependencies"]}
    dependency_ids = [
        item["fact_dependency_id"] for item in phase2["reality_claims"]
    ]
    if len(dependency_ids) != len(set(dependency_ids)):
        _fail("W1_REALITY_CLAIM_MISMATCH", "duplicate Phase2 dependency")
    reality = {item["fact_dependency_id"]: item for item in phase2["reality_claims"]}
    if set(reality) != set(dependencies):
        _fail("W1_REALITY_CLAIM_MISMATCH", "Phase2 reality closure")
    handling_by_status = {
        "adopted": "adopted",
        "open": "preserve_open",
        "not_applicable": "fiction_boundary",
    }
    for dependency_id, dependency in dependencies.items():
        claim = reality[dependency_id]
        if (
            claim["handling"] != handling_by_status[dependency["status"]]
            or dependency["claim"] not in claim["claim"]
        ):
            _fail("W1_REALITY_CLAIM_MISMATCH", dependency_id)
        if dependency["status"] == "adopted" and (
            dependency["allowed_use"] not in claim["claim"]
            or dependency["fiction_boundary"] not in claim["claim"]
        ):
            _fail("W1_REALITY_CLAIM_MISMATCH", dependency_id)


def _validate_phase3_current(
    payloads: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> None:
    _validate_phase2_current(payloads[:2], baseline, storyline, controls, runtime)
    phase1, phase2, phase3 = payloads
    for field, definition in (("institutions", "institution"), ("systems", "system")):
        for index, item in enumerate(phase3[field]):
            _validate_definition(runtime, item, "world-model.schema.json", definition, f"{field}[{index}]")
    for field in ("resource_flows", "authority_flows", "information_flows"):
        for index, item in enumerate(phase3[field]):
            _validate_definition(runtime, item, "canonical-common.schema.json", "relationEdge", f"{field}[{index}]")
    requirements = {item["id"] for item in phase1["storyline_requirements"]}
    lines = {item["id"] for item in storyline["storylines"]}
    actors = {slot for line in storyline["storylines"] for slot in line["actor_slot_ids"]}
    facts = {item["id"] for item in phase2["world_facts"]}
    history = {item["id"] for item in phase2["history_pressures"]}
    institutions = {item["id"]: item for item in phase3["institutions"]}
    systems = {item["id"]: item for item in phase3["systems"]}
    system_coverage: set[str] = set()
    dependency_targets = facts | history | set(institutions) | set(systems)
    for institution in institutions.values():
        for field in ("source_requirement_ids", "world_position", "interests", "intervention_scope"):
            if institution.get(field) in (None, "", []):
                _fail("W1_INSTITUTION_FIELDS_INCOMPLETE", f"{institution['id']}.{field}")
        for field in ("dependencies", "conflicts"):
            if field not in institution or not isinstance(institution[field], list):
                _fail("W1_INSTITUTION_FIELDS_INCOMPLETE", f"{institution['id']}.{field}")
        if not institution["dependencies"] and not institution["conflicts"]:
            _fail("W1_INSTITUTION_RELATION_MISSING", institution["id"])
        if not set(institution["source_requirement_ids"]).issubset(requirements):
            _fail("W1_INSTITUTION_REQUIREMENT_SOURCE_INVALID", institution["id"])
        if not set(institution["dependencies"]).issubset(dependency_targets):
            _fail("W1_INSTITUTION_DEPENDENCY_DANGLING", institution["id"])
    for system in systems.values():
        if not system["actor_slot_ids"] or not set(system["actor_slot_ids"]).issubset(actors):
            _fail("W1_ACTOR_SLOT_DANGLING", system["id"])
        if not set(system["storyline_ids"]).issubset(lines):
            _fail("W1_STORYLINE_ID_DANGLING", system["id"])
        source_ids = system.get("source_requirement_ids")
        if not isinstance(source_ids, list) or not source_ids or not set(source_ids).issubset(requirements):
            _fail("W1_SYSTEM_REQUIREMENT_SOURCE_INVALID", system["id"])
        system_coverage.update(source_ids)
        if not system["resources"] or not system["authorities"]:
            _fail("W1_SYSTEM_NOT_CLOSED", system["id"])
        transformation = rt.canonical_json(system["transformation_rules"])
        if "Scope:" not in transformation or "Exception:" not in transformation:
            _fail("W1_SYSTEM_NOT_CLOSED", system["id"])
    if system_coverage != requirements:
        _fail("W1_SYSTEM_REQUIREMENT_COVERAGE_MISMATCH", "Phase3 system coverage")
    if {line for item in systems.values() for line in item["storyline_ids"]} != lines:
        _fail("W1_STORYLINE_COVERAGE_MISMATCH", "system coverage")
    endpoints = dependency_targets
    for field in ("resource_flows", "authority_flows", "information_flows"):
        signatures: set[tuple[str, str, str, str]] = set()
        for edge in phase3[field]:
            if edge["from_id"] not in endpoints or edge["to_id"] not in endpoints:
                _fail("W1_FLOW_DANGLING", edge["id"])
            signature = (edge["from_id"], edge["to_id"], edge["relation"], edge["mechanism"])
            if signature in signatures:
                _fail("W1_FLOW_DUPLICATE_EDGE", field)
            signatures.add(signature)
    authority_targets = [item["to_id"] for item in phase3["authority_flows"]]
    if len(authority_targets) != len(set(authority_targets)):
        _fail("W1_DOUBLE_OWNERSHIP", "authority_flows")
    for system_id in systems:
        for field in ("resource_flows", "authority_flows", "information_flows"):
            if not any(
                system_id in (item["from_id"], item["to_id"])
                for item in phase3[field]
            ):
                _fail("W1_SYSTEM_NOT_CLOSED", f"{system_id} absent from {field}")
    known_ids: set[str] = set()
    for field in ("design_decisions", "world_facts", "reality_claims", "history_pressures"):
        for item in phase2[field]:
            if item["id"] in known_ids:
                _fail("W1_GLOBAL_ID_COLLISION", item["id"])
            known_ids.add(item["id"])
    for field in ("institutions", "systems", "resource_flows", "authority_flows", "information_flows"):
        for item in phase3[field]:
            if item["id"] in known_ids:
                _fail("W1_GLOBAL_ID_COLLISION", item["id"])
            known_ids.add(item["id"])


def _validate_current_phase_candidate(
    phase: str,
    body: Mapping[str, Any],
    sealed_payloads: Sequence[Mapping[str, Any]],
    session: Mapping[str, Any],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> None:
    payloads = [*sealed_payloads, body]
    if phase == "requirement-projection":
        _validate_phase1_current(body, storyline, runtime)
    elif phase == "world-rules-and-history":
        _validate_phase2_current(payloads, baseline, storyline, controls, runtime)
    elif phase == "systems-and-flows":
        _validate_phase3_current(payloads, baseline, storyline, controls, runtime)
    elif phase == "cross-line-world-test":
        _validate_phase3_current(payloads[:3], baseline, storyline, controls, runtime)
        model = _assemble_current_model(session, payloads)
        _validate_model(
            model,
            baseline,
            storyline,
            controls,
            runtime,
            expected_gate=session["input_gate"],
            expected_sources=session["source_artifacts"],
        )
    elif phase == "final-world-model":
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("W1_PHASE_PAYLOAD_INVALID", "final model is missing")
        expected = _assemble_current_model(session, sealed_payloads)
        if model != expected:
            _fail("W1_PHASE_PROJECTION_MISMATCH", "Phase5 differs from sealed Phase1-4")
        _validate_model(
            model,
            baseline,
            storyline,
            controls,
            runtime,
            expected_gate=session["input_gate"],
            expected_sources=session["source_artifacts"],
        )


def submit_w1_phase(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    input_gate: Any,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    """Accept the next Agent-authored phase and extend its evidence chain."""

    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, storyline, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
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
        _fail("W1_PHASE_ORDER_INVALID", "all phases are already sealed")
    if phase not in PHASES or phase != PHASES[len(completed)]:
        _fail("W1_PHASE_ORDER_INVALID", f"next phase is {PHASES[len(completed)]}")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS[phase]):
        _fail(
            "W1_PHASE_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(PHASE_FIELDS[phase])}",
        )
    sealed_payloads = _sealed_phase_payloads(root, session, completed)
    if session.get("contract_revision") == CURRENT_CONTRACT_REVISION:
        _validate_current_phase_candidate(
            phase,
            body,
            sealed_payloads,
            session,
            baseline,
            storyline,
            controls,
            contract_runtime,
        )
    elif phase == "final-world-model":
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("W1_PHASE_PAYLOAD_INVALID", "final model is missing")
        _validate_model(
            model,
            baseline,
            storyline,
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
        "contract_revision": session["contract_revision"],
        "run_id": session["run_id"],
        "stage": "W1",
        "session_id": session["session_id"],
        "thread_id": session["thread_id"],
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "input_gate": session["input_gate"],
        "state_before": session["state_before"],
        "baseline_completion": session["baseline_completion"],
        "upstream_completions": session["upstream_completions"],
        "source_artifacts": session["source_artifacts"],
        "control_bindings": session["control_bindings"],
        "storyline_bindings": session["storyline_bindings"],
        "requirement_bindings": session["requirement_bindings"],
        "fact_dependency_bindings": session["fact_dependency_bindings"],
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
    common_keys = (
        *(("contract_revision",) if "contract_revision" in session else ()),
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
        "requirement_bindings",
        "fact_dependency_bindings",
    )
    for index, phase in enumerate(PHASES, 1):
        path = evidence_root / f"{index:02d}-{phase}.json"
        evidence = _read(path, "W1_EVIDENCE_MISSING")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("W1_EVIDENCE_INVALID", f"{phase} payload is missing")
        expected = {
            "schema_version": "2.0",
            **{key: copy.deepcopy(session[key]) for key in common_keys},
            "stage": "W1",
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        if evidence != expected or set(payload) != set(PHASE_FIELDS[phase]):
            _fail("W1_EVIDENCE_INVALID", f"{phase} evidence binding is invalid")
        if phase == "final-world-model":
            if payload["model"] != model:
                _fail("W1_EVIDENCE_MODEL_MISMATCH", "final evidence differs from model")
        else:
            for field in PHASE_FIELDS[phase]:
                if payload[field] != model[field]:
                    _fail(
                        "W1_EVIDENCE_MODEL_MISMATCH",
                        f"{phase}.{field} differs from final model",
                    )
        previous = rt.sha256_file(path)
        paths.append(path)
    return paths


def _validation(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "W1",
        "verdict": "ready",
        "checks": [
            "schema",
            "B0/S1/gate-lineage",
            "requirement-exact-projection",
            "rule-scope-exception-cost-constraint",
            "system-and-flow-closure",
            "storyline-support-exact-cover",
            "reality-claim-closure",
            "downstream-boundary",
            "completion-binding",
        ],
        "errors": [],
    }


def _check_package_boundary(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.name in _FORBIDDEN_PACKAGE_NAMES:
            _fail("W1_BOUNDARY_VIOLATION", path.name)


def _validate_legacy_upstream_snapshot(
    root: Path,
    *,
    stage: str,
    canonical_name: str,
    canonical_role: str,
    runtime: Any,
) -> None:
    manifest = _read(root / "package-manifest.json", f"W1_{stage}_INVALID")
    completion = _read(root / "stage-completion.json", f"W1_{stage}_INVALID")
    try:
        runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail(f"W1_{stage}_INVALID", str(error))
    canonical = rt.artifact_reference(root / canonical_name, root=root)
    if (
        manifest.get("artifact_roles", {}).get(canonical_role) != canonical
        or completion.get("stage") != stage
        or completion.get("status") != "ready"
        or completion.get("manifest", {}).get("sha256")
        != rt.sha256_file(root / "package-manifest.json")
    ):
        _fail(f"W1_{stage}_INVALID", "legacy upstream snapshot is unbound")
        if path.is_dir() and path.name in {"environments", "events", "characters"}:
            _fail("W1_BOUNDARY_VIOLATION", path.name)


def validate_w1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_package_boundary(root)
    model = _read(root / "world-model.json", "W1_MODEL_MISSING")
    manifest = _read(root / "package-manifest.json", "W1_MANIFEST_INVALID")
    stored = _read(root / "validation.json", "W1_VALIDATION_MISSING")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("W1_MANIFEST_INVALID", str(error))
    current_contract = _is_current_contract(model)
    if not current_contract:
        early_execution = _read(
            root / "execution-record.json", "W1_EXECUTION_INVALID"
        )
        early_session = _read(
            root / "generation-session.json", "W1_SESSION_INVALID"
        )
        early_evidence_paths = _validate_phase_chain(
            root / "generation-evidence",
            session=early_session,
            model=model,
        )
        early_catalog = {
            item["identity"]: item["artifact"]
            for item in early_execution.get("implementation_catalog", [])
        }
        for identity in _implementation_paths():
            reference = early_catalog.get(identity)
            if reference is None:
                _fail("W1_LEGACY_PROVENANCE_UNTRUSTED", identity)
            try:
                rt.verify_artifact_reference(reference, root=root)
            except Exception as error:
                _fail("W1_LEGACY_PROVENANCE_UNTRUSTED", str(error))
        _validate_legacy_package_provenance(
            model,
            early_session,
            early_evidence_paths,
            early_catalog,
        )
    copied_b0 = root / "sources" / "B0"
    copied_s1 = root / "sources" / "S1"
    if current_contract:
        try:
            rt.validate_baseline_package(copied_b0, runtime=contract_runtime)
        except Exception as error:
            _fail("W1_B0_INVALID", str(error))
        try:
            s1_runtime.validate_s1_package(copied_s1, runtime=contract_runtime)
        except Exception as error:
            _fail("W1_S1_INVALID", str(error))
    else:
        _validate_legacy_upstream_snapshot(
            copied_b0,
            stage="B0",
            canonical_name="author-control-baseline.json",
            canonical_role="baseline",
            runtime=contract_runtime,
        )
        _validate_legacy_upstream_snapshot(
            copied_s1,
            stage="S1",
            canonical_name="storyline-architecture.json",
            canonical_role="canonical",
            runtime=contract_runtime,
        )
    baseline = _read(
        copied_b0 / "author-control-baseline.json", "W1_B0_INVALID"
    )
    storyline = _read(
        copied_s1 / "storyline-architecture.json", "W1_S1_INVALID"
    )
    controls = _controls(copied_b0, baseline)
    gate = _read(root / "input-gate.json", "W1_GATE_MISSING")
    try:
        contract_runtime.validate(gate, "input-gate.schema.json")
    except Exception as error:
        _fail("W1_GATE_INVALID", str(error))
    gate_reference = {
        "path": model["input_gate"]["path"],
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    if not gate_reference["path"].endswith("/input-gate.json"):
        _fail("W1_GATE_REFERENCE_MISMATCH", "gate path is not package-qualified")
    sealed_b0 = gate.get("baseline_completion")
    sealed_upstreams = gate.get("upstream_completions")
    if (
        not isinstance(sealed_b0, Mapping)
        or not isinstance(sealed_upstreams, list)
        or len(sealed_upstreams) != 1
        or not isinstance(sealed_upstreams[0], Mapping)
    ):
        _fail("W1_GATE_INVALID", "stored gate does not select one B0 and S1")
    b0_reference = _sealed_upstream_reference(
        copied_b0,
        sealed_b0,
        stage="B0",
        run_id=model["run_id"],
        previous_stage_completions=[],
        runtime=contract_runtime,
    )
    s1_reference = _sealed_upstream_reference(
        copied_s1,
        sealed_upstreams[0],
        stage="S1",
        run_id=model["run_id"],
        previous_stage_completions=[],
        runtime=contract_runtime,
    )
    copied_s1_b0_completion = (
        copied_s1 / "sources" / "B0" / "stage-completion.json"
    )
    if (
        not copied_s1_b0_completion.is_file()
        or rt.sha256_file(copied_s1_b0_completion) != b0_reference["sha256"]
        or rt.canonical_sha256(
            _read(copied_s1_b0_completion, "W1_BASELINE_MISMATCH")
        )
        != b0_reference["sha256"]
    ):
        _fail("W1_BASELINE_MISMATCH", "S1 does not bind the packaged B0")
    if (
        gate.get("target_stage") != "W1"
        or gate.get("run_id") != model["run_id"]
        or gate.get("baseline_completion") != b0_reference
        or gate.get("upstream_completions") != [s1_reference]
    ):
        _fail("W1_GATE_INVALID", "stored gate has wrong W1 topology")
    expected_sources = _source_artifacts(copied_b0, copied_s1)
    _validate_model(
        model,
        baseline,
        storyline,
        controls,
        contract_runtime,
        expected_gate=gate_reference,
        expected_sources=expected_sources,
    )
    if manifest["artifact_roles"]["canonical"] != rt.artifact_reference(
        root / "world-model.json", root=root
    ):
        _fail("W1_MANIFEST_INVALID", "canonical role does not bind world-model")
    execution = _read(root / "execution-record.json", "W1_EXECUTION_INVALID")
    if (
        execution.get("input_gate") != gate_reference
        or execution.get("baseline_completion") != b0_reference
        or execution.get("upstream_completions") != [s1_reference]
        or execution.get("output_sha256") != rt.canonical_sha256(model)
    ):
        _fail("W1_EXECUTION_INVALID", "execution lineage is stale")
    session = _read(root / "generation-session.json", "W1_SESSION_INVALID")
    session_thread = session.get("thread_id")
    if not isinstance(session_thread, str) or not session_thread.strip():
        _fail("W1_SESSION_INVALID", "session thread is missing")
    expected_session = {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "W1",
        "session_id": _session_id(
            session_thread, gate_reference, b0_reference, s1_reference
        ),
        "thread_id": session_thread,
        "input_gate": gate_reference,
        "state_before": gate.get("run_state"),
        "baseline_completion": b0_reference,
        "upstream_completions": [s1_reference],
        "source_artifacts": expected_sources,
        "control_bindings": _control_bindings(controls),
        "storyline_bindings": _storyline_bindings(storyline),
        "requirement_bindings": _requirement_bindings(storyline),
        "fact_dependency_bindings": _fact_dependency_bindings(baseline),
        "phases": list(PHASES),
    }
    if "contract_revision" in session:
        expected_session["contract_revision"] = session["contract_revision"]
        if session["contract_revision"] != model.get("contract_revision"):
            _fail("W1_CONTRACT_REVISION_MISMATCH", "session/model revision differs")
    elif model.get("contract_revision") is not None:
        _fail("W1_CONTRACT_REVISION_MISMATCH", "legacy session has current model")
    if session != expected_session:
        _fail("W1_SESSION_INVALID", "session lineage differs from package inputs")
    if execution.get("session_id") != session["session_id"]:
        _fail("W1_SESSION_INVALID", "execution does not bind the session")
    evidence_paths = _validate_phase_chain(
        root / "generation-evidence", session=session, model=model
    )
    evidence_index = _read(
        root / "generation-evidence-index.json", "W1_EVIDENCE_INVALID"
    )
    expected_evidence = [
        rt.artifact_reference(path, root=root) for path in evidence_paths
    ]
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "W1",
        "session_id": session["session_id"],
        "phases": list(PHASES),
        "evidence": expected_evidence,
    }:
        _fail("W1_EVIDENCE_INVALID", "evidence index is stale")
    catalog = {
        item["identity"]: item["artifact"]
        for item in execution.get("implementation_catalog", [])
    }
    for identity, current in _implementation_paths().items():
        reference = catalog.get(identity)
        if reference is None:
            _fail("W1_IMPLEMENTATION_STALE", identity)
        try:
            rt.verify_artifact_reference(reference, root=root)
        except Exception as error:
            _fail("W1_IMPLEMENTATION_STALE", str(error))
        if current_contract and reference["sha256"] != rt.sha256_file(current):
            _fail("W1_IMPLEMENTATION_STALE", identity)
    if not current_contract:
        _validate_legacy_package_provenance(
            model,
            session,
            evidence_paths,
            catalog,
        )
    if require_completion:
        completion_path = root / "stage-completion.json"
        completion = _read(completion_path, "W1_COMPLETION_MISSING")
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("W1_COMPLETION_INVALID", str(error))
        manifest_ref = completion.get("manifest")
        manifest_path = (
            manifest_ref.get("path") if isinstance(manifest_ref, Mapping) else ""
        )
        logical_prefix = PurePosixPath(manifest_path).parent.as_posix()
        if (
            not (
                logical_prefix == "W1"
                or logical_prefix.startswith("W1/")
            )
            or completion.get("run_id") != model["run_id"]
            or completion.get("stage") != "W1"
            or completion.get("status") != "ready"
            or completion.get("session_id") != session["session_id"]
            or completion.get("manifest")
            != {
                "path": _logical(logical_prefix, "package-manifest.json"),
                "sha256": rt.sha256_file(root / "package-manifest.json"),
            }
            or completion.get("validation")
            != {
                "path": _logical(logical_prefix, "validation.json"),
                "sha256": rt.sha256_file(root / "validation.json"),
            }
            or completion.get("input_gate") != gate_reference
            or completion.get("state_before") != gate.get("run_state")
            or completion.get("previous_stage_completions") != [s1_reference]
            or completion.get("return_binding") != gate.get("return_binding")
        ):
            _fail(
                "W1_COMPLETION_BINDING_MISMATCH",
                "completion does not bind W1 inputs and package",
            )
    expected_validation = _validation(model["run_id"])
    if stored != expected_validation:
        _fail("W1_VALIDATION_STALE", "stored validation differs from runtime")
    return expected_validation


def run_w1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controlled_workspace: str | Path,
    logical_package_path: str = "W1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> W1RunReceipt:
    destination = Path(package_root).resolve()
    if _path_lexists(destination):
        _fail("W1_OUTPUT_EXISTS", str(destination))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("W1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    workspace = Path(controlled_workspace).resolve()
    session, baseline, storyline, controls = _validated_session(
        workspace,
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    final_evidence = _read(
        workspace
        / "generation-evidence"
        / f"{len(PHASES):02d}-{PHASES[-1]}.json",
        "W1_EVIDENCE_MISSING",
    )
    final_payload = final_evidence.get("payload")
    if not isinstance(final_payload, Mapping) or not isinstance(
        final_payload.get("model"), Mapping
    ):
        _fail("W1_EVIDENCE_INVALID", "final model evidence is missing")
    model = copy.deepcopy(dict(final_payload["model"]))
    _validate_phase_chain(
        workspace / "generation-evidence", session=session, model=model
    )
    _validate_model(
        model,
        baseline,
        storyline,
        controls,
        contract_runtime,
        expected_gate=input_gate.reference,
        expected_sources=session["source_artifacts"],
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = _create_package_staging(destination)
    try:
        shutil.copytree(
            Path(baseline_package).resolve(), staging / "sources" / "B0"
        )
        shutil.copytree(
            Path(storyline_package).resolve(), staging / "sources" / "S1"
        )
        _write(staging / "input-gate.json", input_gate.data)
        expected_sources = _source_artifacts(
            staging / "sources" / "B0", staging / "sources" / "S1"
        )
        if expected_sources != session["source_artifacts"]:
            _fail("W1_SOURCE_ARTIFACT_MISMATCH", "staged inputs changed")
        _write(staging / "world-model.json", model)
        evidence_refs: list[dict[str, str]] = []
        for index, phase in enumerate(PHASES, 1):
            source = (
                workspace / "generation-evidence" / f"{index:02d}-{phase}.json"
            )
            target = staging / "generation-evidence" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            evidence_refs.append(rt.artifact_reference(target, root=staging))
        evidence_index = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "W1",
            "session_id": session["session_id"],
            "phases": list(PHASES),
            "evidence": evidence_refs,
        }
        _write(staging / "generation-evidence-index.json", evidence_index)
        _write(staging / "generation-session.json", session)
        implementation_refs: list[dict[str, str]] = []
        implementation_catalog: list[dict[str, Any]] = []
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
            "stage": "W1",
            "operation": "controlled-world-model-generation",
            "session_id": session["session_id"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "baseline_completion": session["baseline_completion"],
            "upstream_completions": session["upstream_completions"],
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "output_sha256": rt.canonical_sha256(model),
        }
        _write(staging / "execution-record.json", execution)
        (staging / "world-preview.md").write_text(
            "# World model\n\n"
            + "\n".join(
                f"- **{fact['id']} ({fact['kind']})**: {fact['statement']}"
                for fact in model["world_facts"]
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
            "stage": "W1",
            "package_profile": "generated-model",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "canonical": by_path["world-model.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
                "preview": by_path["world-preview.md"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_w1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0",
            "run_id": baseline["run_id"],
            "stage": "W1",
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
            "W1",
            _logical(logical_package_path, "stage-completion.json"),
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_w1_package(staging, runtime=contract_runtime)
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=sealed,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
        )
        _publish_package_staging(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return W1RunReceipt(
        package_root=destination,
        model=copy.deepcopy(model),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
    )


__all__ = [
    "PHASES",
    "PHASE_FIELDS",
    "W1Error",
    "W1RunReceipt",
    "run_w1",
    "start_w1_session",
    "submit_w1_phase",
    "validate_w1_package",
]
