"""Fail-closed intake for finalized legacy-interview migration packages.

The migrator owns extraction and the explicitly selected compatibility-decision route.  The autonomous harness owns
the decision whether that immutable result is admissible as B0 source
evidence.  This module deliberately understands only the finalized protocol;
``waiting_author`` candidates are never a valid handoff.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import ManifestIntegrityError, sha256_file, verify_artifact_reference


DOMAINS = ("I0", "I1", "I2", "I3", "I4", "I5")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MigrationHandoffError(ValueError):
    """Stable error raised when a migration result is not B0-admissible."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class FinalizedMigrationHandoff:
    """Resolved, hash-verified arguments for ``build_baseline_package``."""

    package_root: Path
    finalization_path: Path
    migration_id: str
    source_run_id: str
    source_interview_state: Path
    design_completions: dict[str, Path]
    source_artifacts: dict[str, Path]
    control_projections: dict[str, Path]
    v1_completion: Path
    v2_completion: Path
    v2_author_approval: Path
    fact_dependency_register: Path
    evidence_paths: frozenset[Path]


def _fail(code: str, message: str) -> None:
    raise MigrationHandoffError(code, message)


def _read_object(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"cannot read {path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"JSON root must be an object: {path}")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], *, label: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        _fail(
            "B0_MIGRATION_PROTOCOL_INVALID",
            f"{label} fields differ (missing={missing}, extra={extra})",
        )


def _non_empty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("B0_MIGRATION_PROTOCOL_INVALID", f"{label} must be non-empty")
    return value


def _resolve(
    reference: Any,
    *,
    owner: Path,
    package_root: Path,
    label: str,
) -> Path:
    if not isinstance(reference, Mapping):
        _fail("B0_MIGRATION_REFERENCE_INVALID", f"{label} is not a reference")
    if set(reference) != {"path", "sha256"}:
        _fail("B0_MIGRATION_REFERENCE_INVALID", f"{label} has invalid fields")
    raw_path = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        _fail("B0_MIGRATION_REFERENCE_INVALID", f"{label}.path is invalid")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        _fail("B0_MIGRATION_REFERENCE_INVALID", f"{label}.sha256 is invalid")
    candidate = (owner.parent / raw_path).resolve()
    try:
        candidate.relative_to(package_root)
    except ValueError:
        _fail("B0_MIGRATION_REFERENCE_INVALID", f"{label} escapes package root")
    if not candidate.is_file():
        _fail("B0_MIGRATION_REFERENCE_MISSING", f"{label} is missing: {candidate}")
    if sha256_file(candidate) != digest:
        _fail("B0_MIGRATION_HASH_MISMATCH", f"{label} hash does not match")
    return candidate


def _domain_references(
    value: Any,
    *,
    owner: Path,
    package_root: Path,
    label: str,
) -> dict[str, Path]:
    if not isinstance(value, Mapping) or set(value) != set(DOMAINS):
        _fail("B0_MIGRATION_PROTOCOL_INVALID", f"{label} must bind exactly I0-I5")
    return {
        domain: _resolve(
            value[domain], owner=owner, package_root=package_root, label=f"{label}.{domain}"
        )
        for domain in DOMAINS
    }


def _accepted_ids(value: Any, *, label: str) -> set[str]:
    if not isinstance(value, list):
        _fail("B0_MIGRATION_APPROVAL_INVALID", f"{label} must be an array")
    accepted: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != {"id", "decision"}:
            _fail("B0_MIGRATION_APPROVAL_INVALID", f"{label}[{index}] is invalid")
        item_id = _non_empty(item.get("id"), label=f"{label}[{index}].id")
        if item.get("decision") != "accept" or item_id in accepted:
            _fail(
                "B0_MIGRATION_APPROVAL_INVALID",
                f"{label}[{index}] is duplicate or not accepted",
            )
        accepted.add(item_id)
    return accepted


def _control_ids(paths: Mapping[str, Path]) -> set[str]:
    from .baseline import extract_controls

    result: set[str] = set()
    for domain in DOMAINS:
        for control in extract_controls(paths[domain], domain):
            control_id = control["id"]
            if control_id in result:
                _fail("B0_MIGRATION_CONTROL_CONFLICT", f"duplicate {control_id}")
            result.add(control_id)
    return result


