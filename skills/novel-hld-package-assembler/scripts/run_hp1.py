#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from hp1_runtime import RuntimeFailure, execute

def main() -> int:
    parser = argparse.ArgumentParser(description="Execute deterministic HP1 assembly")
    parser.add_argument("work_order", type=Path)
    args = parser.parse_args()
    try:
        code, result = execute(args.work_order)
    except Exception as error:
        print(json.dumps({"status": "runtime_error", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": result["result"], "stage_result": str(args.work_order.parent / "stage-result.json")}, ensure_ascii=False))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
