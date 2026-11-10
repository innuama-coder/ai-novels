from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import ContractError, SKILL_NAME, load_json, require, sha256_file, write_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically export fragment briefs from a review plan."
    )
    parser.add_argument("review_plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        plan = load_json(args.review_plan)
        require(plan.get("skill") == SKILL_NAME, "review plan skill mismatch")
        require(plan.get("status") == "ready", "review plan is not ready")
        fragments = plan.get("report_blueprint", {}).get("fragments", {})
        slots = fragments.get("slots")
        require(isinstance(slots, list) and slots, "fragment slots missing")
        output = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": plan.get("run_id"),
            "status": "ready",
            "review_plan_sha256": sha256_file(args.review_plan),
            "source_inventory_sha256": plan.get("source_inventory_sha256"),
            "sample_authority": fragments.get("sample_authority"),
            "slots": slots,
            "writer_output_contract": {
                "skill": "novel-conception-fragment-writer",
                "required_files": [
                    "fragment-package.json",
                    "execution-record.json",
                    "validation.json",
                ],
                "verdict": "ready",
                "introduced_authoritative_facts": [],
                "required_contract_checks": [
                    "source_grounding",
                    "narrative_contract",
                    "no_new_authority",
                    "review_question_fit",
                ],
            },
        }
        write_json(args.output, output)
    except ContractError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(f"READY: exported {len(slots)} fragment briefs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
