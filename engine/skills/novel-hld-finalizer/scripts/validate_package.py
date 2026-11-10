#!/usr/bin/env python3
"""Standard-library deterministic HF1 finalizer and validator."""
from __future__ import annotations
import argparse,hashlib,json,re,shutil
from pathlib import Path

STAGE="HF1";SKILL="novel-hld-finalizer";CHAIN=["HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1","HQ1","HP1","HQ2","HH1"]
STAGE_SKILLS={"HB0":"novel-hld-baseline-admitter","HA1":"novel-hld-narrative-architect","HS1":"novel-hld-storyline-choreographer","HC1":"novel-hld-character-arc-placer","HI1":"novel-hld-information-architect","HR1":"novel-hld-rhythm-continuity-architect","HK1":"novel-hld-key-scene-function-planner","HD1":"novel-hld-chapter-definition-designer","HQ1":"novel-hld-semantic-reviewer","HP1":"novel-hld-package-assembler","HQ2":"novel-hld-lld-readiness-evaluator","HH1":"novel-hld-human-review-composite"}
PUBLIC_STAGE_SKILLS={**STAGE_SKILLS,"HQ2":"harness-core/composite-stage-publisher","HH1":"harness-core/composite-stage-publisher"}
UPSTREAM={"HB0":(),"HA1":("HB0",),"HS1":("HB0","HA1"),"HC1":("HB0","HA1","HS1"),"HI1":("HB0","HA1","HS1","HC1"),"HR1":("HB0","HA1","HS1","HC1","HI1"),"HK1":("HB0","HA1","HS1","HC1","HI1","HR1"),"HD1":("HB0","HA1","HS1","HC1","HI1","HR1","HK1"),"HQ1":("HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1"),"HP1":("HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1","HQ1"),"HQ2":("HB0","HP1"),"HH1":("HB0","HP1","HQ2")}
CORE_ROLES={"run_state","author_decision","hp1_package","hp1_manifest","lld_handoff","hld_cross_index","hq2_acceptance","hh1_manifest","hh1_html","render_target_registry"}
EXACT_ROLES=CORE_ROLES|{f"validation_{stage}" for stage in CHAIN}
APPROVED={"hld-completion.json","final-validation.json","finalizer-execution.json","package-manifest.json"}
REVISE={"author-decision.json","revision-report.json","finalizer-execution.json","validation.json","result-manifest.json"}
BLOCKED={"gate-data.json","blocked-report.json","validation.json","result-manifest.json"}
FORBIDDEN_NAMES={"run-state.json","revision-plan.json","return-request.json","lld-content.json","stage-completion.json"}

def read(p):
    with Path(p).open("r",encoding="utf-8") as f:return json.load(f)
def write(p,obj):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8",newline="\n")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(role,path,root):return {"role":role,"path":Path(path).resolve().relative_to(Path(root).resolve()).as_posix(),"sha256":sha(path)}
def resolve(root,r):
    p=(Path(root)/str(r.get("path",""))).resolve();base=Path(root).resolve()
    if p!=base and base not in p.parents:raise ValueError("reference escapes workspace")
    return p
def same_ref(left,right):return all(left.get(k)==right.get(k) for k in ("path","sha256"))
def package_files(p):return {x.relative_to(p).as_posix() for x in Path(p).rglob("*") if x.is_file()}

