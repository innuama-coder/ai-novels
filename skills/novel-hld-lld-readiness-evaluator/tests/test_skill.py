from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL=Path(__file__).resolve().parents[1];REPO=SKILL.parents[1];HARNESS=REPO/"harnesses/novel-hld-autonomous";sys.path[:0]=[str(HARNESS),str(REPO)]
from runtime import composite_publisher as publisher  # noqa:E402
from runtime import coordinator  # noqa:E402
from runtime.canonical import file_ref, read_json, sha256_file, write_json  # noqa:E402
from runtime import hq2_stage_runtime as hq2_runtime  # noqa:E402
from runtime.hq2_stage_runtime import implementation_sha256  # noqa:E402
from runtime.package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope  # noqa:E402
from runtime.schema_catalog import SchemaCatalog  # noqa:E402

cp=importlib.import_module("harnesses.novel-hld-autonomous.tests.test_composite_publisher")
RUNTIME=SKILL/"scripts/run_skill.py";CATALOG=SchemaCatalog(HARNESS/"schemas")


def fref(path:Path,root:Path,role:str)->dict[str,str]:return file_ref(path,root=root,role=role)


def producer_ids(workspace:Path,work:dict)->list[str]:
    values=[]
    for artifact in work["upstream_completions"]:
        completion=read_json(workspace/artifact["completion_path"]);order=read_json(workspace/completion["work_order_ref"]["path"]);values.append(order["task_id"])
    return values


def evidence(role:str,document:dict,locator:str)->dict:
    value=document
    for token in locator.strip("/").split("/"):
        value=value[int(token)] if isinstance(value,list) else value[token]
    return {"role":role,"object_id":value["id"],"object_locator":locator,"actual_value":value,"contract_anchor":"the exact sealed object satisfies this test obligation"}


def test_item(identifier:str,input_ids:set[str],proof:list[dict],verdict="pass")->dict:
    return {"id":identifier,"input_ids":sorted(input_ids),"actual_result":"the sealed inputs reconstruct and trace the required contract","pass_fail_anchor":"all cited IDs and exact object values satisfy the named obligation","evidence":proof,"verdict":verdict}


def dimensions(ids:set[str],proof:list[dict])->list[dict]:
    return [{"dimension":name,"claim":f"{name} is supported by exact sealed object evidence","object_ids":sorted(ids),"evidence":proof[:1],"verdict":"pass"} for name in ("provenance","semantic_fit","instructional_quality","structure","consistency","boundary")]


