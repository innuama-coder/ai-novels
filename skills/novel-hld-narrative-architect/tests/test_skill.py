from __future__ import annotations

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

from runtime.canonical import canonical_sha256, file_ref, json_pointer, read_json, sha256_file, verify_file_ref, write_json  # noqa: E402
from runtime.contracts import SKILLS, UPSTREAM, next_stage  # noqa: E402
from runtime.design_stage_runtime import derive_file_allowlist, implementation_sha256, validate_existing  # noqa: E402
from runtime.hdd import expected_hdd_id, project_unresolved  # noqa: E402
from runtime.package_envelope import (  # noqa: E402
    validate_completion_bindings,
    validate_manifest,
    validate_ready_profile,
    validate_result_envelope,
)
from runtime.schema_catalog import SchemaCatalog  # noqa: E402


CONTRACT = json.loads((SKILL / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
RUNTIME = SKILL / "scripts" / "run_skill.py"
CATALOG = SchemaCatalog(HARNESS / "schemas")
RUN_ID = "RUN-PUBLIC-001"
FREE_ID = "INT-FREE-001"
OPEN_ID = "INT-OPEN-001"
VALUE_HASH = canonical_sha256("choose structure")
OPEN_VALUE_HASH = canonical_sha256("preserve unresolved")


def make_artifact_ref(main: Path, manifest: Path, completion: Path, workspace: Path) -> dict[str, str]:
    return {
        "path": main.relative_to(workspace).as_posix(), "sha256": sha256_file(main),
        "manifest_path": manifest.relative_to(workspace).as_posix(), "manifest_sha256": sha256_file(manifest),
        "completion_path": completion.relative_to(workspace).as_posix(), "completion_sha256": sha256_file(completion),
    }


def write_manifest(package: Path, stage: str, roles: dict[str, Path]) -> Path:
    refs = [file_ref(path, root=package, role=role) for role, path in roles.items()]
    value = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": RUN_ID,
        "revision": 0, "stage": stage, "skill": SKILLS[stage], "status": "ready",
        "files": refs, "artifact_roles": {item["role"]: item for item in refs},
    }
    CATALOG.validate(value, "package-manifest.schema.json")
    path = package / "package-manifest.json"
    write_json(path, value)
    return path


def protocol_refs(workspace: Path, stage: str) -> tuple[dict, dict, dict]:
    root = workspace / "protocol" / stage
    gate = root / "input-gate.json"
    state = root / "state.json"
    order = root / "work-order.json"
    write_json(gate, {"stage": stage, "fixture": True})
    write_json(state, {"stage": stage, "fixture": True})
    write_json(order, {"stage": stage, "fixture": True})
    return (
        file_ref(gate, root=workspace, role="input_gate"),
        file_ref(state, root=workspace, role="state_before"),
        file_ref(order, root=workspace, role="work_order"),
    )


def source_values(workspace: Path, *, must_ask: bool = False) -> tuple[Path, dict, dict]:
    source = workspace / "inputs" / "intent.json"
    write_json(source, {"freedom": "choose structure", "open": "preserve unresolved"})
    source_ref = file_ref(source, root=workspace, role="source::intent")
    free = {
        "source_id": FREE_ID, "classification": "freedom", "open_item": False,
        "authority_class": "downstream_freedom", "domain": "intent", "source": {"fixture": "intent"},
        "workspace_source_ref": source_ref, "locator": "/freedom", "source_text": "choose structure",
        "source_value_sha256": VALUE_HASH, "hld_instruction": "select a bounded structure", "preserve_unresolved": False,
    }
    opened = {
        "source_id": OPEN_ID, "classification": "must_ask" if must_ask else "open", "open_item": True,
        "authority_class": "author_open", "domain": "intent", "source": {"fixture": "intent"},
        "workspace_source_ref": source_ref, "locator": "/open", "source_text": "preserve unresolved",
        "source_value_sha256": OPEN_VALUE_HASH, "hld_instruction": "do not silently resolve", "preserve_unresolved": True,
    }
    return source, free, opened


def build_hb0(workspace: Path, *, must_ask: bool = False) -> tuple[dict, dict[str, Path]]:
    source, free, opened = source_values(workspace, must_ask=must_ask)
    package = workspace / "upstream" / "HB0" / "package"
    package.mkdir(parents=True)
    partition = {
        "source_classifications": {"mandatory": [], "freedom": [FREE_ID], "must_ask": [OPEN_ID] if must_ask else [], "open": [] if must_ask else [OPEN_ID]},
        "source_open_items": [OPEN_ID],
        "source_authority_classes": {"author_locked": [], "autonomous_owned": [], "downstream_freedom": [FREE_ID], "author_open": [OPEN_ID]},
        "hld_ownership": {"source_projection": [], "hld_owned": [], "preserved_open": [], "lld_freedom": []},
    }
    control = {
        "schema_version": "1.0", "skill": SKILLS["HB0"], "stage": "HB0", "hld_run_id": RUN_ID, "status": "ready",
        "source_baseline": file_ref(source, root=workspace, role="source::intent"), "source_release": {"fixture": "1.0"},
        "lineage": {"fixture": True}, "admission_verdicts": [f"gate-{index}" for index in range(8)],
        "authority_partition": partition, "control_registry": [free, opened],
        "unresolved_register": [{"source_id": OPEN_ID, "domain": "intent", "classification": opened["classification"], "open_item": True, "authority_class": "author_open"}],
        "hld_assignment": {"fixture": True}, "change_policy": {"fixture": True},
        "prohibitions": ["change-authority", "write-prose", "produce-lld", "resolve-author-open"],
        "source_access_policy": "SOURCE_ACCESS_MATRIX@1.0",
    }
    main = package / "hld-control-baseline.json"
    write_json(main, control)
    index = {
        "schema_version": "1.0", "skill": SKILLS["HB0"], "stage": "HB0", "hld_run_id": RUN_ID, "status": "ready",
        "entries": [
            {"source_id": row["source_id"], "domain": "intent", "object_type": "string", "schema_discriminator": None,
             "source": {"fixture": "intent"}, "workspace_source_ref": row["workspace_source_ref"],
             "locator": row["locator"], "value_sha256": row["source_value_sha256"],
             "allowed_stages": ["HB0", "HA1", "HS1", "HC1", "HI1", "HR1", "HK1", "HQ1"]}
            for row in (free, opened)
        ],
    }
    index_path = package / "hld-source-index.json"
    write_json(index_path, index)
    write_json(package / "hb0-execution.json", {
        "schema_version": "1.0", "skill": SKILLS["HB0"], "stage": "HB0", "hld_run_id": RUN_ID,
        "work_order_id": "WO-HB0-001", "implementation_sha256": "3" * 64,
        "input_hashes": {"source": sha256_file(source)}, "preparation_validator_exit_code": 0,
        "read_roles": ["source::intent"], "output_hashes": {"control": sha256_file(main), "index": sha256_file(index_path)},
        "deterministic": True,
    })
    write_json(package / "validation.json", {
        "schema_version": "1.0", "skill": SKILLS["HB0"], "stage": "HB0", "hld_run_id": RUN_ID,
        "status": "pass", "checks": ["fixture baseline admitted"], "errors": [],
        "artifacts": [file_ref(main, root=workspace, role="control_baseline"), file_ref(index_path, root=workspace, role="source_index")],
    })
    roles = {
        "control_baseline": main, "source_index": index_path,
        "execution_record": package / "hb0-execution.json", "validation": package / "validation.json",
    }
    manifest = write_manifest(package, "HB0", roles)
    gate_ref, state_ref, order_ref = protocol_refs(workspace, "HB0")
    completion_value = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "stage": "HB0", "skill": SKILLS["HB0"],
        "hld_run_id": RUN_ID, "revision": 0, "status": "ready", "input_gate_ref": gate_ref,
        "state_before_ref": state_ref, "work_order_ref": order_ref,
        "manifest_ref": file_ref(manifest, root=workspace, role="package_manifest"),
        "validation_ref": file_ref(package / "validation.json", root=workspace, role="validation"),
        "upstream_completions": [],
        "canonical_artifacts": [file_ref(main, root=workspace, role="control_baseline"), file_ref(index_path, root=workspace, role="source_index")],
        "owner_implementation": {"skill": SKILLS["HB0"], "version": "1.0.0", "sha256": "3" * 64},
        "return_binding": None, "ready_capabilities": ["baseline_admitted"], "next_allowed_stage": "HA1",
    }
    CATALOG.validate(completion_value, "stage-completion.schema.json")
    completion = package / "stage-completion.json"
    write_json(completion, completion_value)
    validate_ready_profile(package, "HB0")
    validate_manifest(package, read_json(manifest))
    validate_completion_bindings(workspace, package, completion_value)
    return make_artifact_ref(main, manifest, completion, workspace), {
        "source": source, "source_index": index_path, "manifest": manifest,
        "validation": package / "validation.json", "main": main,
    }


