from __future__ import annotations

import argparse
import copy
import datetime as dt
import sys
from pathlib import Path

from common import (
    ContractError,
    SKILL_NAME,
    sha256_file,
    write_json,
)
from render_human_review import render_report
from validate_human_review import (
    _validate_fragment_package,
    _validate_reading_budget,
    validate_assembly_package,
    validate_plan_package,
)
from common import load_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically assemble a human-review content package."
    )
    parser.add_argument("plan_package", type=Path)
    parser.add_argument("fragment_package", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    try:
        plan_dir = args.plan_package.resolve()
        fragment_dir = args.fragment_package.resolve()
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        validate_plan_package(plan_dir, args.r1.resolve())
        plan_path = plan_dir / "review-plan.json"
        plan = load_json(plan_path)
        inventory = load_json(plan_dir / "source-inventory.json")
        fragment_result = _validate_fragment_package(
            fragment_dir,
            plan,
            plan_path,
            set(inventory["fragment_eligible_source_ids"]),
            args.r1.resolve(),
        )
        fragment_by_id = {item["id"]: item for item in fragment_result["fragments"]}
        blueprint = copy.deepcopy(plan["report_blueprint"])
        slots = blueprint["fragments"].pop("slots")
        items = []
        for slot in slots:
            sample = fragment_by_id[slot["id"]]
            items.append(
                {
                    "id": slot["id"],
                    "title": slot["title"],
                    "purpose": slot["purpose"],
                    "review_question": slot["review_question"],
                    "text": sample["text"],
                    "coverage_targets": slot["coverage_targets"],
                    "source_ids": sample["source_ids"],
                }
            )
        blueprint["fragments"]["items"] = items
        synthetic = {
            "review_contract": plan["review_contract"],
            "reading_budget": plan["reading_budget"],
            "report_blueprint": blueprint,
        }
        reading = _validate_reading_budget(synthetic, assembled=True)
        report = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": plan["run_id"],
            "status": "ready",
            "source_bindings": {
                "source_inventory_sha256": sha256_file(plan_dir / "source-inventory.json"),
                "review_plan_sha256": sha256_file(plan_path),
                "fragment_package_sha256": sha256_file(fragment_dir / "fragment-package.json"),
            },
            "review_contract": plan["review_contract"],
            "reading_budget": plan["reading_budget"],
            "reading_measurement": reading,
            "report_blueprint": blueprint,
            "coverage_ledger": plan["coverage_ledger"],
            "review_tasks": plan["review_tasks"],
            "traceability": {
                "fragment_evidence": fragment_result["fragments"],
            },
        }
        report_path = output / "human-review-report.json"
        write_json(report_path, report)
        markdown_path = output / "human-review-report.md"
        markdown_path.write_text(render_report(report), encoding="utf-8")
        execution = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "deterministic_assembly",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "review_plan_sha256": sha256_file(plan_path),
            "fragment_package_sha256": sha256_file(fragment_dir / "fragment-package.json"),
            "outputs": {
                "human-review-report.json": sha256_file(report_path),
                "human-review-report.md": sha256_file(markdown_path),
            },
        }
        execution_path = output / "assembly-execution.json"
        write_json(execution_path, execution)
        manifest = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": plan["run_id"],
            "stage": "H1",
            "verdict": "ready",
            "files": [
                {"path": path.name, "sha256": sha256_file(path)}
                for path in (report_path, markdown_path, execution_path)
            ],
            "author_review_artifact": {
                "path": "human-review-report.json",
                "sha256": sha256_file(report_path),
            },
        }
        write_json(output / "package-manifest.json", manifest)
        evidence = validate_assembly_package(
            output,
            plan_dir,
            fragment_dir,
            args.r1.resolve(),
        )
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "mode": "assemble",
                "verdict": "ready",
                "errors": [],
                "evidence": evidence,
            },
        )
    except ContractError as exc:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "mode": "assemble",
                "verdict": "blocked",
                "errors": [str(exc)],
                "evidence": {},
            },
        )
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(
        f"READY: assembled {len(items)} fragments; "
        f"estimated {reading['measured_total_minutes']:.2f} minutes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
