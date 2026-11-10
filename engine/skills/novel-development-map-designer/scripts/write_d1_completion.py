#!/usr/bin/env python3
"""Create a D1 completion only after the complete package passes the main harness."""
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
INTERVIEW_STAGES = ("I0", "I1", "I2", "I3", "I4", "I5")
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


def clean_reference(reference: Any, label: str) -> dict[str, str]:
    if not isinstance(reference, dict):
        raise ValueError(f"{label} is not a reference")
    path = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(path, str) or not path:
        raise ValueError(f"{label}.path is missing")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in digest)
    ):
        raise ValueError(f"{label}.sha256 is invalid")
    return {"path": path, "sha256": digest.lower()}


def build_completion(package_dir: Path, session_id: str) -> dict[str, Any]:
    map_data = load_json(package_dir / "map-data.json")
    validation = load_json(package_dir / "validation.json")
    manifest = load_json(package_dir / "package-manifest.json")
    if (
        map_data.get("schema_version") != "4.0"
        or map_data.get("harness") != HARNESS
        or map_data.get("status") != "ready"
    ):
        raise ValueError("map-data.json is not a ready D1 4.0 model")
    run_id = map_data.get("run_id")
    if (
        not isinstance(run_id, str)
        or not run_id
        or validation.get("run_id") != run_id
        or validation.get("verdict") != "ready"
        or manifest.get("run_id") != run_id
        or manifest.get("verdict") != "ready"
    ):
        raise ValueError("D1 package records do not identify one ready run")
    gate = map_data.get("input_gate")
    if not isinstance(gate, dict):
        raise ValueError("map-data.json lacks input_gate")
    interviews = gate.get("interview_completions")
    if not isinstance(interviews, list):
        raise ValueError("input_gate.interview_completions is invalid")
    by_stage: dict[str, dict[str, str]] = {}
    for item in interviews:
        if not isinstance(item, dict) or item.get("stage") not in INTERVIEW_STAGES:
            raise ValueError("input_gate contains an invalid interview completion")
        stage = item["stage"]
        if stage in by_stage:
            raise ValueError(f"input_gate duplicates {stage}")
        by_stage[stage] = clean_reference(item, f"{stage} completion")
    if set(by_stage) != set(INTERVIEW_STAGES):
        raise ValueError("input_gate must contain exactly I0-I5")
    inputs = [by_stage[stage] for stage in INTERVIEW_STAGES]
    inputs.extend(
        [
            clean_reference(gate.get("v1_completion"), "V1 completion"),
            clean_reference(gate.get("v2_completion"), "V2 completion"),
        ]
    )
    manifest_path = package_dir / "package-manifest.json"
    validation_path = package_dir / "validation.json"
    return {
        "harness": HARNESS,
        "run_id": run_id,
        "stage": "D1",
        "session_id": session_id,
        "status": "ready",
        "design_artifact": manifest_path.name,
        "design_artifact_sha256": sha256(manifest_path),
        "validation": {
            "path": validation_path.name,
            "sha256": sha256(validation_path),
            "verdict": "ready",
        },
        "input_completions": inputs,
        "run_state": clean_reference(gate.get("run_state"), "run_state"),
        "author_approval": clean_reference(
            gate.get("author_approval"), "V2 author approval"
        ),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and canonically validate a D1 stage completion."
    )
    parser.add_argument("package_directory", type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--output", default="stage-completion.json")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    output = (package_dir / args.output).resolve()
    if output.parent != package_dir:
        print("FAIL: output must stay inside the D1 package directory")
        return 1
    temporary = output.with_name(f".{output.name}.{os.getpid()}.candidate")
    try:
        completion = build_completion(package_dir, args.session_id)
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
            timeout=60,
        )
        if process.returncode != 0:
            detail = (process.stdout or process.stderr).strip()
            raise ValueError(
                "main harness rejected the candidate completion"
                + (f": {detail}" if detail else "")
            )
        os.replace(temporary, output)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        if temporary.exists():
            temporary.unlink()
        print(f"FAIL: {exc}")
        return 1
    print(f"OK: wrote validated D1 completion: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
