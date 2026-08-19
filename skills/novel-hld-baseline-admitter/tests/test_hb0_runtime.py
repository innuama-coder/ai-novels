from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
HARNESS_ROOT = REPO_ROOT / "harnesses" / "novel-hld-autonomous"
UPSTREAM_ROOT = REPO_ROOT / "skills" / "novel-development-baseline-preparer"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import hb0_runtime as runtime  # noqa: E402


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(runtime.canonical_json(value) + "\n", encoding="utf-8", newline="")


def source_ref(workspace: Path, path: Path, domain: str) -> tuple[dict, dict]:
    rel = f"source/{domain}.json"
    source = {"root": "source", "path": rel, "sha256": runtime.sha256_file(path)}
    role = f"source::source::{rel}"
    return source, runtime.make_ref(path, workspace, role)


def build_workspace(root: Path, *, bad_locator: bool = False, illegal_projection: bool = False) -> Path:
    workspace = root / "workspace"
    inputs = workspace / "inputs"
    baseline_dir = inputs / "baseline"
    schemas_dir = inputs / "schemas"
    source_dir = inputs / "source"
    for directory in (baseline_dir, schemas_dir, source_dir):
        directory.mkdir(parents=True)

    domain_ids = {
        "storylines": "SL-001", "world": "WLD-001", "environments": "ENV-001",
        "events": "EV-001", "characters": "CHR-001", "narrative": "NAR-001",
    }
    sources: dict[str, tuple[dict, dict, dict]] = {}
    for domain, source_id in domain_ids.items():
        value = {"id": source_id, "kind": f"{domain}-definition", "payload": f"{domain}-value"}
        if domain == "characters":
            value.update({
                "individual_definition": {
                    "name": "林岚", "identity": "现场调查员",
                    "motivation": "查清事故真相，同时避免无辜者被再次利用。",
                    "temperament": "冷静、谨慎，但不会把程序置于人的安危之上。",
                },
                "story_position": {
                    "entry": "从一份来源可疑的事故记录进入故事。",
                    "function": "连接调查线与人物选择。",
                    "change": "从只相信可核验事实，到愿意承担信任他人的风险。",
                },
            })
        elif domain == "environments":
            value.update({
                "name": "封闭调查室",
                "narrative_responsibility": "让角色在有限信息和时间压力下核对证据并作出选择。",
                "scope": "一间与外部网络隔离、出入受控的临时调查空间。",
                "physical_character": "冷白灯、单向玻璃和持续运转的记录设备构成压迫感。",
                "access_limits": "只有当班调查员可以进入，任何外发材料都必须留下记录。",
            })
        path = source_dir / f"{domain}.json"
        write_json(path, {"value": value})
        ref, allow = source_ref(workspace, path, domain)
        sources[domain] = (value, ref, allow)
    quality_value = {"id": "INT-OPEN", "kind": "quality-question", "payload": "author answer required later"}
    quality_path = source_dir / "quality.json"
    write_json(quality_path, {"value": quality_value})
    quality_ref, quality_allow = source_ref(workspace, quality_path, "quality")

    dummy_ref = sources["storylines"][1]
    lineage_ref = {"root": "source", "path": dummy_ref["path"], "sha256": dummy_ref["sha256"]}
    lineage_keys = (
        "release_descriptor", "conception_completion", "final_validation", "approval_state", "current_state",
        "author_decision", "p1_manifest", "h1_html_manifest", "conception_package", "author_control_baseline",
        "authoritative_design_index", "cross_model_index", "traceability", "development_handoff", "q1_review",
    )
    lineage = {key: dict(lineage_ref) for key in lineage_keys}
    lineage["stage_completions"] = {stage: dict(lineage_ref) for stage in ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1")}
    control_bindings = [
        {
            "source_id": "NAR-001", "classification": "mandatory", "open_item": False,
            "authority_class": "author_locked", "domain": "narrative", "source": sources["narrative"][1],
            "locator": "/value", "source_text": runtime.canonical_json(sources["narrative"][0]),
            "source_value_sha256": runtime.canonical_sha256(sources["narrative"][0]),
            "hld_instruction": "Preserve this narrative control.", "preserve_unresolved": False,
        },
        {
            "source_id": "INT-OPEN", "classification": "must_ask", "open_item": True,
            "authority_class": "author_open", "domain": "quality", "source": quality_ref,
            "locator": "/value", "source_text": runtime.canonical_json(quality_value),
            "source_value_sha256": runtime.canonical_sha256(quality_value),
            "hld_instruction": "Preserve unresolved until the responsible stage assesses it.", "preserve_unresolved": True,
        },
    ]
    for domain in ("characters", "environments"):
        value, ref, _ = sources[domain]
        control_bindings.append({
            "source_id": value["id"], "classification": "mandatory", "open_item": False,
            "authority_class": "author_locked", "domain": domain, "source": ref,
            "locator": "/value", "source_text": runtime.canonical_json(value),
            "source_value_sha256": runtime.canonical_sha256(value),
            "hld_instruction": f"Preserve the complete {domain} definition for human review.",
            "preserve_unresolved": False,
        })
    inventory = {}
    for domain, source_id in domain_ids.items():
        value, ref, _ = sources[domain]
        inventory[domain] = [{
            "source_id": source_id, "source": ref,
            "locator": "/missing" if bad_locator and domain == "events" else "/value",
            "source_value_sha256": runtime.canonical_sha256(value),
            "hld_use": f"Use {source_id} without reinterpretation.",
        }]
    baseline = {
        "schema_version": "2.0", "skill": "novel-development-baseline-preparer", "project_id": "fixture",
        "baseline_version": "1.0.0", "status": "ready",
        "source_release": {"name": "novel-conception-stage", "version": "1.0.0", "status": "frozen", "descriptor_sha256": "0" * 64, "contract_catalog_sha256": "1" * 64, "finalizer_sha256": "2" * 64},
        "run_id": "conception-fixture", "lineage": lineage,
        "input_gate": {key: True for key in ("formal_completion_valid", "released_finalizer_valid", "current_state_valid", "author_approved", "nine_stages_current", "p1_integrity_valid", "h1_integrity_valid", "q1_ready", "one_run_id", "hash_chain_valid")},
        "authority": {"design_authority": "P1", "human_review_role": "verification-only", "conflict_policy": "block-and-route-never-silent-merge"},
        "control_bindings": control_bindings, "design_inventory": inventory,
        "hld_assignment": {"next_stage": "novel-hld", "responsibilities": list(runtime.HLD_RESPONSIBILITIES), "required_capabilities": list(runtime.HLD_CAPABILITIES), "prohibitions": list(runtime.HLD_PROHIBITIONS), "unresolved_author_questions": ["INT-OPEN"]},
        "change_policy": {"local_hld_choice": "decide-only-within-development-freedom", "author_question": "block-affected-decision-and-return-to-author-gate", "conception_conflict": "return-to-earliest-authoritative-owner"},
        "semantic_review": {"review_mode": "deterministic-lossless-projection", "verdict": "pass", "binding_count": 4, "inventory_counts": {domain: 1 for domain in domain_ids}},
    }
    write_json(baseline_dir / "development-baseline.json", baseline)
    (baseline_dir / "development-baseline.md").write_text("# fixture baseline\n", encoding="utf-8")
    baseline_validation = {
        "schema_version": "2.0", "skill": "novel-development-baseline-preparer", "status": "pass", "run_id": "conception-fixture",
        "checks": ["fixture-current"], "errors": [],
        "artifacts": {
            "canonical": {"path": "development-baseline.json", "sha256": runtime.sha256_file(baseline_dir / "development-baseline.json")},
            "human_projection": {"path": "development-baseline.md", "sha256": runtime.sha256_file(baseline_dir / "development-baseline.md")},
        },
    }
    write_json(baseline_dir / "baseline-validation.json", baseline_validation)
    refs = [
        {"path": name, "sha256": runtime.sha256_file(baseline_dir / name)}
        for name in ("development-baseline.json", "development-baseline.md", "baseline-validation.json")
    ]
    manifest = {
        "schema_version": "1.0", "skill": "novel-development-baseline-preparer", "status": "ready",
        "run_id": "conception-fixture", "baseline_version": "1.0.0", "files": refs,
        "artifact_roles": {"canonical": refs[0], "human_projection": refs[1], "validation": refs[2]},
    }
    write_json(baseline_dir / "package-manifest.json", manifest)

    prep_request = {
        "schema_version": "1.0", "skill": "novel-development-baseline-preparer", "project_id": "fixture",
        "baseline_version": "1.0.0", "source_root": "source", "completion_path": "completion.json",
        "current_state_pointer": "state.json", "release_descriptor": "release.json", "contract_dir": "schemas",
        "finalizer_source": "finalizer.py", "output_dir": "baseline", "replace": False,
    }
    write_json(inputs / "preparation-request.json", prep_request)
    run_request = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "project_id": "fixture",
        "hld_run_id": "hld-fixture", "hld_version": "0.1.0", "preparation_request_path": "preparation-request.json",
        "baseline_package_dir": "baseline", "output_root": "hld-output", "author_gate": "required", "replace": False,
    }
    write_json(inputs / "hld-run-request.json", run_request)

    copy_map = {
        "preparation_validator": UPSTREAM_ROOT / "scripts" / "validate_baseline.py",
        "preparation_runtime": UPSTREAM_ROOT / "scripts" / "baseline_runtime.py",
        "preparation_compatibility_lock": SKILL_ROOT / "references" / "preparation-compatibility-lock.json",
        "development_baseline_schema": UPSTREAM_ROOT / "references" / "development-baseline.schema.json",
        "baseline_validation_schema": UPSTREAM_ROOT / "references" / "baseline-validation.schema.json",
        "baseline_manifest_schema": UPSTREAM_ROOT / "references" / "baseline-package-manifest.schema.json",
        "preparation_request_schema": UPSTREAM_ROOT / "references" / "preparation-request.schema.json",
        "upstream_release_lock": UPSTREAM_ROOT / "references" / "supported-release-lock.json",
        "harness_common_schema": HARNESS_ROOT / "schemas" / "common.schema.json",
        "harness_run_request_schema": HARNESS_ROOT / "schemas" / "hld-run-request.schema.json",
        "harness_input_gate_schema": HARNESS_ROOT / "schemas" / "input-gate.schema.json",
        "harness_work_order_schema": HARNESS_ROOT / "schemas" / "work-order.schema.json",
        "harness_run_state_schema": HARNESS_ROOT / "schemas" / "run-state.schema.json",
        "harness_package_manifest_schema": HARNESS_ROOT / "schemas" / "package-manifest.schema.json",
        "harness_stage_completion_schema": HARNESS_ROOT / "schemas" / "stage-completion.schema.json",
        "harness_stage_result_schema": HARNESS_ROOT / "schemas" / "stage-result.schema.json",
        "harness_control_baseline_schema": HARNESS_ROOT / "schemas" / "hld-control-baseline.schema.json",
        "harness_source_index_schema": HARNESS_ROOT / "schemas" / "hld-source-index.schema.json",
        "harness_hb0_validation_schema": HARNESS_ROOT / "schemas" / "hb0-validation.schema.json",
        "harness_hb0_execution_schema": HARNESS_ROOT / "schemas" / "hb0-execution.schema.json",
        "harness_gate_data_schema": HARNESS_ROOT / "schemas" / "gate-data.schema.json",
        "harness_blocked_report_schema": HARNESS_ROOT / "schemas" / "blocked-report.schema.json",
    }
    role_paths = {
        "hld_run_request": inputs / "hld-run-request.json", "preparation_request": inputs / "preparation-request.json",
        "development_baseline": baseline_dir / "development-baseline.json",
        "development_baseline_markdown": baseline_dir / "development-baseline.md",
        "baseline_validation": baseline_dir / "baseline-validation.json", "baseline_manifest": baseline_dir / "package-manifest.json",
    }
    for role, source in copy_map.items():
        target = schemas_dir / f"{role}{source.suffix}"
        shutil.copy2(source, target)
        role_paths[role] = target
    for _, _, allow in sources.values():
        role_paths[allow["role"]] = runtime.resolve_inside(workspace, allow["path"])
    role_paths[quality_allow["role"]] = quality_path
    allowlist = [runtime.make_ref(path, workspace, role) for role, path in sorted(role_paths.items())]

    state = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": "hld-fixture", "revision": 0,
        "event_sequence": 0, "status": "initialized", "current_stage": "HB0", "accepted_completions": [],
        "current_result_ref": None, "previous_state_ref": None, "revision_plan_ref": None,
        "revision_plan_state_ref": None, "waiting_transaction_ref": None,
    }
    write_json(workspace / "revision-000.json", state)
    state_ref = runtime.make_ref(workspace / "revision-000.json", workspace, "state_before")
    projection = ["INT-OPEN"] if illegal_projection else []
    gate = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": "hld-fixture", "stage": "HB0", "mode": "forward",
        "state_before_ref": state_ref, "hb0_completion_ref": None, "upstream_completions": [],
        "baseline_manifest_ref": runtime.make_ref(baseline_dir / "package-manifest.json", workspace, "baseline_manifest"),
        "baseline_validation_ref": runtime.make_ref(baseline_dir / "baseline-validation.json", workspace, "baseline_validation"),
        "source_lineage_refs": [allow for _, _, allow in sources.values()] + [quality_allow],
        "exact_owner_skill": runtime.SKILL, "owner_version": runtime.VERSION, "implementation_sha256": runtime.implementation_sha256(),
        "return_binding": None, "unresolved_projection": projection, "revision_plan_ref": None, "revision_plan_state_ref": None,
        "file_allowlist": allowlist,
    }
    write_json(workspace / "input-gate.json", gate)
    order = {
        "schema_version": "1.0", "harness": "novel-hld-autonomous", "hld_run_id": "hld-fixture", "revision": 0,
        "work_order_id": "WO-HB0-001", "task_id": "TASK-HB0-001", "stage": "HB0", "action": "execute",
        "exact_owner_skill": runtime.SKILL, "owner_version": runtime.VERSION, "implementation_sha256": runtime.implementation_sha256(),
        "event_sequence": 1, "result_timestamp": "2026-08-06T00:00:00Z",
        "input_gate_ref": runtime.make_ref(workspace / "input-gate.json", workspace, "input_gate"), "state_before_ref": state_ref,
        "upstream_completions": [], "file_allowlist": allowlist, "unresolved_projection": projection, "mode": "forward",
        "return_binding": None, "revision_plan_ref": None, "revision_plan_state_ref": None,
        "output_directory": "HB0-package", "submission_status": "open",
    }
    write_json(workspace / "work-order.json", order)
    return workspace / "work-order.json"


