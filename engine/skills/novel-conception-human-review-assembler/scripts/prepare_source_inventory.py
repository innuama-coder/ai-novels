from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import ContractError, build_source_inventory, write_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a technically ready R1 package and extract review subjects."
    )
    parser.add_argument("r1_package", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        inventory = build_source_inventory(args.r1_package)
        write_json(args.output, inventory)
    except ContractError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(
        f"READY: {len(inventory['review_subjects'])} review subjects, "
        f"{len(inventory['known_source_ids'])} known source ids"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
