from __future__ import annotations

import argparse
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = SKILL_ROOT.parents[1] / "harnesses" / "novel-hld-autonomous"
sys.path.insert(0, str(HARNESS_ROOT))

from runtime.review_stage_runtime import execute  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_order", type=Path)
    parser.add_argument("draft_dir", type=Path)
    args = parser.parse_args()
    return execute(SKILL_ROOT, args.work_order.resolve(), args.draft_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
