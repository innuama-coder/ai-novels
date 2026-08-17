"""Production transaction guard for the complete conception chain.

Domain Agents still own semantic payloads and the existing stage runners keep
their contracts.  This module owns only durable ordering: it persists every
coordinator snapshot and H1 workspace, binds one current work order, and splits
H1/author/final into recoverable transactions.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

from .author_decision import AuthorDecisionReceipt, record_author_decision
from .canonical import canonical_sha256, sha256_file
from .contracts import ContractRuntime
from .coordinator import (
    AutonomousCoordinator,
    CoordinatorError,
    H1WorkspaceTransition,
    SealedDocument,
    StateTransition,
)
from .return_routing import STAGE_ORDER, route_return
from .final_completion import FinalCompletionReceipt, publish_final_completion
from .h1_completion import H1CompletionReceipt, publish_h1_completion
from .h1_readability import (
    H1ReadabilityError,
    prepublish_contract as h1_readability_prepublish_contract,
    validate_review as validate_h1_readability_review,
)
from .production_store import ProductionRunStore, ProductionStoreError
from .production_coordinator import ProductionCoordinator


class ProductionOrchestratorError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


ACTION_CONTRACT: dict[str, tuple[str | None, str]] = {
    "B0": ("B0", "baseline-controller"),
    "S1": ("S1", "novel-storyline-architecture-designer"),
    "W1": ("W1", "novel-world-model-designer"),
    "E1": ("E1", "novel-environment-system-designer"),
    "T1": ("T1", "novel-event-timeline-designer"),
    "C1": ("C1", "novel-character-system-designer"),
    # The Q1 owner internally coordinates its mandatory controller, semantic,
    # and isolated handoff contexts; only the final Q1 completion advances the
    # production chain.
    "Q1": ("Q1", "novel-conception-reviewer"),
    "P1": ("P1", "novel-conception-deliverable-assembler"),
    "H1-A-plan": ("H1", "novel-conception-human-review-assembler"),
    "H1-B": ("H1", "novel-conception-fragment-writer"),
    "H1-A-assemble": ("H1", "novel-conception-human-review-assembler"),
    "H1-C": ("H1", "novel-conception-review-html-generator"),
    "H1-publish": ("H1", "production-orchestrator"),
    "author-decision": (None, "external-author-forwarder"),
    "final": (None, "production-orchestrator"),
}

PACKAGE_INPUT_FIELDS = {
    "B0": "baseline_package",
    "S1": "storyline_package",
    "W1": "world_package",
    "E1": "environment_package",
    "T1": "event_package",
    "C1": "character_package",
    "Q1": "review_package",
}
ACTION_PACKAGE_INPUT_STAGES = {
    "B0": (),
    "S1": ("B0",),
    "W1": ("B0", "S1"),
    "E1": ("B0", "S1", "W1"),
    "T1": ("B0", "S1", "W1", "E1"),
    "C1": ("B0", "S1", "W1", "E1", "T1"),
    "Q1": ("B0", "S1", "W1", "E1", "T1", "C1"),
    "P1": ("B0", "S1", "W1", "E1", "T1", "C1", "Q1"),
}
H1_ACTION_STATES = {
    "H1-A-plan": ("initialized", "planned"),
    "H1-B": ("planned", "fragments_ready"),
    "H1-A-assemble": ("fragments_ready", "assembled"),
    "H1-C": ("assembled", "rendered"),
    "H1-publish": ("rendered", None),
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_STAGE_IDENTITY_SOURCES = {
    "E1": {
        "runtime": ("skill/run_v2.py", "skills/novel-environment-system-designer/scripts/run_v2.py"),
        "schema": ("schemas/environment-system.schema.json", "docs/ai-novel-workflow/contracts/autonomous-v2/environment-system.schema.json"),
        "protocol": ("skill/runtime-contract.md", "skills/novel-environment-system-designer/references/runtime-contract.md"),
        "validator_module": "skills.novel-environment-system-designer.scripts.run_v2",
        "validator_name": "validate_e1_package",
    },
    "T1": {
        "runtime": ("skill/run_v2.py", "skills/novel-event-timeline-designer/scripts/run_v2.py"),
        "schema": ("schemas/event-timeline.schema.json", "docs/ai-novel-workflow/contracts/autonomous-v2/event-timeline.schema.json"),
        "protocol": ("skill/runtime-contract.md", "skills/novel-event-timeline-designer/references/runtime-contract.md"),
        "validator_module": "skills.novel-event-timeline-designer.scripts.run_v2",
        "validator_name": "validate_t1_package",
    },
}


def _current_identity_bindings(stage: str) -> dict[str, dict[str, str]]:
    source = _STAGE_IDENTITY_SOURCES[stage]
    return {
        kind: {
            "identity": source[kind][0],
            "sha256": sha256_file(_REPO_ROOT / source[kind][1]),
        }
        for kind in ("runtime", "schema", "protocol")
    }


CURRENT_CONCEPTION_PRODUCTION_CONTRACT = {
    "schema_version": "1.0",
    "E1": {
        "model_schema_version": "2.4",
        "semantic_review_protocols": [
            "e1-authority-capability-semantics-v1",
            "e1-transition-support-semantics-v1",
        ],
        "identity_bindings": _current_identity_bindings("E1"),
    },
    "T1": {
        "model_schema_version": "2.4",
        "semantic_review_protocols": ["t1-initial-event-plan-semantics-v4"],
        "identity_bindings": _current_identity_bindings("T1"),
    },
}
CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256 = canonical_sha256(
    CURRENT_CONCEPTION_PRODUCTION_CONTRACT
)


@dataclass(frozen=True)
class ProductionContext:
    store: ProductionRunStore
    coordinator: AutonomousCoordinator
    state: SealedDocument
    active_return: SealedDocument | None


def _sealed(transition: StateTransition) -> SealedDocument:
    return SealedDocument(
        data=copy.deepcopy(transition.snapshot),
        reference=copy.deepcopy(transition.reference),
    )


def _require_context_current(
    context: ProductionContext, latest: SealedDocument
) -> None:
    if latest.reference != context.state.reference:
        raise ProductionOrchestratorError(
            "PROD_CONTEXT_STALE", "resume the production run before advancing"
        )


def _require_work_actor(work_order: SealedDocument, actor: str) -> None:
    action = work_order.data.get("action")
    contract = ACTION_CONTRACT.get(str(action))
    required = work_order.data.get("required_actor")
    if (
        contract is None
        or not isinstance(actor, str)
        or not actor
        or required != contract[1]
        or actor != required
    ):
        raise ProductionOrchestratorError(
            "PROD_WORK_ACTOR_MISMATCH",
            f"{action} requires {required}",
        )


def _gate_completion_references(gate: SealedDocument) -> dict[str, Mapping[str, str]]:
    references: dict[str, Mapping[str, str]] = {}
    baseline = gate.data.get("baseline_completion")
    if isinstance(baseline, Mapping):
        references["B0"] = baseline
    upstream = gate.data.get("upstream_completions")
    if not isinstance(upstream, list):
        raise ProductionOrchestratorError("PROD_WORK_INPUT_GATE_INVALID", "upstreams")
    for reference in upstream:
        if not isinstance(reference, Mapping) or not isinstance(reference.get("stage"), str):
            raise ProductionOrchestratorError("PROD_WORK_INPUT_GATE_INVALID", "completion")
        stage = str(reference["stage"])
        if stage in references:
            raise ProductionOrchestratorError("PROD_WORK_INPUT_GATE_INVALID", stage)
        references[stage] = reference
    return references


def _authoritative_package_inputs(
    context: ProductionContext,
    *,
    action: str,
    gate: SealedDocument | None,
) -> dict[str, str]:
    stages = ACTION_PACKAGE_INPUT_STAGES.get(action, ())
    if not stages:
        return {}
    if gate is None:
        raise ProductionOrchestratorError("PROD_WORK_INPUT_GATE_INVALID", action)
    references = _gate_completion_references(gate)
    expected_current = context.state.data.get("current_stage_completions", {})
    output: dict[str, str] = {}
    for stage in stages:
        reference = references.get(stage)
        if not isinstance(reference, Mapping) or expected_current.get(stage) != reference:
            raise ProductionOrchestratorError("PROD_WORK_INPUT_NOT_CURRENT", stage)
        try:
            root = context.store.resolve_completion_package_root(
                reference, expected_stage=stage
            )
        except ProductionStoreError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        output[PACKAGE_INPUT_FIELDS[stage]] = str(root)
    return output


def _internal_h1_fragment_inputs(
    context: ProductionContext, *, planned_workspace: SealedDocument
) -> dict[str, str]:
    """Resolve the two sealed package roots admitted by a returned H1-B order."""

    p1_reference = context.state.data.get("current_stage_completions", {}).get("P1")
    if not isinstance(p1_reference, Mapping):
        raise ProductionOrchestratorError("PROD_H1_P1_MISMATCH", "missing P1")
    if planned_workspace.data.get("p1_completion") != p1_reference:
        raise ProductionOrchestratorError("PROD_H1_P1_MISMATCH", "planned workspace")
    try:
        p1_root = context.store.resolve_completion_package_root(
            p1_reference, expected_stage="P1"
        )
        plan_reference = planned_workspace.data.get("artifacts", {}).get(
            "plan_manifest"
        )
        if not isinstance(plan_reference, Mapping):
            raise ProductionStoreError("PROD_H1_WORKSPACE_MISSING", "plan manifest")
        context.store.load_document(plan_reference)
        plan_root = context.store.resolve_document_path(plan_reference).parent
    except ProductionStoreError as error:
        raise ProductionOrchestratorError(error.code, str(error)) from error
    return {"p1_package": str(p1_root), "plan_package": str(plan_root)}


def _validate_internal_h1_fidelity_failure(
    context: ProductionContext,
    failure: SealedDocument,
    *,
    workspace: SealedDocument,
) -> None:
    required = {
        "schema_version", "kind", "run_id", "h1_session_id", "review_id",
        "reviewer", "fragment_manifest", "findings", "verdict", "status",
    }
    reviewer = failure.data.get("reviewer")
    findings = failure.data.get("findings")
    if (
        set(failure.data) != required
        or failure.data.get("schema_version") != "1.0"
        or failure.data.get("kind") != "internal-h1-fragment-fidelity-failure"
        or failure.data.get("run_id") != context.state.data.get("run_id")
        or failure.data.get("h1_session_id") != workspace.data.get("session_id")
        or not isinstance(failure.data.get("review_id"), str)
        or not failure.data["review_id"].strip()
        or not isinstance(reviewer, Mapping)
        or set(reviewer) != {"task_id", "thread_id", "independence_basis"}
        or not all(
            isinstance(reviewer.get(field), str) and reviewer[field].strip()
            for field in ("task_id", "thread_id")
        )
        or reviewer.get("independence_basis")
        != "separate-task-no-producer-context"
        or failure.data.get("fragment_manifest")
        != workspace.data.get("artifacts", {}).get("fragment_manifest")
        or not isinstance(findings, list)
        or not findings
        or any(
            not isinstance(item, Mapping)
            or set(item) != {
                "id", "fragment_id", "projection_id", "source_anchor_id",
                "source_value_sha256", "evidence_quote", "problem",
            }
            or not all(isinstance(value, str) and value.strip() for value in item.values())
            or re.fullmatch(r"[a-f0-9]{64}", item["source_value_sha256"]) is None
            for item in findings
        )
        or failure.data.get("verdict") != "fail"
        or failure.data.get("status") != "sealed"
        or failure.reference.get("path")
        != (
            "reviews/h1-fragment-fidelity/"
            f"{failure.data.get('review_id', '')}.json"
        )
        or canonical_sha256(failure.data) != failure.reference.get("sha256")
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_FIDELITY_FAILURE_INVALID",
            str(failure.data.get("review_id", "")),
        )
    try:
        persisted = context.store.load_document(failure.reference)
    except ProductionStoreError as error:
        raise ProductionOrchestratorError(error.code, str(error)) from error
    if persisted.data != failure.data:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_FIDELITY_FAILURE_INVALID", failure.data["review_id"]
        )


_H1_FRAGMENT_ARTIFACT_ROLES = {
    "fragment_package",
    "fragments",
    "generation_session",
    "session_workspace_completion",
    "generation_evidence_index",
    "execution_record",
}


def _resolve_internal_h1_fragment_sibling(
    store: ProductionRunStore,
    *,
    package_root: Path,
    logical_package_root: PurePosixPath,
    reference: Any,
) -> tuple[Path, dict[str, str]]:
    """Resolve one fragment artifact only beneath its sealed manifest root."""

    if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", str(reference)
        )
    logical = reference.get("path")
    digest = reference.get("sha256")
    if (
        not isinstance(logical, str)
        or not logical
        or "\\" in logical
        or not isinstance(digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", str(reference)
        )
    pure = PurePosixPath(logical)
    if pure.is_absolute() or pure.as_posix() != logical or ".." in pure.parts:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", logical
        )
    if pure.parts[: len(logical_package_root.parts)] == logical_package_root.parts:
        relative = PurePosixPath(*pure.parts[len(logical_package_root.parts) :])
    elif pure.parts and pure.parts[0] == logical_package_root.parts[0]:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"parent mismatch: {logical}"
        )
    else:
        relative = pure
    if not relative.parts:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", logical
        )
    candidate = package_root / Path(*relative.parts)
    try:
        resolved = store.resolve_physical_path(candidate)
        resolved.relative_to(store._without_windows_extended_prefix(package_root))
    except (ProductionStoreError, ValueError) as error:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", logical
        ) from error
    if (
        not store.physical_is_file(resolved)
        or store.physical_sha256(resolved) != digest
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"stale: {logical}"
        )
    return resolved, {
        "path": (logical_package_root / relative).as_posix(),
        "sha256": digest,
    }


def _load_internal_h1_fragment_json(
    store: ProductionRunStore,
    *,
    package_root: Path,
    logical_package_root: PurePosixPath,
    reference: Any,
) -> SealedDocument:
    path, normalized = _resolve_internal_h1_fragment_sibling(
        store,
        package_root=package_root,
        logical_package_root=logical_package_root,
        reference=reference,
    )
    try:
        data = json.loads(store.physical_read_text(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", str(path)
        ) from error
    if not isinstance(data, dict) or canonical_sha256(data) != normalized["sha256"]:
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"noncanonical: {normalized['path']}"
        )
    return SealedDocument(data=data, reference=normalized)


def _validate_internal_h1_fragment_package(
    context: ProductionContext,
    *,
    manifest: SealedDocument,
    workspace: SealedDocument,
    planned_workspace: SealedDocument,
) -> dict[str, SealedDocument]:
    """Validate every fragment manifest reference from one sibling package."""

    try:
        manifest_path = context.store.resolve_document_path(manifest.reference)
    except ProductionStoreError as error:
        raise ProductionOrchestratorError(error.code, str(error)) from error
    logical_root = PurePosixPath(manifest.reference.get("path", "")).parent
    package_root = manifest_path.parent
    roles = manifest.data.get("artifact_roles")
    files = manifest.data.get("files")
    implementation = manifest.data.get("implementation")
    validation = manifest.data.get("validation")
    if (
        canonical_sha256(manifest.data) != manifest.reference.get("sha256")
        or manifest.data.get("schema_version") != "2.0"
        or manifest.data.get("run_id") != context.state.data.get("run_id")
        or manifest.data.get("stage") != "H1"
        or manifest.data.get("package_profile") != "h1-fragments"
        or manifest.data.get("verdict") != "ready"
        or manifest.data.get("session_id") != workspace.data.get("session_id")
        or manifest.data.get("parent_state_sha256")
        != planned_workspace.reference.get("sha256")
        or not isinstance(roles, Mapping)
        or set(roles) != _H1_FRAGMENT_ARTIFACT_ROLES
        or not isinstance(files, list)
        or not files
        or not isinstance(implementation, list)
        or not isinstance(validation, Mapping)
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", "manifest envelope"
        )

    normalized_files: dict[tuple[str, str], Path] = {}
    raw_file_refs: set[tuple[str, str]] = set()
    for reference in files:
        path, normalized = _resolve_internal_h1_fragment_sibling(
            context.store,
            package_root=package_root,
            logical_package_root=logical_root,
            reference=reference,
        )
        key = (normalized["path"], normalized["sha256"])
        raw_key = (str(reference.get("path", "")), str(reference.get("sha256", "")))
        if key in normalized_files or raw_key in raw_file_refs:
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_PACKAGE_INVALID", "duplicate file reference"
            )
        raw_file_refs.add(raw_key)
        normalized_files[key] = path

    def require_listed(reference: Any) -> dict[str, str]:
        _path, normalized = _resolve_internal_h1_fragment_sibling(
            context.store,
            package_root=package_root,
            logical_package_root=logical_root,
            reference=reference,
        )
        key = (normalized["path"], normalized["sha256"])
        if key not in normalized_files:
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"unlisted: {normalized['path']}"
            )
        return normalized

    role_documents: dict[str, SealedDocument] = {}
    for role, reference in roles.items():
        normalized = require_listed(reference)
        if role == "fragments":
            if not normalized["path"].endswith(".md"):
                raise ProductionOrchestratorError(
                    "PROD_H1_FRAGMENT_PACKAGE_INVALID", "fragments media type"
                )
        else:
            if not normalized["path"].endswith(".json"):
                raise ProductionOrchestratorError(
                    "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"role media type: {role}"
                )
            role_documents[role] = _load_internal_h1_fragment_json(
                context.store,
                package_root=package_root,
                logical_package_root=logical_root,
                reference=reference,
            )
    normalized_validation = require_listed(validation)
    if not normalized_validation["path"].endswith(".json"):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", "validation media type"
        )
    _load_internal_h1_fragment_json(
        context.store,
        package_root=package_root,
        logical_package_root=logical_root,
        reference=validation,
    )
    for reference in implementation:
        require_listed(reference)

    fragment_package = role_documents["fragment_package"]
    package_p1 = fragment_package.data.get("p1_completion")
    planned_p1 = planned_workspace.data.get("p1_completion")
    if (
        not isinstance(package_p1, Mapping)
        or set(package_p1) != {"path", "sha256"}
        or not isinstance(planned_p1, Mapping)
        or set(planned_p1) != {"stage", "path", "sha256"}
        or planned_p1.get("stage") != "P1"
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", "P1 binding shape"
        )
    for label, reference in (("package P1", package_p1), ("planned P1", planned_p1)):
        logical = reference.get("path")
        digest = reference.get("sha256")
        if (
            not isinstance(logical, str)
            or not logical
            or "\\" in logical
            or PurePosixPath(logical).is_absolute()
            or PurePosixPath(logical).as_posix() != logical
            or ".." in PurePosixPath(logical).parts
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_PACKAGE_INVALID", f"{label} reference"
            )
    normalized_planned_p1 = {
        "path": planned_p1["path"],
        "sha256": planned_p1["sha256"],
    }
    if (
        fragment_package.data.get("run_id") != context.state.data.get("run_id")
        or fragment_package.data.get("h1_session_id")
        != workspace.data.get("session_id")
        or dict(package_p1) != normalized_planned_p1
        or fragment_package.data.get("plan_manifest")
        != planned_workspace.data.get("artifacts", {}).get("plan_manifest")
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_FRAGMENT_PACKAGE_INVALID", "fragment package bindings"
        )
    return role_documents


def _sealed_executor_inputs(work_order: SealedDocument) -> dict[str, Any]:
    inputs = copy.deepcopy(dict(work_order.data.get("inputs", {})))
    inputs.pop("_contract_qualification", None)
    return inputs


def _completion_model_schema_version(
    store: ProductionRunStore, completion_reference: Mapping[str, str]
) -> str:
    return _completion_contract_identity(store, completion_reference)[
        "model_schema_version"
    ]


def _completion_contract_identity(
    store: ProductionRunStore, completion_reference: Mapping[str, str]
) -> dict[str, Any]:
    completion = store.load_document(completion_reference)
    completion_path = store.resolve_document_path(completion_reference)
    package_root = completion_path.parent
    logical_package_root = PurePosixPath(completion.reference["path"]).parent
    stage = completion.data.get("stage")
    if stage not in {"E1", "T1"} or completion.data.get("status") != "ready":
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_STAGE_INVALID", str(completion_reference)
        )
    manifest_reference = completion.data.get("manifest")
    if not isinstance(manifest_reference, Mapping):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_MANIFEST_MISSING", str(completion_reference)
        )
    manifest = store.load_document(manifest_reference)
    if store.resolve_document_path(manifest_reference).parent != package_root:
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_CHAIN_INVALID", stage
        )
    validation_reference = completion.data.get("validation")
    if not isinstance(validation_reference, Mapping):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_VALIDATION_MISSING", str(completion_reference)
        )
    validation = store.load_document(validation_reference)
    if store.resolve_document_path(validation_reference).parent != package_root:
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_CHAIN_INVALID", stage
        )
    if validation.data.get("verdict", validation.data.get("status")) != "ready":
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_VALIDATION_INVALID", str(completion_reference)
        )
    canonical_reference = manifest.data.get("artifact_roles", {}).get("canonical")
    if not isinstance(canonical_reference, Mapping):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_CANONICAL_MISSING", str(completion_reference)
        )
    canonical = _load_package_json_document(
        store, package_root, logical_package_root, canonical_reference
    )
    version = canonical.data.get("schema_version")
    if not isinstance(version, str):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_SCHEMA_VERSION_MISSING", str(completion_reference)
        )
    artifact_roles = manifest.data.get("artifact_roles", {})
    execution_reference = artifact_roles.get("execution_record")
    session_reference = artifact_roles.get("generation_session")
    if not isinstance(execution_reference, Mapping) or not isinstance(
        session_reference, Mapping
    ):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_ARTIFACT_MISSING", str(completion_reference)
        )
    execution = _load_package_json_document(
        store, package_root, logical_package_root, execution_reference
    )
    session = _load_package_json_document(
        store, package_root, logical_package_root, session_reference
    )
    catalog = execution.data.get("implementation_catalog")
    if not isinstance(catalog, list):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IMPLEMENTATION_CATALOG_INVALID", stage
        )
    implementation: dict[str, dict[str, str]] = {}
    for item in catalog:
        if not isinstance(item, Mapping) or not isinstance(item.get("artifact"), Mapping):
            raise ProductionOrchestratorError(
                "PROD_COMPLETION_IMPLEMENTATION_CATALOG_INVALID", stage
            )
        identity = item.get("identity")
        if not isinstance(identity, str) or identity in implementation:
            raise ProductionOrchestratorError(
                "PROD_COMPLETION_IMPLEMENTATION_CATALOG_INVALID", stage
            )
        artifact_reference = dict(item["artifact"])
        try:
            artifact_path, normalized_reference = _resolve_package_artifact(
                store, package_root, logical_package_root, artifact_reference
            )
        except (OSError, ValueError) as error:
            raise ProductionOrchestratorError(
                "PROD_COMPLETION_IMPLEMENTATION_ARTIFACT_INVALID",
                f"{identity}: {error}",
            ) from error
        implementation[identity] = normalized_reference
    expected = CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]
    observed_bindings: dict[str, dict[str, str]] = {}
    for kind, expected_binding in expected["identity_bindings"].items():
        observed = implementation.get(expected_binding["identity"])
        observed_bindings[kind] = {
            "identity": expected_binding["identity"],
            "artifact": observed,
        }
    if stage == "E1":
        observed_protocols = [
            session.data.get("authority_review_protocol"),
            session.data.get("hosting_review_protocol"),
        ]
    else:
        observed_protocols = [session.data.get("plan_review_protocol")]
    if (
        manifest.data.get("stage") != stage
        or manifest.data.get("verdict") != "ready"
        or _normalize_package_reference(
            store,
            package_root,
            logical_package_root,
            manifest.data.get("validation"),
        )
        != validation.reference
        or completion.data.get("manifest") != manifest.reference
        or completion.data.get("validation") != validation.reference
        or canonical.data.get("stage") != stage
    ):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_CHAIN_INVALID", stage
        )
    _validate_stage_public_package(stage, package_root)
    contract_profile = {
        "stage": stage,
        "model_schema_version": version,
        "identity_bindings": {
            kind: {
                "identity": value["identity"],
                "sha256": (
                    value["artifact"].get("sha256")
                    if isinstance(value["artifact"], Mapping)
                    else None
                ),
            }
            for kind, value in observed_bindings.items()
        },
        "semantic_review_protocols": observed_protocols,
    }
    return {
        "stage": stage,
        "completion": dict(completion.reference),
        "manifest": dict(manifest.reference),
        "validation": dict(validation.reference),
        "canonical": dict(canonical.reference),
        "model_schema_version": version,
        "identity_bindings": observed_bindings,
        "semantic_review_protocols": observed_protocols,
        "contract_profile_sha256": canonical_sha256(contract_profile),
        "canonical_identity_sha256": canonical_sha256(
            {
                "completion": completion.reference,
                "manifest": manifest.reference,
                "validation": validation.reference,
                "canonical": canonical.reference,
                "contract_profile": contract_profile,
            }
        ),
    }


def _resolve_package_artifact(
    store: ProductionRunStore,
    package_root: Path,
    logical_package_root: PurePosixPath,
    reference: Mapping[str, Any],
) -> tuple[Path, dict[str, str]]:
    logical = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(logical, str) or not isinstance(digest, str):
        raise ValueError("artifact reference malformed")
    pure = PurePosixPath(logical)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("artifact path escapes package")
    if pure.parts[: len(logical_package_root.parts)] == logical_package_root.parts:
        relative = PurePosixPath(*pure.parts[len(logical_package_root.parts) :])
        normalized_logical = pure
    else:
        relative = pure
        normalized_logical = logical_package_root / pure
    candidates = [package_root / Path(*relative.parts), store._path(logical)]
    extant = []
    for candidate in candidates:
        try:
            resolved = store.resolve_physical_path(candidate)
        except ProductionStoreError as error:
            raise ValueError("artifact path escapes run root") from error
        if store.physical_exists(resolved) and resolved not in extant:
            extant.append(resolved)
    if len(extant) > 1:
        raise ValueError(f"artifact root ambiguous: {logical}")
    if (
        len(extant) == 1
        and store.physical_is_file(extant[0])
        and store.physical_sha256(extant[0]) == digest
    ):
        return extant[0], {
            "path": normalized_logical.as_posix(),
            "sha256": digest,
        }
    raise ValueError(f"artifact missing or stale: {logical}")


def _load_package_json_document(
    store: ProductionRunStore,
    package_root: Path,
    logical_package_root: PurePosixPath,
    reference: Mapping[str, Any],
) -> SealedDocument:
    try:
        path, normalized = _resolve_package_artifact(
            store, package_root, logical_package_root, reference
        )
    except (OSError, ValueError) as error:
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_ARTIFACT_INVALID", str(reference)
        ) from error
    try:
        data = json.loads(store.physical_read_text(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_ARTIFACT_INVALID", str(path)
        ) from error
    if not isinstance(data, dict):
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_IDENTITY_ARTIFACT_INVALID", str(path)
        )
    return SealedDocument(data=data, reference=normalized)


def _normalize_package_reference(
    store: ProductionRunStore,
    package_root: Path,
    logical_package_root: PurePosixPath,
    reference: Any,
) -> dict[str, str] | None:
    if not isinstance(reference, Mapping):
        return None
    try:
        _path, normalized = _resolve_package_artifact(
            store, package_root, logical_package_root, reference
        )
    except (OSError, ValueError):
        return None
    return normalized


def _validate_stage_public_package(stage: str, package_root: Path) -> None:
    source = _STAGE_IDENTITY_SOURCES[stage]
    module = importlib.import_module(source["validator_module"])
    validator = getattr(module, source["validator_name"])
    validator_root = package_root
    if os.name == "nt" and not str(package_root).startswith("\\\\?\\"):
        validator_root = Path("\\\\?\\" + str(package_root.resolve()))
    try:
        validator(validator_root)
    except Exception as error:
        raise ProductionOrchestratorError(
            "PROD_COMPLETION_PUBLIC_REPLAY_FAILED", f"{stage}: {error}"
        ) from error


def _identity_matches_current_profile(stage: str, identity: Mapping[str, Any]) -> bool:
    expected = CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]
    expected_profile = {
        "stage": stage,
        "model_schema_version": expected["model_schema_version"],
        "identity_bindings": expected["identity_bindings"],
        "semantic_review_protocols": expected["semantic_review_protocols"],
    }
    return identity.get("contract_profile_sha256") == canonical_sha256(
        expected_profile
    )


def _contract_upgrade_owner_target(
    qualification: SealedDocument,
) -> tuple[str, dict[str, Any]]:
    """Classify a digest drift from the sealed owner-level contract diff.

    Schema versions alone cannot identify the owner of implementation or
    protocol changes.  The qualification's complete production contract is
    the immutable predecessor basis; any change outside a known owner is not
    safely routable and therefore fails closed.
    """

    qualified_contract = qualification.data.get("production_contract")
    current_contract = CURRENT_CONCEPTION_PRODUCTION_CONTRACT
    owner_stages = tuple(
        stage for stage in STAGE_ORDER if stage in {"E1", "T1"}
    )
    if not isinstance(qualified_contract, Mapping) or not isinstance(
        current_contract, Mapping
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID", "production_contract"
        )
    qualified_digest = qualification.data.get("new_contract_digest")
    if (
        canonical_sha256(qualified_contract) != qualified_digest
        or canonical_sha256(current_contract)
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID",
            "qualified production contract digest",
        )
    if any(
        not isinstance(qualified_contract.get(stage), Mapping)
        or not isinstance(current_contract.get(stage), Mapping)
        for stage in owner_stages
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID", "owner contract"
        )
    versions = qualification.data.get("production_versions")
    if not isinstance(versions, Mapping) or any(
        qualified_contract[stage].get("model_schema_version")
        != versions.get(stage)
        for stage in owner_stages
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID", "owner schema versions"
        )
    qualified_non_owner = {
        key: value
        for key, value in qualified_contract.items()
        if key not in owner_stages
    }
    current_non_owner = {
        key: value
        for key, value in current_contract.items()
        if key not in owner_stages
    }
    if canonical_sha256(qualified_non_owner) != canonical_sha256(
        current_non_owner
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID", "non-owner contract diff"
        )
    changed_owners = [
        stage
        for stage in owner_stages
        if canonical_sha256(qualified_contract[stage])
        != canonical_sha256(current_contract[stage])
    ]
    if not changed_owners:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_INVALID", "unclassified digest drift"
        )
    target = changed_owners[0]
    return target, {
        "stage": target,
        "qualification": dict(qualification.reference),
        "qualified_contract_digest": qualified_digest,
        "current_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        "changed_owner_stages": changed_owners,
        "qualified_owner_sha256": canonical_sha256(
            qualified_contract[target]
        ),
        "current_owner_sha256": canonical_sha256(current_contract[target]),
    }


def _actual_contract_upgrade_target(
    store: ProductionRunStore,
    latest: SealedDocument,
    qualification: SealedDocument | None,
) -> tuple[str, dict[str, Any]]:
    expected_versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    identities: dict[str, Any] = {}
    for stage in ("E1", "T1"):
        reference = latest.data["current_stage_completions"].get(stage)
        if not isinstance(reference, Mapping):
            continue
        try:
            identity = _completion_contract_identity(store, reference)
        except (ProductionOrchestratorError, ProductionStoreError) as error:
            return stage, {
                "stage": stage,
                "completion": dict(reference),
                "identity_error": error.code,
            }
        identities[stage] = identity
        if not _identity_matches_current_profile(stage, identity):
            return stage, identity
    if qualification is None:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_BASIS_MISSING", "E1/T1"
        )
    versions = qualification.data.get("production_versions", {})
    for stage in ("E1", "T1"):
        if versions.get(stage) != expected_versions[stage]:
            return stage, identities.get(stage, {"stage": stage})
    if (
        qualification.data.get("new_contract_digest")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
    ):
        active_reference = latest.data.get("active_return")
        qualified_return = qualification.data.get("return_request")
        if (
            isinstance(active_reference, Mapping)
            and qualified_return == active_reference
        ):
            active = store.load_document(active_reference)
            active_target = active.data.get("target_stage")
            if active_target in {"E1", "T1"}:
                return active_target, {
                    "stage": active_target,
                    "active_return": dict(active_reference),
                    "qualification": dict(qualification.reference),
                    "qualified_contract_digest": qualification.data.get(
                        "new_contract_digest"
                    ),
                    "qualified_production_versions": copy.deepcopy(
                        qualification.data.get("production_versions")
                    ),
                    "qualified_production_contract": copy.deepcopy(
                        qualification.data.get("production_contract")
                    ),
                }
        return _contract_upgrade_owner_target(qualification)
    raise ProductionOrchestratorError(
        "PROD_CONTRACT_UPGRADE_NOT_REQUIRED", "current qualification"
    )


def _validate_current_contract_qualification(
    store: ProductionRunStore, qualification: SealedDocument | None, *, scope: str
) -> SealedDocument:
    expected_versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    if qualification is None:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_STALE", scope
        )
    store.trusted_contract_upgrade_markers()
    if (
        qualification.data.get("new_contract_digest")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
        or qualification.data.get("production_versions") != expected_versions
        or qualification.data.get("status") != "complete"
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_STALE", scope
        )
    for field in (
        "session_invalidation_receipts",
        "work_order_invalidation_receipts",
        "completion_invalidation_receipts",
        "commit_intent_abandonment_receipts",
    ):
        receipts = qualification.data.get(field, [])
        if not isinstance(receipts, list):
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_QUALIFICATION_STALE", f"{scope}:{field}"
            )
        for reference in receipts:
            store.load_document(reference)
    transition_mode = qualification.data.get("transition_mode")
    if transition_mode is not None:
        production_contract = qualification.data.get("production_contract")
        generation = qualification.data.get("refresh_generation")
        prior_reference = qualification.data.get("prior_qualification")
        if (
            transition_mode not in {
                "new_return",
                "active_return_refresh",
                "active_return_escalation",
                "active_stage_return_refresh",
                "stage_return",
                "internal_h1_fragment_return",
                "internal_h1_readability_return",
                "internal_h1_html_readability_return",
            }
            or canonical_sha256(production_contract)
            != qualification.data.get("new_contract_digest")
            or not isinstance(generation, int)
            or generation < 0
            or (transition_mode == "new_return" and generation != 0)
            or (
                transition_mode == "active_return_refresh"
                and (generation < 1 or not isinstance(prior_reference, Mapping))
            )
            or (
                transition_mode == "active_return_escalation"
                and (
                    generation < 1
                    or not isinstance(prior_reference, Mapping)
                    or not isinstance(
                        qualification.data.get("superseded_return"), Mapping
                    )
                )
            )
            or (
                transition_mode == "active_stage_return_refresh"
                and (
                    generation < 1
                    or not isinstance(prior_reference, Mapping)
                    or not isinstance(
                        qualification.data.get("superseded_return"), Mapping
                    )
                )
            )
            or (
                transition_mode == "stage_return"
                and (
                    generation < 1
                    or not isinstance(prior_reference, Mapping)
                    or qualification.data.get("superseded_return") is not None
                )
            )
            or (
                transition_mode in {
                    "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                }
                and (
                    generation < 1
                    or not isinstance(prior_reference, Mapping)
                    or qualification.data.get("superseded_return") is not None
                    or qualification.data.get("target_stage") != "H1"
                    or qualification.data.get("stale_identity", {}).get(
                        "resume_point"
                    )
                    != (
                        "H1-B"
                        if transition_mode == "internal_h1_fragment_return"
                        else "H1-A-plan"
                    )
                )
            )
            or (
                transition_mode == "internal_h1_html_readability_return"
                and (
                    generation < 1
                    or not isinstance(prior_reference, Mapping)
                    or not isinstance(
                        qualification.data.get("superseded_return"), Mapping
                    )
                    or qualification.data.get("target_stage") != "H1"
                    or qualification.data.get("stale_identity", {}).get(
                        "resume_point"
                    )
                    != "H1-C"
                )
            )
        ):
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_QUALIFICATION_STALE", f"{scope}:refresh-chain"
            )
        if isinstance(prior_reference, Mapping):
            prior = store.load_document(prior_reference)
            prior_generation = prior.data.get("refresh_generation", 0)
            if (
                prior.data.get("new_contract_digest")
                != qualification.data.get("old_contract_digest")
                or (
                    transition_mode in {
                        "active_return_refresh",
                        "active_return_escalation",
                        "active_stage_return_refresh",
                        "stage_return",
                        "internal_h1_fragment_return",
                        "internal_h1_readability_return",
                        "internal_h1_html_readability_return",
                    }
                    and (
                        not isinstance(prior_generation, int)
                        or generation != prior_generation + 1
                    )
                )
            ):
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_QUALIFICATION_STALE",
                    f"{scope}:refresh-predecessor",
                )
    latest = store.latest_state()
    for stage in ("E1", "T1"):
        reference = latest.data["current_stage_completions"].get(stage)
        if not isinstance(reference, Mapping):
            continue
        identity = _completion_contract_identity(store, reference)
        if not _identity_matches_current_profile(stage, identity):
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_QUALIFICATION_STALE", f"{scope}:{stage}"
            )
    return qualification


def _validate_prepared_contract_upgrade(
    *,
    store: ProductionRunStore,
    plan: SealedDocument,
    receipt: SealedDocument,
    predecessor: SealedDocument,
    successor: SealedDocument,
    request: SealedDocument,
    qualification: SealedDocument,
) -> None:
    """Bind a recovered prepared transaction to the current production identity."""

    production_versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    if (
        plan.data.get("transition_mode") == "active_stage_return_refresh"
        and plan.data.get("target_stage") == "H1"
    ):
        stale = plan.data.get("stale_identity", {})
        post = [
            SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        initialized_reference = stale.get("initialized_workspace")
        workspaces = [
            item for item in post if item.reference == initialized_reference
        ]
        gates = [
            item for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        try:
            old_workspace = store.load_document(stale["current_workspace"])
            failure = store.load_document(stale["implementation_failure"])
            plan_manifest = store.load_document(stale["plan_manifest"])
            fragment_manifest = store.load_document(stale["fragment_manifest"])
        except (KeyError, TypeError, ProductionStoreError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        expected_inputs = plan.data.get("post_upgrade_inputs")
        prior_generation = qualification.data.get("refresh_generation", 0)
        if (
            predecessor.data.get("status") != "revise"
            or predecessor.data.get("author_decision") is not None
            or predecessor.data.get("active_return")
            != plan.data.get("superseded_return")
            or successor.data.get("active_return") != request.reference
            or request.data.get("origin_stage") != "H1"
            or request.data.get("calculated_owner") != "H1-A"
            or request.data.get("resume_point") != "H1-A-plan"
            or request.data.get("invalidated_h1_artifacts")
            != ["plan", "fragments", "assembly", "html", "completion"]
            or request.data.get("evidence_ids")
            != [failure.data.get("failure_id")]
            or old_workspace.data.get("state") != "fragments_ready"
            or old_workspace.data.get("artifacts")
            != {
                "plan_manifest": plan_manifest.reference,
                "fragment_manifest": fragment_manifest.reference,
            }
            or initialized_reference is None
            or len(workspaces) != 1
            or workspaces[0].data.get("state") != "initialized"
            or workspaces[0].data.get("p1_completion")
            != successor.data.get("current_stage_completions", {}).get("P1")
            or workspaces[0].data.get("previous_state_sha256") is not None
            or workspaces[0].data.get("artifacts") != {}
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or len(post) != 3
            or len(gates) != 1
            or len(orders) != 1
            or not isinstance(expected_inputs, Mapping)
            or orders[0].data.get("action") != "H1-A-plan"
            or orders[0].data.get("h1_workspace") != initialized_reference
            or orders[0].data.get("inputs") != expected_inputs
            or expected_inputs.get("p1_package")
            != str(
                store.resolve_completion_package_root(
                    successor.data["current_stage_completions"]["P1"],
                    expected_stage="P1",
                )
            )
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        return
    if plan.data.get("transition_mode") == "internal_h1_readability_return":
        stale = plan.data.get("stale_identity", {})
        post = [
            SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        initialized_reference = stale.get("initialized_workspace")
        workspaces = [
            item for item in post if item.reference == initialized_reference
        ]
        if len(workspaces) != 1:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        initialized = workspaces[0]
        try:
            old_workspace = store.load_document(stale["current_workspace"])
            failure = store.load_document(stale["readability_failure"])
            completion = store.load_document(stale["h1_completion"])
            h1_manifest = store.load_document(stale["h1_manifest"])
        except (KeyError, TypeError, ProductionStoreError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        gates = [
            item for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        expected_inputs = plan.data.get("post_upgrade_inputs")
        prior_generation = qualification.data.get("refresh_generation", 0)
        if (
            predecessor.data.get("status") != "waiting_author"
            or predecessor.data.get("author_decision") is not None
            or predecessor.data.get("active_return") is not None
            or predecessor.data.get("current_stage_completions", {}).get("H1")
            != completion.reference
            or old_workspace.data.get("state") != "rendered"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("calculated_owner") != "H1-A"
            or request.data.get("resume_point") != "H1-A-plan"
            or request.data.get("invalidated_h1_artifacts")
            != ["plan", "fragments", "assembly", "html", "completion"]
            or request.data.get("evidence_ids") != [failure.data.get("review_id")]
            or completion.data.get("manifest") != h1_manifest.reference
            or successor.data.get("active_return") != request.reference
            or "H1" in successor.data.get("current_stage_completions", {})
            or initialized.data.get("state") != "initialized"
            or initialized.data.get("p1_completion")
            != successor.data.get("current_stage_completions", {}).get("P1")
            or initialized.data.get("previous_state_sha256") is not None
            or initialized.data.get("artifacts") != {}
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or len(post) != 3
            or len(gates) != 1
            or len(orders) != 1
            or len(workspaces) != 1
            or not isinstance(expected_inputs, Mapping)
            or orders[0].data.get("action") != "H1-A-plan"
            or orders[0].data.get("h1_workspace") != initialized.reference
            or orders[0].data.get("inputs") != expected_inputs
            or expected_inputs.get("p1_package")
            != str(
                store.resolve_completion_package_root(
                    successor.data["current_stage_completions"]["P1"],
                    expected_stage="P1",
                )
            )
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        return
    if plan.data.get("transition_mode") == "internal_h1_html_readability_return":
        stale = plan.data.get("stale_identity", {})
        post = [
            SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        gates = [
            item for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        try:
            old_return = store.load_document(plan.data["superseded_return"])
            rendered = store.load_document(stale["current_workspace"])
            assembled = store.load_document(stale["restored_workspace"])
            failure = store.load_document(stale["readability_failure"])
            plan_manifest = store.load_document(stale["plan_manifest"])
            fragment_manifest = store.load_document(stale["fragment_manifest"])
            assembly_manifest = store.load_document(stale["assembly_manifest"])
            html_manifest = store.load_document(stale["html_manifest"])
            plan_root = store.resolve_document_path(plan_manifest.reference).parent
            fragment_root = store.resolve_document_path(
                fragment_manifest.reference
            ).parent
            assembly_root = store.resolve_document_path(
                assembly_manifest.reference
            ).parent
            html_root = store.resolve_document_path(html_manifest.reference).parent
            review_inputs, producer_identities = h1_readability_prepublish_contract(
                plan_package=plan_root,
                fragment_package_root=fragment_root,
                assembly_package=assembly_root,
                html_package=html_root,
                rendered_workspace=rendered,
            )
            validate_h1_readability_review(
                failure.data,
                expected_run_id=predecessor.data["run_id"],
                expected_session_id=rendered.data["session_id"],
                expected_phase="prepublish",
                inputs=review_inputs,
                producer_identities=producer_identities,
                expected_verdict="fail",
            )
            report_text = (assembly_root / "human-review-report.json").read_text(
                encoding="utf-8"
            )
            fragment_package = json.loads(
                (fragment_root / "fragment-package.json").read_text(
                    encoding="utf-8"
                )
            )
            from .h1_readability import validate_failure_evidence

            validate_failure_evidence(
                failure.data,
                report_text=report_text,
                fragment_texts={
                    item["id"]: item["text"]
                    for item in fragment_package["fragments"]
                },
            )
        except (
            H1ReadabilityError,
            KeyError,
            TypeError,
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ProductionStoreError,
        ) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        raw_inputs = plan.data.get("post_upgrade_inputs")
        expected_inputs = (
            copy.deepcopy(dict(raw_inputs)) if isinstance(raw_inputs, Mapping) else None
        )
        prior_generation = qualification.data.get("refresh_generation", 0)
        expected_stale = {
            "stage": "H1",
            "origin_action": "H1-C",
            "resume_point": "H1-C",
            "current_workspace": dict(rendered.reference),
            "restored_workspace": dict(assembled.reference),
            "plan_manifest": dict(plan_manifest.reference),
            "fragment_manifest": dict(fragment_manifest.reference),
            "assembly_manifest": dict(assembly_manifest.reference),
            "html_manifest": dict(html_manifest.reference),
            "readability_failure": dict(failure.reference),
            "evidence_ids": list(request.data.get("evidence_ids", [])),
        }
        expected_artifacts = {
            "plan_manifest": plan_manifest.reference,
            "fragment_manifest": fragment_manifest.reference,
            "assembly_manifest": assembly_manifest.reference,
            "html_manifest": html_manifest.reference,
        }
        if (
            predecessor.data.get("status") != "revise"
            or predecessor.data.get("author_decision") is not None
            or predecessor.data.get("active_return") != old_return.reference
            or "H1" in predecessor.data.get("current_stage_completions", {})
            or old_return.data.get("resume_stage") != "H1"
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("return_kind") != "local_revision"
            or request.data.get("calculated_owner") != "H1-C"
            or request.data.get("target_stage") != "H1"
            or request.data.get("resume_stage") != "H1"
            or request.data.get("resume_point") != "H1-C"
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts")
            != ["html", "completion"]
            or request.data.get("invalidate_author_decision") is not False
            or request.data.get("invalidate_conception_completion") is not False
            or request.data.get("evidence_ids") != [failure.data.get("review_id")]
            or successor.data.get("active_return") != request.reference
            or successor.data.get("status") != "revise"
            or successor.data.get("author_decision") is not None
            or successor.data.get("h1_workspace") is not None
            or successor.data.get("current_stage_completions")
            != predecessor.data.get("current_stage_completions")
            or rendered.data.get("state") != "rendered"
            or rendered.data.get("artifacts") != expected_artifacts
            or assembled.data.get("state") != "assembled"
            or assembled.data.get("run_id") != rendered.data.get("run_id")
            or assembled.data.get("session_id") != rendered.data.get("session_id")
            or assembled.data.get("p1_completion") != rendered.data.get("p1_completion")
            or rendered.data.get("previous_state_sha256")
            != assembled.reference.get("sha256")
            or assembled.data.get("artifacts")
            != {
                "plan_manifest": plan_manifest.reference,
                "fragment_manifest": fragment_manifest.reference,
                "assembly_manifest": assembly_manifest.reference,
            }
            or plan.data.get("stale_identity") != expected_stale
            or plan.data.get("invalidated_stages") != ["H1"]
            or plan.data.get("target_stage") != "H1"
            or plan.data.get("superseded_return") != old_return.reference
            or receipt.data.get("superseded_return") != old_return.reference
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or len(post) != 2
            or len(gates) != 1
            or len(orders) != 1
            or expected_inputs != {"assembly_package": str(assembly_root)}
            or orders[0].data.get("action") != "H1-C"
            or orders[0].data.get("h1_workspace") != assembled.reference
            or orders[0].data.get("required_actor") != ACTION_CONTRACT["H1-C"][1]
            or orders[0].data.get("inputs") != expected_inputs
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        return
    if plan.data.get("transition_mode") == "internal_h1_fragment_return":
        stale = plan.data.get("stale_identity", {})
        post = [
            SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        gates = [
            item for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        try:
            current_workspace = store.load_document(stale["current_workspace"])
            planned_workspace = store.load_document(stale["planned_workspace"])
            consumed_order = store.load_document(stale["consumed_work_order"])
            fidelity_failure = store.load_document(stale["fidelity_failure"])
            fragment_manifest = store.load_document(stale["fragment_manifest"])
        except (KeyError, TypeError, ProductionStoreError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        raw_inputs = plan.data.get("post_upgrade_inputs")
        expected_inputs = (
            copy.deepcopy(dict(raw_inputs)) if isinstance(raw_inputs, Mapping) else None
        )
        prior_generation = qualification.data.get("refresh_generation", 0)
        if (
            predecessor.data.get("active_return") is not None
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("calculated_owner") != "H1-B"
            or request.data.get("target_stage") != "H1"
            or request.data.get("resume_stage") != "H1"
            or request.data.get("resume_point") != "H1-B"
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts")
            != ["fragments", "assembly", "html", "completion"]
            or plan.data.get("invalidated_stages") != ["H1"]
            or plan.data.get("target_stage") != "H1"
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or successor.data.get("active_return") != request.reference
            or current_workspace.data.get("state") != "fragments_ready"
            or planned_workspace.data.get("state") != "planned"
            or current_workspace.data.get("session_id")
            != planned_workspace.data.get("session_id")
            or current_workspace.data.get("previous_state_sha256")
            != planned_workspace.reference["sha256"]
            or current_workspace.data.get("artifacts", {}).get("plan_manifest")
            != planned_workspace.data.get("artifacts", {}).get("plan_manifest")
            or current_workspace.data.get("artifacts", {}).get("fragment_manifest")
            != fragment_manifest.reference
            or consumed_order.data.get("action") != "H1-B"
            or stale.get("fidelity_failure") != fidelity_failure.reference
            or request.data.get("evidence_ids")
            != [fidelity_failure.data.get("review_id")]
            or plan.data.get("superseded_return") is not None
            or len(gates) != 1
            or len(orders) != 1
            or expected_inputs is None
            or orders[0].data.get("action") != "H1-B"
            or orders[0].data.get("h1_workspace") != planned_workspace.reference
            or orders[0].data.get("required_actor")
            != ACTION_CONTRACT["H1-B"][1]
            or orders[0].data.get("inputs") != expected_inputs
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        refreshed = ProductionCoordinator.from_snapshot(
            successor.data,
            successor.reference,
            active_return_request=request,
            runtime=store.runtime,
        )
        refreshed_context = ProductionContext(store, refreshed, successor, request)
        authoritative = _internal_h1_fragment_inputs(
            refreshed_context,
            planned_workspace=planned_workspace,
        )
        if expected_inputs != authoritative:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        return

    if plan.data.get("transition_mode") == "active_stage_return_refresh":
        old = plan.data.get("superseded_return")
        target = request.data.get("target_stage")
        try:
            old_body = store.load_document(old)
            target_index = STAGE_ORDER.index(target)
        except (ProductionStoreError, ValueError, KeyError, TypeError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        expected_suffix = list(STAGE_ORDER[target_index:])
        target_action = request.data.get("resume_point")
        expected_contract = ACTION_CONTRACT.get(target_action)
        post = [
            SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        gates = [
            item for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        raw_inputs = plan.data.get("post_upgrade_inputs")
        expected_inputs = (
            copy.deepcopy(dict(raw_inputs)) if isinstance(raw_inputs, Mapping) else None
        )
        if expected_inputs is not None:
            contract_qualification = _escalation_contract_qualification_payload(
                qualification, action=target
            )
            if contract_qualification is not None:
                expected_inputs["_contract_qualification"] = contract_qualification
        prior_generation = qualification.data.get("refresh_generation", 0)
        pending = plan.data.get("pending_work_order")
        if (
            predecessor.data.get("active_return") != old
            or not isinstance(old, Mapping)
            or old_body.data.get("resume_stage") != target
            or old_body.data.get("resume_point") != target_action
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != target
            or request.data.get("resume_stage") != target
            or request.data.get("resume_point") != old_body.data.get("resume_point")
            or request.reference == old_body.reference
            or request.data.get("return_id") == old_body.data.get("return_id")
            or request.data.get("invalidated_stages") != expected_suffix
            or plan.data.get("invalidated_stages") != expected_suffix
            or plan.data.get("target_stage") != target
            or plan.data.get("stale_identity") != {
                "stage": target,
                "superseded_return": dict(old),
                "evidence_ids": list(request.data.get("evidence_ids", [])),
            }
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("old_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or successor.data.get("active_return") != request.reference
            or receipt.data.get("superseded_return") != old
            or not isinstance(pending, Mapping)
            or plan.data.get("work_order_references") != [pending]
            or len(gates) != 1
            or len(orders) != 1
            or expected_inputs is None
            or "_contract_qualification" in raw_inputs
            or expected_contract is None
            or expected_contract[0] != target
            or orders[0].data.get("action") != target_action
            or orders[0].data.get("required_actor") != expected_contract[1]
            or orders[0].data.get("inputs") != expected_inputs
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                plan.reference["path"],
            )
        refreshed = ProductionCoordinator.from_snapshot(
            successor.data,
            successor.reference,
            active_return_request=request,
            runtime=store.runtime,
        )
        refreshed_context = ProductionContext(store, refreshed, successor, request)
        authoritative = _authoritative_package_inputs(
            refreshed_context, action=target_action, gate=gates[0]
        )
        if any(expected_inputs.get(field) != value for field, value in authoritative.items()):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                plan.reference["path"],
            )
        return

    if plan.data.get("transition_mode") == "stage_return":
        target = request.data.get("target_stage")
        origin = request.data.get("origin_stage")
        try:
            target_index = STAGE_ORDER.index(target)
            origin_index = STAGE_ORDER.index(origin)
        except (TypeError, ValueError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        expected_suffix = list(STAGE_ORDER[target_index:])
        expected_stale_identity = {
            "stage": target,
            "origin_stage": origin,
            "resume_point": request.data.get("resume_point"),
            "evidence_ids": list(request.data.get("evidence_ids", [])),
        }
        target_action = (
            request.data.get("resume_point") if target == "H1" else target
        )
        expected_contract = ACTION_CONTRACT.get(target_action)
        post = [
            SealedDocument(
                data=dict(item["data"]), reference=dict(item["reference"])
            )
            for item in plan.data.get("post_upgrade_documents", [])
        ]
        gates = [
            item
            for item in post
            if item.reference["path"].startswith("orchestration/input-gates/")
        ]
        orders = [
            item
            for item in post
            if item.reference == plan.data.get("post_upgrade_work_order")
        ]
        raw_inputs = plan.data.get("post_upgrade_inputs")
        expected_inputs = (
            copy.deepcopy(dict(raw_inputs))
            if isinstance(raw_inputs, Mapping)
            else None
        )
        if expected_inputs is not None:
            contract_qualification = _escalation_contract_qualification_payload(
                qualification, action=target
            )
            if contract_qualification is not None:
                expected_inputs["_contract_qualification"] = contract_qualification
        prior_generation = qualification.data.get("refresh_generation", 0)
        pending = plan.data.get("pending_work_order")
        if (
            predecessor.data.get("active_return") is not None
            or request.data.get("origin_kind") != "stage"
            or target_index > origin_index
            or request.data.get("resume_stage") != target
            or request.data.get("invalidated_stages") != expected_suffix
            or plan.data.get("invalidated_stages") != expected_suffix
            or plan.data.get("target_stage") != target
            or plan.data.get("stale_identity") != expected_stale_identity
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("old_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("prior_qualification") != qualification.reference
            or plan.data.get("refresh_generation") != prior_generation + 1
            or successor.data.get("active_return") != request.reference
            or plan.data.get("superseded_return") is not None
            or not isinstance(pending, Mapping)
            or plan.data.get("work_order_references") != [pending]
            or len(gates) != 1
            or len(orders) != 1
            or expected_inputs is None
            or "_contract_qualification" in raw_inputs
            or orders[0].data.get("action") != target_action
            or expected_contract is None
            or expected_contract[0] != target
            or orders[0].data.get("required_actor")
            != expected_contract[1]
            or orders[0].data.get("inputs") != expected_inputs
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                plan.reference["path"],
            )
        return

    if plan.data.get("transition_mode") == "active_return_escalation":
        old = plan.data.get("superseded_return")
        target = request.data.get("target_stage")
        try:
            old_body = store.load_document(old)
            target_index = STAGE_ORDER.index(target)
            old_index = STAGE_ORDER.index(old_body.data["resume_stage"])
        except (ProductionStoreError, ValueError, KeyError, TypeError) as error:
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", str(error)
            ) from error
        expected_suffix = list(STAGE_ORDER[target_index:])
        stale_contract_escalation = (
            qualification.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
        )
        if stale_contract_escalation:
            actual_target, expected_stale_identity = (
                _actual_contract_upgrade_target(store, predecessor, qualification)
            )
        else:
            actual_target = target
            expected_stale_identity = {
                "stage": target,
                "superseded_return": dict(old),
                "evidence_ids": list(request.data["evidence_ids"]),
            }
        post_orders = [
            item for item in plan.data.get("post_upgrade_documents", [])
            if item.get("reference") == plan.data.get("post_upgrade_work_order")
        ]
        raw_inputs = plan.data.get("post_upgrade_inputs")
        expected_inputs = (
            copy.deepcopy(dict(raw_inputs))
            if isinstance(raw_inputs, Mapping) else None
        )
        if expected_inputs is not None:
            expected_contract_qualification = (
                _escalation_contract_qualification_payload(
                    qualification, action=target
                )
            )
            if expected_contract_qualification is not None:
                expected_inputs["_contract_qualification"] = (
                    expected_contract_qualification
                )
        if (
            predecessor.data.get("active_return") != old
            or not isinstance(old, Mapping)
            or target_index >= old_index
            or actual_target != target
            or plan.data.get("old_contract_digest")
            != qualification.data.get("new_contract_digest")
            or plan.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
            or plan.data.get("production_contract")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            or plan.data.get("production_versions") != production_versions
            or plan.data.get("invalidated_stages") != expected_suffix
            or plan.data.get("stale_identity") != expected_stale_identity
            or request.data.get("invalidated_stages") != expected_suffix
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != old_body.data.get("resume_stage")
            or request.data.get("resume_stage") != target
            or successor.data.get("active_return") != request.reference
            or receipt.data.get("superseded_return") != old
            or len(post_orders) != 1
            or expected_inputs is None
            or "_contract_qualification" in raw_inputs
            or post_orders[0]["data"].get("inputs") != expected_inputs
            or post_orders[0]["data"].get("required_actor")
            != ACTION_CONTRACT[target][1]
        ):
            raise ProductionStoreError(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", plan.reference["path"]
            )
        return
    target, stale_identity = _actual_contract_upgrade_target(
        store, predecessor, qualification
    )
    expected_suffix = list(STAGE_ORDER[STAGE_ORDER.index(target) :])
    if (
        plan.data.get("new_contract_digest")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
        or plan.data.get("production_contract")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT
        or plan.data.get("production_versions") != production_versions
        or plan.data.get("target_stage") != target
        or request.data.get("target_stage") != target
        or plan.data.get("invalidated_stages") != expected_suffix
        or request.data.get("invalidated_stages") != expected_suffix
        or plan.data.get("stale_identity") != stale_identity
        or receipt.data.get("new_contract_digest")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
        or receipt.data.get("target_stage") != target
        or receipt.data.get("stale_identity") != stale_identity
        or successor.data.get("active_return") != request.reference
    ):
        raise ProductionStoreError(
            "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
            plan.reference["path"],
        )


def _contract_qualification_payload(
    store: ProductionRunStore,
    upgrade: SealedDocument,
    *,
    latest: SealedDocument,
    action: str,
) -> dict[str, Any] | None:
    if action not in {"E1", "T1"}:
        return None
    versions = upgrade.data.get("production_versions")
    expected_versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    if (
        versions != expected_versions
        or upgrade.data.get("new_contract_digest")
        != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
    ):
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_STALE", action
        )
    upstream_versions: dict[str, str] = {}
    if action == "T1":
        e1_reference = latest.data["current_stage_completions"].get("E1")
        if not isinstance(e1_reference, Mapping):
            raise ProductionOrchestratorError(
                "PROD_T1_E1_COMPLETION_MISSING", action
            )
        observed = _completion_model_schema_version(store, e1_reference)
        if observed != expected_versions["E1"]:
            raise ProductionOrchestratorError(
                "PROD_T1_E1_SCHEMA_VERSION_INVALID",
                f"expected E1 {expected_versions['E1']}, observed {observed}",
            )
        upstream_versions["E1"] = observed
    return {
        "contract_upgrade_receipt": dict(upgrade.reference),
        "contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        "owner_stage": action,
        "owner_schema_version": expected_versions[action],
        "upstream_schema_versions": upstream_versions,
    }


def _escalation_contract_qualification_payload(
    qualification: SealedDocument,
    *,
    action: str,
) -> dict[str, Any] | None:
    """Bind the first escalated order to its predecessor qualification.

    The order is part of the same transaction as the successor qualification,
    so it cannot name that successor receipt without creating a hash cycle.
    Its receipt reference therefore remains the prior qualification while the
    owner contract fields describe the production contract installed by the
    transaction.  This also covers a stale-contract escalation where the old
    and new contract digests differ.
    """

    if action not in {"E1", "T1"}:
        return None
    versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    return {
        "contract_upgrade_receipt": dict(qualification.reference),
        "contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        "owner_stage": action,
        "owner_schema_version": versions[action],
        "upstream_schema_versions": (
            {"E1": versions["E1"]} if action == "T1" else {}
        ),
    }


def _expected_contract_qualification(
    context: ProductionContext,
    *,
    latest: SealedDocument,
    action: str,
    qualification_override: SealedDocument | None = None,
) -> dict[str, Any] | None:
    if action not in {"E1", "T1"}:
        return None
    upgrade = qualification_override or _validate_current_contract_qualification(
        context.store, context.store.current_contract_upgrade(), scope=action
    )
    return _contract_qualification_payload(
        context.store, upgrade, latest=latest, action=action
    )


def _bound_h1_workspace(
    context: ProductionContext, work_order: SealedDocument
) -> SealedDocument:
    reference = work_order.data.get("h1_workspace")
    if not isinstance(reference, Mapping):
        raise ProductionOrchestratorError(
            "PROD_H1_WORKSPACE_UNBOUND", str(work_order.data.get("action"))
        )
    bound = context.store.load_document(reference)
    latest = context.store.latest_workspace()
    if latest.reference != bound.reference or latest.data != bound.data:
        raise ProductionOrchestratorError(
            "PROD_H1_WORKSPACE_STALE", str(work_order.data.get("action"))
        )
    return bound


def _prepare_state_commit(
    context: ProductionContext,
    work_order: SealedDocument,
    successor: SealedDocument,
    evidence: SealedDocument,
    *,
    return_request: SealedDocument | None = None,
) -> None:
    """Recompute the normative full transition before journaling it."""

    action = str(work_order.data.get("action"))
    fresh = ProductionCoordinator.from_snapshot(
        copy.deepcopy(context.state.data),
        copy.deepcopy(context.state.reference),
        active_return_request=context.active_return,
        runtime=context.store.runtime,
    )
    next_state_path = str(successor.reference.get("path"))
    try:
        if action in STAGE_ORDER[:-1] or action == "H1-publish":
            work_gate = context.store.load_document(work_order.data["input_gate"])
            gate = work_gate
            workspace_reference = None
            if action == "H1-publish":
                # H1 completion binds the current publication gate.  Its
                # execution record separately preserves the immutable H1-A
                # plan gate as provenance.
                completion_gate_ref = evidence.data.get("input_gate")
                if not isinstance(completion_gate_ref, Mapping):
                    raise ProductionOrchestratorError(
                        "PROD_COMMIT_EVIDENCE_INVALID",
                        "H1 completion input gate",
                    )
                gate = context.store.load_document(completion_gate_ref)
                if (
                    gate.reference != work_gate.reference
                    or gate.data != work_gate.data
                ):
                    raise ProductionOrchestratorError(
                        "PROD_COMMIT_EVIDENCE_INVALID",
                        "H1 completion does not bind the publication gate",
                    )
                workspace_reference = _bound_h1_workspace(
                    context, work_order
                ).reference
            expected = fresh.accept_stage_completion(
                gate=gate,
                completion=evidence,
                h1_workspace=workspace_reference,
                next_state_path=next_state_path,
                active_return_request=context.active_return,
            )
        elif action == "author-decision":
            return_id = (
                return_request.data["return_id"]
                if return_request is not None
                else "RET-AUTHOR-REVISION"
            )
            recomputed = record_author_decision(
                event=evidence,
                coordinator=fresh,
                next_state_path=next_state_path,
                return_id=return_id,
                runtime=context.store.runtime,
            )
            if (
                recomputed.return_request is None
                and return_request is not None
            ) or (
                recomputed.return_request is not None
                and (
                    return_request is None
                    or recomputed.return_request.reference
                    != return_request.reference
                    or recomputed.return_request.data != return_request.data
                )
            ):
                raise ProductionOrchestratorError(
                    "PROD_COMMIT_EVIDENCE_INVALID", "author return request"
                )
            expected = recomputed.transition
        elif action == "final":
            expected = fresh.accept_final_completion(
                completion=evidence,
                next_state_path=next_state_path,
            )
        else:
            raise ProductionOrchestratorError("PROD_ACTION_UNKNOWN", action)
    except ProductionOrchestratorError:
        raise
    except Exception as error:
        raise ProductionOrchestratorError(
            "PROD_COMMIT_EVIDENCE_INVALID", str(error)
        ) from error
    if (
        expected.snapshot != successor.data
        or expected.reference != successor.reference
    ):
        raise ProductionOrchestratorError(
            "PROD_COMMIT_DELTA_INVALID", action
        )
    context.store.persist_document(evidence)
    context.store._persist_commit_intent(
        work_order,
        successor=successor,
        successor_kind="state",
        evidence=evidence,
    )


def _prepare_h1_commit(
    context: ProductionContext,
    work_order: SealedDocument,
    *,
    bound: SealedDocument,
    successor: SealedDocument,
    manifest: SealedDocument,
) -> None:
    """Prove the exact owner manifest and one legal H1 workspace delta."""

    contracts = {
        "H1-A-plan": ("initialized", "planned", "plan_manifest", "h1-plan"),
        "H1-B": (
            "planned",
            "fragments_ready",
            "fragment_manifest",
            "h1-fragments",
        ),
        "H1-A-assemble": (
            "fragments_ready",
            "assembled",
            "assembly_manifest",
            "h1-assembly",
        ),
        "H1-C": ("assembled", "rendered", "html_manifest", "h1-html"),
    }
    action = str(work_order.data.get("action"))
    expected = contracts.get(action)
    if expected is None:
        raise ProductionOrchestratorError("PROD_ACTION_UNKNOWN", action)
    prior_state, next_state, artifact_key, profile = expected
    expected_artifacts = {
        **bound.data["artifacts"],
        artifact_key: manifest.reference,
    }
    if (
        bound.data.get("state") != prior_state
        or successor.data.get("state") != next_state
        or successor.data.get("run_id") != bound.data.get("run_id")
        or successor.data.get("session_id") != bound.data.get("session_id")
        or successor.data.get("p1_completion")
        != bound.data.get("p1_completion")
        or successor.data.get("previous_state_sha256")
        != bound.reference["sha256"]
        or successor.data.get("artifacts") != expected_artifacts
    ):
        raise ProductionOrchestratorError(
            "PROD_COMMIT_DELTA_INVALID", action
        )
    try:
        context.store.runtime.validate(
            manifest.data, "package-manifest.schema.json"
        )
    except Exception as error:
        raise ProductionOrchestratorError(
            "PROD_COMMIT_EVIDENCE_INVALID", str(error)
        ) from error
    if (
        canonical_sha256(manifest.data) != manifest.reference.get("sha256")
        or manifest.data.get("run_id") != bound.data.get("run_id")
        or manifest.data.get("stage") != "H1"
        or manifest.data.get("package_profile") != profile
        or manifest.data.get("verdict") != "ready"
        or manifest.data.get("session_id") != bound.data.get("session_id")
        or manifest.data.get("parent_state_sha256")
        != bound.reference["sha256"]
    ):
        raise ProductionOrchestratorError(
            "PROD_COMMIT_EVIDENCE_INVALID", action
        )
    context.store.persist_document(manifest)
    context.store._persist_commit_intent(
        work_order,
        successor=successor,
        successor_kind="h1-workspace",
        evidence=manifest,
    )


def _reconcile_pending_commit(
    store: ProductionRunStore, state: SealedDocument
) -> None:
    """Reconcile only a successor named by the immutable prepared intent."""

    order = store.pending_work_order()
    if order is None:
        return
    intent = store._load_commit_intent(order)
    if order.data.get("state") != state.reference:
        if (
            intent is None
            or intent.data.get("successor_kind") != "state"
            or intent.data.get("successor") != state.reference
        ):
            raise ProductionOrchestratorError(
                "PROD_UNJOURNALED_SUCCESSOR", str(order.data.get("work_id"))
            )
        store.mark_work_order_consumed(order, successor=state)
        return
    action = str(order.data.get("action"))
    if action not in H1_ACTION_STATES or action == "H1-publish":
        return
    bound_ref = order.data.get("h1_workspace")
    if not isinstance(bound_ref, Mapping):
        raise ProductionOrchestratorError(
            "PROD_H1_WORKSPACE_UNBOUND", action
        )
    current = store.latest_workspace()
    if current.reference == bound_ref:
        if intent is not None:
            relocation = _relocate_legacy_h1_successor(
                store, state=state, order=order, intent=intent,
                bound=current,
            )
            if relocation is not None:
                successor, receipt = relocation
                store.preflight_immutable_documents([successor, receipt])
                store.persist_workspace(successor)
                store.persist_document(receipt)
                store.mark_work_order_consumed(
                    order,
                    successor=successor,
                    successor_relocation=receipt,
                )
        return
    if intent is not None:
        bound = store.load_document(bound_ref)
        relocation = _relocate_legacy_h1_successor(
            store, state=state, order=order, intent=intent, bound=bound,
        )
        if relocation is not None:
            successor, receipt = relocation
            if current.reference == successor.reference:
                store.preflight_immutable_documents([successor, receipt])
                store.persist_document(receipt)
                store.mark_work_order_consumed(
                    order,
                    successor=current,
                    successor_relocation=receipt,
                )
                return
    if (
        intent is None
        or intent.data.get("successor_kind") != "h1-workspace"
        or intent.data.get("successor") != current.reference
    ):
        raise ProductionOrchestratorError(
            "PROD_UNJOURNALED_SUCCESSOR", str(order.data.get("work_id"))
        )
    store.mark_work_order_consumed(order, successor=current)


def _relocate_legacy_h1_successor(
    store: ProductionRunStore,
    *,
    state: SealedDocument,
    order: SealedDocument,
    intent: SealedDocument,
    bound: SealedDocument,
) -> tuple[SealedDocument, SealedDocument] | None:
    """Recover a retryable H1 intent whose historical flat path is occupied."""

    original = intent.data.get("successor")
    evidence_ref = intent.data.get("admission_evidence")
    specifications = {
        "H1-B": (
            "fragments_ready",
            "fragment_manifest",
            "h1-fragments",
            "h1-fragments-manifest-sha256-prefix-v1",
        ),
        "H1-C": (
            "rendered",
            "html_manifest",
            "h1-html",
            "h1-rendered-manifest-sha256-prefix-v1",
        ),
    }
    specification = specifications.get(str(order.data.get("action")))
    if (
        specification is None
        or intent.data.get("successor_kind") != "h1-workspace"
        or not isinstance(original, Mapping)
        or not isinstance(evidence_ref, Mapping)
    ):
        return None
    next_state, artifact_key, profile, algorithm = specification
    legacy_path = (
        f"H1/{bound.data.get('session_id')}/workspace-{next_state}.json"
    )
    if original.get("path") != legacy_path:
        return None
    collision_path = store.root / legacy_path
    if not collision_path.is_file():
        return None
    collision_ref = {"path": legacy_path, "sha256": sha256_file(collision_path)}
    if collision_ref["sha256"] == original.get("sha256"):
        return None

    collision = store.load_document(collision_ref)
    manifest = store.load_document(evidence_ref)
    expected_data = {
        "schema_version": "2.0",
        "run_id": bound.data["run_id"],
        "stage": "H1",
        "session_id": bound.data["session_id"],
        "state": next_state,
        "p1_completion": copy.deepcopy(bound.data["p1_completion"]),
        "previous_state_sha256": bound.reference["sha256"],
        "artifacts": {
            **copy.deepcopy(bound.data["artifacts"]),
            artifact_key: copy.deepcopy(manifest.reference),
        },
    }
    if (
        original.get("sha256") != canonical_sha256(expected_data)
        or manifest.data.get("package_profile") != profile
        or manifest.data.get("parent_state_sha256") != bound.reference["sha256"]
        or manifest.data.get("session_id") != bound.data["session_id"]
        or state.data.get("active_return") is None
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_SUCCESSOR_RELOCATION_INVALID", order.data["work_id"]
        )
    marker_match = False
    for path in sorted(
        (store.root / "orchestration/h1-artifact-invalidations").glob("*.json")
    ):
        marker = store.load_document({
            "path": path.relative_to(store.root).as_posix(),
            "sha256": sha256_file(path),
        })
        if (
            marker.data.get("status") == "superseded"
            and marker.data.get("h1_workspace") == collision_ref
            and marker.data.get("restored_workspace") == bound.reference
            and marker.data.get("successor_state") == state.reference
            and marker.data.get(artifact_key)
            == collision.data.get("artifacts", {}).get(artifact_key)
        ):
            marker_match = True
            break
    if not marker_match:
        raise ProductionOrchestratorError(
            "PROD_H1_SUCCESSOR_RELOCATION_UNTRUSTED", order.data["work_id"]
        )
    effective = SealedDocument(
        data=expected_data,
        reference={
            "path": (
                f"H1/{bound.data['session_id']}/workspace-{next_state}-"
                f"{manifest.reference['sha256'][:24]}.json"
            ),
            "sha256": original["sha256"],
        },
    )
    collision = {
        "path": collision_ref["path"],
        "sha256": collision_ref["sha256"],
    }
    receipt_data = {
        "schema_version": "1.0",
        "kind": "h1-workspace-successor-relocation",
        "work_order": copy.deepcopy(order.reference),
        "commit_intent": copy.deepcopy(intent.reference),
        "original_successor": copy.deepcopy(original),
        "effective_successor": copy.deepcopy(effective.reference),
        "collision": collision,
        "algorithm": algorithm,
        "status": "complete",
    }
    transition_id = canonical_sha256(receipt_data)[:24]
    receipt = SealedDocument(
        data=receipt_data,
        reference={
            "path": (
                "orchestration/h1-workspace-relocations/"
                f"{transition_id}.json"
            ),
            "sha256": canonical_sha256(receipt_data),
        },
    )
    return effective, receipt


def _relocate_legacy_h1_fragment_successor(
    store: ProductionRunStore,
    *,
    state: SealedDocument,
    order: SealedDocument,
    intent: SealedDocument,
    bound: SealedDocument,
) -> tuple[SealedDocument, SealedDocument] | None:
    """Compatibility alias for callers of the original private H1-B helper."""

    return _relocate_legacy_h1_successor(
        store, state=state, order=order, intent=intent, bound=bound
    )


def initialize_production_run(
    run_root: str | Path,
    *,
    run_id: str,
    source_interview_state: Mapping[str, str],
    runtime: ContractRuntime | None = None,
) -> ProductionContext:
    contract_runtime = runtime or ContractRuntime()
    store = ProductionRunStore(run_root, runtime=contract_runtime)
    with store.lock():
        store.ensure_uninitialized()
        coordinator = ProductionCoordinator.initialize(
            run_id=run_id,
            source_interview_state=source_interview_state,
            state_path="state/revision-000.json",
            runtime=contract_runtime,
        )
        state = SealedDocument(
            data=coordinator.state, reference=coordinator.state_reference
        )
        store.persist_state(state)
        store.install_initial_contract_qualification(
            contract_digest=CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            production_versions={
                stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                    "model_schema_version"
                ]
                for stage in ("E1", "T1")
            },
            production_contract=CURRENT_CONCEPTION_PRODUCTION_CONTRACT,
        )
    return ProductionContext(store, coordinator, state, None)


def _resume_production_run(
    run_root: str | Path,
    *,
    runtime: ContractRuntime | None = None,
    allow_stale_contract_for_upgrade: bool = False,
) -> ProductionContext:
    contract_runtime = runtime or ContractRuntime()
    store = ProductionRunStore(run_root, runtime=contract_runtime)
    with store.lock():
        state = store.latest_state()
        state = store.reconcile_contract_upgrades(
            state,
            transaction_validator=lambda **values: _validate_prepared_contract_upgrade(
                store=store, **values
            ),
        )
        if not allow_stale_contract_for_upgrade:
            _validate_current_contract_qualification(
                store, store.current_contract_upgrade(), scope="resume"
            )
        _reconcile_pending_commit(store, state)
        # Canonical JSON sorts object keys; restore the normative stage order
        # required by author-decision validation without changing the hash.
        state_data = copy.deepcopy(state.data)
        current = state_data["current_stage_completions"]
        state_data["current_stage_completions"] = {
            stage: current[stage] for stage in STAGE_ORDER if stage in current
        }
        state = SealedDocument(data=state_data, reference=state.reference)
        active = None
        if state.data["active_return"] is not None:
            active = store.load_document(state.data["active_return"])
        coordinator = ProductionCoordinator.from_snapshot(
            state.data,
            state.reference,
            active_return_request=active,
            runtime=contract_runtime,
        )
    return ProductionContext(store, coordinator, state, active)


def resume_production_run(
    run_root: str | Path, *, runtime: ContractRuntime | None = None
) -> ProductionContext:
    return _resume_production_run(run_root, runtime=runtime)


def resume_production_run_for_contract_upgrade(
    run_root: str | Path, *, runtime: ContractRuntime | None = None
) -> ProductionContext:
    """Resume a stale run solely so ``apply_contract_upgrade`` can repair it.

    Ordinary E1/T1 work remains qualification-gated; this entry point grants
    no stage-signing authority.
    """
    return _resume_production_run(
        run_root,
        runtime=runtime,
        allow_stale_contract_for_upgrade=True,
    )


def issue_stage_work(
    context: ProductionContext,
    *,
    action: str,
    inputs: Mapping[str, Any],
) -> tuple[SealedDocument, SealedDocument]:
    """Build the exact current gate and publish the unique Agent work order."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        contract = ACTION_CONTRACT.get(action)
        if contract is None:
            raise ProductionOrchestratorError("PROD_ACTION_UNKNOWN", action)
        target_stage, required_actor = contract
        if action == "author-decision" and latest.data["status"] != "waiting_author":
            raise ProductionOrchestratorError(
                "PROD_ACTION_NOT_READY", "author decision requires waiting_author"
            )
        if action == "final" and latest.data["status"] != "approved":
            raise ProductionOrchestratorError(
                "PROD_ACTION_NOT_READY", "final requires approved"
            )
        if action in H1_ACTION_STATES:
            workspace = context.store.latest_workspace()
            required_state = H1_ACTION_STATES[action][0]
            if workspace.data["state"] != required_state:
                raise ProductionOrchestratorError(
                    "PROD_ACTION_NOT_READY",
                    f"{action} requires H1 workspace {required_state}",
                )
        gate = None
        workspace = None
        if target_stage is not None:
            gate_path = (
                "orchestration/input-gates/"
                f"revision-{latest.data['revision']:03d}-{action}/input-gate.json"
            )
            gate = context.coordinator.build_input_gate(
                target_stage, gate_path,
                active_return_request=context.active_return,
            )
        if action in H1_ACTION_STATES:
            workspace = context.store.latest_workspace()
        qualified_inputs = copy.deepcopy(dict(inputs))
        if "_contract_qualification" in qualified_inputs:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_QUALIFICATION_RESERVED", action
            )
        authoritative_inputs = _authoritative_package_inputs(
            context, action=action, gate=gate
        )
        for field, value in authoritative_inputs.items():
            observed = qualified_inputs.get(field)
            if observed is not None and str(observed) != value:
                raise ProductionOrchestratorError(
                    "PROD_WORK_INPUT_OVERRIDE", field
                )
            qualified_inputs[field] = value
        qualification = _expected_contract_qualification(
            context, latest=latest, action=action
        )
        if qualification is not None:
            qualified_inputs["_contract_qualification"] = qualification
        # Qualification replays sealed upstream packages and can fail on
        # missing, ambiguous, or tampered provenance.  Publish no gate until
        # that complete read-only proof has succeeded.
        if gate is not None:
            context.store.persist_document(gate)
        order = context.store.issue_work_order(
            run_id=context.state.data["run_id"],
            action=action,
            state=context.state,
            input_gate=gate,
            h1_workspace=workspace,
            required_actor=required_actor,
            inputs=qualified_inputs,
        )
        return gate, order


