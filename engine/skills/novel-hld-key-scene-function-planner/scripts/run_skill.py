#!/usr/bin/env python3
"""HK1 semantic callback over the public design-stage Harness runtime."""
from __future__ import annotations
import re,sys
from pathlib import Path
from typing import Any,Mapping
SKILL_ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=Path(__file__).resolve().parents[3];HARNESS_ROOT=REPO_ROOT/"harnesses/novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:sys.path.insert(0,str(HARNESS_ROOT))
from runtime.design_stage_runtime import CandidateError,cli_main  # type: ignore[import-not-found]  # noqa:E402

def validate_stage_model(model:dict[str,Any],_contract:Mapping[str,Any])->None:
    hkfs={item["id"]:item for item in model["key_scene_functions"]}
    if not hkfs:raise CandidateError("HK1 requires at least one key-scene function")
    required=("unit_id","preconditions","trigger","primary_functions","secondary_functions","source_obligation_ids","required_state_change","completion_criteria","forbidden_solutions","lld_freedom")
    for item in hkfs.values():
        if any(field not in item for field in required) or len(item["primary_functions"])!=1 or not item["preconditions"] or not item["required_state_change"] or not item["completion_criteria"]:
            raise CandidateError(f"{item['id']}: incomplete function contract or non-unique primary function")
    covered=set()
    for matrix in ("structural_coverage_matrix","storyline_coverage_matrix","arc_coverage_matrix","information_coverage_matrix"):
        for row in model[matrix]:
            refs=set(row.get("hkf_ids",[]))
            if not refs or not refs.issubset(hkfs):raise CandidateError(f"{row['id']}: {matrix} has empty or unknown HKF coverage")
            covered.update(refs)
    if not covered.issubset(hkfs):raise CandidateError("HK1 coverage contains unknown HKF")
    requirements=model["lld_work_requirements"]
    if not requirements:raise CandidateError("HK1 requires LWR grouping")
    consumed=set()
    for requirement in requirements:
        if not re.match(r"^LWR-[A-Za-z0-9._-]+$",requirement["id"]):raise CandidateError(f"{requirement['id']}: HK1 work requirement must use LWR-* (HP1 alone owns LWK-*)")
        refs=requirement.get("hkf_ids",[])
        if not refs or not set(refs).issubset(hkfs):raise CandidateError(f"{requirement['id']}: LWR grouping is empty or references unknown HKF")
        for field in ("merge_split_rationale","entry_state","exit_state","required_elaboration","lld_freedoms","prohibitions","acceptance_criteria"):
            if not requirement.get(field):raise CandidateError(f"{requirement['id']}: missing {field}")
        consumed.update(refs)
    if consumed!=set(hkfs):raise CandidateError("HK1 every HKF must belong to at least one LWR and every LWR must consume an HKF")
    climax_refs=set(model["climax_and_payoff_coverage"].get("hkf_ids",[]))
    if not climax_refs or not climax_refs.issubset(hkfs):raise CandidateError("HK1 climax/payoff coverage is empty or references unknown HKF")

if __name__=="__main__":raise SystemExit(cli_main(SKILL_ROOT,validate_stage_model))
