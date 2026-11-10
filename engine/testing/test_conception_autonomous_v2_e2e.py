from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import contextlib
import copy
import importlib
import inspect
import json
import os
import re
import tempfile
import threading
import typing
import unittest
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
s1 = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
w1 = importlib.import_module("skills.novel-world-model-designer.scripts.run_v2")
e1 = importlib.import_module(
    "skills.novel-environment-system-designer.scripts.run_v2"
)
t1 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.run_v2"
)
c1 = importlib.import_module(
    "skills.novel-character-system-designer.scripts.run_v2"
)
q1 = importlib.import_module(
    "skills.novel-conception-reviewer.scripts.run_v2"
)
p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)
h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)
h1b = importlib.import_module(
    "skills.novel-conception-fragment-writer.scripts.run_v2"
)
h1c = importlib.import_module(
    "skills.novel-conception-review-html-generator.scripts.run_v2"
)
proposal_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.proposal_adapter"
)
storyline_plan_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_plan"
)
storyline_quality_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_quality"
)
canonical_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
contracts_module = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.contracts"
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERIC_FIXTURE = (
    REPOSITORY_ROOT
    / "harnesses"
    / "novel-conception-autonomous"
    / "evals"
    / "fixtures"
    / "generic"
    / "fixture.json"
)
DUANXIAN_FIXTURE = (
    REPOSITORY_ROOT
    / "harnesses"
    / "novel-conception-autonomous"
    / "evals"
    / "fixtures"
    / "duanxian"
    / "fixture.json"
)
EVALS_ROOT = GENERIC_FIXTURE.parents[2]
GENERIC_CASE_MANIFEST = EVALS_ROOT / "manifests" / "generic.v1.json"
DUANXIAN_CASE_MANIFEST = EVALS_ROOT / "manifests" / "duanxian.v1.json"
E2E_CASE_MANIFEST_ENV = "CONCEPTION_E2E_CASE_MANIFEST"
FIXTURE_SCHEMA = DUANXIAN_FIXTURE.with_name("fixture.schema.json")
INTERVIEW_STAGES = ("I0", "I1", "I2", "I3", "I4", "I5")
E2E_PROVENANCE_ENV = "CONCEPTION_E2E_PROVENANCE_DIR"
E2E_PROVENANCE_START = "execution-provenance-start.json"
E2E_PROVENANCE_END = "execution-provenance-hash-stable.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


def _test_fidelity_review(
    *,
    p1_completion: Mapping[str, str],
    plan_root: Path,
    fragment_root: Path,
    runtime: Any,
) -> dict[str, Any]:
    """Author a formal fixture review; production never synthesizes this gate."""
    plan = json.loads(
        (plan_root / "review-plan.json").read_text(encoding="utf-8")
    )
    inventory = json.loads(
        (plan_root / "source-inventory.json").read_text(encoding="utf-8")
    )
    plan_manifest = {
        "path": "H1/plan/package-manifest.json",
        "sha256": rt.sha256_file(plan_root / "package-manifest.json"),
    }
    fragment_manifest = {
        "path": "H1/fragments/package-manifest.json",
        "sha256": rt.sha256_file(fragment_root / "package-manifest.json"),
    }
    fragments = h1a._validated_fragment_records(
        fragment_root,
        plan=plan,
        source_inventory=inventory,
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        p1_completion=dict(p1_completion),
        runtime=runtime,
    )
    report = h1a._assemble_report(plan, inventory, fragments)
    contracts = h1a._fidelity_element_contract(plan, report)
    element_ids = [item["element_id"] for item in contracts]
    return {
        "schema_version": "2.0",
        "skill": "novel-conception-presentation-fidelity-reviewer",
        "run_id": plan["run_id"],
        "h1_session_id": plan["h1_session_id"],
        "reviewer": {
            "task_id": "formal-e2e-fidelity-review-task",
            "thread_id": "formal-e2e-fidelity-review-thread",
            "independence_basis": "separate-task-no-producer-context",
        },
        "inputs": {
            "p1_completion": dict(p1_completion),
            "plan_manifest": plan_manifest,
            "fragment_manifest": fragment_manifest,
            "report_sha256": rt.canonical_sha256(report),
        },
        "dimensions": [
            {
                "id": dimension,
                "verdict": "pass",
                "evidence_element_ids": element_ids,
                "finding": "The sealed candidate was checked element by element against its exact P1 anchors without substantive drift.",
            }
            for dimension in h1a.FIDELITY_DIMENSIONS
        ],
        "element_reviews": [
            {
                "element_id": item["element_id"],
                "content_sha256": item["content_sha256"],
                "source_anchor_ids": item["source_anchor_ids"],
                "verdict": item["expected_verdict"],
                "semantic_assertion": "The candidate preserves the source conditions, relationships and authority boundary.",
                "evidence_quotes": [
                    next(
                        value for value in h1a._string_leaves(item["_content"])
                        if len(value.strip()) >= 4
                    )
                ],
                "no_material_omission": True,
                "no_contradiction": True,
                "no_authority_escalation": True,
            }
            for item in contracts
        ],
        "blockers": [],
        "verdict": "pass",
    }


