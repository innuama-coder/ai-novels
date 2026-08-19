"""Closed public runtime for the two isolated HQ2 internal tasks."""

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

from .canonical import ContractError, canonical_bytes, file_ref, json_pointer, read_json, resolve_inside, sha256_file, verify_file_ref, write_json
from .contracts import INTERNAL_READY_PACKAGE_PROFILES, READY_PACKAGE_PROFILES
from .package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope
from .schema_catalog import SchemaCatalog


HARNESS = "novel-hld-autonomous"
SKILL = "novel-hld-lld-readiness-evaluator"
VERSION = "1.0.0"
STAGE = "HQ2"
DIMENSIONS = ("provenance", "semantic_fit", "instructional_quality", "structure", "consistency", "boundary")
CHECKS = ("public-contract", "task-isolation", "exact-read-closure", "upstream-current-ready", "object-evidence", "verdict-algebra", "exact-profile", "atomic-publication")


class GateError(ContractError):
    pass


class CandidateError(ContractError):
    pass


class SemanticBlocked(ContractError):
    def __init__(self, blocker_class: str, evidence: str, affected_ids: Iterable[str]) -> None:
        super().__init__(evidence)
        self.blocker_class = blocker_class
        self.evidence = evidence
        self.affected_ids = sorted(set(affected_ids))


@dataclass(frozen=True)
class Context:
    skill_root: Path
    workspace: Path
    work_order_path: Path
    work_order: dict[str, Any]
    gate: dict[str, Any]
    mode: str
    mode_contract: dict[str, Any]
    roles: dict[str, Path]
    output: Path
    result_path: Path
    contract: dict[str, Any]
    catalog: SchemaCatalog
    upstream: dict[str, dict[str, Any]]
    producer_task_ids: tuple[str, str]


def _repo(skill_root: Path) -> Path:
    return skill_root.parents[1]


def _contract_path(skill_root: Path) -> Path:
    return skill_root / "references" / "runtime-contract.json"


def _schema_catalog(skill_root: Path) -> SchemaCatalog:
    repo = _repo(skill_root)
    documents: dict[str, Any] = {}
    paths = list((repo / "harnesses/novel-hld-autonomous/schemas").glob("*.schema.json"))
    paths += list((skill_root / "schemas").glob("*.schema.json"))
    paths += list((repo / "skills/novel-hld-package-assembler/references").glob("*.schema.json"))
    paths += [repo / "skills/novel-hld-narrative-architect/schemas/ha1-canonical.schema.json"]
    for path in paths:
        documents[str(path.resolve())] = json.loads(path.read_text(encoding="utf-8"))
    return SchemaCatalog.from_documents(documents)


def load_contract(skill_root: Path, catalog: SchemaCatalog | None = None) -> dict[str, Any]:
    value = json.loads(_contract_path(skill_root).read_text(encoding="utf-8"))
    (catalog or _schema_catalog(skill_root)).validate(value, "hq2-runtime-contract.schema.json")
    return value


def implementation_files(skill_root: Path) -> tuple[Path, ...]:
    catalog = _schema_catalog(skill_root)
    contract = load_contract(skill_root, catalog)
    repo = _repo(skill_root).resolve()
    files = tuple(resolve_inside(repo, relative) for relative in contract["implementation_closure"]["ordered_files"])
    if len(files) != len(set(files)):
        raise GateError("implementation closure contains duplicates")
    entry = resolve_inside(repo, contract["public_entrypoint"]["path"])
    if entry not in files:
        raise GateError("public entrypoint is outside implementation closure")
    return files


