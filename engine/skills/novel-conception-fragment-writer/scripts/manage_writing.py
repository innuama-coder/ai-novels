from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import (
    PHASES,
    PHASE_FILES,
    SKILL_NAME,
    STYLE_CONTRACT,
    ContractError,
    ensure_exact_ids,
    load_json,
    meaningful,
    require,
    require_keys,
    sha256_file,
    sha256_text,
    validate_audit,
    validate_brief_compliance,
    validate_creative_choices,
    write_json,
)


def assembler_validator() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "novel-conception-human-review-assembler"
        / "scripts"
        / "validate_human_review.py"
    )


def validate_upstream(plan_dir: Path, r1_dir: Path) -> None:
    validator = assembler_validator()
    require(validator.is_file(), f"missing assembler validator: {validator}")
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            "plan",
            str(plan_dir),
            "--r1",
            str(r1_dir),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(result.returncode == 0, f"upstream plan validation failed: {result.stderr.strip()}")


def load_context(workspace: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    session = load_json(workspace / "generation-session.json")
    plan_dir = Path(session["inputs"]["plan_directory"])
    briefs = load_json(plan_dir / "fragment-briefs.json")
    slots = {item["id"]: item for item in briefs["slots"]}
    return session, briefs, slots


def validate_sources(item: dict[str, Any], slot: dict[str, Any], label: str) -> None:
    source_ids = item.get("source_ids")
    control_ids = item.get("control_ids")
    unit_ids = item.get("unit_ids")
    require(isinstance(source_ids, list), f"{label} source_ids must be a list")
    require(isinstance(control_ids, list), f"{label} control_ids must be a list")
    require(isinstance(unit_ids, list), f"{label} unit_ids must be a list")
    require(
        set(slot["required_source_ids"]) <= set(source_ids),
        f"{label} misses required sources",
    )
    require(
        set(source_ids) <= set(slot["allowed_source_ids"]),
        f"{label} cites disallowed sources",
    )
    require(
        set(control_ids) <= set(slot["control_ids"]),
        f"{label} cites disallowed controls",
    )
    require(set(unit_ids) == set(slot["unit_ids"]), f"{label} unit_ids mismatch")


def validate_scene_contracts(data: dict[str, Any], slots: dict[str, Any]) -> None:
    require(data.get("phase") == "scene-contracts", "wrong phase payload")
    require(data.get("style_contract") == STYLE_CONTRACT, "style contract was changed")
    by_id = ensure_exact_ids(data.get("fragments"), set(slots), "scene contracts")
    keys = {
        "id",
        "style_contract_id",
        "pov",
        "start_value",
        "end_value",
        "immediate_intention",
        "active_pressure",
        "obstacle",
        "turning_choice",
        "direct_consequence",
        "world_rule_in_action",
        "relationship_change",
        "information_limit",
        "allowed_sensory_channels",
        "forbidden_sensory_channels",
        "creative_choices",
        "source_ids",
        "control_ids",
        "unit_ids",
    }
    for fragment_id, item in by_id.items():
        slot = slots[fragment_id]
        require_keys(item, keys, f"scene contract {fragment_id}")
        require(
            item["style_contract_id"] == STYLE_CONTRACT["id"],
            f"{fragment_id} style contract mismatch",
        )
        require(item["pov"] == slot["pov"], f"{fragment_id} POV mismatch")
        require(
            item["start_value"] == slot["before_state"],
            f"{fragment_id} start value does not match brief",
        )
        require(
            item["end_value"] == slot["after_state"],
            f"{fragment_id} end value does not match brief",
        )
        for key in (
            "start_value",
            "end_value",
            "immediate_intention",
            "active_pressure",
            "obstacle",
            "turning_choice",
            "direct_consequence",
            "world_rule_in_action",
            "relationship_change",
            "information_limit",
        ):
            meaningful(item[key], f"{fragment_id}.{key}")
        require(
            isinstance(item["allowed_sensory_channels"], list),
            f"{fragment_id} allowed senses must be a list",
        )
        require(
            isinstance(item["forbidden_sensory_channels"], list),
            f"{fragment_id} forbidden senses must be a list",
        )
        require(
            not set(item["allowed_sensory_channels"])
            & set(item["forbidden_sensory_channels"]),
            f"{fragment_id} sensory channels conflict",
        )
        validate_creative_choices(
            item["creative_choices"],
            slot["allowed_creative_freedom"],
            fragment_id,
        )
        validate_sources(item, slot, fragment_id)


def validate_drafts(
    data: dict[str, Any],
    slots: dict[str, Any],
    contracts: dict[str, Any],
) -> None:
    require(data.get("phase") == "drafts", "wrong phase payload")
    require(data.get("style_contract") == STYLE_CONTRACT, "style contract was changed")
    by_id = ensure_exact_ids(data.get("fragments"), set(slots), "drafts")
    contract_by_id = {item["id"]: item for item in contracts["fragments"]}
    for fragment_id, item in by_id.items():
        require_keys(
            item,
            {
                "id",
                "title",
                "text",
                "source_ids",
                "control_ids",
                "unit_ids",
                "creative_choices",
                "introduced_authoritative_facts",
            },
            f"draft {fragment_id}",
        )
        meaningful(item["title"], f"{fragment_id}.title")
        meaningful(item["text"], f"{fragment_id}.text", minimum=40)
        require(
            item["introduced_authoritative_facts"] == [],
            f"{fragment_id} draft introduces authoritative facts",
        )
        require(
            item["creative_choices"] == contract_by_id[fragment_id]["creative_choices"],
            f"{fragment_id} draft changed creative choices",
        )
        validate_sources(item, slots[fragment_id], fragment_id)


def validate_revision(
    data: dict[str, Any],
    slots: dict[str, Any],
    drafts: dict[str, Any],
) -> None:
    require(data.get("phase") == "revision-audit", "wrong phase payload")
    require(data.get("style_contract") == STYLE_CONTRACT, "style contract was changed")
    by_id = ensure_exact_ids(data.get("fragments"), set(slots), "revision audit")
    draft_by_id = {item["id"]: item for item in drafts["fragments"]}
    for fragment_id, item in by_id.items():
        require_keys(
            item,
            {
                "id",
                "title",
                "draft_sha256",
                "final_text",
                "source_ids",
                "control_ids",
                "unit_ids",
                "creative_choices",
                "introduced_authoritative_facts",
                "contract_checks",
                "scene_audit",
                "brief_compliance",
                "revisions",
            },
            f"revision {fragment_id}",
        )
        draft = draft_by_id[fragment_id]
        require(
            item["draft_sha256"] == sha256_text(draft["text"]),
            f"{fragment_id} draft hash mismatch",
        )
        meaningful(item["final_text"], f"{fragment_id}.final_text", minimum=40)
        require(item["final_text"] != draft["text"], f"{fragment_id} was not revised")
        require(
            isinstance(item["revisions"], list) and item["revisions"],
            f"{fragment_id} has no revision record",
        )
        for index, revision in enumerate(item["revisions"]):
            require_keys(
                revision,
                {"issue", "change", "reason"},
                f"{fragment_id}.revisions[{index}]",
            )
            for key in ("issue", "change", "reason"):
                meaningful(revision[key], f"{fragment_id}.revisions[{index}].{key}")
        require(
            item["creative_choices"] == draft["creative_choices"],
            f"{fragment_id} revision changed creative choices",
        )
        require(
            item["introduced_authoritative_facts"] == [],
            f"{fragment_id} introduces authoritative facts",
        )
        checks = item["contract_checks"]
        require(
            isinstance(checks, dict)
            and set(checks) == {
                "source_grounding",
                "narrative_contract",
                "no_new_authority",
                "review_question_fit",
            }
            and all(value is True for value in checks.values()),
            f"{fragment_id} contract checks failed",
        )
        validate_sources(item, slots[fragment_id], fragment_id)
        require(
            set(item["source_ids"]) <= set(draft["source_ids"]),
            f"{fragment_id} revision expanded sources",
        )
        validate_audit(
            item["scene_audit"],
            item["final_text"],
            slots[fragment_id]["coverage_targets"],
            fragment_id,
        )
        validate_brief_compliance(
            item["brief_compliance"],
            item["final_text"],
            slots[fragment_id],
            fragment_id,
        )


def begin(args: argparse.Namespace) -> None:
    plan_dir = args.plan_package.resolve()
    r1_dir = args.r1_package.resolve()
    workspace = args.workspace.resolve()
    require(not (workspace / "generation-session.json").exists(), "session already exists")
    validate_upstream(plan_dir, r1_dir)
    briefs_path = plan_dir / "fragment-briefs.json"
    plan_path = plan_dir / "review-plan.json"
    inventory_path = plan_dir / "source-inventory.json"
    for path in (briefs_path, plan_path, inventory_path):
        require(path.is_file(), f"missing plan input: {path.name}")
    briefs = load_json(briefs_path)
    require(briefs.get("status") == "ready", "fragment briefs are not ready")
    require(
        briefs.get("review_plan_sha256") == sha256_file(plan_path),
        "fragment briefs plan hash mismatch",
    )
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "generation-evidence").mkdir(parents=True, exist_ok=True)
    session = {
        "schema_version": "1.0",
        "skill": SKILL_NAME,
        "run_id": briefs.get("run_id"),
        "status": "active",
        "executor_id": args.executor_id,
        "task_id": args.task_id,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "style_contract": STYLE_CONTRACT,
        "inputs": {
            "plan_directory": str(plan_dir),
            "r1_directory": str(r1_dir),
            "review-plan.json": sha256_file(plan_path),
            "fragment-briefs.json": sha256_file(briefs_path),
            "source-inventory.json": sha256_file(inventory_path),
        },
        "phases": [
            {"id": phase, "status": "pending", "path": None, "sha256": None}
            for phase in PHASES
        ],
    }
    write_json(workspace / "generation-session.json", session)