def draft_for(workspace:Path,work_path:Path,mode:str)->Path:
    work=read_json(work_path);actual=work["file_allowlist"];by_role={item["role"]:item for item in actual};handoff=read_json(workspace/by_role["lld_handoff"]["path"])
    units=handoff["work_units"];unit_ids={x["id"] for x in units};story={v for x in units for v in x["storyline_ids"]};chars={v for x in units for v in x["character_ids"]};keys=unit_ids|{v for x in units for v in x["hkf_ids"]};chapter_defs={x["id"] for x in handoff["chapter_definition_refs"]}
    unit_proof=[evidence("lld_handoff",handoff,f"/work_units/{index}") for index in range(len(units))]
    if mode=="consumer_test":
        story_tests=[test_item("HQT-STORY-001",story,unit_proof)]
        char_tests=[] if not chars else [test_item("HQT-CHAR-001",chars,unit_proof)]
        key_tests=[test_item("HQT-KEY-001",keys,unit_proof)]
        chapter_proof=[evidence("lld_handoff",handoff,f"/chapter_definition_refs/{index}") for index in range(len(handoff["chapter_definition_refs"]))]
        chapter_tests=[test_item("HQT-CHAPTER-001",chapter_defs,chapter_proof)]
        constraint=test_item("HQT-CLASS-001",unit_ids,unit_proof)
        model={"schema_version":"1.0","skill":"novel-hld-lld-readiness-evaluator","stage":"HQ2","mode":mode,"hld_run_id":work["hld_run_id"],"task_id":work["task_id"],"source_artifacts":actual,"reconstruction_results":{"lld_work_order":sorted(unit_ids),"boundary":["HLD fixes obligations and prohibitions; LLD chooses scene realization"],"startup_conditions":["current HP1 handoff is sealed and ready"],"entry_exit_states":[{"work_unit_id":x["id"],"entry_state":x["entry_state"],"exit_state":x["exit_state"]} for x in units]},"storyline_trace_tests":story_tests,"character_arc_trace_tests":char_tests,"key_function_consumption_tests":key_tests,"chapter_definition_consumption_tests":chapter_tests,"constraint_open_elaboration_freedom_test":constraint,"missing_guesswork":[],"findings":[],"evidence_dimensions":dimensions(unit_ids|chapter_defs,unit_proof+chapter_proof),"verdict":"pass","defect_origin":"none"}
        sealed_task=None;canonical="handoff-consumption-test.json"
    else:
        trace=read_json(workspace/by_role["traceability"]["path"]);records=trace["records"];trace_proof=[evidence("traceability",trace,f"/records/{index}") for index in range(len(records))];proof=unit_proof+trace_proof
        lwrs={x["source_lwr_id"] for x in units};obligations=unit_ids|{v for x in units for v in x["hkf_ids"]}
        sealed=read_json(workspace/by_role["sealed_consumption_test"]["path"])
        model={"schema_version":"1.0","skill":"novel-hld-lld-readiness-evaluator","stage":"HQ2","mode":mode,"hld_run_id":work["hld_run_id"],"task_id":work["task_id"],"source_artifacts":actual,"sealed_consumption_test_ref":by_role["sealed_consumption_test"],"source_lwr_to_lwk_bijection_test":test_item("HQT-BIJECTION-001",lwrs|unit_ids,proof),"obligation_coverage_tests":[test_item("HQT-OBLIGATION-001",obligations,proof)],"classification_fidelity_tests":[test_item("HQT-CLASSIFICATION-001",unit_ids,proof)],"omission_enhancement_weakening_findings":[],"evidence_dimensions":dimensions(unit_ids,unit_proof),"verdict":"pass","defect_origin":"none"}
        sealed_task=sealed["task_id"];canonical="handoff-fidelity-test.json"
    session={"schema_version":"1.0","skill":"novel-hld-lld-readiness-evaluator","stage":"HQ2","mode":mode,"hld_run_id":work["hld_run_id"],"task_id":work["task_id"],"producer_task_ids":producer_ids(workspace,work),"sealed_consumer_task_id":sealed_task,"actual_read_refs":actual}
    draft=workspace/"drafts"/work["task_id"];write_json(draft/canonical,model);write_json(draft/"review-session.json",session);return draft


def bootstrap(root:Path):
    fixture=cp.Fixture(root);workspace=fixture.workspace
    state={"schema_version":"1.0","harness":coordinator.HARNESS,"hld_run_id":"hld-fixture","revision":1,"event_sequence":20,"status":"running","current_stage":"HQ2","accepted_completions":[cp.artifact(workspace,"HB0"),cp.artifact(workspace,"HP1")],"current_result_ref":None,"previous_state_ref":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"waiting_transaction_ref":None}
    state_path=workspace/"states"/"revision-hq2.json";write_json(state_path,state);state_ref=fref(state_path,workspace,"state_before")
    order,kind,composite=coordinator._issue_forward(workspace,state_ref,state,{},"2026-08-06T00:00:00Z")
    composite_path=workspace/"composite"/"HQ2-r001-state-000.json";write_json(composite_path,composite)
    ledger={"schema_version":"1.0","harness":coordinator.HARNESS,"hld_run_id":"hld-fixture","ledger_revision":0,"event_sequence":read_json(order)["event_sequence"],"current_state_ref":state_ref,"active_work_order_ref":fref(order,workspace,"work_order"),"active_task_kind":kind,"accepted_result_refs":[],"composite_state_ref":fref(composite_path,workspace,"composite_workspace_state"),"consumed_author_event_ids":[],"fingerprint_completion_counts":{},"terminal_status":None}
    coordinator._snapshot(workspace,ledger);return fixture,workspace,order


