"""Controlled H1-A plan generation and deterministic report assembly runtime."""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import math
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
p1_runtime = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)

PLAN_PHASES = (
    "review-task-analysis",
    "information-architecture",
    "visual-and-fragment-plan",
    "ten-minute-budget-test",
    "final-review-plan",
)
SECTION_KINDS = ("world", "storylines", "characters")
CONTENT_DIMENSION_KINDS = (*SECTION_KINDS, "fragments")
REVIEW_OPERATION_KIND = "decision"
REVIEW_PATH_KINDS = (*CONTENT_DIMENSION_KINDS, REVIEW_OPERATION_KIND)
READING_PROFILE = "review-reading-baseline-v1"
CJK_CHARS_PER_MINUTE = 400
LATIN_WORDS_PER_MINUTE = 200
VISUAL_OVERHEAD_SECONDS = 10
DECISION_OVERHEAD_SECONDS = 15
VISUAL_ROLE_SPECS = {
    "control_logic_chain": ("storylines", "flow"),
    "world_environment_map": ("world", "map"),
    "storyline_architecture": ("storylines", "flow"),
    "major_event_timeline": ("storylines", "timeline"),
    "character_relationship_network": ("characters", "network"),
}
_TECHNICAL_IDS = {"run_id", "session_id", "task_id", "thread_id"}
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_FIDELITY_SKILL = _SKILL.parent / "novel-conception-presentation-fidelity-reviewer"
_SCHEMAS = (
    _REPO
    / "docs"
    / "ai-novel-workflow"
    / "contracts"
    / "autonomous-v2"
)
_PLAN_ROOT_FILES = {
    "source-inventory.json",
    "review-plan.json",
    "fragment-briefs.json",
    "generation-session.json",
    "generation-evidence-index.json",
    "execution-record.json",
    "validation.json",
    "package-manifest.json",
}
_PLAN_ROOT_PREFIXES = ("generation-evidence/", "implementation/")
_ASSEMBLY_ROOT_FILES = {
    "human-review-report.json",
    "human-review-report.md",
    "presentation-fidelity-review.json",
    "assembly-execution.json",
    "validation.json",
    "package-manifest.json",
}
_ASSEMBLY_ROOT_PREFIXES = ("implementation/",)


class H1AError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class PlanReceipt:
    package_root: Path
    manifest: dict[str, Any]
    transition: Any


@dataclass(frozen=True)
class AssemblyReceipt:
    package_root: Path
    manifest: dict[str, Any]
    transition: Any


def _fail(code: str, message: str) -> None:
    raise H1AError(code, message)


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
        _fail("H1A_OUTPUT_EXISTS", str(path))
    _write(path, value)


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


def _implementation_paths() -> dict[str, Path]:
    return {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/review-plan-contract.md": (
            _SKILL / "references" / "review-plan-contract.md"
        ),
        "schemas/h1-review-plan.schema.json": (
            _SCHEMAS / "h1-review-plan.schema.json"
        ),
        "schemas/h1-fragment-briefs.schema.json": (
            _SCHEMAS / "h1-fragment-briefs.schema.json"
        ),
        "schemas/h1-workspace-state.schema.json": (
            _SCHEMAS / "h1-workspace-state.schema.json"
        ),
        "schemas/human-review-report.schema.json": (
            _SCHEMAS / "human-review-report.schema.json"
        ),
        "schemas/presentation-fidelity-review.schema.json": (
            _SCHEMAS / "presentation-fidelity-review.schema.json"
        ),
        "fidelity-reviewer/SKILL.md": _FIDELITY_SKILL / "SKILL.md",
        "fidelity-reviewer/review-contract.md": (
            _FIDELITY_SKILL / "references" / "review-contract.md"
        ),
        "schemas/fragment-package.schema.json": (
            _SCHEMAS / "fragment-package.schema.json"
        ),
        "schemas/package-manifest.schema.json": (
            _SCHEMAS / "package-manifest.schema.json"
        ),
    }


