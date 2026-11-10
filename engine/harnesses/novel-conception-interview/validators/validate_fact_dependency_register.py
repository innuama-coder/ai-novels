#!/usr/bin/env python3
"""Validate the V1 fact-dependency register required by B0."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

SHA256 = re.compile(r"^[a-f0-9]{64}$")
TOP_LEVEL_KEYS = {"schema_version", "harness", "run_id", "stage", "status", "fact_dependencies"}
FIELDS = {
    "not_applicable": {"id", "status", "claim", "rationale"},
    "adopted": {"id", "status", "claim", "research_package", "adoption_record", "allowed_use", "fiction_boundary"},
    "open": {"id", "status", "claim", "blocking", "allowed_handling", "rationale"},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_reference(base: Path, value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"} or not isinstance(value.get("path"), str) or not value["path"] or not isinstance(value.get("sha256"), str) or SHA256.fullmatch(value["sha256"]) is None:
        errors.append(f"{label} is not an exact hash-bound reference")
        return
    if Path(value["path"]).is_absolute():
        errors.append(f"{label}.path must be relative to the register")
        return
    target = (base / value["path"]).resolve()
    if not target.is_file() or digest(target) != value["sha256"]:
        errors.append(f"{label} is missing or has changed")


def validate_register(path: Path) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"fact-dependency register is not readable JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["fact-dependency register must be an object"]
    if set(data) != TOP_LEVEL_KEYS:
        errors.append("fact-dependency register must contain exactly the contracted top-level fields")
    if data.get("schema_version") != "1.0" or data.get("harness") != "novel-conception-interview" or data.get("stage") != "V1" or data.get("status") != "ready" or not isinstance(data.get("run_id"), str) or not data["run_id"].strip():
        errors.append("fact-dependency register identity/status is invalid")
    dependencies = data.get("fact_dependencies")
    ids: list[str] = []
    if not isinstance(dependencies, list) or not dependencies:
        errors.append("fact_dependencies must be non-empty; use one not_applicable record when no external fact is needed")
    else:
        for index, item in enumerate(dependencies):
            if not isinstance(item, dict):
                errors.append(f"fact_dependencies[{index}] is not an object")
                continue
            status = item.get("status")
            if status not in FIELDS or set(item) != FIELDS.get(status, set()):
                errors.append(f"fact_dependencies[{index}] fields do not match status {status!r}")
                continue
            fact_id = item.get("id")
            if not isinstance(fact_id, str) or re.fullmatch(r"FACT-[A-Za-z0-9._-]+", fact_id) is None:
                errors.append(f"fact_dependencies[{index}].id is invalid")
            else:
                ids.append(fact_id)
            if not isinstance(item.get("claim"), str) or not item["claim"].strip():
                errors.append(f"fact_dependencies[{index}].claim is empty")
            if status == "not_applicable" and (not isinstance(item.get("rationale"), str) or not item["rationale"].strip()):
                errors.append(f"fact_dependencies[{index}].rationale is empty")
            elif status == "open":
                if item.get("blocking") is not False or item.get("allowed_handling") != "preserve_open" or not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
                    errors.append(f"fact_dependencies[{index}] open fact must be non-blocking and preserve_open")
            elif status == "adopted":
                for field in ("research_package", "adoption_record"):
                    validate_reference(path.parent, item.get(field), f"fact_dependencies[{index}].{field}", errors)
                for field in ("allowed_use", "fiction_boundary"):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        errors.append(f"fact_dependencies[{index}].{field} is empty")
        if len(ids) != len(set(ids)):
            errors.append("fact dependency ids must be unique")
    return data, errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_fact_dependency_register.py <fact-dependency-register.json>", file=sys.stderr)
        return 2
    data, errors = validate_register(Path(argv[1]).resolve())
    if errors:
        for error in errors:
            print("FAIL: " + error)
        return 1
    print(f"OK: V1 fact-dependency register is ready for {data['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
