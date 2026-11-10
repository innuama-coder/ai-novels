"""Public Harness runtime shared by bounded HLD design-thinking stages.

The Agent produces the semantic draft and evidence.  This module owns only
public-contract admission, deterministic boundary/structure checks and the
acyclic package/result envelope.  Stage-specific semantic checks are supplied
as a callback so later design stages can reuse the same protocol implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical import (
    ContractError,
    canonical_sha256,
    file_ref,
    json_pointer,
    read_json,
    resolve_inside,
    sha256_file,
    verify_file_ref,
    write_json,
)
from .contracts import HARNESS, SKILLS, UPSTREAM
from .hdd import expected_hdd_id, project_unresolved
from .package_envelope import (
    validate_completion_bindings,
    validate_manifest,
    validate_ready_profile,
    validate_result_envelope,
)
from .schema_catalog import SchemaCatalog


EVIDENCE_ORDER = (
    "00-dependency-assessment.json",
    "01-obligation-analysis.json",
    "02-option-analysis.json",
    "03-projection-analysis.json",
    "04-adversarial-self-review.json",
)
EVIDENCE_SCHEMAS = {
    "00-dependency-assessment.json": "design-dependency-evidence.schema.json",
    "01-obligation-analysis.json": "design-obligation-evidence.schema.json",
    "02-option-analysis.json": "design-option-evidence.schema.json",
    "03-projection-analysis.json": "design-projection-evidence.schema.json",
    "04-adversarial-self-review.json": "design-adversarial-evidence.schema.json",
}
OWNERSHIP = {"source_projection", "hld_owned", "preserved_open", "lld_freedom"}
DISPOSITIONS = {
    "not_needed_for_current_stage",
    "conditional_structure_preserves_open",
    "required_now",
    "resolved_by_external_author_event",
}
SHARED_GATE_FIELDS = (
    "harness", "hld_run_id", "stage", "mode", "state_before_ref",
    "upstream_completions", "exact_owner_skill", "owner_version",
    "implementation_sha256", "return_binding", "unresolved_projection",
    "revision_plan_ref", "revision_plan_state_ref", "file_allowlist",
)
REQUIRED_CONTRACT_FIELDS = {
    "artifact_role", "canonical_file", "canonical_schema", "decision_prefix", "deterministic_checks",
    "display_name", "forbidden_keys", "model_required", "next_stage",
    "object_arrays", "preview_file", "ready_capabilities", "runtime_version",
    "skill", "stage", "upstream_stages",
}


class GateError(ContractError):
    """The public work order or its sealed inputs are invalid."""


class CandidateError(ContractError):
    """The Agent-owned draft violates its semantic or stage boundary contract."""


class UpstreamDefect(CandidateError):
    """A sealed upstream HLD model must change before this stage can be truthful."""

    def __init__(self, evidence: str, affected_ids: list[str], required_action: str) -> None:
        super().__init__(evidence)
        self.affected_ids = list(dict.fromkeys(affected_ids))
        if not self.affected_ids:
            raise ValueError("upstream defect requires affected stable IDs")
        self.required_action = required_action


class AuthorRequired(CandidateError):
    def __init__(self, assessments: list[dict[str, Any]]) -> None:
        ordered = sorted(
            assessments,
            key=lambda item: (item.get("source_id", ""), item.get("id", "")),
        )
        details = []
        affected_obligations: set[str] = set()
        for item in ordered:
            source_id = item["source_id"]
            rationale = item.get("rationale_anchor") or "no rationale supplied"
            downstream = item.get("downstream_effect") or "downstream effect unspecified"
            obligations = sorted(set(item.get("affected_obligation_ids", [])))
            details.append(
                f"{source_id}: {rationale}; downstream: {downstream}; "
                f"affected obligations: {', '.join(obligations) or 'none'}"
            )
            affected_obligations.update(obligations)
        evidence = " | ".join(details)
        super().__init__(evidence or "one or more projected unresolved controls are required now")
        self.assessments = ordered
        source_ids = sorted({item["source_id"] for item in ordered})
        # The public design gate schema intentionally accepts source IDs only.
        # HLD obligation IDs stay in the human-actionable evidence instead of
        # leaking into the source-resolution routing field.
        self.affected_ids = source_ids
        self.affected_obligation_ids = sorted(affected_obligations)
        self.required_action = (
            "请明确处理以下构思资料中的冲突："
            + ", ".join(source_ids)
            + "。受影响的设计内容："
            + (", ".join(self.affected_obligation_ids) or "无（仅需澄清构思来源）")
            + "。请根据证据决定保留哪项事实、修订哪项事实；后续设计不能替你猜测。"
        )


class AuthorityConflictRequired(CandidateError):
    """A sealed source-authority contradiction that HLD is forbidden to guess through."""

    def __init__(self, claims: list[dict[str, Any]]) -> None:
        ordered = sorted(claims, key=lambda item: item["id"])
        self.claims = ordered
        self.affected_ids = sorted({source_id for item in ordered for source_id in item["source_ids"]})
        self.affected_obligation_ids = sorted(
            {obligation_id for item in ordered for obligation_id in item["affected_obligation_ids"]}
        )
        evidence = " | ".join(
            f"{item['id']} sources[{', '.join(item['source_ids'])}]: {item['conflict_statement']}; "
            f"affected obligations: {', '.join(item['affected_obligation_ids'])}; "
            f"downstream: {item['downstream_effect']}"
            for item in ordered
        )
        super().__init__(evidence)
        choices = " | ".join(f"{item['id']}: {item['author_choice_required']}" for item in ordered)
        self.required_action = (
            "已确认的构思资料彼此矛盾，需要你决定如何修正。"
            + "涉及的构思来源："
            + ", ".join(self.affected_ids)
            + "。受影响的设计内容："
            + (", ".join(self.affected_obligation_ids) or "无（仅需澄清构思来源）")
            + "。需要确认的事项："
            + choices
            + "。在你确认前，后续设计不能自行改写、重排或解释这些事实。"
        )


StageValidator = Callable[[dict[str, Any], Mapping[str, Any]], None]


@dataclass(frozen=True)
class Context:
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    gate: dict[str, Any]
    output: Path
    contract: dict[str, Any]
    catalog: SchemaCatalog
    allowlist: dict[str, dict[str, str]]
    source_index: dict[str, Any]
    control_baseline: dict[str, Any]


def load_contract(skill_root: Path) -> dict[str, Any]:
    contract = json.loads((skill_root / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
    missing = REQUIRED_CONTRACT_FIELDS - set(contract)
    if missing:
        raise GateError(f"runtime contract missing fields: {sorted(missing)}")
    stage = contract["stage"]
    if stage not in UPSTREAM or contract["skill"] != SKILLS[stage]:
        raise GateError("runtime contract does not match public stage ownership")
    if tuple(contract["upstream_stages"]) != UPSTREAM[stage]:
        raise GateError("runtime contract upstream topology differs from public UPSTREAM")
    if contract["runtime_version"] != "1.0.0":
        raise GateError("unsupported design-stage runtime version")
    return contract


def implementation_files(skill_root: Path) -> tuple[Path, ...]:
    """Return the complete, deterministic implementation hash domain."""
    contract = json.loads((skill_root / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
    declared = contract.get("implementation_closure")
    if declared is not None:
        if declared.get("algorithm") != "sha256-basename-nul-content-nul-v1":
            raise GateError("unsupported implementation closure algorithm")
        repository = skill_root.parents[1]
        return tuple(resolve_inside(repository, relative) for relative in declared["ordered_files"])
    paths = [
        Path(__file__).resolve(),
        (skill_root / "scripts" / "run_skill.py").resolve(),
        (skill_root / "references" / "runtime-contract.json").resolve(),
        (skill_root / "schemas" / contract["canonical_schema"]).resolve(),
    ]
    repository = skill_root.parents[1]
    for relative in contract.get("additional_schema_paths", []):
        paths.append(resolve_inside(repository, relative))
    for relative in contract.get("additional_implementation_paths", []):
        paths.append(resolve_inside(repository, relative))
    return tuple(paths)


def implementation_sha256(skill_root: Path) -> str:
    """Bind shared/runtime code plus every declared local semantic schema."""
    digest = hashlib.sha256()
    paths = implementation_files(skill_root)
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _schema_catalog(skill_root: Path, contract: Mapping[str, Any]) -> SchemaCatalog:
    public_root = Path(__file__).resolve().parents[1] / "schemas"
    documents = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(public_root.glob("*.schema.json"))
    }
    canonical_path = skill_root / "schemas" / contract["canonical_schema"]
    if not canonical_path.is_file():
        raise GateError(f"missing canonical schema: {canonical_path}")
    documents[canonical_path.name] = json.loads(canonical_path.read_text(encoding="utf-8"))
    repository = skill_root.parents[1]
    for relative in contract.get("additional_schema_paths", []):
        schema_path = resolve_inside(repository, relative)
        documents[schema_path.name] = json.loads(schema_path.read_text(encoding="utf-8"))
    return SchemaCatalog.from_documents(documents)


def _same_artifact_ref(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return dict(left) == dict(right)


def _verify_path_hash(workspace: Path, path_value: Any, digest_value: Any) -> Path:
    path = resolve_inside(workspace, path_value)
    if sha256_file(path) != digest_value:
        raise GateError(f"hash mismatch: {path_value}")
    return path


def _read_and_check_upstream(
    workspace: Path,
    ref: Mapping[str, Any],
    expected_stage: str,
    expected_prefix: list[Mapping[str, Any]],
    hld_run_id: str,
    catalog: SchemaCatalog,
) -> dict[str, Any]:
    main_path = _verify_path_hash(workspace, ref["path"], ref["sha256"])
    manifest_path = _verify_path_hash(workspace, ref["manifest_path"], ref["manifest_sha256"])
    completion_path = _verify_path_hash(workspace, ref["completion_path"], ref["completion_sha256"])
    package = manifest_path.parent
    if completion_path != package / "stage-completion.json" or main_path.parent != package:
        raise GateError(f"{expected_stage}: artifactReference package paths are not closed")
    manifest = read_json(manifest_path)
    completion = read_json(completion_path)
    catalog.validate(manifest, "package-manifest.schema.json")
    catalog.validate(completion, "stage-completion.schema.json")
    if manifest["stage"] != expected_stage or completion["stage"] != expected_stage:
        raise GateError(f"{expected_stage}: upstream stage identity mismatch")
    if manifest["skill"] != SKILLS[expected_stage] or completion["skill"] != SKILLS[expected_stage]:
        raise GateError(f"{expected_stage}: upstream skill identity mismatch")
    if manifest["hld_run_id"] != hld_run_id or completion["hld_run_id"] != hld_run_id:
        raise GateError(f"{expected_stage}: upstream run identity mismatch")
    if manifest["status"] != "ready" or completion["status"] != "ready":
        raise GateError(f"{expected_stage}: upstream is not ready")
    if completion["upstream_completions"] != expected_prefix:
        raise GateError(f"{expected_stage}: upstream completion chain is not the public prefix")
    if completion["manifest_ref"]["path"] != ref["manifest_path"] or completion["manifest_ref"]["sha256"] != ref["manifest_sha256"]:
        raise GateError(f"{expected_stage}: completion/manifest binding differs from artifactReference")
    canonical_pairs = {(item["path"], item["sha256"]) for item in completion["canonical_artifacts"]}
    if (ref["path"], ref["sha256"]) not in canonical_pairs:
        raise GateError(f"{expected_stage}: main artifact is not completion-bound")
    for field in ("input_gate_ref", "state_before_ref", "work_order_ref", "validation_ref"):
        verify_file_ref(completion[field], workspace)
    validation_path = verify_file_ref(completion["validation_ref"], workspace)
    validation = read_json(validation_path)
    if validation.get("status") not in {"pass", "ready"}:
        raise GateError(f"{expected_stage}: validation is not passing")
    validate_ready_profile(package, expected_stage)
    validate_manifest(package, manifest)
    validate_completion_bindings(workspace, package, completion)
    main = read_json(main_path)
    if main.get("stage") != expected_stage or main.get("hld_run_id") != hld_run_id or main.get("status") != "ready":
        raise GateError(f"{expected_stage}: main artifact identity/status mismatch")
    return {
        "stage": expected_stage,
        "main_path": main_path,
        "manifest_path": manifest_path,
        "completion_path": completion_path,
        "validation_path": validation_path,
        "completion": completion,
        "manifest": manifest,
        "main": main,
    }


def derive_file_allowlist(
    workspace: Path,
    state_before_ref: Mapping[str, Any],
    baseline_manifest_ref: Mapping[str, Any],
    baseline_validation_ref: Mapping[str, Any],
    source_lineage_refs: list[Mapping[str, Any]],
    upstream: list[Mapping[str, Any]],
    stages: tuple[str, ...],
    protocol_refs: tuple[Mapping[str, Any], ...] = (),
) -> list[dict[str, str]]:
    """Derive the exact file-read closure, including upstream control/package files.

    The work-order itself is the invocation payload and the input gate cannot
    hash-reference itself.  Those two bootstrap documents are the only reads
    outside this closure; every referenced state/upstream/source file is listed.
    """
    root = workspace.resolve(strict=True)
    expected: list[dict[str, str]] = []
    by_path: dict[str, dict[str, str]] = {}
    roles: set[str] = set()

    def add(role: str, path: str, sha256: str) -> None:
        candidate = {"role": role, "path": path, "sha256": sha256}
        prior = by_path.get(path)
        if prior is not None:
            if prior["sha256"] != sha256:
                raise GateError(f"same allowlist path has conflicting hashes: {path}")
            return
        if role in roles:
            raise GateError(f"duplicate derived allowlist role: {role}")
        expected.append(candidate)
        by_path[path] = candidate
        roles.add(role)

    add(baseline_manifest_ref["role"], baseline_manifest_ref["path"], baseline_manifest_ref["sha256"])
    add(baseline_validation_ref["role"], baseline_validation_ref["path"], baseline_validation_ref["sha256"])
    add(state_before_ref["role"], state_before_ref["path"], state_before_ref["sha256"])
    for item in source_lineage_refs:
        add(item["role"], item["path"], item["sha256"])
    for stage, artifact in zip(stages, upstream):
        add(f"upstream::{stage}::main", artifact["path"], artifact["sha256"])
        add(f"upstream::{stage}::manifest", artifact["manifest_path"], artifact["manifest_sha256"])
        add(f"upstream::{stage}::completion", artifact["completion_path"], artifact["completion_sha256"])
        manifest_path = _verify_path_hash(root, artifact["manifest_path"], artifact["manifest_sha256"])
        completion_path = _verify_path_hash(root, artifact["completion_path"], artifact["completion_sha256"])
        manifest = read_json(manifest_path)
        completion = read_json(completion_path)
        for field in ("input_gate_ref", "state_before_ref", "work_order_ref", "validation_ref"):
            item = completion[field]
            add(f"upstream::{stage}::{field.removesuffix('_ref')}", item["path"], item["sha256"])
        for item in sorted(manifest["files"], key=lambda value: value["path"]):
            absolute = resolve_inside(manifest_path.parent, item["path"])
            relative = absolute.relative_to(root).as_posix()
            add(f"upstream::{stage}::content::{item['role']}", relative, item["sha256"])
    for item in protocol_refs:
        add(item["role"], item["path"], item["sha256"])
    return expected


def load_context(skill_root: Path, work_order_path: Path, *, require_new_output: bool = True) -> Context:
    contract = load_contract(skill_root)
    workspace = work_order_path.resolve(strict=True).parent
    catalog = _schema_catalog(skill_root, contract)
    work_order = read_json(work_order_path)
    catalog.validate(work_order, "work-order.schema.json")
    if work_order["stage"] != contract["stage"] or work_order["exact_owner_skill"] != contract["skill"]:
        raise GateError("work-order owner identity mismatch")
    if work_order["owner_version"] != contract["runtime_version"]:
        raise GateError("work-order owner version mismatch")
    if work_order["implementation_sha256"] != implementation_sha256(skill_root):
        raise GateError("work-order implementation hash is stale")
    if work_order["action"] != "execute":
        raise GateError("design stage accepts only execute")
    gate_path = verify_file_ref(work_order["input_gate_ref"], workspace, expected_role="input_gate")
    gate = read_json(gate_path)
    catalog.validate(gate, "input-gate.schema.json")
    for field in SHARED_GATE_FIELDS:
        if gate[field] != work_order[field]:
            raise GateError(f"input-gate/work-order drift: {field}")
    if gate["hb0_completion_ref"] != work_order["upstream_completions"][0]:
        raise GateError("input-gate hb0_completion_ref is not the first public upstream")
    if work_order["mode"] == "forward" and any(
        work_order[field] is not None
        for field in ("return_binding", "revision_plan_ref", "revision_plan_state_ref")
    ):
        raise GateError("forward work-order contains return/revision bindings")
    for field, expected_role in (
        ("return_binding", "return_binding"),
        ("revision_plan_ref", "revision_plan"),
        ("revision_plan_state_ref", "revision_plan_state"),
    ):
        ref = work_order[field]
        if ref is not None and ref.get("role") != expected_role:
            raise GateError(f"{field} uses a non-canonical protocol role")
    upstream_refs = work_order["upstream_completions"]
    stages = tuple(contract["upstream_stages"])
    if len(upstream_refs) != len(stages):
        raise GateError("upstream artifactReference count differs from public UPSTREAM")
    if gate["baseline_manifest_ref"]["role"] != "baseline_manifest" or gate["baseline_validation_ref"]["role"] != "baseline_validation":
        raise GateError("baseline references use non-public roles")
    if gate["baseline_manifest_ref"]["path"] != upstream_refs[0]["manifest_path"] or gate["baseline_manifest_ref"]["sha256"] != upstream_refs[0]["manifest_sha256"]:
        raise GateError("baseline manifest does not bind HB0 artifactReference")
    source_refs = gate["source_lineage_refs"]
    source_index_refs = [item for item in source_refs if item["role"] == "source_index"]
    if len(source_index_refs) != 1:
        raise GateError("source_lineage_refs must contain exactly one source_index")

    # Before reading any referenced state/package/source file, prove that the
    # work-order allowlist explicitly authorizes the bootstrap reference.
    raw_allowlist = work_order["file_allowlist"]
    allow_by_path: dict[str, Mapping[str, Any]] = {}
    allow_roles: set[str] = set()
    for item in raw_allowlist:
        if item["role"] in allow_roles or item["path"] in allow_by_path:
            raise GateError("allowlist roles and paths must be unique")
        allow_roles.add(item["role"])
        allow_by_path[item["path"]] = item

    def require_pre_authorized(path: str, sha256: str, label: str) -> None:
        item = allow_by_path.get(path)
        if item is None or item["sha256"] != sha256:
            raise GateError(f"referenced file is not pre-authorized by allowlist: {label}")

    for item, label in (
        (work_order["state_before_ref"], "state_before"),
        (gate["baseline_manifest_ref"], "baseline_manifest"),
        (gate["baseline_validation_ref"], "baseline_validation"),
        *((item, f"source_lineage:{item['role']}") for item in source_refs),
        *((work_order[field], field) for field in ("return_binding", "revision_plan_ref", "revision_plan_state_ref") if work_order[field] is not None),
    ):
        require_pre_authorized(item["path"], item["sha256"], label)
    for stage, artifact in zip(stages, upstream_refs):
        require_pre_authorized(artifact["path"], artifact["sha256"], f"{stage}:main")
        require_pre_authorized(artifact["manifest_path"], artifact["manifest_sha256"], f"{stage}:manifest")
        require_pre_authorized(artifact["completion_path"], artifact["completion_sha256"], f"{stage}:completion")

    expected_allowlist = derive_file_allowlist(
        workspace, gate["state_before_ref"], gate["baseline_manifest_ref"], gate["baseline_validation_ref"],
        gate["source_lineage_refs"], upstream_refs, stages,
        tuple(work_order[field] for field in ("return_binding", "revision_plan_ref", "revision_plan_state_ref") if work_order[field] is not None),
    )
    if work_order["file_allowlist"] != expected_allowlist:
        raise GateError("allowlist is not the exact public role/path/hash closure")
    roles: dict[str, dict[str, str]] = {}
    for item in expected_allowlist:
        verify_file_ref(item, workspace)
        roles[item["role"]] = dict(item)

    state_path = verify_file_ref(work_order["state_before_ref"], workspace, expected_role="state_before")
    state = read_json(state_path)
    catalog.validate(state, "run-state.schema.json")
    if state["hld_run_id"] != work_order["hld_run_id"] or state["revision"] != work_order["revision"] or state["current_stage"] != contract["stage"]:
        raise GateError("state-before identity does not admit this work-order")
    checked: list[dict[str, Any]] = []
    for index, (stage, artifact) in enumerate(zip(stages, upstream_refs)):
        checked.append(_read_and_check_upstream(
            workspace, artifact, stage, upstream_refs[:index], work_order["hld_run_id"], catalog
        ))
    hb0 = checked[0]
    if gate["baseline_validation_ref"]["path"] != hb0["completion"]["validation_ref"]["path"] or gate["baseline_validation_ref"]["sha256"] != hb0["completion"]["validation_ref"]["sha256"]:
        raise GateError("baseline validation does not bind HB0 completion")
    source_index_path = verify_file_ref(source_index_refs[0], workspace, expected_role="source_index")
    source_index = read_json(source_index_path)
    catalog.validate(source_index, "hld-source-index.schema.json")
    control_baseline = hb0["main"]
    catalog.validate(control_baseline, "hld-control-baseline.schema.json")
    projected = project_unresolved(control_baseline["unresolved_register"])[contract["stage"]]
    if work_order["unresolved_projection"] != projected:
        raise GateError("unresolved_projection is not the ordered source-index projection")
    indexed = {entry["source_id"]: entry for entry in source_index["entries"]}
    for source_id in projected:
        if source_id not in indexed or contract["stage"] not in indexed[source_id]["allowed_stages"]:
            raise GateError(f"unresolved source is absent or unauthorized in source index: {source_id}")

    output = resolve_inside(workspace, work_order["output_directory"], must_exist=False, file_only=False)
    if (require_new_output and output.exists()) or output == workspace or workspace not in output.parents:
        raise GateError("output directory must be new and contained")
    return Context(
        workspace, work_order_path.resolve(), work_order, gate, output, contract,
        catalog, roles, source_index, control_baseline,
    )


def _validate_dependency_evidence(context: Context, evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    projected_ids = context.work_order["unresolved_projection"]
    assessments = evidence.get("assessments")
    if not isinstance(assessments, list) or [item.get("source_id") for item in assessments] != projected_ids:
        raise CandidateError("dependency assessment must cover string projection exactly and in order")
    required_now: list[dict[str, Any]] = []
    for item in assessments:
        expected = expected_hdd_id(context.contract["stage"], item["source_id"])
        required = {
            "id", "source_id", "owner_stage", "affected_obligation_ids", "disposition",
            "object_evidence_refs", "rationale_anchor", "downstream_effect", "resolution_ref",
        }
        if set(item) != required or item["id"] != expected or item["owner_stage"] != context.contract["stage"]:
            raise CandidateError(f"{expected}: HDD identity/fields are not exact")
        if item["disposition"] not in DISPOSITIONS:
            raise CandidateError(f"{expected}: invalid disposition")
        resolved = item["disposition"] == "resolved_by_external_author_event"
        if resolved != (item["resolution_ref"] is not None):
            raise CandidateError(f"{expected}: resolution_ref/disposition mismatch")
        if item["disposition"] == "required_now":
            required_now.append(item)
    return required_now


def _validate_author_required_claims(context: Context, session: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims = session.get("author_required_claims", [])
    if not claims:
        return []
    controls = _control_registry(context)
    seen: set[str] = set()
    for claim in claims:
        if claim["id"] in seen:
            raise CandidateError(f"duplicate authority-conflict claim {claim['id']}")
        seen.add(claim["id"])
        missing = [source_id for source_id in claim["source_ids"] if source_id not in controls]
        if missing:
            raise CandidateError(f"{claim['id']}: authority-conflict source IDs are not sealed controls: {missing}")
        if not any(controls[source_id]["authority_class"] == "author_locked" for source_id in claim["source_ids"]):
            raise CandidateError(f"{claim['id']}: authority conflict must include an author-locked control")
    return claims


def _walk_forbidden(value: Any, forbidden: set[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                raise CandidateError(f"{path}.{key}: forbidden boundary field")
            _walk_forbidden(child, forbidden, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, forbidden, f"{path}[{index}]")


def _control_registry(context: Context) -> dict[str, Mapping[str, Any]]:
    return {item["source_id"]: item for item in context.control_baseline["control_registry"]}


def _validate_element(
    context: Context,
    value: Any,
    prefix: str,
    where: str,
    controls: Mapping[str, Mapping[str, Any]],
    dependencies: Mapping[str, Mapping[str, Any]],
) -> None:
    if not isinstance(value, dict):
        raise CandidateError(f"{where}: element must be an object")
    required = ("id", "source_refs", "source_authority_refs", "ownership_class", "resolution_ref")
    if any(field not in value for field in required) or not str(value["id"]).startswith(prefix):
        raise CandidateError(f"{where}: owner ID or trace fields are invalid")
    if value["ownership_class"] not in OWNERSHIP or len(value["source_refs"]) != len(set(value["source_refs"])):
        raise CandidateError(f"{where}: ownership/source refs are invalid")
    authority_ids: list[str] = []
    for index, authority in enumerate(value["source_authority_refs"]):
        fields = {"source_id", "classification", "open_item", "authority_class", "value_sha256"}
        if not isinstance(authority, dict) or set(authority) != fields:
            raise CandidateError(f"{where}.source_authority_refs[{index}]: fields are not exact")
        source_id = authority["source_id"]
        control = controls.get(source_id)
        expected = None if control is None else {
            "source_id": source_id,
            "classification": control["classification"],
            "open_item": control["open_item"],
            "authority_class": control["authority_class"],
            "value_sha256": control["source_value_sha256"],
        }
        if authority != expected:
            raise CandidateError(f"{where}: source authority differs from HB0 control {source_id}")
        authority_ids.append(source_id)
    if value["source_refs"] != authority_ids or len(authority_ids) != len(set(authority_ids)):
        raise CandidateError(f"{where}: source_refs and authority refs must be ordered one-to-one")
    classes = {item["classification"] for item in value["source_authority_refs"]}
    resolution_ref = value["resolution_ref"]
    if classes == {"must_ask"}:
        if value["ownership_class"] == "preserved_open":
            if resolution_ref is not None:
                raise CandidateError(f"{where}: unresolved must_ask may not carry resolution_ref")
            if any(dependencies[source_id]["disposition"] == "resolved_by_external_author_event" for source_id in value["source_refs"]):
                raise CandidateError(f"{where}: resolved must_ask may not remain preserved_open")
        elif value["ownership_class"] == "source_projection":
            if resolution_ref is None:
                raise CandidateError(f"{where}: resolved must_ask requires resolution_ref")
            matching_allowlist = any(reference == resolution_ref for reference in context.allowlist.values())
            if not matching_allowlist:
                raise CandidateError(f"{where}: resolution_ref is not an exact allowed input")
            verify_file_ref(resolution_ref, context.workspace)
            for source_id in value["source_refs"]:
                dependency = dependencies[source_id]
                if dependency["disposition"] != "resolved_by_external_author_event" or dependency["resolution_ref"] != resolution_ref:
                    raise CandidateError(f"{where}: resolved must_ask is not bound to its HDD resolution")
        else:
            raise CandidateError(f"{where}: must_ask ownership is invalid")
        return
    if resolution_ref is not None:
        raise CandidateError(f"{where}: only externally resolved must_ask may carry resolution_ref")
    expected_classes = {
        "source_projection": {"mandatory"},
        "hld_owned": {"freedom"},
        "preserved_open": {"open"},
        "lld_freedom": {"freedom"},
    }[value["ownership_class"]]
    if classes != expected_classes:
        raise CandidateError(f"{where}: ownership_class/source classification mapping is invalid")


def _validate_common_model(context: Context, model: dict[str, Any], session: dict[str, Any]) -> None:
    contract = context.contract
    required = [
        "schema_version", "skill", "stage", "hld_run_id", "status", "input_gate_ref",
        "source_artifacts", "authority_partition", "design_decisions", "derivation_claims",
        "decision_dependencies", "open_items", "downstream_contract",
    ] + contract["model_required"]
    missing = [field for field in required if field not in model]
    if missing:
        raise CandidateError(f"canonical model missing fields: {missing}")
    if model["skill"] != contract["skill"] or model["stage"] != contract["stage"]:
        raise CandidateError("canonical model owner mismatch")
    if model["hld_run_id"] != context.work_order["hld_run_id"] or model["status"] != "ready":
        raise CandidateError("canonical model run/status mismatch")
    if model["input_gate_ref"] != context.work_order["input_gate_ref"]:
        raise CandidateError("canonical input_gate_ref differs from work-order")
    actual_reads = session.get("actual_read_refs")
    if not isinstance(actual_reads, list) or len({item.get("role") for item in actual_reads if isinstance(item, dict)}) != len(actual_reads):
        raise CandidateError("generation session actual_read_refs must have unique roles")
    for item in actual_reads:
        if not isinstance(item, dict) or context.allowlist.get(item.get("role")) != item:
            raise CandidateError("generation session read is not an exact allowlist reference")
        verify_file_ref(item, context.workspace)
    required_read_roles = {
        *(item["role"] for item in context.gate["source_lineage_refs"]),
        *(f"upstream::{stage}::main" for stage in context.contract["upstream_stages"]),
    }
    if not required_read_roles.issubset({item["role"] for item in actual_reads}):
        raise CandidateError("generation session omitted a required semantic upstream/source-index read")
    if model["source_artifacts"] != actual_reads:
        raise CandidateError("source_artifacts must equal actual_read_refs in order")
    if not model["design_decisions"]:
        raise CandidateError("at least one projected design decision is required")
    decision_ids = [item["id"] for item in model["design_decisions"]]
    if len(decision_ids) != len(set(decision_ids)) or any(not item.startswith(contract["decision_prefix"]) for item in decision_ids):
        raise CandidateError("design decision has wrong owner prefix")
    expected_hdds = [expected_hdd_id(contract["stage"], source_id) for source_id in context.work_order["unresolved_projection"]]
    if [item.get("id") for item in model["decision_dependencies"]] != expected_hdds:
        raise CandidateError("canonical decision_dependencies do not exactly project HDD evidence")
    if model["open_items"] != context.work_order["unresolved_projection"]:
        raise CandidateError("open_items must equal the ordered unresolved projection")
    if model["downstream_contract"] != {
        "consumer": contract["next_stage"], "required_roles": contract["ready_capabilities"]
    }:
        raise CandidateError("downstream_contract differs from the frozen stage contract")
    derivation_ids = [item["id"] for item in model["derivation_claims"]]
    if len(derivation_ids) != len(set(derivation_ids)):
        raise CandidateError("derivation claim IDs must be unique")
    known_sources = set(_control_registry(context))
    for claim in model["derivation_claims"]:
        if not set(claim["source_refs"]).issubset(known_sources):
            raise CandidateError(f"{claim['id']}: derivation cites unknown source")
        try:
            target = json_pointer(model, claim["target_locator"])
        except ContractError as error:
            raise CandidateError(f"{claim['id']}: derivation target does not resolve") from error
        if canonical_sha256(target) != claim["value_sha256"]:
            raise CandidateError(f"{claim['id']}: derivation target hash mismatch")
    _walk_forbidden(model, set(contract["forbidden_keys"]))
    controls = _control_registry(context)
    partition = model["authority_partition"]
    expected_classifications = {name: [] for name in ("mandatory", "freedom", "open", "must_ask")}
    expected_open_items: list[str] = []
    expected_authority = {name: [] for name in ("author_locked", "autonomous_owned", "downstream_freedom", "author_open")}
    for control in context.control_baseline["control_registry"]:
        source_id = control["source_id"]
        expected_classifications[control["classification"]].append(source_id)
        expected_authority[control["authority_class"]].append(source_id)
        if control["open_item"]:
            expected_open_items.append(source_id)
    if partition["source_classifications"] != expected_classifications:
        raise CandidateError("authority_partition.source_classifications differs from HB0 registry")
    if partition["source_open_items"] != expected_open_items:
        raise CandidateError("authority_partition.source_open_items differs from HB0 registry")
    if partition["source_authority_classes"] != expected_authority:
        raise CandidateError("authority_partition.source_authority_classes differs from HB0 registry")
    dependencies = {item["source_id"]: item for item in model["decision_dependencies"]}
    seen: set[str] = set()
    ownership_ids: dict[str, list[str]] = {name: [] for name in OWNERSHIP}
    for array_name, prefix in contract["object_arrays"].items():
        values = model[array_name]
        if not isinstance(values, list):
            raise CandidateError(f"{array_name} must be an array")
        for index, element in enumerate(values):
            _validate_element(context, element, prefix, f"{array_name}[{index}]", controls, dependencies)
            if element["id"] in seen:
                raise CandidateError(f"duplicate canonical ID {element['id']}")
            seen.add(element["id"])
            ownership_ids[element["ownership_class"]].append(element["id"])
    for object_name, prefix in contract.get("object_fields", {}).items():
        _validate_element(context, model[object_name], prefix, object_name, controls, dependencies)
        if model[object_name]["id"] in seen:
            raise CandidateError(f"duplicate canonical ID {model[object_name]['id']}")
        seen.add(model[object_name]["id"])
        ownership_ids[model[object_name]["ownership_class"]].append(model[object_name]["id"])
    declared_ownership = model["authority_partition"]["hld_ownership"]
    if any(declared_ownership[name] != ownership_ids[name] for name in OWNERSHIP):
        raise CandidateError("authority_partition.hld_ownership does not exactly map canonical object ownership")


def validate_draft(context: Context, draft_dir: Path, stage_validator: StageValidator) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected = {"canonical.json", "generation-session.json", "generation-evidence"}
    if {path.name for path in draft_dir.iterdir()} != expected:
        raise CandidateError(f"draft file set must be exactly {sorted(expected)}")
    evidence_dir = draft_dir / "generation-evidence"
    if tuple(path.name for path in sorted(evidence_dir.iterdir())) != EVIDENCE_ORDER:
        raise CandidateError("generation evidence files/order mismatch")
    evidence = {name: read_json(evidence_dir / name) for name in EVIDENCE_ORDER}
    for name, value in evidence.items():
        context.catalog.validate(value, EVIDENCE_SCHEMAS[name])
    session = read_json(draft_dir / "generation-session.json")
    context.catalog.validate(session, "design-generation-session.schema.json")
    authority_conflicts = _validate_author_required_claims(context, session)
    if authority_conflicts:
        raise AuthorityConflictRequired(authority_conflicts)
    required_now = _validate_dependency_evidence(context, evidence[EVIDENCE_ORDER[0]])
    if required_now:
        raise AuthorRequired(required_now)
    option = evidence["02-option-analysis.json"]
    candidates = option.get("candidates", [])
    candidate_ids = [item["id"] for item in candidates]
    if not candidates or len(candidate_ids) != len(set(candidate_ids)):
        raise CandidateError("option analysis requires uniquely identified candidates")
    if len(candidates) == 1:
        exclusion = option.get("unique_solution_exclusion_evidence")
        if not isinstance(exclusion, str) or not exclusion.strip():
            raise CandidateError("a unique solution requires non-empty exclusion evidence")
    else:
        if len({item["canonical_difference"] for item in candidates}) != len(candidates):
            raise CandidateError("option candidates do not have distinct canonical differences")
        if len({(item["tradeoff"], item["downstream_impact"]) for item in candidates}) != len(candidates):
            raise CandidateError("option candidates do not expose distinct tradeoff/downstream impact")
    if evidence["04-adversarial-self-review.json"].get("verdict") != "pass":
        raise CandidateError("adversarial self-review did not pass")
    model = read_json(draft_dir / "canonical.json")
    context.catalog.validate(model, context.contract["canonical_schema"])
    _validate_common_model(context, model, session)
    candidate_id_set = set(candidate_ids)
    for decision in model["design_decisions"]:
        if not set(decision["candidate_refs"]).issubset(candidate_id_set):
            raise CandidateError(f"{decision['id']}: candidate_refs do not bind option evidence")
    projection = evidence["03-projection-analysis.json"]
    if projection["selected"] not in candidate_id_set:
        raise CandidateError("projection selected option does not exist")
    if projection["projected_ids"] != [item["id"] for item in model["design_decisions"]]:
        raise CandidateError("projection does not exactly cover canonical design decisions")
    if projection["projected_source_ids"] != context.work_order["unresolved_projection"]:
        raise CandidateError("projection does not exactly cover unresolved source IDs")
    if model["decision_dependencies"] != evidence["00-dependency-assessment.json"]["assessments"]:
        raise CandidateError("canonical HDD projection differs from dependency evidence")
    stage_validator(model, context.contract)
    return model, session, evidence


def _manifest_value(context: Context, package: Path, status: str, roles: Mapping[str, Path]) -> dict[str, Any]:
    refs = [file_ref(path, root=package, role=role) for role, path in roles.items()]
    return {
        "schema_version": "1.0", "harness": HARNESS,
        "hld_run_id": context.work_order["hld_run_id"], "revision": context.work_order["revision"],
        "stage": context.contract["stage"], "skill": context.contract["skill"], "status": status,
        "files": refs, "artifact_roles": {item["role"]: item for item in refs},
    }


def _empty_result_fields() -> dict[str, Any]:
    return {
        "completion_ref": None, "internal_manifest_ref": None, "revision_class": None,
        "revision_report_ref": None, "candidate_ref": None, "local_defect_evidence": [],
        "author_event_ref": None, "gate_data_ref": None, "blocked_report_ref": None,
        "blocker_class": None, "affected_ids": [], "runtime_error_ref": None,
    }


def _base_result(context: Context, outcome: str, manifest_path: Path, validation_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "harness": HARNESS,
        "hld_run_id": context.work_order["hld_run_id"], "revision": context.work_order["revision"],
        "stage": context.contract["stage"], "skill": context.contract["skill"],
        "work_order_id": context.work_order["work_order_id"], "task_id": context.work_order["task_id"],
        "event_sequence": context.work_order["event_sequence"], "result_scope": "top_level", "result": outcome,
        "state_before_ref": context.work_order["state_before_ref"], "input_gate_ref": context.work_order["input_gate_ref"],
        "result_manifest_ref": file_ref(manifest_path, root=context.workspace, role="result_manifest" if outcome != "ready" else "package_manifest"),
        "validation_ref": file_ref(validation_path, root=context.workspace, role="validation"),
        "produced_at": context.work_order["result_timestamp"], **_empty_result_fields(),
    }


def _validate_and_write_result(context: Context, result: dict[str, Any]) -> None:
    context.catalog.validate(result, "stage-result.schema.json")
    validate_result_envelope(result, context.work_order)
    write_json(context.output / "stage-result.json", result)


def publish_ready(context: Context, model: dict[str, Any], session: dict[str, Any], evidence: Mapping[str, Any]) -> None:
    package = context.output / "package"
    package.mkdir(parents=True)
    canonical_path = package / context.contract["canonical_file"]
    write_json(canonical_path, model)
    write_json(package / "generation-session.json", session)
    for name in EVIDENCE_ORDER:
        write_json(package / "generation-evidence" / name, evidence[name])
    execution = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "work_order_id": context.work_order["work_order_id"],
        "implementation_sha256": context.work_order["implementation_sha256"],
        "input_gate_ref": context.work_order["input_gate_ref"], "actual_read_refs": session["actual_read_refs"],
        "runtime_read_refs": list(context.allowlist.values()),
        "canonical_sha256": sha256_file(canonical_path),
        "status": "ready", "errors": [],
    }
    context.catalog.validate(execution, "design-execution-record.schema.json")
    write_json(package / "execution-record.json", execution)
    (package / context.contract["preview_file"]).write_text(
        f"# {context.contract['display_name']}\n\nCanonical: `{context.contract['canonical_file']}`\n\nStatus: ready\n",
        encoding="utf-8", newline="",
    )
    validation = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "pass",
        "deterministic_checks": context.contract["deterministic_checks"], "errors": [],
        "semantic_quality_claim": "agent_evidence_only_not_deterministically_proven",
        "semantic_review_ref": "generation-evidence/04-adversarial-self-review.json",
    }
    context.catalog.validate(validation, "design-validation.schema.json")
    write_json(package / "validation.json", validation)
    roles: dict[str, Path] = {
        context.contract["artifact_role"]: canonical_path,
        "generation_session": package / "generation-session.json",
        **{f"generation_evidence::{Path(name).stem}": package / "generation-evidence" / name for name in EVIDENCE_ORDER},
        "execution_record": package / "execution-record.json",
        "preview": package / context.contract["preview_file"],
        "validation": package / "validation.json",
    }
    manifest = _manifest_value(context, package, "ready", roles)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    write_json(package / "package-manifest.json", manifest)
    completion = {
        "schema_version": "1.0", "harness": HARNESS, "stage": context.contract["stage"],
        "skill": context.contract["skill"], "hld_run_id": context.work_order["hld_run_id"],
        "revision": context.work_order["revision"], "status": "ready",
        "input_gate_ref": context.work_order["input_gate_ref"], "state_before_ref": context.work_order["state_before_ref"],
        "work_order_ref": file_ref(context.work_order_path, root=context.workspace, role="work_order"),
        "manifest_ref": file_ref(package / "package-manifest.json", root=context.workspace, role="package_manifest"),
        "validation_ref": file_ref(package / "validation.json", root=context.workspace, role="validation"),
        "upstream_completions": context.work_order["upstream_completions"],
        "canonical_artifacts": [file_ref(canonical_path, root=context.workspace, role=context.contract["artifact_role"])],
        "owner_implementation": {
            "skill": context.contract["skill"], "version": context.contract["runtime_version"],
            "sha256": context.work_order["implementation_sha256"],
        },
        "return_binding": context.work_order["return_binding"],
        "ready_capabilities": context.contract["ready_capabilities"],
        "next_allowed_stage": context.contract["next_stage"],
    }
    context.catalog.validate(completion, "stage-completion.schema.json")
    write_json(package / "stage-completion.json", completion)
    validate_ready_profile(package, context.contract["stage"])
    validate_manifest(package, manifest)
    validate_completion_bindings(context.workspace, package, completion)
    result = _base_result(context, "ready", package / "package-manifest.json", package / "validation.json")
    result["completion_ref"] = file_ref(package / "stage-completion.json", root=context.workspace, role="stage_completion")
    _validate_and_write_result(context, result)


def _publish_nonready(
    context: Context,
    outcome: str,
    roles: Mapping[str, tuple[str, Mapping[str, Any], str]],
    result_update_factory: Callable[[Mapping[str, Path]], Mapping[str, Any]],
) -> None:
    package = context.output / "package"
    package.mkdir(parents=True, exist_ok=False)
    paths: dict[str, Path] = {}
    for role, (name, value, schema_role) in roles.items():
        context.catalog.validate(value, schema_role)
        target = package / name
        write_json(target, value)
        paths[role] = target
    manifest = _manifest_value(context, package, outcome, paths)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    manifest_path = package / "result-manifest.json"
    write_json(manifest_path, manifest)
    validate_manifest(package, manifest)
    result = _base_result(context, outcome, manifest_path, paths["validation"])
    result.update(result_update_factory(paths))
    _validate_and_write_result(context, result)


def _author_required_gate(
    context: Context,
    error: AuthorRequired | AuthorityConflictRequired,
) -> dict[str, Any]:
    affected_ids = list(error.affected_ids)
    if not affected_ids:
        raise ValueError("author-required result needs at least one source control ID")
    return {
        "schema_version": "1.0", "hld_run_id": context.work_order["hld_run_id"],
        "stage": context.contract["stage"], "failed_gate": "AUTHOR_REQUIRED",
        "evidence": str(error), "affected_ids": affected_ids,
        "source_control_id": affected_ids[0],
        "question_text": error.required_action,
    }


def publish_blocked(
    context: Context,
    error: AuthorRequired | AuthorityConflictRequired,
) -> None:
    gate = _author_required_gate(context, error)
    affected_ids = gate["affected_ids"]
    evidence = gate["evidence"]
    report = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "blocked",
        "blocker_class": "author_required", "code": "AUTHOR_REQUIRED",
        "evidence": evidence, "required_action": error.required_action,
    }
    validation = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "blocked",
        "deterministic_checks": context.contract["deterministic_checks"], "errors": [evidence],
        "semantic_quality_claim": "not_evaluated_author_input_required", "semantic_review_ref": None,
    }
    _publish_nonready(
        context, "blocked",
        {
            "gate_data": ("gate-data.json", gate, "design-gate-data.schema.json"),
            "blocked_report": ("blocked-report.json", report, "design-blocked-report.schema.json"),
            "validation": ("validation.json", validation, "design-validation.schema.json"),
        },
        lambda paths: {
            "gate_data_ref": file_ref(paths["gate_data"], root=context.workspace, role="gate_data"),
            "blocked_report_ref": file_ref(paths["blocked_report"], root=context.workspace, role="blocked_report"),
            "blocker_class": "author_required", "affected_ids": affected_ids,
        },
    )


def publish_upstream_defect(context: Context, error: UpstreamDefect) -> None:
    evidence = str(error)
    gate = {
        "schema_version": "1.0", "hld_run_id": context.work_order["hld_run_id"],
        "stage": context.contract["stage"], "failed_gate": "UPSTREAM_DEFECT",
        "evidence": evidence, "affected_ids": error.affected_ids,
    }
    report = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "blocked",
        "blocker_class": "upstream_defect", "code": "UPSTREAM_DEFECT",
        "evidence": evidence, "required_action": error.required_action,
    }
    validation = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "blocked",
        "deterministic_checks": context.contract["deterministic_checks"], "errors": [evidence],
        "semantic_quality_claim": "not_evaluated_upstream_correction_required", "semantic_review_ref": None,
    }
    _publish_nonready(
        context, "blocked",
        {
            "gate_data": ("gate-data.json", gate, "design-gate-data.schema.json"),
            "blocked_report": ("blocked-report.json", report, "design-blocked-report.schema.json"),
            "validation": ("validation.json", validation, "design-validation.schema.json"),
        },
        lambda paths: {
            "gate_data_ref": file_ref(paths["gate_data"], root=context.workspace, role="gate_data"),
            "blocked_report_ref": file_ref(paths["blocked_report"], root=context.workspace, role="blocked_report"),
            "blocker_class": "upstream_defect", "affected_ids": error.affected_ids,
        },
    )


def publish_revise(context: Context, draft_dir: Path, errors: list[str]) -> None:
    raw_candidate = read_json(draft_dir / "canonical.json") if (draft_dir / "canonical.json").is_file() else {"unavailable": True}
    candidate_snapshot = json.dumps(raw_candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    candidate = {
        "schema_version": "1.0", "stage": context.contract["stage"], "skill": context.contract["skill"],
        "status": "revise", "candidate_sha256": hashlib.sha256(candidate_snapshot.encode("utf-8")).hexdigest(),
        "candidate_snapshot_json": candidate_snapshot,
    }
    execution = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "work_order_id": context.work_order["work_order_id"],
        "status": "revise", "implementation_sha256": context.work_order["implementation_sha256"],
        "input_gate_ref": context.work_order["input_gate_ref"], "actual_read_refs": [],
        "runtime_read_refs": list(context.allowlist.values()), "canonical_sha256": None, "errors": errors,
    }
    report = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "defect_origin": "reviewer_local", "errors": errors,
    }
    validation = {
        "schema_version": "1.0", "skill": context.contract["skill"], "stage": context.contract["stage"],
        "hld_run_id": context.work_order["hld_run_id"], "status": "fail",
        "deterministic_checks": context.contract["deterministic_checks"], "errors": errors,
        "semantic_quality_claim": "candidate_rejected_before_semantic_acceptance", "semantic_review_ref": None,
    }
    _publish_nonready(
        context, "revise",
        {
            "candidate": ("candidate.json", candidate, "design-candidate-envelope.schema.json"),
            "execution_record": ("execution-record.json", execution, "design-execution-record.schema.json"),
            "revision_report": ("revision-report.json", report, "design-revision-report.schema.json"),
            "validation": ("validation.json", validation, "design-validation.schema.json"),
        },
        lambda paths: {
            "revision_class": "local_candidate",
            "revision_report_ref": file_ref(paths["revision_report"], root=context.workspace, role="revision_report"),
            "candidate_ref": file_ref(paths["candidate"], root=context.workspace, role="candidate"),
            "local_defect_evidence": [file_ref(paths["revision_report"], root=context.workspace, role="defect_evidence")],
        },
    )


def validate_existing(skill_root: Path, work_order_path: Path) -> dict[str, Any]:
    """Public-contract revalidation used by tests and the parent Harness."""
    context = load_context(skill_root, work_order_path, require_new_output=False)
    result = read_json(context.output / "stage-result.json")
    context.catalog.validate(result, "stage-result.schema.json")
    validate_result_envelope(result, context.work_order)
    manifest_path = verify_file_ref(result["result_manifest_ref"], context.workspace)
    manifest = read_json(manifest_path)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    validate_manifest(manifest_path.parent, manifest)
    if result["result"] == "ready":
        completion_path = verify_file_ref(result["completion_ref"], context.workspace, expected_role="stage_completion")
        completion = read_json(completion_path)
        context.catalog.validate(completion, "stage-completion.schema.json")
        validate_ready_profile(manifest_path.parent, context.contract["stage"])
        validate_completion_bindings(context.workspace, manifest_path.parent, completion)
    return result


def execute(skill_root: Path, work_order_path: Path, draft_dir: Path, stage_validator: StageValidator) -> tuple[int, dict[str, Any] | None]:
    try:
        context = load_context(skill_root, work_order_path)
    except (OSError, ValueError, ContractError) as error:
        print(f"input gate failed: {error}", file=sys.stderr)
        return 3, None
    try:
        model, session, evidence = validate_draft(context, draft_dir.resolve(strict=True), stage_validator)
    except UpstreamDefect as error:
        context.output.mkdir(parents=True, exist_ok=False)
        publish_upstream_defect(context, error)
        return 2, read_json(context.output / "stage-result.json")
    except (AuthorRequired, AuthorityConflictRequired) as error:
        context.output.mkdir(parents=True, exist_ok=False)
        publish_blocked(context, error)
        return 2, read_json(context.output / "stage-result.json")
    except (OSError, ValueError, ContractError) as error:
        context.output.mkdir(parents=True, exist_ok=False)
        publish_revise(context, draft_dir, [str(error)])
        return 2, read_json(context.output / "stage-result.json")
    context.output.mkdir(parents=True, exist_ok=False)
    publish_ready(context, model, session, evidence)
    return 0, read_json(context.output / "stage-result.json")


def cli_main(skill_root: Path, stage_validator: StageValidator) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_order", type=Path)
    parser.add_argument("draft_dir", type=Path)
    args = parser.parse_args()
    code, _ = execute(skill_root.resolve(), args.work_order.resolve(), args.draft_dir.resolve(), stage_validator)
    return code
