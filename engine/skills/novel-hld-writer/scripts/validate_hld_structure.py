#!/usr/bin/env python3
"""Validate objective structure gates for novel HLD artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "prd_trace": r"PRD\s*引用|PRD\s*确认|PRD\s*输入|需求继承",
    "role_architecture": r"角色架构|角色体系|角色关系",
    "route_architecture": r"路线架构|线索架构|Thread|线程",
    "plot_architecture": r"情节结构|关键场景功能|关键场景生成",
    "space_architecture": r"空间架构",
    "time_architecture": r"时间架构",
    "pacing_pov": r"节奏架构|视角架构|POV",
    "style_rules": r"风格与用语|风格规范|表达规则",
    "lld_handoff": r"LLD\s*交付|HLD→LLD|HLD->LLD|交付包",
}

FORBIDDEN_PATTERNS = {
    "prose": r"小说正文如下|第一章正文|正文：",
    "dialogue": r"逐行对白|具体对白|他说：|她说：",
    "scene_blueprint": r"场景蓝图|画面展开|光线.*声音.*动作|触觉.*气味",
    "prd_redefinition": r"重新定义PRD|改写PRD|新的核心矛盾",
}

NEGATION_MARKERS = ("不得", "禁止", "不写", "不能", "不可", "不进入", "不要", "Won't", "明确不做")


def is_allowed_forbidden_match(name: str, line: str) -> bool:
    """Allow boundary mentions that point the work to LLD instead of doing it."""

    normalized = line.lower()
    if any(marker.lower() in normalized for marker in NEGATION_MARKERS):
        return True
    if name == "scene_blueprint" and "lld" in normalized:
        return True
    return False


def validate(text: str) -> dict:
    failures: list[dict] = []
    for name, pattern in REQUIRED_PATTERNS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            failures.append({"type": "missing_required_section", "name": name})

    for name, pattern in FORBIDDEN_PATTERNS.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not re.search(pattern, line, flags=re.IGNORECASE):
                continue
            if is_allowed_forbidden_match(name, line):
                continue
            failures.append({"type": "forbidden_content", "name": name, "line": line_no})
            break

    return {"status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate novel HLD structure gates.")
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(Path(args.path).read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} failures={result['failure_count']}")
        for failure in result["failures"]:
            print(f"- {failure['type']}: {failure['name']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
