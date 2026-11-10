"""Immutable run-state coordinator for autonomous novel-conception V2.

This module owns orchestration facts only.  It never generates domain content,
never treats a checkpoint as completion, and never infers an active return from
an artifact reference without receiving and validating the referenced body.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import (
    ManifestIntegrityError,
    canonical_sha256,
    resolve_artifact_path,
)
from .contracts import ContractRuntime, ContractValidationError
from .return_routing import (
    ReturnRoutingError,
    STAGE_ORDER,
    RouteSpec,
    validate_return_request,
)


UPSTREAM_TOPOLOGY: dict[str, tuple[str, ...]] = {
    "B0": (),
    "S1": (),
    "W1": ("S1",),
    "E1": ("S1", "W1"),
    "T1": ("S1", "W1", "E1"),
    "C1": ("S1", "W1", "E1", "T1"),
    "Q1": ("S1", "W1", "E1", "T1", "C1"),
    "P1": ("S1", "W1", "E1", "T1", "C1", "Q1"),
    "H1": ("P1",),
}


class CoordinatorError(ValueError):
    """A stable, fail-closed coordinator error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class SealedDocument:
    """An in-memory canonical document and its immutable artifact reference."""

    data: dict[str, Any]
    reference: dict[str, str]


@dataclass(frozen=True)
class StateTransition:
    """The resulting immutable run-state snapshot."""

    snapshot: dict[str, Any]
    reference: dict[str, str]
    replayed: bool = False


@dataclass(frozen=True)
class H1WorkspaceTransition:
    """One immutable, coordinator-validated H1 internal workspace advance."""

    workspace: SealedDocument
    replayed: bool = False


def _fail(code: str, message: str) -> None:
    raise CoordinatorError(code, message)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _validate_reference_path(path: str) -> None:
    try:
        resolve_artifact_path(path, root=Path.cwd())
    except ManifestIntegrityError as error:
        _fail("COORD_REFERENCE_INVALID", str(error))


def seal_document(data: Mapping[str, Any], path: str) -> SealedDocument:
    """Seal a canonical JSON document as a path+SHA artifact reference."""

    _validate_reference_path(path)
    body = _copy(dict(data))
    return SealedDocument(
        data=body,
        reference={"path": path, "sha256": canonical_sha256(body)},
    )


def seal_stage_document(
    data: Mapping[str, Any], stage: str, path: str
) -> SealedDocument:
    """Seal a stage completion using a stage-qualified artifact reference."""

    document = seal_document(data, path)
    return SealedDocument(
        data=document.data,
        reference={"stage": stage, **document.reference},
    )


def _binding(
    request: Mapping[str, Any], request_reference: Mapping[str, str]
) -> dict[str, Any]:
    return {
        "return_id": request["return_id"],
        "return_kind": request["return_kind"],
        "return_request": _copy(dict(request_reference)),
        "calculated_owner": request["calculated_owner"],
        "resume_stage": request["resume_stage"],
        "resume_point": request["resume_point"],
    }


