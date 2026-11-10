#!/usr/bin/env python3
"""Validate the HLD workflow contract, skills, and sample artifacts."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/superpowers/specs/2026-07-07-novel-hld-contract.json"
HARNESS_SKILL = ROOT / "skills/novel-hld-workflow/SKILL.md"
LEGACY_HLD_WRITER = ROOT / "skills/novel-hld-writer/SKILL.md"
REFERENCE_PATH = ROOT / "docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md"

BUSINESS_AUTHORITY_TERMS = [
    "design world facts directly",
    "write character system directly",
    "fix event logic in package",
    "draft scene text",
    "直接设计世界规则",
    "直接设计人物系统",
    "直接修正 HLD facts",
]

PRE_RECONCILIATION_SKILLS = {
    "novel-world-rule-designer",
    "novel-character-system-designer",
    "novel-environment-system-designer",
    "novel-event-system-designer",
    "novel-time-information-system-designer",
    "novel-thread-system-designer",
    "novel-style-pov-system-designer",
}

SOURCE_REF_PATTERNS = [
    re.compile(r"^scene:PRD-S\d{2,}$"),
    re.compile(r"^freeze:PRD-FREEZE-\d{2,}$"),
    re.compile(r"^hldreq:HLD-REQ-\d{2,}$"),
    re.compile(r"^claim:CLAIM-\d{2,}$"),
    re.compile(r"^storylogic:PRD-LOGIC-\d{2,}$"),
    re.compile(r"^inventory:INV-\d{2,}$"),
]
INVENTORY_REF_PATTERN = re.compile(r"^inventory:INV-\d{2,}$")
RECONCILIATION_REQUEST_ID_PATTERN = re.compile(r"^HLD-10-\d{2,}$")
UPSTREAM_FACT_ID_PATTERN = re.compile(r"^UPF-[A-Z0-9-]+$")
UPSTREAM_FACT_SOURCE_FIELDS = {
    "Entry state",
    "Roles",
    "Environment",
    "Event",
    "Causal output",
    "Scene content",
    "Previous dependency",
    "Next pressure",
    "Indispensability proof",
}
ENVIRONMENT_STATE_CHANGE_ID_PATTERN = re.compile(r"^ENV-STATE-[A-Z0-9][A-Z0-9-]*$")
ENVIRONMENT_STATE_REALIZATION_PATTERN = re.compile(
    r"^(ENV-STATE-[A-Z0-9][A-Z0-9-]*)\s+\[([a-z]+)\]\s*:\s*(.+)$"
)
ENVIRONMENT_STATE_VALUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
ENVIRONMENT_STATE_TRANSITION_PATTERN = re.compile(
    r"^(ENV-STATE-[A-Z0-9][A-Z0-9-]*):([A-Z][A-Z0-9_]{2,63})=>([A-Z][A-Z0-9_]{2,63})$"
)
EVENT_ID_PATTERN = re.compile(r"^HLD-06-\d{2,}$")
INFO_ID_PATTERN = re.compile(r"^HLD-07-\d{2,}$")
REVEAL_PHASE_PATTERN = re.compile(r"^REVEAL-(\d{2,})$")

EXPANSION_MODES = {"explain", "constrain", "support", "sequence", "permission", "exclude", "handoff"}
VALID_PRESERVATION = {"preserved", "bounded_expansion", "blocked", "checked", "risk_reported"}
BLOCKING_VERDICT_PREFIXES = ("open:", "violation:", "blocked:", "reopen_upstream:")
RISK_SEVERITIES = {"P0", "P1", "P2", "P3"}
RISK_TRACE_COLUMNS = [
    "Risk",
    "Severity",
    "Source refs",
    "Owner artifact",
    "Rerun target",
    "Handling",
    "Blocking verdict effect",
]
HLD_FACT_TRACE_COLUMNS = [
    "Fact trace id",
    "Upstream fact id",
    "Upstream fact atom",
    "HLD fact atom",
    "Source refs",
    "Expansion mode",
    "Support mechanism",
    "Preservation status",
]
ARTIFACT_12_OUTPUT_FIELDS = {
    "Agent quality verdict",
    "HLD human review state",
    "LLD entry verdict",
}
ARTIFACT_12_OUTPUT_VALUES = {
    "Agent quality verdict": {"pass", "fail"},
    "HLD human review state": {"confirmed", "not_required", "pending_required", "reopen_hld"},
    "LLD entry verdict": {
        "pass_to_lld",
        "blocked_pending_human_review",
        "blocked_revision_required",
    },
}
VERDICT_MATRIX_COLUMNS = [
    "Verdict",
    "Required condition",
    "Actual evidence",
    "Resolved value",
    "Consistency",
]
CONVERGENCE_LOG_COLUMNS = [
    "Stable issue id",
    "Severity",
    "Root cause",
    "Fix hypothesis",
    "Regression proof",
    "Attempt count",
    "Rerun target",
    "Status",
]
CONVERGENCE_STATUSES = {"open", "fixed", "blocked", "versioned_refactor_required"}
VALID_HLD_OWNER_ARTIFACTS = {f"artifact {i:02d}" for i in range(3, 10)} | {"artifact 10"}
VALID_REQUESTING_ARTIFACTS = {"artifact 01"} | {f"artifact {i:02d}" for i in range(3, 10)}
SOURCE_MAP_DESIGN_ARTIFACTS = {
    "03": ("World rule design table", "Rule id"),
    "04": ("Character system table", "Character id"),
    "05": ("Environment system table", "Environment id"),
    "06": ("Event system table", "Event id"),
    "07": ("Time and information table", "Info id"),
    "08": ("Thread system table", "Thread id"),
    "09": ("Style and POV table", "Style/POV id"),
}
LLD_HANDOFF_INDEX_COLUMNS = [
    "LLD handoff target",
    "HLD fact id",
    "Owner artifact",
    "Final inventory id",
    "Upstream fact id",
    "Upstream fact atom",
    "HLD fact atom",
    "Source refs",
    "Handoff status",
]
CONCRETE_MOTIVE_TERMS = {
    "desire",
    "fear",
    "guilt",
    "attachment",
    "concealment",
    "self-protection",
    "ambition",
    "loyalty",
    "欲望",
    "恐惧",
    "内疚",
    "愧疚",
    "依恋",
    "隐瞒",
    "自我保护",
    "野心",
    "忠诚",
}
ABSTRACT_MOTIVE_TERMS = {
    "abstract ethics",
    "good versus evil",
    "good/evil",
    "morality",
    "theme-only",
    "抽象伦理",
    "善恶",
    "道德",
}
RELATIONSHIP_BOUND_MOTIVE_TERMS = {
    "attachment",
    "loyalty",
    "relationship",
    "protect",
    "protection",
    "conceal",
    "concealment",
    "trust",
    "distrust",
    "依恋",
    "忠诚",
    "关系",
    "保护",
    "隐瞒",
    "信任",
    "不信任",
}
DIGITAL_LIFE_TERMS = {"digital life", "digital-life", "digital_life", "数字生命"}
DIGITAL_LIFE_BOUNDARY_TERMS = {
    "not senior",
    "not the senior",
    "not resurrection",
    "distinct from senior",
    "separate from senior",
    "independent identity",
    "不是学长",
    "不是复活",
    "独立身份",
    "身份边界",
}
DIGITAL_LIFE_FORBIDDEN_BOUNDARY_TERMS = {
    "is the senior resurrected",
    "senior resurrected",
    "senior resurrection",
    "is the senior's resurrection",
    "equals the senior",
    "equal to the senior",
    "same as the senior",
    "same identity as the senior",
    "学长复活",
    "就是学长",
    "等同学长",
    "等于学长",
    "与学长同一身份",
}
INVENTORY_OWNER_BY_ENTITY_TYPE = {
    "rule": "artifact 03",
    "character": "artifact 04",
    "group": "artifact 04",
    "environment": "artifact 05",
    "event": "artifact 06",
    "information object": "artifact 07",
    "time layer": "artifact 07",
    "thread": "artifact 08",
    "style/pov rule": "artifact 09",
    "unresolved amendment": "artifact 10",
}
WORLD_RULE_TYPES = {
    "institution",
    "technology",
    "protocol",
    "legality",
    "ethics",
    "security",
    "data",
    "authority",
    "social norm",
    "physical/logistical constraint",
}
EVENT_TYPES = {"trigger", "escalation", "reversal", "revelation", "decision", "consequence"}
EVENT_VISIBILITY = {"visible", "background", "hidden", "implied"}
TIME_LAYERS = {"story_chronology", "narrative_reveal", "memory", "digital_interaction", "organizational_decision"}
DISCLOSURE_TIERS = {"operational_intelligence", "partial_cause", "complete_cause", "protected_memory", "institutional_assessment", "private_motive"}
REVEAL_CONDITION_TYPES = {"action", "permission", "access", "evidence_change"}
THREAD_TYPES = {"main", "hidden", "emotional", "theme", "institutional", "identity", "support"}
REQUIRED_CORE_THREAD_TYPES = {"main", "hidden", "emotional", "theme", "institutional", "identity"}
CORE_THREAD_FUNCTION_BY_TYPE = {
    "main": "advance_crisis_resolution",
    "hidden": "withhold_then_reframe_cause",
    "emotional": "convert_private_relation_to_cost",
    "theme": "test_value_through_choice",
    "institutional": "apply_systemic_pressure",
    "identity": "separate_digital_life_from_human_memory",
}
THREAD_CLOSURE_STATES = {"closed", "deliberately unresolved", "transferred_to_lld", "blocked"}
STYLE_POV_RULE_TYPES = {
    "pov",
    "narrative distance",
    "information access",
    "digital-life interiority",
    "dialogue",
    "image system",
    "prohibited expression",
    "language style",
}
STYLE_ACCESS_POLICY_BY_RULE_TYPE = {
    "pov": "limited_focalization",
    "narrative distance": "controlled_distance",
    "information access": "reveal_gated",
    "digital-life interiority": "no_direct_interior",
    "dialogue": "mediated_dialogue",
    "image system": "bounded_image_system",
    "prohibited expression": "hard_prohibition",
    "language style": "controlled_register",
}
STYLE_READER_DISCLOSURE_MODE_BY_RULE_TYPE = {
    "pov": "external_inference",
    "narrative distance": "external_inference",
    "information access": "reveal_at_information_gate",
    "digital-life interiority": "external_inference",
    "dialogue": "external_inference",
    "image system": "external_inference",
    "prohibited expression": "external_inference",
    "language style": "external_inference",
}
STYLE_EXECUTION_CONSTRAINT_KEYS = {
    "Design fact": {"rule", "scope", "effect"},
    "POV permission": {"focalizer", "permitted", "evidence"},
    "Prohibited expression": {"forbidden", "target", "trigger"},
}
LANGUAGE_PROFILE_DIRECTIVE_KEYS = {
    "register": {"mode", "limit"},
    "syntax": {"sentence", "variation"},
    "diction": {"prefer", "avoid"},
    "rhythm": {"pace", "shift"},
}
STYLE_EXECUTION_MARKERS_BY_RULE_TYPE = {
    "pov": {
        "Design fact": {"focal", "filter", "视角", "限知"},
        "POV permission": {"observ", "观察", "可见"},
        "Prohibited expression": {"interior", "omni", "unrestricted", "内心", "全知"},
    },
    "narrative distance": {
        "Design fact": {"distance", "uncertainty", "距离", "不确定"},
        "POV permission": {"observ", "观察", "距离"},
        "Prohibited expression": {"inference", "certainty", "推断", "确定"},
    },
    "information access": {
        "Design fact": {"reveal", "gate", "揭示", "门"},
        "POV permission": {"reveal", "disclose", "揭示", "披露"},
        "Prohibited expression": {"early", "pre-gate", "提前", "门前"},
    },
    "digital-life interiority": {
        "Design fact": {"agency", "mediate", "interior", "中介", "意识"},
        "POV permission": {"agency", "dialogue", "行为", "对话"},
        "Prohibited expression": {"interior", "thought", "内心", "意识"},
    },
    "dialogue": {
        "Design fact": {"dialogue", "对话"},
        "POV permission": {"dialogue", "exchange", "对话"},
        "Prohibited expression": {"dialogue", "motive", "对话", "动机"},
    },
    "image system": {
        "Design fact": {"image", "imag", "意象", "图像"},
        "POV permission": {"image", "containment", "意象", "图像"},
        "Prohibited expression": {"image", "omni", "意象", "图像", "全知"},
    },
    "prohibited expression": {
        "Design fact": {"identity", "memory", "身份", "记忆"},
        "POV permission": {"identity", "evidence", "身份", "证据"},
        "Prohibited expression": {"resurrect", "identity", "复活", "身份"},
    },
    "language style": {
        "Design fact": {"register", "restrain", "language", "语体", "语言", "克制"},
        "POV permission": {"register", "restrain", "wording", "语体", "措辞", "克制"},
        "Prohibited expression": {"lyric", "melodram", "language", "抒情", "煽情", "语言"},
    },
}
VAGUE_STYLE_TERMS = {
    "appropriate",
    "beautiful",
    "generic",
    "good",
    "natural",
    "pleasing",
    "proper",
    "suitable",
    "不够好",
    "优美",
    "合适",
    "好看",
    "很好",
    "恰当",
    "整体",
    "满意",
    "所需",
    "自然",
    "适当",
}
ENVIRONMENT_STATE_CHANGE_DIMENSIONS = {
    "access",
    "evidence",
    "pressure",
    "safety",
    "visibility",
    "containment",
}
ENTITY_TYPES = {
    "character",
    "group",
    "environment",
    "event",
    "rule",
    "information object",
    "time layer",
    "thread",
    "style/pov rule",
    "unresolved amendment",
}
INVENTORY_INITIAL_STATUSES = {"active"}
RECONCILIATION_DECISIONS = {"accept", "reject", "merge", "reopen_upstream", "blocked_unresolved"}
RUBRIC_COVERAGE_COLUMNS = [
    "Artifact",
    "Good delivery evidence",
    "Blocking failure check",
    "Coverage verdict",
]
ENVIRONMENT_CLOSURE_CHECK_COLUMNS = [
    "Environment id",
    "Inventory id",
    "State change id",
    "State change dimension",
    "State before",
    "State after",
    "Event ids",
    "Event state transition refs",
    "Event state realization refs",
    "Source Map HLD fact id",
    "Evidence",
    "Verdict",
]
EVENT_CLOSURE_CHECK_COLUMNS = [
    "Event id",
    "Inventory id",
    "Cause refs",
    "Event action",
    "Causal role",
    "Consequences",
    "Environment state change refs",
    "Event fact id",
    "Event closure evidence",
    "Verdict",
]
INFORMATION_CLOSURE_CHECK_COLUMNS = [
    "Info id",
    "Inventory id",
    "PRD information boundary id",
    "Freeze refs",
    "Story anchor event ref",
    "Time layer",
    "Narrative reveal phase",
    "Disclosure tier",
    "Known by",
    "Hidden from",
    "Reveal predecessor refs",
    "Reveal event ref",
    "Reveal action",
    "Reveal condition type",
    "Reveal condition refs",
    "Reveal condition",
    "Information fact id",
    "Information closure evidence",
    "Verdict",
]
RECONCILIATION_CLOSURE_CHECK_COLUMNS = [
    "Initial inventory id",
    "Request id",
    "Decision",
    "Canonical subject id",
    "Final inventory id",
    "Origin artifact",
    "Origin source refs",
    "Origin fact trace id",
    "Evidence",
    "Verdict",
]
THREAD_CLOSURE_CHECK_COLUMNS = [
    "Thread id",
    "Thread type",
    "Thread function",
    "Thread anchor refs",
    "Required pressure refs",
    "Thread progression",
    "Crossover",
    "Closure outcome",
    "Evidence",
    "Verdict",
]
STYLE_POV_CLOSURE_CHECK_COLUMNS = [
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
    "Verdict",
]

FACT_ATOM_COLUMNS_BY_HEADING = {
    "Initial world entity inventory": [
        "Entity type",
        "Entity name",
        "Required HLD owner",
        "Secondary HLD owners",
        "Upstream evidence",
        "Initial status",
    ],
    "PRD support matrix": [
        "Supports",
        "Support type",
        "Required HLD owner",
        "Inventory obligations",
        "Required answer",
        "Boundary",
        "Support status",
    ],
    "World rule design table": [
        "Rule type",
        "Design fact",
        "Supports",
        "Boundary",
        "LLD handoff",
        "Amendment request",
    ],
    "Character system table": [
        "Inventory id",
        "Entity type",
        "Entity name",
        "Role type",
        "Function",
        "Relationship/motivation",
        "Relationship targets",
        "Concrete motive evidence",
        "Information permission",
        "Identity boundary",
        "Supports",
        "LLD handoff",
        "Amendment request",
    ],
    "Environment system table": [
        "Inventory id",
        "Entity type",
        "Entity name",
        "Environment type",
        "Function",
        "Spatial relation",
        "State change id",
        "State change dimension",
        "State before",
        "State after",
        "State change",
        "Supports",
        "LLD handoff",
        "Amendment request",
    ],
    "Event system table": [
        "Inventory id",
        "Entity type",
        "Entity name",
        "Cause refs",
        "Event action",
        "Causal role",
        "Visibility",
        "Participants",
        "Environment refs",
        "Environment state change refs",
        "Environment state transitions",
        "Environment state realizations",
        "Consequences",
        "Supports",
        "LLD handoff",
        "Amendment request",
    ],
    "Time and information table": [
        "Inventory id", "Entity type", "Entity name", "PRD information boundary id", "Freeze refs", "Story anchor event ref", "Time layer",
        "Narrative reveal phase", "Disclosure tier", "Information object", "Known by", "Hidden from",
        "Reveal predecessor refs", "Reveal event ref", "Reveal action", "Reveal condition type",
        "Reveal condition refs", "Reveal condition", "Supports", "LLD handoff", "Amendment request",
    ],
    "Thread system table": ["Thread function", "Thread anchor refs", "Required pressure refs", "Core question", "Node distribution", "Thread progression", "Crossover", "Closure state", "Closure outcome"],
    "Style and POV table": ["Rule type", "Access policy", "Information refs", "Thread refs", "Reader disclosure mode", "Language profile", "Design fact", "POV permission", "Prohibited expression", "LLD handoff"],
    "Final inventory reconciliation table": ["Entity name", "Decision", "Canonical subject id", "Final inventory id", "Reason"],
    "HLD Source Map": ["HLD fact atom"],
}

SUPPORT_CONSUMER_HEADINGS = {
    "artifact 03": "World rule design table",
    "artifact 04": "Character system table",
    "artifact 05": "Environment system table",
    "artifact 06": "Event system table",
    "artifact 07": "Time and information table",
    "artifact 08": "Thread system table",
    "artifact 09": "Style and POV table",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing file: {rel(path)}")


def markdown_section_text(text: str, heading: str) -> str:
    match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not match:
        raise ValueError(f"missing heading: {heading}")
    section = text[match.end():]
    next_heading = re.search(r"^##+\s+", section, re.M)
    return section[:next_heading.start()] if next_heading else section


def load_hld_contract() -> dict:
    return json.loads(read(CONTRACT_PATH))


def require_terms(label: str, text: str, terms: list[str]) -> None:
    missing = [term for term in terms if term not in text]
    if missing:
        raise ValueError(f"{label} missing required terms: {missing}")


def validate_contract_rule_coverage(contract: dict) -> None:
    rule_ids = {rule["id"] for rule in contract.get("contract_rules", [])}
    coverage = contract.get("rule_coverage")
    if not isinstance(coverage, dict):
        raise ValueError("HLD contract missing rule_coverage")
    missing = rule_ids - set(coverage)
    extra = set(coverage) - rule_ids
    if missing:
        raise ValueError(f"HLD contract missing rule coverage: {sorted(missing)}")
    if extra:
        raise ValueError(f"HLD contract has unknown rule coverage: {sorted(extra)}")
    test_text = read(ROOT / "tests/test_validate_hld_contract.py")
    for rule_id, entry in coverage.items():
        validators = entry.get("validators")
        tests = entry.get("tests")
        if not validators or not tests:
            raise ValueError(f"{rule_id} must declare validators and tests")
        unknown_validators = [name for name in validators if not callable(globals().get(name))]
        if unknown_validators:
            raise ValueError(f"{rule_id} unknown validators: {unknown_validators}")
        unknown_tests = [name for name in tests if f"def {name}(" not in test_text]
        if unknown_tests:
            raise ValueError(f"{rule_id} unknown tests: {unknown_tests}")


def validate_artifact_dag(contract: dict) -> None:
    graph = contract.get("artifacts", [])
    if not graph:
        raise ValueError("HLD contract artifacts must be non-empty")
    nodes = {artifact["id"]: artifact for artifact in graph}
    for artifact in graph:
        for dep in artifact.get("depends_on", []):
            if dep not in nodes:
                raise ValueError(f"artifact {artifact['id']} depends on unknown artifact {dep}")
    if "12" in nodes["11"].get("depends_on", []):
        raise ValueError("artifact 11 must not depend on artifact 12")
    if set(nodes["final-hld-package"].get("depends_on", [])) != {"11", "12"}:
        raise ValueError("final-hld-package must depend exactly on artifacts 11 and 12")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: list[str]) -> None:
        if node_id in visiting:
            raise ValueError(f"HLD artifact DAG contains cycle: {' -> '.join(path + [node_id])}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in nodes[node_id].get("depends_on", []):
            visit(dep, path + [node_id])
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in nodes:
        visit(node_id, [])


def validate_required_skill_files(contract: dict) -> None:
    read(HARNESS_SKILL)
    for artifact in contract["artifacts"]:
        skill = artifact.get("skill")
        if skill:
            read(ROOT / "skills" / skill / "SKILL.md")


def validate_artifact_schemas(contract: dict) -> None:
    for artifact in contract["artifacts"]:
        skill = artifact.get("skill")
        if not skill:
            continue
        text = read(ROOT / "skills" / skill / "SKILL.md")
        for section in artifact.get("sections", [artifact.get("section")]):
            if section and f"## {section}" not in text and f"`## {section}`" not in text:
                raise ValueError(f"{skill} missing required section: {section}")
        for column in artifact.get("columns", []):
            if column not in text:
                raise ValueError(f"{skill} missing required column: {column}")
        handoff_section = artifact.get("handoff_section")
        if handoff_section and f"## {handoff_section}" not in text and f"`## {handoff_section}`" not in text:
            raise ValueError(f"{skill} missing required section: {handoff_section}")
        for column in artifact.get("handoff_columns", []):
            if column not in text:
                raise ValueError(f"{skill} missing required handoff column: {column}")


def validate_skill_contract_text(contract: dict) -> None:
    required_sections = [
        "## Responsibility",
        "## Inputs",
        "## Output Artifact",
        "## SOP",
        "## Boundary",
        "## Rules",
        "## References",
        "## Traceability",
        "## Acceptance",
        "## Skill Verdict",
    ]
    for artifact in contract["artifacts"]:
        skill = artifact.get("skill")
        if not skill:
            continue
        text = read(ROOT / "skills" / skill / "SKILL.md")
        require_terms(skill, text, required_sections)
        require_terms(skill, text, contract["skill_verdict_fields"])
        require_terms(skill, text, contract["artifact_metadata_fields"])
        require_terms(skill, text, contract["fact_trace_fields"])
        if "Artifact Metadata" not in text:
            raise ValueError(f"{skill} must require Artifact Metadata")
        if "HLD Fact Trace" not in text:
            raise ValueError(f"{skill} must require HLD Fact Trace")
        if skill == "novel-character-system-designer":
            validate_character_relationship_bound_terms_match_skill(text)
            validate_character_skill_reference_quality(text)
        if skill == "novel-environment-system-designer":
            validate_environment_skill_reference_quality(text)
        if skill == "novel-event-system-designer":
            validate_event_skill_reference_quality(text)
        if skill == "novel-hld-integrity-checker":
            validate_hld_integrity_environment_rule_terms(text)
            validate_hld_integrity_event_rule_terms(text)
            validate_hld_integrity_information_rule_terms(text)
            validate_hld_integrity_integrator_rule_terms(text)


def validate_character_relationship_bound_terms_match_skill(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-character-system-designer/SKILL.md")
    require_terms(
        "novel-character-system-designer relationship-bound motive terms",
        skill_text,
        ["relationship-bound motive terms"] + sorted(RELATIONSHIP_BOUND_MOTIVE_TERMS),
    )


def validate_character_skill_reference_quality(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-character-system-designer/SKILL.md")
    if "## References" not in skill_text or "## Traceability" not in skill_text:
        raise ValueError("novel-character-system-designer missing References or Traceability section")
    references = skill_text.split("## References", 1)[1].split("## Traceability", 1)[0]
    require_terms(
        "novel-character-system-designer References",
        references,
        [
            "Good delivery standards",
            "Blocking anti-patterns",
            "narrative function",
            "human pressure",
            "relationship target closure",
            "information permission",
            "identity boundary",
            "LLD handoff",
            "source-backed",
        ],
    )


def validate_environment_skill_reference_quality(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-environment-system-designer/SKILL.md")
    if "## References" not in skill_text or "## Traceability" not in skill_text:
        raise ValueError("novel-environment-system-designer missing References or Traceability section")
    references = skill_text.split("## References", 1)[1].split("## Traceability", 1)[0]
    require_terms(
        "novel-environment-system-designer References",
        references,
        [
            "Good delivery standards",
            "Blocking anti-patterns",
            "spatial function",
            "spatial relation",
            "state change",
            "access",
            "evidence",
            "pressure",
            "safety",
            "LLD handoff",
            "source-backed",
        ],
    )


def validate_event_skill_reference_quality(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-event-system-designer/SKILL.md")
    if "## References" not in skill_text or "## Traceability" not in skill_text:
        raise ValueError("novel-event-system-designer missing References or Traceability section")
    references = skill_text.split("## References", 1)[1].split("## Traceability", 1)[0]
    require_terms(
        "novel-event-system-designer References",
        references.casefold(),
        [
            "good delivery standards",
            "blocking anti-patterns",
            "causal chain",
            "event action",
            "trigger closure",
            "consequence",
            "visibility",
            "lld handoff",
            "source-backed",
        ],
    )


def validate_hld_integrity_environment_rule_terms(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    require_terms(
        "novel-hld-integrity-checker Artifact 05 rubric terms",
        markdown_section_text(skill_text, "Rules"),
        ["state-change dimension", "state transition", "event state realization"],
    )


def validate_hld_integrity_event_rule_terms(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    require_terms(
        "novel-hld-integrity-checker Artifact 06 rubric terms",
        markdown_section_text(skill_text, "Rules"),
        ["event inventory coverage", "causal-chain closure", "concrete event action", "consequence"],
    )


def validate_hld_integrity_information_rule_terms(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    require_terms(
        "novel-hld-integrity-checker Artifact 07 rubric terms",
        markdown_section_text(skill_text, "Rules"),
        [
            "information inventory coverage",
            "story anchor",
            "time layer",
            "narrative reveal phase",
            "reveal predecessor",
            "disclosure tier",
            "knowledge state",
            "reveal event/action",
            "condition type/refs",
            "Source Map trace closure",
        ],
    )


def validate_hld_integrity_integrator_rule_terms(text: str | None = None) -> None:
    skill_text = text if text is not None else read(ROOT / "skills/novel-hld-integrity-checker/SKILL.md")
    require_terms(
        "novel-hld-integrity-checker Artifact 11 rubric terms",
        markdown_section_text(skill_text, "Rules"),
        ["fact-level Source Map closure", "artifact 03-09", "LLD handoff-index closure", "ready"],
    )


def validate_harness_boundary(contract: dict) -> None:
    text = read(HARNESS_SKILL)
    require_terms(
        "novel-hld-workflow",
        text,
        [
            "pure harness",
            "HLD entry verdict = pass_to_hld",
            "blocked_pending_human_review",
            "blocked_revision_required",
            "Dispatch DAG",
            "final-hld-package",
            "must not write HLD business facts",
            "artifact 11",
            "artifact 12",
        ],
    )
    for term in BUSINESS_AUTHORITY_TERMS:
        if term in text:
            raise ValueError(f"novel-hld-workflow contains forbidden business authority term: {term}")


def validate_harness_routing_rules(contract: dict) -> None:
    text = read(HARNESS_SKILL)
    require_terms(
        "novel-hld-workflow Routing Rules",
        text,
        [
            "Artifact rubric coverage",
            "HLD-CONTRACT-13",
            "upstream source inventory",
            "upstream source coverage",
            "validate_upstream_source_coverage",
            "validate_hld_business_rules",
        ],
    )


def validate_release_preflight_contract(contract: dict) -> None:
    workflow_text = read(HARNESS_SKILL)
    release_validator_text = read(ROOT / "scripts/validate_hld_release.py")
    require_terms(
        "novel-hld-workflow Release Preflight",
        workflow_text,
        [
            "Release Preflight",
            "HLD-CONTRACT-18",
            "validate_hld_release.py",
            "Release Artifact Index",
            "committed Git snapshot",
            "release-ready",
        ],
    )
    require_terms(
        "validate_hld_release",
        release_validator_text,
        [
            "validate_release_snapshot_assets",
            "Release Artifact Index",
            "validate_release_output",
            "release_required_assets",
        ],
    )


def validate_prd_gate_terms(contract: dict) -> None:
    text = read(HARNESS_SKILL)
    require_terms(
        "novel-hld-workflow PRD gate",
        text,
        [
            "If PRD gate is blocked, emit only manifest and gate report",
            "No artifacts 01-12",
            "HLD entry verdict = pass_to_hld",
            "validate_prd_contract.py",
            "authenticated registered PRD package",
        ],
    )


def validate_source_grammar_and_expansion_modes(contract: dict) -> None:
    if set(contract.get("source_ref_prefixes", [])) != {"scene", "freeze", "hldreq", "claim", "storylogic", "inventory"}:
        raise ValueError("HLD source_ref_prefixes are incomplete")
    if set(contract.get("expansion_modes", [])) != {"explain", "constrain", "support", "sequence", "permission", "exclude", "handoff"}:
        raise ValueError("HLD expansion modes are incomplete")


def split_source_refs(value: str) -> list[str]:
    refs = [part.strip() for part in re.split(r"[,;，；]\s*", value.strip()) if part.strip()]
    if not refs:
        raise ValueError("source refs must not be empty")
    return refs


def validate_source_ref_values(value: str) -> None:
    for ref in split_source_refs(value):
        if not any(pattern.fullmatch(ref) for pattern in SOURCE_REF_PATTERNS):
            raise ValueError(f"invalid source ref: {ref}")


def validate_inventory_ref_value(
    value: str,
    label: str = "Final inventory id",
    *,
    allow_none: bool = False,
) -> None:
    if is_none_value(value):
        if allow_none:
            return
        raise ValueError(f"{label} must not be empty")
    if len(split_list_refs(value)) != 1:
        raise ValueError(f"exactly one final inventory id is required: {value}")
    if not INVENTORY_REF_PATTERN.fullmatch(value.strip()):
        raise ValueError(f"invalid {label}: {value}")


def validate_reconciliation_amendment_trace(
    origin_trace: dict[str, str],
    reconciliation_trace: dict[str, str],
    amendment_id: str,
) -> None:
    if (
        reconciliation_trace["Upstream fact id"] != origin_trace["Upstream fact id"]
        or normalize_fact_text(reconciliation_trace["Upstream fact atom"])
        != normalize_fact_text(origin_trace["Upstream fact atom"])
        or set(split_source_refs(reconciliation_trace["Source refs"]))
        != set(split_source_refs(origin_trace["Source refs"]))
    ):
        raise ValueError(f"reconciliation amendment fact trace mismatch: {amendment_id}")


def canonical_source_refs(value: str) -> str:
    refs = split_source_refs(value)
    validate_source_ref_values(value)
    return ",".join(sorted(set(refs)))


def source_refs_in_text(text: str) -> set[str]:
    refs: set[str] = set()
    refs.update(re.findall(r"scene:PRD-S\d{2,}", text))
    refs.update(re.findall(r"freeze:PRD-FREEZE-\d{2,}", text))
    refs.update(re.findall(r"hldreq:HLD-REQ-\d{2,}", text))
    refs.update(re.findall(r"claim:CLAIM-\d{2,}", text))
    refs.update(re.findall(r"storylogic:PRD-LOGIC-\d{2,}", text))
    refs.update(f"scene:{value}" for value in re.findall(r"(?<![A-Z0-9-])PRD-S\d{2,}", text))
    refs.update(f"freeze:{value}" for value in re.findall(r"(?<![A-Z0-9-])PRD-FREEZE-\d{2,}", text))
    refs.update(f"hldreq:{value}" for value in re.findall(r"(?<![A-Z0-9-])HLD-REQ-\d{2,}", text))
    refs.update(f"claim:{value}" for value in re.findall(r"(?<![A-Z0-9-])CLAIM-\d{2,}", text))
    refs.update(f"storylogic:{value}" for value in re.findall(r"(?<![A-Z0-9-])PRD-LOGIC-\d{2,}", text))
    return {ref for ref in refs if not ref.startswith("inventory:")}


def extract_required_upstream_source_refs(upstream_text: str | list[str]) -> set[str]:
    texts = upstream_text if isinstance(upstream_text, list) else [upstream_text]
    refs: set[str] = set()
    for text in texts:
        refs.update(source_refs_in_text(text))
    if not refs:
        raise ValueError("upstream source inventory is empty")
    return refs


UPSTREAM_INFORMATION_BOUNDARY_COLUMNS = [
    "Information boundary id",
    "Story anchor scene id",
    "Narrative reveal scene id",
    "Narrative reveal order",
    "Disclosure tier",
    "Information object",
    "Reader access",
    "Known by entity refs",
    "Hidden from entity refs",
    "Reveal predecessor boundary refs",
    "Reveal condition type",
    "Freeze refs",
    "Source",
    "HLD obligation",
]
AUTHENTICATED_PRD_BOUNDARY_SOURCE_KEYS = {
    "artifact_05",
    "artifact_08",
    "final_prd_package",
}


def extract_upstream_information_boundaries(upstream_text: str | list[str]) -> dict[str, dict[str, str]]:
    texts = upstream_text if isinstance(upstream_text, list) else [upstream_text]
    boundaries: dict[str, dict[str, str]] = {}
    found_table = False
    for text in texts:
        if not re.search(r"^##+\s+HLD information boundary table\s*$", text, re.M):
            continue
        found_table = True
        rows = parse_rows(text, "HLD information boundary table")
        missing_columns = set(UPSTREAM_INFORMATION_BOUNDARY_COLUMNS) - set(rows[0])
        if missing_columns:
            raise ValueError(f"upstream information boundary table missing columns: {sorted(missing_columns)}")
        for row in rows:
            boundary_id = row["Information boundary id"]
            if not re.fullmatch(r"PRD-INFO-\d{2,}", boundary_id) or boundary_id in boundaries:
                raise ValueError(f"invalid or duplicate upstream information boundary id: {boundary_id}")
            for scene_column in ["Story anchor scene id", "Narrative reveal scene id"]:
                if not re.fullmatch(r"PRD-S\d{2,}", row[scene_column]):
                    raise ValueError(f"invalid upstream information boundary scene: {boundary_id} {scene_column}")
            if not row["Narrative reveal order"].isdigit() or int(row["Narrative reveal order"]) < 1:
                raise ValueError(f"invalid upstream information boundary reveal order: {boundary_id}")
            if row["Disclosure tier"] not in DISCLOSURE_TIERS:
                raise ValueError(f"invalid upstream information boundary disclosure tier: {boundary_id}")
            if row["Reader access"] not in {"visible", "concealed"}:
                raise ValueError(f"invalid upstream information boundary reader access: {boundary_id}")
            if row["Reveal condition type"] not in REVEAL_CONDITION_TYPES:
                raise ValueError(f"invalid upstream information boundary condition type: {boundary_id}")
            validate_source_ref_values(row["Freeze refs"])
            if any(not ref.startswith("freeze:") for ref in split_source_refs(row["Freeze refs"])):
                raise ValueError(f"invalid upstream information boundary freeze refs: {boundary_id}")
            validate_source_ref_values(row["Source"])
            boundaries[boundary_id] = row
    if not found_table:
        raise ValueError("missing mandatory HLD information boundary table")
    return boundaries


def authenticated_prd_information_boundary_text(boundary_sources: dict[str, str] | None) -> str:
    if not boundary_sources or set(boundary_sources) != AUTHENTICATED_PRD_BOUNDARY_SOURCE_KEYS:
        raise ValueError("authenticated PRD information-boundary sources required")
    canonical = markdown_section_text(
        boundary_sources["artifact_05"],
        "HLD information boundary table",
    ).strip()
    for source_key in ["artifact_08", "final_prd_package"]:
        candidate = markdown_section_text(
            boundary_sources[source_key],
            "HLD information boundary table",
        ).strip()
        if candidate != canonical:
            raise ValueError(f"authenticated PRD information-boundary drift: {source_key}")
    return f"## HLD information boundary table\n\n{canonical}\n"


def validate_upstream_information_boundary_alignment(
    upstream_text: str | list[str],
    artifact_texts: dict[str, str],
) -> None:
    boundaries = extract_upstream_information_boundaries(upstream_text)
    information = parse_rows(artifact_texts["07"], "Time and information table")
    information_by_boundary_id = {row["PRD information boundary id"]: row for row in information}
    if set(information_by_boundary_id) != set(boundaries):
        raise ValueError("HLD information boundary coverage mismatch")
    events = {row["Event id"]: row for row in parse_rows(artifact_texts["06"], "Event system table")}
    characters = {row["Character id"]: row for row in parse_rows(artifact_texts["04"], "Character system table")}

    def normalized_knowledge_refs(value: str, boundary_id: str) -> set[str]:
        refs: set[str] = set()
        for ref in split_list_refs(value):
            if ref == "reader":
                refs.add(ref)
            elif ref in characters:
                refs.add(f"entity:{characters[ref]['Entity name']}")
            else:
                raise ValueError(f"HLD information boundary unresolved knowledge holder: {boundary_id} {ref}")
        return refs

    for boundary_id, boundary in boundaries.items():
        row = information_by_boundary_id[boundary_id]
        if normalize_fact_text(row["Information object"]) != normalize_fact_text(boundary["Information object"]):
            raise ValueError(f"HLD information boundary object mismatch: {boundary_id}")
        for column in ["Disclosure tier", "Reveal condition type", "Freeze refs", "Source"]:
            if row[column] != boundary[column]:
                raise ValueError(f"HLD information boundary {column.casefold()} mismatch: {boundary_id}")
        for event_column, scene_column in [
            ("Story anchor event ref", "Story anchor scene id"),
            ("Reveal event ref", "Narrative reveal scene id"),
        ]:
            event = events[row[event_column]]
            if f"scene:{boundary[scene_column]}" not in split_source_refs(event["Source"]):
                raise ValueError(f"HLD information boundary event source mismatch: {boundary_id} {event_column}")
        known_by = normalized_knowledge_refs(row["Known by"], boundary_id)
        hidden_from = normalized_knowledge_refs(row["Hidden from"], boundary_id)
        expected_known_by = set(split_list_refs(boundary["Known by entity refs"]))
        expected_hidden_from = set(split_list_refs(boundary["Hidden from entity refs"]))
        if known_by != expected_known_by or hidden_from != expected_hidden_from:
            raise ValueError(f"HLD information boundary knowledge state mismatch: {boundary_id}")
        if boundary["Reader access"] == "visible" and "reader" not in known_by:
            raise ValueError(f"HLD information boundary reader visibility mismatch: {boundary_id}")
        if boundary["Reader access"] == "concealed" and "reader" not in hidden_from:
            raise ValueError(f"HLD information boundary reader concealment mismatch: {boundary_id}")
        expected_predecessors = [] if is_none_value(boundary["Reveal predecessor boundary refs"]) else split_list_refs(boundary["Reveal predecessor boundary refs"])
        actual_predecessors = [
            information_by_boundary_id[info_row["PRD information boundary id"]]["PRD information boundary id"]
            for predecessor_id in ([] if is_none_value(row["Reveal predecessor refs"]) else split_list_refs(row["Reveal predecessor refs"]))
            for info_row in [next(candidate for candidate in information if candidate["Info id"] == predecessor_id)]
        ]
        if set(actual_predecessors) != set(expected_predecessors):
            raise ValueError(f"HLD information boundary predecessor mismatch: {boundary_id}")
    for left_id, left_boundary in boundaries.items():
        for right_id, right_boundary in boundaries.items():
            if int(left_boundary["Narrative reveal order"]) >= int(right_boundary["Narrative reveal order"]):
                continue
            if reveal_phase_number(information_by_boundary_id[left_id]["Narrative reveal phase"]) >= reveal_phase_number(information_by_boundary_id[right_id]["Narrative reveal phase"]):
                raise ValueError(f"HLD information boundary reveal order mismatch: {left_id} {right_id}")


def artifact_source_refs(artifact_text: str, heading: str) -> set[str]:
    refs: set[str] = set()
    for row in parse_rows(artifact_text, heading):
        for column in ["Source", "Source refs"]:
            if column in row and not is_none_value(row[column]):
                validate_source_ref_values(row[column])
                refs.update(split_source_refs(row[column]))
    return {ref for ref in refs if not ref.startswith("inventory:")}


def extract_required_upstream_entities(upstream_text: str | list[str]) -> list[dict[str, str]]:
    texts = upstream_text if isinstance(upstream_text, list) else [upstream_text]
    required_entities: list[dict[str, str]] = []
    required_columns = [
        "Upstream fact id",
        "Source fact field",
        "Upstream fact atom",
        "Required HLD entity",
        "Required entity type",
        "Source refs",
    ]
    found_table = False
    for text in texts:
        if not re.search(r"^##+\s+Upstream required HLD entities\s*$", text, re.M):
            continue
        found_table = True
        rows = parse_rows(text, "Upstream required HLD entities")
        observed = set(rows[0]) if rows else set()
        missing = [column for column in required_columns if column not in observed]
        if missing:
            raise ValueError(f"Upstream required HLD entities missing required columns: {missing}")
        for row in rows:
            upstream_fact_id = row["Upstream fact id"]
            if not UPSTREAM_FACT_ID_PATTERN.fullmatch(upstream_fact_id):
                raise ValueError(f"invalid upstream required entity fact id: {upstream_fact_id}")
            entity_type = row["Required entity type"]
            if entity_type not in ENTITY_TYPES:
                raise ValueError(f"invalid upstream required entity type: {entity_type}")
            if not row["Required HLD entity"].strip():
                raise ValueError("upstream required entity name must not be empty")
            if row["Source fact field"] not in UPSTREAM_FACT_SOURCE_FIELDS:
                raise ValueError(
                    f"invalid upstream required entity Source fact field: {row['Source fact field']}"
                )
            validate_source_ref_values(row["Source refs"])
            required_entities.append(row)
    if not found_table:
        raise ValueError("missing mandatory Upstream required HLD entities table")
    return required_entities


def validate_upstream_source_coverage(upstream_text: str | list[str], artifact_texts: dict[str, str]) -> None:
    required_refs = extract_required_upstream_source_refs(upstream_text)
    upstream_texts = upstream_text if isinstance(upstream_text, list) else [upstream_text]
    if any(re.search(r"^##+\s+HLD information boundary table\s*$", text, re.M) for text in upstream_texts):
        for boundary in extract_upstream_information_boundaries(upstream_text).values():
            required_refs -= set(split_source_refs(boundary["Freeze refs"]))
    artifact_01_refs = artifact_source_refs(artifact_texts["01"], "Initial world entity inventory")
    artifact_02_refs = artifact_source_refs(artifact_texts["02"], "PRD support matrix")
    missing_01 = sorted(required_refs - artifact_01_refs)
    missing_02 = sorted(required_refs - artifact_02_refs)
    if missing_01:
        raise ValueError(f"artifact 01 missing upstream source coverage: {missing_01}")
    if missing_02:
        raise ValueError(f"artifact 02 missing upstream source coverage: {missing_02}")
    required_entities = extract_required_upstream_entities(upstream_text)
    if not required_entities:
        return
    inventory_rows = parse_rows(artifact_texts["01"], "Initial world entity inventory")
    trace_rows = parse_rows(artifact_texts["01"], "HLD Fact Trace")
    trace_by_inventory_id = {row["Fact trace id"]: row for row in trace_rows if row.get("Fact trace id")}
    covered_keys: set[tuple[str, str, str, str, str]] = set()
    covered_identity_keys: set[tuple[str, str, str, str]] = set()
    for row in inventory_rows:
        trace = trace_by_inventory_id.get(row["Inventory id"], {})
        for source_ref in split_source_refs(row["Source"]):
            identity_key = (
                trace.get("Upstream fact id", ""),
                normalize_fact_text(row["Entity name"]),
                row["Entity type"],
                source_ref,
            )
            covered_identity_keys.add(identity_key)
            covered_keys.add((
                trace.get("Upstream fact id", ""),
                normalize_fact_text(trace.get("Upstream fact atom", "")),
                normalize_fact_text(row["Entity name"]),
                row["Entity type"],
                source_ref,
            ))
    missing_entities = []
    atom_mismatches = []
    for required in required_entities:
        for ref in split_source_refs(required["Source refs"]):
            identity_key = (
                required["Upstream fact id"],
                normalize_fact_text(required["Required HLD entity"]),
                required["Required entity type"],
                ref,
            )
            covered_key = (
                required["Upstream fact id"],
                normalize_fact_text(required["Upstream fact atom"]),
                normalize_fact_text(required["Required HLD entity"]),
                required["Required entity type"],
                ref,
            )
            if covered_key in covered_keys:
                continue
            if identity_key in covered_identity_keys:
                atom_mismatches.append(
                    f"{required['Upstream fact id']}:{required['Required HLD entity']}:{ref}"
                )
            else:
                missing_entities.append(
                    f"{required['Upstream fact id']}:{required['Required HLD entity']}:{ref}"
                )
    if atom_mismatches:
        raise ValueError(f"artifact 01 upstream fact atom mismatch: {sorted(atom_mismatches)}")
    if missing_entities:
        raise ValueError(f"artifact 01 missing required upstream entity coverage: {missing_entities}")


def validate_hld_owner_list(value: str, label: str) -> None:
    if is_none_value(value):
        return
    for owner in split_list_refs(value):
        if owner not in VALID_HLD_OWNER_ARTIFACTS:
            raise ValueError(f"invalid {label}: {owner}")


def inventory_amendment_id(status: str) -> str | None:
    if not status.startswith("amendment_needed:"):
        return None
    match = re.fullmatch(r"amendment_needed:(HLD-AMEND-\d{2,}):.+", status)
    if not match:
        raise ValueError(f"unrouteable inventory amendment: {status}")
    return match.group(1)


def validate_inventory_initial_status(status: str) -> None:
    if status.startswith("amendment_needed:"):
        inventory_amendment_id(status)
        return
    if status not in INVENTORY_INITIAL_STATUSES:
        raise ValueError(f"invalid Initial status: {status}")


def normalize_fact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("`")).casefold()


def validate_inventory_id_timing(contract: dict) -> None:
    for skill in PRE_RECONCILIATION_SKILLS:
        text = read(ROOT / "skills" / skill / "SKILL.md")
        if "final inventory id" in text.lower() and "provisional" not in text.lower():
            raise ValueError(f"{skill} mentions final inventory id without provisional timing")
        require_terms(skill, text, ["Provisional inventory refs", "artifact 10 finalizes inventory"])
    reconciler = read(ROOT / "skills/novel-hld-inventory-reconciler/SKILL.md")
    require_terms("novel-hld-inventory-reconciler", reconciler, ["only artifact 10 may mint final `inventory:INV-xx` ids"])


def parse_rows(text: str, heading: str) -> list[dict[str, str]]:
    match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not match:
        raise ValueError(f"missing heading: {heading}")
    section = text[match.end():]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[:next_heading.start()]
    table_lines = [
        line.strip() for line in section.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    table_lines = [
        line for line in table_lines
        if not all(set(cell.strip()) <= {"-", ":"} for cell in line.strip("|").split("|"))
    ]
    if len(table_lines) < 2:
        raise ValueError(f"{heading} must contain a table with at least one row")
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            raise ValueError(f"{heading} row has {len(cells)} cells, expected {len(headers)}")
        rows.append(dict(zip(headers, cells)))
    return rows


def parse_field_value_section(text: str, heading: str) -> dict[str, str]:
    rows = parse_rows(text, heading)
    if not rows or "Field" not in rows[0] or "Value" not in rows[0]:
        raise ValueError(f"{heading} must be a Field/Value table")
    values = {row["Field"]: row["Value"].strip("`") for row in rows}
    if not values:
        raise ValueError(f"{heading} must not be empty")
    return values


def validate_required_columns(text: str, heading: str, columns: list[str]) -> list[dict[str, str]]:
    rows = parse_rows(text, heading)
    observed = set(rows[0]) if rows else set()
    missing = [column for column in columns if column not in observed]
    if missing:
        raise ValueError(f"{heading} missing required columns: {missing}")
    return rows


def validate_hld_source_map_rows(source_map_text: str | None = None) -> None:
    text = source_map_text or """
