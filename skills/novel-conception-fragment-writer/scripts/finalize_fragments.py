from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

from common import (
    PHASE_FILES,
    PHASES,
    SKILL_NAME,
    STYLE_CONTRACT,
    ContractError,
    all_skill_files,
    load_json,
    require,
    sha256_file,
    validate_style_text,
    write_json,
)
from render_fragments import render
from validate_fragments import validate_package


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically finalize a staged fragment writing session."
    )
    parser.add_argument("workspace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        workspace = args.workspace.resolve()
        session = load_json(workspace / "generation-session.json")
        require(session.get("status") == "ready_to_finalize", "session is not complete")
        plan_dir = Path(session["inputs"]["plan_directory"])
        r1_dir = Path(session["inputs"]["r1_directory"])
        output.mkdir(parents=True, exist_ok=True)
        evidence_out = output / "generation-evidence"
        evidence_out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            workspace / "generation-session.json",
            output / "generation-session.json",
        )
        for phase in PHASES:
            shutil.copyfile(
                workspace / "generation-evidence" / PHASE_FILES[phase],
                evidence_out / PHASE_FILES[phase],
            )
        audit = load_json(evidence_out / PHASE_FILES["revision-audit"])
        briefs = load_json(plan_dir / "fragment-briefs.json")
        slots = {item["id"]: item for item in briefs["slots"]}
        fragments = []
        for item in audit["fragments"]:
            metrics = validate_style_text(item["final_text"], slots[item["id"]], item["id"])
            fragments.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "text": item["final_text"],
                    "source_ids": item["source_ids"],
                    "control_ids": item["control_ids"],
                    "unit_ids": item["unit_ids"],
                    "creative_choices": item["creative_choices"],
                    "introduced_authoritative_facts": item[
                        "introduced_authoritative_facts"
                    ],
                    "contract_checks": item["contract_checks"],
                    "scene_audit": item["scene_audit"],
                    "brief_compliance": item["brief_compliance"],
                    "style_metrics": metrics,
                }
            )
        package = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": session["run_id"],
            "status": "ready",
            "review_plan_sha256": sha256_file(plan_dir / "review-plan.json"),
            "style_contract": STYLE_CONTRACT,
            "fragments": fragments,
        }
        fragment_path = output / "fragment-package.json"
        write_json(fragment_path, package)
        preview_path = output / "fragments.md"
        preview_path.write_text(render(package), encoding="utf-8")
        skill_dir = Path(__file__).resolve().parent.parent
        execution = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "autonomous_agent",
            "executor_id": session["executor_id"],
            "task_id": session["task_id"],
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "review_plan_sha256": sha256_file(plan_dir / "review-plan.json"),
            "fragment_package_sha256": sha256_file(fragment_path),
            "inputs": {
                "fragment-briefs.json": sha256_file(
                    plan_dir / "fragment-briefs.json"
                ),
                "source-inventory.json": sha256_file(
                    plan_dir / "source-inventory.json"
                ),
            },
            "phases": {
                phase: sha256_file(evidence_out / PHASE_FILES[phase])
                for phase in PHASES
            },
            "skill_files": [
                {
                    "path": str(path.relative_to(skill_dir)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                }
                for path in all_skill_files(skill_dir)
            ],
            "outputs": {
                "fragment-package.json": sha256_file(fragment_path),
                "fragments.md": sha256_file(preview_path),
            },
        }
        execution_path = output / "execution-record.json"
        write_json(execution_path, execution)
        package_files = [
            output / "generation-session.json",
            *[evidence_out / PHASE_FILES[phase] for phase in PHASES],
            fragment_path,
            preview_path,
            execution_path,
        ]
        manifest = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": session["run_id"],
            "stage": "F1",
            "verdict": "ready",
            "files": [
                {
                    "path": str(path.relative_to(output)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                }
                for path in package_files
            ],
            "fragment_package": {
                "path": "fragment-package.json",
                "sha256": sha256_file(fragment_path),
            },
        }
        write_json(output / "package-manifest.json", manifest)
        evidence = validate_package(output, plan_dir, r1_dir)
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "mode": "fragment-writing",
                "verdict": "ready",
                "errors": [],
                "evidence": {
                    "review_plan_sha256": sha256_file(
                        plan_dir / "review-plan.json"
                    ),
                    "fragment_package_sha256": sha256_file(fragment_path),
                    "execution_record_sha256": sha256_file(execution_path),
                    **evidence,
                },
            },
        )
    except ContractError as exc:
        output.mkdir(parents=True, exist_ok=True)
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "mode": "fragment-writing",
                "verdict": "blocked",
                "errors": [str(exc)],
                "evidence": {},
            },
        )
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(f"READY: finalized {len(fragments)} fiction review fragments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
