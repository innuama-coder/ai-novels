#!/usr/bin/env python3
"""Prepare one ready or blocked novel-development baseline package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from baseline_runtime import RuntimeFailure, prepare


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="preparation-request.json")
    args = parser.parse_args()
    try:
        code, result = prepare(args.request)
    except (OSError, ValueError, RuntimeFailure) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
