#!/usr/bin/env python3
"""Deterministic HP1 assembler; owns packaging, never HLD semantics."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

SKILL = "novel-hld-package-assembler"
STAGE = "HP1"
HARNESS = "novel-hld-autonomous"
VERSION = "0.1.0"
SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
HARNESS_ROOT = REPO_ROOT / "harnesses" / HARNESS
sys.path.insert(0, str(HARNESS_ROOT))

from runtime.canonical import ContractError  # noqa: E402
from runtime.hdd import project_unresolved  # noqa: E402
from runtime.schema_catalog import SchemaCatalog  # noqa: E402
from runtime.package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile  # noqa: E402

UPSTREAM = ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1")
DESIGN_STAGES = ("HA1", "HS1", "HC1", "HI1", "HR1", "HK1")
CANONICAL_FILES = {
    "HA1": "narrative-architecture.json",
    "HS1": "storyline-choreography.json",
    "HC1": "character-arc-placement.json",
    "HI1": "narrative-information-architecture.json",
    "HR1": "rhythm-continuity-architecture.json",
    "HK1": "key-scene-function-map.json",
}
MAIN_ROLES = {
    "HB0": "hb0_control_baseline",
    **{stage: f"{stage.lower()}_canonical" for stage in DESIGN_STAGES},
    "HQ1": "hq1_semantic_review",
}
SCHEMA_FILES = (
    "novel-hld-package.schema.json", "hld-cross-index.schema.json",
    "hld-traceability-matrix.schema.json", "lld-handoff.schema.json",
    "assembly-execution.schema.json", "hp1-validation.schema.json",
)
LEGACY_LWR_FIELDS = (
    "id", "hkf_ids", "grouping_rationale", "chapter_shell_ids", "entry_state",
    "exit_state", "character_ids", "environment_ids", "storyline_ids", "event_ids",
    "pov_constraints", "knowledge_boundaries", "prohibitions", "required_elaboration",
    "lld_freedom", "acceptance_criteria",
)
CANONICAL_LWR_FIELDS = (
    "id", "hkf_ids", "merge_split_rationale", "entry_state", "exit_state",
    "required_elaboration", "lld_freedoms", "prohibitions", "acceptance_criteria",
)
READY_TOP_FILES = {
    "novel-hld-package.json", "novel-hld-spec.md", "hld-cross-index.json",
    "hld-traceability-matrix.json", "hld-traceability-matrix.md", "lld-handoff.json",
    "assembly-execution.json", "validation.json", "package-manifest.json",
    "stage-completion.json",
}
BLOCKED_FILES = {"gate-data.json", "blocked-report.json", "validation.json", "result-manifest.json"}
class RuntimeFailure(RuntimeError):
    pass


class AssemblyBlocked(RuntimeError):
    def __init__(self, code: str, evidence: str, affected_ids: Iterable[str] = ()):
        super().__init__(code)
        self.code = code
        self.evidence = evidence
        self.affected_ids = sorted(set(affected_ids))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def value_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeFailure(f"invalid JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeFailure(f"JSON root must be object: {path}")
    return value


def _safe_relative(value: Any) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise RuntimeFailure(f"unsafe relative path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeFailure(f"non-normalized relative path: {value!r}")
    return Path(*parts)


def resolve_inside(root: Path, relative: Any, *, file_only: bool = True, must_exist: bool = True) -> Path:
    candidate = (root / _safe_relative(relative)).resolve(strict=must_exist)
    try:
        candidate.relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise RuntimeFailure(f"path escapes workspace: {relative}") from error
    if must_exist and file_only and not candidate.is_file():
        raise RuntimeFailure(f"not a file: {relative}")
    return candidate


def ref(path: Path, root: Path, role: str) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    return {"role": role, "path": resolved.relative_to(root.resolve(strict=True)).as_posix(), "sha256": file_hash(resolved)}


def output_ref(path: Path, package: Path, context: "Context", role: str) -> dict[str, str]:
    """Bind staged bytes to the package's canonical post-commit location."""
    relative = path.resolve(strict=True).relative_to(package.resolve(strict=True))
    target = (context.output / relative).relative_to(context.workspace).as_posix()
    return {"role": role, "path": target, "sha256": file_hash(path)}


def verify_ref(value: Mapping[str, Any], root: Path, role: str | None = None) -> Path:
    if set(value) != {"role", "path", "sha256"}:
        raise RuntimeFailure("file reference fields must be role/path/sha256")
    if role is not None and value.get("role") != role:
        raise RuntimeFailure(f"wrong reference role: {value.get('role')} != {role}")
    path = resolve_inside(root, value.get("path"))
    if not hmac.compare_digest(file_hash(path), str(value.get("sha256"))):
        raise RuntimeFailure(f"file hash mismatch: {value.get('path')}")
    return path


