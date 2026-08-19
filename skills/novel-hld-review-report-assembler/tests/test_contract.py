from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import public_fixture as fx  # noqa: E402

A = fx.A
publisher = fx.publisher
from runtime.package_envelope import validate_manifest, validate_ready_profile, validate_result_envelope  # noqa: E402


def write(path: Path, value: object) -> None:
    fx.write_json(path, value)


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def rewrite_allow(work_path: Path, gate_path: Path, allow: list[dict], workspace: Path) -> dict:
    work = json.loads(work_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    work["file_allowlist"] = allow
    gate["file_allowlist"] = allow
    write(gate_path, gate)
    work["input_gate_ref"] = fx.fref(gate_path, workspace, "input_gate")
    write(work_path, work)
    return work


class HH1APublicRuntimeTests(unittest.TestCase):
    def build(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        return fx.build_a(Path(self.temp.name))

    def test_ready_public_profile_and_envelope(self):
        fixture, work, order, _, draft, _ = self.build()
        code, result = A.execute(work, draft)
        package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["result_scope"]), (0, "ready", "composite_internal"))
        validate_manifest(package, json.loads((package / "package-manifest.json").read_text(encoding="utf-8")))
        validate_ready_profile(package, "HH1.A")
        validate_result_envelope(result, order)
        self.assertIsNone(result["completion_ref"])
        self.assertFalse((package / "stage-completion.json").exists())
        self.assertEqual((package.parent / "stage-result.json").read_bytes(), publisher.canonical_bytes(result))

    def test_exact_sealed_upstreams_may_precede_hh1_revision(self):
        fixture, work, order, _, draft, report = self.build()
        current_work = json.loads(work.read_text(encoding="utf-8"))
        current_work["revision"] = 2
        write(work, current_work)
        report["revision"] = 2
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["revision"]), (0, "ready", 2))
        self.assertEqual(json.loads((fixture.workspace / "HP1-package/stage-completion.json").read_text(encoding="utf-8"))["revision"], 1)
        self.assertEqual(json.loads((fixture.workspace / "HQ2-package/lld-handoff-acceptance.json").read_text(encoding="utf-8"))["revision"], 1)
        self.assertTrue((package / A.SPEC.canonical_name).is_file())

    def test_machine_runtime_contract_and_public_cli(self):
        fixture, work, order, _, draft, _ = self.build(); contract=json.loads((A.SKILL_ROOT/"references/runtime-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["required_allowlist_roles_ordered"],list(A.REQUIRED_ROLES));self.assertEqual(contract["public_entrypoint"]["argv"][1],"scripts/run_skill.py");self.assertEqual(len(A.impl_hash()),64)
        completed=subprocess.run([sys.executable,str(A.SKILL_ROOT/"scripts/run_skill.py"),str(work),str(draft)],capture_output=True,text=True,timeout=60)
        self.assertEqual((completed.returncode,completed.stderr),(0,""));self.assertTrue((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).is_file())

    def test_deterministic_across_independent_workspaces(self):
        outputs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp:
                fixture, work, order, _, draft, _ = fx.build_a(Path(temp))
                self.assertEqual(A.execute(work, draft)[0], 0)
                outputs.append(tree(fixture.workspace / order["output_directory"]))
        self.assertEqual(outputs[0], outputs[1])

    def test_material_omission_is_local_revise_without_canonical(self):
        fixture, work, order, _, draft, report = self.build()
        victim = report["overall_narrative_architecture"].pop()
        report["source_bindings"] = [x for x in report["source_bindings"] if x["report_element_id"] != victim["id"]]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["revision_class"]), (2, "revise", "local_candidate"))
        self.assertFalse((package / A.SPEC.canonical_name).exists())

    def test_missing_character_definition_is_local_revise_without_canonical(self):
        fixture, work, order, _, draft, report = self.build()
        victim = report["character_definitions"].pop()
        report["source_bindings"] = [item for item in report["source_bindings"] if item["report_element_id"] != victim["id"]]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_missing_environment_definition_is_local_revise_without_canonical(self):
        fixture, work, order, _, draft, report = self.build()
        victim = report["environment_definitions"].pop()
        report["source_bindings"] = [item for item in report["source_bindings"] if item["report_element_id"] != victim["id"]]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_definition_entity_sets_come_from_hc1_and_hk1_not_domain_wide_controls(self):
        fixture, _, _, _, _, report = self.build()
        ws = fixture.workspace
        hc1 = json.loads((ws / "HP1-package/canonical-models/character-arc-placement.json").read_text(encoding="utf-8"))
        hk1 = json.loads((ws / "HP1-package/canonical-models/key-scene-function-map.json").read_text(encoding="utf-8"))
        expected_characters = {item["character_id"] for item in hc1["character_participation_register"]}
        expected_environments = {value for item in hk1["key_scene_functions"] for value in item["environment_refs"]}
        self.assertEqual({item["source_ids"][0] for item in report["character_definitions"]}, expected_characters)
        self.assertEqual({item["source_ids"][0] for item in report["environment_definitions"]}, expected_environments)
        self.assertFalse(any(source.startswith(("REL-", "DEV-", "CHD-")) for source in expected_characters))
        self.assertFalse(any(source.startswith("ZONE-") for source in expected_environments))

    def test_world_environment_cards_require_exact_five_scopes_and_world_bindings(self):
        fixture, work, order, _, draft, report = self.build()
        self.assertEqual({item["environment_scope"] for item in report["world_environment_definitions"]}, A.WORLD_ENVIRONMENT_SCOPES)
        report["world_environment_definitions"][0]["environment_scope"] = report["world_environment_definitions"][1]["environment_scope"]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_author_language_rejects_machine_logic_before_canonical_output(self):
        fixture,work,order,_,draft,report=self.build()
        report["storyline_choreography"][0]["conclusion"]="顾衡线负责留下证据入口，现实调查线负责闭合行动链。"
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertEqual(json.loads((fixture.workspace/order["output_directory"]/"revision-report.json").read_text(encoding="utf-8"))["code"],"HH1A_AUTHOR_LANGUAGE_INVALID")
        self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_author_language_rejects_ai_memo_vocabulary(self):
        fixture,work,order,_,draft,report=self.build()
        report["storyline_choreography"][0]["conclusion"]="把人物关系投影到叙事链路，并与后续工作流对齐。"
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertEqual(json.loads((fixture.workspace/order["output_directory"]/"revision-report.json").read_text(encoding="utf-8"))["code"],"HH1A_AUTHOR_LANGUAGE_INVALID")

    def test_author_language_rejects_repeated_substantive_copy(self):
        fixture,work,order,_,draft,report=self.build()
        repeated="沈逾必须亲自决定是否继续与眼前这个生命交谈。"
        report["storyline_choreography"][0]["conclusion"]=repeated
        report["character_arc_placement"][0]["conclusion"]=repeated
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertEqual(json.loads((fixture.workspace/order["output_directory"]/"revision-report.json").read_text(encoding="utf-8"))["code"],"HH1A_AUTHOR_LANGUAGE_INVALID")

    def test_world_reader_stories_must_cover_exact_source_entities(self):
        fixture,work,order,_,draft,report=self.build()
        city=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="city_and_region")
        city["city_stories"][0]["city_name"]="A city that is not in the source"
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_world_environment_card_cannot_bind_character_source(self):
        fixture, work, order, _, draft, report = self.build()
        target=report["world_environment_definitions"][0];old_source=target["source_ids"][0];old_locator=target["locators"][0]
        character=report["character_definitions"][0];target["source_ids"][0]=character["source_ids"][0];target["locators"][0]=character["locators"][0]
        for item in report["source_bindings"]:
            if item["report_element_id"]==target["id"] and item["source_id"]==old_source and item["locator"]==old_locator:
                item["source_id"]=target["source_ids"][0];item["locator"]=target["locators"][0]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_world_environment_requires_concrete_city_people_and_season_profiles(self):
        mutations=(
            ("city_and_region","city_network"),
            ("local_people_and_daily_life","ordinary_people_portraits"),
            ("climate_and_physical_environment","season_profile"),
        )
        for scope,key in mutations:
            with self.subTest(scope=scope):
                fixture,work,order,_,draft,report=self.build()
                next(item for item in report["world_environment_definitions"] if item["environment_scope"]==scope).pop(key)
                write(draft/"canonical.json",report)
                code,result=A.execute(work,draft)
                self.assertEqual((code,result["result"]),(2,"revise"))
                self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_required_world_decisions_cannot_be_reopened_as_placeholders(self):
        fixture,work,order,_,draft,report=self.build()
        city=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="city_and_region")
        city["author_open_details"]=["具体城市名称仍由作者决定。"]
        city["city_network"]["cities"][0]["city_name"]="某城市"
        report["review_budget"]=A._budget(report)
        write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_city_network_requires_four_connected_story_cities(self):
        fixture,work,order,_,draft,report=self.build()
        city=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="city_and_region")
        removed=city["city_network"]["cities"].pop()
        city["city_network"]["intercity_links"]=[link for link in city["city_network"]["intercity_links"] if removed["city_name"] not in (link["from_city"],link["to_city"])]
        people=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="local_people_and_daily_life")
        people["ordinary_people_portraits"]=[portrait for portrait in people["ordinary_people_portraits"] if portrait["city"]!=removed["city_name"]]
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_city_network_cannot_drift_from_ha1_machine_authority(self):
        fixture,work,order,_,draft,report=self.build()
        city=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="city_and_region")
        city["city_network"]["cities"][0]["name" if "name" in city["city_network"]["cities"][0] else "city_name"]="Invented City"
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        package=fixture.workspace/order["output_directory"]
        self.assertEqual(json.loads((package/"revision-report.json").read_text(encoding="utf-8"))["code"],"HH1A_WORLD_AUTHORITY_DRIFT")
        self.assertFalse((package/A.SPEC.canonical_name).exists())

    def test_ordinary_people_must_cover_every_defined_city(self):
        fixture,work,order,_,draft,report=self.build()
        people=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="local_people_and_daily_life")
        people["ordinary_people_portraits"][0]["city"]=people["ordinary_people_portraits"][1]["city"]
        report["review_budget"]=A._budget(report);write(draft/"canonical.json",report)
        code,result=A.execute(work,draft)
        self.assertEqual((code,result["result"]),(2,"revise"))
        self.assertFalse((fixture.workspace/order["output_directory"]/A.SPEC.canonical_name).exists())

    def test_unknown_source_id_is_local_revise(self):
        fixture, work, order, _, draft, report = self.build()
        element = report["overall_narrative_architecture"][0]
        old = element["source_ids"][0]
        element["source_ids"][0] = "UNKNOWN-SEALED-ID"
        for item in report["source_bindings"]:
            if item["report_element_id"] == element["id"] and item["source_id"] == old:
                item["source_id"] = "UNKNOWN-SEALED-ID"
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_renderer_owned_id_is_rejected_as_local_draft_defect(self):
        fixture, work, order, _, draft, report = self.build()
        report["title_and_decision_scope"][0]["id"] = "HUI-FORBIDDEN"
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_extra_draft_member_is_local_revise(self):
        fixture, work, order, _, draft, _ = self.build()
        (draft / "sample-chapter.txt").write_text("forbidden prose", encoding="utf-8")
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_actual_read_drift_is_local_revise(self):
        fixture, work, order, _, draft, _ = self.build()
        session = json.loads((draft / "generation-session.json").read_text(encoding="utf-8"))
        session["actual_read_refs"] = session["actual_read_refs"][:-1]
        write(draft / "generation-session.json", session)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))
        self.assertFalse((fixture.workspace / order["output_directory"] / A.SPEC.canonical_name).exists())

    def test_extra_sample_input_role_fails_hard_admission(self):
        fixture, work, order, gate, draft, _ = self.build()
        sample = fixture.workspace / "sample-chapter.md"
        sample.write_text("# prose\n", encoding="utf-8")
        allow = [*order["file_allowlist"], fx.fref(sample, fixture.workspace, "sample_chapter")]
        rewrite_allow(work, gate, allow, fixture.workspace)
        with self.assertRaises(A.InternalCondition):
            A.execute(work, draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_missing_required_role_fails_hard_admission(self):
        fixture, work, order, gate, draft, _ = self.build()
        allow = [x for x in order["file_allowlist"] if x["role"] != "hld_model_hk1"]
        rewrite_allow(work, gate, allow, fixture.workspace)
        with self.assertRaises(A.InternalCondition):
            A.execute(work, draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_stale_allowlist_hash_fails_before_semantic_read(self):
        fixture, work, order, gate, draft, _ = self.build()
        allow = copy.deepcopy(order["file_allowlist"])
        allow[0]["sha256"] = "0" * 64
        rewrite_allow(work, gate, allow, fixture.workspace)
        with self.assertRaises(Exception):
            A.execute(work, draft)
        self.assertFalse((fixture.workspace / order["output_directory"]).exists())

    def test_model_tamper_with_updated_allowlist_is_blocked_by_hp1_manifest(self):
        fixture, work, order, gate, draft, _ = self.build()
        model = fixture.workspace / "HP1-package/canonical-models/narrative-architecture.json"
        value = json.loads(model.read_text(encoding="utf-8")); value["objects"].append({"id": "HNU-TAMPER"}); write(model, value)
        allow = copy.deepcopy(order["file_allowlist"])
        for item in allow:
            if item["role"] == "hld_model_ha1": item["sha256"] = publisher.sha256(model)
        new_order = rewrite_allow(work, gate, allow, fixture.workspace)
        session = json.loads((draft / "generation-session.json").read_text(encoding="utf-8")); session["actual_read_refs"] = new_order["file_allowlist"]; write(draft / "generation-session.json", session)
        code, result = A.execute(work, draft)
        package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"], result["blocker_class"]), (2, "blocked", "upstream_defect"))
        self.assertFalse((package / A.SPEC.canonical_name).exists())

    def test_cross_domain_source_locator_misattribution_is_revise(self):
        fixture, work, order, _, draft, report = self.build()
        target = report["overall_narrative_architecture"][0]
        other = report["character_arc_placement"][0]["source_ids"][0]
        old = target["source_ids"][0]; target["source_ids"][0] = other
        for item in report["source_bindings"]:
            if item["report_element_id"] == target["id"] and item["source_id"] == old: item["source_id"] = other
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_extra_unpaired_source_is_revise(self):
        fixture, work, order, _, draft, report = self.build()
        target = report["overall_narrative_architecture"][0]
        target["source_ids"].append(report["character_arc_placement"][0]["source_ids"][0])
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_fake_visual_node_source_is_revise(self):
        fixture, work, order, _, draft, report = self.build()
        node = report["visual_models"][0]["nodes"][0]
        node["source_ids"][0] = report["character_arc_placement"][0]["source_ids"][0]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_dangling_visual_edge_is_revise(self):
        fixture, work, order, _, draft, report = self.build()
        report["visual_models"][0]["edges"][0]["to"] = "MISSING-NODE"
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_duplicate_source_binding_is_revise(self):
        fixture, work, order, _, draft, report = self.build()
        report["source_bindings"].append(copy.deepcopy(report["source_bindings"][0]))
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_title_reference_cannot_replace_primary_domain_coverage(self):
        fixture, work, order, _, draft, report = self.build()
        moved = report["overall_narrative_architecture"].pop()
        report["title_and_decision_scope"].append(moved)
        report["source_bindings"] = [{"report_element_id":item["id"],"source_id":source,"locator":locator} for item in A._all_elements(report) for source,locator in zip(item["source_ids"],item["locators"])]
        write(draft / "canonical.json", report)
        code, result = A.execute(work, draft)
        self.assertEqual((code, result["result"]), (2, "revise"))

    def test_post_admission_runtime_failure_is_durable_and_has_no_canonical(self):
        fixture, work, order, _, draft, _ = self.build()
        missing = draft.parent / "missing-draft"
        code, result = A.execute(work, missing); package = fixture.workspace / order["output_directory"]
        self.assertEqual((code, result["result"]), (1, "runtime_error"))
        self.assertTrue((package / "runtime-error.json").is_file())
        self.assertFalse((package / A.SPEC.canonical_name).exists())


if __name__ == "__main__":
    unittest.main()