def run(work:Path,draft:Path):return subprocess.run([sys.executable,str(RUNTIME),str(work),str(draft)],capture_output=True,text=True)


def run_with_workspace_read_audit(workspace:Path,work:Path,draft:Path,injected_read:Path|None=None):
    seen:set[Path]=set();original_open=Path.open;original_read_text=Path.read_text;original_read_bytes=Path.read_bytes
    def record(path:Path)->None:
        try:path.resolve().relative_to(workspace.resolve())
        except (ValueError,OSError):return
        seen.add(path.resolve())
    def tracked_open(path:Path,*args,**kwargs):
        mode=args[0] if args else kwargs.get("mode","r")
        if "r" in mode:record(path)
        return original_open(path,*args,**kwargs)
    def tracked_text(path:Path,*args,**kwargs):record(path);return original_read_text(path,*args,**kwargs)
    def tracked_bytes(path:Path,*args,**kwargs):record(path);return original_read_bytes(path,*args,**kwargs)
    with mock.patch.object(Path,"open",tracked_open),mock.patch.object(Path,"read_text",tracked_text),mock.patch.object(Path,"read_bytes",tracked_bytes):
        code=hq2_runtime.execute(SKILL,work,draft);result=read_json(workspace/"stage-result.json") if (workspace/"stage-result.json").is_file() else None
        if injected_read is not None:injected_read.read_text(encoding="utf-8")
    order=read_json(work);gate=workspace/order["input_gate_ref"]["path"];state=workspace/order["state_before_ref"]["path"]
    allowed={work.resolve(),gate.resolve(),state.resolve(),*(workspace/ref["path"] for ref in order["file_allowlist"])}
    output=(workspace/order["output_directory"]).resolve();draft=draft.resolve()
    def generated(path:Path)->bool:
        relative=path.relative_to(workspace.resolve())
        return path.name=="stage-result.json" or (relative.parts and relative.parts[0].startswith(".hq2-")) or output in path.parents or draft in path.parents
    unexpected={path for path in seen if path not in {p.resolve() for p in allowed} and not generated(path)}
    return code,result,unexpected


def assert_internal(workspace:Path,work_path:Path,outcome:str):
    work=read_json(work_path);package=workspace/work["output_directory"];result=read_json(workspace/"stage-result.json");CATALOG.validate(result,"stage-result.schema.json");validate_result_envelope(result,work)
    manifest_name="package-manifest.json" if outcome=="ready" else "result-manifest.json";manifest=read_json(package/manifest_name);CATALOG.validate(manifest,"package-manifest.schema.json");validate_manifest(package,manifest)
    if outcome=="ready":validate_ready_profile(package,"HQ2.consumer_test" if "consumer" in work["task_id"] else "HQ2.fidelity_test")
    return package,result


def rewrite_order_and_gate(workspace:Path,work_path:Path,mutate)->None:
    work=read_json(work_path);gate_path=workspace/work["input_gate_ref"]["path"];gate=read_json(gate_path);mutate(work,gate);write_json(gate_path,gate);work["input_gate_ref"]=fref(gate_path,workspace,"input_gate");write_json(work_path,work)


