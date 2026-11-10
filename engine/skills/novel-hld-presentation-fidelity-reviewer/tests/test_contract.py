from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "skills/novel-hld-review-report-assembler/tests"))
import public_fixture as fx  # noqa: E402

B = fx.B
publisher = fx.publisher
from runtime.package_envelope import validate_manifest, validate_ready_profile, validate_result_envelope  # noqa: E402


def write(path: Path, value: object) -> None:
    fx.write_json(path, value)


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def rewrite_allow(work_path: Path, gate_path: Path, allow: list[dict], workspace: Path) -> dict:
    work = json.loads(work_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    work["file_allowlist"] = allow; gate["file_allowlist"] = allow
    write(gate_path, gate); work["input_gate_ref"] = fx.fref(gate_path, workspace, "input_gate"); write(work_path, work)
    return work


def reseal_a_report(fixture, work_path: Path, gate_path: Path, draft: Path, mutate) -> dict:
    workspace = fixture.workspace; report_path = workspace / "internal/HH1-A/package/hld-human-review-report.json"; manifest_path = workspace / "internal/HH1-A/package/package-manifest.json"
    report = json.loads(report_path.read_text(encoding="utf-8")); mutate(report); write(report_path, report)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); digest = publisher.sha256(report_path)
    for item in manifest["files"]:
        if item["path"] == "hld-human-review-report.json": item["sha256"] = digest
    for item in manifest["artifact_roles"].values():
        if item["path"] == "hld-human-review-report.json": item["sha256"] = digest
    write(manifest_path, manifest)
    work = json.loads(work_path.read_text(encoding="utf-8")); allow = copy.deepcopy(work["file_allowlist"])
    for item in allow:
        if item["role"] == "human_review_report": item["sha256"] = digest
        if item["role"] == "hh1_a_manifest": item["sha256"] = publisher.sha256(manifest_path)
    work = rewrite_allow(work_path, gate_path, allow, workspace)
    review_path=draft/"canonical.json";review=json.loads(review_path.read_text(encoding="utf-8"));review["review_bindings"]["report_sha256"]=digest;review["review_bindings"]["report_manifest_sha256"]=publisher.sha256(manifest_path);write(review_path,review)
    session_path=draft/"review-session.json";session=json.loads(session_path.read_text(encoding="utf-8"));session["declared_allowlist"]=allow;session["actual_read_refs"]=allow;refs={item["role"]:item for item in allow};session["candidate_report_ref"]=refs["human_review_report"];session["candidate_manifest_ref"]=refs["hh1_a_manifest"];write(session_path,session)
    return report


