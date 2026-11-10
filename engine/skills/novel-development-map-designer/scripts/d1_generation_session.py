"""Thread-bound, hash-chained generation sessions for the D1 skill."""
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
    "control-model",
    "gap-and-options",
    "story-architecture",
    "event-world-model",
    "character-model",
    "final-map",
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


def begin_session(
    workspace: Path,
    *,
    run_id: str,
    executor_id: str,
    method: str,
    input_gate: dict[str, Any],
) -> Path:
    workspace = workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise RuntimeError("generation workspace must be new and empty")
    workspace.mkdir(parents=True, exist_ok=True)
    thread_id = current_thread_id()
    if len(method.strip()) < 40:
        raise ValueError("method must be an auditable description of at least 40 chars")
    if not run_id.strip() or not executor_id.strip():
        raise ValueError("run_id and executor_id are required")
    session = {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": run_id,
        "stage": "D1",
        "skill_name": "novel-development-map-designer",
        "assurance": "codex_thread_bound_staged_generation",
        "session_id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "executor_id": executor_id,
        "executor_role": "autonomous_designer",
        "evidence_scope": "authoritative_inputs_only",
        "method": method,
        "status": "open",
        "created_at": now(),
        "input_gate_sha256": canonical_sha256(input_gate),
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
        "control-model": {"run_id", "control_points", "authority_partition"},
        "gap-and-options": {"run_id", "development_gaps", "design_decisions"},
        "story-architecture": {"run_id", "conception", "units"},
        "event-world-model": {"run_id", "conception", "units"},
        "character-model": {"run_id", "conception", "units"},
        "final-map": {"schema_version", "run_id", "input_gate"},
    }[phase]
    missing = required_fields - set(value)
    if missing:
        raise ValueError(
            f"{phase} lacks required fields: {', '.join(sorted(missing))}"
        )
    if phase in {"story-architecture", "event-world-model", "character-model"}:
        conception = value.get("conception")
        if not isinstance(conception, dict):
            raise ValueError(f"{phase}.conception must be an object")
        required_domains = {
            "story-architecture": {"story"},
            "event-world-model": {"story", "world"},
            "character-model": {"story", "world", "characters"},
        }[phase]
        missing_domains = required_domains - set(conception)
        if missing_domains:
            raise ValueError(
                f"{phase}.conception lacks required domains: "
                + ", ".join(sorted(missing_domains))
            )
    if phase == PHASES[-1] and (
        value.get("schema_version") != "4.0"
        or value.get("stage") not in (None, "D1")
    ):
        raise ValueError("final-map must be a D1 map-data 4.0 object")
    if phase == PHASES[-1]:
        # Reject the real-run failure mode before the session is sealed.  The
        # full package validator still remains authoritative after rendering.
        from validate_development_map import Review

        preflight = Review(workspace)
        preflight.validate_content_specificity(value)
        preflight_errors = [
            item for item in preflight.errors if "same-field" in item
        ]
        if preflight_errors:
            raise ValueError(
                "final-map content preflight failed: "
                + "; ".join(preflight_errors)
            )
    target_rel = f"{EVIDENCE_DIR}/{index + 1:02d}-{phase}.json"
    target = workspace / target_rel
    write_json(target, value)
    recorded_at = now()
    prior = session.get("chain_head")
    entry_body = {
        "index": index + 1,
        "phase": phase,
        "artifact": {
            "path": target_rel,
            "sha256": sha256(target),
        },
        "summary": summary,
        "thread_id": session["thread_id"],
        "recorded_at": recorded_at,
        "previous_entry_sha256": prior,
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
        "stage": "D1",
        "skill_name": "novel-development-map-designer",
        "assurance": "codex_thread_bound_staged_generation",
        "executor_role": "autonomous_designer",
        "evidence_scope": "authoritative_inputs_only",
        "required_phases": list(PHASES),
    }
    for field, expected in expected_scalars.items():
        if session.get(field) != expected:
            errors.append(f"{SESSION_FILE}.{field} is invalid")
    if not THREAD_PATTERN.fullmatch(str(session.get("thread_id", ""))):
        errors.append(f"{SESSION_FILE}.thread_id is invalid")
    for field in ("session_id", "executor_id", "method", "created_at"):
        if not isinstance(session.get(field), str) or not session[field].strip():
            errors.append(f"{SESSION_FILE}.{field} is missing")
    if len(str(session.get("method", "")).strip()) < 40:
        errors.append(f"{SESSION_FILE}.method is not auditable")
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
        entry_body = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if entry.get("entry_sha256") != canonical_sha256(entry_body):
            errors.append(f"{SESSION_FILE}.{expected_phase} entry hash is invalid")
        if (
            entry.get("index") != index
            or entry.get("phase") != expected_phase
            or entry.get("previous_entry_sha256") != previous
            or entry.get("thread_id") != session.get("thread_id")
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
        expected_final = phases[-1].get("artifact")
        if session.get("final_model") != expected_final:
            errors.append(f"{SESSION_FILE}.final_model is invalid")
        if model_path is not None and isinstance(expected_final, dict):
            if (
                not model_path.is_file()
                or expected_final.get("sha256") != sha256(model_path)
            ):
                errors.append(f"{SESSION_FILE} does not bind the current model")
    if len(phase_values) == len(PHASES):
        (
            control_model,
            gap_model,
            story_model,
            event_world_model,
            character_model,
            final_model,
        ) = phase_values
        for phase_name, phase_model, fields in (
            (
                "control-model",
                control_model,
                ("run_id", "control_points", "authority_partition"),
            ),
            (
                "gap-and-options",
                gap_model,
                ("run_id", "development_gaps", "design_decisions"),
            ),
            (
                "story-architecture",
                story_model,
                ("run_id", "units"),
            ),
            (
                "event-world-model",
                event_world_model,
                ("run_id", "units"),
            ),
            (
                "character-model",
                character_model,
                ("run_id", "conception", "units"),
            ),
        ):
            if any(phase_model.get(field) != final_model.get(field) for field in fields):
                errors.append(
                    f"{SESSION_FILE}.{phase_name} does not project into final-map"
                )
        final_conception = final_model.get("conception")
        story_conception = story_model.get("conception")
        event_world_conception = event_world_model.get("conception")
        if (
            not isinstance(final_conception, dict)
            or not isinstance(story_conception, dict)
            or story_conception.get("story") != final_conception.get("story")
        ):
            errors.append(
                f"{SESSION_FILE}.story-architecture does not project the "
                "final story model"
            )
        if (
            not isinstance(final_conception, dict)
            or not isinstance(event_world_conception, dict)
            or event_world_conception.get("story") != final_conception.get("story")
            or event_world_conception.get("world") != final_conception.get("world")
        ):
            errors.append(
                f"{SESSION_FILE}.event-world-model does not project the "
                "final story and world models"
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
    target_evidence = package_dir / EVIDENCE_DIR
    if target_evidence.exists():
        shutil.rmtree(target_evidence)
    shutil.copytree(workspace / EVIDENCE_DIR, target_evidence)
    session["status"] = "sealed"
    session["sealed_at"] = now()
    write_json(package_dir / SESSION_FILE, session)
    return session
