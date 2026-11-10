from __future__ import annotations

import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_agentic_acceptance import HARNESS_CASES, _bounded_case_owners, validate

N = int("e45be111d0665e90792cbe3aed774f09a1048119f56b107b24b706df1e7ee9774d97a1c0567a09f1c5d3438ff925bdda0613fe6b1f2bbf292fcb94407231e9d1e148f5c9a06254219ab4a0721ee11a509fff5908947e52c7a385ea2dccb3ea3d56fbce06947767b0ec63e8ab69e8b77e11b59f6202a63984dc935b5b79f279ec685850391924b7fee53e0471e38a6d969f86ce45be622557711ac6ae3111c94d184c5e78c3a147a39c86ab22341a6d7c1d02e7f9b0b29ed11ed3dc28310e8447e9f78d0398f12791a68e961278a422e0ba5b9d2f48c4b311f7bf32de47001b2e3ec957e2053a41fa186930851b8de2f8d035991a3a0aecc557337e534f792289", 16)
D = int("347a63def0e63199a06b369d3aa8a62677951e290dc3e8b1eff64ab3382220bb6cbea9aa9684eda79cd767c99c8f3e91adbf67028d938356eef7a90e655fd094cda1b3703e361290f569488ce949403fa2812f2000660656801efc79c176e01ff00f2661cf3920806156b567bd0b40adcd5a9071d8db83d0e352ced6171070d182e2622f18265bd0f583002d52abfb488a912732dc47e24d35b0baa20bfb6862eb52384626dd5a86e3d9f1337cc79912871b6e96926fe7d15ffade6971110f16151fa93da7d76a657429b0093f8a583e2664cf976472d6d81ba6eb6cac8d354531f02fa1b24ebf20e110c261d9465eb0a8173579870550153c96c1202752f65d", 16)
E = 65537
PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
ZERO = "0" * 64
RUN = "qualification-run-001"
HLD_RUN = "hld-duanxian-qualification"
STAMP = "2026-08-06T00:00:00+08:00"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class AgenticQualificationTests(unittest.TestCase):
    def _write(self, root: Path, name: str, value: object, role: str = "evidence") -> dict[str, str]:
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        content = (canonical(value) + b"\n") if not isinstance(value, str) else value.encode("utf-8")
        path.write_bytes(content)
        return {"role": role, "path": name, "sha256": hashlib.sha256(content).hexdigest()}

    def _receipt(self, root: Path, case_id: str, role: str, task_id: str, context_id: str, transcript: dict[str, str]) -> dict[str, str]:
        value = {"schema_version":"1.0","harness":"novel-hld-autonomous","harness_version":"0.1.0","qualification_run_id":RUN,"case_id":case_id,"task_id":task_id,"task_role":role,"runtime":"codex","context_id":context_id,"fresh_context":True,"status":"completed","transcript_ref":transcript,"started_at":STAMP,"completed_at":STAMP}
        return self._write(root, f"receipts/{case_id}-{role}.json", value, f"{role}_task_receipt")

    def _trust_anchor(self, base: Path) -> Path:
        material = {"algorithm":"rsa-pkcs1v15-sha256","exponent":E,"modulus_hex":format(N, "x")}
        anchor = {"schema_version":"1.0","harness":"novel-hld-autonomous","status":"configured",**material,"key_id":hashlib.sha256(canonical(material)).hexdigest()}
        path = base / "trust-anchor.json"; path.write_bytes(canonical(anchor) + b"\n")
        return path

    def _sign(self, message: bytes) -> str:
        size = (N.bit_length() + 7) // 8
        digest_info = PREFIX + hashlib.sha256(message).digest()
        encoded = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
        return pow(int.from_bytes(encoded, "big"), D, N).to_bytes(size, "big").hex()

    def _plain_ref(self) -> dict[str, str]:
        return {"role":"fixture","path":"reference/source.json","sha256":ZERO}

    def _reference_run(self, root: Path) -> dict[str, object]:
        source = self._write(root, "reference/source.json", {"source":True}, "source")
        authority = {"source_classifications":{"mandatory":[],"freedom":[],"must_ask":[],"open":[]},"source_open_items":[],"source_authority_classes":{"author_locked":[],"autonomous_owned":[],"downstream_freedom":[],"author_open":[]},"hld_ownership":{"source_projection":[],"hld_owned":[],"preserved_open":[],"lld_freedom":[]}}
        control = {"source_id":"INT-X","classification":"mandatory","open_item":False,"authority_class":"author_locked","domain":"intent","source":{},"workspace_source_ref":source,"locator":"/x","source_text":"x","source_value_sha256":ZERO,"hld_instruction":"preserve x","preserve_unresolved":False}
        baseline_doc = {"schema_version":"1.0","skill":"novel-hld-baseline-admitter","stage":"HB0","hld_run_id":HLD_RUN,"status":"ready","source_baseline":source,"source_release":{},"lineage":{},"admission_verdicts":[f"v{i}" for i in range(8)],"authority_partition":authority,"control_registry":[control],"unresolved_register":[],"hld_assignment":{},"change_policy":{},"prohibitions":["p1","p2","p3","p4"],"source_access_policy":"SOURCE_ACCESS_MATRIX@1.0"}
        baseline = self._write(root, "reference/hld-control-baseline.json", baseline_doc, "baseline")

        stages = ["HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1","HQ1"]
        models = ["HA1","HS1","HC1","HI1","HR1","HK1","HD1"]
        hp1_doc = {"schema_version":"1.0","skill":"novel-hld-package-assembler","stage":"HP1","hld_run_id":HLD_RUN,"status":"ready","stage_references":[{"stage":stage,"completion_sha256":ZERO,"manifest_sha256":ZERO,"validation_sha256":ZERO} for stage in stages],"canonical_models":[{"stage":stage,"path":f"canonical-models/{stage}.json","sha256":ZERO} for stage in models],"semantic_review":{"path":"semantic.json","sha256":ZERO},"authority_partition":authority,"baseline_controls":[{"source_id":"INT-X","domain":"intent","classification":"mandatory","open_item":False,"authority_class":"author_locked","source_value_sha256":ZERO}],"open_items":[],"hld_decisions":[{"stage":stage,"model_path":f"canonical-models/{stage}.json","locator":"/design_decisions","value_sha256":ZERO,"count":1} for stage in models],"unresolved_dependency_summary":[],"package_profile":["ready"]}
        hp1 = self._write(root, "reference/novel-hld-package.json", hp1_doc, "hp1_package")
        any_ref = self._plain_ref()
        hq2_doc = {"schema_version":"1.0","harness":"novel-hld-autonomous","stage":"HQ2","hld_run_id":HLD_RUN,"revision":0,"status":"ready","consumer_test_ref":any_ref,"consumer_manifest_ref":any_ref,"consumer_result_ref":any_ref,"fidelity_test_ref":any_ref,"fidelity_manifest_ref":any_ref,"fidelity_result_ref":any_ref,"hp1_completion_ref":any_ref,"hb0_completion_ref":any_ref}
        hq2 = self._write(root, "reference/lld-handoff-acceptance.json", hq2_doc, "hq2_acceptance")
        hre = {"id":"HRE-X","element_kind":"conclusion","conclusion":"x","source_ids":["INT-X"],"locators":["/x"],"visual_role":"summary","review_question":"Is x correct?"}
        character = {**hre, "element_kind":"character_definition", "name":"林岚", "story_position":"她负责推动调查作出选择。", "personality_and_motivation":"谨慎，但不愿牺牲无辜者。", "capabilities_and_limits":"擅长核对证据，不能越过授权操控系统。", "relationships_and_change":"她在合作中学会承担信任的风险。"}
        environment = {**hre, "element_kind":"environment_definition", "name":"封闭调查室", "story_function":"迫使人物在有限信息下决定。", "physical_character":"冷白灯与持续运转的记录设备形成压迫感。", "access_and_limits":"只有当班调查员可以进入。", "dramatic_use":"隔离让迟疑与冲突无法被外界打断。"}
        world=importlib.import_module("harnesses.novel-hld-autonomous.tests.test_composite_publisher").minimal_world_environment_definitions()
        report_doc = {"schema_version":"1.0","skill":"novel-hld-review-report-assembler","stage":"HH1","hld_run_id":HLD_RUN,"revision":0,"status":"ready","hp1_content_binding":{"package_sha256":hp1["sha256"],"completion_sha256":ZERO},"hq2_gate_binding":{"acceptance_sha256":hq2["sha256"],"bound_hp1_package_sha256":hp1["sha256"]},"title_and_decision_scope":[hre],"overall_narrative_architecture":[hre],"world_environment_definitions":world,"character_definitions":[character],"environment_definitions":[environment],"storyline_choreography":[hre],"character_arc_placement":[hre],"pov_information_suspense":[hre],"time_space_pacing_tension":[hre],"key_scene_functions":[hre],"chapter_definitions":[hre],"open_items_constraints_and_lld_boundary":[hre],"visual_models":[],"source_bindings":[{"report_element_id":"HRE-X","source_id":"INT-X","locator":"/x"}],"review_budget":{"cjk_characters":1,"latin_words":1,"visual_count":0,"formula":"CJK/500 + Latin/250 + visuals*0.25","estimated_read_minutes":0.01}}
        report = self._write(root, "reference/hld-human-review-report.json", report_doc, "human_review_report")
        registry_doc = {"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":HLD_RUN,"stage":"HH1","skill":"novel-hld-html-renderer","report_ref":report,"fidelity_review_ref":any_ref,"renderer_binding":{"implementation_sha256":ZERO,"template_sha256":ZERO,"stylesheet_sha256":ZERO,"report_schema_sha256":ZERO,"fidelity_schema_sha256":ZERO},"targets":[{"id":"HUI-HRE-X-report_element-0","dom_locator":"#x","render_role":"report_element","source_visual_role":"summary","report_element_id":"HRE-X","report_element_kind":"conclusion","visual_model_id":None,"content_sha256":ZERO}]}
        registry = self._write(root, "reference/render-target-registry.json", registry_doc, "render_target_registry")
        html = self._write(root, "reference/human-review-report.html", "<!doctype html><html><head><title>断线 HLD</title></head><body id='x'>x</body></html>\n", "human_review_html")
        manifest_doc = {"schema_version":"1.0","harness":"novel-hld-autonomous","hld_run_id":HLD_RUN,"revision":0,"stage":"HH1","skill":"novel-hld-human-review-composite","status":"ready","files":[{"role":"human_review_report","path":"hld-human-review-report.json","sha256":report["sha256"]},{"role":"render_target_registry","path":"render-target-registry.json","sha256":registry["sha256"]},{"role":"human_review_html","path":"human-review-report.html","sha256":html["sha256"]}],"artifact_roles":{"human_review_report":{"role":"human_review_report","path":"hld-human-review-report.json","sha256":report["sha256"]},"render_target_registry":{"role":"render_target_registry","path":"render-target-registry.json","sha256":registry["sha256"]},"human_review_html":{"role":"human_review_html","path":"human-review-report.html","sha256":html["sha256"]}}}
        manifest = self._write(root, "reference/package-manifest.json", manifest_doc, "hh1_manifest")
        decision_doc = {"schema_version":"1.0","hld_run_id":HLD_RUN,"revision":0,"event_sequence":1,"event_id":"AUTHOR-001","external":True,"current":True,"consumed":False,"decision":"approved","author_text":"approved","bindings":{"hp1_package_sha256":hp1["sha256"],"hq2_acceptance_sha256":hq2["sha256"],"hh1_manifest_sha256":manifest["sha256"],"html_sha256":html["sha256"]},"revision_targets":[]}
        decision = self._write(root, "reference/author-decision.json", decision_doc, "author_decision")
        final_validation = self._write(root, "reference/final-validation.json", {"status":"pass"}, "final_validation")
        chain = [{"stage":stage,"completion_path":f"{stage}/stage-completion.json","completion_sha256":ZERO,"manifest_path":f"{stage}/package-manifest.json","manifest_sha256":ZERO} for stage in ["HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1","HQ1","HP1","HQ2","HH1"]]
        completion_doc = {"schema_version":"1.0","harness":"novel-hld-autonomous","stage":"HF1","skill":"novel-hld-finalizer","hld_run_id":HLD_RUN,"revision":0,"status":"approved_ready","produced_at":STAMP,"stage_chain":chain,"author_decision_ref":decision,"hp1_package_ref":hp1,"hq2_acceptance_ref":hq2,"hh1_manifest_ref":manifest,"html_ref":html,"lld_handoff_ref":any_ref,"final_validation_ref":final_validation,"lld_admission":{"authorized":True,"handoff_ref":any_ref,"hp1_completion_sha256":ZERO,"hq2_completion_sha256":ZERO,"hh1_completion_sha256":ZERO},"next_stage":"novel-lld"}
        completion = self._write(root, "reference/hld-completion.json", completion_doc, "hld_completion")
        review = self._write(root, "reference/semantic-review.json", {"project_id":"duanxian","hld_run_id":HLD_RUN,"reviewer_task_id":"reference-reviewer","verdict":"pass"}, "semantic_review")
        producer_transcript = self._write(root, "reference/producer-transcript.txt", "reference producer transcript\n", "producer_transcript")
        reviewer_transcript = self._write(root, "reference/reviewer-transcript.txt", "reference reviewer transcript\n", "reviewer_transcript")
        producer_receipt = self._receipt(root, "DUANXIAN-REFERENCE", "producer", "reference-producer", "context-reference-producer", producer_transcript)
        reviewer_receipt = self._receipt(root, "DUANXIAN-REFERENCE", "reviewer", "reference-reviewer", "context-reference-reviewer", reviewer_transcript)
        return {"project_id":"duanxian","hld_run_id":HLD_RUN,"revision":0,"producer_task_id":"reference-producer","reviewer_task_id":"reference-reviewer","producer_task_receipt_ref":producer_receipt,"reviewer_task_receipt_ref":reviewer_receipt,"baseline_ref":baseline,"hld_completion_ref":completion,"hp1_package_ref":hp1,"hq2_acceptance_ref":hq2,"hh1_manifest_ref":manifest,"human_review_report_ref":report,"render_registry_ref":registry,"html_ref":html,"author_decision_ref":decision,"semantic_review_ref":review,"verdict":"pass"}

    def _acceptance(self, root: Path, *, same_identity: bool = False, alias_reference: bool = False) -> tuple[Path, Path]:
        bounded_dimensions = ("scope_fidelity","input_gate_obedience","output_contract_correctness","semantic_or_deterministic_correctness","boundary_discipline","parent_consumability")
        harness_dimensions = ("scope_fidelity","workflow_rigor","skill_type_correctness","adapter_faithfulness","validation_hardness","semantic_acceptance","release_portability")
        groups = []; owners = _bounded_case_owners()
        for layer, cases, dimensions in (("bounded_skill", sorted(owners), bounded_dimensions), ("harness", sorted(HARNESS_CASES), harness_dimensions)):
            refs = []
            for case_id in cases:
                fixture = self._write(root, f"cases/{case_id}/fixture.json", {"sealed":True}, "fixture")
                fixture_manifest = self._write(root, f"cases/{case_id}/fixture-manifest.json", {"status":"sealed"}, "fixture_manifest")
                prompt = self._write(root, f"cases/{case_id}/prompt.md", "Execute the declared case.\n", "prompt")
                instruction = self._write(root, f"cases/{case_id}/instruction.md", "Follow the owner contract.\n", "instruction")
                producer_transcript = self._write(root, f"cases/{case_id}/producer.txt", f"producer transcript {case_id}\n", "producer_transcript")
                reviewer_transcript = self._write(root, f"cases/{case_id}/reviewer.txt", f"reviewer transcript {case_id}\n", "reviewer_transcript")
                artifact = self._write(root, f"cases/{case_id}/artifact.json", {"status":"ready","case_id":case_id}, "artifact")
                deterministic = self._write(root, f"cases/{case_id}/validation.json", {"status":"pass"}, "validation")
                producer = f"producer-{case_id}"; reviewer = producer if same_identity and not refs and layer == "bounded_skill" else f"reviewer-{case_id}"
                producer_receipt = self._receipt(root, case_id, "producer", producer, f"context-{producer}", producer_transcript)
                reviewer_receipt = self._receipt(root, case_id, "reviewer", reviewer, f"context-{reviewer}", reviewer_transcript)
                review = self._write(root, f"cases/{case_id}/semantic-review.json", {"case_id":case_id,"reviewer_task_id":reviewer,"verdict":"pass"}, "semantic_review")
                result = {"schema_version":"1.0","harness":"novel-hld-autonomous","harness_version":"0.1.0","qualification_run_id":RUN,"case_id":case_id,"layer":layer,"target_stage":owners[case_id][0] if layer == "bounded_skill" else "HLD-E2E","target_skill":owners[case_id][1] if layer == "bounded_skill" else None,"fixture_ref":fixture,"fixture_manifest_ref":fixture_manifest,"prompt_ref":prompt,"instruction_refs":[instruction],"producer_task_id":producer,"reviewer_task_id":reviewer,"producer_task_receipt_ref":producer_receipt,"reviewer_task_receipt_ref":reviewer_receipt,"producer_transcript_ref":producer_transcript,"reviewer_transcript_ref":reviewer_transcript,"fresh_context":True,"prior_conclusions_exposed":False,"expected_answer_exposed":False,"allowed_read_refs":[fixture],"actual_read_refs":[fixture],"produced_artifact_refs":[artifact],"deterministic_validation_refs":[deterministic],"semantic_review_ref":review,"dimensions":[{"dimension":dimension,"score":2,"evidence_refs":[artifact]} for dimension in dimensions],"blockers":[],"verdict":"pass","completed_at":STAMP}
                refs.append(self._write(root, f"results/{case_id}.json", result, "case_result"))
            groups.append(refs)
        reference = self._reference_run(root)
        if alias_reference:
            reference["hld_completion_ref"] = reference["baseline_ref"]
        acceptance = {"schema_version":"1.0","harness":"novel-hld-autonomous","harness_version":"0.1.0","qualification_run_id":RUN,"status":"qualified","bounded_case_results":groups[0],"harness_case_results":groups[1],"reference_run":reference,"created_at":STAMP}
        trust = self._trust_anchor(root.parent)
        anchor = json.loads(trust.read_text(encoding="utf-8"))
        acceptance_sha = hashlib.sha256(canonical(acceptance)).hexdigest()
        attestation = {"schema_version":"1.0","harness":"novel-hld-autonomous","harness_version":"0.1.0","qualification_run_id":RUN,"controller_id":"qualification-controller-test","key_id":anchor["key_id"],"algorithm":"rsa-pkcs1v15-sha256","acceptance_payload_sha256":acceptance_sha,"claims":{"runtime_task_receipts_verified":True,"fresh_contexts_verified":True,"sealed_allowlists_verified":True,"transcripts_verified":True,"reference_artifacts_schema_validated":True},"signed_at":STAMP}
        attestation["signature_hex"] = self._sign(canonical(attestation))
        acceptance["attestation_ref"] = self._write(root, "qualification-attestation.json", attestation, "qualification_attestation")
        path = root / "agentic-acceptance.json"; path.write_bytes(canonical(acceptance) + b"\n")
        return path, trust

    def test_signed_closed_evidence_package_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "evidence"; root.mkdir()
            acceptance, trust = self._acceptance(root)
            self.assertEqual(validate(acceptance, trust), [])

    def test_same_task_cannot_produce_and_review(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "evidence"; root.mkdir()
            acceptance, trust = self._acceptance(root, same_identity=True)
            errors = validate(acceptance, trust)
            self.assertTrue(any("must be independent" in error for error in errors), errors)

    def test_unconfigured_packaged_anchor_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "evidence"; root.mkdir()
            acceptance, _ = self._acceptance(root)
            errors = validate(acceptance)
            self.assertTrue(any("not configured" in error for error in errors), errors)

    def test_reference_roles_cannot_alias_one_generic_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "evidence"; root.mkdir()
            acceptance, trust = self._acceptance(root, alias_reference=True)
            errors = validate(acceptance, trust)
            self.assertTrue(any("distinct files" in error for error in errors), errors)

    def test_missing_acceptance_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            errors = validate(Path(raw) / "missing.json")
            self.assertTrue(any("missing" in error for error in errors), errors)


if __name__ == "__main__": unittest.main()
