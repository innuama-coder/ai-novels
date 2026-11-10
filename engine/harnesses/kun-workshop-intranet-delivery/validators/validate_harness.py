#!/usr/bin/env python3
"""Validate the structural completeness of a harness bundle."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FILES = [
    "manifest.yaml",
    "agent.md",
    "workflow.md",
    "rules.md",
    "docs/scope-definition.md",
    "docs/delivery-spec.md",
    "docs/development-process.md",
    "docs/application-spec.md",
    "docs/adapter-authoring-guide.md",
    "docs/release-model.md",
    "docs/evaluation-rubric.md",
    "docs/using-harness-workflow-designer.md",
    "tools/build_release.py",
    "schemas/handoff.schema.json",
]

RUNTIME_ENTRIES = {
    "codex": "system-prompt.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "openclaw": "OPENCLAW.md",
    "hermas": "HERMAS.md",
}
REQUIRED_EVAL_CASES = ["positive.md", "negative.md", "boundary.md"]
REQUIRED_EVAL_HEADINGS = ["## Prompt", "## Expected Behavior", "## Forbidden Behavior", "## Scoring Rule", "## Pass Bar"]


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def require_file(root: Path, rel: str, errors: list[str]) -> None:
    path = root / rel
    if not path.is_file():
        errors.append(f"missing required file: {rel}")
    elif path.stat().st_size == 0:
        errors.append(f"empty required file: {rel}")


def validate(root: Path) -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        require_file(root, rel, errors)

    for adapter, entry_file in RUNTIME_ENTRIES.items():
        adapter_root = root / "adapters" / adapter
        if not adapter_root.is_dir():
            errors.append(f"missing adapter directory: adapters/{adapter}")
            continue
        for filename in ["install.md", "mapping.md", entry_file]:
            require_file(root, f"adapters/{adapter}/{filename}", errors)

    for case in REQUIRED_EVAL_CASES:
        rel = f"evals/cases/{case}"
        require_file(root, rel, errors)
        path = root / rel
        if path.is_file():
            text = path.read_text(encoding="utf-8-sig")
            for heading in REQUIRED_EVAL_HEADINGS:
                if heading not in text:
                    errors.append(f"eval case {rel} missing heading: {heading}")

    schema_path = root / "schemas" / "handoff.schema.json"
    if schema_path.is_file():
        try:
            json.loads(schema_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON schema {schema_path}: {exc}")

    if errors:
        for error in errors:
            fail(error)
        print(f"\n{len(errors)} structural issue(s) found.")
        return 1

    ok(f"harness bundle is structurally complete: {root}")
    return 0


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    if not root.exists():
        fail(f"root does not exist: {root}")
        return 1
    return validate(root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

