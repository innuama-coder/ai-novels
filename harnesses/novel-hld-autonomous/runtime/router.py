"""Sole parent-consumer routing algebra. It returns decisions; callers persist state."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .contracts import next_stage
from .revision import build_revision_plan


def route_stage_result(
    result: Mapping[str, Any], *, source_result_ref: Mapping[str, Any],
    revision_targets: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    outcome = result["result"]
    stage = result["stage"]
    if result["result_scope"] != "top_level":
        raise ValueError("router never consumes composite_internal results")
    if outcome == "ready":
        destination = next_stage(stage)
        return {"action": "complete" if destination is None else "forward", "next_stage": destination, "accepted_completion_ref": result["completion_ref"]}
    if outcome == "runtime_error":
        return {"action": "runtime_stop", "next_stage": stage, "evidence_ref": result["runtime_error_ref"]}
    if outcome == "blocked":
        blocker = result["blocker_class"]
        if blocker == "author_required":
            return {"action": "author_question", "owner_stage": stage, "gate_data_ref": result["gate_data_ref"]}
        if blocker == "reality_dependency":
            return {"action": "reality_reentry", "evidence_ref": result["blocked_report_ref"]}
        if blocker == "author_rejected":
            return {"action": "author_rejected", "evidence_ref": result["blocked_report_ref"]}
        if blocker == "exhausted":
            return {"action": "exhausted", "evidence_ref": result["blocked_report_ref"]}
        if blocker in {"upstream_defect", "input_invalid"}:
            targets = list(revision_targets)
            if not targets:
                return {"action": "blocked", "evidence_ref": result["blocked_report_ref"]}
            plan = build_revision_plan(hld_run_id=result["hld_run_id"], source_result_ref=source_result_ref, targets=targets)
            return {"action": "revision_plan", "plan": plan}
    if outcome == "revise":
        targets = list(revision_targets)
        if not targets:
            raise ValueError("revise result requires parsed revision targets")
        event_ref = result["author_event_ref"] if result["revision_class"] == "external_author_request" else None
        plan = build_revision_plan(hld_run_id=result["hld_run_id"], source_result_ref=source_result_ref, targets=targets, source_event_ref=event_ref)
        return {"action": "revision_plan", "plan": plan}
    raise ValueError("unregistered result algebra")