DESIGN_FILES = {
    "HA1": ("narrative-architecture.json", "narrative-architecture.md", "narrative_architecture"),
    "HS1": ("storyline-choreography.json", "storyline-choreography.md", "storyline_choreography"),
    "HC1": ("character-arc-placement.json", "character-arc-placement.md", "character_arc_placement"),
}


def build_design_upstream(workspace: Path, stage: str, prior: list[dict]) -> dict:
    canonical_name, preview_name, artifact_role = DESIGN_FILES[stage]
    package = workspace / "upstream" / stage / "package"
    package.mkdir(parents=True)
    main = package / canonical_name
    write_json(main, {"schema_version": "1.0", "skill": SKILLS[stage], "stage": stage, "hld_run_id": RUN_ID, "status": "ready"})
    write_json(package / "generation-session.json", {"schema_version": "1.0", "stage": stage})
    write_json(package / "generation-evidence" / "00.json", {"schema_version": "1.0", "stage": stage})
    write_json(package / "execution-record.json", {"schema_version": "1.0", "stage": stage})
    (package / preview_name).write_text(f"# {stage}\n", encoding="utf-8", newline="")
    write_json(package / "validation.json", {"schema_version": "1.0", "stage": stage, "status": "pass"})
    roles = {
        artifact_role: main, "generation_session": package / "generation-session.json",
        "generation_evidence": package / "generation-evidence" / "00.json",
        "execution_record": package / "execution-record.json", "preview": package / preview_name,
        "validation": package / "validation.json",
    }
    manifest = write_manifest(package, stage, roles)
    gate_ref, state_ref, order_ref = protocol_refs(workspace, stage)
    completion_value = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "stage": stage, "skill": SKILLS[stage],
        "hld_run_id": RUN_ID, "revision": 0, "status": "ready", "input_gate_ref": gate_ref,
        "state_before_ref": state_ref, "work_order_ref": order_ref,
        "manifest_ref": file_ref(manifest, root=workspace, role="package_manifest"),
        "validation_ref": file_ref(package / "validation.json", root=workspace, role="validation"),
        "upstream_completions": prior,
        "canonical_artifacts": [file_ref(main, root=workspace, role=artifact_role)],
        "owner_implementation": {"skill": SKILLS[stage], "version": "1.0.0", "sha256": "4" * 64},
        "return_binding": None, "ready_capabilities": [f"{stage.lower()}_ready"], "next_allowed_stage": next_stage(stage),
    }
    CATALOG.validate(completion_value, "stage-completion.schema.json")
    completion = package / "stage-completion.json"
    write_json(completion, completion_value)
    validate_ready_profile(package, stage)
    validate_manifest(package, read_json(manifest))
    validate_completion_bindings(workspace, package, completion_value)
    return make_artifact_ref(main, manifest, completion, workspace)


