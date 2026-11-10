#!/usr/bin/env python3
"""Begin and advance a D1 autonomous generation session."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from d1_generation_session import begin_session, read_json, submit_phase


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    begin = sub.add_parser("begin")
    begin.add_argument("input_gate", type=Path)
    begin.add_argument("workspace", type=Path)
    begin.add_argument("--run-id", required=True)
    begin.add_argument("--executor-id", required=True)
    begin.add_argument("--method", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("workspace", type=Path)
    submit.add_argument("phase")
    submit.add_argument("artifact", type=Path)
    submit.add_argument("--summary", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "begin":
        input_gate = read_json(args.input_gate.resolve())
        result = begin_session(
            args.workspace,
            run_id=args.run_id,
            executor_id=args.executor_id,
            method=args.method,
            input_gate=input_gate,
        )
    else:
        result = submit_phase(
            args.workspace,
            phase=args.phase,
            artifact=args.artifact,
            summary=args.summary,
        )
    print(json.dumps({"written": str(result.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
