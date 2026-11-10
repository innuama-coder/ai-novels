"""B0 completion gate and coordinator admission.

File presence is deliberately insufficient.  The baseline is revalidated
read-only, its manifest and stored validation are hash-checked, and only then
may the TASK-002 coordinator accept the exact B0 gate/completion pair.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .baseline import BaselineError, validate_baseline_package
from .canonical import (
    artifact_reference,
    canonical_json,
    canonical_sha256,
    sha256_file,
)
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import (
    AutonomousCoordinator,
    CoordinatorError,
    SealedDocument,
    StateTransition,
    seal_stage_document,
)


@dataclass(frozen=True)
class B0CompletionReceipt:
    """The accepted completion and immutable successor state."""

    completion: SealedDocument
    transition: StateTransition


def _logical_path(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        raise BaselineError("B0_COMPLETION_PATH_INVALID", value)
    return value


def complete_b0(
    package_root: str | Path,
    *,
    coordinator: AutonomousCoordinator,
    input_gate: SealedDocument,
    logical_package_path: str = "B0",
    next_state_path: str,
    runtime: ContractRuntime | None = None,
) -> B0CompletionReceipt:
    """Revalidate B0, persist completion, and advance run-state exactly once."""

    root = Path(package_root).resolve()
    contract_runtime = runtime or ContractRuntime()
    validation = validate_baseline_package(root, runtime=contract_runtime)
    baseline_path = root / "author-control-baseline.json"
    manifest_path = root / "package-manifest.json"
    validation_path = root / "validation.json"
    gate_path = root / "input-gate.json"
    if not all(path.is_file() for path in (baseline_path, manifest_path, validation_path, gate_path)):
        raise BaselineError(
            "B0_COMPLETION_ARTIFACT_MISSING",
            "baseline, manifest, validation, and input gate are all required",
        )
    if validation.get("verdict") != "ready":
        raise BaselineError("B0_COMPLETION_NOT_READY", "semantic validation is not ready")
    stored_gate_hash = sha256_file(gate_path)
    expected_gate_bytes = canonical_json(input_gate.data).encode("utf-8")
    if gate_path.read_bytes() != expected_gate_bytes:
        raise BaselineError(
            "B0_INPUT_GATE_TAMPERED",
            "stored input gate differs from supplied sealed gate",
        )
    if canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        raise BaselineError(
            "B0_INPUT_GATE_TAMPERED",
            "supplied gate reference does not bind its body",
        )
    baseline = __import__("json").loads(baseline_path.read_text(encoding="utf-8"))
    if baseline["run_id"] != coordinator.state["run_id"]:
        raise BaselineError("B0_RUN_ID_MISMATCH", "baseline belongs to another run")
    current_source_state = coordinator.state["source_interview_state"]
    source_state_matches = (
        baseline["run_state"] == current_source_state
        if baseline.get("source_kind") == "authority_revision"
        else baseline["run_state"]["sha256"] == current_source_state["sha256"]
    )
    if not source_state_matches:
        raise BaselineError(
            "B0_SOURCE_STATE_MISMATCH",
            "baseline does not bind the source interview state frozen by revision 0",
        )

    manifest_reference = {
        "path": _logical_path(logical_package_path, "package-manifest.json"),
        "sha256": sha256_file(manifest_path),
    }
    validation_reference = {
        "path": _logical_path(logical_package_path, "validation.json"),
        "sha256": sha256_file(validation_path),
    }
    gate_reference_path = input_gate.reference.get("path")
    if (
        not isinstance(gate_reference_path, str)
        or not gate_reference_path.endswith("/input-gate.json")
        or input_gate.reference.get("sha256") != stored_gate_hash
    ):
        raise BaselineError(
            "B0_INPUT_GATE_PATH_MISMATCH",
            "supplied gate is not a package-qualified immutable input gate",
        )
    completion_data: dict[str, Any] = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "B0",
        "status": "ready",
        "source_kind": baseline["source_kind"],
        "manifest": manifest_reference,
        "validation": validation_reference,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "previous_stage_completions": [],
        "return_binding": copy.deepcopy(input_gate.data["return_binding"]),
    }
    if baseline["source_kind"] == "authority_revision":
        completion_data["authority_revision"] = copy.deepcopy(
            baseline["authority_revision_finalization"]
        )
        completion_data["base_source_kind"] = baseline["base_source_kind"]
        for field in (
            "base_migration_finalization",
            "parent_b0_baseline",
            "parent_b0_completion",
            "parent_b0_manifest",
        ):
            if field in baseline:
                completion_data[field] = copy.deepcopy(baseline[field])
    try:
        contract_runtime.validate(completion_data, "stage-completion.schema.json")
    except ContractValidationError as error:
        raise BaselineError("B0_COMPLETION_SCHEMA_INVALID", str(error)) from error
    completion = seal_stage_document(
        completion_data,
        "B0",
        _logical_path(logical_package_path, "stage-completion.json"),
    )

    # Coordinator acceptance is the semantic run-state gate.  It occurs before
    # exposing a completion file, so rejection cannot leave a ready candidate.
    try:
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=completion,
            next_state_path=next_state_path,
        )
    except CoordinatorError as error:
        raise BaselineError("B0_COORDINATOR_REJECTED", str(error)) from error

    completion_path = root / "stage-completion.json"
    completion_path.write_text(
        canonical_json(completion.data), encoding="utf-8", newline=""
    )
    if artifact_reference(completion_path, root=root)["sha256"] != completion.reference["sha256"]:
        raise BaselineError(
            "B0_COMPLETION_WRITE_MISMATCH",
            "persisted completion does not match accepted completion",
        )
    return B0CompletionReceipt(completion=completion, transition=transition)


__all__ = ["B0CompletionReceipt", "complete_b0"]
