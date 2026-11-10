from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from unittest import mock


coordinator_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.coordinator"
)
contracts = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.contracts"
)
tfc = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_final_completion"
)
h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)
h1a_tests = importlib.import_module(
    "skills.novel-conception-human-review-assembler.tests.test_v2_runtime"
)
h1b = importlib.import_module(
    "skills.novel-conception-fragment-writer.scripts.run_v2"
)
h1b_tests = importlib.import_module(
    "skills.novel-conception-fragment-writer.tests.test_v2_runtime"
)
h1c = importlib.import_module(
    "skills.novel-conception-review-html-generator.scripts.run_v2"
)


@dataclass
class RenderedH1Fixture:
    temporary: tempfile.TemporaryDirectory
    h1a_case: object
    runtime: object
    coordinator: object
    stage_packages: dict[str, Path]
    p1_package: Path
    plan_package: Path
    plan_input_gate: object
    plan_workspace_state: object
    fragment_package: Path
    fragment_workspace_state: object
    assembly_package: Path
    assembly_workspace_state: object
    html_package: Path
    rendered_workspace: object
    development_handoff: Path

    def close(self) -> None:
        self.h1a_case.tearDown()
        self.temporary.cleanup()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        h1a.rt.canonical_json(value),
        encoding="utf-8",
        newline="",
    )


def _capture_fragment_submissions() -> tuple[list[dict], dict[str, dict]]:
    driver = h1b_tests.H1BRuntimeTests(
        methodName="test_real_h1a_plan_h1b_and_h1a_assembly_integration"
    )
    driver.setUp()
    captured: list[dict] = []
    p1_documents: dict[str, dict] = {}
    original = h1b.submit_fragment_phase
    original_start = h1b.start_fragment_session
    original_inputs = h1a_tests.H1APlanSkeletonTests._formal_inputs

    def capture(*args, **kwargs):
        submission = (
            args[1] if len(args) > 1 else kwargs["submission"]
        )
        captured.append(copy.deepcopy(submission))
        return original(*args, **kwargs)

    def capture_start(*args, **kwargs):
        p1_root = Path(kwargs["p1_package"]).resolve()
        for name in (
            "author-control-baseline.json",
            "S1.json",
            "W1.json",
            "E1.json",
            "T1.json",
            "C1.json",
            "novel-conception-package.json",
        ):
            p1_documents[name] = json.loads(
                (p1_root / name).read_text(encoding="utf-8")
            )
        return original_start(*args, **kwargs)

    def declared_character_source(case):
        """Expose a real C1 source through P1's authoritative source fields.

        The source already exists as the canonical C1 object's ID.  Declaring
        it explicitly before H1-A inventories P1 makes the author-decision
        source registry testable without inventing or post-hoc mutating a
        source after the rendered package has been produced.
        """

        values = original_inputs(case)
        p1_root = Path(values[0]).resolve()
        character_path = p1_root / "C1.json"
        character = json.loads(
            character_path.read_text(encoding="utf-8")
        )
        character["source_ids"] = ["CHR-1"]
        case._write(character_path, character)
        return values

    try:
        with mock.patch.object(
            h1b, "submit_fragment_phase", side_effect=capture
        ), mock.patch.object(
            h1b, "start_fragment_session", side_effect=capture_start
        ), mock.patch.object(
            h1a_tests.H1APlanSkeletonTests,
            "_formal_inputs",
            new=declared_character_source,
        ):
            driver.test_real_h1a_plan_h1b_and_h1a_assembly_integration()
    finally:
        driver.tearDown()
    if [item["phase"] for item in captured] != list(h1b.PHASES):
        raise AssertionError("failed to capture the formal H1-B phase order")
    if len(p1_documents) != 7:
        raise AssertionError("failed to capture the formal P1 documents")
    return captured, p1_documents