def _write_json_atomic(path: Path, value: Any) -> None:
    """Publish a new JSON marker atomically without replacing prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".candidate",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(rt.canonical_json(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _provenance_artifact(
    role: str,
    path: Path,
    *,
    repository_root: Path,
) -> dict[str, str]:
    resolved_root = repository_root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(resolved_root).as_posix()
    except ValueError as error:
        raise AssertionError(
            f"E2E_PROVENANCE_PATH_OUTSIDE_REPOSITORY: {resolved}"
        ) from error
    if not resolved.is_file():
        raise AssertionError(
            f"E2E_PROVENANCE_ARTIFACT_INVALID: {resolved}"
        )
    return {
        "role": role,
        "repository_path": relative,
        "sha256": rt.sha256_file(resolved),
    }


class _ExecutionProvenanceGuard:
    """Bind and recheck opt-in E2E authoring bytes.

    The end marker proves hash stability through a normal test-method exit.
    It is not a chain-success or stage-completion artifact.
    """

    def __init__(
        self,
        *,
        directory: Path,
        repository_root: Path,
        driver_path: Path,
        proposal_path: Path,
        fixture_path: Path,
        run_id: str,
    ) -> None:
        self.directory = directory.resolve()
        self.repository_root = repository_root.resolve(strict=True)
        self.driver_path = driver_path
        self.proposal_path = proposal_path
        self.fixture_path = fixture_path
        self.run_id = run_id
        self.start_path = self.directory / E2E_PROVENANCE_START
        self.end_path = self.directory / E2E_PROVENANCE_END
        if self.start_path.exists() or self.end_path.exists():
            raise AssertionError(
                "E2E_PROVENANCE_MARKER_EXISTS: start/end markers must be absent"
            )
        self._bound = self._capture()
        start = {
            "schema_version": "1.0",
            "kind": "e2e-execution-provenance-start",
            "run_id": self.run_id,
            **self._bound,
        }
        _write_json_atomic(self.start_path, start)
        self._start_sha256 = rt.sha256_file(self.start_path)

    def _capture(self) -> dict[str, Any]:
        implementation = [
            _provenance_artifact(
                "proposal_authoring_adapter",
                self.proposal_path,
                repository_root=self.repository_root,
            ),
            _provenance_artifact(
                "test_driver",
                self.driver_path,
                repository_root=self.repository_root,
            ),
        ]
        implementation.sort(key=lambda item: item["role"])
        fixture = _provenance_artifact(
            "fixture",
            self.fixture_path,
            repository_root=self.repository_root,
        )
        return {
            "fixture": fixture,
            "implementation": implementation,
            "implementation_inventory_sha256": rt.canonical_sha256(
                implementation
            ),
        }

    def __enter__(self) -> _ExecutionProvenanceGuard:
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:
        if exc_type is not None:
            return False
        current = self._capture()
        if (
            current != self._bound
            or rt.sha256_file(self.start_path) != self._start_sha256
        ):
            raise AssertionError(
                "E2E_PROVENANCE_DRIFT: driver, adapter, fixture, or start "
                "marker changed during the test"
            )
        end = {
            "schema_version": "1.0",
            "kind": "e2e-execution-provenance-hash-stable",
            "status": "hash-stable",
            "claim_scope": "implementation-and-fixture-bytes-only",
            "run_id": self.run_id,
            "start_marker": {
                "path": E2E_PROVENANCE_START,
                "sha256": self._start_sha256,
            },
            **current,
        }
        _write_json_atomic(self.end_path, end)
        return False


def _start_execution_provenance_guard(
    fixture_path: Path,
) -> _ExecutionProvenanceGuard | None:
    directory = os.environ.get(E2E_PROVENANCE_ENV)
    if directory is None:
        return None
    if not directory.strip():
        raise AssertionError("E2E_PROVENANCE_DIRECTORY_INVALID")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    run_id = fixture.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise AssertionError("E2E_PROVENANCE_RUN_ID_INVALID")
    return _ExecutionProvenanceGuard(
        directory=Path(directory),
        repository_root=REPOSITORY_ROOT,
        driver_path=Path(__file__),
        proposal_path=Path(proposal_module.__file__),
        fixture_path=fixture_path,
        run_id=run_id,
    )


class _FormalS1ExecutionProvenanceGuard:
    """Hash-bind the complete admitted eval case and its S1 authoring code."""

    def __init__(
        self,
        *,
        directory: Path,
        execution_root: Path,
        validated_case: Any,
    ) -> None:
        self.directory = directory.resolve()
        self.execution_root = execution_root.resolve()
        self.validated_case = validated_case
        self.repository_root = REPOSITORY_ROOT.resolve(strict=True)
        self.run_id = validated_case.structural_case.fixture["run_id"]
        self.start_path = self.directory / E2E_PROVENANCE_START
        self.end_path = self.directory / E2E_PROVENANCE_END
        if self.start_path.exists() or self.end_path.exists():
            raise AssertionError(
                "E2E_PROVENANCE_MARKER_EXISTS: start/end markers must be absent"
            )
        self._bound = self._capture()
        self._output_binding: dict[str, Any] | None = None
        self._output_paths: dict[str, Path] | None = None
        _write_json_atomic(
            self.start_path,
            {
                "schema_version": "1.0",
                "kind": "formal-s1-eval-provenance-start",
                "run_id": self.run_id,
                **self._bound,
            },
        )
        self._start_sha256 = rt.sha256_file(self.start_path)

    def _capture(self) -> dict[str, Any]:
        structural = self.validated_case.structural_case
        case_artifacts = [
            _provenance_artifact(
                role,
                path,
                repository_root=self.repository_root,
            )
            for role, path in (
                ("case_manifest", structural.manifest_path),
                ("case_manifest_schema", structural.manifest_schema_path),
                ("fixture", structural.fixture_path),
                ("storyline_plan", structural.plan_path),
                ("storyline_plan_schema", structural.plan_schema_path),
                ("storyline_quality_gate", self.validated_case.gate_path),
                (
                    "storyline_quality_gate_schema",
                    self.validated_case.gate_schema_path,
                ),
            )
        ]
        expected_case_sha256 = {
            "case_manifest": structural.manifest_sha256,
            "case_manifest_schema": (
                structural.manifest_schema_sha256
            ),
            "fixture": structural.manifest["fixture"]["sha256"],
            "storyline_plan": structural.manifest[
                "storyline_plan"
            ]["sha256"],
            "storyline_plan_schema": structural.manifest[
                "storyline_plan_schema"
            ]["sha256"],
            "storyline_quality_gate": (
                self.validated_case.gate_sha256
            ),
            "storyline_quality_gate_schema": (
                self.validated_case.gate_schema_sha256
            ),
        }
        for artifact in case_artifacts:
            if (
                artifact["sha256"]
                != expected_case_sha256[artifact["role"]]
            ):
                raise AssertionError(
                    "E2E_PROVENANCE_VALIDATED_CASE_DRIFT: "
                    + artifact["role"]
                )
        implementation = [
            _provenance_artifact(
                role,
                path,
                repository_root=self.repository_root,
            )
            for role, path in (
                ("proposal_authoring_adapter", Path(proposal_module.__file__)),
                ("storyline_plan_loader", Path(storyline_plan_module.__file__)),
                (
                    "storyline_quality_loader",
                    Path(storyline_quality_module.__file__),
                ),
                (
                    "canonical_hash_path_admission",
                    Path(canonical_module.__file__),
                ),
                (
                    "contract_schema_admission",
                    Path(contracts_module.__file__),
                ),
                ("test_driver", Path(__file__)),
            )
        ]
        case_artifacts.sort(key=lambda item: item["role"])
        implementation.sort(key=lambda item: item["role"])
        return {
            "case_artifacts": case_artifacts,
            "case_inventory_sha256": rt.canonical_sha256(case_artifacts),
            "implementation": implementation,
            "implementation_inventory_sha256": rt.canonical_sha256(
                implementation
            ),
            "structural_validation_sha256": rt.canonical_sha256(
                structural.validation
            ),
            "quality_validation_sha256": rt.canonical_sha256(
                self.validated_case.validation
            ),
        }

    def __enter__(self) -> "_FormalS1ExecutionProvenanceGuard":
        return self

    def _output_artifact(
        self,
        role: str,
        path: Path,
    ) -> dict[str, str]:
        resolved = path.resolve(strict=True)
        try:
            relative = resolved.relative_to(
                self.execution_root
            ).as_posix()
        except ValueError as error:
            raise AssertionError(
                f"E2E_PROVENANCE_OUTPUT_OUTSIDE_ROOT: {resolved}"
            ) from error
        if not resolved.is_file():
            raise AssertionError(
                f"E2E_PROVENANCE_OUTPUT_INVALID: {resolved}"
            )
        return {
            "role": role,
            "execution_path": relative,
            "sha256": rt.sha256_file(resolved),
        }

    def bind_s1_output(
        self,
        *,
        projected_model: Mapping[str, Any],
        package_model_path: Path,
        package_manifest_path: Path,
        completion_path: Path,
        revision2_state: Mapping[str, Any],
        projection_evidence: Mapping[str, Any],
        revision2_state_reference: Mapping[str, Any] | None = None,
    ) -> None:
        """Bind the real revision-2 S1 publication before success is claimable."""

        if self._output_binding is not None:
            raise AssertionError("E2E_PROVENANCE_OUTPUT_ALREADY_BOUND")
        package_model = json.loads(
            package_model_path.read_text(encoding="utf-8")
        )
        projected_sha256 = rt.canonical_sha256(projected_model)
        package_sha256 = rt.canonical_sha256(package_model)
        if projected_sha256 != package_sha256:
            raise AssertionError(
                "E2E_PROVENANCE_S1_MODEL_MISMATCH"
            )
        if revision2_state.get("revision") != 2:
            raise AssertionError(
                "E2E_PROVENANCE_REVISION2_REQUIRED"
            )
        if (
            not isinstance(revision2_state_reference, Mapping)
            or set(revision2_state_reference) != {"path", "sha256"}
        ):
            raise AssertionError(
                "E2E_PROVENANCE_REVISION2_STATE_REF_REQUIRED"
            )
        sealed_state_reference = copy.deepcopy(
            dict(revision2_state_reference)
        )
        if (
            sealed_state_reference.get("path")
            != "state/revision-002.json"
            or sealed_state_reference.get("sha256")
            != rt.canonical_sha256(revision2_state)
        ):
            raise AssertionError(
                "E2E_PROVENANCE_REVISION2_STATE_REF_INVALID"
            )
        if not isinstance(projection_evidence, Mapping):
            raise AssertionError(
                "E2E_PROVENANCE_PROJECTION_EVIDENCE_REQUIRED"
            )
        sealed_projection_evidence = copy.deepcopy(
            dict(projection_evidence)
        )
        if (
            sealed_projection_evidence.get("model_sha256")
            != projected_sha256
        ):
            raise AssertionError(
                "E2E_PROVENANCE_PROJECTION_MODEL_MISMATCH"
            )
        completion_reference = revision2_state.get(
            "current_stage_completions", {}
        ).get("S1")
        if (
            not isinstance(completion_reference, Mapping)
            or completion_reference.get("sha256")
            != rt.sha256_file(completion_path)
        ):
            raise AssertionError(
                "E2E_PROVENANCE_S1_COMPLETION_REF_INVALID"
            )
        paths = {
            "storyline_model": package_model_path,
            "s1_package_manifest": package_manifest_path,
            "s1_stage_completion": completion_path,
        }
        artifacts = [
            self._output_artifact(role, path)
            for role, path in paths.items()
        ]
        artifacts.sort(key=lambda item: item["role"])
        self._output_paths = paths
        self._output_binding = {
            "artifacts": artifacts,
            "artifact_inventory_sha256": rt.canonical_sha256(
                artifacts
            ),
            "projected_model_sha256": projected_sha256,
            "package_model_sha256": package_sha256,
            "projection_evidence_sha256": rt.canonical_sha256(
                sealed_projection_evidence
            ),
            "revision2_state_envelope": {
                "state": copy.deepcopy(dict(revision2_state)),
                "reference": sealed_state_reference,
            },
            "s1_completion_reference": copy.deepcopy(
                dict(completion_reference)
            ),
        }

    def _recapture_output(self) -> dict[str, Any]:
        if self._output_binding is None or self._output_paths is None:
            raise AssertionError(
                "E2E_PROVENANCE_S1_OUTPUT_NOT_BOUND"
            )
        artifacts = [
            self._output_artifact(role, path)
            for role, path in self._output_paths.items()
        ]
        artifacts.sort(key=lambda item: item["role"])
        current = copy.deepcopy(self._output_binding)
        current["artifacts"] = artifacts
        current["artifact_inventory_sha256"] = rt.canonical_sha256(
            artifacts
        )
        return current

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:
        if exc_type is not None:
            return False
        current_output = self._recapture_output()
        if current_output != self._output_binding:
            raise AssertionError(
                "E2E_PROVENANCE_S1_OUTPUT_DRIFT"
            )
        current = self._capture()
        if (
            current != self._bound
            or rt.sha256_file(self.start_path) != self._start_sha256
        ):
            raise AssertionError(
                "E2E_PROVENANCE_DRIFT: formal case, implementation, or "
                "start marker changed"
            )
        _write_json_atomic(
            self.end_path,
            {
                "schema_version": "1.0",
                "kind": "formal-s1-eval-provenance-hash-stable",
                "status": "hash-stable",
                "claim_scope": (
                    "case-and-implementation-byte-stability-plus-exact-"
                    "s1-projection-publication-identity"
                ),
                "run_id": self.run_id,
                "start_marker": {
                    "path": E2E_PROVENANCE_START,
                    "sha256": self._start_sha256,
                },
                "s1_output": current_output,
                **current,
            },
        )
        return False


def _start_formal_s1_provenance_guard(
    validated_case: Any,
    *,
    execution_root: Path,
) -> _FormalS1ExecutionProvenanceGuard:
    configured = os.environ.get(E2E_PROVENANCE_ENV)
    if configured is not None and not configured.strip():
        raise AssertionError("E2E_PROVENANCE_DIRECTORY_INVALID")
    directory = (
        Path(configured)
        if configured is not None
        else execution_root / "evidence" / "formal-s1-provenance"
    )
    return _FormalS1ExecutionProvenanceGuard(
        directory=directory,
        execution_root=execution_root,
        validated_case=validated_case,
    )


class _FormalFullChainProvenanceGuard:
    """Bind one admitted eval case to every public B0-P1 publication."""

    _OUTPUT_NAMES = {
        "B0": ("author-control-baseline.json",),
        "S1": ("storyline-architecture.json",),
        "W1": ("world-model.json",),
        "E1": ("environment-system.json",),
        "T1": ("event-timeline.json",),
        "C1": ("character-system.json",),
        "Q1": ("conception-review.json",),
        "P1": (
            "novel-conception-package.json",
            "authoritative-design-index.json",
            "development-handoff.json",
        ),
    }
    _STAGES = tuple(_OUTPUT_NAMES)

    def __init__(
        self,
        *,
        execution_root: Path,
        validated_case: Any,
    ) -> None:
        self.execution_root = execution_root.resolve()
        self.validated_case = validated_case
        self.repository_root = REPOSITORY_ROOT.resolve(strict=True)
        self.run_id = validated_case.structural_case.fixture["run_id"]
        self.directory = (
            self.execution_root
            / "evidence"
            / "formal-full-chain-provenance"
        )
        self.start_path = self.directory / E2E_PROVENANCE_START
        self.end_path = self.directory / E2E_PROVENANCE_END
        if self.start_path.exists() or self.end_path.exists():
            raise AssertionError(
                "FORMAL_FULL_PROVENANCE_MARKER_EXISTS"
            )
        self._bound = self._capture_inputs()
        self._stage_bindings: dict[str, Any] = {}
        self._stage_paths: dict[str, list[Path]] = {}
        self._stage_roots: dict[str, Path] = {}
        self._initial_state: dict[str, Any] | None = None
        self._final_state: dict[str, Any] | None = None
        self._q1_controller_admission: dict[str, Any] | None = None
        self._q1_frozen_path: Path | None = None
        self._p1_slc_index_ledger: list[dict[str, Any]] | None = None
        _write_json_atomic(
            self.start_path,
            {
                "schema_version": "1.0",
                "kind": "formal-full-chain-provenance-start",
                "run_id": self.run_id,
                **self._bound,
            },
        )
        self._start_sha256 = rt.sha256_file(self.start_path)

    def _capture_inputs(self) -> dict[str, Any]:
        structural = self.validated_case.structural_case
        case_artifacts = [
            _provenance_artifact(
                role,
                path,
                repository_root=self.repository_root,
            )
            for role, path in (
                ("case_manifest", structural.manifest_path),
                ("case_manifest_schema", structural.manifest_schema_path),
                ("fixture", structural.fixture_path),
                ("storyline_plan", structural.plan_path),
                (
                    "storyline_plan_schema",
                    structural.plan_schema_path,
                ),
                ("storyline_quality_gate", self.validated_case.gate_path),
                (
                    "storyline_quality_gate_schema",
                    self.validated_case.gate_schema_path,
                ),
            )
        ]
        implementation_paths = [
            ("test_driver", Path(__file__)),
            ("proposal_authoring_adapter", Path(proposal_module.__file__)),
            ("storyline_plan_loader", Path(storyline_plan_module.__file__)),
            (
                "storyline_quality_loader",
                Path(storyline_quality_module.__file__),
            ),
            (
                "B0_baseline_runtime",
                Path(
                    typing.cast(
                        str,
                        inspect.getsourcefile(
                            rt.build_baseline_package
                        ),
                    )
                ),
            ),
            (
                "canonical_runtime",
                Path(canonical_module.__file__),
            ),
            (
                "contract_runtime",
                Path(contracts_module.__file__),
            ),
            (
                "coordinator_runtime",
                Path(
                    typing.cast(
                        str,
                        inspect.getsourcefile(
                            rt.AutonomousCoordinator
                        ),
                    )
                ),
            ),
            ("S1_runtime", Path(s1.__file__)),
            ("W1_runtime", Path(w1.__file__)),
            ("E1_runtime", Path(e1.__file__)),
            ("T1_runtime", Path(t1.__file__)),
            ("C1_runtime", Path(c1.__file__)),
            ("Q1_runtime", Path(q1.__file__)),
            ("P1_runtime", Path(p1.__file__)),
        ]
        implementation = [
            _provenance_artifact(
                role,
                path,
                repository_root=self.repository_root,
            )
            for role, path in implementation_paths
        ]
        case_artifacts.sort(key=lambda item: item["role"])
        implementation.sort(key=lambda item: item["role"])
        return {
            "case_artifacts": case_artifacts,
            "case_inventory_sha256": rt.canonical_sha256(case_artifacts),
            "implementation": implementation,
            "implementation_inventory_sha256": rt.canonical_sha256(
                implementation
            ),
        }

    def _output_artifact(
        self,
        role: str,
        path: Path,
    ) -> dict[str, str]:
        resolved = path.resolve(strict=True)
        try:
            relative = resolved.relative_to(
                self.execution_root
            ).as_posix()
        except ValueError as error:
            raise AssertionError(
                f"FORMAL_FULL_OUTPUT_OUTSIDE_ROOT: {resolved}"
            ) from error
        return {
            "role": role,
            "execution_path": relative,
            "sha256": rt.sha256_file(resolved),
        }

    def bind_initial_state(self, coordinator: Any) -> None:
        if self._initial_state is not None or self._stage_bindings:
            raise AssertionError(
                "FORMAL_FULL_INITIAL_STATE_BINDING_INVALID"
            )
        state = copy.deepcopy(coordinator.state)
        reference = copy.deepcopy(coordinator.state_reference)
        if (
            state.get("revision") != 0
            or state.get("current_stage_completions") != {}
            or reference.get("path") != "state/revision-000.json"
            or reference.get("sha256") != rt.canonical_sha256(state)
        ):
            raise AssertionError("FORMAL_FULL_INITIAL_STATE_INVALID")
        self._initial_state = {
            "state": state,
            "reference": reference,
        }

    def bind_stage(
        self,
        stage: str,
        *,
        package: Path,
        validation: Mapping[str, Any],
        coordinator: Any,
    ) -> None:
        if self._initial_state is None:
            raise AssertionError(
                "FORMAL_FULL_INITIAL_STATE_REQUIRED"
            )
        expected_index = len(self._stage_bindings)
        if (
            stage not in self._OUTPUT_NAMES
            or stage in self._stage_bindings
            or self._STAGES[expected_index] != stage
            or validation.get("verdict") != "ready"
        ):
            raise AssertionError(
                f"FORMAL_FULL_STAGE_BINDING_INVALID: {stage}"
            )
        expected_stages = self._STAGES[: expected_index + 1]
        state = copy.deepcopy(coordinator.state)
        if (
            state.get("revision") != expected_index + 1
            or tuple(
                item
                for item in rt.STAGE_ORDER
                if item in state["current_stage_completions"]
            )
            != expected_stages
            or set(state["current_stage_completions"])
            != set(expected_stages)
        ):
            raise AssertionError(
                f"FORMAL_FULL_STATE_PREFIX_INVALID: {stage}"
            )
        state_reference = copy.deepcopy(coordinator.state_reference)
        if (
            state_reference.get("path")
            != f"state/revision-{expected_index + 1:03d}.json"
            or state_reference.get("sha256")
            != rt.canonical_sha256(state)
        ):
            raise AssertionError(
                f"FORMAL_FULL_STATE_REFERENCE_INVALID: {stage}"
            )
        paths = sorted(
            (
                path
                for path in package.rglob("*")
                if path.is_file()
            ),
            key=lambda path: path.relative_to(package).as_posix(),
        )
        required_names = {
            *self._OUTPUT_NAMES[stage],
            "package-manifest.json",
            "stage-completion.json",
        }
        if not required_names.issubset(
            {
                path.relative_to(package).as_posix()
                for path in paths
            }
        ):
            raise AssertionError(
                f"FORMAL_FULL_PACKAGE_TREE_INCOMPLETE: {stage}"
            )
        artifacts = [
            self._output_artifact(
                (
                    f"{stage}:"
                    f"{path.relative_to(package).as_posix()}"
                ),
                path,
            )
            for path in paths
        ]
        completion_reference = state[
            "current_stage_completions"
        ][stage]
        if completion_reference.get("sha256") != rt.sha256_file(
            package / "stage-completion.json"
        ):
            raise AssertionError(
                f"FORMAL_FULL_COMPLETION_REFERENCE_INVALID: {stage}"
            )
        self._stage_paths[stage] = paths
        self._stage_roots[stage] = package
        self._stage_bindings[stage] = {
            "artifacts": artifacts,
            "artifact_inventory_sha256": rt.canonical_sha256(artifacts),
            "validation_verdict": validation["verdict"],
            "completion_reference": copy.deepcopy(completion_reference),
            "coordinator_state_reference": state_reference,
        }

    def bind_q1_controller_admission(
        self,
        *,
        frozen: Mapping[str, Any],
        frozen_path: Path,
        input_gate: Any,
        expected_controller_identity: Mapping[str, str],
    ) -> None:
        expected = ("B0", "S1", "W1", "E1", "T1", "C1")
        required_fields = {
            "schema_version",
            "run_id",
            "stage",
            "controller_identity",
            "input_gate",
            "state_before",
            "baseline_completion",
            "upstream_completions",
            "generation_identities",
            "package_roots",
            "source_inventory",
            "handoff_source_inventory",
        }
        if (
            self._q1_controller_admission is not None
            or tuple(self._stage_bindings) != expected
            or not isinstance(frozen, Mapping)
            or set(frozen) != required_fields
            or frozen.get("schema_version") != "2.0"
            or frozen.get("run_id") != self.run_id
            or frozen.get("stage") != "Q1"
            or frozen.get("input_gate")
            != copy.deepcopy(input_gate.reference)
            or frozen.get("state_before")
            != copy.deepcopy(input_gate.data["run_state"])
        ):
            raise AssertionError(
                "FORMAL_FULL_Q1_CONTROLLER_ADMISSION_INVALID"
            )
        controller_identity = frozen.get("controller_identity")
        if (
            not isinstance(controller_identity, Mapping)
            or set(controller_identity) != {"task_id", "thread_id"}
            or dict(controller_identity)
            != dict(expected_controller_identity)
            or set(expected_controller_identity)
            != {"task_id", "thread_id"}
        ):
            raise AssertionError(
                "FORMAL_FULL_Q1_CONTROLLER_IDENTITY_INVALID"
            )
        generation_identities = frozen.get("generation_identities")
        if (
            not isinstance(generation_identities, list)
            or len(generation_identities) != 5
            or any(
                not isinstance(item, Mapping)
                or set(item) != {"task_id", "thread_id"}
                or not isinstance(item["task_id"], str)
                or not item["task_id"].strip()
                or not isinstance(item["thread_id"], str)
                or not item["thread_id"].strip()
                for item in generation_identities
            )
            or len(
                {
                    (item["task_id"], item["thread_id"])
                    for item in generation_identities
                }
            )
            != 5
            or {
                controller_identity["task_id"],
                controller_identity["thread_id"],
            }
            & {
                identifier
                for item in generation_identities
                for identifier in (
                    item["task_id"],
                    item["thread_id"],
                )
            }
        ):
            raise AssertionError(
                "FORMAL_FULL_Q1_GENERATION_IDENTITIES_INVALID"
            )
        resolved_frozen_path = frozen_path.resolve(strict=True)
        expected_frozen_path = (
            self.execution_root
            / "workspaces"
            / "Q1-controller"
            / "frozen-inputs.json"
        ).resolve(strict=True)
        frozen_from_disk = json.loads(
            resolved_frozen_path.read_text(encoding="utf-8")
        )
        if (
            resolved_frozen_path != expected_frozen_path
            or frozen_from_disk != dict(frozen)
        ):
            raise AssertionError(
                "FORMAL_FULL_Q1_FROZEN_ARTIFACT_INVALID"
            )

        expected_completion = {
            stage: {
                "path": f"{stage}/stage-completion.json",
                "sha256": self._stage_bindings[stage][
                    "completion_reference"
                ]["sha256"],
                "stage": stage,
            }
            for stage in expected
        }
        if frozen.get("baseline_completion") != expected_completion["B0"]:
            raise AssertionError(
                "FORMAL_FULL_Q1_BASELINE_COMPLETION_INVALID"
            )
        upstream = frozen.get("upstream_completions")
        if upstream != [
            expected_completion[stage] for stage in expected[1:]
        ]:
            raise AssertionError(
                "FORMAL_FULL_Q1_UPSTREAM_COMPLETIONS_INVALID"
            )

        expected_source_inventory = []
        for stage in sorted(expected):
            try:
                root = self._stage_roots[stage].resolve(strict=True)
                root_relative = root.relative_to(
                    self.execution_root
                ).as_posix()
            except (OSError, TypeError, ValueError) as error:
                raise AssertionError(
                    "FORMAL_FULL_Q1_PACKAGE_ROOT_OUTSIDE_EXECUTION"
                ) from error
            for artifact in self._stage_bindings[stage]["artifacts"]:
                prefix = f"{stage}:"
                role = artifact.get("role")
                if not isinstance(role, str) or not role.startswith(
                    prefix
                ):
                    raise AssertionError(
                        "FORMAL_FULL_Q1_BOUND_ARTIFACT_INVALID"
                    )
                relative = role[len(prefix) :]
                normalized = PurePosixPath(relative)
                if (
                    not relative
                    or normalized.is_absolute()
                    or ".." in normalized.parts
                    or artifact.get("execution_path")
                    != f"{root_relative}/{relative}"
                ):
                    raise AssertionError(
                        "FORMAL_FULL_Q1_BOUND_ARTIFACT_INVALID"
                    )
                expected_source_inventory.append(
                    {
                        "path": f"{stage}/{relative}",
                        "sha256": artifact["sha256"],
                    }
                )
        source_inventory = frozen.get("source_inventory")
        if source_inventory != expected_source_inventory:
            raise AssertionError(
                "FORMAL_FULL_Q1_SOURCE_INVENTORY_INVALID"
            )
        source_inventory_sha256 = rt.canonical_sha256(
            expected_source_inventory
        )
        full_by_path = {
            item["path"]: item["sha256"]
            for item in expected_source_inventory
        }
        if len(full_by_path) != len(expected_source_inventory):
            raise AssertionError(
                "FORMAL_FULL_Q1_SOURCE_INVENTORY_INVALID"
            )
        expected_handoff_inventory = []
        for stage in expected:
            for relative in (
                q1.STAGE_CANONICAL[stage],
                "package-manifest.json",
            ):
                path = f"{stage}/{relative}"
                if path not in full_by_path:
                    raise AssertionError(
                        "FORMAL_FULL_Q1_HANDOFF_SOURCE_INVENTORY_INVALID"
                    )
                expected_handoff_inventory.append(
                    {"path": path, "sha256": full_by_path[path]}
                )
        expected_handoff_inventory.sort(
            key=lambda item: item["path"]
        )
        handoff_inventory = frozen.get("handoff_source_inventory")
        if (
            handoff_inventory != expected_handoff_inventory
            or len(expected_handoff_inventory) != 12
        ):
            raise AssertionError(
                "FORMAL_FULL_Q1_HANDOFF_SOURCE_INVENTORY_INVALID"
            )
        handoff_inventory_sha256 = rt.canonical_sha256(
            expected_handoff_inventory
        )
        package_roots = frozen.get("package_roots")
        if not isinstance(package_roots, Mapping) or set(
            package_roots
        ) != set(expected):
            raise AssertionError(
                "FORMAL_FULL_Q1_PACKAGE_ROOTS_INVALID"
            )
        resolved_root_inventory = []
        for stage in expected:
            try:
                resolved_root = Path(package_roots[stage]).resolve(
                    strict=True
                )
                relative_root = resolved_root.relative_to(
                    self.execution_root
                ).as_posix()
            except (OSError, TypeError, ValueError) as error:
                raise AssertionError(
                    "FORMAL_FULL_Q1_PACKAGE_ROOT_OUTSIDE_EXECUTION"
                ) from error
            resolved_root_inventory.append(
                (stage, resolved_root, relative_root)
            )
        if len(
            {resolved for _, resolved, _ in resolved_root_inventory}
        ) != len(expected):
            raise AssertionError(
                "FORMAL_FULL_Q1_PACKAGE_ROOTS_NOT_DISTINCT"
            )
        root_bindings = []
        for stage, resolved_root, relative_root in (
            resolved_root_inventory
        ):
            try:
                bound_root = self._stage_roots[stage].resolve(
                    strict=True
                )
            except (OSError, TypeError, ValueError) as error:
                raise AssertionError(
                    f"FORMAL_FULL_Q1_PACKAGE_ROOT_INVALID: {stage}"
                ) from error
            if resolved_root != bound_root:
                raise AssertionError(
                    f"FORMAL_FULL_Q1_PACKAGE_ROOT_INVALID: {stage}"
                )
            root_bindings.append(
                {
                    "stage": stage,
                    "role": f"{stage}_package_root",
                    "execution_path": relative_root,
                }
            )
        frozen_artifact = self._output_artifact(
            "Q1-controller:frozen-inputs.json",
            resolved_frozen_path,
        )
        admission = {
            "frozen_document_sha256": rt.canonical_sha256(frozen),
            "frozen_artifact": frozen_artifact,
            "baseline_completion": copy.deepcopy(
                expected_completion["B0"]
            ),
            "upstream_completions": copy.deepcopy(upstream),
            "controller_identity": copy.deepcopy(
                dict(controller_identity)
            ),
            "generation_identity_inventory_sha256": (
                rt.canonical_sha256(generation_identities)
            ),
            "input_gate": copy.deepcopy(input_gate.reference),
            "state_before_sha256": rt.canonical_sha256(
                input_gate.data["run_state"]
            ),
            "source_inventory_count": len(
                expected_source_inventory
            ),
            "source_inventory_sha256": source_inventory_sha256,
            "handoff_source_inventory_count": len(
                expected_handoff_inventory
            ),
            "handoff_source_inventory_sha256": (
                handoff_inventory_sha256
            ),
            "package_root_bindings": root_bindings,
        }
        admission["admission_sha256"] = rt.canonical_sha256(admission)
        self._q1_controller_admission = admission
        self._q1_frozen_path = resolved_frozen_path

    def bind_p1_slc_index_ledger(
        self,
        ledger: list[dict[str, Any]],
    ) -> None:
        structurally_valid = all(
            item.get("connection_id")
            == item.get("definition", {}).get("id")
            == item.get("reference", {}).get("target_id")
            and item["definition"].get("stage") == "S1"
            and re.fullmatch(
                r"/connections/[0-9]+",
                str(item["definition"].get("json_pointer", "")),
            )
            is not None
            and re.fullmatch(
                r"[0-9a-f]{64}",
                str(item["definition"].get("value_sha256", "")),
            )
            is not None
            and item["reference"].get("stage") == "T1"
            and item["reference"].get("field") == "connection_id"
            and re.fullmatch(
                r"/connection_realization/[0-9]+/connection_id",
                str(item["reference"].get("json_pointer", "")),
            )
            is not None
            for item in ledger
        )
        if (
            self._p1_slc_index_ledger is not None
            or not ledger
            or len({item["connection_id"] for item in ledger})
            != len(ledger)
            or not structurally_valid
        ):
            raise AssertionError(
                "FORMAL_FULL_P1_SLC_LEDGER_INVALID"
            )
        self._p1_slc_index_ledger = copy.deepcopy(ledger)

    def bind_final_state(self, coordinator: Any) -> None:
        if tuple(self._stage_bindings) != self._STAGES:
            raise AssertionError(
                "FORMAL_FULL_FINAL_STATE_BEFORE_ALL_STAGES"
            )
        state = copy.deepcopy(coordinator.state)
        reference = copy.deepcopy(coordinator.state_reference)
        if (
            state.get("revision") != len(self._STAGES)
            or set(state["current_stage_completions"])
            != set(self._STAGES)
            or reference.get("sha256") != rt.canonical_sha256(state)
        ):
            raise AssertionError("FORMAL_FULL_FINAL_STATE_INVALID")
        self._final_state = {
            "state": state,
            "reference": reference,
        }

    def __enter__(self) -> "_FormalFullChainProvenanceGuard":
        return self

    def _write_forensic(self, code: str, message: str) -> None:
        path = self.directory / "forensic-failure.json"
        if path.exists():
            return
        _write_json_atomic(
            path,
            {
                "schema_version": "1.0",
                "kind": "formal-full-chain-forensic-failure",
                "run_id": self.run_id,
                "code": code,
                "message": message,
                "bound_stages": list(self._stage_bindings),
            },
        )

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:
        if exc_type is not None:
            self._write_forensic(
                getattr(exc_type, "__name__", str(exc_type)),
                str(exc_value),
            )
            return False
        if (
            tuple(self._stage_bindings) != self._STAGES
            or self._initial_state is None
            or self._final_state is None
            or self._q1_controller_admission is None
            or self._q1_frozen_path is None
            or self._p1_slc_index_ledger is None
        ):
            self._write_forensic(
                "FORMAL_FULL_PROVENANCE_INCOMPLETE",
                "required B0-P1 bindings are incomplete",
            )
            raise AssertionError(
                "FORMAL_FULL_PROVENANCE_INCOMPLETE"
            )
        if (
            self._capture_inputs() != self._bound
            or rt.sha256_file(self.start_path) != self._start_sha256
        ):
            self._write_forensic(
                "FORMAL_FULL_INPUT_DRIFT",
                "formal inputs or current implementation changed",
            )
            raise AssertionError("FORMAL_FULL_INPUT_DRIFT")
        for stage, paths in self._stage_paths.items():
            package = self._stage_roots[stage]
            current = [
                self._output_artifact(
                    (
                        f"{stage}:"
                        f"{path.relative_to(package).as_posix()}"
                    ),
                    path,
                )
                for path in paths
            ]
            if current != self._stage_bindings[stage]["artifacts"]:
                self._write_forensic(
                    "FORMAL_FULL_OUTPUT_DRIFT",
                    stage,
                )
                raise AssertionError(
                    f"FORMAL_FULL_OUTPUT_DRIFT: {stage}"
                )
        current_frozen_artifact = self._output_artifact(
            "Q1-controller:frozen-inputs.json",
            self._q1_frozen_path,
        )
        if current_frozen_artifact != self._q1_controller_admission[
            "frozen_artifact"
        ]:
            self._write_forensic(
                "FORMAL_FULL_Q1_FROZEN_ARTIFACT_DRIFT",
                "Q1 controller frozen-inputs.json changed",
            )
            raise AssertionError(
                "FORMAL_FULL_Q1_FROZEN_ARTIFACT_DRIFT"
            )
        _write_json_atomic(
            self.end_path,
            {
                "schema_version": "1.0",
                "kind": "formal-full-chain-provenance-bound",
                "status": "ready",
                "claim_scope": (
                    "exact-formal-manifest-admitted-current-"
                    "implementation-B0-through-P1-ready-publications-"
                    "and-final-state"
                ),
                "run_id": self.run_id,
                "start_marker": {
                    "path": E2E_PROVENANCE_START,
                    "sha256": self._start_sha256,
                },
                "initial_state": copy.deepcopy(self._initial_state),
                "stages": copy.deepcopy(self._stage_bindings),
                "q1_controller_admission": copy.deepcopy(
                    self._q1_controller_admission
                ),
                "p1_slc_index_ledger": copy.deepcopy(
                    self._p1_slc_index_ledger
                ),
                "final_state": copy.deepcopy(self._final_state),
                **self._bound,
            },
        )
        return False


def _assert_exact_current_stage_keys(
    test: unittest.TestCase,
    state: Mapping[str, Any],
    expected_stages: tuple[str, ...],
) -> None:
    """Assert an exact topology prefix without relying on JSON object order."""
    current = state["current_stage_completions"]
    test.assertEqual(set(expected_stages), set(current))
    test.assertEqual(
        list(expected_stages),
        [stage for stage in rt.STAGE_ORDER if stage in current],
    )


def _reference(owner: Path, target: Path, **extra: str) -> dict[str, str]:
    value = {
        "path": Path(os.path.relpath(target.resolve(), owner.parent.resolve())).as_posix(),
        "sha256": rt.sha256_file(target),
    }
    value.update(extra)
    return value


@contextlib.contextmanager
def _thread(thread_id: str) -> Iterator[None]:
    with _identity(thread_id, thread_id):
        yield


@contextlib.contextmanager
def _identity(task_id: str, thread_id: str) -> Iterator[None]:
    previous_task = os.environ.get("CODEX_TASK_ID")
    previous_thread = os.environ.get("CODEX_THREAD_ID")
    os.environ["CODEX_TASK_ID"] = task_id
    os.environ["CODEX_THREAD_ID"] = thread_id
    try:
        yield
    finally:
        if previous_task is None:
            os.environ.pop("CODEX_TASK_ID", None)
        else:
            os.environ["CODEX_TASK_ID"] = previous_task
        if previous_thread is None:
            os.environ.pop("CODEX_THREAD_ID", None)
        else:
            os.environ["CODEX_THREAD_ID"] = previous_thread


def _group_fixture_interviews(
    interviews: Any,
) -> dict[str, list[Mapping[str, Any]]]:
    """Validate and group declarative controls into the six interview stages."""

    if not isinstance(interviews, list) or not interviews:
        raise ValueError(
            "E2E_FIXTURE_INTERVIEWS_INVALID: interviews must be non-empty"
        )
    grouped: dict[str, list[Mapping[str, Any]]] = {
        stage: [] for stage in INTERVIEW_STAGES
    }
    stage_positions = {
        stage: index for index, stage in enumerate(INTERVIEW_STAGES)
    }
    previous_position = -1
    control_ids: set[str] = set()
    for index, item in enumerate(interviews):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"E2E_FIXTURE_INTERVIEWS_INVALID: interviews[{index}] "
                "must be an object"
            )
        stage = item.get("stage")
        if stage not in stage_positions:
            raise ValueError(
                f"E2E_FIXTURE_STAGE_INVALID: interviews[{index}]={stage!r}"
            )
        position = stage_positions[stage]
        if position < previous_position:
            raise ValueError(
                "E2E_FIXTURE_STAGE_ORDER_INVALID: stage blocks must be "
                "non-decreasing I0..I5"
            )
        previous_position = position
        control_id = item.get("control_id")
        if not isinstance(control_id, str) or not control_id.strip():
            raise ValueError(
                f"E2E_FIXTURE_CONTROL_ID_INVALID: interviews[{index}]"
            )
        if control_id in control_ids:
            raise ValueError(
                f"E2E_FIXTURE_CONTROL_ID_DUPLICATE: {control_id}"
            )
        control_ids.add(control_id)
        grouped[stage].append(item)
    missing = [
        stage for stage in INTERVIEW_STAGES if not grouped[stage]
    ]
    if missing:
        raise ValueError(
            "E2E_FIXTURE_STAGE_COVERAGE_INVALID: missing "
            + ",".join(missing)
        )
    return grouped


def _project_fixture_fact_dependencies(
    fact_dependencies: Any,
) -> list[dict[str, Any]]:
    """Project eval provenance facts into the closed production B0 dialect."""

    if not isinstance(fact_dependencies, list) or not fact_dependencies:
        raise ValueError(
            "E2E_FIXTURE_FACTS_INVALID: fact_dependencies must be non-empty"
        )
    projected: list[dict[str, Any]] = []
    seen: set[str] = set()
    core_fields = {"id", "status", "claim", "rationale"}
    allowed_fields = core_fields | {"source_ids"}
    for index, value in enumerate(fact_dependencies):
        if not isinstance(value, Mapping):
            raise ValueError(
                f"E2E_FIXTURE_FACTS_INVALID: fact_dependencies[{index}] "
                "must be an object"
            )
        extra = set(value) - allowed_fields
        if extra:
            raise ValueError(
                "E2E_FIXTURE_FACT_FIELDS_INVALID: "
                + ",".join(sorted(extra))
            )
        for field in ("id", "claim", "rationale"):
            if (
                not isinstance(value.get(field), str)
                or not value[field].strip()
            ):
                raise ValueError(
                    f"E2E_FIXTURE_FACT_FIELD_INVALID: "
                    f"fact_dependencies[{index}].{field}"
                )
        fact_id = value["id"]
        if fact_id in seen:
            raise ValueError(
                f"E2E_FIXTURE_FACT_ID_DUPLICATE: {fact_id}"
            )
        seen.add(fact_id)
        source_ids = value.get("source_ids", [])
        if (
            not isinstance(source_ids, list)
            or any(
                not isinstance(source_id, str) or not source_id.strip()
                for source_id in source_ids
            )
            or len(source_ids) != len(set(source_ids))
        ):
            raise ValueError(
                f"E2E_FIXTURE_FACT_SOURCE_IDS_INVALID: {fact_id}"
            )
        status = value.get("status")
        if status in {"verified", "unverified"}:
            raise ValueError(
                f"E2E_FIXTURE_FACT_STATUS_UNSUPPORTED: {status}"
            )
        if status != "not_applicable":
            raise ValueError(
                f"E2E_FIXTURE_FACT_STATUS_INVALID: {status!r}"
            )
        projected.append(
            {
                "id": fact_id,
                "status": "not_applicable",
                "claim": value["claim"],
                "rationale": value["rationale"],
            }
        )
    return projected


class DeclarativeInterviewSource:
    """Materialize a sealed synthetic interview chain from one eval fixture."""

    def __init__(self, root: Path, fixture_path: Path) -> None:
        self.root = root
        self.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.run_id = self.fixture["run_id"]
        grouped_interviews = _group_fixture_interviews(
            self.fixture["interviews"]
        )

        self.completions: dict[str, Path] = {}
        for stage in INTERVIEW_STAGES:
            items = grouped_interviews[stage]
            directory = root / "interviews" / stage
            state = directory / "run-state.input.json"
            _write_json(
                state,
                {
                    "harness": "novel-conception-interview",
                    "run_id": self.run_id,
                    "active_return": None,
                    "current_interview_completions": {
                        key: _reference(state, value)
                        for key, value in self.completions.items()
                    },
                    "resolved_returns": [],
                },
            )
            design = directory / "design.md"
            design.parent.mkdir(parents=True, exist_ok=True)
            control_sections = "\n\n".join(
                (
                    f"## [{item['control_id']}][{item['hardness']}] "
                    f"{item['heading']}\n\n{item['value']}"
                )
                for item in items
            )
            design.write_text(
                f"# {stage}\n\n{control_sections}\n",
                encoding="utf-8",
                newline="",
            )
            report = directory / "report.md"
            report.write_text(
                f"# {stage} complete interview report\n",
                encoding="utf-8",
                newline="",
            )
            validation = directory / "validation.json"
            _write_json(
                validation,
                {"run_id": self.run_id, "verdict": "ready", "errors": []},
            )
            completion = directory / "stage-completion.json"
            _write_json(
                completion,
                {
                    "harness": "novel-conception-interview",
                    "run_id": self.run_id,
                    "stage": stage,
                    "session_id": f"SESSION-{stage}",
                    "status": "ready",
                    "design_artifact": "design.md",
                    "design_artifact_sha256": rt.sha256_file(design),
                    "report": _reference(completion, report),
                    "validation": _reference(
                        completion, validation, verdict="ready"
                    ),
                    "input_completions": [
                        _reference(completion, value)
                        for value in self.completions.values()
                    ],
                    "run_state": _reference(completion, state),
                },
            )
            self.completions[stage] = completion

        v1_dir = root / "interviews" / "V1"
        self.state = v1_dir / "run-state.input.json"
        _write_json(
            self.state,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "active_return": None,
                "current_interview_completions": {
                    key: _reference(self.state, value)
                    for key, value in self.completions.items()
                },
                "resolved_returns": [],
            },
        )
        self.fact_register = v1_dir / "fact-dependency-register.json"
        _write_json(
            self.fact_register,
            {
                "schema_version": "1.0",
                "run_id": self.run_id,
                "status": "ready",
                "fact_dependencies": _project_fixture_fact_dependencies(
                    self.fixture["fact_dependencies"]
                ),
            },
        )
        v1_validation = v1_dir / "validation.json"
        _write_json(
            v1_validation,
            {"run_id": self.run_id, "verdict": "ready", "errors": []},
        )
        v1_report = v1_dir / "integrity-report.md"
        v1_report.write_text("# Complete integrity audit\n", encoding="utf-8")
        semantic = v1_dir / "semantic-review.json"
        _write_json(
            semantic,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V1",
                "verdict": "pass",
                "reviewer_role": "integrity_auditor",
                "return_package": None,
                "evidence": [
                    {
                        "control_area": name,
                        "owner_stage": stage,
                        "artifact": "design.md",
                        "finding": f"{name} has current evidence.",
                    }
                    for name, stage in (
                        ("intent", "I0"),
                        ("subject", "I1"),
                        ("world", "I2"),
                        ("character", "I3"),
                        ("causality", "I4"),
                        ("narrative", "I5"),
                    )
                ],
            },
        )
        self.v1 = v1_dir / "stage-completion.json"
        _write_json(
            self.v1,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V1",
                "session_id": "SESSION-V1",
                "status": "ready",
                "design_artifact": "integrity-report.md",
                "design_artifact_sha256": rt.sha256_file(v1_report),
                "validation": _reference(
                    self.v1, v1_validation, verdict="ready"
                ),
                "input_completions": [
                    _reference(self.v1, value)
                    for value in self.completions.values()
                ],
                "fact_dependency_register": _reference(
                    self.v1, self.fact_register
                ),
                "semantic_review": _reference(self.v1, semantic),
                "run_state": _reference(self.v1, self.state),
            },
        )

        v2_dir = root / "interviews" / "V2"
        self.brief = v2_dir / "review-brief.html"
        self.brief.parent.mkdir(parents=True, exist_ok=True)
        self.brief.write_text("<h1>Approved review brief</h1>", encoding="utf-8")
        v2_validation = v2_dir / "validation.json"
        _write_json(
            v2_validation,
            {"run_id": self.run_id, "verdict": "ready", "errors": []},
        )
        self.v2 = v2_dir / "stage-completion.json"
        _write_json(
            self.v2,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "stage": "V2",
                "session_id": "SESSION-V2",
                "status": "ready",
                "design_artifact": "review-brief.html",
                "design_artifact_sha256": rt.sha256_file(self.brief),
                "validation": _reference(
                    self.v2, v2_validation, verdict="ready"
                ),
                "input_completions": [_reference(self.v2, self.v1)],
                "run_state": _reference(self.v2, self.state),
            },
        )
        self.approval = v2_dir / "author-approval.json"
        _write_json(
            self.approval,
            {
                "harness": "novel-conception-interview",
                "run_id": self.run_id,
                "approval_scope": "V2",
                "decision": "approved",
                "record_assurance": "self_recorded",
                "review_brief": _reference(self.approval, self.brief),
                "approval_record": {
                    "event_seq": 1,
                    "text": "Approve this V2 review brief.",
                },
            },
        )

    def build_args(self, package: Path, gate: Any) -> dict[str, Any]:
        return {
            "package_root": package,
            "run_id": self.run_id,
            "input_gate": gate,
            "source_root": self.root,
            "source_interview_state": self.state,
            "design_completions": self.completions,
            "v1_completion": self.v1,
            "v2_completion": self.v2,
            "v2_author_approval": self.approval,
            "fact_dependency_register": self.fact_register,
        }


class DeclarativeInterviewSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="declarative-interview-source-"
        )
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_fixture(
        self, fixture: Mapping[str, Any], name: str
    ) -> Path:
        path = self.root / "fixtures" / f"{name}.json"
        _write_json(path, fixture)
        return path

    @staticmethod
    def _expected_controls(
        fixture: Mapping[str, Any], stage: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": item["control_id"],
                "hardness": item["hardness"],
                "heading": (
                    f"[{item['control_id']}][{item['hardness']}] "
                    f"{item['heading']}"
                ),
                "value": item["value"],
            }
            for item in fixture["interviews"]
            if item["stage"] == stage
        ]

    def test_duanxian_groups_all_controls_without_losing_evidence(self) -> None:
        fixture_bytes_before = DUANXIAN_FIXTURE.read_bytes()
        fixture = json.loads(fixture_bytes_before.decode("utf-8"))
        source = DeclarativeInterviewSource(
            self.root / "duanxian-source", DUANXIAN_FIXTURE
        )

        self.assertEqual(list(INTERVIEW_STAGES), list(source.completions))
        extracted: list[dict[str, Any]] = []
        for stage in INTERVIEW_STAGES:
            stage_controls = rt.extract_controls(
                source.completions[stage].parent / "design.md",
                stage,
            )
            self.assertEqual(
                self._expected_controls(fixture, stage),
                stage_controls,
            )
            extracted.extend(stage_controls)
        self.assertEqual(22, len(extracted))
        self.assertEqual(
            [item["control_id"] for item in fixture["interviews"]],
            [item["id"] for item in extracted],
        )

        self.assertEqual(fixture, source.fixture)
        self.assertEqual(
            fixture["provenance_manifest"],
            source.fixture["provenance_manifest"],
        )
        self.assertEqual(
            fixture["evidence_manifest"],
            source.fixture["evidence_manifest"],
        )
        self.assertEqual(
            [
                item["provenance_source_ids"]
                for item in fixture["interviews"]
            ],
            [
                item["provenance_source_ids"]
                for item in source.fixture["interviews"]
            ],
        )
        self.assertEqual(
            fixture["semantic_assertions"],
            source.fixture["semantic_assertions"],
        )
        fact_register = json.loads(
            source.fact_register.read_text(encoding="utf-8")
        )
        self.assertEqual(
            [
                {
                    "id": "FACT-DX-001",
                    "status": "not_applicable",
                    "claim": fixture["fact_dependencies"][0]["claim"],
                    "rationale": fixture["fact_dependencies"][0][
                        "rationale"
                    ],
                }
            ],
            fact_register["fact_dependencies"],
        )
        self.assertEqual(
            [
                "SRC-I2-ARTIFACT",
                "SRC-V1-SEMANTIC",
                "SRC-V2-APPROVAL",
            ],
            source.fixture["fact_dependencies"][0]["source_ids"],
        )
        fact_runtime = rt.ContractRuntime()
        for fact in fact_register["fact_dependencies"]:
            fact_runtime.validate_definition(
                fact,
                "author-control-baseline.schema.json",
                "factDependency",
            )
        adapter = proposal_module.DeclarativeProposalAdapter(source.fixture)
        self.assertEqual(fixture, adapter.fixture)
        for field in ("provenance_manifest", "evidence_manifest"):
            reference = fixture[field]
            evidence_path = DUANXIAN_FIXTURE.parent / reference["path"]
            self.assertEqual(
                reference["sha256"], rt.sha256_file(evidence_path)
            )
        self.assertEqual(
            fixture_bytes_before, DUANXIAN_FIXTURE.read_bytes()
        )

        state = json.loads(source.state.read_text(encoding="utf-8"))
        self.assertEqual(
            set(INTERVIEW_STAGES),
            set(state["current_interview_completions"]),
        )
        v1 = json.loads(source.v1.read_text(encoding="utf-8"))
        self.assertEqual(6, len(v1["input_completions"]))

    def test_generic_single_control_materialization_is_unchanged(self) -> None:
        fixture = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        source = DeclarativeInterviewSource(
            self.root / "generic-source", GENERIC_FIXTURE
        )

        self.assertEqual(fixture, source.fixture)
        self.assertEqual(list(INTERVIEW_STAGES), list(source.completions))
        fact_register = json.loads(
            source.fact_register.read_text(encoding="utf-8")
        )
        self.assertEqual(
            fixture["fact_dependencies"],
            fact_register["fact_dependencies"],
        )
        fact_runtime = rt.ContractRuntime()
        for fact in fact_register["fact_dependencies"]:
            fact_runtime.validate_definition(
                fact,
                "author-control-baseline.schema.json",
                "factDependency",
            )
        for item in fixture["interviews"]:
            stage = item["stage"]
            design = source.completions[stage].parent / "design.md"
            self.assertEqual(
                (
                    f"# {stage}\n\n"
                    f"## [{item['control_id']}][{item['hardness']}] "
                    f"{item['heading']}\n\n{item['value']}\n"
                ),
                design.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                self._expected_controls(fixture, stage),
                rt.extract_controls(design, stage),
            )
        proposal_module.DeclarativeProposalAdapter(source.fixture)

    def test_fact_projection_rejects_duplicate_empty_or_extra_fields(
        self,
    ) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        original = generic["fact_dependencies"][0]
        duplicate = [copy.deepcopy(original), copy.deepcopy(original)]
        empty_id = [copy.deepcopy(original)]
        empty_id[0]["id"] = ""
        empty_claim = [copy.deepcopy(original)]
        empty_claim[0]["claim"] = ""
        empty_rationale = [copy.deepcopy(original)]
        empty_rationale[0]["rationale"] = ""
        extra = [copy.deepcopy(original)]
        extra[0]["unexpected"] = "not production evidence"

        for name, facts, code in (
            ("duplicate", duplicate, "E2E_FIXTURE_FACT_ID_DUPLICATE"),
            ("empty-id", empty_id, "E2E_FIXTURE_FACT_FIELD_INVALID"),
            (
                "empty-claim",
                empty_claim,
                "E2E_FIXTURE_FACT_FIELD_INVALID",
            ),
            (
                "empty-rationale",
                empty_rationale,
                "E2E_FIXTURE_FACT_FIELD_INVALID",
            ),
            ("extra", extra, "E2E_FIXTURE_FACT_FIELDS_INVALID"),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, code
            ):
                _project_fixture_fact_dependencies(facts)

    def test_fact_projection_rejects_bad_eval_source_ids(self) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        original = generic["fact_dependencies"][0]
        cases = {
            "not-list": "SRC-ONE",
            "empty": ["SRC-ONE", ""],
            "duplicate": ["SRC-ONE", "SRC-ONE"],
        }
        for name, source_ids in cases.items():
            fact = copy.deepcopy(original)
            fact["source_ids"] = source_ids
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, "E2E_FIXTURE_FACT_SOURCE_IDS_INVALID"
            ):
                _project_fixture_fact_dependencies([fact])

    def test_fact_projection_does_not_infer_verified_or_unverified(
        self,
    ) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        for status in ("verified", "unverified"):
            fact = copy.deepcopy(generic["fact_dependencies"][0])
            fact["status"] = status
            with self.subTest(status=status), self.assertRaisesRegex(
                ValueError, "E2E_FIXTURE_FACT_STATUS_UNSUPPORTED"
            ):
                _project_fixture_fact_dependencies([fact])

    def test_missing_or_invalid_stage_fails_closed(self) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        cases: list[tuple[str, dict[str, Any], str]] = []

        empty = copy.deepcopy(generic)
        empty["interviews"] = []
        cases.append(("empty", empty, "E2E_FIXTURE_INTERVIEWS_INVALID"))

        missing = copy.deepcopy(generic)
        missing["interviews"] = [
            item for item in missing["interviews"]
            if item["stage"] != "I5"
        ]
        cases.append(
            ("missing", missing, "E2E_FIXTURE_STAGE_COVERAGE_INVALID")
        )

        invalid = copy.deepcopy(generic)
        invalid["interviews"][0]["stage"] = "I6"
        cases.append(("invalid", invalid, "E2E_FIXTURE_STAGE_INVALID"))

        for name, fixture, code in cases:
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, code
            ):
                DeclarativeInterviewSource(
                    self.root / f"source-{name}",
                    self._write_fixture(fixture, name),
                )

    def test_stage_order_and_back_insertion_fail_closed(self) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        reversed_blocks = copy.deepcopy(generic)
        (
            reversed_blocks["interviews"][0],
            reversed_blocks["interviews"][1],
        ) = (
            reversed_blocks["interviews"][1],
            reversed_blocks["interviews"][0],
        )
        back_inserted = copy.deepcopy(generic)
        extra = copy.deepcopy(back_inserted["interviews"][0])
        extra["control_id"] = "INT-002"
        back_inserted["interviews"].append(extra)

        for name, fixture in (
            ("reversed", reversed_blocks),
            ("back-inserted", back_inserted),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, "E2E_FIXTURE_STAGE_ORDER_INVALID"
            ):
                DeclarativeInterviewSource(
                    self.root / f"source-{name}",
                    self._write_fixture(fixture, name),
                )

    def test_duplicate_or_empty_control_id_fails_closed(self) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        same_stage = copy.deepcopy(generic)
        same_stage["interviews"].insert(
            1, copy.deepcopy(same_stage["interviews"][0])
        )
        cross_stage = copy.deepcopy(generic)
        cross_stage["interviews"][1]["control_id"] = "INT-001"
        empty = copy.deepcopy(generic)
        empty["interviews"][0]["control_id"] = ""

        for name, fixture, code in (
            (
                "same-stage",
                same_stage,
                "E2E_FIXTURE_CONTROL_ID_DUPLICATE",
            ),
            (
                "cross-stage",
                cross_stage,
                "E2E_FIXTURE_CONTROL_ID_DUPLICATE",
            ),
            ("empty", empty, "E2E_FIXTURE_CONTROL_ID_INVALID"),
        ):
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, code
            ):
                DeclarativeInterviewSource(
                    self.root / f"source-{name}",
                    self._write_fixture(fixture, name),
                )


class ExecutionProvenanceGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="e2e-execution-provenance-"
        )
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _files(self, name: str) -> dict[str, Path]:
        repository = self.root / name / "repository"
        driver = repository / "testing" / "driver.py"
        proposal = repository / "harness" / "proposal.py"
        fixture = repository / "fixtures" / "fixture.json"
        driver.parent.mkdir(parents=True)
        proposal.parent.mkdir(parents=True)
        fixture.parent.mkdir(parents=True)
        driver.write_text("DRIVER = 1\n", encoding="utf-8", newline="")
        proposal.write_text(
            "PROPOSAL = 1\n", encoding="utf-8", newline=""
        )
        _write_json(
            fixture,
            {"schema_version": "1.0", "run_id": "RUN-PROVENANCE"},
        )
        return {
            "repository": repository,
            "driver": driver,
            "proposal": proposal,
            "fixture": fixture,
            "markers": self.root / name / "markers",
        }

    @staticmethod
    def _guard(paths: Mapping[str, Path]) -> _ExecutionProvenanceGuard:
        return _ExecutionProvenanceGuard(
            directory=paths["markers"],
            repository_root=paths["repository"],
            driver_path=paths["driver"],
            proposal_path=paths["proposal"],
            fixture_path=paths["fixture"],
            run_id="RUN-PROVENANCE",
        )

    def test_opt_out_creates_no_marker_or_directory(self) -> None:
        paths = self._files("opt-out")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(E2E_PROVENANCE_ENV, None)
            guard = _start_execution_provenance_guard(GENERIC_FIXTURE)
        self.assertIsNone(guard)
        self.assertFalse(paths["markers"].exists())

    def test_normal_exit_writes_strict_start_and_hash_stable_end(self) -> None:
        paths = self._files("normal")
        guard = self._guard(paths)
        with guard:
            pass

        start = json.loads(guard.start_path.read_text(encoding="utf-8"))
        end = json.loads(guard.end_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schema_version",
                "kind",
                "run_id",
                "fixture",
                "implementation",
                "implementation_inventory_sha256",
            },
            set(start),
        )
        self.assertEqual(
            {
                "schema_version",
                "kind",
                "status",
                "claim_scope",
                "run_id",
                "start_marker",
                "fixture",
                "implementation",
                "implementation_inventory_sha256",
            },
            set(end),
        )
        self.assertEqual("hash-stable", end["status"])
        self.assertNotIn("success", rt.canonical_json(end).casefold())
        self.assertEqual(
            rt.sha256_file(guard.start_path),
            end["start_marker"]["sha256"],
        )
        self.assertEqual(start["fixture"], end["fixture"])
        self.assertEqual(start["implementation"], end["implementation"])
        self.assertNotIn("absolute_path", rt.canonical_json(start))
        self.assertNotIn("absolute_path", rt.canonical_json(end))
        for artifact in [
            start["fixture"],
            *start["implementation"],
        ]:
            self.assertEqual(
                {"role", "repository_path", "sha256"},
                set(artifact),
            )

    def test_preexisting_start_or_end_marker_fails_closed(self) -> None:
        for marker in (E2E_PROVENANCE_START, E2E_PROVENANCE_END):
            with self.subTest(marker=marker):
                paths = self._files(f"preexisting-{marker}")
                existing = paths["markers"] / marker
                _write_json(existing, {"forensic": True})
                with self.assertRaisesRegex(
                    AssertionError, "E2E_PROVENANCE_MARKER_EXISTS"
                ):
                    self._guard(paths)
                self.assertEqual(
                    {"forensic": True},
                    json.loads(existing.read_text(encoding="utf-8")),
                )

    def test_driver_adapter_or_fixture_drift_rejects_without_end(self) -> None:
        for field in ("driver", "proposal", "fixture"):
            with self.subTest(field=field):
                paths = self._files(f"drift-{field}")
                guard = self._guard(paths)
                with self.assertRaisesRegex(
                    AssertionError, "E2E_PROVENANCE_DRIFT"
                ):
                    with guard:
                        paths[field].write_bytes(
                            paths[field].read_bytes() + b"DRIFT"
                        )
                self.assertTrue(guard.start_path.is_file())
                self.assertFalse(guard.end_path.exists())

    def test_abnormal_exit_with_stable_hashes_leaves_start_only(self) -> None:
        paths = self._files("abnormal")
        guard = self._guard(paths)
        with self.assertRaisesRegex(RuntimeError, "in-test failure"):
            with guard:
                raise RuntimeError("in-test failure")
        self.assertTrue(guard.start_path.is_file())
        self.assertFalse(guard.end_path.exists())

    def test_b0_and_w1_early_stops_write_hash_stable_end(self) -> None:
        for stop_after in ("B0", "W1"):
            with self.subTest(stop_after=stop_after):
                provenance = self.root / f"early-{stop_after}"
                environment = {
                    E2E_PROVENANCE_ENV: str(provenance),
                    "CONCEPTION_E2E_FIXTURE": str(GENERIC_FIXTURE),
                    "CONCEPTION_E2E_ROOT": "",
                    "CONCEPTION_E2E_STOP_AFTER": stop_after,
                }
                case = GenericRealChainProbe(
                    "test_real_public_entries_reach_p1"
                )
                result = unittest.TestResult()
                with mock.patch.dict(os.environ, environment, clear=False):
                    case.run(result)
                self.assertTrue(result.wasSuccessful(), result.errors)
                start = json.loads(
                    (provenance / E2E_PROVENANCE_START).read_text(
                        encoding="utf-8"
                    )
                )
                end = json.loads(
                    (provenance / E2E_PROVENANCE_END).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("hash-stable", end["status"])
                self.assertEqual(
                    rt.sha256_file(
                        provenance / E2E_PROVENANCE_START
                    ),
                    end["start_marker"]["sha256"],
                )
                self.assertEqual(
                    start["implementation"], end["implementation"]
                )

    def test_root_context_exit_failure_after_b0_leaves_start_only(
        self,
    ) -> None:
        provenance = self.root / "root-exit-failure-markers"
        chain_root = self.root / "root-exit-failure-chain"
        chain_root.mkdir()

        class FailingRootContext:
            def __enter__(self) -> str:
                return str(chain_root)

            def __exit__(
                self,
                exc_type: Any,
                exc_value: Any,
                traceback: Any,
            ) -> bool:
                raise RuntimeError("root context exit failure")

        environment = {
            E2E_PROVENANCE_ENV: str(provenance),
            "CONCEPTION_E2E_FIXTURE": str(GENERIC_FIXTURE),
            "CONCEPTION_E2E_ROOT": str(chain_root),
            "CONCEPTION_E2E_STOP_AFTER": "B0",
        }
        case = GenericRealChainProbe("test_real_public_entries_reach_p1")
        result = unittest.TestResult()
        with (
            mock.patch.dict(os.environ, environment, clear=False),
            mock.patch.object(
                contextlib,
                "nullcontext",
                return_value=FailingRootContext(),
            ),
        ):
            case.run(result)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(1, len(result.errors))
        self.assertIn("root context exit failure", result.errors[0][1])
        self.assertTrue(
            (provenance / E2E_PROVENANCE_START).is_file()
        )
        self.assertFalse((provenance / E2E_PROVENANCE_END).exists())


def _read_model(package: Path, name: str) -> dict[str, Any]:
    return json.loads((package / name).read_text(encoding="utf-8"))


def _formal_p1_slc_index_ledger(
    p1_package: Path,
    *,
    storyline: Mapping[str, Any],
    timeline: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Verify the exact S1-definition/T1-reference ledger published by P1."""

    cross_model_index = _read_model(
        p1_package, "cross-model-index.json"
    )
    definitions = cross_model_index.get("definitions")
    references = cross_model_index.get("references")
    if not isinstance(definitions, list) or not isinstance(references, list):
        raise AssertionError("P1_SLC_CROSS_MODEL_INDEX_INVALID")
    connections = storyline.get("connections")
    realizations = timeline.get("connection_realization")
    if not isinstance(connections, list) or not isinstance(
        realizations, list
    ):
        raise AssertionError("P1_SLC_SOURCE_MODELS_INVALID")

    ledger = []
    for source_index, connection in enumerate(connections):
        connection_id = connection["id"]
        matching_definitions = [
            item for item in definitions if item.get("id") == connection_id
        ]
        if len(matching_definitions) != 1:
            raise AssertionError(
                f"P1_SLC_DEFINITION_CARDINALITY_INVALID: {connection_id}"
            )
        definition = matching_definitions[0]
        expected_definition = {
            "stage": "S1",
            "json_pointer": f"/connections/{source_index}",
            "value_sha256": rt.canonical_sha256(connection),
        }
        for field, expected in expected_definition.items():
            if definition.get(field) != expected:
                raise AssertionError(
                    f"P1_SLC_DEFINITION_{field.upper()}_INVALID: "
                    f"{connection_id}"
                )

        matching_realizations = [
            (index, realization)
            for index, realization in enumerate(realizations)
            if realization.get("connection_id") == connection_id
        ]
        if len(matching_realizations) != 1:
            raise AssertionError(
                f"P1_SLC_REALIZATION_CARDINALITY_INVALID: {connection_id}"
            )
        realization_index, _ = matching_realizations[0]
        matching_references = [
            item
            for item in references
            if item.get("target_id") == connection_id
            and item.get("stage") == "T1"
            and item.get("field") == "connection_id"
        ]
        if len(matching_references) != 1:
            raise AssertionError(
                f"P1_SLC_REFERENCE_CARDINALITY_INVALID: {connection_id}"
            )
        reference = matching_references[0]
        expected_reference = {
            "stage": "T1",
            "field": "connection_id",
            "json_pointer": (
                f"/connection_realization/{realization_index}/connection_id"
            ),
        }
        for field, expected in expected_reference.items():
            if reference.get(field) != expected:
                raise AssertionError(
                    f"P1_SLC_REFERENCE_{field.upper()}_INVALID: "
                    f"{connection_id}"
                )
        expected_occurrence = {
            key: definition[key]
            for key in (
                "stage",
                "json_pointer",
                "kind",
                "value_sha256",
            )
        }
        if reference.get("target_occurrences") != [expected_occurrence]:
            raise AssertionError(
                f"P1_SLC_TARGET_OCCURRENCE_INVALID: {connection_id}"
            )
        ledger.append(
            {
                "connection_id": connection_id,
                "definition": copy.deepcopy(definition),
                "reference": copy.deepcopy(reference),
            }
        )
    if {item["connection_id"] for item in ledger} != {
        item["id"] for item in connections
    }:
        raise AssertionError("P1_SLC_LEDGER_COVERAGE_INVALID")
    return ledger


