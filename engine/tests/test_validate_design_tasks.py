import unittest
import sys
import copy
import importlib.util
import json
import jsonschema
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import validate_design_tasks as validator


def load_quality_validator():
    module_path = Path(__file__).resolve().parents[1] / "tasks/design/validate_design_doc_quality.py"
    spec = importlib.util.spec_from_file_location("design_doc_quality_validator", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateDesignTasksTest(unittest.TestCase):
    def test_design_task_package_exists_and_is_blocked_by_prd_human_review(self):
        package = validator.load_design_task_package()

        self.assertEqual(package["workflow_node"], "hld-design-planning")
        self.assertEqual(package["prd_hld_entry_verdict"], "blocked_pending_human_review")
        self.assertEqual(package["execution_policy"], "planning_only_until_prd_human_confirmation")

    def test_design_tasks_cover_every_prd_hld_handoff_theme(self):
        package = validator.load_design_task_package()
        prd_themes = validator.extract_prd_hld_handoff_themes()

        missing = validator.find_missing_handoff_theme_coverage(package, prd_themes)

        self.assertEqual(missing, [])

    def test_design_tasks_bind_each_theme_to_artifact_owner_and_acceptance(self):
        package = validator.load_design_task_package()

        invalid_rows = validator.find_invalid_coverage_rows(package)

        self.assertEqual(invalid_rows, [])

    def test_prd_hld_handoff_rows_are_bound_to_prd_scenes_and_boundary(self):
        package = validator.load_design_task_package()
        prd_rows = validator.extract_prd_hld_handoff_rows()
        weakened = copy.deepcopy(package)
        for row in weakened["coverage"]:
            if row["PRD handoff theme"] == "情报交接与事故现场":
                row["Supports"] = "PRD-S18"
                row["Execution boundary"] = "不得改写 PRD。"

        violations = validator.find_prd_handoff_fact_mismatches(weakened, prd_rows)

        self.assertIn("情报交接与事故现场: support scenes do not match PRD HLD handoff", violations)
        self.assertIn("情报交接与事故现场: execution boundary omits PRD handoff boundary facts", violations)

    def test_extra_prd_hld_design_tasks_are_rejected(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        extra = dict(weakened["coverage"][0])
        extra["Task id"] = "HLD-DESIGN-99"
        extra["PRD handoff theme"] = "不存在的额外任务"
        weakened["coverage"].append(extra)

        violations = validator.find_invalid_coverage_rows(weakened)

        self.assertIn("HLD-DESIGN-99: design task is not backed by PRD HLD handoff", violations)

    def test_blocked_package_rejects_business_hld_artifact_execution(self):
        package = validator.load_design_task_package()

        self.assertEqual(validator.find_illegal_business_execution(package), [])

    def test_design_tasks_cover_every_prd_hld_requirement_id(self):
        package = validator.load_design_task_package()
        hld_requirements = validator.extract_prd_hld_requirements()

        missing = validator.find_missing_hld_requirement_coverage(package, hld_requirements)

        self.assertEqual(missing, [])

    def test_design_tasks_cover_every_prd_freeze_boundary_id(self):
        package = validator.load_design_task_package()
        freeze_boundaries = validator.extract_prd_freeze_boundaries()

        missing = validator.find_missing_freeze_boundary_coverage(package, freeze_boundaries)

        self.assertEqual(missing, [])

    def test_design_tasks_cover_every_story_logic_boundary(self):
        package = validator.load_design_task_package()
        story_logic_boundaries = validator.extract_prd_story_logic_boundaries()

        missing = validator.find_missing_story_logic_coverage(package, story_logic_boundaries)

        self.assertEqual(missing, [])

    def test_design_task_owner_artifacts_match_hld_topology(self):
        package = validator.load_design_task_package()

        violations = validator.find_owner_topology_violations(package)

        self.assertEqual(violations, [])

    def test_engineering_tasks_are_allowed_while_business_hld_is_blocked(self):
        package = validator.load_design_task_package()

        violations = validator.find_invalid_engineering_status(package)

        self.assertEqual(violations, [])

    def test_design_tasks_cover_every_hld_artifact_owner(self):
        package = validator.load_design_task_package()

        missing = validator.find_missing_hld_artifact_task_coverage(package)

        self.assertEqual(missing, [])

    def test_hld_requirement_rows_preserve_prd_supports_and_boundaries(self):
        package = validator.load_design_task_package()
        hld_requirements = validator.extract_prd_hld_requirement_rows()

        violations = validator.find_hld_requirement_fact_mismatches(package, hld_requirements)

        self.assertEqual(violations, [])

    def test_freeze_rows_preserve_prd_no_change_boundaries(self):
        package = validator.load_design_task_package()
        freeze_boundaries = validator.extract_prd_freeze_boundary_rows()

        violations = validator.find_freeze_boundary_fact_mismatches(package, freeze_boundaries)

        self.assertEqual(violations, [])

    def test_engineering_outputs_do_not_generate_business_hld_artifacts(self):
        package = validator.load_design_task_package()

        violations = validator.find_engineering_business_output_violations(package)

        self.assertEqual(violations, [])

    def test_engineering_outputs_reject_spelled_out_business_artifacts(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        weakened["engineering"][0]["Output"] = "artifact 01, artifact 02"

        violations = validator.find_engineering_business_output_violations(weakened)

        self.assertIn("HLD-ENG-01: engineering output points to business HLD artifacts", violations)

    def test_hld_requirement_required_answer_atoms_are_mandatory(self):
        package = validator.load_design_task_package()
        hld_requirements = validator.extract_prd_hld_requirement_rows()
        weakened = copy.deepcopy(package)
        for row in weakened["hld_requirement_coverage"]:
            if row["Requirement id"] == "HLD-REQ-14":
                row["Acceptance"] = "回答组织施压。"

        violations = validator.find_hld_requirement_fact_mismatches(weakened, hld_requirements)

        self.assertIn("HLD-REQ-14: acceptance omits PRD required-answer facts", violations)

    def test_hld_artifact_rows_have_task_level_closure(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["hld_artifact_coverage"]:
            if row["Artifact id"] == "artifact 11":
                row["Acceptance"] = "TBD"

        violations = validator.find_hld_artifact_task_closure_violations(weakened)

        self.assertIn("artifact 11: missing task-level closure fields", violations)

    def test_hld_artifact_source_obligations_match_required_topology(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["hld_artifact_coverage"]:
            if row["Artifact id"] == "artifact 08":
                row["Source obligations"] = "HLD-DESIGN-11, story logic boundary"

        violations = validator.find_hld_artifact_task_closure_violations(weakened)

        self.assertIn("artifact 08: source obligations must include topology dependencies ['artifact 01', 'artifact 02', 'artifact 04', 'artifact 06', 'artifact 07']", violations)

    def test_hld_artifact_source_obligations_preserve_required_upstream_sources(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["hld_artifact_coverage"]:
            if row["Artifact id"] == "artifact 01":
                row["Source obligations"] = "PRD-S00"

        violations = validator.find_hld_artifact_task_closure_violations(weakened)

        self.assertIn("artifact 01: source obligations must include required upstream sources ['4 条 story logic boundary', 'HLD-REQ-01 至 HLD-REQ-14', 'PRD-FREEZE-01 至 PRD-FREEZE-14', 'PRD-S00 至 PRD-S18', 'proposal claims']", violations)

    def test_freeze_no_change_rule_atoms_are_mandatory(self):
        package = validator.load_design_task_package()
        freeze_boundaries = validator.extract_prd_freeze_boundary_rows()
        weakened = copy.deepcopy(package)
        for row in weakened["freeze_story_logic_coverage"]:
            if row["Source id"] == "PRD-FREEZE-01":
                row["Preservation requirement"] = "保留关键情报交接失败、事故死亡、最后线索转入死者记忆；不得改成情报已经正常交接。"

        violations = validator.find_freeze_boundary_fact_mismatches(weakened, freeze_boundaries)

        self.assertIn("PRD-FREEZE-01: preservation omits PRD no-change facts", violations)

    def test_story_logic_boundary_atoms_are_mandatory(self):
        package = validator.load_design_task_package()
        story_logic_boundaries = validator.extract_prd_story_logic_boundary_rows()
        weakened = copy.deepcopy(package)
        for row in weakened["freeze_story_logic_coverage"]:
            if row["Source type"] == "story_logic_boundary" and row["Source id"] == "数字生命体终止骗局能力边界":
                row["Preservation requirement"] = "保留该边界。"

        violations = validator.find_story_logic_fact_mismatches(weakened, story_logic_boundaries)

        self.assertIn("数字生命体终止骗局能力边界: preservation omits PRD story-logic facts", violations)

    def test_design_tasks_cover_every_hld_contract_rule(self):
        package = validator.load_design_task_package()

        missing = validator.find_missing_contract_rule_coverage(package)

        self.assertEqual(missing, [])

    def test_design_tasks_cover_every_hld_artifact_schema(self):
        package = validator.load_design_task_package()

        violations = validator.find_artifact_schema_coverage_violations(package)

        self.assertEqual(violations, [])

    def test_artifact_schema_owner_and_task_bindings_are_semantic(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["artifact_schema_coverage"]:
            if row["Artifact id"] == "artifact 04":
                row["Owner skill"] = "`novel-event-system-designer`"
                row["Engineering task id"] = "HLD-SKILL-06"
                row["Validation target"] = "`validate_hld_contract.py::validate_artifact_06_schema`"

        violations = validator.find_artifact_schema_coverage_violations(weakened)

        self.assertIn("artifact 04: owner skill must be novel-character-system-designer", violations)
        self.assertIn("artifact 04: engineering task id must be HLD-SKILL-04", violations)
        self.assertIn("artifact 04: validation target must be validate_hld_contract.py::validate_artifact_04_schema", violations)

    def test_design_tasks_cover_final_hld_schema(self):
        package = validator.load_design_task_package()

        violations = validator.find_final_schema_coverage_violations(package)

        self.assertEqual(violations, [])

    def test_final_schema_source_and_task_bindings_are_semantic(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["final_schema_coverage"]:
            if row["Section"] == "Thread system":
                row["Source artifact"] = "artifact 03"
                row["Engineering task id"] = "HLD-SKILL-03"
                row["Validation target"] = "`validate_hld_contract.py::validate_final_schema_worldview_and_rules`"

        violations = validator.find_final_schema_coverage_violations(weakened)

        self.assertIn("Thread system: source artifact must be artifact 08", violations)
        self.assertIn("Thread system: engineering task id must be HLD-SKILL-08", violations)
        self.assertIn("Thread system: validation target must be validate_hld_contract.py::validate_final_schema_thread_system", violations)

    def test_contract_rule_bindings_are_semantic_not_presence_only(self):
        package = validator.load_design_task_package()
        weakened = copy.deepcopy(package)
        for row in weakened["contract_rule_coverage"]:
            if row["Rule id"] == "HLD-CONTRACT-10":
                row["Design task ids"] = "HLD-GLOBAL-02"
                row["Engineering task ids"] = "HLD-ENG-02"
                row["Planned validator coverage"] = "`validate_hld_contract.py::validate_harness_purity`"
                row["Planned regression proof"] = "`test_validate_hld_contract.py::test_harness_contains_no_business_design`"

        violations = validator.find_contract_rule_coverage_violations(weakened)

        self.assertIn("HLD-CONTRACT-10: design task ids must be HLD-GLOBAL-01", violations)
        self.assertIn("HLD-CONTRACT-10: engineering task ids must be HLD-SKILL-01", violations)
        self.assertIn("HLD-CONTRACT-10: validator coverage must be validate_hld_contract.py::validate_world_entity_inventory_coverage", violations)
        self.assertIn("HLD-CONTRACT-10: regression proof must be test_validate_hld_contract.py::test_initial_inventory_covers_required_entity_types", violations)

    def test_hld_engineering_tasks_are_independently_split_by_skill(self):
        package = validator.load_design_task_package()

        violations = validator.find_hld_skill_engineering_task_violations(package)

        self.assertEqual(violations, [])

    def test_hld_refactor_plan_file_modifications_are_tasked(self):
        package = validator.load_design_task_package()

        violations = validator.find_missing_hld_refactor_file_tasks(package)

        self.assertEqual(violations, [])

    def test_design_planning_contract_outputs_exist(self):
        violations = validator.find_design_planning_contract_violations()

        self.assertEqual(violations, [])

    def test_design_planning_json_matches_design_planning_skill_schema(self):
        schema_path = (
            Path("/Users/royzuo/.codex/skills/design-planning")
            / "schemas/design-planning.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        plan = validator.load_design_planning_json()

        errors = sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(plan),
            key=lambda error: list(error.path),
        )

        self.assertEqual([error.message for error in errors], [])

    def test_fixture_contract_rejects_thin_prompt_agents_and_claude_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "TASK-999"
            fixture_dir.mkdir()
            (fixture_dir / "PROMPT.md").write_text(
                "# Thin Prompt\n\nDo not implement code.\n",
                encoding="utf-8",
            )
            (fixture_dir / "AGENTS.md").write_text(
                "# Thin Agents\n\nDo not implement code.\n",
                encoding="utf-8",
            )
            (fixture_dir / "CLAUDE.md").write_text(
                "# Thin Claude\n\nDo not implement code.\n",
                encoding="utf-8",
            )
            task = {
                "task_id": "TASK-999",
                "title": "Thin fixture",
                "task_type": "detailed_design",
                "source_refs": ["docs/example-prd.md"],
                "outputs": ["docs/design/TASK-999-design.md"],
                "allowed_scope": ["document the design"],
                "forbidden_scope": ["implementation code"],
                "acceptance": ["complete design"],
                "verification": ["quality validator"],
                "stop_conditions": ["missing source refs"],
                "design_doc_path": "docs/design/TASK-999-design.md",
                "fixture_dir": fixture_dir.as_posix(),
            }

            violations = validator.find_fixture_contract_violations(task, fixture_dir)

        self.assertIn("TASK-999: PROMPT.md missing section ## Mission", violations)
        self.assertIn("TASK-999: AGENTS.md missing section ## Source Order", violations)
        self.assertIn("TASK-999: CLAUDE.md missing section ## Required Reading", violations)

    def test_acceptance_fixture_rejects_missing_explicit_dependency_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture_dir = tmp_path / "TASK-003"
            fixture_dir.mkdir()
            generic_text = "\n".join(
                [
                    "# Generic Acceptance Fixture",
                    "## Mission",
                    "Complete acceptance.",
                    "## Read First",
                    "- `tasks/design/design-planning.json`",
                    "## Scope",
                    "Review all detailed design documents.",
                    "## Expected Outputs",
                    "- `docs/design/acceptance.md`",
                    "## Document Review Checks",
                    "Review all documents and fixtures.",
                    "## Stop Conditions",
                    "Stop on missing fixture.",
                    "## Handoff Expectations",
                    "Report review results.",
                    "Do not implement code. Do not modify production source files. Save under docs/design/. HLD business is forbidden.",
                    "TASK-003 Final acceptance docs/design/acceptance.md",
                ]
            )
            for file_name in ["PROMPT.md", "AGENTS.md", "CLAUDE.md"]:
                (fixture_dir / file_name).write_text(generic_text, encoding="utf-8")
            plan = {
                "tasks": [
                    {
                        "task_id": "TASK-001",
                        "domain_task_id": "DP-HLD-001",
                        "task_type": "detailed_design",
                        "design_doc_path": "docs/design/DP-HLD-001-contract-validator-design.md",
                        "fixture_dir": "tasks/design/fixtures/TASK-001",
                    },
                    {
                        "task_id": "TASK-002",
                        "domain_task_id": "DP-HLD-002",
                        "task_type": "detailed_design",
                        "design_doc_path": "docs/design/DP-HLD-002-harness-skills-design.md",
                        "fixture_dir": "tasks/design/fixtures/TASK-002",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Final design acceptance review",
                        "task_type": "design_acceptance",
                        "dependencies": ["TASK-001", "TASK-002"],
                        "design_doc_path": "docs/design/acceptance.md",
                        "fixture_dir": fixture_dir.as_posix(),
                    },
                ]
            }

            violations = validator.find_acceptance_dependency_contract_violations(plan)

        self.assertIn(
            "TASK-003: PROMPT.md missing acceptance dependency TASK-001 -> DP-HLD-001",
            violations,
        )
        self.assertIn(
            "TASK-003: AGENTS.md missing acceptance dependency design document docs/design/DP-HLD-002-harness-skills-design.md",
            violations,
        )
        self.assertIn(
            "TASK-003: CLAUDE.md missing acceptance dependency fixture tasks/design/fixtures/TASK-001",
            violations,
        )

    def test_design_planning_json_contains_fine_grained_prd_hld_coverage(self):
        package = validator.load_design_task_package()
        plan = validator.load_design_planning_json()

        violations = validator.find_design_planning_coverage_violations(plan, package)

        self.assertEqual(violations, [])

    def test_design_planning_json_rejects_missing_fine_grained_coverage(self):
        package = validator.load_design_task_package()
        plan = validator.load_design_planning_json()
        weakened = copy.deepcopy(plan)
        weakened["coverage_matrix"] = [
            row for row in weakened["coverage_matrix"] if row.get("source_id") != "PRD-S00"
        ]

        violations = validator.find_design_planning_coverage_violations(weakened, package)

        self.assertIn("design-planning.json coverage_matrix missing prd_scene coverage: PRD-S00", violations)

    def test_design_doc_quality_rejects_thin_document_that_only_has_headings(self):
        quality_validator = load_quality_validator()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            document = tmp_path / "thin-design.md"
            planning = tmp_path / "design-planning.json"
            document.write_text(
                "\n".join(
                    [
                        "# Thin Design",
                        "## Source Refs",
                        "- `tasks/design/design-planning.json`",
                        "## Scope Boundary",
                        "Documentation-only.",
                        "## Control Flow",
                        "A" * 250,
                        "## Data Flow",
                        "B" * 250,
                        "## Verification",
                        "C" * 250,
                        "## Risks",
                        "D" * 250,
                        "## Handoff",
                        "E" * 250,
                    ]
                ),
                encoding="utf-8",
            )
            planning.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "task_id": "DP-HLD-TEST",
                                "task_type": "detailed_design",
                                "source_refs": ["tasks/design/design-planning.json"],
                                "outputs": [document.as_posix()],
                                "forbidden_scope": ["Do not implement code", "HLD business artifact generation"],
                                "acceptance": ["fact-level binding checks are specified"],
                                "design_doc_path": document.as_posix(),
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            errors = quality_validator.validate(document, planning, acceptance=False)

        self.assertIn(f"{document}: missing required sections ['Interface Contracts', 'State And Persistence', 'Error Handling And Diagnostics', 'Security And Permissions', 'Observability']", errors)
        self.assertIn(f"{document}: does not address planned acceptance item fact-level binding checks are specified", errors)

    def test_design_doc_quality_rejects_generic_doc_without_task_specific_detail(self):
        quality_validator = load_quality_validator()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            document = tmp_path / "DP-HLD-001-contract-validator-design.md"
            planning = tmp_path / "design-planning.json"
            document.write_text(
                "\n".join(
                    [
                        "# Generic Contract Design",
                        "## Source Refs",
                        "- `tasks/design/design-planning.json`",
                        "## Scope Boundary",
                        "Do not implement code. Do not create HLD business artifacts. PRD boundaries remain fixed.",
                        "## Control Flow",
                        "The validator reads inputs, checks them, and returns pass or fail. " * 12,
                        "## Data Flow",
                        "The validator receives files and emits diagnostics. " * 12,
                        "## Interface Contracts",
                        "The script exposes validation helpers. " * 12,
                        "## State And Persistence",
                        "State is file based and deterministic. " * 12,
                        "## Error Handling And Diagnostics",
                        "Errors are reported clearly. " * 12,
                        "## Security And Permissions",
                        "The task remains read only. " * 12,
                        "## Observability",
                        "Regression tests observe failures. " * 12,
                        "## Verification",
                        "Quality validator is used. fact-level binding checks are specified. negative fixtures are specified. planned validator functions map to contract rules.",
                        "## Risks",
                        "Generic documents may omit implementable detail.",
                        "## Handoff",
                        "Handoff includes the document path.",
                    ]
                ),
                encoding="utf-8",
            )
            planning.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "task_id": "TASK-001",
                                "title": "HLD contract and validator design",
                                "task_type": "detailed_design",
                                "source_refs": ["tasks/design/design-planning.json"],
                                "outputs": [document.as_posix()],
                                "forbidden_scope": ["implementation code", "HLD business artifact generation"],
                                "acceptance": [
                                    "fact-level binding checks are specified",
                                    "negative fixtures are specified",
                                    "planned validator functions map to contract rules",
                                ],
                                "design_doc_path": document.as_posix(),
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            errors = quality_validator.validate(document, planning, acceptance=False)

        self.assertIn(
            f"{document}: missing task-specific detail marker Validator Function Contract Matrix",
            errors,
        )

    def test_acceptance_doc_quality_requires_dependency_mapping(self):
        quality_validator = load_quality_validator()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            document = tmp_path / "acceptance.md"
            planning = tmp_path / "design-planning.json"
            document.write_text(
                "\n".join(
                    [
                        "# Acceptance",
                        "## Source Refs",
                        "- `tasks/design/design-planning.json`",
                        "## Scope Boundary",
                        "Do not implement code. Do not create HLD business artifacts. PRD boundaries remain fixed.",
                        "## Control Flow",
                        "Acceptance reviews all documents. " * 12,
                        "## Data Flow",
                        "Planning data flows into fixture checks. " * 12,
                        "## Interface Contracts",
                        "Acceptance checks fixture contracts. " * 12,
                        "## State And Persistence",
                        "State is repository files. " * 12,
                        "## Error Handling And Diagnostics",
                        "Missing artifacts fail acceptance. " * 12,
                        "## Security And Permissions",
                        "The task remains documentation-only. " * 12,
                        "## Observability",
                        "Validator outputs are evidence. " * 12,
                        "## Verification",
                        "every detailed task is reviewed. fixture readiness is checked. no-code boundary is preserved.",
                        "## Design Acceptance Checklist",
                        "Schema compliance and fixture contract checks are required.",
                        "## Residual Risk Disposition Matrix",
                        "PRD human review remains pending.",
                        "## Final Handoff Verdict",
                        "Handoff is documentation-only.",
                        "## Risks",
                        "Generic acceptance can omit dependency mapping.",
                        "## Handoff",
                        "Report acceptance result.",
                    ]
                ),
                encoding="utf-8",
            )
            planning.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "task_id": "TASK-005",
                                "title": "Final design acceptance review",
                                "task_type": "design_acceptance",
                                "source_refs": ["tasks/design/design-planning.json"],
                                "outputs": [document.as_posix()],
                                "forbidden_scope": ["implementation code", "HLD business artifact generation"],
                                "acceptance": [
                                    "every detailed task is reviewed",
                                    "fixture readiness is checked",
                                    "no-code boundary is preserved",
                                ],
                                "design_doc_path": document.as_posix(),
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            errors = quality_validator.validate(document, planning, acceptance=True)

        self.assertIn(
            f"{document}: missing task-specific detail marker Acceptance Dependency Mapping",
            errors,
        )

    def test_manifest_validation_state_matches_validator(self):
        manifest = validator.load_manifest()

        violations = validator.find_manifest_status_violations(manifest)

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