def submit(args: argparse.Namespace) -> None:
    workspace = args.workspace.resolve()
    session, _, slots = load_context(workspace)
    require(session.get("status") == "active", "writing session is not active")
    pending = [item["id"] for item in session["phases"] if item["status"] == "pending"]
    require(pending and pending[0] == args.phase, f"next phase must be {pending[0] if pending else 'none'}")
    data = load_json(args.payload)
    if args.phase == "scene-contracts":
        validate_scene_contracts(data, slots)
    elif args.phase == "drafts":
        contracts = load_json(
            workspace / "generation-evidence" / PHASE_FILES["scene-contracts"]
        )
        validate_drafts(data, slots, contracts)
    else:
        drafts = load_json(workspace / "generation-evidence" / PHASE_FILES["drafts"])
        validate_revision(data, slots, drafts)
    destination = workspace / "generation-evidence" / PHASE_FILES[args.phase]
    require(not destination.exists(), f"phase already submitted: {args.phase}")
    shutil.copyfile(args.payload, destination)
    for item in session["phases"]:
        if item["id"] == args.phase:
            item.update(
                {
                    "status": "complete",
                    "path": f"generation-evidence/{destination.name}",
                    "sha256": sha256_file(destination),
                }
            )
    if args.phase == PHASES[-1]:
        session["status"] = "ready_to_finalize"
    write_json(workspace / "generation-session.json", session)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage staged fragment writing.")
    sub = parser.add_subparsers(dest="command", required=True)
    begin_parser = sub.add_parser("begin")
    begin_parser.add_argument("plan_package", type=Path)
    begin_parser.add_argument("r1_package", type=Path)
    begin_parser.add_argument("workspace", type=Path)
    begin_parser.add_argument("--executor-id", required=True)
    begin_parser.add_argument("--task-id", required=True)
    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("workspace", type=Path)
    submit_parser.add_argument("phase", choices=PHASES)
    submit_parser.add_argument("payload", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "begin":
            begin(args)
        else:
            submit(args)
    except ContractError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(f"READY: {args.command} {getattr(args, 'phase', '')}".rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
