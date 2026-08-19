"""Deterministic HTML/registry validation for HH1-C."""
from __future__ import annotations
import hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any,Mapping

PROFILE={"hld-human-review-report.html","render-target-registry.json","render-execution.json","validation.json","package-manifest.json"}
AUTHOR_PROSE_FORBIDDEN=re.compile(
    r"(?:高层设计|详细设计|人审(?:稿|报告)?|评审(?:范围|方法|问题)?|审阅(?:范围|方法)?|设计入口|场景任务|"
    r"(?:证据|责任|授权|决策|核验|行动)链|闭环|闭合(?:整条|整个)|(?:活动|数字|秘密项目)载体|"
    r"(?:当前|活动|不活动)实例|(?:行动|原因|输入|输出)层|可执行|不可执行|可追责|审计|核验|权限|"
    r"接口|原子记录|只写|只读输入|post-dispatch|人物变化：|出场时：|结尾时：|主要风险：|"
    r"进入时处于|关键变化后达到|不可替代职责|(?:顾衡|沈逾|R-07|现实调查|两国)线负责|"
    r"保持开放|回收落点|证据入口|映射|投影|链路|抓手|维度|颗粒度|赋能|沉淀|对齐|拉通|兜底|"
    r"方法论|范式|结构化输出|职责分工|能力边界|信息边界|决策点|控制点|状态机|工作流|流水线|"
    r"上下游|生产者|消费者|检索召回)",re.I)
CJK=re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.ids=[];self.targets=[];self.report_ids=[];self.bad=[];self.external=[];self.h1=0;self.landmarks=set();self.skip=False;self.title_text=[];self.in_doc_title=False;self.svg=[];self._svg=[];self.node_targets=[];self.edge_targets=[];self.visible_blocks=[];self._visible=[];self._ignored=0;self._nav=0
    def handle_starttag(self,tag,attrs):
        values={k:(v or "") for k,v in attrs}
        if tag in {"style","script","template","noscript"}:self._ignored+=1
        if tag=="nav":self._nav+=1
        if not self._ignored and not self._nav and tag in {"h1","h2","h3","h4","h5","h6","p","dt","dd","li"}:self._visible.append([tag,[]])
        if tag in {"script","iframe","object","embed","link","base","form","input","button"}:self.bad.append(tag)
        for key in ("src","href","xlink:href","action","formaction"):
            if key in values and not (key=="href" and values[key].startswith("#")):self.external.append(f"{tag}.{key}")
        if "id" in values:self.ids.append(values["id"])
        if values.get("data-render-target-id"):self.targets.append(values["data-render-target-id"])
        if values.get("data-report-element-id"):self.report_ids.append(values["data-report-element-id"])
        if values.get("data-svg-node"):self.node_targets.append(values["data-svg-node"])
        if values.get("data-svg-edge"):self.edge_targets.append(values["data-svg-edge"])
        if tag=="h1":self.h1+=1
        if tag in {"header","nav","main","footer"}:self.landmarks.add(tag)
        if tag=="a" and values.get("class")=="skip-link" and values.get("href")=="#review-main":self.skip=True
        if tag=="title" and not self._svg:self.in_doc_title=True
        if tag=="svg":self._svg.append({"role":values.get("role"),"labelledby":values.get("aria-labelledby"),"title":False,"desc":False})
        elif self._svg and tag=="title":self._svg[-1]["title"]=True
        elif self._svg and tag=="desc":self._svg[-1]["desc"]=True
    def handle_endtag(self,tag):
        if self._visible and self._visible[-1][0]==tag:
            _,parts=self._visible.pop();value=re.sub(r"\s+"," ","".join(parts)).strip()
            if value:self.visible_blocks.append(value)
        if tag=="nav" and self._nav:self._nav-=1
        if tag in {"style","script","template","noscript"} and self._ignored:self._ignored-=1
        if tag=="title" and not self._svg:self.in_doc_title=False
        if tag=="svg" and self._svg:self.svg.append(self._svg.pop())
    def handle_data(self,data):
        if self.in_doc_title:self.title_text.append(data)
        if self._visible and not self._ignored and not self._nav:self._visible[-1][1].append(data)
def canonical_sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()
def elements(report):return [item for name in ("title_and_decision_scope","overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","pov_information_suspense","time_space_pacing_tension","key_scene_functions","open_items_constraints_and_lld_boundary","visual_models") for item in report[name]]
def validate_author_visible_language(blocks:list[str])->list[str]:
    errors=[];seen={}
    for index,value in enumerate(blocks):
        if AUTHOR_PROSE_FORBIDDEN.search(value):errors.append(f"visible block {index} uses machine/process wording")
        if CJK.search(value) and value.count("；")>=3:errors.append(f"visible block {index} compresses too many conclusions")
        for sentence in re.split(r"[。！？!?]",value):
            if len(CJK.findall(sentence))>90:errors.append(f"visible block {index} contains an overlong compressed sentence")
        normalized=re.sub(r"\s+","",value).strip("。；，：、!?！？")
        if len(CJK.findall(normalized))>=12:
            previous=seen.get(normalized)
            if previous is not None:errors.append(f"visible block {index} repeats substantive block {previous}")
            else:seen[normalized]=index
    return errors