def _write_sealed_envelope(path: Path, document: Any) -> None:
    _write_json(
        path,
        {
            "data": document.data,
            "reference": document.reference,
        },
    )


def _read_sealed_envelope(path: Path) -> Any:
    value = json.loads(path.read_text(encoding="utf-8"))
    if rt.canonical_sha256(value["data"]) != value["reference"]["sha256"]:
        raise AssertionError(f"sealed envelope drift: {path}")
    return rt.SealedDocument(
        data=value["data"], reference=value["reference"]
    )


def _trace_stage(stage: str, gate: Any, package: Path) -> None:
    print(
        rt.canonical_json(
            {
                "stage": stage,
                "gate_sha256": gate.reference["sha256"],
                "completion_sha256": rt.sha256_file(
                    package / "stage-completion.json"
                ),
            }
        ),
        flush=True,
    )


def _submit_all(
    module: Any,
    submit: Any,
    workspace: Path,
    common: dict[str, Any],
    proposal: dict[str, Any],
) -> None:
    for phase in module.PHASES:
        payload = (
            {"model": proposal}
            if phase == module.PHASES[-1]
            else {
                field: proposal[field]
                for field in module.PHASE_FIELDS[phase]
            }
        )
        submit(
            workspace,
            **common,
            phase=phase,
            payload=payload,
        )


class FormalStorylinePlanProjectionTests(unittest.TestCase):
    def _case(self, manifest: Path) -> Any:
        return storyline_quality_module.load_ready_eval_case(manifest)

    def _project(self, manifest: Path) -> tuple[Any, Any, dict[str, Any]]:
        adapter = proposal_module.DeclarativeProposalAdapter.from_manifest(
            manifest
        )
        case = adapter.formal_case_snapshot
        fixture = case.structural_case.fixture
        model = adapter.storyline(
            run_id=fixture["run_id"],
            gate_reference={
                "path": "S1/input-gate.json",
                "sha256": "a" * 64,
            },
            source_artifacts=[
                {
                    "path": "sources/B0/stage-completion.json",
                    "sha256": "b" * 64,
                }
            ],
            controls=[
                {
                    "id": item["control_id"],
                    "hardness": item["hardness"],
                    "heading": (
                        f"[{item['control_id']}]"
                        f"[{item['hardness']}] {item['heading']}"
                    ),
                    "value": copy.deepcopy(item["value"]),
                    "domain": item["stage"],
                }
                for item in fixture["interviews"]
            ],
        )
        rt.ContractRuntime().validate(
            model, "storyline-architecture.schema.json"
        )
        return case, adapter, model

    def test_formal_adapter_requires_quality_admitted_case(self) -> None:
        structural = storyline_plan_module.load_eval_case(
            GENERIC_CASE_MANIFEST
        )
        compatibility = (
            storyline_quality_module.load_storyline_quality_gate(
                GENERIC_CASE_MANIFEST,
                EVALS_ROOT
                / "fixtures"
                / "generic"
                / "storyline-proposal-quality-gate.v1.json",
            )
        )
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "S1_EVAL_MANIFEST_PATH_REQUIRED",
        ):
            proposal_module.DeclarativeProposalAdapter.from_manifest(
                structural
            )
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "S1_EVAL_MANIFEST_PATH_REQUIRED",
        ):
            proposal_module.DeclarativeProposalAdapter.from_manifest(
                structural.fixture
            )
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "S1_EVAL_MANIFEST_PATH_REQUIRED",
        ):
            proposal_module.DeclarativeProposalAdapter.from_manifest(
                compatibility
            )

    def test_formal_adapter_rechecks_open_authority_before_projection(
        self,
    ) -> None:
        adapter = proposal_module.DeclarativeProposalAdapter.from_manifest(
            GENERIC_CASE_MANIFEST
        )
        admitted = adapter.formal_case_snapshot
        open_control = next(
            item["control_id"]
            for item in admitted.structural_case.fixture["interviews"]
            if item["hardness"] == "author_open"
        )
        admitted.structural_case.plan["design_decisions"][0][
            "source_control_ids"
        ].append(open_control)
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "S1_EVAL_MANIFEST_PATH_REQUIRED",
        ):
            proposal_module.DeclarativeProposalAdapter.from_manifest(
                admitted
            )
        self.assertNotIn(
            open_control,
            adapter.formal_case_snapshot.structural_case.plan[
                "design_decisions"
            ][0]["source_control_ids"],
        )

    def test_generic_and_duanxian_project_every_s1_field(self) -> None:
        for manifest in (
            GENERIC_CASE_MANIFEST,
            DUANXIAN_CASE_MANIFEST,
        ):
            with self.subTest(manifest=manifest.name):
                case, adapter, model = self._project(manifest)
                plan = case.structural_case.plan
                plan_lines = {
                    item["id"]: item for item in plan["lines"]
                }
                projected_lines = {
                    item["id"]: item for item in model["storylines"]
                }
                self.assertEqual(
                    [item["id"] for item in plan["demands"]],
                    [item["id"] for item in model["storyline_demands"]],
                )
                for demand, projected in zip(
                    plan["demands"],
                    model["storyline_demands"],
                    strict=True,
                ):
                    self.assertEqual(
                        [demand["source_control_id"]],
                        projected["source_ids"],
                    )
                    self.assertTrue(
                        projected["obligation"].startswith(
                            demand["obligation"]
                        )
                    )
                    self.assertEqual(
                        demand["disposition"], projected["disposition"]
                    )
                for line_id, source in plan_lines.items():
                    projected = projected_lines[line_id]
                    self.assertEqual(
                        source["states"][0]["description"],
                        projected["start_state"],
                    )
                    self.assertEqual(
                        [
                            item["description"]
                            for item in source["states"][1:-1]
                        ],
                        projected["state_changes"],
                    )
                    self.assertEqual(
                        source["states"][-1]["description"],
                        projected["end_state"],
                    )
                    self.assertEqual(
                        source["decision_ids"],
                        projected["source_decision_ids"],
                    )
                states = {
                    state["id"]: (
                        line["id"],
                        index,
                        state["description"],
                    )
                    for line in plan["lines"]
                    for index, state in enumerate(line["states"])
                }
                for source, projected in zip(
                    plan["connections"],
                    model["connections"],
                    strict=True,
                ):
                    self.assertEqual(
                        source["relation"], projected["relation"]
                    )
                    self.assertEqual(
                        states[source["from_state_id"]][1:],
                        (
                            projected["from_state_index"],
                            projected["from_state"],
                        ),
                    )
                    self.assertEqual(
                        states[source["to_state_id"]][1:],
                        (
                            projected["to_state_index"],
                            projected["to_state"],
                        ),
                    )
                self.assertEqual(
                    {
                        key: plan["architecture"][key]
                        for key in model["architecture"]
                    },
                    model["architecture"],
                )
                for stage, field in (
                    ("W1", "world_requirements"),
                    ("E1", "environment_requirements"),
                    ("T1", "event_requirements"),
                    ("C1", "character_requirements"),
                ):
                    for source, projected in zip(
                        plan["downstream_requirements"][stage],
                        model[field],
                        strict=True,
                    ):
                        self.assertEqual(
                            [source["line_id"], *source["demand_ids"]],
                            projected["source_ids"],
                        )
                open_controls = {
                    item["control_id"]
                    for item in case.structural_case.fixture["interviews"]
                    if item["hardness"] == "author_open"
                }
                self.assertEqual(
                    open_controls,
                    {
                        source_id
                        for item in model["open_items"]
                        for source_id in item["source_ids"]
                    },
                )
                causal = next(
                    item
                    for item in model["cross_line_consistency"]
                    if item["dimension"] == "causality"
                )
                associative_ids = {
                    item["id"]
                    for item in model["connections"]
                    if item["relation"] == "associative"
                }
                self.assertFalse(
                    associative_ids & set(causal["witness_ids"])
                )
                for claim in model["derivation_claims"]:
                    if (
                        set(claim["source_ids"]) & open_controls
                    ):
                        self.assertEqual([], claim["decision_ids"])
                self.assertEqual(
                    rt.canonical_sha256(model),
                    adapter.storyline_projection_evidence[
                        "model_sha256"
                    ],
                )

    def test_formal_projection_is_deterministic(self) -> None:
        for manifest in (
            GENERIC_CASE_MANIFEST,
            DUANXIAN_CASE_MANIFEST,
        ):
            with self.subTest(manifest=manifest.name):
                first = self._project(manifest)[2]
                second = self._project(manifest)[2]
                self.assertEqual(
                    rt.canonical_sha256(first),
                    rt.canonical_sha256(second),
                )

    def test_formal_provenance_rejects_exit_without_real_s1_binding(
        self,
    ) -> None:
        admitted = self._case(GENERIC_CASE_MANIFEST)
        with tempfile.TemporaryDirectory(
            prefix="formal-s1-provenance-"
        ) as temporary:
            guard = _FormalS1ExecutionProvenanceGuard(
                directory=Path(temporary) / "markers",
                execution_root=Path(temporary),
                validated_case=admitted,
            )
            with self.assertRaisesRegex(
                AssertionError,
                "E2E_PROVENANCE_S1_OUTPUT_NOT_BOUND",
            ):
                with guard:
                    pass

            start = json.loads(
                guard.start_path.read_text(encoding="utf-8")
            )
            self.assertFalse(guard.end_path.exists())
            self.assertEqual(
                {
                    "case_manifest",
                    "case_manifest_schema",
                    "fixture",
                    "storyline_plan",
                    "storyline_plan_schema",
                    "storyline_quality_gate",
                    "storyline_quality_gate_schema",
                },
                {item["role"] for item in start["case_artifacts"]},
            )
            self.assertEqual(
                {
                    "proposal_authoring_adapter",
                    "storyline_plan_loader",
                    "storyline_quality_loader",
                    "canonical_hash_path_admission",
                    "contract_schema_admission",
                    "test_driver",
                },
                {item["role"] for item in start["implementation"]},
            )

    @staticmethod
    def _fake_s1_binding_args(
        root: Path,
    ) -> tuple[dict[str, Any], dict[str, Path]]:
        model = {"schema_version": "1.0", "model": "exact"}
        paths = {
            "model": root / "packages" / "S1" / "storyline-architecture.json",
            "manifest": root / "packages" / "S1" / "package-manifest.json",
            "completion": root / "packages" / "S1" / "stage-completion.json",
        }
        _write_json(paths["model"], model)
        _write_json(paths["manifest"], {"kind": "manifest"})
        _write_json(paths["completion"], {"status": "ready"})
        state = {
            "revision": 2,
            "current_stage_completions": {
                "S1": {
                    "path": "S1/stage-completion.json",
                    "sha256": rt.sha256_file(paths["completion"]),
                }
            },
        }
        arguments = {
            "projected_model": model,
            "package_model_path": paths["model"],
            "package_manifest_path": paths["manifest"],
            "completion_path": paths["completion"],
            "revision2_state": state,
            "projection_evidence": {
                "model_sha256": rt.canonical_sha256(model)
            },
            "revision2_state_reference": {
                "path": "state/revision-002.json",
                "sha256": rt.canonical_sha256(state),
            },
        }
        return arguments, paths

    @classmethod
    def _bind_fake_s1_output(
        cls,
        guard: _FormalS1ExecutionProvenanceGuard,
        root: Path,
    ) -> dict[str, Path]:
        arguments, paths = cls._fake_s1_binding_args(root)
        guard.bind_s1_output(**arguments)
        return paths

    def test_formal_provenance_rejects_output_and_implementation_drift(
        self,
    ) -> None:
        admitted = self._case(GENERIC_CASE_MANIFEST)
        for target in ("output", "implementation"):
            with self.subTest(target=target), tempfile.TemporaryDirectory(
                prefix=f"formal-s1-{target}-drift-"
            ) as temporary:
                root = Path(temporary)
                guard = _FormalS1ExecutionProvenanceGuard(
                    directory=root / "markers",
                    execution_root=root,
                    validated_case=admitted,
                )
                with self.assertRaisesRegex(
                    AssertionError,
                    (
                        "E2E_PROVENANCE_S1_OUTPUT_DRIFT"
                        if target == "output"
                        else "E2E_PROVENANCE_DRIFT"
                    ),
                ):
                    with guard:
                        paths = self._bind_fake_s1_output(guard, root)
                        if target == "output":
                            _write_json(
                                paths["manifest"],
                                {"kind": "drifted"},
                            )
                        else:
                            original_capture = guard._capture

                            def drifted_capture() -> dict[str, Any]:
                                current = original_capture()
                                current["implementation"][0][
                                    "sha256"
                                ] = "0" * 64
                                return current

                            guard._capture = drifted_capture
                self.assertFalse(guard.end_path.exists())

    def test_formal_provenance_rejects_state_ref_and_projection_mismatch(
        self,
    ) -> None:
        admitted = self._case(GENERIC_CASE_MANIFEST)
        scenarios = {
            "state-path": (
                "E2E_PROVENANCE_REVISION2_STATE_REF_INVALID",
                lambda value: value["revision2_state_reference"].update(
                    {"path": "state/arbitrary.json"}
                ),
            ),
            "state-hash": (
                "E2E_PROVENANCE_REVISION2_STATE_REF_INVALID",
                lambda value: value["revision2_state_reference"].update(
                    {"sha256": "0" * 64}
                ),
            ),
            "projection-model": (
                "E2E_PROVENANCE_PROJECTION_MODEL_MISMATCH",
                lambda value: value["projection_evidence"].update(
                    {"model_sha256": "0" * 64}
                ),
            ),
            "missing-state-ref": (
                "E2E_PROVENANCE_REVISION2_STATE_REF_REQUIRED",
                lambda value: value.pop(
                    "revision2_state_reference"
                ),
            ),
        }
        for name, (error, mutate) in scenarios.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"formal-s1-{name}-"
            ) as temporary:
                root = Path(temporary)
                guard = _FormalS1ExecutionProvenanceGuard(
                    directory=root / "markers",
                    execution_root=root,
                    validated_case=admitted,
                )
                arguments, _ = self._fake_s1_binding_args(root)
                mutate(arguments)
                with self.assertRaisesRegex(AssertionError, error):
                    guard.bind_s1_output(**arguments)
                self.assertFalse(guard.end_path.exists())

    def test_formal_provenance_is_mandatory_without_environment_opt_in(
        self,
    ) -> None:
        admitted = self._case(GENERIC_CASE_MANIFEST)
        with tempfile.TemporaryDirectory(
            prefix="formal-s1-mandatory-provenance-"
        ) as temporary, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(E2E_PROVENANCE_ENV, None)
            root = Path(temporary)
            guard = _start_formal_s1_provenance_guard(
                admitted,
                execution_root=root,
            )
            self.assertEqual(
                (
                    root
                    / "evidence"
                    / "formal-s1-provenance"
                ).resolve(),
                guard.directory,
            )
            self.assertTrue(guard.start_path.is_file())
            with self.assertRaisesRegex(
                AssertionError,
                "E2E_PROVENANCE_S1_OUTPUT_NOT_BOUND",
            ):
                with guard:
                    pass
            self.assertFalse(guard.end_path.exists())


class FormalStorylineS1Probe(unittest.TestCase):
    """The Phase C1 formal proof stops after a real B0→S1 publication."""

    def test_real_manifest_case_reaches_s1(self) -> None:
        if os.environ.get("CONCEPTION_E2E_FIXTURE") is not None:
            raise AssertionError(
                "S1_EVAL_RAW_FIXTURE_CONFLICT: formal eval accepts only "
                "CONCEPTION_E2E_CASE_MANIFEST"
            )
        stop_after = os.environ.get("CONCEPTION_E2E_STOP_AFTER")
        if stop_after not in (None, "S1"):
            raise AssertionError(
                "S1_EVAL_STOP_AFTER_INVALID: Phase C1 stops at S1"
            )
        manifest = Path(
            os.environ.get(
                E2E_CASE_MANIFEST_ENV,
                str(GENERIC_CASE_MANIFEST),
            )
        )
        adapter = proposal_module.DeclarativeProposalAdapter.from_manifest(
            manifest
        )
        admitted = adapter.formal_case_snapshot
        fixture_path = admitted.structural_case.fixture_path
        external_root = os.environ.get("CONCEPTION_E2E_ROOT")
        if external_root:
            root = Path(external_root)
            root_context = contextlib.nullcontext()
        else:
            temporary_root = tempfile.TemporaryDirectory(
                prefix="conception-v2-formal-s1-"
            )
            root = Path(temporary_root.name)
            root_context = temporary_root
        provenance = _start_formal_s1_provenance_guard(
            admitted,
            execution_root=root,
        )
        with root_context, provenance:
            source = DeclarativeInterviewSource(
                root / "source", fixture_path
            )
            self.assertEqual(
                admitted.structural_case.fixture, source.fixture
            )
            self.assertTrue(adapter.is_formal)
            contract_runtime = rt.ContractRuntime()
            coordinator = rt.AutonomousCoordinator.initialize(
                run_id=source.run_id,
                source_interview_state={
                    "path": "interview/interview-state.json",
                    "sha256": rt.sha256_file(source.state),
                },
                state_path="state/revision-000.json",
            )
            packages = root / "packages"
            workspaces = root / "workspaces"
            b0_gate = coordinator.build_input_gate(
                "B0", "B0/input-gate.json"
            )
            b0 = packages / "B0"
            rt.build_baseline_package(
                **source.build_args(b0, b0_gate),
                runtime=contract_runtime,
            )
            rt.complete_b0(
                b0,
                coordinator=coordinator,
                input_gate=b0_gate,
                logical_package_path="B0",
                next_state_path="state/revision-001.json",
                runtime=contract_runtime,
            )
            baseline = _read_model(
                b0, "author-control-baseline.json"
            )
            preflight = adapter.preflight(baseline=baseline)
            self.assertEqual("ready", preflight["status"])
            self.assertEqual(
                admitted.structural_case.manifest["manifest_id"],
                preflight["manifest_id"],
            )

            s1_gate = coordinator.build_input_gate(
                "S1", "S1/input-gate.json"
            )
            s1_sources = [
                {
                    "path": f"sources/B0/{name}",
                    "sha256": rt.sha256_file(b0 / name),
                }
                for name in (
                    "author-control-baseline.json",
                    "package-manifest.json",
                    "stage-completion.json",
                )
            ]
            kwargs = {
                "run_id": source.run_id,
                "gate_reference": s1_gate.reference,
                "source_artifacts": s1_sources,
                "controls": s1._controls(b0, baseline),
            }
            s1_model = adapter.storyline(**kwargs)
            self.assertEqual(
                rt.canonical_sha256(s1_model),
                rt.canonical_sha256(adapter.storyline(**kwargs)),
            )
            s1_package = packages / "S1"
            s1_workspace = workspaces / "S1"
            common = {
                "baseline_package": b0,
                "input_gate": s1_gate,
                "runtime": contract_runtime,
            }
            with _thread("thread-formal-e2e-s1"):
                s1.start_s1_session(s1_workspace, **common)
                _submit_all(
                    s1,
                    s1.submit_s1_phase,
                    s1_workspace,
                    common,
                    s1_model,
                )
                s1.run_s1(
                    s1_package,
                    **common,
                    coordinator=coordinator,
                    controlled_workspace=s1_workspace,
                    logical_package_path="S1",
                    next_state_path="state/revision-002.json",
                )
            self.assertEqual(
                "ready",
                s1.validate_s1_package(
                    s1_package, runtime=contract_runtime
                )["verdict"],
            )
            self.assertEqual(2, coordinator.state["revision"])
            self.assertEqual(
                {"B0", "S1"},
                set(
                    coordinator.state[
                        "current_stage_completions"
                    ]
                ),
            )
            self.assertEqual(
                rt.canonical_sha256(s1_model),
                rt.canonical_sha256(
                    _read_model(
                        s1_package, "storyline-architecture.json"
                    )
                ),
            )
            provenance.bind_s1_output(
                projected_model=s1_model,
                package_model_path=(
                    s1_package / "storyline-architecture.json"
                ),
                package_manifest_path=(
                    s1_package / "package-manifest.json"
                ),
                completion_path=(
                    s1_package / "stage-completion.json"
                ),
                revision2_state=coordinator.state,
                projection_evidence=(
                    adapter.storyline_projection_evidence
                ),
                revision2_state_reference=(
                    coordinator.state_reference
                ),
            )
            _trace_stage("S1", s1_gate, s1_package)