class AutonomousCoordinator:
    """Validate and advance one latest autonomous run-state snapshot."""

    def __init__(
        self,
        state: Mapping[str, Any],
        state_reference: Mapping[str, str],
        *,
        active_return_request: SealedDocument | None = None,
        runtime: ContractRuntime | None = None,
    ):
        self._runtime = runtime or ContractRuntime()
        self._state = _copy(dict(state))
        self._state_reference = _copy(dict(state_reference))
        self._active_return_request = (
            _copy(active_return_request) if active_return_request is not None else None
        )
        self._transition_cache: dict[
            tuple[str, str, str], tuple[tuple[Any, ...], StateTransition]
        ] = {}
        self._h1_transition_cache: dict[
            tuple[str, str, str],
            tuple[tuple[Any, ...], H1WorkspaceTransition],
        ] = {}
        self._decision_cache: dict[
            tuple[str, str], tuple[tuple[Any, ...], StateTransition]
        ] = {}
        self._final_cache: dict[
            tuple[str, str], tuple[tuple[Any, ...], StateTransition]
        ] = {}
        self._validate_snapshot(
            self._state,
            self._state_reference,
            active_return_request=self._active_return_request,
        )

    @classmethod
    def initialize(
        cls,
        *,
        run_id: str,
        source_interview_state: Mapping[str, str],
        state_path: str,
        runtime: ContractRuntime | None = None,
    ) -> "AutonomousCoordinator":
        state = {
            "schema_version": "2.0",
            "workflow": "novel-conception-autonomous-v2",
            "run_id": run_id,
            "revision": 0,
            "status": "running",
            "source_interview_state": _copy(dict(source_interview_state)),
            "current_stage_completions": {},
            "h1_workspace": None,
            "active_return": None,
            "resolved_returns": [],
            "superseded_completions": [],
            "author_decision": None,
            "development_status": "not_ready",
            "previous_state": None,
        }
        sealed = seal_document(state, state_path)
        return cls(state, sealed.reference, runtime=runtime)

    @classmethod
    def from_snapshot(
        cls,
        state: Mapping[str, Any],
        state_reference: Mapping[str, str],
        *,
        active_return_request: SealedDocument | None = None,
        runtime: ContractRuntime | None = None,
    ) -> "AutonomousCoordinator":
        return cls(
            state,
            state_reference,
            active_return_request=active_return_request,
            runtime=runtime,
        )

    @property
    def state(self) -> dict[str, Any]:
        return _copy(self._state)

    @property
    def state_reference(self) -> dict[str, str]:
        return _copy(self._state_reference)

    def _schema_validate(self, instance: Any, schema_name: str, code: str) -> None:
        try:
            self._runtime.validate(instance, schema_name)
        except ContractValidationError as error:
            _fail(code, str(error))

    def _validate_artifact_reference(
        self, reference: Mapping[str, Any], *, code: str
    ) -> None:
        try:
            self._runtime.validate_definition(
                reference, "common-defs.schema.json", "artifactReference"
            )
        except ContractValidationError as error:
            _fail(code, str(error))
        _validate_reference_path(reference["path"])

    def _validate_stage_reference(
        self, reference: Mapping[str, Any], *, code: str
    ) -> None:
        try:
            self._runtime.validate_definition(
                reference, "common-defs.schema.json", "stageArtifactReference"
            )
        except ContractValidationError as error:
            _fail(code, str(error))
        _validate_reference_path(reference["path"])

    def _validate_sealed(
        self,
        document: SealedDocument,
        *,
        schema_name: str,
        stage_reference: bool = False,
        code: str,
    ) -> None:
        if stage_reference:
            self._validate_stage_reference(document.reference, code=code)
        else:
            self._validate_artifact_reference(document.reference, code=code)
        actual = canonical_sha256(document.data)
        if document.reference["sha256"] != actual:
            _fail(
                "COORD_STALE_REFERENCE",
                f"{document.reference['path']} hash does not bind the supplied body",
            )
        self._schema_validate(document.data, schema_name, code)

    @staticmethod
    def _prefix_keys(state: Mapping[str, Any]) -> tuple[str, ...]:
        current = state["current_stage_completions"]
        count = len(current)
        expected = STAGE_ORDER[:count]
        if set(current) != set(expected):
            _fail(
                "COORD_INVALID_STATE_PREFIX",
                f"current completions must be a prefix, got {sorted(current)}",
            )
        for stage in expected:
            reference = current[stage]
            if not isinstance(reference, Mapping) or reference.get("stage") != stage:
                _fail(
                    "COORD_INVALID_STATE_PREFIX",
                    f"current completion {stage} has a mismatched stage reference",
                )
        return expected

    def _validate_snapshot(
        self,
        state: Mapping[str, Any],
        state_reference: Mapping[str, Any],
        *,
        active_return_request: SealedDocument | None,
    ) -> None:
        self._schema_validate(
            state, "autonomous-run-state.schema.json", "COORD_STATE_SCHEMA_INVALID"
        )
        self._validate_artifact_reference(
            state_reference, code="COORD_STATE_REFERENCE_INVALID"
        )
        if state_reference["sha256"] != canonical_sha256(state):
            _fail(
                "COORD_STALE_REFERENCE",
                "run-state reference does not bind the supplied snapshot",
            )

        prefix = self._prefix_keys(state)
        if state["revision"] == 0:
            if state["previous_state"] is not None:
                _fail(
                    "COORD_STATE_VERSION_INVALID",
                    "revision 0 must not have a previous_state",
                )
        elif state["previous_state"] is None:
            _fail(
                "COORD_STATE_VERSION_INVALID",
                "revision > 0 must bind previous_state",
            )

        current_values = list(state["current_stage_completions"].values())
        superseded = state["superseded_completions"]
        if any(item in superseded for item in current_values):
            _fail(
                "COORD_CURRENT_SUPERSEDED_OVERLAP",
                "the same completion cannot be current and superseded",
            )

        resolved_ids: set[str] = set()
        available = current_values + superseded
        for resolved in state["resolved_returns"]:
            binding = resolved["return_binding"]
            return_id = binding["return_id"]
            if return_id in resolved_ids:
                _fail(
                    "COORD_RETURN_ALREADY_RESOLVED",
                    f"duplicate resolved return: {return_id}",
                )
            resolved_ids.add(return_id)
            resolving = resolved["resolving_completion"]
            if resolving["stage"] != binding["resume_stage"]:
                _fail(
                    "COORD_RESOLUTION_STAGE_MISMATCH",
                    f"{return_id} resolved by {resolving['stage']}, "
                    f"expected {binding['resume_stage']}",
                )
            if resolving not in available:
                _fail(
                    "COORD_RESOLUTION_NOT_BOUND",
                    f"{return_id} resolving completion is neither current nor superseded",
                )

        active_reference = state["active_return"]
        if active_reference is None:
            if active_return_request is not None:
                _fail(
                    "COORD_UNEXPECTED_RETURN_BODY",
                    "a return body was supplied but run-state has no active return",
                )
            if state["status"] == "revise":
                _fail(
                    "COORD_STATE_STATUS_INVALID",
                    "revise status requires an active return",
                )
            return

        if state["status"] != "revise":
            _fail(
                "COORD_STATE_STATUS_INVALID",
                "an active return requires revise status",
            )
        if active_return_request is None:
            _fail(
                "COORD_ACTIVE_RETURN_BODY_REQUIRED",
                "active return body is required for semantic state validation",
            )
        self._validate_sealed(
            active_return_request,
            schema_name="return-request.schema.json",
            code="COORD_RETURN_SCHEMA_INVALID",
        )
        if active_return_request.reference != active_reference:
            _fail(
                "COORD_ACTIVE_RETURN_REFERENCE_MISMATCH",
                "active return reference does not bind the supplied return body",
            )
        try:
            spec = validate_return_request(
                active_return_request.data, runtime=self._runtime
            )
        except ReturnRoutingError as error:
            _fail(error.code, str(error))
        if active_return_request.data["run_id"] != state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "active return belongs to another run")
        if active_return_request.data["return_id"] in resolved_ids:
            _fail(
                "COORD_RETURN_ALREADY_RESOLVED",
                "active return is already present in resolved_returns",
            )
        resume_index = STAGE_ORDER.index(spec.resume_stage)
        if prefix != STAGE_ORDER[:resume_index]:
            _fail(
                "COORD_INVALID_RETURN_PREFIX",
                "active return state must contain exactly the prefix before resume_stage",
            )
        if any(
            stage in state["current_stage_completions"]
            for stage in active_return_request.data["invalidated_stages"]
        ):
            _fail(
                "COORD_INVALIDATED_STAGE_STILL_CURRENT",
                "an invalidated completion remains current",
            )
        if "H1" in active_return_request.data["invalidated_stages"] and state[
            "h1_workspace"
        ] is not None:
            _fail(
                "COORD_INVALIDATED_H1_WORKSPACE",
                "full H1 invalidation must clear the current workspace",
            )
        if (
            active_return_request.data["invalidate_author_decision"]
            and state["author_decision"] is not None
        ):
            _fail(
                "COORD_INVALIDATED_AUTHOR_DECISION",
                "invalidated author decision remains current",
            )

    def _active_request(
        self, supplied: SealedDocument | None
    ) -> SealedDocument | None:
        active = self._state["active_return"]
        if active is None:
            if supplied is not None:
                _fail(
                    "COORD_UNEXPECTED_RETURN_BODY",
                    "no active return exists for the supplied body",
                )
            return None
        request = supplied or self._active_return_request
        if request is None:
            _fail(
                "COORD_ACTIVE_RETURN_BODY_REQUIRED",
                "active return body is required",
            )
        self._validate_sealed(
            request,
            schema_name="return-request.schema.json",
            code="COORD_RETURN_SCHEMA_INVALID",
        )
        if request.reference != active:
            _fail(
                "COORD_ACTIVE_RETURN_REFERENCE_MISMATCH",
                "supplied return body does not match current active_return",
            )
        try:
            validate_return_request(request.data, runtime=self._runtime)
        except ReturnRoutingError as error:
            _fail(error.code, str(error))
        return request

    def _expected_gate_data(
        self,
        target_stage: str,
        active_return_request: SealedDocument | None,
    ) -> dict[str, Any]:
        if target_stage not in STAGE_ORDER:
            _fail("COORD_UNKNOWN_STAGE", f"unknown stage: {target_stage!r}")
        current_prefix = self._prefix_keys(self._state)
        request = self._active_request(active_return_request)
        target_index = STAGE_ORDER.index(target_stage)
        expected_prefix = STAGE_ORDER[:target_index]

        if request is None:
            if current_prefix != expected_prefix:
                _fail(
                    "COORD_ILLEGAL_STAGE_TRANSITION",
                    f"forward target {target_stage} requires current prefix "
                    f"{list(expected_prefix)}",
                )
            entry_mode = "forward"
            active_reference = None
            return_binding = None
        else:
            if request.data["resume_stage"] != target_stage:
                _fail(
                    "COORD_ACTIVE_RETURN_BLOCKS_STAGE",
                    f"only {request.data['resume_stage']} may resolve the active return",
                )
            if current_prefix != expected_prefix:
                _fail(
                    "COORD_INVALID_RETURN_PREFIX",
                    "return resolution input does not start from the required prefix",
                )
            entry_mode = "return_resolution"
            active_reference = _copy(request.reference)
            return_binding = _binding(request.data, request.reference)

        baseline = (
            None
            if target_stage == "B0"
            else _copy(self._state["current_stage_completions"]["B0"])
        )
        upstream = [
            _copy(self._state["current_stage_completions"][stage])
            for stage in UPSTREAM_TOPOLOGY[target_stage]
        ]
        return {
            "schema_version": "2.0",
            "run_id": self._state["run_id"],
            "target_stage": target_stage,
            "entry_mode": entry_mode,
            "run_state": _copy(self._state_reference),
            "baseline_completion": baseline,
            "upstream_completions": upstream,
            "active_return": active_reference,
            "return_binding": return_binding,
        }

    def build_input_gate(
        self,
        target_stage: str,
        gate_path: str,
        *,
        active_return_request: SealedDocument | None = None,
    ) -> SealedDocument:
        data = self._expected_gate_data(target_stage, active_return_request)
        gate = seal_document(data, gate_path)
        self._validate_sealed(
            gate,
            schema_name="input-gate.schema.json",
            code="COORD_INPUT_GATE_SCHEMA_INVALID",
        )
        return gate

    def accept_h1_workspace_transition(
        self,
        *,
        current_workspace: SealedDocument,
        package_manifest: SealedDocument,
        expected_next_state: str,
        active_return_request: SealedDocument | None = None,
    ) -> H1WorkspaceTransition:
        """Advance the same-session H1 workspace without advancing run-state.

        H1-A/B/C packages are internal artifacts.  They may advance only the
        sealed H1 workspace; the top-level state advances exactly once when the
        final H1 stage completion is accepted.
        """

        self._validate_sealed(
            current_workspace,
            schema_name="h1-workspace-state.schema.json",
            code="COORD_H1_WORKSPACE_SCHEMA_INVALID",
        )
        self._validate_sealed(
            package_manifest,
            schema_name="package-manifest.schema.json",
            code="COORD_H1_MANIFEST_SCHEMA_INVALID",
        )
        workspace = current_workspace.data
        manifest = package_manifest.data
        if workspace["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "H1 workspace belongs to another run")
        if self._prefix_keys(self._state) != STAGE_ORDER[:-1]:
            _fail(
                "COORD_ILLEGAL_STAGE_TRANSITION",
                "H1 internal work requires current completions through P1",
            )
        if workspace["p1_completion"] != self._state[
            "current_stage_completions"
        ]["P1"]:
            _fail(
                "COORD_H1_P1_MISMATCH",
                "H1 workspace does not bind the current P1 completion",
            )

        request = self._active_request(active_return_request)
        if request is not None and request.data["resume_stage"] != "H1":
            _fail(
                "COORD_ACTIVE_RETURN_BLOCKS_STAGE",
                "only an H1 return may admit H1 internal work",
            )

        transitions = {
            "initialized": ("planned", "h1-plan", "plan_manifest"),
            "planned": ("fragments_ready", "h1-fragments", "fragment_manifest"),
            "fragments_ready": (
                "assembled",
                "h1-assembly",
                "assembly_manifest",
            ),
            "assembled": ("rendered", "h1-html", "html_manifest"),
        }
        expected = transitions.get(workspace["state"])
        if expected is None or expected_next_state != expected[0]:
            _fail(
                "COORD_H1_TRANSITION_INVALID",
                f"{workspace['state']} cannot advance to {expected_next_state}",
            )
        _, expected_profile, artifact_key = expected
        if (
            manifest["run_id"] != workspace["run_id"]
            or manifest["stage"] != "H1"
            or manifest["package_profile"] != expected_profile
            or manifest["verdict"] != "ready"
            or manifest.get("session_id") != workspace["session_id"]
            or manifest.get("parent_state_sha256")
            != current_workspace.reference["sha256"]
        ):
            _fail(
                "COORD_H1_MANIFEST_LINEAGE_MISMATCH",
                "H1 manifest does not bind the current workspace transition",
            )

        next_data = {
            "schema_version": "2.0",
            "run_id": workspace["run_id"],
            "stage": "H1",
            "session_id": workspace["session_id"],
            "state": expected_next_state,
            "p1_completion": _copy(workspace["p1_completion"]),
            "previous_state_sha256": current_workspace.reference["sha256"],
            "artifacts": {
                **_copy(workspace["artifacts"]),
                artifact_key: _copy(package_manifest.reference),
            },
        }
        next_path = (
            f"H1/{workspace['session_id']}/"
            f"workspace-{expected_next_state}.json"
        )
        sealed = seal_document(next_data, next_path)
        self._validate_sealed(
            sealed,
            schema_name="h1-workspace-state.schema.json",
            code="COORD_H1_WORKSPACE_SCHEMA_INVALID",
        )
        key = (
            workspace["session_id"],
            current_workspace.reference["sha256"],
            expected_next_state,
        )
        fingerprint = (
            package_manifest.reference["path"],
            package_manifest.reference["sha256"],
        )
        cached = self._h1_transition_cache.get(key)
        if cached is not None:
            previous_fingerprint, previous = cached
            if previous_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    "H1 workspace transition was already accepted differently",
                )
            return H1WorkspaceTransition(
                workspace=_copy(previous.workspace), replayed=True
            )
        transition = H1WorkspaceTransition(workspace=sealed, replayed=False)
        self._h1_transition_cache[key] = (fingerprint, transition)
        return transition

    def _seal_next_state(
        self,
        next_state: Mapping[str, Any],
        next_state_path: str,
        *,
        active_return_request: SealedDocument | None,
    ) -> StateTransition:
        if next_state["revision"] != self._state["revision"] + 1:
            _fail(
                "COORD_STATE_VERSION_INVALID",
                "every transition must advance revision by exactly one",
            )
        if next_state["previous_state"] != self._state_reference:
            _fail(
                "COORD_PREVIOUS_STATE_MISMATCH",
                "next snapshot must bind the exact current state reference",
            )
        sealed = seal_document(next_state, next_state_path)
        self._validate_snapshot(
            sealed.data,
            sealed.reference,
            active_return_request=active_return_request,
        )
        return StateTransition(
            snapshot=_copy(sealed.data),
            reference=_copy(sealed.reference),
            replayed=False,
        )

    def _commit(
        self,
        transition: StateTransition,
        *,
        active_return_request: SealedDocument | None,
    ) -> None:
        self._state = _copy(transition.snapshot)
        self._state_reference = _copy(transition.reference)
        self._active_return_request = (
            _copy(active_return_request) if active_return_request is not None else None
        )

    def accept_stage_completion(
        self,
        *,
        gate: SealedDocument,
        completion: SealedDocument,
        next_state_path: str,
        active_return_request: SealedDocument | None = None,
        h1_workspace: Mapping[str, str] | None = None,
    ) -> StateTransition:
        """Accept one ready completion or resolve the single active return."""

        if completion.data.get("status") != "ready":
            _fail(
                "COORD_COMPLETION_NOT_READY",
                "only a ready stage-completion may advance run-state",
            )
        self._validate_sealed(
            gate,
            schema_name="input-gate.schema.json",
            code="COORD_INPUT_GATE_SCHEMA_INVALID",
        )
        self._validate_sealed(
            completion,
            schema_name="stage-completion.schema.json",
            stage_reference=True,
            code="COORD_COMPLETION_SCHEMA_INVALID",
        )
        stage = completion.data["stage"]
        if completion.reference["stage"] != stage:
            _fail(
                "COORD_COMPLETION_REFERENCE_MISMATCH",
                "completion reference stage does not match completion body",
            )

        return_binding = completion.data["return_binding"]
        if return_binding is not None:
            return_id = return_binding["return_id"]
            if any(
                item["return_binding"]["return_id"] == return_id
                for item in self._state["resolved_returns"]
            ):
                _fail(
                    "COORD_RETURN_ALREADY_RESOLVED",
                    f"return {return_id} has already been resolved",
                )

        transition_key = (
            "stage",
            gate.data.get("run_state", {}).get("sha256", ""),
            stage,
        )
        fingerprint = (
            gate.reference["sha256"],
            completion.reference["sha256"],
            next_state_path,
            canonical_sha256(h1_workspace) if h1_workspace is not None else None,
        )
        cached = self._transition_cache.get(transition_key)
        if cached is not None:
            previous_fingerprint, previous = cached
            if previous_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    f"state transition for {stage} was already accepted differently",
                )
            return StateTransition(
                snapshot=_copy(previous.snapshot),
                reference=_copy(previous.reference),
                replayed=True,
            )

        # Persistent replay after reconstructing the coordinator from the
        # successor snapshot: forward completion is idempotent, return
        # resolution is intentionally one-shot.
        current_ref = self._state["current_stage_completions"].get(stage)
        if (
            self._state["previous_state"] == gate.data.get("run_state")
            and current_ref is not None
        ):
            if return_binding is not None:
                _fail(
                    "COORD_RETURN_ALREADY_RESOLVED",
                    f"return {return_binding['return_id']} has already been resolved",
                )
            if current_ref != completion.reference or next_state_path != self._state_reference[
                "path"
            ]:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    f"successor for {stage} already contains another completion",
                )
            return StateTransition(
                snapshot=self.state,
                reference=self.state_reference,
                replayed=True,
            )

        expected_gate = self._expected_gate_data(stage, active_return_request)
        if gate.data != expected_gate:
            _fail(
                "COORD_INPUT_TOPOLOGY_MISMATCH",
                "input gate does not equal the current fixed-topology gate",
            )
        if completion.data["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "completion belongs to another run")
        if gate.data["target_stage"] != stage:
            _fail(
                "COORD_COMPLETION_STAGE_MISMATCH",
                "completion stage differs from input gate target",
            )
        if completion.data["state_before"] != self._state_reference:
            _fail(
                "COORD_STALE_STATE",
                "completion does not bind the latest run-state",
            )
        if completion.data["input_gate"] != gate.reference:
            _fail(
                "COORD_INPUT_GATE_REFERENCE_MISMATCH",
                "completion does not bind the supplied input gate",
            )
        if (
            completion.data["previous_stage_completions"]
            != gate.data["upstream_completions"]
        ):
            _fail(
                "COORD_INPUT_TOPOLOGY_MISMATCH",
                "completion previous_stage_completions differs from the gate",
            )
        if completion.data["return_binding"] != gate.data["return_binding"]:
            _fail(
                "COORD_RETURN_BINDING_MISMATCH",
                "completion did not copy the gate return_binding byte-for-value",
            )

        request = self._active_request(active_return_request)
        if request is None and return_binding is not None:
            _fail(
                "COORD_RETURN_BINDING_MISMATCH",
                "forward completion cannot carry a return binding",
            )
        if request is not None and return_binding != _binding(
            request.data, request.reference
        ):
            _fail(
                "COORD_RETURN_BINDING_MISMATCH",
                "resolution completion does not bind the active return exactly",
            )

        if stage == "H1":
            if h1_workspace is None:
                _fail(
                    "COORD_H1_WORKSPACE_REQUIRED",
                    "H1 completion must bind the current rendered H1 workspace",
                )
            self._validate_artifact_reference(
                h1_workspace, code="COORD_H1_WORKSPACE_REFERENCE_INVALID"
            )
        elif h1_workspace is not None:
            _fail(
                "COORD_UNEXPECTED_H1_WORKSPACE",
                "only H1 completion may update h1_workspace",
            )

        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        next_state["current_stage_completions"][stage] = _copy(
            completion.reference
        )
        next_state["status"] = "waiting_author" if stage == "H1" else "running"
        if stage == "H1":
            next_state["h1_workspace"] = _copy(dict(h1_workspace))

        next_active: SealedDocument | None = None
        if request is not None:
            resolving = {
                "return_binding": _binding(request.data, request.reference),
                "resolving_completion": _copy(completion.reference),
                "pre_resolution_state": self.state_reference,
            }
            next_state["active_return"] = None
            next_state["resolved_returns"].append(resolving)
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=next_active,
        )
        self._commit(transition, active_return_request=next_active)
        self._transition_cache[transition_key] = (fingerprint, transition)
        return transition

    def apply_return_request(
        self,
        *,
        request: SealedDocument,
        next_state_path: str,
        conception_completion_current: bool = False,
    ) -> StateTransition:
        """Apply deterministic invalidation and register one active return."""

        self._validate_sealed(
            request,
            schema_name="return-request.schema.json",
            code="COORD_RETURN_SCHEMA_INVALID",
        )
        try:
            spec: RouteSpec = validate_return_request(
                request.data, runtime=self._runtime
            )
        except ReturnRoutingError as error:
            _fail(error.code, str(error))
        if request.data["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "return request belongs to another run")

        return_id = request.data["return_id"]
        if any(
            item["return_binding"]["return_id"] == return_id
            for item in self._state["resolved_returns"]
        ):
            _fail(
                "COORD_RETURN_ALREADY_RESOLVED",
                f"return {return_id} has already been resolved",
            )

        if self._state["active_return"] is not None:
            active = self._active_request(None)
            assert active is not None
            if active.data["return_id"] == return_id:
                if active.reference != request.reference or active.data != request.data:
                    _fail(
                        "COORD_TRANSITION_CONFLICT",
                        f"return {return_id} is already active with another body",
                    )
                if next_state_path != self._state_reference["path"]:
                    _fail(
                        "COORD_TRANSITION_CONFLICT",
                        f"return {return_id} successor path differs from accepted state",
                    )
                return StateTransition(
                    snapshot=self.state,
                    reference=self.state_reference,
                    replayed=True,
                )
            _fail(
                "COORD_ACTIVE_RETURN_EXISTS",
                f"return {active.data['return_id']} is already active",
            )

        current_prefix = self._prefix_keys(self._state)
        if request.data["origin_kind"] == "stage":
            origin_index = STAGE_ORDER.index(request.data["origin_stage"])
            if origin_index > len(current_prefix):
                _fail(
                    "COORD_RETURN_ORIGIN_NOT_REACHED",
                    "origin stage is neither current nor the next executing stage",
                )
            if (
                not spec.target_stage.startswith("I")
                and STAGE_ORDER.index(spec.target_stage) > origin_index
            ):
                _fail(
                    "COORD_RETURN_DIRECTION_INVALID",
                    "a stage cannot return forward to a later owner",
                )
        else:
            author_waiting = (
                self._state["status"] == "waiting_author"
                and self._state["author_decision"] is None
                and self._prefix_keys(self._state) == STAGE_ORDER
            )
            if (
                not author_waiting
                and request.data["author_decision"]
                != self._state["author_decision"]
            ):
                _fail(
                    "COORD_AUTHOR_DECISION_MISMATCH",
                    "author-origin return does not bind the current decision",
                )

        expected_author_invalidation = (
            self._state["author_decision"] is not None
            or request.data["origin_kind"] == "author"
        )
        if (
            request.data["invalidate_author_decision"]
            != expected_author_invalidation
        ):
            _fail(
                "COORD_INVALIDATION_FLAG_MISMATCH",
                "invalidate_author_decision does not match current state",
            )
        expected_completion_invalidation = (
            conception_completion_current or request.data["origin_kind"] == "author"
        )
        if (
            request.data["invalidate_conception_completion"]
            != expected_completion_invalidation
        ):
            _fail(
                "COORD_INVALIDATION_FLAG_MISMATCH",
                "invalidate_conception_completion does not match current state",
            )

        transition_key = ("return", self._state_reference["sha256"], return_id)
        fingerprint = (
            request.reference["sha256"],
            next_state_path,
            conception_completion_current,
        )
        cached = self._transition_cache.get(transition_key)
        if cached is not None:
            prior_fingerprint, prior = cached
            if prior_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    f"return {return_id} was already applied differently",
                )
            return StateTransition(
                snapshot=_copy(prior.snapshot),
                reference=_copy(prior.reference),
                replayed=True,
            )

        invalidated = set(request.data["invalidated_stages"])
        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference

        kept: dict[str, Any] = {}
        superseded = list(next_state["superseded_completions"])
        for stage in STAGE_ORDER:
            reference = next_state["current_stage_completions"].get(stage)
            if reference is None:
                continue
            if stage in invalidated:
                if reference not in superseded:
                    superseded.append(reference)
            else:
                kept[stage] = reference
        next_state["current_stage_completions"] = kept
        next_state["superseded_completions"] = superseded
        next_state["active_return"] = _copy(request.reference)
        next_state["status"] = "revise"
        if "H1" in invalidated:
            next_state["h1_workspace"] = None
        if request.data["invalidate_author_decision"]:
            next_state["author_decision"] = None
        if request.data["invalidate_conception_completion"]:
            next_state["development_status"] = "stale_input"

        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=request,
        )
        self._commit(transition, active_return_request=request)
        self._transition_cache[transition_key] = (fingerprint, transition)
        return transition

    def refresh_active_return(
        self,
        *,
        request: SealedDocument,
        next_state_path: str,
    ) -> StateTransition:
        """Append a qualification-only revision for the exact active return.

        A production contract may change again while its earlier routed return
        is still being resolved.  That event must advance the append-only state
        chain so the new qualification receipt has an exact predecessor and
        successor, but it must not create, replace, or resolve a second return.
        """

        active = self._active_request(request)
        if active is None:
            _fail(
                "COORD_ACTIVE_RETURN_REQUIRED",
                "qualification refresh requires an active return",
            )
        if active.reference != request.reference or active.data != request.data:
            _fail(
                "COORD_ACTIVE_RETURN_REFRESH_MISMATCH",
                "qualification refresh must reuse the exact active return",
            )

        transition_key = (
            "return-refresh",
            self._state_reference["sha256"],
            request.data["return_id"],
        )
        fingerprint = (request.reference["sha256"], next_state_path)
        cached = self._transition_cache.get(transition_key)
        if cached is not None:
            prior_fingerprint, prior = cached
            if prior_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    "active return refresh was already accepted differently",
                )
            return StateTransition(
                snapshot=_copy(prior.snapshot),
                reference=_copy(prior.reference),
                replayed=True,
            )

        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=request,
        )
        self._commit(transition, active_return_request=request)
        self._transition_cache[transition_key] = (fingerprint, transition)
        return transition

    def supersede_active_return(
        self,
        *,
        request: SealedDocument,
        next_state_path: str,
    ) -> StateTransition:
        """Replace one active return with a strictly earlier routed owner."""

        old = self._active_request(None)
        if old is None:
            _fail("COORD_ACTIVE_RETURN_REQUIRED", "escalation requires active return")
        self._validate_sealed(
            request,
            schema_name="return-request.schema.json",
            code="COORD_RETURN_SCHEMA_INVALID",
        )
        try:
            spec = validate_return_request(request.data, runtime=self._runtime)
        except ReturnRoutingError as error:
            _fail(error.code, str(error))
        if request.data["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "escalation return belongs to another run")
        if (
            request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != old.data.get("resume_stage")
        ):
            _fail(
                "COORD_RETURN_ESCALATION_ORIGIN_MISMATCH",
                "new return must originate at the old active resume stage",
            )
        old_index = STAGE_ORDER.index(old.data["resume_stage"])
        new_index = STAGE_ORDER.index(spec.resume_stage)
        if new_index >= old_index:
            _fail(
                "COORD_RETURN_ESCALATION_NOT_EARLIER",
                "new return resume stage must be strictly earlier",
            )
        if request.reference == old.reference or request.data["return_id"] == old.data["return_id"]:
            _fail("COORD_RETURN_ESCALATION_CONFLICT", "new return must be immutable and distinct")

        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        invalidated = set(request.data["invalidated_stages"])
        kept: dict[str, Any] = {}
        superseded = list(next_state["superseded_completions"])
        for stage in STAGE_ORDER:
            reference = next_state["current_stage_completions"].get(stage)
            if reference is None:
                continue
            if stage in invalidated:
                if reference not in superseded:
                    superseded.append(reference)
            else:
                kept[stage] = reference
        next_state["current_stage_completions"] = kept
        next_state["superseded_completions"] = superseded
        next_state["active_return"] = _copy(request.reference)
        next_state["status"] = "revise"
        if "H1" in invalidated:
            next_state["h1_workspace"] = None
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=request,
        )
        self._commit(transition, active_return_request=request)
        return transition

    def accept_author_decision(
        self,
        *,
        decision: SealedDocument,
        next_state_path: str,
    ) -> StateTransition:
        """Record one externally supplied approved/rejected author decision.

        A revise event is intentionally not accepted here because it must be
        applied atomically with its routed return request.
        """

        self._validate_sealed(
            decision,
            schema_name="author-decision.schema.json",
            code="COORD_AUTHOR_DECISION_SCHEMA_INVALID",
        )
        branch = decision.data["decision"]
        if branch == "revise":
            _fail(
                "COORD_AUTHOR_REVISE_REQUIRES_RETURN",
                "revise must be applied with a deterministic return request",
            )
        if decision.data["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "author decision belongs to another run")

        if self._state["author_decision"] is not None:
            if (
                self._state["author_decision"] == decision.reference
                and self._state["status"] == branch
                and next_state_path == self._state_reference["path"]
            ):
                return StateTransition(
                    snapshot=self.state,
                    reference=self.state_reference,
                    replayed=True,
                )
            _fail(
                "COORD_TRANSITION_CONFLICT",
                "a different author decision is already current",
            )

        key = (self._state_reference["sha256"], branch)
        fingerprint = (
            decision.reference["path"],
            decision.reference["sha256"],
            next_state_path,
        )
        cached = self._decision_cache.get(key)
        if cached is not None:
            prior_fingerprint, prior = cached
            if prior_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    "author decision was already accepted differently",
                )
            return StateTransition(
                snapshot=_copy(prior.snapshot),
                reference=_copy(prior.reference),
                replayed=True,
            )

        if (
            self._state["status"] != "waiting_author"
            or self._state["active_return"] is not None
            or self._state["author_decision"] is not None
            or self._prefix_keys(self._state) != STAGE_ORDER
            or self._state["h1_workspace"] is None
        ):
            _fail(
                "COORD_AUTHOR_DECISION_NOT_ADMISSIBLE",
                "author decision requires the current completed H1 waiting state",
            )
        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        next_state["status"] = branch
        next_state["author_decision"] = _copy(decision.reference)
        next_state["development_status"] = "not_ready"
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=None,
        )
        self._commit(transition, active_return_request=None)
        self._decision_cache[key] = (fingerprint, transition)
        return transition

    def accept_final_completion(
        self,
        *,
        completion: SealedDocument,
        next_state_path: str,
        active_return_request: SealedDocument | None = None,
    ) -> StateTransition:
        """Grant development admission for one current approved completion."""

        if active_return_request is not None:
            _fail(
                "COORD_ACTIVE_RETURN_BLOCKS_FINAL",
                "final completion cannot consume an active return",
            )
        self._validate_sealed(
            completion,
            schema_name="conception-completion.schema.json",
            code="COORD_FINAL_COMPLETION_SCHEMA_INVALID",
        )
        if completion.data["run_id"] != self._state["run_id"]:
            _fail("COORD_RUN_ID_MISMATCH", "final completion belongs to another run")

        if self._state["development_status"] == "ready":
            replay_key = (
                self._state["previous_state"]["sha256"],
                completion.reference["path"],
            )
            cached = self._final_cache.get(replay_key)
            if cached is not None and cached[0] == (
                completion.reference["sha256"],
                next_state_path,
            ):
                return StateTransition(
                    snapshot=self.state,
                    reference=self.state_reference,
                    replayed=True,
                )
            _fail(
                "COORD_TRANSITION_CONFLICT",
                "a different final completion is already admitted",
            )
        if (
            self._state["status"] != "approved"
            or self._state["development_status"] != "not_ready"
            or self._state["active_return"] is not None
            or self._state["author_decision"] is None
            or self._prefix_keys(self._state) != STAGE_ORDER
        ):
            _fail(
                "COORD_FINAL_COMPLETION_NOT_ADMISSIBLE",
                "only the current approved complete run may enter development",
            )
        if completion.data["run_state"] != self._state_reference:
            _fail(
                "COORD_STALE_STATE",
                "final completion does not bind the latest approved state",
            )
        if completion.data["author_decision"] != self._state["author_decision"]:
            _fail(
                "COORD_AUTHOR_DECISION_MISMATCH",
                "final completion does not bind the current decision",
            )
        expected_stages = {
            stage: _copy(reference)
            for stage, reference in self._state[
                "current_stage_completions"
            ].items()
        }
        if completion.data["stage_completions"] != expected_stages:
            _fail(
                "COORD_INPUT_TOPOLOGY_MISMATCH",
                "final completion does not bind all nine current stages",
            )

        key = (self._state_reference["sha256"], completion.reference["path"])
        fingerprint = (
            completion.reference["sha256"],
            next_state_path,
        )
        cached = self._final_cache.get(key)
        if cached is not None:
            prior_fingerprint, prior = cached
            if prior_fingerprint != fingerprint:
                _fail(
                    "COORD_TRANSITION_CONFLICT",
                    "final admission was already accepted differently",
                )
            return StateTransition(
                snapshot=_copy(prior.snapshot),
                reference=_copy(prior.reference),
                replayed=True,
            )
        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        next_state["development_status"] = "ready"
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=None,
        )
        self._commit(transition, active_return_request=None)
        self._final_cache[key] = (fingerprint, transition)
        return transition


__all__ = [
    "AutonomousCoordinator",
    "CoordinatorError",
    "STAGE_ORDER",
    "UPSTREAM_TOPOLOGY",
    "SealedDocument",
    "StateTransition",
    "H1WorkspaceTransition",
    "seal_document",
    "seal_stage_document",
]