def apply_contract_upgrade(
    context: ProductionContext,
    *,
    request: SealedDocument,
    old_contract_digest: str,
    session_references: tuple[Mapping[str, str], ...] = (),
) -> tuple[SealedDocument, ProductionContext]:
    """Append an E1/T1 qualification migration without rewriting old packages.

    The routed return remains the sole owner of suffix invalidation.  This
    transaction adds crash-replayable qualification, session, work-order, and
    commit-intent receipts around that existing coordinator transition.
    """

    if re.fullmatch(r"[a-f0-9]{64}", old_contract_digest) is None:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_DIGEST_INVALID", old_contract_digest
        )
    if request.data.get("return_kind") != "local_revision" or request.data.get(
        "target_stage"
    ) not in {"E1", "T1"}:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_RETURN_INVALID", str(request.data.get("return_id"))
        )
    production_versions = {
        stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
            "model_schema_version"
        ]
        for stage in ("E1", "T1")
    }
    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        current_qualification = context.store.current_contract_upgrade()
        target, stale_identity = _actual_contract_upgrade_target(
            context.store, latest, current_qualification
        )
        if request.data.get("target_stage") != target:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_UPGRADE_TARGET_MISMATCH",
                f"expected {target}, observed {request.data.get('target_stage')}",
            )
        expected_suffix = list(STAGE_ORDER[STAGE_ORDER.index(target) :])
        if request.data.get("invalidated_stages") != expected_suffix:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_UPGRADE_SUFFIX_INVALID", target
            )
        expected_old_digest = (
            current_qualification.data.get("new_contract_digest")
            if current_qualification is not None
            else canonical_sha256(stale_identity)
        )
        if old_contract_digest != expected_old_digest:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_DIGEST_UNBOUND", old_contract_digest
            )

        active_request = context.active_return
        transition_mode = "new_return"
        refresh_generation = 0
        if latest.data.get("active_return") is not None:
            transition_mode = "active_return_refresh"
            if (
                active_request is None
                or latest.data["active_return"] != active_request.reference
                or request.reference != active_request.reference
                or request.data != active_request.data
            ):
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_UPGRADE_ACTIVE_RETURN_MISMATCH",
                    str(request.data.get("return_id")),
                )
            prior_generation = (
                current_qualification.data.get("refresh_generation", 0)
                if current_qualification is not None
                else 0
            )
            if not isinstance(prior_generation, int) or prior_generation < 0:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_QUALIFICATION_STALE",
                    "refresh_generation",
                )
            refresh_generation = prior_generation + 1

        # Inventory is derived from sealed run state and actual files.  Caller
        # values are assertions only; they can never create invalidation scope.
        trusted_markers = context.store.trusted_contract_upgrade_markers()
        invalidated_sessions: set[tuple[str, str]] = trusted_markers[
            "invalidated_sessions"
        ]
        completed_session_ids: set[str] = set()
        for completion_path in context.store.root.rglob("stage-completion.json"):
            completion_relative = completion_path.relative_to(
                context.store.root
            ).as_posix()
            if completion_relative.startswith(
                "orchestration/superseded-packages/"
            ):
                # Only the archived package's own completion identifies a
                # workspace session as completed.  Nested source packages are
                # immutable evidence and can exceed the normal Windows path
                # namespace, so they must not be recursively inspected.
                parts = Path(completion_relative).parts
                if not (
                    len(parts) == 5
                    and parts[:2] == (
                        "orchestration", "superseded-packages"
                    )
                    and parts[2] in {"E1", "T1"}
                    and re.fullmatch(r"[a-f0-9]{64}", parts[3]) is not None
                    and parts[4] == "stage-completion.json"
                ):
                    continue
            try:
                completion_value = json.loads(
                    completion_path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            if (
                completion_value.get("stage") in {"E1", "T1"}
                and isinstance(completion_value.get("session_id"), str)
            ):
                completed_session_ids.add(completion_value["session_id"])
        scanned_sessions: list[dict[str, str]] = []
        for path in sorted(context.store.root.rglob("generation-session.json")):
            relative = path.relative_to(context.store.root).as_posix()
            if relative.startswith((
                "orchestration/contract-upgrades/",
                "orchestration/superseded-packages/",
            )):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_SESSION_INVALID", f"{relative}: {exc}"
                ) from exc
            if data.get("stage") not in {"E1", "T1"}:
                continue
            reference = {"path": relative, "sha256": sha256_file(path)}
            if (
                (reference["path"], reference["sha256"])
                in invalidated_sessions
                or data.get("session_id") in completed_session_ids
            ):
                continue
            scanned_sessions.append(reference)
        asserted_sessions = [dict(item) for item in session_references]
        if asserted_sessions and asserted_sessions != scanned_sessions:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_SESSION_INVENTORY_MISMATCH", target
            )

        active_orders: list[SealedDocument] = []
        order_root = context.store.root / "orchestration" / "work-orders"
        if order_root.is_dir():
            for path in sorted(order_root.glob("*.json")):
                if any(
                    marker in path.name
                    for marker in (".consumed.", ".rejected.")
                ):
                    continue
                reference = {
                    "path": path.relative_to(context.store.root).as_posix(),
                    "sha256": sha256_file(path),
                }
                order = context.store.load_document(reference)
                if order.data.get("action") in expected_suffix:
                    consumed = path.with_name(
                        f"{order.data['work_id']}.consumed.json"
                    )
                    rejected = path.with_name(
                        f"{order.data['work_id']}.rejected.json"
                    )
                    rejected_logical = rejected.relative_to(
                        context.store.root
                    ).as_posix()
                    if not consumed.exists() and rejected_logical not in (
                        trusted_markers["work_order_rejections"]
                    ):
                        active_orders.append(order)
        completion_references = [
            {"stage": stage, "completion": dict(reference)}
            for stage, reference in latest.data["current_stage_completions"].items()
            if stage in expected_suffix
        ]
        pending = context.store.pending_work_order()
        pending_intent = (
            context.store._load_commit_intent(pending)
            if pending is not None
            else None
        )
        # Recompute on an isolated coordinator.  Validation or immutable-write
        # conflicts therefore cannot mutate the caller's in-memory state.
        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            copy.deepcopy(latest.reference),
            active_return_request=active_request,
            runtime=context.store.runtime,
        )
        next_state_path = f"state/revision-{latest.data['revision'] + 1:03d}.json"
        if transition_mode == "active_return_refresh":
            transition = fresh.refresh_active_return(
                request=request,
                next_state_path=next_state_path,
            )
        else:
            transition = fresh.apply_return_request(
                request=request,
                next_state_path=next_state_path,
            )
        successor = _sealed(transition)
        migration_id = canonical_sha256(
            [
                latest.reference,
                request.reference,
                old_contract_digest,
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            ]
        )[:24]
        inventory = {
            "session_references": scanned_sessions,
            "work_order_references": [
                dict(item.reference) for item in active_orders
            ],
            "completion_references": completion_references,
            "pending_work_order": (
                dict(pending.reference) if pending is not None else None
            ),
            "pending_commit_intent": (
                dict(pending_intent.reference)
                if pending_intent is not None
                else None
            ),
        }
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": old_contract_digest,
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": expected_suffix,
            "production_versions": production_versions,
            **inventory,
            "transition_mode": transition_mode,
            "refresh_generation": refresh_generation,
            "prior_qualification": (
                dict(current_qualification.reference)
                if current_qualification is not None
                else None
            ),
            "target_stage": target,
            "stale_identity": copy.deepcopy(stale_identity),
            "production_contract": copy.deepcopy(
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            ),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": None,
            "post_upgrade_documents": [],
            "post_upgrade_work_order": None,
            "post_upgrade_inputs": None,
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
        )
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(
            plan, successor=successor
        )
    return receipt, ProductionContext(
        context.store, fresh, successor, request
    )


