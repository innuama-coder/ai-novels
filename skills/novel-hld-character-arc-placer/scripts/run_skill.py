#!/usr/bin/env python3
"""HC1 semantic callback over the public design-stage Harness runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


SKILL_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = Path(__file__).resolve().parents[3] / "harnesses" / "novel-hld-autonomous"
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from runtime.design_stage_runtime import CandidateError, execute  # type: ignore[import-not-found]  # noqa: E402


_WORKSPACE: Path | None = None
_WORK_ORDER: dict[str, Any] | None = None
_LIFECYCLE_CLAIM = re.compile(
    r"死亡|死去|死了|牺牲|去世|亡故|脑死|脑死亡|身亡|存活|生还|活着|在世|"
    r"昏迷|失去意识|清醒|苏醒|恢复意识|复生|复活|"
    r"\b(?:dead|death|deaths|die|dies|died|dying|alive|living|"
    r"survival|survive|survives|survived|surviving|"
    r"sacrifice|sacrifices|sacrificed|sacrificing|"
    r"brain[- ]dead|brain[- ]death|unconscious|unconsciousness|coma|comatose|"
    r"conscious|consciousness|recover|recovers|recovered|recovering|recovery|"
    r"revival|revive|revives|revived|resurrect|resurrected|resurrection)\b",
    re.IGNORECASE,
)
_ENGLISH_PROSE = re.compile(r"\b[A-Za-z]{2,}\b")
_RESPONSIBILITY_FORM = re.compile(r"^负责\S")
_DESIGN_JARGON = re.compile(
    r"作者|读者|故事|叙事|情节|剧情|章节|场景|角色弧|故事线|"
    r"铺垫|伏笔|高潮|悬念|冲突功能|叙事功能|"
    r"失败路径|成功路径|戏剧功能|文本功能|结构功能"
)


def _upstream(model: Mapping[str, Any], stage: str) -> dict[str, Any]:
    if _WORKSPACE is None:
        raise CandidateError("HC1 validator workspace is unavailable")
    refs = [item for item in model["source_artifacts"] if item.get("role") == f"upstream::{stage}::main"]
    if len(refs) != 1:
        raise CandidateError(f"HC1 requires exactly one {stage} main artifact")
    return json.loads((_WORKSPACE / refs[0]["path"]).read_text(encoding="utf-8"))


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return set().union(*(_strings(item) for item in value), set())
    if isinstance(value, dict):
        return set().union(*(_strings(item) for item in value.values()), set())
    return set()


def _return_binding() -> dict[str, Any] | None:
    if _WORK_ORDER is None or _WORK_ORDER.get("mode") != "return_resolution":
        return None
    if _WORKSPACE is None:
        raise CandidateError("HC1 validator workspace is unavailable")
    ref = _WORK_ORDER.get("return_binding")
    if (
        not isinstance(ref, dict)
        or ref.get("role") != "return_binding"
        or not isinstance(ref.get("path"), str)
        or not isinstance(ref.get("sha256"), str)
    ):
        raise CandidateError("HC1 return-resolution work order requires an exact return binding")
    target = (_WORKSPACE / ref["path"]).resolve(strict=True)
    try:
        target.relative_to(_WORKSPACE.resolve(strict=True))
    except ValueError as exc:
        raise CandidateError("HC1 return binding escapes the sealed workspace") from exc
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise CandidateError("HC1 return binding hash mismatch")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise CandidateError("HC1 return binding must be an object")
    return value


def _return_base() -> dict[str, Any] | None:
    if _WORKSPACE is None or _WORK_ORDER is None:
        raise CandidateError("HC1 return base is unavailable")
    by_role = {item.get("role"): item for item in _WORK_ORDER.get("file_allowlist", [])}
    required = {
        role: by_role.get(role) for role in (
            "return_base::HC1::main",
            "return_base::HC1::manifest",
            "return_base::HC1::completion",
        )
    }
    present = [isinstance(item, dict) for item in required.values()]
    if not any(present):
        return None
    if not all(present):
        raise CandidateError("HC1 return-resolution has a partial prior HC1 base package")

    loaded: dict[str, Any] = {}
    root = _WORKSPACE.resolve(strict=True)
    for role, ref in required.items():
        target = (_WORKSPACE / ref["path"]).resolve(strict=True)
        try:target.relative_to(root)
        except ValueError as exc:raise CandidateError("HC1 return base escapes the sealed workspace") from exc
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise CandidateError("HC1 return base hash mismatch")
        loaded[role] = json.loads(raw.decode("utf-8"))
    completion = loaded["return_base::HC1::completion"]
    main_ref = required["return_base::HC1::main"]
    manifest_ref = required["return_base::HC1::manifest"]
    canonical = [item for item in completion.get("canonical_artifacts", []) if item.get("role") == "character_arc_placement"]
    if (
        completion.get("stage") != "HC1"
        or completion.get("status") != "ready"
        or canonical != [{"path": main_ref["path"], "role": "character_arc_placement", "sha256": main_ref["sha256"]}]
        or completion.get("manifest_ref") != {"path": manifest_ref["path"], "role": "package_manifest", "sha256": manifest_ref["sha256"]}
    ):
        raise CandidateError("HC1 return base is not the exact accepted HC1 package")
    return loaded["return_base::HC1::main"]


def _ordered_target_ids(
    affected_ids: list[str],
    model: Mapping[str, Any],
    field: str,
    prefix: str,
) -> list[str]:
    requested = [item for item in affected_ids if item.startswith(prefix)]
    inventory = [item.get("id") for item in model[field]]
    if len(inventory) != len(set(inventory)):
        raise CandidateError(f"HC1 {field} inventory contains duplicate stable IDs")
    requested_set = set(requested)
    actual = [item for item in inventory if item in requested_set]
    if actual != requested:
        raise CandidateError(
            f"HC1 return-resolution {field} must exactly cover affected stable IDs in canonical order"
        )
    return requested


def _preserve_targeted_collection(
    return_base: Mapping[str, Any],
    model: Mapping[str, Any],
    field: str,
    target_ids: set[str],
) -> None:
    before_items = return_base.get(field, [])
    after_items = model.get(field, [])
    if [item.get("id") for item in before_items] != [item.get("id") for item in after_items]:
        raise CandidateError(f"HC1 return-resolution changed the {field} inventory")
    for before, after in zip(before_items, after_items):
        if before.get("id") not in target_ids and before != after:
            label = field.replace("_", " ")
            raise CandidateError(
                f"{before.get('id')}: unaffected {label} object changed during return resolution"
            )


def _preserve_derivation_claims(
    return_base: Mapping[str, Any],
    model: Mapping[str, Any],
    allowed_target_locators: set[str],
) -> None:
    before_claims = return_base.get("derivation_claims", [])
    after_claims = model.get("derivation_claims", [])
    if [item.get("id") for item in before_claims] != [item.get("id") for item in after_claims]:
        raise CandidateError("HC1 combined return changed the derivation-claim inventory")
    for before, after in zip(before_claims, after_claims):
        if before.get("target_locator") != after.get("target_locator"):
            raise CandidateError(
                f"{before.get('id')}: derivation claim target changed during combined return"
            )
        if before.get("target_locator") not in allowed_target_locators and before != after:
            raise CandidateError(
                f"{before.get('id')}: unrelated derivation claim changed during combined return"
            )


def validate_stage_model(model: dict[str, Any], _contract: Mapping[str, Any]) -> None:
    ha1 = _upstream(model, "HA1")
    hs1 = _upstream(model, "HS1")
    return_binding = _return_binding()
    if return_binding is not None:
        return_base = _return_base()
        affected_ids = return_binding.get("affected_ids")
        if (
            return_binding.get("exact_owner") != "HC1"
            or not isinstance(affected_ids, list)
            or not affected_ids
            or any(not isinstance(item, str) for item in affected_ids)
            or len(affected_ids) != len(set(affected_ids))
        ):
            raise CandidateError("HC1 return-resolution binding is not an exact non-empty HC1 target group")
        if all(item.startswith("HAS-PARTICIPATION-") for item in affected_ids):
            actual_ids = [item.get("id") for item in model["character_participation_register"]]
            if actual_ids != affected_ids:
                raise CandidateError(
                    "HC1 return-resolution participation register must exactly preserve affected stable IDs in order"
                )
            for participant in model["character_participation_register"]:
                expected_character_id = "CHR-" + participant["id"].removeprefix("HAS-PARTICIPATION-")
                if participant.get("character_id") != expected_character_id:
                    raise CandidateError(
                        f"{participant['id']}: participation stable ID does not bind its exact character identity"
                    )
        elif all(item.startswith("HAS-AGENCY-") for item in affected_ids):
            _ordered_target_ids(
                affected_ids, model, "chapter_agency_contracts", "HAS-AGENCY-"
            )
            if return_base is not None:
                _preserve_targeted_collection(
                    return_base,
                    model,
                    "chapter_agency_contracts",
                    set(affected_ids),
                )
                preserved_fields=(
                    "character_participation_register","arc_state_models","arc_steps","relationship_steps",
                    "choice_cost_consequence_links","event_character_alignment",
                    "capability_information_permission_checks","decision_dependencies","open_items",
                )
                for field in preserved_fields:
                    if return_base.get(field) != model.get(field):
                        raise CandidateError(f"HC1 return-resolution changed unaffected semantic field: {field}")
        elif (
            any(item.startswith("HAS-AGENCY-") for item in affected_ids)
            and any(item.startswith("HAS-ARC-") for item in affected_ids)
            and all(
                item.startswith("HAS-AGENCY-") or item.startswith("HAS-ARC-")
                for item in affected_ids
            )
        ):
            family_order = [
                "agency" if item.startswith("HAS-AGENCY-") else "arc"
                for item in affected_ids
            ]
            if family_order != sorted(family_order, key={"agency": 0, "arc": 1}.get):
                raise CandidateError(
                    "HC1 combined return targets must list chapter agency IDs before arc-step IDs"
                )
            agency_ids = _ordered_target_ids(
                affected_ids, model, "chapter_agency_contracts", "HAS-AGENCY-"
            )
            arc_ids = _ordered_target_ids(
                affected_ids, model, "arc_steps", "HAS-ARC-"
            )
            if return_base is None:
                raise CandidateError("HC1 combined return targets require an exact prior HC1 base")
            _preserve_targeted_collection(
                return_base, model, "chapter_agency_contracts", set(agency_ids)
            )
            _preserve_targeted_collection(return_base, model, "arc_steps", set(arc_ids))
            preserved_fields = (
                "character_participation_register",
                "arc_state_models",
                "relationship_steps",
                "choice_cost_consequence_links",
                "event_character_alignment",
                "capability_information_permission_checks",
                "authority_partition",
                "design_decisions",
                "decision_dependencies",
                "open_items",
                "downstream_contract",
            )
            for field in preserved_fields:
                if return_base.get(field) != model.get(field):
                    raise CandidateError(
                        f"HC1 combined return changed unaffected semantic field: {field}"
                    )
            _preserve_derivation_claims(
                return_base,
                model,
                {"/chapter_agency_contracts", "/arc_steps"},
            )
        else:
            raise CandidateError(
                "HC1 return-resolution target group must contain participation IDs, chapter agency IDs, "
                "or the exact supported chapter-agency-plus-arc-step combination"
            )
    for participant in model["character_participation_register"]:
        for responsibility in participant.get("responsibilities", []):
            if (
                not _RESPONSIBILITY_FORM.search(responsibility)
                or _LIFECYCLE_CLAIM.search(responsibility)
                or _ENGLISH_PROSE.search(responsibility)
                or _DESIGN_JARGON.search(responsibility)
            ):
                raise CandidateError(
                    f"{participant['id']}: every responsibility must be a natural Chinese duty sentence "
                    "beginning with '负责' and describing an in-world duty; remove English prose, "
                    "design jargon, and lifecycle claims, then bind availability or lifecycle limits "
                    "in chapter agency contracts"
                )
    core = {
        item.get("character_id") for item in model["character_participation_register"]
        if item.get("importance") == "core"
    }
    models = {item.get("character_id") for item in model["arc_state_models"]}
    if not core or not core.issubset(models):
        raise CandidateError("HC1 every core character requires an arc state model")
    roles: dict[str, set[str]] = {character_id: set() for character_id in core}
    for step in model["arc_steps"]:
        if step.get("character_id") in roles:
            roles[step["character_id"]].add(step.get("role"))
        for field in ("pressure", "choice", "cost", "consequence", "unit_id", "event_id", "storyline_segment_id"):
            if not step.get(field):
                raise CandidateError(f"{step['id']}: missing {field}")
    required_roles = {"start", "pressure", "choice", "cost", "result"}
    for character_id, actual in roles.items():
        if not required_roles.issubset(actual):
            raise CandidateError(f"HC1 core arc {character_id} lacks start-pressure-choice-cost-result")
    for relationship in model["relationship_steps"]:
        if len(relationship.get("character_ids", [])) != 2 or not relationship.get("state_before") or not relationship.get("state_after"):
            raise CandidateError(f"{relationship['id']}: relationship change must be bilateral")

    known_characters = {item.get("character_id") for item in model["character_participation_register"]}
    if None in known_characters:
        raise CandidateError("HC1 participation contains an incomplete character identity")
    shells = ha1.get("chapter_shells", [])
    shell_ids = [item.get("id") for item in shells]
    if not shells or None in shell_ids or len(shell_ids) != len(set(shell_ids)):
        raise CandidateError("HC1 requires unique HA1 chapter shells")
    contracts = model["chapter_agency_contracts"]
    if [item.get("chapter_id") for item in contracts] != shell_ids:
        raise CandidateError("HC1 requires one ordered chapter agency contract per HA1 shell")
    shell_by_id = {item["id"]: item for item in shells}
    plans = hs1.get("chapter_storyline_plan", [])
    if [item.get("chapter_id") for item in plans] != shell_ids:
        raise CandidateError("HC1 requires one ordered HS1 chapter plan per HA1 shell")
    plan_by_chapter = {item["chapter_id"]: item for item in plans}
    for item in contracts:
        chapter_id = item["chapter_id"]
        if item["parent_unit_id"] != shell_by_id[chapter_id].get("parent_unit_id"):
            raise CandidateError(f"{item['id']}: chapter agency parent unit does not match HA1")
        focal = set(item["focal_character_ids"])
        choice = set(item["choice_actor_ids"])
        institutional = item["institutional_choice_actors"]
        cost = set(item["cost_bearer_ids"])
        unavailable = set(item["unavailable_character_ids"])
        if not (focal | choice | cost | unavailable).issubset(known_characters):
            raise CandidateError(f"{item['id']}: chapter agency contract references an unknown character")
        if unavailable & (focal | choice):
            raise CandidateError(f"{item['id']}: unavailable character cannot focalize or choose")
        if not choice and not institutional:
            raise CandidateError(f"{item['id']}: chapter choice requires a named or institutional actor")
        relevant_authority = _strings(shell_by_id[chapter_id]) | _strings(plan_by_chapter[chapter_id])
        contract_sources = set(item["source_refs"])
        for actor in institutional:
            actor_sources = set(actor["source_refs"])
            if not actor_sources.issubset(contract_sources):
                raise CandidateError(f"{item['id']}: institutional actor sources must be bound by the chapter contract")
            if not actor_sources & relevant_authority:
                raise CandidateError(f"{item['id']}: institutional actor lacks this chapter's HA1/HS1 authority")
        path_ids = [path.get("character_id") for path in item["information_paths"]]
        if path_ids != item["focal_character_ids"] or len(path_ids) != len(set(path_ids)):
            raise CandidateError(f"{item['id']}: information paths must exactly cover focal characters in order")
        if any(not path.get("acquisition_modes") or not path.get("limit") for path in item["information_paths"]):
            raise CandidateError(f"{item['id']}: focal information path is incomplete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_order", type=Path)
    parser.add_argument("draft_dir", type=Path)
    args = parser.parse_args()
    global _WORKSPACE, _WORK_ORDER
    _WORKSPACE = args.work_order.resolve(strict=True).parent
    _WORK_ORDER = json.loads(args.work_order.resolve(strict=True).read_text(encoding="utf-8"))
    code, _ = execute(SKILL_ROOT.resolve(), args.work_order.resolve(), args.draft_dir.resolve(), validate_stage_model)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
