from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
SKILL=Path(__file__).resolve().parents[1];REPO=SKILL.parents[1];BASE_PATH=REPO/"skills/novel-hld-narrative-architect/tests/test_skill.py"
spec=importlib.util.spec_from_file_location("public_design_fixture_hi1",BASE_PATH);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
from runtime.canonical import canonical_sha256
CONTRACT=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"));RUNTIME=SKILL/"scripts/run_skill.py"
BASE.SKILL=SKILL;BASE.CONTRACT=CONTRACT;BASE.RUNTIME=RUNTIME
ORIGINAL_ELEMENT=BASE.element
def traced_element(identifier,**extra):
    value=ORIGINAL_ELEMENT(identifier,**extra);value.setdefault("resolution_ref",None);return value
BASE.element=traced_element

def stage_model(stage,input_gate_ref,actual_reads):
    model=BASE.common_model(stage,input_gate_ref,actual_reads);e=BASE.element
    model.update({
        "pov_policy":e("HPV-POLICY-001",allowed_modes=["internal_limited"],switch_rule="unit boundary only",legality_rule="perceived or legitimately inferred"),
        "unit_pov_assignments":[e("HPV-UNIT-001",unit_id="HNU-001",pov_character_id="CHR-001",focalization_mode="internal_limited",perception_limits=["no remote perception"])],
        "chapter_pov_assignments":[e("HPV-CHAPTER-001",chapter_id="HCH-001",parent_unit_id="HNU-001",hc1_agency_contract_id="HAS-AGENCY-001",pov_character_id="CHR-001",focalization_mode="internal_limited",knowledge_acquisition_modes=["perceived"],perception_limits=["只允许人物当时能够感知或合法获知的信息"])],
        "information_nodes":[e("HIN-001",source_information_id="INT-FREE-001",knower_ids=["CHR-001"],reader_state="known",acquisition_mode="perceived",earliest_legal_unit_id="HNU-001",forbidden_leak_unit_ids=[],resolution_ref=None)],
        "knowledge_states":[e("HKS-CHR-001",character_id="CHR-001",unit_id="HNU-001",information_node_ids=["HIN-001"],misbelief_node_ids=[])],
        "reader_information_states":[e("HKS-READER-001",unit_id="HNU-001",information_node_ids=["HIN-001"],inference_permissions=["infer authorized pressure"])],
        "suspense_chains":[e("HSP-001",setup_node_ids=["HIN-001"],probe_node_ids=[],reveal_node_ids=["HIN-001"],payoff_node_ids=["HIN-001"],authorized_open_terminal=None)],
        "reveal_payoff_matrix":[e("HIN-RPM-001",information_node_ids=["HIN-001"],setup_unit_ids=["HNU-001"],terminal_unit_id="HNU-001",terminal_kind="payoff")],
        "concealment_and_inference_rules":[e("HIN-RULE-001",information_node_ids=["HIN-001"],concealment_basis="outside perception before unit",legal_inferences=["authorized pressure"],forbidden_inferences=["remote knowledge"])],
    })
    owned=[item["id"] for name in CONTRACT["object_arrays"] for item in model[name]]+[model[name]["id"] for name in CONTRACT.get("object_fields",{})]
    model["authority_partition"]["hld_ownership"]["hld_owned"]=owned
    model["derivation_claims"]=[{"id":"DRV-001","source_refs":[BASE.FREE_ID],"target_locator":"/pov_policy/legality_rule","value_sha256":canonical_sha256(model["pov_policy"]["legality_rule"])}];return model