def apply_stage_return(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    request: SealedDocument,
    actor: str,
    inputs: Mapping[str, Any],
) -> tuple[SealedDocument, ProductionContext, SealedDocument, SealedDocument]:
    """Atomically register a first stage-origin return and issue its owner work.

    This is the fail-closed path for a pending stage that cannot satisfy hard
    admission because an upstream owner must revise its sealed output.  The
    return, successor state, rejected pending order, invalidation receipts,
    return-resolution gate, and replacement work order share the existing
    append-only qualification journal and its crash recovery protocol.
    """

    if "_contract_qualification" in inputs:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_RESERVED",
            request.data.get("target_stage", "stage-return"),
        )

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        _require_work_actor(work_order, actor)
        if (
            context.active_return is not None
            or latest.data.get("active_return") is not None
        ):
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_ACTIVE_EXISTS",
                str(request.data.get("return_id", "")),
            )

        origin = work_order.data.get("action")
        target = request.data.get("target_stage")
        if (
            origin not in STAGE_ORDER
            or target not in STAGE_ORDER
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != origin
            or request.data.get("resume_stage") != target
        ):
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_ROUTE_INVALID",
                str(request.data.get("return_id", "")),
            )

        qualification = _validate_current_contract_qualification(
            context.store,
            context.store.current_contract_upgrade(),
            scope="stage-return",
        )
        pending = context.store.pending_work_order()
        if (
            pending is None
            or pending.reference != work_order.reference
            or pending.data != work_order.data
            or pending.data.get("status") != "pending"
        ):
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_PENDING_ORDER_INVALID", str(origin)
            )
        try:
            pending_gate = context.store.load_document(pending.data["input_gate"])
            expected_pending_gate = context.coordinator.build_input_gate(
                str(origin), pending_gate.reference["path"]
            )
        except (ProductionStoreError, CoordinatorError) as error:
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_PENDING_GATE_INVALID", str(error)
            ) from error
        if pending_gate != expected_pending_gate:
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_PENDING_GATE_INVALID", pending.data["work_id"]
            )

        expected_suffix = list(STAGE_ORDER[STAGE_ORDER.index(str(target)) :])
        if request.data.get("invalidated_stages") != expected_suffix:
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_SUFFIX_INVALID", str(target)
            )

        trusted = context.store.trusted_contract_upgrade_markers()
        pending_intent = context.store._load_commit_intent(pending)
        completed_session_ids: set[str] = set()
        for completion_path in context.store.root.rglob("stage-completion.json"):
            try:
                value = json.loads(completion_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(value.get("session_id"), str):
                completed_session_ids.add(value["session_id"])
        sessions: list[dict[str, str]] = []
        for path in sorted(context.store.root.rglob("generation-session.json")):
            relative = path.relative_to(context.store.root).as_posix()
            if relative.startswith((
                "orchestration/contract-upgrades/",
                "orchestration/superseded-packages/",
            )):
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except Exception as error:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_SESSION_INVALID", f"{relative}: {error}"
                ) from error
            reference = {"path": relative, "sha256": sha256_file(path)}
            if (
                value.get("stage") in expected_suffix
                and value.get("session_id") not in completed_session_ids
                and (reference["path"], reference["sha256"])
                not in trusted["invalidated_sessions"]
            ):
                sessions.append(reference)
        completions = [
            {"stage": stage, "completion": dict(reference)}
            for stage, reference in latest.data["current_stage_completions"].items()
            if stage in expected_suffix
        ]

        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            copy.deepcopy(latest.reference),
            active_return_request=None,
            runtime=context.store.runtime,
        )
        try:
            transition = fresh.apply_return_request(
                request=request,
                next_state_path=f"state/revision-{latest.data['revision'] + 1:03d}.json",
            )
        except CoordinatorError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        successor = _sealed(transition)

        target_action = (
            request.data["resume_point"] if target == "H1" else str(target)
        )
        contract = ACTION_CONTRACT.get(target_action)
        if contract is None or contract[0] != target:
            raise ProductionOrchestratorError(
                "PROD_STAGE_RETURN_ROUTE_INVALID", target_action
            )
        gate = fresh.build_input_gate(
            str(target),
            (
                "orchestration/input-gates/"
                f"revision-{successor.data['revision']:03d}-{target_action}/"
                "input-gate.json"
            ),
            active_return_request=request,
        )
        returned_context = ProductionContext(
            store=context.store,
            coordinator=fresh,
            state=successor,
            active_return=request,
        )
        qualified_inputs = copy.deepcopy(dict(inputs))
        authoritative_inputs = _authoritative_package_inputs(
            returned_context, action=target_action, gate=gate
        )
        for field, value in authoritative_inputs.items():
            observed = qualified_inputs.get(field)
            if observed is not None and str(observed) != value:
                raise ProductionOrchestratorError(
                    "PROD_WORK_INPUT_OVERRIDE", field
                )
            qualified_inputs[field] = value
        contract_qualification = _escalation_contract_qualification_payload(
            qualification, action=str(target)
        )
        if contract_qualification is not None:
            qualified_inputs["_contract_qualification"] = contract_qualification
        order_body = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "action": target_action,
            "state": dict(successor.reference),
            "input_gate": dict(gate.reference),
            "h1_workspace": None,
            "required_actor": contract[1],
            "inputs": qualified_inputs,
            "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        post_documents = [
            {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
            {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
        ]
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                "model_schema_version"
            ]
            for stage in ("E1", "T1")
        }
        inventory = {
            "session_references": sessions,
            "work_order_references": [dict(pending.reference)],
            "completion_references": completions,
            "pending_work_order": dict(pending.reference),
            "pending_commit_intent": (
                dict(pending_intent.reference) if pending_intent else None
            ),
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256([
            latest.reference,
            request.reference,
            qualification.data["new_contract_digest"],
            CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        ])[:24]
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": expected_suffix,
            "production_versions": production_versions,
            **inventory,
            "transition_mode": "stage_return",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": target,
            "stale_identity": {
                "stage": target,
                "origin_stage": origin,
                "resume_point": request.data["resume_point"],
                "evidence_ids": list(request.data["evidence_ids"]),
            },
            "production_contract": copy.deepcopy(
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            ),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": None,
            "post_upgrade_documents": post_documents,
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": _sealed_executor_inputs(order),
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, _derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
            complete_receipt=receipt,
        )
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(
            plan, successor=successor
        )
    returned = ProductionContext(context.store, fresh, successor, request)
    return receipt, returned, gate, order


