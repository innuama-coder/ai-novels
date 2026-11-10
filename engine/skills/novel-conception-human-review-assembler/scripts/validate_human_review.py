from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import (
    ContractError,
    MAIN_SECTIONS,
    READING_SECTIONS,
    REQUIRED_FRAGMENT_TARGETS,
    REQUIRED_REVIEW_TASKS,
    SKILL_NAME,
    all_skill_files,
    build_source_inventory,
    collect_report_element_ids,
    count_text,
    estimated_minutes,
    load_json,
    meaningful_text,
    require,
    sha256_file,
    validate_source_ids,
    verify_manifest,
    write_json,
)

READING_PROFILE_ID = "review-reading-baseline-v1"
BASELINE_CJK_CHARS_PER_MINUTE = 400
BASELINE_LATIN_WORDS_PER_MINUTE = 200
CONTROL_SPINE_LAYERS = [
    "worldview",
    "world_rules",
    "event_space",
    "story_architecture",
    "character_agency",
    "terminal_contract",
]


def _require_keys(obj: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(obj, dict), f"{label} must be an object")
    missing = sorted(keys - set(obj))
    require(not missing, f"{label} missing keys: {missing}")
    return obj


def _validate_text_item(
    value: Any,
    known: set[str],
    label: str,
    *,
    text_key: str = "text",
) -> dict[str, Any]:
    item = _require_keys(value, {"id", text_key, "source_ids"}, label)
    require(
        isinstance(item["id"], str) and item["id"].startswith("HR-"),
        f"{label} must have an HR-* id",
    )
    meaningful_text(item[text_key], f"{label}.{text_key}")
    validate_source_ids(item["source_ids"], known, label)
    return item


def _validate_control_summary(value: Any, label: str) -> str:
    meaningful_text(value, label)
    text = value.strip()
    require(
        not text.endswith(("…", "...", "......")),
        f"{label} cannot end in an ellipsis",
    )
    compact = "".join(text.split())
    require(len(compact) >= 12, f"{label} is too terse to carry control meaning")
    require(
        any(marker in text for marker in ("→", "；", "，", "。", ":", "：", "—")),
        f"{label} must express a relation, transition, or boundary",
    )
    return text


def _visible_reading_view(section_id: str, content: Any) -> Any:
    """Return only content shown by default in the author-facing renderer.

    The blueprint intentionally retains machine-checkable supporting fields.
    Reading time is charged against the control summaries and decisions that
    the author actually sees without opening trace details.
    """
    if not isinstance(content, dict):
        return content
    if section_id == "orientation":
        return {
            "story_identity": content.get("story_identity"),
            "this_is": content.get("this_is"),
            "this_is_not": content.get("this_is_not"),
            "review_instruction": content.get("review_instruction"),
            "logic_spine": [
                {
                    "title": item.get("title"),
                    "claim": item.get("claim"),
                    "therefore": item.get("therefore"),
                    "boundary": item.get("boundary"),
                }
                for item in content.get("logic_spine", [])
            ],
        }
    if section_id == "world":
        return {
            "definition": content.get("definition"),
            "systems": [
                {"name": item.get("name"), "control_summary": item.get("control_summary")}
                for item in content.get("systems", [])
            ],
            "environments": [
                {"name": item.get("name"), "control_summary": item.get("control_summary")}
                for item in content.get("environments", [])
            ],
            "boundaries": content.get("boundaries"),
            "open_interfaces": content.get("open_interfaces"),
            "review_question": content.get("review_question"),
        }
    if section_id == "story":
        return {
            "definition": content.get("definition"),
            "lines": [
                {"name": item.get("name"), "control_summary": item.get("control_summary")}
                for item in content.get("lines", [])
            ],
            "timeline": [
                {"label": item.get("label"), "logic_summary": item.get("logic_summary")}
                for item in content.get("timeline", [])
            ],
            "event_controls": [
                {
                    "name": item.get("name"),
                }
                for item in content.get("event_controls", [])
            ],
            "narrative_constraints": content.get("narrative_constraints"),
            "open_interfaces": content.get("open_interfaces"),
            "review_question": content.get("review_question"),
        }
    if section_id == "characters":
        return {
            "definition": content.get("definition"),
            "profiles": [
                {
                    "name": item.get("name"),
                    "role": item.get("role"),
                    "responsibility": item.get("responsibility"),
                }
                for item in content.get("profiles", [])
            ],
            "relationship_layers": [
                {
                    "function": item.get("function"),
                }
                for item in content.get("relationship_layers", [])
            ],
            "review_question": content.get("review_question"),
        }
    return content


def _collect_element_sources(value: Any) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id.startswith("HR-"):
                source_ids = item.get("source_ids")
                if isinstance(source_ids, list):
                    result[item_id] = set(source_ids)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return result


