#!/usr/bin/env python3
"""Render a complete user-reviewable Markdown interview report from append-only events."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: render_report.py <session-directory>", file=sys.stderr)
        return 2
    session = Path(argv[1]).resolve()
    plans = [json.loads(path.read_text(encoding="utf-8-sig")) for path in sorted(session.glob("plan.v*.json"))]
    if not plans:
        print("missing plan.vN.json", file=sys.stderr)
        return 1
    events = [json.loads(line) for line in (session / "events.ndjson").read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    plan = plans[-1]
    lines = [
        f"# {plan['stage']} 访谈完整记录",
        "",
        "## 访谈计划",
        f"- 会话：`{plan['session_id']}`；计划版本：{plan['revision']}；问题数：{plan['question_budget']}；预计：{plan['planned_minutes']} 分钟。",
        f"- 记录保证：`{plan['transcript_assurance']}`。" + (" 本报告为自记录的完整工作记录，不宣称为外部事件回放。" if plan['transcript_assurance'] == 'self_recorded' else " 已声明外部事件来源：`%s`。" % plan.get('event_source', '未注明')),
        "- 分组预算：" + "；".join(f"{item['id']} {item['budget']} 问" for item in plan['groups']) + "。",
        "",
        "## 逐轮记录"
    ]
    answers = {event.get("question_id"): event for event in events if event.get("type") == "author_answer"}
    for event in events:
        if event.get("type") == "question":
            question_id = event.get("question_id", "?")
            lines += [f"### 问题 {question_id}（{event.get('group_id', '?')}）", event["text"], "", "**作者回答**", answers.get(question_id, {}).get("text", "【尚未回答】"), ""]
        elif event.get("type") not in {"author_answer"}:
            label = {"agent_recap": "阶段复述", "decision": "决定", "plan_revision": "计划变更", "stage_close": "结束决定"}.get(event.get("type"), event.get("type", "事件"))
            lines += [f"### {label} #{event.get('seq')}", event["text"], ""]
    lines += ["## 证据状态", "请以同目录 `validation.json` 的 verdict 为准；本报告不自行宣布通过。", ""]
    (session / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(session / "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
