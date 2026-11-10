#!/usr/bin/env python3
"""Execute one sealed HB0 work order."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hb0_runtime import RuntimeFailure, execute


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_order", type=Path)
    args = parser.parse_args()
    try:
        code, result = execute(args.work_order)
    except (OSError, ValueError, RuntimeFailure) as error:
        print(json.dumps({"status": "runtime_error", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": result["result"], "stage_result": str(args.work_order.resolve().parent / "stage-result.json")}, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
