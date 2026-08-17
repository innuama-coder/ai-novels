"""Controlled H1-B fragment generation and formal package validation."""

from __future__ import annotations

import copy
import importlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
p1_runtime = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)
h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)

PHASES = (
    "brief-and-source-challenge",
    "scene-draft",
    "boundary-and-style-revision",
)
LANGUAGE_CONTRACT_ID = "zh-Hans-review-v1"
STYLE_CONTRACT_ID = "restrained-concrete-scene-v1"
DEPTH_CONTRACT_ID = "character-grounded-scene-v1"
LANGUAGE = "zh-Hans"
POV_MODE = "third_person_limited"
INTERIORITY_POLICY = "process-only-no-unresolved-decision-disclosure"
SURFACE_DETAIL_POLICY = "fragment-local-non-authoritative-v1"
PURPOSE = "conception_review_sample"
VISIBLE_UNIT_CONTRACT_ID = "zh-Hans-combined-visible-units-v1"
MIN_CJK_UNIT_RATIO = 0.70
STYLE_PRINCIPLES = (
    "single_limited_pov",
    "continuous_scene_now",
    "concrete_selective_detail",
    "pressure_choice_consequence",
    "subtextual_interaction",
    "restrained_emotion",
    "earned_state_change",
)
NARRATIVE_QUALITY_PRINCIPLES = (
    "character_specific_attention",
    "competing_impulses",
    "stimulus_interpretation_action",
    "escalating_resistance",
    "subtext_or_meaning_gap",
    "earned_turn",
    "reader_inference_space",
    "no_explanatory_closure",
)
_DECISIVE_INTERIORITY = re.compile(
    r"(?:早已|已经|终于)(?:在心里)?决定|"
    r"真正的计划是|内心深处.{0,12}(?:知道|确信|决定)"
)
_NON_PROSE = re.compile(
    r"(?m)^\s*(?:#{1,6}\s|[-*]\s|```|(?:镜头|场景|旁白|评审说明)[:：])"
)
_HERE = Path(__file__).resolve()
_SKILL = _HERE.parents[1]
_REPO = _HERE.parents[3]
_SCHEMAS = (
    _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
)
_ROOT_FILES = {
    "fragment-package.json",
    "fragments.md",
    "generation-session.json",
    "generation-evidence-index.json",
    "session-workspace-completion.json",
    "execution-record.json",
    "validation.json",
    "package-manifest.json",
}
_ROOT_PREFIXES = ("generation-evidence/", "implementation/")
_SESSION_FILES = {"generation-session.json", "session-state.json"}


class H1BError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class FragmentReceipt:
    package_root: Path
    manifest: dict[str, Any]
    transition: Any


def _fail(code: str, message: str) -> None:
    raise H1BError(code, message)


