#!/usr/bin/env python3
"""Deterministic two-phase legacy interview migration primitives."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

STAGES = ("I0", "I1", "I2", "I3", "I4", "I5")
ALL_INPUTS = STAGES + ("V1", "V2", "approval")
PREFIXES = {"I0": "INT-", "I1": "SUB-", "I2": "WLD-", "I3": "CHR-", "I4": "CAU-", "I5": "NAR-"}
HARDNESS = {"author_locked", "autonomous_owned", "downstream_freedom", "author_open"}
PROHIBITED_HEADINGS = {"元信息", "交付信息", "metadata", "meta information", "delivery information"}
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]+$")
CONTROL_RE = re.compile(r"^[A-Z][A-Z0-9._-]+$")
FACT_RE = re.compile(r"^FACT-[A-Za-z0-9._-]+$")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


class MigrationError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(lines: list[str], start: int, end: int) -> str:
    return hashlib.sha256("\n".join(lines[start - 1:end]).encode("utf-8")).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise MigrationError(f"{label} must be a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise MigrationError(f"{label} fields mismatch; missing={missing}, extra={extra}")


def rel_ref(base_file: Path, target: Path) -> dict[str, str]:
    return {"path": Path(os.path.relpath(target, base_file.parent)).as_posix(), "sha256": sha256(target)}


def resolve_declared(plan_path: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise MigrationError(f"{label} must be a non-empty path")
    raw = Path(value)
    candidates = [raw.resolve()] if raw.is_absolute() else [(plan_path.parent / raw).resolve(), (Path.cwd() / raw).resolve()]
    found: list[Path] = []
    for candidate in candidates:
        if candidate.is_file() and candidate not in found:
            found.append(candidate)
    if len(found) != 1:
        raise MigrationError(f"{label} must resolve to exactly one existing file; resolved={found}")
    return found[0]


def resolve_ref(owner: Path, value: Any, label: str) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise MigrationError(f"{label} must be an exact artifact reference")
    if not isinstance(value.get("path"), str) or not value["path"] or not isinstance(value.get("sha256"), str) or SHA_RE.fullmatch(value["sha256"]) is None:
        raise MigrationError(f"{label} path/hash is invalid")
    target = (owner.parent / value["path"]).resolve()
    if not target.is_file() or sha256(target) != value["sha256"]:
        raise MigrationError(f"{label} is missing or changed")
    return target


def validate_plan(plan_path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    plan = load_json(plan_path, "projection plan")
    exact_keys(plan, {"schema_version", "migration_id", "run_id", "inputs", "stage_projections", "fact_candidates"}, "projection plan")
    if plan.get("schema_version") != "1.0" or not isinstance(plan.get("migration_id"), str) or ID_RE.fullmatch(plan["migration_id"]) is None:
        raise MigrationError("projection plan schema_version/migration_id is invalid")
    if not isinstance(plan.get("run_id"), str) or not plan["run_id"].strip():
        raise MigrationError("projection plan run_id is missing")
    inputs = plan.get("inputs")
    if not isinstance(inputs, dict):
        raise MigrationError("projection plan inputs must be an object")
    exact_keys(inputs, set(ALL_INPUTS), "projection plan inputs")
    paths = {key: resolve_declared(plan_path, inputs[key], f"inputs.{key}") for key in ALL_INPUTS}
    return plan, paths


def validate_legacy_chain(plan: dict[str, Any], paths: dict[str, Path]) -> tuple[dict[str, dict[str, Any]], dict[str, Path], Path]:
    run_id = plan["run_id"]
    packets: dict[str, dict[str, Any]] = {}
    artifacts: dict[str, Path] = {}
    for stage in STAGES + ("V1", "V2"):
        packet = load_json(paths[stage], f"{stage} completion")
        if packet.get("harness") != "novel-conception-interview" or packet.get("run_id") != run_id or packet.get("stage") != stage or packet.get("status") != "ready":
            raise MigrationError(f"{stage} completion identity/status does not match the plan")
        artifact_name = packet.get("design_artifact")
        artifact_hash = packet.get("design_artifact_sha256")
        if not isinstance(artifact_name, str) or not artifact_name or not isinstance(artifact_hash, str) or SHA_RE.fullmatch(artifact_hash) is None:
            raise MigrationError(f"{stage} completion lacks a hash-bound design artifact")
        artifact = (paths[stage].parent / artifact_name).resolve()
        if not artifact.is_file() or sha256(artifact) != artifact_hash:
            raise MigrationError(f"{stage} design artifact is missing or changed")
        packets[stage] = packet
        artifacts[stage] = artifact

    # V1 must consume exactly the selected I0-I5 completions.
    v1_refs = packets["V1"].get("input_completions")
    if not isinstance(v1_refs, list) or len(v1_refs) != 6:
        raise MigrationError("V1 must consume exactly six interview completions")
    seen: dict[str, Path] = {}
    for index, ref in enumerate(v1_refs):
        target = resolve_ref(paths["V1"], ref, f"V1.input_completions[{index}]")
        packet = load_json(target, "V1 input completion")
        stage = packet.get("stage")
        if stage not in STAGES or stage in seen:
            raise MigrationError("V1 inputs must uniquely cover I0-I5")
        seen[stage] = target
    if set(seen) != set(STAGES) or any(sha256(seen[s]) != sha256(paths[s]) for s in STAGES):
        raise MigrationError("V1 does not bind the selected I0-I5 completion set")

    v2_refs = packets["V2"].get("input_completions")
    if not isinstance(v2_refs, list) or len(v2_refs) != 1 or sha256(resolve_ref(paths["V2"], v2_refs[0], "V2.input_completions[0]")) != sha256(paths["V1"]):
        raise MigrationError("V2 does not bind the selected V1 completion")

    approval = load_json(paths["approval"], "legacy V2 approval")
    if approval.get("harness") != "novel-conception-interview" or approval.get("run_id") != run_id or approval.get("approval_scope") != "V2" or approval.get("decision") != "approved":
        raise MigrationError("legacy approval is not an approved V2 record for this run")
    brief = resolve_ref(paths["approval"], approval.get("review_brief"), "legacy approval review_brief")
    if sha256(brief) != sha256(artifacts["V2"]):
        raise MigrationError("legacy approval does not bind the selected V2 brief")

    state_ref = packets["V2"].get("run_state")
    state = resolve_ref(paths["V2"], state_ref, "V2.run_state")
    return packets, artifacts, state


def markdown_sections(path: Path) -> tuple[list[str], dict[str, list[tuple[int, int, int]]]]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise MigrationError(f"Markdown source is not readable UTF-8: {path}: {exc}") from exc
    headings: list[tuple[int, int, str]] = []
    for number, line in enumerate(lines, 1):
        match = HEADING_RE.match(line)
        if match:
            headings.append((number, len(match.group(1)), match.group(2).strip()))
    sections: dict[str, list[tuple[int, int, int]]] = {}
    for index, (start, level, title) in enumerate(headings):
        end = len(lines)
        for next_start, next_level, _ in headings[index + 1:]:
            if next_level <= level:
                end = next_start - 1
                break
        sections.setdefault(title, []).append((start, end, level))
    return lines, sections


def validate_fact(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise MigrationError(f"fact_candidates[{index}] must be an object")
    status = item.get("proposed_status")
    common = {"id", "proposed_status", "claim"}
    expected = {
        "not_applicable": common | {"rationale"},
        "open": common | {"blocking", "allowed_handling", "rationale"},
        "adopted": common | {"research_package", "adoption_record", "allowed_use", "fiction_boundary"},
    }
    if status not in expected or set(item) != expected[status]:
        raise MigrationError(f"fact_candidates[{index}] fields do not match proposed_status {status!r}")
    if not isinstance(item.get("id"), str) or FACT_RE.fullmatch(item["id"]) is None:
        raise MigrationError(f"fact_candidates[{index}].id is invalid")
    if not isinstance(item.get("claim"), str) or not item["claim"].strip():
        raise MigrationError(f"fact_candidates[{index}].claim is empty")
    if status in {"not_applicable", "open"} and (not isinstance(item.get("rationale"), str) or not item["rationale"].strip()):
        raise MigrationError(f"fact_candidates[{index}].rationale is empty")
    if status == "open" and (item.get("blocking") is not False or item.get("allowed_handling") != "preserve_open"):
        raise MigrationError(f"fact_candidates[{index}] open fact must be non-blocking/preserve_open")
    if status == "adopted":
        for key in ("allowed_use", "fiction_boundary"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise MigrationError(f"fact_candidates[{index}].{key} is empty")
    return dict(item)


def validate_selections(plan: dict[str, Any], artifacts: dict[str, Path]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    projections = plan.get("stage_projections")
    if not isinstance(projections, list) or len(projections) != 6:
        raise MigrationError("stage_projections must contain exactly six stage objects")
    result: dict[str, dict[str, Any]] = {}
    all_ids: list[str] = []
    for stage_index, stage_plan in enumerate(projections):
        if not isinstance(stage_plan, dict):
            raise MigrationError(f"stage_projections[{stage_index}] must be an object")
        exact_keys(stage_plan, {"stage", "sections"}, f"stage_projections[{stage_index}]")
        stage = stage_plan.get("stage")
        if stage not in STAGES or stage in result:
            raise MigrationError("stage_projections must uniquely cover I0-I5")
        sections_plan = stage_plan.get("sections")
        if not isinstance(sections_plan, list) or not sections_plan:
            raise MigrationError(f"{stage} sections must be non-empty")
        lines, available = markdown_sections(artifacts[stage])
        controls: list[dict[str, Any]] = []
        bindings: list[dict[str, Any]] = []
        ranges: list[tuple[int, int, str]] = []
        for index, selected in enumerate(sections_plan):
            if not isinstance(selected, dict):
                raise MigrationError(f"{stage}.sections[{index}] must be an object")
            exact_keys(selected, {"control_id", "hardness", "heading"}, f"{stage}.sections[{index}]")
            control_id, hardness, heading = selected.get("control_id"), selected.get("hardness"), selected.get("heading")
            if not isinstance(control_id, str) or CONTROL_RE.fullmatch(control_id) is None or not control_id.startswith(PREFIXES[stage]):
                raise MigrationError(f"{stage}.sections[{index}].control_id has the wrong prefix or syntax")
            if hardness not in HARDNESS:
                raise MigrationError(f"{stage}.sections[{index}].hardness is invalid")
            if not isinstance(heading, str) or not heading.strip() or heading.strip().casefold() in {x.casefold() for x in PROHIBITED_HEADINGS}:
                raise MigrationError(f"{stage}.sections[{index}].heading is empty or metadata")
            matches = available.get(heading.strip(), [])
            if len(matches) != 1:
                raise MigrationError(f"{stage} heading {heading!r} must occur exactly once; found {len(matches)}")
            start, end, level = matches[0]
            if level not in {2, 3}:
                raise MigrationError(f"{stage} heading {heading!r} must be H2 or H3")
            body = "\n".join(lines[start:end]).strip()
            if not body:
                raise MigrationError(f"{stage} heading {heading!r} has an empty section body")
            for prior_start, prior_end, prior_id in ranges:
                if max(start, prior_start) <= min(end, prior_end):
                    raise MigrationError(f"{stage} selections {prior_id} and {control_id} overlap")
            ranges.append((start, end, control_id))
            controls.append({"id": control_id, "hardness": hardness, "heading": heading.strip(), "value": body})
            bindings.append({"control_id": control_id, "ranges": [{"start_line": start, "end_line": end, "text_sha256": text_sha(lines, start, end)}]})
            all_ids.append(control_id)
        result[stage] = {"controls": controls, "evidence_bindings": bindings}
    if set(result) != set(STAGES) or len(all_ids) != len(set(all_ids)):
        raise MigrationError("stage projections must cover I0-I5 and use globally unique control IDs")
    facts_raw = plan.get("fact_candidates")
    if not isinstance(facts_raw, list) or not facts_raw:
        raise MigrationError("fact_candidates must be non-empty")
    facts = [validate_fact(item, index) for index, item in enumerate(facts_raw)]
    fact_ids = [item["id"] for item in facts]
    if len(fact_ids) != len(set(fact_ids)):
        raise MigrationError("fact candidate IDs must be unique")
    return result, facts


def prepare_new_output(output: Path) -> Path:
    output = output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise MigrationError(f"output directory must not exist or must be empty: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    if output.exists():
        output.rmdir()
    return temp


def publish_temp(temp: Path, output: Path) -> None:
    temp.replace(output.resolve())


def snapshot(temp: Path, source: Path, relative: str, role: str, inventory_entries: list[dict[str, Any]]) -> Path:
    destination = temp / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if sha256(destination) != sha256(source):
        raise MigrationError(f"snapshot copy hash mismatch: {source}")
    inventory_entries.append({
        "role": role,
        "original_path": str(source.resolve()),
        "snapshot": {"path": relative, "sha256": sha256(destination)},
        "size_bytes": destination.stat().st_size,
    })
    return destination


def build_candidate(plan_path: Path, output: Path) -> Path:
    plan_path = plan_path.resolve()
    plan, input_paths = validate_plan(plan_path)
    packets, artifacts, state_path = validate_legacy_chain(plan, input_paths)
    selections, facts = validate_selections(plan, artifacts)
    temp = prepare_new_output(output)
    try:
        entries: list[dict[str, Any]] = []
        completion_snapshots: dict[str, Path] = {}
        artifact_snapshots: dict[str, Path] = {}
        for stage in STAGES + ("V1", "V2"):
            completion_snapshots[stage] = snapshot(temp, input_paths[stage], f"snapshots/{stage}/stage-completion.json", f"{stage}_completion", entries)
            suffix = artifacts[stage].suffix.lower() or ".bin"
            artifact_snapshots[stage] = snapshot(temp, artifacts[stage], f"snapshots/{stage}/design-artifact{suffix}", f"{stage}_design_artifact", entries)
        state_snapshot = snapshot(temp, state_path, "snapshots/source-interview-state.json", "source_interview_state", entries)
        approval_snapshot = snapshot(temp, input_paths["approval"], "snapshots/V2/author-approval.json", "v2_author_approval", entries)
        plan_snapshot = snapshot(temp, plan_path, "snapshots/projection-plan.json", "projection_plan", entries)

        adopted_refs: dict[str, dict[str, dict[str, str]]] = {}
        for fact in facts:
            if fact["proposed_status"] == "adopted":
                adopted_refs[fact["id"]] = {}
                for role in ("research_package", "adoption_record"):
                    source = resolve_declared(plan_path, fact[role], f"{fact['id']}.{role}")
                    safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", fact["id"])
                    target = snapshot(temp, source, f"snapshots/facts/{safe_id}/{role}{source.suffix}", f"{fact['id']}_{role}", entries)
                    adopted_refs[fact["id"]][role] = rel_ref(temp / "fact-candidates.json", target)

        inventory_path = temp / "source-inventory.json"
        inventory = {
            "schema_version": "1.0",
            "migration_id": plan["migration_id"],
            "source_run_id": plan["run_id"],
            "source_interview_state": rel_ref(inventory_path, state_snapshot),
            "design_completions": {stage: rel_ref(inventory_path, completion_snapshots[stage]) for stage in STAGES},
            "v1_completion": rel_ref(inventory_path, completion_snapshots["V1"]),
            "v2_completion": rel_ref(inventory_path, completion_snapshots["V2"]),
            "v2_author_approval": rel_ref(inventory_path, approval_snapshot),
            "source_artifacts": {stage: rel_ref(inventory_path, artifact_snapshots[stage]) for stage in STAGES + ("V1", "V2")},
            "additional_evidence": [rel_ref(inventory_path, plan_snapshot)],
            "entries": entries,
        }
        write_json(inventory_path, inventory)

        projection_paths: dict[str, Path] = {}
        for stage in STAGES:
            path = temp / "control-projections" / f"{stage}-control-projection.json"
            data = {
                "schema_version": "1.0",
                "harness": "novel-conception-interview",
                "migration_id": plan["migration_id"],
                "run_id": plan["run_id"],
                "stage": stage,
                "session_id": packets[stage].get("session_id"),
                "status": "waiting_author",
                "source_artifact": rel_ref(path, artifact_snapshots[stage]),
                "controls": selections[stage]["controls"],
                "evidence_bindings": selections[stage]["evidence_bindings"],
            }
            write_json(path, data)
            projection_paths[stage] = path

        fact_path = temp / "fact-candidates.json"
        candidate_facts: list[dict[str, Any]] = []
        for fact in facts:
            value = {"id": fact["id"], "status": fact["proposed_status"], "claim": fact["claim"]}
            for key, item in fact.items():
                if key not in {"id", "proposed_status", "claim", "research_package", "adoption_record"}:
                    value[key] = item
            if fact["proposed_status"] == "adopted":
                value.update(adopted_refs[fact["id"]])
            candidate_facts.append(value)
        write_json(fact_path, {
            "schema_version": "1.0", "harness": "novel-conception-interview", "migration_id": plan["migration_id"],
            "run_id": plan["run_id"], "stage": "V1", "status": "waiting_author", "fact_dependencies": candidate_facts,
        })

        controls_flat = [control for stage in STAGES for control in selections[stage]["controls"]]
        review_json_path = temp / "migration-review.json"
        review = {
            "schema_version": "1.0", "kind": "interview-b0-migration-review", "migration_id": plan["migration_id"],
            "source_run_id": plan["run_id"], "status": "waiting_author",
            "notice": "These are exact-section extraction and fact-classification candidates. The earlier V2 approval does not approve this migration.",
            "controls": [{"stage": stage, **control} for stage in STAGES for control in selections[stage]["controls"]],
            "facts": candidate_facts,
            "required_decision": {"decision": "approved", "author_role": "author", "control_ids": [c["id"] for c in controls_flat], "fact_ids": [f["id"] for f in candidate_facts]},
        }
        write_json(review_json_path, review)
        review_html_path = temp / "migration-review.html"
        review_html_path.write_text(render_review(review), encoding="utf-8")

        validation_path = temp / "validation.json"
        validation = {
            "schema_version": "1.0", "kind": "interview-b0-migration-validation", "migration_id": plan["migration_id"],
            "source_run_id": plan["run_id"], "status": "waiting_author", "verdict": "pass",
            "checks": ["legacy_chain_hash_closed", "exact_headings_unique", "selected_ranges_non_overlapping", "metadata_excluded", "candidate_not_b0_ready", "fresh_author_decision_required"],
        }
        write_json(validation_path, validation)
        manifest_path = temp / "candidate-manifest.json"
        manifest = {
            "schema_version": "1.0", "kind": "interview-b0-migration-candidate", "migration_id": plan["migration_id"],
            "source_run_id": plan["run_id"], "status": "waiting_author",
            "source_inventory": rel_ref(manifest_path, inventory_path),
            "control_projections": {stage: rel_ref(manifest_path, projection_paths[stage]) for stage in STAGES},
            "fact_candidates": rel_ref(manifest_path, fact_path),
            "migration_review_json": rel_ref(manifest_path, review_json_path),
            "migration_review_html": rel_ref(manifest_path, review_html_path),
            "validation": rel_ref(manifest_path, validation_path),
        }
        write_json(manifest_path, manifest)
        validate_candidate_dir(temp)
        publish_temp(temp, output)
        return output.resolve() / "candidate-manifest.json"
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def render_review(review: dict[str, Any]) -> str:
    controls = []
    for item in review["controls"]:
        controls.append(f"<article><h3>{html.escape(item['id'])} · {html.escape(item['heading'])}</h3><p><b>{html.escape(item['stage'])}</b> · {html.escape(item['hardness'])}</p><pre>{html.escape(str(item['value']))}</pre></article>")
    facts = []
    for item in review["facts"]:
        facts.append(f"<article><h3>{html.escape(item['id'])}</h3><p><b>{html.escape(item['status'])}</b></p><p>{html.escape(item['claim'])}</p></article>")
    return """<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>访谈兼容迁移评审</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:32px;color:#172033;background:#f4f7fb}header,article{background:white;border:1px solid #d9e2ef;border-radius:12px;padding:18px;margin:14px 0}h1{margin-top:0}pre{white-space:pre-wrap;line-height:1.55;background:#f7f9fc;padding:12px;border-radius:8px}.warning{color:#8a3b12;font-weight:700}</style></head><body>""" + f"<header><h1>访谈 → B0 兼容迁移评审</h1><p>{html.escape(review['migration_id'])} · 源运行 {html.escape(review['source_run_id'])}</p><p class=\"warning\">等待作者逐项批准。旧 V2 批准不等于本次迁移批准。</p></header><h2>控制项（{len(controls)}）</h2>{''.join(controls)}<h2>事实依赖候选（{len(facts)}）</h2>{''.join(facts)}</body></html>"