def schema_errors(value,schema,root,path="$",errors=None):
    if errors is None:errors=[]
    if "$ref" in schema:
        target=root
        try:
            for part in schema["$ref"][2:].split("/"):target=target[part]
        except Exception:return errors+[f"schema {path}: unresolved ref"]
        return schema_errors(value,target,root,path,errors)
    if "const" in schema and value!=schema["const"]:errors.append(f"schema {path}: const mismatch")
    if "enum" in schema and value not in schema["enum"]:errors.append(f"schema {path}: enum mismatch")
    checks={"object":lambda x:isinstance(x,dict),"array":lambda x:isinstance(x,list),"string":lambda x:isinstance(x,str),"integer":lambda x:isinstance(x,int) and not isinstance(x,bool),"number":lambda x:isinstance(x,(int,float)) and not isinstance(x,bool)};kind=schema.get("type")
    if kind in checks and not checks[kind](value):errors.append(f"schema {path}: {kind} required");return errors
    if isinstance(value,dict):
        props=schema.get("properties",{})
        for k in schema.get("required",[]):
            if k not in value:errors.append(f"schema {path}: missing {k}")
        if schema.get("additionalProperties") is False:
            for k in value.keys()-props.keys():errors.append(f"schema {path}: additional {k}")
        for k,s in props.items():
            if k in value:schema_errors(value[k],s,root,f"{path}/{k}",errors)
    if isinstance(value,list):
        if len(value)<schema.get("minItems",0):errors.append(f"schema {path}: too few items")
        if isinstance(schema.get("items"),dict):
            for i,x in enumerate(value):schema_errors(x,schema["items"],root,f"{path}/{i}",errors)
    if isinstance(value,str):
        if len(value)<schema.get("minLength",0):errors.append(f"schema {path}: string too short")
        if "pattern" in schema and re.search(schema["pattern"],value) is None:errors.append(f"schema {path}: pattern mismatch")
    if isinstance(value,int) and not isinstance(value,bool) and value<schema.get("minimum",value):errors.append(f"schema {path}: below minimum")
    return errors

def validate_schema(obj,name):
    schema=read(Path(__file__).resolve().parents[1]/"references"/name);return schema_errors(obj,schema,schema)

def preflight(w,g):
    e=[]
    required_work={"schema_version","harness","hld_run_id","revision","work_order_id","task_id","stage","action","exact_owner_skill","owner_version","implementation_sha256","event_sequence","result_timestamp","input_gate_ref","state_before_ref","upstream_completions","file_allowlist","unresolved_projection","mode","return_binding","revision_plan_ref","revision_plan_state_ref","output_directory","submission_status"}
    required_gate={"schema_version","harness","hld_run_id","stage","mode","state_before_ref","hb0_completion_ref","upstream_completions","baseline_manifest_ref","baseline_validation_ref","source_lineage_refs","exact_owner_skill","owner_version","implementation_sha256","return_binding","unresolved_projection","revision_plan_ref","revision_plan_state_ref","file_allowlist"}
    if set(w)!=required_work:e.append("work-order public field set mismatch")
    if set(g)!=required_gate:e.append("input-gate public field set mismatch")
    if w.get("schema_version")!="1.0" or g.get("schema_version")!="1.0" or w.get("harness")!="novel-hld-autonomous" or g.get("harness")!="novel-hld-autonomous":e.append("public envelope identity mismatch")
    if w.get("stage")!=STAGE or g.get("stage")!=STAGE:e.append("stage must be HF1")
    if w.get("exact_owner_skill")!=SKILL or g.get("exact_owner_skill")!=SKILL:e.append("wrong exact owner")
    if w.get("action")!="execute":e.append("action must be execute")
    if w.get("hld_run_id")!=g.get("hld_run_id"):e.append("run mismatch")
    if w.get("mode")!="forward" or w.get("return_binding") is not None:e.append("HF1 requires forward mode without return binding")
    for field in ("hld_run_id","stage","exact_owner_skill","owner_version","implementation_sha256","mode","return_binding","revision_plan_ref","revision_plan_state_ref","unresolved_projection","file_allowlist","state_before_ref","upstream_completions"):
        if w.get(field)!=g.get(field):e.append(f"work-order/input-gate mismatch: {field}")
    if w.get("file_allowlist")!=g.get("file_allowlist"):e.append("allowlist mismatch")
    roles=[x.get("role") for x in w.get("file_allowlist",[]) if isinstance(x,dict)]
    if set(roles)!=EXACT_ROLES or len(roles)!=len(EXACT_ROLES):e.append("HF1 input role set must be exact")
    if len(w.get("upstream_completions",[]))!=len(CHAIN):e.append("HF1 requires eleven upstream completions")
    elif g.get("hb0_completion_ref")!=w["upstream_completions"][0]:e.append("input-gate HB0 binding mismatch")
    if g.get("baseline_manifest_ref") is not None or g.get("baseline_validation_ref") is not None or g.get("source_lineage_refs")!=[]:e.append("HF1 forbids undeclared baseline/source inputs")
    if w.get("submission_status")!="open" or not isinstance(w.get("output_directory"),str) or not w.get("output_directory") or Path(w["output_directory"]).is_absolute():e.append("invalid public work-order delivery fields")
    if w.get("unresolved_projection") or g.get("unresolved_projection"):e.append("HF1 has no unresolved projection")
    return e

