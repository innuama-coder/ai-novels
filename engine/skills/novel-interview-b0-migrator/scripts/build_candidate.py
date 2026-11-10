#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from migration_lib import MigrationError, build_candidate


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: build_candidate.py <projection-plan.json> <new-candidate-directory>", file=sys.stderr)
        return 2
    try:
        result = build_candidate(Path(argv[1]), Path(argv[2]))
    except (MigrationError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"OK: waiting-author migration candidate: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
