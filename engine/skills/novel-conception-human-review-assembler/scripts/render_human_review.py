from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import load_json


def _text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return ""
    for key in ("text", "summary", "definition", "instruction"):
        value = item.get(key)
        if isinstance(value, str):
            return value
    return ""


def _bullets(items: list[Any], field: str = "text") -> list[str]:
    lines: list[str] = []
    for item in items:
        if isinstance(item, str):
            lines.append(f"- {item}")
            continue
        title = item.get("title") or item.get("name") or item.get("label") or ""
        content = item.get(field) or item.get("summary") or item.get("commitment") or ""
        label = f"**{title}**：" if title else ""
        lines.append(f"- {label}{content}")
    return lines


def render_report(report: dict[str, Any]) -> str:
    bp = report["report_blueprint"]
    lines = ["# 小说构思人审报告", ""]
    orientation = bp["orientation"]
    lines.extend(
        [
            "## 快速定向",
            "",
            _text(orientation["story_identity"]),
            "",
            "### 这是",
            "",
            *_bullets(orientation["this_is"]),
            "",
            "### 这不是",
            "",
            *_bullets(orientation["this_is_not"]),
            "",
            _text(orientation["review_instruction"]),
            "",
            "### 构思控制总链",
            "",
        ]
    )
    for layer in orientation["logic_spine"]:
        lines.append(
            f"- **{layer['title']}**：{layer['claim']} → {layer['therefore']}；"
            f"控制：{layer['controls']}；边界：{layer['boundary']}"
        )
    lines.append("")

    world = bp["world"]
    lines.extend(["## 1. 世界设定", "", _text(world["definition"]), "", "### 运行系统", ""])
    for item in world["systems"]:
        lines.append(f"- **{item['name']}**：{item['control_summary']}")
    lines.extend(["", "### 主要环境", ""])
    for item in world["environments"]:
        lines.append(f"- **{item['name']}**：{item['control_summary']}")
    lines.extend(["", "### 边界与开放接口", ""])
    lines.extend(_bullets(world["boundaries"], "commitment"))
    lines.extend(_bullets(world["open_interfaces"], "text"))
    lines.extend(["", f"> 评审问题：{world['review_question']}", ""])

    story = bp["story"]
    definition = story["definition"]
    lines.extend(
        [
            "## 2. 故事线定义",
            "",
            f"**故事承诺**：{definition['promise']}",
            "",
            f"**戏剧问题**：{definition['dramatic_question']}",
            "",
            f"**起点 → 终点**：{definition['start']} → {definition['end']}",
            "",
            f"**赌注**：{definition['stakes']}",
            "",
            "### 主线、支线与背景线",
            "",
        ]
    )
    for line in story["lines"]:
        lines.append(f"- **{line['name']}（{line['kind']}）**：{line['control_summary']}")
    lines.extend(
        [
            "",
            "### 多线时间线",
            "",
            "| 阶段 | 压力 | 选择 | 后果与代价 | 新状态 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for stage in story["timeline"]:
        lines.append(
            f"| {stage['label']} | {stage['pressure']} | {stage['choice']} | "
            f"{stage['consequence']}；{stage['cost']} | {stage['new_state']} |"
        )
    lines.extend(["", "### 主要事件控制链", ""])
    for event in story["event_controls"]:
        lines.append(
            f"- **{event['name']} · {event['role']}**：{event['logic']}；"
            f"控制：{event['controls']}"
        )
    lines.extend(["", "### 叙述约束与开放接口", ""])
    lines.extend(_bullets(story["narrative_constraints"], "text"))
    lines.extend(_bullets(story["open_interfaces"], "text"))
    lines.extend(["", f"> 评审问题：{story['review_question']}", ""])

    characters = bp["characters"]
    lines.extend(["## 3. 角色定义", "", _text(characters["definition"]), "", "### 核心人物", ""])
    for profile in characters["profiles"]:
        lines.extend(
            [
                f"#### {profile['name']} · {profile['role']}",
                "",
                profile["control_summary"],
                "",
            ]
        )
    lines.extend(["### 三层关系变化", ""])
    for layer in characters["relationship_layers"]:
        lines.append(
            f"- **第{layer['layer']}层 · {layer['function']}**：{layer['control_summary']}"
        )
    lines.extend(["", f"> 评审问题：{characters['review_question']}", ""])

    fragments = bp["fragments"]
    lines.extend(["## 4. 小说片段", "", fragments["sample_authority"], ""])
    for item in fragments["items"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"**要验证什么**：{item['purpose']}",
                "",
                item["text"],
                "",
                f"> 评审问题：{item['review_question']}",
                "",
            ]
        )
    lines.extend([f"> 总体评审问题：{fragments['review_question']}", ""])

    decision = bp["decision"]
    lines.extend(["## 作者判断", "", decision["instruction"], ""])
    labels = {"world": "世界", "story": "故事", "characters": "人物", "fragments": "片段"}
    for key in ("world", "story", "characters", "fragments"):
        lines.append(f"- **{labels[key]}**：{decision['questions'][key]}")
    if decision["open_items"]:
        lines.extend(["", "### 仍然开放", ""])
        lines.extend(_bullets(decision["open_items"], "text"))
    lines.extend(
        [
            "",
            "请选择：`approve`（进入开发） / `revise`（指出需要调整的板块与原因）",
            "",
            f"_预计阅读：{report['reading_measurement']['measured_total_minutes']:.2f} 分钟；"
            "该数值依据包内可校准阅读参数估算。_",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render report JSON as deterministic Markdown.")
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = load_json(args.report)
    args.output.write_text(render_report(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
