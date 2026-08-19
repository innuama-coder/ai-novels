#!/usr/bin/env python3
"""Deterministic HH1-C renderer for the sealed A/B public contracts."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

SKILL_ROOT=Path(__file__).resolve().parents[1];REPO=SKILL_ROOT.parents[1];HARNESS_ROOT=REPO/"harnesses/novel-hld-autonomous"
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(HARNESS_ROOT))
from runtime.canonical import ContractError,canonical_sha256,read_json,write_json  # noqa:E402
from runtime.composite_internal_runtime import Context,InternalCondition,Spec,atomic_execute,finalize_condition,finalize_ready,finalize_runtime_error,load_context,sha256  # noqa:E402
from runtime.schema_catalog import SchemaCatalog  # noqa:E402
from render_validation import validate_render_model  # noqa:E402

SKILL="novel-hld-html-renderer";VERSION="1.0.0"
REQUIRED_ROLES=("hb0_completion","hp1_completion","hp1_manifest","novel_hld_package","hq2_completion","hq2_manifest","lld_handoff_acceptance","human_review_report","hh1_a_manifest","hh1_a_generation_session","hh1_a_work_order","presentation_fidelity_review","hh1_b_manifest","hh1_b_review_session","hh1_b_work_order")
SPEC=Spec(SKILL,VERSION,"HH1.C","hld-human-review-report.html","human_review_html","render-execution.json","render-execution.json","hh1-c-validation.schema.json",REQUIRED_ROLES)
REPORT_SCHEMA=REPO/"skills/novel-hld-review-report-assembler/references/hld-human-review-report.schema.json";REVIEW_SCHEMA=REPO/"skills/novel-hld-presentation-fidelity-reviewer/references/presentation-fidelity-review.schema.json"
A_SESSION_SCHEMA=REPO/"skills/novel-hld-review-report-assembler/references/hh1-a-generation-session.schema.json";B_SESSION_SCHEMA=REPO/"skills/novel-hld-presentation-fidelity-reviewer/references/hh1-b-review-session.schema.json"
OWN_SCHEMAS=(SKILL_ROOT/"references/render-target-registry.schema.json",SKILL_ROOT/"references/hh1-c-render-execution.schema.json",SKILL_ROOT/"references/hh1-c-validation.schema.json")
HARNESS_SCHEMA_NAMES=("common.schema.json","work-order.schema.json","input-gate.schema.json","package-manifest.schema.json","stage-completion.schema.json","lld-handoff-acceptance.schema.json","stage-result.schema.json","composite-internal-gate-data.schema.json","composite-internal-blocked-report.schema.json","composite-internal-revision-report.schema.json","composite-internal-runtime-error.schema.json","composite-local-defect-evidence.schema.json")
SECTIONS=(("overall_narrative_architecture","完整的故事会怎样发生"),("world_environment_definitions","故事发生在怎样的世界"),("character_definitions","这些人是谁"),("environment_definitions","这些地方是什么样"),("storyline_choreography","几条故事怎样碰到一起"),("character_arc_placement","人物最后会变成什么样"),("pov_information_suspense","读者会怎样知道真相"),("time_space_pacing_tension","时间和地点怎样推动故事"),("key_scene_functions","哪些场景决定故事能不能成立"),("open_items_constraints_and_lld_boundary","还需要作者拍板的内容"))
MODEL_LABELS={"architecture":"整体推进","storyline_convergence":"故事线汇流","character_arc":"人物选择与责任","information_chain":"信息揭示与回收"}

def schema_paths():return [REPORT_SCHEMA,REVIEW_SCHEMA,A_SESSION_SCHEMA,B_SESSION_SCHEMA,*OWN_SCHEMAS]
def implementation_paths():return [REPO/path for path in json.loads((SKILL_ROOT/"references/runtime-contract.json").read_text(encoding="utf-8"))["implementation_closure"]["ordered_files"]]
def impl_hash():
    paths=implementation_paths();digest=__import__("hashlib").sha256()
    if len(paths)!=len(set(paths)) or any(not path.is_file() for path in paths):raise RuntimeError("HH1-C implementation closure is invalid")
    for path in paths:
        relative=path.resolve().relative_to(REPO.resolve()).as_posix();digest.update(relative.encode("utf-8")+b"\0"+path.read_bytes()+b"\0")
    return digest.hexdigest()
def _catalog():
    paths=[*(HARNESS_ROOT/"schemas"/name for name in HARNESS_SCHEMA_NAMES),*schema_paths()];return SchemaCatalog.from_documents({str(path.resolve()):json.loads(path.read_text(encoding="utf-8")) for path in paths})
def _member(manifest:Mapping[str,Any],path:Path,package:Path)->bool:
    try:relative=path.resolve(strict=True).relative_to(package.resolve(strict=True)).as_posix()
    except ValueError:return False
    return sum(1 for item in manifest.get("files",[]) if item.get("path")==relative and item.get("sha256")==sha256(path))==1
def _artifact(ref:Mapping[str,Any],main:Path,manifest:Path,completion:Path,workspace:Path)->bool:
    return ref=={"path":main.relative_to(workspace).as_posix(),"sha256":sha256(main),"manifest_path":manifest.relative_to(workspace).as_posix(),"manifest_sha256":sha256(manifest),"completion_path":completion.relative_to(workspace).as_posix(),"completion_sha256":sha256(completion)}

def _validate_identity(context:Context,report:Mapping[str,Any],review:Mapping[str,Any],hp1:Mapping[str,Any],hp1_completion:Mapping[str,Any],hq2:Mapping[str,Any],hq2_completion:Mapping[str,Any])->None:
    run=context.work_order["hld_run_id"];revision=context.work_order["revision"]
    if any(value.get("hld_run_id")!=run for value in (report,review,hp1,hp1_completion,hq2,hq2_completion)) or report["revision"]!=revision or review["revision"]!=revision:raise InternalCondition("blocked","HH1C_IDENTITY_DRIFT","A/B consumer identity or sealed HP1/HQ2 run differs",["HH1-A","HH1-B","HP1","HQ2"])
    if (hp1.get("stage"),hp1.get("status"),hp1_completion.get("stage"))!=("HP1","ready","HP1") or (hq2.get("stage"),hq2.get("status"),hq2_completion.get("stage"))!=("HQ2","ready","HQ2"):raise InternalCondition("blocked","HH1C_IDENTITY_DRIFT","sealed HP1/HQ2 stage or readiness differs",["HP1","HQ2"])

def admit(context:Context)->dict[str,Any]:
    report=read_json(context.roles["human_review_report"]);review=read_json(context.roles["presentation_fidelity_review"]);a_manifest=read_json(context.roles["hh1_a_manifest"]);b_manifest=read_json(context.roles["hh1_b_manifest"]);a_session=read_json(context.roles["hh1_a_generation_session"]);b_session=read_json(context.roles["hh1_b_review_session"]);a_work=read_json(context.roles["hh1_a_work_order"]);b_work=read_json(context.roles["hh1_b_work_order"]);hp1=read_json(context.roles["novel_hld_package"]);hp1_completion=read_json(context.roles["hp1_completion"]);hp1_manifest=read_json(context.roles["hp1_manifest"]);hq2=read_json(context.roles["lld_handoff_acceptance"]);hq2_completion=read_json(context.roles["hq2_completion"]);hq2_manifest=read_json(context.roles["hq2_manifest"]);hb0_completion=read_json(context.roles["hb0_completion"])
    for value,schema in ((report,REPORT_SCHEMA.name),(review,REVIEW_SCHEMA.name),(a_manifest,"package-manifest.schema.json"),(b_manifest,"package-manifest.schema.json"),(a_session,A_SESSION_SCHEMA.name),(b_session,B_SESSION_SCHEMA.name),(a_work,"work-order.schema.json"),(b_work,"work-order.schema.json"),(hp1_completion,"stage-completion.schema.json"),(hp1_manifest,"package-manifest.schema.json"),(hq2,"lld-handoff-acceptance.schema.json"),(hq2_completion,"stage-completion.schema.json"),(hq2_manifest,"package-manifest.schema.json"),(hb0_completion,"stage-completion.schema.json")):context.catalog.validate(value,schema)
    if not _member(a_manifest,context.roles["human_review_report"],context.roles["hh1_a_manifest"].parent) or not _member(a_manifest,context.roles["hh1_a_generation_session"],context.roles["hh1_a_manifest"].parent):raise InternalCondition("blocked","HH1C_A_PACKAGE_UNSEALED","HH1-A report/session is not manifest-bound",["HH1-A"])
    if not _member(b_manifest,context.roles["presentation_fidelity_review"],context.roles["hh1_b_manifest"].parent) or not _member(b_manifest,context.roles["hh1_b_review_session"],context.roles["hh1_b_manifest"].parent):raise InternalCondition("blocked","HH1C_B_PACKAGE_UNSEALED","HH1-B review/session is not manifest-bound",["HH1-B"])
    if (a_work["task_id"],a_session["task_id"],review["review_bindings"]["assembler_task_id"])!=(a_work["task_id"],a_work["task_id"],a_work["task_id"]):raise InternalCondition("blocked","HH1C_A_TASK_BINDING_DRIFT","HH1-A producer task binding drift",["HH1-A"])
    if (b_work["task_id"],b_session["review_task_id"],review["review_bindings"]["reviewer_task_id"])!=(b_work["task_id"],b_work["task_id"],b_work["task_id"]):raise InternalCondition("blocked","HH1C_B_TASK_BINDING_DRIFT","HH1-B reviewer task binding drift",["HH1-B"])
    if len({a_work["task_id"],b_work["task_id"],context.work_order["task_id"]})!=3 or b_session["producer_task_id"]!=a_work["task_id"]:raise InternalCondition("blocked","HH1C_TASK_ISOLATION","A, B and C require three distinct correctly linked tasks",["HH1-A","HH1-B","HH1-C"],blocker_class="input_invalid")
    if a_session["actual_read_refs"]!=a_work["file_allowlist"] or b_session["declared_allowlist"]!=b_work["file_allowlist"] or b_session["actual_read_refs"]!=b_work["file_allowlist"]:raise InternalCondition("blocked","HH1C_PRODUCER_READ_CLOSURE_DRIFT","sealed A/B session does not equal its producer allowlist",["HH1-A","HH1-B"])
    _validate_identity(context,report,review,hp1,hp1_completion,hq2,hq2_completion)
    if report["hp1_content_binding"]!={"package_sha256":sha256(context.roles["novel_hld_package"]),"completion_sha256":sha256(context.roles["hp1_completion"])} or report["hq2_gate_binding"]!={"acceptance_sha256":sha256(context.roles["lld_handoff_acceptance"]),"bound_hp1_package_sha256":sha256(context.roles["novel_hld_package"])}:raise InternalCondition("blocked","HH1C_REPORT_UPSTREAM_BINDING_DRIFT","report does not bind current HP1/HQ2",["HH1-A"])
    expected_review={"hp1_package_sha256":sha256(context.roles["novel_hld_package"]),"report_sha256":sha256(context.roles["human_review_report"]),"report_manifest_sha256":sha256(context.roles["hh1_a_manifest"]),"assembler_task_id":a_work["task_id"],"reviewer_task_id":b_work["task_id"]}
    if review["review_bindings"]!=expected_review or review["verdict"]!="pass" or review["defect_origin"]!="none" or review["material_drift_findings"] or review["cognitive_overload_findings"] or any(review[name]["verdict"]!="pass" for name in ("fact_fidelity","structure_and_relation_fidelity","coverage_fidelity","authority_and_open_item_fidelity","visual_data_fidelity")) or any(item["verdict"]!="pass" for item in review["decision_retrieval_tests"]) or review["reading_budget_validation"]["verdict"]!="pass":raise InternalCondition("blocked","HH1C_FIDELITY_NOT_PASS","HH1-B is not a sealed exact pass for this report",["HH1-B"])
    if hp1_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hp1_manifest"]) or hq2_completion["manifest_ref"]["sha256"]!=sha256(context.roles["hq2_manifest"]) or not _member(hp1_manifest,context.roles["novel_hld_package"],context.roles["hp1_manifest"].parent) or not _member(hq2_manifest,context.roles["lld_handoff_acceptance"],context.roles["hq2_manifest"].parent):raise InternalCondition("blocked","HH1C_PUBLIC_ENVELOPE_DRIFT","HP1/HQ2 public envelopes are stale",["HP1","HQ2"])
    if q:=hq2.get("hp1_completion_ref"):
        if q["sha256"]!=sha256(context.roles["hp1_completion"]):raise InternalCondition("blocked","HH1C_HQ2_HP1_DRIFT","HQ2 does not bind current HP1",["HQ2"])
    if hq2["hb0_completion_ref"]["sha256"]!=sha256(context.roles["hb0_completion"]):raise InternalCondition("blocked","HH1C_HQ2_HB0_DRIFT","HQ2 does not bind current HB0",["HQ2"])
    if len(context.work_order["upstream_completions"])!=3 or not _artifact(context.work_order["upstream_completions"][1],context.roles["novel_hld_package"],context.roles["hp1_manifest"],context.roles["hp1_completion"],context.workspace) or not _artifact(context.work_order["upstream_completions"][2],context.roles["lld_handoff_acceptance"],context.roles["hq2_manifest"],context.roles["hq2_completion"],context.workspace):raise InternalCondition("blocked","HH1C_UPSTREAM_ARTIFACT_DRIFT","work-order does not bind current HB0/HP1/HQ2",["HP1","HQ2"],blocker_class="input_invalid")
    hb=context.work_order["upstream_completions"][0]
    if hb["completion_path"]!=context.roles["hb0_completion"].relative_to(context.workspace).as_posix() or hb["completion_sha256"]!=sha256(context.roles["hb0_completion"]):raise InternalCondition("blocked","HH1C_HB0_ARTIFACT_DRIFT","work-order HB0 completion drift",["HB0"],blocker_class="input_invalid")
    return {"report":report,"review":review,"a_task":a_work["task_id"],"b_task":b_work["task_id"]}

def esc(value:Any)->str:return html.escape(str(value),quote=True)
def binding_html(item:Mapping[str,Any])->str:
    pairs="".join(f"<li><code>{esc(source)}</code><br><code>{esc(locator)}</code></li>" for source,locator in zip(item["source_ids"],item["locators"]))
    return f'<details class="bindings"><summary>依据与定位</summary><ul>{pairs}</ul></details>'
def target(item:Mapping[str,Any],role:str)->dict[str,Any]:
    hui=f"HUI-{item['id']}-{role}-0";return {"id":hui,"dom_locator":f'[data-render-target-id="{hui}"]',"render_role":role,"source_visual_role":item["visual_role"],"report_element_id":item["id"],"report_element_kind":item["element_kind"],"visual_model_id":item["id"] if item["id"].startswith("HVG-") else None,"content_sha256":canonical_sha256(item)}
def prose_html(value:Any)->str:
    paragraphs=[part.strip() for part in re.split(r"\n\s*\n",str(value)) if part.strip()]
    return "".join(f"<p>{esc(part)}</p>" for part in paragraphs)
def natural_sentence_list(values:list[str])->str:
    parts=[str(value).strip().rstrip("。；;") for value in values if str(value).strip()]
    return "；".join(parts)+("。" if parts else "")
def render_hre(item:Mapping[str,Any],*,heading_level:int=3,featured:bool=False,show_question:bool=False)->tuple[str,dict[str,Any]]:
    record=target(item,"report_element");heading=f"{record['id']}-heading"
    if heading_level not in {2,3}:raise ValueError("unsupported HRE heading level")
    tag=f"h{heading_level}";classes="report-element first-screen-story" if featured else "report-element"
    question=f'<div class="review-question"><h4>最后，请决定这一点</h4>{prose_html(item["review_question"])}</div>' if show_question else ""
    body=f'<article class="{classes}" data-render-target-id="{esc(record["id"])}" data-report-element-id="{esc(item["id"])}" aria-labelledby="{esc(heading)}"><{tag} id="{esc(heading)}">{esc(item["visual_role"])}</{tag}>{prose_html(item["conclusion"])}{question}</article>'
    return body,record
def render_chapter_design(item:Mapping[str,Any])->tuple[str,dict[str,Any]]:
    record=target(item,"report_element");heading=f"{record['id']}-heading"
    labels={"primary":"主要推进","supporting":"同时推进","background":"形成背景压力","preserved_open":"继续悬而未决"}
    grouped={role:[] for role in labels}
    for storyline in item["storylines"]:grouped[storyline["role"]].append(storyline["name"])
    storylines="".join(f'<li><strong>{esc(labels[role])}：</strong>{esc("、".join(names))}</li>' for role,names in grouped.items() if names)
    body=(f'<article class="report-element chapter-card" data-render-target-id="{esc(record["id"])}" '
          f'data-report-element-id="{esc(item["id"])}" aria-labelledby="{esc(heading)}">'
          f'<h3 id="{esc(heading)}">{esc(item["visual_role"])}</h3>'
          f'<h4>这一章要讲清什么</h4>{prose_html(item["core_content"])}'
          f'<h4>这一章推进哪些故事</h4><ul class="chapter-storylines">{storylines}</ul>'
          f'<h4>本章结束时发生的变化</h4>{prose_html(item["chapter_end_change"])}</article>')
    return body,record
def render_definition(item:Mapping[str,Any])->tuple[str,dict[str,Any]]:
    record=target(item,"report_element");heading=f"{record['id']}-heading";extra=""
    if item["element_kind"]=="character_definition":
        paragraphs=[item["conclusion"],item["story_position"],item["personality_and_motivation"],item["capabilities_and_limits"],item["relationships_and_change"]]
    elif item["element_kind"]=="environment_definition":
        paragraphs=[item["conclusion"],item["story_function"],item["physical_character"],item["access_and_limits"],item["dramatic_use"]]
    elif item["element_kind"]=="world_environment_definition":
        features=natural_sentence_list(item["defining_features"]);open_details=natural_sentence_list(item["author_open_details"]) if item["author_open_details"] else "这一部分已经定清，不需要再补充决定。"
        paragraphs=[item["definition"],features,item["people_and_daily_life"],item["story_pressure_and_limits"],open_details]
        if stories:=item.get("city_stories"):
            city_cards="".join(f'<article class="city-card"><h4>{esc(story["city_name"])}</h4>{prose_html(story["story"])}</article>' for story in stories)
            route_cards="".join(f'<article class="intercity-link-card"><h4>从{esc(story["from_city"])}到{esc(story["to_city"])}</h4>{prose_html(story["story"])}</article>' for story in item["route_stories"])
            extra=f'<section class="city-network" aria-label="四座城市"><h4>四座城市</h4>{city_cards}<h4>人和消息怎样在城市之间移动</h4>{route_cards}</section>'
        elif stories:=item.get("ordinary_people_stories"):
            cards="".join(f'<article class="ordinary-person-card"><h4>{esc(story["portrait_name"])}</h4><p class="portrait-city">生活在{esc(story["city"])}</p>{prose_html(story["story"])}</article>' for story in stories)
            extra=f'<section class="ordinary-people" aria-label="生活在四座城市里的人"><h4>生活在四座城市里的人</h4>{cards}</section>'
        elif story:=item.get("season_story"):
            extra=f'<section class="season-story" aria-label="六周里的天气"><h4>六周里的天气</h4>{prose_html(story)}</section>'
    else:raise InternalCondition("revise","HH1C_DEFINITION_KIND_UNKNOWN",item.get("element_kind",""),[item.get("id","")])
    body=f'<article class="report-element definition-card" data-render-target-id="{esc(record["id"])}" data-report-element-id="{esc(item["id"])}" aria-labelledby="{esc(heading)}"><h3 id="{esc(heading)}">{esc(item["name"])}</h3><div class="definition-story">{"".join(prose_html(value) for value in paragraphs)}</div>{extra}</article>'
    return body,record
def render_visual(item:Mapping[str,Any])->tuple[str,dict[str,Any]]:
    record=target(item,"visual_model");hui=record["id"];heading=f"{hui}-heading";title=f"{hui}-svg-title";desc=f"{hui}-svg-desc";nodes=item["nodes"];node_ids={node["id"] for node in nodes}
    if len(node_ids)!=len(nodes):raise InternalCondition("blocked","HH1C_VISUAL_NODE_DUPLICATE",item["id"],[item["id"]])
    for edge in item["edges"]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:raise InternalCondition("blocked","HH1C_VISUAL_EDGE_DANGLING",item["id"],[item["id"]])
    coords={node["id"]:(120+(index%3)*280,100+(index//3)*150) for index,node in enumerate(nodes)};height=max(250,180+((len(nodes)-1)//3)*150);parts=[f'<svg viewBox="0 0 840 {height}" role="img" aria-labelledby="{title} {desc}" xmlns="http://www.w3.org/2000/svg"><title id="{title}">{esc(item["conclusion"])}</title><desc id="{desc}">{esc(item["text_alternative"])}</desc>']
    labels={node["id"]:node["label"] for node in nodes}
    for index,edge in enumerate(item["edges"]):
        x1,y1=coords[edge["from"]];x2,y2=coords[edge["to"]];et=f"{hui}-edge-{index}-title";parts.append(f'<g role="group" aria-labelledby="{et}" data-svg-edge="{index}"><title id="{et}">{esc(labels[edge["from"]])}到{esc(labels[edge["to"]])}：{esc(edge["label"])}</title><line class="svg-edge" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/></g>')
    for index,node in enumerate(nodes):
        x,y=coords[node["id"]];nt=f"{hui}-node-{index}-title";parts.append(f'<g role="group" aria-labelledby="{nt}" data-svg-node="{esc(node["id"])}"><title id="{nt}">{esc(node["label"])}</title><rect class="svg-node" x="{x-90}" y="{y-34}" width="180" height="68" rx="8"/><text class="svg-label" x="{x}" y="{y+5}">{esc(node["label"])}</text></g>')
    parts.append("</svg>")
    model_label=MODEL_LABELS.get(item["model_kind"])
    if model_label is None:raise InternalCondition("revise","HH1C_VISIBLE_MODEL_KIND_UNKNOWN",f"unknown visible model kind: {item['model_kind']}",[item["id"]])
    body=f'<figure class="report-element visual-model" data-render-target-id="{esc(hui)}" data-report-element-id="{esc(item["id"])}" aria-labelledby="{esc(heading)}"><figcaption><h3 id="{esc(heading)}">{esc(item["visual_role"])}</h3><p>{esc(item["conclusion"])}</p></figcaption>{"".join(parts)}<p class="visual-text">{esc(item["text_alternative"])}</p></figure>'
    return body,record
def work_title(report:Mapping[str,Any])->str:
    orientation=report["title_and_decision_scope"][0]["conclusion"];match=re.match(r"^《([^》]+)》",orientation)
    return match.group(1) if match else "小说"
def render_document(report:Mapping[str,Any],review:Mapping[str,Any])->tuple[str,list[dict[str,Any]]]:
    template=(SKILL_ROOT/"assets/template.html").read_text(encoding="utf-8");css=(SKILL_ROOT/"assets/styles.css").read_text(encoding="utf-8");targets=[];title=work_title(report);title_item=report["title_and_decision_scope"][0];title_target=target(title_item,"report_element");first_story=report["overall_narrative_architecture"][0];featured,featured_target=render_hre(first_story,heading_level=2,featured=True);targets.extend((title_target,featured_target));body=['<a class="skip-link" href="#review-main">跳到主要内容</a>',f'<header data-render-target-id="{esc(title_target["id"])}" data-report-element-id="{esc(title_item["id"])}"><h1>《{esc(title)}》</h1>{featured}</header>'];toc="".join(f'<li><a href="#{name}">{label}</a></li>' for name,label in SECTIONS);body.append(f'<nav aria-label="目录"><h2>目录</h2><ol>{toc}</ol></nav><main id="review-main">')
    for name,label in SECTIONS:
        body.append(f'<section id="{name}" aria-labelledby="{name}-heading"><h2 id="{name}-heading">{label}</h2>')
        for item in report[name]:
            if item["id"]==first_story["id"]:continue
            if item.get("element_kind")=="chapter_design":rendered,record=render_chapter_design(item)
            elif name in {"world_environment_definitions","character_definitions","environment_definitions"}:rendered,record=render_definition(item)
            else:rendered,record=render_hre(item,show_question=name=="open_items_constraints_and_lld_boundary")
            body.append(rendered);targets.append(record)
        body.append("</section>")
    if report["visual_models"]:
        body.append('<section id="visual_models" aria-labelledby="visual_models-heading"><h2 id="visual_models-heading">一眼看懂人物与事件</h2>')
        for item in report["visual_models"]:rendered,record=render_visual(item);body.append(rendered);targets.append(record)
        body.append('</section>')
    body.append(f'</main><footer>《{esc(title)}》故事方案</footer>')
    document=template.replace("{{LANG}}","zh-CN").replace("{{DOCUMENT_TITLE}}",f"《{esc(title)}》故事方案").replace("{{INLINE_CSS}}",css).replace("{{BODY}}","\n".join(body))
    if any(token in document for token in ("{{LANG}}","{{DOCUMENT_TITLE}}","{{INLINE_CSS}}","{{BODY}}")):raise InternalCondition("revise","HH1C_TEMPLATE_TOKEN_UNRESOLVED","renderer template contains unresolved tokens")
    return document,targets

def build_ready(context:Context,staging:Path,admitted:Mapping[str,Any])->dict[str,Any]:
    document,targets=render_document(admitted["report"],admitted["review"]);binding={"implementation_sha256":impl_hash(),"template_sha256":sha256(SKILL_ROOT/"assets/template.html"),"stylesheet_sha256":sha256(SKILL_ROOT/"assets/styles.css"),"report_schema_sha256":sha256(REPORT_SCHEMA),"fidelity_schema_sha256":sha256(REVIEW_SCHEMA)}
    refs={item["role"]:item for item in context.work_order["file_allowlist"]};registry={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":context.work_order["hld_run_id"],"stage":"HH1","skill":SKILL,"report_ref":refs["human_review_report"],"fidelity_review_ref":refs["presentation_fidelity_review"],"renderer_binding":binding,"targets":targets}
    context.catalog.validate(registry,"render-target-registry.schema.json");errors=validate_render_model(document,admitted["report"],registry)
    if errors:raise InternalCondition("revise","HH1C_RENDER_MODEL_INVALID","; ".join(errors),[item["id"] for item in targets])
    staging.mkdir(parents=True,exist_ok=False);(staging/SPEC.canonical_name).write_text(document,encoding="utf-8",newline="\n");write_json(staging/"render-target-registry.json",registry)
    execution={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"assembler_task_id":admitted["a_task"],"reviewer_task_id":admitted["b_task"],"implementation_sha256":impl_hash(),"actual_read_refs":context.work_order["file_allowlist"],"html_sha256":sha256(staging/SPEC.canonical_name),"registry_sha256":sha256(staging/"render-target-registry.json"),"deterministic":True};context.catalog.validate(execution,"hh1-c-render-execution.schema.json");write_json(staging/"render-execution.json",execution)
    validation={"schema_version":"1.0","skill":SKILL,"stage":"HH1","hld_run_id":context.work_order["hld_run_id"],"status":"pass","checks":["exact-read-closure","a-b-task-isolation","hp1-hq2-hb0-binding","report-review-current-pass","hre-hvg-hui-bijection","author-visible-language","nested-svg-accessibility","offline-single-file","responsive-print","deterministic-reproduction"],"errors":[]};context.catalog.validate(validation,"hh1-c-validation.schema.json");write_json(staging/"validation.json",validation)
    return finalize_ready(context,staging,{SPEC.canonical_name:"human_review_html","render-target-registry.json":"render_target_registry","render-execution.json":"execution_record","validation.json":"validation"})

def execute(work_order:Path)->tuple[int,dict[str,Any]]:
    context=load_context(work_order,SPEC,impl_hash(),_catalog())
    def build(ctx:Context,staging:Path):
        try:
            try:admitted=admit(ctx)
            except ContractError as error:raise InternalCondition("blocked","HH1C_UPSTREAM_SCHEMA_INVALID",str(error),["HH1-A","HH1-B"]) from error
            return 0,build_ready(ctx,staging,admitted)
        except InternalCondition as condition:return 2,finalize_condition(ctx,staging,condition)
        except Exception as error:return 1,finalize_runtime_error(ctx,staging,error,"HH1-C admission/render/sealing")
    return atomic_execute(context,build)
def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("work_order",type=Path);args=parser.parse_args(argv)
    try:code,_=execute(args.work_order);return code
    except Exception as error:print(str(error),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
