from __future__ import annotations

import importlib
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import hp1_runtime as hp1  # noqa: E402

hb0_test = importlib.import_module("skills.novel-hld-baseline-admitter.tests.test_hb0_runtime")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(hp1.canonical_bytes(value))


def file_ref(path: Path, workspace: Path, role: str) -> dict[str, str]:
    return {"role": role, "path": path.relative_to(workspace).as_posix(), "sha256": hp1.file_hash(path)}


def artifact_ref(main: Path, manifest: Path, completion: Path, workspace: Path) -> dict[str, str]:
    return {
        "path": main.relative_to(workspace).as_posix(), "sha256": hp1.file_hash(main),
        "manifest_path": manifest.relative_to(workspace).as_posix(), "manifest_sha256": hp1.file_hash(manifest),
        "completion_path": completion.relative_to(workspace).as_posix(), "completion_sha256": hp1.file_hash(completion),
    }


def canonical_entity_source_index(character_ids: list[str], environment_ids: list[str]) -> dict:
    entries = []
    for domain, source_path, collection, identifiers in (
        ("characters", "P1/canonical-models/character-system.json", "profiles", character_ids),
        ("environments", "P1/canonical-models/environment-system.json", "environments", environment_ids),
    ):
        digest = ("c" if domain == "characters" else "e") * 64
        for index, source_id in enumerate(identifiers):
            entries.append({
                "domain": domain,
                "locator": f"/{collection}/{index}",
                "object_type": "object",
                "source_id": source_id,
                "source": {"path": source_path, "root": "source", "sha256": digest},
                "workspace_source_ref": {
                    "path": f"inputs/source-files/{source_path}",
                    "role": f"source::source::{source_path}",
                    "sha256": digest,
                },
            })
    return {"entries": entries}


def add_handoff_story_and_time_controls(admitted: dict, *, storyline_id: str = "SL-001", unit_id: str = "HNU-001") -> None:
    admitted["HS1"] = {"main": {
        "semantic_storyline_register": [{"source_storyline_id": storyline_id}],
        "activation_disposition": [{"source_storyline_id": storyline_id, "disposition": "placed"}],
        "storyline_segments": [{"source_storyline_id": storyline_id, "unit_ids": [unit_id]}],
    }}
    admitted.setdefault("HR1", {"main": {}})["main"].setdefault("space_transition_map", [])
    admitted["HR1"]["main"]["unit_duration_density"] = [{
        "unit_id": unit_id, "elapsed_start_day": 0, "elapsed_end_day": 1, "elapsed_label": "day 0 to day 1",
    }]
    admitted["HD1"]={"main":{"chapter_definitions":[{"id":"HDF-001","chapter_id":"HCH-001","chapter_number":1}]}}


def manifest_for(package: Path, content: list[Path], stage: str) -> Path:
    refs = [file_ref(path, package, "content") for path in sorted(content, key=lambda item: item.relative_to(package).as_posix())]
    value = {
        "schema_version": "1.0", "harness": hp1.HARNESS, "hld_run_id": "hld-fixture", "revision": 1,
        "stage": stage, "skill": "fixture", "status": "ready", "files": refs,
        "artifact_roles": {f"content::{index}": {**item, "role": f"content::{index}"} for index, item in enumerate(refs)},
    }
    value["files"] = [{**item, "role": f"content::{index}"} for index, item in enumerate(refs)]
    target = package / "package-manifest.json"
    write_json(target, value)
    return target


def make_completion(package: Path, stage: str, main: Path, manifest: Path, validation: Path, workspace: Path) -> Path:
    value = {
        "schema_version": "1.0", "harness": hp1.HARNESS, "stage": stage, "skill": f"fixture-{stage.lower()}",
        "hld_run_id": "hld-fixture", "revision": 1, "status": "ready",
        "input_gate_ref": {"role": "fixture", "path": main.relative_to(workspace).as_posix(), "sha256": hp1.file_hash(main)},
        "state_before_ref": {"role": "fixture", "path": main.relative_to(workspace).as_posix(), "sha256": hp1.file_hash(main)},
        "work_order_ref": {"role": "fixture", "path": main.relative_to(workspace).as_posix(), "sha256": hp1.file_hash(main)},
        "manifest_ref": file_ref(manifest, workspace, "package_manifest"),
        "validation_ref": file_ref(validation, workspace, "validation"), "upstream_completions": [],
        "canonical_artifacts": [file_ref(main, workspace, "canonical")],
        "owner_implementation": {"skill": f"fixture-{stage.lower()}", "version": "0.1.0", "sha256": "1" * 64},
        "return_binding": None, "ready_capabilities": ["fixture"], "next_allowed_stage": "HP1",
    }
    target = package / "stage-completion.json"
    write_json(target, value)
    return target


