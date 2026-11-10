from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractValidationError(AssertionError):
    pass


class SchemaRuntime:
    """Execute the Draft 2020-12 keyword subset used by autonomous-v2 contracts.

    This runtime intentionally fails when a contract starts using an unsupported
    validation keyword, so tests cannot silently treat an unexecuted constraint
    as valid.
    """

    VALIDATION_KEYWORDS = {
        "$ref",
        "type",
        "const",
        "enum",
        "required",
        "properties",
        "additionalProperties",
        "minProperties",
        "maxProperties",
        "items",
        "prefixItems",
        "minItems",
        "maxItems",
        "uniqueItems",
        "contains",
        "minContains",
        "maxContains",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
        "oneOf",
        "anyOf",
        "allOf",
        "not",
        "if",
        "then",
        "else",
    }
    ANNOTATION_KEYWORDS = {
        "$schema",
        "$id",
        "$defs",
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
    }

    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self._cache: dict[Path, dict[str, Any]] = {}

    def load(self, name: str | Path) -> tuple[Path, dict[str, Any]]:
        path = Path(name)
        if not path.is_absolute():
            path = self.schema_dir / path
        path = path.resolve()
        if path not in self._cache:
            self._cache[path] = json.loads(path.read_text(encoding="utf-8"))
        return path, self._cache[path]

    def assert_schema_keywords_supported(self, name: str | Path) -> None:
        path, schema = self.load(name)

        def walk_schema(value: Any) -> None:
            if isinstance(value, bool):
                return
            if not isinstance(value, dict):
                raise ContractValidationError(f"{path.name}: malformed subschema")
            for key, item in value.items():
                if key not in self.VALIDATION_KEYWORDS | self.ANNOTATION_KEYWORDS:
                    raise ContractValidationError(
                        f"{path.name}: unsupported schema keyword {key}"
                    )
                if key in {"properties", "$defs"}:
                    for subschema in item.values():
                        walk_schema(subschema)
                elif key in {
                    "additionalProperties",
                    "items",
                    "contains",
                    "not",
                    "if",
                    "then",
                    "else",
                } and isinstance(item, (dict, bool)):
                    walk_schema(item)
                elif key in {"prefixItems", "oneOf", "anyOf", "allOf"}:
                    for subschema in item:
                        walk_schema(subschema)

        walk_schema(schema)

    def assert_valid(self, instance: Any, name: str | Path) -> None:
        path, schema = self.load(name)
        errors = self._validate(instance, schema, path, "$")
        if errors:
            raise ContractValidationError("\n".join(errors[:20]))

    def assert_invalid(self, instance: Any, name: str | Path) -> None:
        path, schema = self.load(name)
        if not self._validate(instance, schema, path, "$"):
            raise ContractValidationError(
                f"{path.name}: invalid fixture unexpectedly passed"
            )

    @staticmethod
    def _artifact_key(reference: dict[str, Any]) -> tuple[str, str]:
        return reference["path"], reference["sha256"]

    @classmethod
    def assert_run_state_semantics(
        cls,
        state: dict[str, Any],
        *,
        active_request: dict[str, Any] | None = None,
        active_request_reference: dict[str, Any] | None = None,
    ) -> None:
        order = ["B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"]
        keys = set(state["current_stage_completions"])
        if keys != set(order[: len(keys)]):
            raise ContractValidationError(
                f"run-state current completions are not a canonical prefix: {sorted(keys)}"
            )
        if state["status"] == "approved" and keys != set(order):
            raise ContractValidationError("approved state must contain B0-H1")
        if state["active_return"] is not None and state["status"] != "revise":
            raise ContractValidationError("active return requires revise state")
        if state["status"] == "revise" and state["active_return"] is None:
            raise ContractValidationError("revise state requires active return")
        if state["active_return"] is not None:
            if active_request is None or active_request_reference is None:
                raise ContractValidationError(
                    "active return semantics require request and bound reference"
                )
            if state["active_return"] != active_request_reference:
                raise ContractValidationError(
                    "active return state does not bind supplied return request"
                )
            invalidated = set(active_request["invalidated_stages"])
            retained = keys & invalidated
            if retained:
                raise ContractValidationError(
                    f"active return retained invalidated current stages: {sorted(retained)}"
                )
            resume_index = order.index(active_request["resume_stage"])
            expected = set(order[:resume_index])
            if keys != expected:
                raise ContractValidationError(
                    "active return current completions are not the exact pre-resume prefix"
                )
            if (
                active_request.get("target_stage") != "H1"
                and active_request["invalidated_h1_artifacts"]
                == ["plan", "fragments", "assembly", "html", "completion"]
                and state.get("h1_workspace") is not None
            ):
                raise ContractValidationError(
                    "full H1 invalidation must clear the current H1 workspace"
                )
        if state["status"] == "approved" and state["development_status"] != "not_ready":
            raise ContractValidationError(
                "final completion, not run-state, grants development readiness"
            )
        current_refs = {
            cls._artifact_key(reference)
            for reference in state["current_stage_completions"].values()
        }
        superseded_refs = {
            cls._artifact_key(reference)
            for reference in state.get("superseded_completions", [])
        }
        seen_returns: set[str] = set()
        for resolved in state.get("resolved_returns", []):
            binding = resolved["return_binding"]
            return_id = binding["return_id"]
            if return_id in seen_returns:
                raise ContractValidationError(
                    f"resolved return {return_id} is recorded more than once"
                )
            seen_returns.add(return_id)
            completion = resolved["resolving_completion"]
            if completion["stage"] != binding["resume_stage"]:
                raise ContractValidationError(
                    f"return {return_id} resolved by {completion['stage']}, "
                    f"expected {binding['resume_stage']}"
                )
            if cls._artifact_key(completion) not in current_refs | superseded_refs:
                raise ContractValidationError(
                    f"return {return_id} resolving completion is neither current nor superseded"
                )

    @staticmethod
    def assert_baseline_semantics(
        baseline: dict[str, Any],
        *,
        extracted_controls_by_domain: dict[str, set[str]],
    ) -> None:
        inventory: dict[str, tuple[str, dict[str, Any]]] = {}
        for source in baseline["design_artifacts"]:
            extracted = extracted_controls_by_domain.get(source["domain"])
            if extracted is None:
                raise ContractValidationError(
                    f"missing independent control extraction for {source['domain']}"
                )
            if set(source["control_ids"]) != extracted:
                raise ContractValidationError(
                    f"{source['domain']} control_ids differ from independently "
                    "extracted source controls"
                )
            for control_id in source["control_ids"]:
                if control_id in inventory:
                    raise ContractValidationError(
                        f"baseline control {control_id} is listed by multiple artifacts"
                    )
                inventory[control_id] = (source["domain"], source["artifact"])
        registry = {item["id"]: item for item in baseline["control_registry"]}
        if len(registry) != len(baseline["control_registry"]):
            raise ContractValidationError("baseline control registry contains duplicate ids")
        if set(inventory) != set(registry):
            missing = sorted(set(inventory) - set(registry))
            extra = sorted(set(registry) - set(inventory))
            raise ContractValidationError(
                f"baseline control registry is not lossless; missing={missing}, extra={extra}"
            )
        for control_id, (domain, artifact) in inventory.items():
            item = registry[control_id]
            if item["domain"] != domain or item["artifact"] != artifact:
                raise ContractValidationError(
                    f"baseline control {control_id} has wrong domain or artifact binding"
                )
        expected_open = {
            item["id"]
            for item in baseline["control_registry"]
            if item["hardness"] == "author_open"
        }
        if set(baseline["open_items"]) != expected_open:
            raise ContractValidationError(
                "baseline open_items are not the exact author_open control set"
            )

    @staticmethod
    def assert_design_decisions_semantics(model: dict[str, Any]) -> None:
        seen: set[str] = set()
        for decision in model["design_decisions"]:
            if decision["id"] in seen:
                raise ContractValidationError(
                    f"duplicate design decision {decision['id']}"
                )
            seen.add(decision["id"])
            if decision["selection"] not in decision["options"]:
                raise ContractValidationError(
                    f"design decision {decision['id']} selects an unlisted option"
                )
            if (
                len(decision["options"]) == 1
                and not decision.get("single_option_exclusion_evidence")
            ):
                raise ContractValidationError(
                    f"single-option decision {decision['id']} lacks exclusion evidence"
                )

    @staticmethod
    def assert_cross_model_semantics(
        s1: dict[str, Any],
        w1: dict[str, Any],
        e1: dict[str, Any],
        t1: dict[str, Any],
        c1: dict[str, Any],
    ) -> None:
        def ids(items: list[dict[str, Any]], key: str = "id") -> set[str]:
            values = [item[key] for item in items]
            if len(values) != len(set(values)):
                raise ContractValidationError(f"duplicate ids in {key} collection")
            return set(values)

        handoffs = (
            ("S1→W1", ids(s1["world_requirements"]), ids(w1["storyline_requirements"])),
            ("W1→E1", ids(w1["environment_demands"]), ids(e1["environment_demands"])),
            ("S1→T1", ids(s1["event_requirements"]), ids(t1["event_demands"])),
            ("S1→C1", ids(s1["character_requirements"]), ids(c1["character_demands"])),
        )
        for label, produced, consumed in handoffs:
            if produced != consumed:
                raise ContractValidationError(
                    f"{label} requirement ids differ: produced={sorted(produced)}, "
                    f"consumed={sorted(consumed)}"
                )
        s1_environment = ids(s1["environment_requirements"])
        w1_environment = ids(w1["environment_demands"])
        if not s1_environment <= w1_environment:
            raise ContractValidationError(
                "S1→W1 environment requirements were lost before E1: "
                f"{sorted(s1_environment - w1_environment)}"
            )

        storyline_ids = ids(s1["storylines"])
        environment_ids = ids(e1["environments"])
        event_ids = ids(t1["major_events"])
        character_ids = ids(c1["profiles"])
        for event in t1["major_events"]:
            if not set(event["storyline_ids"]) <= storyline_ids:
                raise ContractValidationError(
                    f"event {event['id']} references unknown storyline"
                )
            if event["environment_id"] not in environment_ids:
                raise ContractValidationError(
                    f"event {event['id']} references unknown environment"
                )
        resolved_slots = {item["slot_id"] for item in c1["slot_resolution"]}
        event_slots = {
            slot
            for event in t1["major_events"]
            for slot in event["participant_slot_ids"]
        }
        if not event_slots <= resolved_slots:
            raise ContractValidationError(
                f"unresolved event slots: {sorted(event_slots - resolved_slots)}"
            )
        for resolution in c1["slot_resolution"]:
            if resolution["character_id"] not in character_ids:
                raise ContractValidationError(
                    f"slot {resolution['slot_id']} resolves to unknown character"
                )
            if not set(resolution["event_ids"]) <= event_ids:
                raise ContractValidationError(
                    f"slot {resolution['slot_id']} references unknown event"
                )

    @staticmethod
    def assert_human_review_semantics(
        report: dict[str, Any],
        *,
        authoritative_source_ids: set[str],
    ) -> None:
        visible_sources: dict[str, set[str]] = {}
        for section_name, collection_names in {
            "world": ["systems", "environments", "event_conditions"],
            "storylines": ["lines", "connections", "major_events"],
            "characters": [
                "core_characters",
                "supporting_characters",
                "relationship_networks",
                "role_coverage",
            ],
        }.items():
            section = report[section_name]
            for collection_name in collection_names:
                for item in section[collection_name]:
                    if item["id"] in visible_sources:
                        raise ContractValidationError(
                            f"duplicate visible report element {item['id']}"
                        )
                    visible_sources[item["id"]] = set(item["source_ids"])
        for fragment in report["fragments"]:
            if fragment["id"] in visible_sources:
                raise ContractValidationError(
                    f"duplicate visible report element {fragment['id']}"
                )
            visible_sources[fragment["id"]] = set(fragment["source_ids"])

        coverage: dict[str, set[str]] = {}
        for item in report["source_coverage"]:
            if item["source_id"] in coverage:
                raise ContractValidationError(
                    f"duplicate source coverage {item['source_id']}"
                )
            coverage[item["source_id"]] = set(item["visible_element_ids"])
            for visible_id in item["visible_element_ids"]:
                if visible_id not in visible_sources:
                    raise ContractValidationError(
                        f"coverage points to unknown visible element {visible_id}"
                    )
                if item["source_id"] not in visible_sources[visible_id]:
                    raise ContractValidationError(
                        f"visible element {visible_id} does not cite "
                        f"covered source {item['source_id']}"
                    )
        if set(coverage) != authoritative_source_ids:
            raise ContractValidationError(
                "human review source coverage is not the exact authoritative set"
            )

    @staticmethod
    def assert_manifest_semantics(manifest: dict[str, Any]) -> None:
        file_keys = {
            (item["path"], item["sha256"])
            for item in manifest["files"]
        }
        for role, reference in manifest["artifact_roles"].items():
            if (reference["path"], reference["sha256"]) not in file_keys:
                raise ContractValidationError(
                    f"artifact role {role} is not bound in manifest files"
                )
        validation = manifest["validation"]
        if (validation["path"], validation["sha256"]) not in file_keys:
            raise ContractValidationError("validation is not bound in manifest files")

    @staticmethod
    def assert_completion_matches_gate(
        completion: dict[str, Any], gate: dict[str, Any]
    ) -> None:
        if completion["run_id"] != gate["run_id"]:
            raise ContractValidationError("completion/gate run mismatch")
        if completion["stage"] != gate["target_stage"]:
            raise ContractValidationError("completion/gate stage mismatch")
        if completion["previous_stage_completions"] != gate["upstream_completions"]:
            raise ContractValidationError("completion/gate predecessor mismatch")
        if completion["return_binding"] != gate["return_binding"]:
            raise ContractValidationError("completion/gate return binding mismatch")

    @staticmethod
    def assert_return_routing(request: dict[str, Any]) -> None:
        target = request["target_stage"]
        owner = request["calculated_owner"]
        if target in {"I0", "I1", "I2", "I3", "I4", "I5"}:
            expected_owner = target
        elif target == "H1":
            expected_owner = {
                "H1-A-plan": "H1-A",
                "H1-B": "H1-B",
                "H1-A-assemble": "H1-A",
                "H1-C": "H1-C",
            }[request["resume_point"]]
        else:
            expected_owner = target
        if owner != expected_owner:
            raise ContractValidationError(
                f"owner {owner} does not own target {target}/{request['resume_point']}"
            )
        if request["origin_kind"] == "author":
            expected_kind = "author_revision"
        elif target in {"I0", "I1", "I2", "I3", "I4", "I5"}:
            expected_kind = "upstream_reentry"
        else:
            expected_kind = "local_revision"
        if request["return_kind"] != expected_kind:
            raise ContractValidationError(
                f"return kind {request['return_kind']} should be {expected_kind}"
            )
        h1_suffixes = {
            "H1-A-plan": ["plan", "fragments", "assembly", "html", "completion"],
            "H1-B": ["fragments", "assembly", "html", "completion"],
            "H1-A-assemble": ["assembly", "html", "completion"],
            "H1-C": ["html", "completion"],
        }
        expected_h1 = (
            h1_suffixes[request["resume_point"]]
            if target == "H1"
            else h1_suffixes["H1-A-plan"]
        )
        if request["invalidated_h1_artifacts"] != expected_h1:
            raise ContractValidationError(
                "return request has an incorrect H1 invalidation suffix"
            )

    @staticmethod
    def assert_h1_session_consistency(
        workspace: dict[str, Any], manifests: list[dict[str, Any]]
    ) -> None:
        session = workspace["session_id"]
        if any(manifest.get("session_id") != session for manifest in manifests):
            raise ContractValidationError("mixed H1 sessions")

    @staticmethod
    def assert_q1_task_isolation(review: dict[str, Any]) -> None:
        isolation = review["task_isolation"]
        if isolation["semantic_task_id"] == isolation["handoff_task_id"]:
            raise ContractValidationError("Q1 tasks are not isolated")
        required_forbidden = {
            "chat",
            "interview_reports",
            "generation_evidence",
            "semantic_findings",
            "expected_answers",
        }
        if not required_forbidden <= set(isolation["forbidden_reads"]):
            raise ContractValidationError("Q1 handoff forbidden-read set is incomplete")

    def _resolve_ref(
        self, ref: str, current_path: Path
    ) -> tuple[Path, dict[str, Any]]:
        file_part, _, fragment = ref.partition("#")
        target_path = current_path if not file_part else (current_path.parent / file_part)
        target_path, value = self.load(target_path)
        if fragment:
            if not fragment.startswith("/"):
                raise ContractValidationError(f"unsupported pointer {ref}")
            for raw in fragment[1:].split("/"):
                token = raw.replace("~1", "/").replace("~0", "~")
                value = value[token]
        return target_path, value

    @staticmethod
    def _matches_type(value: Any, expected: str) -> bool:
        if expected == "null":
            return value is None
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        raise ContractValidationError(f"unsupported type {expected}")

    def _valid(
        self, instance: Any, schema: Any, current_path: Path, at: str
    ) -> bool:
        return not self._validate(instance, schema, current_path, at)

    def _validate(
        self, instance: Any, schema: Any, current_path: Path, at: str
    ) -> list[str]:
        if schema is True:
            return []
        if schema is False:
            return [f"{at}: false schema"]
        if not isinstance(schema, dict):
            return [f"{at}: schema is not an object or boolean"]

        errors: list[str] = []
        if "$ref" in schema:
            ref_path, target = self._resolve_ref(schema["$ref"], current_path)
            errors.extend(self._validate(instance, target, ref_path, at))

        if "allOf" in schema:
            for index, branch in enumerate(schema["allOf"]):
                errors.extend(
                    self._validate(instance, branch, current_path, f"{at}.allOf[{index}]")
                )
        if "anyOf" in schema:
            if not any(
                self._valid(instance, branch, current_path, at)
                for branch in schema["anyOf"]
            ):
                errors.append(f"{at}: no anyOf branch matched")
        if "oneOf" in schema:
            matches = sum(
                self._valid(instance, branch, current_path, at)
                for branch in schema["oneOf"]
            )
            if matches != 1:
                errors.append(f"{at}: expected exactly one oneOf match, got {matches}")
        if "not" in schema and self._valid(instance, schema["not"], current_path, at):
            errors.append(f"{at}: not schema matched")
        if "if" in schema:
            branch = "then" if self._valid(instance, schema["if"], current_path, at) else "else"
            if branch in schema:
                errors.extend(self._validate(instance, schema[branch], current_path, at))

        expected_type = schema.get("type")
        if expected_type is not None:
            expected = [expected_type] if isinstance(expected_type, str) else expected_type
            if not any(self._matches_type(instance, item) for item in expected):
                errors.append(f"{at}: expected type {expected}, got {type(instance).__name__}")
                return errors

        if "const" in schema and instance != schema["const"]:
            errors.append(f"{at}: expected const {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{at}: value is not in enum")

        if isinstance(instance, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    errors.append(f"{at}: missing required property {key}")
            properties = schema.get("properties", {})
            for key, subschema in properties.items():
                if key in instance:
                    errors.extend(
                        self._validate(
                            instance[key], subschema, current_path, f"{at}.{key}"
                        )
                    )
            extras = set(instance) - set(properties)
            additional = schema.get("additionalProperties", True)
            if additional is False and extras:
                errors.append(f"{at}: additional properties {sorted(extras)}")
            elif isinstance(additional, dict):
                for key in extras:
                    errors.extend(
                        self._validate(
                            instance[key], additional, current_path, f"{at}.{key}"
                        )
                    )
            if len(instance) < schema.get("minProperties", 0):
                errors.append(f"{at}: too few properties")
            if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
                errors.append(f"{at}: too many properties")

        if isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                errors.append(f"{at}: too few items")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                errors.append(f"{at}: too many items")
            if schema.get("uniqueItems"):
                keys = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in instance]
                if len(keys) != len(set(keys)):
                    errors.append(f"{at}: duplicate items")
            prefix = schema.get("prefixItems", [])
            for index, subschema in enumerate(prefix):
                if index < len(instance):
                    errors.extend(
                        self._validate(
                            instance[index],
                            subschema,
                            current_path,
                            f"{at}[{index}]",
                        )
                    )
            if "items" in schema:
                start = len(prefix)
                for index in range(start, len(instance)):
                    errors.extend(
                        self._validate(
                            instance[index],
                            schema["items"],
                            current_path,
                            f"{at}[{index}]",
                        )
                    )
            if "contains" in schema:
                matches = sum(
                    self._valid(item, schema["contains"], current_path, at)
                    for item in instance
                )
                minimum = schema.get("minContains", 1)
                maximum = schema.get("maxContains")
                if matches < minimum or (maximum is not None and matches > maximum):
                    errors.append(f"{at}: contains matched {matches}")

        if isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0):
                errors.append(f"{at}: string too short")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                errors.append(f"{at}: string too long")
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                errors.append(f"{at}: pattern mismatch")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{at}: below minimum")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{at}: above maximum")

        return errors
