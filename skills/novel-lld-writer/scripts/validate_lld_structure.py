#!/usr/bin/env python3
"""Validate objective structure gates for novel LLD artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "hld_trace": r"HLD\s*引用|HLD\s*确认|HLD\s*输入|架构继承",
    "character_detail": r"角色详细设计|角色设计|行为标记",
    "space_detail": r"空间详细设计|空间设计|感官矩阵",
    "route_material": r"路线节点|材料化|路线.*材料",
    "scene_blueprint": r"关键场景设计|场景蓝图|场景设计",
    "sensory_callback": r"感官|回调材料|callback",
    "writing_guidance": r"写作指引|禁用项|Writing Agent",
    "handoff": r"Writing Agent\s*交付|交付包",
}

FORBIDDEN_PATTERNS = {
    "prd_redefinition": r"重新定义PRD|新的核心矛盾|改写PRD方向",
    "hld_redefinition": r"重新定义HLD|新的主线|新的角色弧线|改写场景功能",
    "prose": r"小说正文如下|第一章正文|正文：",
    "line_dialogue": r"逐行对白|完整对白稿",
}

NEGATION_MARKERS = ("不得", "禁止", "不写", "不能", "不可", "不要", "Won't", "明确不做")


def validate(text: str) -> dict:
    failures: list[dict] = []
    for name, pattern in REQUIRED_PATTERNS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            failures.append({"type": "missing_required_section", "name": name})

    for name, pattern in FORBIDDEN_PATTERNS.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not re.search(pattern, line, flags=re.IGNORECASE):
                continue
            if any(marker.lower() in line.lower() for marker in NEGATION_MARKERS):
                continue
            failures.append({"type": "forbidden_content", "name": name, "line": line_no})
            break

    return {"status": "pass" if not failures else "fail", "failure_count": len(failures), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate novel LLD structure gates.")
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