def build_design_package(workspace: Path, stage: str, authority: dict, *, lwr_prefix: str = "LWR") -> tuple[Path, Path, Path, Path]:
    package = workspace / f"{stage}-package"
    package.mkdir()
    decision = f"HDDES-{stage}-001"
    object_ids = {"HA1": "HNU-001", "HS1": "HTS-001", "HC1": "HAS-001", "HI1": "HIN-001", "HR1": "HTM-001", "HK1": "HKF-001", "HD1":"HDF-001"}
    object_id = object_ids[stage]
    stage_authority = hp1.json.loads(hp1.canonical_json(authority))
    stage_authority["hld_ownership"] = {"source_projection": [object_id], "hld_owned": [], "preserved_open": [], "lld_freedom": []}
    model = {
        "schema_version": "1.0", "skill": f"fixture-{stage.lower()}", "stage": stage,
        "hld_run_id": "hld-fixture", "status": "ready", "authority_partition": stage_authority,
        "design_decisions": [{"id": decision}], "decision_dependencies": [], "open_items": [],
        "objects": [] if stage in {"HK1","HD1"} else [{"id": object_id, "source_refs": ["NAR-001"], "design_decision_ids": [decision]}],
    }
    if stage == "HA1":
        model["chapter_shells"]=[{"id":"HCH-001","parent_unit_id":"HNU-001"}]
        def city(identifier,name,country):
            return {"city_id":identifier,"name":name,"country":country,"jurisdiction":f"{country} local jurisdiction","story_function":f"{name} carries one bounded story function","city_scale":"recognisable working city","urban_structure":["old district","institutional district"],"street_and_architecture":"streets and buildings reflect local work","transport_and_daily_rhythm":"public transport and shifts shape the day","seasonal_expression":"early-autumn weather changes movement","ordinary_people":[{"portrait":f"{name} shift worker","daily_routine":"commutes and cares for family","material_details":"work bag and transit card","crisis_exposure":"closures disrupt wages and care","knowledge_boundary":"sees disruption, not the secret cause"}],"key_story_events":[f"a bounded event occurs in {name}"]}
        cities=[city("HST-CITY-NEUTRAL","Neutral Port","Third Country"),city("HST-CITY-C-COAST","C Coast","Country C"),city("HST-CITY-C-CAPITAL","C Capital","Country C"),city("HST-CITY-M-NORTH","M North Port","Country M")]
        def route(index,source,target):
            return {"route_id":f"HST-ROUTE-{index}","from_city_id":source,"to_city_id":target,"travel_time":"several hours","physical_route":"lawful physical transfer","information_route":"authenticated limited copy","custody_rule":"originals remain with the competent jurisdiction until lawful release","story_function":"the route changes who can verify the next step"}
        model["world_setting_architecture"]={"id":"HST-WORLD-001","narrative_distribution":"Four cities separate neutral handoff, experiment, national decision, and physical intervention.","story_window":"six weeks in early autumn","season_profile":{"season":"early autumn storm season","temperature_and_weather":"coastal rain, inland dry air, and northern fog","daylight_and_air":"shortening days and different maritime air","daily_effects":"weather delays commuting and public services","plot_effect":"weather constrains action but never makes choices"},"cities":cities,"intercity_routes":[route("01","HST-CITY-NEUTRAL","HST-CITY-C-COAST"),route("02","HST-CITY-C-COAST","HST-CITY-C-CAPITAL"),route("03","HST-CITY-C-COAST","HST-CITY-M-NORTH"),route("04","HST-CITY-C-CAPITAL","HST-CITY-M-NORTH")],"threat_mechanism":{"target_system":"weather intervention network","physical_target_city_id":"HST-CITY-M-NORTH","political_pressure_city_id":"HST-CITY-C-CAPITAL","natural_hazard":"natural coastal storm","physical_actuators":["flood gate"],"scientific_limit":"the attack cannot create weather","access_path":"compromised maintenance credentials","actuator_chain":["false observation","unsafe command"],"observable_evidence":["log mismatch","physical trace"],"shutdown_condition":"revoke access and safe hardware"}}
    elif stage == "HS1":
        model["semantic_storyline_register"]=[{"source_storyline_id":"SL-001"}]
        model["activation_disposition"]=[{"source_storyline_id":"SL-001","disposition":"placed"}]
        model["storyline_segments"]=[{"source_storyline_id":"SL-001","unit_ids":["HNU-001"]}]
    elif stage == "HC1":
        model["character_participation_register"]=[{"character_id":"CHR-001","importance":"core","absence_reason":None}]
    elif stage == "HR1":
        model["space_transition_map"]=[{"id":"HTM-SPACE-001","from_environment_id":"ENV-001","to_environment_id":"ENV-001"}]
        model["unit_duration_density"]=[{"unit_id":"HNU-001","elapsed_start_day":0,"elapsed_end_day":1,"elapsed_label":"day 0 to day 1"}]
    elif stage == "HD1":
        model["chapter_definitions"]=[{"id":"HDF-001","chapter_id":"HCH-001","chapter_number":1}]
    if stage == "HK1":
        model["key_scene_functions"] = [{
            "id": "HKF-001",
            "source_refs": ["NAR-001"],
            "design_decision_ids": [decision],
            "character_refs": ["CHR-001"],
            "environment_refs": ["ENV-001"],
            "storyline_refs": ["SL-001"],
            "event_refs": ["EV-001"],
        }]
        model["lld_work_requirements"] = [{
            "id": f"{lwr_prefix}-001", "hkf_ids": ["HKF-001"], "grouping_rationale": "one required function",
            "chapter_shell_ids": ["HCH-001"], "entry_state": "before", "exit_state": "after",
            "character_ids": ["CHR-001"], "environment_ids": ["ENV-001"], "storyline_ids": ["SL-001"],
            "event_ids": ["EV-001"], "pov_constraints": ["HPV-001"], "knowledge_boundaries": ["HKS-001"],
            "prohibitions": ["no unsupported solution"], "required_elaboration": ["scene realization"],
            "lld_freedom": ["dialogue and sensory detail"], "acceptance_criteria": ["HKF-001 completed"],
        }]
    main = package / hp1.CANONICAL_FILES[stage]
    write_json(main, model)
    content = [main]
    session = package / "generation-session.json"; write_json(session, {"ready": True}); content.append(session)
    evidence = package / "generation-evidence" / "01.json"; write_json(evidence, {"ready": True}); content.append(evidence)
    execution = package / "execution-record.json"; write_json(execution, {"ready": True}); content.append(execution)
    preview = package / hp1.CANONICAL_FILES[stage].removesuffix(".json").__add__(".md"); preview.write_text("# preview\n", encoding="utf-8"); content.append(preview)
    validation = package / "validation.json"; write_json(validation, {"status": "pass"}); content.append(validation)
    manifest = manifest_for(package, content, stage)
    completion = make_completion(package, stage, main, manifest, validation, workspace)
    return main, manifest, validation, completion