def _validate_hr_elements(value: Any, known: set[str], path: str = "report") -> None:
    if isinstance(value, dict):
        item_id = value.get("id")
        if isinstance(item_id, str) and item_id.startswith("HR-"):
            validate_source_ids(value.get("source_ids"), known, f"{path}.{item_id}")
            visible_candidates = [
                candidate
                for key, candidate in value.items()
                if key
                not in {
                    "id",
                    "source_ids",
                    "control_ids",
                    "unit_ids",
                    "line_ids",
                    "required_source_ids",
                    "allowed_source_ids",
                    "coverage_targets",
                    "max_cjk_chars",
                    "max_latin_words",
                    "layer",
                    "kind",
                    "type",
                    "character_source_id",
                    "from_character_source_id",
                    "to_character_source_id",
                }
                and isinstance(candidate, str)
            ]
            require(visible_candidates, f"{path}.{item_id} has no visible text")
            for candidate in visible_candidates:
                meaningful_text(candidate, f"{path}.{item_id}")
        for key, child in value.items():
            _validate_hr_elements(child, known, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_hr_elements(child, known, f"{path}[{index}]")


def _validate_reading_budget(plan: dict[str, Any], *, assembled: bool = False) -> dict[str, Any]:
    contract = _require_keys(
        plan.get("review_contract"),
        {
            "work_title",
            "audience",
            "decision",
            "target_minutes",
            "main_sections",
            "out_of_scope",
        },
        "review_contract",
    )
    meaningful_text(contract["work_title"], "review_contract.work_title")
    meaningful_text(contract["audience"], "review_contract.audience")
    meaningful_text(contract["decision"], "review_contract.decision")
    require(contract["target_minutes"] == 10, "target_minutes must be 10")
    require(contract["main_sections"] == MAIN_SECTIONS, "main_sections must be fixed")
    require(
        isinstance(contract["out_of_scope"], list) and len(contract["out_of_scope"]) >= 4,
        "out_of_scope must state at least four boundaries",
    )
    require(
        set(contract["out_of_scope"])
        == {
            "machine_package_replacement",
            "final_novel_prose",
            "html_generation",
            "self_approval",
        },
        "out_of_scope must name the four fixed boundary codes",
    )

    budget = _require_keys(
        plan.get("reading_budget"),
        {"profile", "navigation_minutes", "sections"},
        "reading_budget",
    )
    profile = _require_keys(
        budget["profile"],
        {
            "id",
            "cjk_chars_per_minute",
            "latin_words_per_minute",
            "assumption",
        },
        "reading_budget.profile",
    )
    cjk_rate = profile["cjk_chars_per_minute"]
    latin_rate = profile["latin_words_per_minute"]
    require(profile["id"] == READING_PROFILE_ID, "unknown reading profile")
    require(
        cjk_rate == BASELINE_CJK_CHARS_PER_MINUTE,
        "CJK rate must use the versioned review baseline",
    )
    require(
        latin_rate == BASELINE_LATIN_WORDS_PER_MINUTE,
        "Latin rate must use the versioned review baseline",
    )
    meaningful_text(profile["assumption"], "reading rate assumption")
    sections = budget["sections"]
    require(isinstance(sections, list), "reading sections must be a list")
    by_id = {item.get("id"): item for item in sections if isinstance(item, dict)}
    require(set(by_id) == set(READING_SECTIONS), "reading section ids must be exact")
    require(len(sections) == len(by_id), "duplicate reading section id")
    total = float(budget["navigation_minutes"])
    for section_id in READING_SECTIONS:
        minutes = by_id[section_id].get("minutes")
        require(
            isinstance(minutes, (int, float)) and minutes > 0,
            f"bad reading minutes: {section_id}",
        )
        total += float(minutes)
    require(abs(total - 10.0) < 1e-9, f"reading budget sums to {total}, not 10")

    blueprint = plan.get("report_blueprint", {})
    measurements: dict[str, Any] = {}
    for section_id in READING_SECTIONS:
        content = blueprint.get(section_id)
        require(content is not None, f"missing blueprint section: {section_id}")
        if section_id == "fragments" and not assembled:
            slots = content.get("slots", []) if isinstance(content, dict) else []
            # The plan carries a full writing contract for the downstream
            # fragment skill, but the assembled author-facing report exposes
            # only title, purpose, review question, targets and prose. Do not
            # charge hidden required/prohibited facts, source controls or
            # before/after contracts against the author's ten-minute budget.
            visible_fragment_plan = {
                "sample_authority": content.get("sample_authority"),
                "review_question": content.get("review_question"),
                "items": [
                    {
                        "title": slot.get("title"),
                        "purpose": slot.get("purpose"),
                        "review_question": slot.get("review_question"),
                        "coverage_targets": slot.get("coverage_targets"),
                    }
                    for slot in slots
                ],
            }
            counts = count_text(visible_fragment_plan)
            counts["cjk_chars"] += sum(slot.get("max_cjk_chars", 0) for slot in slots)
            counts["latin_words"] += sum(slot.get("max_latin_words", 0) for slot in slots)
        else:
            counts = count_text(_visible_reading_view(section_id, content))
        minutes = estimated_minutes(counts, float(cjk_rate), float(latin_rate))
        allowed = float(by_id[section_id]["minutes"])
        require(
            minutes <= allowed + 1e-9,
            f"{section_id} needs {minutes:.2f} min, exceeds {allowed:.2f}",
        )
        measurements[section_id] = {
            **counts,
            "estimated_minutes": round(minutes, 4),
            "budget_minutes": allowed,
        }
    measured_total = (
        sum(item["estimated_minutes"] for item in measurements.values())
        + float(budget["navigation_minutes"])
    )
    require(measured_total <= 10.0 + 1e-9, "measured report exceeds 10 minutes")
    return {
        "target_minutes": 10,
        "navigation_minutes": budget["navigation_minutes"],
        "measured_total_minutes": round(measured_total, 4),
        "sections": measurements,
    }


def _validate_blueprint(plan: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    known = set(inventory["known_source_ids"])
    fragment_eligible = set(inventory["fragment_eligible_source_ids"])
    unit_sources = set(inventory["source_id_groups"]["units"])
    control_sources = set(inventory["source_id_groups"]["control_points"])
    bp = _require_keys(
        plan.get("report_blueprint"),
        set(READING_SECTIONS),
        "report_blueprint",
    )
    element_ids = collect_report_element_ids(bp)
    require(element_ids, "report has no HR-* elements")
    _validate_hr_elements(bp, known)

    orientation = _require_keys(
        bp["orientation"],
        {
            "story_identity",
            "this_is",
            "this_is_not",
            "review_instruction",
            "logic_spine",
        },
        "orientation",
    )
    _validate_text_item(orientation["story_identity"], known, "orientation.story_identity")
    _validate_text_item(
        orientation["review_instruction"],
        known,
        "orientation.review_instruction",
    )
    require(isinstance(orientation["this_is"], list) and orientation["this_is"], "this_is empty")
    require(
        isinstance(orientation["this_is_not"], list) and orientation["this_is_not"],
        "this_is_not empty",
    )
    for index, entry in enumerate(orientation["this_is"]):
        _validate_text_item(entry, known, f"orientation.this_is[{index}]")
    for index, entry in enumerate(orientation["this_is_not"]):
        _validate_text_item(entry, known, f"orientation.this_is_not[{index}]")
    logic_spine = orientation["logic_spine"]
    require(
        isinstance(logic_spine, list) and len(logic_spine) == len(CONTROL_SPINE_LAYERS),
        "orientation.logic_spine must contain the six fixed control layers",
    )
    require(
        [item.get("layer") for item in logic_spine if isinstance(item, dict)]
        == CONTROL_SPINE_LAYERS,
        "orientation.logic_spine layers are missing or out of order",
    )
    for index, layer in enumerate(logic_spine):
        item = _require_keys(
            layer,
            {
                "id",
                "layer",
                "title",
                "claim",
                "therefore",
                "controls",
                "must_hold",
                "boundary",
                "source_ids",
            },
            f"orientation.logic_spine[{index}]",
        )
        meaningful_text(item["title"], f"orientation.logic_spine[{index}].title")
        for key in ("claim", "therefore", "controls", "must_hold", "boundary"):
            meaningful_text(item[key], f"orientation.logic_spine[{index}].{key}")
        _validate_control_summary(
            f"{item['claim']}→{item['therefore']}；{item['boundary']}",
            f"orientation.logic_spine[{index}].control_relation",
        )

    world = _require_keys(
        bp["world"],
        {
            "definition",
            "systems",
            "environments",
            "boundaries",
            "open_interfaces",
            "visual_model",
            "review_question",
        },
        "world",
    )
    _validate_text_item(world["definition"], known, "world.definition")
    meaningful_text(world["review_question"], "world.review_question")
    require(isinstance(world["systems"], list) and world["systems"], "world systems empty")
    require(
        isinstance(world["environments"], list) and world["environments"],
        "world environments empty",
    )
    for index, system in enumerate(world["systems"]):
        validated_system = _require_keys(
            system,
            {
                "id",
                "name",
                "definition",
                "rule",
                "permissions",
                "resources",
                "cost_or_failure",
                "controls",
                "must_not",
                "control_summary",
                "source_ids",
            },
            f"world.systems[{index}]",
        )
        for key in (
            "name",
            "definition",
            "rule",
            "permissions",
            "resources",
            "cost_or_failure",
            "controls",
            "must_not",
        ):
            meaningful_text(validated_system[key], f"world.systems[{index}].{key}")
        _validate_control_summary(
            validated_system["control_summary"],
            f"world.systems[{index}].control_summary",
        )
    represented_world_systems = {
        source_id
        for system in world["systems"]
        for source_id in system["source_ids"]
    }
    require(
        set(inventory["source_id_groups"]["world_systems"])
        <= represented_world_systems,
        "world systems do not represent every D1 world system",
    )
    for index, environment in enumerate(world["environments"]):
        validated_environment = _require_keys(
            environment,
            {
                "id",
                "name",
                "signature",
                "elements",
                "access_and_hazard",
                "affordances",
                "prohibitions",
                "story_function",
                "state_change",
                "hosted_event_source_ids",
                "controls",
                "must_hold",
                "control_summary",
                "source_ids",
            },
            f"world.environments[{index}]",
        )
        for key in (
            "name",
            "signature",
            "elements",
            "access_and_hazard",
            "affordances",
            "prohibitions",
            "story_function",
            "state_change",
            "controls",
            "must_hold",
        ):
            meaningful_text(
                validated_environment[key],
                f"world.environments[{index}].{key}",
            )
        hosted = validated_environment["hosted_event_source_ids"]
        require(
            isinstance(hosted, list) and hosted,
            f"world.environments[{index}] must host at least one major event",
        )
        validate_source_ids(hosted, known, f"world.environments[{index}].hosted_event_source_ids")
        _validate_control_summary(
            validated_environment["control_summary"],
            f"world.environments[{index}].control_summary",
        )
    require(isinstance(world["boundaries"], list), "world.boundaries must be a list")
    for index, boundary in enumerate(world["boundaries"]):
        item = _require_keys(
            boundary,
            {"id", "name", "commitment", "source_ids"},
            f"world.boundaries[{index}]",
        )
        meaningful_text(item["name"], f"world.boundaries[{index}].name")
        meaningful_text(item["commitment"], f"world.boundaries[{index}].commitment")
    require(
        isinstance(world["open_interfaces"], list),
        "world.open_interfaces must be a list",
    )
    for index, interface in enumerate(world["open_interfaces"]):
        item = _require_keys(
            interface,
            {"id", "title", "text", "source_ids"},
            f"world.open_interfaces[{index}]",
        )
        meaningful_text(item["title"], f"world.open_interfaces[{index}].title")
        meaningful_text(item["text"], f"world.open_interfaces[{index}].text")
    represented_environments = {
        source_id
        for environment in world["environments"]
        for source_id in environment["source_ids"]
    }
    require(
        set(inventory["source_id_groups"]["world_environments"])
        <= represented_environments,
        "world environments do not represent every D1 environment",
    )
    require(
        world["visual_model"].get("type") == "world-system-map",
        "world visual must be world-system-map",
    )
    _require_keys(world["visual_model"], {"type", "nodes", "edges"}, "world.visual_model")
    require(isinstance(world["visual_model"]["nodes"], list), "world visual nodes must be a list")
    require(isinstance(world["visual_model"]["edges"], list), "world visual edges must be a list")

    story = _require_keys(
        bp["story"],
        {
            "definition",
            "lines",
            "timeline",
            "event_controls",
            "narrative_constraints",
            "open_interfaces",
            "visual_model",
            "review_question",
        },
        "story",
    )
    definition = _require_keys(
        story["definition"],
        {
            "id",
            "promise",
            "dramatic_question",
            "start",
            "end",
            "stakes",
            "source_ids",
        },
        "story.definition",
    )
    for key in ("promise", "dramatic_question", "start", "end", "stakes"):
        meaningful_text(definition[key], f"story.definition.{key}")
    meaningful_text(story["review_question"], "story.review_question")
    require(isinstance(story["lines"], list) and story["lines"], "story lines empty")
    for index, line in enumerate(story["lines"]):
        item = _require_keys(
            line,
            {
                "id",
                "name",
                "kind",
                "function",
                "start",
                "objective",
                "driver",
                "intersections",
                "connection_points",
                "end",
                "exit_condition",
                "must_hold",
                "optional_scope",
                "control_summary",
                "source_ids",
            },
            f"story.lines[{index}]",
        )
        for key in (
            "name",
            "function",
            "start",
            "objective",
            "driver",
            "intersections",
            "connection_points",
            "end",
            "exit_condition",
            "must_hold",
            "optional_scope",
        ):
            meaningful_text(item[key], f"story.lines[{index}].{key}")
        _validate_control_summary(
            item["control_summary"], f"story.lines[{index}].control_summary"
        )
    kinds = {line.get("kind") for line in story["lines"] if isinstance(line, dict)}
    require("main" in kinds, "story needs a main line")
    require(
        kinds <= {"main", "subplot", "background"},
        f"unknown story line kinds: {sorted(kinds)}",
    )
    represented_storylines = {
        source_id for line in story["lines"] for source_id in line.get("source_ids", [])
    }
    require(
        set(inventory["source_id_groups"]["storylines"])
        <= represented_storylines,
        "story lines do not represent every D1 storyline",
    )
    timeline = story["timeline"]
    require(isinstance(timeline, list) and 3 <= len(timeline) <= 8, "timeline needs 3-8 stages")
    covered_units: set[str] = set()
    line_ids = {line.get("id") for line in story["lines"]}
    for index, stage in enumerate(timeline):
        _require_keys(
            stage,
            {
                "id",
                "label",
                "pressure",
                "choice",
                "consequence",
                "cost",
                "new_state",
                "logic_summary",
                "unit_ids",
                "line_ids",
                "source_ids",
            },
            f"story.timeline[{index}]",
        )
        require(stage["unit_ids"], f"story.timeline[{index}] has no unit_ids")
        _validate_control_summary(
            stage["logic_summary"], f"story.timeline[{index}].logic_summary"
        )
        covered_units.update(stage["unit_ids"])
        require(
            set(stage["line_ids"]) <= line_ids,
            f"story.timeline[{index}] cites unknown report line",
        )
    inventory_units = {
        item["source_id"] for item in inventory["review_subjects"] if item["domain"] == "units"
    }
    require(covered_units == inventory_units, "timeline must cover every D1 unit exactly as a set")
    event_controls = story["event_controls"]
    require(
        isinstance(event_controls, list) and event_controls,
        "story.event_controls must define the major event chain",
    )
    event_source_ids: set[str] = set()
    for index, event in enumerate(event_controls):
        item = _require_keys(
            event,
            {
                "id",
                "event_source_id",
                "name",
                "role",
                "logic",
                "controls",
                "line_ids",
                "environment_source_ids",
                "character_source_ids",
                "source_ids",
            },
            f"story.event_controls[{index}]",
        )
        require(
            item["event_source_id"] in known,
            f"unknown event source id: {item['event_source_id']}",
        )
        event_source_ids.add(item["event_source_id"])
        meaningful_text(item["name"], f"story.event_controls[{index}].name")
        meaningful_text(item["role"], f"story.event_controls[{index}].role")
        _validate_control_summary(item["logic"], f"story.event_controls[{index}].logic")
        _validate_control_summary(
            item["controls"], f"story.event_controls[{index}].controls"
        )
        require(
            isinstance(item["line_ids"], list) and item["line_ids"],
            f"story.event_controls[{index}] needs line_ids",
        )
        require(
            set(item["line_ids"]) <= line_ids,
            f"story.event_controls[{index}] cites unknown report line",
        )
        for key in ("environment_source_ids", "character_source_ids"):
            require(
                isinstance(item[key], list) and item[key],
                f"story.event_controls[{index}].{key} cannot be empty",
            )
            validate_source_ids(item[key], known, f"story.event_controls[{index}].{key}")
    required_events = set(inventory["source_id_groups"].get("major_events", []))
    if required_events:
        require(
            event_source_ids == required_events,
            "event_controls must represent every and only D1 major event",
        )
    else:
        require(
            inventory_units <= event_source_ids,
            "legacy plans without major events must represent every D1 unit as an event control",
        )
    require(
        story["visual_model"].get("type") == "multi-line-timeline",
        "story visual must be multi-line-timeline",
    )
    _require_keys(story["visual_model"], {"type", "nodes", "edges"}, "story.visual_model")
    require(isinstance(story["visual_model"]["nodes"], list), "story visual nodes must be a list")
    require(isinstance(story["visual_model"]["edges"], list), "story visual edges must be a list")

    characters = _require_keys(
        bp["characters"],
        {
            "definition",
            "profiles",
            "relationship_layers",
            "visual_model",
            "review_question",
        },
        "characters",
    )
    _validate_text_item(characters["definition"], known, "characters.definition")
    meaningful_text(characters["review_question"], "characters.review_question")
    profiles = characters["profiles"]
    require(isinstance(profiles, list) and profiles, "character profiles empty")
    for index, profile in enumerate(profiles):
        _require_keys(
            profile,
            {
                "id",
                "character_source_id",
                "name",
                "role",
                "story_function",
                "surface_goal",
                "deeper_need",
                "fear",
                "values_and_boundaries",
                "information_limits",
                "pressure_behavior",
                "agency_choice",
                "arc",
                "end_state",
                "invariants",
                "responsibility",
                "authority",
                "nondelegable_choice",
                "controls",
                "must_not",
                "control_summary",
                "source_ids",
            },
            f"characters.profiles[{index}]",
        )
        for key in (
            "name",
            "role",
            "story_function",
            "responsibility",
            "authority",
            "nondelegable_choice",
            "controls",
            "must_not",
        ):
            meaningful_text(profile[key], f"characters.profiles[{index}].{key}")
        _validate_control_summary(
            profile["control_summary"],
            f"characters.profiles[{index}].control_summary",
        )
        require(
            profile["character_source_id"] in known,
            f"unknown character source id: {profile['character_source_id']}",
        )
    profile_source_ids = {profile["character_source_id"] for profile in profiles}
    require(
        profile_source_ids
        == set(
            inventory["source_id_groups"].get(
                "review_characters",
                inventory["source_id_groups"]["core_characters"],
            )
        ),
        "profiles must represent every and only review-relevant D1 characters",
    )
    layers = characters["relationship_layers"]
    require(isinstance(layers, list) and len(layers) >= 3, "need at least 3 relationship layers")
    require(
        len({layer.get("layer") for layer in layers}) >= 3,
        "relationship layers need at least 3 distinct levels",
    )
    for index, layer in enumerate(layers):
        _require_keys(
            layer,
            {
                "id",
                "layer",
                "from_character_source_id",
                "to_character_source_id",
                "function",
                "start_state",
                "pressure",
                "change",
                "end_state",
                "trigger",
                "controls",
                "must_hold",
                "control_summary",
                "source_ids",
            },
            f"characters.relationship_layers[{index}]",
        )
        require(layer["from_character_source_id"] in known, "unknown from character")
        require(layer["to_character_source_id"] in known, "unknown to character")
        for key in ("function", "trigger", "controls", "must_hold"):
            meaningful_text(layer[key], f"characters.relationship_layers[{index}].{key}")
        _validate_control_summary(
            layer["control_summary"],
            f"characters.relationship_layers[{index}].control_summary",
        )
    for character_source_id in set(
        inventory["source_id_groups"]["core_characters"]
    ):
        character_levels = {
            layer["layer"]
            for layer in layers
            if character_source_id
            in {
                layer["from_character_source_id"],
                layer["to_character_source_id"],
            }
        }
        require(
            len(character_levels) >= 3,
            f"core character {character_source_id} needs three relationship levels",
        )
    require(
        characters["visual_model"].get("type") == "layered-relationship-map",
        "character visual must be layered-relationship-map",
    )
    _require_keys(
        characters["visual_model"],
        {"type", "nodes", "edges"},
        "characters.visual_model",
    )
    require(
        isinstance(characters["visual_model"]["nodes"], list),
        "character visual nodes must be a list",
    )
    require(
        isinstance(characters["visual_model"]["edges"], list),
        "character visual edges must be a list",
    )

    fragments = _require_keys(
        bp["fragments"],
        {"sample_authority", "slots", "review_question"},
        "fragments",
    )
    meaningful_text(fragments["sample_authority"], "fragment sample_authority")
    meaningful_text(fragments["review_question"], "fragments.review_question")
    slots = fragments["slots"]
    require(isinstance(slots, list) and 2 <= len(slots) <= 4, "need 2-4 fragment slots")
    targets: set[str] = set()
    for index, slot in enumerate(slots):
        _require_keys(
            slot,
            {
                "id",
                "title",
                "purpose",
                "review_question",
                "pov",
                "before_state",
                "after_state",
                "required_facts",
                "prohibited_facts",
                "required_source_ids",
                "allowed_source_ids",
                "control_ids",
                "unit_ids",
                "narrative_constraints",
                "allowed_creative_freedom",
                "coverage_targets",
                "max_cjk_chars",
                "max_latin_words",
                "source_ids",
            },
            f"fragments.slots[{index}]",
        )
        for key in (
            "title",
            "purpose",
            "review_question",
            "pov",
            "before_state",
            "after_state",
        ):
            meaningful_text(slot[key], f"fragments.slots[{index}].{key}")
        for key in (
            "required_facts",
            "prohibited_facts",
            "narrative_constraints",
            "allowed_creative_freedom",
            "coverage_targets",
        ):
            require(
                isinstance(slot[key], list) and slot[key],
                f"fragments.slots[{index}].{key} must be a non-empty list",
            )
            for item_index, value in enumerate(slot[key]):
                meaningful_text(
                    value,
                    f"fragments.slots[{index}].{key}[{item_index}]",
                )
        allowed = set(
            validate_source_ids(
                slot["allowed_source_ids"],
                fragment_eligible,
                f"slot {index} allowed",
            )
        )
        required_ids = set(
            validate_source_ids(
                slot["required_source_ids"],
                fragment_eligible,
                f"slot {index} required",
            )
        )
        require(required_ids <= allowed, f"slot {index} required ids outside allowed ids")
        require(set(slot["source_ids"]) <= allowed, f"slot {index} source_ids outside allowed")
        require(set(slot["unit_ids"]) <= allowed, f"slot {index} unit_ids outside allowed")
        require(
            set(slot["unit_ids"]) <= unit_sources and slot["unit_ids"],
            f"slot {index} has invalid unit_ids",
        )
        require(
            set(slot["control_ids"]) <= control_sources,
            f"slot {index} has invalid control_ids",
        )
        require(
            isinstance(slot["max_cjk_chars"], int) and slot["max_cjk_chars"] >= 0,
            "bad max_cjk_chars",
        )
        require(
            isinstance(slot["max_latin_words"], int) and slot["max_latin_words"] >= 0,
            "bad max_latin_words",
        )
        require(
            slot["max_cjk_chars"] + slot["max_latin_words"] > 0,
            "fragment slot has zero length",
        )
        slot_targets = set(slot["coverage_targets"])
        require(slot_targets <= REQUIRED_FRAGMENT_TARGETS, "unknown fragment target")
        targets.update(slot_targets)
    require(targets == REQUIRED_FRAGMENT_TARGETS, "fragment slots miss required targets")

    decision = _require_keys(
        bp["decision"],
        {"questions", "options", "open_items", "instruction"},
        "decision",
    )
    require(
        isinstance(decision["questions"], dict)
        and set(decision["questions"]) == set(MAIN_SECTIONS),
        "decision questions must cover four domains",
    )
    require(decision["options"] == ["approve", "revise"], "decision options must be exact")
    meaningful_text(decision["instruction"], "decision.instruction")
    require(isinstance(decision["open_items"], list), "decision.open_items must be a list")
    for domain, question in decision["questions"].items():
        meaningful_text(question, f"decision.questions.{domain}")

    return {
        "element_ids": sorted(element_ids),
        "world_systems": len(world["systems"]),
        "world_environments": len(world["environments"]),
        "story_lines": len(story["lines"]),
        "timeline_stages": len(timeline),
        "character_profiles": len(profiles),
        "relationship_layers": len(layers),
        "fragment_slots": len(slots),
    }


def _validate_coverage(
    plan: dict[str, Any],
    inventory: dict[str, Any],
    element_sources: dict[str, set[str]],
) -> dict[str, Any]:
    ledger = plan.get("coverage_ledger")
    require(isinstance(ledger, list), "coverage_ledger must be a list")
    expected = {item["source_id"]: item for item in inventory["review_subjects"]}
    actual: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(ledger):
        _require_keys(
            entry,
            {"source_id", "domain", "visible_element_ids", "role"},
            f"coverage_ledger[{index}]",
        )
        source_id = entry["source_id"]
        require(source_id not in actual, f"duplicate coverage source: {source_id}")
        require(source_id in expected, f"coverage has unknown subject: {source_id}")
        require(entry["domain"] == expected[source_id]["domain"], f"coverage domain mismatch: {source_id}")
        visible = entry["visible_element_ids"]
        require(isinstance(visible, list) and visible, f"coverage not visible: {source_id}")
        require(
            set(visible) <= set(element_sources),
            f"coverage cites unknown report element: {source_id}",
        )
        require(
            any(source_id in element_sources[element_id] for element_id in visible),
            f"coverage element does not actually cite source: {source_id}",
        )
        meaningful_text(entry["role"], f"coverage role {source_id}")
        actual[source_id] = entry
    missing = sorted(set(expected) - set(actual))
    require(not missing, f"coverage missing review subjects: {missing}")
    return {
        "required_subjects": len(expected),
        "covered_subjects": len(actual),
        "by_domain": {
            domain: sum(1 for item in actual.values() if item["domain"] == domain)
            for domain in ("world", "story", "characters", "units", "open_items")
        },
    }


def _validate_review_tasks(
    plan: dict[str, Any],
    known: set[str],
    element_sources: dict[str, set[str]],
) -> dict[str, Any]:
    tasks = plan.get("review_tasks")
    require(isinstance(tasks, list), "review_tasks must be a list")
    actual: dict[str, Any] = {}
    for index, task in enumerate(tasks):
        _require_keys(
            task,
            {"id", "question", "visible_element_ids", "source_ids"},
            f"review_tasks[{index}]",
        )
        task_id = task["id"]
        require(task_id not in actual, f"duplicate review task: {task_id}")
        meaningful_text(task["question"], f"review task {task_id}")
        require(
            set(task["visible_element_ids"]) <= set(element_sources)
            and task["visible_element_ids"],
            f"review task has bad visible elements: {task_id}",
        )
        task_sources = set(
            validate_source_ids(task["source_ids"], known, f"review task {task_id}")
        )
        visible_sources = set().union(
            *(element_sources[item_id] for item_id in task["visible_element_ids"])
        )
        require(
            task_sources <= visible_sources,
            f"review task sources are not supported by visible elements: {task_id}",
        )
        actual[task_id] = task
    require(set(actual) == REQUIRED_REVIEW_TASKS, "review task ids must be exact")
    return {"required": len(REQUIRED_REVIEW_TASKS), "present": len(actual)}


def _validate_execution_record(package: Path) -> dict[str, Any]:
    record = load_json(package / "execution-record.json")
    require(record.get("skill") == SKILL_NAME, "execution skill mismatch")
    require(record.get("mode") == "autonomous_agent", "execution mode mismatch")
    require(record.get("phase") == "plan", "execution phase mismatch")
    meaningful_text(record.get("executor_id"), "executor_id")
    meaningful_text(record.get("task_id"), "task_id")
    require(
        record.get("inputs", {}).get("source-inventory.json")
        == sha256_file(package / "source-inventory.json"),
        "execution input hash mismatch",
    )
    for name in ("review-plan.json", "fragment-briefs.json"):
        require(
            record.get("outputs", {}).get(name) == sha256_file(package / name),
            f"execution output hash mismatch: {name}",
        )
    skill_dir = Path(__file__).resolve().parent.parent
    current = {
        str(path.relative_to(skill_dir)).replace("\\", "/"): sha256_file(path)
        for path in all_skill_files(skill_dir)
    }
    recorded = {
        item.get("path"): item.get("sha256")
        for item in record.get("skill_files", [])
        if isinstance(item, dict)
    }
    require(recorded == current, "execution record is not bound to current skill files")
    return {
        "mode": record["mode"],
        "executor_id": record["executor_id"],
        "task_id": record["task_id"],
        "skill_files": len(recorded),
    }


def validate_plan_package(package: Path, r1: Path) -> dict[str, Any]:
    package = package.resolve()
    for name in (
        "source-inventory.json",
        "review-plan.json",
        "fragment-briefs.json",
        "execution-record.json",
    ):
        require((package / name).is_file(), f"plan package missing {name}")
    inventory = load_json(package / "source-inventory.json")
    regenerated = build_source_inventory(r1)
    require(inventory == regenerated, "source inventory is stale or hand-edited")
    plan_path = package / "review-plan.json"
    plan = load_json(plan_path)
    require(plan.get("schema_version") == "1.0", "plan schema mismatch")
    require(plan.get("skill") == SKILL_NAME, "plan skill mismatch")
    require(plan.get("status") == "ready", "plan status is not ready")
    require(plan.get("run_id") == inventory.get("run_id"), "plan run id mismatch")
    require(
        plan.get("source_inventory_sha256")
        == sha256_file(package / "source-inventory.json"),
        "plan source inventory hash mismatch",
    )
    blueprint_evidence = _validate_blueprint(plan, inventory)
    element_sources = _collect_element_sources(plan["report_blueprint"])
    require(
        set(element_sources) == set(blueprint_evidence["element_ids"]),
        "report element source index is incomplete",
    )
    coverage = _validate_coverage(plan, inventory, element_sources)
    tasks = _validate_review_tasks(
        plan,
        set(inventory["fragment_eligible_source_ids"]),
        element_sources,
    )
    reading = _validate_reading_budget(plan)

    briefs = load_json(package / "fragment-briefs.json")
    require(briefs.get("skill") == SKILL_NAME, "fragment briefs skill mismatch")
    require(
        briefs.get("review_plan_sha256") == sha256_file(plan_path),
        "fragment briefs plan hash mismatch",
    )
    require(
        briefs.get("slots") == plan["report_blueprint"]["fragments"]["slots"],
        "fragment briefs were not deterministically exported",
    )
    execution = _validate_execution_record(package)
    return {
        "mode": "plan",
        "verdict": "ready",
        "source_inventory": inventory["counts"],
        "blueprint": blueprint_evidence,
        "coverage": coverage,
        "review_tasks": tasks,
        "reading_budget": reading,
        "execution": execution,
    }


def _validate_fragment_package(
    fragment_directory: Path,
    plan: dict[str, Any],
    plan_path: Path,
    known: set[str],
    r1: Path,
) -> dict[str, Any]:
    fragment_validator = (
        Path(__file__).resolve().parent.parent.parent
        / "novel-conception-fragment-writer"
        / "scripts"
        / "validate_fragments.py"
    )
    require(
        fragment_validator.is_file(),
        f"canonical fragment validator is missing: {fragment_validator}",
    )
    canonical = subprocess.run(
        [
            sys.executable,
            str(fragment_validator),
            str(fragment_directory),
            "--plan",
            str(plan_path.parent),
            "--r1",
            str(r1.resolve()),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(
        canonical.returncode == 0,
        "canonical fragment validation failed: "
        + (canonical.stderr.strip() or canonical.stdout.strip()),
    )
    for name in (
        "generation-session.json",
        "fragment-package.json",
        "fragments.md",
        "execution-record.json",
        "package-manifest.json",
        "validation.json",
    ):
        require((fragment_directory / name).is_file(), f"fragment package missing {name}")
    validation = load_json(fragment_directory / "validation.json")
    require(
        validation.get("skill") == "novel-conception-fragment-writer",
        "fragment validation skill mismatch",
    )
    require(validation.get("verdict") == "ready", "fragment validation is not ready")
    require(not validation.get("errors"), "fragment validation has errors")
    package = load_json(fragment_directory / "fragment-package.json")
    require(
        package.get("skill") == "novel-conception-fragment-writer",
        "fragment package skill mismatch",
    )
    require(package.get("status") == "ready", "fragment package is not ready")
    require(
        package.get("review_plan_sha256") == sha256_file(plan_path),
        "fragment package targets another review plan",
    )
    fragments = package.get("fragments")
    require(isinstance(fragments, list), "fragments must be a list")
    by_id = {item.get("id"): item for item in fragments if isinstance(item, dict)}
    slots = plan["report_blueprint"]["fragments"]["slots"]
    slot_by_id = {item["id"]: item for item in slots}
    require(len(by_id) == len(fragments), "duplicate fragment id")
    require(set(by_id) == set(slot_by_id), "fragment ids do not match slots")
    evidence: list[dict[str, Any]] = []
    for fragment_id, fragment in by_id.items():
        slot = slot_by_id[fragment_id]
        _require_keys(
            fragment,
            {
                "id",
                "title",
                "text",
                "source_ids",
                "control_ids",
                "unit_ids",
                "creative_choices",
                "introduced_authoritative_facts",
                "contract_checks",
            },
            f"fragment {fragment_id}",
        )
        text = meaningful_text(fragment["text"], f"fragment {fragment_id}", minimum=40)
        counts = count_text(text)
        require(
            counts["cjk_chars"] <= slot["max_cjk_chars"],
            f"fragment {fragment_id} exceeds CJK limit",
        )
        require(
            counts["latin_words"] <= slot["max_latin_words"],
            f"fragment {fragment_id} exceeds Latin limit",
        )
        cited = set(validate_source_ids(fragment["source_ids"], known, fragment_id))
        require(set(slot["required_source_ids"]) <= cited, f"{fragment_id} misses required sources")
        require(cited <= set(slot["allowed_source_ids"]), f"{fragment_id} cites disallowed sources")
        require(set(fragment["unit_ids"]) == set(slot["unit_ids"]), f"{fragment_id} unit mismatch")
        require(
            fragment["introduced_authoritative_facts"] == [],
            f"{fragment_id} introduces authoritative facts",
        )
        checks = fragment["contract_checks"]
        required_checks = {
            "source_grounding",
            "narrative_contract",
            "no_new_authority",
            "review_question_fit",
        }
        require(
            isinstance(checks, dict)
            and all(checks.get(key) is True for key in required_checks),
            f"{fragment_id} contract checks failed",
        )
        evidence.append({"id": fragment_id, **counts})
    execution_path = fragment_directory / "execution-record.json"
    execution = load_json(execution_path)
    require(
        execution.get("skill") == "novel-conception-fragment-writer",
        "fragment execution skill mismatch",
    )
    require(
        execution.get("mode") == "autonomous_agent",
        "fragment execution mode mismatch",
    )
    meaningful_text(execution.get("executor_id"), "fragment executor_id")
    meaningful_text(execution.get("task_id"), "fragment task_id")
    require(
        execution.get("review_plan_sha256") == sha256_file(plan_path),
        "fragment execution plan hash mismatch",
    )
    require(
        execution.get("fragment_package_sha256")
        == sha256_file(fragment_directory / "fragment-package.json"),
        "fragment execution output hash mismatch",
    )
    validation_evidence = validation.get("evidence", {})
    require(
        validation_evidence.get("review_plan_sha256") == sha256_file(plan_path),
        "fragment validation plan hash mismatch",
    )
    require(
        validation_evidence.get("fragment_package_sha256")
        == sha256_file(fragment_directory / "fragment-package.json"),
        "fragment validation output hash mismatch",
    )
    require(
        validation_evidence.get("execution_record_sha256") == sha256_file(execution_path),
        "fragment validation execution hash mismatch",
    )
    return {"fragments": fragments, "evidence": evidence}


def validate_assembly_package(
    package: Path,
    plan_package: Path,
    fragment_package: Path,
    r1: Path,
) -> dict[str, Any]:
    plan_evidence = validate_plan_package(plan_package, r1)
    plan_path = plan_package / "review-plan.json"
    plan = load_json(plan_path)
    inventory = load_json(plan_package / "source-inventory.json")
    fragment_evidence = _validate_fragment_package(
        fragment_package.resolve(),
        plan,
        plan_path,
        set(inventory["known_source_ids"]),
        r1,
    )
    for name in (
        "human-review-report.json",
        "human-review-report.md",
        "assembly-execution.json",
        "package-manifest.json",
    ):
        require((package / name).is_file(), f"assembly package missing {name}")
    report = load_json(package / "human-review-report.json")
    require(report.get("skill") == SKILL_NAME, "report skill mismatch")
    require(report.get("status") == "ready", "report is not ready")
    require(
        report.get("source_bindings", {}).get("review_plan_sha256")
        == sha256_file(plan_path),
        "report plan hash mismatch",
    )
    expected_blueprint = copy.deepcopy(plan["report_blueprint"])
    fragment_by_id = {item["id"]: item for item in fragment_evidence["fragments"]}
    assembled_fragments = []
    for slot in expected_blueprint["fragments"].pop("slots"):
        sample = fragment_by_id[slot["id"]]
        assembled_fragments.append(
            {
                "id": slot["id"],
                "title": slot["title"],
                "purpose": slot["purpose"],
                "review_question": slot["review_question"],
                "text": sample["text"],
                "coverage_targets": slot["coverage_targets"],
                "source_ids": sample["source_ids"],
            }
        )
    expected_blueprint["fragments"]["items"] = assembled_fragments
    require(report.get("report_blueprint") == expected_blueprint, "report is not a deterministic merge")
    require(report.get("coverage_ledger") == plan["coverage_ledger"], "coverage ledger changed")
    require(report.get("review_tasks") == plan["review_tasks"], "review tasks changed")

    synthetic = {
        "review_contract": report["review_contract"],
        "reading_budget": report["reading_budget"],
        "report_blueprint": report["report_blueprint"],
    }
    reading = _validate_reading_budget(synthetic, assembled=True)
    require(
        report.get("reading_measurement") == reading,
        "stored reading measurement is incorrect",
    )
    manifest = load_json(package / "package-manifest.json")
    verify_manifest(package, manifest)
    execution = load_json(package / "assembly-execution.json")
    require(execution.get("mode") == "deterministic_assembly", "assembly mode mismatch")
    require(
        execution.get("review_plan_sha256") == sha256_file(plan_path),
        "assembly execution plan hash mismatch",
    )
    require(
        execution.get("fragment_package_sha256")
        == sha256_file(fragment_package / "fragment-package.json"),
        "assembly execution fragment hash mismatch",
    )
    return {
        "mode": "assemble",
        "verdict": "ready",
        "plan": plan_evidence,
        "fragments": fragment_evidence["evidence"],
        "reading_budget": reading,
        "deterministic_merge": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate human review plan or assembly.")
    sub = parser.add_subparsers(dest="mode", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("package", type=Path)
    plan_parser.add_argument("--r1", required=True, type=Path)
    assembly_parser = sub.add_parser("assemble")
    assembly_parser.add_argument("package", type=Path)
    assembly_parser.add_argument("--plan", required=True, type=Path)
    assembly_parser.add_argument("--fragments", required=True, type=Path)
    assembly_parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    output_path = args.package.resolve() / "validation.json"
    try:
        if args.mode == "plan":
            evidence = validate_plan_package(args.package, args.r1)
        else:
            evidence = validate_assembly_package(
                args.package.resolve(),
                args.plan.resolve(),
                args.fragments.resolve(),
                args.r1.resolve(),
            )
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": args.mode,
            "verdict": "ready",
            "errors": [],
            "evidence": evidence,
        }
        write_json(output_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": args.mode,
            "verdict": "blocked",
            "errors": [str(exc)],
            "evidence": {},
        }
        write_json(output_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
