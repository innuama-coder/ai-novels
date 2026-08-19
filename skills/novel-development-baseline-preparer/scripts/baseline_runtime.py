#!/usr/bin/env python3
"""Deterministic runtime for preparing and validating development baselines."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError as error:  # pragma: no cover - environment failure
    raise RuntimeError(
        "jsonschema is required; run with `uv run --with jsonschema python ...`"
    ) from error


SKILL = "novel-development-baseline-preparer"
STAGES = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1")
DOMAINS = ("storylines", "world", "environments", "events", "characters", "narrative")
STAGE_DOMAINS = {
    "S1": "storylines",
    "W1": "world",
    "E1": "environments",
    "T1": "events",
    "C1": "characters",
}
CLASS_MAP = {
    "mandatory_controls": "mandatory",
    "development_freedoms": "freedom",
    "must_ask": "must_ask",
    "open_items": "open",
}
SOURCE_ID_RE = re.compile(
    r"^(INT|SUB|WLD|CHR|CAU|NAR|SLD|SL|SLC|WR|WF|WS|END|ENV|ZONE|EVD|EV|CHD|SLOT|REL|DEV|FND)-[A-Za-z0-9._-]+$"
)
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
FINAL_CHECKS = (
    "approved-current-run-state",
    "nine-current-stage-completions",
    "current-p1-manifest-and-validation",
    "current-h1-html-manifest-and-validation",
    "current-author-decision-and-development-handoff",
)
READY_CHECKS = (
    "formal-conception-completion-schema",
    "released-finalizer-snapshot",
    "approval-to-current-state-transition",
    "external-author-approval",
    "nine-current-stage-completions",
    "p1-package-integrity",
    "h1-html-integrity",
    "q1-no-actionable-findings",
    "one-run-id-and-closed-hash-chain",
    "lossless-control-projection",
    "complete-six-domain-inventory",
    "deterministic-markdown-projection",
    "four-file-package-closure",
)
HLD_RESPONSIBILITIES = (
    "overall-narrative-architecture",
    "multi-thread-choreography",
    "character-arc-placement",
    "act-and-chapter-progression",
    "key-scene-functions",
    "suspense-setup-probe-reveal-payoff",
    "time-space-pacing-tension-pov-information-architecture",
    "hld-to-lld-handoff-and-acceptance",
)
HLD_PROHIBITIONS = (
    "change-conception-authority",
    "resolve-author-owned-question",
    "produce-lld-material",
    "write-prose",
)
HLD_CAPABILITIES = (
    "traceable-conception-inheritance",
    "complete-multi-thread-architecture",
    "character-arc-and-event-alignment",
    "time-space-pacing-pov-information-control",
    "key-scene-function-coverage",
    "lld-ready-handoff-with-acceptance",
)
OWN_SCHEMA_DIR = Path(__file__).resolve().parents[1] / "references"
RELEASE_LOCK_PATH = OWN_SCHEMA_DIR / "supported-release-lock.json"


class RuntimeFailure(RuntimeError):
    """Raised when execution, rather than source readiness, is invalid."""


class ContractFailure(RuntimeError):
    """Raised for one or more source readiness failures."""

    def __init__(self, failures: list[dict[str, str]], *, run_id: str | None = None):
        self.failures = failures
        self.run_id = run_id
        super().__init__(failures[0]["code"] if failures else "BASE_UNKNOWN")


@dataclass(frozen=True)
class RequestContext:
    request: dict[str, Any]
    request_path: Path
    source_root: Path
    completion_path: Path
    current_state_pointer: Path
    release_descriptor: Path
    release_root: Path
    contract_dir: Path
    finalizer_source: Path
    output_dir: Path


@dataclass
class AdmittedSource:
    request_context: RequestContext
    catalog: "SchemaCatalog"
    run_id: str
    release: dict[str, Any]
    completion: dict[str, Any]
    final_validation: dict[str, Any]
    approval_state: dict[str, Any]
    current_state: dict[str, Any]
    author_decision: dict[str, Any]
    stage_completions: dict[str, dict[str, Any]]
    handoff: dict[str, Any]
    p1_root: Path
    p1_manifest: dict[str, Any]
    conception_package: dict[str, Any]
    author_control: dict[str, Any]
    design_index: dict[str, Any]
    cross_index: dict[str, Any]
    q1_review: dict[str, Any]
    source_paths: dict[str, Path]
    source_documents: dict[str, Any]
    lineage: dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


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


def read_json(path: Path, code: str, owner: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        block(code, str(path), owner, f"Provide a readable valid JSON artifact: {error}")
    if not isinstance(value, dict):
        block(code, str(path), owner, "Provide a JSON object artifact.")
    return value


def block(code: str, evidence: str, owner: str, action: str, *, run_id: str | None = None) -> None:
    raise ContractFailure(
        [{"code": code, "evidence": evidence, "owner": owner, "required_action": action}],
        run_id=run_id,
    )


def failure_report(
    request: Mapping[str, Any], failure: ContractFailure
) -> dict[str, Any]:
    failed_checks = [
        {key: item[key] for key in ("code", "evidence", "owner")}
        for item in failure.failures
    ]
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "skill": SKILL,
        "project_id": request["project_id"],
        "baseline_version": request["baseline_version"],
        "status": "blocked",
        "failed_checks": failed_checks,
        "required_action": failure.failures[0]["required_action"],
    }
    if failure.run_id:
        report["run_id"] = failure.run_id
    return report


class SchemaCatalog:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        if not self.directory.is_dir():
            raise RuntimeFailure(f"schema directory does not exist: {self.directory}")
        self.schemas: dict[str, dict[str, Any]] = {}
        resources: list[tuple[str, Resource]] = []
        for path in sorted(self.directory.glob("*.schema.json")):
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise RuntimeFailure(f"invalid schema catalog entry {path}: {error}") from error
            if not isinstance(schema, dict):
                raise RuntimeFailure(f"schema catalog entry is not an object: {path}")
            schema_id = schema.get("$id")
            if schema_id != path.name:
                raise RuntimeFailure(f"schema id mismatch: {path}")
            Draft202012Validator.check_schema(schema)
            self.schemas[path.name] = schema
            resources.append((path.name, Resource.from_contents(schema)))
        if not self.schemas:
            raise RuntimeFailure(f"empty schema catalog: {self.directory}")
        self.registry = Registry().with_resources(resources)

    def validate(self, value: Any, schema_name: str, code: str, owner: str, evidence: str) -> None:
        if schema_name not in self.schemas:
            block(code, evidence, owner, f"Restore required schema {schema_name}.")
        errors = sorted(
            Draft202012Validator(
                self.schemas[schema_name], registry=self.registry
            ).iter_errors(value),
            key=lambda item: (list(item.absolute_path), item.message),
        )
        if errors:
            first = errors[0]
            pointer = "/" + "/".join(str(part) for part in first.absolute_path)
            block(code, f"{evidence}#{pointer}: {first.message}", owner, "Regenerate the artifact with the released conception contract.")

    def catalog_sha256(self) -> str:
        return canonical_sha256(
            {name: sha256_file(self.directory / name) for name in sorted(self.schemas)}
        )


def validate_local(value: Any, schema_name: str) -> None:
    path = OWN_SCHEMA_DIR / schema_name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            raise ValueError("schema is not an object")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)
    except Exception as error:
        raise RuntimeFailure(f"local contract failure in {schema_name}: {error}") from error


def load_release_lock() -> dict[str, str]:
    try:
        value = json.loads(RELEASE_LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeFailure(f"invalid supported release lock: {error}") from error
    expected_keys = {
        "schema_version",
        "name",
        "version",
        "descriptor_sha256",
        "contract_catalog_sha256",
        "finalizer_sha256",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schema_version") != "1.0"
        or value.get("name") != "novel-conception-stage"
        or value.get("version") != "1.0.0"
        or any(
            not isinstance(value.get(key), str)
            or SHA_RE.fullmatch(value[key]) is None
            for key in (
                "descriptor_sha256",
                "contract_catalog_sha256",
                "finalizer_sha256",
            )
        )
    ):
        raise RuntimeFailure("supported release lock has an invalid contract")
    return value


def _resolve_from(base: Path, value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else base / path).resolve()


def _physical_path(path: Path) -> Path:
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path.absolute()))
    return path


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("not a safe relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", value):
        raise ValueError("not a safe relative POSIX path")
    return value


def resolve_relative(root: Path, relative: Any) -> Path:
    safe = _safe_relative_path(relative)
    physical_root = _physical_path(root)
    candidate = physical_root.joinpath(*PurePosixPath(safe).parts)
    resolved = candidate.resolve(strict=True)
    resolved.relative_to(physical_root.resolve(strict=True))
    if not resolved.is_file():
        raise ValueError("reference is not a file")
    return resolved


def candidate_relative(root: Path, relative: Any) -> Path:
    safe = _safe_relative_path(relative)
    physical_root = _physical_path(root)
    resolved_root = physical_root.resolve(strict=False)
    candidate = resolved_root.joinpath(*PurePosixPath(safe).parts).resolve(strict=False)
    candidate.relative_to(resolved_root)
    return candidate


def verify_ref(ref: Any, root: Path, label: str, owner: str) -> Path:
    if not isinstance(ref, dict) or set(ref) not in ({"path", "sha256"}, {"stage", "path", "sha256"}):
        block("BASE_REF_INVALID", label, owner, "Regenerate the artifact reference.")
    if not isinstance(ref.get("sha256"), str) or not SHA_RE.fullmatch(ref["sha256"]):
        block("BASE_REF_INVALID", label, owner, "Regenerate the SHA-256 reference.")
    try:
        path = resolve_relative(root, ref.get("path"))
    except (OSError, ValueError) as error:
        block("BASE_REF_UNSAFE_OR_MISSING", f"{label}: {error}", owner, "Restore the referenced artifact inside its declared package root.")
    actual = sha256_file(path)
    if not hmac.compare_digest(actual, ref["sha256"]):
        block("BASE_REF_HASH_MISMATCH", label, owner, "Restore the immutable referenced artifact or regenerate its owner package.")
    return path


def root_ref(path: Path, *, root: Path, root_name: str) -> dict[str, str]:
    physical_root = _physical_path(root).resolve(strict=True)
    resolved = _physical_path(path).resolve(strict=True)
    relative = resolved.relative_to(physical_root).as_posix()
    return {"root": root_name, "path": relative, "sha256": sha256_file(resolved)}


def local_ref(path: Path, *, root: Path) -> dict[str, str]:
    physical_root = _physical_path(root).resolve(strict=True)
    resolved = _physical_path(path).resolve(strict=True)
    return {
        "path": resolved.relative_to(physical_root).as_posix(),
        "sha256": sha256_file(resolved),
    }


def _same_ref(left: Any, right: Any) -> bool:
    return (
        isinstance(left, dict)
        and isinstance(right, dict)
        and left.get("path") == right.get("path")
        and left.get("sha256") == right.get("sha256")
    )


def verify_manifest(manifest: Mapping[str, Any], root: Path, owner: str) -> None:
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        block("BASE_MANIFEST_INVALID", str(root), owner, "Regenerate the package manifest.")
    bound: set[tuple[str, str]] = set()
    paths: set[str] = set()
    for index, ref in enumerate(files):
        path = verify_ref(ref, root, f"manifest.files[{index}]", owner)
        key = (path.relative_to(_physical_path(root).resolve(strict=True)).as_posix(), ref["sha256"])
        if key[0] in paths:
            block("BASE_MANIFEST_DUPLICATE_PATH", key[0], owner, "Regenerate a unique manifest file inventory.")
        paths.add(key[0])
        bound.add(key)
    refs: list[tuple[str, Any]] = []
    roles = manifest.get("artifact_roles")
    if isinstance(roles, dict):
        refs.extend((f"artifact_roles.{key}", value) for key, value in roles.items())
    refs.append(("validation", manifest.get("validation")))
    implementation = manifest.get("implementation")
    if isinstance(implementation, list):
        refs.extend((f"implementation[{index}]", value) for index, value in enumerate(implementation))
    for label, ref in refs:
        if not isinstance(ref, dict):
            block("BASE_MANIFEST_ROLE_INVALID", label, owner, "Bind every role to one manifest file reference.")
        key = (ref.get("path"), ref.get("sha256"))
        if key not in bound:
            block("BASE_MANIFEST_ROLE_UNBOUND", label, owner, "Bind every role, validation and implementation reference in files.")


def load_request(request_path: Path) -> RequestContext:
    path = request_path.resolve(strict=True)
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeFailure(f"invalid preparation request: {error}") from error
    if not isinstance(request, dict):
        raise RuntimeFailure("invalid preparation request: root must be an object")
    try:
        validate_local(request, "preparation-request.schema.json")
    except Exception as error:
        raise RuntimeFailure(f"invalid preparation request: {error}") from error
    base = path.parent
    context = RequestContext(
        request=request,
        request_path=path,
        source_root=_resolve_from(base, request["source_root"]),
        completion_path=Path(),
        current_state_pointer=Path(),
        release_descriptor=_resolve_from(base, request["release_descriptor"]),
        release_root=_resolve_from(base, request["release_descriptor"]).parent,
        contract_dir=_resolve_from(base, request["contract_dir"]),
        finalizer_source=_resolve_from(base, request["finalizer_source"]),
        output_dir=_resolve_from(base, request["output_dir"]),
    )
    try:
        completion_path = candidate_relative(context.source_root, request["completion_path"])
        current_pointer = candidate_relative(context.source_root, request["current_state_pointer"])
    except (OSError, ValueError) as error:
        raise RuntimeFailure(f"unsafe request-relative input path: {error}") from error
    context = RequestContext(
        **{
            **context.__dict__,
            "completion_path": completion_path,
            "current_state_pointer": current_pointer,
        }
    )
    for label, required in (
        ("release descriptor", context.release_descriptor),
        ("contract directory", context.contract_dir),
        ("released finalizer", context.finalizer_source),
    ):
        if not required.exists():
            raise RuntimeFailure(f"{label} does not exist: {required}")
    source = context.source_root.resolve()
    output = context.output_dir.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise RuntimeFailure(
            "output_dir must be disjoint from source_root: it may not equal, "
            "descend from, or contain source_root"
        )
    return context


def _formal(catalog: SchemaCatalog, value: Any, name: str, code: str, owner: str, evidence: str) -> None:
    catalog.validate(value, name, code, owner, evidence)


def _verify_decision_paths(
    decision: Mapping[str, Any], source_root: Path
) -> dict[str, dict[str, Path]]:
    result: dict[str, dict[str, Path]] = {}
    for section, fields in (
        ("machine_package", ("completion", "manifest")),
        ("human_review_package", ("completion", "manifest", "html")),
    ):
        package = decision[section]
        result[section] = {}
        for stem in fields:
            ref = {"path": package[f"{stem}_path"], "sha256": package[f"{stem}_sha256"]}
            result[section][stem] = verify_ref(
                ref,
                source_root,
                f"author_decision.{section}.{stem}",
                "author-decision-gate",
            )
    return result


def _relative_ref_from_local(ref: Mapping[str, Any], local_root: Path, source_root: Path) -> dict[str, str]:
    path = verify_ref(dict(ref), local_root, "local artifact", "P1")
    return root_ref(path, root=source_root, root_name="source")


def admit_source(context: RequestContext) -> AdmittedSource:
    if not context.source_root.is_dir():
        block(
            "BASE_SOURCE_ROOT_MISSING",
            str(context.source_root),
            "conception-final",
            "Provide the immutable conception run root.",
        )
    catalog = SchemaCatalog(context.contract_dir)
    release = read_json(context.release_descriptor, "BASE_RELEASE_INVALID", "conception-release")
    if (
        release.get("name") != "novel-conception-stage"
        or release.get("version") != "1.0.0"
        or release.get("status") != "frozen"
        or release.get("terminal") != "final"
        or release.get("compatibility_policy", {}).get("author_approval_required_for_final") is not True
    ):
        block("BASE_RELEASE_UNSUPPORTED", str(context.release_descriptor), "conception-release", "Use the frozen novel-conception-stage@1.0.0 release.")
    release_lock = load_release_lock()
    observed_release = {
        "descriptor_sha256": sha256_file(context.release_descriptor),
        "contract_catalog_sha256": catalog.catalog_sha256(),
        "finalizer_sha256": sha256_file(context.finalizer_source),
    }
    mismatched_release_parts = sorted(
        key for key, value in observed_release.items() if value != release_lock[key]
    )
    if mismatched_release_parts:
        block(
            "BASE_RELEASE_LOCK_MISMATCH",
            ",".join(mismatched_release_parts),
            "conception-release",
            "Use the exact release descriptor, formal contract catalog, and finalizer pinned by this skill.",
        )

    completion_root = context.completion_path.parent
    expected_final_files = {
        "conception-completion.json",
        "validation.json",
        "implementation/final_completion.py",
    }
    actual_final_files = {
        path.relative_to(completion_root).as_posix()
        for path in completion_root.rglob("*")
        if path.is_file()
    }
    if actual_final_files != expected_final_files:
        block("BASE_FINAL_PACKAGE_BOUNDARY_INVALID", str(completion_root), "conception-final", "Republish the exact three-file final completion package.")
    completion = read_json(context.completion_path, "BASE_FINAL_COMPLETION_INVALID", "conception-final")
    _formal(catalog, completion, "conception-completion.schema.json", "BASE_FINAL_COMPLETION_SCHEMA_INVALID", "conception-final", str(context.completion_path))
    run_id = completion["run_id"]
    finalizer_snapshot = completion_root / "implementation" / "final_completion.py"
    if finalizer_snapshot.read_bytes() != context.finalizer_source.read_bytes():
        block("BASE_FINALIZER_SNAPSHOT_MISMATCH", str(finalizer_snapshot), "conception-release", "Republish final completion with the released finalizer implementation.", run_id=run_id)

    final_validation_path = verify_ref(completion["validation"], context.source_root, "completion.validation", "conception-final")
    final_validation = read_json(final_validation_path, "BASE_FINAL_VALIDATION_INVALID", "conception-final")
    if (
        set(final_validation) != {"schema_version", "run_id", "verdict", "checks", "p1_validation", "h1_html_validation"}
        or final_validation.get("schema_version") != "2.0"
        or final_validation.get("run_id") != run_id
        or final_validation.get("verdict") != "ready"
        or tuple(final_validation.get("checks", ())) != FINAL_CHECKS
    ):
        block("BASE_FINAL_VALIDATION_INVALID", str(final_validation_path), "conception-final", "Republish final completion with its deterministic validation record.", run_id=run_id)

    approval_state_path = verify_ref(completion["run_state"], context.source_root, "completion.run_state", "conception-orchestrator/final")
    approval_state = read_json(approval_state_path, "BASE_APPROVAL_STATE_INVALID", "conception-orchestrator/final")
    _formal(catalog, approval_state, "autonomous-run-state.schema.json", "BASE_APPROVAL_STATE_SCHEMA_INVALID", "conception-orchestrator/final", str(approval_state_path))

    pointer = read_json(context.current_state_pointer, "BASE_CURRENT_STATE_POINTER_INVALID", "conception-orchestrator/final")
    if set(pointer) != {"schema_version", "state"} or pointer.get("schema_version") != "2.0":
        block("BASE_CURRENT_STATE_POINTER_INVALID", str(context.current_state_pointer), "conception-orchestrator/final", "Publish the canonical current-state pointer.", run_id=run_id)
    current_state_path = verify_ref(pointer["state"], context.source_root, "current-state.state", "conception-orchestrator/final")
    current_state = read_json(current_state_path, "BASE_CURRENT_STATE_INVALID", "conception-orchestrator/final")
    _formal(catalog, current_state, "autonomous-run-state.schema.json", "BASE_CURRENT_STATE_SCHEMA_INVALID", "conception-orchestrator/final", str(current_state_path))
    if (
        approval_state.get("run_id") != run_id
        or approval_state.get("status") != "approved"
        or approval_state.get("development_status") != "not_ready"
        or approval_state.get("active_return") is not None
        or current_state.get("run_id") != run_id
        or current_state.get("status") != "approved"
        or current_state.get("development_status") != "ready"
        or current_state.get("active_return") is not None
        or not _same_ref(current_state.get("previous_state"), completion["run_state"])
        or current_state.get("current_stage_completions") != completion["stage_completions"]
        or current_state.get("author_decision") != completion["author_decision"]
    ):
        block("BASE_FINAL_STATE_TRANSITION_INVALID", str(current_state_path), "conception-orchestrator/final", "Replay or republish the approved final state transition.", run_id=run_id)

    author_decision_path = verify_ref(completion["author_decision"], context.source_root, "completion.author_decision", "author-decision-gate")
    author_decision = read_json(author_decision_path, "BASE_AUTHOR_DECISION_INVALID", "author-decision-gate")
    _formal(catalog, author_decision, "author-decision.schema.json", "BASE_AUTHOR_DECISION_SCHEMA_INVALID", "author-decision-gate", str(author_decision_path))
    if author_decision.get("run_id") != run_id or author_decision.get("decision") != "approved":
        block("BASE_AUTHOR_APPROVAL_REQUIRED", str(author_decision_path), "author-decision-gate", "Record one external approved conception decision.", run_id=run_id)
    decision_paths = _verify_decision_paths(author_decision, context.source_root)

    if set(completion["stage_completions"]) != set(STAGES):
        block("BASE_STAGE_SET_INVALID", str(context.completion_path), "conception-final", "Publish all nine current stage completions.", run_id=run_id)
    stage_completions: dict[str, dict[str, Any]] = {}
    stage_paths: dict[str, Path] = {}
    stage_manifests: dict[str, dict[str, Any]] = {}
    stage_manifest_paths: dict[str, Path] = {}
    for stage in STAGES:
        ref = completion["stage_completions"][stage]
        stage_path = verify_ref(ref, context.source_root, f"completion.stage_completions.{stage}", stage)
        stage_doc = read_json(stage_path, "BASE_STAGE_COMPLETION_INVALID", stage)
        _formal(catalog, stage_doc, "stage-completion.schema.json", "BASE_STAGE_COMPLETION_SCHEMA_INVALID", stage, str(stage_path))
        if stage_doc.get("run_id") != run_id or stage_doc.get("stage") != stage or stage_doc.get("status") != "ready":
            block("BASE_STAGE_COMPLETION_INVALID", str(stage_path), stage, "Regenerate the current ready stage completion.", run_id=run_id)
        manifest_path = verify_ref(
            stage_doc["manifest"], context.source_root, f"{stage}.manifest", stage
        )
        validation_path = verify_ref(
            stage_doc["validation"], context.source_root, f"{stage}.validation", stage
        )
        verify_ref(
            stage_doc["input_gate"], context.source_root, f"{stage}.input_gate", stage
        )
        stage_root = stage_path.parent
        if any(
            path.parent != stage_root
            for path in (manifest_path, validation_path)
        ):
            block(
                "BASE_STAGE_PACKAGE_ROOT_MISMATCH",
                stage,
                stage,
                "Republish the stage completion, manifest, and validation in one package root.",
                run_id=run_id,
            )
        manifest = read_json(manifest_path, "BASE_STAGE_MANIFEST_INVALID", stage)
        _formal(
            catalog,
            manifest,
            "package-manifest.schema.json",
            "BASE_STAGE_MANIFEST_SCHEMA_INVALID",
            stage,
            str(manifest_path),
        )
        verify_manifest(manifest, stage_root, stage)
        if (
            manifest.get("run_id") != run_id
            or manifest.get("stage") != stage
            or manifest.get("verdict") != "ready"
            or verify_ref(manifest["validation"], stage_root, f"{stage}.manifest.validation", stage)
            != validation_path
        ):
            block(
                "BASE_STAGE_PACKAGE_BINDING_INVALID",
                stage,
                stage,
                "Regenerate the stage package and completion from one ready run.",
                run_id=run_id,
            )
        stage_completions[stage] = stage_doc
        stage_paths[stage] = stage_path
        stage_manifests[stage] = manifest
        stage_manifest_paths[stage] = manifest_path

    p1_manifest_path = verify_ref(completion["p1_manifest"], context.source_root, "completion.p1_manifest", "P1")
    if p1_manifest_path != stage_manifest_paths["P1"]:
        block(
            "BASE_P1_MANIFEST_NOT_CURRENT_STAGE",
            str(p1_manifest_path),
            "P1",
            "Bind final completion to the current P1 stage manifest.",
            run_id=run_id,
        )
    p1_root = p1_manifest_path.parent
    p1_manifest = read_json(p1_manifest_path, "BASE_P1_MANIFEST_INVALID", "P1")
    _formal(catalog, p1_manifest, "package-manifest.schema.json", "BASE_P1_MANIFEST_SCHEMA_INVALID", "P1", str(p1_manifest_path))
    verify_manifest(p1_manifest, p1_root, "P1")
    if p1_manifest.get("run_id") != run_id or p1_manifest.get("stage") != "P1" or p1_manifest.get("package_profile") != "conception-package":
        block("BASE_P1_MANIFEST_INVALID", str(p1_manifest_path), "P1", "Regenerate the current P1 conception package.", run_id=run_id)
    p1_validation_path = verify_ref(stage_completions["P1"]["validation"], context.source_root, "P1.validation", "P1")
    if not _same_ref(final_validation["p1_validation"], local_ref(p1_validation_path, root=context.source_root)):
        block("BASE_P1_VALIDATION_MISMATCH", str(p1_validation_path), "conception-final", "Republish final completion against the current P1 validation.", run_id=run_id)
    p1_validation = read_json(p1_validation_path, "BASE_P1_VALIDATION_INVALID", "P1")
    if p1_validation.get("verdict") != "ready" or p1_validation.get("errors") != []:
        block("BASE_P1_NOT_READY", str(p1_validation_path), "P1", "Resolve P1 validation errors and rerun P1.", run_id=run_id)

    h1_html_manifest_path = verify_ref(completion["h1_html_manifest"], context.source_root, "completion.h1_html_manifest", "H1-C")
    h1_html_root = h1_html_manifest_path.parent
    h1_html_manifest = read_json(h1_html_manifest_path, "BASE_H1_HTML_MANIFEST_INVALID", "H1-C")
    _formal(catalog, h1_html_manifest, "package-manifest.schema.json", "BASE_H1_HTML_MANIFEST_SCHEMA_INVALID", "H1-C", str(h1_html_manifest_path))
    verify_manifest(h1_html_manifest, h1_html_root, "H1-C")
    if h1_html_manifest.get("run_id") != run_id or h1_html_manifest.get("package_profile") != "h1-html":
        block("BASE_H1_HTML_MANIFEST_INVALID", str(h1_html_manifest_path), "H1-C", "Regenerate the current H1 HTML package.", run_id=run_id)
    h1_stage_root = stage_manifest_paths["H1"].parent
    bound_h1_html_ref = stage_manifests["H1"]["artifact_roles"].get("html_manifest")
    verify_ref(
        bound_h1_html_ref,
        h1_stage_root,
        "H1.stage.html_manifest",
        "H1",
    )
    execution_refs = [
        ref
        for ref in stage_manifests["H1"].get("files", [])
        if ref.get("path") == "execution-record.json"
    ]
    if len(execution_refs) != 1:
        block(
            "BASE_H1_EXECUTION_RECORD_MISSING",
            str(h1_stage_root),
            "H1",
            "Republish H1 with one manifest-bound execution record.",
            run_id=run_id,
        )
    h1_execution_path = verify_ref(
        execution_refs[0], h1_stage_root, "H1.stage.execution_record", "H1"
    )
    h1_execution = read_json(
        h1_execution_path, "BASE_H1_EXECUTION_RECORD_INVALID", "H1"
    )
    if (
        not isinstance(bound_h1_html_ref, dict)
        or bound_h1_html_ref.get("sha256") != completion["h1_html_manifest"]["sha256"]
        or h1_execution.get("workspace_artifacts", {}).get("html_manifest")
        != completion["h1_html_manifest"]
    ):
        block(
            "BASE_H1_HTML_NOT_CURRENT_STAGE",
            str(h1_html_manifest_path),
            "H1",
            "Bind H1's manifest snapshot and execution record to the final HTML manifest.",
            run_id=run_id,
        )
    h1_validation_path = verify_ref(h1_html_manifest["validation"], h1_html_root, "H1-html.validation", "H1-C")
    if not _same_ref(final_validation["h1_html_validation"], local_ref(h1_validation_path, root=context.source_root)):
        block("BASE_H1_VALIDATION_MISMATCH", str(h1_validation_path), "conception-final", "Republish final completion against the current H1 validation.", run_id=run_id)
    h1_html_path = verify_ref(
        h1_html_manifest["artifact_roles"].get("html"),
        h1_html_root,
        "H1-html.html",
        "H1-C",
    )
    if (
        decision_paths["machine_package"]["completion"] != stage_paths["P1"]
        or decision_paths["machine_package"]["manifest"] != stage_manifest_paths["P1"]
        or decision_paths["human_review_package"]["completion"] != stage_paths["H1"]
        or decision_paths["human_review_package"]["manifest"] != stage_manifest_paths["H1"]
        or decision_paths["human_review_package"]["html"] != h1_html_path
    ):
        block(
            "BASE_AUTHOR_DECISION_PACKAGE_DRIFT",
            str(author_decision_path),
            "author-decision-gate",
            "Record author approval against the current P1 and H1 packages.",
            run_id=run_id,
        )

    roles = p1_manifest["artifact_roles"]
    required_roles = {
        "conception_package", "author_control_baseline", "authoritative_design_index",
        "cross_model_index", "traceability", "development_handoff",
    }
    if not required_roles.issubset(roles):
        block("BASE_P1_ROLES_MISSING", str(p1_manifest_path), "P1", "Regenerate P1 with all authoritative artifact roles.", run_id=run_id)
    role_paths = {name: verify_ref(roles[name], p1_root, f"P1.{name}", "P1") for name in required_roles}
    handoff_path = verify_ref(completion["development_handoff"], context.source_root, "completion.development_handoff", "P1")
    if handoff_path != role_paths["development_handoff"]:
        block("BASE_HANDOFF_NOT_CURRENT_P1", str(handoff_path), "P1", "Bind final completion to the current P1 development handoff.", run_id=run_id)
    handoff = read_json(handoff_path, "BASE_HANDOFF_INVALID", "P1")
    _formal(catalog, handoff, "development-handoff.schema.json", "BASE_HANDOFF_SCHEMA_INVALID", "P1", str(handoff_path))
    if handoff.get("run_id") != run_id or handoff.get("status") != "ready" or handoff.get("development_entrypoint", {}).get("next_stage") != "novel-development":
        block("BASE_HANDOFF_NOT_READY", str(handoff_path), "P1", "Regenerate a ready novel-development handoff.", run_id=run_id)

    conception_package = read_json(role_paths["conception_package"], "BASE_CONCEPTION_PACKAGE_INVALID", "P1")
    _formal(catalog, conception_package, "novel-conception-package.schema.json", "BASE_CONCEPTION_PACKAGE_SCHEMA_INVALID", "P1", str(role_paths["conception_package"]))
    author_control = read_json(role_paths["author_control_baseline"], "BASE_AUTHOR_CONTROL_INVALID", "B0")
    _formal(catalog, author_control, "author-control-baseline.schema.json", "BASE_AUTHOR_CONTROL_SCHEMA_INVALID", "B0", str(role_paths["author_control_baseline"]))
    design_index = read_json(role_paths["authoritative_design_index"], "BASE_DESIGN_INDEX_INVALID", "P1")
    cross_index = read_json(role_paths["cross_model_index"], "BASE_CROSS_INDEX_INVALID", "P1")
    if conception_package.get("run_id") != run_id or author_control.get("run_id") != run_id or design_index.get("run_id") != run_id or cross_index.get("run_id") != run_id:
        block("BASE_P1_RUN_ID_MISMATCH", str(p1_root), "P1", "Regenerate P1 from one conception run.", run_id=run_id)
    if conception_package.get("cross_model_index") != cross_index:
        block("BASE_CROSS_INDEX_DRIFT", str(role_paths["cross_model_index"]), "P1", "Regenerate the P1 embedded and standalone cross-model index together.", run_id=run_id)

    if not _same_ref(handoff.get("conception_package"), roles["conception_package"]) or not _same_ref(handoff.get("author_control_baseline"), roles["author_control_baseline"]):
        block("BASE_HANDOFF_AUTHORITY_MISMATCH", str(handoff_path), "P1", "Regenerate the handoff from the current P1 authority artifacts.", run_id=run_id)

    q1_manifest_path = verify_ref(stage_completions["Q1"]["manifest"], context.source_root, "Q1.manifest", "Q1")
    q1_root = q1_manifest_path.parent
    q1_manifest = read_json(q1_manifest_path, "BASE_Q1_MANIFEST_INVALID", "Q1")
    _formal(catalog, q1_manifest, "package-manifest.schema.json", "BASE_Q1_MANIFEST_SCHEMA_INVALID", "Q1", str(q1_manifest_path))
    verify_manifest(q1_manifest, q1_root, "Q1")
    q1_review_path = verify_ref(q1_manifest["artifact_roles"]["canonical"], q1_root, "Q1.canonical", "Q1")
    q1_review = read_json(q1_review_path, "BASE_Q1_REVIEW_INVALID", "Q1")
    _formal(catalog, q1_review, "conception-review.schema.json", "BASE_Q1_REVIEW_SCHEMA_INVALID", "Q1", str(q1_review_path))
    if q1_review.get("run_id") != run_id or q1_review.get("verdict") != "ready" or q1_review.get("return_request") is not None or any(item.get("severity") != "note" for item in q1_review.get("findings", [])):
        block("BASE_Q1_ACTIONABLE_FINDING", str(q1_review_path), "Q1", "Resolve Q1 actionable findings and rerun Q1 through final.", run_id=run_id)

    model_paths: dict[str, Path] = {}
    model_docs: dict[str, Any] = {}
    for stage, ref in conception_package["canonical_models"].items():
        path = verify_ref(ref, p1_root, f"conception.canonical_models.{stage}", stage)
        document = read_json(path, "BASE_CANONICAL_MODEL_INVALID", stage)
        # The released P1/final chain already owns full model-schema validation.
        # This runtime re-verifies every model value it projects through the
        # P1 cross-model index below, avoiding a second, divergent model gate.
        if document.get("run_id") != run_id or document.get("stage") != stage or document.get("status") != "ready":
            block("BASE_CANONICAL_MODEL_INVALID", str(path), stage, "Regenerate the current canonical model.", run_id=run_id)
        model_paths[stage] = path
        model_docs[stage] = document

    design_index_items = design_index.get("artifacts")
    if (
        not isinstance(design_index_items, list)
        or len(design_index_items) != 6
        or any(
            not isinstance(item, dict)
            or set(item) != {"domain", "baseline_artifact", "materialized"}
            for item in design_index_items
        )
        or {item["domain"] for item in design_index_items}
        != {"I0", "I1", "I2", "I3", "I4", "I5"}
    ):
        block("BASE_DESIGN_INDEX_INCOMPLETE", str(role_paths["authoritative_design_index"]), "P1", "Regenerate the six-domain authoritative design index.", run_id=run_id)
    design_materialized: dict[str, Path] = {}
    b0_root = stage_manifest_paths["B0"].parent
    for item in design_index_items:
        baseline_path = verify_ref(
            item["baseline_artifact"],
            b0_root,
            f"design-index.{item['domain']}.baseline_artifact",
            "B0",
        )
        path = verify_ref(item.get("materialized"), p1_root, f"design-index.{item.get('domain')}", "P1")
        if sha256_file(baseline_path) != sha256_file(path):
            block(
                "BASE_DESIGN_MATERIALIZATION_DRIFT",
                item["domain"],
                "P1",
                "Regenerate P1's materialized author controls from the current B0 baseline.",
                run_id=run_id,
            )
        design_materialized[item["domain"]] = path

    lineage = {
        "release_descriptor": root_ref(context.release_descriptor, root=context.release_root, root_name="release"),
        "conception_completion": root_ref(context.completion_path, root=context.source_root, root_name="source"),
        "final_validation": root_ref(final_validation_path, root=context.source_root, root_name="source"),
        "approval_state": root_ref(approval_state_path, root=context.source_root, root_name="source"),
        "current_state": root_ref(current_state_path, root=context.source_root, root_name="source"),
        "author_decision": root_ref(author_decision_path, root=context.source_root, root_name="source"),
        "stage_completions": {stage: root_ref(stage_paths[stage], root=context.source_root, root_name="source") for stage in STAGES},
        "p1_manifest": root_ref(p1_manifest_path, root=context.source_root, root_name="source"),
        "h1_html_manifest": root_ref(h1_html_manifest_path, root=context.source_root, root_name="source"),
        "conception_package": root_ref(role_paths["conception_package"], root=context.source_root, root_name="source"),
        "author_control_baseline": root_ref(role_paths["author_control_baseline"], root=context.source_root, root_name="source"),
        "authoritative_design_index": root_ref(role_paths["authoritative_design_index"], root=context.source_root, root_name="source"),
        "cross_model_index": root_ref(role_paths["cross_model_index"], root=context.source_root, root_name="source"),
        "traceability": root_ref(role_paths["traceability"], root=context.source_root, root_name="source"),
        "development_handoff": root_ref(handoff_path, root=context.source_root, root_name="source"),
        "q1_review": root_ref(q1_review_path, root=context.source_root, root_name="source"),
    }
    source_paths = {**model_paths, **{f"I{index}": design_materialized[f"I{index}"] for index in range(6)}}
    source_documents = {**model_docs}
    for domain, path in design_materialized.items():
        source_documents[domain] = read_json(path, "BASE_DESIGN_ARTIFACT_INVALID", domain)
    return AdmittedSource(
        request_context=context,
        catalog=catalog,
        run_id=run_id,
        release=release,
        completion=completion,
        final_validation=final_validation,
        approval_state=approval_state,
        current_state=current_state,
        author_decision=author_decision,
        stage_completions=stage_completions,
        handoff=handoff,
        p1_root=p1_root,
        p1_manifest=p1_manifest,
        conception_package=conception_package,
        author_control=author_control,
        design_index=design_index,
        cross_index=cross_index,
        q1_review=q1_review,
        source_paths=source_paths,
        source_documents=source_documents,
        lineage=lineage,
    )


def json_pointer(document: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("invalid JSON Pointer")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise ValueError("JSON Pointer traverses a scalar")
    return value


def source_text(value: Any) -> str:
    return value if isinstance(value, str) else canonical_json(value)


def binding_domain(source_id: str, stage: str) -> str:
    if stage in STAGE_DOMAINS:
        return STAGE_DOMAINS[stage]
    prefix = source_id.split("-", 1)[0]
    return {
        "INT": "intent", "SUB": "storylines", "WLD": "world", "CHR": "characters",
        "CAU": "storylines", "NAR": "narrative", "SLD": "storylines", "SL": "storylines",
        "SLC": "storylines", "WR": "world", "WF": "world", "WS": "world",
        "END": "environments", "ENV": "environments", "ZONE": "environments",
        "EVD": "events", "EV": "events", "CHD": "characters", "SLOT": "characters",
        "REL": "characters", "DEV": "cross-domain", "FND": "quality",
    }.get(prefix, "cross-domain")


def hld_instruction(source_id: str, classification: str) -> str:
    templates = {
        "mandatory": "Preserve the complete authoritative definition for {id}; do not alter, omit, narrow, enlarge, or resolve it.",
        "freedom": "HLD may decide only within the complete authoritative definition for {id}; preserve all stated limits and authorities.",
        "must_ask": "Block every HLD decision affected by {id} until an external author decision is recorded; preserve the authoritative definition unchanged.",
        "open": "Keep {id} unresolved unless an authorized downstream contract explicitly requires resolution; preserve the authoritative definition unchanged.",
    }
    return templates[classification].format(id=source_id)


def _authority_partition(source: AdmittedSource) -> dict[str, str]:
    partition = source.conception_package["authority_partition"]
    result: dict[str, str] = {}
    for authority_class, values in partition.items():
        for source_id in values:
            if source_id in result:
                block("BASE_AUTHORITY_PARTITION_OVERLAP", source_id, "P1", "Regenerate a disjoint P1 authority partition.", run_id=source.run_id)
            result[source_id] = authority_class
    return result


def _author_control_records(source: AdmittedSource) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for registry in source.author_control["control_registry"]:
        source_id = registry["id"]
        if source_id in records:
            block(
                "BASE_AUTHOR_CONTROL_DUPLICATE",
                source_id,
                "B0",
                "Regenerate a control registry with one entry per stable ID.",
                run_id=source.run_id,
            )
        domain = registry["domain"]
        document = source.source_documents[domain]
        controls = document.get("controls")
        if not isinstance(controls, list):
            block("BASE_AUTHOR_CONTROL_SOURCE_INVALID", str(source.source_paths[domain]), "B0", "Regenerate the materialized interview control projection.", run_id=source.run_id)
        matches = [(index, item) for index, item in enumerate(controls) if isinstance(item, dict) and item.get("id") == source_id]
        if len(matches) != 1:
            block("BASE_AUTHOR_CONTROL_SOURCE_AMBIGUOUS", source_id, "B0", "Regenerate a unique materialized control definition.", run_id=source.run_id)
        index, item = matches[0]
        value = item.get("value")
        if canonical_sha256(value) != registry["value_sha256"] or item.get("hardness") != registry["hardness"]:
            block("BASE_AUTHOR_CONTROL_VALUE_DRIFT", source_id, "B0", "Regenerate B0 and P1 from the approved interview controls.", run_id=source.run_id)
        records[source_id] = {
            "id": source_id,
            "stage": domain,
            "kind": "author_control",
            "pointer": f"/controls/{index}/value",
            "value": value,
            "value_sha256": registry["value_sha256"],
            "path": source.source_paths[domain],
            "authority_class": registry["hardness"],
        }
    return records


def _canonical_records(source: AdmittedSource) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {}
    definitions = source.cross_index.get("definitions")
    if not isinstance(definitions, list):
        block("BASE_CROSS_INDEX_INVALID", str(source.lineage["cross_model_index"]), "P1", "Regenerate the P1 cross-model index.", run_id=source.run_id)
    for definition in definitions:
        if not isinstance(definition, dict) or set(definition) != {"id", "json_pointer", "kind", "stage", "value_sha256"}:
            block("BASE_CROSS_INDEX_DEFINITION_INVALID", canonical_json(definition), "P1", "Regenerate the P1 cross-model index.", run_id=source.run_id)
        stage = definition["stage"]
        if stage not in STAGE_DOMAINS:
            continue
        try:
            value = json_pointer(source.source_documents[stage], definition["json_pointer"])
        except (KeyError, IndexError, ValueError, TypeError) as error:
            block("BASE_CROSS_INDEX_POINTER_INVALID", f"{definition['id']}:{error}", stage, "Regenerate the canonical model and cross-model index together.", run_id=source.run_id)
        indexed_value = value
        if definition["kind"] == "e1_operational_slot":
            slot_id = definition["id"]
            bound_slot = value.get("actor_slot_id") if isinstance(value, Mapping) else value
            if bound_slot != slot_id:
                block("BASE_CROSS_INDEX_VALUE_DRIFT", definition["id"], stage, "Regenerate the canonical model and cross-model index together.", run_id=source.run_id)
            indexed_value = {"slot_id": slot_id, "kind": "e1_operational_slot"}
        if canonical_sha256(indexed_value) != definition["value_sha256"]:
            block("BASE_CROSS_INDEX_VALUE_DRIFT", definition["id"], stage, "Regenerate the canonical model and cross-model index together.", run_id=source.run_id)
        records.setdefault(definition["id"], []).append({
            "id": definition["id"],
            "stage": stage,
            "kind": definition["kind"],
            "pointer": definition["json_pointer"],
            "value": indexed_value,
            "value_sha256": definition["value_sha256"],
            "path": source.source_paths[stage],
        })
    return records


def _control_record(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) != 2:
        return None
    by_kind = {item["kind"]: item for item in candidates}
    if set(by_kind) != {"major_events", "planned_event_registry"}:
        return None
    major = by_kind["major_events"]
    planned = by_kind["planned_event_registry"]
    if major["stage"] != "T1" or planned["stage"] != "T1":
        return None
    major_match = re.fullmatch(r"/major_events/([0-9]+)", major["pointer"])
    planned_match = re.fullmatch(
        r"/planned_event_registry/([0-9]+)", planned["pointer"]
    )
    if (
        major_match is None
        or planned_match is None
        or major_match.group(1) != planned_match.group(1)
    ):
        return None
    return major


def build_projection(source: AdmittedSource) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    authority = _authority_partition(source)
    author_records = _author_control_records(source)
    canonical_records = _canonical_records(source)
    handoff_sets: dict[str, set[str]] = {}
    for handoff_key in CLASS_MAP:
        values = source.handoff.get(handoff_key)
        if not isinstance(values, list) or len(values) != len(set(values)):
            block("BASE_HANDOFF_CONTROL_SET_INVALID", handoff_key, "P1", "Regenerate the formal development handoff.", run_id=source.run_id)
        handoff_sets[handoff_key] = set(values)
    primary_sets = (
        handoff_sets["mandatory_controls"],
        handoff_sets["development_freedoms"],
        handoff_sets["must_ask"],
    )
    if any(primary_sets[left] & primary_sets[right] for left in range(3) for right in range(left + 1, 3)):
        block("BASE_HANDOFF_PRIMARY_CLASSES_OVERLAP", "mandatory/freedom/must_ask", "P1", "Regenerate mutually exclusive decision-authority classes.", run_id=source.run_id)
    illegal_open = handoff_sets["open_items"] & (
        handoff_sets["mandatory_controls"] | handoff_sets["development_freedoms"]
    )
    if illegal_open:
        block("BASE_HANDOFF_OPEN_AUTHORITY_CONFLICT", ",".join(sorted(illegal_open)), "P1", "Keep open status only on open-only or must-ask controls.", run_id=source.run_id)
    classifications: dict[str, str] = {}
    for source_id in handoff_sets["mandatory_controls"]:
        classifications[source_id] = "mandatory"
    for source_id in handoff_sets["development_freedoms"]:
        classifications[source_id] = "freedom"
    for source_id in handoff_sets["must_ask"]:
        classifications[source_id] = "must_ask"
    for source_id in handoff_sets["open_items"] - handoff_sets["must_ask"]:
        classifications[source_id] = "open"
    bindings: list[dict[str, Any]] = []
    for source_id in sorted(classifications):
        authority_class = authority.get(source_id)
        if authority_class in {"author_locked", "author_open"}:
            record = author_records.get(source_id)
        else:
            candidates = canonical_records.get(source_id, [])
            record = _control_record(candidates)
        if authority_class is None or record is None:
            block("BASE_CONTROL_DEFINITION_UNRESOLVED", source_id, "P1", "Repair the authority partition and cross-model definition ownership.", run_id=source.run_id)
        if record.get("authority_class", authority_class) != authority_class:
            block("BASE_CONTROL_AUTHORITY_DRIFT", source_id, "P1", "Regenerate P1 authority and source indexes together.", run_id=source.run_id)
        classification = classifications[source_id]
        bindings.append({
            "source_id": source_id,
            "classification": classification,
            "open_item": source_id in handoff_sets["open_items"],
            "authority_class": authority_class,
            "domain": binding_domain(source_id, record["stage"]),
            "source": root_ref(record["path"], root=source.request_context.source_root, root_name="source"),
            "locator": record["pointer"],
            "source_text": source_text(record["value"]),
            "source_value_sha256": record["value_sha256"],
            "hld_instruction": hld_instruction(source_id, classification),
            "preserve_unresolved": source_id in handoff_sets["open_items"] or classification == "must_ask",
        })

    inventory: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    for source_id, candidates in canonical_records.items():
        if SOURCE_ID_RE.fullmatch(source_id) is None:
            continue
        for record in candidates:
            domain = STAGE_DOMAINS[record["stage"]]
            inventory[domain].append({
                "source_id": source_id,
                "source": root_ref(record["path"], root=source.request_context.source_root, root_name="source"),
                "locator": record["pointer"],
                "source_value_sha256": record["value_sha256"],
                "hld_use": f"Use the authoritative {record['kind']} definition {source_id} when constructing HLD.",
            })
    for source_id, record in author_records.items():
        if source_id.startswith(("INT-", "NAR-")):
            inventory["narrative"].append({
                "source_id": source_id,
                "source": root_ref(record["path"], root=source.request_context.source_root, root_name="source"),
                "locator": record["pointer"],
                "source_value_sha256": record["value_sha256"],
                "hld_use": f"Use the author-controlled narrative definition {source_id} when constructing HLD.",
            })
    for domain in DOMAINS:
        inventory[domain].sort(key=lambda item: (item["source_id"], item["locator"]))
        if not inventory[domain]:
            block("BASE_INVENTORY_DOMAIN_EMPTY", domain, "P1", f"Restore at least one authoritative HLD-relevant definition for {domain}.", run_id=source.run_id)
        keys = [(item["source_id"], item["locator"]) for item in inventory[domain]]
        if len(keys) != len(set(keys)):
            block("BASE_INVENTORY_DUPLICATE", domain, "P1", "Regenerate a unique cross-model index.", run_id=source.run_id)
    return bindings, inventory


def build_baseline(source: AdmittedSource) -> dict[str, Any]:
    request = source.request_context.request
    bindings, inventory = build_projection(source)
    return {
        "schema_version": "2.0",
        "skill": SKILL,
        "project_id": request["project_id"],
        "baseline_version": request["baseline_version"],
        "status": "ready",
        "source_release": {
            "name": "novel-conception-stage",
            "version": "1.0.0",
            "status": "frozen",
            "descriptor_sha256": sha256_file(source.request_context.release_descriptor),
            "contract_catalog_sha256": source.catalog.catalog_sha256(),
            "finalizer_sha256": sha256_file(source.request_context.finalizer_source),
        },
        "run_id": source.run_id,
        "lineage": source.lineage,
        "input_gate": {
            "formal_completion_valid": True,
            "released_finalizer_valid": True,
            "current_state_valid": True,
            "author_approved": True,
            "nine_stages_current": True,
            "p1_integrity_valid": True,
            "h1_integrity_valid": True,
            "q1_ready": True,
            "one_run_id": True,
            "hash_chain_valid": True,
        },
        "authority": {
            "design_authority": "P1",
            "human_review_role": "verification-only",
            "conflict_policy": "block-and-route-never-silent-merge",
        },
        "control_bindings": bindings,
        "design_inventory": inventory,
        "hld_assignment": {
            "next_stage": "novel-hld",
            "responsibilities": list(HLD_RESPONSIBILITIES),
            "required_capabilities": list(HLD_CAPABILITIES),
            "prohibitions": list(HLD_PROHIBITIONS),
            "unresolved_author_questions": sorted(source.handoff["must_ask"]),
        },
        "change_policy": {
            "local_hld_choice": "decide-only-within-development-freedom",
            "author_question": "block-affected-decision-and-return-to-author-gate",
            "conception_conflict": "return-to-earliest-authoritative-owner",
        },
        "semantic_review": {
            "review_mode": "deterministic-lossless-projection",
            "verdict": "pass",
            "binding_count": len(bindings),
            "inventory_counts": {domain: len(inventory[domain]) for domain in DOMAINS},
        },
    }


def render_markdown(baseline: Mapping[str, Any]) -> str:
    lines = [
        f"# Development Baseline — {baseline['project_id']}",
        "",
        f"- Baseline version: `{baseline['baseline_version']}`",
        f"- Conception run: `{baseline['run_id']}`",
        "- Authority: P1 canonical conception",
        "- Status: ready for HLD",
        "",
        "## HLD assignment",
        "",
    ]
    lines.extend(f"- {item}" for item in baseline["hld_assignment"]["responsibilities"])
    lines.extend(["", "## Control bindings", ""])
    for binding in baseline["control_bindings"]:
        lines.extend([
            f"### {binding['source_id']} — {binding['classification']}",
            "",
            f"- Authority: `{binding['authority_class']}`",
            f"- Domain: `{binding['domain']}`",
            f"- Source: `{binding['source']['root']}:{binding['source']['path']}#{binding['locator']}`",
            f"- HLD instruction: {binding['hld_instruction']}",
            "- Exact authoritative value:",
            "",
            "```text",
            binding["source_text"],
            "```",
            "",
        ])
    lines.extend(["## Six-domain design inventory", ""])
    for domain in DOMAINS:
        lines.append(f"### {domain}")
        lines.append("")
        for item in baseline["design_inventory"][domain]:
            lines.append(
                f"- `{item['source_id']}` — `{item['source']['root']}:{item['source']['path']}#{item['locator']}` — {item['hld_use']}"
            )
        lines.append("")
    lines.extend(["## Unresolved author questions", ""])
    questions = baseline["hld_assignment"]["unresolved_author_questions"]
    lines.extend(f"- `{item}`" for item in questions)
    if not questions:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def _validation_report(baseline_path: Path, markdown_path: Path, run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "skill": SKILL,
        "status": "pass",
        "run_id": run_id,
        "checks": list(READY_CHECKS),
        "errors": [],
        "artifacts": {
            "canonical": local_ref(baseline_path, root=baseline_path.parent),
            "human_projection": local_ref(markdown_path, root=markdown_path.parent),
        },
    }


def _manifest(output_dir: Path, baseline_version: str, run_id: str) -> dict[str, Any]:
    refs = {
        "canonical": local_ref(output_dir / "development-baseline.json", root=output_dir),
        "human_projection": local_ref(output_dir / "development-baseline.md", root=output_dir),
        "validation": local_ref(output_dir / "baseline-validation.json", root=output_dir),
    }
    return {
        "schema_version": "1.0",
        "skill": SKILL,
        "status": "ready",
        "run_id": run_id,
        "baseline_version": baseline_version,
        "files": [refs[key] for key in ("canonical", "human_projection", "validation")],
        "artifact_roles": refs,
    }


def write_ready_package(output_dir: Path, baseline: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    baseline_path = output_dir / "development-baseline.json"
    markdown_path = output_dir / "development-baseline.md"
    write_json(baseline_path, baseline)
    markdown_path.write_text(render_markdown(baseline), encoding="utf-8", newline="")
    validation = _validation_report(baseline_path, markdown_path, baseline["run_id"])
    validate_local(validation, "baseline-validation.schema.json")
    write_json(output_dir / "baseline-validation.json", validation)
    manifest = _manifest(output_dir, baseline["baseline_version"], baseline["run_id"])
    validate_local(manifest, "baseline-package-manifest.schema.json")
    write_json(output_dir / "package-manifest.json", manifest)


def validate_ready_package(output_dir: Path, source: AdmittedSource) -> dict[str, Any]:
    output = output_dir.resolve(strict=True)
    expected_files = {
        "development-baseline.json",
        "development-baseline.md",
        "baseline-validation.json",
        "package-manifest.json",
    }
    actual_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        raise RuntimeFailure(f"ready package boundary mismatch: {sorted(actual_files)}")
    baseline = read_json(output / "development-baseline.json", "BASE_OUTPUT_INVALID", SKILL)
    validate_local(baseline, "development-baseline.schema.json")
    expected_baseline = build_baseline(source)
    if baseline != expected_baseline:
        raise RuntimeFailure("development-baseline.json is not the deterministic source projection")
    markdown = (output / "development-baseline.md").read_text(encoding="utf-8")
    if markdown != render_markdown(expected_baseline):
        raise RuntimeFailure("development-baseline.md is not the deterministic JSON projection")
    validation = read_json(output / "baseline-validation.json", "BASE_OUTPUT_VALIDATION_INVALID", SKILL)
    validate_local(validation, "baseline-validation.schema.json")
    if validation != _validation_report(output / "development-baseline.json", output / "development-baseline.md", source.run_id):
        raise RuntimeFailure("baseline-validation.json drift")
    manifest = read_json(output / "package-manifest.json", "BASE_OUTPUT_MANIFEST_INVALID", SKILL)
    validate_local(manifest, "baseline-package-manifest.schema.json")
    if manifest != _manifest(output, expected_baseline["baseline_version"], source.run_id):
        raise RuntimeFailure("package-manifest.json drift")
    return validation


def validate_blocked_package(output_dir: Path) -> dict[str, Any]:
    output = output_dir.resolve(strict=True)
    files = sorted(path for path in output.rglob("*") if path.is_file())
    if [path.relative_to(output).as_posix() for path in files] != ["development-readiness-report.json"]:
        raise RuntimeFailure("blocked package must contain only development-readiness-report.json")
    report = read_json(files[0], "BASE_BLOCKED_REPORT_INVALID", SKILL)
    validate_local(report, "development-readiness-report.schema.json")
    return report


def _admit_and_build(context: RequestContext) -> tuple[AdmittedSource, dict[str, Any]]:
    """Run the complete source-readiness boundary used by prepare and revalidation."""
    source = admit_source(context)
    return source, build_baseline(source)


def validate_package(context: RequestContext) -> dict[str, Any]:
    """Validate either branch against the request and the source's current state."""
    readiness = context.output_dir / "development-readiness-report.json"
    if readiness.is_file():
        report = validate_blocked_package(context.output_dir)
        try:
            _admit_and_build(context)
        except ContractFailure as failure:
            expected = failure_report(context.request, failure)
            if report != expected:
                raise RuntimeFailure(
                    "blocked readiness report does not match the current source failure"
                )
            return {"status": "pass", "package_status": "blocked"}
        raise RuntimeFailure("blocked package is stale because source readiness now passes")
    source = admit_source(context)
    return validate_ready_package(context.output_dir, source)


