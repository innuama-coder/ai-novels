#!/usr/bin/env python3
"""Persisted single-writer control plane for the HLD Harness.

The coordinator owns issuance, result admission, state transitions, composite
ordering and author/revision transactions.  It never executes a bounded skill
and never interprets story content.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from .author_gate import resolve_author_answer, revision_retarget_question, source_resolution_question
from .canonical import ContractError, canonical_bytes, canonical_sha256, read_json, resolve_inside, verify_file_ref
from .composite_publisher import PUBLISHER, TASK_CONTRACT, TASK_ORDER
from .contracts import HARNESS, READY_PACKAGE_PROFILES, SKILLS, STAGES, UPSTREAM, next_stage, owner_for_id
from .package_envelope import validate_completion_bindings, validate_manifest, validate_ready_profile, validate_result_envelope
from .revision import build_revision_plan, initial_plan_state, transition_plan_state
from .schema_catalog import SchemaCatalog
from .state import initial_state
from .owner_registry import resolve_public_owner

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
COMPOSITES = {"HQ2", "HH1"}
PRIMARY_ROLE = {
    "HB0":"control_baseline","HA1":"narrative_architecture","HS1":"storyline_choreography",
    "HC1":"character_arc_placement","HI1":"narrative_information_architecture",
    "HR1":"rhythm_continuity_architecture","HK1":"key_scene_function_map","HQ1":"semantic_review",
    "HP1":"novel_hld_package","HQ2":"lld_handoff_acceptance","HH1":"human_review_report","HF1":"hld_completion",
}
PRIMARY_FILE = {
    "HB0":"hld-control-baseline.json","HA1":"narrative-architecture.json","HS1":"storyline-choreography.json",
    "HC1":"character-arc-placement.json","HI1":"narrative-information-architecture.json",
    "HR1":"rhythm-continuity-architecture.json","HK1":"key-scene-function-map.json","HQ1":"hld-semantic-review.json",
    "HP1":"novel-hld-package.json","HQ2":"lld-handoff-acceptance.json","HH1":"hld-human-review-report.json","HF1":"hld-completion.json",
}


class CoordinatorFailure(RuntimeError):
    pass


def _catalog() -> SchemaCatalog:
    return SchemaCatalog(ROOT / "schemas")


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ref(path: Path, workspace: Path, role: str) -> dict[str, str]:
    path=path.resolve(strict=True);return {"role":role,"path":path.relative_to(workspace.resolve(strict=True)).as_posix(),"sha256":_hash(path)}


def _stage_asset(workspace: Path, source: Path) -> Path:
    source=source.resolve(strict=True);digest=_hash(source);target=workspace/"implementation-assets"/digest/source.name
    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if _hash(target)!=digest:raise CoordinatorFailure("staged implementation asset hash drift")
    return target


def _artifact(main: Path, manifest: Path, completion: Path, workspace: Path) -> dict[str, str]:
    return {"path":main.relative_to(workspace).as_posix(),"sha256":_hash(main),"manifest_path":manifest.relative_to(workspace).as_posix(),"manifest_sha256":_hash(manifest),"completion_path":completion.relative_to(workspace).as_posix(),"completion_sha256":_hash(completion)}


def _verify_artifact_reference(workspace:Path,artifact:Mapping[str,Any])->tuple[Path,Path,Path,dict[str,Any],dict[str,Any]]:
    """Re-admit a stored artifactReference at every use boundary."""
    main=verify_file_ref({"role":"primary_artifact","path":artifact["path"],"sha256":artifact["sha256"]},workspace)
    manifest_path=verify_file_ref({"role":"package_manifest","path":artifact["manifest_path"],"sha256":artifact["manifest_sha256"]},workspace)
    completion_path=verify_file_ref({"role":"stage_completion","path":artifact["completion_path"],"sha256":artifact["completion_sha256"]},workspace)
    manifest=read_json(manifest_path);completion=read_json(completion_path);catalog=_catalog()
    catalog.validate(manifest,"package-manifest.schema.json");catalog.validate(completion,"stage-completion.schema.json")
    validate_manifest(manifest_path.parent,manifest);validate_completion_bindings(workspace,manifest_path.parent,completion)
    if verify_file_ref(completion["manifest_ref"],workspace)!=manifest_path:raise CoordinatorFailure("artifactReference completion/manifest binding drift")
    if not any(ref["path"]==main.relative_to(workspace).as_posix() and ref["sha256"]==artifact["sha256"] for ref in completion["canonical_artifacts"]):raise CoordinatorFailure("artifactReference primary is not completion-bound")
    return main,manifest_path,completion_path,manifest,completion


def _snapshot(workspace: Path, ledger: Mapping[str, Any]) -> Path:
    path=workspace/"coordinator"/f"ledger-{ledger['ledger_revision']:04d}.json"
    if path.exists():raise CoordinatorFailure("coordinator ledger revision already exists")
    _catalog().validate(ledger,"coordinator-ledger.schema.json");_write(path,ledger)
    pointer=workspace/"coordinator-current.json";temp=workspace/".coordinator-current.tmp";_write(temp,{"ledger_ref":_ref(path,workspace,"coordinator_ledger")});os.replace(temp,pointer)
    return path


def load_current(workspace: Path) -> tuple[Path,dict[str,Any]]:
    workspace=workspace.resolve(strict=True);pointer=read_json(workspace/"coordinator-current.json");path=verify_file_ref(pointer["ledger_ref"],workspace,expected_role="coordinator_ledger");value=read_json(path);_catalog().validate(value,"coordinator-ledger.schema.json");return path,value


def _owner_binding(stage: str, task_kind: str | None=None) -> tuple[str,str,str]:
    if task_kind in TASK_CONTRACT:
        expected=TASK_CONTRACT[task_kind][1]
    elif task_kind=="publisher":
        expected=PUBLISHER;task_kind="HH1-publisher" if stage=="HH1" else "publisher"
    else:expected=SKILLS[stage]
    return resolve_public_owner(stage,task_kind,expected_skill=expected)


def _gate_and_order(workspace: Path, state_ref: Mapping[str,Any], state: Mapping[str,Any], *, stage: str, timestamp: str, allowlist: list[dict[str,str]], upstreams: list[dict[str,str]], task_kind: str|None=None, mode: str="forward", return_binding: Mapping[str,Any]|None=None, plan_ref: Mapping[str,Any]|None=None, plan_state_ref: Mapping[str,Any]|None=None, composite_state_ref: Mapping[str,Any]|None=None, after_sequence:int|None=None, supplemental_source_refs:Iterable[Mapping[str,Any]]=()) -> tuple[Path,dict[str,Any]]:
    for artifact in upstreams:_verify_artifact_reference(workspace,artifact)
    sequence=max(int(state["event_sequence"]),after_sequence or 0)+1
    if composite_state_ref is not None:
        composite=read_json(verify_file_ref(composite_state_ref,workspace));sequence=max(sequence,int(composite["last_issued_event_sequence"])+1)
    skill,version,implementation=_owner_binding(stage,task_kind)
    token=task_kind or stage;slug=token.replace("_","-")
    binding_ref=None
    if return_binding is not None:
        _catalog().validate(return_binding,"return-binding.schema.json");binding_path=workspace/"return-bindings"/f"binding-{sequence:06d}-{return_binding['group_id']}.json";_write(binding_path,return_binding);binding_ref=_ref(binding_path,workspace,"return_binding")
    gate={"schema_version":"1.0","harness":HARNESS,"hld_run_id":state["hld_run_id"],"stage":stage,"mode":mode,"state_before_ref":dict(state_ref),"hb0_completion_ref":upstreams[0] if upstreams else None,"upstream_completions":upstreams,"baseline_manifest_ref":None,"baseline_validation_ref":None,"source_lineage_refs":[],"exact_owner_skill":skill,"owner_version":version,"implementation_sha256":implementation,"return_binding":binding_ref,"unresolved_projection":[],"revision_plan_ref":dict(plan_ref) if plan_ref else None,"revision_plan_state_ref":dict(plan_state_ref) if plan_state_ref else None,"file_allowlist":allowlist}
    if stage=="HB0":
        by_role={item["role"]:item for item in allowlist}
        gate["baseline_manifest_ref"]=by_role["baseline_manifest"]
        gate["baseline_validation_ref"]=by_role["baseline_validation"]
        gate["source_lineage_refs"]=[item for item in allowlist if item["role"].startswith("source::")]
    if stage in {"HA1","HS1","HC1","HI1","HR1","HK1","HQ1"}:
        hb0=upstreams[0];gate["baseline_manifest_ref"]={"role":"baseline_manifest","path":hb0["manifest_path"],"sha256":hb0["manifest_sha256"]}
        completion=read_json(workspace/hb0["completion_path"]);validation=completion["validation_ref"];gate["baseline_validation_ref"]={"role":"baseline_validation","path":validation["path"],"sha256":validation["sha256"]}
        source_index=next((x for x in completion["canonical_artifacts"] if x["role"]=="source_index"),None)
        if source_index:
            gate["source_lineage_refs"]=[dict(source_index)]
            index=read_json(workspace/source_index["path"])
            for item in index["entries"]:
                if stage in item["allowed_stages"] and item["workspace_source_ref"] not in gate["source_lineage_refs"]:gate["source_lineage_refs"].append(item["workspace_source_ref"])
        for item in supplemental_source_refs:
            if item not in gate["source_lineage_refs"]:gate["source_lineage_refs"].append(dict(item))
        control=read_json(workspace/hb0["path"])
        from .hdd import project_unresolved
        gate["unresolved_projection"]=project_unresolved(control["unresolved_register"]).get(stage,[])
    gate_path=workspace/f"input-gate-{sequence:06d}-{slug}.json";_write(gate_path,gate)
    order={"schema_version":"1.0","harness":HARNESS,"hld_run_id":state["hld_run_id"],"revision":state["revision"],"work_order_id":f"WO-{sequence:06d}-{slug}","task_id":f"TASK-{sequence:06d}-{slug}","stage":stage,"action":"execute","exact_owner_skill":skill,"owner_version":version,"implementation_sha256":implementation,"event_sequence":sequence,"result_timestamp":timestamp,"input_gate_ref":_ref(gate_path,workspace,"input_gate"),"state_before_ref":dict(state_ref),"upstream_completions":upstreams,"file_allowlist":allowlist,"unresolved_projection":gate["unresolved_projection"],"mode":mode,"return_binding":binding_ref,"revision_plan_ref":dict(plan_ref) if plan_ref else None,"revision_plan_state_ref":dict(plan_state_ref) if plan_state_ref else None,"output_directory":f"{stage}-r{state['revision']:04d}-{slug}-package","submission_status":"open"}
    order_path=workspace/f"work-order-{sequence:06d}-{slug}.json";_write(order_path,order);return order_path,order


def initialize_staged(workspace: Path, run_request_path: Path, hb0_allowlist: list[dict[str,str]], timestamp: str) -> Path:
    workspace=workspace.resolve(strict=True);request_path=run_request_path.resolve(strict=True)
    if request_path.parent!=workspace:raise CoordinatorFailure("staged run request must be in workspace root")
    request=read_json(request_path);catalog=_catalog();catalog.validate(request,"hld-run-request.schema.json")
    if (workspace/"coordinator-current.json").exists():raise CoordinatorFailure("coordinator workspace already initialized")
    if len({x["role"] for x in hb0_allowlist})!=len(hb0_allowlist):raise CoordinatorFailure("HB0 bootstrap roles are not unique")
    for item in hb0_allowlist:verify_file_ref(item,workspace)
    state=initial_state(request["hld_run_id"]);state_path=workspace/"states"/"revision-000.json";_write(state_path,state);state_ref=_ref(state_path,workspace,"state_before")
    order,_=_gate_and_order(workspace,state_ref,state,stage="HB0",timestamp=timestamp,allowlist=hb0_allowlist,upstreams=[])
    ledger={"schema_version":"1.0","harness":HARNESS,"hld_run_id":request["hld_run_id"],"ledger_revision":0,"event_sequence":1,"current_state_ref":state_ref,"active_work_order_ref":_ref(order,workspace,"work_order"),"active_task_kind":"HB0","accepted_result_refs":[],"composite_state_ref":None,"consumed_author_event_ids":[],"fingerprint_completion_counts":{},"terminal_status":None}
    return _snapshot(workspace,ledger)


def _accepted_artifacts(workspace: Path, state: Mapping[str,Any]) -> dict[str,dict[str,str]]:
    values={}
    for artifact in state["accepted_completions"]:
        *_,completion=_verify_artifact_reference(workspace,artifact);values[completion["stage"]]=artifact
    return values


def _basic_allowlist(workspace: Path, state_ref: Mapping[str,Any], stage: str, upstreams: list[dict[str,str]], supplemental_source_refs:Iterable[Mapping[str,Any]]=()) -> list[dict[str,str]]:
    roles:dict[str,Path]={}
    if stage=="HF1":
        roles["run_state"]=workspace/state_ref["path"]
        artifacts={name:item for name,item in zip(UPSTREAM[stage],upstreams)}
        for name,item in artifacts.items():
            completion=read_json(workspace/item["completion_path"]);roles[f"validation_{name}"]=workspace/completion["validation_ref"]["path"]
        hp1=artifacts["HP1"];hp1_manifest_path=workspace/hp1["manifest_path"];hp1_manifest=read_json(hp1_manifest_path);hp1_roles=hp1_manifest["artifact_roles"]
        roles.update({"hp1_package":workspace/hp1["path"],"hp1_manifest":hp1_manifest_path,"lld_handoff":hp1_manifest_path.parent/hp1_roles["lld_handoff"]["path"],"hld_cross_index":hp1_manifest_path.parent/hp1_roles["cross_index"]["path"]})
        hq2=artifacts["HQ2"];roles["hq2_acceptance"]=workspace/hq2["path"]
        hh1=artifacts["HH1"];hh1_manifest_path=workspace/hh1["manifest_path"];hh1_manifest=read_json(hh1_manifest_path);roles.update({"hh1_manifest":hh1_manifest_path,"hh1_html":hh1_manifest_path.parent/hh1_manifest["artifact_roles"]["human_review_html"]["path"],"render_target_registry":hh1_manifest_path.parent/hh1_manifest["artifact_roles"]["render_target_registry"]["path"]})
        return [_ref(path,workspace,role) for role,path in sorted(roles.items())]
    if stage in {"HA1","HS1","HC1","HI1","HR1","HK1","HQ1"}:
        hb0=upstreams[0];completion=read_json(workspace/hb0["completion_path"]);baseline_manifest={"role":"baseline_manifest","path":hb0["manifest_path"],"sha256":hb0["manifest_sha256"]};validation=completion["validation_ref"];baseline_validation={"role":"baseline_validation","path":validation["path"],"sha256":validation["sha256"]}
        source_index=next(x for x in completion["canonical_artifacts"] if x["role"]=="source_index");source_refs=[source_index];index=read_json(workspace/source_index["path"])
        for item in index["entries"]:
            if stage in item["allowed_stages"] and item["workspace_source_ref"] not in source_refs:source_refs.append(item["workspace_source_ref"])
        for item in supplemental_source_refs:
            if item not in source_refs:source_refs.append(dict(item))
        from .design_stage_runtime import derive_file_allowlist
        return derive_file_allowlist(workspace,state_ref,baseline_manifest,baseline_validation,source_refs,upstreams,UPSTREAM[stage])
    if stage=="HP1":
        import importlib
        hp1=importlib.import_module("skills.novel-hld-package-assembler.scripts.hp1_runtime")
        for name,artifact in zip(UPSTREAM[stage],upstreams):
            package=workspace/artifact["manifest_path"];manifest=read_json(package);completion=read_json(workspace/artifact["completion_path"]);main=workspace/artifact["path"]
            roles[hp1.MAIN_ROLES[name]]=main;roles[f"{name.lower()}_manifest"]=package;roles[f"{name.lower()}_validation"]=workspace/completion["validation_ref"]["path"];roles[f"{name.lower()}_completion"]=workspace/artifact["completion_path"]
            if name=="HB0":roles["hb0_source_index"]=workspace/next(x for x in completion["canonical_artifacts"] if x["role"]=="source_index")["path"]
        return [_ref(path,workspace,role) for role,path in sorted(roles.items())]
    # Review/final/composite tasks use public role contracts.  Build from
    # current package manifests; no directory search is performed.
    roles["run_state"]=workspace/state_ref["path"]
    for name,artifact in zip(UPSTREAM[stage],upstreams):
        manifest_path=workspace/artifact["manifest_path"];package=manifest_path.parent;manifest=read_json(manifest_path);completion=read_json(workspace/artifact["completion_path"])
        roles[f"validation_{name}"]=workspace/completion["validation_ref"]["path"]
        for role,ref in manifest["artifact_roles"].items():
            if role in {"validation","execution_record","session","generation_evidence"}:continue
            roles.setdefault(role,package/ref["path"])
        if name in {"HP1","HQ2","HH1"}:roles[f"{name.lower()}_manifest"]=manifest_path
    return [_ref(path,workspace,role) for role,path in sorted(roles.items())]


def _archive_result(workspace: Path, result_path: Path, sequence: int, task_kind: str) -> tuple[Path,dict[str,Any]]:
    result=read_json(result_path);target=workspace/"results"/f"result-{sequence:06d}-{task_kind.replace('_','-')}.json";target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_bytes()!=result_path.read_bytes():raise CoordinatorFailure("result archive collision")
        result_path.unlink();return target,result
    os.replace(result_path,target);return target,result


def _preflight_revision_targets(workspace:Path,result_path:Path,work:Mapping[str,Any],result:Mapping[str,Any],targets:list[Mapping[str,Any]],task_kind:str)->None:
    """Validate a non-ready revision plan before the stage result is archived."""
    if result["result"] in {"ready","runtime_error"}:return
    blocker=result.get("blocker_class")
    if result["result"]=="blocked" and blocker in {"author_required","reality_dependency","author_rejected","exhausted"}:return
    if not targets:raise CoordinatorFailure("revision/upstream-defect result requires parsed targets")
    archive=workspace/"results"/f"result-{work['event_sequence']:06d}-{task_kind.replace('_','-')}.json"
    future_ref={"role":"stage_result","path":archive.relative_to(workspace).as_posix(),"sha256":_hash(result_path)}
    try:build_revision_plan(hld_run_id=result["hld_run_id"],source_result_ref=future_ref,targets=targets,source_event_ref=result.get("author_event_ref"))
    except (KeyError,TypeError,ValueError) as error:raise CoordinatorFailure(str(error)) from error


def _admit_result(workspace: Path, ledger: Mapping[str,Any], result_path: Path) -> tuple[dict[str,Any],dict[str,Any],Path,Path]:
    work_path=verify_file_ref(ledger["active_work_order_ref"],workspace,expected_role="work_order");work=read_json(work_path);result=read_json(result_path);catalog=_catalog();catalog.validate(work,"work-order.schema.json");catalog.validate(result,"stage-result.schema.json");validate_result_envelope(result,work)
    expected_scope="composite_internal" if ledger["active_task_kind"] in TASK_CONTRACT else "top_level"
    if result["result_scope"]!=expected_scope:raise CoordinatorFailure("result scope differs from active task")
    manifest_path=verify_file_ref(result["result_manifest_ref"],workspace);validation_path=verify_file_ref(result["validation_ref"],workspace);manifest=read_json(manifest_path);catalog.validate(manifest,"package-manifest.schema.json");validate_manifest(manifest_path.parent,manifest)
    if result["result"]=="ready" and expected_scope=="top_level":
        completion_path=verify_file_ref(result["completion_ref"],workspace);completion=read_json(completion_path)
        if result["stage"]=="HF1":
            schema=json.loads((REPO/"skills"/"novel-hld-finalizer"/"references"/"hld-completion.schema.json").read_text(encoding="utf-8"));schema["$id"]="hld-completion.schema.json";SchemaCatalog.from_documents({"hld-completion.schema.json":schema}).validate(completion,"hld-completion.schema.json")
            if completion["hld_run_id"]!=work["hld_run_id"] or completion["revision"]!=work["revision"] or completion["produced_at"]!=work["result_timestamp"]:raise CoordinatorFailure("HF1 completion identity/timestamp drift")
        else:
            catalog.validate(completion,"stage-completion.schema.json");validate_completion_bindings(workspace,manifest_path.parent,completion)
            if result["stage"] in READY_PACKAGE_PROFILES:validate_ready_profile(manifest_path.parent,result["stage"])
            if completion["upstream_completions"]!=work["upstream_completions"]:raise CoordinatorFailure("completion upstream binding differs from work order")
    state_path=verify_file_ref(work["state_before_ref"],workspace);current_path=verify_file_ref(ledger["current_state_ref"],workspace)
    if state_path!=current_path:raise CoordinatorFailure("stale result state-before")
    return work,result,manifest_path,validation_path


def _stage_artifact(workspace: Path, result: Mapping[str,Any]) -> dict[str,str]:
    completion_path=verify_file_ref(result["completion_ref"],workspace);completion=read_json(completion_path);main=next((x for x in completion["canonical_artifacts"] if x["role"]==PRIMARY_ROLE[result["stage"]]),None)
    if main is None:raise CoordinatorFailure("completion lacks registered primary canonical role")
    main_path=verify_file_ref(main,workspace);manifest_path=verify_file_ref(completion["manifest_ref"],workspace)
    return _artifact(main_path,manifest_path,completion_path,workspace)


def _next_state(previous: Mapping[str,Any], *, sequence:int,status:str,current_stage:str|None,result_ref:Mapping[str,Any],previous_ref:Mapping[str,Any],accepted:Mapping[str,Any]|None=None,plan_ref:Mapping[str,Any]|None=None,plan_state_ref:Mapping[str,Any]|None=None,waiting:Mapping[str,Any]|None=None,drop_stages:Iterable[str]=()) -> dict[str,Any]:
    dropped=set(drop_stages);completions=[]
    for item in previous["accepted_completions"]:
        # stage is carried by the referenced completion; caller prefilters when needed.
        completions.append(dict(item))
    if dropped:completions=[x for x in completions if x.get("_stage") not in dropped]
    if accepted is not None:completions.append(dict(accepted))
    return {"schema_version":"1.0","harness":HARNESS,"hld_run_id":previous["hld_run_id"],"revision":previous["revision"]+1,"event_sequence":sequence,"status":status,"current_stage":current_stage,"accepted_completions":completions,"current_result_ref":dict(result_ref),"previous_state_ref":dict(previous_ref),"revision_plan_ref":dict(plan_ref) if plan_ref else None,"revision_plan_state_ref":dict(plan_state_ref) if plan_state_ref else None,"waiting_transaction_ref":dict(waiting) if waiting else None}


def _ready_status(stage:str)->str:
    if stage=="HH1":return "waiting_author_decision"
    if stage=="HF1":return "lld_ready"
    return "running"


def _persist_state(workspace:Path,state:Mapping[str,Any])->dict[str,str]:
    _catalog().validate(state,"run-state.schema.json");path=workspace/"states"/f"revision-{state['revision']:03d}.json";_write(path,state);return _ref(path,workspace,"state_before")


def _task_return_context(workspace:Path,state:Mapping[str,Any],task_kind:str)->tuple[str,dict[str,Any]|None,Mapping[str,Any]|None,Mapping[str,Any]|None]:
    if state["status"]!="return_active":return "forward",None,None,None
    plan_ref=state.get("revision_plan_ref");plan_state_ref=state.get("revision_plan_state_ref")
    if not plan_ref or not plan_state_ref:raise CoordinatorFailure("return-active state lacks revision plan bindings")
    plan=read_json(verify_file_ref(plan_ref,workspace));plan_state=read_json(verify_file_ref(plan_state_ref,workspace));active=next(x for x in plan["target_groups"] if x["group_id"]==plan_state["active_group_id"])
    current_index=STAGES.index(state["current_stage"]);target_index=STAGES.index(active["target_stage"])
    # After an earlier revision group resolves, every invalidated intermediate
    # stage must be rebuilt before the next group's exact owner is reached.
    # Those stages are ordinary forward work.  Passing an unresolved owner is
    # still impossible and remains fail-closed.
    if current_index < target_index:return "forward",None,None,None
    if current_index > target_index:raise CoordinatorFailure("active revision target was bypassed")
    # Composite children remain ordinary forward tasks.  The composite
    # publisher alone carries and resolves the immutable revision binding.
    resolves=(task_kind not in TASK_CONTRACT and task_kind==active["exact_owner"]) or task_kind=="publisher"
    if not resolves:return "forward",None,None,None
    binding={"group_id":active["group_id"],"exact_owner":active["exact_owner"],"affected_ids":list(active["affected_ids"]),"completion_condition":active["completion_condition"]}
    return "return_resolution",binding,plan_ref,plan_state_ref


def _issue_forward(workspace:Path,state_ref:Mapping[str,Any],state:Mapping[str,Any],ledger:Mapping[str,Any],timestamp:str,*,supplemental_source_refs:Iterable[Mapping[str,Any]]=())->tuple[Path,str,dict[str,Any]|None]:
    stage=state["current_stage"]
    if stage is None:raise CoordinatorFailure("terminal/waiting state has no issuable stage")
    supplements=[dict(item) for item in supplemental_source_refs]
    if state.get("status")=="return_active" and state.get("revision_plan_ref"):
        plan=read_json(verify_file_ref(state["revision_plan_ref"],workspace))
        source_event=plan.get("source_event_ref")
        if source_event is not None and source_event not in supplements:supplements.append(dict(source_event))
    artifacts=_accepted_artifacts(workspace,state);upstreams=[artifacts[name] for name in UPSTREAM[stage]]
    task_kind=TASK_ORDER[stage][0] if stage in COMPOSITES else None
    if task_kind:
        mode,binding,plan_ref,plan_state_ref=_task_return_context(workspace,state,task_kind)
        allow=_internal_allowlist(workspace,stage,task_kind,upstreams,{})
        order,_=_gate_and_order(workspace,state_ref,state,stage=stage,timestamp=timestamp,allowlist=allow,upstreams=upstreams,task_kind=task_kind,mode=mode,return_binding=binding,plan_ref=plan_ref,plan_state_ref=plan_state_ref)
        composite={"schema_version":"1.0","harness":HARNESS,"hld_run_id":state["hld_run_id"],"revision":state["revision"],"stage":stage,"workspace_id":f"CWS-{stage}-r{state['revision']}","state_before_ref":dict(state_ref),"ordered_task_kinds":list(TASK_ORDER[stage]),"issued_tasks":[],"unissued_task_kinds":list(TASK_ORDER[stage]),"last_issued_event_sequence":read_json(order)["event_sequence"]}
        return order,task_kind,composite
    mode,binding,plan_ref,plan_state_ref=_task_return_context(workspace,state,stage)
    if binding is not None:
        plan_state=read_json(verify_file_ref(plan_state_ref,workspace));retarget=next((x for x in reversed(plan_state["retarget_bindings"]) if x["group_id"]==binding["group_id"]),None)
        if retarget:binding={**binding,"affected_ids":[retarget["new_target_id"]]}
    allow=_basic_allowlist(workspace,state_ref,stage,upstreams,supplements)
    order,_=_gate_and_order(workspace,state_ref,state,stage=stage,timestamp=timestamp,allowlist=allow,upstreams=upstreams,mode=mode,return_binding=binding,plan_ref=plan_ref,plan_state_ref=plan_state_ref,supplemental_source_refs=supplements)
    return order,stage,None


def _internal_allowlist(workspace:Path,stage:str,kind:str,upstreams:list[dict[str,str]],previous:Mapping[str,Any])->list[dict[str,str]]:
    previous={name:_verified_internal_record(workspace,item) for name,item in previous.items()}
    artifacts={name:item for name,item in zip(UPSTREAM[stage],upstreams)};roles:dict[str,Path]={}
    hp1=artifacts["HP1"];hp1_manifest_path=workspace/hp1["manifest_path"];hp1_manifest=read_json(hp1_manifest_path);hp1_completion=read_json(workspace/hp1["completion_path"]);by_role={role:hp1_manifest_path.parent/ref["path"] for role,ref in hp1_manifest["artifact_roles"].items()}
    if kind=="consumer_test":
        hb0_completion=read_json(workspace/artifacts["HB0"]["completion_path"])
        roles={"hb0_completion":workspace/artifacts["HB0"]["completion_path"],"hb0_work_order":workspace/hb0_completion["work_order_ref"]["path"],"hp1_completion":workspace/hp1["completion_path"],"hp1_manifest":hp1_manifest_path,"hp1_work_order":workspace/hp1_completion["work_order_ref"]["path"],"lld_handoff":by_role["lld_handoff"],"lld_handoff_schema":_stage_asset(workspace,REPO/"skills"/"novel-hld-package-assembler"/"references"/"lld-handoff.schema.json")}
    elif kind=="fidelity_test":
        first=previous["consumer_test"];hb0_completion=read_json(workspace/artifacts["HB0"]["completion_path"]);roles={"sealed_consumption_test":first["main"],"sealed_consumption_manifest":first["manifest"],"novel_hld_package":by_role["novel_hld_package"],"canonical_model":hp1_manifest_path.parent/"canonical-models"/"narrative-architecture.json","hld_spec":by_role["hld_spec"],"cross_index":by_role["cross_index"],"traceability":by_role["traceability"],"lld_handoff":by_role["lld_handoff"],"hp1_manifest":hp1_manifest_path,"hp1_validation":workspace/hp1_completion["validation_ref"]["path"],"hp1_completion":workspace/hp1["completion_path"],"hp1_work_order":workspace/hp1_completion["work_order_ref"]["path"],"hb0_completion":workspace/artifacts["HB0"]["completion_path"],"hb0_work_order":workspace/hb0_completion["work_order_ref"]["path"]}
    elif kind=="HH1-A":
        import importlib
        module=importlib.import_module("skills.novel-hld-review-report-assembler.scripts.hh1a_runtime");hq2_completion=read_json(workspace/artifacts["HQ2"]["completion_path"]);hb0_manifest_path=workspace/artifacts["HB0"]["manifest_path"];hb0_manifest=read_json(hb0_manifest_path)
        roles={"hb0_completion":workspace/artifacts["HB0"]["completion_path"],"hb0_manifest":hb0_manifest_path,"hld_control_baseline":hb0_manifest_path.parent/hb0_manifest["artifact_roles"]["control_baseline"]["path"],"hp1_completion":workspace/hp1["completion_path"],"hp1_manifest":workspace/hp1["manifest_path"],"hp1_validation":workspace/hp1_completion["validation_ref"]["path"],"novel_hld_package":by_role["novel_hld_package"],"hld_cross_index":by_role["cross_index"],"hld_traceability_matrix":by_role["traceability"],"hld_spec":by_role["hld_spec"],"hq2_completion":workspace/artifacts["HQ2"]["completion_path"],"hq2_manifest":workspace/artifacts["HQ2"]["manifest_path"],"hq2_validation":workspace/hq2_completion["validation_ref"]["path"],"lld_handoff_acceptance":workspace/artifacts["HQ2"]["path"]}
        roles.update({role:hp1_manifest_path.parent/relative for role,relative in module.MODEL_ROLES.items()})
    elif kind=="HH1-B":
        import importlib
        module=importlib.import_module("skills.novel-hld-review-report-assembler.scripts.hh1a_runtime");first=previous["HH1-A"];a_manifest=read_json(first["manifest"]);hb0_manifest_path=workspace/artifacts["HB0"]["manifest_path"];hb0_manifest=read_json(hb0_manifest_path);roles={"hb0_manifest":hb0_manifest_path,"hld_control_baseline":hb0_manifest_path.parent/hb0_manifest["artifact_roles"]["control_baseline"]["path"],"hp1_completion":workspace/hp1["completion_path"],"hp1_manifest":workspace/hp1["manifest_path"],"novel_hld_package":by_role["novel_hld_package"],"hld_cross_index":by_role["cross_index"],"human_review_report":first["main"],"hh1_a_manifest":first["manifest"],"hh1_a_generation_session":first["manifest"].parent/a_manifest["artifact_roles"]["generation_session"]["path"],"hh1_a_work_order":first["work_order"]}
        roles.update({role:hp1_manifest_path.parent/relative for role,relative in module.MODEL_ROLES.items()})
    else:
        a,b=previous["HH1-A"],previous["HH1-B"];a_manifest=read_json(a["manifest"]);b_manifest=read_json(b["manifest"]);hq2_completion=read_json(workspace/artifacts["HQ2"]["completion_path"])
        roles={"hb0_completion":workspace/artifacts["HB0"]["completion_path"],"hp1_completion":workspace/hp1["completion_path"],"hp1_manifest":workspace/hp1["manifest_path"],"novel_hld_package":by_role["novel_hld_package"],"hq2_completion":workspace/artifacts["HQ2"]["completion_path"],"hq2_manifest":workspace/artifacts["HQ2"]["manifest_path"],"lld_handoff_acceptance":workspace/artifacts["HQ2"]["path"],"human_review_report":a["main"],"hh1_a_manifest":a["manifest"],"hh1_a_generation_session":a["manifest"].parent/a_manifest["artifact_roles"]["generation_session"]["path"],"hh1_a_work_order":a["work_order"],"presentation_fidelity_review":b["main"],"hh1_b_manifest":b["manifest"],"hh1_b_review_session":b["manifest"].parent/b_manifest["artifact_roles"]["review_session"]["path"],"hh1_b_work_order":b["work_order"]}
    if kind in {"HH1-A","HH1-B","HH1-C"}:
        skill=TASK_CONTRACT[kind][1];contract=read_json(REPO/"skills"/skill/"references"/"runtime-contract.json");ordered=contract.get("required_allowlist_roles_ordered",contract.get("required_roles"))
        if not isinstance(ordered,list):raise CoordinatorFailure(f"{kind} runtime-contract lacks an ordered allowlist")
        if set(ordered)!=set(roles) or len(ordered)!=len(roles):raise CoordinatorFailure(f"{kind} runtime-contract allowlist topology differs from coordinator derivation")
        return [_ref(roles[role],workspace,role) for role in ordered]
    return [_ref(path,workspace,role) for role,path in sorted(roles.items())]


def _verified_internal_record(workspace:Path,item:Mapping[str,Any],*,require_ready:bool=True)->dict[str,Any]:
    result_path=verify_file_ref(item["stage_result_ref"],workspace,expected_role="stage_result");result=read_json(result_path)
    manifest_path=verify_file_ref(item["package_manifest_ref"],workspace,expected_role="package_manifest");manifest=read_json(manifest_path)
    work_path=verify_file_ref(item["work_order_ref"],workspace,expected_role="work_order");work=read_json(work_path);catalog=_catalog()
    catalog.validate(result,"stage-result.schema.json");catalog.validate(manifest,"package-manifest.schema.json");catalog.validate(work,"work-order.schema.json")
    validate_result_envelope(result,work);validate_manifest(manifest_path.parent,manifest)
    if result["stage"]!=work["stage"] or (require_ready and result["result"]!="ready"):raise CoordinatorFailure("accepted internal record identity/result drift")
    if work["exact_owner_skill"]!=TASK_CONTRACT[item["task_kind"]][1]:raise CoordinatorFailure("accepted internal owner drift")
    if result["result_manifest_ref"]["path"]!=item["package_manifest_ref"]["path"] or result["result_manifest_ref"]["sha256"]!=item["package_manifest_ref"]["sha256"]:raise CoordinatorFailure("accepted internal result/manifest binding drift")
    main=None
    if result["result"]=="ready":
        role=TASK_CONTRACT[item["task_kind"]][3][0][0];main=verify_file_ref(manifest["artifact_roles"][role],manifest_path.parent)
    return {"main":main,"manifest":manifest_path,"work_order":work_path,"result":result_path,"outcome":result["result"]}


def accept_result(workspace:Path,result_path:Path,timestamp:str,revision_targets:Iterable[Mapping[str,Any]]=())->Path:
    workspace=workspace.resolve(strict=True);ledger_path,ledger=load_current(workspace)
    if ledger["active_work_order_ref"] is None:raise CoordinatorFailure("no active work order")
    work,result,_,_=_admit_result(workspace,ledger,result_path.resolve(strict=True));task=ledger["active_task_kind"]
    targets=list(revision_targets)
    blocker=result.get("blocker_class")
    terminal_blocker=blocker in {"reality_dependency","author_rejected","exhausted"}
    routes_without_targets=result["result"] in {"ready","runtime_error"} or (result["result"]=="blocked" and (blocker=="author_required" or terminal_blocker))
    if task not in TASK_CONTRACT and not routes_without_targets and not targets:
        raise CoordinatorFailure("revision/upstream-defect result requires parsed targets")
    if task not in TASK_CONTRACT:_preflight_revision_targets(workspace,result_path,work,result,targets,task)
    if task in TASK_CONTRACT:
        composite=read_json(verify_file_ref(ledger["composite_state_ref"],workspace,expected_role="composite_workspace_state"))
        for item in composite["issued_tasks"]:_verified_internal_record(workspace,item,require_ready=False)
        state=read_json(verify_file_ref(ledger["current_state_ref"],workspace));_accepted_artifacts(workspace,state)
    archive,result=_archive_result(workspace,result_path,work["event_sequence"],task);result_ref=_ref(archive,workspace,"stage_result")
    state_path=verify_file_ref(ledger["current_state_ref"],workspace);state=read_json(state_path);accepted=list(ledger["accepted_result_refs"])+[result_ref]
    if task in TASK_CONTRACT:
        next_ledger=_accept_internal(workspace,ledger,state_path,state,work,result,result_ref,accepted,timestamp)
        return _snapshot(workspace,next_ledger)
    if result["result"]=="ready":
        artifact=None if result["stage"]=="HF1" else _stage_artifact(workspace,result);destination=next_stage(result["stage"])
        status=_ready_status(result["stage"])
        if result["stage"] in {"HH1","HF1"}:destination=None
        plan_ref=state.get("revision_plan_ref");plan_state_ref=state.get("revision_plan_state_ref");counts=dict(ledger["fingerprint_completion_counts"])
        if state["status"]=="return_active":
            if not plan_ref or not plan_state_ref:raise CoordinatorFailure("return-active state lacks revision plan bindings")
            plan=read_json(verify_file_ref(plan_ref,workspace));plan_state=read_json(verify_file_ref(plan_state_ref,workspace));active=next(x for x in plan["target_groups"] if x["group_id"]==plan_state["active_group_id"])
            if work["mode"]=="return_resolution":
                binding=read_json(verify_file_ref(work["return_binding"],workspace,expected_role="return_binding")) if work.get("return_binding") else {}
                expected_ids=binding.get("affected_ids")
                if binding.get("group_id")!=active["group_id"] or not expected_ids:raise CoordinatorFailure("ready return result lacks current group binding")
                transitioned=transition_plan_state(plan_state,plan_group_ids=[x["group_id"] for x in plan["target_groups"]],previous_state_ref=plan_state_ref,transition_event_ref=result_ref,resolved_group_id=active["group_id"])
                ps_path=workspace/"revision-plan-state"/f"{plan['revision_plan_id']}-revision-{state['revision']+1:03d}.json";_catalog().validate(transitioned,"revision-plan-state.schema.json");_write(ps_path,transitioned);plan_state_ref=_ref(ps_path,workspace,"revision_plan_state")
                fingerprint=active.get("root_cause_fingerprint")
                if fingerprint:counts[fingerprint]=counts.get(fingerprint,0)+1
                if transitioned["plan_status"]=="resolved":plan_ref=None;plan_state_ref=None;status=_ready_status(result["stage"])
                else:status="return_active"
            else:status="return_active"
        new_state=_next_state(state,sequence=work["event_sequence"],status=status,current_stage=destination,result_ref=result_ref,previous_ref=ledger["current_state_ref"],accepted=artifact,plan_ref=plan_ref,plan_state_ref=plan_state_ref)
        state_ref=_persist_state(workspace,new_state);active=None;active_kind=None;composite=None;terminal="lld_ready" if status=="lld_ready" else None;event=work["event_sequence"]
        if destination is not None:
            order,active_kind,composite_doc=_issue_forward(workspace,state_ref,new_state,ledger,timestamp);active=_ref(order,workspace,"work_order");event=read_json(order)["event_sequence"]
            if composite_doc is not None:
                cpath=workspace/"composite"/f"{destination}-r{new_state['revision']:03d}-state-000.json";_write(cpath,composite_doc);composite=_ref(cpath,workspace,"composite_workspace_state")
        next_ledger={**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":event,"current_state_ref":state_ref,"active_work_order_ref":active,"active_task_kind":active_kind,"accepted_result_refs":accepted,"composite_state_ref":composite,"terminal_status":terminal,"fingerprint_completion_counts":counts}
    elif result["result"]=="runtime_error":
        new_state=_next_state(state,sequence=work["event_sequence"],status="runtime_stopped",current_stage=result["stage"],result_ref=result_ref,previous_ref=ledger["current_state_ref"]);state_ref=_persist_state(workspace,new_state);next_ledger={**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":work["event_sequence"],"current_state_ref":state_ref,"active_work_order_ref":None,"active_task_kind":None,"accepted_result_refs":accepted,"terminal_status":"runtime_stopped"}
    else:
        next_ledger=_route_nonready(workspace,ledger,state,result,result_ref,accepted,targets,work["event_sequence"],timestamp)
    return _snapshot(workspace,next_ledger)


def _accept_internal(workspace:Path,ledger:Mapping[str,Any],state_path:Path,state:Mapping[str,Any],work:Mapping[str,Any],result:Mapping[str,Any],result_ref:Mapping[str,Any],accepted:list[dict[str,str]],timestamp:str)->dict[str,Any]:
    cpath=verify_file_ref(ledger["composite_state_ref"],workspace);composite=read_json(cpath);kind=ledger["active_task_kind"]
    manifest=verify_file_ref(result["result_manifest_ref"],workspace);main=None
    if result["result"]=="ready":
        manifest_doc=read_json(manifest);role=TASK_CONTRACT[kind][3][0][0];main=verify_file_ref(manifest_doc["artifact_roles"][role],manifest.parent)
    record={"task_kind":kind,"sequence":work["event_sequence"],"work_order_ref":dict(ledger["active_work_order_ref"]),"stage_result_ref":dict(result_ref),"package_manifest_ref":_ref(manifest,workspace,"package_manifest")}
    issued=composite["issued_tasks"]+[record];order=list(TASK_ORDER[result["stage"]]);remaining=order[len(issued):]
    previous={}
    for item in issued:
        try:
            _verified_internal_record(workspace,item)
            previous[item["task_kind"]]=item
        except CoordinatorFailure:
            if item is issued[-1] and result["result"]!="ready":continue
            raise
    publish=result["result"]!="ready" or not remaining
    cdoc={**composite,"issued_tasks":issued,"unissued_task_kinds":remaining,"last_issued_event_sequence":work["event_sequence"]}
    cnext=workspace/"composite"/f"{result['stage']}-r{state['revision']:03d}-state-{len(issued):03d}.json";_write(cnext,cdoc);cref=_ref(cnext,workspace,"composite_workspace_state")
    upstreams=[_accepted_artifacts(workspace,state)[name] for name in UPSTREAM[result["stage"]]]
    if publish:
        allow=_publisher_allowlist(workspace,result["stage"],upstreams,cdoc,cref)
        mode,binding,plan_ref,plan_state_ref=_task_return_context(workspace,state,"publisher")
        order_path,_=_gate_and_order(workspace,ledger["current_state_ref"],state,stage=result["stage"],timestamp=timestamp,allowlist=allow,upstreams=upstreams,task_kind="publisher",composite_state_ref=cref,mode=mode,return_binding=binding,plan_ref=plan_ref,plan_state_ref=plan_state_ref)
        active_kind="publisher"
    else:
        next_kind=remaining[0];allow=_internal_allowlist(workspace,result["stage"],next_kind,upstreams,previous);mode,binding,plan_ref,plan_state_ref=_task_return_context(workspace,state,next_kind);order_path,_=_gate_and_order(workspace,ledger["current_state_ref"],state,stage=result["stage"],timestamp=timestamp,allowlist=allow,upstreams=upstreams,task_kind=next_kind,composite_state_ref=cref,mode=mode,return_binding=binding,plan_ref=plan_ref,plan_state_ref=plan_state_ref);active_kind=next_kind
    return {**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":read_json(order_path)["event_sequence"],"active_work_order_ref":_ref(order_path,workspace,"work_order"),"active_task_kind":active_kind,"accepted_result_refs":accepted,"composite_state_ref":cref}


def _publisher_allowlist(workspace:Path,stage:str,upstreams:list[dict[str,str]],state:Mapping[str,Any],state_ref:Mapping[str,Any])->list[dict[str,str]]:
    roles={"composite_workspace_state":verify_file_ref(state_ref,workspace,expected_role="composite_workspace_state")}
    for name,artifact in zip(UPSTREAM[stage],upstreams):
        main,manifest_path,completion_path,manifest,_=_verify_artifact_reference(workspace,artifact);prefix=f"upstream::{name}";package=manifest_path.parent;reverse={ref["path"]:role for role,ref in manifest["artifact_roles"].items()}
        roles[f"{prefix}::completion"]=completion_path;roles[f"{prefix}::manifest"]=manifest_path;roles[f"{prefix}::canonical::{PRIMARY_ROLE[name]}"]=main
        for item in manifest["files"]:
            path=package/item["path"]
            if path==main:continue
            role=f"{prefix}::validation" if item["path"]=="validation.json" else f"{prefix}::member::{reverse[item['path']]}";roles[role]=path
    for item in state["issued_tasks"]:
        kind=item["task_kind"];prefix=f"internal::{kind}";verified=_verified_internal_record(workspace,item,require_ready=False);work_path=verified["work_order"];work=read_json(work_path);manifest_path=verified["manifest"];manifest=read_json(manifest_path);package=manifest_path.parent;reverse={ref["path"]:role for role,ref in manifest["artifact_roles"].items()}
        roles[f"{prefix}::work_order"]=work_path;roles[f"{prefix}::stage_result"]=verified["result"];roles[f"{prefix}::package_manifest"]=manifest_path;roles[f"{prefix}::input_gate"]=verify_file_ref(work["input_gate_ref"],workspace)
        for ref in work["file_allowlist"]:roles[f"{prefix}::task_input::{ref['role']}"]=verify_file_ref(ref,workspace)
        for ref in manifest["files"]:roles[f"{prefix}::member::{reverse[ref['path']]}"]=package/ref["path"]
    return [_ref(path,workspace,role) for role,path in sorted(roles.items())]


def _route_nonready(workspace:Path,ledger:Mapping[str,Any],state:Mapping[str,Any],result:Mapping[str,Any],result_ref:Mapping[str,Any],accepted:list[dict[str,str]],targets:list[Mapping[str,Any]],sequence:int,timestamp:str)->dict[str,Any]:
    outcome=result["result"];blocker=result.get("blocker_class")
    terminal={"reality_dependency":"reality_reentry","author_rejected":"author_rejected","exhausted":"exhausted"}.get(blocker)
    if outcome=="blocked" and blocker=="author_required":
        gate=read_json(workspace/result["gate_data_ref"]["path"]);source=gate.get("source_control_id") or gate.get("source_id");hdd=gate.get("hdd_ref") or result["gate_data_ref"]
        question=source_resolution_question(hld_run_id=result["hld_run_id"],revision=state["revision"]+1,owner_stage=result["stage"],source_control_id=source,hdd_ref=hdd,affected_ids=result["affected_ids"],question_text=gate.get("question_text","Resolve the named HLD source dependency."));qpath=workspace/"author-transactions"/f"question-{sequence:06d}.json";_write(qpath,question);qref=_ref(qpath,workspace,"author_question")
        _catalog().validate(question,"author-question.schema.json")
        new=_next_state(state,sequence=sequence,status="waiting_author_answer",current_stage=None,result_ref=result_ref,previous_ref=ledger["current_state_ref"],plan_ref=state.get("revision_plan_ref"),plan_state_ref=state.get("revision_plan_state_ref"),waiting=qref);sref=_persist_state(workspace,new);return {**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":sequence,"current_state_ref":sref,"active_work_order_ref":None,"active_task_kind":None,"accepted_result_refs":accepted}
    if terminal:
        waiting=None
        if blocker=="reality_dependency":
            gate=read_json(verify_file_ref(result["gate_data_ref"],workspace));affected=result.get("affected_ids") or gate.get("affected_ids") or ["HLD-EXTERNAL-FACT"]
            request={"schema_version":"1.0","hld_run_id":result["hld_run_id"],"source_result_ref":dict(result_ref),"claim":gate.get("claim") or gate.get("question_text") or "Verify the external fact required by this HLD decision.","why_external_fact":gate.get("why_external_fact") or "The claim cannot be established from the sealed conception inputs.","affected_ids":list(dict.fromkeys(affected)),"required_evidence_depth":gate.get("required_evidence_depth") or "Enough primary-source evidence to classify the claim and cite its validity window.","research_owner":"conception-fact-research","return_condition":gate.get("return_condition") or "A sealed evidence package resolves or withdraws the claim."}
            _catalog().validate(request,"reality-dependency-request.schema.json");rpath=workspace/"reality-transactions"/f"request-{sequence:06d}.json";_write(rpath,request);waiting=_ref(rpath,workspace,"reality_dependency_request")
        new=_next_state(state,sequence=sequence,status=terminal,current_stage=None,result_ref=result_ref,previous_ref=ledger["current_state_ref"],waiting=waiting);sref=_persist_state(workspace,new);return {**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":sequence,"current_state_ref":sref,"active_work_order_ref":None,"active_task_kind":None,"accepted_result_refs":accepted,"terminal_status":terminal}
    if outcome=="runtime_error":raise CoordinatorFailure("runtime error handled before result routing")
    if not targets:raise CoordinatorFailure("revision/upstream-defect result requires parsed targets")
    plan=build_revision_plan(hld_run_id=result["hld_run_id"],source_result_ref=result_ref,targets=targets,source_event_ref=result.get("author_event_ref"));counts=dict(ledger["fingerprint_completion_counts"])
    if any(counts.get(fp,0)>=2 for fp in plan["root_cause_fingerprints"]):
        new=_next_state(state,sequence=sequence,status="exhausted",current_stage=None,result_ref=result_ref,previous_ref=ledger["current_state_ref"]);sref=_persist_state(workspace,new);return {**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":sequence,"current_state_ref":sref,"active_work_order_ref":None,"active_task_kind":None,"accepted_result_refs":accepted,"terminal_status":"exhausted"}
    ppath=workspace/"revision-plans"/f"{plan['revision_plan_id']}.json";_write(ppath,plan);pref=_ref(ppath,workspace,"revision_plan");ps=initial_plan_state(plan,plan_ref=pref,transition_event_ref=result_ref);pspath=workspace/"revision-plan-state"/f"{plan['revision_plan_id']}-revision-000.json";_write(pspath,ps);psref=_ref(pspath,workspace,"revision_plan_state")
    active=plan["target_groups"][0];invalid=set(plan["invalidated_suffix"]);current=[]
    for artifact in state["accepted_completions"]:
        stage=read_json(workspace/artifact["completion_path"])["stage"]
        if stage not in invalid:current.append(artifact)
    new={**_next_state(state,sequence=sequence,status="return_active",current_stage=active["target_stage"],result_ref=result_ref,previous_ref=ledger["current_state_ref"],plan_ref=pref,plan_state_ref=psref),"accepted_completions":current};sref=_persist_state(workspace,new);order,active_kind,composite_doc=_issue_forward(workspace,sref,new,ledger,timestamp);composite_ref=None
    if composite_doc is not None:
        cpath=workspace/"composite"/f"{active['target_stage']}-r{new['revision']:03d}-state-000.json";_write(cpath,composite_doc);composite_ref=_ref(cpath,workspace,"composite_workspace_state")
    return {**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":read_json(order)["event_sequence"],"current_state_ref":sref,"active_work_order_ref":_ref(order,workspace,"work_order"),"active_task_kind":active_kind,"accepted_result_refs":accepted,"composite_state_ref":composite_ref}


def accept_author_decision(workspace:Path,decision_path:Path,timestamp:str)->Path:
    workspace=workspace.resolve(strict=True);_,ledger=load_current(workspace);state=read_json(verify_file_ref(ledger["current_state_ref"],workspace))
    if state["status"]!="waiting_author_decision" or ledger["active_work_order_ref"] is not None:raise CoordinatorFailure("author decision gate is not active")
    schema=json.loads((REPO/"skills"/"novel-hld-finalizer"/"references"/"author-decision.schema.json").read_text(encoding="utf-8"));schema["$id"]="author-decision.schema.json";decision=read_json(decision_path);SchemaCatalog.from_documents({"author-decision.schema.json":schema}).validate(decision,"author-decision.schema.json")
    if decision["hld_run_id"]!=state["hld_run_id"] or decision["revision"]!=state["revision"] or decision["event_sequence"]<=ledger["event_sequence"] or decision["event_id"] in ledger["consumed_author_event_ids"]:raise CoordinatorFailure("author decision is stale or consumed")
    artifacts=_accepted_artifacts(workspace,state);hp1,hq2,hh1=artifacts["HP1"],artifacts["HQ2"],artifacts["HH1"];hh1_manifest=workspace/hh1["manifest_path"];hh1_doc=read_json(hh1_manifest);html=verify_file_ref(hh1_doc["artifact_roles"]["human_review_html"],hh1_manifest.parent)
    expected={"hp1_package_sha256":hp1["sha256"],"hq2_acceptance_sha256":hq2["sha256"],"hh1_manifest_sha256":hh1["manifest_sha256"],"html_sha256":_hash(html)}
    if decision["bindings"]!=expected:raise CoordinatorFailure("author decision byte bindings are stale")
    target=workspace/"author-events"/f"{decision['event_id']}.json";target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(decision_path,target);dref=_ref(target,workspace,"author_decision")
    if decision["decision"]!="approved":
        terminal="author_rejected" if decision["decision"]=="rejected" else "conception_reentry" if any(x["target_kind"]=="conception_authority" for x in decision["revision_targets"]) else None
        if terminal:
            fake={"schema_version":"1.0","harness":HARNESS,"hld_run_id":state["hld_run_id"],"revision":state["revision"],"stage":"HF1","skill":SKILLS["HF1"],"work_order_id":"AUTHOR-GATE","task_id":"AUTHOR-GATE","event_sequence":decision["event_sequence"],"result_scope":"top_level","result":"blocked","state_before_ref":ledger["current_state_ref"],"input_gate_ref":dref,"result_manifest_ref":dref,"validation_ref":dref,"produced_at":timestamp,"completion_ref":None,"internal_manifest_ref":None,"revision_class":None,"revision_report_ref":None,"candidate_ref":None,"local_defect_evidence":[],"author_event_ref":None,"gate_data_ref":dref,"blocked_report_ref":dref,"blocker_class":"author_rejected" if terminal=="author_rejected" else "reality_dependency","affected_ids":[],"runtime_error_ref":None}
            new=_next_state(state,sequence=decision["event_sequence"],status=terminal,current_stage=None,result_ref=dref,previous_ref=ledger["current_state_ref"]);sref=_persist_state(workspace,new);next_ledger={**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":decision["event_sequence"],"current_state_ref":sref,"consumed_author_event_ids":ledger["consumed_author_event_ids"]+[decision["event_id"]],"terminal_status":terminal};return _snapshot(workspace,next_ledger)
        targets=[]
        for item in decision["revision_targets"]:
            affected=item.get("semantic_target_ids",[]) if item.get("change_scope")=="hld_semantic" else [item["target_id"]]
            source_refs=[item["author_text_locator"],*item.get("target_field_paths",[])]
            targets.append({"target_kind":item["target_kind"],"affected_ids":list(dict.fromkeys(affected)),"requirements":[item["requested_change"]],"source_target_refs":list(dict.fromkeys(source_refs)),"correction_condition":item["requested_change"],"defect_origin":"author_request","violated_contract":"author-request","automatic":False})
        # A final revise must flow through HF1's external-author-request result;
        # the coordinator therefore still issues HF1 and never manufactures it.
    upstreams=[artifacts[name] for name in UPSTREAM["HF1"]];allow=_basic_allowlist(workspace,ledger["current_state_ref"],"HF1",upstreams);allow=[x for x in allow if x["role"]!="run_state"]+[_ref(verify_file_ref(ledger["current_state_ref"],workspace),workspace,"run_state"),dref]
    order,_=_gate_and_order(workspace,ledger["current_state_ref"],state,stage="HF1",timestamp=timestamp,allowlist=sorted(allow,key=lambda x:x["role"]),upstreams=upstreams,after_sequence=decision["event_sequence"])
    next_ledger={**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":read_json(order)["event_sequence"],"active_work_order_ref":_ref(order,workspace,"work_order"),"active_task_kind":"HF1","consumed_author_event_ids":ledger["consumed_author_event_ids"]+[decision["event_id"]]};return _snapshot(workspace,next_ledger)


def supersede_active_group(workspace:Path,original_target:str,lineage_change:str,allowed_new_target_ids:list[str],question_text:str)->Path:
    workspace=workspace.resolve(strict=True);_,ledger=load_current(workspace);state=read_json(verify_file_ref(ledger["current_state_ref"],workspace))
    if state["status"]!="return_active" or not state["revision_plan_ref"] or not state["revision_plan_state_ref"]:raise CoordinatorFailure("no active revision group can be superseded")
    if ledger["active_work_order_ref"] is None:raise CoordinatorFailure("active revision work order is missing")
    plan_path=verify_file_ref(state["revision_plan_ref"],workspace);plan=read_json(plan_path);plan_state_path=verify_file_ref(state["revision_plan_state_ref"],workspace);plan_state=read_json(plan_state_path);group_id=plan_state["active_group_id"];group=next(x for x in plan["target_groups"] if x["group_id"]==group_id)
    if original_target not in group["affected_ids"] or not allowed_new_target_ids:raise CoordinatorFailure("superseded target/allowed replacements do not bind active group")
    sequence=ledger["event_sequence"]+1;event={"schema_version":"1.0","hld_run_id":state["hld_run_id"],"event_sequence":sequence,"event_kind":"target_superseded","group_id":group_id,"original_target":original_target,"lineage_change":lineage_change,"allowed_new_target_ids":allowed_new_target_ids};epath=workspace/"coordinator-events"/f"event-{sequence:06d}-superseded.json";_write(epath,event);eref=_ref(epath,workspace,"coordinator_event")
    transitioned=transition_plan_state(plan_state,plan_group_ids=[x["group_id"] for x in plan["target_groups"]],previous_state_ref=state["revision_plan_state_ref"],transition_event_ref=eref,superseded_group_id=group_id);pspath=workspace/"revision-plan-state"/f"{plan['revision_plan_id']}-revision-{state['revision']+1:03d}.json";_write(pspath,transitioned);psref=_ref(pspath,workspace,"revision_plan_state")
    meaning=canonical_sha256({"requirements":group["requirements"],"completion_condition":group["completion_condition"]});question=revision_retarget_question(hld_run_id=state["hld_run_id"],revision=state["revision"]+1,owner_stage=group["target_stage"],revision_plan_ref=state["revision_plan_ref"],revision_plan_state_ref=psref,group_id=group_id,original_target=original_target,lineage_change=lineage_change,allowed_new_target_ids=allowed_new_target_ids,request_meaning_hash=meaning,question_text=question_text);qpath=workspace/"author-transactions"/f"question-{sequence:06d}-retarget.json";_write(qpath,question);qref=_ref(qpath,workspace,"author_question")
    result_ref=state["current_result_ref"] or eref;new=_next_state(state,sequence=sequence,status="waiting_author_answer",current_stage=None,result_ref=result_ref,previous_ref=ledger["current_state_ref"],plan_ref=state["revision_plan_ref"],plan_state_ref=psref,waiting=qref);sref=_persist_state(workspace,new);next_ledger={**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":sequence,"current_state_ref":sref,"active_work_order_ref":None,"active_task_kind":None};return _snapshot(workspace,next_ledger)


def accept_author_answer(workspace:Path,answer_path:Path,timestamp:str,resolution_kind:str)->Path:
    """Consume exactly one external answer and resume only the sealed question."""
    workspace=workspace.resolve(strict=True);_,ledger=load_current(workspace);state=read_json(verify_file_ref(ledger["current_state_ref"],workspace))
    if state["status"]!="waiting_author_answer" or ledger["active_work_order_ref"] is not None or not state["waiting_transaction_ref"]:raise CoordinatorFailure("author answer gate is not active")
    question_path=verify_file_ref(state["waiting_transaction_ref"],workspace,expected_role="author_question");question=read_json(question_path);_catalog().validate(question,"author-question.schema.json")
    answer=read_json(answer_path);_catalog().validate(answer,"author-answer-event.schema.json")
    if answer["hld_run_id"]!=state["hld_run_id"] or answer["question_ref"]!=state["waiting_transaction_ref"] or answer["question_sha256"]!=_hash(question_path) or answer["external_event_sequence"]<=ledger["event_sequence"]:raise CoordinatorFailure("author answer is stale or does not bind the active question bytes")
    event_id=f"ANSWER-{answer['question_sha256'][:16]}-{answer['external_event_sequence']}"
    if event_id in ledger["consumed_author_event_ids"]:raise CoordinatorFailure("author answer was already consumed")
    stored=workspace/"author-events"/f"{event_id}.json";stored.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(answer_path,stored);aref=_ref(stored,workspace,"author_answer")
    retarget=None
    if question["question_kind"]=="revision_retarget":
        target=answer["author_text"].strip()
        if target not in question["allowed_new_target_ids"]:raise CoordinatorFailure("retarget answer is outside the sealed allowed target set")
        plan=read_json(verify_file_ref(question["revision_plan_ref"],workspace));plan_state=read_json(verify_file_ref(question["revision_plan_state_ref"],workspace));group=next(x for x in plan["target_groups"] if x["group_id"]==question["group_id"])
        if owner_for_id(target)!=group["exact_owner"]:raise CoordinatorFailure("retarget answer changes the exact owner")
        retarget={"group_id":group["group_id"],"original_target_hash":canonical_sha256(question["original_target"]),"author_resolution_ref":aref,"new_target_id":target,"request_meaning_hash":question["request_meaning_hash"]}
    resolution=resolve_author_answer(question=question,question_ref=state["waiting_transaction_ref"],answer_ref=aref,resolution_kind=resolution_kind,new_revision=state["revision"]+1,classification_conclusion=answer["author_text"] if resolution_kind=="hld_local_resolution" else None,retarget_binding=retarget)
    _catalog().validate(resolution,"author-resolution.schema.json");rpath=workspace/"author-transactions"/f"resolution-{answer['external_event_sequence']:06d}.json";_write(rpath,resolution);rref=_ref(rpath,workspace,"author_resolution")
    consumed=ledger["consumed_author_event_ids"]+[event_id]
    if resolution_kind=="conception_authority_change":
        new=_next_state(state,sequence=answer["external_event_sequence"],status="conception_reentry",current_stage=None,result_ref=rref,previous_ref=ledger["current_state_ref"]);sref=_persist_state(workspace,new);return _snapshot(workspace,{**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":answer["external_event_sequence"],"current_state_ref":sref,"consumed_author_event_ids":consumed,"terminal_status":"conception_reentry"})
    plan_ref=state.get("revision_plan_ref");plan_state_ref=state.get("revision_plan_state_ref")
    if resolution_kind=="revision_target_resolution":
        if not plan_ref or not plan_state_ref or retarget is None:raise CoordinatorFailure("retarget resolution lacks active immutable plan")
        plan=read_json(verify_file_ref(plan_ref,workspace));plan_state=read_json(verify_file_ref(plan_state_ref,workspace));transitioned=transition_plan_state(plan_state,plan_group_ids=[x["group_id"] for x in plan["target_groups"]],previous_state_ref=plan_state_ref,transition_event_ref=rref,retarget_binding=retarget);pspath=workspace/"revision-plan-state"/f"{plan['revision_plan_id']}-revision-{state['revision']+1:03d}.json";_catalog().validate(transitioned,"revision-plan-state.schema.json");_write(pspath,transitioned);plan_state_ref=_ref(pspath,workspace,"revision_plan_state")
    resume=resolution["resume_stage"];status="return_active" if plan_ref else "running";new=_next_state(state,sequence=answer["external_event_sequence"],status=status,current_stage=resume,result_ref=rref,previous_ref=ledger["current_state_ref"],plan_ref=plan_ref,plan_state_ref=plan_state_ref);sref=_persist_state(workspace,new)
    supplements=[aref,rref] if question["question_kind"]=="source_resolution" else []
    order,kind,composite=_issue_forward(workspace,sref,new,ledger,timestamp,supplemental_source_refs=supplements)
    if composite is not None:raise CoordinatorFailure("author answer cannot directly resume a composite stage")
    return _snapshot(workspace,{**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":read_json(order)["event_sequence"],"current_state_ref":sref,"active_work_order_ref":_ref(order,workspace,"work_order"),"active_task_kind":kind,"consumed_author_event_ids":consumed,"terminal_status":None})


def reissue_active_work_order(workspace:Path,timestamp:str,reason:str)->Path:
    """Supersede an unexecuted invalid top-level work order without changing run state."""
    workspace=workspace.resolve(strict=True);_,ledger=load_current(workspace)
    if not reason.strip():raise CoordinatorFailure("reissue reason is required")
    if ledger["active_work_order_ref"] is None:raise CoordinatorFailure("no active work order")
    old_path=verify_file_ref(ledger["active_work_order_ref"],workspace,expected_role="work_order");old=read_json(old_path)
    if old["mode"] not in {"forward","return_resolution"}:raise CoordinatorFailure("only an unexecuted forward or return-resolution work order can be reissued")
    if (workspace/old["output_directory"]).exists() or (workspace/"stage-result.json").exists():raise CoordinatorFailure("active work order has execution output and cannot be reissued")
    state=read_json(verify_file_ref(ledger["current_state_ref"],workspace));kind=state["current_stage"]
    if kind is None and ledger["active_task_kind"]=="HF1" and state["status"]=="waiting_author_decision":
        kind="HF1"
    artifacts=_accepted_artifacts(workspace,state)
    if ledger["active_task_kind"] in TASK_CONTRACT:
        kind=ledger["active_task_kind"]
        if state["current_stage"] not in COMPOSITES or old["stage"]!=state["current_stage"] or ledger.get("composite_state_ref") is None:
            raise CoordinatorFailure("reissue changed active composite topology")
        composite_ref=ledger["composite_state_ref"];composite=read_json(verify_file_ref(composite_ref,workspace,expected_role="composite_workspace_state"));previous={item["task_kind"]:item for item in composite["issued_tasks"]};upstreams=[artifacts[name] for name in UPSTREAM[state["current_stage"]]];allow=_internal_allowlist(workspace,state["current_stage"],kind,upstreams,previous);mode,binding,plan_ref,plan_state_ref=_task_return_context(workspace,state,kind)
        order,_=_gate_and_order(workspace,ledger["current_state_ref"],state,stage=state["current_stage"],timestamp=timestamp,allowlist=allow,upstreams=upstreams,task_kind=kind,composite_state_ref=composite_ref,mode=mode,return_binding=binding,plan_ref=plan_ref,plan_state_ref=plan_state_ref,after_sequence=ledger["event_sequence"])
    elif ledger["active_task_kind"]=="publisher":
        if kind not in COMPOSITES or old["stage"]!=kind or ledger.get("composite_state_ref") is None:
            raise CoordinatorFailure("reissue changed active publisher topology")
        composite_ref=ledger["composite_state_ref"]
        composite=read_json(verify_file_ref(composite_ref,workspace,expected_role="composite_workspace_state"))
        upstreams=[artifacts[name] for name in UPSTREAM[kind]]
        allow=_publisher_allowlist(workspace,kind,upstreams,composite,composite_ref)
        order,_=_gate_and_order(
            workspace,ledger["current_state_ref"],state,stage=kind,timestamp=timestamp,
            allowlist=allow,upstreams=upstreams,task_kind="publisher",
            composite_state_ref=composite_ref,after_sequence=ledger["event_sequence"],
        )
    else:
        if kind!=ledger["active_task_kind"] or kind in COMPOSITES:raise CoordinatorFailure("reissue changed active task topology")
        upstreams=[artifacts[name] for name in UPSTREAM[kind]];allow=_basic_allowlist(workspace,ledger["current_state_ref"],kind,upstreams)
        if kind=="HF1":
            author_ref=next((dict(item) for item in old["file_allowlist"] if item.get("role")=="author_decision"),None)
            if author_ref is None:raise CoordinatorFailure("HF1 reissue lacks sealed author decision")
            verify_file_ref(author_ref,workspace,expected_role="author_decision")
            allow=sorted([*allow,author_ref],key=lambda item:item["role"])
        binding=None
        if old["mode"]=="return_resolution":
            if state["status"]!="return_active" or not old.get("return_binding"):raise CoordinatorFailure("return-resolution reissue lacks active revision binding")
            binding=read_json(verify_file_ref(old["return_binding"],workspace,expected_role="return_binding"))
        order,_=_gate_and_order(
            workspace,ledger["current_state_ref"],state,stage=kind,timestamp=timestamp,
            allowlist=allow,upstreams=upstreams,mode=old["mode"],return_binding=binding,
            plan_ref=old.get("revision_plan_ref"),plan_state_ref=old.get("revision_plan_state_ref"),
            after_sequence=ledger["event_sequence"],
        )
    event=read_json(order)["event_sequence"];record={"schema_version":"1.0","harness":HARNESS,"hld_run_id":state["hld_run_id"],"event_sequence":event,"reason":reason.strip(),"superseded_work_order_ref":dict(ledger["active_work_order_ref"]),"replacement_work_order_ref":_ref(order,workspace,"work_order"),"timestamp":timestamp}
    rpath=workspace/"reissues"/f"reissue-{event:06d}-{kind}.json";_write(rpath,record)
    return _snapshot(workspace,{**ledger,"ledger_revision":ledger["ledger_revision"]+1,"event_sequence":event,"active_work_order_ref":_ref(order,workspace,"work_order")})


def _main(argv:list[str]|None=None)->int:
    import argparse
    parser=argparse.ArgumentParser(description="Persisted HLD Harness coordinator");sub=parser.add_subparsers(dest="command",required=True)
    init=sub.add_parser("init-staged");init.add_argument("workspace",type=Path);init.add_argument("run_request",type=Path);init.add_argument("hb0_allowlist",type=Path);init.add_argument("--timestamp",required=True)
    accept=sub.add_parser("accept-result");accept.add_argument("workspace",type=Path);accept.add_argument("result",type=Path);accept.add_argument("--timestamp",required=True);accept.add_argument("--revision-targets",type=Path)
    author=sub.add_parser("accept-author-decision");author.add_argument("workspace",type=Path);author.add_argument("decision",type=Path);author.add_argument("--timestamp",required=True)
    answer=sub.add_parser("accept-author-answer");answer.add_argument("workspace",type=Path);answer.add_argument("answer",type=Path);answer.add_argument("--timestamp",required=True);answer.add_argument("--resolution-kind",required=True,choices=["hld_local_resolution","revision_target_resolution","conception_authority_change"])
    supersede=sub.add_parser("supersede-active-group");supersede.add_argument("workspace",type=Path);supersede.add_argument("original_target");supersede.add_argument("lineage_change");supersede.add_argument("allowed_targets",type=Path);supersede.add_argument("question_text")
    reissue=sub.add_parser("reissue-active");reissue.add_argument("workspace",type=Path);reissue.add_argument("--timestamp",required=True);reissue.add_argument("--reason",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="init-staged":
            raw=read_json(args.hb0_allowlist);allow=raw["hb0_file_allowlist"] if "hb0_file_allowlist" in raw else raw["file_allowlist"];path=initialize_staged(args.workspace,args.run_request,allow,args.timestamp)
        elif args.command=="accept-result":
            targets=read_json(args.revision_targets).get("targets",[]) if args.revision_targets else [];path=accept_result(args.workspace,args.result,args.timestamp,targets)
        elif args.command=="accept-author-decision":path=accept_author_decision(args.workspace,args.decision,args.timestamp)
        elif args.command=="accept-author-answer":path=accept_author_answer(args.workspace,args.answer,args.timestamp,args.resolution_kind)
        elif args.command=="supersede-active-group":path=supersede_active_group(args.workspace,args.original_target,args.lineage_change,read_json(args.allowed_targets)["allowed_new_target_ids"],args.question_text)
        else:path=reissue_active_work_order(args.workspace,args.timestamp,args.reason)
        print(json.dumps({"status":"ok","ledger":str(path)},ensure_ascii=False));return 0
    except (CoordinatorFailure,ContractError,ValueError,OSError,KeyError) as error:
        print(json.dumps({"status":"error","error":str(error)},ensure_ascii=False),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(_main())
