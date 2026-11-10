#!/usr/bin/env python3
"""Render human-readable D1 documents from the authoritative data and verdict."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


AREA_LABELS = {
    "intent": "意图",
    "subject": "主体",
    "world": "世界",
    "character": "人物",
    "causality": "因果",
    "narrative": "叙述",
}
SEMANTIC_LABELS = {
    "gap_resolution": "开发缺口闭合",
    "forward_causality": "因果正向回放",
    "reverse_ending": "结局反向追溯",
    "character_agency": "人物能动性",
    "opposition_adaptation": "对抗适应性",
    "choice_costs": "选择与机会成本",
    "easy_solution": "便捷解法压力测试",
    "world_permissions": "世界与权限",
    "pov_information": "POV 与信息边界",
    "plant_payoff": "铺设与回收",
    "thematic_testing": "主题行动检验",
    "minimality": "最少必要性",
    "downstream_sufficiency": "下游开发充分性",
}
HANDOFF_LABEL = "开发交接自测"


def _text(value: Any, fallback: str = "—") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _items(values: Any) -> str:
    if not isinstance(values, list) or not values:
        return "—"
    return "；".join(_text(value) for value in values)


def _table_cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", "<br>")


def _by_id(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _character_layers(
    profiles: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    core_id: str,
) -> dict[int, list[str]]:
    adjacency: dict[str, set[str]] = {
        item["id"]: set()
        for item in profiles
        if isinstance(item.get("id"), str)
    }
    for edge in relationships:
        source = edge.get("source_id")
        target = edge.get("target_id")
        if source in adjacency and target in adjacency and source != target:
            adjacency[source].add(target)
            adjacency[target].add(source)
    distances = {core_id: 0}
    queue = [core_id]
    for current in queue:
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    layers: dict[int, list[str]] = {}
    for character_id, distance in distances.items():
        if distance:
            layers.setdefault(distance, []).append(character_id)
    return {level: sorted(ids) for level, ids in sorted(layers.items())}


def _control_items(values: Any, controls: dict[str, dict[str, Any]]) -> str:
    if not isinstance(values, list) or not values:
        return "—"
    rendered = []
    for value in values:
        control = controls.get(value, {})
        rendered.append(f"{_text(value)} · {_text(control.get('text'))}")
    return "；".join(rendered)


def _information_items(
    values: Any, obligations: dict[str, dict[str, Any]]
) -> str:
    if not isinstance(values, list) or not values:
        return "—"
    rendered = []
    for value in values:
        obligation = obligations.get(value, {})
        rendered.append(f"{_text(value)} · {_text(obligation.get('statement'))}")
    return "；".join(rendered)


def render_development_map(data: dict[str, Any]) -> str:
    controls = _by_id(data.get("control_points"))
    obligations = _by_id(data.get("information_obligations"))
    derivations = (
        data.get("derivation_claims")
        if isinstance(data.get("derivation_claims"), list)
        else []
    )
    units = data.get("units") if isinstance(data.get("units"), list) else []
    sources = (
        data.get("source_artifacts")
        if isinstance(data.get("source_artifacts"), list)
        else []
    )
    terminal_threads = (
        data.get("terminal_threads")
        if isinstance(data.get("terminal_threads"), list)
        else []
    )
    open_items = (
        data.get("open_items") if isinstance(data.get("open_items"), list) else []
    )
    conception = (
        data.get("conception") if isinstance(data.get("conception"), dict) else {}
    )
    authority = (
        data.get("authority_partition")
        if isinstance(data.get("authority_partition"), dict)
        else {}
    )
    gaps = (
        data.get("development_gaps")
        if isinstance(data.get("development_gaps"), list)
        else []
    )
    decisions = (
        data.get("design_decisions")
        if isinstance(data.get("design_decisions"), list)
        else []
    )

    lines = [
        "# 小说开发地图",
        "",
        "## 输入版本与状态",
        "",
        f"- Run：`{_text(data.get('run_id'))}`",
        f"- 数据契约：`{_text(data.get('schema_version'))}`",
        f"- 状态：`{_text(data.get('status'))}`",
        "",
        "| 来源 ID | 控制区 | 阶段 | 文件 | SHA-256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source in sources:
        if not isinstance(source, dict):
            continue
        lines.append(
            "| {id} | {area} | {stage} | {path} | `{sha}` |".format(
                id=_table_cell(source.get("id")),
                area=_table_cell(AREA_LABELS.get(source.get("area"), source.get("area"))),
                stage=_table_cell(source.get("stage")),
                path=_table_cell(source.get("path")),
                sha=_table_cell(source.get("sha256")),
            )
        )

    lines.extend(
        [
            "",
            "## 自主开发权限",
            "",
            f"- 作者锁定控制点：{_items(authority.get('author_locked'))}",
            f"- 明确授权控制点：{_items(authority.get('delegated'))}",
            f"- 作者开放控制点：{_items(authority.get('open'))}",
            f"- D1 自主职责：{_text(authority.get('autonomous_mandate'))}",
            f"- 下游保留：{_text(authority.get('downstream_reserved'))}",
            f"- 禁止越界：{_text(authority.get('prohibitions'))}",
            "",
            "## 开发缺口",
            "",
            "| 缺口 | 领域／类型 | 必须回答的问题 | 为什么现在必须解决 | 处理 | 决定 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        lines.append(
            "| {id} | {domain} / {kind} | {question} | {why} | {resolution} | "
            "{decisions} |".format(
                id=_table_cell(gap.get("id")),
                domain=_table_cell(gap.get("domain")),
                kind=_table_cell(gap.get("kind")),
                question=_table_cell(gap.get("question")),
                why=_table_cell(gap.get("why_needed")),
                resolution=_table_cell(
                    gap.get("downstream_reservation") or gap.get("resolution")
                ),
                decisions=_table_cell(_items(gap.get("decision_ids"))),
            )
        )

    lines.extend(["", "## D1 新增设计决定", ""])
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        lines.extend(
            [
                f"### {_text(decision.get('id'))} · {_text(decision.get('statement'))}",
                "",
                f"- 领域／类型：{_text(decision.get('domain'))} / "
                f"{_text(decision.get('kind'))}",
                f"- 新增方式：{_text(decision.get('novelty'))}",
                f"- 解决缺口：{_items(decision.get('gap_ids'))}",
                f"- 故事功能：{_text(decision.get('function'))}",
                f"- 必要性：{_text(decision.get('necessity'))}",
                f"- 权限依据：{_text(decision.get('authority_basis'))}",
                f"- 兼容性：{_text(decision.get('compatibility'))}",
                f"- 影响／可撤销性：{_text(decision.get('impact'))} / "
                f"{_text(decision.get('reversibility'))}",
                f"- 投影对象：{_items(decision.get('projected_subjects'))}",
                f"- 下游自由：{_items(decision.get('downstream_freedom'))}",
                "",
                "| 方案 | 状态 | 收益 | 代价 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for alternative in decision.get("alternatives", []):
            if not isinstance(alternative, dict):
                continue
            lines.append(
                "| {proposal} | {status} | {benefit} | {cost} |".format(
                    proposal=_table_cell(alternative.get("proposal")),
                    status=_table_cell(alternative.get("status")),
                    benefit=_table_cell(alternative.get("benefit")),
                    cost=_table_cell(alternative.get("cost")),
                )
            )
        lines.append("")

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
    character_demands = [
        item
        for item in character_model.get("demand_register", [])
        if isinstance(item, dict)
    ]
    character_relationships = [
        item
        for item in character_model.get("relationships", [])
        if isinstance(item, dict)
    ]
    character_index = _by_id(characters)
    lines.extend(
        [
            "",
            "## 完整构思模型",
            "",
            "### 小说世界设定",
            "",
            f"- 定义：{_text(world.get('definition'))}",
            f"- 故事功能：{_text(world.get('story_function'))}",
            f"- 时空范围：{_text(world.get('time_space_scope'))}",
            f"- 运行逻辑：{_items(world.get('operating_logic'))}",
            f"- 权力与资源：{_items(world.get('power_and_resources'))}",
            f"- 行动许可：{_items(world.get('action_permissions'))}",
            f"- 硬约束：{_items(world.get('hard_constraints'))}",
            f"- 压力来源：{_items(world.get('pressure_sources'))}",
            f"- 代价与后果：{_items(world.get('costs_and_consequences'))}",
            f"- 结局世界状态：{_text(world.get('end_state'))}",
            f"- 范围外：{_items(world.get('scope_exclusions'))}",
            f"- 来源控制点：{_items(world.get('source_controls'))}",
            "",
            "#### 世界信息八域",
            "",
        ]
    )
    for facet in world.get("facets", []):
        if not isinstance(facet, dict):
            continue
        lines.extend(
            [
                f"##### {_text(facet.get('id'))} · {_text(facet.get('domain'))}",
                "",
                f"- 状态：{_text(facet.get('status'))}",
                f"- 定义：{_text(facet.get('definition'))}",
                f"- 故事关联：{_text(facet.get('story_relevance'))}",
                f"- 自主决定：{_items(facet.get('development_decisions'))}",
                f"- 下游自由：{_text(facet.get('downstream_freedom'))}",
                "",
            ]
        )
    lines.extend(["#### 世界运行系统", ""])
    for system in world.get("systems", []):
        if not isinstance(system, dict):
            continue
        lines.extend(
            [
                f"##### {_text(system.get('id'))} · {_text(system.get('name'))}",
                "",
                f"- 领域：{_text(system.get('domain'))}",
                f"- 定义：{_text(system.get('definition'))}",
                f"- 输入条件：{_items(system.get('input_conditions'))}",
                f"- 转换规则：{_text(system.get('transformation_rule'))}",
                f"- 可观察输出：{_items(system.get('observable_outputs'))}",
                f"- 覆盖环境：{_items(system.get('environment_ids'))}",
                f"- 覆盖主要事件：{_items(system.get('major_event_ids'))}",
                f"- 行动者：{_items(system.get('actors'))}",
                f"- 资源：{_items(system.get('resources'))}",
                f"- 规则：{_items(system.get('rules'))}",
                f"- 权限：{_items(system.get('permissions'))}",
                f"- 代价：{_items(system.get('costs'))}",
                f"- 限制：{_items(system.get('limits'))}",
                f"- 失败方式：{_items(system.get('failure_modes'))}",
                f"- 故事作用：{_items(system.get('story_effects'))}",
                f"- 状态变化：{_items(system.get('state_changes'))}",
                f"- 自主决定：{_items(system.get('development_decisions'))}",
                f"- 下游自由：{_text(system.get('downstream_freedom'))}",
                "",
            ]
        )
    lines.extend(["#### 主要环境定义", ""])
    for environment in world.get("environments", []):
        if not isinstance(environment, dict):
            continue
        lines.extend(
            [
                f"##### {_text(environment.get('id'))} · "
                f"{_text(environment.get('name'))}",
                "",
                f"- 类型：{_text(environment.get('environment_type'))}",
                f"- 定义：{_text(environment.get('definition'))}",
                f"- 范围：{_text(environment.get('scope'))}",
                f"- 鲜明特征：{_items(environment.get('distinctive_features'))}",
                f"- 基本要素：{_items(environment.get('basic_elements'))}",
                f"- 感知条件：{_items(environment.get('sensory_conditions'))}",
                f"- 进入者与权限：{_items(environment.get('occupants_and_access'))}",
                f"- 资源与设施：{_items(environment.get('resources_and_infrastructure'))}",
                f"- 可行动作与规则：{_items(environment.get('rules_and_affordances'))}",
                f"- 危险与压力：{_items(environment.get('hazards_and_pressures'))}",
                f"- 故事功能：{_items(environment.get('story_functions'))}",
                f"- 状态变化：{_items(environment.get('state_changes'))}",
                "- 内部边界："
                f"{_items(environment.get('topology', {}).get('boundaries'))}",
                f"- 故事线：{_items(environment.get('storyline_ids'))}",
                f"- 开发单元：{_items(environment.get('unit_ids'))}",
                f"- 自主决定：{_items(environment.get('development_decisions'))}",
                f"- 下游自由：{_text(environment.get('downstream_freedom'))}",
                "",
                "**功能区**",
                "",
            ]
        )
        topology = environment.get("topology", {})
        if isinstance(topology, dict):
            for zone in topology.get("zones", []):
                if not isinstance(zone, dict):
                    continue
                lines.extend(
                    [
                        f"- `{_text(zone.get('id'))}` "
                        f"**{_text(zone.get('name'))}**："
                        f"{_text(zone.get('function'))}；"
                        f"状态：{_text(zone.get('state'))}；"
                        f"在场人物：{_items(zone.get('occupant_ids'))}；"
                        f"资源：{_items(zone.get('resources'))}",
                    ]
                )
            lines.extend(["", "**连接与阻断**", ""])
            for connection in topology.get("connections", []):
                if not isinstance(connection, dict):
                    continue
                lines.extend(
                    [
                        f"- `{_text(connection.get('from_zone'))}` → "
                        f"`{_text(connection.get('to_zone'))}`："
                        f"{_text(connection.get('channel'))}；"
                        f"准入：{_text(connection.get('access_condition'))}；"
                        f"阻断后果：{_text(connection.get('blockage_effect'))}",
                    ]
                )
        lines.extend(["", "**事件承载证明**", ""])
        for event in environment.get("event_hosting", []):
            if not isinstance(event, dict):
                continue
            lines.extend(
                [
                    f"- `{_text(event.get('unit_id'))}` @ "
                    f"{_items(event.get('zone_ids'))}："
                    f"{_text(event.get('event_function'))}",
                    f"  - 在场人物：{_items(event.get('active_character_ids'))}",
                    f"  - 进入状态：{_text(event.get('entry_state'))}",
                    f"  - 可做：{_items(event.get('available_actions'))}",
                    f"  - 不可做：{_items(event.get('blocked_actions'))}",
                    f"  - 环境压力：{_text(event.get('pressure'))}",
                    f"  - 离开状态：{_text(event.get('exit_state'))}",
                ]
            )
        lines.append("")
    lines.extend(["#### 主要事件的环境需求与承载选择", ""])
    for requirement in world.get("event_environment_requirements", []):
        if not isinstance(requirement, dict):
            continue
        lines.extend(
            [
                f"- `{_text(requirement.get('major_event_id'))}` → "
                f"**{_text(requirement.get('primary_environment_id'))}**"
                f"（次级：{_items(requirement.get('secondary_environment_ids'))}）",
                f"  - 必需能力：{_items(requirement.get('required_capabilities'))}",
                f"  - 必需功能区：{_items(requirement.get('required_zone_ids'))}",
                f"  - 资源／权限：{_items(requirement.get('required_resources'))} / "
                f"{_items(requirement.get('required_permissions'))}",
                f"  - 信息通道："
                f"{_items(requirement.get('required_information_channels'))}",
                f"  - 风险与约束："
                f"{_items(requirement.get('hazards_and_constraints'))}",
                f"  - 转场要求："
                f"{_items(requirement.get('transition_requirements'))}",
                f"  - 充分性：{_text(requirement.get('adequacy_rationale'))}",
            ]
        )
    lines.append("")
    lines.extend(
        [
            "### 小说故事线设定",
            "",
            f"- 核心承诺：{_text(story.get('core_promise'))}",
            f"- 谁的故事：{_text(story.get('whose_story'))}",
            f"- 中心冲突：{_text(story.get('central_conflict'))}",
            f"- 核心问题：{_text(story.get('dramatic_question'))}",
            f"- 风险与代价：{_items(story.get('stakes'))}",
            f"- 开端状态：{_text(story.get('start_state'))}",
            f"- 触发事件：{_text(story.get('inciting_incident'))}",
            f"- 升级逻辑：{_items(story.get('escalation_logic'))}",
            f"- 高潮：{_text(story.get('climax'))}",
            f"- 结局：{_text(story.get('resolution'))}",
            f"- 开放线：{_items(story.get('open_threads'))}",
            f"- 范围外：{_items(story.get('scope_exclusions'))}",
            f"- 来源控制点：{_items(story.get('source_controls'))}",
            "",
            "#### 事件跨度与来源覆盖",
            "",
            f"- 最早因果变化："
            f"{_text(story.get('event_span', {}).get('earliest_causal_change'))}",
            f"- 主行动入口："
            f"{_text(story.get('event_span', {}).get('main_action_entry_event_id'))}",
            f"- 开篇事件："
            f"{_items(story.get('event_span', {}).get('opening_event_ids'))}",
            f"- 余波事件："
            f"{_items(story.get('event_span', {}).get('aftermath_event_ids'))}",
            f"- 最晚后果："
            f"{_text(story.get('event_span', {}).get('latest_consequence'))}",
            f"- 覆盖说明："
            f"{_text(story.get('event_span', {}).get('coverage_rationale'))}",
            "",
            "**事件来源覆盖台账**",
            "",
        ]
    )
    for coverage in story.get("event_source_coverage", []):
        if not isinstance(coverage, dict):
            continue
        lines.extend(
            [
                f"- `{_text(coverage.get('id'))}` "
                f"[{_text(coverage.get('candidate_type'))} / "
                f"{_text(coverage.get('disposition'))}] "
                f"{_text(coverage.get('source_artifact_id'))} · "
                f"{_text(coverage.get('source_section'))}："
                f"{_text(coverage.get('source_excerpt'))}",
                f"  - 事件：{_items(coverage.get('major_event_ids'))}",
                f"  - 理由：{_text(coverage.get('rationale'))}",
            ]
        )
    lines.extend(
        [
            "",
            "#### 主要事件",
            "",
        ]
    )
    for event in story.get("major_events", []):
        if not isinstance(event, dict):
            continue
        lines.extend(
            [
                f"##### {_text(event.get('id'))} · "
                f"{_text(event.get('title'))}",
                "",
                f"- 事件角色：{_text(event.get('event_role'))}",
                f"- 事件定义：{_text(event.get('definition'))}",
                f"- 所属故事线：{_items(event.get('storyline_ids'))}",
                f"- 承载单元：{_items(event.get('unit_ids'))}",
                f"- 承载环境：{_items(event.get('environment_ids'))}",
                f"- 参与人物：{_items(event.get('participant_ids'))}",
                f"- 发起行动者：{_items(event.get('initiator_ids'))}",
                f"- 对抗行动者：{_items(event.get('opposition_actor_ids'))}",
                f"- 前提：{_items(event.get('preconditions'))}",
                f"- 发起行动：{_text(event.get('initiating_action'))}",
                f"- 对抗或复杂化："
                f"{_text(event.get('opposition_or_complication'))}",
                f"- 决定性变化：{_text(event.get('decisive_change'))}",
                f"- 直接结果：{_text(event.get('immediate_outcome'))}",
                f"- 状态变化：{_text(event.get('state_before'))} → "
                f"{_text(event.get('state_after'))}",
                f"- 下一压力：{_text(event.get('next_pressure'))}",
                f"- 信息变化：{_items(event.get('information_effects'))}",
                f"- 因果前驱："
                f"{_items(event.get('causal_predecessor_ids'))}",
                f"- 下游自由：{_text(event.get('downstream_freedom'))}",
                "",
            ]
        )
    lines.extend(
        [
            "#### 故事线需求审计",
            "",
        ]
    )
    for demand in story.get("storyline_demands", []):
        if not isinstance(demand, dict):
            continue
        lines.extend(
            [
                f"- `{_text(demand.get('id'))}` "
                f"**{_text(demand.get('need'))}**："
                f"{_text(demand.get('story_function'))}",
                f"  - 遗漏后果：{_text(demand.get('omission_consequence'))}",
                f"  - 处置：{_text(demand.get('disposition'))} → "
                f"{_items(demand.get('storyline_ids'))}",
                f"  - 理由：{_text(demand.get('rationale'))}",
            ]
        )
    architecture = story.get("storyline_architecture", {})
    lines.extend(
        [
            "",
            "#### 故事线拓扑与连接点",
            "",
            f"- 入口故事线：{_items(architecture.get('entry_storyline_ids'))}",
            f"- 主干故事线：{_text(architecture.get('main_storyline_id'))}",
            f"- 终点故事线：{_items(architecture.get('terminal_storyline_ids'))}",
            f"- 覆盖说明：{_text(architecture.get('coverage_rationale'))}",
            "",
        ]
    )
    for connection in architecture.get("connection_points", []):
        if not isinstance(connection, dict):
            continue
        lines.extend(
            [
                f"- `{_text(connection.get('id'))}` "
                f"[{_text(connection.get('connection_type'))}] "
                f"{_items(connection.get('incoming_storyline_ids'))} → "
                f"{_items(connection.get('outgoing_storyline_ids'))} "
                f"@ `{_text(connection.get('event_id'))}`",
                f"  - 前提：{_text(connection.get('preconditions'))}",
                f"  - 转移：{_text(connection.get('transferred_obligations'))}",
                f"  - 结果状态：{_text(connection.get('resulting_state'))}",
            ]
        )
    lines.extend(["", "#### 全部故事线", ""])
    for storyline in story.get("storylines", []):
        if not isinstance(storyline, dict):
            continue
        lines.extend(
            [
                f"##### {_text(storyline.get('id'))} · "
                f"{_text(storyline.get('title'))}",
                "",
                f"- 类型：{_text(storyline.get('type'))}",
                f"- 功能：{_text(storyline.get('function'))}",
                f"- 主体：{_items(storyline.get('protagonists'))}",
                f"- 核心问题：{_text(storyline.get('central_question'))}",
                f"- 起点：{_text(storyline.get('start_state'))}",
                f"- 驱动力：{_text(storyline.get('driver'))}",
                f"- 升级：{_items(storyline.get('escalation'))}",
                f"- 主要事件：{_items(storyline.get('major_event_ids'))}",
                f"- 结局状态：{_text(storyline.get('end_state'))}",
                f"- 闭合方式：{_text(storyline.get('resolution'))}",
                f"- 承载单元：{_items(storyline.get('unit_ids'))}",
                f"- 自主决定：{_items(storyline.get('development_decisions'))}",
                f"- 下游自由：{_text(storyline.get('downstream_freedom'))}",
                "",
            ]
        )
    lines.extend(["#### 可选旋律线", ""])
    for melody in story.get("melody_lines", []):
        if not isinstance(melody, dict):
            continue
        lines.extend(
            [
                f"##### {_text(melody.get('id'))} · "
                f"{_text(melody.get('title'))}",
                "",
                f"- 功能：{_text(melody.get('function'))}",
                f"- 复现锚点：{_items(melody.get('anchor_event_ids'))}",
                f"- 变奏路径：{_items(melody.get('variation_pattern'))}",
                f"- 可扩展方式：{_items(melody.get('expansion_options'))}",
                f"- 删除影响：{_text(melody.get('omission_effect'))}",
                f"- 边界：{_items(melody.get('boundaries'))}",
                f"- 系列潜力：{_text(melody.get('series_potential'))}",
                "- 结构依赖：因果=false；结局=false；新增 POV=false；"
                "决定性信息=false",
                f"- 下游自由：{_text(melody.get('downstream_freedom'))}",
                "",
            ]
        )
    lines.extend(
        [
            "#### 故事阶段",
            "",
        ]
    )
    for phase in story.get("phases", []):
        if not isinstance(phase, dict):
            continue
        lines.extend(
            [
                f"##### {_text(phase.get('id'))} · {_text(phase.get('title'))}",
                "",
                f"- 功能：{_text(phase.get('function'))}",
                f"- 单元：{_items(phase.get('unit_ids'))}",
                f"- 进入状态：{_text(phase.get('entry_state'))}",
                f"- 驱动目标：{_text(phase.get('driving_goal'))}",
                f"- 压力：{_text(phase.get('pressure'))}",
                f"- 决定性变化：{_text(phase.get('decisive_change'))}",
                f"- 离开状态：{_text(phase.get('exit_state'))}",
                f"- 来源控制点：{_items(phase.get('source_controls'))}",
                "",
            ]
        )
    lines.extend(["### 小说人物设定", "", "#### 角色需求与建档处置", ""])
    for demand in character_demands:
        lines.append(
            f"- **{_text(demand.get('category'))}**"
            f"（{_text(demand.get('id'))} / {_text(demand.get('criticality'))}）："
            f"触发：{_text(demand.get('trigger'))}；"
            f"故事职责：{_text(demand.get('story_function'))}；"
            f"遗漏后果：{_text(demand.get('omission_consequence'))}；"
            f"处置：{_text(demand.get('resolution'))} → "
            f"{_text(demand.get('profile_id'))}；"
            f"命名要求：{_text(demand.get('naming_requirement'))}"
        )
    lines.extend(["", "#### 已建档人物", ""])
    for character in characters:
        if not isinstance(character, dict):
            continue
        lines.extend(
            [
                f"#### {_text(character.get('id'))} · {_text(character.get('name'))}",
                "",
                f"- 重要度：{_text(character.get('importance'))}",
                f"- 名称状态：{_text(character.get('naming_status'))}",
                f"- 角色：{_text(character.get('role'))}",
                f"- 故事职责：{_text(character.get('story_function'))}",
                f"- 起点状态：{_text(character.get('start_state'))}",
                f"- 外部目标：{_text(character.get('surface_goal'))}",
                f"- 深层需要：{_text(character.get('deeper_need'))}",
                f"- 恐惧或逃避：{_text(character.get('fear_or_avoidance'))}",
                f"- 价值与边界：{_items(character.get('values_and_boundaries'))}",
                f"- 信息限制：{_items(character.get('information_limits'))}",
                f"- 压力行为：{_items(character.get('pressure_behavior'))}",
                f"- 不可替代选择：{_items(character.get('agency_choices'))}",
                f"- 结局状态：{_text(character.get('end_state'))}",
                f"- 不变量：{_items(character.get('invariants'))}",
                f"- 承载故事线：{_items(character.get('storyline_ids'))}",
                f"- 承载单元：{_items(character.get('unit_ids'))}",
                f"- 来源控制点：{_items(character.get('source_controls'))}",
                "",
                "##### 变化阶段",
                "",
            ]
        )
        for stage in character.get("arc_stages", []):
            if not isinstance(stage, dict):
                continue
            lines.extend(
                [
                    f"- **{_text(stage.get('label'))}**（{_items(stage.get('unit_ids'))}）："
                    f"{_text(stage.get('state'))}；压力：{_text(stage.get('pressure'))}；"
                    f"选择：{_text(stage.get('choice'))}；变化：{_text(stage.get('change'))}",
                ]
            )
        if character.get("importance") == "core":
            lines.extend(["", "##### 最短路径人物层", ""])
            for level, node_ids in _character_layers(
                characters,
                character_relationships,
                str(character.get("id")),
            ).items():
                node_labels = [
                    f"{node_id} · {_text(character_index.get(node_id, {}).get('name'))}"
                    for node_id in node_ids
                ]
                lines.append(f"- 第 {level} 层：{'；'.join(node_labels)}")
            lines.append("")

    lines.extend(["", "### 全局人物关系边", ""])
    for relation in character_relationships:
        source = character_index.get(str(relation.get("source_id")), {})
        target = character_index.get(str(relation.get("target_id")), {})
        lines.append(
            f"- **{_text(source.get('name'))} ↔ {_text(target.get('name'))}**"
            f"（{_text(relation.get('id'))}）："
            f"{_text(relation.get('relationship_type'))}；"
            f"共同历史：{_text(relation.get('shared_history'))}；"
            f"一致：{_text(relation.get('alignment'))}；"
            f"冲突：{_text(relation.get('conflict'))}；"
            f"筹码：{_text(relation.get('leverage'))}；"
            f"信息差：{_text(relation.get('information_asymmetry'))}；"
            f"变化：{_text(relation.get('change'))}；"
            f"故事线：{_items(relation.get('storyline_ids'))}；"
            f"单元：{_items(relation.get('unit_ids'))}"
        )

    lines.extend(
        [
            "",
            "## 全局控制摘要",
            "",
            "| 控制点 | 控制区 | 状态 | 控制陈述 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for control in controls.values():
        lines.append(
            "| {id} | {area} | {hardness} | {text} |".format(
                id=_table_cell(control.get("id")),
                area=_table_cell(
                    AREA_LABELS.get(control.get("area"), control.get("area"))
                ),
                hardness=_table_cell(control.get("hardness")),
                text=_table_cell(control.get("text")),
            )
        )

    lines.extend(
        [
            "",
            "## 信息义务",
            "",
            "| 义务 | 受众 | 知识持有者控制点 | 处理期限 | 来源控制点 | 内容／系列接口 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not obligations:
        lines.append(
            "| — | — | — | — | — | 当前地图无须登记跨单元的信息义务 |"
        )
    for obligation in obligations.values():
        interface = obligation.get("series_interface")
        description = _text(obligation.get("statement"))
        if isinstance(interface, str) and interface.strip():
            description += f"；系列接口：{interface.strip()}"
        lines.append(
            "| {id} | {audience} | {holders} | {resolution} | {controls} | "
            "{description} |".format(
                id=_table_cell(obligation.get("id")),
                audience=_table_cell(obligation.get("audience")),
                holders=_table_cell(
                    _control_items(
                        obligation.get("knowledge_holder_controls"),
                        controls,
                    )
                ),
                resolution=_table_cell(obligation.get("resolution")),
                controls=_table_cell(_items(obligation.get("source_controls"))),
                description=_table_cell(description),
            )
        )

    lines.extend(
        [
            "",
            "## 派生语义登记",
            "",
            "| 声明 | 主体 | 字段 | 来源控制点／设计决定 | 理由 | 值哈希 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for claim in derivations:
        if not isinstance(claim, dict):
            continue
        subject = "{type}:{id}".format(
            type=_text(claim.get("subject_type")),
            id=_text(claim.get("subject_id")),
        )
        lines.append(
            "| {id} | {subject} | {field} | {sources} | {rationale} | "
            "`{sha}` |".format(
                id=_table_cell(claim.get("id")),
                subject=_table_cell(subject),
                field=_table_cell(claim.get("field")),
                sources=_table_cell(
                    "控制点："
                    + _items(claim.get("source_controls"))
                    + "；决定："
                    + _items(claim.get("source_decisions"))
                ),
                rationale=_table_cell(claim.get("rationale")),
                sha=_table_cell(claim.get("value_sha256")),
            )
        )

    lines.extend(["", "## 单元依赖图", "", "```mermaid", "flowchart TD"])
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = _text(unit.get("id"))
        title = _text(unit.get("title")).replace('"', "'")
        lines.append(f'  {unit_id}["{unit_id} · {title}"]')
    for unit in units:
        if not isinstance(unit, dict):
            continue
        for dependency in unit.get("depends_on", []):
            lines.append(f"  {dependency} --> {unit.get('id')}")
    lines.extend(["```", "", "## 功能单元", ""])

    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = _text(unit.get("id"))
        shift = unit.get("value_shift") if isinstance(unit.get("value_shift"), dict) else {}
        info = unit.get("information") if isinstance(unit.get("information"), dict) else {}
        lines.extend(
            [
                f"### {unit_id} · {_text(unit.get('title'))}",
                "",
                f"- 目的：{_text(unit.get('purpose'))}",
                f"- 来源控制点：{_items(unit.get('source_controls'))}",
                f"- 因果控制点：{_control_items(unit.get('causal_nodes'), controls)}",
                f"- POV 控制点：{_control_items([unit.get('pov')], controls)}",
                f"- 前置状态：{_items(unit.get('preconditions'))}",
                f"- 目标：{_text(unit.get('objective'))}",
                f"- 阻力：{_text(unit.get('obstacle'))}",
                (
                    "- 对抗：{force}；目标：{goal}；手段：{tactic}；筹码："
                    "{leverage}；适应：{adaptation}".format(
                        force=_text(
                            unit.get("opposition", {}).get("force")
                            if isinstance(unit.get("opposition"), dict)
                            else None
                        ),
                        goal=_text(
                            unit.get("opposition", {}).get("goal")
                            if isinstance(unit.get("opposition"), dict)
                            else None
                        ),
                        tactic=_text(
                            unit.get("opposition", {}).get("tactic")
                            if isinstance(unit.get("opposition"), dict)
                            else None
                        ),
                        leverage=_text(
                            unit.get("opposition", {}).get("leverage")
                            if isinstance(unit.get("opposition"), dict)
                            else None
                        ),
                        adaptation=_text(
                            unit.get("opposition", {}).get("adaptation")
                            if isinstance(unit.get("opposition"), dict)
                            else None
                        ),
                    )
                ),
                f"- 选择：{_text(unit.get('choice'))}",
                f"- 选择代价：{_text(unit.get('choice_cost'))}",
                f"- 直接后果：{_text(unit.get('consequence'))}",
                f"- 下一压力：{_text(unit.get('next_pressure'))}",
                f"- 新增设计决定：{_items(unit.get('development_decisions'))}",
                "- 可选路径：",
                *[
                    (
                        "  - [{status}] {option}｜吸引力：{attraction}｜"
                        "代价：{cost}"
                    ).format(
                        status=_text(option.get("status")),
                        option=_text(option.get("option")),
                        attraction=_text(option.get("attraction")),
                        cost=_text(option.get("cost")),
                    )
                    for option in unit.get("choice_options", [])
                    if isinstance(option, dict)
                ],
                (
                    "- 状态变化：{axis}｜{before} → {after}；转折原因：{cause}".format(
                        axis=_text(shift.get("axis")),
                        before=_text(shift.get("before")),
                        after=_text(shift.get("after")),
                        cause=_text(shift.get("turning_cause")),
                    )
                ),
                f"- 建立信息：{_information_items(info.get('establish'), obligations)}",
                f"- 暗示信息：{_information_items(info.get('hint'), obligations)}",
                f"- 暂缓信息：{_information_items(info.get('withhold'), obligations)}",
                f"- 回收信息：{_information_items(info.get('payoff'), obligations)}",
                (
                    "- 世界／权限控制点："
                    f"{_control_items(unit.get('world_constraints'), controls)}"
                ),
                f"- 末态：{_text(unit.get('exit_state'))}",
                f"- 依赖：{_items(unit.get('depends_on'))}",
                f"- 开发自由：{_items(unit.get('creative_freedom'))}",
                f"- 禁止控制点：{_control_items(unit.get('prohibitions'), controls)}",
                f"- 规模建议：{_text(unit.get('scale'))}",
                "",
            ]
        )
    lines.extend(
        [
            "## 终局线程",
            "",
            "| 线程 | 类型 | 终端单元 | 权威完成条件 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for thread in terminal_threads:
        if not isinstance(thread, dict):
            continue
        lines.append(
            "| {id} · {label} | {role} | {unit} | {controls} |".format(
                id=_table_cell(thread.get("id")),
                label=_table_cell(thread.get("label")),
                role=_table_cell(thread.get("role")),
                unit=_table_cell(thread.get("terminal_unit")),
                controls=_table_cell(
                    _control_items(thread.get("source_controls"), controls)
                ),
            )
        )

    lines.extend(["", "## 开放项处理", ""])
    if not open_items:
        lines.append("- 无。")
    for item in open_items:
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"### {_text(item.get('id'))}",
                "",
                f"- 来源控制点：{_text(item.get('source_control'))}",
                f"- 允许处理：{_text(item.get('allowed_handling'))}",
                f"- 禁止裁决：{_text(item.get('forbidden_resolution'))}",
                "",
            ]
        )

    lines.extend(
        [
            "## 开发授权与禁止项",
            "",
            "- 开发者可以在各单元的 `creative_freedom` 范围内设计场景实现。",
            "- 开发者必须遵守控制点、POV、世界／权限、信息责任和单元末态。",
            "- 需要改变控制点、关键选择、世界规则、事实真相或终局线程时，停止开发并退回唯一拥有者。",
            "",
        ]
    )
    return "\n".join(lines)


def render_coverage_matrix(data: dict[str, Any]) -> str:
    controls = _by_id(data.get("control_points"))
    coverage = {
        item.get("control_id"): item
        for item in data.get("coverage", [])
        if isinstance(item, dict)
    }
    open_items = {
        item.get("source_control"): item
        for item in data.get("open_items", [])
        if isinstance(item, dict)
    }
    lines = [
        "# 小说开发地图覆盖矩阵",
        "",
        f"- Run：`{_text(data.get('run_id'))}`",
        f"- 状态：`{_text(data.get('status'))}`",
        "",
    ]
    for area, label in AREA_LABELS.items():
        lines.extend(
            [
                f"## {label}控制区",
                "",
                "| 控制点 | 状态 | 权威证据 | 承载单元 | 覆盖证据 | 未决处理 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for control in controls.values():
            if control.get("area") != area:
                continue
            record = coverage.get(control.get("id"), {})
            source_notes = []
            for source in control.get("sources", []):
                if not isinstance(source, dict):
                    continue
                source_notes.append(
                    "{artifact} / {section}: {evidence}".format(
                        artifact=_text(source.get("artifact_id")),
                        section=_text(source.get("section")),
                        evidence=_text(source.get("evidence")),
                    )
                )
            open_item = open_items.get(control.get("id"), {})
            handling = "—"
            if open_item:
                handling = "{allowed}；禁止：{forbidden}".format(
                    allowed=_text(open_item.get("allowed_handling")),
                    forbidden=_text(open_item.get("forbidden_resolution")),
                )
            lines.append(
                "| {id} | {status} | {sources} | {units} | {evidence} | {handling} |".format(
                    id=_table_cell(control.get("id")),
                    status=_table_cell(record.get("status")),
                    sources=_table_cell("；".join(source_notes)),
                    units=_table_cell(_items(record.get("unit_ids"))),
                    evidence=_table_cell(record.get("evidence")),
                    handling=_table_cell(handling),
                )
            )
        lines.append("")
    return "\n".join(lines)


def render_map_check(data: dict[str, Any], result: dict[str, Any]) -> str:
    checks = data.get("semantic_checks")
    checks = checks if isinstance(checks, dict) else {}
    lines = [
        "# 小说开发地图检查报告",
        "",
        "## 输入真实性",
        "",
        f"- Run：`{_text(data.get('run_id'))}`",
        f"- 权威来源数：{len(data.get('source_artifacts', []))}",
        "- 所有控制点证据必须精确落在哈希绑定的权威设计稿章节中。",
        "",
        "## 结构验收",
        "",
        f"- 控制点数：{len(data.get('control_points', []))}",
        f"- 功能单元数：{len(data.get('units', []))}",
        f"- 终局线程数：{len(data.get('terminal_threads', []))}",
        f"- 开放项数：{len(data.get('open_items', []))}",
        "",
        "## 语义复核",
        "",
    ]
    for check_id, label in SEMANTIC_LABELS.items():
        check = checks.get(check_id, {})
        if not isinstance(check, dict):
            check = {}
        lines.extend(
            [
                f"### {label} · `{check_id}`",
                "",
                f"- 状态：{_text(check.get('status'))}",
                f"- 评审者：{_text(check.get('reviewer_id'))}（{_text(check.get('reviewer_role'))}）",
                f"- 方法：{_text(check.get('method'))}",
                f"- 检查对象：{_items(check.get('subject_ids'))}",
            ]
        )
        evidence = check.get("evidence") if isinstance(check.get("evidence"), list) else []
        for index, item in enumerate(evidence, start=1):
            if not isinstance(item, dict):
                continue
            lines.append(
                "- 证据 {index}：{claim}｜控制点：{controls}｜单元：{units}".format(
                    index=index,
                    claim=_text(item.get("claim")),
                    controls=_items(item.get("control_ids")),
                    units=_items(item.get("unit_ids")),
                )
            )
        lines.append("")

    handoff = data.get("handoff_self_test")
    handoff = handoff if isinstance(handoff, dict) else {}
    lines.extend(
        [
            f"### {HANDOFF_LABEL} · `handoff_self_test`",
            "",
            f"- 状态：{_text(handoff.get('status'))}",
            f"- 执行者：{_text(handoff.get('reviewer_id'))}（{_text(handoff.get('reviewer_role'))}）",
            f"- 保障级别：{_text(handoff.get('assurance'))}",
            f"- 方法：{_text(handoff.get('method'))}",
            f"- 证据范围：{_text(handoff.get('evidence_scope'))}",
        ]
    )
    for task in handoff.get("tasks", []):
        if not isinstance(task, dict):
            continue
        lines.append(
            "- 任务 `{id}`（{status}）：{response}｜证据：{evidence}".format(
                id=_text(task.get("id")),
                status=_text(task.get("status")),
                response=_text(task.get("response")),
                evidence=_items(task.get("evidence_ids")),
            )
        )
    lines.append("")

    lines.extend(["## 风险与回退", ""])
    blockers = (
        data.get("declared_blockers")
        if isinstance(data.get("declared_blockers"), list)
        else []
    )
    if not blockers:
        lines.append("- 无声明 blocker。")
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        lines.append(
            "- `{id}` → {owner}：{problem}；需要：{decision}".format(
                id=_text(blocker.get("id")),
                owner=_text(blocker.get("owner_stage")),
                problem=_text(blocker.get("problem")),
                decision=_text(blocker.get("required_decision")),
            )
        )
    errors = result.get("errors") if isinstance(result.get("errors"), list) else []
    actual_blockers = (
        result.get("blockers") if isinstance(result.get("blockers"), list) else []
    )
    lines.extend(["", "## 权威验证结果", ""])
    if not errors and not actual_blockers:
        lines.append("- 未发现结构、来源或准入错误。")
    for message in actual_blockers:
        lines.append(f"- BLOCKER：{_text(message)}")
    for message in errors:
        lines.append(f"- ERROR：{_text(message)}")
    lines.extend(["", f"verdict: {_text(result.get('verdict'), 'revise')}", ""])
    return "\n".join(lines)


def render_content_documents(data: dict[str, Any]) -> dict[str, str]:
    return {
        "development-map.md": render_development_map(data),
        "coverage-matrix.md": render_coverage_matrix(data),
    }


def render_all(
    data: dict[str, Any], result: dict[str, Any]
) -> dict[str, str]:
    return {
        **render_content_documents(data),
        "map-check.md": render_map_check(data, result),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Render D1 Markdown documents from map-data.json."
    )
    parser.add_argument("package_directory", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that existing Markdown exactly matches deterministic rendering.",
    )
    args = parser.parse_args(argv)
    package_dir = args.package_directory.resolve()
    try:
        data = json.loads(
            (package_dir / "map-data.json").read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load map-data.json: {exc}", file=sys.stderr)
        return 2
    rendered = render_content_documents(data)
    mismatches: list[str] = []
    for filename, text in rendered.items():
        path = package_dir / filename
        expected = text.rstrip() + "\n"
        if args.check:
            try:
                actual = path.read_text(encoding="utf-8-sig")
            except OSError:
                mismatches.append(filename)
                continue
            if actual != expected:
                mismatches.append(filename)
        else:
            path.write_text(expected, encoding="utf-8")
    if mismatches:
        print("FAIL: stale rendered documents: " + ", ".join(mismatches))
        return 1
    print("OK: content documents are current; the validator owns map-check.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