def _copy_exact(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        _fail("H1A_COPY_DRIFT", str(source))


def _identity() -> dict[str, str]:
    task_id = os.environ.get("CODEX_TASK_ID", "").strip()
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not task_id or not thread_id:
        _fail(
            "H1A_CONTROLLED_CONTEXT_REQUIRED",
            "CODEX_TASK_ID and CODEX_THREAD_ID are required",
        )
    return {"task_id": task_id, "thread_id": thread_id}


def _p1_reference(root: Path) -> dict[str, str]:
    completion = _read(
        root / "stage-completion.json", "H1A_P1_COMPLETION_INVALID"
    )
    if completion.get("stage") != "P1" or completion.get("status") != "ready":
        _fail("H1A_P1_COMPLETION_INVALID", "P1 is not ready")
    return {
        "stage": "P1",
        "path": "P1/stage-completion.json",
        "sha256": rt.sha256_file(root / "stage-completion.json"),
    }


def _artifact_only(reference: Mapping[str, str]) -> dict[str, str]:
    return {"path": reference["path"], "sha256": reference["sha256"]}


def _work_identity(
    work_title: Any, input_gate: Mapping[str, str]
) -> dict[str, Any]:
    if (
        not isinstance(work_title, str)
        or not work_title
        or work_title != work_title.strip()
        or len(work_title) > 200
        or any(character in work_title for character in "\r\n")
        or any(ord(character) < 32 for character in work_title)
    ):
        _fail(
            "H1A_WORK_IDENTITY_INVALID",
            "work_title must be trimmed project display metadata",
        )
    if any(token in work_title for token in ("《", "》", "构想人审包", "构思人审报告")):
        _fail(
            "H1A_WORK_IDENTITY_INVALID",
            "work_title must be the plain author-facing work title",
        )
    return {
        "metadata_kind": "project_display_metadata",
        "work_title": work_title,
        "report_title": f"《{work_title}》构思人审报告",
        "input_gate": copy.deepcopy(dict(input_gate)),
    }


def _validate_work_identity(
    value: Any, *, input_gate: Mapping[str, str]
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("H1A_WORK_IDENTITY_INVALID", "work_identity must be an object")
    expected = _work_identity(value.get("work_title"), input_gate)
    if dict(value) != expected:
        _fail(
            "H1A_WORK_IDENTITY_INVALID",
            "work_identity is not the exact launch metadata projection",
        )
    return expected


def _validate_plan_context(
    *,
    p1_package: str | Path,
    input_gate: Any,
    workspace_state: Any,
    active_return_request: Any | None,
    runtime: Any,
) -> tuple[Path, dict[str, Any], dict[str, str], dict[str, Any]]:
    root = Path(p1_package).resolve()
    before = _tree_inventory(root)
    try:
        validation = p1_runtime.validate_p1_package(root, runtime=runtime)
    except Exception as error:
        _fail("H1A_P1_INVALID", str(error))
    if validation.get("verdict") != "ready":
        _fail("H1A_P1_INVALID", "P1 validator did not return ready")
    p1_stage_ref = _p1_reference(root)
    package = _read(
        root / "novel-conception-package.json", "H1A_P1_PACKAGE_INVALID"
    )
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("H1A_INPUT_GATE_INVALID", str(error))
    gate = input_gate.data
    if (
        gate.get("target_stage") != "H1"
        or gate.get("run_id") != package.get("run_id")
        or gate.get("upstream_completions") != [p1_stage_ref]
        or rt.canonical_sha256(gate)
        != input_gate.reference.get("sha256")
    ):
        _fail("H1A_INPUT_GATE_INVALID", "gate does not bind exact P1")
    if gate.get("entry_mode") == "forward":
        if (
            gate.get("active_return") is not None
            or gate.get("return_binding") is not None
            or active_return_request is not None
        ):
            _fail("H1A_INPUT_GATE_INVALID", "forward gate carries return")
    elif gate.get("entry_mode") == "return_resolution":
        binding = gate.get("return_binding")
        if (
            active_return_request is None
            or not isinstance(binding, Mapping)
            or binding.get("resume_stage") != "H1"
            or binding.get("resume_point") != "H1-A-plan"
            or active_return_request.reference
            != gate.get("active_return")
            or active_return_request.reference
            != binding.get("return_request")
            or active_return_request.data.get("return_id")
            != binding.get("return_id")
        ):
            _fail(
                "H1A_INPUT_GATE_INVALID",
                "return is not an exact H1-A-plan resolution",
            )
    else:
        _fail("H1A_INPUT_GATE_INVALID", "unknown entry mode")
    workspace = validate_plan_workspace(
        workspace_state,
        p1_completion=p1_stage_ref,
        runtime=runtime,
    )
    if (
        workspace["run_id"] != package["run_id"]
        or before != _tree_inventory(root)
    ):
        _fail("H1A_P1_MUTATED", "P1 changed during plan admission")
    return root, package, p1_stage_ref, workspace


def _walk(value: Any, pointer: str = ""):
    yield pointer or "/", value
    if isinstance(value, Mapping):
        for key in sorted(value):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk(value[key], f"{pointer}/{escaped}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{pointer}/{index}")


def build_source_inventory(
    p1_package: str | Path,
    *,
    p1_completion: Mapping[str, str],
) -> dict[str, Any]:
    """Deterministically inventory complete P1 objects without summarizing them."""

    root = Path(p1_package).resolve()
    package = _read(
        root / "novel-conception-package.json", "H1A_P1_PACKAGE_INVALID"
    )
    artifacts: list[tuple[str, Mapping[str, str]]] = [
        ("B0", package["author_control_baseline"])
    ]
    artifacts.extend(
        (stage, package["canonical_models"][stage])
        for stage in ("S1", "W1", "E1", "T1", "C1")
    )
    anchors: list[dict[str, Any]] = []
    for stage, reference in artifacts:
        try:
            path = rt.verify_artifact_reference(reference, root=root)
        except Exception as error:
            _fail("H1A_P1_ARTIFACT_INVALID", f"{stage}: {error}")
        model = _read(path, "H1A_P1_ARTIFACT_INVALID")
        for pointer, value in _walk(model):
            if (
                isinstance(value, Mapping)
                and isinstance(value.get("id"), str)
            ):
                anchors.append(
                    {
                        "stage": stage,
                        "source_id": value["id"],
                        "artifact": copy.deepcopy(dict(reference)),
                        "json_pointer": pointer,
                        "value_sha256": rt.canonical_sha256(value),
                    }
                )
    anchors.sort(
        key=lambda item: (
            item["stage"],
            item["source_id"],
            item["json_pointer"],
        )
    )
    if not anchors:
        _fail("H1A_SOURCE_INVENTORY_EMPTY", "P1 has no reviewable objects")
    for index, item in enumerate(anchors, 1):
        item["id"] = f"SRC-{index:06d}"
    return {
        "schema_version": "2.0",
        "run_id": package["run_id"],
        "p1_completion": copy.deepcopy(dict(p1_completion)),
        "anchors": anchors,
    }


def validate_plan_workspace(
    workspace_state: Any,
    *,
    p1_completion: Mapping[str, str],
    runtime: Any,
) -> dict[str, Any]:
    try:
        runtime.validate(
            workspace_state.data, "h1-workspace-state.schema.json"
        )
    except Exception as error:
        _fail("H1A_WORKSPACE_INVALID", str(error))
    state = workspace_state.data
    if (
        state.get("state") != "initialized"
        or state.get("p1_completion") != p1_completion
        or state.get("previous_state_sha256") is not None
        or state.get("artifacts") != {}
        or rt.canonical_sha256(state)
        != workspace_state.reference.get("sha256")
    ):
        _fail(
            "H1A_WORKSPACE_INVALID",
            "plan requires the exact initialized P1-bound workspace",
        )
    return copy.deepcopy(state)


def validate_plan_phases(
    submissions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if len(submissions) != len(PLAN_PHASES):
        _fail("H1A_PLAN_PHASE_ORDER_INVALID", "exactly five phases required")
    normalized: list[dict[str, Any]] = []
    for index, (expected, submission) in enumerate(
        zip(PLAN_PHASES, submissions), 1
    ):
        if (
            not isinstance(submission, Mapping)
            or submission.get("phase") != expected
            or submission.get("phase_index") != index
            or not isinstance(submission.get("payload"), Mapping)
        ):
            _fail("H1A_PLAN_PHASE_ORDER_INVALID", expected)
        normalized.append(copy.deepcopy(dict(submission)))
    return normalized


def _validate_phase_payloads(
    phases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    expected_fields = (
        {"review_requirements", "risk_register"},
        {
            "review_path",
            "sections",
            "review_scope_contract",
            "decision_controls",
            "reduction_ledger",
            "drilldown_index",
        },
        {
            "visual_models",
            "fragment_briefs",
            "decision_prompts",
            "assembly_projection",
            "presentation_bindings",
        },
        {"reading_profile", "budget_items", "budget_total_seconds"},
        {"review_plan", "final_checks"},
    )
    for phase, fields in zip(phases, expected_fields):
        if set(phase["payload"]) != fields:
            _fail(
                "H1A_PLAN_PHASE_PAYLOAD_INVALID",
                f"{phase['phase']} fields",
            )
    plan = phases[4]["payload"]["review_plan"]
    if not isinstance(plan, Mapping):
        _fail("H1A_PLAN_PHASE_PAYLOAD_INVALID", "review_plan")
    bindings = (
        ("review_requirements", phases[0]["payload"]["review_requirements"]),
        ("risk_register", phases[0]["payload"]["risk_register"]),
        ("review_path", phases[1]["payload"]["review_path"]),
        ("sections", phases[1]["payload"]["sections"]),
        (
            "review_scope_contract",
            phases[1]["payload"]["review_scope_contract"],
        ),
        (
            "decision_controls",
            phases[1]["payload"]["decision_controls"],
        ),
        (
            "reduction_ledger",
            phases[1]["payload"]["reduction_ledger"],
        ),
        (
            "drilldown_index",
            phases[1]["payload"]["drilldown_index"],
        ),
        ("visual_models", phases[2]["payload"]["visual_models"]),
        ("fragment_briefs", phases[2]["payload"]["fragment_briefs"]),
        (
            "assembly_projection",
            phases[2]["payload"]["assembly_projection"],
        ),
        (
            "decision_prompts",
            phases[2]["payload"]["decision_prompts"],
        ),
        (
            "presentation_bindings",
            phases[2]["payload"]["presentation_bindings"],
        ),
        ("budget_items", phases[3]["payload"]["budget_items"]),
        ("reading_profile", phases[3]["payload"]["reading_profile"]),
    )
    for field, expected in bindings:
        if plan.get(field) != expected:
            _fail(
                "H1A_PLAN_PHASE_BINDING_INVALID",
                f"{field} differs from its presentation phase",
            )
    total = sum(
        item.get("estimated_seconds", 0)
        for item in phases[3]["payload"]["budget_items"]
        if isinstance(item, Mapping)
    )
    if phases[3]["payload"]["budget_total_seconds"] != total:
        _fail("H1A_PLAN_PHASE_BINDING_INVALID", "budget total")
    checks = phases[4]["payload"]["final_checks"]
    if (
        not isinstance(checks, Mapping)
        or set(checks)
        != {
            "three_boards",
            "all_source_anchors_covered",
            "budget_within_600",
            "fragments_non_authoritative",
            "decision_unselected",
        }
        or set(checks.values()) != {True}
    ):
        _fail("H1A_PLAN_FINAL_CHECK_INVALID", "final checks")
    return copy.deepcopy(dict(plan))


def _validate_assembly_projection(plan: Mapping[str, Any]) -> None:
    projection = plan["assembly_projection"]
    sections = {section["kind"]: section for section in plan["sections"]}
    specifications = {
        "world": {
            "singles": (
                "definition_module_id",
                "operating_logic_module_id",
            ),
            "lists": (
                "system_module_ids",
                "environment_module_ids",
                "event_condition_module_ids",
                "constraint_module_ids",
                "boundary_module_ids",
            ),
            "partition": (
                "system_module_ids",
                "environment_module_ids",
                "event_condition_module_ids",
            ),
        },
        "storylines": {
            "singles": (
                "story_subject_module_id",
                "suspense_conflict_rhythm_module_id",
            ),
            "lists": (
                "line_module_ids",
                "connection_module_ids",
                "major_event_module_ids",
                "constraint_module_ids",
            ),
            "partition": (
                "line_module_ids",
                "connection_module_ids",
                "major_event_module_ids",
            ),
        },
        "characters": {
            "singles": (),
            "lists": (
                "core_character_module_ids",
                "supporting_character_module_ids",
                "relationship_network_module_ids",
                "role_coverage_module_ids",
                "constraint_module_ids",
            ),
            "partition": (
                "core_character_module_ids",
                "supporting_character_module_ids",
                "relationship_network_module_ids",
                "role_coverage_module_ids",
            ),
        },
    }
    for kind, specification in specifications.items():
        section_ids = {
            module["id"] for module in sections[kind]["modules"]
        }
        selected: list[str] = []
        for field in specification["singles"]:
            module_id = projection[kind][field]
            if module_id not in section_ids:
                _fail(
                    "H1A_ASSEMBLY_PROJECTION_INVALID",
                    f"{kind}.{field} is not in its section",
                )
        for field in specification["lists"]:
            module_ids = projection[kind][field]
            if not set(module_ids) <= section_ids:
                _fail(
                    "H1A_ASSEMBLY_PROJECTION_INVALID",
                    f"{kind}.{field} crosses section",
                )
        for field in specification["partition"]:
            selected.extend(projection[kind][field])
        if len(selected) != len(set(selected)) or set(selected) != section_ids:
            _fail(
                "H1A_ASSEMBLY_PROJECTION_INVALID",
                f"{kind} control arrays must partition every module",
            )


def _require_continuous_order(
    items: Sequence[Mapping[str, Any]], label: str
) -> None:
    if [item.get("order") for item in items] != list(
        range(1, len(items) + 1)
    ):
        _fail(
            "H1A_VISUAL_GRAPH_ORDER_INVALID",
            f"{label} order must be continuous and match array order",
        )


def _validate_visual_models(
    plan: Mapping[str, Any], source_inventory: Mapping[str, Any]
) -> None:
    visuals = plan["visual_models"]
    roles = [visual["semantic_role"] for visual in visuals]
    if (
        len(visuals) != len(VISUAL_ROLE_SPECS)
        or len(roles) != len(set(roles))
        or set(roles) != set(VISUAL_ROLE_SPECS)
    ):
        _fail(
            "H1A_VISUAL_ROLE_INVALID",
            "the five semantic roles must each appear exactly once",
        )
    sections = {section["kind"]: section for section in plan["sections"]}
    anchors_by_id = {
        anchor["id"]: anchor for anchor in source_inventory["anchors"]
    }
    known_anchors = set(anchors_by_id)
    global_ids: set[str] = set()
    for visual in visuals:
        role = visual["semantic_role"]
        expected_section, expected_kind = VISUAL_ROLE_SPECS[role]
        if (
            visual["section_id"] != sections[expected_section]["id"]
            or visual["visual_kind"] != expected_kind
        ):
            _fail(
                "H1A_VISUAL_ROLE_INVALID",
                f"{role} must be {expected_section}/{expected_kind}",
            )
        groups = visual["groups"]
        nodes = visual["nodes"]
        edges = visual["edges"]
        equivalents = visual["text_equivalents"]
        _require_continuous_order(groups, f"{visual['id']} groups")
        _require_continuous_order(nodes, f"{visual['id']} nodes")
        _require_continuous_order(edges, f"{visual['id']} edges")
        _require_continuous_order(
            equivalents, f"{visual['id']} text equivalents"
        )
        element_records = [*groups, *nodes, *edges]
        element_ids = [item["id"] for item in element_records]
        local_ids = [
            visual["id"],
            *element_ids,
            *(item["id"] for item in equivalents),
        ]
        if (
            len(local_ids) != len(set(local_ids))
            or global_ids.intersection(local_ids)
        ):
            _fail(
                "H1A_VISUAL_GRAPH_ID_INVALID",
                f"{visual['id']} graph ids are not globally unique",
            )
        global_ids.update(local_ids)
        group_by_id = {group["id"]: group for group in groups}
        node_ids = {node["id"] for node in nodes}
        for node in nodes:
            if (
                node["group_id"] is not None
                and node["group_id"] not in group_by_id
            ):
                _fail(
                    "H1A_VISUAL_GRAPH_GROUP_INVALID",
                    f"{node['id']} has a dangling group",
                )
        for edge in edges:
            if (
                edge["from_node_id"] not in node_ids
                or edge["to_node_id"] not in node_ids
            ):
                _fail(
                    "H1A_VISUAL_GRAPH_EDGE_INVALID",
                    f"{edge['id']} has a dangling endpoint",
                )
            if (
                edge["group_id"] is not None
                and edge["group_id"] not in group_by_id
            ):
                _fail(
                    "H1A_VISUAL_GRAPH_GROUP_INVALID",
                    f"{edge['id']} has a dangling group",
                )
        if role == "control_logic_chain" and (
            len(nodes) < 2 or len(edges) < 1
        ):
            _fail(
                "H1A_VISUAL_ROLE_INVALID",
                "control_logic_chain requires at least two nodes and one edge",
            )
        if role == "major_event_timeline":
            lanes = [group["lane"] for group in groups]
            if (
                not groups
                or any(not lane for lane in lanes)
                or len(lanes) != len(set(lanes))
            ):
                _fail(
                    "H1A_VISUAL_TIMELINE_INVALID",
                    "major_event_timeline requires unique non-empty lanes",
                )
            for node in nodes:
                group = group_by_id.get(node["group_id"])
                if (
                    group is None
                    or not node["lane"]
                    or node["lane"] != group["lane"]
                    or not node["temporal_label"]
                ):
                    _fail(
                        "H1A_VISUAL_TIMELINE_INVALID",
                        f"{node['id']} lacks bound lane/temporal_label",
                    )
            # Graph elements bind inventory anchor IDs, while TPH/MS/NM are
            # the source IDs carried by those anchors.  Looking for prefixes
            # on the anchor IDs silently disabled the temporal hard gate.
            temporal_anchor_ids = {
                anchor_id
                for anchor_id, anchor in anchors_by_id.items()
                if anchor["source_id"].startswith(("TPH-", "MS-", "NM-"))
            }
            if temporal_anchor_ids:
                node_sources = {
                    anchor_id
                    for node in nodes
                    for anchor_id in node["source_anchor_ids"]
                }
                missing_temporal = temporal_anchor_ids - node_sources
                if missing_temporal:
                    _fail(
                        "H1A_VISUAL_TIMELINE_INVALID",
                        "major_event_timeline omits temporal controls: "
                        f"{sorted(missing_temporal)}",
                    )
                required_marker_kinds = {
                    "setup",
                    "probe",
                    "turning_point",
                    "climax",
                    "payoff",
                }
                node_kinds = {node["kind"] for node in nodes}
                if not required_marker_kinds <= node_kinds:
                    _fail(
                        "H1A_VISUAL_TIMELINE_INVALID",
                        "major_event_timeline lacks required narrative "
                        f"functions: {sorted(required_marker_kinds - node_kinds)}",
                    )
                storyline_anchor_ids = {
                    anchor_id
                    for anchor_id, anchor in anchors_by_id.items()
                    if anchor["source_id"].startswith("SL-")
                }
                temporal_labels = [
                    node["temporal_label"] for node in nodes
                ]
                if (
                    len(storyline_anchor_ids) > 1
                    and (
                        len(groups) < 2
                        or len(set(temporal_labels)) == len(temporal_labels)
                    )
                ):
                    _fail(
                        "H1A_VISUAL_TIMELINE_INVALID",
                        "a multi-line source requires multiple lanes and at "
                        "least one shared temporal position",
                    )
                if nodes:
                    adjacency = {node_id: set() for node_id in node_ids}
                    for edge in edges:
                        adjacency[edge["from_node_id"]].add(
                            edge["to_node_id"]
                        )
                        adjacency[edge["to_node_id"]].add(
                            edge["from_node_id"]
                        )
                    visited: set[str] = set()
                    pending = [nodes[0]["id"]]
                    while pending:
                        current = pending.pop()
                        if current in visited:
                            continue
                        visited.add(current)
                        pending.extend(adjacency[current] - visited)
                    if visited != node_ids:
                        _fail(
                            "H1A_VISUAL_TIMELINE_INVALID",
                            "major_event_timeline must be one connected "
                            "progression graph",
                        )
        element_by_id = {
            item["id"]: item for item in element_records
        }
        covered_ids: list[str] = []
        for equivalent in equivalents:
            bound_ids = equivalent["element_ids"]
            if any(item not in element_by_id for item in bound_ids):
                _fail(
                    "H1A_VISUAL_TEXT_EQUIVALENT_INVALID",
                    f"{equivalent['id']} binds a ghost graph element",
                )
            expected_sources = {
                anchor_id
                for element_id in bound_ids
                for anchor_id in element_by_id[element_id][
                    "source_anchor_ids"
                ]
            }
            if set(equivalent["source_anchor_ids"]) != expected_sources:
                _fail(
                    "H1A_VISUAL_TEXT_EQUIVALENT_INVALID",
                    f"{equivalent['id']} source binding drift",
                )
            covered_ids.extend(bound_ids)
        if (
            len(covered_ids) != len(set(covered_ids))
            or set(covered_ids) != set(element_ids)
        ):
            _fail(
                "H1A_VISUAL_TEXT_EQUIVALENT_INVALID",
                f"{visual['id']} text equivalents must partition the graph",
            )
        graph_sources = {
            anchor_id
            for item in [*element_records, *equivalents]
            for anchor_id in item["source_anchor_ids"]
        }
        if (
            not graph_sources <= known_anchors
            or set(visual["source_anchor_ids"]) != graph_sources
        ):
            _fail(
                "H1A_VISUAL_GRAPH_SOURCE_INVALID",
                f"{visual['id']} source anchors are not an exact graph union",
            )


def _validate_fragment_brief_contracts(
    plan: Mapping[str, Any], source_inventory: Mapping[str, Any]
) -> None:
    source_by_anchor = _source_id_map(source_inventory)
    scene_fields = {
        "before_state",
        "immediate_goal",
        "pressure",
        "obstacle",
        "required_choice",
        "direct_consequence",
        "after_state",
    }
    for brief in plan["fragment_briefs"]:
        information = brief.get("information_limits")
        scene = brief.get("scene_contract")
        channels = brief.get("allowed_perception_channels")
        if (
            brief.get("language_contract_id") != "zh-Hans-review-v1"
            or brief.get("style_contract_id")
            != "restrained-concrete-scene-v1"
            or brief.get("depth_contract_id")
            != "character-grounded-scene-v1"
            or brief.get("pov_mode") != "third_person_limited"
            or brief.get("decisive_interiority_policy")
            != "process-only-no-unresolved-decision-disclosure"
            or brief.get("surface_detail_policy")
            != "fragment-local-non-authoritative-v1"
            or not isinstance(information, Mapping)
            or set(information)
            != {"may_present", "must_not_present_as_known"}
            or any(
                not isinstance(information[field], list)
                or not information[field]
                or len(information[field]) != len(set(information[field]))
                or any(
                    not isinstance(item, str) or not item.strip()
                    for item in information[field]
                )
                for field in information
            )
            or not isinstance(channels, list)
            or not channels
            or len(channels) != len(set(channels))
            or any(
                not isinstance(item, str) or not item.strip()
                for item in channels
            )
            or not isinstance(scene, Mapping)
            or set(scene) != scene_fields
            or any(
                not isinstance(scene[field], str) or not scene[field].strip()
                for field in scene_fields
            )
        ):
            _fail(
                "H1A_FRAGMENT_BRIEF_INVALID",
                f"{brief.get('id', '<unknown>')} control contract",
            )
        try:
            source_ids = {
                source_by_anchor[anchor_id]
                for anchor_id in brief["source_anchor_ids"]
            }
        except (KeyError, TypeError) as error:
            _fail("H1A_FRAGMENT_BRIEF_INVALID", str(error))
        if brief["pov_character_id"] not in source_ids:
            _fail(
                "H1A_FRAGMENT_BRIEF_INVALID",
                f"{brief['id']} POV is not source-bound",
            )


def _presentation_elements(
    plan: Mapping[str, Any],
) -> list[tuple[Mapping[str, Any], str]]:
    elements: list[tuple[Mapping[str, Any], str]] = []
    for section in plan["sections"]:
        elements.extend(
            (module, "source_anchor_ids")
            for module in section["modules"]
        )
    elements.extend(
        (visual, "source_anchor_ids") for visual in plan["visual_models"]
    )
    elements.extend(
        (brief, "source_anchor_ids") for brief in plan["fragment_briefs"]
    )
    elements.extend(
        (prompt, "affected_source_anchor_ids")
        for prompt in plan["decision_prompts"]
    )
    return elements


def _validate_presentation_bindings(
    plan: Mapping[str, Any], source_inventory: Mapping[str, Any]
) -> None:
    elements = _presentation_elements(plan)
    bindings = plan["presentation_bindings"]
    element_ids = [element["id"] for element, _ in elements]
    binding_ids = [binding["element_id"] for binding in bindings]
    if (
        len(element_ids) != len(set(element_ids))
        or binding_ids != element_ids
    ):
        _fail(
            "H1A_PRESENTATION_BINDING_INVALID",
            "bindings must exactly cover elements in presentation order",
        )
    source_hashes = {
        anchor["id"]: anchor["value_sha256"]
        for anchor in source_inventory["anchors"]
    }
    for (element, anchor_field), binding in zip(elements, bindings):
        anchor_ids = element[anchor_field]
        try:
            expected_values = [
                {
                    "source_anchor_id": anchor_id,
                    "value_sha256": source_hashes[anchor_id],
                }
                for anchor_id in anchor_ids
            ]
        except KeyError as error:
            _fail("H1A_PRESENTATION_BINDING_INVALID", str(error))
        if (
            binding["content_sha256"] != rt.canonical_sha256(element)
            or binding["source_values"] != expected_values
            or binding["challenge_result"] != "passed"
        ):
            _fail(
                "H1A_PRESENTATION_BINDING_INVALID",
                element["id"],
            )
        if (
            element["id"].startswith("MOD-")
            and binding["must_not_imply"] != element["must_not_imply"]
        ):
            _fail(
                "H1A_PRESENTATION_BINDING_INVALID",
                f"{element['id']} must_not_imply drift",
            )


def _validate_default_visible_closure(
    plan: Mapping[str, Any],
    source_inventory: Mapping[str, Any],
) -> dict[str, tuple[str, tuple[str, ...]]]:
    registry: dict[str, tuple[str, tuple[str, ...]]] = {}
    sections_by_id = {section["id"]: section for section in plan["sections"]}

    def register(
        element_id: str, kind: str, anchor_ids: Sequence[str]
    ) -> None:
        if element_id in registry:
            _fail(
                "H1A_VISIBLE_REGISTRY_INVALID",
                f"duplicate element id {element_id}",
            )
        registry[element_id] = (kind, tuple(anchor_ids))

    for section in plan["sections"]:
        for module in section["modules"]:
            if module["default_visible"] is not True:
                _fail(
                    "H1A_VISIBLE_REGISTRY_INVALID",
                    f"{module['id']} is not default visible",
                )
            register(
                module["id"], section["kind"], module["source_anchor_ids"]
            )
        section_module_ids = {
            module["id"] for module in section["modules"]
        }
        for visual in plan["visual_models"]:
            if visual["section_id"] != section["id"]:
                continue
            if visual["text_equivalent_module_id"] not in section_module_ids:
                _fail(
                    "H1A_VISIBLE_REGISTRY_INVALID",
                    f"{visual['id']} text equivalent crosses section",
                )
            register(
                visual["id"], section["kind"], visual["source_anchor_ids"]
            )
    if any(
        visual["section_id"] not in sections_by_id
        for visual in plan["visual_models"]
    ):
        _fail(
            "H1A_VISIBLE_REGISTRY_INVALID",
            "visual references unknown section",
        )
    for brief in plan["fragment_briefs"]:
        register(
            brief["slot_id"], "fragments", brief["source_anchor_ids"]
        )
    for prompt in plan["decision_prompts"]:
        register(
            prompt["id"],
            "decision",
            prompt["affected_source_anchor_ids"],
        )

    path_ids: list[str] = []
    for step in plan["review_path"]:
        visible_ids = step["visible_element_ids"]
        if len(visible_ids) != len(set(visible_ids)):
            _fail("H1A_REVIEW_PATH_INVALID", f"duplicates in {step['id']}")
        for element_id in visible_ids:
            if (
                element_id not in registry
                or registry[element_id][0] != step["kind"]
            ):
                _fail(
                    "H1A_REVIEW_PATH_INVALID",
                    f"{step['id']} has ghost or cross-kind {element_id}",
                )
        path_ids.extend(visible_ids)
    if path_ids != list(registry):
        _fail(
            "H1A_REVIEW_PATH_INVALID",
            "default path must exactly cover registry in order",
        )
    path_id_set = set(path_ids)

    minimums = _minimum_reading_seconds(plan)
    for step in plan["review_path"]:
        if step["estimated_seconds"] < minimums[step["kind"]]:
            _fail(
                "H1A_READING_BUDGET_INVALID",
                f"{step['id']} is below measured minimum "
                f"{minimums[step['kind']]} seconds",
            )

    budget = plan["budget_items"]
    expected_budget = [
        {
            "element_id": step["id"],
            "estimated_seconds": step["estimated_seconds"],
        }
        for step in plan["review_path"]
    ]
    if budget != expected_budget:
        _fail(
            "H1A_READING_BUDGET_INVALID",
            "budget must exactly bind four content dimensions and the trailing decision operation",
        )
    if sum(item["estimated_seconds"] for item in budget) > 600:
        _fail("H1A_READING_BUDGET_EXCEEDED", "budget exceeds ten minutes")

    anchors = {item["id"] for item in source_inventory["anchors"]}
    source_by_anchor = {
        item["id"]: item for item in source_inventory["anchors"]
    }
    controls = plan["decision_controls"]
    control_by_id = {item["id"]: item for item in controls}
    if (
        len(control_by_id) != len(controls)
        or {item["domain"] for item in controls}
        != set(CONTENT_DIMENSION_KINDS)
    ):
        _fail(
            "H1A_DECISION_CONTROL_INVALID",
            "decision controls must be unique and cover exactly the four content dimensions",
        )
    for control in controls:
        if any(
            element_id not in path_id_set
            for element_id in control["default_element_ids"]
        ):
            _fail(
                "H1A_DECISION_CONTROL_INVALID",
                f"{control['id']} is not fully default visible",
            )
    fragment_control_ids = {
        item["id"] for item in controls if item["domain"] == "fragments"
    }
    for brief in plan["fragment_briefs"]:
        if not set(brief["decision_control_ids"]) <= fragment_control_ids:
            _fail(
                "H1A_FRAGMENT_DECISION_CONTROL_INVALID",
                brief["id"],
            )

    drilldown = plan["drilldown_index"]
    drilldown_by_id = {item["id"]: item for item in drilldown}
    drilldown_anchors = [item["source_anchor_id"] for item in drilldown]
    if (
        len(drilldown_by_id) != len(drilldown)
        or len(drilldown_anchors) != len(set(drilldown_anchors))
        or set(drilldown_anchors) != anchors
    ):
        _fail(
            "H1A_DRILLDOWN_INDEX_INVALID",
            "drilldown must losslessly index every P1 anchor once",
        )
    for evidence in drilldown:
        source = source_by_anchor.get(evidence["source_anchor_id"])
        if source is None or any(
            evidence[field] != source[field]
            for field in (
                "stage",
                "source_id",
                "json_pointer",
                "value_sha256",
            )
        ):
            _fail(
                "H1A_DRILLDOWN_INDEX_INVALID",
                evidence["id"],
            )

    ledger = plan["reduction_ledger"]
    ledger_ids = [item["source_anchor_id"] for item in ledger]
    if len(ledger_ids) != len(set(ledger_ids)) or set(ledger_ids) != anchors:
        _fail(
            "H1A_REDUCTION_LEDGER_INVALID",
            "reduction ledger must map every P1 anchor exactly once",
        )
    used_controls: set[str] = set()
    ledger_by_anchor: dict[str, Mapping[str, Any]] = {}
    for entry in ledger:
        ledger_by_anchor[entry["source_anchor_id"]] = entry
        unknown = set(entry["decision_control_ids"]) - set(control_by_id)
        if unknown:
            _fail(
                "H1A_REDUCTION_LEDGER_INVALID",
                f"unknown decision controls: {sorted(unknown)}",
            )
        used_controls.update(entry["decision_control_ids"])
    if used_controls != set(control_by_id):
        _fail(
            "H1A_REDUCTION_LEDGER_INVALID",
            "every decision control must retain source evidence",
        )

    coverage_items = plan["control_coverage"]
    coverage_ids = [item["source_anchor_id"] for item in coverage_items]
    if (
        len(coverage_ids) != len(set(coverage_ids))
        or set(coverage_ids) != anchors
    ):
        _fail("H1A_SOURCE_COVERAGE_INVALID", "coverage must be exact")
    for coverage in coverage_items:
        anchor_id = coverage["source_anchor_id"]
        default_ids: list[str] = []
        evidence_ids: list[str] = []
        for element_id in coverage["visible_element_ids"]:
            if element_id.startswith("EVID-"):
                evidence = drilldown_by_id.get(element_id)
                if evidence is None or evidence["source_anchor_id"] != anchor_id:
                    _fail(
                        "H1A_SOURCE_COVERAGE_INVALID",
                        f"{anchor_id} is not bound by {element_id}",
                    )
                evidence_ids.append(element_id)
            elif (
                element_id not in registry
                or element_id not in path_id_set
                or anchor_id not in registry[element_id][1]
            ):
                _fail(
                    "H1A_SOURCE_COVERAGE_INVALID",
                    f"{anchor_id} is not bound by {element_id}",
                )
            else:
                default_ids.append(element_id)
        entry = ledger_by_anchor[anchor_id]
        if not evidence_ids and entry["exposure"] == "drilldown-only":
            _fail(
                "H1A_SOURCE_COVERAGE_INVALID",
                f"{anchor_id} has no drilldown evidence",
            )
        if entry["review_priority"] == "critical" and (
            entry["exposure"] != "default-and-drilldown" or not default_ids
        ):
            _fail(
                "H1A_CRITICAL_EVIDENCE_NOT_DEFAULT_VISIBLE",
                anchor_id,
            )
    return registry


def _count_reading_text(strings: Sequence[str]) -> tuple[int, int]:
    text = "\n".join(strings)
    cjk = len(
        re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text)
    )
    latin = len(
        re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b", text)
    )
    return cjk, latin


def _minimum_reading_seconds(
    plan: Mapping[str, Any],
) -> dict[str, int]:
    if plan.get("reading_profile") != READING_PROFILE:
        _fail(
            "H1A_READING_PROFILE_INVALID",
            "reading profile is fixed and not caller-configurable",
        )
    strings: dict[str, list[str]] = {
        kind: [] for kind in REVIEW_PATH_KINDS
    }
    visual_counts = {kind: 0 for kind in SECTION_KINDS}
    section_kind_by_id = {
        section["id"]: section["kind"] for section in plan["sections"]
    }
    world_projection = plan["assembly_projection"]["world"]
    world_default_summary_ids = set(
        world_projection["environment_module_ids"]
    )
    world_default_summary_ids.update(
        set(world_projection["system_module_ids"])
        - {
            world_projection["definition_module_id"],
            world_projection["operating_logic_module_id"],
        }
    )
    character_projection = plan["assembly_projection"]["characters"]
    character_default_summary_ids = set(
        character_projection["core_character_module_ids"]
        + character_projection["supporting_character_module_ids"]
    )
    world_default_summary_ids.update(
        set(world_projection["event_condition_module_ids"])
        - set(world_projection["constraint_module_ids"])
        - set(world_projection["boundary_module_ids"])
    )
    for section in plan["sections"]:
        kind = section["kind"]
        strings[kind].append(section["title"])
        for module in section["modules"]:
            definition = module["definition"]
            if kind == "world" and module["id"] in world_default_summary_ids:
                definition = re.split(r"(?<=[。！？.!?])", definition, 1)[0]
            if kind == "characters" and module["id"] in character_default_summary_ids:
                definition = re.split(r"(?<=[。！？.!?])", definition, 1)[0]
            strings[kind].extend(
                [
                    module["title"],
                    definition,
                ]
            )
    for visual in plan["visual_models"]:
        kind = section_kind_by_id[visual["section_id"]]
        visible_graph_text = [
            visual["title"],
            visual["review_purpose"],
        ]
        for group in visual["groups"]:
            visible_graph_text.append(group["label"])
        for node in visual["nodes"]:
            visible_graph_text.extend(
                [node["label"], node["temporal_label"] or node["kind"]]
            )
            if visual["semantic_role"] not in {
                "control_logic_chain",
                "storyline_architecture",
                "major_event_timeline",
            }:
                visible_graph_text.append(node["summary"])
        for edge in visual["edges"]:
            visible_graph_text.append(edge["relation_label"])
        visible_graph_text.extend(
            equivalent["text"]
            for equivalent in visual["text_equivalents"]
        )
        strings[kind].extend(visible_graph_text)
        visual_counts[kind] += 1
    fragment_target_cjk = 0
    fragment_target_latin = 0
    for brief in plan["fragment_briefs"]:
        strings["fragments"].append(brief["title"])
        if brief["language_contract_id"].startswith("zh-Hans"):
            fragment_target_cjk += brief["target_words_max"]
        else:
            fragment_target_latin += brief["target_words_max"]
    for prompt in plan["decision_prompts"]:
        strings["decision"].append(prompt["question"])
    for step in plan["review_path"]:
        strings[step["kind"]].append(step["title"])
    minimums: dict[str, int] = {}
    for kind in REVIEW_PATH_KINDS:
        cjk, latin = _count_reading_text(strings[kind])
        if kind == "fragments":
            cjk += fragment_target_cjk
            latin += fragment_target_latin
        seconds = (
            cjk / CJK_CHARS_PER_MINUTE * 60
            + latin / LATIN_WORDS_PER_MINUTE * 60
        )
        if kind in SECTION_KINDS:
            seconds += visual_counts[kind] * VISUAL_OVERHEAD_SECONDS
        if kind == "decision":
            seconds += (
                len(plan["decision_prompts"]) * DECISION_OVERHEAD_SECONDS
            )
        minimums[kind] = max(1, math.ceil(seconds))
    return minimums


_PUBLIC_MACHINE_JARGON = re.compile(
    r"(?:\b(?:MOD|VIS|FRAG|PROMPT|DCTRL|P1|Q1|S1|W1|E1|T1|C1)-"
    r"|source[_ -]?anchor|sha256|json[_ -]?pointer|→|->)",
    re.IGNORECASE,
)


def _validate_human_presentation(plan: Mapping[str, Any]) -> None:
    """Reject review copy that reads like an audit trace or Agent shorthand."""

    seen_titles: set[str] = set()
    for section in plan["sections"]:
        for module in section["modules"]:
            public_values = (
                module["title"],
                module["definition"],
                module["responsibility"],
                *module["must_hold"],
                *module["must_not_imply"],
            )
            if any(_PUBLIC_MACHINE_JARGON.search(value) for value in public_values):
                _fail(
                    "H1A_HUMAN_PRESENTATION_INVALID",
                    f"{module['id']} exposes machine shorthand",
                )
            if module["title"] in seen_titles:
                _fail(
                    "H1A_HUMAN_PRESENTATION_INVALID",
                    f"duplicate reader-facing title: {module['title']}",
                )
            seen_titles.add(module["title"])
            if re.match(r"^\s*\d+\s*(?:[+×x/]|条|线|前置|主线)", module["definition"]):
                _fail(
                    "H1A_HUMAN_PRESENTATION_INVALID",
                    f"{module['id']} is compressed shorthand, not review copy",
                )


def _validate_world_review_completeness(
    plan: Mapping[str, Any], source_inventory: Mapping[str, Any]
) -> None:
    """Keep the public world board complete without exposing the audit model."""

    anchors = {
        item["id"]: (item["stage"], item["source_id"])
        for item in source_inventory["anchors"]
    }
    world_section = next(
        section for section in plan["sections"] if section["kind"] == "world"
    )
    modules = {item["id"]: item for item in world_section["modules"]}
    projection = plan["assembly_projection"]["world"]

    def required_anchor_ids(stage: str, prefix: str) -> set[str]:
        return {
            anchor_id
            for anchor_id, (anchor_stage, source_id) in anchors.items()
            if anchor_stage == stage and source_id.startswith(prefix)
        }

    def covered(module_ids: Sequence[str]) -> set[str]:
        return {
            anchor_id
            for module_id in module_ids
            for anchor_id in modules[module_id]["source_anchor_ids"]
        }

    system_ids = projection["system_module_ids"]
    event_ids = projection["event_condition_module_ids"]
    system_anchors = covered(system_ids)
    event_anchors = covered(event_ids)

    premise = {
        anchor_id
        for anchor_id, (_, source_id) in anchors.items()
        if source_id == "WLD-PREMISE"
    }
    if premise and not premise <= system_anchors:
        _fail(
            "H1A_WORLD_REVIEW_INCOMPLETE",
            "world background premise is not publicly projected",
        )

    institutions = required_anchor_ids("W1", "INST-")
    if institutions and not institutions <= system_anchors:
        _fail(
            "H1A_WORLD_REVIEW_INCOMPLETE",
            "world organizations and their operating relationships are incomplete",
        )

    activities = required_anchor_ids("E1", "AFF-")
    if activities and not activities <= event_anchors:
        _fail(
            "H1A_WORLD_REVIEW_INCOMPLETE",
            "story-bearing world activities are incomplete",
        )

    environments = required_anchor_ids("E1", "ENV-")
    environment_modules = [
        modules[module_id] for module_id in projection["environment_module_ids"]
    ]
    if environments:
        projected: list[str] = []
        for module in environment_modules:
            bound = environments.intersection(module["source_anchor_ids"])
            if len(bound) != 1:
                _fail(
                    "H1A_WORLD_ENVIRONMENT_PROJECTION_INVALID",
                    f"{module['id']} must present exactly one major environment",
                )
            if len(module["definition"].strip()) < 48:
                _fail(
                    "H1A_WORLD_ENVIRONMENT_PROJECTION_INVALID",
                    f"{module['id']} does not define a reviewable environment",
                )
            synopsis = re.split(
                r"(?<=[。！？.!?])", module["definition"].strip(), 1
            )[0]
            if not 28 <= len(synopsis) <= 110:
                _fail(
                    "H1A_WORLD_ENVIRONMENT_PROJECTION_INVALID",
                    f"{module['id']} needs a concise environment synopsis",
                )
            projected.extend(bound)
        if set(projected) != environments or len(projected) != len(environments):
            _fail(
                "H1A_WORLD_ENVIRONMENT_PROJECTION_INVALID",
                "every major environment must have one independent public entry",
            )

        visual = next(
            item
            for item in plan["visual_models"]
            if item["semantic_role"] == "world_environment_map"
        )
        node_environment: dict[str, str] = {}
        for node in visual["nodes"]:
            bound = environments.intersection(node["source_anchor_ids"])
            if len(bound) != 1:
                _fail(
                    "H1A_WORLD_ENVIRONMENT_MAP_INVALID",
                    f"{node['id']} must represent exactly one major environment",
                )
            node_environment[node["id"]] = next(iter(bound))
        if set(node_environment.values()) != environments or len(
            node_environment
        ) != len(environments):
            _fail(
                "H1A_WORLD_ENVIRONMENT_MAP_INVALID",
                "environment map must represent every major environment once",
            )
        if len(node_environment) > 1:
            adjacency = {node_id: set() for node_id in node_environment}
            for edge in visual["edges"]:
                start = edge["from_node_id"]
                end = edge["to_node_id"]
                adjacency[start].add(end)
                adjacency[end].add(start)
            visited: set[str] = set()
            pending = [next(iter(adjacency))]
            while pending:
                node_id = pending.pop()
                if node_id in visited:
                    continue
                visited.add(node_id)
                pending.extend(adjacency[node_id] - visited)
            if visited != set(adjacency):
                _fail(
                    "H1A_WORLD_ENVIRONMENT_MAP_INVALID",
                    "environment map must show how all environments connect",
                )


def _validate_character_review_completeness(
    plan: Mapping[str, Any], source_inventory: Mapping[str, Any]
) -> None:
    """Require one public, reviewable individual definition per C1 profile."""

    profile_anchors = {
        item["id"]: item["source_id"]
        for item in source_inventory["anchors"]
        if item["stage"] == "C1"
        and item["source_id"].startswith("CHR-")
        and item["json_pointer"].startswith("/profiles/")
    }
    # Legacy unit fixtures may use a deliberately reduced inventory without
    # canonical C1 profile pointers. A production P1 inventory always carries
    # them; when present, the projection below is fail-closed.
    if not profile_anchors:
        return
    character_section = next(
        section for section in plan["sections"] if section["kind"] == "characters"
    )
    modules = {item["id"]: item for item in character_section["modules"]}
    projection = plan["assembly_projection"]["characters"]
    profile_module_ids = [
        *projection["core_character_module_ids"],
        *projection["supporting_character_module_ids"],
    ]
    required_labels = (
        "故事位置｜",
        "参与活动｜",
        "外貌辨识｜",
        "性格机制｜",
        "生活背景｜",
        "职业与日常｜",
        "社交圈｜",
        "具身或接口边界｜",
    )
    projected: list[str] = []
    for module_id in profile_module_ids:
        module = modules[module_id]
        bound = set(module["source_anchor_ids"]).intersection(profile_anchors)
        if len(bound) != 1:
            _fail(
                "H1A_CHARACTER_PROFILE_PROJECTION_INVALID",
                f"{module_id} must present exactly one C1 profile",
            )
        definition = module["definition"].strip()
        if any(label not in definition for label in required_labels):
            _fail(
                "H1A_CHARACTER_PROFILE_INCOMPLETE",
                f"{module_id} lacks story/activity/individual controls",
            )
        synopsis = re.split(r"(?<=[。！？.!?])", definition, 1)[0]
        if not 12 <= len(synopsis) <= 72:
            _fail(
                "H1A_CHARACTER_PROFILE_INCOMPLETE",
                f"{module_id} needs a concise scan synopsis",
            )
        projected.extend(bound)
    if set(projected) != set(profile_anchors) or len(projected) != len(profile_anchors):
        _fail(
            "H1A_CHARACTER_PROFILE_PROJECTION_INVALID",
            "every C1 profile must have one and only one public character entry",
        )


def validate_review_plan(
    plan: Mapping[str, Any],
    *,
    source_inventory: Mapping[str, Any],
    workspace_state: Mapping[str, Any],
    work_identity: Mapping[str, Any],
    runtime: Any,
) -> dict[str, Any]:
    value = copy.deepcopy(dict(plan))
    try:
        runtime.validate(value, "h1-review-plan.schema.json")
    except Exception as error:
        _fail("H1A_REVIEW_PLAN_SCHEMA_INVALID", str(error))
    if (
        value["run_id"] != source_inventory["run_id"]
        or value["h1_session_id"] != workspace_state["session_id"]
        or value["p1_completion"] != source_inventory["p1_completion"]
        or value["work_identity"] != work_identity
    ):
        _fail(
            "H1A_REVIEW_PLAN_LINEAGE_INVALID",
            "run/session/P1/work identity mismatch",
        )
    if [item["kind"] for item in value["sections"]] != list(SECTION_KINDS):
        _fail("H1A_THREE_BOARD_INVALID", "sections must be world/storylines/characters")
    _validate_assembly_projection(value)
    _validate_visual_models(value, source_inventory)
    _validate_fragment_brief_contracts(value, source_inventory)
    _validate_presentation_bindings(value, source_inventory)
    _validate_human_presentation(value)
    validate_human_visible_strings(_human_visible_plan_strings(value))
    _validate_world_review_completeness(value, source_inventory)
    _validate_character_review_completeness(value, source_inventory)
    path = value["review_path"]
    if (
        [item["kind"] for item in path] != list(REVIEW_PATH_KINDS)
        or [item["order"] for item in path] != list(range(1, 6))
    ):
        _fail(
            "H1A_REVIEW_PATH_INVALID",
            "four content dimensions plus one trailing decision operation required",
        )
    if sum(item["estimated_seconds"] for item in path) > 600:
        _fail("H1A_READING_BUDGET_EXCEEDED", "path exceeds ten minutes")
    _validate_default_visible_closure(value, source_inventory)
    anchors = {item["id"] for item in source_inventory["anchors"]}
    referenced_anchors: set[str] = set()
    for section in value["sections"]:
        for module in section["modules"]:
            referenced_anchors.update(module["source_anchor_ids"])
    for visual in value["visual_models"]:
        referenced_anchors.update(visual["source_anchor_ids"])
    for brief in value["fragment_briefs"]:
        referenced_anchors.update(brief["source_anchor_ids"])
        if (
            brief["target_words_min"] > brief["target_words_max"]
            or brief["target_words_min"] < 320
            or brief["target_words_max"] - brief["target_words_min"] < 60
            or brief["target_words_max"] > 1200
        ):
            _fail("H1A_FRAGMENT_BRIEF_INVALID", brief["id"])
    for risk in value["risk_register"]:
        referenced_anchors.update(risk["source_anchor_ids"])
    for prompt in value["decision_prompts"]:
        referenced_anchors.update(prompt["affected_source_anchor_ids"])
    if not referenced_anchors <= anchors:
        _fail("H1A_SOURCE_ANCHOR_INVALID", "plan cites a non-P1 anchor")
    return value


def _plan_validation(run_id: str, session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "H1",
        "operation": "H1-A-plan",
        "session_id": session_id,
        "verdict": "ready",
        "checks": [
            "current-P1-and-initialized-workspace",
            "controlled-five-phase-plan",
            "input-gate-bound-work-identity",
            "four-content-dimensions-plus-trailing-decision-operation",
            "five-attributed-graph-semantic-roles",
            "ten-minute-default-visible-budget",
            "versioned-reading-baseline-measurement",
            "P1-source-anchor-coverage",
            "fragment-brief-and-decision-boundaries",
            "manifest-and-implementation-binding",
        ],
        "errors": [],
    }


def _check_plan_boundary(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _PLAN_ROOT_FILES or any(
            relative.startswith(prefix) for prefix in _PLAN_ROOT_PREFIXES
        ):
            continue
        _fail("H1A_PLAN_PACKAGE_BOUNDARY_INVALID", relative)
    evidence = {
        path.name
        for path in (root / "generation-evidence").glob("*.json")
        if path.is_file()
    }
    expected = {
        f"{index:02d}-{phase}.json"
        for index, phase in enumerate(PLAN_PHASES, 1)
    }
    if evidence != expected:
        _fail(
            "H1A_PLAN_PACKAGE_BOUNDARY_INVALID",
            "generation evidence is not exact",
        )
    if (root / "h1-review-plan.json").exists():
        _fail(
            "H1A_LEGACY_INPUT_FORBIDDEN",
            "h1-review-plan.json is not a V2 artifact",
        )


def validate_plan_package(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    input_gate: Any,
    workspace_state: Any,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_plan_boundary(root)
    p1_root, p1_package_value, p1_stage_ref, workspace = (
        _validate_plan_context(
            p1_package=p1_package,
            input_gate=input_gate,
            workspace_state=workspace_state,
            active_return_request=active_return_request,
            runtime=contract_runtime,
        )
    )
    p1_artifact_ref = _artifact_only(p1_stage_ref)
    inventory = _read(
        root / "source-inventory.json", "H1A_SOURCE_INVENTORY_INVALID"
    )
    expected_inventory = build_source_inventory(
        p1_root, p1_completion=p1_artifact_ref
    )
    if inventory != expected_inventory:
        _fail("H1A_SOURCE_INVENTORY_INVALID", "inventory is not reproducible")
    session = _read(
        root / "generation-session.json", "H1A_PLAN_SESSION_INVALID"
    )
    identity = session.get("identity")
    work_identity = _validate_work_identity(
        session.get("work_identity"), input_gate=input_gate.reference
    )
    if (
        session.get("schema_version") != "2.0"
        or session.get("run_id") != p1_package_value["run_id"]
        or session.get("h1_session_id") != workspace["session_id"]
        or session.get("operation") != "controlled-H1-A-plan"
        or session.get("phases") != list(PLAN_PHASES)
        or session.get("source_inventory")
        != rt.artifact_reference(root / "source-inventory.json", root=root)
        or session.get("workspace_state") != workspace_state.reference
        or session.get("work_identity") != work_identity
        or not isinstance(identity, Mapping)
        or not identity.get("task_id")
        or not identity.get("thread_id")
    ):
        _fail("H1A_PLAN_SESSION_INVALID", "session binding")
    evidence_refs: list[dict[str, str]] = []
    submissions: list[dict[str, Any]] = []
    prior = None
    for index, phase in enumerate(PLAN_PHASES, 1):
        path = root / "generation-evidence" / f"{index:02d}-{phase}.json"
        evidence = _read(path, "H1A_PLAN_EVIDENCE_INVALID")
        if (
            evidence.get("schema_version") != "2.0"
            or evidence.get("run_id") != p1_package_value["run_id"]
            or evidence.get("h1_session_id") != workspace["session_id"]
            or evidence.get("identity") != identity
            or evidence.get("phase") != phase
            or evidence.get("phase_index") != index
            or evidence.get("prior_evidence") != prior
            or evidence.get("source_inventory")
            != session["source_inventory"]
            or not isinstance(evidence.get("payload"), Mapping)
            or evidence.get("payload_sha256")
            != rt.canonical_sha256(evidence["payload"])
        ):
            _fail("H1A_PLAN_EVIDENCE_INVALID", phase)
        reference = rt.artifact_reference(path, root=root)
        evidence_refs.append(reference)
        prior = reference
        submissions.append(
            {
                "phase": phase,
                "phase_index": index,
                "payload": evidence["payload"],
            }
        )
    phases = validate_plan_phases(submissions)
    agent_plan = _validate_phase_payloads(phases)
    stored_plan = _read(root / "review-plan.json", "H1A_REVIEW_PLAN_INVALID")
    if stored_plan != agent_plan:
        _fail("H1A_REVIEW_PLAN_INVALID", "not the sealed final Agent plan")
    validate_review_plan(
        stored_plan,
        source_inventory=inventory,
        workspace_state=workspace,
        work_identity=work_identity,
        runtime=contract_runtime,
    )
    evidence_index = _read(
        root / "generation-evidence-index.json",
        "H1A_PLAN_EVIDENCE_INVALID",
    )
    if evidence_index != {
        "schema_version": "2.0",
        "run_id": p1_package_value["run_id"],
        "h1_session_id": workspace["session_id"],
        "phases": list(PLAN_PHASES),
        "evidence": evidence_refs,
    }:
        _fail("H1A_PLAN_EVIDENCE_INVALID", "index")
    plan_ref = rt.artifact_reference(root / "review-plan.json", root=root)
    briefs = _read(
        root / "fragment-briefs.json", "H1A_FRAGMENT_BRIEFS_INVALID"
    )
    expected_briefs = {
        "schema_version": "2.0",
        "run_id": p1_package_value["run_id"],
        "h1_session_id": workspace["session_id"],
        "p1_completion": p1_artifact_ref,
        "review_plan": plan_ref,
        "briefs": stored_plan["fragment_briefs"],
    }
    try:
        contract_runtime.validate(
            briefs, "h1-fragment-briefs.schema.json"
        )
    except Exception as error:
        _fail("H1A_FRAGMENT_BRIEFS_INVALID", str(error))
    if briefs != expected_briefs:
        _fail("H1A_FRAGMENT_BRIEFS_INVALID", "brief projection")
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in _read(
            root / "execution-record.json", "H1A_PLAN_EXECUTION_INVALID"
        ).get("implementation_catalog", [])
        if isinstance(item, Mapping)
    }
    if set(catalog) != set(_implementation_paths()):
        _fail("H1A_IMPLEMENTATION_STALE", "implementation catalog")
    for implementation_id, source in _implementation_paths().items():
        reference = catalog[implementation_id]
        copied = rt.verify_artifact_reference(reference, root=root)
        if copied.read_bytes() != source.read_bytes():
            _fail("H1A_IMPLEMENTATION_STALE", implementation_id)
    implementation_refs = [catalog[key] for key in sorted(catalog)]
    execution = _read(
        root / "execution-record.json", "H1A_PLAN_EXECUTION_INVALID"
    )
    expected_execution = {
        "schema_version": "2.0",
        "run_id": p1_package_value["run_id"],
        "stage": "H1",
        "operation": "controlled-H1-A-plan",
        "h1_session_id": workspace["session_id"],
        "input_gate": input_gate.reference,
        "workspace_state": workspace_state.reference,
        "work_identity": work_identity,
        "p1_completion": p1_stage_ref,
        "generation_session": rt.artifact_reference(
            root / "generation-session.json", root=root
        ),
        "generation_evidence": evidence_refs,
        "outputs": {
            name: rt.artifact_reference(root / name, root=root)
            for name in (
                "source-inventory.json",
                "review-plan.json",
                "fragment-briefs.json",
            )
        },
        "implementation": implementation_refs,
        "implementation_catalog": [
            {"identity": key, "artifact": catalog[key]}
            for key in sorted(catalog)
        ],
    }
    if execution != expected_execution:
        _fail("H1A_PLAN_EXECUTION_INVALID", "execution binding")
    validation = _read(
        root / "validation.json", "H1A_PLAN_VALIDATION_INVALID"
    )
    expected_validation = _plan_validation(
        p1_package_value["run_id"], workspace["session_id"]
    )
    if validation != expected_validation:
        _fail("H1A_PLAN_VALIDATION_INVALID", "validation is stale")
    manifest = _read(
        root / "package-manifest.json", "H1A_PLAN_MANIFEST_INVALID"
    )
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("H1A_PLAN_MANIFEST_INVALID", str(error))
    actual_files = [
        reference
        for reference in _tree_inventory(root)
        if reference["path"] != "package-manifest.json"
    ]
    by_path = {item["path"]: item for item in actual_files}
    expected_roles = {
        "source_inventory": by_path["source-inventory.json"],
        "review_plan": by_path["review-plan.json"],
        "fragment_briefs": by_path["fragment-briefs.json"],
        "generation_session": by_path["generation-session.json"],
        "generation_evidence_index": by_path[
            "generation-evidence-index.json"
        ],
        "execution_record": by_path["execution-record.json"],
    }
    if (
        manifest.get("run_id") != p1_package_value["run_id"]
        or manifest.get("stage") != "H1"
        or manifest.get("package_profile") != "h1-plan"
        or manifest.get("verdict") != "ready"
        or manifest.get("session_id") != workspace["session_id"]
        or manifest.get("parent_state_sha256")
        != workspace_state.reference["sha256"]
        or manifest.get("artifact_roles") != expected_roles
        or manifest.get("validation") != by_path["validation.json"]
        or manifest.get("implementation") != implementation_refs
        or manifest.get("files") != actual_files
    ):
        _fail("H1A_PLAN_MANIFEST_INVALID", "manifest is not exact")
    return copy.deepcopy(validation)


def run_plan(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    input_gate: Any,
    workspace_state: Any,
    work_title: str,
    phase_submissions: Sequence[Mapping[str, Any]],
    coordinator: Any,
    logical_package_path: str = "H1/plan",
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> PlanReceipt:
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("H1A_OUTPUT_EXISTS", str(destination))
    contract_runtime = runtime or rt.ContractRuntime()
    p1_root, p1_package_value, p1_stage_ref, workspace = (
        _validate_plan_context(
            p1_package=p1_package,
            input_gate=input_gate,
            workspace_state=workspace_state,
            active_return_request=active_return_request,
            runtime=contract_runtime,
        )
    )
    p1_artifact_ref = _artifact_only(p1_stage_ref)
    work_identity = _work_identity(work_title, input_gate.reference)
    identity = _identity()
    phases = validate_plan_phases(phase_submissions)
    agent_plan = _validate_phase_payloads(phases)
    inventory = build_source_inventory(
        p1_root, p1_completion=p1_artifact_ref
    )
    validate_review_plan(
        agent_plan,
        source_inventory=inventory,
        workspace_state=workspace,
        work_identity=work_identity,
        runtime=contract_runtime,
    )
    original_p1_inventory = _tree_inventory(p1_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        _write_new(staging / "source-inventory.json", inventory)
        inventory_ref = rt.artifact_reference(
            staging / "source-inventory.json", root=staging
        )
        session = {
            "schema_version": "2.0",
            "run_id": p1_package_value["run_id"],
            "h1_session_id": workspace["session_id"],
            "operation": "controlled-H1-A-plan",
            "identity": identity,
            "phases": list(PLAN_PHASES),
            "source_inventory": inventory_ref,
            "workspace_state": workspace_state.reference,
            "work_identity": work_identity,
        }
        _write_new(staging / "generation-session.json", session)
        evidence_refs: list[dict[str, str]] = []
        prior = None
        for index, submission in enumerate(phases, 1):
            phase = submission["phase"]
            evidence = {
                "schema_version": "2.0",
                "run_id": p1_package_value["run_id"],
                "h1_session_id": workspace["session_id"],
                "identity": identity,
                "phase": phase,
                "phase_index": index,
                "prior_evidence": prior,
                "source_inventory": inventory_ref,
                "payload": submission["payload"],
                "payload_sha256": rt.canonical_sha256(
                    submission["payload"]
                ),
            }
            path = (
                staging
                / "generation-evidence"
                / f"{index:02d}-{phase}.json"
            )
            _write_new(path, evidence)
            prior = rt.artifact_reference(path, root=staging)
            evidence_refs.append(prior)
        _write_new(
            staging / "generation-evidence-index.json",
            {
                "schema_version": "2.0",
                "run_id": p1_package_value["run_id"],
                "h1_session_id": workspace["session_id"],
                "phases": list(PLAN_PHASES),
                "evidence": evidence_refs,
            },
        )
        _write_new(staging / "review-plan.json", agent_plan)
        plan_ref = rt.artifact_reference(
            staging / "review-plan.json", root=staging
        )
        briefs = {
            "schema_version": "2.0",
            "run_id": p1_package_value["run_id"],
            "h1_session_id": workspace["session_id"],
            "p1_completion": p1_artifact_ref,
            "review_plan": plan_ref,
            "briefs": agent_plan["fragment_briefs"],
        }
        contract_runtime.validate(
            briefs, "h1-fragment-briefs.schema.json"
        )
        _write_new(staging / "fragment-briefs.json", briefs)
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
            "run_id": p1_package_value["run_id"],
            "stage": "H1",
            "operation": "controlled-H1-A-plan",
            "h1_session_id": workspace["session_id"],
            "input_gate": input_gate.reference,
            "workspace_state": workspace_state.reference,
            "work_identity": work_identity,
            "p1_completion": p1_stage_ref,
            "generation_session": rt.artifact_reference(
                staging / "generation-session.json", root=staging
            ),
            "generation_evidence": evidence_refs,
            "outputs": {
                name: rt.artifact_reference(staging / name, root=staging)
                for name in (
                    "source-inventory.json",
                    "review-plan.json",
                    "fragment-briefs.json",
                )
            },
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
        }
        _write_new(staging / "execution-record.json", execution)
        _write_new(
            staging / "validation.json",
            _plan_validation(
                p1_package_value["run_id"], workspace["session_id"]
            ),
        )
        files = _tree_inventory(staging)
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": p1_package_value["run_id"],
            "stage": "H1",
            "package_profile": "h1-plan",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "source_inventory": by_path["source-inventory.json"],
                "review_plan": by_path["review-plan.json"],
                "fragment_briefs": by_path["fragment-briefs.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path[
                    "generation-evidence-index.json"
                ],
                "execution_record": by_path["execution-record.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
            "parent_state_sha256": workspace_state.reference["sha256"],
            "session_id": workspace["session_id"],
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write_new(staging / "package-manifest.json", manifest)
        validate_plan_package(
            staging,
            p1_package=p1_root,
            input_gate=input_gate,
            workspace_state=workspace_state,
            active_return_request=active_return_request,
            runtime=contract_runtime,
        )
        if original_p1_inventory != _tree_inventory(p1_root):
            _fail("H1A_P1_MUTATED", "P1 changed during plan generation")
        staging.replace(destination)
        validate_plan_package(
            destination,
            p1_package=p1_root,
            input_gate=input_gate,
            workspace_state=workspace_state,
            active_return_request=active_return_request,
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
            expected_next_state="planned",
            active_return_request=active_return_request,
        )
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return PlanReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        transition=transition,
    )


def _check_assembly_boundary(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ASSEMBLY_ROOT_FILES or any(
            relative.startswith(prefix)
            for prefix in _ASSEMBLY_ROOT_PREFIXES
        ):
            continue
        _fail("H1A_ASSEMBLY_PACKAGE_BOUNDARY_INVALID", relative)


def validate_assembly_workspace(
    workspace_state: Any,
    *,
    p1_completion: Mapping[str, str],
    plan_manifest: Mapping[str, str],
    fragment_manifest: Mapping[str, str],
    fragment_workspace_sha256: str,
    runtime: Any,
) -> dict[str, Any]:
    try:
        runtime.validate(
            workspace_state.data, "h1-workspace-state.schema.json"
        )
    except Exception as error:
        _fail("H1A_ASSEMBLY_WORKSPACE_INVALID", str(error))
    state = workspace_state.data
    if (
        state.get("state") != "fragments_ready"
        or state.get("p1_completion") != p1_completion
        or state.get("previous_state_sha256")
        != fragment_workspace_sha256
        or state.get("artifacts")
        != {
            "plan_manifest": dict(plan_manifest),
            "fragment_manifest": dict(fragment_manifest),
        }
        or rt.canonical_sha256(state)
        != workspace_state.reference.get("sha256")
    ):
        _fail(
            "H1A_ASSEMBLY_WORKSPACE_INVALID",
            "assembly requires exact same-session fragments_ready state",
        )
    return copy.deepcopy(state)


def validate_fragment_workspace(
    fragment_workspace_state: Any,
    *,
    p1_completion: Mapping[str, str],
    plan_manifest: Mapping[str, str],
    runtime: Any,
) -> dict[str, Any]:
    try:
        runtime.validate(
            fragment_workspace_state.data,
            "h1-workspace-state.schema.json",
        )
    except Exception as error:
        _fail("H1A_FRAGMENT_WORKSPACE_INVALID", str(error))
    state = fragment_workspace_state.data
    if (
        state.get("state") != "planned"
        or state.get("p1_completion") != p1_completion
        or not state.get("previous_state_sha256")
        or state.get("artifacts")
        != {"plan_manifest": dict(plan_manifest)}
        or rt.canonical_sha256(state)
        != fragment_workspace_state.reference.get("sha256")
    ):
        _fail(
            "H1A_FRAGMENT_WORKSPACE_INVALID",
            "formal H1-B input must be the exact planned workspace",
        )
    return copy.deepcopy(state)


def _validate_with_h1b(
    fragment_package: Path,
    *,
    p1_package: Path,
    plan_package: Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_workspace_state: Any,
    plan_active_return_request: Any | None,
    runtime: Any,
) -> None:
    try:
        h1b = importlib.import_module(
            "skills.novel-conception-fragment-writer.scripts.run_v2"
        )
        result = h1b.validate_fragment_package(
            fragment_package,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            workspace_state=fragment_workspace_state,
            plan_active_return_request=plan_active_return_request,
            runtime=runtime,
        )
    except Exception as error:
        _fail("H1A_H1B_VALIDATION_FAILED", str(error))
    if not isinstance(result, Mapping) or result.get("verdict") != "ready":
        _fail("H1A_H1B_VALIDATION_FAILED", "H1-B did not return ready")


def _validated_fragment_records(
    fragment_package: Path,
    *,
    plan: Mapping[str, Any],
    source_inventory: Mapping[str, Any],
    plan_manifest: Mapping[str, str],
    fragment_manifest: Mapping[str, str],
    p1_completion: Mapping[str, str],
    runtime: Any,
) -> list[dict[str, Any]]:
    package_value = _read(
        fragment_package / "fragment-package.json",
        "H1A_FRAGMENT_PACKAGE_INVALID",
    )
    try:
        runtime.validate(package_value, "fragment-package.schema.json")
    except Exception as error:
        _fail("H1A_FRAGMENT_PACKAGE_INVALID", str(error))
    if (
        package_value.get("run_id") != plan["run_id"]
        or package_value.get("h1_session_id") != plan["h1_session_id"]
        or package_value.get("p1_completion") != p1_completion
        or package_value.get("plan_manifest") != plan_manifest
        or package_value.get("authority_status")
        != "non_authoritative_sample"
    ):
        _fail("H1A_FRAGMENT_PACKAGE_INVALID", "fragment package lineage")
    actual_manifest = {
        "path": fragment_manifest["path"],
        "sha256": rt.sha256_file(fragment_package / "package-manifest.json"),
    }
    if actual_manifest != fragment_manifest:
        _fail("H1A_FRAGMENT_PACKAGE_INVALID", "fragment manifest binding")
    fragments = package_value.get("fragments")
    if not isinstance(fragments, list):
        _fail("H1A_FRAGMENT_PACKAGE_INVALID", "fragments")
    briefs = plan["fragment_briefs"]
    if len(fragments) != len(briefs):
        _fail("H1A_FRAGMENT_PACKAGE_INVALID", "fragment slot count")
    source_by_anchor = _source_id_map(source_inventory)
    normalized: list[dict[str, Any]] = []
    expected_fragment_keys = {
        "id",
        "title",
        "review_purpose",
        "text",
        "source_ids",
        "decision_control_ids",
    }
    for fragment, brief in zip(fragments, briefs):
        expected_source_ids = _source_ids(
            brief["source_anchor_ids"], source_by_anchor
        )
        if (
            not isinstance(fragment, Mapping)
            or set(fragment) != expected_fragment_keys
            or fragment.get("id") != brief["slot_id"]
            or fragment.get("title") != brief["title"]
            or fragment.get("review_purpose") != brief["review_purpose"]
            or fragment.get("source_ids") != expected_source_ids
            or fragment.get("decision_control_ids")
            != brief["decision_control_ids"]
            or not isinstance(fragment.get("text"), str)
            or not fragment["text"].strip()
        ):
            _fail(
                "H1A_FRAGMENT_PACKAGE_INVALID",
                f"fragment/brief projection drift at {brief['slot_id']}",
            )
        normalized.append(copy.deepcopy(dict(fragment)))
    return normalized


def _source_id_map(
    source_inventory: Mapping[str, Any],
) -> dict[str, str]:
    return {
        anchor["id"]: anchor["source_id"]
        for anchor in source_inventory["anchors"]
    }


def _source_ids(
    anchor_ids: Sequence[str], source_by_anchor: Mapping[str, str]
) -> list[str]:
    try:
        return sorted({source_by_anchor[item] for item in anchor_ids})
    except KeyError as error:
        _fail("H1A_ASSEMBLY_SOURCE_INVALID", str(error))


def _control_item(
    module: Mapping[str, Any], source_by_anchor: Mapping[str, str]
) -> dict[str, Any]:
    return {
        "id": module["id"],
        "title": module["title"],
        "definition": module["definition"],
        "responsibility": module["responsibility"],
        "must_hold": copy.deepcopy(module["must_hold"]),
        "must_not_imply": copy.deepcopy(module["must_not_imply"]),
        "source_ids": _source_ids(
            module["source_anchor_ids"], source_by_anchor
        ),
    }


def _project_visual_value(
    value: Any, source_by_anchor: Mapping[str, str]
) -> Any:
    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for key, item in value.items():
            if key == "source_anchor_ids":
                try:
                    projected["source_ids"] = [
                        source_by_anchor[anchor_id]
                        for anchor_id in item
                    ]
                except KeyError as error:
                    _fail("H1A_ASSEMBLY_SOURCE_INVALID", str(error))
                if len(projected["source_ids"]) != len(
                    set(projected["source_ids"])
                ):
                    _fail(
                        "H1A_ASSEMBLY_SOURCE_INVALID",
                        "visual anchor projection creates duplicate source ids",
                    )
            else:
                projected[key] = _project_visual_value(
                    item, source_by_anchor
                )
        return projected
    if isinstance(value, list):
        return [
            _project_visual_value(item, source_by_anchor)
            for item in value
        ]
    return copy.deepcopy(value)


def _assemble_report(
    plan: Mapping[str, Any],
    source_inventory: Mapping[str, Any],
    fragments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    source_by_anchor = _source_id_map(source_inventory)
    sections = {section["kind"]: section for section in plan["sections"]}
    modules = {
        kind: {
            module["id"]: module for module in sections[kind]["modules"]
        }
        for kind in SECTION_KINDS
    }
    projection = plan["assembly_projection"]

    def control_items(kind: str, field: str) -> list[dict[str, Any]]:
        return [
            _control_item(modules[kind][module_id], source_by_anchor)
            for module_id in projection[kind][field]
        ]

    def definitions(kind: str, field: str) -> list[str]:
        return [
            modules[kind][module_id]["definition"]
            for module_id in projection[kind][field]
        ]

    def section_sources(kind: str) -> list[str]:
        return sorted(
            {
                source_by_anchor[anchor_id]
                for module in modules[kind].values()
                for anchor_id in module["source_anchor_ids"]
            }
        )

    report_fragments = [
        {
            "id": fragment["id"],
            "title": fragment["title"],
            "review_purpose": fragment["review_purpose"],
            "text": fragment["text"],
            "source_ids": copy.deepcopy(fragment["source_ids"]),
            "decision_control_ids": copy.deepcopy(
                fragment["decision_control_ids"]
            ),
        }
        for fragment in fragments
    ]
    coverage_by_source: dict[str, list[str]] = {}
    for coverage in plan["control_coverage"]:
        source_id = source_by_anchor[coverage["source_anchor_id"]]
        coverage_by_source.setdefault(source_id, [])
        for visible_id in coverage["visible_element_ids"]:
            if visible_id not in coverage_by_source[source_id]:
                coverage_by_source[source_id].append(visible_id)
    report = {
        "schema_version": "2.0",
        "run_id": plan["run_id"],
        "h1_session_id": plan["h1_session_id"],
        "p1_completion": copy.deepcopy(plan["p1_completion"]),
        "title": plan["work_identity"]["report_title"],
        "review_budget": {
            "target_minutes": 10,
            "estimated_minutes": (
                sum(
                    item["estimated_seconds"]
                    for item in plan["budget_items"]
                )
                / 60
            ),
            "reading_baseline": "review-reading-baseline-v1",
        },
        "review_scope_contract": copy.deepcopy(
            plan["review_scope_contract"]
        ),
        "decision_controls": copy.deepcopy(plan["decision_controls"]),
        "review_path": copy.deepcopy(plan["review_path"]),
        "visual_models": [
            _project_visual_value(visual, source_by_anchor)
            for visual in plan["visual_models"]
        ],
        "world": {
            "definition": modules["world"][
                projection["world"]["definition_module_id"]
            ]["definition"],
            "operating_logic": modules["world"][
                projection["world"]["operating_logic_module_id"]
            ]["definition"],
            "systems": control_items("world", "system_module_ids"),
            "environments": control_items(
                "world", "environment_module_ids"
            ),
            "event_conditions": control_items(
                "world", "event_condition_module_ids"
            ),
            "constraints": definitions(
                "world", "constraint_module_ids"
            ),
            "boundaries": definitions("world", "boundary_module_ids"),
            "source_ids": section_sources("world"),
        },
        "storylines": {
            "story_subject": modules["storylines"][
                projection["storylines"]["story_subject_module_id"]
            ]["definition"],
            "lines": control_items("storylines", "line_module_ids"),
            "connections": control_items(
                "storylines", "connection_module_ids"
            ),
            "major_events": control_items(
                "storylines", "major_event_module_ids"
            ),
            "suspense_conflict_rhythm": modules["storylines"][
                projection["storylines"][
                    "suspense_conflict_rhythm_module_id"
                ]
            ]["definition"],
            "constraints": definitions(
                "storylines", "constraint_module_ids"
            ),
            "source_ids": section_sources("storylines"),
        },
        "characters": {
            "core_characters": control_items(
                "characters", "core_character_module_ids"
            ),
            "supporting_characters": control_items(
                "characters", "supporting_character_module_ids"
            ),
            "relationship_networks": control_items(
                "characters", "relationship_network_module_ids"
            ),
            "role_coverage": control_items(
                "characters", "role_coverage_module_ids"
            ),
            "constraints": definitions(
                "characters", "constraint_module_ids"
            ),
            "source_ids": section_sources("characters"),
        },
        "fragments": report_fragments,
        "decision_prompts": [
            {
                "id": prompt["id"],
                "question": prompt["question"],
                "affected_source_ids": _source_ids(
                    prompt["affected_source_anchor_ids"],
                    source_by_anchor,
                ),
                "allowed_decisions": copy.deepcopy(
                    prompt["allowed_decisions"]
                ),
            }
            for prompt in plan["decision_prompts"]
        ],
        "source_coverage": [
            {
                "source_id": source_id,
                "visible_element_ids": visible_ids,
            }
            for source_id, visible_ids in sorted(
                coverage_by_source.items()
            )
        ],
        "reduction_ledger": copy.deepcopy(plan["reduction_ledger"]),
        "drilldown_index": copy.deepcopy(plan["drilldown_index"]),
    }
    return report


_VISIBLE_INTERNAL_ID = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"MOD|DCTRL|SRC|PROJ|VIS|FRAG|PROMPT|ENV|SL|SLC|SLOT|DEMAND|CHR|"
    r"AFF|INST|TPH|MS|NM|EV|CONN|STATE|STEP|BIND|OBL|CLAIM|SEQ|UNIT|"
    r"ATOM|FACT|SYS|DEC|REL|COV|ARC|WR|IF|RF|TOK|DEP|CHD"
    r"|ACTOR|AUTH|ROLE|TOKEN|LIFECYCLE|PERMIT|INIT"
    r")-[A-Za-z0-9][A-Za-z0-9._-]*",
    re.IGNORECASE,
)
_VISIBLE_STAGE_ID = re.compile(
    r"(?<![A-Za-z0-9])(?:B0|S1|W1|E1|T1|C1|Q1|P1|H1(?:-[ABC])?)"
    r"(?![A-Za-z0-9])"
)
_VISIBLE_INTERNAL_STATUS = re.compile(
    r"(?<![A-Za-z0-9_])(?:NOT_STARTED|ACTIVE|SHUTDOWN|PENDING|READY|"
    r"SUPERSEDED|INVALIDATED|UNISSUED|ISSUED|UNCONSUMED|CONSUMED|"
    r"AVAILABLE|LOCKED|AUTHORIZED)(?![A-Za-z0-9_])"
)
_VISIBLE_HASH = re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])")
_VISIBLE_AUDIT_JARGON = re.compile(
    r"(?:Responsibility|Review scope|Review path|\bAllowed\b|"
    r"decision-control|evidence index|JSON Pointer|sha-?256|source[_ -]?anchor|"
    r"验证用途|评审用途|《《|》》|\[/?DEMAND(?::|\]))",
    re.IGNORECASE,
)
_VISIBLE_COPY_FORBIDDEN = re.compile(
    "|".join(
        (
            f"(?i:{_VISIBLE_INTERNAL_ID.pattern})",
            f"(?:{_VISIBLE_STAGE_ID.pattern})",
            f"(?:{_VISIBLE_INTERNAL_STATUS.pattern})",
            f"(?:{_VISIBLE_HASH.pattern})",
            f"(?i:{_VISIBLE_AUDIT_JARGON.pattern})",
        )
    )
)


def _append_visible(values: list[str], value: Any) -> None:
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        values.extend(item for item in value if isinstance(item, str))


def _human_visible_visual_strings(visual: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for field in ("title", "review_purpose"):
        _append_visible(values, visual.get(field))
    for collection, fields in (
        (
            "groups",
            ("label", "summary", "kind", "lane", "tier", "temporal_label"),
        ),
        ("nodes", ("label", "summary", "kind", "lane", "tier", "temporal_label")),
        (
            "edges",
            ("relation_label", "summary", "kind", "lane", "tier", "temporal_label"),
        ),
        ("text_equivalents", ("text",)),
    ):
        for item in visual.get(collection, []):
            if not isinstance(item, Mapping):
                continue
            for field in fields:
                _append_visible(values, item.get(field))
    return values


def _human_visible_plan_strings(plan: Mapping[str, Any]) -> list[str]:
    """Return every natural-language plan field that can reach report or brief copy."""

    values: list[str] = []
    work_identity = plan.get("work_identity", {})
    if isinstance(work_identity, Mapping):
        for field in ("work_title", "report_title"):
            _append_visible(values, work_identity.get(field))
    scope = plan.get("review_scope_contract", {})
    if isinstance(scope, Mapping):
        _append_visible(values, scope.get("semantic_disclaimer"))
    for control in plan.get("decision_controls", []):
        if not isinstance(control, Mapping):
            continue
        for field in ("statement", "must_hold", "must_not_imply"):
            _append_visible(values, control.get(field))
    for step in plan.get("review_path", []):
        if isinstance(step, Mapping):
            for field in ("title", "review_question"):
                _append_visible(values, step.get(field))
    for section in plan.get("sections", []):
        if not isinstance(section, Mapping):
            continue
        for field in ("title", "review_goal"):
            _append_visible(values, section.get(field))
        for module in section.get("modules", []):
            if not isinstance(module, Mapping):
                continue
            for field in (
                "title", "definition", "responsibility", "must_hold", "must_not_imply"
            ):
                _append_visible(values, module.get(field))
    for visual in plan.get("visual_models", []):
        if isinstance(visual, Mapping):
            values.extend(_human_visible_visual_strings(visual))
    for brief in plan.get("fragment_briefs", []):
        if not isinstance(brief, Mapping):
            continue
        for field in ("title", "review_purpose"):
            _append_visible(values, brief.get(field))
        limits = brief.get("information_limits", {})
        if isinstance(limits, Mapping):
            for field in ("may_present", "must_not_present_as_known"):
                _append_visible(values, limits.get(field))
        _append_visible(values, brief.get("allowed_perception_channels"))
        scene = brief.get("scene_contract", {})
        if isinstance(scene, Mapping):
            for field in (
                "before_state", "immediate_goal", "pressure", "obstacle",
                "required_choice", "direct_consequence", "after_state",
            ):
                _append_visible(values, scene.get(field))
        for field in ("required_demonstrations", "forbidden_additions"):
            _append_visible(values, brief.get(field))
    for prompt in plan.get("decision_prompts", []):
        if isinstance(prompt, Mapping):
            _append_visible(values, prompt.get("question"))
    return values


def _human_visible_report_strings(report: Mapping[str, Any]) -> list[str]:
    """Return author-visible text while excluding ids, hashes and bindings."""

    values: list[str] = [
        report["title"],
        report["review_scope_contract"]["semantic_disclaimer"],
    ]
    for control in report.get("decision_controls", []):
        for field in ("statement", "must_hold", "must_not_imply"):
            _append_visible(values, control.get(field))
    for step in report["review_path"]:
        values.extend((step["title"], step["review_question"]))
    for visual in report["visual_models"]:
        values.extend(_human_visible_visual_strings(visual))
    for section_name in ("world", "storylines", "characters"):
        section = report[section_name]
        for key, item in section.items():
            if key == "source_ids":
                continue
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, list):
                for child in item:
                    if isinstance(child, str):
                        values.append(child)
                    elif isinstance(child, Mapping):
                        values.extend(
                            str(child[field])
                            for field in ("title", "definition", "responsibility")
                            if isinstance(child.get(field), str)
                        )
                        for field in ("must_hold", "must_not_imply"):
                            if isinstance(child.get(field), list):
                                values.extend(
                                    str(value) for value in child[field]
                                    if isinstance(value, str)
                                )
    for fragment in report["fragments"]:
        values.extend(
            (fragment["title"], fragment["review_purpose"], fragment["text"])
        )
    values.extend(prompt["question"] for prompt in report["decision_prompts"])
    return values


def validate_human_visible_strings(values: Sequence[str]) -> None:
    for value in values:
        if not isinstance(value, str) or not value.strip():
            _fail("H1A_VISIBLE_COPY_INVALID", "visible copy must be non-empty text")
        match = _VISIBLE_COPY_FORBIDDEN.search(value)
        if match:
            _fail(
                "H1A_VISIBLE_COPY_INVALID",
                f"reader-facing copy exposes forbidden token: {match.group(0)}",
            )


def validate_human_visible_copy(report: Mapping[str, Any]) -> None:
    validate_human_visible_strings(_human_visible_report_strings(report))


def _render_report_markdown(report: Mapping[str, Any]) -> str:
    already_visible_definitions: set[str] = set()
    intro_timeline_edge_summaries: set[str] = set()

    def render_items(
        heading: str,
        items: Sequence[Mapping[str, Any]],
        *,
        seen_ids: set[str],
    ) -> None:
        fresh = [item for item in items if item["id"] not in seen_ids]
        if not fresh:
            return
        lines.extend([f"### {heading}", ""])
        for item in fresh:
            seen_ids.add(item["id"])
            lines.extend([f"#### {item['title']}", ""])
            if item["definition"] not in already_visible_definitions:
                lines.extend([item["definition"], ""])
            lines.extend([f"它在故事里的作用：{item['responsibility']}", ""])

    def render_texts(heading: str, items: Sequence[str]) -> None:
        if not items:
            return
        lines.extend([f"### {heading}", ""])
        for item in items:
            lines.extend([f"- {item}", ""])

    def render_texts_unless_expanded(
        heading: str,
        values: Sequence[str],
        item_groups: Sequence[Sequence[Mapping[str, Any]]],
    ) -> None:
        expanded_definitions = {
            item["definition"]
            for group in item_groups
            for item in group
        }
        render_texts(
            heading,
            [value for value in values if value not in expanded_definitions],
        )

    def render_scalar_unless_expanded(
        heading: str,
        value: str,
        item_groups: Sequence[Sequence[Mapping[str, Any]]],
    ) -> None:
        expanded_definitions = {
            item["definition"]
            for group in item_groups
            for item in group
        }
        if value in expanded_definitions:
            return
        lines.extend([f"### {heading}", "", value, ""])

    def humanize_visual_label(value: str) -> str:
        return value.replace(" / ", "与").replace(" + ", "与")

    timeline_visual = next(
        visual
        for visual in report["visual_models"]
        if visual["semantic_role"] == "major_event_timeline"
    )
    timeline_phases: list[list[Mapping[str, Any]]] = []
    for node in sorted(timeline_visual["nodes"], key=lambda item: item["order"]):
        if (
            not timeline_phases
            or timeline_phases[-1][0]["temporal_label"] != node["temporal_label"]
        ):
            timeline_phases.append([])
        timeline_phases[-1].append(node)

    def phase_summary(nodes: Sequence[Mapping[str, Any]]) -> str:
        parts: list[str] = []
        for node in nodes:
            summary = node["summary"].rstrip("。！？；")
            if summary.startswith(("他", "她", "它")):
                lane = node["lane"]
                if lane and all(separator not in lane for separator in ("与", "/", "+")):
                    summary = f"{lane}{summary[1:]}"
            parts.append(summary)
        return "；".join(parts)

    story_introduction = [report["world"]["definition"]]
    already_visible_definitions.add(report["world"]["definition"])
    ordered_timeline_edges = sorted(
        timeline_visual["edges"], key=lambda item: item["order"]
    )
    if ordered_timeline_edges:
        edge_summaries = [edge["summary"] for edge in ordered_timeline_edges]
        intro_timeline_edge_summaries.update(edge_summaries)
        chunk_size = max(1, (len(edge_summaries) + 2) // 3)
        chunks = [
            edge_summaries[index:index + chunk_size]
            for index in range(0, len(edge_summaries), chunk_size)
        ]
        introductions = ("故事从这里开始：", "随后，", "")
        for index, chunk in enumerate(chunks):
            prefix = introductions[min(index, len(introductions) - 1)]
            story_introduction.append(f"{prefix}{''.join(chunk)}")
    elif timeline_phases:
        opening = f"故事开始时，{phase_summary(timeline_phases[0])}。"
        if len(timeline_phases) > 1:
            opening += f"随后，{phase_summary(timeline_phases[1])}。"
        story_introduction.append(opening)
        middle_index = (len(timeline_phases) - 1) // 2
        if len(timeline_phases) >= 5 and middle_index not in (0, 1, len(timeline_phases) - 1):
            story_introduction.append(
                f"关系与危机逐渐加深时，{phase_summary(timeline_phases[middle_index])}。"
            )
        if len(timeline_phases) >= 3:
            ending_parts: list[str] = []
            if len(timeline_phases) > 3:
                ending_parts.append(
                    f"危机逼近结局时，{phase_summary(timeline_phases[-2])}。"
                )
            ending_parts.append(f"最后，{phase_summary(timeline_phases[-1])}。")
            story_introduction.append("".join(ending_parts))
    lines = [
        f"# {report['title']}",
        "",
        "## 这是一个怎样的故事",
        "",
        *[part for paragraph in story_introduction for part in (paragraph, "")],
        "## 先说在前面",
        "",
    ]
    lines.extend([report["review_scope_contract"]["semantic_disclaimer"], ""])
    lines.extend(["## 阅读顺序", ""])
    for step in report["review_path"]:
        lines.extend(
            [f"{step['order']}. {step['title']}：{step['review_question']}", ""]
        )
    lines.extend(["## 一眼看懂故事", ""])
    for visual in report["visual_models"]:
        lines.extend([f"### {visual['title']}", "", visual["review_purpose"], ""])
        kind = visual["visual_kind"]
        node_labels = {
            node["id"]: node["label"] for node in visual["nodes"]
        }
        group_headings = {
            "timeline": "故事线如何分组",
            "network": "关系分成哪几层",
        }
        node_headings = {
            "map": "图里的地点",
            "flow": "图里的关键步骤",
            "timeline": "时间线上的转折（同一阶段并列）",
            "network": "图里的人物与角色",
        }
        edge_headings = {
            "map": "地点之间怎样连接",
            "flow": "一步怎样推到下一步",
            "timeline": "转折怎样接上下一步",
            "network": "这些关系怎样改变选择",
        }
        if visual["groups"]:
            lines.extend([f"#### {group_headings.get(kind, '图如何分组')}", ""])
            for group in sorted(visual["groups"], key=lambda item: item["order"]):
                lines.extend(
                    [f"- {humanize_visual_label(group['label'])}：{group['summary']}", ""]
                )
        connected_node_ids = {
            endpoint
            for edge in visual["edges"]
            for endpoint in (edge["from_node_id"], edge["to_node_id"])
        }
        visible_edges = [
            edge
            for edge in visual["edges"]
            if not (
                kind == "timeline"
                and edge["summary"] in intro_timeline_edge_summaries
            )
        ]
        visible_nodes = list(visual["nodes"])
        if kind in ("flow", "network"):
            visible_nodes = [
                node for node in visual["nodes"] if node["id"] not in connected_node_ids
            ]
        if visible_nodes:
            lines.extend([f"#### {node_headings.get(kind, '图里的关键部分')}", ""])
            ordered_nodes = sorted(visible_nodes, key=lambda item: item["order"])
            if kind == "timeline":
                phase_names = {
                    f"P{index}": f"第{'一二三四五六七八九十'[index - 1]}阶段"
                    for index in range(1, 9)
                }
                timeline_presentations = {
                    "危机埋点": ("铺垫", "危机伏笔"),
                    "沈逾入场": ("铺垫", "沈逾进入任务"),
                    "死亡与汇流": ("转折", "顾衡死亡促成汇流"),
                    "生命探针": ("探问", "R-07 的新意识显现"),
                    "旧影与新情": ("关系变化", "顾衡旧记忆与 R-07 新感情"),
                    "伦理探针": ("探问", "伦理冲突显形"),
                    "人质转折": ("转折", "人质危机迫近"),
                    "决定影子": ("铺垫", "尚未说出口的决定"),
                    "威胁回收": ("回收", "威胁得到核验"),
                    "外部高潮": ("高潮", "现实行动完成阻断"),
                    "情感高潮": ("高潮", "沈逾执行最终告别"),
                    "关系回收": ("回收", "这段关系得到确认"),
                    "开放余波": ("余波", "仍然开放的问题"),
                }
                current_phase: str | None = None
                for node in ordered_nodes:
                    phase = node["temporal_label"]
                    if phase != current_phase:
                        lines.extend([f"##### {phase_names.get(phase, phase)}", ""])
                        current_phase = phase
                    lane = node["lane"]
                    if not lane.endswith("线"):
                        lane = f"{lane}{' 线' if re.search(r'[A-Za-z0-9]$', lane) else '线'}"
                    narrative_role, visible_label = timeline_presentations.get(
                        node["label"], ("推进", node["label"])
                    )
                    lines.extend(
                        [
                            f"- {narrative_role}｜{visible_label}：{node['summary']}"
                            f"（这一步属于“{humanize_visual_label(lane)}”。）",
                            "",
                        ]
                    )
            else:
                for node in ordered_nodes:
                    lines.extend([f"- {node['label']}：{node['summary']}", ""])
        if visible_edges:
            lines.extend([f"#### {edge_headings.get(kind, '它们怎样互相推动')}", ""])
            for edge in sorted(visible_edges, key=lambda item: item["order"]):
                if kind in ("flow", "timeline", "network"):
                    lines.extend([f"- {edge['summary']}", ""])
                    continue
                source = node_labels[edge["from_node_id"]]
                target = node_labels[edge["to_node_id"]]
                if edge["direction"] == "bidirectional":
                    relation = f"“{source}”与“{target}”"
                else:
                    relation = f"从“{source}”到“{target}”"
                lines.extend([f"- {relation}：{edge['summary']}", ""])
        if not visual["nodes"] and not visual["edges"]:
            for equivalent in visual["text_equivalents"]:
                lines.extend([f"- {equivalent['text']}", ""])
    world = report["world"]
    lines.extend(["## 这是什么故事，也看世界如何施压", ""])
    world_groups = (
        world["systems"],
        world["environments"],
        world["event_conditions"],
    )
    render_scalar_unless_expanded(
        "故事所在的世界", world["definition"], world_groups
    )
    render_scalar_unless_expanded(
        "世界怎样运转", world["operating_logic"], world_groups
    )
    seen_world: set[str] = set()
    render_items("关键机制", world["systems"], seen_ids=seen_world)
    render_items("故事发生的地方", world["environments"], seen_ids=seen_world)
    render_items(
        "推动局势变化的行动",
        world["event_conditions"],
        seen_ids=seen_world,
    )
    render_texts_unless_expanded(
        "必须守住的规则", world["constraints"], world_groups
    )
    render_texts_unless_expanded(
        "暂时不替作者下结论的边界", world["boundaries"], world_groups
    )

    storylines = report["storylines"]
    lines.extend(["## 为什么值得写，故事怎样发展", ""])
    storyline_groups = (
        storylines["lines"],
        storylines["connections"],
        storylines["major_events"],
    )
    render_scalar_unless_expanded(
        "故事真正追问什么",
        storylines["story_subject"],
        storyline_groups,
    )
    seen_story: set[str] = set()
    render_items("几条故事线", storylines["lines"], seen_ids=seen_story)
    render_items(
        "故事线怎样汇合",
        storylines["connections"],
        seen_ids=seen_story,
    )
    render_items(
        "推动人物改变的事件",
        storylines["major_events"],
        seen_ids=seen_story,
    )
    render_scalar_unless_expanded(
        "悬念、冲突与节奏",
        storylines["suspense_conflict_rhythm"],
        storyline_groups,
    )
    render_texts_unless_expanded(
        "故事不能越过的边界",
        storylines["constraints"],
        storyline_groups,
    )

    characters = report["characters"]
    lines.extend(["## 人物想要什么，又害怕什么", ""])
    seen_characters: set[str] = set()
    render_items(
        "故事中心的人",
        characters["core_characters"],
        seen_ids=seen_characters,
    )
    render_items(
        "推动局势的其他人物",
        characters["supporting_characters"],
        seen_ids=seen_characters,
    )
    render_items(
        "人物之间的关系",
        characters["relationship_networks"],
        seen_ids=seen_characters,
    )
    render_items(
        "人物在故事中的位置",
        characters["role_coverage"],
        seen_ids=seen_characters,
    )
    character_groups = (
        characters["core_characters"],
        characters["supporting_characters"],
        characters["relationship_networks"],
        characters["role_coverage"],
    )
    render_texts_unless_expanded(
        "人物不能被写成什么",
        characters["constraints"],
        character_groups,
    )
    lines.extend(["## 三个试读场景", ""])
    for fragment in report["fragments"]:
        lines.extend([f"### {fragment['title']}", "", fragment["text"], ""])
    lines.extend(["## 真正需要作者判断的问题", ""])
    for prompt in report["decision_prompts"]:
        lines.extend([prompt["question"], ""])
    markdown = "\n".join(lines).rstrip() + "\n"
    validate_human_visible_strings([markdown])
    return markdown


FIDELITY_DIMENSIONS = (
    "author_control_fidelity",
    "world_story_character_fidelity",
    "omission_and_emphasis_fidelity",
    "fragment_authority_boundary",
    "review_decision_integrity",
)


def _string_leaves(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [
            item
            for child in value.values()
            for item in _string_leaves(child)
        ]
    if isinstance(value, list):
        return [
            item for child in value for item in _string_leaves(child)
        ]
    return []


def _report_objects_by_id(report: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            object_id = value.get("id")
            if (
                isinstance(object_id, str)
                and re.fullmatch(r"(?:MOD|VIS|FRAG|PROMPT)-[A-Za-z0-9._-]+", object_id)
            ):
                if object_id in found:
                    _fail("H1A_FIDELITY_REVIEW_INVALID", f"duplicate report element {object_id}")
                found[object_id] = copy.deepcopy(dict(value))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(report)
    return found


def _fidelity_element_contract(
    plan: Mapping[str, Any], report: Mapping[str, Any]
) -> list[dict[str, Any]]:
    report_objects = _report_objects_by_id(report)
    contracts: list[dict[str, Any]] = []
    for element, anchor_field in _presentation_elements(plan):
        element_id = (
            element["slot_id"]
            if element["id"].startswith("BRIEF-")
            else element["id"]
        )
        if element_id not in report_objects:
            _fail("H1A_FIDELITY_REVIEW_INVALID", f"missing report element {element_id}")
        contracts.append(
            {
                "element_id": element_id,
                "content_sha256": rt.canonical_sha256(report_objects[element_id]),
                "source_anchor_ids": copy.deepcopy(element[anchor_field]),
                "expected_verdict": (
                    "non_authoritative_sample"
                    if element_id.startswith("FRAG-")
                    else "faithful"
                ),
                "_content": report_objects[element_id],
            }
        )
    if set(report_objects) != {item["element_id"] for item in contracts}:
        extra = sorted(set(report_objects) - {item["element_id"] for item in contracts})
        _fail("H1A_FIDELITY_REVIEW_INVALID", f"unplanned report elements: {extra}")
    return contracts


def validate_presentation_fidelity_review(
    review: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    report: Mapping[str, Any],
    p1_completion: Mapping[str, str],
    plan_manifest: Mapping[str, str],
    fragment_manifest: Mapping[str, str],
    plan_identity: Mapping[str, str],
    fragment_identity: Mapping[str, str],
    runtime: Any | None = None,
) -> dict[str, Any]:
    contract_runtime = runtime or rt.ContractRuntime()
    try:
        contract_runtime.validate(
            review, "presentation-fidelity-review.schema.json"
        )
    except Exception as error:
        _fail("H1A_FIDELITY_REVIEW_INVALID", str(error))
    reviewer = review["reviewer"]
    if reviewer in (plan_identity, fragment_identity) or (
        reviewer["task_id"] in {
            plan_identity.get("task_id"), fragment_identity.get("task_id")
        }
        or reviewer["thread_id"] in {
            plan_identity.get("thread_id"), fragment_identity.get("thread_id")
        }
    ):
        _fail("H1A_FIDELITY_REVIEW_NOT_INDEPENDENT", "reviewer reused producer identity")
    expected_inputs = {
        "p1_completion": copy.deepcopy(dict(p1_completion)),
        "plan_manifest": copy.deepcopy(dict(plan_manifest)),
        "fragment_manifest": copy.deepcopy(dict(fragment_manifest)),
        "report_sha256": rt.canonical_sha256(report),
    }
    if (
        review["run_id"] != plan["run_id"]
        or review["h1_session_id"] != plan["h1_session_id"]
        or review["inputs"] != expected_inputs
        or review["verdict"] != "pass"
        or review["blockers"] != []
        or [item["id"] for item in review["dimensions"]]
        != list(FIDELITY_DIMENSIONS)
    ):
        _fail("H1A_FIDELITY_REVIEW_INVALID", "review lineage or verdict drift")
    contracts = _fidelity_element_contract(plan, report)
    submitted = review["element_reviews"]
    if [item.get("element_id") for item in submitted] != [
        item["element_id"] for item in contracts
    ]:
        _fail("H1A_FIDELITY_REVIEW_INVALID", "element coverage or order drift")
    element_ids = {item["element_id"] for item in contracts}
    dimension_evidence = {
        element_id
        for dimension in review["dimensions"]
        for element_id in dimension["evidence_element_ids"]
    }
    if not dimension_evidence <= element_ids or dimension_evidence != element_ids:
        _fail("H1A_FIDELITY_REVIEW_INVALID", "dimension evidence does not cover all elements")
    for item, expected in zip(submitted, contracts):
        if (
            item["content_sha256"] != expected["content_sha256"]
            or item["source_anchor_ids"] != expected["source_anchor_ids"]
            or item["verdict"] != expected["expected_verdict"]
            or not all(
                item[field] is True
                for field in (
                    "no_material_omission",
                    "no_contradiction",
                    "no_authority_escalation",
                )
            )
        ):
            _fail("H1A_FIDELITY_REVIEW_INVALID", expected["element_id"])
        leaves = _string_leaves(expected["_content"])
        if any(
            not any(quote in leaf for leaf in leaves)
            for quote in item["evidence_quotes"]
        ):
            _fail(
                "H1A_FIDELITY_REVIEW_INVALID",
                f"{expected['element_id']} evidence is not exact report text",
            )
    return copy.deepcopy(dict(review))


def _assembly_validation(run_id: str, session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "H1",
        "operation": "H1-A-assemble",
        "session_id": session_id,
        "verdict": "ready",
        "checks": [
            "fragments-ready-same-session-workspace",
            "formal-H1-B-package-validation",
            "deterministic-plan-and-fragment-merge",
            "independent-presentation-fidelity-semantic-review",
            "human-review-report-schema",
            "manifest-and-implementation-binding",
        ],
        "errors": [],
    }


def validate_assembly_package(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_package: str | Path,
    fragment_workspace_state: Any,
    workspace_state: Any,
    plan_logical_package_path: str = "H1/plan",
    fragment_logical_package_path: str = "H1/fragments",
    plan_active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    plan_root = Path(plan_package).resolve()
    fragment_root = Path(fragment_package).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_assembly_boundary(root)
    validate_plan_package(
        plan_root,
        p1_package=p1_package,
        input_gate=plan_input_gate,
        workspace_state=plan_workspace_state,
        active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    plan = _read(plan_root / "review-plan.json", "H1A_REVIEW_PLAN_INVALID")
    inventory = _read(
        plan_root / "source-inventory.json",
        "H1A_SOURCE_INVENTORY_INVALID",
    )
    p1_stage_ref = _p1_reference(Path(p1_package).resolve())
    plan_manifest = {
        "path": f"{plan_logical_package_path}/package-manifest.json",
        "sha256": rt.sha256_file(plan_root / "package-manifest.json"),
    }
    fragment_manifest = {
        "path": f"{fragment_logical_package_path}/package-manifest.json",
        "sha256": rt.sha256_file(fragment_root / "package-manifest.json"),
    }
    fragment_workspace = validate_fragment_workspace(
        fragment_workspace_state,
        p1_completion=p1_stage_ref,
        plan_manifest=plan_manifest,
        runtime=contract_runtime,
    )
    workspace = validate_assembly_workspace(
        workspace_state,
        p1_completion=p1_stage_ref,
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        fragment_workspace_sha256=fragment_workspace_state.reference[
            "sha256"
        ],
        runtime=contract_runtime,
    )
    if (
        workspace["run_id"] != plan["run_id"]
        or workspace["session_id"] != plan["h1_session_id"]
        or fragment_workspace["run_id"] != plan["run_id"]
        or fragment_workspace["session_id"] != plan["h1_session_id"]
    ):
        _fail("H1A_ASSEMBLY_WORKSPACE_INVALID", "run/session mismatch")
    _validate_with_h1b(
        fragment_root,
        p1_package=Path(p1_package).resolve(),
        plan_package=plan_root,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_workspace_state=fragment_workspace_state,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    fragments = _validated_fragment_records(
        fragment_root,
        plan=plan,
        source_inventory=inventory,
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        p1_completion=_artifact_only(p1_stage_ref),
        runtime=contract_runtime,
    )
    expected_report = _assemble_report(plan, inventory, fragments)
    report = _read(
        root / "human-review-report.json",
        "H1A_ASSEMBLY_REPORT_INVALID",
    )
    try:
        contract_runtime.validate(
            report, "human-review-report.schema.json"
        )
    except Exception as error:
        _fail("H1A_ASSEMBLY_REPORT_INVALID", str(error))
    if report != expected_report:
        _fail(
            "H1A_ASSEMBLY_REPORT_INVALID",
            "report is not the deterministic projection",
        )
    validate_human_visible_copy(report)
    fidelity_review = _read(
        root / "presentation-fidelity-review.json",
        "H1A_FIDELITY_REVIEW_INVALID",
    )
    plan_session = _read(
        plan_root / "generation-session.json", "H1A_PLAN_SESSION_INVALID"
    )
    fragment_session = _read(
        fragment_root / "generation-session.json", "H1B_SESSION_INVALID"
    )
    validate_presentation_fidelity_review(
        fidelity_review,
        plan=plan,
        report=report,
        p1_completion=_artifact_only(p1_stage_ref),
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        plan_identity=plan_session["identity"],
        fragment_identity=fragment_session["identity"],
        runtime=contract_runtime,
    )
    try:
        markdown = (root / "human-review-report.md").read_text(
            encoding="utf-8"
        )
    except (OSError, UnicodeError) as error:
        _fail("H1A_ASSEMBLY_REPORT_INVALID", str(error))
    if markdown != _render_report_markdown(expected_report):
        _fail("H1A_ASSEMBLY_REPORT_INVALID", "Markdown projection drift")
    execution = _read(
        root / "assembly-execution.json",
        "H1A_ASSEMBLY_EXECUTION_INVALID",
    )
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping)
    }
    if set(catalog) != set(_implementation_paths()):
        _fail("H1A_IMPLEMENTATION_STALE", "implementation catalog")
    for implementation_id, source in _implementation_paths().items():
        reference = catalog[implementation_id]
        copied = rt.verify_artifact_reference(reference, root=root)
        if copied.read_bytes() != source.read_bytes():
            _fail("H1A_IMPLEMENTATION_STALE", implementation_id)
    implementation_refs = [catalog[key] for key in sorted(catalog)]
    expected_execution = {
        "schema_version": "2.0",
        "run_id": plan["run_id"],
        "stage": "H1",
        "operation": "H1-A-assemble",
        "h1_session_id": plan["h1_session_id"],
        "workspace_state": workspace_state.reference,
        "fragment_workspace_state": fragment_workspace_state.reference,
        "p1_completion": p1_stage_ref,
        "plan_manifest": plan_manifest,
        "fragment_manifest": fragment_manifest,
        "outputs": {
            name: rt.artifact_reference(root / name, root=root)
            for name in (
                "human-review-report.json",
                "human-review-report.md",
                "presentation-fidelity-review.json",
            )
        },
        "implementation": implementation_refs,
        "implementation_catalog": [
            {"identity": key, "artifact": catalog[key]}
            for key in sorted(catalog)
        ],
    }
    if execution != expected_execution:
        _fail("H1A_ASSEMBLY_EXECUTION_INVALID", "execution binding")
    expected_validation = _assembly_validation(
        plan["run_id"], plan["h1_session_id"]
    )
    validation = _read(
        root / "validation.json", "H1A_ASSEMBLY_VALIDATION_INVALID"
    )
    if validation != expected_validation:
        _fail("H1A_ASSEMBLY_VALIDATION_INVALID", "validation drift")
    manifest = _read(
        root / "package-manifest.json",
        "H1A_ASSEMBLY_MANIFEST_INVALID",
    )
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("H1A_ASSEMBLY_MANIFEST_INVALID", str(error))
    actual_files = [
        reference
        for reference in _tree_inventory(root)
        if reference["path"] != "package-manifest.json"
    ]
    by_path = {item["path"]: item for item in actual_files}
    expected_roles = {
        "human_review_report_json": by_path[
            "human-review-report.json"
        ],
        "human_review_report_md": by_path["human-review-report.md"],
        "presentation_fidelity_review": by_path[
            "presentation-fidelity-review.json"
        ],
        "execution_record": by_path["assembly-execution.json"],
    }
    if (
        manifest.get("run_id") != plan["run_id"]
        or manifest.get("stage") != "H1"
        or manifest.get("package_profile") != "h1-assembly"
        or manifest.get("verdict") != "ready"
        or manifest.get("session_id") != plan["h1_session_id"]
        or manifest.get("parent_state_sha256")
        != workspace_state.reference["sha256"]
        or manifest.get("artifact_roles") != expected_roles
        or manifest.get("validation") != by_path["validation.json"]
        or manifest.get("implementation") != implementation_refs
        or manifest.get("files") != actual_files
    ):
        _fail("H1A_ASSEMBLY_MANIFEST_INVALID", "manifest is not exact")
    return copy.deepcopy(validation)


def run_assemble(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_package: str | Path,
    fragment_workspace_state: Any,
    workspace_state: Any,
    coordinator: Any,
    logical_package_path: str = "H1/assembly",
    plan_logical_package_path: str = "H1/plan",
    fragment_logical_package_path: str = "H1/fragments",
    plan_active_return_request: Any | None = None,
    active_return_request: Any | None = None,
    fidelity_review: Mapping[str, Any] | None = None,
    runtime: Any | None = None,
) -> AssemblyReceipt:
    """Deterministically merge a formally validated H1-B package."""

    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("H1A_OUTPUT_EXISTS", str(destination))
    contract_runtime = runtime or rt.ContractRuntime()
    plan_root = Path(plan_package).resolve()
    fragment_root = Path(fragment_package).resolve()
    validate_plan_package(
        plan_root,
        p1_package=p1_package,
        input_gate=plan_input_gate,
        workspace_state=plan_workspace_state,
        active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    plan = _read(plan_root / "review-plan.json", "H1A_REVIEW_PLAN_INVALID")
    inventory = _read(
        plan_root / "source-inventory.json",
        "H1A_SOURCE_INVENTORY_INVALID",
    )
    p1_stage_ref = _p1_reference(Path(p1_package).resolve())
    plan_manifest = {
        "path": f"{plan_logical_package_path}/package-manifest.json",
        "sha256": rt.sha256_file(plan_root / "package-manifest.json"),
    }
    fragment_manifest = {
        "path": f"{fragment_logical_package_path}/package-manifest.json",
        "sha256": rt.sha256_file(fragment_root / "package-manifest.json"),
    }
    fragment_workspace = validate_fragment_workspace(
        fragment_workspace_state,
        p1_completion=p1_stage_ref,
        plan_manifest=plan_manifest,
        runtime=contract_runtime,
    )
    workspace = validate_assembly_workspace(
        workspace_state,
        p1_completion=p1_stage_ref,
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        fragment_workspace_sha256=fragment_workspace_state.reference[
            "sha256"
        ],
        runtime=contract_runtime,
    )
    if (
        workspace["run_id"] != plan["run_id"]
        or workspace["session_id"] != plan["h1_session_id"]
        or fragment_workspace["run_id"] != plan["run_id"]
        or fragment_workspace["session_id"] != plan["h1_session_id"]
    ):
        _fail("H1A_ASSEMBLY_WORKSPACE_INVALID", "run/session mismatch")
    _validate_with_h1b(
        fragment_root,
        p1_package=Path(p1_package).resolve(),
        plan_package=plan_root,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_workspace_state=fragment_workspace_state,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    fragments = _validated_fragment_records(
        fragment_root,
        plan=plan,
        source_inventory=inventory,
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        p1_completion=_artifact_only(p1_stage_ref),
        runtime=contract_runtime,
    )
    report = _assemble_report(plan, inventory, fragments)
    try:
        contract_runtime.validate(
            report, "human-review-report.schema.json"
        )
    except Exception as error:
        _fail("H1A_ASSEMBLY_REPORT_INVALID", str(error))
    validate_human_visible_copy(report)
    if fidelity_review is None:
        _fail("H1A_FIDELITY_REVIEW_REQUIRED", "independent semantic review is required")
    plan_session = _read(
        plan_root / "generation-session.json", "H1A_PLAN_SESSION_INVALID"
    )
    fragment_session = _read(
        fragment_root / "generation-session.json", "H1B_SESSION_INVALID"
    )
    fidelity_review_value = validate_presentation_fidelity_review(
        fidelity_review,
        plan=plan,
        report=report,
        p1_completion=_artifact_only(p1_stage_ref),
        plan_manifest=plan_manifest,
        fragment_manifest=fragment_manifest,
        plan_identity=plan_session["identity"],
        fragment_identity=fragment_session["identity"],
        runtime=contract_runtime,
    )
    markdown = _render_report_markdown(report)
    original_inputs = {
        "p1": _tree_inventory(Path(p1_package).resolve()),
        "plan": _tree_inventory(plan_root),
        "fragment": _tree_inventory(fragment_root),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        _write_new(staging / "human-review-report.json", report)
        _write_new(
            staging / "presentation-fidelity-review.json",
            fidelity_review_value,
        )
        (staging / "human-review-report.md").write_text(
            markdown, encoding="utf-8", newline=""
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
            "run_id": plan["run_id"],
            "stage": "H1",
            "operation": "H1-A-assemble",
            "h1_session_id": plan["h1_session_id"],
            "workspace_state": workspace_state.reference,
            "fragment_workspace_state": fragment_workspace_state.reference,
            "p1_completion": p1_stage_ref,
            "plan_manifest": plan_manifest,
            "fragment_manifest": fragment_manifest,
            "outputs": {
                name: rt.artifact_reference(
                    staging / name, root=staging
                )
                for name in (
                    "human-review-report.json",
                    "human-review-report.md",
                    "presentation-fidelity-review.json",
                )
            },
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
        }
        _write_new(
            staging / "assembly-execution.json", execution
        )
        _write_new(
            staging / "validation.json",
            _assembly_validation(plan["run_id"], plan["h1_session_id"]),
        )
        files = _tree_inventory(staging)
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": plan["run_id"],
            "stage": "H1",
            "package_profile": "h1-assembly",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "human_review_report_json": by_path[
                    "human-review-report.json"
                ],
                "human_review_report_md": by_path[
                    "human-review-report.md"
                ],
                "presentation_fidelity_review": by_path[
                    "presentation-fidelity-review.json"
                ],
                "execution_record": by_path[
                    "assembly-execution.json"
                ],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
            "parent_state_sha256": workspace_state.reference["sha256"],
            "session_id": plan["h1_session_id"],
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write_new(staging / "package-manifest.json", manifest)
        validate_assembly_package(
            staging,
            p1_package=p1_package,
            plan_package=plan_root,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_root,
            fragment_workspace_state=fragment_workspace_state,
            workspace_state=workspace_state,
            plan_logical_package_path=plan_logical_package_path,
            fragment_logical_package_path=fragment_logical_package_path,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
        )
        if original_inputs != {
            "p1": _tree_inventory(Path(p1_package).resolve()),
            "plan": _tree_inventory(plan_root),
            "fragment": _tree_inventory(fragment_root),
        }:
            _fail("H1A_ASSEMBLY_INPUT_MUTATED", "assembly input changed")
        staging.replace(destination)
        validate_assembly_package(
            destination,
            p1_package=p1_package,
            plan_package=plan_root,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_root,
            fragment_workspace_state=fragment_workspace_state,
            workspace_state=workspace_state,
            plan_logical_package_path=plan_logical_package_path,
            fragment_logical_package_path=fragment_logical_package_path,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
        )
        manifest_ref = {
            "path": f"{logical_package_path}/package-manifest.json",
            "sha256": rt.sha256_file(
                destination / "package-manifest.json"
            ),
        }
        transition = coordinator.accept_h1_workspace_transition(
            current_workspace=workspace_state,
            package_manifest=rt.SealedDocument(
                data=manifest, reference=manifest_ref
            ),
            expected_next_state="assembled",
            active_return_request=active_return_request,
        )
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return AssemblyReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        transition=transition,
    )


__all__ = [
    "PLAN_PHASES",
    "H1AError",
    "PlanReceipt",
    "AssemblyReceipt",
    "build_source_inventory",
    "validate_plan_workspace",
    "validate_plan_phases",
    "validate_review_plan",
    "validate_plan_package",
    "validate_assembly_workspace",
    "validate_fragment_workspace",
    "validate_assembly_package",
    "validate_human_visible_copy",
    "validate_human_visible_strings",
    "run_plan",
    "run_assemble",
]
