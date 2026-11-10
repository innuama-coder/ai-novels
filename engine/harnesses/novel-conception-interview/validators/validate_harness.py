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
    "schemas/interview-plan.schema.json",
    "schemas/interview-event.schema.json",
    "schemas/stage-completion.schema.json",
    "schemas/control-projection.schema.json",
    "schemas/fact-dependency-register.schema.json",
    "schemas/independent-handoff.schema.json",
    "validators/validate_session.py",
    "validators/validate_stage_completion.py",
    "validators/validate_control_projection.py",
    "validators/validate_fact_dependency_register.py",
    "tools/render_report.py",
    "evals/run_evals.py",
]

B0_CONTRACT_FILES = [
    "schemas/control-projection.schema.json",
    "schemas/fact-dependency-register.schema.json",
    "validators/validate_control_projection.py",
    "validators/validate_fact_dependency_register.py",
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

    for schema_path in (root / "schemas").glob("*.json"):
        try:
            json.loads(schema_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON schema {schema_path}: {exc}")

    manifest_path = root / "manifest.yaml"
    if manifest_path.is_file():
        manifest_text = manifest_path.read_text(encoding="utf-8-sig")
        for line in (
            "name: novel-conception-interview",
            "version: 1.0.0",
            "status: frozen",
            "release_date: 2026-08-05",
        ):
            if line not in manifest_text:
                errors.append(f"release manifest omits frozen product identity: {line}")
        for rel in B0_CONTRACT_FILES:
            if f"- {rel}" not in manifest_text:
                errors.append(f"portable manifest omits B0 contract file: {rel}")
        if "two downstream\n  design gates" in manifest_text:
            errors.append("manifest still defines legacy downstream design gates")

    agent_path = root / "agent.md"
    if agent_path.is_file():
        agent_text = agent_path.read_text(encoding="utf-8-sig")
        if "D1 and R1 have consumed" in agent_text:
            errors.append("agent completion criteria still require legacy D1/R1")
        for token in (
            "approved V2's HTML brief",
            "admissible\nas B0 input to the autonomous conception workflow",
            "D1/R1 are legacy",
        ):
            if token not in agent_text:
                errors.append(f"agent completion criteria omit current handoff: {token}")

    completion_schema_path = root / "schemas" / "stage-completion.schema.json"
    if completion_schema_path.is_file():
        try:
            completion_schema = json.loads(
                completion_schema_path.read_text(encoding="utf-8-sig")
            )
        except json.JSONDecodeError:
            completion_schema = {}
        properties = completion_schema.get("properties", {})
        if completion_schema.get("additionalProperties") is not False:
            errors.append("stage completion schema must reject unknown fields")
        for field in ("contract_version", "control_projection", "fact_dependency_register"):
            if field not in properties:
                errors.append(f"stage completion schema omits B0 field: {field}")

    completion_validator_path = root / "validators" / "validate_stage_completion.py"
    if completion_validator_path.is_file():
        validator_text = completion_validator_path.read_text(encoding="utf-8-sig")
        for token in (
            "CONTROL_PROJECTION_VALIDATOR",
            "FACT_DEPENDENCY_VALIDATOR",
            "validate_bound_contract_artifact",
            'packet.get("contract_version") != "2.0"',
        ):
            if token not in validator_text:
                errors.append(
                    f"stage completion validator is not wired to B0 contract: {token}"
                )

    for path in root.rglob("*.md"):
        if "TODO" in path.read_text(encoding="utf-8-sig"):
            errors.append(f"unresolved TODO in {path.relative_to(root)}")

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

