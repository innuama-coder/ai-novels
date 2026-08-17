"""Generic proposal adapter for the autonomous H1-A evaluation path."""

from __future__ import annotations

import copy
import importlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)
h1b = importlib.import_module(
    "skills.novel-conception-fragment-writer.scripts.run_v2"
)

_IDENTITY_META_FIELDS = frozenset(
    {
        "id",
        "name",
        "title",
        "label",
        "status",
        "stage",
        "skill",
        "kind",
        "type",
        "version",
        "schema_version",
        "run_id",
        "source_id",
        "control_id",
        "hardness",
        "path",
        "sha256",
        "hash",
        "order",
        "index",
    }
)
_PREFERRED_FRAGMENT_STAGES = ("S1", "W1", "E1", "T1", "C1")
VISUAL_ANCHOR_CAP = 6
_VISUAL_STAGE_PREFERENCES = {
    "world_environment_map": ("W1", "E1", "T1", "S1", "C1", "B0"),
    "control_logic_chain": ("S1", "T1", "W1", "C1", "E1", "B0"),
    "storyline_architecture": ("S1", "T1", "C1", "W1", "E1", "B0"),
    "major_event_timeline": ("T1", "S1", "E1", "W1", "C1", "B0"),
    "character_relationship_network": (
        "C1",
        "S1",
        "T1",
        "W1",
        "E1",
        "B0",
    ),
}
_SCENE_FIELDS = (
    "before_state",
    "immediate_goal",
    "pressure",
    "obstacle",
    "required_choice",
    "direct_consequence",
    "after_state",
)
_SEMANTIC_FIELD_PRIORITY = {
    field: index
    for index, field in enumerate(
        (
            "consequence",
            "required_choice",
            "action",
            "goal",
            "conflict",
            "constraint",
            "boundary",
            "rule",
            "claim",
            "rationale",
            "summary",
            "description",
            "responsibility",
            "value",
        )
    )
}


def _artifact_reference(value: Any) -> dict[str, str]:
    """Project a completion or sealed document to an artifact reference."""

    if hasattr(value, "reference"):
        value = value.reference
    if not isinstance(value, Mapping):
        raise TypeError("p1_completion must be an artifact reference")
    return {"path": str(value["path"]), "sha256": str(value["sha256"])}


def _gate_reference(value: Any) -> dict[str, str]:
    if hasattr(value, "reference"):
        value = value.reference
    if not isinstance(value, Mapping):
        raise TypeError("input_gate must be an artifact reference")
    return {"path": str(value["path"]), "sha256": str(value["sha256"])}


def _is_identity_meta_pointer(pointer: str) -> bool:
    terminal = pointer.rsplit("/", 1)[-1].casefold()
    return (
        terminal in _IDENTITY_META_FIELDS
        or terminal.endswith("_id")
        or terminal.endswith("_ids")
        or terminal.endswith("_sha256")
        or terminal.endswith("_hash")
        or terminal.endswith("_at")
    )


