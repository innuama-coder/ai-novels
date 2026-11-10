#!/usr/bin/env python3
"""Run deterministic positive, negative and provenance-boundary fixtures."""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(root: Path, fixture: str, expected_code: int) -> tuple[bool, str]:
    session = root / "evals" / "fixtures" / fixture
    validator = root / "validators" / "validate_session.py"
    renderer = root / "tools" / "render_report.py"
    result = subprocess.run([sys.executable, str(validator), str(session)], capture_output=True, text=True)
    if result.returncode != expected_code:
        return False, f"{fixture}: expected exit {expected_code}, got {result.returncode}: {result.stdout}{result.stderr}"
    if fixture != "negative-unanswered":
        rendered = subprocess.run([sys.executable, str(renderer), str(session)], capture_output=True, text=True)
        if rendered.returncode != 0:
            return False, f"{fixture}: report did not render"
    validation = json.loads((session / "validation.json").read_text(encoding="utf-8"))
    return True, f"{fixture}: {validation['verdict']}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(path: Path) -> dict[str, str]:
    return {"path": path.name, "sha256": sha256(path)}


def relative_reference(base: Path, path: Path) -> dict[str, str]:
    return {
        "path": Path(os.path.relpath(path, base)).as_posix(),
        "sha256": sha256(path),
    }


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def plan_lifecycle_checks(root: Path) -> bool:
    validator = root / "validators" / "validate_session.py"

    def plan(revision: int, budget: int) -> dict:
        return {"harness": "novel-conception-interview", "run_id": "lifecycle-eval", "stage": "I0", "session_id": "lifecycle", "revision": revision, "question_budget": budget, "groups": [{"id": "meaning", "budget": budget}], "planned_minutes": budget * 3, "transcript_assurance": "self_recorded"}

    def blocked(events: list[dict], plans: list[dict], expected_error: str) -> bool:
        with tempfile.TemporaryDirectory() as temp:
            session = Path(temp)
            for item in plans:
                (session / f"plan.v{item['revision']}.json").write_text(json.dumps(item), encoding="utf-8")
            (session / "events.ndjson").write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events), encoding="utf-8")
            result = subprocess.run([sys.executable, str(validator), str(session)], capture_output=True, text=True)
            return result.returncode != 0 and expected_error in result.stdout

    future_revision = blocked([
        {"seq": 1, "type": "plan_presented", "plan_revision": 1, "announced_question_budget": 1, "announced_minutes": 3, "text": "one question"},
        {"seq": 2, "type": "plan_revision", "plan_revision": 2, "author_approved": True, "approval_ref": "author-decision-2", "announced_question_budget": 1, "announced_minutes": 3, "text": "revised plan"},
        {"seq": 3, "type": "question", "question_id": "I0-Q1", "group_id": "meaning", "plan_revision": 1, "text": "question under stale plan"},
        {"seq": 4, "type": "author_answer", "question_id": "I0-Q1", "text": "answer"},
    ], [plan(1, 1), plan(2, 1)], "not bound to the active plan revision")
    early_close = blocked([
        {"seq": 1, "type": "plan_presented", "plan_revision": 1, "announced_question_budget": 2, "announced_minutes": 6, "text": "two questions"},
        {"seq": 2, "type": "question", "question_id": "I0-Q1", "group_id": "meaning", "plan_revision": 1, "text": "first question"},
        {"seq": 3, "type": "author_answer", "question_id": "I0-Q1", "text": "answer"},
        {"seq": 4, "type": "stage_close", "decision": "early_close", "author_approved": True, "plan_revision": 1, "text": "close now"},
    ], [plan(1, 2)], "lacks explicit author approval evidence")
    print(("OK: " if future_revision else "FAIL: ") + "future plan revision is rejected")
    print(("OK: " if early_close else "FAIL: ") + "unreferenced early close is rejected")
    return future_revision and early_close


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    checks = [run(root, "positive-i0", 0), run(root, "negative-unanswered", 1), run(root, "negative-unannounced-plan", 1), run(root, "boundary-self-recorded", 0)]
    for passed, message in checks:
        print(("OK: " if passed else "FAIL: ") + message)
    plan_lifecycle_ok = plan_lifecycle_checks(root)
    boundary_report = (root / "evals" / "fixtures" / "boundary-self-recorded" / "report.md").read_text(encoding="utf-8")
    provenance = "不宣称为外部事件回放" in boundary_report
    print(("OK: " if provenance else "FAIL: ") + "boundary provenance notice")
    positive = root / "evals" / "fixtures" / "positive-i0"
    validation = json.loads((positive / "validation.json").read_text(encoding="utf-8"))
    run_state = positive / "run-state.json"
    run_state.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "active_return": None}), encoding="utf-8")
    design_artifact = positive / "intent-card.md"
    source_lines = design_artifact.read_text(encoding="utf-8-sig").splitlines()
    source_line_number, source_line = next(
        (index, line)
        for index, line in enumerate(source_lines, 1)
        if line.strip() == "## Fixture intent"
    )
    source_end_line = len(source_lines)
    source_section = "\n".join(
        source_lines[source_line_number - 1 : source_end_line]
    )
    source_value = "\n".join(source_lines[source_line_number:]).strip()
    projection = positive / "control-projection.json"
    projection.write_text(json.dumps({
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": validation["run_id"],
        "stage": "I0",
        "session_id": "positive-i0",
        "status": "ready",
        "source_artifact": reference(design_artifact),
        "controls": [{
            "id": "INT-EVAL-001",
            "hardness": "author_locked",
            "heading": "Fixture intent",
            "value": source_value,
        }],
        "evidence_bindings": [{
            "control_id": "INT-EVAL-001",
            "ranges": [{
                "start_line": source_line_number,
                "end_line": source_end_line,
                "text_sha256": text_sha256(source_section),
            }],
        }],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    def stage_projection(stage: str, session_id: str, filename: str) -> dict[str, str]:
        data = json.loads(projection.read_text(encoding="utf-8"))
        prefixes = {"I0": "INT", "I1": "SUB", "I2": "WLD", "I3": "CHR", "I4": "CAU", "I5": "NAR"}
        data["stage"] = stage
        data["session_id"] = session_id
        data["controls"][0]["id"] = f"{prefixes[stage]}-EVAL-001"
        data["evidence_bindings"][0]["control_id"] = data["controls"][0]["id"]
        target = positive / filename
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return reference(target)
    completion_payload = {
        "contract_version": "2.0",
        "harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": "I0", "session_id": "positive-i0", "status": "ready",
        "design_artifact": "intent-card.md", "design_artifact_sha256": sha256(positive / "intent-card.md"),
        "report": {"path": "report.md", "sha256": sha256(positive / "report.md")},
        "validation": {"path": "validation.json", "verdict": "ready", "sha256": sha256(positive / "validation.json")},
        "control_projection": reference(projection),
        "run_state": {"path": "run-state.json", "sha256": sha256(run_state)},
        "input_completions": []
    }
    runtime_completion = positive / "runtime-stage-completion.json"
    runtime_completion.write_text(json.dumps(completion_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    completion = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(runtime_completion)], capture_output=True, text=True)
    completion_ok = completion.returncode == 0
    print(("OK: " if completion_ok else "FAIL: ") + "ready completion is consumable")
    missing_projection_payload = dict(completion_payload)
    missing_projection_payload.pop("control_projection")
    missing_projection_path = positive / "runtime-missing-control-projection.json"
    missing_projection_path.write_text(json.dumps(missing_projection_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    missing_projection = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(missing_projection_path)], capture_output=True, text=True)
    missing_projection_blocked = missing_projection.returncode != 0 and "control projection" in missing_projection.stdout
    print(("OK: " if missing_projection_blocked else "FAIL: ") + "missing I-stage control projection is rejected")
    projection_check = subprocess.run([sys.executable, str(root / "validators" / "validate_control_projection.py"), str(projection)], capture_output=True, text=True)
    projection_ok = projection_check.returncode == 0
    print(("OK: " if projection_ok else "FAIL: ") + "control projection fixture passes canonical validation")
    lossy_projection = positive / "control-projection-lossy.json"
    lossy_projection_data = json.loads(projection.read_text(encoding="utf-8"))
    lossy_projection_data["controls"][0]["value"] = "A plausible paraphrase."
    lossy_projection.write_text(
        json.dumps(lossy_projection_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lossy_result = subprocess.run(
        [
            sys.executable,
            str(root / "validators" / "validate_control_projection.py"),
            str(lossy_projection),
        ],
        capture_output=True,
        text=True,
    )
    lossy_blocked = (
        lossy_result.returncode != 0 and "lossless projection" in lossy_result.stdout
    )
    print(
        ("OK: " if lossy_blocked else "FAIL: ")
        + "hash-bound paraphrase is rejected"
    )
    partial_projection = positive / "control-projection-partial.json"
    partial_projection_data = json.loads(projection.read_text(encoding="utf-8"))
    partial_range = partial_projection_data["evidence_bindings"][0]["ranges"][0]
    partial_range["end_line"] -= 1
    partial_range["text_sha256"] = text_sha256(
        "\n".join(
            source_lines[
                partial_range["start_line"] - 1 : partial_range["end_line"]
            ]
        )
    )
    partial_projection.write_text(
        json.dumps(partial_projection_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    partial_result = subprocess.run(
        [
            sys.executable,
            str(root / "validators" / "validate_control_projection.py"),
            str(partial_projection),
        ],
        capture_output=True,
        text=True,
    )
    partial_blocked = (
        partial_result.returncode != 0 and "complete Markdown section" in partial_result.stdout
    )
    print(
        ("OK: " if partial_blocked else "FAIL: ")
        + "hash-valid partial section is rejected"
    )
    invalid_projection = positive / "control-projection-invalid.json"
    invalid_projection_data = json.loads(projection.read_text(encoding="utf-8"))
    invalid_projection_data["controls"][0]["id"] = "WLD-WRONG-001"
    invalid_projection.write_text(json.dumps(invalid_projection_data, ensure_ascii=False, indent=2), encoding="utf-8")
    invalid_projection_check = subprocess.run([sys.executable, str(root / "validators" / "validate_control_projection.py"), str(invalid_projection)], capture_output=True, text=True)
    invalid_projection_blocked = invalid_projection_check.returncode != 0 and "prefix" in invalid_projection_check.stdout
    print(("OK: " if invalid_projection_blocked else "FAIL: ") + "wrong-stage control prefix is rejected")
    fact_register = positive / "fact-dependency-register.json"
    fact_register.write_text(json.dumps({
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": validation["run_id"],
        "stage": "V1",
        "status": "ready",
        "fact_dependencies": [{
            "id": "FACT-EVAL-001",
            "status": "not_applicable",
            "claim": "This fixture needs no external factual dependency.",
            "rationale": "It tests contract wiring only.",
        }],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    fact_check = subprocess.run([sys.executable, str(root / "validators" / "validate_fact_dependency_register.py"), str(fact_register)], capture_output=True, text=True)
    fact_register_ok = fact_check.returncode == 0
    print(("OK: " if fact_register_ok else "FAIL: ") + "fact dependency fixture passes canonical validation")
    v1_missing_fact = dict(completion_payload)
    v1_missing_fact.update({"stage": "V1", "session_id": "v1-missing-fact"})
    v1_missing_fact.pop("report")
    v1_missing_fact.pop("control_projection")
    v1_missing_fact_path = positive / "runtime-v1-missing-fact-register.json"
    v1_missing_fact_path.write_text(json.dumps(v1_missing_fact, ensure_ascii=False, indent=2), encoding="utf-8")
    v1_missing_fact_result = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(v1_missing_fact_path)], capture_output=True, text=True)
    v1_missing_fact_blocked = v1_missing_fact_result.returncode != 0 and "fact-dependency register" in v1_missing_fact_result.stdout
    print(("OK: " if v1_missing_fact_blocked else "FAIL: ") + "missing V1 fact dependency register is rejected")
    bypass_payload = dict(completion_payload)
    bypass_payload.update({"stage": "I1", "session_id": "bypass-i1", "control_projection": stage_projection("I1", "bypass-i1", "control-projection-bypass-i1.json")})
    runtime_bypass = positive / "runtime-bypass-i1.json"
    runtime_bypass.write_text(json.dumps(bypass_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    bypass = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(runtime_bypass)], capture_output=True, text=True)
    bypass_blocked = bypass.returncode != 0 and "stage bypasses required inputs" in bypass.stdout
    print(("OK: " if bypass_blocked else "FAIL: ") + "bypass completion is rejected")
    return_package = positive / "active-return.json"
    return_package.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "status": "active", "origin_stage": "V1", "target_stage": "I0", "defect": "intent must be clarified", "evidence": ["semantic finding"], "requested_decision": "Clarify the authoritative intent boundary.", "affected_artifacts": ["intent-card.md"]}), encoding="utf-8")
    active_state = positive / "active-run-state.json"
    active_state.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "active_return": reference(return_package)}), encoding="utf-8")
    active_block = dict(completion_payload)
    active_block.update({"stage": "I1", "session_id": "active-return-block", "control_projection": stage_projection("I1", "active-return-block", "control-projection-active-i1.json"), "run_state": reference(active_state)})
    active_block_path = positive / "runtime-active-return-block.json"
    active_block_path.write_text(json.dumps(active_block, ensure_ascii=False, indent=2), encoding="utf-8")
    active_block_result = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(active_block_path)], capture_output=True, text=True)
    active_blocked = active_block_result.returncode != 0 and "active return package blocks further handoff" in active_block_result.stdout
    print(("OK: " if active_blocked else "FAIL: ") + "active return blocks non-target stage")
    return_target = dict(completion_payload)
    return_target.update({"session_id": "return-target-i0", "control_projection": stage_projection("I0", "return-target-i0", "control-projection-return-i0.json"), "run_state": reference(active_state), "return_resolution": reference(return_package)})
    return_target_path = positive / "return-target-i0-completion.json"
    return_target_path.write_text(json.dumps(return_target, ensure_ascii=False, indent=2), encoding="utf-8")
    return_target_result = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(return_target_path)], capture_output=True, text=True)
    return_target_ok = return_target_result.returncode == 0
    print(("OK: " if return_target_ok else "FAIL: ") + "return target can complete with bound resolution")
    nested_target_dir = positive / "nested-return-target"
    nested_target_dir.mkdir(exist_ok=True)
    stage_projection("I0", "nested-return-target-i0", "control-projection-nested-i0.json")
    nested_target = dict(completion_payload)
    nested_target.update({
        "session_id": "nested-return-target-i0",
        "control_projection": relative_reference(nested_target_dir, positive / "control-projection-nested-i0.json"),
        "design_artifact": "../intent-card.md",
        "report": relative_reference(nested_target_dir, positive / "report.md"),
        "validation": {
            "path": "../validation.json",
            "verdict": "ready",
            "sha256": sha256(positive / "validation.json"),
        },
        "run_state": relative_reference(nested_target_dir, active_state),
        "return_resolution": relative_reference(
            nested_target_dir, return_package
        ),
    })
    nested_target_path = nested_target_dir / "stage-completion.json"
    nested_target_path.write_text(
        json.dumps(nested_target, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    nested_target_result = subprocess.run(
        [
            sys.executable,
            str(root / "validators" / "validate_stage_completion.py"),
            str(nested_target_path),
        ],
        capture_output=True,
        text=True,
    )
    nested_target_ok = nested_target_result.returncode == 0
    print(
        ("OK: " if nested_target_ok else "FAIL: ")
        + "cross-directory return references compare by identity"
    )
    resolved_state = positive / "resolved-run-state.json"
    resolved_state.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "active_return": None, "current_interview_completions": {"I0": reference(return_target_path)}, "resolved_returns": [{"return": reference(return_package), "target_completion": reference(return_target_path)}]}), encoding="utf-8")
    corrected_i1 = dict(completion_payload)
    corrected_i1.update({"stage": "I1", "session_id": "post-return-i1", "control_projection": stage_projection("I1", "post-return-i1", "control-projection-post-return-i1.json"), "run_state": reference(resolved_state), "input_completions": [reference(return_target_path)]})
    corrected_i1_path = positive / "runtime-post-return-i1.json"
    corrected_i1_path.write_text(json.dumps(corrected_i1, ensure_ascii=False, indent=2), encoding="utf-8")
    corrected_i1_result = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(corrected_i1_path)], capture_output=True, text=True)
    corrected_i1_ok = corrected_i1_result.returncode == 0
    print(("OK: " if corrected_i1_ok else "FAIL: ") + "resolved return accepts corrected target input")
    stale_i1 = dict(corrected_i1)
    stale_i1["input_completions"] = [reference(runtime_completion)]
    stale_i1_path = positive / "runtime-stale-post-return-i1.json"
    stale_i1_path.write_text(json.dumps(stale_i1, ensure_ascii=False, indent=2), encoding="utf-8")
    stale_i1_result = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(stale_i1_path)], capture_output=True, text=True)
    stale_i1_blocked = stale_i1_result.returncode != 0 and "stage does not consume the current I0 completion" in stale_i1_result.stdout
    print(("OK: " if stale_i1_blocked else "FAIL: ") + "resolved return rejects stale target input")
    d1_artifact = positive / "development-map.md"
    d1_artifact.write_text("# Fixture map\n", encoding="utf-8")
    d1_validation = positive / "d1-validation.json"
    d1_validation.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "verdict": "ready"}), encoding="utf-8")
    semantic = positive / "v1-semantic-review.json"
    semantic.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": "V1", "verdict": "pass", "reviewer_role": "integrity_auditor", "evidence": [
        {"control_area": "intent", "owner_stage": "I0", "artifact": "intent-card.md", "finding": "covered"},
        {"control_area": "subject", "owner_stage": "I1", "artifact": "intent-card.md", "finding": "covered"},
        {"control_area": "world", "owner_stage": "I2", "artifact": "intent-card.md", "finding": "covered"},
        {"control_area": "character", "owner_stage": "I3", "artifact": "intent-card.md", "finding": "covered"},
        {"control_area": "causality", "owner_stage": "I4", "artifact": "intent-card.md", "finding": "covered"},
        {"control_area": "narrative", "owner_stage": "I5", "artifact": "intent-card.md", "finding": "covered"},
    ], "return_package": None}), encoding="utf-8")
    (positive / "v1-completion.json").write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": "V1", "status": "ready", "semantic_review": {"path": "v1-semantic-review.json", "sha256": sha256(semantic)}}), encoding="utf-8")
    (positive / "v2-completion.json").write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": "V2", "status": "ready"}), encoding="utf-8")
    d1_interview_refs = []
    for stage in ("I0", "I1", "I2", "I3", "I4", "I5"):
        stage_path = positive / f"d1-{stage.lower()}-completion.json"
        stage_path.write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": stage, "status": "ready"}), encoding="utf-8")
        d1_interview_refs.append(reference(stage_path))
    d1_state = positive / "d1-run-state.json"
    d1_state.write_text(json.dumps({
        "harness": "novel-conception-interview",
        "run_id": validation["run_id"],
        "active_return": None,
        "current_interview_completions": {
            stage: ref for stage, ref in zip(("I0", "I1", "I2", "I3", "I4", "I5"), d1_interview_refs)
        },
        "resolved_returns": [],
    }), encoding="utf-8")
    d1_without_approval = dict(completion_payload)
    d1_without_approval.update({"stage": "D1", "session_id": "d1-without-approval", "design_artifact": "development-map.md", "design_artifact_sha256": sha256(d1_artifact), "validation": {"path": "d1-validation.json", "verdict": "ready", "sha256": sha256(d1_validation)}, "run_state": reference(d1_state), "input_completions": d1_interview_refs + [reference(positive / "v1-completion.json"), reference(positive / "v2-completion.json")]})
    d1_path = positive / "runtime-d1-without-approval.json"
    d1_path.write_text(json.dumps(d1_without_approval, ensure_ascii=False, indent=2), encoding="utf-8")
    d1 = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(d1_path)], capture_output=True, text=True)
    approval_blocked = d1.returncode != 0 and "legacy D1/R1 stage is not part" in d1.stdout
    print(("OK: " if approval_blocked else "FAIL: ") + "legacy D1 is rejected by the current contract")
    (positive / "d1-completion.json").write_text(json.dumps({"harness": "novel-conception-interview", "run_id": validation["run_id"], "stage": "D1", "status": "ready"}), encoding="utf-8")
    r1_without_approval = dict(d1_without_approval)
    r1_without_approval.update({"stage": "R1", "session_id": "r1-without-approval", "input_completions": [reference(positive / "v1-completion.json"), reference(positive / "v2-completion.json"), reference(positive / "d1-completion.json")]})
    r1_path = positive / "runtime-r1-without-approval.json"
    r1_path.write_text(json.dumps(r1_without_approval, ensure_ascii=False, indent=2), encoding="utf-8")
    r1 = subprocess.run([sys.executable, str(root / "validators" / "validate_stage_completion.py"), str(r1_path)], capture_output=True, text=True)
    final_approval_blocked = r1.returncode != 0 and "legacy D1/R1 stage is not part" in r1.stdout
    print(("OK: " if final_approval_blocked else "FAIL: ") + "legacy R1 is rejected by the current contract")
    return 0 if all(passed for passed, _ in checks) and plan_lifecycle_ok and provenance and completion_ok and missing_projection_blocked and projection_ok and lossy_blocked and partial_blocked and invalid_projection_blocked and fact_register_ok and v1_missing_fact_blocked and bypass_blocked and active_blocked and return_target_ok and nested_target_ok and corrected_i1_ok and stale_i1_blocked and approval_blocked and final_approval_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
