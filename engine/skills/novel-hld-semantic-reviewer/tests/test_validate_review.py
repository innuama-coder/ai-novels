from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
HARNESS = REPO / "harnesses" / "novel-hld-autonomous"
sys.path.insert(0, str(HARNESS))

from runtime.canonical import file_ref, read_json, sha256_file, verify_file_ref, write_json  # noqa:E402
from runtime.contracts import SKILLS, UPSTREAM, next_stage  # noqa:E402
from runtime.design_stage_runtime import derive_file_allowlist, implementation_sha256  # noqa:E402
from runtime.hdd import project_unresolved  # noqa:E402
from runtime.package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope  # noqa:E402
from runtime.review_stage_runtime import CHALLENGES, CROSS_CHECKS, DOMAIN_CHECKS, _indexed_source_value, _load_upstream_models  # noqa:E402
from runtime.schema_catalog import SchemaCatalog  # noqa:E402


CATALOG = SchemaCatalog(HARNESS / "schemas")
CONTRACT = json.loads((SKILL / "references/runtime-contract.json").read_text(encoding="utf-8"))
RUNTIME = SKILL / "scripts/run_skill.py"
RUN_ID = "RUN-PUBLIC-001"
STAGES = ("HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HD1")
FILES = {
    "HA1": ("narrative-architecture.json", "narrative-architecture.md", "narrative_architecture"),
    "HS1": ("storyline-choreography.json", "storyline-choreography.md", "storyline_choreography"),
    "HC1": ("character-arc-placement.json", "character-arc-placement.md", "character_arc_placement"),
    "HI1": ("narrative-information-architecture.json", "narrative-information-architecture.md", "narrative_information_architecture"),
    "HR1": ("rhythm-continuity-architecture.json", "rhythm-continuity-architecture.md", "rhythm_continuity_architecture"),
    "HK1": ("key-scene-function-map.json", "key-scene-function-map.md", "key_scene_function_map"),
    "HD1": ("chapter-definition-architecture.json", "chapter-definition-architecture.md", "chapter_definition_architecture"),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_module("hq1_base_fixture", REPO / "skills/novel-hld-narrative-architect/tests/test_skill.py")
STAGE_MODULES = {
    "HA1": BASE,
    "HS1": load_module("hq1_hs", REPO / "skills/novel-hld-storyline-choreographer/tests/test_skill.py"),
    "HC1": load_module("hq1_hc", REPO / "skills/novel-hld-character-arc-placer/tests/test_skill.py"),
    "HI1": load_module("hq1_hi", REPO / "skills/novel-hld-information-architect/tests/test_skill.py"),
    "HR1": load_module("hq1_hr", REPO / "skills/novel-hld-rhythm-continuity-architect/tests/test_skill.py"),
    "HK1": load_module("hq1_hk", REPO / "skills/novel-hld-key-scene-function-planner/tests/test_skill.py"),
    "HD1": load_module("hq1_hd", REPO / "skills/novel-hld-chapter-definition-designer/tests/test_skill.py"),
}


def producer_protocol_refs(workspace: Path, stage: str):
    protocol=workspace/"protocol"/stage;gate=protocol/"input-gate.json";state=protocol/"state.json";order=protocol/"work-order.json"
    write_json(gate,{"stage":stage,"fixture":True});write_json(state,{"stage":stage,"fixture":True})
    gate_ref=file_ref(gate,root=workspace,role="input_gate");state_ref=file_ref(state,root=workspace,role="state_before")
    write_json(order,{"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":RUN_ID,"revision":0,"work_order_id":f"WO-{stage}-FIXTURE","task_id":f"TASK-{stage}-FIXTURE","stage":stage,"action":"execute","exact_owner_skill":SKILLS[stage],"owner_version":"1.0.0","implementation_sha256":"4"*64,"event_sequence":1,"result_timestamp":"2026-08-06T00:00:00Z","input_gate_ref":gate_ref,"state_before_ref":state_ref,"upstream_completions":[],"file_allowlist":[gate_ref],"unresolved_projection":[],"mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"output_directory":"fixture","submission_status":"open"})
    return gate_ref,state_ref,file_ref(order,root=workspace,role="work_order")


BASE.protocol_refs=producer_protocol_refs


def artifact_ref(main: Path, manifest: Path, completion: Path, workspace: Path) -> dict:
    return {"path":main.relative_to(workspace).as_posix(),"sha256":sha256_file(main),"manifest_path":manifest.relative_to(workspace).as_posix(),"manifest_sha256":sha256_file(manifest),"completion_path":completion.relative_to(workspace).as_posix(),"completion_sha256":sha256_file(completion)}


def build_design_package(root: Path, stage: str, prior: list[dict], source_refs: list[dict]) -> dict:
    module = STAGE_MODULES[stage]
    canonical_name, preview_name, artifact_role = FILES[stage]
    package = root / "upstream" / stage / "package"
    package.mkdir(parents=True)
    gate_ref, state_ref, order_ref = BASE.protocol_refs(root, stage)
    actual_reads = source_refs + [
        {"role":f"upstream::{s}::main","path":item["path"],"sha256":item["sha256"]}
        for s, item in zip(UPSTREAM[stage], prior)
    ]
    if stage in {"HA1", "HS1", "HC1"}:
        prior_contract = BASE.CONTRACT
        BASE.CONTRACT = json.loads((REPO / f"skills/{SKILLS[stage]}/references/runtime-contract.json").read_text(encoding="utf-8"))
        try:
            model = BASE.stage_model(stage, gate_ref, actual_reads)
        finally:
            BASE.CONTRACT = prior_contract
    else:
        model = module.stage_model(stage, gate_ref, actual_reads)
    main = package / canonical_name
    write_json(main, model)
    write_json(package / "generation-session.json", {"schema_version":"1.0","stage":stage})
    write_json(package / "generation-evidence/00.json", {"schema_version":"1.0","stage":stage})
    write_json(package / "execution-record.json", {"schema_version":"1.0","stage":stage})
    (package / preview_name).write_text(f"# {stage}\n", encoding="utf-8", newline="")
    validation = {"schema_version":"1.0","skill":SKILLS[stage],"stage":stage,"hld_run_id":RUN_ID,"status":"pass","deterministic_checks":["fixture producer passed"],"errors":[],"semantic_quality_claim":"producer claim is not HQ1 evidence","semantic_review_ref":"generation-evidence/00.json"}
    CATALOG.validate(validation,"design-validation.schema.json")
    write_json(package / "validation.json", validation)
    manifest = BASE.write_manifest(package, stage, {artifact_role:main,"generation_session":package/"generation-session.json","generation_evidence":package/"generation-evidence/00.json","execution_record":package/"execution-record.json","preview":package/preview_name,"validation":package/"validation.json"})
    completion_value={"schema_version":"1.0","harness":"novel-hld-autonomous","stage":stage,"skill":SKILLS[stage],"hld_run_id":RUN_ID,"revision":0,"status":"ready","input_gate_ref":gate_ref,"state_before_ref":state_ref,"work_order_ref":order_ref,"manifest_ref":file_ref(manifest,root=root,role="package_manifest"),"validation_ref":file_ref(package/"validation.json",root=root,role="validation"),"upstream_completions":prior,"canonical_artifacts":[file_ref(main,root=root,role=artifact_role)],"owner_implementation":{"skill":SKILLS[stage],"version":"1.0.0","sha256":"4"*64},"return_binding":None,"ready_capabilities":[f"{stage.lower()}_ready"],"next_allowed_stage":next_stage(stage)}
    CATALOG.validate(completion_value,"stage-completion.schema.json")
    completion=package/"stage-completion.json";write_json(completion,completion_value)
    validate_ready_profile(package,stage);validate_manifest(package,read_json(manifest));validate_completion_bindings(root,package,completion_value)
    return artifact_ref(main,manifest,completion,root)


def walk_objects(value, stage, locator=""):
    out={}
    prefixes={"HA1":("HST-","HNU-","HCH-"),"HS1":("HTS-","HTC-","HCD-"),"HC1":("HAS-","HRS-"),"HI1":("HPV-","HKS-","HSP-","HIN-"),"HR1":("HTM-","HPC-","HTN-"),"HK1":("HKF-","LWR-"),"HD1":("HDF-","HDC-")}[stage]
    if isinstance(value,dict):
        if isinstance(value.get("id"),str) and value["id"].startswith(prefixes):out[value["id"]]=(locator,value)
        for key,child in value.items():out.update(walk_objects(child,stage,f"{locator}/{key.replace('~','~0').replace('/','~1')}"))
    elif isinstance(value,list):
        for i,child in enumerate(value):out.update(walk_objects(child,stage,f"{locator}/{i}"))
    return out


def build_case(root: Path, defect: str = "none"):
    hb0_ref, hb0_files = BASE.build_hb0(root)
    source_refs=[file_ref(hb0_files["source_index"],root=root,role="source_index"),file_ref(hb0_files["source"],root=root,role="source::intent")]
    upstream=[hb0_ref]
    for stage in STAGES: upstream.append(build_design_package(root,stage,list(upstream),source_refs))
    state={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":RUN_ID,"revision":0,"event_sequence":1,"status":"running","current_stage":"HQ1","accepted_completions":upstream,"current_result_ref":None,"previous_state_ref":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"waiting_transaction_ref":None}
    state_path=root/"state-before.json";write_json(state_path,state);state_ref=file_ref(state_path,root=root,role="state_before")
    baseline_manifest=file_ref(hb0_files["manifest"],root=root,role="baseline_manifest");baseline_validation=file_ref(hb0_files["validation"],root=root,role="baseline_validation")
    allowlist=derive_file_allowlist(root,state_ref,baseline_manifest,baseline_validation,source_refs,upstream,UPSTREAM["HQ1"])
    projection=project_unresolved(read_json(hb0_files["main"])["unresolved_register"])["HQ1"]
    gate={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":RUN_ID,"stage":"HQ1","mode":"forward","state_before_ref":state_ref,"hb0_completion_ref":upstream[0],"upstream_completions":upstream,"baseline_manifest_ref":baseline_manifest,"baseline_validation_ref":baseline_validation,"source_lineage_refs":source_refs,"exact_owner_skill":SKILLS["HQ1"],"owner_version":"1.0.0","implementation_sha256":implementation_sha256(SKILL),"return_binding":None,"unresolved_projection":projection,"revision_plan_ref":None,"revision_plan_state_ref":None,"file_allowlist":allowlist}
    gate_path=root/"input-gate.json";write_json(gate_path,gate);gate_ref=file_ref(gate_path,root=root,role="input_gate")
    order={"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":RUN_ID,"revision":0,"work_order_id":"WO-HQ1-001","task_id":"TASK-HQ1-001","stage":"HQ1","action":"execute","exact_owner_skill":SKILLS["HQ1"],"owner_version":"1.0.0","implementation_sha256":implementation_sha256(SKILL),"event_sequence":2,"result_timestamp":"2026-08-06T00:00:00Z","input_gate_ref":gate_ref,"state_before_ref":state_ref,"upstream_completions":upstream,"file_allowlist":allowlist,"unresolved_projection":projection,"mode":"forward","return_binding":None,"revision_plan_ref":None,"revision_plan_state_ref":None,"output_directory":"output","submission_status":"open"}
    order_path=root/"work-order.json";write_json(order_path,order)
    role_map={item["role"]:item for item in allowlist};actual_reads=[role_map[item["role"]] for item in source_refs]
    for stage in UPSTREAM["HQ1"]:
        roles=("upstream::HB0::main","baseline_manifest","upstream::HB0::completion","baseline_validation") if stage=="HB0" else tuple(f"upstream::{stage}::{suffix}" for suffix in ("main","manifest","completion","validation"))
        actual_reads.extend(role_map[role] for role in roles)
    models={stage:read_json(root/item["path"]) for stage,item in zip(UPSTREAM["HQ1"],upstream)}
    objects={}
    for stage in STAGES:objects.update({key:(stage,*value) for key,value in walk_objects(models[stage],stage).items()})
    first_ids=list(objects)
    def ev(identifier):
        stage,locator,value=objects[identifier]
        return [{"stage":stage,"object_id":identifier,"object_locator":locator,"actual_value":value,"contract_anchor":"the exact canonical object carries the claimed obligation"}]
    by_stage={stage:[identifier for identifier,(owner,_locator,_value) in objects.items() if owner==stage] for stage in STAGES}
    domain=[{"check_id":name,"status":"pass","evidence":[item for identifier in by_stage[stage] for item in ev(identifier)],"reason":"every object-level state and obligation in this producer is checked"} for name,stage in zip(DOMAIN_CHECKS,STAGES)]
    cross_stage_sets=(("HA1","HS1"),("HS1","HC1"),("HA1","HS1","HC1","HR1"),("HI1","HR1","HK1","HD1"))
    cross=[{"check_id":name,"status":"pass","evidence":[item for stage in stage_set for item in ev(by_stage[stage][0])],"reason":"cross-stage references preserve cause, state, derivation and responsibility"} for name,stage_set in zip(CROSS_CHECKS,cross_stage_sets)]
    authority={"check_id":"authority_and_open_items","status":"pass","evidence":ev(first_ids[0]),"reason":"authority and open items remain within the admitted baseline"}
    challenges=[{"check_id":f"HQC-{i:02d}","dimension":dimension,"status":"pass","evidence":ev(first_ids[(i+10)%len(first_ids)]),"reason":"the adversarial challenge is answered by an exact canonical value"} for i,dimension in enumerate(CHALLENGES,1)]
    boundary={"check_id":"hld_lld_boundary_review","status":"pass","evidence":ev(first_ids[-1]),"reason":"the artifact fixes high-level control without scene prose"}
    checks=[*domain,*cross,authority,*challenges,boundary]
    review={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":RUN_ID,"review_task_id":order["task_id"],"input_gate_ref":gate_ref,"source_artifacts":actual_reads,"domain_reviews":domain,"cross_domain_checks":cross,"authority_and_open_item_review":authority,"decision_dependencies":[],"decision_dependency_review":[],"causal_and_reality_challenges":challenges,"boundary_review":boundary,"findings":[],"verdict":"pass","pass_claims":[{"check_id":item["check_id"],"evidence":item["evidence"],"pass_anchor":"the cited actual value satisfies the named contract"} for item in checks],"coverage_summary":{"checked_object_ids":first_ids,"applicable_checks":[item["check_id"] for item in checks],"not_applicable_checks":[]}}
    if defect in {"upstream","author","reality"}:
        origin={"upstream":"upstream_content","author":"author_required","reality":"reality_dependency"}[defect]
        challenges[0]["status"]="fail";review["pass_claims"]=[item for item in review["pass_claims"] if item["check_id"]!=challenges[0]["check_id"]]
        review["findings"]=[{"id":"HFN-001","severity":"major","issue":"the cited causal transition lacks an authorized enabling condition","evidence_refs":[challenges[0]["check_id"]],"affected_ids":[first_ids[0]],"violated_contract":"causal transitions require an explicit enabling state","defect_origin":origin,"correction_condition":"supply an authorized cause and preserve all downstream state bindings"}];review["verdict"]="fail"
    elif defect=="routing":
        review["findings"]=[{"id":"HFN-001","severity":"major","issue":"defect","evidence_refs":["HQC-01"],"affected_ids":[first_ids[0]],"violated_contract":"x","defect_origin":"upstream_content","correction_condition":"x","target_skill":"novel-hld-narrative-architect"}];review["verdict"]="fail"
    elif defect=="near_miss":review["domain_reviews"][0]["evidence"][0]["actual_value"]={"plausible":"but not canonical"}
    elif defect=="pass_only_coverage":
        primary=[*domain,*cross,authority,*challenges,boundary]
        counts={identifier:sum(1 for check in primary for item in check["evidence"] if item["object_id"]==identifier) for identifier in first_ids}
        target=next(identifier for identifier,count in counts.items() if count==1)
        for check in primary:check["evidence"]=[item for item in check["evidence"] if item["object_id"]!=target]
    elif defect=="pass_claim_tamper":review["pass_claims"][0]["evidence"]=ev(first_ids[-1])
    elif defect=="missing_read":review["source_artifacts"]=review["source_artifacts"][:-1]
    elif defect=="extra_read":review["source_artifacts"].append(role_map["state_before"])
    draft=root/"draft";write_json(draft/"canonical.json",review)
    session={"schema_version":"1.0","skill":SKILLS["HQ1"],"task_id":order["task_id"],"producer_task_ids":[f"TASK-{stage}-FIXTURE" for stage in UPSTREAM["HQ1"]],"actual_read_refs":actual_reads}
    session["producer_task_ids"]=[read_json(root/read_json(root/item["completion_path"])["work_order_ref"]["path"])["task_id"] for item in upstream]
    if defect=="missing_read":session["actual_read_refs"]=session["actual_read_refs"][:-1]
    elif defect=="extra_read":session["actual_read_refs"].append(role_map["state_before"])
    write_json(draft/"review-session.json",session)
    return order_path,draft,root/"output",upstream


class HQ1PublicRuntimeTests(unittest.TestCase):
    def test_e1_operational_slot_uses_closed_typed_source_projection(self):
        entry={"source_id":"SLOT-ARCHIVE-CUSTODIAN","domain":"environments","source":{"path":"P1/canonical-models/environment-system.json"},"schema_discriminator":"e1_operational_slot"}
        value={"actor_slot_id":"SLOT-ARCHIVE-CUSTODIAN","permitted_actions":["sealed detail"]}
        self.assertEqual({"slot_id":"SLOT-ARCHIVE-CUSTODIAN","kind":"e1_operational_slot"},_indexed_source_value(entry,value))
        self.assertEqual({"slot_id":"SLOT-ARCHIVE-CUSTODIAN","kind":"e1_operational_slot"},_indexed_source_value(entry,"SLOT-ARCHIVE-CUSTODIAN"))
        with self.assertRaisesRegex(Exception,"projection is invalid"):
            _indexed_source_value(entry,{"actor_slot_id":"SLOT-OTHER"})
        with self.assertRaisesRegex(Exception,"projection is invalid"):
            _indexed_source_value(entry,"SLOT-OTHER")
        with self.assertRaisesRegex(Exception,"discriminator is invalid"):
            _indexed_source_value({**entry,"schema_discriminator":"untrusted"},value)
        ordinary={"source_id":"EV-STEP-001","domain":"events","source":{"path":"P1/canonical-models/event-timeline.json"},"schema_discriminator":"process"}
        self.assertIs(value,_indexed_source_value(ordinary,value))

    def run_case(self,defect="none"):
        temp=tempfile.TemporaryDirectory();root=Path(temp.name);order,draft,output,upstream=build_case(root,defect);completed=subprocess.run([sys.executable,str(RUNTIME),str(order),str(draft)],capture_output=True,text=True);return temp,root,order,output,upstream,completed

    def assert_result(self,root,order_path,output,outcome):
        order=read_json(order_path);result=read_json(output/"stage-result.json");CATALOG.validate(result,"stage-result.schema.json");validate_result_envelope(result,order);self.assertEqual(outcome,result["result"]);manifest=read_json(verify_file_ref(result["result_manifest_ref"],root));CATALOG.validate(manifest,"package-manifest.schema.json");validate_manifest(output/"package",manifest);return result

    def test_p01_real_public_ready_and_deterministic(self):
        snapshots=[]
        for _ in range(2):
            temp,root,order,output,_upstream,completed=self.run_case()
            with temp:
                self.assertEqual(0,completed.returncode,completed.stderr);result=self.assert_result(root,order,output,"ready");validate_ready_profile(output/"package","HQ1");completion=read_json(verify_file_ref(result["completion_ref"],root));validate_completion_bindings(root,output/"package",completion);snapshots.append(read_json(output/"package/hld-semantic-review.json"))
        self.assertEqual(snapshots[0],snapshots[1])

    def test_local_schema_evidence_and_read_defects_are_revise(self):
        for defect in ("routing","near_miss","missing_read","extra_read","pass_only_coverage","pass_claim_tamper"):
            with self.subTest(defect=defect):
                temp,root,order,output,_upstream,completed=self.run_case(defect)
                with temp:self.assertEqual(2,completed.returncode,completed.stderr);self.assert_result(root,order,output,"revise");self.assertFalse((output/"package/hld-semantic-review.json").exists())

    def test_nonlocal_findings_route_only_by_affected_ids(self):
        expected={"upstream":"upstream_defect","author":"author_required","reality":"reality_dependency"}
        for defect,blocker in expected.items():
            with self.subTest(defect=defect):
                temp,root,order,output,_upstream,completed=self.run_case(defect)
                with temp:
                    self.assertEqual(2,completed.returncode,completed.stderr);result=self.assert_result(root,order,output,"blocked");self.assertEqual(blocker,result["blocker_class"]);report=read_json(output/"package/blocked-report.json");self.assertNotIn("target_skill",report);self.assertNotIn("reopen_from",report)

    def test_stale_upstream_manifest_fails_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);order,draft,output,upstream=build_case(root);path=root/upstream[-1]["manifest_path"];value=read_json(path);value["status"]="blocked";write_json(path,value);completed=subprocess.run([sys.executable,str(RUNTIME),str(order),str(draft)],capture_output=True,text=True);self.assertEqual(3,completed.returncode);self.assertFalse(output.exists())

    def test_closed_work_order_and_allowlist_defects_fail_admission(self):
        mutations={
            "extra":lambda value:value.update({"unexpected":True}),
            "missing":lambda value:value.pop("stage"),
            "wrong_type":lambda value:value.update({"revision":"zero"}),
            "wrong_enum":lambda value:value.update({"action":"repair"}),
            "allowlist_missing":lambda value:value["file_allowlist"].pop(),
            "allowlist_extra":lambda value:value["file_allowlist"].append(value["input_gate_ref"]),
        }
        for label,mutate in mutations.items():
            with self.subTest(label=label),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);order,draft,output,_upstream=build_case(root);value=read_json(order);mutate(value);write_json(order,value)
                completed=subprocess.run([sys.executable,str(RUNTIME),str(order),str(draft)],capture_output=True,text=True)
                self.assertEqual(3,completed.returncode,completed.stderr);self.assertFalse(output.exists())

    def test_each_upstream_integrity_surface_fails_closed(self):
        for role in ("main","manifest","completion","validation"):
            with self.subTest(role=role),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);order,draft,output,upstream=build_case(root)
                if role=="main":path=root/upstream[-1]["path"]
                elif role=="manifest":path=root/upstream[-1]["manifest_path"]
                elif role=="completion":path=root/upstream[-1]["completion_path"]
                else:
                    work_order=read_json(order);last_stage=STAGES[-1];path=root/next(item["path"] for item in work_order["file_allowlist"] if item["role"]==f"upstream::{last_stage}::validation")
                value=read_json(path);value["tampered_after_seal"]=True;write_json(path,value)
                completed=subprocess.run([sys.executable,str(RUNTIME),str(order),str(draft)],capture_output=True,text=True)
                self.assertEqual(3,completed.returncode,completed.stderr);self.assertFalse(output.exists())


if __name__=="__main__":unittest.main()
