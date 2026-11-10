from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from common import (
    ContractError,
    SKILL_NAME,
    all_skill_files,
    require,
    sha256_file,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind a generated plan to this skill.")
    parser.add_argument("phase", choices=["plan"])
    parser.add_argument("package", type=Path)
    parser.add_argument("--executor-id", required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()
    try:
        package = args.package.resolve()
        plan = package / "review-plan.json"
        inventory = package / "source-inventory.json"
        briefs = package / "fragment-briefs.json"
        for target in (plan, inventory, briefs):
            require(target.is_file(), f"missing output: {target.name}")
        skill_dir = Path(__file__).resolve().parent.parent
        skill_files = [
            {
                "path": str(path.relative_to(skill_dir)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for path in all_skill_files(skill_dir)
        ]
        record = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "autonomous_agent",
            "phase": args.phase,
            "executor_id": args.executor_id,
            "task_id": args.task_id,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "skill_files": skill_files,
            "inputs": {
                "source-inventory.json": sha256_file(inventory),
            },
            "outputs": {
                "review-plan.json": sha256_file(plan),
                "fragment-briefs.json": sha256_file(briefs),
            },
        }
        write_json(package / "execution-record.json", record)
    except ContractError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(f"READY: execution record bound to {len(skill_files)} skill files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
