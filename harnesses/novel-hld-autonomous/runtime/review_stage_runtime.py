"""Public HQ1 runtime: independent, evidence-bound semantic review and packaging."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import ContractError, canonical_sha256, file_ref, json_pointer, read_json, resolve_inside, sha256_file, verify_file_ref, write_json
from .contracts import HARNESS, ID_OWNER_PREFIX, SKILLS, UPSTREAM
from .design_stage_runtime import GateError, CandidateError, Context, _manifest_value, implementation_sha256, load_context
from .hdd import expected_hdd_id
from .package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope


STAGE_SCHEMAS = {
    "HA1": "ha1-canonical.schema.json", "HS1": "hs1-canonical.schema.json",
    "HC1": "hc1-canonical.schema.json", "HI1": "hi1-canonical.schema.json",
    "HR1": "hr1-canonical.schema.json", "HK1": "hk1-canonical.schema.json",
}
DOMAIN_CHECKS = (
    "narrative_architecture", "storyline_choreography", "character_arc_placement",
    "information_architecture", "rhythm_continuity", "key_scene_functions",
)
CROSS_CHECKS = (
    "subject_and_storyline_coverage", "world_environment_event_character_derivation",
    "cross_stage_causality_and_state", "suspense_conflict_rhythm_and_key_function",
)
CHALLENGES = (
    "causality", "resource_authority", "knowledge_pov", "time_space",
    "character_state", "choice_cost_consequence", "theme_support", "hld_lld_boundary",
)
ROUTING_KEYS = {"owner", "owner_stage", "target_skill", "target_stage", "return_stage", "reopen_from", "resume_stage", "invalidated_suffix"}
PREFERENCE_MARKERS = ("personal preference", "marketable", "must use three act", "must use five act", "我不喜欢", "市场不喜欢")

HQ1_CONTRACT_KEYS = {
    "artifact_role", "canonical_file", "canonical_schema", "additional_schema_paths",
    "additional_implementation_paths", "contract_schema_version", "public_entrypoint",
    "implementation_closure", "decision_prefix", "deterministic_checks", "display_name",
    "forbidden_keys", "model_required", "next_stage", "object_arrays", "preview_file",
    "ready_capabilities", "runtime_version", "skill", "stage", "upstream_stages",
}


def _validate_hq1_runtime_contract(skill_root: Path) -> None:
    """Fail closed before load_context if the coordinator-facing contract drifts."""
    contract = json.loads((skill_root / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
    if set(contract) != HQ1_CONTRACT_KEYS:
        raise GateError("HQ1 runtime contract keys are not the closed public set")
    expected_entry = {
        "path": "skills/novel-hld-semantic-reviewer/scripts/run_skill.py",
        "runtime": "python",
        "arguments": ["work_order", "draft_dir"],
    }
    if contract["contract_schema_version"] != "1.0" or contract["public_entrypoint"] != expected_entry:
        raise GateError("HQ1 public entrypoint contract is invalid")
    closure = contract["implementation_closure"]
    if set(closure) != {"algorithm", "ordered_files"}:
        raise GateError("HQ1 implementation closure fields are not closed")
    if closure["algorithm"] != "sha256-basename-nul-content-nul-v1":
        raise GateError("HQ1 implementation closure algorithm is invalid")
    repository = skill_root.parents[1]
    declared = [resolve_inside(repository, relative) for relative in closure["ordered_files"]]
    if len(declared) != len(set(declared)) or not all(path.is_file() for path in declared):
        raise GateError("HQ1 implementation closure is missing, duplicated, or unreadable")


class ReviewBlocked(ContractError):
    def __init__(self, blocker_class: str, findings: list[dict[str, Any]]) -> None:
        super().__init__(f"HQ1 blocked by {blocker_class}")
        self.blocker_class = blocker_class
        self.findings = findings


def _walk_ids(value: Any, stage: str, locator: str = "") -> dict[str, tuple[str, Any]]:
    found: dict[str, tuple[str, Any]] = {}
    if isinstance(value, dict):
        identifier = value.get("id")
        if isinstance(identifier, str):
            prefix = identifier.split("-", 1)[0]
            if ID_OWNER_PREFIX.get(prefix) == stage:
                found[identifier] = (locator or "", value)
        for key, child in value.items():
            token = key.replace("~", "~0").replace("/", "~1")
            found.update(_walk_ids(child, stage, f"{locator}/{token}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.update(_walk_ids(child, stage, f"{locator}/{index}"))
    return found


def _semantic_read_refs(context: Context) -> list[dict[str, str]]:
    roles = context.allowlist
    ordered: list[dict[str, str]] = []
    for item in context.gate["source_lineage_refs"]:
        ordered.append(roles[item["role"]])
    for stage in UPSTREAM["HQ1"]:
        stage_roles = (
            ("upstream::HB0::main", "baseline_manifest", "upstream::HB0::completion", "baseline_validation")
            if stage == "HB0" else tuple(f"upstream::{stage}::{suffix}" for suffix in ("main", "manifest", "completion", "validation"))
        )
        ordered.extend(roles[role] for role in stage_roles)
    if len({item["role"] for item in ordered}) != len(ordered):
        raise GateError("HQ1 semantic read roles are not unique")
    return ordered


def _producer_tasks(context: Context) -> list[str]:
    tasks: list[str] = []
    for stage, artifact in zip(UPSTREAM["HQ1"], context.work_order["upstream_completions"]):
        completion = read_json(verify_file_ref({
            "role": f"upstream::{stage}::completion", "path": artifact["completion_path"],
            "sha256": artifact["completion_sha256"],
        }, context.workspace))
        order = read_json(verify_file_ref(completion["work_order_ref"], context.workspace))
        context.catalog.validate(order, "work-order.schema.json")
        tasks.append(order["task_id"])
    if len(tasks) != len(set(tasks)) or context.work_order["task_id"] in tasks:
        raise GateError("HQ1 task identity is not isolated from every producer")
    return tasks


def _load_upstream_models(context: Context) -> tuple[dict[str, dict[str, Any]], dict[str, tuple[str, Any]]]:
    models: dict[str, dict[str, Any]] = {}
    objects: dict[str, tuple[str, Any]] = {}
    for stage, artifact in zip(UPSTREAM["HQ1"], context.work_order["upstream_completions"]):
        main = read_json(verify_file_ref({"role": f"upstream::{stage}::main", "path": artifact["path"], "sha256": artifact["sha256"]}, context.workspace))
        if stage in STAGE_SCHEMAS:
            context.catalog.validate(main, STAGE_SCHEMAS[stage])
            validation = read_json(verify_file_ref(context.allowlist[f"upstream::{stage}::validation"], context.workspace))
            context.catalog.validate(validation, "design-validation.schema.json")
            objects.update(_walk_ids(main, stage))
        else:
            context.catalog.validate(main, "hld-control-baseline.schema.json")
            validation = read_json(verify_file_ref(context.allowlist["baseline_validation"], context.workspace))
            context.catalog.validate(validation, "hb0-validation.schema.json")
        models[stage] = main
    return models, objects


def _validate_source_values(context: Context) -> set[str]:
    source_ids: set[str] = set()
    lineage = {(item["path"], item["sha256"]): item for item in context.gate["source_lineage_refs"]}
    for entry in context.source_index["entries"]:
        if "HQ1" not in entry["allowed_stages"]:
            continue
        key = (entry["workspace_source_ref"]["path"], entry["workspace_source_ref"]["sha256"])
        if key not in lineage:
            raise GateError(f"HQ1 authorized source omitted from source lineage: {entry['source_id']}")
        document = read_json(verify_file_ref(entry["workspace_source_ref"], context.workspace))
        value = json_pointer(document, entry["locator"])
        indexed_value = _indexed_source_value(entry, value)
        if canonical_sha256(indexed_value) != entry["value_sha256"]:
            raise GateError(f"HQ1 source locator/value hash mismatch: {entry['source_id']}")
        source_ids.add(entry["source_id"])
    return source_ids


def _indexed_source_value(entry: Mapping[str, Any], value: Any) -> Any:
    """Reproduce the baseline's closed typed source-index projections."""
    discriminator = entry.get("schema_discriminator")
    is_e1_slot = (
        entry.get("domain") == "environments"
        and entry.get("source", {}).get("path") == "P1/canonical-models/environment-system.json"
        and str(entry.get("source_id", "")).startswith("SLOT-")
    )
    if not is_e1_slot:
        return value
    if discriminator != "e1_operational_slot":
        raise GateError(f"HQ1 E1 operational slot discriminator is invalid: {entry['source_id']}")
    bound_slot = value.get("actor_slot_id") if isinstance(value, Mapping) else value
    if bound_slot != entry["source_id"]:
        raise GateError(f"HQ1 E1 operational slot projection is invalid: {entry['source_id']}")
    return {"slot_id": entry["source_id"], "kind": "e1_operational_slot"}