def _fact_ids(path: Path) -> set[str]:
    value = _read_object(path, code="B0_MIGRATION_FACT_REGISTER_INVALID")
    facts = value.get("fact_dependencies")
    if not isinstance(facts, list) or not facts:
        _fail("B0_MIGRATION_FACT_REGISTER_INVALID", "fact_dependencies is empty")
    result: set[str] = set()
    for index, fact in enumerate(facts):
        if not isinstance(fact, Mapping):
            _fail("B0_MIGRATION_FACT_REGISTER_INVALID", f"fact[{index}] is invalid")
        fact_id = _non_empty(fact.get("id"), label=f"fact[{index}].id")
        if fact_id in result:
            _fail("B0_MIGRATION_FACT_REGISTER_INVALID", f"duplicate {fact_id}")
        result.add(fact_id)
    return result


def validate_finalized_migration_handoff(
    finalization: str | Path,
) -> FinalizedMigrationHandoff:
    """Validate and resolve one finalized migrator package, without mutation."""

    finalization_path = Path(finalization).resolve()
    if finalization_path.name != "migration-finalization.json":
        _fail(
            "B0_MIGRATION_PROTOCOL_INVALID",
            "handoff must be migration-finalization.json",
        )
    package_root = finalization_path.parent
    document = _read_object(finalization_path, code="B0_MIGRATION_PROTOCOL_INVALID")
    _exact_keys(
        document,
        {
            "schema_version",
            "kind",
            "migration_id",
            "source_run_id",
            "status",
            "candidate_manifest",
            "compatibility_decision",
            "source_inventory",
            "control_projections",
            "fact_dependency_register",
            "validation",
        },
        label="migration finalization",
    )
    if (
        document.get("schema_version") != "1.0"
        or document.get("kind") != "interview-b0-migration-finalization"
        or document.get("status") != "finalized"
    ):
        _fail("B0_MIGRATION_NOT_FINALIZED", "handoff is not a finalized V1 protocol")
    migration_id = _non_empty(document.get("migration_id"), label="migration_id")
    source_run_id = _non_empty(document.get("source_run_id"), label="source_run_id")

    evidence: set[Path] = {finalization_path}
    candidate_path = _resolve(
        document["candidate_manifest"], owner=finalization_path,
        package_root=package_root, label="candidate_manifest",
    )
    decision_path = _resolve(
        document["compatibility_decision"], owner=finalization_path,
        package_root=package_root, label="compatibility_decision",
    )
    inventory_path = _resolve(
        document["source_inventory"], owner=finalization_path,
        package_root=package_root, label="source_inventory",
    )
    validation_path = _resolve(
        document["validation"], owner=finalization_path,
        package_root=package_root, label="validation",
    )
    projections = _domain_references(
        document["control_projections"], owner=finalization_path,
        package_root=package_root, label="control_projections",
    )
    fact_register = _resolve(
        document["fact_dependency_register"], owner=finalization_path,
        package_root=package_root, label="fact_dependency_register",
    )
    evidence.update(
        {candidate_path, decision_path, inventory_path, validation_path, fact_register}
    )
    evidence.update(projections.values())

    candidate = _read_object(candidate_path, code="B0_MIGRATION_CANDIDATE_INVALID")
    _exact_keys(
        candidate,
        {
            "schema_version", "kind", "migration_id", "source_run_id", "status",
            "source_inventory", "control_projections", "fact_candidates",
            "migration_review_json", "migration_review_html", "validation",
        },
        label="migration candidate",
    )
    if (
        candidate.get("schema_version") != "1.0"
        or candidate.get("kind") != "interview-b0-migration-candidate"
        or candidate.get("migration_id") != migration_id
        or candidate.get("source_run_id") != source_run_id
        or candidate.get("status") != "waiting_author"
    ):
        _fail("B0_MIGRATION_CANDIDATE_INVALID", "candidate identity/status mismatch")
    candidate_inventory_path = _resolve(
        candidate["source_inventory"], owner=candidate_path,
        package_root=package_root, label="candidate.source_inventory",
    )
    candidate_projections = _domain_references(
        candidate["control_projections"], owner=candidate_path,
        package_root=package_root, label="candidate.control_projections",
    )
    candidate_facts_path = _resolve(
        candidate["fact_candidates"], owner=candidate_path,
        package_root=package_root, label="candidate.fact_candidates",
    )
    for label in ("migration_review_json", "migration_review_html", "validation"):
        evidence.add(
            _resolve(
                candidate[label], owner=candidate_path,
                package_root=package_root, label=f"candidate.{label}",
            )
        )
    evidence.update({candidate_inventory_path, candidate_facts_path})
    evidence.update(candidate_projections.values())

    decision = _read_object(decision_path, code="B0_MIGRATION_APPROVAL_INVALID")
    common_valid = (
        decision.get("schema_version") == "1.0"
        and decision.get("migration_id") == migration_id
        and decision.get("source_run_id") == source_run_id
        and decision.get("candidate_manifest_sha256") == sha256_file(candidate_path)
        and decision.get("author_role") == "author"
    )
    if decision.get("kind") == "interview-b0-migration-author-decision":
        _exact_keys(
            decision,
            {
                "schema_version", "kind", "migration_id", "source_run_id",
                "candidate_manifest_sha256", "decision", "author_role",
                "control_decisions", "fact_decisions",
            },
            label="migration author decision",
        )
        if not common_valid or decision.get("decision") != "approved":
            _fail(
                "B0_MIGRATION_APPROVAL_INVALID",
                "author item decision does not bind approval",
            )
        decision_mode = "item_approval"
    elif decision.get("kind") == "interview-b0-migration-author-process-decision":
        _exact_keys(
            decision,
            {
                "schema_version", "kind", "migration_id", "source_run_id",
                "candidate_manifest_sha256", "decision", "author_role",
                "human_review_scope", "statement",
            },
            label="migration author process decision",
        )
        if (
            not common_valid
            or decision.get("decision")
            != "delegate_internal_compatibility_conversion"
            or decision.get("human_review_scope")
            != ["world", "story", "characters", "fragments"]
            or not isinstance(decision.get("statement"), str)
            or not decision["statement"].strip()
        ):
            _fail(
                "B0_MIGRATION_APPROVAL_INVALID",
                "author process decision does not reserve the exact four-part H1 review",
            )
        decision_mode = "delegated_internal"
    else:
        _fail("B0_MIGRATION_APPROVAL_INVALID", "unsupported compatibility decision")

    validation = _read_object(validation_path, code="B0_MIGRATION_VALIDATION_INVALID")
    if (
        validation.get("migration_id") != migration_id
        or validation.get("source_run_id") != source_run_id
        or validation.get("status") != "finalized"
        or validation.get("verdict") != "pass"
        or not isinstance(validation.get("checks"), list)
        or not validation["checks"]
        or any(not isinstance(item, str) or not item for item in validation["checks"])
    ):
        _fail("B0_MIGRATION_VALIDATION_INVALID", "final validation is not a pass")

    inventory = _read_object(inventory_path, code="B0_MIGRATION_INVENTORY_INVALID")
    required_inventory = {
        "schema_version", "migration_id", "source_run_id",
        "source_interview_state", "design_completions", "v1_completion",
        "v2_completion", "v2_author_approval", "source_artifacts",
        "additional_evidence", "entries",
    }
    _exact_keys(inventory, required_inventory, label="source inventory")
    if (
        inventory.get("schema_version") != "1.0"
        or inventory.get("migration_id") != migration_id
        or inventory.get("source_run_id") != source_run_id
    ):
        _fail("B0_MIGRATION_INVENTORY_INVALID", "source inventory identity mismatch")
    state = _resolve(
        inventory["source_interview_state"], owner=inventory_path,
        package_root=package_root, label="source_interview_state",
    )
    completions = _domain_references(
        inventory["design_completions"], owner=inventory_path,
        package_root=package_root, label="design_completions",
    )
    raw_source_artifacts = inventory["source_artifacts"]
    if not isinstance(raw_source_artifacts, Mapping) or set(raw_source_artifacts) != set(DOMAINS) | {"V1", "V2"}:
        _fail(
            "B0_MIGRATION_INVENTORY_INVALID",
            "source_artifacts must bind exactly I0-I5, V1 and V2",
        )
    all_source_artifacts = {
        stage: _resolve(
            raw_source_artifacts[stage], owner=inventory_path,
            package_root=package_root, label=f"source_artifacts.{stage}",
        )
        for stage in DOMAINS + ("V1", "V2")
    }
    source_artifacts = {domain: all_source_artifacts[domain] for domain in DOMAINS}
    v1 = _resolve(
        inventory["v1_completion"], owner=inventory_path,
        package_root=package_root, label="v1_completion",
    )
    v2 = _resolve(
        inventory["v2_completion"], owner=inventory_path,
        package_root=package_root, label="v2_completion",
    )
    approval = _resolve(
        inventory["v2_author_approval"], owner=inventory_path,
        package_root=package_root, label="v2_author_approval",
    )
    additional = inventory["additional_evidence"]
    if not isinstance(additional, list):
        _fail("B0_MIGRATION_INVENTORY_INVALID", "additional_evidence must be an array")
    for index, reference in enumerate(additional):
        evidence.add(
            _resolve(
                reference, owner=inventory_path, package_root=package_root,
                label=f"additional_evidence[{index}]",
            )
        )
    entries = inventory["entries"]
    if not isinstance(entries, list) or not entries:
        _fail("B0_MIGRATION_INVENTORY_INVALID", "entries must be non-empty")
    entry_snapshots: set[Path] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping) or set(entry) != {
            "role", "original_path", "snapshot", "size_bytes"
        }:
            _fail("B0_MIGRATION_INVENTORY_INVALID", f"entries[{index}] is invalid")
        _non_empty(entry.get("role"), label=f"entries[{index}].role")
        _non_empty(entry.get("original_path"), label=f"entries[{index}].original_path")
        snapshot = _resolve(
            entry["snapshot"], owner=inventory_path, package_root=package_root,
            label=f"entries[{index}].snapshot",
        )
        if (
            not isinstance(entry.get("size_bytes"), int)
            or isinstance(entry.get("size_bytes"), bool)
            or entry["size_bytes"] < 0
            or snapshot.stat().st_size != entry["size_bytes"]
            or snapshot in entry_snapshots
        ):
            _fail("B0_MIGRATION_INVENTORY_INVALID", f"entries[{index}] size/identity invalid")
        entry_snapshots.add(snapshot)
        evidence.add(snapshot)
    evidence.update({state, v1, v2, approval})
    evidence.update(completions.values())
    evidence.update(all_source_artifacts.values())

    if sha256_file(candidate_inventory_path) != sha256_file(inventory_path):
        _fail("B0_MIGRATION_CANDIDATE_INVALID", "final inventory differs from candidate")
    for domain in DOMAINS:
        waiting = _read_object(
            candidate_projections[domain], code="B0_MIGRATION_CANDIDATE_INVALID"
        )
        ready = _read_object(projections[domain], code="B0_MIGRATION_PROTOCOL_INVALID")
        if (
            waiting.get("status") != "waiting_author"
            or ready.get("status") != "ready"
            or waiting.get("run_id") != source_run_id
            or ready.get("run_id") != source_run_id
            or waiting.get("stage") != domain
            or ready.get("stage") != domain
            or waiting.get("controls") != ready.get("controls")
            or waiting.get("evidence_bindings") != ready.get("evidence_bindings")
        ):
            _fail(
                "B0_MIGRATION_CANDIDATE_INVALID",
                f"final {domain} projection differs from the approved candidate",
            )
    candidate_facts = _read_object(
        candidate_facts_path, code="B0_MIGRATION_CANDIDATE_INVALID"
    )
    final_facts = _read_object(
        fact_register, code="B0_MIGRATION_FACT_REGISTER_INVALID"
    )
    if (
        candidate_facts.get("status") != "waiting_author"
        or final_facts.get("status") != "ready"
        or candidate_facts.get("run_id") != source_run_id
        or final_facts.get("run_id") != source_run_id
        or candidate_facts.get("fact_dependencies")
        != final_facts.get("fact_dependencies")
    ):
        _fail(
            "B0_MIGRATION_CANDIDATE_INVALID",
            "final fact register differs from the approved candidate",
        )

    control_ids = _control_ids(projections)
    fact_ids = _fact_ids(fact_register)
    if decision_mode == "item_approval":
        if _accepted_ids(decision["control_decisions"], label="control_decisions") != control_ids:
            _fail("B0_MIGRATION_APPROVAL_INCOMPLETE", "control approval set is not exact")
        if _accepted_ids(decision["fact_decisions"], label="fact_decisions") != fact_ids:
            _fail("B0_MIGRATION_APPROVAL_INCOMPLETE", "fact approval set is not exact")

    return FinalizedMigrationHandoff(
        package_root=package_root,
        finalization_path=finalization_path,
        migration_id=migration_id,
        source_run_id=source_run_id,
        source_interview_state=state,
        design_completions=completions,
        source_artifacts=source_artifacts,
        control_projections=projections,
        v1_completion=v1,
        v2_completion=v2,
        v2_author_approval=approval,
        fact_dependency_register=fact_register,
        evidence_paths=frozenset(evidence),
    )


__all__ = [
    "FinalizedMigrationHandoff",
    "MigrationHandoffError",
    "validate_finalized_migration_handoff",
]
