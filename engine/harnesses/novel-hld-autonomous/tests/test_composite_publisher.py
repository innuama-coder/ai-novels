from __future__ import annotations

import importlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO))

from runtime import composite_publisher as publisher  # noqa: E402

hp1 = importlib.import_module("skills.novel-hld-package-assembler.scripts.hp1_runtime")
hp1_fixture = importlib.import_module("skills.novel-hld-package-assembler.tests.test_hp1_runtime")


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes): path.write_bytes(value)
    else: path.write_bytes(publisher.canonical_bytes(value))


def fref(path: Path, root: Path, role: str) -> dict[str, str]:
    return publisher.file_ref(path, root, role)


def artifact(workspace: Path, stage: str) -> dict[str, str]:
    folder = workspace / f"{stage}-package"
    main = folder / publisher.UPSTREAM_PRIMARY[stage]
    manifest = folder / "package-manifest.json"
    completion = folder / "stage-completion.json"
    return {"path":main.relative_to(workspace).as_posix(),"sha256":publisher.sha256(main),"manifest_path":manifest.relative_to(workspace).as_posix(),"manifest_sha256":publisher.sha256(manifest),"completion_path":completion.relative_to(workspace).as_posix(),"completion_sha256":publisher.sha256(completion)}


def manifest(package: Path, stage: str, skill: str, content: list[tuple[str, Path]], status: str = "ready") -> Path:
    refs=[];roles={}
    for role,path in content:
        item=fref(path,package,role);refs.append(item);roles[role]=item
    value={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","revision":1,"stage":stage,"skill":skill,"status":status,"files":refs,"artifact_roles":roles}
    target=package/"package-manifest.json" if status=="ready" else package/"result-manifest.json";write(target,value);return target


def result_base(work: dict, skill: str, result: str, manifest_path: Path, validation: Path, workspace: Path) -> dict:
    return {"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","revision":1,"stage":work["stage"],"skill":skill,"work_order_id":work["work_order_id"],"task_id":work["task_id"],"event_sequence":work["event_sequence"],"result_scope":"composite_internal","result":result,"state_before_ref":work["state_before_ref"],"input_gate_ref":work["input_gate_ref"],"result_manifest_ref":fref(manifest_path,workspace,"result_manifest" if result!="ready" else "package_manifest"),"validation_ref":fref(validation,workspace,"validation"),"produced_at":work["result_timestamp"],"completion_ref":None,"internal_manifest_ref":fref(manifest_path,workspace,"internal_manifest") if result=="ready" else None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None}


def internal_work(workspace: Path, kind: str, sequence: int, state_ref: dict, upstream: list[dict], allowlist: list[dict]) -> tuple[Path, dict]:
    stage,skill,_,_=publisher.TASK_CONTRACT[kind]
    gate=workspace/"internal"/kind/"input-gate.json";write(gate,{"sealed":True,"kind":kind})
    value={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","revision":1,"work_order_id":f"WO-{kind}","task_id":f"TASK-{kind}","stage":stage,"action":"execute","exact_owner_skill":skill,"owner_version":"1.0.0","implementation_sha256":"6"*64,"event_sequence":sequence,"result_timestamp":"2026-08-06T00:00:00Z","input_gate_ref":fref(gate,workspace,"input_gate"),"state_before_ref":state_ref,"upstream_completions":upstream,"file_allowlist":allowlist,"unresolved_projection":[],"mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"output_directory":f"internal/{kind}/package","submission_status":"open"}
    path=workspace/"internal"/kind/"work-order.json";write(path,value);return path,value


def minimal_world_environment_definitions() -> list[dict]:
    scopes=("city_and_region","local_people_and_daily_life","social_order_and_public_atmosphere","technology_and_infrastructure","climate_and_physical_environment")
    cards=[]
    for index,scope in enumerate(scopes,1):
        card={"id":f"HRE-WORLD-{index}","element_kind":"world_environment_definition","environment_scope":scope,"name":f"World definition {index}","definition":"A concrete world condition shapes daily life and story pressure.","defining_features":["The condition is visible in ordinary scenes.","The condition constrains action without making choices."],"people_and_daily_life":"People work, travel, and care for families around the hidden conflict.","story_pressure_and_limits":"The environment creates pressure while decisions remain human.","author_open_details":[],"source_ids":["NAR-001"],"locators":["/x"],"visual_role":"world definition","review_question":"Is this world condition clear?"}
        cards.append(card)
    cities=[]
    for index in range(4):
        cities.append({"city_name":f"City {index+1}","country":f"Country {index+1}","jurisdiction":f"Jurisdiction {index+1}","story_function":f"Carries story function {index+1}.","city_scale":"A specific regional city.","urban_structure":["A working district.","A civic district."],"street_and_architecture":"Streets and buildings have a recognisable local form.","transport_and_daily_rhythm":"Public transport and shift work define daily movement.","seasonal_expression":"Seasonal weather changes travel and public space.","key_story_events":[f"Event {index+1} occurs here."]})
    links=[]
    for index in range(4):
        links.append({"from_city":cities[index]["city_name"],"to_city":cities[(index+1)%4]["city_name"],"travel_time":"Several hours.","physical_route":"People and sealed materials travel under explicit custody.","information_route":"Verified information travels through a bounded channel.","custody_rule":"Original evidence remains sealed until lawful release.","story_function":"The route moves one consequence into the next city."})
    cards[0]["city_network"]={"narrative_distribution":"Four cities separate handoff, investigation, decision, and intervention.","cities":cities,"intercity_links":links}
    cards[0]["city_stories"]=[{"city_name":city["city_name"],"story":f"{city['city_name']} carries {city['story_function'].lower()}"} for city in cities]
    cards[0]["route_stories"]=[{"from_city":link["from_city"],"to_city":link["to_city"],"story":f"People and verified information move from {link['from_city']} to {link['to_city']} through separate routes."} for link in links]
    cards[1]["ordinary_people_portraits"]=[{"portrait_name":f"Resident {index+1}","city":cities[index]["city_name"],"who_they_are":"An ordinary worker with family obligations.","daily_routine":"Work and caregiving structure the day.","material_details":"Transit cards, food, and weather gear make life concrete.","crisis_exposure":"Disruption reaches wages, travel, and care.","knowledge_boundary":"The resident sees effects but not the hidden cause."} for index in range(4)]
    cards[1]["ordinary_people_stories"]=[{"portrait_name":f"Resident {index+1}","city":cities[index]["city_name"],"story":"An ordinary worker balances wages, travel, and family care while seeing only the public effects of the crisis."} for index in range(4)]
    cards[4]["season_profile"]={"season":"Early autumn.","story_window":"Six weeks.","temperature_and_weather":"Coastal rain, inland dry air, and northern fog.","daylight_and_air":"Days shorten and each city has distinct air and light.","daily_effects":"Weather changes commuting, shifts, and public services.","plot_effect":"Weather limits action without deciding the outcome."}
    cards[4]["season_story"]="Early-autumn rain, dry inland air, and northern fog alter travel and public services without deciding any character's choice."
    return cards


def report_model(hp1_completion: Path, hp1_main: Path, q2_completion: Path, q2_main: Path) -> dict:
    element={"id":"HRE-001","element_kind":"control","conclusion":"conclusion","source_ids":["NAR-001"],"locators":["/x"],"visual_role":"summary","review_question":"approve?"}
    character={"id":"HRE-CHARACTER","element_kind":"character_definition","name":"人物","conclusion":"人物在故事中承担明确选择。","story_position":"人物推动一项关键变化。","personality_and_motivation":"人物具有具体性格和愿望。","capabilities_and_limits":"人物的能力与限制清楚。","relationships_and_change":"人物关系和变化清楚。","source_ids":["NAR-001"],"locators":["/x"],"visual_role":"角色定义","review_question":"人物是否成立？"}
    environment={"id":"HRE-ENVIRONMENT","element_kind":"environment_definition","name":"场所","conclusion":"场所承载明确的故事作用。","story_function":"场所推动一项关键变化。","physical_character":"空间形态清楚。","access_and_limits":"准入和限制清楚。","dramatic_use":"适合承载的戏剧冲突清楚。","source_ids":["NAR-001"],"locators":["/x"],"visual_role":"环境定义","review_question":"环境是否成立？"}
    return {"schema_version":"1.0","skill":"novel-hld-review-report-assembler","stage":"HH1","hld_run_id":"hld-fixture","revision":1,"status":"ready","hp1_content_binding":{"package_sha256":publisher.sha256(hp1_main),"completion_sha256":publisher.sha256(hp1_completion)},"hq2_gate_binding":{"acceptance_sha256":publisher.sha256(q2_main),"bound_hp1_package_sha256":publisher.sha256(hp1_main)},"title_and_decision_scope":[element],"overall_narrative_architecture":[element],"world_environment_definitions":minimal_world_environment_definitions(),"character_definitions":[character],"environment_definitions":[environment],"storyline_choreography":[element],"character_arc_placement":[element],"pov_information_suspense":[element],"time_space_pacing_tension":[element],"key_scene_functions":[element],"chapter_definitions":[element],"open_items_constraints_and_lld_boundary":[element],"visual_models":[],"source_bindings":[{"report_element_id":"HRE-001","source_id":"NAR-001","locator":"/x"}],"review_budget":{"cjk_characters":100,"latin_words":0,"visual_count":0,"formula":"CJK/500 + Latin/250 + visuals*0.25","estimated_read_minutes":0.2}}


def review_model(report: Path, report_manifest: Path) -> dict:
    dimension={"verdict":"pass","claims":["ok"],"challenges":["none"],"report_element_ids":["HRE-001"],"source_ids":["NAR-001"],"locators":["/x"]}
    retrieval={"question_code":"architecture_progression","question":"q","answer":"a","report_element_ids":["HRE-001"],"source_ids":["NAR-001"],"locators":["/x"],"verdict":"pass"}
    codes=("architecture_progression","world_environment_definitions","character_definitions","environment_definitions","mandatory_storyline_connections","core_arc_choices","pov_knowledge_boundaries","continuity_constraints","key_functions_and_climax","chapter_definition_readiness","open_items_and_lld_boundary")
    tests=[{**retrieval,"question_code":code} for code in codes]
    return {"schema_version":"1.0","skill":"novel-hld-presentation-fidelity-reviewer","stage":"HH1","hld_run_id":"hld-fixture","revision":1,"review_bindings":{"hp1_package_sha256":"TO_FILL","report_sha256":publisher.sha256(report),"report_manifest_sha256":publisher.sha256(report_manifest),"assembler_task_id":"TASK-HH1-A","reviewer_task_id":"TASK-HH1-B"},"fact_fidelity":dimension,"structure_and_relation_fidelity":dimension,"coverage_fidelity":dimension,"authority_and_open_item_fidelity":dimension,"visual_data_fidelity":dimension,"material_drift_findings":[],"reading_budget_validation":{"formula":"CJK/500 + Latin/250 + visuals*0.25","declared":{"cjk_characters":100,"latin_words":0,"visual_count":0,"estimated_read_minutes":0.2},"recomputed":{"cjk_characters":100,"latin_words":0,"visual_count":0,"estimated_read_minutes":0.2},"verdict":"pass"},"decision_retrieval_tests":tests,"cognitive_overload_findings":[],"defect_origin":"none","verdict":"pass"}


class Fixture:
    def __init__(self, root: Path):
        hp1_order=hp1_fixture.build_workspace(root)
        code,_=hp1.execute(hp1_order)
        if code!=0:raise AssertionError("HP1 fixture failed")
        self.workspace=hp1_order.parent; (self.workspace/"stage-result.json").unlink()
        self.state=self.workspace/"publisher-state.json";write(self.state,{"sealed":True,"hld_run_id":"hld-fixture","revision":1})

    def upstream(self, stage: str) -> list[dict]:
        return [artifact(self.workspace,item) for item in publisher.UPSTREAM[stage]]

    def ready_task(self, kind: str, sequence: int, state_ref: dict, upstream: list[dict], previous: dict[str,"TaskFixture"]) -> "TaskFixture":
        stage,skill,profile,main_contracts=publisher.TASK_CONTRACT[kind];mains=tuple(name for _,name in main_contracts); package=self.workspace/"internal"/kind/"package";package.mkdir(parents=True)
        allow=[]
        if kind=="consumer_test":
            handoff=self.workspace/"HP1-package"/"lld-handoff.json";allow=[fref(handoff,self.workspace,"lld_handoff")]
            model={"schema_version":"1.0","skill":skill,"stage":"HQ2","mode":"consumer_test","hld_run_id":"hld-fixture","task_id":"TASK-consumer_test","verdict":"pass","defect_origin":"none"}
        elif kind=="fidelity_test":
            consumer=previous["consumer_test"]
            allow=[fref(self.workspace/"HP1-package"/"stage-completion.json",self.workspace,"hp1_completion"),fref(consumer.mains[0],self.workspace,"sealed_consumption_test"),fref(consumer.manifest,self.workspace,"sealed_consumption_manifest")]
            model={"schema_version":"1.0","skill":skill,"stage":"HQ2","mode":"fidelity_test","hld_run_id":"hld-fixture","task_id":"TASK-fidelity_test","verdict":"pass","defect_origin":"none","sealed_consumption_test_ref":fref(consumer.mains[0],self.workspace,"sealed_consumption_test")}
        elif kind=="HH1-A":
            allow=[fref(self.workspace/"HP1-package"/"novel-hld-package.json",self.workspace,"novel_hld_package"),fref(self.workspace/"HQ2-package"/"lld-handoff-acceptance.json",self.workspace,"lld_handoff_acceptance")]
            model=report_model(self.workspace/"HP1-package"/"stage-completion.json",self.workspace/"HP1-package"/"novel-hld-package.json",self.workspace/"HQ2-package"/"stage-completion.json",self.workspace/"HQ2-package"/"lld-handoff-acceptance.json")
        elif kind=="HH1-B":
            a=previous["HH1-A"];allow=[fref(a.mains[0],self.workspace,"human_review_report"),fref(a.manifest,self.workspace,"hh1_a_manifest"),fref(self.workspace/"HP1-package"/"novel-hld-package.json",self.workspace,"novel_hld_package")];model=review_model(a.mains[0],a.manifest);model["review_bindings"]["hp1_package_sha256"]=publisher.sha256(self.workspace/"HP1-package"/"novel-hld-package.json")
        else:
            a=previous["HH1-A"];b=previous["HH1-B"];allow=[fref(a.mains[0],self.workspace,"human_review_report"),fref(b.mains[0],self.workspace,"presentation_fidelity_review")];model=None
        if kind=="HH1-C":
            html=package/mains[0];write(html,b"<!doctype html><title>HLD review</title>\n")
            registry={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","stage":"HH1","skill":"novel-hld-html-renderer","report_ref":fref(a.mains[0],self.workspace,"human_review_report"),"fidelity_review_ref":fref(b.mains[0],self.workspace,"presentation_fidelity_review"),"renderer_binding":{"implementation_sha256":"1"*64,"template_sha256":"2"*64,"stylesheet_sha256":"3"*64,"report_schema_sha256":"4"*64,"fidelity_schema_sha256":"6"*64},"targets":[{"id":"HUI-HRE-001-report_element-0","dom_locator":"[data-render-target-id=\"HUI-HRE-001-report_element-0\"]","render_role":"report_element","source_visual_role":"summary","report_element_id":"HRE-001","report_element_kind":"control","visual_model_id":None,"content_sha256":"5"*64}]}
            write(package/mains[1],registry)
        else:write(package/mains[0],model)
        session=package/("generation-session.json" if kind=="HH1-A" else "review-session.json" if kind!="HH1-C" else "render-execution.json")
        if kind=="HH1-C":execution=session;write(execution,{"sealed":True})
        else:write(session,{"sealed":True});execution=package/{"consumer_test":"consumption-test-execution.json","fidelity_test":"fidelity-test-execution.json","HH1-A":"report-assembly-execution.json","HH1-B":"fidelity-review-execution.json"}[kind];write(execution,{"sealed":True})
        validation=package/"validation.json";write(validation,{"status":"pass"})
        content=[]
        for index,name in enumerate(mains):content.append(({"consumer_test":"handoff_consumption_test","fidelity_test":"handoff_fidelity_test","HH1-A":"human_review_report","HH1-B":"presentation_fidelity_review","HH1-C":"human_review_html"}[kind] if index==0 else "render_target_registry",package/name))
        if kind!="HH1-C":content.append(("session",session))
        if kind=="HH1-A":
            evidence=package/"generation-evidence"/"01.json";write(evidence,{"sealed":True});content.append(("generation_evidence",evidence))
        content.extend([("execution",execution),("validation",validation)])
        man=manifest(package,stage,skill,content)
        work_path,work=internal_work(self.workspace,kind,sequence,state_ref,upstream,allow)
        result=result_base(work,skill,"ready",man,validation,self.workspace);result_path=package.parent/"stage-result.json";write(result_path,result)
        return TaskFixture(kind,work_path,work,result_path,man,tuple(package/name for name in mains))

    def nonready_task(self, kind: str, sequence: int, state_ref: dict, upstream: list[dict], outcome: str, previous: dict[str,"TaskFixture"]|None=None, invalid_condition: bool=False) -> "TaskFixture":
        stage,skill,_,_=publisher.TASK_CONTRACT[kind];package=self.workspace/"internal"/kind/"package";package.mkdir(parents=True)
        if kind=="consumer_test":
            handoff=self.workspace/"HP1-package"/"lld-handoff.json";allow=[fref(handoff,self.workspace,"lld_handoff")]
        elif kind=="HH1-B" and previous is not None:
            a=previous["HH1-A"];allow=[fref(a.mains[0],self.workspace,"human_review_report"),fref(a.manifest,self.workspace,"hh1_a_manifest"),fref(self.workspace/"HP1-package"/"novel-hld-package.json",self.workspace,"novel_hld_package")]
        else:raise AssertionError("unsupported blocked fixture kind")
        work_path,work=internal_work(self.workspace,kind,sequence,state_ref,upstream,allow)
        validation=package/"validation.json";write(validation,{"status":outcome});affected=["LWK-001"] if outcome!="runtime_error" else []
        if outcome=="blocked":
            gate=package/"gate-data.json";report=package/"blocked-report.json"
            gate_value={"schema_version":"1.0","hld_run_id":"hld-fixture","stage":stage,"failed_gate":"upstream-contract","evidence":"sealed upstream evidence failed","affected_ids":affected}
            if invalid_condition:gate_value.pop("evidence")
            write(gate,gate_value);write(report,{"schema_version":"1.0","skill":skill,"stage":stage,"hld_run_id":"hld-fixture","status":"blocked","blocker_class":"upstream_defect","code":"INTERNAL_UPSTREAM_DEFECT","evidence":"upstream contract failed","affected_ids":affected,"required_action":"repair upstream artifact"})
            content=[("gate_data",gate),("blocked_report",report),("validation",validation)]
        elif outcome=="revise":
            report=package/"revision-report.json";candidate=package/"candidate.json";evidence=package/"local-defect-evidence.json"
            write(report,{"schema_version":"1.0","skill":skill,"stage":stage,"hld_run_id":"hld-fixture","status":"revise","revision_class":"local_candidate","code":"LOCAL_CANDIDATE_REQUIRED","evidence":"local repair is bounded","affected_ids":affected,"required_action":"review sealed candidate"});write(candidate,{"candidate":"bounded"});write(evidence,{"finding":"local"})
            content=[("revision_report",report),("candidate",candidate),("local_defect_evidence",evidence),("validation",validation)]
        elif outcome=="runtime_error":
            error=package/"runtime-error.json";write(error,{"schema_version":"1.0","harness":publisher.HARNESS,"skill":skill,"stage":stage,"hld_run_id":"hld-fixture","status":"runtime_error","error_code":"INTERNAL_RUNTIME_FAILURE","message":"runtime failed before semantic completion","failed_operation":"sealed test execution"})
            content=[("runtime_error",error),("validation",validation)]
        else:raise AssertionError("unsupported non-ready outcome")
        man=manifest(package,stage,skill,content,outcome);result=result_base(work,skill,outcome,man,validation,self.workspace);result["affected_ids"]=affected
        if outcome=="blocked":result.update({"gate_data_ref":fref(gate,self.workspace,"gate_data"),"blocked_report_ref":fref(report,self.workspace,"blocked_report"),"blocker_class":"upstream_defect"})
        elif outcome=="revise":result.update({"revision_class":"local_candidate","revision_report_ref":fref(report,self.workspace,"revision_report"),"candidate_ref":fref(candidate,self.workspace,"candidate"),"local_defect_evidence":[fref(evidence,self.workspace,"local_defect_evidence")]})
        else:result["runtime_error_ref"]=fref(error,self.workspace,"runtime_error")
        result_path=package.parent/"stage-result.json";write(result_path,result);return TaskFixture(kind,work_path,work,result_path,man,tuple(path for _,path in content))

    def blocked_task(self, kind: str, sequence: int, state_ref: dict, upstream: list[dict], previous: dict[str,"TaskFixture"]|None=None, invalid_condition: bool=False) -> "TaskFixture":
        return self.nonready_task(kind,sequence,state_ref,upstream,"blocked",previous,invalid_condition)

    def publish_order(self, stage: str, tasks: list["TaskFixture"], issued_override: list["TaskFixture"]|None=None) -> Path:
        issued=issued_override if issued_override is not None else tasks;order=publisher.TASK_ORDER[stage];state_ref=fref(self.state,self.workspace,"state_before")
        records=[{"task_kind":item.kind,"sequence":item.work["event_sequence"],"work_order_ref":fref(item.work_path,self.workspace,"work_order"),"stage_result_ref":fref(item.result_path,self.workspace,"stage_result"),"package_manifest_ref":fref(item.manifest,self.workspace,"package_manifest")} for item in issued]
        state_doc={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","revision":1,"stage":stage,"workspace_id":f"WS-{stage}","state_before_ref":state_ref,"ordered_task_kinds":list(order),"issued_tasks":records,"unissued_task_kinds":list(order[len(issued):]),"last_issued_event_sequence":records[-1]["sequence"]}
        state_path=self.workspace/f"{stage}-composite-state.json";write(state_path,state_doc)
        upstream=self.upstream(stage);allow=[fref(state_path,self.workspace,"composite_workspace_state")]
        for name,item in zip(publisher.UPSTREAM[stage],upstream):
            prefix=f"upstream::{name}";package=self.workspace/f"{name}-package";completion=package/"stage-completion.json";man=package/"package-manifest.json";main=self.workspace/item["path"]
            allow.extend([fref(completion,self.workspace,f"{prefix}::completion"),fref(man,self.workspace,f"{prefix}::manifest"),fref(main,self.workspace,f"{prefix}::canonical::{publisher.UPSTREAM_PRIMARY_ROLE[name]}")])
            man_value=json.loads(man.read_text(encoding="utf-8"));reverse={ref["path"]:role for role,ref in man_value["artifact_roles"].items()}
            for member in man_value["files"]:
                path=package/member["path"]
                if path==main:continue
                role=f"{prefix}::validation" if member["path"]=="validation.json" else f"{prefix}::member::{reverse[member['path']]}"
                allow.append(fref(path,self.workspace,role))
        for item in issued:
            prefix=f"internal::{item.kind}";allow += [fref(item.work_path,self.workspace,f"{prefix}::work_order"),fref(item.result_path,self.workspace,f"{prefix}::stage_result"),fref(item.manifest,self.workspace,f"{prefix}::package_manifest")]
            allow.append(fref(self.workspace/item.work["input_gate_ref"]["path"],self.workspace,f"{prefix}::input_gate"))
            for task_input in item.work["file_allowlist"]:allow.append(fref(self.workspace/task_input["path"],self.workspace,f"{prefix}::task_input::{task_input['role']}"))
            man_value=json.loads(item.manifest.read_text(encoding="utf-8"));reverse={ref["path"]:role for role,ref in man_value["artifact_roles"].items()}
            for member in man_value["files"]:allow.append(fref(item.manifest.parent/member["path"],self.workspace,f"{prefix}::member::{reverse[member['path']]}"))
        gate={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","stage":stage,"mode":"forward","state_before_ref":state_ref,"hb0_completion_ref":upstream[0],"upstream_completions":upstream,"baseline_manifest_ref":None,"baseline_validation_ref":None,"source_lineage_refs":[],"exact_owner_skill":publisher.PUBLISHER,"owner_version":publisher.VERSION,"implementation_sha256":publisher.implementation_sha256(),"return_binding":None,"unresolved_projection":[],"revision_plan_ref":None,"revision_plan_state_ref":None,"file_allowlist":allow}
        gate_path=self.workspace/f"{stage}-publisher-gate.json";write(gate_path,gate)
        work={"schema_version":"1.0","harness":publisher.HARNESS,"hld_run_id":"hld-fixture","revision":1,"work_order_id":f"WO-PUBLISH-{stage}","task_id":f"TASK-PUBLISH-{stage}","stage":stage,"action":"execute","exact_owner_skill":publisher.PUBLISHER,"owner_version":publisher.VERSION,"implementation_sha256":publisher.implementation_sha256(),"event_sequence":99,"result_timestamp":"2026-08-06T00:00:00Z","input_gate_ref":fref(gate_path,self.workspace,"input_gate"),"state_before_ref":state_ref,"upstream_completions":upstream,"file_allowlist":allow,"unresolved_projection":[],"mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"output_directory":f"{stage}-package","submission_status":"open"}
        path=self.workspace/f"{stage}-publisher-work-order.json";write(path,work);return path


class TaskFixture:
    def __init__(self,kind,work_path,work,result_path,manifest_path,mains):self.kind=kind;self.work_path=work_path;self.work=work;self.result_path=result_path;self.manifest=manifest_path;self.mains=mains


class CompositePublisherTests(unittest.TestCase):
    @staticmethod
    def remove_allowlist_role(order: Path, role: str) -> None:
        work=json.loads(order.read_text(encoding="utf-8"));gate_path=order.parent/work["input_gate_ref"]["path"];gate=json.loads(gate_path.read_text(encoding="utf-8"))
        work["file_allowlist"]=[item for item in work["file_allowlist"] if item["role"]!=role];gate["file_allowlist"]=work["file_allowlist"];write(gate_path,gate);work["input_gate_ref"]=fref(gate_path,order.parent,"input_gate");write(order,work)
    def build_hq2(self, root: Path, blocked=False, issue_later=False):
        fixture=Fixture(root);state_ref=fref(fixture.state,fixture.workspace,"state_before");up=fixture.upstream("HQ2");previous={}
        first=fixture.blocked_task("consumer_test",30,state_ref,up) if blocked else fixture.ready_task("consumer_test",30,state_ref,up,previous);previous[first.kind]=first
        tasks=[first]
        if not blocked or issue_later:
            second=fixture.ready_task("fidelity_test",31,state_ref,up,previous);tasks.append(second)
        order=fixture.publish_order("HQ2",tasks);return fixture,tasks,order

    def test_hq2_ready_profile_and_reproduction(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,order=self.build_hq2(Path(temp));code,result=publisher.execute(order);self.assertEqual((code,result["result"]),(0,"ready"));self.assertEqual(publisher.validate_existing(order)["status"],"pass")
            self.assertEqual({p.name for p in (fixture.workspace/"HQ2-package").iterdir()},{"lld-handoff-acceptance.json","q2-publish-execution.json","validation.json","package-manifest.json","stage-completion.json"})

    def test_nonready_return_resolution_publisher_preserves_exact_revision_bindings(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,order=self.build_hq2(Path(temp),blocked=True);work=json.loads(order.read_text(encoding="utf-8"));gate_path=fixture.workspace/work["input_gate_ref"]["path"];gate=json.loads(gate_path.read_text(encoding="utf-8"))
            refs={}
            for key,role in (("return_binding","return_binding"),("revision_plan_ref","revision_plan"),("revision_plan_state_ref","revision_plan_state")):
                path=fixture.workspace/f"{key}.json";write(path,{"sealed":key});refs[key]=fref(path,fixture.workspace,role);work[key]=refs[key];gate[key]=refs[key]
            work["mode"]="return_resolution";gate["mode"]="return_resolution";write(gate_path,gate);work["input_gate_ref"]=fref(gate_path,fixture.workspace,"input_gate");write(order,work)
            code,result=publisher.execute(order);self.assertEqual((code,result["result"],result["result_scope"]),(2,"blocked","top_level"))

    def test_exact_upstream_may_precede_composite_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace=Path(temp);package=workspace/"HP1-package";package.mkdir()
            main=package/"novel-hld-package.json";validation=package/"validation.json"
            write(main,{"ready":True});write(validation,{"status":"pass"})
            manifest_path=package/"package-manifest.json"
            manifest_value={"files":[
                {"path":main.name,"sha256":publisher.sha256(main)},
                {"path":validation.name,"sha256":publisher.sha256(validation)},
            ]}
            write(manifest_path,manifest_value)
            completion_path=package/"stage-completion.json"
            write(completion_path,{"stage":"HP1","hld_run_id":"hld-fixture","revision":1})
            roles={
                "upstream::HP1::completion":completion_path,
                "upstream::HP1::manifest":manifest_path,
                "upstream::HP1::validation":validation,
                "upstream::HP1::canonical::novel_hld_package":main,
            }
            artifact={
                "path":main.relative_to(workspace).as_posix(),"sha256":publisher.sha256(main),
                "manifest_path":manifest_path.relative_to(workspace).as_posix(),"manifest_sha256":publisher.sha256(manifest_path),
                "completion_path":completion_path.relative_to(workspace).as_posix(),"completion_sha256":publisher.sha256(completion_path),
            }
            context=SimpleNamespace(
                workspace=workspace,roles=roles,catalog=SimpleNamespace(validate=lambda *_:None),
                work_order={"hld_run_id":"hld-fixture","revision":2},
            )
            with patch.object(publisher,"validate_ready_profile"), patch.object(publisher,"validate_manifest"), patch.object(publisher,"validate_completion_bindings"):
                admitted=publisher._admit_upstream(context,"HP1",artifact)
            self.assertEqual(admitted["completion"]["revision"],1)

    def test_hq2_first_nonready_is_byte_copied_and_mapped(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,tasks,order=self.build_hq2(Path(temp),blocked=True);code,result=publisher.execute(order);self.assertEqual((code,result["result"],result["blocker_class"]),(2,"blocked","upstream_defect"));package=fixture.workspace/"HQ2-package"
            self.assertEqual((package/"source-internal-stage-result.json").read_bytes(),tasks[0].result_path.read_bytes());self.assertEqual((package/"source-internal-package"/"gate-data.json").read_bytes(),(tasks[0].manifest.parent/"gate-data.json").read_bytes());self.assertFalse((package/"source-internal-package"/"result-manifest.json").exists());self.assertFalse((package/"stage-completion.json").exists())

    def test_hq2_revise_and_runtime_conditions_are_mapped(self):
        for outcome in ("revise","runtime_error"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temp:
                fixture=Fixture(Path(temp));state_ref=fref(fixture.state,fixture.workspace,"state_before");up=fixture.upstream("HQ2");task=fixture.nonready_task("consumer_test",30,state_ref,up,outcome);order=fixture.publish_order("HQ2",[task]);code,result=publisher.execute(order)
                self.assertEqual((code,result["result"]),(2,outcome));self.assertFalse((fixture.workspace/"HQ2-package"/"stage-completion.json").exists());self.assertEqual(publisher.validate_existing(order)["result"],outcome)

    def test_hh1_ready_copies_four_content_files(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,hq_tasks,hq_order=self.build_hq2(Path(temp));publisher.execute(hq_order);(fixture.workspace/"stage-result.json").unlink();state_ref=fref(fixture.state,fixture.workspace,"state_before");up=fixture.upstream("HH1");previous={};tasks=[]
            for index,kind in enumerate(publisher.TASK_ORDER["HH1"],40):task=fixture.ready_task(kind,index,state_ref,up,previous);previous[kind]=task;tasks.append(task)
            order=fixture.publish_order("HH1",tasks);code,result=publisher.execute(order);self.assertEqual((code,result["result"]),(0,"ready"));package=fixture.workspace/"HH1-package"
            for task,name in ((previous["HH1-A"],"hld-human-review-report.json"),(previous["HH1-B"],"presentation-fidelity-review.json"),(previous["HH1-C"],"hld-human-review-report.html")):
                self.assertEqual((package/name).read_bytes(),task.mains[0].read_bytes())
            self.assertEqual((package/"render-target-registry.json").read_bytes(),previous["HH1-C"].mains[1].read_bytes())

    def test_hh1_first_nonready_after_a_pass_is_byte_copied(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,hq_order=self.build_hq2(Path(temp));publisher.execute(hq_order);(fixture.workspace/"stage-result.json").unlink();state_ref=fref(fixture.state,fixture.workspace,"state_before");up=fixture.upstream("HH1");previous={}
            a=fixture.ready_task("HH1-A",40,state_ref,up,previous);previous["HH1-A"]=a;b=fixture.blocked_task("HH1-B",41,state_ref,up,previous);order=fixture.publish_order("HH1",[a,b]);code,result=publisher.execute(order)
            self.assertEqual((code,result["result"],result["blocker_class"]),(2,"blocked","upstream_defect"));self.assertEqual((fixture.workspace/"HH1-package"/"source-internal-stage-result.json").read_bytes(),b.result_path.read_bytes());self.assertFalse((fixture.workspace/"HH1-package"/"stage-completion.json").exists())

    def test_boundary_later_task_issued_after_nonready_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            _,_,order=self.build_hq2(Path(temp),blocked=True,issue_later=True)
            with self.assertRaisesRegex(publisher.PublishFailure,"first stop"):publisher.execute(order)

    def test_boundary_internal_hash_drift_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            _,tasks,order=self.build_hq2(Path(temp));write(tasks[0].mains[0],{"tampered":True})
            with self.assertRaises((publisher.PublishFailure,publisher.ContractError)):publisher.execute(order)

    def test_boundary_stale_upstream_hash_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,order=self.build_hq2(Path(temp));completion=fixture.workspace/"HP1-package"/"stage-completion.json";write(completion,{"tampered":True})
            with self.assertRaises((publisher.PublishFailure,publisher.ContractError)):publisher.execute(order)

    def test_boundary_order_error_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,tasks,order=self.build_hq2(Path(temp));state_path=fixture.workspace/"HQ2-composite-state.json";state=json.loads(state_path.read_text(encoding="utf-8"));state["issued_tasks"].reverse();write(state_path,state)
            with self.assertRaises((publisher.PublishFailure,publisher.ContractError)):publisher.execute(order)

    def test_boundary_published_byte_drift_fails_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,order=self.build_hq2(Path(temp));publisher.execute(order);write(fixture.workspace/"HQ2-package"/"lld-handoff-acceptance.json",{"tampered":True})
            with self.assertRaises((publisher.PublishFailure,publisher.ContractError)):publisher.validate_existing(order)

    def test_boundary_unallowlisted_internal_main_fails_before_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            _,_,order=self.build_hq2(Path(temp));self.remove_allowlist_role(order,"internal::consumer_test::member::handoff_consumption_test")
            with self.assertRaisesRegex(publisher.PublishFailure,"preauthorized|allowlist"):publisher.execute(order)

    def test_boundary_unallowlisted_upstream_validation_fails_before_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            _,_,order=self.build_hq2(Path(temp));self.remove_allowlist_role(order,"upstream::HP1::validation")
            with self.assertRaisesRegex(publisher.PublishFailure,"preauthorized|allowlist"):publisher.execute(order)

    def test_boundary_invalid_nonready_condition_schema_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture=Fixture(Path(temp));state_ref=fref(fixture.state,fixture.workspace,"state_before");up=fixture.upstream("HQ2");task=fixture.blocked_task("consumer_test",30,state_ref,up,invalid_condition=True);order=fixture.publish_order("HQ2",[task])
            with self.assertRaises(publisher.ContractError):publisher.execute(order)

    def test_boundary_extra_source_package_member_fails_closure(self):
        with tempfile.TemporaryDirectory() as temp:
            _,tasks,order=self.build_hq2(Path(temp),blocked=True);write(tasks[0].manifest.parent/"undeclared.tmp",b"extra")
            with self.assertRaises(publisher.ContractError):publisher.execute(order)

    def test_boundary_post_commit_validation_failure_rolls_back_canonical_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,_,order=self.build_hq2(Path(temp))
            with patch.object(publisher,"validate_existing",side_effect=publisher.PublishFailure("injected post-commit failure")):
                with self.assertRaisesRegex(publisher.PublishFailure,"injected post-commit"):publisher.execute(order)
            self.assertFalse((fixture.workspace/"HQ2-package").exists());self.assertFalse((fixture.workspace/"stage-result.json").exists())


if __name__=="__main__":unittest.main()