def _plan_phases(plan: dict) -> list[dict]:
    return [
        {
            "phase": h1a.PLAN_PHASES[0],
            "phase_index": 1,
            "payload": {
                "review_requirements": plan["review_requirements"],
                "risk_register": plan["risk_register"],
            },
        },
        {
            "phase": h1a.PLAN_PHASES[1],
            "phase_index": 2,
            "payload": {
                "review_path": plan["review_path"],
                "sections": plan["sections"],
                "review_scope_contract": plan["review_scope_contract"],
                "decision_controls": plan["decision_controls"],
                "reduction_ledger": plan["reduction_ledger"],
                "drilldown_index": plan["drilldown_index"],
            },
        },
        {
            "phase": h1a.PLAN_PHASES[2],
            "phase_index": 3,
            "payload": {
                key: plan[key]
                for key in (
                    "visual_models",
                    "fragment_briefs",
                    "decision_prompts",
                    "assembly_projection",
                    "presentation_bindings",
                )
            },
        },
        {
            "phase": h1a.PLAN_PHASES[3],
            "phase_index": 4,
            "payload": {
                "reading_profile": plan["reading_profile"],
                "budget_items": plan["budget_items"],
                "budget_total_seconds": sum(
                    item["estimated_seconds"]
                    for item in plan["budget_items"]
                ),
            },
        },
        {
            "phase": h1a.PLAN_PHASES[4],
            "phase_index": 5,
            "payload": {
                "review_plan": plan,
                "final_checks": {
                    "three_boards": True,
                    "all_source_anchors_covered": True,
                    "budget_within_600": True,
                    "fragments_non_authoritative": True,
                    "decision_unselected": True,
                },
            },
        },
    ]


def _prepare_p1(
    case, p1: Path, documents: dict[str, dict]
) -> None:
    for filename, value in documents.items():
        case._write(p1 / filename, value)