## HLD Source Map

| HLD fact id | Upstream fact id | Fact type | Upstream fact atom | HLD fact atom | Source refs | Owner artifact | Final inventory id | Expansion mode | Support mechanism | LLD handoff target | Preservation status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HLD-F-01 | UPF-PRD-S01-01 | rule | upstream atom | HLD expands atom without replacing it | scene:PRD-S01 | artifact 03 | inventory:INV-01 | explain | explains technical boundary | LLD-RULE-01 | bounded_expansion |
"""
    rows = parse_rows(text, "HLD Source Map")
    upstream_atoms_by_id: dict[str, str] = {}
    hld_fact_ids: set[str] = set()
    for row in rows:
        for column in ["HLD fact id", "Upstream fact id", "Upstream fact atom", "HLD fact atom", "Source refs", "Owner artifact", "Expansion mode", "Preservation status"]:
            if not row.get(column):
                raise ValueError(f"HLD Source Map row missing {column}")
        hld_fact_id = row["HLD fact id"]
        if hld_fact_id in hld_fact_ids:
            raise ValueError(f"duplicate HLD fact id: {hld_fact_id}")
        hld_fact_ids.add(hld_fact_id)
        upstream_fact_id = row["Upstream fact id"]
        if not UPSTREAM_FACT_ID_PATTERN.fullmatch(upstream_fact_id):
            raise ValueError(f"invalid upstream fact id: {upstream_fact_id}")
        canonical_source_refs(row["Source refs"])
        if row["Expansion mode"] not in EXPANSION_MODES:
            raise ValueError(f"invalid expansion mode: {row['Expansion mode']}")
        if row["Preservation status"] not in VALID_PRESERVATION:
            raise ValueError(f"invalid preservation status: {row['Preservation status']}")
        validate_inventory_ref_value(row.get("Final inventory id", ""), allow_none=True)
        validate_lld_handoff_values(row.get("LLD handoff target", ""))
        upstream_atom = normalize_fact_text(row["Upstream fact atom"])
        if upstream_fact_id in upstream_atoms_by_id and upstream_atoms_by_id[upstream_fact_id] != upstream_atom:
            raise ValueError(f"same upstream fact id rewrites upstream fact atom: {upstream_fact_id}")
        upstream_atoms_by_id[upstream_fact_id] = upstream_atom


def validate_source_map_trace_binding(artifact_11_text: str) -> None:
    source_map_rows = parse_rows(artifact_11_text, "HLD Source Map")
    trace_rows = parse_rows(artifact_11_text, "HLD Fact Trace")
    trace_by_id = {row["Fact trace id"]: row for row in trace_rows}
    for source_map_row in source_map_rows:
        trace_row = trace_by_id.get(source_map_row["HLD fact id"])
        if trace_row is None:
            raise ValueError(f"Source Map row lacks HLD Fact Trace: {source_map_row['HLD fact id']}")
        for column in [
            "Upstream fact id",
            "Upstream fact atom",
            "HLD fact atom",
            "Expansion mode",
            "Support mechanism",
            "Preservation status",
        ]:
            if normalize_fact_text(source_map_row[column]) != normalize_fact_text(trace_row[column]):
                raise ValueError(f"Source Map HLD Fact Trace mismatch: {source_map_row['HLD fact id']} {column}")
        if canonical_source_refs(source_map_row["Source refs"]) != canonical_source_refs(trace_row["Source refs"]):
            raise ValueError(f"Source Map HLD Fact Trace mismatch: {source_map_row['HLD fact id']} Source refs")


def validate_lld_handoff_index(artifact_11_text: str) -> None:
    source_map_rows = parse_rows(artifact_11_text, "HLD Source Map")
    handoff_rows = validate_required_columns(
        artifact_11_text,
        "LLD handoff index",
        LLD_HANDOFF_INDEX_COLUMNS,
    )
    handoff_pairs: set[tuple[str, str]] = set()
    handoff_fact_ids: set[str] = set()
    for handoff_row in handoff_rows:
        for column in LLD_HANDOFF_INDEX_COLUMNS:
            if not handoff_row.get(column):
                raise ValueError(f"LLD handoff index row missing {column}")
        if handoff_row["Handoff status"] != "ready":
            raise ValueError(f"LLD handoff index is not ready: {handoff_row['HLD fact id']}")
        validate_lld_handoff_values(handoff_row["LLD handoff target"])
        validate_inventory_ref_value(handoff_row["Final inventory id"], allow_none=True)
        canonical_source_refs(handoff_row["Source refs"])
        pair = (handoff_row["LLD handoff target"], handoff_row["HLD fact id"])
        if pair in handoff_pairs:
            raise ValueError(f"duplicate LLD handoff index row: {pair}")
        handoff_pairs.add(pair)
        hld_fact_id = handoff_row["HLD fact id"]
        if hld_fact_id in handoff_fact_ids:
            raise ValueError(f"duplicate LLD handoff mappings for HLD fact: {hld_fact_id}")
        handoff_fact_ids.add(hld_fact_id)

    matched_hld_fact_ids: set[str] = set()
    for source_map_row in source_map_rows:
        expected = {
            "LLD handoff target": source_map_row["LLD handoff target"],
            "HLD fact id": source_map_row["HLD fact id"],
            "Owner artifact": source_map_row["Owner artifact"],
            "Final inventory id": source_map_row["Final inventory id"],
            "Upstream fact id": source_map_row["Upstream fact id"],
            "Upstream fact atom": source_map_row["Upstream fact atom"],
            "HLD fact atom": source_map_row["HLD fact atom"],
            "Source refs": source_map_row["Source refs"],
        }
        matches = [
            row for row in handoff_rows
            if row["LLD handoff target"] == expected["LLD handoff target"]
            and row["HLD fact id"] == expected["HLD fact id"]
            and row["Owner artifact"] == expected["Owner artifact"]
            and row["Final inventory id"] == expected["Final inventory id"]
            and row["Upstream fact id"] == expected["Upstream fact id"]
            and normalize_fact_text(row["Upstream fact atom"])
            == normalize_fact_text(expected["Upstream fact atom"])
            and normalize_fact_text(row["HLD fact atom"])
            == normalize_fact_text(expected["HLD fact atom"])
            and canonical_source_refs(row["Source refs"])
            == canonical_source_refs(expected["Source refs"])
        ]
        if len(matches) != 1:
            raise ValueError(
                f"LLD handoff index drift: {source_map_row['HLD fact id']} expected 1 mapping, found {len(matches)}"
            )
        matched_hld_fact_ids.add(source_map_row["HLD fact id"])

    orphaned = {row["HLD fact id"] for row in handoff_rows} - matched_hld_fact_ids
    if orphaned:
        raise ValueError(f"LLD handoff index contains orphaned HLD facts: {sorted(orphaned)}")


def validate_design_fact_source_map_coverage(
    artifact_texts: dict[str, str],
    source_map_rows: list[dict[str, str]],
    resolved_final_inventory_ids: dict[str, str],
) -> None:
    matched_hld_fact_ids: set[str] = set()
    for artifact_id, (heading, id_column) in SOURCE_MAP_DESIGN_ARTIFACTS.items():
        business_rows = parse_rows(artifact_texts[artifact_id], heading)
        trace_by_id = {
            row["Fact trace id"]: row
            for row in parse_rows(artifact_texts[artifact_id], "HLD Fact Trace")
        }
        for business_row in business_rows:
            design_id = business_row[id_column]
            trace_row = trace_by_id[design_id]
            final_inventory_id = "none"
            if "Inventory id" in business_row:
                final_inventory_id = resolved_final_inventory_ids.get(business_row["Inventory id"], "")
                if not final_inventory_id:
                    raise ValueError(
                        f"unresolved Source Map inventory disposition: artifact {artifact_id} {design_id}"
                    )
            matches = [
                row for row in source_map_rows
                if row["Owner artifact"] == f"artifact {artifact_id}"
                and row["Final inventory id"] == final_inventory_id
                and row["Upstream fact id"] == trace_row["Upstream fact id"]
                and normalize_fact_text(row["Upstream fact atom"])
                == normalize_fact_text(trace_row["Upstream fact atom"])
                and normalize_fact_text(row["HLD fact atom"])
                == normalize_fact_text(trace_row["HLD fact atom"])
                and canonical_source_refs(row["Source refs"])
                == canonical_source_refs(trace_row["Source refs"])
                and row["LLD handoff target"] == business_row["LLD handoff"]
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"missing Source Map closure: artifact {artifact_id} {design_id} "
                    f"expected 1 mapping, found {len(matches)}"
                )
            matched_hld_fact_ids.add(matches[0]["HLD fact id"])

    orphaned = {row["HLD fact id"] for row in source_map_rows} - matched_hld_fact_ids
    if orphaned:
        raise ValueError(f"Source Map contains orphaned design facts: {sorted(orphaned)}")


def split_list_refs(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;，；]\s*", value.strip()) if part.strip()]


def parse_environment_state_realizations(value: str, event_id: str) -> dict[str, tuple[str, str]]:
    if is_none_value(value):
        raise ValueError(f"missing event environment state realizations: {event_id}")
    realizations: dict[str, tuple[str, str]] = {}
    for item in re.split(r"[;；]\s*", value.strip()):
        match = ENVIRONMENT_STATE_REALIZATION_PATTERN.fullmatch(item.strip())
        if not match:
            raise ValueError(f"invalid event environment state realization: {event_id}")
        state_change_id, dimension, realization = match.groups()
        realization = realization.strip()
        if (
            state_change_id in realizations
            or dimension not in ENVIRONMENT_STATE_CHANGE_DIMENSIONS
            or is_none_value(realization)
            or realization.casefold() in {"tbd", "todo", "unknown", "placeholder", "待定", "未定义"}
            or len(normalize_fact_text(realization)) < 8
        ):
            raise ValueError(f"invalid event environment state realization: {event_id}")
        realizations[state_change_id] = (dimension, realization)
    return realizations


def parse_environment_state_transitions(value: str, event_id: str) -> dict[str, tuple[str, str]]:
    if is_none_value(value):
        raise ValueError(f"missing event environment state transitions: {event_id}")
    transitions: dict[str, tuple[str, str]] = {}
    for item in re.split(r"[;；]\s*", value.strip()):
        match = ENVIRONMENT_STATE_TRANSITION_PATTERN.fullmatch(item.strip())
        if not match:
            raise ValueError(f"invalid event environment state transition: {event_id}")
        state_change_id, state_before, state_after = match.groups()
        if state_change_id in transitions:
            raise ValueError(f"invalid event environment state transition: {event_id}")
        transitions[state_change_id] = (state_before, state_after)
    return transitions


def validate_lld_handoff_values(value: str) -> None:
    refs = split_list_refs(value)
    if not refs:
        raise ValueError("LLD handoff must not be empty")
    for ref in refs:
        if not re.fullmatch(r"LLD-[A-Z0-9-]+", ref):
            raise ValueError(f"invalid LLD handoff: {ref}")


def validate_amendment_request(value: str) -> None:
    if is_none_value(value):
        return
    for ref in split_list_refs(value):
        if not re.fullmatch(r"HLD-AMEND-\d{2,}", ref):
            raise ValueError(f"invalid amendment request: {ref}")


def validate_support_refs(value: str, support_ids: set[str]) -> None:
    refs = split_list_refs(value)
    if not refs:
        raise ValueError("Supports must not be empty")
    for ref in refs:
        if ref not in support_ids:
            raise ValueError(f"unresolved support reference: {ref}")


def validate_reference_list(value: str, allowed: set[str], label: str, extra_allowed: set[str] | None = None) -> None:
    extra = extra_allowed or set()
    refs = split_list_refs(value)
    if not refs:
        raise ValueError(f"{label} must not be empty")
    for ref in refs:
        if ref in allowed or ref in extra:
            continue
        raise ValueError(f"unresolved {label} reference: {ref}")


def validate_inventory_obligations(value: str, inventory_ids: set[str], support_id: str) -> None:
    if is_none_value(value):
        return
    refs = split_list_refs(value)
    if not refs:
        raise ValueError(f"Inventory obligations must not be empty: {support_id}")
    for ref in refs:
        if ref not in inventory_ids:
            raise ValueError(f"unresolved inventory obligation: {support_id} {ref}")


def duplicate_values(rows: list[dict[str, str]], column: str) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        value = row.get(column, "")
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def contains_any_term(value: str, terms: set[str]) -> bool:
    text = normalize_fact_text(value)
    return any(term in text for term in terms)


def validate_character_quality_row(row: dict[str, str]) -> None:
    for column in ["Role type", "Function", "Relationship/motivation", "Information permission"]:
        if is_none_value(row.get(column)):
            raise ValueError(f"missing character core field: {row.get('Character id', '')} {column}")

    motive = row.get("Concrete motive evidence", "")
    if is_none_value(motive) or not contains_any_term(motive, CONCRETE_MOTIVE_TERMS):
        raise ValueError(f"invalid concrete motive evidence: {row.get('Character id', '')}")
    if contains_any_term(motive, ABSTRACT_MOTIVE_TERMS):
        raise ValueError(f"invalid concrete motive evidence: {row.get('Character id', '')}")
    normalized_motive = normalize_fact_text(motive)
    word_count = len(re.findall(r"[a-z0-9]+", normalized_motive))
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", normalized_motive))
    if (has_cjk and len(normalized_motive) < 6) or (not has_cjk and word_count < 4):
        raise ValueError(f"invalid concrete motive evidence: {row.get('Character id', '')}")

    identity_subject = " ".join(
        row.get(column, "")
        for column in ["Entity type", "Entity name", "Role type", "Function", "Relationship/motivation"]
    )
    boundary = row.get("Identity boundary", "")
    if contains_any_term(identity_subject, DIGITAL_LIFE_TERMS):
        if is_none_value(boundary) or not contains_any_term(boundary, DIGITAL_LIFE_BOUNDARY_TERMS):
            raise ValueError(f"missing digital-life identity boundary: {row.get('Character id', '')}")
        if contains_any_term(boundary, DIGITAL_LIFE_FORBIDDEN_BOUNDARY_TERMS):
            raise ValueError(f"invalid digital-life identity boundary: {row.get('Character id', '')}")
    elif is_none_value(boundary):
        raise ValueError(f"missing character core field: {row.get('Character id', '')} Identity boundary")


def validate_environment_quality_row(row: dict[str, str]) -> None:
    for column in [
        "Environment type",
        "Function",
        "Spatial relation",
        "State change id",
        "State change dimension",
        "State before",
        "State after",
        "State change",
    ]:
        if is_none_value(row.get(column)):
            raise ValueError(f"missing environment core field: {row.get('Environment id', '')} {column}")
    if not ENVIRONMENT_STATE_CHANGE_ID_PATTERN.fullmatch(row["State change id"]):
        raise ValueError(f"invalid environment state change id: {row['Environment id']}")
    if row["State change dimension"] not in ENVIRONMENT_STATE_CHANGE_DIMENSIONS:
        raise ValueError(f"invalid environment state change dimension: {row['Environment id']}")
    if not ENVIRONMENT_STATE_VALUE_PATTERN.fullmatch(row["State before"]):
        raise ValueError(f"invalid environment state before: {row['Environment id']}")
    if not ENVIRONMENT_STATE_VALUE_PATTERN.fullmatch(row["State after"]):
        raise ValueError(f"invalid environment state after: {row['Environment id']}")
    if row["State before"] == row["State after"]:
        raise ValueError(f"environment state transition has no change: {row['Environment id']}")


def validate_event_quality_row(row: dict[str, str]) -> None:
    for column in ["Event action", "Causal role", "Consequences"]:
        value = row.get(column, "")
        normalized = normalize_fact_text(value)
        if (
            is_none_value(value)
            or value.casefold() in {"tbd", "todo", "unknown", "placeholder", "待定", "未定义"}
            or len(normalized) < 8
        ):
            raise ValueError(f"missing event core field: {row.get('Event id', '')} {column}")


def validate_information_quality_row(row: dict[str, str]) -> None:
    for column in [
        "PRD information boundary id",
        "Freeze refs",
        "Story anchor event ref",
        "Time layer",
        "Narrative reveal phase",
        "Disclosure tier",
        "Information object",
        "Reveal event ref",
        "Reveal action",
        "Reveal condition type",
        "Reveal condition refs",
        "Reveal condition",
    ]:
        value = row.get(column, "")
        if is_none_value(value) or value.casefold() in {"tbd", "todo", "unknown", "placeholder", "待定", "未定义"}:
            raise ValueError(f"missing information core field: {row.get('Info id', '')} {column}")
    if row["Time layer"] not in TIME_LAYERS:
        raise ValueError(f"invalid information time layer: {row['Info id']}")
    if row["Disclosure tier"] not in DISCLOSURE_TIERS:
        raise ValueError(f"invalid information disclosure tier: {row['Info id']}")
    if not REVEAL_PHASE_PATTERN.fullmatch(row["Narrative reveal phase"]):
        raise ValueError(f"invalid information narrative reveal phase: {row['Info id']}")
    if row["Reveal condition type"] not in REVEAL_CONDITION_TYPES:
        raise ValueError(f"invalid information reveal condition type: {row['Info id']}")
    if not re.fullmatch(r"PRD-INFO-\d{2,}", row["PRD information boundary id"]):
        raise ValueError(f"invalid PRD information boundary id: {row['Info id']}")
    freeze_refs = split_source_refs(row["Freeze refs"])
    if not freeze_refs or any(not re.fullmatch(r"freeze:PRD-FREEZE-\d{2,}", ref) for ref in freeze_refs):
        raise ValueError(f"invalid information freeze refs: {row['Info id']}")
    if len(normalize_fact_text(row["Reveal condition"])) < 8:
        raise ValueError(f"missing information core field: {row['Info id']} Reveal condition")


def validate_thread_text(value: str, label: str) -> None:
    normalized = normalize_fact_text(value)
    if (
        is_none_value(value)
        or value.casefold() in {"tbd", "todo", "unknown", "placeholder", "待定", "未定义"}
        or len(normalized) < 12
    ):
        raise ValueError(f"invalid {label}")


def validate_style_text(value: str, label: str, allow_short: bool = False) -> None:
    normalized = normalize_fact_text(value)
    if (
        is_none_value(value)
        or value.casefold() in {"tbd", "todo", "unknown", "placeholder", "待定", "未定义"}
        or (not allow_short and len(normalized) < 4)
        or any(term in normalized for term in VAGUE_STYLE_TERMS)
    ):
        raise ValueError(f"invalid {label}")


def parse_exact_key_value_parts(value: str, expected_keys: set[str], label: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            raise ValueError(f"invalid {label}")
        key, item_value = (item.strip() for item in part.split("=", 1))
        normalized_key = key.casefold()
        if not normalized_key or not item_value or normalized_key in parts:
            raise ValueError(f"invalid {label}")
        parts[normalized_key] = item_value
    if set(parts) != expected_keys:
        raise ValueError(f"invalid {label}")
    return parts


def validate_style_execution_constraint(
    value: str,
    field_name: str,
    rule_type: str,
    style_id: str,
    information_refs: set[str],
    thread_refs: set[str],
    reader_disclosure_mode: str,
    character_names: set[str],
) -> None:
    parts = parse_exact_key_value_parts(
        value,
        STYLE_EXECUTION_CONSTRAINT_KEYS[field_name],
        "style execution constraint",
    )
    for key, item_value in parts.items():
        validate_style_text(
            item_value,
            f"style execution constraint {field_name}.{key}: {style_id}",
            allow_short=field_name == "POV permission" and key == "focalizer",
        )
    required_markers = STYLE_EXECUTION_MARKERS_BY_RULE_TYPE[rule_type][field_name]
    action_key = {
        "Design fact": "rule",
        "POV permission": "permitted",
        "Prohibited expression": "forbidden",
    }[field_name]
    if not any(marker in normalize_fact_text(parts[action_key]) for marker in required_markers):
        label = {
            "Design fact": "rule",
            "POV permission": "permission",
            "Prohibited expression": "prohibition",
        }[field_name]
        raise ValueError(f"invalid style execution {label}: {style_id}")
    if field_name == "Design fact":
        if parts["scope"] not in information_refs | thread_refs:
            raise ValueError(f"style execution scope mismatch: {style_id}")
    elif field_name == "POV permission":
        validate_style_focalizer(parts["focalizer"], character_names, style_id)
        if parts["evidence"] not in information_refs:
            raise ValueError(f"style execution evidence mismatch: {style_id}")
    else:
        if parts["target"] not in information_refs | thread_refs:
            raise ValueError(f"style execution target mismatch: {style_id}")
        if parts["trigger"] != reader_disclosure_mode:
            raise ValueError(f"style execution trigger mismatch: {style_id}")


def validate_style_focalizer(value: str, character_names: set[str], style_id: str) -> None:
    validate_style_text(value, f"style focalizer: {style_id}", allow_short=True)
    if normalize_fact_text(value) not in character_names:
        raise ValueError(f"unresolved style focalizer: {style_id} {value}")


def validate_language_profile(value: str, style_id: str) -> None:
    profile_parts = parse_exact_key_value_parts(value, set(LANGUAGE_PROFILE_DIRECTIVE_KEYS), "language profile")
    for dimension, directives in profile_parts.items():
        directive_parts: dict[str, str] = {}
        for directive in directives.split(","):
            if ":" not in directive:
                raise ValueError(f"invalid language profile: {style_id}")
            key, item_value = (item.strip() for item in directive.split(":", 1))
            normalized_key = key.casefold()
            if not normalized_key or not item_value or normalized_key in directive_parts:
                raise ValueError(f"invalid language profile: {style_id}")
            directive_parts[normalized_key] = item_value
        if set(directive_parts) != LANGUAGE_PROFILE_DIRECTIVE_KEYS[dimension]:
            raise ValueError(f"invalid language profile: {style_id}")
        for key, item_value in directive_parts.items():
            validate_style_text(item_value, f"language profile {dimension}.{key}: {style_id}")


def validate_thread_system_rows(
    threads: list[dict[str, str]],
    event_ids: set[str],
    info_ids: set[str],
    support_by_id: dict[str, dict[str, str]],
    rule_ids: set[str] | None = None,
    character_ids: set[str] | None = None,
) -> None:
    rule_ids = rule_ids or set()
    character_ids = character_ids or set()
    anchor_ids_by_type = {
        "rule": rule_ids,
        "character": character_ids,
        "event": event_ids,
        "information": info_ids,
    }
    required_anchor_types_by_thread_type = {
        "main": {"event"},
        "hidden": {"information"},
        "emotional": {"character"},
        "theme": {"event"},
        "institutional": {"rule"},
        "identity": {"character", "information"},
    }
    thread_ids = {row["Thread id"] for row in threads}
    for row in threads:
        if row["Thread type"].casefold() not in THREAD_TYPES:
            raise ValueError(f"invalid Thread type: {row['Thread type']}")
        if row["Closure state"].casefold() not in THREAD_CLOSURE_STATES:
            raise ValueError(f"invalid Closure state: {row['Closure state']}")
    missing_types = sorted(
        REQUIRED_CORE_THREAD_TYPES - {row["Thread type"].casefold() for row in threads}
    )
    if missing_types:
        raise ValueError(f"missing required thread types: {missing_types}")

    crossover_targets: dict[str, set[str]] = {}
    core_questions: dict[str, str] = {}
    core_pressure_refs: dict[str, set[str]] = {}
    for row in threads:
        thread_id = row["Thread id"]
        thread_type = row["Thread type"].casefold()
        expected_function = CORE_THREAD_FUNCTION_BY_TYPE.get(thread_type)
        if expected_function and row["Thread function"] != expected_function:
            raise ValueError(f"invalid core thread function: {thread_id}")
        if thread_type == "support" and row["Thread function"] != "support":
            raise ValueError(f"invalid support thread function: {thread_id}")
        anchor_refs = split_list_refs(row["Thread anchor refs"])
        anchor_types: set[str] = set()
        for anchor_ref in anchor_refs:
            anchor_match = re.fullmatch(
                r"(rule|character|event|information):(HLD-(?:03|04|06|07)-\d{2,})",
                anchor_ref,
            )
            if not anchor_match:
                raise ValueError(f"invalid thread anchor ref: {thread_id}")
            anchor_type, anchor_id = anchor_match.groups()
            expected_ids = anchor_ids_by_type[anchor_type]
            if expected_ids and anchor_id not in expected_ids:
                raise ValueError(f"unresolved thread anchor ref: {thread_id} {anchor_ref}")
            anchor_types.add(anchor_type)
        required_anchor_types = required_anchor_types_by_thread_type.get(thread_type, set())
        if not required_anchor_types <= anchor_types:
            raise ValueError(f"missing required thread anchor type: {thread_id}")
        pressure_refs = set(split_source_refs(row["Required pressure refs"]))
        support_refs = split_list_refs(row["Supports"])
        supported_pressure_refs = {
            ref
            for support_ref in support_refs
            for ref in split_source_refs(support_by_id[support_ref]["Source"])
        }
        if not pressure_refs <= supported_pressure_refs:
            raise ValueError(f"thread pressure refs are not supported: {thread_id}")
        validate_thread_text(row["Core question"], f"thread core question: {thread_id}")
        if not row["Core question"].rstrip().endswith(("?", "？")):
            raise ValueError(f"invalid thread core question: {thread_id}")
        if thread_type in REQUIRED_CORE_THREAD_TYPES:
            normalized_question = normalize_fact_text(row["Core question"])
            if normalized_question in core_questions:
                raise ValueError(
                    f"duplicate core thread question: {thread_id} {core_questions[normalized_question]}"
                )
            core_questions[normalized_question] = thread_id
            core_pressure_refs[thread_id] = pressure_refs
        validate_thread_text(row["Closure outcome"], f"thread closure outcome: {thread_id}")

        nodes = split_list_refs(row["Node distribution"])
        if len(nodes) < 2 or len(nodes) != len(set(nodes)):
            raise ValueError(f"thread node distribution must contain two distinct nodes: {thread_id}")
        validate_reference_list(row["Node distribution"], event_ids | info_ids, "thread node")
        progression_steps = [step.strip() for step in row["Thread progression"].split("->") if step.strip()]
        if len(progression_steps) < 2:
            raise ValueError(f"invalid thread progression: {thread_id}")
        progression_nodes: list[str] = []
        progression_states: list[str] = []
        for step in progression_steps:
            progression_match = re.fullmatch(r"(HLD-(?:06|07)-\d{2,})\s*:\s*(.+)", step)
            if not progression_match:
                raise ValueError(f"invalid thread progression: {thread_id}")
            node_id, state = progression_match.groups()
            validate_thread_text(state, f"thread progression state: {thread_id}")
            progression_nodes.append(node_id)
            progression_states.append(normalize_fact_text(state))
        if progression_nodes != nodes or len(progression_states) != len(set(progression_states)):
            raise ValueError(f"invalid thread progression: {thread_id}")
        if thread_type in REQUIRED_CORE_THREAD_TYPES and row["Closure state"].casefold() == "blocked":
            raise ValueError(f"required thread cannot be blocked: {thread_id}")

        crossover_match = re.fullmatch(r"thread:(HLD-08-\d{2,})\s*;\s*effect=(.+)", row["Crossover"].strip())
        if not crossover_match:
            raise ValueError(f"invalid thread crossover: {thread_id}")
        target_id, effect = crossover_match.groups()
        if target_id == thread_id:
            raise ValueError(f"self thread crossover: {thread_id}")
        if target_id not in thread_ids:
            raise ValueError(f"unresolved thread crossover: {thread_id} {target_id}")
        validate_thread_text(effect, f"thread crossover effect: {thread_id}")
        crossover_targets[thread_id] = {target_id}

    core_thread_ids = {
        row["Thread id"]
        for row in threads
        if row["Thread type"].casefold() in REQUIRED_CORE_THREAD_TYPES
    }
    for thread_id, pressure_refs in core_pressure_refs.items():
        other_pressure_refs = set().union(
            *(refs for candidate_id, refs in core_pressure_refs.items() if candidate_id != thread_id)
        )
        if not pressure_refs - other_pressure_refs:
            raise ValueError(f"core thread lacks distinct pressure ref: {thread_id}")
    connected: set[str] = set()
    pending = [next(iter(core_thread_ids))]
    while pending:
        thread_id = pending.pop()
        if thread_id in connected:
            continue
        connected.add(thread_id)
        for candidate_id, targets in crossover_targets.items():
            if candidate_id == thread_id or thread_id in targets:
                if candidate_id in core_thread_ids:
                    pending.append(candidate_id)
        pending.extend(target_id for target_id in crossover_targets[thread_id] if target_id in core_thread_ids)
    if connected != core_thread_ids:
        raise ValueError(f"required thread crossover graph is disconnected: {sorted(core_thread_ids - connected)}")


def validate_style_pov_rows(
    style_rows: list[dict[str, str]],
    information_by_id: dict[str, dict[str, str]],
    thread_ids: set[str],
    character_names: set[str],
) -> None:
    info_ids = set(information_by_id)
    observed_rule_types = {row["Rule type"].casefold() for row in style_rows}
    missing_rule_types = sorted(set(STYLE_ACCESS_POLICY_BY_RULE_TYPE) - observed_rule_types)
    if missing_rule_types:
        raise ValueError(f"missing required Style/POV Rule types: {missing_rule_types}")
    for row in style_rows:
        style_id = row["Style/POV id"]
        rule_type = row["Rule type"].casefold()
        expected_policy = STYLE_ACCESS_POLICY_BY_RULE_TYPE[rule_type]
        if row["Access policy"] != expected_policy:
            raise ValueError(f"invalid Style/POV access policy: {style_id}")
        expected_disclosure_mode = STYLE_READER_DISCLOSURE_MODE_BY_RULE_TYPE[rule_type]
        if not row["Reader disclosure mode"]:
            raise ValueError(f"missing style reader disclosure mode: {style_id}")
        if row["Reader disclosure mode"] != expected_disclosure_mode:
            raise ValueError(f"invalid style reader disclosure mode: {style_id}")
        information_refs = split_list_refs(row["Information refs"])
        if not information_refs:
            raise ValueError(f"missing style information refs: {style_id}")
        for information_ref in information_refs:
            match = re.fullmatch(r"info:(HLD-07-\d{2,})", information_ref)
            if not match or match.group(1) not in info_ids:
                raise ValueError(f"unresolved style information ref: {style_id} {information_ref}")
            information = information_by_id[match.group(1)]
            if "reader" in split_list_refs(information["Hidden from"]):
                allowed_modes = {"external_inference", "reveal_at_information_gate"}
                if row["Reader disclosure mode"] not in allowed_modes:
                    raise ValueError(f"style reader disclosure violates information boundary: {style_id}")
            if row["Reader disclosure mode"] == "reveal_at_information_gate" and is_none_value(information["Reveal event ref"]):
                raise ValueError(f"style reveal gate lacks information event: {style_id}")
        thread_refs = split_list_refs(row["Thread refs"])
        if not thread_refs:
            raise ValueError(f"missing style thread refs: {style_id}")
        for thread_ref in thread_refs:
            match = re.fullmatch(r"thread:(HLD-08-\d{2,})", thread_ref)
            if not match or match.group(1) not in thread_ids:
                raise ValueError(f"unresolved style thread ref: {style_id} {thread_ref}")
        if rule_type == "language style":
            validate_language_profile(row["Language profile"], style_id)
        elif not is_none_value(row["Language profile"]):
            raise ValueError(f"non-language style carries language profile: {style_id}")
        for field_name in STYLE_EXECUTION_CONSTRAINT_KEYS:
            validate_style_execution_constraint(
                row[field_name],
                field_name,
                rule_type,
                style_id,
                set(information_refs),
                set(thread_refs),
                row["Reader disclosure mode"],
                character_names,
            )


def reveal_phase_number(value: str) -> int:
    match = REVEAL_PHASE_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"invalid information narrative reveal phase: {value}")
    return int(match.group(1))


def validate_information_predecessor_graph(predecessors_by_info_id: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(info_id: str) -> None:
        if info_id in visiting:
            raise ValueError(f"cyclic information reveal predecessor: {info_id}")
        if info_id in visited:
            return
        visiting.add(info_id)
        for predecessor_id in predecessors_by_info_id[info_id]:
            visit(predecessor_id)
        visiting.remove(info_id)
        visited.add(info_id)

    for info_id in predecessors_by_info_id:
        visit(info_id)


def validate_information_tier_dependencies(
    information_by_id: dict[str, dict[str, str]],
    predecessors_by_info_id: dict[str, set[str]],
) -> None:
    operational_info_ids = {
        info_id for info_id, row in information_by_id.items()
        if row["Disclosure tier"] == "operational_intelligence"
    }
    if not operational_info_ids:
        return

    def has_operational_predecessor(info_id: str, visited: set[str] | None = None) -> bool:
        visited = visited or set()
        for predecessor_id in predecessors_by_info_id[info_id]:
            if predecessor_id in operational_info_ids:
                return True
            if predecessor_id not in visited and has_operational_predecessor(predecessor_id, visited | {predecessor_id}):
                return True
        return False

    for info_id, row in information_by_id.items():
        if row["Disclosure tier"] == "complete_cause" and not has_operational_predecessor(info_id):
            raise ValueError(f"complete cause lacks operational-intelligence predecessor: {info_id}")


def validate_event_causal_graph(predecessors_by_event_id: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(event_id: str) -> None:
        if event_id in visiting:
            raise ValueError(f"cyclic event predecessor: {event_id}")
        if event_id in visited:
            return
        visiting.add(event_id)
        for predecessor_id in predecessors_by_event_id[event_id]:
            visit(predecessor_id)
        visiting.remove(event_id)
        visited.add(event_id)

    for event_id in predecessors_by_event_id:
        visit(event_id)


def event_precedes_or_equals(
    predecessor_id: str,
    event_id: str,
    predecessors_by_event_id: dict[str, set[str]],
) -> bool:
    if predecessor_id == event_id:
        return True
    visited: set[str] = set()

    def visit(candidate_id: str) -> bool:
        if candidate_id in visited:
            return False
        visited.add(candidate_id)
        for direct_predecessor in predecessors_by_event_id[candidate_id]:
            if direct_predecessor == predecessor_id or visit(direct_predecessor):
                return True
        return False

    return visit(event_id)


def validate_hld_business_rules(artifact_texts: dict[str, str]) -> None:
    inventory = parse_rows(artifact_texts["01"], "Initial world entity inventory")
    support = parse_rows(artifact_texts["02"], "PRD support matrix")
    rules = parse_rows(artifact_texts["03"], "World rule design table")
    characters = parse_rows(artifact_texts["04"], "Character system table")
    environments = parse_rows(artifact_texts["05"], "Environment system table")
    events = parse_rows(artifact_texts["06"], "Event system table")
    information = parse_rows(artifact_texts["07"], "Time and information table")
    threads = parse_rows(artifact_texts["08"], "Thread system table")
    style = parse_rows(artifact_texts["09"], "Style and POV table")
    reconciliation = parse_rows(artifact_texts["10"], "Final inventory reconciliation table")

    duplicate_inventory_ids = duplicate_values(inventory, "Inventory id")
    if duplicate_inventory_ids:
        raise ValueError(f"duplicate Initial world entity inventory id: {duplicate_inventory_ids}")
    inventory_ids = {row["Inventory id"] for row in inventory}

    for row in inventory:
        if row["Entity type"] not in ENTITY_TYPES:
            raise ValueError(f"invalid Entity type: {row['Entity type']}")
        if row["Required HLD owner"] not in VALID_HLD_OWNER_ARTIFACTS:
            raise ValueError(f"invalid Required HLD owner: {row['Required HLD owner']}")
        validate_inventory_initial_status(row["Initial status"])
        amendment_id = inventory_amendment_id(row["Initial status"])
        expected_owner = INVENTORY_OWNER_BY_ENTITY_TYPE[row["Entity type"]]
        if row["Required HLD owner"] != expected_owner:
            raise ValueError(
                f"invalid inventory owner routing: {row['Inventory id']} "
                f"{row['Entity type']} requires {expected_owner}"
            )
        validate_hld_owner_list(row["Secondary HLD owners"], "Secondary HLD owners")
        if amendment_id:
            if row["Entity type"] != "unresolved amendment":
                raise ValueError(f"inventory amendment must use unresolved amendment entity type: {row['Inventory id']}")
        validate_source_ref_values(row["Source"])

    support_ids = {row["Support id"] for row in support}
    if len(support_ids) != len(support):
        raise ValueError("duplicate support id in PRD support matrix")
    if not support_ids:
        raise ValueError("PRD support matrix must not be empty")
    for row in support:
        if row["Support type"] not in EXPANSION_MODES:
            raise ValueError(f"invalid Support type: {row['Support type']}")
        if row["Required HLD owner"] not in VALID_HLD_OWNER_ARTIFACTS:
            raise ValueError(f"invalid Required HLD owner: {row['Required HLD owner']}")
        validate_source_ref_values(row["Source"])
        validate_inventory_obligations(row["Inventory obligations"], inventory_ids, row["Support id"])
        if not row.get("Required answer") or not row.get("Boundary"):
            raise ValueError(f"support row missing answer or boundary: {row['Support id']}")

    support_rows_by_owner = {
        owner: [row for row in support if row["Required HLD owner"] == owner]
        for owner in VALID_HLD_OWNER_ARTIFACTS
    }
    for row in inventory:
        if row["Entity type"] == "unresolved amendment":
            continue
        inventory_sources = set(split_source_refs(row["Source"]))
        for secondary_owner in split_list_refs(row["Secondary HLD owners"]):
            if is_none_value(secondary_owner):
                continue
            inventory_bound_support_rows = [
                support_row
                for support_row in support_rows_by_owner.get(secondary_owner, [])
                if row["Inventory id"] in split_list_refs(support_row["Inventory obligations"])
            ]
            if not inventory_bound_support_rows:
                raise ValueError(
                    f"secondary owner lacks inventory-bound support obligation: {row['Inventory id']} {secondary_owner}"
                )
            if not any(set(split_source_refs(support_row["Source"])) == inventory_sources for support_row in inventory_bound_support_rows):
                raise ValueError(
                    f"secondary owner support source mismatch: {row['Inventory id']} {secondary_owner}"
                )

    design_tables = [
        ("03", rules),
        ("04", characters),
        ("05", environments),
        ("06", events),
        ("07", information),
        ("08", threads),
        ("09", style),
    ]
    support_consumers: dict[str, set[str]] = {support_id: set() for support_id in support_ids}
    for artifact_id, rows in design_tables:
        for row in rows:
            support_refs = split_list_refs(row["Supports"])
            validate_support_refs(row["Supports"], support_ids)
            for support_ref in support_refs:
                if support_ref in support_consumers:
                    support_consumers[support_ref].add(f"artifact {artifact_id}")
            validate_source_ref_values(row["Source"])
            validate_lld_handoff_values(row["LLD handoff"])
            validate_amendment_request(row["Amendment request"])

    for row in support:
        support_id = row["Support id"]
        owner = row["Required HLD owner"]
        if owner == "artifact 10":
            continue
        consumers = support_consumers.get(support_id, set())
        if not consumers:
            raise ValueError(f"unconsumed support: {support_id}")
        if owner not in consumers:
            raise ValueError(f"support owner did not consume support: {support_id} expected {owner}")
        non_owner_consumers = sorted(consumers - {owner})
        if non_owner_consumers:
            raise ValueError(f"support consumed by non-owner: {support_id} {non_owner_consumers}")

    for row in rules:
        if row["Rule type"].casefold() not in WORLD_RULE_TYPES:
            raise ValueError(f"invalid Rule type: {row['Rule type']}")

    for row in events:
        if row["Event type"].casefold() not in EVENT_TYPES:
            raise ValueError(f"invalid Event type: {row['Event type']}")
        if row["Visibility"].casefold() not in EVENT_VISIBILITY:
            raise ValueError(f"invalid Visibility: {row['Visibility']}")

    character_ids = {row["Character id"] for row in characters}
    character_by_id = {row["Character id"]: row for row in characters}
    event_ids = {row["Event id"] for row in events}
    info_ids = {row["Info id"] for row in information}
    thread_ids = {row["Thread id"] for row in threads}
    for row in style:
        if row["Rule type"].casefold() not in STYLE_POV_RULE_TYPES:
            raise ValueError(f"invalid Style/POV Rule type: {row['Rule type']}")
    design_id_columns = {
        "03": "Rule id",
        "04": "Character id",
        "05": "Environment id",
        "06": "Event id",
        "07": "Info id",
        "08": "Thread id",
        "09": "Style/POV id",
    }
    amendment_trace_by_artifact = {
        artifact_id: {
            trace["Fact trace id"]: trace
            for trace in parse_rows(artifact_texts[artifact_id], "HLD Fact Trace")
            if trace.get("Fact trace id")
        }
        for artifact_id in design_id_columns
    }
    amendment_origins: dict[str, list[tuple[str, str, str, dict[str, str]]]] = {}
    for artifact_id, rows in [
        ("03", rules),
        ("04", characters),
        ("05", environments),
        ("06", events),
        ("07", information),
        ("08", threads),
        ("09", style),
    ]:
        for row in rows:
            for amendment_id in split_list_refs(row["Amendment request"]):
                if is_none_value(amendment_id):
                    continue
                origin_record_id = row[design_id_columns[artifact_id]]
                origin_trace = amendment_trace_by_artifact[artifact_id].get(origin_record_id)
                if not origin_trace:
                    raise ValueError(f"missing amendment origin fact trace: {amendment_id}")
                amendment_origins.setdefault(amendment_id, []).append(
                    (f"artifact {artifact_id}", origin_record_id, row["Source"], origin_trace)
                )
    ambiguous_amendments = sorted(
        amendment_id
        for amendment_id, origins in amendment_origins.items()
        if len(origins) != 1
    )
    if ambiguous_amendments:
        raise ValueError(f"amendment request must have one origin: {ambiguous_amendments}")
    amendment_ids = set(amendment_origins)

    inventory_by_id = {row["Inventory id"]: row for row in inventory}
    inventory_trace_by_id = {
        row["Fact trace id"]: row
        for row in parse_rows(artifact_texts["01"], "HLD Fact Trace")
        if row.get("Fact trace id")
    }
    character_trace_by_id = {
        row["Fact trace id"]: row
        for row in parse_rows(artifact_texts["04"], "HLD Fact Trace")
        if row.get("Fact trace id")
    }
    environment_trace_by_id = {
        row["Fact trace id"]: row
        for row in parse_rows(artifact_texts["05"], "HLD Fact Trace")
        if row.get("Fact trace id")
    }
    event_trace_by_id = {
        row["Fact trace id"]: row
        for row in parse_rows(artifact_texts["06"], "HLD Fact Trace")
        if row.get("Fact trace id")
    }
    duplicate_character_inventory_ids = duplicate_values(characters, "Inventory id")
    if duplicate_character_inventory_ids:
        raise ValueError(f"duplicate character inventory binding: {duplicate_character_inventory_ids}")
    character_rows_by_inventory_id = {row["Inventory id"]: row for row in characters if row.get("Inventory id")}
    character_support_inventory_consumers: dict[str, set[str]] = {support_id: set() for support_id in support_ids}
    for row in characters:
        validate_character_quality_row(row)
        relationship_targets = split_list_refs(row.get("Relationship targets", "none"))
        if contains_any_term(row.get("Relationship/motivation", ""), RELATIONSHIP_BOUND_MOTIVE_TERMS) and all(
            is_none_value(target) for target in relationship_targets
        ):
            raise ValueError(f"missing character relationship target: {row['Character id']}")
        for target in relationship_targets:
            if is_none_value(target):
                continue
            if target == row["Character id"]:
                raise ValueError(f"self character relationship target: {row['Character id']}")
            if target not in character_ids:
                raise ValueError(f"unresolved character relationship target: {row['Character id']} {target}")
        for support_ref in split_list_refs(row["Supports"]):
            if support_ref in character_support_inventory_consumers:
                character_support_inventory_consumers[support_ref].add(row["Inventory id"])
        inventory_row = inventory_by_id.get(row["Inventory id"])
        if not inventory_row:
            raise ValueError(f"unresolved character inventory id: {row['Inventory id']}")
        if inventory_row["Entity type"] not in {"character", "group"} or inventory_row["Required HLD owner"] != "artifact 04":
            raise ValueError(f"invalid character inventory binding: {row['Inventory id']}")
        for column in ["Entity type", "Entity name"]:
            if row[column] != inventory_row[column]:
                raise ValueError(f"character inventory identity mismatch: {row['Inventory id']} {column}")
        if set(split_source_refs(row["Source"])) != set(split_source_refs(inventory_row["Source"])):
            raise ValueError(f"character inventory source mismatch: {row['Inventory id']}")
        inventory_trace = inventory_trace_by_id.get(row["Inventory id"])
        character_trace = character_trace_by_id.get(row["Character id"])
        if not inventory_trace or not character_trace:
            raise ValueError(f"missing character inventory design: {row['Inventory id']}")
        if character_trace["Upstream fact id"] != inventory_trace["Upstream fact id"]:
            raise ValueError(f"character inventory upstream fact mismatch: {row['Inventory id']}")
        character_atom = normalize_fact_text(character_trace["HLD fact atom"])
        for required_value in [row["Inventory id"], row["Entity type"], row["Entity name"]]:
            if normalize_fact_text(required_value) not in character_atom:
                raise ValueError(
                    f"HLD fact atom does not bind {row['Character id']} to Character system table.{required_value}"
                )
    missing_character_inventory_design = sorted(
        row["Inventory id"]
        for row in inventory
        if row["Entity type"] in {"character", "group"}
        and row["Required HLD owner"] == "artifact 04"
        and row["Inventory id"] not in character_rows_by_inventory_id
    )
    if missing_character_inventory_design:
        raise ValueError(f"missing character inventory design: {missing_character_inventory_design}")

    duplicate_environment_inventory_ids = duplicate_values(environments, "Inventory id")
    if duplicate_environment_inventory_ids:
        raise ValueError(f"duplicate environment inventory binding: {duplicate_environment_inventory_ids}")
    duplicate_environment_state_change_ids = duplicate_values(environments, "State change id")
    if duplicate_environment_state_change_ids:
        raise ValueError(f"duplicate environment state change id: {duplicate_environment_state_change_ids}")
    environment_rows_by_inventory_id = {
        row["Inventory id"] for row in environments if row.get("Inventory id")
    }
    environment_support_inventory_consumers: dict[str, set[str]] = {support_id: set() for support_id in support_ids}
    for row in environments:
        validate_environment_quality_row(row)
        for support_ref in split_list_refs(row["Supports"]):
            if support_ref in environment_support_inventory_consumers:
                environment_support_inventory_consumers[support_ref].add(row["Inventory id"])
        inventory_row = inventory_by_id.get(row["Inventory id"])
        if not inventory_row:
            raise ValueError(f"unresolved environment inventory id: {row['Inventory id']}")
        if inventory_row["Entity type"] != "environment" or inventory_row["Required HLD owner"] != "artifact 05":
            raise ValueError(f"invalid environment inventory binding: {row['Inventory id']}")
        for column in ["Entity type", "Entity name"]:
            if row[column] != inventory_row[column]:
                raise ValueError(f"environment inventory identity mismatch: {row['Inventory id']} {column}")
        if set(split_source_refs(row["Source"])) != set(split_source_refs(inventory_row["Source"])):
            raise ValueError(f"environment inventory source mismatch: {row['Inventory id']}")
        inventory_trace = inventory_trace_by_id.get(row["Inventory id"])
        environment_trace = environment_trace_by_id.get(row["Environment id"])
        if not inventory_trace or not environment_trace:
            raise ValueError(f"missing environment inventory design: {row['Inventory id']}")
        if environment_trace["Upstream fact id"] != inventory_trace["Upstream fact id"]:
            raise ValueError(f"environment inventory upstream fact mismatch: {row['Inventory id']}")
        if normalize_fact_text(environment_trace["Upstream fact atom"]) != normalize_fact_text(inventory_trace["Upstream fact atom"]):
            raise ValueError(f"environment inventory upstream fact atom mismatch: {row['Inventory id']}")
        environment_atom = normalize_fact_text(environment_trace["HLD fact atom"])
        for required_value in [row["Inventory id"], row["Entity type"], row["Entity name"]]:
            if normalize_fact_text(required_value) not in environment_atom:
                raise ValueError(
                    f"HLD fact atom does not bind {row['Environment id']} to Environment system table.{required_value}"
                )
    missing_environment_inventory_design = sorted(
        row["Inventory id"]
        for row in inventory
        if row["Entity type"] == "environment"
        and row["Required HLD owner"] == "artifact 05"
        and row["Inventory id"] not in environment_rows_by_inventory_id
    )
    if missing_environment_inventory_design:
        raise ValueError(f"missing environment inventory design: {missing_environment_inventory_design}")

    duplicate_event_inventory_ids = duplicate_values(events, "Inventory id")
    if duplicate_event_inventory_ids:
        raise ValueError(f"duplicate event inventory binding: {duplicate_event_inventory_ids}")
    event_rows_by_inventory_id = {row["Inventory id"] for row in events if row.get("Inventory id")}
    event_support_inventory_consumers: dict[str, set[str]] = {support_id: set() for support_id in support_ids}
    for row in events:
        validate_event_quality_row(row)
        inventory_row = inventory_by_id.get(row["Inventory id"])
        if not inventory_row:
            raise ValueError(f"unresolved event inventory id: {row['Inventory id']}")
        if inventory_row["Entity type"] != "event" or inventory_row["Required HLD owner"] != "artifact 06":
            raise ValueError(f"invalid event inventory binding: {row['Inventory id']}")
        for column in ["Entity type", "Entity name"]:
            if row[column] != inventory_row[column]:
                raise ValueError(f"event inventory identity mismatch: {row['Inventory id']} {column}")
        if set(split_source_refs(row["Source"])) != set(split_source_refs(inventory_row["Source"])):
            raise ValueError(f"event inventory source mismatch: {row['Inventory id']}")
        inventory_trace = inventory_trace_by_id.get(row["Inventory id"])
        event_trace = event_trace_by_id.get(row["Event id"])
        if not inventory_trace or not event_trace:
            raise ValueError(f"missing event inventory design: {row['Inventory id']}")
        if event_trace["Upstream fact id"] != inventory_trace["Upstream fact id"]:
            raise ValueError(f"event inventory upstream fact mismatch: {row['Inventory id']}")
        if normalize_fact_text(event_trace["Upstream fact atom"]) != normalize_fact_text(inventory_trace["Upstream fact atom"]):
            raise ValueError(f"event inventory upstream fact atom mismatch: {row['Inventory id']}")
        event_atom = normalize_fact_text(event_trace["HLD fact atom"])
        for required_value in [row["Inventory id"], row["Entity type"], row["Entity name"]]:
            if normalize_fact_text(required_value) not in event_atom:
                raise ValueError(
                    f"HLD fact atom does not bind {row['Event id']} to Event system table.{required_value}"
                )
        for support_ref in split_list_refs(row["Supports"]):
            if support_ref in event_support_inventory_consumers:
                event_support_inventory_consumers[support_ref].add(row["Inventory id"])
    missing_event_inventory_design = sorted(
        row["Inventory id"]
        for row in inventory
        if row["Entity type"] == "event"
        and row["Required HLD owner"] == "artifact 06"
        and row["Inventory id"] not in event_rows_by_inventory_id
    )
    if missing_event_inventory_design:
        raise ValueError(f"missing event inventory design: {missing_event_inventory_design}")

    for support_row in support:
        if support_row["Required HLD owner"] != "artifact 04":
            continue
        obligations = {
            ref
            for ref in split_list_refs(support_row["Inventory obligations"])
            if not is_none_value(ref)
        }
        if not obligations:
            continue
        consumers = character_support_inventory_consumers.get(support_row["Support id"], set())
        missing_bound_consumers = sorted(obligations - consumers)
        if missing_bound_consumers:
            raise ValueError(
                f"support inventory obligation not consumed by bound character: "
                f"{support_row['Support id']} {missing_bound_consumers}"
            )
        unbound_consumers = sorted(consumers - obligations)
        if unbound_consumers:
            raise ValueError(
                f"support inventory obligation consumed by unbound character: "
                f"{support_row['Support id']} {unbound_consumers}"
            )

    for support_row in support:
        if support_row["Required HLD owner"] != "artifact 05":
            continue
        obligations = {
            ref
            for ref in split_list_refs(support_row["Inventory obligations"])
            if not is_none_value(ref)
        }
        if not obligations:
            continue
        consumers = environment_support_inventory_consumers.get(support_row["Support id"], set())
        missing_bound_consumers = sorted(obligations - consumers)
        if missing_bound_consumers:
            raise ValueError(
                f"support inventory obligation not consumed by bound environment: "
                f"{support_row['Support id']} {missing_bound_consumers}"
            )
        unbound_consumers = sorted(consumers - obligations)
        if unbound_consumers:
            raise ValueError(
                f"support inventory obligation consumed by unbound environment: "
                f"{support_row['Support id']} {unbound_consumers}"
            )

    for support_row in support:
        if support_row["Required HLD owner"] != "artifact 06":
            continue
        obligations = {
            ref
            for ref in split_list_refs(support_row["Inventory obligations"])
            if not is_none_value(ref)
        }
        if not obligations:
            continue
        consumers = event_support_inventory_consumers.get(support_row["Support id"], set())
        missing_bound_consumers = sorted(obligations - consumers)
        if missing_bound_consumers:
            raise ValueError(
                f"support inventory obligation not consumed by bound event: "
                f"{support_row['Support id']} {missing_bound_consumers}"
            )
        unbound_consumers = sorted(consumers - obligations)
        if unbound_consumers:
            raise ValueError(
                f"support inventory obligation consumed by unbound event: "
                f"{support_row['Support id']} {unbound_consumers}"
            )

    for row in parse_rows(artifact_texts["12"], "Artifact rubric coverage"):
        if row["Artifact"] != "Artifact 04":
            continue
        rubric_text = normalize_fact_text(
            f"{row['Good delivery evidence']} {row['Blocking failure check']}"
        )
        required_terms = ["concrete motive", "relationship target", "digital-life identity boundary"]
        if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 04 rubric missing character quality checks")
        break

    for row in parse_rows(artifact_texts["12"], "Artifact rubric coverage"):
        if row["Artifact"] != "Artifact 06":
            continue
        rubric_text = normalize_fact_text(
            f"{row['Good delivery evidence']} {row['Blocking failure check']}"
        )
        required_terms = [
            "event inventory",
            "causal-chain",
            "concrete event action",
            "consequence",
            "visibility",
            "environment integration",
            "source map",
        ]
        if any(term not in rubric_text for term in required_terms):
            raise ValueError("Artifact 06 rubric missing event quality checks")
        break

    environment_ids = {row["Environment id"] for row in environments}
    environment_by_id = {row["Environment id"]: row for row in environments}
    event_ids = {row["Event id"] for row in events}
    event_by_id = {row["Event id"]: row for row in events}
    predecessors_by_event_id: dict[str, set[str]] = {}
    for row in events:
        event_id = row["Event id"]
        if not EVENT_ID_PATTERN.fullmatch(event_id):
            raise ValueError(f"invalid event id: {event_id}")
        cause_refs = split_list_refs(row["Cause refs"])
        if not cause_refs or is_none_value(row["Cause refs"]):
            raise ValueError(f"missing event cause refs: {event_id}")
        predecessors: set[str] = set()
        source_refs = set(split_source_refs(row["Source"]))
        for cause_ref in cause_refs:
            if EVENT_ID_PATTERN.fullmatch(cause_ref):
                if cause_ref == event_id:
                    raise ValueError(f"self event predecessor: {event_id}")
                if cause_ref not in event_ids:
                    raise ValueError(f"unresolved event predecessor: {event_id} {cause_ref}")
                predecessors.add(cause_ref)
                continue
            validate_source_ref_values(cause_ref)
            if cause_ref not in source_refs:
                raise ValueError(f"event cause source mismatch: {event_id} {cause_ref}")
        if row["Event type"].casefold() != "trigger" and not predecessors:
            raise ValueError(f"missing event predecessor: {event_id}")
        predecessors_by_event_id[event_id] = predecessors
    validate_event_causal_graph(predecessors_by_event_id)
    event_environment_refs: set[str] = set()
    for row in events:
        validate_reference_list(row["Participants"], character_ids, "participant")
        if is_none_value(row["Environment refs"]):
            raise ValueError(f"missing event environment refs: {row['Event id']}")
        validate_reference_list(row["Environment refs"], environment_ids, "event environment")
        if is_none_value(row["Environment state change refs"]):
            raise ValueError(f"missing event environment state change refs: {row['Event id']}")
        referenced_environment_ids = split_list_refs(row["Environment refs"])
        expected_state_change_ids = {
            environment_by_id[environment_id]["State change id"]
            for environment_id in referenced_environment_ids
        }
        referenced_state_change_ids = split_list_refs(row["Environment state change refs"])
        if (
            len(referenced_state_change_ids) != len(set(referenced_state_change_ids))
            or set(referenced_state_change_ids) != expected_state_change_ids
        ):
            raise ValueError(f"event environment state change mismatch: {row['Event id']}")
        realizations = parse_environment_state_realizations(
            row["Environment state realizations"],
            row["Event id"],
        )
        if set(realizations) != expected_state_change_ids:
            raise ValueError(f"event environment state realization mismatch: {row['Event id']}")
        transitions = parse_environment_state_transitions(
            row["Environment state transitions"],
            row["Event id"],
        )
        if set(transitions) != expected_state_change_ids:
            raise ValueError(f"event environment state transition mismatch: {row['Event id']}")
        for environment_id in referenced_environment_ids:
            state_change_id = environment_by_id[environment_id]["State change id"]
            dimension, _ = realizations[state_change_id]
            if dimension != environment_by_id[environment_id]["State change dimension"]:
                raise ValueError(f"event environment state realization dimension mismatch: {row['Event id']}")
            if transitions[state_change_id] != (
                environment_by_id[environment_id]["State before"],
                environment_by_id[environment_id]["State after"],
            ):
                raise ValueError(f"event environment state transition mismatch: {row['Event id']}")
        event_environment_refs.update(referenced_environment_ids)
    missing_environment_event_integration = sorted(environment_ids - event_environment_refs)
    if missing_environment_event_integration:
        raise ValueError(f"missing environment event integration: {missing_environment_event_integration}")

    knowledge_labels = {"reader", "none"}
    information_trace_by_id = {
        trace_row["Fact trace id"]: trace_row
        for trace_row in parse_rows(artifact_texts["07"], "HLD Fact Trace")
        if trace_row.get("Fact trace id")
    }
    duplicate_information_inventory_ids = duplicate_values(information, "Inventory id")
    if duplicate_information_inventory_ids:
        raise ValueError(f"duplicate information inventory binding: {duplicate_information_inventory_ids}")
    information_by_id = {row["Info id"]: row for row in information}
    duplicate_information_boundary_ids = duplicate_values(information, "PRD information boundary id")
    if duplicate_information_boundary_ids:
        raise ValueError(f"duplicate PRD information boundary binding: {duplicate_information_boundary_ids}")
    information_inventory_ids: set[str] = set()
    for row in information:
        validate_information_quality_row(row)
        if not INFO_ID_PATTERN.fullmatch(row["Info id"]):
            raise ValueError(f"invalid information id: {row['Info id']}")
        inventory_row = inventory_by_id.get(row["Inventory id"])
        if not inventory_row or inventory_row["Entity type"] != "information object" or inventory_row["Required HLD owner"] != "artifact 07":
            raise ValueError(f"invalid information inventory binding: {row['Inventory id']}")
        if row["Entity type"] != inventory_row["Entity type"] or row["Entity name"] != inventory_row["Entity name"]:
            raise ValueError(f"information inventory identity mismatch: {row['Inventory id']}")
        if set(split_source_refs(row["Source"])) != set(split_source_refs(inventory_row["Source"])):
            raise ValueError(f"information inventory source mismatch: {row['Inventory id']}")
        info_trace = information_trace_by_id.get(row["Info id"])
        inventory_trace = inventory_trace_by_id.get(row["Inventory id"])
        if not info_trace or not inventory_trace or info_trace["Upstream fact id"] != inventory_trace["Upstream fact id"]:
            raise ValueError(f"missing information inventory design: {row['Inventory id']}")
        if normalize_fact_text(info_trace["Upstream fact atom"]) != normalize_fact_text(inventory_trace["Upstream fact atom"]):
            raise ValueError(f"information inventory upstream fact atom mismatch: {row['Inventory id']}")
        information_inventory_ids.add(row["Inventory id"])
        validate_reference_list(row["Known by"], character_ids, "known-by", knowledge_labels)
        validate_reference_list(row["Hidden from"], character_ids, "hidden-from", knowledge_labels)
        known_by = set(split_list_refs(row["Known by"])) - {"none"}
        hidden_from = set(split_list_refs(row["Hidden from"])) - {"none"}
        if not known_by and not hidden_from:
            raise ValueError(f"information knowledge state is empty: {row['Info id']}")
        if known_by & hidden_from:
            raise ValueError(f"information knowledge state overlaps: {row['Info id']}")
        story_anchor_refs = split_list_refs(row["Story anchor event ref"])
        if len(story_anchor_refs) != 1 or story_anchor_refs[0] not in event_ids:
            raise ValueError(f"unresolved information story anchor event: {row['Info id']}")
        reveal_event_refs = split_list_refs(row["Reveal event ref"])
        if len(reveal_event_refs) != 1 or reveal_event_refs[0] not in event_ids:
            raise ValueError(f"unresolved information reveal event: {row['Info id']}")
        reveal_event = event_by_id[reveal_event_refs[0]]
        if not event_precedes_or_equals(story_anchor_refs[0], reveal_event_refs[0], predecessors_by_event_id):
            raise ValueError(f"information story anchor occurs after reveal: {row['Info id']}")
        if normalize_fact_text(row["Reveal action"]) != normalize_fact_text(reveal_event["Event action"]):
            raise ValueError(f"information reveal action mismatch: {row['Info id']}")
        condition_refs = split_list_refs(row["Reveal condition refs"])
        if len(condition_refs) != 1:
            raise ValueError(f"invalid information reveal condition refs: {row['Info id']}")
        condition_ref = condition_refs[0]
        condition_type = row["Reveal condition type"]
        if condition_type == "action":
            if condition_ref != reveal_event_refs[0] or normalize_fact_text(row["Reveal condition"]) != normalize_fact_text(row["Reveal action"]):
                raise ValueError(f"information action reveal condition mismatch: {row['Info id']}")
        elif condition_type == "permission":
            validate_reference_list(condition_ref, character_ids, "information permission condition")
            if condition_ref not in split_list_refs(reveal_event["Participants"]):
                raise ValueError(f"information permission condition is not an event participant: {row['Info id']}")
            if normalize_fact_text(row["Reveal condition"]) != normalize_fact_text(character_by_id[condition_ref]["Information permission"]):
                raise ValueError(f"information permission reveal condition mismatch: {row['Info id']}")
        elif condition_type == "access":
            validate_reference_list(condition_ref, environment_ids, "information access condition")
            if condition_ref not in split_list_refs(reveal_event["Environment refs"]):
                raise ValueError(f"information access condition is not an event environment: {row['Info id']}")
            state_change_id = environment_by_id[condition_ref]["State change id"]
            realization = parse_environment_state_realizations(
                reveal_event["Environment state realizations"],
                reveal_event["Event id"],
            )[state_change_id][1]
            if normalize_fact_text(row["Reveal condition"]) != normalize_fact_text(realization):
                raise ValueError(f"information access reveal condition mismatch: {row['Info id']}")
        else:
            validate_reference_list(condition_ref, event_ids, "information evidence condition")
            if not event_precedes_or_equals(condition_ref, reveal_event_refs[0], predecessors_by_event_id):
                raise ValueError(f"information evidence condition occurs after reveal: {row['Info id']}")
            if normalize_fact_text(row["Reveal condition"]) != normalize_fact_text(event_by_id[condition_ref]["Consequences"]):
                raise ValueError(f"information evidence reveal condition mismatch: {row['Info id']}")
    missing_information_inventory_ids = sorted(
        inventory_row["Inventory id"]
        for inventory_row in inventory
        if inventory_row["Entity type"] == "information object"
        and inventory_row["Required HLD owner"] == "artifact 07"
        and inventory_row["Inventory id"] not in information_inventory_ids
    )
    if missing_information_inventory_ids:
        raise ValueError(f"missing information inventory design: {missing_information_inventory_ids}")
    reveal_phases = {
        info_id: reveal_phase_number(row["Narrative reveal phase"])
        for info_id, row in information_by_id.items()
    }
    expected_reveal_phases = set(range(1, max(reveal_phases.values()) + 1))
    if set(reveal_phases.values()) != expected_reveal_phases:
        raise ValueError("information narrative reveal phases are not contiguous")
    predecessors_by_info_id: dict[str, set[str]] = {}
    for info_id, row in information_by_id.items():
        predecessor_refs = [] if is_none_value(row["Reveal predecessor refs"]) else split_list_refs(row["Reveal predecessor refs"])
        if len(predecessor_refs) != len(set(predecessor_refs)):
            raise ValueError(f"duplicate information reveal predecessor: {info_id}")
        predecessors = set(predecessor_refs)
        if info_id in predecessors:
            raise ValueError(f"self information reveal predecessor: {info_id}")
        unresolved_predecessors = predecessors - set(information_by_id)
        if unresolved_predecessors:
            raise ValueError(f"unresolved information reveal predecessor: {info_id} {sorted(unresolved_predecessors)}")
        if any(reveal_phases[predecessor_id] >= reveal_phases[info_id] for predecessor_id in predecessors):
            raise ValueError(f"information reveal predecessor phase mismatch: {info_id}")
        predecessors_by_info_id[info_id] = predecessors
    validate_information_predecessor_graph(predecessors_by_info_id)
    validate_information_tier_dependencies(information_by_id, predecessors_by_info_id)
    validate_thread_system_rows(
        threads,
        event_ids,
        info_ids,
        {row["Support id"]: row for row in support},
        {row["Rule id"] for row in rules},
        {row["Character id"] for row in characters},
    )
    validate_style_pov_rows(
        style,
        information_by_id,
        thread_ids,
        {normalize_fact_text(row["Entity name"]) for row in characters},
    )

    for row in style:
        validate_reference_list(row["Supports"], support_ids | info_ids | thread_ids, "style support")

    inventory_amendment_ids = {
        amendment_id
        for row in inventory
        for amendment_id in [inventory_amendment_id(row["Initial status"])]
        if amendment_id
    }
    reconciliation_trace_by_id = {
        row["Fact trace id"]: row
        for row in parse_rows(artifact_texts["10"], "HLD Fact Trace")
        if row.get("Fact trace id")
    }
    inventory_by_id = {row["Inventory id"]: row for row in inventory}
    expected_subjects = inventory_ids | amendment_ids | inventory_amendment_ids
    reconciliation_subjects: dict[str, dict[str, str]] = {}
    reconciliation_request_ids: set[str] = set()
    minted_final_inventory_ids: set[str] = set()
    for row in reconciliation:
        initial_inventory_id = row["Initial inventory id"]
        if initial_inventory_id in reconciliation_subjects:
            raise ValueError(f"duplicate final inventory disposition: {initial_inventory_id}")
        reconciliation_subjects[initial_inventory_id] = row
        request_id = row["Request id"]
        if not RECONCILIATION_REQUEST_ID_PATTERN.fullmatch(request_id) or request_id in reconciliation_request_ids:
            raise ValueError(f"invalid or duplicate reconciliation request id: {request_id}")
        reconciliation_request_ids.add(request_id)
        if initial_inventory_id not in expected_subjects:
            raise ValueError(f"unexpected reconciliation subject: {initial_inventory_id}")
        if row["Decision"] not in RECONCILIATION_DECISIONS:
            raise ValueError(f"invalid reconciliation decision: {row['Decision']}")
        validate_source_ref_values(row["Source"])
        trace = reconciliation_trace_by_id.get(initial_inventory_id)
        if not trace:
            raise ValueError(f"missing reconciliation fact trace: {initial_inventory_id}")
        if initial_inventory_id in inventory_by_id:
            inventory_row = inventory_by_id[initial_inventory_id]
            for column in ["Entity name", "Entity type", "Required HLD owner"]:
                if row[column] != inventory_row[column]:
                    raise ValueError(f"reconciliation inventory identity mismatch: {initial_inventory_id} {column}")
            if row["Requested by artifact"] != inventory_row["Required HLD owner"]:
                raise ValueError(f"reconciliation inventory requester mismatch: {initial_inventory_id}")
            if set(split_source_refs(row["Source"])) != set(split_source_refs(inventory_row["Source"])):
                raise ValueError(f"reconciliation inventory source mismatch: {initial_inventory_id}")
            inventory_trace = inventory_trace_by_id.get(initial_inventory_id)
            if not inventory_trace or (
                trace["Upstream fact id"] != inventory_trace["Upstream fact id"]
                or normalize_fact_text(trace["Upstream fact atom"])
                != normalize_fact_text(inventory_trace["Upstream fact atom"])
                or set(split_source_refs(trace["Source refs"])) != set(split_source_refs(inventory_trace["Source refs"]))
            ):
                raise ValueError(f"reconciliation inventory fact trace mismatch: {initial_inventory_id}")
        else:
            origins = amendment_origins.get(initial_inventory_id)
            if not origins:
                raise ValueError(f"unexpected reconciliation subject: {initial_inventory_id}")
            origin_artifact, _, origin_source, origin_trace = origins[0]
            if row["Requested by artifact"] != origin_artifact:
                raise ValueError(f"reconciliation amendment requester mismatch: {initial_inventory_id}")
            if set(split_source_refs(row["Source"])) != set(split_source_refs(origin_source)):
                raise ValueError(f"reconciliation amendment source mismatch: {initial_inventory_id}")
            if row["Entity type"] != "unresolved amendment" or row["Required HLD owner"] != "artifact 10":
                raise ValueError(f"reconciliation amendment identity mismatch: {initial_inventory_id}")
            validate_reconciliation_amendment_trace(origin_trace, trace, initial_inventory_id)
        decision = row["Decision"]
        canonical_subject_id = row["Canonical subject id"]
        if decision == "accept":
            if initial_inventory_id not in inventory_by_id:
                raise ValueError(f"amendment acceptance requires upstream rerun: {initial_inventory_id}")
            if not is_none_value(canonical_subject_id):
                raise ValueError(f"accepted reconciliation must not name canonical subject: {initial_inventory_id}")
            validate_inventory_ref_value(row["Final inventory id"])
            final_id = row["Final inventory id"]
            if final_id in minted_final_inventory_ids:
                raise ValueError(f"duplicate final inventory id: {final_id}")
            minted_final_inventory_ids.add(final_id)
        elif decision == "merge":
            if initial_inventory_id not in inventory_by_id:
                raise ValueError(f"amendment cannot merge into inventory: {initial_inventory_id}")
            if is_none_value(canonical_subject_id):
                raise ValueError(f"merge reconciliation requires canonical subject: {initial_inventory_id}")
            if not is_none_value(row["Final inventory id"]):
                raise ValueError("merge reconciliation must not mint final inventory id")
        else:
            if not is_none_value(canonical_subject_id):
                raise ValueError(f"non-merge reconciliation must not name canonical subject: {initial_inventory_id}")
            if not is_none_value(row["Final inventory id"]):
                raise ValueError("rejected or blocked reconciliation must not mint final inventory id")
    missing_final_disposition = sorted(inventory_ids - set(reconciliation_subjects))
    if missing_final_disposition:
        raise ValueError(f"missing final inventory disposition: {missing_final_disposition}")
    missing_design_amendment_disposition = sorted(amendment_ids - set(reconciliation_subjects))
    if missing_design_amendment_disposition:
        raise ValueError(f"unclosed amendment request: {missing_design_amendment_disposition}")
    unresolved_design_amendment_disposition = sorted(
        amendment_id
        for amendment_id in amendment_ids
        if reconciliation_subjects[amendment_id]["Decision"] != "reject"
    )
    if unresolved_design_amendment_disposition:
        raise ValueError(f"unclosed amendment request: {unresolved_design_amendment_disposition}")
    missing_amendment_disposition = sorted(inventory_amendment_ids - set(reconciliation_subjects))
    if missing_amendment_disposition:
        raise ValueError(f"missing final amendment disposition: {missing_amendment_disposition}")

    resolved_final_inventory_ids = {
        subject_id: row["Final inventory id"]
        for subject_id, row in reconciliation_subjects.items()
        if row["Decision"] == "accept"
    }
    for subject_id, row in reconciliation_subjects.items():
        if row["Decision"] != "merge":
            continue
        canonical_subject_id = row["Canonical subject id"]
        canonical_row = reconciliation_subjects.get(canonical_subject_id)
        if not canonical_row or canonical_row["Decision"] != "accept":
            raise ValueError(f"merge reconciliation has unresolved canonical subject: {subject_id}")
        for column in ["Entity name", "Entity type", "Required HLD owner"]:
            if row[column] != canonical_row[column]:
                raise ValueError(f"merge reconciliation identity mismatch: {subject_id} {column}")
        resolved_final_inventory_ids[subject_id] = canonical_row["Final inventory id"]

    accepted_subject_by_final_id = {
        row["Final inventory id"]: subject_id
        for subject_id, row in reconciliation_subjects.items()
        if row["Decision"] == "accept"
    }

    source_map_rows = parse_rows(artifact_texts["11"], "HLD Source Map")
    for row in source_map_rows:
        final_id = row["Final inventory id"]
        if is_none_value(final_id):
            if row["Owner artifact"] not in {"artifact 03", "artifact 08", "artifact 09"}:
                raise ValueError(f"Source Map inventory-bound fact lacks final inventory id: {row['HLD fact id']}")
            continue
        if final_id not in minted_final_inventory_ids:
            raise ValueError(f"unresolved final inventory id: {final_id}")
        subject_id = accepted_subject_by_final_id[final_id]
        reconciliation_row = reconciliation_subjects[subject_id]
        reconciliation_trace = reconciliation_trace_by_id[subject_id]
        if row["Owner artifact"] != reconciliation_row["Required HLD owner"]:
            raise ValueError(f"Source Map reconciliation owner mismatch: {row['HLD fact id']}")
        if set(split_source_refs(row["Source refs"])) != set(split_source_refs(reconciliation_row["Source"])):
            raise ValueError(f"Source Map reconciliation source mismatch: {row['HLD fact id']}")
        if (
            row["Upstream fact id"] != reconciliation_trace["Upstream fact id"]
            or normalize_fact_text(row["Upstream fact atom"])
            != normalize_fact_text(reconciliation_trace["Upstream fact atom"])
        ):
            raise ValueError(f"Source Map reconciliation fact mismatch: {row['HLD fact id']}")

    validate_design_fact_source_map_coverage(
        artifact_texts,
        source_map_rows,
        resolved_final_inventory_ids,
    )
    validate_reconciliation_closure_checks(artifact_texts, reconciliation)

    environment_source_map_ids: dict[str, str] = {}
    for environment_row in environments:
        inventory_id = environment_row["Inventory id"]
        environment_trace = environment_trace_by_id[environment_row["Environment id"]]
        final_inventory_id = resolved_final_inventory_ids.get(inventory_id)
        if not final_inventory_id:
            raise ValueError(f"unresolved environment inventory disposition: {inventory_id}")
        matching_source_map_rows = [
            row
            for row in source_map_rows
            if row["Owner artifact"] == "artifact 05"
            and row["Upstream fact id"] == environment_trace["Upstream fact id"]
            and normalize_fact_text(row["Upstream fact atom"]) == normalize_fact_text(environment_trace["Upstream fact atom"])
            and normalize_fact_text(row["HLD fact atom"]) == normalize_fact_text(environment_trace["HLD fact atom"])
            and set(split_source_refs(row["Source refs"])) == set(split_source_refs(environment_trace["Source refs"]))
            and row["Final inventory id"] == final_inventory_id
            and row["LLD handoff target"] == environment_row["LLD handoff"]
        ]
        if len(matching_source_map_rows) != 1:
            raise ValueError(
                f"missing environment Source Map closure: {environment_row['Environment id']} "
                f"expected 1 mapping, found {len(matching_source_map_rows)}"
            )
        environment_source_map_ids[environment_row["Environment id"]] = matching_source_map_rows[0]["HLD fact id"]

    event_source_map_ids: dict[str, str] = {}
    for event_row in events:
        inventory_id = event_row["Inventory id"]
        event_trace = event_trace_by_id[event_row["Event id"]]
        final_inventory_id = resolved_final_inventory_ids.get(inventory_id)
        if not final_inventory_id:
            raise ValueError(f"unresolved event inventory disposition: {inventory_id}")
        matching_source_map_rows = [
            row
            for row in source_map_rows
            if row["Owner artifact"] == "artifact 06"
            and row["Upstream fact id"] == event_trace["Upstream fact id"]
            and normalize_fact_text(row["Upstream fact atom"]) == normalize_fact_text(event_trace["Upstream fact atom"])
            and normalize_fact_text(row["HLD fact atom"]) == normalize_fact_text(event_trace["HLD fact atom"])
            and set(split_source_refs(row["Source refs"])) == set(split_source_refs(event_trace["Source refs"]))
            and row["Final inventory id"] == final_inventory_id
            and row["LLD handoff target"] == event_row["LLD handoff"]
        ]
        if len(matching_source_map_rows) != 1:
            raise ValueError(
                f"missing event Source Map closure: {event_row['Event id']} "
                f"expected 1 mapping, found {len(matching_source_map_rows)}"
            )
        event_source_map_ids[event_row["Event id"]] = matching_source_map_rows[0]["HLD fact id"]

    information_source_map_ids: dict[str, str] = {}
    for information_row in information:
        information_trace = information_trace_by_id[information_row["Info id"]]
        final_inventory_id = resolved_final_inventory_ids.get(information_row["Inventory id"])
        if not final_inventory_id:
            raise ValueError(f"unresolved information inventory disposition: {information_row['Inventory id']}")
        matching_source_map_rows = [
            row for row in source_map_rows
            if row["Owner artifact"] == "artifact 07"
            and row["Upstream fact id"] == information_trace["Upstream fact id"]
            and normalize_fact_text(row["Upstream fact atom"]) == normalize_fact_text(information_trace["Upstream fact atom"])
            and normalize_fact_text(row["HLD fact atom"]) == normalize_fact_text(information_trace["HLD fact atom"])
            and set(split_source_refs(row["Source refs"])) == set(split_source_refs(information_trace["Source refs"]))
            and row["Final inventory id"] == final_inventory_id
            and row["LLD handoff target"] == information_row["LLD handoff"]
        ]
        if len(matching_source_map_rows) != 1:
            raise ValueError(f"missing information Source Map closure: {information_row['Info id']}")
        information_source_map_ids[information_row["Info id"]] = matching_source_map_rows[0]["HLD fact id"]

    closure_rows = validate_required_columns(
        artifact_texts["12"],
        "Environment closure checks",
        ENVIRONMENT_CLOSURE_CHECK_COLUMNS,
    )
    closure_rows_by_environment_id = {row["Environment id"]: row for row in closure_rows}
    duplicate_closure_environment_ids = duplicate_values(closure_rows, "Environment id")
    if duplicate_closure_environment_ids:
        raise ValueError(f"duplicate environment closure check: {duplicate_closure_environment_ids}")
    missing_closure_environment_ids = sorted(environment_ids - set(closure_rows_by_environment_id))
    if missing_closure_environment_ids:
        raise ValueError(f"missing environment closure check: {missing_closure_environment_ids}")
    unexpected_closure_environment_ids = sorted(set(closure_rows_by_environment_id) - environment_ids)
    if unexpected_closure_environment_ids:
        raise ValueError(f"unresolved environment closure check: {unexpected_closure_environment_ids}")
    for environment_id, environment_row in environment_by_id.items():
        closure_row = closure_rows_by_environment_id[environment_id]
        if closure_row["Inventory id"] != environment_row["Inventory id"]:
            raise ValueError(f"environment closure inventory mismatch: {environment_id}")
        if closure_row["State change id"] != environment_row["State change id"]:
            raise ValueError(f"environment closure state change mismatch: {environment_id}")
        if closure_row["State change dimension"] != environment_row["State change dimension"]:
            raise ValueError(f"environment closure state change dimension mismatch: {environment_id}")
        if closure_row["State before"] != environment_row["State before"]:
            raise ValueError(f"environment closure state before mismatch: {environment_id}")
        if closure_row["State after"] != environment_row["State after"]:
            raise ValueError(f"environment closure state after mismatch: {environment_id}")
        expected_event_ids = {
            event_row["Event id"]
            for event_row in events
            if environment_id in split_list_refs(event_row["Environment refs"])
        }
        event_ids = split_list_refs(closure_row["Event ids"])
        if not event_ids or is_none_value(closure_row["Event ids"]) or set(event_ids) != expected_event_ids:
            raise ValueError(f"environment closure event mismatch: {environment_id}")
        expected_transition_refs = {
            f"{event_id}:{environment_row['State change id']}:"
            f"{environment_row['State before']}=>{environment_row['State after']}"
            for event_id in expected_event_ids
        }
        actual_transition_refs = set(split_list_refs(closure_row["Event state transition refs"]))
        if actual_transition_refs != expected_transition_refs:
            raise ValueError(f"environment closure transition mismatch: {environment_id}")
        expected_realization_refs = {
            f"{event_id}:{environment_row['State change id']}"
            for event_id in expected_event_ids
        }
        actual_realization_refs = set(split_list_refs(closure_row["Event state realization refs"]))
        if actual_realization_refs != expected_realization_refs:
            raise ValueError(f"environment closure realization mismatch: {environment_id}")
        if closure_row["Source Map HLD fact id"] != environment_source_map_ids[environment_id]:
            raise ValueError(f"environment closure Source Map mismatch: {environment_id}")
        evidence = normalize_fact_text(closure_row["Evidence"])
        evidence_markers = [
            "function=",
            "spatial=",
            "transition=",
            "realization=",
            f"before={normalize_fact_text(environment_row['State before'])}",
            f"after={normalize_fact_text(environment_row['State after'])}",
        ]
        if is_none_value(evidence) or any(marker not in evidence for marker in evidence_markers):
            raise ValueError(f"environment closure missing evidence: {environment_id}")
        if closure_row["Verdict"] != "pass":
            raise ValueError(f"environment closure contains non-pass verdict: {environment_id}")

    event_closure_rows = validate_required_columns(
        artifact_texts["12"],
        "Event closure checks",
        EVENT_CLOSURE_CHECK_COLUMNS,
    )
    event_closure_by_id = {row["Event id"]: row for row in event_closure_rows}
    duplicate_event_closure_ids = duplicate_values(event_closure_rows, "Event id")
    if duplicate_event_closure_ids:
        raise ValueError(f"duplicate event closure check: {duplicate_event_closure_ids}")
    missing_event_closure_ids = sorted(set(event_by_id) - set(event_closure_by_id))
    if missing_event_closure_ids:
        raise ValueError(f"missing event closure check: {missing_event_closure_ids}")
    unexpected_event_closure_ids = sorted(set(event_closure_by_id) - set(event_by_id))
    if unexpected_event_closure_ids:
        raise ValueError(f"unresolved event closure check: {unexpected_event_closure_ids}")
    event_by_id = {row["Event id"]: row for row in events}
    for event_id, event_row in event_by_id.items():
        closure_row = event_closure_by_id[event_id]
        for column in ["Inventory id", "Cause refs", "Event action", "Causal role", "Consequences"]:
            if closure_row[column] != event_row[column]:
                raise ValueError(f"event closure {column.casefold()} mismatch: {event_id}")
        if closure_row["Environment state change refs"] != event_row["Environment state change refs"]:
            raise ValueError(f"event closure environment state mismatch: {event_id}")
        if closure_row["Event fact id"] != event_source_map_ids[event_id]:
            raise ValueError(f"event closure Source Map mismatch: {event_id}")
        evidence = normalize_fact_text(closure_row["Event closure evidence"])
        evidence_markers = ["cause=", "action=", "role=", "consequence=", "environment="]
        if is_none_value(evidence) or any(marker not in evidence for marker in evidence_markers):
            raise ValueError(f"event closure missing evidence: {event_id}")
        if closure_row["Verdict"] != "pass":
            raise ValueError(f"event closure contains non-pass verdict: {event_id}")


    validate_information_closure_checks(artifact_texts, information, information_source_map_ids)


def validate_information_closure_checks(
    artifact_texts: dict[str, str],
    information: list[dict[str, str]],
    information_source_map_ids: dict[str, str],
) -> None:
    rows = validate_required_columns(
        artifact_texts["12"], "Information closure checks", INFORMATION_CLOSURE_CHECK_COLUMNS,
    )
    by_id = {row["Info id"]: row for row in rows}
    information_by_id = {row["Info id"]: row for row in information}
    if duplicate_values(rows, "Info id") or set(by_id) != set(information_by_id):
        raise ValueError("information closure coverage mismatch")
    for info_id, information_row in information_by_id.items():
        closure = by_id[info_id]
        for column in [
            "Inventory id",
            "PRD information boundary id",
            "Freeze refs",
            "Story anchor event ref",
            "Time layer",
            "Narrative reveal phase",
            "Disclosure tier",
            "Known by",
            "Hidden from",
            "Reveal predecessor refs",
            "Reveal event ref",
            "Reveal action",
            "Reveal condition type",
            "Reveal condition refs",
            "Reveal condition",
        ]:
            if closure[column] != information_row[column]:
                raise ValueError(f"information closure {column.casefold()} mismatch: {info_id}")
        if closure["Information fact id"] != information_source_map_ids[info_id]:
            raise ValueError(f"information closure Source Map mismatch: {info_id}")
        evidence = normalize_fact_text(closure["Information closure evidence"])
        evidence_markers = [
            "boundary=", "freeze=", "anchor=", "layer=", "phase=", "tier=", "knowledge=", "predecessor=",
            "reveal=", "action=", "condition_type=", "condition_ref=", "condition=",
        ]
        if is_none_value(evidence) or any(marker not in evidence for marker in evidence_markers):
            raise ValueError(f"information closure missing evidence: {info_id}")
        if closure["Verdict"] != "pass":
            raise ValueError(f"information closure contains non-pass verdict: {info_id}")


def validate_reconciliation_closure_checks(
    artifact_texts: dict[str, str],
    reconciliation: list[dict[str, str]],
) -> None:
    rows = validate_required_columns(
        artifact_texts["12"],
        "Reconciliation closure checks",
        RECONCILIATION_CLOSURE_CHECK_COLUMNS,
    )
    by_subject = {row["Initial inventory id"]: row for row in rows}
    expected_subjects = {row["Initial inventory id"] for row in reconciliation}
    if duplicate_values(rows, "Initial inventory id") or set(by_subject) != expected_subjects:
        raise ValueError("reconciliation closure coverage mismatch")
    for reconciliation_row in reconciliation:
        subject_id = reconciliation_row["Initial inventory id"]
        closure = by_subject[subject_id]
        for column in ["Request id", "Decision", "Canonical subject id", "Final inventory id"]:
            if closure[column] != reconciliation_row[column]:
                raise ValueError(f"reconciliation closure {column.casefold()} mismatch: {subject_id}")
        if closure["Origin artifact"] != reconciliation_row["Requested by artifact"]:
            raise ValueError(f"reconciliation closure origin artifact mismatch: {subject_id}")
        if set(split_source_refs(closure["Origin source refs"])) != set(split_source_refs(reconciliation_row["Source"])):
            raise ValueError(f"reconciliation closure origin source mismatch: {subject_id}")
        if closure["Origin fact trace id"] != subject_id:
            raise ValueError(f"reconciliation closure fact trace mismatch: {subject_id}")
        if is_none_value(closure["Evidence"]) or closure["Verdict"] != "pass":
            raise ValueError(f"reconciliation closure contains non-pass verdict: {subject_id}")


def validate_thread_closure_checks(artifact_texts: dict[str, str]) -> None:
    threads = parse_rows(artifact_texts["08"], "Thread system table")
    required_threads = {
        row["Thread id"]: row
        for row in threads
        if row["Thread type"].casefold() in REQUIRED_CORE_THREAD_TYPES
    }
    rows = validate_required_columns(
        artifact_texts["12"], "Thread closure checks", THREAD_CLOSURE_CHECK_COLUMNS,
    )
    by_id = {row["Thread id"]: row for row in rows}
    if duplicate_values(rows, "Thread id") or set(by_id) != set(required_threads):
        raise ValueError("thread closure coverage mismatch")
    for thread_id, thread in required_threads.items():
        closure = by_id[thread_id]
        for column in [
            "Thread type",
            "Thread function",
            "Thread anchor refs",
            "Required pressure refs",
            "Thread progression",
            "Crossover",
            "Closure outcome",
        ]:
            if closure[column] != thread[column]:
                raise ValueError(f"thread closure {column.casefold()} mismatch: {thread_id}")
        evidence = normalize_fact_text(closure["Evidence"])
        evidence_markers = ["function=", "anchors=", "pressure=", "progression=", "crossover=", "closure="]
        if is_none_value(evidence) or any(marker not in evidence for marker in evidence_markers):
            raise ValueError(f"thread closure missing evidence: {thread_id}")
        if closure["Verdict"] != "pass":
            raise ValueError(f"thread closure contains non-pass verdict: {thread_id}")


def validate_style_pov_closure_checks(artifact_texts: dict[str, str]) -> None:
    style_rows = parse_rows(artifact_texts["09"], "Style and POV table")
    rows = validate_required_columns(
        artifact_texts["12"], "Style/POV closure checks", STYLE_POV_CLOSURE_CHECK_COLUMNS,
    )
    style_by_id = {row["Style/POV id"]: row for row in style_rows}
    closure_by_id = {row["Style/POV id"]: row for row in rows}
    if duplicate_values(rows, "Style/POV id") or set(closure_by_id) != set(style_by_id):
        raise ValueError("Style/POV closure coverage mismatch")
    for style_id, style in style_by_id.items():
        closure = closure_by_id[style_id]
        for column in [
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
        ]:
            if closure[column] != style[column]:
                raise ValueError(f"Style/POV closure {column.casefold()} mismatch: {style_id}")
        evidence = normalize_fact_text(closure["Evidence"])
        evidence_markers = ["policy=", "information=", "thread=", "reader=", "language=", "design=", "permission=", "prohibition=", "handoff="]
        if is_none_value(evidence) or any(marker not in evidence for marker in evidence_markers):
            raise ValueError(f"Style/POV closure missing evidence: {style_id}")
        if closure["Verdict"] != "pass":
            raise ValueError(f"Style/POV closure contains non-pass verdict: {style_id}")


def validate_hld_artifact_trace_binding(artifact_text: str, business_heading: str, id_column: str) -> None:
    business_rows = parse_rows(artifact_text, business_heading)
    trace_rows = parse_rows(artifact_text, "HLD Fact Trace")
    duplicate_business_ids = duplicate_values(business_rows, id_column)
    if duplicate_business_ids:
        raise ValueError(f"duplicate {business_heading} id: {duplicate_business_ids}")
    duplicate_trace_ids = duplicate_values(trace_rows, "Fact trace id")
    if duplicate_trace_ids:
        raise ValueError(f"duplicate fact trace id: {duplicate_trace_ids}")
    business_by_id = {row[id_column]: row for row in business_rows if row.get(id_column)}
    trace_by_id = {row["Fact trace id"]: row for row in trace_rows if row.get("Fact trace id")}
    business_ids = set(business_by_id)
    trace_ids = set(trace_by_id)
    missing = business_ids - trace_ids
    if missing:
        raise ValueError(f"missing fact trace coverage: {sorted(missing)}")
    orphaned = trace_ids - business_ids
    if orphaned:
        raise ValueError(f"orphan fact trace rows: {sorted(orphaned)}")
    for row in trace_rows:
        for column in ["Upstream fact id", "Upstream fact atom", "HLD fact atom", "Source refs", "Expansion mode", "Support mechanism", "Preservation status"]:
            if not row.get(column):
                raise ValueError(f"HLD Fact Trace row missing {column}")
        upstream_fact_id = row["Upstream fact id"]
        if not is_none_value(upstream_fact_id) and not UPSTREAM_FACT_ID_PATTERN.fullmatch(upstream_fact_id):
            raise ValueError(f"invalid upstream fact id: {upstream_fact_id}")
        validate_source_ref_values(row["Source refs"])
        if row["Expansion mode"] not in EXPANSION_MODES:
            raise ValueError(f"invalid expansion mode: {row['Expansion mode']}")
        if row["Preservation status"] not in VALID_PRESERVATION:
            raise ValueError(f"invalid preservation status: {row['Preservation status']}")
        business_row = business_by_id[row["Fact trace id"]]
        if "Source" in business_row:
            business_source_refs = set(split_source_refs(business_row["Source"]))
            trace_source_refs = set(split_source_refs(row["Source refs"]))
            if business_source_refs != trace_source_refs:
                raise ValueError(f"fact trace source mismatch: {row['Fact trace id']}")
        hld_atom = normalize_fact_text(row["HLD fact atom"])
        for column in FACT_ATOM_COLUMNS_BY_HEADING.get(business_heading, []):
            value = business_row.get(column, "").strip()
            if value and value.lower() != "none" and normalize_fact_text(value) not in hld_atom:
                raise ValueError(
                    f"HLD fact atom does not bind {row['Fact trace id']} to {business_heading}.{column}"
                )


def validate_skill_verdict_output(artifact_text: str) -> None:
    values = parse_field_value_section(artifact_text, "Skill Verdict")
    required = {
        "Skill quality verdict",
        "Source closure",
        "Inventory coverage",
        "Boundary obedience",
        "Downstream readiness",
        "Blocking issue",
        "Rerun target",
    }
    missing = required - set(values)
    if missing:
        raise ValueError(f"invalid Skill Verdict missing fields: {sorted(missing)}")
    checks = [
        values["Skill quality verdict"] in {"pass", "pass_with_p2", "fail"},
        values["Source closure"] == "closed" or values["Source closure"].startswith("open:"),
        values["Inventory coverage"] in {"closed", "not_applicable"} or values["Inventory coverage"].startswith("open:"),
        values["Boundary obedience"] == "pass" or values["Boundary obedience"].startswith("violation:"),
        values["Downstream readiness"] == "ready" or values["Downstream readiness"].startswith("blocked:") or values["Downstream readiness"].startswith("reopen_upstream:"),
        bool(values["Blocking issue"]),
        bool(values["Rerun target"]),
    ]
    if not all(checks):
        raise ValueError("invalid Skill Verdict values")
    has_blocking_state = (
        values["Source closure"].startswith(BLOCKING_VERDICT_PREFIXES)
        or values["Inventory coverage"].startswith("open:")
        or values["Boundary obedience"].startswith("violation:")
        or values["Downstream readiness"].startswith(("blocked:", "reopen_upstream:"))
    )
    if values["Skill quality verdict"] == "fail":
        has_blocking_state = True
    blocking_issue = values["Blocking issue"]
    rerun_target = values["Rerun target"]
    if values["Skill quality verdict"] in {"pass", "pass_with_p2"} and not has_blocking_state:
        if blocking_issue != "none" or rerun_target != "none":
            raise ValueError("pass verdict cannot carry blocking issue or rerun target")
    if has_blocking_state:
        if values["Skill quality verdict"] != "fail":
            raise ValueError("blocking state requires fail Skill quality verdict")
        if blocking_issue == "none" or rerun_target == "none":
            raise ValueError("blocking verdict must name blocking issue and rerun target")


def validate_artifact_metadata(artifact_text: str, artifact: dict) -> None:
    metadata = parse_field_value_section(artifact_text, "Artifact Metadata")
    required = {
        "Artifact id",
        "Owner skill",
        "Run id",
        "Upstream package",
        "Input artifacts",
        "Output path",
        "Version",
    }
    missing = required - set(metadata)
    if missing:
        raise ValueError(f"Artifact Metadata missing fields: {sorted(missing)}")
    if metadata["Artifact id"] != artifact["id"]:
        raise ValueError(f"Artifact Metadata id mismatch for artifact {artifact['id']}")
    if metadata["Owner skill"] != artifact["skill"]:
        raise ValueError(f"Artifact Metadata owner mismatch for artifact {artifact['id']}")
    empty = [field for field in required if not metadata.get(field)]
    if empty:
        raise ValueError(f"Artifact Metadata empty fields: {sorted(empty)}")


def validate_skill_preservation_status_terms(contract: dict, skill: str, text: str) -> None:
    match = re.search(r"Preservation status must (?:state|be one of)\s+([^\n.]+)", text)
    if not match:
        raise ValueError(f"{skill} must declare Preservation status allowed values")
    declaration = match.group(1).casefold()
    invalid_terms = {"unsupported", "contradiction", "replacement", "reinterpretation", "unsupported expansion"}
    bad_terms = sorted(term for term in invalid_terms if term in declaration)
    if bad_terms:
        raise ValueError(f"{skill} declares invalid preservation status values: {bad_terms}")
    missing = sorted(status for status in VALID_PRESERVATION if status not in declaration)
    if missing:
        raise ValueError(f"{skill} missing valid preservation statuses: {missing}")


def reconciliation_resolved_final_ids(reconciliation_text: str) -> dict[str, str]:
    rows = parse_rows(reconciliation_text, "Final inventory reconciliation table")
    by_subject = {row["Initial inventory id"]: row for row in rows}
    resolved = {
        subject_id: row["Final inventory id"]
        for subject_id, row in by_subject.items()
        if row["Decision"] == "accept"
    }
    for subject_id, row in by_subject.items():
        if row["Decision"] != "merge":
            continue
        canonical = by_subject.get(row["Canonical subject id"])
        if canonical and canonical["Decision"] == "accept":
            resolved[subject_id] = canonical["Final inventory id"]
    return resolved


def validate_reconciliation_continuity(
    previous_reconciliation_text: str,
    current_reconciliation_text: str,
) -> None:
    previous_resolved = reconciliation_resolved_final_ids(previous_reconciliation_text)
    current_resolved = reconciliation_resolved_final_ids(current_reconciliation_text)
    for subject_id in sorted(set(previous_resolved) & set(current_resolved)):
        if previous_resolved[subject_id] != current_resolved[subject_id]:
            raise ValueError(f"reconciliation final inventory id changed: {subject_id}")


def validate_reconciliation_mode(
    reconciliation_text: str,
    previous_reconciliation_text: str | None,
) -> None:
    metadata = parse_field_value_section(reconciliation_text, "Artifact Metadata")
    mode = metadata.get("Reconciliation mode", "bootstrap")
    expected_digest = metadata.get("Previous reconciliation SHA256", "none")
    if mode == "bootstrap":
        if previous_reconciliation_text is not None or expected_digest != "none":
            raise ValueError("bootstrap reconciliation must not declare previous artifact")
        return
    if mode != "continuity":
        raise ValueError(f"invalid reconciliation mode: {mode}")
    if previous_reconciliation_text is None:
        raise ValueError("continuity reconciliation requires previous artifact")
    actual_digest = hashlib.sha256(previous_reconciliation_text.encode("utf-8")).hexdigest()
    if expected_digest != actual_digest:
        raise ValueError("continuity reconciliation previous artifact digest mismatch")


def validate_hld_artifact_package(
    contract: dict,
    artifact_texts: dict[str, str],
    upstream_text: str | list[str] | None = None,
    prd_boundary_sources: dict[str, str] | None = None,
    previous_reconciliation_text: str | None = None,
) -> None:
    required = [artifact for artifact in contract["artifacts"] if artifact.get("skill")]
    missing = [artifact["id"] for artifact in required if artifact["id"] not in artifact_texts]
    if missing:
        raise ValueError(f"missing HLD artifact outputs: {missing}")
    if upstream_text is None:
        raise ValueError("upstream source inventory required for HLD artifact package validation")
    for artifact in required:
        text = artifact_texts[artifact["id"]]
        validate_artifact_metadata(text, artifact)
        if artifact["id"] == "12":
            parse_rows(text, "HLD Fact Trace")
            validate_verdict_consistency_matrix(text)
            validate_artifact_12_rubric_coverage(text)
            validate_artifact_12_risk_rows(text)
            validate_risk_verdict_consistency(text)
            validate_artifact_12_risk_trace_binding(text, artifact_texts)
            validate_skill_verdict_output(text)
            continue
        heading = artifact.get("section")
        if not heading:
            raise ValueError(f"artifact {artifact['id']} missing business section in contract")
        validate_required_columns(text, heading, artifact["columns"])
        validate_hld_artifact_trace_binding(text, heading, artifact["columns"][0])
        validate_skill_verdict_output(text)
        if artifact["id"] == "11":
            validate_hld_source_map_rows(text)
            validate_source_map_trace_binding(text)
            validate_lld_handoff_index(text)
    validate_reconciliation_mode(artifact_texts["10"], previous_reconciliation_text)
    validate_hld_business_rules(artifact_texts)
    if previous_reconciliation_text is not None:
        validate_reconciliation_continuity(previous_reconciliation_text, artifact_texts["10"])
    validate_thread_closure_checks(artifact_texts)
    validate_style_pov_closure_checks(artifact_texts)
    validate_upstream_source_coverage(upstream_text, artifact_texts)
    boundary_text = authenticated_prd_information_boundary_text(prd_boundary_sources)
    validate_upstream_information_boundary_alignment(boundary_text, artifact_texts)


def load_hld_artifact_texts(artifact_dir: Path) -> dict[str, str]:
    if not artifact_dir.exists():
        raise ValueError(f"HLD artifact directory does not exist: {artifact_dir}")
    artifact_texts: dict[str, str] = {}
    for path in sorted(artifact_dir.rglob("*.md")):
        text = read(path)
        try:
            metadata = parse_field_value_section(text, "Artifact Metadata")
        except ValueError:
            continue
        artifact_id = metadata.get("Artifact id", "").strip("`")
        if re.fullmatch(r"\d{2}", artifact_id):
            if artifact_id in artifact_texts:
                raise ValueError(f"duplicate HLD artifact id {artifact_id} in {artifact_dir}")
            artifact_texts[artifact_id] = text
    return artifact_texts


def validate_authenticated_prd_handoff(final_prd_package_path: Path) -> None:
    try:
        from scripts import validate_prd_contract
    except ModuleNotFoundError:
        import validate_prd_contract

    resolved_final_package = final_prd_package_path.resolve()
    prd_contract = validate_prd_contract.load_contract()
    registered_runs = [
        artifact_run
        for artifact_run in prd_contract.get("artifact_runs", [])
        if (validate_prd_contract.resolve_recorded_path(artifact_run["final_prd_package"])).resolve()
        == resolved_final_package
    ]
    if len(registered_runs) != 1:
        raise ValueError(
            f"final PRD package is not registered for authenticated HLD handoff: {resolved_final_package}"
        )
    validate_prd_contract.validate_formal_prd_artifact_run(
        registered_runs[0],
        prd_contract,
        "authenticated HLD handoff",
    )


def validate_hld_artifact_dir(
    contract: dict,
    artifact_dir: Path,
    upstream_paths: list[Path] | None = None,
    authenticate_prd_handoff: bool = True,
    previous_reconciliation_path: Path | None = None,
) -> None:
    if not upstream_paths:
        raise ValueError("upstream source files required for HLD artifact dir validation")
    final_package_paths = [path for path in upstream_paths if path.name == "final-prd-package.md"]
    if authenticate_prd_handoff:
        if len(final_package_paths) != 1:
            raise ValueError("exactly one final-prd-package.md is required for authenticated HLD handoff")
        validate_authenticated_prd_handoff(final_package_paths[0])
    upstream_text = [read(path) for path in upstream_paths]
    source_key_by_filename = {
        "05-information-flow.md": "artifact_05",
        "08-prd-integrator.md": "artifact_08",
        "final-prd-package.md": "final_prd_package",
    }
    prd_boundary_sources = {
        source_key_by_filename[path.name]: text
        for path, text in zip(upstream_paths, upstream_text)
        if path.name in source_key_by_filename
    }
    validate_hld_artifact_package(
        contract,
        load_hld_artifact_texts(artifact_dir),
        upstream_text=upstream_text,
        prd_boundary_sources=prd_boundary_sources,
        previous_reconciliation_text=(
            read(previous_reconciliation_path) if previous_reconciliation_path is not None else None
        ),
    )


def unresolved_p0_p1_risks(report_text: str) -> list[dict[str, str]]:
    blocking = []
    for row in parse_rows(report_text, "Risks"):
        if row.get("Severity") not in {"P0", "P1"}:
            continue
        if not risk_handling_is_resolved(row):
            blocking.append(row)
    return blocking


def risk_handling_is_resolved(risk: dict[str, str]) -> bool:
    handling = risk.get("Handling", "").strip().lower()
    return handling in {"resolved", "fixed", "closed"} or handling.startswith("resolved:")


def is_none_value(value: str | None) -> bool:
    return (value or "").strip().lower() in {"", "none", "n/a", "not_applicable"}


def validate_artifact_12_risk_rows(report_text: str) -> None:
    rows = validate_required_columns(report_text, "Risks", RISK_TRACE_COLUMNS)
    risk_ids: set[str] = set()
    for row in rows:
        risk_id = row.get("Risk", "").strip()
        severity = row.get("Severity", "").strip()
        if severity not in RISK_SEVERITIES:
            raise ValueError(f"invalid risk severity: {severity}")
        if risk_id.lower() == "none":
            for column in ["Source refs", "Owner artifact", "Rerun target"]:
                if not is_none_value(row.get(column)):
                    raise ValueError(f"none risk row must not carry {column}")
            continue
        if risk_id in risk_ids:
            raise ValueError(f"duplicate risk id: {risk_id}")
        risk_ids.add(risk_id)
        missing_traceability = [
            column for column in ["Source refs", "Owner artifact", "Rerun target"]
            if is_none_value(row.get(column))
        ]
        if missing_traceability:
            raise ValueError(f"risk row missing traceability values: {risk_id}")
        validate_source_ref_values(row["Source refs"])
        if not re.fullmatch(r"artifact (0[1-9]|1[0-2])", row["Owner artifact"]):
            raise ValueError(f"invalid risk owner artifact: {row['Owner artifact']}")
        if not re.fullmatch(r"artifact (0[1-9]|1[0-2])", row["Rerun target"]):
            raise ValueError(f"invalid risk rerun target: {row['Rerun target']}")


def parse_artifact_12_output(report_text: str) -> dict[str, str]:
    rows = validate_required_columns(report_text, "Output", ["Field", "Value"])
    values: dict[str, str] = {}
    for row in rows:
        field = row["Field"].strip()
        value = row["Value"].strip("`")
        if field in values:
            raise ValueError(f"duplicate Output field: {field}")
        values[field] = value
    missing = ARTIFACT_12_OUTPUT_FIELDS - set(values)
    if missing:
        raise ValueError(f"Output missing verdict fields: {sorted(missing)}")
    unexpected = set(values) - ARTIFACT_12_OUTPUT_FIELDS
    if unexpected:
        raise ValueError(f"Output contains unknown fields: {sorted(unexpected)}")
    for field, allowed_values in ARTIFACT_12_OUTPUT_VALUES.items():
        if values[field] not in allowed_values:
            raise ValueError(f"invalid Output {field}: {values[field]}")
    return values


def validate_hld_convergence_log(report_text: str) -> list[dict[str, str]]:
    rows = validate_required_columns(report_text, "HLD Convergence Log", CONVERGENCE_LOG_COLUMNS)
    issue_ids: set[str] = set()
    for row in rows:
        issue_id = row["Stable issue id"].strip()
        if is_none_value(issue_id):
            if (
                row["Severity"] != "P3"
                or row["Attempt count"] != "0"
                or not is_none_value(row["Rerun target"])
                or row["Status"] != "closed"
            ):
                raise ValueError("invalid none convergence row")
            continue
        if issue_id in issue_ids:
            raise ValueError(f"duplicate convergence issue id: {issue_id}")
        issue_ids.add(issue_id)
        if row["Severity"] not in RISK_SEVERITIES:
            raise ValueError(f"invalid convergence severity: {issue_id}")
        if any(is_none_value(row[column]) for column in ["Root cause", "Fix hypothesis", "Regression proof"]):
            raise ValueError(f"convergence row lacks resolution evidence: {issue_id}")
        if not row["Attempt count"].isdigit() or int(row["Attempt count"]) < 1:
            raise ValueError(f"invalid convergence attempt count: {issue_id}")
        if not re.fullmatch(r"artifact (0[1-9]|1[0-2])", row["Rerun target"]):
            raise ValueError(f"invalid convergence rerun target: {issue_id}")
        if row["Status"] not in CONVERGENCE_STATUSES:
            raise ValueError(f"invalid convergence status: {issue_id}")
    return rows


def validate_artifact_12_rubric_coverage(report_text: str) -> None:
    rows = validate_required_columns(report_text, "Artifact rubric coverage", RUBRIC_COVERAGE_COLUMNS)
    required_artifacts = {f"Artifact {i:02d}" for i in range(1, 13)}
    observed = {row["Artifact"] for row in rows}
    missing = required_artifacts - observed
    if missing:
        raise ValueError(f"Artifact rubric coverage missing artifacts: {sorted(missing)}")
    for row in rows:
        for column in RUBRIC_COVERAGE_COLUMNS:
            if not row.get(column) or is_none_value(row.get(column)):
                raise ValueError(f"rubric coverage row missing {column}: {row.get('Artifact', '')}")
        if row["Coverage verdict"] not in {"pass", "fail", "blocked"}:
            raise ValueError(f"invalid rubric coverage verdict: {row['Coverage verdict']}")
        if row["Coverage verdict"] != "pass":
            raise ValueError(f"rubric coverage contains non-pass verdict: {row['Artifact']}")
        if row["Artifact"] == "Artifact 04":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = ["concrete motive", "relationship target", "digital-life identity boundary"]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 04 rubric missing character quality checks")
        if row["Artifact"] == "Artifact 05":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "inventory coverage",
                "spatial relation",
                "state-change dimension",
                "state transition",
                "event state realization",
                "source map trace closure",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 05 rubric missing environment closure checks")
        if row["Artifact"] == "Artifact 07":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "information inventory",
                "story anchor",
                "time layer",
                "narrative reveal phase",
                "disclosure tier",
                "knowledge state",
                "reveal predecessor",
                "reveal event",
                "reveal action",
                "condition type",
                "condition refs",
                "source map trace closure",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 07 rubric missing information closure checks")
        if row["Artifact"] == "Artifact 08":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "main",
                "hidden",
                "emotional",
                "theme",
                "institutional",
                "identity",
                "thread function",
                "required pressure",
                "thread progression",
                "crossover",
                "closure outcome",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 08 rubric missing thread quality checks")
        if row["Artifact"] == "Artifact 09":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "pov",
                "narrative distance",
                "information access",
                "digital-life interiority",
                "dialogue",
                "image system",
                "prohibited expression",
                "language style",
                "access policy",
                "information refs",
                "thread refs",
                "reader disclosure mode",
                "language profile directives",
                "type-specific behavior",
                "vague expression",
                "execution reference closure",
                "focalizer resolution",
                "structured design fact",
                "pov permission",
                "execution fields",
                "lld handoff",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 09 rubric missing Style/POV quality checks")
        if row["Artifact"] == "Artifact 10":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "subject register",
                "origin binding",
                "canonical merge",
                "single final inventory id",
                "amendment blocking",
                "continuity",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 10 rubric missing reconciliation quality checks")
        if row["Artifact"] == "Artifact 11":
            rubric_text = normalize_fact_text(
                f"{row['Good delivery evidence']} {row['Blocking failure check']}"
            )
            required_terms = [
                "fact-level source map closure",
                "artifact 03-09",
                "lld handoff index",
                "ready",
            ]
            if any(term not in rubric_text for term in required_terms):
                raise ValueError("Artifact 11 rubric missing integration closure checks")


def validate_verdict_consistency_matrix(
    report_text: str,
    output: dict[str, str] | None = None,
) -> None:
    rows = validate_required_columns(report_text, "Verdict consistency matrix", VERDICT_MATRIX_COLUMNS)
    output = output or parse_artifact_12_output(report_text)
    matrix_by_verdict: dict[str, dict[str, str]] = {}
    for row in rows:
        for column in VERDICT_MATRIX_COLUMNS:
            if not row.get(column):
                raise ValueError(f"Verdict consistency matrix row missing {column}")
        verdict = row["Verdict"]
        if verdict in matrix_by_verdict:
            raise ValueError(f"duplicate Verdict consistency matrix row: {verdict}")
        matrix_by_verdict[verdict] = row
        if row["Consistency"] not in {"pass", "fail", "blocked"}:
            raise ValueError(f"invalid verdict matrix consistency: {row['Consistency']}")
        if row["Consistency"] != "pass":
            raise ValueError(f"verdict matrix contains non-pass consistency: {row['Verdict']}")
    missing_verdicts = ARTIFACT_12_OUTPUT_FIELDS - set(matrix_by_verdict)
    if missing_verdicts:
        raise ValueError(f"Verdict consistency matrix missing verdict rows: {sorted(missing_verdicts)}")
    unexpected_verdicts = set(matrix_by_verdict) - ARTIFACT_12_OUTPUT_FIELDS
    if unexpected_verdicts:
        raise ValueError(f"Verdict consistency matrix contains unknown verdicts: {sorted(unexpected_verdicts)}")
    for verdict, value in output.items():
        if matrix_by_verdict[verdict]["Resolved value"].strip("`") != value:
            raise ValueError(f"Verdict consistency matrix value mismatch: {verdict}")


def validate_artifact_12_risk_trace_binding(
    report_text: str,
    artifact_texts: dict[str, str] | None = None,
) -> None:
    trace_rows = validate_required_columns(report_text, "HLD Fact Trace", HLD_FACT_TRACE_COLUMNS)
    traces_by_id: dict[str, list[dict[str, str]]] = {}
    for trace in trace_rows:
        traces_by_id.setdefault(trace.get("Fact trace id", ""), []).append(trace)
    for risk in parse_rows(report_text, "Risks"):
        risk_id = risk["Risk"]
        if risk_id.lower() == "none":
            continue
        traces = traces_by_id.get(risk_id, [])
        if len(traces) != 1:
            if risk in unresolved_p0_p1_risks(report_text):
                raise ValueError(f"blocking risk lacks fact trace: {risk_id}")
            raise ValueError(f"risk lacks fact trace: {risk_id}")
        trace = traces[0]
        for column in HLD_FACT_TRACE_COLUMNS:
            if is_none_value(trace.get(column)):
                raise ValueError(f"risk fact trace missing {column}: {risk_id}")
        if not UPSTREAM_FACT_ID_PATTERN.fullmatch(trace["Upstream fact id"]):
            raise ValueError(f"invalid risk fact trace upstream fact id: {risk_id}")
        if trace["Expansion mode"] not in EXPANSION_MODES:
            raise ValueError(f"invalid risk fact trace expansion mode: {risk_id}")
        if canonical_source_refs(trace["Source refs"]) != canonical_source_refs(risk["Source refs"]):
            raise ValueError(f"risk fact trace source mismatch: {risk_id}")
        if trace["Preservation status"] != "risk_reported":
            raise ValueError(f"risk fact trace preservation status mismatch: {risk_id}")
        if artifact_texts is not None:
            source_trace_rows = [
                source_trace
                for artifact_id, artifact_text in artifact_texts.items()
                if artifact_id != "12"
                for source_trace in parse_rows(artifact_text, "HLD Fact Trace")
                if source_trace.get("Upstream fact id") == trace["Upstream fact id"]
                and normalize_fact_text(source_trace.get("Upstream fact atom", ""))
                == normalize_fact_text(trace["Upstream fact atom"])
                and canonical_source_refs(source_trace.get("Source refs", ""))
                == canonical_source_refs(trace["Source refs"])
            ]
            if not source_trace_rows:
                raise ValueError(f"risk fact trace lacks HLD source binding: {risk_id}")


def validate_risk_verdict_consistency(report_text: str | None = None) -> None:
    text = report_text or """
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | not_required |
| LLD entry verdict | pass_to_lld |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| none | P3 | none | none | none | none | none |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| none | P3 | none | none | none | 0 | none | closed |
"""
    output = parse_artifact_12_output(text)
    validate_artifact_12_risk_rows(text)
    convergence = validate_hld_convergence_log(text)
    blocking = unresolved_p0_p1_risks(text)
    risks_by_id = {
        row["Risk"]: row
        for row in parse_rows(text, "Risks")
        if not is_none_value(row["Risk"])
    }
    agent = output.get("Agent quality verdict")
    human = output.get("HLD human review state")
    lld = output.get("LLD entry verdict")
    if blocking:
        if agent != "fail" or lld != "blocked_revision_required":
            raise ValueError("unresolved P0/P1 cannot coexist with pass Agent quality or pass_to_lld")
    elif agent == "fail":
        if lld != "blocked_revision_required":
            raise ValueError("failed Agent quality must require blocked_revision_required")
    elif human == "reopen_hld":
        if lld != "blocked_revision_required":
            raise ValueError("human review state reopen_hld must require blocked_revision_required")
    elif human == "pending_required":
        if lld != "blocked_pending_human_review":
            raise ValueError("human review state pending_required must block LLD entry")
    elif lld != "pass_to_lld":
        raise ValueError("human review state permits pass_to_lld when Agent quality passes")
    convergence_by_id = {
        row["Stable issue id"]: row
        for row in convergence
        if not is_none_value(row["Stable issue id"])
    }
    for risk in blocking:
        risk_id = risk["Risk"]
        convergence_row = convergence_by_id.get(risk_id)
        if convergence_row is None:
            raise ValueError(f"blocking risk lacks convergence row: {risk_id}")
        if convergence_row["Severity"] != risk["Severity"]:
            raise ValueError(f"convergence severity mismatch: {risk_id}")
        if convergence_row["Rerun target"] != risk["Rerun target"]:
            raise ValueError(f"convergence rerun target mismatch: {risk_id}")
        if convergence_row["Status"] not in {"open", "blocked"}:
            raise ValueError(f"unresolved risk has closed convergence row: {risk_id}")
    for convergence_row in convergence:
        issue_id = convergence_row["Stable issue id"]
        if is_none_value(issue_id):
            continue
        risk = risks_by_id.get(issue_id)
        if risk is None:
            raise ValueError(f"convergence issue lacks Risk row: {issue_id}")
        if convergence_row["Severity"] != risk["Severity"]:
            raise ValueError(f"convergence severity mismatch: {issue_id}")
        if convergence_row["Rerun target"] != risk["Rerun target"]:
            raise ValueError(f"convergence rerun target mismatch: {issue_id}")
        if (
            convergence_row["Status"] in {"open", "blocked"}
            and risk_handling_is_resolved(risk)
        ):
            raise ValueError(f"open convergence issue has resolved Risk row: {issue_id}")


def validate_legacy_writer_demoted(contract: dict) -> None:
    text = read(LEGACY_HLD_WRITER)
    require_terms(
        "novel-hld-writer",
        text,
        [
            "Legacy status",
            "not an authoritative HLD entry point",
            "novel-hld-workflow",
            "must not be used as frozen authority",
        ],
    )
    forbidden = "本技能是**自包含的**"
    if forbidden in text:
        raise ValueError("legacy novel-hld-writer still claims self-contained authority")


def validate_methodology_reference(contract: dict) -> None:
    text = read(REFERENCE_PATH)
    refs = set(re.findall(r"REF-\d{2}", text))
    if len(refs) < 10:
        raise ValueError("methodology reference must cite at least ten references")
    for artifact_id in [f"{i:02d}" for i in range(1, 13)]:
        if f"Artifact {artifact_id}" not in text:
            raise ValueError(f"methodology reference missing rubric for Artifact {artifact_id}")


def validate_all() -> None:
    contract = load_hld_contract()
    validate_contract_rule_coverage(contract)
    validate_required_skill_files(contract)
    validate_artifact_dag(contract)
    validate_artifact_schemas(contract)
    validate_skill_contract_text(contract)
    validate_harness_boundary(contract)
    validate_harness_routing_rules(contract)
    validate_release_preflight_contract(contract)
    validate_prd_gate_terms(contract)
    validate_source_grammar_and_expansion_modes(contract)
    validate_inventory_id_timing(contract)
    validate_skill_preservation_status_terms(
        contract,
        "novel-hld-integrator",
        read(ROOT / "skills/novel-hld-integrator/SKILL.md"),
    )
    validate_hld_source_map_rows()
    validate_risk_verdict_consistency()
    validate_legacy_writer_demoted(contract)
    validate_methodology_reference(contract)


if __name__ == "__main__":
    try:
        validate_all()
        if len(sys.argv) > 1:
            arguments = sys.argv[1:]
            previous_reconciliation_path = None
            if "--previous-reconciliation" in arguments:
                option_index = arguments.index("--previous-reconciliation")
                if option_index + 1 >= len(arguments):
                    raise ValueError("--previous-reconciliation requires an artifact 10 path")
                previous_reconciliation_path = Path(arguments[option_index + 1])
                del arguments[option_index:option_index + 2]
            validate_hld_artifact_dir(
                load_hld_contract(),
                Path(arguments[0]),
                [Path(arg) for arg in arguments[1:]],
                previous_reconciliation_path=previous_reconciliation_path,
            )
    except Exception as exc:
        fail(str(exc))
    print("PASS: HLD workflow contract is valid")
