"""Shared public envelope runtime for HH1 composite-internal semantic tasks."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .canonical import canonical_bytes, file_ref, read_json, resolve_inside, verify_file_ref, write_json
from .package_envelope import validate_manifest, validate_ready_profile, validate_result_envelope
from .schema_catalog import SchemaCatalog

HARNESS = "novel-hld-autonomous"


class InternalRuntimeError(RuntimeError):
    pass


class InternalCondition(RuntimeError):
    def __init__(self, outcome: str, code: str, evidence: str, affected_ids: Iterable[str] = (), *, blocker_class: str = "upstream_defect") -> None:
        super().__init__(code)
        self.outcome = outcome
        self.code = code
        self.evidence = evidence
        self.affected_ids = sorted(set(affected_ids))
        self.blocker_class = blocker_class


@dataclass(frozen=True)
class Spec:
    skill: str
    version: str
    profile: str
    canonical_name: str
    canonical_role: str
    session_name: str
    execution_name: str
    validation_schema: str
    required_roles: tuple[str, ...]
    evidence_required: bool = False


@dataclass
class Context:
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    gate: dict[str, Any]
    roles: dict[str, Path]
    output: Path
    catalog: SchemaCatalog
    spec: Spec


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def implementation_sha256(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((item.resolve(strict=True) for item in paths), key=lambda item: item.as_posix()):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def catalog(harness_root: Path, skill_schemas: Iterable[Path]) -> SchemaCatalog:
    docs: dict[str, Any] = {}
    for path in sorted((harness_root / "schemas").glob("*.schema.json")):
        docs[f"harness::{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for path in skill_schemas:
        docs[f"skill::{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    return SchemaCatalog.from_documents(docs)


def _shared_gate_fields() -> tuple[str, ...]:
    return (
        "harness", "hld_run_id", "stage", "mode", "state_before_ref", "upstream_completions",
        "exact_owner_skill", "owner_version", "implementation_sha256", "return_binding",
        "unresolved_projection", "revision_plan_ref", "revision_plan_state_ref", "file_allowlist",
    )


def load_context(work_order_path: Path, spec: Spec, implementation_hash: str, schema_catalog: SchemaCatalog) -> Context:
    path = work_order_path.resolve(strict=True)
    work = read_json(path)
    schema_catalog.validate(work, "work-order.schema.json")
    # Composite work orders live below ``internal/<task>/`` while every public
    # reference remains workspace-relative.  Resolve the workspace from the two
    # sealed bootstrap refs; never guess from or enumerate the input packages.
    candidates: list[Path] = []
    for ancestor in (path.parent, *path.parents):
        try:
            verify_file_ref(work["input_gate_ref"], ancestor)
            verify_file_ref(work["state_before_ref"], ancestor)
        except Exception:
            continue
        candidates.append(ancestor.resolve(strict=True))
    unique = list(dict.fromkeys(candidates))
    if len(unique) != 1:
        raise InternalRuntimeError("work-order workspace cannot be resolved uniquely from sealed bootstrap refs")
    workspace = unique[0]
    if work["stage"] != "HH1" or work["exact_owner_skill"] != spec.skill:
        raise InternalRuntimeError("work-order owner/stage mismatch")
    if work["action"] != "execute" or work["submission_status"] != "open":
        raise InternalRuntimeError("one open execute work-order is required")
    if work["implementation_sha256"] != implementation_hash or work["owner_version"] != spec.version:
        raise InternalRuntimeError("implementation binding mismatch")
    if work["mode"] != "forward" or work["return_binding"] is not None or work["unresolved_projection"]:
        raise InternalRuntimeError("HH1 internal task requires forward mode without unresolved projection")
    gate_path = verify_file_ref(work["input_gate_ref"], workspace)
    state_path = verify_file_ref(work["state_before_ref"], workspace)
    gate = read_json(gate_path)
    schema_catalog.validate(gate, "input-gate.schema.json")
    for field in _shared_gate_fields():
        if gate[field] != work[field]:
            raise InternalRuntimeError(f"input-gate/work-order mismatch: {field}")
    roles: dict[str, Path] = {}
    role_order: list[str] = []
    for ref in work["file_allowlist"]:
        role = ref["role"]
        if role in roles:
            raise InternalRuntimeError(f"duplicate allowlist role: {role}")
        value = verify_file_ref(ref, workspace)
        if value in roles.values():
            raise InternalRuntimeError("duplicate allowlist path under different roles")
        roles[role] = value; role_order.append(role)
    expected = set(spec.required_roles)
    if tuple(role_order) != spec.required_roles:
        raise InternalCondition("blocked", "HH1_INPUT_CLOSURE_INVALID", f"missing={sorted(expected-set(roles))}; extra={sorted(set(roles)-expected)}", blocker_class="input_invalid")
    output = resolve_inside(workspace, work["output_directory"], must_exist=False, file_only=False)
    result_path = output.parent / "stage-result.json"
    if output.exists() or result_path.exists():
        raise InternalRuntimeError("canonical output or task result already exists")
    if state_path == gate_path or state_path in roles.values() or gate_path in roles.values():
        raise InternalRuntimeError("operational references must remain outside the semantic read closure")
    return Context(workspace, path, work, gate, roles, output, schema_catalog, spec)


def output_ref(path: Path, staging: Path, context: Context, role: str) -> dict[str, str]:
    relative = path.resolve(strict=True).relative_to(staging.resolve(strict=True))
    target = context.output / relative
    return {"role": role, "path": target.relative_to(context.workspace).as_posix(), "sha256": sha256(path)}


def manifest_value(context: Context, staging: Path, status: str, name: str, fixed_roles: Mapping[str, str]) -> dict[str, Any]:
    excluded = {name}
    files = sorted((path for path in staging.rglob("*") if path.is_file() and path.name not in excluded), key=lambda path: path.relative_to(staging).as_posix())
    refs: list[dict[str, str]] = []
    roles: dict[str, dict[str, str]] = {}
    for path in files:
        relative = path.relative_to(staging).as_posix()
        role = fixed_roles.get(relative, f"content::{relative}")
        if role in roles:
            raise InternalRuntimeError(f"duplicate package artifact role: {role}")
        ref = {"role": role, "path": relative, "sha256": sha256(path)}
        refs.append(ref); roles[role] = ref
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": "HH1", "skill": context.spec.skill,
        "status": status, "files": refs, "artifact_roles": roles,
    }


def base_result(context: Context, outcome: str, staging: Path, manifest: Path, validation: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "stage": "HH1", "skill": context.spec.skill,
        "work_order_id": context.work_order["work_order_id"], "task_id": context.work_order["task_id"],
        "event_sequence": context.work_order["event_sequence"], "result_scope": "composite_internal", "result": outcome,
        "state_before_ref": context.work_order["state_before_ref"], "input_gate_ref": context.work_order["input_gate_ref"],
        "result_manifest_ref": output_ref(manifest, staging, context, "package_manifest" if outcome == "ready" else "result_manifest"),
        "validation_ref": output_ref(validation, staging, context, "validation"), "produced_at": context.work_order["result_timestamp"],
        "completion_ref": None, "internal_manifest_ref": None, "revision_class": None,
        "revision_report_ref": None, "candidate_ref": None, "local_defect_evidence": [],
        "author_event_ref": None, "gate_data_ref": None, "blocked_report_ref": None,
        "blocker_class": None, "affected_ids": [], "runtime_error_ref": None,
    }


def finalize_ready(context: Context, staging: Path, fixed_roles: Mapping[str, str]) -> dict[str, Any]:
    manifest = manifest_value(context, staging, "ready", "package-manifest.json", fixed_roles)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    write_json(staging / "package-manifest.json", manifest)
    validate_manifest(staging, manifest)
    validate_ready_profile(staging, context.spec.profile)
    result = base_result(context, "ready", staging, staging / "package-manifest.json", staging / "validation.json")
    result["internal_manifest_ref"] = output_ref(staging / "package-manifest.json", staging, context, "internal_manifest")
    context.catalog.validate(result, "stage-result.schema.json")
    validate_result_envelope(result, context.work_order)
    return result


def finalize_condition(context: Context, staging: Path, condition: InternalCondition, candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    staging.mkdir(parents=True, exist_ok=False)
    validation = {
        "schema_version": "1.0", "skill": context.spec.skill, "stage": "HH1",
        "hld_run_id": context.work_order["hld_run_id"], "status": condition.outcome,
        "checks": ["condition-bound", "no-canonical-residue"], "errors": [condition.code],
    }
    context.catalog.validate(validation, context.spec.validation_schema)
    write_json(staging / "validation.json", validation)
    roles = {"validation.json": "validation"}
    if condition.outcome == "blocked":
        gate = {"schema_version":"1.0","hld_run_id":context.work_order["hld_run_id"],"stage":"HH1","failed_gate":condition.code,"evidence":condition.evidence,"affected_ids":condition.affected_ids}
        report = {"schema_version":"1.0","skill":context.spec.skill,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"status":"blocked","blocker_class":condition.blocker_class,"code":condition.code,"evidence":condition.evidence,"affected_ids":condition.affected_ids,"required_action":"Repair the owning upstream artifact or input closure; this task must not invent replacement content."}
        context.catalog.validate(gate,"composite-internal-gate-data.schema.json");context.catalog.validate(report,"composite-internal-blocked-report.schema.json")
        write_json(staging/"gate-data.json",gate);write_json(staging/"blocked-report.json",report)
        roles.update({"gate-data.json":"gate_data","blocked-report.json":"blocked_report"})
    elif condition.outcome == "revise":
        report = {"schema_version":"1.0","skill":context.spec.skill,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"status":"revise","revision_class":"local_candidate","code":condition.code,"evidence":condition.evidence,"affected_ids":condition.affected_ids,"required_action":"Regenerate the bounded local candidate without changing HP1 authority."}
        context.catalog.validate(report,"composite-internal-revision-report.schema.json")
        write_json(staging/"revision-report.json",report);write_json(staging/"candidate.json",candidate or {"status":"candidate_rejected"})
        evidence = {"schema_version":"1.0","skill":context.spec.skill,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"code":condition.code,"evidence":condition.evidence,"affected_ids":condition.affected_ids}
        context.catalog.validate(evidence,"composite-local-defect-evidence.schema.json")
        write_json(staging/"local-defect-evidence.json",evidence)
        roles.update({"revision-report.json":"revision_report","candidate.json":"candidate","local-defect-evidence.json":"local_defect_evidence"})
    else:
        raise InternalRuntimeError(f"unsupported condition outcome: {condition.outcome}")
    manifest = manifest_value(context, staging, condition.outcome, "result-manifest.json", roles)
    context.catalog.validate(manifest,"package-manifest.schema.json");write_json(staging/"result-manifest.json",manifest);validate_manifest(staging,manifest)
    result=base_result(context,condition.outcome,staging,staging/"result-manifest.json",staging/"validation.json");result["affected_ids"]=condition.affected_ids
    if condition.outcome=="blocked":
        result.update({"gate_data_ref":output_ref(staging/"gate-data.json",staging,context,"gate_data"),"blocked_report_ref":output_ref(staging/"blocked-report.json",staging,context,"blocked_report"),"blocker_class":condition.blocker_class})
    else:
        result.update({"revision_class":"local_candidate","revision_report_ref":output_ref(staging/"revision-report.json",staging,context,"revision_report"),"candidate_ref":output_ref(staging/"candidate.json",staging,context,"candidate"),"local_defect_evidence":[output_ref(staging/"local-defect-evidence.json",staging,context,"local_defect_evidence")]})
    context.catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,context.work_order)
    return result


def finalize_runtime_error(context: Context, staging: Path, error: Exception, operation: str) -> dict[str, Any]:
    """Seal a post-admission runtime failure without leaving canonical residue."""
    staging.mkdir(parents=True, exist_ok=False)
    evidence = {
        "schema_version": "1.0", "harness": HARNESS, "skill": context.spec.skill,
        "stage": "HH1", "hld_run_id": context.work_order["hld_run_id"], "status": "runtime_error",
        "error_code": "HH1_INTERNAL_RUNTIME_FAILURE", "message": f"{type(error).__name__}: {error}",
        "failed_operation": operation,
    }
    context.catalog.validate(evidence, "composite-internal-runtime-error.schema.json")
    write_json(staging / "runtime-error.json", evidence)
    validation = {
        "schema_version": "1.0", "skill": context.spec.skill, "stage": "HH1",
        "hld_run_id": context.work_order["hld_run_id"], "status": "runtime_error",
        "checks": ["post-admission-runtime-failure", "no-canonical-residue"],
        "errors": ["HH1_INTERNAL_RUNTIME_FAILURE"],
    }
    context.catalog.validate(validation, context.spec.validation_schema)
    write_json(staging / "validation.json", validation)
    manifest = manifest_value(context, staging, "runtime_error", "result-manifest.json", {
        "runtime-error.json": "runtime_error", "validation.json": "validation",
    })
    context.catalog.validate(manifest, "package-manifest.schema.json")
    write_json(staging / "result-manifest.json", manifest); validate_manifest(staging, manifest)
    result = base_result(context, "runtime_error", staging, staging / "result-manifest.json", staging / "validation.json")
    result["runtime_error_ref"] = output_ref(staging / "runtime-error.json", staging, context, "runtime_error")
    context.catalog.validate(result, "stage-result.schema.json"); validate_result_envelope(result, context.work_order)
    return result


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


Build = Callable[[Context, Path], tuple[int, dict[str, Any]]]


def atomic_execute(context: Context, build: Build) -> tuple[int, dict[str, Any]]:
    temp = Path(tempfile.mkdtemp(prefix=f".{context.spec.profile.lower().replace('.', '-')}-", dir=context.workspace))
    first = temp / "first"; second = temp / "second"
    try:
        code, result = build(context, first)
        second_code, second_result = build(context, second)
        if code != second_code or canonical_bytes(result) != canonical_bytes(second_result) or _tree_bytes(first) != _tree_bytes(second):
            raise InternalRuntimeError("deterministic reproduction mismatch before commit")
        context.output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(first, context.output)
        result_path = context.output.parent / "stage-result.json"
        write_json(result_path, result)
        try:
            manifest_name = "package-manifest.json" if result["result"] == "ready" else "result-manifest.json"
            manifest = read_json(context.output / manifest_name)
            validate_manifest(context.output, manifest)
            validate_result_envelope(read_json(result_path), context.work_order)
        except Exception:
            shutil.rmtree(context.output, ignore_errors=True)
            result_path.unlink(missing_ok=True)
            raise
        return code, result
    finally:
        shutil.rmtree(temp, ignore_errors=True)
