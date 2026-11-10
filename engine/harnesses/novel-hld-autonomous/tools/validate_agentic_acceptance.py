#!/usr/bin/env python3
"""Fail-closed validation for fresh-Agent HLD qualification evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

from runtime.contracts import BOUNDED_EVAL_DIMENSIONS, HARNESS, VERSION  # noqa: E402
from runtime.schema_catalog import SchemaCatalog  # noqa: E402

HARNESS_DIMENSIONS = {
    "scope_fidelity", "workflow_rigor", "skill_type_correctness",
    "adapter_faithfulness", "validation_hardness", "semantic_acceptance",
    "release_portability",
}
HARNESS_CASES = {f"HLD-E2E-{suffix}" for suffix in ("P01", "N01", "B01", "R01", "R02")}
REFERENCE_CASE_ID = "DUANXIAN-REFERENCE"
TRUST_ANCHOR = ROOT / "references/qualification-trust-anchor.json"
SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _bounded_case_owners() -> dict[str, tuple[str, str]]:
    registry = json.loads((ROOT / "references/public-runtime-registry.json").read_text(encoding="utf-8"))["entries"]
    skills = {entry["skill"] for entry in registry.values() if not entry["skill"].startswith("harness-core/")}
    cases: dict[str, tuple[str, str]] = {}
    for skill in skills:
        for path in (REPO / "skills" / skill / "evals" / "cases").glob("*.md"):
            cases[path.stem] = (path.stem.rsplit("-", 1)[0], skill)
    return cases


def _bounded_cases() -> set[str]:
    return set(_bounded_case_owners())


def _resolve(evidence_root: Path, ref: dict[str, Any], errors: list[str], label: str) -> Path | None:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not isinstance(ref.get("sha256"), str):
        errors.append(f"{label} is not a valid file reference")
        return None
    candidate = (evidence_root / ref["path"]).resolve()
    try:
        candidate.relative_to(evidence_root)
    except ValueError:
        errors.append(f"{label} escapes evidence root")
        return None
    if not candidate.is_file():
        errors.append(f"{label} is missing: {ref['path']}")
        return None
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != ref["sha256"]:
        errors.append(f"{label} digest mismatch: {ref['path']}")
        return None
    return candidate


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"{label} is not valid UTF-8 JSON: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return None
    return value


def _reference_catalog() -> SchemaCatalog:
    paths = list((ROOT / "schemas").glob("*.schema.json")) + [
        REPO / "skills/novel-hld-package-assembler/references/novel-hld-package.schema.json",
        REPO / "skills/novel-hld-review-report-assembler/references/hld-human-review-report.schema.json",
        REPO / "skills/novel-hld-html-renderer/references/render-target-registry.schema.json",
    ]
    documents = {str(path.resolve()): json.loads(path.read_text(encoding="utf-8")) for path in paths}
    return SchemaCatalog.from_documents(documents)


def _schema_check(catalog: SchemaCatalog, value: dict[str, Any], schema: str, errors: list[str], label: str) -> None:
    for issue in catalog.iter_errors(value, schema):
        pointer = "/" + "/".join(map(str, issue.absolute_path))
        errors.append(f"{label} schema {pointer}: {issue.message}")


def _hf1_schema_check(value: dict[str, Any], schema: str, errors: list[str], label: str) -> None:
    script = REPO / "skills/novel-hld-finalizer/scripts/validate_package.py"
    spec = importlib.util.spec_from_file_location("qualification_hf1_validator", script)
    if spec is None or spec.loader is None:
        errors.append("HF1 validator cannot be loaded")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors.extend(f"{label} {message}" for message in module.validate_schema(value, schema))


def _validate_receipt(
    evidence_root: Path,
    catalog: SchemaCatalog,
    receipt_ref: dict[str, Any],
    transcript_ref: dict[str, Any] | None,
    *,
    case_id: str,
    task_id: str,
    task_role: str,
    qualification_run_id: str,
    errors: list[str],
) -> dict[str, Any] | None:
    path = _resolve(evidence_root, receipt_ref, errors, f"{case_id} {task_role} task receipt")
    if path is None:
        return None
    receipt = _read_json(path, errors, f"{case_id} {task_role} task receipt")
    if receipt is None:
        return None
    _schema_check(catalog, receipt, "agent-task-receipt.schema.json", errors, f"{case_id} {task_role} task receipt")
    expected_transcript = receipt.get("transcript_ref") if transcript_ref is None else transcript_ref
    expected = (case_id, task_id, task_role, qualification_run_id, expected_transcript)
    actual = (receipt.get("case_id"), receipt.get("task_id"), receipt.get("task_role"), receipt.get("qualification_run_id"), receipt.get("transcript_ref"))
    if actual != expected:
        errors.append(f"{case_id} {task_role} task receipt identity/transcript mismatch")
    if isinstance(expected_transcript, dict):
        _resolve(evidence_root, expected_transcript, errors, f"{case_id} {task_role} transcript")
    else:
        errors.append(f"{case_id} {task_role} task receipt lacks a transcript reference")
    return receipt


def _validate_manifest_closure(path: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    package = path.parent.resolve()
    for index, ref in enumerate(manifest.get("files", [])):
        candidate = (package / str(ref.get("path", ""))).resolve()
        try:
            candidate.relative_to(package)
        except ValueError:
            errors.append(f"reference HH1 manifest member[{index}] escapes package")
            continue
        if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest() != ref.get("sha256"):
            errors.append(f"reference HH1 manifest member[{index}] missing or hash-mismatched")


def _validate_reference_run(evidence_root: Path, acceptance: dict[str, Any], catalog: SchemaCatalog, errors: list[str], seen_tasks: set[str], seen_contexts: set[str]) -> None:
    run = acceptance["reference_run"]
    if run["producer_task_id"] == run["reviewer_task_id"]:
        errors.append("reference run producer and reviewer must be independent")
    refs = {name: value for name, value in run.items() if name.endswith("_ref")}
    identities = [(ref["path"], ref["sha256"]) for name, ref in refs.items() if name not in {"producer_task_receipt_ref", "reviewer_task_receipt_ref"}]
    if len(identities) != len(set(identities)):
        errors.append("reference run artifact roles must resolve to distinct files")
    resolved: dict[str, Path] = {}
    documents: dict[str, dict[str, Any]] = {}
    for name, ref in refs.items():
        path = _resolve(evidence_root, ref, errors, f"reference_run.{name}")
        if path is not None:
            resolved[name] = path
            if name not in {"html_ref"}:
                document = _read_json(path, errors, f"reference_run.{name}")
                if document is not None:
                    documents[name] = document

    for role, schema in {
        "baseline_ref": "hld-control-baseline.schema.json",
        "hp1_package_ref": "novel-hld-package.schema.json",
        "hq2_acceptance_ref": "lld-handoff-acceptance.schema.json",
        "hh1_manifest_ref": "package-manifest.schema.json",
        "human_review_report_ref": "hld-human-review-report.schema.json",
        "render_registry_ref": "render-target-registry.schema.json",
    }.items():
        if role in documents:
            _schema_check(catalog, documents[role], schema, errors, f"reference_run.{role}")
    if "hld_completion_ref" in documents:
        _hf1_schema_check(documents["hld_completion_ref"], "hld-completion.schema.json", errors, "reference_run.hld_completion_ref")
    if "author_decision_ref" in documents:
        _hf1_schema_check(documents["author_decision_ref"], "author-decision.schema.json", errors, "reference_run.author_decision_ref")

    expected_run = run["hld_run_id"]
    expected_revision = run["revision"]
    for role, document in documents.items():
        if role in {"semantic_review_ref", "producer_task_receipt_ref", "reviewer_task_receipt_ref"}:
            continue
        if document.get("hld_run_id") != expected_run:
            errors.append(f"reference_run.{role} hld_run_id mismatch")
        if "revision" in document and document["revision"] != expected_revision:
            errors.append(f"reference_run.{role} revision mismatch")
    manifest = documents.get("hh1_manifest_ref")
    if manifest is not None and "hh1_manifest_ref" in resolved:
        if (manifest.get("stage"), manifest.get("status")) != ("HH1", "ready"):
            errors.append("reference HH1 manifest identity/status mismatch")
        _validate_manifest_closure(resolved["hh1_manifest_ref"], manifest, errors)
        roles = manifest.get("artifact_roles", {})
        expected_roles = {
            "human_review_report": run["human_review_report_ref"]["sha256"],
            "render_target_registry": run["render_registry_ref"]["sha256"],
            "human_review_html": run["html_ref"]["sha256"],
        }
        for role, digest in expected_roles.items():
            if not isinstance(roles.get(role), dict) or roles[role].get("sha256") != digest:
                errors.append(f"reference HH1 manifest does not bind {role}")
    completion = documents.get("hld_completion_ref")
    if completion is not None:
        expected = {
            "hp1_package_ref": run["hp1_package_ref"]["sha256"],
            "hq2_acceptance_ref": run["hq2_acceptance_ref"]["sha256"],
            "hh1_manifest_ref": run["hh1_manifest_ref"]["sha256"],
            "html_ref": run["html_ref"]["sha256"],
            "author_decision_ref": run["author_decision_ref"]["sha256"],
        }
        for role, digest in expected.items():
            if not isinstance(completion.get(role), dict) or completion[role].get("sha256") != digest:
                errors.append(f"reference HLD completion does not bind {role}")
    report = documents.get("human_review_report_ref")
    if report is not None:
        if report.get("hp1_content_binding", {}).get("package_sha256") != run["hp1_package_ref"]["sha256"]:
            errors.append("reference human review report does not bind HP1 package")
        if report.get("hq2_gate_binding", {}).get("acceptance_sha256") != run["hq2_acceptance_ref"]["sha256"]:
            errors.append("reference human review report does not bind HQ2 acceptance")
    registry = documents.get("render_registry_ref")
    if registry is not None and registry.get("report_ref", {}).get("sha256") != run["human_review_report_ref"]["sha256"]:
        errors.append("reference render registry does not bind human review report")
    decision = documents.get("author_decision_ref")
    if decision is not None:
        expected = {
            "hp1_package_sha256": run["hp1_package_ref"]["sha256"],
            "hq2_acceptance_sha256": run["hq2_acceptance_ref"]["sha256"],
            "hh1_manifest_sha256": run["hh1_manifest_ref"]["sha256"],
            "html_sha256": run["html_ref"]["sha256"],
        }
        if decision.get("decision") != "approved" or decision.get("bindings") != expected:
            errors.append("reference author decision is not an approved exact binding")
    html_path = resolved.get("html_ref")
    if html_path is not None:
        try:
            html = html_path.read_text(encoding="utf-8").lower()
            if "<html" not in html or "<title" not in html:
                errors.append("reference HTML is not a titled HTML document")
        except UnicodeError as error:
            errors.append(f"reference HTML is not UTF-8: {error}")
    semantic = documents.get("semantic_review_ref")
    if semantic and (semantic.get("project_id") != "duanxian" or semantic.get("hld_run_id") != expected_run or semantic.get("reviewer_task_id") != run["reviewer_task_id"] or semantic.get("verdict") != "pass"):
        errors.append("reference run semantic review identity/verdict mismatch")

    producer = _validate_receipt(evidence_root, catalog, run["producer_task_receipt_ref"], None, case_id=REFERENCE_CASE_ID, task_id=run["producer_task_id"], task_role="producer", qualification_run_id=acceptance["qualification_run_id"], errors=errors)
    reviewer = _validate_receipt(evidence_root, catalog, run["reviewer_task_receipt_ref"], None, case_id=REFERENCE_CASE_ID, task_id=run["reviewer_task_id"], task_role="reviewer", qualification_run_id=acceptance["qualification_run_id"], errors=errors)
    for receipt in (producer, reviewer):
        if receipt:
            if receipt["task_id"] in seen_tasks or receipt["context_id"] in seen_contexts:
                errors.append("reference run reuses a qualification task or context")
            seen_tasks.add(receipt["task_id"]); seen_contexts.add(receipt["context_id"])
    if producer and reviewer and producer["context_id"] == reviewer["context_id"]:
        errors.append("reference run producer and reviewer contexts must be independent")


def _trust_key_id(anchor: dict[str, Any]) -> str:
    material = {"algorithm": anchor["algorithm"], "exponent": anchor["exponent"], "modulus_hex": anchor["modulus_hex"]}
    return hashlib.sha256(_canonical(material)).hexdigest()


def _verify_rsa_signature(anchor: dict[str, Any], message: bytes, signature_hex: str) -> bool:
    modulus = int(anchor["modulus_hex"], 16)
    size = (modulus.bit_length() + 7) // 8
    try:
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False
    if len(signature) != size:
        return False
    decoded = pow(int.from_bytes(signature, "big"), anchor["exponent"], modulus).to_bytes(size, "big")
    digest_info = SHA256_DIGEST_INFO + hashlib.sha256(message).digest()
    padding = b"\xff" * (size - len(digest_info) - 3)
    return decoded == b"\x00\x01" + padding + b"\x00" + digest_info


def _validate_attestation(evidence_root: Path, acceptance: dict[str, Any], catalog: SchemaCatalog, trust_anchor_path: Path, errors: list[str]) -> None:
    try:
        anchor = json.loads(trust_anchor_path.resolve(strict=True).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"qualification trust anchor is unavailable or invalid: {error}")
        return
    _schema_check(catalog, anchor, "qualification-trust-anchor.schema.json", errors, "qualification trust anchor")
    if anchor.get("status") != "configured":
        errors.append("qualification trust anchor is not configured")
        return
    if anchor.get("key_id") != _trust_key_id(anchor):
        errors.append("qualification trust anchor key_id mismatch")
        return
    path = _resolve(evidence_root, acceptance["attestation_ref"], errors, "qualification attestation")
    if path is None:
        return
    attestation = _read_json(path, errors, "qualification attestation")
    if attestation is None:
        return
    _schema_check(catalog, attestation, "qualification-attestation.schema.json", errors, "qualification attestation")
    payload = dict(acceptance); payload.pop("attestation_ref", None)
    payload_sha = hashlib.sha256(_canonical(payload)).hexdigest()
    if attestation.get("acceptance_payload_sha256") != payload_sha or attestation.get("qualification_run_id") != acceptance["qualification_run_id"] or attestation.get("key_id") != anchor["key_id"]:
        errors.append("qualification attestation payload/run/key binding mismatch")
        return
    signed = dict(attestation); signature = signed.pop("signature_hex", "")
    if not _verify_rsa_signature(anchor, _canonical(signed), signature):
        errors.append("qualification attestation signature is invalid")


def validate(acceptance_path: Path, trust_anchor_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    acceptance_path = acceptance_path.resolve()
    if not acceptance_path.is_file():
        return [f"acceptance file is missing: {acceptance_path}"]
    evidence_root = acceptance_path.parent.resolve()
    acceptance = _read_json(acceptance_path, errors, "acceptance")
    if acceptance is None:
        return errors
    catalog = _reference_catalog()
    _schema_check(catalog, acceptance, "agentic-acceptance.schema.json", errors, "acceptance")
    if errors:
        return errors
    if acceptance["harness_version"] != VERSION:
        errors.append("acceptance version differs from runtime")

    expected_by_layer = {
        "bounded_skill": (set(BOUNDED_EVAL_DIMENSIONS), _bounded_cases()),
        "harness": (HARNESS_DIMENSIONS, HARNESS_CASES),
    }
    bounded_owners = _bounded_case_owners()
    seen: dict[str, set[str]] = {"bounded_skill": set(), "harness": set()}
    seen_tasks: set[str] = set(); seen_contexts: set[str] = set()
    seen_products: set[tuple[str, str]] = set(); seen_transcripts: set[tuple[str, str]] = set()
    result_groups = (("bounded_skill", acceptance["bounded_case_results"]), ("harness", acceptance["harness_case_results"]))
    for layer, references in result_groups:
        dimensions, _ = expected_by_layer[layer]
        for index, reference in enumerate(references):
            result_path = _resolve(evidence_root, reference, errors, f"{layer} result[{index}]")
            if result_path is None:
                continue
            result = _read_json(result_path, errors, f"{layer} result[{index}]")
            if result is None:
                continue
            _schema_check(catalog, result, "agentic-eval-result.schema.json", errors, result_path.name)
            case_id = result.get("case_id")
            if result.get("layer") != layer or not isinstance(case_id, str) or case_id in seen[layer]:
                errors.append(f"{result_path.name} has duplicate/invalid case or layer")
                continue
            seen[layer].add(case_id)
            if result.get("qualification_run_id") != acceptance["qualification_run_id"]:
                errors.append(f"{case_id} qualification run mismatch")
            if result.get("harness") != HARNESS or result.get("harness_version") != VERSION:
                errors.append(f"{case_id} harness identity mismatch")
            if layer == "bounded_skill" and (result.get("target_stage"), result.get("target_skill")) != bounded_owners.get(case_id):
                errors.append(f"{case_id} target stage/skill differs from the registered case owner")
            if layer == "harness" and (result.get("target_stage") != "HLD-E2E" or result.get("target_skill") is not None):
                errors.append(f"{case_id} harness target identity mismatch")
            if result.get("producer_task_id") == result.get("reviewer_task_id"):
                errors.append(f"{case_id} producer and reviewer must be independent")
            products = {(ref["path"], ref["sha256"]) for ref in result.get("produced_artifact_refs", [])}
            transcripts = {(ref["path"], ref["sha256"]) for ref in (result.get("producer_transcript_ref"), result.get("reviewer_transcript_ref")) if isinstance(ref, dict)}
            if seen_products.intersection(products):
                errors.append(f"{case_id} reuses another case's produced artifact")
            if seen_transcripts.intersection(transcripts) or len(transcripts) != 2:
                errors.append(f"{case_id} reuses or aliases a task transcript")
            seen_products.update(products); seen_transcripts.update(transcripts)
            allowed = {(ref["path"], ref["sha256"]) for ref in result.get("allowed_read_refs", [])}
            actual = {(ref["path"], ref["sha256"]) for ref in result.get("actual_read_refs", [])}
            if actual != allowed:
                errors.append(f"{case_id} actual reads must exactly match the sealed allowlist")
            actual_dimensions = {row.get("dimension") for row in result.get("dimensions", [])}
            if actual_dimensions != dimensions or len(result.get("dimensions", [])) != len(dimensions):
                errors.append(f"{case_id} scoring dimension closure mismatch")
            scores = [row.get("score", -1) for row in result.get("dimensions", [])]
            pass_bar = all(score == 2 for score in scores) if layer == "bounded_skill" else sum(scores) >= 12
            if result.get("verdict") != "pass" or result.get("blockers") or not pass_bar:
                errors.append(f"{case_id} does not meet the {layer} pass bar")
            refs = [result.get("fixture_ref"), result.get("fixture_manifest_ref"), result.get("prompt_ref"), result.get("producer_task_receipt_ref"), result.get("reviewer_task_receipt_ref"), result.get("producer_transcript_ref"), result.get("reviewer_transcript_ref"), result.get("semantic_review_ref")]
            refs += result.get("instruction_refs", []) + result.get("allowed_read_refs", []) + result.get("actual_read_refs", []) + result.get("produced_artifact_refs", []) + result.get("deterministic_validation_refs", [])
            refs += [ref for row in result.get("dimensions", []) for ref in row.get("evidence_refs", [])]
            for ref_index, ref in enumerate(refs):
                if isinstance(ref, dict):
                    _resolve(evidence_root, ref, errors, f"{case_id} evidence[{ref_index}]")
            review_path = _resolve(evidence_root, result["semantic_review_ref"], errors, f"{case_id} semantic review")
            if review_path:
                review = _read_json(review_path, errors, f"{case_id} semantic review")
                if review and (review.get("case_id") != case_id or review.get("reviewer_task_id") != result.get("reviewer_task_id") or review.get("verdict") != "pass"):
                    errors.append(f"{case_id} semantic review identity/verdict mismatch")
            for validation_ref in result.get("deterministic_validation_refs", []):
                validation_path = _resolve(evidence_root, validation_ref, errors, f"{case_id} deterministic validation")
                if validation_path:
                    validation = _read_json(validation_path, errors, f"{case_id} deterministic validation")
                    if validation and validation.get("status", validation.get("verdict")) != "pass":
                        errors.append(f"{case_id} deterministic validation did not pass")
            receipts = (
                _validate_receipt(evidence_root, catalog, result["producer_task_receipt_ref"], result["producer_transcript_ref"], case_id=case_id, task_id=result["producer_task_id"], task_role="producer", qualification_run_id=acceptance["qualification_run_id"], errors=errors),
                _validate_receipt(evidence_root, catalog, result["reviewer_task_receipt_ref"], result["reviewer_transcript_ref"], case_id=case_id, task_id=result["reviewer_task_id"], task_role="reviewer", qualification_run_id=acceptance["qualification_run_id"], errors=errors),
            )
            for receipt in receipts:
                if receipt:
                    if receipt["task_id"] in seen_tasks or receipt["context_id"] in seen_contexts:
                        errors.append(f"{case_id} reuses a qualification task or context")
                    seen_tasks.add(receipt["task_id"]); seen_contexts.add(receipt["context_id"])
            if all(receipts) and receipts[0]["context_id"] == receipts[1]["context_id"]:
                errors.append(f"{case_id} producer and reviewer contexts must be independent")

    for layer, (_, expected) in expected_by_layer.items():
        if seen[layer] != expected:
            errors.append(f"{layer} case closure mismatch: missing={sorted(expected-seen[layer])}, extra={sorted(seen[layer]-expected)}")
    _validate_reference_run(evidence_root, acceptance, catalog, errors, seen_tasks, seen_contexts)
    _validate_attestation(evidence_root, acceptance, catalog, (trust_anchor_path or TRUST_ANCHOR), errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acceptance", type=Path)
    parser.add_argument("--trust-anchor", type=Path, default=TRUST_ANCHOR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate(args.acceptance, args.trust_anchor)
    result = {"harness": HARNESS, "status": "pass" if not errors else "fail", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("PASS" if not errors else "\n".join(errors)))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
