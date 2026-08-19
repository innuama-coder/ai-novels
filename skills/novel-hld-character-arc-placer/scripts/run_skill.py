#!/usr/bin/env python3
"""HC1 semantic callback over the public design-stage Harness runtime."""

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
    core = {
        item.get("character_id") for item in model["character_participation_register"]
        if item.get("importance") == "core"
    }
    models = {item.get("character_id") for item in model["arc_state_models"]}
    if not core or not core.issubset(models):
        raise CandidateError("HC1 every core character requires an arc state model")
    roles: dict[str, set[str]] = {character_id: set() for character_id in core}
    for step in model["arc_steps"]:
        if step.get("character_id") in roles:
            roles[step["character_id"]].add(step.get("role"))
        for field in ("pressure", "choice", "cost", "consequence", "unit_id", "event_id", "storyline_segment_id"):
            if not step.get(field):
                raise CandidateError(f"{step['id']}: missing {field}")
    required_roles = {"start", "pressure", "choice", "cost", "result"}
    for character_id, actual in roles.items():
        if not required_roles.issubset(actual):
            raise CandidateError(f"HC1 core arc {character_id} lacks start-pressure-choice-cost-result")
    for relationship in model["relationship_steps"]:
        if len(relationship.get("character_ids", [])) != 2 or not relationship.get("state_before") or not relationship.get("state_after"):
            raise CandidateError(f"{relationship['id']}: relationship change must be bilateral")


if __name__ == "__main__":
    raise SystemExit(cli_main(SKILL_ROOT, validate_stage_model))