def verify_manifest_closure(ws,artifact,stage,validation_ref):
    """Verify the public acyclic envelope: manifest closes content; completion binds it."""
    e=[]
    try:
        canonical=resolve(ws,{"path":artifact["path"]});completion=resolve(ws,{"path":artifact["completion_path"]});manifest_path=resolve(ws,{"path":artifact["manifest_path"]})
        if not canonical.is_file() or sha(canonical)!=artifact["sha256"]:e.append(f"canonical artifact mismatch: {stage}")
        if not completion.is_file() or sha(completion)!=artifact["completion_sha256"]:e.append(f"completion artifact mismatch: {stage}")
        if not manifest_path.is_file() or sha(manifest_path)!=artifact["manifest_sha256"]:e.append(f"manifest artifact mismatch: {stage}")
        if e:return e,None
        package=manifest_path.parent
        if manifest_path.name!="package-manifest.json" or completion!=package/"stage-completion.json":e.append(f"noncanonical public envelope path: {stage}")
        try:canonical.resolve().relative_to(package.resolve())
        except Exception:e.append(f"canonical artifact outside package: {stage}")
        manifest=read(manifest_path);actual=package_files(package)-{"package-manifest.json","stage-completion.json"}
        refs=manifest.get("files")
        if not isinstance(refs,list):return [f"manifest files missing: {stage}"],None
        declared=set();bound={};declared_roles=set()
        for r in refs:
            if not isinstance(r,dict) or set(r)!={"role","path","sha256"}:e.append(f"malformed manifest ref: {stage}");continue
            try:
                p=(package/r["path"]).resolve()
                if package.resolve()!=p and package.resolve() not in p.parents:raise ValueError("escape")
                rel=p.relative_to(package.resolve()).as_posix()
                if rel in declared:e.append(f"duplicate manifest path: {stage}:{rel}")
                if r["role"] in declared_roles:e.append(f"duplicate manifest role: {stage}:{r['role']}")
                declared.add(rel);declared_roles.add(r["role"])
                if not p.is_file() or sha(p)!=r["sha256"]:e.append(f"manifest member hash mismatch: {stage}:{rel}")
                bound[(rel,r["sha256"])]=r["role"]
            except Exception:e.append(f"manifest member invalid: {stage}")
        if declared!=actual:e.append(f"manifest closure mismatch: {stage}")
        roles=manifest.get("artifact_roles");expected_roles={r.get("role"):r for r in refs if isinstance(r,dict) and set(r)=={"role","path","sha256"}}
        if roles!=expected_roles:e.append(f"artifact roles invalid: {stage}")
        required=[canonical,resolve(ws,validation_ref)]
        for p,label in zip(required,("canonical","validation")):
            try:
                rel=p.resolve().relative_to(package.resolve()).as_posix()
                if (rel,sha(p)) not in bound:e.append(f"manifest does not bind {label}: {stage}")
            except Exception:e.append(f"{label} is outside manifest package: {stage}")
        comp=read(completion)
        if manifest.get("hld_run_id")!=comp.get("hld_run_id") or manifest.get("revision")!=comp.get("revision") or manifest.get("stage")!=stage or manifest.get("skill")!=comp.get("skill") or manifest.get("status")!="ready":e.append(f"manifest identity mismatch: {stage}")
        expected_manifest={"role":"package_manifest","path":manifest_path.relative_to(Path(ws).resolve()).as_posix(),"sha256":sha(manifest_path)}
        if comp.get("manifest_ref")!=expected_manifest:e.append(f"completion manifest binding mismatch: {stage}")
        return e,{"canonical":canonical,"completion":completion,"manifest":manifest_path,"manifest_object":manifest,"package":package}
    except Exception as ex:return [f"manifest verification failed {stage}: {ex}"],None