def apply_internal_h1_fragment_return(
    context: ProductionContext,
    *,
    consumed_work_order: SealedDocument,
    fidelity_failure: SealedDocument,
    request: SealedDocument,
    actor: str,
    inputs: Mapping[str, Any],
) -> tuple[SealedDocument, ProductionContext, SealedDocument, SealedDocument]:
    """Return an accepted mechanical H1-B package after independent fidelity fail.

    This deliberately does not widen :func:`apply_stage_return`.  It is the
    single internal-H1 recovery edge from ``fragments_ready`` to the already
    sealed same-session ``planned`` workspace.
    """

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError("PROD_WORK_ACTOR_MISMATCH", actor)
    if "_contract_qualification" in inputs:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_RESERVED", "H1-B"
        )

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        if context.active_return is not None or latest.data.get("active_return") is not None:
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_ACTIVE_EXISTS",
                str(request.data.get("return_id", "")),
            )
        qualification = _validate_current_contract_qualification(
            context.store,
            context.store.current_contract_upgrade(),
            scope="internal-h1-fragment-return",
        )
        workspace = context.store.latest_workspace()
        if (
            workspace.data.get("state") != "fragments_ready"
            or set(workspace.data.get("artifacts", {}))
            != {"plan_manifest", "fragment_manifest"}
            or "H1" in latest.data.get("current_stage_completions", {})
            or any(
                (context.store.root / "H1" / name).exists()
                for name in ("assembly", "html", "stage")
            )
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_STATE_INVALID", "fragments_ready"
            )
        planned_reference = {
            "path": (
                f"H1/{workspace.data['session_id']}/workspace-planned.json"
            ),
            "sha256": workspace.data["previous_state_sha256"],
        }
        try:
            planned = context.store.load_document(planned_reference)
            persisted_order = context.store.load_document(
                consumed_work_order.reference
            )
            fragment_manifest = context.store.load_document(
                workspace.data["artifacts"]["fragment_manifest"]
            )
        except ProductionStoreError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        if (
            persisted_order.data != consumed_work_order.data
            or consumed_work_order.data.get("action") != "H1-B"
            or consumed_work_order.data.get("state") != latest.reference
            or consumed_work_order.data.get("h1_workspace") != planned.reference
            or planned.data.get("state") != "planned"
            or planned.data.get("session_id") != workspace.data.get("session_id")
            or planned.data.get("p1_completion") != workspace.data.get("p1_completion")
            or planned.data.get("artifacts")
            != {"plan_manifest": workspace.data["artifacts"]["plan_manifest"]}
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_ORDER_INVALID",
                str(consumed_work_order.data.get("work_id", "")),
            )
        consumed_path = (
            context.store.root / "orchestration" / "work-orders"
            / f"{consumed_work_order.data['work_id']}.consumed.json"
        )
        if not consumed_path.is_file():
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_ORDER_INVALID", "missing consumed marker"
            )
        consumed_body = json.loads(consumed_path.read_text(encoding="utf-8"))
        expected_consumed = {
            "schema_version": "2.0",
            "work_order": dict(consumed_work_order.reference),
            "successor": dict(workspace.reference),
            "status": "consumed",
        }
        if consumed_body != expected_consumed:
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_ORDER_INVALID", "consumed marker"
            )

        fragment_artifacts = _validate_internal_h1_fragment_package(
            context,
            manifest=fragment_manifest,
            workspace=workspace,
            planned_workspace=planned,
        )

        _validate_internal_h1_fidelity_failure(
            context, fidelity_failure, workspace=workspace
        )
        for path in (
            context.store.root / "orchestration" / "contract-upgrades"
        ).glob("*.json"):
            try:
                prior = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_QUALIFICATION_STALE", str(error)
                ) from error
            if prior.get("stale_identity", {}).get(
                "fidelity_failure"
            ) == fidelity_failure.reference:
                raise ProductionOrchestratorError(
                    "PROD_H1_FRAGMENT_FIDELITY_FAILURE_REUSED",
                    fidelity_failure.data["review_id"],
                )
        if (
            request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("return_kind") != "local_revision"
            or request.data.get("calculated_owner") != "H1-B"
            or request.data.get("target_stage") != "H1"
            or request.data.get("resume_stage") != "H1"
            or request.data.get("resume_point") != "H1-B"
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts")
            != ["fragments", "assembly", "html", "completion"]
            or request.data.get("evidence_ids")
            != [fidelity_failure.data["review_id"]]
            or request.reference.get("path")
            != (
                f"returns/{request.data.get('return_id', '')}/return-request.json"
            )
            or canonical_sha256(request.data) != request.reference.get("sha256")
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_FRAGMENT_RETURN_ROUTE_INVALID",
                str(request.data.get("return_id", "")),
            )

        pending = context.store.pending_work_order()
        pending_intent = None
        if pending is not None:
            if (
                pending.data.get("action") != "H1-A-assemble"
                or pending.data.get("state") != latest.reference
                or pending.data.get("h1_workspace") != workspace.reference
            ):
                raise ProductionOrchestratorError(
                    "PROD_H1_FRAGMENT_RETURN_DOWNSTREAM_INVALID",
                    str(pending.data.get("work_id", "")),
                )
            pending_intent = context.store._load_commit_intent(pending)

        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            copy.deepcopy(latest.reference),
            active_return_request=None,
            runtime=context.store.runtime,
        )
        try:
            transition = fresh.apply_return_request(
                request=request,
                next_state_path=f"state/revision-{latest.data['revision'] + 1:03d}.json",
            )
        except CoordinatorError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        successor = _sealed(transition)
        gate = fresh.build_input_gate(
            "H1",
            (
                "orchestration/input-gates/"
                f"revision-{successor.data['revision']:03d}-H1-B/input-gate.json"
            ),
            active_return_request=request,
        )
        returned_context = ProductionContext(
            context.store, fresh, successor, request
        )
        authoritative_inputs = _internal_h1_fragment_inputs(
            returned_context, planned_workspace=planned
        )
        if dict(inputs) and dict(inputs) != authoritative_inputs:
            raise ProductionOrchestratorError(
                "PROD_WORK_INPUT_OVERRIDE", "H1-B"
            )
        order_body = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "action": "H1-B",
            "state": dict(successor.reference),
            "input_gate": dict(gate.reference),
            "h1_workspace": dict(planned.reference),
            "required_actor": ACTION_CONTRACT["H1-B"][1],
            "inputs": authoritative_inputs,
            "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        session_references = [
            dict(fragment_artifacts["generation_session"].reference)
        ]
        inventory = {
            "session_references": session_references,
            "work_order_references": (
                [dict(pending.reference)] if pending is not None else []
            ),
            "completion_references": [],
            "pending_work_order": (
                dict(pending.reference) if pending is not None else None
            ),
            "pending_commit_intent": (
                dict(pending_intent.reference) if pending_intent is not None else None
            ),
        }
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                "model_schema_version"
            ]
            for stage in ("E1", "T1")
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256([
            latest.reference,
            request.reference,
            qualification.data["new_contract_digest"],
            CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        ])[:24]
        consumed_reference = {
            "path": consumed_path.relative_to(context.store.root).as_posix(),
            "sha256": sha256_file(consumed_path),
        }
        stale_identity = {
            "stage": "H1",
            "origin_action": "H1-B",
            "resume_point": "H1-B",
            "consumed_work_order": dict(consumed_work_order.reference),
            "consumed_marker": consumed_reference,
            "current_workspace": dict(workspace.reference),
            "planned_workspace": dict(planned.reference),
            "fragment_manifest": dict(fragment_manifest.reference),
            "fidelity_failure": dict(fidelity_failure.reference),
            "evidence_ids": list(request.data["evidence_ids"]),
        }
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": ["H1"],
            "production_versions": production_versions,
            **inventory,
            "transition_mode": "internal_h1_fragment_return",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": "H1",
            "stale_identity": stale_identity,
            "production_contract": copy.deepcopy(
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            ),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": None,
            "post_upgrade_documents": [
                {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
                {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
            ],
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": copy.deepcopy(authoritative_inputs),
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, _derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
            complete_receipt=receipt,
        )
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(
            plan, successor=successor
        )
    return (
        receipt,
        ProductionContext(context.store, fresh, successor, request),
        gate,
        order,
    )


def apply_internal_h1_readability_return(
    context: ProductionContext,
    *,
    readability_failure: SealedDocument,
    request: SealedDocument,
    actor: str,
) -> tuple[
    SealedDocument, ProductionContext, SealedDocument, SealedDocument,
    SealedDocument,
]:
    """Atomically return an unreadable waiting-author H1 to fresh H1-A-plan.

    The author has made no decision.  A separately identified reviewer binds
    exact published author-facing bytes and the transaction supersedes only
    the H1 suffix while preserving every accepted B0--P1 completion.
    """

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError("PROD_WORK_ACTOR_MISMATCH", actor)
    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        if (
            latest.data.get("status") != "waiting_author"
            or latest.data.get("author_decision") is not None
            or latest.data.get("active_return") is not None
            or context.active_return is not None
            or context.store.pending_work_order() is not None
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_RETURN_STATE_INVALID", "waiting_author"
            )
        qualification = _validate_current_contract_qualification(
            context.store,
            context.store.current_contract_upgrade(),
            scope="internal-h1-readability-return",
        )
        completion_reference = latest.data.get("current_stage_completions", {}).get(
            "H1"
        )
        if not isinstance(completion_reference, Mapping):
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_RETURN_STATE_INVALID", "missing H1 completion"
            )
        try:
            completion = context.store.load_document(completion_reference)
            h1_manifest = context.store.load_document(completion.data["manifest"])
            rendered = context.store.latest_workspace()
        except (ProductionStoreError, KeyError, TypeError) as error:
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_RETURN_BINDING_INVALID", str(error)
            ) from error
        artifacts = rendered.data.get("artifacts", {})
        if (
            rendered.data.get("state") != "rendered"
            or completion.data.get("session_id") != rendered.data.get("session_id")
            or set(artifacts)
            != {"plan_manifest", "fragment_manifest", "assembly_manifest", "html_manifest"}
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_RETURN_BINDING_INVALID", "rendered workspace"
            )
        fragment_root = context.store.resolve_document_path(
            artifacts["fragment_manifest"]
        ).parent
        plan_root = context.store.resolve_document_path(artifacts["plan_manifest"]).parent
        assembly_root = context.store.resolve_document_path(
            artifacts["assembly_manifest"]
        ).parent
        html_root = context.store.resolve_document_path(artifacts["html_manifest"]).parent
        try:
            review_inputs, producer_identities = h1_readability_prepublish_contract(
                plan_package=plan_root,
                fragment_package_root=fragment_root,
                assembly_package=assembly_root,
                html_package=html_root,
                rendered_workspace=rendered,
            )
            review_inputs["h1_completion"] = dict(completion.reference)
            review_inputs["h1_manifest"] = dict(h1_manifest.reference)
            validate_h1_readability_review(
                readability_failure.data,
                expected_run_id=latest.data["run_id"],
                expected_session_id=rendered.data["session_id"],
                expected_phase="postpublish_failure",
                inputs=review_inputs,
                producer_identities=producer_identities,
                expected_verdict="fail",
            )
            report_text = (
                assembly_root / "human-review-report.json"
            ).read_text(encoding="utf-8")
            fragment_package_value = json.loads(
                (fragment_root / "fragment-package.json").read_text(encoding="utf-8")
            )
            from .h1_readability import validate_failure_evidence

            validate_failure_evidence(
                readability_failure.data,
                report_text=report_text,
                fragment_texts={
                    item["id"]: item["text"]
                    for item in fragment_package_value["fragments"]
                },
            )
        except (H1ReadabilityError, OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_FAILURE_INVALID", str(error)
            ) from error
        if (
            request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("return_kind") != "local_revision"
            or request.data.get("calculated_owner") != "H1-A"
            or request.data.get("target_stage") != "H1"
            or request.data.get("resume_stage") != "H1"
            or request.data.get("resume_point") != "H1-A-plan"
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts")
            != ["plan", "fragments", "assembly", "html", "completion"]
            or request.data.get("invalidate_author_decision") is not False
            or request.data.get("invalidate_conception_completion") is not False
            or request.data.get("evidence_ids")
            != [readability_failure.data["review_id"]]
            or request.reference.get("path")
            != f"returns/{request.data.get('return_id', '')}/return-request.json"
            or canonical_sha256(request.data) != request.reference.get("sha256")
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_RETURN_ROUTE_INVALID",
                str(request.data.get("return_id", "")),
            )
        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            copy.deepcopy(latest.reference),
            active_return_request=None,
            runtime=context.store.runtime,
        )
        try:
            transition = fresh.apply_return_request(
                request=request,
                next_state_path=f"state/revision-{latest.data['revision'] + 1:03d}.json",
            )
        except CoordinatorError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        successor = _sealed(transition)
        session_id = f"H1-READABILITY-{canonical_sha256(request.reference)[:20]}"
        workspace_data = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "stage": "H1",
            "session_id": session_id,
            "state": "initialized",
            "p1_completion": copy.deepcopy(
                successor.data["current_stage_completions"]["P1"]
            ),
            "previous_state_sha256": None,
            "artifacts": {},
        }
        initialized = SealedDocument(
            data=workspace_data,
            reference={
                "path": f"H1/{session_id}/workspace-initialized.json",
                "sha256": canonical_sha256(workspace_data),
            },
        )
        gate = fresh.build_input_gate(
            "H1",
            f"orchestration/input-gates/revision-{successor.data['revision']:03d}-H1-A-plan/input-gate.json",
            active_return_request=request,
        )
        p1_root = context.store.resolve_completion_package_root(
            successor.data["current_stage_completions"]["P1"], expected_stage="P1"
        )
        authoritative_inputs = {"p1_package": str(p1_root)}
        order_body = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "action": "H1-A-plan",
            "state": dict(successor.reference),
            "input_gate": dict(gate.reference),
            "h1_workspace": dict(initialized.reference),
            "required_actor": ACTION_CONTRACT["H1-A-plan"][1],
            "inputs": authoritative_inputs,
            "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        inventory = {
            "session_references": [],
            "work_order_references": [],
            "completion_references": [
                {"stage": "H1", "completion": dict(completion.reference)}
            ],
            "pending_work_order": None,
            "pending_commit_intent": None,
        }
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]["model_schema_version"]
            for stage in ("E1", "T1")
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256(
            [
                latest.reference,
                request.reference,
                qualification.data["new_contract_digest"],
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            ]
        )[:24]
        stale_identity = {
            "stage": "H1",
            "origin_action": "H1-publish",
            "resume_point": "H1-A-plan",
            "current_workspace": dict(rendered.reference),
            "initialized_workspace": dict(initialized.reference),
            "fragment_manifest": copy.deepcopy(artifacts["fragment_manifest"]),
            "readability_failure": dict(readability_failure.reference),
            "h1_completion": dict(completion.reference),
            "h1_manifest": dict(h1_manifest.reference),
            "h1_artifacts": copy.deepcopy(artifacts),
            "evidence_ids": list(request.data["evidence_ids"]),
        }
        post_documents = [
            {"data": copy.deepcopy(initialized.data), "reference": dict(initialized.reference)},
            {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
            {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
        ]
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": ["H1"],
            "production_versions": production_versions,
            **inventory,
            "transition_mode": "internal_h1_readability_return",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": "H1",
            "stale_identity": stale_identity,
            "production_contract": copy.deepcopy(CURRENT_CONCEPTION_PRODUCTION_CONTRACT),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": None,
            "post_upgrade_documents": post_documents,
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": copy.deepcopy(authoritative_inputs),
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.preflight_immutable_documents(
            (readability_failure, request, plan, successor, *derived, receipt)
        )
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
            complete_receipt=receipt,
        )
        context.store.persist_document(readability_failure)
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(plan, successor=successor)
    return (
        receipt,
        ProductionContext(context.store, fresh, successor, request),
        initialized,
        gate,
        order,
    )


def apply_internal_h1_html_readability_return(
    context: ProductionContext,
    *,
    readability_failure: SealedDocument,
    request: SealedDocument,
    actor: str,
) -> tuple[
    SealedDocument, ProductionContext, SealedDocument, SealedDocument,
    SealedDocument,
]:
    """Atomically retry only unreadable prepublish H1 HTML.

    A separate reviewer binds the exact rendered package that failed.  The
    transaction preserves the accepted plan, fragments, and assembly, rolls
    the H1 workspace pointer back to that exact assembled predecessor, replaces
    the broader active H1 return with a narrower H1-C return, and issues one
    fresh H1-C order.  No author decision or H1 completion may exist.
    """

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError("PROD_WORK_ACTOR_MISMATCH", actor)
    if context.active_return is None:
        raise ProductionOrchestratorError(
            "PROD_H1_HTML_READABILITY_RETURN_STATE_INVALID", "active return"
        )
    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        if (
            latest.data.get("status") != "revise"
            or latest.data.get("author_decision") is not None
            or latest.data.get("active_return") != context.active_return.reference
            or context.store.pending_work_order() is not None
            or "H1" in latest.data.get("current_stage_completions", {})
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_HTML_READABILITY_RETURN_STATE_INVALID", "prepublish H1"
            )
        qualification = _validate_current_contract_qualification(
            context.store,
            context.store.current_contract_upgrade(),
            scope="internal-h1-html-readability-return",
        )
        rendered = context.store.latest_workspace()
        artifacts = rendered.data.get("artifacts", {})
        if (
            rendered.data.get("state") != "rendered"
            or set(artifacts)
            != {"plan_manifest", "fragment_manifest", "assembly_manifest", "html_manifest"}
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_HTML_READABILITY_RETURN_BINDING_INVALID",
                "rendered workspace",
            )
        assembled_reference = {
            "path": (
                f"H1/{rendered.data.get('session_id', '')}/"
                "workspace-assembled.json"
            ),
            "sha256": rendered.data.get("previous_state_sha256"),
        }
        try:
            assembled = context.store.load_document(assembled_reference)
            plan_root = context.store.resolve_document_path(
                artifacts["plan_manifest"]
            ).parent
            fragment_root = context.store.resolve_document_path(
                artifacts["fragment_manifest"]
            ).parent
            assembly_root = context.store.resolve_document_path(
                artifacts["assembly_manifest"]
            ).parent
            html_root = context.store.resolve_document_path(
                artifacts["html_manifest"]
            ).parent
            review_inputs, producer_identities = h1_readability_prepublish_contract(
                plan_package=plan_root,
                fragment_package_root=fragment_root,
                assembly_package=assembly_root,
                html_package=html_root,
                rendered_workspace=rendered,
            )
            validate_h1_readability_review(
                readability_failure.data,
                expected_run_id=latest.data["run_id"],
                expected_session_id=rendered.data["session_id"],
                expected_phase="prepublish",
                inputs=review_inputs,
                producer_identities=producer_identities,
                expected_verdict="fail",
            )
            report_text = (assembly_root / "human-review-report.json").read_text(
                encoding="utf-8"
            )
            fragment_package_value = json.loads(
                (fragment_root / "fragment-package.json").read_text(encoding="utf-8")
            )
            from .h1_readability import validate_failure_evidence

            validate_failure_evidence(
                readability_failure.data,
                report_text=report_text,
                fragment_texts={
                    item["id"]: item["text"]
                    for item in fragment_package_value["fragments"]
                },
            )
        except (
            H1ReadabilityError,
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ProductionStoreError,
        ) as error:
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_FAILURE_INVALID", str(error)
            ) from error
        if (
            assembled.data.get("state") != "assembled"
            or assembled.data.get("run_id") != rendered.data.get("run_id")
            or assembled.data.get("session_id") != rendered.data.get("session_id")
            or assembled.data.get("p1_completion") != rendered.data.get("p1_completion")
            or rendered.data.get("previous_state_sha256")
            != assembled.reference.get("sha256")
            or assembled.data.get("artifacts")
            != {
                "plan_manifest": artifacts["plan_manifest"],
                "fragment_manifest": artifacts["fragment_manifest"],
                "assembly_manifest": artifacts["assembly_manifest"],
            }
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or request.data.get("return_kind") != "local_revision"
            or request.data.get("calculated_owner") != "H1-C"
            or request.data.get("target_stage") != "H1"
            or request.data.get("resume_stage") != "H1"
            or request.data.get("resume_point") != "H1-C"
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts") != ["html", "completion"]
            or request.data.get("invalidate_author_decision") is not False
            or request.data.get("invalidate_conception_completion") is not False
            or request.data.get("evidence_ids")
            != [readability_failure.data["review_id"]]
            or request.reference.get("path")
            != f"returns/{request.data.get('return_id', '')}/return-request.json"
            or canonical_sha256(request.data) != request.reference.get("sha256")
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_HTML_READABILITY_RETURN_ROUTE_INVALID",
                str(request.data.get("return_id", "")),
            )
        old = context.active_return
        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            copy.deepcopy(latest.reference),
            active_return_request=old,
            runtime=context.store.runtime,
        )
        try:
            transition = fresh.narrow_active_h1_return(
                request=request,
                next_state_path=f"state/revision-{latest.data['revision'] + 1:03d}.json",
            )
        except CoordinatorError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        successor = _sealed(transition)
        gate = fresh.build_input_gate(
            "H1",
            (
                "orchestration/input-gates/"
                f"revision-{successor.data['revision']:03d}-H1-C/input-gate.json"
            ),
            active_return_request=request,
        )
        authoritative_inputs = {"assembly_package": str(assembly_root)}
        order_body = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "action": "H1-C",
            "state": dict(successor.reference),
            "input_gate": dict(gate.reference),
            "h1_workspace": dict(assembled.reference),
            "required_actor": ACTION_CONTRACT["H1-C"][1],
            "inputs": authoritative_inputs,
            "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        inventory = {
            "session_references": [],
            "work_order_references": [],
            "completion_references": [],
            "pending_work_order": None,
            "pending_commit_intent": None,
        }
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]["model_schema_version"]
            for stage in ("E1", "T1")
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256(
            [
                latest.reference,
                request.reference,
                qualification.data["new_contract_digest"],
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            ]
        )[:24]
        stale_identity = {
            "stage": "H1",
            "origin_action": "H1-C",
            "resume_point": "H1-C",
            "current_workspace": dict(rendered.reference),
            "restored_workspace": dict(assembled.reference),
            "plan_manifest": copy.deepcopy(artifacts["plan_manifest"]),
            "fragment_manifest": copy.deepcopy(artifacts["fragment_manifest"]),
            "assembly_manifest": copy.deepcopy(artifacts["assembly_manifest"]),
            "html_manifest": copy.deepcopy(artifacts["html_manifest"]),
            "readability_failure": dict(readability_failure.reference),
            "evidence_ids": list(request.data["evidence_ids"]),
        }
        post_documents = [
            {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
            {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
        ]
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": ["H1"],
            "production_versions": production_versions,
            **inventory,
            "transition_mode": "internal_h1_html_readability_return",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": "H1",
            "stale_identity": stale_identity,
            "production_contract": copy.deepcopy(CURRENT_CONCEPTION_PRODUCTION_CONTRACT),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": dict(old.reference),
            "post_upgrade_documents": post_documents,
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": copy.deepcopy(authoritative_inputs),
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.preflight_immutable_documents(
            (readability_failure, request, plan, successor, *derived, receipt)
        )
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
            complete_receipt=receipt,
        )
        context.store.persist_document(readability_failure)
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(plan, successor=successor)
    return (
        receipt,
        ProductionContext(context.store, fresh, successor, request),
        assembled,
        gate,
        order,
    )


def _h1_refresh_artifact(
    store: ProductionRunStore,
    *,
    manifest: SealedDocument,
    reference: Any,
) -> tuple[Path, dict[str, str]]:
    """Resolve one manifest-relative H1 artifact without scanning its package."""

    if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", str(reference)
        )
    logical = reference.get("path")
    digest = reference.get("sha256")
    if (
        not isinstance(logical, str)
        or not logical
        or "\\" in logical
        or not isinstance(digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", str(reference)
        )
    pure = PurePosixPath(logical)
    if pure.is_absolute() or pure.as_posix() != logical or ".." in pure.parts:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", logical
        )
    manifest_root = PurePosixPath(manifest.reference["path"]).parent
    if pure.parts[: len(manifest_root.parts)] == manifest_root.parts:
        relative = PurePosixPath(*pure.parts[len(manifest_root.parts) :])
    elif pure.parts and pure.parts[0] == manifest_root.parts[0]:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", f"parent mismatch: {logical}"
        )
    else:
        relative = pure
    if not relative.parts:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", logical
        )
    package_root = store.resolve_document_path(manifest.reference).parent
    candidate = package_root / Path(*relative.parts)
    try:
        resolved = store.resolve_physical_path(candidate)
        resolved.relative_to(store._without_windows_extended_prefix(package_root))
    except (ProductionStoreError, ValueError) as error:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", logical
        ) from error
    if (
        not store.physical_is_file(resolved)
        or store.physical_sha256(resolved) != digest
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", f"stale: {logical}"
        )
    return resolved, {
        "path": (manifest_root / relative).as_posix(),
        "sha256": digest,
    }