def build_hq1_package(workspace: Path, *, finding: bool = False) -> tuple[Path, Path, Path, Path]:
    package = workspace / "HQ1-package"; package.mkdir()
    hdd = {"id": "HDD-HQ1-INT-OPEN", "owner_stage": "HQ1", "source_id": "INT-OPEN", "disposition": "not_needed_for_current_stage", "resolution_ref": None}
    review = {
        "schema_version": "1.0", "stage": "HQ1", "hld_run_id": "hld-fixture", "verdict": "pass" if not finding else "fail",
        "findings": [] if not finding else [{"id": "HFN-001"}], "decision_dependencies": [hdd],
        "decision_dependency_review": [{"source_id": "INT-OPEN", "status": "covered"}],
    }
    main = package / "hld-semantic-review.json"; write_json(main, review)
    session = package / "review-session.json"; write_json(session, {"ready": True})
    execution = package / "review-execution.json"; write_json(execution, {"ready": True})
    validation = package / "validation.json"; write_json(validation, {"status": "pass"})
    manifest = manifest_for(package, [main, session, execution, validation], "HQ1")
    completion = make_completion(package, "HQ1", main, manifest, validation, workspace)
    return main, manifest, validation, completion


class HP1DependencyProjectionTests(unittest.TestCase):
    def test_current_hk1_unique_stage_decision_traces_exact_lwr_derivation(self):
        lwr = {"id": "LWR-001", "hkf_ids": ["HKF-001"]}
        admitted = {
            stage: {"main": {"design_decisions": []}}
            for stage in hp1.DESIGN_STAGES
        }
        admitted["HK1"] = {"main": {
            "design_decisions": [{"id": "HDDES-HK1-001"}],
            "derivation_claims": [{
                "id": "HDRV-HK1-LWR", "target_locator": "/lld_work_requirements",
                "value_sha256": hp1.value_hash([lwr]),
            }],
            "lld_work_requirements": [lwr],
        }}
        trace = hp1.build_traceability(
            admitted,
            {
                "NAR-001": ("HB0", {"source_id": "NAR-001"}),
                "HKF-001": ("HK1", {"id": "HKF-001", "source_refs": ["NAR-001"]}),
            },
            {"hld_run_id": "hld-current", "work_units": [{
                "id": "LWK-001", "source_lwr_id": "LWR-001", "hkf_ids": ["HKF-001"],
            }]},
        )
        self.assertEqual(trace["records"][0]["decision_ids"], ["HDDES-HK1-001"])

    def test_current_hk1_ambiguous_stage_decisions_do_not_create_trace(self):
        lwr = {"id": "LWR-001", "hkf_ids": ["HKF-001"]}
        admitted = {
            stage: {"main": {"design_decisions": []}}
            for stage in hp1.DESIGN_STAGES
        }
        admitted["HK1"] = {"main": {
            "design_decisions": [{"id": "HDDES-HK1-001"}, {"id": "HDDES-HK1-002"}],
            "derivation_claims": [{
                "id": "HDRV-HK1-LWR", "target_locator": "/lld_work_requirements",
                "value_sha256": hp1.value_hash([lwr]),
            }],
            "lld_work_requirements": [lwr],
        }}
        with self.assertRaisesRegex(hp1.AssemblyBlocked, "HP1_TRACEABILITY_GAP"):
            hp1.build_traceability(
                admitted,
                {
                    "NAR-001": ("HB0", {"source_id": "NAR-001"}),
                    "HKF-001": ("HK1", {"id": "HKF-001", "source_refs": ["NAR-001"]}),
                },
                {"hld_run_id": "hld-current", "work_units": [{
                    "id": "LWK-001", "source_lwr_id": "LWR-001", "hkf_ids": ["HKF-001"],
                }]},
            )

    def test_current_lwr_projects_exact_handoff_fields_from_hkf_and_chapter_shells(self):
        admitted = {
            "HB0": {"completion": {"hld_run_id": "hld-current-lwr"}, "main": {"control_registry": [
                {"source_id": "CHR-001", "domain": "characters"},
                {"source_id": "CHR-002", "domain": "characters"},
                {"source_id": "ENV-001", "domain": "environments"},
            ]}, "source_index": canonical_entity_source_index(["CHR-001", "CHR-002"], ["ENV-001"])},
            "HA1": {"main": {"chapter_shells": [
                {"id": "HCH-001", "parent_unit_id": "HNU-001"},
                {"id": "HCH-OTHER", "parent_unit_id": "HNU-OTHER"},
            ], "world_setting_architecture": {"cities":[{"city_id":"HST-CITY-001"}],"intercity_routes":[]}}},
            "HC1": {"main": {"character_participation_register": [
                {"character_id": "CHR-001", "importance": "core", "absence_reason": None},
                {"character_id": "CHR-002", "importance": "support", "absence_reason": None},
            ]}},
            "HR1": {"main": {"space_transition_map": []}},
            "HK1": {"main": {
                "key_scene_functions": [{
                    "id": "HKF-001", "unit_id": "HNU-001",
                    "character_refs": ["CHR-001", "CHR-002"],
                    "environment_refs": ["ENV-001"],
                    "storyline_refs": ["SL-001"],
                    "event_refs": ["EV-001"],
                    "pov_constraint": "third-person-limited",
                    "knowledge_before": ["K-BEFORE"],
                    "knowledge_after": ["K-AFTER"],
                    "required_state_change": "The choice is irreversible.",
                }],
                "lld_work_requirements": [{
                    "id": "LWR-001", "source_refs": ["NAR-001"],
                    "source_authority_refs": ["NAR-001"],
                    "ownership_class": "hld-owned", "resolution_ref": None,
                    "hkf_ids": ["HKF-001"],
                    "merge_split_rationale": "one necessary scene function",
                    "entry_state": "before", "exit_state": "after",
                    "required_elaboration": ["scene realization"],
                    "lld_freedoms": ["dialogue and sensory detail"],
                    "prohibitions": ["no unsupported solution"],
                    "acceptance_criteria": ["HKF-001 completed"],
                }],
            }},
        }

        add_handoff_story_and_time_controls(admitted)
        handoff, lwr_map = hp1.build_handoff(
            admitted,
            {"path": "HP1/package-manifest.json", "sha256": "a" * 64},
            [], [], [],
        )

        self.assertEqual(set(lwr_map), {"LWR-001"})
        self.assertEqual(handoff["hld_run_id"], "hld-current-lwr")
        self.assertEqual(handoff["work_units"], [{
            "id": "LWK-001", "source_lwr_id": "LWR-001",
            "hkf_ids": ["HKF-001"],
            "grouping_rationale": "one necessary scene function",
            "chapter_shell_ids": ["HCH-001"],
            "entry_state": "before", "exit_state": "after",
            "exit_state_refs": ["after", "K-AFTER", "The choice is irreversible."],
            "character_ids": ["CHR-001", "CHR-002"],
            "environment_ids": ["ENV-001"],
            "storyline_ids": ["SL-001"], "event_ids": ["EV-001"],
            "pov_constraints": ["third-person-limited"],
            "knowledge_boundaries": ["K-BEFORE", "K-AFTER"],
            "prohibitions": ["no unsupported solution"],
            "required_elaboration": ["scene realization"],
            "lld_freedom": ["dialogue and sensory detail"],
            "acceptance_criteria": ["HKF-001 completed"],
            "source_value_sha256": hp1.value_hash(admitted["HK1"]["main"]["lld_work_requirements"][0]),
        }])
        self.assertEqual(handoff["character_dispositions"], [
            {"character_id":"CHR-001","importance":"core","disposition":"placed","work_unit_ids":["LWK-001"],"absence_reason":None},
            {"character_id":"CHR-002","importance":"support","disposition":"placed","work_unit_ids":["LWK-001"],"absence_reason":None},
        ])
        self.assertEqual(handoff["environment_coverage"], {"required_ids":["ENV-001"],"placed_ids":["ENV-001"]})
        self.assertEqual(handoff["storyline_dispositions"], [{
            "storyline_id": "SL-001", "disposition": "placed", "work_unit_ids": ["LWK-001"], "absence_reason": None,
        }])
        self.assertEqual(handoff["work_unit_time_windows"], [{
            "work_unit_id": "LWK-001", "source_unit_ids": ["HNU-001"],
            "elapsed_start_day": 0, "elapsed_end_day": 1, "label": "day 0 to day 1",
        }])
        self.assertEqual(handoff["terminal_state_refs"], ["after", "K-AFTER", "The choice is irreversible."])
        self.assertEqual(handoff["chapter_definition_refs"],[{"id":"HDF-001","chapter_id":"HCH-001","chapter_number":1,"model_path":"canonical-models/chapter-definition-architecture.json","locator":"/chapter_definitions/0","value_sha256":hp1.value_hash(admitted["HD1"]["main"]["chapter_definitions"][0])}])

    def test_missing_character_or_environment_disposition_fails_closed(self):
        admitted = {
            "HB0":{"completion":{"hld_run_id":"coverage"},"main":{"control_registry":[{"source_id":"CHR-001","domain":"characters"},{"source_id":"CHR-002","domain":"characters"},{"source_id":"ENV-001","domain":"environments"},{"source_id":"ENV-002","domain":"environments"}]},"source_index":canonical_entity_source_index(["CHR-001","CHR-002"],["ENV-001","ENV-002"])},
            "HA1":{"main":{"chapter_shells":[{"id":"HCH-001","parent_unit_id":"HNU-001"}],"world_setting_architecture":{"cities":[{"city_id":"HST-CITY-001"}],"intercity_routes":[]}}},
            "HC1":{"main":{"character_participation_register":[{"character_id":"CHR-001","importance":"core","absence_reason":None}]}},
            "HR1":{"main":{"space_transition_map":[]}},
            "HK1":{"main":{"key_scene_functions":[{"id":"HKF-001","unit_id":"HNU-001","character_refs":["CHR-001"],"environment_refs":["ENV-001"],"storyline_refs":["SL-001"],"event_refs":["EV-001"],"pov_constraint":"limited","knowledge_before":["K0"],"knowledge_after":["K1"],"required_state_change":"changed"}],"lld_work_requirements":[{"id":"LWR-001","hkf_ids":["HKF-001"],"merge_split_rationale":"one function","entry_state":"before","exit_state":"after","required_elaboration":["realize"],"lld_freedoms":["wording"],"prohibitions":[],"acceptance_criteria":["done"]}]}},
        }
        add_handoff_story_and_time_controls(admitted)
        with self.assertRaisesRegex(hp1.AssemblyBlocked,"HP1_CHARACTER_DISPOSITION_GAP"):
            hp1.build_handoff(admitted,{"path":"HP1/package-manifest.json","sha256":"a"*64},[],[],[])
        admitted["HC1"]["main"]["character_participation_register"].append({"character_id":"CHR-002","importance":"context","absence_reason":"named background only"})
        with self.assertRaisesRegex(hp1.AssemblyBlocked,"HP1_ENVIRONMENT_PLACEMENT_GAP"):
            hp1.build_handoff(admitted,{"path":"HP1/package-manifest.json","sha256":"a"*64},[],[],[])

    def test_entity_coverage_uses_only_canonical_profiles_and_environments(self):
        admitted = {
            "HB0": {"completion": {"hld_run_id": "entities"}, "main": {"control_registry": [
                {"source_id": "CHR-001", "domain": "characters"},
                {"source_id": "REL-001", "domain": "characters"},
                {"source_id": "DEV-C1-001", "domain": "characters"},
                {"source_id": "ENV-001", "domain": "environments"},
                {"source_id": "ZONE-001", "domain": "environments"},
            ]}, "source_index": {"entries": [
                *canonical_entity_source_index(["CHR-001"], ["ENV-001"])["entries"],
                {"domain": "characters", "locator": "/relationships/0", "object_type": "object", "source_id": "REL-001", "source": {"path": "P1/canonical-models/character-system.json", "root": "source", "sha256": "c" * 64}, "workspace_source_ref": {"path": "inputs/source-files/P1/canonical-models/character-system.json", "role": "source::character", "sha256": "c" * 64}},
                {"domain": "characters", "locator": "/development_freedoms/0", "object_type": "object", "source_id": "DEV-C1-001", "source": {"path": "P1/canonical-models/character-system.json", "root": "source", "sha256": "c" * 64}, "workspace_source_ref": {"path": "inputs/source-files/P1/canonical-models/character-system.json", "role": "source::character", "sha256": "c" * 64}},
                {"domain": "environments", "locator": "/functional_zones/0", "object_type": "object", "source_id": "ZONE-001", "source": {"path": "P1/canonical-models/environment-system.json", "root": "source", "sha256": "e" * 64}, "workspace_source_ref": {"path": "inputs/source-files/P1/canonical-models/environment-system.json", "role": "source::environment", "sha256": "e" * 64}},
            ]}},
            "HA1": {"main": {"chapter_shells": [{"id": "HCH-001", "parent_unit_id": "HNU-001"}], "world_setting_architecture": {"cities": [{"city_id": "HST-CITY-001"}], "intercity_routes": []}}},
            "HC1": {"main": {"character_participation_register": [{"character_id": "CHR-001", "importance": "core", "absence_reason": None}]}},
            "HR1": {"main": {"space_transition_map": []}},
            "HK1": {"main": {"key_scene_functions": [{"id": "HKF-001", "unit_id": "HNU-001", "character_refs": ["CHR-001"], "environment_refs": ["ENV-001"], "storyline_refs": ["SL-001"], "event_refs": ["EV-001"], "pov_constraint": "limited", "knowledge_before": ["K0"], "knowledge_after": ["K1"], "required_state_change": "changed"}], "lld_work_requirements": [{"id": "LWR-001", "hkf_ids": ["HKF-001"], "merge_split_rationale": "one function", "entry_state": "before", "exit_state": "after", "required_elaboration": ["realize"], "lld_freedoms": ["wording"], "prohibitions": [], "acceptance_criteria": ["done"]}]}},
        }
        add_handoff_story_and_time_controls(admitted)
        handoff, _ = hp1.build_handoff(admitted, {"path": "HP1/package-manifest.json", "sha256": "a" * 64}, [], [], [])
        self.assertEqual([item["character_id"] for item in handoff["character_dispositions"]], ["CHR-001"])
        self.assertEqual(handoff["environment_coverage"], {"required_ids": ["ENV-001"], "placed_ids": ["ENV-001"]})

    def test_baseline_control_matches_exact_duplicate_source_id_entry(self):
        workspace_ref={"role":"source::author","path":"inputs/author.json","sha256":"a"*64}
        control={"source_id":"CHR-R07","domain":"characters","classification":"mandatory","open_item":False,"authority_class":"author_locked","source_value_sha256":"1"*64,"locator":"/controls/1/value","workspace_source_ref":workspace_ref}
        admitted={"HB0":{"main":{"control_registry":[control]},"source_index":{"entries":[
            {"source_id":"CHR-R07","domain":"characters","locator":"/controls/1/value","workspace_source_ref":workspace_ref,"value_sha256":"1"*64},
            {"source_id":"CHR-R07","domain":"characters","locator":"/profiles/12","workspace_source_ref":{"role":"source::profile","path":"inputs/profile.json","sha256":"b"*64},"value_sha256":"2"*64},
        ]}}}
        self.assertEqual("1"*64,hp1.build_baseline_controls(admitted)[0]["source_value_sha256"])

    def test_non_quality_open_source_does_not_require_hq1_hdd(self):
        unresolved=[{"source_id":"CAU-OPEN","domain":"cross-domain"}]
        projected=hp1.project_unresolved(unresolved)
        self.assertNotIn("CAU-OPEN",projected["HQ1"])
        self.assertTrue(all("CAU-OPEN" in projected[stage] for stage in hp1.DESIGN_STAGES))

    def test_quality_open_source_requires_hq1_hdd(self):
        unresolved=[{"source_id":"QUAL-OPEN","domain":"quality"}]
        projected=hp1.project_unresolved(unresolved)
        self.assertEqual(["QUAL-OPEN"],projected["HQ1"])
        self.assertTrue(all("QUAL-OPEN" not in projected[stage] for stage in hp1.DESIGN_STAGES))