class HB0RuntimeTests(unittest.TestCase):
    def test_e1_operational_slot_uses_the_closed_typed_projection(self) -> None:
        item = {
            "source_id": "SLOT-ARCHIVE-CUSTODIAN",
            "domain": "environments",
            "source": {"path": "P1/canonical-models/environment-system.json"},
            "locator": "/actor_authority_bindings/39",
            "expected_hash": runtime.canonical_sha256(
                {"slot_id": "SLOT-ARCHIVE-CUSTODIAN", "kind": "e1_operational_slot"}
            ),
        }
        source_value = {"actor_slot_id": "SLOT-ARCHIVE-CUSTODIAN", "authority": "sealed"}
        self.assertEqual(
            {"slot_id": "SLOT-ARCHIVE-CUSTODIAN", "kind": "e1_operational_slot"},
            runtime._indexed_value(item, source_value),
        )
        self.assertEqual(
            {"slot_id": "SLOT-ARCHIVE-CUSTODIAN", "kind": "e1_operational_slot"},
            runtime._indexed_value(item, "SLOT-ARCHIVE-CUSTODIAN"),
        )
        wrong_slot = {**source_value, "actor_slot_id": "SLOT-OTHER"}
        self.assertIs(wrong_slot, runtime._indexed_value(item, wrong_slot))

    def test_positive_ready_is_reproducible_and_parent_consumable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                code, result = runtime.execute(order)
                validation = runtime.validate_existing(order)
            self.assertEqual(code, 0)
            self.assertEqual(result["result"], "ready")
            self.assertEqual(validation["status"], "pass")
            package = order.parent / "HB0-package"
            control = runtime.read_json(package / "hld-control-baseline.json")
            self.assertEqual([item["source_id"] for item in control["unresolved_register"]], ["INT-OPEN"])
            self.assertNotIn("decision_dependencies", control)
            self.assertTrue((order.parent / "stage-result.json").is_file())
            self.assertFalse((package / "stage-result.json").exists())
            completion = runtime.read_json(package / "stage-completion.json")
            self.assertFalse(any(".hb0-" in ref["path"] for ref in [completion["manifest_ref"], completion["validation_ref"], *completion["canonical_artifacts"]]))
            for ref in [completion["manifest_ref"], completion["validation_ref"], *completion["canonical_artifacts"]]:
                runtime.verify_ref(ref, order.parent)

    def test_negative_committed_completion_rejects_staging_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary))
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                runtime.execute(order)
            package = order.parent / "HB0-package"
            completion_path = package / "stage-completion.json"
            completion = runtime.read_json(completion_path)
            completion["manifest_ref"]["path"] = ".hb0-forbidden/package/package-manifest.json"
            runtime.write_json(completion_path, completion)
            result_path = order.parent / "stage-result.json"
            result = runtime.read_json(result_path)
            result["completion_ref"]["sha256"] = runtime.sha256_file(completion_path)
            runtime.write_json(result_path, result)
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                with self.assertRaisesRegex(runtime.RuntimeFailure, "staging path"):
                    runtime.validate_existing(order)

    def test_negative_invalid_locator_blocks_without_ready_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), bad_locator=True)
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                code, result = runtime.execute(order)
                validation = runtime.validate_existing(order)
            self.assertEqual(code, 2)
            self.assertEqual(result["blocker_class"], "input_invalid")
            self.assertEqual(validation["result"], "blocked")
            package = order.parent / "HB0-package"
            self.assertEqual({path.name for path in package.iterdir()}, {"gate-data.json", "blocked-report.json", "validation.json", "result-manifest.json"})
            self.assertEqual(runtime.read_json(package / "blocked-report.json")["code"], "HB0_LOCATOR_UNRESOLVED")

    def test_negative_self_consistent_but_stale_blocked_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), bad_locator=True)
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                code, _ = runtime.execute(order)
            self.assertEqual(code, 2)
            package = order.parent / "HB0-package"
            report_path = package / "blocked-report.json"
            report = runtime.read_json(report_path)
            report["evidence"] = "tampered-but-rehashed"
            write_json(report_path, report)
            manifest_path = package / "result-manifest.json"
            manifest = runtime.read_json(manifest_path)
            for ref in manifest["files"]:
                if ref["path"] == "blocked-report.json":
                    ref["sha256"] = runtime.sha256_file(report_path)
            manifest["artifact_roles"]["blocked_report"]["sha256"] = runtime.sha256_file(report_path)
            write_json(manifest_path, manifest)
            with patch.object(runtime, "_run_preparation_validator", return_value=None):
                with self.assertRaisesRegex(runtime.RuntimeFailure, "hash mismatch|stale or altered"):
                    runtime.validate_existing(order)

    def test_boundary_hb0_cannot_receive_unresolved_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            order = build_workspace(Path(temporary), illegal_projection=True)
            with self.assertRaises(runtime.RuntimeFailure):
                runtime.load_context(order)
            self.assertFalse((order.parent / "stage-result.json").exists())
            self.assertFalse((order.parent / "HB0-package").exists())


if __name__ == "__main__":
    unittest.main()
