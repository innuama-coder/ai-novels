"""Official Draft 2020-12 runtime for autonomous conception V2 contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from .canonical import canonical_sha256, sha256_file


DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"
DEFAULT_SCHEMA_DIRECTORY = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "ai-novel-workflow"
    / "contracts"
    / "autonomous-v2"
)


class ContractRuntimeError(RuntimeError):
    """Base error for an unusable contract runtime."""


class SchemaCatalogError(ContractRuntimeError):
    """Raised when authoritative schemas cannot form a closed catalog."""


@dataclass(frozen=True)
class ValidationDiagnostic:
    """A stable, serializable Draft 2020-12 validation diagnostic."""

    code: str
    instance_path: str
    schema_path: str
    keyword: str
    object_id: str | None
    message: str

    def as_record(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "instance_path": self.instance_path,
            "schema_path": self.schema_path,
            "keyword": self.keyword,
            "object_id": self.object_id,
            "message": self.message,
        }

    def render(self) -> str:
        object_id = self.object_id if self.object_id is not None else "-"
        return (
            f"{self.code} | instance={self.instance_path} | "
            f"schema={self.schema_path} | keyword={self.keyword} | "
            f"object_id={object_id} | {self.message}"
        )


class ContractValidationError(ValueError):
    """Raised when an instance violates an authoritative contract."""

    def __init__(
        self, schema_name: str, diagnostics: Iterable[ValidationDiagnostic]
    ):
        self.schema_name = schema_name
        self.diagnostics = tuple(diagnostics)
        self.messages = tuple(item.render() for item in self.diagnostics)
        detail = "\n".join(self.messages[:20])
        super().__init__(f"{schema_name} validation failed:\n{detail}")

    def as_records(self) -> list[dict[str, str | None]]:
        return [diagnostic.as_record() for diagnostic in self.diagnostics]


def _walk_refs(value: Any) -> Iterator[str]:
    if isinstance(value, Mapping):
        reference = value.get("$ref")
        if isinstance(reference, str):
            yield reference
        for child in value.values():
            yield from _walk_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_refs(child)


def _json_path(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(part)):
            result += f".{part}"
        else:
            result += f"[{json.dumps(str(part), ensure_ascii=False)}]"
    return result


def _error_code(keyword: Any) -> str:
    raw = str(keyword) if keyword is not None else "unknown"
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", raw)
    token = re.sub(r"[^A-Za-z0-9]+", "_", separated).strip("_").upper()
    return f"V2_SCHEMA_{token or 'UNKNOWN'}"


def _nearby_object_id(instance: Any, path: Iterable[Any]) -> str | None:
    current = instance
    object_id: str | None = None
    if isinstance(current, Mapping):
        candidate = current.get("id")
        if isinstance(candidate, str) and candidate:
            object_id = candidate
    for part in path:
        try:
            if isinstance(current, Mapping):
                current = current[part]
            elif isinstance(current, list) and isinstance(part, int):
                current = current[part]
            else:
                break
        except (KeyError, IndexError, TypeError):
            break
        if isinstance(current, Mapping):
            candidate = current.get("id")
            if isinstance(candidate, str) and candidate:
                object_id = candidate
    return object_id


class ContractRuntime:
    """Load, self-check, and execute the closed autonomous-v2 schema catalog."""

    def __init__(
        self,
        schema_dir: str | Path = DEFAULT_SCHEMA_DIRECTORY,
        *,
        expected_schema_count: int | None = 32,
    ):
        self.schema_dir = Path(schema_dir).resolve()
        self.expected_schema_count = expected_schema_count
        self._schemas: dict[str, dict[str, Any]] | None = None
        self._paths: dict[str, Path] | None = None
        self._registry: Registry | None = None
        self._checked = False

    @property
    def schema_names(self) -> tuple[str, ...]:
        self._load_catalog()
        assert self._schemas is not None
        return tuple(sorted(self._schemas))

    def _load_catalog(self) -> None:
        if self._schemas is not None:
            return
        if not self.schema_dir.is_dir():
            raise SchemaCatalogError(
                f"schema directory does not exist: {self.schema_dir}"
            )

        paths = sorted(self.schema_dir.glob("*.schema.json"))
        if self.expected_schema_count is not None and len(paths) != self.expected_schema_count:
            raise SchemaCatalogError(
                f"expected {self.expected_schema_count} schemas, found {len(paths)}"
            )

        schemas: dict[str, dict[str, Any]] = {}
        schema_paths: dict[str, Path] = {}
        resources: list[tuple[str, Resource]] = []
        for path in paths:
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise SchemaCatalogError(f"cannot load {path.name}: {error}") from error
            if not isinstance(schema, dict):
                raise SchemaCatalogError(f"{path.name} root must be an object")
            if schema.get("$schema") != DRAFT_2020_12_URI:
                raise SchemaCatalogError(
                    f"{path.name} does not declare JSON Schema Draft 2020-12"
                )
            schema_id = schema.get("$id")
            if schema_id != path.name:
                raise SchemaCatalogError(
                    f"{path.name} must use its filename as relative $id"
                )
            if schema_id in schemas:
                raise SchemaCatalogError(f"duplicate schema $id: {schema_id}")
            schemas[schema_id] = schema
            schema_paths[schema_id] = path
            try:
                resources.append((schema_id, Resource.from_contents(schema)))
            except Exception as error:
                raise SchemaCatalogError(
                    f"cannot register {path.name}: {error}"
                ) from error

        self._schemas = schemas
        self._paths = schema_paths
        self._registry = Registry().with_resources(resources)

    def load_schema(self, name: str) -> dict[str, Any]:
        """Return an authoritative schema by exact catalog name."""

        self._load_catalog()
        assert self._schemas is not None
        try:
            return self._schemas[name]
        except KeyError as error:
            raise SchemaCatalogError(f"unknown schema: {name}") from error

    def check_all_schemas(self) -> tuple[str, ...]:
        """Meta-validate every schema and prove every local reference resolves."""

        self._load_catalog()
        assert self._schemas is not None
        assert self._registry is not None
        if self._checked:
            return self.schema_names

        for name in self.schema_names:
            schema = self._schemas[name]
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError as error:
                raise SchemaCatalogError(
                    f"{name} is not a valid Draft 2020-12 schema: {error.message}"
                ) from error

            resolver = self._registry.resolver(base_uri=name)
            for reference in _walk_refs(schema):
                try:
                    resolver.lookup(reference)
                except (Unresolvable, LookupError, KeyError) as error:
                    raise SchemaCatalogError(
                        f"{name} has unresolved $ref {reference!r}: {error}"
                    ) from error

        self._checked = True
        return self.schema_names

    def _validator(self, name: str) -> Draft202012Validator:
        self.check_all_schemas()
        assert self._registry is not None
        return Draft202012Validator(self.load_schema(name), registry=self._registry)

    @staticmethod
    def _diagnostics(
        instance: Any, errors: Iterable[Any]
    ) -> list[ValidationDiagnostic]:
        diagnostics = [
            ValidationDiagnostic(
                code=_error_code(error.validator),
                instance_path=_json_path(error.absolute_path),
                schema_path=_json_path(error.absolute_schema_path),
                keyword=str(error.validator or "unknown"),
                object_id=_nearby_object_id(instance, error.absolute_path),
                message=error.message,
            )
            for error in errors
        ]
        diagnostics.sort(
            key=lambda item: (
                item.instance_path,
                item.schema_path,
                item.code,
                item.object_id or "",
                item.message,
            )
        )
        return diagnostics

    def validate(self, instance: Any, schema_name: str) -> None:
        """Raise :class:`ContractValidationError` for any contract violation."""

        diagnostics = self._diagnostics(
            instance,
            self._validator(schema_name).iter_errors(instance)
        )
        if diagnostics:
            raise ContractValidationError(schema_name, diagnostics)

    def is_valid(self, instance: Any, schema_name: str) -> bool:
        """Return whether *instance* satisfies the named authoritative schema."""

        return self._validator(schema_name).is_valid(instance)

    def validate_definition(
        self, instance: Any, schema_name: str, definition_name: str
    ) -> None:
        """Validate against a named top-level ``$defs`` entry."""

        schema = self.load_schema(schema_name)
        definitions = schema.get("$defs")
        if not isinstance(definitions, Mapping) or definition_name not in definitions:
            raise SchemaCatalogError(
                f"{schema_name} has no $defs entry {definition_name!r}"
            )
        self.check_all_schemas()
        assert self._registry is not None
        wrapper_name = "__runtime-definition-wrapper__.schema.json"
        wrapper = {
            "$schema": DRAFT_2020_12_URI,
            "$id": wrapper_name,
            "$ref": f"{schema_name}#/$defs/{definition_name}",
        }
        validator = Draft202012Validator(wrapper, registry=self._registry)
        diagnostics = self._diagnostics(instance, validator.iter_errors(instance))
        if diagnostics:
            raise ContractValidationError(
                f"{schema_name}#/$defs/{definition_name}", diagnostics
            )

    def schema_sha256(self, name: str) -> str:
        """Hash an authoritative schema's exact bytes."""

        self._load_catalog()
        assert self._paths is not None
        try:
            return sha256_file(self._paths[name])
        except KeyError as error:
            raise SchemaCatalogError(f"unknown schema: {name}") from error

    def catalog_sha256(self) -> str:
        """Hash the ordered filename-to-file-hash catalog."""

        return canonical_sha256(
            {name: self.schema_sha256(name) for name in self.schema_names}
        )