class GenericRealChainProbe(unittest.TestCase):
    """Initial real-chain milestone; later TASK-016 scenarios extend this driver."""

    def test_real_public_entries_reach_p1(self) -> None:
        external_root = os.environ.get("CONCEPTION_E2E_ROOT")
        temporary_root = (
            None
            if external_root
            else tempfile.TemporaryDirectory(prefix="conception-v2-e2e-")
        )
        root = Path(
            external_root
            if external_root
            else typing.cast(Any, temporary_root).name
        )
        root_context = (
            contextlib.nullcontext(str(root))
            if external_root
            else typing.cast(Any, temporary_root)
        )
        stop_after = os.environ.get("CONCEPTION_E2E_STOP_AFTER")
        manifest_value = os.environ.get(E2E_CASE_MANIFEST_ENV)
        formal_case = None
        if manifest_value is not None:
            if (
                not manifest_value.strip()
                or os.environ.get("CONCEPTION_E2E_FIXTURE") is not None
            ):
                raise AssertionError(
                    "FORMAL_FULL_MANIFEST_ENTRY_INVALID"
                )
            manifest_path = Path(manifest_value).resolve()
            if manifest_path not in {
                GENERIC_CASE_MANIFEST.resolve(),
                DUANXIAN_CASE_MANIFEST.resolve(),
            }:
                raise AssertionError(
                    "FORMAL_FULL_MANIFEST_NOT_ADMITTED"
                )
            adapter = (
                proposal_module.DeclarativeProposalAdapter.from_manifest(
                    manifest_path
                )
            )
            formal_case = adapter.formal_case_snapshot
            fixture_path = formal_case.structural_case.fixture_path
            provenance_context = _FormalFullChainProvenanceGuard(
                execution_root=root,
                validated_case=formal_case,
            )
        else:
            fixture_path = Path(
                os.environ.get(
                    "CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE)
                )
            )
            adapter = None
            provenance_context = _start_execution_provenance_guard(
                fixture_path
            )
        with contextlib.ExitStack() as stack:
            if formal_case is not None:
                temporary = stack.enter_context(root_context)
                stack.enter_context(
                    provenance_context or contextlib.nullcontext()
                )
            else:
                stack.enter_context(
                    provenance_context or contextlib.nullcontext()
                )
                temporary = stack.enter_context(root_context)
            self.assertEqual(root, Path(temporary))
            source = DeclarativeInterviewSource(root / "source", fixture_path)
            if formal_case is not None:
                self.assertEqual(
                    formal_case.structural_case.fixture,
                    source.fixture,
                )
                self.assertTrue(typing.cast(Any, adapter).is_formal)
            else:
                adapter = proposal_module.DeclarativeProposalAdapter(
                    source.fixture
                )
            adapter = typing.cast(Any, adapter)
            contract_runtime = rt.ContractRuntime()
            coordinator = rt.AutonomousCoordinator.initialize(
                run_id=source.run_id,
                source_interview_state={
                    "path": "interview/interview-state.json",
                    "sha256": rt.sha256_file(source.state),
                },
                state_path="state/revision-000.json",
            )
            packages = root / "packages"
            workspaces = root / "workspaces"
            formal_guard = (
                provenance_context
                if isinstance(
                    provenance_context,
                    _FormalFullChainProvenanceGuard,
                )
                else None
            )
            if formal_guard is not None:
                formal_guard.bind_initial_state(coordinator)
            public_validators = {
                "B0": rt.validate_baseline_package,
                "S1": s1.validate_s1_package,
                "W1": w1.validate_w1_package,
                "E1": e1.validate_e1_package,
                "T1": t1.validate_t1_package,
                "C1": c1.validate_c1_package,
                "Q1": q1.validate_q1_package,
                "P1": p1.validate_p1_package,
            }

            def validate_public_stage(
                stage: str,
                package: Path,
            ) -> dict[str, Any]:
                validation = public_validators[stage](
                    package,
                    runtime=contract_runtime,
                )
                self.assertEqual("ready", validation["verdict"])
                expected = tuple(
                    item
                    for item in rt.STAGE_ORDER
                    if item
                    in coordinator.state["current_stage_completions"]
                )
                self.assertEqual(
                    tuple(public_validators)[: len(expected)],
                    expected,
                )
                self.assertEqual(
                    len(expected),
                    coordinator.state["revision"],
                )
                self.assertEqual(
                    rt.sha256_file(package / "stage-completion.json"),
                    coordinator.state[
                        "current_stage_completions"
                    ][stage]["sha256"],
                )
                if formal_guard is not None:
                    formal_guard.bind_stage(
                        stage,
                        package=package,
                        validation=validation,
                        coordinator=coordinator,
                    )
                return validation

            b0_gate = coordinator.build_input_gate("B0", "B0/input-gate.json")
            b0 = packages / "B0"
            rt.build_baseline_package(
                **source.build_args(b0, b0_gate),
                runtime=contract_runtime,
            )
            rt.complete_b0(
                b0,
                coordinator=coordinator,
                input_gate=b0_gate,
                logical_package_path="B0",
                next_state_path="state/revision-001.json",
                runtime=contract_runtime,
            )
            validate_public_stage("B0", b0)
            _trace_stage("B0", b0_gate, b0)
            baseline = _read_model(b0, "author-control-baseline.json")
            preflight = adapter.preflight(baseline=baseline)
            self.assertEqual("ready", preflight["status"])
            self.assertEqual(
                sorted(item["control_id"] for item in source.fixture["interviews"]),
                preflight["baseline_definition_ids"],
            )
            if stop_after == "B0":
                return

            s1_gate = coordinator.build_input_gate("S1", "S1/input-gate.json")
            s1_package, s1_workspace = packages / "S1", workspaces / "S1"
            s1_model = adapter.storyline(
                run_id=source.run_id,
                gate_reference=s1_gate.reference,
                source_artifacts=[
                    {
                        "path": f"sources/B0/{name}",
                        "sha256": rt.sha256_file(b0 / name),
                    }
                    for name in (
                        "author-control-baseline.json",
                        "package-manifest.json",
                        "stage-completion.json",
                    )
                ],
                controls=s1._controls(b0, baseline),
            )
            with _thread("thread-e2e-s1"):
                s1.start_s1_session(
                    s1_workspace,
                    baseline_package=b0,
                    input_gate=s1_gate,
                    runtime=contract_runtime,
                )
                _submit_all(
                    s1,
                    s1.submit_s1_phase,
                    s1_workspace,
                    {
                        "baseline_package": b0,
                        "input_gate": s1_gate,
                        "runtime": contract_runtime,
                    },
                    s1_model,
                )
                s1.run_s1(
                    s1_package,
                    baseline_package=b0,
                    coordinator=coordinator,
                    input_gate=s1_gate,
                    controlled_workspace=s1_workspace,
                    logical_package_path="S1",
                    next_state_path="state/revision-002.json",
                    runtime=contract_runtime,
                )
            validate_public_stage("S1", s1_package)
            _trace_stage("S1", s1_gate, s1_package)
            storyline = _read_model(s1_package, "storyline-architecture.json")
            if stop_after == "S1":
                return

            w1_gate = coordinator.build_input_gate("W1", "W1/input-gate.json")
            w1_package, w1_workspace = packages / "W1", workspaces / "W1"
            w1_model = adapter.world(
                run_id=source.run_id,
                gate_reference=w1_gate.reference,
                source_artifacts=w1._source_artifacts(b0, s1_package),
                baseline=baseline,
                storyline=storyline,
            )
            w1_common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "input_gate": w1_gate,
                "runtime": contract_runtime,
            }
            with _thread("thread-e2e-w1"):
                w1.start_w1_session(w1_workspace, **w1_common)
                _submit_all(
                    w1,
                    w1.submit_w1_phase,
                    w1_workspace,
                    w1_common,
                    w1_model,
                )
                w1.run_w1(
                    w1_package,
                    **w1_common,
                    coordinator=coordinator,
                    controlled_workspace=w1_workspace,
                    logical_package_path="W1",
                    next_state_path="state/revision-003.json",
                )
            validate_public_stage("W1", w1_package)
            _trace_stage("W1", w1_gate, w1_package)
            world = _read_model(w1_package, "world-model.json")
            if formal_guard is not None:
                line_ids = {
                    item["id"] for item in storyline["storylines"]
                }
                world_requirements = {
                    item["id"]: next(
                        source_id
                        for source_id in item["source_ids"]
                        if source_id in line_ids
                    )
                    for item in storyline["world_requirements"]
                }
                support_sources = [
                    record["source_ids"]
                    for record in world["storyline_support_ledger"]
                ]
                self.assertEqual(
                    [[item] for item in world_requirements],
                    support_sources,
                )
                self.assertEqual(
                    line_ids,
                    set(world_requirements.values()),
                )
            if stop_after == "W1":
                return

            e1_gate = coordinator.build_input_gate("E1", "E1/input-gate.json")
            e1_package, e1_workspace = packages / "E1", workspaces / "E1"
            e1_model = adapter.environment(
                run_id=source.run_id,
                gate_reference=e1_gate.reference,
                source_artifacts=e1._source_artifacts(
                    b0, s1_package, w1_package
                ),
                baseline=baseline,
                storyline=storyline,
                world=world,
            )
            e1_common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "input_gate": e1_gate,
                "runtime": contract_runtime,
            }
            with _thread("thread-e2e-e1"):
                e1.start_e1_session(e1_workspace, **e1_common)
                _submit_all(
                    e1,
                    e1.submit_e1_phase,
                    e1_workspace,
                    e1_common,
                    e1_model,
                )
                e1.run_e1(
                    e1_package,
                    **e1_common,
                    coordinator=coordinator,
                    controlled_workspace=e1_workspace,
                    logical_package_path="E1",
                    next_state_path="state/revision-004.json",
                )
            validate_public_stage("E1", e1_package)
            _trace_stage("E1", e1_gate, e1_package)
            environment = _read_model(
                e1_package, "environment-system.json"
            )
            if formal_guard is not None:
                environment_requirement_ids = {
                    item["id"]
                    for item in storyline[
                        "environment_requirements"
                    ]
                }
                world_environment_demands = {
                    item["id"]: item
                    for item in world["environment_demands"]
                }
                hosted_world_demand_ids = [
                    next(
                        source_id
                        for source_id in record["source_ids"]
                        if source_id in world_environment_demands
                    )
                    for record in environment[
                        "storyline_hosting_ledger"
                    ]
                ]
                self.assertEqual(
                    len(storyline["storylines"]),
                    len(environment["storyline_hosting_ledger"]),
                )
                self.assertEqual(
                    list(world_environment_demands),
                    hosted_world_demand_ids,
                )
                self.assertEqual(
                    line_ids,
                    {
                        world_requirements[
                            next(
                                source_id
                                for source_id in world_environment_demands[
                                    demand_id
                                ]["source_ids"]
                                if source_id in world_requirements
                            )
                        ]
                        for demand_id in hosted_world_demand_ids
                    },
                )
                self.assertEqual(
                    environment_requirement_ids,
                    {
                        next(
                            source_id
                            for source_id in record["source_ids"]
                            if source_id
                            in environment_requirement_ids
                        )
                        for record in environment[
                            "storyline_hosting_ledger"
                        ]
                    },
                )
                self.assertEqual(
                    {
                        item["id"]
                        for item in storyline["event_requirements"]
                    },
                    {
                        requirement_id
                        for affordance in environment[
                            "event_affordance_catalog"
                        ]
                        for requirement_id in affordance[
                            "event_requirement_ids"
                        ]
                    },
                )

            t1_gate = coordinator.build_input_gate("T1", "T1/input-gate.json")
            t1_package, t1_workspace = packages / "T1", workspaces / "T1"
            t1_model = adapter.event(
                run_id=source.run_id,
                gate_reference=t1_gate.reference,
                source_artifacts=t1._source_artifacts(
                    b0, s1_package, w1_package, e1_package
                ),
                baseline=baseline,
                storyline=storyline,
                world=world,
                environment=environment,
            )
            t1_common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "environment_package": e1_package,
                "input_gate": t1_gate,
                "runtime": contract_runtime,
            }
            with _thread("thread-e2e-t1"):
                t1.start_t1_session(t1_workspace, **t1_common)
                _submit_all(
                    t1,
                    t1.submit_t1_phase,
                    t1_workspace,
                    t1_common,
                    t1_model,
                )
                t1.run_t1(
                    t1_package,
                    **t1_common,
                    coordinator=coordinator,
                    controlled_workspace=t1_workspace,
                    logical_package_path="T1",
                    next_state_path="state/revision-005.json",
                )
            validate_public_stage("T1", t1_package)
            _trace_stage("T1", t1_gate, t1_package)
            timeline = _read_model(t1_package, "event-timeline.json")
            if formal_guard is not None:
                expected_t1 = (
                    (14, 12, 4)
                    if Path(manifest_value).resolve()
                    == GENERIC_CASE_MANIFEST.resolve()
                    else (18, 16, 5)
                )
                self.assertEqual(
                    expected_t1,
                    (
                        len(timeline["major_events"]),
                        len(timeline["causal_edges"]),
                        len(timeline["connection_realization"]),
                    ),
                )
                realization_by_connection = {
                    item["connection_id"]: item
                    for item in timeline["connection_realization"]
                }
                for connection in storyline["connections"]:
                    realization = realization_by_connection[
                        connection["id"]
                    ]
                    self.assertEqual(
                        connection["relation"],
                        realization["relation"],
                    )
                    if connection["relation"] == "associative":
                        self.assertEqual(
                            [],
                            realization["causal_edge_ids"],
                        )

            c1_gate = coordinator.build_input_gate("C1", "C1/input-gate.json")
            c1_package, c1_workspace = packages / "C1", workspaces / "C1"
            c1_model = adapter.character(
                run_id=source.run_id,
                gate_reference=c1_gate.reference,
                source_artifacts=c1._source_artifacts(
                    b0, s1_package, w1_package, e1_package, t1_package
                ),
                baseline=baseline,
                storyline=storyline,
                world=world,
                environment=environment,
                timeline=timeline,
            )
            adapter.assert_authority_partitions(
                [s1_model, w1_model, e1_model, t1_model, c1_model]
            )
            c1_common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "environment_package": e1_package,
                "event_package": t1_package,
                "input_gate": c1_gate,
                "runtime": contract_runtime,
            }
            with _thread("thread-e2e-c1"):
                c1.start_c1_session(c1_workspace, **c1_common)
                _submit_all(
                    c1,
                    c1.submit_c1_phase,
                    c1_workspace,
                    c1_common,
                    c1_model,
                )
                receipt = c1.run_c1(
                    c1_package,
                    **c1_common,
                    coordinator=coordinator,
                    controlled_workspace=c1_workspace,
                    logical_package_path="C1",
                    next_state_path="state/revision-006.json",
                )
            validate_public_stage("C1", c1_package)
            _trace_stage("C1", c1_gate, c1_package)
            if formal_guard is not None:
                character = _read_model(
                    c1_package,
                    "character-system.json",
                )
                main_line = next(
                    item
                    for item in storyline["storylines"]
                    if item["type"] == "main"
                )
                main_sequence = next(
                    item
                    for item in timeline[
                        "storyline_event_sequences"
                    ]
                    if item["storyline_id"] == main_line["id"]
                )
                first_main_event = next(
                    item
                    for item in timeline["major_events"]
                    if item["id"] == main_sequence["event_ids"][0]
                )
                slot_to_character = {
                    item["slot_id"]: item["character_id"]
                    for item in character["slot_resolution"]
                }
                self.assertEqual(
                    slot_to_character[
                        first_main_event["initiator_slot_id"]
                    ],
                    character["three_layer_networks"][0][
                        "core_character_id"
                    ],
                )

            q1_gate = coordinator.build_input_gate("Q1", "Q1/input-gate.json")
            q1_package = packages / "Q1"
            q1_controller = workspaces / "Q1-controller"
            q1_semantic = workspaces / "Q1-semantic"
            q1_handoff = workspaces / "Q1-handoff"
            q1_inputs = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "environment_package": e1_package,
                "event_package": t1_package,
                "character_package": c1_package,
            }
            controller_identity = ("task-e2e-q1-controller", "thread-e2e-q1-controller")
            semantic_identity = ("task-e2e-q1-semantic", "thread-e2e-q1-semantic")
            handoff_identity = ("task-e2e-q1-handoff", "thread-e2e-q1-handoff")
            with _identity(*controller_identity):
                frozen = q1.start_q1_controller(
                    q1_controller,
                    **q1_inputs,
                    input_gate=q1_gate,
                    runtime=contract_runtime,
                )
            if formal_guard is not None:
                formal_guard.bind_q1_controller_admission(
                    frozen=frozen,
                    frozen_path=(
                        q1_controller / "frozen-inputs.json"
                    ),
                    input_gate=q1_gate,
                    expected_controller_identity={
                        "task_id": controller_identity[0],
                        "thread_id": controller_identity[1],
                    },
                )
            q1_adapter = proposal_module.Q1ProposalAdapter(frozen)
            semantic_payloads = q1_adapter.semantic_payloads()
            with _identity(*semantic_identity):
                q1.start_semantic_review(
                    q1_controller,
                    q1_semantic,
                    **q1_inputs,
                    input_gate=q1_gate,
                    runtime=contract_runtime,
                )
                for phase in q1.SEMANTIC_PHASES:
                    q1.submit_semantic_phase(
                        q1_controller,
                        q1_semantic,
                        phase=phase,
                        payload=semantic_payloads[phase],
                        runtime=contract_runtime,
                    )
            with _identity(*handoff_identity):
                handoff_session = q1.start_handoff_review(
                    q1_controller,
                    q1_handoff,
                    **q1_inputs,
                )
                handoff_payload = q1_adapter.handoff_payload(
                    allowlist=handoff_session["allowlist"]
                )
                q1.seal_handoff_review(
                    q1_controller,
                    q1_handoff,
                    payload=handoff_payload,
                    runtime=contract_runtime,
                )
            with _identity(*semantic_identity):
                q1.import_sealed_handoff(
                    q1_controller,
                    q1_semantic,
                    q1_handoff,
                    runtime=contract_runtime,
                )
                handoff_evidence = rt.artifact_reference(
                    q1_semantic
                    / "sealed-handoff"
                    / "handoff-test-evidence.json",
                    root=q1_semantic,
                )
                final_review = q1_adapter.final_review(
                    run_id=source.run_id,
                    input_gate=q1_gate.reference,
                    semantic_payloads=semantic_payloads,
                    development_usability_test=handoff_payload[
                        "development_usability_test"
                    ],
                    handoff_evidence=handoff_evidence,
                    semantic_task_id=semantic_identity[0],
                    handoff_task_id=handoff_identity[0],
                    handoff_allowlist=handoff_session["allowlist"],
                )
                q1.submit_final_review(
                    q1_controller,
                    q1_semantic,
                    review=final_review,
                    runtime=contract_runtime,
                )
                q1.run_q1(
                    q1_package,
                    **q1_inputs,
                    coordinator=coordinator,
                    input_gate=q1_gate,
                    controller_workspace=q1_controller,
                    semantic_workspace=q1_semantic,
                    handoff_workspace=q1_handoff,
                    logical_package_path="Q1",
                    next_state_path="state/revision-007.json",
                    runtime=contract_runtime,
                )
            validate_public_stage("Q1", q1_package)
            _trace_stage("Q1", q1_gate, q1_package)
            review = _read_model(
                q1_package,
                "conception-review.json",
            )
            self.assertEqual([], review["findings"])

            p1_gate = coordinator.build_input_gate("P1", "P1/input-gate.json")
            p1_package = packages / "P1"
            p1.run_p1(
                p1_package,
                **q1_inputs,
                review_package=q1_package,
                coordinator=coordinator,
                input_gate=p1_gate,
                logical_package_path="P1",
                next_state_path="state/revision-008.json",
                runtime=contract_runtime,
            )
            validate_public_stage("P1", p1_package)
            _trace_stage("P1", p1_gate, p1_package)
            if formal_guard is not None:
                slc_index_ledger = _formal_p1_slc_index_ledger(
                    p1_package,
                    storyline=storyline,
                    timeline=timeline,
                )
                formal_guard.bind_p1_slc_index_ledger(
                    slc_index_ledger
                )

            self.assertEqual("ready", receipt.model["status"])
            self.assertEqual(8, coordinator.state["revision"])
            self.assertEqual(
                {"B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"},
                set(coordinator.state["current_stage_completions"]),
            )
            if formal_guard is not None:
                formal_guard.bind_final_state(coordinator)


class FormalManifestToP1Probe(unittest.TestCase):
    """Run one admitted manifest through the exact public B0-P1 chain."""

    def test_formal_manifest_reaches_p1(self) -> None:
        manifest = os.environ.get(
            E2E_CASE_MANIFEST_ENV,
            str(GENERIC_CASE_MANIFEST),
        )
        with mock.patch.dict(
            os.environ,
            {E2E_CASE_MANIFEST_ENV: manifest},
            clear=False,
        ):
            os.environ.pop("CONCEPTION_E2E_FIXTURE", None)
            os.environ.pop("CONCEPTION_E2E_STOP_AFTER", None)
            GenericRealChainProbe(
                "test_real_public_entries_reach_p1"
            ).test_real_public_entries_reach_p1()


class FormalManifestToP1ProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="formal-full-provenance-"
        )
        self.root = Path(self.temporary.name)
        self.case = storyline_quality_module.load_ready_eval_case(
            GENERIC_CASE_MANIFEST
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _guard(self, name: str) -> _FormalFullChainProvenanceGuard:
        return _FormalFullChainProvenanceGuard(
            execution_root=self.root / name,
            validated_case=self.case,
        )

    @staticmethod
    def _q1_admission_fixture(
        guard: _FormalFullChainProvenanceGuard,
    ) -> tuple[dict[str, Any], Path, Any, dict[str, str]]:
        stages = ("B0", "S1", "W1", "E1", "T1", "C1")
        completions = {}
        for stage in stages:
            package = guard.execution_root / "packages" / stage
            package.mkdir(parents=True, exist_ok=True)
            relative_paths = sorted(
                {
                    q1.STAGE_CANONICAL[stage],
                    "package-manifest.json",
                    "stage-completion.json",
                }
            )
            for relative in relative_paths:
                _write_json(
                    package / relative,
                    {
                        "run_id": guard.run_id,
                        "stage": stage,
                        "kind": relative,
                    },
                )
            completion = package / "stage-completion.json"
            reference = {
                "path": f"{stage}/stage-completion.json",
                "sha256": rt.sha256_file(completion),
                "stage": stage,
            }
            completions[stage] = reference
            artifacts = [
                guard._output_artifact(
                    f"{stage}:{relative}",
                    package / relative,
                )
                for relative in relative_paths
            ]
            guard._stage_bindings[stage] = {
                "artifacts": artifacts,
                "completion_reference": copy.deepcopy(reference),
            }
            guard._stage_roots[stage] = package
            guard._stage_paths[stage] = [
                package / relative for relative in relative_paths
            ]
        input_gate = type("_Q1AdmissionGate", (), {})()
        input_gate.reference = {
            "path": "Q1/input-gate.json",
            "sha256": "c" * 64,
        }
        input_gate.data = {
            "run_state": {
                "schema_version": "2.0",
                "run_id": guard.run_id,
                "revision": 6,
                "next_stage": "Q1",
            }
        }
        controller_identity = {
            "task_id": "task-e2e-q1-controller",
            "thread_id": "thread-e2e-q1-controller",
        }
        source_inventory = []
        for stage in sorted(stages):
            for artifact in guard._stage_bindings[stage]["artifacts"]:
                source_inventory.append(
                    {
                        "path": (
                            f"{stage}/"
                            f"{artifact['role'][len(stage) + 1:]}"
                        ),
                        "sha256": artifact["sha256"],
                    }
                )
        source_by_path = {
            item["path"]: item["sha256"]
            for item in source_inventory
        }
        handoff_source_inventory = sorted(
            [
                {
                    "path": f"{stage}/{relative}",
                    "sha256": source_by_path[
                        f"{stage}/{relative}"
                    ],
                }
                for stage in stages
                for relative in (
                    q1.STAGE_CANONICAL[stage],
                    "package-manifest.json",
                )
            ],
            key=lambda item: item["path"],
        )
        frozen = {
            "schema_version": "2.0",
            "run_id": guard.run_id,
            "stage": "Q1",
            "controller_identity": copy.deepcopy(
                controller_identity
            ),
            "input_gate": copy.deepcopy(input_gate.reference),
            "state_before": copy.deepcopy(
                input_gate.data["run_state"]
            ),
            "baseline_completion": copy.deepcopy(completions["B0"]),
            "upstream_completions": [
                copy.deepcopy(completions[stage])
                for stage in stages[1:]
            ],
            "generation_identities": [
                {
                    "task_id": f"task-e2e-{stage.lower()}",
                    "thread_id": f"thread-e2e-{stage.lower()}",
                }
                for stage in stages[1:]
            ],
            "package_roots": {
                stage: str(guard._stage_roots[stage])
                for stage in stages
            },
            "source_inventory": source_inventory,
            "handoff_source_inventory": handoff_source_inventory,
        }
        frozen_path = (
            guard.execution_root
            / "workspaces"
            / "Q1-controller"
            / "frozen-inputs.json"
        )
        _write_json(frozen_path, frozen)
        return (
            frozen,
            frozen_path,
            input_gate,
            controller_identity,
        )

    @staticmethod
    def _fake_complete(
        guard: _FormalFullChainProvenanceGuard,
    ) -> None:
        guard._stage_bindings = {
            stage: {"artifacts": []}
            for stage in guard._STAGES
        }
        guard._initial_state = {"bound": True}
        guard._final_state = {"bound": True}
        guard._q1_controller_admission = {
            "frozen_artifact": {"sha256": "0" * 64}
        }
        guard._q1_frozen_path = guard.execution_root / "frozen.json"
        guard._p1_slc_index_ledger = [{"connection_id": "SLC-X"}]

    def test_early_stop_has_start_and_forensic_but_no_end(self) -> None:
        guard = self._guard("early")
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_PROVENANCE_INCOMPLETE",
        ):
            with guard:
                pass
        self.assertTrue(guard.start_path.is_file())
        self.assertTrue(
            (guard.directory / "forensic-failure.json").is_file()
        )
        self.assertFalse(guard.end_path.exists())

    def test_q1_controller_admission_binds_frozen_evidence(self) -> None:
        guard = self._guard("q1-admission")
        (
            frozen,
            frozen_path,
            input_gate,
            controller_identity,
        ) = self._q1_admission_fixture(guard)
        guard.bind_q1_controller_admission(
            frozen=frozen,
            frozen_path=frozen_path,
            input_gate=input_gate,
            expected_controller_identity=controller_identity,
        )
        admission = guard._q1_controller_admission
        self.assertIsNotNone(admission)
        self.assertEqual(18, admission["source_inventory_count"])
        self.assertEqual(
            12, admission["handoff_source_inventory_count"]
        )
        self.assertEqual(
            ["B0", "S1", "W1", "E1", "T1", "C1"],
            [
                item["stage"]
                for item in admission["package_root_bindings"]
            ],
        )

    def test_q1_controller_admission_rejects_completion_drift(
        self,
    ) -> None:
        for name, mutation in (
            (
                "missing",
                lambda frozen: frozen["upstream_completions"].pop(),
            ),
            (
                "stale",
                lambda frozen: frozen["upstream_completions"][0].update(
                    {"sha256": "f" * 64}
                ),
            ),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-completion-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                mutation(frozen)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(
                    AssertionError,
                    "FORMAL_FULL_Q1_UPSTREAM_COMPLETIONS_INVALID",
                ):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_empty_inventories(
        self,
    ) -> None:
        for field in (
            "source_inventory",
            "handoff_source_inventory",
        ):
            with self.subTest(field=field):
                guard = self._guard(f"q1-empty-{field}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                frozen[field] = []
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(
                    AssertionError,
                    f"FORMAL_FULL_Q1_{field.upper()}_INVALID",
                ):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_forged_source_inventory(
        self,
    ) -> None:
        def remove_item(frozen: dict[str, Any]) -> None:
            frozen["source_inventory"].pop()

        def add_item(frozen: dict[str, Any]) -> None:
            frozen["source_inventory"].append(
                {
                    "path": "B0/unbound.json",
                    "sha256": "a" * 64,
                }
            )

        def reorder(frozen: dict[str, Any]) -> None:
            frozen["source_inventory"].reverse()

        def escape(frozen: dict[str, Any]) -> None:
            frozen["source_inventory"][0]["path"] = (
                "B0/../escape.json"
            )

        def wrong_sha(frozen: dict[str, Any]) -> None:
            frozen["source_inventory"][0]["sha256"] = "f" * 64

        for name, mutation in (
            ("missing", remove_item),
            ("additional", add_item),
            ("reorder", reorder),
            ("path-escape", escape),
            ("wrong-sha", wrong_sha),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-source-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                mutation(frozen)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(
                    AssertionError,
                    "FORMAL_FULL_Q1_SOURCE_INVENTORY_INVALID",
                ):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_forged_handoff_inventory(
        self,
    ) -> None:
        def remove_item(frozen: dict[str, Any]) -> None:
            frozen["handoff_source_inventory"].pop()

        def replace_member(frozen: dict[str, Any]) -> None:
            frozen["handoff_source_inventory"][0]["path"] = (
                "B0/stage-completion.json"
            )

        def reorder(frozen: dict[str, Any]) -> None:
            frozen["handoff_source_inventory"].reverse()

        def wrong_sha(frozen: dict[str, Any]) -> None:
            frozen["handoff_source_inventory"][0]["sha256"] = "f" * 64

        for name, mutation in (
            ("count", remove_item),
            ("member", replace_member),
            ("order", reorder),
            ("wrong-sha", wrong_sha),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-handoff-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                mutation(frozen)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(
                    AssertionError,
                    (
                        "FORMAL_FULL_Q1_"
                        "HANDOFF_SOURCE_INVENTORY_INVALID"
                    ),
                ):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_identity_forgery(
        self,
    ) -> None:
        for name, error, mutation in (
            (
                "wrong-controller",
                "FORMAL_FULL_Q1_CONTROLLER_IDENTITY_INVALID",
                lambda frozen: frozen["controller_identity"].update(
                    {"thread_id": "thread-forged-controller"}
                ),
            ),
            (
                "generation-overlap",
                "FORMAL_FULL_Q1_GENERATION_IDENTITIES_INVALID",
                lambda frozen: frozen["generation_identities"][0].update(
                    {
                        "task_id": frozen["controller_identity"][
                            "thread_id"
                        ]
                    }
                ),
            ),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-identity-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                mutation(frozen)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(AssertionError, error):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_top_level_and_gate_forgery(
        self,
    ) -> None:
        for name, mutation in (
            ("missing-key", lambda frozen: frozen.pop("state_before")),
            (
                "schema",
                lambda frozen: frozen.update(
                    {"schema_version": "1.0"}
                ),
            ),
            (
                "run-id",
                lambda frozen: frozen.update({"run_id": "forged-run"}),
            ),
            (
                "stage",
                lambda frozen: frozen.update({"stage": "P1"}),
            ),
            (
                "gate",
                lambda frozen: frozen["input_gate"].update(
                    {"sha256": "f" * 64}
                ),
            ),
            (
                "state",
                lambda frozen: frozen["state_before"].update(
                    {"revision": 5}
                ),
            ),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-top-level-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                mutation(frozen)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(
                    AssertionError,
                    "FORMAL_FULL_Q1_CONTROLLER_ADMISSION_INVALID",
                ):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_invalid_package_roots(
        self,
    ) -> None:
        for name, error, replacement in (
            (
                "outside",
                "FORMAL_FULL_Q1_PACKAGE_ROOT_OUTSIDE_EXECUTION",
                lambda guard: self.root / "outside-package",
            ),
            (
                "duplicate",
                "FORMAL_FULL_Q1_PACKAGE_ROOTS_NOT_DISTINCT",
                lambda guard: guard._stage_roots["B0"],
            ),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"q1-root-{name}")
                (
                    frozen,
                    frozen_path,
                    input_gate,
                    controller_identity,
                ) = self._q1_admission_fixture(guard)
                replacement_root = replacement(guard)
                replacement_root.mkdir(parents=True, exist_ok=True)
                frozen["package_roots"]["C1"] = str(replacement_root)
                _write_json(frozen_path, frozen)
                with self.assertRaisesRegex(AssertionError, error):
                    guard.bind_q1_controller_admission(
                        frozen=frozen,
                        frozen_path=frozen_path,
                        input_gate=input_gate,
                        expected_controller_identity=(
                            controller_identity
                        ),
                    )

    def test_q1_controller_admission_rejects_returned_disk_drift(
        self,
    ) -> None:
        guard = self._guard("q1-returned-disk-drift")
        (
            frozen,
            frozen_path,
            input_gate,
            controller_identity,
        ) = self._q1_admission_fixture(guard)
        _write_json(
            frozen_path,
            {**frozen, "controller_identity": {
                "task_id": "disk-forged",
                "thread_id": "disk-forged",
            }},
        )
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_Q1_FROZEN_ARTIFACT_INVALID",
        ):
            guard.bind_q1_controller_admission(
                frozen=frozen,
                frozen_path=frozen_path,
                input_gate=input_gate,
                expected_controller_identity=controller_identity,
            )

    def test_q1_controller_admission_requires_controller_return(
        self,
    ) -> None:
        guard = self._guard("q1-no-return")
        (
            _,
            frozen_path,
            input_gate,
            controller_identity,
        ) = self._q1_admission_fixture(guard)
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_Q1_CONTROLLER_ADMISSION_INVALID",
        ):
            guard.bind_q1_controller_admission(
                frozen=typing.cast(Any, None),
                frozen_path=frozen_path,
                input_gate=input_gate,
                expected_controller_identity=controller_identity,
            )

    def test_q1_frozen_file_drift_has_no_end(self) -> None:
        guard = self._guard("q1-frozen-drift")
        (
            frozen,
            frozen_path,
            input_gate,
            controller_identity,
        ) = self._q1_admission_fixture(guard)
        guard.bind_q1_controller_admission(
            frozen=frozen,
            frozen_path=frozen_path,
            input_gate=input_gate,
            expected_controller_identity=controller_identity,
        )
        for stage in ("Q1", "P1"):
            guard._stage_bindings[stage] = {"artifacts": []}
        guard._initial_state = {"bound": True}
        guard._final_state = {"bound": True}
        guard._p1_slc_index_ledger = [{"connection_id": "SLC-X"}]
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_Q1_FROZEN_ARTIFACT_DRIFT",
        ):
            with guard:
                _write_json(
                    frozen_path,
                    {**frozen, "run_id": "DRIFT"},
                )
        self.assertTrue(
            (guard.directory / "forensic-failure.json").is_file()
        )
        self.assertFalse(guard.end_path.exists())

    def test_input_implementation_drift_has_no_end(self) -> None:
        guard = self._guard("input-drift")
        self._fake_complete(guard)
        with (
            mock.patch.object(
                guard,
                "_capture_inputs",
                return_value={"drift": True},
            ),
            self.assertRaisesRegex(
                AssertionError,
                "FORMAL_FULL_INPUT_DRIFT",
            ),
        ):
            with guard:
                pass
        self.assertFalse(guard.end_path.exists())
        self.assertTrue(
            (guard.directory / "forensic-failure.json").is_file()
        )

    def test_output_drift_has_no_end(self) -> None:
        guard = self._guard("output-drift")
        self._fake_complete(guard)
        package = guard.execution_root / "packages" / "B0"
        output = package / "output.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("before", encoding="utf-8")
        guard._stage_roots["B0"] = package
        guard._stage_paths["B0"] = [output]
        guard._stage_bindings["B0"]["artifacts"] = [
            guard._output_artifact("B0:output.json", output)
        ]
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_OUTPUT_DRIFT",
        ):
            with guard:
                output.write_text("after", encoding="utf-8")
        self.assertFalse(guard.end_path.exists())
        self.assertTrue(
            (guard.directory / "forensic-failure.json").is_file()
        )

    def test_wrong_final_state_is_rejected(self) -> None:
        guard = self._guard("final-state")
        guard._stage_bindings = {
            stage: {"artifacts": []}
            for stage in guard._STAGES
        }
        invalid = type(
            "InvalidCoordinator",
            (),
            {
                "state": {
                    "revision": 7,
                    "current_stage_completions": {},
                },
                "state_reference": {
                    "path": "state/revision-007.json",
                    "sha256": "0" * 64,
                },
            },
        )()
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_FINAL_STATE_INVALID",
        ):
            guard.bind_final_state(invalid)
        self.assertFalse(guard.end_path.exists())

    def test_bind_stage_requires_initial_state_first(self) -> None:
        guard = self._guard("stage-without-initial")
        with self.assertRaisesRegex(
            AssertionError,
            "FORMAL_FULL_INITIAL_STATE_REQUIRED",
        ):
            guard.bind_stage(
                "B0",
                package=guard.execution_root / "packages" / "B0",
                validation={"verdict": "ready"},
                coordinator=object(),
            )
        self.assertEqual({}, guard._stage_bindings)
        self.assertFalse(guard.end_path.exists())

    def test_slc_ledger_missing_duplicate_or_wrong_is_rejected(
        self,
    ) -> None:
        valid = {
            "connection_id": "SLC-X",
            "definition": {
                "id": "SLC-X",
                "stage": "S1",
                "json_pointer": "/connections/0",
                "value_sha256": "a" * 64,
            },
            "reference": {
                "target_id": "SLC-X",
                "stage": "T1",
                "field": "connection_id",
                "json_pointer": (
                    "/connection_realization/0/connection_id"
                ),
            },
        }
        for name, ledger in (
            ("missing", []),
            ("duplicate", [valid, copy.deepcopy(valid)]),
            (
                "wrong-reference",
                [
                    {
                        **copy.deepcopy(valid),
                        "reference": {
                            **valid["reference"],
                            "json_pointer": "/wrong/0",
                        },
                    }
                ],
            ),
        ):
            with self.subTest(name=name):
                guard = self._guard(f"slc-{name}")
                with self.assertRaisesRegex(
                    AssertionError,
                    "FORMAL_FULL_P1_SLC_LEDGER_INVALID",
                ):
                    guard.bind_p1_slc_index_ledger(ledger)
                self.assertFalse(guard.end_path.exists())

    def test_p1_slc_ledger_reads_cross_model_index_exactly(self) -> None:
        package = self.root / "p1-index"
        package.mkdir()
        connection = {
            "id": "SLC-X",
            "from_storyline_id": "SL-A",
            "to_storyline_id": "SL-B",
        }
        definition = {
            "id": "SLC-X",
            "stage": "S1",
            "json_pointer": "/connections/0",
            "kind": "storyline-connection",
            "value_sha256": rt.canonical_sha256(connection),
        }
        occurrence = {
            key: definition[key]
            for key in (
                "stage",
                "json_pointer",
                "kind",
                "value_sha256",
            )
        }
        reference = {
            "target_id": "SLC-X",
            "stage": "T1",
            "field": "connection_id",
            "json_pointer": "/connection_realization/0/connection_id",
            "target_occurrences": [occurrence],
        }
        internal_reference = {
            "target_id": "SLC-X",
            "stage": "S1",
            "field": "connection_ids",
            "json_pointer": "/storylines/0/connection_ids/0",
            "target_occurrences": [occurrence],
        }
        _write_json(
            package / "authoritative-design-index.json",
            {"definitions": [], "references": []},
        )
        _write_json(
            package / "cross-model-index.json",
            {
                "definitions": [definition],
                "references": [internal_reference, reference],
            },
        )
        ledger = _formal_p1_slc_index_ledger(
            package,
            storyline={"connections": [connection]},
            timeline={
                "connection_realization": [
                    {"connection_id": "SLC-X"}
                ]
            },
        )
        self.assertEqual(
            [
                {
                    "connection_id": "SLC-X",
                    "definition": definition,
                    "reference": reference,
                }
            ],
            ledger,
        )
        _write_json(
            package / "cross-model-index.json",
            {
                "definitions": [definition],
                "references": [
                    internal_reference,
                    reference,
                    copy.deepcopy(reference),
                ],
            },
        )
        with self.assertRaisesRegex(
            AssertionError,
            "P1_SLC_REFERENCE_CARDINALITY_INVALID",
        ):
            _formal_p1_slc_index_ledger(
                package,
                storyline={"connections": [connection]},
                timeline={
                    "connection_realization": [
                        {"connection_id": "SLC-X"}
                    ]
                },
            )


def _restore_coordinator_from_prefix(
    *,
    source: DeclarativeInterviewSource,
    packages: Path,
    runtime: Any,
    stop_after: str | None = None,
) -> Any:
    """Replay sealed public completions to resume a checkpointed fresh run."""

    replay_order = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1")
    if stop_after is not None and stop_after not in replay_order:
        raise ValueError(f"unknown prefix stop stage: {stop_after}")
    coordinator = rt.AutonomousCoordinator.initialize(
        run_id=source.run_id,
        source_interview_state={
            "path": "interview/interview-state.json",
            "sha256": rt.sha256_file(source.state),
        },
        state_path="state/revision-000.json",
        runtime=runtime,
    )
    for revision, stage in enumerate(replay_order, 1):
        package = packages / stage
        completion_path = package / "stage-completion.json"
        if not completion_path.is_file():
            break
        gate = coordinator.build_input_gate(
            stage, f"{stage}/input-gate.json"
        )
        completion_data = json.loads(
            completion_path.read_text(encoding="utf-8")
        )
        if completion_data["input_gate"] != gate.reference:
            raise AssertionError(
                f"checkpoint gate mismatch at {stage}"
            )
        base_sealed = rt.seal_document(
            completion_data, f"{stage}/stage-completion.json"
        )
        sealed = rt.SealedDocument(
            data=base_sealed.data,
            reference={
                **base_sealed.reference,
                "stage": stage,
            },
        )
        if sealed.reference["sha256"] != rt.sha256_file(completion_path):
            raise AssertionError(
                f"checkpoint completion mismatch at {stage}"
            )
        coordinator.accept_stage_completion(
            gate=gate,
            completion=sealed,
            next_state_path=f"state/revision-{revision:03d}.json",
        )
        if stage == stop_after:
            break
    return coordinator


SYNTHETIC_RETURN_MARKER = "synthetic_test_injection"
RETURN_STATE_ENVELOPES = {
    7: "state-revision-007.envelope.json",
    8: "state-revision-008.envelope.json",
    11: "state-revision-011.envelope.json",
    12: "state-revision-012.envelope.json",
    # R4 seals the P1 transition at revision 13; R5 resumes from it
    # without advancing run-state while it writes deterministic evidence.
    13: "state-revision-013.envelope.json",
}
RETURN_CHECKPOINT_TESTS = (
    "test_return_00_q1_routes_to_w1",
    "test_return_01_resume_w1",
    "test_return_02_forward_e1_t1_c1",
    "test_return_03_q1_ready",
    "test_return_04_p1_ready",
    "test_return_05_finalize_and_deterministic",
)
RETURN_IMPLEMENTATION_EVIDENCE = "e2e-implementation.json"


def _return_e2e_implementation_evidence() -> dict[str, Any]:
    """Bind the test-only authoring surface omitted from stage packages.

    Stage packages already snapshot their production implementations.  The
    return E2E additionally uses this test driver and proposal authoring
    adapter, so R0 seals them at the root and R5 rechecks them.  The H1
    proposal adapter is intentionally outside this boundary: R0-R5 stop at P1
    and only derive an H1 input gate.
    """

    files = (
        ("return_e2e_driver", Path(__file__).resolve()),
        (
            "proposal_authoring_adapter",
            Path(proposal_module.__file__).resolve(),
        ),
    )
    artifacts = [
        {
            "role": role,
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": rt.sha256_file(path),
        }
        for role, path in sorted(files)
    ]
    return {
        "schema_version": "1.0",
        "scenario": "TASK-016D-return-resume",
        "boundary": "test-only E2E authoring surface outside stage packages",
        "artifacts": artifacts,
        "inventory_sha256": rt.canonical_sha256(artifacts),
    }


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": rt.sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _require_disjoint_paths(
    left: Path,
    right: Path,
    *,
    label: str,
) -> None:
    if _paths_overlap(left.resolve(), right.resolve()):
        raise AssertionError(
            f"{label} must be distinct non-ancestor roots: {left} vs {right}"
        )