def _read(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(code, f"{path}: {error}")
    if not isinstance(value, dict):
        _fail(code, f"{path} root must be an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


def _write_new(path: Path, value: Any) -> None:
    if path.exists():
        _fail("H1B_OUTPUT_EXISTS", str(path))
    _write(path, value)


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


def _copy_exact(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        _fail("H1B_COPY_DRIFT", str(source))


def _implementation_paths() -> dict[str, Path]:
    return {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/v2-fragment-contract.md": (
            _SKILL / "references" / "v2-fragment-contract.md"
        ),
        "skill/style-contract.md": (
            _SKILL / "references" / "style-contract.md"
        ),
        "schemas/fragment-package.schema.json": (
            _SCHEMAS / "fragment-package.schema.json"
        ),
        "schemas/h1-fragment-briefs.schema.json": (
            _SCHEMAS / "h1-fragment-briefs.schema.json"
        ),
        "schemas/h1-review-plan.schema.json": (
            _SCHEMAS / "h1-review-plan.schema.json"
        ),
        "schemas/h1-workspace-state.schema.json": (
            _SCHEMAS / "h1-workspace-state.schema.json"
        ),
        "schemas/human-review-report.schema.json": (
            _SCHEMAS / "human-review-report.schema.json"
        ),
        "schemas/package-manifest.schema.json": (
            _SCHEMAS / "package-manifest.schema.json"
        ),
    }


def _identity() -> dict[str, str]:
    task_id = os.environ.get("CODEX_TASK_ID", "").strip()
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not task_id or not thread_id:
        _fail(
            "H1B_CONTROLLED_CONTEXT_REQUIRED",
            "CODEX_TASK_ID and CODEX_THREAD_ID are required",
        )
    return {"task_id": task_id, "thread_id": thread_id}


def _p1_reference(root: Path) -> dict[str, str]:
    completion = _read(
        root / "stage-completion.json", "H1B_P1_COMPLETION_INVALID"
    )
    if completion.get("stage") != "P1" or completion.get("status") != "ready":
        _fail("H1B_P1_COMPLETION_INVALID", "P1 is not ready")
    return {
        "stage": "P1",
        "path": "P1/stage-completion.json",
        "sha256": rt.sha256_file(root / "stage-completion.json"),
    }


def _artifact_only(reference: Mapping[str, str]) -> dict[str, str]:
    return {"path": reference["path"], "sha256": reference["sha256"]}


def _sealed_plan_manifest_reference(
    *,
    plan_root: Path,
    workspace_state: Any,
    runtime: Any,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve the sole plan manifest authorized by the planned workspace.

    The caller supplies the physical package root, while the sealed workspace
    supplies its logical name.  Requiring both views to describe the same H1
    package prevents a stale legacy root or a foreign look-alike package from
    being admitted without resorting to filesystem discovery.
    """

    try:
        runtime.validate(
            workspace_state.data, "h1-workspace-state.schema.json"
        )
    except Exception as error:
        _fail("H1B_WORKSPACE_INVALID", str(error))
    workspace = workspace_state.data
    artifacts = workspace.get("artifacts")
    reference = (
        artifacts.get("plan_manifest")
        if isinstance(artifacts, Mapping)
        else None
    )
    if not isinstance(reference, Mapping) or set(reference) != {
        "path",
        "sha256",
    }:
        _fail(
            "H1B_PLAN_MANIFEST_INVALID",
            "planned workspace must seal one exact plan manifest reference",
        )
    logical = reference.get("path")
    digest = reference.get("sha256")
    if (
        not isinstance(logical, str)
        or "\\" in logical
        or not isinstance(digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    ):
        _fail(
            "H1B_PLAN_MANIFEST_INVALID",
            "plan manifest reference must be canonical POSIX plus raw SHA-256",
        )
    path = PurePosixPath(logical)
    if (
        path.is_absolute()
        or path.as_posix() != logical
        or len(path.parts) < 3
        or path.parts[0] != "H1"
        or path.parts[-1] != "package-manifest.json"
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _fail(
            "H1B_PLAN_MANIFEST_INVALID",
            "plan manifest must be a contained canonical H1 package path",
        )

    package_parts = path.parts[1:-1]
    physical = plan_root.resolve()
    if (
        len(physical.parts) <= len(package_parts)
        or tuple(physical.parts[-len(package_parts) :]) != package_parts
        or physical.parts[-len(package_parts) - 1] != "H1"
    ):
        _fail(
            "H1B_PLAN_MANIFEST_INVALID",
            "supplied plan root does not match the sealed H1 logical package",
        )
    manifest_path = physical / "package-manifest.json"
    if not manifest_path.is_file() or rt.sha256_file(manifest_path) != digest:
        _fail(
            "H1B_PLAN_MANIFEST_INVALID",
            "sealed plan manifest raw hash does not match the supplied root",
        )
    return copy.deepcopy(workspace), copy.deepcopy(dict(reference))


def _resolve_pointer(value: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return value
    current = value
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        try:
            current = (
                current[int(token)] if isinstance(current, list)
                else current[token]
            )
        except (KeyError, IndexError, ValueError, TypeError) as error:
            _fail("H1B_SOURCE_INVENTORY_INVALID", str(error))
    return current


def _validate_source_inventory(
    inventory: Mapping[str, Any], *, p1_root: Path
) -> dict[str, dict[str, Any]]:
    anchors = inventory.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        _fail("H1B_SOURCE_INVENTORY_INVALID", "anchors are empty")
    result: dict[str, dict[str, Any]] = {}
    source_object_ids: set[str] = set()
    for anchor in anchors:
        if (
            not isinstance(anchor, Mapping)
            or set(anchor)
            != {
                "id",
                "stage",
                "source_id",
                "artifact",
                "json_pointer",
                "value_sha256",
            }
            or anchor["id"] in result
        ):
            _fail("H1B_SOURCE_INVENTORY_INVALID", "anchor shape/id")
        try:
            path = rt.verify_artifact_reference(
                anchor["artifact"], root=p1_root
            )
        except Exception as error:
            _fail("H1B_SOURCE_INVENTORY_INVALID", str(error))
        source = _read(path, "H1B_SOURCE_INVENTORY_INVALID")
        value = _resolve_pointer(source, anchor["json_pointer"])
        if (
            not isinstance(value, Mapping)
            or value.get("id") != anchor["source_id"]
            or rt.canonical_sha256(value) != anchor["value_sha256"]
        ):
            _fail(
                "H1B_SOURCE_INVENTORY_INVALID",
                f"stale P1 value {anchor['id']}",
            )
        result[anchor["id"]] = {
            **copy.deepcopy(dict(anchor)),
            "_value": copy.deepcopy(value),
        }
        source_object_ids.add(anchor["source_id"])
    return result


def _validate_upstream(
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    plan_active_return_request: Any | None,
    runtime: Any,
) -> dict[str, Any]:
    p1_root = Path(p1_package).resolve()
    plan_root = Path(plan_package).resolve()
    workspace, plan_manifest = _sealed_plan_manifest_reference(
        plan_root=plan_root,
        workspace_state=workspace_state,
        runtime=runtime,
    )
    p1_before = _tree_inventory(p1_root)
    plan_before = _tree_inventory(plan_root)
    try:
        h1a.validate_plan_package(
            plan_root,
            p1_package=p1_root,
            input_gate=plan_input_gate,
            workspace_state=plan_workspace_state,
            active_return_request=plan_active_return_request,
            runtime=runtime,
        )
    except Exception as error:
        _fail("H1B_PLAN_INVALID", str(error))
    try:
        p1_validation = p1_runtime.validate_p1_package(
            p1_root, runtime=runtime
        )
    except Exception as error:
        _fail("H1B_P1_INVALID", str(error))
    if p1_validation.get("verdict") != "ready":
        _fail("H1B_P1_INVALID", "P1 validator did not return ready")
    p1_stage = _p1_reference(p1_root)
    p1_artifact = _artifact_only(p1_stage)
    try:
        initialized = h1a.validate_plan_workspace(
            plan_workspace_state,
            p1_completion=p1_stage,
            runtime=runtime,
        )
    except Exception as error:
        _fail("H1B_PLAN_WORKSPACE_INVALID", str(error))
    plan = _read(plan_root / "review-plan.json", "H1B_PLAN_INVALID")
    inventory = _read(
        plan_root / "source-inventory.json",
        "H1B_SOURCE_INVENTORY_INVALID",
    )
    briefs = _read(
        plan_root / "fragment-briefs.json", "H1B_BRIEFS_INVALID"
    )
    plan_manifest_value = _read(
        plan_root / "package-manifest.json", "H1B_PLAN_MANIFEST_INVALID"
    )
    try:
        runtime.validate(briefs, "h1-fragment-briefs.schema.json")
        runtime.validate(plan_manifest_value, "package-manifest.schema.json")
        rt.verify_manifest_integrity(plan_manifest_value, root=plan_root)
    except Exception as error:
        _fail("H1B_PLAN_MANIFEST_INVALID", str(error))
    plan_ref = rt.artifact_reference(
        plan_root / "review-plan.json", root=plan_root
    )
    if (
        plan.get("run_id") != inventory.get("run_id")
        or plan.get("h1_session_id") != initialized["session_id"]
        or plan.get("p1_completion") != p1_artifact
        or inventory.get("p1_completion") != p1_artifact
        or briefs
        != {
            "schema_version": "2.0",
            "run_id": plan["run_id"],
            "h1_session_id": plan["h1_session_id"],
            "p1_completion": p1_artifact,
            "review_plan": plan_ref,
            "briefs": plan["fragment_briefs"],
        }
        or plan_manifest_value.get("run_id") != plan["run_id"]
        or plan_manifest_value.get("stage") != "H1"
        or plan_manifest_value.get("package_profile") != "h1-plan"
        or plan_manifest_value.get("verdict") != "ready"
        or plan_manifest_value.get("session_id") != plan["h1_session_id"]
        or plan_manifest_value.get("parent_state_sha256")
        != plan_workspace_state.reference["sha256"]
    ):
        _fail("H1B_PLAN_INVALID", "plan lineage/projection")
    anchor_by_id = _validate_source_inventory(
        inventory, p1_root=p1_root
    )
    if (
        workspace.get("state") != "planned"
        or workspace.get("run_id") != plan["run_id"]
        or workspace.get("session_id") != plan["h1_session_id"]
        or workspace.get("p1_completion") != p1_stage
        or workspace.get("previous_state_sha256")
        != plan_workspace_state.reference["sha256"]
        or workspace.get("artifacts")
        != {"plan_manifest": plan_manifest}
        or rt.canonical_sha256(workspace)
        != workspace_state.reference.get("sha256")
    ):
        _fail(
            "H1B_WORKSPACE_INVALID",
            "H1-B requires exact same-session planned workspace",
        )
    for brief in plan["fragment_briefs"]:
        if (
            brief["language_contract_id"] != LANGUAGE_CONTRACT_ID
            or brief["style_contract_id"] != STYLE_CONTRACT_ID
            or brief.get("depth_contract_id") != DEPTH_CONTRACT_ID
            or brief["pov_mode"] != POV_MODE
            or brief["decisive_interiority_policy"] != INTERIORITY_POLICY
            or brief["surface_detail_policy"] != SURFACE_DETAIL_POLICY
            or set(brief["required_demonstrations"])
            & set(brief["forbidden_additions"])
        ):
            _fail("H1B_BRIEF_CONFLICT", brief["id"])
        try:
            sources = [anchor_by_id[item] for item in brief["source_anchor_ids"]]
        except KeyError as error:
            _fail("H1B_SOURCE_GROUNDING_INVALID", str(error))
        if brief["pov_character_id"] not in {
            item["source_id"] for item in sources
        }:
            _fail(
                "H1B_SOURCE_GROUNDING_INVALID",
                f"{brief['id']} POV is not source-bound",
            )
    if (
        p1_before != _tree_inventory(p1_root)
        or plan_before != _tree_inventory(plan_root)
    ):
        _fail("H1B_INPUT_MUTATED", "upstream changed during admission")
    return {
        "p1_root": p1_root,
        "plan_root": plan_root,
        "p1_stage": p1_stage,
        "p1_artifact": p1_artifact,
        "plan": plan,
        "inventory": inventory,
        "briefs": plan["fragment_briefs"],
        "anchors": anchor_by_id,
        "plan_manifest": plan_manifest,
        "workspace": copy.deepcopy(workspace),
        "input_gate": copy.deepcopy(plan_input_gate.reference),
        "p1_tree": p1_before,
        "plan_tree": plan_before,
    }


def _validate_phase_order(
    submissions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if len(submissions) != len(PHASES):
        _fail("H1B_PHASE_ORDER_INVALID", "exactly three phases required")
    normalized: list[dict[str, Any]] = []
    for index, (phase, submission) in enumerate(zip(PHASES, submissions), 1):
        if (
            not isinstance(submission, Mapping)
            or set(submission) != {"phase", "phase_index", "payload"}
            or submission.get("phase") != phase
            or submission.get("phase_index") != index
            or not isinstance(submission.get("payload"), Mapping)
        ):
            _fail("H1B_PHASE_ORDER_INVALID", phase)
        normalized.append(copy.deepcopy(dict(submission)))
    return normalized


def _validate_phase_prefix(
    submissions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not 0 <= len(submissions) <= len(PHASES):
        _fail("H1B_PHASE_ORDER_INVALID", "phase prefix length")
    normalized: list[dict[str, Any]] = []
    for index, submission in enumerate(submissions, 1):
        phase = PHASES[index - 1]
        if (
            not isinstance(submission, Mapping)
            or set(submission) != {"phase", "phase_index", "payload"}
            or submission.get("phase") != phase
            or submission.get("phase_index") != index
            or not isinstance(submission.get("payload"), Mapping)
        ):
            _fail("H1B_PHASE_ORDER_INVALID", f"next phase is {phase}")
        normalized.append(copy.deepcopy(dict(submission)))
    return normalized


def _require_exact_keys(
    value: Any, keys: set[str], code: str, label: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(code, f"{label} fields")
    return value


def _quote(text: str, value: Any, code: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value not in text
    ):
        _fail(code, f"{label} is not exact final-text evidence")
    return value


def _visible_units(text: str) -> tuple[int, int, int]:
    """Return (combined, CJK chars, Latin word tokens) for zh-Hans v1."""

    cjk = len(
        re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text)
    )
    latin = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", text))
    return cjk + latin, cjk, latin


def _meaningful_scalar_tokens(value: str) -> set[str]:
    """Return a conservative lexical fingerprint, not a semantic proof."""

    tokens: set[str] = set()
    for run in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]{4,}", value):
        tokens.update(run[index : index + 4] for index in range(len(run) - 3))
    tokens.update(
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", value)
    )
    return tokens


def _generic_identity_tokens(anchor_value: Any) -> set[str]:
    if not isinstance(anchor_value, Mapping):
        return set()
    result: set[str] = set()
    for field in ("id", "name", "title", "label"):
        value = anchor_value.get(field)
        if isinstance(value, str) and value.strip():
            result.add(value.strip().casefold())
    return result


def _quote_has_non_identity_substance(
    quote: str, anchor_values: Sequence[Any]
) -> bool:
    reduced = quote.casefold()
    identity_tokens: set[str] = set()
    for anchor_value in anchor_values:
        identity_tokens.update(_generic_identity_tokens(anchor_value))
    for token in sorted(identity_tokens, key=len, reverse=True):
        reduced = reduced.replace(token, "")
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", reduced))
    latin = len(re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", reduced))
    return cjk >= 6 or latin >= 2


def _validate_text(text: Any, brief: Mapping[str, Any]) -> str:
    if not isinstance(text, str) or not text.strip():
        _fail("H1B_FRAGMENT_TEXT_INVALID", brief["slot_id"])
    count, cjk, _ = _visible_units(text)
    if not brief["target_words_min"] <= count <= brief["target_words_max"]:
        _fail(
            "H1B_FRAGMENT_LENGTH_INVALID",
            f"{brief['slot_id']} has {count} combined visible units",
        )
    if not count or cjk / count < MIN_CJK_UNIT_RATIO:
        _fail(
            "H1B_LANGUAGE_CONTRACT_INVALID",
            (
                f"{brief['slot_id']} CJK ratio {cjk / count:.3f} "
                f"is below {MIN_CJK_UNIT_RATIO:.2f}"
            ),
        )
    paragraphs = [item.strip() for item in text.splitlines() if item.strip()]
    if (
        len(paragraphs) < 5
        or len(re.findall(r"[。！？!?]", text)) < 10
        or _NON_PROSE.search(text)
        or text.count("！") + text.count("!") > 2
        or "正文终稿" in text
        or "最终章节" in text
    ):
        _fail("H1B_FRAGMENT_TEXT_INVALID", brief["slot_id"])
    if _DECISIVE_INTERIORITY.search(text):
        _fail("H1B_DECISIVE_INNER_REVELATION", brief["slot_id"])
    return text


def _validate_contracts(
    contracts: Any,
    *,
    briefs: Sequence[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, dict[str, Any]]],
]:
    if not isinstance(contracts, list) or len(contracts) != len(briefs):
        _fail("H1B_FRAGMENT_COVERAGE_INVALID", "brief contracts")
    normalized: list[dict[str, Any]] = []
    projections_by_brief: dict[str, dict[str, dict[str, Any]]] = {}
    keys = {
        "brief_id",
        "slot_id",
        "brief_sha256",
        "title",
        "review_purpose",
        "language_contract_id",
        "style_contract_id",
        "depth_contract_id",
        "pov_mode",
        "pov_character_id",
        "information_limits",
        "allowed_perception_channels",
        "scene_contract",
        "decisive_interiority_policy",
        "surface_detail_policy",
        "target_chars_min",
        "target_chars_max",
        "source_challenges",
        "required_demonstrations",
        "forbidden_additions",
        "opposition_challenge",
        "narrative_scene_design",
    }
    for contract, brief in zip(contracts, briefs):
        item = _require_exact_keys(
            contract, keys, "H1B_BRIEF_CONTRACT_INVALID", brief["id"]
        )
        source_challenges = item["source_challenges"]
        expected_anchor_ids = brief["source_anchor_ids"]
        if (
            item["brief_id"] != brief["id"]
            or item["slot_id"] != brief["slot_id"]
            or item["brief_sha256"] != rt.canonical_sha256(brief)
            or item["title"] != brief["title"]
            or item["review_purpose"] != brief["review_purpose"]
            or item["language_contract_id"] != LANGUAGE_CONTRACT_ID
            or item["style_contract_id"] != STYLE_CONTRACT_ID
            or item["depth_contract_id"] != DEPTH_CONTRACT_ID
            or item["pov_mode"] != POV_MODE
            or item["pov_character_id"] != brief["pov_character_id"]
            or item["information_limits"] != brief["information_limits"]
            or item["allowed_perception_channels"]
            != brief["allowed_perception_channels"]
            or item["scene_contract"] != brief["scene_contract"]
            or item["decisive_interiority_policy"] != INTERIORITY_POLICY
            or item["surface_detail_policy"] != SURFACE_DETAIL_POLICY
            or item["target_chars_min"] != brief["target_words_min"]
            or item["target_chars_max"] != brief["target_words_max"]
            or item["required_demonstrations"]
            != brief["required_demonstrations"]
            or item["forbidden_additions"] != brief["forbidden_additions"]
            or not isinstance(source_challenges, list)
            or len(source_challenges) != len(expected_anchor_ids)
        ):
            _fail("H1B_BRIEF_CONTRACT_INVALID", brief["id"])
        brief_projections: dict[str, dict[str, Any]] = {}
        for challenge, anchor_id in zip(
            source_challenges, expected_anchor_ids
        ):
            _require_exact_keys(
                challenge,
                {
                    "source_anchor_id",
                    "value_sha256",
                    "story_specific_use",
                    "does_not_authorize",
                    "fact_projections",
                },
                "H1B_SOURCE_GROUNDING_INVALID",
                anchor_id,
            )
            if (
                challenge["source_anchor_id"] != anchor_id
                or challenge["value_sha256"]
                != anchors[anchor_id]["value_sha256"]
                or not isinstance(challenge["story_specific_use"], str)
                or not challenge["story_specific_use"].strip()
                or not isinstance(challenge["does_not_authorize"], str)
                or not challenge["does_not_authorize"].strip()
                or not isinstance(challenge["fact_projections"], list)
                or not challenge["fact_projections"]
            ):
                _fail("H1B_SOURCE_GROUNDING_INVALID", anchor_id)
            for projection in challenge["fact_projections"]:
                _require_exact_keys(
                    projection,
                    {
                        "id",
                        "field_pointer",
                        "value_sha256",
                        "required_usage",
                    },
                    "H1B_FACT_PROJECTION_INVALID",
                    anchor_id,
                )
                projection_id = projection["id"]
                pointer = projection["field_pointer"]
                if (
                    not isinstance(projection_id, str)
                    or not projection_id.strip()
                    or projection_id in brief_projections
                    or not isinstance(pointer, str)
                    or not pointer.startswith("/")
                    or pointer.rsplit("/", 1)[-1].casefold()
                    in {"id", "name", "title", "label"}
                    or not isinstance(projection["required_usage"], str)
                    or not projection["required_usage"].strip()
                ):
                    _fail("H1B_FACT_PROJECTION_INVALID", anchor_id)
                value = _resolve_pointer(anchors[anchor_id]["_value"], pointer)
                if isinstance(value, (dict, list)) or value is None:
                    _fail(
                        "H1B_FACT_PROJECTION_INVALID",
                        f"{projection_id} must select a non-null scalar",
                    )
                value_hash = rt.canonical_sha256(value)
                if projection["value_sha256"] != value_hash:
                    _fail(
                        "H1B_FACT_PROJECTION_INVALID",
                        f"{projection_id} value drift",
                    )
                brief_projections[projection_id] = {
                    **copy.deepcopy(dict(projection)),
                    "source_anchor_id": anchor_id,
                    "source_value_sha256": anchors[anchor_id][
                        "value_sha256"
                    ],
                    "_value": copy.deepcopy(value),
                    "_anchor_value": anchors[anchor_id]["_value"],
                }
        opposition = _require_exact_keys(
            item["opposition_challenge"],
            {"verdict", "evidence"},
            "H1B_BRIEF_CONFLICT",
            brief["id"],
        )
        if (
            opposition["verdict"] != "compatible"
            or not isinstance(opposition["evidence"], str)
            or not opposition["evidence"].strip()
            or set(brief["required_demonstrations"])
            & set(brief["forbidden_additions"])
        ):
            _fail("H1B_BRIEF_CONFLICT", brief["id"])
        design = _require_exact_keys(
            item["narrative_scene_design"],
            {
                "carry_in",
                "surface_want",
                "counterwant_or_fear",
                "interpretive_bias",
                "protective_tactic",
                "contradiction_under_pressure",
                "relationship_or_system_pressure",
                "beat_progression",
                "turning_pressure",
                "choice_cost",
                "aftershock",
                "source_anchor_ids",
            },
            "H1B_NARRATIVE_DEPTH_INVALID",
            brief["id"],
        )
        design_text_fields = {
            "carry_in",
            "surface_want",
            "counterwant_or_fear",
            "interpretive_bias",
            "protective_tactic",
            "contradiction_under_pressure",
            "relationship_or_system_pressure",
            "turning_pressure",
            "choice_cost",
            "aftershock",
        }
        beats = design["beat_progression"]
        if (
            any(
                not isinstance(design[field], str)
                or len(design[field].strip()) < 4
                for field in design_text_fields
            )
            or not isinstance(beats, list)
            or not 5 <= len(beats) <= 10
            or len(beats) != len(set(beats))
            or any(not isinstance(beat, str) or len(beat.strip()) < 6 for beat in beats)
            or design["source_anchor_ids"] != brief["source_anchor_ids"]
        ):
            _fail("H1B_NARRATIVE_DEPTH_INVALID", brief["id"])
        normalized.append(copy.deepcopy(dict(item)))
        projections_by_brief[brief["id"]] = brief_projections
    return normalized, projections_by_brief


def _validate_drafts(
    drafts: Any,
    *,
    briefs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(drafts, list) or len(drafts) != len(briefs):
        _fail("H1B_FRAGMENT_COVERAGE_INVALID", "drafts")
    keys = {
        "id",
        "brief_sha256",
        "title",
        "review_purpose",
        "text",
        "source_anchor_ids",
        "surface_details",
        "introduced_control_facts",
    }
    normalized: list[dict[str, Any]] = []
    for draft, brief in zip(drafts, briefs):
        item = _require_exact_keys(
            draft, keys, "H1B_DRAFT_INVALID", brief["slot_id"]
        )
        if (
            item["id"] != brief["slot_id"]
            or item["brief_sha256"] != rt.canonical_sha256(brief)
            or item["title"] != brief["title"]
            or item["review_purpose"] != brief["review_purpose"]
            or item["source_anchor_ids"] != brief["source_anchor_ids"]
            or not isinstance(item["surface_details"], list)
        ):
            _fail("H1B_DRAFT_INVALID", brief["slot_id"])
        if item["introduced_control_facts"] != []:
            _fail("H1B_NEW_CONTROL_FACT", brief["slot_id"])
        _validate_text(item["text"], brief)
        normalized.append(copy.deepcopy(dict(item)))
    return normalized


def _validate_surface_details(
    details: Any, *, text: str, fragment_id: str
) -> None:
    if not isinstance(details, list):
        _fail("H1B_SURFACE_DETAIL_INVALID", fragment_id)
    for detail in details:
        _require_exact_keys(
            detail,
            {
                "id",
                "detail",
                "evidence_quote",
                "authority_status",
                "control_effect",
                "scope",
                "causal_role",
                "history_claim",
                "rule_claim",
                "relationship_claim",
                "reused_across_fragments",
            },
            "H1B_SURFACE_DETAIL_INVALID",
            fragment_id,
        )
        if (
            not isinstance(detail["id"], str)
            or not detail["id"].strip()
            or not isinstance(detail["detail"], str)
            or not detail["detail"].strip()
            or detail["authority_status"]
            != "fragment_local_non_authoritative"
            or detail["control_effect"] != "none"
            or detail["scope"] != "fragment_only"
            or detail["causal_role"] != "none"
            or detail["history_claim"] is not False
            or detail["rule_claim"] is not False
            or detail["relationship_claim"] is not False
            or detail["reused_across_fragments"] is not False
        ):
            _fail("H1B_SURFACE_DETAIL_INVALID", fragment_id)
        _quote(
            text,
            detail["evidence_quote"],
            "H1B_SURFACE_DETAIL_INVALID",
            fragment_id,
        )


def _validate_compliance(
    reviews: Any,
    *,
    briefs: Sequence[Mapping[str, Any]],
    drafts: Sequence[Mapping[str, Any]],
    final_fragments: Sequence[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
    projections_by_brief: Mapping[
        str, Mapping[str, Mapping[str, Any]]
    ],
) -> list[dict[str, Any]]:
    if not isinstance(reviews, list) or len(reviews) != len(briefs):
        _fail("H1B_FRAGMENT_COVERAGE_INVALID", "compliance reviews")
    keys = {
        "fragment_id",
        "brief_sha256",
        "draft_sha256",
        "text_sha256",
        "fact_projection_ledger",
        "required_demonstrations",
        "forbidden_additions",
        "information_boundary",
        "scene_contract_evidence",
        "style_checks",
        "narrative_quality_checks",
        "boundary_checks",
        "surface_details",
    }
    normalized: list[dict[str, Any]] = []
    scene_fields = (
        "before_state",
        "immediate_goal",
        "pressure",
        "obstacle",
        "required_choice",
        "direct_consequence",
        "after_state",
    )
    for review, brief, draft, final in zip(
        reviews, briefs, drafts, final_fragments
    ):
        item = _require_exact_keys(
            review, keys, "H1B_COMPLIANCE_INVALID", brief["slot_id"]
        )
        text = final["text"]
        if (
            item["fragment_id"] != brief["slot_id"]
            or item["brief_sha256"] != rt.canonical_sha256(brief)
            or item["draft_sha256"] != rt.canonical_sha256(draft["text"])
            or item["text_sha256"] != rt.canonical_sha256(text)
        ):
            _fail("H1B_COMPLIANCE_INVALID", brief["slot_id"])
        projections = projections_by_brief[brief["id"]]
        fact_uses = item["fact_projection_ledger"]
        if (
            not isinstance(fact_uses, list)
            or [entry.get("fact_projection_id") for entry in fact_uses]
            != list(projections)
        ):
            _fail("H1B_SOURCE_GROUNDING_INVALID", brief["slot_id"])
        for fact_use, (projection_id, projection) in zip(
            fact_uses, projections.items()
        ):
            anchor_id = projection["source_anchor_id"]
            _require_exact_keys(
                fact_use,
                {
                    "fact_projection_id",
                    "source_anchor_id",
                    "source_value_sha256",
                    "field_value_sha256",
                    "story_specific_claim",
                    "evidence_quote",
                    "evidence_quote_sha256",
                    "challenge_result",
                    "challenge_notes",
                    "control_status",
                },
                "H1B_SOURCE_GROUNDING_INVALID",
                anchor_id,
            )
            if (
                fact_use["fact_projection_id"] != projection_id
                or fact_use["source_anchor_id"] != anchor_id
                or fact_use["source_value_sha256"]
                != projection["source_value_sha256"]
                or fact_use["field_value_sha256"]
                != projection["value_sha256"]
                or not isinstance(fact_use["story_specific_claim"], str)
                or not fact_use["story_specific_claim"].strip()
                or not isinstance(fact_use["challenge_notes"], str)
                or len(fact_use["challenge_notes"].strip()) < 12
                or fact_use["control_status"] != "preserved"
            ):
                _fail("H1B_SOURCE_GROUNDING_INVALID", anchor_id)
            evidence_quote = _quote(
                text,
                fact_use["evidence_quote"],
                "H1B_SOURCE_GROUNDING_INVALID",
                anchor_id,
            )
            if fact_use["evidence_quote_sha256"] != rt.canonical_sha256(
                evidence_quote
            ):
                _fail("H1B_SOURCE_GROUNDING_INVALID", anchor_id)
            source_value = projection["_value"]
            if not _quote_has_non_identity_substance(
                evidence_quote,
                [anchor["_value"] for anchor in anchors.values()],
            ):
                _fail(
                    "H1B_GENERIC_SOURCE_EVIDENCE",
                    f"{brief['slot_id']}:{projection_id}",
                )
            lexical = (
                isinstance(source_value, str)
                and bool(
                    _meaningful_scalar_tokens(source_value)
                    & _meaningful_scalar_tokens(evidence_quote)
                )
            )
            result = fact_use["challenge_result"]
            if lexical:
                if result not in {
                    "lexically_grounded",
                    "agent_verified_paraphrase",
                }:
                    _fail("H1B_SOURCE_GROUNDING_INVALID", projection_id)
            elif isinstance(source_value, str):
                if result != "agent_verified_paraphrase":
                    _fail("H1B_SOURCE_GROUNDING_INVALID", projection_id)
            elif result != "agent_verified_non_string":
                _fail("H1B_SOURCE_GROUNDING_INVALID", projection_id)
        demonstrations = item["required_demonstrations"]
        if (
            not isinstance(demonstrations, list)
            or [entry.get("requirement") for entry in demonstrations]
            != brief["required_demonstrations"]
        ):
            _fail("H1B_BRIEF_COMPLIANCE_INVALID", brief["slot_id"])
        for demonstration in demonstrations:
            _require_exact_keys(
                demonstration,
                {
                    "requirement",
                    "fact_projection_ids",
                    "finding",
                    "evidence_quote",
                },
                "H1B_BRIEF_COMPLIANCE_INVALID",
                brief["slot_id"],
            )
            if (
                not isinstance(demonstration["fact_projection_ids"], list)
                or not demonstration["fact_projection_ids"]
                or not set(demonstration["fact_projection_ids"])
                <= set(projections)
                or not isinstance(demonstration["finding"], str)
                or not demonstration["finding"].strip()
            ):
                _fail("H1B_BRIEF_COMPLIANCE_INVALID", brief["slot_id"])
            _quote(
                text,
                demonstration["evidence_quote"],
                "H1B_BRIEF_COMPLIANCE_INVALID",
                brief["slot_id"],
            )
        prohibited = item["forbidden_additions"]
        if (
            not isinstance(prohibited, list)
            or [entry.get("prohibition") for entry in prohibited]
            != brief["forbidden_additions"]
        ):
            _fail("H1B_BRIEF_COMPLIANCE_INVALID", brief["slot_id"])
        for check in prohibited:
            _require_exact_keys(
                check,
                {"prohibition", "verdict", "check_notes"},
                "H1B_BRIEF_COMPLIANCE_INVALID",
                brief["slot_id"],
            )
            if (
                check["verdict"] != "absent"
                or not isinstance(check["check_notes"], str)
                or not check["check_notes"].strip()
            ):
                _fail("H1B_BRIEF_COMPLIANCE_INVALID", brief["slot_id"])
        information = _require_exact_keys(
            item["information_boundary"],
            {
                "may_present",
                "must_not_present_as_known",
                "used_perception_channels",
                "evidence_quotes",
                "verdict",
            },
            "H1B_INFORMATION_BOUNDARY_INVALID",
            brief["slot_id"],
        )
        used_channels = information["used_perception_channels"]
        if (
            information["may_present"]
            != brief["information_limits"]["may_present"]
            or information["must_not_present_as_known"]
            != brief["information_limits"]["must_not_present_as_known"]
            or not isinstance(used_channels, list)
            or not set(used_channels)
            <= set(brief["allowed_perception_channels"])
            or information["verdict"] != "passed"
            or not isinstance(information["evidence_quotes"], list)
            or not information["evidence_quotes"]
        ):
            _fail(
                "H1B_INFORMATION_BOUNDARY_INVALID", brief["slot_id"]
            )
        for evidence_quote in information["evidence_quotes"]:
            _quote(
                text,
                evidence_quote,
                "H1B_INFORMATION_BOUNDARY_INVALID",
                brief["slot_id"],
            )
        scene_evidence = item["scene_contract_evidence"]
        if (
            not isinstance(scene_evidence, list)
            or [entry.get("field") for entry in scene_evidence]
            != list(scene_fields)
        ):
            _fail("H1B_SCENE_CONTRACT_INVALID", brief["slot_id"])
        for evidence, field in zip(scene_evidence, scene_fields):
            _require_exact_keys(
                evidence,
                {"field", "expected_value", "finding", "evidence_quote"},
                "H1B_SCENE_CONTRACT_INVALID",
                brief["slot_id"],
            )
            if (
                evidence["expected_value"]
                != brief["scene_contract"][field]
                or not isinstance(evidence["finding"], str)
                or not evidence["finding"].strip()
            ):
                _fail("H1B_SCENE_CONTRACT_INVALID", brief["slot_id"])
            _quote(
                text,
                evidence["evidence_quote"],
                "H1B_SCENE_CONTRACT_INVALID",
                brief["slot_id"],
            )
        if item["style_checks"] != {
            principle: True for principle in STYLE_PRINCIPLES
        }:
            _fail("H1B_STYLE_INVALID", brief["slot_id"])
        quality_checks = item["narrative_quality_checks"]
        if (
            not isinstance(quality_checks, list)
            or [entry.get("principle") for entry in quality_checks]
            != list(NARRATIVE_QUALITY_PRINCIPLES)
        ):
            _fail("H1B_NARRATIVE_DEPTH_INVALID", brief["slot_id"])
        evidence_signatures: set[tuple[str, ...]] = set()
        for quality in quality_checks:
            _require_exact_keys(
                quality,
                {"principle", "finding", "evidence_quotes"},
                "H1B_NARRATIVE_DEPTH_INVALID",
                brief["slot_id"],
            )
            quotes = quality["evidence_quotes"]
            if (
                not isinstance(quality["finding"], str)
                or len(quality["finding"].strip()) < 12
                or not isinstance(quotes, list)
                or len(quotes) != 2
                or len(quotes) != len(set(quotes))
                or any(not isinstance(quote, str) or len(quote.strip()) < 4 for quote in quotes)
                or tuple(quotes) in evidence_signatures
            ):
                _fail("H1B_NARRATIVE_DEPTH_INVALID", brief["slot_id"])
            evidence_signatures.add(tuple(quotes))
            for quote in quotes:
                _quote(
                    text,
                    quote,
                    "H1B_NARRATIVE_DEPTH_INVALID",
                    brief["slot_id"],
                )
        boundary = _require_exact_keys(
            item["boundary_checks"],
            {
                "language_contract_id",
                "style_contract_id",
                "pov_mode",
                "pov_character_id",
                "decisive_interiority_policy",
                "surface_detail_policy",
                "choice_evidence_quote",
                "consequence_evidence_quote",
                "state_change_evidence_quote",
                "decisive_inner_revelation",
                "introduced_control_facts",
                "final_prose_claim",
            },
            "H1B_BOUNDARY_INVALID",
            brief["slot_id"],
        )
        if (
            boundary["language_contract_id"] != LANGUAGE_CONTRACT_ID
            or boundary["style_contract_id"] != STYLE_CONTRACT_ID
            or boundary["pov_mode"] != POV_MODE
            or boundary["pov_character_id"] != brief["pov_character_id"]
            or boundary["decisive_interiority_policy"]
            != INTERIORITY_POLICY
            or boundary["surface_detail_policy"] != SURFACE_DETAIL_POLICY
            or boundary["decisive_inner_revelation"] is not False
            or boundary["introduced_control_facts"] != []
            or boundary["final_prose_claim"] is not False
        ):
            if boundary.get("decisive_inner_revelation") is True:
                _fail(
                    "H1B_DECISIVE_INNER_REVELATION", brief["slot_id"]
                )
            if boundary.get("introduced_control_facts") != []:
                _fail("H1B_NEW_CONTROL_FACT", brief["slot_id"])
            _fail("H1B_BOUNDARY_INVALID", brief["slot_id"])
        for field in (
            "choice_evidence_quote",
            "consequence_evidence_quote",
            "state_change_evidence_quote",
        ):
            _quote(
                text,
                boundary[field],
                "H1B_BOUNDARY_INVALID",
                f"{brief['slot_id']}.{field}",
            )
        if item["surface_details"] != final["surface_details"]:
            _fail("H1B_SURFACE_DETAIL_INVALID", brief["slot_id"])
        _validate_surface_details(
            item["surface_details"],
            text=text,
            fragment_id=brief["slot_id"],
        )
        normalized.append(copy.deepcopy(dict(item)))
    return normalized


def _validate_agent_submissions(
    submissions: Sequence[Mapping[str, Any]],
    *,
    briefs: Sequence[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    phases = _validate_phase_order(submissions)
    if set(phases[0]["payload"]) != {"brief_contracts"}:
        _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[0])
    if set(phases[1]["payload"]) != {"drafts"}:
        _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[1])
    if set(phases[2]["payload"]) != {
        "final_fragments",
        "compliance_reviews",
    }:
        _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[2])
    contracts, projections_by_brief = _validate_contracts(
        phases[0]["payload"]["brief_contracts"],
        briefs=briefs,
        anchors=anchors,
    )
    drafts = _validate_drafts(
        phases[1]["payload"]["drafts"], briefs=briefs
    )
    final_fragments = _validate_drafts(
        phases[2]["payload"]["final_fragments"], briefs=briefs
    )
    reviews = _validate_compliance(
        phases[2]["payload"]["compliance_reviews"],
        briefs=briefs,
        drafts=drafts,
        final_fragments=final_fragments,
        anchors=anchors,
        projections_by_brief=projections_by_brief,
    )
    seen_surface_ids: set[str] = set()
    seen_surface_claims: set[str] = set()
    for fragment in final_fragments:
        for detail in fragment["surface_details"]:
            detail_id = detail["id"]
            claim = re.sub(r"\s+", "", detail["detail"]).casefold()
            if (
                detail_id in seen_surface_ids
                or claim in seen_surface_claims
            ):
                _fail(
                    "H1B_SURFACE_DETAIL_REUSED",
                    f"{fragment['id']}:{detail_id}",
                )
            seen_surface_ids.add(detail_id)
            seen_surface_claims.add(claim)
    return phases, contracts, final_fragments, reviews


def _validate_partial_submissions(
    submissions: Sequence[Mapping[str, Any]],
    *,
    briefs: Sequence[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    phases = _validate_phase_prefix(submissions)
    if not phases:
        return phases
    if set(phases[0]["payload"]) != {"brief_contracts"}:
        _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[0])
    _, projections_by_brief = _validate_contracts(
        phases[0]["payload"]["brief_contracts"],
        briefs=briefs,
        anchors=anchors,
    )
    if len(phases) >= 2:
        if set(phases[1]["payload"]) != {"drafts"}:
            _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[1])
        drafts = _validate_drafts(
            phases[1]["payload"]["drafts"], briefs=briefs
        )
    if len(phases) == 3:
        if set(phases[2]["payload"]) != {
            "final_fragments",
            "compliance_reviews",
        }:
            _fail("H1B_PHASE_PAYLOAD_INVALID", PHASES[2])
        final_fragments = _validate_drafts(
            phases[2]["payload"]["final_fragments"], briefs=briefs
        )
        _validate_compliance(
            phases[2]["payload"]["compliance_reviews"],
            briefs=briefs,
            drafts=drafts,
            final_fragments=final_fragments,
            anchors=anchors,
            projections_by_brief=projections_by_brief,
        )
        seen_ids: set[str] = set()
        seen_claims: set[str] = set()
        for fragment in final_fragments:
            for detail in fragment["surface_details"]:
                claim = re.sub(r"\s+", "", detail["detail"]).casefold()
                if detail["id"] in seen_ids or claim in seen_claims:
                    _fail(
                        "H1B_SURFACE_DETAIL_REUSED",
                        f"{fragment['id']}:{detail['id']}",
                    )
                seen_ids.add(detail["id"])
                seen_claims.add(claim)
    return phases


def _source_ids(
    anchor_ids: Sequence[str], anchors: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    return sorted({anchors[item]["source_id"] for item in anchor_ids})


def _fragment_package(
    *,
    plan: Mapping[str, Any],
    p1_artifact: Mapping[str, str],
    plan_manifest: Mapping[str, str],
    final_fragments: Sequence[Mapping[str, Any]],
    anchors: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    briefs_by_slot = {
        brief["slot_id"]: brief for brief in plan["fragment_briefs"]
    }
    return {
        "schema_version": "2.0",
        "run_id": plan["run_id"],
        "h1_session_id": plan["h1_session_id"],
        "p1_completion": copy.deepcopy(dict(p1_artifact)),
        "plan_manifest": copy.deepcopy(dict(plan_manifest)),
        "fragments": [
            {
                "id": item["id"],
                "title": item["title"],
                "review_purpose": item["review_purpose"],
                "text": item["text"],
                "source_ids": _source_ids(
                    item["source_anchor_ids"], anchors
                ),
                "decision_control_ids": copy.deepcopy(
                    briefs_by_slot[item["id"]]["decision_control_ids"]
                ),
            }
            for item in final_fragments
        ],
        "authority_status": "non_authoritative_sample",
    }


def _render_markdown(package: Mapping[str, Any]) -> str:
    lines = [
        "# 小说构思评审片段",
        "",
        "> 非权威场景样片；仅用于检验构思阅读体验。",
        "",
    ]
    for fragment in package["fragments"]:
        lines.extend(
            [
                f"## {fragment['title']}",
                "",
                f"评审用途：{fragment['review_purpose']}",
                "",
                fragment["text"],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _validation(run_id: str, session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "H1",
        "operation": "H1-B",
        "session_id": session_id,
        "verdict": "ready",
        "checks": [
            "current-P1-plan-briefs-and-planned-workspace",
            "controlled-three-phase-generation",
            "fixed-language-style-and-limited-POV",
            "combined-visible-unit-budget-and-cjk-ratio",
            "exact-brief-source-value-and-final-text-evidence",
            "no-new-control-facts-or-decisive-interiority",
            "non-authoritative-surface-details",
            "manifest-implementation-and-transaction-binding",
        ],
        "errors": [],
    }


def _skill_profile() -> list[dict[str, str]]:
    return [
        {"identity": identity, "sha256": rt.sha256_file(path)}
        for identity, path in sorted(_implementation_paths().items())
    ]


def _session_identifier(
    *,
    identity: Mapping[str, str],
    p1_completion: Mapping[str, str],
    plan_manifest: Mapping[str, str],
    plan_input_gate: Mapping[str, str],
    plan_workspace_state: Mapping[str, str],
    workspace_state: Mapping[str, str],
    skill_profile: Sequence[Mapping[str, str]],
) -> str:
    return "H1B-" + rt.canonical_sha256(
        [
            identity,
            p1_completion,
            plan_manifest,
            plan_input_gate,
            plan_workspace_state,
            workspace_state,
            skill_profile,
        ]
    )[:24]


def _session_document(
    *,
    upstream: Mapping[str, Any],
    identity: Mapping[str, str],
    plan_workspace_state: Any,
    workspace_state: Any,
) -> dict[str, Any]:
    profile = _skill_profile()
    session_id = _session_identifier(
        identity=identity,
        p1_completion=upstream["p1_stage"],
        plan_manifest=upstream["plan_manifest"],
        plan_input_gate=upstream["input_gate"],
        plan_workspace_state=plan_workspace_state.reference,
        workspace_state=workspace_state.reference,
        skill_profile=profile,
    )
    return {
        "schema_version": "2.0",
        "run_id": upstream["plan"]["run_id"],
        "h1_session_id": upstream["plan"]["h1_session_id"],
        "operation": "controlled-H1-B",
        "session_id": session_id,
        "identity": copy.deepcopy(dict(identity)),
        "phases": list(PHASES),
        "p1_completion": copy.deepcopy(upstream["p1_stage"]),
        "plan_manifest": copy.deepcopy(upstream["plan_manifest"]),
        "plan_input_gate": copy.deepcopy(upstream["input_gate"]),
        "plan_workspace_state": copy.deepcopy(
            plan_workspace_state.reference
        ),
        "workspace_state": copy.deepcopy(workspace_state.reference),
        "input_trees": {
            "p1": copy.deepcopy(upstream["p1_tree"]),
            "plan": copy.deepcopy(upstream["plan_tree"]),
        },
        "skill_profile": profile,
    }


def _initial_session_state(
    session: Mapping[str, Any], session_reference: Mapping[str, str]
) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "h1_session_id": session["h1_session_id"],
        "session_id": session["session_id"],
        "status": "active",
        "next_phase_index": 1,
        "completed_evidence": [],
        "session_reference": copy.deepcopy(dict(session_reference)),
        "previous_state_sha256": None,
        "forward_hash": rt.canonical_sha256(
            [session_reference, "H1-B-session-seed"]
        ),
    }


def _advanced_session_state(
    prior: Mapping[str, Any],
    evidence_reference: Mapping[str, str],
    *,
    phase_index: int,
) -> dict[str, Any]:
    completed = [
        *copy.deepcopy(prior["completed_evidence"]),
        copy.deepcopy(dict(evidence_reference)),
    ]
    return {
        "schema_version": "2.0",
        "run_id": prior["run_id"],
        "h1_session_id": prior["h1_session_id"],
        "session_id": prior["session_id"],
        "status": (
            "completed" if phase_index == len(PHASES) else "active"
        ),
        "next_phase_index": phase_index + 1,
        "completed_evidence": completed,
        "session_reference": copy.deepcopy(prior["session_reference"]),
        "previous_state_sha256": rt.canonical_sha256(prior),
        "forward_hash": rt.canonical_sha256(
            [
                prior["forward_hash"],
                evidence_reference,
                phase_index,
            ]
        ),
    }


def _check_session_boundary(root: Path) -> None:
    allowed_evidence = {
        f"{index:02d}-{phase}.json"
        for index, phase in enumerate(PHASES, 1)
    }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _SESSION_FILES:
            continue
        if (
            relative.startswith("generation-evidence/")
            and Path(relative).name in allowed_evidence
        ):
            continue
        _fail("H1B_SESSION_WORKSPACE_INVALID", relative)


def _session_evidence_document(
    *,
    session: Mapping[str, Any],
    state: Mapping[str, Any],
    submission: Mapping[str, Any],
    prior_evidence: Mapping[str, str] | None,
) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "h1_session_id": session["h1_session_id"],
        "operation": "controlled-H1-B",
        "session_id": session["session_id"],
        "identity": copy.deepcopy(session["identity"]),
        "phase": submission["phase"],
        "phase_index": submission["phase_index"],
        "pre_state_sha256": rt.canonical_sha256(state),
        "previous_evidence": copy.deepcopy(prior_evidence),
        "plan_manifest": copy.deepcopy(session["plan_manifest"]),
        "plan_input_gate": copy.deepcopy(session["plan_input_gate"]),
        "workspace_state": copy.deepcopy(session["workspace_state"]),
        "payload": copy.deepcopy(submission["payload"]),
        "payload_sha256": rt.canonical_sha256(submission["payload"]),
    }


def _validate_session_chain(
    root: Path,
    *,
    session: Mapping[str, Any],
    upstream: Mapping[str, Any],
    plan_workspace_state: Any,
    workspace_state: Any,
    require_complete: bool,
    state_filename: str = "session-state.json",
    enforce_current_identity: bool = True,
    check_boundary: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if check_boundary:
        _check_session_boundary(root)
    identity = session.get("identity")
    if (
        not isinstance(identity, Mapping)
        or set(identity) != {"task_id", "thread_id"}
        or not all(
            isinstance(identity.get(field), str)
            and identity[field].strip()
            for field in ("task_id", "thread_id")
        )
    ):
        _fail("H1B_SESSION_INVALID", "controlled identity is invalid")
    session_path = root / "generation-session.json"
    session_reference = rt.artifact_reference(session_path, root=root)
    expected_session = _session_document(
        upstream=upstream,
        identity=(
            _identity()
            if enforce_current_identity
            else session.get("identity", {})
        ),
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
    )
    if session != expected_session:
        _fail(
            "H1B_SESSION_INVALID",
            "session no longer binds identity, inputs, or skill profile",
        )
    state = _read(
        root / state_filename, "H1B_SESSION_STATE_INVALID"
    )
    completed = state.get("completed_evidence")
    if (
        not isinstance(completed, list)
        or len(completed) > len(PHASES)
    ):
        _fail("H1B_SESSION_STATE_INVALID", "completed evidence")
    actual_files = sorted(
        path.name
        for path in (root / "generation-evidence").glob("*.json")
        if path.is_file()
    )
    expected_files = [
        f"{index:02d}-{PHASES[index-1]}.json"
        for index in range(1, len(completed) + 1)
    ]
    if actual_files != expected_files:
        _fail(
            "H1B_EVIDENCE_INVALID",
            "evidence cannot be missing, repeated, or backfilled",
        )
    reconstructed = _initial_session_state(session, session_reference)
    submissions: list[dict[str, Any]] = []
    prior_reference = None
    for index, phase in enumerate(PHASES[: len(completed)], 1):
        path = root / "generation-evidence" / f"{index:02d}-{phase}.json"
        evidence = _read(path, "H1B_EVIDENCE_INVALID")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("H1B_EVIDENCE_INVALID", phase)
        submission = {
            "phase": phase,
            "phase_index": index,
            "payload": copy.deepcopy(dict(payload)),
        }
        expected = _session_evidence_document(
            session=session,
            state=reconstructed,
            submission=submission,
            prior_evidence=prior_reference,
        )
        reference = rt.artifact_reference(path, root=root)
        if (
            evidence != expected
            or completed[index - 1] != reference
        ):
            _fail("H1B_EVIDENCE_INVALID", f"{phase} chain drift")
        submissions.append(submission)
        reconstructed = _advanced_session_state(
            reconstructed, reference, phase_index=index
        )
        prior_reference = reference
    _validate_partial_submissions(
        submissions,
        briefs=upstream["briefs"],
        anchors=upstream["anchors"],
    )
    if state != reconstructed:
        _fail("H1B_SESSION_STATE_INVALID", "forward state seal drift")
    if require_complete and (
        state["status"] != "completed"
        or state["next_phase_index"] != len(PHASES) + 1
        or len(submissions) != len(PHASES)
    ):
        _fail("H1B_SESSION_INCOMPLETE", "three sealed phases required")
    return copy.deepcopy(state), submissions


def _validated_fragment_session(
    workspace_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    plan_active_return_request: Any | None,
    runtime: Any,
    require_complete: bool,
) -> tuple[Path, dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    root = Path(workspace_root).resolve()
    session = _read(
        root / "generation-session.json", "H1B_SESSION_INVALID"
    )
    if (
        session.get("input_trees", {}).get("p1")
        != _tree_inventory(Path(p1_package).resolve())
        or session.get("input_trees", {}).get("plan")
        != _tree_inventory(Path(plan_package).resolve())
    ):
        _fail("H1B_INPUT_MUTATED", "frozen input tree changed")
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        plan_active_return_request=plan_active_return_request,
        runtime=runtime,
    )
    state, submissions = _validate_session_chain(
        root,
        session=session,
        upstream=upstream,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        require_complete=require_complete,
    )
    return root, session, state, submissions, upstream


def start_fragment_session(
    workspace_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    plan_active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze formal inputs and controlled identity before phase one."""

    destination = Path(workspace_root).resolve()
    if destination.exists():
        _fail("H1B_SESSION_EXISTS", str(destination))
    contract_runtime = runtime or rt.ContractRuntime()
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    session = _session_document(
        upstream=upstream,
        identity=_identity(),
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.", dir=destination.parent
        )
    )
    staging = temp_parent / "session"
    staging.mkdir()
    try:
        _write_new(staging / "generation-session.json", session)
        session_reference = rt.artifact_reference(
            staging / "generation-session.json", root=staging
        )
        state = _initial_session_state(session, session_reference)
        _write_new(staging / "session-state.json", state)
        staging.replace(destination)
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return {
        "session": copy.deepcopy(session),
        "state": copy.deepcopy(state),
    }


def submit_fragment_phase(
    workspace_root: str | Path,
    submission: Mapping[str, Any],
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    plan_active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, str]:
    """Seal exactly the current phase and atomically advance state."""

    contract_runtime = runtime or rt.ContractRuntime()
    root, session, state, prior_submissions, upstream = (
        _validated_fragment_session(
            workspace_root,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            workspace_state=workspace_state,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
            require_complete=False,
        )
    )
    if state["status"] == "completed":
        _fail("H1B_PHASE_ORDER_INVALID", "all phases are sealed")
    candidate = copy.deepcopy(dict(submission))
    _validate_partial_submissions(
        [*prior_submissions, candidate],
        briefs=upstream["briefs"],
        anchors=upstream["anchors"],
    )
    index = state["next_phase_index"]
    phase = PHASES[index - 1]
    prior_reference = (
        state["completed_evidence"][-1]
        if state["completed_evidence"]
        else None
    )
    evidence = _session_evidence_document(
        session=session,
        state=state,
        submission=candidate,
        prior_evidence=prior_reference,
    )
    target = root / "generation-evidence" / f"{index:02d}-{phase}.json"
    if target.exists():
        _fail("H1B_EVIDENCE_EXISTS", str(target))
    pending = root / f".phase-{index}.pending"
    pending.mkdir()
    state_pending = pending / "session-state.json"
    evidence_pending = pending / "evidence.json"
    published_evidence = False
    try:
        _write_new(evidence_pending, evidence)
        evidence_reference = {
            "path": f"generation-evidence/{index:02d}-{phase}.json",
            "sha256": rt.sha256_file(evidence_pending),
        }
        advanced = _advanced_session_state(
            state, evidence_reference, phase_index=index
        )
        _write_new(state_pending, advanced)
        target.parent.mkdir(parents=True, exist_ok=True)
        evidence_pending.replace(target)
        published_evidence = True
        state_pending.replace(root / "session-state.json")
    except Exception:
        if published_evidence and target.is_file():
            target.unlink()
        shutil.rmtree(pending, ignore_errors=True)
        raise
    shutil.rmtree(pending, ignore_errors=True)
    return copy.deepcopy(evidence_reference)


def _check_boundary(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ROOT_FILES or any(
            relative.startswith(prefix) for prefix in _ROOT_PREFIXES
        ):
            continue
        _fail("H1B_PACKAGE_BOUNDARY_INVALID", relative)
    evidence = {
        path.name
        for path in (root / "generation-evidence").glob("*.json")
        if path.is_file()
    }
    expected = {
        f"{index:02d}-{phase}.json"
        for index, phase in enumerate(PHASES, 1)
    }
    if evidence != expected:
        _fail("H1B_PACKAGE_BOUNDARY_INVALID", "generation evidence")
    forbidden = {
        "scene-contracts.json",
        "writing-session.json",
        "revision-audit.json",
    }
    if any((root / name).exists() for name in forbidden):
        _fail("H1B_LEGACY_INPUT_FORBIDDEN", "legacy 1.x artifact")


def validate_fragment_package(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    plan_active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Formal H1-B validator called dynamically by H1-A assembly."""

    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_boundary(root)
    upstream = _validate_upstream(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    session = _read(
        root / "generation-session.json", "H1B_SESSION_INVALID"
    )
    completion, submissions = _validate_session_chain(
        root,
        session=session,
        upstream=upstream,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        require_complete=True,
        state_filename="session-workspace-completion.json",
        enforce_current_identity=False,
        check_boundary=False,
    )
    evidence_refs = copy.deepcopy(completion["completed_evidence"])
    phases, _, final_fragments, _ = _validate_agent_submissions(
        submissions,
        briefs=upstream["briefs"],
        anchors=upstream["anchors"],
    )
    index_value = _read(
        root / "generation-evidence-index.json",
        "H1B_EVIDENCE_INVALID",
    )
    if index_value != {
        "schema_version": "2.0",
        "run_id": upstream["plan"]["run_id"],
        "h1_session_id": upstream["plan"]["h1_session_id"],
        "phases": list(PHASES),
        "evidence": evidence_refs,
    }:
        _fail("H1B_EVIDENCE_INVALID", "index")
    expected_package = _fragment_package(
        plan=upstream["plan"],
        p1_artifact=upstream["p1_artifact"],
        plan_manifest=upstream["plan_manifest"],
        final_fragments=final_fragments,
        anchors=upstream["anchors"],
    )
    package = _read(
        root / "fragment-package.json", "H1B_FRAGMENT_PACKAGE_INVALID"
    )
    try:
        contract_runtime.validate(package, "fragment-package.schema.json")
    except Exception as error:
        _fail("H1B_FRAGMENT_PACKAGE_INVALID", str(error))
    if package != expected_package:
        _fail(
            "H1B_FRAGMENT_PACKAGE_INVALID",
            "package is not the sealed final Agent projection",
        )
    try:
        markdown = (root / "fragments.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        _fail("H1B_FRAGMENT_PACKAGE_INVALID", str(error))
    if markdown != _render_markdown(expected_package):
        _fail("H1B_FRAGMENT_PACKAGE_INVALID", "Markdown drift")
    execution = _read(
        root / "execution-record.json", "H1B_EXECUTION_INVALID"
    )
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping)
    }
    if set(catalog) != set(_implementation_paths()):
        _fail("H1B_IMPLEMENTATION_STALE", "implementation catalog")
    for implementation_id, source in _implementation_paths().items():
        reference = catalog[implementation_id]
        try:
            copied = rt.verify_artifact_reference(reference, root=root)
        except Exception as error:
            _fail("H1B_IMPLEMENTATION_STALE", str(error))
        if copied.read_bytes() != source.read_bytes():
            _fail("H1B_IMPLEMENTATION_STALE", implementation_id)
    implementation_refs = [catalog[key] for key in sorted(catalog)]
    expected_execution = {
        "schema_version": "2.0",
        "run_id": upstream["plan"]["run_id"],
        "stage": "H1",
        "operation": "controlled-H1-B",
        "h1_session_id": upstream["plan"]["h1_session_id"],
        "workspace_state": workspace_state.reference,
        "plan_input_gate": plan_input_gate.reference,
        "p1_completion": upstream["p1_stage"],
        "plan_manifest": upstream["plan_manifest"],
        "generation_session": rt.artifact_reference(
            root / "generation-session.json", root=root
        ),
        "session_workspace_completion": rt.artifact_reference(
            root / "session-workspace-completion.json", root=root
        ),
        "generation_evidence": evidence_refs,
        "outputs": {
            name: rt.artifact_reference(root / name, root=root)
            for name in ("fragment-package.json", "fragments.md")
        },
        "implementation": implementation_refs,
        "implementation_catalog": [
            {"identity": key, "artifact": catalog[key]}
            for key in sorted(catalog)
        ],
    }
    if execution != expected_execution:
        _fail("H1B_EXECUTION_INVALID", "execution binding")
    expected_validation = _validation(
        upstream["plan"]["run_id"], upstream["plan"]["h1_session_id"]
    )
    validation = _read(
        root / "validation.json", "H1B_VALIDATION_INVALID"
    )
    if validation != expected_validation:
        _fail("H1B_VALIDATION_INVALID", "validation drift")
    manifest = _read(
        root / "package-manifest.json", "H1B_MANIFEST_INVALID"
    )
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("H1B_MANIFEST_INVALID", str(error))
    actual_files = [
        reference
        for reference in _tree_inventory(root)
        if reference["path"] != "package-manifest.json"
    ]
    by_path = {item["path"]: item for item in actual_files}
    expected_roles = {
        "fragment_package": by_path["fragment-package.json"],
        "fragments": by_path["fragments.md"],
        "generation_session": by_path["generation-session.json"],
        "session_workspace_completion": by_path[
            "session-workspace-completion.json"
        ],
        "generation_evidence_index": by_path[
            "generation-evidence-index.json"
        ],
        "execution_record": by_path["execution-record.json"],
    }
    if (
        manifest.get("run_id") != upstream["plan"]["run_id"]
        or manifest.get("stage") != "H1"
        or manifest.get("package_profile") != "h1-fragments"
        or manifest.get("verdict") != "ready"
        or manifest.get("session_id")
        != upstream["plan"]["h1_session_id"]
        or manifest.get("parent_state_sha256")
        != workspace_state.reference["sha256"]
        or manifest.get("artifact_roles") != expected_roles
        or manifest.get("validation") != by_path["validation.json"]
        or manifest.get("implementation") != implementation_refs
        or manifest.get("files") != actual_files
    ):
        _fail("H1B_MANIFEST_INVALID", "manifest is not exact")
    return copy.deepcopy(validation)


def finalize_fragment_package(
    package_root: str | Path,
    *,
    session_workspace: str | Path,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    coordinator: Any,
    logical_package_path: str = "H1/fragments",
    plan_active_return_request: Any | None = None,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> FragmentReceipt:
    """Finalize only a completed, immutable H1-B session workspace."""

    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("H1B_OUTPUT_EXISTS", str(destination))
    contract_runtime = runtime or rt.ContractRuntime()
    session_root, session, completion, phases, upstream = (
        _validated_fragment_session(
            session_workspace,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            workspace_state=workspace_state,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
            require_complete=True,
        )
    )
    phases, _, final_fragments, _ = _validate_agent_submissions(
        phases,
        briefs=upstream["briefs"],
        anchors=upstream["anchors"],
    )
    p1_before = _tree_inventory(upstream["p1_root"])
    plan_before = _tree_inventory(upstream["plan_root"])
    session_before = _tree_inventory(session_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        _copy_exact(
            session_root / "generation-session.json",
            staging / "generation-session.json",
        )
        _copy_exact(
            session_root / "session-state.json",
            staging / "session-workspace-completion.json",
        )
        evidence_refs: list[dict[str, str]] = []
        for index, submission in enumerate(phases, 1):
            phase = submission["phase"]
            source = (
                session_root
                / "generation-evidence"
                / f"{index:02d}-{phase}.json"
            )
            path = (
                staging
                / "generation-evidence"
                / f"{index:02d}-{phase}.json"
            )
            _copy_exact(source, path)
            evidence_refs.append(
                rt.artifact_reference(path, root=staging)
            )
        _write_new(
            staging / "generation-evidence-index.json",
            {
                "schema_version": "2.0",
                "run_id": upstream["plan"]["run_id"],
                "h1_session_id": upstream["plan"]["h1_session_id"],
                "phases": list(PHASES),
                "evidence": evidence_refs,
            },
        )
        package = _fragment_package(
            plan=upstream["plan"],
            p1_artifact=upstream["p1_artifact"],
            plan_manifest=upstream["plan_manifest"],
            final_fragments=final_fragments,
            anchors=upstream["anchors"],
        )
        contract_runtime.validate(package, "fragment-package.schema.json")
        _write_new(staging / "fragment-package.json", package)
        (staging / "fragments.md").write_text(
            _render_markdown(package), encoding="utf-8", newline=""
        )
        implementation_refs: list[dict[str, str]] = []
        implementation_catalog: list[dict[str, Any]] = []
        for implementation_id, source in sorted(
            _implementation_paths().items()
        ):
            target = staging / "implementation" / implementation_id
            _copy_exact(source, target)
            reference = rt.artifact_reference(target, root=staging)
            implementation_refs.append(reference)
            implementation_catalog.append(
                {"identity": implementation_id, "artifact": reference}
            )
        execution = {
            "schema_version": "2.0",
            "run_id": upstream["plan"]["run_id"],
            "stage": "H1",
            "operation": "controlled-H1-B",
            "h1_session_id": upstream["plan"]["h1_session_id"],
            "workspace_state": workspace_state.reference,
            "plan_input_gate": plan_input_gate.reference,
            "p1_completion": upstream["p1_stage"],
            "plan_manifest": upstream["plan_manifest"],
            "generation_session": rt.artifact_reference(
                staging / "generation-session.json", root=staging
            ),
            "session_workspace_completion": rt.artifact_reference(
                staging / "session-workspace-completion.json",
                root=staging,
            ),
            "generation_evidence": evidence_refs,
            "outputs": {
                name: rt.artifact_reference(
                    staging / name, root=staging
                )
                for name in ("fragment-package.json", "fragments.md")
            },
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
        }
        _write_new(staging / "execution-record.json", execution)
        _write_new(
            staging / "validation.json",
            _validation(
                upstream["plan"]["run_id"],
                upstream["plan"]["h1_session_id"],
            ),
        )
        files = _tree_inventory(staging)
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": upstream["plan"]["run_id"],
            "stage": "H1",
            "package_profile": "h1-fragments",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "fragment_package": by_path["fragment-package.json"],
                "fragments": by_path["fragments.md"],
                "generation_session": by_path["generation-session.json"],
                "session_workspace_completion": by_path[
                    "session-workspace-completion.json"
                ],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
            "parent_state_sha256": workspace_state.reference["sha256"],
            "session_id": upstream["plan"]["h1_session_id"],
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write_new(staging / "package-manifest.json", manifest)
        validate_fragment_package(
            staging,
            p1_package=upstream["p1_root"],
            plan_package=upstream["plan_root"],
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            workspace_state=workspace_state,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
        )
        if (
            p1_before != _tree_inventory(upstream["p1_root"])
            or plan_before != _tree_inventory(upstream["plan_root"])
            or session_before != _tree_inventory(session_root)
        ):
            _fail("H1B_INPUT_MUTATED", "input changed during generation")
        staging.replace(destination)
        validate_fragment_package(
            destination,
            p1_package=upstream["p1_root"],
            plan_package=upstream["plan_root"],
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            workspace_state=workspace_state,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
        )
        manifest_ref = {
            "path": f"{logical_package_path}/package-manifest.json",
            "sha256": rt.sha256_file(destination / "package-manifest.json"),
        }
        transition = coordinator.accept_h1_workspace_transition(
            current_workspace=workspace_state,
            package_manifest=rt.SealedDocument(
                data=manifest, reference=manifest_ref
            ),
            expected_next_state="fragments_ready",
            active_return_request=active_return_request,
        )
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return FragmentReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        transition=transition,
    )


def run(
    package_root: str | Path,
    *,
    session_workspace: str | Path,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    workspace_state: Any,
    coordinator: Any,
    logical_package_path: str = "H1/fragments",
    plan_active_return_request: Any | None = None,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> FragmentReceipt:
    """Compatibility name for finalization; accepts no Agent payload."""

    return finalize_fragment_package(
        package_root,
        session_workspace=session_workspace,
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        workspace_state=workspace_state,
        coordinator=coordinator,
        logical_package_path=logical_package_path,
        plan_active_return_request=plan_active_return_request,
        active_return_request=active_return_request,
        runtime=runtime,
    )


__all__ = [
    "PHASES",
    "LANGUAGE_CONTRACT_ID",
    "STYLE_CONTRACT_ID",
    "DEPTH_CONTRACT_ID",
    "LANGUAGE",
    "POV_MODE",
    "INTERIORITY_POLICY",
    "SURFACE_DETAIL_POLICY",
    "PURPOSE",
    "VISIBLE_UNIT_CONTRACT_ID",
    "MIN_CJK_UNIT_RATIO",
    "STYLE_PRINCIPLES",
    "NARRATIVE_QUALITY_PRINCIPLES",
    "H1BError",
    "FragmentReceipt",
    "start_fragment_session",
    "submit_fragment_phase",
    "finalize_fragment_package",
    "validate_fragment_package",
    "run",
]
