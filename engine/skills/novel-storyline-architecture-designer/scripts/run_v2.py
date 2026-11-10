"""Production S1 runner for autonomous novel-conception V2."""

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
import hashlib
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
stage_identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
PHASES = (
    "demand-scan",
    "line-design",
    "topology-and-consistency",
    "downstream-requirements",
    "final-storyline-model",
)
PHASE_FIELDS = {
    "demand-scan": ("storyline_demands",),
    "line-design": (
        "design_decisions",
        "storylines",
        "line_claim_authority",
        "source_sequence_realizations",
    ),
    "topology-and-consistency": (
        "connections",
        "architecture",
        "temporal_architecture",
        "story_claim_units",
        "story_claim_atoms",
        "story_obligation_register",
        "story_obligation_coverage",
        "cross_line_consistency",
    ),
    "downstream-requirements": (
        "world_requirements",
        "environment_requirements",
        "event_requirements",
        "character_requirements",
        "coverage_ledger",
        "authority_partition",
        "derivation_claims",
        "open_items",
    ),
    "final-storyline-model": ("model",),
}
LEGACY_PHASE_FIELDS = {
    **PHASE_FIELDS,
    "line-design": tuple(
        field
        for field in PHASE_FIELDS["line-design"]
        if field != "source_sequence_realizations"
    ),
}
CONSISTENCY_DIMENSIONS = (
    "time",
    "causality",
    "information",
    "authority",
    "state",
    "theme",
)
# Machine-audited inventory of the Phase-1-through-3 semantic rules that once
# existed only on the final-model path.  Both Phase 3 gates and final model
# validation now reach these codes through _validate_model's shared prefix.
UPSTREAM_ONLY_SEMANTIC_ERROR_CODES = (
    "S1_LINE_INCOMPLETE",
    "S1_OPTIONAL_ASSOCIATION_MISSING",
    "S1_TEMPORAL_PHASE_DUPLICATE",
    "S1_TEMPORAL_PHASE_ORDER_INVALID",
    "S1_TEMPORAL_PHASE_LINE_DANGLING",
    "S1_MILESTONE_DUPLICATE",
    "S1_MILESTONE_ORDER_INVALID",
    "S1_MILESTONE_PHASE_DANGLING",
    "S1_MILESTONE_LINE_DANGLING",
    "S1_MILESTONE_STATE_COVERAGE_MISMATCH",
    "S1_MILESTONE_STATE_INVALID",
    "S1_MILESTONE_CONNECTION_DANGLING",
    "S1_MILESTONE_CONNECTION_STATE_MISMATCH",
    "S1_MILESTONE_PHASE_ORDER_INVALID",
    "S1_TEMPORAL_PHASE_COVERAGE_MISMATCH",
    "S1_MILESTONE_CONNECTION_COVERAGE_MISMATCH",
    "S1_MILESTONE_LINE_COVERAGE_MISSING",
    "S1_MILESTONE_LINE_STATE_REGRESSION",
    "S1_MILESTONE_LINE_BOUNDARY_MISSING",
    "S1_GLOBAL_TEMPORAL_ANCHOR_UNSCHEDULED",
    "S1_CAUSAL_FIRST_OCCURRENCE_REVERSED",
    "S1_GLOBAL_STRICT_ORDER_INVALID",
    "S1_GLOBAL_RELATION_ORDER_INVALID",
    "S1_GLOBAL_INFORMATION_WINDOW_INVALID",
    "S1_NARRATIVE_MARKER_DUPLICATE",
    "S1_NARRATIVE_MARKER_KIND_MISSING",
    "S1_NARRATIVE_MARKER_MILESTONE_DANGLING",
    "S1_NARRATIVE_MARKER_LINE_MISMATCH",
    "S1_NARRATIVE_MARKER_REFERENCE_INVALID",
    "S1_NARRATIVE_MARKER_REFERENCE_FORWARD",
    "S1_PROBE_QUESTION_MISSING",
    "S1_PAYOFF_SETUP_MISSING",
    "S1_CLIMAX_CONVERGENCE_MISSING",
    "S1_MILESTONE_MARKER_MISSING",
    "S1_NARRATIVE_MARKER_LINE_COVERAGE_MISSING",
    "S1_CONSISTENCY_CHECK_DUPLICATE",
    "S1_CONSISTENCY_DIMENSION_DUPLICATE",
    "S1_CONSISTENCY_DIMENSIONS_MISMATCH",
    "S1_CONSISTENCY_SOURCE_COVERAGE_MISMATCH",
    "S1_CONSISTENCY_SOURCE_SEMANTICS_MISSING",
    "S1_CONSISTENCY_SOURCE_IN_GENERIC_WITNESS",
    "S1_CONSISTENCY_LINE_COVERAGE_MISSING",
    "S1_CONSISTENCY_TEMPORAL_COVERAGE_MISSING",
    "S1_CONSISTENCY_WITNESS_INVALID",
    "S1_CONSISTENCY_PLACEHOLDER",
    "S1_CONSISTENCY_CLAIM_NOT_FALSIFIABLE",
)
TOPOLOGY_SEMANTIC_REVIEW_DIMENSIONS = (
    "time",
    "causality",
    "information",
    "state",
    "source-sequence",
    "overcorrection",
)
TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL = "topology-information-semantics-v1"
LINE_REVIEW_PROTOCOL = "line-claim-and-source-sequence-semantics-v2"
CURRENT_CONTRACT_REVISION = "s1-bounded-v2-2026-08"
LINE_CLAIM_DISPOSITIONS = (
    "source_bound",
    "s1_structural_derivation",
    "downstream_requirement",
    "open_item",
)
_DECISION_CONCLUSION_FIELDS = (
    "selection",
    "authority_basis",
    "compatibility",
    "cost",
    "downstream_freedom",
    "single_option_exclusion_evidence",
)
_STORYLINE_CONCLUSION_FIELDS = (
    "responsibility",
    "goal",
    "pressure",
    "start_state",
    "state_changes",
    "end_state",
    "downstream_freedom",
)
_TARGET_REQUIREMENT_PREFIX = {
    "W1": "WR-",
    "E1": "END-",
    "T1": "EVD-",
    "C1": "CHD-",
}
_PLACEHOLDER = re.compile(
    r"(?i)(?:\b(?:tbd|todo|placeholder|lorem\s+ipsum|xxx)\b|"
    r"待定|未定义|占位)"
)
_ASCII_QUESTION_DAMAGE = re.compile(r"\?{3,}")
_HIGH_CONFIDENCE_MOJIBAKE = re.compile(
    r"(?:Ã[\u0080-\u00bf]|Â[\u0080-\u00bf]).{0,24}"
    r"(?:Ã[\u0080-\u00bf]|Â[\u0080-\u00bf])"
)


