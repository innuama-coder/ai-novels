#!/usr/bin/env python3
"""HR1 semantic callback over the public design-stage Harness runtime."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
SKILL_ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=Path(__file__).resolve().parents[3];HARNESS_ROOT=REPO_ROOT/"harnesses/novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:sys.path.insert(0,str(HARNESS_ROOT))
from runtime.design_stage_runtime import CandidateError,cli_main  # type: ignore[import-not-found]  # noqa:E402

def validate_stage_model(model:dict[str,Any],_contract:Mapping[str,Any])->None:
    order=model["narrative_order_map"]
    unit_ids=[item.get("unit_id") for item in order];positions=[item.get("narrative_position") for item in order]
    if not order or None in unit_ids or len(unit_ids)!=len(set(unit_ids)) or positions!=list(range(len(positions))):raise CandidateError("HR1 narrative order must cover unique units in contiguous order")
    known=set(unit_ids)
    for item in model["unit_duration_density"]:
        if item.get("unit_id") not in known or item.get("story_duration_class") not in {"instant","short","medium","long","open"} or item.get("discourse_density") not in {"compressed","balanced","expanded","open"}:raise CandidateError(f"{item['id']}: invalid duration/density contract")
    for transition in model["space_transition_map"]:
        if transition.get("from_unit_id") not in known or transition.get("to_unit_id") not in known or not transition.get("continuity_preconditions"):raise CandidateError(f"{transition['id']}: illegal or unsupported space transition")
    for sync in model["parallel_synchronization"]:
        branches=sync.get("branch_unit_ids",[])
        if len(branches)<2 or not set(branches).issubset(known) or not sync.get("synchronization_anchor"):raise CandidateError(f"{sync['id']}: parallel synchronization is incomplete")
    for name in ("pacing_curve","tension_curve"):
        covered={item.get("unit_id") for item in model[name]}
        if covered!=known:raise CandidateError(f"HR1 {name} must cover every narrative unit exactly")
    ledger_units={item.get("unit_id") for item in model["continuity_ledger"]}
    if ledger_units!=known:raise CandidateError("HR1 continuity ledger must cover every narrative unit")
    high={item.get("unit_id") for item in model["tension_curve"] if item.get("level") in {"high","peak"}}
    recovered={unit for item in model["recovery_windows"] for unit in item.get("after_unit_ids",[])}
    if high and not high.intersection(recovered):raise CandidateError("HR1 high tension has no explicit recovery-window decision")

if __name__=="__main__":raise SystemExit(cli_main(SKILL_ROOT,validate_stage_model))