def _h1_implementation_refresh_material(
    context: ProductionContext,
    *,
    pending: SealedDocument,
    workspace: SealedDocument,
) -> tuple[SealedDocument, tuple[SealedDocument, ...]]:
    """Build the exact stale-implementation evidence for one H1 re-plan."""

    artifacts = workspace.data.get("artifacts", {})
    if (
        workspace.data.get("state") != "fragments_ready"
        or artifacts.keys() != {"plan_manifest", "fragment_manifest"}
        or pending.data.get("action") != "H1-A-assemble"
        or pending.data.get("h1_workspace") != workspace.reference
    ):
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_STATE_INVALID", "fragments_ready"
        )
    try:
        plan_manifest = context.store.load_document(artifacts["plan_manifest"])
        fragment_manifest = context.store.load_document(artifacts["fragment_manifest"])
    except ProductionStoreError as error:
        raise ProductionOrchestratorError(error.code, str(error)) from error
    implementation = plan_manifest.data.get("implementation")
    if not isinstance(implementation, list):
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", "plan implementation"
        )
    sealed_by_path: dict[str, dict[str, str]] = {}
    for reference in implementation:
        _physical, normalized = _h1_refresh_artifact(
            context.store, manifest=plan_manifest, reference=reference
        )
        relative = PurePosixPath(normalized["path"]).relative_to(
            PurePosixPath(plan_manifest.reference["path"]).parent
        ).as_posix()
        if relative in sealed_by_path:
            raise ProductionOrchestratorError(
                "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", f"duplicate: {relative}"
            )
        sealed_by_path[relative] = normalized
    module = importlib.import_module(
        "skills.novel-conception-human-review-assembler.scripts.run_v2"
    )
    current_paths = module._implementation_paths()
    expected_paths = {f"implementation/{identity}" for identity in current_paths}
    if set(sealed_by_path) != expected_paths:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", "implementation catalog"
        )
    stale: list[dict[str, Any]] = []
    for identity, source in sorted(current_paths.items()):
        relative = f"implementation/{identity}"
        current_sha = sha256_file(Path(source))
        sealed = sealed_by_path[relative]
        if sealed["sha256"] != current_sha:
            stale.append(
                {
                    "identity": identity,
                    "sealed_artifact": sealed,
                    "current_sha256": current_sha,
                }
            )
    if not stale:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_NOT_REQUIRED", pending.data["work_id"]
        )
    sessions: list[SealedDocument] = []
    for manifest in (plan_manifest, fragment_manifest):
        role = manifest.data.get("artifact_roles", {}).get("generation_session")
        _physical, normalized = _h1_refresh_artifact(
            context.store, manifest=manifest, reference=role
        )
        sessions.append(context.store.load_document(normalized))
    failure_id = "H1-IMPLEMENTATION-" + canonical_sha256(
        [
            context.state.reference,
            pending.reference,
            workspace.reference,
            plan_manifest.reference,
            fragment_manifest.reference,
            stale,
        ]
    )[:24]
    body = {
        "schema_version": "1.0",
        "failure_id": failure_id,
        "run_id": context.state.data["run_id"],
        "stage": "H1",
        "action": "H1-A-assemble",
        "code": "H1A_IMPLEMENTATION_STALE",
        "state": dict(context.state.reference),
        "active_return": dict(context.active_return.reference),
        "pending_work_order": dict(pending.reference),
        "current_workspace": dict(workspace.reference),
        "plan_manifest": dict(plan_manifest.reference),
        "fragment_manifest": dict(fragment_manifest.reference),
        "stale_implementations": stale,
        "status": "fail",
    }
    failure = SealedDocument(
        data=body,
        reference={
            "path": f"reviews/h1-implementation-stale/{failure_id}.json",
            "sha256": canonical_sha256(body),
        },
    )
    return failure, tuple(sessions)


