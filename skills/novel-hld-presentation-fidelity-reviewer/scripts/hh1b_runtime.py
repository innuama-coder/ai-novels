#!/usr/bin/env python3
"""Public HH1-B hybrid runtime: independently validate report fidelity and seal the review."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any,Mapping

SKILL_ROOT=Path(__file__).resolve().parents[1];REPO=SKILL_ROOT.parents[1];HARNESS_ROOT=REPO/"harnesses/novel-hld-autonomous"
sys.path.insert(0,str(HARNESS_ROOT))
from runtime.canonical import ContractError,canonical_sha256,json_pointer,read_json,write_json  # noqa:E402
from runtime.composite_internal_runtime import (Context,InternalCondition,Spec,atomic_execute,catalog,finalize_condition,finalize_ready,finalize_runtime_error,implementation_sha256,load_context,sha256)  # noqa:E402

SKILL="novel-hld-presentation-fidelity-reviewer";VERSION="1.0.0"
MODEL_ROLES={"hld_model_ha1":"canonical-models/narrative-architecture.json","hld_model_hs1":"canonical-models/storyline-choreography.json","hld_model_hc1":"canonical-models/character-arc-placement.json","hld_model_hi1":"canonical-models/narrative-information-architecture.json","hld_model_hr1":"canonical-models/rhythm-continuity-architecture.json","hld_model_hk1":"canonical-models/key-scene-function-map.json","hld_model_hd1":"canonical-models/chapter-definition-architecture.json"}
DOMAIN_BY_PATH={"canonical-models/narrative-architecture.json":"overall_narrative_architecture","canonical-models/storyline-choreography.json":"storyline_choreography","canonical-models/character-arc-placement.json":"character_arc_placement","canonical-models/narrative-information-architecture.json":"pov_information_suspense","canonical-models/rhythm-continuity-architecture.json":"time_space_pacing_tension","canonical-models/key-scene-function-map.json":"key_scene_functions","canonical-models/chapter-definition-architecture.json":"chapter_definitions","novel-hld-package.json":"open_items_constraints_and_lld_boundary"}
DOMAIN_SECTIONS=("overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","pov_information_suspense","time_space_pacing_tension","key_scene_functions","chapter_definitions","open_items_constraints_and_lld_boundary")
HP1_PACKAGE_SCHEMA=REPO/"skills/novel-hld-package-assembler/references/novel-hld-package.schema.json"
HP1_CROSS_INDEX_SCHEMA=REPO/"skills/novel-hld-package-assembler/references/hld-cross-index.schema.json"
REQUIRED_ROLES=("hb0_manifest","hld_control_baseline","hp1_completion","hp1_manifest","novel_hld_package","hld_cross_index",*MODEL_ROLES,"human_review_report","hh1_a_manifest","hh1_a_generation_session","hh1_a_work_order")
SPEC=Spec(SKILL,VERSION,"HH1.B","presentation-fidelity-review.json","presentation_fidelity_review","review-session.json","fidelity-review-execution.json","hh1-b-validation.schema.json",REQUIRED_ROLES)
QUESTIONS={"architecture_progression","world_environment_definitions","character_definitions","environment_definitions","mandatory_storyline_connections","core_arc_choices","pov_knowledge_boundaries","continuity_constraints","key_functions_and_climax","chapter_definition_readiness","open_items_and_lld_boundary"}
QUESTION_SECTIONS={"architecture_progression":"overall_narrative_architecture","world_environment_definitions":"world_environment_definitions","character_definitions":"character_definitions","environment_definitions":"environment_definitions","mandatory_storyline_connections":"storyline_choreography","core_arc_choices":"character_arc_placement","pov_knowledge_boundaries":"pov_information_suspense","continuity_constraints":"time_space_pacing_tension","key_functions_and_climax":"key_scene_functions","chapter_definition_readiness":"chapter_definitions","open_items_and_lld_boundary":"open_items_constraints_and_lld_boundary"}
WORLD_ENVIRONMENT_SCOPES={"city_and_region","local_people_and_daily_life","social_order_and_public_atmosphere","technology_and_infrastructure","climate_and_physical_environment"}
DIMENSIONS=("fact_fidelity","structure_and_relation_fidelity","coverage_fidelity","authority_and_open_item_fidelity","visual_data_fidelity")
IDENTITY_FIELDS={"schema_version","skill","stage","hld_run_id","status","input_gate_ref","source_artifacts","derivation_claims","decision_dependencies"}
CJK=re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]");LATIN=re.compile(r"\b[A-Za-z]+(?:['’][A-Za-z]+)*\b")
SCHEMA_NAMES=("presentation-fidelity-review.schema.json","hh1-b-review-session.schema.json","hh1-b-execution.schema.json","hh1-b-validation.schema.json")

def schema_paths():return [*(SKILL_ROOT/"references"/name for name in SCHEMA_NAMES),HP1_PACKAGE_SCHEMA,HP1_CROSS_INDEX_SCHEMA]
def implementation_paths():return [Path(__file__),SKILL_ROOT/"scripts/run_skill.py",SKILL_ROOT/"references/runtime-contract.json",HARNESS_ROOT/"runtime/composite_internal_runtime.py",HARNESS_ROOT/"runtime/canonical.py",HARNESS_ROOT/"runtime/package_envelope.py",HARNESS_ROOT/"runtime/schema_catalog.py",*sorted((HARNESS_ROOT/"schemas").glob("*.schema.json")),*schema_paths(),REPO/"skills/novel-hld-review-report-assembler/references/hld-human-review-report.schema.json"]
def impl_hash():return implementation_sha256(implementation_paths())
def _catalog():return catalog(HARNESS_ROOT,[*schema_paths(),REPO/"skills/novel-hld-review-report-assembler/references/hld-human-review-report.schema.json"])

def _member(manifest:Mapping[str,Any],path:Path,package:Path)->bool:
    try:relative=path.resolve(strict=True).relative_to(package.resolve(strict=True)).as_posix()
    except ValueError:return False
    return sum(1 for item in manifest.get("files",[]) if item.get("path")==relative and item.get("sha256")==sha256(path))==1

def _all_elements(report:Mapping[str,Any])->list[dict[str,Any]]:
    names=("title_and_decision_scope","overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","pov_information_suspense","time_space_pacing_tension","key_scene_functions","chapter_definitions","open_items_constraints_and_lld_boundary","visual_models")
    return [item for name in names for item in report.get(name,[]) if isinstance(item,dict)]

def _definition_controls(baseline:Mapping[str,Any])->dict[str,set[str]]:
    result={"world_environment_definitions":set(),"character_definitions":set(),"environment_definitions":set()}
    for control in baseline.get("control_registry",[]):
        if not isinstance(control,dict) or not isinstance(control.get("source_text"),str):continue
        source_id=control.get("source_id")
        text=control["source_text"]
        try:value=json.loads(text)
        except (TypeError,ValueError):value=None
        if isinstance(value,dict) and value.get("id")==source_id:
            if control.get("domain")=="characters" and isinstance(value.get("individual_definition"),dict) and isinstance(value.get("story_position"),dict):result["character_definitions"].add(source_id)
            elif control.get("domain")=="environments" and isinstance(value.get("narrative_responsibility"),str) and isinstance(value.get("scope"),str):result["environment_definitions"].add(source_id)
        elif control.get("domain")=="characters" and isinstance(source_id,str) and source_id.startswith("CHR-") and "### 可观察行为" in text and "位置" in text:
            result["character_definitions"].add(source_id)
        if control.get("domain")=="world" and control.get("authority_class")=="author_locked" and isinstance(source_id,str):result["world_environment_definitions"].add(source_id)
    if not result["world_environment_definitions"]:
        fallback=next((control for control in baseline.get("control_registry",[]) if isinstance(control,dict) and control.get("authority_class")=="author_locked" and control.get("domain") not in {"characters","environments"} and isinstance(control.get("source_id"),str) and isinstance(control.get("source_text"),str)),None)
        if fallback:result["world_environment_definitions"].add(fallback["source_id"])
    return result

def _pairs(item:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any],label:str)->list[tuple[str,str]]:
    if len(item["source_ids"])!=len(item["locators"]):raise InternalCondition("blocked","HH1B_REPORT_UNPAIRED_EVIDENCE",label,[label])
    pairs=list(zip(item["source_ids"],item["locators"]))
    if len(pairs)!=len(set(pairs)) or any(pair not in binding_index for pair in pairs):raise InternalCondition("blocked","HH1B_REPORT_MISATTRIBUTED_EVIDENCE",label,[label])
    return pairs

def _visual_pairs(visual:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any])->set[tuple[str,str]]:
    result=set(_pairs(visual,binding_index,visual["id"]));node_ids=[node["id"] for node in visual["nodes"]]
    if len(node_ids)!=len(set(node_ids)):raise InternalCondition("blocked","HH1B_VISUAL_NODE_DUPLICATE",visual["id"],[visual["id"]])
    for node in visual["nodes"]:result.update(_pairs(node,binding_index,f"{visual['id']}:node:{node['id']}"))
    for index,edge in enumerate(visual["edges"]):
        if edge["from"] not in node_ids or edge["to"] not in node_ids:raise InternalCondition("blocked","HH1B_VISUAL_EDGE_DANGLING",visual["id"],[visual["id"]])
        result.update(_pairs(edge,binding_index,f"{visual['id']}:edge:{index}"))
    return result

def _primary_locators(item:Mapping[str,Any])->list[str]:
    if item.get("element_kind") in {"character_definition","environment_definition"}:
        return list(item["locators"][:1])
    return list(item["locators"])

def _validate_definition_supplements(report:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any],documents:Mapping[str,Any])->None:
    canonical_paths=set(MODEL_ROLES.values())
    for section in ("character_definitions","environment_definitions"):
        for item in report[section]:
            base_source=item["source_ids"][0]
            for pair in list(zip(item["source_ids"],item["locators"]))[1:]:
                entry=binding_index.get(pair)
                if entry is None or entry["model_path"] not in canonical_paths:
                    raise InternalCondition("blocked","HH1B_DEFINITION_SUPPLEMENT_INVALID",f"{item['id']} supplemental binding is not a current canonical HLD model",[item["id"]])
                value=json_pointer(documents[entry["model_path"]],entry["locator"])
                direct_refs=set(value.get("source_refs",[])) if isinstance(value,Mapping) else set()
                authority_refs={ref.get("source_id") for ref in value.get("source_authority_refs",[]) if isinstance(ref,Mapping)} if isinstance(value,Mapping) else set()
                if base_source not in direct_refs|authority_refs:
                    raise InternalCondition("blocked","HH1B_DEFINITION_SUPPLEMENT_INVALID",f"{item['id']} supplemental binding is not derived from {base_source}",[item["id"]])

def admit(context:Context)->tuple[dict[str,Any],dict[str,Any],dict[str,Any],dict[str,Any]]:
    machine=read_json(context.roles["novel_hld_package"]);report=read_json(context.roles["human_review_report"]);a_manifest=read_json(context.roles["hh1_a_manifest"]);a_session=read_json(context.roles["hh1_a_generation_session"]);a_work=read_json(context.roles["hh1_a_work_order"]);hp1_completion=read_json(context.roles["hp1_completion"]);hp1_manifest=read_json(context.roles["hp1_manifest"]);cross=read_json(context.roles["hld_cross_index"]);hb0_manifest=read_json(context.roles["hb0_manifest"]);baseline=read_json(context.roles["hld_control_baseline"])
    context.catalog.validate(report,"hld-human-review-report.schema.json");context.catalog.validate(a_manifest,"package-manifest.schema.json");context.catalog.validate(a_work,"work-order.schema.json");context.catalog.validate(hp1_completion,"stage-completion.schema.json");context.catalog.validate(hp1_manifest,"package-manifest.schema.json");context.catalog.validate(hb0_manifest,"package-manifest.schema.json");context.catalog.validate(baseline,"hld-control-baseline.schema.json")
    if not _member(a_manifest,context.roles["human_review_report"],context.roles["hh1_a_manifest"].parent) or not _member(a_manifest,context.roles["hh1_a_generation_session"],context.roles["hh1_a_manifest"].parent):raise InternalCondition("blocked","HH1B_ASSEMBLER_PACKAGE_UNSEALED","HH1-A report/session is not uniquely manifest-bound",["HH1-A"])
    if a_work["task_id"]!=a_session.get("task_id") or a_work["task_id"]==context.work_order["task_id"]:raise InternalCondition("blocked","HH1B_TASK_ISOLATION","reviewer task must differ from sealed assembler producer task",["HH1-A","HH1-B"],blocker_class="input_invalid")
    if a_work["hld_run_id"]!=context.work_order["hld_run_id"] or a_work["revision"]!=context.work_order["revision"]:raise InternalCondition("blocked","HH1B_PRODUCER_IDENTITY_DRIFT","assembler work-order is not current",["HH1-A"])
    if report["hp1_content_binding"]!={"package_sha256":sha256(context.roles["novel_hld_package"]),"completion_sha256":sha256(context.roles["hp1_completion"])}:raise InternalCondition("blocked","HH1B_REPORT_HP1_BINDING_DRIFT","candidate report does not bind current HP1",["HH1-A"])
    if hp1_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hp1_manifest"]) or not _member(hp1_manifest,context.roles["novel_hld_package"],context.roles["hp1_manifest"].parent):raise InternalCondition("blocked","HH1B_HP1_ENVELOPE_DRIFT","HP1 package is not current/sealed",["HP1"])
    if not _member(hb0_manifest,context.roles["hld_control_baseline"],context.roles["hb0_manifest"].parent):raise InternalCondition("blocked","HH1B_HB0_BASELINE_UNSEALED","HB0 control baseline is not uniquely sealed",["HB0"])
    context.catalog.validate(machine,HP1_PACKAGE_SCHEMA.name);context.catalog.validate(cross,HP1_CROSS_INDEX_SCHEMA.name)
    models={role:read_json(context.roles[role]) for role in MODEL_ROLES}
    if any(value.get("hld_run_id")!=context.work_order["hld_run_id"] or value.get("status")!="ready" for value in models.values()):raise InternalCondition("blocked","HH1B_CANONICAL_IDENTITY_DRIFT","one or more HP1 canonical models are stale",list(MODEL_ROLES))
    documents={"novel-hld-package.json":machine,**{MODEL_ROLES[role]:value for role,value in models.items()}};binding_index={}
    for item in cross["entries"]:
        key=(item["id"],f"{item['model_path']}#{item['locator']}")
        if item["model_path"] not in documents or key in binding_index or canonical_sha256(json_pointer(documents[item["model_path"]],item["locator"]))!=item["value_sha256"]:raise InternalCondition("blocked","HH1B_CROSS_INDEX_VALUE_DRIFT",item["id"],[item["id"]])
        binding_index[key]=item
    _validate_definition_supplements(report,binding_index,documents)
    elements=_all_elements(report);expected=[]
    for item in elements:expected.extend((item["id"],source,locator) for source,locator in _pairs(item,binding_index,item["id"]))
    actual=[(item["report_element_id"],item["source_id"],item["locator"]) for item in report["source_bindings"]]
    if len(actual)!=len(set(actual)) or actual!=expected:raise InternalCondition("blocked","HH1B_REPORT_BINDING_CLOSURE_DRIFT","sealed report source bindings are not a unique ordered expansion",["HH1-A"])
    definitions=_definition_controls(baseline);world_environment_ids=definitions["world_environment_definitions"];character_ids=definitions["character_definitions"];environment_ids=definitions["environment_definitions"]
    if not world_environment_ids or {item["source_ids"][0] for item in report["character_definitions"]}!=character_ids or {item["source_ids"][0] for item in report["environment_definitions"]}!=environment_ids:raise InternalCondition("blocked","HH1B_DEFINITION_COVERAGE_DRIFT","world/character/place definition sources do not match the sealed conception baseline",["HH1-A"])
    world_items=report["world_environment_definitions"]
    if {item["environment_scope"] for item in world_items}!=WORLD_ENVIRONMENT_SCOPES or {source for item in world_items for source in item["source_ids"]}!=world_environment_ids:raise InternalCondition("blocked","HH1B_WORLD_ENVIRONMENT_COVERAGE_DRIFT","world environment cards do not cover the exact five scopes and sealed sources",["HH1-A"])
    by_scope={item["environment_scope"]:item for item in world_items}
    city_network=by_scope["city_and_region"].get("city_network",{});cities=city_network.get("cities",[]);links=city_network.get("intercity_links",[]);portraits=by_scope["local_people_and_daily_life"].get("ordinary_people_portraits",[]);city_names={city.get("city_name") for city in cities}
    if len(cities)<4 or len(city_names)!=len(cities) or len(links)<4 or {portrait.get("city") for portrait in portraits}!=city_names or "season_profile" not in by_scope["climate_and_physical_environment"]:raise InternalCondition("blocked","HH1B_WORLD_ENVIRONMENT_PROFILE_SHALLOW","four-city network, city-wide ordinary-person coverage, and season profile are not complete",["HH1-A"])
    expected_domains={locator:("character_definitions" if item["id"] in character_ids else "environment_definitions" if item["id"] in environment_ids else "world_environment_definitions" if item["id"] in world_environment_ids else DOMAIN_BY_PATH[item["model_path"]]) for (source,locator),item in binding_index.items()}
    primary={section:{locator for element in report[section] for locator in _primary_locators(element)} for section in set(DOMAIN_BY_PATH.values())|{"world_environment_definitions","character_definitions","environment_definitions"}}
    if any(locator not in primary[section] for locator,section in expected_domains.items()) or any(locator in expected_domains and expected_domains[locator]!=section for section,locators in primary.items() for locator in locators):raise InternalCondition("blocked","HH1B_PRIMARY_DOMAIN_COVERAGE_DRIFT","title/visual references cannot replace exact nine-domain primary coverage",["HH1-A"])
    for visual in report["visual_models"]:_visual_pairs(visual,binding_index)
    return machine,models,report,{"a_manifest":a_manifest,"a_session":a_session,"a_work":a_work,"binding_index":binding_index}

def _evidence_for(report:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any],element_ids:set[str])->tuple[set[str],set[str]]:
    sources=set();locators=set()
    by_id={item["id"]:item for item in _all_elements(report)}
    for element_id in element_ids:
        item=by_id[element_id]
        for source,locator in _pairs(item,binding_index,element_id):sources.add(source);locators.add(locator)
        if element_id.startswith("HVG-"):
            for source,locator in _visual_pairs(item,binding_index):sources.add(source);locators.add(locator)
    return sources,locators

def _budget(report:Mapping[str,Any])->dict[str,Any]:
    values=[]
    def visible(item:Mapping[str,Any])->list[str]:
        if item.get("element_kind")=="character_definition":keys=("name","conclusion","story_position","personality_and_motivation","capabilities_and_limits","relationships_and_change")
        elif item.get("element_kind")=="environment_definition":keys=("name","conclusion","story_function","physical_character","access_and_limits","dramatic_use")
        elif item.get("element_kind")=="world_environment_definition":
            keys=("name","definition","people_and_daily_life","story_pressure_and_limits")
            result=[str(item[key]) for key in keys if key in item]
            def collect(value:Any)->None:
                if isinstance(value,str):result.append(value)
                elif isinstance(value,list):
                    for child in value:collect(child)
                elif isinstance(value,Mapping):
                    for child in value.values():collect(child)
            for key in ("defining_features","author_open_details","city_stories","route_stories","ordinary_people_stories","season_story"):collect(item.get(key))
            return result
        else:keys=("conclusion","visual_role","review_question")
        return [str(item[key]) for key in keys if key in item]
    for section in (*DOMAIN_SECTIONS,"visual_models"):
        for item in report.get(section,[]):
            if item.get("element_kind") in {"character_definition","environment_definition","world_environment_definition"}:values.extend(visible(item))
            elif section=="visual_models":
                values.extend(str(item[key]) for key in ("visual_role","conclusion","text_alternative") if key in item)
                values.extend(str(node["label"]) for node in item.get("nodes",[]));values.extend(str(edge["label"]) for edge in item.get("edges",[]))
            else:
                values.extend(str(item[key]) for key in ("conclusion","visual_role") if key in item)
                if section=="open_items_constraints_and_lld_boundary" and "review_question" in item:values.append(str(item["review_question"]))
    text=" ".join(values);cjk=len(CJK.findall(text));latin=len(LATIN.findall(text));visuals=len(report["visual_models"]);minutes=round(cjk/500+latin/250+visuals*.25,4)
    return {"cjk_characters":cjk,"latin_words":latin,"visual_count":visuals,"estimated_read_minutes":minutes}

def validate_draft(context:Context,draft:Path,machine:Mapping[str,Any],models:Mapping[str,Any],report:Mapping[str,Any],producer:Mapping[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    if {path.name for path in draft.iterdir()}!={"canonical.json","review-session.json"}:raise InternalCondition("revise","HH1B_DRAFT_CLOSURE","draft must contain canonical.json and review-session.json only")
    review=read_json(draft/"canonical.json");session=read_json(draft/"review-session.json");context.catalog.validate(review,"presentation-fidelity-review.schema.json");context.catalog.validate(session,"hh1-b-review-session.schema.json")
    allow=context.work_order["file_allowlist"]
    if session["declared_allowlist"]!=allow or session["actual_read_refs"]!=allow:raise InternalCondition("revise","HH1B_READ_CLOSURE_DRIFT","declared and actual reads must exactly equal ordered allowlist")
    a_task=producer["a_work"]["task_id"]
    expected_refs={"hp1_package_ref":next(item for item in allow if item["role"]=="novel_hld_package"),"candidate_report_ref":next(item for item in allow if item["role"]=="human_review_report"),"candidate_manifest_ref":next(item for item in allow if item["role"]=="hh1_a_manifest"),"producer_session_ref":next(item for item in allow if item["role"]=="hh1_a_generation_session"),"producer_work_order_ref":next(item for item in allow if item["role"]=="hh1_a_work_order")}
    if any(session[key]!=value for key,value in expected_refs.items()) or session["review_task_id"]!=context.work_order["task_id"] or session["producer_task_id"]!=a_task or a_task==context.work_order["task_id"]:raise InternalCondition("revise","HH1B_SESSION_BINDING_DRIFT","review session identity/reference binding mismatch")
    expected_bindings={"hp1_package_sha256":sha256(context.roles["novel_hld_package"]),"report_sha256":sha256(context.roles["human_review_report"]),"report_manifest_sha256":sha256(context.roles["hh1_a_manifest"]),"assembler_task_id":a_task,"reviewer_task_id":context.work_order["task_id"]}
    if review["review_bindings"]!=expected_bindings or (review["hld_run_id"],review["revision"])!=(context.work_order["hld_run_id"],context.work_order["revision"]):raise InternalCondition("revise","HH1B_REVIEW_BINDING_DRIFT","canonical review identity/bindings mismatch")
    elements=_all_elements(report);element_ids={item["id"] for item in elements};source_bindings={(item["report_element_id"],item["source_id"],item["locator"]) for item in report["source_bindings"]};sources={source for _,source,_ in source_bindings};locators={locator for _,_,locator in source_bindings};binding_index=producer["binding_index"];required={locator for _,locator in binding_index}
    runtime_missing=required-locators
    relation_sections=("overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","time_space_pacing_tension","key_scene_functions","chapter_definitions")
    dimension_ids={"fact_fidelity":element_ids,"coverage_fidelity":element_ids,"structure_and_relation_fidelity":{item["id"] for section in relation_sections for item in report[section]},"authority_and_open_item_fidelity":{item["id"] for item in report["open_items_constraints_and_lld_boundary"]},"visual_data_fidelity":{item["id"] for item in report["visual_models"]}}
    for dimension in DIMENSIONS:
        value=review[dimension];expected_ids=dimension_ids[dimension];expected_sources,expected_locators=_evidence_for(report,binding_index,expected_ids)
        if set(value["report_element_ids"])!=expected_ids or set(value["source_ids"])!=expected_sources or set(value["locators"])!=expected_locators:raise InternalCondition("revise","HH1B_DIMENSION_EVIDENCE_NOT_EXACT",dimension,[dimension])
    codes=[item["question_code"] for item in review["decision_retrieval_tests"]]
    if set(codes)!=QUESTIONS or len(codes)!=len(QUESTIONS):raise InternalCondition("revise","HH1B_RETRIEVAL_SET_DRIFT","retrieval tests must be the exact ten-code set")
    for item in review["decision_retrieval_tests"]:
        expected_ids={entry["id"] for entry in report[QUESTION_SECTIONS[item["question_code"]]]};expected_sources,expected_locators=_evidence_for(report,binding_index,expected_ids)
        if set(item["report_element_ids"])!=expected_ids or set(item["source_ids"])!=expected_sources or set(item["locators"])!=expected_locators:raise InternalCondition("revise","HH1B_RETRIEVAL_EVIDENCE_NOT_EXACT",item["question_code"],[item["question_code"]])
    recomputed=_budget(report);declared={key:report["review_budget"][key] for key in ("cjk_characters","latin_words","visual_count","estimated_read_minutes")};budget=review["reading_budget_validation"]
    if budget["declared"]!=declared or budget["recomputed"]!=recomputed or (budget["verdict"]=="pass")!=(declared==recomputed and recomputed["estimated_read_minutes"]<=18):raise InternalCondition("revise","HH1B_BUDGET_EVIDENCE_DRIFT","reading budget evidence/algebra mismatch")
    failed_retrieval={item["question_code"] for item in review["decision_retrieval_tests"] if item["verdict"]=="fail"}
    if review["cognitive_overload_findings"] and not failed_retrieval and budget["verdict"]=="pass":raise InternalCondition("revise","HH1B_PREFERENCE_AS_FAILURE","cognitive/style preference cannot be a hard failure without retrieval or budget impact")
    all_pass=not runtime_missing and all(review[name]["verdict"]=="pass" for name in DIMENSIONS) and not review["material_drift_findings"] and not review["cognitive_overload_findings"] and not failed_retrieval and budget["verdict"]=="pass"
    if review["verdict"]=="pass" and (review["defect_origin"]!="none" or not all_pass):raise InternalCondition("revise","HH1B_FALSE_PASS",f"pass contradicted by runtime checks; missing={sorted(runtime_missing)}")
    if review["verdict"]=="revise" and review["defect_origin"]!="reviewer_local":raise InternalCondition("revise","HH1B_VERDICT_ALGEBRA","revise must own reviewer_local")
    if review["verdict"]=="fail" and (review["defect_origin"]!="upstream_content" or all_pass):raise InternalCondition("revise","HH1B_VERDICT_ALGEBRA","fail must identify material upstream_content evidence")
    return review,session

def build_ready(context:Context,staging:Path,review:Mapping[str,Any],session:Mapping[str,Any])->dict[str,Any]:
    staging.mkdir(parents=True,exist_ok=False);write_json(staging/SPEC.canonical_name,review);write_json(staging/SPEC.session_name,session)
    execution={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"producer_task_id":session["producer_task_id"],"implementation_sha256":impl_hash(),"actual_read_hashes":{role:sha256(path) for role,path in sorted(context.roles.items())},"review_sha256":sha256(staging/SPEC.canonical_name),"deterministic":True}
    context.catalog.validate(execution,"hh1-b-execution.schema.json");write_json(staging/SPEC.execution_name,execution)
    validation={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"status":"pass","checks":["exact-read-closure","task-isolation","bidirectional-material-coverage","world-character-place-definition-fidelity","dimension-evidence-binding","ten-retrieval-tests","budget-recount","preference-not-hard-failure","deterministic-reproduction"],"errors":[]}
    context.catalog.validate(validation,"hh1-b-validation.schema.json");write_json(staging/"validation.json",validation)
    return finalize_ready(context,staging,{SPEC.canonical_name:SPEC.canonical_role,SPEC.session_name:"review_session",SPEC.execution_name:"execution_record","validation.json":"validation"})

def affected(review:Mapping[str,Any])->list[str]:
    ids=[]
    for finding in review.get("material_drift_findings",[]):ids.extend(finding.get("affected_report_element_ids",[]))
    for finding in review.get("cognitive_overload_findings",[]):ids.extend(finding.get("affected_report_element_ids",[]))
    ids.extend(item["question_code"] for item in review.get("decision_retrieval_tests",[]) if item.get("verdict")=="fail")
    return sorted(set(ids))

def execute(work_order:Path,draft:Path)->tuple[int,dict[str,Any]]:
    context=load_context(work_order,SPEC,impl_hash(),_catalog())
    def build(ctx:Context,staging:Path):
        try:
            try:machine,models,report,producer=admit(ctx)
            except ContractError as error:raise InternalCondition("blocked","HH1B_UPSTREAM_SCHEMA_INVALID",str(error),["HP1","HH1-A"]) from error
            try:review,session=validate_draft(ctx,draft.resolve(strict=True),machine,models,report,producer)
            except ContractError as error:raise InternalCondition("revise","HH1B_DRAFT_SCHEMA_INVALID",str(error)) from error
            if review["verdict"]=="pass":return 0,build_ready(ctx,staging,review,session)
            if review["verdict"]=="fail":return 2,finalize_condition(ctx,staging,InternalCondition("blocked","HH1B_UPSTREAM_CONTENT_DEFECT","presentation fidelity review found material report drift",affected(review)),review)
            return 2,finalize_condition(ctx,staging,InternalCondition("revise","HH1B_REVIEWER_LOCAL_DEFECT","review evidence requires bounded local regeneration",affected(review)),review)
        except InternalCondition as condition:return 2,finalize_condition(ctx,staging,condition,read_json(draft/"canonical.json") if (draft/"canonical.json").is_file() else None)
        except Exception as error:return 1,finalize_runtime_error(ctx,staging,error,"HH1-B admission/review validation/sealing")
    return atomic_execute(context,build)

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("work_order",type=Path);parser.add_argument("draft_dir",type=Path);args=parser.parse_args(argv)
    try:code,_=execute(args.work_order,args.draft_dir);return code
    except Exception as error:print(str(error),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
