#!/usr/bin/env python3
"""HS1 semantic callback over the public design-stage Harness runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = Path(__file__).resolve().parents[3] / "harnesses" / "novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from runtime.design_stage_runtime import CandidateError, cli_main  # type: ignore[import-not-found]  # noqa: E402


def validate_stage_model(model: dict[str, Any], _contract: Mapping[str, Any]) -> None:
    register = {item.get("source_storyline_id"): item for item in model["semantic_storyline_register"]}
    if None in register or len(register) != len(model["semantic_storyline_register"]):
        raise CandidateError("HS1 storyline register IDs must be unique")
    dispositions = {item.get("source_storyline_id"): item.get("disposition") for item in model["activation_disposition"]}
    if set(dispositions) != set(register):
        raise CandidateError("HS1 activation disposition must cover storyline register exactly")
    allowed = {"placed", "background-carried", "optional-not-activated", "preserved-open"}
    if any(value not in allowed for value in dispositions.values()):
        raise CandidateError("HS1 activation disposition is invalid")
    segment_lines = [item.get("source_storyline_id") for item in model["storyline_segments"]]
    if len(segment_lines) != len(set(segment_lines)):
        raise CandidateError("HS1 storyline segments must be unique by source storyline")
    for line_id, disposition in dispositions.items():
        if disposition in {"placed", "background-carried"} and line_id not in segment_lines:
            raise CandidateError(f"HS1 active/background storyline {line_id} has no auditable carrier segment")
        if disposition in {"optional-not-activated", "preserved-open"} and line_id in segment_lines:
            raise CandidateError(f"HS1 inactive/open storyline {line_id} cannot masquerade as a placed segment")
    segments_by_line = {item["source_storyline_id"]: item for item in model["storyline_segments"]}
    chapters = model["chapter_storyline_plan"]
    chapter_ids = [item["chapter_id"] for item in chapters]
    plan_ids = [item["id"] for item in chapters]
    if len(chapter_ids) != len(set(chapter_ids)) or len(plan_ids) != len(set(plan_ids)):
        raise CandidateError("HS1 chapter plan IDs must be unique")
    if [item["chapter_number"] for item in chapters] != list(range(1, len(chapters) + 1)):
        raise CandidateError("HS1 chapter plan numbers must be contiguous and ordered")
    carried_shells = {shell_id for segment in model["storyline_segments"] for shell_id in segment["chapter_shell_ids"]}
    if set(chapter_ids) != carried_shells:
        raise CandidateError("HS1 chapter plan must exactly cover carried HA1 chapter shells")
    for chapter in chapters:
        assigned = [
            chapter["primary_storyline_id"],
            *chapter["supporting_storyline_ids"],
            *chapter["background_storyline_ids"],
            *chapter["preserved_open_storyline_ids"],
        ]
        if len(assigned) != len(set(assigned)):
            raise CandidateError(f"{chapter['id']}: storyline roles overlap")
        if set(assigned) - set(register):
            raise CandidateError(f"{chapter['id']}: unknown storyline assignment")
        active = [chapter["primary_storyline_id"], *chapter["supporting_storyline_ids"], *chapter["background_storyline_ids"]]
        for line_id in active:
            segment = segments_by_line.get(line_id)
            if segment is None or chapter["chapter_id"] not in segment["chapter_shell_ids"]:
                raise CandidateError(f"{chapter['id']}: active storyline lacks chapter carrier")
        for line_id in chapter["preserved_open_storyline_ids"]:
            if dispositions[line_id] not in {"optional-not-activated", "preserved-open"}:
                raise CandidateError(f"{chapter['id']}: preserved-open storyline is active")
    connection_ids = {item["id"] for item in model["storyline_connections"]}
    for point in model["convergence_and_split_points"]:
        if not set(point.get("connection_ids", [])).issubset(connection_ids):
            raise CandidateError(f"{point['id']}: unknown connection")
    if model["subject_reconstruction_test"].get("verdict") != "pass":
        raise CandidateError("HS1 subject reconstruction test must pass")


if __name__ == "__main__":
    raise SystemExit(cli_main(SKILL_ROOT, validate_stage_model))
