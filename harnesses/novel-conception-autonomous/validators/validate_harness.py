"""Static, portable harness validator with a CLI-compatible report."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    errors: tuple[str, ...]
    checked: tuple[str, ...]


_REQUIRED = (
    "manifest.yaml",
    "agent.md",
    "workflow.md",
    "rules.md",
    "runtime/harness.py",
    "runtime/production_orchestrator.py",
    "runtime/production_coordinator.py",
    "runtime/production_store.py",
    "adapters/codex/SKILL.md",
    "adapters/codex/install.md",
    "adapters/codex/mapping.md",
    "tools/build_release.py",
    "requirements.txt",
    "docs/input-contract.md",
    "docs/output-contract.md",
    "docs/final-delivery-contract.md",
    "docs/validation-and-release.md",
    "schemas/schema-index.json",
    "dependency-spec.json",
    "validators/validate_dependencies.py",
)
_TERMINAL_PARAMETERS = (
    "output_root", "coordinator", "stage_packages", "p1_package",
    "plan_package", "plan_input_gate", "plan_workspace_state",
    "fragment_package", "fragment_workspace_state", "assembly_package",
    "assembly_workspace_state", "html_package", "rendered_workspace",
    "author_event", "development_handoff", "next_state_paths", "runtime",
)
_STAGES = (
    "B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1",
    "H1-A-plan", "H1-B", "H1-A-assemble", "H1-C", "H1",
    "author-decision", "final",
)
_EDGES = (
    ("B0", "S1"), ("S1", "W1"), ("W1", "E1"), ("E1", "T1"),
    ("T1", "C1"), ("C1", "Q1"), ("Q1", "P1"),
    ("P1", "H1-A-plan"), ("H1-A-plan", "H1-B"),
    ("H1-B", "H1-A-assemble"), ("H1-A-assemble", "H1-C"),
    ("H1-C", "H1"), ("H1", "author-decision"),
    ("author-decision", "final"),
)
_ROUTES = (
    ("approved", "final", True),
    ("revise", "routed-return", False),
    ("rejected", "terminal-rejected", False),
)
_ADAPTER_STATUSES = ("native", "prompt", "tool", "manual", "unsupported")
_ADAPTER_STEPS = (
    (1, "verify-approved-interview-input"),
    (2, "initialize-or-resume-production-run"),
    (3, "dispatch-exact-stage-owner"),
    (4, "persist-and-revalidate-transaction"),
    (5, "forward-external-author-decision"),
    (6, "report-authoritative-result"),
)
_ADAPTER_MAPPINGS = (
    (
        "approved-interview-input", "manual", "interview-workflow",
        "verify-and-bind",
    ),
    (
        "production-run-state", "native", "production-orchestrator",
        "persist-and-report",
    ),
    (
        "domain-content-generation", "prompt", "exact-stage-owner",
        "dispatch-work-order",
    ),
    (
        "external-author-decision", "manual", "external-author",
        "verify-and-forward",
    ),
    (
        "terminal-compatibility", "tool", "portable-runtime",
        "legacy-api-compatibility-only",
    ),
    ("legacy-d1-r1", "unsupported", "none", "reject"),
)
_OUTPUT_ROOT_CONTRACT = {
    "schema_version": "2.0",
    "fresh": ["absent", "empty-real-directory"],
    "retry": {
        "allowed_shape": "H1/stage",
        "scope": "h1-publication-orphan-only",
        "content_validator": "formal-h1-publisher",
    },
    "root_entry": {
        "symlink": False,
        "reparse_alias": False,
        "parent_resolution": "platform-normal",
    },
    "forbidden_residue": [
        "D1",
        "R1",
        "author-decision",
        "completion",
        "final",
        "terminal",
        "sibling",
        "extra",
    ],
    "later_transaction_recovery": False,
    "author_decision_basename_enforced": False,
}
_STALE_OUTPUT_ROOT_TEXT = (
    "`output_root`: empty destination namespace",
    "`HARN_OUTPUT_ROOT_INVALID`: the requested invocation root is not empty.",
)


def _marked_json(text: str, marker: str) -> dict:
    match = re.fullmatch(
        rf"[\s\S]*<!-- {re.escape(marker)}:BEGIN -->\n"
        rf"(?P<body>\{{[\s\S]*\}})\n"
        rf"<!-- {re.escape(marker)}:END -->[\s\S]*",
        text,
    )
    if match is None:
        raise ValueError(f"missing {marker}")
    value = json.loads(match.group("body"))
    if not isinstance(value, dict):
        raise ValueError(f"{marker} must be an object")
    return value


def validate_harness(root=None):
    base = (
        Path(root).resolve()
        if root is not None
        else Path(__file__).resolve().parents[1]
    )
    errors: list[str] = []
    checked: list[str] = []
    manifest: dict = {}
    for relative in _REQUIRED:
        path = base / relative
        checked.append(relative)
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"HARN_FILE_MISSING:{relative}")
    output_root_contracts = []
    for relative in ("docs/input-contract.md", "rules.md"):
        path = base / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
            output_root_contracts.append(
                _marked_json(text, "OUTPUT-ROOT-CONTRACT")
            )
            if any(stale in text for stale in _STALE_OUTPUT_ROOT_TEXT):
                errors.append("HARN_OUTPUT_ROOT_CONTRACT_INVALID")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            errors.append("HARN_OUTPUT_ROOT_CONTRACT_INVALID")
    if (
        len(output_root_contracts) != 2
        or any(
            contract != _OUTPUT_ROOT_CONTRACT
            for contract in output_root_contracts
        )
    ):
        errors.append("HARN_OUTPUT_ROOT_CONTRACT_INVALID")
    checked.append("docs:output-root-contract")
    manifest_path = base / "manifest.yaml"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checked.append("manifest:json-yaml")
            if (
                manifest.get("schema_version") != "2.1"
                or manifest.get("name") != "novel-conception-autonomous"
                or manifest.get("version") != "1.0.0"
                or manifest.get("status") != "frozen"
                or manifest.get("release_date") != "2026-08-05"
                or manifest.get("workflow") != "novel-conception-autonomous-v2"
                or manifest.get("entrypoint")
                != "runtime.production_orchestrator:initialize_production_run"
                or manifest.get("resume_entrypoint")
                != "runtime.production_orchestrator:resume_production_run"
                or manifest.get("terminal_compatibility_entrypoint")
                != "runtime.harness:run_from_rendered_h1"
                or manifest.get("validator")
                != "validators.validate_harness:validate_harness"
                or manifest.get("dependency_spec") != "dependency-spec.json"
                or manifest.get("dependency_lock") != "dependency-lock.json"
            ):
                errors.append("HARN_MANIFEST_VERSION_INVALID")
            if manifest.get("legacy_profiles_forbidden") != ["D1", "R1"]:
                errors.append("HARN_LEGACY_POLICY_INVALID")
            if manifest.get("forbidden_skill_names") != [
                "novel-development-map-designer"
            ]:
                errors.append("HARN_LEGACY_POLICY_INVALID")
            if tuple(manifest.get("stages", ())) != _STAGES:
                errors.append("HARN_MANIFEST_STAGES_INVALID")
            if tuple(
                tuple(edge) for edge in manifest.get("edges", ())
            ) != _EDGES:
                errors.append("HARN_MANIFEST_GRAPH_INVALID")
            routes = tuple(
                (
                    item.get("decision"),
                    item.get("result"),
                    item.get("produces_final"),
                )
                for item in manifest.get("decision_routes", ())
                if isinstance(item, dict)
            )
            adapter_contract = manifest.get("adapter_contract")
            adapter_steps = tuple(
                (item.get("order"), item.get("id"))
                for item in (
                    adapter_contract.get("ordered_steps", ())
                    if isinstance(adapter_contract, dict) else ()
                )
                if isinstance(item, dict)
            )
            adapter_mappings = tuple(
                (
                    item.get("id"), item.get("status"), item.get("owner"),
                    item.get("adapter_role"),
                )
                for item in (
                    adapter_contract.get("mappings", ())
                    if isinstance(adapter_contract, dict) else ()
                )
                if isinstance(item, dict)
            )
            if (
                routes != _ROUTES
                or manifest.get("author_branches")
                != {"approved": "final", "revise": None, "rejected": None}
                or manifest.get("next_state_paths")
                != ["h1", "approved", "revise", "rejected", "final"]
            ):
                errors.append("HARN_MANIFEST_ROUTES_INVALID")
            if (
                not isinstance(adapter_contract, dict)
                or tuple(adapter_contract.get("status_enum", ()))
                != _ADAPTER_STATUSES
                or adapter_steps != _ADAPTER_STEPS
                or adapter_contract.get("authority")
                != {
                    "author_decision": "external-author",
                    "run_state": "production-orchestrator",
                    "domain_content": "exact-stage-owner",
                }
                or adapter_contract.get("forbidden")
                != [
                    "synthesize-author-decision", "own-run-state",
                    "redefine-run-state", "legacy-success",
                    "semantic-owner-fallback", "bypass-work-order",
                ]
                or adapter_mappings != _ADAPTER_MAPPINGS
            ):
                errors.append("HARN_MANIFEST_ADAPTER_CONTRACT_INVALID")
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append("HARN_MANIFEST_INVALID")
    runner = base / "runtime" / "harness.py"
    if runner.is_file():
        try:
            tree = ast.parse(runner.read_text(encoding="utf-8"))
            function = next(
                node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "run_from_rendered_h1"
            )
            names = tuple(argument.arg for argument in function.args.args) + tuple(
                argument.arg for argument in function.args.kwonlyargs
            )
            checked.append("runtime:public-api")
            if names != _TERMINAL_PARAMETERS:
                errors.append("HARN_PUBLIC_API_INVALID")
            if (
                tuple(argument.arg for argument in function.args.args)
                != ("output_root",)
                or len(function.args.kw_defaults) != 16
                or function.args.kw_defaults[-1] is None
            ):
                errors.append("HARN_PUBLIC_API_KIND_INVALID")
        except (OSError, UnicodeError, SyntaxError, StopIteration):
            errors.append("HARN_RUNTIME_INVALID")
    production_runner = base / "runtime" / "production_orchestrator.py"
    if production_runner.is_file():
        try:
            tree = ast.parse(production_runner.read_text(encoding="utf-8"))
            functions = {
                node.name: node
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
            }
            required_functions = {
                "initialize_production_run",
                "resume_production_run",
                "issue_stage_work",
                "initialize_h1_workspace",
                "execute_stage_work",
                "recover_stage_admission",
                "commit_h1_workspace",
                "recover_h1_workspace",
                "publish_h1_transaction",
                "record_author_transaction",
                "publish_final_transaction",
            }
            exports = set()
            for node in tree.body:
                if not isinstance(node, ast.Assign):
                    continue
                if not any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                ):
                    continue
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    exports.update(
                        item.value
                        for item in node.value.elts
                        if isinstance(item, ast.Constant)
                        and isinstance(item.value, str)
                    )
            checked.append("runtime:production-api")
            if (
                not required_functions <= set(functions)
                or not required_functions <= exports
                or any(
                    "actor"
                    not in {
                        argument.arg
                        for argument in functions[name].args.kwonlyargs
                    }
                    for name in {
                        "execute_stage_work",
                        "recover_stage_admission",
                        "commit_h1_workspace",
                        "recover_h1_workspace",
                    }
                )
            ):
                errors.append("HARN_PRODUCTION_API_INVALID")
        except (OSError, UnicodeError, SyntaxError):
            errors.append("HARN_PRODUCTION_RUNTIME_INVALID")
    production_store = base / "runtime" / "production_store.py"
    if production_store.is_file():
        try:
            tree = ast.parse(production_store.read_text(encoding="utf-8"))
            store_class = next(
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == "ProductionRunStore"
            )
            methods = {
                node.name
                for node in store_class.body
                if isinstance(node, ast.FunctionDef)
            }
            required_store_methods = {
                "persist_state",
                "latest_state",
                "persist_workspace",
                "latest_workspace",
                "issue_work_order",
                "pending_work_order",
                "require_current_work_order",
                "mark_work_order_consumed",
            }
            checked.append("runtime:production-store-api")
            if not required_store_methods <= methods:
                errors.append("HARN_PRODUCTION_STORE_API_INVALID")
        except (OSError, UnicodeError, SyntaxError, StopIteration):
            errors.append("HARN_PRODUCTION_STORE_API_INVALID")
    production_coordinator = base / "runtime" / "production_coordinator.py"
    if production_coordinator.is_file():
        try:
            tree = ast.parse(production_coordinator.read_text(encoding="utf-8"))
            owner_class = next(
                node for node in tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == "ProductionCoordinator"
            )
            methods = {
                node.name for node in owner_class.body
                if isinstance(node, ast.FunctionDef)
            }
            checked.append("runtime:production-coordinator-api")
            if methods != {"refresh_active_stage_return"}:
                errors.append("HARN_PRODUCTION_COORDINATOR_API_INVALID")
        except (OSError, UnicodeError, SyntaxError, StopIteration):
            errors.append("HARN_PRODUCTION_COORDINATOR_API_INVALID")
    schema_index_path = base / "schemas" / "schema-index.json"
    if schema_index_path.is_file():
        try:
            index = json.loads(schema_index_path.read_text(encoding="utf-8"))
            checked.append("schemas:index")
            bundled = schema_index_path.parent / "bundled"
            authority = (
                schema_index_path.parent / index["authority"]
            ).resolve()
            schema_root = bundled if bundled.is_dir() else authority
            if (
                index.get("schema_version") != "2.0"
                or index.get("legacy_profiles_forbidden") != ["D1", "R1"]
            ):
                errors.append("HARN_SCHEMA_INDEX_INVALID")
            for name in index.get("required", ()):
                path = schema_root / name
                if not path.is_file():
                    errors.append(f"HARN_SCHEMA_MISSING:{name}")
                    continue
                json.loads(path.read_text(encoding="utf-8"))
                checked.append(f"schema:{name}")
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError):
            errors.append("HARN_SCHEMA_INDEX_INVALID")
    cases_root = base / "evals" / "cases"
    positive = 0
    negative = 0
    identities: set[str] = set()
    for path in sorted(cases_root.glob("*.json"), key=lambda item: item.name):
        try:
            case = json.loads(path.read_text(encoding="utf-8"))
            checked.append(f"eval:{path.name}")
            required = {"id", "kind", "Prompt", "Expected", "Forbidden", "Scoring", "Pass Bar"}
            if set(case) != required or case["id"] in identities:
                errors.append(f"HARN_EVAL_CONTRACT_INVALID:{path.name}")
                continue
            identities.add(case["id"])
            if (
                case["kind"] not in {"positive", "negative"}
                or not isinstance(case["Prompt"], str)
                or not case["Prompt"].strip()
                or not isinstance(case["Expected"], list)
                or not case["Expected"]
                or not isinstance(case["Forbidden"], list)
                or not case["Forbidden"]
                or not isinstance(case["Scoring"], dict)
                or not case["Scoring"]
                or any(
                    not isinstance(score, int) or isinstance(score, bool) or score <= 0
                    for score in case["Scoring"].values()
                )
                or case["Pass Bar"] != sum(case["Scoring"].values())
            ):
                errors.append(f"HARN_EVAL_CONTRACT_INVALID:{path.name}")
            positive += case["kind"] == "positive"
            negative += case["kind"] == "negative"
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
            errors.append(f"HARN_EVAL_CONTRACT_INVALID:{path.name}")
    if positive < 3 or negative < 5:
        errors.append("HARN_EVAL_COVERAGE_INVALID")
    adapter = base / "adapters" / "codex" / "SKILL.md"
    if adapter.is_file():
        try:
            text = adapter.read_text(encoding="utf-8")
            checked.append("adapter:codex-frontmatter")
            embedded = _marked_json(text, "ADAPTER-CONTRACT")
            numbered = tuple(
                (int(match.group(1)), match.group(2))
                for line in text.splitlines()
                if (match := re.match(
                    r"^([1-6])\. .*\(`([^`]+)`\)$", line
                ))
            )
            expected_embedded = {
                "schema_version": "2.1",
                "manifest_name": manifest["name"],
                "entrypoint": manifest["entrypoint"],
                "resume_entrypoint": manifest["resume_entrypoint"],
                "ordered_steps": manifest["adapter_contract"]["ordered_steps"],
                "authority": manifest["adapter_contract"]["authority"],
                "forbidden": manifest["adapter_contract"]["forbidden"],
            }
            if (
                not text.startswith("---\nname: novel-conception-autonomous\n")
                or embedded != expected_embedded
                or numbered != _ADAPTER_STEPS
            ):
                errors.append("HARN_ADAPTER_INVALID")
        except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError):
            errors.append("HARN_ADAPTER_INVALID")
    mapping_path = base / "adapters" / "codex" / "mapping.md"
    if mapping_path.is_file():
        try:
            text = mapping_path.read_text(encoding="utf-8")
            checked.append("adapter:codex-mapping")
            embedded = _marked_json(text, "ADAPTER-MAPPING")
            mappings = tuple(
                (
                    item.get("id"), item.get("status"), item.get("owner"),
                    item.get("adapter_role"),
                )
                for item in embedded.get("mappings", ())
                if isinstance(item, dict)
            )
            rows = tuple(
                tuple(value.strip("` ") for value in match)
                for match in re.findall(
                    r"(?m)^\| `([^`]+)` \| `([^`]+)` \| "
                    r"`([^`]+)` \| `([^`]+)` \|$",
                    text,
                )
            )
            if (
                embedded.get("schema_version") != "2.1"
                or tuple(embedded.get("status_enum", ()))
                != _ADAPTER_STATUSES
                or mappings != _ADAPTER_MAPPINGS
                or rows != _ADAPTER_MAPPINGS
                or "must never synthesize an author decision" not in text
                or "mutate persisted run-state directly" not in text
                or "bypass the\ncurrent work order" not in text
            ):
                errors.append("HARN_ADAPTER_INVALID")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            errors.append("HARN_ADAPTER_INVALID")
    requirements = base / "requirements.txt"
    if requirements.is_file():
        checked.append("requirements:pinned")
        for line in requirements.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "==" not in stripped:
                errors.append("HARN_REQUIREMENTS_UNPINNED")
                break
    dependency_validator = base / "validators" / "validate_dependencies.py"
    if dependency_validator.is_file():
        try:
            module_name = f"_harness_dependencies_{abs(hash(str(dependency_validator)))}"
            spec = importlib.util.spec_from_file_location(
                module_name, dependency_validator
            )
            if spec is None or spec.loader is None:
                raise ImportError("dependency validator loader unavailable")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            dependency_report = module.validate_dependencies(
                base, require_lock=(base / "dependency-lock.json").is_file()
            )
            checked.extend(dependency_report.checked)
            errors.extend(dependency_report.errors)
        except (ImportError, OSError, UnicodeError, ValueError):
            errors.append("HARN_DEPENDENCY_VALIDATOR_INVALID")
    return ValidationReport(not errors, tuple(errors), tuple(checked))


def main() -> int:
    report = validate_harness(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({
        "ok": report.ok,
        "errors": list(report.errors),
        "checked": list(report.checked),
    }, ensure_ascii=False, indent=2))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
