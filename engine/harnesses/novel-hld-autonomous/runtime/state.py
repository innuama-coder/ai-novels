"""Pure constructors for immutable run-state revisions."""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import HARNESS


def initial_state(hld_run_id: str) -> dict[str, Any]:
    if not hld_run_id:
        raise ValueError("hld_run_id is required")
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": hld_run_id,
        "revision": 0, "event_sequence": 0, "status": "initialized", "current_stage": "HB0",
        "accepted_completions": [], "current_result_ref": None, "previous_state_ref": None,
        "revision_plan_ref": None, "revision_plan_state_ref": None, "waiting_transaction_ref": None,
    }


def successor_state(
    previous: Mapping[str, Any], *, event_sequence: int, status: str, current_stage: str | None,
    current_result_ref: Mapping[str, Any], previous_state_ref: Mapping[str, Any],
    accepted_completion: Mapping[str, Any] | None = None,
    revision_plan_ref: Mapping[str, Any] | None = None,
    revision_plan_state_ref: Mapping[str, Any] | None = None,
    waiting_transaction_ref: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if event_sequence <= int(previous["event_sequence"]):
        raise ValueError("event_sequence must increase")
    completions = list(previous["accepted_completions"])
    if accepted_completion is not None:
        completions.append(dict(accepted_completion))
    return {
        "schema_version": "1.0", "harness": HARNESS, "hld_run_id": previous["hld_run_id"],
        "revision": int(previous["revision"]) + 1, "event_sequence": event_sequence,
        "status": status, "current_stage": current_stage, "accepted_completions": completions,
        "current_result_ref": dict(current_result_ref), "previous_state_ref": dict(previous_state_ref),
        "revision_plan_ref": dict(revision_plan_ref) if revision_plan_ref else None,
        "revision_plan_state_ref": dict(revision_plan_state_ref) if revision_plan_state_ref else None,
        "waiting_transaction_ref": dict(waiting_transaction_ref) if waiting_transaction_ref else None,
    }