class HH1BPublicRuntimeTests(unittest.TestCase):
    def build(self, verdict: str = "pass"):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        return fx.build_b(Path(self.temp.name), verdict)

    def test_independent_budget_accepts_twenty_four_minutes_not_more(self):
        fixture, work, _, _, draft, _ = self.build()
        context = B.load_context(work, B.SPEC, B.impl_hash(), B._catalog())
        machine, models, report, producer = B.admit(context)
        review_path = draft / "canonical.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))

        within = {"cjk_characters": 10368, "latin_words": 122, "visual_count": 0, "estimated_read_minutes": 21.224}
        report["review_budget"].update(within)
        review["reading_budget_validation"] = {"formula": "CJK/500 + Latin/250 + visuals*0.25", "declared": within, "recomputed": within, "verdict": "pass"}
        write(review_path, review)
        with patch.object(B, "_budget", return_value=within):
            B.validate_draft(context, draft, machine, models, report, producer)

        over = {**within, "estimated_read_minutes": 24.0001}
        report["review_budget"].update(over)
        review["reading_budget_validation"] = {"formula": "CJK/500 + Latin/250 + visuals*0.25", "declared": over, "recomputed": over, "verdict": "pass"}
        write(review_path, review)
        with patch.object(B, "_budget", return_value=over), self.assertRaises(B.InternalCondition) as failure:
            B.validate_draft(context, draft, machine, models, report, producer)
        self.assertEqual(failure.exception.code, "HH1B_BUDGET_EVIDENCE_DRIFT")

    def test_world_environment_budget_recount_is_executable(self):
        fixture, _, _, _, _, _ = self.build()
        report = json.loads((fixture.workspace / "internal/HH1-A/package/hld-human-review-report.json").read_text(encoding="utf-8"))
        self.assertEqual(B._budget(report), {key: report["review_budget"][key] for key in ("cjk_characters", "latin_words", "visual_count", "estimated_read_minutes")})

    def test_ready_public_profile_and_envelope(self):
        fixture, work, order, _, draft, _ = self.build()
        code, result = B.execute(work, draft); package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["result_scope"]), (0, "ready", "composite_internal"))
        validate_manifest(package, json.loads((package / "package-manifest.json").read_text(encoding="utf-8")))
        validate_ready_profile(package, "HH1.B"); validate_result_envelope(result, order)
        self.assertIsNone(result["completion_ref"]); self.assertFalse((package / "stage-completion.json").exists())
        self.assertEqual((package.parent / "stage-result.json").read_bytes(), publisher.canonical_bytes(result))

    def test_machine_runtime_contract_and_public_cli(self):
        fixture, work, order, _, draft, _ = self.build();contract=json.loads((B.SKILL_ROOT/"references/runtime-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["required_allowlist_roles_ordered"],list(B.REQUIRED_ROLES));self.assertEqual(contract["public_entrypoint"]["argv"][1],"scripts/run_skill.py");self.assertEqual(len(B.impl_hash()),64)
        completed=subprocess.run([sys.executable,str(B.SKILL_ROOT/"scripts/run_skill.py"),str(work),str(draft)],capture_output=True,text=True,timeout=60)
        self.assertEqual((completed.returncode,completed.stderr),(0,""));self.assertTrue((fixture.workspace/order["output_directory"]/B.SPEC.canonical_name).is_file())

    def test_deterministic_across_independent_workspaces(self):
        outputs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp:
                fixture, work, order, _, draft, _ = fx.build_b(Path(temp)); self.assertEqual(B.execute(work, draft)[0], 0)
                outputs.append(tree(fixture.workspace / order["output_directory"]))
        self.assertEqual(outputs[0], outputs[1])

    def test_material_report_failure_maps_to_upstream_blocked(self):
        fixture, work, order, _, draft, review = self.build("fail");self.assertEqual((review["verdict"],review["defect_origin"],review["coverage_fidelity"]["verdict"]),("fail","upstream_content","fail"));self.assertTrue(review["material_drift_findings"])
        code, result = B.execute(work, draft); package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["blocker_class"]), (2, "blocked", "upstream_defect"))
        self.assertFalse((package / B.SPEC.canonical_name).exists())

    def test_preference_cannot_be_promoted_to_hard_failure(self):
        fixture, work, order, _, draft, review = self.build()
        eid = review["fact_fidelity"]["report_element_ids"][0]
        review["cognitive_overload_findings"] = [{"overload_type":"jargon","affected_report_element_ids":[eid],"evidence":"A reviewer dislikes the wording.","decision_impact":"No retrieval or budget failure is demonstrated."}]
        write(draft / "canonical.json", review)
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / B.SPEC.canonical_name).exists())

    def test_false_pass_with_material_finding_is_local_revise(self):
        fixture, work, order, _, draft, review = self.build()
        eid = review["fact_fidelity"]["report_element_ids"][0]; source=review["fact_fidelity"]["source_ids"][0]; locator=review["fact_fidelity"]["locators"][0]
        review["material_drift_findings"] = [{"drift_type":"omission","affected_report_element_ids":[eid],"source_ids":[source],"hp1_locators":[locator],"report_evidence":"A required control is absent.","material_impact":"Approval would miss a fixed boundary.","requested_correction":"Restore the bound control."}]
        write(draft / "canonical.json", review)
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / B.SPEC.canonical_name).exists())

    def test_actual_read_drift_is_local_revise(self):
        fixture, work, order, _, draft, _ = self.build()
        session = json.loads((draft / "review-session.json").read_text(encoding="utf-8")); session["actual_read_refs"] = session["actual_read_refs"][:-1]; write(draft / "review-session.json", session)
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / B.SPEC.canonical_name).exists())

    def test_unbound_dimension_evidence_is_local_revise(self):
        fixture, work, order, _, draft, review = self.build()
        review["fact_fidelity"]["locators"] = ["canonical-models/ghost.json#/never"]
        write(draft / "canonical.json", review)
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / B.SPEC.canonical_name).exists())

    def test_extra_draft_member_is_local_revise(self):
        fixture, work, order, _, draft, _ = self.build(); (draft / "rendered.html").write_text("<p>forbidden</p>", encoding="utf-8")
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / B.SPEC.canonical_name).exists())

    def test_extra_html_input_role_fails_hard_admission(self):
        fixture, work, order, gate, draft, _ = self.build(); html=fixture.workspace/"candidate.html";html.write_text("<!doctype html>",encoding="utf-8")
        allow=[*order["file_allowlist"],fx.fref(html,fixture.workspace,"human_review_html")];rewrite_allow(work,gate,allow,fixture.workspace)
        with self.assertRaises(B.InternalCondition): B.execute(work,draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_missing_producer_work_order_fails_hard_admission(self):
        fixture, work, order, gate, draft, _ = self.build();allow=[x for x in order["file_allowlist"] if x["role"]!="hh1_a_work_order"];rewrite_allow(work,gate,allow,fixture.workspace)
        with self.assertRaises(B.InternalCondition): B.execute(work,draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_stale_allowlist_hash_fails_before_review(self):
        fixture, work, order, gate, draft, _ = self.build();allow=copy.deepcopy(order["file_allowlist"]);allow[0]["sha256"]="0"*64;rewrite_allow(work,gate,allow,fixture.workspace)
        with self.assertRaises(Exception): B.execute(work,draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_report_tamper_with_updated_allowlist_is_blocked_by_a_manifest(self):
        fixture, work, order, gate, draft, _ = self.build();report=fixture.workspace/"internal/HH1-A/package/hld-human-review-report.json";value=json.loads(report.read_text(encoding="utf-8"));value["title_and_decision_scope"][0]["conclusion"]="tampered";write(report,value)
        allow=copy.deepcopy(order["file_allowlist"])
        for item in allow:
            if item["role"]=="human_review_report":item["sha256"]=publisher.sha256(report)
        rewrite_allow(work,gate,allow,fixture.workspace)
        code,result=B.execute(work,draft);package=fixture.workspace/order["output_directory"]
        self.assertEqual((code,result["result"],result["blocker_class"]),(2,"blocked","upstream_defect"));self.assertFalse((package/B.SPEC.canonical_name).exists())

    def test_partial_fact_coverage_cannot_claim_pass(self):
        fixture, work, order, _, draft, review = self.build()
        self.assertGreater(len(review["fact_fidelity"]["report_element_ids"]), 1)
        review["fact_fidelity"]["report_element_ids"] = review["fact_fidelity"]["report_element_ids"][:-1]
        write(draft / "canonical.json", review)
        code, result = B.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_resealed_cross_domain_misattribution_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):
            target=report["overall_narrative_architecture"][0];other=report["character_arc_placement"][0]["source_ids"][0];old=target["source_ids"][0];target["source_ids"][0]=other
            for item in report["source_bindings"]:
                if item["report_element_id"]==target["id"] and item["source_id"]==old:item["source_id"]=other
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertNotEqual(report["overall_narrative_architecture"][0]["source_ids"][0],report["character_arc_placement"][0]["locators"][0])
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"],result["blocker_class"]),(2,"blocked","upstream_defect"))

    def test_resealed_unpaired_source_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):report["overall_narrative_architecture"][0]["source_ids"].append(report["character_arc_placement"][0]["source_ids"][0])
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertNotEqual(len(report["overall_narrative_architecture"][0]["source_ids"]),len(report["overall_narrative_architecture"][0]["locators"]))
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_resealed_fake_visual_node_source_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):report["visual_models"][0]["nodes"][0]["source_ids"][0]=report["character_arc_placement"][0]["source_ids"][0]
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertTrue(report["visual_models"][0]["nodes"])
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_resealed_dangling_visual_edge_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):report["visual_models"][0]["edges"][0]["to"]="MISSING-NODE"
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertEqual(report["visual_models"][0]["edges"][0]["to"],"MISSING-NODE")
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_report_without_visuals_can_seal_exact_empty_visual_evidence(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):
            visual_ids={item["id"] for item in report["visual_models"]};report["visual_models"]=[]
            report["source_bindings"]=[item for item in report["source_bindings"] if item["report_element_id"] not in visual_ids]
            report["review_budget"].update(B._budget(report))
        report=reseal_a_report(fixture,work,gate,draft,mutate)
        context=B.load_context(work,B.SPEC,B.impl_hash(),B._catalog());_,_,report,producer=B.admit(context)
        review=json.loads((draft/"canonical.json").read_text(encoding="utf-8"));binding_index=producer["binding_index"]
        elements=B._all_elements(report);all_ids={item["id"] for item in elements}
        relation_sections=("overall_narrative_architecture","world_environment_definitions","character_definitions","environment_definitions","storyline_choreography","character_arc_placement","time_space_pacing_tension","key_scene_functions","chapter_definitions")
        dimension_ids={"fact_fidelity":all_ids,"coverage_fidelity":all_ids,"structure_and_relation_fidelity":{item["id"] for section in relation_sections for item in report[section]},"authority_and_open_item_fidelity":{item["id"] for item in report["open_items_constraints_and_lld_boundary"]},"visual_data_fidelity":set()}
        for name,ids in dimension_ids.items():
            sources,locators=B._evidence_for(report,binding_index,ids);review[name]["report_element_ids"]=sorted(ids);review[name]["source_ids"]=sorted(sources);review[name]["locators"]=sorted(locators)
        for item in review["decision_retrieval_tests"]:
            ids={entry["id"] for entry in report[B.QUESTION_SECTIONS[item["question_code"]]]};sources,locators=B._evidence_for(report,binding_index,ids);item["report_element_ids"]=sorted(ids);item["source_ids"]=sorted(sources);item["locators"]=sorted(locators)
        review["reading_budget_validation"]["declared"]=B._budget(report);review["reading_budget_validation"]["recomputed"]=B._budget(report);write(draft/"canonical.json",review)
        code,result=B.execute(work,draft)
        self.assertEqual((code,result["result"],review["visual_data_fidelity"]["source_ids"]),(0,"ready",[]))

    def test_resealed_title_only_coverage_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):
            moved=report["overall_narrative_architecture"].pop();report["title_and_decision_scope"].append(moved);report["source_bindings"]=[{"report_element_id":item["id"],"source_id":source,"locator":locator} for item in fx.A._all_elements(report) for source,locator in zip(item["source_ids"],item["locators"])]
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertGreater(len(report["title_and_decision_scope"]),1)
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_resealed_missing_character_definition_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):
            victim=report["character_definitions"].pop();report["source_bindings"]=[item for item in report["source_bindings"] if item["report_element_id"]!=victim["id"]]
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertEqual(report["character_definitions"],[])
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_definition_card_accepts_same_entity_current_model_supplement_without_moving_primary_domain(self):
        path="canonical-models/character-arc-placement.json";locator=f"{path}#/character_participation_register/0"
        card={"id":"HRE-CHAR-01","element_kind":"character_definition","source_ids":["CHR-01","HAS-PARTICIPATION-01"],"locators":["novel-hld-package.json#/baseline_controls/0",locator]}
        report={"character_definitions":[card],"environment_definitions":[]};binding_index={("HAS-PARTICIPATION-01",locator):{"model_path":path,"locator":"/character_participation_register/0"}};documents={path:{"character_participation_register":[{"source_refs":["CHR-01"]}]}}
        B._validate_definition_supplements(report,binding_index,documents)
        self.assertEqual(B._primary_locators(card),["novel-hld-package.json#/baseline_controls/0"])

    def test_definition_card_rejects_unrelated_current_model_supplement(self):
        path="canonical-models/character-arc-placement.json";locator=f"{path}#/character_participation_register/0"
        report={"character_definitions":[{"id":"HRE-CHAR-01","source_ids":["CHR-01","HAS-PARTICIPATION-02"],"locators":["novel-hld-package.json#/baseline_controls/0",locator]}],"environment_definitions":[]};binding_index={("HAS-PARTICIPATION-02",locator):{"model_path":path,"locator":"/character_participation_register/0"}};documents={path:{"character_participation_register":[{"source_refs":["CHR-02"]}]}}
        with self.assertRaises(B.InternalCondition) as raised:B._validate_definition_supplements(report,binding_index,documents)
        self.assertEqual(raised.exception.code,"HH1B_DEFINITION_SUPPLEMENT_INVALID")

    def test_resealed_missing_world_environment_scope_is_blocked(self):
        fixture, work, order, gate, draft, _ = self.build()
        def mutate(report):
            victim=report["world_environment_definitions"].pop();report["source_bindings"]=[item for item in report["source_bindings"] if item["report_element_id"]!=victim["id"]]
        report=reseal_a_report(fixture,work,gate,draft,mutate);self.assertEqual(len(report["world_environment_definitions"]),4)
        code,result=B.execute(work,draft);self.assertEqual((code,result["result"]),(2,"blocked"))

    def test_post_admission_runtime_failure_is_durable(self):
        fixture, work, order, _, draft, _ = self.build();missing=draft.parent/"missing-review-draft"
        code,result=B.execute(work,missing);package=fixture.workspace/order["output_directory"]
        self.assertEqual((code,result["result"]),(1,"runtime_error"));self.assertTrue((package/"runtime-error.json").is_file());self.assertFalse((package/B.SPEC.canonical_name).exists())


if __name__ == "__main__":
    unittest.main()
