"""Dependency-free JSON Schema subset used by every HLD runtime component.

The released contracts intentionally use a bounded Draft 2020-12 vocabulary.
This module implements that vocabulary with the Python standard library so the
Codex runtime does not depend on an ambient ``jsonschema`` installation.
Unsupported schema keywords fail catalog construction instead of being ignored.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .canonical import ContractError

SUPPORTED_KEYWORDS = {
    "$schema", "$id", "$defs", "$ref", "title", "type", "properties",
    "required", "additionalProperties", "items", "minItems", "maxItems",
    "uniqueItems", "minLength", "pattern", "minimum", "enum", "const",
    "oneOf", "allOf", "if", "then", "else", "format", "maximum",
}
JSON_TYPES = {"null", "boolean", "object", "array", "string", "integer", "number"}


@dataclass(frozen=True)
class ValidationIssue:
    absolute_path: tuple[str | int, ...]
    message: str


def _pointer(document: Any, fragment: str) -> Any:
    if fragment in {"", "#"}:
        return document
    if not fragment.startswith("#/"):
        raise ContractError(f"unsupported schema reference fragment: {fragment}")
    current = document
    for raw in fragment[2:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ContractError(f"invalid schema reference escape: {fragment}")
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ContractError(f"unresolved schema reference: {fragment}")
    return current


def _schema_children(schema: Mapping[str, Any]) -> Iterable[tuple[str, Any]]:
    for container in ("$defs", "properties"):
        values = schema.get(container, {})
        if isinstance(values, dict):
            for name, child in values.items():
                yield f"{container}/{name}", child
    for key in ("additionalProperties", "items", "if", "then", "else"):
        child = schema.get(key)
        if isinstance(child, (dict, bool)):
            yield key, child
    for container in ("oneOf", "allOf"):
        values = schema.get(container, [])
        if isinstance(values, list):
            for index, child in enumerate(values):
                yield f"{container}/{index}", child


def _check_schema(schema: Any, location: str = "$") -> None:
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise ContractError(f"schema at {location} must be an object or boolean")
    unknown = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unknown:
        raise ContractError(f"unsupported schema keyword at {location}: {unknown[0]}")
    if "type" in schema:
        declared = schema["type"]
        if isinstance(declared, str):
            valid_type = declared in JSON_TYPES
        else:
            valid_type = (
                isinstance(declared, list) and bool(declared)
                and all(isinstance(item, str) and item in JSON_TYPES for item in declared)
                and len(declared) == len(set(declared))
            )
        if not valid_type:
            raise ContractError(f"invalid type at {location}: {declared!r}")
    for key in ("$schema", "$id", "$ref", "title", "pattern", "format"):
        if key in schema and not isinstance(schema[key], str):
            raise ContractError(f"{key} at {location} must be a string")
    for key in ("$defs", "properties"):
        if key in schema and not isinstance(schema[key], dict):
            raise ContractError(f"{key} at {location} must be an object")
    if "required" in schema:
        required = schema["required"]
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required) or len(required) != len(set(required)):
            raise ContractError(f"required at {location} must contain unique strings")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], (dict, bool)):
        raise ContractError(f"additionalProperties at {location} must be a schema or boolean")
    for key in ("minItems", "maxItems", "minLength"):
        if key in schema and (not isinstance(schema[key], int) or isinstance(schema[key], bool) or schema[key] < 0):
            raise ContractError(f"{key} at {location} must be a non-negative integer")
    if "minimum" in schema and (not isinstance(schema["minimum"], (int, float)) or isinstance(schema["minimum"], bool) or not math.isfinite(schema["minimum"])):
        raise ContractError(f"minimum at {location} must be a finite number")
    if "maximum" in schema and (not isinstance(schema["maximum"], (int, float)) or isinstance(schema["maximum"], bool) or not math.isfinite(schema["maximum"])):
        raise ContractError(f"maximum at {location} must be a finite number")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise ContractError(f"uniqueItems at {location} must be boolean")
    for key in ("oneOf", "allOf", "enum"):
        if key in schema and (not isinstance(schema[key], list) or not schema[key]):
            raise ContractError(f"{key} at {location} must be a non-empty array")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except re.error as error:
            raise ContractError(f"invalid pattern at {location}: {error}") from error
    for name, child in _schema_children(schema):
        _check_schema(child, f"{location}/{name}")


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
    }[expected]


def _valid_datetime(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return True


class SchemaCatalog:
    def __init__(self, directory: Path | None = None, *, documents: Mapping[str, Any] | None = None):
        if (directory is None) == (documents is None):
            raise ContractError("provide exactly one schema directory or document mapping")
        raw: dict[str, Any] = {}
        if directory is not None:
            self.directory = directory.resolve(strict=True)
            for path in sorted(self.directory.glob("*.schema.json")):
                raw[path.name] = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.directory = None
            raw = dict(documents or {})
        if not raw:
            raise ContractError("empty schema catalog")
        self.schemas: dict[str, Any] = {}
        self.role_ids: dict[str, str] = {}
        for role, schema in raw.items():
            _check_schema(schema)
            schema_id = schema.get("$id") if isinstance(schema, dict) else None
            if not isinstance(schema_id, str) or not schema_id:
                raise ContractError(f"schema lacks $id: {role}")
            if directory is not None and schema_id != role:
                raise ContractError(f"schema id mismatch: {role}")
            if schema_id in self.schemas:
                raise ContractError(f"duplicate schema id: {schema_id}")
            self.schemas[schema_id] = schema
            self.role_ids[role] = schema_id
        for schema_id, schema in self.schemas.items():
            self._check_references(schema, schema_id)

    @classmethod
    def from_documents(cls, documents: Mapping[str, Any]) -> "SchemaCatalog":
        return cls(documents=documents)

    def _resolve(self, reference: str, current_id: str) -> tuple[Any, str]:
        target_name, marker, fragment = reference.partition("#")
        target_id = target_name or current_id
        if target_id not in self.schemas:
            raise ContractError(f"unknown schema reference: {reference}")
        return _pointer(self.schemas[target_id], "#" + fragment if marker else ""), target_id

    def _check_references(self, schema: Any, current_id: str) -> None:
        if isinstance(schema, bool):
            return
        reference = schema.get("$ref")
        if reference is not None:
            self._resolve(reference, current_id)
        for _, child in _schema_children(schema):
            self._check_references(child, current_id)

    def _issues(self, value: Any, schema: Any, current_id: str, path: tuple[str | int, ...]) -> list[ValidationIssue]:
        if schema is True:
            return []
        if schema is False:
            return [ValidationIssue(path, "value is rejected by false schema")]
        issues: list[ValidationIssue] = []
        if "$ref" in schema:
            target, target_id = self._resolve(schema["$ref"], current_id)
            issues.extend(self._issues(value, target, target_id, path))
        if "type" in schema:
            declared_types = [schema["type"]] if isinstance(schema["type"], str) else schema["type"]
            if not any(_type_matches(value, expected) for expected in declared_types):
                return issues + [ValidationIssue(path, f"expected {' or '.join(declared_types)}")]
        if "const" in schema and not _json_equal(value, schema["const"]):
            issues.append(ValidationIssue(path, f"value must equal {schema['const']!r}"))
        if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
            issues.append(ValidationIssue(path, "value is not in enum"))
        if "allOf" in schema:
            for child in schema["allOf"]:
                issues.extend(self._issues(value, child, current_id, path))
        if "oneOf" in schema:
            matches = sum(not self._issues(value, child, current_id, path) for child in schema["oneOf"])
            if matches != 1:
                issues.append(ValidationIssue(path, f"value must match exactly one oneOf branch; matched {matches}"))
        if "if" in schema:
            condition_matches = not self._issues(value, schema["if"], current_id, path)
            branch = schema.get("then") if condition_matches else schema.get("else")
            if branch is not None:
                issues.extend(self._issues(value, branch, current_id, path))
        if isinstance(value, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in value:
                    issues.append(ValidationIssue(path, f"missing required property: {key}"))
            properties = schema.get("properties", {})
            for key, child in properties.items():
                if key in value:
                    issues.extend(self._issues(value[key], child, current_id, path + (key,)))
            extras = [key for key in value if key not in properties]
            additional = schema.get("additionalProperties", True)
            if additional is False and extras:
                issues.append(ValidationIssue(path, f"additional property is not allowed: {sorted(extras)[0]}"))
            elif isinstance(additional, dict):
                for key in extras:
                    issues.extend(self._issues(value[key], additional, current_id, path + (key,)))
        if isinstance(value, list):
            if "minItems" in schema and len(value) < schema["minItems"]:
                issues.append(ValidationIssue(path, f"array has fewer than {schema['minItems']} items"))
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                issues.append(ValidationIssue(path, f"array has more than {schema['maxItems']} items"))
            if schema.get("uniqueItems"):
                for index, item in enumerate(value):
                    if any(_json_equal(item, prior) for prior in value[:index]):
                        issues.append(ValidationIssue(path + (index,), "array items must be unique"))
                        break
            if "items" in schema:
                for index, item in enumerate(value):
                    issues.extend(self._issues(item, schema["items"], current_id, path + (index,)))
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                issues.append(ValidationIssue(path, f"string is shorter than {schema['minLength']}") )
            if "pattern" in schema and re.search(schema["pattern"], value) is None:
                issues.append(ValidationIssue(path, f"string does not match pattern {schema['pattern']!r}"))
            if schema.get("format") == "date-time" and not _valid_datetime(value):
                issues.append(ValidationIssue(path, "string is not RFC 3339 date-time"))
            elif schema.get("format") not in {None, "date-time"}:
                issues.append(ValidationIssue(path, f"unsupported format: {schema['format']}"))
        if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
            issues.append(ValidationIssue(path, f"number is less than minimum {schema['minimum']}"))
        if isinstance(value, (int, float)) and not isinstance(value, bool) and "maximum" in schema and value > schema["maximum"]:
            issues.append(ValidationIssue(path, f"number is greater than maximum {schema['maximum']}"))
        return issues

    def iter_errors(self, value: Any, schema_name_or_role: str) -> list[ValidationIssue]:
        schema_id = self.role_ids.get(schema_name_or_role, schema_name_or_role)
        if schema_id not in self.schemas:
            raise ContractError(f"unknown schema: {schema_name_or_role}")
        return sorted(self._issues(value, self.schemas[schema_id], schema_id, ()), key=lambda item: (item.absolute_path, item.message))

    def validate(self, value: Any, schema_name_or_role: str) -> None:
        errors = self.iter_errors(value, schema_name_or_role)
        if errors:
            first = errors[0]
            pointer = "/" + "/".join(str(part) for part in first.absolute_path)
            raise ContractError(f"{schema_name_or_role}{pointer}: {first.message}")
