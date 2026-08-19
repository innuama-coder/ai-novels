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
    reader_names = [item.get("reader_name") for item in model["semantic_storyline_register"]]
    if None in reader_names or len(reader_names) != len(set(reader_names)):
        raise CandidateError("HS1 reader-facing storyline names must be present and unique")
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
    chapters = model["chapter_storyline_plan"]
    design_ids = [item.get("id") for item in chapters]
    chapter_ids = [item.get("chapter_id") for item in chapters]
    chapter_numbers = [item.get("chapter_number") for item in chapters]
    if None in design_ids or len(design_ids) != len(set(design_ids)) or None in chapter_ids or len(chapter_ids) != len(set(chapter_ids)):
        raise CandidateError("HS1 chapter design and chapter-shell IDs must each be unique")
    if chapter_numbers != list(range(1, len(chapters) + 1)):
        raise CandidateError("HS1 chapter numbers must be contiguous and ordered from one")
    if len({item.get("working_title") for item in chapters}) != len(chapters):
        raise CandidateError("HS1 chapter working titles must be unique")
    dispositions_by_role = {
        "primary_storyline_id": {line_id for line_id, value in dispositions.items() if value == "placed"},
        "supporting_storyline_ids": {line_id for line_id, value in dispositions.items() if value == "placed"},
        "background_storyline_ids": {line_id for line_id, value in dispositions.items() if value == "background-carried"},
        "preserved_open_storyline_ids": {line_id for line_id, value in dispositions.items() if value == "preserved-open"},
    }
    chapter_roles: dict[str, set[str]] = {line_id: set() for line_id in register}
    for chapter in chapters:
        role_values = {
            "primary_storyline_id": [chapter["primary_storyline_id"]],
            "supporting_storyline_ids": chapter["supporting_storyline_ids"],
            "background_storyline_ids": chapter["background_storyline_ids"],
            "preserved_open_storyline_ids": chapter["preserved_open_storyline_ids"],
        }
        flattened = [value for values in role_values.values() for value in values]
        if len(flattened) != len(set(flattened)):
            raise CandidateError(f"HS1 chapter {chapter['id']} assigns one storyline to multiple roles")
        for role, values in role_values.items():
            invalid = set(values) - dispositions_by_role[role]
            if invalid:
                raise CandidateError(f"HS1 chapter {chapter['id']} uses invalid {role}: {sorted(invalid)}")
            for line_id in values:
                chapter_roles[line_id].add(chapter["chapter_id"])
    segments = {item["source_storyline_id"]: set(item["chapter_shell_ids"]) for item in model["storyline_segments"]}
    active_chapter_ids = set().union(*segments.values()) if segments else set()
    if set(chapter_ids) != active_chapter_ids:
        raise CandidateError("HS1 chapter designs must exactly cover every active chapter shell")
    for line_id, disposition in dispositions.items():
        expected = segments.get(line_id, set())
        actual = chapter_roles[line_id]
        if disposition in {"placed", "background-carried"} and actual != expected:
            raise CandidateError(f"HS1 chapter/storyline placement drifts from segment: {line_id}")
        if disposition in {"optional-not-activated", "preserved-open"} and disposition != "preserved-open" and actual:
            raise CandidateError(f"HS1 inactive storyline appears in a chapter: {line_id}")
    connection_ids = {item["id"] for item in model["storyline_connections"]}
    for point in model["convergence_and_split_points"]:
        if not set(point.get("connection_ids", [])).issubset(connection_ids):
            raise CandidateError(f"{point['id']}: unknown connection")
    if model["subject_reconstruction_test"].get("verdict") != "pass":
        raise CandidateError("HS1 subject reconstruction test must pass")


if __name__ == "__main__":
    raise SystemExit(cli_main(SKILL_ROOT, validate_stage_model))