def implementation_sha256(skill_root: Path | None = None) -> str:
    skill_root = skill_root or Path(__file__).resolve().parents[3] / "skills" / SKILL
    repo = _repo(skill_root).resolve()
    digest = hashlib.sha256()
    for path in implementation_files(skill_root):
        relative = path.relative_to(repo).as_posix()
        digest.update(relative.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _workspace(work_order_path: Path, work: Mapping[str, Any]) -> Path:
    candidates: list[Path] = []
    for ancestor in (work_order_path.parent, *work_order_path.parents):
        try:
            verify_file_ref(work["input_gate_ref"], ancestor)
            verify_file_ref(work["state_before_ref"], ancestor)
        except Exception:
            continue
        candidates.append(ancestor.resolve())
    unique = list(dict.fromkeys(candidates))
    if len(unique) != 1:
        raise GateError("workspace cannot be resolved uniquely from sealed bootstrap references")
    return unique[0]


def _same_ref(path: Path, reference: Mapping[str, str], workspace: Path) -> bool:
    return reference["path"] == path.relative_to(workspace).as_posix() and reference["sha256"] == sha256_file(path)


def _admit_upstream(context: Context, stage: str, artifact: Mapping[str, Any]) -> dict[str, Any]:
    workspace = context.workspace
    prefix = stage.lower()
    completion_path = context.roles[f"{prefix}_completion"]
    producer_path = context.roles[f"{prefix}_work_order"]
    if completion_path.relative_to(workspace).as_posix() != artifact["completion_path"] or sha256_file(completion_path) != artifact["completion_sha256"]:
        raise GateError(f"{stage} completion artifactReference is stale")
    completion = read_json(completion_path)
    context.catalog.validate(completion, "stage-completion.schema.json")
    if (completion["stage"], completion["status"]) != (stage, "ready"):
        raise GateError(f"{stage} is not a current ready package")
    if completion["hld_run_id"] != context.work_order["hld_run_id"]:
        raise GateError(f"{stage} run identity differs from HQ2")
    if not any(ref["path"] == artifact["path"] and ref["sha256"] == artifact["sha256"] for ref in completion["canonical_artifacts"]):
        raise GateError(f"{stage} primary artifact is not completion-bound")
    if completion["work_order_ref"]["path"] != producer_path.relative_to(workspace).as_posix() or completion["work_order_ref"]["sha256"] != sha256_file(producer_path):
        raise GateError(f"{stage} producer work-order binding is stale")
    producer_order = read_json(producer_path)
    context.catalog.validate(producer_order, "work-order.schema.json")
    if producer_order["stage"] != stage or producer_order["hld_run_id"] != context.work_order["hld_run_id"]:
        raise GateError(f"{stage} producer work-order identity is stale")
    result = {"main": resolve_inside(workspace, artifact["path"]), "completion_path": completion_path, "completion": completion, "producer_task_id": producer_order["task_id"]}
    if stage == "HP1":
        manifest_path = context.roles["hp1_manifest"]
        if manifest_path.relative_to(workspace).as_posix() != artifact["manifest_path"] or sha256_file(manifest_path) != artifact["manifest_sha256"]:
            raise GateError("HP1 manifest artifactReference is stale")
        manifest = read_json(manifest_path)
        context.catalog.validate(manifest, "package-manifest.schema.json")
        if (manifest["stage"], manifest["status"], manifest["hld_run_id"]) != ("HP1", "ready", context.work_order["hld_run_id"]):
            raise GateError("HP1 manifest identity is stale")
        if completion["manifest_ref"]["path"] != manifest_path.relative_to(workspace).as_posix() or completion["manifest_ref"]["sha256"] != sha256_file(manifest_path):
            raise GateError("HP1 completion/manifest binding is stale")
        result.update({"manifest_path": manifest_path, "manifest": manifest})
    return result


def _bound_manifest_role(upstream: Mapping[str, Any], role: str) -> Path:
    ref = upstream["manifest"]["artifact_roles"].get(role)
    if not isinstance(ref, dict):
        raise GateError(f"HP1 manifest lacks role {role}")
    return verify_file_ref(ref, upstream["manifest_path"].parent)


def _validate_role_bindings(context: Context) -> None:
    hb0, hp1 = context.upstream["HB0"], context.upstream["HP1"]
    roles = context.roles
    if context.mode == "consumer_test":
        if roles["lld_handoff"] != _bound_manifest_role(hp1, "lld_handoff"):
            raise GateError("consumer lld_handoff is not current HP1 handoff")
        canonical_schema = context.skill_root.parent / "novel-hld-package-assembler/references/lld-handoff.schema.json"
        if roles["lld_handoff_schema"].read_bytes() != canonical_schema.read_bytes():
            raise GateError("consumer handoff schema differs from the implementation-bound schema")
    else:
        expected = {
            "novel_hld_package": hp1["main"], "hp1_manifest": hp1["manifest_path"],
            "hp1_completion": hp1["completion_path"], "hp1_validation": verify_file_ref(hp1["completion"]["validation_ref"], context.workspace),
            "lld_handoff": _bound_manifest_role(hp1, "lld_handoff"), "hld_spec": _bound_manifest_role(hp1, "hld_spec"),
            "cross_index": _bound_manifest_role(hp1, "cross_index"), "traceability": _bound_manifest_role(hp1, "traceability"),
        }
        canonical = hp1["manifest_path"].parent / "canonical-models/narrative-architecture.json"
        if not any(item["path"] == canonical.relative_to(hp1["manifest_path"].parent).as_posix() and item["sha256"] == sha256_file(canonical) for item in hp1["manifest"]["files"]):
            raise GateError("fidelity canonical_model is not manifest-bound")
        expected["canonical_model"] = canonical
        for role, path in expected.items():
            if roles[role] != path:
                raise GateError(f"fidelity role is not bound to current HP1: {role}")


def load_context(skill_root: Path, work_order_path: Path) -> Context:
    catalog = _schema_catalog(skill_root); contract = load_contract(skill_root, catalog)
    work = read_json(work_order_path); catalog.validate(work, "work-order.schema.json")
    workspace = _workspace(work_order_path, work)
    if (work["stage"], work["exact_owner_skill"], work["owner_version"], work["action"], work["submission_status"]) != (STAGE, SKILL, VERSION, "execute", "open"):
        raise GateError("HQ2 work-order identity/action is invalid")
    if work["implementation_sha256"] != implementation_sha256(skill_root):
        raise GateError("HQ2 implementation digest is stale")
    if work["mode"] != "forward" or work["return_binding"] is not None or work["revision_plan_ref"] is not None or work["revision_plan_state_ref"] is not None or work["unresolved_projection"]:
        raise GateError("HQ2 internal work-order must be forward with no unresolved or return binding")
    gate_path = verify_file_ref(work["input_gate_ref"], workspace); state_path = verify_file_ref(work["state_before_ref"], workspace)
    gate = read_json(gate_path); catalog.validate(gate, "input-gate.schema.json")
    shared = ("harness","hld_run_id","stage","mode","state_before_ref","upstream_completions","exact_owner_skill","owner_version","implementation_sha256","return_binding","unresolved_projection","revision_plan_ref","revision_plan_state_ref","file_allowlist")
    if any(gate[field] != work[field] for field in shared):
        raise GateError("HQ2 input-gate/work-order drift")
    if len(work["upstream_completions"]) != 2:
        raise GateError("HQ2 requires exactly HB0 and HP1")
    refs = work["file_allowlist"]
    role_order = tuple(ref["role"] for ref in refs)
    matching = [name for name, spec in contract["modes"].items() if role_order == tuple(spec["required_roles"])]
    if len(matching) != 1:
        raise GateError("HQ2 allowlist is not one exact mode closure")
    mode = matching[0]; mode_contract = contract["modes"][mode]
    roles: dict[str, Path] = {}
    for ref in refs:
        if ref["role"] in roles:
            raise GateError("HQ2 duplicate allowlist role")
        path = verify_file_ref(ref, workspace)
        if path in roles.values():
            raise GateError("HQ2 duplicate allowlist path")
        roles[ref["role"]] = path
    output = resolve_inside(workspace, work["output_directory"], must_exist=False, file_only=False)
    result_path = output.parent / "stage-result.json"
    if output.exists() or result_path.exists():
        raise GateError("HQ2 output/result path already exists")
    if gate_path == state_path or gate_path in roles.values() or state_path in roles.values():
        raise GateError("operational refs leaked into semantic closure")
    provisional = Context(skill_root, workspace, work_order_path, work, gate, mode, mode_contract, roles, output, result_path, contract, catalog, {}, ("", ""))
    hb0 = _admit_upstream(provisional, "HB0", work["upstream_completions"][0])
    hp1 = _admit_upstream(provisional, "HP1", work["upstream_completions"][1])
    producer_ids = (hb0["producer_task_id"], hp1["producer_task_id"])
    if len(set(producer_ids)) != 2 or work["task_id"] in producer_ids:
        raise GateError("HQ2 task is not isolated from HB0/HP1 producer tasks")
    context = Context(skill_root, workspace, work_order_path, work, gate, mode, mode_contract, roles, output, result_path, contract, catalog, {"HB0":hb0,"HP1":hp1}, producer_ids)
    _validate_role_bindings(context)
    return context


def _iter_evidence(model: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    groups = ("storyline_trace_tests","character_arc_trace_tests","key_function_consumption_tests") if model["mode"] == "consumer_test" else ("obligation_coverage_tests","classification_fidelity_tests")
    for group in groups:
        for test in model[group]:
            yield from test["evidence"]
    singleton = "constraint_open_elaboration_freedom_test" if model["mode"] == "consumer_test" else "source_lwr_to_lwk_bijection_test"
    yield from model[singleton]["evidence"]
    for dimension in model["evidence_dimensions"]:
        yield from dimension["evidence"]


def _validate_evidence(context: Context, model: Mapping[str, Any]) -> None:
    json_roles = {role: read_json(path) for role, path in context.roles.items() if path.suffix.lower() == ".json"}
    for evidence in _iter_evidence(model):
        role = evidence["role"]
        if role not in json_roles:
            raise CandidateError(f"evidence role is not a JSON semantic input: {role}")
        actual = json_pointer(json_roles[role], evidence["object_locator"])
        if actual != evidence["actual_value"]:
            raise CandidateError(f"evidence actual value drift: {evidence['object_id']}")
        if not isinstance(actual, dict) or actual.get("id") != evidence["object_id"]:
            raise CandidateError(f"evidence locator does not resolve the named object: {evidence['object_id']}")


def _validate_session(context: Context, model: Mapping[str, Any], session: Mapping[str, Any]) -> None:
    context.catalog.validate(session, "hq2-review-session.schema.json")
    identity = (SKILL, STAGE, context.mode, context.work_order["hld_run_id"], context.work_order["task_id"])
    if (session["skill"],session["stage"],session["mode"],session["hld_run_id"],session["task_id"]) != identity:
        raise CandidateError("HQ2 review-session identity differs from work-order")
    if tuple(session["producer_task_ids"]) != context.producer_task_ids:
        raise CandidateError("HQ2 review-session producer task binding is stale")
    expected = context.work_order["file_allowlist"]
    if session["actual_read_refs"] != expected or model["source_artifacts"] != expected:
        raise CandidateError("HQ2 actual reads are not the exact mode closure")
    if context.mode == "consumer_test":
        if session["sealed_consumer_task_id"] is not None:
            raise CandidateError("consumer task cannot bind another consumer task")
    else:
        sealed = read_json(context.roles["sealed_consumption_test"])
        if session["sealed_consumer_task_id"] != sealed.get("task_id") or sealed.get("task_id") == context.work_order["task_id"]:
            raise CandidateError("fidelity task is not isolated from its sealed consumer task")


def _test_ids(tests: Iterable[Mapping[str, Any]]) -> list[str]:
    return [item["id"] for item in tests]


def _covered(tests: Iterable[Mapping[str, Any]]) -> set[str]:
    return {identifier for item in tests for identifier in item["input_ids"]}


def _check_test_identity(tests: list[dict[str, Any]], expected: set[str], label: str, *, allow_empty: bool = False) -> None:
    if len(_test_ids(tests)) != len(set(_test_ids(tests))):
        raise CandidateError(f"{label} has duplicate test IDs")
    if not expected and allow_empty:
        if tests:
            raise CandidateError(f"{label} must be empty when no source IDs exist")
        return
    if _covered(tests) != expected:
        raise CandidateError(f"{label} does not exactly cover required IDs")


def _validate_dimensions(model: Mapping[str, Any], known_ids: set[str]) -> None:
    if tuple(item["dimension"] for item in model["evidence_dimensions"]) != DIMENSIONS:
        raise CandidateError("HQ2 evidence dimensions are not in frozen order")
    for item in model["evidence_dimensions"]:
        if not set(item["object_ids"]).issubset(known_ids):
            raise CandidateError(f"dimension cites unknown object: {item['dimension']}")


def _verdict(model: Mapping[str, Any], tests: list[Mapping[str, Any]], findings: list[Mapping[str, Any]]) -> None:
    failed = {item["id"] for item in tests if item["verdict"] == "fail"}
    evidence_refs = {ref for finding in findings for ref in finding["evidence_refs"]}
    if not failed.issubset(evidence_refs):
        raise CandidateError("each failed HQ2 test must be finding-bound")
    verdict, origin = model["verdict"], model["defect_origin"]
    if verdict == "pass":
        if origin != "none" or failed or findings or any(item["verdict"] != "pass" for item in model["evidence_dimensions"]):
            raise CandidateError("HQ2 pass contradicts its tests/findings/dimensions")
    elif verdict == "revise":
        if origin != "reviewer_local":
            raise CandidateError("HQ2 revise is reserved for reviewer-local defects")
    elif verdict == "fail":
        mapping = {"upstream_content":"upstream_defect","author_required":"author_required","reality_dependency":"reality_dependency"}
        if origin not in mapping or not findings:
            raise CandidateError("HQ2 fail lacks an actionable nonlocal origin/finding")
        raise SemanticBlocked(mapping[origin], f"HQ2 {model['mode']} found {origin}", [value for item in findings for value in item["affected_ids"]])


def _validate_consumer(context: Context, model: dict[str, Any]) -> None:
    handoff = read_json(context.roles["lld_handoff"])
    context.catalog.validate(handoff, "lld-handoff.schema.json")
    if handoff["hld_run_id"] != context.work_order["hld_run_id"]:
        raise CandidateError("consumer handoff run identity is stale")
    units = handoff["work_units"]; unit_ids = {item["id"] for item in units}
    story_ids = {value for item in units for value in item["storyline_ids"]}
    character_ids = {value for item in units for value in item["character_ids"]}
    key_ids = unit_ids | {value for item in units for value in item["hkf_ids"]}
    if set(model["reconstruction_results"]["lld_work_order"]) != unit_ids:
        raise CandidateError("consumer reconstruction omits or invents LLD work units")
    states = {item["work_unit_id"]:(item["entry_state"],item["exit_state"]) for item in model["reconstruction_results"]["entry_exit_states"]}
    if states != {item["id"]:(item["entry_state"],item["exit_state"]) for item in units}:
        raise CandidateError("consumer entry/exit reconstruction differs from handoff")
    _check_test_identity(model["storyline_trace_tests"], story_ids, "storyline tests")
    _check_test_identity(model["character_arc_trace_tests"], character_ids, "character tests", allow_empty=True)
    _check_test_identity(model["key_function_consumption_tests"], key_ids, "key-function tests")
    constraint = model["constraint_open_elaboration_freedom_test"]
    if set(constraint["input_ids"]) != unit_ids:
        raise CandidateError("classification test does not exactly cover work units")
    primary = [*model["storyline_trace_tests"],*model["character_arc_trace_tests"],*model["key_function_consumption_tests"],constraint]
    primary_evidence = {evidence["object_id"] for test in primary for evidence in test["evidence"] if evidence["role"] == "lld_handoff"}
    if primary_evidence != unit_ids:
        raise CandidateError("consumer first-order evidence does not cover every handoff work unit")
    known = unit_ids | story_ids | character_ids | key_ids
    _validate_dimensions(model, known)
    findings = [*model["missing_guesswork"],*model["findings"]]
    _verdict(model, primary, findings)


def _validate_sealed_consumer(context: Context) -> dict[str, Any]:
    manifest_path = context.roles["sealed_consumption_manifest"]
    manifest = read_json(manifest_path)
    context.catalog.validate(manifest, "package-manifest.schema.json")
    if (manifest["stage"],manifest["skill"],manifest["status"],manifest["hld_run_id"]) != (STAGE,SKILL,"ready",context.work_order["hld_run_id"]):
        raise GateError("sealed consumer manifest identity is stale")
    expected_members = set(context.contract["modes"]["consumer_test"]["ready_profile"]) - {"package-manifest.json"}
    if {item["path"] for item in manifest["files"]} != expected_members:
        raise GateError("sealed consumer manifest profile is not exact")
    main_ref = manifest["artifact_roles"].get("handoff_consumption_test")
    if not isinstance(main_ref, dict) or verify_file_ref(main_ref, manifest_path.parent) != context.roles["sealed_consumption_test"]:
        raise GateError("sealed consumer main is not manifest-bound")
    sealed = read_json(context.roles["sealed_consumption_test"])
    context.catalog.validate(sealed, "hq2-consumption-test.schema.json")
    if (sealed["mode"],sealed["verdict"],sealed["defect_origin"],sealed["hld_run_id"]) != ("consumer_test","pass","none",context.work_order["hld_run_id"]):
        raise GateError("fidelity requires a current sealed consumer pass")
    return sealed


def _validate_fidelity(context: Context, model: dict[str, Any]) -> None:
    sealed = _validate_sealed_consumer(context)
    if model["sealed_consumption_test_ref"] != next(ref for ref in context.work_order["file_allowlist"] if ref["role"] == "sealed_consumption_test"):
        raise CandidateError("fidelity canonical does not bind the exact sealed consumer")
    package = read_json(context.roles["novel_hld_package"]); handoff = read_json(context.roles["lld_handoff"])
    cross = read_json(context.roles["cross_index"]); trace = read_json(context.roles["traceability"])
    canonical = read_json(context.roles["canonical_model"]); validation = read_json(context.roles["hp1_validation"])
    context.catalog.validate(package,"novel-hld-package.schema.json");context.catalog.validate(handoff,"lld-handoff.schema.json")
    context.catalog.validate(cross,"hld-cross-index.schema.json");context.catalog.validate(trace,"hld-traceability-matrix.schema.json")
    if not isinstance(canonical,dict):raise GateError("HP1 canonical_model is not a JSON object")
    context.catalog.validate(validation,"hp1-validation.schema.json")
    if not context.roles["hld_spec"].read_text(encoding="utf-8").strip():
        raise GateError("HP1 HLD specification is empty")
    handoff_package = verify_file_ref(handoff["current_hld_package"], context.roles["lld_handoff"].parent)
    if handoff_package != context.roles["novel_hld_package"]:
        raise CandidateError("handoff does not bind the current machine package")
    units = handoff["work_units"]; unit_ids = {item["id"] for item in units}; source_lwrs = {item["source_lwr_id"] for item in units}
    trace_lwrs = {value for record in trace["records"] for value in record["lwr_ids"]}; trace_lwks = {value for record in trace["records"] for value in record["lwk_ids"]}
    if source_lwrs != trace_lwrs or unit_ids != trace_lwks:
        raise CandidateError("HP1 traceability and handoff LWR/LWK sets differ")
    bijection = model["source_lwr_to_lwk_bijection_test"]
    if set(bijection["input_ids"]) != source_lwrs | unit_ids:
        raise CandidateError("fidelity bijection test does not cover exact LWR/LWK sets")
    obligation_ids = unit_ids | {value for item in units for value in item["hkf_ids"]}
    _check_test_identity(model["obligation_coverage_tests"], obligation_ids, "fidelity obligation tests")
    _check_test_identity(model["classification_fidelity_tests"], unit_ids, "fidelity classification tests")
    primary = [bijection,*model["obligation_coverage_tests"],*model["classification_fidelity_tests"]]
    unit_evidence = {ev["object_id"] for test in primary for ev in test["evidence"] if ev["role"] == "lld_handoff"}
    trace_evidence = {ev["object_id"] for test in primary for ev in test["evidence"] if ev["role"] == "traceability"}
    if unit_evidence != unit_ids or trace_evidence != {item["id"] for item in trace["records"]}:
        raise CandidateError("fidelity first-order proof coverage is partial")
    _validate_dimensions(model, unit_ids | source_lwrs | obligation_ids | {item["id"] for item in trace["records"]})
    _verdict(model, primary, model["omission_enhancement_weakening_findings"])
    if sealed["task_id"] == context.work_order["task_id"]:
        raise CandidateError("fidelity and consumer task identities are not isolated")


def validate_candidate(context: Context, draft: Path) -> tuple[dict[str, Any],dict[str,Any]]:
    expected = {context.mode_contract["canonical_file"],"review-session.json"}
    if not draft.is_dir() or {path.name for path in draft.iterdir()} != expected:
        raise CandidateError("HQ2 draft file set is not exact")
    model = read_json(draft/context.mode_contract["canonical_file"]);session=read_json(draft/"review-session.json")
    context.catalog.validate(model,context.mode_contract["canonical_schema"])
    identity=(SKILL,STAGE,context.mode,context.work_order["hld_run_id"],context.work_order["task_id"])
    if (model["skill"],model["stage"],model["mode"],model["hld_run_id"],model["task_id"])!=identity:
        raise CandidateError("HQ2 canonical identity differs from work-order")
    _validate_session(context,model,session);_validate_evidence(context,model)
    if context.mode=="consumer_test":_validate_consumer(context,model)
    else:_validate_fidelity(context,model)
    return model,session


def _future_ref(path:Path,staging:Path,context:Context,role:str)->dict[str,str]:
    target=context.output/path.relative_to(staging)
    return {"role":role,"path":target.relative_to(context.workspace).as_posix(),"sha256":sha256_file(path)}


def _manifest(staging:Path,context:Context,status:str,name:str,roles:Mapping[str,str])->dict[str,Any]:
    files=[];by_role={}
    for path in sorted((p for p in staging.rglob("*") if p.is_file() and p.name!=name),key=lambda p:p.relative_to(staging).as_posix()):
        relative=path.relative_to(staging).as_posix();role=roles[relative];ref=file_ref(path,root=staging,role=role);files.append(ref);by_role[role]=ref
    return {"schema_version":"1.0","harness":HARNESS,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"stage":STAGE,"skill":SKILL,"status":status,"files":files,"artifact_roles":by_role}


def _result(context:Context,outcome:str,staging:Path,manifest:Path,validation:Path)->dict[str,Any]:
    return {"schema_version":"1.0","harness":HARNESS,"hld_run_id":context.work_order["hld_run_id"],"revision":context.work_order["revision"],"stage":STAGE,"skill":SKILL,"work_order_id":context.work_order["work_order_id"],"task_id":context.work_order["task_id"],"event_sequence":context.work_order["event_sequence"],"result_scope":"composite_internal","result":outcome,"state_before_ref":context.work_order["state_before_ref"],"input_gate_ref":context.work_order["input_gate_ref"],"result_manifest_ref":_future_ref(manifest,staging,context,"package_manifest" if outcome=="ready" else "result_manifest"),"validation_ref":_future_ref(validation,staging,context,"validation"),"produced_at":context.work_order["result_timestamp"],"completion_ref":None,"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":None,"blocked_report_ref":None,"blocker_class":None,"affected_ids":[],"runtime_error_ref":None}


def build_ready(context:Context,model:dict[str,Any],session:dict[str,Any],staging:Path)->tuple[int,dict[str,Any]]:
    staging.mkdir(parents=True,exist_ok=False);name=context.mode_contract["canonical_file"];write_json(staging/name,model);write_json(staging/"review-session.json",session)
    execution={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"mode":context.mode,"hld_run_id":context.work_order["hld_run_id"],"task_id":context.work_order["task_id"],"work_order_id":context.work_order["work_order_id"],"status":"ready","implementation_sha256":context.work_order["implementation_sha256"],"input_gate_ref":context.work_order["input_gate_ref"],"actual_read_refs":session["actual_read_refs"],"canonical_sha256":sha256_file(staging/name),"errors":[]}
    validation={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"mode":context.mode,"hld_run_id":context.work_order["hld_run_id"],"status":"pass","checks":list(CHECKS),"errors":[],"semantic_verdict":"pass"}
    context.catalog.validate(execution,"hq2-execution.schema.json");context.catalog.validate(validation,"hq2-validation.schema.json")
    write_json(staging/context.mode_contract["execution_file"],execution);write_json(staging/"validation.json",validation)
    roles={name:"handoff_consumption_test" if context.mode=="consumer_test" else "handoff_fidelity_test","review-session.json":"review_session",context.mode_contract["execution_file"]:"execution_record","validation.json":"validation"}
    manifest=_manifest(staging,context,"ready","package-manifest.json",roles);context.catalog.validate(manifest,"package-manifest.schema.json");write_json(staging/"package-manifest.json",manifest)
    validate_manifest(staging,manifest);validate_ready_profile(staging,f"HQ2.{context.mode}")
    result=_result(context,"ready",staging,staging/"package-manifest.json",staging/"validation.json");result["internal_manifest_ref"]=_future_ref(staging/"package-manifest.json",staging,context,"internal_manifest")
    context.catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,context.work_order);return 0,result


def build_revise(context:Context,candidate:Any,errors:list[str],staging:Path)->tuple[int,dict[str,Any]]:
    staging.mkdir(parents=True,exist_ok=False);affected=[]
    envelope={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"mode":context.mode,"hld_run_id":context.work_order["hld_run_id"],"task_id":context.work_order["task_id"],"candidate":candidate,"errors":errors}
    report={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"hld_run_id":context.work_order["hld_run_id"],"status":"revise","revision_class":"local_candidate","code":"HQ2_LOCAL_CANDIDATE_DEFECT","evidence":"; ".join(errors),"affected_ids":affected,"required_action":"regenerate this isolated HQ2 candidate without changing upstream HLD"}
    evidence={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"hld_run_id":context.work_order["hld_run_id"],"code":"HQ2_LOCAL_CANDIDATE_DEFECT","evidence":"; ".join(errors),"affected_ids":affected}
    validation={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"mode":context.mode,"hld_run_id":context.work_order["hld_run_id"],"status":"revise","checks":list(CHECKS),"errors":errors,"semantic_verdict":"revise"}
    for value,schema in ((envelope,"hq2-candidate.schema.json"),(report,"composite-internal-revision-report.schema.json"),(evidence,"hq2-local-defect-evidence.schema.json"),(validation,"hq2-validation.schema.json")):context.catalog.validate(value,schema)
    write_json(staging/"candidate.json",envelope);write_json(staging/"revision-report.json",report);write_json(staging/"local-defect-evidence.json",evidence);write_json(staging/"validation.json",validation)
    roles={"candidate.json":"candidate","revision-report.json":"revision_report","local-defect-evidence.json":"local_defect_evidence","validation.json":"validation"};manifest=_manifest(staging,context,"revise","result-manifest.json",roles);write_json(staging/"result-manifest.json",manifest);context.catalog.validate(manifest,"package-manifest.schema.json");validate_manifest(staging,manifest)
    result=_result(context,"revise",staging,staging/"result-manifest.json",staging/"validation.json");result.update({"revision_class":"local_candidate","revision_report_ref":_future_ref(staging/"revision-report.json",staging,context,"revision_report"),"candidate_ref":_future_ref(staging/"candidate.json",staging,context,"candidate"),"local_defect_evidence":[_future_ref(staging/"local-defect-evidence.json",staging,context,"local_defect_evidence")]})
    context.catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,context.work_order);return 2,result


