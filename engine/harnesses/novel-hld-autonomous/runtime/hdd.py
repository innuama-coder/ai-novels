"""Deterministic unresolved-source projection and HDD identity checks."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .contracts import DESIGN_STAGES, SOURCE_ACCESS_MATRIX


def project_unresolved(unresolved_register: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    result = {stage: [] for stage in (*DESIGN_STAGES, "HQ1")}
    for item in sorted(unresolved_register, key=lambda value: value["source_id"]):
        source_id = item["source_id"]
        domain = item["domain"]
        if domain == "quality":
            result["HQ1"].append(source_id)
            continue
        for stage in DESIGN_STAGES:
            if domain in SOURCE_ACCESS_MATRIX[stage]:
                result[stage].append(source_id)
    return result


def expected_hdd_id(owner_stage: str, source_id: str) -> str:
    if owner_stage not in (*DESIGN_STAGES, "HQ1"):
        raise ValueError(f"stage cannot own HDD: {owner_stage}")
    return f"HDD-{owner_stage}-{source_id}"


def validate_hdd(value: Mapping[str, Any]) -> None:
    expected = expected_hdd_id(value["owner_stage"], value["source_id"])
    if value["id"] != expected:
        raise ValueError(f"HDD id must be {expected}")
    resolved = value["disposition"] == "resolved_by_external_author_event"
    if resolved != (value.get("resolution_ref") is not None):
        raise ValueError("resolution_ref is present only for external resolution")


def aggregate_dispositions(
    projections: Mapping[str, Iterable[str]], assessments: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    indexed: dict[tuple[str, str], Mapping[str, Any]] = {}
    by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in assessments:
        validate_hdd(item)
        key = (item["owner_stage"], item["source_id"])
        if key in indexed:
            raise ValueError(f"duplicate HDD: {key}")
        indexed[key] = item
        by_source[item["source_id"]].append(item)
    for stage, source_ids in projections.items():
        for source_id in source_ids:
            if (stage, source_id) not in indexed:
                raise ValueError(f"missing projected HDD: {stage}/{source_id}")
    summaries = []
    for source_id in sorted(by_source):
        rows = sorted(by_source[source_id], key=lambda item: item["owner_stage"])
        dispositions = {row["disposition"] for row in rows}
        if "required_now" in dispositions:
            status = "required_now"
        elif "resolved_by_external_author_event" in dispositions:
            status = "resolved_by_external_author_event"
        elif dispositions == {"not_needed_for_current_stage"}:
            status = "not_needed_for_current_hld"
        else:
            status = "preserved_open_conditionally"
        summaries.append({
            "source_id": source_id,
            "aggregate_status": status,
            "hdd_ids": [row["id"] for row in rows],
            "resolution_refs": [row["resolution_ref"] for row in rows if row.get("resolution_ref")],
        })
    return summaries
