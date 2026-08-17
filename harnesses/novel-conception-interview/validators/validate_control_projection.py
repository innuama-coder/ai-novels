#!/usr/bin/env python3
"""Validate one hash-bound, B0-compatible interview control projection."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

PREFIXES = {"I0": "INT-", "I1": "SUB-", "I2": "WLD-", "I3": "CHR-", "I4": "CAU-", "I5": "NAR-"}
HARDNESS = {"author_locked", "autonomous_owned", "downstream_freedom", "author_open"}
SHA256 = re.compile(r"^[a-f0-9]{64}$")
TOP_LEVEL_KEYS = {"schema_version", "harness", "run_id", "stage", "session_id", "status", "source_artifact", "controls", "evidence_bindings"}
CONTROL_KEYS = {"id", "hardness", "heading", "value"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_digest(lines: list[str], start: int, end: int) -> str:
    value = "\n".join(lines[start - 1:end])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def section_value(
    lines: list[str], start: int, end: int
) -> tuple[str | None, str, int | None]:
    """Return the Markdown heading text and exact non-blank section body."""

    heading_match = re.fullmatch(r"(#{2,3})\s+(.+?)\s*", lines[start - 1])
    if heading_match is None:
        return None, "", None
    level = len(heading_match.group(1))
    expected_end = len(lines)
    for offset in range(start, len(lines)):
        next_heading = re.match(r"^(#{1,%d})\s+" % level, lines[offset])
        if next_heading is not None:
            expected_end = offset
            break
    body = list(lines[start:end])
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return heading_match.group(2), "\n".join(body), expected_end


def nonempty(value: object) -> bool:
    return value is not None and value not in ("", [], {})


def validate_projection(path: Path) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"control projection is not readable JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["control projection must be an object"]
    if set(data) != TOP_LEVEL_KEYS:
        errors.append("control projection must contain exactly the contracted top-level fields")
    stage = data.get("stage")
    if data.get("schema_version") != "1.0" or data.get("harness") != "novel-conception-interview" or stage not in PREFIXES or data.get("status") != "ready":
        errors.append("control projection identity/status is invalid")
    if not isinstance(data.get("run_id"), str) or not data["run_id"].strip() or not isinstance(data.get("session_id"), str) or not data["session_id"].strip():
        errors.append("control projection run_id/session_id is missing")
    source = data.get("source_artifact")
    source_path: Path | None = None
    lines: list[str] = []
    if not isinstance(source, dict) or set(source) != {"path", "sha256"} or not isinstance(source.get("path"), str) or not source["path"] or not isinstance(source.get("sha256"), str) or SHA256.fullmatch(source["sha256"]) is None:
        errors.append("source_artifact must be an exact hash-bound reference")
    elif Path(source["path"]).is_absolute():
        errors.append("source_artifact.path must be relative to the projection")
    else:
        source_path = (path.parent / source["path"]).resolve()
        if not source_path.is_file() or digest(source_path) != source["sha256"]:
            errors.append("source_artifact is missing or has changed")
        else:
            try:
                lines = source_path.read_text(encoding="utf-8-sig").splitlines()
            except (OSError, UnicodeError) as exc:
                errors.append(f"source_artifact is not readable UTF-8 text: {exc}")
    controls = data.get("controls")
    control_ids: list[str] = []
    if not isinstance(controls, list) or not controls:
        errors.append("controls must be a non-empty array")
    else:
        for index, item in enumerate(controls):
            if not isinstance(item, dict) or set(item) != CONTROL_KEYS:
                errors.append(f"controls[{index}] must contain exactly id/hardness/heading/value")
                continue
            control_id = item.get("id")
            prefix = PREFIXES.get(stage, "")
            if not isinstance(control_id, str) or not control_id.startswith(prefix) or re.fullmatch(r"[A-Z][A-Z0-9._-]+", control_id) is None:
                errors.append(f"controls[{index}].id does not match the {stage} prefix")
            else:
                control_ids.append(control_id)
            if item.get("hardness") not in HARDNESS:
                errors.append(f"controls[{index}].hardness is invalid")
            if not isinstance(item.get("heading"), str) or not item["heading"].strip():
                errors.append(f"controls[{index}].heading is empty")
            if not nonempty(item.get("value")):
                errors.append(f"controls[{index}].value is empty")
        if len(control_ids) != len(set(control_ids)):
            errors.append("control ids must be unique")
    bindings = data.get("evidence_bindings")
    bound_ids: list[str] = []
    if not isinstance(bindings, list) or not bindings:
        errors.append("evidence_bindings must be a non-empty array")
    else:
        for index, binding in enumerate(bindings):
            if not isinstance(binding, dict) or set(binding) != {"control_id", "ranges"}:
                errors.append(f"evidence_bindings[{index}] has invalid fields")
                continue
            control_id = binding.get("control_id")
            if not isinstance(control_id, str) or not control_id:
                errors.append(f"evidence_bindings[{index}].control_id is missing")
            else:
                bound_ids.append(control_id)
            ranges = binding.get("ranges")
            if not isinstance(ranges, list) or len(ranges) != 1:
                errors.append(
                    f"evidence_bindings[{index}].ranges must contain exactly one complete Markdown section"
                )
                continue
            for range_index, item in enumerate(ranges):
                if not isinstance(item, dict) or set(item) != {"start_line", "end_line", "text_sha256"}:
                    errors.append(f"evidence_bindings[{index}].ranges[{range_index}] has invalid fields")
                    continue
                start, end, expected = item.get("start_line"), item.get("end_line"), item.get("text_sha256")
                if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start or end > len(lines):
                    errors.append(f"evidence_bindings[{index}].ranges[{range_index}] is outside the source artifact")
                elif not isinstance(expected, str) or SHA256.fullmatch(expected) is None or text_digest(lines, start, end) != expected:
                    errors.append(f"evidence_bindings[{index}].ranges[{range_index}] text hash does not match")
                elif control_id in control_ids:
                    control = next(
                        item for item in controls if item.get("id") == control_id
                    )
                    source_heading, source_value, expected_end = section_value(
                        lines, start, end
                    )
                    plain_heading = control.get("heading")
                    marked_heading = (
                        f"[{control_id}][{control.get('hardness')}] {plain_heading}"
                    )
                    if source_heading not in {plain_heading, marked_heading}:
                        errors.append(
                            f"evidence_bindings[{index}] heading does not exactly match the control"
                        )
                    if expected_end != end:
                        errors.append(
                            f"evidence_bindings[{index}] range does not cover the complete Markdown section"
                        )
                    if source_value != control.get("value"):
                        errors.append(
                            f"evidence_bindings[{index}] value is not a lossless projection of the bound section"
                        )
    if len(bound_ids) != len(set(bound_ids)):
        errors.append("each control must have exactly one evidence binding")
    if set(bound_ids) != set(control_ids):
        errors.append("evidence bindings must cover exactly the declared controls")
    return data, errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_control_projection.py <control-projection.json>", file=sys.stderr)
        return 2
    data, errors = validate_projection(Path(argv[1]).resolve())
    if errors:
        for error in errors:
            print("FAIL: " + error)
        return 1
    print(f"OK: {data['stage']} control projection is B0-compatible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