def build_h1_implementation_refresh(
    context: ProductionContext,
) -> tuple[SealedDocument, SealedDocument]:
    """Purely derive the sealed failure and same-owner H1 refresh request."""

    pending = context.store.pending_work_order()
    workspace = context.store.latest_workspace()
    if context.active_return is None or pending is None:
        raise ProductionOrchestratorError(
            "PROD_H1_IMPLEMENTATION_REFRESH_STATE_INVALID", "active return/order"
        )
    failure, _sessions = _h1_implementation_refresh_material(
        context, pending=pending, workspace=workspace
    )
    body = route_return(
        run_id=context.state.data["run_id"],
        return_id=f"RET-H1-H1-A-IMPLEMENTATION-{failure.data['failure_id'][-24:]}",
        origin_kind="stage",
        origin_stage="H1",
        issue_kind="h1_plan",
        problem="The sealed H1-A implementation no longer matches the current runtime.",
        evidence_ids=[failure.data["failure_id"]],
        violated_contract="H1 packages must replay against the exact current implementation.",
        required_revision="Re-plan H1 with the accepted content and current implementation snapshot.",
        author_decision=None,
        has_current_author_decision=False,
        has_current_conception_completion=False,
    )
    request = SealedDocument(
        data=body,
        reference={
            "path": f"returns/{body['return_id']}/return-request.json",
            "sha256": canonical_sha256(body),
        },
    )
    return failure, request