class HQ2PublicRuntimeTests(unittest.TestCase):
    def test_read_audit_detects_injected_forbidden_package_member(self):
        with tempfile.TemporaryDirectory() as temp:
            _fixture,workspace,consumer=bootstrap(Path(temp));draft=draft_for(workspace,consumer,"consumer_test");work=read_json(consumer);hidden=workspace/work["upstream_completions"][1]["path"]
            code,_result,unexpected=run_with_workspace_read_audit(workspace,consumer,draft,hidden);self.assertEqual(0,code);self.assertIn(hidden.resolve(),unexpected)

    def test_real_workspace_reads_equal_each_sealed_mode_closure(self):
        with tempfile.TemporaryDirectory() as temp:
            _fixture,workspace,consumer=bootstrap(Path(temp));draft=draft_for(workspace,consumer,"consumer_test")
            code,_result,unexpected=run_with_workspace_read_audit(workspace,consumer,draft);self.assertEqual(0,code);self.assertEqual(set(),unexpected)
            consumer_order=read_json(consumer);consumer_roles={ref["role"] for ref in consumer_order["file_allowlist"]};self.assertNotIn("novel_hld_package",consumer_roles);self.assertNotIn("canonical_model",consumer_roles);self.assertNotIn("traceability",consumer_roles)
            coordinator.accept_result(workspace,workspace/"stage-result.json","2026-08-06T00:01:00Z");_,ledger=coordinator.load_current(workspace);fidelity=coordinator.verify_file_ref(ledger["active_work_order_ref"],workspace);draft2=draft_for(workspace,fidelity,"fidelity_test")
            code2,_result2,unexpected2=run_with_workspace_read_audit(workspace,fidelity,draft2);self.assertEqual(0,code2);self.assertEqual(set(),unexpected2)

    def test_p01_two_real_isolated_tasks_then_public_publisher(self):
        snapshots=[]
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp:
                _fixture,workspace,consumer=bootstrap(Path(temp));draft=draft_for(workspace,consumer,"consumer_test");done=run(consumer,draft);self.assertEqual(0,done.returncode,done.stderr);consumer_package,_=assert_internal(workspace,consumer,"ready")
                self.assertEqual(set(p.name for p in consumer_package.iterdir()),set(("handoff-consumption-test.json","review-session.json","consumption-test-execution.json","validation.json","package-manifest.json")))
                coordinator.accept_result(workspace,workspace/"stage-result.json","2026-08-06T00:01:00Z");_,ledger=coordinator.load_current(workspace);self.assertEqual("fidelity_test",ledger["active_task_kind"]);fidelity=coordinator.verify_file_ref(ledger["active_work_order_ref"],workspace)
                draft2=draft_for(workspace,fidelity,"fidelity_test");done2=run(fidelity,draft2);self.assertEqual(0,done2.returncode,done2.stderr);assert_internal(workspace,fidelity,"ready")
                coordinator.accept_result(workspace,workspace/"stage-result.json","2026-08-06T00:02:00Z");_,ledger=coordinator.load_current(workspace);self.assertEqual("publisher",ledger["active_task_kind"]);publish_order=coordinator.verify_file_ref(ledger["active_work_order_ref"],workspace)
                code,result=publisher.execute(publish_order);self.assertEqual((0,"ready"),(code,result["result"]));public=workspace/"HQ2-r0001-publisher-package";validate_ready_profile(public,"HQ2");validate_completion_bindings(workspace,public,read_json(public/"stage-completion.json"));snapshots.append(read_json(public/"lld-handoff-acceptance.json"))
        self.assertEqual(snapshots[0],snapshots[1])

    def test_local_contract_read_and_task_defects_are_revise(self):
        for defect in ("extra_schema","missing_read","extra_read","producer_task","partial_proof","fake_consumer_binding"):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as temp:
                _fixture,workspace,consumer=bootstrap(Path(temp));work=consumer;mode="consumer_test"
                if defect in {"fake_consumer_binding","partial_proof"}:
                    first=draft_for(workspace,consumer,mode);self.assertEqual(0,run(consumer,first).returncode);coordinator.accept_result(workspace,workspace/"stage-result.json","2026-08-06T00:01:00Z");_,ledger=coordinator.load_current(workspace);work=coordinator.verify_file_ref(ledger["active_work_order_ref"],workspace);mode="fidelity_test"
                draft=draft_for(workspace,work,mode);canonical=draft/("handoff-consumption-test.json" if mode=="consumer_test" else "handoff-fidelity-test.json");model=read_json(canonical);session=read_json(draft/"review-session.json")
                if defect=="extra_schema":model["unexpected"]=True
                elif defect=="missing_read":session["actual_read_refs"]=session["actual_read_refs"][:-1];model["source_artifacts"]=model["source_artifacts"][:-1]
                elif defect=="extra_read":session["actual_read_refs"].append(read_json(work)["state_before_ref"]);model["source_artifacts"].append(read_json(work)["state_before_ref"])
                elif defect=="producer_task":session["producer_task_ids"][0]="TASK-FORGED"
                elif defect=="partial_proof":
                    tests=[model["source_lwr_to_lwk_bijection_test"],*model["obligation_coverage_tests"],*model["classification_fidelity_tests"]]
                    for test in tests:test["evidence"]=[x for x in test["evidence"] if x["role"]!="traceability"]
                else:model["sealed_consumption_test_ref"]={**model["sealed_consumption_test_ref"],"role":"forged_consumer"}
                write_json(canonical,model);write_json(draft/"review-session.json",session);done=run(work,draft);self.assertEqual(2,done.returncode,done.stderr);_package,result=assert_internal(workspace,work,"revise");self.assertEqual("local_candidate",result["revision_class"])

    def test_consumer_report_access_and_tamper_reseal_fail_admission(self):
        for defect in ("presentation_candidate","tamper_handoff_reseal"):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as temp:
                _fixture,workspace,work=bootstrap(Path(temp));draft=draft_for(workspace,work,"consumer_test")
                if defect=="presentation_candidate":
                    report=workspace/"forbidden-human-review-report.json";write_json(report,{"answer":"leaked"})
                    def mutate(order,gate):
                        ref=fref(report,workspace,"presentation_candidate");order["file_allowlist"].append(ref);gate["file_allowlist"].append(ref)
                    rewrite_order_and_gate(workspace,work,mutate)
                else:
                    order=read_json(work);handoff_ref=next(x for x in order["file_allowlist"] if x["role"]=="lld_handoff");handoff=workspace/handoff_ref["path"];value=read_json(handoff);value["work_units"][0]["exit_state"]="tampered but resealed";write_json(handoff,value)
                    def mutate(order,gate):
                        for collection in (order["file_allowlist"],gate["file_allowlist"]):
                            next(x for x in collection if x["role"]=="lld_handoff")["sha256"]=sha256_file(handoff)
                    rewrite_order_and_gate(workspace,work,mutate)
                done=run(work,draft);self.assertEqual(3,done.returncode,done.stderr);self.assertFalse((workspace/read_json(work)["output_directory"]).exists());self.assertFalse((workspace/"stage-result.json").exists())

    def test_blocked_algebra_and_first_nonready_prefix(self):
        origins={"upstream_content":"upstream_defect","author_required":"author_required","reality_dependency":"reality_dependency"}
        for origin,blocker in origins.items():
            with self.subTest(origin=origin),tempfile.TemporaryDirectory() as temp:
                _fixture,workspace,work=bootstrap(Path(temp));draft=draft_for(workspace,work,"consumer_test");canonical=draft/"handoff-consumption-test.json";model=read_json(canonical);failed=model["key_function_consumption_tests"][0];failed["verdict"]="fail";model["verdict"]="fail";model["defect_origin"]=origin;model["findings"]=[{"id":"HQF-001","issue":"the handoff cannot be consumed without this unresolved condition","evidence_refs":[failed["id"]],"affected_ids":[failed["input_ids"][0]],"correction_condition":"supply the missing authorized condition"}];write_json(canonical,model)
                done=run(work,draft);self.assertEqual(2,done.returncode,done.stderr);_package,result=assert_internal(workspace,work,"blocked");self.assertEqual(blocker,result["blocker_class"])
                if origin=="upstream_content":
                    coordinator.accept_result(workspace,workspace/"stage-result.json","2026-08-06T00:01:00Z");_,ledger=coordinator.load_current(workspace);self.assertEqual("publisher",ledger["active_task_kind"]);publisher_order=coordinator.verify_file_ref(ledger["active_work_order_ref"],workspace);code,public_result=publisher.execute(publisher_order);self.assertEqual((2,"blocked",blocker),(code,public_result["result"],public_result["blocker_class"]));self.assertFalse((workspace/read_json(publisher_order)["output_directory"]/"stage-completion.json").exists())


if __name__=="__main__":unittest.main()