def resolve_author_locator(decision,target,index):
    locator=target.get("author_text_locator","")
    if "#" in locator:
        prefix,pointer=locator.split("#",1)
        if prefix not in {"","author-decision.json"}:raise ValueError("locator must address current author-decision")
    else:pointer=locator
    if not pointer.startswith("/"):raise ValueError("locator must be an RFC6901 pointer")
    parts=[]
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])",raw):raise ValueError("invalid RFC6901 escape")
        parts.append(raw.replace("~1","/").replace("~0","~"))
    cur=decision
    for part in parts:
        if isinstance(cur,dict) and part in cur:cur=cur[part]
        elif isinstance(cur,list) and part.isdigit() and int(part)<len(cur):cur=cur[int(part)]
        else:raise ValueError("locator does not resolve")
    allowed=["author_text"] if parts==["author_text"] else ["revision_targets",str(index),"requested_change"] if parts==["revision_targets",str(index),"requested_change"] else []
    if not allowed:raise ValueError("locator may address only author_text or this target requested_change")
    expected=decision["author_text"] if parts==["author_text"] else target["requested_change"]
    if not isinstance(cur,str) or not cur.strip() or cur!=expected:raise ValueError("locator value mismatch")
    return cur

def collect_ids(obj):
    out=set()
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in {"id","target_id","canonical_id","report_element_id","render_target_id","source_id"} and isinstance(v,str):out.add(v)
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(obj);return out