def authority() -> dict:
    return {"source_id": FREE_ID, "classification": "freedom", "open_item": False, "authority_class": "downstream_freedom", "value_sha256": VALUE_HASH}


def must_ask_authority() -> dict:
    return {"source_id": OPEN_ID, "classification": "must_ask", "open_item": True, "authority_class": "author_open", "value_sha256": OPEN_VALUE_HASH}


def element(identifier: str, **extra) -> dict:
    value = {"id": identifier, "source_refs": [FREE_ID], "source_authority_refs": [authority()], "ownership_class": "hld_owned", "resolution_ref": None}
    value.update(extra)
    return value


def dependency(stage: str, resolution_ref: dict | None = None) -> dict:
    return {
        "id": expected_hdd_id(stage, OPEN_ID), "source_id": OPEN_ID, "owner_stage": stage,
        "affected_obligation_ids": [], "disposition": "resolved_by_external_author_event" if resolution_ref else "not_needed_for_current_stage",
        "object_evidence_refs": [], "rationale_anchor": f"source_index:{OPEN_ID}",
        "downstream_effect": "project clarified answer" if resolution_ref else "preserve unresolved", "resolution_ref": resolution_ref,
    }


def common_model(stage: str, input_gate_ref: dict, actual_reads: list[dict]) -> dict:
    return {
        "schema_version": "1.0", "skill": CONTRACT["skill"], "stage": stage, "hld_run_id": RUN_ID, "status": "ready",
        "input_gate_ref": input_gate_ref, "source_artifacts": actual_reads,
        "authority_partition": {
            "source_classifications": {"mandatory": [], "freedom": [FREE_ID], "must_ask": [], "open": [OPEN_ID]},
            "source_open_items": [OPEN_ID],
            "source_authority_classes": {"author_locked": [], "autonomous_owned": [], "downstream_freedom": [FREE_ID], "author_open": [OPEN_ID]},
            "hld_ownership": {"source_projection": [], "hld_owned": [], "preserved_open": [], "lld_freedom": []},
        },
        "design_decisions": [{"id": CONTRACT["decision_prefix"] + "001", "choice": "selected", "candidate_refs": ["OPT-1", "OPT-2"]}],
        "derivation_claims": [],
        "decision_dependencies": [dependency(stage)], "open_items": [OPEN_ID],
        "downstream_contract": {"consumer": CONTRACT["next_stage"], "required_roles": CONTRACT["ready_capabilities"]},
    }


