"""Deterministic B0 author-control baseline packaging and validation.

B0 has no creative authority.  It copies approved interview artifacts byte for
byte, extracts only explicitly marked controls, and rejects any source chain or
fact dependency it cannot prove.  A failed build never leaves a candidate
package at the requested destination.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .canonical import (
    artifact_reference,
    canonical_json,
    canonical_sha256,
    sha256_file,
    verify_artifact_reference,
    verify_manifest_integrity,
)
from .b0_implementation_identity import (
    TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256,
    TRUSTED_LEGACY_MISMATCH_BINDINGS,
    TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES,
)
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import SealedDocument
from .migration_handoff import (
    FinalizedMigrationHandoff,
    validate_finalized_migration_handoff,
)


DOMAINS = ("I0", "I1", "I2", "I3", "I4", "I5")
DOMAIN_PREFIX = {
    "I0": "INT",
    "I1": "SUB",
    "I2": "WLD",
    "I3": "CHR",
    "I4": "CAU",
    "I5": "NAR",
}
HARDNESS = {
    "author_locked",
    "autonomous_owned",
    "downstream_freedom",
    "author_open",
}
_CONTROL_HEADING = re.compile(
    r"^(?P<marks>#{1,6})\s+"
    r"\[(?P<id>[A-Z][A-Z0-9._-]*)\]"
    r"\[(?P<hardness>author_locked|autonomous_owned|"
    r"downstream_freedom|author_open)\]\s+"
    r"(?P<title>\S.*)$"
)
_INTERVIEW_VALIDATOR = (
    Path(__file__).resolve().parents[2]
    / "novel-conception-interview"
    / "validators"
    / "validate_stage_completion.py"
)

# B0 package readiness is bound only to the implementation it actually uses.
# The complete schema catalog is still self-checked by ContractRuntime, but a
# later-stage schema (for example W1's world model) must not retroactively make
# an already sealed B0 package stale.
B0_SCHEMA_DEPENDENCIES = (
    "author-control-baseline.schema.json",
    "autonomous-run-state.schema.json",
    "common-defs.schema.json",
    "input-gate.schema.json",
    "package-manifest.schema.json",
    "return-request.schema.json",
    "stage-completion.schema.json",
    "authority-revision-finalization.schema.json",
    "authority-revision-patch-plan.schema.json",
    "authority-revision-semantic-review.schema.json",
)

# Behavioral B0 runtime boundary. ``runtime/__init__.py`` is only the
# package's public-export aggregator: it defines none of the behavior invoked
# by the B0 builder, validator, completion gate, canonicalizer, contract
# runtime, coordinator, migration handoff, return router, or authority-revision
# logic.
# Excluding it prevents unrelated later-stage exports from retroactively
# invalidating a sealed B0. Legacy packages may retain it as a stored extra;
# the required subset below remains exact and fail-closed.
B0_REQUIRED_RUNTIME_FILES = (
    "baseline.py",
    "b0_completion.py",
    "b0_implementation_identity.py",
    "canonical.py",
    "conception_revision.py",
    "contracts.py",
    "coordinator.py",
    "migration_handoff.py",
    "return_routing.py",
)
B0_LEGACY_AGGREGATE_EXPORT_IDENTITIES = ("runtime/__init__.py",)


class BaselineError(ValueError):
    """A stable, fail-closed B0 error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class BaselineBuild:
    """References returned after one immutable package is committed."""

    package_root: Path
    baseline: dict[str, Any]
    manifest: dict[str, Any]
    validation: dict[str, Any]


@dataclass(frozen=True)
class AuthorityRevisionMigrationBase:
    """A hash-verified accepted B0 whose current authority came from migration."""

    package_root: Path
    baseline_path: Path
    completion_path: Path
    manifest_path: Path
    baseline: dict[str, Any]
    completion: dict[str, Any]
    manifest: dict[str, Any]
    migration: FinalizedMigrationHandoff
    design_completions: dict[str, Path]
    source_artifacts: dict[str, Path]
    authority_artifacts: dict[str, Path]


def _fail(code: str, message: str) -> None:
    raise BaselineError(code, message)


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"cannot read JSON {path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"JSON document must be an object: {path}")
    return value


def _require_source(path: str | Path, source_root: Path, *, label: str) -> Path:
    candidate = Path(path).resolve()
    root = source_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        _fail("B0_SOURCE_OUTSIDE_ROOT", f"{label} is outside source_root: {candidate}")
    if not candidate.is_file():
        _fail("B0_SOURCE_MISSING", f"{label} does not exist: {candidate}")
    return candidate


def _resolve_source_reference(
    reference: Mapping[str, Any],
    *,
    owner_path: Path,
    source_root: Path,
    label: str,
) -> Path:
    if not isinstance(reference, Mapping):
        _fail("B0_SOURCE_REFERENCE_INVALID", f"{label} is not an object")
    path = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(path, str) or not path:
        _fail("B0_SOURCE_REFERENCE_INVALID", f"{label}.path is missing")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        _fail("B0_SOURCE_REFERENCE_INVALID", f"{label}.sha256 is invalid")
    candidate = (owner_path.parent / Path(path)).resolve()
    candidate = _require_source(candidate, source_root, label=label)
    actual = sha256_file(candidate)
    if actual != digest:
        _fail(
            "B0_SOURCE_HASH_MISMATCH",
            f"{label} expected {digest}, got {actual}",
        )
    return candidate


def _completion_artifact(
    completion: Mapping[str, Any],
    completion_path: Path,
    source_root: Path,
) -> Path:
    value = completion.get("design_artifact")
    digest = completion.get("design_artifact_sha256")
    if not isinstance(value, str) or not value:
        _fail("B0_SOURCE_COMPLETION_INVALID", "design_artifact is missing")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        _fail("B0_SOURCE_COMPLETION_INVALID", "design_artifact_sha256 is invalid")
    artifact = _require_source(
        (completion_path.parent / value).resolve(),
        source_root,
        label=f"{completion.get('stage')} design artifact",
    )
    if sha256_file(artifact) != digest:
        _fail(
            "B0_SOURCE_HASH_MISMATCH",
            f"{completion.get('stage')} design artifact hash does not match completion",
        )
    return artifact