def build_blocked(context:Context,blocked:SemanticBlocked,staging:Path)->tuple[int,dict[str,Any]]:
    staging.mkdir(parents=True,exist_ok=False);code={"upstream_defect":"HQ2_UPSTREAM_DEFECT","author_required":"HQ2_AUTHOR_REQUIRED","reality_dependency":"HQ2_REALITY_DEPENDENCY"}[blocked.blocker_class]
    gate={"schema_version":"1.0","hld_run_id":context.work_order["hld_run_id"],"stage":STAGE,"failed_gate":code,"evidence":blocked.evidence,"affected_ids":blocked.affected_ids}
    report={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"hld_run_id":context.work_order["hld_run_id"],"status":"blocked","blocker_class":blocked.blocker_class,"code":code,"evidence":blocked.evidence,"affected_ids":blocked.affected_ids,"required_action":"resolve the cited upstream, author, or reality dependency; HQ2 must not invent replacement content"}
    validation={"schema_version":"1.0","skill":SKILL,"stage":STAGE,"mode":context.mode,"hld_run_id":context.work_order["hld_run_id"],"status":"blocked","checks":list(CHECKS),"errors":[blocked.evidence],"semantic_verdict":"fail"}
    context.catalog.validate(gate,"composite-internal-gate-data.schema.json");context.catalog.validate(report,"composite-internal-blocked-report.schema.json");context.catalog.validate(validation,"hq2-validation.schema.json")
    write_json(staging/"gate-data.json",gate);write_json(staging/"blocked-report.json",report);write_json(staging/"validation.json",validation)
    roles={"gate-data.json":"gate_data","blocked-report.json":"blocked_report","validation.json":"validation"};manifest=_manifest(staging,context,"blocked","result-manifest.json",roles);write_json(staging/"result-manifest.json",manifest);context.catalog.validate(manifest,"package-manifest.schema.json");validate_manifest(staging,manifest)
    result=_result(context,"blocked",staging,staging/"result-manifest.json",staging/"validation.json");result.update({"gate_data_ref":_future_ref(staging/"gate-data.json",staging,context,"gate_data"),"blocked_report_ref":_future_ref(staging/"blocked-report.json",staging,context,"blocked_report"),"blocker_class":blocked.blocker_class,"affected_ids":blocked.affected_ids})
    context.catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,context.work_order);return 2,result


