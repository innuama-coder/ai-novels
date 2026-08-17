#!/usr/bin/env python3
"""Validate one append-only novel-conception interview session (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

STAGES = {"I0", "I1", "I2", "I3", "I4", "I5"}
EVENT_TYPES = {"plan_presented", "question", "author_answer", "agent_recap", "decision", "plan_revision", "stage_close"}


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON: {path.name}: {exc}")
        return None


def load_events(path: Path, errors: list[str]):
    events = []
    if not path.is_file():
        errors.append("missing events.ndjson")
        return events
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"events.ndjson line {line_number}: {exc}")
            continue
        events.append(event)
    return events


def validate_plan(plan: dict, expected_revision: int, errors: list[str]):
    required = {"harness", "run_id", "stage", "session_id", "revision", "question_budget", "groups", "planned_minutes", "transcript_assurance"}
    missing = required - set(plan)
    if missing:
        errors.append(f"plan.v{expected_revision}.json missing fields: {', '.join(sorted(missing))}")
        return
    if plan["harness"] != "novel-conception-interview":
        errors.append(f"plan.v{expected_revision}.json has wrong harness")
    if plan["stage"] not in STAGES:
        errors.append(f"plan.v{expected_revision}.json has invalid stage")
    if plan["revision"] != expected_revision:
        errors.append(f"plan revision mismatch: expected {expected_revision}, got {plan['revision']}")
    if not isinstance(plan["question_budget"], int) or plan["question_budget"] < 1:
        errors.append(f"plan.v{expected_revision}.json requires positive question_budget")
    groups = plan["groups"]
    if not isinstance(groups, list) or not groups:
        errors.append(f"plan.v{expected_revision}.json requires non-empty groups")
        return
    group_ids = [group.get("id") for group in groups if isinstance(group, dict)]
    if len(group_ids) != len(set(group_ids)) or any(not group_id for group_id in group_ids):
        errors.append(f"plan.v{expected_revision}.json has duplicate or blank group id")
    if any(not isinstance(group.get("budget"), int) or group["budget"] < 0 for group in groups if isinstance(group, dict)):
        errors.append(f"plan.v{expected_revision}.json group budgets must be non-negative integers")
    elif sum(group["budget"] for group in groups) != plan["question_budget"]:
        errors.append(f"plan.v{expected_revision}.json group budgets must equal question_budget")
    assurance = plan["transcript_assurance"]
    if assurance != "self_recorded":
        errors.append(f"plan.v{expected_revision}.json has invalid transcript_assurance")


def validate(session: Path) -> dict:
    errors: list[str] = []
    plan_paths = sorted(session.glob("plan.v*.json"), key=lambda p: p.name)
    if not plan_paths:
        errors.append("missing immutable plan.v1.json")
        plans = []
    else:
        plans = [load_json(path, errors) for path in plan_paths]
        plans = [plan for plan in plans if plan is not None]
        for expected, plan in enumerate(plans, 1):
            validate_plan(plan, expected, errors)
        if plans and len({plan["session_id"] for plan in plans}) != 1:
            errors.append("all plan revisions must have the same session_id")
        if plans and len({plan["stage"] for plan in plans}) != 1:
            errors.append("all plan revisions must have the same stage")
        if plans and len({plan["run_id"] for plan in plans}) != 1:
            errors.append("all plan revisions must have the same run_id")

    events = load_events(session / "events.ndjson", errors)
    for expected_seq, event in enumerate(events, 1):
        if not isinstance(event, dict):
            errors.append(f"event {expected_seq} is not an object")
            continue
        if event.get("seq") != expected_seq:
            errors.append(f"events must have contiguous seq; expected {expected_seq}")
        if event.get("type") not in EVENT_TYPES:
            errors.append(f"event {expected_seq} has invalid type")
        if not isinstance(event.get("text"), str) or not event["text"].strip():
            errors.append(f"event {expected_seq} requires non-empty text")

    if plans:
        first = events[0] if events else {}
        if first.get("type") != "plan_presented" or first.get("plan_revision") != 1:
            errors.append("first event must record that the exact plan was presented before questions")
        elif first.get("announced_question_budget") != plans[0]["question_budget"] or first.get("announced_minutes") != plans[0]["planned_minutes"]:
            errors.append("first plan presentation does not match the exact planned question budget and duration")

    unanswered = None
    questions = []
    group_counts: Counter[str] = Counter()
    group_counts_by_revision: dict[int, Counter[str]] = {}
    active_revision = None
    early_close = False
    plan_by_revision = {plan.get("revision"): plan for plan in plans if isinstance(plan.get("revision"), int)}
    for event in events:
        event_type = event.get("type")
        if event_type == "plan_presented":
            revision = event.get("plan_revision")
            if revision != 1 or active_revision is not None:
                errors.append(f"plan_presented event {event.get('seq')} may announce only plan revision 1")
            elif revision not in plan_by_revision:
                errors.append("plan_presented references a missing plan revision")
            else:
                active_revision = revision
        elif event_type == "plan_revision":
            revision = event.get("plan_revision")
            plan = plan_by_revision.get(revision)
            if active_revision is None or revision != active_revision + 1 or plan is None:
                errors.append(f"plan_revision event {event.get('seq')} does not activate the next immutable plan")
                continue
            if event.get("author_approved") is not True or not isinstance(event.get("approval_ref"), str) or not event["approval_ref"].strip():
                errors.append(f"plan_revision event {event.get('seq')} lacks explicit author approval evidence")
            if event.get("announced_question_budget") != plan.get("question_budget") or event.get("announced_minutes") != plan.get("planned_minutes"):
                errors.append(f"plan_revision event {event.get('seq')} does not announce the exact revised plan")
            revised_groups = {group["id"]: group["budget"] for group in plan.get("groups", []) if isinstance(group, dict) and isinstance(group.get("id"), str) and isinstance(group.get("budget"), int)}
            if len(questions) > plan.get("question_budget", -1) or any(group_counts[group_id] > revised_groups.get(group_id, -1) for group_id in group_counts):
                errors.append(f"plan_revision event {event.get('seq')} retroactively invalidates already asked questions")
            active_revision = revision
        elif event_type == "question":
            revision = event.get("plan_revision")
            if active_revision is None or revision != active_revision:
                errors.append(f"question {event.get('question_id')} is not bound to the active plan revision")
            plan = plan_by_revision.get(revision)
            if plan is None:
                errors.append(f"question {event.get('question_id')} references a missing plan revision")
            if unanswered is not None:
                errors.append(f"question {event.get('question_id')} asked before answer to {unanswered}")
            question_id = event.get("question_id")
            group_id = event.get("group_id")
            if not question_id or not group_id:
                errors.append(f"question event {event.get('seq')} needs question_id and group_id")
            questions.append(event)
            group_counts[group_id] += 1
            group_counts_by_revision.setdefault(revision, Counter())[group_id] += 1
            if plan is not None:
                active_groups = {group["id"]: group["budget"] for group in plan["groups"]}
                if group_id not in active_groups:
                    errors.append(f"question {question_id} uses a group absent from active plan revision {revision}")
                elif group_counts[group_id] > active_groups[group_id] or len(questions) > plan["question_budget"]:
                    errors.append(f"question {question_id} exceeds active plan revision {revision}")
            unanswered = question_id
        elif event_type == "author_answer":
            if unanswered is None:
                errors.append(f"answer event {event.get('seq')} has no pending question")
            elif event.get("question_id") != unanswered:
                errors.append(f"answer event {event.get('seq')} does not match pending question {unanswered}")
            else:
                unanswered = None
        elif event_type == "stage_close" and event.get("decision") == "early_close":
            if active_revision is None or event.get("plan_revision") != active_revision:
                errors.append(f"early close event {event.get('seq')} is not bound to the active plan revision")
            if event.get("author_approved") is not True or not isinstance(event.get("approval_ref"), str) or not event["approval_ref"].strip():
                errors.append(f"early close event {event.get('seq')} lacks explicit author approval evidence")
            else:
                early_close = True
    if unanswered is not None:
        errors.append(f"question {unanswered} has no author answer")

    latest = plans[-1] if plans else None
    if latest:
        expected_budget = latest["question_budget"]
        if len(questions) != expected_budget and not early_close:
            errors.append(f"asked {len(questions)} questions; latest approved plan requires exactly {expected_budget}")
        latest_group_budgets = {group["id"]: group["budget"] for group in latest["groups"]}
        unknown_groups = set(group_counts) - set(latest_group_budgets)
        if unknown_groups:
            errors.append(f"questions use unplanned groups: {', '.join(sorted(unknown_groups))}")
        if not early_close:
            for group_id, budget in latest_group_budgets.items():
                if group_counts[group_id] != budget:
                    errors.append(f"group {group_id}: asked {group_counts[group_id]}, plan requires {budget}")
    report_path = session / "report.md"
    if plans and events:
        renderer = Path(__file__).resolve().parents[1] / "tools" / "render_report.py"
        rendered = subprocess.run([sys.executable, str(renderer), str(session)], capture_output=True, text=True)
        if rendered.returncode != 0 or not report_path.is_file():
            errors.append("unable to regenerate complete report from the event log")
    report_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest() if report_path.is_file() else None
    ready = not errors and bool(latest) and len(questions) > 0 and bool(report_sha256)
    return {
        "harness": "novel-conception-interview",
        "run_id": latest.get("run_id") if latest else None,
        "session_path": str(session),
        "verdict": "ready" if ready else "blocked",
        "errors": errors,
        "evidence": {
            "plan_revisions": len(plans),
            "questions_planned": latest["question_budget"] if latest else 0,
            "questions_answered": len(questions),
            "group_counts": dict(group_counts),
            "transcript_assurance": latest.get("transcript_assurance") if latest else "unknown",
            "report_path": "report.md" if report_sha256 else None,
            "report_sha256": report_sha256,
            "event_backed_claim_allowed": False
        }
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_session.py <session-directory>", file=sys.stderr)
        return 2
    session = Path(argv[1]).resolve()
    result = validate(session)
    (session / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
