"""Authoritative public-runtime registry used before coordinator issuance.

The registry is deliberately outside the coordinator: bounded skills own their
implementation closure and this adapter only resolves that public contract.
Any disagreement with the frozen stage registry or a skill runtime contract is
an issuance-time error.
"""

from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .canonical import ContractError
from .contracts import SKILLS
from .schema_catalog import SchemaCatalog

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
REGISTRY_PATH = ROOT / "references" / "public-runtime-registry.json"
TOKENS=frozenset({"HB0","HA1","HS1","HC1","HI1","HR1","HK1","HD1","HQ1","HP1","consumer_test","fidelity_test","HH1-A","HH1-B","HH1-C","publisher","HH1-publisher","HF1"})


class RuntimeRegistryError(ContractError):
    pass


def _load(path: Path = REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    value=json.loads(path.read_text(encoding="utf-8"))
    try:SchemaCatalog(ROOT/"schemas").validate(value,"public-runtime-registry.schema.json")
    except ContractError as exc:raise RuntimeRegistryError("public runtime registry schema is invalid") from exc
    if set(value["entries"])!=TOKENS:raise RuntimeRegistryError("public runtime registry token topology is not exact")
    for entry in value["entries"].values():
        has_provider="module" in entry or "digest_callable" in entry
        has_contract="contract_path" in entry or "contract_schema" in entry or "closure_paths_sha256" in entry
        if entry["digest_strategy"]=="module_callable" and not ("module" in entry and "digest_callable" in entry):raise RuntimeRegistryError("module digest provider is incomplete")
        if entry["digest_strategy"]!="module_callable" and has_provider:raise RuntimeRegistryError("non-module digest entry declares an illegal provider")
        if entry["digest_strategy"]=="closed_runtime_contract" and not all(key in entry for key in ("contract_path","contract_schema","closure_paths_sha256")):raise RuntimeRegistryError("closed runtime contract provider is incomplete")
        if entry["digest_strategy"]!="closed_runtime_contract" and has_contract:raise RuntimeRegistryError("non-contract digest entry declares an illegal contract provider")
    return value["entries"]


def _module_digest(entry: Mapping[str,Any]) -> str:
    module=importlib.import_module(entry["module"])
    declared_skill=getattr(module,"SKILL",getattr(module,"PUBLISHER",None))
    declared_version=getattr(module,"VERSION",None)
    if declared_skill is not None and declared_skill!=entry["skill"]:raise RuntimeRegistryError("registered module owner differs from registry")
    if declared_version is not None and declared_version!=entry["version"]:raise RuntimeRegistryError("registered module version differs from registry")
    function=getattr(module,entry["digest_callable"],None)
    if not callable(function):raise RuntimeRegistryError("registered digest callable is unavailable")
    return function()


def _contract_digest(entry: Mapping[str,Any],skill_root:Path) -> tuple[str,str,str]:
    from .design_stage_runtime import implementation_sha256,load_contract
    contract=load_contract(skill_root)
    if (contract["skill"],contract["stage"],contract["runtime_version"])!=(entry["skill"],entry["stage"],entry["version"]):
        raise RuntimeRegistryError("public runtime registry differs from skill runtime contract")
    declared=contract.get("public_entrypoint")
    declared_path=declared.get("path") if isinstance(declared,dict) else declared
    if declared_path is not None and declared_path!=entry["public_entrypoint"]:raise RuntimeRegistryError("public entrypoint differs from skill runtime contract")
    closure=contract.get("implementation_closure")
    if closure is not None:
        from .design_stage_runtime import implementation_files
        actual=[path.resolve().relative_to(REPO.resolve()).as_posix() for path in implementation_files(skill_root)]
        if closure.get("algorithm")!="sha256-basename-nul-content-nul-v1" or closure.get("ordered_files")!=actual:raise RuntimeRegistryError("skill implementation closure differs from public runtime")
    return contract["skill"],contract["runtime_version"],implementation_sha256(skill_root)


def _closure_paths_hash(ordered: list[str]) -> str:
    return hashlib.sha256(json.dumps(ordered,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()


def _resolve_closure_paths(repo: Path, ordered: list[str]) -> list[Path]:
    root=repo.resolve();paths=[]
    for relative in ordered:
        path=(root/relative).resolve()
        try:path.relative_to(root)
        except ValueError as exc:raise RuntimeRegistryError("implementation closure escapes repository") from exc
        if not path.is_file():raise RuntimeRegistryError("implementation closure member is unavailable")
        paths.append(path)
    if len(paths)!=len(set(paths)):raise RuntimeRegistryError("implementation closure contains duplicate paths")
    return paths


def _closure_content_digest(repo: Path, paths: list[Path]) -> str:
    root=repo.resolve();digest=hashlib.sha256()
    for path in paths:
        relative=path.resolve().relative_to(root).as_posix();digest.update(relative.encode("utf-8")+b"\0"+path.read_bytes()+b"\0")
    return digest.hexdigest()


def _closed_contract_digest(entry: Mapping[str,Any], token:str) -> tuple[str,str,str]:
    skill_root=(REPO/"skills"/entry["skill"]).resolve()
    contract_path=(REPO/entry["contract_path"]).resolve();schema_path=(REPO/entry["contract_schema"]).resolve()
    try:
        contract_path.relative_to(skill_root);schema_path.relative_to(skill_root/"schemas")
    except ValueError as exc:raise RuntimeRegistryError("closed runtime contract/schema escapes its skill root") from exc
    if not contract_path.is_file() or not schema_path.is_file():raise RuntimeRegistryError("closed runtime contract/schema is unavailable")
    documents={str(path.resolve()):json.loads(path.read_text(encoding="utf-8")) for path in (ROOT/"schemas").glob("*.schema.json")}
    for path in (skill_root/"schemas").glob("*.schema.json"):documents[str(path.resolve())]=json.loads(path.read_text(encoding="utf-8"))
    catalog=SchemaCatalog.from_documents(documents);contract=json.loads(contract_path.read_text(encoding="utf-8"))
    try:catalog.validate(contract,schema_path.name)
    except ContractError as exc:raise RuntimeRegistryError("closed runtime contract schema is invalid") from exc
    if (contract["skill"],contract["stage"],contract["owner_version"])!=(entry["skill"],entry["stage"],entry["version"]):raise RuntimeRegistryError("closed runtime contract owner identity differs from registry")
    if token not in contract["task_kinds"]:raise RuntimeRegistryError("closed runtime contract does not own task kind")
    declared=contract["public_entrypoint"]["path"]
    if declared!=entry["public_entrypoint"]:raise RuntimeRegistryError("closed runtime public entrypoint differs from registry")
    closure=contract["implementation_closure"]
    if closure["algorithm"]!="sha256-relative-path-nul-content-nul-v1":raise RuntimeRegistryError("closed runtime digest algorithm is unsupported")
    path_list_hash=_closure_paths_hash(closure["ordered_files"])
    if path_list_hash!=entry["closure_paths_sha256"]:raise RuntimeRegistryError("implementation closure order/path set differs from registry")
    paths=_resolve_closure_paths(REPO,closure["ordered_files"])
    entrypoint=(REPO/declared).resolve()
    if entrypoint not in paths:raise RuntimeRegistryError("public entrypoint is outside implementation closure")
    return contract["skill"],contract["owner_version"],_closure_content_digest(REPO,paths)


def resolve_public_owner(stage:str, task_kind:str|None=None, *, registry_path:Path|None=None, expected_skill:str|None=None) -> tuple[str,str,str]:
    """Resolve owner identity and the exact digest its public gate verifies."""
    token=task_kind or stage;entries=_load(REGISTRY_PATH if registry_path is None else registry_path)
    if token not in entries:raise RuntimeRegistryError(f"unregistered public runtime: {token}")
    entry=entries[token]
    required={"stage","skill","version","public_entrypoint","digest_strategy"}
    if not required.issubset(entry):raise RuntimeRegistryError("public runtime registry entry is incomplete")
    if entry["stage"]!=stage:raise RuntimeRegistryError("public runtime registry stage drift")
    if expected_skill is not None and entry["skill"]!=expected_skill:raise RuntimeRegistryError("public runtime registry owner drift")
    if task_kind is None and SKILLS.get(stage)!=entry["skill"]:raise RuntimeRegistryError("public runtime registry differs from frozen stage owner")
    entrypoint=(REPO/entry["public_entrypoint"]).resolve()
    try:entrypoint.relative_to(REPO.resolve())
    except ValueError as exc:raise RuntimeRegistryError("public entrypoint escapes repository") from exc
    if not entrypoint.is_file():raise RuntimeRegistryError("registered public entrypoint is unavailable")
    strategy=entry["digest_strategy"]
    if strategy=="runtime_contract":return _contract_digest(entry,REPO/"skills"/entry["skill"])
    if strategy=="closed_runtime_contract":return _closed_contract_digest(entry,token)
    if strategy=="module_callable":digest=_module_digest(entry)
    else:raise RuntimeRegistryError("unsupported public digest strategy")
    if not isinstance(digest,str) or len(digest)!=64:raise RuntimeRegistryError("public runtime digest is invalid")
    return entry["skill"],entry["version"],digest