def _publish(staging: Path, destination: Path, replace: bool) -> Path | None:
    backup: Path | None = None
    if destination.exists():
        if not replace:
            raise RuntimeFailure(f"output directory already exists: {destination}")
        backup = staging.parent / "previous-package"
        destination.replace(backup)
        try:
            staging.replace(destination)
        except Exception:
            backup.replace(destination)
            raise
        return backup
    staging.replace(destination)
    return None


def _rollback_publish(destination: Path, backup: Path | None) -> None:
    if destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists():
        destination.unlink()
    if backup is not None and backup.exists():
        backup.replace(destination)


def _discard_backup(backup: Path | None) -> None:
    if backup is None:
        return
    if backup.is_dir():
        shutil.rmtree(backup, ignore_errors=True)
    elif backup.exists():
        try:
            backup.unlink()
        except OSError:
            pass


def prepare(request_path: Path) -> tuple[int, dict[str, Any]]:
    context = load_request(request_path)
    destination = context.output_dir
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    staging = temporary / "package"
    try:
        try:
            source, baseline = _admit_and_build(context)
        except ContractFailure as failure:
            staging.mkdir()
            report = failure_report(context.request, failure)
            validate_local(report, "development-readiness-report.schema.json")
            write_json(staging / "development-readiness-report.json", report)
            validate_blocked_package(staging)
            backup = _publish(staging, destination, context.request["replace"])
            try:
                validate_package(context)
            except Exception:
                _rollback_publish(destination, backup)
                raise
            _discard_backup(backup)
            return 2, report
        validate_local(baseline, "development-baseline.schema.json")
        write_ready_package(staging, baseline)
        validation = validate_ready_package(staging, source)
        backup = _publish(staging, destination, context.request["replace"])
        try:
            validate_ready_package(destination, source)
        except Exception:
            _rollback_publish(destination, backup)
            raise
        _discard_backup(backup)
        return 0, validation
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
