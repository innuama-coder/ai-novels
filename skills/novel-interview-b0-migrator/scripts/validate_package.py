#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from migration_lib import MigrationError, validate_candidate_dir, validate_final_dir


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_package.py <candidate-or-final-directory>", file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve()
    try:
        if (root / "migration-finalization.json").is_file():
            validate_final_dir(root)
            kind = "finalized"
        elif (root / "candidate-manifest.json").is_file():
            validate_candidate_dir(root)
            kind = "waiting_author"
        else:
            raise MigrationError("directory has neither package root manifest")
    except (MigrationError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"OK: migration package is valid ({kind})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
