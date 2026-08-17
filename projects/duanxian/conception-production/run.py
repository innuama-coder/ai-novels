from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

S1_LINE_REVIEW_PROTOCOL = "line-claim-and-source-sequence-semantics-v2"

prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)


def _runtime():
    return importlib.import_module("harnesses.novel-conception-autonomous.runtime")


def _paths(run_id: str) -> tuple[Path, Path]:
    run_root = ROOT / "projects" / "duanxian" / "conception-runs" / run_id
    migration = (
        ROOT
        / "projects"
        / "duanxian"
        / "compatibility-migrations"
        / "b0-compat-01"
        / "final"
        / "migration-finalization.json"
    )
    return run_root, migration


def _load_stage_runtime(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load stage runtime: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _s1_runtime():
    return _load_stage_runtime(
        "duanxian_production_s1_runtime",
        "skills/novel-storyline-architecture-designer/scripts/run_v2.py",
    )


STAGE_SPECS: dict[str, dict[str, Any]] = {
    "S1": {
        "actor": "novel-storyline-architecture-designer",
        "module": _s1_runtime,
        "start": "start_s1_session",
        "submit": "submit_s1_phase",
        "finalize": "run_s1",
        "dependencies": (),
    },
    "W1": {
        "actor": "novel-world-model-designer",
        "module_path": "skills/novel-world-model-designer/scripts/run_v2.py",
        "start": "start_w1_session",
        "submit": "submit_w1_phase",
        "finalize": "run_w1",
        "dependencies": ("S1",),
    },
    "E1": {
        "actor": "novel-environment-system-designer",
        "module_path": "skills/novel-environment-system-designer/scripts/run_v2.py",
        "start": "start_e1_session",
        "submit": "submit_e1_phase",
        "finalize": "run_e1",
        "dependencies": ("S1", "W1"),
    },
    "T1": {
        "actor": "novel-event-timeline-designer",
        "module_path": "skills/novel-event-timeline-designer/scripts/run_v2.py",
        "start": "start_t1_session",
        "submit": "submit_t1_phase",
        "finalize": "run_t1",
        "dependencies": ("S1", "W1", "E1"),
    },
    "C1": {
        "actor": "novel-character-system-designer",
        "module_path": "skills/novel-character-system-designer/scripts/run_v2.py",
        "start": "start_c1_session",
        "submit": "submit_c1_phase",
        "finalize": "run_c1",
        "dependencies": ("S1", "W1", "E1", "T1"),
    },
}

PACKAGE_ARGUMENTS = {
    "B0": "baseline_package",
    "S1": "storyline_package",
    "W1": "world_package",
    "E1": "environment_package",
    "T1": "event_package",
    "C1": "character_package",
    "Q1": "review_package",
}


def _stage_runtime(stage: str):
    spec = STAGE_SPECS[stage]
    factory = spec.get("module")
    if factory is not None:
        return factory()
    return _load_stage_runtime(
        f"duanxian_production_{stage.lower()}_runtime",
        str(spec["module_path"]),
    )


def _q1_runtime():
    return _load_stage_runtime(
        "duanxian_production_q1_runtime",
        "skills/novel-conception-reviewer/scripts/run_v2.py",
    )


def _p1_runtime():
    return _load_stage_runtime(
        "duanxian_production_p1_runtime",
        "skills/novel-conception-deliverable-assembler/scripts/run_v2.py",
    )


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("attempt must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("attempt must be a positive integer")
    return parsed


def _workspace(
    run_root: Path,
    stage: str,
    role: str | None = None,
    attempt: int = 1,
) -> Path:
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    suffix = f"-{role}" if role else ""
    return run_root / "workspaces" / f"{stage}{suffix}-attempt-{attempt:02d}"


def _s1_workspace(run_root: Path) -> Path:
    return _workspace(run_root, "S1")


def _sealed_package_arguments(
    order: Any, stages: tuple[str, ...]
) -> dict[str, Path]:
    inputs = order.data.get("inputs", {})
    output: dict[str, Path] = {}
    for stage in stages:
        field = PACKAGE_ARGUMENTS[stage]
        value = inputs.get(field)
        if not isinstance(value, str) or not value:
            raise RuntimeError(f"sealed {order.data.get('action')} work lacks {field}")
        output[field] = Path(value)
    return output


def _sealed_executor_inputs(order: Any) -> dict[str, Any]:
    return {
        key: value
        for key, value in order.data.get("inputs", {}).items()
        if key != "_contract_qualification"
    }


def _issue(run_id: str, action: str, inputs: dict[str, str]) -> tuple[Any, Any, Any]:
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    pending = context.store.pending_work_order()
    if pending is None:
        gate, order = prod.issue_stage_work(
            context,
            action=action,
            inputs=inputs,
        )
    elif pending.data.get("action") == action:
        order = pending
        gate = context.store.load_document(order.data["input_gate"])
    else:
        raise RuntimeError(
            f"cannot issue {action} while {pending.data.get('action')} is pending"
        )
    return context, gate, order


def _issue_result(run_id: str, run_root: Path, gate: Any, order: Any) -> dict[str, object]:
    return {
        "run_id": run_id,
        "action": order.data["action"],
        "actor": order.data["required_actor"],
        "work_order": order.reference,
        "input_gate": gate.reference,
        "run_root": str(run_root),
    }


def _next_phase(session: dict[str, Any], workspace: Path) -> str | None:
    phases = session.get("phases")
    if not isinstance(phases, list):
        return None
    evidence_root = workspace / "generation-evidence"
    completed = len(list(evidence_root.glob("*.json"))) if evidence_root.is_dir() else 0
    return phases[completed] if completed < len(phases) else None


def _load_existing_session(workspace: Path, gate: Any) -> dict[str, Any] | None:
    session_path = workspace / "generation-session.json"
    if not session_path.is_file():
        return None
    session = json.loads(session_path.read_text(encoding="utf-8"))
    if session.get("input_gate") != gate.reference:
        raise RuntimeError(f"existing session is not bound to the current input gate: {workspace}")
    return session


def initialize_b0(run_id: str) -> dict[str, object]:
    rt = _runtime()
    run_root, migration = _paths(run_id)
    handoff = rt.validate_finalized_migration_handoff(migration)
    context = prod.initialize_production_run(
        run_root,
        run_id=run_id,
        source_interview_state={
            "path": "compatibility/source-interview-state.json",
            "sha256": rt.sha256_file(handoff.source_interview_state),
        },
    )
    _, order = prod.issue_stage_work(
        context,
        action="B0",
        inputs={
            "migration_finalization": str(migration),
            "source_run_id": handoff.source_run_id,
        },
    )

    def execute_b0(coordinator, input_gate):
        package = run_root / "B0"
        rt.build_baseline_from_handoff(
            package,
            production_run_id=run_id,
            input_gate=input_gate,
            migration_finalization=migration,
        )
        return rt.complete_b0(
            package,
            coordinator=coordinator,
            input_gate=input_gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="baseline-controller",
        executor=execute_b0,
    )
    return {
        "run_id": run_id,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "run_root": str(run_root),
    }


def status(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    return prod.resume_production_run(run_root).state.data


def issue_s1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    _, gate, order = _issue(run_id, "S1", {})
    result = _issue_result(run_id, run_root, gate, order)
    result["baseline_package"] = order.data["inputs"]["baseline_package"]
    return result


def start_s1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issued = issue_s1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    packages = _sealed_package_arguments(order, ("B0",))
    gate = context.store.load_document(issued["input_gate"])
    workspace = _s1_workspace(run_root)
    session = _load_existing_session(workspace, gate)
    recovered = session is not None
    if session is None:
        session = _s1_runtime().start_s1_session(
            workspace,
            baseline_package=packages["baseline_package"],
            input_gate=gate,
        )
    return {
        **issued,
        "workspace": str(workspace),
        "session_id": session["session_id"],
        "next_phase": _next_phase(session, workspace),
        "recovered": recovered,
    }


def submit_s1(run_id: str, phase: str, payload_path: Path) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issued = issue_s1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    packages = _sealed_package_arguments(order, ("B0",))
    gate = context.store.load_document(issued["input_gate"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    evidence = _s1_runtime().submit_s1_phase(
        _s1_workspace(run_root),
        baseline_package=packages["baseline_package"],
        input_gate=gate,
        phase=phase,
        payload=payload,
    )
    return {
        "run_id": run_id,
        "phase": phase,
        "evidence": evidence,
    }


def start_s1_line_review(run_id: str, payload_path: Path) -> dict[str, object]:
    runtime = _s1_runtime()
    start_review, _ = _require_s1_line_review_v2_api(runtime)
    run_root, _ = _paths(run_id)
    issued = issue_s1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    packages = _sealed_package_arguments(order, ("B0",))
    gate = context.store.load_document(issued["input_gate"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    request = start_review(
        _s1_workspace(run_root),
        baseline_package=packages["baseline_package"],
        input_gate=gate,
        payload=payload,
    )
    sequence_ids = request.get("source_sequence_realization_ids")
    sequence_count = request.get("source_sequence_realization_count")
    sequence_hash = request.get("source_sequence_register_sha256")
    if (
        request.get("review_protocol") != S1_LINE_REVIEW_PROTOCOL
        or not isinstance(sequence_ids, list)
        or not all(isinstance(item, str) and item for item in sequence_ids)
        or len(sequence_ids) != len(set(sequence_ids))
        or not isinstance(sequence_count, int)
        or sequence_count != len(sequence_ids)
        or not isinstance(sequence_hash, str)
        or len(sequence_hash) != 64
    ):
        raise RuntimeError("S1 line review request does not implement protocol v2")
    return {
        "run_id": run_id,
        "candidate_sha256": request["candidate_sha256"],
        "claim_register_sha256": request["claim_register_sha256"],
        "claim_count": len(request["claim_ids"]),
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "source_sequence_realization_count": sequence_count,
        "source_sequence_register_sha256": sequence_hash,
    }


def submit_s1_line_review(
    run_id: str, candidate_sha256: str, review_path: Path
) -> dict[str, object]:
    reviewer_thread_id = _authenticated_reviewer_thread_id(
        "submit-s1-line-review"
    )
    run_root, _ = _paths(run_id)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (
        not isinstance(review, dict)
        or set(review) != {"claim_verdicts", "source_sequence_verdicts"}
        or not isinstance(review["claim_verdicts"], list)
        or not isinstance(review["source_sequence_verdicts"], list)
    ):
        raise RuntimeError(
            "submit-s1-line-review requires an exact protocol-v2 review envelope"
        )
    runtime = _s1_runtime()
    _, submit_review = _require_s1_line_review_v2_api(runtime)
    evidence = submit_review(
        _s1_workspace(run_root),
        candidate_sha256=candidate_sha256,
        review=review,
    )
    return {
        "run_id": run_id,
        "candidate_sha256": candidate_sha256,
        "reviewer_thread_id": reviewer_thread_id,
        "review_evidence": evidence,
    }


def _require_s1_review_api(runtime: Any, name: str):
    api = getattr(runtime, name, None)
    if not callable(api):
        raise RuntimeError(
            f"installed S1 runtime does not provide required review API: {name}"
        )
    return api


def _require_s1_line_review_v2_api(runtime: Any):
    """Fail before writing a request when the installed S1 API is still v1."""

    start_review = _require_s1_review_api(runtime, "start_s1_line_claim_review")
    submit_review = _require_s1_review_api(runtime, "submit_s1_line_claim_review")
    if "review" not in inspect.signature(submit_review).parameters:
        raise RuntimeError(
            "installed S1 runtime does not provide line review protocol v2"
        )
    return start_review, submit_review


def _authenticated_reviewer_thread_id(action: str) -> str:
    """Return the reviewer identity supplied by the Codex runtime.

    The production CLI deliberately has no reviewer-thread argument: accepting
    one would let a caller forge the identity that the S1 review contract is
    meant to authenticate.  The owning skill performs the generation-thread
    separation check when it seals the review evidence.
    """

    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        raise RuntimeError(
            f"{action} requires an authenticated CODEX_THREAD_ID environment"
        )
    return thread_id


def start_s1_topology_review(
    run_id: str, payload_path: Path
) -> dict[str, object]:
    """Freeze the phase-3 topology candidate for independent semantic review."""

    run_root, _ = _paths(run_id)
    issued = issue_s1(run_id)
    context = prod.resume_production_run(run_root)
    gate = context.store.load_document(issued["input_gate"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    runtime = _s1_runtime()
    start_review = _require_s1_review_api(
        runtime, "start_s1_topology_semantic_review"
    )
    request = start_review(
        _s1_workspace(run_root),
        baseline_package=run_root / "B0",
        input_gate=gate,
        payload=payload,
    )
    if not isinstance(request, dict) or not isinstance(
        request.get("candidate_sha256"), str
    ):
        raise RuntimeError("S1 topology review API returned an invalid request")
    dimension_ids = request.get("dimension_ids")
    source_unit_ids = request.get("source_unit_ids")
    if (
        not isinstance(dimension_ids, list)
        or not dimension_ids
        or not all(isinstance(item, str) and item for item in dimension_ids)
        or not isinstance(source_unit_ids, list)
    ):
        raise RuntimeError("S1 topology review request has an invalid contract")
    return {
        "run_id": run_id,
        "candidate_sha256": request["candidate_sha256"],
        "review_kind": request.get("review_kind", "topology-semantic"),
        "review_protocol": request.get("review_protocol"),
        "dimension_ids": dimension_ids,
        "source_unit_count": len(source_unit_ids),
    }


def submit_s1_topology_review(
    run_id: str, candidate_sha256: str, verdicts_path: Path
) -> dict[str, object]:
    """Seal an independent phase-3 semantic review under the real thread ID."""

    reviewer_thread_id = _authenticated_reviewer_thread_id(
        "submit-s1-topology-review"
    )
    run_root, _ = _paths(run_id)
    verdicts = json.loads(verdicts_path.read_text(encoding="utf-8"))
    runtime = _s1_runtime()
    submit_review = _require_s1_review_api(
        runtime, "submit_s1_topology_semantic_review"
    )
    evidence = submit_review(
        _s1_workspace(run_root),
        candidate_sha256=candidate_sha256,
        verdicts=verdicts,
    )
    return {
        "run_id": run_id,
        "candidate_sha256": candidate_sha256,
        "reviewer_thread_id": reviewer_thread_id,
        "review_evidence": evidence,
    }


def finalize_s1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "S1":
        raise RuntimeError("current pending work order is not S1")

    sealed_inputs = _sealed_executor_inputs(order)

    def execute_s1(coordinator, input_gate, inputs):
        return _s1_runtime().run_s1(
            run_root / "S1",
            baseline_package=Path(inputs["baseline_package"]),
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=_s1_workspace(run_root),
            logical_package_path="S1",
            next_state_path="state/revision-002.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-storyline-architecture-designer",
        executor=execute_s1,
        input_bindings=sealed_inputs,
    )
    return {
        "run_id": run_id,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "storyline_count": len(receipt.model["storylines"]),
        "obligation_count": len(receipt.model["story_obligation_register"]),
    }


def issue_stage(run_id: str, stage: str) -> dict[str, object]:
    if stage == "S1":
        return issue_s1(run_id)
    run_root, _ = _paths(run_id)
    dependencies = tuple(STAGE_SPECS[stage]["dependencies"])
    _, gate, order = _issue(
        run_id,
        stage,
        {},
    )
    result = _issue_result(run_id, run_root, gate, order)
    result["packages"] = {
        key: value
        for key, value in order.data["inputs"].items()
        if key != "_contract_qualification"
    }
    return result


def start_stage(
    run_id: str, stage: str, attempt: int = 1
) -> dict[str, object]:
    if stage == "S1":
        return start_s1(run_id)
    run_root, _ = _paths(run_id)
    issued = issue_stage(run_id, stage)
    context = prod.resume_production_run(run_root)
    gate = context.store.load_document(issued["input_gate"])
    order = context.store.pending_work_order()
    workspace = _workspace(run_root, stage, attempt=attempt)
    dependencies = tuple(STAGE_SPECS[stage]["dependencies"])
    runtime = _stage_runtime(stage)
    session = getattr(runtime, STAGE_SPECS[stage]["start"])(
        workspace,
        **_sealed_package_arguments(order, ("B0", *dependencies)),
        input_gate=gate,
    )
    return {
        **issued,
        "attempt": attempt,
        "workspace": str(workspace),
        "session_id": session["session_id"],
        "next_phase": _next_phase(session, workspace),
    }


def submit_stage(
    run_id: str,
    stage: str,
    phase: str,
    payload_path: Path,
    attempt: int = 1,
) -> dict[str, object]:
    if stage == "S1":
        return submit_s1(run_id, phase, payload_path)
    run_root, _ = _paths(run_id)
    issued = issue_stage(run_id, stage)
    context = prod.resume_production_run(run_root)
    gate = context.store.load_document(issued["input_gate"])
    order = context.store.pending_work_order()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    dependencies = tuple(STAGE_SPECS[stage]["dependencies"])
    workspace = _workspace(run_root, stage, attempt=attempt)
    evidence = getattr(_stage_runtime(stage), STAGE_SPECS[stage]["submit"])(
        workspace,
        **_sealed_package_arguments(order, ("B0", *dependencies)),
        input_gate=gate,
        phase=phase,
        payload=payload,
    )
    return {
        "run_id": run_id,
        "stage": stage,
        "phase": phase,
        "attempt": attempt,
        "workspace": str(workspace),
        "evidence": evidence,
    }


def finalize_stage(
    run_id: str, stage: str, attempt: int = 1
) -> dict[str, object]:
    if stage == "S1":
        return finalize_s1(run_id)
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != stage:
        raise RuntimeError(f"current pending work order is not {stage}")
    dependencies = tuple(STAGE_SPECS[stage]["dependencies"])
    workspace = _workspace(run_root, stage, attempt=attempt)
    sealed_inputs = _sealed_executor_inputs(order)

    def execute_stage(coordinator, input_gate, inputs):
        return getattr(_stage_runtime(stage), STAGE_SPECS[stage]["finalize"])(
            run_root / stage,
            **{
                PACKAGE_ARGUMENTS[item]: Path(inputs[PACKAGE_ARGUMENTS[item]])
                for item in ("B0", *dependencies)
            },
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path=stage,
            next_state_path=f"state/revision-{context.state.data['revision'] + 1:03d}.json",
            active_return_request=context.active_return,
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor=str(STAGE_SPECS[stage]["actor"]),
        executor=execute_stage,
        input_bindings=sealed_inputs,
    )
    return {
        "run_id": run_id,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "attempt": attempt,
        "workspace": str(workspace),
        "state_revision": successor.state.data["revision"],
        "completion": receipt.completion.reference,
    }


def issue_q1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    stages = ("B0", "S1", "W1", "E1", "T1", "C1")
    _, gate, order = _issue(run_id, "Q1", {})
    result = _issue_result(run_id, run_root, gate, order)
    result["packages"] = _sealed_executor_inputs(order)
    result["controller_workspace"] = str(_workspace(run_root, "Q1", "controller"))
    result["semantic_workspace"] = str(_workspace(run_root, "Q1", "semantic"))
    result["handoff_workspace"] = str(_workspace(run_root, "Q1", "handoff"))
    return result


def _q1_package_arguments(order: Any) -> dict[str, Path]:
    return _sealed_package_arguments(
        order, ("B0", "S1", "W1", "E1", "T1", "C1")
    )


def start_q1_controller(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issued = issue_q1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    gate = context.store.load_document(issued["input_gate"])
    frozen = _q1_runtime().start_q1_controller(
        _workspace(run_root, "Q1", "controller"),
        **_q1_package_arguments(order),
        input_gate=gate,
    )
    return {
        **issued,
        "controller_identity": frozen["controller_identity"],
        "status": "inputs_frozen",
    }


def start_q1_semantic(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issued = issue_q1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    gate = context.store.load_document(issued["input_gate"])
    session = _q1_runtime().start_semantic_review(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "semantic"),
        **_q1_package_arguments(order),
        input_gate=gate,
    )
    return {
        **issued,
        "session_id": session["session_id"],
        "phases": session["phases"],
        "identity": session["identity"],
    }


def submit_q1_semantic(
    run_id: str, phase: str, payload_path: Path
) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issue_q1(run_id)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    evidence = _q1_runtime().submit_semantic_phase(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "semantic"),
        phase=phase,
        payload=payload,
    )
    return {"run_id": run_id, "phase": phase, "evidence": evidence}


def start_q1_handoff(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issued = issue_q1(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    session = _q1_runtime().start_handoff_review(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "handoff"),
        **_q1_package_arguments(order),
    )
    return {
        **issued,
        "session_id": session["session_id"],
        "identity": session["identity"],
        "forbidden_reads": session["forbidden_reads"],
    }


def seal_q1_handoff(run_id: str, payload_path: Path) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issue_q1(run_id)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    evidence = _q1_runtime().seal_handoff_review(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "handoff"),
        payload=payload,
    )
    return {"run_id": run_id, "evidence": evidence}


def import_q1_handoff(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issue_q1(run_id)
    evidence = _q1_runtime().import_sealed_handoff(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "semantic"),
        _workspace(run_root, "Q1", "handoff"),
    )
    return {"run_id": run_id, "evidence": evidence}


def submit_q1_final(run_id: str, payload_path: Path) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    issue_q1(run_id)
    review = json.loads(payload_path.read_text(encoding="utf-8"))
    evidence = _q1_runtime().submit_final_review(
        _workspace(run_root, "Q1", "controller"),
        _workspace(run_root, "Q1", "semantic"),
        review=review,
    )
    return {"run_id": run_id, "evidence": evidence}


def finalize_q1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "Q1":
        raise RuntimeError("current pending work order is not Q1")

    sealed_inputs = _sealed_executor_inputs(order)

    def execute_q1(coordinator, input_gate, inputs):
        return _q1_runtime().run_q1(
            run_root / "Q1",
            **{
                PACKAGE_ARGUMENTS[item]: Path(inputs[PACKAGE_ARGUMENTS[item]])
                for item in ("B0", "S1", "W1", "E1", "T1", "C1")
            },
            coordinator=coordinator,
            input_gate=input_gate,
            controller_workspace=_workspace(run_root, "Q1", "controller"),
            semantic_workspace=_workspace(run_root, "Q1", "semantic"),
            handoff_workspace=_workspace(run_root, "Q1", "handoff"),
            logical_package_path="Q1",
            next_state_path=f"state/revision-{context.state.data['revision'] + 1:03d}.json",
            active_return_request=context.active_return,
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-conception-reviewer",
        executor=execute_q1,
        input_bindings=sealed_inputs,
    )
    return {
        "run_id": run_id,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "completion": receipt.completion.reference,
    }


def issue_p1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    stages = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1")
    _, gate, order = _issue(run_id, "P1", {})
    result = _issue_result(run_id, run_root, gate, order)
    result["packages"] = _sealed_executor_inputs(order)
    return result


def finalize_p1(run_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "P1":
        raise RuntimeError("current pending work order is not P1")

    sealed_inputs = _sealed_executor_inputs(order)

    def execute_p1(coordinator, input_gate, inputs):
        return _p1_runtime().run_p1(
            run_root / "P1",
            **{
                PACKAGE_ARGUMENTS[item]: Path(inputs[PACKAGE_ARGUMENTS[item]])
                for item in ("B0", "S1", "W1", "E1", "T1", "C1", "Q1")
            },
            coordinator=coordinator,
            input_gate=input_gate,
            logical_package_path="P1",
            next_state_path=f"state/revision-{context.state.data['revision'] + 1:03d}.json",
            active_return_request=context.active_return,
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-conception-deliverable-assembler",
        executor=execute_p1,
        input_bindings=sealed_inputs,
    )
    return {
        "run_id": run_id,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "completion": receipt.completion.reference,
    }


def initialize_h1(run_id: str, session_id: str) -> dict[str, object]:
    run_root, _ = _paths(run_id)
    context = prod.resume_production_run(run_root)
    workspace = prod.initialize_h1_workspace(context, session_id=session_id)
    return {
        "run_id": run_id,
        "stage": "H1",
        "session_id": workspace.data["session_id"],
        "workspace_state": workspace.data["state"],
        "workspace": workspace.reference,
    }


def selftest() -> dict[str, object]:
    absent = ROOT / "projects" / "duanxian" / "conception-production" / ".selftest-absent"
    assert _next_phase({"phases": ["first", "second"]}, absent) == "first"
    assert _next_phase({"phases": []}, absent) is None
    assert _next_phase({}, absent) is None
    assert _workspace(absent, "W1") == absent / "workspaces" / "W1-attempt-01"
    assert _workspace(absent, "W1", attempt=2) == absent / "workspaces" / "W1-attempt-02"
    for stage, spec in STAGE_SPECS.items():
        contract = prod.ACTION_CONTRACT[stage]
        assert contract[0] == stage
        assert contract[1] == spec["actor"]
    s1_runtime = _s1_runtime()
    _require_s1_line_review_v2_api(s1_runtime)
    _require_s1_review_api(s1_runtime, "start_s1_topology_semantic_review")
    _require_s1_review_api(s1_runtime, "submit_s1_topology_semantic_review")
    return {
        "status": "passed",
        "checks": [
            "session-shape-compatibility",
            "attempt-workspace-selection",
            "stage-owner-contracts",
            "s1-line-review-v2-api-compatibility",
            "s1-topology-review-api-compatibility",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Duanxian conception production entrypoint")
    parser.add_argument("run_id")
    simple_actions = tuple(
        f"{verb}-{stage.lower()}"
        for stage in ("S1", "W1", "E1", "T1", "C1")
        for verb in ("issue", "start", "submit", "finalize")
    )
    parser.add_argument(
        "action",
        choices=(
            "b0",
            "status",
            "selftest",
            *simple_actions,
            "issue-q1",
            "start-s1-line-review",
            "submit-s1-line-review",
            "start-s1-topology-review",
            "submit-s1-topology-review",
            "start-q1-controller",
            "start-q1-semantic",
            "submit-q1-semantic",
            "start-q1-handoff",
            "seal-q1-handoff",
            "import-q1-handoff",
            "submit-q1-final",
            "finalize-q1",
            "issue-p1",
            "finalize-p1",
            "init-h1",
        ),
    )
    parser.add_argument("--phase")
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--session-id")
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--attempt", type=_positive_int, default=1)
    args = parser.parse_args()
    if args.action == "b0":
        result = initialize_b0(args.run_id)
    elif args.action == "selftest":
        result = selftest()
    elif args.action in simple_actions:
        verb, stage_name = args.action.split("-", 1)
        stage = stage_name.upper()
        if verb == "issue":
            result = issue_stage(args.run_id, stage)
        elif verb == "start":
            if stage == "S1":
                result = start_stage(args.run_id, stage)
            else:
                result = start_stage(args.run_id, stage, attempt=args.attempt)
        elif verb == "submit":
            if not args.phase or args.payload is None:
                parser.error(f"{args.action} requires --phase and --payload")
            if stage == "S1":
                result = submit_stage(args.run_id, stage, args.phase, args.payload)
            else:
                result = submit_stage(
                    args.run_id,
                    stage,
                    args.phase,
                    args.payload,
                    attempt=args.attempt,
                )
        else:
            if stage == "S1":
                result = finalize_stage(args.run_id, stage)
            else:
                result = finalize_stage(args.run_id, stage, attempt=args.attempt)
    elif args.action == "start-s1-line-review":
        if args.payload is None:
            parser.error("start-s1-line-review requires --payload")
        result = start_s1_line_review(args.run_id, args.payload)
    elif args.action == "submit-s1-line-review":
        if args.payload is None or not args.candidate_sha256:
            parser.error(
                "submit-s1-line-review requires --candidate-sha256 and --payload"
            )
        result = submit_s1_line_review(
            args.run_id, args.candidate_sha256, args.payload
        )
    elif args.action == "start-s1-topology-review":
        if args.payload is None:
            parser.error("start-s1-topology-review requires --payload")
        result = start_s1_topology_review(args.run_id, args.payload)
    elif args.action == "submit-s1-topology-review":
        if args.payload is None or not args.candidate_sha256:
            parser.error(
                "submit-s1-topology-review requires "
                "--candidate-sha256 and --payload"
            )
        result = submit_s1_topology_review(
            args.run_id, args.candidate_sha256, args.payload
        )
    elif args.action == "issue-q1":
        result = issue_q1(args.run_id)
    elif args.action == "start-q1-controller":
        result = start_q1_controller(args.run_id)
    elif args.action == "start-q1-semantic":
        result = start_q1_semantic(args.run_id)
    elif args.action == "submit-q1-semantic":
        if not args.phase or args.payload is None:
            parser.error("submit-q1-semantic requires --phase and --payload")
        result = submit_q1_semantic(args.run_id, args.phase, args.payload)
    elif args.action == "start-q1-handoff":
        result = start_q1_handoff(args.run_id)
    elif args.action == "seal-q1-handoff":
        if args.payload is None:
            parser.error("seal-q1-handoff requires --payload")
        result = seal_q1_handoff(args.run_id, args.payload)
    elif args.action == "import-q1-handoff":
        result = import_q1_handoff(args.run_id)
    elif args.action == "submit-q1-final":
        if args.payload is None:
            parser.error("submit-q1-final requires --payload")
        result = submit_q1_final(args.run_id, args.payload)
    elif args.action == "finalize-q1":
        result = finalize_q1(args.run_id)
    elif args.action == "issue-p1":
        result = issue_p1(args.run_id)
    elif args.action == "finalize-p1":
        result = finalize_p1(args.run_id)
    elif args.action == "init-h1":
        if not args.session_id:
            parser.error("init-h1 requires --session-id")
        result = initialize_h1(args.run_id, args.session_id)
    else:
        result = status(args.run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