def build_workspace(root: Path, *, finding: bool = False, lwr_prefix: str = "LWR", unresolved_projection: bool = False) -> Path:
    hb0_order = hb0_test.build_workspace(root)
    with patch.object(hb0_test.runtime, "_run_preparation_validator", return_value=None):
        code, _ = hb0_test.runtime.execute(hb0_order)
    if code != 0:
        raise AssertionError("HB0 fixture did not become ready")
    workspace = hb0_order.parent
    (workspace / "stage-result.json").unlink()
    hb0_package = workspace / "HB0-package"
    role_paths: dict[str, Path] = {
        "hb0_control_baseline": hb0_package / "hld-control-baseline.json",
        "hb0_source_index": hb0_package / "hld-source-index.json",
        "hb0_manifest": hb0_package / "package-manifest.json",
        "hb0_validation": hb0_package / "validation.json",
        "hb0_completion": hb0_package / "stage-completion.json",
    }
    authority = hp1.read_json(role_paths["hb0_control_baseline"])["authority_partition"]
    stage_values: dict[str, tuple[Path, Path, Path, Path]] = {}
    for stage in hp1.DESIGN_STAGES:
        values = build_design_package(workspace, stage, authority, lwr_prefix=lwr_prefix if stage == "HK1" else "LWR")
        stage_values[stage] = values
        for suffix, path in zip(("canonical", "manifest", "validation", "completion"), values):
            role_paths[f"{stage.lower()}_{suffix}"] = path
    stage_values["HQ1"] = build_hq1_package(workspace, finding=finding)
    for suffix, path in zip(("semantic_review", "manifest", "validation", "completion"), stage_values["HQ1"]):
        role_paths[f"hq1_{suffix}"] = path
    upstream = []
    for stage in hp1.UPSTREAM:
        main_role = hp1.MAIN_ROLES[stage]
        upstream.append(artifact_ref(role_paths[main_role], role_paths[f"{stage.lower()}_manifest"], role_paths[f"{stage.lower()}_completion"], workspace))
    allowlist = [file_ref(path, workspace, role) for role, path in sorted(role_paths.items())]
    state = workspace / "hp1-state-before.json"; write_json(state, {"stage": "HP1", "revision": 1})
    gate_path = workspace / "hp1-input-gate.json"
    gate = {
        "schema_version": "1.0", "harness": hp1.HARNESS, "hld_run_id": "hld-fixture", "stage": "HP1", "mode": "forward",
        "state_before_ref": file_ref(state, workspace, "state_before"), "hb0_completion_ref": upstream[0], "upstream_completions": upstream,
        "baseline_manifest_ref": None, "baseline_validation_ref": None, "source_lineage_refs": [],
        "exact_owner_skill": hp1.SKILL, "owner_version": hp1.VERSION, "implementation_sha256": hp1.implementation_sha256(),
        "return_binding": None, "unresolved_projection": ["INT-OPEN"] if unresolved_projection else [],
        "revision_plan_ref": None, "revision_plan_state_ref": None, "file_allowlist": allowlist,
    }
    write_json(gate_path, gate)
    work_order = {
        "schema_version": "1.0", "harness": hp1.HARNESS, "hld_run_id": "hld-fixture", "revision": 1,
        "work_order_id": "WO-HP1-001", "task_id": "TASK-HP1-001", "stage": "HP1", "action": "execute",
        "exact_owner_skill": hp1.SKILL, "owner_version": hp1.VERSION, "implementation_sha256": hp1.implementation_sha256(),
        "event_sequence": 9, "result_timestamp": "2026-08-06T00:00:00Z", "input_gate_ref": file_ref(gate_path, workspace, "input_gate"),
        "state_before_ref": file_ref(state, workspace, "state_before"), "upstream_completions": upstream,
        "file_allowlist": allowlist, "unresolved_projection": gate["unresolved_projection"], "mode": "forward",
        "return_binding": None, "revision_plan_ref": None, "revision_plan_state_ref": None,
        "output_directory": "HP1-package", "submission_status": "open",
    }
    order = workspace / "hp1-work-order.json"; write_json(order, work_order)
    return order