def validate_ref_map(owner: Path, mapping: Any, required: tuple[str, ...], label: str) -> dict[str, Path]:
    if not isinstance(mapping, dict) or set(mapping) != set(required):
        raise MigrationError(f"{label} must exactly cover {required}")
    return {key: resolve_ref(owner, mapping[key], f"{label}.{key}") for key in required}


def validate_source_inventory(path: Path, migration_id: str, run_id: str) -> None:
    data = load_json(path, "source inventory")
    expected = {
        "schema_version", "migration_id", "source_run_id", "source_interview_state",
        "design_completions", "v1_completion", "v2_completion", "v2_author_approval",
        "source_artifacts", "additional_evidence", "entries",
    }
    exact_keys(data, expected, "source inventory")
    if data.get("schema_version") != "1.0" or data.get("migration_id") != migration_id or data.get("source_run_id") != run_id:
        raise MigrationError("source inventory identity does not match candidate")
    state_path = resolve_ref(path, data.get("source_interview_state"), "inventory source_interview_state")
    completion_paths = validate_ref_map(path, data.get("design_completions"), STAGES, "inventory design_completions")
    v1_path = resolve_ref(path, data.get("v1_completion"), "inventory v1_completion")
    v2_path = resolve_ref(path, data.get("v2_completion"), "inventory v2_completion")
    approval_path = resolve_ref(path, data.get("v2_author_approval"), "inventory v2_author_approval")
    artifact_paths = validate_ref_map(path, data.get("source_artifacts"), STAGES + ("V1", "V2"), "inventory source_artifacts")
    evidence = data.get("additional_evidence")
    if not isinstance(evidence, list) or not evidence:
        raise MigrationError("inventory additional_evidence must be non-empty")
    evidence_paths = [resolve_ref(path, ref, f"inventory additional_evidence[{index}]") for index, ref in enumerate(evidence)]
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise MigrationError("inventory entries must be non-empty")
    entry_refs: list[tuple[str, str]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"role", "original_path", "snapshot", "size_bytes"}:
            raise MigrationError(f"inventory entries[{index}] fields are invalid")
        target = resolve_ref(path, entry.get("snapshot"), f"inventory entries[{index}].snapshot")
        if not isinstance(entry.get("role"), str) or not entry["role"] or not isinstance(entry.get("original_path"), str) or not entry["original_path"] or entry.get("size_bytes") != target.stat().st_size:
            raise MigrationError(f"inventory entries[{index}] metadata is invalid")
        entry_refs.append((entry["snapshot"]["path"], entry["snapshot"]["sha256"]))
    if len(entry_refs) != len(set(entry_refs)):
        raise MigrationError("inventory entries contain duplicate snapshot references")
    authoritative_refs = [data["source_interview_state"], data["v1_completion"], data["v2_completion"], data["v2_author_approval"]]
    authoritative_refs += list(data["design_completions"].values()) + list(data["source_artifacts"].values()) + list(data["additional_evidence"])
    if not {(item["path"], item["sha256"]) for item in authoritative_refs}.issubset(set(entry_refs)):
        raise MigrationError("inventory entries do not cover all authoritative snapshot references")

    # Replay the source chain using embedded hashes, not the now-relocated legacy paths.
    completions = {stage: load_json(completion_paths[stage], f"inventory {stage} completion") for stage in STAGES}
    for stage, packet in completions.items():
        if packet.get("harness") != "novel-conception-interview" or packet.get("run_id") != run_id or packet.get("stage") != stage or packet.get("status") != "ready" or packet.get("design_artifact_sha256") != sha256(artifact_paths[stage]):
            raise MigrationError(f"inventory {stage} completion identity/design hash is invalid")
    v1 = load_json(v1_path, "inventory V1 completion")
    v2 = load_json(v2_path, "inventory V2 completion")
    approval = load_json(approval_path, "inventory V2 approval")
    if v1.get("harness") != "novel-conception-interview" or v1.get("run_id") != run_id or v1.get("stage") != "V1" or v1.get("status") != "ready" or v1.get("design_artifact_sha256") != sha256(artifact_paths["V1"]):
        raise MigrationError("inventory V1 completion identity/design hash is invalid")
    v1_inputs = v1.get("input_completions")
    if not isinstance(v1_inputs, list) or len(v1_inputs) != 6 or {item.get("sha256") for item in v1_inputs if isinstance(item, dict)} != {sha256(completion_paths[stage]) for stage in STAGES}:
        raise MigrationError("inventory V1 does not hash-bind exactly the six selected completions")
    if v2.get("harness") != "novel-conception-interview" or v2.get("run_id") != run_id or v2.get("stage") != "V2" or v2.get("status") != "ready" or v2.get("design_artifact_sha256") != sha256(artifact_paths["V2"]):
        raise MigrationError("inventory V2 completion identity/design hash is invalid")
    v2_inputs = v2.get("input_completions")
    if not isinstance(v2_inputs, list) or len(v2_inputs) != 1 or not isinstance(v2_inputs[0], dict) or v2_inputs[0].get("sha256") != sha256(v1_path) or not isinstance(v2.get("run_state"), dict) or v2["run_state"].get("sha256") != sha256(state_path):
        raise MigrationError("inventory V2 does not hash-bind V1 and the source state")
    if approval.get("harness") != "novel-conception-interview" or approval.get("run_id") != run_id or approval.get("approval_scope") != "V2" or approval.get("decision") != "approved" or not isinstance(approval.get("review_brief"), dict) or approval["review_brief"].get("sha256") != sha256(artifact_paths["V2"]):
        raise MigrationError("inventory legacy approval does not hash-bind the V2 brief")


