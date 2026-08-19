"""Exact package-profile and package-external result-envelope checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .canonical import ContractError, read_json, verify_file_ref
from .contracts import INTERNAL_READY_PACKAGE_PROFILES, READY_PACKAGE_PROFILES


def package_files(package_dir: Path) -> set[str]:
    root = package_dir.resolve(strict=True)
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _match_profile(actual: set[str], required: tuple[str, ...], *, generation_evidence: bool = False) -> None:
    fixed = set(required)
    evidence = {path for path in actual if path.startswith("generation-evidence/") and path.endswith(".json")}
    if generation_evidence:
        if not evidence:
            raise ContractError("generation-evidence/*.json is required")
        actual = actual - evidence
    elif evidence:
        raise ContractError("generation evidence is forbidden by this profile")
    if actual != fixed:
        raise ContractError(f"package profile mismatch: expected={sorted(fixed)} actual={sorted(actual)}")


def validate_ready_profile(package_dir: Path, profile: str) -> None:
    actual = package_files(package_dir)
    if profile in READY_PACKAGE_PROFILES:
        _match_profile(actual, READY_PACKAGE_PROFILES[profile])
        return
    if profile in INTERNAL_READY_PACKAGE_PROFILES:
        generation = profile == "HH1.A"
        _match_profile(actual, INTERNAL_READY_PACKAGE_PROFILES[profile], generation_evidence=generation)
        return
    if profile in {"HA1", "HS1", "HC1", "HI1", "HR1", "HK1"}:
        canonical = {
            "HA1": "narrative-architecture.json", "HS1": "storyline-choreography.json",
            "HC1": "character-arc-placement.json", "HI1": "narrative-information-architecture.json",
            "HR1": "rhythm-continuity-architecture.json", "HK1": "key-scene-function-map.json",
        }[profile]
        preview = canonical.removesuffix(".json") + ".md"
        required = (canonical, "generation-session.json", "execution-record.json", preview, "validation.json", "package-manifest.json", "stage-completion.json")
        _match_profile(actual, required, generation_evidence=True)
        return
    raise ContractError(f"unknown package profile: {profile}")


def validate_manifest(package_dir: Path, manifest: Mapping[str, Any]) -> None:
    root = package_dir.resolve(strict=True)
    # Completion binds the finished manifest and therefore cannot be a member
    # of that manifest's content closure without creating a hash cycle.
    actual = package_files(root) - {"package-manifest.json", "result-manifest.json", "stage-completion.json"}
    refs = manifest.get("files")
    if not isinstance(refs, list):
        raise ContractError("manifest.files must be an array")
    declared_paths: set[str] = set()
    declared_refs: dict[tuple[str, str], str] = {}
    for ref in refs:
        path = verify_file_ref(ref, root)
        relative = path.relative_to(root).as_posix()
        if relative in declared_paths:
            raise ContractError(f"duplicate manifest path: {relative}")
        declared_paths.add(relative)
        declared_refs[(relative, ref["sha256"])] = ref["role"]
    if declared_paths != actual:
        raise ContractError(f"manifest closure mismatch: declared={sorted(declared_paths)} actual={sorted(actual)}")
    roles = manifest.get("artifact_roles")
    if not isinstance(roles, dict) or len(roles) != len(set(roles)):
        raise ContractError("artifact roles are invalid")
    for role, ref in roles.items():
        if ref.get("role") != role or (ref.get("path"), ref.get("sha256")) not in declared_refs:
            raise ContractError(f"unbound artifact role: {role}")


def validate_completion_bindings(workspace: Path, package_dir: Path, completion: Mapping[str, Any]) -> None:
    """Validate the acyclic completion -> manifest/validation/artifact envelope."""
    root = package_dir.resolve(strict=True)
    workspace_root = workspace.resolve(strict=True)
    manifest_path = verify_file_ref(completion.get("manifest_ref"), workspace_root)
    validation_path = verify_file_ref(completion.get("validation_ref"), workspace_root)
    if manifest_path != root / "package-manifest.json":
        raise ContractError("completion manifest_ref does not bind package-manifest.json")
    if validation_path != root / "validation.json":
        raise ContractError("completion validation_ref does not bind validation.json")
    manifest = read_json(manifest_path)
    validate_manifest(root, manifest)
    declared = {(item["path"], item["sha256"]) for item in manifest["files"]}
    artifacts = completion.get("canonical_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContractError("completion canonical_artifacts must be non-empty")
    for artifact in artifacts:
        path = verify_file_ref(artifact, workspace_root)
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as error:
            raise ContractError("completion canonical artifact is outside package") from error
        if (relative, artifact["sha256"]) not in declared:
            raise ContractError(f"completion artifact is not manifest-bound: {relative}")


def validate_result_envelope(result: Mapping[str, Any], work_order: Mapping[str, Any]) -> None:
    for field in ("hld_run_id", "revision", "stage", "work_order_id", "task_id", "event_sequence"):
        if result[field] != work_order[field]:
            raise ContractError(f"result does not copy work-order {field}")
    if result["produced_at"] != work_order["result_timestamp"]:
        raise ContractError("result produced_at must copy result_timestamp")
    outcome = result["result"]
    scope = result["result_scope"]
    if outcome == "ready" and scope == "top_level":
        if result.get("completion_ref") is None or result.get("internal_manifest_ref") is not None:
            raise ContractError("top-level ready requires only completion_ref")
    elif outcome == "ready" and scope == "composite_internal":
        if result.get("completion_ref") is not None or result.get("internal_manifest_ref") is None:
            raise ContractError("internal ready requires only internal_manifest_ref")
    elif outcome == "blocked":
        if not result.get("gate_data_ref") or not result.get("blocked_report_ref") or not result.get("blocker_class"):
            raise ContractError("blocked result lacks durable gate evidence")
    elif outcome == "runtime_error":
        if not result.get("runtime_error_ref"):
            raise ContractError("runtime error lacks evidence")
    elif outcome == "revise":
        if not result.get("revision_report_ref") or result.get("revision_class") not in {"local_candidate", "external_author_request"}:
            raise ContractError("revise result lacks revision evidence")
    else:
        raise ContractError("invalid result/scope combination")


def load_and_validate_workspace(workspace: Path, schema_catalog: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    work_order = read_json(workspace / "work-order.json")
    result = read_json(workspace / "stage-result.json")
    schema_catalog.validate(work_order, "work-order.schema.json")
    schema_catalog.validate(result, "stage-result.schema.json")
    validate_result_envelope(result, work_order)
    return work_order, result
