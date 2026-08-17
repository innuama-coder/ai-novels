from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = (
    ROOT / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
)
WORKFLOW = (
    ROOT / "docs" / "ai-novel-workflow" / "conception-autonomous-workflow-v2.md"
)


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((CONTRACT_DIR / name).read_text(encoding="utf-8"))


def resolve_pointer(value: Any, fragment: str) -> Any:
    if not fragment:
        return value
    if not fragment.startswith("/"):
        raise AssertionError(f"unsupported JSON pointer: {fragment}")
    current = value
    for raw in fragment[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[token]
    return current


def iter_refs(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref":
                yield item
            yield from iter_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_refs(item)


def validate_author_decision_shape(value: dict[str, Any]) -> None:
    common = {
        "schema_version",
        "run_id",
        "approval_scope",
        "decision",
        "machine_package",
        "human_review_package",
    }
    decision = value["decision"]
    if decision == "approved":
        allowed = common | {"approval_record", "unresolved_items"}
        required = allowed
    elif decision == "revise":
        allowed = common | {"revision_record", "revision_targets"}
        required = allowed
        if not value["revision_targets"]:
            raise AssertionError("revise needs targets")
        for target in value["revision_targets"]:
            if target["target_scope"] == "conception" and not target["source_ids"]:
                raise AssertionError("conception revise needs source ids")
            if (
                target["target_scope"] in {"report", "fragment", "html"}
                and not target["visible_element_ids"]
            ):
                raise AssertionError("presentation revise needs visible element ids")
            if "owner" in target:
                raise AssertionError("author must not calculate owner")
    elif decision == "rejected":
        allowed = common | {"rejection_record"}
        required = allowed
    else:
        raise AssertionError("unknown decision")
    if set(value) != allowed or not required <= set(value):
        raise AssertionError("decision branch fields do not match")


def artifact(path: str = "package/file.json") -> dict[str, str]:
    return {"path": path, "sha256": "a" * 64}


def human_package() -> dict[str, str]:
    return {
        "completion_path": "h1/stage-completion.json",
        "completion_sha256": "b" * 64,
        "manifest_path": "h1/package-manifest.json",
        "manifest_sha256": "c" * 64,
        "html_path": "h1/human-review-report.html",
        "html_sha256": "d" * 64,
    }


def machine_package() -> dict[str, str]:
    return {
        "completion_path": "p1/stage-completion.json",
        "completion_sha256": "e" * 64,
        "manifest_path": "p1/package-manifest.json",
        "manifest_sha256": "f" * 64,
    }


class AutonomousV2ContractTests(unittest.TestCase):
    def test_all_schema_files_parse(self) -> None:
        schemas = sorted(CONTRACT_DIR.glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 10)
        for path in schemas:
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    value.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )

    def test_all_file_refs_resolve(self) -> None:
        for path in CONTRACT_DIR.glob("*.schema.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            for ref in iter_refs(schema):
                with self.subTest(path=path.name, ref=ref):
                    file_part, _, fragment = ref.partition("#")
                    target_path = path if not file_part else CONTRACT_DIR / file_part
                    self.assertTrue(target_path.is_file())
                    target = json.loads(target_path.read_text(encoding="utf-8"))
                    resolve_pointer(target, fragment)

    def test_relative_paths_reject_absolute_and_parent_escape(self) -> None:
        common = load_schema("common-defs.schema.json")
        pattern = common["$defs"]["relativePath"]["pattern"]
        self.assertRegex("p1/package-manifest.json", pattern)
        for bad in (
            "C:/repo/package.json",
            "/repo/package.json",
            "\\\\server\\share\\package.json",
            "../package.json",
            "p1/../package.json",
        ):
            with self.subTest(path=bad):
                self.assertIsNone(re.match(pattern, bad))

    def test_source_ids_admit_terminal_development_freedoms(self) -> None:
        common = load_schema("common-defs.schema.json")
        pattern = common["$defs"]["sourceId"]["pattern"]
        self.assertRegex("DEV-SCENE-001", pattern)

    def test_character_system_requires_explicit_development_freedoms(self) -> None:
        character = load_schema("character-system.schema.json")
        self.assertIn("development_freedoms", character["required"])
        self.assertEqual(
            character["properties"]["development_freedoms"]["$ref"],
            "canonical-common.schema.json#/$defs/developmentFreedoms",
        )
        common = load_schema("canonical-common.schema.json")
        freedom = common["$defs"]["developmentFreedom"]
        self.assertEqual(
            set(freedom["required"]),
            {
                "id",
                "subject_ids",
                "scope",
                "allowed_variations",
                "forbidden_changes",
                "acceptance_checks",
                "source_ids",
            },
        )
        self.assertEqual(
            freedom["properties"]["id"]["pattern"],
            "^DEV-[A-Za-z0-9._-]+$",
        )
        self.assertEqual(
            common["$defs"]["developmentFreedoms"]["minItems"],
            1,
        )

    def test_environment_system_requires_storyline_requirement_projection(
        self,
    ) -> None:
        environment = load_schema("environment-system.schema.json")
        self.assertIn(
            "storyline_environment_requirements",
            environment["required"],
        )
        self.assertEqual(
            environment["properties"]["storyline_environment_requirements"][
                "$ref"
            ],
            "canonical-common.schema.json#/$defs/environmentRequirements",
        )

    def test_baseline_requires_six_distinct_domains(self) -> None:
        schema = load_schema("author-control-baseline.schema.json")
        domains = {
            branch["properties"]["design_artifacts"]["contains"]["properties"][
                "domain"
            ]["const"]
            for branch in schema["allOf"]
            if "design_artifacts" in branch["properties"]
        }
        self.assertEqual(domains, {"I0", "I1", "I2", "I3", "I4", "I5"})
        design = schema["properties"]["design_artifacts"]
        self.assertEqual(design["minItems"], 6)
        self.assertEqual(design["maxItems"], 6)

    def test_baseline_registry_requires_every_interview_domain(self) -> None:
        schema = load_schema("author-control-baseline.schema.json")
        domains = {
            branch["properties"]["control_registry"]["contains"]["properties"][
                "domain"
            ]["const"]
            for branch in schema["allOf"]
            if "control_registry" in branch["properties"]
        }
        self.assertEqual(domains, {"I0", "I1", "I2", "I3", "I4", "I5"})
        source_item = schema["properties"]["design_artifacts"]["items"]
        self.assertIn("control_ids", source_item["required"])

    def test_design_decision_single_option_requires_exclusion_evidence(self) -> None:
        schema = load_schema("canonical-common.schema.json")
        decision = schema["$defs"]["designDecision"]
        self.assertIn(
            "single_option_exclusion_evidence",
            decision["properties"],
        )
        self.assertEqual(
            decision["allOf"][0]["then"]["required"],
            ["single_option_exclusion_evidence"],
        )

    def test_handoff_requirements_are_semantic_objects(self) -> None:
        schema = load_schema("canonical-common.schema.json")
        required = set(schema["$defs"]["handoffRequirement"]["required"])
        self.assertEqual(
            required,
            {
                "id",
                "target_stage",
                "responsibility",
                "source_ids",
                "required_capability",
                "constraints",
                "acceptance_checks",
                "downstream_freedom",
            },
        )
        s1 = load_schema("storyline-architecture.schema.json")
        for field, definition in {
            "world_requirements": "worldRequirements",
            "environment_requirements": "environmentRequirements",
            "event_requirements": "eventRequirements",
            "character_requirements": "characterRequirements",
        }.items():
            self.assertTrue(
                s1["properties"][field]["$ref"].endswith(f"#/$defs/{definition}")
            )

    def test_ready_baseline_cannot_hide_structural_open_fact(self) -> None:
        schema = load_schema("author-control-baseline.schema.json")
        variants = schema["$defs"]["factDependency"]["oneOf"]
        open_variant = next(
            item
            for item in variants
            if item["properties"]["status"].get("const") == "open"
        )
        self.assertEqual(open_variant["properties"]["blocking"]["const"], False)
        self.assertEqual(
            open_variant["properties"]["allowed_handling"]["const"],
            "preserve_open",
        )
        adopted = next(
            item
            for item in variants
            if item["properties"]["status"].get("const") == "adopted"
        )
        self.assertIn("research_package", adopted["required"])
        self.assertIn("adoption_record", adopted["required"])
        self.assertIn("fact_dependency_register", schema["required"])

    def test_h1_state_has_exact_artifact_progression(self) -> None:
        schema = load_schema("h1-workspace-state.schema.json")
        expected = {
            "initialized": set(),
            "planned": {"plan_manifest"},
            "fragments_ready": {"plan_manifest", "fragment_manifest"},
            "assembled": {
                "plan_manifest",
                "fragment_manifest",
                "assembly_manifest",
            },
            "rendered": {
                "plan_manifest",
                "fragment_manifest",
                "assembly_manifest",
                "html_manifest",
            },
        }
        actual: dict[str, set[str]] = {}
        for branch in schema["allOf"]:
            if "properties" not in branch["if"]:
                continue
            state = branch["if"]["properties"]["state"]["const"]
            artifact_rule = branch["then"]["properties"]["artifacts"]
            actual[state] = set(artifact_rule.get("required", []))
            self.assertEqual(artifact_rule["maxProperties"], len(actual[state]))
        self.assertEqual(actual, expected)
        self.assertNotIn("ready", schema["properties"]["state"]["enum"])
        initialized = schema["allOf"][0]["then"]["properties"]
        self.assertEqual(initialized["previous_state_sha256"]["type"], "null")
        non_initial = schema["allOf"][1]["then"]["properties"]
        self.assertIn("$ref", non_initial["previous_state_sha256"])

    def test_h1_manifest_and_completion_require_session_binding(self) -> None:
        manifest = load_schema("package-manifest.schema.json")
        h1_manifest_rule = manifest["allOf"][0]["then"]["required"]
        self.assertEqual(
            set(h1_manifest_rule),
            {"session_id", "parent_state_sha256"},
        )
        completion = load_schema("stage-completion.schema.json")
        self.assertIn("session_id", completion["allOf"][0]["then"]["required"])

    def test_return_explicitly_invalidates_approval_chain(self) -> None:
        schema = load_schema("return-request.schema.json")
        required = set(schema["required"])
        self.assertIn("invalidate_author_decision", required)
        self.assertIn("invalidate_conception_completion", required)

    def test_author_decision_allows_three_closed_branches(self) -> None:
        base = {
            "schema_version": "2.0",
            "run_id": "run-1",
            "approval_scope": "conception",
            "machine_package": machine_package(),
            "human_review_package": human_package(),
        }
        approved = {
            **base,
            "decision": "approved",
            "approval_record": {"event_seq": 1, "text": "批准"},
            "unresolved_items": [],
        }
        validate_author_decision_shape(approved)
        conception_revise = {
            **base,
            "decision": "revise",
            "revision_record": {"event_seq": 2, "text": "修改世界规则"},
            "revision_targets": [
                {
                    "target_scope": "conception",
                    "visible_element_ids": ["world-rule-1"],
                    "source_ids": ["WF-001"],
                    "requested_change": "重新定义限制",
                }
            ],
        }
        validate_author_decision_shape(conception_revise)
        html_revise = {
            **base,
            "decision": "revise",
            "revision_record": {"event_seq": 3, "text": "图太密"},
            "revision_targets": [
                {
                    "target_scope": "html",
                    "visible_element_ids": ["world-map"],
                    "source_ids": [],
                    "requested_change": "提高可读性",
                }
            ],
        }
        validate_author_decision_shape(html_revise)
        rejected = {
            **base,
            "decision": "rejected",
            "rejection_record": {"event_seq": 4, "text": "放弃当前构思"},
        }
        validate_author_decision_shape(rejected)

    def test_bad_author_decision_branches_fail(self) -> None:
        base = {
            "schema_version": "2.0",
            "run_id": "run-1",
            "approval_scope": "conception",
            "machine_package": machine_package(),
            "human_review_package": human_package(),
            "decision": "revise",
            "revision_record": {"event_seq": 1, "text": "修改"},
        }
        missing_source = {
            **base,
            "revision_targets": [
                {
                    "target_scope": "conception",
                    "visible_element_ids": ["story-1"],
                    "source_ids": [],
                    "requested_change": "修改",
                }
            ],
        }
        with self.assertRaises(AssertionError):
            validate_author_decision_shape(missing_source)
        author_chose_owner = {
            **base,
            "revision_targets": [
                {
                    "target_scope": "html",
                    "visible_element_ids": ["map-1"],
                    "source_ids": [],
                    "requested_change": "修改",
                    "owner": "H1-C",
                }
            ],
        }
        with self.assertRaises(AssertionError):
            validate_author_decision_shape(author_chose_owner)

    def test_final_completion_requires_all_top_level_stages(self) -> None:
        schema = load_schema("conception-completion.schema.json")
        stages = schema["properties"]["stage_completions"]
        expected = {"B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"}
        self.assertEqual(set(stages["required"]), expected)
        self.assertEqual(set(stages["properties"]), expected)
        self.assertFalse(stages["additionalProperties"])
        for stage, rule in stages["properties"].items():
            self.assertEqual(rule["allOf"][1]["properties"]["stage"]["const"], stage)

    def test_workflow_document_closes_reviewed_gaps(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        required_phrases = (
            "author-control-baseline.json",
            "semantic-reviewer",
            "handoff-evaluator",
            "h1-workspace-state.json",
            "author-decision.schema.json",
            "stale_input",
            "authoritative-design-artifacts/",
            "reality_claims",
            "fact-dependency-register.json",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertNotIn("`rendered → ready`", text)

    def test_v2_skill_entry_chain_exists_and_uses_current_stage_names(self) -> None:
        expected = {
            "novel-storyline-architecture-designer": "S1",
            "novel-world-model-designer": "W1",
            "novel-environment-system-designer": "E1",
            "novel-event-timeline-designer": "T1",
            "novel-character-system-designer": "C1",
            "novel-conception-reviewer": "Q1",
            "novel-conception-deliverable-assembler": "P1",
            "novel-conception-human-review-assembler": "H1",
            "novel-conception-fragment-writer": "H1",
            "novel-conception-review-html-generator": "H1",
        }
        for skill, stage in expected.items():
            with self.subTest(skill=skill):
                path = ROOT / "skills" / skill / "SKILL.md"
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"name: {skill}", text)
                self.assertIn(stage, text)
                self.assertNotIn("对 D1 已完成", text)
                self.assertNotIn("在 R1 技术验收通过后", text)


if __name__ == "__main__":
    unittest.main()