def implementation_sha256() -> str:
    digest = hashlib.sha256()
    paths = [
        SCRIPT_PATH,
        HARNESS_ROOT / "runtime" / "schema_catalog.py",
        HARNESS_ROOT / "runtime" / "package_envelope.py",
    ]
    paths.extend(SKILL_ROOT / "references" / name for name in SCHEMA_FILES)
    for path in paths:
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _schema_catalog() -> SchemaCatalog:
    documents: dict[str, Any] = {}
    for path in sorted((HARNESS_ROOT / "schemas").glob("*.schema.json")):
        documents[f"harness::{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for name in SCHEMA_FILES:
        path = SKILL_ROOT / "references" / name
        documents[f"hp1::{name}"] = json.loads(path.read_text(encoding="utf-8"))
    return SchemaCatalog.from_documents(documents)


def _schema_validate(catalog: SchemaCatalog, value: Any, schema: str, *, blocked: bool = False) -> None:
    try:
        catalog.validate(value, schema)
    except Exception as error:
        if blocked:
            raise AssemblyBlocked("HP1_SCHEMA_INVALID", str(error)) from error
        raise RuntimeFailure(str(error)) from error


@dataclass
class Context:
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    gate: dict[str, Any]
    roles: dict[str, Path]
    catalog: SchemaCatalog
    output: Path


def _required_roles() -> set[str]:
    roles = {"hb0_source_index"}
    for stage in UPSTREAM:
        roles.update({MAIN_ROLES[stage], f"{stage.lower()}_manifest", f"{stage.lower()}_validation", f"{stage.lower()}_completion"})
    return roles


def load_context(work_order_path: Path) -> Context:
    path = work_order_path.resolve(strict=True)
    workspace = path.parent.resolve(strict=True)
    catalog = _schema_catalog()
    work_order = read_json(path)
    _schema_validate(catalog, work_order, "work-order.schema.json")
    if work_order["stage"] != STAGE or work_order["exact_owner_skill"] != SKILL:
        raise RuntimeFailure("work order owner/stage mismatch")
    if work_order["action"] != "execute" or work_order["submission_status"] != "open":
        raise RuntimeFailure("HP1 requires one open execute work order")
    if work_order["implementation_sha256"] != implementation_sha256():
        raise RuntimeFailure("HP1 implementation hash mismatch")
    if work_order["mode"] not in {"forward", "return_resolution"}:
        raise RuntimeFailure("unsupported HP1 mode")
    if work_order["unresolved_projection"]:
        raise RuntimeFailure("HP1 has no source access and cannot receive unresolved projection")
    allowlist = work_order["file_allowlist"]
    roles: dict[str, Path] = {}
    for item in allowlist:
        role = item["role"]
        if role in roles:
            raise RuntimeFailure(f"duplicate allowlist role: {role}")
        roles[role] = verify_ref(item, workspace, role)
    expected_roles = _required_roles()
    if set(roles) != expected_roles:
        raise RuntimeFailure(f"HP1 allowlist roles mismatch: missing={sorted(expected_roles-set(roles))} extra={sorted(set(roles)-expected_roles)}")
    roles["input_gate"] = verify_ref(work_order["input_gate_ref"], workspace, "input_gate")
    roles["state_before"] = verify_ref(work_order["state_before_ref"], workspace, "state_before")
    gate = read_json(roles["input_gate"])
    _schema_validate(catalog, gate, "input-gate.schema.json")
    for key in ("harness", "hld_run_id", "stage", "mode", "state_before_ref", "upstream_completions", "exact_owner_skill", "owner_version", "implementation_sha256", "return_binding", "unresolved_projection", "revision_plan_ref", "revision_plan_state_ref", "file_allowlist"):
        gate_key = "state_before_ref" if key == "state_before_ref" else key
        if gate[gate_key] != work_order[key]:
            raise RuntimeFailure(f"input gate/work order mismatch: {key}")
    output = resolve_inside(workspace, work_order["output_directory"], must_exist=False, file_only=False)
    if output.exists() or (workspace / "stage-result.json").exists():
        raise RuntimeFailure("HP1 output/result already exists")
    return Context(workspace, path, work_order, gate, roles, catalog, output)


def _manifest_binds(manifest: Mapping[str, Any], path: Path, sha256: str) -> bool:
    return any(item.get("path") == path.name and item.get("sha256") == sha256 for item in manifest.get("files", []))


def admit_upstreams(context: Context) -> dict[str, dict[str, Any]]:
    refs = context.work_order["upstream_completions"]
    if len(refs) != len(UPSTREAM):
        raise AssemblyBlocked("HP1_UPSTREAM_TOPOLOGY", "expected eight ordered completions")
    admitted: dict[str, dict[str, Any]] = {}
    authority: Any = None
    for stage, artifact in zip(UPSTREAM, refs):
        main = context.roles[MAIN_ROLES[stage]]
        manifest_path = context.roles[f"{stage.lower()}_manifest"]
        validation_path = context.roles[f"{stage.lower()}_validation"]
        completion_path = context.roles[f"{stage.lower()}_completion"]
        expected = {
            "path": main.relative_to(context.workspace).as_posix(), "sha256": file_hash(main),
            "manifest_path": manifest_path.relative_to(context.workspace).as_posix(), "manifest_sha256": file_hash(manifest_path),
            "completion_path": completion_path.relative_to(context.workspace).as_posix(), "completion_sha256": file_hash(completion_path),
        }
        if artifact != expected:
            raise AssemblyBlocked("HP1_UPSTREAM_BINDING_DRIFT", stage, [stage])
        manifest = read_json(manifest_path)
        validation = read_json(validation_path)
        completion = read_json(completion_path)
        try:
            _schema_validate(context.catalog, manifest, "package-manifest.schema.json")
            _schema_validate(context.catalog, completion, "stage-completion.schema.json")
            validate_ready_profile(manifest_path.parent, stage)
            validate_manifest(manifest_path.parent, manifest)
            validate_completion_bindings(context.workspace, manifest_path.parent, completion)
        except (ContractError, RuntimeFailure, OSError) as error:
            raise AssemblyBlocked("HP1_UPSTREAM_ENVELOPE_INVALID", f"{stage}: {error}", [stage]) from error
        if completion.get("stage") != stage or completion.get("hld_run_id") != context.work_order["hld_run_id"] or completion.get("status") != "ready":
            raise AssemblyBlocked("HP1_UPSTREAM_NOT_CURRENT_READY", stage, [stage])
        if validation.get("status") not in {"pass", "ready"}:
            raise AssemblyBlocked("HP1_UPSTREAM_VALIDATION_FAILED", stage, [stage])
        if not _manifest_binds(manifest, main, file_hash(main)) or not _manifest_binds(manifest, validation_path, file_hash(validation_path)):
            raise AssemblyBlocked("HP1_UPSTREAM_MANIFEST_BINDING_GAP", stage, [stage])
        if completion["manifest_ref"].get("sha256") != file_hash(manifest_path):
            raise AssemblyBlocked("HP1_COMPLETION_MANIFEST_DRIFT", stage, [stage])
        if completion["validation_ref"].get("sha256") != file_hash(validation_path):
            raise AssemblyBlocked("HP1_COMPLETION_VALIDATION_DRIFT", stage, [stage])
        canonical_binding = completion.get("canonical_artifacts", [completion.get("canonical_artifact")])
        if not isinstance(canonical_binding, list) or not any(isinstance(item, dict) and item.get("sha256") == file_hash(main) for item in canonical_binding):
            raise AssemblyBlocked("HP1_COMPLETION_CANONICAL_DRIFT", stage, [stage])
        value = read_json(main)
        if stage in DESIGN_STAGES:
            if value.get("stage") != stage or value.get("hld_run_id") != context.work_order["hld_run_id"] or value.get("status") != "ready":
                raise AssemblyBlocked("HP1_CANONICAL_IDENTITY_DRIFT", stage, [stage])
            required = ("authority_partition", "design_decisions", "decision_dependencies", "open_items")
            if any(key not in value for key in required):
                raise AssemblyBlocked("HP1_CANONICAL_INCOMPLETE", stage, [stage])
            source_authority = {key: value["authority_partition"].get(key) for key in ("source_classifications", "source_open_items", "source_authority_classes")}
            if authority is None:
                authority = source_authority
            elif source_authority != authority:
                raise AssemblyBlocked("HP1_AUTHORITY_PARTITION_DRIFT", stage, [stage])
        admitted[stage] = {"main": value, "main_path": main, "manifest": manifest, "validation": validation, "completion": completion}
    control = admitted["HB0"]["main"]
    if control.get("stage") != "HB0" or control.get("status") != "ready":
        raise AssemblyBlocked("HP1_HB0_INVALID", "HB0 control baseline is not ready")
    hb0_source_authority = {key: control.get("authority_partition", {}).get(key) for key in ("source_classifications", "source_open_items", "source_authority_classes")}
    if authority is not None and hb0_source_authority != authority:
        raise AssemblyBlocked("HP1_AUTHORITY_PARTITION_DRIFT", "HB0 vs design stages")
    source_index_path = context.roles["hb0_source_index"]
    hb0_manifest = admitted["HB0"]["manifest"]
    if not _manifest_binds(hb0_manifest, source_index_path, file_hash(source_index_path)):
        raise AssemblyBlocked("HP1_UPSTREAM_MANIFEST_BINDING_GAP", "HB0 source index", ["HB0"])
    source_index = read_json(source_index_path)
    if source_index.get("stage") != "HB0" or source_index.get("hld_run_id") != context.work_order["hld_run_id"] or source_index.get("status") != "ready":
        raise AssemblyBlocked("HP1_HB0_SOURCE_INDEX_INVALID", "HB0 source index")
    admitted["HB0"]["source_index"] = source_index
    review = admitted["HQ1"]["main"]
    if review.get("stage") != "HQ1" or review.get("verdict") != "pass" or review.get("findings") != []:
        raise AssemblyBlocked("HP1_HQ1_NOT_PASS", "HQ1 must be pass with findings=[]", ["HQ1"])
    return admitted


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _walk_ids(value: Any, path: str = "") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            yield value["id"], path, value
        for key in sorted(value):
            yield from _walk_ids(value[key], path + "/" + _pointer_escape(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_ids(child, path + f"/{index}")


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)


def _named_string_values(value: Any, field: str) -> Iterable[str]:
    """Yield only explicit lineage fields, never IDs inferred by prefix."""
    if isinstance(value, dict):
        selected = value.get(field)
        if isinstance(selected, list):
            for item in selected:
                if isinstance(item, str):
                    yield item
        for child in value.values():
            yield from _named_string_values(child, field)
    elif isinstance(value, list):
        for child in value:
            yield from _named_string_values(child, field)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def build_baseline_controls(admitted: Mapping[str, Any]) -> list[dict[str, Any]]:
    registry = admitted["HB0"]["main"].get("control_registry")
    entries = admitted["HB0"]["source_index"].get("entries")
    if not isinstance(registry, list) or not isinstance(entries, list):
        raise AssemblyBlocked("HP1_BASELINE_INDEX_INVALID", "HB0 control/source index")
    indexed: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("source_id"), str):
            indexed.setdefault(entry["source_id"], []).append(entry)
    controls = []
    for item in sorted(registry, key=lambda value: value.get("source_id", "")):
        source_id = item.get("source_id") if isinstance(item, dict) else None
        if not isinstance(source_id, str) or source_id not in indexed:
            raise AssemblyBlocked("HP1_BASELINE_INDEX_GAP", str(source_id), [str(source_id)])
        matches = [
            source for source in indexed[source_id]
            if source.get("domain") == item.get("domain")
            and source.get("locator") == item.get("locator")
            and source.get("workspace_source_ref") == item.get("workspace_source_ref")
            and source.get("value_sha256") == item.get("source_value_sha256")
        ]
        if len(matches) != 1:
            raise AssemblyBlocked("HP1_BASELINE_INDEX_DRIFT", source_id, [source_id])
        controls.append({
            "source_id": source_id, "domain": item["domain"], "classification": item["classification"],
            "open_item": item["open_item"], "authority_class": item["authority_class"],
            "source_value_sha256": item["source_value_sha256"],
        })
    return controls


def aggregate_authority_partition(admitted: Mapping[str, Any]) -> dict[str, Any]:
    baseline = admitted["HB0"]["main"]["authority_partition"]
    ownership = {key: set() for key in ("source_projection", "hld_owned", "preserved_open", "lld_freedom")}
    for stage in DESIGN_STAGES:
        stage_ownership = admitted[stage]["main"]["authority_partition"].get("hld_ownership", {})
        if set(stage_ownership) != set(ownership):
            raise AssemblyBlocked("HP1_HLD_OWNERSHIP_INVALID", stage, [stage])
        for key in ownership:
            values = stage_ownership[key]
            if not isinstance(values, list) or len(values) != len(set(values)):
                raise AssemblyBlocked("HP1_HLD_OWNERSHIP_INVALID", f"{stage}.{key}", [stage])
            ownership[key].update(values)
    return {
        "source_classifications": baseline["source_classifications"],
        "source_open_items": baseline["source_open_items"],
        "source_authority_classes": baseline["source_authority_classes"],
        "hld_ownership": {key: sorted(values) for key, values in ownership.items()},
    }


def build_cross_index(admitted: Mapping[str, Any], baseline_controls: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, tuple[str, Any]]]:
    entries = []
    objects: dict[str, tuple[str, Any]] = {}
    for index, value in enumerate(baseline_controls):
        source_id = value["source_id"]
        objects[source_id] = ("HB0", value)
        entries.append({
            "id": source_id, "owner_stage": "HB0", "model_path": "novel-hld-package.json",
            "locator": f"/baseline_controls/{index}", "value_sha256": value_hash(value), "kind": "source_control",
        })
    for stage in DESIGN_STAGES:
        model = admitted[stage]["main"]
        model_path = f"canonical-models/{CANONICAL_FILES[stage]}"
        for stable_id, locator, value in _walk_ids(model):
            if stable_id in objects:
                raise AssemblyBlocked("HP1_DUPLICATE_STABLE_ID", stable_id, [stable_id])
            objects[stable_id] = (stage, value)
            entries.append({
                "id": stable_id, "owner_stage": stage, "model_path": model_path,
            "locator": locator, "value_sha256": value_hash(value), "kind": "canonical_object",
            })
    entries.sort(key=lambda item: item["id"])
    return {"schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": admitted["HB0"]["completion"]["hld_run_id"], "status": "ready", "entries": entries}, objects


