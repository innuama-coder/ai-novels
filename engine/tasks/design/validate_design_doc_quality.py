#!/usr/bin/env python3
"""Validate generated detailed-design documents for the HLD workflow planning run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TERMS = [
    "Source Refs",
    "Scope Boundary",
    "Control Flow",
    "Data Flow",
    "Interface Contracts",
    "State And Persistence",
    "Error Handling And Diagnostics",
    "Security And Permissions",
    "Observability",
    "Verification",
    "Risks",
    "Handoff",
]

REQUIRED_TASK_DETAIL_MARKERS = {
    "HLD contract and validator design": [
        "Validator Function Contract Matrix",
        "Negative Fixture Matrix",
        "Contract Rule Traceability Matrix",
    ],
    "HLD harness and independent skills design": [
        "Harness Responsibility Boundary Matrix",
        "Skill Contract Matrix",
        "Artifact Dispatch DAG",
    ],
    "Global workflow spec and legacy HLD writer migration design": [
        "Global Spec Migration Matrix",
        "Legacy Writer Downgrade Contract",
        "Stale Authority Detection Matrix",
    ],
    "HLD blocked/pass fixture and acceptance design": [
        "Blocked Fixture Contract",
        "Pass Fixture Contract",
        "Acceptance Evidence Matrix",
    ],
    "Final design acceptance review": [
        "Acceptance Dependency Mapping",
        "Design Acceptance Checklist",
        "Residual Risk Disposition Matrix",
        "Final Handoff Verdict",
    ],
}

IMPLEMENTATION_REPORT_MARKERS = [
    "Changed files",
    "Files changed",
    "Implemented",
    "Test results",
    "Diff summary",
]


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL: {error}")
    sys.exit(1)


def load_plan(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail([f"cannot read planning JSON {path}: {exc}"])
    raise AssertionError("unreachable")


def normalize(value: str) -> str:
    return "".join(value.lower().split())


def document_rel_path(document: Path) -> str:
    rel = document.as_posix()
    if document.is_absolute():
        try:
            rel = document.relative_to(Path.cwd()).as_posix()
        except ValueError:
            rel = document.as_posix()
    return rel


def matching_task_for_document(plan: dict, document: Path) -> dict | None:
    rel = document_rel_path(document)
    for task in plan.get("tasks", []):
        if task.get("design_doc_path") == rel:
            return task
    return None


def check_task_context(document: Path, text: str, task: dict, acceptance: bool) -> list[str]:
    errors: list[str] = []
    task_type = task.get("task_type")
    if acceptance and task_type != "design_acceptance":
        errors.append(f"{document}: --acceptance used for non-acceptance task")
    elif not acceptance and task_type == "design_acceptance":
        errors.append(f"{document}: acceptance task must be validated with --acceptance")

    normalized_text = normalize(text)
    for source_ref in task.get("source_refs", []):
        if str(source_ref) not in text:
            errors.append(f"{document}: missing planned source ref {source_ref}")

    design_doc_path = task.get("design_doc_path")
    outputs = task.get("outputs", [])
    if design_doc_path and design_doc_path not in outputs:
        errors.append(f"{document}: planned outputs do not include design_doc_path {design_doc_path}")

    forbidden_text = " ".join(str(item) for item in task.get("forbidden_scope", []))
    if "implementation code" in forbidden_text.lower() and "do not implement code" not in text.lower():
        errors.append(f"{document}: missing no-code boundary from forbidden scope")
    if "hld business" in forbidden_text.lower() and "hld business" not in text.lower():
        errors.append(f"{document}: missing HLD business artifact boundary from forbidden scope")
    if "prd" in forbidden_text.lower() and "prd" not in text.lower():
        errors.append(f"{document}: missing PRD boundary from forbidden scope")

    for item in task.get("acceptance", []):
        if normalize(str(item)) not in normalized_text:
            errors.append(f"{document}: does not address planned acceptance item {item}")

    for marker in REQUIRED_TASK_DETAIL_MARKERS.get(str(task.get("title")), []):
        if marker not in text:
            errors.append(f"{document}: missing task-specific detail marker {marker}")

    return errors


def validate(document: Path, planning: Path, acceptance: bool) -> list[str]:
    errors: list[str] = []
    if not document.exists():
        return [f"missing design document: {document}"]
    text = document.read_text(encoding="utf-8")
    if len(text) < (900 if not acceptance else 700):
        errors.append(f"{document}: design document is too small")
    lowered = text.lower()
    for marker in ["tbd", "todo", "placeholder"]:
        if marker in lowered:
            errors.append(f"{document}: contains placeholder marker {marker}")
    for marker in IMPLEMENTATION_REPORT_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"{document}: looks like an implementation report, not a design document")
    missing_terms = [term for term in REQUIRED_TERMS if term not in text]
    if missing_terms:
        errors.append(f"{document}: missing required sections {missing_terms}")

    plan = load_plan(planning)
    matching_task = matching_task_for_document(plan, document)
    if not matching_task:
        errors.append(f"{document}: not referenced by design-planning.json")
    else:
        errors.extend(check_task_context(document, text, matching_task, acceptance))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--planning", required=True)
    parser.add_argument("--acceptance", action="store_true")
    parser.add_argument("document")
    args = parser.parse_args()

    errors = validate(Path(args.document), Path(args.planning), args.acceptance)
    if errors:
        fail(errors)
    print("PASS: design document quality valid")


if __name__ == "__main__":
    main()