def stage_model(stage: str, input_gate_ref: dict, actual_reads: list[dict]) -> dict:
    model = common_model(stage, input_gate_ref, actual_reads)
    if stage == "HA1":
        model.update({
            "architecture_choice": element("HST-ARCH-001", form="parallel_convergence", rationale="fits authorized lines"),
            "world_setting_architecture": element("HST-WORLD-001", story_window="six weeks in early autumn", season_profile={"season":"early autumn storm season","temperature_and_weather":"humid coast, dry inland capital, cold-current fog in the north","daylight_and_air":"shortening days and contrasting maritime air masses","daily_effects":"rain, closures, and transport delays affect ordinary routines","plot_effect":"weather constrains verification but never chooses for a character"}, cities=[{"city_id":"HST-CITY-NEUTRAL","name":"Neutral Port","country":"Third Country","jurisdiction":"neutral local criminal and customs jurisdiction","story_function":"the interrupted intelligence handoff occurs here","city_scale":"medium free port","urban_structure":["bonded warehouse belt","dense workers district"],"street_and_architecture":"rain-dark freight lanes and concrete arcades","transport_and_daily_rhythm":"night freight and dawn commuter buses","seasonal_expression":"warm storm rain","ordinary_people":[{"portrait":"night-shift logistics worker","daily_routine":"changes buses before dawn","material_details":"rain boots and lunch tin","crisis_exposure":"closures remove wages","knowledge_boundary":"knows shift alerts, not the operation"}],"key_story_events":["Gu dies after sending only a minimal clue"]},{"city_id":"HST-CITY-C-COAST","name":"C Coast","country":"Country C","jurisdiction":"Country C civil and research jurisdiction","story_function":"the hidden experiment and central relationship unfold here","city_scale":"large coastal city","urban_structure":["old river district","research quarter"],"street_and_architecture":"arcades, towers, and drainage channels","transport_and_daily_rhythm":"metro and clinic shifts","seasonal_expression":"humid rain","ordinary_people":[{"portrait":"caregiver and shop assistant","daily_routine":"opens a shop after buying medicine","material_details":"umbrella and transit card","crisis_exposure":"flooded streets delay care","knowledge_boundary":"sees disruption, not its cause"}],"key_story_events":["R-07 is activated"]},{"city_id":"HST-CITY-C-CAPITAL","name":"C Capital","country":"Country C","jurisdiction":"Country C national jurisdiction","story_function":"national decisions and the bilateral meeting are prepared here","city_scale":"large inland capital","urban_structure":["diplomatic district","government quarter"],"street_and_architecture":"broad avenues and controlled compounds","transport_and_daily_rhythm":"commuter rail and security closures","seasonal_expression":"drier early-autumn air","ordinary_people":[{"portrait":"government-quarter cleaner","daily_routine":"takes the first suburban train","material_details":"thermos and temporary badge","crisis_exposure":"lockdowns remove shifts","knowledge_boundary":"sees sealed rooms, not agendas"}],"key_story_events":["meeting security changes"]},{"city_id":"HST-CITY-M-NORTH","name":"M North Port","country":"Country M","jurisdiction":"Country M local and national technical jurisdiction","story_function":"independent weather verification and hardware intervention occur here","city_scale":"small cold-water port","urban_structure":["radar headland","maintenance harbour"],"street_and_architecture":"low windproof buildings","transport_and_daily_rhythm":"service vans and fishing traffic before dawn","seasonal_expression":"cold-current fog and strong wind","ordinary_people":[{"portrait":"harbour shopkeeper","daily_routine":"opens before boats depart","material_details":"radio and waterproof notebook","crisis_exposure":"a hardware alert sends family onto the headland","knowledge_boundary":"knows equipment failed, not the diplomatic reason"}],"key_story_events":["local team verifies and disables compromised hardware"]}], intercity_routes=[{"route_id":"HST-ROUTE-NEUTRAL-C","from_city_id":"HST-CITY-NEUTRAL","to_city_id":"HST-CITY-C-COAST","travel_time":"several hours by secure air and road","physical_route":"original evidence remains under neutral-country custody until lawful release","information_route":"authenticated copies and a minimal encrypted clue reach Country C first","custody_rule":"body, original evidence, and digital clues follow separate legal chains","story_function":"the interrupted handoff becomes a verifiable input without erasing jurisdiction"},{"route_id":"HST-ROUTE-C-M","from_city_id":"HST-CITY-C-COAST","to_city_id":"HST-CITY-M-NORTH","travel_time":"same-day flight but no remote substitute for field action","physical_route":"Country M personnel reach their own equipment","information_route":"a restricted channel sends only independently testable indicators","custody_rule":"each country controls evidence and hardware inside its own jurisdiction","story_function":"digital clues are tested against physical systems"}], threat_mechanism={"target_system":"weather-sensing and intervention network used to protect the bilateral meeting corridor","access_path":"compromised maintenance credentials alter trusted sensor and actuator instructions","actuator_chain":["false observations enter the forecast chain","authorized controllers issue unsafe physical commands","local hardware changes atmospheric intervention at the wrong time"],"observable_evidence":["signed maintenance records disagree with device state","independent radar and power traces reproduce the anomaly"],"shutdown_condition":"revoke credentials, isolate the control path, and physically safe the affected hardware"}),
            "structural_phases": [element("HST-PHASE-001", order=0, purpose="establish pressure", entry_state_ref="STATE-0", exit_state_ref="STATE-1")],
            "narrative_units": [element("HNU-001", parent_phase_id="HST-PHASE-001", order=0, purpose="commit conflict", entry_state_ref="STATE-0", required_change="options narrow", exit_state_ref="STATE-1", source_anchors=["EV-001"])],
            "chapter_shells": [element("HCH-001", parent_unit_id="HNU-001", order=0, purpose="carry turn")],
            "turning_point_anchors": [element("HST-ANCHOR-001", unit_id="HNU-001", kind="commitment", event_refs=["EV-001"])],
            "entry_exit_state_contracts": [element("HST-STATE-001", unit_id="HNU-001", entry_state_ref="STATE-0", exit_state_ref="STATE-1")],
            "scale_and_flexibility": {"chapter_range": [1, 3], "split_condition": "capacity", "merge_condition": "state intact"},
            "downstream_obligations": [{"id": "OBL-HS1-001", "requirement": "place lines"}],
        })
        model["world_setting_architecture"]["narrative_distribution"] = "Four cities carry distinct jurisdictional, relational, political, and physical-action functions."
        model["world_setting_architecture"]["intercity_routes"].append({"route_id":"HST-ROUTE-C-CAPITAL","from_city_id":"HST-CITY-C-COAST","to_city_id":"HST-CITY-C-CAPITAL","travel_time":"a few hours by secure rail","physical_route":"authorized staff and verified reports travel separately","information_route":"layered conclusions enter the national command chain","custody_rule":"the capital receives authenticated results, not automatically the neutral-country originals","story_function":"laboratory evidence changes diplomatic security decisions"})
        model["world_setting_architecture"]["intercity_routes"].append({"route_id":"HST-ROUTE-CAPITAL-M","from_city_id":"HST-CITY-C-CAPITAL","to_city_id":"HST-CITY-M-NORTH","travel_time":"several hours by direct flight","physical_route":"delegations and technical liaisons travel under separate authority","information_route":"the meeting channel confirms permission without exposing the experiment","custody_rule":"each country retains original records and exchanges authenticated conclusions","story_function":"political permission and local physical action remain separate"})
    elif stage == "HS1":
        model.update({
            "semantic_storyline_register": [element("HTS-REG-001", source_storyline_id="SL-MAIN-001", line_type="main", driver="goal", goal="result", conflict="obstacle", turn="EV-001", payoff="END-001")],
            "storyline_segments": [element("HTS-SEG-001", source_storyline_id="SL-MAIN-001", unit_ids=["HNU-001"], chapter_shell_ids=["HCH-001"], entry_state_ref="STATE-0", exit_state_ref="STATE-1")],
            "unit_storyline_matrix": [element("HTS-MAT-001", unit_id="HNU-001", segment_ids=["HTS-SEG-001"])],
            "storyline_connections": [element("HTC-001", connection_type="causal", from_segment_id="HTS-SEG-001", to_segment_id="HTS-SEG-001", function="event changes line")],
            "convergence_and_split_points": [element("HTC-POINT-001", connection_ids=["HTC-001"], unit_id="HNU-001", point_type="convergence")],
            "event_storyline_placement": [element("HTS-EVT-001", event_id="EV-001", segment_ids=["HTS-SEG-001"], unit_id="HNU-001", function="turn")],
            "activation_disposition": [element("HTS-DISP-001", source_storyline_id="SL-MAIN-001", disposition="placed", authorization_refs=[FREE_ID])],
            "subject_reconstruction_test": {"verdict": "pass", "subject": "authorized subject", "evidence_ids": ["HTS-SEG-001", "HTC-001"]},
        })
    else:
        roles = ["start", "pressure", "choice", "cost", "result"]
        model.update({
            "character_participation_register": [element("HAS-PART-001", character_id="CHR-001", importance="core", storyline_segment_ids=["HTS-SEG-001"], responsibilities=["carry result"], absence_reason=None)],
            "arc_state_models": [element("HAS-MODEL-001", character_id="CHR-001", start_state={"goal": "G0"}, end_state={"goal": "G1"})],
            "arc_steps": [element(f"HAS-STEP-{i:03d}", character_id="CHR-001", role=role, pressure=f"p-{role}", choice=f"c-{role}", cost=f"k-{role}", consequence=f"r-{role}", unit_id="HNU-001", event_id="EV-001", storyline_segment_id="HTS-SEG-001") for i, role in enumerate(roles, 1)],
            "relationship_steps": [element("HRS-001", relationship_id="REL-001", character_ids=["CHR-001", "CHR-002"], state_before={"CHR-001": "distant", "CHR-002": "uncertain"}, state_after={"CHR-001": "trusting", "CHR-002": "committed"}, unit_id="HNU-001", event_id="EV-001")],
            "choice_cost_consequence_links": [element("HAS-CCC-001", character_id="CHR-001", choice_step_id="HAS-STEP-003", cost_step_id="HAS-STEP-004", result_step_id="HAS-STEP-005")],
            "event_character_alignment": [element("HAS-EVT-001", event_id="EV-001", responsible_character_ids=["CHR-001"], result="authorized")],
            "capability_information_permission_checks": [element("HAS-CHECK-001", character_id="CHR-001", event_id="EV-001", capability_ref="CAP-001", information_ref="KNOW-001", permission_ref="PERM-001", verdict="supported")],
        })
    owned = []
    for name in CONTRACT["object_arrays"]:
        owned.extend(item["id"] for item in model[name])
    for name in CONTRACT.get("object_fields", {}):
        owned.append(model[name]["id"])
    model["authority_partition"]["hld_ownership"]["hld_owned"] = owned
    locator = {
        "HA1": "/architecture_choice/form",
        "HS1": "/semantic_storyline_register/0/goal",
        "HC1": "/arc_state_models/0/end_state/goal",
    }[stage]
    model["derivation_claims"] = [{
        "id": "DRV-001", "source_refs": [FREE_ID], "target_locator": locator,
        "value_sha256": canonical_sha256(json_pointer(model, locator)),
    }]
    return model


