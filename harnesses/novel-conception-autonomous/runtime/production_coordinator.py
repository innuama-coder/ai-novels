"""Production-only coordinator extensions for atomic control-plane work.

Domain stage packages bind the portable :mod:`coordinator` byte identity.  A
production transaction that reissues an unresolved owner's work therefore
lives here and cannot silently alter any B0-Q1 implementation catalog.
"""

from __future__ import annotations

import copy
from typing import Any

from .coordinator import (
    AutonomousCoordinator,
    CoordinatorError,
    H1WorkspaceTransition,
    SealedDocument,
    StateTransition,
)
from .return_routing import ReturnRoutingError, STAGE_ORDER, validate_return_request


def _fail(code: str, message: str) -> None:
    raise CoordinatorError(code, message)


class ProductionCoordinator(AutonomousCoordinator):
    """Coordinator used only by production-owned transaction replay."""

    def accept_h1_workspace_transition(
        self,
        *,
        current_workspace: SealedDocument,
        package_manifest: SealedDocument,
        expected_next_state: str,
        active_return_request: SealedDocument | None = None,
    ) -> H1WorkspaceTransition:
        """Bind retryable H1 successors to the immutable accepted package.

        An internal H1-B or H1-C return preserves the session and its accepted
        predecessor workspace.  The portable coordinator's historical
        state-only filename would then collide with the superseded attempt.
        Production adds the accepted manifest fingerprint for retryable
        ``fragments_ready`` and ``rendered`` successors; exact replay derives
        the same path while a corrected package necessarily receives a fresh
        one.
        """

        transition = super().accept_h1_workspace_transition(
            current_workspace=current_workspace,
            package_manifest=package_manifest,
            expected_next_state=expected_next_state,
            active_return_request=active_return_request,
        )
        if expected_next_state not in {"fragments_ready", "rendered"}:
            return transition
        workspace = transition.workspace
        reference = {
            **workspace.reference,
            "path": (
                f"H1/{workspace.data['session_id']}/"
                f"workspace-{expected_next_state}-"
                f"{package_manifest.reference['sha256'][:24]}.json"
            ),
        }
        return H1WorkspaceTransition(
            workspace=SealedDocument(
                data=copy.deepcopy(workspace.data), reference=reference
            ),
            replayed=transition.replayed,
        )

    def refresh_active_stage_return(
        self,
        *,
        request: SealedDocument,
        next_state_path: str,
    ) -> StateTransition:
        """Replace an active stage return with a fresh route to the same owner."""

        old = self._active_request(None)
        if old is None:
            _fail("COORD_ACTIVE_RETURN_REQUIRED", "stage refresh requires active return")
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
            _fail("COORD_RUN_ID_MISMATCH", "stage refresh belongs to another run")
        old_stage = old.data.get("resume_stage")
        if (
            request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != old_stage
            or spec.target_stage != old_stage
            or spec.resume_stage != old_stage
            or request.data.get("resume_point") != old.data.get("resume_point")
        ):
            _fail(
                "COORD_RETURN_STAGE_REFRESH_TARGET_MISMATCH",
                "fresh return must preserve the exact active owner and resume point",
            )
        if (
            request.reference == old.reference
            or request.data["return_id"] == old.data.get("return_id")
        ):
            _fail(
                "COORD_RETURN_STAGE_REFRESH_CONFLICT",
                "fresh return must be immutable and distinct",
            )

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
        next_state["active_return"] = copy.deepcopy(request.reference)
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

    def narrow_active_h1_return(
        self,
        *,
        request: SealedDocument,
        next_state_path: str,
    ) -> StateTransition:
        """Retarget an active H1 return to an already-reached H1-C action.

        This is deliberately narrower than a normal stage refresh: it is only
        valid when independently rejected author-facing HTML can be rebuilt
        from an already accepted assembled workspace.  A fresh H1-C failure
        may replace an older H1-C failure after a completed retry; other
        same-action refreshes remain forbidden.  It never reinstates an H1
        completion and it cannot move work outside H1.
        """

        old = self._active_request(None)
        if old is None:
            _fail("COORD_ACTIVE_RETURN_REQUIRED", "H1 narrowing requires active return")
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
            _fail("COORD_RUN_ID_MISMATCH", "H1 narrowing belongs to another run")
        h1_actions = ("H1-A-plan", "H1-B", "H1-A-assemble", "H1-C")
        old_action = old.data.get("resume_point")
        new_action = request.data.get("resume_point")
        later_h1_action = (
            old_action in h1_actions
            and new_action in h1_actions
            and h1_actions.index(new_action) > h1_actions.index(old_action)
        )
        repeated_h1_c = (
            old_action == "H1-C"
            and new_action == "H1-C"
            and old.data.get("invalidated_stages") == ["H1"]
            and old.data.get("invalidated_h1_artifacts") == ["html", "completion"]
        )
        if (
            old.data.get("resume_stage") != "H1"
            or request.data.get("origin_kind") != "stage"
            or request.data.get("origin_stage") != "H1"
            or spec.target_stage != "H1"
            or spec.resume_stage != "H1"
            or not (later_h1_action or repeated_h1_c)
            or request.data.get("invalidated_stages") != ["H1"]
            or request.data.get("invalidated_h1_artifacts") != ["html", "completion"]
        ):
            _fail(
                "COORD_H1_RETURN_NARROWING_INVALID",
                "fresh return must target only the already-reached H1-C suffix",
            )
        if (
            request.reference == old.reference
            or request.data["return_id"] == old.data.get("return_id")
        ):
            _fail(
                "COORD_RETURN_STAGE_REFRESH_CONFLICT",
                "fresh return must be immutable and distinct",
            )

        next_state = self.state
        next_state["revision"] += 1
        next_state["previous_state"] = self.state_reference
        next_state["active_return"] = copy.deepcopy(request.reference)
        next_state["status"] = "revise"
        next_state["h1_workspace"] = None
        transition = self._seal_next_state(
            next_state,
            next_state_path,
            active_return_request=request,
        )
        self._commit(transition, active_return_request=request)
        return transition


__all__ = ["ProductionCoordinator"]