class HP1RuntimeTests(unittest.TestCase):
    def test_fixture_manifest_hashes_are_current(self) -> None:
        fixture_root = SKILL_ROOT / "tests" / "fixtures"
        manifest = hp1.read_json(fixture_root / "fixture-manifest.json")
        self.assertEqual(
            [(item["path"], item["sha256"]) for item in manifest["files"]],
            sorted((item["path"], item["sha256"]) for item in manifest["files"]),
        )
        for item in manifest["files"]:
            self.assertEqual(hashlib.sha256((fixture_root / item["path"]).read_bytes()).hexdigest(), item["sha256"])

    def test_positive_ready_is_lossless_bijective_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            code, result = hp1.execute(order)
            self.assertEqual((code, result["result"]), (0, "ready"))
            self.assertEqual(hp1.validate_existing(order)["status"], "pass")
            package = order.parent / "HP1-package"
            handoff = hp1.read_json(package / "lld-handoff.json")
            self.assertEqual([(item["source_lwr_id"], item["id"]) for item in handoff["work_units"]], [("LWR-001", "LWK-001")])
            cross_ids = {item["id"] for item in hp1.read_json(package / "hld-cross-index.json")["entries"]}
            self.assertTrue({"NAR-001", "INT-OPEN", "LWR-001", "HKF-001"}.issubset(cross_ids))
            entries = {item["id"]: item for item in hp1.read_json(package / "hld-cross-index.json")["entries"]}
            self.assertEqual((entries["NAR-001"]["owner_stage"], entries["NAR-001"]["kind"]), ("HB0", "source_control"))
            for record in hp1.read_json(package / "hld-traceability-matrix.json")["records"]:
                self.assertTrue(set(record["source_ids"]).issubset(entries))
            self.assertTrue((order.parent / "stage-result.json").is_file())
            self.assertFalse((package / "stage-result.json").exists())
            completion = hp1.read_json(package / "stage-completion.json")
            result_document = hp1.read_json(order.parent / "stage-result.json")
            refs = [completion["manifest_ref"], completion["validation_ref"], *completion["canonical_artifacts"], result_document["completion_ref"], result_document["result_manifest_ref"], result_document["validation_ref"]]
            self.assertFalse(any(".hp1-" in item["path"] for item in refs))
            for item in refs:
                hp1.verify_ref(item, order.parent)

    def test_negative_hq1_nonpass_blocks_without_ready_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), finding=True)
            code, result = hp1.execute(order)
            self.assertEqual((code, result["result"]), (2, "blocked"))
            self.assertEqual({path.name for path in (order.parent / "HP1-package").iterdir()}, hp1.BLOCKED_FILES)

    def test_negative_hk1_lwk_source_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), lwr_prefix="LWK")
            code, result = hp1.execute(order)
            self.assertEqual((code, result["result"]), (2, "blocked"))
            self.assertEqual(hp1.read_json(order.parent / "HP1-package" / "blocked-report.json")["code"], "HP1_LWR_ID_INVALID")

    def test_boundary_unresolved_projection_is_rejected_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), unresolved_projection=True)
            with self.assertRaises(hp1.RuntimeFailure):
                hp1.load_context(order)
            self.assertFalse((order.parent / "HP1-package").exists())
            self.assertFalse((order.parent / "stage-result.json").exists())

    def test_negative_non_main_upstream_hash_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            context = hp1.load_context(order)
            write_json(order.parent / "HA1-package" / "generation-session.json", {"ready": False})
            with self.assertRaisesRegex(hp1.AssemblyBlocked, "HP1_UPSTREAM_ENVELOPE_INVALID"):
                hp1.admit_upstreams(context)

    def test_negative_upstream_closure_extra_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            context = hp1.load_context(order)
            write_json(order.parent / "HS1-package" / "undeclared.json", {"extra": True})
            with self.assertRaisesRegex(hp1.AssemblyBlocked, "HP1_UPSTREAM_ENVELOPE_INVALID"):
                hp1.admit_upstreams(context)

    def test_negative_completion_canonical_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            context = hp1.load_context(order)
            completion_path = order.parent / "HC1-package" / "stage-completion.json"
            completion = hp1.read_json(completion_path)
            completion["canonical_artifacts"] = [file_ref(order.parent / "HC1-package" / "package-manifest.json", order.parent, "canonical")]
            write_json(completion_path, completion)
            context.work_order["upstream_completions"][3]["completion_sha256"] = hp1.file_hash(completion_path)
            with self.assertRaisesRegex(hp1.AssemblyBlocked, "HP1_UPSTREAM_ENVELOPE_INVALID"):
                hp1.admit_upstreams(context)


if __name__ == "__main__":
    unittest.main()
