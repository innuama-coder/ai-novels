#!/usr/bin/env python3
"""Validate a complete ready or blocked development-baseline package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from baseline_runtime import (
    ContractFailure,
    RuntimeFailure,
    load_request,
    validate_package,
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="preparation-request.json")
    args = parser.parse_args()
    try:
        context = load_request(args.request)
        result = validate_package(context)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, ContractFailure, RuntimeFailure) as error:
        print(json.dumps({"status": "fail", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
