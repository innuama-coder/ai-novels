#!/usr/bin/env python3
"""Validate HLD design task planning coverage against the latest PRD."""

from __future__ import annotations

import re
import json
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
NOVEL = ROOT.parent / "duanxian"
DESIGN_PLANNING_SCHEMA = (
    Path("/Users/royzuo/.codex/skills/design-planning")
    / "schemas/design-planning.schema.json"
)
PRD_PACKAGE = (
    NOVEL
    / "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md"
)
PRD_HLD_REQUIREMENTS = (
    NOVEL
    / "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md"
)
PRD_FREEZE_BOUNDARIES = (
    NOVEL
    / "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md"
)
DESIGN_TASK_PACKAGE = (
    NOVEL
    / "design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md"
)
DESIGN_TASK_MANIFEST = (
    NOVEL
    / "design/design-tasks/2026-07-07-duanxian-hld-design-planning/manifest.md"
)
DESIGN_PLANNING_JSON = ROOT / "tasks/design/design-planning.json"
DESIGN_PLANNING_QUALITY_VALIDATOR = ROOT / "tasks/design/validate_design_doc_quality.py"
DESIGN_PLANNING_ROOT_DESIGN_DOC = ROOT / "docs/design/rust-implementation-design.md"
PRD_RISK_REPORT = (
    NOVEL
    / "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md"
)

REQUIRED_COVERAGE_COLUMNS = [
    "Task id",
    "PRD handoff theme",
    "Supports",
    "Owner artifact",
    "Skill owner",
    "Acceptance",
    "Execution boundary",
    "Status",
]
REQUIRED_HLD_ARTIFACT_IDS = set(ARTIFACT_SKILL_OWNERS := {
    "artifact 01": "novel-world-entity-inventory-builder",
    "artifact 02": "novel-prd-support-matrix-builder",
    "artifact 03": "novel-world-rule-designer",
    "artifact 04": "novel-character-system-designer",
    "artifact 05": "novel-environment-system-designer",
    "artifact 06": "novel-event-system-designer",
    "artifact 07": "novel-time-information-system-designer",
    "artifact 08": "novel-thread-system-designer",
    "artifact 09": "novel-style-pov-system-designer",
    "artifact 10": "novel-hld-inventory-reconciler",
    "artifact 11": "novel-hld-integrator",
    "artifact 12": "novel-hld-integrity-checker",
})

