#!/usr/bin/env python3
"""Deterministic HB0 runtime. It never owns story interpretation or run state."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SKILL = "novel-hld-baseline-admitter"
STAGE = "HB0"
HARNESS = "novel-hld-autonomous"
VERSION = "0.1.0"
SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
HARNESS_ROOT = REPO_ROOT / "harnesses" / HARNESS
sys.path.insert(0, str(HARNESS_ROOT))

from runtime.schema_catalog import SchemaCatalog  # noqa: E402
from runtime.package_envelope import validate_completion_bindings  # noqa: E402

STAGES = ("HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1", "HP1", "HQ2", "HH1", "HF1")
DESIGN_STAGES = ("HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HD1")
NON_QUALITY_DOMAINS = ("intent", "storylines", "world", "environments", "events", "characters", "narrative", "cross-domain")
ALL_DOMAINS = NON_QUALITY_DOMAINS + ("quality",)
SOURCE_ACCESS = {
    "HB0": ALL_DOMAINS,
    **{stage: NON_QUALITY_DOMAINS for stage in DESIGN_STAGES},
    "HQ1": ALL_DOMAINS,
    "HP1": (), "HQ2": (), "HH1": (), "HF1": (),
}

HLD_RESPONSIBILITIES = (
    "overall-narrative-architecture", "multi-thread-choreography", "character-arc-placement",
    "act-and-chapter-progression", "key-scene-functions",
    "suspense-setup-probe-reveal-payoff",
    "time-space-pacing-tension-pov-information-architecture",
    "hld-to-lld-handoff-and-acceptance",
)
HLD_CAPABILITIES = (
    "traceable-conception-inheritance", "complete-multi-thread-architecture",
    "character-arc-and-event-alignment", "time-space-pacing-pov-information-control",
    "key-scene-function-coverage", "lld-ready-handoff-with-acceptance",
)
HLD_PROHIBITIONS = (
    "change-conception-authority", "resolve-author-owned-question", "produce-lld-material", "write-prose",
)

BASE_ROLES = {
    "hld_run_request", "preparation_request", "preparation_validator", "preparation_runtime", "preparation_compatibility_lock",
    "development_baseline", "development_baseline_markdown", "baseline_validation", "baseline_manifest",
    "development_baseline_schema", "baseline_validation_schema", "baseline_manifest_schema",
    "preparation_request_schema", "upstream_release_lock", "harness_common_schema",
    "harness_run_request_schema", "harness_input_gate_schema", "harness_work_order_schema",
    "harness_run_state_schema", "harness_package_manifest_schema", "harness_stage_completion_schema",
    "harness_stage_result_schema", "harness_control_baseline_schema", "harness_source_index_schema",
    "harness_hb0_validation_schema", "harness_hb0_execution_schema", "harness_gate_data_schema",
    "harness_blocked_report_schema",
}

READY_CHECKS = (
    "work-order-identity-and-gate", "allowlist-closure-and-hashes", "revision-000-state",
    "preparation-compatibility-lock", "preparation-validator-current-pass", "four-file-baseline-boundary",
    "baseline-schema-and-manifest", "project-release-lineage", "authority-partition-totality",
    "unresolved-register-lossless", "source-locator-and-value-hashes", "fixed-source-access-matrix",
    "hld-assignment-exact", "no-hld-decisions", "ready-package-profile",
)


class RuntimeFailure(RuntimeError):
    pass


class AdmissionBlocked(RuntimeError):
    def __init__(self, code: str, evidence: str, required_action: str, affected_ids: list[str] | None = None):
        super().__init__(code)
        self.code = code
        self.evidence = evidence
        self.required_action = required_action
        self.affected_ids = affected_ids or []


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeFailure(f"invalid JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeFailure(f"JSON root must be object: {path}")
    return value


def _safe_relative(value: Any) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or re.match(r"^[A-Za-z]:", value) or value.startswith("/"):
        raise RuntimeFailure("unsafe relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeFailure("non-normalized relative path")
    return Path(*parts)


def resolve_inside(root: Path, relative: Any, *, must_exist: bool = True, file_only: bool = True) -> Path:
    candidate = (root / _safe_relative(relative)).resolve(strict=must_exist)
    try:
        candidate.relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise RuntimeFailure(f"path escapes workspace: {relative}") from error
    if must_exist and file_only and not candidate.is_file():
        raise RuntimeFailure(f"not a file: {relative}")
    return candidate


def make_ref(path: Path, root: Path, role: str) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    relative = resolved.relative_to(root.resolve(strict=True)).as_posix()
    return {"role": role, "path": relative, "sha256": sha256_file(resolved)}


def output_ref(path: Path, package: Path, context: "Context", role: str) -> dict[str, str]:
    """Hash staged bytes while binding their canonical post-publish path."""
    relative = path.resolve(strict=True).relative_to(package.resolve(strict=True))
    target = (context.output_dir / relative).relative_to(context.workspace).as_posix()
    return {"role": role, "path": target, "sha256": sha256_file(path)}


def verify_ref(ref: Mapping[str, Any], root: Path, expected_role: str | None = None) -> Path:
    if set(ref) != {"role", "path", "sha256"}:
        raise RuntimeFailure("reference fields must be role/path/sha256")
    if expected_role and ref.get("role") != expected_role:
        raise RuntimeFailure(f"wrong role: expected {expected_role}, got {ref.get('role')}")
    path = resolve_inside(root, ref.get("path"))
    if not hmac.compare_digest(sha256_file(path), str(ref.get("sha256"))):
        raise RuntimeFailure(f"hash mismatch: {ref.get('path')}")
    return path


def json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise AdmissionBlocked("HB0_LOCATOR_INVALID", str(pointer), "Regenerate the upstream baseline locator.")
    current = document
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise AdmissionBlocked("HB0_LOCATOR_INVALID", pointer, "Regenerate the RFC 6901 locator.")
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise AdmissionBlocked("HB0_LOCATOR_UNRESOLVED", pointer, "Restore the referenced source or regenerate baseline.")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token[0] == "0") or int(token) >= len(current):
                raise AdmissionBlocked("HB0_LOCATOR_UNRESOLVED", pointer, "Regenerate the exact array locator.")
            current = current[int(token)]
        else:
            raise AdmissionBlocked("HB0_LOCATOR_UNRESOLVED", pointer, "Regenerate a locator that does not traverse a scalar.")
    return current


def _schema_registry(role_paths: Mapping[str, Path]) -> tuple[dict[str, dict[str, Any]], SchemaCatalog]:
    schemas: dict[str, dict[str, Any]] = {}
    for role, path in role_paths.items():
        if not role.endswith("_schema") and role != "harness_common_schema":
            continue
        value = read_json(path)
        schema_id = value.get("$id")
        if not isinstance(schema_id, str):
            raise RuntimeFailure(f"schema lacks $id: {role}")
        schemas[role] = value
    try:
        catalog = SchemaCatalog.from_documents(schemas)
    except Exception as error:
        raise RuntimeFailure(f"invalid staged schema catalog: {error}") from error
    return schemas, catalog


def validate_schema(value: Any, schema_role: str, schemas: Mapping[str, dict[str, Any]], registry: SchemaCatalog, *, blocked: bool = False) -> None:
    if schema_role not in schemas:
        raise RuntimeFailure(f"missing schema role: {schema_role}")
    errors = registry.iter_errors(value, schema_role)
    if errors:
        first = errors[0]
        pointer = "/" + "/".join(str(part) for part in first.absolute_path)
        message = f"{schema_role}{pointer}: {first.message}"
        if blocked:
            raise AdmissionBlocked("HB0_SCHEMA_INVALID", message, "Regenerate the artifact with its released producer.")
        raise RuntimeFailure(message)


@dataclass
class Context:
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    input_gate: dict[str, Any]
    state_before: dict[str, Any]
    roles: dict[str, Path]
    schemas: dict[str, dict[str, Any]]
    registry: SchemaCatalog
    output_dir: Path


def implementation_sha256() -> str:
    digest = hashlib.sha256()
    for path in (
        SCRIPT_PATH,
        HARNESS_ROOT / "runtime" / "schema_catalog.py",
        HARNESS_ROOT / "runtime" / "package_envelope.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_context(work_order_path: Path) -> Context:
    path = work_order_path.resolve(strict=True)
    workspace = path.parent.resolve(strict=True)
    work_order = read_json(path)
    raw_refs = work_order.get("file_allowlist")
    if not isinstance(raw_refs, list):
        raise RuntimeFailure("work-order allowlist missing")
    preliminary_roles: dict[str, Path] = {}
    for ref in raw_refs:
        role = ref.get("role") if isinstance(ref, dict) else None
        if not isinstance(role, str) or role in preliminary_roles:
            raise RuntimeFailure("allowlist roles must be unique")
        preliminary_roles[role] = verify_ref(ref, workspace, role)
    missing = BASE_ROLES - set(preliminary_roles)
    extras = set(preliminary_roles) - BASE_ROLES
    if missing or any(not (role.startswith("source::") or role.startswith("upstream::")) for role in extras):
        raise RuntimeFailure(f"allowlist role closure mismatch; missing={sorted(missing)} extras={sorted(extras)}")
    schemas, registry = _schema_registry(preliminary_roles)
    validate_schema(work_order, "harness_work_order_schema", schemas, registry)
    if work_order["stage"] != STAGE or work_order["exact_owner_skill"] != SKILL or work_order["owner_version"] != VERSION:
        raise RuntimeFailure("work-order owner identity mismatch")
    if work_order["implementation_sha256"] != implementation_sha256():
        raise RuntimeFailure("work-order implementation hash mismatch")
    if work_order["action"] != "execute" or work_order["mode"] != "forward" or work_order["return_binding"] is not None:
        raise RuntimeFailure("HB0 accepts only forward execute")
    if work_order["upstream_completions"] or work_order["unresolved_projection"] or work_order["revision_plan_ref"] is not None or work_order["revision_plan_state_ref"] is not None:
        raise RuntimeFailure("HB0 control inputs must be empty")
    input_gate_path = verify_ref(work_order["input_gate_ref"], workspace, "input_gate")
    state_path = verify_ref(work_order["state_before_ref"], workspace, "state_before")
    input_gate = read_json(input_gate_path)
    state = read_json(state_path)
    validate_schema(input_gate, "harness_input_gate_schema", schemas, registry)
    validate_schema(state, "harness_run_state_schema", schemas, registry)
    if input_gate["file_allowlist"] != work_order["file_allowlist"] or input_gate["state_before_ref"] != work_order["state_before_ref"]:
        raise RuntimeFailure("input gate and work order bindings differ")
    for field in ("hld_run_id", "stage", "mode", "exact_owner_skill", "owner_version", "implementation_sha256", "return_binding", "unresolved_projection", "revision_plan_ref", "revision_plan_state_ref"):
        if input_gate[field] != work_order[field]:
            raise RuntimeFailure(f"input gate differs on {field}")
    if state != {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": work_order["hld_run_id"],
        "revision": 0, "event_sequence": 0, "status": "initialized", "current_stage": "HB0",
        "accepted_completions": [], "current_result_ref": None, "previous_state_ref": None,
        "revision_plan_ref": None, "revision_plan_state_ref": None, "waiting_transaction_ref": None,
    }:
        raise RuntimeFailure("state before is not the exact revision-000 state")
    output_dir = resolve_inside(workspace, work_order["output_directory"], must_exist=False, file_only=False)
    if output_dir.exists() or output_dir == workspace or workspace not in output_dir.parents:
        raise RuntimeFailure("HB0 output directory must be new and inside workspace")
    if (workspace / "stage-result.json").exists():
        raise RuntimeFailure("stage-result.json already exists")
    return Context(workspace, path, work_order, input_gate, state, preliminary_roles, schemas, registry, output_dir)


def _validate_compatibility(context: Context) -> dict[str, Any]:
    lock = read_json(context.roles["preparation_compatibility_lock"])
    expected = lock.get("files")
    if lock.get("schema_version") != "1.0" or lock.get("producer_skill") != "novel-development-baseline-preparer" or not isinstance(expected, dict):
        raise RuntimeFailure("invalid HB0 compatibility lock")
    for role, sha in expected.items():
        if role not in context.roles or not hmac.compare_digest(sha256_file(context.roles[role]), sha):
            raise AdmissionBlocked("HB0_PREPARATION_INCOMPATIBLE", role, "Install the exact supported preparation release or update the HLD compatibility release.")
    return lock


def _run_preparation_validator(context: Context) -> None:
    command = [sys.executable, str(context.roles["preparation_validator"]), str(context.roles["preparation_request"])]
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    if completed.returncode != 0:
        evidence = (completed.stdout or completed.stderr or f"exit={completed.returncode}").strip()[:2000]
        raise AdmissionBlocked("HB0_PREPARATION_REVALIDATION_FAILED", evidence, "Repair or regenerate the upstream preparation package; HB0 will not repair it.")


def _validate_baseline_package(context: Context) -> dict[str, Any]:
    run_request = read_json(context.roles["hld_run_request"])
    validate_schema(run_request, "harness_run_request_schema", context.schemas, context.registry, blocked=True)
    baseline = read_json(context.roles["development_baseline"])
    validation = read_json(context.roles["baseline_validation"])
    manifest = read_json(context.roles["baseline_manifest"])
    validate_schema(baseline, "development_baseline_schema", context.schemas, context.registry, blocked=True)
    validate_schema(validation, "baseline_validation_schema", context.schemas, context.registry, blocked=True)
    validate_schema(manifest, "baseline_manifest_schema", context.schemas, context.registry, blocked=True)
    if run_request["project_id"] != baseline["project_id"] or run_request["hld_run_id"] != context.work_order["hld_run_id"]:
        raise AdmissionBlocked("HB0_RUN_IDENTITY_MISMATCH", "project/run identity", "Issue a new work order for the exact baseline project.")
    baseline_dir = context.roles["development_baseline"].parent.resolve()
    expected_files = {"development-baseline.json", "development-baseline.md", "baseline-validation.json", "package-manifest.json"}
    actual_files = {path.name for path in baseline_dir.iterdir() if path.is_file()}
    if actual_files != expected_files:
        raise AdmissionBlocked("HB0_BASELINE_BOUNDARY_MISMATCH", str(sorted(actual_files)), "Regenerate the exact four-file baseline package.")
    role_to_name = {
        "development_baseline": "development-baseline.json", "development_baseline_markdown": "development-baseline.md",
        "baseline_validation": "baseline-validation.json", "baseline_manifest": "package-manifest.json",
    }
    for role, name in role_to_name.items():
        if context.roles[role].resolve() != (baseline_dir / name).resolve():
            raise AdmissionBlocked("HB0_BASELINE_ROLE_MISMATCH", role, "Bind the exact baseline package files.")
    manifest_refs = manifest.get("files", [])
    bound = {(ref.get("path"), ref.get("sha256")) for ref in manifest_refs if isinstance(ref, dict)}
    for role in ("development_baseline", "development_baseline_markdown", "baseline_validation"):
        name = context.roles[role].name
        digest = sha256_file(context.roles[role])
        if (name, digest) not in bound:
            raise AdmissionBlocked("HB0_BASELINE_MANIFEST_DRIFT", role, "Regenerate the upstream baseline manifest.")
    if baseline.get("status") != "ready" or validation.get("status") != "pass":
        raise AdmissionBlocked("HB0_BASELINE_NOT_READY", "baseline/validation status", "Provide a currently ready preparation package.")
    assignment = baseline.get("hld_assignment", {})
    if tuple(assignment.get("responsibilities", ())) != HLD_RESPONSIBILITIES or tuple(assignment.get("required_capabilities", ())) != HLD_CAPABILITIES or tuple(assignment.get("prohibitions", ())) != HLD_PROHIBITIONS or assignment.get("next_stage") != "novel-hld":
        raise AdmissionBlocked("HB0_HLD_ASSIGNMENT_MISMATCH", "hld_assignment", "Regenerate baseline with the supported preparation contract.")
    return {"run_request": run_request, "baseline": baseline, "validation": validation, "manifest": manifest}


def _partition(baseline: Mapping[str, Any]) -> dict[str, Any]:
    bindings = baseline["control_bindings"]
    ids = [item["source_id"] for item in bindings]
    if len(ids) != len(set(ids)):
        raise AdmissionBlocked("HB0_CONTROL_DUPLICATE", "control source_id", "Regenerate a unique upstream control registry.", ids)
    classes = {key: [] for key in ("mandatory", "freedom", "must_ask", "open")}
    authorities = {key: [] for key in ("author_locked", "autonomous_owned", "downstream_freedom", "author_open")}
    open_items: list[str] = []
    for item in bindings:
        classes[item["classification"]].append(item["source_id"])
        authorities[item["authority_class"]].append(item["source_id"])
        if item["open_item"]:
            open_items.append(item["source_id"])
    for partition in (classes, authorities):
        flat = [value for values in partition.values() for value in values]
        if len(flat) != len(set(flat)) or set(flat) != set(ids):
            raise AdmissionBlocked("HB0_AUTHORITY_PARTITION_INVALID", "authority partition", "Regenerate the upstream baseline authority sets.", ids)
        for key in partition:
            partition[key] = sorted(partition[key])
    return {
        "source_classifications": classes, "source_open_items": sorted(open_items),
        "source_authority_classes": authorities,
        "hld_ownership": {"source_projection": [], "hld_owned": [], "preserved_open": [], "lld_freedom": []},
    }


def _source_role(source: Mapping[str, Any]) -> str:
    return f"source::{source['root']}::{source['path']}"


def _structural_type(value: Any) -> str:
    if value is None: return "null"
    if isinstance(value, bool): return "boolean"
    if isinstance(value, int): return "integer"
    if isinstance(value, float): return "number"
    if isinstance(value, str): return "string"
    if isinstance(value, list): return "array"
    if isinstance(value, dict): return "object"
    raise AdmissionBlocked("HB0_SOURCE_VALUE_UNSUPPORTED", type(value).__name__, "Regenerate a JSON-compatible source value.")


def _indexed_value(item: Mapping[str, Any], value: Any) -> Any:
    """Reproduce the baseline producer's closed typed projections.

    E1 operational slots are intentionally indexed by stable slot identity,
    while their locator points at the richer actor-authority binding that
    proves that identity.  Admit only that one exact projection shape.
    """
    if (
        item["domain"] == "environments"
        and item["source"]["path"] == "P1/canonical-models/environment-system.json"
        and item["source_id"].startswith("SLOT-")
    ):
        bound_slot = value.get("actor_slot_id") if isinstance(value, dict) else value
        projected = {"slot_id": item["source_id"], "kind": "e1_operational_slot"}
        if bound_slot == item["source_id"] and hmac.compare_digest(canonical_sha256(projected), item["expected_hash"]):
            return projected
    return value


def _source_index(context: Context, baseline: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    for item in baseline["control_bindings"]:
        raw.append({"source_id": item["source_id"], "domain": item["domain"], "source": item["source"], "locator": item["locator"], "expected_hash": item["source_value_sha256"]})
    for domain, entries in baseline["design_inventory"].items():
        for item in entries:
            raw.append({"source_id": item["source_id"], "domain": domain, "source": item["source"], "locator": item["locator"], "expected_hash": item["source_value_sha256"]})
    indexed: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    document_cache: dict[Path, Any] = {}
    for item in raw:
        source = item["source"]
        role = _source_role(source)
        if role not in context.roles:
            raise AdmissionBlocked("HB0_SOURCE_NOT_ALLOWLISTED", role, "Stage and allowlist every baseline-referenced source file.", [item["source_id"]])
        path = context.roles[role]
        if not hmac.compare_digest(sha256_file(path), source["sha256"]):
            raise AdmissionBlocked("HB0_SOURCE_BYTE_DRIFT", role, "Restore the immutable source artifact.", [item["source_id"]])
        if path not in document_cache:
            document_cache[path] = json.loads(path.read_text(encoding="utf-8"))
        value = _indexed_value(item, json_pointer(document_cache[path], item["locator"]))
        actual_hash = canonical_sha256(value)
        if not hmac.compare_digest(actual_hash, item["expected_hash"]):
            raise AdmissionBlocked("HB0_SOURCE_VALUE_DRIFT", f"{item['source_id']}#{item['locator']}", "Regenerate the baseline locator/value binding.", [item["source_id"]])
        discriminator = None
        if isinstance(value, dict):
            for key in ("object_type", "kind", "type"):
                if isinstance(value.get(key), str) and value[key]:
                    discriminator = value[key]
                    break
        allowed = [stage for stage in STAGES if item["domain"] in SOURCE_ACCESS[stage]]
        entry = {
            "source_id": item["source_id"], "domain": item["domain"], "object_type": _structural_type(value),
            "schema_discriminator": discriminator, "source": source,
            "workspace_source_ref": make_ref(path, context.workspace, role), "locator": item["locator"],
            "value_sha256": actual_hash, "allowed_stages": allowed,
        }
        key = (entry["source_id"], entry["domain"], source["path"], entry["locator"])
        if key in indexed and indexed[key] != entry:
            raise AdmissionBlocked("HB0_SOURCE_INDEX_CONFLICT", str(key), "Regenerate non-conflicting upstream index entries.", [entry["source_id"]])
        indexed[key] = entry
    return [indexed[key] for key in sorted(indexed)]


def build_outputs(context: Context, admitted: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = admitted["baseline"]
    partition = _partition(baseline)
    registry = []
    unresolved = []
    for item in sorted(baseline["control_bindings"], key=lambda value: value["source_id"]):
        role = _source_role(item["source"])
        record = {**item, "workspace_source_ref": make_ref(context.roles[role], context.workspace, role)}
        registry.append(record)
        if item["classification"] == "must_ask" or item["open_item"]:
            unresolved.append({
                "source_id": item["source_id"], "domain": item["domain"],
                "classification": item["classification"], "open_item": item["open_item"],
                "authority_class": item["authority_class"],
            })
    control = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE,
        "hld_run_id": context.work_order["hld_run_id"], "status": "ready",
        "source_baseline": make_ref(context.roles["development_baseline"], context.workspace, "development_baseline"),
        "source_release": baseline["source_release"], "lineage": baseline["lineage"],
        "admission_verdicts": list(READY_CHECKS), "authority_partition": partition,
        "control_registry": registry, "unresolved_register": unresolved,
        "hld_assignment": baseline["hld_assignment"], "change_policy": baseline["change_policy"],
        "prohibitions": list(HLD_PROHIBITIONS), "source_access_policy": "SOURCE_ACCESS_MATRIX@1.0",
    }
    source_index = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE,
        "hld_run_id": context.work_order["hld_run_id"], "status": "ready",
        "entries": _source_index(context, baseline),
    }
    return control, source_index


def _manifest(package: Path, context: Context, filenames: list[tuple[str, str]], status: str, name: str = "package-manifest.json") -> dict[str, Any]:
    refs = [make_ref(package / filename, package, role) for role, filename in filenames]
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": STAGE, "skill": SKILL, "status": status,
        "files": refs, "artifact_roles": {ref["role"]: ref for ref in refs},
    }


def _empty_result_fields() -> dict[str, Any]:
    return {
        "completion_ref": None, "internal_manifest_ref": None, "revision_class": None,
        "revision_report_ref": None, "candidate_ref": None, "local_defect_evidence": [],
        "author_event_ref": None, "gate_data_ref": None, "blocked_report_ref": None,
        "blocker_class": None, "affected_ids": [], "runtime_error_ref": None,
    }


def _base_result(context: Context, result: str, manifest_ref: Mapping[str, Any], validation_ref: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": STAGE, "skill": SKILL,
        "work_order_id": context.work_order["work_order_id"], "task_id": context.work_order["task_id"],
        "event_sequence": context.work_order["event_sequence"], "result_scope": "top_level", "result": result,
        "state_before_ref": context.work_order["state_before_ref"], "input_gate_ref": context.work_order["input_gate_ref"],
        "result_manifest_ref": dict(manifest_ref), "validation_ref": dict(validation_ref),
        "produced_at": context.work_order["result_timestamp"], **_empty_result_fields(),
    }


def write_ready(context: Context, control: Mapping[str, Any], source_index: Mapping[str, Any], destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination / "hld-control-baseline.json", control)
    write_json(destination / "hld-source-index.json", source_index)
    execution = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "work_order_id": context.work_order["work_order_id"], "implementation_sha256": implementation_sha256(),
        "input_hashes": {role: sha256_file(path) for role, path in sorted(context.roles.items())},
        "preparation_validator_exit_code": 0, "read_roles": sorted(context.roles),
        "output_hashes": {
            "control_baseline": sha256_file(destination / "hld-control-baseline.json"),
            "source_index": sha256_file(destination / "hld-source-index.json"),
        }, "deterministic": True,
    }
    write_json(destination / "hb0-execution.json", execution)
    validation = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "status": "pass", "checks": list(READY_CHECKS), "errors": [],
        "artifacts": [
            make_ref(destination / "hld-control-baseline.json", destination, "control_baseline"),
            make_ref(destination / "hld-source-index.json", destination, "source_index"),
            make_ref(destination / "hb0-execution.json", destination, "execution_record"),
        ],
    }
    validate_schema(control, "harness_control_baseline_schema", context.schemas, context.registry)
    validate_schema(source_index, "harness_source_index_schema", context.schemas, context.registry)
    validate_schema(execution, "harness_hb0_execution_schema", context.schemas, context.registry)
    validate_schema(validation, "harness_hb0_validation_schema", context.schemas, context.registry)
    write_json(destination / "validation.json", validation)
    manifest = _manifest(destination, context, [
        ("control_baseline", "hld-control-baseline.json"), ("source_index", "hld-source-index.json"),
        ("execution_record", "hb0-execution.json"), ("validation", "validation.json"),
    ], "ready")
    validate_schema(manifest, "harness_package_manifest_schema", context.schemas, context.registry)
    write_json(destination / "package-manifest.json", manifest)
    completion = {
        "schema_version": "1.0", "harness": HARNESS, "stage": STAGE, "skill": SKILL,
        "hld_run_id": context.work_order["hld_run_id"], "revision": context.work_order["revision"], "status": "ready",
        "input_gate_ref": context.work_order["input_gate_ref"], "state_before_ref": context.work_order["state_before_ref"],
        "work_order_ref": make_ref(context.work_order_path, context.workspace, "work_order"),
        "manifest_ref": output_ref(destination / "package-manifest.json", destination, context, "package_manifest"),
        "validation_ref": output_ref(destination / "validation.json", destination, context, "validation"),
        "upstream_completions": [],
        "canonical_artifacts": [
            output_ref(destination / "hld-control-baseline.json", destination, context, "control_baseline"),
            output_ref(destination / "hld-source-index.json", destination, context, "source_index"),
        ],
        "owner_implementation": {"skill": SKILL, "version": VERSION, "sha256": implementation_sha256()},
        "return_binding": None,
        "ready_capabilities": ["baseline_admitted", "authority_partition_frozen", "source_index_verified", "unresolved_registered"],
        "next_allowed_stage": "HA1",
    }
    validate_schema(completion, "harness_stage_completion_schema", context.schemas, context.registry)
    write_json(destination / "stage-completion.json", completion)
    result = _base_result(
        context, "ready", output_ref(destination / "package-manifest.json", destination, context, "package_manifest"),
        output_ref(destination / "validation.json", destination, context, "validation"),
    )
    result["completion_ref"] = output_ref(destination / "stage-completion.json", destination, context, "stage_completion")
    validate_schema(result, "harness_stage_result_schema", context.schemas, context.registry)
    return result


def write_blocked(context: Context, failure: AdmissionBlocked, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    gate = {
        "schema_version": "1.0", "hld_run_id": context.work_order["hld_run_id"], "stage": STAGE,
        "failed_gate": failure.code, "evidence": failure.evidence, "affected_ids": failure.affected_ids,
    }
    report = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "status": "blocked", "blocker_class": "input_invalid", "code": failure.code,
        "evidence": failure.evidence, "required_action": failure.required_action,
    }
    validation = {
        "schema_version": "1.0", "skill": SKILL, "stage": STAGE, "hld_run_id": context.work_order["hld_run_id"],
        "status": "blocked", "checks": ["failure-evidence-bound", "no-ready-artifacts", "result-envelope-complete"],
        "errors": [failure.code], "artifacts": [],
    }
    for role, value, schema in (
        ("gate_data", gate, "harness_gate_data_schema"),
        ("blocked_report", report, "harness_blocked_report_schema"),
        ("validation", validation, "harness_hb0_validation_schema"),
    ):
        validate_schema(value, schema, context.schemas, context.registry)
        write_json(destination / {"gate_data": "gate-data.json", "blocked_report": "blocked-report.json", "validation": "validation.json"}[role], value)
    manifest = _manifest(destination, context, [
        ("gate_data", "gate-data.json"), ("blocked_report", "blocked-report.json"), ("validation", "validation.json"),
    ], "blocked", "result-manifest.json")
    validate_schema(manifest, "harness_package_manifest_schema", context.schemas, context.registry)
    write_json(destination / "result-manifest.json", manifest)
    result = _base_result(
        context, "blocked", output_ref(destination / "result-manifest.json", destination, context, "result_manifest"),
        output_ref(destination / "validation.json", destination, context, "validation"),
    )
    result.update({
        "gate_data_ref": output_ref(destination / "gate-data.json", destination, context, "gate_data"),
        "blocked_report_ref": output_ref(destination / "blocked-report.json", destination, context, "blocked_report"),
        "blocker_class": "input_invalid", "affected_ids": failure.affected_ids,
    })
    validate_schema(result, "harness_stage_result_schema", context.schemas, context.registry)
    return result


def _publish(staging: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeFailure("output destination already exists")
    os.replace(staging, destination)


def execute(work_order_path: Path) -> tuple[int, dict[str, Any]]:
    context = load_context(work_order_path)
    temporary = Path(tempfile.mkdtemp(prefix=".hb0-", dir=context.workspace))
    staging = temporary / "package"
    try:
        try:
            _validate_compatibility(context)
            _run_preparation_validator(context)
            admitted = _validate_baseline_package(context)
            control, source_index = build_outputs(context, admitted)
            result = write_ready(context, control, source_index, staging)
            code = 0
        except AdmissionBlocked as failure:
            result = write_blocked(context, failure, staging)
            code = 2
        _publish(staging, context.output_dir)
        write_json(context.workspace / "stage-result.json", result)
        validate_existing(work_order_path)
        return code, result
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _assert_exact_files(root: Path, expected: set[str]) -> None:
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual != expected:
        raise RuntimeFailure(f"package file profile mismatch: expected={sorted(expected)} actual={sorted(actual)}")


def _verify_manifest(root: Path, manifest_name: str) -> dict[str, Any]:
    manifest = read_json(root / manifest_name)
    declared = set()
    for ref in manifest["files"]:
        path = verify_ref(ref, root)
        declared.add(path.relative_to(root).as_posix())
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()} - {manifest_name, "stage-completion.json"}
    if declared != actual:
        raise RuntimeFailure("manifest closure mismatch")
    for role, ref in manifest["artifact_roles"].items():
        if ref.get("role") != role or ref.get("path") not in declared:
            raise RuntimeFailure(f"unbound manifest role: {role}")
    return manifest


def validate_existing(work_order_path: Path) -> dict[str, Any]:
    # Context loading normally rejects the existing result/output; validate with temporary names disabled.
    path = work_order_path.resolve(strict=True)
    workspace = path.parent
    existing_result = read_json(workspace / "stage-result.json")
    existing_output = resolve_inside(workspace, read_json(path)["output_directory"], must_exist=True, file_only=False)
    # Temporarily validate immutable inputs through a local context clone without mutating them.
    result_path = workspace / "stage-result.json"
    shadow_result = workspace / ".stage-result.hb0-validation"
    output_shadow = workspace / ".hb0-output-validation-shadow"
    os.replace(result_path, shadow_result)
    os.replace(existing_output, output_shadow)
    original_work_order = read_json(path)
    shadow_work_order = dict(original_work_order)
    shadow_work_order["output_directory"] = ".hb0-output-validation-shadow"
    shadow_work_path = workspace / ".work-order.hb0-validation.json"
    write_json(shadow_work_path, shadow_work_order)
    try:
        # load_context requires a new output, so use original output path while shadow holds package.
        context = load_context(path)
    finally:
        if shadow_work_path.exists():
            shadow_work_path.unlink()
        os.replace(output_shadow, existing_output)
        os.replace(shadow_result, result_path)
    validate_schema(existing_result, "harness_stage_result_schema", context.schemas, context.registry)
    for field in ("result_manifest_ref", "validation_ref", "completion_ref", "gate_data_ref", "blocked_report_ref"):
        bound = existing_result.get(field)
        if bound is not None:
            if ".hb0-" in bound.get("path", ""):
                raise RuntimeFailure(f"result reference leaks staging path: {field}")
            verify_ref(bound, workspace)
    if existing_result["produced_at"] != context.work_order["result_timestamp"] or existing_result["event_sequence"] != context.work_order["event_sequence"]:
        raise RuntimeFailure("result time/event drift")
    if existing_result["result"] == "ready":
        _assert_exact_files(existing_output, {
            "hld-control-baseline.json", "hld-source-index.json", "hb0-execution.json", "validation.json", "package-manifest.json", "stage-completion.json",
        })
        _verify_manifest(existing_output, "package-manifest.json")
        _validate_compatibility(context)
        _run_preparation_validator(context)
        admitted = _validate_baseline_package(context)
        expected_control, expected_index = build_outputs(context, admitted)
        if read_json(existing_output / "hld-control-baseline.json") != expected_control or read_json(existing_output / "hld-source-index.json") != expected_index:
            raise RuntimeFailure("ready canonical outputs are not reproducible")
        completion = read_json(existing_output / "stage-completion.json")
        validate_schema(completion, "harness_stage_completion_schema", context.schemas, context.registry)
        for field in ("manifest_ref", "validation_ref"):
            if ".hb0-" in completion[field]["path"]:
                raise RuntimeFailure(f"completion reference leaks staging path: {field}")
        for artifact in completion["canonical_artifacts"]:
            if ".hb0-" in artifact["path"]:
                raise RuntimeFailure("completion canonical artifact leaks staging path")
        validate_completion_bindings(workspace, existing_output, completion)
    elif existing_result["result"] == "blocked":
        _assert_exact_files(existing_output, {"gate-data.json", "blocked-report.json", "validation.json", "result-manifest.json"})
        _verify_manifest(existing_output, "result-manifest.json")
        try:
            _validate_compatibility(context)
            _run_preparation_validator(context)
            admitted = _validate_baseline_package(context)
            # Admission includes the lossless projection itself.  A baseline can
            # pass its package gates and still fail while resolving a locator,
            # checking a source value, or building the verified source index.
            build_outputs(context, admitted)
        except AdmissionBlocked as failure:
            report = read_json(existing_output / "blocked-report.json")
            if report["code"] != failure.code or report["evidence"] != failure.evidence or report["required_action"] != failure.required_action:
                raise RuntimeFailure("blocked report is stale or altered")
            # Rebuild the complete blocked envelope so the manifest hashes and
            # bound evidence are compared, rather than trusting a self-consistent
            # but stale package.
            expected_root = Path(tempfile.mkdtemp(prefix=".hb0-blocked-validation-", dir=context.workspace))
            expected_package = expected_root / "package"
            try:
                write_blocked(context, failure, expected_package)
                for name in ("gate-data.json", "blocked-report.json", "validation.json", "result-manifest.json"):
                    if read_json(existing_output / name) != read_json(expected_package / name):
                        raise RuntimeFailure(f"blocked package is stale or altered: {name}")
            finally:
                shutil.rmtree(expected_root, ignore_errors=True)
        else:
            raise RuntimeFailure("blocked package is stale because admission now passes")
    else:
        raise RuntimeFailure("HB0 existing result must be ready or blocked")
    return {"status": "pass", "result": existing_result["result"], "result_sha256": sha256_file(result_path)}