BASE.stage_model=stage_model
ORIGINAL=BASE.build_case
SHARED_DEFECTS={"authority_tamper","derivation_tamper","option_tamper","projection_tamper","fake_resolution","auxiliary_extra","unique_solution","unique_solution_missing_exclusion","resolved_mustask","resolved_mustask_missing","resolved_mustask_wrong"}
TARGET_ARRAY="unit_pov_assignments"
def assert_shared_injection(draft,defect,model):
    option=BASE.read_json(draft/"generation-evidence/02-option-analysis.json");projection=BASE.read_json(draft/"generation-evidence/03-projection-analysis.json");target=model[TARGET_ARRAY][0]
    checks={
        "authority_tamper":lambda:model["authority_partition"]["source_classifications"]["freedom"]==[],
        "derivation_tamper":lambda:model["derivation_claims"][0]["value_sha256"]=="0"*64,
        "option_tamper":lambda:len(option["candidates"])>1 and option["candidates"][0]["canonical_difference"]==option["candidates"][1]["canonical_difference"],
        "projection_tamper":lambda:projection["selected"]=="OPT-NOT-EXIST",
        "fake_resolution":lambda:target["resolution_ref"] is not None,
        "auxiliary_extra":lambda:option.get("unexpected") is True,
        "unique_solution":lambda:len(option["candidates"])==1 and bool(option["unique_solution_exclusion_evidence"]),
        "unique_solution_missing_exclusion":lambda:len(option["candidates"])==1 and option["unique_solution_exclusion_evidence"] is None,
        "resolved_mustask":lambda:target["ownership_class"]=="source_projection" and target["resolution_ref"]["role"]=="source::resolution",
        "resolved_mustask_missing":lambda:target["ownership_class"]=="source_projection" and target["resolution_ref"] is None,
        "resolved_mustask_wrong":lambda:target["ownership_class"]=="source_projection" and target["resolution_ref"]["role"]=="source::intent",
    }
    if defect in checks and not checks[defect]():raise AssertionError(f"shared defect was not injected: {defect}")
def build_case(root,defect="none"):
    order,draft,output,upstream=ORIGINAL(root,defect if defect in SHARED_DEFECTS else "none");model=BASE.read_json(draft/"canonical.json");assert_shared_injection(draft,defect,model)
    option_path=draft/"generation-evidence/02-option-analysis.json";option=BASE.read_json(option_path)
    for index,candidate in enumerate(option["candidates"],1):candidate.setdefault("downstream_impact",f"impact-{index}")
    option.setdefault("unique_solution_exclusion_evidence",None)
    BASE.write_json(option_path,option)
    review_path=draft/"generation-evidence/04-adversarial-self-review.json";review=BASE.read_json(review_path)
    for challenge in review["challenges"]:challenge["result"]="pass"
    BASE.write_json(review_path,review)
    if defect=="semantic":model["suspense_chains"][0]["payoff_node_ids"]=[]
    elif defect=="boundary":model["dialogue"]="out-of-scope wording"
    elif defect=="extra_top":model["unexpected_control"]="closed schema"
    elif defect=="object_extra":model["unit_pov_assignments"][0]["unexpected_control"]=True
    elif defect=="object_missing":del model["unit_pov_assignments"][0]["focalization_mode"]
    elif defect=="wrong_enum":model["unit_pov_assignments"][0]["ownership_class"]="author_owned"
    elif defect=="wrong_type":model["unit_pov_assignments"][0]["perception_limits"]="not-an-array"
    elif defect=="spurious_resolution":model["unit_pov_assignments"][0]["resolution_ref"]=model["input_gate_ref"]
    BASE.write_json(draft/"canonical.json",model);return order,draft,output,upstream
BASE.build_case=build_case

class PublicHarnessCompatibilityTests(BASE.PublicHarnessCompatibilityTests):
    def test_closed_schema_rejects_wrong_type(self):
        temporary,root,order,output,_upstream,completed=self.run_case("wrong_type")
        with temporary:self.assertEqual(2,completed.returncode,completed.stderr);self.assert_public_envelope(root,order,output,"revise")
    def test_spurious_resolution_binding_is_revise(self):
        temporary,root,order,output,_upstream,completed=self.run_case("spurious_resolution")
        with temporary:self.assertEqual(2,completed.returncode,completed.stderr);self.assert_public_envelope(root,order,output,"revise")
    def test_author_required_is_public_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);order,draft,output,_=build_case(root);path=draft/"generation-evidence/00-dependency-assessment.json";value=BASE.read_json(path);value["assessments"][0]["disposition"]="required_now";BASE.write_json(path,value)
            completed=subprocess.run([sys.executable,str(RUNTIME),str(order),str(draft)],capture_output=True,text=True);self.assertEqual(2,completed.returncode,completed.stderr);result=self.assert_public_envelope(root,order,output,"blocked");self.assertEqual("author_required",result["blocker_class"]);self.assertIsNone(result["completion_ref"])

if __name__=="__main__":unittest.main()