BLOCKED_VERDICT = "blocked_pending_human_review"
BLOCKED_POLICY = "planning_only_until_prd_human_confirmation"
BLOCKED_TASK_STATUSES = {
    "blocked_pending_prd_human_review",
    "planning_ready_blocked",
}
ENGINEERING_TASK_STATUSES = {
    "ready_before_prd_confirmation",
    "planning_ready_blocked",
}
BUSINESS_HLD_ARTIFACT_OUTPUT_PATTERNS = [
    "artifact 01",
    "artifact 02",
    "artifact 03",
    "artifact 04",
    "artifact 05",
    "artifact 06",
    "artifact 07",
    "artifact 08",
    "artifact 09",
    "artifact 10",
    "artifact 11",
    "artifact 12",
    "final-hld-package",
]
PLACEHOLDER_VALUES = {"", "tbd", "unknown", "n/a"}
REQUIRED_CONTRACT_RULE_IDS = {f"HLD-CONTRACT-{index:02d}" for index in range(1, 19)}
REQUIRED_ARTIFACT_SCHEMAS = {
    "artifact 01": (
        "## Initial world entity inventory",
        ["Inventory id", "Entity type", "Entity name", "Required HLD owner", "Upstream evidence", "Source", "Initial status"],
    ),
    "artifact 02": (
        "## PRD support matrix",
        ["Support id", "Supports", "Support type", "Required HLD owner", "Required answer", "Boundary", "Source", "Support status"],
    ),
    "artifact 03": (
        "## World rule design table",
        ["Rule id", "Rule type", "Design fact", "Supports", "Boundary", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 04": (
        "## Character system table",
        [
            "Character id",
            "Role type",
            "Function",
            "Relationship/motivation",
            "Information permission",
            "Supports",
            "Source",
            "LLD handoff",
            "Amendment request",
        ],
    ),
    "artifact 05": (
        "## Environment system table",
        ["Environment id", "Environment type", "Function", "Spatial relation", "State change", "Supports", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 06": (
        "## Event system table",
        ["Event id", "Event type", "Causal role", "Visibility", "Participants", "Consequences", "Supports", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 07": (
        "## Time and information table",
        ["Info id", "Time layer", "Information object", "Known by", "Hidden from", "Reveal condition", "Supports", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 08": (
        "## Thread system table",
        ["Thread id", "Thread type", "Thread function", "Thread anchor refs", "Required pressure refs", "Core question", "Node distribution", "Thread progression", "Crossover", "Closure state", "Closure outcome", "Supports", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 09": (
        "## Style and POV table",
        ["Style/POV id", "Rule type", "Access policy", "Information refs", "Thread refs", "Reader disclosure mode", "Language profile", "Design fact", "POV permission", "Prohibited expression", "Supports", "Source", "LLD handoff", "Amendment request"],
    ),
    "artifact 10": (
        "## Inventory amendment disposition",
        ["Request id", "Requested entity", "Requested by artifact", "Decision", "Final inventory id", "Reason", "Source", "Support status"],
    ),
    "artifact 11": (
        "## HLD Source Map",
        [
            "HLD fact id",
            "Fact type",
            "Upstream fact atom",
            "HLD fact atom",
            "Source refs",
            "Owner artifact",
            "Final inventory id",
            "Expansion mode",
            "Support mechanism",
            "LLD handoff target",
            "Preservation status",
        ],
    ),
    "artifact 12": (
        "## Output; ## Risks; ## Verdict consistency matrix; ## Environment closure checks; ## Event closure checks; ## Information closure checks; ## Thread closure checks; ## Style/POV closure checks; ## HLD Convergence Log",
        [
            "Field",
            "Value",
            "Risk",
            "Severity",
            "Handling",
            "Blocking verdict effect",
            "Verdict",
            "Required condition",
            "Actual evidence",
            "Consistency",
            "Style/POV id",
            "Rule type",
            "Access policy",
            "Information refs",
            "Thread refs",
            "Reader disclosure mode",
            "Language profile",
            "Design fact",
            "POV permission",
            "Prohibited expression",
            "LLD handoff",
            "Evidence",
            "Stable issue id",
            "Root cause",
            "Fix hypothesis",
            "Regression proof",
            "Attempt count",
            "Rerun target",
            "Status",
        ],
    ),
}
REQUIRED_FINAL_HLD_SCHEMA_SECTIONS = [
    "Revision table",
    "Input gate proof",
    "HLD scope and exclusions",
    "World entity inventory",
    "PRD support matrix",
    "Worldview and world rules",
    "World structure",
    "Character system",
    "Environment system",
    "Event system",
    "Time and information system",
    "Thread system",
    "Style and POV system",
    "HLD Source Map",
    "LLD handoff index",
    "HLD risk report and LLD entry verdict",
]
REQUIRED_HLD_ARTIFACT_DEPENDENCIES = {
    "artifact 01": set(),
    "artifact 02": {"artifact 01"},
    "artifact 03": {"artifact 01", "artifact 02"},
    "artifact 04": {"artifact 01", "artifact 02", "artifact 03"},
    "artifact 05": {"artifact 01", "artifact 02", "artifact 03"},
    "artifact 06": {"artifact 01", "artifact 02", "artifact 03", "artifact 04", "artifact 05"},
    "artifact 07": {"artifact 01", "artifact 02", "artifact 03", "artifact 04", "artifact 06"},
    "artifact 08": {"artifact 01", "artifact 02", "artifact 04", "artifact 06", "artifact 07"},
    "artifact 09": {"artifact 01", "artifact 02", "artifact 04", "artifact 05", "artifact 07", "artifact 08"},
    "artifact 10": {f"artifact {index:02d}" for index in range(1, 10)},
    "artifact 11": {f"artifact {index:02d}" for index in range(1, 11)},
    "artifact 12": {f"artifact {index:02d}" for index in range(1, 12)},
}
REQUIRED_HLD_ARTIFACT_UPSTREAM_SOURCES = {
    "artifact 01": {
        "proposal claims",
        "PRD-S00 至 PRD-S18",
        "PRD-FREEZE-01 至 PRD-FREEZE-14",
        "HLD-REQ-01 至 HLD-REQ-14",
        "4 条 story logic boundary",
    },
    "artifact 02": {
        "PRD-S00 至 PRD-S18",
        "PRD-FREEZE-01 至 PRD-FREEZE-14",
        "HLD-REQ-01 至 HLD-REQ-14",
        "story logic boundary",
    },
    "artifact 11": {
        "PRD canonical facts",
        "HLD-REQ",
        "freeze",
        "story logic boundary",
    },
    "artifact 12": {"HLD contract rules"},
}
REQUIRED_HLD_REFACTOR_FILE_TASKS = {
    "docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md",
    "docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md",
    "skills/novel-hld-writer/SKILL.md",
}
REQUIRED_DESIGN_PLANNING_SOURCE_PATHS = {
    "design/design-tasks/2026-07-07-duanxian-hld-design-planning/design-task-package.md",
    "docs/superpowers/plans/2026-07-07-novel-hld-workflow-refactor.md",
    "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/final-prd-package.md",
    "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/06-freeze-boundaries.md",
    "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/07-hld-expansion-requirements.md",
    "design/runs/prd/2026-07-07-duanxian-prd-workflow/artifacts/09-prd-risk-report.md",
}
DESIGN_PLANNING_CONTRACT_TASK_ID = "TASK-001"
REQUIRED_FIXTURE_SECTIONS = {
    "PROMPT.md": [
        "## Mission",
        "## Read First",
        "## Scope",
        "## Expected Outputs",
        "## Document Review Checks",
        "## Stop Conditions",
        "## Handoff Expectations",
    ],
    "AGENTS.md": [
        "## Role And Mission",
        "## Source Order",
        "## PRD/HLD Source Requirement",
        "## Task Fixture Source Requirement",
        "## Stack And Boundary Constraints",
        "## Hard Rules",
        "## Verification And Acceptance Expectations",
        "## Handoff Format",
    ],
    "CLAUDE.md": [
        "## Role",
        "## Fixed Input And Output Paths",
        "## Required Reading",
        "## Detailed Design Checklist",
        "## Task Boundary Rules",
        "## Consistency With AGENTS.md",
        "## Final Response",
    ],
}
REQUIRED_CONTRACT_RULE_BINDINGS = {
    "HLD-CONTRACT-01": (
        "HLD-GLOBAL-01 至 HLD-GLOBAL-12",
        "HLD-ENG-01, HLD-ENG-05",
        "validate_hld_contract.py::validate_hld_entry_gate",
        "test_validate_hld_contract.py::test_hld_blocks_without_prd_pass_to_hld",
    ),
    "HLD-CONTRACT-02": (
        "HLD-GLOBAL-01 至 HLD-GLOBAL-12",
        "HLD-ENG-02",
        "validate_hld_contract.py::validate_harness_purity",
        "test_validate_hld_contract.py::test_harness_contains_no_business_design",
    ),
    "HLD-CONTRACT-03": (
        "HLD-GLOBAL-01 至 HLD-GLOBAL-12",
        "HLD-SKILL-01 至 HLD-SKILL-12",
        "validate_hld_contract.py::validate_independent_skill_owners",
        "test_validate_hld_contract.py::test_every_hld_business_gate_has_independent_skill_owner",
    ),
    "HLD-CONTRACT-04": (
        "HLD-GLOBAL-11, HLD-GLOBAL-12",
        "HLD-ENG-01, HLD-ENG-02",
        "validate_hld_contract.py::validate_artifact_dag",
        "test_validate_hld_contract.py::test_artifact_11_does_not_depend_on_12",
    ),
    "HLD-CONTRACT-05": (
        "HLD-GLOBAL-01 至 HLD-GLOBAL-12",
        "HLD-SKILL-01 至 HLD-SKILL-12",
        "validate_hld_contract.py::validate_universal_skill_verdict_schema",
        "test_validate_hld_contract.py::test_every_artifact_has_structured_skill_verdict",
    ),
    "HLD-CONTRACT-06": (
        "HLD-GLOBAL-02, HLD-GLOBAL-11",
        "HLD-ENG-01, HLD-SKILL-02, HLD-SKILL-11",
        "validate_hld_contract.py::validate_source_reference_grammar",
        "test_validate_hld_contract.py::test_support_refs_use_allowed_source_grammar",
    ),
    "HLD-CONTRACT-07": (
        "HLD-GLOBAL-02, HLD-GLOBAL-11",
        "HLD-ENG-01, HLD-SKILL-11",
        "validate_hld_contract.py::validate_prd_canonical_fact_preservation",
        "test_validate_hld_contract.py::test_same_source_scene_fact_rewrite_fails",
    ),
    "HLD-CONTRACT-08": (
        "HLD-GLOBAL-03 至 HLD-GLOBAL-09",
        "HLD-SKILL-03 至 HLD-SKILL-09",
        "validate_hld_contract.py::validate_supported_world_system_facts",
        "test_validate_hld_contract.py::test_unsupported_core_hld_fact_fails",
    ),
    "HLD-CONTRACT-09": (
        "HLD-GLOBAL-01, HLD-GLOBAL-11",
        "HLD-ENG-01, HLD-ENG-04",
        "validate_hld_contract.py::validate_legacy_input_rejection",
        "test_validate_hld_contract.py::test_legacy_hld_lld_writing_are_not_frozen_inputs",
    ),
    "HLD-CONTRACT-10": (
        "HLD-GLOBAL-01",
        "HLD-SKILL-01",
        "validate_hld_contract.py::validate_world_entity_inventory_coverage",
        "test_validate_hld_contract.py::test_initial_inventory_covers_required_entity_types",
    ),
    "HLD-CONTRACT-11": (
        "HLD-GLOBAL-02, HLD-GLOBAL-10",
        "HLD-SKILL-02, HLD-SKILL-10",
        "validate_hld_contract.py::validate_support_matrix_coverage",
        "test_validate_hld_contract.py::test_support_matrix_covers_scenes_freeze_hldreq_storylogic_inventory",
    ),
    "HLD-CONTRACT-12": (
        "HLD-GLOBAL-12",
        "HLD-SKILL-12",
        "validate_hld_contract.py::validate_p0_p1_verdict_gate",
        "test_validate_hld_contract.py::test_unresolved_p0_p1_blocks_agent_quality_and_lld_entry",
    ),
    "HLD-CONTRACT-13": (
        "HLD-GLOBAL-03 至 HLD-GLOBAL-09",
        "HLD-SKILL-03 至 HLD-SKILL-09",
        "validate_hld_contract.py::validate_business_artifact_closure",
        "test_validate_hld_contract.py::test_business_artifacts_prove_inventory_support_boundary_and_no_prose_leakage",
    ),
    "HLD-CONTRACT-14": (
        "HLD-GLOBAL-11",
        "HLD-ENG-01, HLD-SKILL-11",
        "validate_hld_contract.py::validate_final_hld_schema_and_source_map",
        "test_validate_hld_contract.py::test_final_hld_missing_schema_or_fact_atoms_fails",
    ),
    "HLD-CONTRACT-15": (
        "HLD-GLOBAL-12",
        "HLD-SKILL-12",
        "validate_hld_contract.py::validate_lld_entry_state_machine",
        "test_validate_hld_contract.py::test_lld_entry_verdict_state_machine_is_closed",
    ),
    "HLD-CONTRACT-16": (
        "HLD-GLOBAL-10, HLD-GLOBAL-11",
        "HLD-SKILL-10, HLD-SKILL-11",
        "validate_hld_contract.py::validate_inventory_amendment_reconciliation",
        "test_validate_hld_contract.py::test_unreconciled_or_rejected_used_amendment_fails",
    ),
    "HLD-CONTRACT-17": (
        "HLD-GLOBAL-11",
        "HLD-SKILL-11",
        "validate_hld_contract.py::validate_story_logic_source_map_preservation",
        "test_validate_hld_contract.py::test_story_logic_boundary_missing_or_rewritten_fails",
    ),
    "HLD-CONTRACT-18": (
        "HLD-GLOBAL-12",
        "HLD-ENG-01, HLD-SKILL-12",
        "validate_hld_contract.py::validate_contract_rule_executable_coverage_and_convergence",
        "test_validate_hld_contract.py::test_contract_rules_and_convergence_have_executable_proof",
    ),
}
REQUIRED_FINAL_SCHEMA_BINDINGS = {
    "Revision table": (
        "harness package",
        "HLD-ENG-02",
        "validate_hld_contract.py::validate_final_schema_revision_table",
    ),
    "Input gate proof": (
        "harness input gate",
        "HLD-ENG-02",
        "validate_hld_contract.py::validate_final_schema_input_gate_proof",
    ),
    "HLD scope and exclusions": (
        "artifact 01",
        "HLD-SKILL-01",
        "validate_hld_contract.py::validate_final_schema_scope_and_exclusions",
    ),
    "World entity inventory": (
        "artifacts 01, 10",
        "HLD-SKILL-01, HLD-SKILL-10",
        "validate_hld_contract.py::validate_final_schema_world_entity_inventory",
    ),
    "PRD support matrix": (
        "artifacts 02, 10",
        "HLD-SKILL-02, HLD-SKILL-10",
        "validate_hld_contract.py::validate_final_schema_prd_support_matrix",
    ),
    "Worldview and world rules": (
        "artifact 03",
        "HLD-SKILL-03",
        "validate_hld_contract.py::validate_final_schema_worldview_and_rules",
    ),
    "World structure": (
        "artifacts 03, 05, 07",
        "HLD-SKILL-03, HLD-SKILL-05, HLD-SKILL-07",
        "validate_hld_contract.py::validate_final_schema_world_structure",
    ),
    "Character system": (
        "artifact 04",
        "HLD-SKILL-04",
        "validate_hld_contract.py::validate_final_schema_character_system",
    ),
    "Environment system": (
        "artifact 05",
        "HLD-SKILL-05",
        "validate_hld_contract.py::validate_final_schema_environment_system",
    ),
    "Event system": (
        "artifact 06",
        "HLD-SKILL-06",
        "validate_hld_contract.py::validate_final_schema_event_system",
    ),
    "Time and information system": (
        "artifact 07",
        "HLD-SKILL-07",
        "validate_hld_contract.py::validate_final_schema_time_information_system",
    ),
    "Thread system": (
        "artifact 08",
        "HLD-SKILL-08",
        "validate_hld_contract.py::validate_final_schema_thread_system",
    ),
    "Style and POV system": (
        "artifact 09",
        "HLD-SKILL-09",
        "validate_hld_contract.py::validate_final_schema_style_pov_system",
    ),
    "HLD Source Map": (
        "artifact 11",
        "HLD-SKILL-11",
        "validate_hld_contract.py::validate_final_schema_hld_source_map",
    ),
    "LLD handoff index": (
        "artifact 11",
        "HLD-SKILL-11",
        "validate_hld_contract.py::validate_final_schema_lld_handoff_index",
    ),
    "HLD risk report and LLD entry verdict": (
        "artifact 12",
        "HLD-SKILL-12",
        "validate_hld_contract.py::validate_final_schema_risk_report_and_lld_verdict",
    ),
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing file: {path.relative_to(ROOT)}")


def unquote(value: str) -> str:
    return value.strip().strip("`").strip()


def split_refs(value: str) -> list[str]:
    return [unquote(item) for item in value.split(",") if unquote(item)]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", unquote(value))


def normalized_binding(value: str) -> str:
    return normalize_text(value).lower()


def mentioned_artifact_refs(value: str) -> set[str]:
    refs = {f"artifact {int(ref):02d}" for ref in re.findall(r"\bartifacts?\s+(\d{2})\b", value)}
    for start, end in re.findall(r"\bartifact\s+(\d{2})\s*至\s*artifact\s+(\d{2})\b", value):
        start_index = int(start)
        end_index = int(end)
        if start_index <= end_index:
            refs.update(f"artifact {index:02d}" for index in range(start_index, end_index + 1))
    return refs


def extract_scene_refs(value: str) -> set[str]:
    return set(re.findall(r"PRD-S\d{2}", value))


def boundary_keywords(value: str) -> set[str]:
    normalized = normalize_text(value)
    keywords = set()
    for keyword in [
        "不得",
        "不能",
        "不允许",
        "不可",
        "已经正常交接",
        "直接成功读取",
        "技术故障",
        "普通加密",
        "成熟产品",
        "学长复活",
        "抽象大义",
        "简单加害者",
        "绕开数字生命体和研究员",
        "被保护者身份成为阻断危机的必要条件",
        "结案无代价",
        "组织命令",
        "研究员单方决定",
        "系统故障",
        "无约束超能力",
        "真正原因完整公开",
        "数字生命继续存活",
        "研究员立即释然",
        "直接复制",
        "直接接管",
        "抢走",
    ]:
        if keyword in normalized:
            keywords.add(keyword)
    return keywords


def required_answer_atoms(value: str) -> list[str]:
    normalized = normalize_text(value)
    normalized = re.sub(r"^HLD需(回答|定义)", "", normalized)
    atoms = []
    for atom in re.split(r"[，。、；：,;: ]+", normalized):
        atom = atom.strip()
        if len(atom) >= 4:
            atoms.append(atom)
    return atoms


def fact_atoms(value: str) -> list[str]:
    normalized = normalize_text(value)
    normalized = re.sub(r"(HLD/LLD/writing|HLD|LLD|writing|下游)", "", normalized)
    normalized = re.sub(r"(不得|不能|不允许|不可|必须|保留|把|将|让|改成|起点改成|也|只|仍会)", "", normalized)
    atoms: list[str] = []
    for atom in re.split(r"[，。、；：,;: ]+|以及|且|并且|或|和", normalized):
        atom = atom.strip()
        if len(atom) >= 4 and atom not in {"完整原因", "可用情报"}:
            atoms.append(atom)
    return atoms


def table_after_heading(text: str, heading: str, label: str) -> list[list[str]]:
    match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not match:
        raise ValueError(f"{label} missing heading: {heading}")
    section = text[match.end() :]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]

    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and not all(set(cell) <= {"-", ":"} for cell in cells):
            rows.append(cells)
    if len(rows) < 2:
        raise ValueError(f"{label} table under {heading} must include header and rows")
    return rows


def row_dicts(rows: list[list[str]], required_headers: list[str], label: str) -> list[dict[str, str]]:
    headers = rows[0]
    missing = [header for header in required_headers if header not in headers]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")

    result: list[dict[str, str]] = []
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            raise ValueError(f"{label} row {index} has {len(row)} cells, expected {len(headers)}")
        result.append(dict(zip(headers, row)))
    return result


def field_map(rows: list[list[str]], label: str) -> dict[str, str]:
    entries = row_dicts(rows, ["Field", "Value"], label)
    return {entry["Field"]: unquote(entry["Value"]) for entry in entries}


def load_design_task_package() -> dict:
    text = read(DESIGN_TASK_PACKAGE)
    metadata = field_map(table_after_heading(text, "Package Metadata", "design task package"), "metadata")
    coverage = row_dicts(
        table_after_heading(text, "PRD/HLD Coverage Matrix", "design task package"),
        REQUIRED_COVERAGE_COLUMNS,
        "coverage matrix",
    )
    hld_requirement_coverage = row_dicts(
        table_after_heading(text, "HLD Requirement Coverage Matrix", "design task package"),
        [
            "Requirement id",
            "Design task ids",
            "Owner artifacts",
            "Skill owners",
            "Supports",
            "Acceptance",
            "Boundary",
            "Status",
        ],
        "HLD requirement coverage matrix",
    )
    freeze_story_logic_coverage = row_dicts(
        table_after_heading(text, "Freeze and Story Logic Coverage Matrix", "design task package"),
        [
            "Source id",
            "Source type",
            "Supports",
            "Design task ids",
            "Owner artifacts",
            "Skill owners",
            "Preservation requirement",
            "Status",
        ],
        "freeze and story logic coverage matrix",
    )
    hld_artifact_coverage = row_dicts(
        table_after_heading(text, "HLD Artifact Task Coverage Matrix", "design task package"),
        [
            "Artifact id",
            "Skill owner",
            "Task id",
            "Task purpose",
            "Source obligations",
            "Acceptance",
            "Status",
        ],
        "HLD artifact task coverage matrix",
    )
    contract_rule_coverage = row_dicts(
        table_after_heading(text, "HLD Contract Rule Coverage Matrix", "design task package"),
        [
            "Rule id",
            "Design task ids",
            "Engineering task ids",
            "Planned validator coverage",
            "Planned regression proof",
            "Acceptance",
            "Status",
        ],
        "HLD contract rule coverage matrix",
    )
    artifact_schema_coverage = row_dicts(
        table_after_heading(text, "HLD Artifact Schema Coverage Matrix", "design task package"),
        [
            "Artifact id",
            "Required table",
            "Required columns",
            "Owner skill",
            "Engineering task id",
            "Validation target",
            "Status",
        ],
        "HLD artifact schema coverage matrix",
    )
    final_schema_coverage = row_dicts(
        table_after_heading(text, "Final HLD Schema Coverage Matrix", "design task package"),
        [
            "Section",
            "Source artifact",
            "Engineering task id",
            "Validation target",
            "Status",
        ],
        "final HLD schema coverage matrix",
    )
    engineering = row_dicts(
        table_after_heading(text, "HLD Workflow Engineering Task Matrix", "design task package"),
        ["Task id", "Task", "Output", "Acceptance", "Status"],
        "engineering task matrix",
    )
    return {
        "text": text,
        "workflow_node": metadata.get("Workflow node", ""),
        "prd_hld_entry_verdict": metadata.get("PRD HLD entry verdict", ""),
        "execution_policy": metadata.get("Execution policy", ""),
        "coverage": coverage,
        "hld_requirement_coverage": hld_requirement_coverage,
        "freeze_story_logic_coverage": freeze_story_logic_coverage,
        "hld_artifact_coverage": hld_artifact_coverage,
        "contract_rule_coverage": contract_rule_coverage,
        "artifact_schema_coverage": artifact_schema_coverage,
        "final_schema_coverage": final_schema_coverage,
        "engineering": engineering,
    }


def load_manifest() -> dict:
    text = read(DESIGN_TASK_MANIFEST)
    metadata = field_map(table_after_heading(text, "Package Metadata", "design task manifest"), "manifest metadata")
    return {"text": text, "metadata": metadata}


def load_design_planning_json() -> dict:
    try:
        return json.loads(read(DESIGN_PLANNING_JSON))
    except json.JSONDecodeError as exc:
        fail(f"invalid design-planning.json: {exc}")
    raise AssertionError("unreachable")


def find_design_planning_schema_violations(plan: dict) -> list[str]:
    if not DESIGN_PLANNING_SCHEMA.exists():
        return [f"missing design-planning schema: {DESIGN_PLANNING_SCHEMA}"]
    schema = json.loads(DESIGN_PLANNING_SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(plan), key=lambda error: list(error.path))
    violations: list[str] = []
    for error in errors:
        path = "/" + "/".join(str(part) for part in error.path)
        violations.append(f"design-planning.json schema violation at {path}: {error.message}")
    return violations


def find_fixture_contract_violations(task: dict, fixture_dir: Path) -> list[str]:
    violations: list[str] = []
    task_id = str(task.get("task_id", "<missing>"))
    title = str(task.get("title", ""))
    design_doc_path = str(task.get("design_doc_path", ""))
    source_refs = [str(ref) for ref in task.get("source_refs", [])]

    for file_name, required_sections in REQUIRED_FIXTURE_SECTIONS.items():
        path = fixture_dir / file_name
        if not path.exists():
            violations.append(f"{task_id}: missing fixture file {file_name}")
            continue
        text = path.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                violations.append(f"{task_id}: {file_name} missing section {section}")
        for required_text in [
            "Do not implement code",
            "Do not modify production source files",
            "docs/design/",
            design_doc_path,
            task_id,
        ]:
            if required_text and required_text not in text:
                violations.append(f"{task_id}: {file_name} missing required text {required_text}")
        if title and title not in text:
            violations.append(f"{task_id}: {file_name} missing task title")
        if "HLD business" not in text:
            violations.append(f"{task_id}: {file_name} missing HLD business boundary")
        if file_name in {"PROMPT.md", "AGENTS.md", "CLAUDE.md"}:
            missing_refs = [ref for ref in source_refs if ref not in text]
            if missing_refs:
                violations.append(f"{task_id}: {file_name} missing source refs {missing_refs}")

    return violations


def find_acceptance_dependency_contract_violations(plan: dict) -> list[str]:
    violations: list[str] = []
    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list):
        return ["design-planning.json: tasks must be a list for acceptance dependency validation"]
    task_index = {task.get("task_id"): task for task in tasks if isinstance(task, dict)}
    acceptance_tasks = [
        task for task in tasks if isinstance(task, dict) and task.get("task_type") == "design_acceptance"
    ]
    for acceptance in acceptance_tasks:
        task_id = str(acceptance.get("task_id", "<missing>"))
        fixture_dir_value = str(acceptance.get("fixture_dir", ""))
        fixture_dir = Path(fixture_dir_value)
        if not fixture_dir.is_absolute():
            fixture_dir = ROOT / fixture_dir
        dependencies = acceptance.get("dependencies", [])
        if not dependencies:
            violations.append(f"{task_id}: design_acceptance task must list detailed task dependencies")
            continue
        for dep_id in dependencies:
            dependency = task_index.get(dep_id)
            if not isinstance(dependency, dict):
                violations.append(f"{task_id}: unknown acceptance dependency {dep_id}")
                continue
            domain_task_id = str(dependency.get("domain_task_id", dep_id))
            design_doc_path = str(dependency.get("design_doc_path", ""))
            dependency_fixture_dir = str(dependency.get("fixture_dir", ""))
            expected_fragments = [
                (f"{dep_id} -> {domain_task_id}", "acceptance dependency"),
                (design_doc_path, "acceptance dependency design document"),
                (dependency_fixture_dir, "acceptance dependency fixture"),
            ]
            for file_name in ["PROMPT.md", "AGENTS.md", "CLAUDE.md"]:
                path = fixture_dir / file_name
                if not path.exists():
                    violations.append(f"{task_id}: missing acceptance fixture file {path}")
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment, label in expected_fragments:
                    if fragment and fragment not in text:
                        violations.append(f"{task_id}: {file_name} missing {label} {fragment}")
    return violations


def find_design_planning_contract_violations() -> list[str]:
    violations: list[str] = []
    required_files = [
        DESIGN_PLANNING_JSON,
        DESIGN_PLANNING_QUALITY_VALIDATOR,
        DESIGN_PLANNING_ROOT_DESIGN_DOC,
    ]
    for path in required_files:
        if not path.exists():
            violations.append(f"missing design-planning output: {path.relative_to(ROOT)}")
    if not DESIGN_PLANNING_JSON.exists():
        return violations

    plan = load_design_planning_json()
    violations.extend(find_design_planning_schema_violations(plan))
    if plan.get("planning_status") != "ready":
        violations.append("design-planning.json: planning_status must be ready")
    if plan.get("output_root") != "tasks/design":
        violations.append("design-planning.json: output_root must be tasks/design")
    if plan.get("detailed_design_root") != "docs/design":
        violations.append("design-planning.json: detailed_design_root must be docs/design")
    if plan.get("quality_validator_path") != "tasks/design/validate_design_doc_quality.py":
        violations.append("design-planning.json: quality_validator_path must be tasks/design/validate_design_doc_quality.py")

    tasks = plan.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        violations.append("design-planning.json: tasks must be non-empty")
        return violations
    detailed_tasks = [task for task in tasks if task.get("task_type") == "detailed_design"]
    acceptance_tasks = [task for task in tasks if task.get("task_type") == "design_acceptance"]
    if not detailed_tasks:
        violations.append("design-planning.json: must include detailed_design tasks")
    if len(acceptance_tasks) != 1:
        violations.append("design-planning.json: must include exactly one design_acceptance task")

    detailed_ids = {task.get("task_id") for task in detailed_tasks}
    if acceptance_tasks:
        missing_deps = sorted(detailed_ids - set(acceptance_tasks[0].get("dependencies", [])))
        if missing_deps:
            violations.append(f"design acceptance task missing dependencies {missing_deps}")

    required_fixture_files = ["PROMPT.md", "AGENTS.md", "CLAUDE.md", "spec.yaml"]
    for task in tasks:
        task_id = task.get("task_id", "<missing>")
        for field in [
            "source_refs",
            "inputs",
            "outputs",
            "allowed_scope",
            "forbidden_scope",
            "acceptance",
            "verification",
            "stop_conditions",
            "dependencies",
            "design_doc_path",
            "fixture_dir",
            "prompt_path",
            "agents_path",
            "claude_path",
            "spec_path",
        ]:
            if field not in task:
                violations.append(f"{task_id}: missing design-planning task field {field}")
        design_doc_path = task.get("design_doc_path", "")
        if not str(design_doc_path).startswith("docs/design/"):
            violations.append(f"{task_id}: design_doc_path must be under docs/design")
        expected_fixture_dir = f"tasks/design/fixtures/{task_id}"
        if task.get("fixture_dir") != expected_fixture_dir:
            violations.append(f"{task_id}: fixture_dir must be {expected_fixture_dir}")
        for file_name in required_fixture_files:
            fixture_file = ROOT / str(task.get("fixture_dir", "")) / file_name
            if not fixture_file.exists():
                violations.append(f"{task_id}: missing fixture file {fixture_file.relative_to(ROOT)}")
        fixture_dir = ROOT / str(task.get("fixture_dir", ""))
        violations.extend(find_fixture_contract_violations(task, fixture_dir))

    violations.extend(find_acceptance_dependency_contract_violations(plan))
    violations.extend(find_design_planning_coverage_violations(plan, load_design_task_package()))
    return violations


def fine_coverage_entries(plan: dict) -> dict[tuple[str, str], dict]:
    entries: dict[tuple[str, str], dict] = {}
    for row in plan.get("coverage_matrix", []):
        source_type = row.get("source_type")
        source_id = row.get("source_id")
        if source_type and source_id:
            entries[(str(source_type), str(source_id))] = row
    return entries


def required_design_planning_coverage_ids() -> dict[str, list[str]]:
    prd_scene_ids = sorted(extract_scene_refs(read(PRD_PACKAGE)))
    return {
        "prd_scene": prd_scene_ids,
        "hld_requirement": extract_prd_hld_requirements(),
        "freeze_boundary": extract_prd_freeze_boundaries(),
        "story_logic_boundary": extract_prd_story_logic_boundaries(),
    }


def find_design_planning_coverage_violations(plan: dict, package: dict) -> list[str]:
    violations: list[str] = []
    source_paths = {item.get("path") for item in plan.get("source_inventory", []) if isinstance(item, dict)}
    missing_sources = sorted(REQUIRED_DESIGN_PLANNING_SOURCE_PATHS - source_paths)
    for path in missing_sources:
        violations.append(f"design-planning.json source_inventory missing material source: {path}")

    task_ids = {task.get("task_id") for task in plan.get("tasks", []) if task.get("task_type") == "detailed_design"}
    coverage = fine_coverage_entries(plan)
    for source_type, source_ids in required_design_planning_coverage_ids().items():
        for source_id in source_ids:
            row = coverage.get((source_type, source_id))
            if row is None:
                violations.append(f"design-planning.json coverage_matrix missing {source_type} coverage: {source_id}")
                continue
            row_task_ids = set(row.get("task_ids", []))
            if not row_task_ids:
                violations.append(f"design-planning.json coverage_matrix {source_type}:{source_id} has no task_ids")
            unknown_tasks = sorted(row_task_ids - task_ids)
            if unknown_tasks:
                violations.append(
                    f"design-planning.json coverage_matrix {source_type}:{source_id} has unknown detailed task_ids {unknown_tasks}"
                )
            if DESIGN_PLANNING_CONTRACT_TASK_ID not in row_task_ids:
                violations.append(
                    f"design-planning.json coverage_matrix {source_type}:{source_id} "
                    f"must include {DESIGN_PLANNING_CONTRACT_TASK_ID}"
                )
            if not row.get("source_refs"):
                violations.append(f"design-planning.json coverage_matrix {source_type}:{source_id} missing source_refs")

    return violations


def extract_prd_hld_handoff_themes() -> list[str]:
    return [row["HLD 主题"].strip() for row in extract_prd_hld_handoff_rows()]


def extract_prd_hld_handoff_rows() -> list[dict[str, str]]:
    text = read(PRD_PACKAGE)
    rows = row_dicts(
        table_after_heading(text, "10. HLD 交接要求", "final PRD package"),
        ["HLD 主题", "支撑场景", "必须回答的问题", "不得突破的边界", "出处"],
        "PRD HLD handoff table",
    )
    return rows


def extract_prd_hld_requirements() -> list[str]:
    return [row["Requirement id"].strip() for row in extract_prd_hld_requirement_rows()]


def extract_prd_hld_requirement_rows() -> list[dict[str, str]]:
    text = read(PRD_HLD_REQUIREMENTS)
    rows = row_dicts(
        table_after_heading(text, "HLD expansion requirement list", "PRD HLD requirements"),
        ["Requirement id", "Required expansion", "Supports scene ids", "Required answer", "Boundary", "Source"],
        "PRD HLD requirements",
    )
    return rows


def extract_prd_freeze_boundaries() -> list[str]:
    return [row["Freeze id"].strip() for row in extract_prd_freeze_boundary_rows()]


def extract_prd_freeze_boundary_rows() -> list[dict[str, str]]:
    text = read(PRD_FREEZE_BOUNDARIES)
    rows = row_dicts(
        table_after_heading(text, "Freeze boundary list", "PRD freeze boundaries"),
        ["Freeze id", "Frozen item", "Source", "Downstream no-change rule", "Reopen condition"],
        "PRD freeze boundaries",
    )
    return rows


def extract_prd_story_logic_boundaries() -> list[str]:
    return [row["边界"].strip() for row in extract_prd_story_logic_boundary_rows()]


def extract_prd_story_logic_boundary_rows() -> list[dict[str, str]]:
    text = read(PRD_PACKAGE)
    rows = row_dicts(
        table_after_heading(text, "7. 故事逻辑边界", "final PRD package"),
        ["边界", "PRD 冻结答案", "HLD 可展开内容"],
        "PRD story logic boundary table",
    )
    return rows


def find_missing_handoff_theme_coverage(package: dict, prd_themes: list[str]) -> list[str]:
    covered = {row["PRD handoff theme"].strip() for row in package["coverage"]}
    return [theme for theme in prd_themes if theme not in covered]


def find_prd_handoff_fact_mismatches(package: dict, prd_rows: list[dict[str, str]]) -> list[str]:
    rows = {row["PRD handoff theme"].strip(): row for row in package["coverage"]}
    mismatches: list[str] = []
    for prd_row in prd_rows:
        theme = prd_row["HLD 主题"].strip()
        package_row = rows.get(theme)
        if not package_row:
            continue
        if extract_scene_refs(package_row["Supports"]) != extract_scene_refs(prd_row["支撑场景"]):
            mismatches.append(f"{theme}: support scenes do not match PRD HLD handoff")
        prd_boundary_atoms = set(fact_atoms(prd_row["不得突破的边界"]))
        package_boundary_atoms = set(fact_atoms(package_row["Execution boundary"]))
        if prd_boundary_atoms - package_boundary_atoms:
            mismatches.append(f"{theme}: execution boundary omits PRD handoff boundary facts")
    return mismatches


def find_missing_hld_requirement_coverage(package: dict, hld_requirements: list[str]) -> list[str]:
    covered = {row["Requirement id"].strip() for row in package["hld_requirement_coverage"]}
    return [requirement_id for requirement_id in hld_requirements if requirement_id not in covered]


def find_missing_freeze_boundary_coverage(package: dict, freeze_boundaries: list[str]) -> list[str]:
    covered = {
        row["Source id"].strip()
        for row in package["freeze_story_logic_coverage"]
        if row["Source type"].strip() == "freeze_boundary"
    }
    return [freeze_id for freeze_id in freeze_boundaries if freeze_id not in covered]


def find_missing_story_logic_coverage(package: dict, story_logic_boundaries: list[str]) -> list[str]:
    covered = {
        row["Source id"].strip()
        for row in package["freeze_story_logic_coverage"]
        if row["Source type"].strip() == "story_logic_boundary"
    }
    return [boundary for boundary in story_logic_boundaries if boundary not in covered]


def find_missing_contract_rule_coverage(package: dict) -> list[str]:
    covered = {row["Rule id"].strip() for row in package["contract_rule_coverage"]}
    return sorted(REQUIRED_CONTRACT_RULE_IDS - covered)


def find_missing_hld_artifact_task_coverage(package: dict) -> list[str]:
    covered = {row["Artifact id"].strip() for row in package["hld_artifact_coverage"]}
    return sorted(REQUIRED_HLD_ARTIFACT_IDS - covered)


def find_hld_requirement_fact_mismatches(
    package: dict,
    hld_requirements: list[dict[str, str]],
) -> list[str]:
    by_id = {row["Requirement id"].strip(): row for row in package["hld_requirement_coverage"]}
    mismatches: list[str] = []
    for prd_row in hld_requirements:
        requirement_id = prd_row["Requirement id"].strip()
        package_row = by_id.get(requirement_id)
        if not package_row:
            continue
        if extract_scene_refs(package_row["Supports"]) != extract_scene_refs(prd_row["Supports scene ids"]):
            mismatches.append(f"{requirement_id}: supports scene ids do not match PRD")
        prd_boundary_keywords = boundary_keywords(prd_row["Boundary"])
        package_boundary_keywords = boundary_keywords(package_row["Boundary"])
        missing_boundary = prd_boundary_keywords - package_boundary_keywords
        if missing_boundary:
            mismatches.append(f"{requirement_id}: boundary weakens PRD keywords {sorted(missing_boundary)}")
        prd_answer_keywords = required_answer_atoms(prd_row["Required answer"])
        package_acceptance = normalize_text(package_row["Acceptance"])
        missing_answer = [keyword for keyword in prd_answer_keywords if keyword not in package_acceptance]
        if missing_answer:
            mismatches.append(f"{requirement_id}: acceptance omits PRD required-answer facts")
    return mismatches


def find_freeze_boundary_fact_mismatches(
    package: dict,
    freeze_boundaries: list[dict[str, str]],
) -> list[str]:
    rows = {
        row["Source id"].strip(): row
        for row in package["freeze_story_logic_coverage"]
        if row["Source type"].strip() == "freeze_boundary"
    }
    mismatches: list[str] = []
    for prd_row in freeze_boundaries:
        freeze_id = prd_row["Freeze id"].strip()
        package_row = rows.get(freeze_id)
        if not package_row:
            continue
        if extract_scene_refs(package_row["Supports"]) != extract_scene_refs(prd_row["Source"]):
            mismatches.append(f"{freeze_id}: supports scene refs do not match PRD source refs")
        prd_keywords = boundary_keywords(prd_row["Downstream no-change rule"])
        package_keywords = boundary_keywords(package_row["Preservation requirement"])
        missing_keywords = prd_keywords - package_keywords
        if missing_keywords:
            mismatches.append(f"{freeze_id}: preservation weakens PRD no-change keywords {sorted(missing_keywords)}")
        prd_atoms = set(fact_atoms(prd_row["Downstream no-change rule"]))
        package_atoms = set(fact_atoms(package_row["Preservation requirement"]))
        if prd_atoms - package_atoms:
            mismatches.append(f"{freeze_id}: preservation omits PRD no-change facts")
    return mismatches


def find_story_logic_fact_mismatches(
    package: dict,
    story_logic_boundaries: list[dict[str, str]],
) -> list[str]:
    rows = {
        row["Source id"].strip(): row
        for row in package["freeze_story_logic_coverage"]
        if row["Source type"].strip() == "story_logic_boundary"
    }
    mismatches: list[str] = []
    for prd_row in story_logic_boundaries:
        boundary = prd_row["边界"].strip()
        package_row = rows.get(boundary)
        if not package_row:
            continue
        prd_atoms = set(fact_atoms(prd_row["PRD 冻结答案"]))
        package_atoms = set(fact_atoms(package_row["Preservation requirement"]))
        if prd_atoms - package_atoms:
            mismatches.append(f"{boundary}: preservation omits PRD story-logic facts")
    return mismatches


def owner_pairs_for_row(row: dict[str, str]) -> tuple[list[str], list[str]]:
    artifact_value = row.get("Owner artifacts", row.get("Owner artifact", ""))
    skill_value = row.get("Skill owners", row.get("Skill owner", ""))
    return split_refs(artifact_value), split_refs(skill_value)


def find_owner_topology_violations(package: dict) -> list[str]:
    violations: list[str] = []
    row_sets = [
        ("PRD/HLD Coverage Matrix", package["coverage"]),
        ("HLD Requirement Coverage Matrix", package["hld_requirement_coverage"]),
        ("Freeze and Story Logic Coverage Matrix", package["freeze_story_logic_coverage"]),
    ]
    for label, rows in row_sets:
        for row in rows:
            row_id = row.get("Task id") or row.get("Requirement id") or row.get("Source id") or "unknown"
            artifacts, skills = owner_pairs_for_row(row)
            if not artifacts:
                violations.append(f"{label} {row_id}: missing owner artifacts")
                continue
            if len(artifacts) != len(skills):
                violations.append(f"{label} {row_id}: owner artifact count does not match skill owner count")
                continue
            for artifact, skill in zip(artifacts, skills):
                expected = ARTIFACT_SKILL_OWNERS.get(artifact)
                if expected is None:
                    violations.append(f"{label} {row_id}: unknown owner artifact {artifact}")
                elif expected != skill:
                    violations.append(f"{label} {row_id}: {artifact} must be owned by {expected}, got {skill}")
    return violations


def find_hld_artifact_topology_violations(package: dict) -> list[str]:
    violations: list[str] = []
    for row in package["hld_artifact_coverage"]:
        artifact = row["Artifact id"].strip()
        expected = ARTIFACT_SKILL_OWNERS.get(artifact)
        owner = unquote(row["Skill owner"])
        if expected is None:
            violations.append(f"{artifact}: unknown HLD artifact")
        elif owner != expected:
            violations.append(f"{artifact}: must be owned by {expected}, got {owner}")
    return violations


def find_hld_artifact_task_closure_violations(package: dict) -> list[str]:
    violations: list[str] = []
    rows = {row["Artifact id"].strip(): row for row in package["hld_artifact_coverage"]}
    for artifact in sorted(REQUIRED_HLD_ARTIFACT_IDS):
        row = rows.get(artifact)
        if not row:
            continue
        required_fields = [
            row["Skill owner"],
            row["Task id"],
            row["Task purpose"],
            row["Source obligations"],
            row["Acceptance"],
            row["Status"],
        ]
        if any(unquote(value).lower() in PLACEHOLDER_VALUES for value in required_fields):
            violations.append(f"{artifact}: missing task-level closure fields")
            continue
        expected_task_id = f"HLD-GLOBAL-{artifact.split()[1]}"
        if row["Task id"].strip() != expected_task_id:
            violations.append(f"{artifact}: task id must be {expected_task_id}")
        if unquote(row["Status"]) not in BLOCKED_TASK_STATUSES:
            violations.append(f"{artifact}: invalid blocked planning status")
        required_dependencies = REQUIRED_HLD_ARTIFACT_DEPENDENCIES[artifact]
        missing_dependencies = sorted(required_dependencies - mentioned_artifact_refs(row["Source obligations"]))
        if missing_dependencies:
            violations.append(f"{artifact}: source obligations must include topology dependencies {missing_dependencies}")
        required_upstream_sources = REQUIRED_HLD_ARTIFACT_UPSTREAM_SOURCES.get(artifact, set())
        missing_upstream_sources = sorted(
            source for source in required_upstream_sources if source not in row["Source obligations"]
        )
        if missing_upstream_sources:
            violations.append(f"{artifact}: source obligations must include required upstream sources {missing_upstream_sources}")

    artifact_10 = rows.get("artifact 10", {})
    if "finalinventory" not in normalize_text(artifact_10.get("Acceptance", "")).lower():
        violations.append("artifact 10: acceptance must close final inventory reconciliation")
    artifact_11 = rows.get("artifact 11", {})
    artifact_11_acceptance = normalize_text(artifact_11.get("Acceptance", "")).lower()
    if "sourcemap" not in artifact_11_acceptance or "factatom" not in artifact_11_acceptance:
        violations.append("artifact 11: acceptance must require fact-level HLD Source Map")
    artifact_12 = rows.get("artifact 12", {})
    artifact_12_acceptance = normalize_text(artifact_12.get("Acceptance", "")).lower()
    if "p0/p1" not in artifact_12_acceptance or "verdict" not in artifact_12_acceptance:
        violations.append("artifact 12: acceptance must bind P0/P1 to verdict")

    return violations


def find_artifact_schema_coverage_violations(package: dict) -> list[str]:
    rows = {row["Artifact id"].strip(): row for row in package["artifact_schema_coverage"]}
    violations: list[str] = []
    for artifact, (required_table, required_columns) in REQUIRED_ARTIFACT_SCHEMAS.items():
        row = rows.get(artifact)
        if not row:
            violations.append(f"{artifact}: missing artifact schema coverage")
            continue
        if required_table not in row["Required table"]:
            violations.append(f"{artifact}: required table must include {required_table}")
        columns_text = row["Required columns"]
        missing_columns = [column for column in required_columns if column not in columns_text]
        if missing_columns:
            violations.append(f"{artifact}: missing required schema columns {missing_columns}")
        expected_owner = ARTIFACT_SKILL_OWNERS[artifact]
        expected_index = artifact.split()[1]
        expected_task = f"HLD-SKILL-{expected_index}"
        expected_validation_target = f"validate_hld_contract.py::validate_artifact_{expected_index}_schema"
        if unquote(row["Owner skill"]) != expected_owner:
            violations.append(f"{artifact}: owner skill must be {expected_owner}")
        if unquote(row["Engineering task id"]) != expected_task:
            violations.append(f"{artifact}: engineering task id must be {expected_task}")
        if unquote(row["Validation target"]) != expected_validation_target:
            violations.append(f"{artifact}: validation target must be {expected_validation_target}")
        if unquote(row["Status"]) not in ENGINEERING_TASK_STATUSES:
            violations.append(f"{artifact}: invalid schema coverage status")
    return violations


def find_final_schema_coverage_violations(package: dict) -> list[str]:
    rows = package["final_schema_coverage"]
    sections = [row["Section"].strip() for row in rows]
    violations: list[str] = []
    if sections != REQUIRED_FINAL_HLD_SCHEMA_SECTIONS:
        violations.append("final HLD schema sections must match required order")
    for row in rows:
        if unquote(row["Status"]) not in ENGINEERING_TASK_STATUSES:
            violations.append(f"{row['Section']}: invalid final schema status")
        required_values = [row["Source artifact"], row["Engineering task id"], row["Validation target"]]
        if any(unquote(value).lower() in PLACEHOLDER_VALUES for value in required_values):
            violations.append(f"{row['Section']}: missing final schema closure fields")
        expected_binding = REQUIRED_FINAL_SCHEMA_BINDINGS.get(row["Section"].strip())
        if expected_binding is None:
            continue
        expected_source, expected_task, expected_validation_target = expected_binding
        if normalized_binding(row["Source artifact"]) != normalized_binding(expected_source):
            violations.append(f"{row['Section']}: source artifact must be {expected_source}")
        if normalized_binding(row["Engineering task id"]) != normalized_binding(expected_task):
            violations.append(f"{row['Section']}: engineering task id must be {expected_task}")
        if unquote(row["Validation target"]) != expected_validation_target:
            violations.append(f"{row['Section']}: validation target must be {expected_validation_target}")
    return violations


def find_contract_rule_coverage_violations(package: dict) -> list[str]:
    violations: list[str] = []
    for row in package["contract_rule_coverage"]:
        rule_id = row["Rule id"].strip()
        required_values = [
            row["Design task ids"],
            row["Engineering task ids"],
            row["Planned validator coverage"],
            row["Planned regression proof"],
            row["Acceptance"],
        ]
        if rule_id not in REQUIRED_CONTRACT_RULE_IDS:
            violations.append(f"{rule_id}: unknown contract rule")
            continue
        if any(unquote(value).lower() in PLACEHOLDER_VALUES for value in required_values):
            violations.append(f"{rule_id}: missing contract rule coverage fields")
        expected_design, expected_engineering, expected_validator, expected_regression = REQUIRED_CONTRACT_RULE_BINDINGS[rule_id]
        if normalized_binding(row["Design task ids"]) != normalized_binding(expected_design):
            violations.append(f"{rule_id}: design task ids must be {expected_design}")
        if normalized_binding(row["Engineering task ids"]) != normalized_binding(expected_engineering):
            violations.append(f"{rule_id}: engineering task ids must be {expected_engineering}")
        if unquote(row["Planned validator coverage"]) != expected_validator:
            violations.append(f"{rule_id}: validator coverage must be {expected_validator}")
        if unquote(row["Planned regression proof"]) != expected_regression:
            violations.append(f"{rule_id}: regression proof must be {expected_regression}")
        if unquote(row["Status"]) not in ENGINEERING_TASK_STATUSES:
            violations.append(f"{rule_id}: invalid contract rule coverage status")
    return violations


def find_hld_skill_engineering_task_violations(package: dict) -> list[str]:
    outputs = {unquote(row["Output"]) for row in package["engineering"]}
    violations: list[str] = []
    for artifact, skill in ARTIFACT_SKILL_OWNERS.items():
        expected_output = f"skills/{skill}/SKILL.md"
        if expected_output not in outputs:
            violations.append(f"{artifact}: missing independent engineering task for {skill}")
    for row in package["engineering"]:
        if "12 个 HLD 独立技能" in row["Task"] or "12 个 `skills/novel-*` HLD skill" in row["Output"]:
            violations.append(f"{row['Task id']}: aggregates independent HLD skills")
    return violations


def find_missing_hld_refactor_file_tasks(package: dict) -> list[str]:
    engineering_text = "\n".join(
        f"{row['Task']} {row['Output']} {row['Acceptance']}" for row in package["engineering"]
    )
    return sorted(path for path in REQUIRED_HLD_REFACTOR_FILE_TASKS if path not in engineering_text)


def find_invalid_coverage_rows(package: dict) -> list[str]:
    invalid: list[str] = []
    prd_themes = set(extract_prd_hld_handoff_themes())
    seen_themes: set[str] = set()
    for row in package["coverage"]:
        task_id = row["Task id"].strip()
        required_values = [
            row["PRD handoff theme"],
            row["Supports"],
            row["Owner artifact"],
            row["Skill owner"],
            row["Acceptance"],
            row["Execution boundary"],
            row["Status"],
        ]
        if not task_id.startswith("HLD-DESIGN-"):
            invalid.append(f"{task_id}: invalid task id")
        theme = row["PRD handoff theme"].strip()
        if theme not in prd_themes:
            invalid.append(f"{task_id}: design task is not backed by PRD HLD handoff")
        elif theme in seen_themes:
            invalid.append(f"{task_id}: duplicate PRD HLD handoff theme {theme}")
        seen_themes.add(theme)
        if any(not value.strip() or value.strip().lower() in {"tbd", "unknown", "n/a"} for value in required_values):
            invalid.append(f"{task_id}: empty or placeholder value")
        if not row["Owner artifact"].strip().startswith("artifact "):
            invalid.append(f"{task_id}: owner artifact must name artifact xx")
        if "不得改写 PRD" not in row["Execution boundary"]:
            invalid.append(f"{task_id}: boundary must forbid PRD rewrite")
    return invalid


def find_illegal_business_execution(package: dict) -> list[str]:
    if package["prd_hld_entry_verdict"] != BLOCKED_VERDICT:
        return []
    if package["execution_policy"] != BLOCKED_POLICY:
        return ["package execution policy does not encode blocked planning-only state"]

    illegal: list[str] = []
    for row in package["coverage"]:
        status = unquote(row["Status"])
        if status not in BLOCKED_TASK_STATUSES:
            illegal.append(f"{row['Task id']}: illegal status while PRD HLD entry is blocked: {status}")
    return illegal


def find_invalid_engineering_status(package: dict) -> list[str]:
    invalid: list[str] = []
    for row in package["engineering"]:
        status = unquote(row["Status"])
        if status not in ENGINEERING_TASK_STATUSES:
            invalid.append(f"{row['Task id']}: invalid engineering status: {status}")
    return invalid


def find_engineering_business_output_violations(package: dict) -> list[str]:
    violations: list[str] = []
    for row in package["engineering"]:
        output = normalize_text(row["Output"]).lower()
        task_id = row["Task id"].strip()
        if "artifact01-12" in output or "final-hld-package" in output or re.search(r"artifact0[1-9]|artifact1[0-2]", output):
            violations.append(f"{task_id}: engineering output points to business HLD artifacts")
    return violations


def find_manifest_status_violations(manifest: dict) -> list[str]:
    violations: list[str] = []
    if "待校验" in manifest["text"]:
        violations.append("manifest: validation state must not be pending after validator pass")
    metadata = manifest["metadata"]
    if metadata.get("PRD HLD entry verdict") != BLOCKED_VERDICT:
        violations.append("manifest: PRD HLD entry verdict must mirror blocked PRD state")
    if metadata.get("Execution policy") != BLOCKED_POLICY:
        violations.append("manifest: execution policy must mirror planning-only state")
    return violations


def validate() -> None:
    package = load_design_task_package()
    if package["workflow_node"] != "hld-design-planning":
        raise ValueError("design task package workflow node must be hld-design-planning")
    if package["prd_hld_entry_verdict"] != BLOCKED_VERDICT:
        raise ValueError("design task package must reflect current PRD blocked HLD entry verdict")
    if package["execution_policy"] != BLOCKED_POLICY:
        raise ValueError("design task package must be planning-only until PRD human confirmation")

    missing = find_missing_handoff_theme_coverage(package, extract_prd_hld_handoff_themes())
    if missing:
        raise ValueError(f"missing PRD HLD handoff theme coverage: {missing}")
    missing_requirements = find_missing_hld_requirement_coverage(package, extract_prd_hld_requirements())
    if missing_requirements:
        raise ValueError(f"missing PRD HLD requirement coverage: {missing_requirements}")
    missing_freeze = find_missing_freeze_boundary_coverage(package, extract_prd_freeze_boundaries())
    if missing_freeze:
        raise ValueError(f"missing PRD freeze boundary coverage: {missing_freeze}")
    missing_story_logic = find_missing_story_logic_coverage(package, extract_prd_story_logic_boundaries())
    if missing_story_logic:
        raise ValueError(f"missing PRD story logic coverage: {missing_story_logic}")
    invalid = find_invalid_coverage_rows(package)
    if invalid:
        raise ValueError(f"invalid design task coverage rows: {invalid}")
    handoff_mismatches = find_prd_handoff_fact_mismatches(package, extract_prd_hld_handoff_rows())
    if handoff_mismatches:
        raise ValueError(f"PRD HLD handoff fact mismatches: {handoff_mismatches}")
    owner_violations = find_owner_topology_violations(package)
    if owner_violations:
        raise ValueError(f"owner topology violations: {owner_violations}")
    missing_artifacts = find_missing_hld_artifact_task_coverage(package)
    if missing_artifacts:
        raise ValueError(f"missing HLD artifact task coverage: {missing_artifacts}")
    missing_contract_rules = find_missing_contract_rule_coverage(package)
    if missing_contract_rules:
        raise ValueError(f"missing HLD contract rule coverage: {missing_contract_rules}")
    contract_rule_violations = find_contract_rule_coverage_violations(package)
    if contract_rule_violations:
        raise ValueError(f"HLD contract rule coverage violations: {contract_rule_violations}")
    artifact_topology_violations = find_hld_artifact_topology_violations(package)
    if artifact_topology_violations:
        raise ValueError(f"HLD artifact topology violations: {artifact_topology_violations}")
    artifact_task_closure_violations = find_hld_artifact_task_closure_violations(package)
    if artifact_task_closure_violations:
        raise ValueError(f"HLD artifact task closure violations: {artifact_task_closure_violations}")
    artifact_schema_violations = find_artifact_schema_coverage_violations(package)
    if artifact_schema_violations:
        raise ValueError(f"HLD artifact schema coverage violations: {artifact_schema_violations}")
    final_schema_violations = find_final_schema_coverage_violations(package)
    if final_schema_violations:
        raise ValueError(f"final HLD schema coverage violations: {final_schema_violations}")
    requirement_mismatches = find_hld_requirement_fact_mismatches(package, extract_prd_hld_requirement_rows())
    if requirement_mismatches:
        raise ValueError(f"HLD requirement fact mismatches: {requirement_mismatches}")
    freeze_mismatches = find_freeze_boundary_fact_mismatches(package, extract_prd_freeze_boundary_rows())
    if freeze_mismatches:
        raise ValueError(f"freeze boundary fact mismatches: {freeze_mismatches}")
    story_logic_mismatches = find_story_logic_fact_mismatches(package, extract_prd_story_logic_boundary_rows())
    if story_logic_mismatches:
        raise ValueError(f"story logic fact mismatches: {story_logic_mismatches}")
    illegal = find_illegal_business_execution(package)
    if illegal:
        raise ValueError(f"illegal business HLD execution in blocked package: {illegal}")
    invalid_engineering = find_invalid_engineering_status(package)
    if invalid_engineering:
        raise ValueError(f"invalid engineering task status: {invalid_engineering}")
    hld_skill_engineering_violations = find_hld_skill_engineering_task_violations(package)
    if hld_skill_engineering_violations:
        raise ValueError(f"HLD skill engineering task violations: {hld_skill_engineering_violations}")
    missing_refactor_file_tasks = find_missing_hld_refactor_file_tasks(package)
    if missing_refactor_file_tasks:
        raise ValueError(f"missing HLD refactor file tasks: {missing_refactor_file_tasks}")
    engineering_output_violations = find_engineering_business_output_violations(package)
    if engineering_output_violations:
        raise ValueError(f"engineering business output violations: {engineering_output_violations}")
    design_planning_violations = find_design_planning_contract_violations()
    if design_planning_violations:
        raise ValueError(f"design-planning contract violations: {design_planning_violations}")
    manifest_violations = find_manifest_status_violations(load_manifest())
    if manifest_violations:
        raise ValueError(f"manifest status violations: {manifest_violations}")


if __name__ == "__main__":
    try:
        validate()
    except ValueError as error:
        fail(str(error))
    print("PASS: design task package coverage is valid")