def aggregate_dependencies(admitted: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Any]]:
    control = admitted["HB0"]["main"]
    unresolved = control.get("unresolved_register", [])
    all_hdds: dict[str, list[dict[str, Any]]] = {}
    for stage in DESIGN_STAGES:
        for hdd in admitted[stage]["main"].get("decision_dependencies", []):
            if not isinstance(hdd, dict) or hdd.get("owner_stage") != stage or not isinstance(hdd.get("source_id"), str):
                raise AssemblyBlocked("HP1_HDD_INVALID", stage, [stage])
            all_hdds.setdefault(hdd["source_id"], []).append(hdd)
    for hdd in admitted["HQ1"]["main"].get("decision_dependencies", []):
        if not isinstance(hdd, dict) or hdd.get("owner_stage") != "HQ1" or not isinstance(hdd.get("source_id"), str):
            raise AssemblyBlocked("HP1_HDD_INVALID", "HQ1", ["HQ1"])
        all_hdds.setdefault(hdd["source_id"], []).append(hdd)
    summaries = []
    resolutions: list[Any] = []
    unresolved_ids = [item.get("source_id") for item in unresolved]
    if any(not isinstance(item, str) for item in unresolved_ids) or len(unresolved_ids) != len(set(unresolved_ids)):
        raise AssemblyBlocked("HP1_UNRESOLVED_REGISTER_INVALID", "HB0 unresolved register")
    reviews = admitted["HQ1"]["main"].get("decision_dependency_review", [])
    reviewed_sources = {item.get("source_id") for item in reviews if isinstance(item, dict) and item.get("status") == "covered"}
    projections = project_unresolved(unresolved)
    source_entries = {item.get("source_id"): item for item in admitted["HB0"]["source_index"].get("entries", []) if isinstance(item, dict)}
    for source_id in sorted(unresolved_ids):
        hdds = sorted(all_hdds.get(source_id, []), key=lambda item: (item.get("owner_stage", ""), item.get("id", "")))
        if not hdds or (source_id in projections["HQ1"] and source_id not in reviewed_sources):
            raise AssemblyBlocked("HP1_HDD_COVERAGE_GAP", source_id, [source_id])
        owners = [item.get("owner_stage") for item in hdds]
        if len(owners) != len(set(owners)):
            raise AssemblyBlocked("HP1_HDD_DUPLICATE_OWNER", source_id, [source_id])
        source_entry = source_entries.get(source_id)
        if source_entry is None:
            raise AssemblyBlocked("HP1_HDD_SOURCE_UNINDEXED", source_id, [source_id])
        expected_owners = sorted(stage for stage, source_ids in projections.items() if source_id in source_ids)
        if sorted(owners) != expected_owners:
            raise AssemblyBlocked("HP1_HDD_COVERAGE_GAP", f"{source_id}: expected={expected_owners} actual={sorted(owners)}", [source_id])
        dispositions = [item.get("disposition") for item in hdds]
        if "required_now" in dispositions:
            raise AssemblyBlocked("HP1_REQUIRED_NOW_SURVIVED_REVIEW", source_id, [source_id])
        resolution_refs = sorted({item.get("resolution_ref") for item in hdds if item.get("resolution_ref") is not None})
        if "resolved_by_external_author_event" in dispositions:
            if any(item != "resolved_by_external_author_event" for item in dispositions) or len(resolution_refs) != 1:
                raise AssemblyBlocked("HP1_HDD_RESOLUTION_CONFLICT", source_id, [source_id])
            aggregate = "resolved"
            resolution = resolution_refs[0]
            resolutions.append(resolution)
        elif all(item == "not_needed_for_current_stage" for item in dispositions):
            aggregate = "not_needed_for_current_hld"
            resolution = None
        elif all(item in {"not_needed_for_current_stage", "conditional_structure_preserves_open"} for item in dispositions):
            aggregate = "conditionally_preserved"
            resolution = None
        else:
            raise AssemblyBlocked("HP1_HDD_DISPOSITION_INVALID", source_id, [source_id])
        summaries.append({
            "source_id": source_id,
            "stage_hdd_refs": [{"id": item["id"], "owner_stage": item["owner_stage"], "value_sha256": value_hash(item)} for item in hdds],
            "aggregate_disposition": aggregate,
            "resolution_ref": resolution,
        })
    preserved = [{"origin_stage": "HB0", "value_json": canonical_json(item), "value_sha256": value_hash(item)} for item in unresolved]
    for stage in DESIGN_STAGES:
        preserved.extend({"origin_stage": stage, "value_json": canonical_json(item), "value_sha256": value_hash(item)} for item in admitted[stage]["main"].get("open_items", []))
    return summaries, preserved, sorted(set(resolutions))


