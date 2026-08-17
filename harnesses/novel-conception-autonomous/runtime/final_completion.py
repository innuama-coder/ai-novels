"""Publish the only development-admitting conception completion."""

from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from . import canonical as rt
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import SealedDocument, StateTransition, STAGE_ORDER, seal_document


class FinalCompletionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class FinalCompletionReceipt:
    package_root: Path
    completion: SealedDocument
    transition: StateTransition
    replayed: bool = False


def _fail(code: str, message: str) -> None:
    raise FinalCompletionError(code, message)


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


def _logical_h1_package_root(
    artifact_path: Any,
    *,
    package_kind: str,
    filename: str,
    code: str,
) -> str:
    if not isinstance(artifact_path, str) or "\\" in artifact_path:
        _fail(code, "logical H1 artifact path is not canonical POSIX")
    path = PurePosixPath(artifact_path)
    root = path.parent.as_posix()
    if (
        path.name != filename
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != artifact_path
        or re.fullmatch(
            rf"H1/{re.escape(package_kind)}(?:-attempt-0*[1-9][0-9]*)?",
            root,
        )
        is None
    ):
        _fail(code, "logical H1 artifact path is outside the accepted package root")
    return root


def _tree(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


def _sealed_stage_completion(
    stage: str,
    package: str | Path,
    *,
    runtime: ContractRuntime,
) -> tuple[Path, SealedDocument, dict[str, Any]]:
    root = Path(package).resolve()
    completion_path = root / "stage-completion.json"
    manifest_path = root / "package-manifest.json"
    validation_path = root / "validation.json"
    completion = _read(completion_path, "FINAL_STAGE_COMPLETION_INVALID")
    manifest = _read(manifest_path, "FINAL_STAGE_MANIFEST_INVALID")
    try:
        runtime.validate(completion, "stage-completion.schema.json")
        runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except (ContractValidationError, rt.ManifestIntegrityError) as error:
        _fail("FINAL_STAGE_PACKAGE_INVALID", f"{stage}: {error}")
    if (
        completion.get("stage") != stage
        or manifest.get("stage") != stage
        or completion["manifest"]["sha256"] != rt.sha256_file(manifest_path)
        or completion["validation"]["sha256"] != rt.sha256_file(validation_path)
    ):
        _fail("FINAL_STAGE_PACKAGE_INVALID", f"{stage} binding drift")
    reference = {
        "stage": stage,
        "path": completion["manifest"]["path"].rsplit("/", 1)[0]
        + "/stage-completion.json",
        "sha256": rt.sha256_file(completion_path),
    }
    return root, SealedDocument(data=completion, reference=reference), manifest


def _validate_inputs(
    *,
    run_state: SealedDocument,
    stage_packages: Mapping[str, str | Path],
    p1_package: str | Path,
    h1_package: str | Path,
    html_package: str | Path,
    author_decision: SealedDocument,
    development_handoff: str | Path,
    coordinator: Any,
    runtime: ContractRuntime,
) -> dict[str, Any]:
    try:
        runtime.validate(run_state.data, "autonomous-run-state.schema.json")
        runtime.validate(author_decision.data, "author-decision.schema.json")
    except ContractValidationError as error:
        _fail("FINAL_INPUT_SCHEMA_INVALID", str(error))
    coordinator_state = coordinator.state
    is_current_approved = (
        run_state.reference == coordinator.state_reference
        and run_state.data == coordinator_state
    )
    is_admitted_replay = (
        coordinator_state["status"] == "approved"
        and coordinator_state["development_status"] == "ready"
        and coordinator_state["previous_state"] == run_state.reference
        and coordinator_state["current_stage_completions"]
        == run_state.data["current_stage_completions"]
        and coordinator_state["author_decision"] == run_state.data["author_decision"]
    )
    if (
        not (is_current_approved or is_admitted_replay)
        or run_state.reference["sha256"] != rt.canonical_sha256(run_state.data)
    ):
        _fail("FINAL_STATE_NOT_CURRENT", "run-state is not current")
    if (
        run_state.data["status"] != "approved"
        or run_state.data["development_status"] != "not_ready"
        or run_state.data["active_return"] is not None
        or author_decision.data["decision"] != "approved"
        or author_decision.reference != run_state.data["author_decision"]
    ):
        _fail(
            "FINAL_APPROVAL_REQUIRED",
            "only the current external approved decision may admit development",
        )
    if set(stage_packages) != set(STAGE_ORDER):
        _fail("FINAL_STAGE_SET_INVALID", "exactly nine stage packages are required")

    roots: dict[str, Path] = {}
    completions: dict[str, SealedDocument] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for stage in STAGE_ORDER:
        roots[stage], completions[stage], manifests[stage] = (
            _sealed_stage_completion(
                stage, stage_packages[stage], runtime=runtime
            )
        )
        if (
            completions[stage].data["run_id"] != run_state.data["run_id"]
            or completions[stage].reference
            != run_state.data["current_stage_completions"][stage]
        ):
            _fail(
                "FINAL_STAGE_NOT_CURRENT",
                f"{stage} is not the current completion",
            )
    if Path(p1_package).resolve() != roots["P1"]:
        _fail("FINAL_P1_MISMATCH", "P1 package differs from stage package")
    if Path(h1_package).resolve() != roots["H1"]:
        _fail("FINAL_H1_MISMATCH", "H1 package differs from stage package")

    html_root = Path(html_package).resolve()
    html_manifest_path = html_root / "package-manifest.json"
    html_validation_path = html_root / "validation.json"
    html_manifest = _read(html_manifest_path, "FINAL_HTML_MANIFEST_INVALID")
    try:
        runtime.validate(html_manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(html_manifest, root=html_root)
    except (ContractValidationError, rt.ManifestIntegrityError) as error:
        _fail("FINAL_HTML_MANIFEST_INVALID", str(error))
    h1_execution = _read(
        roots["H1"] / "execution-record.json", "FINAL_H1_EXECUTION_INVALID"
    )
    html_reference = h1_execution.get("workspace_artifacts", {}).get(
        "html_manifest"
    )
    if not isinstance(html_reference, Mapping) or set(html_reference) != {
        "path",
        "sha256",
    }:
        _fail("FINAL_HTML_NOT_CURRENT", "H1 does not bind an exact HTML manifest")
    html_logical_root = _logical_h1_package_root(
        html_reference.get("path"),
        package_kind="html",
        filename="package-manifest.json",
        code="FINAL_HTML_NOT_CURRENT",
    )
    if (
        html_manifest.get("package_profile") != "h1-html"
        or html_manifest.get("run_id") != run_state.data["run_id"]
        or dict(html_reference)
        != {
            "path": f"{html_logical_root}/package-manifest.json",
            "sha256": rt.sha256_file(html_manifest_path),
        }
    ):
        _fail("FINAL_HTML_NOT_CURRENT", "HTML is not the H1-bound package")

    handoff_path = Path(development_handoff).resolve()
    if handoff_path != roots["P1"] / "development-handoff.json":
        _fail(
            "FINAL_HANDOFF_MISMATCH",
            "development handoff must be the current P1 artifact",
        )
    handoff = _read(handoff_path, "FINAL_HANDOFF_INVALID")
    try:
        runtime.validate(handoff, "development-handoff.schema.json")
    except ContractValidationError as error:
        _fail("FINAL_HANDOFF_INVALID", str(error))
    p1_role = manifests["P1"]["artifact_roles"]["development_handoff"]
    if p1_role != rt.artifact_reference(handoff_path, root=roots["P1"]):
        _fail("FINAL_HANDOFF_MISMATCH", "P1 manifest does not bind handoff")

    input_roots = {
        **{f"stage:{stage}": root for stage, root in roots.items()},
        "html": html_root,
    }
    return {
        "run_id": run_state.data["run_id"],
        "run_state": copy.deepcopy(run_state.reference),
        "stage_completions": {
            stage: copy.deepcopy(completions[stage].reference)
            for stage in STAGE_ORDER
        },
        "p1_manifest": {
            "path": "P1/package-manifest.json",
            "sha256": rt.sha256_file(roots["P1"] / "package-manifest.json"),
        },
        "p1_validation": {
            "path": "P1/validation.json",
            "sha256": rt.sha256_file(roots["P1"] / "validation.json"),
        },
        "h1_html_manifest": {
            "path": f"{html_logical_root}/package-manifest.json",
            "sha256": rt.sha256_file(html_manifest_path),
        },
        "h1_html_validation": {
            "path": f"{html_logical_root}/validation.json",
            "sha256": rt.sha256_file(html_validation_path),
        },
        "author_decision": copy.deepcopy(author_decision.reference),
        "development_handoff": {
            "path": "P1/development-handoff.json",
            "sha256": rt.sha256_file(handoff_path),
        },
        "input_roots": input_roots,
        "inventory": {key: _tree(root) for key, root in input_roots.items()},
    }


def _expected_validation(inputs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": inputs["run_id"],
        "verdict": "ready",
        "checks": [
            "approved-current-run-state",
            "nine-current-stage-completions",
            "current-p1-manifest-and-validation",
            "current-h1-html-manifest-and-validation",
            "current-author-decision-and-development-handoff",
        ],
        "p1_validation": copy.deepcopy(inputs["p1_validation"]),
        "h1_html_validation": copy.deepcopy(inputs["h1_html_validation"]),
    }


def validate_final_completion_package(
    package_root: str | Path,
    *,
    run_state: SealedDocument,
    stage_packages: Mapping[str, str | Path],
    p1_package: str | Path,
    h1_package: str | Path,
    html_package: str | Path,
    author_decision: SealedDocument,
    development_handoff: str | Path,
    coordinator: Any,
    logical_package_path: str = "completion",
    runtime: ContractRuntime | None = None,
) -> dict[str, Any]:
    contract_runtime = runtime or ContractRuntime()
    inputs = _validate_inputs(
        run_state=run_state,
        stage_packages=stage_packages,
        p1_package=p1_package,
        h1_package=h1_package,
        html_package=html_package,
        author_decision=author_decision,
        development_handoff=development_handoff,
        coordinator=coordinator,
        runtime=contract_runtime,
    )
    root = Path(package_root).resolve()
    allowed = {
        "conception-completion.json",
        "validation.json",
        "implementation/final_completion.py",
    }
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual != allowed:
        _fail("FINAL_PACKAGE_BOUNDARY_INVALID", f"unexpected files: {sorted(actual)}")
    validation = _read(root / "validation.json", "FINAL_VALIDATION_INVALID")
    if validation != _expected_validation(inputs):
        _fail("FINAL_VALIDATION_INVALID", "validation record drift")
    if (
        root / "implementation" / "final_completion.py"
    ).read_bytes() != Path(__file__).resolve().read_bytes():
        _fail("FINAL_IMPLEMENTATION_DRIFT", "implementation snapshot drift")
    completion = _read(
        root / "conception-completion.json", "FINAL_COMPLETION_INVALID"
    )
    try:
        contract_runtime.validate(
            completion, "conception-completion.schema.json"
        )
    except ContractValidationError as error:
        _fail("FINAL_COMPLETION_INVALID", str(error))
    expected = {
        "schema_version": "2.0",
        "run_id": inputs["run_id"],
        "status": "ready",
        "run_state": inputs["run_state"],
        "stage_completions": inputs["stage_completions"],
        "p1_manifest": inputs["p1_manifest"],
        "h1_html_manifest": inputs["h1_html_manifest"],
        "author_decision": inputs["author_decision"],
        "development_handoff": inputs["development_handoff"],
        "validation": {
            "path": f"{logical_package_path}/validation.json",
            "sha256": rt.sha256_file(root / "validation.json"),
        },
    }
    if completion != expected:
        _fail("FINAL_COMPLETION_INVALID", "completion binding drift")
    return validation


def publish_final_completion(
    package_root: str | Path,
    *,
    run_state: SealedDocument,
    stage_packages: Mapping[str, str | Path],
    p1_package: str | Path,
    h1_package: str | Path,
    html_package: str | Path,
    author_decision: SealedDocument,
    development_handoff: str | Path,
    coordinator: Any,
    next_state_path: str,
    active_return_request: SealedDocument | None = None,
    logical_package_path: str = "completion",
    runtime: ContractRuntime | None = None,
) -> FinalCompletionReceipt:
    if active_return_request is not None:
        _fail("FINAL_ACTIVE_RETURN", "active return forbids final completion")
    destination = Path(package_root).resolve()
    contract_runtime = runtime or ContractRuntime()
    inputs = _validate_inputs(
        run_state=run_state,
        stage_packages=stage_packages,
        p1_package=p1_package,
        h1_package=h1_package,
        html_package=html_package,
        author_decision=author_decision,
        development_handoff=development_handoff,
        coordinator=coordinator,
        runtime=contract_runtime,
    )
    if destination.exists():
        validate_final_completion_package(
            destination,
            run_state=run_state,
            stage_packages=stage_packages,
            p1_package=p1_package,
            h1_package=h1_package,
            html_package=html_package,
            author_decision=author_decision,
            development_handoff=development_handoff,
            coordinator=coordinator,
            logical_package_path=logical_package_path,
            runtime=contract_runtime,
        )
        completion_data = _read(
            destination / "conception-completion.json",
            "FINAL_COMPLETION_INVALID",
        )
        completion = seal_document(
            completion_data,
            f"{logical_package_path}/conception-completion.json",
        )
        transition = coordinator.accept_final_completion(
            completion=completion,
            next_state_path=next_state_path,
            active_return_request=None,
        )
        return FinalCompletionReceipt(
            destination, completion, transition, replayed=True
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temporary / "package"
    staging.mkdir()
    try:
        _write(staging / "validation.json", _expected_validation(inputs))
        completion_data = {
            "schema_version": "2.0",
            "run_id": inputs["run_id"],
            "status": "ready",
            "run_state": inputs["run_state"],
            "stage_completions": inputs["stage_completions"],
            "p1_manifest": inputs["p1_manifest"],
            "h1_html_manifest": inputs["h1_html_manifest"],
            "author_decision": inputs["author_decision"],
            "development_handoff": inputs["development_handoff"],
            "validation": {
                "path": f"{logical_package_path}/validation.json",
                "sha256": rt.sha256_file(staging / "validation.json"),
            },
        }
        contract_runtime.validate(
            completion_data, "conception-completion.schema.json"
        )
        _write(staging / "conception-completion.json", completion_data)
        target = staging / "implementation" / "final_completion.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).resolve(), target)
        validate_final_completion_package(
            staging,
            run_state=run_state,
            stage_packages=stage_packages,
            p1_package=p1_package,
            h1_package=h1_package,
            html_package=html_package,
            author_decision=author_decision,
            development_handoff=development_handoff,
            coordinator=coordinator,
            logical_package_path=logical_package_path,
            runtime=contract_runtime,
        )
        if inputs["inventory"] != {
            key: _tree(root) for key, root in inputs["input_roots"].items()
        }:
            _fail("FINAL_INPUT_MUTATED", "input changed before publish")
        staging.replace(destination)
        validate_final_completion_package(
            destination,
            run_state=run_state,
            stage_packages=stage_packages,
            p1_package=p1_package,
            h1_package=h1_package,
            html_package=html_package,
            author_decision=author_decision,
            development_handoff=development_handoff,
            coordinator=coordinator,
            logical_package_path=logical_package_path,
            runtime=contract_runtime,
        )
        completion = seal_document(
            completion_data,
            f"{logical_package_path}/conception-completion.json",
        )
        transition = coordinator.accept_final_completion(
            completion=completion,
            next_state_path=next_state_path,
            active_return_request=None,
        )
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    shutil.rmtree(temporary, ignore_errors=True)
    return FinalCompletionReceipt(
        package_root=destination,
        completion=completion,
        transition=transition,
        replayed=False,
    )


__all__ = [
    "FinalCompletionError",
    "FinalCompletionReceipt",
    "publish_final_completion",
    "validate_final_completion_package",
]