def validate_candidate_dir(directory: Path) -> dict[str, Any]:
    manifest_path = directory.resolve() / "candidate-manifest.json"
    manifest = load_json(manifest_path, "candidate manifest")
    expected = {"schema_version", "kind", "migration_id", "source_run_id", "status", "source_inventory", "control_projections", "fact_candidates", "migration_review_json", "migration_review_html", "validation"}
    exact_keys(manifest, expected, "candidate manifest")
    if manifest.get("schema_version") != "1.0" or manifest.get("kind") != "interview-b0-migration-candidate" or manifest.get("status") != "waiting_author":
        raise MigrationError("candidate manifest identity/status is invalid")
    inventory_path = resolve_ref(manifest_path, manifest.get("source_inventory"), "candidate manifest source_inventory")
    validate_source_inventory(inventory_path, manifest["migration_id"], manifest["source_run_id"])
    for key in ("fact_candidates", "migration_review_json", "migration_review_html", "validation"):
        resolve_ref(manifest_path, manifest.get(key), f"candidate manifest {key}")
    projection_paths = validate_ref_map(manifest_path, manifest.get("control_projections"), STAGES, "candidate control_projections")
    ids: list[str] = []
    for stage, path in projection_paths.items():
        data = load_json(path, f"candidate {stage} projection")
        if data.get("status") != "waiting_author" or data.get("migration_id") != manifest.get("migration_id") or data.get("run_id") != manifest.get("source_run_id") or data.get("stage") != stage:
            raise MigrationError(f"candidate {stage} projection identity/status is invalid")
        resolve_ref(path, data.get("source_artifact"), f"candidate {stage} source_artifact")
        controls = data.get("controls")
        bindings = data.get("evidence_bindings")
        if not isinstance(controls, list) or not controls or not isinstance(bindings, list):
            raise MigrationError(f"candidate {stage} controls/bindings are invalid")
        source = resolve_ref(path, data.get("source_artifact"), f"candidate {stage} source_artifact")
        lines = source.read_text(encoding="utf-8-sig").splitlines()
        stage_ids: list[str] = []
        for item in controls:
            if not isinstance(item, dict) or set(item) != {"id", "hardness", "heading", "value"} or not isinstance(item.get("id"), str) or not item["id"].startswith(PREFIXES[stage]) or item.get("hardness") not in HARDNESS or not item.get("heading") or item.get("value") in (None, "", [], {}):
                raise MigrationError(f"candidate {stage} control is invalid")
            stage_ids.append(item["id"])
        bound: list[str] = []
        for binding in bindings:
            if not isinstance(binding, dict) or set(binding) != {"control_id", "ranges"} or not isinstance(binding.get("ranges"), list) or not binding["ranges"]:
                raise MigrationError(f"candidate {stage} evidence binding is invalid")
            bound.append(binding.get("control_id"))
            for value in binding["ranges"]:
                if not isinstance(value, dict) or set(value) != {"start_line", "end_line", "text_sha256"}:
                    raise MigrationError(f"candidate {stage} evidence range is invalid")
                start, end = value.get("start_line"), value.get("end_line")
                if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start or end > len(lines) or text_sha(lines, start, end) != value.get("text_sha256"):
                    raise MigrationError(f"candidate {stage} evidence range hash is invalid")
        if len(stage_ids) != len(controls) or set(stage_ids) != set(bound) or len(bound) != len(set(bound)):
            raise MigrationError(f"candidate {stage} evidence does not exactly cover controls")
        ids.extend(stage_ids)
    if len(ids) != len(set(ids)):
        raise MigrationError("candidate control IDs are not globally unique")
    fact_path = resolve_ref(manifest_path, manifest["fact_candidates"], "candidate fact_candidates")
    facts = load_json(fact_path, "candidate facts")
    if facts.get("status") != "waiting_author" or facts.get("migration_id") != manifest.get("migration_id") or facts.get("run_id") != manifest.get("source_run_id") or not isinstance(facts.get("fact_dependencies"), list) or not facts["fact_dependencies"]:
        raise MigrationError("candidate facts identity/status is invalid")
    fact_ids = [x.get("id") for x in facts["fact_dependencies"] if isinstance(x, dict)]
    if len(fact_ids) != len(facts["fact_dependencies"]) or len(fact_ids) != len(set(fact_ids)):
        raise MigrationError("candidate fact IDs are invalid or duplicated")
    validate_fact_dependencies(fact_path, facts["fact_dependencies"])
    review_path = resolve_ref(manifest_path, manifest["migration_review_json"], "candidate migration_review_json")
    review = load_json(review_path, "migration review")
    if review.get("status") != "waiting_author" or review.get("migration_id") != manifest["migration_id"] or review.get("source_run_id") != manifest["source_run_id"]:
        raise MigrationError("migration review identity/status is invalid")
    reviewed_controls = review.get("controls")
    reviewed_facts = review.get("facts")
    expected_controls = []
    for stage in STAGES:
        projection = load_json(projection_paths[stage], f"candidate {stage}")
        expected_controls.extend({"stage": stage, **item} for item in projection["controls"])
    if reviewed_controls != expected_controls or reviewed_facts != facts["fact_dependencies"]:
        raise MigrationError("migration review does not exactly present the candidate controls/facts")
    required = review.get("required_decision")
    if not isinstance(required, dict) or required.get("decision") != "approved" or required.get("author_role") != "author" or required.get("control_ids") != ids or required.get("fact_ids") != fact_ids:
        raise MigrationError("migration review required_decision does not exactly cover candidates")
    html_path = resolve_ref(manifest_path, manifest["migration_review_html"], "candidate migration_review_html")
    if html_path.read_text(encoding="utf-8") != render_review(review):
        raise MigrationError("migration review HTML is not the exact rendering of review JSON")
    validation_path = resolve_ref(manifest_path, manifest["validation"], "candidate validation")
    validation = load_json(validation_path, "candidate validation")
    if validation.get("verdict") != "pass" or validation.get("status") != "waiting_author" or validation.get("migration_id") != manifest["migration_id"] or validation.get("source_run_id") != manifest["source_run_id"]:
        raise MigrationError("candidate validation is not a matching pass")
    return {"manifest": manifest, "manifest_path": manifest_path, "control_paths": projection_paths, "fact_path": fact_path, "control_ids": ids, "fact_ids": fact_ids}


