#!/usr/bin/env python3
"""HD1 semantic callback over the public design-stage Harness runtime."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

SKILL_ROOT=Path(__file__).resolve().parents[1]
REPO_ROOT=Path(__file__).resolve().parents[3]
HARNESS_ROOT=REPO_ROOT/"harnesses/novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:sys.path.insert(0,str(HARNESS_ROOT))
from runtime.design_stage_runtime import CandidateError,UpstreamDefect,execute  # type: ignore[import-not-found]  # noqa:E402

_WORKSPACE:Path|None=None
GENERIC=re.compile(r"^(?:推进(?:主线|剧情)|加深(?:矛盾|人物)|塑造人物|增加悬念|承上启下)[。.!！]?$",re.I)

def _upstream(model:Mapping[str,Any],stage:str)->dict[str,Any]:
    if _WORKSPACE is None:raise CandidateError("HD1 validator workspace is unavailable")
    role=f"upstream::{stage}::main"
    refs=[item for item in model["source_artifacts"] if item.get("role")==role]
    if len(refs)!=1:raise CandidateError(f"HD1 requires exactly one {stage} main artifact")
    return json.loads((_WORKSPACE/refs[0]["path"]).read_text(encoding="utf-8"))

def _all(values:list[list[str]])->list[str]:return list(dict.fromkeys(item for group in values for item in group))

def _strings(value:Any)->set[str]:
    if isinstance(value,str):return {value}
    if isinstance(value,list):return set().union(*(_strings(item) for item in value),set())
    if isinstance(value,dict):return set().union(*(_strings(item) for item in value.values()),set())
    return set()

def validate_stage_model(model:dict[str,Any],_contract:Mapping[str,Any])->None:
    ha1=_upstream(model,"HA1");hs1=_upstream(model,"HS1");hc1=_upstream(model,"HC1");hi1=_upstream(model,"HI1")
    hr1=_upstream(model,"HR1");hk1=_upstream(model,"HK1")
    shells=ha1.get("chapter_shells",[])
    if not shells:raise CandidateError("HD1 requires HA1 chapter shells")
    shell_by_id={item["id"]:item for item in shells}
    plans=hs1.get("chapter_storyline_plan",[]);plan_by_chapter={item["chapter_id"]:item for item in plans}
    definitions=model["chapter_definitions"]
    ids=[item["id"] for item in definitions];chapter_ids=[item["chapter_id"] for item in definitions];numbers=[item["chapter_number"] for item in definitions]
    if len(ids)!=len(set(ids)) or len(chapter_ids)!=len(set(chapter_ids)):raise CandidateError("HD1 chapter definitions must be unique")
    if chapter_ids!=[item["id"] for item in shells] or numbers!=list(range(1,len(shells)+1)):raise CandidateError("HD1 must cover HA1 chapter shells exactly once and in order")
    if set(plan_by_chapter)!=set(chapter_ids):raise CandidateError("HS1 chapter storyline plan does not exactly cover HA1 shells")
    agency_contracts=hc1.get("chapter_agency_contracts",[])
    if [item.get("chapter_id") for item in agency_contracts]!=chapter_ids:
        affected=[item.get("id") for item in hc1.get("character_participation_register",[]) if item.get("id")]
        raise UpstreamDefect(
            "HC1 chapter agency contracts do not exactly cover HA1 chapter shells; HD1 cannot assign focalization, consequential choice, or cost without explicit character availability",
            affected or ["HAS-UPSTREAM-CHAPTER-AGENCY"],
            "Return to HC1 and publish one ordered chapter agency contract per HA1 shell before HI1 and HD1 are regenerated.",
        )
    agency_by_chapter={item["chapter_id"]:item for item in agency_contracts}
    chapter_pov=hi1.get("chapter_pov_assignments",[])
    chapter_pov_by_id={item.get("chapter_id"):item for item in chapter_pov}
    if None in chapter_pov_by_id or len(chapter_pov_by_id)!=len(chapter_pov) or set(chapter_pov_by_id)!=set(chapter_ids):
        parent_units={shell_by_id[chapter_id]["parent_unit_id"] for chapter_id in chapter_ids}
        affected=[item["id"] for item in hi1.get("unit_pov_assignments",[]) if item.get("unit_id") in parent_units and item.get("id")]
        raise UpstreamDefect(
            "HI1 chapter POV assignments do not exactly cover HA1 chapter shells; unit-level POV cannot authorize chapters whose focal character changes or becomes unavailable",
            affected or ["HPV-UPSTREAM-CHAPTER-COVERAGE"],
            "Return to HI1 and create one exact chapter POV assignment for every HA1 chapter shell before HD1 is regenerated.",
        )
    purposes:set[str]=set();changes:set[str]=set()
    relevant_authority_by_index:list[set[str]]=[]
    for definition in definitions:
        chapter_id=definition["chapter_id"];shell=shell_by_id[chapter_id];plan=plan_by_chapter[chapter_id]
        relevant_authority=_strings(shell)|_strings(plan)
        relevant_authority_by_index.append(relevant_authority)
        if not set(definition["source_refs"])&relevant_authority:
            raise CandidateError(f"{definition['id']}: source_refs do not cite this chapter's HA1/HS1 authority")
        if definition["parent_unit_id"]!=shell["parent_unit_id"]:raise CandidateError(f"{definition['id']}: parent_unit_id differs from HA1 shell")
        for field in ("chapter_number","working_title","parent_unit_id"):
            if definition[field]!=plan[field]:raise CandidateError(f"{definition['id']}: {field} differs from HS1 chapter plan")
        expected_roles={key:plan[key] for key in ("primary_storyline_id","supporting_storyline_ids","background_storyline_ids","preserved_open_storyline_ids")}
        if definition["storyline_roles"]!=expected_roles:raise CandidateError(f"{definition['id']}: storyline roles differ from HS1")
        purpose=definition["narrative_necessity"].strip();change=definition["dramatic_contract"]["irreversible_change"].strip()
        if GENERIC.match(purpose) or GENERIC.match(change):raise CandidateError(f"{definition['id']}: generic chapter definition")
        if purpose in purposes or change in changes:raise CandidateError(f"{definition['id']}: duplicated chapter purpose or change")
        purposes.add(purpose);changes.add(change)
        if definition["entry_state"]==definition["exit_state"]:raise CandidateError(f"{definition['id']}: entry and exit states are identical")
        changed=sum(definition["entry_state"][field]!=definition["exit_state"][field] for field in ("story_state","character_state","knowledge_state","pressure_state","available_actions"))
        if changed<2:raise CandidateError(f"{definition['id']}: chapter does not create a material multi-dimensional state change")
        dramatic=[value for value in definition["dramatic_contract"].values() if isinstance(value,str)]
        if len(set(dramatic))!=len(dramatic):raise CandidateError(f"{definition['id']}: dramatic contract repeats one statement across distinct obligations")
        development=definition["story_development"]
        if set(development["information_revealed"])&set(development["information_withheld"]):raise CandidateError(f"{definition['id']}: the same information is both revealed and withheld")
        pov=definition["pov_contract"]
        assignment=chapter_pov_by_id[chapter_id]
        agency=agency_by_chapter[chapter_id]
        if assignment.get("parent_unit_id")!=definition["parent_unit_id"]:
            raise CandidateError(f"{definition['id']}: HI1 chapter POV parent unit drift")
        if pov["hi1_assignment_id"]!=assignment.get("id") or pov["focal_character_id"]!=assignment.get("pov_character_id") or pov["pov_mode"]!=assignment.get("focalization_mode"):
            raise CandidateError(f"{definition['id']}: POV contract does not exactly bind HI1 chapter assignment")
        if assignment.get("hc1_agency_contract_id")!=agency.get("id") or pov["focal_character_id"] not in agency.get("focal_character_ids",[]):
            raise CandidateError(f"{definition['id']}: POV contract does not bind an HC1-authorized focal character")
        if set(pov["may_know"])&set(pov["must_not_know"]):raise CandidateError(f"{definition['id']}: POV knowledge permission and prohibition overlap")
        if pov["reader_knows_before"]==pov["reader_knows_after"]:raise CandidateError(f"{definition['id']}: reader knowledge does not change")
        if not set(definition["place_scope"]).issubset(set(definition["references"]["environment_ids"])):raise CandidateError(f"{definition['id']}: place scope is not bound to referenced environments")
        handoff=definition["lld_handoff"]
        if set(handoff["freedoms"])&set(handoff["prohibitions"]):raise CandidateError(f"{definition['id']}: LLD freedom and prohibition overlap")
        pulls={definition["chapter_end_hook"],definition["unresolved_question"],definition["next_chapter_necessity"]}
        if len(pulls)!=3:raise CandidateError(f"{definition['id']}: ending hook, unresolved question, and next-chapter necessity are not distinct")
        if definition["memory_design"] is not None and definition["memory_design"]["objective_evidence_rule"]!="memory_alone_is_not_objective_evidence":raise CandidateError(f"{definition['id']}: memory is not properly bounded")
        roles=definition["storyline_roles"]
        role_sets=[{roles["primary_storyline_id"]},set(roles["supporting_storyline_ids"]),set(roles["background_storyline_ids"]),set(roles["preserved_open_storyline_ids"])]
        if any(role_sets[i]&role_sets[j] for i in range(4) for j in range(i+1,4)):raise CandidateError(f"{definition['id']}: storyline roles overlap")
        refs=definition["references"]
        dramatic=definition["dramatic_contract"]
        institutional=dramatic["institutional_choice_actors"]
        if not dramatic["choice_actor_ids"] and not institutional:
            raise CandidateError(f"{definition['id']}: consequential choice requires a named or institutional actor")
        participants={pov["focal_character_id"],*dramatic["choice_actor_ids"],*dramatic["cost_bearer_ids"]}
        if not participants.issubset(set(refs["character_ids"])):
            raise CandidateError(f"{definition['id']}: POV, choice actors, and cost bearers must be explicit chapter character references")
        if not participants.issubset(_strings(hc1)):
            raise CandidateError(f"{definition['id']}: POV, choice actor, or cost bearer is unknown to HC1")
        if not set(dramatic["choice_actor_ids"]).issubset(set(agency.get("choice_actor_ids",[]))):
            raise CandidateError(f"{definition['id']}: consequential choice is assigned to an HC1-unauthorized actor")
        if institutional != agency.get("institutional_choice_actors",[]):
            raise CandidateError(f"{definition['id']}: institutional choice actors do not exactly bind HC1")
        if not set(dramatic["cost_bearer_ids"]).issubset(set(agency.get("cost_bearer_ids",[]))):
            raise CandidateError(f"{definition['id']}: cost is assigned to an HC1-unauthorized bearer")
        allowed={
            "character_ids":_strings(hc1),
            "environment_ids":_strings(ha1)|_strings(hr1)|_strings(hk1),
            "event_ids":_strings(ha1)|_strings(hs1)|_strings(hc1)|_strings(hr1)|_strings(hk1),
        }
        for field,known in allowed.items():
            unknown=set(refs[field])-known
            if unknown:raise CandidateError(f"{definition['id']}: unknown {field}: {sorted(unknown)}")
    for claim in model["derivation_claims"]:
        match=re.match(r"^/chapter_definitions/(\d+)(?:/|$)",claim["target_locator"])
        if match is None:continue
        index=int(match.group(1))
        if index>=len(definitions):raise CandidateError(f"{claim['id']}: derivation target chapter does not exist")
        if not set(claim["source_refs"]).issubset(set(definitions[index]["source_refs"])):
            raise CandidateError(f"{claim['id']}: derivation sources are not bound by the target chapter")
        if not set(claim["source_refs"])&relevant_authority_by_index[index]:
            raise CandidateError(f"{claim['id']}: derivation sources do not cite the target chapter's HA1/HS1 authority")
    links=model["chapter_chain"]
    if len(links)!=max(0,len(definitions)-1):raise CandidateError("HD1 chapter chain must contain exactly n-1 links")
    for index,link in enumerate(links):
        if (link["from_chapter_id"],link["to_chapter_id"])!=(chapter_ids[index],chapter_ids[index+1]):raise CandidateError(f"{link['id']}: chapter chain is not consecutive")
        current=definitions[index];following=definitions[index+1]
        exact=(("inherited_change",current["dramatic_contract"]["irreversible_change"]),("unresolved_pressure",current["exit_state"]["pressure_state"]),("continuity_requirement",following["entry_state"]["story_state"]),("why_next_cannot_be_skipped",current["next_chapter_necessity"]))
        for field,expected_value in exact:
            if link[field]!=expected_value:raise CandidateError(f"{link['id']}: {field} does not exactly bind adjacent chapter definitions")
    summary=model["coverage_summary"]
    if summary["chapter_shell_ids"]!=chapter_ids or summary["chapter_definition_ids"]!=ids:raise CandidateError("HD1 coverage summary does not match chapters")
    expected={
        "storyline_ids":_all([[item["storyline_roles"]["primary_storyline_id"],*item["storyline_roles"]["supporting_storyline_ids"],*item["storyline_roles"]["background_storyline_ids"],*item["storyline_roles"]["preserved_open_storyline_ids"]] for item in definitions]),
        "character_ids":_all([item["references"]["character_ids"] for item in definitions]),
        "environment_ids":_all([item["references"]["environment_ids"] for item in definitions]),
        "event_ids":_all([item["references"]["event_ids"] for item in definitions]),
        "key_function_ids":_all([item["references"]["key_function_ids"] for item in definitions]),
    }
    for key,value in expected.items():
        if summary[key]!=value:raise CandidateError(f"HD1 coverage summary differs from chapter references: {key}")
    known_hkf={item["id"] for item in hk1.get("key_scene_functions",[])}
    if not set(summary["key_function_ids"]).issubset(known_hkf):raise CandidateError("HD1 references unknown HK1 key functions")

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("work_order",type=Path);parser.add_argument("draft_dir",type=Path);args=parser.parse_args()
    global _WORKSPACE;_WORKSPACE=args.work_order.resolve(strict=True).parent
    code,_=execute(SKILL_ROOT.resolve(),args.work_order.resolve(),args.draft_dir.resolve(),validate_stage_model)
    return code

if __name__=="__main__":raise SystemExit(main())
