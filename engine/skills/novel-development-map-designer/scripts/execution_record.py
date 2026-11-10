"""Create and verify the immutable D1 autonomous-skill execution record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from d1_generation_session import (
    SESSION_FILE,
    sha256 as session_sha256,
    verify_session,
)


SKILL_NAME = "novel-development-map-designer"
STAGE = "D1"
MODEL_FILE = "map-data.json"
EVIDENCE_SCOPE = "authoritative_inputs_only"
EXECUTOR_ROLE = "autonomous_designer"
RECORD_FILE = "execution-record.json"
SKILL_FILES = (
    "SKILL.md",
    "references/output-contract.md",
    "references/sop.md",
    "scripts/render_development_map.py",
    "scripts/validate_development_map.py",
    "scripts/write_d1_completion.py",
    "scripts/execution_record.py",
    "scripts/execute_autonomous.py",
    "scripts/d1_generation_session.py",
    "scripts/manage_generation.py",
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
        raise ValueError("generation session does not bind the model run")
    if session.get("input_gate_sha256") != canonical_sha256(
        model.get("input_gate")
    ):
        raise ValueError("generation session does not bind the model input gate")
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
            errors.append(f"{RECORD_FILE}.{field} does not match the D1 run")
    if (
        not isinstance(record.get("executor_id"), str)
        or not record["executor_id"].strip()
    ):
        errors.append(f"{RECORD_FILE}.executor_id is missing")
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
    if record.get("executor_id") != session.get("executor_id"):
        errors.append(f"{RECORD_FILE}.executor_id does not match generation session")
    if record.get("method") != session.get("method"):
        errors.append(f"{RECORD_FILE}.method does not match generation session")
    if session.get("run_id") != model.get("run_id"):
        errors.append(f"{SESSION_FILE}.run_id does not match the model")
    if session.get("input_gate_sha256") != canonical_sha256(
        model.get("input_gate")
    ):
        errors.append(f"{SESSION_FILE} does not bind the model input gate")
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
        "generation_session_id": session.get("session_id"),
        "generation_phases": len(session.get("phases", []))
        if isinstance(session.get("phases"), list)
        else 0,
    }
