#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from migration_lib import MigrationError, finalize_candidate


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: finalize_migration.py <candidate-directory> <compatibility-decision.json> <new-final-directory>", file=sys.stderr)
        return 2
    try:
        result = finalize_candidate(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    except (MigrationError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"OK: compatibility migration finalized: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