def _validate_ready_completion(
    completion: Mapping[str, Any],
    *,
    expected_stage: str,
    run_id: str,
    completion_path: Path,
    source_root: Path,
) -> set[Path]:
    if completion.get("stage") != expected_stage:
        _fail(
            "B0_SOURCE_COMPLETION_INVALID",
            f"expected {expected_stage} completion, got {completion.get('stage')!r}",
        )
    if completion.get("run_id") != run_id:
        _fail("B0_RUN_ID_MISMATCH", f"{expected_stage} belongs to another run")
    if completion.get("status") != "ready":
        _fail("B0_SOURCE_NOT_READY", f"{expected_stage} is not ready")
    validation_ref = completion.get("validation")
    validation_path = _resolve_source_reference(
        validation_ref,
        owner_path=completion_path,
        source_root=source_root,
        label=f"{expected_stage} validation",
    )
    validation = _load_json(validation_path, code="B0_SOURCE_VALIDATION_INVALID")
    if validation_ref.get("verdict") not in {None, "ready"}:
        _fail("B0_SOURCE_NOT_READY", f"{expected_stage} validation ref is not ready")
    if (
        validation.get("verdict") != "ready"
        or validation.get("run_id") != run_id
    ):
        _fail("B0_SOURCE_NOT_READY", f"{expected_stage} validation is not ready")
    try:
        process = subprocess.run(
            [sys.executable, str(_INTERVIEW_VALIDATOR), str(completion_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(
            "B0_SOURCE_COMPLETION_INVALID",
            f"official interview completion validator could not run: {error}",
        )
    if process.returncode != 0:
        detail = (process.stdout or process.stderr).strip()
        _fail(
            "B0_SOURCE_COMPLETION_INVALID",
            f"{expected_stage} failed official interview validation: {detail}",
        )
    bound = {completion_path, validation_path}
    for field in (
        "run_state",
        "report",
        "semantic_review",
        "control_projection",
        "fact_dependency_register",
    ):
        reference = completion.get(field)
        if reference is not None:
            bound.add(
                _resolve_source_reference(
                    reference,
                    owner_path=completion_path,
                    source_root=source_root,
                    label=f"{expected_stage} {field}",
                )
            )
    return bound


def _extract_markdown_controls(path: Path, domain: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        _fail("B0_CONTROL_EXTRACTION_FAILED", f"cannot read {path}: {error}")
    headings: list[tuple[int, int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = _CONTROL_HEADING.fullmatch(line.strip())
        if match:
            headings.append((index, len(match.group("marks")), match))
    controls: list[dict[str, Any]] = []
    for position, (start, level, match) in enumerate(headings):
        end = len(lines)
        for next_start, next_level, _ in headings[position + 1 :]:
            if next_level <= level:
                end = next_start
                break
        body = "\n".join(lines[start + 1 : end]).strip()
        if not body:
            _fail(
                "B0_CONTROL_EVIDENCE_MISSING",
                f"{domain} {match.group('id')} has no section body",
            )
        controls.append(
            {
                "id": match.group("id"),
                "hardness": match.group("hardness"),
                "heading": line_heading(match),
                "value": body,
            }
        )
    return controls


def line_heading(match: re.Match[str]) -> str:
    """Return the exact Markdown heading title without the ``#`` prefix."""

    return (
        f"[{match.group('id')}][{match.group('hardness')}] "
        f"{match.group('title')}"
    )


def _extract_json_controls(path: Path) -> list[dict[str, Any]]:
    document = _load_json(path, code="B0_CONTROL_EXTRACTION_FAILED")
    raw_controls = document.get("controls")
    if not isinstance(raw_controls, list):
        return []
    controls: list[dict[str, Any]] = []
    for index, item in enumerate(raw_controls):
        if not isinstance(item, Mapping):
            _fail(
                "B0_CONTROL_EXTRACTION_FAILED",
                f"controls[{index}] is not an object",
            )
        if set(item) != {"id", "hardness", "heading", "value"}:
            _fail(
                "B0_CONTROL_EXTRACTION_FAILED",
                f"controls[{index}] must contain exactly id/hardness/heading/value",
            )
        controls.append(dict(item))
    return controls


def extract_controls(path: str | Path, domain: str) -> list[dict[str, Any]]:
    """Independently extract explicit controls from one authority artifact.

    Markdown controls use ``## [ID][hardness] Exact title`` followed by a
    non-empty section body.  JSON artifacts use a closed top-level ``controls``
    array.  No natural-language inference or implicit heading promotion occurs.
    """

    artifact = Path(path)
    controls = (
        _extract_json_controls(artifact)
        if artifact.suffix.lower() == ".json"
        else _extract_markdown_controls(artifact, domain)
    )
    if not controls:
        _fail("B0_CONTROL_EVIDENCE_MISSING", f"{domain} has no explicit controls")
    prefix = DOMAIN_PREFIX[domain] + "-"
    seen: set[str] = set()
    for item in controls:
        control_id = item.get("id")
        if not isinstance(control_id, str) or not control_id.startswith(prefix):
            _fail(
                "B0_CONTROL_DOMAIN_MISMATCH",
                f"{domain} control id must start with {prefix}: {control_id!r}",
            )
        if control_id in seen:
            _fail("B0_CONTROL_CONFLICT", f"duplicate control id: {control_id}")
        seen.add(control_id)
        if item.get("hardness") not in HARDNESS:
            _fail("B0_CONTROL_EXTRACTION_FAILED", f"{control_id} hardness is invalid")
        if not isinstance(item.get("heading"), str) or not item["heading"].strip():
            _fail("B0_CONTROL_EVIDENCE_MISSING", f"{control_id} heading is missing")
        if item.get("value") in (None, "", [], {}):
            _fail("B0_CONTROL_EVIDENCE_MISSING", f"{control_id} value is missing")
    return controls


def _source_key(path: Path, source_root: Path) -> str:
    return path.resolve().relative_to(source_root.resolve()).as_posix()


def _staged_path(source_path: Path, source_root: Path, staging_root: Path) -> Path:
    return staging_root / "sources" / _source_key(source_path, source_root)


def _staged_reference(
    source_path: Path, source_root: Path, staging_root: Path
) -> dict[str, str]:
    return artifact_reference(
        _staged_path(source_path, source_root, staging_root), root=staging_root
    )


def _copy_sources(
    source_paths: Iterable[Path], source_root: Path, staging_root: Path
) -> None:
    for source in sorted(set(source_paths), key=lambda item: _source_key(item, source_root)):
        target = _staged_path(source, source_root, staging_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256_file(source) != sha256_file(target):
            _fail("B0_COPY_MISMATCH", f"byte copy changed {source}")


def _fact_dependencies(
    register: Mapping[str, Any],
    *,
    register_path: Path,
    source_root: Path,
) -> tuple[list[dict[str, Any]], set[Path]]:
    raw = register.get("fact_dependencies")
    if not isinstance(raw, list) or not raw:
        _fail("B0_FACT_REGISTER_INVALID", "fact_dependencies must be non-empty")
    result: list[dict[str, Any]] = []
    bound_paths: set[Path] = {register_path}
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            _fail("B0_FACT_REGISTER_INVALID", f"fact_dependencies[{index}] is invalid")
        fact = copy.deepcopy(dict(item))
        fact_id = fact.get("id")
        if not isinstance(fact_id, str) or not fact_id:
            _fail("B0_FACT_REGISTER_INVALID", f"fact_dependencies[{index}].id missing")
        if fact_id in seen:
            _fail("B0_FACT_CONFLICT", f"duplicate fact dependency: {fact_id}")
        seen.add(fact_id)
        status = fact.get("status")
        if status == "open" and fact.get("blocking") is not False:
            _fail(
                "B0_STRUCTURAL_FACT_UNRESOLVED",
                f"{fact_id} is structural or otherwise blocking",
            )
        if status == "adopted":
            for field in ("research_package", "adoption_record"):
                path = _resolve_source_reference(
                    fact.get(field),
                    owner_path=register_path,
                    source_root=source_root,
                    label=f"{fact_id}.{field}",
                )
                bound_paths.add(path)
                fact[field] = path
        elif status not in {"not_applicable", "open"}:
            _fail("B0_FACT_REGISTER_INVALID", f"{fact_id} has invalid status {status!r}")
        result.append(fact)
    return result, bound_paths


def _project_fact_references(
    facts: Sequence[Mapping[str, Any]],
    source_root: Path,
    staging_root: Path,
) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    for value in facts:
        item = copy.deepcopy(dict(value))
        if item["status"] == "adopted":
            for field in ("research_package", "adoption_record"):
                item[field] = _staged_reference(
                    Path(item[field]), source_root, staging_root
                )
        projected.append(item)
    return projected


def _assert_ref_targets(
    reference: Mapping[str, Any],
    *,
    owner_path: Path,
    expected_path: Path,
    source_root: Path,
    label: str,
) -> None:
    actual = _resolve_source_reference(
        reference,
        owner_path=owner_path,
        source_root=source_root,
        label=label,
    )
    if actual != expected_path.resolve():
        _fail("B0_SOURCE_CHAIN_MISMATCH", f"{label} binds {actual}, expected {expected_path}")


def _validate_source_chain(
    *,
    run_id: str,
    source_root: Path,
    source_interview_state: Path,
    design_completions: Mapping[str, Path],
    v1_completion_path: Path,
    v2_completion_path: Path,
    approval_path: Path,
    fact_register_path: Path,
) -> tuple[
    dict[str, Path], dict[str, Path], set[Path], list[dict[str, Any]]
]:
    source_paths: set[Path] = {
        source_interview_state,
        v1_completion_path,
        v2_completion_path,
        approval_path,
        fact_register_path,
    }
    artifacts: dict[str, Path] = {}
    authority_artifacts: dict[str, Path] = {}
    completions: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        completion_path = design_completions[domain]
        completion = _load_json(
            completion_path, code="B0_SOURCE_COMPLETION_INVALID"
        )
        source_paths.update(
            _validate_ready_completion(
                completion,
                expected_stage=domain,
                run_id=run_id,
                completion_path=completion_path,
                source_root=source_root,
            )
        )
        artifact = _completion_artifact(completion, completion_path, source_root)
        artifacts[domain] = artifact
        authority_artifacts[domain] = _resolve_source_reference(
            completion.get("control_projection"),
            owner_path=completion_path,
            source_root=source_root,
            label=f"{domain} control projection",
        )
        completions[domain] = completion
        source_paths.add(artifact)

    state = _load_json(source_interview_state, code="B0_SOURCE_STATE_INVALID")
    if state.get("run_id") != run_id or state.get("active_return") is not None:
        _fail(
            "B0_SOURCE_STATE_INVALID",
            "source interview state must match run_id and have no active return",
        )
    current = state.get("current_interview_completions")
    if not isinstance(current, Mapping) or set(current) != set(DOMAINS):
        _fail(
            "B0_SOURCE_STATE_INVALID",
            "source interview state must bind exactly I0-I5",
        )
    for domain in DOMAINS:
        _assert_ref_targets(
            current[domain],
            owner_path=source_interview_state,
            expected_path=design_completions[domain],
            source_root=source_root,
            label=f"source state {domain}",
        )

    v1 = _load_json(v1_completion_path, code="B0_SOURCE_COMPLETION_INVALID")
    source_paths.update(
        _validate_ready_completion(
            v1,
            expected_stage="V1",
            run_id=run_id,
            completion_path=v1_completion_path,
            source_root=source_root,
        )
    )
    source_paths.add(_completion_artifact(v1, v1_completion_path, source_root))
    v1_inputs = v1.get("input_completions")
    if not isinstance(v1_inputs, list) or len(v1_inputs) != len(DOMAINS):
        _fail("B0_SOURCE_CHAIN_MISMATCH", "V1 must bind exactly I0-I5 completions")
    for domain, reference in zip(DOMAINS, v1_inputs):
        _assert_ref_targets(
            reference,
            owner_path=v1_completion_path,
            expected_path=design_completions[domain],
            source_root=source_root,
            label=f"V1 input {domain}",
        )
    _assert_ref_targets(
        v1.get("fact_dependency_register"),
        owner_path=v1_completion_path,
        expected_path=fact_register_path,
        source_root=source_root,
        label="V1 fact dependency register",
    )

    v2 = _load_json(v2_completion_path, code="B0_SOURCE_COMPLETION_INVALID")
    source_paths.update(
        _validate_ready_completion(
            v2,
            expected_stage="V2",
            run_id=run_id,
            completion_path=v2_completion_path,
            source_root=source_root,
        )
    )
    v2_inputs = v2.get("input_completions")
    if not isinstance(v2_inputs, list) or len(v2_inputs) != 1:
        _fail("B0_SOURCE_CHAIN_MISMATCH", "V2 must bind exactly the current V1")
    _assert_ref_targets(
        v2_inputs[0],
        owner_path=v2_completion_path,
        expected_path=v1_completion_path,
        source_root=source_root,
        label="V2 input V1",
    )
    v2_artifact = _completion_artifact(v2, v2_completion_path, source_root)
    source_paths.add(v2_artifact)

    approval = _load_json(approval_path, code="B0_SOURCE_APPROVAL_INVALID")
    if (
        approval.get("harness") != "novel-conception-interview"
        or
        approval.get("run_id") != run_id
        or approval.get("approval_scope") != "V2"
        or approval.get("decision") != "approved"
        or approval.get("record_assurance") != "self_recorded"
    ):
        _fail("B0_SOURCE_NOT_APPROVED", "current V2 is not explicitly approved")
    approval_record = approval.get("approval_record")
    if (
        not isinstance(approval_record, Mapping)
        or not isinstance(approval_record.get("event_seq"), int)
        or approval_record["event_seq"] < 1
        or not isinstance(approval_record.get("text"), str)
        or not approval_record["text"].strip()
    ):
        _fail(
            "B0_SOURCE_NOT_APPROVED",
            "V2 approval lacks a non-empty self-recorded approval event",
        )
    _assert_ref_targets(
        approval.get("review_brief"),
        owner_path=approval_path,
        expected_path=v2_artifact,
        source_root=source_root,
        label="V2 author approval review brief",
    )

    register = _load_json(fact_register_path, code="B0_FACT_REGISTER_INVALID")
    if register.get("run_id") != run_id or register.get("status") != "ready":
        _fail("B0_FACT_REGISTER_INVALID", "fact register is not ready for this run")
    facts, fact_paths = _fact_dependencies(
        register,
        register_path=fact_register_path,
        source_root=source_root,
    )
    source_paths.update(fact_paths)
    return artifacts, authority_artifacts, source_paths, facts


def _canonical_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8", newline="")


def _required_implementation_catalog(
    runtime: ContractRuntime,
) -> dict[str, Path]:
    runtime_directory = Path(__file__).resolve().parent
    catalog = {
        f"runtime/{name}": runtime_directory / name
        for name in B0_REQUIRED_RUNTIME_FILES
    }
    catalog["interview/validate_stage_completion.py"] = _INTERVIEW_VALIDATOR
    catalog["interview/stage-completion.schema.json"] = (
        _INTERVIEW_VALIDATOR.parents[1]
        / "schemas"
        / "stage-completion.schema.json"
    )
    runtime.check_all_schemas()
    for name in B0_SCHEMA_DEPENDENCIES:
        catalog[f"schemas/{name}"] = runtime.schema_dir / name
    for identity, path in catalog.items():
        if not path.is_file():
            _fail("B0_IMPLEMENTATION_MISSING", f"{identity} is missing: {path}")
    return catalog


def _validation_report(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "B0",
        "verdict": "ready",
        "checks": [
            "source-chain-approved-and-hash-bound",
            "six-domain-control-extraction-and-set-equality",
            "fact-dependencies-closed",
            "baseline-schema-valid",
        ],
        "errors": [],
    }


def _coverage_markdown(registry: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# B0 control coverage",
        "",
        "| ID | Domain | Hardness | Exact heading | Value SHA-256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in registry:
        heading = str(item["heading"]).replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | {item['domain']} | {item['hardness']} | "
            f"{heading} | `{item['value_sha256']}` |"
        )
    return "\n".join(lines) + "\n"


def _authority_revision_material(
    revision_root: Path,
    finalization_path: Path,
    *,
    run_id: str,
    runtime: ContractRuntime,
) -> tuple[dict[str, Any], dict[str, Path], Path, Path]:
    """Validate one fork and resolve its effective and current-state material."""

    root = revision_root.resolve()
    try:
        finalization_path.resolve().relative_to(root)
    except ValueError:
        _fail("B0_AUTHORITY_REVISION_INVALID", "finalization is outside revision root")
    finalization = _load_json(
        finalization_path, code="B0_AUTHORITY_REVISION_INVALID"
    )
    bootstrap_state_path = root / "state" / "revision-000.json"
    if not bootstrap_state_path.is_file():
        _fail("B0_AUTHORITY_REVISION_INVALID", "bootstrap revision-000 is missing")
    try:
        from .conception_revision import validate_conception_revision_run

        revision_context = validate_conception_revision_run(root, runtime=runtime)
    except (ValueError, OSError) as error:
        _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    if revision_context.finalization.reference != artifact_reference(
        finalization_path, root=root
    ):
        _fail("B0_AUTHORITY_REVISION_INVALID", "bootstrap finalization changed")
    try:
        runtime.validate(finalization, "authority-revision-finalization.schema.json")
    except ContractValidationError as error:
        _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    if finalization.get("run_id") != run_id or finalization.get("author_approved_bytes") is not False:
        _fail("B0_AUTHORITY_REVISION_INVALID", "run or author byte authority mismatch")
    try:
        patch_path = verify_artifact_reference(finalization["patch_plan"], root=root)
        review_path = verify_artifact_reference(finalization["semantic_review"], root=root)
        verify_artifact_reference(finalization["directive_binding"], root=root)
        verify_artifact_reference(finalization["evidence_index"], root=root)
        parent_run_path = verify_artifact_reference(
            finalization["parent_run"], root=root
        )
        for reference in finalization["base_artifacts"] + finalization["effective_artifacts"]:
            verify_artifact_reference(reference, root=root)
    except ValueError as error:
        _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    patch = _load_json(patch_path, code="B0_AUTHORITY_REVISION_INVALID")
    review = _load_json(review_path, code="B0_AUTHORITY_REVISION_INVALID")
    try:
        runtime.validate(patch, "authority-revision-patch-plan.schema.json")
        runtime.validate(review, "authority-revision-semantic-review.schema.json")
    except ContractValidationError as error:
        _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    expected_ids = [
        "CAU-AUDIT-BOUNDARY",
        "CAU-GLOBAL-SPINE",
        "CAU-MAJOR-NODES",
        "CHR-GU-HENG-MEMORY",
        "CHR-ROLE-TIERS",
        "NAR-FAIRNESS",
        "NAR-POV-ARCHITECTURE",
    ]
    if (
        review.get("candidate_material_sha256")
        != patch.get("candidate_material_sha256")
        or review.get("producer") != patch.get("producer")
        or review.get("covered_ids") != expected_ids
        or review.get("item_reviews")
        != [
            {"source_id": source_id, "verdict": "pass", "findings": []}
            for source_id in expected_ids
        ]
        or review.get("verdict") != "pass"
        or review.get("reviewer_produced_patch") is not False
        or any(
            review.get("reviewer", {}).get(field)
            == review.get("producer", {}).get(field)
            for field in ("actor_id", "session_id", "implementation_sha256")
        )
    ):
        _fail("B0_AUTHORITY_REVISION_INVALID", "semantic review binding failed")
    effective: dict[str, Path] = {}
    for artifact in patch.get("artifacts", []):
        domain = artifact.get("domain")
        if domain in effective:
            _fail("B0_AUTHORITY_REVISION_INVALID", f"duplicate domain {domain}")
        try:
            effective[str(domain)] = verify_artifact_reference(
                artifact["effective_artifact"], root=root
            )
        except (KeyError, ValueError) as error:
            _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    if set(effective) != {"I3", "I4", "I5"}:
        _fail("B0_AUTHORITY_REVISION_INVALID", "effective projections must be I3-I5")
    if (
        [item["base_artifact"] for item in patch["artifacts"]]
        != finalization["base_artifacts"]
        or [item["effective_artifact"] for item in patch["artifacts"]]
        != finalization["effective_artifacts"]
    ):
        _fail("B0_AUTHORITY_REVISION_INVALID", "finalization artifact lists changed")
    bootstrap_state = _load_json(
        bootstrap_state_path, code="B0_AUTHORITY_REVISION_INVALID"
    )
    try:
        runtime.validate(bootstrap_state, "autonomous-run-state.schema.json")
    except ContractValidationError as error:
        _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
    if (
        bootstrap_state.get("run_id") != run_id
        or bootstrap_state.get("source_kind") != "authority_revision"
        or bootstrap_state.get("source_interview_state")
        != finalization.get("parent_run")
        or bootstrap_state.get("authority_revision")
        != artifact_reference(finalization_path, root=root)
    ):
        _fail(
            "B0_SOURCE_STATE_MISMATCH",
            "authority bootstrap does not bind finalization.parent_run",
        )
    return finalization, effective, parent_run_path, bootstrap_state_path


def _authority_revision_gate_state_chain(
    revision_root: Path,
    *,
    input_gate: Mapping[str, Any],
    finalization: Mapping[str, Any],
    finalization_path: Path,
    bootstrap_state_path: Path,
    run_id: str,
    runtime: ContractRuntime,
    require_current_pointer: bool,
) -> list[Path]:
    """Resolve an authority B0 gate to its immutable bootstrap ancestry.

    The first B0 gate is bound directly to revision-000.  A later append-only
    B0 rebuild is issued from a descendant production state (for example after
    an S1 -> B0 return), so requiring revision-000 literally makes the recovery
    protocol impossible.  Descendants are accepted only when every state is a
    canonical, contiguous hash chain rooted at that bootstrap and preserves the
    same authority source/finalization identity.  At build time the gate must
    also bind the production run's current-state pointer, preventing stale gates
    from creating a new candidate.
    """

    root = revision_root.resolve()
    gate_reference = input_gate.get("run_state")
    if not isinstance(gate_reference, Mapping):
        _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate run_state is missing")
    gate_reference = dict(gate_reference)
    try:
        gate_state_path = verify_artifact_reference(gate_reference, root=root)
    except ValueError as error:
        _fail("B0_SOURCE_STATE_MISMATCH", str(error))
    try:
        relative = gate_state_path.relative_to(root).as_posix()
    except ValueError:
        _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate state is outside revision root")
    match = re.fullmatch(r"state/revision-(\d{3,})\.json", relative)
    if match is None:
        _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate state path is not a revision")
    gate_revision = int(match.group(1))
    if relative != f"state/revision-{gate_revision:03d}.json":
        _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate state path is noncanonical")

    finalization_reference = artifact_reference(finalization_path, root=root)
    bootstrap_reference = artifact_reference(bootstrap_state_path, root=root)
    expected_source = finalization.get("parent_run")
    paths: list[Path] = []
    previous_reference: dict[str, str] | None = None
    for revision in range(gate_revision + 1):
        path = root / "state" / f"revision-{revision:03d}.json"
        state = _load_json(path, code="B0_SOURCE_STATE_MISMATCH")
        try:
            runtime.validate(state, "autonomous-run-state.schema.json")
        except ContractValidationError as error:
            _fail("B0_SOURCE_STATE_MISMATCH", str(error))
        reference = artifact_reference(path, root=root)
        if canonical_sha256(state) != reference["sha256"]:
            _fail("B0_SOURCE_STATE_MISMATCH", f"state revision-{revision:03d} is noncanonical")
        if (
            state.get("revision") != revision
            or state.get("previous_state") != previous_reference
            or state.get("run_id") != run_id
            or state.get("source_kind") != "authority_revision"
            or state.get("source_interview_state") != expected_source
            or state.get("authority_revision") != finalization_reference
        ):
            _fail(
                "B0_SOURCE_STATE_MISMATCH",
                f"authority state revision-{revision:03d} changed bootstrap identity",
            )
        if revision == 0 and reference != bootstrap_reference:
            _fail("B0_SOURCE_STATE_MISMATCH", "authority bootstrap reference changed")
        previous_reference = reference
        paths.append(path)
    if previous_reference != gate_reference:
        _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate state does not close the revision chain")

    if require_current_pointer:
        pointer = _load_json(
            root / "orchestration" / "current-state.json",
            code="B0_SOURCE_STATE_MISMATCH",
        )
        if pointer != {"schema_version": "2.0", "state": gate_reference}:
            _fail("B0_SOURCE_STATE_MISMATCH", "B0 gate does not bind current state")
    return paths


def _authority_revision_migration_base(
    package_root: Path, *, runtime: ContractRuntime
) -> AuthorityRevisionMigrationBase:
    """Validate an accepted migration B0, including legacy baselines.

    Early B0 schema-2 packages did not persist ``source_kind``.  Presence of a
    valid ``migration_finalization`` is the only supported compatibility
    inference; absence or mixed current-source evidence fails closed.
    """

    root = package_root.resolve()
    baseline_path = root / "author-control-baseline.json"
    completion_path = root / "stage-completion.json"
    manifest_path = root / "package-manifest.json"
    validation_path = root / "validation.json"
    baseline = _load_json(baseline_path, code="B0_AUTHORITY_PARENT_INVALID")
    completion = _load_json(completion_path, code="B0_AUTHORITY_PARENT_INVALID")
    manifest = _load_json(manifest_path, code="B0_AUTHORITY_PARENT_INVALID")
    validation = _load_json(validation_path, code="B0_AUTHORITY_PARENT_INVALID")
    for path, document in (
        (baseline_path, baseline),
        (completion_path, completion),
        (manifest_path, manifest),
        (validation_path, validation),
    ):
        if path.read_bytes() != canonical_json(document).encode("utf-8"):
            _fail("B0_AUTHORITY_PARENT_INVALID", f"noncanonical {path.name}")
    completion_manifest = completion.get("manifest", {})
    completion_validation = completion.get("validation", {})
    completion_manifest_path = completion_manifest.get("path")
    completion_validation_path = completion_validation.get("path")
    try:
        runtime.validate(manifest, "package-manifest.schema.json")
        runtime.validate(completion, "stage-completion.schema.json")
        verify_manifest_integrity(manifest, root=root)
    except (ContractValidationError, ValueError) as error:
        _fail("B0_AUTHORITY_PARENT_INVALID", f"manifest: {error}")
    if (
        baseline.get("schema_version") != "2.0"
        or baseline.get("stage") != "B0"
        or baseline.get("status") != "ready"
        or baseline.get("source_kind", "compatibility_migration")
        != "compatibility_migration"
        or "migration_finalization" not in baseline
        or "authority_revision_finalization" in baseline
        or validation.get("verdict") != "ready"
        or manifest.get("stage") != "B0"
        or manifest.get("run_id") != baseline.get("run_id")
        or manifest.get("artifact_roles", {}).get("baseline")
        != artifact_reference(baseline_path, root=root)
        or manifest.get("validation") != artifact_reference(validation_path, root=root)
        or completion.get("stage") != "B0"
        or completion.get("status") != "ready"
        or completion.get("run_id") != baseline.get("run_id")
        or completion.get("source_kind", "compatibility_migration")
        != "compatibility_migration"
        or not isinstance(completion_manifest_path, str)
        or "\\" in completion_manifest_path
        or PurePosixPath(completion_manifest_path).is_absolute()
        or ".." in PurePosixPath(completion_manifest_path).parts
        or PurePosixPath(completion_manifest_path).name != manifest_path.name
        or completion_manifest.get("sha256") != sha256_file(manifest_path)
        or not isinstance(completion_validation_path, str)
        or "\\" in completion_validation_path
        or PurePosixPath(completion_validation_path).is_absolute()
        or ".." in PurePosixPath(completion_validation_path).parts
        or PurePosixPath(completion_validation_path).name != validation_path.name
        or completion_validation.get("sha256") != sha256_file(validation_path)
    ):
        _fail("B0_AUTHORITY_PARENT_INVALID", "baseline/completion/manifest chain")
    try:
        migration_path = verify_artifact_reference(
            baseline["migration_finalization"], root=root
        )
        migration = validate_finalized_migration_handoff(migration_path)
    except (KeyError, ValueError) as error:
        _fail("B0_AUTHORITY_PARENT_INVALID", f"migration finalization: {error}")
    if baseline.get("source_run_id") != migration.source_run_id:
        _fail("B0_AUTHORITY_PARENT_INVALID", "migration source_run_id changed")
    entries = baseline.get("design_artifacts")
    if not isinstance(entries, list) or len(entries) != len(DOMAINS):
        _fail("B0_AUTHORITY_PARENT_INVALID", "design artifact count")
    by_domain = {
        entry.get("domain"): entry for entry in entries if isinstance(entry, Mapping)
    }
    if set(by_domain) != set(DOMAINS) or len(by_domain) != len(entries):
        _fail("B0_AUTHORITY_PARENT_INVALID", "design domains")
    try:
        design_completions = {
            domain: verify_artifact_reference(by_domain[domain]["completion"], root=root)
            for domain in DOMAINS
        }
        source_artifacts = {
            domain: verify_artifact_reference(
                by_domain[domain].get("source_artifact", by_domain[domain]["artifact"]),
                root=root,
            )
            for domain in DOMAINS
        }
        authority_artifacts = {
            domain: verify_artifact_reference(by_domain[domain]["artifact"], root=root)
            for domain in DOMAINS
        }
        for field in (
            "run_state", "v1_completion", "v2_completion",
            "v2_author_approval", "fact_dependency_register",
        ):
            verify_artifact_reference(baseline[field], root=root)
    except (KeyError, ValueError) as error:
        _fail("B0_AUTHORITY_PARENT_INVALID", f"baseline reference: {error}")
    registry = baseline.get("control_registry")
    if not isinstance(registry, list):
        _fail("B0_AUTHORITY_PARENT_INVALID", "control registry")
    expected_registry: list[dict[str, Any]] = []
    for domain in DOMAINS:
        controls = extract_controls(authority_artifacts[domain], domain)
        if by_domain[domain].get("control_ids") != [item["id"] for item in controls]:
            _fail("B0_AUTHORITY_PARENT_INVALID", f"{domain} control ids")
        artifact_ref = copy.deepcopy(by_domain[domain]["artifact"])
        expected_registry.extend(
            {
                "id": item["id"],
                "domain": domain,
                "hardness": item["hardness"],
                "artifact": artifact_ref,
                "heading": item["heading"],
                "value_sha256": canonical_sha256(item["value"]),
            }
            for item in controls
        )
    expected_registry.sort(key=lambda item: item["id"])
    if registry != expected_registry:
        _fail("B0_AUTHORITY_PARENT_INVALID", "control registry changed")
    if (
        design_completions != migration.design_completions
        or source_artifacts != migration.source_artifacts
        or authority_artifacts != migration.control_projections
        or verify_artifact_reference(baseline["run_state"], root=root)
        != migration.source_interview_state
        or verify_artifact_reference(baseline["v1_completion"], root=root)
        != migration.v1_completion
        or verify_artifact_reference(baseline["v2_completion"], root=root)
        != migration.v2_completion
        or verify_artifact_reference(baseline["v2_author_approval"], root=root)
        != migration.v2_author_approval
        or verify_artifact_reference(baseline["fact_dependency_register"], root=root)
        != migration.fact_dependency_register
    ):
        _fail("B0_AUTHORITY_PARENT_INVALID", "migration projection changed")
    return AuthorityRevisionMigrationBase(
        package_root=root,
        baseline_path=baseline_path,
        completion_path=completion_path,
        manifest_path=manifest_path,
        baseline=baseline,
        completion=completion,
        manifest=manifest,
        migration=migration,
        design_completions=design_completions,
        source_artifacts=source_artifacts,
        authority_artifacts=authority_artifacts,
    )


def _assert_revision_over_migration_base(
    base: AuthorityRevisionMigrationBase,
    *,
    effective_artifacts: Mapping[str, Path],
) -> None:
    changed: set[str] = set()
    for domain in DOMAINS:
        before = extract_controls(base.authority_artifacts[domain], domain)
        after = (
            extract_controls(effective_artifacts[domain], domain)
            if domain in effective_artifacts
            else before
        )
        if len(before) != len(after):
            _fail("B0_AUTHORITY_PARENT_DRIFT", f"{domain} control count")
        for old, new in zip(before, after):
            if (
                old["id"] != new["id"]
                or old["hardness"] != new["hardness"]
                or old["heading"] != new["heading"]
            ):
                _fail("B0_AUTHORITY_PARENT_DRIFT", old["id"])
            if old != new:
                if old["id"] not in {
                    "CAU-AUDIT-BOUNDARY", "CAU-GLOBAL-SPINE", "CAU-MAJOR-NODES",
                    "CHR-GU-HENG-MEMORY", "CHR-ROLE-TIERS",
                    "NAR-FAIRNESS", "NAR-POV-ARCHITECTURE",
                }:
                    _fail("B0_AUTHORITY_PARENT_DRIFT", old["id"])
                changed.add(old["id"])
    if changed != {
        "CAU-AUDIT-BOUNDARY", "CAU-GLOBAL-SPINE", "CAU-MAJOR-NODES",
        "CHR-GU-HENG-MEMORY", "CHR-ROLE-TIERS",
        "NAR-FAIRNESS", "NAR-POV-ARCHITECTURE",
    }:
        _fail("B0_AUTHORITY_PARENT_DRIFT", f"changed controls: {sorted(changed)}")


def build_baseline_package(
    package_root: str | Path,
    *,
    run_id: str,
    input_gate: SealedDocument,
    source_root: str | Path | None = None,
    source_interview_state: str | Path | None = None,
    design_completions: Mapping[str, str | Path] | None = None,
    v1_completion: str | Path | None = None,
    v2_completion: str | Path | None = None,
    v2_author_approval: str | Path | None = None,
    fact_dependency_register: str | Path | None = None,
    implementation_files: Sequence[str | Path] = (),
    runtime: ContractRuntime | None = None,
    migration_handoff: FinalizedMigrationHandoff | None = None,
    authority_revision_root: str | Path | None = None,
    authority_revision_finalization: str | Path | None = None,
    authority_source_run_id: str | None = None,
    authority_parent_b0_root: str | Path | None = None,
) -> BaselineBuild:
    """Build and atomically commit one immutable, ready B0 package."""

    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("B0_PACKAGE_EXISTS", f"immutable package already exists: {destination}")
    if not run_id:
        _fail("B0_RUN_ID_MISMATCH", "run_id must be non-empty")
    contract_runtime = runtime or ContractRuntime()
    try:
        contract_runtime.validate(input_gate.data, "input-gate.schema.json")
    except ContractValidationError as error:
        _fail("B0_INPUT_GATE_INVALID", str(error))
    if (
        input_gate.data.get("target_stage") != "B0"
        or input_gate.data.get("run_id") != run_id
        or input_gate.data.get("baseline_completion") is not None
        or input_gate.data.get("upstream_completions") != []
    ):
        _fail("B0_INPUT_GATE_INVALID", "gate is not the exact B0 topology")
    if canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("B0_INPUT_GATE_INVALID", "gate reference does not bind gate body")

    verified_migration: FinalizedMigrationHandoff | None = None
    verified_revision: dict[str, Any] | None = None
    revision_migration_base: AuthorityRevisionMigrationBase | None = None
    revision_root: Path | None = None
    revision_authority_artifacts: dict[str, Path] = {}
    revision_parent_state_path: Path | None = None
    revision_bootstrap_state_path: Path | None = None
    revision_gate_state_paths: list[Path] = []
    if migration_handoff is not None and authority_revision_root is not None:
        _fail("B0_SOURCE_KIND_CONFLICT", "migration and authority revision are exclusive")
    if (authority_revision_root is None) != (authority_revision_finalization is None):
        _fail("B0_AUTHORITY_REVISION_INVALID", "root and finalization are both required")
    if authority_parent_b0_root is not None and authority_revision_root is None:
        _fail("B0_SOURCE_KIND_CONFLICT", "authority parent requires authority revision")
    source_run_id = run_id
    if migration_handoff is not None:
        verified_migration = validate_finalized_migration_handoff(
            migration_handoff.finalization_path
        )
        if verified_migration != migration_handoff:
            _fail(
                "B0_MIGRATION_HANDOFF_STALE",
                "resolved migration handoff changed after caller validation",
            )
        source_run_id = verified_migration.source_run_id
    elif authority_revision_root is not None:
        if not isinstance(authority_source_run_id, str) or not authority_source_run_id:
            _fail("B0_AUTHORITY_REVISION_INVALID", "authority_source_run_id is required")
        source_run_id = authority_source_run_id
        revision_root = Path(authority_revision_root).resolve()
        revision_finalization_path = Path(authority_revision_finalization).resolve()
        (
            verified_revision,
            revision_authority_artifacts,
            revision_parent_state_path,
            revision_bootstrap_state_path,
        ) = _authority_revision_material(
            revision_root,
            revision_finalization_path,
            run_id=run_id,
            runtime=contract_runtime,
        )
        revision_gate_state_paths = _authority_revision_gate_state_chain(
            revision_root,
            input_gate=input_gate.data,
            finalization=verified_revision,
            finalization_path=revision_finalization_path,
            bootstrap_state_path=revision_bootstrap_state_path,
            run_id=run_id,
            runtime=contract_runtime,
            require_current_pointer=True,
        )

    if authority_parent_b0_root is not None:
        revision_migration_base = _authority_revision_migration_base(
            Path(authority_parent_b0_root), runtime=contract_runtime
        )
        if source_root is not None or any(
            value is not None
            for value in (
                source_interview_state, design_completions, v1_completion,
                v2_completion, v2_author_approval, fact_dependency_register,
            )
        ):
            _fail(
                "B0_SOURCE_KIND_CONFLICT",
                "migration ancestry cannot be mixed with native source arguments",
            )
        if authority_source_run_id != revision_migration_base.baseline["source_run_id"]:
            _fail("B0_AUTHORITY_PARENT_INVALID", "authority source_run_id mismatch")
        source_run_id = revision_migration_base.baseline["source_run_id"]
        _assert_revision_over_migration_base(
            revision_migration_base,
            effective_artifacts=revision_authority_artifacts,
        )

    if revision_migration_base is not None:
        root = revision_migration_base.package_root
        parent_baseline = revision_migration_base.baseline
        state_path = verify_artifact_reference(parent_baseline["run_state"], root=root)
        completion_paths = revision_migration_base.design_completions
        v1_path = verify_artifact_reference(parent_baseline["v1_completion"], root=root)
        v2_path = verify_artifact_reference(parent_baseline["v2_completion"], root=root)
        approval_path = verify_artifact_reference(
            parent_baseline["v2_author_approval"], root=root
        )
        register_path = verify_artifact_reference(
            parent_baseline["fact_dependency_register"], root=root
        )
        artifacts = revision_migration_base.source_artifacts
        authority_artifacts = {
            **revision_migration_base.authority_artifacts,
            **revision_authority_artifacts,
        }
        raw_facts, _ = _fact_dependencies(
            _load_json(register_path, code="B0_FACT_REGISTER_INVALID"),
            register_path=register_path,
            source_root=root,
        )
        source_paths = {
            path for path in root.rglob("*") if path.is_file()
        }
    else:
        if any(
            value is None
            for value in (
                source_root, source_interview_state, design_completions,
                v1_completion, v2_completion, v2_author_approval,
                fact_dependency_register,
            )
        ):
            _fail("B0_SOURCE_CHAIN_MISMATCH", "complete source chain is required")
        root = Path(source_root).resolve()
        state_path = _require_source(
            source_interview_state, root, label="source interview state"
        )
        if not isinstance(design_completions, Mapping) or set(design_completions) != set(DOMAINS):
            _fail("B0_SOURCE_CHAIN_MISMATCH", "design_completions must be exactly I0-I5")
        completion_paths = {
            domain: _require_source(
                design_completions[domain], root, label=f"{domain} completion"
            )
            for domain in DOMAINS
        }
        v1_path = _require_source(v1_completion, root, label="V1 completion")
        v2_path = _require_source(v2_completion, root, label="V2 completion")
        approval_path = _require_source(
            v2_author_approval, root, label="V2 author approval"
        )
        register_path = _require_source(
            fact_dependency_register, root, label="fact dependency register"
        )
    if revision_migration_base is None and verified_migration is None:
        artifacts, authority_artifacts, source_paths, raw_facts = _validate_source_chain(
            run_id=source_run_id,
            source_root=root,
            source_interview_state=state_path,
            design_completions=completion_paths,
            v1_completion_path=v1_path,
            v2_completion_path=v2_path,
            approval_path=approval_path,
            fact_register_path=register_path,
        )
        if verified_revision is not None:
            authority_artifacts = {
                **authority_artifacts,
                **revision_authority_artifacts,
            }
    elif verified_migration is not None:
        if verified_migration.package_root != root:
            _fail(
                "B0_MIGRATION_HANDOFF_STALE",
                "migration package root differs from source_root",
            )
        expected_paths = {
            "state": state_path,
            "v1": v1_path,
            "v2": v2_path,
            "approval": approval_path,
            "facts": register_path,
        }
        actual_paths = {
            "state": verified_migration.source_interview_state,
            "v1": verified_migration.v1_completion,
            "v2": verified_migration.v2_completion,
            "approval": verified_migration.v2_author_approval,
            "facts": verified_migration.fact_dependency_register,
        }
        if actual_paths != expected_paths or verified_migration.design_completions != completion_paths:
            _fail(
                "B0_MIGRATION_HANDOFF_STALE",
                "B0 source arguments do not exactly match the finalized handoff",
            )
        artifacts = verified_migration.source_artifacts
        authority_artifacts = verified_migration.control_projections
        raw_facts, fact_paths = _fact_dependencies(
            _load_json(register_path, code="B0_FACT_REGISTER_INVALID"),
            register_path=register_path,
            source_root=root,
        )
        source_paths = set(verified_migration.evidence_paths) | fact_paths

    extracted: dict[str, list[dict[str, Any]]] = {
        domain: extract_controls(authority_artifacts[domain], domain)
        for domain in DOMAINS
    }
    all_ids: set[str] = set()
    for domain in DOMAINS:
        domain_ids = {item["id"] for item in extracted[domain]}
        overlap = all_ids & domain_ids
        if overlap:
            _fail("B0_CONTROL_CONFLICT", f"controls appear in multiple domains: {sorted(overlap)}")
        all_ids.update(domain_ids)

    implementation_catalog = _required_implementation_catalog(contract_runtime)
    extra_implementation_paths = [
        Path(path).resolve() for path in implementation_files
    ]
    for path in extra_implementation_paths:
        if not path.is_file():
            _fail("B0_IMPLEMENTATION_MISSING", f"implementation missing: {path}")
    for index, path in enumerate(extra_implementation_paths):
        implementation_catalog[f"extra/{index:02d}-{path.name}"] = path

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = staging_parent / "package"
    staging.mkdir()
    try:
        _copy_sources(source_paths, root, staging)
        if verified_revision is not None and revision_root is not None:
            revision_source = revision_root / "authority-revision"
            revision_destination = staging / "authority-revision"
            if not revision_source.is_dir():
                _fail("B0_AUTHORITY_REVISION_INVALID", str(revision_source))
            shutil.copytree(revision_source, revision_destination)
            if revision_bootstrap_state_path is None:
                _fail("B0_AUTHORITY_REVISION_INVALID", "bootstrap state unresolved")
            if not revision_gate_state_paths:
                _fail("B0_AUTHORITY_REVISION_INVALID", "gate state chain unresolved")
            for source_state in revision_gate_state_paths:
                state_destination = staging / source_state.relative_to(revision_root)
                state_destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_state, state_destination)
                if sha256_file(source_state) != sha256_file(state_destination):
                    _fail("B0_COPY_MISMATCH", f"authority state changed: {source_state.name}")
            pointer_source = (
                revision_root
                / "orchestration"
                / "authority-revision"
                / "current-bootstrap.json"
            )
            if not pointer_source.is_file():
                _fail("B0_AUTHORITY_REVISION_INVALID", "bootstrap pointer missing")
            pointer_destination = (
                staging
                / "orchestration"
                / "authority-revision"
                / "current-bootstrap.json"
            )
            pointer_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pointer_source, pointer_destination)
            if sha256_file(pointer_source) != sha256_file(pointer_destination):
                _fail("B0_COPY_MISMATCH", "authority bootstrap pointer changed")
        implementation_refs: list[dict[str, str]] = []
        implementation_records: list[dict[str, Any]] = []
        for identity, source in sorted(implementation_catalog.items()):
            target = staging / "implementation" / identity
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied_reference = artifact_reference(target, root=staging)
            implementation_refs.append(copied_reference)
            implementation_records.append(
                {"identity": identity, "artifact": copied_reference}
            )

        design_entries: list[dict[str, Any]] = []
        registry: list[dict[str, Any]] = []
        for domain in DOMAINS:
            if verified_revision is not None and domain in revision_authority_artifacts:
                artifact_ref = artifact_reference(
                    staging
                    / Path(
                        *PurePosixPath(
                            next(
                                item["effective_artifact"]["path"]
                                for item in _load_json(
                                    staging / "authority-revision" / "patch-plan.json",
                                    code="B0_AUTHORITY_REVISION_INVALID",
                                )["artifacts"]
                                if item["domain"] == domain
                            )
                        ).parts
                    ),
                    root=staging,
                )
            else:
                artifact_ref = _staged_reference(authority_artifacts[domain], root, staging)
            source_artifact_ref = _staged_reference(artifacts[domain], root, staging)
            controls = extracted[domain]
            design_entries.append(
                {
                    "domain": domain,
                    "completion": _staged_reference(
                        completion_paths[domain], root, staging
                    ),
                    "artifact": artifact_ref,
                    "source_artifact": source_artifact_ref,
                    "control_ids": [item["id"] for item in controls],
                }
            )
            registry.extend(
                {
                    "id": item["id"],
                    "domain": domain,
                    "hardness": item["hardness"],
                    "artifact": artifact_ref,
                    "heading": item["heading"],
                    "value_sha256": canonical_sha256(item["value"]),
                }
                for item in controls
            )
        registry.sort(key=lambda item: item["id"])
        baseline = {
            "schema_version": "2.0",
            "stage": "B0",
            "run_id": run_id,
            "source_run_id": source_run_id,
            "status": "ready",
            "source_kind": (
                "authority_revision"
                if verified_revision is not None
                else (
                    "compatibility_migration"
                    if verified_migration is not None
                    else "native"
                )
            ),
            "run_state": (
                artifact_reference(
                    staging
                    / Path(
                        *PurePosixPath(verified_revision["parent_run"]["path"]).parts
                    ),
                    root=staging,
                )
                if verified_revision is not None
                else _staged_reference(state_path, root, staging)
            ),
            "design_artifacts": design_entries,
            "v1_completion": _staged_reference(v1_path, root, staging),
            "v2_completion": _staged_reference(v2_path, root, staging),
            "v2_author_approval": _staged_reference(approval_path, root, staging),
            "fact_dependency_register": _staged_reference(
                register_path, root, staging
            ),
            "control_registry": registry,
            "fact_dependencies": _project_fact_references(
                raw_facts, root, staging
            ),
            "open_items": [
                item["id"] for item in registry if item["hardness"] == "author_open"
            ],
        }
        if verified_migration is not None:
            baseline["migration_finalization"] = _staged_reference(
                verified_migration.finalization_path, root, staging
            )
        if verified_revision is not None:
            baseline["authority_revision_finalization"] = artifact_reference(
                staging / "authority-revision" / "finalization.json", root=staging
            )
            baseline["base_design_artifacts"] = copy.deepcopy(
                verified_revision["base_artifacts"]
            )
            baseline["effective_design_artifacts"] = copy.deepcopy(
                verified_revision["effective_artifacts"]
            )
            baseline["base_source_kind"] = (
                "compatibility_migration"
                if revision_migration_base is not None
                else "native"
            )
        if revision_migration_base is not None:
            baseline["base_migration_finalization"] = _staged_reference(
                verify_artifact_reference(
                    revision_migration_base.baseline["migration_finalization"],
                    root=revision_migration_base.package_root,
                ),
                root,
                staging,
            )
            baseline["parent_b0_baseline"] = _staged_reference(
                revision_migration_base.baseline_path, root, staging
            )
            baseline["parent_b0_completion"] = _staged_reference(
                revision_migration_base.completion_path, root, staging
            )
            baseline["parent_b0_manifest"] = _staged_reference(
                revision_migration_base.manifest_path, root, staging
            )
        try:
            contract_runtime.validate(
                baseline, "author-control-baseline.schema.json"
            )
        except ContractValidationError as error:
            _fail("B0_BASELINE_SCHEMA_INVALID", str(error))

        _canonical_write(staging / "input-gate.json", input_gate.data)
        _canonical_write(staging / "author-control-baseline.json", baseline)
        (staging / "control-coverage.md").write_text(
            _coverage_markdown(registry), encoding="utf-8", newline=""
        )
        execution = {
            "schema_version": "2.0",
            "run_id": run_id,
            "stage": "B0",
            "operation": "deterministic-author-control-baseline",
            "input_gate": artifact_reference(staging / "input-gate.json", root=staging),
            "source_artifacts": [
                artifact_reference(path, root=staging)
                for path in sorted(
                    (staging / "sources").rglob("*"),
                    key=lambda item: item.as_posix(),
                )
                if path.is_file()
            ],
            "implementation": implementation_refs,
            "implementation_catalog": implementation_records,
            "output_sha256": canonical_sha256(baseline),
        }
        _canonical_write(staging / "baseline-execution.json", execution)
        validation = _validation_report(run_id)
        _canonical_write(staging / "validation.json", validation)

        files = [
            artifact_reference(path, root=staging)
            for path in sorted(staging.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
        ]
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": run_id,
            "stage": "B0",
            "package_profile": "baseline",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "baseline": by_path["author-control-baseline.json"],
                "control_coverage": by_path["control-coverage.md"],
                "execution_record": by_path["baseline-execution.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        if verified_revision is not None:
            manifest["source_kind"] = "authority_revision"
            manifest["authority_revision"] = copy.deepcopy(
                baseline["authority_revision_finalization"]
            )
            manifest["base_source_kind"] = baseline["base_source_kind"]
        if revision_migration_base is not None:
            manifest["base_migration_finalization"] = copy.deepcopy(
                baseline["base_migration_finalization"]
            )
            manifest["parent_b0_baseline"] = copy.deepcopy(
                baseline["parent_b0_baseline"]
            )
            manifest["parent_b0_completion"] = copy.deepcopy(
                baseline["parent_b0_completion"]
            )
            manifest["parent_b0_manifest"] = copy.deepcopy(
                baseline["parent_b0_manifest"]
            )
        try:
            contract_runtime.validate(manifest, "package-manifest.schema.json")
            verify_manifest_integrity(manifest, root=staging)
        except (ContractValidationError, ValueError) as error:
            _fail("B0_MANIFEST_INVALID", str(error))
        _canonical_write(staging / "package-manifest.json", manifest)

        destination.parent.mkdir(parents=True, exist_ok=True)
        staging.replace(destination)
    except Exception:
        shutil.rmtree(staging_parent, ignore_errors=True)
        raise
    shutil.rmtree(staging_parent, ignore_errors=True)
    return BaselineBuild(
        package_root=destination,
        baseline=copy.deepcopy(baseline),
        manifest=copy.deepcopy(manifest),
        validation=copy.deepcopy(validation),
    )


def build_baseline_from_handoff(
    package_root: str | Path,
    *,
    production_run_id: str,
    input_gate: SealedDocument,
    migration_finalization: str | Path,
    implementation_files: Sequence[str | Path] = (),
    runtime: ContractRuntime | None = None,
) -> BaselineBuild:
    """Build B0 from one finalized, newly author-approved migration package.

    ``production_run_id`` identifies the autonomous run and is validated by
    the B0 gate.  The original interview ``source_run_id`` remains immutable
    inside the finalized handoff and is used only to validate that source
    chain.  No caller-provided path mapping or inferred control is accepted.
    """

    handoff = validate_finalized_migration_handoff(migration_finalization)
    return build_baseline_package(
        package_root,
        run_id=production_run_id,
        input_gate=input_gate,
        source_root=handoff.package_root,
        source_interview_state=handoff.source_interview_state,
        design_completions=handoff.design_completions,
        v1_completion=handoff.v1_completion,
        v2_completion=handoff.v2_completion,
        v2_author_approval=handoff.v2_author_approval,
        fact_dependency_register=handoff.fact_dependency_register,
        implementation_files=implementation_files,
        runtime=runtime,
        migration_handoff=handoff,
    )


def build_baseline_from_authority_revision(
    package_root: str | Path,
    *,
    authority_revision_finalization: str | Path,
    authority_source_run_id: str,
    authority_parent_b0_root: str | Path | None = None,
    **arguments: Any,
) -> BaselineBuild:
    """Build B0 from a completed authority-revision fork.

    A native base supplies the old source chain through ``arguments``.  A
    finalized-migration base supplies only ``authority_parent_b0_root``; mixing
    those two ancestry modes is rejected while the new current source remains
    uniquely ``authority_revision``.
    """

    finalization = Path(authority_revision_finalization).resolve()
    if (
        finalization.name != "finalization.json"
        or finalization.parent.name != "authority-revision"
    ):
        _fail("B0_AUTHORITY_REVISION_INVALID", str(finalization))
    forbidden = {
        "migration_handoff",
        "authority_revision_root",
        "authority_revision_finalization",
        "authority_source_run_id",
        "authority_parent_b0_root",
    } & set(arguments)
    if forbidden:
        _fail("B0_SOURCE_KIND_CONFLICT", str(sorted(forbidden)))
    return build_baseline_package(
        package_root,
        authority_revision_root=finalization.parent.parent,
        authority_revision_finalization=finalization,
        authority_source_run_id=authority_source_run_id,
        authority_parent_b0_root=authority_parent_b0_root,
        **arguments,
    )


def validate_baseline_package(
    package_root: str | Path,
    *,
    runtime: ContractRuntime | None = None,
) -> dict[str, Any]:
    """Read-only semantic, schema, source-evidence, and hash revalidation."""

    root = Path(package_root).resolve()
    contract_runtime = runtime or ContractRuntime()
    baseline = _load_json(
        root / "author-control-baseline.json", code="B0_BASELINE_MISSING"
    )
    manifest = _load_json(root / "package-manifest.json", code="B0_MANIFEST_INVALID")
    stored_validation = _load_json(
        root / "validation.json", code="B0_VALIDATION_MISSING"
    )
    try:
        contract_runtime.validate(baseline, "author-control-baseline.schema.json")
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        verify_manifest_integrity(manifest, root=root)
    except (ContractValidationError, ValueError) as error:
        _fail("B0_PACKAGE_INTEGRITY_FAILED", str(error))
    if manifest.get("run_id") != baseline.get("run_id"):
        _fail("B0_RUN_ID_MISMATCH", "manifest and baseline run_id differ")
    if manifest["artifact_roles"]["baseline"] != artifact_reference(
        root / "author-control-baseline.json", root=root
    ):
        _fail("B0_MANIFEST_INVALID", "manifest baseline role does not bind baseline")
    if baseline.get("source_kind") == "authority_revision":
        expected_manifest_lineage = {
            "source_kind": "authority_revision",
            "authority_revision": baseline["authority_revision_finalization"],
            "base_source_kind": baseline["base_source_kind"],
        }
        for field in (
            "base_migration_finalization", "parent_b0_baseline",
            "parent_b0_completion", "parent_b0_manifest",
        ):
            if field in baseline:
                expected_manifest_lineage[field] = baseline[field]
        if any(
            manifest.get(field) != value
            for field, value in expected_manifest_lineage.items()
        ):
            _fail("B0_MANIFEST_INVALID", "authority ancestry changed")

    migration_reference = baseline.get("migration_finalization")
    revision_reference = baseline.get("authority_revision_finalization")
    verified_migration: FinalizedMigrationHandoff | None = None
    authority_parent: AuthorityRevisionMigrationBase | None = None
    if baseline.get("source_kind") == "compatibility_migration":
        if migration_reference is None or revision_reference is not None:
            _fail("B0_SOURCE_KIND_CONFLICT", "migration evidence mismatch")
        try:
            migration_path = verify_artifact_reference(migration_reference, root=root)
        except ValueError as error:
            _fail("B0_MIGRATION_HANDOFF_STALE", str(error))
        verified_migration = validate_finalized_migration_handoff(migration_path)
        if verified_migration.source_run_id != baseline["source_run_id"]:
            _fail("B0_MIGRATION_SOURCE_MISMATCH", "source_run_id changed")
    elif baseline.get("source_kind") == "authority_revision":
        if revision_reference is None or migration_reference is not None:
            _fail("B0_SOURCE_KIND_CONFLICT", "authority revision evidence mismatch")
        try:
            revision_path = verify_artifact_reference(revision_reference, root=root)
        except ValueError as error:
            _fail("B0_AUTHORITY_REVISION_INVALID", str(error))
        (
            finalization,
            effective,
            revision_parent_state_path,
            revision_bootstrap_state_path,
        ) = _authority_revision_material(
            root,
            revision_path,
            run_id=baseline["run_id"],
            runtime=contract_runtime,
        )
        if baseline.get("run_state") != artifact_reference(
            revision_parent_state_path, root=root
        ):
            _fail(
                "B0_SOURCE_STATE_MISMATCH",
                "authority baseline does not bind finalization.parent_run",
            )
        authority_input_gate = _load_json(
            root / "input-gate.json", code="B0_INPUT_GATE_INVALID"
        )
        _authority_revision_gate_state_chain(
            root,
            input_gate=authority_input_gate,
            finalization=finalization,
            finalization_path=revision_path,
            bootstrap_state_path=revision_bootstrap_state_path,
            run_id=baseline["run_id"],
            runtime=contract_runtime,
            require_current_pointer=False,
        )
        if (
            baseline.get("base_design_artifacts") != finalization["base_artifacts"]
            or baseline.get("effective_design_artifacts") != finalization["effective_artifacts"]
        ):
            _fail("B0_AUTHORITY_REVISION_INVALID", "base/effective lineage changed")
        entries = {entry["domain"]: entry for entry in baseline["design_artifacts"]}
        for domain, path in effective.items():
            if verify_artifact_reference(entries[domain]["artifact"], root=root) != path:
                _fail("B0_AUTHORITY_REVISION_INVALID", f"{domain} effective artifact changed")
        base_source_kind = baseline.get("base_source_kind")
        ancestry_fields = (
            "base_migration_finalization", "parent_b0_baseline",
            "parent_b0_completion", "parent_b0_manifest",
        )
        if base_source_kind == "native":
            if any(field in baseline for field in ancestry_fields):
                _fail("B0_SOURCE_KIND_CONFLICT", "native ancestry has migration evidence")
        elif base_source_kind == "compatibility_migration":
            try:
                parent_baseline_path = verify_artifact_reference(
                    baseline["parent_b0_baseline"], root=root
                )
                authority_parent = _authority_revision_migration_base(
                    parent_baseline_path.parent, runtime=contract_runtime
                )
                if (
                    artifact_reference(authority_parent.completion_path, root=root)
                    != baseline["parent_b0_completion"]
                    or artifact_reference(authority_parent.manifest_path, root=root)
                    != baseline["parent_b0_manifest"]
                    or artifact_reference(
                        authority_parent.migration.finalization_path, root=root
                    ) != baseline["base_migration_finalization"]
                ):
                    _fail("B0_AUTHORITY_PARENT_INVALID", "ancestry reference changed")
            except (KeyError, ValueError) as error:
                _fail("B0_AUTHORITY_PARENT_INVALID", str(error))
            _assert_revision_over_migration_base(
                authority_parent, effective_artifacts=effective
            )
            parent_entries = {
                entry["domain"]: entry
                for entry in authority_parent.baseline["design_artifacts"]
            }
            for domain in DOMAINS:
                if (
                    entries[domain]["completion"]
                    != artifact_reference(
                        authority_parent.design_completions[domain], root=root
                    )
                    or entries[domain].get("source_artifact")
                    != artifact_reference(
                        authority_parent.source_artifacts[domain], root=root
                    )
                    or (
                        domain in {"I0", "I1", "I2"}
                        and entries[domain]["artifact"]
                        != artifact_reference(
                            authority_parent.authority_artifacts[domain], root=root
                        )
                    )
                    or entries[domain]["control_ids"]
                    != parent_entries[domain]["control_ids"]
                ):
                    _fail("B0_AUTHORITY_PARENT_DRIFT", domain)
            parent_top = authority_parent.baseline
            for field in (
                "v1_completion", "v2_completion",
                "v2_author_approval", "fact_dependency_register",
            ):
                parent_path = verify_artifact_reference(
                    parent_top[field], root=authority_parent.package_root
                )
                if baseline[field] != artifact_reference(parent_path, root=root):
                    _fail("B0_AUTHORITY_PARENT_DRIFT", field)
            if baseline.get("source_run_id") != parent_top.get("source_run_id"):
                _fail("B0_AUTHORITY_PARENT_DRIFT", "source_run_id")
        else:
            _fail("B0_SOURCE_KIND_CONFLICT", f"base source {base_source_kind!r}")
    elif baseline.get("source_kind") != "native":
        _fail("B0_SOURCE_KIND_CONFLICT", str(baseline.get("source_kind")))
    elif baseline["source_run_id"] != baseline["run_id"]:
        _fail(
            "B0_MIGRATION_HANDOFF_MISSING",
            "a cross-run baseline requires finalized migration evidence",
        )

    resolved_design_completions = {
        entry["domain"]: verify_artifact_reference(entry["completion"], root=root)
        for entry in baseline["design_artifacts"]
    }
    if verified_migration is not None:
        entries = {entry["domain"]: entry for entry in baseline["design_artifacts"]}
        resolved_source_artifacts = {
            domain: verify_artifact_reference(entries[domain]["source_artifact"], root=root)
            for domain in DOMAINS
        }
        resolved_authority_artifacts = {
            domain: verify_artifact_reference(entries[domain]["artifact"], root=root)
            for domain in DOMAINS
        }
        exact_bindings = (
            resolved_design_completions == verified_migration.design_completions
            and resolved_source_artifacts == verified_migration.source_artifacts
            and resolved_authority_artifacts == verified_migration.control_projections
            and verify_artifact_reference(baseline["run_state"], root=root)
            == verified_migration.source_interview_state
            and verify_artifact_reference(baseline["v1_completion"], root=root)
            == verified_migration.v1_completion
            and verify_artifact_reference(baseline["v2_completion"], root=root)
            == verified_migration.v2_completion
            and verify_artifact_reference(baseline["v2_author_approval"], root=root)
            == verified_migration.v2_author_approval
            and verify_artifact_reference(
                baseline["fact_dependency_register"], root=root
            )
            == verified_migration.fact_dependency_register
        )
        if not exact_bindings:
            _fail(
                "B0_MIGRATION_HANDOFF_STALE",
                "baseline does not exactly project the finalized migration handoff",
            )
    source_run_id = baseline["source_run_id"]
    register_path = verify_artifact_reference(
        baseline["fact_dependency_register"], root=root
    )
    if verified_migration is None and authority_parent is None:
        source_chain_state = verify_artifact_reference(
            baseline["run_state"], root=root
        )
        if baseline.get("source_kind") == "authority_revision":
            base_v2_completion = verify_artifact_reference(
                baseline["v2_completion"], root=root
            )
            base_v2_model = _load_json(
                base_v2_completion, code="B0_SOURCE_COMPLETION_INVALID"
            )
            try:
                source_chain_state = _resolve_source_reference(
                    base_v2_model["run_state"],
                    owner_path=base_v2_completion,
                    source_root=root,
                    label="V2 base run state",
                )
            except (KeyError, ValueError) as error:
                _fail("B0_SOURCE_STATE_MISMATCH", str(error))
        _, _, _, register_facts = _validate_source_chain(
            run_id=source_run_id,
            source_root=root,
            source_interview_state=source_chain_state,
            design_completions=resolved_design_completions,
            v1_completion_path=verify_artifact_reference(
                baseline["v1_completion"], root=root
            ),
            v2_completion_path=verify_artifact_reference(
                baseline["v2_completion"], root=root
            ),
            approval_path=verify_artifact_reference(
                baseline["v2_author_approval"], root=root
            ),
            fact_register_path=register_path,
        )
    else:
        register_facts, _ = _fact_dependencies(
            _load_json(register_path, code="B0_FACT_REGISTER_INVALID"),
            register_path=register_path,
            source_root=root,
        )
    expected_facts: list[dict[str, Any]] = []
    for value in register_facts:
        item = copy.deepcopy(dict(value))
        if item["status"] == "adopted":
            for field in ("research_package", "adoption_record"):
                item[field] = artifact_reference(Path(item[field]), root=root)
        expected_facts.append(item)
    if baseline["fact_dependencies"] != expected_facts:
        _fail(
            "B0_FACT_REGISTER_MISMATCH",
            "baseline fact dependencies are not the exact source-register projection",
        )

    execution = _load_json(
        root / "baseline-execution.json", code="B0_EXECUTION_INVALID"
    )
    stored_catalog = execution.get("implementation_catalog")
    if not isinstance(stored_catalog, list):
        _fail("B0_IMPLEMENTATION_STALE", "implementation catalog is missing")
    stored_by_identity: dict[str, Mapping[str, Any]] = {}
    for record in stored_catalog:
        if (
            not isinstance(record, Mapping)
            or not isinstance(record.get("identity"), str)
            or not isinstance(record.get("artifact"), Mapping)
            or record["identity"] in stored_by_identity
        ):
            _fail("B0_IMPLEMENTATION_STALE", "implementation catalog is invalid")
        stored_by_identity[record["identity"]] = record["artifact"]
    stored_binding_digest = canonical_sha256(
        {
            identity: reference.get("sha256")
            for identity, reference in sorted(stored_by_identity.items())
        }
    )
    trusted_legacy = (
        stored_binding_digest
        in TRUSTED_LEGACY_IMPLEMENTATION_CATALOG_SHA256
    )
    required_catalog = _required_implementation_catalog(contract_runtime)
    missing_required = set(required_catalog) - set(stored_by_identity)
    if missing_required and not (
        trusted_legacy
        and missing_required == set(TRUSTED_LEGACY_MISSING_CURRENT_IDENTITIES)
    ):
        _fail("B0_IMPLEMENTATION_STALE", "required implementation binding is missing")
    current_mismatches: list[str] = []
    for identity, current_path in required_catalog.items():
        if identity in missing_required:
            continue
        copied_reference = stored_by_identity[identity]
        try:
            verify_artifact_reference(copied_reference, root=root)
        except ValueError as error:
            _fail("B0_IMPLEMENTATION_STALE", f"{identity} binding failed: {error}")
        if copied_reference["sha256"] != sha256_file(current_path):
            current_mismatches.append(identity)
    if trusted_legacy:
        expected_mismatches = set(TRUSTED_LEGACY_MISMATCH_BINDINGS)
        if set(current_mismatches) != expected_mismatches:
            _fail(
                "B0_IMPLEMENTATION_STALE",
                "trusted legacy implementation migration does not match",
            )
        for identity, binding in TRUSTED_LEGACY_MISMATCH_BINDINGS.items():
            if (
                stored_by_identity[identity].get("sha256")
                != binding["stored_sha256"]
                or sha256_file(required_catalog[identity])
                != binding["approved_current_sha256"]
            ):
                _fail(
                    "B0_IMPLEMENTATION_STALE",
                    f"trusted legacy {identity} migration differs",
                )
        # A trusted historical digest is meaningful only if every bound copy,
        # including its aggregate export, still exists with the sealed bytes.
        for identity, copied_reference in stored_by_identity.items():
            try:
                verify_artifact_reference(copied_reference, root=root)
            except ValueError as error:
                _fail(
                    "B0_IMPLEMENTATION_STALE",
                    f"legacy {identity} binding failed: {error}",
                )
    elif current_mismatches:
        _fail(
            "B0_IMPLEMENTATION_STALE",
            "current "
            + current_mismatches[0]
            + " differs from the package-bound implementation",
        )

    inventory: dict[str, tuple[str, dict[str, str]]] = {}
    for entry in baseline["design_artifacts"]:
        artifact_path = verify_artifact_reference(entry["artifact"], root=root)
        source_artifact_path = verify_artifact_reference(
            entry.get("source_artifact", entry["artifact"]), root=root
        )
        completion_path = verify_artifact_reference(entry["completion"], root=root)
        completion = _load_json(
            completion_path, code="B0_SOURCE_COMPLETION_INVALID"
        )
        if completion.get("stage") != entry["domain"] or completion.get("status") != "ready":
            _fail("B0_SOURCE_COMPLETION_INVALID", f"{entry['domain']} is not ready")
        if (
            verified_migration is None
            and baseline.get("source_kind") != "authority_revision"
            and _completion_artifact(completion, completion_path, root)
            != source_artifact_path
        ):
            _fail("B0_SOURCE_CHAIN_MISMATCH", f"{entry['domain']} artifact binding changed")
        controls = extract_controls(artifact_path, entry["domain"])
        extracted_ids = [item["id"] for item in controls]
        if set(extracted_ids) != set(entry["control_ids"]):
            _fail(
                "B0_CONTROL_SET_MISMATCH",
                f"{entry['domain']} declared controls differ from source extraction",
            )
        for item in controls:
            if item["id"] in inventory:
                _fail("B0_CONTROL_CONFLICT", f"duplicate control {item['id']}")
            inventory[item["id"]] = (entry["domain"], entry["artifact"])

    registry = {item["id"]: item for item in baseline["control_registry"]}
    if len(registry) != len(baseline["control_registry"]) or set(registry) != set(
        inventory
    ):
        _fail("B0_CONTROL_SET_MISMATCH", "control registry is not lossless")
    for control_id, (domain, artifact_ref) in inventory.items():
        item = registry[control_id]
        artifact_path = verify_artifact_reference(artifact_ref, root=root)
        source_control = {
            value["id"]: value
            for value in extract_controls(artifact_path, domain)
        }[control_id]
        if (
            item["domain"] != domain
            or item["artifact"] != artifact_ref
            or item["hardness"] != source_control["hardness"]
            or item["heading"] != source_control["heading"]
            or item["value_sha256"] != canonical_sha256(source_control["value"])
        ):
            _fail("B0_CONTROL_SET_MISMATCH", f"{control_id} evidence binding changed")
    expected_open = sorted(
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    )
    if sorted(baseline["open_items"]) != expected_open:
        _fail("B0_OPEN_SET_MISMATCH", "open_items is not the exact author_open set")

    fact_ids: set[str] = set()
    for fact in baseline["fact_dependencies"]:
        if fact["id"] in fact_ids:
            _fail("B0_FACT_CONFLICT", f"duplicate fact dependency {fact['id']}")
        fact_ids.add(fact["id"])
        if fact["status"] == "open" and fact["blocking"] is not False:
            _fail("B0_STRUCTURAL_FACT_UNRESOLVED", f"{fact['id']} remains blocking")
        if fact["status"] == "adopted":
            verify_artifact_reference(fact["research_package"], root=root)
            verify_artifact_reference(fact["adoption_record"], root=root)

    expected_validation = _validation_report(baseline["run_id"])
    if stored_validation != expected_validation:
        _fail(
            "B0_VALIDATION_STALE",
            "stored validation differs from deterministic read-only revalidation",
        )
    return expected_validation


__all__ = [
    "BaselineBuild",
    "BaselineError",
    "DOMAINS",
    "build_baseline_package",
    "build_baseline_from_authority_revision",
    "extract_controls",
    "validate_baseline_package",
]