def build_case(root: Path, defect: str = "none") -> tuple[Path, Path, Path, list[dict]]:
    resolved_case = defect in {"resolved_mustask", "resolved_mustask_missing", "resolved_mustask_wrong"}
    hb0_ref, hb0_files = build_hb0(root, must_ask=resolved_case)
    upstream = [hb0_ref]
    for stage in UPSTREAM[CONTRACT["stage"]][1:]:
        upstream.append(build_design_upstream(root, stage, list(upstream)))
    source_refs = [file_ref(hb0_files["source_index"], root=root, role="source_index"), file_ref(hb0_files["source"], root=root, role="source::intent")]
    resolution_ref = None
    if resolved_case:
        resolution_path = root / "inputs" / "author-resolution.json"
        write_json(resolution_path, {"source_id": OPEN_ID, "answer": "author clarified this control"})
        resolution_ref = file_ref(resolution_path, root=root, role="source::resolution")
        source_refs.append(resolution_ref)
    baseline_manifest = file_ref(hb0_files["manifest"], root=root, role="baseline_manifest")
    baseline_validation = file_ref(hb0_files["validation"], root=root, role="baseline_validation")
    state = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": RUN_ID, "revision": 0,
        "event_sequence": 1, "status": "running", "current_stage": CONTRACT["stage"], "accepted_completions": upstream,
        "current_result_ref": None, "previous_state_ref": None, "revision_plan_ref": None,
        "revision_plan_state_ref": None, "waiting_transaction_ref": None,
    }
    state_path = root / "state-before.json"
    write_json(state_path, state)
    state_ref = file_ref(state_path, root=root, role="state_before")
    allowlist = derive_file_allowlist(
        root, state_ref, baseline_manifest, baseline_validation, source_refs,
        upstream, UPSTREAM[CONTRACT["stage"]],
    )
    projection = project_unresolved(read_json(hb0_files["main"])["unresolved_register"])[CONTRACT["stage"]]
    gate = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": RUN_ID,
        "stage": CONTRACT["stage"], "mode": "forward", "state_before_ref": state_ref,
        "hb0_completion_ref": upstream[0], "upstream_completions": upstream,
        "baseline_manifest_ref": baseline_manifest, "baseline_validation_ref": baseline_validation,
        "source_lineage_refs": source_refs, "exact_owner_skill": CONTRACT["skill"],
        "owner_version": CONTRACT["runtime_version"], "implementation_sha256": implementation_sha256(SKILL),
        "return_binding": None, "unresolved_projection": projection, "revision_plan_ref": None,
        "revision_plan_state_ref": None, "file_allowlist": allowlist,
    }
    gate_path = root / "input-gate.json"
    write_json(gate_path, gate)
    gate_ref = file_ref(gate_path, root=root, role="input_gate")
    order = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": RUN_ID, "revision": 0,
        "work_order_id": f"WO-{CONTRACT['stage']}-001", "task_id": f"TASK-{CONTRACT['stage']}-001",
        "stage": CONTRACT["stage"], "action": "execute", "exact_owner_skill": CONTRACT["skill"],
        "owner_version": CONTRACT["runtime_version"], "implementation_sha256": implementation_sha256(SKILL),
        "event_sequence": 2, "result_timestamp": "2026-08-06T00:00:00Z", "input_gate_ref": gate_ref,
        "state_before_ref": state_ref, "upstream_completions": upstream, "file_allowlist": allowlist,
        "unresolved_projection": projection, "mode": "forward", "return_binding": None,
        "revision_plan_ref": None, "revision_plan_state_ref": None, "output_directory": "output", "submission_status": "open",
    }
    order_path = root / "work-order.json"
    write_json(order_path, order)
    actual_reads = [next(item for item in allowlist if item["role"] == source_ref["role"]) for source_ref in source_refs]
    actual_reads.extend(next(item for item in allowlist if item["role"] == f"upstream::{stage}::main") for stage in UPSTREAM[CONTRACT["stage"]])
    model = stage_model(CONTRACT["stage"], gate_ref, actual_reads)
    if resolved_case:
        model["authority_partition"]["source_classifications"]["open"] = []
        model["authority_partition"]["source_classifications"]["must_ask"] = [OPEN_ID]
        target_array = {
            "HA1": "structural_phases", "HS1": "semantic_storyline_register",
            "HC1": "character_participation_register", "HI1": "unit_pov_assignments",
            "HR1": "narrative_order_map", "HK1": "key_scene_functions",
        }[CONTRACT["stage"]]
        target = model[target_array][0]
        target["source_refs"] = [OPEN_ID]
        target["source_authority_refs"] = [must_ask_authority()]
        target["ownership_class"] = "source_projection"
        target["resolution_ref"] = resolution_ref
        model["authority_partition"]["hld_ownership"]["hld_owned"].remove(target["id"])
        model["authority_partition"]["hld_ownership"]["source_projection"].append(target["id"])
        model["decision_dependencies"] = [dependency(CONTRACT["stage"], resolution_ref)]
        if defect == "resolved_mustask_missing":
            target["resolution_ref"] = None
        elif defect == "resolved_mustask_wrong":
            target["resolution_ref"] = next(item for item in actual_reads if item["role"] == "source::intent")
    if defect == "semantic":
        if CONTRACT["stage"] == "HA1":
            model["turning_point_anchors"] = []
        elif CONTRACT["stage"] == "HS1":
            model["semantic_storyline_register"].append(element("HTS-REG-002", source_storyline_id="SL-SUPPORT-001", line_type="support", driver="goal", goal="G", conflict="C", turn="T", payoff="P"))
            model["activation_disposition"].append(element("HTS-DISP-002", source_storyline_id="SL-SUPPORT-001", disposition="placed", authorization_refs=[FREE_ID]))
        else:
            model["new_relationship"] = {"characters": ["CHR-001", "CHR-003"]}
    elif defect == "boundary":
        model[{"HA1": "scene_actions", "HS1": "pov_assignment", "HC1": "appearance"}[CONTRACT["stage"]]] = "out-of-scope"
    elif defect == "extra_top":
        model["unexpected_control"] = "schema must remain closed"
    elif defect == "object_extra":
        model[{"HA1": "structural_phases", "HS1": "semantic_storyline_register", "HC1": "character_participation_register"}[CONTRACT["stage"]]][0]["unexpected_control"] = True
    elif defect == "object_missing":
        del model[{"HA1": "structural_phases", "HS1": "semantic_storyline_register", "HC1": "character_participation_register"}[CONTRACT["stage"]]][0][{"HA1": "purpose", "HS1": "driver", "HC1": "responsibilities"}[CONTRACT["stage"]]]
    elif defect == "wrong_enum":
        model[{"HA1": "structural_phases", "HS1": "semantic_storyline_register", "HC1": "character_participation_register"}[CONTRACT["stage"]]][0]["ownership_class"] = "author_owned"
    elif defect == "authority_tamper":
        model["authority_partition"]["source_classifications"]["freedom"] = []
    elif defect == "derivation_tamper":
        model["derivation_claims"][0]["value_sha256"] = "0" * 64
    elif defect == "fake_resolution":
        model[{
            "HA1": "structural_phases", "HS1": "semantic_storyline_register",
            "HC1": "character_participation_register", "HI1": "unit_pov_assignments",
            "HR1": "narrative_order_map", "HK1": "key_scene_functions",
        }[CONTRACT["stage"]]][0]["resolution_ref"] = gate_ref
    elif defect in {"unique_solution", "unique_solution_missing_exclusion"}:
        model["design_decisions"][0]["candidate_refs"] = ["OPT-1"]
    draft = root / "draft"
    write_json(draft / "canonical.json", model)
    write_json(draft / "generation-session.json", {"schema_version": "1.0", "skill": CONTRACT["skill"], "task_id": order["task_id"], "actual_read_refs": actual_reads})
    dep = dependency(CONTRACT["stage"], resolution_ref if resolved_case else None)
    evidence = {
        "00-dependency-assessment.json": {"schema_version": "1.0", "assessments": [dep]},
        "01-obligation-analysis.json": {"schema_version": "1.0", "obligations": ["OBL-001"], "open_items": [OPEN_ID], "forbidden": CONTRACT["forbidden_keys"]},
        "02-option-analysis.json": {"schema_version": "1.0", "candidates": [{"id": "OPT-1", "canonical_difference": "placement-a", "tradeoff": "cost-a", "downstream_impact": "impact-a"}, {"id": "OPT-2", "canonical_difference": "placement-b", "tradeoff": "cost-b", "downstream_impact": "impact-b"}], "unique_solution_exclusion_evidence": None},
        "03-projection-analysis.json": {"schema_version": "1.0", "selected": "OPT-1", "projected_ids": [CONTRACT["decision_prefix"] + "001"], "projected_source_ids": projection},
        "04-adversarial-self-review.json": {"schema_version": "1.0", "verdict": "pass", "challenges": [{"id": "CH-001", "claim": "boundary attack", "evidence_ids": [CONTRACT["decision_prefix"] + "001"], "result": "pass"}], "blockers": []},
    }
    if defect in {"unique_solution", "unique_solution_missing_exclusion"}:
        evidence["02-option-analysis.json"]["candidates"] = evidence["02-option-analysis.json"]["candidates"][:1]
        evidence["02-option-analysis.json"]["unique_solution_exclusion_evidence"] = (
            "all other authorized structures violate the frozen downstream contract"
            if defect == "unique_solution" else None
        )
    elif defect == "option_tamper":
        evidence["02-option-analysis.json"]["candidates"][1]["canonical_difference"] = "placement-a"
    elif defect == "projection_tamper":
        evidence["03-projection-analysis.json"]["selected"] = "OPT-NOT-EXIST"
    elif defect == "auxiliary_extra":
        evidence["02-option-analysis.json"]["unexpected"] = True
    for name, value in evidence.items():
        write_json(draft / "generation-evidence" / name, value)
    return order_path, draft, root / "output", upstream