def apply_active_return_escalation(
    context: ProductionContext,
    *,
    request: SealedDocument,
    actor: str,
    inputs: Mapping[str, Any],
) -> tuple[SealedDocument, ProductionContext, SealedDocument, SealedDocument]:
    """Atomically replace an active return with a strictly earlier owner."""

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError("PROD_WORK_ACTOR_MISMATCH", actor)
    if context.active_return is None:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_ACTIVE_RETURN_MISMATCH", "missing active return"
        )
    if "_contract_qualification" in inputs:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_RESERVED",
            request.data.get("target_stage", "escalation"),
        )
    old = context.active_return
    if (
        request.data.get("origin_kind") != "stage"
        or request.data.get("origin_stage") != old.data.get("resume_stage")
        or request.data.get("target_stage") not in STAGE_ORDER
        or request.data.get("resume_stage") != request.data.get("target_stage")
    ):
        raise ProductionOrchestratorError(
            "PROD_ACTIVE_RETURN_ESCALATION_INVALID", request.data.get("return_id", "")
        )
    old_index = STAGE_ORDER.index(old.data["resume_stage"])
    new_index = STAGE_ORDER.index(request.data["resume_stage"])
    if new_index >= old_index:
        raise ProductionOrchestratorError(
            "PROD_ACTIVE_RETURN_ESCALATION_NOT_EARLIER", request.data["resume_stage"]
        )
    expected_suffix = list(STAGE_ORDER[new_index:])
    if request.data.get("invalidated_stages") != expected_suffix:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_SUFFIX_INVALID", request.data["resume_stage"]
        )

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        qualification = context.store.current_contract_upgrade()
        if qualification is None:
            raise ProductionOrchestratorError(
                "PROD_CONTRACT_QUALIFICATION_STALE", "escalation"
            )
        context.store.trusted_contract_upgrade_markers()
        stale_contract_escalation = (
            qualification.data.get("new_contract_digest")
            != CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256
        )
        if stale_contract_escalation:
            actual_target, stale_identity = _actual_contract_upgrade_target(
                context.store, latest, qualification
            )
            if actual_target != request.data["target_stage"]:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_UPGRADE_TARGET_MISMATCH",
                    f"expected {actual_target}, observed {request.data['target_stage']}",
                )
        else:
            qualification = _validate_current_contract_qualification(
                context.store, qualification, scope="escalation"
            )
            stale_identity = {
                "stage": request.data["target_stage"],
                "superseded_return": dict(old.reference),
                "evidence_ids": list(request.data["evidence_ids"]),
            }
        pending = context.store.pending_work_order()
        old_action = old.data.get("resume_point")
        if (
            pending is None
            or old_action not in ACTION_CONTRACT
            or pending.data.get("action") != old_action
            or pending.data.get("run_id") != latest.data.get("run_id")
            or pending.data.get("state") != latest.reference
            or pending.data.get("required_actor")
            != ACTION_CONTRACT[old_action][1]
            or pending.data.get("status") != "pending"
            or not isinstance(pending.data.get("input_gate"), Mapping)
        ):
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_RETURN_ESCALATION_PENDING_ORDER_INVALID",
                old.data["resume_stage"],
            )
        try:
            pending_gate = context.store.load_document(pending.data["input_gate"])
            expected_pending_gate = context.coordinator.build_input_gate(
                old.data["resume_stage"],
                pending_gate.reference["path"],
                active_return_request=old,
            )
        except (ProductionStoreError, CoordinatorError) as error:
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_RETURN_ESCALATION_PENDING_GATE_INVALID", str(error)
            ) from error
        if pending_gate != expected_pending_gate:
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_RETURN_ESCALATION_PENDING_GATE_INVALID",
                pending.data["work_id"],
            )
        pending_intent = context.store._load_commit_intent(pending)
        trusted = context.store.trusted_contract_upgrade_markers()
        completed_session_ids: set[str] = set()
        for completion_path in context.store.root.rglob("stage-completion.json"):
            try:
                value = json.loads(completion_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(value.get("session_id"), str):
                completed_session_ids.add(value["session_id"])
        sessions: list[dict[str, str]] = []
        for path in sorted(context.store.root.rglob("generation-session.json")):
            relative = path.relative_to(context.store.root).as_posix()
            if relative.startswith("orchestration/"):
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except Exception as error:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_SESSION_INVALID", f"{relative}: {error}"
                ) from error
            reference = {"path": relative, "sha256": sha256_file(path)}
            if (
                value.get("stage") in expected_suffix
                and value.get("session_id") not in completed_session_ids
                and (reference["path"], reference["sha256"])
                not in trusted["invalidated_sessions"]
            ):
                sessions.append(reference)
        completions = [
            {"stage": stage, "completion": dict(reference)}
            for stage, reference in latest.data["current_stage_completions"].items()
            if stage in expected_suffix
        ]
        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data), latest.reference,
            active_return_request=old, runtime=context.store.runtime,
        )
        transition = fresh.supersede_active_return(
            request=request,
            next_state_path=f"state/revision-{latest.data['revision'] + 1:03d}.json",
        )
        successor = _sealed(transition)
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                "model_schema_version"
            ]
            for stage in ("E1", "T1")
        }
        inventory = {
            "session_references": sessions,
            "work_order_references": [dict(pending.reference)],
            "completion_references": completions,
            "pending_work_order": dict(pending.reference),
            "pending_commit_intent": (
                dict(pending_intent.reference) if pending_intent else None
            ),
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256([
            latest.reference, request.reference,
            qualification.data["new_contract_digest"],
            CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        ])[:24]
        qualified_inputs = copy.deepcopy(dict(inputs))
        contract_qualification = _escalation_contract_qualification_payload(
            qualification, action=request.data["resume_stage"]
        )
        if contract_qualification is not None:
            qualified_inputs["_contract_qualification"] = contract_qualification
        gate = fresh.build_input_gate(
            request.data["resume_stage"],
            f"orchestration/input-gates/revision-{successor.data['revision']:03d}-{request.data['resume_stage']}/input-gate.json",
            active_return_request=request,
        )
        order_body = {
            "schema_version": "2.0", "run_id": successor.data["run_id"],
            "action": request.data["resume_stage"], "state": dict(successor.reference),
            "input_gate": dict(gate.reference), "h1_workspace": None,
            "required_actor": ACTION_CONTRACT[request.data["resume_stage"]][1],
            "inputs": qualified_inputs, "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        post_documents = [
            {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
            {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
        ]
        plan_body = {
            "schema_version": "1.0", "migration_id": migration_id,
            "reason": "contract_upgrade", "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": expected_suffix,
            "production_versions": dict(production_versions), **inventory,
            "transition_mode": "active_return_escalation",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": request.data["target_stage"],
            "stale_identity": copy.deepcopy(stale_identity),
            "production_contract": copy.deepcopy(CURRENT_CONCEPTION_PRODUCTION_CONTRACT),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": dict(old.reference),
            "post_upgrade_documents": post_documents,
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": copy.deepcopy(dict(inputs)),
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        context.store.preflight_contract_upgrade_transaction(
            request=request, plan=plan, successor=successor,
            complete_receipt=receipt,
        )
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(plan, successor=successor)
    escalated = ProductionContext(context.store, fresh, successor, request)
    return receipt, escalated, gate, order


def refresh_active_stage_return(
    context: ProductionContext,
    *,
    request: SealedDocument,
    actor: str,
    inputs: Mapping[str, Any],
    implementation_failure: SealedDocument | None = None,
) -> tuple[SealedDocument, ProductionContext, SealedDocument, SealedDocument]:
    """Atomically replace one active stage return with fresh same-owner work."""

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError("PROD_WORK_ACTOR_MISMATCH", actor)
    if context.active_return is None:
        raise ProductionOrchestratorError(
            "PROD_ACTIVE_STAGE_RETURN_REQUIRED", "missing active return"
        )
    if "_contract_qualification" in inputs:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_QUALIFICATION_RESERVED",
            str(request.data.get("target_stage", "stage-refresh")),
        )
    old = context.active_return
    old_stage = old.data.get("resume_stage")
    h1_implementation_refresh = implementation_failure is not None
    if (
        request.data.get("origin_kind") != "stage"
        or request.data.get("origin_stage") != old_stage
        or request.data.get("target_stage") != old_stage
        or request.data.get("resume_stage") != old_stage
        or request.data.get("resume_point") != old.data.get("resume_point")
        or request.reference == old.reference
        or request.data.get("return_id") == old.data.get("return_id")
    ):
        raise ProductionOrchestratorError(
            "PROD_ACTIVE_STAGE_RETURN_ROUTE_INVALID",
            str(request.data.get("return_id", "")),
        )
    if old_stage not in STAGE_ORDER:
        raise ProductionOrchestratorError(
            "PROD_ACTIVE_STAGE_RETURN_ROUTE_INVALID", str(old_stage)
        )
    expected_suffix = list(STAGE_ORDER[STAGE_ORDER.index(str(old_stage)) :])
    if request.data.get("invalidated_stages") != expected_suffix:
        raise ProductionOrchestratorError(
            "PROD_CONTRACT_UPGRADE_SUFFIX_INVALID", str(old_stage)
        )

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        qualification = _validate_current_contract_qualification(
            context.store,
            context.store.current_contract_upgrade(),
            scope="active-stage-return-refresh",
        )
        if latest.data.get("active_return") != old.reference:
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_STAGE_RETURN_MISMATCH", str(old_stage)
            )
        pending = context.store.pending_work_order()
        old_action = old.data.get("resume_point")
        contract = ACTION_CONTRACT.get(str(old_action))
        expected_pending_action = old_action
        if h1_implementation_refresh:
            if old_stage != "H1" or old_action != "H1-A-plan":
                raise ProductionOrchestratorError(
                    "PROD_H1_IMPLEMENTATION_REFRESH_STATE_INVALID",
                    str(old_action),
                )
            expected_pending_action = "H1-A-assemble"
        if (
            pending is None
            or contract is None
            or contract[0] != old_stage
            or pending.data.get("action") != expected_pending_action
            or pending.data.get("run_id") != latest.data.get("run_id")
            or pending.data.get("state") != latest.reference
            or pending.data.get("required_actor") != contract[1]
            or pending.data.get("status") != "pending"
            or not isinstance(pending.data.get("input_gate"), Mapping)
        ):
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_STAGE_RETURN_PENDING_ORDER_INVALID", str(old_stage)
            )
        try:
            pending_gate = context.store.load_document(pending.data["input_gate"])
            expected_pending_gate = context.coordinator.build_input_gate(
                str(old_stage),
                pending_gate.reference["path"],
                active_return_request=old,
            )
        except (ProductionStoreError, CoordinatorError) as error:
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_STAGE_RETURN_PENDING_GATE_INVALID", str(error)
            ) from error
        if pending_gate != expected_pending_gate:
            raise ProductionOrchestratorError(
                "PROD_ACTIVE_STAGE_RETURN_PENDING_GATE_INVALID",
                str(pending.data.get("work_id")),
            )

        pending_intent = context.store._load_commit_intent(pending)
        h1_workspace = None
        h1_sessions: tuple[SealedDocument, ...] = ()
        if h1_implementation_refresh:
            h1_workspace = context.store.latest_workspace()
            expected_failure, h1_sessions = _h1_implementation_refresh_material(
                context, pending=pending, workspace=h1_workspace
            )
            if implementation_failure != expected_failure:
                raise ProductionOrchestratorError(
                    "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", "failure evidence"
                )
            if request.data.get("evidence_ids") != [
                implementation_failure.data["failure_id"]
            ]:
                raise ProductionOrchestratorError(
                    "PROD_H1_IMPLEMENTATION_REFRESH_INVALID", "request evidence"
                )
        trusted = context.store.trusted_contract_upgrade_markers()
        completed_session_ids: set[str] = set()
        for completion_path in context.store.root.rglob("stage-completion.json"):
            try:
                value = json.loads(completion_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(value.get("session_id"), str):
                completed_session_ids.add(value["session_id"])
        sessions: list[dict[str, str]] = []
        for path in sorted(context.store.root.rglob("generation-session.json")):
            relative = path.relative_to(context.store.root).as_posix()
            if relative.startswith("orchestration/"):
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except Exception as error:
                raise ProductionOrchestratorError(
                    "PROD_CONTRACT_SESSION_INVALID", f"{relative}: {error}"
                ) from error
            reference = {"path": relative, "sha256": sha256_file(path)}
            if (
                value.get("stage") in expected_suffix
                and value.get("session_id") not in completed_session_ids
                and (reference["path"], reference["sha256"])
                not in trusted["invalidated_sessions"]
            ):
                sessions.append(reference)
        if h1_implementation_refresh:
            sessions = [dict(item.reference) for item in h1_sessions]
        completions = [
            {"stage": stage, "completion": dict(reference)}
            for stage, reference in latest.data["current_stage_completions"].items()
            if stage in expected_suffix
        ]

        fresh = ProductionCoordinator.from_snapshot(
            copy.deepcopy(latest.data),
            latest.reference,
            active_return_request=old,
            runtime=context.store.runtime,
        )
        try:
            transition = fresh.refresh_active_stage_return(
                request=request,
                next_state_path=(
                    f"state/revision-{latest.data['revision'] + 1:03d}.json"
                ),
            )
        except CoordinatorError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        successor = _sealed(transition)
        refreshed_context = ProductionContext(
            context.store, fresh, successor, request
        )
        initialized = None
        if h1_implementation_refresh:
            session_id = "H1-IMPLEMENTATION-" + canonical_sha256(
                [
                    successor.reference,
                    implementation_failure.reference,
                    request.reference,
                ]
            )[:20]
            initialized_data = {
                "schema_version": "2.0",
                "run_id": successor.data["run_id"],
                "stage": "H1",
                "session_id": session_id,
                "state": "initialized",
                "p1_completion": copy.deepcopy(
                    successor.data["current_stage_completions"]["P1"]
                ),
                "previous_state_sha256": None,
                "artifacts": {},
            }
            initialized = SealedDocument(
                data=initialized_data,
                reference={
                    "path": f"H1/{session_id}/workspace-initialized.json",
                    "sha256": canonical_sha256(initialized_data),
                },
            )
        target_action = str(request.data["resume_point"])
        gate = fresh.build_input_gate(
            str(old_stage),
            (
                "orchestration/input-gates/"
                f"revision-{successor.data['revision']:03d}-{target_action}/"
                "input-gate.json"
            ),
            active_return_request=request,
        )
        raw_inputs = copy.deepcopy(dict(inputs))
        authoritative_inputs = _authoritative_package_inputs(
            refreshed_context, action=target_action, gate=gate
        )
        if h1_implementation_refresh:
            p1_root = context.store.resolve_completion_package_root(
                successor.data["current_stage_completions"]["P1"],
                expected_stage="P1",
            )
            authoritative_inputs = {"p1_package": str(p1_root)}
        for field, value in authoritative_inputs.items():
            observed = raw_inputs.get(field)
            if observed is not None and str(observed) != value:
                raise ProductionOrchestratorError("PROD_WORK_INPUT_OVERRIDE", field)
            raw_inputs[field] = value
        qualified_inputs = copy.deepcopy(raw_inputs)
        contract_qualification = _escalation_contract_qualification_payload(
            qualification, action=str(old_stage)
        )
        if contract_qualification is not None:
            qualified_inputs["_contract_qualification"] = contract_qualification
        order_body = {
            "schema_version": "2.0",
            "run_id": successor.data["run_id"],
            "action": target_action,
            "state": dict(successor.reference),
            "input_gate": dict(gate.reference),
            "h1_workspace": (
                dict(initialized.reference) if initialized is not None else None
            ),
            "required_actor": contract[1],
            "inputs": qualified_inputs,
            "status": "pending",
        }
        work_id = canonical_sha256(order_body)[:24]
        order = SealedDocument(
            data={**order_body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**order_body, "work_id": work_id}),
            },
        )
        post_documents = [
            {"data": copy.deepcopy(gate.data), "reference": dict(gate.reference)},
            {"data": copy.deepcopy(order.data), "reference": dict(order.reference)},
        ]
        if initialized is not None:
            post_documents.insert(
                0,
                {
                    "data": copy.deepcopy(initialized.data),
                    "reference": dict(initialized.reference),
                },
            )
        production_versions = {
            stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage][
                "model_schema_version"
            ]
            for stage in ("E1", "T1")
        }
        inventory = {
            "session_references": sessions,
            "work_order_references": [dict(pending.reference)],
            "completion_references": completions,
            "pending_work_order": dict(pending.reference),
            "pending_commit_intent": (
                dict(pending_intent.reference) if pending_intent else None
            ),
        }
        generation = qualification.data.get("refresh_generation", 0) + 1
        migration_id = canonical_sha256([
            latest.reference,
            request.reference,
            qualification.data["new_contract_digest"],
            CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
        ])[:24]
        stale_identity = {
            "stage": str(old_stage),
            "superseded_return": dict(old.reference),
            "evidence_ids": list(request.data["evidence_ids"]),
        }
        if h1_implementation_refresh:
            stale_identity.update(
                {
                    "origin_action": "H1-A-assemble",
                    "resume_point": "H1-A-plan",
                    "pending_work_order": dict(pending.reference),
                    "current_workspace": dict(h1_workspace.reference),
                    "initialized_workspace": dict(initialized.reference),
                    "plan_manifest": copy.deepcopy(
                        h1_workspace.data["artifacts"]["plan_manifest"]
                    ),
                    "fragment_manifest": copy.deepcopy(
                        h1_workspace.data["artifacts"]["fragment_manifest"]
                    ),
                    "implementation_failure": dict(
                        implementation_failure.reference
                    ),
                }
            )
        plan_body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "predecessor_state": dict(latest.reference),
            "successor_state": dict(successor.reference),
            "successor_snapshot": copy.deepcopy(successor.data),
            "return_request": dict(request.reference),
            "old_contract_digest": qualification.data["new_contract_digest"],
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": expected_suffix,
            "production_versions": production_versions,
            **inventory,
            "transition_mode": "active_stage_return_refresh",
            "refresh_generation": generation,
            "prior_qualification": dict(qualification.reference),
            "target_stage": str(old_stage),
            "stale_identity": stale_identity,
            "production_contract": copy.deepcopy(
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT
            ),
            "inventory_sha256": canonical_sha256(inventory),
            "superseded_return": dict(old.reference),
            "post_upgrade_documents": post_documents,
            "post_upgrade_work_order": dict(order.reference),
            "post_upgrade_inputs": raw_inputs,
            "status": "prepared",
        }
        plan = context.store.build_contract_upgrade_plan(plan_body)
        receipt, _derived = context.store.build_contract_upgrade_completion(
            plan, successor=successor
        )
        if implementation_failure is not None:
            context.store.preflight_immutable_documents((implementation_failure,))
        context.store.preflight_contract_upgrade_transaction(
            request=request,
            plan=plan,
            successor=successor,
            complete_receipt=receipt,
        )
        if implementation_failure is not None:
            context.store.persist_document(implementation_failure)
        context.store.persist_document(request)
        context.store.persist_document(plan)
        context.store.persist_state(successor)
        receipt = context.store.complete_contract_upgrade(
            plan, successor=successor
        )
    refreshed_context = ProductionContext(
        context.store, fresh, successor, request
    )
    return receipt, refreshed_context, gate, order


