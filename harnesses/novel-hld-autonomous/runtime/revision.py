"""Immutable revision-plan and append-only plan-state constructors."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .canonical import canonical_sha256
from .contracts import STAGES, invalidated_suffix, owner_for_id


def root_cause_fingerprint(
    *, defect_origin: str, exact_owner: str, violated_contract: str,
    affected_ids: Iterable[str], correction_condition: str,
) -> str:
    payload = {
        "defect_origin": defect_origin,
        "exact_owner": exact_owner,
        "violated_contract": violated_contract,
        "sorted_affected_ids": sorted(set(affected_ids)),
        "correction_condition_hash": canonical_sha256(correction_condition),
    }
    return canonical_sha256(payload)


def _owner_and_kind(target: Mapping[str, Any]) -> tuple[str, str]:
    kind = target.get("target_kind", "hld_content")
    if kind == "conception_authority":
        raise ValueError("conception_authority exits the HLD run; no local plan is legal")
    affected = target.get("affected_ids")
    if not isinstance(affected, list) or not affected:
        raise ValueError("each target requires affected_ids")
    owners = {owner_for_id(value) for value in affected}
    if len(owners) != 1:
        raise ValueError("one target group cannot span owners")
    owner = owners.pop()
    if kind == "hld_content" and owner in {"HH1-A", "HH1-C"}:
        raise ValueError("semantic author changes must target their canonical HLD owner, not a report element")
    expected_kind = "render_expression" if owner == "HH1-C" else "report_content" if owner == "HH1-A" else kind
    if kind not in {expected_kind, "presentation_review", "hld_content"}:
        raise ValueError("target kind conflicts with stable ID owner")
    if owner == "HH1-C":
        kind = "render_expression"
    elif owner == "HH1-A":
        kind = "report_content"
    return owner, kind


def build_revision_plan(
    *, hld_run_id: str, source_result_ref: Mapping[str, Any],
    targets: Iterable[Mapping[str, Any]], source_event_ref: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    raw_targets = list(targets)
    if not raw_targets:
        raise ValueError("revision plan requires targets")
    prepared: list[tuple[int, int, dict[str, Any]]] = []
    fingerprints: list[str] = []
    for source_order, target in enumerate(raw_targets):
        owner, kind = _owner_and_kind(target)
        stage = owner.split("-", 1)[0]
        affected_ids = list(dict.fromkeys(target["affected_ids"]))
        fingerprint = None
        if target.get("automatic", True):
            fingerprint = root_cause_fingerprint(
                defect_origin=target["defect_origin"], exact_owner=owner,
                violated_contract=target["violated_contract"], affected_ids=affected_ids,
                correction_condition=target["correction_condition"],
            )
            fingerprints.append(fingerprint)
        identity = canonical_sha256({"source_order": source_order, "affected_ids": affected_ids, "owner": owner})[:20]
        group = {
            "group_id": f"HRG-{source_order:03d}-{identity}", "exact_owner": owner,
            "target_stage": stage, "resume_stage": stage, "target_kind": kind,
            "affected_ids": affected_ids, "requirements": list(target["requirements"]),
            "source_target_refs": list(target["source_target_refs"]),
            "invalidated_suffix": list(invalidated_suffix(owner, kind)),
            "completion_condition": target["correction_condition"],
            "root_cause_fingerprint": fingerprint,
        }
        prepared.append((STAGES.index(stage), source_order, group))
    prepared.sort(key=lambda item: (item[0], item[1]))
    groups = [item[2] for item in prepared]
    earliest = min((STAGES.index(group["invalidated_suffix"][0]) for group in groups))
    plan_material = {
        "hld_run_id": hld_run_id, "source_result_ref": source_result_ref,
        "source_event_ref": source_event_ref, "groups": groups,
    }
    return {
        "schema_version": "1.0",
        "revision_plan_id": f"HRP-{canonical_sha256(plan_material)[:24]}",
        "hld_run_id": hld_run_id,
        "source_result_ref": dict(source_result_ref),
        "source_event_ref": dict(source_event_ref) if source_event_ref else None,
        "target_groups": groups,
        "invalidated_suffix": list(STAGES[earliest:]),
        "author_reapproval_required": True,
        "root_cause_fingerprints": sorted(set(fingerprints)),
    }


def initial_plan_state(
    plan: Mapping[str, Any], *, plan_ref: Mapping[str, Any], transition_event_ref: Mapping[str, Any]
) -> dict[str, Any]:
    groups = [item["group_id"] for item in plan["target_groups"]]
    return {
        "schema_version": "1.0", "revision_plan_ref": dict(plan_ref),
        "previous_plan_state_ref": None, "active_group_id": groups[0],
        "pending_group_ids": groups[1:], "resolved_group_ids": [], "superseded_group_ids": [],
        "retarget_bindings": [], "plan_status": "active",
        "transition_event_ref": dict(transition_event_ref),
    }


def transition_plan_state(
    previous: Mapping[str, Any], *, plan_group_ids: Iterable[str],
    previous_state_ref: Mapping[str, Any], transition_event_ref: Mapping[str, Any],
    resolved_group_id: str | None = None, superseded_group_id: str | None = None,
    retarget_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    groups = set(plan_group_ids)
    active = previous["active_group_id"]
    pending = list(previous["pending_group_ids"])
    resolved = list(previous["resolved_group_ids"])
    superseded = list(previous["superseded_group_ids"])
    retargets = list(previous["retarget_bindings"])
    if resolved_group_id:
        if resolved_group_id != active:
            raise ValueError("only active group can resolve")
        resolved.append(resolved_group_id)
        active = pending.pop(0) if pending else None
    if superseded_group_id:
        if superseded_group_id != active:
            raise ValueError("only active group can become superseded")
        superseded.append(superseded_group_id)
        active = None
    if retarget_binding:
        group_id = retarget_binding["group_id"]
        if group_id not in superseded:
            raise ValueError("retarget applies only to superseded group")
        superseded.remove(group_id)
        active = group_id
        retargets.append(dict(retarget_binding))
    sets = [set(value for value in collection if value is not None) for collection in ([active], pending, resolved, superseded)]
    if any(sets[i] & sets[j] for i in range(4) for j in range(i + 1, 4)) or set().union(*sets) != groups:
        raise ValueError("plan-state partition is not total and disjoint")
    status = "waiting_retarget" if superseded and active is None else "resolved" if not active and not pending and not superseded else "active"
    return {
        "schema_version": "1.0", "revision_plan_ref": dict(previous["revision_plan_ref"]),
        "previous_plan_state_ref": dict(previous_state_ref), "active_group_id": active,
        "pending_group_ids": pending, "resolved_group_ids": resolved,
        "superseded_group_ids": superseded, "retarget_bindings": retargets,
        "plan_status": status, "transition_event_ref": dict(transition_event_ref),
    }