def _return_e2e_roots(
    test: unittest.TestCase,
) -> tuple[Path, Path, Path, str]:
    input_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
    output_value = os.environ.get("CONCEPTION_E2E_RETURN_ROOT")
    execution_root_id = os.environ.get(
        "CONCEPTION_E2E_RETURN_RUN_ID", ""
    ).strip()
    if not input_value:
        test.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
    if not output_value:
        test.skipTest("CONCEPTION_E2E_RETURN_ROOT is not set")
    if not execution_root_id:
        test.skipTest("CONCEPTION_E2E_RETURN_RUN_ID is not set")
    input_root = Path(input_value).resolve()
    output_root = Path(output_value).resolve()
    fixture = Path(
        os.environ.get("CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE))
    ).resolve()
    _require_disjoint_paths(
        input_root, output_root, label="input/output roots"
    )
    protected_roots = {
        (input_root / "packages").resolve(),
        fixture.parent.resolve(),
        GENERIC_FIXTURE.parent.parent.resolve(),
        DUANXIAN_FIXTURE.parent.parent.resolve(),
    }
    for protected in protected_roots:
        _require_disjoint_paths(
            output_root,
            protected,
            label="output/protected fixture or input roots",
        )
    compare_value = os.environ.get("CONCEPTION_E2E_RETURN_COMPARE_ROOT")
    if compare_value:
        compare_root = Path(compare_value).resolve()
        for other, label in (
            (input_root, "compare/input roots"),
            (output_root, "compare/output roots"),
            (input_root / "packages", "compare/input package roots"),
            (fixture.parent, "compare/selected fixture roots"),
            (GENERIC_FIXTURE.parent.parent, "compare/generic fixture roots"),
            (DUANXIAN_FIXTURE.parent.parent, "compare/duanxian fixture roots"),
        ):
            _require_disjoint_paths(compare_root, other, label=label)
    input_packages = input_root / "packages"
    if not input_packages.is_dir():
        raise AssertionError(f"sealed generic packages are missing: {input_packages}")
    return input_root, output_root, fixture, execution_root_id


def _assert_fresh_return_root(output_root: Path) -> None:
    protected_targets = [
        output_root / "packages",
        output_root / "workspaces",
        output_root / "evidence",
        output_root / "source",
        *[
            _return_state_path(output_root, revision)
            for revision in RETURN_STATE_ENVELOPES
        ],
    ]
    residue = [str(path) for path in protected_targets if path.exists()]
    if residue:
        raise AssertionError(
            "return/resume output root contains prior-run residue: "
            + ", ".join(residue)
        )


def _read_return_root_identity(
    output_root: Path,
    expected_execution_root_id: str,
) -> dict[str, Any]:
    identity_path = output_root / "evidence" / "root-identity.json"
    if not identity_path.is_file():
        raise AssertionError(f"return root identity is missing: {identity_path}")
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    expected = {
        "schema_version": "1.0",
        "scenario": "TASK-016D-return-resume",
        "execution_root_id": expected_execution_root_id,
        "status": "started",
    }
    if identity != expected:
        raise AssertionError(
            f"return root identity mismatch: {identity!r} != {expected!r}"
        )
    return identity


def _return_state_path(output_root: Path, revision: int) -> Path:
    return output_root / "evidence" / RETURN_STATE_ENVELOPES[revision]


def _return_packages(input_root: Path, output_root: Path) -> dict[str, Path]:
    original = input_root / "packages"
    resumed = output_root / "packages"
    return {
        "B0": original / "B0",
        "S1": original / "S1",
        "W1": resumed / "W1",
        "E1": resumed / "E1",
        "T1": resumed / "T1",
        "C1": resumed / "C1",
        "Q1": resumed / "Q1",
        "P1": resumed / "P1",
    }


def _q1_inputs(packages: Mapping[str, Path]) -> dict[str, Path]:
    return {
        "baseline_package": packages["B0"],
        "storyline_package": packages["S1"],
        "world_package": packages["W1"],
        "environment_package": packages["E1"],
        "event_package": packages["T1"],
        "character_package": packages["C1"],
    }


def _select_synthetic_w1_owned_id(
    world: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    partition = world.get("authority_partition")
    expected_partition_keys = {
        "author_locked",
        "author_open",
        "autonomous_owned",
        "downstream_freedom",
    }
    if (
        not isinstance(partition, Mapping)
        or set(partition) != expected_partition_keys
    ):
        raise AssertionError("W1 authority partition is missing or malformed")
    partition_sets = {
        key: set(value)
        for key, value in partition.items()
        if isinstance(value, list)
    }
    if set(partition_sets) != expected_partition_keys:
        raise AssertionError("W1 authority partition members must be arrays")
    owned = partition_sets["autonomous_owned"]
    forbidden = (
        partition_sets["author_locked"]
        | partition_sets["author_open"]
        | partition_sets["downstream_freedom"]
    )
    if owned & forbidden:
        raise AssertionError("W1 authority partitions are not disjoint")

    decisions = [
        item
        for item in world.get("design_decisions", [])
        if isinstance(item, Mapping) and item.get("owner") == "W1"
    ]
    projected_by_owner: dict[str, set[str]] = {}
    impacted_by_owner: dict[str, set[str]] = {}
    for decision in decisions:
        decision_id = decision.get("id")
        if not isinstance(decision_id, str) or decision_id not in owned:
            raise AssertionError(
                "W1-owned design decision is absent from autonomous_owned"
            )
        projection_ids = decision.get("projection_ids", [])
        impact_ids = decision.get("impact_ids", [])
        if not isinstance(projection_ids, list):
            raise AssertionError("W1 decision projection_ids must be an array")
        if not isinstance(impact_ids, list):
            raise AssertionError("W1 decision impact_ids must be an array")
        for identifier in projection_ids:
            if isinstance(identifier, str):
                projected_by_owner.setdefault(identifier, set()).add(
                    decision_id
                )
        for identifier in impact_ids:
            if isinstance(identifier, str):
                impacted_by_owner.setdefault(identifier, set()).add(
                    decision_id
                )

    canonical_kinds: dict[str, str] = {}
    for collection, kind in (
        ("world_facts", "world_fact"),
        ("systems", "world_system"),
    ):
        values = world.get(collection)
        if not isinstance(values, list):
            raise AssertionError(f"W1 {collection} must be an array")
        for item in values:
            if not isinstance(item, Mapping) or not isinstance(
                item.get("id"), str
            ):
                raise AssertionError(f"W1 {collection} contains no object ID")
            canonical_kinds[item["id"]] = kind

    candidates: list[tuple[str, str, tuple[str, ...]]] = []
    for identifier in sorted(
        owned & set(canonical_kinds) & set(projected_by_owner)
    ):
        if identifier in forbidden:
            continue
        owner, resume_point = q1._owner_for_finding(
            {
                "id": "FND-TASK016D-W1-SELECTOR",
                "evidence_ids": [identifier],
                "affected_ids": [identifier],
            },
            author_ids=set(),
        )
        if owner == "W1" and resume_point == "W1":
            candidates.append(
                (
                    identifier,
                    canonical_kinds[identifier],
                    tuple(sorted(projected_by_owner[identifier])),
                )
            )
    if not candidates:
        raise AssertionError(
            "no routable canonical W1-owned object is projected by a W1 decision"
        )
    selected, canonical_kind, decision_ids = candidates[0]
    return selected, {
        "selected_id": selected,
        "partition": "autonomous_owned",
        "canonical_kind": canonical_kind,
        "projecting_w1_decision_ids": list(decision_ids),
        "impacting_w1_decision_ids": sorted(
            impacted_by_owner.get(selected, set())
        ),
        "q1_calculated_owner": "W1",
        "q1_minimum_rerun": "W1",
        "excluded_partitions": [
            "author_locked",
            "author_open",
            "downstream_freedom",
        ],
        "candidate_count": len(candidates),
    }


def _run_q1_public_checkpoint(
    *,
    package_root: Path,
    workspace_root: Path,
    logical_package_path: str,
    next_state_path: str,
    run_id: str,
    packages: Mapping[str, Path],
    coordinator: Any,
    input_gate: Any,
    runtime: Any,
    identity_prefix: str,
    synthetic_world_id: str | None = None,
) -> Any:
    inputs = _q1_inputs(packages)
    controller = workspace_root / "controller"
    semantic = workspace_root / "semantic"
    handoff = workspace_root / "handoff"
    controller_identity = (
        f"task-{identity_prefix}-controller",
        f"thread-{identity_prefix}-controller",
    )
    semantic_identity = (
        f"task-{identity_prefix}-semantic",
        f"thread-{identity_prefix}-semantic",
    )
    handoff_identity = (
        f"task-{identity_prefix}-handoff",
        f"thread-{identity_prefix}-handoff",
    )
    with _identity(*controller_identity):
        frozen = q1.start_q1_controller(
            controller,
            **inputs,
            input_gate=input_gate,
            runtime=runtime,
        )
    adapter = proposal_module.Q1ProposalAdapter(frozen)
    semantic_payloads = adapter.semantic_payloads()
    with _identity(*semantic_identity):
        q1.start_semantic_review(
            controller,
            semantic,
            **inputs,
            input_gate=input_gate,
            runtime=runtime,
        )
        for phase in q1.SEMANTIC_PHASES:
            q1.submit_semantic_phase(
                controller,
                semantic,
                phase=phase,
                payload=semantic_payloads[phase],
                runtime=runtime,
            )
    with _identity(*handoff_identity):
        handoff_session = q1.start_handoff_review(
            controller,
            handoff,
            **inputs,
        )
        handoff_payload = adapter.handoff_payload(
            allowlist=handoff_session["allowlist"]
        )
        q1.seal_handoff_review(
            controller,
            handoff,
            payload=handoff_payload,
            runtime=runtime,
        )
    with _identity(*semantic_identity):
        q1.import_sealed_handoff(
            controller,
            semantic,
            handoff,
            runtime=runtime,
        )
        handoff_evidence = rt.artifact_reference(
            semantic / "sealed-handoff" / "handoff-test-evidence.json",
            root=semantic,
        )
        review = adapter.final_review(
            run_id=run_id,
            input_gate=input_gate.reference,
            semantic_payloads=semantic_payloads,
            development_usability_test=handoff_payload[
                "development_usability_test"
            ],
            handoff_evidence=handoff_evidence,
            semantic_task_id=semantic_identity[0],
            handoff_task_id=handoff_identity[0],
            handoff_allowlist=handoff_session["allowlist"],
        )
        if synthetic_world_id is not None:
            finding_id = "FND-TASK016D-W1-RETURN"
            review["status"] = "revise"
            review["verdict"] = "revise"
            review["findings"] = [
                {
                    "id": finding_id,
                    "severity": "revise",
                    "problem": (
                        f"[{SYNTHETIC_RETURN_MARKER}] exercise the public "
                        "Q1-to-W1 return and resume contract"
                    ),
                    "evidence_ids": [synthetic_world_id],
                    "affected_ids": [synthetic_world_id],
                    "violated_contract": (
                        f"TASK-016D {SYNTHETIC_RETURN_MARKER} scenario"
                    ),
                    "calculated_owner": "W1",
                    "required_revision": (
                        f"[{SYNTHETIC_RETURN_MARKER}] regenerate W1 and its "
                        "invalidated suffix without asserting a real story defect"
                    ),
                    "minimum_rerun": "W1",
                }
            ]
            review["return_request"] = {"finding_id": finding_id}
        q1.submit_final_review(
            controller,
            semantic,
            review=review,
            runtime=runtime,
        )
        return q1.run_q1(
            package_root,
            **inputs,
            coordinator=coordinator,
            input_gate=input_gate,
            controller_workspace=controller,
            semantic_workspace=semantic,
            handoff_workspace=handoff,
            logical_package_path=logical_package_path,
            next_state_path=next_state_path,
            runtime=runtime,
        )


class ReturnSelectorContractTests(unittest.TestCase):
    @staticmethod
    def _minimal_world(*, projected: bool) -> dict[str, Any]:
        fact_id = "WF-SELECTOR-TEST"
        decision_id = "DEC-W1-SELECTOR-TEST"
        return {
            "authority_partition": {
                "author_locked": [],
                "author_open": [],
                "autonomous_owned": [decision_id, fact_id],
                "downstream_freedom": [],
            },
            "design_decisions": [
                {
                    "id": decision_id,
                    "owner": "W1",
                    "projection_ids": [fact_id] if projected else [],
                    "impact_ids": [fact_id],
                }
            ],
            "world_facts": [{"id": fact_id}],
            "systems": [],
        }

    def test_projection_qualifies_w1_owned_canonical_object(self) -> None:
        selected, evidence = _select_synthetic_w1_owned_id(
            self._minimal_world(projected=True)
        )
        self.assertEqual("WF-SELECTOR-TEST", selected)
        self.assertEqual(
            ["DEC-W1-SELECTOR-TEST"],
            evidence["projecting_w1_decision_ids"],
        )
        self.assertEqual(
            ["DEC-W1-SELECTOR-TEST"],
            evidence["impacting_w1_decision_ids"],
        )

    def test_impact_without_projection_cannot_qualify(self) -> None:
        with self.assertRaisesRegex(
            AssertionError,
            "no routable canonical W1-owned object",
        ):
            _select_synthetic_w1_owned_id(
                self._minimal_world(projected=False)
            )

    def test_existing_generic_checkpoint_still_qualifies(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        world = _read_model(
            Path(root_value) / "packages" / "W1",
            "world-model.json",
        )
        selected, evidence = _select_synthetic_w1_owned_id(world)
        self.assertIn(
            selected,
            world["authority_partition"]["autonomous_owned"],
        )
        self.assertNotIn(
            selected,
            (
                set(world["authority_partition"]["author_locked"])
                | set(world["authority_partition"]["author_open"])
                | set(world["authority_partition"]["downstream_freedom"])
            ),
        )
        self.assertTrue(evidence["projecting_w1_decision_ids"])
        self.assertEqual("W1", evidence["q1_calculated_owner"])
        self.assertEqual("W1", evidence["q1_minimum_rerun"])


def _h1_attempt_root(root: Path) -> Path:
    attempt = os.environ.get("CONCEPTION_H1_ATTEMPT", "H1")
    relative = Path(attempt)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("CONCEPTION_H1_ATTEMPT must stay within the run root")
    result = (root / relative).resolve()
    result.relative_to(root.resolve())
    return result


def _h1_plan_attempt_root(root: Path) -> Path:
    attempt = os.environ.get("CONCEPTION_H1_PLAN_ATTEMPT")
    if attempt is None:
        return _h1_attempt_root(root)
    relative = Path(attempt)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(
            "CONCEPTION_H1_PLAN_ATTEMPT must stay within the run root"
        )
    result = (root / relative).resolve()
    result.relative_to(root.resolve())
    return result


def _assert_expected_hash(
    testcase: unittest.TestCase,
    environment_name: str,
    actual: str,
) -> None:
    expected = os.environ.get(environment_name)
    if expected is not None:
        testcase.assertEqual(expected.casefold(), actual.casefold())


def _initialized_h1_workspace(
    *,
    root: Path,
    source: DeclarativeInterviewSource,
    coordinator: Any,
) -> Any:
    attempt_root = _h1_attempt_root(root)
    envelope = attempt_root / "workspace-initialized.envelope.json"
    if envelope.is_file():
        return _read_sealed_envelope(envelope)
    p1_reference = coordinator.state["current_stage_completions"]["P1"]
    session_seed = {
        "run_id": source.run_id,
        "p1_completion": p1_reference,
    }
    if attempt_root.name != "H1":
        session_seed["attempt"] = attempt_root.name
    session_id = "H1-SESSION-" + rt.canonical_sha256(session_seed)[:16]
    data = {
        "schema_version": "2.0",
        "run_id": source.run_id,
        "stage": "H1",
        "session_id": session_id,
        "state": "initialized",
        "p1_completion": p1_reference,
        "previous_state_sha256": None,
        "artifacts": {},
    }
    document = rt.seal_document(
        data, "H1/workspace-initialized.json"
    )
    _write_sealed_envelope(envelope, document)
    return document


def _assert_h1b_checkpoint(
    testcase: unittest.TestCase,
    session_root: Path,
    *,
    expected_completed: int,
) -> dict[str, Any]:
    """Independently audit a public H1-B resume checkpoint."""

    session_path = session_root / "generation-session.json"
    state_path = session_root / "session-state.json"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    session_reference = rt.artifact_reference(
        session_path, root=session_root
    )
    testcase.assertEqual(
        session_reference, state["session_reference"]
    )
    reconstructed = {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "h1_session_id": session["h1_session_id"],
        "session_id": session["session_id"],
        "status": "active",
        "next_phase_index": 1,
        "completed_evidence": [],
        "session_reference": session_reference,
        "previous_state_sha256": None,
        "forward_hash": rt.canonical_sha256(
            [session_reference, "H1-B-session-seed"]
        ),
    }
    testcase.assertEqual(
        expected_completed, len(state["completed_evidence"])
    )
    prior_reference = None
    for index, phase in enumerate(
        h1b.PHASES[:expected_completed], 1
    ):
        evidence_path = (
            session_root
            / "generation-evidence"
            / f"{index:02d}-{phase}.json"
        )
        reference = rt.artifact_reference(
            evidence_path, root=session_root
        )
        testcase.assertEqual(
            reference, state["completed_evidence"][index - 1]
        )
        evidence = json.loads(
            evidence_path.read_text(encoding="utf-8")
        )
        testcase.assertEqual(phase, evidence["phase"])
        testcase.assertEqual(index, evidence["phase_index"])
        testcase.assertEqual(
            rt.canonical_sha256(reconstructed),
            evidence["pre_state_sha256"],
        )
        testcase.assertEqual(
            prior_reference, evidence["previous_evidence"]
        )
        testcase.assertEqual(
            rt.canonical_sha256(evidence["payload"]),
            evidence["payload_sha256"],
        )
        prior = reconstructed
        completed = [
            *copy.deepcopy(prior["completed_evidence"]),
            reference,
        ]
        reconstructed = {
            "schema_version": "2.0",
            "run_id": prior["run_id"],
            "h1_session_id": prior["h1_session_id"],
            "session_id": prior["session_id"],
            "status": (
                "completed"
                if index == len(h1b.PHASES)
                else "active"
            ),
            "next_phase_index": index + 1,
            "completed_evidence": completed,
            "session_reference": prior["session_reference"],
            "previous_state_sha256": rt.canonical_sha256(prior),
            "forward_hash": rt.canonical_sha256(
                [prior["forward_hash"], reference, index]
            ),
        }
        prior_reference = reference
    testcase.assertEqual(reconstructed, state)
    testcase.assertEqual(expected_completed + 1, state["next_phase_index"])
    testcase.assertEqual(
        "completed"
        if expected_completed == len(h1b.PHASES)
        else "active",
        state["status"],
    )
    return state


class CheckpointedModelChainProbe(unittest.TestCase):
    """Resume E1/T1/C1 from a public B0-W1 sealed prefix."""

    def test_resume_e1_t1_c1_from_sealed_prefix(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        root = Path(root_value)
        fixture = Path(
            os.environ.get(
                "CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE)
            )
        )
        stop_after = os.environ.get("CONCEPTION_E2E_STOP_AFTER")
        runtime = rt.ContractRuntime()
        source = DeclarativeInterviewSource(root / "source", fixture)
        adapter = proposal_module.DeclarativeProposalAdapter(source.fixture)
        packages = root / "packages"
        workspaces = root / "checkpoint-workspaces"
        coordinator = _restore_coordinator_from_prefix(
            source=source, packages=packages, runtime=runtime
        )
        self.assertIn(coordinator.state["revision"], (3, 4, 5))
        b0 = packages / "B0"
        s1_package = packages / "S1"
        w1_package = packages / "W1"
        baseline = _read_model(b0, "author-control-baseline.json")
        storyline = _read_model(
            s1_package, "storyline-architecture.json"
        )
        world = _read_model(w1_package, "world-model.json")

        if coordinator.state["revision"] < 4:
            e1_gate = coordinator.build_input_gate(
                "E1", "E1/input-gate.json"
            )
            e1_package = packages / "E1"
            e1_workspace = workspaces / "E1"
            e1_model = adapter.environment(
                run_id=source.run_id,
                gate_reference=e1_gate.reference,
                source_artifacts=e1._source_artifacts(
                    b0, s1_package, w1_package
                ),
                baseline=baseline,
                storyline=storyline,
                world=world,
            )
            common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "input_gate": e1_gate,
                "runtime": runtime,
            }
            with _thread("thread-e2e-e1"):
                e1.start_e1_session(e1_workspace, **common)
                _submit_all(
                    e1,
                    e1.submit_e1_phase,
                    e1_workspace,
                    common,
                    e1_model,
                )
                e1.run_e1(
                    e1_package,
                    **common,
                    coordinator=coordinator,
                    controlled_workspace=e1_workspace,
                    logical_package_path="E1",
                    next_state_path="state/revision-004.json",
                )
            _trace_stage("E1", e1_gate, e1_package)
        if stop_after == "E1":
            return
        environment = _read_model(
            packages / "E1", "environment-system.json"
        )

        if coordinator.state["revision"] < 5:
            t1_gate = coordinator.build_input_gate(
                "T1", "T1/input-gate.json"
            )
            t1_package = packages / "T1"
            t1_workspace = workspaces / "T1"
            t1_model = adapter.event(
                run_id=source.run_id,
                gate_reference=t1_gate.reference,
                source_artifacts=t1._source_artifacts(
                    b0, s1_package, w1_package, packages / "E1"
                ),
                baseline=baseline,
                storyline=storyline,
                world=world,
                environment=environment,
            )
            common = {
                "baseline_package": b0,
                "storyline_package": s1_package,
                "world_package": w1_package,
                "environment_package": packages / "E1",
                "input_gate": t1_gate,
                "runtime": runtime,
            }
            with _thread("thread-e2e-t1"):
                t1.start_t1_session(t1_workspace, **common)
                _submit_all(
                    t1,
                    t1.submit_t1_phase,
                    t1_workspace,
                    common,
                    t1_model,
                )
                t1.run_t1(
                    t1_package,
                    **common,
                    coordinator=coordinator,
                    controlled_workspace=t1_workspace,
                    logical_package_path="T1",
                    next_state_path="state/revision-005.json",
                )
            _trace_stage("T1", t1_gate, t1_package)
        if stop_after == "T1":
            return
        timeline = _read_model(
            packages / "T1", "event-timeline.json"
        )

        c1_gate = coordinator.build_input_gate(
            "C1", "C1/input-gate.json"
        )
        c1_package = packages / "C1"
        c1_workspace = workspaces / "C1"
        c1_model = adapter.character(
            run_id=source.run_id,
            gate_reference=c1_gate.reference,
            source_artifacts=c1._source_artifacts(
                b0,
                s1_package,
                w1_package,
                packages / "E1",
                packages / "T1",
            ),
            baseline=baseline,
            storyline=storyline,
            world=world,
            environment=environment,
            timeline=timeline,
        )
        common = {
            "baseline_package": b0,
            "storyline_package": s1_package,
            "world_package": w1_package,
            "environment_package": packages / "E1",
            "event_package": packages / "T1",
            "input_gate": c1_gate,
            "runtime": runtime,
        }
        with _thread("thread-e2e-c1"):
            c1.start_c1_session(c1_workspace, **common)
            _submit_all(
                c1,
                c1.submit_c1_phase,
                c1_workspace,
                common,
                c1_model,
            )
            c1.run_c1(
                c1_package,
                **common,
                coordinator=coordinator,
                controlled_workspace=c1_workspace,
                logical_package_path="C1",
                next_state_path="state/revision-006.json",
            )
        _trace_stage("C1", c1_gate, c1_package)
        self.assertEqual(6, coordinator.state["revision"])


class CheckpointedPublicChainProbe(unittest.TestCase):
    """Resume Q1 from a public B0-C1 sealed prefix."""

    def test_resume_q1_from_sealed_prefix(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        root = Path(root_value)
        fixture = Path(
            os.environ.get(
                "CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE)
            )
        )
        runtime = rt.ContractRuntime()
        source = DeclarativeInterviewSource(root / "source", fixture)
        packages = root / "packages"
        workspaces = root / "resume-workspaces"
        coordinator = _restore_coordinator_from_prefix(
            source=source, packages=packages, runtime=runtime
        )
        self.assertEqual(6, coordinator.state["revision"])
        checkpoint_packages = {}
        for stage in ("B0", "S1", "W1", "E1", "T1", "C1"):
            package = packages / stage
            checkpoint_packages[stage] = {
                name: rt.sha256_file(package / name)
                for name in (
                    "stage-completion.json",
                    "package-manifest.json",
                    "validation.json",
                )
            }
        residue = [
            path.relative_to(packages).as_posix()
            for path in packages.rglob("*")
            if any(
                token in path.name.lower()
                for token in ("staging", ".tmp", "temporary")
            )
        ]
        self.assertEqual([], residue)
        checkpoint_evidence = {
            "status": "ready",
            "run_id": source.run_id,
            "fixture_sha256": rt.sha256_file(fixture),
            "fixture_schema_sha256": rt.sha256_file(FIXTURE_SCHEMA),
            "revision": coordinator.state["revision"],
            "state_sha256": coordinator.state_reference["sha256"],
            "packages": checkpoint_packages,
            "tree_inventory_sha256": rt.canonical_sha256(
                [
                    {
                        "path": path.relative_to(packages).as_posix(),
                        "sha256": rt.sha256_file(path),
                    }
                    for path in sorted(
                        item for item in packages.rglob("*") if item.is_file()
                    )
                ]
            ),
            "residue": residue,
        }
        _write_json(
            root / "evidence" / "checkpoint-C1.json",
            checkpoint_evidence,
        )
        q1_inputs = {
            "baseline_package": packages / "B0",
            "storyline_package": packages / "S1",
            "world_package": packages / "W1",
            "environment_package": packages / "E1",
            "event_package": packages / "T1",
            "character_package": packages / "C1",
        }
        q1_gate = coordinator.build_input_gate(
            "Q1", "Q1/input-gate.json"
        )
        q1_package = packages / "Q1"
        q1_controller = workspaces / "Q1-controller"
        q1_semantic = workspaces / "Q1-semantic"
        q1_handoff = workspaces / "Q1-handoff"
        controller_identity = (
            "task-e2e-q1-controller",
            "thread-e2e-q1-controller",
        )
        semantic_identity = (
            "task-e2e-q1-semantic",
            "thread-e2e-q1-semantic",
        )
        handoff_identity = (
            "task-e2e-q1-handoff",
            "thread-e2e-q1-handoff",
        )
        with _identity(*controller_identity):
            frozen = q1.start_q1_controller(
                q1_controller,
                **q1_inputs,
                input_gate=q1_gate,
                runtime=runtime,
            )
        adapter = proposal_module.Q1ProposalAdapter(frozen)
        semantic_payloads = adapter.semantic_payloads()
        with _identity(*semantic_identity):
            q1.start_semantic_review(
                q1_controller,
                q1_semantic,
                **q1_inputs,
                input_gate=q1_gate,
                runtime=runtime,
            )
            for phase in q1.SEMANTIC_PHASES:
                q1.submit_semantic_phase(
                    q1_controller,
                    q1_semantic,
                    phase=phase,
                    payload=semantic_payloads[phase],
                    runtime=runtime,
                )
        with _identity(*handoff_identity):
            handoff_session = q1.start_handoff_review(
                q1_controller, q1_handoff, **q1_inputs
            )
            handoff_payload = adapter.handoff_payload(
                allowlist=handoff_session["allowlist"]
            )
            q1.seal_handoff_review(
                q1_controller,
                q1_handoff,
                payload=handoff_payload,
                runtime=runtime,
            )
        with _identity(*semantic_identity):
            q1.import_sealed_handoff(
                q1_controller,
                q1_semantic,
                q1_handoff,
                runtime=runtime,
            )
            handoff_evidence = rt.artifact_reference(
                q1_semantic
                / "sealed-handoff"
                / "handoff-test-evidence.json",
                root=q1_semantic,
            )
            review = adapter.final_review(
                run_id=source.run_id,
                input_gate=q1_gate.reference,
                semantic_payloads=semantic_payloads,
                development_usability_test=handoff_payload[
                    "development_usability_test"
                ],
                handoff_evidence=handoff_evidence,
                semantic_task_id=semantic_identity[0],
                handoff_task_id=handoff_identity[0],
                handoff_allowlist=handoff_session["allowlist"],
            )
            q1.submit_final_review(
                q1_controller,
                q1_semantic,
                review=review,
                runtime=runtime,
            )
            q1.run_q1(
                q1_package,
                **q1_inputs,
                coordinator=coordinator,
                input_gate=q1_gate,
                controller_workspace=q1_controller,
                semantic_workspace=q1_semantic,
                handoff_workspace=q1_handoff,
                logical_package_path="Q1",
                next_state_path="state/revision-007.json",
                runtime=runtime,
            )
        _trace_stage("Q1", q1_gate, q1_package)


class CheckpointedP1Probe(unittest.TestCase):
    """Resume only P1 from a public B0-Q1 sealed prefix."""

    def test_resume_p1_from_sealed_prefix(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        root = Path(root_value)
        fixture = Path(
            os.environ.get(
                "CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE)
            )
        )
        runtime = rt.ContractRuntime()
        source = DeclarativeInterviewSource(root / "source", fixture)
        packages = root / "packages"
        coordinator = _restore_coordinator_from_prefix(
            source=source, packages=packages, runtime=runtime
        )
        self.assertEqual(7, coordinator.state["revision"])
        q1_inputs = {
            "baseline_package": packages / "B0",
            "storyline_package": packages / "S1",
            "world_package": packages / "W1",
            "environment_package": packages / "E1",
            "event_package": packages / "T1",
            "character_package": packages / "C1",
        }
        p1_gate = coordinator.build_input_gate(
            "P1", "P1/input-gate.json"
        )
        q1_package = packages / "Q1"
        p1_package = packages / "P1"
        p1.run_p1(
            p1_package,
            **q1_inputs,
            review_package=q1_package,
            coordinator=coordinator,
            input_gate=p1_gate,
            logical_package_path="P1",
            next_state_path="state/revision-008.json",
            runtime=runtime,
        )
        _trace_stage("P1", p1_gate, p1_package)
        self.assertEqual(8, coordinator.state["revision"])


class CheckpointedReturnResumeProbe(unittest.TestCase):
    """Exercise a synthetic Q1-to-W1 return through sealed checkpoints.

    R4 owns the only production P1 write and seals revision 13 immediately
    after that write succeeds. R5 is a fail-closed recovery step: it requires
    both sealed revision 13 and the immutable P1 package, validates P1 once,
    and writes only deterministic terminal evidence.
    """

    def _coordinator_from_envelope(
        self,
        *,
        output_root: Path,
        revision: int,
        runtime: Any,
        active_return_request: Any | None = None,
    ) -> Any:
        state = _read_sealed_envelope(
            _return_state_path(output_root, revision)
        )
        return rt.AutonomousCoordinator.from_snapshot(
            state.data,
            state.reference,
            active_return_request=active_return_request,
            runtime=runtime,
        )

    def test_return_00_q1_routes_to_w1(self) -> None:
        input_root, output_root, fixture, execution_root_id = (
            _return_e2e_roots(self)
        )
        _assert_fresh_return_root(output_root)
        q1_return_package = output_root / "packages" / "Q1-return"
        runtime = rt.ContractRuntime()
        source = DeclarativeInterviewSource(output_root / "source", fixture)
        _write_json(
            output_root / "evidence" / "root-identity.json",
            {
                "schema_version": "1.0",
                "scenario": "TASK-016D-return-resume",
                "execution_root_id": execution_root_id,
                "status": "started",
            },
        )
        _write_json(
            output_root / "evidence" / RETURN_IMPLEMENTATION_EVIDENCE,
            _return_e2e_implementation_evidence(),
        )
        coordinator = _restore_coordinator_from_prefix(
            source=source,
            packages=input_root / "packages",
            runtime=runtime,
            stop_after="C1",
        )
        self.assertEqual(6, coordinator.state["revision"])
        _assert_exact_current_stage_keys(
            self,
            coordinator.state,
            ("B0", "S1", "W1", "E1", "T1", "C1"),
        )
        packages = {
            stage: input_root / "packages" / stage
            for stage in ("B0", "S1", "W1", "E1", "T1", "C1")
        }
        world = _read_model(packages["W1"], "world-model.json")
        synthetic_world_id, selector_evidence = (
            _select_synthetic_w1_owned_id(world)
        )
        injection_evidence = {
            "schema_version": "1.0",
            "scenario": SYNTHETIC_RETURN_MARKER,
            "scope": "TASK-016D return/resume E2E only",
            "asserts_real_story_defect": False,
            "frozen_fixture_modified": False,
            "selected_w1_id": synthetic_world_id,
            "expected_owner": "W1",
            "expected_resume_stage": "W1",
            "selector_evidence": selector_evidence,
        }
        _write_json(
            output_root / "evidence" / "synthetic-test-injection.json",
            injection_evidence,
        )
        input_inventory = _tree_inventory(input_root / "packages")
        source_inventory = _tree_inventory(output_root / "source")
        _write_json(
            output_root / "evidence" / "input-package-inventory.json",
            {
                "fixture": {
                    "file_name": fixture.name,
                    "sha256": rt.sha256_file(fixture),
                    "run_id": source.run_id,
                },
                "source_inventory": source_inventory,
                "source_inventory_sha256": rt.canonical_sha256(
                    source_inventory
                ),
                "inventory": input_inventory,
                "inventory_sha256": rt.canonical_sha256(input_inventory),
            },
        )
        q1_gate = coordinator.build_input_gate(
            "Q1", "Q1-return/input-gate.json"
        )
        pre_return = copy.deepcopy(coordinator.state)
        receipt = _run_q1_public_checkpoint(
            package_root=q1_return_package,
            workspace_root=output_root / "workspaces" / "Q1-return",
            logical_package_path="Q1-return",
            next_state_path="state/return-revision-007.json",
            run_id=source.run_id,
            packages=packages,
            coordinator=coordinator,
            input_gate=q1_gate,
            runtime=runtime,
            identity_prefix="e2e-return-q1",
            synthetic_world_id=synthetic_world_id,
        )
        self.assertEqual("revise", receipt.verdict)
        self.assertIsNone(receipt.completion)
        validation = q1.validate_q1_package(
            q1_return_package,
            runtime=runtime,
        )
        self.assertEqual("revise", validation["verdict"])
        for required in (
            "return-request.json",
            "next-run-state.json",
            "blocked-report.md",
            "validation.json",
        ):
            self.assertTrue((q1_return_package / required).is_file(), required)
        for forbidden in ("package-manifest.json", "stage-completion.json"):
            self.assertFalse((q1_return_package / forbidden).exists(), forbidden)
        request_data = _read_model(
            q1_return_package, "return-request.json"
        )
        self.assertIn(SYNTHETIC_RETURN_MARKER, request_data["problem"])
        self.assertEqual("W1", request_data["calculated_owner"])
        self.assertEqual("W1", request_data["target_stage"])
        self.assertEqual("W1", request_data["resume_stage"])
        self.assertEqual("W1", request_data["resume_point"])
        self.assertEqual(
            ["W1", "E1", "T1", "C1", "Q1", "P1", "H1"],
            request_data["invalidated_stages"],
        )
        self.assertEqual(
            ["plan", "fragments", "assembly", "html", "completion"],
            request_data["invalidated_h1_artifacts"],
        )
        request = rt.seal_document(
            request_data, "Q1-return/return-request.json"
        )
        state = coordinator.state
        self.assertEqual(7, state["revision"])
        self.assertEqual("revise", state["status"])
        _assert_exact_current_stage_keys(
            self,
            state,
            ("B0", "S1"),
        )
        self.assertEqual(request.reference, state["active_return"])
        self.assertEqual([], state["resolved_returns"])
        self.assertEqual(
            [
                pre_return["current_stage_completions"][stage]
                for stage in ("W1", "E1", "T1", "C1")
            ],
            state["superseded_completions"],
        )
        before_replay = copy.deepcopy(state)
        replay = coordinator.apply_return_request(
            request=request,
            next_state_path=coordinator.state_reference["path"],
            conception_completion_current=False,
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(before_replay, coordinator.state)
        with self.assertRaises(rt.CoordinatorError) as missing_body:
            rt.AutonomousCoordinator.from_snapshot(
                coordinator.state,
                coordinator.state_reference,
                runtime=runtime,
            )
        self.assertEqual(
            "COORD_ACTIVE_RETURN_BODY_REQUIRED",
            missing_body.exception.code,
        )
        _write_sealed_envelope(
            _return_state_path(output_root, 7),
            rt.SealedDocument(
                data=coordinator.state,
                reference=coordinator.state_reference,
            ),
        )
        _write_sealed_envelope(
            output_root / "evidence" / "active-return.envelope.json",
            request,
        )

    def test_return_01_resume_w1(self) -> None:
        input_root, output_root, fixture, execution_root_id = (
            _return_e2e_roots(self)
        )
        _read_return_root_identity(output_root, execution_root_id)
        runtime = rt.ContractRuntime()
        request = _read_sealed_envelope(
            output_root / "evidence" / "active-return.envelope.json"
        )
        coordinator = self._coordinator_from_envelope(
            output_root=output_root,
            revision=7,
            runtime=runtime,
            active_return_request=request,
        )
        with self.assertRaises(rt.CoordinatorError) as blocked:
            coordinator.build_input_gate(
                "E1",
                "E1/blocked-input-gate.json",
                active_return_request=request,
            )
        self.assertEqual(
            "COORD_ACTIVE_RETURN_BLOCKS_STAGE", blocked.exception.code
        )
        gate = coordinator.build_input_gate(
            "W1",
            "W1/input-gate.json",
            active_return_request=request,
        )
        self.assertEqual("return_resolution", gate.data["entry_mode"])
        self.assertEqual(request.reference, gate.data["active_return"])
        packages = _return_packages(input_root, output_root)
        baseline = _read_model(
            packages["B0"], "author-control-baseline.json"
        )
        storyline = _read_model(
            packages["S1"], "storyline-architecture.json"
        )
        fixture_data = json.loads(fixture.read_text(encoding="utf-8"))
        adapter = proposal_module.DeclarativeProposalAdapter(fixture_data)
        proposal = adapter.world(
            run_id=coordinator.state["run_id"],
            gate_reference=gate.reference,
            source_artifacts=w1._source_artifacts(
                packages["B0"], packages["S1"]
            ),
            baseline=baseline,
            storyline=storyline,
        )
        common = {
            "baseline_package": packages["B0"],
            "storyline_package": packages["S1"],
            "input_gate": gate,
            "runtime": runtime,
        }
        workspace = output_root / "workspaces" / "W1"
        with _thread("thread-e2e-return-w1"):
            w1.start_w1_session(workspace, **common)
            _submit_all(
                w1,
                w1.submit_w1_phase,
                workspace,
                common,
                proposal,
            )
            receipt = w1.run_w1(
                packages["W1"],
                **common,
                coordinator=coordinator,
                controlled_workspace=workspace,
                logical_package_path="W1",
                next_state_path="state/return-revision-008.json",
                active_return_request=request,
            )
        self.assertEqual(
            "ready",
            w1.validate_w1_package(
                packages["W1"], runtime=runtime
            )["verdict"],
        )
        self.assertEqual(
            gate.data["return_binding"],
            receipt.completion.data["return_binding"],
        )
        state = coordinator.state
        self.assertEqual(8, state["revision"])
        self.assertEqual("running", state["status"])
        self.assertIsNone(state["active_return"])
        _assert_exact_current_stage_keys(
            self,
            state,
            ("B0", "S1", "W1"),
        )
        self.assertEqual(1, len(state["resolved_returns"]))
        resolution = state["resolved_returns"][0]
        self.assertEqual(
            gate.data["return_binding"], resolution["return_binding"]
        )
        self.assertEqual(
            receipt.completion.reference,
            resolution["resolving_completion"],
        )
        self.assertEqual(
            _read_sealed_envelope(
                _return_state_path(output_root, 7)
            ).reference,
            resolution["pre_resolution_state"],
        )
        before_repeat = copy.deepcopy(state)
        with self.assertRaises(rt.CoordinatorError) as repeated:
            coordinator.accept_stage_completion(
                gate=gate,
                completion=receipt.completion,
                next_state_path="state/return-revision-008.json",
                active_return_request=request,
            )
        self.assertEqual(
            "COORD_RETURN_ALREADY_RESOLVED", repeated.exception.code
        )
        self.assertEqual(before_repeat, coordinator.state)
        _write_sealed_envelope(
            _return_state_path(output_root, 8),
            rt.SealedDocument(
                data=coordinator.state,
                reference=coordinator.state_reference,
            ),
        )

    def test_return_02_forward_e1_t1_c1(self) -> None:
        input_root, output_root, fixture, execution_root_id = (
            _return_e2e_roots(self)
        )
        _read_return_root_identity(output_root, execution_root_id)
        runtime = rt.ContractRuntime()
        coordinator = self._coordinator_from_envelope(
            output_root=output_root,
            revision=8,
            runtime=runtime,
        )
        packages = _return_packages(input_root, output_root)
        baseline = _read_model(
            packages["B0"], "author-control-baseline.json"
        )
        storyline = _read_model(
            packages["S1"], "storyline-architecture.json"
        )
        world = _read_model(packages["W1"], "world-model.json")
        adapter = proposal_module.DeclarativeProposalAdapter(
            json.loads(fixture.read_text(encoding="utf-8"))
        )

        e1_gate = coordinator.build_input_gate("E1", "E1/input-gate.json")
        e1_proposal = adapter.environment(
            run_id=coordinator.state["run_id"],
            gate_reference=e1_gate.reference,
            source_artifacts=e1._source_artifacts(
                packages["B0"], packages["S1"], packages["W1"]
            ),
            baseline=baseline,
            storyline=storyline,
            world=world,
        )
        e1_common = {
            "baseline_package": packages["B0"],
            "storyline_package": packages["S1"],
            "world_package": packages["W1"],
            "input_gate": e1_gate,
            "runtime": runtime,
        }
        e1_workspace = output_root / "workspaces" / "E1"
        with _thread("thread-e2e-return-e1"):
            e1.start_e1_session(e1_workspace, **e1_common)
            _submit_all(
                e1,
                e1.submit_e1_phase,
                e1_workspace,
                e1_common,
                e1_proposal,
            )
            e1.run_e1(
                packages["E1"],
                **e1_common,
                coordinator=coordinator,
                controlled_workspace=e1_workspace,
                logical_package_path="E1",
                next_state_path="state/return-revision-009.json",
            )
        environment = _read_model(
            packages["E1"], "environment-system.json"
        )

        t1_gate = coordinator.build_input_gate("T1", "T1/input-gate.json")
        t1_proposal = adapter.event(
            run_id=coordinator.state["run_id"],
            gate_reference=t1_gate.reference,
            source_artifacts=t1._source_artifacts(
                packages["B0"],
                packages["S1"],
                packages["W1"],
                packages["E1"],
            ),
            baseline=baseline,
            storyline=storyline,
            world=world,
            environment=environment,
        )
        t1_common = {
            "baseline_package": packages["B0"],
            "storyline_package": packages["S1"],
            "world_package": packages["W1"],
            "environment_package": packages["E1"],
            "input_gate": t1_gate,
            "runtime": runtime,
        }
        t1_workspace = output_root / "workspaces" / "T1"
        with _thread("thread-e2e-return-t1"):
            t1.start_t1_session(t1_workspace, **t1_common)
            _submit_all(
                t1,
                t1.submit_t1_phase,
                t1_workspace,
                t1_common,
                t1_proposal,
            )
            t1.run_t1(
                packages["T1"],
                **t1_common,
                coordinator=coordinator,
                controlled_workspace=t1_workspace,
                logical_package_path="T1",
                next_state_path="state/return-revision-010.json",
            )
        timeline = _read_model(packages["T1"], "event-timeline.json")

        c1_gate = coordinator.build_input_gate("C1", "C1/input-gate.json")
        c1_proposal = adapter.character(
            run_id=coordinator.state["run_id"],
            gate_reference=c1_gate.reference,
            source_artifacts=c1._source_artifacts(
                packages["B0"],
                packages["S1"],
                packages["W1"],
                packages["E1"],
                packages["T1"],
            ),
            baseline=baseline,
            storyline=storyline,
            world=world,
            environment=environment,
            timeline=timeline,
        )
        c1_common = {
            "baseline_package": packages["B0"],
            "storyline_package": packages["S1"],
            "world_package": packages["W1"],
            "environment_package": packages["E1"],
            "event_package": packages["T1"],
            "input_gate": c1_gate,
            "runtime": runtime,
        }
        c1_workspace = output_root / "workspaces" / "C1"
        with _thread("thread-e2e-return-c1"):
            c1.start_c1_session(c1_workspace, **c1_common)
            _submit_all(
                c1,
                c1.submit_c1_phase,
                c1_workspace,
                c1_common,
                c1_proposal,
            )
            c1.run_c1(
                packages["C1"],
                **c1_common,
                coordinator=coordinator,
                controlled_workspace=c1_workspace,
                logical_package_path="C1",
                next_state_path="state/return-revision-011.json",
            )
        state = coordinator.state
        self.assertEqual(11, state["revision"])
        _assert_exact_current_stage_keys(
            self,
            state,
            ("B0", "S1", "W1", "E1", "T1", "C1"),
        )
        old_by_stage = {
            item["stage"]: item for item in state["superseded_completions"]
        }
        self.assertEqual(
            {"W1", "E1", "T1", "C1"}, set(old_by_stage)
        )
        for stage in ("W1", "E1", "T1", "C1"):
            self.assertNotEqual(
                old_by_stage[stage],
                state["current_stage_completions"][stage],
            )
            validator = {
                "W1": w1.validate_w1_package,
                "E1": e1.validate_e1_package,
                "T1": t1.validate_t1_package,
                "C1": c1.validate_c1_package,
            }[stage]
            self.assertEqual(
                "ready", validator(packages[stage], runtime=runtime)["verdict"]
            )
        _write_sealed_envelope(
            _return_state_path(output_root, 11),
            rt.SealedDocument(
                data=coordinator.state,
                reference=coordinator.state_reference,
            ),
        )

    def test_return_03_q1_ready(self) -> None:
        input_root, output_root, _, execution_root_id = (
            _return_e2e_roots(self)
        )
        _read_return_root_identity(output_root, execution_root_id)
        runtime = rt.ContractRuntime()
        coordinator = self._coordinator_from_envelope(
            output_root=output_root,
            revision=11,
            runtime=runtime,
        )
        packages = _return_packages(input_root, output_root)
        gate = coordinator.build_input_gate("Q1", "Q1/input-gate.json")
        receipt = _run_q1_public_checkpoint(
            package_root=packages["Q1"],
            workspace_root=output_root / "workspaces" / "Q1",
            logical_package_path="Q1",
            next_state_path="state/return-revision-012.json",
            run_id=coordinator.state["run_id"],
            packages=packages,
            coordinator=coordinator,
            input_gate=gate,
            runtime=runtime,
            identity_prefix="e2e-resumed-q1",
        )
        self.assertEqual("ready", receipt.verdict)
        self.assertIsNotNone(receipt.completion)
        self.assertEqual(
            "ready",
            q1.validate_q1_package(packages["Q1"], runtime=runtime)[
                "verdict"
            ],
        )
        self.assertEqual(12, coordinator.state["revision"])
        self.assertIsNone(coordinator.state["active_return"])
        self.assertEqual(1, len(coordinator.state["resolved_returns"]))
        _write_sealed_envelope(
            _return_state_path(output_root, 12),
            rt.SealedDocument(
                data=coordinator.state,
                reference=coordinator.state_reference,
            ),
        )

    def test_return_04_p1_ready(self) -> None:
        input_root, output_root, fixture, execution_root_id = (
            _return_e2e_roots(self)
        )
        _read_return_root_identity(output_root, execution_root_id)
        runtime = rt.ContractRuntime()
        coordinator = self._coordinator_from_envelope(
            output_root=output_root,
            revision=12,
            runtime=runtime,
        )
        packages = _return_packages(input_root, output_root)
        revision_13_path = _return_state_path(output_root, 13)
        self.assertFalse(
            revision_13_path.exists(),
            f"R4 requires revision 13 to be absent: {revision_13_path}",
        )
        p1_preexisted = packages["P1"].exists()
        gate = coordinator.build_input_gate("P1", "P1/input-gate.json")
        receipt = p1.run_p1(
            packages["P1"],
            **_q1_inputs(packages),
            review_package=packages["Q1"],
            coordinator=coordinator,
            input_gate=gate,
            logical_package_path="P1",
            next_state_path="state/return-revision-013.json",
            runtime=runtime,
        )
        self.assertEqual(p1_preexisted, receipt.replayed)
        state = coordinator.state
        self.assertEqual(13, state["revision"])
        self.assertEqual("running", state["status"])
        self.assertEqual("not_ready", state["development_status"])
        self.assertIsNone(state["active_return"])
        self.assertIsNone(state["author_decision"])
        self.assertEqual(1, len(state["resolved_returns"]))
        self.assertTrue((packages["P1"] / "package-manifest.json").is_file())
        self.assertTrue((packages["P1"] / "stage-completion.json").is_file())
        _write_sealed_envelope(
            _return_state_path(output_root, 13),
            rt.SealedDocument(
                data=coordinator.state,
                reference=coordinator.state_reference,
            ),
        )

    def test_return_05_finalize_and_deterministic(self) -> None:
        input_root, output_root, fixture, execution_root_id = (
            _return_e2e_roots(self)
        )
        _read_return_root_identity(output_root, execution_root_id)
        implementation_evidence_path = (
            output_root / "evidence" / RETURN_IMPLEMENTATION_EVIDENCE
        )
        self.assertTrue(
            implementation_evidence_path.is_file(),
            (
                "R5 requires sealed E2E implementation evidence: "
                f"{implementation_evidence_path}"
            ),
        )
        implementation_evidence = json.loads(
            implementation_evidence_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            _return_e2e_implementation_evidence(),
            implementation_evidence,
            "R0/R5 E2E implementation changed inside one execution root",
        )
        completion_marker_path = (
            output_root / "evidence" / "run-completed.json"
        )
        self.assertFalse(
            completion_marker_path.exists(),
            f"R5 completion marker must be absent: {completion_marker_path}",
        )
        revision_13_path = _return_state_path(output_root, 13)
        self.assertTrue(
            revision_13_path.is_file(),
            f"R5 requires sealed revision 13: {revision_13_path}",
        )
        packages = _return_packages(input_root, output_root)
        self.assertTrue(
            packages["P1"].is_dir(),
            f"R5 requires immutable P1 output: {packages['P1']}",
        )
        runtime = rt.ContractRuntime()
        coordinator = self._coordinator_from_envelope(
            output_root=output_root,
            revision=13,
            runtime=runtime,
        )
        self.assertEqual(
            "ready",
            p1.validate_p1_package(packages["P1"], runtime=runtime)[
                "verdict"
            ],
        )
        state = coordinator.state
        self.assertEqual(13, state["revision"])
        self.assertEqual("running", state["status"])
        self.assertEqual("not_ready", state["development_status"])
        self.assertIsNone(state["active_return"])
        self.assertIsNone(state["author_decision"])
        self.assertEqual(1, len(state["resolved_returns"]))
        _assert_exact_current_stage_keys(
            self,
            state,
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"),
        )
        self.assertEqual(
            state["current_stage_completions"]["P1"]["sha256"],
            rt.sha256_file(packages["P1"] / "stage-completion.json"),
        )
        self.assertEqual(
            ["W1", "E1", "T1", "C1"],
            [
                completion["stage"]
                for completion in state["superseded_completions"]
            ],
        )
        resolved_return = state["resolved_returns"][0]
        return_request = json.loads(
            (
                output_root
                / "packages"
                / "Q1-return"
                / "return-request.json"
            ).read_text(encoding="utf-8")
        )
        binding_keys = (
            "return_id",
            "return_kind",
            "calculated_owner",
            "resume_stage",
            "resume_point",
        )
        self.assertEqual(
            {key: return_request[key] for key in binding_keys},
            {
                key: resolved_return["return_binding"][key]
                for key in binding_keys
            },
        )
        h1_gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        self.assertEqual("forward", h1_gate.data["entry_mode"])
        self.assertIsNone(h1_gate.data["active_return"])
        input_evidence = json.loads(
            (
                output_root
                / "evidence"
                / "input-package-inventory.json"
            ).read_text(encoding="utf-8")
        )
        current_input_inventory = _tree_inventory(input_root / "packages")
        self.assertEqual(
            input_evidence["inventory"], current_input_inventory
        )
        self.assertEqual(
            input_evidence["inventory_sha256"],
            rt.canonical_sha256(current_input_inventory),
        )
        expected_fixture = {
            "file_name": fixture.name,
            "sha256": rt.sha256_file(fixture),
            "run_id": state["run_id"],
        }
        self.assertEqual(input_evidence["fixture"], expected_fixture)
        current_source_inventory = _tree_inventory(output_root / "source")
        self.assertEqual(
            input_evidence["source_inventory"],
            current_source_inventory,
        )
        self.assertEqual(
            input_evidence["source_inventory_sha256"],
            rt.canonical_sha256(current_source_inventory),
        )
        canonical_hashes: dict[str, str] = {}
        marker = SYNTHETIC_RETURN_MARKER.encode("utf-8")
        for stage in ("W1", "E1", "T1", "C1", "Q1", "P1"):
            manifest = _read_model(packages[stage], "package-manifest.json")
            role = "conception_package" if stage == "P1" else "canonical"
            canonical = manifest["artifact_roles"][role]
            canonical_path = packages[stage] / canonical["path"]
            self.assertTrue(canonical_path.is_file(), canonical_path)
            self.assertEqual(
                canonical["sha256"], rt.sha256_file(canonical_path)
            )
            self.assertNotIn(
                marker,
                canonical_path.read_bytes(),
                (
                    f"{SYNTHETIC_RETURN_MARKER} leaked into the ready "
                    f"{stage} authoritative output"
                ),
            )
            canonical_hashes[stage] = canonical["sha256"]
        summary = {
            "schema_version": "1.0",
            "scenario": "TASK-016D-return-resume",
            "synthetic_test_injection": True,
            "fixture_sha256": input_evidence["fixture"]["sha256"],
            "source_inventory_sha256": input_evidence[
                "source_inventory_sha256"
            ],
            "input_inventory_sha256": input_evidence[
                "inventory_sha256"
            ],
            "e2e_implementation": implementation_evidence,
            "return_request_sha256": rt.sha256_file(
                output_root / "packages" / "Q1-return" / "return-request.json"
            ),
            "state_sha256s": {
                str(revision): _read_sealed_envelope(
                    _return_state_path(output_root, revision)
                ).reference["sha256"]
                for revision in (7, 8, 11, 12, 13)
            },
            "stage_artifacts": {
                stage: {
                    "completion_sha256": rt.sha256_file(
                        packages[stage] / "stage-completion.json"
                    ),
                    "manifest_sha256": rt.sha256_file(
                        packages[stage] / "package-manifest.json"
                    ),
                }
                for stage in ("W1", "E1", "T1", "C1", "Q1", "P1")
            },
            "authoritative_output_sha256s": canonical_hashes,
            "resolved_return_count": len(state["resolved_returns"]),
            "final_revision": state["revision"],
            "h1_gate_sha256": h1_gate.reference["sha256"],
        }
        summary_path = output_root / "evidence" / "determinism-summary.json"
        _write_json(summary_path, summary)
        compare_value = os.environ.get("CONCEPTION_E2E_RETURN_COMPARE_ROOT")
        if compare_value:
            compare_root = Path(compare_value).resolve()
            compare_identity_path = (
                compare_root / "evidence" / "root-identity.json"
            )
            compare_completion_path = (
                compare_root / "evidence" / "run-completed.json"
            )
            compare_path = (
                compare_root / "evidence" / "determinism-summary.json"
            )
            compare_implementation_path = (
                compare_root
                / "evidence"
                / RETURN_IMPLEMENTATION_EVIDENCE
            )
            self.assertTrue(
                compare_identity_path.is_file(),
                f"comparison identity is missing: {compare_identity_path}",
            )
            compare_identity = json.loads(
                compare_identity_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                {
                    "schema_version": "1.0",
                    "scenario": "TASK-016D-return-resume",
                    "status": "started",
                },
                {
                    key: compare_identity.get(key)
                    for key in ("schema_version", "scenario", "status")
                },
            )
            compare_execution_root_id = compare_identity.get(
                "execution_root_id"
            )
            self.assertIsInstance(compare_execution_root_id, str)
            self.assertTrue(compare_execution_root_id)
            self.assertNotEqual(
                execution_root_id,
                compare_execution_root_id,
                "determinism comparison requires another execution root ID",
            )
            self.assertTrue(
                compare_completion_path.is_file(),
                (
                    "comparison completion marker is missing: "
                    f"{compare_completion_path}"
                ),
            )
            self.assertTrue(
                compare_implementation_path.is_file(),
                (
                    "comparison E2E implementation evidence is missing: "
                    f"{compare_implementation_path}"
                ),
            )
            self.assertEqual(
                implementation_evidence,
                json.loads(
                    compare_implementation_path.read_text(
                        encoding="utf-8"
                    )
                ),
                "determinism roots used different E2E authoring code",
            )
            compare_completion = json.loads(
                compare_completion_path.read_text(encoding="utf-8")
            )
            self.assertTrue(
                compare_path.is_file(),
                f"comparison summary is missing: {compare_path}",
            )
            self.assertEqual(
                {
                    "schema_version": "1.0",
                    "scenario": "TASK-016D-return-resume",
                    "execution_root_id": compare_execution_root_id,
                    "status": "completed",
                    "summary_sha256": rt.sha256_file(compare_path),
                    "final_state_sha256": summary["state_sha256s"]["13"],
                },
                compare_completion,
            )
            self.assertEqual(
                json.loads(compare_path.read_text(encoding="utf-8")),
                summary,
            )
        completion_marker = {
            "schema_version": "1.0",
            "scenario": "TASK-016D-return-resume",
            "execution_root_id": execution_root_id,
            "status": "completed",
            "summary_sha256": rt.sha256_file(summary_path),
            "final_state_sha256": coordinator.state_reference["sha256"],
        }
        _write_json_atomic(completion_marker_path, completion_marker)


class ReturnResumeCheckpointStaticContract(unittest.TestCase):
    """Keep the lightweight R4/R5 recovery boundary discoverable."""

    def test_return_implementation_evidence_covers_test_authoring_surface(
        self,
    ) -> None:
        evidence = _return_e2e_implementation_evidence()
        self.assertEqual(
            [
                "harnesses/novel-conception-autonomous/evals/"
                "proposal_adapter.py",
                "testing/test_conception_autonomous_v2_e2e.py",
            ],
            sorted(item["path"] for item in evidence["artifacts"]),
        )
        self.assertEqual(
            evidence["inventory_sha256"],
            rt.canonical_sha256(evidence["artifacts"]),
        )
        for item in evidence["artifacts"]:
            self.assertEqual(
                item["sha256"],
                rt.sha256_file(REPOSITORY_ROOT / item["path"]),
            )

    def test_stage_key_contract_ignores_json_object_order(self) -> None:
        expected = ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1")
        topology_order = {
            stage: {"stage": stage}
            for stage in expected
        }
        reverse_order = dict(reversed(list(topology_order.items())))
        states = [
            {"current_stage_completions": topology_order},
            {"current_stage_completions": reverse_order},
            json.loads(
                rt.canonical_json(
                    {"current_stage_completions": reverse_order}
                )
            ),
        ]
        for state in states:
            with self.subTest(keys=list(state["current_stage_completions"])):
                _assert_exact_current_stage_keys(self, state, expected)

    def test_stage_key_contract_rejects_missing_or_extra_stage(self) -> None:
        expected = ("B0", "S1", "W1")
        missing = {
            "current_stage_completions": {
                "B0": {"stage": "B0"},
                "S1": {"stage": "S1"},
            }
        }
        extra = {
            "current_stage_completions": {
                "B0": {"stage": "B0"},
                "S1": {"stage": "S1"},
                "W1": {"stage": "W1"},
                "E1": {"stage": "E1"},
            }
        }
        for state in (missing, extra):
            with self.subTest(keys=set(state["current_stage_completions"])):
                with self.assertRaises(AssertionError):
                    _assert_exact_current_stage_keys(self, state, expected)

    def test_return_checkpoint_discovery_and_state_contract(self) -> None:
        self.assertEqual(
            list(RETURN_CHECKPOINT_TESTS),
            unittest.defaultTestLoader.getTestCaseNames(
                CheckpointedReturnResumeProbe
            ),
        )
        self.assertEqual(
            [7, 8, 11, 12, 13],
            list(RETURN_STATE_ENVELOPES),
        )
        self.assertEqual(
            "state-revision-013.envelope.json",
            RETURN_STATE_ENVELOPES[13],
        )

        r4_names = set(
            CheckpointedReturnResumeProbe.test_return_04_p1_ready.__code__.co_names
        )
        r0_names = set(
            CheckpointedReturnResumeProbe
            .test_return_00_q1_routes_to_w1.__code__.co_names
        )
        r5_names = set(
            CheckpointedReturnResumeProbe
            .test_return_05_finalize_and_deterministic.__code__.co_names
        )
        self.assertIn("_return_e2e_implementation_evidence", r0_names)
        self.assertIn("run_p1", r4_names)
        self.assertIn("_write_sealed_envelope", r4_names)
        self.assertIn("replayed", r4_names)
        self.assertNotIn("validate_p1_package", r4_names)
        self.assertIn("validate_p1_package", r5_names)
        self.assertIn("_return_e2e_implementation_evidence", r5_names)
        self.assertIn("_write_json_atomic", r5_names)
        self.assertNotIn("run_p1", r5_names)

        r5_source = inspect.getsource(
            CheckpointedReturnResumeProbe
            .test_return_05_finalize_and_deterministic
        )
        compare_index = r5_source.index(
            'os.environ.get("CONCEPTION_E2E_RETURN_COMPARE_ROOT")'
        )
        marker_index = r5_source.rindex("_write_json_atomic")
        self.assertLess(compare_index, marker_index)
        self.assertEqual(
            "",
            r5_source[
                r5_source.index(
                    "\n", marker_index
                ) + 1:
            ].strip(),
            "the atomic completion marker must be the final R5 action",
        )

    def test_atomic_completion_marker_is_create_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence" / "run-completed.json"
            first = {"status": "completed", "value": 1}
            _write_json_atomic(path, first)
            self.assertEqual(
                rt.canonical_json(first),
                path.read_text(encoding="utf-8"),
            )
            with self.assertRaises(FileExistsError):
                _write_json_atomic(
                    path,
                    {"status": "completed", "value": 2},
                )
            self.assertEqual(
                rt.canonical_json(first),
                path.read_text(encoding="utf-8"),
            )

    def test_atomic_completion_marker_has_one_concurrent_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence" / "run-completed.json"
            barrier = threading.Barrier(2)
            original_link = os.link
            results: list[tuple[str, dict[str, Any]]] = []
            lock = threading.Lock()

            def synchronized_link(source, destination):
                barrier.wait(timeout=10)
                return original_link(source, destination)

            def publish(value):
                try:
                    _write_json_atomic(path, value)
                    result = ("winner", value)
                except FileExistsError:
                    result = ("exists", value)
                with lock:
                    results.append(result)

            values = [
                {"status": "completed", "writer": "A"},
                {"status": "completed", "writer": "B"},
            ]
            with mock.patch.object(
                os, "link", side_effect=synchronized_link
            ):
                threads = [
                    threading.Thread(target=publish, args=(value,))
                    for value in values
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=15)
                    self.assertFalse(thread.is_alive())

            winners = [value for status, value in results if status == "winner"]
            losers = [value for status, value in results if status == "exists"]
            self.assertEqual(1, len(winners))
            self.assertEqual(1, len(losers))
            winner_bytes = rt.canonical_json(winners[0])
            self.assertEqual(winner_bytes, path.read_text(encoding="utf-8"))
            self.assertEqual(
                [],
                list(path.parent.glob(".run-completed.json.*.candidate")),
            )

    def test_atomic_completion_marker_cleans_candidate_after_link_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence" / "run-completed.json"
            with mock.patch.object(
                os, "link", side_effect=OSError("injected link failure")
            ):
                with self.assertRaisesRegex(OSError, "injected link failure"):
                    _write_json_atomic(path, {"status": "completed"})
            self.assertFalse(path.exists())
            self.assertEqual(
                [],
                list(path.parent.glob(".run-completed.json.*.candidate")),
            )


class CheckpointedH1Probe(unittest.TestCase):
    """Run one real H1 internal step per process on a sealed P1 prefix."""

    def _context(self) -> tuple[Path, Any, Any, Any, Path]:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        root = Path(root_value)
        fixture = Path(
            os.environ.get(
                "CONCEPTION_E2E_FIXTURE", str(GENERIC_FIXTURE)
            )
        )
        runtime = rt.ContractRuntime()
        source = DeclarativeInterviewSource(root / "source", fixture)
        coordinator = _restore_coordinator_from_prefix(
            source=source,
            packages=root / "packages",
            runtime=runtime,
        )
        self.assertEqual(8, coordinator.state["revision"])
        return root, runtime, source, coordinator, root / "packages" / "P1"

    def test_h1_00_fresh_plan_binding_audit_only(self) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        root, _, _, coordinator, _ = self._context()
        h1_root = _h1_attempt_root(root)
        plan_root = _h1_plan_attempt_root(root)
        self.assertEqual(h1_root, plan_root)
        self.assertFalse(h1_root.exists())
        adapter_sha256 = rt.sha256_file(Path(adapter.__file__))
        _assert_expected_hash(
            self,
            "CONCEPTION_H1_EXPECTED_ADAPTER_SHA256",
            adapter_sha256,
        )
        gate = coordinator.build_input_gate(
            "H1", "H1/input-gate.json"
        )
        self.assertEqual("H1", gate.data["target_stage"])
        self.assertIn(
            coordinator.state["current_stage_completions"]["P1"],
            gate.data["upstream_completions"],
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-A-fresh-plan-binding-audit",
                    "attempt_root": h1_root.name,
                    "adapter_sha256": adapter_sha256,
                    "input_gate_sha256": gate.reference["sha256"],
                }
            ),
            flush=True,
        )

    def _waiting_context(self) -> tuple[Path, Any, Any, Any, Path]:
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        rendered = _read_sealed_envelope(
            h1_root / "workspace-rendered.envelope.json"
        )
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        completion_path = (
            root / "packages" / "H1" / "stage-completion.json"
        )
        data = json.loads(completion_path.read_text(encoding="utf-8"))
        base = rt.seal_document(
            data, "H1/stage/stage-completion.json"
        )
        completion = rt.SealedDocument(
            data=base.data,
            reference={**base.reference, "stage": "H1"},
        )
        self.assertEqual(
            rt.sha256_file(completion_path),
            completion.reference["sha256"],
        )
        coordinator.accept_stage_completion(
            gate=gate,
            completion=completion,
            next_state_path="state/revision-009.json",
            h1_workspace=rendered.reference,
        )
        self.assertEqual("waiting_author", coordinator.state["status"])
        return root, runtime, source, coordinator, p1_package

    def test_h1_01_plan(self) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _initialized_h1_workspace(
            root=root, source=source, coordinator=coordinator
        )
        plan_inputs = adapter.plan_inputs(
            p1_package,
            p1_completion=coordinator.state[
                "current_stage_completions"
            ]["P1"],
            input_gate=gate.reference,
            run_id=source.run_id,
            session_id=initialized.data["session_id"],
        )
        work_title, submissions = plan_inputs[0], list(plan_inputs[1:])
        self.assertEqual(list(h1a.PLAN_PHASES), [
            item["phase"] for item in submissions
        ])
        with _identity("task-e2e-h1-plan", "thread-e2e-h1-plan"):
            receipt = h1a.run_plan(
                h1_root / "plan",
                p1_package=p1_package,
                input_gate=gate,
                workspace_state=initialized,
                work_title=work_title,
                phase_submissions=submissions,
                coordinator=coordinator,
                logical_package_path="H1/plan",
                runtime=runtime,
            )
        _write_sealed_envelope(
            h1_root / "workspace-planned.envelope.json",
            receipt.transition.workspace,
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-A-plan",
                    "manifest_sha256": rt.sha256_file(
                        receipt.package_root / "package-manifest.json"
                    ),
                    "workspace_sha256": (
                        receipt.transition.workspace.reference["sha256"]
                    ),
                }
            ),
            flush=True,
        )

    def test_h1_02_fragments(self) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _initialized_h1_workspace(
            root=root, source=source, coordinator=coordinator
        )
        planned = _read_sealed_envelope(
            h1_root / "workspace-planned.envelope.json"
        )
        submissions = adapter.fragment_submissions(
            h1_root / "plan", p1_package=p1_package
        )
        session = h1_root / "fragment-session"
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            h1b.start_fragment_session(
                session,
                p1_package=p1_package,
                plan_package=h1_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
            for submission in submissions:
                h1b.submit_fragment_phase(
                    session,
                    submission,
                    p1_package=p1_package,
                    plan_package=h1_root / "plan",
                    plan_input_gate=gate,
                    plan_workspace_state=initialized,
                    workspace_state=planned,
                    runtime=runtime,
                )
            receipt = h1b.run(
                h1_root / "fragments",
                session_workspace=session,
                p1_package=p1_package,
                plan_package=h1_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                coordinator=coordinator,
                logical_package_path="H1/fragments",
                runtime=runtime,
            )
        _write_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json",
            receipt.transition.workspace,
        )

    def _fragment_step_context(
        self,
    ) -> tuple[
        Path,
        Any,
        Any,
        Any,
        Path,
        Path,
        Path,
        Any,
        Any,
        Any,
        tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    ]:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        plan_root = _h1_plan_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _read_sealed_envelope(
            plan_root / "workspace-initialized.envelope.json"
        )
        planned = _read_sealed_envelope(
            plan_root / "workspace-planned.envelope.json"
        )
        submissions = adapter.fragment_submissions(
            plan_root / "plan", p1_package=p1_package
        )
        return (
            root,
            runtime,
            source,
            coordinator,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            submissions,
        )

    def test_h1_02_reuse_contract_audit_only(self) -> None:
        (
            _,
            _,
            _,
            coordinator,
            _,
            h1_root,
            plan_root,
            _,
            initialized,
            planned,
            submissions,
        ) = self._fragment_step_context()
        self.assertNotEqual(h1_root, plan_root)
        self.assertFalse(h1_root.exists())
        self.assertEqual("initialized", initialized.data["state"])
        self.assertEqual("planned", planned.data["state"])
        self.assertEqual(
            initialized.reference["sha256"],
            planned.data["previous_state_sha256"],
        )
        self.assertEqual(
            coordinator.state["current_stage_completions"]["P1"],
            initialized.data["p1_completion"],
        )
        self.assertEqual(list(h1b.PHASES), [
            item["phase"] for item in submissions
        ])
        manifest_sha256 = rt.sha256_file(
            plan_root / "plan" / "package-manifest.json"
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_PLAN_MANIFEST_SHA256",
            manifest_sha256,
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-reuse-contract-audit",
                    "plan_manifest_sha256": manifest_sha256,
                    "initialized_sha256": initialized.reference["sha256"],
                    "planned_sha256": planned.reference["sha256"],
                    "output_root": h1_root.name,
                }
            ),
            flush=True,
        )

    def test_h1_02s0_fragment_start(self) -> None:
        (
            _,
            runtime,
            _,
            _,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            _,
        ) = self._fragment_step_context()
        session = h1_root / "fragment-session"
        self.assertFalse(session.exists())
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            h1b.start_fragment_session(
                session,
                p1_package=p1_package,
                plan_package=plan_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
        state = _assert_h1b_checkpoint(
            self, session, expected_completed=0
        )
        session_sha256 = rt.sha256_file(
            session / "generation-session.json"
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_SESSION_SHA256",
            session_sha256,
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-start",
                    "generation_session_sha256": session_sha256,
                    "forward_hash": state["forward_hash"],
                    "next_phase_index": state["next_phase_index"],
                }
            ),
            flush=True,
        )

    def test_h1_02s1_fragment_phase1(self) -> None:
        (
            _,
            runtime,
            _,
            _,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            submissions,
        ) = self._fragment_step_context()
        session = h1_root / "fragment-session"
        _assert_h1b_checkpoint(self, session, expected_completed=0)
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            evidence = h1b.submit_fragment_phase(
                session,
                submissions[0],
                p1_package=p1_package,
                plan_package=plan_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
        state = _assert_h1b_checkpoint(
            self, session, expected_completed=1
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_PHASE1_SHA256",
            evidence["sha256"],
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-phase1",
                    "evidence": evidence,
                    "forward_hash": state["forward_hash"],
                    "next_phase_index": state["next_phase_index"],
                }
            ),
            flush=True,
        )

    def test_h1_02_checkpoint_audit_only(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        completed_value = os.environ.get(
            "CONCEPTION_H1B_EXPECTED_COMPLETED"
        )
        if not root_value or completed_value is None:
            self.skipTest("H1-B checkpoint audit inputs are not set")
        session = (
            _h1_attempt_root(Path(root_value)) / "fragment-session"
        )
        state = _assert_h1b_checkpoint(
            self,
            session,
            expected_completed=int(completed_value),
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-checkpoint-audit",
                    "completed": len(state["completed_evidence"]),
                    "next_phase_index": state["next_phase_index"],
                    "forward_hash": state["forward_hash"],
                }
            ),
            flush=True,
        )

    def test_h1_02s2_fragment_phase2(self) -> None:
        (
            _,
            runtime,
            _,
            _,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            submissions,
        ) = self._fragment_step_context()
        session = h1_root / "fragment-session"
        _assert_h1b_checkpoint(self, session, expected_completed=1)
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            evidence = h1b.submit_fragment_phase(
                session,
                submissions[1],
                p1_package=p1_package,
                plan_package=plan_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
        state = _assert_h1b_checkpoint(
            self, session, expected_completed=2
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_PHASE2_SHA256",
            evidence["sha256"],
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-phase2",
                    "evidence": evidence,
                    "forward_hash": state["forward_hash"],
                    "next_phase_index": state["next_phase_index"],
                }
            ),
            flush=True,
        )

    def test_h1_02s3_fragment_phase3(self) -> None:
        (
            _,
            runtime,
            _,
            _,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            submissions,
        ) = self._fragment_step_context()
        session = h1_root / "fragment-session"
        _assert_h1b_checkpoint(self, session, expected_completed=2)
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            evidence = h1b.submit_fragment_phase(
                session,
                submissions[2],
                p1_package=p1_package,
                plan_package=plan_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                runtime=runtime,
            )
        state = _assert_h1b_checkpoint(
            self, session, expected_completed=3
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_PHASE3_SHA256",
            evidence["sha256"],
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-phase3",
                    "evidence": evidence,
                    "forward_hash": state["forward_hash"],
                    "next_phase_index": state["next_phase_index"],
                }
            ),
            flush=True,
        )

    def test_h1_02s4_fragment_finalize(self) -> None:
        (
            _,
            runtime,
            _,
            coordinator,
            p1_package,
            h1_root,
            plan_root,
            gate,
            initialized,
            planned,
            _,
        ) = self._fragment_step_context()
        session = h1_root / "fragment-session"
        _assert_h1b_checkpoint(self, session, expected_completed=3)
        with _identity(
            "task-e2e-h1-fragments", "thread-e2e-h1-fragments"
        ):
            receipt = h1b.finalize_fragment_package(
                h1_root / "fragments",
                session_workspace=session,
                p1_package=p1_package,
                plan_package=plan_root / "plan",
                plan_input_gate=gate,
                plan_workspace_state=initialized,
                workspace_state=planned,
                coordinator=coordinator,
                logical_package_path="H1/fragments",
                runtime=runtime,
            )
        _write_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json",
            receipt.transition.workspace,
        )
        manifest_sha256 = rt.sha256_file(
            receipt.package_root / "package-manifest.json"
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1B_EXPECTED_MANIFEST_SHA256",
            manifest_sha256,
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-B-finalize",
                    "manifest_sha256": manifest_sha256,
                    "workspace_sha256": (
                        receipt.transition.workspace.reference["sha256"]
                    ),
                }
            ),
            flush=True,
        )

    def test_h1_03_assembly(self) -> None:
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        plan_root = _h1_plan_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _read_sealed_envelope(
            plan_root / "workspace-initialized.envelope.json"
        )
        planned = _read_sealed_envelope(
            plan_root / "workspace-planned.envelope.json"
        )
        fragments_ready = _read_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json"
        )
        self.assertFalse((h1_root / "assembly").exists())
        self.assertFalse(
            (h1_root / "workspace-assembled.envelope.json").exists()
        )
        p1_completion = {
            "path": initialized.data["p1_completion"]["path"],
            "sha256": initialized.data["p1_completion"]["sha256"],
        }
        fidelity_review = _test_fidelity_review(
            p1_completion=p1_completion,
            plan_root=plan_root / "plan",
            fragment_root=h1_root / "fragments",
            runtime=runtime,
        )
        receipt = h1a.run_assemble(
            h1_root / "assembly",
            p1_package=p1_package,
            plan_package=plan_root / "plan",
            plan_input_gate=gate,
            plan_workspace_state=initialized,
            fragment_package=h1_root / "fragments",
            fragment_workspace_state=planned,
            workspace_state=fragments_ready,
            coordinator=coordinator,
            logical_package_path="H1/assembly",
            fidelity_review=fidelity_review,
            runtime=runtime,
        )
        _write_sealed_envelope(
            h1_root / "workspace-assembled.envelope.json",
            receipt.transition.workspace,
        )
        manifest_sha256 = rt.sha256_file(
            receipt.package_root / "package-manifest.json"
        )
        _assert_expected_hash(
            self,
            "CONCEPTION_H1A_EXPECTED_ASSEMBLY_MANIFEST_SHA256",
            manifest_sha256,
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-A-assembly",
                    "manifest_sha256": manifest_sha256,
                    "workspace_sha256": (
                        receipt.transition.workspace.reference["sha256"]
                    ),
                }
            ),
            flush=True,
        )

    def test_h1_03_binding_audit_only(self) -> None:
        root, _, _, coordinator, _ = self._context()
        h1_root = _h1_attempt_root(root)
        plan_root = _h1_plan_attempt_root(root)
        self.assertNotEqual(h1_root, plan_root)
        initialized = _read_sealed_envelope(
            plan_root / "workspace-initialized.envelope.json"
        )
        planned = _read_sealed_envelope(
            plan_root / "workspace-planned.envelope.json"
        )
        fragments_ready = _read_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json"
        )
        self.assertEqual("initialized", initialized.data["state"])
        self.assertEqual("planned", planned.data["state"])
        self.assertEqual("fragments_ready", fragments_ready.data["state"])
        self.assertEqual(
            initialized.reference["sha256"],
            planned.data["previous_state_sha256"],
        )
        self.assertEqual(
            planned.reference["sha256"],
            fragments_ready.data["previous_state_sha256"],
        )
        self.assertEqual(
            coordinator.state["current_stage_completions"]["P1"],
            initialized.data["p1_completion"],
        )
        self.assertEqual(
            rt.sha256_file(plan_root / "plan" / "package-manifest.json"),
            fragments_ready.data["artifacts"]["plan_manifest"]["sha256"],
        )
        self.assertEqual(
            rt.sha256_file(h1_root / "fragments" / "package-manifest.json"),
            fragments_ready.data["artifacts"]["fragment_manifest"]["sha256"],
        )
        self.assertFalse((h1_root / "assembly").exists())
        self.assertFalse(
            (h1_root / "workspace-assembled.envelope.json").exists()
        )
        print(
            rt.canonical_json(
                {
                    "stage": "H1-A-assembly-binding-audit",
                    "plan_root": plan_root.name,
                    "fragment_root": h1_root.name,
                    "planned_sha256": planned.reference["sha256"],
                    "fragments_ready_sha256": (
                        fragments_ready.reference["sha256"]
                    ),
                }
            ),
            flush=True,
        )

    def test_h1_04_html(self) -> None:
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _initialized_h1_workspace(
            root=root, source=source, coordinator=coordinator
        )
        planned = _read_sealed_envelope(
            h1_root / "workspace-planned.envelope.json"
        )
        fragments_ready = _read_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json"
        )
        assembled = _read_sealed_envelope(
            h1_root / "workspace-assembled.envelope.json"
        )
        receipt = h1c.run(
            h1_root / "html",
            p1_package=p1_package,
            plan_package=h1_root / "plan",
            plan_input_gate=gate,
            plan_workspace_state=initialized,
            fragment_package=h1_root / "fragments",
            fragment_workspace_state=planned,
            assembly_package=h1_root / "assembly",
            assembly_workspace_state=fragments_ready,
            workspace_state=assembled,
            coordinator=coordinator,
            logical_package_path="H1/html",
            runtime=runtime,
        )
        _write_sealed_envelope(
            h1_root / "workspace-rendered.envelope.json",
            receipt.transition.workspace,
        )

    def test_h1_05_formal_completion(self) -> None:
        root, runtime, source, coordinator, p1_package = self._context()
        h1_root = _h1_attempt_root(root)
        gate = coordinator.build_input_gate("H1", "H1/input-gate.json")
        initialized = _initialized_h1_workspace(
            root=root, source=source, coordinator=coordinator
        )
        planned = _read_sealed_envelope(
            h1_root / "workspace-planned.envelope.json"
        )
        fragments_ready = _read_sealed_envelope(
            h1_root / "workspace-fragments-ready.envelope.json"
        )
        assembled = _read_sealed_envelope(
            h1_root / "workspace-assembled.envelope.json"
        )
        rendered = _read_sealed_envelope(
            h1_root / "workspace-rendered.envelope.json"
        )
        receipt = rt.publish_h1_completion(
            root / "packages" / "H1",
            p1_package=p1_package,
            plan_package=h1_root / "plan",
            plan_input_gate=gate,
            plan_workspace_state=initialized,
            fragment_package=h1_root / "fragments",
            fragment_workspace_state=planned,
            assembly_package=h1_root / "assembly",
            assembly_workspace_state=fragments_ready,
            html_package=h1_root / "html",
            rendered_workspace=rendered,
            coordinator=coordinator,
            next_state_path="state/revision-009.json",
            logical_package_path="H1/stage",
            runtime=runtime,
        )
        waiting = rt.SealedDocument(
            data=receipt.transition.snapshot,
            reference=receipt.transition.reference,
        )
        _write_sealed_envelope(
            h1_root / "state-waiting-author.envelope.json",
            waiting,
        )
        self.assertEqual("waiting_author", waiting.data["status"])

    def test_h1_06_external_approved_decision(self) -> None:
        root, runtime, source, coordinator, p1_package = (
            self._waiting_context()
        )
        h1_root = _h1_attempt_root(root)
        h1_package = root / "packages" / "H1"
        html_package = h1_root / "html"
        machine = {
            "completion_path": "P1/stage-completion.json",
            "completion_sha256": rt.sha256_file(
                p1_package / "stage-completion.json"
            ),
            "manifest_path": "P1/package-manifest.json",
            "manifest_sha256": rt.sha256_file(
                p1_package / "package-manifest.json"
            ),
        }
        human = {
            "completion_path": "H1/stage/stage-completion.json",
            "completion_sha256": rt.sha256_file(
                h1_package / "stage-completion.json"
            ),
            "manifest_path": "H1/stage/package-manifest.json",
            "manifest_sha256": rt.sha256_file(
                h1_package / "package-manifest.json"
            ),
            "html_path": "H1/html/human-review-report.html",
            "html_sha256": rt.sha256_file(
                html_package / "human-review-report.html"
            ),
        }
        event_data = {
            "schema_version": "2.0",
            "run_id": source.run_id,
            "approval_scope": "conception",
            "decision": "approved",
            "machine_package": machine,
            "human_review_package": human,
            "approval_record": {
                "event_seq": 1,
                "text": "External author approved the complete conception.",
            },
            "unresolved_items": [],
        }
        event = rt.seal_document(
            event_data, "external-author/approved-decision.json"
        )
        _write_sealed_envelope(
            root / "external-author" / "approved-decision.envelope.json",
            event,
        )
        waiting = rt.SealedDocument(
            data=coordinator.state,
            reference=coordinator.state_reference,
        )
        receipt = rt.record_author_decision(
            event=event,
            coordinator=coordinator,
            next_state_path="state/approved.json",
            p1_package=p1_package,
            h1_package=h1_package,
            html_package=html_package,
            run_state=waiting,
            runtime=runtime,
        )
        approved = rt.SealedDocument(
            data=receipt.transition.snapshot,
            reference=receipt.transition.reference,
        )
        _write_sealed_envelope(
            root / "external-author" / "state-approved.envelope.json",
            approved,
        )
        self.assertEqual("approved", approved.data["status"])
        self.assertEqual("not_ready", approved.data["development_status"])

    def test_h1_07_final_completion(self) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        root = Path(root_value)
        h1_root = _h1_attempt_root(root)
        runtime = rt.ContractRuntime()
        approved = _read_sealed_envelope(
            root / "external-author" / "state-approved.envelope.json"
        )
        event = _read_sealed_envelope(
            root / "external-author" / "approved-decision.envelope.json"
        )
        coordinator = rt.AutonomousCoordinator.from_snapshot(
            approved.data,
            approved.reference,
            runtime=runtime,
        )
        stage_packages = {
            stage: root / "packages" / stage
            for stage in (
                "B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"
            )
        }
        receipt = rt.publish_final_completion(
            root / "completion",
            run_state=approved,
            stage_packages=stage_packages,
            p1_package=stage_packages["P1"],
            h1_package=stage_packages["H1"],
            html_package=h1_root / "html",
            author_decision=event,
            development_handoff=(
                stage_packages["P1"] / "development-handoff.json"
            ),
            coordinator=coordinator,
            next_state_path="state/final.json",
            logical_package_path="completion",
            runtime=runtime,
        )
        self.assertEqual(
            "ready", receipt.transition.snapshot["development_status"]
        )
        print(
            rt.canonical_json(
                {
                    "stage": "final",
                    "completion_sha256": rt.sha256_file(
                        receipt.package_root
                        / "conception-completion.json"
                    ),
                    "decision_sha256": event.reference["sha256"],
                    "state_sha256": receipt.transition.reference["sha256"],
                }
            ),
            flush=True,
        )


