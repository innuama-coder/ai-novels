from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from runtime.canonical import ContractError  # noqa: E402
from runtime.schema_catalog import SchemaCatalog  # noqa: E402


class StandardLibrarySchemaCatalogTests(unittest.TestCase):
    def test_runtime_has_no_jsonschema_dependency(self) -> None:
        self.assertIsNone(importlib.util.find_spec("jsonschema"))
        self.assertIsNone(importlib.util.find_spec("referencing"))

    def test_released_catalog_compiles(self) -> None:
        catalog = SchemaCatalog(HARNESS_ROOT / "schemas")
        self.assertGreaterEqual(len(catalog.schemas), 16)

    def test_refs_object_array_and_closed_properties(self) -> None:
        catalog = SchemaCatalog.from_documents({
            "common": {
                "$id": "common.schema.json",
                "$defs": {"id": {"type": "string", "pattern": "^[A-Z]+$"}},
            },
            "root": {
                "$id": "root.schema.json",
                "type": "object",
                "required": ["id", "values"],
                "properties": {
                    "id": {"$ref": "common.schema.json#/$defs/id"},
                    "values": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "integer", "minimum": 1}},
                },
                "additionalProperties": False,
            },
        })
        catalog.validate({"id": "ABC", "values": [1, 2]}, "root")
        for invalid in (
            {"id": "abc", "values": [1]},
            {"id": "ABC", "values": [1, 1]},
            {"id": "ABC", "values": [0]},
            {"id": "ABC", "values": [1], "extra": True},
        ):
            with self.assertRaises(ContractError):
                catalog.validate(invalid, "root")

    def test_one_of_and_conditional_semantics(self) -> None:
        catalog = SchemaCatalog.from_documents({
            "root": {
                "$id": "conditional.schema.json",
                "type": "object",
                "required": ["kind", "value"],
                "properties": {
                    "kind": {"enum": ["text", "count"]},
                    "value": {},
                },
                "additionalProperties": False,
                "allOf": [{
                    "if": {"properties": {"kind": {"const": "text"}}, "required": ["kind"]},
                    "then": {"properties": {"value": {"type": "string", "minLength": 1}}},
                    "else": {"properties": {"value": {"type": "integer", "minimum": 1}}},
                }],
            },
        })
        catalog.validate({"kind": "text", "value": "x"}, "root")
        catalog.validate({"kind": "count", "value": 2}, "root")
        with self.assertRaises(ContractError):
            catalog.validate({"kind": "text", "value": 2}, "root")

    def test_date_time_and_unsupported_keyword_fail_closed(self) -> None:
        catalog = SchemaCatalog.from_documents({
            "root": {"$id": "time.schema.json", "type": "string", "format": "date-time"},
        })
        catalog.validate("2026-08-06T12:00:00Z", "root")
        with self.assertRaises(ContractError):
            catalog.validate("2026-08-06", "root")
        with self.assertRaises(ContractError):
            SchemaCatalog.from_documents({"bad": {"$id": "bad.schema.json", "not": {"type": "string"}}})

    def test_union_type_used_by_review_contracts(self) -> None:
        catalog = SchemaCatalog.from_documents({
            "root": {"$id": "union.schema.json", "type": ["string", "null"]},
        })
        catalog.validate("resolution-ref", "root")
        catalog.validate(None, "root")
        with self.assertRaises(ContractError):
            catalog.validate(1, "root")

    def test_maximum_is_enforced_for_public_review_contracts(self) -> None:
        catalog = SchemaCatalog.from_documents({"root": {"$id": "bounded.schema.json", "type": "number", "maximum": 10}})
        catalog.validate(10, "root")
        with self.assertRaises(ContractError):
            catalog.validate(10.1, "root")


if __name__ == "__main__":
    unittest.main()