def apply_internal_h1_implementation_refresh(
    context: ProductionContext,
    *,
    actor: str,
) -> tuple[
    SealedDocument,
    ProductionContext,
    SealedDocument,
    SealedDocument,
    SealedDocument,
    SealedDocument,
]:
    """Re-plan an active H1 return after its sealed H1-A code goes stale."""

    if actor != "production-orchestrator":
        raise ProductionOrchestratorError(
            "PROD_WORK_ACTOR_MISMATCH", actor
        )
    failure, request = build_h1_implementation_refresh(context)
    receipt, refreshed, gate, order = refresh_active_stage_return(
        context,
        request=request,
        actor=actor,
        inputs={},
        implementation_failure=failure,
    )
    return receipt, refreshed, failure, request, gate, order


def initialize_h1_workspace(
    context: ProductionContext, *, session_id: str
) -> SealedDocument:
    """Create the deterministic H1 ``initialized`` workspace after current P1."""

    with context.store.lock():
        latest = context.store.latest_state()
        if latest.reference != context.state.reference:
            raise ProductionOrchestratorError(
                "PROD_CONTEXT_STALE", "reload before initializing H1"
            )
        current = latest.data["current_stage_completions"]
        if set(current) != set(STAGE_ORDER[:-1]) or len(current) != len(
            STAGE_ORDER[:-1]
        ):
            raise ProductionOrchestratorError(
                "PROD_ACTION_NOT_READY", "H1 initialization requires B0-P1"
            )
        try:
            prior = context.store.latest_workspace()
        except ProductionStoreError as error:
            if error.code != "PROD_H1_WORKSPACE_MISSING":
                raise
            prior = None
        if prior is not None:
            same_p1 = prior.data["p1_completion"] == current["P1"]
            if (
                same_p1
                and prior.data["state"] == "initialized"
                and prior.data["session_id"] == session_id
            ):
                return prior
            h1_return = (
                context.active_return is not None
                and context.active_return.data.get("resume_stage") == "H1"
            )
            if same_p1 and not (
                h1_return and prior.data["state"] == "rendered"
            ):
                raise ProductionOrchestratorError(
                    "PROD_H1_SESSION_EXISTS",
                    "resume the current H1 workspace instead of replacing it",
                )
            if same_p1 and prior.data["session_id"] == session_id:
                raise ProductionOrchestratorError(
                    "PROD_H1_SESSION_ID_REUSED",
                    "an H1 revision requires a new session_id",
                )
        data = {
            "schema_version": "2.0",
            "run_id": latest.data["run_id"],
            "stage": "H1",
            "session_id": session_id,
            "state": "initialized",
            "p1_completion": copy.deepcopy(current["P1"]),
            "previous_state_sha256": None,
            "artifacts": {},
        }
        workspace = SealedDocument(
            data=data,
            reference={
                "path": f"H1/{session_id}/workspace-initialized.json",
                "sha256": canonical_sha256(data),
            },
        )
        context.store.persist_workspace(workspace)
        return workspace


def execute_stage_work(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    actor: str,
    executor: Callable[..., Any],
    input_bindings: Mapping[str, Any] | None = None,
) -> tuple[Any, ProductionContext]:
    """Execute one existing stage runner and durably commit its transition.

    The callback is the only semantic seam.  It must call the stage's existing
    start/submit/run API and return a receipt exposing ``transition``.
    """

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        _require_work_actor(work_order, actor)
        action = str(work_order.data.get("action"))
        observed_qualification = work_order.data.get("inputs", {}).get(
            "_contract_qualification"
        )
        qualification_override = None
        escalation_qualification = None
        current_qualification = context.store.current_contract_upgrade()
        if (
            current_qualification is not None
            and current_qualification.data.get("transition_mode")
            in {
                "active_return_escalation",
                "active_stage_return_refresh",
                "stage_return",
            }
            and current_qualification.data.get("successor_state") == latest.reference
            and current_qualification.data.get("target_stage") == action
            and isinstance(observed_qualification, Mapping)
            and observed_qualification.get("contract_upgrade_receipt")
            == current_qualification.data.get("prior_qualification")
        ):
            _validate_current_contract_qualification(
                context.store, current_qualification, scope=action
            )
            escalation_qualification = context.store.load_document(
                current_qualification.data["prior_qualification"]
            )
        if escalation_qualification is not None:
            expected_qualification = _escalation_contract_qualification_payload(
                escalation_qualification, action=action
            )
        else:
            expected_qualification = _expected_contract_qualification(
                context, latest=latest, action=action,
                qualification_override=qualification_override,
            )
        if observed_qualification != expected_qualification:
            raise ProductionOrchestratorError(
                "PROD_WORK_CONTRACT_QUALIFICATION_INVALID",
                str(work_order.data.get("work_id")),
            )
        gate_ref = work_order.data.get("input_gate")
        if not isinstance(gate_ref, Mapping):
            raise ProductionOrchestratorError(
                "PROD_WORK_GATE_MISSING", str(work_order.data.get("work_id"))
            )
        gate = context.store.load_document(gate_ref)
        sealed_inputs = _sealed_executor_inputs(work_order)
        if input_bindings is not None and canonical_sha256(dict(input_bindings)) != canonical_sha256(
            sealed_inputs
        ):
            raise ProductionOrchestratorError(
                "PROD_EXECUTOR_INPUT_BINDINGS_MISMATCH",
                str(work_order.data.get("work_id")),
            )
        if input_bindings is None:
            receipt = executor(context.coordinator, gate)
        else:
            receipt = executor(context.coordinator, gate, copy.deepcopy(sealed_inputs))
        transition = getattr(receipt, "transition", None)
        completion = getattr(receipt, "completion", None)
        if not isinstance(transition, StateTransition):
            raise ProductionOrchestratorError(
                "PROD_STAGE_RECEIPT_INVALID", "executor returned no StateTransition"
            )
        if not isinstance(completion, SealedDocument):
            raise ProductionOrchestratorError(
                "PROD_STAGE_RECEIPT_INVALID", "executor returned no completion"
            )
        successor = _sealed(transition)
        _prepare_state_commit(context, work_order, successor, completion)
        context.store.persist_state(successor)
        context.store.mark_work_order_consumed(work_order, successor=successor)
    return receipt, ProductionContext(
        context.store, context.coordinator, successor, None
    )


def recover_stage_admission(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    actor: str,
    completion: SealedDocument,
) -> ProductionContext:
    """Admit a validator-proven package orphan after a worker crash.

    The caller must first run the owning skill's public package validator and
    seal its persisted ``stage-completion.json``.  No package is repaired.
    """

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        _require_work_actor(work_order, actor)
        gate = context.store.load_document(work_order.data["input_gate"])
        transition = context.coordinator.accept_stage_completion(
            gate=gate,
            completion=completion,
            next_state_path=(
                f"state/revision-{context.state.data['revision'] + 1:03d}.json"
            ),
            active_return_request=context.active_return,
        )
        successor = _sealed(transition)
        _prepare_state_commit(context, work_order, successor, completion)
        context.store.persist_state(successor)
        context.store.mark_work_order_consumed(work_order, successor=successor)
    return ProductionContext(
        context.store, context.coordinator, successor, None
    )


def commit_h1_workspace(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    actor: str,
    executor: Callable[[AutonomousCoordinator, SealedDocument], Any],
) -> tuple[Any, SealedDocument]:
    """Commit one H1-A/B/C package and its durable internal workspace."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        _require_work_actor(work_order, actor)
        bound = _bound_h1_workspace(context, work_order)
        gate = context.store.load_document(work_order.data["input_gate"])
        receipt = executor(context.coordinator, gate)
        transition = getattr(receipt, "transition", None)
        if not isinstance(transition, H1WorkspaceTransition):
            raise ProductionOrchestratorError(
                "PROD_H1_RECEIPT_INVALID", "executor returned no H1 workspace"
            )
        workspace = transition.workspace
        action = work_order.data["action"]
        expected = H1_ACTION_STATES.get(action)
        if expected is None or expected[1] != workspace.data["state"]:
            raise ProductionOrchestratorError(
                "PROD_H1_ACTION_MISMATCH", str(action)
            )
        if (
            workspace.data.get("previous_state_sha256")
            != bound.reference["sha256"]
            or workspace.data.get("session_id") != bound.data.get("session_id")
            or workspace.data.get("p1_completion")
            != bound.data.get("p1_completion")
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_WORKSPACE_STALE", str(action)
            )
        manifest_data = getattr(receipt, "manifest", None)
        added = set(workspace.data["artifacts"]) - set(bound.data["artifacts"])
        if not isinstance(manifest_data, Mapping) or len(added) != 1:
            raise ProductionOrchestratorError(
                "PROD_H1_RECEIPT_INVALID", "executor returned no exact manifest"
            )
        manifest_reference = workspace.data["artifacts"][added.pop()]
        manifest = SealedDocument(
            data=copy.deepcopy(dict(manifest_data)),
            reference=copy.deepcopy(dict(manifest_reference)),
        )
        _prepare_h1_commit(
            context,
            work_order,
            bound=bound,
            successor=workspace,
            manifest=manifest,
        )
        context.store.persist_workspace(workspace)
        context.store.mark_work_order_consumed(work_order, successor=workspace)
        return receipt, workspace


def recover_h1_workspace(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    actor: str,
    current_workspace: SealedDocument,
    package_manifest: SealedDocument,
    expected_next_state: str,
) -> SealedDocument:
    """Reconstruct one validated H1 package orphan without regenerating it."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        _require_work_actor(work_order, actor)
        bound = _bound_h1_workspace(context, work_order)
        if (
            current_workspace.reference != bound.reference
            or current_workspace.data != bound.data
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_WORKSPACE_STALE", str(work_order.data.get("action"))
            )
        transition = context.coordinator.accept_h1_workspace_transition(
            current_workspace=current_workspace,
            package_manifest=package_manifest,
            expected_next_state=expected_next_state,
            active_return_request=context.active_return,
        )
        workspace = transition.workspace
        action = work_order.data["action"]
        expected = H1_ACTION_STATES.get(action)
        if expected is None or expected[1] != workspace.data["state"]:
            raise ProductionOrchestratorError(
                "PROD_H1_ACTION_MISMATCH", str(action)
            )
        _prepare_h1_commit(
            context,
            work_order,
            bound=bound,
            successor=workspace,
            manifest=package_manifest,
        )
        context.store.persist_workspace(workspace)
        context.store.mark_work_order_consumed(work_order, successor=workspace)
        return workspace


def publish_h1_transaction(
    context: ProductionContext,
    output_root: str | Path,
    *,
    work_order: SealedDocument,
    **arguments: Any,
) -> tuple[H1CompletionReceipt, ProductionContext]:
    """Publish H1 and persist ``waiting_author`` before accepting a decision."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        if work_order.data["action"] != "H1-publish":
            raise ProductionOrchestratorError("PROD_ACTION_MISMATCH", "H1-publish")
        logical_package_path = arguments.get(
            "logical_package_path", "H1/stage"
        )
        try:
            expected_output = context.store._path(logical_package_path)
            actual_output = context.store.resolve_physical_path(output_root)
        except ProductionStoreError as error:
            raise ProductionOrchestratorError(error.code, str(error)) from error
        if actual_output != expected_output:
            raise ProductionOrchestratorError(
                "PROD_H1_OUTPUT_PATH_MISMATCH", str(logical_package_path)
            )
        bound = _bound_h1_workspace(context, work_order)
        rendered = arguments.get("rendered_workspace")
        if (
            not isinstance(rendered, SealedDocument)
            or rendered.reference != bound.reference
            or rendered.data != bound.data
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_WORKSPACE_STALE", "H1-publish"
            )
        admission_input_gate = context.store.load_document(
            work_order.data["input_gate"]
        )
        supplied_admission_gate = arguments.pop(
            "admission_input_gate", None
        )
        if supplied_admission_gate is not None and (
            not isinstance(supplied_admission_gate, SealedDocument)
            or supplied_admission_gate.reference
            != admission_input_gate.reference
            or supplied_admission_gate.data != admission_input_gate.data
        ):
            raise ProductionOrchestratorError(
                "PROD_H1_ADMISSION_GATE_MISMATCH", "H1-publish"
            )
        readability_review = arguments.get("human_readability_review")
        if not isinstance(readability_review, SealedDocument):
            raise ProductionOrchestratorError(
                "PROD_H1_READABILITY_REVIEW_REQUIRED", "H1-publish"
            )
        try:
            persisted_review = context.store.load_document(
                readability_review.reference
            )
            if persisted_review.data != readability_review.data:
                raise ProductionOrchestratorError(
                    "PROD_H1_READABILITY_REVIEW_STALE",
                    readability_review.data.get("review_id", ""),
                )
            readability_inputs, producer_identities = (
                h1_readability_prepublish_contract(
                    plan_package=arguments["plan_package"],
                    fragment_package_root=arguments["fragment_package"],
                    assembly_package=arguments["assembly_package"],
                    html_package=arguments["html_package"],
                    rendered_workspace=rendered,
                )
            )
            validate_h1_readability_review(
                readability_review.data,
                expected_run_id=rendered.data["run_id"],
                expected_session_id=rendered.data["session_id"],
                expected_phase="prepublish",
                inputs=readability_inputs,
                producer_identities=producer_identities,
                expected_verdict="pass",
            )
        except (ProductionStoreError, H1ReadabilityError, KeyError) as error:
            code = getattr(error, "code", "PROD_H1_READABILITY_REVIEW_INVALID")
            raise ProductionOrchestratorError(code, str(error)) from error
        receipt = publish_h1_completion(
            output_root,
            coordinator=context.coordinator,
            next_state_path=(
                f"state/revision-{context.state.data['revision'] + 1:03d}.json"
            ),
            active_return_request=context.active_return,
            admission_input_gate=admission_input_gate,
            runtime=context.store.runtime,
            **arguments,
        )
        successor = _sealed(receipt.transition)
        _prepare_state_commit(
            context, work_order, successor, receipt.completion
        )
        context.store.persist_state(successor)
        context.store.mark_work_order_consumed(work_order, successor=successor)
    return receipt, ProductionContext(
        context.store, context.coordinator, successor, None
    )


def record_author_transaction(
    context: ProductionContext,
    *,
    work_order: SealedDocument,
    event: SealedDocument,
    **arguments: Any,
) -> tuple[AuthorDecisionReceipt, ProductionContext]:
    """Consume an external event and persist return body before revise state."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        if work_order.data["action"] != "author-decision":
            raise ProductionOrchestratorError(
                "PROD_ACTION_MISMATCH", "author-decision"
            )
        receipt = record_author_decision(
            event=event,
            coordinator=context.coordinator,
            next_state_path=(
                f"state/revision-{context.state.data['revision'] + 1:03d}.json"
            ),
            runtime=context.store.runtime,
            **arguments,
        )
        if receipt.return_request is not None:
            context.store.persist_document(receipt.return_request)
        successor = _sealed(receipt.transition)
        _prepare_state_commit(
            context,
            work_order,
            successor,
            receipt.decision,
            return_request=receipt.return_request,
        )
        context.store.persist_state(successor)
        context.store.mark_work_order_consumed(work_order, successor=successor)
    return receipt, ProductionContext(
        context.store,
        context.coordinator,
        successor,
        receipt.return_request,
    )


def publish_final_transaction(
    context: ProductionContext,
    output_root: str | Path,
    *,
    work_order: SealedDocument,
    **arguments: Any,
) -> tuple[FinalCompletionReceipt, ProductionContext]:
    """Publish/recover final completion and durably grant admission."""

    with context.store.lock():
        latest = context.store.latest_state()
        _require_context_current(context, latest)
        context.store.require_current_work_order(work_order, state=latest)
        if work_order.data["action"] != "final":
            raise ProductionOrchestratorError("PROD_ACTION_MISMATCH", "final")
        receipt = publish_final_completion(
            output_root,
            coordinator=context.coordinator,
            next_state_path=(
                f"state/revision-{context.state.data['revision'] + 1:03d}.json"
            ),
            runtime=context.store.runtime,
            **arguments,
        )
        successor = _sealed(receipt.transition)
        _prepare_state_commit(
            context, work_order, successor, receipt.completion
        )
        context.store.persist_state(successor)
        context.store.mark_work_order_consumed(work_order, successor=successor)
    return receipt, ProductionContext(
        context.store, context.coordinator, successor, None
    )


__all__ = [
    "ProductionContext",
    "ProductionOrchestratorError",
    "ACTION_CONTRACT",
    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT",
    "CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256",
    "H1_ACTION_STATES",
    "commit_h1_workspace",
    "apply_active_return_escalation",
    "apply_contract_upgrade",
    "apply_internal_h1_implementation_refresh",
    "apply_internal_h1_fragment_return",
    "apply_internal_h1_readability_return",
    "apply_internal_h1_html_readability_return",
    "apply_stage_return",
    "build_h1_implementation_refresh",
    "refresh_active_stage_return",
    "execute_stage_work",
    "initialize_production_run",
    "initialize_h1_workspace",
    "issue_stage_work",
    "publish_final_transaction",
    "publish_h1_transaction",
    "recover_h1_workspace",
    "recover_stage_admission",
    "record_author_transaction",
    "resume_production_run",
    "resume_production_run_for_contract_upgrade",
]
