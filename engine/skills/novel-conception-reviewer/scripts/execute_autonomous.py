#!/usr/bin/env python3
"""Official R1 autonomous-skill entrypoint: review, validate and seal a run."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from execution_record import write_record
from r1_generation_session import PHASES, read_json, seal_into_package


SCRIPT_DIR = Path(__file__).resolve().parent
RENDERER = SCRIPT_DIR / "render_conception_review.py"
VALIDATOR = SCRIPT_DIR / "validate_conception_review.py"


def run(command: list[str]) -> None:
    process = subprocess.run(
        command,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    if process.returncode != 0:
        detail = (process.stdout or process.stderr).strip()
        raise RuntimeError(detail or f"command failed: {' '.join(command)}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute and seal one autonomous R1 skill run."
    )
    parser.add_argument("generation_workspace", type=Path)
    parser.add_argument("package_directory", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    package_dir.mkdir(parents=True, exist_ok=True)
    workspace = args.generation_workspace.resolve()
    session = read_json(workspace / "generation-session.json")
    phases = session.get("phases")
    if not isinstance(phases, list) or len(phases) != len(PHASES):
        raise RuntimeError("generation workspace has not completed every R1 phase")
    final_record = phases[-1].get("artifact")
    if not isinstance(final_record, dict):
        raise RuntimeError("generation workspace lacks a final-review artifact")
    model = read_json(workspace / str(final_record.get("path", "")))
    if session.get("run_id") != model.get("run_id"):
        raise RuntimeError("generation session and final review run_id differ")
    seal_into_package(workspace, package_dir)
    model_path = package_dir / "review-data.json"
    model_path.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_record(
        package_dir,
        model,
    )
    run([sys.executable, str(RENDERER), str(package_dir)])
    run([sys.executable, str(VALIDATOR), str(package_dir), "--write-validation"])
    print(
        json.dumps(
            {
                "skill": "novel-conception-reviewer",
                "stage": "R1",
                "verdict": "ready",
                "package": str(package_dir),
                "author_approval_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