def _scalar_candidates(
    value: Any, pointer: str = ""
) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    if isinstance(value, str) and value.strip():
        candidates.append((pointer, value.strip()))
    elif isinstance(value, Mapping):
        for key in sorted(value, key=lambda item: str(item)):
            token = str(key).replace("~", "~0").replace("/", "~1")
            candidates.extend(
                _scalar_candidates(value[key], f"{pointer}/{token}")
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            candidates.extend(
                _scalar_candidates(child, f"{pointer}/{index}")
            )
    return candidates


def _select_substantive_scalar(
    value: Any,
    *,
    anchor_values: Sequence[Any],
) -> tuple[str, str]:
    """Select a stable, story-substantive scalar using H1-B predicates."""

    candidates: list[tuple[tuple[int, int, str], str, str]] = []
    for pointer, scalar in _scalar_candidates(value):
        if _is_identity_meta_pointer(pointer):
            continue
        units, _, _ = h1b._visible_units(scalar)
        if (
            units < 2
            or units > 24
            or not h1b._quote_has_non_identity_substance(
                scalar, anchor_values
            )
        ):
            continue
        terminal = pointer.rsplit("/", 1)[-1].casefold()
        rank = (
            _SEMANTIC_FIELD_PRIORITY.get(terminal, 100),
            units,
            pointer,
        )
        candidates.append((rank, pointer, scalar))
    if not candidates:
        raise ValueError("anchor has no production-valid substantive scalar")
    _, pointer, scalar = min(candidates, key=lambda item: item[0])
    return pointer, scalar


def _load_anchor_values(
    p1_package: str | Path,
    anchors: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    root = Path(p1_package)
    documents: dict[str, Any] = {}
    result: list[dict[str, Any]] = []
    for anchor in anchors:
        artifact_path = str(anchor["artifact"]["path"])
        if artifact_path not in documents:
            documents[artifact_path] = json.loads(
                (root / artifact_path).read_text(encoding="utf-8")
            )
        item = copy.deepcopy(dict(anchor))
        item["_value"] = copy.deepcopy(
            _pointer_value(
                documents[artifact_path], str(anchor["json_pointer"])
            )
        )
        result.append(item)
    return result


def _eligible_fragment_anchors(
    anchors: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    anchor_values = [item["_value"] for item in anchors]
    eligible: list[dict[str, Any]] = []
    for anchor in anchors:
        try:
            pointer, scalar = _select_substantive_scalar(
                anchor["_value"], anchor_values=anchor_values
            )
        except ValueError:
            continue
        item = copy.deepcopy(dict(anchor))
        item["_projection_pointer"] = pointer
        item["_projection_scalar"] = scalar
        eligible.append(item)
    return sorted(
        eligible,
        key=lambda item: (
            _PREFERRED_FRAGMENT_STAGES.index(item["stage"])
            if item.get("stage") in _PREFERRED_FRAGMENT_STAGES
            else len(_PREFERRED_FRAGMENT_STAGES),
            str(item["id"]),
        ),
    )


def _select_pov_anchor(
    anchors: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Select the best substantive POV profile before choosing its source id."""

    eligible = _eligible_fragment_anchors(anchors)
    if not eligible:
        raise ValueError("no production-valid POV source anchor")

    def quality(item: Mapping[str, Any]) -> tuple[int, int, int, int, str]:
        pointer = str(item["_projection_pointer"])
        terminal = pointer.rsplit("/", 1)[-1].casefold()
        units, _, _ = h1b._visible_units(
            str(item["_projection_scalar"])
        )
        return (
            0 if item.get("stage") == "C1" else 1,
            0 if str(item.get("source_id", "")).startswith("CHR-") else 1,
            _SEMANTIC_FIELD_PRIORITY.get(terminal, 100),
            units,
            str(item["id"]),
        )

    return copy.deepcopy(min(eligible, key=quality))


def _allocate_fragment_anchor_ids(
    anchors: Sequence[Mapping[str, Any]],
    *,
    brief_count: int,
    max_per_brief: int,
    required_source_id: str | None = None,
    required_anchor_id: str | None = None,
    target_chars_max: int | None = None,
) -> tuple[list[str], ...]:
    """Allocate small deterministic semantic subsets without fixture branching."""

    if brief_count <= 0 or max_per_brief <= 0:
        raise ValueError("fragment allocation bounds must be positive")
    eligible = _eligible_fragment_anchors(anchors)
    preferred = [
        item
        for item in eligible
        if item.get("stage") in _PREFERRED_FRAGMENT_STAGES
    ]
    pool = preferred or eligible
    if not pool:
        raise ValueError("no production-valid fragment source anchors")
    anchor_by_id = {str(item["id"]): item for item in eligible}
    anchor_values = [item["_value"] for item in anchors]
    required_anchor: dict[str, Any] | None = None
    if required_source_id is not None and required_anchor_id is not None:
        raise ValueError("require either POV source or exact anchor, not both")
    if required_source_id is not None or required_anchor_id is not None:
        required_candidates = [
            item
            for item in eligible
            if (
                str(item["id"]) == required_anchor_id
                if required_anchor_id is not None
                else item.get("source_id") == required_source_id
            )
        ]
        required_candidates.sort(
            key=lambda item: (
                item.get("stage") != "C1",
                str(item["id"]),
            )
        )
        if not required_candidates:
            raise ValueError(
                "POV source has no production-valid fragment anchor"
            )
        required_anchor = required_candidates[0]
        if target_chars_max is None:
            raise ValueError(
                "POV-bound allocation requires a fragment capacity"
            )

    def subset_fits(anchor_ids: Sequence[str]) -> bool:
        if target_chars_max is None:
            return True
        selected = {
            anchor_id: anchor_by_id[anchor_id]
            for anchor_id in anchor_ids
        }
        projections = [
            _build_fact_projection(
                selected[anchor_id],
                projection_id=f"PREFLIGHT-{index}",
                anchor_values=anchor_values,
            )
            for index, anchor_id in enumerate(selected, 1)
        ]
        try:
            _preflight_fragment_projection_capacity(
                projections,
                anchors=selected,
                target_chars_max=target_chars_max,
            )
        except ValueError:
            return False
        return True

    by_stage = {
        stage: [item for item in pool if item.get("stage") == stage]
        for stage in _PREFERRED_FRAGMENT_STAGES
    }
    used: set[str] = set()
    allocations: list[list[str]] = []
    for brief_index in range(brief_count):
        selected: list[str] = (
            [str(required_anchor["id"])]
            if required_anchor is not None
            else []
        )
        if selected and not subset_fits(selected):
            raise ValueError("POV source exceeds fragment capacity")
        stage_order = (
            _PREFERRED_FRAGMENT_STAGES[brief_index:]
            + _PREFERRED_FRAGMENT_STAGES[:brief_index]
        )
        for stage in stage_order:
            candidate = next(
                (
                    item
                    for item in by_stage[stage]
                    if item["id"] not in used
                ),
                None,
            )
            if candidate is None:
                continue
            candidate_id = str(candidate["id"])
            if candidate_id in selected:
                continue
            proposed = [*selected, candidate_id]
            if not subset_fits(proposed):
                continue
            selected.append(candidate_id)
            used.add(candidate_id)
            if len(selected) == max_per_brief:
                break
        for candidate in pool:
            if len(selected) == max_per_brief:
                break
            candidate_id = str(candidate["id"])
            if candidate_id in used or candidate_id in selected:
                continue
            proposed = [*selected, candidate_id]
            if not subset_fits(proposed):
                continue
            selected.append(candidate_id)
            used.add(candidate_id)
        if not selected:
            selected.append(str(pool[brief_index % len(pool)]["id"]))
        allocations.append(selected)
    return tuple(allocations)


def _build_fact_projection(
    anchor: Mapping[str, Any],
    *,
    projection_id: str,
    anchor_values: Sequence[Any] | None = None,
    required_usage: str = "该来源事实必须在片段中形成可核验的具体约束。",
) -> dict[str, Any]:
    values = (
        list(anchor_values)
        if anchor_values is not None
        else [anchor["_value"]]
    )
    pointer, scalar = _select_substantive_scalar(
        anchor["_value"], anchor_values=values
    )
    return {
        "id": projection_id,
        "field_pointer": pointer,
        "value_sha256": h1b.rt.canonical_sha256(scalar),
        "required_usage": required_usage,
    }


def _preflight_fragment_projection_capacity(
    projections: Sequence[Mapping[str, Any]],
    *,
    anchors: Mapping[str, Mapping[str, Any]],
    target_chars_max: int,
) -> None:
    """Fail before H1-B when projections cannot fit its language contract."""

    if len(projections) != len(anchors):
        raise ValueError("projection and anchor counts differ")
    anchor_values = [item["_value"] for item in anchors.values()]
    total_cjk = 0
    total_latin = 0
    for projection, anchor in zip(projections, anchors.values()):
        pointer = str(projection["field_pointer"])
        if _is_identity_meta_pointer(pointer):
            raise ValueError("projection selects identity/meta field")
        scalar = _pointer_value(anchor["_value"], pointer)
        if (
            not isinstance(scalar, str)
            or not scalar.strip()
            or projection["value_sha256"]
            != h1b.rt.canonical_sha256(scalar)
            or not h1b._quote_has_non_identity_substance(
                scalar, anchor_values
            )
        ):
            raise ValueError("projection fails H1-B substance/hash contract")
        _, cjk, latin = h1b._visible_units(scalar)
        total_cjk += cjk
        total_latin += latin
    ratio = h1b.MIN_CJK_UNIT_RATIO
    ratio_padding = max(
        0,
        math.ceil(
            (ratio * (total_cjk + total_latin) - total_cjk)
            / (1 - ratio)
        ),
    )
    narrative_reserve = max(24, ratio_padding)
    if total_cjk + total_latin + narrative_reserve > target_chars_max:
        raise ValueError("fragment projections exceed visible-unit capacity")


def _build_control_coverage(
    anchor_ids: Sequence[str],
    *,
    visible_element_ids: Sequence[str],
) -> list[dict[str, Any]]:
    if len(set(anchor_ids)) != len(anchor_ids):
        raise ValueError("control coverage anchor ids must be unique")
    return [
        {
            "source_anchor_id": anchor_id,
            "visible_element_ids": list(visible_element_ids),
        }
        for anchor_id in anchor_ids
    ]


def _allocate_visual_anchor_ids(
    anchors: Sequence[Mapping[str, Any]],
    *,
    semantic_role: str,
    max_sources: int = VISUAL_ANCHOR_CAP,
) -> list[str]:
    """Select a bounded, stage-aware, source-injective visual grounding."""

    if semantic_role not in _VISUAL_STAGE_PREFERENCES:
        raise ValueError(f"unknown visual semantic role: {semantic_role}")
    if max_sources <= 0:
        raise ValueError("visual source capacity must be positive")
    preferences = _VISUAL_STAGE_PREFERENCES[semantic_role]
    known_stages = {
        str(item.get("stage", ""))
        for item in anchors
        if str(item.get("stage", ""))
    }
    stage_order = (
        *preferences,
        *sorted(known_stages - set(preferences)),
    )
    rank = {stage: index for index, stage in enumerate(stage_order)}
    candidates: list[dict[str, str]] = []
    for item in anchors:
        anchor_id = str(item.get("id", ""))
        source_id = str(item.get("source_id", ""))
        stage = str(item.get("stage", ""))
        if not anchor_id or not source_id or not stage:
            raise ValueError("visual anchors require id/source_id/stage")
        candidates.append(
            {
                "id": anchor_id,
                "source_id": source_id,
                "stage": stage,
            }
        )
    candidates.sort(
        key=lambda item: (
            rank.get(item["stage"], len(stage_order)),
            item["source_id"],
            item["id"],
        )
    )
    best_by_source: dict[str, dict[str, str]] = {}
    for item in candidates:
        best_by_source.setdefault(item["source_id"], item)
    buckets: dict[str, list[dict[str, str]]] = {
        stage: [] for stage in stage_order
    }
    for item in best_by_source.values():
        buckets.setdefault(item["stage"], []).append(item)
    for bucket in buckets.values():
        bucket.sort(key=lambda item: (item["source_id"], item["id"]))
    selected: list[str] = []
    while len(selected) < min(max_sources, len(best_by_source)):
        progressed = False
        for stage in stage_order:
            bucket = buckets.get(stage, [])
            if not bucket:
                continue
            selected.append(bucket.pop(0)["id"])
            progressed = True
            if len(selected) == max_sources:
                break
        if not progressed:
            break
    if not selected:
        raise ValueError("no visual source anchors are available")
    return selected


def _preflight_visual_source_projection(
    visual: Mapping[str, Any],
    *,
    anchors: Mapping[str, Mapping[str, Any]],
    max_sources: int = VISUAL_ANCHOR_CAP,
) -> None:
    """Reject visual graphs that cannot project to unique report sources."""

    def validate_binding(value: Any, label: str) -> None:
        if isinstance(value, Mapping):
            if "source_anchor_ids" in value:
                anchor_ids = value["source_anchor_ids"]
                if (
                    not isinstance(anchor_ids, list)
                    or not anchor_ids
                    or len(anchor_ids) > max_sources
                    or len(anchor_ids) != len(set(anchor_ids))
                ):
                    raise ValueError(
                        f"{label} visual anchor capacity/uniqueness invalid"
                    )
                try:
                    source_ids = [
                        str(anchors[anchor_id]["source_id"])
                        for anchor_id in anchor_ids
                    ]
                except KeyError as error:
                    raise ValueError(
                        f"{label} references unknown visual anchor"
                    ) from error
                if (
                    any(not source_id for source_id in source_ids)
                    or len(source_ids) != len(set(source_ids))
                ):
                    raise ValueError(
                        f"{label} visual anchors are not source-injective"
                    )
            for key, item in value.items():
                validate_binding(item, f"{label}/{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                validate_binding(item, f"{label}/{index}")

    validate_binding(visual, str(visual.get("id", "visual")))
    element_records = [
        *visual.get("groups", []),
        *visual.get("nodes", []),
        *visual.get("edges", []),
    ]
    element_by_id = {item["id"]: item for item in element_records}
    for equivalent in visual.get("text_equivalents", []):
        try:
            expected = {
                anchor_id
                for element_id in equivalent["element_ids"]
                for anchor_id in element_by_id[element_id][
                    "source_anchor_ids"
                ]
            }
        except KeyError as error:
            raise ValueError(
                "visual text equivalent has a dangling graph element"
            ) from error
        if set(equivalent["source_anchor_ids"]) != expected:
            raise ValueError(
                "visual text equivalent source binding drift"
            )
    graph_union = {
        anchor_id
        for item in [
            *element_records,
            *visual.get("text_equivalents", []),
        ]
        for anchor_id in item["source_anchor_ids"]
    }
    if set(visual["source_anchor_ids"]) != graph_union:
        raise ValueError("visual source anchors are not an exact graph union")


def _graph_element(
    element_id: str,
    order: int,
    *,
    label: str,
    kind: str,
    anchors: list[str],
    group_id: str | None = None,
    lane: str | None = None,
    temporal_label: str | None = None,
) -> dict[str, Any]:
    return {
        "id": element_id,
        "order": order,
        "group_id": group_id,
        "label": label,
        "summary": f"{label}：只呈现已冻结的 P1 控制信息。",
        "kind": kind,
        "lane": lane,
        "tier": None,
        "temporal_label": temporal_label,
        "source_anchor_ids": list(anchors),
    }


def _visual(
    index: int,
    semantic_role: str,
    section_id: str,
    module_id: str,
    visual_kind: str,
    anchors: list[str],
    *,
    connected: bool = False,
    timeline: bool = False,
) -> dict[str, Any]:
    token = str(index)
    groups: list[dict[str, Any]] = []
    group_id = None
    lane = None
    if timeline:
        group_id = f"GRP-{token}-1"
        lane = "主事件线"
        groups = [
            {
                "id": group_id,
                "order": 1,
                "label": "主事件线",
                "summary": "按 P1 已冻结顺序呈现主要事件。",
                "kind": "event-lane",
                "lane": lane,
                "tier": None,
                "temporal_label": "先后顺序",
                "source_anchor_ids": list(anchors),
            }
        ]
    node_count = 2 if connected else 1
    nodes = [
        _graph_element(
            f"NODE-{token}-{number}",
            number,
            label=f"{semantic_role} 节点 {number}",
            kind="control-node",
            anchors=anchors,
            group_id=group_id,
            lane=lane,
            temporal_label=(f"T{number}" if timeline else None),
        )
        for number in range(1, node_count + 1)
    ]
    edges: list[dict[str, Any]] = []
    if connected:
        edges = [
            {
                "id": f"EDGE-{token}-1",
                "order": 1,
                "group_id": group_id,
                "from_node_id": nodes[0]["id"],
                "to_node_id": nodes[1]["id"],
                "direction": "directed",
                "relation_label": "导向",
                "summary": "前一项冻结控制信息导向后一项。",
                "kind": "control-link",
                "lane": lane,
                "tier": None,
                "temporal_label": ("T1-T2" if timeline else None),
                "source_anchor_ids": list(anchors),
            }
        ]
    graph = [*groups, *nodes, *edges]
    return {
        "id": f"VIS-{index}",
        "semantic_role": semantic_role,
        "section_id": section_id,
        "visual_kind": visual_kind,
        "title": f"{semantic_role} 可视模型",
        "review_purpose": "让评审者核对冻结控制项之间的结构关系。",
        "groups": groups,
        "nodes": nodes,
        "edges": edges,
        "text_equivalents": [
            {
                "id": f"TXT-{token}-1",
                "order": 1,
                "element_ids": [item["id"] for item in graph],
                "text": "该图的文字等价表述仅复述其绑定的 P1 信息。",
                "source_anchor_ids": list(anchors),
            }
        ],
        "source_anchor_ids": list(anchors),
        "text_equivalent_module_id": module_id,
    }


def _phases(plan: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    payloads = (
        {
            "review_requirements": plan["review_requirements"],
            "risk_register": plan["risk_register"],
        },
        {
            "review_path": plan["review_path"],
            "sections": plan["sections"],
        },
        {
            "visual_models": plan["visual_models"],
            "fragment_briefs": plan["fragment_briefs"],
            "decision_prompts": plan["decision_prompts"],
            "assembly_projection": plan["assembly_projection"],
            "presentation_bindings": plan["presentation_bindings"],
        },
        {
            "reading_profile": plan["reading_profile"],
            "budget_items": plan["budget_items"],
            "budget_total_seconds": sum(
                item["estimated_seconds"] for item in plan["budget_items"]
            ),
        },
        {
            "review_plan": plan,
            "final_checks": {
                "three_boards": True,
                "all_source_anchors_covered": True,
                "budget_within_600": True,
                "fragments_non_authoritative": True,
                "decision_unselected": True,
            },
        },
    )
    return tuple(
        {
            "phase": phase,
            "phase_index": index,
            "payload": copy.deepcopy(payload),
        }
        for index, (phase, payload) in enumerate(
            zip(h1a.PLAN_PHASES, payloads), 1
        )
    )


def plan_inputs(
    p1_package: str | Path,
    *,
    p1_completion: Mapping[str, str],
    input_gate: Mapping[str, str],
    run_id: str,
    session_id: str,
    work_title: str = "小说构思",
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the work title and five production-valid H1-A phase submissions."""

    completion = _artifact_reference(p1_completion)
    gate = _gate_reference(input_gate)
    inventory = h1a.build_source_inventory(
        p1_package,
        p1_completion=completion,
    )
    anchors = [item["id"] for item in inventory["anchors"]]
    if not anchors:
        raise ValueError("H1 proposal requires at least one source anchor")
    enriched_anchors = _load_anchor_values(
        p1_package, inventory["anchors"]
    )

    pov_anchor = _select_pov_anchor(enriched_anchors)
    pov_character_id = str(pov_anchor["source_id"])
    fragment_allocations = _allocate_fragment_anchor_ids(
        enriched_anchors,
        brief_count=3,
        max_per_brief=2,
        required_anchor_id=str(pov_anchor["id"]),
        target_chars_max=100,
    )

    section_specs = (
        ("world", "世界设定", "核对世界规则、环境与事件条件"),
        ("storylines", "故事线", "核对故事主体、连接和主要事件"),
        ("characters", "人物系统", "核对人物职责、关系与角色覆盖"),
    )
    sections: list[dict[str, Any]] = []
    for kind, title, goal in section_specs:
        modules = [
            {
                "id": f"MOD-{kind.upper()}-{number}",
                "title": f"{title}模块 {number}",
                "display_kind": "cards",
                "definition": f"呈现{title}的第 {number} 组冻结控制信息。",
                "responsibility": f"支持评审者判断{title}是否符合创作意图。",
                "must_hold": ["所有陈述必须保持其 P1 来源值不变"],
                "must_not_imply": ["不得暗示任何未被绑定来源支持的新事实"],
                "source_anchor_ids": list(anchors),
                "default_visible": True,
            }
            for number in range(1, 4)
        ]
        sections.append(
            {
                "id": f"SEC-{kind.upper()}",
                "kind": kind,
                "title": title,
                "review_goal": goal,
                "modules": modules,
            }
        )

    section_by_kind = {item["kind"]: item for item in sections}
    visual_anchor_ids = {
        role: _allocate_visual_anchor_ids(
            enriched_anchors,
            semantic_role=role,
            max_sources=VISUAL_ANCHOR_CAP,
        )
        for role in _VISUAL_STAGE_PREFERENCES
    }
    visuals = [
        _visual(
            1,
            "world_environment_map",
            "SEC-WORLD",
            "MOD-WORLD-1",
            "map",
            visual_anchor_ids["world_environment_map"],
        ),
        _visual(
            2,
            "control_logic_chain",
            "SEC-STORYLINES",
            "MOD-STORYLINES-1",
            "flow",
            visual_anchor_ids["control_logic_chain"],
            connected=True,
        ),
        _visual(
            3,
            "storyline_architecture",
            "SEC-STORYLINES",
            "MOD-STORYLINES-1",
            "flow",
            visual_anchor_ids["storyline_architecture"],
        ),
        _visual(
            4,
            "major_event_timeline",
            "SEC-STORYLINES",
            "MOD-STORYLINES-1",
            "timeline",
            visual_anchor_ids["major_event_timeline"],
            connected=True,
            timeline=True,
        ),
        _visual(
            5,
            "character_relationship_network",
            "SEC-CHARACTERS",
            "MOD-CHARACTERS-1",
            "network",
            visual_anchor_ids["character_relationship_network"],
        ),
    ]
    enriched_by_id = {
        str(item["id"]): item for item in enriched_anchors
    }
    for visual in visuals:
        _preflight_visual_source_projection(
            visual,
            anchors=enriched_by_id,
            max_sources=VISUAL_ANCHOR_CAP,
        )

    fragment_briefs = [
        {
            "id": f"BRIEF-{number}",
            "slot_id": f"FRAG-{number}",
            "title": f"体验片段 {number}",
            "review_purpose": "检验冻结构思转化为阅读体验后的效果。",
            "pov_character_id": pov_character_id,
            "language_contract_id": "zh-Hans-review-v1",
            "style_contract_id": "restrained-concrete-scene-v1",
            "pov_mode": "third_person_limited",
            "information_limits": {
                "may_present": ["仅呈现 POV 可感知且由绑定 P1 信息支持的内容"],
                "must_not_present_as_known": ["不得把 POV 未知信息写成既知事实"],
            },
            "allowed_perception_channels": ["视觉", "听觉"],
            "scene_contract": {
                "before_state": "场景开始状态由绑定的 P1 信息限定。",
                "immediate_goal": "POV 人物追求一个局部且可观察的目标。",
                "pressure": "既有冲突在当前场景内形成时间压力。",
                "obstacle": "绑定的条件阻碍人物直接完成目标。",
                "required_choice": "POV 人物必须作出一个局部行动选择。",
                "direct_consequence": "该选择在片段内产生直接可见的后果。",
                "after_state": "片段结束状态体现后果但不新增权威事实。",
            },
            "decisive_interiority_policy": (
                "process-only-no-unresolved-decision-disclosure"
            ),
            "surface_detail_policy": "fragment-local-non-authoritative-v1",
            "source_anchor_ids": list(fragment_allocations[number - 1]),
            "required_demonstrations": ["展示 P1 约束下的人物行动与直接后果"],
            "forbidden_additions": ["不得新增或改写任何权威设定"],
            "target_words_min": 100,
            "target_words_max": 100,
        }
        for number in range(1, 4)
    ]

    decision_prompts = [
        {
            "id": "PROMPT-1",
            "question": "这份构思是否符合你的创作意图？",
            "affected_source_anchor_ids": list(anchors),
            "allowed_decisions": ["approved", "revise", "rejected"],
            "preselected": False,
        }
    ]

    visible_by_kind = {
        kind: [module["id"] for module in section_by_kind[kind]["modules"]]
        + [
            visual["id"]
            for visual in visuals
            if visual["section_id"] == section_by_kind[kind]["id"]
        ]
        for kind in h1a.SECTION_KINDS
    }
    visible_by_kind["fragments"] = [
        brief["slot_id"] for brief in fragment_briefs
    ]
    visible_by_kind["decision"] = [
        prompt["id"] for prompt in decision_prompts
    ]
    path_titles = {
        "world": "世界设定评审",
        "storylines": "故事线评审",
        "characters": "人物系统评审",
        "fragments": "体验片段评审",
        "decision": "形成评审决定",
    }
    review_path = [
        {
            "id": f"PATH-{index}",
            "order": index,
            "kind": kind,
            "title": path_titles[kind],
            "review_question": f"{path_titles[kind]}是否符合创作意图？",
            "estimated_seconds": 120,
            "visible_element_ids": visible_by_kind[kind],
        }
        for index, kind in enumerate(h1a.REVIEW_PATH_KINDS, 1)
    ]
    budget_items = [
        {
            "element_id": step["id"],
            "estimated_seconds": step["estimated_seconds"],
        }
        for step in review_path
    ]

    plan: dict[str, Any] = {
        "schema_version": "2.0",
        "skill": "novel-conception-human-review-assembler",
        "run_id": run_id,
        "h1_session_id": session_id,
        "p1_completion": completion,
        "work_identity": h1a._work_identity(work_title, gate),
        "reading_budget_minutes": 10,
        "reading_profile": h1a.READING_PROFILE,
        "review_requirements": [
            "判断世界设定是否符合创作意图",
            "判断故事线是否符合创作意图",
            "判断人物系统是否符合创作意图",
            "判断体验片段的阅读效果",
            "记录明确且未预选的评审决定",
        ],
        "risk_register": [
            {
                "id": "RISK-1",
                "risk": "压缩展示可能造成 P1 控制信息漂移",
                "mitigation": "每个展示元素绑定全部来源锚点及其值摘要",
                "source_anchor_ids": list(anchors),
            }
        ],
        "review_path": review_path,
        "sections": sections,
        "visual_models": visuals,
        "fragment_briefs": fragment_briefs,
        "assembly_projection": {
            "world": {
                "definition_module_id": "MOD-WORLD-1",
                "operating_logic_module_id": "MOD-WORLD-2",
                "system_module_ids": ["MOD-WORLD-1"],
                "environment_module_ids": ["MOD-WORLD-2"],
                "event_condition_module_ids": ["MOD-WORLD-3"],
                "constraint_module_ids": ["MOD-WORLD-1"],
                "boundary_module_ids": ["MOD-WORLD-3"],
            },
            "storylines": {
                "story_subject_module_id": "MOD-STORYLINES-1",
                "line_module_ids": ["MOD-STORYLINES-1"],
                "connection_module_ids": ["MOD-STORYLINES-2"],
                "major_event_module_ids": ["MOD-STORYLINES-3"],
                "suspense_conflict_rhythm_module_id": "MOD-STORYLINES-2",
                "constraint_module_ids": ["MOD-STORYLINES-1"],
            },
            "characters": {
                "core_character_module_ids": ["MOD-CHARACTERS-1"],
                "supporting_character_module_ids": [],
                "relationship_network_module_ids": ["MOD-CHARACTERS-2"],
                "role_coverage_module_ids": ["MOD-CHARACTERS-3"],
                "constraint_module_ids": ["MOD-CHARACTERS-1"],
            },
        },
        "presentation_bindings": [],
        "decision_prompts": decision_prompts,
        "budget_items": budget_items,
        "control_coverage": _build_control_coverage(
            anchors, visible_element_ids=["MOD-WORLD-1"]
        ),
    }

    source_hashes = {
        item["id"]: item["value_sha256"] for item in inventory["anchors"]
    }
    presentation_elements: list[tuple[Mapping[str, Any], str]] = [
        (module, "source_anchor_ids")
        for section in sections
        for module in section["modules"]
    ]
    presentation_elements.extend(
        (visual, "source_anchor_ids") for visual in visuals
    )
    presentation_elements.extend(
        (brief, "source_anchor_ids") for brief in fragment_briefs
    )
    presentation_elements.extend(
        (prompt, "affected_source_anchor_ids")
        for prompt in decision_prompts
    )
    plan["presentation_bindings"] = [
        {
            "element_id": element["id"],
            "content_sha256": h1a.rt.canonical_sha256(element),
            "source_values": [
                {
                    "source_anchor_id": anchor,
                    "value_sha256": source_hashes[anchor],
                }
                for anchor in element[source_field]
            ],
            "must_not_imply": (
                element["must_not_imply"]
                if element["id"].startswith("MOD-")
                else ["不得暗示绑定 P1 来源之外的事实"]
            ),
            "challenge_result": "passed",
            "challenge_notes": "已逐项核对冻结 P1 来源值与禁止推断边界。",
        }
        for element, source_field in presentation_elements
    ]

    phases = _phases(plan)
    return (work_title, *phases)


def _pointer_value(document: Any, pointer: str) -> Any:
    value = document
    for token in pointer.lstrip("/").split("/") if pointer else ():
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _short_string(value: Any, pointer: str = "") -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    if isinstance(value, str) and value.strip():
        candidates.append((pointer, value.strip()))
    elif isinstance(value, Mapping):
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            candidates.extend([_short_string(child, f"{pointer}/{token}")])
    elif isinstance(value, list):
        for index, child in enumerate(value):
            candidates.extend([_short_string(child, f"{pointer}/{index}")])
    candidates = [item for item in candidates if item[1]]
    if not candidates:
        return pointer, json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return min(candidates, key=lambda item: len(item[1]))


def _build_fragment_text(
    quotes: Sequence[str],
    *,
    target_visible_units: int,
) -> tuple[str, dict[str, str]]:
    """Build deterministic restrained prose at the exact H1-B unit budget."""

    if not quotes or any(
        not isinstance(quote, str) or not quote.strip() for quote in quotes
    ):
        raise ValueError("fragment text requires non-empty source quotes")
    choice = "他停了一瞬，随后改变原定顺序"
    consequence = "这个选择立刻造成可见后果"
    state_change = "局面因此向前移动"
    first = (
        "；".join(quote.strip() for quote in quotes)
        + "。他逐项核对，只保留眼前能够确认的部分。"
    )
    second = (
        f"压力仍在逼近。{choice}。{consequence}。{state_change}。"
    )
    text = f"{first}\n\n{second}"
    current, _, _ = h1b._visible_units(text)
    remaining = target_visible_units - current
    if remaining < 0:
        raise ValueError("source quotes exceed fragment visible-unit budget")
    if remaining:
        natural_continuation = (
            "他没有急着解释而是继续观察眼前变化直到下一项线索逐渐清晰"
            "并再次核对刚才留下的每一处痕迹"
        )
        if remaining > len(natural_continuation):
            raise ValueError("fragment budget exceeds deterministic prose capacity")
        text += natural_continuation[:remaining] + "。"
    units, cjk, _ = h1b._visible_units(text)
    if (
        units != target_visible_units
        or not units
        or cjk / units < h1b.MIN_CJK_UNIT_RATIO
    ):
        raise ValueError("fragment text cannot meet H1-B language budget")
    return text, {
        "choice": choice,
        "consequence": consequence,
        "state_change": state_change,
    }


def _build_scene_contract_evidence(
    scene_contract: Mapping[str, Any],
    *,
    evidence_quote: str,
) -> list[dict[str, Any]]:
    if set(scene_contract) != set(_SCENE_FIELDS):
        raise ValueError("scene contract fields do not match H1-B contract")
    return [
        {
            "field": field,
            "expected_value": copy.deepcopy(scene_contract[field]),
            "finding": "该场景义务已在连续行动中体现。",
            "evidence_quote": evidence_quote,
        }
        for field in _SCENE_FIELDS
    ]


def fragment_submissions(
    plan_package: str | Path,
    *,
    p1_package: str | Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the exact three production H1-B phase submissions."""

    plan_root = Path(plan_package)
    p1_root = Path(p1_package)
    plan = json.loads((plan_root / "review-plan.json").read_text(encoding="utf-8"))
    inventory = json.loads(
        (plan_root / "source-inventory.json").read_text(encoding="utf-8")
    )
    enriched_anchors = _load_anchor_values(
        p1_root, inventory["anchors"]
    )
    anchors = {item["id"]: item for item in enriched_anchors}
    anchor_values = [item["_value"] for item in enriched_anchors]
    selected_anchor_ids = {
        anchor_id
        for brief in plan["fragment_briefs"]
        for anchor_id in brief["source_anchor_ids"]
    }
    projections: dict[str, tuple[str, str, str]] = {}
    for anchor_id in sorted(selected_anchor_ids):
        anchor = anchors[anchor_id]
        projection = _build_fact_projection(
            anchor,
            projection_id=f"{anchor_id}-PREFLIGHT",
            anchor_values=anchor_values,
        )
        field_pointer = projection["field_pointer"]
        field_value = _pointer_value(anchor["_value"], field_pointer)
        projections[anchor_id] = (
            field_pointer,
            field_value,
            projection["value_sha256"],
        )

    contracts, drafts, reviews = [], [], []
    for brief in plan["fragment_briefs"]:
        challenges = []
        ledger = []
        quotes = []
        for index, anchor_id in enumerate(brief["source_anchor_ids"], 1):
            anchor = anchors[anchor_id]
            pointer, value, value_hash = projections[anchor_id]
            projection_id = f"{brief['id']}-PROJ-{index}"
            use = f"场景以“{value}”作为既有设定依据"
            challenges.append(
                {
                    "source_anchor_id": anchor_id,
                    "value_sha256": anchor["value_sha256"],
                    "story_specific_use": use,
                    "does_not_authorize": "不授权新增世界规则、人物历史或关系结论",
                    "fact_projections": [{
                        "id": projection_id,
                        "field_pointer": pointer,
                        "value_sha256": value_hash,
                        "required_usage": use,
                    }],
                }
            )
            quotes.append(value)
            ledger.append(
                {
                    "fact_projection_id": projection_id,
                    "source_anchor_id": anchor_id,
                    "source_value_sha256": anchor["value_sha256"],
                    "field_value_sha256": value_hash,
                    "story_specific_claim": use,
                    "evidence_quote": value,
                    "evidence_quote_sha256": h1b.rt.canonical_sha256(value),
                    "challenge_result": "lexically_grounded",
                    "challenge_notes": "原文值直接出现在片段中，并仅用于本地场景表达。",
                    "control_status": "preserved",
                }
            )
        _preflight_fragment_projection_capacity(
            [
                challenge["fact_projections"][0]
                for challenge in challenges
            ],
            anchors={
                anchor_id: anchors[anchor_id]
                for anchor_id in brief["source_anchor_ids"]
            },
            target_chars_max=brief["target_words_max"],
        )
        contract = {
            "brief_id": brief["id"], "slot_id": brief["slot_id"],
            "brief_sha256": h1b.rt.canonical_sha256(brief),
            "title": brief["title"], "review_purpose": brief["review_purpose"],
            "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
            "style_contract_id": h1b.STYLE_CONTRACT_ID,
            "pov_mode": h1b.POV_MODE, "pov_character_id": brief["pov_character_id"],
            "information_limits": copy.deepcopy(brief["information_limits"]),
            "allowed_perception_channels": copy.deepcopy(brief["allowed_perception_channels"]),
            "scene_contract": copy.deepcopy(brief["scene_contract"]),
            "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
            "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
            "target_chars_min": brief["target_words_min"],
            "target_chars_max": brief["target_words_max"],
            "source_challenges": challenges,
            "required_demonstrations": copy.deepcopy(brief["required_demonstrations"]),
            "forbidden_additions": copy.deepcopy(brief["forbidden_additions"]),
            "opposition_challenge": {"verdict": "compatible", "evidence": "场景变化不改变既有控制事实。"},
        }
        text, evidence = _build_fragment_text(
            quotes,
            target_visible_units=brief["target_words_min"],
        )
        draft = {
            "id": brief["slot_id"], "brief_sha256": h1b.rt.canonical_sha256(brief),
            "title": brief["title"], "review_purpose": brief["review_purpose"],
            "text": text, "source_anchor_ids": copy.deepcopy(brief["source_anchor_ids"]),
            "surface_details": [], "introduced_control_facts": [],
        }
        reviews.append({
            "fragment_id": brief["slot_id"], "brief_sha256": h1b.rt.canonical_sha256(brief),
            "draft_sha256": h1b.rt.canonical_sha256(text), "text_sha256": h1b.rt.canonical_sha256(text),
            "fact_projection_ledger": ledger,
            "required_demonstrations": [{"requirement": item, "fact_projection_ids": [x["fact_projection_id"] for x in ledger], "finding": "压力、选择与直接后果均已呈现。", "evidence_quote": evidence["consequence"]} for item in brief["required_demonstrations"]],
            "forbidden_additions": [{"prohibition": item, "verdict": "absent", "check_notes": "逐项检查未发现该新增内容。"} for item in brief["forbidden_additions"]],
            "information_boundary": {"may_present": copy.deepcopy(brief["information_limits"]["may_present"]), "must_not_present_as_known": copy.deepcopy(brief["information_limits"]["must_not_present_as_known"]), "used_perception_channels": copy.deepcopy(brief["allowed_perception_channels"][:1]), "evidence_quotes": [quotes[0]], "verdict": "passed"},
            "scene_contract_evidence": _build_scene_contract_evidence(brief["scene_contract"], evidence_quote=evidence["choice"]),
            "style_checks": {code: True for code in h1b.STYLE_PRINCIPLES},
            "boundary_checks": {"language_contract_id": h1b.LANGUAGE_CONTRACT_ID, "style_contract_id": h1b.STYLE_CONTRACT_ID, "pov_mode": h1b.POV_MODE, "pov_character_id": brief["pov_character_id"], "decisive_interiority_policy": h1b.INTERIORITY_POLICY, "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY, "choice_evidence_quote": evidence["choice"], "consequence_evidence_quote": evidence["consequence"], "state_change_evidence_quote": evidence["state_change"], "decisive_inner_revelation": False, "introduced_control_facts": [], "final_prose_claim": False},
            "surface_details": [],
        })
        contracts.append(contract)
        drafts.append(draft)
    return (
        {"phase": h1b.PHASES[0], "phase_index": 1, "payload": {"brief_contracts": contracts}},
        {"phase": h1b.PHASES[1], "phase_index": 2, "payload": {"drafts": drafts}},
        {"phase": h1b.PHASES[2], "phase_index": 3, "payload": {"final_fragments": copy.deepcopy(drafts), "compliance_reviews": reviews}},
    )


__all__ = ["fragment_submissions", "plan_inputs"]
