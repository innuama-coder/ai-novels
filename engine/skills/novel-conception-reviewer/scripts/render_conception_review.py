#!/usr/bin/env python3
"""Deterministically render the R1 review package from review-data.json."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any


AREAS = (
    ("intent", "意图与承诺"),
    ("subject", "主体职责"),
    ("world", "世界运行边界"),
    ("character", "人物选择逻辑"),
    ("causality", "因果与结局"),
    ("narrative", "叙述与信息"),
)
CROSS_CHECK_LABELS = {
    "autonomous_value": "自主增量价值",
    "gap_closure": "开发缺口闭合",
    "promise_scope": "承诺与范围",
    "world_causality": "世界与因果",
    "character_agency": "人物能动性",
    "opposition_response": "对抗与反制",
    "choice_costs": "选择与成本",
    "easy_solution": "便捷解法压力测试",
    "causal_closure": "因果闭环",
    "narrative_information": "叙述信息",
    "thematic_testing": "主题行动检验",
    "open_boundaries": "开放边界",
    "development_usability": "开发可用性",
}
TASK_LABELS = {
    "promise": "故事承诺",
    "autonomous_value": "自主增量价值",
    "causal_chain": "主因果链",
    "unit_contract": "单元契约",
    "freedom_boundary": "开发自由边界",
    "drift_detection": "偏航识别",
    "easy_solution": "便捷解法攻击",
    "scene_plan": "场景规划可行性",
}
GENERATED_OUTPUTS = {
    "novel-design-brief.md",
    "conception-review.md",
    "independent-handoff.json",
    "return-package.json",
    "next-run-state.json",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} root is not an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def resolve_relative(base: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError(f"{label} must use a relative path")
    return (base / candidate).resolve()


def _text(value: Any, default: str = "—") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().replace("\r", " ").replace("\n", " ")
    return default


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _ids(value: Any) -> str:
    values = _strings(value)
    return ", ".join(f"`{item}`" for item in values) if values else "—"


def _relative_reference(base: Path, target: Path) -> dict[str, str]:
    relative = Path(os.path.relpath(target, base)).as_posix()
    return {"path": relative, "sha256": sha256(target)}


def rebase_reference(
    source_base: Path,
    target_base: Path,
    reference: Any,
    label: str,
) -> dict[str, str]:
    if (
        not isinstance(reference, dict)
        or not isinstance(reference.get("path"), str)
        or not isinstance(reference.get("sha256"), str)
    ):
        raise ValueError(f"{label} is not a hash-bound reference")
    target = resolve_relative(source_base, reference["path"], label)
    if not target.is_file() or sha256(target) != reference["sha256"].lower():
        raise ValueError(f"{label} is missing or has changed")
    return _relative_reference(target_base, target)


def locate_d1(
    package_dir: Path, review_data: dict[str, Any]
) -> tuple[Path, dict[str, Any], Path, dict[str, Any], dict[str, Any]]:
    gate = review_data.get("input_gate")
    if not isinstance(gate, dict):
        raise ValueError("review-data lacks input_gate")
    reference = gate.get("d1_completion")
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        raise ValueError("input_gate lacks d1_completion")
    completion_path = resolve_relative(
        package_dir, reference["path"], "D1 completion reference"
    )
    completion = load_json(completion_path)
    artifact = completion.get("design_artifact")
    if not isinstance(artifact, str) or not artifact:
        raise ValueError("D1 completion lacks design_artifact")
    manifest_path = resolve_relative(
        completion_path.parent, artifact, "D1 design_artifact"
    )
    manifest = load_json(manifest_path)
    map_data = load_json(manifest_path.parent / "map-data.json")
    return completion_path, completion, manifest_path, manifest, map_data


def build_independent_handoff(
    package_dir: Path,
    review_data: dict[str, Any],
    manifest_path: Path,
) -> dict[str, Any]:
    reviewer = (
        review_data.get("reviewer")
        if isinstance(review_data.get("reviewer"), dict)
        else {}
    )
    return {
        "schema_version": "1.0",
        "harness": "novel-conception-interview",
        "run_id": review_data.get("run_id"),
        "stage": "R1",
        "verdict": "pass",
        "reviewer_id": reviewer.get("id"),
        "reviewer_role": reviewer.get("role"),
        "assurance": reviewer.get("assurance"),
        "evidence_scope": reviewer.get("evidence_scope"),
        "method": reviewer.get("method"),
        "d1_package": _relative_reference(package_dir, manifest_path),
        "subject_ids": review_data.get("subject_ids", []),
        "world_model_reviews": review_data.get("world_model_reviews", []),
        "major_event_reviews": review_data.get("major_event_reviews", []),
        "storyline_reviews": review_data.get("storyline_reviews", []),
        "character_demand_reviews": review_data.get(
            "character_demand_reviews", []
        ),
        "character_profile_reviews": review_data.get(
            "character_profile_reviews", []
        ),
        "relationship_edge_reviews": review_data.get(
            "relationship_edge_reviews", []
        ),
        "relationship_network_reviews": review_data.get(
            "relationship_network_reviews", []
        ),
        "development_gap_reviews": review_data.get(
            "development_gap_reviews", []
        ),
        "design_decision_reviews": review_data.get(
            "design_decision_reviews", []
        ),
        "derivation_reviews": review_data.get("derivation_reviews", []),
        "tasks": review_data.get("tasks", []),
    }


def build_return_outputs(
    package_dir: Path, review_data: dict[str, Any]
) -> dict[str, str]:
    request = review_data.get("return_request")
    if not isinstance(request, dict):
        raise ValueError("blocked review lacks return_request")
    finding_ids = request.get("finding_ids")
    findings = {
        item.get("id"): item
        for item in review_data.get("findings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if not isinstance(finding_ids, list) or not finding_ids:
        raise ValueError("return_request lacks finding_ids")
    selected = [findings.get(item) for item in finding_ids]
    if any(not isinstance(item, dict) for item in selected):
        raise ValueError("return_request cites an unknown finding")
    evidence = sorted(
        {
            evidence_id
            for item in selected
            for evidence_id in _strings(item.get("evidence_ids"))
        }
    )
    defects = [_text(item.get("problem")) for item in selected]
    return_data = {
        "harness": "novel-conception-interview",
        "run_id": review_data.get("run_id"),
        "status": "active",
        "origin_stage": "R1",
        "target_stage": request.get("target_stage"),
        "defect": "；".join(defects),
        "evidence": evidence,
        "requested_decision": request.get("requested_decision"),
        "affected_artifacts": request.get("affected_artifacts"),
    }
    return_content = (
        json.dumps(return_data, ensure_ascii=False, indent=2) + "\n"
    )

    gate = review_data.get("input_gate")
    if not isinstance(gate, dict):
        raise ValueError("review-data lacks input_gate")
    state_reference = gate.get("run_state")
    if (
        not isinstance(state_reference, dict)
        or not isinstance(state_reference.get("path"), str)
    ):
        raise ValueError("input_gate lacks run_state")
    current_state_path = resolve_relative(
        package_dir, state_reference["path"], "run-state reference"
    )
    next_state = copy.deepcopy(load_json(current_state_path))
    current = next_state.get("current_interview_completions")
    if isinstance(current, dict):
        next_state["current_interview_completions"] = {
            stage: rebase_reference(
                current_state_path.parent,
                package_dir,
                reference,
                f"current {stage} completion",
            )
            for stage, reference in current.items()
        }
    resolved = next_state.get("resolved_returns")
    if isinstance(resolved, list):
        rebased_resolved = []
        for index, item in enumerate(resolved):
            if not isinstance(item, dict):
                raise ValueError(
                    f"resolved_returns[{index}] is not an object"
                )
            rebased_item = copy.deepcopy(item)
            rebased_item["return"] = rebase_reference(
                current_state_path.parent,
                package_dir,
                item.get("return"),
                f"resolved_returns[{index}].return",
            )
            rebased_item["target_completion"] = rebase_reference(
                current_state_path.parent,
                package_dir,
                item.get("target_completion"),
                f"resolved_returns[{index}].target_completion",
            )
            rebased_resolved.append(rebased_item)
        next_state["resolved_returns"] = rebased_resolved
    next_state["active_return"] = {
        "path": "return-package.json",
        "sha256": sha256_text(return_content),
    }
    next_state_content = (
        json.dumps(next_state, ensure_ascii=False, indent=2) + "\n"
    )
    return {
        "return-package.json": return_content,
        "next-run-state.json": next_state_content,
    }


def render_canonical_characters(
    demands: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[str]:
    """Render the canonical character graph without recreating derived layers."""
    lines: list[str] = ["### 角色需求与建档处置", ""]
    for demand in demands:
        lines.extend(
            [
                f"- `{_text(demand.get('id'))}` "
                f"[{_text(demand.get('category'))} / "
                f"{_text(demand.get('criticality'))}]："
                f"触发：{_text(demand.get('trigger'))}；"
                f"故事职责：{_text(demand.get('story_function'))}；"
                f"遗漏后果：{_text(demand.get('omission_consequence'))}；"
                f"处置：{_text(demand.get('resolution'))} → "
                f"`{_text(demand.get('profile_id'))}`；"
                f"命名要求：{_text(demand.get('naming_requirement'))}",
            ]
        )
    lines.extend(["", "### 已建档人物", ""])
    for character in profiles:
        lines.extend(
            [
                f"### `{_text(character.get('id'))}` {_text(character.get('name'))}",
                "",
                f"- 重要度：`{_text(character.get('importance'))}`；命名状态："
                f"`{_text(character.get('naming_status'))}`",
                f"- 角色位置：{_text(character.get('role'))}",
                f"- 故事职责：{_text(character.get('story_function'))}",
                f"- 起点状态：{_text(character.get('start_state'))}",
                f"- 外部目标：{_text(character.get('surface_goal'))}",
                f"- 深层需要：{_text(character.get('deeper_need'))}",
                f"- 恐惧或回避：{_text(character.get('fear_or_avoidance'))}",
                f"- 价值与边界：{'；'.join(_strings(character.get('values_and_boundaries'))) or '—'}",
                f"- 信息限制：{'；'.join(_strings(character.get('information_limits'))) or '—'}",
                f"- 压力行为：{'；'.join(_strings(character.get('pressure_behavior'))) or '—'}",
                f"- 能动选择：{'；'.join(_strings(character.get('agency_choices'))) or '—'}",
                f"- 结局状态：{_text(character.get('end_state'))}",
                f"- 不变量：{'；'.join(_strings(character.get('invariants'))) or '—'}",
                f"- 所属故事线：{_ids(character.get('storyline_ids'))}",
                f"- 承载单元：{_ids(character.get('unit_ids'))}",
                f"- 下游自由：{_text(character.get('downstream_freedom'))}",
                "",
                "#### 人物变化阶段",
                "",
            ]
        )
        for stage in character.get("arc_stages", []):
            if not isinstance(stage, dict):
                continue
            lines.append(
                f"- **{_text(stage.get('label'))}**（{_ids(stage.get('unit_ids'))}）："
                f"{_text(stage.get('state'))}；压力：{_text(stage.get('pressure'))}；"
                f"选择：{_text(stage.get('choice'))}；变化：{_text(stage.get('change'))}"
            )
        lines.append("")
    lines.extend(["### 全局人物关系边", ""])
    for relation in relationships:
        lines.append(
            f"- `{_text(relation.get('id'))}` "
            f"`{_text(relation.get('source_id'))}` ↔ "
            f"`{_text(relation.get('target_id'))}`："
            f"{_text(relation.get('relationship_type'))}；"
            f"共同历史：{_text(relation.get('shared_history'))}；"
            f"立场：{_text(relation.get('alignment'))}；"
            f"冲突：{_text(relation.get('conflict'))}；"
            f"制衡：{_text(relation.get('leverage'))}；"
            f"信息差：{_text(relation.get('information_asymmetry'))}；"
            f"变化：{_text(relation.get('change'))}；"
            f"故事线：{_ids(relation.get('storyline_ids'))}；"
            f"单元：{_ids(relation.get('unit_ids'))}"
        )
    lines.append("")
    return lines


def render_conception_sections(map_data: dict[str, Any]) -> list[str]:
    conception = (
        map_data.get("conception")
        if isinstance(map_data.get("conception"), dict)
        else {}
    )
    world = conception.get("world") if isinstance(conception.get("world"), dict) else {}
    story = conception.get("story") if isinstance(conception.get("story"), dict) else {}
    character_model = (
        conception.get("characters")
        if isinstance(conception.get("characters"), dict)
        else {}
    )
    characters = [
        item
        for item in character_model.get("profiles", [])
        if isinstance(item, dict)
    ]
    relationships = [
        item
        for item in character_model.get("relationships", [])
        if isinstance(item, dict)
    ]
    demands = [
        item
        for item in character_model.get("demand_register", [])
        if isinstance(item, dict)
    ]
    lines = [
        "## 1. 小说世界设定",
        "",
        f"- 世界定义：{_text(world.get('definition'))}",
        f"- 对故事的作用：{_text(world.get('story_function'))}",
        f"- 时空范围：{_text(world.get('time_space_scope'))}",
        f"- 运行逻辑：{'；'.join(_strings(world.get('operating_logic'))) or '—'}",
        f"- 权力与资源：{'；'.join(_strings(world.get('power_and_resources'))) or '—'}",
        f"- 人物可采取的行动：{'；'.join(_strings(world.get('action_permissions'))) or '—'}",
        f"- 不可突破的限制：{'；'.join(_strings(world.get('hard_constraints'))) or '—'}",
        f"- 持续压力：{'；'.join(_strings(world.get('pressure_sources'))) or '—'}",
        f"- 代价与后果：{'；'.join(_strings(world.get('costs_and_consequences'))) or '—'}",
        f"- 结局后的世界：{_text(world.get('end_state'))}",
        f"- 本部不展开：{'；'.join(_strings(world.get('scope_exclusions'))) or '—'}",
        f"- 来源控制点：{_ids(world.get('source_controls'))}",
        "",
        "### 世界信息八域",
        "",
    ]
    for facet in world.get("facets", []):
        if not isinstance(facet, dict):
            continue
        lines.extend(
            [
                f"- **{_text(facet.get('domain'))}**（`{_text(facet.get('id'))}` / "
                f"{_text(facet.get('status'))}）：{_text(facet.get('definition'))}；"
                f"故事关联：{_text(facet.get('story_relevance'))}",
            ]
        )
    lines.extend(["", "### 世界运行系统", ""])
    for system in world.get("systems", []):
        if not isinstance(system, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(system.get('id'))}` {_text(system.get('name'))}",
                "",
                f"- 定义：{_text(system.get('definition'))}",
                f"- 行动者与资源：{'；'.join(_strings(system.get('actors') + system.get('resources', []))) if isinstance(system.get('actors'), list) else '—'}",
                f"- 规则与权限：{'；'.join(_strings(system.get('rules') + system.get('permissions', []))) if isinstance(system.get('rules'), list) else '—'}",
                f"- 代价与限制：{'；'.join(_strings(system.get('costs') + system.get('limits', []))) if isinstance(system.get('costs'), list) else '—'}",
                f"- 失败方式：{'；'.join(_strings(system.get('failure_modes'))) or '—'}",
                f"- 故事作用：{'；'.join(_strings(system.get('story_effects'))) or '—'}",
                f"- 故事内变化：{'；'.join(_strings(system.get('state_changes'))) or '—'}",
                "",
            ]
        )
    lines.extend(["", "### 主要环境定义", ""])
    for environment in world.get("environments", []):
        if not isinstance(environment, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(environment.get('id'))}` "
                f"{_text(environment.get('name'))}",
                "",
                f"- 类型／范围：{_text(environment.get('environment_type'))}；"
                f"{_text(environment.get('scope'))}",
                f"- 定义：{_text(environment.get('definition'))}",
                f"- 鲜明特征：{'；'.join(_strings(environment.get('distinctive_features'))) or '—'}",
                f"- 基本要素：{'；'.join(_strings(environment.get('basic_elements'))) or '—'}",
                f"- 感知条件：{'；'.join(_strings(environment.get('sensory_conditions'))) or '—'}",
                f"- 进入者与权限：{'；'.join(_strings(environment.get('occupants_and_access'))) or '—'}",
                f"- 资源与设施：{'；'.join(_strings(environment.get('resources_and_infrastructure'))) or '—'}",
                f"- 可行动作与规则：{'；'.join(_strings(environment.get('rules_and_affordances'))) or '—'}",
                f"- 危险与压力：{'；'.join(_strings(environment.get('hazards_and_pressures'))) or '—'}",
                f"- 故事功能：{'；'.join(_strings(environment.get('story_functions'))) or '—'}",
                f"- 故事内变化：{'；'.join(_strings(environment.get('state_changes'))) or '—'}",
                f"- 内部边界：{'；'.join(_strings(environment.get('topology', {}).get('boundaries'))) if isinstance(environment.get('topology'), dict) else '—'}",
                f"- 故事线／单元：{_ids(environment.get('storyline_ids'))}；"
                f"{_ids(environment.get('unit_ids'))}",
                "",
                "**功能区与连接**",
                "",
            ]
        )
        topology = environment.get("topology", {})
        if isinstance(topology, dict):
            for zone in topology.get("zones", []):
                if not isinstance(zone, dict):
                    continue
                lines.append(
                    f"- `{_text(zone.get('id'))}` "
                    f"**{_text(zone.get('name'))}**："
                    f"{_text(zone.get('function'))}；"
                    f"状态：{_text(zone.get('state'))}；"
                    f"人物：{_ids(zone.get('occupant_ids'))}；"
                    f"资源：{'；'.join(_strings(zone.get('resources'))) or '—'}"
                )
            for connection in topology.get("connections", []):
                if not isinstance(connection, dict):
                    continue
                lines.append(
                    f"- `{_text(connection.get('from_zone'))}` → "
                    f"`{_text(connection.get('to_zone'))}`："
                    f"{_text(connection.get('channel'))}；"
                    f"准入：{_text(connection.get('access_condition'))}；"
                    f"阻断后果：{_text(connection.get('blockage_effect'))}"
                )
        lines.extend(["", "**关键事件如何在此发生**", ""])
        for event in environment.get("event_hosting", []):
            if not isinstance(event, dict):
                continue
            lines.extend(
                [
                    f"- `{_text(event.get('unit_id'))}` @ "
                    f"{_ids(event.get('zone_ids'))}："
                    f"{_text(event.get('event_function'))}",
                    f"  - 人物：{_ids(event.get('active_character_ids'))}",
                    f"  - 状态：{_text(event.get('entry_state'))} → "
                    f"{_text(event.get('exit_state'))}",
                    f"  - 可做／不可做："
                    f"{'；'.join(_strings(event.get('available_actions'))) or '—'}"
                    "／"
                    f"{'；'.join(_strings(event.get('blocked_actions'))) or '—'}",
                    f"  - 压力：{_text(event.get('pressure'))}",
                ]
            )
        lines.append("")
    lines.extend(["### 逐事件环境需求", ""])
    for requirement in world.get("event_environment_requirements", []):
        if not isinstance(requirement, dict):
            continue
        lines.extend(
            [
                f"- `{_text(requirement.get('major_event_id'))}` → "
                f"`{_text(requirement.get('primary_environment_id'))}`"
                f"（次级：{_ids(requirement.get('secondary_environment_ids'))}）",
                f"  - 能力／功能区："
                f"{'；'.join(_strings(requirement.get('required_capabilities'))) or '—'}"
                f"；{_ids(requirement.get('required_zone_ids'))}",
                f"  - 资源／权限／信息通道："
                f"{'；'.join(_strings(requirement.get('required_resources'))) or '—'}"
                "；"
                f"{'；'.join(_strings(requirement.get('required_permissions'))) or '—'}"
                "；"
                f"{'；'.join(_strings(requirement.get('required_information_channels'))) or '—'}",
                f"  - 风险／转场："
                f"{'；'.join(_strings(requirement.get('hazards_and_constraints'))) or '—'}"
                "；"
                f"{'；'.join(_strings(requirement.get('transition_requirements'))) or '—'}",
                f"  - 充分性：{_text(requirement.get('adequacy_rationale'))}",
            ]
        )
    lines.append("")
    lines.extend(
        [
        "## 2. 小说故事线设定",
        "",
        f"- 核心承诺：{_text(story.get('core_promise'))}",
        f"- 这是谁的故事：{_text(story.get('whose_story'))}",
        f"- 中心冲突：{_text(story.get('central_conflict'))}",
        f"- 核心问题：{_text(story.get('dramatic_question'))}",
        f"- 风险与代价：{'；'.join(_strings(story.get('stakes'))) or '—'}",
        f"- 开端状态：{_text(story.get('start_state'))}",
        f"- 触发事件：{_text(story.get('inciting_incident'))}",
        f"- 升级逻辑：{'；'.join(_strings(story.get('escalation_logic'))) or '—'}",
        f"- 高潮：{_text(story.get('climax'))}",
        f"- 结局：{_text(story.get('resolution'))}",
        f"- 有意开放：{'；'.join(_strings(story.get('open_threads'))) or '—'}",
        f"- 本部不展开：{'；'.join(_strings(story.get('scope_exclusions'))) or '—'}",
        f"- 来源控制点：{_ids(story.get('source_controls'))}",
        "",
        "### 主要事件",
        "",
        ]
    )
    for event in story.get("major_events", []):
        if not isinstance(event, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(event.get('id'))}` {_text(event.get('title'))}",
                "",
                f"- 角色／定义：{_text(event.get('event_role'))}；"
                f"{_text(event.get('definition'))}",
                f"- 故事线／单元：{_ids(event.get('storyline_ids'))}；"
                f"{_ids(event.get('unit_ids'))}",
                f"- 环境／人物：{_ids(event.get('environment_ids'))}；"
                f"{_ids(event.get('participant_ids'))}",
                f"- 前提：{'；'.join(_strings(event.get('preconditions'))) or '—'}",
                f"- 行动／对抗：{_text(event.get('initiating_action'))}；"
                f"{_text(event.get('opposition_or_complication'))}",
                f"- 决定性变化／结果：{_text(event.get('decisive_change'))}；"
                f"{_text(event.get('immediate_outcome'))}",
                f"- 状态变化：{_text(event.get('state_before'))} → "
                f"{_text(event.get('state_after'))}",
                f"- 下一压力：{_text(event.get('next_pressure'))}",
                f"- 信息变化："
                f"{'；'.join(_strings(event.get('information_effects'))) or '—'}",
                f"- 因果前驱：{_ids(event.get('causal_predecessor_ids'))}",
                "",
            ]
        )
    lines.extend(
        [
        "### 故事线需求与架构",
        "",
        ]
    )
    for demand in story.get("storyline_demands", []):
        if not isinstance(demand, dict):
            continue
        lines.append(
            f"- `{_text(demand.get('id'))}` "
            f"**{_text(demand.get('need'))}**："
            f"{_text(demand.get('story_function'))}；"
            f"遗漏后果：{_text(demand.get('omission_consequence'))}；"
            f"处置：{_text(demand.get('disposition'))} → "
            f"{_ids(demand.get('storyline_ids'))}"
        )
    architecture = story.get("storyline_architecture", {})
    lines.extend(
        [
            "",
            f"- 入口：{_ids(architecture.get('entry_storyline_ids'))}",
            f"- 主干：`{_text(architecture.get('main_storyline_id'))}`",
            f"- 终点：{_ids(architecture.get('terminal_storyline_ids'))}",
            f"- 覆盖说明：{_text(architecture.get('coverage_rationale'))}",
            "",
            "**连接点**",
            "",
        ]
    )
    for connection in architecture.get("connection_points", []):
        if not isinstance(connection, dict):
            continue
        lines.append(
            f"- `{_text(connection.get('id'))}` "
            f"[{_text(connection.get('connection_type'))}] "
            f"{_ids(connection.get('incoming_storyline_ids'))} → "
            f"{_ids(connection.get('outgoing_storyline_ids'))} @ "
            f"`{_text(connection.get('event_id'))}`；"
            f"{_text(connection.get('transferred_obligations'))}；"
            f"{_text(connection.get('resulting_state'))}"
        )
    lines.extend(["", "### 全部故事线", ""])
    for storyline in story.get("storylines", []):
        if not isinstance(storyline, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(storyline.get('id'))}` {_text(storyline.get('title'))}",
                "",
                f"- 类型／功能：{_text(storyline.get('type'))}；{_text(storyline.get('function'))}",
                f"- 承载者：{_ids(storyline.get('protagonists'))}",
                f"- 核心问题：{_text(storyline.get('central_question'))}",
                f"- 起点／驱动：{_text(storyline.get('start_state'))}；{_text(storyline.get('driver'))}",
                f"- 升级：{'；'.join(_strings(storyline.get('escalation'))) or '—'}",
                f"- 主要事件：{_ids(storyline.get('major_event_ids'))}",
                f"- 结局：{_text(storyline.get('end_state'))}；{_text(storyline.get('resolution'))}",
                f"- 承载单元：{_ids(storyline.get('unit_ids'))}",
                "",
            ]
        )
    lines.extend(["### 可选旋律线", ""])
    for melody in story.get("melody_lines", []):
        if not isinstance(melody, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(melody.get('id'))}` {_text(melody.get('title'))}",
                "",
                f"- 功能：{_text(melody.get('function'))}",
                f"- 锚点：{_ids(melody.get('anchor_event_ids'))}",
                f"- 变奏：{'；'.join(_strings(melody.get('variation_pattern'))) or '—'}",
                f"- 扩展：{'；'.join(_strings(melody.get('expansion_options'))) or '—'}",
                f"- 删除影响：{_text(melody.get('omission_effect'))}",
                f"- 边界：{'；'.join(_strings(melody.get('boundaries'))) or '—'}",
                f"- 系列潜力：{_text(melody.get('series_potential'))}",
                "",
            ]
        )
    lines.extend(
        [
        "### 故事发展阶段",
        "",
        ]
    )
    for phase in story.get("phases", []):
        if not isinstance(phase, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(phase.get('id'))}` {_text(phase.get('title'))}",
                "",
                f"- 阶段职责：{_text(phase.get('function'))}",
                f"- 开发单元：{_ids(phase.get('unit_ids'))}",
                f"- 进入状态：{_text(phase.get('entry_state'))}",
                f"- 驱动目标：{_text(phase.get('driving_goal'))}",
                f"- 主要压力：{_text(phase.get('pressure'))}",
                f"- 决定性变化：{_text(phase.get('decisive_change'))}",
                f"- 离开状态：{_text(phase.get('exit_state'))}",
                "",
            ]
        )
    lines.extend(["## 3. 小说人物设定", ""])
    lines.extend(render_canonical_characters(demands, characters, relationships))
    return lines


def render_ndb(review_data: dict[str, Any], map_data: dict[str, Any]) -> str:
    controls = [
        item
        for item in map_data.get("control_points", [])
        if isinstance(item, dict)
    ]
    units = [item for item in map_data.get("units", []) if isinstance(item, dict)]
    obligations = [
        item
        for item in map_data.get("information_obligations", [])
        if isinstance(item, dict)
    ]
    open_items = [
        item for item in map_data.get("open_items", []) if isinstance(item, dict)
    ]
    threads = [
        item
        for item in map_data.get("terminal_threads", [])
        if isinstance(item, dict)
    ]
    lines = [
        "# 小说构思开发规格",
        "",
        "## 0. 权威与交接状态",
        "",
        f"- Run：`{_text(review_data.get('run_id'))}`",
        f"- R1 候选状态：`{_text(review_data.get('status'))}`",
        "- 本文是开发导航视图；故事事实仍以六份权威设计稿及其控制点为准。",
        "- 世界、故事、人物和单元文字来自已经逐条复核自主决定与派生声明的 D1 4.0 模型。",
        "",
    ]
    authority = (
        map_data.get("authority_partition")
        if isinstance(map_data.get("authority_partition"), dict)
        else {}
    )
    lines.extend(
        [
            "## D1 自主开发增量",
            "",
            f"- D1 自主职责：{_text(authority.get('autonomous_mandate'))}",
            f"- 下游保留：{_text(authority.get('downstream_reserved'))}",
            f"- 禁止越界：{_text(authority.get('prohibitions'))}",
            "",
            "### 开发缺口",
            "",
        ]
    )
    for gap in map_data.get("development_gaps", []):
        if not isinstance(gap, dict):
            continue
        lines.append(
            f"- `{_text(gap.get('id'))}` [{_text(gap.get('resolution'))}] "
            f"{_text(gap.get('question'))}；必要性：{_text(gap.get('why_needed'))}；"
            f"决定：{_ids(gap.get('decision_ids'))}"
        )
    lines.extend(["", "### 新增设计决定", ""])
    for decision in map_data.get("design_decisions", []):
        if not isinstance(decision, dict):
            continue
        lines.extend(
            [
                f"#### `{_text(decision.get('id'))}` {_text(decision.get('statement'))}",
                "",
                f"- 解决：{_ids(decision.get('gap_ids'))}",
                f"- 功能：{_text(decision.get('function'))}",
                f"- 必要性：{_text(decision.get('necessity'))}",
                f"- 兼容性：{_text(decision.get('compatibility'))}",
                f"- 投影：{_ids(decision.get('projected_subjects'))}",
                f"- 下游自由：{'；'.join(_strings(decision.get('downstream_freedom'))) or '—'}",
                "",
            ]
        )
    lines.extend(render_conception_sections(map_data))
    lines.extend(["## 4. 控制与执行细节", ""])
    for area, label in AREAS:
        if area == "causality":
            continue
        area_controls = [item for item in controls if item.get("area") == area]
        lines.extend([f"## {label}", ""])
        if not area_controls:
            lines.append("- 本区没有可消费控制点。")
        for control in area_controls:
            lines.append(
                f"- `{_text(control.get('id'))}` "
                f"[{_text(control.get('hardness'))}]：{_text(control.get('text'))}"
            )
        lines.append("")

    lines.extend(["## 因果开发线", "", "### 因果控制点", ""])
    causal_controls = [
        item for item in controls if item.get("area") == "causality"
    ]
    if not causal_controls:
        lines.append("- 本区没有可消费控制点。")
    for control in causal_controls:
        lines.append(
            f"- `{_text(control.get('id'))}` "
            f"[{_text(control.get('hardness'))}]：{_text(control.get('text'))}"
        )
    lines.extend(["", "### 开发单元", ""])
    for unit in units:
        shift = (
            unit.get("value_shift")
            if isinstance(unit.get("value_shift"), dict)
            else {}
        )
        information = (
            unit.get("information")
            if isinstance(unit.get("information"), dict)
            else {}
        )
        lines.extend(
            [
                f"#### `{_text(unit.get('id'))}` {_text(unit.get('title'))}",
                "",
                f"- 职责：{_text(unit.get('purpose'))}",
                f"- 因果节点：{_ids(unit.get('causal_nodes'))}",
                f"- POV：`{_text(unit.get('pov'))}`",
                f"- 前置：{'；'.join(_strings(unit.get('preconditions'))) or '—'}",
                f"- 目标：{_text(unit.get('objective'))}",
                f"- 阻力：{_text(unit.get('obstacle'))}",
                "- 对抗系统："
                + json.dumps(
                    unit.get("opposition", {}),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                f"- 选择：{_text(unit.get('choice'))}",
                "- 选项："
                + json.dumps(
                    unit.get("choice_options", []),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                f"- 选择成本：{_text(unit.get('choice_cost'))}",
                f"- 后果：{_text(unit.get('consequence'))}",
                f"- 下一压力：{_text(unit.get('next_pressure'))}",
                f"- D1 新增决定：{_ids(unit.get('development_decisions'))}",
                (
                    f"- 变化：{_text(shift.get('axis'))}："
                    f"{_text(shift.get('before'))} → {_text(shift.get('after'))}；"
                    f"原因：{_text(shift.get('turning_cause'))}"
                ),
                (
                    "- 信息责任："
                    f"建立 {_ids(information.get('establish'))}；"
                    f"提示 {_ids(information.get('hint'))}；"
                    f"暂缓 {_ids(information.get('withhold'))}；"
                    f"回收 {_ids(information.get('payoff'))}"
                ),
                f"- 世界约束：{_ids(unit.get('world_constraints'))}",
                f"- 末态：{_text(unit.get('exit_state'))}",
                f"- 依赖：{_ids(unit.get('depends_on'))}",
                f"- 规模：`{_text(unit.get('scale'))}`",
                f"- 来源控制点：{_ids(unit.get('source_controls'))}",
                "",
            ]
        )

    lines.extend(["## 信息义务", ""])
    if not obligations:
        lines.append("- 没有需要跨单元管理的信息义务。")
    for item in obligations:
        lines.append(
            f"- `{_text(item.get('id'))}`：{_text(item.get('statement'))}；"
            f"受众 `{_text(item.get('audience'))}`；"
            f"回收 `{_text(item.get('resolution'))}`；"
            f"知识持有者 {_ids(item.get('knowledge_holder_controls'))}。"
        )
    lines.extend(["", "## 终点与结局接口", ""])
    for thread in threads:
        lines.append(
            f"- `{_text(thread.get('id'))}` {_text(thread.get('label'))}："
            f"角色 `{_text(thread.get('role'))}`，终点单元 "
            f"`{_text(thread.get('terminal_unit'))}`，来源 "
            f"{_ids(thread.get('source_controls'))}。"
        )

    lines.extend(["", "## 开发自由与禁止", ""])
    for unit in units:
        lines.append(f"### `{_text(unit.get('id'))}`")
        lines.append(
            f"- 可自主实现：{'；'.join(_strings(unit.get('creative_freedom'))) or '—'}"
        )
        lines.append(f"- 不得越过：{_ids(unit.get('prohibitions'))}")
        lines.append("")

    lines.extend(["## 开放问题", ""])
    if not open_items:
        lines.append("- 当前没有登记的开放控制点。")
    for item in open_items:
        lines.extend(
            [
                f"### `{_text(item.get('id'))}`",
                "",
                f"- 来源：`{_text(item.get('source_control'))}`",
                f"- 允许处理：{_text(item.get('allowed_handling'))}",
                f"- 禁止预决：{_text(item.get('forbidden_resolution'))}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_review(review_data: dict[str, Any]) -> str:
    reviewer = (
        review_data.get("reviewer")
        if isinstance(review_data.get("reviewer"), dict)
        else {}
    )
    lines = [
        "# 小说构思交接审阅",
        "",
        "## 审阅身份与范围",
        "",
        f"- Run：`{_text(review_data.get('run_id'))}`",
        f"- Reviewer：`{_text(reviewer.get('id'))}`",
        f"- 角色：`{_text(reviewer.get('role'))}`",
        f"- 角色分离声明：`{_text(reviewer.get('assurance'))}`",
        f"- 八任务证据范围：`{_text(reviewer.get('evidence_scope'))}`",
        f"- 方法：{_text(reviewer.get('method'))}",
        "",
    ]
    conception_reviews = [
        item
        for item in review_data.get("conception_reviews", [])
        if isinstance(item, dict)
    ]
    lines.extend(
        [
            "",
            "## 完整构思审查",
            "",
            "| 构思板块 | 状态 | 构思对象 | 依据控制点 | 审查结论 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in conception_reviews:
        lines.append(
            f"| {_text(item.get('area'))} | `{_text(item.get('status'))}` | "
            f"{_ids(item.get('subject_ids'))} | "
            f"{_ids(item.get('control_ids'))} | "
            f"{_text(item.get('finding'))} |"
        )
    lines.extend(["", "### 世界信息、运行系统与主要环境复核", ""])
    for item in review_data.get("world_model_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('subject_id'))}` "
            f"[{_text(item.get('subject_type'))} / {_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；决定：{_ids(item.get('decision_ids'))}"
        )
    lines.extend(["", "### 主要事件复核", ""])
    for item in review_data.get("major_event_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('event_id'))}` "
            f"[{_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；故事线："
            f"{_ids(item.get('storyline_ids'))}；单元："
            f"{_ids(item.get('unit_ids'))}；环境："
            f"{_ids(item.get('environment_ids'))}；人物："
            f"{_ids(item.get('participant_ids'))}；来源覆盖："
            f"{_ids(item.get('source_coverage_ids'))}"
        )
    lines.extend(["", "### 主线、支线与背景线复核", ""])
    for item in review_data.get("storyline_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('storyline_id'))}` "
            f"[{_text(item.get('type'))} / {_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；单元：{_ids(item.get('unit_ids'))}"
        )
    lines.extend(["", "### 故事线需求、拓扑与连接点复核", ""])
    architecture_review = review_data.get("storyline_architecture_review")
    if isinstance(architecture_review, dict):
        lines.append(
            f"- `{_text(architecture_review.get('subject_id'))}` "
            f"[{_text(architecture_review.get('status'))}]："
            f"{_text(architecture_review.get('finding'))}；入口："
            f"{_ids(architecture_review.get('entry_storyline_ids'))}；"
            f"主干：`{_text(architecture_review.get('main_storyline_id'))}`；"
            f"终点：{_ids(architecture_review.get('terminal_storyline_ids'))}"
        )
    for item in review_data.get("storyline_demand_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- 需求 `{_text(item.get('demand_id'))}` "
            f"[{_text(item.get('disposition'))} / "
            f"{_text(item.get('status'))}]：{_text(item.get('finding'))}；"
            f"故事线：{_ids(item.get('storyline_ids'))}"
        )
    for item in review_data.get("storyline_connection_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- 连接 `{_text(item.get('connection_id'))}` "
            f"[{_text(item.get('connection_type'))} / "
            f"{_text(item.get('status'))}]："
            f"{_ids(item.get('incoming_storyline_ids'))} → "
            f"{_ids(item.get('outgoing_storyline_ids'))} @ "
            f"`{_text(item.get('event_id'))}`；"
            f"{_text(item.get('finding'))}"
        )
    lines.extend(["", "### 可选旋律线复核", ""])
    for item in review_data.get("melody_line_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('melody_line_id'))}` "
            f"[{_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；锚点："
            f"{_ids(item.get('anchor_event_ids'))}；"
            "因果／结局／新 POV／决定性信息："
            f"{_text(item.get('required_for_causality'))} / "
            f"{_text(item.get('required_for_resolution'))} / "
            f"{_text(item.get('new_pov_allowed'))} / "
            f"{_text(item.get('carries_decisive_information'))}"
        )
    lines.extend(["", "### 角色需求与建档处置复核", ""])
    for item in review_data.get("character_demand_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('demand_id'))}` "
            f"[{_text(item.get('category'))} / {_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；处置："
            f"{_text(item.get('resolution'))} → "
            f"`{_text(item.get('profile_id'))}`；设计决定："
            f"{_ids(item.get('decision_ids'))}"
        )
    lines.extend(["", "### 人物定义逐项复核", ""])
    for item in review_data.get("character_profile_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('character_id'))}` "
            f"[{_text(item.get('importance'))} / {_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}；设计决定："
            f"{_ids(item.get('decision_ids'))}"
        )
    lines.extend(["", "### 人物关系边逐项复核", ""])
    for item in review_data.get("relationship_edge_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('relationship_id'))}` "
            f"`{_text(item.get('source_id'))}` ↔ "
            f"`{_text(item.get('target_id'))}` "
            f"[{_text(item.get('status'))}]：{_text(item.get('finding'))}；"
            f"设计决定：{_ids(item.get('decision_ids'))}"
        )
    lines.extend(["", "### 核心人物关系网络复核", ""])
    for item in review_data.get("relationship_network_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('character_id'))}` "
            f"[{_text(item.get('status'))}]：{_text(item.get('finding'))}；"
            f"最大人物图深度：{_text(item.get('max_depth'))}；"
            f"分层人物：{_text(item.get('layer_character_ids'))}；"
            f"已覆盖人物：{_ids(item.get('profiled_character_ids'))}；"
            f"关系：{_ids(item.get('relationship_ids'))}"
        )

    lines.extend(
        [
            "",
            "## 六区控制审查",
            "",
            "| 控制区 | 拥有者 | 状态 | 证据 | 结论 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in review_data.get("control_area_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| {_text(item.get('area'))} | `{_text(item.get('owner_stage'))}` | "
            f"`{_text(item.get('status'))}` | {_ids(item.get('control_ids'))} | "
            f"{_text(item.get('finding'))} |"
        )

    lines.extend(["", "## 十三项跨域检查", ""])
    checks = (
        review_data.get("cross_domain_checks")
        if isinstance(review_data.get("cross_domain_checks"), dict)
        else {}
    )
    for check_id in CROSS_CHECK_LABELS:
        item = checks.get(check_id) if isinstance(checks.get(check_id), dict) else {}
        lines.extend(
            [
                f"### {CROSS_CHECK_LABELS[check_id]} `{check_id}`",
                "",
                f"- 状态：`{_text(item.get('status'))}`",
                f"- 结论：{_text(item.get('finding'))}",
                f"- 控制点：{_ids(item.get('control_ids'))}",
                f"- 单元：{_ids(item.get('unit_ids'))}",
                "",
            ]
        )

    lines.extend(["## 自主开发增量复核", "", "### 开发缺口", ""])
    for item in review_data.get("development_gap_reviews", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{_text(item.get('gap_id'))}` "
            f"[{_text(item.get('resolution'))} / {_text(item.get('status'))}]："
            f"{_text(item.get('finding'))}"
        )
    lines.extend(["", "### 设计决定", ""])
    for item in review_data.get("design_decision_reviews", []):
        if not isinstance(item, dict):
            continue
        dimensions = (
            item.get("dimensions")
            if isinstance(item.get("dimensions"), dict)
            else {}
        )
        lines.extend(
            [
                f"#### `{_text(item.get('decision_id'))}` "
                f"`{_text(item.get('status'))}`",
                "",
                f"- 缺口：{_ids(item.get('gap_ids'))}",
                f"- 控制点：{_ids(item.get('source_control_ids'))}",
                f"- 六维复核："
                + "；".join(
                    f"{key}={value}" for key, value in sorted(dimensions.items())
                ),
                f"- 结论：{_text(item.get('finding'))}",
                "",
            ]
        )

    derivations = [
        item
        for item in review_data.get("derivation_reviews", [])
        if isinstance(item, dict)
    ]
    lines.extend(
        [
            "## 派生声明复核",
            "",
            f"- 已复核：{len(derivations)} 条。",
            "",
            "| 派生声明 | 状态 | 来源控制点／设计决定 | 结论 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in derivations:
        lines.append(
            f"| `{_text(item.get('derivation_id'))}` | "
            f"`{_text(item.get('status'))}` | "
            f"控制点 {_ids(item.get('source_control_ids'))}；"
            f"决定 {_ids(item.get('source_decision_ids'))} | "
            f"{_text(item.get('finding'))} |"
        )

    lines.extend(["", "## 独立八任务交接", ""])
    for item in review_data.get("tasks", []):
        if not isinstance(item, dict):
            continue
        task_id = item.get("id")
        lines.extend(
            [
                f"### {TASK_LABELS.get(task_id, _text(task_id))} `{_text(task_id)}`",
                "",
                f"- 状态：`{_text(item.get('status'))}`",
                f"- 回答：{_text(item.get('response'))}",
                f"- 证据：{_ids(item.get('evidence_ids'))}",
                "",
            ]
        )

    lines.extend(["## 开放项复核", ""])
    open_reviews = [
        item
        for item in review_data.get("open_item_reviews", [])
        if isinstance(item, dict)
    ]
    if not open_reviews:
        lines.append("- D1 没有登记开放项。")
    for item in open_reviews:
        lines.append(
            f"- `{_text(item.get('open_item_id'))}` "
            f"[{_text(item.get('status'))}]：{_text(item.get('finding'))}"
        )

    lines.extend(["", "## Findings 与责任", ""])
    findings = [
        item for item in review_data.get("findings", []) if isinstance(item, dict)
    ]
    if not findings:
        lines.append("- 没有登记风险、修订项或阻塞项。")
    for item in findings:
        lines.extend(
            [
                f"### `{_text(item.get('id'))}` "
                f"{_text(item.get('severity'))}",
                "",
                f"- 问题：{_text(item.get('problem'))}",
                f"- 证据：{_ids(item.get('evidence_ids'))}",
                f"- 责任：`{_text(item.get('owner'))}`",
                f"- 动作：{_text(item.get('required_action'))}",
                "",
            ]
        )

    lines.extend(
        [
            "## 候选 Verdict",
            "",
            f"`{_text(review_data.get('status'))}`",
            "",
            "该 verdict 是技术审阅结论，不是作者最终批准。只有作者批准当前审阅报告并形成通过主 harness 的 R1 completion，才允许进入开发。",
            "",
        ]
    )
    return "\n".join(lines)


def render_outputs(
    package_dir: Path,
    review_data: dict[str, Any],
    *,
    include_handoff: bool = False,
    include_return: bool = False,
) -> dict[str, str]:
    _completion_path, _completion, manifest_path, _manifest, map_data = locate_d1(
        package_dir, review_data
    )
    outputs = {
        "novel-design-brief.md": render_ndb(review_data, map_data),
        "conception-review.md": render_review(review_data),
    }
    if include_handoff:
        handoff = build_independent_handoff(
            package_dir, review_data, manifest_path
        )
        outputs["independent-handoff.json"] = (
            json.dumps(handoff, ensure_ascii=False, indent=2) + "\n"
        )
    if include_return:
        outputs.update(build_return_outputs(package_dir, review_data))
    return outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render deterministic R1 conception-review deliverables."
    )
    parser.add_argument("package_directory", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    data = load_json(package_dir / "review-data.json")
    outputs = render_outputs(package_dir, data)
    for filename in GENERATED_OUTPUTS - set(outputs):
        path = package_dir / filename
        if path.exists():
            path.unlink()
    for filename, content in outputs.items():
        (package_dir / filename).write_bytes(content.encode("utf-8"))
    print("OK: rendered R1 conception-review deliverables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
