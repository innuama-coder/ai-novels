"""Create and verify the immutable R1 autonomous-skill execution record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from r1_generation_session import (
    SESSION_FILE,
    collect_upstream_evidence_ids,
    sha256 as session_sha256,
    verify_session,
)


SKILL_NAME = "novel-conception-reviewer"
STAGE = "R1"
MODEL_FILE = "review-data.json"
EVIDENCE_SCOPE = "d1_package_only"
EXECUTOR_ROLE = "independent_developer"
RECORD_FILE = "execution-record.json"
SKILL_FILES = (
    "SKILL.md",
    "references/output-contract.md",
    "references/sop.md",
    "scripts/render_conception_review.py",
    "scripts/validate_conception_review.py",
    "scripts/write_r1_completion.py",
    "scripts/execution_record.py",
    "scripts/execute_autonomous.py",
    "scripts/r1_generation_session.py",
    "scripts/manage_generation.py",
    "../novel-development-map-designer/scripts/validate_development_map.py",
    "../../harnesses/novel-conception-interview/validators/validate_stage_completion.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_file_records() -> list[dict[str, str]]:
    root = skill_root()
    return [
        {"path": relative, "sha256": sha256(root / relative)}
        for relative in SKILL_FILES
    ]


def build_record(
    package_dir: Path,
    model: dict[str, Any],
) -> dict[str, Any]:
    model_path = package_dir / MODEL_FILE
    session_errors, session = verify_session(
        package_dir,
        require_open=False,
        model_path=model_path,
    )
    if session_errors:
        raise ValueError("; ".join(session_errors))
    if session.get("run_id") != model.get("run_id"):
        raise ValueError("generation session does not bind the review run")
    if session.get("input_gate_sha256") != canonical_sha256(
        model.get("input_gate")
    ):
        raise ValueError("generation session does not bind the review input gate")
    return {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": model.get("run_id"),
        "stage": STAGE,
        "skill_name": SKILL_NAME,
        "mode": "autonomous_agent",
        "executor_id": session.get("executor_id"),
        "executor_role": EXECUTOR_ROLE,
        "evidence_scope": EVIDENCE_SCOPE,
        "method": session.get("method"),
        "thread_id": session.get("thread_id"),
        "upstream_d1_thread_id": session.get("upstream_d1_thread_id"),
        "generation_session": {
            "path": SESSION_FILE,
            "sha256": session_sha256(package_dir / SESSION_FILE),
            "session_id": session.get("session_id"),
            "chain_head": session.get("chain_head"),
        },
        "model": {"path": MODEL_FILE, "sha256": sha256(model_path)},
        "input_gate_sha256": canonical_sha256(model.get("input_gate")),
        "skill_files": skill_file_records(),
    }


def write_record(
    package_dir: Path,
    model: dict[str, Any],
) -> Path:
    record = build_record(package_dir, model)
    path = package_dir / RECORD_FILE
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def verify_record(
    package_dir: Path,
    model: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    path = package_dir / RECORD_FILE
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{RECORD_FILE} is missing or invalid: {exc}"], {}
    if not isinstance(record, dict):
        return [f"{RECORD_FILE} root is not an object"], {}
    allowed = {
        "schema_version",
        "harness",
        "run_id",
        "stage",
        "skill_name",
        "mode",
        "executor_id",
        "executor_role",
        "evidence_scope",
        "method",
        "thread_id",
        "upstream_d1_thread_id",
        "generation_session",
        "model",
        "input_gate_sha256",
        "skill_files",
    }
    extra = set(record) - allowed
    if extra:
        errors.append(
            f"{RECORD_FILE} contains unsupported fields: "
            + ", ".join(sorted(extra))
        )
    expected_scalars = {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": model.get("run_id"),
        "stage": STAGE,
        "skill_name": SKILL_NAME,
        "mode": "autonomous_agent",
        "executor_role": EXECUTOR_ROLE,
        "evidence_scope": EVIDENCE_SCOPE,
        "input_gate_sha256": canonical_sha256(model.get("input_gate")),
    }
    for field, expected in expected_scalars.items():
        if record.get(field) != expected:
            errors.append(f"{RECORD_FILE}.{field} does not match the R1 run")
    reviewer = model.get("reviewer")
    reviewer_id = reviewer.get("id") if isinstance(reviewer, dict) else None
    if record.get("executor_id") != reviewer_id:
        errors.append(f"{RECORD_FILE}.executor_id must equal reviewer.id")
    if (
        not isinstance(record.get("method"), str)
        or len(record["method"].strip()) < 40
    ):
        errors.append(f"{RECORD_FILE}.method is not auditable")
    session_errors, session = verify_session(
        package_dir,
        require_open=False,
        model_path=package_dir / MODEL_FILE,
    )
    errors.extend(session_errors)
    expected_session = {
        "path": SESSION_FILE,
        "sha256": session_sha256(package_dir / SESSION_FILE)
        if (package_dir / SESSION_FILE).is_file()
        else None,
        "session_id": session.get("session_id"),
        "chain_head": session.get("chain_head"),
    }
    if record.get("generation_session") != expected_session:
        errors.append(f"{RECORD_FILE} does not bind the generation session")
    if record.get("thread_id") != session.get("thread_id"):
        errors.append(f"{RECORD_FILE}.thread_id does not match generation session")
    if record.get("upstream_d1_thread_id") != session.get(
        "upstream_d1_thread_id"
    ):
        errors.append(
            f"{RECORD_FILE}.upstream_d1_thread_id does not match generation session"
        )
    if record.get("executor_id") != session.get("executor_id"):
        errors.append(f"{RECORD_FILE}.executor_id does not match generation session")
    if record.get("method") != session.get("method"):
        errors.append(f"{RECORD_FILE}.method does not match generation session")
    if session.get("run_id") != model.get("run_id"):
        errors.append(f"{SESSION_FILE}.run_id does not match the review model")
    if session.get("input_gate_sha256") != canonical_sha256(
        model.get("input_gate")
    ):
        errors.append(f"{SESSION_FILE} does not bind the review input gate")
    try:
        d1_reference = model["input_gate"]["d1_completion"]["path"]
        d1_completion_path = (package_dir / d1_reference).resolve()
        d1_completion = json.loads(
            d1_completion_path.read_text(encoding="utf-8-sig")
        )
        d1_manifest_path = (
            d1_completion_path.parent / d1_completion["design_artifact"]
        ).resolve()
        d1_record = json.loads(
            (d1_manifest_path.parent / RECORD_FILE).read_text(
                encoding="utf-8-sig"
            )
        )
        actual_d1_thread = d1_record.get("thread_id")
        d1_model_record = d1_record.get("model")
        if not isinstance(d1_model_record, dict) or not isinstance(
            d1_model_record.get("path"), str
        ):
            raise KeyError("model")
        d1_model = json.loads(
            (
                d1_manifest_path.parent / d1_model_record["path"]
            ).read_text(encoding="utf-8-sig")
        )
        expected_task_ids, expected_finding_ids = collect_upstream_evidence_ids(
            d1_model
        )
    except (KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError):
        actual_d1_thread = None
        expected_task_ids = []
        expected_finding_ids = []
    if (
        not actual_d1_thread
        or session.get("upstream_d1_thread_id") != actual_d1_thread
    ):
        errors.append(
            f"{SESSION_FILE}.upstream_d1_thread_id does not bind current D1"
        )
    if session.get("allowed_task_evidence_ids") != expected_task_ids:
        errors.append(
            f"{SESSION_FILE}.allowed_task_evidence_ids do not bind current D1"
        )
    if session.get("allowed_finding_evidence_ids") != expected_finding_ids:
        errors.append(
            f"{SESSION_FILE}.allowed_finding_evidence_ids do not bind current D1"
        )
    expected_model = {"path": MODEL_FILE, "sha256": sha256(package_dir / MODEL_FILE)}
    if record.get("model") != expected_model:
        errors.append(f"{RECORD_FILE} does not bind the current {MODEL_FILE}")
    expected_files = skill_file_records()
    if record.get("skill_files") != expected_files:
        errors.append(f"{RECORD_FILE} does not bind the current skill implementation")
    return errors, {
        "skill_name": record.get("skill_name"),
        "mode": record.get("mode"),
        "executor_id": record.get("executor_id"),
        "skill_files": len(expected_files),
        "model_sha256": expected_model["sha256"],
        "thread_id": record.get("thread_id"),
        "upstream_d1_thread_id": record.get("upstream_d1_thread_id"),
        "generation_session_id": session.get("session_id"),
        "generation_phases": len(session.get("phases", []))
        if isinstance(session.get("phases"), list)
        else 0,
    }
