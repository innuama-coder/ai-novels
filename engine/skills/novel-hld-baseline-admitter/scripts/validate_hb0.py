#!/usr/bin/env python3
"""Independently reproduce and validate an existing HB0 result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hb0_runtime import RuntimeFailure, validate_existing


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_order", type=Path)
    args = parser.parse_args()
    try:
        result = validate_existing(args.work_order)
    except (OSError, ValueError, RuntimeFailure) as error:
        print(json.dumps({"status": "fail", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
