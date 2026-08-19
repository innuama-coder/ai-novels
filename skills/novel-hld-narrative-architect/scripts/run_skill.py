#!/usr/bin/env python3
"""HA1 semantic callback over the public design-stage Harness runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_ROOT = REPO_ROOT / "harnesses" / "novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from runtime.design_stage_runtime import (  # type: ignore[import-not-found]  # noqa: E402
    CandidateError,
    cli_main,
)


def validate_stage_model(model: dict[str, Any], _contract: Mapping[str, Any]) -> None:
    phases = {item["id"]: item for item in model["structural_phases"]}
    units = {item["id"]: item for item in model["narrative_units"]}
    if not phases or not units or not model["chapter_shells"]:
        raise CandidateError("HA1 requires phases, narrative units, and chapter shells")
    orders = [item.get("order") for item in model["narrative_units"]]
    if orders != list(range(len(orders))):
        raise CandidateError("HA1 narrative unit order must be contiguous from zero")
    for unit in model["narrative_units"]:
        for field in ("parent_phase_id", "purpose", "entry_state_ref", "required_change", "exit_state_ref", "source_anchors"):
            if field not in unit:
                raise CandidateError(f"{unit['id']}: missing {field}")
        if unit["parent_phase_id"] not in phases or not unit["required_change"]:
            raise CandidateError(f"{unit['id']}: invalid phase or empty required change")
    for shell in model["chapter_shells"]:
        if shell.get("parent_unit_id") not in units or not isinstance(shell.get("order"), int):
            raise CandidateError(f"{shell['id']}: invalid chapter parent/order")
    if not model["turning_point_anchors"]:
        raise CandidateError("HA1 requires at least one authoritative turning-point anchor")
    if not {item.get("unit_id") for item in model["turning_point_anchors"]}.issubset(units):
        raise CandidateError("HA1 turning point references unknown narrative unit")
    if {item.get("unit_id") for item in model["entry_exit_state_contracts"]} != set(units):
        raise CandidateError("HA1 state contracts must cover every narrative unit exactly")


if __name__ == "__main__":
    raise SystemExit(cli_main(SKILL_ROOT, validate_stage_model))
