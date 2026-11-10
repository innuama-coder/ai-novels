#!/usr/bin/env python3
"""Deterministic publisher for HQ2 and HH1 composite stages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import ContractError, canonical_bytes, read_json, resolve_inside, verify_file_ref
from .contracts import HARNESS, UPSTREAM
from .package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope
from .schema_catalog import SchemaCatalog

PUBLISHER = "harness-core/composite-stage-publisher"
VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
TASK_ORDER = {"HQ2": ("consumer_test", "fidelity_test"), "HH1": ("HH1-A", "HH1-B", "HH1-C")}
TASK_CONTRACT = {
    "consumer_test": ("HQ2", "novel-hld-lld-readiness-evaluator", "HQ2.consumer_test", (("handoff_consumption_test", "handoff-consumption-test.json"),)),
    "fidelity_test": ("HQ2", "novel-hld-lld-readiness-evaluator", "HQ2.fidelity_test", (("handoff_fidelity_test", "handoff-fidelity-test.json"),)),
    "HH1-A": ("HH1", "novel-hld-review-report-assembler", "HH1.A", (("human_review_report", "hld-human-review-report.json"),)),
    "HH1-B": ("HH1", "novel-hld-presentation-fidelity-reviewer", "HH1.B", (("presentation_fidelity_review", "presentation-fidelity-review.json"),)),
    "HH1-C": ("HH1", "novel-hld-html-renderer", "HH1.C", (("human_review_html", "hld-human-review-report.html"), ("render_target_registry", "render-target-registry.json"))),
}
UPSTREAM_PRIMARY = {"HB0": "hld-control-baseline.json", "HP1": "novel-hld-package.json", "HQ2": "lld-handoff-acceptance.json"}
UPSTREAM_PRIMARY_ROLE = {"HB0": "control_baseline", "HP1": "novel_hld_package", "HQ2": "lld_handoff_acceptance"}
READY_EXECUTION = {"HQ2": "q2-publish-execution.json", "HH1": "hh1-publish-execution.json"}
NONREADY_EXECUTION = {"HQ2": "q2-nonready-publish-execution.json", "HH1": "hh1-nonready-publish-execution.json"}
READY_CONTENT = {
    "HQ2": ("lld-handoff-acceptance.json",),
    "HH1": ("hld-human-review-report.json", "presentation-fidelity-review.json", "hld-human-review-report.html", "render-target-registry.json"),
}
SCHEMAS = (
    "composite-workspace-state.schema.json", "lld-handoff-acceptance.schema.json",
    "composite-publish-execution.schema.json", "composite-publish-validation.schema.json",
    "composite-internal-gate-data.schema.json", "composite-internal-blocked-report.schema.json",
    "composite-internal-revision-report.schema.json", "composite-internal-runtime-error.schema.json",
)
DOMAIN_SCHEMAS = (
    ROOT.parents[1] / "skills" / "novel-hld-review-report-assembler" / "references" / "hld-human-review-report.schema.json",
    ROOT.parents[1] / "skills" / "novel-hld-presentation-fidelity-reviewer" / "references" / "presentation-fidelity-review.schema.json",
    ROOT.parents[1] / "skills" / "novel-hld-html-renderer" / "references" / "render-target-registry.schema.json",
)


class PublishFailure(RuntimeError):
    pass


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_ref(path: Path, root: Path, role: str) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    return {"role": role, "path": resolved.relative_to(root.resolve(strict=True)).as_posix(), "sha256": sha256(resolved)}


def implementation_sha256() -> str:
    digest = hashlib.sha256()
    paths = [
        SCRIPT, ROOT / "runtime" / "canonical.py", ROOT / "runtime" / "contracts.py",
        ROOT / "runtime" / "package_envelope.py", ROOT / "runtime" / "schema_catalog.py",
    ] + [ROOT / "schemas" / name for name in SCHEMAS] + list(DOMAIN_SCHEMAS)
    for path in paths:
        identity = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.relative_to(ROOT.parents[1]).as_posix()
        digest.update(identity.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def output_ref(path: Path, package: Path, context: "Context", role: str) -> dict[str, str]:
    relative = path.resolve(strict=True).relative_to(package.resolve(strict=True))
    target = (context.output / relative).relative_to(context.workspace).as_posix()
    return {"role": role, "path": target, "sha256": sha256(path)}


def _catalog() -> SchemaCatalog:
    return SchemaCatalog(ROOT / "schemas")


@dataclass
class Context:
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    input_gate: dict[str, Any]
    composite_state: dict[str, Any]
    roles: dict[str, Path]
    output: Path
    catalog: SchemaCatalog


@dataclass
class InternalTask:
    kind: str
    work_order_path: Path
    work_order: dict[str, Any]
    result_path: Path
    result: dict[str, Any]
    manifest_path: Path
    manifest: dict[str, Any]
    package: Path
    main_paths: tuple[Path, ...]


def _reverse_manifest_roles(manifest: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for role, ref in manifest.get("artifact_roles", {}).items():
        if ref["path"] in result:
            raise PublishFailure(f"manifest path has multiple roles: {ref['path']}")
        result[ref["path"]] = role
    return result


def _authorized(roles: Mapping[str, Path], role: str, path: Path) -> Path:
    if role not in roles or roles[role] != path:
        raise PublishFailure(f"publisher bootstrap/derived role is not preauthorized: {role}")
    return path


def _expected_allowlist(context_stage: str, workspace: Path, work_order: Mapping[str, Any], state: Mapping[str, Any], roles: Mapping[str, Path]) -> dict[str, Path]:
    expected: dict[str, Path] = {"composite_workspace_state": roles["composite_workspace_state"]}
    for stage, artifact in zip(UPSTREAM[context_stage], work_order["upstream_completions"]):
        prefix=f"upstream::{stage}"
        completion=resolve_inside(workspace,artifact["completion_path"]);manifest_path=resolve_inside(workspace,artifact["manifest_path"]);main=resolve_inside(workspace,artifact["path"])
        _authorized(roles,f"{prefix}::completion",completion);_authorized(roles,f"{prefix}::manifest",manifest_path);_authorized(roles,f"{prefix}::canonical::{UPSTREAM_PRIMARY_ROLE[stage]}",main)
        expected[f"{prefix}::completion"]=completion;expected[f"{prefix}::manifest"]=manifest_path
        manifest=read_json(manifest_path);reverse=_reverse_manifest_roles(manifest);package=manifest_path.parent
        for item in manifest["files"]:
            member=resolve_inside(package,item["path"])
            if member==main: role=f"{prefix}::canonical::{UPSTREAM_PRIMARY_ROLE[stage]}"
            elif item["path"]=="validation.json":role=f"{prefix}::validation"
            else:role=f"{prefix}::member::{reverse[item['path']]}"
            _authorized(roles,role,member);expected[role]=member
    for record in state["issued_tasks"]:
        kind=record["task_kind"];prefix=f"internal::{kind}"
        work=resolve_inside(workspace,record["work_order_ref"]["path"]);result=resolve_inside(workspace,record["stage_result_ref"]["path"]);manifest_path=resolve_inside(workspace,record["package_manifest_ref"]["path"])
        _authorized(roles,f"{prefix}::work_order",work);_authorized(roles,f"{prefix}::stage_result",result);_authorized(roles,f"{prefix}::package_manifest",manifest_path)
        expected[f"{prefix}::work_order"]=work;expected[f"{prefix}::stage_result"]=result;expected[f"{prefix}::package_manifest"]=manifest_path
        work_value=read_json(work);input_gate=resolve_inside(workspace,work_value["input_gate_ref"]["path"]);_authorized(roles,f"{prefix}::input_gate",input_gate);expected[f"{prefix}::input_gate"]=input_gate
        for item in work_value["file_allowlist"]:
            role=f"{prefix}::task_input::{item['role']}";value=resolve_inside(workspace,item["path"]);_authorized(roles,role,value);expected[role]=value
        manifest=read_json(manifest_path);reverse=_reverse_manifest_roles(manifest);package=manifest_path.parent
        for item in manifest["files"]:
            role=f"{prefix}::member::{reverse[item['path']]}";value=resolve_inside(package,item["path"]);_authorized(roles,role,value);expected[role]=value
    return expected


def load_context(work_order_path: Path) -> Context:
    path = work_order_path.resolve(strict=True)
    workspace = path.parent.resolve(strict=True)
    catalog = _catalog()
    work_order = read_json(path)
    catalog.validate(work_order, "work-order.schema.json")
    if work_order["stage"] not in TASK_ORDER or work_order["exact_owner_skill"] != PUBLISHER:
        raise PublishFailure("publisher work-order owner/stage mismatch")
    if work_order["owner_version"] != VERSION or work_order["implementation_sha256"] != implementation_sha256():
        raise PublishFailure("publisher implementation binding mismatch")
    if work_order["unresolved_projection"]:
        raise PublishFailure("publisher requires empty unresolved projection")
    if work_order["mode"]=="return_resolution":
        if not all(work_order.get(key) for key in ("return_binding","revision_plan_ref","revision_plan_state_ref")):raise PublishFailure("return-resolution publisher requires exact revision bindings")
        for key in ("return_binding","revision_plan_ref","revision_plan_state_ref"):verify_file_ref(work_order[key],workspace)
    elif work_order["mode"]!="forward":raise PublishFailure("publisher mode is unsupported")
    roles: dict[str, Path] = {}
    for ref in work_order["file_allowlist"]:
        if ref["role"] in roles:
            raise PublishFailure(f"duplicate publisher allowlist role: {ref['role']}")
        roles[ref["role"]] = verify_file_ref(ref, workspace)
    if "composite_workspace_state" not in roles:
        raise PublishFailure("composite workspace state is required")
    state = read_json(roles["composite_workspace_state"])
    catalog.validate(state, "composite-workspace-state.schema.json")
    expected_allowlist=_expected_allowlist(work_order["stage"],workspace,work_order,state,roles)
    if set(roles)!=set(expected_allowlist) or any(roles[role]!=expected for role,expected in expected_allowlist.items()):raise PublishFailure("publisher actual-read allowlist closure mismatch")
    gate_path = verify_file_ref(work_order["input_gate_ref"], workspace)
    gate = read_json(gate_path)
    catalog.validate(gate, "input-gate.schema.json")
    for key in ("harness", "hld_run_id", "stage", "mode", "state_before_ref", "upstream_completions", "exact_owner_skill", "owner_version", "implementation_sha256", "return_binding", "unresolved_projection", "revision_plan_ref", "revision_plan_state_ref", "file_allowlist"):
        if gate[key] != work_order[key]:
            raise PublishFailure(f"publisher input-gate/work-order mismatch: {key}")
    if state["hld_run_id"] != work_order["hld_run_id"] or state["revision"] != work_order["revision"] or state["stage"] != work_order["stage"]:
        raise PublishFailure("composite workspace identity mismatch")
    if state["state_before_ref"] != work_order["state_before_ref"]:
        raise PublishFailure("composite tasks do not share publisher state-before")
    order = TASK_ORDER[work_order["stage"]]
    issued = [item["task_kind"] for item in state["issued_tasks"]]
    if state["ordered_task_kinds"] != list(order) or issued != list(order[:len(issued)]) or state["unissued_task_kinds"] != list(order[len(issued):]):
        raise PublishFailure("composite task issuance is not an exact ordered prefix")
    sequences = [item["sequence"] for item in state["issued_tasks"]]
    if sequences != sorted(set(sequences)) or state["last_issued_event_sequence"] != sequences[-1]:
        raise PublishFailure("composite task event sequence is invalid")
    output = resolve_inside(workspace, work_order["output_directory"], must_exist=False)
    if output.exists() or (workspace / "stage-result.json").exists():
        raise PublishFailure("publisher output or result already exists")
    return Context(workspace, path, work_order, gate, state, roles, output, catalog)


def _manifest_has(manifest: Mapping[str, Any], path: Path, digest: str) -> bool:
    return any(item["path"] == path.name and item["sha256"] == digest for item in manifest["files"])


def _admit_upstream(context: Context, stage: str, artifact: Mapping[str, Any]) -> dict[str, Any]:
    prefix=f"upstream::{stage}";completion_path=context.roles[f"{prefix}::completion"];manifest_path=context.roles[f"{prefix}::manifest"];validation_path=context.roles[f"{prefix}::validation"];main_path=context.roles[f"{prefix}::canonical::{UPSTREAM_PRIMARY_ROLE[stage]}"];package=manifest_path.parent
    expected = {
        "path": main_path.relative_to(context.workspace).as_posix(), "sha256": sha256(main_path),
        "manifest_path": manifest_path.relative_to(context.workspace).as_posix(), "manifest_sha256": sha256(manifest_path),
        "completion_path": completion_path.relative_to(context.workspace).as_posix(), "completion_sha256": sha256(completion_path),
    }
    if artifact != expected:
        raise PublishFailure(f"{stage} upstream artifact reference drift")
    manifest = read_json(manifest_path)
    completion = read_json(completion_path)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    context.catalog.validate(completion, "stage-completion.schema.json")
    validate_ready_profile(package, stage)
    validate_manifest(package, manifest)
    validate_completion_bindings(context.workspace, package, completion)
    # An accepted upstream is necessarily from an earlier run-state revision.
    # Freshness is carried by the exact artifact reference sealed into the
    # publisher work-order/input-gate, not by equating the producer revision
    # with the downstream composite revision.
    if completion["stage"] != stage or completion["hld_run_id"] != context.work_order["hld_run_id"]:
        raise PublishFailure(f"{stage} upstream identity is stale")
    if not _manifest_has(manifest, main_path, sha256(main_path)) or not _manifest_has(manifest, validation_path, sha256(validation_path)):
        raise PublishFailure(f"{stage} upstream main/validation is not manifest-bound")
    return {"completion_path": completion_path, "completion": completion, "main_path": main_path, "manifest_path": manifest_path, "package": package}


def admit_upstreams(context: Context) -> dict[str, dict[str, Any]]:
    stages = UPSTREAM[context.work_order["stage"]]
    if len(context.work_order["upstream_completions"]) != len(stages):
        raise PublishFailure("publisher upstream topology mismatch")
    values = {stage: _admit_upstream(context, stage, artifact) for stage, artifact in zip(stages, context.work_order["upstream_completions"])}
    hp1 = values["HP1"]
    if context.work_order["stage"] == "HH1":
        acceptance = read_json(values["HQ2"]["main_path"])
        if acceptance["hp1_completion_ref"]["sha256"] != sha256(hp1["completion_path"]) or acceptance["hb0_completion_ref"]["sha256"] != sha256(values["HB0"]["completion_path"]):
            raise PublishFailure("HQ2 acceptance does not bind current HP1/HB0")
    return values


def _same_ref(left: Mapping[str, Any], path: Path, workspace: Path) -> bool:
    return left["path"] == path.relative_to(workspace).as_posix() and left["sha256"] == sha256(path)


def _manifest_role_path(manifest: Mapping[str, Any], role: str, package: Path) -> Path:
    ref = manifest.get("artifact_roles", {}).get(role)
    if not isinstance(ref, dict):
        raise PublishFailure(f"internal manifest missing role: {role}")
    path = verify_file_ref(ref, package)
    return path


def admit_internal_tasks(context: Context) -> list[InternalTask]:
    tasks: list[InternalTask] = []
    package_roots: list[Path] = []
    for record in context.composite_state["issued_tasks"]:
        kind = record["task_kind"]
        prefix = f"internal::{kind}"
        work_path = context.roles[f"{prefix}::work_order"]
        result_path = context.roles[f"{prefix}::stage_result"]
        manifest_path = context.roles[f"{prefix}::package_manifest"]
        for field, actual in (("work_order_ref", work_path), ("stage_result_ref", result_path), ("package_manifest_ref", manifest_path)):
            if not _same_ref(record[field], actual, context.workspace):
                raise PublishFailure(f"composite state {kind} {field} drift")
        work = read_json(work_path); result = read_json(result_path); manifest = read_json(manifest_path)
        context.catalog.validate(work, "work-order.schema.json")
        context.catalog.validate(result, "stage-result.schema.json")
        context.catalog.validate(manifest, "package-manifest.schema.json")
        stage, skill, profile, main_contracts = TASK_CONTRACT[kind]
        if work["stage"] != stage or work["exact_owner_skill"] != skill or work["hld_run_id"] != context.work_order["hld_run_id"] or work["revision"] != context.work_order["revision"]:
            raise PublishFailure(f"internal task identity mismatch: {kind}")
        allow_roles: set[str] = set()
        for allowed in work["file_allowlist"]:
            if allowed["role"] in allow_roles:
                raise PublishFailure(f"internal task duplicate allowlist role: {kind}/{allowed['role']}")
            allow_roles.add(allowed["role"]); verify_file_ref(allowed, context.workspace)
        verify_file_ref(work["input_gate_ref"], context.workspace); verify_file_ref(work["state_before_ref"], context.workspace)
        if work["state_before_ref"] != context.work_order["state_before_ref"] or work["upstream_completions"] != context.work_order["upstream_completions"]:
            raise PublishFailure(f"internal task state/upstream isolation mismatch: {kind}")
        if work["event_sequence"] != record["sequence"]:
            raise PublishFailure(f"internal task sequence mismatch: {kind}")
        validate_result_envelope(result, work)
        if result["result_scope"] != "composite_internal" or result["stage"] != stage or result["skill"] != skill:
            raise PublishFailure(f"internal result identity/scope mismatch: {kind}")
        package = manifest_path.parent
        validate_manifest(package, manifest)
        if not _same_ref(result["result_manifest_ref"], manifest_path, context.workspace):
            raise PublishFailure(f"internal result manifest mismatch: {kind}")
        validation_path = verify_file_ref(result["validation_ref"], context.workspace)
        if validation_path.parent != package or not _manifest_has(manifest, validation_path, sha256(validation_path)):
            raise PublishFailure(f"internal validation is not manifest-bound: {kind}")
        if any(root == package or root in package.parents or package in root.parents for root in package_roots):
            raise PublishFailure("internal task packages are not isolated")
        package_roots.append(package)
        mains: tuple[Path, ...] = ()
        if result["result"] == "ready":
            mains = tuple(_manifest_role_path(manifest,role,package) for role,_ in main_contracts)
            validate_ready_profile(package, profile)
            if not _same_ref(result["internal_manifest_ref"], manifest_path, context.workspace):
                raise PublishFailure(f"internal ready manifest mismatch: {kind}")
            if read_json(validation_path).get("status") != "pass":
                raise PublishFailure(f"internal validation did not pass: {kind}")
            for main,(role,name) in zip(mains,main_contracts):
                if main.name!=name or not main.is_file() or not _manifest_has(manifest, main, sha256(main)):
                    raise PublishFailure(f"internal canonical missing/unbound: {kind}/{main.name}")
        else:
            if (package / "stage-completion.json").exists():
                raise PublishFailure(f"internal non-ready package contains completion: {kind}")
            _validate_nonready_refs(context, package, manifest, result)
        tasks.append(InternalTask(kind, work_path, work, result_path, result, manifest_path, manifest, package, mains))
    outcomes = [task.result["result"] for task in tasks]
    nonready = [index for index, outcome in enumerate(outcomes) if outcome != "ready"]
    if nonready:
        first = nonready[0]
        if first != len(tasks) - 1 or any(outcome != "ready" for outcome in outcomes[:first]) or context.composite_state["unissued_task_kinds"] != list(TASK_ORDER[context.work_order["stage"]][first + 1:]):
            raise PublishFailure("non-ready internal result is not the first stop with later tasks unissued")
    elif context.composite_state["unissued_task_kinds"]:
        raise PublishFailure("ready issued prefix cannot omit a later task")
    return tasks


def _condition_refs(result: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for key in ("revision_report_ref", "candidate_ref", "author_event_ref", "gate_data_ref", "blocked_report_ref", "runtime_error_ref"):
        if result.get(key) is not None:
            yield result[key]
    yield from result.get("local_defect_evidence", [])


def _validate_nonready_refs(context: Context, package: Path, manifest: Mapping[str, Any], result: Mapping[str, Any]) -> None:
    declared = {(item["path"], item["sha256"]) for item in manifest["files"]}
    for ref in _condition_refs(result):
        path = verify_file_ref(ref, context.workspace)
        try:
            relative = path.relative_to(package).as_posix()
        except ValueError as error:
            raise PublishFailure("internal non-ready condition ref escapes source package") from error
        if (relative, ref["sha256"]) not in declared:
            raise PublishFailure("internal non-ready condition ref is not manifest-bound")
    outcome = result["result"]
    validation = read_json(verify_file_ref(result["validation_ref"], context.workspace))
    if validation.get("status") != outcome:
        raise PublishFailure("internal non-ready validation status mismatch")
    identity = (result["skill"], result["stage"], result["hld_run_id"])
    affected = result["affected_ids"]
    if outcome == "blocked":
        gate = read_json(verify_file_ref(result["gate_data_ref"], context.workspace))
        report = read_json(verify_file_ref(result["blocked_report_ref"], context.workspace))
        context.catalog.validate(gate, "composite-internal-gate-data.schema.json")
        context.catalog.validate(report, "composite-internal-blocked-report.schema.json")
        if (gate["stage"], gate["hld_run_id"], gate["affected_ids"]) != (result["stage"], result["hld_run_id"], affected):
            raise PublishFailure("internal blocked gate identity/affected IDs drift")
        if (report["skill"], report["stage"], report["hld_run_id"]) != identity or report["blocker_class"] != result["blocker_class"] or report["affected_ids"] != affected:
            raise PublishFailure("internal blocked report identity/condition drift")
    elif outcome == "revise":
        report = read_json(verify_file_ref(result["revision_report_ref"], context.workspace))
        context.catalog.validate(report, "composite-internal-revision-report.schema.json")
        if result["revision_class"] != "local_candidate" or result["candidate_ref"] is None or not result["local_defect_evidence"]:
            raise PublishFailure("composite internal revise must carry a local candidate and evidence")
        if (report["skill"], report["stage"], report["hld_run_id"]) != identity or report["revision_class"] != result["revision_class"] or report["affected_ids"] != affected:
            raise PublishFailure("internal revision report identity/condition drift")
    elif outcome == "runtime_error":
        error = read_json(verify_file_ref(result["runtime_error_ref"], context.workspace))
        context.catalog.validate(error, "composite-internal-runtime-error.schema.json")
        if (error["skill"], error["stage"], error["hld_run_id"]) != identity:
            raise PublishFailure("internal runtime error identity drift")
    else:
        raise PublishFailure(f"unsupported internal non-ready outcome: {outcome}")


def _validate_task_semantics(context: Context, tasks: list[InternalTask], upstream: Mapping[str, Any]) -> None:
    if any(task.result["result"] != "ready" for task in tasks):
        return
    by_kind = {task.kind: task for task in tasks}
    hp1_completion = upstream["HP1"]["completion"]
    hp1_canonicals = {item["role"]: item for item in hp1_completion["canonical_artifacts"]}
    if context.work_order["stage"] == "HQ2":
        consumer = read_json(by_kind["consumer_test"].main_paths[0])
        fidelity = read_json(by_kind["fidelity_test"].main_paths[0])
        if (consumer.get("stage"), consumer.get("mode"), consumer.get("hld_run_id"), consumer.get("task_id"), consumer.get("verdict"), consumer.get("defect_origin")) != ("HQ2", "consumer_test", context.work_order["hld_run_id"], by_kind["consumer_test"].work_order["task_id"], "pass", "none"):
            raise PublishFailure("consumer test canonical is not a passing current identity")
        if (fidelity.get("stage"), fidelity.get("mode"), fidelity.get("hld_run_id"), fidelity.get("task_id"), fidelity.get("verdict"), fidelity.get("defect_origin")) != ("HQ2", "fidelity_test", context.work_order["hld_run_id"], by_kind["fidelity_test"].work_order["task_id"], "pass", "none"):
            raise PublishFailure("fidelity test canonical is not a passing current identity")
        sealed = fidelity.get("sealed_consumption_test_ref")
        if not isinstance(sealed, dict) or sealed.get("sha256") != sha256(by_kind["consumer_test"].main_paths[0]):
            raise PublishFailure("fidelity test does not bind sealed consumer bytes")
        consumer_roles = {item["role"]: item for item in by_kind["consumer_test"].work_order["file_allowlist"]}
        fidelity_roles = {item["role"]: item for item in by_kind["fidelity_test"].work_order["file_allowlist"]}
        if consumer_roles.get("lld_handoff", {}).get("sha256") != hp1_canonicals.get("lld_handoff", {}).get("sha256"):
            raise PublishFailure("consumer task does not bind current HP1 LLD handoff")
        if fidelity_roles.get("hp1_completion", {}).get("sha256") != sha256(upstream["HP1"]["completion_path"]):
            raise PublishFailure("fidelity task does not bind current HP1 completion")
        if fidelity_roles.get("sealed_consumption_test", {}).get("sha256") != sha256(by_kind["consumer_test"].main_paths[0]) or fidelity_roles.get("sealed_consumption_manifest", {}).get("sha256") != sha256(by_kind["consumer_test"].manifest_path):
            raise PublishFailure("fidelity task sealed-consumer binding drift")
    else:
        a, b, c = by_kind["HH1-A"], by_kind["HH1-B"], by_kind["HH1-C"]
        report = read_json(a.main_paths[0]); review = read_json(b.main_paths[0]); registry = read_json(c.main_paths[1])
        domain_schemas = zip((report, review, registry), DOMAIN_SCHEMAS)
        for value, schema_path in domain_schemas:
            schema = json.loads(schema_path.read_text(encoding="utf-8")); SchemaCatalog.from_documents({schema["$id"]:schema}).validate(value,schema["$id"])
        hp1_package_hash = hp1_canonicals["novel_hld_package"]["sha256"]
        q2_hash = sha256(upstream["HQ2"]["main_path"])
        if report.get("hld_run_id") != context.work_order["hld_run_id"] or report.get("revision") != context.work_order["revision"] or report.get("status") != "ready":
            raise PublishFailure("HH1-A report identity drift")
        if report["hp1_content_binding"] != {"package_sha256": hp1_package_hash, "completion_sha256": sha256(upstream["HP1"]["completion_path"])}:
            raise PublishFailure("HH1-A report HP1 binding drift")
        if report["hq2_gate_binding"] != {"acceptance_sha256": q2_hash, "bound_hp1_package_sha256": hp1_package_hash}:
            raise PublishFailure("HH1-A report HQ2 binding drift")
        if review.get("hld_run_id") != context.work_order["hld_run_id"] or review.get("revision") != context.work_order["revision"] or review.get("verdict") != "pass" or review.get("defect_origin") != "none":
            raise PublishFailure("HH1-B review is not a passing current identity")
        bindings = review["review_bindings"]
        if bindings["hp1_package_sha256"] != hp1_package_hash or bindings["report_sha256"] != sha256(a.main_paths[0]) or bindings["report_manifest_sha256"] != sha256(a.manifest_path) or bindings["assembler_task_id"] != a.work_order["task_id"] or bindings["reviewer_task_id"] != b.work_order["task_id"]:
            raise PublishFailure("HH1-B review binding drift")
        if registry.get("hld_run_id") != context.work_order["hld_run_id"] or registry.get("report_ref", {}).get("sha256") != sha256(a.main_paths[0]) or registry.get("fidelity_review_ref", {}).get("sha256") != sha256(b.main_paths[0]):
            raise PublishFailure("HH1-C registry binding drift")


def _manifest(package: Path, context: Context, *, ready: bool) -> dict[str, Any]:
    name = "package-manifest.json" if ready else "result-manifest.json"
    excluded = {name, "stage-completion.json"}
    paths = sorted((path for path in package.rglob("*") if path.is_file() and path.relative_to(package).as_posix() not in excluded), key=lambda item: item.relative_to(package).as_posix())
    files = []
    roles: dict[str, dict[str, str]] = {}
    fixed = {
        "lld-handoff-acceptance.json": "lld_handoff_acceptance", "hld-human-review-report.json": "human_review_report",
        "presentation-fidelity-review.json": "presentation_fidelity_review", "hld-human-review-report.html": "human_review_html",
        "render-target-registry.json": "render_target_registry", "validation.json": "validation",
        READY_EXECUTION.get(context.work_order["stage"]): "execution_record", NONREADY_EXECUTION.get(context.work_order["stage"]): "execution_record",
        "source-internal-stage-result.json": "source_internal_stage_result",
    }
    for path in paths:
        relative = path.relative_to(package).as_posix()
        role = fixed.get(relative, f"source_internal::{relative}" if relative.startswith("source-internal-package/") else f"content::{relative}")
        value = file_ref(path, package, role)
        files.append(value); roles[role] = value
    return {"schema_version":"1.0","harness":HARNESS,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"stage":context.work_order["stage"],"skill":PUBLISHER,"status":"ready" if ready else context._outcome,"files":files,"artifact_roles":roles}


def _execution(context: Context, tasks: list[InternalTask], outcome: str, output_hashes: Mapping[str, str]) -> dict[str, Any]:
    value = {
        "schema_version":"1.0","harness":HARNESS,"stage":context.work_order["stage"],"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],
        "work_order_id":context.work_order["work_order_id"],"implementation_sha256":implementation_sha256(),"publish_outcome":outcome,
        "source_result_refs":[file_ref(task.result_path, context.workspace, f"internal_{task.kind}_result") for task in tasks],
        "input_hashes":{role:sha256(path) for role,path in sorted(context.roles.items())},"output_hashes":dict(sorted(output_hashes.items())),"deterministic":True,
    }
    context.catalog.validate(value, "composite-publish-execution.schema.json")
    return value


def _validation(context: Context, outcome: str, checks: list[str]) -> dict[str, Any]:
    value = {"schema_version":"1.0","harness":HARNESS,"stage":context.work_order["stage"],"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"status":"pass" if outcome == "ready" else outcome,"checks":checks,"errors":[]}
    context.catalog.validate(value, "composite-publish-validation.schema.json")
    return value


def _empty_result() -> dict[str, Any]:
    return {"completion_ref":None,"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None}


def _base_result(context: Context, outcome: str, package: Path, manifest: Path, validation: Path) -> dict[str, Any]:
    return {"schema_version":"1.0","harness":HARNESS,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"stage":context.work_order["stage"],"skill":PUBLISHER,"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"event_sequence":context.work_order["event_sequence"],"result_scope":"top_level","result":outcome,"state_before_ref":context.work_order["state_before_ref"],"input_gate_ref":context.work_order["input_gate_ref"],"result_manifest_ref":output_ref(manifest,package,context,"package_manifest" if outcome=="ready" else "result_manifest"),"validation_ref":output_ref(validation,package,context,"validation"),"produced_at":context.work_order["result_timestamp"],**_empty_result()}


def write_ready(context: Context, tasks: list[InternalTask], upstream: Mapping[str, Any], destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    stage = context.work_order["stage"]
    if stage == "HQ2":
        by_kind = {task.kind: task for task in tasks}
        acceptance = {"schema_version":"1.0","harness":HARNESS,"stage":"HQ2","hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"status":"ready",
            "consumer_test_ref":file_ref(by_kind["consumer_test"].main_paths[0],context.workspace,"handoff_consumption_test"),"consumer_manifest_ref":file_ref(by_kind["consumer_test"].manifest_path,context.workspace,"consumer_manifest"),"consumer_result_ref":file_ref(by_kind["consumer_test"].result_path,context.workspace,"consumer_result"),
            "fidelity_test_ref":file_ref(by_kind["fidelity_test"].main_paths[0],context.workspace,"handoff_fidelity_test"),"fidelity_manifest_ref":file_ref(by_kind["fidelity_test"].manifest_path,context.workspace,"fidelity_manifest"),"fidelity_result_ref":file_ref(by_kind["fidelity_test"].result_path,context.workspace,"fidelity_result"),
            "hp1_completion_ref":file_ref(upstream["HP1"]["completion_path"],context.workspace,"hp1_completion"),"hb0_completion_ref":file_ref(upstream["HB0"]["completion_path"],context.workspace,"hb0_completion")}
        context.catalog.validate(acceptance,"lld-handoff-acceptance.schema.json")
        write_json(destination/"lld-handoff-acceptance.json",acceptance)
    else:
        by_kind={task.kind:task for task in tasks}
        sources=((by_kind["HH1-A"].main_paths[0],"hld-human-review-report.json"),(by_kind["HH1-B"].main_paths[0],"presentation-fidelity-review.json"),(by_kind["HH1-C"].main_paths[0],"hld-human-review-report.html"),(by_kind["HH1-C"].main_paths[1],"render-target-registry.json"))
        for source,name in sources:
            shutil.copyfile(source,destination/name)
            if (destination/name).read_bytes()!=source.read_bytes(): raise PublishFailure(f"HH1 byte copy drift: {name}")
    content_hashes={name:sha256(destination/name) for name in READY_CONTENT[stage]}
    execution_name=READY_EXECUTION[stage]
    write_json(destination/execution_name,_execution(context,tasks,"ready",content_hashes))
    write_json(destination/"validation.json",_validation(context,"ready",["internal-identity","ordered-prefix-complete","public-manifest-and-result","upstream-binding","cross-package-binding","byte-copy-or-reference-only","canonical-final-refs"]))
    manifest=_manifest(destination,context,ready=True); context.catalog.validate(manifest,"package-manifest.schema.json"); write_json(destination/"package-manifest.json",manifest)
    completion={"schema_version":"1.0","harness":HARNESS,"stage":stage,"skill":PUBLISHER,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"status":"ready","input_gate_ref":context.work_order["input_gate_ref"],"state_before_ref":context.work_order["state_before_ref"],"work_order_ref":file_ref(context.work_order_path,context.workspace,"work_order"),"manifest_ref":output_ref(destination/"package-manifest.json",destination,context,"package_manifest"),"validation_ref":output_ref(destination/"validation.json",destination,context,"validation"),"upstream_completions":context.work_order["upstream_completions"],"canonical_artifacts":[output_ref(destination/name,destination,context,{"lld-handoff-acceptance.json":"lld_handoff_acceptance","hld-human-review-report.json":"human_review_report","presentation-fidelity-review.json":"presentation_fidelity_review","hld-human-review-report.html":"human_review_html","render-target-registry.json":"render_target_registry"}[name]) for name in READY_CONTENT[stage]],"owner_implementation":{"skill":PUBLISHER,"version":VERSION,"sha256":implementation_sha256()},"return_binding":context.work_order["return_binding"],"ready_capabilities":["composite_internal_results_sealed","composite_publish_verified"],"next_allowed_stage":"HH1" if stage=="HQ2" else "HF1"}
    context.catalog.validate(completion,"stage-completion.schema.json"); write_json(destination/"stage-completion.json",completion)
    result=_base_result(context,"ready",destination,destination/"package-manifest.json",destination/"validation.json"); result["completion_ref"]=output_ref(destination/"stage-completion.json",destination,context,"stage_completion"); context.catalog.validate(result,"stage-result.schema.json"); return result


def _remap_condition_ref(ref: Mapping[str, Any] | None, task: InternalTask, destination: Path, context: Context) -> dict[str,str] | None:
    if ref is None:return None
    source=verify_file_ref(ref,context.workspace); relative=source.relative_to(task.package); copied=destination/"source-internal-package"/relative
    return output_ref(copied,destination,context,ref["role"])


def write_nonready(context: Context, tasks: list[InternalTask], destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True,exist_ok=False); source=tasks[-1]; outcome=source.result["result"]; context._outcome=outcome
    copy_root=destination/"source-internal-package"
    for item in source.manifest["files"]:
        path=verify_file_ref(item,source.package); target=copy_root/item["path"]; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
        if target.read_bytes()!=path.read_bytes():raise PublishFailure("source internal package byte-copy drift")
    shutil.copyfile(source.result_path,destination/"source-internal-stage-result.json")
    if (destination/"source-internal-stage-result.json").read_bytes()!=source.result_path.read_bytes():raise PublishFailure("source internal result byte-copy drift")
    execution_name=NONREADY_EXECUTION[context.work_order["stage"]]
    copied_hashes={p.relative_to(destination).as_posix():sha256(p) for p in destination.rglob("*") if p.is_file()}
    write_json(destination/execution_name,_execution(context,tasks,outcome,copied_hashes))
    write_json(destination/"validation.json",_validation(context,outcome,["first-nonready-only","prior-ready-prefix","later-task-unissued","source-package-byte-copy","source-result-byte-copy","condition-ref-remap","no-completion"]))
    manifest=_manifest(destination,context,ready=False); context.catalog.validate(manifest,"package-manifest.schema.json"); write_json(destination/"result-manifest.json",manifest)
    result=_base_result(context,outcome,destination,destination/"result-manifest.json",destination/"validation.json")
    for key in ("revision_class","blocker_class","affected_ids"):
        result[key]=source.result[key]
    for key in ("revision_report_ref","candidate_ref","author_event_ref","gate_data_ref","blocked_report_ref","runtime_error_ref"):
        result[key]=_remap_condition_ref(source.result.get(key),source,destination,context)
    result["local_defect_evidence"]=[_remap_condition_ref(item,source,destination,context) for item in source.result.get("local_defect_evidence",[])]
    context.catalog.validate(result,"stage-result.schema.json"); return result


def execute(work_order_path: Path) -> tuple[int,dict[str,Any]]:
    context=load_context(work_order_path); upstream=admit_upstreams(context); tasks=admit_internal_tasks(context); _validate_task_semantics(context,tasks,upstream)
    nonready=any(task.result["result"]!="ready" for task in tasks); temp=Path(tempfile.mkdtemp(prefix=".composite-publish-",dir=context.workspace)); staging=temp/"package"
    try:
        result=write_nonready(context,tasks,staging) if nonready else write_ready(context,tasks,upstream,staging)
        os.replace(staging,context.output)
        try:
            write_json(context.workspace/"stage-result.json",result)
            validate_existing(work_order_path)
        except Exception:
            result_path=context.workspace/"stage-result.json"
            if result_path.exists():os.replace(result_path,temp/"failed-stage-result.json")
            if context.output.exists():os.replace(context.output,temp/"failed-package")
            raise
        return (0 if result["result"]=="ready" else 2),result
    finally:shutil.rmtree(temp,ignore_errors=True)


def validate_existing(work_order_path: Path) -> dict[str,Any]:
    path=work_order_path.resolve(strict=True); workspace=path.parent; work=read_json(path); output=resolve_inside(workspace,work["output_directory"],file_only=False); result_path=workspace/"stage-result.json"; result=read_json(result_path)
    shadow_output=workspace/".composite-output-validation"; shadow_result=workspace/".composite-result-validation"; os.replace(output,shadow_output); os.replace(result_path,shadow_result)
    try:context=load_context(path)
    finally:os.replace(shadow_output,output);os.replace(shadow_result,result_path)
    context.catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,context.work_order)
    for key in ("result_manifest_ref","validation_ref","completion_ref","revision_report_ref","candidate_ref","author_event_ref","gate_data_ref","blocked_report_ref","runtime_error_ref"):
        if result.get(key) is not None:verify_file_ref(result[key],workspace)
    for item in result.get("local_defect_evidence",[]):verify_file_ref(item,workspace)
    upstream=admit_upstreams(context);tasks=admit_internal_tasks(context);_validate_task_semantics(context,tasks,upstream);ready=all(task.result["result"]=="ready" for task in tasks)
    temp=Path(tempfile.mkdtemp(prefix=".composite-reproduce-",dir=workspace));expected=temp/"package"
    try:
        expected_result=write_ready(context,tasks,upstream,expected) if ready else write_nonready(context,tasks,expected)
        actual_files=sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file());expected_files=sorted(p.relative_to(expected).as_posix() for p in expected.rglob("*") if p.is_file())
        if actual_files!=expected_files:raise PublishFailure("published package profile drift")
        for relative in actual_files:
            if (output/relative).read_bytes()!=(expected/relative).read_bytes():raise PublishFailure(f"published package byte drift: {relative}")
        if canonical_bytes(result)!=canonical_bytes(expected_result):raise PublishFailure("top-level stage result is not reproducible")
        manifest_name="package-manifest.json" if ready else "result-manifest.json";manifest=read_json(output/manifest_name);validate_manifest(output,manifest)
        if ready:
            validate_ready_profile(output,context.work_order["stage"]);validate_completion_bindings(workspace,output,read_json(output/"stage-completion.json"))
        elif (output/"stage-completion.json").exists():raise PublishFailure("non-ready publisher emitted completion")
    finally:shutil.rmtree(temp,ignore_errors=True)
    return {"status":"pass","result":result["result"],"result_sha256":sha256(result_path)}


def _main(argv: list[str] | None=None) -> int:
    import argparse
    parser=argparse.ArgumentParser(description="Publish HQ2/HH1 composite stage");parser.add_argument("work_order",type=Path);parser.add_argument("--validate-only",action="store_true");args=parser.parse_args(argv)
    try:
        if args.validate_only:print(json.dumps(validate_existing(args.work_order),sort_keys=True));return 0
        code,result=execute(args.work_order);print(json.dumps({"status":result["result"],"stage":result["stage"]},sort_keys=True));return code
    except Exception as error:
        print(json.dumps({"status":"runtime_error","error":str(error)},ensure_ascii=False,sort_keys=True),file=sys.stderr);return 1


if __name__=="__main__":raise SystemExit(_main())
