from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
RUNTIME_PATH = SKILL / "scripts" / "baseline_runtime.py"
SPEC = importlib.util.spec_from_file_location("baseline_runtime_test", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


def _write_json(root: Path, relative: str, value: dict) -> dict:
    path = root / relative
    runtime.write_json(path, value)
    return runtime.local_ref(path, root=root)


def _write_text(root: Path, relative: str, text: str = "fixture") -> dict:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    return runtime.local_ref(path, root=root)


def _stage_ref(ref: dict, stage: str) -> dict:
    return {**ref, "stage": stage}


def _manifest(
    root: Path,
    *,
    run_id: str,
    stage: str,
    profile: str,
    roles: dict[str, dict],
    validation: dict,
    implementation: list[dict],
    extra_files: list[dict] | None = None,
    extras: dict | None = None,
) -> dict:
    refs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for ref in [*roles.values(), validation, *implementation, *(extra_files or [])]:
        key = (ref["path"], ref["sha256"])
        if key not in seen:
            seen.add(key)
            refs.append(ref)
    value = {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": stage,
        "package_profile": profile,
        "verdict": "ready",
        "files": refs,
        "artifact_roles": roles,
        "validation": validation,
        "implementation": implementation,
    }
    value.update(extras or {})
    return value


def _review(run_id: str, refs: list[dict], input_gate: dict, handoff_evidence: dict) -> dict:
    def check(check_id: str, scope: str) -> dict:
        return {
            "id": check_id,
            "scope": scope,
            "checked_contract": "fixture contract",
            "method": "deterministic fixture check",
            "evidence_ids": ["INT-001"],
            "conclusion": "pass",
            "result": "pass",
        }

    required_quality_objects = [
        {
            "stage": "S1",
            "id": "SL-001",
            "classification": "s1_obligation",
            "value_sha256": runtime.canonical_sha256(
                {"id": "SL-001", "definition": "storyline"}
            ),
        },
        {
            "stage": "T1",
            "id": "EV-001",
            "classification": "t1_realization",
            "value_sha256": runtime.canonical_sha256(
                {"id": "EV-001", "definition": "event"}
            ),
        },
    ]
    return {
        "schema_version": "2.0",
        "skill": "novel-conception-reviewer",
        "stage": "Q1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": input_gate,
        "domain_reviews": [
            check("CHK-DOMAIN-S1", "S1"),
            check("CHK-DOMAIN-W1", "W1"),
            check("CHK-DOMAIN-E1", "E1"),
            check("CHK-DOMAIN-T1", "T1"),
            check("CHK-DOMAIN-C1", "C1"),
        ],
        "cross_domain_checks": [check("CHK-CROSS-001", "cross-domain")],
        "reality_claim_review": [check("CHK-REALITY-001", "reality")],
        "coverage_recalculation": [check("CHK-COVERAGE-001", "coverage")],
        "consistency_matrix": [check("CHK-CONSISTENCY-001", "consistency")],
        "causal_challenges": [check("CHK-CAUSE-001", "causality")],
        "easy_solution_challenges": [check("CHK-EASY-001", "easy-solution")],
        "development_usability_test": {
            "id": "HANDOFF-FIXTURE",
            "tested_tasks": ["storyline trace"],
            "evidence_ids": ["INT-001"],
            "conclusion": "usable",
            "result": "pass",
        },
        "quality_coverage": {
            "coverage_basis": "all-id-bearing-objects-in-S1-and-T1-canonical-models",
            "required_objects": required_quality_objects,
            "covered_objects": [
                {**required_quality_objects[0], "handoff_check_ids": ["CHK-DOMAIN-S1"]},
                {**required_quality_objects[1], "handoff_check_ids": ["CHK-DOMAIN-T1"]},
            ],
            "unresolved_blocking_quality_record_ids": [],
            "result": "complete",
        },
        "handoff_test_evidence": handoff_evidence,
        "task_isolation": {
            "semantic_task_id": "semantic-fixture",
            "handoff_task_id": "handoff-fixture",
            "handoff_allowlist": refs,
            "forbidden_reads": ["expected answers"],
        },
        "findings": [],
        "return_request": None,
        "verdict": "ready",
    }


def _fixture(base: Path) -> Path:
    source = base / "source"
    output = base / "output"
    source.mkdir()
    run_id = "RUN-FINAL-001"
    common_ref = _write_json(source, "shared/evidence.json", {"fixture": True})
    state_before_ref = _write_json(source, "state/revision-000.json", {"fixture": "state-before"})

    # Q1 package with a formally valid ready review.
    q1_root = source / "Q1"
    q1_input = _write_json(q1_root, "input-gate.json", {"fixture": True})
    q1_handoff = _write_json(q1_root, "sealed-handoff/evidence.json", {"fixture": True})
    allowlist = [
        _write_json(q1_root, f"inputs/input-{index}.json", {"index": index})
        for index in range(6)
    ]
    review_ref = _write_json(q1_root, "conception-review.json", _review(run_id, allowlist, q1_input, q1_handoff))
    q1_roles = {
        "canonical": review_ref,
        "generation_session": _write_json(q1_root, "generation-session.json", {"fixture": True}),
        "generation_evidence_index": _write_json(q1_root, "generation-evidence-index.json", {"fixture": True}),
        "execution_record": _write_json(q1_root, "execution-record.json", {"fixture": True}),
        "preview": _write_text(q1_root, "review-preview.md"),
        "handoff_evidence": q1_handoff,
    }
    q1_validation = _write_json(q1_root, "validation.json", {"verdict": "ready", "errors": []})
    q1_impl = [_write_text(q1_root, "implementation/run_v2.py")]
    q1_manifest_ref = _write_json(
        q1_root,
        "package-manifest.json",
        _manifest(q1_root, run_id=run_id, stage="Q1", profile="independent-review", roles=q1_roles, validation=q1_validation, implementation=q1_impl),
    )

    # P1 authority artifacts and deterministic cross-model index.
    p1_root = source / "P1"
    dummy = _write_json(p1_root, "support/dummy.json", {"fixture": True})
    controls_by_domain = {
        "I0": [
            ("INT-001", "author_locked", "Intent", "Preserve the central idea."),
            ("NAR-OPEN", "author_open", "Narrative question", "Keep the ending interpretation open."),
            ("CAU-OPEN", "author_open", "Causal question", "Keep the causal interpretation open."),
        ],
        "I1": [("SUB-001", "author_locked", "Subject", "Preserve subject agency.")],
        "I2": [("WLD-001", "author_locked", "World", "Preserve the world premise.")],
        "I3": [("CHR-LOCK-001", "author_locked", "Character", "Preserve character identity.")],
        "I4": [("CAU-001", "author_locked", "Causality", "Preserve causal direction.")],
        "I5": [("NAR-001", "author_locked", "Narrative", "Preserve reader knowledge limits.")],
    }
    design_artifacts = []
    registry = []
    design_index_items = []
    for domain, controls in controls_by_domain.items():
        projection = {
            "schema_version": "1.0",
            "harness": "novel-conception-interview",
            "run_id": "INTERVIEW-001",
            "stage": domain,
            "session_id": f"{domain}-fixture",
            "source_artifact": common_ref,
            "controls": [
                {"id": source_id, "hardness": hardness, "heading": heading, "value": value}
                for source_id, hardness, heading, value in controls
            ],
            "evidence_bindings": [],
            "status": "ready",
        }
        baseline_artifact_ref = _write_json(
            source / "B0",
            f"sources/control-projections/{domain}-control-projection.json",
            projection,
        )
        artifact_ref = _write_json(p1_root, f"authoritative-design-artifacts/{domain}.json", projection)
        design_artifacts.append({
            "domain": domain,
            "completion": dummy,
            "artifact": baseline_artifact_ref,
            "control_ids": [item[0] for item in controls],
        })
        design_index_items.append({
            "domain": domain,
            "baseline_artifact": baseline_artifact_ref,
            "materialized": artifact_ref,
        })
        for source_id, hardness, heading, value in controls:
            registry.append({
                "id": source_id,
                "domain": domain,
                "hardness": hardness,
                "artifact": baseline_artifact_ref,
                "heading": heading,
                "value_sha256": runtime.canonical_sha256(value),
            })
    design_index_ref = _write_json(p1_root, "authoritative-design-index.json", {
        "schema_version": "2.0", "run_id": run_id, "artifacts": design_index_items
    })
    author_control = {
        "schema_version": "2.0",
        "stage": "B0",
        "run_id": run_id,
        "source_run_id": "INTERVIEW-001",
        "status": "ready",
        "run_state": dummy,
        "design_artifacts": design_artifacts,
        "v1_completion": dummy,
        "v2_completion": dummy,
        "v2_author_approval": dummy,
        "fact_dependency_register": dummy,
        "control_registry": registry,
        "fact_dependencies": [{
            "id": "FACT-FIXTURE",
            "status": "not_applicable",
            "claim": "No external fact dependency.",
            "rationale": "Fixture uses fictional facts.",
        }],
        "open_items": ["NAR-OPEN", "CAU-OPEN"],
    }
    author_control_ref = _write_json(p1_root, "author-control-baseline.json", author_control)

    model_specs = {
        "S1": ("storyline-architecture.json", "storylines", "SL-001", "storyline"),
        "W1": ("world-model.json", "world_rules", "WF-001", "world rule"),
        "E1": ("environment-system.json", "environments", "ENV-001", "environment"),
        "T1": ("event-timeline.json", "events", "EV-001", "event"),
        "C1": ("character-system.json", "characters", "CHR-001", "character"),
    }
    model_refs = {}
    cross_definitions = []
    for stage, (filename, field, source_id, text) in model_specs.items():
        values = [{"id": source_id, "definition": text}]
        if stage == "C1":
            values.append({"id": "DEV-C1-001", "definition": "HLD may choose chapter placement."})
        document = {
            "schema_version": "2.0",
            "skill": f"fixture-{stage.lower()}",
            "stage": stage,
            "run_id": run_id,
            "status": "ready",
            field: values,
        }
        if stage == "E1":
            operational_slot = {
                "id": "AAB-FIXTURE-OPS",
                "actor_slot_id": "SLOT-FIXTURE-OPS",
            }
            document["actor_authority_bindings"] = [operational_slot]
            cross_definitions.append({
                "id": "SLOT-FIXTURE-OPS",
                "json_pointer": "/actor_authority_bindings/0",
                "kind": "e1_operational_slot",
                "stage": "E1",
                "value_sha256": runtime.canonical_sha256({
                    "slot_id": "SLOT-FIXTURE-OPS",
                    "kind": "e1_operational_slot",
                }),
            })
        if stage == "T1":
            document["planned_event_registry"] = copy.deepcopy(values)
            cross_definitions.append({
                "id": "EV-001",
                "json_pointer": "/planned_event_registry/0",
                "kind": "planned_event_registry",
                "stage": "T1",
                "value_sha256": runtime.canonical_sha256(values[0]),
            })
        model_refs[stage] = _write_json(p1_root, f"canonical-models/{filename}", document)
        for index, value in enumerate(values):
            cross_definitions.append({
                "id": value["id"],
                "json_pointer": f"/{field}/{index}",
                "kind": field,
                "stage": stage,
                "value_sha256": runtime.canonical_sha256(value),
            })
    cross_index = {"schema_version": "2.0", "run_id": run_id, "definitions": cross_definitions, "references": []}
    cross_index_ref = _write_json(p1_root, "cross-model-index.json", cross_index)
    traceability_ref = _write_text(p1_root, "traceability-matrix.md", "# Traceability\n")
    p1_review_ref = _write_json(p1_root, "conception-review.json", {"verdict": "ready"})
    p1_input_ref = _write_json(p1_root, "input-gate.json", {"fixture": True})
    authority_partition = {
        "author_locked": [item["id"] for item in registry if item["hardness"] == "author_locked"],
        "autonomous_owned": ["SL-001", "WF-001", "ENV-001", "EV-001", "CHR-001"],
        "downstream_freedom": ["DEV-C1-001"],
        "author_open": ["NAR-OPEN", "CAU-OPEN"],
    }
    conception = {
        "schema_version": "2.0",
        "skill": "novel-conception-deliverable-assembler",
        "stage": "P1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": p1_input_ref,
        "author_control_baseline": author_control_ref,
        "authoritative_design_artifacts": [item["materialized"] for item in design_index_items],
        "canonical_models": model_refs,
        "review": p1_review_ref,
        "quality_admission": {
            "review": p1_review_ref,
            "coverage_basis": "all-id-bearing-objects-in-S1-and-T1-canonical-models",
            "required_object_count": 2,
            "covered_object_count": 2,
            "unresolved_blocking_quality_record_ids": [],
            "result": "admitted",
        },
        "cross_model_index": cross_index,
        "authority_partition": authority_partition,
        "open_items": [
            {"id": "OPEN-NARRATIVE", "question": "Narrative interpretation?", "source_ids": ["NAR-OPEN"], "status": "author_open"},
            {"id": "OPEN-CAUSAL", "question": "Causal interpretation?", "source_ids": ["CAU-OPEN"], "status": "author_open"},
        ],
        "development_handoff": {"path": "development-handoff.json"},
    }
    conception_ref = _write_json(p1_root, "novel-conception-package.json", conception)
    handoff = {
        "schema_version": "2.0",
        "run_id": run_id,
        "status": "ready",
        "author_control_baseline": author_control_ref,
        "conception_package": conception_ref,
        "mandatory_controls": ["INT-001"],
        "development_freedoms": ["DEV-C1-001"],
        "must_ask": ["NAR-OPEN"],
        "open_items": ["NAR-OPEN", "CAU-OPEN"],
        "development_entrypoint": {"next_stage": "novel-development", "instruction": "Prepare HLD input."},
    }
    handoff_ref = _write_json(p1_root, "development-handoff.json", handoff)
    p1_validation = _write_json(p1_root, "validation.json", {"verdict": "ready", "errors": []})
    p1_spec = _write_text(p1_root, "novel-conception-spec.md", "# Fixture conception\n")
    p1_execution = _write_json(p1_root, "execution-record.json", {"fixture": True})
    p1_impl = [_write_text(p1_root, "implementation/run_v2.py")]
    p1_roles = {
        "conception_package": conception_ref,
        "author_control_baseline": author_control_ref,
        "authoritative_design_index": design_index_ref,
        "spec": p1_spec,
        "cross_model_index": cross_index_ref,
        "traceability": traceability_ref,
        "development_handoff": handoff_ref,
        "execution_record": p1_execution,
    }
    p1_manifest_ref = _write_json(
        p1_root,
        "package-manifest.json",
        _manifest(p1_root, run_id=run_id, stage="P1", profile="conception-package", roles=p1_roles, validation=p1_validation, implementation=p1_impl),
    )

    # H1 HTML package, fully bound by its released manifest profile.
    html_root = source / "H1" / "html"
    html_ref = _write_text(html_root, "human-review-report.html", "<!doctype html><title>Fixture</title>")
    render_ref = _write_json(html_root, "render-record.json", {"fixture": True})
    html_validation = _write_json(html_root, "validation.json", {"verdict": "ready", "errors": []})
    html_impl = [_write_text(html_root, "implementation/run_v2.py")]
    html_manifest_ref = _write_json(
        html_root,
        "package-manifest.json",
        _manifest(
            html_root,
            run_id=run_id,
            stage="H1",
            profile="h1-html",
            roles={"html": html_ref, "render_record": render_ref},
            validation=html_validation,
            implementation=html_impl,
            extras={"session_id": "H1-HTML-FIXTURE", "parent_state_sha256": "0" * 64},
        ),
    )

    # Stage completions are created in contract order.
    stage_refs: dict[str, dict] = {}
    previous_by_stage = {
        "B0": [], "S1": [], "W1": ["S1"], "E1": ["S1", "W1"],
        "T1": ["S1", "W1", "E1"], "C1": ["S1", "W1", "E1", "T1"],
        "Q1": ["S1", "W1", "E1", "T1", "C1"],
        "P1": ["S1", "W1", "E1", "T1", "C1", "Q1"], "H1": ["P1"],
    }
    for stage in runtime.STAGES:
        stage_root = source / "H1" / "stage" if stage == "H1" else source / stage
        if stage == "Q1":
            manifest_ref = runtime.local_ref(q1_root / "package-manifest.json", root=source)
            validation_ref = runtime.local_ref(q1_root / "validation.json", root=source)
            input_ref = runtime.local_ref(q1_root / "input-gate.json", root=source)
        elif stage == "P1":
            manifest_ref = runtime.local_ref(p1_root / "package-manifest.json", root=source)
            validation_ref = runtime.local_ref(p1_root / "validation.json", root=source)
            input_ref = runtime.local_ref(p1_root / "input-gate.json", root=source)
        else:
            local_validation = _write_json(
                stage_root, "validation.json", {"verdict": "ready", "errors": []}
            )
            local_input = _write_json(stage_root, "input-gate.json", {"fixture": True})
            implementation = [_write_text(stage_root, "implementation/run_v2.py")]
            if stage == "B0":
                profile = "baseline"
                roles = {
                    "baseline": _write_json(stage_root, "baseline.json", {"fixture": True}),
                    "control_coverage": _write_json(stage_root, "control-coverage.json", {"fixture": True}),
                    "execution_record": _write_json(stage_root, "execution-record.json", {"fixture": True}),
                }
                extras = None
            elif stage == "H1":
                profile = "h1-stage"
                html_snapshot = stage_root / "sources/html-package-manifest.json"
                html_snapshot.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(html_root / "package-manifest.json", html_snapshot)
                execution = _write_json(
                    stage_root,
                    "execution-record.json",
                    {
                        "workspace_artifacts": {
                            "html_manifest": runtime.local_ref(
                                html_root / "package-manifest.json", root=source
                            )
                        }
                    },
                )
                roles = {
                    "plan_manifest": _write_json(stage_root, "sources/plan-package-manifest.json", {"fixture": True}),
                    "fragment_manifest": _write_json(stage_root, "sources/fragment-package-manifest.json", {"fixture": True}),
                    "assembly_manifest": _write_json(stage_root, "sources/assembly-package-manifest.json", {"fixture": True}),
                    "html_manifest": runtime.local_ref(html_snapshot, root=stage_root),
                }
                extras = {"session_id": "H1-SESSION", "parent_state_sha256": "0" * 64}
                extra_files = [execution]
            else:
                profile = "generated-model"
                roles = {
                    "canonical": _write_json(stage_root, "canonical.json", {"fixture": True}),
                    "generation_session": _write_json(stage_root, "generation-session.json", {"fixture": True}),
                    "generation_evidence_index": _write_json(stage_root, "generation-evidence-index.json", {"fixture": True}),
                    "execution_record": _write_json(stage_root, "execution-record.json", {"fixture": True}),
                    "preview": _write_text(stage_root, "preview.md"),
                }
                extras = None
                extra_files = None
            _write_json(
                stage_root,
                "package-manifest.json",
                _manifest(
                    stage_root,
                    run_id=run_id,
                    stage=stage,
                    profile=profile,
                    roles=roles,
                    validation=local_validation,
                    implementation=implementation,
                    extra_files=extra_files if stage == "H1" else None,
                    extras=extras,
                ),
            )
            manifest_ref = runtime.local_ref(stage_root / "package-manifest.json", root=source)
            validation_ref = runtime.local_ref(stage_root / "validation.json", root=source)
            input_ref = runtime.local_ref(stage_root / "input-gate.json", root=source)
        input_ref = _write_json(
            source,
            f"orchestration/input-gates/revision-{len(stage_refs):03d}-{stage}/input-gate.json",
            {"stage": stage, "fixture": True},
        )
        stage_doc = {
            "schema_version": "2.0",
            "run_id": run_id,
            "stage": stage,
            "status": "ready",
            "manifest": manifest_ref,
            "validation": validation_ref,
            "input_gate": input_ref,
            "state_before": state_before_ref,
            "previous_stage_completions": [stage_refs[item] for item in previous_by_stage[stage]],
            "return_binding": None,
        }
        if stage in {"S1", "W1", "E1", "T1", "C1", "Q1", "H1"}:
            stage_doc["session_id"] = f"{stage}-SESSION"
        completion_relative = (
            "H1/stage/stage-completion.json"
            if stage == "H1"
            else f"{stage}/stage-completion.json"
        )
        ref = _write_json(source, completion_relative, stage_doc)
        stage_refs[stage] = _stage_ref(ref, stage)

    # Author decision and the two-state final transition.
    h1_stage_manifest_ref = runtime.local_ref(
        source / "H1" / "stage" / "package-manifest.json", root=source
    )
    author_decision = {
        "schema_version": "2.0",
        "run_id": run_id,
        "approval_scope": "conception",
        "decision": "approved",
        "machine_package": {
            "completion_path": stage_refs["P1"]["path"],
            "completion_sha256": stage_refs["P1"]["sha256"],
            "manifest_path": runtime.local_ref(p1_root / "package-manifest.json", root=source)["path"],
            "manifest_sha256": p1_manifest_ref["sha256"],
        },
        "human_review_package": {
            "completion_path": stage_refs["H1"]["path"],
            "completion_sha256": stage_refs["H1"]["sha256"],
            "manifest_path": h1_stage_manifest_ref["path"],
            "manifest_sha256": h1_stage_manifest_ref["sha256"],
            "html_path": runtime.local_ref(html_root / "human-review-report.html", root=source)["path"],
            "html_sha256": html_ref["sha256"],
        },
        "approval_record": {"event_seq": 1, "text": "Approved fixture conception."},
        "unresolved_items": ["NAR-OPEN", "CAU-OPEN"],
    }
    decision_ref = _write_json(source, "author-decision.json", author_decision)
    source_interview_ref = _write_json(source, "compatibility/source-interview-state.json", {"fixture": True})
    h1_workspace_ref = _write_json(source, "H1/workspace.json", {"fixture": True})
    previous_state_ref = _write_json(source, "state/revision-008.json", {"fixture": True})
    approval_state = {
        "schema_version": "2.0",
        "workflow": "novel-conception-autonomous-v2",
        "run_id": run_id,
        "revision": 9,
        "status": "approved",
        "source_interview_state": source_interview_ref,
        "current_stage_completions": stage_refs,
        "h1_workspace": h1_workspace_ref,
        "active_return": None,
        "resolved_returns": [],
        "superseded_completions": [],
        "author_decision": decision_ref,
        "development_status": "not_ready",
        "previous_state": previous_state_ref,
    }
    approval_ref = _write_json(source, "state/revision-009.json", approval_state)

    completion_root = source / "completion"
    final_validation = {
        "schema_version": "2.0",
        "run_id": run_id,
        "verdict": "ready",
        "checks": list(runtime.FINAL_CHECKS),
        "p1_validation": runtime.local_ref(p1_root / "validation.json", root=source),
        "h1_html_validation": runtime.local_ref(html_root / "validation.json", root=source),
    }
    final_validation_ref = _write_json(source, "completion/validation.json", final_validation)
    completion = {
        "schema_version": "2.0",
        "run_id": run_id,
        "status": "ready",
        "run_state": approval_ref,
        "stage_completions": stage_refs,
        "p1_manifest": runtime.local_ref(p1_root / "package-manifest.json", root=source),
        "h1_html_manifest": runtime.local_ref(html_root / "package-manifest.json", root=source),
        "author_decision": decision_ref,
        "development_handoff": runtime.local_ref(p1_root / "development-handoff.json", root=source),
        "validation": final_validation_ref,
    }
    _write_json(source, "completion/conception-completion.json", completion)
    finalizer = REPO / "harnesses" / "novel-conception-autonomous" / "runtime" / "final_completion.py"
    target_finalizer = completion_root / "implementation" / "final_completion.py"
    target_finalizer.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(finalizer, target_finalizer)

    current_state = {**copy.deepcopy(approval_state)}
    current_state["revision"] = 10
    current_state["development_status"] = "ready"
    current_state["previous_state"] = approval_ref
    current_ref = _write_json(source, "state/revision-010.json", current_state)
    _write_json(source, "orchestration/current-state.json", {"schema_version": "2.0", "state": current_ref})

    request = {
        "schema_version": "1.0",
        "skill": runtime.SKILL,
        "project_id": "PROJECT-FIXTURE",
        "baseline_version": "1.0.0",
        "source_root": str(source),
        "completion_path": "completion/conception-completion.json",
        "current_state_pointer": "orchestration/current-state.json",
        "release_descriptor": str(REPO / "docs" / "ai-novel-workflow" / "conception-stage-release.json"),
        "contract_dir": str(REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"),
        "finalizer_source": str(finalizer),
        "output_dir": str(output),
        "replace": True,
    }
    request_path = base / "preparation-request.json"
    runtime.write_json(request_path, request)
    return request_path


class BaselineRuntimeTests(unittest.TestCase):
    def test_t1_projection_pair_selects_only_matching_major_event(self) -> None:
        major = {
            "stage": "T1",
            "kind": "major_events",
            "pointer": "/major_events/4",
        }
        planned = {
            "stage": "T1",
            "kind": "planned_event_registry",
            "pointer": "/planned_event_registry/4",
        }
        self.assertIs(major, runtime._control_record([planned, major]))
        self.assertIsNone(runtime._control_record([planned, major, dict(major)]))
        self.assertIsNone(
            runtime._control_record([planned, {**major, "pointer": "/major_events/5"}])
        )
        self.assertIsNone(
            runtime._control_record([planned, {**major, "stage": "S1"}])
        )

    @unittest.skipUnless(os.name == "nt", "Windows extended-path behavior")
    def test_long_source_reference_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "/".join(["nested-segment-" + ("x" * 32)] * 7 + ["artifact.json"])
            target = runtime._physical_path(root).joinpath(*relative.split("/"))
            target.parent.mkdir(parents=True)
            target.write_text('{"ready":true}', encoding="utf-8", newline="")
            resolved = runtime.resolve_relative(root, relative)
            self.assertEqual(target.read_bytes(), resolved.read_bytes())
            self.assertEqual(relative, runtime.local_ref(resolved, root=root)["path"])
            shutil.rmtree(runtime._physical_path(root))

    def test_invalid_request_is_a_runtime_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = Path(temporary) / "preparation-request.json"
            request_path.write_text("not-json", encoding="utf-8")
            with self.assertRaisesRegex(runtime.RuntimeFailure, "invalid preparation request"):
                runtime.load_request(request_path)

    def test_output_directory_must_be_disjoint_from_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            request_path = _fixture(base)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            source = Path(request["source_root"])
            for unsafe_output in (source, source / "generated", source.parent):
                with self.subTest(output_dir=unsafe_output):
                    request["output_dir"] = str(unsafe_output)
                    runtime.write_json(request_path, request)
                    with self.assertRaisesRegex(runtime.RuntimeFailure, "must be disjoint"):
                        runtime.load_request(request_path)

    def test_ready_package_is_generated_and_revalidated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            b0_completion = json.loads(
                (Path(request["source_root"]) / "B0/stage-completion.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                b0_completion["input_gate"]["path"].startswith(
                    "orchestration/input-gates/"
                )
            )
            code, report = runtime.prepare(request_path)
            self.assertEqual(0, code)
            self.assertEqual("pass", report["status"])
            context = runtime.load_request(request_path)
            source = runtime.admit_source(context)
            runtime.validate_ready_package(context.output_dir, source)
            baseline = json.loads((context.output_dir / "development-baseline.json").read_text(encoding="utf-8"))
            overlap = next(item for item in baseline["control_bindings"] if item["source_id"] == "NAR-OPEN")
            self.assertEqual("must_ask", overlap["classification"])
            self.assertTrue(overlap["open_item"])
            self.assertIn("Keep the ending interpretation open.", overlap["source_text"])

    def test_cli_prepare_and_validate_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            prepared = subprocess.run(
                [
                    sys.executable,
                    str(SKILL / "scripts" / "prepare_baseline.py"),
                    str(request_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, prepared.returncode, prepared.stderr or prepared.stdout)
            self.assertEqual("pass", json.loads(prepared.stdout)["status"])
            validated = subprocess.run(
                [
                    sys.executable,
                    str(SKILL / "scripts" / "validate_baseline.py"),
                    str(request_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, validated.returncode, validated.stderr or validated.stdout)
            self.assertEqual("pass", json.loads(validated.stdout)["status"])

    def test_formally_invalid_completion_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            completion_path = Path(request["source_root"]) / request["completion_path"]
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            del completion["stage_completions"]["H1"]
            runtime.write_json(completion_path, completion)
            code, report = runtime.prepare(request_path)
            self.assertEqual(2, code)
            self.assertEqual("blocked", report["status"])
            output = Path(request["output_dir"])
            self.assertEqual(["development-readiness-report.json"], [path.name for path in output.iterdir()])
            self.assertEqual("BASE_FINAL_COMPLETION_SCHEMA_INVALID", report["failed_checks"][0]["code"])

    def test_projection_contract_failure_is_blocked_and_revalidated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            context = runtime.load_request(request_path)
            source = runtime.admit_source(context)
            source.handoff["mandatory_controls"].append("INT-MISSING")
            with patch.object(runtime, "admit_source", return_value=source):
                code, report = runtime.prepare(request_path)
                self.assertEqual(2, code)
                self.assertEqual("blocked", report["status"])
                self.assertEqual(
                    "BASE_CONTROL_DEFINITION_UNRESOLVED",
                    report["failed_checks"][0]["code"],
                )
                self.assertEqual(
                    {"status": "pass", "package_status": "blocked"},
                    runtime.validate_package(context),
                )
            self.assertEqual(
                ["development-readiness-report.json"],
                [path.name for path in context.output_dir.iterdir()],
            )

    def test_fabricated_source_text_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            runtime.prepare(request_path)
            context = runtime.load_request(request_path)
            baseline_path = context.output_dir / "development-baseline.json"
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline["control_bindings"][0]["source_text"] = "fabricated"
            runtime.write_json(baseline_path, baseline)
            source = runtime.admit_source(context)
            with self.assertRaises(runtime.RuntimeFailure):
                runtime.validate_ready_package(context.output_dir, source)

    def test_markdown_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            runtime.prepare(request_path)
            context = runtime.load_request(request_path)
            (context.output_dir / "development-baseline.md").write_text("drift", encoding="utf-8")
            source = runtime.admit_source(context)
            with self.assertRaises(runtime.RuntimeFailure):
                runtime.validate_ready_package(context.output_dir, source)

    def test_manifest_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            runtime.prepare(request_path)
            context = runtime.load_request(request_path)
            manifest_path = context.output_dir / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"][0]["sha256"] = "0" * 64
            runtime.write_json(manifest_path, manifest)
            source = runtime.admit_source(context)
            with self.assertRaises(runtime.RuntimeFailure):
                runtime.validate_ready_package(context.output_dir, source)

    def test_released_finalizer_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            snapshot = Path(request["source_root"]) / "completion/implementation/final_completion.py"
            snapshot.write_text("tampered", encoding="utf-8")
            code, report = runtime.prepare(request_path)
            self.assertEqual(2, code)
            self.assertEqual("BASE_FINALIZER_SNAPSHOT_MISMATCH", report["failed_checks"][0]["code"])

    def test_source_stage_manifest_tampering_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            manifest_path = Path(request["source_root"]) / "B0/package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["verdict"] = "tampered"
            runtime.write_json(manifest_path, manifest)
            code, report = runtime.prepare(request_path)
            self.assertEqual(2, code)
            self.assertEqual("BASE_REF_HASH_MISMATCH", report["failed_checks"][0]["code"])
            self.assertEqual("B0", report["failed_checks"][0]["owner"])

    def test_missing_source_root_is_an_actionable_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["source_root"] = str(Path(temporary) / "missing-source")
            runtime.write_json(request_path, request)
            code, report = runtime.prepare(request_path)
            self.assertEqual(2, code)
            self.assertEqual("BASE_SOURCE_ROOT_MISSING", report["failed_checks"][0]["code"])
            self.assertEqual("conception-final", report["failed_checks"][0]["owner"])

    def test_stale_blocked_report_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            request = json.loads(request_path.read_text(encoding="utf-8"))
            completion_path = Path(request["source_root"]) / request["completion_path"]
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            del completion["stage_completions"]["H1"]
            runtime.write_json(completion_path, completion)
            code, _ = runtime.prepare(request_path)
            self.assertEqual(2, code)
            context = runtime.load_request(request_path)
            report_path = context.output_dir / "development-readiness-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["required_action"] = "Unrelated stale action."
            runtime.write_json(report_path, report)
            with self.assertRaises(runtime.RuntimeFailure):
                runtime.validate_package(context)

    def test_substituted_formal_contract_catalog_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            request_path = _fixture(base)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            contracts = base / "substituted-contracts"
            shutil.copytree(
                REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2",
                contracts,
            )
            changed = contracts / "common-defs.schema.json"
            changed.write_text(changed.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            request["contract_dir"] = str(contracts)
            runtime.write_json(request_path, request)
            code, report = runtime.prepare(request_path)
            self.assertEqual(2, code)
            self.assertEqual("BASE_RELEASE_LOCK_MISMATCH", report["failed_checks"][0]["code"])
            self.assertEqual(
                "contract_catalog_sha256",
                report["failed_checks"][0]["evidence"],
            )

    def test_failed_destination_revalidation_restores_previous_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            request_path = _fixture(Path(temporary))
            code, _ = runtime.prepare(request_path)
            self.assertEqual(0, code)
            context = runtime.load_request(request_path)
            previous = {
                path.name: path.read_bytes()
                for path in context.output_dir.iterdir()
                if path.is_file()
            }
            real_validate = runtime.validate_ready_package
            calls = 0

            def fail_after_publish(output_dir, source):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise runtime.RuntimeFailure("injected destination failure")
                return real_validate(output_dir, source)

            with patch.object(runtime, "validate_ready_package", side_effect=fail_after_publish):
                with self.assertRaisesRegex(runtime.RuntimeFailure, "injected"):
                    runtime.prepare(request_path)
            restored = {
                path.name: path.read_bytes()
                for path in context.output_dir.iterdir()
                if path.is_file()
            }
            self.assertEqual(previous, restored)


if __name__ == "__main__":
    unittest.main()
