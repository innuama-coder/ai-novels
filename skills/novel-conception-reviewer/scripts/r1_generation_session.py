"""Thread-bound, hash-chained generation sessions for the R1 skill."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SESSION_FILE = "generation-session.json"
EVIDENCE_DIR = "generation-evidence"
THREAD_ENV = "CODEX_THREAD_ID"
THREAD_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
PHASES = (
    "review-plan",
    "semantic-challenges",
    "handoff-test",
    "final-review",
)


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root is not an object")
    return value


def current_thread_id() -> str:
    value = os.environ.get(THREAD_ENV, "").strip()
    if not THREAD_PATTERN.fullmatch(value):
        raise RuntimeError(
            f"{THREAD_ENV} is required and must identify the current Codex task"
        )
    return value.lower()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def collect_upstream_evidence_ids(
    map_data: dict[str, Any],
) -> tuple[list[str], list[str]]:
    def ids(collection: Any) -> set[str]:
        if not isinstance(collection, list):
            return set()
        return {
            str(item["id"])
            for item in collection
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item["id"].strip()
        }

    task_ids = set()
    for key in (
        "control_points",
        "units",
        "information_obligations",
        "derivation_claims",
        "development_gaps",
        "design_decisions",
    ):
        task_ids.update(ids(map_data.get(key)))

    def collect_conception(value: Any) -> None:
        if isinstance(value, dict):
            identifier = value.get("id")
            if isinstance(identifier, str) and identifier.strip():
                task_ids.add(identifier)
            for nested in value.values():
                collect_conception(nested)
        elif isinstance(value, list):
            for nested in value:
                collect_conception(nested)

    collect_conception(map_data.get("conception"))
    finding_ids = task_ids | ids(map_data.get("open_items"))
    return sorted(task_ids), sorted(finding_ids)


def validate_phase_evidence_ids(
    value: dict[str, Any],
    *,
    phase: str,
    task_ids: set[str],
    finding_ids: set[str],
) -> None:
    def check(records: Any, field: str, allowed: set[str], label: str) -> None:
        if not isinstance(records, list):
            return
        unknown: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            evidence = record.get(field)
            if isinstance(evidence, list):
                unknown.update(
                    item
                    for item in evidence
                    if isinstance(item, str) and item not in allowed
                )
        if unknown:
            raise ValueError(
                f"{phase} {label} cites IDs outside the D1 evidence set: "
                + ", ".join(sorted(unknown))
            )

    if phase in {"handoff-test", "final-review"}:
        check(value.get("tasks"), "evidence_ids", task_ids, "tasks")
    if phase == "final-review":
        check(value.get("findings"), "evidence_ids", finding_ids, "findings")


def begin_session(
    workspace: Path,
    *,
    run_id: str,
    executor_id: str,
    method: str,
    input_gate: dict[str, Any],
    upstream_execution_record: Path,
) -> Path:
    workspace = workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise RuntimeError("generation workspace must be new and empty")
    d1_record = read_json(upstream_execution_record.resolve())
    upstream_thread_id = str(d1_record.get("thread_id", "")).lower()
    thread_id = current_thread_id()
    if not THREAD_PATTERN.fullmatch(upstream_thread_id):
        raise ValueError("D1 execution record lacks a valid Codex task ID")
    if upstream_thread_id == thread_id:
        raise RuntimeError("R1 must run in a different Codex task from D1")
    model_record = d1_record.get("model")
    if not isinstance(model_record, dict) or not isinstance(
        model_record.get("path"), str
    ):
        raise ValueError("D1 execution record lacks a model reference")
    d1_model_path = (
        upstream_execution_record.resolve().parent / model_record["path"]
    ).resolve()
    d1_model = read_json(d1_model_path)
    task_evidence_ids, finding_evidence_ids = collect_upstream_evidence_ids(
        d1_model
    )
    workspace.mkdir(parents=True, exist_ok=True)
    if len(method.strip()) < 40:
        raise ValueError("method must be an auditable description of at least 40 chars")
    session = {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": run_id,
        "stage": "R1",
        "skill_name": "novel-conception-reviewer",
        "assurance": "codex_thread_isolated_staged_review",
        "session_id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "upstream_d1_thread_id": upstream_thread_id,
        "executor_id": executor_id,
        "executor_role": "independent_developer",
        "evidence_scope": "d1_package_only",
        "method": method,
        "status": "open",
        "created_at": now(),
        "input_gate_sha256": canonical_sha256(input_gate),
        "allowed_task_evidence_ids": task_evidence_ids,
        "allowed_finding_evidence_ids": finding_evidence_ids,
        "required_phases": list(PHASES),
        "phases": [],
        "chain_head": None,
        "final_model": None,
    }
    write_json(workspace / SESSION_FILE, session)
    return workspace / SESSION_FILE


def load_open_session(workspace: Path) -> dict[str, Any]:
    session = read_json(workspace.resolve() / SESSION_FILE)
    if session.get("status") != "open":
        raise RuntimeError("generation session is not open")
    if session.get("thread_id") != current_thread_id():
        raise RuntimeError("generation session belongs to a different Codex task")
    return session


def submit_phase(
    workspace: Path,
    *,
    phase: str,
    artifact: Path,
    summary: str,
) -> Path:
    workspace = workspace.resolve()
    session = load_open_session(workspace)
    completed = session.get("phases")
    if not isinstance(completed, list):
        raise RuntimeError("generation session phases are invalid")
    index = len(completed)
    if index >= len(PHASES) or phase != PHASES[index]:
        expected = PHASES[index] if index < len(PHASES) else "<complete>"
        raise RuntimeError(f"expected phase {expected}, received {phase}")
    if len(summary.strip()) < 40:
        raise ValueError("phase summary must contain at least 40 characters")
    value = read_json(artifact.resolve())
    required_fields = {
        "review-plan": {
            "run_id",
            "control_area_reviews",
            "conception_reviews",
            "world_model_reviews",
            "major_event_reviews",
            "storyline_reviews",
            "storyline_demand_reviews",
            "storyline_architecture_review",
            "storyline_connection_reviews",
            "melody_line_reviews",
        },
        "semantic-challenges": {
            "run_id",
            "cross_domain_checks",
            "design_decision_reviews",
        },
        "handoff-test": {"run_id", "subject_ids", "tasks"},
        "final-review": {"schema_version", "run_id", "stage", "input_gate"},
    }[phase]
    missing = required_fields - set(value)
    if missing:
        raise ValueError(
            f"{phase} lacks required fields: {', '.join(sorted(missing))}"
        )
    if phase == PHASES[-1] and (
        value.get("schema_version") != "1.0" or value.get("stage") != "R1"
    ):
        raise ValueError("final-review must be an R1 review-data 1.0 object")
    task_ids = session.get("allowed_task_evidence_ids")
    finding_ids = session.get("allowed_finding_evidence_ids")
    if not isinstance(task_ids, list) or not isinstance(finding_ids, list):
        raise RuntimeError("generation session lacks bound D1 evidence IDs")
    validate_phase_evidence_ids(
        value,
        phase=phase,
        task_ids=set(task_ids),
        finding_ids=set(finding_ids),
    )
    target_rel = f"{EVIDENCE_DIR}/{index + 1:02d}-{phase}.json"
    target = workspace / target_rel
    write_json(target, value)
    entry_body = {
        "index": index + 1,
        "phase": phase,
        "artifact": {"path": target_rel, "sha256": sha256(target)},
        "summary": summary,
        "thread_id": session["thread_id"],
        "recorded_at": now(),
        "previous_entry_sha256": session.get("chain_head"),
    }
    entry = dict(entry_body)
    entry["entry_sha256"] = canonical_sha256(entry_body)
    completed.append(entry)
    session["chain_head"] = entry["entry_sha256"]
    if phase == PHASES[-1]:
        session["final_model"] = dict(entry["artifact"])
    write_json(workspace / SESSION_FILE, session)
    return target


def verify_session(
    root: Path,
    *,
    require_open: bool | None = None,
    model_path: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    root = root.resolve()
    try:
        session = read_json(root / SESSION_FILE)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return [f"{SESSION_FILE} is missing or invalid: {exc}"], {}
    expected_scalars = {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "stage": "R1",
        "skill_name": "novel-conception-reviewer",
        "assurance": "codex_thread_isolated_staged_review",
        "executor_role": "independent_developer",
        "evidence_scope": "d1_package_only",
        "required_phases": list(PHASES),
    }
    for field, expected in expected_scalars.items():
        if session.get(field) != expected:
            errors.append(f"{SESSION_FILE}.{field} is invalid")
    thread_id = str(session.get("thread_id", ""))
    upstream = str(session.get("upstream_d1_thread_id", ""))
    if not THREAD_PATTERN.fullmatch(thread_id):
        errors.append(f"{SESSION_FILE}.thread_id is invalid")
    if not THREAD_PATTERN.fullmatch(upstream) or upstream == thread_id:
        errors.append(f"{SESSION_FILE} does not prove a distinct D1/R1 task")
    for field in ("session_id", "executor_id", "method", "created_at"):
        if not isinstance(session.get(field), str) or not session[field].strip():
            errors.append(f"{SESSION_FILE}.{field} is missing")
    if len(str(session.get("method", "")).strip()) < 40:
        errors.append(f"{SESSION_FILE}.method is not auditable")
    for field in (
        "allowed_task_evidence_ids",
        "allowed_finding_evidence_ids",
    ):
        value = session.get(field)
        if (
            not isinstance(value, list)
            or value != sorted(set(value))
            or not all(isinstance(item, str) and item for item in value)
        ):
            errors.append(f"{SESSION_FILE}.{field} is invalid")
    expected_status = "open" if require_open else "sealed"
    if require_open is not None and session.get("status") != expected_status:
        errors.append(f"{SESSION_FILE}.status must be {expected_status}")
    phases = session.get("phases")
    if not isinstance(phases, list) or len(phases) != len(PHASES):
        errors.append(f"{SESSION_FILE}.phases must contain every required phase")
        phases = []
    previous = None
    phase_values: list[dict[str, Any]] = []
    previous_time = session.get("created_at")
    for index, expected_phase in enumerate(PHASES, 1):
        if index > len(phases):
            break
        entry = phases[index - 1]
        if not isinstance(entry, dict):
            errors.append(f"{SESSION_FILE}.phases[{index - 1}] is invalid")
            continue
        body = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if entry.get("entry_sha256") != canonical_sha256(body):
            errors.append(f"{SESSION_FILE}.{expected_phase} entry hash is invalid")
        if (
            entry.get("index") != index
            or entry.get("phase") != expected_phase
            or entry.get("previous_entry_sha256") != previous
            or entry.get("thread_id") != thread_id
        ):
            errors.append(f"{SESSION_FILE}.{expected_phase} chain metadata is invalid")
        artifact_record = entry.get("artifact")
        if not isinstance(artifact_record, dict):
            errors.append(f"{SESSION_FILE}.{expected_phase} artifact is invalid")
        else:
            relative = artifact_record.get("path")
            if (
                not isinstance(relative, str)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                errors.append(f"{SESSION_FILE}.{expected_phase} path is unsafe")
            else:
                artifact_path = root / relative
                if (
                    not artifact_path.is_file()
                    or artifact_record.get("sha256") != sha256(artifact_path)
                ):
                    errors.append(
                        f"{SESSION_FILE}.{expected_phase} artifact hash is invalid"
                    )
                else:
                    try:
                        phase_values.append(read_json(artifact_path))
                    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                        errors.append(
                            f"{SESSION_FILE}.{expected_phase} artifact is not JSON"
                        )
        recorded_at = entry.get("recorded_at")
        try:
            if (
                not isinstance(recorded_at, str)
                or not isinstance(previous_time, str)
                or datetime.fromisoformat(recorded_at)
                < datetime.fromisoformat(previous_time)
            ):
                raise ValueError
            previous_time = recorded_at
        except ValueError:
            errors.append(f"{SESSION_FILE}.{expected_phase} timestamp is invalid")
        previous = entry.get("entry_sha256")
    if session.get("chain_head") != previous:
        errors.append(f"{SESSION_FILE}.chain_head is invalid")
    if phases:
        final = phases[-1].get("artifact")
        if session.get("final_model") != final:
            errors.append(f"{SESSION_FILE}.final_model is invalid")
        if model_path is not None and isinstance(final, dict):
            if not model_path.is_file() or final.get("sha256") != sha256(model_path):
                errors.append(f"{SESSION_FILE} does not bind the current model")
    if len(phase_values) == len(PHASES):
        plan, challenges, handoff, final_review = phase_values
        for phase_name, phase_model, fields in (
            (
                "review-plan",
                plan,
                (
                    "run_id",
                    "control_area_reviews",
                    "conception_reviews",
                    "world_model_reviews",
                    "major_event_reviews",
                    "storyline_reviews",
                    "storyline_demand_reviews",
                    "storyline_architecture_review",
                    "storyline_connection_reviews",
                    "melody_line_reviews",
                ),
            ),
            (
                "semantic-challenges",
                challenges,
                ("run_id", "cross_domain_checks", "design_decision_reviews"),
            ),
            (
                "handoff-test",
                handoff,
                ("run_id", "subject_ids", "tasks"),
            ),
        ):
            if any(
                phase_model.get(field) != final_review.get(field)
                for field in fields
            ):
                errors.append(
                    f"{SESSION_FILE}.{phase_name} does not project into final-review"
                )
    return errors, session


def seal_into_package(workspace: Path, package_dir: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    package_dir = package_dir.resolve()
    session = load_open_session(workspace)
    errors, _ = verify_session(workspace, require_open=True)
    if errors:
        raise RuntimeError("; ".join(errors))
    package_dir.mkdir(parents=True, exist_ok=True)
    target = package_dir / EVIDENCE_DIR
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(workspace / EVIDENCE_DIR, target)
    session["status"] = "sealed"
    session["sealed_at"] = now()
    write_json(package_dir / SESSION_FILE, session)
    return session
