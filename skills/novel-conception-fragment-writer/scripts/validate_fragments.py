from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import (
    PHASE_FILES,
    PHASES,
    SKILL_NAME,
    STYLE_CONTRACT,
    ContractError,
    all_skill_files,
    ensure_exact_ids,
    load_json,
    meaningful,
    require,
    sha256_file,
    validate_audit,
    validate_style_text,
    verify_manifest,
    write_json,
)
from manage_writing import (
    validate_drafts,
    validate_revision,
    validate_scene_contracts,
    validate_sources,
    validate_upstream,
)
from render_fragments import render


def validate_package(
    package_dir: Path,
    plan_dir: Path,
    r1_dir: Path,
) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    plan_dir = plan_dir.resolve()
    r1_dir = r1_dir.resolve()
    validate_upstream(plan_dir, r1_dir)
    required = [
        "generation-session.json",
        "fragment-package.json",
        "fragments.md",
        "execution-record.json",
        "package-manifest.json",
    ]
    for name in required:
        require((package_dir / name).is_file(), f"package missing {name}")
    session = load_json(package_dir / "generation-session.json")
    require(session.get("skill") == SKILL_NAME, "session skill mismatch")
    require(session.get("status") == "ready_to_finalize", "session is incomplete")
    require(session.get("style_contract") == STYLE_CONTRACT, "session style changed")
    meaningful(session.get("executor_id"), "executor_id")
    meaningful(session.get("task_id"), "task_id")

    plan_path = plan_dir / "review-plan.json"
    briefs_path = plan_dir / "fragment-briefs.json"
    inventory_path = plan_dir / "source-inventory.json"
    require(
        session["inputs"]["plan_directory"] == str(plan_dir),
        "session targets another plan directory",
    )
    require(
        session["inputs"]["r1_directory"] == str(r1_dir),
        "session targets another R1 directory",
    )
    for name, path in (
        ("review-plan.json", plan_path),
        ("fragment-briefs.json", briefs_path),
        ("source-inventory.json", inventory_path),
    ):
        require(session["inputs"][name] == sha256_file(path), f"session input changed: {name}")

    briefs = load_json(briefs_path)
    slots = {item["id"]: item for item in briefs["slots"]}
    phase_data: dict[str, dict[str, Any]] = {}
    phase_records = {item["id"]: item for item in session["phases"]}
    require(set(phase_records) == set(PHASES), "session phase set mismatch")
    for phase in PHASES:
        record = phase_records[phase]
        require(record.get("status") == "complete", f"phase incomplete: {phase}")
        expected_rel = f"generation-evidence/{PHASE_FILES[phase]}"
        require(record.get("path") == expected_rel, f"phase path mismatch: {phase}")
        path = package_dir / expected_rel
        require(path.is_file(), f"phase evidence missing: {phase}")
        require(record.get("sha256") == sha256_file(path), f"phase hash mismatch: {phase}")
        phase_data[phase] = load_json(path)
    validate_scene_contracts(phase_data["scene-contracts"], slots)
    validate_drafts(
        phase_data["drafts"],
        slots,
        phase_data["scene-contracts"],
    )
    validate_revision(
        phase_data["revision-audit"],
        slots,
        phase_data["drafts"],
    )

    fragment_package_path = package_dir / "fragment-package.json"
    fragment_package = load_json(fragment_package_path)
    require(fragment_package.get("schema_version") == "1.0", "fragment schema mismatch")
    require(fragment_package.get("skill") == SKILL_NAME, "fragment skill mismatch")
    require(fragment_package.get("status") == "ready", "fragment package is not ready")
    require(fragment_package.get("style_contract") == STYLE_CONTRACT, "final style changed")
    require(
        fragment_package.get("review_plan_sha256") == sha256_file(plan_path),
        "final package plan hash mismatch",
    )
    final_by_id = ensure_exact_ids(
        fragment_package.get("fragments"),
        set(slots),
        "final fragments",
    )
    audit_by_id = {
        item["id"]: item for item in phase_data["revision-audit"]["fragments"]
    }
    measurements: list[dict[str, Any]] = []
    for fragment_id, fragment in final_by_id.items():
        slot = slots[fragment_id]
        audit = audit_by_id[fragment_id]
        expected = {
            "id": audit["id"],
            "title": audit["title"],
            "text": audit["final_text"],
            "source_ids": audit["source_ids"],
            "control_ids": audit["control_ids"],
            "unit_ids": audit["unit_ids"],
            "creative_choices": audit["creative_choices"],
            "introduced_authoritative_facts": audit[
                "introduced_authoritative_facts"
            ],
            "contract_checks": audit["contract_checks"],
            "scene_audit": audit["scene_audit"],
            "brief_compliance": audit["brief_compliance"],
            "style_metrics": fragment.get("style_metrics"),
        }
        require(fragment == expected, f"{fragment_id} is not derived from revision audit")
        validate_sources(fragment, slot, fragment_id)
        metrics = validate_style_text(fragment["text"], slot, fragment_id)
        require(fragment["style_metrics"] == metrics, f"{fragment_id} metrics mismatch")
        validate_audit(
            fragment["scene_audit"],
            fragment["text"],
            slot["coverage_targets"],
            fragment_id,
        )
        require(
            fragment["introduced_authoritative_facts"] == [],
            f"{fragment_id} introduces authoritative facts",
        )
        measurements.append({"id": fragment_id, **metrics})

    preview = (package_dir / "fragments.md").read_text(encoding="utf-8")
    require(preview == render(fragment_package), "fragments.md is not deterministic")

    execution_path = package_dir / "execution-record.json"
    execution = load_json(execution_path)
    require(execution.get("skill") == SKILL_NAME, "execution skill mismatch")
    require(execution.get("mode") == "autonomous_agent", "execution mode mismatch")
    require(execution.get("executor_id") == session["executor_id"], "executor mismatch")
    require(execution.get("task_id") == session["task_id"], "task mismatch")
    require(
        execution.get("review_plan_sha256") == sha256_file(plan_path),
        "execution plan hash mismatch",
    )
    require(
        execution.get("fragment_package_sha256") == sha256_file(fragment_package_path),
        "execution fragment hash mismatch",
    )
    for name, path in (
        ("fragment-briefs.json", briefs_path),
        ("source-inventory.json", inventory_path),
    ):
        require(execution.get("inputs", {}).get(name) == sha256_file(path), f"execution input mismatch: {name}")
    for phase in PHASES:
        rel = f"generation-evidence/{PHASE_FILES[phase]}"
        require(
            execution.get("phases", {}).get(phase) == sha256_file(package_dir / rel),
            f"execution phase mismatch: {phase}",
        )
    skill_dir = Path(__file__).resolve().parent.parent
    current_skill_files = {
        str(path.relative_to(skill_dir)).replace("\\", "/"): sha256_file(path)
        for path in all_skill_files(skill_dir)
    }
    recorded_skill_files = {
        item.get("path"): item.get("sha256")
        for item in execution.get("skill_files", [])
        if isinstance(item, dict)
    }
    require(
        recorded_skill_files == current_skill_files,
        "execution is not bound to current skill files",
    )

    manifest = load_json(package_dir / "package-manifest.json")
    verify_manifest(package_dir, manifest)
    require(manifest.get("verdict") == "ready", "manifest is not ready")
    return {
        "fragments": measurements,
        "fixed_style_contract": STYLE_CONTRACT["id"],
        "phase_evidence": PHASES,
        "skill_files": len(current_skill_files),
        "deterministic_package": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fiction review fragments.")
    parser.add_argument("package", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    output = args.package.resolve() / "validation.json"
    try:
        evidence = validate_package(args.package, args.plan, args.r1)
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "fragment-writing",
            "verdict": "ready",
            "errors": [],
            "evidence": {
                "review_plan_sha256": sha256_file(
                    args.plan.resolve() / "review-plan.json"
                ),
                "fragment_package_sha256": sha256_file(
                    args.package.resolve() / "fragment-package.json"
                ),
                "execution_record_sha256": sha256_file(
                    args.package.resolve() / "execution-record.json"
                ),
                **evidence,
            },
        }
        write_json(output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "fragment-writing",
            "verdict": "blocked",
            "errors": [str(exc)],
            "evidence": {},
        }
        write_json(output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
