"""Fail-closed authority-revision fork bootstrap for conception runs.

The revision transaction does not mutate or reinterpret an approved parent
run.  It copies the exact evidence named by the caller, deterministically
replays byte-local text edits against the approved authority projections, and
opens a fresh revision-000 run only after an independent semantic review has
been bound.  The previous author approval is evidence, never approval of the
new bytes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping, Sequence

from .baseline import BaselineError, extract_controls
from .canonical import canonical_json, canonical_sha256, sha256_file
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import AutonomousCoordinator, SealedDocument
from .production_orchestrator import (
    CURRENT_CONCEPTION_PRODUCTION_CONTRACT,
    CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
    ProductionContext,
)
from .production_store import ProductionRunStore


AUTHORITY_REVISION_ALLOWSET = frozenset(
    {
        "CAU-AUDIT-BOUNDARY",
        "CAU-GLOBAL-SPINE",
        "CAU-MAJOR-NODES",
        "CHR-GU-HENG-MEMORY",
        "CHR-ROLE-TIERS",
        "NAR-FAIRNESS",
        "NAR-POV-ARCHITECTURE",
    }
)

REQUIRED_EVIDENCE_LABELS = frozenset(
    {
        "parent_state",
        "parent_final_completion",
        "parent_p1_completion",
        "parent_h1_completion",
        "parent_author_decision",
        "hld_question",
        "hld_answer",
        "hld_resolution",
        "hld_state",
        "author_event",
    }
)

_IDENTITY_FIELDS = ("actor_id", "session_id", "implementation_sha256")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ConceptionRevisionError(ValueError):
    """Stable fail-closed error raised by the revision bootstrap."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class ConceptionRevisionContext:
    """The promoted revision run and its immutable bootstrap evidence."""

    production: ProductionContext
    transaction_id: str
    directive_binding: SealedDocument
    patch_plan: SealedDocument
    semantic_review: SealedDocument
    finalization: SealedDocument
    bootstrap_completion: SealedDocument
    replayed: bool


def _fail(code: str, message: str) -> None:
    raise ConceptionRevisionError(code, message)