def canonical_projection(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: candidate[key] for key in ("schema_version", "harness", "run_id", "stage", "session_id", "source_artifact", "controls", "evidence_bindings")} | {"status": "ready"}


def canonical_fact_register(candidate: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "1.0", "harness": "novel-conception-interview", "run_id": candidate["run_id"], "stage": "V1", "status": "ready", "fact_dependencies": candidate["fact_dependencies"]}


def validate_author_decision(path: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    decision = load_json(path, "author decision")
    expected = {"schema_version", "kind", "migration_id", "source_run_id", "candidate_manifest_sha256", "decision", "author_role", "control_decisions", "fact_decisions"}
    exact_keys(decision, expected, "author decision")
    if decision.get("schema_version") != "1.0" or decision.get("kind") != "interview-b0-migration-author-decision" or decision.get("migration_id") != candidate["manifest"]["migration_id"] or decision.get("source_run_id") != candidate["manifest"]["source_run_id"]:
        raise MigrationError("author decision identity does not match candidate")
    if decision.get("candidate_manifest_sha256") != sha256(candidate["manifest_path"]) or decision.get("decision") != "approved" or decision.get("author_role") != "author":
        raise MigrationError("author decision is stale or is not an explicit author approval")
    for key, expected_ids in (("control_decisions", candidate["control_ids"]), ("fact_decisions", candidate["fact_ids"])):
        values = decision.get(key)
        if not isinstance(values, list) or any(not isinstance(x, dict) or set(x) != {"id", "decision"} or x.get("decision") != "accept" for x in values):
            raise MigrationError(f"author decision {key} has invalid entries")
        ids = [x["id"] for x in values]
        if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
            raise MigrationError(f"author decision {key} must exactly cover all candidate IDs")
    return decision


def validate_process_decision(path: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    decision = load_json(path, "author process decision")
    expected = {
        "schema_version", "kind", "migration_id", "source_run_id",
        "candidate_manifest_sha256", "decision", "author_role",
        "human_review_scope", "statement",
    }
    exact_keys(decision, expected, "author process decision")
    if (
        decision.get("schema_version") != "1.0"
        or decision.get("kind")
        != "interview-b0-migration-author-process-decision"
        or decision.get("migration_id") != candidate["manifest"]["migration_id"]
        or decision.get("source_run_id")
        != candidate["manifest"]["source_run_id"]
        or decision.get("candidate_manifest_sha256")
        != sha256(candidate["manifest_path"])
        or decision.get("decision")
        != "delegate_internal_compatibility_conversion"
        or decision.get("author_role") != "author"
        or decision.get("human_review_scope")
        != ["world", "story", "characters", "fragments"]
        or not isinstance(decision.get("statement"), str)
        or not decision["statement"].strip()
    ):
        raise MigrationError(
            "author process decision does not delegate compatibility conversion "
            "and reserve the four-part H1 review"
        )
    return decision


def validate_compatibility_decision(
    path: Path, candidate: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    document = load_json(path, "compatibility decision")
    kind = document.get("kind")
    if kind == "interview-b0-migration-author-decision":
        return validate_author_decision(path, candidate), "item_approval"
    if kind == "interview-b0-migration-author-process-decision":
        return validate_process_decision(path, candidate), "delegated_internal"
    raise MigrationError("compatibility decision kind is unsupported")


def validate_control_projection(path: Path) -> None:
    data = load_json(path, "final control projection")
    expected = {"schema_version", "harness", "run_id", "stage", "session_id", "status", "source_artifact", "controls", "evidence_bindings"}
    exact_keys(data, expected, "final control projection")
    stage = data.get("stage")
    if data.get("schema_version") != "1.0" or data.get("harness") != "novel-conception-interview" or stage not in STAGES or data.get("status") != "ready":
        raise MigrationError("final control projection identity/status is invalid")
    source = resolve_ref(path, data.get("source_artifact"), "final control projection source")
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    controls = data.get("controls")
    bindings = data.get("evidence_bindings")
    if not isinstance(controls, list) or not controls or not isinstance(bindings, list):
        raise MigrationError("final projection controls/bindings are invalid")
    ids: list[str] = []
    for item in controls:
        if not isinstance(item, dict) or set(item) != {"id", "hardness", "heading", "value"} or not isinstance(item.get("id"), str) or not item["id"].startswith(PREFIXES[stage]) or item.get("hardness") not in HARDNESS or not item.get("heading") or item.get("value") in (None, "", [], {}):
            raise MigrationError("final projection control is invalid")
        ids.append(item["id"])
    bound: list[str] = []
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"control_id", "ranges"} or not isinstance(binding.get("ranges"), list) or not binding["ranges"]:
            raise MigrationError("final projection evidence binding is invalid")
        bound.append(binding.get("control_id"))
        for value in binding["ranges"]:
            if not isinstance(value, dict) or set(value) != {"start_line", "end_line", "text_sha256"}:
                raise MigrationError("final projection evidence range is invalid")
            start, end = value.get("start_line"), value.get("end_line")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines) or text_sha(lines, start, end) != value.get("text_sha256"):
                raise MigrationError("final projection evidence range hash is invalid")
    if len(ids) != len(set(ids)) or set(ids) != set(bound) or len(bound) != len(set(bound)):
        raise MigrationError("final projection evidence must exactly cover unique controls")


def validate_fact_dependencies(path: Path, dependencies: Any) -> None:
    if not isinstance(dependencies, list) or not dependencies:
        raise MigrationError("fact dependencies must be non-empty")
    ids: list[str] = []
    for index, item in enumerate(dependencies):
        if not isinstance(item, dict):
            raise MigrationError(f"final fact[{index}] is invalid")
        status = item.get("status")
        fields = {
            "not_applicable": {"id", "status", "claim", "rationale"},
            "open": {"id", "status", "claim", "blocking", "allowed_handling", "rationale"},
            "adopted": {"id", "status", "claim", "research_package", "adoption_record", "allowed_use", "fiction_boundary"},
        }
        if status not in fields or set(item) != fields[status] or not isinstance(item.get("id"), str) or FACT_RE.fullmatch(item["id"]) is None or not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise MigrationError(f"final fact[{index}] fields are invalid")
        if status == "open" and (item.get("blocking") is not False or item.get("allowed_handling") != "preserve_open"):
            raise MigrationError(f"final fact[{index}] open handling is invalid")
        if status in {"open", "not_applicable"} and not isinstance(item.get("rationale"), str):
            raise MigrationError(f"final fact[{index}] rationale is invalid")
        if status == "adopted":
            resolve_ref(path, item.get("research_package"), f"final fact[{index}].research_package")
            resolve_ref(path, item.get("adoption_record"), f"final fact[{index}].adoption_record")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise MigrationError("final fact IDs are duplicated")


def validate_fact_register(path: Path) -> None:
    data = load_json(path, "final fact register")
    exact_keys(data, {"schema_version", "harness", "run_id", "stage", "status", "fact_dependencies"}, "final fact register")
    if data.get("schema_version") != "1.0" or data.get("harness") != "novel-conception-interview" or data.get("stage") != "V1" or data.get("status") != "ready":
        raise MigrationError("final fact register identity/status is invalid")
    validate_fact_dependencies(path, data.get("fact_dependencies"))


def finalize_candidate(candidate_dir: Path, decision_path: Path, output: Path) -> Path:
    candidate = validate_candidate_dir(candidate_dir)
    _, decision_mode = validate_compatibility_decision(
        decision_path.resolve(), candidate
    )
    temp = prepare_new_output(output)
    try:
        shutil.copytree(candidate_dir.resolve(), temp / "candidate")
        shutil.copytree(candidate_dir.resolve() / "snapshots", temp / "snapshots")
        shutil.copyfile(candidate_dir.resolve() / "source-inventory.json", temp / "source-inventory.json")
        decision_copy = temp / "compatibility-decision.json"
        shutil.copyfile(decision_path.resolve(), decision_copy)
        projection_paths: dict[str, Path] = {}
        for stage in STAGES:
            source = load_json(candidate["control_paths"][stage], f"candidate {stage}")
            path = temp / "control-projections" / f"{stage}-control-projection.json"
            canonical = canonical_projection(source)
            # Rebase source reference from the equivalent candidate layout.
            canonical["source_artifact"] = rel_ref(path, temp / "snapshots" / stage / f"design-artifact{Path(resolve_ref(candidate['control_paths'][stage], source['source_artifact'], 'source')).suffix}")
            write_json(path, canonical)
            validate_control_projection(path)
            projection_paths[stage] = path
        fact_candidate = load_json(candidate["fact_path"], "candidate fact register")
        fact_path = temp / "fact-dependency-register.json"
        final_facts = canonical_fact_register(fact_candidate)
        for item in final_facts["fact_dependencies"]:
            if item["status"] == "adopted":
                for role in ("research_package", "adoption_record"):
                    candidate_asset = resolve_ref(candidate["fact_path"], item[role], f"candidate fact {item['id']} {role}")
                    relative_asset = candidate_asset.relative_to(candidate_dir.resolve())
                    item[role] = rel_ref(fact_path, temp / relative_asset)
        write_json(fact_path, final_facts)
        validate_fact_register(fact_path)
        validation_path = temp / "validation.json"
        decision_checks = (
            ["author_decision_fresh", "all_controls_accepted", "all_facts_accepted"]
            if decision_mode == "item_approval"
            else [
                "author_process_delegation_fresh",
                "compatibility_conversion_machine_owned",
                "human_review_reserved_for_four_part_h1",
            ]
        )
        validation = {
            "schema_version": "1.0", "kind": "interview-b0-migration-validation", "migration_id": candidate["manifest"]["migration_id"],
            "source_run_id": candidate["manifest"]["source_run_id"], "status": "finalized", "verdict": "pass",
            "checks": ["candidate_hashes_valid", *decision_checks, "canonical_projections_valid", "canonical_fact_register_valid", "no_handoff_emitted"],
        }
        write_json(validation_path, validation)
        manifest_path = temp / "migration-finalization.json"
        manifest = {
            "schema_version": "1.0", "kind": "interview-b0-migration-finalization", "migration_id": candidate["manifest"]["migration_id"],
            "source_run_id": candidate["manifest"]["source_run_id"], "status": "finalized",
            "candidate_manifest": rel_ref(manifest_path, temp / "candidate" / "candidate-manifest.json"),
            "compatibility_decision": rel_ref(manifest_path, decision_copy),
            "source_inventory": rel_ref(manifest_path, temp / "source-inventory.json"),
            "control_projections": {stage: rel_ref(manifest_path, projection_paths[stage]) for stage in STAGES},
            "fact_dependency_register": rel_ref(manifest_path, fact_path),
            "validation": rel_ref(manifest_path, validation_path),
        }
        write_json(manifest_path, manifest)
        validate_final_dir(temp)
        publish_temp(temp, output)
        return output.resolve() / "migration-finalization.json"
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def validate_final_dir(directory: Path) -> dict[str, Any]:
    root = directory.resolve()
    manifest_path = root / "migration-finalization.json"
    manifest = load_json(manifest_path, "migration finalization")
    expected = {"schema_version", "kind", "migration_id", "source_run_id", "status", "candidate_manifest", "compatibility_decision", "source_inventory", "control_projections", "fact_dependency_register", "validation"}
    exact_keys(manifest, expected, "migration finalization")
    if manifest.get("schema_version") != "1.0" or manifest.get("kind") != "interview-b0-migration-finalization" or manifest.get("status") != "finalized":
        raise MigrationError("migration finalization identity/status is invalid")
    candidate_manifest_path = resolve_ref(manifest_path, manifest.get("candidate_manifest"), "finalization candidate_manifest")
    decision_path = resolve_ref(manifest_path, manifest.get("compatibility_decision"), "finalization compatibility_decision")
    inventory_path = resolve_ref(manifest_path, manifest.get("source_inventory"), "finalization source_inventory")
    validate_source_inventory(inventory_path, manifest["migration_id"], manifest["source_run_id"])
    validation_path = resolve_ref(manifest_path, manifest.get("validation"), "finalization validation")
    validation = load_json(validation_path, "final validation")
    if validation.get("verdict") != "pass" or validation.get("status") != "finalized" or validation.get("migration_id") != manifest.get("migration_id"):
        raise MigrationError("final validation is not a matching pass")
    projections = validate_ref_map(manifest_path, manifest.get("control_projections"), STAGES, "finalization control_projections")
    all_ids: list[str] = []
    for stage, path in projections.items():
        validate_control_projection(path)
        data = load_json(path, f"final {stage} projection")
        if data.get("run_id") != manifest.get("source_run_id") or data.get("stage") != stage:
            raise MigrationError(f"final {stage} projection does not match finalization")
        all_ids.extend(x["id"] for x in data["controls"])
    fact_path = resolve_ref(manifest_path, manifest.get("fact_dependency_register"), "finalization fact register")
    validate_fact_register(fact_path)
    facts = load_json(fact_path, "final fact register")
    if facts.get("run_id") != manifest.get("source_run_id"):
        raise MigrationError("final fact register run_id does not match finalization")
    embedded_candidate = validate_candidate_dir(candidate_manifest_path.parent)
    if embedded_candidate["manifest_path"] != candidate_manifest_path:
        raise MigrationError("finalization candidate manifest is not the embedded candidate package root")
    final_fact_ids = [x["id"] for x in facts["fact_dependencies"]]
    if set(all_ids) != set(embedded_candidate["control_ids"]) or set(final_fact_ids) != set(embedded_candidate["fact_ids"]):
        raise MigrationError("final artifacts do not preserve the approved candidate ID sets")
    validate_compatibility_decision(decision_path, embedded_candidate)
    return manifest
