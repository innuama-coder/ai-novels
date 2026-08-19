#!/usr/bin/env python3
"""HI1 semantic callback over the public design-stage Harness runtime."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
SKILL_ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=Path(__file__).resolve().parents[3];HARNESS_ROOT=REPO_ROOT/"harnesses/novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:sys.path.insert(0,str(HARNESS_ROOT))
from runtime.design_stage_runtime import CandidateError,cli_main  # type: ignore[import-not-found]  # noqa:E402

def validate_stage_model(model:dict[str,Any],_contract:Mapping[str,Any])->None:
    assignments=model["unit_pov_assignments"]
    units=[item.get("unit_id") for item in assignments]
    if not assignments or None in units or len(units)!=len(set(units)):raise CandidateError("HI1 requires one unambiguous POV assignment per represented unit")
    for item in assignments:
        if not item.get("pov_character_id") or not item.get("focalization_mode") or not item.get("perception_limits"):raise CandidateError(f"{item['id']}: incomplete POV legality contract")
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

if __name__=="__main__":raise SystemExit(cli_main(SKILL_ROOT,validate_stage_model))
