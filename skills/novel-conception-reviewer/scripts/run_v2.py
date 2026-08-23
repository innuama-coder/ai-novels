"""Production Q1 dual-context runtime for autonomous novel-conception V2.

The runtime owns identity, input projection, phase order, routing, validation
and packaging.  It never writes domain-review prose, findings, handoff answers
or a verdict on behalf of either reviewing Agent.
"""

from __future__ import annotations

import copy
import importlib
import json
import hashlib
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


canonical_runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
stage_identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)
_HERE = Path(__file__).resolve()
_SKILL = _HERE.parents[1]
_REPO = _HERE.parents[3]
_SCHEMAS = (
    _REPO
    / "docs"
    / "ai-novel-workflow"
    / "contracts"
    / "autonomous-v2"
)
SEMANTIC_PHASES = (
    "review-plan",
    "domain-challenges",
    "cross-domain-challenges",
)
SEMANTIC_PHASE_FIELDS = {
    "review-plan": ("review_plan",),
    "domain-challenges": (
        "domain_reviews",
        "reality_claim_review",
        "coverage_recalculation",
        "causal_challenges",
        "easy_solution_challenges",
        "assertion_bindings",
    ),
    "cross-domain-challenges": (
        "cross_domain_checks",
        "consistency_matrix",
        "assertion_bindings",
    ),
}
HANDOFF_PHASE = "development-handoff-test"
FINAL_PHASE = "final-review"
STAGE_CANONICAL = {
    "B0": "author-control-baseline.json",
    "S1": "storyline-architecture.json",
    "W1": "world-model.json",
    "E1": "environment-system.json",
    "T1": "event-timeline.json",
    "C1": "character-system.json",
}
UPSTREAM_STAGES = ("S1", "W1", "E1", "T1", "C1")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CHECK_FIELDS_BY_PHASE = {
    "domain-challenges": (
        "domain_reviews",
        "reality_claim_review",
        "coverage_recalculation",
        "causal_challenges",
        "easy_solution_challenges",
    ),
    "cross-domain-challenges": (
        "cross_domain_checks",
        "consistency_matrix",
    ),
    "handoff": ("handoff_checks",),
}
FORBIDDEN_HANDOFF_READS = (
    "stage completions",
    "validation records",
    "generation evidence",
    "chat transcripts",
    "interview records",
    "semantic review files",
    "expected answers",
)
HANDOFF_TASKS = (
    "story_subject",
    "storyline_trace",
    "event_conditions",
    "character_choices",
    "development_freedoms",
    "chronology_reconstruction",
    "causal_precondition_trace",
    "information_release_trace",
    "author_control_trace",
)
QUALITY_TRACE_SCOPES = HANDOFF_TASKS[-4:]
QUALITY_COVERAGE_BASIS = (
    "all-id-bearing-objects-in-S1-and-T1-canonical-models"
)
T1_LIFECYCLE_CLOSURE_SCOPE = "typed_lifecycle_causal_closure"
T1_LIFECYCLE_REVIEW_CONTRACT = "T1-2.5-typed-lifecycle-causal-closure"