def validate_render_model(document:str,report:Mapping[str,Any],registry:Mapping[str,Any])->list[str]:
    errors=[];parser=Parser();parser.feed(document);items=elements(report);item_by_id={item["id"]:item for item in items};targets=registry.get("targets",[]);registry_ids=[item.get("id") for item in targets];registry_reports=[item.get("report_element_id") for item in targets]
    if len(item_by_id)!=len(items):errors.append("duplicate report element IDs")
    if len(registry_ids)!=len(set(registry_ids)) or len(registry_reports)!=len(set(registry_reports)):errors.append("duplicate registry target")
    if set(registry_reports)!=set(item_by_id) or len(registry_reports)!=len(item_by_id):errors.append("report/registry element bijection failed")
    if parser.targets!=registry_ids or parser.report_ids!=registry_reports:errors.append("DOM/registry ordered bijection failed")
    if len(parser.ids)!=len(set(parser.ids)):errors.append("duplicate DOM ID")
    if parser.bad or parser.external:errors.append(f"offline/security violation tags={parser.bad} attrs={parser.external}")
    if parser.h1!=1 or parser.landmarks!={"header","nav","main","footer"} or not parser.skip or not "".join(parser.title_text).strip():errors.append("document landmark/title contract failed")
    if chr(0xfffd) in document:errors.append("Unicode replacement character detected")
    errors.extend(validate_author_visible_language(parser.visible_blocks))
    for entry in targets:
        identifier=entry.get("id");report_id=entry.get("report_element_id");expected_role="visual_model" if str(report_id).startswith("HVG-") else "report_element"
        if identifier!=f"HUI-{report_id}-{expected_role}-0" or entry.get("render_role")!=expected_role or entry.get("dom_locator")!=f'[data-render-target-id="{identifier}"]':errors.append(f"HUI formula/locator mismatch: {report_id}")
        if report_id not in item_by_id or entry.get("content_sha256")!=canonical_sha(item_by_id.get(report_id,{})):errors.append(f"content hash mismatch: {report_id}")
        if entry.get("source_visual_role")!=item_by_id.get(report_id,{}).get("visual_role"):errors.append(f"source visual role drift: {report_id}")
    visuals=report["visual_models"]
    if len(parser.svg)!=len(visuals):errors.append("visual/SVG count mismatch")
    for index,svg in enumerate(parser.svg):
        if svg["role"]!="img" or not svg["labelledby"] or not svg["title"] or not svg["desc"]:errors.append(f"SVG {index} lacks accessible title/description")
    expected_nodes=[node["id"] for visual in visuals for node in visual["nodes"]];expected_edges=[str(index) for visual in visuals for index,_ in enumerate(visual["edges"])]
    if parser.node_targets!=expected_nodes:errors.append("SVG node accessible-target closure mismatch")
    if parser.edge_targets!=expected_edges:errors.append("SVG edge accessible-target closure mismatch")
    for visual in visuals:
        node_ids={node["id"] for node in visual["nodes"]}
        if len(node_ids)!=len(visual["nodes"]) or any(edge["from"] not in node_ids or edge["to"] not in node_ids for edge in visual["edges"]):errors.append(f"visual graph invalid: {visual['id']}")
    for token in ("@media print","@page","overflow-wrap:anywhere","@media(max-width:40rem)","@media(forced-colors:active)"):
        if token not in document:errors.append(f"missing responsive/print token: {token}")
    return errors
def validate_package(package:Path,report:Mapping[str,Any]|None=None)->list[str]:
    if not package.is_dir():return ["package missing"]
    actual={p.name for p in package.iterdir() if p.is_file()}
    if actual!=PROFILE:return [f"profile mismatch: {sorted(actual)}"]
    try:registry=json.loads((package/"render-target-registry.json").read_text(encoding="utf-8"));manifest=json.loads((package/"package-manifest.json").read_text(encoding="utf-8"));document=(package/"hld-human-review-report.html").read_text(encoding="utf-8")
    except Exception as error:return [f"read failure: {error}"]
    errors=[]
    if report is not None:errors.extend(validate_render_model(document,report,registry))
    declared={item.get("path") for item in manifest.get("files",[]) if isinstance(item,dict)}
    if declared!=PROFILE-{"package-manifest.json"}:errors.append("manifest closure mismatch")
    for item in manifest.get("files",[]):
        path=package/item.get("path","")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item.get("sha256"):errors.append(f"manifest hash mismatch: {item.get('path')}")
    return errors