class PublicHarnessCompatibilityTests(unittest.TestCase):
    def run_case(self, defect: str = "none"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        order, draft, output, upstream = build_case(root, defect)
        completed = subprocess.run([sys.executable, str(RUNTIME), str(order), str(draft)], capture_output=True, text=True)
        return temporary, root, order, output, upstream, completed

    def assert_public_envelope(self, root: Path, order_path: Path, output: Path, expected: str) -> dict:
        order = read_json(order_path)
        gate = read_json(root / "input-gate.json")
        result = read_json(output / "stage-result.json")
        CATALOG.validate(order, "work-order.schema.json")
        CATALOG.validate(gate, "input-gate.schema.json")
        CATALOG.validate(result, "stage-result.schema.json")
        validate_result_envelope(result, order)
        manifest_path = verify_file_ref(result["result_manifest_ref"], root)
        manifest = read_json(manifest_path)
        CATALOG.validate(manifest, "package-manifest.schema.json")
        validate_manifest(output / "package", manifest)
        self.assertEqual(result["result"], expected)
        return result

    def test_p01_ready_passes_public_catalog_profile_manifest_completion_and_result(self):
        temporary, root, order, output, _upstream, completed = self.run_case()
        with temporary:
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = self.assert_public_envelope(root, order, output, "ready")
            validate_ready_profile(output / "package", CONTRACT["stage"])
            completion_path = verify_file_ref(result["completion_ref"], root, expected_role="stage_completion")
            completion = read_json(completion_path)
            CATALOG.validate(completion, "stage-completion.schema.json")
            validate_completion_bindings(root, output / "package", completion)
            self.assertEqual(validate_existing(SKILL, order)["result"], "ready")
            manifest_paths = {item["path"] for item in read_json(output / "package" / "package-manifest.json")["files"]}
            self.assertNotIn("package-manifest.json", manifest_paths)
            self.assertNotIn("stage-completion.json", manifest_paths)
            self.assertFalse((output / "package" / "stage-result.json").exists())

    def test_n01_semantic_defect_is_public_revise(self):
        temporary, root, order, output, _upstream, completed = self.run_case("semantic")
        with temporary:
            self.assertEqual(completed.returncode, 2, completed.stderr)
            result = self.assert_public_envelope(root, order, output, "revise")
            self.assertIsNone(result["completion_ref"])
            self.assertEqual(result["revision_class"], "local_candidate")

    def test_b01_boundary_defect_is_public_revise(self):
        temporary, root, order, output, _upstream, completed = self.run_case("boundary")
        with temporary:
            self.assertEqual(completed.returncode, 2, completed.stderr)
            result = self.assert_public_envelope(root, order, output, "revise")
            self.assertIsNone(result["completion_ref"])

    def test_closed_schema_rejects_extra_top_level_field(self):
        temporary, root, order, output, _upstream, completed = self.run_case("extra_top")
        with temporary:
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assert_public_envelope(root, order, output, "revise")
            errors = read_json(output / "package" / "revision-report.json")["errors"]
            self.assertIn("additional property", errors[0])

    def test_closed_schema_rejects_object_extra_and_missing_fields(self):
        for defect, marker in (("object_extra", "additional property"), ("object_missing", "missing required property")):
            with self.subTest(defect=defect):
                temporary, root, order, output, _upstream, completed = self.run_case(defect)
                with temporary:
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assert_public_envelope(root, order, output, "revise")
                    errors = read_json(output / "package" / "revision-report.json")["errors"]
                    self.assertIn(marker, errors[0])

    def test_closed_schema_rejects_wrong_enum_before_semantic_callback(self):
        temporary, root, order, output, _upstream, completed = self.run_case("wrong_enum")
        with temporary:
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assert_public_envelope(root, order, output, "revise")
            errors = read_json(output / "package" / "revision-report.json")["errors"]
            self.assertIn("not in enum", errors[0])

    def test_authority_derivation_option_projection_resolution_and_auxiliary_tamper_are_revise(self):
        defects = (
            "authority_tamper", "derivation_tamper", "option_tamper",
            "projection_tamper", "fake_resolution", "auxiliary_extra",
            "unique_solution_missing_exclusion",
        )
        for defect in defects:
            with self.subTest(defect=defect):
                temporary, root, order, output, _upstream, completed = self.run_case(defect)
                with temporary:
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assert_public_envelope(root, order, output, "revise")

    def test_unique_solution_with_exclusion_evidence_is_ready(self):
        temporary, root, order, output, _upstream, completed = self.run_case("unique_solution")
        with temporary:
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_public_envelope(root, order, output, "ready")

    def test_externally_resolved_must_ask_requires_exact_hdd_resolution_binding(self):
        temporary, root, order, output, _upstream, completed = self.run_case("resolved_mustask")
        with temporary:
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_public_envelope(root, order, output, "ready")
        for defect in ("resolved_mustask_missing", "resolved_mustask_wrong"):
            with self.subTest(defect=defect):
                temporary, root, order, output, _upstream, completed = self.run_case(defect)
                with temporary:
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assert_public_envelope(root, order, output, "revise")

    def test_stale_upstream_manifest_fails_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            order, draft, output, upstream = build_case(root)
            manifest = root / upstream[0]["manifest_path"]
            value = read_json(manifest)
            value["status"] = "blocked"
            write_json(manifest, value)
            completed = subprocess.run([sys.executable, str(RUNTIME), str(order), str(draft)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 3)
            self.assertFalse(output.exists())

    def test_extra_allowlist_ref_fails_exact_closure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            order_path, draft, output, _ = build_case(root)
            extra = root / "inputs" / "extra.json"
            write_json(extra, {"extra": True})
            gate_path = root / "input-gate.json"
            gate = read_json(gate_path)
            gate["file_allowlist"].append(file_ref(extra, root=root, role="source::extra"))
            write_json(gate_path, gate)
            order = read_json(order_path)
            order["file_allowlist"] = gate["file_allowlist"]
            order["input_gate_ref"] = file_ref(gate_path, root=root, role="input_gate")
            write_json(order_path, order)
            completed = subprocess.run([sys.executable, str(RUNTIME), str(order_path), str(draft)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 3)
            self.assertFalse(output.exists())

    def test_unallowlisted_upstream_completion_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            order_path, draft, output, upstream = build_case(root)
            forbidden_path = upstream[-1]["completion_path"]
            gate_path = root / "input-gate.json"
            gate = read_json(gate_path)
            gate["file_allowlist"] = [item for item in gate["file_allowlist"] if item["path"] != forbidden_path]
            write_json(gate_path, gate)
            order = read_json(order_path)
            order["file_allowlist"] = gate["file_allowlist"]
            order["input_gate_ref"] = file_ref(gate_path, root=root, role="input_gate")
            write_json(order_path, order)
            completed = subprocess.run([sys.executable, str(RUNTIME), str(order_path), str(draft)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 3)
            self.assertIn("not pre-authorized", completed.stderr)
            self.assertFalse(output.exists())

    def test_gate_drift_fails_even_when_gate_is_rehashed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            order_path, draft, output, _ = build_case(root)
            gate_path = root / "input-gate.json"
            gate = read_json(gate_path)
            gate["unresolved_projection"] = []
            write_json(gate_path, gate)
            order = read_json(order_path)
            order["input_gate_ref"] = file_ref(gate_path, root=root, role="input_gate")
            write_json(order_path, order)
            completed = subprocess.run([sys.executable, str(RUNTIME), str(order_path), str(draft)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 3)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