def _tree(root:Path)->dict[str,bytes]:return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _atomic(context:Context,builder)->int:
    temp=Path(tempfile.mkdtemp(prefix=f".hq2-{context.mode}-",dir=context.workspace));first=temp/"first";second=temp/"second"
    try:
        code,result=builder(first);code2,result2=builder(second)
        if code!=code2 or canonical_bytes(result)!=canonical_bytes(result2) or _tree(first)!=_tree(second):raise ContractError("HQ2 deterministic reproduction mismatch")
        context.output.parent.mkdir(parents=True,exist_ok=True);os.replace(first,context.output);write_json(context.result_path,result)
        try:
            manifest_name="package-manifest.json" if result["result"]=="ready" else "result-manifest.json";manifest=read_json(context.output/manifest_name);validate_manifest(context.output,manifest);validate_result_envelope(read_json(context.result_path),context.work_order)
        except Exception:
            shutil.rmtree(context.output,ignore_errors=True);context.result_path.unlink(missing_ok=True);raise
        return code
    finally:shutil.rmtree(temp,ignore_errors=True)


def execute(skill_root:Path,work_order_path:Path,draft:Path)->int:
    try:context=load_context(skill_root,work_order_path)
    except (OSError,ValueError,ContractError) as error:print(f"HQ2 input gate failed: {error}",file=sys.stderr);return 3
    try:model,session=validate_candidate(context,draft.resolve(strict=True))
    except SemanticBlocked as blocked:return _atomic(context,lambda staging:build_blocked(context,blocked,staging))
    except (OSError,ValueError,ContractError) as error:
        candidate=None
        try:candidate=read_json(draft/context.mode_contract["canonical_file"])
        except Exception:candidate={"unavailable":True}
        return _atomic(context,lambda staging:build_revise(context,candidate,[str(error)],staging))
    if model["verdict"] == "revise":
        return _atomic(context,lambda staging:build_revise(context,model,["canonical verdict requests reviewer-local revision"],staging))
    return _atomic(context,lambda staging:build_ready(context,model,session,staging))