def validate_inputs(w,g,ws,input_gate_path=None):
    e=preflight(w,g);by={x.get("role"):x for x in w.get("file_allowlist",[]) if isinstance(x,dict)}
    for role,r in by.items():
        try:
            p=resolve(ws,r)
            if not p.is_file() or sha(p)!=r.get("sha256"):e.append(f"input hash mismatch: {role}")
        except Exception as ex:e.append(f"input {role}: {ex}")
    try:
        gp=Path(input_gate_path).resolve() if input_gate_path else resolve(ws,w.get("input_gate_ref",{}))
        if not gp.is_file() or sha(gp)!=w.get("input_gate_ref",{}).get("sha256") or read(gp)!=g:e.append("input_gate_ref does not bind supplied input gate")
    except Exception as ex:e.append(f"input gate binding failed: {ex}")
    if e:return e,{}
    run=read(resolve(ws,by["run_state"]));decision=read(resolve(ws,by["author_decision"]));e.extend(validate_schema(decision,"author-decision.schema.json"))
    if not same_ref(w.get("state_before_ref",{}),by["run_state"]) or not same_ref(g.get("state_before_ref",{}),by["run_state"]):e.append("state_before_ref must bind the same run-state bytes")
    if run.get("hld_run_id")!=w.get("hld_run_id") or run.get("revision")!=w.get("revision"):e.append("run-state identity mismatch")
    if run.get("status")!="waiting_author_decision" or run.get("current_stage") is not None:e.append("run-state is not at author decision gate")
    if run.get("revision_plan_ref") is not None or run.get("revision_plan_state_ref") is not None:e.append("active or unresolved revision state")
    if w.get("return_binding") is not None or g.get("return_binding") is not None:e.append("active return binding")
    ups=w.get("upstream_completions",[])
    if run.get("accepted_completions")!=ups:e.append("accepted completion chain mismatch")
    stage_chain=[];stage_packages={}
    for i,a in enumerate(ups):
        try:
            cp=resolve(ws,{"path":a["completion_path"]});mp=resolve(ws,{"path":a["manifest_path"]})
            validation_ref=by[f"validation_{CHAIN[i]}"]
            closed,pack=verify_manifest_closure(ws,a,CHAIN[i],validation_ref);e.extend(closed)
            if pack is None:continue
            c=read(cp)
            if c.get("stage")!=CHAIN[i] or c.get("status")!="ready" or c.get("hld_run_id")!=w.get("hld_run_id"):e.append(f"completion identity mismatch: {CHAIN[i]}")
            public_skill=PUBLIC_STAGE_SKILLS[CHAIN[i]]
            if c.get("schema_version")!="1.0" or c.get("harness")!="novel-hld-autonomous" or c.get("skill")!=public_skill:e.append(f"completion public identity mismatch: {CHAIN[i]}")
            owner=c.get("owner_implementation",{})
            if owner.get("skill")!=public_skill or not isinstance(owner.get("version"),str) or not re.match(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$",owner.get("version","")) or not re.match(r"^[0-9a-f]{64}$",owner.get("sha256","")):e.append(f"completion owner implementation mismatch: {CHAIN[i]}")
            expected_upstreams=[ups[CHAIN.index(s)] for s in UPSTREAM[CHAIN[i]]]
            if c.get("upstream_completions")!=expected_upstreams:e.append(f"completion upstream topology mismatch: {CHAIN[i]}")
            expected_next=CHAIN[i+1] if i+1<len(CHAIN) else "HF1"
            if c.get("next_allowed_stage")!=expected_next or not isinstance(c.get("ready_capabilities"),list) or not c.get("ready_capabilities"):e.append(f"completion readiness contract mismatch: {CHAIN[i]}")
            if c.get("return_binding") is not None:
                try:
                    return_path=resolve(ws,c["return_binding"])
                    if not return_path.is_file() or sha(return_path)!=c["return_binding"].get("sha256"):e.append(f"completion return binding mismatch: {CHAIN[i]}")
                except Exception:e.append(f"completion return binding invalid: {CHAIN[i]}")
            for role in ("input_gate_ref","state_before_ref","work_order_ref"):
                rr=c.get(role,{})
                try:
                    rp=resolve(ws,rr)
                    if not rp.is_file() or sha(rp)!=rr.get("sha256"):e.append(f"completion {role} mismatch: {CHAIN[i]}")
                except Exception:e.append(f"completion {role} invalid: {CHAIN[i]}")
            vr=c.get("validation_ref",{});vp=resolve(ws,vr)
            if not same_ref(vr,validation_ref) or not vp.is_file() or sha(vp)!=vr.get("sha256"):e.append(f"completion validation mismatch: {CHAIN[i]}")
            canonical_refs=c.get("canonical_artifacts",[])
            if not any(isinstance(x,dict) and x.get("path")==a.get("path") and x.get("sha256")==a.get("sha256") for x in canonical_refs):e.append(f"completion does not bind canonical: {CHAIN[i]}")
            stage_chain.append({"stage":CHAIN[i],"completion_path":a["completion_path"],"completion_sha256":a["completion_sha256"],"manifest_path":a["manifest_path"],"manifest_sha256":a["manifest_sha256"]})
            stage_packages[CHAIN[i]]=pack
        except Exception as ex:e.append(f"completion {CHAIN[i]}: {ex}")
    if decision.get("hld_run_id")!=w.get("hld_run_id") or decision.get("revision")!=w.get("revision") or not (run.get("event_sequence",-1)<decision.get("event_sequence",-1)<w.get("event_sequence",-1)):e.append("author decision is not current")
    expected={"hp1_package_sha256":by["hp1_package"]["sha256"],"hq2_acceptance_sha256":by["hq2_acceptance"]["sha256"],"hh1_manifest_sha256":by["hh1_manifest"]["sha256"],"html_sha256":by["hh1_html"]["sha256"]}
    if decision.get("bindings")!=expected:e.append("author decision binding mismatch")
    targets=decision.get("revision_targets",[]);kind=decision.get("decision")
    if kind=="revise" and not targets:e.append("revise requires targets")
    if kind in {"approved","rejected"} and targets:e.append("approved/rejected forbid targets")
    acceptance=read(resolve(ws,by["hq2_acceptance"]));
    if (acceptance.get("schema_version"),acceptance.get("harness"),acceptance.get("stage"),acceptance.get("status"),acceptance.get("hld_run_id"))!=("1.0","novel-hld-autonomous","HQ2","ready",w.get("hld_run_id")):e.append("HQ2 acceptance is not ready")
    if len(ups)==len(CHAIN):
        hp1_completion=ups[CHAIN.index("HP1")];hb0_completion=ups[CHAIN.index("HB0")]
        if not same_ref(acceptance.get("hp1_completion_ref",{}),{"path":hp1_completion["completion_path"],"sha256":hp1_completion["completion_sha256"]}):e.append("HQ2 HP1 completion binding mismatch")
        if not same_ref(acceptance.get("hb0_completion_ref",{}),{"path":hb0_completion["completion_path"],"sha256":hb0_completion["completion_sha256"]}):e.append("HQ2 HB0 completion binding mismatch")
    if len(stage_packages)==len(CHAIN):
        hp1a=ups[CHAIN.index("HP1")];hq2a=ups[CHAIN.index("HQ2")];hh1a=ups[CHAIN.index("HH1")]
        if by["hp1_manifest"]["path"]!=hp1a["manifest_path"] or by["hp1_manifest"]["sha256"]!=hp1a["manifest_sha256"]:e.append("HP1 manifest is not current upstream manifest")
        if by["hh1_manifest"]["path"]!=hh1a["manifest_path"] or by["hh1_manifest"]["sha256"]!=hh1a["manifest_sha256"]:e.append("HH1 manifest is not current upstream manifest")
        for stage,required in (("HP1",[by["hp1_package"],by["lld_handoff"],by["hld_cross_index"]]),("HH1",[by["hh1_html"],by["render_target_registry"]]),("HQ2",[by["hq2_acceptance"]])):
            pack=stage_packages[stage];members={(x.get("path"),x.get("sha256")) for x in pack["manifest_object"].get("files",[]) if isinstance(x,dict)}
            for rr in required:
                try:rel=resolve(ws,rr).relative_to(pack["package"].resolve()).as_posix()
                except Exception:rel=None
                if (rel,rr["sha256"]) not in members:e.append(f"{stage} manifest does not bind required artifact: {rr['role']}")
        if hq2a.get("path")!=by["hq2_acceptance"]["path"] or hq2a.get("sha256")!=by["hq2_acceptance"]["sha256"]:e.append("HQ2 canonical artifact is not acceptance")
        if hp1a.get("path")!=by["hp1_package"]["path"] or hp1a.get("sha256")!=by["hp1_package"]["sha256"]:e.append("HP1 canonical artifact is not package")
    if kind=="revise":
        cross=collect_ids(read(resolve(ws,by["hld_cross_index"])));registry=collect_ids(read(resolve(ws,by["render_target_registry"])))
        if decision.get("schema_version")!="1.1":e.append("new author revisions require schema_version 1.1 with explicit semantic scope")
        for index,t in enumerate(targets):
            tk=t.get("target_kind");tid=t.get("target_id","");scope=t.get("change_scope");semantic=t.get("semantic_target_ids",[])
            if scope=="hld_semantic":
                if tk!="hld_content" or not semantic:e.append(f"semantic target must use hld_content and semantic_target_ids: {tid}")
                for semantic_id in semantic:
                    if semantic_id not in cross:e.append(f"unresolved semantic hld target: {semantic_id}")
            elif scope=="presentation_only":
                if semantic:e.append(f"presentation target cannot carry semantic_target_ids: {tid}")
                if tk not in {"report_content","render_expression"}:e.append(f"presentation target has semantic target_kind: {tid}")
            elif scope=="conception_authority":
                if tk!="conception_authority" or tid not in cross:e.append(f"invalid conception authority target: {tid}")
            else:e.append(f"missing or invalid change_scope: {tid}")
            if tk=="hld_content" and scope!="hld_semantic" and tid not in cross:e.append(f"unresolved hld_content target: {tid}")
            elif tk=="report_content" and (not re.match(r"^H(RE|VG)-",tid) or tid not in registry):e.append(f"unresolved report_content target: {tid}")
            elif tk=="render_expression" and (not tid.startswith("HUI-") or tid not in registry):e.append(f"unresolved render_expression target: {tid}")
            elif tk=="conception_authority" and tid not in cross:e.append(f"unresolved conception_authority target: {tid}")
            try:resolve_author_locator(decision,t,index)
            except Exception as ex:e.append(f"invalid author_text_locator for {tid}: {ex}")
    return e,{"by":by,"run":run,"decision":decision,"stage_chain":stage_chain,"upstream":ups,"stage_packages":stage_packages}

def base_result(w):
    return {"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":w["hld_run_id"],"revision":w["revision"],"stage":"HF1","skill":SKILL,"work_order_id":w["work_order_id"],"task_id":w["task_id"],"event_sequence":w["event_sequence"],"result_scope":"top_level","state_before_ref":w["state_before_ref"],"input_gate_ref":w["input_gate_ref"],"produced_at":w["result_timestamp"],"completion_ref":None,"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None}

def write_manifest(package,filename,status,w,roles):
    refs=[];arts={}
    for role,p in roles.items():
        r={"role":role,"path":Path(p).relative_to(package).as_posix(),"sha256":sha(p)};refs.append(r);arts[role]=r
    obj={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":w["hld_run_id"],"revision":w["revision"],"stage":"HF1","skill":SKILL,"status":status,"files":refs,"artifact_roles":arts};write(package/filename,obj);return obj

def emit_blocked(w,ws,errors,author_rejected=False):
    package=Path(ws)/w["output_directory"];package.mkdir(parents=True,exist_ok=False)
    write(package/"gate-data.json",{"schema_version":"1.0","stage":"HF1","decision":"rejected" if author_rejected else "invalid","errors":errors})
    write(package/"blocked-report.json",{"schema_version":"1.0","stage":"HF1","reason":"author_rejected" if author_rejected else "input_invalid","errors":errors})
    write(package/"validation.json",{"status":"pass","projection":"blocked"})
    write_manifest(package,"result-manifest.json","blocked",w,{"gate_data":package/"gate-data.json","blocked_report":package/"blocked-report.json","validation":package/"validation.json"})
    r=base_result(w);r.update({"result":"blocked","result_manifest_ref":ref("result_manifest",package/"result-manifest.json",ws),"validation_ref":ref("validation",package/"validation.json",ws),"gate_data_ref":ref("gate_data",package/"gate-data.json",ws),"blocked_report_ref":ref("blocked_report",package/"blocked-report.json",ws),"blocker_class":"author_rejected" if author_rejected else "input_invalid"});write(Path(ws)/"stage-result.json",r)

def execute(w,g,ws,input_gate_path=None):
    errors,ctx=validate_inputs(w,g,ws,input_gate_path)
    if errors:emit_blocked(w,ws,errors);return
    package=Path(ws)/w["output_directory"];decision=ctx["decision"]
    if decision["decision"]=="rejected":emit_blocked(w,ws,[],True);return
    package.mkdir(parents=True,exist_ok=False);by=ctx["by"]
    if decision["decision"]=="revise":
        shutil.copyfile(resolve(ws,by["author_decision"]),package/"author-decision.json")
        write(package/"revision-report.json",{"schema_version":"1.0","hld_run_id":w["hld_run_id"],"revision":w["revision"],"author_event_sha256":by["author_decision"]["sha256"],"revision_targets":decision["revision_targets"]})
        write(package/"finalizer-execution.json",{"schema_version":"1.0","decision":"revise","executed_at":w["result_timestamp"],"projection":"lossless_external_author_request"});write(package/"validation.json",{"status":"pass","targets_resolved":True,"lossless_projection":True})
        write_manifest(package,"result-manifest.json","revise",w,{"author_event":package/"author-decision.json","revision_report":package/"revision-report.json","execution_record":package/"finalizer-execution.json","validation":package/"validation.json"})
        affected=[]
        for target in decision["revision_targets"]:
            affected.extend(target.get("semantic_target_ids",[]) if target.get("change_scope")=="hld_semantic" else [target["target_id"]])
        r=base_result(w);r.update({"result":"revise","result_manifest_ref":ref("result_manifest",package/"result-manifest.json",ws),"validation_ref":ref("validation",package/"validation.json",ws),"revision_class":"external_author_request","revision_report_ref":ref("revision_report",package/"revision-report.json",ws),"author_event_ref":ref("author_event",package/"author-decision.json",ws),"affected_ids":list(dict.fromkeys(affected))});write(Path(ws)/"stage-result.json",r);return
    checks={"all_input_hashes_valid":True,"complete_current_chain":True,"no_active_return":True,"no_unresolved_revision_plan":True,"external_current_unconsumed_decision":True,"all_decision_bindings_match":True,"hq2_pass":True,"handoff_revalidated":True,"approved_only_completion":True}
    validation={"schema_version":"1.0","skill":SKILL,"stage":"HF1","hld_run_id":w["hld_run_id"],"revision":w["revision"],"checks":checks,"status":"pass"};write(package/"final-validation.json",validation)
    chain=ctx["stage_chain"];stage_hash={x["stage"]:x["completion_sha256"] for x in chain}
    completion={"schema_version":"1.0","harness":"novel-hld-autonomous","stage":"HF1","skill":SKILL,"hld_run_id":w["hld_run_id"],"revision":w["revision"],"status":"approved_ready","produced_at":w["result_timestamp"],"stage_chain":chain,"author_decision_ref":by["author_decision"],"hp1_package_ref":by["hp1_package"],"hq2_acceptance_ref":by["hq2_acceptance"],"hh1_manifest_ref":by["hh1_manifest"],"html_ref":by["hh1_html"],"lld_handoff_ref":by["lld_handoff"],"final_validation_ref":ref("final_validation",package/"final-validation.json",ws),"lld_admission":{"authorized":True,"handoff_ref":by["lld_handoff"],"hp1_completion_sha256":stage_hash["HP1"],"hq2_completion_sha256":stage_hash["HQ2"],"hh1_completion_sha256":stage_hash["HH1"]},"next_stage":"novel-lld"};write(package/"hld-completion.json",completion)
    write(package/"finalizer-execution.json",{"schema_version":"1.0","decision":"approved","executed_at":w["result_timestamp"],"completion_sha256":sha(package/"hld-completion.json")})
    write_manifest(package,"package-manifest.json","ready",w,{"hld_completion":package/"hld-completion.json","final_validation":package/"final-validation.json","execution_record":package/"finalizer-execution.json"})
    r=base_result(w);r.update({"result":"ready","result_manifest_ref":ref("package_manifest",package/"package-manifest.json",ws),"validation_ref":ref("final_validation",package/"final-validation.json",ws),"completion_ref":ref("hld_completion",package/"hld-completion.json",ws)});write(Path(ws)/"stage-result.json",r)

def validate_output(w,g,ws,input_gate_path=None):
    input_errors,ctx=validate_inputs(w,g,ws,input_gate_path);package=Path(ws)/w["output_directory"];rp=Path(ws)/"stage-result.json";e=[]
    if not package.is_dir() or not rp.is_file():return ["missing package or external result"]
    actual=package_files(package);r=read(rp)
    if any(x in actual for x in FORBIDDEN_NAMES):e.append("forbidden state/plan/completion artifact")
    if r.get("result_scope")!="top_level" or r.get("stage")!="HF1" or r.get("skill")!=SKILL:e.append("result identity mismatch")
    if r.get("event_sequence")!=w.get("event_sequence") or r.get("produced_at")!=w.get("result_timestamp"):e.append("result event mismatch")
    if input_errors:
        if actual!=BLOCKED or r.get("result")!="blocked" or r.get("blocker_class")!="input_invalid":e.append("invalid input must fail closed")
        return e
    decision=ctx["decision"]["decision"]
    if decision=="approved":
        if actual!=APPROVED or r.get("result")!="ready" or r.get("completion_ref") is None:e.append("approved profile/result mismatch")
        else:e.extend(validate_schema(read(package/"hld-completion.json"),"hld-completion.schema.json"));e.extend(validate_schema(read(package/"final-validation.json"),"final-validation.schema.json"))
    elif decision=="revise":
        if actual!=REVISE or r.get("result")!="revise" or r.get("revision_class")!="external_author_request" or r.get("completion_ref") is not None:e.append("revise profile/result mismatch")
        elif read(package/"revision-report.json").get("revision_targets")!=ctx["decision"]["revision_targets"]:e.append("revision target projection drift")
        elif (package/"author-decision.json").read_bytes()!=resolve(ws,ctx["by"]["author_decision"]).read_bytes():e.append("author event byte-copy drift")
    else:
        if actual!=BLOCKED or r.get("result")!="blocked" or r.get("blocker_class")!="author_rejected" or r.get("completion_ref") is not None:e.append("rejected profile/result mismatch")
    manifest_name="package-manifest.json" if decision=="approved" else "result-manifest.json";m=read(package/manifest_name);declared={x.get("path") for x in m.get("files",[]) if isinstance(x,dict)}
    if declared!=actual-{manifest_name}:e.append("manifest closure mismatch")
    for x in m.get("files",[]):
        p=package/str(x.get("path",""))
        if not p.is_file() or sha(p)!=x.get("sha256"):e.append(f"manifest hash mismatch: {x.get('path')}")
    return e

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["preflight","execute","validate"]);p.add_argument("--work-order",required=True,type=Path);p.add_argument("--input-gate",required=True,type=Path);p.add_argument("--workspace",type=Path);p.add_argument("--json",action="store_true");a=p.parse_args(argv)
    try:
        w,g=read(a.work_order),read(a.input_gate)
        if a.mode=="execute":execute(w,g,a.workspace or Path("."),a.input_gate);err=[]
        elif a.mode=="validate":err=validate_output(w,g,a.workspace or Path("."),a.input_gate)
        else:err=preflight(w,g)
        status="pass" if not err else "fail"
    except Exception as ex:status="runtime_error";err=[str(ex)]
    print(json.dumps({"stage":STAGE,"skill":SKILL,"status":status,"errors":err},ensure_ascii=False,sort_keys=True));return 0 if status=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
