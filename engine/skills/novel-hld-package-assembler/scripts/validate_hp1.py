#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from hp1_runtime import validate_existing

def main() -> int:
    parser = argparse.ArgumentParser(description="Independently validate an HP1 delivery")
    parser.add_argument("work_order", type=Path)
    args = parser.parse_args()
    try:
        result = validate_existing(args.work_order)
    except Exception as error:
        print(json.dumps({"status": "fail", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
