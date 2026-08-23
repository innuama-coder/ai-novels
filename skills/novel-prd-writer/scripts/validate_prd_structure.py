#!/usr/bin/env python3
"""Validate objective structure gates for novel PRD artifacts.

This script intentionally checks only deterministic gates. It does not judge
semantic quality; use docs/evaluation-spec.md for subjective review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "summary": r"##\s*1\.\s*(摘要|概要|概述)|##\s*(摘要|概要|概述)",
    "core_concept": r"核心概念|核心矛盾",
    "role_requirements": r"角色需求|角色定义",
    "setting_requirements": r"设定需求|设定要求|核心设定|世界观规则",
    "route_plot": r"路线与情节约定|路线需求|路线与情节约束|情节约定",
    "theme_style": r"主题、风格与叙事约束|主题与风格约束|风格需求|叙事约束",
    "acceptance": r"内容验收基准|内容约束矩阵|成功标准",
    "risks": r"风险与开放问题|开放问题",
}

REQUIRED_TERMS = {
    "must": r"\bMust\b|必须",
    "wont": r"\bWon'?t\b|明确不做|不得|禁止",
}

FORBIDDEN_PATTERNS = {
    "market_metrics": r"市场规模|市场指标|商业指标|商业目标|商业可行性|目标读者画像|同类定位|市场定位|读者增长|销售目标|转化率|留存率",
    "chapter_outline": r"\b30\s*章\b|第[一二三四五六七八九十\d]+章|章节大纲",
    "key_scene_table": r"关键场景表|场景顺序|节点顺序",
    "prose_output": r"第一章正文|小说正文如下|正文：",
    "scene_detail": r"光线.*声音.*动作|对白方向|场景蓝图",
}

NEGATION_MARKERS = (
    "不得",
    "禁止",
    "不使用",
    "不写",
    "不会",
    "不能",
    "不可",
    "明确不做",
    "Won't",
    "Wont",
)


def validate(text: str) -> dict:
    failures: list[dict] = []

    for name, pattern in REQUIRED_PATTERNS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            failures.append({"type": "missing_required_section", "name": name})

    for name, pattern in REQUIRED_TERMS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            failures.append({"type": "missing_required_term", "name": name})

    for name, pattern in FORBIDDEN_PATTERNS.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not re.search(pattern, line, flags=re.IGNORECASE):
                continue
            if any(marker.lower() in line.lower() for marker in NEGATION_MARKERS):
                continue
            failures.append({"type": "forbidden_content", "name": name, "line": line_no})
            break

    return {
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate novel PRD structure gates.")
    parser.add_argument("path", help="Path to a PRD markdown artifact.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args()

    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    result = validate(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} failures={result['failure_count']}")
        for failure in result["failures"]:
            print(f"- {failure['type']}: {failure['name']}")

    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