class DeclarativeProposalAdapterTests(unittest.TestCase):
    def test_h1_plan_adapter_declares_six_item_return_contract(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        hints = typing.get_type_hints(adapter.plan_inputs)
        self.assertEqual(tuple, typing.get_origin(hints["return"]))
        self.assertEqual(6, len(typing.get_args(hints["return"])))
        fragment_return = typing.get_type_hints(
            adapter.fragment_submissions
        )["return"]
        self.assertEqual(tuple, typing.get_origin(fragment_return))
        self.assertEqual(3, len(typing.get_args(fragment_return)))
        self.assertEqual(
            ["fragment_submissions", "plan_inputs"], adapter.__all__
        )

    def test_h1_fragment_selector_rejects_identity_meta_leaves(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        value = {
            "id": "FACT-001",
            "status": "not_applicable",
            "claim": "这条控制事实能够被小说片段直接引用并形成可见行动。",
        }
        pointer, selected = adapter._select_substantive_scalar(
            value, anchor_values=[value]
        )
        self.assertEqual("/claim", pointer)
        self.assertEqual(value["claim"], selected)
        self.assertTrue(
            h1b._quote_has_non_identity_substance(selected, [value])
        )

    def test_h1_fragment_briefs_use_bounded_semantic_anchor_subsets(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        anchors = [
            {
                "id": f"SRC-{stage}-{index}",
                "stage": stage,
                "_value": {
                    "claim": f"{stage} 阶段的第 {index} 条控制事实支持片段中的具体行动。"
                },
            }
            for stage in ("S1", "W1", "E1", "T1", "C1")
            for index in range(1, 4)
        ] + [
            {
                "id": "SRC-B0-1",
                "stage": "B0",
                "_value": {"claim": "访谈来源只承担全局追溯，不挤占片段容量。"},
            }
        ]
        allocations = adapter._allocate_fragment_anchor_ids(
            anchors, brief_count=3, max_per_brief=5
        )
        self.assertEqual(3, len(allocations))
        by_id = {item["id"]: item for item in anchors}
        for allocation in allocations:
            self.assertGreaterEqual(len(allocation), 1)
            self.assertLessEqual(len(allocation), 5)
            self.assertTrue(
                {by_id[anchor_id]["stage"] for anchor_id in allocation}
                <= {"S1", "W1", "E1", "T1", "C1"}
            )

    def test_h1_fragment_projection_preflight_matches_production_contract(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        value = {
            "id": "EVT-001",
            "title": "短标题",
            "consequence": "门禁封锁迫使调查者在倒计时结束前改变行动路径。",
        }
        anchor = {
            "id": "SRC-TEST-1",
            "stage": "T1",
            "value_sha256": h1b.rt.canonical_sha256(value),
            "_value": value,
        }
        projection = adapter._build_fact_projection(
            anchor, projection_id="BRIEF-1-PROJ-1"
        )
        self.assertNotIn(
            projection["field_pointer"].rsplit("/", 1)[-1].casefold(),
            {"id", "name", "title", "label"},
        )
        scalar = adapter._pointer_value(
            value, projection["field_pointer"]
        )
        self.assertEqual(
            h1b.rt.canonical_sha256(scalar),
            projection["value_sha256"],
        )
        self.assertTrue(
            h1b._quote_has_non_identity_substance(scalar, [value])
        )
        adapter._preflight_fragment_projection_capacity(
            [projection],
            anchors={anchor["id"]: anchor},
            target_chars_max=100,
        )

    def test_h1_fragment_adapter_is_fixture_agnostic_and_deterministic(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        anchors = [
            {
                "id": f"SRC-{index:02d}",
                "stage": stage,
                "_value": {
                    "claim": f"{stage} 的稳定语义控制事实用于确定性分配。"
                },
            }
            for index, stage in enumerate(
                ("C1", "S1", "T1", "E1", "W1", "C1"), 1
            )
        ]
        forward = adapter._allocate_fragment_anchor_ids(
            anchors, brief_count=3, max_per_brief=4
        )
        reverse = adapter._allocate_fragment_anchor_ids(
            list(reversed(anchors)), brief_count=3, max_per_brief=4
        )
        self.assertEqual(forward, reverse)

    def test_h1_global_control_coverage_remains_complete(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        anchor_ids = ["SRC-000003", "SRC-000001", "SRC-000002"]
        coverage = adapter._build_control_coverage(
            anchor_ids, visible_element_ids=["MOD-WORLD-1"]
        )
        self.assertEqual(set(anchor_ids), {
            item["source_anchor_id"] for item in coverage
        })
        self.assertEqual(len(anchor_ids), len(coverage))
        self.assertTrue(
            all(
                item["visible_element_ids"] == ["MOD-WORLD-1"]
                for item in coverage
            )
        )

    def _real_h1_visual_plan_case(
        self,
    ) -> tuple[Any, Path, dict[str, Any], dict[str, Any]]:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        p1_root = Path(root_value) / "packages" / "P1"
        p1_completion = {
            "path": "P1/stage-completion.json",
            "sha256": rt.sha256_file(
                p1_root / "stage-completion.json"
            ),
        }
        inventory = h1a.build_source_inventory(
            p1_root, p1_completion=p1_completion
        )
        package = json.loads(
            (p1_root / "novel-conception-package.json").read_text(
                encoding="utf-8"
            )
        )
        plan = adapter.plan_inputs(
            p1_root,
            p1_completion=p1_completion,
            input_gate={
                "path": "H1/input-gate.json",
                "sha256": rt.sha256_file(p1_root / "input-gate.json"),
            },
            run_id=package["run_id"],
            session_id="H1-TEST-VISUAL-SOURCES",
            work_title="通用构思评审",
        )[-1]["payload"]["review_plan"]
        return adapter, p1_root, inventory, plan

    def test_h1_visual_allocator_is_bounded_source_injective_and_deterministic(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        anchors = [
            {
                "id": "SRC-S1-A",
                "source_id": "SHARED-001",
                "stage": "S1",
            },
            {
                "id": "SRC-T1-A",
                "source_id": "SHARED-001",
                "stage": "T1",
            },
            {
                "id": "SRC-W1-A",
                "source_id": "WORLD-001",
                "stage": "W1",
            },
            {
                "id": "SRC-E1-A",
                "source_id": "ENV-001",
                "stage": "E1",
            },
            {
                "id": "SRC-C1-A",
                "source_id": "CHAR-001",
                "stage": "C1",
            },
        ]
        forward = adapter._allocate_visual_anchor_ids(
            anchors,
            semantic_role="major_event_timeline",
            max_sources=6,
        )
        reverse = adapter._allocate_visual_anchor_ids(
            list(reversed(anchors)),
            semantic_role="major_event_timeline",
            max_sources=6,
        )
        self.assertEqual(forward, reverse)
        self.assertLessEqual(len(forward), 6)
        by_anchor = {item["id"]: item["source_id"] for item in anchors}
        projected = [by_anchor[item] for item in forward]
        self.assertEqual(len(projected), len(set(projected)))
        self.assertEqual(1, projected.count("SHARED-001"))

    def test_h1_real_visuals_are_bounded_and_source_injective_at_every_level(
        self,
    ) -> None:
        adapter, _, inventory, plan = self._real_h1_visual_plan_case()
        source_by_anchor = {
            item["id"]: item["source_id"]
            for item in inventory["anchors"]
        }
        seen_bindings = 0

        def audit(value: Any) -> None:
            nonlocal seen_bindings
            if isinstance(value, Mapping):
                anchor_ids = value.get("source_anchor_ids")
                if anchor_ids is not None:
                    seen_bindings += 1
                    self.assertGreaterEqual(len(anchor_ids), 1)
                    self.assertLessEqual(
                        len(anchor_ids), adapter.VISUAL_ANCHOR_CAP
                    )
                    projected = [
                        source_by_anchor[item] for item in anchor_ids
                    ]
                    self.assertEqual(
                        len(projected),
                        len(set(projected)),
                    )
                for item in value.values():
                    audit(item)
            elif isinstance(value, list):
                for item in value:
                    audit(item)

        for visual in plan["visual_models"]:
            audit(visual)
        self.assertGreaterEqual(seen_bindings, 5)
        inventory_anchor_ids = {
            item["id"] for item in inventory["anchors"]
        }
        coverage_anchor_ids = {
            item["source_anchor_id"]
            for item in plan["control_coverage"]
        }
        self.assertEqual(inventory_anchor_ids, coverage_anchor_ids)
        self.assertEqual(
            len(inventory["anchors"]),
            len(plan["control_coverage"]),
        )

    def test_h1_real_visual_plan_dry_runs_assembly_projection(
        self,
    ) -> None:
        _, _, inventory, plan = self._real_h1_visual_plan_case()
        source_by_anchor = {
            item["id"]: item["source_id"]
            for item in inventory["anchors"]
        }
        fragments = [
            {
                "id": brief["slot_id"],
                "title": brief["title"],
                "review_purpose": brief["review_purpose"],
                "text": "用于验证视觉投影边界的构思体验片段。",
                "source_ids": sorted({
                    source_by_anchor[item]
                    for item in brief["source_anchor_ids"]
                }),
            }
            for brief in plan["fragment_briefs"]
        ]
        report = h1a._assemble_report(plan, inventory, fragments)
        self.assertEqual(
            [item["id"] for item in plan["visual_models"]],
            [item["id"] for item in report["visual_models"]],
        )
        runtime = rt.ContractRuntime()
        runtime.validate(
            report, "human-review-report.schema.json"
        )

    def test_h1_real_visual_plan_is_deterministic(
        self,
    ) -> None:
        _, _, _, first = self._real_h1_visual_plan_case()
        _, _, _, second = self._real_h1_visual_plan_case()
        self.assertEqual(
            rt.canonical_sha256(first),
            rt.canonical_sha256(second),
        )

    def test_h1_fragment_text_builder_meets_production_contract(
        self,
    ) -> None:
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        quote = (
            "A forged warning can be defeated by comparing upstream marks "
            "and physical travel time."
        )
        text, evidence = adapter._build_fragment_text(
            [quote], target_visible_units=100
        )
        self.assertEqual((100, 86, 14), h1b._visible_units(text))
        self.assertEqual(text, adapter._build_fragment_text(
            [quote], target_visible_units=100
        )[0])
        self.assertEqual(2, len([
            item for item in text.splitlines() if item.strip()
        ]))
        for key in ("choice", "consequence", "state_change"):
            self.assertIn(evidence[key], text)
        self.assertIn(quote, text)
        h1b._validate_text(
            text,
            {
                "slot_id": "FRAG-TEST",
                "target_words_min": 100,
                "target_words_max": 100,
            },
        )
        scene_fields = (
            "before_state",
            "immediate_goal",
            "pressure",
            "obstacle",
            "required_choice",
            "direct_consequence",
            "after_state",
        )
        scene_contract = {
            field: f"value-{index}"
            for index, field in enumerate(reversed(scene_fields), 1)
        }
        canonical_round_trip = json.loads(
            rt.canonical_json(scene_contract)
        )
        scene_evidence = adapter._build_scene_contract_evidence(
            canonical_round_trip,
            evidence_quote=evidence["choice"],
        )
        self.assertEqual(
            list(scene_fields),
            [item["field"] for item in scene_evidence],
        )

    def test_h1_real_inventory_briefs_bind_pov_source(
        self,
    ) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        p1_root = Path(root_value) / "packages" / "P1"
        package = json.loads(
            (p1_root / "novel-conception-package.json").read_text(
                encoding="utf-8"
            )
        )
        p1_completion = {
            "path": "P1/stage-completion.json",
            "sha256": rt.sha256_file(
                p1_root / "stage-completion.json"
            ),
        }
        plan_inputs = adapter.plan_inputs(
            p1_root,
            p1_completion=p1_completion,
            input_gate={
                "path": "H1/input-gate.json",
                "sha256": rt.sha256_file(p1_root / "input-gate.json"),
            },
            run_id=package["run_id"],
            session_id="H1-TEST-POV-SOURCE",
            work_title="通用构思评审",
        )
        plan = plan_inputs[-1]["payload"]["review_plan"]
        inventory = h1a.build_source_inventory(
            p1_root, p1_completion=p1_completion
        )
        validated = h1a.validate_review_plan(
            plan,
            source_inventory=inventory,
            workspace_state={"session_id": plan["h1_session_id"]},
            work_identity=plan["work_identity"],
            runtime=rt.ContractRuntime(),
        )
        source_by_anchor = {
            item["id"]: item["source_id"]
            for item in inventory["anchors"]
        }
        for brief in validated["fragment_briefs"]:
            self.assertIn(
                brief["pov_character_id"],
                {
                    source_by_anchor[anchor_id]
                    for anchor_id in brief["source_anchor_ids"]
                },
            )
        with tempfile.TemporaryDirectory(
            prefix="h1-pov-focused-"
        ) as temporary:
            plan_root = Path(temporary)
            _write_json(plan_root / "review-plan.json", plan)
            _write_json(
                plan_root / "source-inventory.json", inventory
            )
            submissions = adapter.fragment_submissions(
                plan_root, p1_package=p1_root
            )
            enriched = adapter._load_anchor_values(
                p1_root, inventory["anchors"]
            )
            anchors = {item["id"]: item for item in enriched}
            for phase_count in range(1, 4):
                h1b._validate_partial_submissions(
                    submissions[:phase_count],
                    briefs=plan["fragment_briefs"],
                    anchors=anchors,
                )

    def test_h1_real_inventory_uses_substantive_c1_pov_anchor(
        self,
    ) -> None:
        root_value = os.environ.get("CONCEPTION_E2E_RESUME_ROOT")
        if not root_value:
            self.skipTest("CONCEPTION_E2E_RESUME_ROOT is not set")
        adapter = importlib.import_module(
            "harnesses.novel-conception-autonomous.evals.h1_proposal_adapter"
        )
        p1_root = Path(root_value) / "packages" / "P1"
        p1_completion = {
            "path": "P1/stage-completion.json",
            "sha256": rt.sha256_file(
                p1_root / "stage-completion.json"
            ),
        }
        inventory = h1a.build_source_inventory(
            p1_root, p1_completion=p1_completion
        )
        enriched = adapter._load_anchor_values(
            p1_root, inventory["anchors"]
        )
        pov_anchor = adapter._select_pov_anchor(enriched)
        self.assertEqual("C1", pov_anchor["stage"])
        self.assertTrue(str(pov_anchor["source_id"]).startswith("CHR-"))
        package = json.loads(
            (p1_root / "novel-conception-package.json").read_text(
                encoding="utf-8"
            )
        )
        plan = adapter.plan_inputs(
            p1_root,
            p1_completion=p1_completion,
            input_gate={
                "path": "H1/input-gate.json",
                "sha256": rt.sha256_file(p1_root / "input-gate.json"),
            },
            run_id=package["run_id"],
            session_id="H1-TEST-C1-POV",
            work_title="通用构思评审",
        )[-1]["payload"]["review_plan"]
        for brief in plan["fragment_briefs"]:
            self.assertEqual(
                pov_anchor["source_id"], brief["pov_character_id"]
            )
            self.assertIn(
                pov_anchor["id"], brief["source_anchor_ids"]
            )

    @staticmethod
    def _baseline_from_fixture(
        fixture: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "run_id": fixture["run_id"],
            "control_registry": [
                {
                    "id": item["control_id"],
                    "hardness": item["hardness"],
                    "heading": item["heading"],
                    "value": item["value"],
                }
                for item in fixture["interviews"]
            ],
            "fact_dependencies": _project_fixture_fact_dependencies(
                fixture["fact_dependencies"]
            ),
        }

    @staticmethod
    def _fixture_controls(
        fixture: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        return sorted(
            [
                {
                    "id": item["control_id"],
                    "hardness": item["hardness"],
                    "heading": item["heading"],
                    "value": item["value"],
                    "domain": item["stage"],
                }
                for item in fixture["interviews"]
            ],
            key=lambda item: item["id"],
        )

    @staticmethod
    def _direct_models(
        *,
        controls: list[dict[str, Any]],
        fact_dependencies: list[dict[str, Any]],
        run_id: str,
    ) -> tuple[
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
    ]:
        baseline = {
            "run_id": run_id,
            "control_registry": [
                {
                    "id": item["id"],
                    "hardness": item["hardness"],
                    "heading": item["heading"],
                    "value": item["value"],
                }
                for item in controls
            ],
            "fact_dependencies": copy.deepcopy(fact_dependencies),
        }
        gate = {"path": "input-gate.json", "sha256": "a" * 64}
        source_artifacts = [
            {
                "path": "sources/B0/author-control-baseline.json",
                "sha256": "b" * 64,
            }
        ]
        storyline = proposal_module._storyline_proposal(
            run_id=run_id,
            gate_reference=gate,
            source_artifacts=source_artifacts,
            controls=controls,
        )
        common = {
            "run_id": run_id,
            "gate_reference": gate,
            "source_artifacts": source_artifacts,
            "baseline": baseline,
            "storyline": storyline,
        }
        world = proposal_module._world_proposal(**common)
        environment = proposal_module._environment_proposal(
            **common,
            world=world,
        )
        timeline = proposal_module._event_proposal(
            **common,
            world=world,
            environment=environment,
        )
        return baseline, storyline, world, environment, timeline

    def test_graph_world_times_use_stable_longest_path_ranks(self) -> None:
        event_ids = ["EV-D", "EV-C", "EV-B", "EV-A"]
        edges = [
            {
                "id": "CE-A-C",
                "from_event_id": "EV-A",
                "to_event_id": "EV-C",
            },
            {
                "id": "CE-B-C",
                "from_event_id": "EV-B",
                "to_event_id": "EV-C",
            },
            {
                "id": "CE-C-D",
                "from_event_id": "EV-C",
                "to_event_id": "EV-D",
            },
        ]
        forward = proposal_module._graph_derived_world_times(
            event_ids, edges
        )
        reverse = proposal_module._graph_derived_world_times(
            list(reversed(event_ids)),
            list(reversed(edges)),
        )
        self.assertEqual(forward, reverse)
        self.assertEqual("[WT:000100]", forward["EV-A"])
        self.assertEqual(forward["EV-A"], forward["EV-B"])
        self.assertEqual("[WT:000101]", forward["EV-C"])
        self.assertEqual("[WT:000102]", forward["EV-D"])

    def test_graph_world_times_fail_closed_on_invalid_graphs(self) -> None:
        cases = (
            (
                "duplicate-event",
                ["EV-A", "EV-A"],
                [],
                "T1_PROPOSAL_EVENT_ID_DUPLICATE",
            ),
            (
                "dangling",
                ["EV-A"],
                [
                    {
                        "id": "CE-DANGLING",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-Z",
                    }
                ],
                "T1_PROPOSAL_CAUSAL_DANGLING",
            ),
            (
                "self-loop",
                ["EV-A"],
                [
                    {
                        "id": "CE-SELF",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-A",
                    }
                ],
                "T1_PROPOSAL_CAUSAL_SELF_LOOP",
            ),
            (
                "duplicate-edge-id",
                ["EV-A", "EV-B", "EV-C"],
                [
                    {
                        "id": "CE-DUPLICATE",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-B",
                    },
                    {
                        "id": "CE-DUPLICATE",
                        "from_event_id": "EV-B",
                        "to_event_id": "EV-C",
                    },
                ],
                "T1_PROPOSAL_CAUSAL_EDGE_ID_DUPLICATE",
            ),
            (
                "duplicate-endpoint-pair",
                ["EV-A", "EV-B"],
                [
                    {
                        "id": "CE-FIRST",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-B",
                    },
                    {
                        "id": "CE-SECOND",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-B",
                    },
                ],
                "T1_PROPOSAL_CAUSAL_ENDPOINT_PAIR_DUPLICATE",
            ),
            (
                "cycle",
                ["EV-A", "EV-B"],
                [
                    {
                        "id": "CE-A-B",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-B",
                    },
                    {
                        "id": "CE-B-A",
                        "from_event_id": "EV-B",
                        "to_event_id": "EV-A",
                    },
                ],
                "T1_PROPOSAL_CAUSAL_CYCLE",
            ),
        )
        for name, event_ids, edges, code in cases:
            original_edges = copy.deepcopy(edges)
            with self.subTest(name=name), self.assertRaisesRegex(
                proposal_module.ProposalEvidenceError, code
            ):
                proposal_module._graph_derived_world_times(
                    event_ids, edges
                )
            self.assertEqual(original_edges, edges)

    def test_graph_world_times_fail_closed_on_six_digit_overflow(
        self,
    ) -> None:
        with (
            mock.patch.object(proposal_module, "_WORLD_TIME_MAX", 100),
            self.assertRaisesRegex(
                proposal_module.ProposalEvidenceError,
                "T1_PROPOSAL_WORLD_TIME_OVERFLOW",
            ),
        ):
            proposal_module._graph_derived_world_times(
                ["EV-A", "EV-B"],
                [
                    {
                        "id": "CE-A-B",
                        "from_event_id": "EV-A",
                        "to_event_id": "EV-B",
                    }
                ],
            )

    def test_event_clock_scales_past_old_ten_line_threshold(self) -> None:
        generic = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        facts = _project_fixture_fact_dependencies(
            generic["fact_dependencies"]
        )
        for line_count in (10, 22):
            controls = [
                {
                    "id": f"CTL-{index:03d}",
                    "hardness": "author_locked",
                    "heading": f"Control {index}",
                    "value": f"Substantive obligation {index}.",
                    "domain": "I0",
                }
                for index in range(1, line_count + 1)
            ]
            _, storyline, _, _, timeline = self._direct_models(
                controls=controls,
                fact_dependencies=facts,
                run_id=f"scale-{line_count}",
            )
            times = {
                event["id"]: event["world_time"]
                for event in timeline["major_events"]
            }
            self.assertEqual(line_count, len(storyline["storylines"]))
            self.assertEqual(
                sum(
                    len(line["state_changes"]) + 1
                    for line in storyline["storylines"]
                ),
                len(timeline["major_events"]),
            )
            expected_responsibilities = {
                role
                for group in proposal_module.ROLES
                for role in group
            }
            for line in storyline["storylines"]:
                line_responsibilities = "\n".join(
                    event["responsibility"]
                    for event in timeline["major_events"]
                    if line["id"] in event["storyline_ids"]
                )
                with self.subTest(
                    line_count=line_count,
                    storyline_id=line["id"],
                ):
                    self.assertTrue(
                        all(
                            f"[RESP:{role}]" in line_responsibilities
                            for role in expected_responsibilities
                        ),
                        line["id"],
                    )
            self.assertTrue(
                all(
                    times[edge["from_event_id"]]
                    < times[edge["to_event_id"]]
                    for edge in timeline["causal_edges"]
                )
            )

    def test_actual_proposal_and_t1_owner_reject_duplicate_edges(
        self,
    ) -> None:
        fixture = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        controls = self._fixture_controls(fixture)
        facts = _project_fixture_fact_dependencies(
            fixture["fact_dependencies"]
        )
        original_clock = proposal_module._graph_derived_world_times
        adapter_cases = (
            (
                "edge-id",
                "T1_PROPOSAL_CAUSAL_EDGE_ID_DUPLICATE",
                lambda edge: edge,
            ),
            (
                "endpoint-pair",
                "T1_PROPOSAL_CAUSAL_ENDPOINT_PAIR_DUPLICATE",
                lambda edge: {**edge, "id": "CE-ADHOC-DUPLICATE-PAIR"},
            ),
        )
        for name, code, duplicate in adapter_cases:
            observed: dict[str, Any] = {}

            def inject_duplicate(
                event_ids: list[str],
                causal_edges: list[Mapping[str, Any]],
            ) -> dict[str, str]:
                observed["event_ids"] = list(event_ids)
                observed["before_count"] = len(causal_edges)
                causal_edges.append(
                    duplicate(copy.deepcopy(causal_edges[0]))
                )
                observed["injected_edges"] = copy.deepcopy(causal_edges)
                try:
                    return original_clock(event_ids, causal_edges)
                finally:
                    observed["final_edges"] = copy.deepcopy(causal_edges)

            with (
                self.subTest(layer="adapter", case=name),
                mock.patch.object(
                    proposal_module,
                    "_graph_derived_world_times",
                    side_effect=inject_duplicate,
                ),
                self.assertRaisesRegex(
                    proposal_module.ProposalEvidenceError, code
                ),
            ):
                self._direct_models(
                    controls=controls,
                    fact_dependencies=facts,
                    run_id=f"duplicate-{name}",
                )
            self.assertEqual(
                observed["before_count"] + 1,
                len(observed["injected_edges"]),
            )
            self.assertEqual(
                observed["injected_edges"],
                observed["final_edges"],
            )
            self.assertEqual(
                len(observed["event_ids"]),
                len(set(observed["event_ids"])),
            )

        baseline, storyline, world, environment, timeline = (
            self._direct_models(
                controls=controls,
                fact_dependencies=facts,
                run_id="duplicate-owner",
            )
        )
        owner_cases = (
            (
                "edge-id",
                copy.deepcopy(timeline["causal_edges"][0]),
            ),
            (
                "endpoint-pair",
                {
                    **copy.deepcopy(timeline["causal_edges"][0]),
                    "id": "CE-ADHOC-DUPLICATE-PAIR",
                },
            ),
        )
        for name, duplicate_edge in owner_cases:
            invalid = copy.deepcopy(timeline)
            original_count = len(invalid["causal_edges"])
            invalid["causal_edges"].append(duplicate_edge)
            submitted_edges = copy.deepcopy(invalid["causal_edges"])
            with (
                self.subTest(layer="owner", case=name),
                self.assertRaisesRegex(
                    t1.T1Error, "T1_CAUSAL_EDGE_DUPLICATE"
                ),
            ):
                t1._validate_model(
                    invalid,
                    baseline,
                    storyline,
                    world,
                    environment,
                    controls,
                    rt.ContractRuntime(),
                )
            self.assertEqual(
                original_count + 1,
                len(invalid["causal_edges"]),
            )
            self.assertEqual(
                submitted_edges,
                invalid["causal_edges"],
            )

    def test_generic_and_duanxian_direct_timelines_pass_t1_owner(
        self,
    ) -> None:
        expected_counts = {
            GENERIC_FIXTURE: (6, 18, 17, 6, 5),
            DUANXIAN_FIXTURE: (22, 66, 65, 22, 21),
        }
        for fixture_path, counts in expected_counts.items():
            with self.subTest(fixture=fixture_path.parent.name):
                fixture_bytes = fixture_path.read_bytes()
                fixture = json.loads(fixture_bytes.decode("utf-8"))
                controls = self._fixture_controls(fixture)
                baseline, storyline, world, environment, timeline = (
                    self._direct_models(
                        controls=controls,
                        fact_dependencies=_project_fixture_fact_dependencies(
                            fixture["fact_dependencies"]
                        ),
                        run_id=fixture["run_id"],
                    )
                )
                t1._validate_model(
                    timeline,
                    baseline,
                    storyline,
                    world,
                    environment,
                    controls,
                    rt.ContractRuntime(),
                )
                (
                    control_count,
                    event_count,
                    edge_count,
                    sequence_count,
                    connection_count,
                ) = counts
                self.assertEqual(
                    control_count, len(baseline["control_registry"])
                )
                self.assertEqual(
                    control_count, len(storyline["storyline_demands"])
                )
                self.assertEqual(
                    event_count, len(timeline["major_events"])
                )
                self.assertEqual(
                    edge_count, len(timeline["causal_edges"])
                )
                self.assertEqual(
                    sequence_count,
                    len(timeline["storyline_event_sequences"]),
                )
                self.assertEqual(
                    connection_count,
                    len(timeline["connection_realization"]),
                )
                self.assertEqual(
                    {control["id"] for control in controls},
                    {
                        control["id"]
                        for control in baseline["control_registry"]
                    },
                )
                times = {
                    event["id"]: event["world_time"]
                    for event in timeline["major_events"]
                }
                self.assertNotIn("[WT:000000]", times.values())
                self.assertEqual("[WT:000100]", min(times.values()))
                self.assertEqual(
                    min(times.values()),
                    timeline["event_span"]["start"],
                )
                self.assertEqual(
                    max(times.values()),
                    timeline["event_span"]["end"],
                )
                self.assertTrue(
                    all(
                        times[edge["from_event_id"]]
                        < times[edge["to_event_id"]]
                        for edge in timeline["causal_edges"]
                    )
                )
                reversed_time = copy.deepcopy(timeline)
                first_edge = reversed_time["causal_edges"][0]
                reversed_times = {
                    event["id"]: event
                    for event in reversed_time["major_events"]
                }
                reversed_times[first_edge["to_event_id"]]["world_time"] = (
                    reversed_times[first_edge["from_event_id"]]["world_time"]
                )
                with self.assertRaises(t1.T1Error):
                    t1._validate_model(
                        reversed_time,
                        baseline,
                        storyline,
                        world,
                        environment,
                        controls,
                        rt.ContractRuntime(),
                    )
                self.assertEqual(
                    len(fixture["semantic_assertions"]),
                    16 if fixture_path == DUANXIAN_FIXTURE else 3,
                )
                self.assertEqual(fixture_bytes, fixture_path.read_bytes())

    def test_preflight_scans_generic_and_duanxian_without_collisions(
        self,
    ) -> None:
        for fixture_path in (GENERIC_FIXTURE, DUANXIAN_FIXTURE):
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            evidence = proposal_module.DeclarativeProposalAdapter(
                fixture
            ).preflight(
                baseline=self._baseline_from_fixture(fixture)
            )
            self.assertEqual("ready", evidence["status"])
            self.assertEqual(
                sorted(item["control_id"] for item in fixture["interviews"]),
                evidence["baseline_definition_ids"],
            )
            self.assertEqual(
                {"S1", "W1", "E1", "T1", "C1"},
                set(evidence["definitions_by_stage"]),
            )

    def test_preflight_reports_reserved_definition_collision(self) -> None:
        registry = proposal_module.IdRegistry(["INT-001"])
        with self.assertRaisesRegex(
            ValueError, "ID_PREFLIGHT_COLLISION"
        ) as caught:
            registry.register(
                {
                    "stage": "S1",
                    "authority_partition": {
                        "author_locked": [],
                        "autonomous_owned": ["INT-001"],
                        "downstream_freedom": [],
                        "author_open": [],
                    },
                    "definitions": [
                        {"id": "INT-001", "meaning": "collision"}
                    ],
                }
            )
        self.assertIn(
            "generated_reserved_collisions", str(caught.exception)
        )

    def test_complete_fixture_authority_partitions_are_globally_disjoint(
        self,
    ) -> None:
        fixture = json.loads(GENERIC_FIXTURE.read_text(encoding="utf-8"))
        adapter = proposal_module.DeclarativeProposalAdapter(fixture)
        controls = [
            {
                "id": item["control_id"],
                "hardness": item["hardness"],
                "heading": item["heading"],
                "value": item["value"],
            }
            for item in fixture["interviews"]
        ]
        baseline = {
            "run_id": fixture["run_id"],
            "control_registry": controls,
            "fact_dependencies": fixture["fact_dependencies"],
        }
        gate = {"path": "gate.json", "sha256": "a" * 64}
        common = {
            "run_id": fixture["run_id"],
            "gate_reference": gate,
            "source_artifacts": [],
            "baseline": baseline,
        }
        storyline = adapter.storyline(
            run_id=fixture["run_id"],
            gate_reference=gate,
            source_artifacts=[],
            controls=controls,
        )
        world = adapter.world(**common, storyline=storyline)
        environment = adapter.environment(
            **common, storyline=storyline, world=world
        )
        timeline = adapter.event(
            **common,
            storyline=storyline,
            world=world,
            environment=environment,
        )
        character = adapter.character(
            **common,
            storyline=storyline,
            world=world,
            environment=environment,
            timeline=timeline,
        )
        partitions = adapter.assert_authority_partitions(
            [storyline, world, environment, timeline, character]
        )
        names = list(partitions)
        for index, left in enumerate(names):
            for right in names[index + 1 :]:
                self.assertFalse(
                    set(partitions[left]) & set(partitions[right]),
                    f"{left}/{right}",
                )
        controls_by_hardness = {
            "author_locked": {
                item["control_id"]
                for item in fixture["interviews"]
                if item["hardness"] == "author_locked"
            },
            "author_open": {
                item["control_id"]
                for item in fixture["interviews"]
                if item["hardness"] == "author_open"
            },
        }
        self.assertTrue(
            controls_by_hardness["author_locked"]
            <= set(partitions["author_locked"])
        )
        self.assertTrue(
            controls_by_hardness["author_open"]
            <= set(partitions["author_open"])
        )

    def test_empty_information_evidence_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "C1_PROPOSAL_INFORMATION_EVIDENCE_MISSING",
        ):
            proposal_module._select_information_evidence(
                {
                    "information_changes": [],
                    "causal_edges": [],
                    "major_events": [],
                }
            )

    @staticmethod
    def _q1_record(
        stage: str, identifier: str, links: list[str]
    ) -> dict[str, Any]:
        value = {
            "id": identifier,
            "meaning": f"{stage} deterministic story meaning",
            "links": links,
        }
        return {
            "id": identifier,
            "stage": stage,
            "kind": "governance",
            "value": value,
            "value_sha256": rt.canonical_sha256(value),
        }

    def test_cross_stage_binding_rejects_same_stage_only_candidates(self) -> None:
        adapter = object.__new__(proposal_module.Q1ProposalAdapter)
        adapter.by_stage = {
            "S1": [
                self._q1_record("S1", "SL-A", ["SL-B"]),
                self._q1_record("S1", "SL-B", []),
            ],
            "T1": [],
        }
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "Q1_PROPOSAL_RELATION_MISSING",
        ):
            adapter._bind(
                adapter._check("CHK-CROSS", "cross-domain"),
                stages=["S1", "T1"],
                predicate="cross-domain-reference",
                operator="compare-domains",
                target_stage="S1",
                cross_stage=True,
            )

    def test_cross_stage_binding_selects_deterministic_frozen_relation(self) -> None:
        adapter = object.__new__(proposal_module.Q1ProposalAdapter)
        adapter.by_stage = {
            "S1": [self._q1_record("S1", "SL-A", [])],
            "T1": [
                self._q1_record("T1", "EV-A", ["SL-A"]),
                self._q1_record("T1", "EV-Z", ["SL-A"]),
            ],
        }
        check = adapter._check("CHK-CROSS", "cross-domain")
        binding = adapter._bind(
            check,
            stages=["S1", "T1"],
            predicate="cross-domain-reference",
            operator="compare-domains",
            target_stage="S1",
            cross_stage=True,
        )
        self.assertEqual(["EV-A", "SL-A"], check["evidence_ids"])
        self.assertEqual(
            ["T1", "S1"],
            [item["stage"] for item in binding["evidence_objects"]],
        )

    def test_consistency_chain_rejects_noncanonical_relations(self) -> None:
        def adapter_with(
            t1_links: list[str],
            e1_links: list[str],
        ) -> Any:
            adapter = object.__new__(proposal_module.Q1ProposalAdapter)
            t1_record = self._q1_record("T1", "ST-A", t1_links)
            t1_record["value"]["meaning"] += " mentions ENV-A in prose"
            t1_record["value_sha256"] = rt.canonical_sha256(
                t1_record["value"]
            )
            adapter.by_stage = {
                "T1": [
                    t1_record,
                    self._q1_record("T1", "ENV-A", ["WF-A"]),
                ],
                "E1": [self._q1_record("E1", "ENV-A", e1_links)],
                "W1": [self._q1_record("W1", "WF-A", [])],
            }
            return adapter

        cases = [
            ("substring-only first hop", [], ["WF-A"]),
            ("same-stage shadow", [], []),
            ("missing second hop", ["ENV-A"], []),
        ]
        for label, t1_links, e1_links in cases:
            with (
                self.subTest(case=label),
                self.assertRaisesRegex(
                    proposal_module.ProposalEvidenceError,
                    "Q1_PROPOSAL_CHAIN_MISSING",
                ),
            ):
                adapter = adapter_with(t1_links, e1_links)
                adapter._bind_chain(
                    adapter._check("CHK-CONSISTENCY", "consistency"),
                    stage_path=("T1", "E1", "W1"),
                    predicate="consistent-with",
                    operator="compare-semantics",
                    preferred_target_kind="world-fact",
                )
        with self.assertRaisesRegex(
            proposal_module.ProposalEvidenceError,
            "Q1_PROPOSAL_CHAIN_STAGE_PATH_INVALID",
        ):
            adapter = adapter_with(["ENV-A"], ["WF-A"])
            adapter._bind_chain(
                adapter._check("CHK-CONSISTENCY", "consistency"),
                stage_path=("T1", "W1", "E1"),
                predicate="consistent-with",
                operator="compare-semantics",
            )

    def test_handoff_payload_binds_all_scopes_and_exact_read_set(self) -> None:
        def typed_record(
            stage: str,
            identifier: str,
            value: dict[str, Any],
            *,
            kind: str = "governance",
        ) -> dict[str, Any]:
            body = {"id": identifier, **value}
            return {
                "id": identifier,
                "stage": stage,
                "kind": kind,
                "value": body,
                "value_sha256": rt.canonical_sha256(body),
            }

        adapter = object.__new__(proposal_module.Q1ProposalAdapter)
        adapter.by_stage = {
            "B0": [
                typed_record(
                    "B0",
                    "INT-A",
                    {"meaning": "A concrete author control meaning."},
                )
            ],
            "S1": [
                typed_record(
                    "S1",
                    "EVD-A",
                    {
                        "responsibility": (
                            "Carry the complete event responsibility."
                        )
                    },
                )
            ],
            "W1": [
                typed_record(
                    "W1",
                    "AF-A",
                    {"constraints": ["A concrete world constraint."]},
                ),
                typed_record(
                    "W1",
                    "DEC-A",
                    {
                        "selection": "Select the costly world rule.",
                        "impact_ids": ["WF-A"],
                    },
                ),
                typed_record(
                    "W1",
                    "WF-A",
                    {"statement": "The world enforces a costly rule."},
                    kind="world-fact",
                ),
            ],
            "E1": [
                typed_record(
                    "E1",
                    "ACCESS-A",
                    {
                        "responsibility": (
                            "Authorize bounded access to the environment."
                        ),
                        "evidence_ids": ["WF-A"],
                    },
                )
            ],
            "T1": [
                typed_record(
                    "T1",
                    "CE-A",
                    {
                        "from_event_id": "EV-A",
                        "mechanism": (
                            "The first event creates the next condition."
                        ),
                    },
                ),
                typed_record(
                    "T1",
                    "COV-A",
                    {
                        "evidence": (
                            "The event chain realizes the responsibility."
                        ),
                        "source_ids": ["EVD-A"],
                    },
                ),
                typed_record(
                    "T1",
                    "CR-A",
                    {
                        "causal_edge_ids": ["CE-A"],
                        "source_anchor": {
                            "state": (
                                "A measured consequence changes the "
                                "available choice."
                            )
                        },
                    },
                ),
                typed_record(
                    "T1",
                    "EV-A",
                    {
                        "responsibility": (
                            "Execute the decisive causal event."
                        )
                    },
                ),
                typed_record(
                    "T1",
                    "ST-A",
                    {
                        "from_state": "The prior state limits action.",
                        "to_state": "The next state exposes a choice.",
                        "consequence": (
                            "The transition creates a visible consequence."
                        ),
                        "allowed_by_ids": ["ACCESS-A"],
                    },
                ),
            ],
            "C1": [
                typed_record(
                    "C1",
                    "AGY-A",
                    {
                        "chosen_action": (
                            "The agent chooses the costly action."
                        ),
                        "cost": "The choice creates a personal cost.",
                        "event_ids": ["EV-A"],
                    },
                ),
                typed_record(
                    "C1",
                    "DEV-A",
                    {
                        "acceptance_checks": [
                            "Development preserves an explicit freedom."
                        ]
                    },
                    kind="development-freedom",
                ),
            ],
        }
        allowlist = [
            {"path": f"inputs/file-{index}.json", "sha256": f"{index:064x}"}
            for index in range(12)
        ]
        payload = adapter.handoff_payload(allowlist=allowlist)
        self.assertEqual(
            [item["path"] for item in allowlist], payload["read_set"]
        )
        self.assertEqual(
            {
                "story_subject",
                "storyline_trace",
                "event_conditions",
                "character_choices",
                "development_freedoms",
            },
            {item["scope"] for item in payload["handoff_checks"]},
        )
        checks = {item["id"]: item for item in payload["handoff_checks"]}
        self.assertEqual(
            ["DEV-A"],
            checks["HANDOFF-FREEDOM"]["evidence_ids"],
        )
        for binding in payload["assertion_bindings"]:
            self.assertEqual(
                checks[binding["check_id"]]["scope"], binding["scope"]
            )
            objects = binding["evidence_objects"]
            if binding["scope"] in {
                "storyline_trace",
                "event_conditions",
                "character_choices",
            }:
                self.assertNotEqual(objects[0]["stage"], objects[1]["stage"])
            for selected in objects:
                record = next(
                    item
                    for item in adapter.by_stage[selected["stage"]]
                    if item["id"] == selected["id"]
                )
                self.assertEqual(
                    record["value_sha256"], selected["value_sha256"]
                )
                for projection in selected["projections"]:
                    self.assertEqual(
                        rt.canonical_sha256(
                            proposal_module._eval_pointer_value(
                                record["value"], projection["path"]
                            )
                        ),
                        projection["value_sha256"],
                    )
        semantic = adapter.semantic_payloads()
        review = adapter.final_review(
            run_id="RUN-UNIT",
            input_gate={"path": "Q1/input-gate.json", "sha256": "a" * 64},
            semantic_payloads=semantic,
            development_usability_test=payload[
                "development_usability_test"
            ],
            handoff_evidence={
                "path": "sealed-handoff/handoff-test-evidence.json",
                "sha256": "b" * 64,
            },
            semantic_task_id="semantic-task",
            handoff_task_id="handoff-task",
            handoff_allowlist=allowlist,
        )
        self.assertEqual([], review["findings"])
        self.assertIsNone(review["return_request"])
        rt.ContractRuntime().validate(
            review, "conception-review.schema.json"
        )
        self.assertEqual(
            11,
            sum(
                len(review[field])
                for field in (
                    "domain_reviews",
                    "cross_domain_checks",
                    "reality_claim_review",
                    "coverage_recalculation",
                    "consistency_matrix",
                    "causal_challenges",
                    "easy_solution_challenges",
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
