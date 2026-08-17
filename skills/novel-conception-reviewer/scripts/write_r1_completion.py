#!/usr/bin/env python3
"""Create an R1 completion after package validation and final author approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


HARNESS = "novel-conception-interview"
VALIDATOR = Path(__file__).resolve().parent / "validate_conception_review.py"
HARNESS_VALIDATOR = (
    Path(__file__).resolve().parents[3]
    / "harnesses"
    / HARNESS
    / "validators"
    / "validate_stage_completion.py"
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} root is not an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(base: Path, target: Path) -> dict[str, str]:
    return {
        "path": Path(os.path.relpath(target, base)).as_posix(),
        "sha256": sha256(target),
    }


def clean_reference(base: Path, value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not a reference")
    relative = value.get("path")
    digest = value.get("sha256")
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label}.path is missing")
    if Path(relative).is_absolute():
        raise ValueError(f"{label}.path must be relative")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in digest)
    ):
        raise ValueError(f"{label}.sha256 is invalid")
    target = (base / relative).resolve()
    if not target.is_file() or sha256(target) != digest.lower():
        raise ValueError(f"{label} is missing or has changed")
    return reference(base, target)


def validate_package(package_dir: Path) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(VALIDATOR), str(package_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("R1 validator returned invalid output") from exc
    if process.returncode != 0 or result.get("verdict") != "ready":
        raise ValueError("R1 package is not canonically ready")
    stored = load_json(package_dir / "validation.json")
    if result != stored:
        raise ValueError("stored R1 validation differs from canonical result")
    return result


def validate_approval(
    package_dir: Path, approval_path: Path, run_id: str
) -> None:
    approval = load_json(approval_path)
    if (
        approval.get("harness") != HARNESS
        or approval.get("run_id") != run_id
        or approval.get("approval_scope") != "R1"
        or approval.get("decision") != "approved"
        or approval.get("record_assurance") != "self_recorded"
    ):
        raise ValueError("final approval does not approve this R1 run")
    review = approval.get("review_brief")
    if not isinstance(review, dict):
        raise ValueError("final approval lacks review_brief")
    relative = review.get("path")
    digest = review.get("sha256")
    if not isinstance(relative, str) or not isinstance(digest, str):
        raise ValueError("final approval review_brief is invalid")
    if Path(relative).is_absolute():
        raise ValueError("final approval review_brief must be relative")
    target = (approval_path.parent / relative).resolve()
    expected = package_dir / "conception-review.md"
    if target != expected or not target.is_file() or sha256(target) != digest:
        raise ValueError(
            "final approval is not bound to the current conception-review.md"
        )
    record = approval.get("approval_record")
    if (
        not isinstance(record, dict)
        or not isinstance(record.get("event_seq"), int)
        or not isinstance(record.get("text"), str)
        or not record["text"].strip()
    ):
        raise ValueError("final approval lacks an explicit author decision")


def build_completion(
    package_dir: Path,
    approval_path: Path,
    session_id: str,
) -> dict[str, Any]:
    data = load_json(package_dir / "review-data.json")
    manifest = load_json(package_dir / "package-manifest.json")
    validation = load_json(package_dir / "validation.json")
    if (
        data.get("schema_version") != "1.0"
        or data.get("harness") != HARNESS
        or data.get("stage") != "R1"
        or data.get("status") != "ready"
    ):
        raise ValueError("review-data.json is not a ready R1 model")
    run_id = data.get("run_id")
    if (
        not isinstance(run_id, str)
        or not run_id
        or manifest.get("run_id") != run_id
        or manifest.get("stage") != "R1"
        or manifest.get("verdict") != "ready"
        or validation.get("run_id") != run_id
        or validation.get("verdict") != "ready"
    ):
        raise ValueError("R1 package records do not identify one ready run")
    validate_approval(package_dir, approval_path, run_id)
    gate = data.get("input_gate")
    if not isinstance(gate, dict):
        raise ValueError("review-data.json lacks input_gate")
    inputs = [
        clean_reference(package_dir, gate.get(field), f"{stage} completion")
        for stage, field in (
            ("V1", "v1_completion"),
            ("V2", "v2_completion"),
            ("D1", "d1_completion"),
        )
    ]
    return {
        "harness": HARNESS,
        "run_id": run_id,
        "stage": "R1",
        "session_id": session_id,
        "status": "ready",
        "design_artifact": "package-manifest.json",
        "design_artifact_sha256": sha256(
            package_dir / "package-manifest.json"
        ),
        "validation": {
            "path": "validation.json",
            "sha256": sha256(package_dir / "validation.json"),
            "verdict": "ready",
        },
        "input_completions": inputs,
        "run_state": clean_reference(
            package_dir, gate.get("run_state"), "run-state"
        ),
        "final_author_approval": reference(package_dir, approval_path),
        "independent_handoff": {
            "path": "independent-handoff.json",
            "sha256": sha256(package_dir / "independent-handoff.json"),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and canonically validate an R1 completion."
    )
    parser.add_argument("package_directory", type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--final-approval", required=True, type=Path)
    parser.add_argument("--output", default="stage-completion.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    approval_path = args.final_approval.resolve()
    output = (package_dir / args.output).resolve()
    if output.parent != package_dir:
        print("FAIL: output must stay inside the R1 package directory")
        return 1
    temporary = output.with_name(f".{output.name}.{os.getpid()}.candidate")
    try:
        validate_package(package_dir)
        completion = build_completion(
            package_dir, approval_path, args.session_id
        )
        temporary.write_text(
            json.dumps(completion, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        process = subprocess.run(
            [sys.executable, str(HARNESS_VALIDATOR), str(temporary)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=90,
        )
        if process.returncode != 0:
            detail = (process.stdout or process.stderr).strip()
            raise ValueError(
                "main harness rejected the candidate completion"
                + (f": {detail}" if detail else "")
            )
        os.replace(temporary, output)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        if temporary.exists():
            temporary.unlink()
        print(f"FAIL: {exc}")
        return 1
    print(f"OK: wrote validated R1 completion: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
