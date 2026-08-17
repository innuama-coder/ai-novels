"""Validate the exact production skill owners and an optional release lock."""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DependencyValidationReport:
    ok: bool
    errors: tuple[str, ...]
    checked: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_root(harness_root: Path) -> Path:
    candidate = harness_root.parents[1]
    if (candidate / "skills").is_dir() and (candidate / "docs").is_dir():
        return candidate
    raise ValueError("dependency repository root is not repo-shaped")


def _frontmatter_name(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _public_symbols(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    exported: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            for item in node.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    exported.add(item.value)
    return definitions, exported


def _literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if isinstance(node.target, ast.Name) and node.target.id == name:
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal assignment {name}")


def load_dependency_spec(harness_root: str | Path) -> dict[str, Any]:
    path = Path(harness_root).resolve() / "dependency-spec.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("dependency spec must be an object")
    return value


def dependency_files(repository: str | Path, spec: dict[str, Any]) -> tuple[Path, ...]:
    root = Path(repository).resolve()
    files: list[Path] = []
    for owner in spec["stage_owners"]:
        skill_root = root / owner["path"]
        files.extend(path for path in skill_root.rglob("*") if path.is_file())
    for dependency in spec.get("quality_gate_dependencies", []):
        skill_root = root / dependency["path"]
        files.extend(path for path in skill_root.rglob("*") if path.is_file())
        files.append(root / dependency["contract_schema"])
    workflow = root / "docs" / "ai-novel-workflow" / "conception-autonomous-workflow-v2.md"
    contracts = root / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
    files.append(workflow)
    files.extend(path for path in contracts.rglob("*") if path.is_file())
    return tuple(sorted(set(files), key=lambda item: item.relative_to(root).as_posix()))


def build_dependency_lock(repository: str | Path, spec: dict[str, Any]) -> dict[str, Any]:
    root = Path(repository).resolve()
    return {
        "schema_version": "2.1",
        "workflow": spec["workflow"],
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
            for path in dependency_files(root, spec)
        ],
    }


def validate_dependencies(harness_root: str | Path, *, require_lock: bool = False) -> DependencyValidationReport:
    base = Path(harness_root).resolve()
    errors: list[str] = []
    checked: list[str] = []
    try:
        repository = _repository_root(base)
        spec = load_dependency_spec(base)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, IndexError) as error:
        return DependencyValidationReport(False, (f"HARN_DEPENDENCY_SPEC_INVALID:{error}",), ())
    owners = spec.get("stage_owners")
    if (
        spec.get("schema_version") != "2.1"
        or spec.get("workflow") != "novel-conception-autonomous-v2"
        or not isinstance(owners, list)
        or len(owners) != 10
    ):
        errors.append("HARN_DEPENDENCY_SPEC_INVALID")
        owners = owners if isinstance(owners, list) else []
    stages: set[str] = set()
    skills: set[str] = set()
    forbidden = set(spec.get("forbidden_skill_names", ()))
    quality_dependencies = spec.get("quality_gate_dependencies")
    expected_quality_dependency = {
        "gate": "H1-A-presentation-fidelity",
        "skill": "novel-conception-presentation-fidelity-reviewer",
        "path": "skills/novel-conception-presentation-fidelity-reviewer",
        "contract_schema": (
            "docs/ai-novel-workflow/contracts/autonomous-v2/"
            "presentation-fidelity-review.schema.json"
        ),
        "consumer_stage": "H1-A",
        "consumer_api": "run_assemble",
    }
    if quality_dependencies != [expected_quality_dependency]:
        errors.append("HARN_QUALITY_GATE_DEPENDENCY_INVALID")
    else:
        dependency = quality_dependencies[0]
        skill_root = repository / dependency["path"]
        schema_path = repository / dependency["contract_schema"]
        consumer = next(
            (
                owner for owner in owners
                if isinstance(owner, dict)
                and owner.get("stage") == dependency["consumer_stage"]
            ),
            None,
        )
        consumer_runtime = (
            repository / consumer["path"] / consumer["runtime"]
            if consumer is not None else None
        )
        checked.extend((
            "quality-gate:H1-A-presentation-fidelity",
            "quality-gate:contract-schema",
            "quality-gate:consumer",
        ))
        if _frontmatter_name(skill_root / "SKILL.md") != dependency["skill"]:
            errors.append("HARN_QUALITY_GATE_SKILL_INVALID")
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append("HARN_QUALITY_GATE_SCHEMA_INVALID")
        try:
            definitions, _ = _public_symbols(consumer_runtime)
            source = consumer_runtime.read_text(encoding="utf-8")
            if (
                dependency["consumer_api"] not in definitions
                or "validate_presentation_fidelity_review" not in definitions
                or "H1A_FIDELITY_REVIEW_REQUIRED" not in source
                or '"presentation_fidelity_review"' not in source
            ):
                errors.append("HARN_QUALITY_GATE_CONSUMER_INVALID")
        except (OSError, UnicodeError, SyntaxError, TypeError):
            errors.append("HARN_QUALITY_GATE_CONSUMER_INVALID")
    for owner in owners:
        if not isinstance(owner, dict):
            errors.append("HARN_DEPENDENCY_OWNER_INVALID")
            continue
        stage = owner.get("stage")
        skill = owner.get("skill")
        relative = owner.get("path")
        runtime_relative = owner.get("runtime")
        apis = owner.get("apis")
        if (
            not all(isinstance(value, str) and value for value in (stage, skill, relative, runtime_relative))
            or not isinstance(apis, list)
            or not apis
            or any(not isinstance(api, str) or not api for api in apis)
        ):
            errors.append(f"HARN_DEPENDENCY_OWNER_INVALID:{stage}")
            continue
        if stage in stages or skill in skills or skill in forbidden:
            errors.append(f"HARN_DEPENDENCY_OWNER_CONFLICT:{stage}")
        stages.add(stage)
        skills.add(skill)
        skill_root = repository / relative
        skill_md = skill_root / "SKILL.md"
        runtime_path = skill_root / runtime_relative
        checked.extend((f"skill:{skill}", f"runtime:{stage}"))
        if _frontmatter_name(skill_md) != skill:
            errors.append(f"HARN_DEPENDENCY_SKILL_INVALID:{skill}")
        try:
            definitions, exported = _public_symbols(runtime_path)
        except (OSError, UnicodeError, SyntaxError):
            errors.append(f"HARN_DEPENDENCY_RUNTIME_INVALID:{stage}")
            continue
        for api in apis:
            if api not in definitions or api not in exported:
                errors.append(f"HARN_DEPENDENCY_API_MISSING:{stage}:{api}")
    expected_stages = {"S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1-A", "H1-B", "H1-C"}
    if stages != expected_stages:
        errors.append("HARN_DEPENDENCY_STAGE_SET_INVALID")
    if "novel-development-map-designer" not in forbidden:
        errors.append("HARN_DEPENDENCY_LEGACY_POLICY_INVALID")
    try:
        action_contract = _literal_assignment(
            base / "runtime" / "production_orchestrator.py", "ACTION_CONTRACT"
        )
        by_stage = {owner["stage"]: owner["skill"] for owner in owners}
        expected_actions = {
            "B0": ("B0", "baseline-controller"),
            "S1": ("S1", by_stage["S1"]),
            "W1": ("W1", by_stage["W1"]),
            "E1": ("E1", by_stage["E1"]),
            "T1": ("T1", by_stage["T1"]),
            "C1": ("C1", by_stage["C1"]),
            "Q1": ("Q1", by_stage["Q1"]),
            "P1": ("P1", by_stage["P1"]),
            "H1-A-plan": ("H1", by_stage["H1-A"]),
            "H1-B": ("H1", by_stage["H1-B"]),
            "H1-A-assemble": ("H1", by_stage["H1-A"]),
            "H1-C": ("H1", by_stage["H1-C"]),
            "H1-publish": ("H1", "production-orchestrator"),
            "author-decision": (None, "external-author-forwarder"),
            "final": (None, "production-orchestrator"),
        }
        checked.append("dependencies:action-contract")
        if action_contract != expected_actions:
            errors.append("HARN_DEPENDENCY_ACTION_CONTRACT_INVALID")
        if any(owner in forbidden for _, owner in action_contract.values()):
            errors.append("HARN_DEPENDENCY_LEGACY_OWNER_ACTIVE")
    except (KeyError, OSError, UnicodeError, SyntaxError, ValueError):
        errors.append("HARN_DEPENDENCY_ACTION_CONTRACT_INVALID")

    lock_path = base / "dependency-lock.json"
    if require_lock and not lock_path.is_file():
        errors.append("HARN_DEPENDENCY_LOCK_MISSING")
    if lock_path.is_file():
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            expected = build_dependency_lock(repository, spec)
            checked.append("dependencies:lock")
            if lock != expected:
                errors.append("HARN_DEPENDENCY_LOCK_MISMATCH")
        except (OSError, UnicodeError, ValueError, KeyError, json.JSONDecodeError):
            errors.append("HARN_DEPENDENCY_LOCK_INVALID")
    return DependencyValidationReport(not errors, tuple(errors), tuple(checked))


__all__ = [
    "DependencyValidationReport",
    "build_dependency_lock",
    "dependency_files",
    "load_dependency_spec",
    "validate_dependencies",
]
