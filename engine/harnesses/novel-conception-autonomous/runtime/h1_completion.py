"""Formal H1 stage completion publisher.

H1-A/B/C manifests are internal workspace artifacts.  This module is the only
runtime boundary that may turn the current rendered workspace into the single
top-level H1 stage completion.
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
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from . import canonical as rt
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import (
    AutonomousCoordinator,
    CoordinatorError,
    SealedDocument,
    StateTransition,
    seal_stage_document,
)


class H1CompletionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class H1CompletionReceipt:
    package_root: Path
    manifest: dict[str, Any]
    completion: SealedDocument
    transition: StateTransition
    replayed: bool


def _fail(code: str, message: str) -> None:
    raise H1CompletionError(code, message)


def _validated_h1_logical_package_path(value: str) -> str:
    """Accept the legacy H1 root or one immutable attempt-qualified root."""

    if (
        not isinstance(value, str)
        or "\\" in value
        or PurePosixPath(value).as_posix() != value
        or PurePosixPath(value).is_absolute()
        or ".." in PurePosixPath(value).parts
        or re.fullmatch(r"H1/stage(?:-attempt-0*[1-9][0-9]*)?", value) is None
    ):
        _fail(
            "H1_COMPLETION_PATH_INVALID",
            "formal H1 path must be H1/stage or H1/stage-attempt-N",
        )
    return value


def _read(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, str(error))
    if not isinstance(value, dict):
        _fail(code, f"{path} must contain a JSON object")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


def _inventory(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
        and path.relative_to(root).as_posix()
        not in {"package-manifest.json", "stage-completion.json"}
    ]


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


def _package_manifest(
    package: str | Path,
    *,
    runtime: ContractRuntime,
    profile: str,
    code: str,
) -> tuple[Path, dict[str, Any]]:
    root = Path(package).resolve()
    manifest = _read(root / "package-manifest.json", code)
    try:
        runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except (ContractValidationError, rt.ManifestIntegrityError) as error:
        _fail(code, str(error))
    if manifest.get("package_profile") != profile or manifest.get("verdict") != "ready":
        _fail(code, f"expected ready {profile} package")
    return root, manifest


def _h1_manifest_root_from_reference(
    reference: Mapping[str, Any],
    *,
    h1_root: Path,
    code: str,
) -> Path:
    """Resolve one sealed logical H1 manifest reference without discovery."""

    if set(reference) != {"path", "sha256"}:
        _fail(code, "manifest reference must contain only path and sha256")
    logical = reference.get("path")
    if not isinstance(logical, str) or "\\" in logical:
        _fail(code, "manifest reference path is not canonical POSIX")
    path = PurePosixPath(logical)
    if (
        path.is_absolute()
        or len(path.parts) < 3
        or path.parts[0] != "H1"
        or path.parts[-1] != "package-manifest.json"
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _fail(code, "manifest reference must be a contained H1 package path")
    candidate = h1_root.joinpath(*path.parts[1:-1]).resolve()
    try:
        candidate.relative_to(h1_root.resolve())
    except ValueError:
        _fail(code, "manifest reference escapes the H1 package root")
    return candidate


def _html_validator() -> Any:
    return importlib.import_module(
        "skills.novel-conception-review-html-generator.scripts.run_v2"
    )


def _assembled_workspace_from_rendered(
    *,
    rendered_workspace: SealedDocument,
    assembly_workspace_state: SealedDocument,
) -> SealedDocument:
    """Reconstruct the exact sealed assembled predecessor.

    H1-C advances the workspace deterministically and the public H1 completion
    API carries the rendered successor plus the fragments-ready predecessor.
    The intermediate assembled body is therefore fully determined: it has the
    rendered identity and bindings except for the H1-C manifest, and its parent
    is the supplied fragments-ready state.  The rendered successor supplies the
    predecessor hash; the owning H1-C validator then proves that the rebuilt
    canonical body matches that hash.
    """

    rendered = rendered_workspace.data
    artifacts = copy.deepcopy(rendered.get("artifacts", {}))
    if "html_manifest" not in artifacts:
        _fail(
            "H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
            "rendered workspace lacks html manifest",
        )
    artifacts.pop("html_manifest")
    data = {
        "schema_version": "2.0",
        "run_id": rendered["run_id"],
        "stage": "H1",
        "session_id": rendered["session_id"],
        "state": "assembled",
        "p1_completion": copy.deepcopy(rendered["p1_completion"]),
        "previous_state_sha256": assembly_workspace_state.reference["sha256"],
        "artifacts": artifacts,
    }
    sealed = SealedDocument(
        data=data,
        reference={
            "path": (
                f"H1/{rendered['session_id']}/workspace-assembled.json"
            ),
            "sha256": rendered["previous_state_sha256"],
        },
    )
    return sealed


def _validate_upstream(
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: SealedDocument,
    plan_workspace_state: SealedDocument,
    fragment_package: str | Path,
    fragment_workspace_state: SealedDocument,
    assembly_package: str | Path,
    assembly_workspace_state: SealedDocument,
    html_package: str | Path,
    rendered_workspace: SealedDocument,
    plan_active_return_request: SealedDocument | None,
    runtime: ContractRuntime,
) -> dict[str, Any]:
    roots: dict[str, Path] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for key, package, profile in (
        ("p1", p1_package, "conception-package"),
        ("plan", plan_package, "h1-plan"),
        ("fragment", fragment_package, "h1-fragments"),
        ("assembly", assembly_package, "h1-assembly"),
        ("html", html_package, "h1-html"),
    ):
        roots[key], manifests[key] = _package_manifest(
            package,
            runtime=runtime,
            profile=profile,
            code=f"H1_COMPLETION_{key.upper()}_INVALID",
        )
    try:
        runtime.validate(
            rendered_workspace.data, "h1-workspace-state.schema.json"
        )
    except ContractValidationError as error:
        _fail("H1_COMPLETION_WORKSPACE_INVALID", str(error))
    if (
        rendered_workspace.reference["sha256"]
        != rt.canonical_sha256(rendered_workspace.data)
        or rendered_workspace.data.get("state") != "rendered"
    ):
        _fail(
            "H1_COMPLETION_WORKSPACE_INVALID",
            "workspace must be the exact sealed rendered state",
        )
    run_id = rendered_workspace.data["run_id"]
    session_id = rendered_workspace.data["session_id"]
    if any(manifest["run_id"] != run_id for manifest in manifests.values()):
        _fail("H1_COMPLETION_RUN_MISMATCH", "upstream packages mix runs")
    if any(
        manifests[key].get("session_id") != session_id
        for key in ("plan", "fragment", "assembly", "html")
    ):
        _fail("H1_COMPLETION_SESSION_MISMATCH", "H1 packages mix sessions")
    workspace_artifacts = rendered_workspace.data["artifacts"]
    h1_root = roots["plan"].parent.resolve()
    logical_package_paths: dict[str, str] = {}
    flat_package_patterns = {
        "plan": r"H1/plan(?:-attempt-0*[1-9][0-9]*)?",
        "assembly": r"H1/assembly(?:-attempt-0*[1-9][0-9]*)?",
        "html": r"H1/html(?:-attempt-0*[1-9][0-9]*)?",
    }
    for key, field in (
        ("plan", "plan_manifest"),
        ("fragment", "fragment_manifest"),
        ("assembly", "assembly_manifest"),
        ("html", "html_manifest"),
    ):
        reference = workspace_artifacts[field]
        expected_root = _h1_manifest_root_from_reference(
            reference,
            h1_root=h1_root,
            code="H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
        )
        logical_root = PurePosixPath(reference["path"]).parent.as_posix()
        if key in flat_package_patterns and re.fullmatch(
            flat_package_patterns[key], logical_root
        ) is None:
            _fail(
                "H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
                f"rendered workspace {key} manifest path is not canonical",
            )
        if (
            roots[key] != expected_root
            or reference["sha256"]
            != rt.sha256_file(roots[key] / "package-manifest.json")
        ):
            _fail(
                "H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
                f"rendered workspace does not bind current {key} manifest",
            )
        logical_package_paths[key] = logical_root

    assembled_workspace = _assembled_workspace_from_rendered(
        rendered_workspace=rendered_workspace,
        assembly_workspace_state=assembly_workspace_state,
    )
    validator = _html_validator()
    validator.validate_html_package(
        roots["html"],
        p1_package=roots["p1"],
        plan_package=roots["plan"],
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=roots["fragment"],
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=roots["assembly"],
        assembly_workspace_state=assembly_workspace_state,
        workspace_state=assembled_workspace,
        plan_logical_package_path=logical_package_paths["plan"],
        fragment_logical_package_path=logical_package_paths["fragment"],
        assembly_logical_package_path=logical_package_paths["assembly"],
        plan_active_return_request=plan_active_return_request,
        runtime=runtime,
    )
    return {
        "roots": roots,
        "manifests": manifests,
        "run_id": run_id,
        "session_id": session_id,
        "workspace_artifacts": copy.deepcopy(workspace_artifacts),
        "inventory": {
            key: _tree_inventory(root) for key, root in roots.items()
        },
    }


def validate_h1_completion_package(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: SealedDocument,
    plan_workspace_state: SealedDocument,
    fragment_package: str | Path,
    fragment_workspace_state: SealedDocument,
    assembly_package: str | Path,
    assembly_workspace_state: SealedDocument,
    html_package: str | Path,
    rendered_workspace: SealedDocument,
    admission_input_gate: SealedDocument | None = None,
    plan_active_return_request: SealedDocument | None = None,
    human_readability_review: SealedDocument | None = None,
    logical_package_path: str = "H1/stage",
    runtime: ContractRuntime | None = None,
) -> dict[str, Any]:
    contract_runtime = runtime or ContractRuntime()
    logical_package_path = _validated_h1_logical_package_path(
        logical_package_path
    )
    admission_gate = admission_input_gate or plan_input_gate
    _require_h1_gate_rebinding(
        plan_input_gate=plan_input_gate,
        admission_input_gate=admission_gate,
    )
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        html_package=html_package,
        rendered_workspace=rendered_workspace,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    root = Path(package_root).resolve()
    manifest = _read(root / "package-manifest.json", "H1_COMPLETION_MANIFEST_INVALID")
    execution_value = _read(
        root / "execution-record.json", "H1_COMPLETION_EXECUTION_INVALID"
    )
    copied_review_path = root / "sources" / "human-readability-review.json"
    recorded_review = execution_value.get("human_readability_review")
    if human_readability_review is None and recorded_review is not None:
        if (
            not isinstance(recorded_review, Mapping)
            or set(recorded_review) != {"path", "sha256"}
            or not copied_review_path.is_file()
        ):
            _fail("H1_COMPLETION_READABILITY_REVIEW_DRIFT", "execution binding")
        copied_review = _read(
            copied_review_path, "H1_COMPLETION_READABILITY_REVIEW_DRIFT"
        )
        human_readability_review = SealedDocument(
            data=copied_review, reference=dict(recorded_review)
        )
    elif human_readability_review is not None and (
        recorded_review != human_readability_review.reference
        or not copied_review_path.is_file()
    ):
        _fail("H1_COMPLETION_READABILITY_REVIEW_DRIFT", "execution binding")
    elif recorded_review is None and copied_review_path.exists():
        _fail("H1_COMPLETION_READABILITY_REVIEW_DRIFT", "unbound review copy")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except (ContractValidationError, rt.ManifestIntegrityError) as error:
        _fail("H1_COMPLETION_MANIFEST_INVALID", str(error))
    files = _inventory(root)
    by_path = {item["path"]: item for item in files}
    expected_paths = {
        "sources/plan-package-manifest.json",
        "sources/fragment-package-manifest.json",
        "sources/assembly-package-manifest.json",
        "sources/html-package-manifest.json",
        "implementation/h1_completion.py",
        "execution-record.json",
        "validation.json",
    }
    if human_readability_review is not None:
        expected_paths.update({
            "sources/human-readability-review.json",
            "implementation/h1_readability.py",
        })
    role_paths = {
        "plan_manifest": "sources/plan-package-manifest.json",
        "fragment_manifest": "sources/fragment-package-manifest.json",
        "assembly_manifest": "sources/assembly-package-manifest.json",
        "html_manifest": "sources/html-package-manifest.json",
    }
    if (
        manifest.get("run_id") != upstream["run_id"]
        or manifest.get("stage") != "H1"
        or manifest.get("package_profile") != "h1-stage"
        or manifest.get("verdict") != "ready"
        or manifest.get("session_id") != upstream["session_id"]
        or manifest.get("parent_state_sha256")
        != rendered_workspace.reference["sha256"]
        or manifest.get("files") != files
        or manifest.get("artifact_roles")
        != {role: by_path[path] for role, path in role_paths.items()}
        or manifest.get("validation") != by_path.get("validation.json")
        or manifest.get("implementation")
        != [
            by_path[path]
            for path in (
                ["implementation/h1_completion.py"]
                + (
                    ["implementation/h1_readability.py"]
                    if human_readability_review is not None else []
                )
            )
        ]
        or set(by_path) != expected_paths
    ):
        _fail("H1_COMPLETION_MANIFEST_INVALID", "manifest is not exact")
    for key in ("plan", "fragment", "assembly", "html"):
        copied = root / role_paths[f"{key}_manifest"]
        if copied.read_bytes() != (
            upstream["roots"][key] / "package-manifest.json"
        ).read_bytes():
            _fail("H1_COMPLETION_SOURCE_DRIFT", f"{key} manifest snapshot drift")
    if (
        root / "implementation" / "h1_completion.py"
    ).read_bytes() != Path(__file__).resolve().read_bytes():
        _fail(
            "H1_COMPLETION_IMPLEMENTATION_DRIFT",
            "implementation snapshot drift",
        )
    if human_readability_review is not None:
        review_copy = root / "sources" / "human-readability-review.json"
        if (
            review_copy.read_text(encoding="utf-8")
            != rt.canonical_json(human_readability_review.data)
            or rt.sha256_file(review_copy)
            != human_readability_review.reference["sha256"]
        ):
            _fail("H1_COMPLETION_READABILITY_REVIEW_DRIFT", "review snapshot")
        from . import h1_readability

        if (
            root / "implementation" / "h1_readability.py"
        ).read_bytes() != Path(h1_readability.__file__).resolve().read_bytes():
            _fail(
                "H1_COMPLETION_IMPLEMENTATION_DRIFT",
                "readability implementation snapshot drift",
            )
    completion = _read(
        root / "stage-completion.json", "H1_COMPLETION_DOCUMENT_INVALID"
    )
    try:
        contract_runtime.validate(completion, "stage-completion.schema.json")
    except ContractValidationError as error:
        _fail("H1_COMPLETION_DOCUMENT_INVALID", str(error))
    validation = _read(root / "validation.json", "H1_COMPLETION_VALIDATION_INVALID")
    expected_validation = {
        "schema_version": "2.0",
        "run_id": upstream["run_id"],
        "stage": "H1",
        "verdict": "ready",
        "checks": [
            "formal-h1-c-revalidation",
            "same-run-session-lineage",
            "rendered-workspace-four-manifest-binding",
            "manifest-and-file-integrity",
            *(
                ["independent-human-readability-pass"]
                if human_readability_review is not None else []
            ),
        ],
    }
    if validation != expected_validation:
        _fail("H1_COMPLETION_VALIDATION_INVALID", "validation is not ready")
    expected_completion = {
        "schema_version": "2.0",
        "run_id": upstream["run_id"],
        "stage": "H1",
        "status": "ready",
        "manifest": {
            "path": f"{logical_package_path}/package-manifest.json",
            "sha256": rt.sha256_file(root / "package-manifest.json"),
        },
        "validation": {
            "path": f"{logical_package_path}/validation.json",
            "sha256": rt.sha256_file(root / "validation.json"),
        },
        "input_gate": copy.deepcopy(admission_gate.reference),
        "state_before": copy.deepcopy(admission_gate.data["run_state"]),
        "session_id": upstream["session_id"],
        "previous_stage_completions": [
            copy.deepcopy(rendered_workspace.data["p1_completion"])
        ],
        "return_binding": copy.deepcopy(admission_gate.data["return_binding"]),
    }
    if completion != expected_completion:
        _fail(
            "H1_COMPLETION_DOCUMENT_INVALID",
            "completion does not bind the formal H1 input chain",
        )
    expected_execution = {
        "schema_version": "2.0",
        "run_id": upstream["run_id"],
        "stage": "H1",
        "operation": "formal-h1-completion",
        "session_id": upstream["session_id"],
        "rendered_workspace": copy.deepcopy(rendered_workspace.reference),
        "workspace_artifacts": upstream["workspace_artifacts"],
        "input_gate": copy.deepcopy(admission_gate.reference),
        "plan_input_gate": copy.deepcopy(plan_input_gate.reference),
        "admission_input_gate": copy.deepcopy(admission_gate.reference),
        **(
            {"human_readability_review": copy.deepcopy(human_readability_review.reference)}
            if human_readability_review is not None else {}
        ),
    }
    if execution_value != expected_execution:
        _fail("H1_COMPLETION_EXECUTION_INVALID", "execution record drift")
    return validation


def _require_current_h1_gate(
    *,
    coordinator: Any,
    admission_input_gate: SealedDocument,
    active_return_request: SealedDocument | None,
) -> None:
    """Require the admission gate to be the exact current H1 gate."""

    try:
        expected = coordinator.build_input_gate(
            "H1",
            admission_input_gate.reference["path"],
            active_return_request=active_return_request,
        )
        if not isinstance(expected, SealedDocument):
            raise TypeError(
                "coordinator.build_input_gate did not return SealedDocument"
            )
    except CoordinatorError:
        raise
    except Exception as error:
        _fail(
            "H1_COMPLETION_GATE_INVALID",
            f"current coordinator gate: {error}",
        )
    if (
        expected.data != admission_input_gate.data
        or expected.reference != admission_input_gate.reference
    ):
        _fail(
            "H1_COMPLETION_GATE_INVALID",
            "admission input gate is not the exact current coordinator H1 gate",
        )


def _require_h1_gate_rebinding(
    *,
    plan_input_gate: SealedDocument,
    admission_input_gate: SealedDocument,
) -> None:
    """Bind current admission to the immutable topology sealed by H1-A.

    A local H1 return may advance run-state and add a return binding without
    rewriting the accepted plan.  Those admission fields may differ; run,
    target, baseline, and upstream package topology may not.
    """

    immutable_fields = (
        "schema_version",
        "run_id",
        "target_stage",
        "baseline_completion",
        "upstream_completions",
    )
    if any(
        plan_input_gate.data.get(field)
        != admission_input_gate.data.get(field)
        for field in immutable_fields
    ):
        _fail(
            "H1_COMPLETION_GATE_REBINDING_INVALID",
            "plan provenance and current admission gates differ in immutable topology",
        )
    if plan_input_gate.data.get("target_stage") != "H1":
        _fail(
            "H1_COMPLETION_GATE_REBINDING_INVALID",
            "plan provenance gate must target H1",
        )


def _is_exact_h1_successor(
    *,
    coordinator: Any,
    admission_input_gate: SealedDocument,
    completion: SealedDocument,
    rendered_workspace: SealedDocument,
    next_state_path: str,
) -> bool:
    """Recognize only the persisted H1 successor supported by replay."""

    if not isinstance(coordinator, AutonomousCoordinator):
        return False
    state = coordinator.state
    state_reference = coordinator.state_reference
    return (
        state.get("status") == "waiting_author"
        and state.get("previous_state")
        == admission_input_gate.data.get("run_state")
        and state.get("current_stage_completions", {}).get("H1")
        == completion.reference
        and state.get("h1_workspace") == rendered_workspace.reference
        and state_reference.get("path") == next_state_path
    )


def _require_unchanged_inputs(
    upstream: Mapping[str, Any],
) -> None:
    current = {
        key: _tree_inventory(root)
        for key, root in upstream["roots"].items()
    }
    if current != upstream["inventory"]:
        _fail(
            "H1_COMPLETION_INPUT_MUTATED",
            "input package inventory changed",
        )


def _require_unchanged_output(
    destination: Path,
    expected: list[dict[str, str]],
) -> None:
    if _tree_inventory(destination) != expected:
        _fail(
            "H1_COMPLETION_OUTPUT_MUTATED",
            "H1 package changed during validation",
        )


def _recover_existing_h1(
    destination: Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: SealedDocument,
    admission_input_gate: SealedDocument,
    plan_workspace_state: SealedDocument,
    fragment_package: str | Path,
    fragment_workspace_state: SealedDocument,
    assembly_package: str | Path,
    assembly_workspace_state: SealedDocument,
    html_package: str | Path,
    rendered_workspace: SealedDocument,
    coordinator: Any,
    next_state_path: str,
    plan_active_return_request: SealedDocument | None,
    active_return_request: SealedDocument | None,
    human_readability_review: SealedDocument | None,
    logical_package_path: str,
    runtime: ContractRuntime,
) -> H1CompletionReceipt:
    """Validate and replay an exact, already-published formal H1 package."""

    before = _tree_inventory(destination)
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        html_package=html_package,
        rendered_workspace=rendered_workspace,
        plan_active_return_request=plan_active_return_request,
        runtime=runtime,
    )
    validate_h1_completion_package(
        destination,
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        html_package=html_package,
        rendered_workspace=rendered_workspace,
        admission_input_gate=admission_input_gate,
        plan_active_return_request=plan_active_return_request,
        human_readability_review=human_readability_review,
        logical_package_path=logical_package_path,
        runtime=runtime,
    )
    completion_data = _read(
        destination / "stage-completion.json",
        "H1_COMPLETION_DOCUMENT_INVALID",
    )
    completion = seal_stage_document(
        completion_data,
        "H1",
        f"{logical_package_path}/stage-completion.json",
    )
    if completion.reference["sha256"] != rt.sha256_file(
        destination / "stage-completion.json"
    ):
        _fail(
            "H1_COMPLETION_DOCUMENT_INVALID",
            "existing completion is not the canonical sealed document",
        )
    if not _is_exact_h1_successor(
        coordinator=coordinator,
        admission_input_gate=admission_input_gate,
        completion=completion,
        rendered_workspace=rendered_workspace,
        next_state_path=next_state_path,
    ):
        _require_current_h1_gate(
            coordinator=coordinator,
            admission_input_gate=admission_input_gate,
            active_return_request=active_return_request,
        )
    manifest = _read(
        destination / "package-manifest.json",
        "H1_COMPLETION_MANIFEST_INVALID",
    )
    _require_unchanged_output(destination, before)
    _require_unchanged_inputs(upstream)
    _require_unchanged_output(destination, before)
    transition = coordinator.accept_stage_completion(
        gate=admission_input_gate,
        completion=completion,
        next_state_path=next_state_path,
        active_return_request=active_return_request,
        h1_workspace=rendered_workspace.reference,
    )
    return H1CompletionReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        completion=completion,
        transition=transition,
        replayed=True,
    )


def publish_h1_completion(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: SealedDocument,
    plan_workspace_state: SealedDocument,
    fragment_package: str | Path,
    fragment_workspace_state: SealedDocument,
    assembly_package: str | Path,
    assembly_workspace_state: SealedDocument,
    html_package: str | Path,
    rendered_workspace: SealedDocument,
    coordinator: Any,
    next_state_path: str,
    logical_package_path: str = "H1/stage",
    admission_input_gate: SealedDocument | None = None,
    plan_active_return_request: SealedDocument | None = None,
    active_return_request: SealedDocument | None = None,
    human_readability_review: SealedDocument | None = None,
    runtime: ContractRuntime | None = None,
) -> H1CompletionReceipt:
    destination = Path(package_root).resolve()
    contract_runtime = runtime or ContractRuntime()
    admission_gate = admission_input_gate or plan_input_gate
    logical_package_path = _validated_h1_logical_package_path(
        logical_package_path
    )
    _require_h1_gate_rebinding(
        plan_input_gate=plan_input_gate,
        admission_input_gate=admission_gate,
    )
    recovery_arguments = {
        "p1_package": p1_package,
        "plan_package": plan_package,
        "plan_input_gate": plan_input_gate,
        "admission_input_gate": admission_gate,
        "plan_workspace_state": plan_workspace_state,
        "fragment_package": fragment_package,
        "fragment_workspace_state": fragment_workspace_state,
        "assembly_package": assembly_package,
        "assembly_workspace_state": assembly_workspace_state,
        "html_package": html_package,
        "rendered_workspace": rendered_workspace,
        "coordinator": coordinator,
        "next_state_path": next_state_path,
        "plan_active_return_request": plan_active_return_request,
        "active_return_request": active_return_request,
        "human_readability_review": human_readability_review,
        "logical_package_path": logical_package_path,
        "runtime": contract_runtime,
    }
    if destination.exists():
        return _recover_existing_h1(destination, **recovery_arguments)
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        html_package=html_package,
        rendered_workspace=rendered_workspace,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    _require_current_h1_gate(
        coordinator=coordinator,
        admission_input_gate=admission_gate,
        active_return_request=active_return_request,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temporary / "package"
    staging.mkdir()
    try:
        for key in ("plan", "fragment", "assembly", "html"):
            target = staging / "sources" / f"{key}-package-manifest.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                upstream["roots"][key] / "package-manifest.json", target
            )
        if human_readability_review is not None:
            _write(
                staging / "sources" / "human-readability-review.json",
                human_readability_review.data,
            )
        implementation_target = staging / "implementation" / "h1_completion.py"
        implementation_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).resolve(), implementation_target)
        if human_readability_review is not None:
            from . import h1_readability

            shutil.copyfile(
                Path(h1_readability.__file__).resolve(),
                staging / "implementation" / "h1_readability.py",
            )
        execution = {
            "schema_version": "2.0",
            "run_id": upstream["run_id"],
            "stage": "H1",
            "operation": "formal-h1-completion",
            "session_id": upstream["session_id"],
            "rendered_workspace": copy.deepcopy(rendered_workspace.reference),
            "workspace_artifacts": upstream["workspace_artifacts"],
            "input_gate": copy.deepcopy(admission_gate.reference),
            "plan_input_gate": copy.deepcopy(plan_input_gate.reference),
            "admission_input_gate": copy.deepcopy(admission_gate.reference),
            **(
                {"human_readability_review": copy.deepcopy(human_readability_review.reference)}
                if human_readability_review is not None else {}
            ),
        }
        _write(staging / "execution-record.json", execution)
        validation = {
            "schema_version": "2.0",
            "run_id": upstream["run_id"],
            "stage": "H1",
            "verdict": "ready",
            "checks": [
                "formal-h1-c-revalidation",
                "same-run-session-lineage",
                "rendered-workspace-four-manifest-binding",
                "manifest-and-file-integrity",
                *(
                    ["independent-human-readability-pass"]
                    if human_readability_review is not None else []
                ),
            ],
        }
        _write(staging / "validation.json", validation)
        files = _inventory(staging)
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": upstream["run_id"],
            "stage": "H1",
            "package_profile": "h1-stage",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "plan_manifest": by_path["sources/plan-package-manifest.json"],
                "fragment_manifest": by_path[
                    "sources/fragment-package-manifest.json"
                ],
                "assembly_manifest": by_path[
                    "sources/assembly-package-manifest.json"
                ],
                "html_manifest": by_path["sources/html-package-manifest.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": [
                by_path[path]
                for path in (
                    ["implementation/h1_completion.py"]
                    + (
                        ["implementation/h1_readability.py"]
                        if human_readability_review is not None else []
                    )
                )
            ],
            "parent_state_sha256": rendered_workspace.reference["sha256"],
            "session_id": upstream["session_id"],
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        completion_data = {
            "schema_version": "2.0",
            "run_id": upstream["run_id"],
            "stage": "H1",
            "status": "ready",
            "manifest": {
                "path": f"{logical_package_path}/package-manifest.json",
                "sha256": rt.sha256_file(staging / "package-manifest.json"),
            },
            "validation": {
                "path": f"{logical_package_path}/validation.json",
                "sha256": rt.sha256_file(staging / "validation.json"),
            },
            "input_gate": copy.deepcopy(admission_gate.reference),
            "state_before": copy.deepcopy(admission_gate.data["run_state"]),
            "session_id": upstream["session_id"],
            "previous_stage_completions": [
                copy.deepcopy(rendered_workspace.data["p1_completion"])
            ],
            "return_binding": copy.deepcopy(admission_gate.data["return_binding"]),
        }
        completion = seal_stage_document(
            completion_data,
            "H1",
            f"{logical_package_path}/stage-completion.json",
        )
        _write(staging / "stage-completion.json", completion.data)
        validate_h1_completion_package(
            staging,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_package,
            fragment_workspace_state=fragment_workspace_state,
            assembly_package=assembly_package,
            assembly_workspace_state=assembly_workspace_state,
            html_package=html_package,
            rendered_workspace=rendered_workspace,
            admission_input_gate=admission_gate,
            plan_active_return_request=plan_active_return_request,
            human_readability_review=human_readability_review,
            logical_package_path=logical_package_path,
            runtime=contract_runtime,
        )
        _require_unchanged_inputs(upstream)
        try:
            staging.replace(destination)
        except OSError:
            if destination.exists():
                shutil.rmtree(temporary, ignore_errors=True)
                return _recover_existing_h1(
                    destination,
                    **recovery_arguments,
                )
            raise
        published_inventory = _tree_inventory(destination)
        validate_h1_completion_package(
            destination,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_package,
            fragment_workspace_state=fragment_workspace_state,
            assembly_package=assembly_package,
            assembly_workspace_state=assembly_workspace_state,
            html_package=html_package,
            rendered_workspace=rendered_workspace,
            admission_input_gate=admission_gate,
            plan_active_return_request=plan_active_return_request,
            human_readability_review=human_readability_review,
            logical_package_path=logical_package_path,
            runtime=contract_runtime,
        )
        _require_unchanged_output(destination, published_inventory)
        _require_unchanged_inputs(upstream)
        _require_unchanged_output(destination, published_inventory)
        transition = coordinator.accept_stage_completion(
            gate=admission_gate,
            completion=completion,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
            h1_workspace=rendered_workspace.reference,
        )
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    shutil.rmtree(temporary, ignore_errors=True)
    return H1CompletionReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        completion=completion,
        transition=transition,
        replayed=False,
    )


__all__ = [
    "H1CompletionError",
    "H1CompletionReceipt",
    "publish_h1_completion",
    "validate_h1_completion_package",
]
