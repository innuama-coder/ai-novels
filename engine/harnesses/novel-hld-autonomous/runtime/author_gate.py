"""Pure constructors for external author question and resolution transactions."""

from __future__ import annotations

from typing import Any, Mapping

from .canonical import canonical_sha256


def source_resolution_question(
    *, hld_run_id: str, revision: int, owner_stage: str, source_control_id: str,
    hdd_ref: Mapping[str, Any], affected_ids: list[str], question_text: str,
) -> dict[str, Any]:
    seed = {"run": hld_run_id, "revision": revision, "owner": owner_stage, "source": source_control_id}
    return {
        "schema_version": "1.0", "hld_run_id": hld_run_id, "revision": revision,
        "question_id": f"HAQ-{canonical_sha256(seed)[:24]}", "question_kind": "source_resolution",
        "owner_stage": owner_stage, "question_text": question_text,
        "allowed_answer_scope": "Resolve only the named existing source control; do not revise other conception authority.",
        "resume_stage": owner_stage, "source_control_id": source_control_id,
        "hdd_ref": dict(hdd_ref), "affected_ids": list(dict.fromkeys(affected_ids)),
        "revision_plan_ref": None, "revision_plan_state_ref": None, "group_id": None,
        "original_target": None, "lineage_change": None, "allowed_new_target_ids": [],
        "request_meaning_hash": None,
    }


def revision_retarget_question(
    *, hld_run_id: str, revision: int, owner_stage: str,
    revision_plan_ref: Mapping[str, Any], revision_plan_state_ref: Mapping[str, Any],
    group_id: str, original_target: str, lineage_change: str,
    allowed_new_target_ids: list[str], request_meaning_hash: str, question_text: str,
) -> dict[str, Any]:
    seed = {"run": hld_run_id, "revision": revision, "group": group_id, "meaning": request_meaning_hash}
    return {
        "schema_version": "1.0", "hld_run_id": hld_run_id, "revision": revision,
        "question_id": f"HAQ-{canonical_sha256(seed)[:24]}", "question_kind": "revision_retarget",
        "owner_stage": owner_stage, "question_text": question_text,
        "allowed_answer_scope": "Select one current target that preserves the original request meaning.",
        "resume_stage": owner_stage, "source_control_id": None, "hdd_ref": None, "affected_ids": [],
        "revision_plan_ref": dict(revision_plan_ref), "revision_plan_state_ref": dict(revision_plan_state_ref),
        "group_id": group_id, "original_target": original_target, "lineage_change": lineage_change,
        "allowed_new_target_ids": list(dict.fromkeys(allowed_new_target_ids)),
        "request_meaning_hash": request_meaning_hash,
    }


def resolve_author_answer(
    *, question: Mapping[str, Any], question_ref: Mapping[str, Any],
    answer_ref: Mapping[str, Any], resolution_kind: str, new_revision: int,
    classification_conclusion: str | None = None,
    retarget_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    kind = question["question_kind"]
    if kind == "source_resolution" and resolution_kind not in {"hld_local_resolution", "conception_authority_change"}:
        raise ValueError("source-resolution question has incompatible resolution kind")
    if kind == "revision_retarget" and resolution_kind != "revision_target_resolution":
        raise ValueError("retarget question must produce revision_target_resolution")
    if resolution_kind == "hld_local_resolution" and not classification_conclusion:
        raise ValueError("local source resolution requires a classification conclusion")
    if resolution_kind == "revision_target_resolution" and not retarget_binding:
        raise ValueError("retarget resolution requires binding")
    return {
        "schema_version": "1.0", "hld_run_id": question["hld_run_id"],
        "question_ref": dict(question_ref), "answer_ref": dict(answer_ref),
        "resolution_kind": resolution_kind,
        "resume_stage": question["resume_stage"] if resolution_kind != "conception_authority_change" else None,
        "new_revision": new_revision, "classification_conclusion": classification_conclusion,
        "retarget_binding": dict(retarget_binding) if retarget_binding else None,
    }