def build_handoff(admitted: Mapping[str, Any], package_ref: Mapping[str, Any], summaries: list[dict[str, Any]], preserved: list[dict[str, Any]], resolutions: list[Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    hk1 = admitted["HK1"]["main"]
    lwrs = hk1.get("lld_work_requirements")
    if not isinstance(lwrs, list) or not lwrs:
        raise AssemblyBlocked("HP1_LWR_MISSING", "HK1.lld_work_requirements")
    lwks = []
    lwr_map: dict[str, dict[str, Any]] = {}
    lwk_ids: set[str] = set()
    hkfs = {item.get("id"): item for item in hk1.get("key_scene_functions", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    chapter_shells = admitted["HA1"]["main"].get("chapter_shells", [])
    lwk_source_units: dict[str, list[str]] = {}

    def unique(values: Iterable[str]) -> list[str]:
        return list(dict.fromkeys(values))

    def project_current_lwr(lwr: Mapping[str, Any]) -> dict[str, Any]:
        functions = [hkfs.get(identifier) for identifier in lwr["hkf_ids"]]
        if any(item is None for item in functions):
            raise AssemblyBlocked("HP1_LWR_HKF_MISSING", str(lwr["id"]), list(lwr["hkf_ids"]))
        typed_functions = [item for item in functions if isinstance(item, dict)]
        unit_ids = unique(str(item["unit_id"]) for item in typed_functions)
        chapters = [
            str(item["id"]) for item in chapter_shells
            if isinstance(item, dict) and item.get("parent_unit_id") in unit_ids and isinstance(item.get("id"), str)
        ]
        if not chapters:
            raise AssemblyBlocked("HP1_LWR_CHAPTER_SHELL_GAP", str(lwr["id"]), list(lwr["hkf_ids"]))
        return {
            "hkf_ids": list(lwr["hkf_ids"]),
            "grouping_rationale": lwr["merge_split_rationale"],
            "chapter_shell_ids": chapters,
            "entry_state": lwr["entry_state"],
            "exit_state": lwr["exit_state"],
            "exit_state_refs": unique([
                str(lwr["exit_state"]),
                *(value for item in typed_functions for value in item["knowledge_after"]),
                *(str(item["required_state_change"]) for item in typed_functions if item.get("required_state_change")),
            ]),
            "character_ids": unique(value for item in typed_functions for value in item["character_refs"]),
            "environment_ids": unique(value for item in typed_functions for value in item["environment_refs"]),
            "storyline_ids": unique(value for item in typed_functions for value in item["storyline_refs"]),
            "event_ids": unique(value for item in typed_functions for value in item["event_refs"]),
            "pov_constraints": unique(str(item["pov_constraint"]) for item in typed_functions),
            "knowledge_boundaries": unique(value for item in typed_functions for value in [*item["knowledge_before"], *item["knowledge_after"]]),
            "prohibitions": list(lwr["prohibitions"]),
            "required_elaboration": list(lwr["required_elaboration"]),
            "lld_freedom": list(lwr["lld_freedoms"]),
            "acceptance_criteria": list(lwr["acceptance_criteria"]),
        }

    for lwr in lwrs:
        if not isinstance(lwr, dict):
            raise AssemblyBlocked("HP1_LWR_INCOMPLETE", "not-an-object")
        legacy = all(field in lwr for field in LEGACY_LWR_FIELDS)
        current = all(field in lwr for field in CANONICAL_LWR_FIELDS)
        if not legacy and not current:
            missing = [field for field in CANONICAL_LWR_FIELDS if field not in lwr]
            raise AssemblyBlocked("HP1_LWR_INCOMPLETE", ",".join(missing), [str(lwr.get("id"))] if isinstance(lwr, dict) else [])
        source_id = lwr["id"]
        if not isinstance(source_id, str) or not re.fullmatch(r"LWR-[A-Za-z0-9._-]+", source_id):
            raise AssemblyBlocked("HP1_LWR_ID_INVALID", str(source_id))
        if source_id in lwr_map:
            raise AssemblyBlocked("HP1_LWR_DUPLICATE", source_id, [source_id])
        lwk_id = "LWK-" + source_id.split("-", 1)[1]
        if lwk_id in lwk_ids:
            raise AssemblyBlocked("HP1_LWK_COLLISION", lwk_id, [source_id])
        lwk_ids.add(lwk_id)
        projected = {"id": lwk_id, "source_lwr_id": source_id}
        projected.update(
            {field: lwr[field] for field in LEGACY_LWR_FIELDS[1:]}
            if legacy else project_current_lwr(lwr)
        )
        if legacy:
            projected["exit_state_refs"] = [str(lwr["exit_state"])]
        projected["source_value_sha256"] = value_hash(lwr)
        lwks.append(projected)
        lwr_map[source_id] = lwr
        functions = [hkfs[identifier] for identifier in lwr["hkf_ids"]]
        if all(isinstance(item.get("unit_id"), str) for item in functions):
            lwk_source_units[lwk_id] = unique(str(item["unit_id"]) for item in functions)
        else:
            shell_ids = set(projected["chapter_shell_ids"])
            lwk_source_units[lwk_id] = unique(
                str(item["parent_unit_id"]) for item in chapter_shells
                if item.get("id") in shell_ids and isinstance(item.get("parent_unit_id"), str)
            )
        if not lwk_source_units[lwk_id]:
            raise AssemblyBlocked("HP1_LWR_UNIT_LINEAGE_GAP", lwk_id, list(projected["hkf_ids"]))
    hs1 = admitted["HS1"]["main"]
    register_ids = [item.get("source_storyline_id") for item in hs1.get("semantic_storyline_register", [])]
    register_by_id = {item.get("source_storyline_id"): item for item in hs1.get("semantic_storyline_register", [])}
    disposition_items = hs1.get("activation_disposition", [])
    dispositions_by_id = {item.get("source_storyline_id"): item.get("disposition") for item in disposition_items}
    if None in register_ids or len(register_ids) != len(set(register_ids)) or set(dispositions_by_id) != set(register_ids):
        raise AssemblyBlocked("HP1_STORYLINE_REGISTER_INVALID", "HS1 storyline register/disposition mismatch")
    segments_by_id = {item.get("source_storyline_id"): item for item in hs1.get("storyline_segments", [])}
    if None in segments_by_id or len(segments_by_id) != len(hs1.get("storyline_segments", [])):
        raise AssemblyBlocked("HP1_STORYLINE_SEGMENT_INVALID", "HS1 storyline segment identity mismatch")
    expected_by_lwk = {item["id"]: set() for item in lwks}
    storyline_dispositions = []
    for storyline_id in register_ids:
        disposition = dispositions_by_id[storyline_id]
        segment = segments_by_id.get(storyline_id)
        if disposition in {"placed", "background-carried"} and not segment:
            raise AssemblyBlocked("HP1_STORYLINE_PLACEMENT_GAP", storyline_id, [storyline_id])
        if disposition in {"optional-not-activated", "preserved-open"} and segment:
            raise AssemblyBlocked("HP1_STORYLINE_DISPOSITION_CONFLICT", storyline_id, [storyline_id])
        source_units = set(segment.get("unit_ids", [])) if segment else set()
        work_unit_ids = []
        for lwk in lwks:
            if source_units.intersection(lwk_source_units[lwk["id"]]):
                work_unit_ids.append(lwk["id"])
                expected_by_lwk[lwk["id"]].add(storyline_id)
        if disposition in {"placed", "background-carried"} and not work_unit_ids:
            raise AssemblyBlocked("HP1_STORYLINE_WORK_UNIT_GAP", storyline_id, [storyline_id])
        storyline_dispositions.append({
            "storyline_id": storyline_id,
            "reader_name": register_by_id[storyline_id]["reader_name"],
            "disposition": disposition,
            "work_unit_ids": work_unit_ids,
            "absence_reason": None if work_unit_ids else "该故事线保持未激活或开放，不得由详细设计擅自兑现。",
        })
    for lwk in lwks:
        if set(lwk["storyline_ids"]) != expected_by_lwk[lwk["id"]]:
            raise AssemblyBlocked("HP1_STORYLINE_HKF_DRIFT", lwk["id"], sorted(set(lwk["storyline_ids"]) ^ expected_by_lwk[lwk["id"]]))
    shell_ids = [item.get("id") for item in chapter_shells]
    if None in shell_ids or len(shell_ids) != len(set(shell_ids)):
        raise AssemblyBlocked("HP1_CHAPTER_SHELL_IDENTITY_INVALID", "HA1 chapter shell identity mismatch")
    chapter_plans = hs1.get("chapter_storyline_plan")
    if not isinstance(chapter_plans, list) or [item.get("chapter_id") for item in chapter_plans] != shell_ids:
        raise AssemblyBlocked("HP1_CHAPTER_DESIGN_COVERAGE_GAP", "HS1 must design every HA1 chapter shell in exact order", [str(value) for value in shell_ids])
    shell_by_id = {item["id"]: item for item in chapter_shells}
    lwk_by_shell: dict[str, dict[str, Any]] = {}
    for lwk in lwks:
        for shell_id in lwk["chapter_shell_ids"]:
            if shell_id in lwk_by_shell:
                raise AssemblyBlocked("HP1_CHAPTER_WORK_UNIT_COLLISION", shell_id, [shell_id])
            lwk_by_shell[shell_id] = lwk
    if set(lwk_by_shell) != set(shell_ids):
        raise AssemblyBlocked("HP1_CHAPTER_WORK_UNIT_GAP", "each chapter must belong to exactly one LLD work unit", sorted(set(shell_ids) ^ set(lwk_by_shell)))
    chapter_designs = []
    for index, chapter in enumerate(chapter_plans, 1):
        chapter_id = chapter["chapter_id"]
        shell = shell_by_id[chapter_id]
        if chapter.get("chapter_number") != index or chapter.get("parent_unit_id") != shell.get("parent_unit_id"):
            raise AssemblyBlocked("HP1_CHAPTER_DESIGN_LINEAGE_DRIFT", chapter["id"], [chapter["id"], chapter_id])
        lwk = lwk_by_shell[chapter_id]
        chapter_lines = {
            chapter["primary_storyline_id"],
            *chapter["supporting_storyline_ids"],
            *chapter["background_storyline_ids"],
        }
        if not chapter_lines.issubset(set(lwk["storyline_ids"])):
            raise AssemblyBlocked("HP1_CHAPTER_STORYLINE_WORK_UNIT_DRIFT", chapter["id"], sorted(chapter_lines - set(lwk["storyline_ids"])))
        chapter_designs.append({
            "id": chapter_id, "source_design_id": chapter["id"], "chapter_number": index,
            "working_title": chapter["working_title"], "source_unit_id": chapter["parent_unit_id"],
            "work_unit_id": lwk["id"], "core_content": chapter["core_content"],
            "chapter_end_change": chapter["chapter_end_change"],
            "primary_storyline_id": chapter["primary_storyline_id"],
            "supporting_storyline_ids": list(chapter["supporting_storyline_ids"]),
            "background_storyline_ids": list(chapter["background_storyline_ids"]),
            "preserved_open_storyline_ids": list(chapter["preserved_open_storyline_ids"]),
            "content_obligations": list(chapter["content_obligations"]),
            "prohibitions": list(chapter["prohibitions"]),
            "source_value_sha256": value_hash(chapter),
        })
    duration_by_unit = {item.get("unit_id"): item for item in admitted["HR1"]["main"].get("unit_duration_density", [])}
    work_unit_time_windows = []
    for lwk in lwks:
        source_units = lwk_source_units[lwk["id"]]
        if any(unit_id not in duration_by_unit for unit_id in source_units):
            raise AssemblyBlocked("HP1_TIME_WINDOW_GAP", lwk["id"], source_units)
        windows = [duration_by_unit[unit_id] for unit_id in source_units]
        work_unit_time_windows.append({
            "work_unit_id": lwk["id"], "source_unit_ids": source_units,
            "elapsed_start_day": min(item["elapsed_start_day"] for item in windows),
            "elapsed_end_day": max(item["elapsed_end_day"] for item in windows),
            "label": "；".join(unique(str(item["elapsed_label"]) for item in windows)),
        })
    controls=admitted["HB0"]["main"].get("control_registry",[])
    control_ids={item.get("source_id") for item in controls if isinstance(item,dict)}

    def canonical_entities(domain:str,source_path:str,collection:str)->set[str]:
        source_index=admitted["HB0"].get("source_index",{})
        entries=source_index.get("entries") if isinstance(source_index,dict) else None
        if not isinstance(entries,list):
            raise AssemblyBlocked("HP1_SOURCE_ENTITY_INDEX_MISSING",domain)
        pattern=re.compile(rf"/{re.escape(collection)}/(0|[1-9][0-9]*)")
        matched=[]
        for item in entries:
            if not isinstance(item,dict) or item.get("domain")!=domain:
                continue
            source=item.get("source")
            locator=item.get("locator")
            if not isinstance(source,dict) or source.get("path")!=source_path or not isinstance(locator,str) or pattern.fullmatch(locator) is None:
                continue
            if item.get("object_type")!="object" or source.get("root")!="source":
                raise AssemblyBlocked("HP1_SOURCE_ENTITY_INDEX_INVALID",str(item.get("source_id")),[str(item.get("source_id"))])
            source_id=item.get("source_id")
            workspace_ref=item.get("workspace_source_ref")
            if (
                not isinstance(source_id,str)
                or not isinstance(workspace_ref,dict)
                or workspace_ref.get("path")!=f"inputs/source-files/{source_path}"
                or workspace_ref.get("sha256")!=source.get("sha256")
            ):
                raise AssemblyBlocked("HP1_SOURCE_ENTITY_INDEX_INVALID",str(source_id),[str(source_id)])
            matched.append((source_id,locator))
        if not matched:
            discriminator=f"{domain}-definition"
            for item in entries:
                if (
                    not isinstance(item,dict)
                    or item.get("domain")!=domain
                    or item.get("locator")!="/value"
                    or item.get("schema_discriminator")!=discriminator
                    or item.get("object_type")!="object"
                ):
                    continue
                source=item.get("source")
                workspace_ref=item.get("workspace_source_ref")
                source_id=item.get("source_id")
                if (
                    not isinstance(source,dict)
                    or source.get("root")!="source"
                    or not isinstance(source.get("path"),str)
                    or not isinstance(source_id,str)
                    or not isinstance(workspace_ref,dict)
                    or workspace_ref.get("path")!=f"inputs/{source['path']}"
                    or workspace_ref.get("sha256")!=source.get("sha256")
                ):
                    raise AssemblyBlocked("HP1_SOURCE_ENTITY_INDEX_INVALID",str(source_id),[str(source_id)])
                matched.append((source_id,"/value"))
        source_ids=[item[0] for item in matched]
        locators=[item[1] for item in matched]
        if not source_ids or len(source_ids)!=len(set(source_ids)) or len(locators)!=len(set(locators)):
            raise AssemblyBlocked("HP1_SOURCE_ENTITY_INDEX_INVALID",domain,sorted(set(source_ids)))
        missing_controls=sorted(set(source_ids)-control_ids)
        if missing_controls:
            raise AssemblyBlocked("HP1_SOURCE_ENTITY_CONTROL_GAP",domain,missing_controls)
        return set(source_ids)

    expected_characters=canonical_entities("characters","P1/canonical-models/character-system.json","profiles")
    expected_environments=canonical_entities("environments","P1/canonical-models/environment-system.json","environments")
    participation=admitted["HC1"]["main"].get("character_participation_register",[])
    participation_by_id={item.get("character_id"):item for item in participation if isinstance(item,dict)}
    if set(participation_by_id)!=expected_characters:
        missing=sorted(expected_characters-set(participation_by_id));extra=sorted(set(participation_by_id)-expected_characters)
        raise AssemblyBlocked("HP1_CHARACTER_DISPOSITION_GAP",f"missing={missing};extra={extra}",missing or extra)
    character_units={identifier:[item["id"] for item in lwks if identifier in item["character_ids"]] for identifier in sorted(expected_characters)}
    dispositions=[]
    for identifier in sorted(expected_characters):
        source=participation_by_id[identifier];units=character_units[identifier]
        if not units and (source.get("importance")!="context" or not source.get("absence_reason")):
            raise AssemblyBlocked("HP1_CHARACTER_PLACEMENT_GAP",identifier,[identifier])
        dispositions.append({"character_id":identifier,"importance":source["importance"],"disposition":"placed" if units else "context_only","work_unit_ids":units,"absence_reason":source.get("absence_reason")})
    placed_environments={identifier for item in lwks for identifier in item["environment_ids"]}
    missing_environments=sorted(expected_environments-placed_environments)
    if missing_environments:
        raise AssemblyBlocked("HP1_ENVIRONMENT_PLACEMENT_GAP",",".join(missing_environments),missing_environments)
    world=admitted["HA1"]["main"].get("world_setting_architecture")
    if not isinstance(world,dict):
        raise AssemblyBlocked("HP1_WORLD_SETTING_MISSING","HA1.world_setting_architecture")
    cities=world.get("cities",[]);city_ids=[item.get("city_id") for item in cities if isinstance(item,dict)]
    if not city_ids or len(city_ids)!=len(cities) or len(city_ids)!=len(set(city_ids)):
        raise AssemblyBlocked("HP1_CITY_REGISTRY_INVALID","HA1.world_setting_architecture/cities")
    routes=world.get("intercity_routes",[])
    if len(city_ids)>=3 and not routes:
        raise AssemblyBlocked("HP1_MULTI_CITY_ROUTE_GAP",",".join(city_ids),city_ids)
    if len(city_ids)>=4 and len(routes)<4:
        raise AssemblyBlocked("HP1_MULTI_CITY_ROUTE_SHALLOW",f"cities={len(city_ids)};routes={len(routes)}",city_ids)
    if any(item.get("from_city_id") not in city_ids or item.get("to_city_id") not in city_ids or item.get("from_city_id")==item.get("to_city_id") for item in routes):
        raise AssemblyBlocked("HP1_CITY_ROUTE_INVALID","intercity route endpoint drift",city_ids)
    if len(city_ids)>=3:
        reached={city_ids[0]}
        while True:
            expanded=reached|{item["to_city_id"] for item in routes if item["from_city_id"] in reached}|{item["from_city_id"] for item in routes if item["to_city_id"] in reached}
            if expanded==reached:break
            reached=expanded
        if reached!=set(city_ids):raise AssemblyBlocked("HP1_CITY_NETWORK_DISCONNECTED",",".join(sorted(set(city_ids)-reached)),sorted(set(city_ids)-reached))
    space_transitions=admitted["HR1"]["main"].get("space_transition_map",[])
    if len(city_ids)>=3 and not space_transitions:
        raise AssemblyBlocked("HP1_MULTI_CITY_SPACE_TRANSITION_GAP",",".join(city_ids),city_ids)
    terminal_state_refs=list(lwks[-1]["exit_state_refs"])
    handoff = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE,
        "hld_run_id": admitted["HB0"]["completion"]["hld_run_id"], "status": "ready",
        "next_stage": "novel-lld", "current_hld_package": dict(package_ref),
        "work_units": lwks, "chapter_designs": chapter_designs, "storyline_dispositions":storyline_dispositions,
        "work_unit_time_windows":work_unit_time_windows, "character_dispositions":dispositions,
        "environment_coverage":{"required_ids":sorted(expected_environments),"placed_ids":sorted(placed_environments)},
        "world_setting":world,"space_transition_map":space_transitions,
        "terminal_state_refs":terminal_state_refs,
        "unresolved_dependency_summary": summaries,
        "preserved_open_items": preserved, "resolution_refs": resolutions,
    }
    return handoff, lwr_map


def build_traceability(admitted: Mapping[str, Any], objects: Mapping[str, tuple[str, Any]], handoff: Mapping[str, Any]) -> dict[str, Any]:
    decision_ids = {
        item.get("id") for stage in DESIGN_STAGES for item in admitted[stage]["main"].get("design_decisions", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    records = []
    hk1 = admitted["HK1"]["main"]
    current_lwrs = hk1.get("lld_work_requirements")
    lwr_claims = [
        item for item in hk1.get("derivation_claims", [])
        if isinstance(item, dict)
        and item.get("target_locator") == "/lld_work_requirements"
        and isinstance(current_lwrs, list)
        and item.get("value_sha256") == value_hash(current_lwrs)
    ]
    hk1_stage_decisions = [
        item["id"] for item in hk1.get("design_decisions", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    for index, lwk in enumerate(handoff["work_units"], 1):
        object_ids = list(lwk["hkf_ids"])
        values = [objects[item][1] for item in object_ids if item in objects]
        sources = sorted(set(_named_string_values(values, "source_refs")))
        decisions = sorted(decision_ids.intersection(_named_string_values(values, "design_decision_ids")))
        if not decisions and len(lwr_claims) == 1 and len(hk1_stage_decisions) == 1:
            decisions = list(hk1_stage_decisions)
        if not sources or not decisions:
            raise AssemblyBlocked("HP1_TRACEABILITY_GAP", lwk["source_lwr_id"], [lwk["source_lwr_id"]])
        if any(source_id not in objects or objects[source_id][0] != "HB0" for source_id in sources):
            raise AssemblyBlocked("HP1_TRACE_SOURCE_UNRESOLVED", lwk["source_lwr_id"], sources)
        records.append({
            "id": f"TRC-{index:06d}", "source_ids": sources, "decision_ids": decisions,
            "hld_object_ids": object_ids, "lwr_ids": [lwk["source_lwr_id"]], "lwk_ids": [lwk["id"]],
        })
    return {"schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": handoff["hld_run_id"], "status": "ready", "records": records}


def _markdown_spec(machine: Mapping[str, Any], handoff: Mapping[str, Any]) -> str:
    lines = ["# Novel HLD machine specification", "", f"Run: `{machine['hld_run_id']}`", "", "## Canonical models", ""]
    for item in machine["canonical_models"]:
        lines.append(f"- {item['stage']}: `{item['path']}` (`{item['sha256']}`)")
    lines.extend(["", "## HLD decisions", ""])
    for group in machine["hld_decisions"]:
        lines.append(f"- {group['stage']}: {group['count']} decisions at `{group['model_path']}#{group['locator']}`")
    lines.extend(["", "## LLD work handoff", ""])
    for item in handoff["work_units"]:
        lines.append(f"- `{item['source_lwr_id']}` → `{item['id']}`; HKF: {', '.join(item['hkf_ids'])}")
    lines.extend(["", "## Chapter design handoff", ""])
    for item in handoff["chapter_designs"]:
        lines.append(f"- Chapter {item['chapter_number']} `{item['id']}` / `{item['source_design_id']}`: {item['working_title']}; primary `{item['primary_storyline_id']}`; work unit `{item['work_unit_id']}`")
    lines.extend(["", "## Unresolved dependency status", ""])
    for item in machine["unresolved_dependency_summary"]:
        lines.append(f"- `{item['source_id']}`: `{item['aggregate_disposition']}`")
    return "\n".join(lines) + "\n"


def _markdown_trace(trace: Mapping[str, Any]) -> str:
    lines = ["# HLD traceability matrix", "", "| Trace | Sources | Decisions | HLD objects | LWR | LWK |", "|---|---|---|---|---|---|"]
    for item in trace["records"]:
        lines.append("| " + " | ".join([
            item["id"], ", ".join(item["source_ids"]), ", ".join(item["decision_ids"]),
            ", ".join(item["hld_object_ids"]), ", ".join(item["lwr_ids"]), ", ".join(item["lwk_ids"]),
        ]) + " |")
    return "\n".join(lines) + "\n"


def _clean_markdown_spec(machine: Mapping[str, Any], handoff: Mapping[str, Any]) -> str:
    """Render the normative human view using portable ASCII punctuation."""
    lines = ["# Novel HLD machine specification", "", f"Run: `{machine['hld_run_id']}`", "", "## Canonical models", ""]
    for item in machine["canonical_models"]:
        lines.append(f"- {item['stage']}: `{item['path']}` (`{item['sha256']}`)")
    lines.extend(["", "## HLD decisions", ""])
    for group in machine["hld_decisions"]:
        lines.append(f"- {group['stage']}: {group['count']} decisions at `{group['model_path']}#{group['locator']}`")
    lines.extend(["", "## LLD work handoff", ""])
    for item in handoff["work_units"]:
        lines.append(f"- `{item['source_lwr_id']}` -> `{item['id']}`; HKF: {', '.join(item['hkf_ids'])}")
    lines.extend(["", "## Chapter design handoff", ""])
    for item in handoff["chapter_designs"]:
        lines.append(f"- Chapter {item['chapter_number']} `{item['id']}` / `{item['source_design_id']}`: {item['working_title']}; primary `{item['primary_storyline_id']}`; work unit `{item['work_unit_id']}`")
    lines.extend(["", "## Unresolved dependency status", ""])
    for item in machine["unresolved_dependency_summary"]:
        lines.append(f"- `{item['source_id']}`: `{item['aggregate_disposition']}`")
    return "\n".join(lines) + "\n"


def _manifest(package: Path, context: Context, status: str, name: str) -> dict[str, Any]:
    excluded = {name, "stage-completion.json"}
    files = [path for path in package.rglob("*") if path.is_file() and path.relative_to(package).as_posix() not in excluded]
    refs = [ref(path, package, "content") for path in sorted(files, key=lambda item: item.relative_to(package).as_posix())]
    role_map = {}
    fixed = {
        "novel-hld-package.json": "novel_hld_package", "novel-hld-spec.md": "hld_spec",
        "hld-cross-index.json": "cross_index", "hld-traceability-matrix.json": "traceability",
        "lld-handoff.json": "lld_handoff", "assembly-execution.json": "execution_record", "validation.json": "validation",
    }
    for item in refs:
        role = fixed.get(item["path"], "canonical_model" if item["path"].startswith("canonical-models/") else "content")
        if role in role_map:
            role = f"{role}::{item['path']}"
        role_map[role] = {**item, "role": role}
    refs = [{**item, "role": next(role for role, bound in role_map.items() if bound["path"] == item["path"])} for item in refs]
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": STAGE, "skill": SKILL,
        "status": status, "files": refs, "artifact_roles": role_map,
    }


def _base_result(context: Context, result: str, package: Path, manifest: Path, validation: Path) -> dict[str, Any]:
    empty = {
        "completion_ref": None, "internal_manifest_ref": None, "revision_class": None,
        "revision_report_ref": None, "candidate_ref": None, "local_defect_evidence": [],
        "author_event_ref": None, "gate_data_ref": None, "blocked_report_ref": None,
        "blocker_class": None, "affected_ids": [], "runtime_error_ref": None,
    }
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": STAGE, "skill": SKILL,
        "work_order_id": context.work_order["work_order_id"], "task_id": context.work_order["task_id"],
        "event_sequence": context.work_order["event_sequence"], "result_scope": "top_level", "result": result,
        "state_before_ref": context.work_order["state_before_ref"], "input_gate_ref": context.work_order["input_gate_ref"],
        "result_manifest_ref": output_ref(manifest, package, context, "package_manifest" if result == "ready" else "result_manifest"),
        "validation_ref": output_ref(validation, package, context, "validation"), "produced_at": context.work_order["result_timestamp"],
        **empty,
    }


def write_ready(context: Context, admitted: Mapping[str, Any], destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    copied = []
    for stage in DESIGN_STAGES:
        target = destination / "canonical-models" / CANONICAL_FILES[stage]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(admitted[stage]["main_path"], target)
        if target.read_bytes() != admitted[stage]["main_path"].read_bytes():
            raise RuntimeFailure(f"canonical byte copy drift: {stage}")
        copied.append({"stage": stage, "path": target.relative_to(destination).as_posix(), "sha256": file_hash(target)})
    review_target = destination / "canonical-models" / "hld-semantic-review.json"
    shutil.copyfile(admitted["HQ1"]["main_path"], review_target)
    if review_target.read_bytes() != admitted["HQ1"]["main_path"].read_bytes():
        raise RuntimeFailure("HQ1 review byte copy drift")
    summaries, preserved, resolutions = aggregate_dependencies(admitted)
    baseline_controls = build_baseline_controls(admitted)
    cross_index, objects = build_cross_index(admitted, baseline_controls)
    machine = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE,
        "hld_run_id": context.work_order["hld_run_id"], "status": "ready",
        "stage_references": [{"stage": stage, "completion_sha256": file_hash(context.roles[f"{stage.lower()}_completion"]), "manifest_sha256": file_hash(context.roles[f"{stage.lower()}_manifest"]), "validation_sha256": file_hash(context.roles[f"{stage.lower()}_validation"])} for stage in UPSTREAM],
        "canonical_models": copied,
        "semantic_review": {"path": "canonical-models/hld-semantic-review.json", "sha256": file_hash(review_target)},
        "authority_partition": aggregate_authority_partition(admitted),
        "baseline_controls": baseline_controls,
        "open_items": preserved,
        "hld_decisions": [{
            "stage": stage, "model_path": f"canonical-models/{CANONICAL_FILES[stage]}",
            "locator": "/design_decisions", "value_sha256": value_hash(admitted[stage]["main"]["design_decisions"]),
            "count": len(admitted[stage]["main"]["design_decisions"]),
        } for stage in DESIGN_STAGES],
        "unresolved_dependency_summary": summaries,
        "package_profile": sorted(READY_TOP_FILES | {"canonical-models/**"}),
    }
    machine_path = destination / "novel-hld-package.json"
    write_json(machine_path, machine)
    handoff, _ = build_handoff(admitted, ref(machine_path, destination, "novel_hld_package"), summaries, preserved, resolutions)
    trace = build_traceability(admitted, objects, handoff)
    for name, value, schema in (
        ("novel-hld-package.json", machine, "novel-hld-package.schema.json"),
        ("hld-cross-index.json", cross_index, "hld-cross-index.schema.json"),
        ("hld-traceability-matrix.json", trace, "hld-traceability-matrix.schema.json"),
        ("lld-handoff.json", handoff, "lld-handoff.schema.json"),
    ):
        _schema_validate(context.catalog, value, schema)
        write_json(destination / name, value)
    (destination / "novel-hld-spec.md").write_text(_clean_markdown_spec(machine, handoff), encoding="utf-8", newline="\n")
    (destination / "hld-traceability-matrix.md").write_text(_markdown_trace(trace), encoding="utf-8", newline="\n")
    execution = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "work_order_id": context.work_order["work_order_id"], "implementation_sha256": implementation_sha256(),
        "input_hashes": {role: file_hash(path) for role, path in sorted(context.roles.items())},
        "output_hashes": {name: file_hash(destination / name) for name in sorted({
            "novel-hld-package.json", "novel-hld-spec.md", "hld-cross-index.json", "hld-traceability-matrix.json",
            "hld-traceability-matrix.md", "lld-handoff.json",
        })}, "deterministic": True,
    }
    _schema_validate(context.catalog, execution, "assembly-execution.schema.json")
    write_json(destination / "assembly-execution.json", execution)
    validation = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "status": "pass", "checks": [
            "eight-upstream-current-ready", "canonical-byte-copy", "authority-partition-equality",
            "hq1-pass-empty-findings", "hdd-aggregate-deterministic", "stable-id-index-unique",
            "trace-source-decision-lwk", "lwr-lwk-bijection", "chapter-design-exact-coverage", "chapter-storyline-role-projection", "markdown-deterministic", "ready-profile-closed",
        ], "errors": [],
    }
    _schema_validate(context.catalog, validation, "hp1-validation.schema.json")
    write_json(destination / "validation.json", validation)
    manifest_value = _manifest(destination, context, "ready", "package-manifest.json")
    _schema_validate(context.catalog, manifest_value, "package-manifest.schema.json")
    write_json(destination / "package-manifest.json", manifest_value)
    completion = {
        "schema_version": "1.0", "harness": HARNESS, "stage": STAGE, "skill": SKILL,
        "hld_run_id": context.work_order["hld_run_id"], "revision": context.work_order["revision"], "status": "ready",
        "input_gate_ref": context.work_order["input_gate_ref"], "state_before_ref": context.work_order["state_before_ref"],
        "work_order_ref": ref(context.work_order_path, context.workspace, "work_order"),
        "manifest_ref": output_ref(destination / "package-manifest.json", destination, context, "package_manifest"),
        "validation_ref": output_ref(destination / "validation.json", destination, context, "validation"),
        "upstream_completions": context.work_order["upstream_completions"],
        "canonical_artifacts": [output_ref(destination / name, destination, context, role) for name, role in (
            ("novel-hld-package.json", "novel_hld_package"), ("hld-cross-index.json", "cross_index"),
            ("hld-traceability-matrix.json", "traceability"), ("lld-handoff.json", "lld_handoff"),
        )],
        "owner_implementation": {"skill": SKILL, "version": VERSION, "sha256": implementation_sha256()},
        "return_binding": context.work_order["return_binding"],
        "ready_capabilities": ["machine_hld_sealed", "canonical_models_lossless", "traceability_indexed", "lld_handoff_projected", "chapter_designs_projected"],
        "next_allowed_stage": "HQ2",
    }
    _schema_validate(context.catalog, completion, "stage-completion.schema.json")
    write_json(destination / "stage-completion.json", completion)
    result = _base_result(context, "ready", destination, destination / "package-manifest.json", destination / "validation.json")
    result["completion_ref"] = output_ref(destination / "stage-completion.json", destination, context, "stage_completion")
    _schema_validate(context.catalog, result, "stage-result.schema.json")
    return result


def write_blocked(context: Context, failure: AssemblyBlocked, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    gate = {"schema_version": "1.0", "hld_run_id": context.work_order["hld_run_id"], "stage": STAGE, "failed_gate": failure.code, "evidence": failure.evidence, "affected_ids": failure.affected_ids}
    report = {"schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"], "status": "blocked", "blocker_class": "upstream_defect", "code": failure.code, "evidence": failure.evidence, "required_action": "Correct the producing stage; HP1 cannot repair or reinterpret upstream content."}
    validation = {"schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"], "status": "blocked", "checks": ["failure-bound", "no-ready-artifacts"], "errors": [failure.code]}
    write_json(destination / "gate-data.json", gate)
    write_json(destination / "blocked-report.json", report)
    write_json(destination / "validation.json", validation)
    manifest_value = _manifest(destination, context, "blocked", "result-manifest.json")
    _schema_validate(context.catalog, manifest_value, "package-manifest.schema.json")
    write_json(destination / "result-manifest.json", manifest_value)
    result = _base_result(context, "blocked", destination, destination / "result-manifest.json", destination / "validation.json")
    result.update({
        "gate_data_ref": output_ref(destination / "gate-data.json", destination, context, "gate_data"),
        "blocked_report_ref": output_ref(destination / "blocked-report.json", destination, context, "blocked_report"),
        "blocker_class": "upstream_defect", "affected_ids": failure.affected_ids,
    })
    _schema_validate(context.catalog, result, "stage-result.schema.json")
    return result


def execute(work_order_path: Path) -> tuple[int, dict[str, Any]]:
    context = load_context(work_order_path)
    temp = Path(tempfile.mkdtemp(prefix=".hp1-", dir=context.workspace))
    staging = temp / "package"
    try:
        try:
            admitted = admit_upstreams(context)
            result = write_ready(context, admitted, staging)
            code = 0
        except AssemblyBlocked as failure:
            if staging.exists():
                shutil.rmtree(staging)
            result = write_blocked(context, failure, staging)
            code = 2
        os.replace(staging, context.output)
        write_json(context.workspace / "stage-result.json", result)
        validate_existing(work_order_path)
        return code, result
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def _exact_files(package: Path, ready: bool) -> None:
    actual = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    expected = set(READY_TOP_FILES if ready else BLOCKED_FILES)
    if ready:
        expected.update(f"canonical-models/{name}" for name in CANONICAL_FILES.values())
        expected.add("canonical-models/hld-semantic-review.json")
    if actual != expected:
        raise RuntimeFailure(f"HP1 package profile mismatch: expected={sorted(expected)} actual={sorted(actual)}")


def validate_existing(work_order_path: Path) -> dict[str, Any]:
    path = work_order_path.resolve(strict=True)
    workspace = path.parent
    result_path = workspace / "stage-result.json"
    result = read_json(result_path)
    output = resolve_inside(workspace, read_json(path)["output_directory"], file_only=False)
    shadow_result = workspace / ".hp1-result-validation"
    shadow_output = workspace / ".hp1-output-validation"
    os.replace(result_path, shadow_result)
    os.replace(output, shadow_output)
    try:
        context = load_context(path)
    finally:
        os.replace(shadow_output, output)
        os.replace(shadow_result, result_path)
    _schema_validate(context.catalog, result, "stage-result.schema.json")
    for field in ("result_manifest_ref", "validation_ref", "completion_ref", "gate_data_ref", "blocked_report_ref"):
        bound = result.get(field)
        if bound is not None:
            if ".hp1-" in bound.get("path", ""):
                raise RuntimeFailure(f"stage result leaks staging path: {field}")
            verify_ref(bound, workspace)
    if result["event_sequence"] != context.work_order["event_sequence"] or result["produced_at"] != context.work_order["result_timestamp"]:
        raise RuntimeFailure("stage result work-order binding drift")
    temp = Path(tempfile.mkdtemp(prefix=".hp1-reproduce-", dir=workspace))
    expected = temp / "package"
    try:
        try:
            admitted = admit_upstreams(context)
            expected_result = write_ready(context, admitted, expected)
            expected_code = 0
        except AssemblyBlocked as failure:
            if expected.exists():
                shutil.rmtree(expected)
            expected_result = write_blocked(context, failure, expected)
            expected_code = 2
        ready = expected_code == 0
        _exact_files(output, ready)
        _exact_files(expected, ready)
        for relative in sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()):
            if (output / relative).read_bytes() != (expected / relative).read_bytes():
                raise RuntimeFailure(f"HP1 output is not byte reproducible: {relative}")
        # Result paths differ only because expected package is temporary; compare all non-reference identity fields.
        for key in ("schema_version", "harness", "hld_run_id", "revision", "stage", "skill", "work_order_id", "task_id", "event_sequence", "result_scope", "result", "produced_at", "blocker_class", "affected_ids"):
            if result[key] != expected_result[key]:
                raise RuntimeFailure(f"HP1 stage result drift: {key}")
        if ready:
            validate_completion_bindings(workspace, output, read_json(output / "stage-completion.json"))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return {"status": "pass", "result": result["result"], "result_sha256": file_hash(result_path)}
