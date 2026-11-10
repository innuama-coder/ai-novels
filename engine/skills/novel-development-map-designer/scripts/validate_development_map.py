#!/usr/bin/env python3
"""Validate a D1 development-map package and write immutable handoff evidence."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from execution_record import verify_record
from render_development_map import render_content_documents, render_map_check


HARNESS = "novel-conception-interview"
INTERVIEW_STAGES = ("I0", "I1", "I2", "I3", "I4", "I5")
AREAS = {
    "intent": "I0",
    "subject": "I1",
    "world": "I2",
    "character": "I3",
    "causality": "I4",
    "narrative": "I5",
}
HARDNESS = {"hard", "delegated", "open"}
DEVELOPMENT_DOMAINS = {"world", "story", "character", "cross"}
DEVELOPMENT_GAP_KINDS = {
    "causal_bridge",
    "opposition",
    "world_operation",
    "character_tactic",
    "choice_cost",
    "relationship_change",
    "information_design",
    "thematic_test",
    "supporting_function",
    "ending_setup",
}
DEVELOPMENT_GAP_RESOLUTIONS = {
    "autonomous_decision",
    "downstream_freedom",
    "author_open",
}
DESIGN_DECISION_NOVELTY = {"inference", "concretization", "invention"}
DESIGN_DECISION_IMPACT = {"local", "structural"}
DESIGN_DECISION_REVERSIBILITY = {"local", "cross_unit", "whole_design"}
ALTERNATIVE_STATUS = {"selected", "rejected"}
WORLD_FACET_DOMAINS = {
    "ontology_and_nature",
    "time_and_history",
    "space_and_geography",
    "society_and_culture",
    "institutions_and_power",
    "economy_and_resources",
    "law_ethics_and_norms",
    "daily_life",
}
WORLD_FACET_STATUS = {"defined", "not_applicable"}
WORLD_SYSTEM_DOMAINS = {
    "physical",
    "technological",
    "political",
    "institutional",
    "economic",
    "social",
    "cultural",
    "legal",
    "ethical",
    "informational",
}
WORLD_ENVIRONMENT_TYPES = {
    "physical",
    "digital",
    "memory",
    "institutional",
    "social",
    "hybrid",
}
STORYLINE_TYPES = {"main", "precursor", "subplot", "background"}
STORYLINE_DEMAND_DISPOSITIONS = {
    "dedicated_line",
    "integrated_into_lines",
    "not_applicable",
}
STORYLINE_CONNECTION_TYPES = {
    "merge",
    "split",
    "handoff",
    "collision",
    "reveal",
    "synchronization",
}
MAJOR_EVENT_ROLES = {
    "setup",
    "trigger",
    "escalation",
    "turning_point",
    "crisis",
    "climax",
    "resolution",
    "aftermath",
    "context_shift",
}
EVENT_SOURCE_CANDIDATE_TYPES = {
    "story_event",
    "causal_antecedent",
    "causal_transition",
    "narrative_required",
    "character_transition",
    "world_state_change",
    "operational_step",
    "static_context",
}
EVENT_SOURCE_DISPOSITIONS = {
    "enacted",
    "distributed",
    "context_only",
    "excluded",
}
MIN_RELATIONSHIP_DEPTH = 3
RELATION_NAMING_STATUS = {"confirmed", "autonomous", "functional"}
CHARACTER_IMPORTANCE = {"core", "supporting", "peripheral"}
CHARACTER_DEMAND_CATEGORIES = {
    "decision_authority",
    "information_transfer",
    "expertise_formation",
    "opposition_execution",
    "relationship_pressure",
    "operational_execution",
    "aftermath_responsibility",
}
CHARACTER_DEMAND_RESOLUTIONS = {"profile", "not_applicable"}
CHARACTER_DEMAND_CRITICALITY = {"structural", "supporting", "contextual"}
CHARACTER_NAMING_REQUIREMENTS = {"named", "functional", "not_applicable"}
FUNCTIONAL_CHARACTER_NAME_PATTERN = re.compile(
    r"^(?:the\s+)?(?:(?:[a-z][a-z-]*\s+){0,4})"
    r"(?:teacher|mentor|leader|supervisor|handler|contact|"
    r"liaison|officer|captain|expert|doctor|wife|husband|colleague|"
    r"commander|director|agent|operator|technician|scientist|guard|"
    r"project\s+lead|team\s+leader|ferry\s+captain)$|"
    r"^(?:老师|导师|领导|上级|接头人|联络人|负责人|主任|队长|"
    r"专家|医生|妻子|丈夫|同事|官员|指挥员|行动人员|技术员|"
    r"科学家|警卫)$",
    re.IGNORECASE,
)
COVERAGE_STATUS = {"covered", "open", "deferred"}
SCALES = {"short", "medium", "long", "unspecified"}
PACKAGE_STATUS = {"ready", "revise", "blocked"}
TERMINAL_ROLES = {"main", "subplot", "series"}
INFORMATION_RESOLUTIONS = {"within_book", "series"}
INFORMATION_AUDIENCES = {
    "reader",
    "pov_character",
    "story_characters",
    "mixed",
}
DERIVED_SUBJECTS = {
    "control_point": (
        "control_points",
        ("kind", "hardness"),
    ),
    "unit": (
        "units",
        (
            "title",
            "purpose",
            "preconditions",
            "objective",
            "obstacle",
            "choice",
            "opposition",
            "choice_options",
            "choice_cost",
            "consequence",
            "next_pressure",
            "value_shift",
            "information",
            "exit_state",
            "depends_on",
            "creative_freedom",
            "scale",
        ),
    ),
    "information_obligation": (
        "information_obligations",
        (
            "statement",
            "audience",
            "knowledge_holder_controls",
            "resolution",
        ),
    ),
    "open_item": (
        "open_items",
        ("allowed_handling", "forbidden_resolution"),
    ),
    "terminal_thread": (
        "terminal_threads",
        ("label", "role"),
    ),
}
WORLD_CONCEPTION_FIELDS = (
    "definition",
    "story_function",
    "time_space_scope",
    "operating_logic",
    "power_and_resources",
    "action_permissions",
    "hard_constraints",
    "pressure_sources",
    "costs_and_consequences",
    "end_state",
    "scope_exclusions",
)
WORLD_FACET_FIELDS = (
    "domain",
    "status",
    "definition",
    "story_relevance",
    "downstream_freedom",
)
WORLD_SYSTEM_FIELDS = (
    "name",
    "domain",
    "definition",
    "input_conditions",
    "transformation_rule",
    "observable_outputs",
    "actors",
    "resources",
    "rules",
    "permissions",
    "costs",
    "limits",
    "failure_modes",
    "story_effects",
    "state_changes",
    "environment_ids",
    "major_event_ids",
    "downstream_freedom",
)
WORLD_ENVIRONMENT_FIELDS = (
    "name",
    "environment_type",
    "definition",
    "scope",
    "distinctive_features",
    "basic_elements",
    "sensory_conditions",
    "occupants_and_access",
    "resources_and_infrastructure",
    "rules_and_affordances",
    "hazards_and_pressures",
    "story_functions",
    "state_changes",
    "topology",
    "event_hosting",
    "storyline_ids",
    "unit_ids",
    "downstream_freedom",
)
STORY_CONCEPTION_FIELDS = (
    "core_promise",
    "whose_story",
    "central_conflict",
    "dramatic_question",
    "stakes",
    "start_state",
    "inciting_incident",
    "escalation_logic",
    "climax",
    "resolution",
    "open_threads",
    "scope_exclusions",
)
EVENT_SPAN_FIELDS = (
    "earliest_causal_change",
    "latest_consequence",
    "opening_event_ids",
    "main_action_entry_event_id",
    "aftermath_event_ids",
    "coverage_rationale",
)
STORYLINE_FIELDS = (
    "type",
    "title",
    "function",
    "protagonists",
    "central_question",
    "start_state",
    "driver",
    "escalation",
    "major_event_ids",
    "end_state",
    "resolution",
    "unit_ids",
    "downstream_freedom",
)
STORYLINE_DEMAND_FIELDS = (
    "need",
    "story_function",
    "omission_consequence",
    "disposition",
    "storyline_ids",
    "rationale",
)
STORYLINE_ARCHITECTURE_FIELDS = (
    "entry_storyline_ids",
    "main_storyline_id",
    "terminal_storyline_ids",
    "coverage_rationale",
)
STORYLINE_CONNECTION_FIELDS = (
    "connection_type",
    "event_id",
    "incoming_storyline_ids",
    "outgoing_storyline_ids",
    "preconditions",
    "transferred_obligations",
    "resulting_state",
)
MELODY_LINE_FIELDS = (
    "title",
    "function",
    "anchor_event_ids",
    "variation_pattern",
    "expansion_options",
    "omission_effect",
    "boundaries",
    "series_potential",
    "required_for_causality",
    "required_for_resolution",
    "new_pov_allowed",
    "carries_decisive_information",
    "downstream_freedom",
)
EVENT_ENVIRONMENT_REQUIREMENT_FIELDS = (
    "major_event_id",
    "primary_environment_id",
    "secondary_environment_ids",
    "required_capabilities",
    "required_zone_ids",
    "required_resources",
    "required_permissions",
    "required_information_channels",
    "hazards_and_constraints",
    "transition_requirements",
    "adequacy_rationale",
)
MAJOR_EVENT_FIELDS = (
    "title",
    "event_role",
    "definition",
    "storyline_ids",
    "unit_ids",
    "environment_ids",
    "participant_ids",
    "initiator_ids",
    "opposition_actor_ids",
    "preconditions",
    "initiating_action",
    "opposition_or_complication",
    "decisive_change",
    "immediate_outcome",
    "state_before",
    "state_after",
    "next_pressure",
    "information_effects",
    "causal_predecessor_ids",
    "downstream_freedom",
)
STORY_PHASE_FIELDS = (
    "title",
    "function",
    "entry_state",
    "driving_goal",
    "pressure",
    "decisive_change",
    "exit_state",
    "unit_ids",
)
CHARACTER_CONCEPTION_FIELDS = (
    "name",
    "naming_status",
    "importance",
    "role",
    "story_function",
    "start_state",
    "surface_goal",
    "deeper_need",
    "fear_or_avoidance",
    "values_and_boundaries",
    "information_limits",
    "pressure_behavior",
    "agency_choices",
    "arc_stages",
    "end_state",
    "invariants",
    "storyline_ids",
    "unit_ids",
    "demand_ids",
    "downstream_freedom",
)
CHARACTER_DEMAND_FIELDS = (
    "category",
    "criticality",
    "trigger",
    "story_function",
    "omission_consequence",
    "resolution",
    "profile_id",
    "naming_requirement",
    "source_subject_ids",
    "downstream_freedom",
)
RELATIONSHIP_FIELDS = (
    "source_id",
    "target_id",
    "relationship_type",
    "shared_history",
    "alignment",
    "conflict",
    "leverage",
    "information_asymmetry",
    "change",
    "storyline_ids",
    "unit_ids",
    "downstream_freedom",
)
SEMANTIC_CHECKS = (
    "gap_resolution",
    "forward_causality",
    "reverse_ending",
    "character_agency",
    "opposition_adaptation",
    "choice_costs",
    "easy_solution",
    "world_permissions",
    "pov_information",
    "plant_payoff",
    "thematic_testing",
    "minimality",
    "downstream_sufficiency",
)
SEMANTIC_REQUIRED_UNIT_FIELDS = {
    "gap_resolution": {"objective", "exit_state", "development_decisions"},
    "forward_causality": {"consequence", "next_pressure", "exit_state"},
    "reverse_ending": {"preconditions", "exit_state"},
    "character_agency": {"choice", "choice_options", "choice_cost"},
    "opposition_adaptation": {"obstacle", "opposition"},
    "choice_costs": {"choice_options", "choice_cost", "consequence"},
    "easy_solution": {"obstacle", "world_constraints", "prohibitions"},
    "world_permissions": {"world_constraints", "prohibitions"},
    "pov_information": {"pov", "information"},
    "plant_payoff": {"information"},
    "thematic_testing": {"choice_options", "choice_cost", "value_shift"},
    "minimality": {"purpose", "depends_on"},
    "downstream_sufficiency": {"creative_freedom", "prohibitions"},
}
HANDOFF_TASKS = {
    "promise",
    "autonomous_value",
    "causal_chain",
    "unit_contract",
    "freedom_boundary",
    "drift_detection",
    "easy_solution",
    "scene_plan",
}
CONTENT_DOCS = ("development-map.md", "coverage-matrix.md")
DOCS = ("development-map.md", "coverage-matrix.md", "map-check.md")
PACKAGE_FILES = (
    "map-data.json",
    "generation-session.json",
    "generation-evidence/01-control-model.json",
    "generation-evidence/02-gap-and-options.json",
    "generation-evidence/03-story-architecture.json",
    "generation-evidence/04-event-world-model.json",
    "generation-evidence/05-character-model.json",
    "generation-evidence/06-final-map.json",
    "execution-record.json",
    *DOCS,
    "validation.json",
)
RETURN_OWNERS = {*INTERVIEW_STAGES, "V1", "V2", "AUTHOR"}
HARNESS_VALIDATOR = (
    Path(__file__).resolve().parents[3]
    / "harnesses"
    / HARNESS
    / "validators"
    / "validate_stage_completion.py"
)
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PLACEHOLDER_PATTERN = re.compile(
    r"(?:\b(?:generic|placeholder|todo|tbd|lorem\s+ipsum)\b|"
    r"占位|待补|待定内容|某人|某地)",
    re.IGNORECASE,
)
GROUNDING_STOPWORDS = {
    "story",
    "world",
    "character",
    "development",
    "control",
    "decision",
    "current",
    "system",
    "environment",
    "relationship",
    "confirmed",
    "required",
    "pressure",
    "outcome",
    "constraint",
    "constraints",
    "cost",
    "costly",
    "available",
    "relevant",
    "action",
    "actions",
    "rules",
    "actors",
    "only",
    "must",
    "without",
    "within",
    "through",
    "into",
    "from",
    "with",
    "that",
    "this",
    "their",
    "choice",
    "choose",
    "the",
    "and",
    "for",
    "are",
    "but",
    "not",
    "all",
    "any",
    "can",
    "has",
    "have",
    "open",
    "hard",
    "accept",
    "until",
    "concrete",
    "downstream",
    "controls",
    "design",
    "implementation",
    "protagonist",
    "agency",
    "commitment",
    "creates",
    "changing",
    "convert",
    "leaves",
    "preserves",
    "remove",
    "rejected",
    "external",
    "故事",
    "世界",
    "人物",
    "角色",
    "开发",
    "构思",
    "关系",
    "系统",
    "环境",
    "信息",
    "定义",
    "边界",
    "选择",
    "变化",
    "因果",
    "单元",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def business_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(business_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(
            business_text(item)
            for key, item in value.items()
            if key
            not in {
                "id",
                "source_controls",
                "development_decisions",
                "unit_ids",
                "storyline_ids",
            }
        )
    return ""


def normalized_business_text(value: Any) -> str:
    text = business_text(value)
    text = re.sub(
        r"\b(?:[A-Z]{2,}(?:[-_][A-Z0-9]+)+|[A-Z]+\d+[A-Z0-9_-]*)\b",
        " ",
        text,
    )
    text = text.lower()
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def repeated_template_pairs(items: list[Any], threshold: float = 0.90) -> int:
    normalized = [normalized_business_text(item) for item in items]
    pairs = 0
    for left in range(len(normalized)):
        for right in range(left + 1, len(normalized)):
            if not normalized[left] or not normalized[right]:
                continue
            similarity = difflib.SequenceMatcher(
                None,
                normalized[left],
                normalized[right],
                autojunk=False,
            ).ratio()
            if similarity >= threshold:
                pairs += 1
    return pairs


def repeated_field_templates(
    items: list[Any],
    fields: tuple[str, ...],
    *,
    threshold: float = 0.88,
) -> dict[str, int]:
    """Find majority template reuse inside the same semantic field.

    Whole-record similarity is intentionally insufficient here: a generator can
    copy one responsibility sentence across several records while unique names,
    IDs and neighbouring fields dilute the record-level score.  Only flag a
    field when high-similarity pairs form a majority, so an occasional shared
    premise or boundary remains legal.
    """
    if len(items) < 2:
        return {}
    total_pairs = len(items) * (len(items) - 1) // 2
    majority = max(1 if len(items) == 2 else 2, (total_pairs + 1) // 2)
    repeated: dict[str, int] = {}
    records = [item for item in items if isinstance(item, dict)]
    if len(records) != len(items):
        return repeated
    for field in fields:
        values = [normalized_business_text(item.get(field)) for item in records]
        pairs = 0
        compared = 0
        for left in range(len(values)):
            for right in range(left + 1, len(values)):
                if min(len(values[left]), len(values[right])) < 12:
                    continue
                compared += 1
                similarity = difflib.SequenceMatcher(
                    None,
                    values[left],
                    values[right],
                    autojunk=False,
                ).ratio()
                if similarity >= threshold:
                    pairs += 1
        if compared >= majority and pairs >= majority:
            repeated[field] = pairs
    return repeated


def grounding_tokens(value: Any) -> set[str]:
    text = business_text(value).lower()
    tokens = {
        token
        for token in re.findall(r"[a-z][a-z0-9-]{2,}", text)
        if token not in GROUNDING_STOPWORDS
    }
    for run in re.findall(r"[\u3400-\u9fff]{2,}", text):
        for size in (2, 3, 4):
            tokens.update(
                run[index : index + size]
                for index in range(0, max(0, len(run) - size + 1))
            )
    return {token for token in tokens if token not in GROUNDING_STOPWORDS}


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_value_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nonempty_string(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def string_list(value: Any, *, nonempty: bool) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(nonempty_string(item) for item in value)
    )


def string_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def derived_subject_specs(
    data: dict[str, Any],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    specs: dict[tuple[str, str, str], dict[str, Any]] = {}
    for subject_type, (collection_name, fields) in DERIVED_SUBJECTS.items():
        collection = data.get(collection_name)
        if not isinstance(collection, list):
            continue
        for record in collection:
            if not isinstance(record, dict):
                continue
            subject_id = record.get("id")
            if not isinstance(subject_id, str) or not subject_id:
                continue
            active_fields = list(fields)
            if (
                subject_type == "information_obligation"
                and record.get("resolution") == "series"
            ):
                active_fields.append("series_interface")
            for field in active_fields:
                specs[(subject_type, subject_id, field)] = {
                    "record": record,
                    "value": record.get(field),
                }
    conception = data.get("conception")
    if isinstance(conception, dict):
        world = conception.get("world")
        story = conception.get("story")
        characters = conception.get("characters")
        for subject_type, record, fields in (
            ("world_conception", world, WORLD_CONCEPTION_FIELDS),
            ("story_conception", story, STORY_CONCEPTION_FIELDS),
        ):
            if not isinstance(record, dict):
                continue
            subject_id = record.get("id")
            if not isinstance(subject_id, str) or not subject_id:
                continue
            for field in fields:
                specs[(subject_type, subject_id, field)] = {
                    "record": record,
                    "value": record.get(field),
                }
        if isinstance(world, dict):
            for record in world.get("facets", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in WORLD_FACET_FIELDS:
                    specs[("world_facet", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in world.get("systems", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in WORLD_SYSTEM_FIELDS:
                    specs[("world_system", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in world.get("environments", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in WORLD_ENVIRONMENT_FIELDS:
                    specs[("world_environment", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in world.get("event_environment_requirements", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in EVENT_ENVIRONMENT_REQUIREMENT_FIELDS:
                    specs[("event_environment_requirement", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
        if isinstance(story, dict):
            for record in story.get("phases", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in STORY_PHASE_FIELDS:
                    specs[("story_phase", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in story.get("major_events", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in MAJOR_EVENT_FIELDS:
                    specs[("major_event", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in story.get("storylines", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in STORYLINE_FIELDS:
                    specs[("storyline", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in story.get("storyline_demands", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in STORYLINE_DEMAND_FIELDS:
                    specs[("storyline_demand", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for record in story.get("melody_lines", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in MELODY_LINE_FIELDS:
                    specs[("melody_line", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            architecture = story.get("storyline_architecture")
            if isinstance(architecture, dict):
                subject_id = architecture.get("id")
                if isinstance(subject_id, str) and subject_id:
                    for field in STORYLINE_ARCHITECTURE_FIELDS:
                        specs[("storyline_architecture", subject_id, field)] = {
                            "record": architecture,
                            "value": architecture.get(field),
                        }
                for record in architecture.get("connection_points", []):
                    if not isinstance(record, dict):
                        continue
                    connection_id = record.get("id")
                    if not isinstance(connection_id, str) or not connection_id:
                        continue
                    for field in STORYLINE_CONNECTION_FIELDS:
                        specs[("storyline_connection", connection_id, field)] = {
                            "record": record,
                            "value": record.get(field),
                        }
        if isinstance(characters, dict):
            for demand in characters.get("demand_register", []):
                if not isinstance(demand, dict):
                    continue
                demand_id = demand.get("id")
                if not isinstance(demand_id, str) or not demand_id:
                    continue
                for field in CHARACTER_DEMAND_FIELDS:
                    specs[("character_demand", demand_id, field)] = {
                        "record": demand,
                        "value": demand.get(field),
                    }
            for record in characters.get("profiles", []):
                if not isinstance(record, dict):
                    continue
                subject_id = record.get("id")
                if not isinstance(subject_id, str) or not subject_id:
                    continue
                for field in CHARACTER_CONCEPTION_FIELDS:
                    specs[("character_conception", subject_id, field)] = {
                        "record": record,
                        "value": record.get(field),
                    }
            for relationship in characters.get("relationships", []):
                if not isinstance(relationship, dict):
                    continue
                relation_id = relationship.get("id")
                if not isinstance(relation_id, str) or not relation_id:
                    continue
                for field in RELATIONSHIP_FIELDS:
                    specs[("character_relationship", relation_id, field)] = {
                        "record": relationship,
                        "value": relationship.get(field),
                    }
    return specs


def allowed_derivation_sources(
    subject_type: str,
    subject_id: str,
    record: dict[str, Any],
) -> set[str]:
    if subject_type == "control_point":
        return {subject_id}
    if subject_type in {
        "unit",
        "information_obligation",
        "terminal_thread",
        "world_conception",
        "world_facet",
        "world_system",
        "world_environment",
        "event_environment_requirement",
        "story_conception",
        "story_phase",
        "major_event",
        "storyline",
        "storyline_demand",
        "storyline_architecture",
        "storyline_connection",
        "melody_line",
        "character_demand",
        "character_conception",
        "relationship_layer",
        "character_relationship",
    }:
        return set(string_values(record.get("source_controls")))
    if subject_type == "open_item":
        source = record.get("source_control")
        return {source} if isinstance(source, str) and source else set()
    return set()


def allowed_derivation_decisions(
    subject_type: str,
    record: dict[str, Any],
) -> set[str]:
    if subject_type in {
        "unit",
        "world_facet",
        "world_system",
        "world_environment",
        "event_environment_requirement",
        "major_event",
        "storyline",
        "storyline_demand",
        "storyline_architecture",
        "storyline_connection",
        "melody_line",
        "character_demand",
        "relationship_layer",
        "character_relationship",
    }:
        return set(string_values(record.get("development_decisions")))
    return set()


def markdown_sections(text: str) -> dict[str, list[str]]:
    """Return exact Markdown heading titles mapped to their section bodies."""
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))
    result: dict[str, list[str]] = {}
    for position, (start, level, title) in enumerate(headings):
        end = len(lines)
        for next_start, next_level, _ in headings[position + 1 :]:
            if next_level <= level:
                end = next_start
                break
        result.setdefault(title, []).append("\n".join(lines[start + 1 : end]).strip())
    return result


class Review:
    def __init__(self, package_dir: Path) -> None:
        self.package_dir = package_dir
        self.blockers: list[str] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.evidence: dict[str, Any] = {}
        self.harness_validated = 0
        self.stage_packets: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.source_texts: dict[str, tuple[dict[str, Any], str]] = {}
        self.mode = "map"
        self.data: dict[str, Any] = {}

    def block(self, message: str) -> None:
        self.blockers.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def validate_stage_packet(self, packet_path: Path, label: str) -> None:
        if not HARNESS_VALIDATOR.is_file():
            self.block(f"{label}: harness validator is unavailable")
            return
        try:
            result = subprocess.run(
                [sys.executable, str(HARNESS_VALIDATOR), str(packet_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            self.block(f"{label}: harness validation timed out")
            return
        except OSError as exc:
            self.block(f"{label}: harness validation could not run: {exc}")
            return
        if result.returncode != 0:
            detail = (result.stdout or result.stderr).strip()
            self.block(
                f"{label}: harness validation failed"
                + (f": {detail}" if detail else "")
            )
            return
        self.harness_validated += 1

    def resolve_json_reference(
        self, reference: Any, base: Path, label: str
    ) -> tuple[Path | None, dict[str, Any] | None]:
        path = self.resolve_file_reference(reference, base, label)
        if path is None:
            return None, None
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            self.block(f"{label}: referenced JSON is invalid: {exc}")
            return None, None
        if not isinstance(data, dict):
            self.block(f"{label}: referenced JSON root is not an object")
            return None, None
        return path, data

    def resolve_file_reference(
        self,
        reference: Any,
        base: Path,
        label: str,
        *,
        blocking: bool = True,
    ) -> Path | None:
        report = self.block if blocking else self.error
        if not isinstance(reference, dict):
            report(f"{label}: reference is not an object")
            return None
        relative = reference.get("path")
        expected = reference.get("sha256")
        if not nonempty_string(relative) or not isinstance(expected, str):
            report(f"{label}: path or sha256 is missing")
            return None
        if not SHA256_PATTERN.fullmatch(expected):
            report(f"{label}: sha256 is malformed")
            return None
        candidate = (base / relative).resolve()
        if not candidate.is_file():
            report(f"{label}: referenced file is missing: {candidate}")
            return None
        try:
            actual = sha256(candidate)
        except OSError as exc:
            report(f"{label}: referenced file is unreadable: {exc}")
            return None
        if actual.lower() != expected.lower():
            report(f"{label}: hash mismatch")
            return None
        return candidate

    def validate_input_gate(self, data: dict[str, Any]) -> None:
        gate = data.get("input_gate")
        if not isinstance(gate, dict):
            self.block("input_gate is missing")
            return
        run_id = data.get("run_id")
        state_path, state = self.resolve_json_reference(
            gate.get("run_state"), self.package_dir, "run_state"
        )
        if state is None or state_path is None:
            state = {}
        else:
            if state.get("harness") != HARNESS or state.get("run_id") != run_id:
                self.block("run_state belongs to another harness or run")
            if state.get("active_return") is not None:
                self.block("run_state has an active return package")

        interview_refs = gate.get("interview_completions")
        if not isinstance(interview_refs, list):
            self.block("input_gate.interview_completions is not an array")
            interview_refs = []
        seen: dict[str, tuple[Path, str]] = {}
        for index, reference in enumerate(interview_refs):
            stage = reference.get("stage") if isinstance(reference, dict) else None
            if stage not in INTERVIEW_STAGES:
                self.block(f"interview_completions[{index}] has invalid stage")
                continue
            if stage in seen:
                self.block(f"duplicate interview completion stage: {stage}")
                continue
            packet_ref = {
                "path": reference.get("path"),
                "sha256": reference.get("sha256"),
            }
            packet_path, packet = self.resolve_json_reference(
                packet_ref, self.package_dir, f"{stage} completion"
            )
            if packet_path is None or packet is None:
                continue
            if (
                packet.get("harness") != HARNESS
                or packet.get("run_id") != run_id
                or packet.get("stage") != stage
                or packet.get("status") != "ready"
            ):
                self.block(f"{stage} completion is not ready for this run")
            self.validate_stage_packet(packet_path, f"{stage} completion")
            seen[stage] = (packet_path, str(reference.get("sha256")).lower())
            self.stage_packets[stage] = (packet_path, packet)
        missing = set(INTERVIEW_STAGES) - set(seen)
        if missing:
            self.block("missing interview completions: " + ", ".join(sorted(missing)))
        if len(interview_refs) != len(INTERVIEW_STAGES):
            self.block("interview completions must contain exactly I0-I5")

        current = state.get("current_interview_completions")
        if not isinstance(current, dict):
            self.block("run_state.current_interview_completions is invalid")
        else:
            for stage, (packet_path, expected_hash) in seen.items():
                reference = current.get(stage)
                if not isinstance(reference, dict):
                    self.block(f"run_state does not name current {stage}")
                    continue
                relative = reference.get("path")
                if not nonempty_string(relative):
                    self.block(f"run_state current {stage} path is invalid")
                    continue
                current_path = (state_path.parent / relative).resolve()
                if (
                    current_path != packet_path
                    or str(reference.get("sha256", "")).lower() != expected_hash
                ):
                    self.block(f"input does not consume current {stage} completion")

        for stage in ("V1", "V2"):
            path, packet = self.resolve_json_reference(
                gate.get(f"{stage.lower()}_completion"),
                self.package_dir,
                f"{stage} completion",
            )
            if path is None or packet is None:
                continue
            if (
                packet.get("harness") != HARNESS
                or packet.get("run_id") != run_id
                or packet.get("stage") != stage
                or packet.get("status") != "ready"
            ):
                self.block(f"{stage} completion is not ready for this run")
            self.validate_stage_packet(path, f"{stage} completion")
            self.stage_packets[stage] = (path, packet)

        v1_entry = self.stage_packets.get("V1")
        if v1_entry:
            v1_path, v1 = v1_entry
            _, semantic = self.resolve_json_reference(
                v1.get("semantic_review"), v1_path.parent, "V1 semantic review"
            )
            if semantic is not None and (
                semantic.get("harness") != HARNESS
                or semantic.get("run_id") != run_id
                or semantic.get("stage") != "V1"
                or semantic.get("verdict") != "pass"
                or semantic.get("return_package") is not None
            ):
                self.block("V1 semantic review is not a passing review")

        approval_path, approval = self.resolve_json_reference(
            gate.get("author_approval"), self.package_dir, "V2 author approval"
        )
        if approval is not None and approval_path is not None:
            if (
                approval.get("harness") != HARNESS
                or approval.get("run_id") != run_id
                or approval.get("approval_scope") != "V2"
                or approval.get("decision") != "approved"
                or approval.get("record_assurance") != "self_recorded"
            ):
                self.block("author approval does not approve this V2 run")
            record = approval.get("approval_record")
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("event_seq"), int)
                or not nonempty_string(record.get("text"))
            ):
                self.block("author approval lacks a recorded explicit decision")
            brief_path = self.resolve_file_reference(
                approval.get("review_brief"), approval_path.parent, "approved V2 brief"
            )
            v2_entry = self.stage_packets.get("V2")
            if brief_path is not None and v2_entry:
                v2_path, v2 = v2_entry
                artifact = v2.get("design_artifact")
                artifact_hash = v2.get("design_artifact_sha256")
                if (
                    not nonempty_string(artifact)
                    or not isinstance(artifact_hash, str)
                    or (v2_path.parent / artifact).resolve() != brief_path
                    or artifact_hash.lower()
                    != str(approval.get("review_brief", {}).get("sha256", "")).lower()
                ):
                    self.block("author approval is not bound to the current V2 artifact")

        self.evidence["input_gate"] = {
            "interview_completions": len(seen),
            "v1_checked": "V1" in self.stage_packets,
            "v2_checked": "V2" in self.stage_packets,
            "author_approval_checked": approval is not None,
            "harness_validated_packets": self.harness_validated,
            "active_return": state.get("active_return"),
        }

    def validate_source_artifacts(self, data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        records = data.get("source_artifacts")
        by_id: dict[str, dict[str, Any]] = {}
        seen_areas: set[str] = set()
        if not isinstance(records, list):
            self.error("source_artifacts must be an array")
            records = []
        for index, record in enumerate(records):
            label = f"source_artifacts[{index}]"
            if not isinstance(record, dict):
                self.error(f"{label} is not an object")
                continue
            artifact_id = record.get("id")
            area = record.get("area")
            stage = record.get("stage")
            if not nonempty_string(artifact_id) or not ID_PATTERN.fullmatch(artifact_id):
                self.error(f"{label}.id is invalid")
                continue
            if artifact_id in by_id:
                self.error(f"duplicate source artifact id: {artifact_id}")
                continue
            if area not in AREAS or stage != AREAS.get(area):
                self.error(f"{artifact_id}: area and stage do not match")
                continue
            if area in seen_areas:
                self.error(f"duplicate source artifact area: {area}")
                continue
            packet_entry = self.stage_packets.get(stage)
            path = self.resolve_file_reference(
                record, self.package_dir, artifact_id, blocking=False
            )
            if packet_entry is None or path is None:
                continue
            packet_path, packet = packet_entry
            design_artifact = packet.get("design_artifact")
            expected_path = (
                (packet_path.parent / design_artifact).resolve()
                if nonempty_string(design_artifact)
                else None
            )
            if (
                path != expected_path
                or str(record.get("sha256", "")).lower()
                != str(packet.get("design_artifact_sha256", "")).lower()
            ):
                self.error(
                    f"{artifact_id}: source artifact is not the design artifact "
                    f"bound by {stage} completion"
                )
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                self.error(f"{artifact_id}: source artifact is unreadable: {exc}")
                continue
            by_id[artifact_id] = record
            seen_areas.add(area)
            self.source_texts[artifact_id] = (record, text)
        missing = set(AREAS) - seen_areas
        if missing:
            self.error("missing source artifact areas: " + ", ".join(sorted(missing)))
        if len(records) != len(AREAS):
            self.error("source_artifacts must contain exactly six records")
        self.evidence["source_artifacts"] = {
            "validated": len(by_id),
            "areas": sorted(seen_areas),
        }
        return by_id

    def validate_control_points(
        self, data: dict[str, Any], artifacts: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        controls = data.get("control_points")
        by_id: dict[str, dict[str, Any]] = {}
        area_counts = {area: 0 for area in AREAS}
        if not isinstance(controls, list) or not controls:
            self.error("control_points must be a non-empty array")
            return by_id
        for index, control in enumerate(controls):
            label = f"control_points[{index}]"
            if not isinstance(control, dict):
                self.error(f"{label} is not an object")
                continue
            control_id = control.get("id")
            if not nonempty_string(control_id) or not ID_PATTERN.fullmatch(control_id):
                self.error(f"{label}.id is invalid")
                continue
            if control_id in by_id:
                self.error(f"duplicate control id: {control_id}")
                continue
            area = control.get("area")
            if area not in AREAS:
                self.error(f"{control_id}: invalid control area")
            else:
                area_counts[area] += 1
                if control.get("owner_stage") != AREAS[area]:
                    self.error(f"{control_id}: owner_stage does not match control area")
            if control.get("hardness") not in HARDNESS:
                self.error(f"{control_id}: invalid hardness")
            if not nonempty_string(control.get("kind")):
                self.error(f"{control_id}: kind is missing")
            if not nonempty_string(control.get("text"), 12):
                self.error(f"{control_id}: text is too small to be an auditable control")
            if "development_effect" in control:
                self.error(
                    f"{control_id}: development_effect is not allowed; "
                    "development meaning belongs in hash-bound derivation_claims"
                )
            sources = control.get("sources")
            if not isinstance(sources, list) or not sources:
                self.error(f"{control_id}: sources must be a non-empty array")
                sources = []
            owner_area_proved = False
            owner_statement_proved = False
            for source_index, source in enumerate(sources):
                source_label = f"{control_id}.sources[{source_index}]"
                if not isinstance(source, dict):
                    self.error(f"{source_label} is not an object")
                    continue
                artifact_id = source.get("artifact_id")
                if artifact_id not in artifacts or artifact_id not in self.source_texts:
                    self.error(f"{source_label}: unknown artifact_id {artifact_id}")
                    continue
                artifact_record, text = self.source_texts[artifact_id]
                source_is_valid = True
                section = source.get("section")
                evidence = source.get("evidence")
                evidence_hash = source.get("evidence_sha256")
                if not nonempty_string(section):
                    self.error(f"{source_label}: section is missing")
                    source_is_valid = False
                    continue
                sections = markdown_sections(text).get(section, [])
                if len(sections) != 1:
                    self.error(
                        f"{source_label}: section must identify one exact Markdown heading"
                    )
                    source_is_valid = False
                    continue
                if not nonempty_string(evidence, 8):
                    self.error(f"{source_label}: evidence is too small")
                    source_is_valid = False
                elif evidence not in sections[0]:
                    self.error(
                        f"{source_label}: evidence does not occur in the named section"
                    )
                    source_is_valid = False
                if (
                    not isinstance(evidence_hash, str)
                    or not SHA256_PATTERN.fullmatch(evidence_hash)
                    or (isinstance(evidence, str) and text_sha256(evidence) != evidence_hash)
                ):
                    self.error(f"{source_label}: evidence_sha256 does not bind evidence")
                    source_is_valid = False
                if source_is_valid and artifact_record.get("area") == area:
                    owner_area_proved = True
                    if evidence == control.get("text"):
                        owner_statement_proved = True
            if area in AREAS and not owner_area_proved:
                self.error(
                    f"{control_id}: no source proves the control in its owner area"
                )
            if area in AREAS and not owner_statement_proved:
                self.error(
                    f"{control_id}: text must exactly equal a valid source statement "
                    "from its owner area"
                )
            by_id[control_id] = control
        for area, count in area_counts.items():
            if count == 0:
                self.error(f"control area has no control points: {area}")
        self.evidence["control_areas"] = area_counts
        return by_id

    def validate_authority_partition(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
    ) -> None:
        partition = data.get("authority_partition")
        if not isinstance(partition, dict):
            self.error("authority_partition is missing")
            return
        expected_fields = {
            "author_locked",
            "delegated",
            "open",
            "autonomous_mandate",
            "downstream_reserved",
            "prohibitions",
        }
        extra = set(partition) - expected_fields
        missing = expected_fields - set(partition)
        if extra:
            self.error(
                "authority_partition contains unsupported fields: "
                + ", ".join(sorted(extra))
            )
        if missing:
            self.error(
                "authority_partition is missing fields: "
                + ", ".join(sorted(missing))
            )
        expected_by_hardness = {
            "author_locked": {
                control_id
                for control_id, control in controls.items()
                if control.get("hardness") == "hard"
            },
            "delegated": {
                control_id
                for control_id, control in controls.items()
                if control.get("hardness") == "delegated"
            },
            "open": {
                control_id
                for control_id, control in controls.items()
                if control.get("hardness") == "open"
            },
        }
        for field, expected in expected_by_hardness.items():
            values = partition.get(field)
            if not string_list(values, nonempty=False):
                self.error(f"authority_partition.{field} must be a string array")
                values = []
            if len(values) != len(set(values)):
                self.error(f"authority_partition.{field} contains duplicates")
            if set(values) != expected:
                self.error(
                    f"authority_partition.{field} must exactly match "
                    f"{field.replace('_', ' ')} controls"
                )
        for field in (
            "autonomous_mandate",
            "downstream_reserved",
            "prohibitions",
        ):
            if not nonempty_string(partition.get(field), 20):
                self.error(f"authority_partition.{field} is too small")
        self.evidence["authority_partition"] = {
            field: len(values)
            for field, values in expected_by_hardness.items()
        }

    def validate_development_gaps(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        records = data.get("development_gaps")
        by_id: dict[str, dict[str, Any]] = {}
        if not isinstance(records, list) or not records:
            self.error("development_gaps must be a non-empty array")
            return by_id
        for index, gap in enumerate(records):
            label = f"development_gaps[{index}]"
            if not isinstance(gap, dict):
                self.error(f"{label} is not an object")
                continue
            gap_id = gap.get("id")
            if not nonempty_string(gap_id) or not ID_PATTERN.fullmatch(gap_id):
                self.error(f"{label}.id is invalid")
                continue
            if gap_id in by_id:
                self.error(f"duplicate development gap id: {gap_id}")
                continue
            if gap.get("domain") not in DEVELOPMENT_DOMAINS:
                self.error(f"{gap_id}: invalid domain")
            if gap.get("kind") not in DEVELOPMENT_GAP_KINDS:
                self.error(f"{gap_id}: invalid kind")
            for field in ("question", "why_needed"):
                if not nonempty_string(gap.get(field), 20):
                    self.error(f"{gap_id}: {field} is too small")
            source_controls = gap.get("source_controls")
            if not string_list(source_controls, nonempty=True):
                self.error(
                    f"{gap_id}: source_controls must be a non-empty string array"
                )
                source_controls = []
            for control_id in source_controls:
                if control_id not in controls:
                    self.error(f"{gap_id}: unknown source control {control_id}")
            decision_ids = gap.get("decision_ids")
            if not string_list(decision_ids, nonempty=False):
                self.error(f"{gap_id}: decision_ids must be a string array")
                decision_ids = []
            resolution = gap.get("resolution")
            if resolution not in DEVELOPMENT_GAP_RESOLUTIONS:
                self.error(f"{gap_id}: invalid resolution")
            reservation = gap.get("downstream_reservation")
            if resolution == "autonomous_decision":
                if not decision_ids:
                    self.error(
                        f"{gap_id}: autonomous_decision requires decision_ids"
                    )
                if reservation is not None:
                    self.error(
                        f"{gap_id}: autonomous_decision cannot reserve the gap downstream"
                    )
            else:
                if decision_ids:
                    self.error(
                        f"{gap_id}: {resolution} cannot contain decision_ids"
                    )
                if not nonempty_string(reservation, 20):
                    self.error(
                        f"{gap_id}: {resolution} requires downstream_reservation"
                    )
                if (
                    resolution == "author_open"
                    and not any(
                        controls.get(control_id, {}).get("hardness") == "open"
                        for control_id in source_controls
                    )
                ):
                    self.error(
                        f"{gap_id}: author_open must cite at least one open control"
                    )
            by_id[gap_id] = gap
        self.evidence["development_gaps"] = {
            "count": len(by_id),
            "autonomous": sum(
                1
                for gap in by_id.values()
                if gap.get("resolution") == "autonomous_decision"
            ),
            "downstream": sum(
                1
                for gap in by_id.values()
                if gap.get("resolution") == "downstream_freedom"
            ),
            "author_open": sum(
                1
                for gap in by_id.values()
                if gap.get("resolution") == "author_open"
            ),
        }
        return by_id

    def validate_design_decisions(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        gaps: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        records = data.get("design_decisions")
        by_id: dict[str, dict[str, Any]] = {}
        if not isinstance(records, list) or not records:
            self.error("design_decisions must be a non-empty array")
            return by_id
        control_texts = {
            str(control.get("text", "")).strip()
            for control in controls.values()
        }
        for index, decision in enumerate(records):
            label = f"design_decisions[{index}]"
            if not isinstance(decision, dict):
                self.error(f"{label} is not an object")
                continue
            decision_id = decision.get("id")
            if (
                not nonempty_string(decision_id)
                or not ID_PATTERN.fullmatch(decision_id)
            ):
                self.error(f"{label}.id is invalid")
                continue
            if decision_id in by_id:
                self.error(f"duplicate design decision id: {decision_id}")
                continue
            if decision.get("domain") not in DEVELOPMENT_DOMAINS:
                self.error(f"{decision_id}: invalid domain")
            if decision.get("kind") not in DEVELOPMENT_GAP_KINDS:
                self.error(f"{decision_id}: invalid kind")
            for field in (
                "statement",
                "function",
                "authority_basis",
                "necessity",
                "compatibility",
            ):
                if not nonempty_string(decision.get(field), 20):
                    self.error(f"{decision_id}: {field} is too small")
            if str(decision.get("statement", "")).strip() in control_texts:
                self.error(
                    f"{decision_id}: statement merely repeats an upstream control"
                )
            gap_ids = decision.get("gap_ids")
            if not string_list(gap_ids, nonempty=True):
                self.error(f"{decision_id}: gap_ids must be non-empty")
                gap_ids = []
            for gap_id in gap_ids:
                gap = gaps.get(gap_id)
                if gap is None:
                    self.error(f"{decision_id}: unknown development gap {gap_id}")
                elif gap.get("resolution") != "autonomous_decision":
                    self.error(
                        f"{decision_id}: gap is not delegated to autonomous design: "
                        f"{gap_id}"
                    )
            source_controls = decision.get("source_controls")
            if not string_list(source_controls, nonempty=True):
                self.error(
                    f"{decision_id}: source_controls must be a non-empty string array"
                )
                source_controls = []
            for control_id in source_controls:
                if control_id not in controls:
                    self.error(
                        f"{decision_id}: unknown source control {control_id}"
                    )
            if decision.get("novelty") not in DESIGN_DECISION_NOVELTY:
                self.error(f"{decision_id}: invalid novelty")
            if decision.get("impact") not in DESIGN_DECISION_IMPACT:
                self.error(f"{decision_id}: invalid impact")
            if decision.get("reversibility") not in DESIGN_DECISION_REVERSIBILITY:
                self.error(f"{decision_id}: invalid reversibility")
            alternatives = decision.get("alternatives")
            if not isinstance(alternatives, list) or len(alternatives) < 2:
                self.error(
                    f"{decision_id}: alternatives must contain at least two options"
                )
                alternatives = []
            alternative_ids: set[str] = set()
            selected = 0
            for alt_index, alternative in enumerate(alternatives):
                alt_label = f"{decision_id}.alternatives[{alt_index}]"
                if not isinstance(alternative, dict):
                    self.error(f"{alt_label} is not an object")
                    continue
                alt_id = alternative.get("id")
                if (
                    not nonempty_string(alt_id)
                    or not ID_PATTERN.fullmatch(alt_id)
                    or alt_id in alternative_ids
                ):
                    self.error(f"{alt_label}.id is invalid or duplicated")
                else:
                    alternative_ids.add(alt_id)
                for field in ("proposal", "benefit", "cost"):
                    if not nonempty_string(alternative.get(field), 12):
                        self.error(f"{alt_label}.{field} is too small")
                status = alternative.get("status")
                if status not in ALTERNATIVE_STATUS:
                    self.error(f"{alt_label}.status is invalid")
                if status == "selected":
                    selected += 1
            if selected != 1:
                self.error(
                    f"{decision_id}: alternatives must contain exactly one selected option"
                )
            projected = decision.get("projected_subjects")
            if not string_list(projected, nonempty=True):
                self.error(f"{decision_id}: projected_subjects must be non-empty")
            freedom = decision.get("downstream_freedom")
            if not string_list(freedom, nonempty=True):
                self.error(
                    f"{decision_id}: downstream_freedom must be a non-empty string array"
                )
            by_id[decision_id] = decision

        expected_links = {
            gap_id: set(string_values(gap.get("decision_ids")))
            for gap_id, gap in gaps.items()
            if gap.get("resolution") == "autonomous_decision"
        }
        observed_links = {gap_id: set() for gap_id in expected_links}
        for decision_id, decision in by_id.items():
            for gap_id in string_values(decision.get("gap_ids")):
                if gap_id in observed_links:
                    observed_links[gap_id].add(decision_id)
        for gap_id, expected in expected_links.items():
            if observed_links.get(gap_id, set()) != expected:
                self.error(
                    f"{gap_id}: decision_ids do not exactly match reverse decision links"
                )
        self.evidence["design_decisions"] = {
            "count": len(by_id),
            "structural": sum(
                1
                for decision in by_id.values()
                if decision.get("impact") == "structural"
            ),
        }
        return by_id

    def validate_information_obligations(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        obligations = data.get("information_obligations")
        by_id: dict[str, dict[str, Any]] = {}
        if not isinstance(obligations, list):
            self.error("information_obligations must be an array")
            return by_id
        for index, obligation in enumerate(obligations):
            label = f"information_obligations[{index}]"
            if not isinstance(obligation, dict):
                self.error(f"{label} is not an object")
                continue
            obligation_id = obligation.get("id")
            if (
                not nonempty_string(obligation_id)
                or not ID_PATTERN.fullmatch(obligation_id)
            ):
                self.error(f"{label}.id is invalid")
                continue
            if obligation_id in by_id:
                self.error(f"duplicate information obligation id: {obligation_id}")
                continue
            if not nonempty_string(obligation.get("statement"), 12):
                self.error(f"{obligation_id}: statement is too small")
            source_controls = obligation.get("source_controls")
            if not string_list(source_controls, nonempty=True):
                self.error(
                    f"{obligation_id}: source_controls must be a non-empty string array"
                )
                source_controls = []
            for control_id in source_controls:
                if control_id not in controls:
                    self.error(
                        f"{obligation_id}: unknown source control {control_id}"
                    )
            audience = obligation.get("audience")
            if audience not in INFORMATION_AUDIENCES:
                self.error(f"{obligation_id}: invalid audience")
            knowledge_holders = obligation.get("knowledge_holder_controls")
            if not string_list(knowledge_holders, nonempty=False):
                self.error(
                    f"{obligation_id}: knowledge_holder_controls must be a "
                    "string array"
                )
                knowledge_holders = []
            elif len(set(knowledge_holders)) != len(knowledge_holders):
                self.error(
                    f"{obligation_id}: knowledge_holder_controls contains duplicates"
                )
            if audience in {"story_characters", "mixed"} and not knowledge_holders:
                self.error(
                    f"{obligation_id}: {audience} audience requires "
                    "knowledge_holder_controls"
                )
            source_control_set = set(source_controls)
            for control_id in knowledge_holders:
                if control_id not in controls:
                    self.error(
                        f"{obligation_id}: unknown knowledge-holder control "
                        f"{control_id}"
                    )
                if control_id not in source_control_set:
                    self.error(
                        f"{obligation_id}: knowledge-holder control is absent "
                        f"from source_controls: {control_id}"
                    )
            resolution = obligation.get("resolution")
            if resolution not in INFORMATION_RESOLUTIONS:
                self.error(f"{obligation_id}: invalid resolution")
            series_interface = obligation.get("series_interface")
            if resolution == "series":
                if not nonempty_string(series_interface, 12):
                    self.error(
                        f"{obligation_id}: series resolution requires series_interface"
                    )
            elif series_interface is not None:
                self.error(
                    f"{obligation_id}: within_book resolution must not set series_interface"
                )
            by_id[obligation_id] = obligation
        self.evidence["information_obligations"] = {
            "declared": len(by_id),
            "within_book": sum(
                item.get("resolution") == "within_book"
                for item in by_id.values()
            ),
            "series": sum(
                item.get("resolution") == "series" for item in by_id.values()
            ),
        }
        return by_id

    def validate_units(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        obligations: dict[str, dict[str, Any]],
        decisions: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        allowed_povs = data.get("allowed_povs")
        if not string_list(allowed_povs, nonempty=True):
            self.error("allowed_povs must be a non-empty string array")
            allowed_povs = []
        elif len(set(allowed_povs)) != len(allowed_povs):
            self.error("allowed_povs contains duplicates")
        for control_id in allowed_povs:
            if control_id not in controls:
                self.error(f"allowed_povs contains unknown control {control_id}")
            elif controls[control_id].get("area") != "narrative":
                self.error(
                    f"allowed_povs control must belong to narrative: {control_id}"
                )
        units = data.get("units")
        by_id: dict[str, dict[str, Any]] = {}
        if not isinstance(units, list) or not units:
            self.error("units must be a non-empty array")
            return by_id
        for index, unit in enumerate(units):
            label = f"units[{index}]"
            if not isinstance(unit, dict):
                self.error(f"{label} is not an object")
                continue
            unit_id = unit.get("id")
            if not nonempty_string(unit_id) or not ID_PATTERN.fullmatch(unit_id):
                self.error(f"{label}.id is invalid")
                continue
            if unit_id in by_id:
                self.error(f"duplicate unit id: {unit_id}")
                continue
            for field in (
                "title",
                "purpose",
                "objective",
                "obstacle",
                "choice",
                "choice_cost",
                "consequence",
                "next_pressure",
                "exit_state",
            ):
                if not nonempty_string(unit.get(field)):
                    self.error(f"{unit_id}: {field} is missing")
            for field in (
                "source_controls",
                "causal_nodes",
                "preconditions",
                "creative_freedom",
            ):
                if not string_list(unit.get(field), nonempty=True):
                    self.error(f"{unit_id}: {field} must be a non-empty string array")
            for field in (
                "world_constraints",
                "prohibitions",
                "depends_on",
                "development_decisions",
            ):
                if not string_list(unit.get(field), nonempty=False):
                    self.error(f"{unit_id}: {field} must be a string array")
            for decision_id in string_values(unit.get("development_decisions")):
                if decision_id not in decisions:
                    self.error(
                        f"{unit_id}: unknown development decision {decision_id}"
                    )
            opposition = unit.get("opposition")
            if not isinstance(opposition, dict):
                self.error(f"{unit_id}: opposition is missing")
            else:
                for field in ("force", "goal", "tactic", "leverage", "adaptation"):
                    if not nonempty_string(opposition.get(field), 8):
                        self.error(f"{unit_id}: opposition.{field} is too small")
            options = unit.get("choice_options")
            if not isinstance(options, list) or len(options) < 2:
                self.error(
                    f"{unit_id}: choice_options must contain at least two options"
                )
                options = []
            selected_options = 0
            option_ids: set[str] = set()
            for option_index, option in enumerate(options):
                option_label = f"{unit_id}.choice_options[{option_index}]"
                if not isinstance(option, dict):
                    self.error(f"{option_label} is not an object")
                    continue
                option_id = option.get("id")
                if (
                    not nonempty_string(option_id)
                    or not ID_PATTERN.fullmatch(option_id)
                    or option_id in option_ids
                ):
                    self.error(f"{option_label}.id is invalid or duplicated")
                else:
                    option_ids.add(option_id)
                for field in ("option", "attraction", "cost"):
                    if not nonempty_string(option.get(field), 8):
                        self.error(f"{option_label}.{field} is too small")
                status = option.get("status")
                if status not in ALTERNATIVE_STATUS:
                    self.error(f"{option_label}.status is invalid")
                if status == "selected":
                    selected_options += 1
            if selected_options != 1:
                self.error(
                    f"{unit_id}: choice_options must contain exactly one selected option"
                )
            for control_id in string_values(unit.get("source_controls")):
                if control_id not in controls:
                    self.error(f"{unit_id}: unknown source control {control_id}")
            source_control_set = set(string_values(unit.get("source_controls")))
            reference_areas = {
                "causal_nodes": "causality",
                "world_constraints": "world",
            }
            for field, expected_area in reference_areas.items():
                values = string_values(unit.get(field))
                for control_id in values:
                    if control_id not in controls:
                        self.error(f"{unit_id}: unknown {field} control {control_id}")
                    elif controls[control_id].get("area") != expected_area:
                        self.error(
                            f"{unit_id}: {field} control must belong to "
                            f"{expected_area}: {control_id}"
                        )
                    if control_id not in source_control_set:
                        self.error(
                            f"{unit_id}: {field} control is absent from "
                            f"source_controls: {control_id}"
                        )
            for control_id in string_values(unit.get("prohibitions")):
                if control_id not in controls:
                    self.error(
                        f"{unit_id}: unknown prohibitions control {control_id}"
                    )
                if control_id not in source_control_set:
                    self.error(
                        f"{unit_id}: prohibitions control is absent from "
                        f"source_controls: {control_id}"
                    )
            if unit.get("pov") not in allowed_povs:
                self.error(f"{unit_id}: POV is not in allowed_povs")
            elif unit.get("pov") not in source_control_set:
                self.error(f"{unit_id}: POV control is absent from source_controls")
            if unit.get("scale") not in SCALES:
                self.error(f"{unit_id}: invalid scale")
            shift = unit.get("value_shift")
            if not isinstance(shift, dict):
                self.error(f"{unit_id}: value_shift is missing")
            else:
                for field in ("axis", "before", "after", "turning_cause"):
                    if not nonempty_string(shift.get(field)):
                        self.error(f"{unit_id}: value_shift.{field} is missing")
                if shift.get("before") == shift.get("after"):
                    self.error(f"{unit_id}: value_shift before and after are identical")
            information = unit.get("information")
            if not isinstance(information, dict):
                self.error(f"{unit_id}: information is missing")
            else:
                for field in ("establish", "hint", "withhold", "payoff"):
                    if not string_list(information.get(field), nonempty=False):
                        self.error(f"{unit_id}: information.{field} must be a string array")
                        continue
                    if len(set(information[field])) != len(information[field]):
                        self.error(
                            f"{unit_id}: information.{field} contains duplicates"
                        )
                    for obligation_id in information[field]:
                        if obligation_id not in obligations:
                            self.error(
                                f"{unit_id}: information.{field} references "
                                f"unknown obligation {obligation_id}"
                            )
            by_id[unit_id] = unit

        order = {
            unit["id"]: index
            for index, unit in enumerate(units)
            if isinstance(unit, dict) and unit.get("id") in by_id
        }
        for unit_id, unit in by_id.items():
            for dependency in string_values(unit.get("depends_on")):
                if dependency not in by_id:
                    self.error(f"{unit_id}: unknown dependency {dependency}")
                elif order[dependency] >= order[unit_id]:
                    self.error(f"{unit_id}: dependency {dependency} is not earlier")
        self.validate_acyclic(by_id)
        self.evidence["units"] = {
            "count": len(by_id),
            "allowed_povs": allowed_povs,
        }
        return by_id

    def validate_conception(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
        decisions: dict[str, dict[str, Any]],
    ) -> None:
        conception = data.get("conception")
        if not isinstance(conception, dict):
            self.error("conception must contain world, story and characters")
            return
        if set(conception) != {"world", "story", "characters"}:
            self.error("conception must contain exactly world, story and characters")

        def reject_extra(
            record: dict[str, Any],
            allowed: set[str],
            label: str,
        ) -> None:
            extra = set(record) - allowed
            if extra:
                self.error(
                    f"{label} contains unsupported fields: "
                    + ", ".join(sorted(extra))
                )

        def validate_sources(
            record: dict[str, Any],
            label: str,
            *,
            required_areas: set[str],
        ) -> list[str]:
            sources = record.get("source_controls")
            if not string_list(sources, nonempty=True):
                self.error(f"{label}.source_controls must be non-empty")
                return []
            if len(sources) != len(set(sources)):
                self.error(f"{label}.source_controls contains duplicates")
            observed_areas: set[str] = set()
            for control_id in sources:
                control = controls.get(control_id)
                if control is None:
                    self.error(f"{label}: unknown source control {control_id}")
                else:
                    observed_areas.add(str(control.get("area")))
            missing = required_areas - observed_areas
            if missing:
                self.error(
                    f"{label}: source controls do not cover required areas: "
                    + ", ".join(sorted(missing))
                )
            return list(sources)

        def validate_text_fields(
            record: dict[str, Any],
            fields: tuple[str, ...],
            label: str,
        ) -> None:
            for field in fields:
                if not nonempty_string(record.get(field), 4):
                    self.error(f"{label}.{field} is too small")

        def validate_list_fields(
            record: dict[str, Any],
            fields: tuple[str, ...],
            label: str,
            *,
            nonempty: set[str],
        ) -> None:
            for field in fields:
                values = record.get(field)
                if not string_list(values, nonempty=field in nonempty):
                    self.error(f"{label}.{field} must be a string array")
                    continue
                if len(values) != len(set(values)):
                    self.error(f"{label}.{field} contains duplicates")
                for index, value in enumerate(values):
                    if not nonempty_string(value, 8):
                        self.error(f"{label}.{field}[{index}] is too small")

        def validate_decision_links(
            record: dict[str, Any],
            label: str,
            *,
            nonempty: bool,
        ) -> None:
            values = record.get("development_decisions")
            if not string_list(values, nonempty=nonempty):
                self.error(
                    f"{label}.development_decisions must be "
                    + ("non-empty" if nonempty else "a string array")
                )
                return
            if len(values) != len(set(values)):
                self.error(f"{label}.development_decisions contains duplicates")
            for decision_id in values:
                if decision_id not in decisions:
                    self.error(f"{label}: unknown design decision {decision_id}")

        environment_storyline_refs: list[tuple[str, str]] = []
        environment_storylines_by_id: dict[str, set[str]] = {}
        environment_unit_coverage: set[str] = set()
        environment_ids: set[str] = set()
        unit_host_environments: dict[str, set[str]] = {}
        unit_environment_characters: dict[
            tuple[str, str], set[str]
        ] = {}
        environment_character_refs: list[tuple[str, str, str | None]] = []
        environment_zone_occupants: dict[
            str, dict[str, set[str]]
        ] = {}
        environment_event_bindings: list[
            tuple[str, str, set[str], set[str]]
        ] = []
        world_system_environment_refs: dict[str, set[str]] = {}
        world_system_event_refs: dict[str, set[str]] = {}
        event_environment_requirement_records: dict[
            str, dict[str, Any]
        ] = {}
        event_environment_requirement_events: dict[str, str] = {}
        event_environment_requirement_envs: dict[str, set[str]] = {}
        world = conception.get("world")
        if not isinstance(world, dict):
            self.error("conception.world is missing")
        else:
            reject_extra(
                world,
                {
                    "id",
                    "source_controls",
                    "facets",
                    "systems",
                    "environments",
                    "event_environment_requirements",
                    *WORLD_CONCEPTION_FIELDS,
                },
                "conception.world",
            )
            world_id = world.get("id")
            if (
                not nonempty_string(world_id)
                or not ID_PATTERN.fullmatch(str(world_id))
            ):
                self.error("conception.world.id is invalid")
            validate_sources(
                world,
                "conception.world",
                required_areas={"world"},
            )
            validate_text_fields(
                world,
                (
                    "definition",
                    "story_function",
                    "time_space_scope",
                    "end_state",
                ),
                "conception.world",
            )
            validate_list_fields(
                world,
                (
                    "operating_logic",
                    "power_and_resources",
                    "action_permissions",
                    "hard_constraints",
                    "pressure_sources",
                    "costs_and_consequences",
                    "scope_exclusions",
                ),
                "conception.world",
                nonempty={
                    "operating_logic",
                    "hard_constraints",
                    "pressure_sources",
                    "costs_and_consequences",
                    "scope_exclusions",
                },
            )
            facets = world.get("facets")
            if not isinstance(facets, list) or not facets:
                self.error("conception.world.facets must be non-empty")
                facets = []
            facet_ids: set[str] = set()
            facet_domains: set[str] = set()
            for index, facet in enumerate(facets):
                label = f"conception.world.facets[{index}]"
                if not isinstance(facet, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    facet,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *WORLD_FACET_FIELDS,
                    },
                    label,
                )
                facet_id = facet.get("id")
                if (
                    not nonempty_string(facet_id)
                    or not ID_PATTERN.fullmatch(str(facet_id))
                    or facet_id in facet_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                facet_ids.add(str(facet_id))
                domain = facet.get("domain")
                if domain not in WORLD_FACET_DOMAINS or domain in facet_domains:
                    self.error(f"{label}.domain is invalid or duplicated")
                else:
                    facet_domains.add(str(domain))
                if facet.get("status") not in WORLD_FACET_STATUS:
                    self.error(f"{label}.status is invalid")
                validate_sources(facet, label, required_areas={"world"})
                validate_text_fields(
                    facet,
                    ("definition", "story_relevance", "downstream_freedom"),
                    label,
                )
                validate_decision_links(
                    facet,
                    label,
                    nonempty=facet.get("status") == "defined",
                )
            if facet_domains != WORLD_FACET_DOMAINS:
                self.error(
                    "conception.world.facets must exactly cover all eight "
                    "world information domains"
                )

            systems = world.get("systems")
            if not isinstance(systems, list) or not systems:
                self.error("conception.world.systems must be non-empty")
                systems = []
            system_ids: set[str] = set()
            for index, system in enumerate(systems):
                label = f"conception.world.systems[{index}]"
                if not isinstance(system, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    system,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *WORLD_SYSTEM_FIELDS,
                    },
                    label,
                )
                system_id = system.get("id")
                if (
                    not nonempty_string(system_id)
                    or not ID_PATTERN.fullmatch(str(system_id))
                    or system_id in system_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                system_ids.add(str(system_id))
                if system.get("domain") not in WORLD_SYSTEM_DOMAINS:
                    self.error(f"{label}.domain is invalid")
                validate_sources(system, label, required_areas={"world"})
                validate_text_fields(
                    system,
                    (
                        "name",
                        "definition",
                        "transformation_rule",
                        "downstream_freedom",
                    ),
                    label,
                )
                validate_list_fields(
                    system,
                    (
                        "input_conditions",
                        "observable_outputs",
                        "actors",
                        "resources",
                        "rules",
                        "permissions",
                        "costs",
                        "limits",
                        "failure_modes",
                        "story_effects",
                        "state_changes",
                    ),
                    label,
                    nonempty={
                        "input_conditions",
                        "observable_outputs",
                        "actors",
                        "rules",
                        "permissions",
                        "costs",
                        "limits",
                        "failure_modes",
                        "story_effects",
                        "state_changes",
                    },
                )
                for field, target in (
                    ("environment_ids", world_system_environment_refs),
                    ("major_event_ids", world_system_event_refs),
                ):
                    values = system.get(field)
                    if not string_list(values, nonempty=True):
                        self.error(
                            f"{label}.{field} must be a non-empty string array"
                        )
                        values = []
                    elif len(values) != len(set(values)):
                        self.error(f"{label}.{field} contains duplicates")
                    target[str(system_id)] = set(string_values(values))
                validate_decision_links(system, label, nonempty=True)

            environments = world.get("environments")
            if not isinstance(environments, list) or not environments:
                self.error("conception.world.environments must be non-empty")
                environments = []
            for index, environment in enumerate(environments):
                label = f"conception.world.environments[{index}]"
                if not isinstance(environment, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    environment,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *WORLD_ENVIRONMENT_FIELDS,
                    },
                    label,
                )
                environment_id = environment.get("id")
                if (
                    not nonempty_string(environment_id)
                    or not ID_PATTERN.fullmatch(str(environment_id))
                    or environment_id in environment_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                environment_ids.add(str(environment_id))
                if (
                    environment.get("environment_type")
                    not in WORLD_ENVIRONMENT_TYPES
                ):
                    self.error(f"{label}.environment_type is invalid")
                validate_sources(
                    environment,
                    label,
                    required_areas={"world"},
                )
                validate_text_fields(
                    environment,
                    ("name", "definition", "scope", "downstream_freedom"),
                    label,
                )
                validate_list_fields(
                    environment,
                    (
                        "distinctive_features",
                        "basic_elements",
                        "sensory_conditions",
                        "occupants_and_access",
                        "resources_and_infrastructure",
                        "rules_and_affordances",
                        "hazards_and_pressures",
                        "story_functions",
                        "state_changes",
                    ),
                    label,
                    nonempty={
                        "distinctive_features",
                        "basic_elements",
                        "sensory_conditions",
                        "occupants_and_access",
                        "rules_and_affordances",
                        "hazards_and_pressures",
                        "story_functions",
                        "state_changes",
                    },
                )
                for left_field, right_field in (
                    ("distinctive_features", "sensory_conditions"),
                    ("basic_elements", "resources_and_infrastructure"),
                ):
                    left_value = normalized_business_text(
                        environment.get(left_field)
                    )
                    right_value = normalized_business_text(
                        environment.get(right_field)
                    )
                    if left_value and left_value == right_value:
                        self.error(
                            f"{label}: {left_field} and {right_field} must "
                            "perform different environment-design jobs"
                        )

                topology = environment.get("topology")
                zone_ids: set[str] = set()
                zone_occupants: dict[str, set[str]] = {}
                if not isinstance(topology, dict):
                    self.error(f"{label}.topology must be an object")
                    topology = {}
                else:
                    reject_extra(
                        topology,
                        {"boundaries", "zones", "connections"},
                        f"{label}.topology",
                    )
                boundaries = topology.get("boundaries")
                if not string_list(boundaries, nonempty=True):
                    self.error(
                        f"{label}.topology.boundaries must be a non-empty "
                        "string array"
                    )
                else:
                    if len(boundaries) != len(set(boundaries)):
                        self.error(
                            f"{label}.topology.boundaries contains duplicates"
                        )
                    for boundary_index, boundary in enumerate(boundaries):
                        if not nonempty_string(boundary, 8):
                            self.error(
                                f"{label}.topology.boundaries"
                                f"[{boundary_index}] is too small"
                            )

                zones = topology.get("zones")
                if not isinstance(zones, list) or not zones:
                    self.error(
                        f"{label}.topology.zones must be a non-empty array"
                    )
                    zones = []
                for zone_index, zone in enumerate(zones):
                    zone_label = (
                        f"{label}.topology.zones[{zone_index}]"
                    )
                    if not isinstance(zone, dict):
                        self.error(f"{zone_label} is not an object")
                        continue
                    reject_extra(
                        zone,
                        {
                            "id",
                            "name",
                            "function",
                            "state",
                            "occupant_ids",
                            "resources",
                        },
                        zone_label,
                    )
                    zone_id = zone.get("id")
                    if (
                        not nonempty_string(zone_id)
                        or not ID_PATTERN.fullmatch(str(zone_id))
                        or zone_id in zone_ids
                    ):
                        self.error(
                            f"{zone_label}.id is invalid or duplicated"
                        )
                        continue
                    zone_id = str(zone_id)
                    zone_ids.add(zone_id)
                    validate_text_fields(
                        zone,
                        ("name", "function", "state"),
                        zone_label,
                    )
                    occupants = zone.get("occupant_ids")
                    if not string_list(occupants, nonempty=False):
                        self.error(
                            f"{zone_label}.occupant_ids must be a string array"
                        )
                        occupants = []
                    elif len(occupants) != len(set(occupants)):
                        self.error(
                            f"{zone_label}.occupant_ids contains duplicates"
                        )
                    resources = zone.get("resources")
                    if not string_list(resources, nonempty=True):
                        self.error(
                            f"{zone_label}.resources must be a non-empty "
                            "string array"
                        )
                    else:
                        if len(resources) != len(set(resources)):
                            self.error(
                                f"{zone_label}.resources contains duplicates"
                            )
                        for resource_index, resource in enumerate(resources):
                            if not nonempty_string(resource, 8):
                                self.error(
                                    f"{zone_label}.resources"
                                    f"[{resource_index}] is too small"
                                )
                    zone_occupants[zone_id] = set(occupants)
                    environment_character_refs.extend(
                        (zone_label, character_id, None)
                        for character_id in occupants
                    )

                connections = topology.get("connections")
                if not isinstance(connections, list):
                    self.error(
                        f"{label}.topology.connections must be an array"
                    )
                    connections = []
                if len(zone_ids) > 1 and not connections:
                    self.error(
                        f"{label}.topology.connections must connect "
                        "multi-zone environments"
                    )
                adjacency: dict[str, set[str]] = {
                    zone_id: set() for zone_id in zone_ids
                }
                observed_connections: set[tuple[str, str, str]] = set()
                for connection_index, connection in enumerate(connections):
                    connection_label = (
                        f"{label}.topology.connections"
                        f"[{connection_index}]"
                    )
                    if not isinstance(connection, dict):
                        self.error(f"{connection_label} is not an object")
                        continue
                    reject_extra(
                        connection,
                        {
                            "from_zone",
                            "to_zone",
                            "channel",
                            "access_condition",
                            "blockage_effect",
                        },
                        connection_label,
                    )
                    validate_text_fields(
                        connection,
                        (
                            "from_zone",
                            "to_zone",
                            "channel",
                            "access_condition",
                            "blockage_effect",
                        ),
                        connection_label,
                    )
                    from_zone = connection.get("from_zone")
                    to_zone = connection.get("to_zone")
                    if (
                        from_zone not in zone_ids
                        or to_zone not in zone_ids
                        or from_zone == to_zone
                    ):
                        self.error(
                            f"{connection_label}: from_zone and to_zone "
                            "must reference different declared zones"
                        )
                        continue
                    connection_key = (
                        str(from_zone),
                        str(to_zone),
                        normalized_business_text(
                            connection.get("channel")
                        ),
                    )
                    if connection_key in observed_connections:
                        self.error(
                            f"{connection_label} duplicates a connection"
                        )
                    observed_connections.add(connection_key)
                    adjacency[str(from_zone)].add(str(to_zone))
                    adjacency[str(to_zone)].add(str(from_zone))
                if len(zone_ids) > 1:
                    start_zone = next(iter(zone_ids))
                    reached = {start_zone}
                    queue = [start_zone]
                    for current_zone in queue:
                        for next_zone in adjacency.get(current_zone, set()):
                            if next_zone in reached:
                                continue
                            reached.add(next_zone)
                            queue.append(next_zone)
                    if reached != zone_ids:
                        self.error(
                            f"{label}.topology must connect every declared zone"
                        )
                if nonempty_string(environment_id):
                    environment_zone_occupants[str(environment_id)] = (
                        zone_occupants
                    )

                environment_storylines = environment.get("storyline_ids")
                if not string_list(environment_storylines, nonempty=True):
                    self.error(f"{label}.storyline_ids must be non-empty")
                    environment_storylines = []
                if len(environment_storylines) != len(set(environment_storylines)):
                    self.error(f"{label}.storyline_ids contains duplicates")
                environment_storyline_refs.extend(
                    (label, storyline_id)
                    for storyline_id in environment_storylines
                )
                environment_storylines_by_id[str(environment_id)] = set(
                    environment_storylines
                )
                environment_units = environment.get("unit_ids")
                if not string_list(environment_units, nonempty=True):
                    self.error(f"{label}.unit_ids must be non-empty")
                    environment_units = []
                if len(environment_units) != len(set(environment_units)):
                    self.error(f"{label}.unit_ids contains duplicates")
                for unit_id in environment_units:
                    if unit_id not in units:
                        self.error(f"{label}: unknown unit {unit_id}")
                    else:
                        environment_unit_coverage.add(unit_id)

                event_hosting = environment.get("event_hosting")
                if not isinstance(event_hosting, list) or not event_hosting:
                    self.error(
                        f"{label}.event_hosting must be a non-empty array"
                    )
                    event_hosting = []
                hosted_units: set[str] = set()
                for event_index, event in enumerate(event_hosting):
                    event_label = f"{label}.event_hosting[{event_index}]"
                    if not isinstance(event, dict):
                        self.error(f"{event_label} is not an object")
                        continue
                    reject_extra(
                        event,
                        {
                            "unit_id",
                            "zone_ids",
                            "active_character_ids",
                            "event_function",
                            "entry_state",
                            "available_actions",
                            "blocked_actions",
                            "pressure",
                            "exit_state",
                        },
                        event_label,
                    )
                    validate_text_fields(
                        event,
                        (
                            "event_function",
                            "entry_state",
                            "pressure",
                            "exit_state",
                        ),
                        event_label,
                    )
                    unit_id = event.get("unit_id")
                    if (
                        not nonempty_string(unit_id)
                        or not ID_PATTERN.fullmatch(str(unit_id))
                    ):
                        self.error(f"{event_label}.unit_id is invalid")
                    if unit_id in hosted_units:
                        self.error(
                            f"{event_label}.unit_id is duplicated"
                        )
                    if isinstance(unit_id, str):
                        hosted_units.add(unit_id)
                    if unit_id not in environment_units:
                        self.error(
                            f"{event_label}.unit_id must belong to "
                            "environment.unit_ids"
                        )
                    used_zones = event.get("zone_ids")
                    if not string_list(used_zones, nonempty=True):
                        self.error(
                            f"{event_label}.zone_ids must be a non-empty "
                            "string array"
                        )
                        used_zones = []
                    elif len(used_zones) != len(set(used_zones)):
                        self.error(
                            f"{event_label}.zone_ids contains duplicates"
                        )
                    unknown_zones = set(used_zones) - zone_ids
                    if unknown_zones:
                        self.error(
                            f"{event_label}.zone_ids contains unknown zones: "
                            + ", ".join(sorted(unknown_zones))
                        )
                    active_characters = event.get(
                        "active_character_ids"
                    )
                    if not string_list(active_characters, nonempty=True):
                        self.error(
                            f"{event_label}.active_character_ids must be a "
                            "non-empty string array"
                        )
                        active_characters = []
                    elif len(active_characters) != len(
                        set(active_characters)
                    ):
                        self.error(
                            f"{event_label}.active_character_ids contains "
                            "duplicates"
                        )
                    for action_field in (
                        "available_actions",
                        "blocked_actions",
                    ):
                        actions = event.get(action_field)
                        if not string_list(actions, nonempty=True):
                            self.error(
                                f"{event_label}.{action_field} must be a "
                                "non-empty string array"
                            )
                            continue
                        if len(actions) != len(set(actions)):
                            self.error(
                                f"{event_label}.{action_field} contains "
                                "duplicates"
                            )
                        for action_index, action in enumerate(actions):
                            if not nonempty_string(action, 8):
                                self.error(
                                    f"{event_label}.{action_field}"
                                    f"[{action_index}] is too small"
                                )
                    available = {
                        normalized_business_text(action)
                        for action in string_values(
                            event.get("available_actions")
                        )
                    }
                    blocked = {
                        normalized_business_text(action)
                        for action in string_values(
                            event.get("blocked_actions")
                        )
                    }
                    if available & blocked:
                        self.error(
                            f"{event_label}: available_actions and "
                            "blocked_actions must be disjoint"
                        )
                    if normalized_business_text(
                        event.get("entry_state")
                    ) == normalized_business_text(
                        event.get("exit_state")
                    ):
                        self.error(
                            f"{event_label}: entry_state and exit_state "
                            "must differ"
                        )
                    environment_character_refs.extend(
                        (event_label, character_id, str(unit_id))
                        for character_id in active_characters
                    )
                    environment_event_bindings.append(
                        (
                            event_label,
                            str(environment_id),
                            set(used_zones),
                            set(active_characters),
                        )
                    )
                    if isinstance(unit_id, str) and nonempty_string(
                        environment_id
                    ):
                        host_environment_id = str(environment_id)
                        unit_host_environments.setdefault(
                            unit_id, set()
                        ).add(host_environment_id)
                        unit_environment_characters.setdefault(
                            (unit_id, host_environment_id), set()
                        ).update(active_characters)
                if hosted_units != set(environment_units):
                    self.error(
                        f"{label}.event_hosting must exactly cover "
                        "environment.unit_ids"
                    )
                validate_decision_links(environment, label, nonempty=True)

            environment_requirements = world.get(
                "event_environment_requirements"
            )
            if (
                not isinstance(environment_requirements, list)
                or not environment_requirements
            ):
                self.error(
                    "conception.world.event_environment_requirements "
                    "must be a non-empty array"
                )
                environment_requirements = []
            seen_requirement_events: set[str] = set()
            covered_requirement_environments: set[str] = set()
            for requirement_index, requirement in enumerate(
                environment_requirements
            ):
                requirement_label = (
                    "conception.world.event_environment_requirements"
                    f"[{requirement_index}]"
                )
                if not isinstance(requirement, dict):
                    self.error(f"{requirement_label} is not an object")
                    continue
                reject_extra(
                    requirement,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *EVENT_ENVIRONMENT_REQUIREMENT_FIELDS,
                    },
                    requirement_label,
                )
                requirement_id = requirement.get("id")
                if (
                    not nonempty_string(requirement_id)
                    or not ID_PATTERN.fullmatch(str(requirement_id))
                    or requirement_id in event_environment_requirement_records
                ):
                    self.error(
                        f"{requirement_label}.id is invalid or duplicated"
                    )
                    continue
                requirement_id = str(requirement_id)
                event_environment_requirement_records[requirement_id] = requirement
                validate_sources(
                    requirement,
                    requirement_label,
                    required_areas={"world", "causality"},
                )
                validate_decision_links(
                    requirement,
                    requirement_label,
                    nonempty=True,
                )
                validate_text_fields(
                    requirement,
                    ("adequacy_rationale",),
                    requirement_label,
                )
                event_id = requirement.get("major_event_id")
                if (
                    not nonempty_string(event_id)
                    or not ID_PATTERN.fullmatch(str(event_id))
                ):
                    self.error(
                        f"{requirement_label}.major_event_id is invalid"
                    )
                elif event_id in seen_requirement_events:
                    self.error(
                        f"{requirement_label}.major_event_id is duplicated"
                    )
                else:
                    seen_requirement_events.add(str(event_id))
                    event_environment_requirement_events[
                        requirement_id
                    ] = str(event_id)
                primary_environment_id = requirement.get(
                    "primary_environment_id"
                )
                if primary_environment_id not in environment_ids:
                    self.error(
                        f"{requirement_label}.primary_environment_id "
                        "must reference a declared environment"
                    )
                secondary_environment_ids = string_values(
                    requirement.get("secondary_environment_ids")
                )
                if not string_list(
                    requirement.get("secondary_environment_ids"),
                    nonempty=False,
                ):
                    self.error(
                        f"{requirement_label}.secondary_environment_ids "
                        "must be a string array"
                    )
                if len(secondary_environment_ids) != len(
                    set(secondary_environment_ids)
                ):
                    self.error(
                        f"{requirement_label}.secondary_environment_ids "
                        "contains duplicates"
                    )
                selected_environment_ids = {
                    str(primary_environment_id)
                } | set(secondary_environment_ids)
                if primary_environment_id in secondary_environment_ids:
                    self.error(
                        f"{requirement_label}: primary environment cannot "
                        "also be secondary"
                    )
                unknown_requirement_environments = (
                    selected_environment_ids - environment_ids
                )
                if unknown_requirement_environments:
                    self.error(
                        f"{requirement_label} references unknown environments: "
                        + ", ".join(
                            sorted(unknown_requirement_environments)
                        )
                    )
                event_environment_requirement_envs[
                    requirement_id
                ] = selected_environment_ids
                covered_requirement_environments.update(
                    selected_environment_ids & environment_ids
                )
                for field in (
                    "required_capabilities",
                    "required_zone_ids",
                    "required_resources",
                    "required_permissions",
                    "required_information_channels",
                    "hazards_and_constraints",
                    "transition_requirements",
                ):
                    values = requirement.get(field)
                    must_be_nonempty = field in {
                        "required_capabilities",
                        "required_zone_ids",
                        "hazards_and_constraints",
                    }
                    if not string_list(values, nonempty=must_be_nonempty):
                        self.error(
                            f"{requirement_label}.{field} must be "
                            + (
                                "a non-empty string array"
                                if must_be_nonempty
                                else "a string array"
                            )
                        )
                        continue
                    if len(values) != len(set(values)):
                        self.error(
                            f"{requirement_label}.{field} contains duplicates"
                        )
                available_zone_ids = {
                    zone_id
                    for environment_id in selected_environment_ids
                    for zone_id in environment_zone_occupants.get(
                        environment_id, {}
                    )
                }
                unknown_required_zones = set(
                    string_values(requirement.get("required_zone_ids"))
                ) - available_zone_ids
                if unknown_required_zones:
                    self.error(
                        f"{requirement_label}.required_zone_ids are not "
                        "provided by its selected environments: "
                        + ", ".join(sorted(unknown_required_zones))
                    )
            if covered_requirement_environments != environment_ids:
                self.error(
                    "event environment requirements must collectively use "
                    "every major environment"
                )
            if environment_unit_coverage != set(units):
                self.error(
                    "world environments must collectively cover every "
                    "development unit"
                )
            covered_system_environments: set[str] = set()
            for system_id, referenced_ids in world_system_environment_refs.items():
                unknown = referenced_ids - environment_ids
                if unknown:
                    self.error(
                        f"world system {system_id} references unknown environments: "
                        + ", ".join(sorted(unknown))
                    )
                covered_system_environments.update(
                    referenced_ids & environment_ids
                )
            if covered_system_environments != environment_ids:
                self.error(
                    "world systems must collectively cover every major environment"
                )

        storyline_ids: set[str] = set()
        storyline_unit_coverage: set[str] = set()
        major_event_character_refs: list[
            tuple[str, str, set[str], set[str]]
        ] = []
        major_event_actor_refs: list[
            tuple[str, str, str, str]
        ] = []
        story = conception.get("story")
        if not isinstance(story, dict):
            self.error("conception.story is missing")
        else:
            reject_extra(
                story,
                {
                    "id",
                    "source_controls",
                    "phases",
                    "major_events",
                    "storylines",
                    "storyline_demands",
                    "storyline_architecture",
                    "melody_lines",
                    "event_span",
                    "event_source_coverage",
                    *STORY_CONCEPTION_FIELDS,
                },
                "conception.story",
            )
            story_id = story.get("id")
            if (
                not nonempty_string(story_id)
                or not ID_PATTERN.fullmatch(str(story_id))
            ):
                self.error("conception.story.id is invalid")
            story_sources = validate_sources(
                story,
                "conception.story",
                required_areas={"intent", "causality"},
            )
            validate_text_fields(
                story,
                (
                    "core_promise",
                    "whose_story",
                    "central_conflict",
                    "dramatic_question",
                    "start_state",
                    "inciting_incident",
                    "climax",
                    "resolution",
                ),
                "conception.story",
            )
            validate_list_fields(
                story,
                (
                    "stakes",
                    "escalation_logic",
                    "open_threads",
                    "scope_exclusions",
                ),
                "conception.story",
                nonempty={"stakes", "escalation_logic", "scope_exclusions"},
            )
            phases = story.get("phases")
            if not isinstance(phases, list) or not phases:
                self.error("conception.story.phases must be non-empty")
                phases = []
            phase_ids: set[str] = set()
            observed_units: list[str] = []
            order = {unit_id: index for index, unit_id in enumerate(units)}
            for index, phase in enumerate(phases):
                label = f"conception.story.phases[{index}]"
                if not isinstance(phase, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    phase,
                    {"id", "source_controls", *STORY_PHASE_FIELDS},
                    label,
                )
                phase_id = phase.get("id")
                if (
                    not nonempty_string(phase_id)
                    or not ID_PATTERN.fullmatch(str(phase_id))
                    or phase_id in phase_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                phase_ids.add(str(phase_id))
                phase_sources = validate_sources(
                    phase,
                    label,
                    required_areas={"causality"},
                )
                if not set(phase_sources).issubset(set(story_sources)):
                    self.error(f"{label}: phase sources must belong to story sources")
                validate_text_fields(
                    phase,
                    (
                        "title",
                        "function",
                        "entry_state",
                        "driving_goal",
                        "pressure",
                        "decisive_change",
                        "exit_state",
                    ),
                    label,
                )
                unit_ids = phase.get("unit_ids")
                if not string_list(unit_ids, nonempty=True):
                    self.error(f"{label}.unit_ids must be non-empty")
                    continue
                for unit_id in unit_ids:
                    if unit_id not in units:
                        self.error(f"{label}: unknown unit {unit_id}")
                    observed_units.append(unit_id)
                indices = [order[item] for item in unit_ids if item in order]
                if indices != sorted(indices):
                    self.error(f"{label}.unit_ids are not in development order")
                if indices and indices != list(range(min(indices), max(indices) + 1)):
                    self.error(f"{label}.unit_ids must form one contiguous range")
            if observed_units != list(units):
                self.error(
                    "story phases must exactly cover all units in development order"
                )
            major_events = story.get("major_events")
            if not isinstance(major_events, list) or not major_events:
                self.error("conception.story.major_events must be non-empty")
                major_events = []
            major_event_ids: set[str] = set()
            major_event_order: dict[str, int] = {}
            major_event_records: dict[str, dict[str, Any]] = {}
            major_event_line_refs: dict[str, set[str]] = {}
            for index, event in enumerate(major_events):
                label = f"conception.story.major_events[{index}]"
                if not isinstance(event, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    event,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *MAJOR_EVENT_FIELDS,
                    },
                    label,
                )
                event_id = event.get("id")
                if (
                    not nonempty_string(event_id)
                    or not ID_PATTERN.fullmatch(str(event_id))
                    or event_id in major_event_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                event_id = str(event_id)
                major_event_ids.add(event_id)
                major_event_order[event_id] = index
                major_event_records[event_id] = event
                if event.get("event_role") not in MAJOR_EVENT_ROLES:
                    self.error(f"{label}.event_role is invalid")
                validate_sources(event, label, required_areas={"causality"})
                validate_decision_links(event, label, nonempty=True)
                validate_text_fields(
                    event,
                    (
                        "title",
                        "definition",
                        "initiating_action",
                        "opposition_or_complication",
                        "decisive_change",
                        "immediate_outcome",
                        "state_before",
                        "state_after",
                        "next_pressure",
                        "downstream_freedom",
                    ),
                    label,
                )
                if normalized_business_text(
                    event.get("state_before")
                ) == normalized_business_text(event.get("state_after")):
                    self.error(
                        f"{label}: state_before and state_after must differ"
                    )
                validate_list_fields(
                    event,
                    (
                        "preconditions",
                        "information_effects",
                    ),
                    label,
                    nonempty={"preconditions"},
                )
                for field in (
                    "storyline_ids",
                    "unit_ids",
                    "environment_ids",
                    "participant_ids",
                    "initiator_ids",
                    "opposition_actor_ids",
                    "information_effects",
                    "causal_predecessor_ids",
                ):
                    raw_values = event.get(field)
                    if not string_list(
                        raw_values,
                        nonempty=field
                        in {
                            "storyline_ids",
                            "unit_ids",
                            "environment_ids",
                            "participant_ids",
                            "initiator_ids",
                        },
                    ):
                        self.error(
                            f"{label}.{field} must be a "
                            + (
                                "non-empty string array"
                                if field
                                in {
                                    "storyline_ids",
                                    "unit_ids",
                                    "environment_ids",
                                    "participant_ids",
                                    "initiator_ids",
                                }
                                else "string array"
                            )
                        )
                    values = string_values(raw_values)
                    if len(values) != len(set(values)):
                        self.error(f"{label}.{field} contains duplicates")
                event_units = set(string_values(event.get("unit_ids")))
                participants = set(
                    string_values(event.get("participant_ids"))
                )
                initiators = set(
                    string_values(event.get("initiator_ids"))
                )
                opposition_actors = set(
                    string_values(event.get("opposition_actor_ids"))
                )
                if not initiators.issubset(participants):
                    self.error(
                        f"{label}.initiator_ids must be a subset of participant_ids"
                    )
                if not opposition_actors.issubset(participants):
                    self.error(
                        f"{label}.opposition_actor_ids must be a subset of "
                        "participant_ids"
                    )
                unknown_units = event_units - set(units)
                if unknown_units:
                    self.error(
                        f"{label}.unit_ids contains unknown units: "
                        + ", ".join(sorted(unknown_units))
                    )
                event_environments = set(
                    string_values(event.get("environment_ids"))
                )
                unknown_environments = event_environments - environment_ids
                if unknown_environments:
                    self.error(
                        f"{label}.environment_ids contains unknown "
                        "environments: "
                        + ", ".join(sorted(unknown_environments))
                    )
                for unit_id in event_units & set(units):
                    if not (
                        unit_host_environments.get(unit_id, set())
                        & event_environments
                    ):
                        self.error(
                            f"{label}: unit {unit_id} is not hosted by any "
                            "listed environment"
                        )
                for environment_id in event_environments & environment_ids:
                    if not any(
                        environment_id
                        in unit_host_environments.get(unit_id, set())
                        for unit_id in event_units
                    ):
                        self.error(
                            f"{label}: environment {environment_id} hosts "
                            "none of the event units"
                        )
                predecessors = string_values(
                    event.get("causal_predecessor_ids")
                )
                for predecessor_id in predecessors:
                    if predecessor_id not in major_event_order:
                        self.error(
                            f"{label}: causal predecessor {predecessor_id} "
                            "must be an earlier major event"
                        )
                event_lines = set(
                    string_values(event.get("storyline_ids"))
                )
                major_event_line_refs[event_id] = event_lines
                major_event_character_refs.extend(
                    (
                        label,
                        character_id,
                        event_units,
                        event_environments,
                    )
                    for character_id in string_values(
                        event.get("participant_ids")
                    )
                )
                major_event_actor_refs.extend(
                    (
                        label,
                        character_id,
                        "initiator",
                        str(event.get("initiating_action", "")),
                    )
                    for character_id in initiators
                )
                major_event_actor_refs.extend(
                    (
                        label,
                        character_id,
                        "opposition",
                        str(event.get("opposition_or_complication", "")),
                    )
                    for character_id in opposition_actors
                )
            covered_system_events: set[str] = set()
            for system_id, referenced_ids in world_system_event_refs.items():
                unknown = referenced_ids - major_event_ids
                if unknown:
                    self.error(
                        f"world system {system_id} references unknown major events: "
                        + ", ".join(sorted(unknown))
                    )
                covered_system_events.update(referenced_ids & major_event_ids)
            if covered_system_events != major_event_ids:
                self.error(
                    "world systems must collectively cover every major event"
                )
            required_environment_event_ids = set(
                event_environment_requirement_events.values()
            )
            if required_environment_event_ids != major_event_ids:
                missing_requirements = (
                    major_event_ids - required_environment_event_ids
                )
                extra_requirements = (
                    required_environment_event_ids - major_event_ids
                )
                detail: list[str] = []
                if missing_requirements:
                    detail.append(
                        "missing " + ", ".join(sorted(missing_requirements))
                    )
                if extra_requirements:
                    detail.append(
                        "unknown " + ", ".join(sorted(extra_requirements))
                    )
                self.error(
                    "event environment requirements must exactly cover every "
                    "major event"
                    + (": " + "; ".join(detail) if detail else "")
                )
            for requirement_id, event_id in (
                event_environment_requirement_events.items()
            ):
                event = major_event_records.get(event_id)
                if event is None:
                    continue
                selected_environments = (
                    event_environment_requirement_envs.get(
                        requirement_id, set()
                    )
                )
                event_environments = set(
                    string_values(event.get("environment_ids"))
                )
                if selected_environments != event_environments:
                    self.error(
                        f"{requirement_id}: selected environments must "
                        f"exactly match major event {event_id}.environment_ids"
                    )
            event_span = story.get("event_span")
            if not isinstance(event_span, dict):
                self.error("conception.story.event_span is missing")
                event_span = {}
            else:
                reject_extra(
                    event_span,
                    set(EVENT_SPAN_FIELDS),
                    "conception.story.event_span",
                )
                validate_text_fields(
                    event_span,
                    (
                        "earliest_causal_change",
                        "latest_consequence",
                        "coverage_rationale",
                    ),
                    "conception.story.event_span",
                )
                for field in ("opening_event_ids", "aftermath_event_ids"):
                    values = string_values(event_span.get(field))
                    if not string_list(event_span.get(field), nonempty=True):
                        self.error(
                            f"conception.story.event_span.{field} must be a "
                            "non-empty string array"
                        )
                    if len(values) != len(set(values)):
                        self.error(
                            f"conception.story.event_span.{field} contains duplicates"
                        )
                    unknown = set(values) - major_event_ids
                    if unknown:
                        self.error(
                            f"conception.story.event_span.{field} contains "
                            "unknown events: "
                            + ", ".join(sorted(unknown))
                        )
                entry_event = event_span.get("main_action_entry_event_id")
                if (
                    not nonempty_string(entry_event)
                    or entry_event not in major_event_ids
                ):
                    self.error(
                        "conception.story.event_span.main_action_entry_event_id "
                        "must reference a major event"
                    )
                opening_ids = string_values(
                    event_span.get("opening_event_ids")
                )
                aftermath_ids = string_values(
                    event_span.get("aftermath_event_ids")
                )
                if major_events and opening_ids and opening_ids[0] != major_events[0].get(
                    "id"
                ):
                    self.error(
                        "conception.story.event_span.opening_event_ids must "
                        "begin with the first major event"
                    )
                if major_events and aftermath_ids and aftermath_ids[-1] != major_events[
                    -1
                ].get("id"):
                    self.error(
                        "conception.story.event_span.aftermath_event_ids must "
                        "end with the final major event"
                    )
                span_order = [
                    major_event_order[event_id]
                    for event_id in opening_ids + aftermath_ids
                    if event_id in major_event_order
                ]
                if span_order != sorted(span_order):
                    self.error(
                        "conception.story.event_span event IDs are not in "
                        "causal order"
                    )

            event_source_coverage = story.get("event_source_coverage")
            if (
                not isinstance(event_source_coverage, list)
                or not event_source_coverage
            ):
                self.error(
                    "conception.story.event_source_coverage must be non-empty"
                )
                event_source_coverage = []
            coverage_ids: set[str] = set()
            covered_event_ids: set[str] = set()
            covered_areas: set[str] = set()
            for index, coverage_item in enumerate(event_source_coverage):
                label = f"conception.story.event_source_coverage[{index}]"
                if not isinstance(coverage_item, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    coverage_item,
                    {
                        "id",
                        "source_artifact_id",
                        "source_section",
                        "source_excerpt",
                        "candidate_type",
                        "disposition",
                        "major_event_ids",
                        "rationale",
                    },
                    label,
                )
                coverage_id = coverage_item.get("id")
                if (
                    not nonempty_string(coverage_id)
                    or not ID_PATTERN.fullmatch(str(coverage_id))
                    or coverage_id in coverage_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                else:
                    coverage_ids.add(str(coverage_id))
                validate_text_fields(
                    coverage_item,
                    ("source_section", "source_excerpt", "rationale"),
                    label,
                )
                artifact_id = coverage_item.get("source_artifact_id")
                source_record = self.source_texts.get(str(artifact_id))
                if source_record is None:
                    self.error(f"{label}.source_artifact_id is unknown")
                else:
                    artifact_record, source_text = source_record
                    covered_areas.add(str(artifact_record.get("area", "")))
                    excerpt = coverage_item.get("source_excerpt")
                    if (
                        isinstance(excerpt, str)
                        and excerpt.strip()
                        and excerpt.strip() not in source_text
                    ):
                        self.error(
                            f"{label}.source_excerpt is not present in its "
                            "source artifact"
                        )
                candidate_type = coverage_item.get("candidate_type")
                disposition = coverage_item.get("disposition")
                if candidate_type not in EVENT_SOURCE_CANDIDATE_TYPES:
                    self.error(f"{label}.candidate_type is invalid")
                if disposition not in EVENT_SOURCE_DISPOSITIONS:
                    self.error(f"{label}.disposition is invalid")
                linked_events = string_values(
                    coverage_item.get("major_event_ids")
                )
                if not string_list(
                    coverage_item.get("major_event_ids"),
                    nonempty=disposition in {"enacted", "distributed"},
                ):
                    self.error(
                        f"{label}.major_event_ids must match its disposition"
                    )
                if len(linked_events) != len(set(linked_events)):
                    self.error(f"{label}.major_event_ids contains duplicates")
                unknown_events = set(linked_events) - major_event_ids
                if unknown_events:
                    self.error(
                        f"{label}.major_event_ids contains unknown events: "
                        + ", ".join(sorted(unknown_events))
                    )
                if disposition in {"context_only", "excluded"} and linked_events:
                    self.error(
                        f"{label}: context-only or excluded coverage cannot "
                        "reference major events"
                    )
                if (
                    candidate_type != "static_context"
                    and disposition in {"context_only", "excluded"}
                ):
                    self.error(
                        f"{label}: an event-bearing source candidate cannot be "
                        "dismissed as context"
                    )
                excerpt_tokens = grounding_tokens(
                    coverage_item.get("source_excerpt")
                )
                for event_id in linked_events:
                    event = major_event_records.get(event_id)
                    if event is None:
                        continue
                    enacted_text = {
                        "title": event.get("title"),
                        "initiating_action": event.get("initiating_action"),
                        "decisive_change": event.get("decisive_change"),
                        "immediate_outcome": event.get("immediate_outcome"),
                    }
                    event_tokens = grounding_tokens(enacted_text)
                    overlap = excerpt_tokens & event_tokens
                    overlap_ratio = (
                        len(overlap) / len(excerpt_tokens)
                        if excerpt_tokens
                        else 1.0
                    )
                    if excerpt_tokens and (
                        not overlap or overlap_ratio < 0.25
                    ):
                        self.error(
                            f"{label}: source excerpt is not enacted by major "
                            f"event {event_id}; a precondition mention is not "
                            "event coverage"
                        )
                    covered_event_ids.add(event_id)
            required_event_source_areas = {
                record.get("area")
                for record, _text in self.source_texts.values()
                if record.get("area") in {"causality", "narrative"}
            }
            if not required_event_source_areas.issubset(covered_areas):
                missing_areas = required_event_source_areas - covered_areas
                self.error(
                    "event_source_coverage must scan causality and narrative "
                    "artifacts; missing: "
                    + ", ".join(sorted(str(item) for item in missing_areas))
                )
            if covered_event_ids != major_event_ids:
                missing_events = major_event_ids - covered_event_ids
                self.error(
                    "event_source_coverage must justify every major event"
                    + (
                        ": " + ", ".join(sorted(missing_events))
                        if missing_events
                        else ""
                    )
                )
            storylines = story.get("storylines")
            if not isinstance(storylines, list) or not storylines:
                self.error("conception.story.storylines must be non-empty")
                storylines = []
            observed_types: list[str] = []
            storyline_event_refs: dict[str, set[str]] = {}
            storyline_records: dict[str, dict[str, Any]] = {}
            storyline_protagonist_refs: dict[str, list[str]] = {}
            for index, storyline in enumerate(storylines):
                label = f"conception.story.storylines[{index}]"
                if not isinstance(storyline, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    storyline,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *STORYLINE_FIELDS,
                    },
                    label,
                )
                storyline_id = storyline.get("id")
                if (
                    not nonempty_string(storyline_id)
                    or not ID_PATTERN.fullmatch(str(storyline_id))
                    or storyline_id in storyline_ids
                ):
                    self.error(f"{label}.id is invalid or duplicated")
                    continue
                storyline_ids.add(str(storyline_id))
                storyline_records[str(storyline_id)] = storyline
                storyline_type = storyline.get("type")
                if storyline_type not in STORYLINE_TYPES:
                    self.error(f"{label}.type is invalid")
                else:
                    observed_types.append(str(storyline_type))
                validate_sources(
                    storyline,
                    label,
                    required_areas={"causality"},
                )
                validate_text_fields(
                    storyline,
                    (
                        "title",
                        "function",
                        "central_question",
                        "start_state",
                        "driver",
                        "end_state",
                        "resolution",
                        "downstream_freedom",
                    ),
                    label,
                )
                validate_list_fields(
                    storyline,
                    (
                        "escalation",
                        "major_event_ids",
                    ),
                    label,
                    nonempty={
                        "escalation",
                        "major_event_ids",
                    },
                )
                protagonists = storyline.get("protagonists")
                if not string_list(protagonists, nonempty=True):
                    self.error(
                        f"{label}.protagonists must be a non-empty "
                        "canonical character ID array"
                    )
                    protagonists = []
                elif len(protagonists) != len(set(protagonists)):
                    self.error(f"{label}.protagonists contains duplicates")
                storyline_protagonist_refs[str(storyline_id)] = list(
                    protagonists
                )
                line_event_ids = string_values(
                    storyline.get("major_event_ids")
                )
                if len(line_event_ids) != len(set(line_event_ids)):
                    self.error(f"{label}.major_event_ids contains duplicates")
                minimum_events = 3 if storyline_type == "main" else 2
                if len(line_event_ids) < minimum_events:
                    self.error(
                        f"{label}.major_event_ids must contain at least "
                        f"{minimum_events}"
                    )
                unknown_events = set(line_event_ids) - major_event_ids
                if unknown_events:
                    self.error(
                        f"{label}.major_event_ids contains unknown events: "
                        + ", ".join(sorted(unknown_events))
                    )
                event_indices = [
                    major_event_order[event_id]
                    for event_id in line_event_ids
                    if event_id in major_event_order
                ]
                if event_indices != sorted(event_indices):
                    self.error(
                        f"{label}.major_event_ids are not in causal order"
                    )
                storyline_event_refs[str(storyline_id)] = set(line_event_ids)
                storyline_units = storyline.get("unit_ids")
                if not string_list(storyline_units, nonempty=True):
                    self.error(f"{label}.unit_ids must be non-empty")
                    storyline_units = []
                if len(storyline_units) != len(set(storyline_units)):
                    self.error(f"{label}.unit_ids contains duplicates")
                for unit_id in storyline_units:
                    if unit_id not in units:
                        self.error(f"{label}: unknown unit {unit_id}")
                    else:
                        storyline_unit_coverage.add(unit_id)
                valid_line_events = [
                    major_event_records[event_id]
                    for event_id in line_event_ids
                    if event_id in major_event_records
                ]
                line_units = set(storyline_units)
                for event_id in line_event_ids:
                    event = major_event_records.get(event_id)
                    if event is None:
                        continue
                    if not (
                        set(string_values(event.get("unit_ids")))
                        & line_units
                    ):
                        self.error(
                            f"{label}: major event {event_id} does not "
                            "carry a unit from this storyline"
                        )
                covered_line_units = {
                    unit_id
                    for event in valid_line_events
                    for unit_id in string_values(event.get("unit_ids"))
                    if unit_id in line_units
                }
                if storyline_units and (
                    storyline_units[0] not in covered_line_units
                    or storyline_units[-1] not in covered_line_units
                ):
                    self.error(
                        f"{label}: major events must anchor the first and "
                        "last storyline units"
                    )
                for event_position, event_id in enumerate(line_event_ids):
                    if (
                        event_position == 0
                        or event_id not in major_event_records
                    ):
                        continue
                    earlier_line_events = set(
                        line_event_ids[:event_position]
                    )
                    predecessors = set(
                        string_values(
                            major_event_records[event_id].get(
                                "causal_predecessor_ids"
                            )
                        )
                    )
                    if not predecessors & earlier_line_events:
                        self.error(
                            f"{label}: major event {event_id} must cite an "
                            "earlier event from the same storyline"
                        )
                validate_decision_links(storyline, label, nonempty=True)

            storyline_demands = story.get("storyline_demands")
            if not isinstance(storyline_demands, list) or not storyline_demands:
                self.error(
                    "conception.story.storyline_demands must be a non-empty array"
                )
                storyline_demands = []
            storyline_demand_ids: set[str] = set()
            demanded_storylines: set[str] = set()
            demand_source_coverage: set[str] = set()
            for demand_index, demand in enumerate(storyline_demands):
                demand_label = (
                    f"conception.story.storyline_demands[{demand_index}]"
                )
                if not isinstance(demand, dict):
                    self.error(f"{demand_label} is not an object")
                    continue
                reject_extra(
                    demand,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *STORYLINE_DEMAND_FIELDS,
                    },
                    demand_label,
                )
                demand_id = demand.get("id")
                if (
                    not nonempty_string(demand_id)
                    or not ID_PATTERN.fullmatch(str(demand_id))
                    or demand_id in storyline_demand_ids
                ):
                    self.error(
                        f"{demand_label}.id is invalid or duplicated"
                    )
                    continue
                storyline_demand_ids.add(str(demand_id))
                demand_sources = validate_sources(
                    demand,
                    demand_label,
                    required_areas={"causality"},
                )
                demand_source_coverage.update(demand_sources)
                validate_decision_links(demand, demand_label, nonempty=True)
                validate_text_fields(
                    demand,
                    (
                        "need",
                        "story_function",
                        "omission_consequence",
                        "rationale",
                    ),
                    demand_label,
                )
                disposition = demand.get("disposition")
                if disposition not in STORYLINE_DEMAND_DISPOSITIONS:
                    self.error(f"{demand_label}.disposition is invalid")
                demand_lines = string_values(demand.get("storyline_ids"))
                if not string_list(
                    demand.get("storyline_ids"),
                    nonempty=disposition
                    in {"dedicated_line", "integrated_into_lines"},
                ):
                    self.error(
                        f"{demand_label}.storyline_ids must match its disposition"
                    )
                if len(demand_lines) != len(set(demand_lines)):
                    self.error(
                        f"{demand_label}.storyline_ids contains duplicates"
                    )
                unknown_demand_lines = set(demand_lines) - storyline_ids
                if unknown_demand_lines:
                    self.error(
                        f"{demand_label}.storyline_ids contains unknown lines: "
                        + ", ".join(sorted(unknown_demand_lines))
                    )
                if disposition == "dedicated_line" and len(demand_lines) != 1:
                    self.error(
                        f"{demand_label}: dedicated_line must resolve to "
                        "exactly one storyline"
                    )
                if disposition == "not_applicable" and demand_lines:
                    self.error(
                        f"{demand_label}: not_applicable cannot reference "
                        "storylines"
                    )
                demanded_storylines.update(demand_lines)
            if demanded_storylines != storyline_ids:
                missing_demand_lines = storyline_ids - demanded_storylines
                self.error(
                    "storyline demands must justify every designed storyline"
                    + (
                        ": " + ", ".join(sorted(missing_demand_lines))
                        if missing_demand_lines
                        else ""
                    )
                )
            causality_story_sources = {
                source_id
                for source_id in story_sources
                if source_id in controls
                and controls[source_id].get("area") == "causality"
            }
            if not causality_story_sources.issubset(demand_source_coverage):
                self.error(
                    "storyline demands must scan every causality control "
                    "used by the story conception"
                )

            architecture = story.get("storyline_architecture")
            connection_line_ids: set[str] = set()
            if not isinstance(architecture, dict):
                self.error("conception.story.storyline_architecture is missing")
                architecture = {}
            else:
                reject_extra(
                    architecture,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        "connection_points",
                        *STORYLINE_ARCHITECTURE_FIELDS,
                    },
                    "conception.story.storyline_architecture",
                )
                architecture_id = architecture.get("id")
                if (
                    not nonempty_string(architecture_id)
                    or not ID_PATTERN.fullmatch(str(architecture_id))
                ):
                    self.error(
                        "conception.story.storyline_architecture.id is invalid"
                    )
                validate_sources(
                    architecture,
                    "conception.story.storyline_architecture",
                    required_areas={"causality"},
                )
                validate_decision_links(
                    architecture,
                    "conception.story.storyline_architecture",
                    nonempty=True,
                )
                validate_text_fields(
                    architecture,
                    ("coverage_rationale",),
                    "conception.story.storyline_architecture",
                )
                for field in (
                    "entry_storyline_ids",
                    "terminal_storyline_ids",
                ):
                    values = architecture.get(field)
                    if not string_list(values, nonempty=True):
                        self.error(
                            "conception.story.storyline_architecture."
                            f"{field} must be a non-empty string array"
                        )
                        continue
                    if len(values) != len(set(values)):
                        self.error(
                            "conception.story.storyline_architecture."
                            f"{field} contains duplicates"
                        )
                    unknown = set(values) - storyline_ids
                    if unknown:
                        self.error(
                            "conception.story.storyline_architecture."
                            f"{field} contains unknown lines: "
                            + ", ".join(sorted(unknown))
                        )
                declared_main_line = architecture.get("main_storyline_id")
                if declared_main_line not in storyline_ids:
                    self.error(
                        "conception.story.storyline_architecture."
                        "main_storyline_id is invalid"
                    )
                connection_points = architecture.get("connection_points")
                if not isinstance(connection_points, list):
                    self.error(
                        "conception.story.storyline_architecture."
                        "connection_points must be an array"
                    )
                    connection_points = []
                if len(storyline_ids) > 1 and not connection_points:
                    self.error(
                        "multi-line story architecture requires explicit "
                        "connection points"
                    )
                connection_ids: set[str] = set()
                outgoing_graph: dict[str, set[str]] = {
                    line_id: set() for line_id in storyline_ids
                }
                for connection_index, connection in enumerate(
                    connection_points
                ):
                    connection_label = (
                        "conception.story.storyline_architecture."
                        f"connection_points[{connection_index}]"
                    )
                    if not isinstance(connection, dict):
                        self.error(f"{connection_label} is not an object")
                        continue
                    reject_extra(
                        connection,
                        {
                            "id",
                            "source_controls",
                            "development_decisions",
                            *STORYLINE_CONNECTION_FIELDS,
                        },
                        connection_label,
                    )
                    connection_id = connection.get("id")
                    if (
                        not nonempty_string(connection_id)
                        or not ID_PATTERN.fullmatch(str(connection_id))
                        or connection_id in connection_ids
                    ):
                        self.error(
                            f"{connection_label}.id is invalid or duplicated"
                        )
                        continue
                    connection_ids.add(str(connection_id))
                    if (
                        connection.get("connection_type")
                        not in STORYLINE_CONNECTION_TYPES
                    ):
                        self.error(
                            f"{connection_label}.connection_type is invalid"
                        )
                    validate_sources(
                        connection,
                        connection_label,
                        required_areas={"causality"},
                    )
                    validate_decision_links(
                        connection,
                        connection_label,
                        nonempty=True,
                    )
                    validate_text_fields(
                        connection,
                        (
                            "preconditions",
                            "transferred_obligations",
                            "resulting_state",
                        ),
                        connection_label,
                    )
                    event_id = connection.get("event_id")
                    if event_id not in major_event_ids:
                        self.error(
                            f"{connection_label}.event_id must reference "
                            "a major event"
                        )
                    incoming = string_values(
                        connection.get("incoming_storyline_ids")
                    )
                    outgoing = string_values(
                        connection.get("outgoing_storyline_ids")
                    )
                    for field, values in (
                        ("incoming_storyline_ids", incoming),
                        ("outgoing_storyline_ids", outgoing),
                    ):
                        if not string_list(
                            connection.get(field), nonempty=True
                        ):
                            self.error(
                                f"{connection_label}.{field} must be a "
                                "non-empty string array"
                            )
                        if len(values) != len(set(values)):
                            self.error(
                                f"{connection_label}.{field} contains duplicates"
                            )
                        unknown = set(values) - storyline_ids
                        if unknown:
                            self.error(
                                f"{connection_label}.{field} contains "
                                "unknown lines: "
                                + ", ".join(sorted(unknown))
                            )
                    if set(incoming) & set(outgoing):
                        self.error(
                            f"{connection_label}: incoming and outgoing "
                            "storylines must be disjoint"
                        )
                    if (
                        connection.get("connection_type") == "merge"
                        and len(incoming) < 2
                    ):
                        self.error(
                            f"{connection_label}: merge requires at least "
                            "two incoming storylines"
                        )
                    if (
                        connection.get("connection_type") == "split"
                        and len(outgoing) < 2
                    ):
                        self.error(
                            f"{connection_label}: split requires at least "
                            "two outgoing storylines"
                        )
                    connection_line_ids.update(incoming)
                    connection_line_ids.update(outgoing)
                    for incoming_id in incoming:
                        outgoing_graph.setdefault(incoming_id, set()).update(
                            outgoing
                        )
                    event_lines = major_event_line_refs.get(
                        str(event_id), set()
                    )
                    if event_id in major_event_ids and not (
                        set(incoming) | set(outgoing)
                    ).issubset(event_lines):
                        self.error(
                            f"{connection_label}: connection event must "
                            "belong to every incoming and outgoing storyline"
                        )
                if len(storyline_ids) > 1:
                    disconnected_lines = (
                        storyline_ids - {str(declared_main_line)}
                    ) - connection_line_ids
                    if disconnected_lines:
                        self.error(
                            "every non-main storyline must participate in "
                            "at least one explicit connection point: "
                            + ", ".join(sorted(disconnected_lines))
                        )
                    for line_id in storyline_ids - {str(declared_main_line)}:
                        reached = {line_id}
                        queue = [line_id]
                        for current in queue:
                            for next_line in outgoing_graph.get(
                                current, set()
                            ):
                                if next_line not in reached:
                                    reached.add(next_line)
                                    queue.append(next_line)
                        if declared_main_line not in reached:
                            self.error(
                                f"storyline {line_id} has no explicit "
                                "connection path into the main storyline"
                            )

            melody_lines = story.get("melody_lines")
            if not isinstance(melody_lines, list):
                self.error("conception.story.melody_lines must be an array")
                melody_lines = []
            melody_line_ids: set[str] = set()
            for melody_index, melody in enumerate(melody_lines):
                melody_label = (
                    f"conception.story.melody_lines[{melody_index}]"
                )
                if not isinstance(melody, dict):
                    self.error(f"{melody_label} is not an object")
                    continue
                reject_extra(
                    melody,
                    {
                        "id",
                        "source_controls",
                        "development_decisions",
                        *MELODY_LINE_FIELDS,
                    },
                    melody_label,
                )
                melody_id = melody.get("id")
                if (
                    not nonempty_string(melody_id)
                    or not ID_PATTERN.fullmatch(str(melody_id))
                    or melody_id in melody_line_ids
                    or melody_id in storyline_ids
                ):
                    self.error(
                        f"{melody_label}.id is invalid, duplicated, or "
                        "collides with a structural storyline"
                    )
                    continue
                melody_line_ids.add(str(melody_id))
                validate_sources(
                    melody, melody_label, required_areas=set()
                )
                validate_decision_links(
                    melody, melody_label, nonempty=True
                )
                validate_text_fields(
                    melody,
                    (
                        "title",
                        "function",
                        "omission_effect",
                        "series_potential",
                        "downstream_freedom",
                    ),
                    melody_label,
                )
                for field in (
                    "anchor_event_ids",
                    "variation_pattern",
                    "expansion_options",
                    "boundaries",
                ):
                    values = melody.get(field)
                    if not string_list(values, nonempty=True):
                        self.error(
                            f"{melody_label}.{field} must be a non-empty "
                            "string array"
                        )
                        continue
                    if len(values) != len(set(values)):
                        self.error(
                            f"{melody_label}.{field} contains duplicates"
                        )
                anchor_ids = string_values(
                    melody.get("anchor_event_ids")
                )
                if not 3 <= len(anchor_ids) <= 7:
                    self.error(
                        f"{melody_label}.anchor_event_ids must contain "
                        "three to seven recurrence anchors"
                    )
                unknown_anchors = set(anchor_ids) - major_event_ids
                if unknown_anchors:
                    self.error(
                        f"{melody_label}.anchor_event_ids contains unknown "
                        "events: " + ", ".join(sorted(unknown_anchors))
                    )
                anchor_order = [
                    major_event_order[event_id]
                    for event_id in anchor_ids
                    if event_id in major_event_order
                ]
                if anchor_order != sorted(anchor_order):
                    self.error(
                        f"{melody_label}.anchor_event_ids are not in "
                        "causal order"
                    )
                for field in (
                    "required_for_causality",
                    "required_for_resolution",
                    "new_pov_allowed",
                    "carries_decisive_information",
                ):
                    if melody.get(field) is not False:
                        self.error(
                            f"{melody_label}.{field} must be false; melody "
                            "lines are optional modulation, not structural plot"
                        )
            if observed_types.count("main") != 1:
                self.error("storylines must contain exactly one main line")
            if isinstance(architecture, dict):
                declared_main = architecture.get("main_storyline_id")
                actual_main = {
                    storyline_id
                    for storyline_id, record in storyline_records.items()
                    if record.get("type") == "main"
                }
                if len(actual_main) == 1 and declared_main not in actual_main:
                    self.error(
                        "storyline_architecture.main_storyline_id must match "
                        "the sole main storyline"
                    )
            if storyline_unit_coverage != set(units):
                self.error("storylines must collectively cover every development unit")
            referenced_major_events = set().union(
                *storyline_event_refs.values()
            ) if storyline_event_refs else set()
            if referenced_major_events != major_event_ids:
                self.error(
                    "storylines must collectively reference every major event"
                )
            for event_id, declared_lines in major_event_line_refs.items():
                actual_lines = {
                    storyline_id
                    for storyline_id, event_ids in storyline_event_refs.items()
                    if event_id in event_ids
                }
                if declared_lines != actual_lines:
                    self.error(
                        f"major event {event_id}.storyline_ids must match "
                        "storyline major_event_ids"
                    )
                unknown_lines = declared_lines - storyline_ids
                if unknown_lines:
                    self.error(
                        f"major event {event_id} references unknown "
                        "storylines: "
                        + ", ".join(sorted(unknown_lines))
                    )
            for label, storyline_id in environment_storyline_refs:
                if storyline_id not in storyline_ids:
                    self.error(
                        f"{label}: unknown storyline {storyline_id}"
                    )

        characters = conception.get("characters")
        if not isinstance(characters, dict):
            self.error("conception.characters must be a character-model object")
            characters = {}
        else:
            reject_extra(
                characters,
                {"demand_register", "profiles", "relationships"},
                "conception.characters",
            )
        demand_register = characters.get("demand_register")
        if not isinstance(demand_register, list) or not demand_register:
            self.error(
                "conception.characters.demand_register must be a non-empty array"
            )
            demand_register = []
        profiles = characters.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            self.error("conception.characters.profiles must be a non-empty array")
            profiles = []
        relationships = characters.get("relationships")
        if not isinstance(relationships, list) or not relationships:
            self.error(
                "conception.characters.relationships must be a non-empty array"
            )
            relationships = []
        character_ids: set[str] = set()
        character_names: set[str] = set()
        core_character_ids: set[str] = set()
        profile_units: dict[str, set[str]] = {}
        profile_storylines: dict[str, set[str]] = {}
        profile_demand_ids: dict[str, set[str]] = {}
        profile_importance: dict[str, str] = {}
        profile_naming_status: dict[str, str] = {}
        profile_names: dict[str, str] = {}
        for index, character in enumerate(profiles):
            label = f"conception.characters.profiles[{index}]"
            if not isinstance(character, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                character,
                {
                    "id",
                    "source_controls",
                    "development_decisions",
                    *CHARACTER_CONCEPTION_FIELDS,
                },
                label,
            )
            character_id = character.get("id")
            name = character.get("name")
            if (
                not nonempty_string(character_id)
                or not ID_PATTERN.fullmatch(str(character_id))
                or character_id in character_ids
            ):
                self.error(f"{label}.id is invalid or duplicated")
                continue
            character_ids.add(str(character_id))
            if not nonempty_string(name) or name in character_names:
                self.error(f"{label}.name is missing or duplicated")
            else:
                character_names.add(str(name))
                profile_names[str(character_id)] = str(name)
            importance = character.get("importance")
            if importance not in CHARACTER_IMPORTANCE:
                self.error(f"{label}.importance is invalid")
            elif importance == "core":
                core_character_ids.add(str(character_id))
            if isinstance(importance, str):
                profile_importance[str(character_id)] = importance
            if isinstance(character.get("naming_status"), str):
                profile_naming_status[str(character_id)] = str(
                    character.get("naming_status")
                )
            if character.get("naming_status") not in RELATION_NAMING_STATUS:
                self.error(f"{label}.naming_status is invalid")
            elif (
                importance in {"core", "supporting"}
                and character.get("naming_status") == "functional"
            ):
                self.error(
                    f"{label}: core and supporting characters must be "
                    "explicitly named"
                )
            elif (
                character.get("naming_status") in {"confirmed", "autonomous"}
                and isinstance(name, str)
                and FUNCTIONAL_CHARACTER_NAME_PATTERN.fullmatch(name.strip())
            ):
                self.error(
                    f"{label}.name is only a functional role label, not a "
                    "completed character name"
                )
            validate_sources(
                character,
                label,
                required_areas=(
                    {"subject", "character"}
                    if importance == "core"
                    else {"character"}
                ),
            )
            validate_decision_links(
                character,
                label,
                nonempty=importance != "core",
            )
            validate_text_fields(
                character,
                (
                    "role",
                    "story_function",
                    "start_state",
                    "surface_goal",
                    "deeper_need",
                    "fear_or_avoidance",
                    "end_state",
                ),
                label,
            )
            validate_list_fields(
                character,
                (
                    "values_and_boundaries",
                    "information_limits",
                    "pressure_behavior",
                    "agency_choices",
                    "invariants",
                ),
                label,
                nonempty={
                    "values_and_boundaries",
                    "information_limits",
                    "pressure_behavior",
                    "agency_choices",
                    "invariants",
                },
            )
            unit_ids = character.get("unit_ids")
            if not string_list(unit_ids, nonempty=True):
                self.error(f"{label}.unit_ids must be non-empty")
                unit_ids = []
            elif len(unit_ids) != len(set(unit_ids)):
                self.error(f"{label}.unit_ids contains duplicates")
            for unit_id in unit_ids:
                if unit_id not in units:
                    self.error(f"{label}: unknown unit {unit_id}")
            profile_units[str(character_id)] = set(unit_ids)
            character_storylines = character.get("storyline_ids")
            if not string_list(character_storylines, nonempty=True):
                self.error(f"{label}.storyline_ids must be non-empty")
                character_storylines = []
            elif len(character_storylines) != len(set(character_storylines)):
                self.error(f"{label}.storyline_ids contains duplicates")
            for storyline_id in character_storylines:
                if storyline_id not in storyline_ids:
                    self.error(f"{label}: unknown storyline {storyline_id}")
            profile_storylines[str(character_id)] = set(character_storylines)
            demand_ids = character.get("demand_ids")
            if not string_list(demand_ids, nonempty=True):
                self.error(f"{label}.demand_ids must be non-empty")
                demand_ids = []
            elif len(demand_ids) != len(set(demand_ids)):
                self.error(f"{label}.demand_ids contains duplicates")
            profile_demand_ids[str(character_id)] = set(demand_ids)
            if not nonempty_string(character.get("downstream_freedom"), 12):
                self.error(f"{label}.downstream_freedom is too small")
            arc_stages = character.get("arc_stages")
            if not isinstance(arc_stages, list):
                self.error(f"{label}.arc_stages must be an array")
                arc_stages = []
            elif importance == "core" and not arc_stages:
                self.error(f"{label}.arc_stages must be non-empty for core characters")
            seen_arc_units: list[str] = []
            for arc_index, arc in enumerate(arc_stages):
                arc_label = f"{label}.arc_stages[{arc_index}]"
                if not isinstance(arc, dict):
                    self.error(f"{arc_label} is not an object")
                    continue
                reject_extra(
                    arc,
                    {
                        "label",
                        "state",
                        "pressure",
                        "choice",
                        "change",
                        "unit_ids",
                    },
                    arc_label,
                )
                validate_text_fields(
                    arc,
                    ("label", "state", "pressure", "choice", "change"),
                    arc_label,
                )
                arc_units = arc.get("unit_ids")
                if not string_list(arc_units, nonempty=True):
                    self.error(f"{arc_label}.unit_ids must be non-empty")
                    continue
                if not set(arc_units).issubset(set(unit_ids)):
                    self.error(
                        f"{arc_label}.unit_ids must belong to character.unit_ids"
                    )
                seen_arc_units.extend(arc_units)
            if len(seen_arc_units) != len(set(seen_arc_units)):
                self.error(f"{label}.arc_stages contain duplicate unit coverage")
            if importance == "core" and set(seen_arc_units) != set(unit_ids):
                self.error(
                    f"{label}.arc_stages must exactly cover core character.unit_ids"
                )
        if not core_character_ids:
            self.error("conception.characters must contain at least one core profile")

        for label, character_id, unit_id in environment_character_refs:
            if character_id not in character_ids:
                self.error(
                    f"{label}: unknown canonical character {character_id}"
                )
                continue
            if (
                unit_id is not None
                and unit_id not in profile_units.get(character_id, set())
            ):
                self.error(
                    f"{label}: active character {character_id} does not "
                    f"carry hosted unit {unit_id}"
                )
        for (
            label,
            character_id,
            event_unit_ids,
            event_environment_ids,
        ) in major_event_character_refs:
            if character_id not in character_ids:
                self.error(
                    f"{label}: unknown canonical participant {character_id}"
                )
                continue
            if not (
                profile_units.get(character_id, set()) & event_unit_ids
            ):
                self.error(
                    f"{label}: participant {character_id} does not carry "
                    "any event unit"
                )
            if not any(
                character_id
                in unit_environment_characters.get(
                    (unit_id, environment_id), set()
                )
                for unit_id in event_unit_ids
                for environment_id in event_environment_ids
            ):
                self.error(
                    f"{label}: participant {character_id} is not active in "
                    "a listed event environment"
                )
        enacted_opposition_characters: set[str] = set()
        for label, character_id, actor_role, action_text in major_event_actor_refs:
            if character_id not in character_ids:
                continue
            name = profile_names.get(character_id, "")
            normalized_action = normalized_business_text(action_text)
            normalized_name = normalized_business_text(name)
            name_tokens = [
                normalized_business_text(token)
                for token in str(name).split()
                if len(normalized_business_text(token)) >= 2
            ]
            if normalized_name not in normalized_action and not any(
                token in normalized_action for token in name_tokens
            ):
                self.error(
                    f"{label}: {actor_role} {character_id} must be named in "
                    "the corresponding event action"
                )
            if actor_role == "opposition":
                enacted_opposition_characters.add(character_id)
        for (
            event_label,
            environment_id,
            used_zone_ids,
            active_character_ids,
        ) in environment_event_bindings:
            zone_occupants = environment_zone_occupants.get(
                environment_id, {}
            )
            present_characters: set[str] = set()
            for zone_id in used_zone_ids:
                present_characters.update(
                    zone_occupants.get(zone_id, set())
                )
            missing_characters = (
                active_character_ids - present_characters
            )
            if missing_characters:
                self.error(
                    f"{event_label}: active characters must occupy at least "
                    "one used zone: "
                    + ", ".join(sorted(missing_characters))
                )

        demand_source_ids = set(controls) | set(units) | set(storyline_ids)
        for container in (world, story):
            if not isinstance(container, dict):
                continue
            if nonempty_string(container.get("id")):
                demand_source_ids.add(str(container["id"]))
            for collection in (
                "facets",
                "systems",
                "environments",
                "event_environment_requirements",
                "phases",
                "major_events",
                "storylines",
                "storyline_demands",
            ):
                for record in container.get(collection, []):
                    if (
                        isinstance(record, dict)
                        and nonempty_string(record.get("id"))
                    ):
                        demand_source_ids.add(str(record["id"]))
        if isinstance(story, dict):
            architecture = story.get("storyline_architecture")
            if isinstance(architecture, dict):
                if nonempty_string(architecture.get("id")):
                    demand_source_ids.add(str(architecture["id"]))
                for connection in architecture.get("connection_points", []):
                    if (
                        isinstance(connection, dict)
                        and nonempty_string(connection.get("id"))
                    ):
                        demand_source_ids.add(str(connection["id"]))
        story_character_source_ids = (
            set(storyline_ids)
            | set(major_event_ids)
            | set(environment_ids)
            | set(event_environment_requirement_records)
            | set(world_system_environment_refs)
        )
        if isinstance(story, dict):
            architecture = story.get("storyline_architecture")
            if isinstance(architecture, dict):
                if nonempty_string(architecture.get("id")):
                    story_character_source_ids.add(str(architecture["id"]))
                story_character_source_ids.update(
                    str(connection["id"])
                    for connection in architecture.get(
                        "connection_points", []
                    )
                    if isinstance(connection, dict)
                    and nonempty_string(connection.get("id"))
                )
        demand_ids: set[str] = set()
        observed_demand_categories: set[str] = set()
        resolved_demand_profiles: dict[str, str] = {}
        for index, demand in enumerate(demand_register):
            label = f"conception.characters.demand_register[{index}]"
            if not isinstance(demand, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                demand,
                {
                    "id",
                    "source_controls",
                    "development_decisions",
                    *CHARACTER_DEMAND_FIELDS,
                },
                label,
            )
            demand_id = demand.get("id")
            if (
                not nonempty_string(demand_id)
                or not ID_PATTERN.fullmatch(str(demand_id))
                or demand_id in demand_ids
            ):
                self.error(f"{label}.id is invalid or duplicated")
                continue
            demand_id = str(demand_id)
            demand_ids.add(demand_id)
            category = demand.get("category")
            if category not in CHARACTER_DEMAND_CATEGORIES:
                self.error(f"{label}.category is invalid")
            else:
                observed_demand_categories.add(str(category))
            criticality = demand.get("criticality")
            if criticality not in CHARACTER_DEMAND_CRITICALITY:
                self.error(f"{label}.criticality is invalid")
            resolution = demand.get("resolution")
            if resolution not in CHARACTER_DEMAND_RESOLUTIONS:
                self.error(f"{label}.resolution is invalid")
            naming_requirement = demand.get("naming_requirement")
            if naming_requirement not in CHARACTER_NAMING_REQUIREMENTS:
                self.error(f"{label}.naming_requirement is invalid")
            validate_text_fields(
                demand,
                (
                    "trigger",
                    "story_function",
                    "omission_consequence",
                    "downstream_freedom",
                ),
                label,
            )
            if not nonempty_string(demand.get("omission_consequence"), 20):
                self.error(f"{label}.omission_consequence is too small")
            validate_sources(demand, label, required_areas=set())
            validate_decision_links(demand, label, nonempty=True)
            source_subject_ids = demand.get("source_subject_ids")
            if not string_list(source_subject_ids, nonempty=True):
                self.error(f"{label}.source_subject_ids must be non-empty")
                source_subject_ids = []
            elif len(source_subject_ids) != len(set(source_subject_ids)):
                self.error(f"{label}.source_subject_ids contains duplicates")
            unknown_sources = set(source_subject_ids) - demand_source_ids
            if unknown_sources:
                self.error(
                    f"{label}.source_subject_ids contains unknown subjects: "
                    + ", ".join(sorted(unknown_sources))
                )
            if (
                criticality in {"structural", "supporting"}
                and not set(source_subject_ids) & story_character_source_ids
            ):
                self.error(
                    f"{label}: structural or supporting character demand "
                    "must derive from a finalized storyline, major event, "
                    "storyline connection, world system, event-environment "
                    "requirement, or major environment"
                )
            profile_id = demand.get("profile_id")
            if resolution == "not_applicable":
                if profile_id is not None:
                    self.error(
                        f"{label}.profile_id must be null when not_applicable"
                    )
                if naming_requirement != "not_applicable":
                    self.error(
                        f"{label}.naming_requirement must be not_applicable"
                    )
                if criticality != "contextual":
                    self.error(
                        f"{label}: structural or supporting demand cannot be "
                        "not_applicable"
                    )
            elif resolution == "profile":
                if profile_id not in character_ids:
                    self.error(
                        f"{label}.profile_id must reference a canonical profile"
                    )
                else:
                    resolved_demand_profiles[demand_id] = str(profile_id)
                    if demand_id not in profile_demand_ids.get(
                        str(profile_id), set()
                    ):
                        self.error(
                            f"{label}: profile {profile_id} does not carry "
                            "the demand id"
                        )
                    if (
                        criticality in {"structural", "supporting"}
                        and profile_importance.get(str(profile_id))
                        == "peripheral"
                    ):
                        self.error(
                            f"{label}: structural or supporting demand cannot "
                            "resolve to a peripheral profile"
                        )
                    if (
                        criticality in {"structural", "supporting"}
                        and naming_requirement != "named"
                    ):
                        self.error(
                            f"{label}: structural or supporting demand requires "
                            "a named character"
                        )
                    if (
                        naming_requirement == "named"
                        and profile_naming_status.get(str(profile_id))
                        == "functional"
                    ):
                        self.error(
                            f"{label}: named demand resolves to a functional "
                            "character label"
                        )
                if naming_requirement == "not_applicable":
                    self.error(
                        f"{label}.naming_requirement cannot be not_applicable "
                        "for a profile resolution"
                    )
            if (
                category == "opposition_execution"
                and resolution == "profile"
                and isinstance(profile_id, str)
                and profile_id not in enacted_opposition_characters
            ):
                self.error(
                    f"{label}: opposition profile {profile_id} must enact at "
                    "least one major-event opposition response"
                )
        if observed_demand_categories != CHARACTER_DEMAND_CATEGORIES:
            missing = CHARACTER_DEMAND_CATEGORIES - observed_demand_categories
            extra = observed_demand_categories - CHARACTER_DEMAND_CATEGORIES
            details = sorted(missing | extra)
            self.error(
                "character demand register must cover every responsibility "
                "category"
                + (": " + ", ".join(details) if details else "")
            )
        for character_id, carried_demands in profile_demand_ids.items():
            unknown_demands = carried_demands - demand_ids
            if unknown_demands:
                self.error(
                    f"{character_id}.demand_ids contains unknown demands: "
                    + ", ".join(sorted(unknown_demands))
                )
            expected_demands = {
                demand_id
                for demand_id, profile_id in resolved_demand_profiles.items()
                if profile_id == character_id
            }
            if carried_demands != expected_demands:
                self.error(
                    f"{character_id}.demand_ids must exactly match resolved "
                    "character demands"
                )

        relationship_ids: set[str] = set()
        observed_pairs: set[tuple[str, str]] = set()
        adjacency: dict[str, set[str]] = {
            character_id: set() for character_id in character_ids
        }
        storyline_relationship_adjacency: dict[
            str, dict[str, set[str]]
        ] = {
            storyline_id: {
                character_id: set() for character_id in character_ids
            }
            for storyline_id in storyline_ids
        }
        for index, relation in enumerate(relationships):
            label = f"conception.characters.relationships[{index}]"
            if not isinstance(relation, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                relation,
                {
                    "id",
                    "source_controls",
                    "development_decisions",
                    *RELATIONSHIP_FIELDS,
                },
                label,
            )
            relation_id = relation.get("id")
            if (
                not nonempty_string(relation_id)
                or not ID_PATTERN.fullmatch(str(relation_id))
                or relation_id in relationship_ids
            ):
                self.error(f"{label}.id is invalid or duplicated")
                continue
            relationship_ids.add(str(relation_id))
            validate_sources(relation, label, required_areas={"character"})
            validate_decision_links(relation, label, nonempty=True)
            validate_text_fields(
                relation,
                (
                    "source_id",
                    "target_id",
                    "relationship_type",
                    "shared_history",
                    "alignment",
                    "conflict",
                    "leverage",
                    "information_asymmetry",
                    "change",
                    "downstream_freedom",
                ),
                label,
            )
            source_id = relation.get("source_id")
            target_id = relation.get("target_id")
            if (
                source_id not in character_ids
                or target_id not in character_ids
                or source_id == target_id
            ):
                self.error(
                    f"{label}: source_id and target_id must identify two "
                    "different canonical character profiles"
                )
                continue
            pair = tuple(sorted((str(source_id), str(target_id))))
            if pair in observed_pairs:
                self.error(
                    f"{label}: duplicate character pair; merge multiple pressures "
                    "into one canonical relationship edge"
                )
            observed_pairs.add(pair)
            adjacency[str(source_id)].add(str(target_id))
            adjacency[str(target_id)].add(str(source_id))
            relation_storylines = relation.get("storyline_ids")
            if not string_list(relation_storylines, nonempty=True):
                self.error(f"{label}.storyline_ids must be non-empty")
                relation_storylines = []
            elif len(relation_storylines) != len(set(relation_storylines)):
                self.error(f"{label}.storyline_ids contains duplicates")
            for storyline_id in relation_storylines:
                if storyline_id not in storyline_ids:
                    self.error(f"{label}: unknown storyline {storyline_id}")
            if not set(relation_storylines).issubset(
                profile_storylines.get(str(source_id), set())
                & profile_storylines.get(str(target_id), set())
            ):
                self.error(
                    f"{label}.storyline_ids must be carried by both endpoint profiles"
                )
            for storyline_id in set(relation_storylines) & storyline_ids:
                line_adjacency = storyline_relationship_adjacency[
                    storyline_id
                ]
                line_adjacency[str(source_id)].add(str(target_id))
                line_adjacency[str(target_id)].add(str(source_id))
            relation_units = relation.get("unit_ids")
            if not string_list(relation_units, nonempty=True):
                self.error(f"{label}.unit_ids must be non-empty")
                relation_units = []
            elif len(relation_units) != len(set(relation_units)):
                self.error(f"{label}.unit_ids contains duplicates")
            if not set(relation_units).issubset(
                profile_units.get(str(source_id), set())
                & profile_units.get(str(target_id), set())
            ):
                self.error(
                    f"{label}.unit_ids must be carried by both endpoint profiles"
                )

        connection_incoming_pairs: set[tuple[str, str]] = set()
        if isinstance(story, dict):
            architecture = story.get("storyline_architecture")
            if isinstance(architecture, dict):
                for connection in architecture.get("connection_points", []):
                    if not isinstance(connection, dict):
                        continue
                    event_id = connection.get("event_id")
                    if not isinstance(event_id, str):
                        continue
                    connection_incoming_pairs.update(
                        (event_id, storyline_id)
                        for storyline_id in string_values(
                            connection.get("incoming_storyline_ids")
                        )
                    )

        profile_carriers_by_storyline = {
            storyline_id: {
                character_id
                for character_id, carried_lines in profile_storylines.items()
                if storyline_id in carried_lines
            }
            for storyline_id in storyline_ids
        }
        environment_carriers_by_storyline = {
            storyline_id: {
                environment_id
                for (
                    environment_id,
                    carried_lines,
                ) in environment_storylines_by_id.items()
                if storyline_id in carried_lines
            }
            for storyline_id in storyline_ids
        }
        for storyline_id, storyline in storyline_records.items():
            protagonists = storyline_protagonist_refs.get(storyline_id, [])
            unknown_protagonists = set(protagonists) - character_ids
            if unknown_protagonists:
                self.error(
                    f"storyline {storyline_id}.protagonists must reference "
                    "canonical character profiles: "
                    + ", ".join(sorted(unknown_protagonists))
                )
            noncarrying_protagonists = {
                protagonist_id
                for protagonist_id in protagonists
                if protagonist_id in character_ids
                and storyline_id
                not in profile_storylines.get(protagonist_id, set())
            }
            if noncarrying_protagonists:
                self.error(
                    f"storyline {storyline_id}.protagonists must carry the "
                    "storyline in their profiles: "
                    + ", ".join(sorted(noncarrying_protagonists))
                )
            if not profile_carriers_by_storyline.get(storyline_id):
                self.error(
                    f"storyline {storyline_id} has no canonical character carrier"
                )
            if not environment_carriers_by_storyline.get(storyline_id):
                self.error(
                    f"storyline {storyline_id} has no major environment carrier"
                )
            canonical_protagonists = [
                protagonist_id
                for protagonist_id in protagonists
                if protagonist_id in character_ids
            ]
            if len(canonical_protagonists) > 1:
                line_adjacency = storyline_relationship_adjacency.get(
                    storyline_id, {}
                )
                reached = {canonical_protagonists[0]}
                queue = [canonical_protagonists[0]]
                for current in queue:
                    for neighbor in line_adjacency.get(current, set()):
                        if neighbor in reached:
                            continue
                        reached.add(neighbor)
                        queue.append(neighbor)
                missing_protagonists = set(canonical_protagonists) - reached
                if missing_protagonists:
                    self.error(
                        f"storyline {storyline_id}.protagonists must form a "
                        "connected relationship subgraph carried by that line: "
                        + ", ".join(sorted(missing_protagonists))
                    )

        for event_id, event in major_event_records.items():
            participants = set(
                string_values(event.get("participant_ids"))
            )
            event_environments = set(
                string_values(event.get("environment_ids"))
            )
            for storyline_id in major_event_line_refs.get(event_id, set()):
                character_carriers = (
                    participants
                    & profile_carriers_by_storyline.get(storyline_id, set())
                )
                if (
                    not character_carriers
                    and (event_id, storyline_id)
                    not in connection_incoming_pairs
                ):
                    self.error(
                        f"major event {event_id} has no participating "
                        f"character who carries storyline {storyline_id}"
                    )
                environment_carriers = (
                    event_environments
                    & environment_carriers_by_storyline.get(
                        storyline_id, set()
                    )
                )
                if not environment_carriers:
                    self.error(
                        f"major event {event_id} has no listed environment "
                        f"that carries storyline {storyline_id}"
                    )

        character_network_depths: dict[str, int] = {}
        reached_from_core: set[str] = set()
        for core_id in sorted(core_character_ids):
            distances = {core_id: 0}
            queue = [core_id]
            for current in queue:
                for neighbor in sorted(adjacency.get(current, set())):
                    if neighbor in distances:
                        continue
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
            reached_from_core.update(distances)
            max_depth = max(distances.values(), default=0)
            character_network_depths[core_id] = max_depth
            if max_depth < MIN_RELATIONSHIP_DEPTH:
                self.error(
                    f"{core_id}: canonical character graph must reach at least "
                    "shortest-path depth 3"
                )
        unreachable = character_ids - reached_from_core
        if unreachable:
            self.error(
                "canonical character profiles are unreachable from every core: "
                + ", ".join(sorted(unreachable))
            )
        self.evidence["conception"] = {
            "world": isinstance(world, dict),
            "story": isinstance(story, dict),
            "phases": len(story.get("phases", []))
            if isinstance(story, dict) and isinstance(story.get("phases"), list)
            else 0,
            "characters": len(profiles),
            "character_demands": len(demand_register),
            "character_demand_categories": sorted(
                observed_demand_categories
            ),
            "character_relationships": len(relationships),
            "character_network_depths": character_network_depths,
            "world_facets": len(world.get("facets", []))
            if isinstance(world, dict) and isinstance(world.get("facets"), list)
            else 0,
            "world_systems": len(world.get("systems", []))
            if isinstance(world, dict) and isinstance(world.get("systems"), list)
            else 0,
            "world_environments": len(world.get("environments", []))
            if isinstance(world, dict)
            and isinstance(world.get("environments"), list)
            else 0,
            "major_events": len(story.get("major_events", []))
            if isinstance(story, dict)
            and isinstance(story.get("major_events"), list)
            else 0,
            "storylines": len(story.get("storylines", []))
            if isinstance(story, dict) and isinstance(story.get("storylines"), list)
            else 0,
            "melody_lines": len(story.get("melody_lines", []))
            if isinstance(story, dict)
            and isinstance(story.get("melody_lines"), list)
            else 0,
        }

    def validate_content_specificity(self, data: dict[str, Any]) -> None:
        critical = {
            "development_gaps": data.get("development_gaps"),
            "design_decisions": data.get("design_decisions"),
            "units": data.get("units"),
            "conception": data.get("conception"),
            "semantic_checks": data.get("semantic_checks"),
            "handoff_self_test": data.get("handoff_self_test"),
        }
        placeholder_hits = []
        for area, value in critical.items():
            match = PLACEHOLDER_PATTERN.search(business_text(value))
            if match:
                placeholder_hits.append(f"{area}:{match.group(0)}")
        if placeholder_hits:
            self.error(
                "content-specificity rejects placeholder language: "
                + ", ".join(placeholder_hits)
            )

        conception = data.get("conception")
        if not isinstance(conception, dict):
            return
        world = conception.get("world")
        story = conception.get("story")
        characters = conception.get("characters")
        groups: dict[str, list[Any]] = {}
        if isinstance(world, dict):
            for key in ("facets", "systems", "environments"):
                value = world.get(key)
                if isinstance(value, list):
                    groups[f"world.{key}"] = value
            environment_zones: list[Any] = []
            environment_events: list[Any] = []
            for environment in world.get("environments", []):
                if not isinstance(environment, dict):
                    continue
                topology = environment.get("topology")
                if isinstance(topology, dict) and isinstance(
                    topology.get("zones"), list
                ):
                    environment_zones.extend(topology["zones"])
                if isinstance(environment.get("event_hosting"), list):
                    environment_events.extend(
                        environment["event_hosting"]
                    )
            groups["world.environment_zones"] = environment_zones
            groups["world.environment_events"] = environment_events
        if isinstance(story, dict):
            value = story.get("major_events")
            if isinstance(value, list):
                groups["story.major_events"] = value
            value = story.get("storylines")
            if isinstance(value, list):
                groups["story.storylines"] = value
        if isinstance(characters, dict):
            for key in ("profiles", "relationships"):
                value = characters.get(key)
                if isinstance(value, list):
                    groups[f"characters.{key}"] = value
        units = data.get("units")
        if isinstance(units, list):
            groups["units"] = units

        repeated: dict[str, int] = {}
        for label, items in groups.items():
            if len(items) < 3:
                continue
            if label == "units" and len(items) < 4:
                continue
            pairs = repeated_template_pairs(items)
            if pairs >= max(2, len(items) // 2):
                repeated[label] = pairs
                self.error(
                    f"content-specificity rejects repeated template language in {label}"
                )

        field_groups: dict[str, tuple[list[Any], tuple[str, ...]]] = {}
        if isinstance(world, dict):
            field_groups["world.systems"] = (
                world.get("systems", []),
                (
                    "definition",
                    "rules",
                    "permissions",
                    "costs",
                    "limits",
                    "failure_modes",
                    "story_effects",
                    "state_changes",
                ),
            )
            field_groups["world.environments"] = (
                world.get("environments", []),
                (
                    "definition",
                    "scope",
                    "distinctive_features",
                    "basic_elements",
                    "sensory_conditions",
                    "occupants_and_access",
                    "resources_and_infrastructure",
                    "rules_and_affordances",
                    "hazards_and_pressures",
                    "story_functions",
                    "state_changes",
                    "topology",
                    "event_hosting",
                    "downstream_freedom",
                ),
            )
            field_groups["world.environment_zones"] = (
                environment_zones,
                ("name", "function", "state", "resources"),
            )
            field_groups["world.environment_events"] = (
                environment_events,
                (
                    "event_function",
                    "entry_state",
                    "available_actions",
                    "blocked_actions",
                    "pressure",
                    "exit_state",
                ),
            )
        if isinstance(story, dict):
            field_groups["story.major_events"] = (
                story.get("major_events", []),
                (
                    "definition",
                    "initiating_action",
                    "opposition_or_complication",
                    "decisive_change",
                    "immediate_outcome",
                    "state_before",
                    "state_after",
                    "next_pressure",
                    "information_effects",
                ),
            )
            field_groups["story.phases"] = (
                story.get("phases", []),
                (
                    "function",
                    "entry_state",
                    "driving_goal",
                    "pressure",
                    "decisive_change",
                    "exit_state",
                ),
            )
            field_groups["story.storylines"] = (
                story.get("storylines", []),
                (
                    "function",
                    "central_question",
                    "driver",
                    "escalation",
                    "major_event_ids",
                    "end_state",
                    "resolution",
                ),
            )
            field_groups["story.melody_lines"] = (
                story.get("melody_lines", []),
                (
                    "function",
                    "variation_pattern",
                    "expansion_options",
                    "omission_effect",
                    "boundaries",
                    "series_potential",
                ),
            )
        if isinstance(characters, dict):
            character_demands = characters.get("demand_register", [])
            character_profiles = characters.get("profiles", [])
            character_relationships = characters.get("relationships", [])
            field_groups["characters.demand_register"] = (
                character_demands,
                (
                    "trigger",
                    "story_function",
                    "omission_consequence",
                ),
            )
            field_groups["characters.profiles"] = (
                character_profiles,
                (
                    "story_function",
                    "surface_goal",
                    "deeper_need",
                    "information_limits",
                    "pressure_behavior",
                    "agency_choices",
                ),
            )
            field_groups["characters.relationships"] = (
                character_relationships,
                (
                    "shared_history",
                    "alignment",
                    "conflict",
                    "leverage",
                    "information_asymmetry",
                    "change",
                ),
            )
        if isinstance(units, list):
            field_groups["units"] = (
                units,
                (
                    "preconditions",
                    "objective",
                    "obstacle",
                    "choice",
                    "opposition",
                    "choice_cost",
                    "consequence",
                    "next_pressure",
                    "exit_state",
                ),
            )
        handoff = data.get("handoff_self_test")
        if isinstance(handoff, dict) and isinstance(handoff.get("tasks"), list):
            field_groups["handoff_self_test.tasks"] = (
                handoff["tasks"],
                ("response",),
            )

        repeated_fields: dict[str, dict[str, int]] = {}
        for label, (items, fields) in field_groups.items():
            if not isinstance(items, list):
                continue
            if label == "units" and len(items) < 4:
                # Two adjacent units may deliberately share a local contract;
                # repeated late-stage responsibility becomes diagnostic only
                # across a larger development chain.
                continue
            hits = repeated_field_templates(items, fields)
            if hits:
                repeated_fields[label] = hits
                self.error(
                    "content-specificity rejects majority same-field template "
                    f"reuse in {label}: {', '.join(sorted(hits))}"
                )
        controls_by_id = {
            item.get("id"): item
            for item in data.get("control_points", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        decisions_by_id = {
            item.get("id"): item
            for item in data.get("design_decisions", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        grounded_subjects: list[tuple[str, dict[str, Any]]] = []
        for label in ("design_decisions", "units"):
            for item in data.get(label, []):
                if isinstance(item, dict):
                    grounded_subjects.append((label, item))
        if isinstance(world, dict):
            for label in ("facets", "systems", "environments"):
                for item in world.get(label, []):
                    if isinstance(item, dict):
                        grounded_subjects.append((f"world.{label}", item))
        if isinstance(story, dict):
            for item in story.get("major_events", []):
                if isinstance(item, dict):
                    grounded_subjects.append(("story.major_events", item))
            for item in story.get("storylines", []):
                if isinstance(item, dict):
                    grounded_subjects.append(("story.storylines", item))
        if isinstance(characters, dict):
            for demand in characters.get("demand_register", []):
                if isinstance(demand, dict):
                    grounded_subjects.append(("character_demands", demand))
            for character in characters.get("profiles", []):
                if not isinstance(character, dict):
                    continue
                grounded_subjects.append(("characters", character))
            for relation in characters.get("relationships", []):
                if isinstance(relation, dict):
                    grounded_subjects.append(("relationships", relation))
        ungrounded = []
        for label, subject in grounded_subjects:
            sources = [
                controls_by_id[item]
                for item in subject.get("source_controls", [])
                if isinstance(item, str) and item in controls_by_id
            ]
            sources.extend(
                decisions_by_id[item]
                for item in subject.get("development_decisions", [])
                if isinstance(item, str) and item in decisions_by_id
            )
            if not sources:
                continue
            overlap = grounding_tokens(subject) & grounding_tokens(sources)
            if len(overlap) < 2:
                subject_id = subject.get("id", "<unknown>")
                ungrounded.append(f"{label}:{subject_id}")
                self.error(
                    "content-specificity subject lacks story-grounded terms: "
                    f"{label}:{subject_id}"
                )
        self.evidence["content_specificity"] = {
            "placeholder_hits": placeholder_hits,
            "groups_checked": sorted(groups),
            "repeated_template_pairs": repeated,
            "repeated_field_templates": repeated_fields,
            "grounded_subjects_checked": len(grounded_subjects),
            "ungrounded_subjects": ungrounded,
        }

    def validate_design_projection(
        self,
        data: dict[str, Any],
        decisions: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
        obligations: dict[str, dict[str, Any]],
    ) -> None:
        conception = data.get("conception")
        conception_ids: set[str] = set()
        linked_conception_subjects: set[str] = set()
        projected_by_conception: dict[str, set[str]] = {
            decision_id: set() for decision_id in decisions
        }

        def register_record(record: Any, *, decision_bound: bool) -> None:
            if not isinstance(record, dict) or not nonempty_string(record.get("id")):
                return
            subject_id = str(record["id"])
            conception_ids.add(subject_id)
            if not decision_bound:
                return
            linked_conception_subjects.add(subject_id)
            for decision_id in string_values(record.get("development_decisions")):
                if decision_id in projected_by_conception:
                    projected_by_conception[decision_id].add(subject_id)

        if isinstance(conception, dict):
            world = conception.get("world")
            story = conception.get("story")
            characters = conception.get("characters")
            if isinstance(world, dict):
                register_record(world, decision_bound=False)
                for facet in world.get("facets", []):
                    register_record(facet, decision_bound=True)
                for system in world.get("systems", []):
                    register_record(system, decision_bound=True)
                for environment in world.get("environments", []):
                    register_record(environment, decision_bound=True)
                for requirement in world.get(
                    "event_environment_requirements", []
                ):
                    register_record(requirement, decision_bound=True)
            if isinstance(story, dict):
                register_record(story, decision_bound=False)
                for phase in story.get("phases", []):
                    register_record(phase, decision_bound=False)
                for event in story.get("major_events", []):
                    register_record(event, decision_bound=True)
                for storyline in story.get("storylines", []):
                    register_record(storyline, decision_bound=True)
                for demand in story.get("storyline_demands", []):
                    register_record(demand, decision_bound=True)
                for melody in story.get("melody_lines", []):
                    register_record(melody, decision_bound=True)
                architecture = story.get("storyline_architecture")
                register_record(architecture, decision_bound=True)
                if isinstance(architecture, dict):
                    for connection in architecture.get(
                        "connection_points", []
                    ):
                        register_record(connection, decision_bound=True)
            if isinstance(characters, dict):
                for demand in characters.get("demand_register", []):
                    register_record(demand, decision_bound=True)
                for character in characters.get("profiles", []):
                    register_record(
                        character,
                        decision_bound=(
                            isinstance(character, dict)
                            and character.get("importance") != "core"
                        ),
                    )
                for relationship in characters.get("relationships", []):
                    register_record(relationship, decision_bound=True)
        valid_subjects = set(units) | conception_ids | set(obligations)
        projected_by_units: dict[str, set[str]] = {
            decision_id: set() for decision_id in decisions
        }
        for unit_id, unit in units.items():
            for decision_id in string_values(unit.get("development_decisions")):
                if decision_id in projected_by_units:
                    projected_by_units[decision_id].add(unit_id)
        for decision_id, decision in decisions.items():
            projected = set(string_values(decision.get("projected_subjects")))
            for subject_id in projected:
                if subject_id not in valid_subjects:
                    self.error(
                        f"{decision_id}: projected_subjects contains unknown "
                        f"subject {subject_id}"
                    )
            if not projected.intersection(units):
                self.error(
                    f"{decision_id}: must project into at least one development unit"
                )
            if not projected.intersection(conception_ids | set(obligations)):
                self.error(
                    f"{decision_id}: must project into the conception or "
                    "information model"
                )
            if projected_by_units.get(decision_id, set()) != projected.intersection(
                units
            ):
                self.error(
                    f"{decision_id}: projected unit set does not match "
                    "unit development_decisions links"
                )
            if projected_by_conception.get(
                decision_id, set()
            ) != projected.intersection(linked_conception_subjects):
                self.error(
                    f"{decision_id}: projected conception set does not match "
                    "development_decisions links"
                )
        self.evidence["design_projection"] = {
            "decisions": len(decisions),
            "conception_subjects": len(conception_ids),
            "unit_links": sum(len(value) for value in projected_by_units.values()),
            "conception_links": sum(
                len(value) for value in projected_by_conception.values()
            ),
        }

    def validate_derivation_claims(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        claims = data.get("derivation_claims")
        by_id: dict[str, dict[str, Any]] = {}
        by_subject: dict[tuple[str, str, str], dict[str, Any]] = {}
        expected_specs = derived_subject_specs(data)
        decisions = {
            record.get("id"): record
            for record in data.get("design_decisions", [])
            if isinstance(record, dict) and nonempty_string(record.get("id"))
        }
        if not isinstance(claims, list):
            self.error("derivation_claims must be an array")
            claims = []
        for index, claim in enumerate(claims):
            label = f"derivation_claims[{index}]"
            if not isinstance(claim, dict):
                self.error(f"{label} is not an object")
                continue
            claim_id = claim.get("id")
            if not nonempty_string(claim_id) or not ID_PATTERN.fullmatch(claim_id):
                self.error(f"{label}.id is invalid")
                continue
            if claim_id in by_id:
                self.error(f"duplicate derivation claim id: {claim_id}")
                continue
            subject_type = claim.get("subject_type")
            subject_id = claim.get("subject_id")
            field = claim.get("field")
            if not all(
                nonempty_string(value)
                for value in (subject_type, subject_id, field)
            ):
                self.error(f"{claim_id}: derived subject identity is invalid")
                by_id[claim_id] = claim
                continue
            subject = (subject_type, subject_id, field)
            spec = expected_specs.get(subject)
            if spec is None:
                self.error(
                    f"{claim_id}: unknown derived subject "
                    f"{subject_type}.{subject_id}.{field}"
                )
                by_id[claim_id] = claim
                continue
            if subject in by_subject:
                self.error(
                    "duplicate derivation claim for "
                    f"{subject_type}.{subject_id}.{field}"
                )
            else:
                by_subject[subject] = claim
            expected_hash = canonical_value_sha256(spec["value"])
            if claim.get("value_sha256") != expected_hash:
                self.error(
                    f"{claim_id}: value_sha256 does not bind "
                    f"{subject_type}.{subject_id}.{field}"
                )
            source_controls = claim.get("source_controls")
            source_decisions = claim.get("source_decisions", [])
            if not string_list(source_controls, nonempty=False):
                self.error(
                    f"{claim_id}: source_controls must be a string array"
                )
                source_controls = []
            if not string_list(source_decisions, nonempty=False):
                self.error(
                    f"{claim_id}: source_decisions must be a string array"
                )
                source_decisions = []
            if not source_controls and not source_decisions:
                self.error(
                    f"{claim_id}: at least one source control or design decision is required"
                )
            allowed_sources = allowed_derivation_sources(
                str(subject_type),
                str(subject_id),
                spec["record"],
            )
            for control_id in source_controls:
                if control_id not in controls:
                    self.error(f"{claim_id}: unknown source control {control_id}")
                if control_id not in allowed_sources:
                    self.error(
                        f"{claim_id}: source control is not authorized for "
                        f"{subject_type}.{subject_id}: {control_id}"
                    )
            allowed_decisions = {
                decision_id
                for decision_id, decision in decisions.items()
                if subject_id
                in set(string_values(decision.get("projected_subjects")))
            }
            if subject_type in {
                "unit",
                "world_facet",
                "world_system",
                "world_environment",
                "event_environment_requirement",
                "major_event",
                "storyline",
                "storyline_demand",
                "storyline_architecture",
                "storyline_connection",
                "melody_line",
                "relationship_layer",
                "character_relationship",
            }:
                allowed_decisions &= allowed_derivation_decisions(
                    str(subject_type),
                    spec["record"],
                )
            for decision_id in source_decisions:
                if decision_id not in decisions:
                    self.error(
                        f"{claim_id}: unknown source decision {decision_id}"
                    )
                elif decision_id not in allowed_decisions:
                    self.error(
                        f"{claim_id}: source decision is not projected to "
                        f"{subject_type}.{subject_id}: {decision_id}"
                    )
            if field in {
                "opposition",
                "choice_options",
                "choice_cost",
                "consequence",
                "next_pressure",
            } and not source_decisions:
                self.error(
                    f"{claim_id}: autonomous development field {field} "
                    "requires source_decisions"
                )
            if not nonempty_string(claim.get("rationale"), 20):
                self.error(f"{claim_id}: rationale is too small")
            by_id[claim_id] = claim
        expected_subjects = set(expected_specs)
        missing = expected_subjects - set(by_subject)
        for subject_type, subject_id, field in sorted(missing):
            self.error(
                "missing derivation claim for "
                f"{subject_type}.{subject_id}.{field}"
            )
        extras = set(by_subject) - expected_subjects
        for subject_type, subject_id, field in sorted(extras):
            self.error(
                "unexpected derivation claim for "
                f"{subject_type}.{subject_id}.{field}"
            )
        self.evidence["derivation_claims"] = {
            "required": len(expected_subjects),
            "recorded": len(by_subject),
        }
        return by_id

    def validate_information_lifecycle(
        self,
        obligations: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
        terminal_threads: set[str],
        data: dict[str, Any],
    ) -> None:
        order = {unit_id: index for index, unit_id in enumerate(units)}
        occurrences: dict[str, dict[str, list[int]]] = {
            obligation_id: {
                "establish": [],
                "hint": [],
                "withhold": [],
                "payoff": [],
            }
            for obligation_id in obligations
        }
        for unit_id, unit in units.items():
            information = unit.get("information")
            if not isinstance(information, dict):
                continue
            for field in ("establish", "hint", "withhold", "payoff"):
                values = information.get(field)
                if not isinstance(values, list):
                    continue
                for obligation_id in values:
                    if obligation_id in occurrences:
                        occurrences[obligation_id][field].append(order[unit_id])

        series_terminals = {
            thread.get("terminal_unit")
            for thread in data.get("terminal_threads", [])
            if (
                isinstance(thread, dict)
                and thread.get("role") == "series"
                and isinstance(thread.get("terminal_unit"), str)
            )
        }
        for obligation_id, obligation in obligations.items():
            lifecycle = occurrences[obligation_id]
            plants = sorted(lifecycle["establish"] + lifecycle["hint"])
            payoffs = sorted(lifecycle["payoff"])
            if not plants:
                self.error(
                    f"{obligation_id}: information obligation has no establish or hint"
                )
            if payoffs and (not plants or min(payoffs) <= min(plants)):
                self.error(
                    f"{obligation_id}: payoff must occur after an earlier establish or hint"
                )
            if obligation.get("resolution") == "within_book":
                if not payoffs:
                    self.error(
                        f"{obligation_id}: within_book obligation has no payoff"
                    )
                elif plants and max(payoffs) <= min(plants):
                    self.error(
                        f"{obligation_id}: within_book payoff is not later than its plant"
                    )
            elif obligation.get("resolution") == "series":
                if not series_terminals.intersection(terminal_threads):
                    self.error(
                        f"{obligation_id}: series obligation requires a registered "
                        "series terminal"
                    )
            if not any(lifecycle.values()):
                self.error(f"{obligation_id}: information obligation is never referenced")
        self.evidence["information_lifecycle"] = {
            obligation_id: {
                field: len(indices) for field, indices in lifecycle.items()
            }
            for obligation_id, lifecycle in occurrences.items()
        }

    def validate_acyclic(self, units: dict[str, dict[str, Any]]) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(unit_id: str) -> None:
            if unit_id in visited:
                return
            if unit_id in visiting:
                self.error(f"dependency cycle detected at {unit_id}")
                return
            visiting.add(unit_id)
            for dependency in string_values(units[unit_id].get("depends_on")):
                if dependency in units:
                    visit(dependency)
            visiting.remove(unit_id)
            visited.add(unit_id)

        for unit_id in units:
            visit(unit_id)

    def validate_terminal_threads(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
    ) -> set[str]:
        depended_on: set[str] = set()
        for unit in units.values():
            depended_on.update(
                item
                for item in string_values(unit.get("depends_on"))
                if item in units
            )
        graph_terminals = set(units) - depended_on
        threads = data.get("terminal_threads")
        if not isinstance(threads, list) or not threads:
            self.error("terminal_threads must be a non-empty array")
            threads = []
        ids: set[str] = set()
        registered: set[str] = set()
        main_count = 0
        for index, thread in enumerate(threads):
            label = f"terminal_threads[{index}]"
            if not isinstance(thread, dict):
                self.error(f"{label} is not an object")
                continue
            thread_id = thread.get("id")
            if not nonempty_string(thread_id) or not ID_PATTERN.fullmatch(thread_id):
                self.error(f"{label}.id is invalid")
            elif thread_id in ids:
                self.error(f"duplicate terminal thread id: {thread_id}")
            else:
                ids.add(thread_id)
            if not nonempty_string(thread.get("label")):
                self.error(f"{label}.label is missing")
            role = thread.get("role")
            if role not in TERMINAL_ROLES:
                self.error(f"{label}.role is invalid")
            elif role == "main":
                main_count += 1
            terminal_unit = thread.get("terminal_unit")
            if not isinstance(terminal_unit, str) or terminal_unit not in units:
                self.error(f"{label}: unknown terminal_unit {terminal_unit}")
                continue
            if terminal_unit not in graph_terminals:
                self.error(f"{label}: terminal_unit is not a graph terminal")
            if terminal_unit in registered:
                self.error(f"{label}: duplicate terminal_unit registration {terminal_unit}")
            registered.add(terminal_unit)
            source_controls = thread.get("source_controls")
            if not string_list(source_controls, nonempty=True):
                self.error(f"{label}.source_controls must be non-empty")
                source_controls = []
            for control_id in source_controls:
                if control_id not in controls:
                    self.error(f"{label}: unknown source control {control_id}")
                elif control_id not in units[terminal_unit].get("source_controls", []):
                    self.error(
                        f"{label}: terminal unit does not carry source control {control_id}"
                    )
            if "development_meaning" in thread:
                self.error(
                    f"{label}.development_meaning is not allowed; terminal meaning "
                    "is defined by its source controls and terminal unit"
                )
        if main_count < 1:
            self.error("terminal_threads must contain at least one main thread")
        if graph_terminals != registered:
            self.error(
                "terminal thread registry does not match graph terminals: "
                f"graph={sorted(graph_terminals)}, registered={sorted(registered)}"
            )
        self.evidence["terminal_threads"] = {
            "graph_terminals": sorted(graph_terminals),
            "registered": sorted(registered),
            "main_threads": main_count,
        }
        return graph_terminals

    def validate_coverage(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
    ) -> None:
        coverage = data.get("coverage")
        if not isinstance(coverage, list):
            self.error("coverage must be an array")
            coverage = []
        by_control: dict[str, dict[str, Any]] = {}
        covered_units: set[str] = set()
        for index, item in enumerate(coverage):
            label = f"coverage[{index}]"
            if not isinstance(item, dict):
                self.error(f"{label} is not an object")
                continue
            control_id = item.get("control_id")
            if not nonempty_string(control_id) or control_id not in controls:
                self.error(f"{label}: unknown control_id {control_id}")
                continue
            if control_id in by_control:
                self.error(f"duplicate coverage record for {control_id}")
                continue
            status = item.get("status")
            if status not in COVERAGE_STATUS:
                self.error(f"{control_id}: invalid coverage status")
            unit_ids = item.get("unit_ids")
            if not string_list(unit_ids, nonempty=False):
                self.error(f"{control_id}: unit_ids must be a string array")
                unit_ids = []
            for unit_id in unit_ids:
                if unit_id not in units:
                    self.error(f"{control_id}: unknown unit {unit_id}")
                else:
                    covered_units.add(unit_id)
                    if control_id not in units[unit_id].get("source_controls", []):
                        self.error(
                            f"{control_id}: coverage names {unit_id}, but the unit "
                            "does not name the control"
                        )
            if not nonempty_string(item.get("evidence"), 12):
                self.error(f"{control_id}: coverage evidence is too small")
            hardness = controls[control_id].get("hardness")
            if hardness in {"hard", "delegated"} and (
                status != "covered" or not unit_ids
            ):
                self.error(f"{control_id}: {hardness} control is not fully covered")
            if hardness == "open" and status == "covered" and not unit_ids:
                self.error(f"{control_id}: covered open control has no unit")
            by_control[control_id] = item
        missing_controls = set(controls) - set(by_control)
        if missing_controls:
            self.error(
                "controls missing coverage: " + ", ".join(sorted(missing_controls))
            )
        orphan_units = set(units) - covered_units
        if orphan_units:
            self.error("orphan units: " + ", ".join(sorted(orphan_units)))
        for unit_id, unit in units.items():
            for control_id in string_values(unit.get("source_controls")):
                record = by_control.get(control_id)
                if record is not None and unit_id not in record.get("unit_ids", []):
                    self.error(
                        f"{unit_id}: source control {control_id} does not map back to unit"
                    )
        required = [
            control_id
            for control_id, control in controls.items()
            if control.get("hardness") in {"hard", "delegated"}
        ]
        covered = [
            control_id
            for control_id in required
            if by_control.get(control_id, {}).get("status") == "covered"
            and by_control.get(control_id, {}).get("unit_ids")
        ]
        self.evidence["coverage"] = {
            "control_points": len(controls),
            "records": len(by_control),
            "required": len(required),
            "required_covered": len(covered),
            "hard_coverage_percent": (
                round(len(covered) * 100 / len(required), 2) if required else 0
            ),
            "orphan_units": sorted(orphan_units),
        }

    def validate_open_items(
        self, data: dict[str, Any], controls: dict[str, dict[str, Any]]
    ) -> None:
        open_items = data.get("open_items")
        if not isinstance(open_items, list):
            self.error("open_items must be an array")
            open_items = []
        by_control: dict[str, dict[str, Any]] = {}
        ids: set[str] = set()
        for index, item in enumerate(open_items):
            label = f"open_items[{index}]"
            if not isinstance(item, dict):
                self.error(f"{label} is not an object")
                continue
            item_id = item.get("id")
            if not nonempty_string(item_id) or not ID_PATTERN.fullmatch(item_id):
                self.error(f"{label}.id is invalid")
            elif item_id in ids:
                self.error(f"duplicate open item id: {item_id}")
            else:
                ids.add(item_id)
            control_id = item.get("source_control")
            if not nonempty_string(control_id) or control_id not in controls:
                self.error(f"{label}: unknown source_control {control_id}")
                continue
            if controls[control_id].get("hardness") != "open":
                self.error(f"{control_id}: open item points to non-open control")
            if control_id in by_control:
                self.error(f"duplicate open item for {control_id}")
            if item.get("owner_stage") != controls[control_id].get("owner_stage"):
                self.error(f"{control_id}: open item owner does not match control")
            for field in ("allowed_handling", "forbidden_resolution"):
                if not nonempty_string(item.get(field), 12):
                    self.error(f"{control_id}: {field} is too small")
            by_control[control_id] = item
        expected = {
            control_id
            for control_id, control in controls.items()
            if control.get("hardness") == "open"
        }
        missing = expected - set(by_control)
        if missing:
            self.error("open controls missing handling: " + ", ".join(sorted(missing)))
        self.evidence["open_items"] = {
            "open_controls": len(expected),
            "handling_records": len(by_control),
        }

    def validate_evidence_items(
        self,
        check_id: str,
        evidence: Any,
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
    ) -> set[str]:
        covered_units: set[str] = set()
        if not isinstance(evidence, list) or not evidence:
            self.error(f"semantic check evidence is missing: {check_id}")
            return covered_units
        for index, item in enumerate(evidence):
            label = f"semantic_checks.{check_id}.evidence[{index}]"
            if not isinstance(item, dict):
                self.error(f"{label} is not an object")
                continue
            if not nonempty_string(item.get("claim"), 20):
                self.error(f"{label}.claim is too small")
            control_ids = item.get("control_ids")
            unit_ids = item.get("unit_ids")
            if not string_list(control_ids, nonempty=False):
                self.error(f"{label}.control_ids must be a string array")
                control_ids = []
            if not string_list(unit_ids, nonempty=False):
                self.error(f"{label}.unit_ids must be a string array")
                unit_ids = []
            if not control_ids and not unit_ids:
                self.error(f"{label} cites no control or unit")
            for control_id in control_ids:
                if control_id not in controls:
                    self.error(f"{label}: unknown control {control_id}")
            for unit_id in unit_ids:
                if unit_id not in units:
                    self.error(f"{label}: unknown unit {unit_id}")
                else:
                    covered_units.add(unit_id)
        return covered_units

    def validate_semantic_checks(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
        graph_terminals: set[str],
    ) -> None:
        checks = data.get("semantic_checks")
        if not isinstance(checks, dict):
            self.error("semantic_checks is missing")
            return
        passed = 0
        all_units = set(units)
        plant_units = {
            unit_id
            for unit_id, unit in units.items()
            if isinstance(unit.get("information"), dict)
            and (
                unit["information"].get("hint")
                or unit["information"].get("payoff")
            )
        }
        required_coverage = {
            "gap_resolution": all_units,
            "forward_causality": all_units,
            "reverse_ending": graph_terminals,
            "character_agency": all_units,
            "opposition_adaptation": all_units,
            "choice_costs": all_units,
            "easy_solution": all_units,
            "world_permissions": all_units,
            "pov_information": all_units,
            "plant_payoff": plant_units or all_units,
            "thematic_testing": all_units,
            "minimality": all_units,
            "downstream_sufficiency": all_units,
        }
        for check_id in SEMANTIC_CHECKS:
            errors_before = len(self.errors)
            item = checks.get(check_id)
            if not isinstance(item, dict):
                self.error(f"semantic check is missing: {check_id}")
                continue
            allowed_check_fields = {
                    "status",
                    "reviewer_id",
                    "reviewer_role",
                    "method",
                    "subject_ids",
                    "assertions",
            }
            extra_check_fields = set(item) - allowed_check_fields
            if extra_check_fields:
                self.error(
                    f"semantic_checks.{check_id} has unexpected fields: "
                    + ", ".join(sorted(extra_check_fields))
                )
            if item.get("status") != "pass":
                self.error(f"semantic check did not pass: {check_id}")
            if not nonempty_string(item.get("reviewer_id")):
                self.error(f"semantic check lacks reviewer_id: {check_id}")
            if not nonempty_string(item.get("method"), 20):
                self.error(f"semantic check method is too small: {check_id}")
            subject_ids = item.get("subject_ids")
            if not string_list(subject_ids, nonempty=True):
                self.error(f"semantic check subject_ids are invalid: {check_id}")
                subject_ids = []
            for subject_id in subject_ids:
                if subject_id not in controls and subject_id not in units:
                    self.error(f"{check_id}: unknown subject {subject_id}")
            if item.get("reviewer_role") not in {
                "map_designer",
                "independent_reviewer",
            }:
                self.error(f"invalid reviewer_role for {check_id}")
            assertions = item.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                self.error(f"{check_id}: assertions must be non-empty")
                assertions = []
            assertion_ids: set[str] = set()
            assertion_units: set[str] = set()
            bound_fields_by_unit: dict[str, set[str]] = {}
            for index, assertion in enumerate(assertions):
                label = f"semantic_checks.{check_id}.assertions[{index}]"
                if not isinstance(assertion, dict):
                    self.error(f"{label} is not an object")
                    continue
                allowed_assertion_fields = {
                        "id",
                        "subject_id",
                        "result",
                        "failure_found",
                        "test",
                        "failure_condition",
                        "counterexample",
                        "conclusion",
                        "field_evidence",
                }
                extra_assertion_fields = set(assertion) - allowed_assertion_fields
                if extra_assertion_fields:
                    self.error(
                        f"{label} has unexpected fields: "
                        + ", ".join(sorted(extra_assertion_fields))
                    )
                assertion_id = assertion.get("id")
                if (
                    not nonempty_string(assertion_id)
                    or assertion_id in assertion_ids
                ):
                    self.error(f"{label}.id is missing or duplicated")
                else:
                    assertion_ids.add(str(assertion_id))
                subject_id = assertion.get("subject_id")
                if subject_id not in units:
                    self.error(f"{label}.subject_id must identify a unit")
                    continue
                assertion_units.add(str(subject_id))
                if assertion.get("result") != "pass":
                    self.error(f"{label}.result did not pass")
                if assertion.get("failure_found") is not False:
                    self.error(
                        f"{label}.failure_found must be false for a pass result"
                    )
                for field in (
                    "test",
                    "failure_condition",
                    "counterexample",
                    "conclusion",
                ):
                    if not nonempty_string(assertion.get(field), 20):
                        self.error(f"{label}.{field} is too small")
                field_evidence = assertion.get("field_evidence")
                if not isinstance(field_evidence, list) or not field_evidence:
                    self.error(f"{label}.field_evidence must be non-empty")
                    field_evidence = []
                observed_fields: set[str] = set()
                bound_values: list[Any] = []
                for evidence_index, evidence in enumerate(field_evidence):
                    evidence_label = (
                        f"{label}.field_evidence[{evidence_index}]"
                    )
                    if not isinstance(evidence, dict):
                        self.error(f"{evidence_label} is not an object")
                        continue
                    extra_evidence_fields = set(evidence) - {
                        "field",
                        "value_sha256",
                    }
                    if extra_evidence_fields:
                        self.error(
                            f"{evidence_label} has unexpected fields: "
                            + ", ".join(sorted(extra_evidence_fields))
                        )
                    field = evidence.get("field")
                    unit = units[str(subject_id)]
                    if field not in unit:
                        self.error(
                            f"{evidence_label}.field does not exist on "
                            f"unit {subject_id}"
                        )
                        continue
                    if field in observed_fields:
                        self.error(f"{evidence_label}.field is duplicated")
                    observed_fields.add(str(field))
                    value = unit.get(str(field))
                    bound_values.append(value)
                    if evidence.get("value_sha256") != canonical_value_sha256(
                        value
                    ):
                        self.error(
                            f"{evidence_label}.value_sha256 does not bind the "
                            "current unit field"
                        )
                bound_fields_by_unit.setdefault(str(subject_id), set()).update(
                    observed_fields
                )
                assertion_text = {
                    field: assertion.get(field)
                    for field in (
                        "test",
                        "failure_condition",
                        "counterexample",
                        "conclusion",
                    )
                }
                bound_tokens = grounding_tokens(bound_values)
                overlap = grounding_tokens(assertion_text) & bound_tokens
                required_overlap = min(2, len(bound_tokens))
                if bound_tokens and len(overlap) < required_overlap:
                    self.error(
                        f"{label}: semantic assertion is not grounded in its "
                        "bound field values"
                    )
            missing_units = required_coverage[check_id] - assertion_units
            if missing_units:
                self.error(
                    f"{check_id} assertions do not cover units: "
                    + ", ".join(sorted(missing_units))
                )
            for unit_id in required_coverage[check_id]:
                missing_fields = SEMANTIC_REQUIRED_UNIT_FIELDS[check_id] - (
                    bound_fields_by_unit.get(unit_id, set())
                )
                if missing_fields:
                    self.error(
                        f"{check_id}: unit {unit_id} lacks required field "
                        "bindings: "
                        + ", ".join(sorted(missing_fields))
                    )
            if len(self.errors) == errors_before:
                passed += 1
        self.evidence["semantic_checks"] = {
            "required": len(SEMANTIC_CHECKS),
            "recorded": len([key for key in SEMANTIC_CHECKS if key in checks]),
            "nominally_passed": passed,
        }

    def validate_handoff_self_test(
        self,
        data: dict[str, Any],
        controls: dict[str, dict[str, Any]],
        units: dict[str, dict[str, Any]],
    ) -> None:
        item = data.get("handoff_self_test")
        if not isinstance(item, dict):
            self.error("handoff_self_test is missing")
            return
        if item.get("status") != "pass":
            self.error("handoff_self_test did not pass")
        if item.get("reviewer_role") != "map_designer":
            self.error("handoff_self_test reviewer_role must be map_designer")
        if item.get("assurance") != "self_test":
            self.error("handoff_self_test assurance must be self_test")
        if item.get("evidence_scope") != "d1_package_only":
            self.error(
                "handoff_self_test evidence_scope must be d1_package_only"
            )
        if "context_policy" in item:
            self.error(
                "handoff_self_test must not claim context isolation; "
                "use evidence_scope"
            )
        if not nonempty_string(item.get("reviewer_id")):
            self.error("handoff_self_test lacks reviewer_id")
        if not nonempty_string(item.get("method"), 20):
            self.error("handoff_self_test method is too small")
        subject_ids = item.get("subject_ids")
        if not string_list(subject_ids, nonempty=True):
            self.error("handoff_self_test subject_ids are invalid")
            subject_ids = []
        if set(subject_ids) != set(units):
            self.error("handoff_self_test subject_ids must exactly cover all units")
        self.validate_evidence_items(
            "handoff_self_test", item.get("evidence"), controls, units
        )
        tasks = item.get("tasks")
        if not isinstance(tasks, list):
            self.error("handoff_self_test tasks must be an array")
            tasks = []
        observed: set[str] = set()
        additional_evidence_ids = {
            record.get("id")
            for collection in (
                data.get("derivation_claims"),
                data.get("information_obligations"),
                data.get("development_gaps"),
                data.get("design_decisions"),
            )
            if isinstance(collection, list)
            for record in collection
            if isinstance(record, dict) and nonempty_string(record.get("id"))
        }
        valid_evidence_ids = set(controls) | set(units) | additional_evidence_ids
        for index, task in enumerate(tasks):
            label = f"handoff_self_test.tasks[{index}]"
            if not isinstance(task, dict):
                self.error(f"{label} is not an object")
                continue
            task_id = task.get("id")
            if task_id in observed:
                self.error(f"duplicate handoff self-test task: {task_id}")
            observed.add(task_id)
            if task.get("status") != "pass":
                self.error(f"{label} did not pass")
            if not nonempty_string(task.get("response"), 40):
                self.error(f"{label}.response is too small")
            evidence_ids = task.get("evidence_ids")
            if not string_list(evidence_ids, nonempty=True):
                self.error(f"{label}.evidence_ids must be non-empty")
                evidence_ids = []
            for evidence_id in evidence_ids:
                if evidence_id not in valid_evidence_ids:
                    self.error(f"{label}: unknown evidence id {evidence_id}")
        if observed != HANDOFF_TASKS:
            self.error("handoff_self_test must contain exactly eight required tasks")
        self.evidence["handoff_self_test"] = {
            "required_tasks": len(HANDOFF_TASKS),
            "recorded_tasks": len(observed),
            "assurance": item.get("assurance"),
        }

    def validate_content_documents(self, data: dict[str, Any]) -> None:
        if (self.package_dir / "blocked-map-report.md").exists():
            self.error("ready/revise map package must not contain blocked-map-report.md")
        expected = render_content_documents(data)
        for filename, rendered in expected.items():
            path = self.package_dir / filename
            if not path.is_file():
                self.error(f"missing rendered business document: {filename}")
                continue
            try:
                actual = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                self.error(f"business document is unreadable: {filename}: {exc}")
                continue
            if actual != rendered.rstrip() + "\n":
                self.error(
                    f"{filename} is stale or was not produced by the deterministic renderer"
                )
        self.evidence["documents"] = {
            filename: {
                "present": (self.package_dir / filename).is_file(),
                "sha256": sha256(self.package_dir / filename)
                if (self.package_dir / filename).is_file()
                else None,
            }
            for filename in CONTENT_DOCS
        }

    def result(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.blockers:
            verdict = "blocked"
        elif self.errors or self.mode == "gate" or data.get("status") != "ready":
            verdict = "revise"
        else:
            verdict = "ready"
        return {
            "schema_version": "1.0",
            "harness": HARNESS,
            "run_id": data.get("run_id"),
            "stage": "D1",
            "mode": self.mode,
            "verdict": verdict,
            "errors": self.errors,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "evidence": self.evidence,
        }

    def validate_or_write_map_check(
        self, data: dict[str, Any], result: dict[str, Any], *, write: bool
    ) -> None:
        path = self.package_dir / "map-check.md"
        expected = render_map_check(data, result).rstrip() + "\n"
        if write:
            path.write_text(expected, encoding="utf-8")
        else:
            try:
                actual = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                self.error(f"business document is unreadable: map-check.md: {exc}")
            else:
                if actual != expected:
                    self.error(
                        "map-check.md is stale or does not report the canonical verdict"
                    )
        self.evidence.setdefault("documents", {})["map-check.md"] = {
            "present": path.is_file(),
            "sha256": sha256(path) if path.is_file() else None,
        }

    def validate_declared_blockers(self, data: dict[str, Any]) -> None:
        blockers = data.get("declared_blockers")
        if not isinstance(blockers, list):
            self.error("declared_blockers must be an array")
            return
        for index, blocker in enumerate(blockers):
            if not isinstance(blocker, dict):
                self.block(f"declared_blockers[{index}] is invalid")
                continue
            for field in ("id", "owner_stage", "problem", "required_decision"):
                if not nonempty_string(blocker.get(field)):
                    self.block(f"declared blocker {index} lacks {field}")
            if blocker.get("owner_stage") not in INTERVIEW_STAGES:
                self.block(f"declared blocker {index} has invalid owner_stage")
            if not string_list(blocker.get("affected_controls"), nonempty=True):
                self.block(f"declared blocker {index} lacks affected_controls")
            self.block(
                f"declared blocker {blocker.get('id', index)}: "
                f"{blocker.get('problem', 'unspecified')}"
            )

    def validate_declared_failures(self, data: dict[str, Any]) -> None:
        failures = data.get("declared_failures")
        if not isinstance(failures, list):
            self.error("gate-data.declared_failures must be an array")
            return
        for index, failure in enumerate(failures):
            label = f"declared_failures[{index}]"
            if not isinstance(failure, dict):
                self.error(f"{label} is not an object")
                continue
            for field in ("id", "problem", "evidence", "required_action"):
                if not nonempty_string(failure.get(field), 8):
                    self.error(f"{label}.{field} is too small")
            if failure.get("owner") not in RETURN_OWNERS:
                self.error(f"{label}.owner is invalid")
            self.block(
                f"declared gate failure {failure.get('id', index)}: "
                f"{failure.get('problem', 'unspecified')}"
            )

    def load_root(self) -> dict[str, Any]:
        map_path = self.package_dir / "map-data.json"
        gate_path = self.package_dir / "gate-data.json"
        path: Path | None
        if map_path.is_file():
            path = map_path
            self.mode = "map"
        elif gate_path.is_file():
            path = gate_path
            self.mode = "gate"
        else:
            self.block("map-data.json or gate-data.json is required")
            return {}
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            self.block(f"{path.name} is invalid: {exc}")
            return {}
        if not isinstance(data, dict):
            self.block(f"{path.name} root is not an object")
            return {}
        return data

    def run(self, *, write_map_check: bool = False) -> dict[str, Any]:
        data = self.load_root()
        self.data = data
        if data:
            expected_schema = "4.0" if self.mode == "map" else "1.0"
            if data.get("schema_version") != expected_schema:
                self.error(f"unsupported {self.mode} schema_version")
            allowed_root_fields = (
                {
                    "schema_version",
                    "harness",
                    "run_id",
                    "status",
                    "input_gate",
                    "source_artifacts",
                    "allowed_povs",
                    "control_points",
                    "authority_partition",
                    "development_gaps",
                    "design_decisions",
                    "units",
                    "conception",
                    "information_obligations",
                    "derivation_claims",
                    "terminal_threads",
                    "coverage",
                    "open_items",
                    "semantic_checks",
                    "handoff_self_test",
                    "declared_blockers",
                }
                if self.mode == "map"
                else {
                    "schema_version",
                    "harness",
                    "run_id",
                    "status",
                    "input_gate",
                    "declared_failures",
                }
            )
            extra_root_fields = set(data) - allowed_root_fields
            if extra_root_fields:
                self.error(
                    f"{self.mode} root contains unsupported fields: "
                    + ", ".join(sorted(extra_root_fields))
                )
            if data.get("harness") != HARNESS:
                self.block("package belongs to another harness")
            if not nonempty_string(data.get("run_id")):
                self.block("run_id is missing")
            if self.mode == "map":
                execution_errors, execution_evidence = verify_record(
                    self.package_dir,
                    data,
                )
                self.errors.extend(execution_errors)
                self.evidence["autonomous_execution"] = execution_evidence
            self.validate_input_gate(data)
            if self.mode == "gate":
                if data.get("status") != "blocked":
                    self.error("gate-data status must be blocked")
                self.validate_declared_failures(data)
                if any((self.package_dir / filename).exists() for filename in DOCS):
                    self.error("blocked gate package must not contain ready business documents")
                if not self.blockers:
                    self.error("gate-data declares blocked without a gate failure")
            else:
                if data.get("status") not in PACKAGE_STATUS:
                    self.error("invalid package status")
                artifacts = self.validate_source_artifacts(data)
                controls = self.validate_control_points(data, artifacts)
                self.validate_authority_partition(data, controls)
                gaps = self.validate_development_gaps(data, controls)
                decisions = self.validate_design_decisions(
                    data, controls, gaps
                )
                obligations = self.validate_information_obligations(data, controls)
                units = self.validate_units(
                    data, controls, obligations, decisions
                )
                self.validate_conception(data, controls, units, decisions)
                self.validate_content_specificity(data)
                self.validate_design_projection(
                    data, decisions, units, obligations
                )
                self.validate_derivation_claims(data, controls)
                terminals = self.validate_terminal_threads(data, controls, units)
                self.validate_information_lifecycle(
                    obligations, units, terminals, data
                )
                self.validate_coverage(data, controls, units)
                self.validate_open_items(data, controls)
                self.validate_semantic_checks(data, controls, units, terminals)
                self.validate_handoff_self_test(data, controls, units)
                self.validate_content_documents(data)
                self.validate_declared_blockers(data)

        result = self.result(data)
        if self.mode == "map":
            self.validate_or_write_map_check(data, result, write=write_map_check)
            if result["verdict"] == "ready" and self.errors:
                result = self.result(data)
        return result


def render_blocked_report(data: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [
        "# 小说开发地图阻塞报告",
        "",
        "## 运行与范围",
        "",
        f"- Run：`{data.get('run_id', '—')}`",
        "- 阶段：D1 硬准入",
        "- 结论：不得生成开发地图。",
        "",
        "## 客观阻塞证据",
        "",
    ]
    for message in result.get("blockers", []):
        lines.append(f"- {message}")
    lines.extend(["", "## 声明缺口与唯一拥有者", ""])
    for failure in data.get("declared_failures", []):
        if not isinstance(failure, dict):
            continue
        lines.extend(
            [
                f"### {failure.get('id', 'UNKNOWN')}",
                "",
                f"- 问题：{failure.get('problem', '—')}",
                f"- 证据：{failure.get('evidence', '—')}",
                f"- 唯一拥有者：{failure.get('owner', '—')}",
                f"- 所需动作：{failure.get('required_action', '—')}",
                "",
            ]
        )
    lines.extend(
        [
            "## 受影响范围与重跑边界",
            "",
            "- 只重跑拥有该缺口的阶段及其失效下游；不得由 D1 补写答案。",
            "- 新 completion、run-state 或作者批准形成后，重新执行硬准入。",
            "",
            "verdict: blocked",
            "",
        ]
    )
    return "\n".join(lines)


def write_package_manifest(
    package_dir: Path, data: dict[str, Any], validation_path: Path
) -> Path:
    files = []
    for filename in PACKAGE_FILES:
        path = package_dir / filename
        files.append({"path": filename, "sha256": sha256(path)})
    manifest = {
        "schema_version": "1.0",
        "harness": HARNESS,
        "run_id": data.get("run_id"),
        "stage": "D1",
        "verdict": "ready",
        "files": files,
        "validation": {
            "path": validation_path.name,
            "sha256": sha256(validation_path),
        },
    }
    path = package_dir / "package-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a novel development-map or blocked gate package."
    )
    parser.add_argument("package_directory", type=Path)
    parser.add_argument(
        "--write-validation",
        action="store_true",
        help="Write validation.json and the appropriate handoff artifact.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    review = Review(package_dir)
    result = review.run(write_map_check=args.write_validation)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.write_validation:
        package_dir.mkdir(parents=True, exist_ok=True)
        validation_path = package_dir / "validation.json"
        validation_path.write_text(rendered + "\n", encoding="utf-8")
        manifest_path = package_dir / "package-manifest.json"
        if result["verdict"] == "ready" and review.mode == "map":
            write_package_manifest(package_dir, review.data, validation_path)
        else:
            if manifest_path.exists():
                manifest_path.unlink()
            if result["verdict"] == "blocked":
                (package_dir / "blocked-map-report.md").write_text(
                    render_blocked_report(review.data, result), encoding="utf-8"
                )
    print(rendered)
    return 0 if result["verdict"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
