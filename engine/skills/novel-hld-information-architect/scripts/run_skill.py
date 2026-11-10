#!/usr/bin/env python3
"""HI1 semantic callback over the public design-stage Harness runtime."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any,Mapping
SKILL_ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=Path(__file__).resolve().parents[3];HARNESS_ROOT=REPO_ROOT/"harnesses/novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:sys.path.insert(0,str(HARNESS_ROOT))
from runtime.design_stage_runtime import CandidateError,UpstreamDefect,execute  # type: ignore[import-not-found]  # noqa:E402

_WORKSPACE:Path|None=None

def _upstream(model:Mapping[str,Any],stage:str)->dict[str,Any]:
    if _WORKSPACE is None:raise CandidateError("HI1 validator workspace is unavailable")
    refs=[item for item in model["source_artifacts"] if item.get("role")==f"upstream::{stage}::main"]
    if len(refs)!=1:raise CandidateError(f"HI1 requires exactly one {stage} main artifact")
    return json.loads((_WORKSPACE/refs[0]["path"]).read_text(encoding="utf-8"))

def _strings(value:Any)->set[str]:
    if isinstance(value,str):return {value}
    if isinstance(value,list):return set().union(*(_strings(item) for item in value),set())
    if isinstance(value,dict):return set().union(*(_strings(item) for item in value.values()),set())
    return set()

def validate_stage_model(model:dict[str,Any],_contract:Mapping[str,Any])->None:
    ha1=_upstream(model,"HA1");hc1=_upstream(model,"HC1")
    narrative_units=ha1.get("narrative_units",[]);chapter_shells=ha1.get("chapter_shells",[])
    if not narrative_units or not chapter_shells:raise CandidateError("HI1 requires HA1 narrative units and chapter shells")
    unit_ids=[item.get("id") for item in narrative_units]
    shell_ids=[item.get("id") for item in chapter_shells]
    if None in unit_ids or len(unit_ids)!=len(set(unit_ids)) or None in shell_ids or len(shell_ids)!=len(set(shell_ids)):
        raise CandidateError("HI1 upstream unit or chapter identities are incomplete or duplicated")
    assignments=model["unit_pov_assignments"]
    units=[item.get("unit_id") for item in assignments]
    if units!=unit_ids:raise CandidateError("HI1 requires one ordered POV assignment per HA1 narrative unit")
    for item in assignments:
        if not item.get("pov_character_id") or not item.get("focalization_mode") or not item.get("perception_limits"):raise CandidateError(f"{item['id']}: incomplete POV legality contract")
    chapter_assignments=model["chapter_pov_assignments"]
    assigned_chapters=[item.get("chapter_id") for item in chapter_assignments]
    if assigned_chapters!=shell_ids:raise CandidateError("HI1 requires one ordered POV assignment per HA1 chapter shell")
    shell_by_id={item["id"]:item for item in chapter_shells}
    known_characters={item.get("character_id") for item in hc1.get("character_participation_register",[])}
    agency_contracts=hc1.get("chapter_agency_contracts",[])
    if [item.get("chapter_id") for item in agency_contracts]!=shell_ids:
        affected=[item.get("id") for item in hc1.get("character_participation_register",[]) if item.get("id")]
        raise UpstreamDefect(
            "HC1 chapter agency contracts do not exactly cover HA1 chapter shells; HI1 cannot infer focal availability, decision authority, or information access from unit prose",
            affected or ["HAS-UPSTREAM-CHAPTER-AGENCY"],
            "Return to HC1 and publish one ordered chapter agency contract per HA1 shell before HI1 is regenerated.",
        )
    agency_by_chapter={item["chapter_id"]:item for item in agency_contracts}
    for item in chapter_assignments:
        shell=shell_by_id[item["chapter_id"]]
        if item["parent_unit_id"]!=shell.get("parent_unit_id") or item["parent_unit_id"] not in set(unit_ids):
            raise CandidateError(f"{item['id']}: chapter POV parent unit does not match HA1")
        if item["pov_character_id"] not in known_characters:
            raise CandidateError(f"{item['id']}: chapter POV character is unknown to HC1")
        agency=agency_by_chapter[item["chapter_id"]]
        if item["hc1_agency_contract_id"]!=agency.get("id"):
            raise CandidateError(f"{item['id']}: chapter POV does not bind the exact HC1 agency contract")
        if item["pov_character_id"] not in agency.get("focal_character_ids",[]):
            raise CandidateError(f"{item['id']}: focal character is unavailable or unauthorized by HC1")
        paths=[path for path in agency.get("information_paths",[]) if path.get("character_id")==item["pov_character_id"]]
        if len(paths)!=1 or item["knowledge_acquisition_modes"]!=paths[0].get("acquisition_modes"):
            raise CandidateError(f"{item['id']}: chapter knowledge acquisition does not exactly bind HC1")
        if item["perception_limits"]!=[paths[0].get("limit")]:
            raise CandidateError(f"{item['id']}: chapter perception limit does not exactly bind HC1")
        if not item.get("focalization_mode") or not item.get("perception_limits"):
            raise CandidateError(f"{item['id']}: incomplete chapter POV legality contract")
    nodes={item["id"]:item for item in model["information_nodes"]}
    if not nodes:raise CandidateError("HI1 requires at least one information node")
    legal_modes={"perceived","told","inferred","remembered","documented","system_output","authorized_open"}
    for node in nodes.values():
        required=("source_information_id","knower_ids","reader_state","acquisition_mode","earliest_legal_unit_id","forbidden_leak_unit_ids","resolution_ref")
        if any(field not in node for field in required) or node["acquisition_mode"] not in legal_modes:raise CandidateError(f"{node['id']}: incomplete or illegal information acquisition")
        if not node["knower_ids"] and node["reader_state"]=="known":raise CandidateError(f"{node['id']}: reader knowledge lacks a legal carrier")
    state_nodes=set()
    for state in model["knowledge_states"]+model["reader_information_states"]:state_nodes.update(state.get("information_node_ids",[]))
    if not state_nodes.issubset(nodes):raise CandidateError("HI1 knowledge states reference unknown information nodes")
    for chain in model["suspense_chains"]:
        if not chain.get("setup_node_ids") or not set(chain["setup_node_ids"]).issubset(nodes):raise CandidateError(f"{chain['id']}: suspense setup is missing or unknown")
        terminal=chain.get("payoff_node_ids") or chain.get("authorized_open_terminal")
        if not terminal:raise CandidateError(f"{chain['id']}: suspense chain lacks payoff or authorized-open terminal")
        if chain.get("payoff_node_ids") and not set(chain["payoff_node_ids"]).issubset(nodes):raise CandidateError(f"{chain['id']}: payoff references unknown information node")
    for row in model["reveal_payoff_matrix"]:
        if not set(row.get("information_node_ids",[])).issubset(nodes) or not row.get("setup_unit_ids") or not row.get("terminal_unit_id"):raise CandidateError(f"{row['id']}: reveal/payoff trace is incomplete")

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("work_order",type=Path);parser.add_argument("draft_dir",type=Path);args=parser.parse_args()
    global _WORKSPACE;_WORKSPACE=args.work_order.resolve(strict=True).parent
    code,_=execute(SKILL_ROOT.resolve(),args.work_order.resolve(),args.draft_dir.resolve(),validate_stage_model)
    return code

if __name__=="__main__":raise SystemExit(main())
