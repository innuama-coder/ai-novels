#!/usr/bin/env python3
"""Public HH1-A hybrid runtime: admit HP1/HQ2, validate a semantic draft, seal atomically."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

SKILL_ROOT=Path(__file__).resolve().parents[1];REPO=SKILL_ROOT.parents[1];HARNESS_ROOT=REPO/"harnesses/novel-hld-autonomous"
sys.path.insert(0,str(HARNESS_ROOT))
from runtime.canonical import ContractError, canonical_sha256, json_pointer, read_json, write_json  # noqa:E402
from runtime.composite_internal_runtime import (Context,InternalCondition,InternalRuntimeError,Spec,atomic_execute,catalog,finalize_condition,finalize_ready,finalize_runtime_error,implementation_sha256,load_context,sha256)  # noqa:E402

SKILL="novel-hld-review-report-assembler";VERSION="1.0.0"
MODEL_ROLES={
 "hld_model_ha1":"canonical-models/narrative-architecture.json","hld_model_hs1":"canonical-models/storyline-choreography.json",
 "hld_model_hc1":"canonical-models/character-arc-placement.json","hld_model_hi1":"canonical-models/narrative-information-architecture.json",
 "hld_model_hr1":"canonical-models/rhythm-continuity-architecture.json","hld_model_hk1":"canonical-models/key-scene-function-map.json",
}
HP1_PACKAGE_SCHEMA=REPO/"skills/novel-hld-package-assembler/references/novel-hld-package.schema.json"
HP1_CROSS_INDEX_SCHEMA=REPO/"skills/novel-hld-package-assembler/references/hld-cross-index.schema.json"
REQUIRED_ROLES=("hb0_completion","hb0_manifest","hld_control_baseline","hp1_completion","hp1_manifest","hp1_validation","novel_hld_package","hld_cross_index","hld_traceability_matrix","hld_spec",*MODEL_ROLES,"hq2_completion","hq2_manifest","hq2_validation","lld_handoff_acceptance")
SPEC=Spec(SKILL,VERSION,"HH1.A","hld-human-review-report.json","human_review_report","generation-session.json","report-assembly-execution.json","hh1-a-validation.schema.json",REQUIRED_ROLES,True)
DOMAIN_BY_ROLE={"hld_model_ha1":"overall_narrative_architecture","hld_model_hs1":"storyline_choreography","hld_model_hc1":"character_arc_placement","hld_model_hi1":"pov_information_suspense","hld_model_hr1":"time_space_pacing_tension","hld_model_hk1":"key_scene_functions"}
DOMAIN_SECTIONS=("overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","pov_information_suspense","time_space_pacing_tension","key_scene_functions","open_items_constraints_and_lld_boundary")
WORLD_ENVIRONMENT_SCOPES={"city_and_region","local_people_and_daily_life","social_order_and_public_atmosphere","technology_and_infrastructure","climate_and_physical_environment"}
IDENTITY_FIELDS={"schema_version","skill","stage","hld_run_id","status","input_gate_ref","source_artifacts","derivation_claims","decision_dependencies"}
CJK=re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]");LATIN=re.compile(r"\b[A-Za-z]+(?:['’][A-Za-z]+)*\b")
AUTHOR_PROSE_FORBIDDEN=re.compile(
    r"(?:高层设计|详细设计|人审(?:稿|报告)?|评审(?:范围|方法|问题)?|审阅(?:范围|方法)?|设计入口|场景任务|"
    r"(?:证据|责任|授权|决策|核验|行动)链|闭环|闭合(?:整条|整个)|(?:活动|数字|秘密项目)载体|"
    r"(?:当前|活动|不活动)实例|(?:行动|原因|输入|输出)层|可执行|不可执行|可追责|审计|核验|权限|"
    r"接口|原子记录|只写|只读输入|post-dispatch|人物变化：|出场时：|结尾时：|主要风险：|"
    r"进入时处于|关键变化后达到|不可替代职责|(?:顾衡|沈逾|R-07|现实调查|两国)线负责|"
    r"保持开放|回收落点|证据入口|映射|投影|链路|抓手|维度|颗粒度|赋能|沉淀|对齐|拉通|兜底|"
    r"方法论|范式|结构化输出|职责分工|能力边界|信息边界|决策点|控制点|状态机|工作流|流水线|"
    r"上下游|生产者|消费者|检索召回)",re.I)
SCHEMA_NAMES=("hld-human-review-report.schema.json","hh1-a-generation-session.schema.json","hh1-a-material-inventory.schema.json","hh1-a-organization.schema.json","hh1-a-adversarial-review.schema.json","hh1-a-execution.schema.json","hh1-a-validation.schema.json")

def schema_paths():return [*(SKILL_ROOT/"references"/name for name in SCHEMA_NAMES),HP1_PACKAGE_SCHEMA,HP1_CROSS_INDEX_SCHEMA]
def implementation_paths():return [Path(__file__),SKILL_ROOT/"scripts/run_skill.py",SKILL_ROOT/"references/runtime-contract.json",HARNESS_ROOT/"runtime/composite_internal_runtime.py",HARNESS_ROOT/"runtime/canonical.py",HARNESS_ROOT/"runtime/package_envelope.py",HARNESS_ROOT/"runtime/schema_catalog.py",*sorted((HARNESS_ROOT/"schemas").glob("*.schema.json")),*schema_paths()]
def impl_hash():return implementation_sha256(implementation_paths())
def _catalog():return catalog(HARNESS_ROOT,schema_paths())

def _member(manifest:Mapping[str,Any],path:Path,package:Path)->bool:
    try:relative=path.resolve(strict=True).relative_to(package.resolve(strict=True)).as_posix()
    except ValueError:return False
    return sum(1 for item in manifest.get("files",[]) if item.get("path")==relative and item.get("sha256")==sha256(path))==1

def _artifact(ref:Mapping[str,Any],main:Path,manifest:Path,completion:Path,workspace:Path)->bool:
    return ref=={"path":main.relative_to(workspace).as_posix(),"sha256":sha256(main),"manifest_path":manifest.relative_to(workspace).as_posix(),"manifest_sha256":sha256(manifest),"completion_path":completion.relative_to(workspace).as_posix(),"completion_sha256":sha256(completion)}

def admit(context:Context)->dict[str,Any]:
    if len(context.work_order["upstream_completions"])!=3:raise InternalCondition("blocked","HH1A_UPSTREAM_TOPOLOGY","expected ordered HB0, HP1, HQ2",blocker_class="input_invalid")
    machine=read_json(context.roles["novel_hld_package"]);hp1_manifest=read_json(context.roles["hp1_manifest"]);hp1_completion=read_json(context.roles["hp1_completion"]);hp1_validation=read_json(context.roles["hp1_validation"])
    q2=read_json(context.roles["lld_handoff_acceptance"]);q2_manifest=read_json(context.roles["hq2_manifest"]);q2_completion=read_json(context.roles["hq2_completion"]);q2_validation=read_json(context.roles["hq2_validation"]);hb0_completion=read_json(context.roles["hb0_completion"]);hb0_manifest=read_json(context.roles["hb0_manifest"]);baseline=read_json(context.roles["hld_control_baseline"])
    for value,schema in ((hp1_manifest,"package-manifest.schema.json"),(hp1_completion,"stage-completion.schema.json"),(q2,"lld-handoff-acceptance.schema.json"),(q2_manifest,"package-manifest.schema.json"),(q2_completion,"stage-completion.schema.json"),(hb0_completion,"stage-completion.schema.json"),(hb0_manifest,"package-manifest.schema.json"),(baseline,"hld-control-baseline.schema.json")):
        context.catalog.validate(value,schema)
    run=context.work_order["hld_run_id"]
    if (machine.get("stage"),machine.get("hld_run_id"),machine.get("status"))!=("HP1",run,"ready") or hp1_completion.get("stage")!="HP1" or hp1_completion.get("hld_run_id")!=run or hp1_validation.get("status")!="pass":raise InternalCondition("blocked","HH1A_HP1_NOT_CURRENT_READY","HP1 identity/validation mismatch",["HP1"])
    if (q2.get("stage"),q2.get("hld_run_id"),q2.get("status"))!=("HQ2",run,"ready") or q2_completion.get("stage")!="HQ2" or q2_completion.get("hld_run_id")!=run or q2_validation.get("status")!="pass":raise InternalCondition("blocked","HH1A_HQ2_NOT_CURRENT_READY","HQ2 identity/validation mismatch",["HQ2"])
    if hp1_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hp1_manifest"]) or hp1_completion["validation_ref"]["sha256"]!=sha256(context.roles["hp1_validation"]):raise InternalCondition("blocked","HH1A_HP1_ENVELOPE_DRIFT","HP1 completion bindings drift",["HP1"])
    if q2_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hq2_manifest"]) or q2_completion["validation_ref"]["sha256"]!=sha256(context.roles["hq2_validation"]):raise InternalCondition("blocked","HH1A_HQ2_ENVELOPE_DRIFT","HQ2 completion bindings drift",["HQ2"])
    for role in ("novel_hld_package","hld_cross_index","hld_traceability_matrix","hld_spec",*MODEL_ROLES):
        if not _member(hp1_manifest,context.roles[role],context.roles["hp1_manifest"].parent):raise InternalCondition("blocked","HH1A_HP1_MEMBER_UNSEALED",role,[role])
    for role in ("lld_handoff_acceptance","hq2_validation"):
        if not _member(q2_manifest,context.roles[role],context.roles["hq2_manifest"].parent):raise InternalCondition("blocked","HH1A_HQ2_MEMBER_UNSEALED",role,[role])
    if not _artifact(context.work_order["upstream_completions"][1],context.roles["novel_hld_package"],context.roles["hp1_manifest"],context.roles["hp1_completion"],context.workspace):raise InternalCondition("blocked","HH1A_HP1_ARTIFACT_DRIFT","work-order HP1 artifact differs from sealed inputs",["HP1"])
    if not _artifact(context.work_order["upstream_completions"][2],context.roles["lld_handoff_acceptance"],context.roles["hq2_manifest"],context.roles["hq2_completion"],context.workspace):raise InternalCondition("blocked","HH1A_HQ2_ARTIFACT_DRIFT","work-order HQ2 artifact differs from sealed inputs",["HQ2"])
    hb=context.work_order["upstream_completions"][0]
    if hb.get("completion_path")!=context.roles["hb0_completion"].relative_to(context.workspace).as_posix() or hb.get("completion_sha256")!=sha256(context.roles["hb0_completion"]):raise InternalCondition("blocked","HH1A_HB0_ARTIFACT_DRIFT","HB0 completion binding drift",["HB0"])
    if hb0_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hb0_manifest"]) or not _member(hb0_manifest,context.roles["hld_control_baseline"],context.roles["hb0_manifest"].parent):raise InternalCondition("blocked","HH1A_HB0_BASELINE_UNSEALED","HB0 control baseline is not current and uniquely sealed",["HB0"])
    if q2["hp1_completion_ref"]!={"role":q2["hp1_completion_ref"]["role"],"path":context.roles["hp1_completion"].relative_to(context.workspace).as_posix(),"sha256":sha256(context.roles["hp1_completion"])} or q2["hb0_completion_ref"]["sha256"]!=sha256(context.roles["hb0_completion"]):raise InternalCondition("blocked","HH1A_Q2_BASELINE_BINDING_DRIFT","HQ2 does not bind current HP1/HB0",["HQ2"])
    context.catalog.validate(machine,HP1_PACKAGE_SCHEMA.name)
    cross_index=read_json(context.roles["hld_cross_index"]);context.catalog.validate(cross_index,HP1_CROSS_INDEX_SCHEMA.name)
    models={role:read_json(context.roles[role]) for role in MODEL_ROLES}
    expected_stages={role[10:].upper() for role in MODEL_ROLES}
    if {value.get("stage") for value in models.values()}!=expected_stages or any(value.get("hld_run_id")!=run or value.get("status")!="ready" for value in models.values()):raise InternalCondition("blocked","HH1A_CANONICAL_IDENTITY_DRIFT","one or more HP1 canonical-model copies are not current ready",sorted(expected_stages))
    documents={"novel-hld-package.json":machine,**{MODEL_ROLES[role]:value for role,value in models.items()}}
    binding_index={}
    for item in cross_index["entries"]:
        model_path=item["model_path"];locator=f"{model_path}#{item['locator']}";key=(item["id"],locator)
        if model_path not in documents or key in binding_index or canonical_sha256(json_pointer(documents[model_path],item["locator"]))!=item["value_sha256"]:raise InternalCondition("blocked","HH1A_CROSS_INDEX_VALUE_DRIFT",f"cross-index entry is not a unique value-bound locator: {item['id']}",[item["id"]])
        binding_index[key]=item
    character_ids=[item.get("character_id") for item in models["hld_model_hc1"].get("character_participation_register",[])]
    environment_ids=list(dict.fromkeys(environment_id for item in models["hld_model_hk1"].get("key_scene_functions",[]) for environment_id in item.get("environment_refs",[])))
    if not character_ids or len(character_ids)!=len(set(character_ids)) or any(not isinstance(value,str) for value in character_ids):raise InternalCondition("blocked","HH1A_CHARACTER_ENTITY_SET_INVALID","HC1 must provide one unique canonical character identity per participation record",["HC1"])
    if not environment_ids or any(not isinstance(value,str) for value in environment_ids):raise InternalCondition("blocked","HH1A_ENVIRONMENT_ENTITY_SET_INVALID","HK1 must place at least one canonical environment identity",["HK1"])
    definitions=_definition_controls(baseline,character_ids=character_ids,environment_ids=environment_ids)
    return {"machine":machine,"models":models,"baseline":baseline,"definitions":definitions,"hp1_completion":hp1_completion,"q2":q2,"cross_entries":cross_index["entries"],"binding_index":binding_index}

def material_locator_map(admitted:Mapping[str,Any])->dict[str,str]:
    by_path={name:DOMAIN_BY_ROLE[role] for role,name in MODEL_ROLES.items()};by_path["novel-hld-package.json"]="open_items_constraints_and_lld_boundary"
    character_ids=set(admitted.get("definitions",{}).get("character_definitions",{}));environment_ids=set(admitted.get("definitions",{}).get("environment_definitions",{}));world_environment_ids=set(admitted.get("definitions",{}).get("world_environment_definitions",{}))
    result={}
    for item in admitted["cross_entries"]:
        owner=by_path[item["model_path"]]
        if item["model_path"]=="novel-hld-package.json" and item["id"] in character_ids:owner="character_definitions"
        elif item["model_path"]=="novel-hld-package.json" and item["id"] in environment_ids:owner="environment_definitions"
        elif item["model_path"]=="novel-hld-package.json" and item["id"] in world_environment_ids:owner="world_environment_definitions"
        result[f"{item['model_path']}#{item['locator']}"]=owner
    return result

def _definition_controls(baseline:Mapping[str,Any],*,character_ids:list[str]|None=None,environment_ids:list[str]|None=None)->dict[str,dict[str,dict[str,Any]]]:
    result={"world_environment_definitions":{},"character_definitions":{},"environment_definitions":{}}
    for control in baseline.get("control_registry",[]):
        if not isinstance(control,dict) or not isinstance(control.get("source_text"),str):continue
        source_id=control.get("source_id")
        text=control["source_text"]
        try:value=json.loads(text)
        except (TypeError,ValueError):value=None
        if isinstance(value,dict) and value.get("id")==source_id:
            if control.get("domain")=="characters" and isinstance(value.get("individual_definition"),dict) and isinstance(value.get("story_position"),dict):result["character_definitions"][source_id]=value
            elif control.get("domain")=="environments" and isinstance(value.get("narrative_responsibility"),str) and isinstance(value.get("scope"),str):result["environment_definitions"][source_id]=value
        elif control.get("domain")=="characters" and isinstance(source_id,str) and source_id.startswith("CHR-") and "### 可观察行为" in text and "位置" in text:
            result["character_definitions"][source_id]={"id":source_id,"authoritative_markdown":text}
        if control.get("domain")=="world" and control.get("authority_class")=="author_locked" and isinstance(source_id,str):
            result["world_environment_definitions"][source_id]={"id":source_id,"authoritative_text":text}
    if not result["world_environment_definitions"]:
        fallback=next((control for control in baseline.get("control_registry",[]) if isinstance(control,dict) and control.get("authority_class")=="author_locked" and control.get("domain") not in {"characters","environments"} and isinstance(control.get("source_id"),str) and isinstance(control.get("source_text"),str)),None)
        if fallback:result["world_environment_definitions"][fallback["source_id"]]={"id":fallback["source_id"],"authoritative_text":fallback["source_text"]}
    for section,expected,code,label in (
        ("character_definitions",character_ids,"HH1A_CHARACTER_DEFINITION_SOURCE_DRIFT","HC1 character"),
        ("environment_definitions",environment_ids,"HH1A_ENVIRONMENT_DEFINITION_SOURCE_DRIFT","HK1 environment"),
    ):
        if expected is None:continue
        missing=[source_id for source_id in expected if source_id not in result[section]]
        if missing:raise InternalCondition("blocked",code,f"HB0 lacks exact definitions for current {label} entities",missing)
        result[section]={source_id:result[section][source_id] for source_id in expected}
    if not result["world_environment_definitions"] or not result["character_definitions"] or not result["environment_definitions"]:raise InternalCondition("blocked","HH1A_DEFINITION_BASELINE_EMPTY","HB0 must provide world, character, and place definitions",["HB0"])
    return result

def _all_elements(report:Mapping[str,Any])->list[dict[str,Any]]:
    result=[]
    for section in ("title_and_decision_scope",*DOMAIN_SECTIONS,"visual_models"):
        value=report.get(section,[])
        if isinstance(value,list):result.extend(item for item in value if isinstance(item,dict))
    return result

def _definition_visible_values(item:Mapping[str,Any])->list[str]:
    if item.get("element_kind")=="character_definition":
        keys=("name","conclusion","story_position","personality_and_motivation","capabilities_and_limits","relationships_and_change")
    elif item.get("element_kind")=="environment_definition":
        keys=("name","conclusion","story_function","physical_character","access_and_limits","dramatic_use")
    elif item.get("element_kind")=="world_environment_definition":
        keys=("name","definition","people_and_daily_life","story_pressure_and_limits")
        values=[str(item[key]) for key in keys if key in item]
        def collect(value:Any)->None:
            if isinstance(value,str):values.append(value)
            elif isinstance(value,list):
                for child in value:collect(child)
            elif isinstance(value,Mapping):
                for child in value.values():collect(child)
        # Exact source projections stay in the report for traceability.  Only the
        # separately authored reader stories belong to the human-visible layer.
        for key in ("defining_features","author_open_details","city_stories","route_stories","ordinary_people_stories","season_story"):
            collect(item.get(key))
        return values
    elif item.get("element_kind")=="chapter_design":
        values=[str(item[key]) for key in ("chapter_title","core_content","chapter_end_change")]
        values.extend(str(storyline["name"]) for storyline in item["storylines"])
        return values
    else:
        keys=("conclusion","visual_role","review_question")
    return [str(item[key]) for key in keys if key in item]

def _author_visible_values(report:Mapping[str,Any])->list[tuple[str,str]]:
    values=[]
    for section in DOMAIN_SECTIONS:
        for item in report.get(section,[]):
            if item.get("element_kind") in {"character_definition","environment_definition","world_environment_definition","chapter_design"}:
                item_values=_definition_visible_values(item)
            else:
                item_values=[str(item[key]) for key in ("visual_role","conclusion") if key in item]
                if section=="open_items_constraints_and_lld_boundary" and item.get("review_question"):
                    item_values.append(str(item["review_question"]))
            values.extend((f"{section}:{item.get('id','')}:{index}",value.strip()) for index,value in enumerate(item_values) if value.strip())
    for item in report.get("visual_models",[]):
        for key in ("visual_role","conclusion","text_alternative"):
            if item.get(key):values.append((f"visual_models:{item.get('id','')}:{key}",str(item[key]).strip()))
        for index,node in enumerate(item.get("nodes",[])):
            values.append((f"visual_models:{item.get('id','')}:node:{index}",str(node.get("label","")).strip()))
        for index,edge in enumerate(item.get("edges",[])):
            values.append((f"visual_models:{item.get('id','')}:edge:{index}",str(edge.get("label","")).strip()))
    return [(path,value) for path,value in values if value]

def _validate_author_language(report:Mapping[str,Any])->None:
    seen={};errors=[]
    for path,value in _author_visible_values(report):
        if AUTHOR_PROSE_FORBIDDEN.search(value):errors.append(f"{path} uses machine/process wording")
        if CJK.search(value) and value.count("；")>=3:errors.append(f"{path} compresses too many conclusions into one sentence")
        for sentence in re.split(r"[。！？!?]",value):
            if len(CJK.findall(sentence))>90:errors.append(f"{path} contains an overlong compressed sentence")
        normalized=re.sub(r"\s+","",value).strip("。；，：、!?！？")
        if len(CJK.findall(normalized))>=12:
            previous=seen.get(normalized)
            if previous is not None:errors.append(f"{path} repeats substantive copy from {previous}")
            else:seen[normalized]=path
    if errors:raise InternalCondition("revise","HH1A_AUTHOR_LANGUAGE_INVALID","; ".join(errors[:12]))

def _world_authority_projection(admitted:Mapping[str,Any])->dict[str,Any]:
    world=admitted["models"]["hld_model_ha1"].get("world_setting_architecture")
    if not isinstance(world,Mapping):
        raise InternalCondition("blocked","HH1A_WORLD_AUTHORITY_MISSING","HA1 has no machine-authoritative world setting; HH1 must not invent cities, residents, season, routes, or threat mechanics",["HA1"])
    city_names={item["city_id"]:item["name"] for item in world["cities"]}
    cities=[{key:value for key,value in {
        "city_name":item["name"],"country":item["country"],"jurisdiction":item["jurisdiction"],"story_function":item["story_function"],"city_scale":item["city_scale"],"urban_structure":item["urban_structure"],"street_and_architecture":item["street_and_architecture"],"transport_and_daily_rhythm":item["transport_and_daily_rhythm"],"seasonal_expression":item["seasonal_expression"],"key_story_events":item["key_story_events"],
    }.items()} for item in world["cities"]]
    routes=[{"from_city":city_names[item["from_city_id"]],"to_city":city_names[item["to_city_id"]],"travel_time":item["travel_time"],"physical_route":item["physical_route"],"information_route":item["information_route"],"custody_rule":item["custody_rule"],"story_function":item["story_function"]} for item in world["intercity_routes"]]
    portraits=[]
    for city in world["cities"]:
        for item in city["ordinary_people"]:
            portraits.append({"portrait_name":item["portrait"],"city":city["name"],"who_they_are":item["portrait"],"daily_routine":item["daily_routine"],"material_details":item["material_details"],"crisis_exposure":item["crisis_exposure"],"knowledge_boundary":item["knowledge_boundary"]})
    season={"season":world["season_profile"]["season"],"story_window":world["story_window"],"temperature_and_weather":world["season_profile"]["temperature_and_weather"],"daylight_and_air":world["season_profile"]["daylight_and_air"],"daily_effects":world["season_profile"]["daily_effects"],"plot_effect":world["season_profile"]["plot_effect"]}
    return {"city_network":{"narrative_distribution":world["narrative_distribution"],"cities":cities,"intercity_links":routes},"ordinary_people_portraits":portraits,"season_profile":season}

def _validate_definition_sections(report:Mapping[str,Any],admitted:Mapping[str,Any])->None:
    material=material_locator_map(admitted)
    model_documents={MODEL_ROLES[role]:value for role,value in admitted["models"].items()}

    def validate_current_supplements(item:Mapping[str,Any],base_source:str)->None:
        for pair in list(zip(item["source_ids"],item["locators"]))[1:]:
            entry=admitted["binding_index"].get(pair)
            if entry is None or entry["model_path"] not in model_documents:
                raise InternalCondition("revise","HH1A_DEFINITION_SUPPLEMENT_INVALID",f"{item['id']} supplemental binding is not a current canonical HLD model",[item["id"]])
            value=json_pointer(model_documents[entry["model_path"]],entry["locator"])
            direct_refs=set(value.get("source_refs",[])) if isinstance(value,Mapping) else set()
            authority_refs={ref.get("source_id") for ref in value.get("source_authority_refs",[]) if isinstance(ref,Mapping)} if isinstance(value,Mapping) else set()
            if base_source not in direct_refs|authority_refs:
                raise InternalCondition("revise","HH1A_DEFINITION_SUPPLEMENT_INVALID",f"{item['id']} supplemental binding is not derived from {base_source}",[item["id"]])

    for section,kind in (("character_definitions","character_definition"),("environment_definitions","environment_definition")):
        expected=admitted["definitions"][section];items=report[section];actual=[item["source_ids"][0] for item in items]
        if len(actual)!=len(set(actual)) or set(actual)!=set(expected):raise InternalCondition("revise","HH1A_DEFINITION_COVERAGE_DRIFT",f"{section} must contain exactly one card for every sealed baseline definition",sorted(set(expected)-set(actual)))
        for item in items:
            source=item["source_ids"][0];locator=item["locators"][0]
            if item["element_kind"]!=kind or material.get(locator)!=section:raise InternalCondition("revise","HH1A_DEFINITION_BINDING_DRIFT",f"{item['id']} is not bound to its exact definition domain",[item["id"]])
            validate_current_supplements(item,source)
            visible=" ".join(_definition_visible_values(item))
            if re.search(r"(?:\[CLASS:|\[DEMAND|\[/DEMAND|\b(?:CHR|ENV|SL|HRE|HVG)-|\b(?:HLD|LLD)\b)",visible,re.I):raise InternalCondition("revise","HH1A_DEFINITION_VISIBLE_JARGON",f"{item['id']} exposes machine-facing vocabulary",[item["id"]])
    world_items=report["world_environment_definitions"]
    authority=_world_authority_projection(admitted);by_scope={item["environment_scope"]:item for item in world_items}
    for scope,key in (("city_and_region","city_network"),("local_people_and_daily_life","ordinary_people_portraits"),("climate_and_physical_environment","season_profile")):
        if by_scope.get(scope,{}).get(key)!=authority[key]:raise InternalCondition("revise","HH1A_WORLD_AUTHORITY_DRIFT",f"{scope}.{key} must be the exact projection of HA1.world_setting_architecture",[by_scope.get(scope,{}).get("id",scope)])
    scopes=[item["environment_scope"] for item in world_items]
    if len(scopes)!=len(set(scopes)) or set(scopes)!=WORLD_ENVIRONMENT_SCOPES:raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_SCOPE_DRIFT","world environment cards must cover the exact five author-facing scopes",sorted(WORLD_ENVIRONMENT_SCOPES-set(scopes)))
    world_sources=set(admitted["definitions"]["world_environment_definitions"])
    if {source for item in world_items for source in item["source_ids"]}!=world_sources:raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_SOURCE_COVERAGE_DRIFT","world environment cards must collectively cover the exact sealed world sources",sorted(world_sources))
    for item in world_items:
        if item["element_kind"]!="world_environment_definition" or any(material.get(locator)!="world_environment_definitions" for locator in item["locators"]):raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_BINDING_DRIFT",f"{item['id']} is not bound to the world environment domain",[item["id"]])
        visible=" ".join(_definition_visible_values(item))
        if re.search(r"(?:\[CLASS:|\[DEMAND|\[/DEMAND|\b(?:WLD|CHR|ENV|SL|HRE|HVG)-|\b(?:HLD|LLD)\b)",visible,re.I):raise InternalCondition("revise","HH1A_DEFINITION_VISIBLE_JARGON",f"{item['id']} exposes machine-facing vocabulary",[item["id"]])
        scope=item["environment_scope"];special={key for key in ("city_network","city_stories","route_stories","ordinary_people_portraits","ordinary_people_stories","season_profile","season_story") if key in item};expected={"city_and_region":{"city_network","city_stories","route_stories"},"local_people_and_daily_life":{"ordinary_people_portraits","ordinary_people_stories"},"climate_and_physical_environment":{"season_profile","season_story"}}.get(scope,set())
        if special!=expected:raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_PROFILE_DRIFT",f"{item['id']} must carry only the structured profile required by {scope}",[item["id"]])
        if any(re.search(r"(?:待定|某(?:座)?城市|城市名称|具体城市|某个季节|季节待定|职业构成待定)",text) for text in _definition_visible_values(item)):raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_PLACEHOLDER",f"{item['id']} leaves a required world definition generic",[item["id"]])
        if any(re.search(r"(?:城市(?:名称)?|季节|普通人|居民画像|职业构成).*(?:开放|决定|待定)",text) for text in item["author_open_details"]):raise InternalCondition("revise","HH1A_WORLD_ENVIRONMENT_REOPENED",f"{item['id']} reopens a required city, season, or resident decision",[item["id"]])
        if scope=="city_and_region":
            network=item["city_network"];cities=network["cities"];names=[city["city_name"] for city in cities]
            if len(cities)<4 or len(names)!=len(set(names)) or any(len(city["urban_structure"])<2 for city in cities):raise InternalCondition("revise","HH1A_CITY_NETWORK_SHALLOW",f"{item['id']} needs four distinct, internally defined cities",[item["id"]])
            links=network["intercity_links"]
            if len(links)<4 or any(link["from_city"] not in names or link["to_city"] not in names or link["from_city"]==link["to_city"] for link in links):raise InternalCondition("revise","HH1A_INTERCITY_LINK_INVALID",f"{item['id']} has missing, dangling, or self-referential city links",[item["id"]])
            reached={names[0]}
            while True:
                expanded=reached|{link["to_city"] for link in links if link["from_city"] in reached}|{link["from_city"] for link in links if link["to_city"] in reached}
                if expanded==reached:break
                reached=expanded
            if reached!=set(names):raise InternalCondition("revise","HH1A_CITY_NETWORK_DISCONNECTED",f"{item['id']} contains a city that cannot participate in the story network",sorted(set(names)-reached))
            stories=item["city_stories"];story_names=[story["city_name"] for story in stories]
            if len(story_names)!=len(set(story_names)) or set(story_names)!=set(names):raise InternalCondition("revise","HH1A_CITY_STORY_COVERAGE_DRIFT",f"{item['id']} needs one reader story for every city",sorted(set(names)-set(story_names)))
            route_keys={(link["from_city"],link["to_city"]) for link in links};story_routes=[(story["from_city"],story["to_city"]) for story in item["route_stories"]]
            if len(story_routes)!=len(set(story_routes)) or set(story_routes)!=route_keys:raise InternalCondition("revise","HH1A_ROUTE_STORY_COVERAGE_DRIFT",f"{item['id']} needs one reader story for every route")
        elif scope=="local_people_and_daily_life":
            portraits=item["ordinary_people_portraits"];names=[portrait["portrait_name"] for portrait in portraits]
            if len(portraits)<4 or len(names)!=len(set(names)):raise InternalCondition("revise","HH1A_ORDINARY_PEOPLE_SHALLOW",f"{item['id']} needs four distinct ordinary-person portraits",[item["id"]])
            portrait_keys={(portrait["portrait_name"],portrait["city"]) for portrait in portraits};story_keys=[(story["portrait_name"],story["city"]) for story in item["ordinary_people_stories"]]
            if len(story_keys)!=len(set(story_keys)) or set(story_keys)!=portrait_keys:raise InternalCondition("revise","HH1A_ORDINARY_PEOPLE_STORY_COVERAGE_DRIFT",f"{item['id']} needs one reader story for every ordinary-person portrait")
        elif scope=="climate_and_physical_environment":
            profile=item["season_profile"]
            if not profile["season"].strip() or not profile["story_window"].strip():raise InternalCondition("revise","HH1A_SEASON_PROFILE_SHALLOW",f"{item['id']} lacks a concrete season and story window",[item["id"]])
    by_scope={item["environment_scope"]:item for item in world_items};city_names={city["city_name"] for city in by_scope["city_and_region"]["city_network"]["cities"]};portrait_cities={portrait["city"] for portrait in by_scope["local_people_and_daily_life"]["ordinary_people_portraits"]}
    if portrait_cities!=city_names:raise InternalCondition("revise","HH1A_CITY_RESIDENT_COVERAGE_DRIFT","ordinary-person portraits must cover every and only defined city",sorted(city_names-portrait_cities))

def _validate_chapter_designs(report:Mapping[str,Any],admitted:Mapping[str,Any])->None:
    hs1=admitted["models"]["hld_model_hs1"]
    chapters=hs1.get("chapter_storyline_plan")
    if not isinstance(chapters,list) or not chapters:
        raise InternalCondition("blocked","HH1A_CHAPTER_DESIGN_MISSING","HS1 does not contain chapter-level design",["HS1"])
    reader_names={item["source_storyline_id"]:item["reader_name"] for item in hs1["semantic_storyline_register"]}
    cards=[item for item in report["storyline_choreography"] if item.get("element_kind")=="chapter_design"]
    if len(cards)!=len(chapters):
        raise InternalCondition("revise","HH1A_CHAPTER_CARD_COVERAGE_DRIFT","the reader report needs exactly one chapter card for every chapter design",[item["id"] for item in chapters])
    chapter_locators={f"canonical-models/storyline-choreography.json#/chapter_storyline_plan/{index}" for index in range(len(chapters))}
    other_locators={locator for item in report["storyline_choreography"] if item.get("element_kind")!="chapter_design" for locator in item["locators"]}
    if chapter_locators & other_locators:
        raise InternalCondition("revise","HH1A_CHAPTER_CARD_BINDING_AMBIGUOUS","chapter design locators must appear only on chapter cards")
    for index,(chapter,card) in enumerate(zip(chapters,cards),1):
        locator=f"canonical-models/storyline-choreography.json#/chapter_storyline_plan/{index-1}"
        if card["source_ids"]!=[chapter["id"]] or card["locators"]!=[locator]:
            raise InternalCondition("revise","HH1A_CHAPTER_CARD_BINDING_DRIFT",f"chapter {index} is not bound to its exact HS1 design",[chapter["id"]])
        expected_storylines=[
            {"name":reader_names[chapter["primary_storyline_id"]],"role":"primary"},
            *({"name":reader_names[value],"role":"supporting"} for value in chapter["supporting_storyline_ids"]),
            *({"name":reader_names[value],"role":"background"} for value in chapter["background_storyline_ids"]),
            *({"name":reader_names[value],"role":"preserved_open"} for value in chapter["preserved_open_storyline_ids"]),
        ]
        expected=(index,chapter["working_title"],chapter["core_content"],chapter["chapter_end_change"],expected_storylines,f"第{index}章　{chapter['working_title']}")
        actual=(card["chapter_number"],card["chapter_title"],card["core_content"],card["chapter_end_change"],card["storylines"],card["visual_role"])
        if actual!=expected:
            raise InternalCondition("revise","HH1A_CHAPTER_CARD_CONTENT_DRIFT",f"chapter {index} does not faithfully present its title, core content, ending change, and storylines",[chapter["id"]])

def _validate_pairs(item:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any],label:str)->list[tuple[str,str]]:
    sources=item["source_ids"];locators=item["locators"]
    if len(sources)!=len(locators):raise InternalCondition("revise","HH1A_UNPAIRED_EVIDENCE",f"{label} source_ids/locators lengths differ",[label])
    pairs=list(zip(sources,locators))
    if len(pairs)!=len(set(pairs)) or any(pair not in binding_index for pair in pairs):raise InternalCondition("revise","HH1A_MISATTRIBUTED_EVIDENCE",f"{label} contains duplicate or non-cross-index source/locator pairs",[label])
    return pairs

def _validate_visual(visual:Mapping[str,Any],binding_index:Mapping[tuple[str,str],Any])->None:
    node_ids=[node["id"] for node in visual["nodes"]]
    if len(node_ids)!=len(set(node_ids)):raise InternalCondition("revise","HH1A_VISUAL_NODE_DUPLICATE",visual["id"],[visual["id"]])
    for node in visual["nodes"]:_validate_pairs(node,binding_index,f"{visual['id']}:node:{node['id']}")
    for index,edge in enumerate(visual["edges"]):
        if edge["from"] not in node_ids or edge["to"] not in node_ids:raise InternalCondition("revise","HH1A_VISUAL_EDGE_DANGLING",f"{visual['id']} edge {index}",[visual["id"]])
        _validate_pairs(edge,binding_index,f"{visual['id']}:edge:{index}")

def _budget(report:Mapping[str,Any])->dict[str,Any]:
    values=[value for _,value in _author_visible_values(report)]
    text=" ".join(values);visuals=len(report["visual_models"]);cjk=len(CJK.findall(text));latin=len(LATIN.findall(text));minutes=round(cjk/500+latin/250+visuals*.25,4)
    return {"cjk_characters":cjk,"latin_words":latin,"visual_count":visuals,"formula":"CJK/500 + Latin/250 + visuals*0.25","estimated_read_minutes":minutes}

def _validate_budget(report:Mapping[str,Any],elements:list[dict[str,Any]])->None:
    budget=_budget(report)
    if report["review_budget"]!=budget:raise InternalCondition("revise","HH1A_BUDGET_DRIFT","declared reading budget differs from deterministic visible-surface recount")
    if budget["estimated_read_minutes"]>24:raise InternalCondition("revise","HH1A_BUDGET_EXCEEDED",f"estimated {budget['estimated_read_minutes']} minutes exceeds 24")

def validate_draft(context:Context,draft:Path,admitted:Mapping[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    expected={"canonical.json","generation-session.json","generation-evidence"}
    if {path.name for path in draft.iterdir()}!=expected:raise InternalCondition("revise","HH1A_DRAFT_CLOSURE","draft must contain canonical, session and generation-evidence only")
    evidence_dir=draft/"generation-evidence";names=("00-material-inventory.json","01-organization.json","02-adversarial-review.json")
    if tuple(path.name for path in sorted(evidence_dir.iterdir()))!=names:raise InternalCondition("revise","HH1A_EVIDENCE_CLOSURE","generation evidence set/order mismatch")
    report=read_json(draft/"canonical.json");session=read_json(draft/"generation-session.json");evidence={name:read_json(evidence_dir/name) for name in names}
    context.catalog.validate(report,"hld-human-review-report.schema.json");context.catalog.validate(session,"hh1-a-generation-session.schema.json");context.catalog.validate(evidence[names[0]],"hh1-a-material-inventory.schema.json");context.catalog.validate(evidence[names[1]],"hh1-a-organization.schema.json");context.catalog.validate(evidence[names[2]],"hh1-a-adversarial-review.schema.json")
    if (report["hld_run_id"],report["revision"])!=(context.work_order["hld_run_id"],context.work_order["revision"]):raise InternalCondition("revise","HH1A_REPORT_IDENTITY","report run/revision mismatch")
    if report["hp1_content_binding"]!={"package_sha256":sha256(context.roles["novel_hld_package"]),"completion_sha256":sha256(context.roles["hp1_completion"])} or report["hq2_gate_binding"]!={"acceptance_sha256":sha256(context.roles["lld_handoff_acceptance"]),"bound_hp1_package_sha256":sha256(context.roles["novel_hld_package"])}:raise InternalCondition("revise","HH1A_REPORT_BINDING","report HP1/HQ2 binding mismatch")
    declared=context.work_order["file_allowlist"]
    if session["actual_read_refs"]!=declared or session["task_id"]!=context.work_order["task_id"] or session["hld_run_id"]!=context.work_order["hld_run_id"]:raise InternalCondition("revise","HH1A_SESSION_READ_DRIFT","generation session must exactly equal ordered allowlist and task identity")
    elements=_all_elements(report);ids=[item["id"] for item in elements];_validate_definition_sections(report,admitted);_validate_chapter_designs(report,admitted);_validate_author_language(report)
    if len(ids)!=len(set(ids)) or any("HUI-" in json.dumps(item,ensure_ascii=False) for item in elements):raise InternalCondition("revise","HH1A_ELEMENT_ID_INVALID","duplicate or renderer-owned report ID")
    expected_list=[]
    for item in elements:
        expected_list.extend((item["id"],source,locator) for source,locator in _validate_pairs(item,admitted["binding_index"],item["id"]))
        if item["id"].startswith("HVG-"):_validate_visual(item,admitted["binding_index"])
    actual_list=[(item["report_element_id"],item["source_id"],item["locator"]) for item in report["source_bindings"]]
    if len(actual_list)!=len(set(actual_list)) or actual_list!=expected_list:raise InternalCondition("revise","HH1A_SOURCE_BINDING_DRIFT","source_bindings must be the unique ordered expansion of all outer element pairs")
    actual_bindings=set(actual_list)
    material=material_locator_map(admitted)
    def primary_locators(item:Mapping[str,Any])->list[str]:
        if item.get("element_kind") in {"character_definition","environment_definition"}:
            return list(item["locators"][:1])
        return list(item["locators"])
    primary_covered={locator for section in DOMAIN_SECTIONS for item in report[section] for locator in primary_locators(item) if locator in material}
    missing=set(material)-primary_covered
    wrong_domain=[]
    for section in DOMAIN_SECTIONS:
        for item in report[section]:
            wrong_domain.extend(locator for locator in primary_locators(item) if locator in material and material[locator]!=section)
    if missing:raise InternalCondition("revise","HH1A_REPORT_MATERIAL_OMISSION",f"uncovered material locators: {sorted(missing)}",missing)
    if wrong_domain:raise InternalCondition("revise","HH1A_DOMAIN_MISPLACEMENT",f"locators placed in wrong domain: {sorted(set(wrong_domain))}",wrong_domain)
    domain_coverage={section:{"expected_locators":sorted(locator for locator,owner in material.items() if owner==section),"covered_locators":sorted(locator for locator in primary_covered if material[locator]==section),"uncovered_locators":sorted(locator for locator,owner in material.items() if owner==section and locator not in primary_covered)} for section in DOMAIN_SECTIONS}
    if evidence[names[0]]["material_locators"]!=sorted(material) or evidence[names[0]]["covered_locators"]!=sorted(primary_covered) or evidence[names[0]]["uncovered_locators"]!=sorted(missing) or evidence[names[0]]["domain_coverage"]!=domain_coverage:raise InternalCondition("revise","HH1A_INVENTORY_DRIFT","material inventory/domain coverage does not exactly bind runtime inventory")
    org=evidence[names[1]]["domain_element_ids"]
    if any(org[section]!=[item["id"] for item in report[section]] for section in DOMAIN_SECTIONS) or evidence[names[1]]["visual_model_ids"]!=[item["id"] for item in report["visual_models"]]:raise InternalCondition("revise","HH1A_ORGANIZATION_DRIFT","organization evidence differs from report")
    if session["material_locator_count"]!=len(material):raise InternalCondition("revise","HH1A_SESSION_INVENTORY_DRIFT","session material count mismatch")
    _validate_budget(report,elements)
    return report,session,evidence

def build_ready(context:Context,staging:Path,report:Mapping[str,Any],session:Mapping[str,Any],evidence:Mapping[str,Any])->dict[str,Any]:
    staging.mkdir(parents=True,exist_ok=False);write_json(staging/SPEC.canonical_name,report);write_json(staging/SPEC.session_name,session)
    for name,value in evidence.items():write_json(staging/"generation-evidence"/name,value)
    execution={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"implementation_sha256":impl_hash(),"actual_read_hashes":{role:sha256(path) for role,path in sorted(context.roles.items())},"report_sha256":sha256(staging/SPEC.canonical_name),"deterministic":True}
    context.catalog.validate(execution,"hh1-a-execution.schema.json");write_json(staging/SPEC.execution_name,execution)
    validation={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"status":"pass","checks":["exact-read-closure","hp1-hq2-current-bindings","character-environment-definition-closure","author-language-contract","nine-domain-material-coverage","source-binding-bijection","budget-recount","task-isolation","adversarial-pass","deterministic-reproduction"],"errors":[]}
    context.catalog.validate(validation,"hh1-a-validation.schema.json");write_json(staging/"validation.json",validation)
    roles={SPEC.canonical_name:SPEC.canonical_role,SPEC.session_name:"generation_session",SPEC.execution_name:"execution_record","validation.json":"validation"}
    return finalize_ready(context,staging,roles)

def execute(work_order:Path,draft:Path)->tuple[int,dict[str,Any]]:
    context=load_context(work_order,SPEC,impl_hash(),_catalog())
    def build(ctx:Context,staging:Path):
        try:
            try:admitted=admit(ctx)
            except ContractError as error:raise InternalCondition("blocked","HH1A_UPSTREAM_SCHEMA_INVALID",str(error),["HP1"]) from error
            try:report,session,evidence=validate_draft(ctx,draft.resolve(strict=True),admitted)
            except ContractError as error:raise InternalCondition("revise","HH1A_DRAFT_SCHEMA_INVALID",str(error)) from error
            return 0,build_ready(ctx,staging,report,session,evidence)
        except InternalCondition as condition:
            return 2,finalize_condition(ctx,staging,condition,read_json(draft/"canonical.json") if (draft/"canonical.json").is_file() else None)
        except Exception as error:return 1,finalize_runtime_error(ctx,staging,error,"HH1-A admission/draft validation/sealing")
    return atomic_execute(context,build)

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("work_order",type=Path);parser.add_argument("draft_dir",type=Path);args=parser.parse_args(argv)
    try:code,_=execute(args.work_order,args.draft_dir);return code
    except Exception as error:print(str(error),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