def _iter_primary_evidence(review: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield first-order check evidence; pass claims are summaries, never coverage."""
    for group in ("domain_reviews", "cross_domain_checks", "causal_and_reality_challenges"):
        for item in review[group]:
            yield from item["evidence"]
    yield from review["authority_and_open_item_review"]["evidence"]
    yield from review["boundary_review"]["evidence"]
    for item in review["decision_dependency_review"]:
        yield from item["evidence"]


def _validate_evidence(review: dict[str, Any], models: Mapping[str, Any], known_ids: set[str]) -> None:
    evidence_items = list(_iter_primary_evidence(review))
    evidence_items.extend(evidence for claim in review["pass_claims"] for evidence in claim["evidence"])
    for evidence in evidence_items:
        target = json_pointer(models[evidence["stage"]], evidence["object_locator"])
        if target != evidence["actual_value"]:
            raise CandidateError(f"evidence value differs from canonical locator: {evidence['object_id']}")
        if isinstance(target, dict):
            target_id = target.get("id", target.get("source_id"))
            if target_id != evidence["object_id"]:
                raise CandidateError(f"evidence object_id differs from canonical object: {evidence['object_id']}")
        elif evidence["object_id"] not in known_ids:
            raise CandidateError(f"scalar evidence lacks a known object anchor: {evidence['object_id']}")


def _validate_hdds(context: Context, review: dict[str, Any], known_ids: set[str]) -> None:
    projection = context.work_order["unresolved_projection"]
    hdds = review["decision_dependencies"]
    if [item["source_id"] for item in hdds] != projection:
        raise CandidateError("HQ1 HDDs do not exactly cover ordered quality projection")
    dependencies = {item["source_id"]: item for item in hdds}
    for item in hdds:
        source_id = item["source_id"]
        if item["id"] != expected_hdd_id("HQ1", source_id):
            raise CandidateError(f"invalid HQ1 HDD identity: {source_id}")
        if not set(item["object_evidence_refs"]).issubset(known_ids | set(projection)):
            raise CandidateError(f"HQ1 HDD cites unknown evidence: {source_id}")
        resolved = item["disposition"] == "resolved_by_external_author_event"
        if resolved != (item["resolution_ref"] is not None):
            raise CandidateError(f"HQ1 HDD resolution binding mismatch: {source_id}")
        if resolved:
            if item["resolution_ref"] not in context.allowlist.values():
                raise CandidateError(f"HQ1 HDD resolution is not an exact allowlisted input: {source_id}")
            verify_file_ref(item["resolution_ref"], context.workspace)
        if item["disposition"] == "required_now":
            raise ReviewBlocked("author_required", [{"id": "HFN-HDD-" + source_id, "affected_ids": [source_id]}])
    dependency_review = review["decision_dependency_review"]
    if [item["source_id"] for item in dependency_review] != projection:
        raise CandidateError("decision_dependency_review does not exactly cover quality projection")
    for item in dependency_review:
        if item["hdd_ref"] != dependencies[item["source_id"]]["id"]:
            raise CandidateError("dependency review does not bind its HQ1 HDD")


def validate_review(context: Context, draft: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    if {item.name for item in draft.iterdir()} != {"canonical.json", "review-session.json"}:
        raise CandidateError("HQ1 draft must contain exactly canonical.json and review-session.json")
    review = read_json(draft / "canonical.json")
    session = read_json(draft / "review-session.json")
    context.catalog.validate(review, context.contract["canonical_schema"])
    context.catalog.validate(session, "hq1-review-session.schema.json")
    if review["hld_run_id"] != context.work_order["hld_run_id"] or review["review_task_id"] != context.work_order["task_id"]:
        raise CandidateError("review identity differs from work order")
    if review["input_gate_ref"] != context.work_order["input_gate_ref"]:
        raise CandidateError("review input_gate_ref differs from work order")
    expected_reads = _semantic_read_refs(context)
    if session["actual_read_refs"] != expected_reads or review["source_artifacts"] != expected_reads:
        raise CandidateError("HQ1 actual reads are not the exact isolated semantic closure")
    if session["task_id"] != context.work_order["task_id"] or session["producer_task_ids"] != _producer_tasks(context):
        raise CandidateError("review session task isolation/producers mismatch")
    models, objects = _load_upstream_models(context)
    source_ids = _validate_source_values(context)
    known_ids = set(objects) | source_ids
    _validate_evidence(review, models, known_ids)
    _validate_hdds(context, review, known_ids)

    domain_ids = [item["check_id"] for item in review["domain_reviews"]]
    cross_ids = [item["check_id"] for item in review["cross_domain_checks"]]
    dimensions = [item["dimension"] for item in review["causal_and_reality_challenges"]]
    if domain_ids != list(DOMAIN_CHECKS) or cross_ids != list(CROSS_CHECKS) or dimensions != list(CHALLENGES):
        raise CandidateError("review checklist does not exactly cover frozen domain/cross/challenge order")
    for check, stage in zip(review["domain_reviews"], STAGE_SCHEMAS):
        if {item["stage"] for item in check["evidence"]} != {stage}:
            raise CandidateError(f"domain review evidence is not isolated to {stage}")
    required_cross_stages = {
        CROSS_CHECKS[0]: {"HA1", "HS1"},
        CROSS_CHECKS[1]: {"HS1", "HC1"},
        CROSS_CHECKS[2]: {"HA1", "HS1", "HC1", "HR1"},
        CROSS_CHECKS[3]: {"HI1", "HR1", "HK1"},
    }
    for check in review["cross_domain_checks"]:
        if not required_cross_stages[check["check_id"]].issubset({item["stage"] for item in check["evidence"]}):
            raise CandidateError(f"cross-domain review lacks required producer evidence: {check['check_id']}")
    all_checks = [*review["domain_reviews"], *review["cross_domain_checks"], review["authority_and_open_item_review"], *review["causal_and_reality_challenges"], review["boundary_review"]]
    check_ids = [item["check_id"] for item in all_checks]
    if len(check_ids) != len(set(check_ids)):
        raise CandidateError("review check IDs are not unique")
    if set(review["coverage_summary"]["checked_object_ids"]) != set(objects):
        raise CandidateError("coverage_summary does not exactly cover all six canonical object sets")
    reviewed_object_ids = {
        evidence["object_id"] for evidence in _iter_primary_evidence(review)
        if evidence["stage"] in STAGE_SCHEMAS
    }
    if reviewed_object_ids != set(objects):
        raise CandidateError("object-level evidence does not actually cover every canonical HLD object")
    applicable = [item["check_id"] for item in all_checks if item["status"] != "not_applicable"]
    if review["coverage_summary"]["applicable_checks"] != applicable:
        raise CandidateError("coverage applicable checks differ from actual checklist")
    na_ids = [item["check_id"] for item in review["coverage_summary"]["not_applicable_checks"]]
    if na_ids != [item["check_id"] for item in all_checks if item["status"] == "not_applicable"]:
        raise CandidateError("coverage not-applicable checks differ from actual checklist")

    findings = review["findings"]
    finding_ids = [item["id"] for item in findings]
    if len(finding_ids) != len(set(finding_ids)):
        raise CandidateError("finding IDs are not unique")
    for finding in findings:
        if ROUTING_KEYS & set(finding):
            raise CandidateError("HQ1 finding illegally owns final routing")
        if not set(finding["affected_ids"]).issubset(known_ids):
            raise CandidateError(f"finding cites unknown affected ID: {finding['id']}")
        if any(marker in finding["issue"].lower() for marker in PREFERENCE_MARKERS):
            raise CandidateError(f"preference-only finding is forbidden: {finding['id']}")
    failed_ids = {item["check_id"] for item in all_checks if item["status"] == "fail"}
    cited_failed = {ref for item in findings for ref in item["evidence_refs"] if ref in failed_ids}
    if failed_ids != cited_failed:
        raise CandidateError("every failed check must be bound by a finding")
    pass_ids = [item["check_id"] for item in all_checks if item["status"] == "pass"]
    if [item["check_id"] for item in review["pass_claims"]] != pass_ids:
        raise CandidateError("pass_claims must exactly cover passing checks in order")
    checks_by_id = {item["check_id"]: item for item in all_checks}
    for claim in review["pass_claims"]:
        if claim["evidence"] != checks_by_id[claim["check_id"]]["evidence"]:
            raise CandidateError(f"pass claim evidence is not identical to its passing check: {claim['check_id']}")
    verdict = review["verdict"]
    origins = {item["defect_origin"] for item in findings}
    if verdict == "pass":
        if findings or failed_ids:
            raise CandidateError("pass cannot contain findings or failed checks")
        return review, session, models
    if verdict == "revise":
        if not findings or origins != {"reviewer_local"}:
            raise CandidateError("revise is reserved for HQ1-local review defects")
        raise CandidateError("HQ1 candidate declares reviewer-local revise")
    nonlocal_origins = origins - {"reviewer_local"}
    if verdict != "fail" or len(nonlocal_origins) != 1 or "reviewer_local" in origins:
        raise CandidateError("fail requires one unambiguous non-local defect origin")
    blocker = {"upstream_content": "upstream_defect", "author_required": "author_required", "reality_dependency": "reality_dependency"}[next(iter(nonlocal_origins))]
    raise ReviewBlocked(blocker, findings)


def _future_ref(source: Path, final: Path, workspace: Path, role: str) -> dict[str, str]:
    return {"role": role, "path": final.relative_to(workspace).as_posix(), "sha256": sha256_file(source)}


def _empty_result() -> dict[str, Any]:
    return {"completion_ref":None,"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None}


def _stage_result(context: Context, outcome: str, manifest: Path, validation: Path) -> dict[str, Any]:
    result={"schema_version":"1.0","harness":HARNESS,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"stage":"HQ1","skill":SKILLS["HQ1"],"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"event_sequence":context.work_order["event_sequence"],"result_scope":"top_level","result":outcome,"state_before_ref":context.work_order["state_before_ref"],"input_gate_ref":context.work_order["input_gate_ref"],"result_manifest_ref":None,"validation_ref":None,"produced_at":context.work_order["result_timestamp"],**_empty_result()}
    result["result_manifest_ref"]=_future_ref(manifest, context.output/"package"/manifest.name, context.workspace, "package_manifest" if outcome=="ready" else "result_manifest")
    result["validation_ref"]=_future_ref(validation, context.output/"package"/"validation.json", context.workspace,"validation")
    return result


def _commit(context: Context, staging: Path, outcome: str) -> None:
    result=read_json(staging/"stage-result.json")
    context.catalog.validate(result,"stage-result.schema.json")
    validate_result_envelope(result,context.work_order)
    staging.replace(context.output)
    try:
        manifest_name="package-manifest.json" if outcome=="ready" else "result-manifest.json"
        package=context.output/"package";manifest=read_json(package/manifest_name)
        validate_manifest(package,manifest)
        if outcome=="ready":
            completion=read_json(package/"stage-completion.json")
            validate_ready_profile(package,"HQ1")
            validate_completion_bindings(context.workspace,package,completion)
    except Exception:
        shutil.rmtree(context.output,ignore_errors=True)
        raise


def publish_ready(context: Context, review: dict[str,Any], session: dict[str,Any]) -> None:
    staging=context.output.with_name(context.output.name+f".staging-{uuid.uuid4().hex}");package=staging/"package";package.mkdir(parents=True)
    canonical=package/"hld-semantic-review.json";write_json(canonical,review);write_json(package/"review-session.json",session)
    execution={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"work_order_id":context.work_order["work_order_id"],"status":"ready","implementation_sha256":context.work_order["implementation_sha256"],"input_gate_ref":context.work_order["input_gate_ref"],"actual_read_refs":session["actual_read_refs"],"runtime_read_refs":list(context.allowlist.values()),"canonical_sha256":sha256_file(canonical),"errors":[]}
    context.catalog.validate(execution,"hq1-review-execution.schema.json");write_json(package/"review-execution.json",execution)
    validation={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"status":"pass","deterministic_checks":context.contract["deterministic_checks"],"errors":[],"semantic_verdict":"pass","review_ref":"hld-semantic-review.json"}
    context.catalog.validate(validation,"hq1-validation.schema.json");write_json(package/"validation.json",validation)
    roles={"semantic_review":canonical,"review_session":package/"review-session.json","review_execution":package/"review-execution.json","validation":package/"validation.json"}
    manifest=_manifest_value(context,package,"ready",roles);context.catalog.validate(manifest,"package-manifest.schema.json");write_json(package/"package-manifest.json",manifest)
    completion={"schema_version":"1.0","harness":HARNESS,"stage":"HQ1","skill":SKILLS["HQ1"],"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"status":"ready","input_gate_ref":context.work_order["input_gate_ref"],"state_before_ref":context.work_order["state_before_ref"],"work_order_ref":file_ref(context.work_order_path,root=context.workspace,role="work_order"),"manifest_ref":_future_ref(package/"package-manifest.json",context.output/"package/package-manifest.json",context.workspace,"package_manifest"),"validation_ref":_future_ref(package/"validation.json",context.output/"package/validation.json",context.workspace,"validation"),"upstream_completions":context.work_order["upstream_completions"],"canonical_artifacts":[_future_ref(canonical,context.output/"package/hld-semantic-review.json",context.workspace,"semantic_review")],"owner_implementation":{"skill":SKILLS["HQ1"],"version":"1.0.0","sha256":context.work_order["implementation_sha256"]},"return_binding":context.work_order["return_binding"],"ready_capabilities":context.contract["ready_capabilities"],"next_allowed_stage":"HP1"}
    context.catalog.validate(completion,"stage-completion.schema.json");write_json(package/"stage-completion.json",completion)
    result=_stage_result(context,"ready",package/"package-manifest.json",package/"validation.json");result["completion_ref"]=_future_ref(package/"stage-completion.json",context.output/"package/stage-completion.json",context.workspace,"stage_completion");write_json(staging/"stage-result.json",result);_commit(context,staging,"ready")


def _publish_nonready(context:Context,outcome:str,values:Mapping[str,tuple[str,dict[str,Any],str]],update:Mapping[str,Any])->None:
    staging=context.output.with_name(context.output.name+f".staging-{uuid.uuid4().hex}");package=staging/"package";package.mkdir(parents=True);paths={}
    for role,(name,value,schema) in values.items():context.catalog.validate(value,schema);paths[role]=package/name;write_json(paths[role],value)
    manifest=_manifest_value(context,package,outcome,{role:path for role,path in paths.items()});context.catalog.validate(manifest,"package-manifest.schema.json");write_json(package/"result-manifest.json",manifest)
    result=_stage_result(context,outcome,package/"result-manifest.json",paths["validation"]);result.update(update)
    for key,value in list(result.items()):
        if isinstance(value,dict) and value.get("__role"):
            role=value.pop("__role");result[key]=_future_ref(paths[role],context.output/"package"/paths[role].name,context.workspace,value.pop("role"))
        elif isinstance(value,list) and value and isinstance(value[0],dict) and value[0].get("__role"):
            result[key]=[_future_ref(paths[item["__role"]],context.output/"package"/paths[item["__role"]].name,context.workspace,item["role"]) for item in value]
    write_json(staging/"stage-result.json",result);_commit(context,staging,outcome)


def publish_revise(context:Context,draft:Path,errors:list[str])->None:
    raw=read_json(draft/"canonical.json") if (draft/"canonical.json").is_file() else {"unavailable":True};snapshot=json.dumps(raw,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    candidate={"schema_version":"1.0","stage":"HQ1","skill":SKILLS["HQ1"],"status":"revise","candidate_sha256":hashlib.sha256(snapshot.encode()).hexdigest(),"candidate_snapshot_json":snapshot}
    execution={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"work_order_id":context.work_order["work_order_id"],"status":"revise","implementation_sha256":context.work_order["implementation_sha256"],"input_gate_ref":context.work_order["input_gate_ref"],"actual_read_refs":[],"runtime_read_refs":list(context.allowlist.values()),"canonical_sha256":None,"errors":errors}
    report={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"defect_origin":"reviewer_local","errors":errors}
    validation={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"status":"fail","deterministic_checks":context.contract["deterministic_checks"],"errors":errors,"semantic_verdict":"revise","review_ref":None}
    marker=lambda key,role:{"__role":key,"role":role}
    _publish_nonready(context,"revise",{"candidate":("candidate.json",candidate,"hq1-candidate-envelope.schema.json"),"review_execution":("review-execution.json",execution,"hq1-review-execution.schema.json"),"revision_report":("revision-report.json",report,"hq1-revision-report.schema.json"),"validation":("validation.json",validation,"hq1-validation.schema.json")},{"revision_class":"local_candidate","revision_report_ref":marker("revision_report","revision_report"),"candidate_ref":marker("candidate","candidate"),"local_defect_evidence":[marker("revision_report","defect_evidence")]})


def publish_blocked(context:Context,blocker:str,findings:list[dict[str,Any]])->None:
    affected=sorted({identifier for finding in findings for identifier in finding.get("affected_ids",[])}) or context.work_order["unresolved_projection"]
    finding_ids=sorted({finding["id"] for finding in findings if str(finding.get("id","")).startswith("HFN-")}) or ["HFN-HQ1-BLOCKED"]
    label={"upstream_defect":"UPSTREAM_DEFECT","author_required":"AUTHOR_REQUIRED","reality_dependency":"REALITY_DEPENDENCY"}[blocker]
    gate={"schema_version":"1.0","hld_run_id":context.work_order["hld_run_id"],"stage":"HQ1","failed_gate":label,"evidence":f"HQ1 findings: {','.join(finding_ids)}","affected_ids":affected}
    report={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"status":"blocked","blocker_class":blocker,"code":"HQ1_"+label,"evidence":gate["evidence"],"required_action":"router must derive the producer owner and minimal reopen point from affected IDs","finding_ids":finding_ids,"affected_ids":affected}
    validation={"schema_version":"1.0","skill":SKILLS["HQ1"],"stage":"HQ1","hld_run_id":context.work_order["hld_run_id"],"status":"blocked","deterministic_checks":context.contract["deterministic_checks"],"errors":[gate["evidence"]],"semantic_verdict":"fail","review_ref":None}
    marker=lambda key,role:{"__role":key,"role":role}
    _publish_nonready(context,"blocked",{"gate_data":("gate-data.json",gate,"hq1-gate-data.schema.json"),"blocked_report":("blocked-report.json",report,"hq1-blocked-report.schema.json"),"validation":("validation.json",validation,"hq1-validation.schema.json")},{"gate_data_ref":marker("gate_data","gate_data"),"blocked_report_ref":marker("blocked_report","blocked_report"),"blocker_class":blocker,"affected_ids":affected})


def execute(skill_root:Path,work_order_path:Path,draft:Path)->int:
    try:
        _validate_hq1_runtime_contract(skill_root)
        context=load_context(skill_root,work_order_path)
    except (OSError,ValueError,ContractError) as error:print(f"input gate failed: {error}",file=sys.stderr);return 3
    try:review,session,_=validate_review(context,draft.resolve(strict=True))
    except ReviewBlocked as error:publish_blocked(context,error.blocker_class,error.findings);return 2
    except (OSError,ValueError,ContractError) as error:publish_revise(context,draft,[str(error)]);return 2
    publish_ready(context,review,session);return 0