def _prepare_p1_manifest(p1: Path) -> Path:
    handoff = p1 / "development-handoff.json"
    _write(
        handoff,
        {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "status": "ready",
            "author_control_baseline": h1a.rt.artifact_reference(
                p1 / "author-control-baseline.json", root=p1
            ),
            "conception_package": h1a.rt.artifact_reference(
                p1 / "novel-conception-package.json", root=p1
            ),
            "mandatory_controls": ["INT-1"],
            "development_freedoms": [],
            "must_ask": [],
            "open_items": [],
            "development_entrypoint": {
                "next_stage": "novel-development",
                "instruction": "enter development only after approval",
            },
        },
    )
    extra = {
        "authoritative-design-index.json": {"schema_version": "2.0"},
        "spec.json": {"schema_version": "2.0"},
        "cross-model-index.json": {"schema_version": "2.0"},
        "traceability.json": {"schema_version": "2.0"},
        "execution-record.json": {"schema_version": "2.0"},
        "validation.json": {"verdict": "ready"},
    }
    for name, value in extra.items():
        _write(p1 / name, value)
    implementation = p1 / "implementation" / "fixture.py"
    implementation.parent.mkdir(parents=True, exist_ok=True)
    implementation.write_text("# formal P1 isolation fixture\n", encoding="utf-8")
    files = [
        h1a.rt.artifact_reference(path, root=p1)
        for path in sorted(p1.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
        and path.name not in {
            "package-manifest.json",
            "stage-completion.json",
        }
    ]
    by_path = {item["path"]: item for item in files}
    manifest = {
        "schema_version": "2.0",
        "run_id": "RUN-1",
        "stage": "P1",
        "package_profile": "conception-package",
        "verdict": "ready",
        "files": files,
        "artifact_roles": {
            "conception_package": by_path["novel-conception-package.json"],
            "author_control_baseline": by_path[
                "author-control-baseline.json"
            ],
            "authoritative_design_index": by_path[
                "authoritative-design-index.json"
            ],
            "spec": by_path["spec.json"],
            "cross_model_index": by_path["cross-model-index.json"],
            "traceability": by_path["traceability.json"],
            "development_handoff": by_path["development-handoff.json"],
            "execution_record": by_path["execution-record.json"],
        },
        "validation": by_path["validation.json"],
        "implementation": [by_path["implementation/fixture.py"]],
    }
    _write(p1 / "package-manifest.json", manifest)
    return handoff


def _complete_stage(subject, stage: str, package: Path):
    gate = subject.build_input_gate(stage, f"{stage}/input-gate.json")
    logical_root = stage
    manifest = package / "package-manifest.json"
    validation = package / "validation.json"
    body = {
        "schema_version": "2.0",
        "run_id": "RUN-1",
        "stage": stage,
        "status": "ready",
        "manifest": {
            "path": f"{logical_root}/package-manifest.json",
            "sha256": h1a.rt.sha256_file(manifest),
        },
        "validation": {
            "path": f"{logical_root}/validation.json",
            "sha256": h1a.rt.sha256_file(validation),
        },
        "input_gate": copy.deepcopy(gate.reference),
        "state_before": copy.deepcopy(gate.data["run_state"]),
        "previous_stage_completions": copy.deepcopy(
            gate.data["upstream_completions"]
        ),
        "return_binding": copy.deepcopy(gate.data["return_binding"]),
    }
    if stage in {"S1", "W1", "E1", "T1", "C1", "Q1"}:
        body["session_id"] = f"SESSION-{stage}"
    completion = coordinator_runtime.seal_stage_document(
        body, stage, f"{logical_root}/stage-completion.json"
    )
    _write(package / "stage-completion.json", completion.data)
    subject.accept_stage_completion(
        gate=gate,
        completion=completion,
        next_state_path=(
            f"state/revision-{subject.state['revision'] + 1:03d}.json"
        ),
    )
    return completion


def build_current_rendered_h1_fixture(
    *, fragment_logical_package_path: str = "H1/fragments"
) -> RenderedH1Fixture:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    runtime = contracts.ContractRuntime()
    fragment_submissions, p1_documents = _capture_fragment_submissions()

    case = h1a_tests.H1APlanSkeletonTests(
        methodName="test_plan_requires_exact_initialized_workspace"
    )
    case.setUp()
    case.runtime = runtime
    p1, _, _, _ = case._formal_inputs()
    _prepare_p1(case, p1, p1_documents)
    handoff = _prepare_p1_manifest(p1)

    subject = coordinator_runtime.AutonomousCoordinator.initialize(
        run_id="RUN-1",
        source_interview_state={
            "path": "interview/run-state.json",
            "sha256": "1" * 64,
        },
        state_path="state/revision-000.json",
        runtime=runtime,
    )
    profiles = {
        "B0": "baseline",
        "S1": "generated-model",
        "W1": "generated-model",
        "E1": "generated-model",
        "T1": "generated-model",
        "C1": "generated-model",
        "Q1": "independent-review",
    }
    stage_packages: dict[str, Path] = {}
    for stage, profile in profiles.items():
        package = tfc.write_formal_package(
            root / stage,
            profile=profile,
            stage=stage,
            run_id="RUN-1",
        )
        _complete_stage(subject, stage, package)
        stage_packages[stage] = package
    p1_completion = _complete_stage(subject, "P1", p1)
    stage_packages["P1"] = p1

    initialized_data = {
        "schema_version": "2.0",
        "run_id": "RUN-1",
        "stage": "H1",
        "session_id": "H1-SESSION-1",
        "state": "initialized",
        "p1_completion": copy.deepcopy(p1_completion.reference),
        "previous_state_sha256": None,
        "artifacts": {},
    }
    initialized = coordinator_runtime.seal_document(
        initialized_data, "H1/workspace-initialized.json"
    )
    gate = subject.build_input_gate("H1", "H1/input-gate.json")
    inventory = h1a.build_source_inventory(
        p1,
        p1_completion={
            "path": p1_completion.reference["path"],
            "sha256": p1_completion.reference["sha256"],
        },
    )
    plan = case._plan(inventory, p1_completion.reference, gate.reference)
    plan_phases = _plan_phases(plan)

    try:
        with mock.patch.object(
            h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-015-plan",
                "CODEX_THREAD_ID": "thread-015-plan",
            },
            clear=True,
        ):
            plan_receipt = h1a.run_plan(
                root / "H1" / "plan",
                p1_package=p1,
                input_gate=gate,
                workspace_state=initialized,
                work_title=plan["work_identity"]["work_title"],
                phase_submissions=plan_phases,
                coordinator=subject,
                runtime=runtime,
            )
        planned = plan_receipt.transition.workspace

        session = root / "H1-fragment-session"
        with mock.patch.object(
            h1b.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-015-fragments",
                "CODEX_THREAD_ID": "thread-015-fragments",
            },
            clear=True,
        ):
            h1b.start_fragment_session(
                session,
                p1_package=p1,
                plan_package=plan_receipt.package_root,
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
            for submission in fragment_submissions:
                h1b.submit_fragment_phase(
                    session,
                    submission,
                    p1_package=p1,
                    plan_package=plan_receipt.package_root,
                    plan_input_gate=gate,
                    plan_workspace_state=initialized,
                    workspace_state=planned,
                    runtime=runtime,
                )
            fragment_receipt = h1b.run(
                root.joinpath(
                    *PurePosixPath(fragment_logical_package_path).parts
                ),
                session_workspace=session,
                p1_package=p1,
                plan_package=plan_receipt.package_root,
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                coordinator=subject,
                logical_package_path=fragment_logical_package_path,
                runtime=runtime,
            )
        fragments_ready = fragment_receipt.transition.workspace

        fidelity_review = case._make_fidelity_review(
            p1_completion={
                "path": initialized.data["p1_completion"]["path"],
                "sha256": initialized.data["p1_completion"]["sha256"],
            },
            plan_root=plan_receipt.package_root,
            fragment_root=fragment_receipt.package_root,
        )
        fidelity_review["inputs"]["fragment_manifest"]["path"] = (
            f"{fragment_logical_package_path}/package-manifest.json"
        )

        with mock.patch.object(
            h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ):
            assembly_receipt = h1a.run_assemble(
                root / "H1" / "assembly",
                p1_package=p1,
                plan_package=plan_receipt.package_root,
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                fragment_package=fragment_receipt.package_root,
                fragment_workspace_state=planned,
                workspace_state=fragments_ready,
                coordinator=subject,
                fidelity_review=fidelity_review,
                fragment_logical_package_path=fragment_logical_package_path,
                runtime=runtime,
            )
        assembled = assembly_receipt.transition.workspace

        with mock.patch.object(
            h1c.h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ):
            html_receipt = h1c.run(
                root / "H1" / "html",
                p1_package=p1,
                plan_package=plan_receipt.package_root,
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                fragment_package=fragment_receipt.package_root,
                fragment_workspace_state=planned,
                assembly_package=assembly_receipt.package_root,
                assembly_workspace_state=fragments_ready,
                workspace_state=assembled,
                coordinator=subject,
                fragment_logical_package_path=fragment_logical_package_path,
                runtime=runtime,
            )
        rendered = html_receipt.transition.workspace
    except Exception:
        case.tearDown()
        temporary.cleanup()
        raise

    return RenderedH1Fixture(
        temporary=temporary,
        h1a_case=case,
        runtime=runtime,
        coordinator=subject,
        stage_packages=stage_packages,
        p1_package=p1,
        plan_package=plan_receipt.package_root,
        plan_input_gate=gate,
        plan_workspace_state=initialized,
        fragment_package=fragment_receipt.package_root,
        fragment_workspace_state=planned,
        assembly_package=assembly_receipt.package_root,
        assembly_workspace_state=fragments_ready,
        html_package=html_receipt.package_root,
        rendered_workspace=rendered,
        development_handoff=handoff,
    )