class S1Error(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class S1RunReceipt:
    package_root: Path
    model: dict[str, Any]
    manifest: dict[str, Any]
    completion: Any
    transition: Any


def _fail(code: str, message: str) -> None:
    raise S1Error(code, message)


def _validate_authority_disjoint(partition: Mapping[str, Any]) -> None:
    names = (
        "author_locked",
        "autonomous_owned",
        "downstream_freedom",
        "author_open",
    )
    values = {name: set(partition[name]) for name in names}
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = sorted(values[left] & values[right])
            if overlap:
                _fail(
                    "S1_AUTHORITY_PARTITION_OVERLAP",
                    f"{left}/{right}: {overlap}",
                )


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


def _logical(prefix: str, name: str) -> str:
    value = PurePosixPath(prefix, name).as_posix() if prefix else name
    if value.startswith("/") or ".." in PurePosixPath(value).parts:
        _fail("S1_PATH_INVALID", value)
    return value


def _path_lexists(path: Path) -> bool:
    """Return true for every occupied target, including dangling symlinks."""

    return os.path.lexists(os.fspath(path))


def _create_package_staging(destination: Path) -> Path:
    """Create a bounded-name, same-volume directory for atomic publication.

    The package tree can contain immutable review directories whose names are
    SHA-256 values.  Repeating the (potentially long) destination name in a
    temporary parent and adding another ``package`` component can therefore
    exceed the legacy Windows path limit even though the final package fits.
    The staging directory itself is the package root and uses a fixed short
    prefix.  Keeping it beside the destination also makes the final rename a
    same-volume operation.
    """

    parent = destination.parent.resolve()
    if _path_lexists(destination):
        _fail("S1_OUTPUT_EXISTS", str(destination))
    temporary = Path(tempfile.mkdtemp(prefix=".s1-", dir=parent))
    try:
        resolved = temporary.resolve(strict=True)
        if resolved.parent != parent:
            _fail("S1_STAGING_INVALID", str(resolved))
        if os.stat(resolved).st_dev != os.stat(parent).st_dev:
            _fail("S1_STAGING_CROSS_VOLUME", str(resolved))
        return resolved
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _publish_package_staging(staging: Path, destination: Path) -> None:
    """Publish one complete package without replacing an occupied target."""

    if _path_lexists(destination):
        _fail("S1_OUTPUT_EXISTS", str(destination))
    try:
        staging.rename(destination)
    except FileExistsError:
        _fail("S1_OUTPUT_EXISTS", str(destination))


S1_RUNTIME_DEPENDENCIES = (
    "canonical.py",
    "contracts.py",
    "coordinator.py",
    "stage_implementation_identity.py",
)

S1_SCHEMA_DEPENDENCIES = (
    "storyline-architecture.schema.json",
    "canonical-common.schema.json",
    "common-defs.schema.json",
    "input-gate.schema.json",
    "package-manifest.schema.json",
    "stage-completion.schema.json",
)


def _implementation_paths() -> dict[str, Path]:
    runtime_dir = _REPO / "harnesses" / "novel-conception-autonomous" / "runtime"
    values = {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/runtime-contract.md": _SKILL / "references" / "runtime-contract.md",
    }
    for name in S1_RUNTIME_DEPENDENCIES:
        values[f"runtime/{name}"] = runtime_dir / name
    for name in S1_SCHEMA_DEPENDENCIES:
        values[f"schemas/{name}"] = _SCHEMAS / name
    return values


def _controls(b0_root: Path, baseline: Mapping[str, Any]) -> list[dict[str, Any]]:
    registry = {item["id"]: item for item in baseline["control_registry"]}
    found: list[dict[str, Any]] = []
    for entry in baseline["design_artifacts"]:
        source = rt.verify_artifact_reference(entry["artifact"], root=b0_root)
        for value in rt.extract_controls(source, entry["domain"]):
            registered = registry.get(value["id"])
            if registered is None:
                _fail("S1_B0_CONTROL_MISMATCH", value["id"])
            found.append(
                {
                    **value,
                    "domain": entry["domain"],
                    "source_locator": {
                        "control_id": value["id"],
                        "artifact": copy.deepcopy(registered["artifact"]),
                        "selector": f"control:{value['id']}",
                        "value_sha256": registered["value_sha256"],
                    },
                }
            )
    found.sort(key=lambda item: item["id"])
    return found


def _control_text(value: Any) -> str:
    return value if isinstance(value, str) else rt.canonical_json(value)


_ARROW = re.compile(r"(?:->|=>|→|⇒|⟶)")
_NUMBERED = re.compile(r"^\s*\d+[.)、:：]\s+\S")
_TABLE_SEPARATOR = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_SENTENCE = re.compile(r"[^。！？!?；;]+[。！？!?；;]?", re.MULTILINE)


def _text_claim_units(text: str, pointer: str) -> list[dict[str, Any]]:
    """Split structural source syntax without inferring domain semantics."""

    line_records: list[tuple[int, int, str]] = []
    cursor = 0
    for raw in text.splitlines(keepends=True):
        body = raw.rstrip("\r\n")
        line_records.append((cursor, cursor + len(body), body))
        cursor += len(raw)
    if not line_records and text:
        line_records.append((0, len(text), text))
    semantic = [
        item
        for item in line_records
        if item[2].strip() and not item[2].strip().startswith("```")
    ]
    units: list[dict[str, Any]] = []

    def add(kind: str, mode: str, start: int, end: int, value: str) -> None:
        units.append(
            {
                "source_pointer": pointer,
                "start_offset": start,
                "end_offset": end,
                "kind": kind,
                "relation_mode": mode,
                "text": value,
            }
        )

    index = 0
    while index < len(semantic):
        start, end, line = semantic[index]
        stripped = line.strip()
        if _TABLE_SEPARATOR.match(stripped):
            index += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            next_is_separator = (
                index + 1 < len(semantic)
                and bool(_TABLE_SEPARATOR.match(semantic[index + 1][2].strip()))
            )
            if not next_is_separator:
                add("table_row", "candidate", start, end, line)
            index += 1
            continue
        if _NUMBERED.match(line):
            block: list[tuple[int, int, str]] = []
            while index < len(semantic) and _NUMBERED.match(semantic[index][2]):
                block.append(semantic[index])
                index += 1
            for item_start, item_end, item_text in block:
                add("numbered_step", "none", item_start, item_end, item_text)
            for left, right in zip(block, block[1:]):
                add(
                    "ordered_link",
                    "candidate",
                    left[0],
                    right[1],
                    text[left[0] : right[1]],
                )
            continue

        # A continuation chain is written as one head line followed by lines
        # whose first semantic token is an arrow.
        if (
            index + 1 < len(semantic)
            and _ARROW.match(semantic[index + 1][2].lstrip())
            and not _ARROW.search(line)
        ):
            nodes = [(start, end, line)]
            index += 1
            while index < len(semantic):
                item_start, item_end, item_text = semantic[index]
                match = _ARROW.match(item_text.lstrip())
                if match is None:
                    break
                leading = len(item_text) - len(item_text.lstrip())
                node_start = item_start + leading + match.end()
                while node_start < item_end and text[node_start].isspace():
                    node_start += 1
                nodes.append((node_start, item_end, text[node_start:item_end]))
                index += 1
            for left, right in zip(nodes, nodes[1:]):
                add(
                    "arrow_link",
                    "required",
                    left[0],
                    right[1],
                    text[left[0] : right[1]],
                )
            continue

        arrows = list(_ARROW.finditer(line))
        if arrows:
            bounds = [0, *[match.start() for match in arrows], len(line)]
            node_bounds: list[tuple[int, int]] = []
            previous = 0
            for match in arrows:
                left_start, left_end = previous, match.start()
                while left_start < left_end and line[left_start].isspace():
                    left_start += 1
                while left_end > left_start and line[left_end - 1].isspace():
                    left_end -= 1
                node_bounds.append((left_start, left_end))
                previous = match.end()
            right_start, right_end = previous, len(line)
            while right_start < right_end and line[right_start].isspace():
                right_start += 1
            while right_end > right_start and line[right_end - 1].isspace():
                right_end -= 1
            node_bounds.append((right_start, right_end))
            for arrow_index, match in enumerate(arrows):
                link_start = start + node_bounds[arrow_index][0]
                link_end = start + node_bounds[arrow_index + 1][1]
                add(
                    "arrow_link",
                    "required",
                    link_start,
                    link_end,
                    text[link_start:link_end],
                )
            index += 1
            continue

        sentence_found = False
        for match in _SENTENCE.finditer(line):
            value = match.group(0)
            if not value.strip():
                continue
            local_start, local_end = match.span()
            while local_start < local_end and line[local_start].isspace():
                local_start += 1
            while local_end > local_start and line[local_end - 1].isspace():
                local_end -= 1
            add(
                "sentence",
                "none",
                start + local_start,
                start + local_end,
                line[local_start:local_end],
            )
            sentence_found = True
        if not sentence_found:
            add("sentence", "none", start, end, line)
        index += 1
    return units


def _claim_units_for_control(control: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_units: list[dict[str, Any]] = []

    def walk(value: Any, pointer: str) -> None:
        if isinstance(value, str):
            raw_units.extend(_text_claim_units(value, pointer))
        elif isinstance(value, Mapping):
            for key in sorted(value):
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                walk(value[key], f"{pointer}/{escaped}")
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for index, item in enumerate(value):
                walk(item, f"{pointer}/{index}")
        else:
            text = rt.canonical_json(value)
            raw_units.append(
                {
                    "source_pointer": pointer,
                    "start_offset": 0,
                    "end_offset": len(text),
                    "kind": "structured_leaf",
                    "relation_mode": "none",
                    "text": text,
                }
            )
    walk(control["value"], "")
    if not raw_units:
        text = _control_text(control["value"])
        raw_units.append(
            {
                "source_pointer": "",
                "start_offset": 0,
                "end_offset": len(text),
                "kind": "structured_leaf",
                "relation_mode": "none",
                "text": text,
            }
        )
    result = []
    for ordinal, unit in enumerate(raw_units, 1):
        result.append(
            {
                "id": f"SCU-{control['id']}-{ordinal:03d}",
                "control_id": control["id"],
                "source_locator": copy.deepcopy(control["source_locator"]),
                "ordinal": ordinal,
                **unit,
                "text_sha256": hashlib.sha256(
                    unit["text"].encode("utf-8")
                ).hexdigest(),
            }
        )
    return result


def _expected_claim_units(
    controls: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [unit for control in controls for unit in _claim_units_for_control(control)]


def _source_unit_is_ordered(unit: Mapping[str, Any]) -> bool:
    """Return whether source semantics declare an order that cannot collapse."""

    return unit.get("relation_mode") == "required" or unit.get("kind") == "ordered_link"


def _phase_fields_for_session(
    session: Mapping[str, Any], phase: str
) -> tuple[str, ...]:
    """Return the immutable phase shape selected when the session started.

    Sessions created before the source-sequence protocol remain verifiable, but
    only newly created sessions may be advanced by production.
    """

    fields = (
        PHASE_FIELDS
        if session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
        else LEGACY_PHASE_FIELDS
    )
    return fields[phase]


def _value_participates(control_value: Any, artifact_value: Any) -> bool:
    """Return whether an exact control value participates in an artifact tree.

    Searching a serialized JSON document is not semantically sound: JSON
    escaping changes newlines, quotes, and backslashes, so a verbatim multiline
    author control can be present in a string field yet fail a raw substring
    test.  Traverse the in-memory value instead.  String controls must appear
    verbatim in a string leaf; structured controls must occur as an exact
    subtree (and may also be carried by their canonical textual form).
    """

    if artifact_value == control_value:
        return True
    if isinstance(artifact_value, str):
        expected = _control_text(control_value)
        return expected in artifact_value
    if isinstance(artifact_value, Mapping):
        return any(
            _value_participates(control_value, value)
            for value in artifact_value.values()
        )
    if isinstance(artifact_value, Sequence) and not isinstance(
        artifact_value, (str, bytes, bytearray)
    ):
        return any(
            _value_participates(control_value, value)
            for value in artifact_value
        )
    return False


def _line_conclusion_leaves(
    line_payload: Mapping[str, Any],
) -> list[tuple[str, str]]:
    """Return every authoritative free-text leaf in deterministic pointer order."""

    result: list[tuple[str, str]] = []
    for root_name, fields in (
        ("design_decisions", _DECISION_CONCLUSION_FIELDS),
        ("storylines", _STORYLINE_CONCLUSION_FIELDS),
    ):
        objects = line_payload.get(root_name)
        if not isinstance(objects, list):
            _fail(
                "S1_LINE_CLAIM_COVERAGE_INVALID",
                f"{root_name} must be a list",
            )
        for index, item in enumerate(objects):
            if not isinstance(item, Mapping):
                _fail(
                    "S1_LINE_CLAIM_COVERAGE_INVALID",
                    f"/{root_name}/{index} must be an object",
                )
            for field in fields:
                if field not in item:
                    continue
                value = item[field]
                pointer = f"/{root_name}/{index}/{field}"
                if isinstance(value, str):
                    if not value:
                        _fail(
                            "S1_LINE_CLAIM_COVERAGE_INVALID",
                            f"{pointer} must not be empty",
                        )
                    result.append((pointer, value))
                elif field == "state_changes" and isinstance(value, list):
                    for child_index, child in enumerate(value):
                        child_pointer = f"{pointer}/{child_index}"
                        if not isinstance(child, str) or not child:
                            _fail(
                                "S1_LINE_CLAIM_COVERAGE_INVALID",
                                f"{child_pointer} must be non-empty text",
                            )
                        result.append((child_pointer, child))
                else:
                    _fail(
                        "S1_LINE_CLAIM_COVERAGE_INVALID",
                        f"{pointer} must be text",
                    )
    return result


def _source_fragment_intervals(
    text: str, controls: Sequence[Mapping[str, Any]]
) -> list[tuple[int, int]]:
    """Select a deterministic non-overlapping set of exact B0 fragments."""

    candidates: set[tuple[int, int]] = set()
    for control in controls:
        for fragment in (control["heading"], _control_text(control["value"])):
            if not fragment:
                continue
            cursor = 0
            while True:
                start = text.find(fragment, cursor)
                if start < 0:
                    break
                candidates.add((start, start + len(fragment)))
                cursor = start + 1
    selected: list[tuple[int, int]] = []
    cursor = 0
    ordered = sorted(candidates, key=lambda item: (item[0], -(item[1] - item[0])))
    while True:
        available = [item for item in ordered if item[0] >= cursor]
        if not available:
            break
        start = available[0][0]
        interval = max(
            (item for item in available if item[0] == start),
            key=lambda item: item[1],
        )
        selected.append(interval)
        cursor = interval[1]
    return selected


def inspect_s1_line_claims(
    line_payload: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build the exact non-overlapping span universe the Agent must adjudicate."""

    claims: list[dict[str, Any]] = []
    for pointer, text_value in _line_conclusion_leaves(line_payload):
        intervals = _source_fragment_intervals(text_value, controls)
        boundaries: list[tuple[int, int]] = []
        cursor = 0
        for start, end in intervals:
            if start > cursor:
                boundaries.append((cursor, start))
            boundaries.append((start, end))
            cursor = end
        if cursor < len(text_value):
            boundaries.append((cursor, len(text_value)))
        if not boundaries:
            boundaries.append((0, len(text_value)))
        for start, end in boundaries:
            text = text_value[start:end]
            claim_id = (
                "LCA-"
                + rt.canonical_sha256([pointer, start, end, text])[:20]
            )
            claims.append(
                {
                    "claim_id": claim_id,
                    "pointer": pointer,
                    "start_offset": start,
                    "end_offset": end,
                    "text": text,
                    "text_sha256": rt.canonical_sha256(text),
                }
            )
    if len({item["claim_id"] for item in claims}) != len(claims):
        _fail("S1_LINE_CLAIM_COVERAGE_INVALID", "claim IDs collide")
    return claims


def _contains_placeholder(value: str) -> bool:
    return bool(_PLACEHOLDER.search(" ".join(value.split())))


def _validate_agent_text(value: Any, *, path: str = "$") -> None:
    """Fail closed on high-confidence encoding damage in Agent payloads."""

    if isinstance(value, str):
        reason = None
        if "\ufffd" in value:
            reason = "Unicode replacement character"
        elif _ASCII_QUESTION_DAMAGE.search(value):
            reason = "three or more consecutive ASCII question marks"
        elif "锟斤拷" in value:
            reason = "known replacement mojibake"
        elif _HIGH_CONFIDENCE_MOJIBAKE.search(value):
            reason = "repeated UTF-8/Latin-1 mojibake pairs"
        if reason is not None:
            _fail("S1_TEXT_ENCODING_CORRUPT", f"{path}: {reason}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _validate_agent_text(child, path=f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value):
            _validate_agent_text(child, path=f"{path}[{index}]")


StateAnchor = tuple[str, int]
StateCausalGraph = dict[StateAnchor, set[StateAnchor]]


def _build_state_causal_graph(
    lines: Mapping[str, Mapping[str, Any]],
    connections: Sequence[Mapping[str, Any]],
) -> StateCausalGraph:
    """Build the one authoritative implementation graph for S1 causality."""

    graph: StateCausalGraph = {}
    for line_id, line in lines.items():
        final_index = len(line["state_changes"]) + 1
        for state_index in range(final_index + 1):
            graph[(line_id, state_index)] = set()
        for state_index in range(final_index):
            graph[(line_id, state_index)].add((line_id, state_index + 1))
    for connection in connections:
        if connection.get("relation") != "causal":
            continue
        source = (
            connection.get("from_storyline_id"),
            connection.get("from_state_index"),
        )
        target = (
            connection.get("to_storyline_id"),
            connection.get("to_state_index"),
        )
        if source not in graph or target not in graph:
            _fail(
                "S1_CONNECTION_STATE_INVALID",
                str(connection.get("id", f"{source}->{target}")),
            )
        graph[source].add(target)
    return graph


def _validate_physical_connection_uniqueness(
    connections: Sequence[Mapping[str, Any]],
) -> None:
    """Reject two IDs for the same exact physical endpoint/relation edge."""

    seen: dict[tuple[Any, ...], str] = {}
    for connection in connections:
        signature = (
            connection.get("relation"),
            connection.get("from_storyline_id"),
            connection.get("from_state_index"),
            connection.get("from_state"),
            connection.get("to_storyline_id"),
            connection.get("to_state_index"),
            connection.get("to_state"),
        )
        previous = seen.get(signature)
        if previous is not None:
            _fail(
                "S1_CONNECTION_ENDPOINT_DUPLICATE",
                f"{previous} and {connection.get('id')} duplicate one physical edge",
            )
        seen[signature] = str(connection.get("id"))


def _validate_state_causal_dag(graph: StateCausalGraph) -> None:
    """Reject cycles in the complete state graph, never in its line projection."""

    indegree = {node: 0 for node in graph}
    for targets in graph.values():
        for target in targets:
            indegree[target] += 1
    frontier = sorted(node for node, degree in indegree.items() if degree == 0)
    consumed = 0
    while frontier:
        node = frontier.pop()
        consumed += 1
        for target in sorted(graph[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                frontier.append(target)
    if consumed != len(graph):
        blocked = sorted(node for node, degree in indegree.items() if degree > 0)
        _fail("S1_STATE_CAUSAL_CYCLE", f"cycle reaches state anchors {blocked}")


def _reachable_state_anchors(
    graph: StateCausalGraph, source: StateAnchor
) -> set[StateAnchor]:
    visited = {source}
    frontier = list(graph[source])
    while frontier:
        current = frontier.pop()
        if current in visited:
            continue
        visited.add(current)
        frontier.extend(graph[current] - visited)
    return visited


def _state_reachable(
    graph: StateCausalGraph, source: StateAnchor, target: StateAnchor
) -> bool:
    return target in _reachable_state_anchors(graph, source)


def _validate_structural_state_closure(
    lines: Mapping[str, Mapping[str, Any]], graph: StateCausalGraph
) -> None:
    """Require every structural side line to have a state path into main."""

    main_ids = [line_id for line_id, line in lines.items() if line["type"] == "main"]
    if len(main_ids) != 1:
        _fail("S1_MAIN_TRUNK_INVALID", "exactly one main storyline is required")
    main_id = main_ids[0]
    for line_id, line in lines.items():
        if (
            line_id == main_id
            or line["type"] == "optional_melody"
            or line.get("closure_mode") == "terminal_consequence"
        ):
            continue
        reachable = _reachable_state_anchors(graph, (line_id, 0))
        if not any(anchor[0] == main_id for anchor in reachable):
            _fail("S1_STRUCTURAL_CAUSAL_CLOSURE_MISSING", line_id)


def _validate_line_closure_declarations(
    line_payload: Mapping[str, Any],
    *,
    required: bool,
    connections: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """Validate explicit convergence versus terminal-consequence closure."""

    if not required:
        return
    code = "S1_STORYLINE_CLOSURE_DECLARATION_INVALID"
    lines = {item.get("id"): item for item in line_payload.get("storylines", [])}
    terminal_lines: dict[str, Mapping[str, Any]] = {}
    closure_fields = {
        "closure_mode", "terminal_source_anchor", "terminal_entry_connection_id"
    }
    for line_id, line in lines.items():
        if not closure_fields.issubset(line):
            _fail(code, f"{line_id} lacks current closure fields")
        mode = line.get("closure_mode")
        source_anchor = line.get("terminal_source_anchor")
        entry_id = line.get("terminal_entry_connection_id")
        if line.get("type") in {"main", "optional_melody"}:
            if any(value is not None for value in (mode, source_anchor, entry_id)):
                _fail(code, f"{line_id} cannot declare structural closure")
            continue
        if mode == "converges_to_main":
            if source_anchor is not None or entry_id is not None:
                _fail(code, f"{line_id} convergence carries terminal fields")
            continue
        if mode != "terminal_consequence":
            _fail(code, f"{line_id} has an invalid closure mode")
        if (
            not isinstance(source_anchor, Mapping)
            or set(source_anchor) != {"storyline_id", "state_index", "state"}
            or not isinstance(entry_id, str)
            or not re.fullmatch(r"SLC-[A-Za-z0-9._-]+", entry_id)
        ):
            _fail(code, f"{line_id} lacks an exact terminal entry declaration")
        source_line = lines.get(source_anchor.get("storyline_id"))
        state_index = source_anchor.get("state_index")
        if (
            source_line is None
            or source_line is line
            or source_line.get("type") == "optional_melody"
            or source_line.get("closure_mode") == "terminal_consequence"
            or not isinstance(state_index, int)
            or state_index < 0
        ):
            _fail(code, f"{line_id} terminal source is outside the structural trunk")
        states = [
            source_line.get("start_state"),
            *source_line.get("state_changes", []),
            source_line.get("end_state"),
        ]
        if state_index >= len(states) or states[state_index] != source_anchor.get("state"):
            _fail(code, f"{line_id} terminal source anchor is stale")
        entry_owners = {
            owner_id
            for owner_id, owner in lines.items()
            if entry_id in set(owner.get("connection_ids", []))
        }
        if entry_owners != {line_id, source_anchor["storyline_id"]}:
            _fail(code, f"{line_id} terminal entry is not shared by its owner lines")
        terminal_lines[str(line_id)] = line

    if connections is None:
        return
    connection_by_id = {item.get("id"): item for item in connections}
    for line_id, line in terminal_lines.items():
        entry_id = line["terminal_entry_connection_id"]
        entry = connection_by_id.get(entry_id)
        source_anchor = line["terminal_source_anchor"]
        if entry is None or any(
            entry.get(field) != expected
            for field, expected in (
                ("relation", "causal"),
                ("from_storyline_id", source_anchor["storyline_id"]),
                ("from_state_index", source_anchor["state_index"]),
                ("from_state", source_anchor["state"]),
                ("to_storyline_id", line_id),
            )
        ):
            _fail(code, f"{line_id} terminal entry connection is not exact and causal")
        if any(
            item.get("relation") == "causal"
            and item.get("from_storyline_id") == line_id
            for item in connections
        ):
            _fail("S1_TERMINAL_CAUSAL_OUTBOUND_FORBIDDEN", line_id)


def _validate_story_obligations(
    model: Mapping[str, Any],
    controls_by_id: Mapping[str, Mapping[str, Any]],
    lines: Mapping[str, Mapping[str, Any]],
    state_graph: StateCausalGraph | None = None,
    *,
    enforce_semantic_gate: bool = True,
    require_current_contract: bool = False,
) -> tuple[set[str], set[str], set[str], set[str]]:
    """Validate the source-complete, machine-consumable story obligations."""

    expected_units = _expected_claim_units(list(controls_by_id.values()))
    if model["story_claim_units"] != expected_units:
        _fail(
            "S1_STORY_CLAIM_UNIT_MISMATCH",
            "claim units do not equal deterministic B0 decomposition",
        )
    unit_by_id = {item["id"]: item for item in expected_units}
    if len(unit_by_id) != len(expected_units):
        _fail("S1_STORY_CLAIM_UNIT_DUPLICATE", "claim unit IDs must be unique")

    obligations = model["story_obligation_register"]
    obligation_by_id = {item["id"]: item for item in obligations}
    if len(obligation_by_id) != len(obligations):
        _fail("S1_STORY_OBLIGATION_DUPLICATE", "obligation IDs must be unique")
    atoms = model["story_claim_atoms"]
    atom_by_id = {item["id"]: item for item in atoms}
    atom_by_unit = {item["source_unit_id"]: item for item in atoms}
    if (
        len(atom_by_id) != len(atoms)
        or len(atom_by_unit) != len(atoms)
        or set(atom_by_unit) != set(unit_by_id)
    ):
        _fail(
            "S1_STORY_CLAIM_ATOM_COVERAGE_MISMATCH",
            "every deterministic source unit needs exactly one claim atom",
        )

    atoms_by_control: dict[str, set[str]] = {
        control_id: set() for control_id in controls_by_id
    }
    atoms_by_obligation: dict[str, set[str]] = {
        obligation_id: set() for obligation_id in obligation_by_id
    }
    required_obligation_owner: dict[str, str] = {}
    reviewed_non_relational_units = {
        item.get("source_unit_id")
        for item in model.get("source_sequence_realizations", [])
        if isinstance(item, Mapping)
        and item.get("realization_scope") == "non_relational_candidate"
    }
    for atom in atoms:
        atom_id = atom["id"]
        unit = unit_by_id[atom["source_unit_id"]]
        control_id = atom["control_id"]
        control = controls_by_id.get(control_id)
        if (
            control is None
            or unit["control_id"] != control_id
            or atom["source_locator"] != unit["source_locator"]
        ):
            _fail("S1_STORY_CLAIM_ATOM_SOURCE_MISMATCH", atom_id)
        atoms_by_control[control_id].add(atom_id)
        obligation_ids = set(atom["obligation_ids"])
        if not obligation_ids.issubset(obligation_by_id):
            _fail("S1_STORY_CLAIM_ATOM_OBLIGATION_DANGLING", atom_id)
        for obligation_id in obligation_ids:
            atoms_by_obligation[obligation_id].add(atom_id)
        atom_kind = atom["atom_kind"]
        consistency_dimensions = atom.get("consistency_dimensions")
        if require_current_contract and not isinstance(consistency_dimensions, list):
            _fail("S1_CONSISTENCY_SOURCE_SHAPE_INVALID", atom_id)
        if atom_kind == "consistency_constraint":
            if (
                not isinstance(consistency_dimensions, list)
                or not consistency_dimensions
                or len(consistency_dimensions) != len(set(consistency_dimensions))
                or not set(consistency_dimensions).issubset(CONSISTENCY_DIMENSIONS)
                or obligation_ids
                or atom["review_required"] is not True
            ):
                _fail("S1_CONSISTENCY_SOURCE_SHAPE_INVALID", atom_id)
        elif consistency_dimensions not in (None, []):
            _fail("S1_CONSISTENCY_SOURCE_SHAPE_INVALID", atom_id)
        co_group = atom.get("co_realization_group")
        co_reason = atom.get("co_realization_justification")
        co_witnesses = atom.get("co_realization_witness_ids")
        co_fields_present = any(
            field in atom
            for field in (
                "co_realization_group",
                "co_realization_justification",
                "co_realization_witness_ids",
            )
        )
        if co_fields_present and (
            not isinstance(co_group, str)
            or not co_group.strip()
            or not isinstance(co_reason, str)
            or not co_reason.strip()
            or not isinstance(co_witnesses, list)
            or not co_witnesses
            or len(co_witnesses) != len(set(co_witnesses))
        ):
            _fail("S1_CO_REALIZATION_INVALID", atom_id)
        if co_fields_present and _source_unit_is_ordered(unit):
            _fail(
                "S1_CO_REALIZATION_ORDERED_SOURCE_INVALID",
                f"{atom_id}: an ordered source claim may not be co-realized",
            )
        if control["hardness"] == "author_open":
            if atom_kind != "author_open" or obligation_ids or atom["review_required"]:
                _fail("S1_STORY_OBLIGATION_AUTHORITY_VIOLATION", atom_id)
            continue
        if atom_kind == "author_open":
            _fail("S1_STORY_OBLIGATION_AUTHORITY_VIOLATION", atom_id)
        if atom_kind == "consistency_constraint":
            if any(
                _contains_placeholder(atom[field])
                for field in ("claim", "rationale")
            ):
                _fail("S1_STORY_OBLIGATION_PLACEHOLDER", atom_id)
            continue
        if unit["relation_mode"] == "required" and atom_kind == "non_relational":
            _fail("S1_REQUIRED_RELATION_UNDISPOSED", atom_id)
        if atom_kind == "non_relational":
            expected_atom_review = (
                unit["relation_mode"] == "candidate"
                and unit["id"] not in reviewed_non_relational_units
            )
            if obligation_ids or atom["review_required"] != expected_atom_review:
                _fail("S1_STORY_CLAIM_ATOM_DISPOSITION_INVALID", atom_id)
        else:
            if not obligation_ids or atom["review_required"]:
                _fail("S1_STORY_CLAIM_ATOM_DISPOSITION_INVALID", atom_id)
            kinds = {obligation_by_id[item]["kind"] for item in obligation_ids}
            valid_kinds = {
                "causal_relation": {"causes"},
                "temporal_relation": {"strict_before", "not_before"},
                "all_prerequisites": {"requires_all"},
                "information_window": {
                    "first_disclosure", "must_remain_unknown"
                },
            }[atom_kind]
            if not kinds.issubset(valid_kinds):
                _fail("S1_STORY_CLAIM_ATOM_KIND_MISMATCH", atom_id)
            if atom_kind in {"all_prerequisites"} and len(obligation_ids) != 1:
                _fail("S1_STORY_CLAIM_ATOM_KIND_MISMATCH", atom_id)
            if atom_kind == "information_window":
                if kinds != valid_kinds or len(obligation_ids) != 2:
                    _fail("S1_INFORMATION_WINDOW_INCOMPLETE", atom_id)
                info = [obligation_by_id[item] for item in obligation_ids]
                if len({(item["proposition_id"], item["audience"]) for item in info}) != 1:
                    _fail("S1_INFORMATION_WINDOW_INCOMPLETE", atom_id)
            if unit["relation_mode"] == "required":
                if len(obligation_ids) != 1:
                    _fail("S1_REQUIRED_RELATION_NOT_ATOMIC", atom_id)
                obligation_id = next(iter(obligation_ids))
                previous = required_obligation_owner.get(obligation_id)
                if previous is not None:
                    _fail("S1_REQUIRED_RELATION_NOT_ATOMIC", obligation_id)
                required_obligation_owner[obligation_id] = atom_id
        if any(
            _contains_placeholder(atom[field])
            for field in ("claim", "rationale")
        ):
            _fail("S1_STORY_OBLIGATION_PLACEHOLDER", atom_id)

    coverage = model["story_obligation_coverage"]
    coverage_by_control = {item["control_id"]: item for item in coverage}
    coverage_ids = [item["id"] for item in coverage]
    if (
        len(coverage_by_control) != len(coverage)
        or len(coverage_ids) != len(set(coverage_ids))
        or set(coverage_by_control) != set(controls_by_id)
    ):
        _fail(
            "S1_STORY_OBLIGATION_COVERAGE_MISMATCH",
            "every B0 control must have exactly one obligation disposition",
        )

    for control_id, record in coverage_by_control.items():
        control = controls_by_id[control_id]
        if record["source_locator"] != control["source_locator"]:
            _fail("S1_STORY_OBLIGATION_SOURCE_STALE", control_id)
        hardness = control["hardness"]
        disposition = record["disposition"]
        claim_atom_ids = set(record["claim_atom_ids"])
        if claim_atom_ids != atoms_by_control[control_id]:
            _fail("S1_STORY_OBLIGATION_COVERAGE_MISMATCH", control_id)
        control_atoms = [atom_by_id[item] for item in claim_atom_ids]
        obligation_ids = {
            obligation_id
            for atom in control_atoms
            for obligation_id in atom["obligation_ids"]
        }
        if set(record["obligation_ids"]) != obligation_ids:
            _fail("S1_STORY_OBLIGATION_COVERAGE_MISMATCH", control_id)
        has_relational = any(
            item["atom_kind"] not in {
                "non_relational", "consistency_constraint", "author_open"
            }
            for item in control_atoms
        )
        has_non_relational = any(
            item["atom_kind"] in {"non_relational", "consistency_constraint"}
            for item in control_atoms
        )
        expected_disposition = (
            "author_open"
            if hardness == "author_open"
            else "mixed"
            if has_relational and has_non_relational
            else "obligated"
            if has_relational
            else "no_relational_obligation"
        )
        expected_review = (
            expected_disposition in {"no_relational_obligation", "mixed"}
            and any(item["review_required"] for item in control_atoms)
        )
        if (
            disposition != expected_disposition
            or record["review_required"] != expected_review
        ):
            _fail("S1_STORY_OBLIGATION_COVERAGE_MISMATCH", control_id)
        if (
            _contains_placeholder(record["rationale"])
            or not " ".join(record["rationale"].split())
        ):
            _fail("S1_STORY_OBLIGATION_PLACEHOLDER", record["id"])

    state_by_anchor: dict[tuple[str, int], str] = {}
    for line_id, line in lines.items():
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        state_by_anchor.update(
            {(line_id, index): state for index, state in enumerate(states)}
        )

    graph_edges: list[tuple[tuple[str, int], tuple[str, int], bool]] = []
    first_disclosures: set[tuple[str, str]] = set()
    disclosure_anchors: dict[tuple[str, str], tuple[str, int]] = {}
    unknown_anchors: list[tuple[str, str, tuple[str, int], str]] = []
    causal_reachability_requirements: list[
        tuple[tuple[str, int], tuple[str, int], str]
    ] = []
    obligation_signatures: dict[str, tuple[Any, ...]] = {}
    for obligation_id, obligation in obligation_by_id.items():
        source_atom_ids = set(obligation["source_claim_atom_ids"])
        if source_atom_ids != atoms_by_obligation[obligation_id] or not source_atom_ids:
            _fail("S1_STORY_OBLIGATION_COVERAGE_MISMATCH", obligation_id)
        source_ids = {atom_by_id[item]["control_id"] for item in source_atom_ids}
        if source_ids != set(obligation["source_control_ids"]):
            _fail("S1_STORY_OBLIGATION_SOURCE_MISMATCH", obligation_id)
        if any(
            controls_by_id.get(control_id, {}).get("hardness") != "author_locked"
            for control_id in source_ids
        ):
            _fail("S1_STORY_OBLIGATION_AUTHORITY_VIOLATION", obligation_id)
        locators = {
            locator["control_id"]: locator
            for locator in obligation["source_locators"]
        }
        if len(locators) != len(obligation["source_locators"]) or set(locators) != source_ids:
            _fail("S1_STORY_OBLIGATION_SOURCE_MISMATCH", obligation_id)
        for control_id, locator in locators.items():
            if locator != controls_by_id[control_id]["source_locator"]:
                _fail("S1_STORY_OBLIGATION_SOURCE_STALE", obligation_id)
        if any(
            _contains_placeholder(obligation[field])
            for field in ("rationale", "acceptance_check")
        ):
            _fail("S1_STORY_OBLIGATION_PLACEHOLDER", obligation_id)

        def anchor_key(anchor: Mapping[str, Any]) -> tuple[str, int]:
            key = (anchor["storyline_id"], anchor["state_index"])
            if state_by_anchor.get(key) != anchor["state"]:
                _fail("S1_STORY_OBLIGATION_ANCHOR_INVALID", obligation_id)
            return key

        antecedents = [anchor_key(item) for item in obligation["antecedent_anchors"]]
        consequent = anchor_key(obligation["consequent_anchor"])
        if consequent in antecedents:
            _fail("S1_STORY_OBLIGATION_SELF_EDGE", obligation_id)
        kind = obligation["kind"]
        for antecedent in antecedents:
            if antecedent[0] == consequent[0] and antecedent[1] >= consequent[1]:
                _fail("S1_STORY_OBLIGATION_LINE_ORDER_INVALID", obligation_id)
            graph_edges.append(
                (antecedent, consequent, kind != "not_before")
            )
            if kind in {"causes", "requires_all"}:
                causal_reachability_requirements.append(
                    (antecedent, consequent, obligation_id)
                )

        proposition_id = obligation["proposition_id"]
        audience = obligation["audience"]
        obligation_signatures[obligation_id] = (
            kind,
            tuple(sorted(antecedents)),
            consequent,
            proposition_id,
            audience,
        )
        if kind == "first_disclosure":
            disclosure_key = (proposition_id, audience)
            if disclosure_key in first_disclosures:
                _fail("S1_FIRST_DISCLOSURE_DUPLICATE", obligation_id)
            first_disclosures.add(disclosure_key)
            disclosure_anchors[disclosure_key] = consequent
        elif kind == "must_remain_unknown":
            unknown_anchors.append((proposition_id, audience, consequent, obligation_id))

    # Separate author-locked causal/temporal claims may not be compressed into
    # one indistinguishable realization. Information-window claims are exempt:
    # several narrative controls may legitimately protect the same proposition.
    realization_owner: dict[tuple[tuple[Any, ...], ...], Mapping[str, Any]] = {}
    for atom in atoms:
        if atom["atom_kind"] not in {
            "causal_relation",
            "temporal_relation",
            "all_prerequisites",
        }:
            continue
        signature = tuple(
            sorted(
                (obligation_signatures[item] for item in atom["obligation_ids"]),
                key=repr,
            )
        )
        previous = realization_owner.get(signature)
        if previous is not None and previous["id"] != atom["id"] and enforce_semantic_gate:
            groups = {previous.get("co_realization_group"), atom.get("co_realization_group")}
            previous_unit = unit_by_id[previous["source_unit_id"]]
            justified = (
                len(groups) == 1
                and None not in groups
                and not _source_unit_is_ordered(unit)
                and not _source_unit_is_ordered(previous_unit)
                and all(
                    isinstance(item.get("co_realization_justification"), str)
                    and item["co_realization_justification"].strip()
                    and isinstance(item.get("co_realization_witness_ids"), list)
                    and item["co_realization_witness_ids"]
                    for item in (previous, atom)
                )
            )
            if not justified:
                _fail(
                    "S1_RELATION_REALIZATION_COLLISION",
                    f"{previous['id']} and {atom['id']} share one realization",
                )
        realization_owner[signature] = atom

    # `not_before` is non-strict. A cycle made only of non-strict edges means
    # simultaneity and is valid; any closed path containing a strict edge is a
    # contradiction. Compute transitive reachability while carrying that bit.
    reach: dict[tuple[tuple[str, int], tuple[str, int]], bool] = {}
    for source, target, strict in graph_edges:
        reach[(source, target)] = reach.get((source, target), False) or strict
    nodes = list(state_by_anchor)
    for pivot in nodes:
        for source in nodes:
            left = reach.get((source, pivot))
            if left is None:
                continue
            for target in nodes:
                right = reach.get((pivot, target))
                if right is None:
                    continue
                strict = left or right
                key = (source, target)
                if key not in reach or strict:
                    reach[key] = strict
    for node in nodes:
        if reach.get((node, node), False):
            _fail("S1_STORY_OBLIGATION_CYCLE", f"strict cycle at {node}")

    for proposition_id, audience, unknown_until, obligation_id in unknown_anchors:
        disclosure = disclosure_anchors.get((proposition_id, audience))
        if (
            disclosure is not None
            and disclosure[0] == unknown_until[0]
            and unknown_until[1] > disclosure[1]
        ):
            _fail("S1_INFORMATION_WINDOW_INVALID", obligation_id)

    # Causal obligations must be implementable by the actual state topology,
    # not merely by a separate obligation DAG. Reuse the same canonical graph
    # as cycle detection and structural-to-main closure.
    if state_graph is None:
        state_graph = _build_state_causal_graph(lines, model["connections"])
        _validate_state_causal_dag(state_graph)

    for source, target, obligation_id in causal_reachability_requirements:
        if not _state_reachable(state_graph, source, target):
            _fail(
                "S1_CAUSAL_OBLIGATION_UNREACHABLE",
                f"{obligation_id}: {source} cannot causally reach {target}",
            )
    return (
        set(unit_by_id),
        set(atom_by_id),
        set(obligation_by_id),
        set(coverage_ids),
    )


def _validate_causal_target_first_registration(
    connections: Mapping[str, Mapping[str, Any]],
    milestones: Mapping[str, Mapping[str, Any]],
) -> None:
    first_target_order: dict[tuple[str, int], int] = {}
    realized_at: dict[str, list[int]] = {}
    for milestone in milestones.values():
        order = milestone.get("order")
        if not isinstance(order, int):
            continue
        for ref in milestone.get("state_refs", []):
            if not isinstance(ref, Mapping):
                continue
            key = (ref.get("storyline_id"), ref.get("state_index"))
            first_target_order[key] = min(
                order, first_target_order.get(key, order)
            )
        for connection_id in milestone.get("connection_ids", []):
            realized_at.setdefault(str(connection_id), []).append(order)
    for connection_id, connection in connections.items():
        if connection.get("relation") != "causal":
            continue
        target_order = first_target_order.get(
            (connection.get("to_storyline_id"), connection.get("to_state_index"))
        )
        if realized_at.get(connection_id) != [target_order]:
            _fail(
                "S1_CAUSAL_TARGET_FIRST_OCCURRENCE_MISMATCH",
                (
                    f"{connection_id}: realized milestones "
                    f"{realized_at.get(connection_id, [])} != target first {target_order}"
                ),
            )


def _validate_global_temporal_semantics(
    model: Mapping[str, Any],
    *,
    connections: Mapping[str, Mapping[str, Any]],
    milestones: Mapping[str, Mapping[str, Any]],
    line_state_visits: Mapping[str, Sequence[tuple[int, int]]],
    require_current_contract: bool = False,
) -> None:
    """Validate relation order against the globally scheduled first occurrence.

    A state may remain present across several milestones.  Its temporal rank is
    therefore the earliest milestone at which it appears, not the milestone
    chosen to display a connection.  This closes the loophole where a later
    cause could be attached to a target state that already existed earlier.
    """

    del line_state_visits  # Milestone ref order supplies the within-milestone rank.
    if require_current_contract:
        _validate_causal_target_first_registration(connections, milestones)
    first_rank: dict[tuple[str, int], tuple[int, int]] = {}
    for milestone in sorted(milestones.values(), key=lambda item: item["order"]):
        for within_order, state_ref in enumerate(milestone["state_refs"], 1):
            key = (state_ref["storyline_id"], state_ref["state_index"])
            value = (milestone["order"], within_order)
            first_rank[key] = min(value, first_rank.get(key, value))

    def rank(anchor: Mapping[str, Any], owner: str) -> tuple[int, int]:
        key = (anchor["storyline_id"], anchor["state_index"])
        value = first_rank.get(key)
        if value is None:
            _fail(
                "S1_GLOBAL_TEMPORAL_ANCHOR_UNSCHEDULED",
                f"{owner}: {key} has no milestone",
            )
        return value

    for connection_id, connection in connections.items():
        if connection["relation"] != "causal":
            continue
        source = first_rank.get(
            (connection["from_storyline_id"], connection["from_state_index"])
        )
        target = first_rank.get(
            (connection["to_storyline_id"], connection["to_state_index"])
        )
        if source is None or target is None:
            _fail("S1_GLOBAL_TEMPORAL_ANCHOR_UNSCHEDULED", connection_id)
        if source > target:
            _fail(
                "S1_CAUSAL_FIRST_OCCURRENCE_REVERSED",
                f"{connection_id}: source rank {source} > target rank {target}",
            )

    disclosure_rank: dict[tuple[str, str], tuple[int, int]] = {}
    unknown_rank: list[tuple[tuple[str, str], tuple[int, int], str]] = []
    for obligation in model["story_obligation_register"]:
        obligation_id = obligation["id"]
        consequent_rank = rank(obligation["consequent_anchor"], obligation_id)
        antecedent_ranks = [
            rank(item, obligation_id) for item in obligation["antecedent_anchors"]
        ]
        kind = obligation["kind"]
        if kind == "strict_before" and any(
            item >= consequent_rank for item in antecedent_ranks
        ):
            _fail("S1_GLOBAL_STRICT_ORDER_INVALID", obligation_id)
        if kind in {"causes", "requires_all", "not_before", "first_disclosure"} and any(
            item > consequent_rank for item in antecedent_ranks
        ):
            _fail("S1_GLOBAL_RELATION_ORDER_INVALID", obligation_id)
        if kind == "first_disclosure":
            disclosure_rank[(obligation["proposition_id"], obligation["audience"])] = (
                consequent_rank
            )
        elif kind == "must_remain_unknown":
            unknown_rank.append(
                (
                    (obligation["proposition_id"], obligation["audience"]),
                    consequent_rank,
                    obligation_id,
                )
            )

    for key, until_rank, obligation_id in unknown_rank:
        revealed_at = disclosure_rank.get(key)
        if revealed_at is not None and revealed_at < until_rank:
            _fail(
                "S1_GLOBAL_INFORMATION_WINDOW_INVALID",
                f"{obligation_id}: disclosure rank {revealed_at} < unknown rank {until_rank}",
            )


def _validate_milestone_line_state_progression(
    line_state_visits: Mapping[str, Sequence[tuple[int, int]]],
) -> None:
    """Require each line's milestone state indexes to remain monotonic."""

    for line_id, visits in line_state_visits.items():
        if not visits:
            _fail("S1_MILESTONE_LINE_COVERAGE_MISSING", line_id)
        ordered_indexes = [state_index for _, state_index in sorted(visits)]
        if ordered_indexes != sorted(ordered_indexes):
            _fail("S1_MILESTONE_LINE_STATE_REGRESSION", line_id)


def _semantic_consistency_witness_allowances(
    model: Mapping[str, Any],
) -> dict[str, set[str]]:
    """Return only phase-2-declared atom/control witnesses for each dimension."""

    allowances = {dimension: set() for dimension in CONSISTENCY_DIMENSIONS}
    units_by_id = {
        item["id"]: item for item in model.get("story_claim_units", [])
    }
    atoms_by_unit: dict[str, list[Mapping[str, Any]]] = {}
    for atom in model.get("story_claim_atoms", []):
        atoms_by_unit.setdefault(atom["source_unit_id"], []).append(atom)
    for realization in model.get("source_sequence_realizations", []):
        if (
            realization.get("realization_scope") != "semantic_constraint"
            or realization.get("phase3_fulfillment_kind") != "consistency"
        ):
            continue
        dimension = realization.get("consistency_dimension")
        unit = units_by_id.get(realization.get("source_unit_id"))
        if dimension not in allowances or unit is None:
            continue
        for atom in atoms_by_unit.get(unit["id"], []):
            if atom.get("control_id") == unit.get("control_id"):
                allowances[dimension].update({atom["id"], unit["control_id"]})
    return allowances


def _validate_consistency_witness_subset(
    dimension: str, witnesses: set[str], allowed: set[str]
) -> None:
    """Reject consistency witnesses outside the dimension-scoped allow-list."""

    invalid = sorted(witnesses - allowed)
    if invalid:
        _fail(
            "S1_CONSISTENCY_WITNESS_INVALID",
            f"{dimension}: {invalid}",
        )


def _validate_model(
    model: Mapping[str, Any],
    baseline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
    *,
    expected_gate: Mapping[str, str] | None = None,
    expected_sources: Sequence[Mapping[str, str]] | None = None,
    enforce_semantic_gate: bool = True,
    require_source_sequences: bool = True,
    require_current_contract: bool = False,
    upstream_only: bool = False,
) -> None:
    partition: Mapping[str, Any] | None = None
    if not upstream_only:
        _validate_agent_text(model, path="$.model")
        try:
            runtime.validate(model, "storyline-architecture.schema.json")
        except Exception as error:
            _fail("S1_MODEL_SCHEMA_INVALID", str(error))
        partition = model["authority_partition"]
        _validate_authority_disjoint(partition)
    demands = model["storyline_demands"]
    controls_by_id = {x["id"]: x for x in controls}
    baseline_controls = {x["id"] for x in baseline["control_registry"]}
    if set(controls_by_id) != baseline_controls:
        _fail("S1_B0_CONTROL_MISMATCH", "source controls differ from B0 registry")
    if {x["source_ids"][0] for x in demands} != baseline_controls or any(len(x["source_ids"]) != 1 for x in demands):
        _fail("S1_DEMAND_COVERAGE_MISMATCH", "controls and storyline demands are not one-to-one")
    demand_by_control = {item["source_ids"][0]: item for item in demands}
    if len(demand_by_control) != len(demands):
        _fail("S1_DEMAND_COVERAGE_MISMATCH", "a control has duplicate demands")
    for control_id, control in controls_by_id.items():
        obligation = demand_by_control[control_id]["obligation"]
        if (
            control["heading"] not in obligation
            or _control_text(control["value"]) not in obligation
        ):
            _fail(
                "S1_CONTROL_MEANING_UNBOUND",
                f"{control_id} title/value is not carried verbatim by its demand",
            )
    _validate_line_phase_semantics(
        model,
        model,
        controls,
        require_source_sequences=require_source_sequences,
        require_current_contract=require_current_contract,
    )
    demand_ids = {x["id"] for x in demands}
    if not upstream_only:
        covered = [x["source_ids"][0] for x in model["coverage_ledger"]]
        if set(covered) != demand_ids or len(covered) != len(set(covered)):
            _fail(
                "S1_DEMAND_COVERAGE_MISMATCH",
                "demands are not covered exactly once",
            )
    lines = {x["id"]: x for x in model["storylines"]}
    if len(lines) != len(model["storylines"]):
        _fail("S1_LINE_DUPLICATE", "storyline IDs must be unique")
    line_claim_ids = _validate_line_claim_authority(
        model,
        controls,
        final_model=None if upstream_only else model,
    )
    source_sequence_ids = _validate_source_sequence_realizations(
        model, controls, required=require_source_sequences
    )
    mains = [x for x in lines.values() if x["type"] == "main"]
    if len(mains) != 1:
        _fail("S1_MAIN_TRUNK_INVALID", "exactly one main storyline is required")
    if require_source_sequences:
        _validate_source_sequence_structural_closure(
            model,
            require_closure_declarations=require_current_contract,
        )
    connections = {x["id"]: x for x in model["connections"]}
    if len(connections) != len(model["connections"]):
        _fail("S1_CONNECTION_DUPLICATE", "connection IDs must be unique")
    if require_current_contract:
        _validate_physical_connection_uniqueness(model["connections"])
    for line in lines.values():
        if not line["start_state"] or not line["state_changes"] or not line["end_state"]:
            _fail("S1_LINE_INCOMPLETE", line["id"])
    structural_ids = {
        line_id
        for line_id, line in lines.items()
        if line["type"] != "optional_melody"
    }
    incident: dict[str, set[str]] = {line_id: set() for line_id in lines}
    for connection in connections.values():
        source_id = connection["from_storyline_id"]
        target_id = connection["to_storyline_id"]
        source = lines.get(source_id)
        target = lines.get(target_id)
        if source is None or target is None or source_id == target_id:
            _fail("S1_CONNECTION_DANGLING", connection["id"])
        source_states = [
            source["start_state"],
            *source["state_changes"],
            source["end_state"],
        ]
        target_states = [
            target["start_state"],
            *target["state_changes"],
            target["end_state"],
        ]
        if (
            connection["from_state_index"] >= len(source_states)
            or source_states[connection["from_state_index"]]
            != connection["from_state"]
            or connection["to_state_index"] >= len(target_states)
            or target_states[connection["to_state_index"]]
            != connection["to_state"]
        ):
            _fail("S1_CONNECTION_STATE_INVALID", connection["id"])
        incident[source_id].add(connection["id"])
        incident[target_id].add(connection["id"])
        if connection["relation"] == "causal":
            if source_id not in structural_ids or target_id not in structural_ids:
                _fail("S1_OPTIONAL_CAUSAL_LINK_FORBIDDEN", connection["id"])
    for line_id, line in lines.items():
        if set(line["connection_ids"]) != incident[line_id]:
            _fail("S1_CONNECTION_RECIPROCAL_MISMATCH", line_id)
        if line["type"] == "optional_melody":
            structural_associations = [
                connection
                for connection in connections.values()
                if connection["id"] in incident[line_id]
                and connection["relation"] == "associative"
                and (
                    connection["from_storyline_id"] in structural_ids
                    or connection["to_storyline_id"] in structural_ids
                )
            ]
            if not structural_associations:
                _fail("S1_OPTIONAL_ASSOCIATION_MISSING", line_id)
    _validate_reserved_source_sequence_connections(model, connections)
    _validate_semantic_constraint_fulfillment(model, model)
    _validate_line_closure_declarations(
        model,
        required=require_current_contract,
        connections=model["connections"],
    )
    line_order = model["architecture"]["line_order"]
    if set(line_order) != set(lines) or len(line_order) != len(lines):
        _fail(
            "S1_LINE_ORDER_INVALID",
            "line_order must contain every storyline exactly once",
        )
    state_graph = _build_state_causal_graph(lines, model["connections"])
    _validate_state_causal_dag(state_graph)
    _validate_structural_state_closure(lines, state_graph)

    (
        claim_unit_ids,
        claim_atom_ids,
        obligation_ids,
        obligation_coverage_ids,
    ) = _validate_story_obligations(
        model,
        controls_by_id,
        lines,
        state_graph,
        enforce_semantic_gate=enforce_semantic_gate,
        require_current_contract=require_current_contract,
    )
    obligation_ids_by_dimension = {
        "time": {
            item["id"]
            for item in model["story_obligation_register"]
            if item["kind"] in {
                "causes", "strict_before", "not_before", "requires_all"
            }
        },
        "causality": {
            item["id"]
            for item in model["story_obligation_register"]
            if item["kind"] in {"causes", "requires_all"}
        },
        "information": {
            item["id"]
            for item in model["story_obligation_register"]
            if item["kind"] in {"first_disclosure", "must_remain_unknown"}
        },
    }

    temporal = model["temporal_architecture"]
    phases = {item["id"]: item for item in temporal["phases"]}
    if len(phases) != len(temporal["phases"]):
        _fail("S1_TEMPORAL_PHASE_DUPLICATE", "phase IDs must be unique")
    phase_orders = [item["order"] for item in temporal["phases"]]
    if sorted(phase_orders) != list(range(1, len(phases) + 1)):
        _fail("S1_TEMPORAL_PHASE_ORDER_INVALID", str(phase_orders))
    if any(not set(item["active_storyline_ids"]).issubset(lines) for item in phases.values()):
        _fail("S1_TEMPORAL_PHASE_LINE_DANGLING", "unknown active storyline")

    milestones = {item["id"]: item for item in temporal["milestones"]}
    if len(milestones) != len(temporal["milestones"]):
        _fail("S1_MILESTONE_DUPLICATE", "milestone IDs must be unique")
    milestone_orders = [item["order"] for item in temporal["milestones"]]
    if sorted(milestone_orders) != list(range(1, len(milestones) + 1)):
        _fail("S1_MILESTONE_ORDER_INVALID", str(milestone_orders))
    milestone_phase_orders: list[int] = []
    phase_lines: dict[str, set[str]] = {phase_id: set() for phase_id in phases}
    line_state_visits: dict[str, list[tuple[int, int]]] = {
        line_id: [] for line_id in lines
    }
    realized_connections: list[str] = []
    for milestone in sorted(milestones.values(), key=lambda item: item["order"]):
        phase = phases.get(milestone["phase_id"])
        if phase is None:
            _fail("S1_MILESTONE_PHASE_DANGLING", milestone["id"])
        milestone_phase_orders.append(phase["order"])
        milestone_lines = set(milestone["storyline_ids"])
        if not milestone_lines or not milestone_lines.issubset(lines):
            _fail("S1_MILESTONE_LINE_DANGLING", milestone["id"])
        state_refs = milestone["state_refs"]
        ref_lines = [item["storyline_id"] for item in state_refs]
        if set(ref_lines) != milestone_lines or len(ref_lines) != len(set(ref_lines)):
            _fail("S1_MILESTONE_STATE_COVERAGE_MISMATCH", milestone["id"])
        for ref in state_refs:
            line_id = ref["storyline_id"]
            states = [
                lines[line_id]["start_state"],
                *lines[line_id]["state_changes"],
                lines[line_id]["end_state"],
            ]
            if ref["state_index"] >= len(states) or states[ref["state_index"]] != ref["state"]:
                _fail("S1_MILESTONE_STATE_INVALID", milestone["id"])
            line_state_visits[line_id].append(
                (milestone["order"], ref["state_index"])
            )
        phase_lines[milestone["phase_id"]].update(milestone_lines)
        ref_pairs = {
            (item["storyline_id"], item["state_index"])
            for item in state_refs
        }
        for connection_id in milestone["connection_ids"]:
            connection = connections.get(connection_id)
            if connection is None:
                _fail("S1_MILESTONE_CONNECTION_DANGLING", connection_id)
            expected_pairs = {
                (
                    connection["from_storyline_id"],
                    connection["from_state_index"],
                ),
                (
                    connection["to_storyline_id"],
                    connection["to_state_index"],
                ),
            }
            if not expected_pairs.issubset(ref_pairs):
                _fail("S1_MILESTONE_CONNECTION_STATE_MISMATCH", connection_id)
            realized_connections.append(connection_id)
    if milestone_phase_orders != sorted(milestone_phase_orders):
        _fail("S1_MILESTONE_PHASE_ORDER_INVALID", str(milestone_phase_orders))
    for phase_id, phase in phases.items():
        if phase_lines[phase_id] != set(phase["active_storyline_ids"]):
            _fail("S1_TEMPORAL_PHASE_COVERAGE_MISMATCH", phase_id)
    if set(realized_connections) != set(connections) or len(realized_connections) != len(set(realized_connections)):
        _fail(
            "S1_MILESTONE_CONNECTION_COVERAGE_MISMATCH",
            "every connection must be realized exactly once",
        )
    _validate_milestone_line_state_progression(line_state_visits)
    for line_id, visits in line_state_visits.items():
        ordered_indexes = [state_index for _, state_index in sorted(visits)]
        if lines[line_id]["type"] != "optional_melody":
            final_index = len(lines[line_id]["state_changes"]) + 1
            if 0 not in ordered_indexes or final_index not in ordered_indexes:
                _fail("S1_MILESTONE_LINE_BOUNDARY_MISSING", line_id)

    if enforce_semantic_gate:
        _validate_global_temporal_semantics(
            model,
            connections=connections,
            milestones=milestones,
            line_state_visits=line_state_visits,
            require_current_contract=require_current_contract,
        )

    markers = {item["id"]: item for item in temporal["markers"]}
    if len(markers) != len(temporal["markers"]):
        _fail("S1_NARRATIVE_MARKER_DUPLICATE", "marker IDs must be unique")
    required_marker_kinds = {
        "setup", "probe", "turning_point", "climax", "payoff"
    }
    marker_kinds = {item["kind"] for item in markers.values()}
    if not required_marker_kinds.issubset(marker_kinds):
        _fail(
            "S1_NARRATIVE_MARKER_KIND_MISSING",
            str(sorted(required_marker_kinds - marker_kinds)),
        )
    markers_by_milestone: dict[str, list[str]] = {
        milestone_id: [] for milestone_id in milestones
    }
    marked_lines: set[str] = set()
    for marker in markers.values():
        milestone = milestones.get(marker["milestone_id"])
        if milestone is None:
            _fail("S1_NARRATIVE_MARKER_MILESTONE_DANGLING", marker["id"])
        marker_lines = set(marker["storyline_ids"])
        if not marker_lines or not marker_lines.issubset(milestone["storyline_ids"]):
            _fail("S1_NARRATIVE_MARKER_LINE_MISMATCH", marker["id"])
        marked_lines.update(marker_lines)
        markers_by_milestone[milestone["id"]].append(marker["id"])
        references = marker["reference_marker_ids"]
        if marker["id"] in references or any(item not in markers for item in references):
            _fail("S1_NARRATIVE_MARKER_REFERENCE_INVALID", marker["id"])
        if any(
            milestones[markers[item]["milestone_id"]]["order"]
            > milestone["order"]
            for item in references
        ):
            _fail("S1_NARRATIVE_MARKER_REFERENCE_FORWARD", marker["id"])
        if marker["kind"] == "probe" and not marker["reader_question"]:
            _fail("S1_PROBE_QUESTION_MISSING", marker["id"])
        if marker["kind"] == "payoff":
            if not references or not any(markers[item]["kind"] == "setup" for item in references):
                _fail("S1_PAYOFF_SETUP_MISSING", marker["id"])
        if marker["kind"] == "climax" and len(
            marker_lines & structural_ids
        ) < 2:
            _fail("S1_CLIMAX_CONVERGENCE_MISSING", marker["id"])
    if any(not value for value in markers_by_milestone.values()):
        _fail("S1_MILESTONE_MARKER_MISSING", "every milestone needs a marker")
    if not structural_ids.issubset(marked_lines):
        _fail(
            "S1_NARRATIVE_MARKER_LINE_COVERAGE_MISSING",
            str(sorted(structural_ids - marked_lines)),
        )
    consistency = model["cross_line_consistency"]
    consistency_by_dimension: dict[str, Mapping[str, Any]] = {}
    consistency_ids: set[str] = set()
    for check in consistency:
        if check["id"] in consistency_ids:
            _fail("S1_CONSISTENCY_CHECK_DUPLICATE", check["id"])
        consistency_ids.add(check["id"])
        dimension = check["dimension"]
        if dimension in consistency_by_dimension:
            _fail("S1_CONSISTENCY_DIMENSION_DUPLICATE", dimension)
        consistency_by_dimension[dimension] = check
    if set(consistency_by_dimension) != set(CONSISTENCY_DIMENSIONS):
        _fail(
            "S1_CONSISTENCY_DIMENSIONS_MISMATCH",
            (
                f"expected={list(CONSISTENCY_DIMENSIONS)} "
                f"actual={sorted(consistency_by_dimension)}"
            ),
        )
    line_ids = set(lines)
    connection_ids = set(connections)
    causal_connection_ids = {
        connection_id
        for connection_id, connection in connections.items()
        if connection["relation"] == "causal"
    }
    decision_ids = {
        item["id"] for item in model["design_decisions"]
    }
    temporal_phase_ids = set(phases)
    milestone_ids = set(milestones)
    marker_ids = set(markers)
    consistency_allowed = {
        "time": line_ids | connection_ids | temporal_phase_ids | milestone_ids | obligation_ids,
        "causality": line_ids | causal_connection_ids | milestone_ids | obligation_ids,
        "information": line_ids | connection_ids | demand_ids | milestone_ids | marker_ids | obligation_ids,
        "authority": line_ids | decision_ids | demand_ids,
        "state": line_ids | connection_ids | milestone_ids,
        "theme": line_ids | connection_ids | demand_ids | decision_ids | marker_ids,
    }
    if not require_current_contract:
        for dimension, declared_ids in _semantic_consistency_witness_allowances(
            model
        ).items():
            consistency_allowed[dimension].update(declared_ids)
    consistency_source_atoms = [
        item
        for item in model["story_claim_atoms"]
        if item["atom_kind"] == "consistency_constraint"
    ]
    for dimension in CONSISTENCY_DIMENSIONS:
        check = consistency_by_dimension[dimension]
        if require_current_contract:
            source_atom_ids = check.get("source_claim_atom_ids")
            source_control_ids = check.get("source_control_ids")
            expected_atoms = {
                item["id"]
                for item in consistency_source_atoms
                if dimension in item["consistency_dimensions"]
            }
            expected_controls = {
                item["control_id"]
                for item in consistency_source_atoms
                if item["id"] in expected_atoms
            }
            if (
                not isinstance(source_atom_ids, list)
                or len(source_atom_ids) != len(set(source_atom_ids))
                or set(source_atom_ids) != expected_atoms
                or not isinstance(source_control_ids, list)
                or len(source_control_ids) != len(set(source_control_ids))
                or set(source_control_ids) != expected_controls
            ):
                _fail("S1_CONSISTENCY_SOURCE_COVERAGE_MISMATCH", dimension)
            source_atoms_by_id = {
                item["id"]: item for item in consistency_source_atoms
            }
            if any(
                not _value_participates(
                    source_atoms_by_id[atom_id]["claim"], check["claim"]
                )
                or not _value_participates(
                    source_atoms_by_id[atom_id]["claim"],
                    check["failure_condition"],
                )
                for atom_id in expected_atoms
            ):
                _fail("S1_CONSISTENCY_SOURCE_SEMANTICS_MISSING", dimension)
        witnesses = set(check["witness_ids"])
        if require_current_contract and witnesses & (
            claim_atom_ids | set(controls_by_id)
        ):
            _fail("S1_CONSISTENCY_SOURCE_IN_GENERIC_WITNESS", dimension)
        if not line_ids.issubset(witnesses):
            _fail(
                "S1_CONSISTENCY_LINE_COVERAGE_MISSING",
                dimension,
            )
        required_temporal_witnesses = {
            "time": temporal_phase_ids | milestone_ids | obligation_ids_by_dimension["time"],
            "causality": obligation_ids_by_dimension["causality"],
            "information": marker_ids | obligation_ids_by_dimension["information"],
            "state": milestone_ids,
            "theme": marker_ids,
        }.get(dimension, set())
        if not required_temporal_witnesses.issubset(witnesses):
            _fail(
                "S1_CONSISTENCY_TEMPORAL_COVERAGE_MISSING",
                dimension,
            )
        _validate_consistency_witness_subset(
            dimension, witnesses, consistency_allowed[dimension]
        )
        claim = " ".join(check["claim"].split())
        failure = " ".join(check["failure_condition"].split())
        if (
            _contains_placeholder(claim)
            or _contains_placeholder(failure)
        ):
            _fail("S1_CONSISTENCY_PLACEHOLDER", dimension)
        if claim == failure:
            _fail(
                "S1_CONSISTENCY_CLAIM_NOT_FALSIFIABLE",
                dimension,
            )
    if upstream_only:
        return
    assert partition is not None
    coverage_by_demand = {
        item["source_ids"][0]: item["realization_ids"]
        for item in model["coverage_ledger"]
    }
    demands_by_line: dict[str, list[str]] = {line_id: [] for line_id in lines}
    for demand in demands:
        realization_ids = coverage_by_demand.get(demand["id"], [])
        if len(realization_ids) != 1 or realization_ids[0] not in lines:
            _fail("S1_DEMAND_COVERAGE_MISMATCH", demand["id"])
        demands_by_line[realization_ids[0]].append(demand["id"])
    for line_id, demand_id_list in demands_by_line.items():
        relevant_controls = [
            controls_by_id[demand_by_control_id]
            for demand_id in demand_id_list
            for demand_by_control_id in next(
                item["source_ids"] for item in demands if item["id"] == demand_id
            )
        ]
        for control in relevant_controls:
            if not _value_participates(control["value"], lines[line_id]):
                _fail(
                    "S1_CONTROL_MEANING_UNBOUND",
                    f"{control['id']} value does not participate in {line_id}",
                )
    for line_id, demand_id_list in demands_by_line.items():
        if lines[line_id]["type"] != "optional_melody":
            continue
        if any(
            controls_by_id[next(
                item["source_ids"][0]
                for item in demands
                if item["id"] == demand_id
            )]["hardness"]
            == "author_open"
            for demand_id in demand_id_list
        ) and any(
            connection["relation"] == "causal"
            and connection["id"] in incident[line_id]
            for connection in connections.values()
        ):
            _fail("S1_AUTHOR_OPEN_OPTIONAL_CAUSAL", line_id)
    downstream_ids: set[str] = set()
    for field, stage in (
        ("world_requirements", "W1"),
        ("environment_requirements", "E1"),
        ("event_requirements", "T1"),
        ("character_requirements", "C1"),
    ):
        requirements = model[field]
        expected_line_ids = set(lines)
        observed_line_ids: list[str] = []
        observed_demand_ids: list[str] = []
        for requirement in requirements:
            if requirement["target_stage"] != stage:
                _fail("S1_REQUIREMENT_TARGET_MISMATCH", requirement["id"])
            source_ids = requirement["source_ids"]
            line_ids = [item for item in source_ids if item in lines]
            demand_refs = [item for item in source_ids if item in demand_ids]
            if len(line_ids) != 1:
                _fail("S1_REQUIREMENT_COVERAGE_MISMATCH", requirement["id"])
            line_id = line_ids[0]
            if source_ids != [line_id, *demands_by_line[line_id]]:
                _fail(
                    "S1_REQUIREMENT_COVERAGE_MISMATCH",
                    f"{requirement['id']} does not exactly bind its line demands",
                )
            observed_line_ids.append(line_id)
            observed_demand_ids.extend(demand_refs)
            for demand_id in demands_by_line[line_id]:
                control_id = next(
                    item["source_ids"][0] for item in demands if item["id"] == demand_id
                )
                if not _value_participates(
                    controls_by_id[control_id]["value"], requirement
                ):
                    _fail(
                        "S1_CONTROL_MEANING_UNBOUND",
                        f"{control_id} value does not participate in {requirement['id']}",
                    )
            downstream_ids.add(requirement["id"])
        if (
            set(observed_line_ids) != expected_line_ids
            or len(observed_line_ids) != len(set(observed_line_ids))
            or set(observed_demand_ids) != demand_ids
            or len(observed_demand_ids) != len(set(observed_demand_ids))
        ):
            _fail(
                "S1_REQUIREMENT_COVERAGE_MISMATCH",
                f"{field} must cover every line and demand exactly once",
            )
    locked = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    }
    author_open = {
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    }
    owned = {
        item["id"]
        for field in ("design_decisions", "storylines")
        for item in model[field]
    }
    owned.update(line_claim_ids)
    owned.update(source_sequence_ids)
    owned.update(phases)
    owned.update(milestones)
    owned.update(markers)
    owned.update(claim_unit_ids)
    owned.update(claim_atom_ids)
    owned.update(obligation_ids)
    owned.update(obligation_coverage_ids)
    expected_partition = {
        "author_locked": locked,
        "autonomous_owned": owned,
        "downstream_freedom": downstream_ids,
        "author_open": author_open,
    }
    for name, expected in expected_partition.items():
        if set(partition[name]) != expected:
            _fail(
                "S1_AUTHORITY_PARTITION_MISMATCH",
                f"{name} differs: expected={sorted(expected)} "
                f"actual={sorted(set(partition[name]))}",
            )
    for claim in model["derivation_claims"]:
        if len(claim["projection_ids"]) == 1 and claim["projection_ids"][0] in lines:
            expected = rt.canonical_sha256(lines[claim["projection_ids"][0]])
            if claim["value_sha256"] != expected:
                _fail("S1_DERIVATION_STALE", claim["id"])
        elif claim["id"] == "DRV-ARCHITECTURE" and claim["value_sha256"] != rt.canonical_sha256(model["architecture"]):
            _fail("S1_DERIVATION_STALE", claim["id"])
        elif claim["id"] == "DRV-TEMPORAL-ARCHITECTURE" and claim["value_sha256"] != rt.canonical_sha256(model["temporal_architecture"]):
            _fail("S1_DERIVATION_STALE", claim["id"])
        elif claim["id"] == "DRV-STORY-OBLIGATIONS" and claim["value_sha256"] != rt.canonical_sha256({
            "story_claim_units": model["story_claim_units"],
            "story_claim_atoms": model["story_claim_atoms"],
            "story_obligation_register": model["story_obligation_register"],
            "story_obligation_coverage": model["story_obligation_coverage"],
        }):
            _fail("S1_DERIVATION_STALE", claim["id"])
    obligation_derivations = [
        claim
        for claim in model["derivation_claims"]
        if claim["id"] == "DRV-STORY-OBLIGATIONS"
    ]
    if (
        len(obligation_derivations) != 1
        or set(obligation_derivations[0]["projection_ids"])
        != claim_unit_ids | claim_atom_ids | obligation_ids | obligation_coverage_ids
        or set(obligation_derivations[0]["source_ids"])
        != baseline_controls
    ):
        _fail(
            "S1_STORY_OBLIGATION_DERIVATION_MISSING",
            "register and source-complete coverage need one exact derivation",
        )
    expected_open = author_open
    actual_open = {source for item in model["open_items"] for source in item["source_ids"]}
    if expected_open != actual_open:
        _fail("S1_OPEN_ITEMS_MISMATCH", "author-open controls changed")
    if expected_gate is not None and model["input_gate"] != expected_gate:
        _fail("S1_GATE_REFERENCE_MISMATCH", "model does not bind the stored input gate")
    if expected_sources is not None and model["source_artifacts"] != list(expected_sources):
        _fail("S1_B0_SOURCE_MISMATCH", "model does not bind the exact B0 source set")


def _b0_reference(
    b0_root: Path,
    sealed_reference: Mapping[str, Any],
    *,
    baseline: Mapping[str, Any],
    runtime: Any,
) -> dict[str, str]:
    """Validate and return the B0 completion selected by the sealed S1 gate.

    The filesystem package is deliberately decoupled from its logical run path:
    production may place a rebuilt B0 below an immutable workspace rather than
    the legacy ``B0`` directory.  The coordinator gate owns that logical path;
    this function proves that it names the exact completion body in the supplied
    package before S1 creates any workspace artifacts.
    """

    completion_path = b0_root / "stage-completion.json"
    completion = _read(completion_path, "S1_B0_INVALID")
    reference = copy.deepcopy(dict(sealed_reference))
    try:
        runtime.validate(completion, "stage-completion.schema.json")
    except Exception as error:
        _fail("S1_B0_INVALID", str(error))
    if set(reference) != {"stage", "path", "sha256"}:
        _fail("S1_B0_INVALID", "sealed B0 reference has an invalid shape")
    path = reference.get("path")
    digest = reference.get("sha256")
    if (
        reference.get("stage") != "B0"
        or not isinstance(path, str)
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        _fail("S1_B0_INVALID", "sealed B0 reference identity is invalid")
    logical_path = PurePosixPath(path)
    if (
        "\\" in path
        or logical_path.is_absolute()
        or logical_path.as_posix() != path
        or any(part in {"", ".", ".."} for part in logical_path.parts)
        or logical_path.name != "stage-completion.json"
        or len(logical_path.parts) < 2
    ):
        _fail("S1_B0_INVALID", "sealed B0 completion path is not canonical")
    if (
        rt.sha256_file(completion_path) != digest
        or rt.canonical_sha256(completion) != digest
    ):
        _fail("S1_B0_INVALID", "sealed B0 completion body or hash differs")
    if (
        completion.get("stage") != "B0"
        or completion.get("status") != "ready"
        or completion.get("run_id") != baseline.get("run_id")
        or completion.get("previous_stage_completions") != []
    ):
        _fail("S1_B0_INVALID", "sealed completion is not this run's ready B0")
    logical_root = logical_path.parent
    expected_manifest = {
        "path": (logical_root / "package-manifest.json").as_posix(),
        "sha256": rt.sha256_file(b0_root / "package-manifest.json"),
    }
    expected_validation = {
        "path": (logical_root / "validation.json").as_posix(),
        "sha256": rt.sha256_file(b0_root / "validation.json"),
    }
    if (
        completion.get("manifest") != expected_manifest
        or completion.get("validation") != expected_validation
    ):
        _fail(
            "S1_B0_INVALID",
            "sealed B0 path is foreign to the completion's package lineage",
        )
    return reference


def _source_artifacts(b0_root: Path) -> list[dict[str, str]]:
    return [
        {
            "path": f"sources/B0/{name}",
            "sha256": rt.sha256_file(b0_root / name),
        }
        for name in (
            "author-control-baseline.json",
            "package-manifest.json",
            "stage-completion.json",
        )
    ]


def _control_bindings(controls: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "domain": item["domain"],
            "heading": item["heading"],
            "value_sha256": rt.canonical_sha256(item["value"]),
            "source_locator": copy.deepcopy(item["source_locator"]),
        }
        for item in controls
    ]


def _session_context(
    *,
    baseline_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[Path, dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    b0_root = Path(baseline_package).resolve()
    try:
        runtime.validate(input_gate.data, "input-gate.schema.json")
    except Exception as error:
        _fail("S1_GATE_INVALID", str(error))
    if rt.canonical_sha256(input_gate.data) != input_gate.reference.get("sha256"):
        _fail("S1_GATE_INVALID", "gate reference does not bind its body")
    if full_validation:
        try:
            rt.validate_baseline_package(b0_root, runtime=runtime)
        except Exception as error:
            _fail("S1_B0_INVALID", str(error))
    baseline = _read(
        b0_root / "author-control-baseline.json", "S1_B0_INVALID"
    )
    expected_b0 = _b0_reference(
        b0_root,
        input_gate.data.get("baseline_completion", {}),
        baseline=baseline,
        runtime=runtime,
    )
    if (
        input_gate.data.get("target_stage") != "S1"
        or input_gate.data.get("run_id") != baseline["run_id"]
        or input_gate.data.get("baseline_completion") != expected_b0
        or input_gate.data.get("upstream_completions") != []
    ):
        _fail("S1_GATE_INVALID", "gate is not the exact sealed S1/B0 gate")
    controls = _controls(b0_root, baseline)
    return b0_root, baseline, controls, expected_b0


def start_s1_session(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    input_gate: Any,
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze B0/gate/thread before any Agent-authored S1 phase is accepted."""

    root = Path(workspace).resolve()
    if root.exists():
        _fail("S1_SESSION_EXISTS", str(root))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("S1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    contract_runtime = runtime or rt.ContractRuntime()
    b0_root, baseline, controls, expected_b0 = _session_context(
        baseline_package=baseline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    session_id = f"S1-{rt.canonical_sha256([thread_id, input_gate.reference, expected_b0])[:20]}"
    session = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "S1",
        "session_id": session_id,
        "thread_id": thread_id,
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "input_manifest": expected_b0,
        "source_artifacts": _source_artifacts(b0_root),
        "control_bindings": _control_bindings(controls),
        "phases": list(PHASES),
        "line_review_protocol": LINE_REVIEW_PROTOCOL,
        "semantic_review_protocol": TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL,
        "contract_revision": CURRENT_CONTRACT_REVISION,
    }
    root.mkdir(parents=True)
    _write(root / "generation-session.json", session)
    return copy.deepcopy(session)


def _validated_session(
    workspace: Path,
    *,
    baseline_package: str | Path,
    input_gate: Any,
    runtime: Any,
    full_validation: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    session = _read(
        workspace / "generation-session.json", "S1_SESSION_INVALID"
    )
    b0_root, baseline, controls, expected_b0 = _session_context(
        baseline_package=baseline_package,
        input_gate=input_gate,
        runtime=runtime,
        full_validation=full_validation,
    )
    expected = {
        "schema_version": "2.0",
        "run_id": baseline["run_id"],
        "stage": "S1",
        "session_id": (
            "S1-"
            + rt.canonical_sha256(
                [
                    os.environ.get("CODEX_THREAD_ID", "").strip(),
                    input_gate.reference,
                    expected_b0,
                ]
            )[:20]
        ),
        "thread_id": os.environ.get("CODEX_THREAD_ID", "").strip(),
        "input_gate": copy.deepcopy(input_gate.reference),
        "state_before": copy.deepcopy(input_gate.data["run_state"]),
        "input_manifest": expected_b0,
        "source_artifacts": _source_artifacts(b0_root),
        "control_bindings": _control_bindings(controls),
        "phases": list(PHASES),
        "line_review_protocol": LINE_REVIEW_PROTOCOL,
        "semantic_review_protocol": TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL,
        "contract_revision": CURRENT_CONTRACT_REVISION,
    }
    if (
        not expected["thread_id"]
        or not isinstance(expected["session_id"], str)
        or not expected["session_id"]
        or session != expected
    ):
        _fail("S1_SESSION_INVALID", "session no longer binds B0/gate/thread")
    return session, baseline, controls


def _line_review_paths(root: Path, candidate_sha256: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[0-9a-f]{64}", candidate_sha256):
        _fail("S1_LINE_REVIEW_INVALID", "candidate hash is invalid")
    review_root = root / "line-claim-reviews" / candidate_sha256
    return review_root / "request.json", review_root / "review.json"


def _topology_review_paths(root: Path, candidate_sha256: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[0-9a-f]{64}", candidate_sha256):
        _fail("S1_TOPOLOGY_REVIEW_INVALID", "candidate hash is invalid")
    review_root = root / "topology-semantic-reviews" / candidate_sha256
    return review_root / "request.json", review_root / "review.json"


def _json_pointer_resolves(value: Any, pointer: str) -> bool:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return False
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                return False
            current = current[token]
        elif isinstance(current, Sequence) and not isinstance(
            current, (str, bytes, bytearray)
        ):
            if not token.isdigit() or int(token) >= len(current):
                return False
            current = current[int(token)]
        else:
            return False
    return True


def _collect_id_witnesses(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            result.add(identifier)
        for item in value.values():
            result.update(_collect_id_witnesses(item))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            result.update(_collect_id_witnesses(item))
    return result


def _topology_review_coverage(
    line_payload: Mapping[str, Any],
    body: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    include_current_extensions: bool = False,
) -> dict[str, Any]:
    """Build the deterministic exact-cover universe for semantic review."""

    units = body["story_claim_units"]
    atoms = body["story_claim_atoms"]
    milestones = body["temporal_architecture"]["milestones"]
    connections = body["connections"]
    ordered_unit_ids = [item["id"] for item in units if _source_unit_is_ordered(item)]
    information_atoms = [
        (index, item)
        for index, item in enumerate(atoms)
        if item["atom_kind"] == "information_window"
    ]
    information_control_ids = sorted({item["control_id"] for _, item in information_atoms})
    visibility_control_ids = sorted(
        {
            item["id"]
            for item in controls
            if item["hardness"] == "author_locked"
            and (item.get("domain") == "I5" or item["id"] in information_control_ids)
        }
    )
    milestone_pointers = [
        f"/topology/temporal_architecture/milestones/{index}"
        for index in range(len(milestones))
    ]
    milestone_state_pointers = [
        f"/topology/temporal_architecture/milestones/{index}/state_refs/{state_index}"
        for index, milestone in enumerate(milestones)
        for state_index in range(len(milestone["state_refs"]))
    ]
    connection_endpoint_pointers = [
        f"/topology/connections/{index}/{field}"
        for index in range(len(connections))
        for field in ("from_state_index", "to_state_index")
    ]
    information_atom_pointers = [
        f"/topology/story_claim_atoms/{index}" for index, _ in information_atoms
    ]
    consistency_atoms = [
        (index, item)
        for index, item in enumerate(atoms)
        if item["atom_kind"] == "consistency_constraint"
    ]
    reviewed_non_relational_unit_ids = [
        item["source_unit_id"]
        for item in line_payload.get("source_sequence_realizations", [])
        if item.get("realization_scope") == "non_relational_candidate"
    ]
    result = {
        "ordered_source_unit_ids": ordered_unit_ids,
        "milestone_ids": [item["id"] for item in milestones],
        "milestone_pointers": milestone_pointers,
        "milestone_state_pointers": milestone_state_pointers,
        "connection_endpoint_pointers": connection_endpoint_pointers,
        "connection_ids": [item["id"] for item in connections],
        "information_atom_ids": [item["id"] for _, item in information_atoms],
        "information_source_unit_ids": [
            item["source_unit_id"] for _, item in information_atoms
        ],
        "information_atom_pointers": information_atom_pointers,
        "visibility_control_ids": visibility_control_ids,
        "relational_visibility_control_ids": information_control_ids,
        "visibility_exemption_control_ids": sorted(
            set(visibility_control_ids) - set(information_control_ids)
        ),
    }
    if include_current_extensions:
        result.update(
            {
                "consistency_constraint_atom_ids": [
                    item["id"] for _, item in consistency_atoms
                ],
                "consistency_constraint_atom_pointers": [
                    f"/topology/story_claim_atoms/{index}"
                    for index, _ in consistency_atoms
                ],
                "consistency_constraint_dimensions": {
                    item["id"]: list(item.get("consistency_dimensions", []))
                    for _, item in consistency_atoms
                },
                "reviewed_non_relational_candidate_source_unit_ids": (
                    reviewed_non_relational_unit_ids
                ),
            }
        )
    return result


def _expected_topology_review_request(
    session: Mapping[str, Any],
    line_payload: Mapping[str, Any],
    body: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    candidate_sha256 = rt.canonical_sha256(body)
    source_unit_ids = [item["id"] for item in body["story_claim_units"]]
    bundle = {
        "line_design": copy.deepcopy(dict(line_payload)),
        "topology": copy.deepcopy(dict(body)),
    }
    current_contract = (
        session.get("contract_revision") == CURRENT_CONTRACT_REVISION
    )
    coverage_universe = _topology_review_coverage(
        line_payload,
        body,
        controls,
        include_current_extensions=current_contract,
    )
    request = {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "stage": "S1",
        "review_kind": "topology-and-information-semantics",
        "review_protocol": TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL,
        "session_id": session["session_id"],
        "generation_thread_id": session["thread_id"],
        "candidate_sha256": candidate_sha256,
        "line_design_sha256": rt.canonical_sha256(line_payload),
        "source_unit_ids": source_unit_ids,
        "dimension_ids": list(TOPOLOGY_SEMANTIC_REVIEW_DIMENSIONS),
        "candidate": bundle,
        "coverage_universe": coverage_universe,
        "control_context": [
            {
                "id": item["id"],
                "domain": item["domain"],
                "hardness": item["hardness"],
                "heading": item["heading"],
                "value": copy.deepcopy(item["value"]),
            }
            for item in controls
        ],
        "review_contract": {
            "pass_rule": (
                "Pass only when all six dimensions cite structural evidence "
                "from the frozen candidate and preserve author-locked meaning."
            ),
            "dimensions": list(TOPOLOGY_SEMANTIC_REVIEW_DIMENSIONS),
            "required_evidence": [
                "source_unit_ids",
                "candidate_pointers",
                "witness_ids",
                "source_order",
                "milestone_order",
                "visibility_result",
                "visibility_exemptions",
            ],
            "exact_cover_rule": (
                "Each dimension must exactly cover its deterministic pointer, "
                "source-order, milestone-order, and visibility universe; sampling "
                "or surplus evidence is invalid."
            ),
            "sequence_rule": (
                "Source order must map monotonically to milestone order; a fix "
                "must also reject the inverse overcorrection."
            ),
            "information_rule": (
                "Internal event order and audience disclosure order are separate; "
                "unknown and first-disclosure windows must remain intact."
            ),
        },
    }
    if current_contract:
        request["review_contract"].update(
            {
                "consistency_source_rule": (
                    "Review every consistency_constraint atom against the exact "
                    "dimension check whose claim and failure_condition each carry "
                    "that source claim; source atom/control provenance is separate "
                    "from generic witness IDs."
                ),
                "non_relational_candidate_rule": (
                    "Keep every independently reviewed non_relational_candidate "
                    "visible as a no-relation disposition; do not invent an "
                    "uncited antecedent merely to avoid a realization collision."
                ),
            }
        )
    return request


def _topology_verdicts_valid(
    request: Mapping[str, Any], verdicts: Sequence[Mapping[str, Any]]
) -> bool:
    verdict_list = list(verdicts)
    dimensions = list(TOPOLOGY_SEMANTIC_REVIEW_DIMENSIONS)
    if len(verdict_list) != len(dimensions):
        return False
    candidate = request["candidate"]
    source_units = set(request["source_unit_ids"])
    witnesses = _collect_id_witnesses(candidate)
    universe = request.get("coverage_universe")
    if not isinstance(universe, Mapping):
        return False
    expected_fields = {
        "dimension", "verdict", "source_unit_ids", "candidate_pointers",
        "witness_ids", "source_order", "milestone_order",
        "visibility_result", "visibility_exemptions", "rationale",
    }
    for index, item in enumerate(verdict_list):
        if not isinstance(item, Mapping) or set(item) != expected_fields:
            return False
        if (
            item.get("dimension") != dimensions[index]
            or item.get("verdict") not in {"pass", "fail"}
            or not isinstance(item.get("rationale"), str)
            or not item["rationale"].strip()
        ):
            return False
        source_ids = item.get("source_unit_ids")
        pointers = item.get("candidate_pointers")
        witness_ids = item.get("witness_ids")
        source_order = item.get("source_order")
        milestone_order = item.get("milestone_order")
        visibility = item.get("visibility_result")
        exemptions = item.get("visibility_exemptions")
        if (
            not isinstance(source_ids, list)
            or len(source_ids) != len(set(source_ids))
            or not set(source_ids).issubset(source_units)
            or not isinstance(pointers, list)
            or len(pointers) != len(set(pointers))
            or any(not _json_pointer_resolves(candidate, pointer) for pointer in pointers)
            or not isinstance(witness_ids, list)
            or len(witness_ids) != len(set(witness_ids))
            or not set(witness_ids).issubset(witnesses)
            or not isinstance(source_order, list)
            or len(source_order) != len(set(source_order))
            or not set(source_order).issubset(source_units)
            or not isinstance(milestone_order, list)
            or len(milestone_order) != len(set(milestone_order))
            or not set(milestone_order).issubset(witnesses)
            or visibility not in {"preserved", "violated", "not_applicable"}
            or not isinstance(exemptions, list)
        ):
            return False
        exemption_ids: list[str] = []
        for exemption in exemptions:
            if (
                not isinstance(exemption, Mapping)
                or set(exemption) != {"control_id", "justification", "witness_ids"}
                or not isinstance(exemption.get("control_id"), str)
                or not isinstance(exemption.get("justification"), str)
                or not exemption["justification"].strip()
                or not isinstance(exemption.get("witness_ids"), list)
                or not exemption["witness_ids"]
                or len(exemption["witness_ids"])
                != len(set(exemption["witness_ids"]))
                or not set(exemption["witness_ids"]).issubset(witnesses)
            ):
                return False
            exemption_ids.append(exemption["control_id"])
        if len(exemption_ids) != len(set(exemption_ids)):
            return False

        milestone_ids = universe["milestone_ids"]
        dimension = item["dimension"]
        expected_source_ids: list[str] = list(request["source_unit_ids"])
        expected_pointers: list[str]
        expected_source_order: list[str] = []
        expected_milestone_order: list[str] = []
        expected_exemptions: list[str] = []
        expected_witness_ids: list[str]
        if dimension == "time":
            expected_pointers = universe["milestone_pointers"]
            expected_milestone_order = milestone_ids
            expected_witness_ids = milestone_ids
        elif dimension == "causality":
            expected_pointers = universe["connection_endpoint_pointers"]
            expected_milestone_order = milestone_ids
            expected_witness_ids = universe["connection_ids"]
        elif dimension == "information":
            expected_source_ids = universe["information_source_unit_ids"]
            expected_pointers = universe["information_atom_pointers"]
            expected_exemptions = universe["visibility_exemption_control_ids"]
            expected_witness_ids = (
                universe["information_atom_ids"] or milestone_ids
            )
        elif dimension == "state":
            expected_pointers = universe["milestone_state_pointers"]
            expected_milestone_order = milestone_ids
            expected_witness_ids = milestone_ids
        elif dimension == "source-sequence":
            expected_source_ids = universe["ordered_source_unit_ids"]
            expected_pointers = universe["milestone_pointers"] if expected_source_ids else []
            expected_source_order = universe["ordered_source_unit_ids"]
            expected_milestone_order = milestone_ids if expected_source_ids else []
            expected_witness_ids = universe["ordered_source_unit_ids"]
        else:  # overcorrection
            expected_pointers = universe["milestone_pointers"]
            expected_source_order = universe["ordered_source_unit_ids"]
            expected_milestone_order = milestone_ids
            expected_witness_ids = [*milestone_ids, *universe["ordered_source_unit_ids"]]
        if (
            source_ids != expected_source_ids
            or pointers != expected_pointers
            or witness_ids != expected_witness_ids
            or source_order != expected_source_order
            or milestone_order != expected_milestone_order
            or exemption_ids != expected_exemptions
        ):
            return False
        if item["verdict"] == "pass":
            if visibility == "violated":
                return False
            if dimension == "information" and universe["visibility_control_ids"]:
                if visibility != "preserved":
                    return False
            elif dimension == "information" and visibility != "not_applicable":
                return False
    return True


def _expected_line_review_request(
    session: Mapping[str, Any],
    body: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if any(
        not isinstance(item, Mapping)
        or not {"id", "domain", "hardness", "heading", "value"}.issubset(item)
        for item in controls
    ):
        _fail(
            "S1_LINE_REVIEW_INVALID",
            "control context is incomplete for independent review",
        )
    claims = body["line_claim_authority"]
    candidate_sha256 = rt.canonical_sha256(body)
    request = {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "stage": "S1",
        "review_kind": "line-claim-authority",
        "session_id": session["session_id"],
        "generation_thread_id": session["thread_id"],
        "candidate_sha256": candidate_sha256,
        "claim_register_sha256": rt.canonical_sha256(claims),
        "claim_ids": [item["claim_id"] for item in claims],
        "control_context": [
            {
                "id": item["id"],
                "domain": item["domain"],
                "hardness": item["hardness"],
                "heading": item["heading"],
                "value": copy.deepcopy(item["value"]),
            }
            for item in controls
        ],
        "candidate": copy.deepcopy(dict(body)),
        "review_contract": {
            "pass_rule": (
                "Pass only when the claim disposition matches its meaning and "
                "the claim stays within its cited source, S1 structural authority, "
                "declared downstream handoff, or unresolved open item."
            ),
            "source_bound_rule": (
                "The span must be exactly the cited B0 heading or value and must "
                "not contain an additional assertion."
            ),
            "s1_boundary": (
                "S1 may define storyline responsibility, state progression, "
                "connections and narrative function; it may not settle world, "
                "environment, event-realization or character-profile facts."
            ),
            "noncanonical_rule": (
                "downstream_requirement and open_item are handoffs or unresolved "
                "questions, never established story-world facts."
            ),
        },
    }
    if session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL:
        realizations = body["source_sequence_realizations"]
        ordered_units = [
            unit
            for unit in _expected_claim_units(controls)
            if _source_unit_is_ordered(unit)
        ]
        request.update(
            {
                "review_protocol": LINE_REVIEW_PROTOCOL,
                "source_sequence_realization_count": len(realizations),
                "source_sequence_register_sha256": rt.canonical_sha256(
                    realizations
                ),
                "source_sequence_realization_ids": [
                    item["id"] for item in realizations
                ],
                "ordered_source_units": copy.deepcopy(ordered_units),
            }
        )
        request["review_contract"]["source_sequence_rule"] = (
            "Pass each realization only when its exact from/to states preserve "
            "the complete meaning and direction of that ordered source unit; "
            "inspect the neighboring states and surrounding line context at "
            "both semantic endpoints. For a cross-line realization, separately "
            "check that from_anchor-to-boundary_from is forward on the source "
            "line and boundary_to-to_anchor is forward on the target line. "
            "The review rationale "
            "must explain both the exact semantic endpoint choice and the "
            "implementation-boundary choice. Reject an intermediate or later "
            "boundary substituted for the source endpoint, even when the "
            "structural reservation itself is valid. "
            "Use semantic_constraint only for a genuine narrative norm, "
            "information boundary, evaluation rule, or similar non-state rule; "
            "reject any causal or character-development sequence disguised as "
            "a constraint. Its declared phase-3 witness kind must be appropriate."
        )
        if session.get("contract_revision") == CURRENT_CONTRACT_REVISION:
            request["review_contract"]["source_sequence_rule"] += (
                " For an ordered_link candidate, pass "
                "non_relational_candidate only when the source expresses no "
                "relation; every anchor, reservation, fulfillment, and dimension "
                "field must then remain null. Never add an uncited antecedent "
                "merely to avoid a realization collision."
            )
    return request


def start_s1_line_claim_review(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    input_gate: Any,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze one mechanically valid line candidate for an independent reviewer."""

    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, _, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    if (root / "generation-evidence" / "02-line-design.json").exists():
        _fail("S1_PHASE_ORDER_INVALID", "line-design is already sealed")
    body = copy.deepcopy(dict(payload))
    line_fields = _phase_fields_for_session(session, "line-design")
    if set(body) != set(line_fields):
        _fail(
            "S1_PHASE_PAYLOAD_INVALID",
            f"line-design must contain exactly {list(line_fields)}",
        )
    _validate_agent_text(body, path="$.line-design-review")
    demand_payload = _sealed_phase_payload(root, "demand-scan", session)
    _validate_line_phase_semantics(
        demand_payload,
        body,
        controls,
        require_source_sequences=(
            session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
        ),
        require_current_contract=(
            session.get("contract_revision") == CURRENT_CONTRACT_REVISION
        ),
    )
    request = _expected_line_review_request(session, body, controls)
    request_path, _ = _line_review_paths(root, request["candidate_sha256"])
    if request_path.exists():
        if _read(request_path, "S1_LINE_REVIEW_INVALID") != request:
            _fail("S1_LINE_REVIEW_INVALID", "existing request differs")
        return copy.deepcopy(request)
    _write(request_path, request)
    return copy.deepcopy(request)


def submit_s1_line_claim_review(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    review: Mapping[str, Any] | None = None,
    verdicts: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    """Seal a reviewer-thread verdict for one exact line candidate."""

    root = Path(workspace).resolve()
    request_path, review_path = _line_review_paths(root, candidate_sha256)
    request = _read(request_path, "S1_LINE_REVIEW_MISSING")
    session = _read(root / "generation-session.json", "S1_SESSION_INVALID")
    reviewer_thread = os.environ.get("CODEX_THREAD_ID", "").strip()
    if (
        not reviewer_thread
        or reviewer_thread == session.get("thread_id")
        or request.get("generation_thread_id") != session.get("thread_id")
        or request.get("session_id") != session.get("session_id")
        or request.get("candidate_sha256") != candidate_sha256
        or rt.canonical_sha256(request.get("candidate")) != candidate_sha256
        or rt.canonical_sha256(
            request.get("candidate", {}).get("line_claim_authority")
        )
        != request.get("claim_register_sha256")
    ):
        _fail(
            "S1_LINE_REVIEW_NOT_INDEPENDENT",
            "reviewer must be a distinct authenticated thread on the frozen request",
        )
    if review_path.exists():
        _fail("S1_LINE_REVIEW_ALREADY_SEALED", candidate_sha256)
    current_protocol = request.get("review_protocol") == LINE_REVIEW_PROTOCOL
    if current_protocol:
        if verdicts is not None or not isinstance(review, Mapping) or set(review) != {
            "claim_verdicts", "source_sequence_verdicts"
        }:
            _fail(
                "S1_LINE_REVIEW_INVALID",
                "current protocol requires the complete claim and source-sequence review envelope",
            )
        claim_input = review["claim_verdicts"]
        sequence_input = review["source_sequence_verdicts"]
    else:
        if review is not None or verdicts is None:
            _fail("S1_LINE_REVIEW_INVALID", "legacy review requires verdicts")
        claim_input = verdicts
        sequence_input = []
    if not isinstance(claim_input, Sequence) or isinstance(claim_input, (str, bytes)):
        _fail("S1_LINE_REVIEW_INVALID", "claim_verdicts must be a list")
    verdict_list = [copy.deepcopy(dict(item)) for item in claim_input]
    expected_ids = request.get("claim_ids")
    if (
        not isinstance(expected_ids, list)
        or len(verdict_list) != len(expected_ids)
        or any(
            set(item) != {"claim_id", "verdict", "rationale"}
            or item.get("claim_id") != expected_ids[index]
            or item.get("verdict") not in {"pass", "fail"}
            or not isinstance(item.get("rationale"), str)
            or not item["rationale"].strip()
            for index, item in enumerate(verdict_list)
        )
    ):
        _fail("S1_LINE_REVIEW_INVALID", "verdicts must exactly cover every claim")
    sequence_verdicts = [
        copy.deepcopy(dict(item)) for item in sequence_input
    ] if isinstance(sequence_input, Sequence) and not isinstance(sequence_input, (str, bytes)) else []
    if current_protocol:
        realizations = request["candidate"]["source_sequence_realizations"]
        if (
            len(sequence_verdicts) != len(realizations)
            or any(
                set(item) != {
                    "realization_id", "source_unit_id", "verdict", "rationale"
                }
                or item.get("realization_id") != realizations[index]["id"]
                or item.get("source_unit_id") != realizations[index]["source_unit_id"]
                or item.get("verdict") not in {"pass", "fail"}
                or not isinstance(item.get("rationale"), str)
                or not item["rationale"].strip()
                for index, item in enumerate(sequence_verdicts)
            )
        ):
            _fail(
                "S1_LINE_REVIEW_INVALID",
                "source_sequence_verdicts must exactly cover every realization",
            )
    review_record = {
        "schema_version": "2.0",
        "run_id": request["run_id"],
        "stage": "S1",
        "review_kind": "line-claim-authority",
        "session_id": request["session_id"],
        "generation_thread_id": request["generation_thread_id"],
        "reviewer_thread_id": reviewer_thread,
        "candidate_sha256": candidate_sha256,
        "claim_register_sha256": request["claim_register_sha256"],
        "request_sha256": rt.sha256_file(request_path),
        "verdict": (
            "pass"
            if all(item["verdict"] == "pass" for item in [*verdict_list, *sequence_verdicts])
            else "fail"
        ),
        "claim_verdicts": verdict_list,
    }
    if current_protocol:
        review_record.update(
            {
                "review_protocol": LINE_REVIEW_PROTOCOL,
                "source_sequence_register_sha256": request[
                    "source_sequence_register_sha256"
                ],
                "source_sequence_verdicts": sequence_verdicts,
            }
        )
    _write(review_path, review_record)
    return rt.artifact_reference(review_path, root=root)


def start_s1_topology_semantic_review(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    input_gate: Any,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, Any]:
    """Freeze one mechanically valid topology candidate for semantic review."""

    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    if session.get("semantic_review_protocol") != TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL:
        _fail("S1_TOPOLOGY_REVIEW_INVALID", "session does not require the current review")
    if (root / "generation-evidence" / "03-topology-and-consistency.json").exists():
        _fail("S1_PHASE_ORDER_INVALID", "topology-and-consistency is already sealed")
    body = copy.deepcopy(dict(payload))
    if set(body) != set(PHASE_FIELDS["topology-and-consistency"]):
        _fail(
            "S1_PHASE_PAYLOAD_INVALID",
            "topology-and-consistency payload fields are invalid",
        )
    _validate_agent_text(body, path="$.topology-semantic-review")
    demand_payload = _sealed_phase_payload(root, "demand-scan", session)
    line_payload = _sealed_phase_payload(root, "line-design", session)
    _validate_topology_phase_semantics(
        demand_payload,
        line_payload,
        body,
        controls,
        baseline=baseline,
        runtime=contract_runtime,
        require_current_contract=(
            session.get("contract_revision") == CURRENT_CONTRACT_REVISION
        ),
    )
    request = _expected_topology_review_request(
        session, line_payload, body, controls
    )
    request_path, _ = _topology_review_paths(root, request["candidate_sha256"])
    if request_path.exists():
        if _read(request_path, "S1_TOPOLOGY_REVIEW_INVALID") != request:
            _fail("S1_TOPOLOGY_REVIEW_INVALID", "existing request differs")
        return copy.deepcopy(request)
    _write(request_path, request)
    return copy.deepcopy(request)


def submit_s1_topology_semantic_review(
    workspace: str | Path,
    *,
    candidate_sha256: str,
    verdicts: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Seal a distinct-thread, structurally evidenced topology review."""

    root = Path(workspace).resolve()
    request_path, review_path = _topology_review_paths(root, candidate_sha256)
    request = _read(request_path, "S1_TOPOLOGY_REVIEW_MISSING")
    session = _read(root / "generation-session.json", "S1_SESSION_INVALID")
    reviewer_thread = os.environ.get("CODEX_THREAD_ID", "").strip()
    if (
        not reviewer_thread
        or reviewer_thread == session.get("thread_id")
        or request.get("generation_thread_id") != session.get("thread_id")
        or request.get("session_id") != session.get("session_id")
        or request.get("candidate_sha256") != candidate_sha256
        or rt.canonical_sha256(request.get("candidate", {}).get("topology"))
        != candidate_sha256
    ):
        _fail(
            "S1_TOPOLOGY_REVIEW_NOT_INDEPENDENT",
            "reviewer must be a distinct authenticated thread on the frozen request",
        )
    if review_path.exists():
        _fail("S1_TOPOLOGY_REVIEW_ALREADY_SEALED", candidate_sha256)

    verdict_list = [copy.deepcopy(dict(item)) for item in verdicts]
    if not _topology_verdicts_valid(request, verdict_list):
        _fail(
            "S1_TOPOLOGY_REVIEW_INVALID",
            "verdicts must cover six dimensions with structural evidence",
        )
    review = {
        "schema_version": "2.0",
        "run_id": request["run_id"],
        "stage": "S1",
        "review_kind": request["review_kind"],
        "review_protocol": request["review_protocol"],
        "session_id": request["session_id"],
        "generation_thread_id": request["generation_thread_id"],
        "reviewer_thread_id": reviewer_thread,
        "candidate_sha256": candidate_sha256,
        "line_design_sha256": request["line_design_sha256"],
        "request_sha256": rt.sha256_file(request_path),
        "verdict": (
            "pass"
            if all(item["verdict"] == "pass" for item in verdict_list)
            else "fail"
        ),
        "dimension_verdicts": verdict_list,
    }
    _write(review_path, review)
    return rt.artifact_reference(review_path, root=root)


def _validate_line_claim_review(
    root: Path,
    body: Mapping[str, Any],
    session: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    require_pass: bool = True,
) -> tuple[Path, Path]:
    expected_request = _expected_line_review_request(session, body, controls)
    request_path, review_path = _line_review_paths(
        root, expected_request["candidate_sha256"]
    )
    request = _read(request_path, "S1_LINE_REVIEW_MISSING")
    if request != expected_request:
        _fail("S1_LINE_REVIEW_INVALID", "request does not bind the candidate")
    review = _read(review_path, "S1_LINE_REVIEW_MISSING")
    reviewer_thread = review.get("reviewer_thread_id")
    verdicts = review.get("claim_verdicts")
    expected_ids = expected_request["claim_ids"]
    current_protocol = expected_request.get("review_protocol") == LINE_REVIEW_PROTOCOL
    expected_fields = {
        "schema_version",
        "run_id",
        "stage",
        "review_kind",
        "session_id",
        "generation_thread_id",
        "reviewer_thread_id",
        "candidate_sha256",
        "claim_register_sha256",
        "request_sha256",
        "verdict",
        "claim_verdicts",
    }
    if current_protocol:
        expected_fields.update(
            {
                "review_protocol",
                "source_sequence_register_sha256",
                "source_sequence_verdicts",
            }
        )
    if (
        set(review) != expected_fields
        or review.get("schema_version") != "2.0"
        or review.get("run_id") != session["run_id"]
        or review.get("stage") != "S1"
        or review.get("review_kind") != "line-claim-authority"
        or review.get("session_id") != session["session_id"]
        or review.get("generation_thread_id") != session["thread_id"]
        or not isinstance(reviewer_thread, str)
        or not reviewer_thread.strip()
        or reviewer_thread == session["thread_id"]
        or review.get("candidate_sha256") != expected_request["candidate_sha256"]
        or review.get("claim_register_sha256")
        != expected_request["claim_register_sha256"]
        or review.get("request_sha256") != rt.sha256_file(request_path)
        or not isinstance(verdicts, list)
        or len(verdicts) != len(expected_ids)
        or any(
            not isinstance(item, Mapping)
            or set(item) != {"claim_id", "verdict", "rationale"}
            or item.get("claim_id") != expected_ids[index]
            or item.get("verdict") not in {"pass", "fail"}
            or not isinstance(item.get("rationale"), str)
            or not item["rationale"].strip()
            for index, item in enumerate(verdicts)
        )
    ):
        _fail("S1_LINE_REVIEW_INVALID", "review evidence is stale or incomplete")
    sequence_verdicts = review.get("source_sequence_verdicts", [])
    if current_protocol:
        realizations = body["source_sequence_realizations"]
        if (
            review.get("review_protocol") != LINE_REVIEW_PROTOCOL
            or review.get("source_sequence_register_sha256")
            != expected_request["source_sequence_register_sha256"]
            or not isinstance(sequence_verdicts, list)
            or len(sequence_verdicts) != len(realizations)
            or any(
                not isinstance(item, Mapping)
                or set(item) != {
                    "realization_id", "source_unit_id", "verdict", "rationale"
                }
                or item.get("realization_id") != realizations[index]["id"]
                or item.get("source_unit_id") != realizations[index]["source_unit_id"]
                or item.get("verdict") not in {"pass", "fail"}
                or not isinstance(item.get("rationale"), str)
                or not item["rationale"].strip()
                for index, item in enumerate(sequence_verdicts)
            )
        ):
            _fail(
                "S1_LINE_REVIEW_INVALID",
                "source-sequence review evidence is stale or incomplete",
            )
    expected_verdict = (
        "pass"
        if all(
            item["verdict"] == "pass"
            for item in [*verdicts, *sequence_verdicts]
        )
        else "fail"
    )
    if review.get("verdict") != expected_verdict:
        _fail("S1_LINE_REVIEW_INVALID", "aggregate verdict is inconsistent")
    if require_pass and expected_verdict != "pass":
        _fail(
            "S1_LINE_CLAIM_AUTHORITY_INVALID",
            "independent review rejected claims or source-sequence realizations",
        )
    return request_path, review_path


def _validate_topology_semantic_review(
    root: Path,
    line_payload: Mapping[str, Any],
    body: Mapping[str, Any],
    session: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    require_pass: bool = True,
) -> tuple[Path, Path]:
    expected_request = _expected_topology_review_request(
        session, line_payload, body, controls
    )
    request_path, review_path = _topology_review_paths(
        root, expected_request["candidate_sha256"]
    )
    request = _read(request_path, "S1_TOPOLOGY_REVIEW_MISSING")
    if request != expected_request:
        _fail("S1_TOPOLOGY_REVIEW_INVALID", "request does not bind the candidate")
    review = _read(review_path, "S1_TOPOLOGY_REVIEW_MISSING")
    verdicts = review.get("dimension_verdicts")
    expected_fields = {
        "schema_version", "run_id", "stage", "review_kind", "review_protocol",
        "session_id", "generation_thread_id", "reviewer_thread_id",
        "candidate_sha256", "line_design_sha256", "request_sha256",
        "verdict", "dimension_verdicts",
    }
    if (
        set(review) != expected_fields
        or review.get("schema_version") != "2.0"
        or review.get("run_id") != session["run_id"]
        or review.get("stage") != "S1"
        or review.get("review_kind") != "topology-and-information-semantics"
        or review.get("review_protocol") != TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL
        or review.get("session_id") != session["session_id"]
        or review.get("generation_thread_id") != session["thread_id"]
        or not isinstance(review.get("reviewer_thread_id"), str)
        or not review["reviewer_thread_id"].strip()
        or review["reviewer_thread_id"] == session["thread_id"]
        or review.get("candidate_sha256") != expected_request["candidate_sha256"]
        or review.get("line_design_sha256") != expected_request["line_design_sha256"]
        or review.get("request_sha256") != rt.sha256_file(request_path)
        or not isinstance(verdicts, list)
        or not _topology_verdicts_valid(expected_request, verdicts)
    ):
        _fail("S1_TOPOLOGY_REVIEW_INVALID", "review evidence is stale or incomplete")
    expected_verdict = (
        "pass" if all(item["verdict"] == "pass" for item in verdicts) else "fail"
    )
    if review.get("verdict") != expected_verdict:
        _fail("S1_TOPOLOGY_REVIEW_INVALID", "aggregate verdict is inconsistent")
    if require_pass and expected_verdict != "pass":
        _fail(
            "S1_TOPOLOGY_SEMANTICS_INVALID",
            "independent review rejected topology semantics",
        )
    return request_path, review_path


def _sealed_phase_payload(
    root: Path, phase: str, session: Mapping[str, Any]
) -> dict[str, Any]:
    index = PHASES.index(phase) + 1
    evidence = _read(
        root / "generation-evidence" / f"{index:02d}-{phase}.json",
        "S1_EVIDENCE_INVALID",
    )
    payload = evidence.get("payload")
    if (
        not isinstance(payload, Mapping)
        or evidence.get("phase") != phase
        or evidence.get("sequence") != index
        or evidence.get("session_id") != session["session_id"]
        or evidence.get("payload_sha256") != rt.canonical_sha256(payload)
        or set(payload) != set(_phase_fields_for_session(session, phase))
    ):
        _fail("S1_EVIDENCE_INVALID", f"sealed {phase} payload is invalid")
    return copy.deepcopy(dict(payload))


def _validate_demand_phase_semantics(
    demands: Any,
    controls: Sequence[Mapping[str, Any]],
) -> None:
    code = "S1_DEMAND_PHASE_SEMANTIC_INVALID"
    if not isinstance(demands, list):
        _fail(code, "storyline_demands must be a list")
    controls_by_id = {item["id"]: item for item in controls}
    demand_ids: set[str] = set()
    bound_controls: list[str] = []
    for demand in demands:
        if not isinstance(demand, Mapping):
            _fail(code, "every demand must be an object")
        demand_id = demand.get("id")
        source_ids = demand.get("source_ids")
        if (
            not isinstance(demand_id, str)
            or demand_id in demand_ids
            or not isinstance(source_ids, list)
            or len(source_ids) != 1
            or source_ids[0] not in controls_by_id
        ):
            _fail(code, "demand IDs and source IDs must be unique and one-to-one")
        demand_ids.add(demand_id)
        control_id = source_ids[0]
        bound_controls.append(control_id)
        control = controls_by_id[control_id]
        obligation = demand.get("obligation")
        if (
            not isinstance(obligation, str)
            or control["heading"] not in obligation
            or _control_text(control["value"]) not in obligation
        ):
            _fail(code, f"{demand_id} does not carry the exact heading/value")
        disposition = demand.get("disposition")
        if control["hardness"] == "author_open" and disposition not in {
            "optional_melody", "not_applicable"
        }:
            _fail(code, f"{demand_id} adjudicates an author-open control")
    if (
        set(bound_controls) != set(controls_by_id)
        or len(bound_controls) != len(set(bound_controls))
    ):
        _fail(code, "B0 controls and demands must be exactly one-to-one")


def _validate_line_claim_authority(
    line_payload: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    final_model: Mapping[str, Any] | None = None,
) -> set[str]:
    code = "S1_LINE_CLAIM_AUTHORITY_INVALID"
    ledger = line_payload.get("line_claim_authority")
    if not isinstance(ledger, list):
        _fail(code, "line_claim_authority must be a list")
    expected = inspect_s1_line_claims(line_payload, controls)
    if len(ledger) != len(expected):
        _fail(code, "claim ledger does not exactly cover all conclusion spans")
    controls_by_id = {item["id"]: item for item in controls}
    decisions = line_payload.get("design_decisions", [])
    storylines = line_payload.get("storylines", [])
    decisions_by_id = {
        item.get("id"): item
        for item in decisions
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    required_keys = {
        "claim_id",
        "pointer",
        "start_offset",
        "end_offset",
        "text",
        "text_sha256",
        "disposition",
        "source_control_ids",
        "decision_ids",
        "target_stage",
        "target_requirement_id",
        "open_item_id",
    }
    claim_ids: set[str] = set()
    for expected_claim, claim in zip(expected, ledger, strict=True):
        if not isinstance(claim, Mapping) or set(claim) != required_keys:
            _fail(code, "every claim must contain exactly the contract fields")
        for field, value in expected_claim.items():
            if claim.get(field) != value:
                _fail(code, f"{expected_claim['claim_id']} has stale {field}")
        claim_id = claim["claim_id"]
        if claim_id in claim_ids:
            _fail(code, f"duplicate claim {claim_id}")
        claim_ids.add(claim_id)
        disposition = claim.get("disposition")
        source_ids = claim.get("source_control_ids")
        decision_ids = claim.get("decision_ids")
        target_stage = claim.get("target_stage")
        target_id = claim.get("target_requirement_id")
        open_id = claim.get("open_item_id")
        if (
            disposition not in LINE_CLAIM_DISPOSITIONS
            or not isinstance(source_ids, list)
            or len(source_ids) != len(set(source_ids))
            or not isinstance(decision_ids, list)
            or len(decision_ids) != len(set(decision_ids))
        ):
            _fail(code, f"{claim_id} has invalid disposition or references")
        exact_source_ids = sorted(
            control_id
            for control_id, control in controls_by_id.items()
            if claim["text"]
            in {control["heading"], _control_text(control["value"])}
        )
        if exact_source_ids:
            if (
                disposition != "source_bound"
                or sorted(source_ids) != exact_source_ids
                or decision_ids
                or target_stage is not None
                or target_id is not None
                or open_id is not None
            ):
                _fail(code, f"{claim_id} exact source span is not source-bound")
            continue
        if disposition == "source_bound":
            _fail(code, f"{claim_id} source-bound text is not an exact source fragment")
        if source_ids:
            _fail(code, f"{claim_id} non-source disposition cites source controls")
        pointer_parts = claim["pointer"].strip("/").split("/")
        if disposition == "s1_structural_derivation":
            if (
                not decision_ids
                or any(item not in decisions_by_id for item in decision_ids)
                or target_stage is not None
                or target_id is not None
                or open_id is not None
            ):
                _fail(code, f"{claim_id} has invalid S1 decision provenance")
            if pointer_parts[0] == "design_decisions":
                owner = decisions[int(pointer_parts[1])]["id"]
                if decision_ids != [owner]:
                    _fail(code, f"{claim_id} must bind its owning decision")
            elif pointer_parts[0] == "storylines":
                line = storylines[int(pointer_parts[1])]
                allowed = set(line.get("source_decision_ids", []))
                if not set(decision_ids).issubset(allowed) or any(
                    line["id"] not in decisions_by_id[item].get("projection_ids", [])
                    for item in decision_ids
                ):
                    _fail(code, f"{claim_id} decision does not project to its line")
            else:
                _fail(code, f"{claim_id} pointer is outside line design")
        elif disposition == "downstream_requirement":
            if (
                decision_ids
                or target_stage not in _TARGET_REQUIREMENT_PREFIX
                or not isinstance(target_id, str)
                or not target_id.startswith(_TARGET_REQUIREMENT_PREFIX[target_stage])
                or open_id is not None
            ):
                _fail(code, f"{claim_id} has invalid downstream target")
            if final_model is not None:
                field = {
                    "W1": "world_requirements",
                    "E1": "environment_requirements",
                    "T1": "event_requirements",
                    "C1": "character_requirements",
                }[target_stage]
                target = next(
                    (
                        item
                        for item in final_model[field]
                        if item.get("id") == target_id
                    ),
                    None,
                )
                if target is None or not _value_participates(claim["text"], target):
                    _fail(code, f"{claim_id} downstream target is not realized")
        elif disposition == "open_item":
            if (
                decision_ids
                or target_stage is not None
                or target_id is not None
                or not isinstance(open_id, str)
                or not open_id.startswith("OPEN-")
            ):
                _fail(code, f"{claim_id} has invalid open-item reference")
            if final_model is not None:
                target = next(
                    (
                        item
                        for item in final_model["open_items"]
                        if item.get("id") == open_id
                    ),
                    None,
                )
                if target is None or not _value_participates(claim["text"], target):
                    _fail(code, f"{claim_id} open item is not realized")
    return claim_ids


def _validate_source_sequence_realizations(
    line_payload: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    required: bool,
) -> list[str]:
    """Validate the phase-2 exact cover of locked ordered source transitions."""

    code = "S1_SOURCE_SEQUENCE_REALIZATION_INVALID"
    register = line_payload.get("source_sequence_realizations")
    if register is None and not required:
        return []
    if not isinstance(register, list):
        _fail(code, "source_sequence_realizations must be a list")
    ordered_units = [
        unit for unit in _expected_claim_units(controls) if _source_unit_is_ordered(unit)
    ]
    ordered_unit_by_id = {unit["id"]: unit for unit in ordered_units}
    expected_unit_ids = [unit["id"] for unit in ordered_units]
    lines = {
        item.get("id"): item
        for item in line_payload.get("storylines", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    realization_ids: list[str] = []
    realized_unit_ids: list[str] = []
    reserved_ids: list[str] = []
    legacy_fields = {
        "id",
        "source_unit_id",
        "from_anchor",
        "to_anchor",
        "realization_scope",
        "reserved_connection_id",
        "phase3_fulfillment_kind",
        "expected_witness_type",
        "rationale",
    }
    boundary_fields = {"boundary_from_anchor", "boundary_to_anchor"}
    extension_fields = boundary_fields | {"consistency_dimension"}
    for index, item in enumerate(register):
        allowed_shapes = (
            {frozenset(legacy_fields | extension_fields)}
            if required
            else {
                frozenset(legacy_fields),
                frozenset(legacy_fields | extension_fields),
            }
        )
        if not isinstance(item, Mapping) or frozenset(item) not in allowed_shapes:
            _fail(code, f"realization {index} has an invalid shape")
        realization_id = item.get("id")
        source_unit_id = item.get("source_unit_id")
        rationale = item.get("rationale")
        if (
            not isinstance(realization_id, str)
            or not re.fullmatch(r"SSR-[A-Za-z0-9._-]+", realization_id)
            or not isinstance(source_unit_id, str)
            or not isinstance(rationale, str)
            or not rationale.strip()
        ):
            _fail(code, f"realization {index} has invalid identity or rationale")
        scope = item.get("realization_scope")
        reserved_id = item.get("reserved_connection_id")
        fulfillment_kind = item.get("phase3_fulfillment_kind")
        witness_type = item.get("expected_witness_type")
        consistency_dimension = item.get("consistency_dimension")
        expected_witness_types = {
            "obligation": "story_obligation",
            "marker": "narrative_marker",
            "consistency": "consistency_check",
        }
        if scope == "non_relational_candidate":
            unit = ordered_unit_by_id.get(source_unit_id)
            if (
                unit is None
                or unit.get("kind") != "ordered_link"
                or unit.get("relation_mode") != "candidate"
                or any(
                    item.get(field) is not None
                    for field in (
                        "from_anchor",
                        "to_anchor",
                        "boundary_from_anchor",
                        "boundary_to_anchor",
                        "reserved_connection_id",
                        "phase3_fulfillment_kind",
                        "expected_witness_type",
                        "consistency_dimension",
                    )
                )
            ):
                _fail(
                    code,
                    f"{realization_id} is not a null reviewed candidate disposition",
                )
            realization_ids.append(realization_id)
            realized_unit_ids.append(source_unit_id)
            continue
        if scope == "semantic_constraint":
            if (
                item.get("from_anchor") is not None
                or item.get("to_anchor") is not None
                or item.get("boundary_from_anchor") is not None
                or item.get("boundary_to_anchor") is not None
                or reserved_id is not None
                or expected_witness_types.get(fulfillment_kind) != witness_type
                or (
                    consistency_dimension not in CONSISTENCY_DIMENSIONS
                    if fulfillment_kind == "consistency"
                    else consistency_dimension is not None
                )
            ):
                _fail(
                    code,
                    f"{realization_id} semantic constraint has invalid state or fulfillment fields",
                )
            realization_ids.append(realization_id)
            realized_unit_ids.append(source_unit_id)
            continue
        if (
            fulfillment_kind is not None
            or witness_type is not None
            or consistency_dimension is not None
        ):
            _fail(
                code,
                f"{realization_id} state realization declares semantic fulfillment",
            )
        anchors: list[tuple[str, int, str]] = []
        for field in ("from_anchor", "to_anchor"):
            anchor = item.get(field)
            if not isinstance(anchor, Mapping) or set(anchor) != {
                "storyline_id", "state_index", "state"
            }:
                _fail(code, f"{realization_id}.{field} is not an exact anchor")
            line_id = anchor.get("storyline_id")
            state_index = anchor.get("state_index")
            line = lines.get(line_id)
            if line is None or not isinstance(state_index, int) or state_index < 0:
                _fail(code, f"{realization_id}.{field} is dangling")
            states = [line.get("start_state"), *line.get("state_changes", []), line.get("end_state")]
            if state_index >= len(states) or states[state_index] != anchor.get("state"):
                _fail(code, f"{realization_id}.{field} does not bind exact state text")
            anchors.append((line_id, state_index, states[state_index]))
        if anchors[0][:2] == anchors[1][:2]:
            _fail(code, f"{realization_id} collapses an ordered transition")
        if scope == "within_line":
            if anchors[0][0] != anchors[1][0] or anchors[0][1] >= anchors[1][1]:
                _fail(code, f"{realization_id} within-line anchors are reversed")
            if (
                reserved_id is not None
                or item.get("boundary_from_anchor") is not None
                or item.get("boundary_to_anchor") is not None
            ):
                _fail(
                    code,
                    f"{realization_id} within-line realization has boundary or reservation state",
                )
        elif scope == "cross_line":
            if anchors[0][0] == anchors[1][0]:
                _fail(code, f"{realization_id} cross-line anchors use one line")
            boundary_anchors: list[tuple[str, int, str]] = []
            if boundary_fields.issubset(item):
                for field in ("boundary_from_anchor", "boundary_to_anchor"):
                    anchor = item.get(field)
                    if not isinstance(anchor, Mapping) or set(anchor) != {
                        "storyline_id", "state_index", "state"
                    }:
                        _fail(code, f"{realization_id}.{field} is not an exact anchor")
                    line_id = anchor.get("storyline_id")
                    state_index = anchor.get("state_index")
                    line = lines.get(line_id)
                    if line is None or not isinstance(state_index, int) or state_index < 0:
                        _fail(code, f"{realization_id}.{field} is dangling")
                    states = [
                        line.get("start_state"),
                        *line.get("state_changes", []),
                        line.get("end_state"),
                    ]
                    if state_index >= len(states) or states[state_index] != anchor.get("state"):
                        _fail(code, f"{realization_id}.{field} does not bind exact state text")
                    boundary_anchors.append((line_id, state_index, states[state_index]))
            else:
                boundary_anchors = list(anchors)
            if (
                boundary_anchors[0][0] != anchors[0][0]
                or boundary_anchors[0][1] < anchors[0][1]
                or boundary_anchors[1][0] != anchors[1][0]
                or boundary_anchors[1][1] > anchors[1][1]
            ):
                _fail(
                    code,
                    f"{realization_id} boundary anchors do not form forward line paths",
                )
            if not isinstance(reserved_id, str) or not re.fullmatch(
                r"SLC-[A-Za-z0-9._-]+", reserved_id
            ):
                _fail(code, f"{realization_id} lacks a valid reserved connection")
            if any(
                reserved_id not in set(lines[line_id].get("connection_ids", []))
                for line_id in (boundary_anchors[0][0], boundary_anchors[1][0])
            ):
                _fail(code, f"{realization_id} reservation is not shared by both lines")
            reserved_ids.append(reserved_id)
        else:
            _fail(code, f"{realization_id} has invalid realization_scope")
        realization_ids.append(realization_id)
        realized_unit_ids.append(source_unit_id)
    if len(realization_ids) != len(set(realization_ids)):
        _fail(code, "realization IDs collide")
    if realized_unit_ids != expected_unit_ids:
        _fail(code, "ordered source units must be covered exactly once in registry order")
    if len(reserved_ids) != len(set(reserved_ids)):
        _fail(code, "different ordered transitions reuse one reserved connection")
    return realization_ids


def _validate_source_sequence_structural_closure(
    line_payload: Mapping[str, Any],
    *,
    require_closure_declarations: bool = False,
) -> None:
    """Prove phase-2 structural closure from fixed and still-free line capacity."""

    code = "S1_SOURCE_SEQUENCE_STRUCTURAL_CLOSURE_MISSING"
    lines = {
        item.get("id"): item
        for item in line_payload.get("storylines", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    main_ids = [
        line_id for line_id, line in lines.items() if line.get("type") == "main"
    ]
    if len(main_ids) != 1:
        return
    _validate_line_closure_declarations(
        line_payload, required=require_closure_declarations
    )
    main_id = main_ids[0]
    structural_ids = {
        line_id
        for line_id, line in lines.items()
        if line.get("type") != "optional_melody"
    }
    converging_ids = (
        {
            line_id
            for line_id in structural_ids
            if line_id == main_id
            or lines[line_id].get("closure_mode") == "converges_to_main"
        }
        if require_closure_declarations
        else structural_ids
    )
    graph: dict[str, set[str]] = {line_id: set() for line_id in converging_ids}
    reserved_ids: set[str] = set()

    for realization in line_payload.get("source_sequence_realizations", []):
        if (
            not isinstance(realization, Mapping)
            or realization.get("realization_scope") != "cross_line"
        ):
            continue
        connection_id = realization.get("reserved_connection_id")
        if isinstance(connection_id, str):
            reserved_ids.add(connection_id)
        from_anchor = realization.get("boundary_from_anchor") or realization.get(
            "from_anchor"
        )
        to_anchor = realization.get("boundary_to_anchor") or realization.get(
            "to_anchor"
        )
        if not isinstance(from_anchor, Mapping) or not isinstance(to_anchor, Mapping):
            continue
        source_id = from_anchor.get("storyline_id")
        target_id = to_anchor.get("storyline_id")
        if source_id in converging_ids and target_id in converging_ids:
            graph[source_id].add(target_id)

    connection_owners: dict[str, set[str]] = {}
    for line_id, line in lines.items():
        connection_ids = line.get("connection_ids", [])
        if not isinstance(connection_ids, list):
            continue
        for connection_id in connection_ids:
            if isinstance(connection_id, str):
                connection_owners.setdefault(connection_id, set()).add(line_id)
    for connection_id, owners in connection_owners.items():
        if connection_id in reserved_ids or len(owners) != 2:
            continue
        source_id, target_id = sorted(owners)
        if source_id not in converging_ids or target_id not in converging_ids:
            continue
        graph[source_id].add(target_id)
        graph[target_id].add(source_id)

    missing: list[str] = []
    for line_id in sorted(converging_ids - {main_id}):
        visited = {line_id}
        frontier = list(graph[line_id])
        while frontier:
            current = frontier.pop()
            if current in visited:
                continue
            visited.add(current)
            frontier.extend(graph[current] - visited)
        if main_id not in visited:
            missing.append(line_id)
    if missing:
        _fail(code, f"structural lines cannot reach {main_id}: {missing}")


def _validate_line_phase_semantics(
    demand_payload: Mapping[str, Any],
    line_payload: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    require_source_sequences: bool = False,
    require_current_contract: bool = False,
) -> None:
    code = "S1_LINE_PHASE_SEMANTIC_INVALID"
    demands = demand_payload["storyline_demands"]
    _validate_demand_phase_semantics(demands, controls)
    storylines = line_payload.get("storylines")
    decisions = line_payload.get("design_decisions")
    if not isinstance(storylines, list) or not isinstance(decisions, list):
        _fail(code, "storylines and design_decisions must be lists")
    try:
        _validate_line_claim_authority(line_payload, controls)
    except S1Error as error:
        _fail(code, str(error))
    lines = {
        item.get("id"): item
        for item in storylines
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    if len(lines) != len(storylines) or not lines:
        _fail(code, "storyline IDs must be present and unique")
    controls_by_id = {item["id"]: item for item in controls}
    demand_by_control = {item["source_ids"][0]: item for item in demands}
    realized_by_storyline_id: dict[str, list[str]] = {
        line_id: [] for line_id in lines
    }
    for control_id, demand in demand_by_control.items():
        control = controls_by_id[control_id]
        matches = [
            line_id
            for line_id, line in lines.items()
            if _value_participates(control["heading"], line)
            and _value_participates(control["value"], line)
        ]
        if demand["disposition"] == "not_applicable":
            if matches:
                _fail(code, f"{demand['id']} is not_applicable but realized")
            continue
        if len(matches) != 1:
            _fail(
                code,
                f"{demand['id']} heading/value must participate in exactly one line",
            )
        line_id = matches[0]
        realized_by_storyline_id[line_id].append(control_id)
        if control["hardness"] == "author_open" and lines[line_id].get(
            "type"
        ) != "optional_melody":
            _fail(code, f"{demand['id']} author-open realization must remain optional")
    if any(not source_ids for source_ids in realized_by_storyline_id.values()):
        _fail(code, "every line must realize at least one active demand")
    for line_id, source_ids in realized_by_storyline_id.items():
        hardness = {controls_by_id[item]["hardness"] for item in source_ids}
        if len(hardness) > 1:
            _fail(code, f"{line_id} mixes author-open and locked controls")

    decision_by_id = {
        item.get("id"): item
        for item in decisions
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    if len(decision_by_id) != len(decisions):
        _fail(code, "decision IDs must be present and unique")
    projected_by_line: dict[str, set[str]] = {line_id: set() for line_id in lines}
    for decision_id, decision in decision_by_id.items():
        projection_ids = decision.get("projection_ids")
        impact_ids = decision.get("impact_ids")
        if (
            decision.get("owner") != "S1"
            or not isinstance(projection_ids, list)
            or not projection_ids
            or not set(projection_ids).issubset(lines)
            or not isinstance(impact_ids, list)
            or not set(impact_ids).issubset(lines)
        ):
            _fail(code, f"{decision_id} has an invalid owner or line projection")
        for line_id in projection_ids:
            projected_by_line[line_id].add(decision_id)
    for line_id, line in lines.items():
        source_decisions = line.get("source_decision_ids")
        if (
            not isinstance(source_decisions, list)
            or set(source_decisions) != projected_by_line[line_id]
            or not source_decisions
        ):
            _fail(code, f"{line_id} decision projection is not reciprocal")
        for control_id in realized_by_storyline_id[line_id]:
            control = controls_by_id[control_id]
            if not any(
                _value_participates(control["heading"], decision_by_id[item])
                and _value_participates(control["value"], decision_by_id[item])
                for item in source_decisions
            ):
                _fail(
                    code,
                    f"{line_id} decisions do not bind {control_id} heading/value",
                )
    if sum(line.get("type") == "main" for line in lines.values()) != 1:
        _fail(code, "line-design must contain exactly one main line")
    try:
        _validate_source_sequence_realizations(
            line_payload, controls, required=require_source_sequences
        )
    except S1Error as error:
        _fail(code, str(error))
    if require_source_sequences:
        _validate_source_sequence_structural_closure(
            line_payload,
            require_closure_declarations=require_current_contract,
        )


def _validate_reserved_source_sequence_connections(
    line_payload: Mapping[str, Any],
    connection_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require phase 3 to spend each phase-2 reservation on exact endpoints."""

    code = "S1_SOURCE_SEQUENCE_CONNECTION_MISMATCH"
    for realization in line_payload.get("source_sequence_realizations", []):
        if realization["realization_scope"] != "cross_line":
            continue
        connection_id = realization["reserved_connection_id"]
        connection = connection_by_id.get(connection_id)
        from_anchor = realization.get("boundary_from_anchor") or realization[
            "from_anchor"
        ]
        to_anchor = realization.get("boundary_to_anchor") or realization["to_anchor"]
        if connection is None or any(
            connection.get(field) != expected
            for field, expected in (
                ("from_storyline_id", from_anchor["storyline_id"]),
                ("from_state_index", from_anchor["state_index"]),
                ("from_state", from_anchor["state"]),
                ("to_storyline_id", to_anchor["storyline_id"]),
                ("to_state_index", to_anchor["state_index"]),
                ("to_state", to_anchor["state"]),
            )
        ):
            _fail(
                code,
                f"{realization['id']} reserved connection does not realize exact endpoints",
            )


def _validate_semantic_constraint_fulfillment(
    line_payload: Mapping[str, Any],
    topology_payload: Mapping[str, Any],
) -> None:
    """Require phase 3 to realize every phase-2 non-state semantic constraint."""

    code = "S1_SOURCE_SEQUENCE_FULFILLMENT_INVALID"
    units = {
        item.get("id"): item
        for item in topology_payload.get("story_claim_units", [])
        if isinstance(item, Mapping)
    }
    atoms_by_unit: dict[str, list[Mapping[str, Any]]] = {}
    for atom in topology_payload.get("story_claim_atoms", []):
        if isinstance(atom, Mapping):
            atoms_by_unit.setdefault(str(atom.get("source_unit_id")), []).append(atom)
    obligations = [
        item
        for item in topology_payload.get("story_obligation_register", [])
        if isinstance(item, Mapping)
    ]
    markers = [
        item
        for item in topology_payload.get("temporal_architecture", {}).get("markers", [])
        if isinstance(item, Mapping)
    ]
    consistency = [
        item
        for item in topology_payload.get("cross_line_consistency", [])
        if isinstance(item, Mapping)
    ]
    for realization in line_payload.get("source_sequence_realizations", []):
        if realization.get("realization_scope") == "non_relational_candidate":
            atoms = atoms_by_unit.get(realization["source_unit_id"], [])
            if (
                len(atoms) != 1
                or atoms[0].get("atom_kind") != "non_relational"
                or atoms[0].get("obligation_ids") != []
                or atoms[0].get("review_required") is not False
            ):
                _fail(
                    code,
                    f"{realization['id']} lacks its approved non-relational atom",
                )
            continue
        if realization.get("realization_scope") != "semantic_constraint":
            continue
        unit_id = realization["source_unit_id"]
        unit = units.get(unit_id)
        atoms = atoms_by_unit.get(unit_id, [])
        if unit is None or not atoms or any(
            atom.get("atom_kind") == "non_relational" for atom in atoms
        ):
            _fail(
                code,
                f"{realization['id']} lacks a relational source atom",
            )
        control_id = unit.get("control_id")
        kind = realization["phase3_fulfillment_kind"]
        for atom in atoms:
            atom_id = atom.get("id")
            if kind == "obligation":
                witnessed = any(
                    atom_id in item.get("source_claim_atom_ids", [])
                    and control_id in item.get("source_control_ids", [])
                    for item in obligations
                )
            elif kind == "marker":
                witnessed = any(
                    atom_id in item.get("source_claim_atom_ids", [])
                    and control_id in item.get("source_control_ids", [])
                    for item in markers
                )
            elif kind == "consistency":
                witnessed = any(
                    item.get("dimension") == realization.get("consistency_dimension")
                    and
                    (
                        (
                            atom_id in item.get("source_claim_atom_ids", [])
                            and control_id in item.get("source_control_ids", [])
                        )
                        if "source_claim_atom_ids" in item
                        else (
                            atom_id in item.get("witness_ids", [])
                            and control_id in item.get("witness_ids", [])
                        )
                    )
                    for item in consistency
                )
            else:
                witnessed = False
            if not witnessed:
                _fail(
                    code,
                    f"{realization['id']} has no traceable {kind} witness for {atom_id}",
                )


def _validate_topology_phase_semantics(
    demand_payload: Mapping[str, Any],
    line_payload: Mapping[str, Any],
    topology_payload: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    *,
    baseline: Mapping[str, Any] | None = None,
    runtime: Any | None = None,
    require_current_contract: bool = False,
) -> None:
    code = "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID"
    contract_runtime = runtime or rt.ContractRuntime()
    combined = {**demand_payload, **line_payload, **topology_payload}
    try:
        contract_runtime.validate_definition(
            combined,
            "storyline-architecture.schema.json",
            "upstreamPhasePayload",
        )
    except Exception as error:
        _fail(code, f"upstream phase payload schema invalid: {error}")
    baseline_model = baseline or {
        "control_registry": [
            {"id": item["id"], "hardness": item["hardness"]}
            for item in controls
        ]
    }
    try:
        _validate_model(
            combined,
            baseline_model,
            controls,
            contract_runtime,
            require_source_sequences=(
                "source_sequence_realizations" in line_payload
            ),
            require_current_contract=require_current_contract,
            upstream_only=True,
        )
    except S1Error as error:
        _fail(code, str(error))


def _candidate_from_phases(
    session: Mapping[str, Any],
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    model: dict[str, Any] = {
        "schema_version": "2.0",
        "skill": "novel-storyline-architecture-designer",
        "stage": "S1",
        "run_id": session["run_id"],
        "status": "ready",
        "input_gate": copy.deepcopy(session["input_gate"]),
        "source_artifacts": copy.deepcopy(session["source_artifacts"]),
    }
    for payload in payloads:
        model.update(copy.deepcopy(dict(payload)))
    return model


def _validate_phase_semantics(
    root: Path,
    *,
    phase: str,
    body: Mapping[str, Any],
    session: Mapping[str, Any],
    baseline: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    runtime: Any,
) -> None:
    prior = {
        item: _sealed_phase_payload(root, item, session)
        for item in PHASES[: PHASES.index(phase)]
    }
    if phase == "demand-scan":
        _validate_demand_phase_semantics(body["storyline_demands"], controls)
    elif phase == "line-design":
        _validate_line_phase_semantics(
            prior["demand-scan"],
            body,
            controls,
            require_source_sequences=(
                session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
            ),
            require_current_contract=(
                session.get("contract_revision") == CURRENT_CONTRACT_REVISION
            ),
        )
        _validate_line_claim_review(root, body, session, controls)
    elif phase == "topology-and-consistency":
        _validate_topology_phase_semantics(
            prior["demand-scan"],
            prior["line-design"],
            body,
            controls,
            baseline=baseline,
            runtime=runtime,
            require_current_contract=(
                session.get("contract_revision") == CURRENT_CONTRACT_REVISION
            ),
        )
        if session.get("semantic_review_protocol") == TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL:
            _validate_topology_semantic_review(
                root,
                prior["line-design"],
                body,
                session,
                controls,
            )
    elif phase == "downstream-requirements":
        candidate = _candidate_from_phases(
            session,
            [
                prior["demand-scan"],
                prior["line-design"],
                prior["topology-and-consistency"],
                body,
            ],
        )
        try:
            _validate_model(
                candidate,
                baseline,
                controls,
                runtime,
                expected_gate=session["input_gate"],
                expected_sources=session["source_artifacts"],
                require_source_sequences=(
                    session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
                ),
                require_current_contract=(
                    session.get("contract_revision") == CURRENT_CONTRACT_REVISION
                ),
            )
        except S1Error as error:
            _fail("S1_DOWNSTREAM_PHASE_SEMANTIC_INVALID", str(error))
    else:
        model = body.get("model")
        if not isinstance(model, Mapping):
            _fail("S1_FINAL_PHASE_SEMANTIC_INVALID", "final model is missing")
        for previous_phase, payload in prior.items():
            if previous_phase == "final-storyline-model":
                continue
            for field in _phase_fields_for_session(session, previous_phase):
                if model.get(field) != payload[field]:
                    _fail(
                        "S1_FINAL_PHASE_SEMANTIC_INVALID",
                        f"model.{field} differs from sealed {previous_phase}",
                    )
        try:
            _validate_model(
                model,
                baseline,
                controls,
                runtime,
                expected_gate=session["input_gate"],
                expected_sources=session["source_artifacts"],
                require_source_sequences=(
                    session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
                ),
                require_current_contract=(
                    session.get("contract_revision") == CURRENT_CONTRACT_REVISION
                ),
            )
        except S1Error as error:
            _fail("S1_FINAL_PHASE_SEMANTIC_INVALID", str(error))


def submit_s1_phase(
    workspace: str | Path,
    *,
    baseline_package: str | Path,
    input_gate: Any,
    phase: str,
    payload: Mapping[str, Any],
    runtime: Any | None = None,
) -> dict[str, str]:
    """Accept the next Agent-authored phase and extend the forward hash chain."""

    root = Path(workspace).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    session, baseline, controls = _validated_session(
        root,
        baseline_package=baseline_package,
        input_gate=input_gate,
        runtime=contract_runtime,
        full_validation=False,
    )
    completed = [
        item for item in PHASES
        if (root / "generation-evidence" / f"{PHASES.index(item)+1:02d}-{item}.json").is_file()
    ]
    if len(completed) >= len(PHASES):
        _fail("S1_PHASE_ORDER_INVALID", "all phases are already sealed")
    if phase not in PHASES or phase != PHASES[len(completed)]:
        _fail("S1_PHASE_ORDER_INVALID", f"next phase is {PHASES[len(completed)]}")
    body = copy.deepcopy(dict(payload))
    phase_fields = _phase_fields_for_session(session, phase)
    if set(body) != set(phase_fields):
        _fail(
            "S1_PHASE_PAYLOAD_INVALID",
            f"{phase} must contain exactly {list(phase_fields)}",
        )
    _validate_agent_text(body, path=f"$.{phase}")
    _validate_phase_semantics(
        root,
        phase=phase,
        body=body,
        session=session,
        baseline=baseline,
        controls=controls,
        runtime=contract_runtime,
    )
    previous = None
    if completed:
        previous_path = (
            root
            / "generation-evidence"
            / f"{len(completed):02d}-{completed[-1]}.json"
        )
        previous = rt.sha256_file(previous_path)
    evidence = {
        "schema_version": "2.0",
        "run_id": session["run_id"],
        "stage": "S1",
        "session_id": session["session_id"],
        "thread_id": session["thread_id"],
        "phase": phase,
        "sequence": len(completed) + 1,
        "previous_evidence_sha256": previous,
        "input_gate": session["input_gate"],
        "state_before": session["state_before"],
        "input_manifest": session["input_manifest"],
        "control_bindings": session["control_bindings"],
        "payload": body,
        "payload_sha256": rt.canonical_sha256(body),
    }
    path = (
        root
        / "generation-evidence"
        / f"{len(completed)+1:02d}-{phase}.json"
    )
    _write(path, evidence)
    return rt.artifact_reference(path, root=root)


def _validate_phase_chain(
    evidence_root: Path,
    *,
    session: Mapping[str, Any],
    model: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
) -> list[Path]:
    paths: list[Path] = []
    previous = None
    for index, phase in enumerate(PHASES, 1):
        path = evidence_root / f"{index:02d}-{phase}.json"
        evidence = _read(path, "S1_EVIDENCE_MISSING")
        payload = evidence.get("payload")
        if not isinstance(payload, Mapping):
            _fail("S1_EVIDENCE_INVALID", f"{phase} payload is missing")
        expected_common = {
            "schema_version": "2.0",
            "run_id": session["run_id"],
            "stage": "S1",
            "session_id": session["session_id"],
            "thread_id": session["thread_id"],
            "phase": phase,
            "sequence": index,
            "previous_evidence_sha256": previous,
            "input_gate": session["input_gate"],
            "state_before": session["state_before"],
            "input_manifest": session["input_manifest"],
            "control_bindings": session["control_bindings"],
            "payload": dict(payload),
            "payload_sha256": rt.canonical_sha256(payload),
        }
        phase_fields = _phase_fields_for_session(session, phase)
        if evidence != expected_common or set(payload) != set(phase_fields):
            _fail("S1_EVIDENCE_INVALID", f"{phase} evidence binding is invalid")
        if phase == "line-design":
            _validate_line_claim_review(
                evidence_root.parent,
                payload,
                session,
                controls,
            )
        if (
            phase == "topology-and-consistency"
            and session.get("semantic_review_protocol")
            == TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL
        ):
            _validate_topology_semantic_review(
                evidence_root.parent,
                {
                    field: model[field]
                    for field in _phase_fields_for_session(session, "line-design")
                },
                payload,
                session,
                controls,
            )
        if phase == "final-storyline-model":
            if payload["model"] != model:
                _fail("S1_EVIDENCE_MODEL_MISMATCH", "final evidence differs from model")
        else:
            for field in phase_fields:
                if payload[field] != model[field]:
                    _fail(
                        "S1_EVIDENCE_MODEL_MISMATCH",
                        f"{phase}.{field} differs from final model",
                    )
        previous = rt.sha256_file(path)
        paths.append(path)
    return paths


def _validation(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "S1",
        "verdict": "ready",
        "checks": [
            "schema", "b0-binding", "demand-exact-cover", "single-main",
            "causal-structural-closure", "optional-association-boundary",
            "connection-state-index-binding", "reciprocal-incidence",
            "state-causal-dag", "line-presentation-order",
            "six-dimension-consistency",
            "line-claim-span-authority", "independent-line-claim-review",
            "dimension-witness-whitelists", "downstream-requirements",
            "story-obligation-source-cover", "story-obligation-anchor-binding",
            "story-obligation-dag", "story-obligation-information-window",
            "global-first-milestone-semantics",
            "relation-realization-distinctness",
            "independent-topology-information-review",
            "topology-review-exact-cover",
            "open-items", "derivations",
        ],
        "errors": [],
    }


def validate_s1_package(
    package_root: str | Path,
    *,
    runtime: Any | None = None,
    require_completion: bool = True,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    model = _read(root / "storyline-architecture.json", "S1_MODEL_MISSING")
    manifest = _read(root / "package-manifest.json", "S1_MANIFEST_INVALID")
    stored = _read(root / "validation.json", "S1_VALIDATION_MISSING")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("S1_MANIFEST_INVALID", str(error))
    copied_b0 = root / "sources" / "B0"
    try:
        rt.validate_baseline_package(copied_b0, runtime=contract_runtime)
    except Exception as error:
        _fail("S1_B0_INVALID", str(error))
    baseline = _read(copied_b0 / "author-control-baseline.json", "S1_B0_INVALID")
    if baseline["run_id"] != model["run_id"]:
        _fail("S1_RUN_ID_MISMATCH", "S1 and B0 run IDs differ")
    gate = _read(root / "input-gate.json", "S1_GATE_MISSING")
    try:
        contract_runtime.validate(gate, "input-gate.schema.json")
    except Exception as error:
        _fail("S1_GATE_INVALID", str(error))
    stored_gate_reference = {
        "path": model["input_gate"]["path"],
        "sha256": rt.sha256_file(root / "input-gate.json"),
    }
    if not stored_gate_reference["path"].endswith("/input-gate.json"):
        _fail("S1_GATE_REFERENCE_MISMATCH", "input gate path is not package-qualified")
    expected_b0_reference = _b0_reference(
        copied_b0,
        gate.get("baseline_completion", {}),
        baseline=baseline,
        runtime=contract_runtime,
    )
    if (
        gate.get("target_stage") != "S1"
        or gate.get("run_id") != model["run_id"]
        or gate.get("baseline_completion") != expected_b0_reference
        or gate.get("upstream_completions") != []
    ):
        _fail("S1_GATE_INVALID", "gate does not bind the exact S1/B0 topology")
    expected_sources = [
        rt.artifact_reference(copied_b0 / name, root=root)
        for name in (
            "author-control-baseline.json",
            "package-manifest.json",
            "stage-completion.json",
        )
    ]
    controls = _controls(copied_b0, baseline)
    session = _read(root / "generation-session.json", "S1_SESSION_INVALID")
    review_protocol = session.get("semantic_review_protocol")
    if review_protocol not in {None, TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL}:
        _fail("S1_SESSION_INVALID", "unknown semantic review protocol")
    requires_topology_review = review_protocol == TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL
    line_review_protocol = session.get("line_review_protocol")
    if line_review_protocol not in {None, LINE_REVIEW_PROTOCOL}:
        _fail("S1_SESSION_INVALID", "unknown line review protocol")
    requires_source_sequences = line_review_protocol == LINE_REVIEW_PROTOCOL
    contract_revision = session.get("contract_revision")
    if contract_revision not in {None, CURRENT_CONTRACT_REVISION}:
        _fail("S1_SESSION_INVALID", "unknown S1 contract revision")
    requires_current_contract = contract_revision == CURRENT_CONTRACT_REVISION
    _validate_model(
        model,
        baseline,
        controls,
        contract_runtime,
        expected_gate=stored_gate_reference,
        expected_sources=expected_sources,
        enforce_semantic_gate=requires_topology_review,
        require_source_sequences=requires_source_sequences,
        require_current_contract=requires_current_contract,
    )
    if manifest["artifact_roles"]["canonical"] != rt.artifact_reference(
        root / "storyline-architecture.json", root=root
    ):
        _fail("S1_MANIFEST_INVALID", "canonical role does not bind the model")
    execution = _read(root / "execution-record.json", "S1_EXECUTION_INVALID")
    if (
        execution.get("input_gate") != stored_gate_reference
        or execution.get("input_manifest") != expected_b0_reference
        or execution.get("output_sha256") != rt.canonical_sha256(model)
    ):
        _fail("S1_EXECUTION_INVALID", "execution lineage does not bind gate/B0/model")
    session_thread = session.get("thread_id")
    if not isinstance(session_thread, str) or not session_thread.strip():
        _fail("S1_SESSION_INVALID", "session thread is missing")
    expected_session = {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "S1",
        "session_id": (
            "S1-"
            + rt.canonical_sha256(
                [session_thread, stored_gate_reference, expected_b0_reference]
            )[:20]
        ),
        "thread_id": session_thread,
        "input_gate": stored_gate_reference,
        "state_before": gate.get("run_state"),
        "input_manifest": expected_b0_reference,
        "source_artifacts": expected_sources,
        "control_bindings": _control_bindings(controls),
        "phases": list(PHASES),
    }
    if requires_topology_review:
        expected_session["semantic_review_protocol"] = (
            TOPOLOGY_SEMANTIC_REVIEW_PROTOCOL
        )
    if requires_source_sequences:
        expected_session["line_review_protocol"] = LINE_REVIEW_PROTOCOL
    if requires_current_contract:
        expected_session["contract_revision"] = CURRENT_CONTRACT_REVISION
    if session != expected_session:
        _fail("S1_SESSION_INVALID", "session lineage differs from package inputs")
    if execution.get("session_id") != session["session_id"]:
        _fail("S1_SESSION_INVALID", "execution does not bind the frozen session")
    evidence_paths = _validate_phase_chain(
        root / "generation-evidence",
        session=session,
        model=model,
        controls=controls,
    )
    line_payload = _sealed_phase_payload(root, "line-design", session)
    review_request_path, line_review_path = _validate_line_claim_review(
        root,
        line_payload,
        session,
        controls,
    )
    topology_review_paths: tuple[Path, Path] | None = None
    if requires_topology_review:
        topology_payload = _sealed_phase_payload(
            root, "topology-and-consistency", session
        )
        topology_review_paths = _validate_topology_semantic_review(
            root, line_payload, topology_payload, session, controls
        )
    evidence_index = _read(
        root / "generation-evidence-index.json", "S1_EVIDENCE_INVALID"
    )
    expected_evidence_refs = [
        rt.artifact_reference(path, root=root) for path in evidence_paths
    ]
    expected_evidence_index = {
        "schema_version": "2.0",
        "run_id": model["run_id"],
        "stage": "S1",
        "session_id": session["session_id"],
        "phases": list(PHASES),
        "evidence": expected_evidence_refs,
        "line_claim_review_request": rt.artifact_reference(
            review_request_path, root=root
        ),
        "line_claim_review": rt.artifact_reference(line_review_path, root=root),
    }
    if topology_review_paths is not None:
        expected_evidence_index["topology_semantic_review_request"] = (
            rt.artifact_reference(topology_review_paths[0], root=root)
        )
        expected_evidence_index["topology_semantic_review"] = (
            rt.artifact_reference(topology_review_paths[1], root=root)
        )
    if evidence_index != expected_evidence_index:
        _fail("S1_EVIDENCE_INVALID", "evidence index differs from phase chain")
    try:
        stage_identity.validate_stage_catalog(
            stage="S1",
            records=execution.get("implementation_catalog"),
            package_root=root,
            current_paths=_implementation_paths(),
            verify_artifact_reference=rt.verify_artifact_reference,
            sha256_file=rt.sha256_file,
        )
    except stage_identity.StageImplementationIdentityError as error:
        _fail("S1_IMPLEMENTATION_STALE", str(error))
    if require_completion:
        completion_path = root / "stage-completion.json"
        completion = _read(completion_path, "S1_COMPLETION_MISSING")
        try:
            contract_runtime.validate(completion, "stage-completion.schema.json")
        except Exception as error:
            _fail("S1_COMPLETION_INVALID", str(error))
        manifest_ref = completion.get("manifest")
        manifest_path = (
            manifest_ref.get("path") if isinstance(manifest_ref, Mapping) else ""
        )
        logical_prefix = PurePosixPath(manifest_path).parent.as_posix()
        expected_manifest = {
            "path": _logical(logical_prefix, "package-manifest.json"),
            "sha256": rt.sha256_file(root / "package-manifest.json"),
        }
        expected_validation = {
            "path": _logical(logical_prefix, "validation.json"),
            "sha256": rt.sha256_file(root / "validation.json"),
        }
        if (
            not (
                logical_prefix == "S1"
                or logical_prefix.startswith("S1/")
            )
            or completion.get("run_id") != model["run_id"]
            or completion.get("stage") != "S1"
            or completion.get("status") != "ready"
            or completion.get("session_id") != session.get("session_id")
            or completion.get("manifest") != expected_manifest
            or completion.get("validation") != expected_validation
            or completion.get("input_gate") != stored_gate_reference
            or completion.get("state_before") != gate.get("run_state")
            or completion.get("previous_stage_completions")
            != gate.get("upstream_completions")
            or completion.get("return_binding") != gate.get("return_binding")
        ):
            _fail(
                "S1_COMPLETION_BINDING_MISMATCH",
                "completion does not exactly bind gate/state/B0/package/session",
            )
    expected = _validation(model["run_id"])
    if stored != expected:
        _fail("S1_VALIDATION_STALE", "stored validation differs from read-only validation")
    return expected


def run_s1(
    package_root: str | Path,
    *,
    baseline_package: str | Path,
    coordinator: Any,
    input_gate: Any,
    controlled_workspace: str | Path,
    logical_package_path: str = "S1",
    next_state_path: str,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> S1RunReceipt:
    destination = Path(package_root).resolve()
    b0_root = Path(baseline_package).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    if _path_lexists(destination):
        _fail("S1_OUTPUT_EXISTS", str(destination))
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread_id:
        _fail("S1_THREAD_REQUIRED", "CODEX_THREAD_ID is required")
    workspace = Path(controlled_workspace).resolve()
    session, baseline, controls = _validated_session(
        workspace,
        baseline_package=b0_root,
        input_gate=input_gate,
        runtime=contract_runtime,
    )
    final_evidence = _read(
        workspace
        / "generation-evidence"
        / f"{len(PHASES):02d}-{PHASES[-1]}.json",
        "S1_EVIDENCE_MISSING",
    )
    final_payload = final_evidence.get("payload")
    if not isinstance(final_payload, Mapping) or not isinstance(
        final_payload.get("model"), Mapping
    ):
        _fail("S1_EVIDENCE_INVALID", "final model evidence is missing")
    model = copy.deepcopy(dict(final_payload["model"]))
    _validate_phase_chain(
        workspace / "generation-evidence",
        session=session,
        model=model,
        controls=controls,
    )
    _validate_model(
        model,
        baseline,
        controls,
        contract_runtime,
        expected_gate=input_gate.reference,
        expected_sources=session["source_artifacts"],
        require_source_sequences=(
            session.get("line_review_protocol") == LINE_REVIEW_PROTOCOL
        ),
        require_current_contract=(
            session.get("contract_revision") == CURRENT_CONTRACT_REVISION
        ),
    )
    expected_b0_ref = session["input_manifest"]
    line_payload = _sealed_phase_payload(workspace, "line-design", session)
    review_request_path, line_review_path = _validate_line_claim_review(
        workspace,
        line_payload,
        session,
        controls,
    )
    topology_payload = _sealed_phase_payload(
        workspace, "topology-and-consistency", session
    )
    topology_request_path, topology_review_path = (
        _validate_topology_semantic_review(
            workspace, line_payload, topology_payload, session, controls
        )
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = _create_package_staging(destination)
    try:
        shutil.copytree(b0_root, staging / "sources" / "B0")
        _write(staging / "input-gate.json", input_gate.data)
        source_artifacts = [
            rt.artifact_reference(staging / "sources" / "B0" / name, root=staging)
            for name in (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ]
        if source_artifacts != session["source_artifacts"]:
            _fail("S1_B0_SOURCE_MISMATCH", "staged B0 differs from frozen session")
        _write(staging / "storyline-architecture.json", model)

        evidence_refs = []
        for index, phase in enumerate(PHASES, 1):
            source = (
                workspace / "generation-evidence" / f"{index:02d}-{phase}.json"
            )
            path = staging / "generation-evidence" / source.name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, path)
            reference = rt.artifact_reference(path, root=staging)
            evidence_refs.append(reference)
        evidence_index = {
            "schema_version": "2.0", "run_id": baseline["run_id"], "stage": "S1",
            "session_id": session["session_id"],
            "phases": list(PHASES), "evidence": evidence_refs,
        }
        review_refs: list[dict[str, str]] = []
        for source in (review_request_path, line_review_path):
            target = staging / source.relative_to(workspace)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            review_refs.append(rt.artifact_reference(target, root=staging))
        evidence_index["line_claim_review_request"] = review_refs[0]
        evidence_index["line_claim_review"] = review_refs[1]
        topology_review_refs: list[dict[str, str]] = []
        for source in (topology_request_path, topology_review_path):
            target = staging / source.relative_to(workspace)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            topology_review_refs.append(rt.artifact_reference(target, root=staging))
        evidence_index["topology_semantic_review_request"] = (
            topology_review_refs[0]
        )
        evidence_index["topology_semantic_review"] = topology_review_refs[1]
        _write(staging / "generation-evidence-index.json", evidence_index)
        _write(staging / "generation-session.json", session)
        session_id = session["session_id"]
        implementation_refs = []
        implementation_catalog = []
        for identity, source in sorted(_implementation_paths().items()):
            target = staging / "implementation" / identity
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            reference = rt.artifact_reference(target, root=staging)
            implementation_refs.append(reference)
            implementation_catalog.append({"identity": identity, "artifact": reference})
        execution = {
            "schema_version": "2.0", "run_id": baseline["run_id"], "stage": "S1",
            "operation": "controlled-storyline-architecture-generation",
            "session_id": session_id, "input_gate": copy.deepcopy(input_gate.reference),
            "input_manifest": expected_b0_ref,
            "implementation": implementation_refs,
            "implementation_catalog": implementation_catalog,
            "output_sha256": rt.canonical_sha256(model),
        }
        _write(staging / "execution-record.json", execution)
        (staging / "storyline-preview.md").write_text(
            "# Storyline architecture\n\n"
            + "\n".join(
                f"- **{line['id']} ({line['type']})**: {line['responsibility']}"
                for line in model["storylines"]
            )
            + "\n",
            encoding="utf-8",
            newline="",
        )
        validation = _validation(baseline["run_id"])
        _write(staging / "validation.json", validation)
        files = [
            rt.artifact_reference(path, root=staging)
            for path in sorted(staging.rglob("*"), key=lambda x: x.as_posix())
            if path.is_file()
        ]
        by_path = {x["path"]: x for x in files}
        manifest = {
            "schema_version": "2.0", "run_id": baseline["run_id"], "stage": "S1",
            "package_profile": "generated-model", "verdict": "ready", "files": files,
            "artifact_roles": {
                "canonical": by_path["storyline-architecture.json"],
                "generation_session": by_path["generation-session.json"],
                "generation_evidence_index": by_path["generation-evidence-index.json"],
                "execution_record": by_path["execution-record.json"],
                "preview": by_path["storyline-preview.md"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation_refs,
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write(staging / "package-manifest.json", manifest)
        validate_s1_package(
            staging, runtime=contract_runtime, require_completion=False
        )
        completion_data = {
            "schema_version": "2.0", "run_id": baseline["run_id"], "stage": "S1",
            "status": "ready", "session_id": session_id,
            "manifest": {
                "path": _logical(logical_package_path, "package-manifest.json"),
                "sha256": rt.sha256_file(staging / "package-manifest.json"),
            },
            "validation": {
                "path": _logical(logical_package_path, "validation.json"),
                "sha256": rt.sha256_file(staging / "validation.json"),
            },
            "input_gate": copy.deepcopy(input_gate.reference),
            "state_before": copy.deepcopy(input_gate.data["run_state"]),
            "previous_stage_completions": [],
            "return_binding": copy.deepcopy(input_gate.data["return_binding"]),
        }
        contract_runtime.validate(completion_data, "stage-completion.schema.json")
        sealed = rt.seal_stage_document(
            completion_data, "S1", _logical(logical_package_path, "stage-completion.json")
        )
        _write(staging / "stage-completion.json", sealed.data)
        validate_s1_package(staging, runtime=contract_runtime)
        transition = coordinator.accept_stage_completion(
            gate=input_gate,
            completion=sealed,
            next_state_path=next_state_path,
            active_return_request=active_return_request,
        )
        _publish_package_staging(staging, destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return S1RunReceipt(
        package_root=destination,
        model=copy.deepcopy(model),
        manifest=copy.deepcopy(manifest),
        completion=sealed,
        transition=transition,
    )


__all__ = [
    "S1Error",
    "S1RunReceipt",
    "inspect_s1_line_claims",
    "run_s1",
    "start_s1_session",
    "start_s1_line_claim_review",
    "start_s1_topology_semantic_review",
    "submit_s1_line_claim_review",
    "submit_s1_topology_semantic_review",
    "submit_s1_phase",
    "validate_s1_package",
]