class Q1Error(ValueError):
    """Stable fail-closed Q1 runtime error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class Q1RunReceipt:
    package_root: Path
    verdict: str
    completion: Any | None
    transition: Any


def _fail(code: str, message: str) -> None:
    raise Q1Error(code, message)


def _identity() -> dict[str, str]:
    task_id = os.environ.get("CODEX_TASK_ID", "").strip()
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not task_id or not thread_id:
        _fail(
            "Q1_CONTROLLED_IDENTITY_REQUIRED",
            "CODEX_TASK_ID and CODEX_THREAD_ID are required",
        )
    return {"task_id": task_id, "thread_id": thread_id}


def _read(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path} root must be an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
        encoding="utf-8",
        newline="",
    )


def _write_new(path: Path, value: Any) -> None:
    if path.exists():
        _fail("Q1_IMMUTABLE_ARTIFACT_EXISTS", str(path))
    _write(path, value)


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_reference(path: Path, *, root: Path) -> dict[str, str]:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(resolved_root).as_posix()
    except ValueError:
        _fail("Q1_REFERENCE_ESCAPE", str(path))
    _logical(relative)
    if not resolved.is_file():
        _fail("Q1_ARTIFACT_MISSING", relative)
    return {"path": relative, "sha256": _sha256_file(resolved)}


def _logical(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _fail("Q1_PATH_INVALID", repr(value))
    return value


def _state_paths(root: Path) -> list[Path]:
    state_root = root / "state"
    return (
        sorted(state_root.glob("revision-*.json"))
        if state_root.is_dir()
        else []
    )


def _latest_state(root: Path) -> dict[str, Any]:
    paths = _state_paths(root)
    if not paths:
        _fail("Q1_STATE_MISSING", str(root))
    state = _read(paths[-1], "Q1_STATE_INVALID")
    if paths[-1].name != f"revision-{state.get('revision', -1):03d}.json":
        _fail("Q1_STATE_INVALID", "revision filename/body mismatch")
    return state


def _advance_state(
    root: Path, prior: Mapping[str, Any], **changes: Any
) -> dict[str, Any]:
    if _latest_state(root) != dict(prior):
        _fail("Q1_STATE_STALE", "caller does not hold latest state")
    next_state = copy.deepcopy(dict(prior))
    next_state.update(copy.deepcopy(changes))
    next_state["revision"] = prior["revision"] + 1
    next_state["previous_state_sha256"] = _canonical_sha256(prior)
    _write_new(
        root / "state" / f"revision-{next_state['revision']:03d}.json",
        next_state,
    )
    return next_state


def _exact_tree(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def materialize_exact_allowlist(
    workspace: str | Path,
    *,
    files: Mapping[str, str | Path],
) -> list[dict[str, str]]:
    """Copy an exact file whitelist into ``workspace/inputs``."""

    root = Path(workspace).resolve()
    if root.exists():
        _fail("Q1_WORKSPACE_EXISTS", str(root))
    if not files:
        _fail("Q1_ALLOWLIST_EMPTY", "at least one file is required")
    records: list[dict[str, str]] = []
    for logical_name, source_name in sorted(files.items()):
        logical_name = _logical(logical_name)
        source = Path(source_name).resolve()
        if not source.is_file():
            _fail("Q1_ALLOWLIST_SOURCE_MISSING", str(source))
        target = root / "inputs" / PurePosixPath(logical_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append(
            {
                "path": f"inputs/{logical_name}",
                "sha256": _sha256_file(target),
            }
        )
    if _exact_tree(root / "inputs") != {
        item["path"].removeprefix("inputs/") for item in records
    }:
        _fail("Q1_ALLOWLIST_TREE_MISMATCH", "materialized tree is not exact")
    return records


def _handoff_allowlist(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
) -> dict[str, Path]:
    roots = {
        "B0": Path(baseline_package).resolve(),
        "S1": Path(storyline_package).resolve(),
        "W1": Path(world_package).resolve(),
        "E1": Path(environment_package).resolve(),
        "T1": Path(event_package).resolve(),
        "C1": Path(character_package).resolve(),
    }
    files: dict[str, Path] = {}
    for stage, root in roots.items():
        files[f"{stage}/{STAGE_CANONICAL[stage]}"] = (
            root / STAGE_CANONICAL[stage]
        )
        files[f"{stage}/package-manifest.json"] = (
            root / "package-manifest.json"
        )
    if len(files) != 12:
        _fail("Q1_ALLOWLIST_INVALID", "B0 plus five packages must yield 12 files")
    return files


def _package_roots(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
) -> dict[str, Path]:
    return {
        "B0": Path(baseline_package).resolve(),
        "S1": Path(storyline_package).resolve(),
        "W1": Path(world_package).resolve(),
        "E1": Path(environment_package).resolve(),
        "T1": Path(event_package).resolve(),
        "C1": Path(character_package).resolve(),
    }


def _source_inventory(roots: Mapping[str, Path]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for stage, root in sorted(roots.items()):
        if not root.is_dir():
            _fail("Q1_INPUT_PACKAGE_MISSING", f"{stage}: {root}")
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_file():
                records.append(
                    {
                        "path": f"{stage}/{path.relative_to(root).as_posix()}",
                        "sha256": _sha256_file(path),
                    }
                )
    if not records:
        _fail("Q1_INPUT_INVENTORY_EMPTY", "no package files found")
    return records


def _validate_frozen_source_inventory(controller: Path) -> dict[str, Any]:
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    frozen = _read(
        controller / "frozen-inputs.json", "Q1_FROZEN_INPUTS_INVALID"
    )
    roots = frozen.get("package_roots")
    if not isinstance(roots, Mapping) or set(roots) != set(STAGE_CANONICAL):
        _fail("Q1_FROZEN_INPUTS_INVALID", "package roots are incomplete")
    current = _source_inventory(
        {stage: Path(roots[stage]).resolve() for stage in STAGE_CANONICAL}
    )
    if current != frozen.get("source_inventory"):
        _fail("Q1_FROZEN_INPUTS_STALE", "source package bytes changed")
    return frozen


def _stage_reference(
    root: Path, stage: str, expected: Mapping[str, Any]
) -> dict[str, str]:
    path = root / "stage-completion.json"
    if expected.get("stage") != stage:
        _fail("Q1_INPUT_TOPOLOGY_INVALID", f"expected {stage} completion")
    reference = {
        "stage": stage,
        "path": expected.get("path"),
        "sha256": _sha256_file(path),
    }
    if reference != dict(expected):
        _fail("Q1_INPUT_COMPLETION_STALE", stage)
    return reference


def _revalidate_inputs(
    roots: Mapping[str, Path],
    *,
    input_gate: Any,
    runtime: Any | None,
) -> dict[str, Any]:
    runtime_module = importlib.import_module(
        "harnesses.novel-conception-autonomous.runtime"
    )
    contract_runtime = runtime or runtime_module.ContractRuntime()
    try:
        contract_runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("Q1_GATE_INVALID", str(error))
    if (
        input_gate.data.get("target_stage") != "Q1"
        or _canonical_sha256(input_gate.data)
        != input_gate.reference.get("sha256")
        or input_gate.data.get("upstream_completions") is None
    ):
        _fail("Q1_GATE_INVALID", "gate is not the exact sealed Q1 gate")
    validators = {
        "S1": (
            "skills.novel-storyline-architecture-designer.scripts.run_v2",
            "validate_s1_package",
        ),
        "W1": (
            "skills.novel-world-model-designer.scripts.run_v2",
            "validate_w1_package",
        ),
        "E1": (
            "skills.novel-environment-system-designer.scripts.run_v2",
            "validate_e1_package",
        ),
        "T1": (
            "skills.novel-event-timeline-designer.scripts.run_v2",
            "validate_t1_package",
        ),
        "C1": (
            "skills.novel-character-system-designer.scripts.run_v2",
            "validate_c1_package",
        ),
    }
    try:
        runtime_module.validate_baseline_package(
            roots["B0"], runtime=contract_runtime
        )
        for stage, (module_name, validator_name) in validators.items():
            validator = getattr(importlib.import_module(module_name), validator_name)
            validator(roots[stage], runtime=contract_runtime)
    except Exception as error:
        _fail("Q1_UPSTREAM_REVALIDATION_FAILED", str(error))
    gate = input_gate.data
    baseline_reference = _stage_reference(
        roots["B0"], "B0", gate["baseline_completion"]
    )
    upstream = gate["upstream_completions"]
    if (
        not isinstance(upstream, list)
        or [item.get("stage") for item in upstream] != list(UPSTREAM_STAGES)
    ):
        _fail("Q1_INPUT_TOPOLOGY_INVALID", "expected ordered S1-W1-E1-T1-C1")
    completion_references = [
        _stage_reference(roots[stage], stage, expected)
        for stage, expected in zip(UPSTREAM_STAGES, upstream, strict=True)
    ]
    run_id = gate["run_id"]
    b0_manifest_hash = _sha256_file(
        roots["B0"] / "package-manifest.json"
    )
    generation_identities: list[dict[str, str]] = []
    for stage in UPSTREAM_STAGES:
        completion = _read(
            roots[stage] / "stage-completion.json",
            "Q1_UPSTREAM_COMPLETION_INVALID",
        )
        manifest = _read(
            roots[stage] / "package-manifest.json",
            "Q1_UPSTREAM_MANIFEST_INVALID",
        )
        model = _read(
            roots[stage] / STAGE_CANONICAL[stage],
            "Q1_UPSTREAM_MODEL_INVALID",
        )
        session = _read(
            roots[stage] / "generation-session.json",
            "Q1_UPSTREAM_SESSION_INVALID",
        )
        if (
            completion.get("run_id") != run_id
            or completion.get("stage") != stage
            or completion.get("status") != "ready"
            or manifest.get("run_id") != run_id
            or manifest.get("stage") != stage
            or manifest.get("verdict") != "ready"
            or model.get("run_id") != run_id
        ):
            _fail("Q1_UPSTREAM_RUN_MISMATCH", stage)
        copied_b0_manifest = (
            roots[stage] / "sources" / "B0" / "package-manifest.json"
        )
        if (
            not copied_b0_manifest.is_file()
            or _sha256_file(copied_b0_manifest) != b0_manifest_hash
        ):
            _fail("Q1_BASELINE_BINDING_MISMATCH", stage)
        thread_id = session.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id.strip():
            _fail("Q1_GENERATION_IDENTITY_INVALID", stage)
        generation_identities.append(
            {"task_id": thread_id.strip(), "thread_id": thread_id.strip()}
        )
    if len({item["thread_id"] for item in generation_identities}) != 5:
        _fail(
            "Q1_GENERATION_IDENTITY_INVALID",
            "S1-C1 must have five distinct generation contexts",
        )
    return {
        "run_id": run_id,
        "baseline_completion": baseline_reference,
        "upstream_completions": completion_references,
        "generation_identities": generation_identities,
        "source_inventory": _source_inventory(roots),
    }


def _validate_review_checks(value: Any, *, label: str) -> None:
    if not isinstance(value, list) or not value:
        _fail("Q1_SEMANTIC_PAYLOAD_INVALID", f"{label} must be non-empty")
    required = {
        "id",
        "scope",
        "checked_contract",
        "method",
        "evidence_ids",
        "conclusion",
        "result",
    }
    for item in value:
        if not isinstance(item, Mapping) or set(item) != required:
            _fail(
                "Q1_SEMANTIC_PAYLOAD_INVALID",
                f"{label} item fields differ from reviewCheck",
            )
        if (
            not all(
                isinstance(item[field], str) and item[field].strip()
                for field in (
                    "id",
                    "scope",
                    "checked_contract",
                    "method",
                    "conclusion",
                )
            )
            or not isinstance(item["evidence_ids"], list)
            or not item["evidence_ids"]
            or len(set(item["evidence_ids"])) != len(item["evidence_ids"])
            or any(
                not isinstance(evidence_id, str) or not evidence_id.strip()
                for evidence_id in item["evidence_ids"]
            )
            or item["result"] not in {"pass", "revise", "blocked"}
        ):
            _fail(
                "Q1_SEMANTIC_PAYLOAD_INVALID",
                f"{label} contains an empty or invalid review check",
            )


def _validate_semantic_payload(phase: str, body: Mapping[str, Any]) -> None:
    if set(body) != set(SEMANTIC_PHASE_FIELDS[phase]):
        _fail(
            "Q1_SEMANTIC_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(SEMANTIC_PHASE_FIELDS[phase])}",
        )
    if phase == "review-plan":
        plan = body["review_plan"]
        required = {
            "domain_scopes",
            "cross_domain_dimensions",
            "evidence_strategy",
            "challenge_strategy",
            "object_fingerprints",
        }
        if (
            not isinstance(plan, Mapping)
            or set(plan) != required
            or plan["domain_scopes"] != list(UPSTREAM_STAGES)
            or not isinstance(plan["cross_domain_dimensions"], list)
            or not plan["cross_domain_dimensions"]
            or not isinstance(plan["object_fingerprints"], list)
            or not plan["object_fingerprints"]
            or any(
                not isinstance(plan[field], str) or not plan[field].strip()
                for field in ("evidence_strategy", "challenge_strategy")
            )
        ):
            _fail("Q1_SEMANTIC_PAYLOAD_INVALID", "review plan is incomplete")
        return
    for field in _CHECK_FIELDS_BY_PHASE[phase]:
        _validate_review_checks(body[field], label=field)
    phase_checks = [
        item
        for field in _CHECK_FIELDS_BY_PHASE[phase]
        for item in body[field]
    ]
    conclusions = [
        " ".join(item["conclusion"].split()) for item in phase_checks
    ]
    if len(conclusions) != len(set(conclusions)):
        _fail(
            "Q1_GENERIC_SEMANTIC_EVIDENCE",
            f"{phase} reuses template conclusions",
        )
    if phase == "domain-challenges":
        scopes = [item["scope"] for item in body["domain_reviews"]]
        if scopes != list(UPSTREAM_STAGES):
            _fail(
                "Q1_SEMANTIC_PAYLOAD_INVALID",
                "domain_reviews must be ordered S1-W1-E1-T1-C1",
            )

def _verify_handoff_inputs(
    root: Path, allowlist: Sequence[Mapping[str, Any]]
) -> None:
    expected = {item["path"] for item in allowlist}
    actual = {
        path.relative_to(root).as_posix()
        for path in (root / "inputs").rglob("*")
        if path.is_file()
    }
    if actual != expected:
        _fail(
            "Q1_HANDOFF_ALLOWLIST_MISMATCH",
            f"physical input tree differs: {sorted(actual ^ expected)}",
        )
    for reference in allowlist:
        path = root / PurePosixPath(reference["path"])
        if (
            not path.is_file()
            or not isinstance(reference.get("sha256"), str)
            or _SHA256.fullmatch(reference["sha256"]) is None
            or _sha256_file(path) != reference["sha256"]
        ):
            _fail(
                "Q1_HANDOFF_ALLOWLIST_MISMATCH",
                str(reference.get("path")),
            )


def _validate_handoff_payload(
    payload: Mapping[str, Any],
    allowlist: Sequence[Mapping[str, Any]],
    *,
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> None:
    if set(payload) != {
        "development_usability_test",
        "read_set",
        "responses",
        "handoff_checks",
        "assertion_bindings",
    }:
        _fail(
            "Q1_HANDOFF_PAYLOAD_INVALID",
            "payload fields are not the sealed handoff contract",
        )
    read_set = payload["read_set"]
    allowed_paths = [item["path"] for item in allowlist]
    if (
        not isinstance(read_set, list)
        or len(read_set) != len(set(read_set))
        or set(read_set) != set(allowed_paths)
    ):
        _fail(
            "Q1_HANDOFF_READ_SET_INVALID",
            "read_set must equal the exact 12-file allowlist",
        )
    test = payload["development_usability_test"]
    if (
        not isinstance(test, Mapping)
        or set(test)
        != {"id", "tested_tasks", "evidence_ids", "conclusion", "result"}
        or not isinstance(test["tested_tasks"], list)
        or not test["tested_tasks"]
        or not isinstance(test["evidence_ids"], list)
        or not test["evidence_ids"]
        or test["result"] not in {"pass", "revise", "blocked"}
        or any(
            not isinstance(test[field], str) or not test[field].strip()
            for field in ("id", "conclusion")
        )
    ):
        _fail(
            "Q1_HANDOFF_PAYLOAD_INVALID",
            "development_usability_test is incomplete",
        )
    responses = payload["responses"]
    required = set(HANDOFF_TASKS)
    if (
        not isinstance(responses, Mapping)
        or set(responses) != required
        or any(
            not isinstance(responses[field], str)
            or not responses[field].strip()
            for field in required
        )
    ):
        _fail(
            "Q1_HANDOFF_PAYLOAD_INVALID",
            "all nine development handoff responses are required",
        )
    checks = payload["handoff_checks"]
    _validate_review_checks(checks, label="handoff_checks")
    if (
        [item["scope"] for item in checks] != list(HANDOFF_TASKS)
        or test["tested_tasks"] != list(HANDOFF_TASKS)
        or any(
            item["scope"] in QUALITY_TRACE_SCOPES
            and re.fullmatch(r"CHK-[A-Za-z0-9._-]+", item["id"])
            is None
            for item in checks
        )
        or any(item["result"] != test["result"] for item in checks)
        or set(test["evidence_ids"])
        != {
            evidence_id
            for item in checks
            for evidence_id in item["evidence_ids"]
        }
    ):
        _fail(
            "Q1_HANDOFF_PAYLOAD_INVALID",
            "handoff checks do not bind all nine tasks",
        )
    _validate_assertion_bindings(
        {
            "handoff_checks": checks,
            "assertion_bindings": payload["assertion_bindings"],
        },
        object_index=object_index,
        phase="handoff",
    )
    _validate_t1_lifecycle_handoff_coverage(
        payload, object_index=object_index
    )
    _validate_quality_trace_coverage(payload, object_index)


_OWNER_PREFIXES = {
    "SLD-": "S1",
    "SL-": "S1",
    "SLC-": "S1",
    "WR-": "W1",
    "WF-": "W1",
    "WS-": "W1",
    "END-": "E1",
    "ENV-": "E1",
    "ZONE-": "E1",
    "EVD-": "T1",
    "EV-": "T1",
    "LFS-": "T1",
    "LFC-": "T1",
    "CHD-": "C1",
    "SLOT-": "C1",
    "CHR-": "C1",
    "REL-": "C1",
    "DEV-": "C1",
}
_AUTHOR_OWNER_PREFIXES = {
    "INT-": "I0",
    "SUB-": "I1",
    "WLD-": "I2",
    "CHR-": "I3",
    "CAU-": "I4",
    "NAR-": "I5",
}
_OWNER_ORDER = ("I0", "I1", "I2", "I3", "I4", "I5", "S1", "W1", "E1", "T1", "C1", "Q1")
_OWNER_ISSUE_KIND = {
    "S1": "storyline",
    "W1": "world",
    "E1": "environment",
    "T1": "event_timeline",
    "C1": "character",
    "Q1": "semantic_review",
}


def _collect_ids(value: Any, output: set[str]) -> None:
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            output.add(identifier)
        for child in value.values():
            _collect_ids(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_ids(child, output)


_STAGE_KIND_PREFIXES = {
    "S1": {
        "SLD-": "storyline-demand",
        "SLC-": "storyline-connection",
        "SL-": "storyline",
    },
    "W1": {
        "WR-": "world-requirement",
        "WF-": "world-fact",
        "WS-": "world-system",
    },
    "E1": {
        "END-": "environment-demand",
        "ENV-": "environment",
        "ZONE-": "environment-zone",
    },
    "T1": {
        "EVD-": "event-demand",
        "EV-": "event",
        "LFS-": "lifecycle-scope",
        "LFC-": "lifecycle-contract",
    },
    "C1": {
        "CHD-": "character-demand",
        "SLOT-": "character-slot",
        "CHR-": "character",
        "REL-": "relationship",
        "DEV-": "development-freedom",
    },
}


def _object_kind(stage: str, identifier: str) -> str:
    if stage == "B0":
        return "author-control"
    for prefix, kind in _STAGE_KIND_PREFIXES[stage].items():
        if identifier.startswith(prefix):
            return kind
    return "governance"


_T1_EVENT_PROJECTION_MAP = {
    "kind": "event_kind",
    "milestone_id": "milestone_id",
    "world_time_slot": "world_time",
    "storyline_ids": "storyline_ids",
    "environment_id": "environment_id",
    "affordance_ids": "affordance_ids",
    "initiating_action": "initiating_action",
    "e1_capability_step_ids": "e1_capability_step_ids",
    "capability_step_occurrences": "capability_step_occurrences",
    "requires_capability_fact_ids": "requires_capability_fact_ids",
    "produces_capability_fact_ids": "produces_capability_fact_ids",
    "requires_token_instance_ids": "requires_token_instance_ids",
    "produces_token_instance_ids": "produces_token_instance_ids",
    "requires_proposition_ids": "requires_proposition_ids",
    "produces_proposition_ids": "produces_proposition_ids",
    "discloses_proposition_ids": "discloses_proposition_ids",
    "initial_anchor_refs": "initial_anchor_refs",
    "predecessor_event_ids": "predecessor_event_ids",
    "preconditions": "preconditions",
    "direct_result": "direct_result",
    "next_pressure": "next_pressure",
    "source_ids": "source_ids",
    "atomicity_reason": "atomicity_reason",
}
_T1_EVENT_PROJECTION_MAP_25 = {
    "consumes_token_instance_ids": "consumes_token_instance_ids",
    "lifecycle_effects": "lifecycle_effects",
}
_T1_PROPOSITION_PROJECTION_FIELDS = (
    "id",
    "statement",
    "source_ids",
    "audience",
    "initially_true",
    "terminality",
    "initial_anchor_refs",
    "producer_event_ids",
)
_T1_PROJECTION_PAIRS = (
    ("planned_event_registry", "major_events", "event"),
    ("planned_proposition_registry", "proposition_registry", "proposition"),
    ("planned_causal_edges", "causal_edges", "causal-edge"),
)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _child_pointer(pointer: str, token: str | int) -> str:
    return f"{pointer}/{_pointer_token(str(token))}"


def _record_for_object(
    *,
    stage: str,
    identifier: str,
    value: Mapping[str, Any],
    source_pointer: str,
    projection_source_pointer: str | None = None,
) -> dict[str, Any]:
    record = {
        "id": identifier,
        "stage": stage,
        "kind": _object_kind(stage, identifier),
        "value": copy.deepcopy(dict(value)),
        "value_sha256": _canonical_sha256(value),
        "source_pointer": source_pointer,
        "source_pointers": [source_pointer],
    }
    if projection_source_pointer is not None:
        record["projection_source_pointer"] = projection_source_pointer
        record["source_pointers"].append(projection_source_pointer)
    return record


def _merge_exact_duplicate(
    output: dict[tuple[str, str], dict[str, Any]],
    *,
    stage: str,
    identifier: str,
    value: Mapping[str, Any],
    source_pointer: str,
    protected_projection_keys: set[tuple[str, str]],
) -> None:
    key = (stage, identifier)
    existing = output.get(key)
    if existing is None:
        output[key] = _record_for_object(
            stage=stage,
            identifier=identifier,
            value=value,
            source_pointer=source_pointer,
        )
        return
    if key in protected_projection_keys:
        _fail(
            "Q1_STORY_OBJECT_AMBIGUOUS",
            f"{stage}:{identifier} has a third projection source",
        )
    value_sha256 = _canonical_sha256(value)
    if existing["value_sha256"] != value_sha256:
        _fail("Q1_STORY_OBJECT_AMBIGUOUS", f"{stage}:{identifier}")
    existing["source_pointers"].append(source_pointer)


def _index_objects(
    value: Any,
    *,
    stage: str,
    output: dict[tuple[str, str], dict[str, Any]],
    pointer: str = "",
    excluded_top_level_fields: set[str] | None = None,
    protected_projection_keys: set[tuple[str, str]] | None = None,
) -> None:
    protected_projection_keys = protected_projection_keys or set()
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            _merge_exact_duplicate(
                output,
                stage=stage,
                identifier=identifier,
                value=value,
                source_pointer=pointer,
                protected_projection_keys=protected_projection_keys,
            )
        for token, child in value.items():
            if pointer == "" and excluded_top_level_fields and token in excluded_top_level_fields:
                continue
            _index_objects(
                child,
                stage=stage,
                output=output,
                pointer=_child_pointer(pointer, token),
                protected_projection_keys=protected_projection_keys,
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _index_objects(
                child,
                stage=stage,
                output=output,
                pointer=_child_pointer(pointer, index),
                protected_projection_keys=protected_projection_keys,
            )


def _registry_by_id(
    model: Mapping[str, Any], field: str
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    values = model.get(field)
    if not isinstance(values, list):
        _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1.{field} missing")
    records: dict[str, Mapping[str, Any]] = {}
    pointers: dict[str, str] = {}
    for index, value in enumerate(values):
        if not isinstance(value, Mapping) or not isinstance(value.get("id"), str):
            _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1.{field}[{index}]")
        identifier = value["id"]
        if identifier in records:
            _fail("Q1_STORY_OBJECT_AMBIGUOUS", f"T1:{identifier}")
        records[identifier] = value
        pointers[identifier] = f"/{field}/{index}"
    return records, pointers


def _validate_t1_event_projection(
    identifier: str,
    planned: Mapping[str, Any],
    canonical: Mapping[str, Any],
    *,
    schema_version: Any,
) -> None:
    projection_map = dict(_T1_EVENT_PROJECTION_MAP)
    if schema_version == "2.5":
        projection_map.update(_T1_EVENT_PROJECTION_MAP_25)
    for source_field, target_field in projection_map.items():
        if source_field not in planned or planned[source_field] != canonical.get(target_field):
            _fail(
                "Q1_STORY_OBJECT_PROJECTION_INVALID",
                f"T1:{identifier}.{source_field}",
            )
    changed = planned.get("changed_subject")
    if not isinstance(changed, Mapping):
        _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1:{identifier}.changed_subject")
    subject_id = changed.get("subject_id")
    if (
        not isinstance(subject_id, str)
        or canonical.get("subject_id") != subject_id
        or canonical.get("subject_kind") != changed.get("subject_kind")
        or canonical.get("before_state") != {subject_id: changed.get("before")}
        or canonical.get("after_state") != {subject_id: changed.get("after")}
    ):
        _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1:{identifier}.changed_subject")


def _index_t1_projection_pairs(
    model: Mapping[str, Any],
    output: dict[tuple[str, str], dict[str, Any]],
) -> set[tuple[str, str]]:
    protected: set[tuple[str, str]] = set()
    for planned_field, canonical_field, pair_kind in _T1_PROJECTION_PAIRS:
        planned, planned_pointers = _registry_by_id(model, planned_field)
        canonical, canonical_pointers = _registry_by_id(model, canonical_field)
        if set(planned) != set(canonical):
            _fail(
                "Q1_STORY_OBJECT_PROJECTION_INVALID",
                f"T1.{planned_field}/{canonical_field} ID sets differ",
            )
        for identifier in sorted(canonical):
            source = planned[identifier]
            target = canonical[identifier]
            if pair_kind == "event":
                _validate_t1_event_projection(
                    identifier,
                    source,
                    target,
                    schema_version=model.get("schema_version"),
                )
            elif pair_kind == "proposition":
                try:
                    source_projection = {
                        field: source[field]
                        for field in _T1_PROPOSITION_PROJECTION_FIELDS
                    }
                    target_projection = {
                        field: target[field]
                        for field in _T1_PROPOSITION_PROJECTION_FIELDS
                    }
                except KeyError as error:
                    _fail(
                        "Q1_STORY_OBJECT_PROJECTION_INVALID",
                        f"T1:{identifier}.{error.args[0]}",
                    )
                if source_projection != target_projection:
                    _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1:{identifier}")
            elif source != target:
                _fail("Q1_STORY_OBJECT_PROJECTION_INVALID", f"T1:{identifier}")
            key = ("T1", identifier)
            if key in protected or key in output:
                _fail("Q1_STORY_OBJECT_AMBIGUOUS", f"T1:{identifier}")
            output[key] = _record_for_object(
                stage="T1",
                identifier=identifier,
                value=target,
                source_pointer=canonical_pointers[identifier],
                projection_source_pointer=planned_pointers[identifier],
            )
            protected.add(key)
    return protected


def _index_stage_model(
    model: Mapping[str, Any],
    *,
    stage: str,
    output: dict[tuple[str, str], dict[str, Any]],
) -> None:
    excluded: set[str] = set()
    protected: set[tuple[str, str]] = set()
    if stage == "T1" and model.get("schema_version") in {"2.2", "2.3", "2.4", "2.5"}:
        protected = _index_t1_projection_pairs(model, output)
        excluded = {
            field
            for pair in _T1_PROJECTION_PAIRS
            for field in pair[:2]
        }
    _index_objects(
        model,
        stage=stage,
        output=output,
        excluded_top_level_fields=excluded,
        protected_projection_keys=protected,
    )


def _story_object_index(
    frozen: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    roots = frozen.get("package_roots")
    if not isinstance(roots, Mapping):
        _fail("Q1_FROZEN_INPUTS_INVALID", "package roots missing")
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for stage, canonical in STAGE_CANONICAL.items():
        model = _read(
            Path(roots[stage]) / canonical,
            "Q1_FROZEN_INPUTS_STALE",
        )
        _index_stage_model(model, stage=stage, output=output)
    return output


def _handoff_object_index(
    root: Path,
) -> dict[tuple[str, str], dict[str, Any]]:
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for stage, canonical in STAGE_CANONICAL.items():
        model = _read(
            root / "inputs" / stage / canonical,
            "Q1_HANDOFF_ALLOWLIST_MISMATCH",
        )
        _index_stage_model(model, stage=stage, output=output)
    return output


def _quality_targets(
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Return the complete, deterministic Q1 coverage universe.

    S1 owns obligations and T1 owns their event/timeline realizations.  Every
    ID-bearing canonical object in those stages is therefore reviewable; the
    definition deliberately follows the schemas instead of story-specific ID
    names.
    """

    targets = []
    for (stage, identifier), record in object_index.items():
        if stage not in {"S1", "T1"}:
            continue
        targets.append(
            {
                "stage": stage,
                "id": identifier,
                "classification": (
                    "s1_obligation" if stage == "S1" else "t1_realization"
                ),
                "value_sha256": record["value_sha256"],
            }
        )
    return sorted(
        targets,
        key=lambda item: (
            0 if item["stage"] == "S1" else 1,
            item["id"],
        ),
    )


