import ast,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1];HARNESS=REPO/"harnesses/novel-hld-autonomous"
sys.path.insert(0,str(HARNESS))
from runtime.contracts import SKILLS,UPSTREAM
from runtime.package_envelope import validate_completion_bindings,validate_manifest,validate_ready_profile,validate_result_envelope
from runtime.schema_catalog import SchemaCatalog
CATALOG=SchemaCatalog(HARNESS/"schemas")
SPEC=importlib.util.spec_from_file_location("v",ROOT/"scripts/validate_package.py")
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V)

CANONICAL={"HB0":"hld-control-baseline.json","HA1":"narrative-architecture.json","HS1":"storyline-choreography.json","HC1":"character-arc-placement.json","HI1":"narrative-information-architecture.json","HR1":"rhythm-continuity-architecture.json","HK1":"key-scene-function-map.json","HD1":"chapter-definition-architecture.json","HQ1":"hld-semantic-review.json","HP1":"novel-hld-package.json","HQ2":"lld-handoff-acceptance.json","HH1":"hld-human-review-report.html"}
CONTENT={
    "HB0":["hld-control-baseline.json","hld-source-index.json","hb0-execution.json","validation.json"],
    "HA1":["narrative-architecture.json","generation-session.json","execution-record.json","narrative-architecture.md","validation.json","generation-evidence/evidence.json"],
    "HS1":["storyline-choreography.json","generation-session.json","execution-record.json","storyline-choreography.md","validation.json","generation-evidence/evidence.json"],
    "HC1":["character-arc-placement.json","generation-session.json","execution-record.json","character-arc-placement.md","validation.json","generation-evidence/evidence.json"],
    "HI1":["narrative-information-architecture.json","generation-session.json","execution-record.json","narrative-information-architecture.md","validation.json","generation-evidence/evidence.json"],
    "HR1":["rhythm-continuity-architecture.json","generation-session.json","execution-record.json","rhythm-continuity-architecture.md","validation.json","generation-evidence/evidence.json"],
    "HK1":["key-scene-function-map.json","generation-session.json","execution-record.json","key-scene-function-map.md","validation.json","generation-evidence/evidence.json"],
    "HD1":["chapter-definition-architecture.json","generation-session.json","execution-record.json","chapter-definition-architecture.md","validation.json","generation-evidence/evidence.json"],
    "HQ1":["hld-semantic-review.json","review-session.json","review-execution.json","validation.json"],
    "HP1":["novel-hld-package.json","novel-hld-spec.md","hld-cross-index.json","hld-traceability-matrix.json","hld-traceability-matrix.md","lld-handoff.json","assembly-execution.json","validation.json",
           "canonical-models/narrative-architecture.json","canonical-models/storyline-choreography.json","canonical-models/character-arc-placement.json","canonical-models/narrative-information-architecture.json","canonical-models/rhythm-continuity-architecture.json","canonical-models/key-scene-function-map.json","canonical-models/chapter-definition-architecture.json","canonical-models/hld-semantic-review.json"],
    "HQ2":["lld-handoff-acceptance.json","publisher-execution.json","validation.json"],
    "HH1":["hld-human-review-report.html","render-target-registry.json","publisher-execution.json","validation.json"],
}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix in {".md",".html"}:path.write_text(str(value),encoding="utf-8",newline="\n")
    else:path.write_text(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8",newline="\n")
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def wsref(role,path,ws):return {"role":role,"path":path.relative_to(ws).as_posix(),"sha256":digest(path)}
def pkgref(role,path,pkg):return {"role":role,"path":path.relative_to(pkg).as_posix(),"sha256":digest(path)}
def artifact(canonical,manifest,completion,ws):return {"path":canonical.relative_to(ws).as_posix(),"sha256":digest(canonical),"manifest_path":manifest.relative_to(ws).as_posix(),"manifest_sha256":digest(manifest),"completion_path":completion.relative_to(ws).as_posix(),"completion_sha256":digest(completion)}

class FinalizerTest(unittest.TestCase):
    def build(self,decision="approved",locator="author-decision.json#/author_text"):
        root=Path(tempfile.mkdtemp());ws=root/"ws";inputs=ws/"inputs";inputs.mkdir(parents=True)
        packages={};artifacts={};validations={}
        def make_stage(stage,values=None):
            values=values or {};pkg=inputs/stage/"package";ctx=inputs/stage/"context";pkg.mkdir(parents=True);ctx.mkdir()
            for name in CONTENT[stage]:
                default=f"# {stage}\n" if Path(name).suffix in {".md",".html"} else {"schema_version":"1.0","stage":stage,"id":stage+"-DATA"}
                write(pkg/name,values.get(name,default))
            canonical=pkg/CANONICAL[stage];validation=pkg/"validation.json";validations[stage]=validation
            upstreams=[artifacts[s] for s in UPSTREAM[stage]]
            run=ctx/"run-state.json";write(run,{"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"event_sequence":2*V.CHAIN.index(stage),"status":"running","current_stage":stage,"accepted_completions":upstreams,"current_result_ref":None,"previous_state_ref":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"waiting_transaction_ref":None})
            state_ref=wsref("run_state",run,ws);gate=ctx/"input-gate.json"
            gate_value={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","stage":stage,"mode":"forward","state_before_ref":state_ref,"hb0_completion_ref":None if stage=="HB0" else artifacts["HB0"],"upstream_completions":upstreams,"baseline_manifest_ref":None,"baseline_validation_ref":None,"source_lineage_refs":[],"exact_owner_skill":SKILLS[stage],"owner_version":"1.0.0","implementation_sha256":"f"*64,"return_binding":None,"unresolved_projection":[],"revision_plan_ref":None,"revision_plan_state_ref":None,"file_allowlist":[state_ref]};write(gate,gate_value)
            work=ctx/"work-order.json";work_value={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"work_order_id":"WO-"+stage,"task_id":"TASK-"+stage,"stage":stage,"action":"execute","exact_owner_skill":SKILLS[stage],"owner_version":"1.0.0","implementation_sha256":"f"*64,"event_sequence":2*V.CHAIN.index(stage)+1,"result_timestamp":"2026-08-06T00:00:00Z","input_gate_ref":wsref("input_gate",gate,ws),"state_before_ref":state_ref,"upstream_completions":upstreams,"file_allowlist":[state_ref],"unresolved_projection":[],"mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"output_directory":f"inputs/{stage}/package","submission_status":"open"};write(work,work_value)
            refs=[]
            for path in sorted((p for p in pkg.rglob("*") if p.is_file()),key=lambda p:p.as_posix()):
                role=path.relative_to(pkg).as_posix().replace("/","_").replace(".","_");refs.append(pkgref(role,path,pkg))
            public_skill=V.PUBLIC_STAGE_SKILLS[stage]
            manifest=pkg/"package-manifest.json";manifest_value={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"stage":stage,"skill":public_skill,"status":"ready","files":refs,"artifact_roles":{x["role"]:x for x in refs}};write(manifest,manifest_value)
            completion=pkg/"stage-completion.json";next_stage=V.CHAIN[V.CHAIN.index(stage)+1] if stage!="HH1" else "HF1"
            completion_value={"schema_version":"1.0","harness":"novel-hld-autonomous","stage":stage,"skill":public_skill,"hld_run_id":"RUN","revision":0,"status":"ready","input_gate_ref":wsref("input_gate",gate,ws),"state_before_ref":state_ref,"work_order_ref":wsref("work_order",work,ws),"manifest_ref":wsref("package_manifest",manifest,ws),"validation_ref":wsref("validation",validation,ws),"upstream_completions":upstreams,"canonical_artifacts":[wsref(f"canonical_{stage}",canonical,ws)],"owner_implementation":{"skill":public_skill,"version":"1.0.0","sha256":"f"*64},"return_binding":None,"ready_capabilities":[stage.lower()+"-ready"],"next_allowed_stage":next_stage};write(completion,completion_value)
            art=artifact(canonical,manifest,completion,ws);artifacts[stage]=art
            result=ctx/"stage-result.json";result_value={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"stage":stage,"skill":SKILLS[stage],"work_order_id":"WO-"+stage,"task_id":"TASK-"+stage,"event_sequence":work_value["event_sequence"],"result_scope":"top_level","result":"ready","state_before_ref":state_ref,"input_gate_ref":wsref("input_gate",gate,ws),"result_manifest_ref":wsref("package_manifest",manifest,ws),"validation_ref":wsref(f"validation_{stage}",validation,ws),"produced_at":"2026-08-06T00:00:00Z","completion_ref":wsref("stage_completion",completion,ws),"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None};write(result,result_value)
            for value,schema in ((run and read(run),"run-state.schema.json"),(gate_value,"input-gate.schema.json"),(work_value,"work-order.schema.json"),(manifest_value,"package-manifest.schema.json"),(completion_value,"stage-completion.schema.json"),(result_value,"stage-result.schema.json")):CATALOG.validate(value,schema)
            validate_manifest(pkg,manifest_value);validate_completion_bindings(ws,pkg,completion_value);validate_result_envelope(result_value,work_value)
            if stage not in {"HQ2","HH1"}:validate_ready_profile(pkg,stage)
            packages[stage]={"pkg":pkg,"context":ctx,"canonical":canonical,"manifest":manifest,"completion":completion,"validation":validation};return art
        for stage in V.CHAIN:
            values={}
            if stage=="HP1":values={"novel-hld-package.json":{"id":"HST-1"},"lld-handoff.json":{"ready":True},"hld-cross-index.json":{"ids":[{"id":"HST-1"},{"id":"HRE-1"}]}}
            elif stage=="HQ2":values={"lld-handoff-acceptance.json":{"schema_version":"1.0","harness":"novel-hld-autonomous","stage":"HQ2","hld_run_id":"RUN","revision":0,"status":"ready","consumer_test_ref":wsref("consumer_test",packages["HP1"]["canonical"],ws),"consumer_manifest_ref":wsref("consumer_manifest",packages["HP1"]["manifest"],ws),"consumer_result_ref":wsref("consumer_result",packages["HP1"]["completion"],ws),"fidelity_test_ref":wsref("fidelity_test",packages["HP1"]["canonical"],ws),"fidelity_manifest_ref":wsref("fidelity_manifest",packages["HP1"]["manifest"],ws),"fidelity_result_ref":wsref("fidelity_result",packages["HP1"]["completion"],ws),"hp1_completion_ref":wsref("hp1_completion",packages["HP1"]["completion"],ws),"hb0_completion_ref":wsref("hb0_completion",packages["HB0"]["completion"],ws)}}
            elif stage=="HH1":values={"hld-human-review-report.html":"<html>review</html>","render-target-registry.json":{"targets":[{"id":"HRE-1"},{"id":"HUI-1"}]}}
            make_stage(stage,values)
        ups=[artifacts[s] for s in V.CHAIN]
        run=inputs/"run-state.json";write(run,{"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"event_sequence":20,"status":"waiting_author_decision","current_stage":None,"accepted_completions":ups,"current_result_ref":None,"previous_state_ref":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"waiting_transaction_ref":None})
        hp1=packages["HP1"]["canonical"];handoff=packages["HP1"]["pkg"]/"lld-handoff.json";cross=packages["HP1"]["pkg"]/"hld-cross-index.json";hq2=packages["HQ2"]["canonical"];html=packages["HH1"]["canonical"];registry=packages["HH1"]["pkg"]/"render-target-registry.json"
        targets=[] if decision!="revise" else [{"target_kind":"report_content","target_id":"HRE-1","requested_change":"Clarify presentation.","author_text_locator":locator,"change_scope":"presentation_only","target_field_paths":["/title_and_decision_scope/0/conclusion"]}]
        author=inputs/"author-decision.json";write(author,{"schema_version":"1.1" if decision=="revise" else "1.0","hld_run_id":"RUN","revision":0,"event_sequence":21,"event_id":"ADE-1","external":True,"current":True,"consumed":False,"decision":decision,"author_text":"Final author decision.","bindings":{"hp1_package_sha256":artifacts["HP1"]["sha256"],"hq2_acceptance_sha256":artifacts["HQ2"]["sha256"],"hh1_manifest_sha256":artifacts["HH1"]["manifest_sha256"],"html_sha256":artifacts["HH1"]["sha256"]},"revision_targets":targets})
        roles={"run_state":run,"author_decision":author,"hp1_package":hp1,"hp1_manifest":packages["HP1"]["manifest"],"lld_handoff":handoff,"hld_cross_index":cross,"hq2_acceptance":hq2,"hh1_manifest":packages["HH1"]["manifest"],"hh1_html":html,"render_target_registry":registry};roles.update({f"validation_{s}":validations[s] for s in V.CHAIN});allow=[wsref(k,p,ws) for k,p in roles.items()]
        state_ref=next(x for x in allow if x["role"]=="run_state");gate=inputs/"input-gate.json";common={"schema_version":"1.0","harness":"novel-hld-autonomous","stage":"HF1","exact_owner_skill":V.SKILL,"owner_version":"1.0.0","implementation_sha256":"f"*64,"hld_run_id":"RUN","mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"state_before_ref":state_ref,"file_allowlist":allow,"unresolved_projection":[],"upstream_completions":ups}
        g={**common,"hb0_completion_ref":ups[0],"baseline_manifest_ref":None,"baseline_validation_ref":None,"source_lineage_refs":[]};write(gate,g)
        w={**common,"action":"execute","revision":0,"event_sequence":22,"result_timestamp":"2026-08-06T00:00:00Z","work_order_id":"WO-HF1","task_id":"TASK-HF1","input_gate_ref":wsref("input_gate",gate,ws),"output_directory":"package","submission_status":"open"}
        CATALOG.validate(read(run),"run-state.schema.json");CATALOG.validate(g,"input-gate.schema.json");CATALOG.validate(w,"work-order.schema.json")
        return root,ws,w,g,packages,artifacts

    def execute_and_validate(self,decision="approved",locator="author-decision.json#/author_text"):
        root,ws,w,g,packs,arts=self.build(decision,locator);self.addCleanup(shutil.rmtree,root);V.execute(w,g,ws);errors=V.validate_output(w,g,ws);self.assert_public_result(ws,w);return ws,w,g,packs,arts,errors
    def assert_public_result(self,ws,w):
        result=read(ws/"stage-result.json");package=ws/"package";manifest_name="package-manifest.json" if result["result"]=="ready" else "result-manifest.json"
        CATALOG.validate(result,"stage-result.schema.json");validate_result_envelope(result,w);manifest=read(package/manifest_name);CATALOG.validate(manifest,"package-manifest.schema.json");validate_manifest(package,manifest)
        if result["result"]=="ready":self.assertEqual([],V.validate_schema(read(package/"hld-completion.json"),"hld-completion.schema.json"))

    def refresh_hf1(self,ws,w,g):
        run=ws/"inputs/run-state.json";rv=read(run);rv["accepted_completions"]=w["upstream_completions"];write(run,rv);state_ref=wsref("run_state",run,ws);w["state_before_ref"]=state_ref;g["state_before_ref"]=state_ref;g["upstream_completions"]=w["upstream_completions"];g["hb0_completion_ref"]=w["upstream_completions"][0]
        for arr in (w["file_allowlist"],g["file_allowlist"]):
            next(x for x in arr if x["role"]=="run_state").update(state_ref)
        gate=ws/"inputs/input-gate.json";write(gate,g);w["input_gate_ref"]=wsref("input_gate",gate,ws)
    def reseal_chain(self,ws,w,g,packs,arts,refresh_hq2=True):
        for stage in V.CHAIN:
            p=packs[stage];manifest=read(p["manifest"])
            if stage=="HQ2" and refresh_hq2:
                acceptance=read(p["canonical"]);acceptance["hp1_completion_ref"]=wsref("hp1_completion",packs["HP1"]["completion"],ws);acceptance["hb0_completion_ref"]=wsref("hb0_completion",packs["HB0"]["completion"],ws);write(p["canonical"],acceptance)
            for rr in manifest["files"]:
                target=p["pkg"]/rr["path"];rr["sha256"]=digest(target);manifest["artifact_roles"][rr["role"]]=rr
            write(p["manifest"],manifest);completion=read(p["completion"]);completion["manifest_ref"]=wsref("package_manifest",p["manifest"],ws);completion["validation_ref"]=wsref("validation",p["validation"],ws);completion["canonical_artifacts"]=[wsref(f"canonical_{stage}",p["canonical"],ws)];completion["upstream_completions"]=[arts[s] for s in UPSTREAM[stage]];write(p["completion"],completion);arts[stage].update(artifact(p["canonical"],p["manifest"],p["completion"],ws))
        w["upstream_completions"]=[arts[s] for s in V.CHAIN]
        core={"hp1_package":packs["HP1"]["canonical"],"hp1_manifest":packs["HP1"]["manifest"],"hq2_acceptance":packs["HQ2"]["canonical"],"hh1_manifest":packs["HH1"]["manifest"],"hh1_html":packs["HH1"]["canonical"]}
        author=ws/"inputs/author-decision.json";av=read(author);av["bindings"]={"hp1_package_sha256":digest(core["hp1_package"]),"hq2_acceptance_sha256":digest(core["hq2_acceptance"]),"hh1_manifest_sha256":digest(core["hh1_manifest"]),"html_sha256":digest(core["hh1_html"])};write(author,av);core["author_decision"]=author
        for arr in (w["file_allowlist"],g["file_allowlist"]):
            by={x["role"]:x for x in arr}
            for role,path in core.items():by[role].update(wsref(role,path,ws))
        self.refresh_hf1(ws,w,g)

    def test_approved_and_deterministic_public_contract(self):
        ws1,w1,g1,_,_,e1=self.execute_and_validate();ws2,w2,g2,_,_,e2=self.execute_and_validate();self.assertEqual([],e1);self.assertEqual([],e2);self.assertEqual((ws1/"package/hld-completion.json").read_bytes(),(ws2/"package/hld-completion.json").read_bytes())
    def test_historical_revisions_and_return_bindings_remain_current_by_exact_chain(self):
        root,ws,w,g,packs,arts=self.build();self.addCleanup(shutil.rmtree,root)
        for index,stage in enumerate(V.CHAIN):
            package=packs[stage];manifest=read(package["manifest"]);completion=read(package["completion"]);manifest["revision"]=index;completion["revision"]=index
            if stage in {"HA1","HS1","HI1","HK1","HD1","HQ1","HP1","HH1"}:
                binding=ws/f"return-bindings/{stage}.json";write(binding,{"stage":stage,"accepted":True});completion["return_binding"]=wsref("return_binding",binding,ws)
            write(package["manifest"],manifest);write(package["completion"],completion)
        self.reseal_chain(ws,w,g,packs,arts);V.execute(w,g,ws);self.assertEqual([],V.validate_output(w,g,ws));self.assertTrue((ws/"package/hld-completion.json").is_file())
    def test_canonical_tamper_fails_closed(self):
        root,ws,w,g,_,_=self.build();self.addCleanup(shutil.rmtree,root);(ws/"inputs/HP1/package/novel-hld-package.json").write_text("tampered",encoding="utf-8");V.execute(w,g,ws);self.assertFalse((ws/"package/hld-completion.json").exists())
    def test_fake_manifest_fails_closed_even_when_resealed(self):
        root,ws,w,g,packs,arts=self.build();self.addCleanup(shutil.rmtree,root);write(packs["HA1"]["manifest"],{"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":"RUN","revision":0,"stage":"HA1","skill":SKILLS["HA1"],"status":"ready","files":[],"artifact_roles":{}});self.reseal_chain(ws,w,g,packs,arts);V.execute(w,g,ws);self.assertFalse((ws/"package/hld-completion.json").exists())
    def test_manifest_omitting_validation_fails_closed(self):
        root,ws,w,g,packs,arts=self.build();self.addCleanup(shutil.rmtree,root);m=read(packs["HA1"]["manifest"]);m["files"]=[x for x in m["files"] if x["path"]!="validation.json"];m["artifact_roles"]={x["role"]:x for x in m["files"]};write(packs["HA1"]["manifest"],m);self.reseal_chain(ws,w,g,packs,arts);V.execute(w,g,ws);self.assertFalse((ws/"package/hld-completion.json").exists())
    def test_missing_hq2_binding_fails_closed_after_full_reseal(self):
        root,ws,w,g,packs,arts=self.build();self.addCleanup(shutil.rmtree,root);value=read(packs["HQ2"]["canonical"]);value["hp1_completion_ref"]["sha256"]="0"*64;write(packs["HQ2"]["canonical"],value);self.reseal_chain(ws,w,g,packs,arts,refresh_hq2=False);V.execute(w,g,ws);self.assertIn("HQ2 HP1 completion binding mismatch",read(ws/"package/blocked-report.json")["errors"])
    def test_invalid_author_locator_fails_closed(self):
        root,ws,w,g,_,_=self.build("revise","author-decision.json#/revision_targets/9/requested_change");self.addCleanup(shutil.rmtree,root);V.execute(w,g,ws);self.assertEqual("input_invalid",read(ws/"stage-result.json")["blocker_class"])
    def test_revise_projection(self):
        ws,w,g,_,_,errors=self.execute_and_validate("revise");self.assertEqual([],errors);self.assertFalse((ws/"package/hld-completion.json").exists())
    def test_semantic_author_revision_projects_canonical_owner_ids(self):
        root,ws,w,g,_,_=self.build("revise");self.addCleanup(shutil.rmtree,root)
        author=ws/"inputs/author-decision.json";value=read(author);value["revision_targets"]=[{"target_kind":"hld_content","target_id":"HRE-1","requested_change":"Add the author-approved city network to canonical HLD authority.","author_text_locator":"author-decision.json#/author_text","change_scope":"hld_semantic","semantic_target_ids":["HST-1"],"target_field_paths":["/world_setting_architecture"]}];write(author,value)
        for collection in (w["file_allowlist"],g["file_allowlist"]):next(item for item in collection if item["role"]=="author_decision").update(wsref("author_decision",author,ws))
        gate=ws/"inputs/input-gate.json";write(gate,g);w["input_gate_ref"]=wsref("input_gate",gate,ws)
        V.execute(w,g,ws);self.assertEqual(read(ws/"stage-result.json")["affected_ids"],["HST-1"])
    def test_legacy_unscoped_revise_is_rejected(self):
        root,ws,w,g,_,_=self.build("revise");self.addCleanup(shutil.rmtree,root)
        author=ws/"inputs/author-decision.json";value=read(author);value["schema_version"]="1.0";target=value["revision_targets"][0];target.pop("change_scope");target.pop("target_field_paths");write(author,value)
        for collection in (w["file_allowlist"],g["file_allowlist"]):next(item for item in collection if item["role"]=="author_decision").update(wsref("author_decision",author,ws))
        gate=ws/"inputs/input-gate.json";write(gate,g);w["input_gate_ref"]=wsref("input_gate",gate,ws)
        V.execute(w,g,ws);self.assertEqual(read(ws/"stage-result.json")["blocker_class"],"input_invalid")
    def test_rejected_no_completion(self):
        ws,w,g,_,_,errors=self.execute_and_validate("rejected");self.assertEqual([],errors);self.assertEqual("author_rejected",read(ws/"stage-result.json")["blocker_class"])
    def test_public_work_gate_regression(self):
        root,ws,w,g,_,_=self.build();self.addCleanup(shutil.rmtree,root);g["source_lineage_refs"]=[g["state_before_ref"]];write(ws/"inputs/input-gate.json",g);w["input_gate_ref"]=wsref("input_gate",ws/"inputs/input-gate.json",ws);V.execute(w,g,ws);self.assertEqual("input_invalid",read(ws/"stage-result.json")["blocker_class"])
    def test_no_third_party_imports(self):
        tree=ast.parse((ROOT/"scripts/validate_package.py").read_text(encoding="utf-8"));allowed={"__future__","argparse","hashlib","json","re","shutil","pathlib"};seen=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):seen.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom):seen.add((node.module or "").split(".")[0])
        self.assertEqual(set(),seen-allowed)

if __name__=="__main__":unittest.main()