def _reference(path: Path, *, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def _sealed(data: Mapping[str, Any], path: str) -> SealedDocument:
    body = copy.deepcopy(dict(data))
    return SealedDocument(
        data=body,
        reference={"path": path, "sha256": canonical_sha256(body)},
    )


def _safe_relative(value: Any, *, code: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        _fail(code, str(value))
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        _fail(code, value)
    return path


def _resolve_bound(root: Path, reference: Mapping[str, Any], *, code: str) -> Path:
    if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
        _fail(code, str(reference))
    logical = _safe_relative(reference.get("path"), code=code)
    digest = reference.get("sha256")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        _fail(code, str(reference))
    candidate = (root / Path(*logical.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        _fail(code, str(candidate))
    if not candidate.is_file() or sha256_file(candidate) != digest:
        _fail(code, str(candidate))
    return candidate


def _validate_identity(value: Mapping[str, Any], *, code: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(_IDENTITY_FIELDS):
        _fail(code, str(value))
    result: dict[str, str] = {}
    for field in _IDENTITY_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            _fail(code, field)
        if field == "implementation_sha256" and _SHA256.fullmatch(item) is None:
            _fail(code, field)
        result[field] = item
    return result


def _normalize_revision_inputs(
    *,
    run_id: str,
    evidence_bindings: Mapping[str, Mapping[str, Any]],
    author_text: str,
    directive_clauses: Sequence[Mapping[str, Any]],
    text_edits: Sequence[Mapping[str, Any]],
    producer_identity: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize the immutable inputs which an independent reviewer receives."""

    if not isinstance(run_id, str) or not run_id:
        _fail("REV_RUN_ID_INVALID", str(run_id))
    producer = _validate_identity(
        producer_identity, code="REV_PRODUCER_IDENTITY_INVALID"
    )
    if not isinstance(author_text, str) or not author_text.strip():
        _fail("REV_AUTHOR_TEXT_INVALID", "author_text")
    if set(evidence_bindings) != REQUIRED_EVIDENCE_LABELS:
        _fail("REV_EVIDENCE_SET_INVALID", str(sorted(evidence_bindings)))
    for label, binding in evidence_bindings.items():
        if (
            not isinstance(binding, Mapping)
            or set(binding) != {"root", "artifact"}
            or not isinstance(binding.get("root"), str)
            or not binding["root"]
            or not isinstance(binding.get("artifact"), Mapping)
            or set(binding["artifact"]) != {"path", "sha256"}
        ):
            _fail("REV_EVIDENCE_BINDING_INVALID", label)
        _safe_relative(
            binding["artifact"].get("path"), code="REV_EVIDENCE_BINDING_INVALID"
        )
        if _SHA256.fullmatch(str(binding["artifact"].get("sha256"))) is None:
            _fail("REV_EVIDENCE_BINDING_INVALID", label)
    if not isinstance(directive_clauses, Sequence) or isinstance(
        directive_clauses, (str, bytes)
    ):
        _fail("REV_DIRECTIVE_INVALID", "clauses")
    clauses = [
        copy.deepcopy(dict(item))
        for item in directive_clauses
        if isinstance(item, Mapping)
    ]
    if len(clauses) != len(directive_clauses) or not clauses:
        _fail("REV_DIRECTIVE_INVALID", "clauses")
    clause_ids = [item.get("clause_id") for item in clauses]
    if any(
        set(item) != {"clause_id", "text", "evidence_labels"}
        or not isinstance(item.get("clause_id"), str)
        or not item["clause_id"]
        or not isinstance(item.get("text"), str)
        or not item["text"]
        or not isinstance(item.get("evidence_labels"), list)
        or not item["evidence_labels"]
        or not set(item["evidence_labels"]) <= REQUIRED_EVIDENCE_LABELS
        for item in clauses
    ) or len(set(clause_ids)) != len(clause_ids):
        _fail("REV_DIRECTIVE_INVALID", "clauses")
    if not isinstance(text_edits, Sequence) or isinstance(text_edits, (str, bytes)):
        _fail("REV_PATCH_SET_INVALID", "edits")
    edits = [
        copy.deepcopy(dict(item)) for item in text_edits if isinstance(item, Mapping)
    ]
    ids = [item.get("source_id") for item in edits]
    if (
        len(edits) != len(text_edits)
        or len(edits) != len(AUTHORITY_REVISION_ALLOWSET)
        or set(ids) != AUTHORITY_REVISION_ALLOWSET
    ):
        _fail("REV_PATCH_ALLOWSET_INVALID", str(ids))
    return producer, clauses, edits


def _review_material_core(
    *,
    run_id: str,
    evidence_bindings: Mapping[str, Mapping[str, Any]],
    author_text: str,
    directive_clauses: Sequence[Mapping[str, Any]],
    text_edits: Sequence[Mapping[str, Any]],
    producer: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "kind": "authority-revision-review-material",
        "run_id": run_id,
        "producer": copy.deepcopy(dict(producer)),
        "allowset": sorted(AUTHORITY_REVISION_ALLOWSET),
        "evidence_bindings": copy.deepcopy(dict(evidence_bindings)),
        "author_text": author_text,
        "directive_clauses": copy.deepcopy(list(directive_clauses)),
        "text_edits": sorted(
            copy.deepcopy(list(text_edits)), key=lambda item: item["source_id"]
        ),
    }


def build_authority_revision_review_material(
    *,
    run_id: str,
    evidence_bindings: Mapping[str, Mapping[str, Any]],
    author_text: str,
    directive_clauses: Sequence[Mapping[str, Any]],
    text_edits: Sequence[Mapping[str, Any]],
    producer_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Build, without filesystem writes, the exact material to review.

    The returned digest is the transaction identity.  A reviewer seals a
    separate semantic-review document against it; the initializer never
    creates or amends that verdict.
    """

    producer, clauses, edits = _normalize_revision_inputs(
        run_id=run_id,
        evidence_bindings=evidence_bindings,
        author_text=author_text,
        directive_clauses=directive_clauses,
        text_edits=text_edits,
        producer_identity=producer_identity,
    )
    core = _review_material_core(
        run_id=run_id,
        evidence_bindings=evidence_bindings,
        author_text=author_text,
        directive_clauses=clauses,
        text_edits=edits,
        producer=producer,
    )
    return {
        **core,
        "candidate_material_sha256": canonical_sha256(core),
    }


def _load_sealed_semantic_review(
    *,
    root: Path,
    reference: Mapping[str, Any],
    review_material: Mapping[str, Any],
    runtime: ContractRuntime,
) -> tuple[dict[str, Any], bytes]:
    """Validate an externally sealed review before any run-root write."""

    path = _resolve_bound(root, reference, code="REV_REVIEW_ARTIFACT_INVALID")
    raw = path.read_bytes()
    try:
        review = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail("REV_REVIEW_ARTIFACT_INVALID", str(error))
    if not isinstance(review, dict):
        _fail("REV_REVIEW_ARTIFACT_INVALID", "review must be an object")
    canonical = canonical_json(review).encode("utf-8")
    expected_sha = reference.get("sha256")
    if (
        raw != canonical
        or hashlib.sha256(raw).hexdigest() != expected_sha
        or canonical_sha256(review) != expected_sha
    ):
        _fail("REV_REVIEW_NOT_CANONICAL", str(path))
    try:
        runtime.validate(review, "authority-revision-semantic-review.schema.json")
    except ContractValidationError as error:
        _fail("REV_REVIEW_SCHEMA_INVALID", str(error))

    producer = review_material["producer"]
    reviewer = _validate_identity(
        review.get("reviewer"), code="REV_REVIEWER_IDENTITY_INVALID"
    )
    exact_items = [
        {"source_id": source_id, "verdict": "pass", "findings": []}
        for source_id in sorted(AUTHORITY_REVISION_ALLOWSET)
    ]
    if (
        review.get("transaction_id")
        != review_material["candidate_material_sha256"][:24]
        or review.get("run_id") != review_material["run_id"]
        or review.get("candidate_material_sha256")
        != review_material["candidate_material_sha256"]
        or review.get("producer") != producer
        or review.get("covered_ids") != sorted(AUTHORITY_REVISION_ALLOWSET)
        or review.get("item_reviews") != exact_items
        or review.get("reviewer_produced_patch") is not False
        or review.get("verdict") != "pass"
        or review.get("status") != "sealed"
    ):
        _fail("REV_REVIEW_BINDING_INVALID", "sealed review does not bind candidate")
    if any(producer[field] == reviewer[field] for field in _IDENTITY_FIELDS):
        _fail("REV_REVIEW_NOT_INDEPENDENT", "producer and reviewer identities overlap")
    return review, raw


def _write_exact(path: Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            _fail("REV_IMMUTABLE_CONFLICT", str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _write_exact(path, canonical_json(value).encode("utf-8"))


@contextmanager
def _parent_lock(target: Path) -> Iterator[None]:
    lock_path = target.parent / f".{target.name}.authority-revision.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        _fail("REV_PARENT_LOCKED", str(lock_path))
        raise AssertionError from error
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(b"authority-revision-bootstrap-v1")
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _copy_evidence(
    staging: Path,
    *,
    evidence_bindings: Mapping[str, Mapping[str, Any]],
    evidence_roots: Mapping[str, str | Path],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]]:
    if set(evidence_bindings) != REQUIRED_EVIDENCE_LABELS:
        _fail("REV_EVIDENCE_SET_INVALID", str(sorted(evidence_bindings)))
    copied: dict[str, dict[str, str]] = {}
    source_records: dict[str, dict[str, Any]] = {}
    for label in sorted(evidence_bindings):
        binding = evidence_bindings[label]
        if not isinstance(binding, Mapping) or set(binding) != {"root", "artifact"}:
            _fail("REV_EVIDENCE_BINDING_INVALID", label)
        root_name = binding.get("root")
        if not isinstance(root_name, str) or root_name not in evidence_roots:
            _fail("REV_EVIDENCE_BINDING_INVALID", label)
        source_root = Path(evidence_roots[root_name]).resolve()
        artifact = binding.get("artifact")
        source = _resolve_bound(source_root, artifact, code="REV_EVIDENCE_STALE")
        suffix = source.suffix if source.suffix else ".bin"
        target = staging / "authority-revision" / "evidence" / f"{label}{suffix}"
        _write_exact(target, source.read_bytes())
        copied[label] = _reference(target, root=staging)
        source_records[label] = {
            "root": root_name,
            "root_identity_sha256": canonical_sha256(source_root.as_posix()),
            "source_artifact": copy.deepcopy(dict(artifact)),
            "copied_artifact": copied[label],
        }
    return copied, source_records


def _control_projection(path: Path, domain: str) -> list[dict[str, Any]]:
    try:
        return extract_controls(path, domain)
    except BaselineError as error:
        _fail("REV_CONTROL_PROJECTION_INVALID", str(error))
    raise AssertionError


def _expected_control_heading(path: Path, edit: Mapping[str, Any]) -> str:
    """Return the source-format heading represented by one patch edit."""

    if path.suffix.lower() == ".json":
        return str(edit["title"])
    return f"[{edit['source_id']}][{edit['hardness']}] {edit['title']}"


def _apply_patch_plan(
    staging: Path,
    *,
    source_root: Path,
    edits: Sequence[Mapping[str, Any]],
    directive_clause_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(edits, Sequence) or isinstance(edits, (str, bytes)):
        _fail("REV_PATCH_SET_INVALID", "edits")
    ids = [item.get("source_id") for item in edits if isinstance(item, Mapping)]
    if len(edits) != len(AUTHORITY_REVISION_ALLOWSET) or set(ids) != AUTHORITY_REVISION_ALLOWSET:
        _fail("REV_PATCH_ALLOWSET_INVALID", str(ids))

    prepared: list[dict[str, Any]] = []
    by_artifact: dict[str, list[dict[str, Any]]] = {}
    for raw in edits:
        if not isinstance(raw, Mapping):
            _fail("REV_PATCH_INVALID", str(raw))
        required = {
            "source_id", "domain", "hardness", "title", "control_index",
            "parent_artifact", "parent_value_sha256", "effective_value_sha256",
            "start_byte", "end_byte", "old_text", "old_text_sha256",
            "new_text", "new_text_sha256", "directive_clause_refs",
        }
        if set(raw) != required:
            _fail("REV_PATCH_INVALID", str(raw.get("source_id")))
        source_id = str(raw["source_id"])
        domain = raw["domain"]
        index = raw["control_index"]
        if domain not in {"I3", "I4", "I5"} or not isinstance(index, int) or index < 0:
            _fail("REV_PATCH_IDENTITY_INVALID", source_id)
        parent = raw["parent_artifact"]
        parent_path = _resolve_bound(source_root, parent, code="REV_PATCH_PARENT_STALE")
        controls = _control_projection(parent_path, domain)
        if index >= len(controls):
            _fail("REV_PATCH_INDEX_INVALID", source_id)
        control = controls[index]
        expected_heading = _expected_control_heading(parent_path, raw)
        if (
            control.get("id") != source_id
            or control.get("hardness") != raw["hardness"]
            or control.get("heading") != expected_heading
            or canonical_sha256(control.get("value")) != raw["parent_value_sha256"]
        ):
            _fail("REV_PATCH_PARENT_PROJECTION_MISMATCH", source_id)
        start, end = raw["start_byte"], raw["end_byte"]
        old_text, new_text = raw["old_text"], raw["new_text"]
        refs = raw["directive_clause_refs"]
        if (
            not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start
            or not isinstance(old_text, str) or not old_text
            or not isinstance(new_text, str) or not new_text
            or _text_sha256(old_text) != raw["old_text_sha256"]
            or _text_sha256(new_text) != raw["new_text_sha256"]
            or not isinstance(refs, list) or not refs or not set(refs) <= directive_clause_ids
        ):
            _fail("REV_PATCH_EDIT_INVALID", source_id)
        body = parent_path.read_bytes()
        old_bytes = old_text.encode("utf-8")
        if end > len(body) or body[start:end] != old_bytes:
            _fail("REV_PATCH_OFFSET_MISMATCH", source_id)
        record = copy.deepcopy(dict(raw))
        record["parent_artifact"] = copy.deepcopy(dict(parent))
        prepared.append(record)
        by_artifact.setdefault(str(parent["path"]), []).append(record)

    artifact_records: list[dict[str, Any]] = []
    for logical, group in sorted(by_artifact.items()):
        parent_ref = group[0]["parent_artifact"]
        if any(item["parent_artifact"] != parent_ref for item in group):
            _fail("REV_PATCH_PARENT_CONFLICT", logical)
        source = _resolve_bound(source_root, parent_ref, code="REV_PATCH_PARENT_STALE")
        original = source.read_bytes()
        ranges = sorted((item["start_byte"], item["end_byte"]) for item in group)
        if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
            _fail("REV_PATCH_OVERLAP", logical)
        effective = original
        for item in sorted(group, key=lambda value: value["start_byte"], reverse=True):
            effective = (
                effective[: item["start_byte"]]
                + item["new_text"].encode("utf-8")
                + effective[item["end_byte"] :]
            )
        destination = (
            staging / "authority-revision" / "effective"
            / f"{canonical_sha256(parent_ref)[:16]}-{source.name}"
        )
        base_destination = (
            staging / "authority-revision" / "base"
            / f"{canonical_sha256(parent_ref)[:16]}-{source.name}"
        )
        _write_exact(base_destination, original)
        _write_exact(destination, effective)

        domains = {item["domain"] for item in group}
        if len(domains) != 1:
            _fail("REV_PATCH_DOMAIN_CONFLICT", logical)
        domain = next(iter(domains))
        before = _control_projection(source, domain)
        after = _control_projection(destination, domain)
        if len(before) != len(after):
            _fail("REV_PATCH_CONTROL_COUNT_CHANGED", logical)
        target_ids = {item["source_id"] for item in group}
        group_by_id = {item["source_id"]: item for item in group}
        for index, (old, new) in enumerate(zip(before, after)):
            if old["id"] != new["id"] or old["hardness"] != new["hardness"] or old["heading"] != new["heading"]:
                _fail("REV_PATCH_CONTROL_IDENTITY_CHANGED", old["id"])
            if old["id"] not in target_ids:
                if old != new:
                    _fail("REV_PATCH_NON_TARGET_CHANGED", old["id"])
            else:
                spec = group_by_id[old["id"]]
                if spec["control_index"] != index:
                    _fail("REV_PATCH_INDEX_INVALID", old["id"])
                if canonical_sha256(new["value"]) != spec["effective_value_sha256"]:
                    _fail("REV_PATCH_EFFECTIVE_VALUE_MISMATCH", old["id"])
        artifact_records.append(
            {
                "domain": domain,
                "parent_artifact": copy.deepcopy(dict(parent_ref)),
                "base_artifact": _reference(base_destination, root=staging),
                "effective_artifact": _reference(destination, root=staging),
                "target_ids": sorted(target_ids),
                "parent_projection_sha256": canonical_sha256(before),
                "effective_projection_sha256": canonical_sha256(after),
            }
        )
    return sorted(prepared, key=lambda item: item["source_id"]), artifact_records


def _validate_schema(runtime: ContractRuntime, value: Mapping[str, Any], name: str) -> None:
    try:
        runtime.validate(value, name)
    except ContractValidationError as error:
        _fail("REV_SCHEMA_INVALID", f"{name}: {error}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail("REV_BOOTSTRAP_INVALID", f"{path}: {error}")
    if not isinstance(value, dict):
        _fail("REV_BOOTSTRAP_INVALID", str(path))
    return value


def _validate_completed_root(root: Path, *, transaction_id: str, runtime: ContractRuntime) -> None:
    pointer = root / "orchestration" / "authority-revision" / "current-bootstrap.json"
    if not pointer.is_file():
        _fail("REV_BOOTSTRAP_INCOMPLETE", str(root))
    body = _load_json(pointer)
    if body != {
        "schema_version": "1.0",
        "transaction_id": transaction_id,
        "completion": {
            "path": "authority-revision/bootstrap-completion.json",
            "sha256": sha256_file(root / "authority-revision" / "bootstrap-completion.json"),
        },
    }:
        _fail("REV_BOOTSTRAP_FOREIGN", str(root))
    documents: dict[str, dict[str, Any]] = {}
    for name, schema in (
        ("bootstrap-intent.json", "authority-revision-bootstrap-intent.schema.json"),
        ("evidence-index.json", "authority-revision-evidence-index.schema.json"),
        ("author-directive-binding.json", "author-directive-binding.schema.json"),
        ("patch-plan.json", "authority-revision-patch-plan.schema.json"),
        ("semantic-review.json", "authority-revision-semantic-review.schema.json"),
        ("finalization.json", "authority-revision-finalization.schema.json"),
        ("bootstrap-validation.json", "authority-revision-bootstrap-validation.schema.json"),
        ("bootstrap-completion.json", "authority-revision-bootstrap-completion.schema.json"),
    ):
        value = _load_json(root / "authority-revision" / name)
        _validate_schema(runtime, value, schema)
        if value.get("transaction_id") != transaction_id:
            _fail("REV_BOOTSTRAP_FOREIGN", name)
        documents[name] = value
    refs = {
        name: _reference(root / "authority-revision" / name, root=root)
        for name in documents
    }
    intent = documents["bootstrap-intent.json"]
    evidence = documents["evidence-index.json"]
    directive = documents["author-directive-binding.json"]
    patch = documents["patch-plan.json"]
    review = documents["semantic-review.json"]
    finalization = documents["finalization.json"]
    validation = documents["bootstrap-validation.json"]
    completion = documents["bootstrap-completion.json"]
    if intent["material_sha256"][:24] != transaction_id:
        _fail("REV_BOOTSTRAP_FOREIGN", "material identity")
    for label, reference in evidence["evidence"].items():
        _resolve_bound(root, reference, code="REV_EVIDENCE_STALE")
        if evidence["source_bindings"][label]["copied_artifact"] != reference:
            _fail("REV_EVIDENCE_STALE", label)
    if (
        directive["evidence_index"] != refs["evidence-index.json"]
        or directive["required_evidence"] != evidence["evidence"]
        or directive["author_text_sha256"] != _text_sha256(directive["author_text"])
        or directive["author_approved_bytes"] is not False
    ):
        _fail("REV_DIRECTIVE_STALE", "binding")
    if (
        patch["directive_binding"] != refs["author-directive-binding.json"]
        or set(patch["allowset"]) != AUTHORITY_REVISION_ALLOWSET
        or {item["source_id"] for item in patch["edits"]} != AUTHORITY_REVISION_ALLOWSET
    ):
        _fail("REV_PATCH_STALE", "binding")
    reconstructed_bindings = {
        label: {
            "root": record["root"],
            "artifact": record["source_artifact"],
        }
        for label, record in evidence["source_bindings"].items()
    }
    review_material = build_authority_revision_review_material(
        run_id=patch["run_id"],
        evidence_bindings=reconstructed_bindings,
        author_text=directive["author_text"],
        directive_clauses=directive["clauses"],
        text_edits=patch["edits"],
        producer_identity=patch["producer"],
    )
    exact_item_reviews = [
        {"source_id": source_id, "verdict": "pass", "findings": []}
        for source_id in sorted(AUTHORITY_REVISION_ALLOWSET)
    ]
    review_path = root / "authority-revision" / "semantic-review.json"
    if review_path.read_bytes() != canonical_json(review).encode("utf-8"):
        _fail("REV_REVIEW_STALE", "review is not canonical")
    if (
        patch["candidate_material_sha256"]
        != review_material["candidate_material_sha256"]
        or patch["candidate_material_sha256"][:24] != transaction_id
        or review.get("candidate_material_sha256")
        != patch["candidate_material_sha256"]
        or review.get("transaction_id") != transaction_id
        or review.get("run_id") != patch["run_id"]
        or review.get("producer") != patch["producer"]
        or review.get("covered_ids") != sorted(AUTHORITY_REVISION_ALLOWSET)
        or review.get("item_reviews") != exact_item_reviews
        or any(
            patch["producer"][field] == review["reviewer"][field]
            for field in _IDENTITY_FIELDS
        )
        or review.get("reviewer_produced_patch") is not False
        or review.get("verdict") != "pass"
        or review.get("status") != "sealed"
    ):
        _fail("REV_REVIEW_STALE", "binding")
    edit_groups: dict[str, list[dict[str, Any]]] = {}
    for edit in patch["edits"]:
        edit_groups.setdefault(edit["parent_artifact"]["path"], []).append(edit)
    for artifact in patch["artifacts"]:
        base_path = _resolve_bound(root, artifact["base_artifact"], code="REV_PATCH_STALE")
        effective_path = _resolve_bound(root, artifact["effective_artifact"], code="REV_PATCH_STALE")
        group = edit_groups.get(artifact["parent_artifact"]["path"], [])
        if (
            not group
            or any(item["parent_artifact"] != artifact["parent_artifact"] for item in group)
            or sorted(item["source_id"] for item in group) != artifact["target_ids"]
            or sha256_file(base_path) != artifact["parent_artifact"]["sha256"]
        ):
            _fail("REV_PATCH_STALE", artifact["domain"])
        base = base_path.read_bytes()
        ranges = sorted((item["start_byte"], item["end_byte"]) for item in group)
        if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
            _fail("REV_PATCH_OVERLAP", artifact["domain"])
        rebuilt = base
        for edit in sorted(group, key=lambda item: item["start_byte"], reverse=True):
            old = edit["old_text"].encode("utf-8")
            if (
                rebuilt[edit["start_byte"] : edit["end_byte"]] != old
                or _text_sha256(edit["old_text"]) != edit["old_text_sha256"]
                or _text_sha256(edit["new_text"]) != edit["new_text_sha256"]
            ):
                _fail("REV_PATCH_OFFSET_MISMATCH", edit["source_id"])
            rebuilt = rebuilt[: edit["start_byte"]] + edit["new_text"].encode("utf-8") + rebuilt[edit["end_byte"] :]
        if rebuilt != effective_path.read_bytes():
            _fail("REV_PATCH_REPLAY_MISMATCH", artifact["domain"])
        before = _control_projection(base_path, artifact["domain"])
        after = _control_projection(effective_path, artifact["domain"])
        for edit in group:
            index = edit["control_index"]
            if index >= len(before) or index >= len(after):
                _fail("REV_PATCH_INDEX_INVALID", edit["source_id"])
            old_control = before[index]
            new_control = after[index]
            expected_heading = _expected_control_heading(base_path, edit)
            if (
                old_control.get("id") != edit["source_id"]
                or old_control.get("hardness") != edit["hardness"]
                or old_control.get("heading") != expected_heading
                or canonical_sha256(old_control.get("value"))
                != edit["parent_value_sha256"]
                or new_control.get("id") != old_control.get("id")
                or new_control.get("hardness") != old_control.get("hardness")
                or new_control.get("heading") != old_control.get("heading")
                or canonical_sha256(new_control.get("value"))
                != edit["effective_value_sha256"]
            ):
                _fail("REV_PATCH_PROJECTION_STALE", edit["source_id"])
        if (
            canonical_sha256(before) != artifact["parent_projection_sha256"]
            or canonical_sha256(after) != artifact["effective_projection_sha256"]
        ):
            _fail("REV_PATCH_PROJECTION_STALE", artifact["domain"])
    if finalization != {
        "schema_version": "1.0",
        "kind": "authority-revision-finalization",
        "transaction_id": transaction_id,
        "run_id": patch["run_id"],
        "source_kind": "authority_revision",
        "parent_run": evidence["evidence"]["parent_state"],
        "parent_final_completion": evidence["evidence"]["parent_final_completion"],
        "evidence_index": refs["evidence-index.json"],
        "directive_binding": refs["author-directive-binding.json"],
        "patch_plan": refs["patch-plan.json"],
        "semantic_review": refs["semantic-review.json"],
        "base_artifacts": [item["base_artifact"] for item in patch["artifacts"]],
        "effective_artifacts": [item["effective_artifact"] for item in patch["artifacts"]],
        "author_approved_bytes": False,
        "status": "ready",
    }:
        _fail("REV_FINALIZATION_STALE", "binding")
    state = _load_json(root / "state" / "revision-000.json")
    _validate_schema(runtime, state, "autonomous-run-state.schema.json")
    if state.get("source_kind") != "authority_revision":
        _fail("REV_BOOTSTRAP_FOREIGN", "revision-000")
    if state.get("authority_revision") != refs["finalization.json"]:
        _fail("REV_BOOTSTRAP_FOREIGN", "revision authority")
    if (
        validation["state"] != _reference(root / "state" / "revision-000.json", root=root)
        or validation["finalization"] != refs["finalization.json"]
        or completion["state"] != validation["state"]
        or completion["finalization"] != refs["finalization.json"]
        or completion["validation"] != refs["bootstrap-validation.json"]
    ):
        _fail("REV_BOOTSTRAP_STALE", "completion chain")
    for field in ("base_artifacts", "effective_artifacts"):
        for reference in finalization[field]:
            _resolve_bound(root, reference, code="REV_BOOTSTRAP_ARTIFACT_STALE")


def _context_from_root(
    root: Path, *, transaction_id: str, runtime: ContractRuntime, replayed: bool
) -> ConceptionRevisionContext:
    _validate_completed_root(root, transaction_id=transaction_id, runtime=runtime)
    store = ProductionRunStore(root, runtime=runtime)
    # An authority-revision finalization is bound to its immutable bootstrap
    # snapshot, not to whatever production state happens to be current later.
    # Loading latest_state() made validation depend on downstream orchestration
    # (and made a legitimate active return impossible to validate without also
    # supplying the later return-request body).  Keep this validator anchored to
    # the exact state whose reference is sealed by bootstrap-validation and
    # bootstrap-completion.
    state_data = _load_json(root / "state" / "revision-000.json")
    state = _sealed(state_data, "state/revision-000.json")
    coordinator = AutonomousCoordinator.from_snapshot(state.data, state.reference, runtime=runtime)
    refs = {
        name: store.load_document(
            {
                "path": f"authority-revision/{name}.json",
                "sha256": sha256_file(root / "authority-revision" / f"{name}.json"),
            }
        )
        for name in (
            "author-directive-binding", "patch-plan", "semantic-review",
            "finalization", "bootstrap-completion",
        )
    }
    return ConceptionRevisionContext(
        production=ProductionContext(store, coordinator, state, None),
        transaction_id=transaction_id,
        directive_binding=refs["author-directive-binding"],
        patch_plan=refs["patch-plan"],
        semantic_review=refs["semantic-review"],
        finalization=refs["finalization"],
        bootstrap_completion=refs["bootstrap-completion"],
        replayed=replayed,
    )


def initialize_conception_revision_run(
    parent_run_root: str | Path,
    run_root: str | Path,
    *,
    run_id: str,
    source_root: str | Path,
    evidence_roots: Mapping[str, str | Path],
    evidence_bindings: Mapping[str, Mapping[str, Any]],
    author_text: str,
    directive_clauses: Sequence[Mapping[str, Any]],
    text_edits: Sequence[Mapping[str, Any]],
    producer_identity: Mapping[str, Any],
    semantic_review_root: str | Path,
    semantic_review: Mapping[str, Any],
    runtime: ContractRuntime | None = None,
) -> ConceptionRevisionContext:
    """Create or exactly replay one approved authority-revision fork.

    ``parent_run_root`` and every evidence/source root are read only.  The
    caller must supply an externally produced, canonical and hash-sealed
    semantic review of ``build_authority_revision_review_material``.  That
    review is fully validated before the target parent, lock or staging tree
    can be written.  The target is then assembled in a deterministic sibling
    staging directory and promoted only after the whole bootstrap validates.
    """

    parent = Path(parent_run_root).resolve()
    target = Path(run_root).resolve()
    sources = Path(source_root).resolve()
    contract_runtime = runtime or ContractRuntime()
    review_root = Path(semantic_review_root).resolve()
    if not parent.is_dir() or not sources.is_dir() or not review_root.is_dir() or not run_id:
        _fail("REV_INPUT_ROOT_INVALID", f"{parent} / {sources} / {run_id!r}")
    if target.parent.resolve() == target:
        _fail("REV_TARGET_INVALID", str(target))
    producer, clauses, edits = _normalize_revision_inputs(
        run_id=run_id,
        evidence_bindings=evidence_bindings,
        author_text=author_text,
        directive_clauses=directive_clauses,
        text_edits=text_edits,
        producer_identity=producer_identity,
    )
    clause_ids = [item["clause_id"] for item in clauses]
    review_material = build_authority_revision_review_material(
        run_id=run_id,
        evidence_bindings=evidence_bindings,
        author_text=author_text,
        directive_clauses=clauses,
        text_edits=edits,
        producer_identity=producer,
    )
    material_digest = review_material["candidate_material_sha256"]
    transaction_id = material_digest[:24]
    staging = target.parent / f".{target.name}.authority-revision-{transaction_id}.staging"
    external_review_path = _resolve_bound(
        review_root, semantic_review, code="REV_REVIEW_ARTIFACT_INVALID"
    )
    for forbidden_root in (target, staging):
        try:
            external_review_path.relative_to(forbidden_root)
        except ValueError:
            continue
        _fail(
            "REV_REVIEW_SOURCE_INVALID",
            "review cannot originate inside target or transaction staging",
        )
    review, review_raw = _load_sealed_semantic_review(
        root=review_root,
        reference=semantic_review,
        review_material=review_material,
        runtime=contract_runtime,
    )

    with _parent_lock(target):
        candidates = sorted(target.parent.glob(f".{target.name}.authority-revision-*.staging"))
        foreign = [path for path in candidates if path != staging]
        if foreign or len(candidates) > 1:
            _fail("REV_STAGING_AMBIGUOUS", str([str(path) for path in candidates]))
        if target.exists():
            if staging.exists():
                _fail("REV_TARGET_AND_STAGING_COLLISION", str(target))
            if not target.is_dir():
                _fail("REV_TARGET_COLLISION", str(target))
            context = _context_from_root(
                target, transaction_id=transaction_id, runtime=contract_runtime,
                replayed=True,
            )
            if context.semantic_review.reference["sha256"] != semantic_review["sha256"]:
                _fail("REV_REVIEW_REPLAY_MISMATCH", "sealed review differs from target")
            return context
        if staging.exists() and not staging.is_dir():
            _fail("REV_STAGING_FOREIGN", str(staging))
        staging.mkdir(parents=False, exist_ok=True)

        intent = {
            "schema_version": "1.0",
            "kind": "authority-revision-bootstrap-intent",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "source_kind": "authority_revision",
            "parent_run": {
                "path": parent.as_posix(),
                "identity_sha256": canonical_sha256(parent.as_posix()),
            },
            "material_sha256": material_digest,
            "target_name": target.name,
            "status": "prepared",
        }
        _validate_schema(contract_runtime, intent, "authority-revision-bootstrap-intent.schema.json")
        _write_json(staging / "authority-revision" / "bootstrap-intent.json", intent)

        evidence, evidence_sources = _copy_evidence(
            staging,
            evidence_bindings=evidence_bindings,
            evidence_roots=evidence_roots,
        )
        evidence_index = {
            "schema_version": "1.0",
            "kind": "authority-revision-evidence-index",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "evidence": evidence,
            "source_bindings": evidence_sources,
            "status": "sealed",
        }
        _validate_schema(contract_runtime, evidence_index, "authority-revision-evidence-index.schema.json")
        _write_json(staging / "authority-revision" / "evidence-index.json", evidence_index)
        evidence_ref = _reference(staging / "authority-revision" / "evidence-index.json", root=staging)

        directive = {
            "schema_version": "1.0",
            "kind": "author-directive-binding",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "author_text": author_text,
            "author_text_sha256": _text_sha256(author_text),
            "author_approved_bytes": False,
            "clauses": clauses,
            "evidence_index": evidence_ref,
            "required_evidence": {label: evidence[label] for label in sorted(REQUIRED_EVIDENCE_LABELS)},
            "status": "sealed",
        }
        _validate_schema(contract_runtime, directive, "author-directive-binding.schema.json")
        _write_json(staging / "authority-revision" / "author-directive-binding.json", directive)
        directive_ref = _reference(staging / "authority-revision" / "author-directive-binding.json", root=staging)

        prepared_edits, artifacts = _apply_patch_plan(
            staging,
            source_root=sources,
            edits=edits,
            directive_clause_ids=set(clause_ids),
        )
        patch_plan = {
            "schema_version": "1.0",
            "kind": "authority-revision-patch-plan",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "producer": producer,
            "candidate_material_sha256": material_digest,
            "allowset": sorted(AUTHORITY_REVISION_ALLOWSET),
            "directive_binding": directive_ref,
            "edits": prepared_edits,
            "artifacts": artifacts,
            "status": "sealed",
        }
        _validate_schema(contract_runtime, patch_plan, "authority-revision-patch-plan.schema.json")
        _write_json(staging / "authority-revision" / "patch-plan.json", patch_plan)
        patch_ref = _reference(staging / "authority-revision" / "patch-plan.json", root=staging)

        _write_exact(
            staging / "authority-revision" / "semantic-review.json", review_raw
        )
        review_ref = _reference(staging / "authority-revision" / "semantic-review.json", root=staging)

        finalization = {
            "schema_version": "1.0",
            "kind": "authority-revision-finalization",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "source_kind": "authority_revision",
            "parent_run": evidence["parent_state"],
            "parent_final_completion": evidence["parent_final_completion"],
            "evidence_index": evidence_ref,
            "directive_binding": directive_ref,
            "patch_plan": patch_ref,
            "semantic_review": review_ref,
            "base_artifacts": [item["base_artifact"] for item in artifacts],
            "effective_artifacts": [item["effective_artifact"] for item in artifacts],
            "author_approved_bytes": False,
            "status": "ready",
        }
        _validate_schema(contract_runtime, finalization, "authority-revision-finalization.schema.json")
        _write_json(staging / "authority-revision" / "finalization.json", finalization)
        finalization_ref = _reference(staging / "authority-revision" / "finalization.json", root=staging)

        coordinator = AutonomousCoordinator.initialize(
            run_id=run_id,
            source_interview_state=evidence["parent_state"],
            state_path="state/revision-000.json",
            runtime=contract_runtime,
        )
        state_data = coordinator.state
        state_data["source_kind"] = "authority_revision"
        state_data["authority_revision"] = finalization_ref
        state = _sealed(state_data, "state/revision-000.json")
        coordinator = AutonomousCoordinator.from_snapshot(state.data, state.reference, runtime=contract_runtime)
        _write_json(staging / "state" / "revision-000.json", state.data)

        qualification_id = canonical_sha256(
            [
                "contract_bootstrap",
                CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
                {
                    stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]["model_schema_version"]
                    for stage in ("E1", "T1")
                },
            ]
        )[:24]
        qualification = {
            "schema_version": "1.0",
            "migration_id": qualification_id,
            "reason": "contract_bootstrap",
            "old_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "new_contract_digest": CURRENT_CONCEPTION_PRODUCTION_CONTRACT_SHA256,
            "invalidated_stages": [],
            "production_versions": {
                stage: CURRENT_CONCEPTION_PRODUCTION_CONTRACT[stage]["model_schema_version"]
                for stage in ("E1", "T1")
            },
            "production_contract": CURRENT_CONCEPTION_PRODUCTION_CONTRACT,
            "session_invalidation_receipts": [],
            "work_order_invalidation_receipts": [],
            "completion_invalidation_receipts": [],
            "status": "complete",
        }
        qualification_path = (
            staging / "orchestration" / "contract-upgrades"
            / f"{qualification_id}.complete.json"
        )
        _write_json(qualification_path, qualification)
        qualification_ref = _reference(qualification_path, root=staging)
        validation = {
            "schema_version": "1.0",
            "kind": "authority-revision-bootstrap-validation",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "state": state.reference,
            "finalization": finalization_ref,
            "checks": [
                "parent-evidence-hash-bound",
                "author-approved-bytes-false",
                "patch-allowset-exact",
                "text-edits-non-overlapping",
                "non-target-controls-byte-stable",
                "independent-semantic-review",
            ],
            "verdict": "ready",
        }
        _validate_schema(contract_runtime, validation, "authority-revision-bootstrap-validation.schema.json")
        _write_json(staging / "authority-revision" / "bootstrap-validation.json", validation)
        validation_ref = _reference(staging / "authority-revision" / "bootstrap-validation.json", root=staging)
        completion = {
            "schema_version": "1.0",
            "kind": "authority-revision-bootstrap-completion",
            "transaction_id": transaction_id,
            "run_id": run_id,
            "source_kind": "authority_revision",
            "state": state.reference,
            "finalization": finalization_ref,
            "validation": validation_ref,
            "status": "ready",
        }
        _validate_schema(contract_runtime, completion, "authority-revision-bootstrap-completion.schema.json")
        _write_json(staging / "authority-revision" / "bootstrap-completion.json", completion)
        completion_ref = _reference(staging / "authority-revision" / "bootstrap-completion.json", root=staging)
        _write_json(
            staging / "orchestration" / "current-state.json",
            {"schema_version": "2.0", "state": state.reference},
        )
        _write_json(
            staging / "orchestration" / "current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": qualification_ref},
        )
        pointer = {
            "schema_version": "1.0",
            "transaction_id": transaction_id,
            "completion": completion_ref,
        }
        _write_json(staging / "orchestration" / "authority-revision" / "current-bootstrap.json", pointer)
        _validate_completed_root(staging, transaction_id=transaction_id, runtime=contract_runtime)
        try:
            staging.replace(target)
        except FileExistsError:
            _fail("REV_TARGET_COLLISION", str(target))
        _validate_completed_root(target, transaction_id=transaction_id, runtime=contract_runtime)

    return _context_from_root(
        target, transaction_id=transaction_id, runtime=contract_runtime,
        replayed=False,
    )


def validate_conception_revision_run(
    run_root: str | Path, *, runtime: ContractRuntime | None = None
) -> ConceptionRevisionContext:
    """Read-only validation of a completed authority-revision bootstrap."""

    root = Path(run_root).resolve()
    completion_path = root / "authority-revision" / "bootstrap-completion.json"
    if not completion_path.is_file():
        _fail("REV_BOOTSTRAP_INCOMPLETE", str(root))
    completion = _load_json(completion_path)
    transaction_id = completion.get("transaction_id")
    if not isinstance(transaction_id, str) or re.fullmatch(r"[0-9a-f]{24}", transaction_id) is None:
        _fail("REV_BOOTSTRAP_INVALID", "transaction_id")
    return _context_from_root(
        root,
        transaction_id=transaction_id,
        runtime=runtime or ContractRuntime(),
        replayed=True,
    )


__all__ = [
    "AUTHORITY_REVISION_ALLOWSET",
    "REQUIRED_EVIDENCE_LABELS",
    "ConceptionRevisionContext",
    "ConceptionRevisionError",
    "build_authority_revision_review_material",
    "initialize_conception_revision_run",
    "validate_conception_revision_run",
]
