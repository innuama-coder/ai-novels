"""Canonical JSON, hashing, path containment and schema validation utilities."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Raised when a deterministic contract fails."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_bytes(value: Any) -> bytes:
    """Canonical UTF-8 JSON document bytes with one final newline."""
    return (canonical_json(value) + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def safe_relative(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise ContractError("path must be a nonempty relative POSIX path")
    result = PurePosixPath(value)
    if result.is_absolute() or ".." in result.parts or "." in result.parts:
        raise ContractError("path escapes or is not normalized")
    return result


def resolve_inside(root: Path, relative: Any, *, must_exist: bool = True, file_only: bool = True) -> Path:
    rel = safe_relative(relative)
    candidate = root.joinpath(*rel.parts).resolve(strict=must_exist)
    try:
        candidate.relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise ContractError(f"path escapes declared root: {relative}") from error
    if must_exist and file_only and not candidate.is_file():
        raise ContractError(f"reference is not a file: {relative}")
    return candidate


def file_ref(path: Path, *, root: Path, role: str) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(root.resolve(strict=True)).as_posix()
    except ValueError as error:
        raise ContractError(f"artifact is outside root: {path}") from error
    return {"role": role, "path": relative, "sha256": sha256_file(resolved)}


def verify_file_ref(ref: Mapping[str, Any], root: Path, *, expected_role: str | None = None) -> Path:
    if set(ref) != {"role", "path", "sha256"}:
        raise ContractError("file reference fields must be role/path/sha256")
    if expected_role is not None and ref.get("role") != expected_role:
        raise ContractError(f"unexpected artifact role: {ref.get('role')}")
    expected = ref.get("sha256")
    if not isinstance(expected, str) or SHA_RE.fullmatch(expected) is None:
        raise ContractError("invalid SHA-256")
    path = resolve_inside(root, ref.get("path"))
    actual = sha256_file(path)
    if not hmac.compare_digest(actual, expected):
        raise ContractError(f"hash mismatch: {ref.get('path')}")
    return path


def json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ContractError("invalid RFC 6901 pointer")
    current = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if "~" in raw.replace("~1", "").replace("~0", ""):
            raise ContractError("invalid JSON Pointer escape")
        if isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token[0] == "0"):
                raise ContractError(f"invalid array index in pointer: {token}")
            index = int(token)
            if index >= len(current):
                raise ContractError(f"array index out of range: {token}")
            current = current[index]
        elif isinstance(current, dict):
            if token not in current:
                raise ContractError(f"missing pointer token: {token}")
            current = current[token]
        else:
            raise ContractError(f"pointer traverses scalar at: {token}")
    return current
