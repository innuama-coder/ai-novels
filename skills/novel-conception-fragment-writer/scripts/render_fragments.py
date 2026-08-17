from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import load_json


def render(package: dict[str, Any]) -> str:
    lines = [
        "# 小说构思评审片段",
        "",
        "> 以下内容用于构思评审，不是最终正文或新的设定权威。",
        "",
        f"固定文风：{package['style_contract']['name']}",
        "",
    ]
    for fragment in package["fragments"]:
        lines.extend(
            [
                f"## {fragment['title']}",
                "",
                fragment["text"],
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render fragment package as Markdown.")
    parser.add_argument("package", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(render(load_json(args.package)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
