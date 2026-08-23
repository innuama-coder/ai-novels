#!/usr/bin/env python3
"""Validate HLD structure and keep semantic release claims fail-closed."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.contracts import BOUNDED_EVAL_DIMENSIONS, HARNESS, STAGES  # noqa: E402
from runtime.schema_catalog import SchemaCatalog  # noqa: E402

REQUIRED_FILES = (
    "manifest.yaml", "MANIFEST.runtime.yaml", "agent.md", "workflow.md", "rules.md",
    "adapters/codex/install.md", "adapters/codex/mapping.md", "adapters/codex/operation.md", "adapters/codex/system-prompt.md",
    "validators/validate_harness.py", "validators/validate_instance.py", "tools/build_release.py",
    "tools/post_install_validate.py", "tools/validate_agentic_acceptance.py", "releases/0.1.0-acceptance.json", "docs/release-checklist.md",
    "runtime/coordinator.py", "runtime/run_coordinator.py", "runtime/owner_registry.py",
    "references/public-runtime-registry.json", "references/hld-identity-contract.json", "docs/coordinator-contract.md",
    "references/qualification-trust-anchor.json", "docs/agentic-qualification-contract.md",
)
CASE_IDS = (
    "HLD-E2E-P01", "HLD-E2E-N01", "HLD-E2E-B01", "HLD-E2E-R01", "HLD-E2E-R02",
    "HLD-COMPOSITE-P01", "HLD-COMPOSITE-N01", "HLD-COMPOSITE-B01",
    "HLD-COORDINATOR-P01", "HLD-COORDINATOR-N01", "HLD-COORDINATOR-B01", "HLD-COORDINATOR-R01", "HLD-COORDINATOR-R02",
)
CASE_HEADINGS = ("## Prompt", "## Sealed Fixture", "## Expected Behavior", "## Forbidden Behavior", "## Scoring Rule", "## Pass Bar")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(root: Path, *, require_test_anchors: bool = True) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            fail(errors, f"missing required file: {relative}")
    manifest_path = root / "manifest.yaml"
    manifest_status = None
    if manifest_path.is_file():
        text = manifest_path.read_text(encoding="utf-8")
        match = re.search(r"^status: ([a-z-]+)$", text, flags=re.MULTILINE)
        manifest_status = match.group(1) if match else None
        for needle in (f"name: {HARNESS}", "version: 0.1.0", "portable_core: true", "author_gate: required"):
            if needle not in text:
                fail(errors, f"manifest missing: {needle}")
        if manifest_status not in {"implementation-candidate", "release-candidate"}:
            fail(errors, "manifest status is not a supported gated state")
        listed = re.findall(r"^  - (H[A-Z0-9]+)$", text, flags=re.MULTILINE)
        if tuple(listed[: len(STAGES)]) != STAGES:
            fail(errors, f"manifest stage order mismatch: {listed[:len(STAGES)]}")
        if "  - codex" not in text or "unsupported_runtimes:" not in text:
            fail(errors, "runtime support declarations are incomplete")
    runtime_manifest_path=root/"MANIFEST.runtime.yaml";acceptance_path=root/"releases/0.1.0-acceptance.json";checklist_path=root/"docs/release-checklist.md";registry_path=root/"references/public-runtime-registry.json"
    if runtime_manifest_path.is_file():
        runtime_manifest=runtime_manifest_path.read_text(encoding="utf-8")
        for needle in ("runtime: codex", "operation_contract: adapters/codex/operation.md", "registered_skill_count: 15"):
            if needle not in runtime_manifest:fail(errors,f"runtime manifest missing: {needle}")
        expected_qualification="agentic_qualification: qualified" if manifest_status=="release-candidate" else "agentic_qualification: not-run"
        if f"status: {manifest_status}" not in runtime_manifest or expected_qualification not in runtime_manifest:fail(errors,"portable and runtime manifest status drift")
    if acceptance_path.is_file() and registry_path.is_file():
        try:
            acceptance=json.loads(acceptance_path.read_text(encoding="utf-8"));registry=json.loads(registry_path.read_text(encoding="utf-8"))["entries"]
            actual_skills={entry["skill"] for entry in registry.values() if not entry["skill"].startswith("harness-core/")}
            expected_cases=[f"HLD-COORDINATOR-{suffix}" for suffix in ("P01","N01","B01","R01","R02")]
            if acceptance.get("status")!=manifest_status or acceptance.get("version")!="0.1.0" or acceptance.get("stable_major") is not False:fail(errors,"release acceptance status/version/stability drift")
            if acceptance.get("registered_skill_count")!=len(actual_skills) or len(actual_skills)!=15 or acceptance.get("registry_token_count")!=len(registry) or len(registry)!=18:fail(errors,"release acceptance registry counts drift")
            if acceptance.get("structural_executable_eval_cases")!=expected_cases:fail(errors,"release acceptance structural eval set drift")
            if set(acceptance.get("forbidden_skills",[])).intersection(actual_skills):fail(errors,"release acceptance includes a forbidden legacy skill")
            if acceptance.get("archive_layout")!="repository-root" or acceptance.get("post_install_validation")!="required":fail(errors,"release acceptance portability contract drift")
            if acceptance.get("bounded_agentic_case_count")!=42:fail(errors,"bounded agentic case closure drift")
            if manifest_status=="implementation-candidate" and (acceptance.get("agentic_qualification")!="not-run" or acceptance.get("hld_e2e_fixture_status")!="declaration-only"):fail(errors,"implementation candidate overclaims agentic evidence")
            if manifest_status=="release-candidate" and (acceptance.get("agentic_qualification")!="qualified" or acceptance.get("hld_e2e_fixture_status")!="executed-agentic"):fail(errors,"release candidate lacks promoted agentic status")
            structural_anchors=[]
            for skill in sorted(actual_skills):
                path=root.parents[1]/"skills"/skill/"tests"/"acceptance-evidence.json"
                if not path.is_file():continue
                structural_anchors.append(path)
                anchor=json.loads(path.read_text(encoding="utf-8"))
                if anchor.get("evidence_class")!="structural-fixture-anchor" or anchor.get("agentic_qualification")!="not-run" or anchor.get("qualification_credit") is not False or anchor.get("reviewer_role")!="implementation-test-author":fail(errors,f"structural fixture anchor overclaims qualification: {skill}")
                if any(key in anchor for key in ("verdict","reviewer")):fail(errors,f"structural fixture anchor uses semantic-acceptance fields: {skill}")
            if require_test_anchors and len(structural_anchors)!=11:fail(errors,f"structural fixture anchor closure drift: {len(structural_anchors)}")
        except (UnicodeError,json.JSONDecodeError,KeyError,TypeError) as error:fail(errors,f"release acceptance evidence invalid: {error}")
    if checklist_path.is_file():
        checklist=checklist_path.read_text(encoding="utf-8")
        if manifest_status=="implementation-candidate" and checklist.count("- [ ]")!=4:fail(errors,"implementation candidate must expose the four unresolved semantic gates")
        if manifest_status=="release-candidate" and "- [ ]" in checklist:fail(errors,"release checklist contains an unresolved item while manifest is release-candidate")
    agentic_acceptance=root/"releases/agentic-acceptance.json"
    if manifest_status=="release-candidate":
        if not agentic_acceptance.is_file():fail(errors,"release-candidate lacks agentic acceptance evidence")
        else:
            completed=subprocess.run([sys.executable,str(root/"tools/validate_agentic_acceptance.py"),str(agentic_acceptance),"--json"],text=True,capture_output=True,encoding="utf-8")
            if completed.returncode:fail(errors,"agentic acceptance gate failed: "+(completed.stdout or completed.stderr).strip())
    try:
        catalog = SchemaCatalog(root / "schemas")
        required_schemas = {
            "hld-run-request.schema.json", "input-gate.schema.json", "work-order.schema.json",
            "run-state.schema.json", "stage-result.schema.json", "stage-completion.schema.json",
            "package-manifest.schema.json", "hdd.schema.json", "revision-plan.schema.json",
            "revision-plan-state.schema.json", "author-question.schema.json",
            "author-answer-event.schema.json", "author-resolution.schema.json",
            "composite-workspace-state.schema.json", "lld-handoff-acceptance.schema.json",
            "composite-publish-execution.schema.json", "composite-publish-validation.schema.json",
            "composite-internal-gate-data.schema.json", "composite-internal-blocked-report.schema.json",
            "composite-internal-revision-report.schema.json", "composite-internal-runtime-error.schema.json",
            "coordinator-ledger.schema.json", "coordinator-bootstrap.schema.json",
            "reality-dependency-request.schema.json", "public-runtime-registry.schema.json", "return-binding.schema.json",
            "hld-identity-contract.schema.json", "agentic-eval-result.schema.json", "agentic-acceptance.schema.json",
            "agent-task-receipt.schema.json", "qualification-attestation.schema.json", "qualification-trust-anchor.schema.json",
        }
        missing = sorted(required_schemas - set(catalog.schemas))
        if missing:
            fail(errors, f"missing schemas: {missing}")
        identity=json.loads((root/"references/hld-identity-contract.json").read_text(encoding="utf-8"));catalog.validate(identity,"hld-identity-contract.schema.json")
        trust_anchor=json.loads((root/"references/qualification-trust-anchor.json").read_text(encoding="utf-8"));catalog.validate(trust_anchor,"qualification-trust-anchor.schema.json")
        if manifest_status=="release-candidate" and trust_anchor.get("status")!="configured":fail(errors,"release candidate lacks a configured qualification trust anchor")
        from runtime.design_stage_runtime import EVIDENCE_ORDER
        if tuple(identity["design_evidence_files"])!=EVIDENCE_ORDER:fail(errors,"design evidence order differs from identity contract")
        from runtime.contracts import ID_OWNER_PREFIX
        work=identity["work_requirement"]
        if ID_OWNER_PREFIX.get(work["producer_prefix"].rstrip("-"))!=work["producer_stage"] or ID_OWNER_PREFIX.get(work["downstream_prefix"].rstrip("-"))!=work["projector_stage"]:fail(errors,"work requirement ownership differs from identity contract")
    except Exception as error:
        fail(errors, f"schema catalog invalid: {error}")
    for case_id in CASE_IDS:
        path = root / "evals" / "cases" / f"{case_id}.md"
        if not path.is_file():
            fail(errors, f"missing harness eval: {case_id}")
            continue
        text = path.read_text(encoding="utf-8")
        if f"case_id: {case_id}" not in text:
            fail(errors, f"eval case id mismatch: {case_id}")
        for heading in CASE_HEADINGS:
            if heading not in text:
                fail(errors, f"{case_id} missing {heading}")
        for dimension in ("scope_fidelity", "workflow_rigor", "skill_type_correctness", "adapter_faithfulness", "validation_hardness", "semantic_acceptance", "release_portability"):
            if case_id.startswith("HLD-E2E-") and dimension not in text:
                fail(errors, f"{case_id} missing scoring dimension {dimension}")
        if case_id.startswith("HLD-COMPOSITE-"):
            for dimension in ("scope_fidelity", "input_gate_obedience", "output_contract_correctness", "semantic_or_deterministic_correctness", "boundary_discipline", "parent_consumability"):
                if dimension not in text:
                    fail(errors, f"{case_id} missing scoring dimension {dimension}")
        if case_id.startswith("HLD-COORDINATOR-"):
            for dimension in ("scope_fidelity", "input_gate_obedience", "output_contract_correctness", "semantic_or_deterministic_correctness", "boundary_discipline", "parent_consumability"):
                if dimension not in text:
                    fail(errors, f"{case_id} missing scoring dimension {dimension}")
        fixture_path = root / "evals" / "fixtures" / f"{case_id}.json"
        if not fixture_path.is_file():
            fail(errors, f"missing sealed eval fixture: {case_id}")
        else:
            try:
                fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
                if fixture.get("case_id") != case_id:
                    fail(errors, f"eval fixture identity mismatch: {case_id}")
                if case_id.startswith("HLD-E2E-"):
                    if manifest_status=="implementation-candidate" and (fixture.get("fixture_status")!="declaration-only" or fixture.get("qualification_status")!="pending-agent-execution" or fixture.get("sealed_before_execution") is not False):fail(errors,f"declaration-only E2E fixture overclaims execution: {case_id}")
                    if manifest_status=="release-candidate" and (fixture.get("fixture_status")!="executed-agentic" or fixture.get("qualification_status")!="qualified" or fixture.get("sealed_before_execution") is not True):fail(errors,f"release-candidate E2E fixture lacks executed qualification: {case_id}")
                elif fixture.get("sealed_before_execution") is not True:
                    fail(errors, f"executable eval fixture is not sealed: {case_id}")
            except (UnicodeError, json.JSONDecodeError) as error:
                fail(errors, f"eval fixture invalid JSON: {case_id}: {error}")
    mapping = root / "adapters" / "codex" / "mapping.md"
    if mapping.is_file():
        text = mapping.read_text(encoding="utf-8")
        for status in ("native", "tool", "manual", "unsupported"):
            if status not in text:
                fail(errors, f"Codex mapping omits status {status}")
        if "operation.md" not in text or "same-context simulation" not in text:fail(errors,"Codex mapping lacks fail-closed operation/degradation rules")
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".py"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeError:
                fail(errors, f"not readable UTF-8: {path.relative_to(root)}")
                continue
            if "\ufffd" in content:
                fail(errors, f"replacement glyph found: {path.relative_to(root)}")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    result = {"harness": HARNESS, "status": "pass" if not errors else "fail", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("PASS" if not errors else "\n".join(errors)))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
