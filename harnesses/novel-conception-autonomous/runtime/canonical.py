"""Deterministic JSON, SHA-256, and package-manifest integrity primitives.

The canonical representation is deliberately small and explicit: UTF-8 JSON,
lexicographically sorted object keys, no insignificant whitespace, no trailing
newline, and no non-finite numbers.  It is not a claim of RFC 8785 support; it
is the repository's stable V2 representation for JSON-compatible Python data.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented as canonical JSON."""


class ManifestIntegrityError(ValueError):
    """Raised when a manifest reference is unsafe, stale, or unbound."""


def canonical_json(value: Any) -> str:
    """Return the deterministic V2 JSON representation of *value*."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise CanonicalizationError(f"value is not canonical JSON: {error}") from error


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical JSON encoded as UTF-8 without a byte-order mark."""

    return canonical_json(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Hash the exact canonical JSON bytes for *value*."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 of a file's exact bytes."""

    file_path = Path(path)
    digest = hashlib.sha256()
    with file_path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(path: str) -> PurePosixPath:
    if not isinstance(path, str) or not path:
        raise ManifestIntegrityError("artifact path must be a non-empty string")
    if "\\" in path:
        raise ManifestIntegrityError("artifact path must use POSIX '/' separators")
    if _WINDOWS_DRIVE_PATTERN.match(path):
        raise ManifestIntegrityError("artifact path must not contain a drive prefix")
    relative = PurePosixPath(path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ManifestIntegrityError(
            f"artifact path must be a normalized relative path: {path!r}"
        )
    if relative.as_posix() != path:
        raise ManifestIntegrityError(
            f"artifact path has a noncanonical alias: {path!r}"
        )
    return relative


def resolve_artifact_path(path: str, *, root: str | Path) -> Path:
    """Resolve a manifest path below *root* and reject traversal or absolutes."""

    relative = _safe_relative_path(path)
    root_path = Path(root).resolve()
    candidate = root_path.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(root_path)
    except ValueError as error:
        raise ManifestIntegrityError(
            f"artifact path escapes package root: {path!r}"
        ) from error
    return candidate


def artifact_reference(path: str | Path, *, root: str | Path) -> dict[str, str]:
    """Create a relative POSIX path and exact byte hash for an existing file."""

    root_path = Path(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(root_path)
    except ValueError as error:
        raise ManifestIntegrityError(
            f"artifact is outside package root: {candidate}"
        ) from error
    if not candidate.is_file():
        raise ManifestIntegrityError(f"artifact is not a file: {candidate}")
    relative_text = relative.as_posix()
    _safe_relative_path(relative_text)
    return {"path": relative_text, "sha256": sha256_file(candidate)}


def _reference_key(reference: Mapping[str, Any]) -> tuple[str, str]:
    if set(reference) != {"path", "sha256"}:
        raise ManifestIntegrityError(
            "artifact reference must contain exactly path and sha256"
        )
    path = reference["path"]
    digest = reference["sha256"]
    _safe_relative_path(path)
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise ManifestIntegrityError("artifact sha256 must be 64 lowercase hex digits")
    return path, digest


def verify_artifact_reference(
    reference: Mapping[str, Any], *, root: str | Path
) -> Path:
    """Verify a reference resolves to an existing file with the bound hash."""

    path, expected = _reference_key(reference)
    candidate = resolve_artifact_path(path, root=root)
    if not candidate.is_file():
        raise ManifestIntegrityError(f"referenced artifact is missing: {path}")
    actual = sha256_file(candidate)
    if not hmac.compare_digest(actual, expected):
        raise ManifestIntegrityError(
            f"artifact hash mismatch for {path}: expected {expected}, got {actual}"
        )
    return candidate


def verify_manifest_integrity(
    manifest: Mapping[str, Any], *, root: str | Path
) -> None:
    """Verify file hashes and that every manifest reference is file-bound.

    JSON Schema remains responsible for package-profile shape.  This function
    enforces the cross-field and filesystem facts a schema cannot prove.
    """

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestIntegrityError("manifest files must be a non-empty array")

    bound: set[tuple[str, str]] = set()
    paths: set[str] = set()
    for reference in files:
        if not isinstance(reference, Mapping):
            raise ManifestIntegrityError("manifest file entry is not an object")
        key = _reference_key(reference)
        if key[0] in paths:
            raise ManifestIntegrityError(f"duplicate manifest file path: {key[0]}")
        paths.add(key[0])
        bound.add(key)
        verify_artifact_reference(reference, root=root)

    roles = manifest.get("artifact_roles")
    if not isinstance(roles, Mapping):
        raise ManifestIntegrityError("manifest artifact_roles must be an object")
    references: list[tuple[str, Mapping[str, Any]]] = []
    references.extend((f"artifact_roles.{role}", value) for role, value in roles.items())

    validation = manifest.get("validation")
    if not isinstance(validation, Mapping):
        raise ManifestIntegrityError("manifest validation must be an artifact reference")
    references.append(("validation", validation))

    implementation = manifest.get("implementation")
    if not isinstance(implementation, list) or not implementation:
        raise ManifestIntegrityError(
            "manifest implementation must be a non-empty reference array"
        )
    references.extend(
        (f"implementation[{index}]", value)
        for index, value in enumerate(implementation)
    )

    for label, reference in references:
        if not isinstance(reference, Mapping):
            raise ManifestIntegrityError(f"{label} is not an artifact reference")
        if _reference_key(reference) not in bound:
            raise ManifestIntegrityError(f"{label} is not bound in manifest files")