def _t1_lifecycle_review_keys(
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> set[tuple[str, str]]:
    lifecycle_keys = {
        key
        for key, record in object_index.items()
        if key[0] == "T1"
        and record.get("kind") in {"lifecycle-scope", "lifecycle-contract"}
    }
    source_ids: set[str] = set()
    for key in lifecycle_keys:
        value = object_index[key]["value"]
        source_ids.update(value.get("source_ids", []))
    source_keys = {
        key for key in object_index if key[1] in source_ids
    }
    return lifecycle_keys | source_keys


def _validate_t1_lifecycle_review_coverage(
    body: Mapping[str, Any],
    *,
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
    phase: str,
) -> None:
    required_keys = _t1_lifecycle_review_keys(object_index)
    if not required_keys:
        return
    if phase == "review-plan":
        if T1_LIFECYCLE_CLOSURE_SCOPE not in body["review_plan"][
            "cross_domain_dimensions"
        ]:
            _fail(
                "Q1_T1_LIFECYCLE_REVIEW_MISSING",
                "review plan omits typed lifecycle causal closure",
            )
        return
    if phase == "domain-challenges":
        t1_review = next(
            item for item in body["domain_reviews"] if item["scope"] == "T1"
        )
        if t1_review["checked_contract"] != T1_LIFECYCLE_REVIEW_CONTRACT:
            _fail(
                "Q1_T1_LIFECYCLE_REVIEW_MISSING",
                "T1 domain review does not bind the 2.5 lifecycle contract",
            )
        return
    if phase == "cross-domain-challenges":
        checks = [
            item
            for item in body["cross_domain_checks"]
            if item["scope"] == T1_LIFECYCLE_CLOSURE_SCOPE
        ]
        if len(checks) != 1:
            _fail(
                "Q1_T1_LIFECYCLE_REVIEW_MISSING",
                "one typed lifecycle cross-domain check is required",
            )
        binding = next(
            item
            for item in body["assertion_bindings"]
            if item["check_id"] == checks[0]["id"]
        )
        observed = {
            (item["stage"], item["id"])
            for item in binding["evidence_objects"]
        }
        if not required_keys.issubset(observed):
            _fail(
                "Q1_T1_LIFECYCLE_REVIEW_INCOMPLETE",
                "typed lifecycle source and realization objects are incomplete",
            )


def _validate_t1_lifecycle_handoff_coverage(
    payload: Mapping[str, Any],
    *,
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> None:
    required_keys = _t1_lifecycle_review_keys(object_index)
    if not required_keys:
        return
    for scope in ("chronology_reconstruction", "causal_precondition_trace"):
        check_id = next(
            item["id"]
            for item in payload["handoff_checks"]
            if item["scope"] == scope
        )
        binding = next(
            item
            for item in payload["assertion_bindings"]
            if item["check_id"] == check_id
        )
        observed = {
            (item["stage"], item["id"])
            for item in binding["evidence_objects"]
        }
        if not required_keys.issubset(observed):
            _fail(
                "Q1_T1_LIFECYCLE_HANDOFF_INCOMPLETE",
                scope,
            )


def _quality_coverage_records(
    payload: Mapping[str, Any],
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    required = {
        (item["stage"], item["id"]): item
        for item in _quality_targets(object_index)
    }
    check_ids_by_target: dict[tuple[str, str], set[str]] = {
        key: set() for key in required
    }
    for binding in payload.get("assertion_bindings", []):
        if binding.get("scope") not in QUALITY_TRACE_SCOPES:
            continue
        for evidence in binding.get("evidence_objects", []):
            key = (evidence.get("stage"), evidence.get("id"))
            if key in check_ids_by_target:
                check_ids_by_target[key].add(binding["check_id"])
    missing = [
        f"{stage}:{identifier}"
        for (stage, identifier), check_ids in check_ids_by_target.items()
        if not check_ids
    ]
    if missing:
        _fail(
            "Q1_QUALITY_COVERAGE_INCOMPLETE",
            "trace tasks missed " + ", ".join(sorted(missing)),
        )
    records = []
    for target in _quality_targets(object_index):
        key = (target["stage"], target["id"])
        records.append(
            {
                **target,
                "handoff_check_ids": sorted(check_ids_by_target[key]),
            }
        )
    return records


def _validate_quality_trace_coverage(
    payload: Mapping[str, Any],
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> None:
    _quality_coverage_records(payload, object_index)


def _quality_coverage_certificate(
    *,
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
    handoff_payload: Mapping[str, Any],
    semantic_payloads: Sequence[Mapping[str, Any]],
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    required = _quality_targets(object_index)
    covered = _quality_coverage_records(handoff_payload, object_index)
    unresolved: set[str] = set()
    for payload in [*semantic_payloads, handoff_payload]:
        for field in (
            "domain_reviews",
            "reality_claim_review",
            "coverage_recalculation",
            "causal_challenges",
            "easy_solution_challenges",
            "cross_domain_checks",
            "consistency_matrix",
            "handoff_checks",
        ):
            for check in payload.get(field, []):
                if check.get("result") != "pass":
                    unresolved.add(str(check.get("id")))
        usability = payload.get("development_usability_test")
        if isinstance(usability, Mapping) and usability.get("result") != "pass":
            unresolved.add(str(usability.get("id")))
    for finding in findings:
        if finding.get("severity") in {"contradictory", "revise", "blocked"}:
            unresolved.add(str(finding.get("id")))
    return {
        "coverage_basis": QUALITY_COVERAGE_BASIS,
        "required_objects": required,
        "covered_objects": covered,
        "unresolved_blocking_quality_record_ids": sorted(unresolved),
        "result": "complete" if not unresolved else "incomplete",
    }


def _validate_packaged_quality_coverage(
    review: Mapping[str, Any], handoff_payload: Mapping[str, Any]
) -> None:
    certificate = review.get("quality_coverage")
    if not isinstance(certificate, Mapping):
        _fail("Q1_QUALITY_COVERAGE_INVALID", "certificate missing")
    required = certificate.get("required_objects", [])
    covered = certificate.get("covered_objects", [])
    required_keys = {
        (item.get("stage"), item.get("id"), item.get("value_sha256"))
        for item in required
        if isinstance(item, Mapping)
    }
    covered_keys = {
        (item.get("stage"), item.get("id"), item.get("value_sha256"))
        for item in covered
        if isinstance(item, Mapping)
    }
    if (
        len(required_keys) != len(required)
        or len(covered_keys) != len(covered)
        or required_keys != covered_keys
    ):
        _fail(
            "Q1_QUALITY_COVERAGE_INCOMPLETE",
            "required and covered quality objects differ",
        )
    trace_bindings = {
        binding.get("check_id"): binding
        for binding in handoff_payload.get("assertion_bindings", [])
        if isinstance(binding, Mapping)
        and binding.get("scope") in QUALITY_TRACE_SCOPES
    }
    for item in covered:
        check_ids = item.get("handoff_check_ids", [])
        key = (item.get("stage"), item.get("id"), item.get("value_sha256"))
        if not check_ids or any(check_id not in trace_bindings for check_id in check_ids):
            _fail("Q1_QUALITY_COVERAGE_INVALID", str(key))
        if not any(
            any(
                evidence.get("stage") == key[0]
                and evidence.get("id") == key[1]
                and evidence.get("value_sha256") == key[2]
                for evidence in trace_bindings[check_id].get(
                    "evidence_objects", []
                )
            )
            for check_id in check_ids
        ):
            _fail("Q1_QUALITY_COVERAGE_INVALID", str(key))
    unresolved = {
        item.get("id")
        for field in (
            "domain_reviews",
            "reality_claim_review",
            "coverage_recalculation",
            "causal_challenges",
            "easy_solution_challenges",
            "cross_domain_checks",
            "consistency_matrix",
        )
        for item in review.get(field, [])
        if isinstance(item, Mapping) and item.get("result") != "pass"
    }
    unresolved.update(
        item.get("id")
        for item in handoff_payload.get("handoff_checks", [])
        if isinstance(item, Mapping) and item.get("result") != "pass"
    )
    if review.get("development_usability_test", {}).get("result") != "pass":
        unresolved.add(review.get("development_usability_test", {}).get("id"))
    unresolved.update(
        item.get("id")
        for item in review.get("findings", [])
        if isinstance(item, Mapping)
        and item.get("severity") in {"contradictory", "revise", "blocked"}
    )
    unresolved.discard(None)
    if sorted(unresolved) != certificate.get(
        "unresolved_blocking_quality_record_ids"
    ):
        _fail("Q1_QUALITY_COVERAGE_INVALID", "unresolved record drift")
    expected_result = "complete" if not unresolved else "incomplete"
    if certificate.get("result") != expected_result:
        _fail("Q1_QUALITY_COVERAGE_INVALID", "result drift")


def _pointer_value(value: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        _fail("Q1_ASSERTION_BINDING_INVALID", f"pointer {pointer!r}")
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            if index >= len(current):
                _fail("Q1_ASSERTION_BINDING_INVALID", pointer)
            current = current[index]
        else:
            _fail("Q1_ASSERTION_BINDING_INVALID", pointer)
    return current


def _contains_id(value: Any, identifier: str) -> bool:
    if value == identifier:
        return True
    if isinstance(value, Mapping):
        return any(_contains_id(child, identifier) for child in value.values())
    if isinstance(value, list):
        return any(_contains_id(child, identifier) for child in value)
    return False


def _projected_story_strings(
    value: Any, *, selected_ids: set[str]
) -> list[str]:
    output: list[str] = []
    if isinstance(value, str):
        normalized = " ".join(value.split())
        if (
            len(normalized) >= 3
            and normalized not in selected_ids
            and not normalized.startswith(("CHK-", "HANDOFF-"))
        ):
            output.append(normalized)
    elif isinstance(value, Mapping):
        for child in value.values():
            output.extend(
                _projected_story_strings(
                    child, selected_ids=selected_ids
                )
            )
    elif isinstance(value, list):
        for child in value:
            output.extend(
                _projected_story_strings(
                    child, selected_ids=selected_ids
                )
            )
    return output


def _validate_plan_fingerprints(
    plan: Mapping[str, Any],
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> None:
    fingerprints = plan.get("object_fingerprints")
    if not isinstance(fingerprints, list) or not fingerprints:
        _fail(
            "Q1_REVIEW_PLAN_BINDING_INVALID",
            "object_fingerprints are required",
        )
    seen_objects: set[tuple[str, str]] = set()
    seen_stages: set[str] = set()
    for item in fingerprints:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"id", "stage", "value_sha256"}
        ):
            _fail(
                "Q1_REVIEW_PLAN_BINDING_INVALID",
                "fingerprint shape",
            )
        key = (item["stage"], item["id"])
        record = object_index.get(key)
        if (
            record is None
            or key in seen_objects
            or item["stage"] != record["stage"]
            or item["value_sha256"] != record["value_sha256"]
        ):
            _fail(
                "Q1_REVIEW_PLAN_BINDING_INVALID",
                str(item.get("id")),
            )
        seen_objects.add(key)
        seen_stages.add(record["stage"])
    if seen_stages != set(STAGE_CANONICAL):
        _fail(
            "Q1_REVIEW_PLAN_BINDING_INVALID",
            "Agent must select at least one current object from B0/S1-C1",
        )
    required_quality_objects = {
        (item["stage"], item["id"])
        for item in _quality_targets(object_index)
    }
    if not required_quality_objects <= seen_objects:
        missing = sorted(required_quality_objects - seen_objects)
        _fail(
            "Q1_REVIEW_PLAN_BINDING_INVALID",
            "review plan omits S1/T1 quality objects: "
            + ", ".join(f"{stage}:{identifier}" for stage, identifier in missing),
        )


def _binding_policy(
    field: str, check: Mapping[str, Any]
) -> dict[str, Any]:
    if field == "domain_reviews":
        stage = check["scope"]
        if stage not in UPSTREAM_STAGES:
            _fail("Q1_ASSERTION_BINDING_INVALID", "domain scope")
        return {
            "stages": {stage},
            "predicate": "domain-contract",
            "operator": "challenge-domain",
            "cross_stage": False,
            "target_required": False,
        }
    if field == "handoff_checks":
        policies = {
            "story_subject": {
                "stages": {"B0", "S1"},
                "predicate": "story-subject",
                "operator": "reconstruct-subject",
                "cross_stage": False,
                "target_required": False,
            },
            "storyline_trace": {
                "stages": {"S1", "T1"},
                "predicate": "storyline-event-trace",
                "operator": "trace-development",
                "cross_stage": True,
                "target_required": True,
            },
            "event_conditions": {
                "stages": {"W1", "E1", "T1"},
                "predicate": "event-condition",
                "operator": "locate-preconditions",
                "cross_stage": True,
                "target_required": True,
            },
            "character_choices": {
                "stages": {"T1", "C1"},
                "predicate": "character-choice",
                "operator": "explain-choice",
                "cross_stage": True,
                "target_required": True,
            },
            "development_freedoms": {
                "stages": set(STAGE_CANONICAL),
                "predicate": "development-boundary",
                "operator": "locate-freedom",
                "cross_stage": False,
                "target_required": False,
            },
            "chronology_reconstruction": {
                # T1 2.5 lifecycle scopes/contracts explicitly cite both
                # storyline obligations and E1 capability facts.  Chronology
                # reconstruction must therefore admit the E1 preconditions it
                # is required to cover, while remaining closed to W1/C1.
                "stages": {"S1", "E1", "T1"},
                "predicate": "chronology-reconstruction",
                "operator": "reconstruct-chronology",
                "cross_stage": True,
                "target_required": True,
            },
            "causal_precondition_trace": {
                "stages": {"S1", "E1", "T1"},
                "predicate": "causal-precondition",
                "operator": "trace-preconditions",
                "cross_stage": True,
                "target_required": True,
            },
            "information_release_trace": {
                "stages": {"S1", "T1"},
                "predicate": "information-release",
                "operator": "trace-information-release",
                "cross_stage": True,
                "target_required": True,
            },
            "author_control_trace": {
                "stages": {"B0", "S1", "T1"},
                "predicate": "author-control",
                "operator": "trace-author-control",
                "cross_stage": True,
                "target_required": True,
            },
        }
        policy = policies.get(check["scope"])
        if policy is None:
            _fail("Q1_ASSERTION_BINDING_INVALID", "handoff scope")
        return policy
    policies = {
        "reality_claim_review": {
            "stages": {"B0", "W1", "E1", "T1"},
            "predicate": "reality-claim",
            "operator": "verify-reality",
            "cross_stage": False,
            "target_required": False,
        },
        "coverage_recalculation": {
            "stages": set(STAGE_CANONICAL),
            "predicate": "covers",
            "operator": "recompute-coverage",
            "cross_stage": False,
            "target_required": True,
        },
        "causal_challenges": {
            "stages": {"S1", "W1", "E1", "T1", "C1"},
            "predicate": "causal-dependency",
            "operator": "break-cause",
            "cross_stage": False,
            "target_required": True,
        },
        "easy_solution_challenges": {
            "stages": {"S1", "W1", "E1", "T1", "C1"},
            "predicate": "counterfactual-pressure",
            "operator": "remove-convenience",
            "cross_stage": False,
            "target_required": True,
        },
        "cross_domain_checks": {
            "stages": {"S1", "W1", "E1", "T1", "C1"},
            "predicate": "cross-domain-reference",
            "operator": "compare-domains",
            "cross_stage": True,
            "target_required": True,
        },
        "consistency_matrix": {
            "stages": {"S1", "W1", "E1", "T1", "C1"},
            "predicate": "consistent-with",
            "operator": "compare-semantics",
            "cross_stage": True,
            "target_required": True,
        },
    }
    return policies[field]


def _validate_assertion_bindings(
    body: Mapping[str, Any],
    *,
    object_index: Mapping[tuple[str, str], Mapping[str, Any]],
    phase: str,
) -> None:
    bindings = body.get("assertion_bindings")
    if not isinstance(bindings, list):
        _fail("Q1_ASSERTION_BINDING_INVALID", "bindings are required")
    checks_by_id: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for field in _CHECK_FIELDS_BY_PHASE[phase]:
        for check in body[field]:
            if check["id"] in checks_by_id:
                _fail("Q1_ASSERTION_BINDING_INVALID", check["id"])
            checks_by_id[check["id"]] = (field, check)
    if len(bindings) != len(checks_by_id):
        _fail(
            "Q1_ASSERTION_BINDING_INVALID",
            "exactly one binding per review check is required",
        )
    seen: set[str] = set()
    for binding in bindings:
        if (
            not isinstance(binding, Mapping)
            or set(binding)
            != {
                "check_id",
                "scope",
                "evidence_objects",
                "assertion",
                "assertion_sha256",
            }
        ):
            _fail("Q1_ASSERTION_BINDING_INVALID", "binding shape")
        check_id = binding["check_id"]
        if check_id in seen or check_id not in checks_by_id:
            _fail("Q1_ASSERTION_BINDING_INVALID", str(check_id))
        seen.add(check_id)
        field, check = checks_by_id[check_id]
        policy = _binding_policy(field, check)
        evidence_objects = binding["evidence_objects"]
        if not isinstance(evidence_objects, list) or not evidence_objects:
            _fail("Q1_ASSERTION_BINDING_INVALID", f"{check_id} evidence")
        selected: dict[str, Mapping[str, Any]] = {}
        projected_values: list[Any] = []
        for selected_object in evidence_objects:
            if (
                not isinstance(selected_object, Mapping)
                or set(selected_object)
                != {
                    "id",
                    "stage",
                    "kind",
                    "value_sha256",
                    "projections",
                }
            ):
                _fail("Q1_ASSERTION_BINDING_INVALID", f"{check_id} object")
            identifier = selected_object["id"]
            current = object_index.get(
                (selected_object["stage"], identifier)
            )
            if (
                current is None
                or identifier in selected
                or current["stage"] not in policy["stages"]
                or selected_object["stage"] != current["stage"]
                or selected_object["kind"] != current["kind"]
                or selected_object["value_sha256"]
                != current["value_sha256"]
            ):
                _fail("Q1_ASSERTION_BINDING_INVALID", str(identifier))
            projections = selected_object["projections"]
            if not isinstance(projections, list) or not projections:
                _fail(
                    "Q1_ASSERTION_BINDING_INVALID",
                    f"{identifier} projections",
                )
            paths: set[str] = set()
            for projection in projections:
                if (
                    not isinstance(projection, Mapping)
                    or set(projection) != {"path", "value_sha256"}
                    or projection["path"] in paths
                    or projection["path"].endswith("/id")
                ):
                    _fail(
                        "Q1_ASSERTION_BINDING_INVALID",
                        f"{identifier} projection shape",
                    )
                value = _pointer_value(
                    current["value"], projection["path"]
                )
                if projection["value_sha256"] != _canonical_sha256(value):
                    _fail(
                        "Q1_ASSERTION_BINDING_INVALID",
                        f"{identifier}{projection['path']}",
                    )
                paths.add(projection["path"])
                projected_values.append(value)
            selected[identifier] = current
        if list(selected) != check["evidence_ids"]:
            _fail(
                "Q1_ASSERTION_BINDING_INVALID",
                f"{check_id} evidence IDs differ",
            )
        assertion = binding["assertion"]
        if (
            not isinstance(assertion, Mapping)
            or set(assertion)
            != {
                "predicate",
                "subject_id",
                "target_id",
                "challenge_operator",
                "result",
            }
            or assertion["predicate"] != policy["predicate"]
            or assertion["challenge_operator"] != policy["operator"]
            or assertion["result"] != check["result"]
            or assertion["subject_id"] not in selected
            or (
                assertion["target_id"] is not None
                and assertion["target_id"] not in selected
            )
            or (
                policy["target_required"]
                and assertion["target_id"] is None
            )
        ):
            _fail("Q1_ASSERTION_BINDING_INVALID", f"{check_id} assertion")
        if policy["cross_stage"] and len(
            {record["stage"] for record in selected.values()}
        ) < 2:
            _fail(
                "Q1_ASSERTION_BINDING_INVALID",
                f"{check_id} is not cross-domain",
            )
        target_id = assertion["target_id"]
        if target_id is not None and not any(
            _contains_id(value, target_id) for value in projected_values
        ):
            _fail(
                "Q1_ASSERTION_BINDING_INVALID",
                f"{check_id} target is absent from projected relation",
            )
        story_strings = [
            story_string
            for projected_value in projected_values
            for story_string in _projected_story_strings(
                projected_value, selected_ids=set(selected)
            )
        ]
        conclusion = " ".join(check["conclusion"].split())
        if not story_strings or not any(
            story_string in conclusion for story_string in story_strings
        ):
            _fail(
                "Q1_GENERIC_SEMANTIC_EVIDENCE",
                f"{check_id} conclusion is not bound to projected story values",
            )
        unsigned = {
            key: copy.deepcopy(value)
            for key, value in binding.items()
            if key != "assertion_sha256"
        }
        expected_sha = _canonical_sha256(unsigned)
        if (
            binding["assertion_sha256"] != expected_sha
            or binding["scope"] != check["scope"]
            or check["method"] != f"story-assertion:{expected_sha}"
        ):
            _fail(
                "Q1_ASSERTION_BINDING_INVALID",
                f"{check_id} reviewCheck binding",
            )


def _known_story_ids(frozen: Mapping[str, Any]) -> set[str]:
    return {
        record["id"] for record in _story_object_index(frozen).values()
    }


def _author_control_ids(frozen: Mapping[str, Any]) -> set[str]:
    roots = frozen.get("package_roots")
    baseline = _read(
        Path(roots["B0"]) / STAGE_CANONICAL["B0"],
        "Q1_FROZEN_INPUTS_STALE",
    )
    registry = baseline.get("control_registry")
    if not isinstance(registry, list):
        _fail("Q1_FROZEN_INPUTS_STALE", "B0 control registry missing")
    return {
        item["id"]
        for item in registry
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


def _owner_for_finding(
    finding: Mapping[str, Any], *, author_ids: set[str]
) -> tuple[str, str]:
    affected = finding.get("affected_ids", [])
    ids = affected if affected else finding.get("evidence_ids", [])
    owners: set[str] = set()
    for identifier in ids:
        if not isinstance(identifier, str):
            continue
        if identifier in author_ids:
            for prefix, owner in _AUTHOR_OWNER_PREFIXES.items():
                if identifier.startswith(prefix):
                    owners.add(owner)
                    break
            continue
        for prefix, owner in _OWNER_PREFIXES.items():
            if identifier.startswith(prefix):
                owners.add(owner)
                break
    if not owners:
        _fail(
            "Q1_FINDING_OWNER_INVALID",
            f"{finding.get('id')} has no routable story object",
        )
    owner = min(owners, key=_OWNER_ORDER.index)
    resume_point = "B0" if owner.startswith("I") else owner
    return owner, resume_point


def _phase_payload(semantic: Path, index: int, phase: str) -> dict[str, Any]:
    evidence = _read(
        semantic / "generation-evidence" / f"{index:02d}-{phase}.json",
        "Q1_SEMANTIC_EVIDENCE_INVALID",
    )
    payload = evidence.get("payload")
    if not isinstance(payload, dict):
        _fail("Q1_SEMANTIC_EVIDENCE_INVALID", phase)
    if evidence.get("payload_sha256") != _canonical_sha256(payload):
        _fail("Q1_SEMANTIC_EVIDENCE_INVALID", f"{phase} payload hash")
    return payload


def _implementation_paths() -> dict[str, Path]:
    runtime_root = (
        _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    )
    values = {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/references/isolation-protocol.md": (
            _SKILL / "references" / "isolation-protocol.md"
        ),
    }
    for name in (
        "canonical.py",
        "contracts.py",
        "coordinator.py",
        "return_routing.py",
        "stage_implementation_identity.py",
    ):
        values[f"runtime/{name}"] = runtime_root / name
    for name in (
        "conception-review.schema.json",
        "return-request.schema.json",
        "input-gate.schema.json",
        "package-manifest.schema.json",
        "stage-completion.schema.json",
        "canonical-common.schema.json",
        "common-defs.schema.json",
    ):
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


_IMPLEMENTATION_IDENTITY_ALGORITHM = "q1-implementation-catalog-v1"


def _implementation_identity() -> dict[str, Any]:
    catalog: list[dict[str, str]] = []
    repository = _REPO.resolve()
    for identity, source in sorted(_implementation_paths().items()):
        resolved = source.resolve()
        try:
            source_path = resolved.relative_to(repository).as_posix()
        except ValueError:
            _fail("Q1_IMPLEMENTATION_INVALID", f"path escapes repository: {source}")
        if not resolved.is_file():
            _fail("Q1_IMPLEMENTATION_INVALID", f"missing: {source_path}")
        catalog.append(
            {
                "identity": identity,
                "source_path": source_path,
                "sha256": _sha256_file(resolved),
            }
        )
    return {
        "algorithm": _IMPLEMENTATION_IDENTITY_ALGORITHM,
        "catalog": catalog,
        "canonical_digest": _canonical_sha256(catalog),
    }


def _validate_implementation_identity(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"algorithm", "catalog", "canonical_digest"}
        or value.get("algorithm") != _IMPLEMENTATION_IDENTITY_ALGORITHM
        or not isinstance(value.get("catalog"), list)
        or value.get("canonical_digest")
        != _canonical_sha256(value.get("catalog"))
    ):
        _fail("Q1_IMPLEMENTATION_STALE", "sealed identity is malformed")
    current = _implementation_identity()
    if dict(value) != current:
        _fail("Q1_IMPLEMENTATION_STALE", "current implementation differs")
    return current


def _validate_controller_implementation(
    controller: Path, state: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    frozen = _read(
        controller / "frozen-inputs.json", "Q1_FROZEN_INPUTS_INVALID"
    )
    sealed = frozen.get("implementation_identity")
    current = _validate_implementation_identity(sealed)
    active = dict(state) if state is not None else _latest_state(controller)
    if active.get("implementation_identity") != sealed:
        _fail(
            "Q1_IMPLEMENTATION_STALE",
            "controller state does not bind frozen implementation",
        )
    return current


def _validation_record(run_id: str, verdict: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "Q1",
        "verdict": verdict,
        "checks": [
            "input-gate-and-upstream-revalidation",
            "dual-task-identity-isolation",
            "semantic-phase-forward-hash-chain",
            "exact-handoff-allowlist-and-read-set",
            "sealed-one-way-handoff-import",
            "review-schema-and-story-evidence",
            "full-s1-t1-quality-coverage-and-trace-tasks",
            "finding-owner-and-minimum-rerun",
            "ready-or-return-exclusive-package",
        ],
        "errors": [],
    }


def start_q1_controller(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze the exact Q1 gate and current B0/S1/W1/E1/T1/C1 lineage."""

    identity = _identity()
    root = Path(workspace).resolve()
    if root.exists():
        _fail("Q1_WORKSPACE_EXISTS", str(root))
    roots = _package_roots(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        character_package=character_package,
    )
    validated = _revalidate_inputs(
        roots, input_gate=input_gate, runtime=runtime
    )
    implementation_identity = _implementation_identity()
    handoff_files = _handoff_allowlist(
        baseline_package=roots["B0"],
        storyline_package=roots["S1"],
        world_package=roots["W1"],
        environment_package=roots["E1"],
        event_package=roots["T1"],
        character_package=roots["C1"],
    )
    frozen = {
        "schema_version": "2.0",
        "run_id": validated["run_id"],
        "stage": "Q1",
        "controller_identity": identity,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "baseline_completion": validated["baseline_completion"],
        "upstream_completions": validated["upstream_completions"],
        "generation_identities": validated["generation_identities"],
        "package_roots": {
            stage: str(path) for stage, path in roots.items()
        },
        "source_inventory": validated["source_inventory"],
        "handoff_source_inventory": [
            {"path": name, "sha256": _sha256_file(path)}
            for name, path in sorted(handoff_files.items())
        ],
        "implementation_identity": implementation_identity,
    }
    initial = {
        "schema_version": "2.0",
        "run_id": validated["run_id"],
        "revision": 0,
        "status": "inputs_frozen",
        "previous_state_sha256": None,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "generation_identities": validated["generation_identities"],
        "handoff_source_inventory": frozen["handoff_source_inventory"],
        "implementation_identity": implementation_identity,
        "semantic_identity": None,
        "handoff_identity": None,
        "completed_phases": [],
    }
    root.mkdir(parents=True)
    _write_new(root / "frozen-inputs.json", frozen)
    _write_new(root / "state" / "revision-000.json", initial)
    return copy.deepcopy(frozen)


def start_semantic_review(
    controller_workspace: str | Path,
    semantic_workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Start P1-P3 in the current controlled semantic Agent context."""

    identity = _identity()
    controller = Path(controller_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    if state.get("status") != "inputs_frozen":
        _fail("Q1_SEMANTIC_ORDER_INVALID", str(state.get("status")))
    frozen = _read(
        controller / "frozen-inputs.json", "Q1_FROZEN_INPUTS_INVALID"
    )
    roots = _package_roots(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        character_package=character_package,
    )
    if frozen.get("package_roots") != {
        stage: str(path) for stage, path in roots.items()
    }:
        _fail("Q1_FROZEN_INPUTS_STALE", "package roots changed")
    validated = _revalidate_inputs(
        roots, input_gate=input_gate, runtime=runtime
    )
    if (
        validated["source_inventory"] != frozen.get("source_inventory")
        or input_gate.reference != frozen.get("input_gate")
        or validated["generation_identities"]
        != frozen.get("generation_identities")
    ):
        _fail("Q1_FROZEN_INPUTS_STALE", "source inventory changed")
    if any(
        identity["task_id"] == prior["task_id"]
        or identity["thread_id"] == prior["thread_id"]
        for prior in validated["generation_identities"]
    ):
        _fail(
            "Q1_SEMANTIC_NOT_ISOLATED",
            "semantic task/thread overlaps a generation context",
        )
    semantic = Path(semantic_workspace).resolve()
    if semantic.exists():
        _fail("Q1_WORKSPACE_EXISTS", str(semantic))
    semantic.mkdir(parents=True)
    session = {
        "schema_version": "2.0",
        "run_id": validated["run_id"],
        "stage": "Q1",
        "role": "semantic-reviewer",
        "session_id": (
            "Q1-SEMANTIC-"
            + _canonical_sha256(
                [identity, input_gate.reference, validated["source_inventory"]]
            )[:20]
        ),
        "identity": identity,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "source_inventory": validated["source_inventory"],
        "phases": list(SEMANTIC_PHASES),
    }
    _write_new(semantic / "generation-session.json", session)
    _advance_state(
        controller,
        state,
        status="semantic_running",
        semantic_identity=identity,
        semantic_session_id=session["session_id"],
    )
    return copy.deepcopy(session)


def submit_semantic_phase(
    controller_workspace: str | Path,
    semantic_workspace: str | Path,
    *,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    """Seal only the next Agent-authored semantic phase."""

    identity = _identity()
    if phase not in SEMANTIC_PHASES:
        _fail("Q1_SEMANTIC_PHASE_FORBIDDEN", phase)
    if not isinstance(payload, Mapping) or not payload:
        _fail("Q1_SEMANTIC_PAYLOAD_INVALID", phase)
    controller = Path(controller_workspace).resolve()
    semantic = Path(semantic_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    frozen = _validate_frozen_source_inventory(controller)
    session = _read(
        semantic / "generation-session.json", "Q1_SEMANTIC_SESSION_INVALID"
    )
    if (
        state.get("status")
        not in {"semantic_running", "semantic_p1_p3_complete"}
        or state.get("semantic_identity") != identity
        or session.get("identity") != identity
        or session.get("session_id") != state.get("semantic_session_id")
        or session.get("input_gate") != state.get("input_gate")
    ):
        _fail(
            "Q1_SEMANTIC_IDENTITY_MISMATCH",
            "active semantic session does not match current environment",
        )
    completed = state.get("completed_phases")
    if not isinstance(completed, list) or completed != list(
        SEMANTIC_PHASES[: len(completed)]
    ):
        _fail("Q1_SEMANTIC_PHASE_ORDER_INVALID", "state phase prefix invalid")
    evidence_root = semantic / "generation-evidence"
    actual = (
        {path.name for path in evidence_root.glob("*.json")}
        if evidence_root.is_dir()
        else set()
    )
    expected_existing = {
        f"{index:02d}-{name}.json"
        for index, name in enumerate(completed, 1)
    }
    if actual != expected_existing:
        _fail(
            "Q1_SEMANTIC_EVIDENCE_TAMPERED",
            "evidence tree differs from controller phase state",
        )
    if len(completed) >= len(SEMANTIC_PHASES):
        _fail("Q1_SEMANTIC_PHASE_ORDER_INVALID", "P1-P3 already sealed")
    expected_phase = SEMANTIC_PHASES[len(completed)]
    if phase != expected_phase:
        _fail(
            "Q1_SEMANTIC_PHASE_ORDER_INVALID",
            f"next phase is {expected_phase}",
        )
    body = copy.deepcopy(dict(payload))
    _validate_semantic_payload(phase, body)
    object_index = _story_object_index(frozen)
    if phase == "review-plan":
        _validate_plan_fingerprints(body["review_plan"], object_index)
    else:
        _validate_assertion_bindings(
            body,
            object_index=object_index,
            phase=phase,
        )
    _validate_t1_lifecycle_review_coverage(
        body, object_index=object_index, phase=phase
    )
    previous = None
    if completed:
        previous = _sha256_file(
            evidence_root / f"{len(completed):02d}-{completed[-1]}.json"
        )
    evidence = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "role": "semantic-reviewer",
        "session_id": session["session_id"],
        "task_id": identity["task_id"],
        "thread_id": identity["thread_id"],
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "input_gate": copy.deepcopy(state["input_gate"]),
        "source_inventory_sha256": _canonical_sha256(
            session["source_inventory"]
        ),
        "payload": body,
        "payload_sha256": _canonical_sha256(body),
    }
    path = evidence_root / f"{len(completed)+1:02d}-{phase}.json"
    _write_new(path, evidence)
    next_completed = [*completed, phase]
    _advance_state(
        controller,
        state,
        status=(
            "semantic_p1_p3_complete"
            if len(next_completed) == len(SEMANTIC_PHASES)
            else "semantic_running"
        ),
        completed_phases=next_completed,
    )
    return _artifact_reference(path, root=semantic)


def start_handoff_review(
    controller_workspace: str | Path,
    handoff_workspace: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
) -> dict[str, Any]:
    """Materialize canonical+manifest only in a distinct handoff context."""

    identity = _identity()
    controller = Path(controller_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    _validate_frozen_source_inventory(controller)
    if state.get("status") != "semantic_p1_p3_complete":
        _fail(
            "Q1_HANDOFF_ORDER_INVALID",
            f"controller status is {state.get('status')!r}",
        )
    semantic_identity = state.get("semantic_identity")
    generation_identities = state.get("generation_identities")
    if (
        not isinstance(semantic_identity, Mapping)
        or not isinstance(generation_identities, list)
        or len(generation_identities) != 5
    ):
        _fail("Q1_IDENTITY_STATE_INVALID", "missing frozen task identities")
    all_prior = [dict(semantic_identity), *generation_identities]
    if any(
        identity["task_id"] == prior.get("task_id")
        or identity["thread_id"] == prior.get("thread_id")
        for prior in all_prior
    ):
        _fail(
            "Q1_HANDOFF_NOT_ISOLATED",
            "handoff task/thread overlaps semantic or generation context",
        )
    files = _handoff_allowlist(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        character_package=character_package,
    )
    expected_sources = [
        {"path": name, "sha256": _sha256_file(path)}
        for name, path in sorted(files.items())
    ]
    if state.get("handoff_source_inventory") != expected_sources:
        _fail(
            "Q1_FROZEN_INPUTS_STALE",
            "handoff source inventory differs from controller freeze",
        )
    handoff = Path(handoff_workspace).resolve()
    inventory = materialize_exact_allowlist(handoff, files=files)
    expected_inventory = [
        {"path": f"inputs/{item['path']}", "sha256": item["sha256"]}
        for item in expected_sources
    ]
    if inventory != expected_inventory or len(inventory) != 12:
        _fail("Q1_ALLOWLIST_TREE_MISMATCH", "handoff projection is not exact")
    session = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "role": "handoff-evaluator",
        "session_id": (
            "Q1-HANDOFF-"
            + _canonical_sha256(
                [identity, state["input_gate"], expected_sources]
            )[:20]
        ),
        "identity": identity,
        "input_gate": copy.deepcopy(state["input_gate"]),
        "allowlist": inventory,
        "forbidden_reads": list(FORBIDDEN_HANDOFF_READS),
    }
    _write_new(handoff / "handoff-session.json", session)
    _advance_state(
        controller,
        state,
        status="handoff_running",
        handoff_identity=identity,
        handoff_session_id=session["session_id"],
        handoff_allowlist=inventory,
    )
    return copy.deepcopy(session)


def seal_handoff_review(
    controller_workspace: str | Path,
    handoff_workspace: str | Path,
    *,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    """Seal externally authored handoff answers without generating semantics."""

    identity = _identity()
    if not isinstance(payload, Mapping) or not payload:
        _fail("Q1_HANDOFF_PAYLOAD_INVALID", "empty payload")
    controller = Path(controller_workspace).resolve()
    handoff = Path(handoff_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    _validate_frozen_source_inventory(controller)
    session = _read(
        handoff / "handoff-session.json", "Q1_HANDOFF_SESSION_INVALID"
    )
    if (
        state.get("status") != "handoff_running"
        or state.get("handoff_identity") != identity
        or session.get("identity") != identity
        or state.get("handoff_session_id") != session.get("session_id")
        or state.get("handoff_allowlist") != session.get("allowlist")
    ):
        _fail(
            "Q1_HANDOFF_IDENTITY_MISMATCH",
            "active handoff session does not match current environment",
        )
    _verify_handoff_inputs(handoff, session["allowlist"])
    body = copy.deepcopy(dict(payload))
    _validate_handoff_payload(
        body,
        session["allowlist"],
        object_index=_handoff_object_index(handoff),
    )
    evidence = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "role": "handoff-evaluator",
        "session_id": session["session_id"],
        "task_id": identity["task_id"],
        "thread_id": identity["thread_id"],
        "input_gate": copy.deepcopy(state["input_gate"]),
        "allowlist": copy.deepcopy(session["allowlist"]),
        "forbidden_reads": list(FORBIDDEN_HANDOFF_READS),
        "payload": body,
        "payload_sha256": _canonical_sha256(body),
    }
    evidence_path = handoff / "handoff-test-evidence.json"
    _write_new(evidence_path, evidence)
    evidence_ref = _artifact_reference(evidence_path, root=handoff)
    execution = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "operation": "independent-development-handoff-test",
        "session_id": session["session_id"],
        "identity": identity,
        "input_gate": copy.deepcopy(state["input_gate"]),
        "allowlist": copy.deepcopy(session["allowlist"]),
        "forbidden_reads": list(FORBIDDEN_HANDOFF_READS),
        "read_set": copy.deepcopy(body["read_set"]),
        "output": evidence_ref,
    }
    execution_path = handoff / "handoff-execution-record.json"
    _write_new(execution_path, execution)
    execution_ref = _artifact_reference(execution_path, root=handoff)
    _advance_state(
        controller,
        state,
        status="handoff_sealed",
        sealed_handoff={
            "evidence": evidence_ref,
            "execution": execution_ref,
        },
    )
    return evidence_ref


def import_sealed_handoff(
    controller_workspace: str | Path,
    semantic_workspace: str | Path,
    handoff_workspace: str | Path,
    *,
    runtime: Any | None = None,
) -> dict[str, str]:
    """Controller-only P4 projection of already sealed handoff evidence."""

    identity = _identity()
    controller = Path(controller_workspace).resolve()
    semantic = Path(semantic_workspace).resolve()
    handoff = Path(handoff_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    _validate_frozen_source_inventory(controller)
    session = _read(
        semantic / "generation-session.json", "Q1_SEMANTIC_SESSION_INVALID"
    )
    if (
        state.get("status") != "handoff_sealed"
        or state.get("semantic_identity") != identity
        or session.get("identity") != identity
        or session.get("session_id") != state.get("semantic_session_id")
        or state.get("completed_phases") != list(SEMANTIC_PHASES)
    ):
        _fail(
            "Q1_HANDOFF_IMPORT_INVALID",
            "P4 import requires the original semantic context after P1-P3",
        )
    handoff_session = _read(
        handoff / "handoff-session.json", "Q1_HANDOFF_SESSION_INVALID"
    )
    _verify_handoff_inputs(handoff, handoff_session["allowlist"])
    sealed = state.get("sealed_handoff")
    if not isinstance(sealed, Mapping):
        _fail("Q1_HANDOFF_IMPORT_INVALID", "sealed references missing")
    source_evidence = _artifact_reference(
        handoff / "handoff-test-evidence.json", root=handoff
    )
    source_execution = _artifact_reference(
        handoff / "handoff-execution-record.json", root=handoff
    )
    if sealed != {
        "evidence": source_evidence,
        "execution": source_execution,
    }:
        _fail("Q1_HANDOFF_IMPORT_INVALID", "sealed handoff was modified")
    import_root = semantic / "sealed-handoff"
    if import_root.exists():
        _fail("Q1_IMMUTABLE_ARTIFACT_EXISTS", str(import_root))
    import_root.mkdir(parents=True)
    shutil.copyfile(
        handoff / source_evidence["path"],
        import_root / "handoff-test-evidence.json",
    )
    shutil.copyfile(
        handoff / source_execution["path"],
        import_root / "handoff-execution-record.json",
    )
    imported_evidence = _artifact_reference(
        import_root / "handoff-test-evidence.json", root=semantic
    )
    imported_execution = _artifact_reference(
        import_root / "handoff-execution-record.json", root=semantic
    )
    previous = _sha256_file(
        semantic / "generation-evidence/03-cross-domain-challenges.json"
    )
    phase4 = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "role": "controller-import",
        "session_id": session["session_id"],
        "task_id": identity["task_id"],
        "thread_id": identity["thread_id"],
        "phase": HANDOFF_PHASE,
        "sequence": 4,
        "previous_evidence_sha256": previous,
        "handoff_evidence": imported_evidence,
        "handoff_execution": imported_execution,
    }
    phase4_path = (
        semantic / "generation-evidence/04-development-handoff-test.json"
    )
    _write_new(phase4_path, phase4)
    phase4_ref = _artifact_reference(phase4_path, root=semantic)
    _advance_state(
        controller,
        state,
        status="handoff_imported",
        completed_phases=[*SEMANTIC_PHASES, HANDOFF_PHASE],
        imported_handoff={
            "phase4": phase4_ref,
            "evidence": imported_evidence,
            "execution": imported_execution,
        },
    )
    return phase4_ref


def submit_final_review(
    controller_workspace: str | Path,
    semantic_workspace: str | Path,
    *,
    review: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    """Seal P5 in the original semantic context."""

    identity = _identity()
    if not isinstance(review, Mapping) or not review:
        _fail("Q1_FINAL_REVIEW_INVALID", "empty review")
    controller = Path(controller_workspace).resolve()
    semantic = Path(semantic_workspace).resolve()
    state = _latest_state(controller)
    _validate_controller_implementation(controller, state)
    _validate_frozen_source_inventory(controller)
    session = _read(
        semantic / "generation-session.json", "Q1_SEMANTIC_SESSION_INVALID"
    )
    if (
        state.get("status") != "handoff_imported"
        or state.get("semantic_identity") != identity
        or session.get("identity") != identity
        or state.get("completed_phases")
        != [*SEMANTIC_PHASES, HANDOFF_PHASE]
    ):
        _fail(
            "Q1_FINAL_REVIEW_INVALID",
            "P5 requires imported P4 in the original semantic context",
        )
    body = copy.deepcopy(dict(review))
    p1 = _phase_payload(semantic, 1, "review-plan")
    p2 = _phase_payload(semantic, 2, "domain-challenges")
    p3 = _phase_payload(semantic, 3, "cross-domain-challenges")
    handoff = _read(
        semantic / state["imported_handoff"]["evidence"]["path"],
        "Q1_HANDOFF_IMPORT_INVALID",
    )
    public_p2 = {
        key: value
        for key, value in p2.items()
        if key != "assertion_bindings"
    }
    public_p3 = {
        key: value
        for key, value in p3.items()
        if key != "assertion_bindings"
    }
    frozen = _read(
        controller / "frozen-inputs.json", "Q1_FROZEN_INPUTS_INVALID"
    )
    object_index = _story_object_index(frozen)
    submitted_findings = body.get("findings", [])
    quality_coverage = _quality_coverage_certificate(
        object_index=object_index,
        handoff_payload=handoff["payload"],
        semantic_payloads=(p2, p3),
        findings=(
            submitted_findings
            if isinstance(submitted_findings, list)
            else []
        ),
    )
    expected_fields = {
        **public_p2,
        **public_p3,
        "development_usability_test": handoff["payload"][
            "development_usability_test"
        ],
        "handoff_test_evidence": state["imported_handoff"]["evidence"],
        "task_isolation": {
            "semantic_task_id": state["semantic_identity"]["task_id"],
            "handoff_task_id": state["handoff_identity"]["task_id"],
            "handoff_allowlist": state["handoff_allowlist"],
            "forbidden_reads": list(FORBIDDEN_HANDOFF_READS),
        },
        "input_gate": state["input_gate"],
        "quality_coverage": quality_coverage,
    }
    for field, expected in expected_fields.items():
        if body.get(field) != expected:
            _fail(
                "Q1_FINAL_REVIEW_LINEAGE_MISMATCH",
                f"{field} differs from sealed phase evidence",
            )
    if (
        body.get("schema_version") != "2.0"
        or body.get("skill") != "novel-conception-reviewer"
        or body.get("stage") != "Q1"
        or body.get("run_id") != state["run_id"]
        or body.get("status") != body.get("verdict")
    ):
        _fail("Q1_FINAL_REVIEW_INVALID", "fixed Q1 fields are invalid")
    _validate_plan_fingerprints(p1["review_plan"], object_index)
    _validate_assertion_bindings(
        p2,
        object_index=object_index,
        phase="domain-challenges",
    )
    _validate_assertion_bindings(
        p3,
        object_index=object_index,
        phase="cross-domain-challenges",
    )
    known_ids = _known_story_ids(frozen)
    author_ids = _author_control_ids(frozen)
    checks = [
        *body.get("domain_reviews", []),
        *body.get("cross_domain_checks", []),
        *body.get("reality_claim_review", []),
        *body.get("coverage_recalculation", []),
        *body.get("consistency_matrix", []),
        *body.get("causal_challenges", []),
        *body.get("easy_solution_challenges", []),
    ]
    for check in checks:
        evidence_ids = check.get("evidence_ids", [])
        if not evidence_ids or not set(evidence_ids) <= known_ids:
            _fail(
                "Q1_STORY_EVIDENCE_INVALID",
                str(check.get("id")),
            )
    conclusions = [
        " ".join(str(check.get("conclusion", "")).split())
        for check in checks
    ]
    if len(conclusions) != len(set(conclusions)):
        _fail(
            "Q1_GENERIC_SEMANTIC_EVIDENCE",
            "review checks reuse template conclusions",
        )
    handoff_evidence_ids = body["development_usability_test"].get(
        "evidence_ids", []
    )
    if (
        not handoff_evidence_ids
        or not set(handoff_evidence_ids) <= known_ids
    ):
        _fail("Q1_STORY_EVIDENCE_INVALID", "development usability test")
    findings = body.get("findings")
    if not isinstance(findings, list):
        _fail("Q1_FINAL_REVIEW_INVALID", "findings must be an array")
    for finding in findings:
        if not isinstance(finding, Mapping):
            _fail("Q1_FINAL_REVIEW_INVALID", "finding is not an object")
        cited = set(finding.get("evidence_ids", [])) | set(
            finding.get("affected_ids", [])
        )
        if not cited or not cited <= known_ids:
            _fail(
                "Q1_STORY_EVIDENCE_INVALID",
                str(finding.get("id")),
            )
        owner, minimum_rerun = _owner_for_finding(
            finding, author_ids=author_ids
        )
        if (
            finding.get("calculated_owner") != owner
            or finding.get("minimum_rerun") != minimum_rerun
        ):
            _fail(
                "Q1_FINDING_OWNER_INVALID",
                str(finding.get("id")),
            )
    actionable = [
        item
        for item in findings
        if item.get("severity") in {"contradictory", "revise", "blocked"}
    ]
    verdict = body.get("verdict")
    if verdict == "ready":
        if (
            actionable
            or body.get("return_request") is not None
            or quality_coverage["result"] != "complete"
            or quality_coverage["unresolved_blocking_quality_record_ids"]
        ):
            _fail("Q1_READY_GATE_FAILED", "ready contains actionable return")
    elif verdict in {"revise", "blocked"}:
        route_selector = body.get("return_request")
        if (
            not actionable
            or not isinstance(route_selector, Mapping)
            or set(route_selector) != {"finding_id"}
        ):
            _fail(
                "Q1_RETURN_ROUTE_INVALID",
                "non-ready review must select one actionable finding",
            )
        selected = next(
            (
                item
                for item in actionable
                if item.get("id") == route_selector["finding_id"]
            ),
            None,
        )
        if selected is None:
            _fail("Q1_RETURN_ROUTE_INVALID", "selected finding is absent")
        def route_key(item: Mapping[str, Any]) -> tuple[int, str]:
            item_owner, _ = _owner_for_finding(
                item, author_ids=author_ids
            )
            return _OWNER_ORDER.index(item_owner), str(item.get("id"))

        expected_selected = min(actionable, key=route_key)
        if selected.get("id") != expected_selected.get("id"):
            _fail(
                "Q1_RETURN_ROUTE_INVALID",
                "selected finding is not the minimum invalidation route",
            )
        owner, _ = _owner_for_finding(selected, author_ids=author_ids)
        issue_kind = (
            "author_locked"
            if owner.startswith("I")
            else _OWNER_ISSUE_KIND[owner]
        )
        runtime_module = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime"
        )
        contract_runtime = runtime or runtime_module.ContractRuntime()
        try:
            request = runtime_module.route_return(
                run_id=state["run_id"],
                return_id=(
                    "RET-Q1-"
                    + _canonical_sha256(
                        [state["run_id"], selected["id"], selected["problem"]]
                    )[:20]
                ),
                origin_kind="stage",
                origin_stage="Q1",
                issue_kind=issue_kind,
                problem=selected["problem"],
                evidence_ids=selected["evidence_ids"],
                violated_contract=selected["violated_contract"],
                required_revision=selected["required_revision"],
                author_decision=None,
                has_current_author_decision=False,
                has_current_conception_completion=False,
                runtime=contract_runtime,
            )
        except Exception as error:
            _fail("Q1_RETURN_ROUTE_INVALID", str(error))
        request_path = semantic / "return-request.json"
        _write_new(request_path, request)
        body["return_request"] = _artifact_reference(
            request_path, root=semantic
        )
    else:
        _fail("Q1_FINAL_REVIEW_INVALID", f"unknown verdict {verdict!r}")
    contract_runtime = runtime
    if contract_runtime is None:
        runtime_module = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime"
        )
        contract_runtime = runtime_module.ContractRuntime()
    try:
        contract_runtime.validate(body, "conception-review.schema.json")
    except Exception as error:
        _fail("Q1_FINAL_REVIEW_SCHEMA_INVALID", str(error))
    review_path = semantic / "conception-review.json"
    _write_new(review_path, body)
    review_ref = _artifact_reference(review_path, root=semantic)
    phase5 = {
        "schema_version": "2.0",
        "run_id": state["run_id"],
        "stage": "Q1",
        "role": "semantic-reviewer",
        "session_id": session["session_id"],
        "task_id": identity["task_id"],
        "thread_id": identity["thread_id"],
        "phase": FINAL_PHASE,
        "sequence": 5,
        "previous_evidence_sha256": _sha256_file(
            semantic / "generation-evidence/04-development-handoff-test.json"
        ),
        "review": review_ref,
        "verdict": verdict,
    }
    phase5_path = semantic / "generation-evidence/05-final-review.json"
    _write_new(phase5_path, phase5)
    phase5_ref = _artifact_reference(phase5_path, root=semantic)
    _advance_state(
        controller,
        state,
        status="final_sealed",
        completed_phases=[
            *SEMANTIC_PHASES,
            HANDOFF_PHASE,
            FINAL_PHASE,
        ],
        final_review=review_ref,
        final_phase=phase5_ref,
        verdict=verdict,
    )
    return review_ref


def validate_q1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    """Validate the ready package or the non-ready return bundle."""

    root = Path(package_root).resolve()
    contract_runtime = runtime
    if contract_runtime is None:
        runtime_module = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime"
        )
        contract_runtime = runtime_module.ContractRuntime()
    review = _read(
        root / "conception-review.json", "Q1_REVIEW_MISSING"
    )
    try:
        contract_runtime.validate(review, "conception-review.schema.json")
    except Exception as error:
        _fail("Q1_REVIEW_SCHEMA_INVALID", str(error))
    verdict = review["verdict"]
    stored_validation = _read(
        root / "validation.json", "Q1_VALIDATION_MISSING"
    )
    if stored_validation != _validation_record(review["run_id"], verdict):
        _fail("Q1_VALIDATION_STALE", "stored validation is not reproducible")
    review_ref = _artifact_reference(
        root / "conception-review.json", root=root
    )
    gate_path = root / "input-gate.json"
    if (
        not gate_path.is_file()
        or _sha256_file(gate_path) != review["input_gate"]["sha256"]
        or not review["input_gate"]["path"].endswith("/input-gate.json")
    ):
        _fail("Q1_GATE_BINDING_INVALID", "packaged input gate differs")
    gate = _read(gate_path, "Q1_GATE_BINDING_INVALID")
    if review["handoff_test_evidence"] != _artifact_reference(
        root / "sealed-handoff/handoff-test-evidence.json", root=root
    ):
        _fail("Q1_HANDOFF_BINDING_INVALID", "review handoff reference")
    session = _read(
        root / "generation-session.json", "Q1_SESSION_INVALID"
    )
    if (
        session.get("run_id") != review["run_id"]
        or session.get("stage") != "Q1"
        or session.get("role") != "semantic-reviewer"
    ):
        _fail("Q1_SESSION_INVALID", "session fixed fields")
    expected_phases = [*SEMANTIC_PHASES, HANDOFF_PHASE, FINAL_PHASE]
    evidence_refs: list[dict[str, str]] = []
    previous = None
    for index, phase in enumerate(expected_phases, 1):
        path = root / "generation-evidence" / f"{index:02d}-{phase}.json"
        evidence = _read(path, "Q1_EVIDENCE_INVALID")
        if (
            evidence.get("phase") != phase
            or evidence.get("sequence") != index
            or evidence.get("previous_evidence_sha256") != previous
        ):
            _fail("Q1_EVIDENCE_INVALID", phase)
        if index <= 3:
            payload = evidence.get("payload")
            if (
                not isinstance(payload, Mapping)
                or evidence.get("payload_sha256")
                != _canonical_sha256(payload)
            ):
                _fail("Q1_EVIDENCE_INVALID", f"{phase} payload")
        if index == 5 and evidence.get("review") != review_ref:
            _fail("Q1_EVIDENCE_INVALID", "final review reference")
        reference = _artifact_reference(path, root=root)
        evidence_refs.append(reference)
        previous = reference["sha256"]
    evidence_index = _read(
        root / "generation-evidence-index.json", "Q1_EVIDENCE_INVALID"
    )
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": review["run_id"],
        "stage": "Q1",
        "session_id": session["session_id"],
        "phases": expected_phases,
        "evidence": evidence_refs,
    }:
        _fail("Q1_EVIDENCE_INVALID", "evidence index")
    aggregate = _read(
        root / "execution-record.json", "Q1_EXECUTION_INVALID"
    )
    semantic_execution = _artifact_reference(
        root / "semantic-execution-record.json", root=root
    )
    handoff_execution = _artifact_reference(
        root / "sealed-handoff/handoff-execution-record.json", root=root
    )
    if (
        aggregate.get("semantic_execution") != semantic_execution
        or aggregate.get("handoff_execution") != handoff_execution
        or aggregate.get("output") != review_ref
        or aggregate.get("task_isolation") != review["task_isolation"]
    ):
        _fail("Q1_EXECUTION_INVALID", "aggregate execution bindings")
    semantic_execution_body = _read(
        root / "semantic-execution-record.json", "Q1_EXECUTION_INVALID"
    )
    if (
        semantic_execution_body.get("identity", {}).get("task_id")
        != review["task_isolation"]["semantic_task_id"]
        or semantic_execution_body.get("input_gate") != review["input_gate"]
        or semantic_execution_body.get("phases") != evidence_refs
        or semantic_execution_body.get("output") != review_ref
    ):
        _fail("Q1_EXECUTION_INVALID", "semantic execution bindings")
    handoff_execution_body = _read(
        root / "sealed-handoff/handoff-execution-record.json",
        "Q1_EXECUTION_INVALID",
    )
    handoff_evidence_ref = _artifact_reference(
        root / "sealed-handoff/handoff-test-evidence.json", root=root
    )
    handoff_evidence_body = _read(
        root / "sealed-handoff/handoff-test-evidence.json",
        "Q1_HANDOFF_BINDING_INVALID",
    )
    handoff_payload = handoff_evidence_body.get("payload")
    if not isinstance(handoff_payload, Mapping):
        _fail("Q1_HANDOFF_BINDING_INVALID", "handoff payload missing")
    _validate_packaged_quality_coverage(review, handoff_payload)
    if (
        handoff_execution_body.get("identity", {}).get("task_id")
        != review["task_isolation"]["handoff_task_id"]
        or handoff_execution_body.get("allowlist")
        != review["task_isolation"]["handoff_allowlist"]
        or set(handoff_execution_body.get("read_set", []))
        != {
            item["path"]
            for item in review["task_isolation"]["handoff_allowlist"]
        }
        or handoff_execution_body.get("output", {}).get("sha256")
        != handoff_evidence_ref["sha256"]
    ):
        _fail("Q1_EXECUTION_INVALID", "handoff execution bindings")
    implementation = aggregate.get("implementation_catalog")
    if not isinstance(implementation, list):
        _fail("Q1_IMPLEMENTATION_STALE", "catalog missing")
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in implementation
        if isinstance(item, Mapping)
    }
    try:
        identity_mode, catalog = stage_identity.validate_stage_catalog(
            stage="Q1",
            records=implementation,
            package_root=root,
            current_paths=_implementation_paths(),
            verify_artifact_reference=canonical_runtime.verify_artifact_reference,
            sha256_file=_sha256_file,
        )
    except stage_identity.StageImplementationIdentityError as error:
        _fail("Q1_IMPLEMENTATION_STALE", str(error))
    sealed_identity = aggregate.get("implementation_identity")
    if identity_mode == stage_identity.STAGE_IMPLEMENTATION_IDENTITY_CONTRACT_VERSION:
        if sealed_identity != _implementation_identity():
            _fail("Q1_IMPLEMENTATION_STALE", "package identity differs")
    else:
        if (
            not isinstance(sealed_identity, Mapping)
            or set(sealed_identity) != {"algorithm", "catalog", "canonical_digest"}
            or sealed_identity.get("algorithm") != _IMPLEMENTATION_IDENTITY_ALGORITHM
            or not isinstance(sealed_identity.get("catalog"), list)
            or sealed_identity.get("canonical_digest")
            != _canonical_sha256(sealed_identity.get("catalog"))
        ):
            _fail("Q1_IMPLEMENTATION_STALE", "legacy package identity is malformed")
        sealed_catalog = {
            item.get("identity"): item
            for item in sealed_identity["catalog"]
            if isinstance(item, Mapping)
        }
        current_sources = {
            item["identity"]: item["source_path"]
            for item in _implementation_identity()["catalog"]
        }
        if (
            len(sealed_catalog) != len(sealed_identity["catalog"])
            or set(sealed_catalog) != set(catalog)
            or any(
                item.get("sha256") != catalog[identity].get("sha256")
                or (
                    identity in current_sources
                    and item.get("source_path") != current_sources[identity]
                )
                for identity, item in sealed_catalog.items()
            )
        ):
            _fail("Q1_IMPLEMENTATION_STALE", "legacy package identity differs")
    if (
        len(catalog) != len(implementation)
        or aggregate.get("implementation")
        != [item["artifact"] for item in implementation]
    ):
        _fail("Q1_IMPLEMENTATION_STALE", "package catalog is not exact")
    if verdict == "ready":
        manifest = _read(
            root / "package-manifest.json", "Q1_MANIFEST_INVALID"
        )
        try:
            contract_runtime.validate(
                manifest, "package-manifest.schema.json"
            )
        except Exception as error:
            _fail("Q1_MANIFEST_INVALID", str(error))
        if (
            manifest.get("stage") != "Q1"
            or manifest.get("package_profile") != "independent-review"
            or manifest.get("artifact_roles", {}).get("canonical") != review_ref
            or manifest.get("artifact_roles", {}).get("handoff_evidence")
            != review["handoff_test_evidence"]
        ):
            _fail("Q1_MANIFEST_INVALID", "Q1 roles")
        manifest_files = manifest.get("files")
        if not isinstance(manifest_files, list):
            _fail("Q1_MANIFEST_INVALID", "files")
        actual = {
            _artifact_reference(path, root=root)["path"]: _artifact_reference(
                path, root=root
            )
            for path in root.rglob("*")
            if path.is_file()
            and path.name
            not in {"package-manifest.json", "stage-completion.json"}
        }
        if {item["path"]: item for item in manifest_files} != actual:
            _fail("Q1_MANIFEST_INVALID", "files are not exact")
        for reference in manifest_files:
            path = root / PurePosixPath(reference["path"])
            if not path.is_file() or _sha256_file(path) != reference["sha256"]:
                _fail("Q1_MANIFEST_INVALID", reference["path"])
        if require_completion:
            completion = _read(
                root / "stage-completion.json", "Q1_COMPLETION_MISSING"
            )
            try:
                contract_runtime.validate(
                    completion, "stage-completion.schema.json"
                )
            except Exception as error:
                _fail("Q1_COMPLETION_INVALID", str(error))
            manifest_ref = completion.get("manifest")
            manifest_path = (
                manifest_ref.get("path")
                if isinstance(manifest_ref, Mapping)
                else ""
            )
            logical_prefix = PurePosixPath(manifest_path).parent.as_posix()
            expected_manifest = {
                "path": (PurePosixPath(logical_prefix) / "package-manifest.json").as_posix(),
                "sha256": _sha256_file(root / "package-manifest.json"),
            }
            expected_validation = {
                "path": (PurePosixPath(logical_prefix) / "validation.json").as_posix(),
                "sha256": _sha256_file(root / "validation.json"),
            }
            if (
                not (
                    logical_prefix == "Q1"
                    or logical_prefix.startswith("Q1/")
                )
                or completion.get("run_id") != review["run_id"]
                or completion.get("stage") != "Q1"
                or completion.get("status") != "ready"
                or completion.get("session_id") != session["session_id"]
                or completion.get("manifest") != expected_manifest
                or completion.get("validation") != expected_validation
                or completion.get("input_gate") != review["input_gate"]
                or completion.get("state_before") != gate.get("run_state")
                or completion.get("previous_stage_completions")
                != gate.get("upstream_completions")
                or completion.get("return_binding")
                != gate.get("return_binding")
            ):
                _fail("Q1_COMPLETION_INVALID", "completion binding")
        if any(
            (root / name).exists()
            for name in (
                "return-request.json",
                "next-run-state.json",
                "blocked-report.md",
            )
        ):
            _fail("Q1_READY_PACKAGE_INVALID", "return-only files present")
    else:
        for required in (
            "return-request.json",
            "next-run-state.json",
            "blocked-report.md",
        ):
            if not (root / required).is_file():
                _fail("Q1_RETURN_PACKAGE_INVALID", f"missing {required}")
        if (root / "stage-completion.json").exists() or (
            root / "package-manifest.json"
        ).exists():
            _fail(
                "Q1_RETURN_PACKAGE_INVALID",
                "non-ready package contains ready artifacts",
            )
        request_ref = _artifact_reference(
            root / "return-request.json", root=root
        )
        if review["return_request"] != request_ref:
            _fail("Q1_RETURN_PACKAGE_INVALID", "request reference")
        request = _read(
            root / "return-request.json", "Q1_RETURN_PACKAGE_INVALID"
        )
        try:
            contract_runtime.validate(request, "return-request.schema.json")
        except Exception as error:
            _fail("Q1_RETURN_PACKAGE_INVALID", str(error))
        actionable = [
            item
            for item in review["findings"]
            if item["severity"] in {"contradictory", "revise", "blocked"}
        ]
        if not actionable:
            _fail("Q1_RETURN_PACKAGE_INVALID", "no actionable finding")
        selected = min(
            actionable,
            key=lambda item: (
                _OWNER_ORDER.index(item["calculated_owner"]),
                item["id"],
            ),
        )
        expected_request_fields = {
            "run_id": review["run_id"],
            "origin_kind": "stage",
            "origin_stage": "Q1",
            "problem": selected["problem"],
            "evidence_ids": selected["evidence_ids"],
            "violated_contract": selected["violated_contract"],
            "calculated_owner": selected["calculated_owner"],
            "required_revision": selected["required_revision"],
            "resume_point": selected["minimum_rerun"],
            "status": "active",
        }
        if any(
            request.get(field) != expected
            for field, expected in expected_request_fields.items()
        ):
            _fail(
                "Q1_RETURN_PACKAGE_INVALID",
                "request does not bind deterministic finding route",
            )
        next_state = _read(
            root / "next-run-state.json", "Q1_RETURN_PACKAGE_INVALID"
        )
        try:
            contract_runtime.validate(
                next_state, "autonomous-run-state.schema.json"
            )
        except Exception as error:
            _fail("Q1_RETURN_PACKAGE_INVALID", str(error))
        if (
            next_state.get("status") != "revise"
            or next_state.get("active_return") is None
        ):
            _fail(
                "Q1_RETURN_PACKAGE_INVALID",
                "next state did not activate return",
            )
    return copy.deepcopy(stored_validation)


def run_q1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    event_package: str | Path,
    character_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controller_workspace: str | Path,
    semantic_workspace: str | Path,
    handoff_workspace: str | Path,
    logical_package_path: str = "Q1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> Q1RunReceipt:
    """Package a sealed Q1 result and advance or return through coordinator."""

    identity = _identity()
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("Q1_OUTPUT_EXISTS", str(destination))
    controller = Path(controller_workspace).resolve()
    semantic = Path(semantic_workspace).resolve()
    state = _latest_state(controller)
    implementation_identity = _validate_controller_implementation(
        controller, state
    )
    if (
        state.get("status") != "final_sealed"
        or state.get("semantic_identity") != identity
        or state.get("completed_phases")
        != [*SEMANTIC_PHASES, HANDOFF_PHASE, FINAL_PHASE]
    ):
        _fail("Q1_FINAL_STATE_INVALID", "Q1 is not sealed in semantic context")
    roots = _package_roots(
        baseline_package=baseline_package,
        storyline_package=storyline_package,
        world_package=world_package,
        environment_package=environment_package,
        event_package=event_package,
        character_package=character_package,
    )
    frozen = _read(
        controller / "frozen-inputs.json", "Q1_FROZEN_INPUTS_INVALID"
    )
    if (
        frozen.get("package_roots")
        != {stage: str(path) for stage, path in roots.items()}
        or frozen.get("source_inventory") != _source_inventory(roots)
        or frozen.get("input_gate") != input_gate.reference
    ):
        _fail("Q1_FROZEN_INPUTS_STALE", "inputs changed before packaging")
    review = _read(
        semantic / "conception-review.json", "Q1_REVIEW_MISSING"
    )
    if (
        state.get("final_review")
        != _artifact_reference(
            semantic / "conception-review.json", root=semantic
        )
        or review.get("verdict") != state.get("verdict")
    ):
        _fail("Q1_FINAL_REVIEW_INVALID", "sealed final review changed")
    runtime_module = importlib.import_module(
        "harnesses.novel-conception-autonomous.runtime"
    )
    contract_runtime = runtime or runtime_module.ContractRuntime()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.", dir=destination.parent
        )
    )
    staging = temp_parent / "package"
    staging.mkdir()
    completion = None
    transition = None
    try:
        _write(staging / "input-gate.json", input_gate.data)
        shutil.copyfile(
            semantic / "conception-review.json",
            staging / "conception-review.json",
        )
        shutil.copyfile(
            semantic / "generation-session.json",
            staging / "generation-session.json",
        )
        evidence_refs: list[dict[str, str]] = []
        phase_names = [*SEMANTIC_PHASES, HANDOFF_PHASE, FINAL_PHASE]
        for index, phase in enumerate(phase_names, 1):
            source = (
                semantic
                / "generation-evidence"
                / f"{index:02d}-{phase}.json"
            )
            target = staging / "generation-evidence" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            evidence_refs.append(
                _artifact_reference(target, root=staging)
            )
        _write(
            staging / "generation-evidence-index.json",
            {
                "schema_version": "2.0",
                "run_id": review["run_id"],
                "stage": "Q1",
                "session_id": state["semantic_session_id"],
                "phases": phase_names,
                "evidence": evidence_refs,
            },
        )
        sealed_root = staging / "sealed-handoff"
        sealed_root.mkdir()
        for name in (
            "handoff-test-evidence.json",
            "handoff-execution-record.json",
        ):
            shutil.copyfile(
                semantic / "sealed-handoff" / name,
                sealed_root / name,
            )
        if review["verdict"] != "ready":
            shutil.copyfile(
                semantic / "return-request.json",
                staging / "return-request.json",
            )
        implementation_refs: list[dict[str, str]] = []
        implementation_catalog: list[dict[str, Any]] = []
        for implementation_id, source in sorted(
            _implementation_paths().items()
        ):
            target = staging / "implementation" / implementation_id
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            reference = _artifact_reference(target, root=staging)
            implementation_refs.append(reference)
            implementation_catalog.append(
                {"identity": implementation_id, "artifact": reference}
            )
        review_ref = _artifact_reference(
            staging / "conception-review.json", root=staging
        )
        semantic_execution = {
            "schema_version": "2.0",
            "run_id": review["run_id"],
            "stage": "Q1",
            "operation": "controlled-independent-semantic-review",
            "session_id": state["semantic_session_id"],
            "identity": state["semantic_identity"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "source_inventory_sha256": _canonical_sha256(
                frozen["source_inventory"]
            ),
            "phases": evidence_refs,
            "output": review_ref,
        }
        _write(
            staging / "semantic-execution-record.json",
            semantic_execution,
        )
        semantic_execution_ref = _artifact_reference(
            staging / "semantic-execution-record.json", root=staging
        )
        handoff_execution_ref = _artifact_reference(
            staging / "sealed-handoff/handoff-execution-record.json",
            root=staging,
        )
        aggregate = {
            "schema_version": "2.0",
            "run_id": review["run_id"],
            "stage": "Q1",
            "operation": "dual-context-independent-conception-review",
            "session_id": state["semantic_session_id"],
            "input_gate": copy.deepcopy(input_gate.reference),
            "semantic_execution": semantic_execution_ref,
            "handoff_execution": handoff_execution_ref,
            "task_isolation": copy.deepcopy(review["task_isolation"]),
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "implementation_identity": implementation_identity,
            "output": review_ref,
        }
        _write(staging / "execution-record.json", aggregate)
        (staging / "review-preview.md").write_text(
            "# Q1 independent conception review\n\n"
            f"- Verdict: `{review['verdict']}`\n"
            f"- Findings: {len(review['findings'])}\n"
            f"- Semantic task: `{review['task_isolation']['semantic_task_id']}`\n"
            f"- Handoff task: `{review['task_isolation']['handoff_task_id']}`\n",
            encoding="utf-8",
            newline="",
        )
        _write(
            staging / "validation.json",
            _validation_record(review["run_id"], review["verdict"]),
        )
        if review["verdict"] == "ready":
            files = [
                _artifact_reference(path, root=staging)
                for path in sorted(
                    staging.rglob("*"), key=lambda item: item.as_posix()
                )
                if path.is_file()
            ]
            by_path = {item["path"]: item for item in files}
            manifest = {
                "schema_version": "2.0",
                "run_id": review["run_id"],
                "stage": "Q1",
                "package_profile": "independent-review",
                "verdict": "ready",
                "files": files,
                "artifact_roles": {
                    "canonical": by_path["conception-review.json"],
                    "generation_session": by_path["generation-session.json"],
                    "generation_evidence_index": by_path[
                        "generation-evidence-index.json"
                    ],
                    "execution_record": by_path["execution-record.json"],
                    "preview": by_path["review-preview.md"],
                    "handoff_evidence": by_path[
                        "sealed-handoff/handoff-test-evidence.json"
                    ],
                },
                "validation": by_path["validation.json"],
                "implementation": implementation_refs,
            }
            contract_runtime.validate(
                manifest, "package-manifest.schema.json"
            )
            _write(staging / "package-manifest.json", manifest)
            validate_q1_package(
                staging,
                runtime=contract_runtime,
                require_completion=False,
            )
            completion_data = {
                "schema_version": "2.0",
                "run_id": review["run_id"],
                "stage": "Q1",
                "status": "ready",
                "session_id": state["semantic_session_id"],
                "manifest": {
                    "path": _logical(
                        f"{logical_package_path}/package-manifest.json"
                    ),
                    "sha256": _sha256_file(
                        staging / "package-manifest.json"
                    ),
                },
                "validation": {
                    "path": _logical(
                        f"{logical_package_path}/validation.json"
                    ),
                    "sha256": _sha256_file(staging / "validation.json"),
                },
                "input_gate": copy.deepcopy(input_gate.reference),
                "state_before": copy.deepcopy(input_gate.data["run_state"]),
                "previous_stage_completions": copy.deepcopy(
                    input_gate.data["upstream_completions"]
                ),
                "return_binding": copy.deepcopy(
                    input_gate.data["return_binding"]
                ),
            }
            contract_runtime.validate(
                completion_data, "stage-completion.schema.json"
            )
            completion = runtime_module.seal_stage_document(
                completion_data,
                "Q1",
                _logical(f"{logical_package_path}/stage-completion.json"),
            )
            _write(staging / "stage-completion.json", completion.data)
            validate_q1_package(staging, runtime=contract_runtime)
            transition = coordinator.accept_stage_completion(
                gate=input_gate,
                completion=completion,
                next_state_path=next_state_path,
                active_return_request=active_return_request,
            )
        else:
            request = _read(
                staging / "return-request.json",
                "Q1_RETURN_PACKAGE_INVALID",
            )
            sealed_request = runtime_module.seal_document(
                request,
                _logical(f"{logical_package_path}/return-request.json"),
            )
            transition = coordinator.apply_return_request(
                request=sealed_request,
                next_state_path=next_state_path,
                conception_completion_current=False,
            )
            _write(staging / "next-run-state.json", transition.snapshot)
            (staging / "blocked-report.md").write_text(
                "# Q1 return\n\n"
                f"- Verdict: `{review['verdict']}`\n"
                f"- Owner: `{request['calculated_owner']}`\n"
                f"- Resume: `{request['resume_point']}`\n"
                f"- Problem: {request['problem']}\n",
                encoding="utf-8",
                newline="",
            )
            validate_q1_package(staging, runtime=contract_runtime)
        staging.replace(destination)
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return Q1RunReceipt(
        package_root=destination,
        verdict=review["verdict"],
        completion=completion,
        transition=transition,
    )


__all__ = [
    "SEMANTIC_PHASES",
    "HANDOFF_PHASE",
    "FINAL_PHASE",
    "FORBIDDEN_HANDOFF_READS",
    "T1_LIFECYCLE_CLOSURE_SCOPE",
    "T1_LIFECYCLE_REVIEW_CONTRACT",
    "Q1Error",
    "Q1RunReceipt",
    "materialize_exact_allowlist",
    "start_q1_controller",
    "start_semantic_review",
    "submit_semantic_phase",
    "start_handoff_review",
    "seal_handoff_review",
    "import_sealed_handoff",
    "submit_final_review",
    "validate_q1_package",
    "run_q1",
]
