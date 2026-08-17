"""Validate one interview session directory using only the Python standard library."""
import json
import re
import sys
from pathlib import Path


def fail(errors, message):
    errors.append(message)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_interview_artifacts.py <session-dir>")
        return 2
    root = Path(sys.argv[1])
    errors = []
    plan_file, report_file = root / "plan.json", root / "report.md"
    if not plan_file.is_file(): fail(errors, "missing plan.json")
    if not report_file.is_file(): fail(errors, "missing report.md")
    if errors:
        print(json.dumps({"verdict": "blocked", "errors": errors}, ensure_ascii=False)); return 1
    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"verdict": "blocked", "errors": [f"invalid plan.json: {exc}"]}, ensure_ascii=False)); return 1
    required = {"schema_version", "interview_id", "stage", "input_versions", "question_budget", "groups", "estimated_minutes", "completion_conditions", "transcript_assurance"}
    missing = sorted(required - set(plan))
    if missing: fail(errors, "missing plan fields: " + ", ".join(missing))
    if plan.get("transcript_assurance") not in {"self_recorded", "event_backed"}: fail(errors, "invalid transcript_assurance")
    groups = plan.get("groups", [])
    if not isinstance(plan.get("question_budget"), int) or plan.get("question_budget", 0) < 1: fail(errors, "question_budget must be a positive integer")
    if not isinstance(groups, list) or not groups or any(not isinstance(x, dict) or not isinstance(x.get("budget"), int) or x["budget"] < 0 for x in groups): fail(errors, "groups require non-negative integer budgets")
    elif sum(x["budget"] for x in groups) != plan["question_budget"]: fail(errors, "group budgets do not equal question_budget")
    report = report_file.read_text(encoding="utf-8")
    questions = [int(x) for x in re.findall(r"^### 问题 #(\d+)\s*$", report, re.M)]
    if questions and questions != list(range(1, len(questions) + 1)): fail(errors, "question numbers are not continuous from 1")
    if len(questions) > plan.get("question_budget", 0) and "## plan_revision" not in report: fail(errors, "over-budget report has no plan_revision")
    for heading in ("## 访谈计划", "## 逐轮记录", "## 决策账本", "## 交接包", "## 完成判定"):
        if heading not in report: fail(errors, f"report missing {heading}")
    verdict = "ready" if not errors else "revise"
    output = {"schema_version": "1.0", "interview_id": plan.get("interview_id"), "verdict": verdict, "question_budget": plan.get("question_budget"), "recorded_questions": len(questions), "transcript_assurance": plan.get("transcript_assurance"), "errors": errors}
    (root / "validation.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return 0 if verdict == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
