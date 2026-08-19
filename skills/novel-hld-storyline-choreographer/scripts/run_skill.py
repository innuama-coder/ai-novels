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
    for line_id, disposition in dispositions.items():
        if disposition == "placed" and line_id not in segment_lines:
            raise CandidateError(f"HS1 placed storyline {line_id} has no segment")
    connection_ids = {item["id"] for item in model["storyline_connections"]}
    for point in model["convergence_and_split_points"]:
        if not set(point.get("connection_ids", [])).issubset(connection_ids):
            raise CandidateError(f"{point['id']}: unknown connection")
    if model["subject_reconstruction_test"].get("verdict") != "pass":
        raise CandidateError("HS1 subject reconstruction test must pass")


if __name__ == "__main__":
    raise SystemExit(cli_main(SKILL_ROOT, validate_stage_model))
