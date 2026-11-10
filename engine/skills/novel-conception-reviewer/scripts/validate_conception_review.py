#!/usr/bin/env python3
"""Validate an R1 conception-review package and write immutable evidence."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from execution_record import verify_record
from render_conception_review import locate_d1, render_outputs


HARNESS = "novel-conception-interview"
AREAS = {
    "intent": "I0",
    "subject": "I1",
    "world": "I2",
    "character": "I3",
    "causality": "I4",
    "narrative": "I5",
}
CROSS_CHECKS = {
    "autonomous_value",
    "gap_closure",
    "promise_scope",
    "world_causality",
    "character_agency",
    "opposition_response",
    "choice_costs",
    "easy_solution",
    "causal_closure",
    "narrative_information",
    "thematic_testing",
    "open_boundaries",
    "development_usability",
}
HANDOFF_TASKS = {
    "promise",
    "autonomous_value",
    "causal_chain",
    "unit_contract",
    "freedom_boundary",
    "drift_detection",
    "easy_solution",
    "scene_plan",
}
DESIGN_REVIEW_DIMENSIONS = {
    "necessity",
    "compatibility",
    "causal_utility",
    "specificity",
    "author_boundary",
    "downstream_freedom",
}
STATUSES = {"ready", "revise", "blocked"}
FINDING_SEVERITIES = {"risk", "revise", "blocked"}
FINDING_OWNERS = {
    "R1",
    "D1",
    "I0",
    "I1",
    "I2",
    "I3",
    "I4",
    "I5",
    "V1",
    "V2",
    "AUTHOR",
}
LOCAL_REVISE_OWNERS = {"D1", "R1"}
CONTROL_STAGE_ARTIFACTS = {
    "I0": "intent-card.md",
    "I1": "subject-definition.md",
    "I2": "world-operating-contract.md",
    "I3": "core-character-design.md",
    "I4": "causal-storyline.md",
    "I5": "narrative-contract.md",
}
CONTROL_STAGES = set(CONTROL_STAGE_ARTIFACTS)
GATE_OWNERS = {"V1", "V2", "D1", "AUTHOR", "R1"}
READY_OUTPUT_FILES = {
    "novel-design-brief.md",
    "conception-review.md",
    "independent-handoff.json",
}
RETURN_OUTPUT_FILES = {
    "return-package.json",
    "next-run-state.json",
}
GENERATED_OUTPUT_FILES = READY_OUTPUT_FILES | RETURN_OUTPUT_FILES
PACKAGE_FILES = {
    "review-data.json",
    "generation-session.json",
    "generation-evidence/01-review-plan.json",
    "generation-evidence/02-semantic-challenges.json",
    "generation-evidence/03-handoff-test.json",
    "generation-evidence/04-final-review.json",
    "execution-record.json",
    *READY_OUTPUT_FILES,
    "validation.json",
}
HARNESS_VALIDATOR = (
    Path(__file__).resolve().parents[3]
    / "harnesses"
    / HARNESS
    / "validators"
    / "validate_stage_completion.py"
)
D1_VALIDATOR = (
    Path(__file__).resolve().parents[2]
    / "novel-development-map-designer"
    / "scripts"
    / "validate_development_map.py"
)
PLACEHOLDER_PATTERN = re.compile(
    r"(?:\b(?:generic|placeholder|todo|tbd|lorem\s+ipsum)\b|"
    r"占位|待补|待定内容|某人|某地)",
    re.IGNORECASE,
)
UNRESOLVED_FAILURE_PATTERN = re.compile(
    r"(?:\b(?:cannot|fails?\s+to|contradicts?|inconsistent|invalid)\b|"
    r"\bnot\s+coherent\b|无法支撑|不能支撑|相互矛盾|存在矛盾|不一致|"
    r"无法形成自洽|审查失败)",
    re.IGNORECASE,
)
GROUNDING_STOPWORDS = {
    "story",
    "world",
    "character",
    "development",
    "control",
    "decision",
    "review",
    "current",
    "complete",
    "system",
    "environment",
    "relationship",
    "declared",
    "indexed",
    "record",
    "formal",
    "completeness",
    "inspection",
    "procedure",
    "passes",
    "currently",
    "reviewed",
    "validated",
    "sufficient",
    "relevant",
    "the",
    "and",
    "for",
    "from",
    "with",
    "without",
    "under",
    "into",
    "that",
    "this",
    "these",
    "those",
    "only",
    "must",
    "can",
    "has",
    "have",
    "are",
    "was",
    "were",
    "故事",
    "世界",
    "人物",
    "角色",
    "开发",
    "构思",
    "关系",
    "系统",
    "环境",
    "信息",
    "定义",
    "边界",
    "选择",
    "变化",
    "因果",
    "单元",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_value_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def business_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(business_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(
            business_text(item)
            for key, item in value.items()
            if key
            not in {
                "id",
                "subject_id",
                "source_controls",
                "development_decisions",
                "unit_ids",
                "storyline_ids",
                "domain",
                "type",
                "status",
                "role",
                "level",
                "area",
            }
        )
    return ""


def normalized_business_text(value: Any) -> str:
    text = business_text(value)
    text = re.sub(
        r"\b(?:[A-Z]{2,}(?:[-_][A-Z0-9]+)+|[A-Z]+\d+[A-Z0-9_-]*)\b",
        " ",
        text,
    )
    text = text.lower()
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def repeated_template_pairs(items: list[Any], threshold: float = 0.90) -> int:
    normalized = [normalized_business_text(item) for item in items]
    pairs = 0
    for left in range(len(normalized)):
        for right in range(left + 1, len(normalized)):
            if not normalized[left] or not normalized[right]:
                continue
            similarity = difflib.SequenceMatcher(
                None,
                normalized[left],
                normalized[right],
                autojunk=False,
            ).ratio()
            if similarity >= threshold:
                pairs += 1
    return pairs


def repeated_field_templates(
    items: list[Any],
    field: str,
    *,
    threshold: float = 0.88,
) -> int:
    """Count majority same-field template reuse without over-policing prose."""
    records = [item for item in items if isinstance(item, dict)]
    if len(records) != len(items) or len(records) < 3:
        return 0
    values = [normalized_business_text(item.get(field)) for item in records]
    total_pairs = len(values) * (len(values) - 1) // 2
    majority = max(2, (total_pairs + 1) // 2)
    compared = 0
    pairs = 0
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            if min(len(values[left]), len(values[right])) < 12:
                continue
            compared += 1
            similarity = difflib.SequenceMatcher(
                None,
                values[left],
                values[right],
                autojunk=False,
            ).ratio()
            if similarity >= threshold:
                pairs += 1
    return pairs if compared >= majority and pairs >= majority else 0


def grounding_tokens(value: Any) -> set[str]:
    text = business_text(value).lower()
    tokens = {
        token
        for token in re.findall(r"[a-z][a-z0-9-]{2,}", text)
        if token not in GROUNDING_STOPWORDS
    }
    for run in re.findall(r"[\u3400-\u9fff]{2,}", text):
        for size in (2, 3, 4):
            tokens.update(
                run[index : index + size]
                for index in range(0, max(0, len(run) - size + 1))
            )
    return {token for token in tokens if token not in GROUNDING_STOPWORDS}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nonempty_string(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(nonempty_string(item) for item in value)
    )


def string_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def reject_extra(
    review: "Review", value: Any, allowed: set[str], label: str
) -> None:
    if not isinstance(value, dict):
        return
    extras = set(value) - allowed
    if extras:
        review.error(
            f"{label} contains unsupported fields: "
            + ", ".join(sorted(str(item) for item in extras))
        )


def reference_identity(base: Path, reference: Any) -> tuple[Path, str] | None:
    if not isinstance(reference, dict):
        return None
    relative = reference.get("path")
    digest = reference.get("sha256")
    if not nonempty_string(relative) or not nonempty_string(digest):
        return None
    relative_path = Path(relative)
    if relative_path.is_absolute():
        return None
    return ((base / relative_path).resolve(), digest.lower())


def run_json_validator(script: Path, target: Path, timeout: int = 60):
    try:
        process = subprocess.run(
            [sys.executable, str(script), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"validator could not run: {exc}"
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError:
        detail = (process.stdout or process.stderr).strip() or "no output"
        return None, f"validator returned invalid JSON: {detail}"
    if process.returncode != 0:
        return result, "validator returned a non-ready verdict"
    return result, None


class Review:
    def __init__(self, package_dir: Path) -> None:
        self.package_dir = package_dir.resolve()
        self.mode = "unknown"
        self.data: dict[str, Any] = {}
        self.errors: list[str] = []
        self.blockers: list[str] = []
        self.evidence: dict[str, Any] = {}
        self.map_data: dict[str, Any] = {}
        self.d1_manifest_path: Path | None = None
        self.revise_findings: set[str] = set()
        self.blocked_findings: set[str] = set()
        self.findings_by_id: dict[str, dict[str, Any]] = {}
        self.return_request_valid = False

    def error(self, message: str) -> None:
        if message not in self.errors:
            self.errors.append(message)

    def block(self, message: str) -> None:
        if message not in self.blockers:
            self.blockers.append(message)

    def result(self) -> dict[str, Any]:
        if self.blockers or self.blocked_findings:
            verdict = "blocked"
        elif self.errors or self.revise_findings:
            verdict = "revise"
        else:
            verdict = "ready"
        return {
            "schema_version": "1.0",
            "harness": HARNESS,
            "run_id": self.data.get("run_id"),
            "stage": "R1",
            "mode": self.mode,
            "verdict": verdict,
            "errors": sorted(self.errors),
            "blockers": sorted(self.blockers),
            "evidence": self.evidence,
        }

    def load_root(self) -> None:
        review_path = self.package_dir / "review-data.json"
        gate_path = self.package_dir / "gate-data.json"
        review_exists = review_path.is_file()
        gate_exists = gate_path.is_file()
        if review_exists and gate_exists:
            self.block(
                "review-data.json and gate-data.json must not coexist"
            )
            return
        if not review_exists and not gate_exists:
            self.block(
                "exactly one of review-data.json or gate-data.json is required"
            )
            return
        if review_exists:
            self.mode = "review"
            path = review_path
        else:
            self.mode = "gate"
            path = gate_path
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            self.block(f"{path.name} is invalid: {exc}")
            return
        if not isinstance(data, dict):
            self.block(f"{path.name} root is not an object")
            return
        self.data = data

    def load_reference(
        self, base: Path, reference: Any, label: str
    ) -> tuple[Path | None, dict[str, Any] | None]:
        identity = reference_identity(base, reference)
        if identity is None:
            self.block(f"{label} is not a hash-bound reference")
            return None, None
        path, expected = identity
        if not path.is_file() or sha256(path) != expected:
            self.block(f"{label} is missing or has changed")
            return None, None
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError):
            self.block(f"{label} is invalid")
            return None, None
        if not isinstance(data, dict):
            self.block(f"{label} root is not an object")
            return None, None
        return path, data

    def validate_ready_completion(self, path: Path, stage: str) -> None:
        try:
            process = subprocess.run(
                [sys.executable, str(HARNESS_VALIDATOR), str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.block(f"{stage} completion validation could not run: {exc}")
            return
        if process.returncode != 0:
            detail = (process.stdout or process.stderr).strip()
            self.block(
                f"{stage} completion failed canonical validation"
                + (f": {detail}" if detail else "")
            )

    def validate_input_gate(self) -> None:
        gate = self.data.get("input_gate")
        if not isinstance(gate, dict):
            self.block("input_gate is missing")
            return
        reject_extra(
            self,
            gate,
            {
                "run_state",
                "v1_completion",
                "v2_completion",
                "d1_completion",
            },
            "input_gate",
        )
        run_id = self.data.get("run_id")
        run_state_path, run_state = self.load_reference(
            self.package_dir, gate.get("run_state"), "run-state"
        )
        if run_state is not None:
            if (
                run_state.get("harness") != HARNESS
                or run_state.get("run_id") != run_id
            ):
                self.block("run-state belongs to another conception run")
            if run_state.get("active_return") is not None:
                self.block("an active return blocks R1")

        completions: dict[str, tuple[Path, dict[str, Any]]] = {}
        for stage, field in (
            ("V1", "v1_completion"),
            ("V2", "v2_completion"),
            ("D1", "d1_completion"),
        ):
            path, completion = self.load_reference(
                self.package_dir, gate.get(field), f"{stage} completion"
            )
            if path is None or completion is None:
                continue
            if (
                completion.get("harness") != HARNESS
                or completion.get("run_id") != run_id
                or completion.get("stage") != stage
                or completion.get("status") != "ready"
            ):
                self.block(f"{stage} completion is not ready for this run")
                continue
            completions[stage] = (path, completion)
            self.validate_ready_completion(path, stage)

        d1 = completions.get("D1")
        if d1 is not None:
            d1_path, d1_completion = d1
            if reference_identity(
                self.package_dir, gate.get("run_state")
            ) != reference_identity(d1_path.parent, d1_completion.get("run_state")):
                self.block("R1 and D1 bind different run-state records")
            upstream: dict[str, tuple[Path, str]] = {}
            for reference in d1_completion.get("input_completions", []):
                identity = reference_identity(d1_path.parent, reference)
                if identity is None:
                    continue
                try:
                    upstream_data = load_json(identity[0])
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(upstream_data, dict):
                    stage = upstream_data.get("stage")
                    if isinstance(stage, str):
                        upstream[stage] = identity
            for stage, field in (
                ("V1", "v1_completion"),
                ("V2", "v2_completion"),
            ):
                if reference_identity(
                    self.package_dir, gate.get(field)
                ) != upstream.get(stage):
                    self.block(f"R1 and D1 bind different {stage} completions")
            try:
                (
                    _d1_completion_path,
                    _d1_completion,
                    manifest_path,
                    manifest,
                    map_data,
                ) = locate_d1(self.package_dir, self.data)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                self.block(f"D1 package cannot be resolved: {exc}")
            else:
                self.d1_manifest_path = manifest_path
                self.map_data = map_data
                if (
                    manifest.get("harness") != HARNESS
                    or manifest.get("run_id") != run_id
                    or manifest.get("stage") != "D1"
                    or manifest.get("verdict") != "ready"
                ):
                    self.block("D1 manifest is not ready for this run")
                validation_path = manifest_path.parent / "validation.json"
                try:
                    stored = load_json(validation_path)
                except (OSError, json.JSONDecodeError):
                    self.block("D1 stored validation is invalid")
                else:
                    canonical, error = run_json_validator(
                        D1_VALIDATOR, manifest_path.parent
                    )
                    if error:
                        self.block(f"D1 canonical revalidation failed: {error}")
                    elif canonical != stored:
                        self.block(
                            "D1 stored validation differs from canonical revalidation"
                        )
                if map_data.get("schema_version") != "4.0":
                    self.block("R1 requires D1 map-data schema 4.0")
        self.evidence["input_gate"] = {
            "run_state": run_state_path.name if run_state_path else None,
            "validated_stages": sorted(completions),
            "d1_schema": self.map_data.get("schema_version"),
        }

    def valid_ids(self) -> tuple[set[str], set[str], set[str], dict[str, dict], set[str]]:
        controls = {
            item.get("id"): item
            for item in self.map_data.get("control_points", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        units = {
            item.get("id")
            for item in self.map_data.get("units", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        obligations = {
            item.get("id")
            for item in self.map_data.get("information_obligations", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        derivations = {
            item.get("id"): item
            for item in self.map_data.get("derivation_claims", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        open_items = {
            item.get("id")
            for item in self.map_data.get("open_items", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        return set(controls), units, obligations, derivations, open_items

    def development_records(
        self,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        gaps = {
            item.get("id"): item
            for item in self.map_data.get("development_gaps", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        decisions = {
            item.get("id"): item
            for item in self.map_data.get("design_decisions", [])
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        return gaps, decisions

    def conception_ids(self) -> dict[str, set[str]]:
        conception = self.map_data.get("conception")
        if not isinstance(conception, dict):
            return {"world": set(), "story": set(), "characters": set()}
        world = conception.get("world")
        story = conception.get("story")
        characters = conception.get("characters")
        world_ids = (
            {world.get("id")}
            if isinstance(world, dict) and nonempty_string(world.get("id"))
            else set()
        )
        if isinstance(world, dict):
            for collection in ("facets", "systems", "environments"):
                for item in world.get(collection, []):
                    if isinstance(item, dict) and nonempty_string(item.get("id")):
                        world_ids.add(item["id"])
        story_ids: set[str] = set()
        if isinstance(story, dict):
            if nonempty_string(story.get("id")):
                story_ids.add(story["id"])
            for phase in story.get("phases", []):
                if isinstance(phase, dict) and nonempty_string(phase.get("id")):
                    story_ids.add(phase["id"])
            for event in story.get("major_events", []):
                if isinstance(event, dict) and nonempty_string(event.get("id")):
                    story_ids.add(event["id"])
            for storyline in story.get("storylines", []):
                if isinstance(storyline, dict) and nonempty_string(
                    storyline.get("id")
                ):
                    story_ids.add(storyline["id"])
        character_ids: set[str] = set()
        if isinstance(characters, dict):
            for collection in ("demand_register", "profiles", "relationships"):
                for item in characters.get(collection, []):
                    if isinstance(item, dict) and nonempty_string(item.get("id")):
                        character_ids.add(item["id"])
        return {
            "world": world_ids,
            "story": story_ids,
            "characters": character_ids,
        }

    def validate_reviewer(self) -> None:
        reviewer = self.data.get("reviewer")
        if not isinstance(reviewer, dict):
            self.error("reviewer is missing")
            return
        reject_extra(
            self,
            reviewer,
            {"id", "role", "assurance", "evidence_scope", "method"},
            "reviewer",
        )
        if not nonempty_string(reviewer.get("id")):
            self.error("reviewer.id is missing")
        if reviewer.get("role") != "independent_developer":
            self.error("reviewer.role must be independent_developer")
        if reviewer.get("assurance") != "role_separated_execution":
            self.error("reviewer.assurance must be role_separated_execution")
        if reviewer.get("evidence_scope") != "d1_package_only":
            self.error("reviewer.evidence_scope must be d1_package_only")
        if not nonempty_string(reviewer.get("method"), 20):
            self.error("reviewer.method is too small")
        self_test = self.map_data.get("handoff_self_test")
        if (
            isinstance(self_test, dict)
            and reviewer.get("id") == self_test.get("reviewer_id")
        ):
            self.error("R1 reviewer must differ from the D1 self-test executor")

    def validate_control_areas(self) -> None:
        controls_by_area: dict[str, set[str]] = {area: set() for area in AREAS}
        for item in self.map_data.get("control_points", []):
            if not isinstance(item, dict):
                continue
            area = item.get("area")
            control_id = item.get("id")
            if area in controls_by_area and isinstance(control_id, str):
                controls_by_area[area].add(control_id)
        reviews = self.data.get("control_area_reviews")
        if not isinstance(reviews, list):
            self.error("control_area_reviews must be an array")
            reviews = []
        observed: set[str] = set()
        for index, review in enumerate(reviews):
            label = f"control_area_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {"area", "owner_stage", "status", "finding", "control_ids"},
                label,
            )
            area = review.get("area")
            if area not in AREAS or area in observed:
                self.error(f"{label}.area is invalid or duplicated")
                continue
            observed.add(area)
            if review.get("owner_stage") != AREAS[area]:
                self.error(f"{area}: owner_stage is invalid")
            if review.get("status") != "pass":
                self.error(f"{area}: review did not pass")
            if not nonempty_string(review.get("finding"), 20):
                self.error(f"{area}: finding is too small")
            ids = review.get("control_ids")
            if not string_list(ids, nonempty=True):
                self.error(f"{area}: control_ids must be non-empty")
                ids = []
            unknown = set(ids) - controls_by_area[area]
            if unknown:
                self.error(
                    f"{area}: review cites controls outside its area: "
                    + ", ".join(sorted(unknown))
                )
        if observed != set(AREAS):
            self.error("control_area_reviews must exactly cover all six areas")
        self.evidence["control_area_reviews"] = sorted(observed)

    def validate_conception_reviews(self) -> None:
        expected = self.conception_ids()
        controls, _units, _obligations, _derivations, _open_items = self.valid_ids()
        reviews = self.data.get("conception_reviews")
        if not isinstance(reviews, list):
            self.error("conception_reviews must be an array")
            reviews = []
        observed: set[str] = set()
        for index, review in enumerate(reviews):
            label = f"conception_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {"area", "status", "finding", "subject_ids", "control_ids"},
                label,
            )
            area = review.get("area")
            if area not in expected or area in observed:
                self.error(f"{label}.area is invalid or duplicated")
                continue
            observed.add(area)
            if review.get("status") != "pass":
                self.error(f"{area}: conception review did not pass")
            if not nonempty_string(review.get("finding"), 20):
                self.error(f"{area}: conception finding is too small")
            subject_ids = review.get("subject_ids")
            if (
                not string_list(subject_ids, nonempty=True)
                or set(subject_ids) != expected[area]
                or len(subject_ids) != len(set(subject_ids))
            ):
                self.error(
                    f"{area}: conception subject_ids must exactly cover "
                    "the D1 conception subjects"
                )
            control_ids = review.get("control_ids")
            if not string_list(control_ids, nonempty=True):
                self.error(f"{area}: conception control_ids must be non-empty")
                control_ids = []
            unknown = set(control_ids) - controls
            if unknown:
                self.error(
                    f"{area}: conception review cites unknown controls: "
                    + ", ".join(sorted(unknown))
                )
        if observed != set(expected):
            self.error("conception_reviews must exactly cover world, story and characters")
        self.evidence["conception_reviews"] = {
            area: len(ids) for area, ids in expected.items()
        }

    def validate_three_domain_reviews(self) -> None:
        conception = self.map_data.get("conception")
        if not isinstance(conception, dict):
            self.error("D1 conception is unavailable for three-domain review")
            return
        world = conception.get("world")
        story = conception.get("story")
        characters = conception.get("characters")

        world_records: dict[str, tuple[str, dict[str, Any]]] = {}
        if isinstance(world, dict):
            for collection, subject_type in (
                ("facets", "facet"),
                ("systems", "system"),
                ("environments", "environment"),
                (
                    "event_environment_requirements",
                    "event_environment_requirement",
                ),
            ):
                for item in world.get(collection, []):
                    if isinstance(item, dict) and nonempty_string(item.get("id")):
                        world_records[item["id"]] = (subject_type, item)
        world_reviews = self.data.get("world_model_reviews")
        if not isinstance(world_reviews, list):
            self.error("world_model_reviews must be an array")
            world_reviews = []
        observed_world: set[str] = set()
        for index, review in enumerate(world_reviews):
            label = f"world_model_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "subject_id",
                    "subject_type",
                    "status",
                    "finding",
                    "decision_ids",
                },
                label,
            )
            subject_id = review.get("subject_id")
            if subject_id not in world_records or subject_id in observed_world:
                self.error(f"{label}.subject_id is invalid or duplicated")
                continue
            observed_world.add(subject_id)
            subject_type, record = world_records[subject_id]
            if review.get("subject_type") != subject_type:
                self.error(f"{subject_id}: subject_type does not match D1")
            if review.get("status") != "pass":
                self.error(f"{subject_id}: world model review did not pass")
            if not nonempty_string(review.get("finding"), 40):
                self.error(f"{subject_id}: world model finding is too small")
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(f"{subject_id}: world decision_ids do not match D1")
        if observed_world != set(world_records):
            self.error(
                "world_model_reviews must exactly cover all world facets, "
                "systems, environments and event-environment requirements"
            )

        major_events = {
            item.get("id"): item
            for item in (
                story.get("major_events", []) if isinstance(story, dict) else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        event_source_coverage = (
            story.get("event_source_coverage", [])
            if isinstance(story, dict)
            else []
        )
        expected_event_source_ids: dict[str, list[str]] = {
            event_id: [
                item.get("id")
                for item in event_source_coverage
                if isinstance(item, dict)
                and event_id in item.get("major_event_ids", [])
            ]
            for event_id in major_events
        }
        major_event_reviews = self.data.get("major_event_reviews")
        if not isinstance(major_event_reviews, list):
            self.error("major_event_reviews must be an array")
            major_event_reviews = []
        observed_major_events: set[str] = set()
        for index, review in enumerate(major_event_reviews):
            label = f"major_event_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "event_id",
                    "status",
                    "finding",
                    "storyline_ids",
                    "unit_ids",
                    "environment_ids",
                    "participant_ids",
                    "source_coverage_ids",
                    "decision_ids",
                },
                label,
            )
            event_id = review.get("event_id")
            if (
                event_id not in major_events
                or event_id in observed_major_events
            ):
                self.error(f"{label}.event_id is invalid or duplicated")
                continue
            observed_major_events.add(event_id)
            record = major_events[event_id]
            if review.get("status") != "pass":
                self.error(f"{event_id}: major event review did not pass")
            if not nonempty_string(review.get("finding"), 40):
                self.error(f"{event_id}: major event finding is too small")
            for field in (
                "storyline_ids",
                "unit_ids",
                "environment_ids",
                "participant_ids",
            ):
                if review.get(field) != record.get(field):
                    self.error(f"{event_id}: {field} does not match D1")
            if review.get("source_coverage_ids") != expected_event_source_ids[
                event_id
            ]:
                self.error(
                    f"{event_id}: source_coverage_ids do not match D1"
                )
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(f"{event_id}: decision_ids do not match D1")
        if observed_major_events != set(major_events):
            self.error(
                "major_event_reviews must exactly cover all D1 major events"
            )

        storylines = {
            item.get("id"): item
            for item in (
                story.get("storylines", []) if isinstance(story, dict) else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        storyline_reviews = self.data.get("storyline_reviews")
        if not isinstance(storyline_reviews, list):
            self.error("storyline_reviews must be an array")
            storyline_reviews = []
        observed_storylines: set[str] = set()
        for index, review in enumerate(storyline_reviews):
            label = f"storyline_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "storyline_id",
                    "type",
                    "status",
                    "finding",
                    "unit_ids",
                    "decision_ids",
                },
                label,
            )
            storyline_id = review.get("storyline_id")
            if (
                storyline_id not in storylines
                or storyline_id in observed_storylines
            ):
                self.error(f"{label}.storyline_id is invalid or duplicated")
                continue
            observed_storylines.add(storyline_id)
            record = storylines[storyline_id]
            if review.get("type") != record.get("type"):
                self.error(f"{storyline_id}: reviewed type does not match D1")
            if review.get("status") != "pass":
                self.error(f"{storyline_id}: storyline review did not pass")
            if not nonempty_string(review.get("finding"), 40):
                self.error(f"{storyline_id}: storyline finding is too small")
            if review.get("unit_ids") != record.get("unit_ids"):
                self.error(f"{storyline_id}: unit_ids do not match D1")
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(f"{storyline_id}: decision_ids do not match D1")
        if observed_storylines != set(storylines):
            self.error("storyline_reviews must exactly cover all D1 storylines")

        storyline_demands = {
            item.get("id"): item
            for item in (
                story.get("storyline_demands", [])
                if isinstance(story, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        storyline_demand_reviews = self.data.get(
            "storyline_demand_reviews"
        )
        if not isinstance(storyline_demand_reviews, list):
            self.error("storyline_demand_reviews must be an array")
            storyline_demand_reviews = []
        observed_storyline_demands: set[str] = set()
        for index, review in enumerate(storyline_demand_reviews):
            label = f"storyline_demand_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "demand_id",
                    "status",
                    "finding",
                    "disposition",
                    "storyline_ids",
                    "decision_ids",
                },
                label,
            )
            demand_id = review.get("demand_id")
            if (
                demand_id not in storyline_demands
                or demand_id in observed_storyline_demands
            ):
                self.error(f"{label}.demand_id is invalid or duplicated")
                continue
            observed_storyline_demands.add(str(demand_id))
            record = storyline_demands[str(demand_id)]
            if review.get("status") != "pass":
                self.error(
                    f"{demand_id}: storyline demand review did not pass"
                )
            if not nonempty_string(review.get("finding"), 40):
                self.error(
                    f"{demand_id}: storyline demand finding is too small"
                )
            for field in ("disposition", "storyline_ids"):
                if review.get(field) != record.get(field):
                    self.error(
                        f"{demand_id}: reviewed {field} does not match D1"
                    )
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(
                    f"{demand_id}: storyline demand decision_ids do not match D1"
                )
        if observed_storyline_demands != set(storyline_demands):
            self.error(
                "storyline_demand_reviews must exactly cover all D1 "
                "storyline demands"
            )

        architecture = (
            story.get("storyline_architecture")
            if isinstance(story, dict)
            else {}
        )
        architecture_review = self.data.get("storyline_architecture_review")
        if not isinstance(architecture_review, dict):
            self.error("storyline_architecture_review must be an object")
            architecture_review = {}
        if isinstance(architecture, dict):
            reject_extra(
                self,
                architecture_review,
                {
                    "subject_id",
                    "status",
                    "finding",
                    "entry_storyline_ids",
                    "main_storyline_id",
                    "terminal_storyline_ids",
                    "decision_ids",
                },
                "storyline_architecture_review",
            )
            if architecture_review.get("subject_id") != architecture.get(
                "id"
            ):
                self.error(
                    "storyline_architecture_review.subject_id does not match D1"
                )
            if architecture_review.get("status") != "pass":
                self.error("storyline architecture review did not pass")
            if not nonempty_string(
                architecture_review.get("finding"), 40
            ):
                self.error("storyline architecture finding is too small")
            for field in (
                "entry_storyline_ids",
                "main_storyline_id",
                "terminal_storyline_ids",
            ):
                if architecture_review.get(field) != architecture.get(field):
                    self.error(
                        "storyline_architecture_review."
                        f"{field} does not match D1"
                    )
            if architecture_review.get("decision_ids") != architecture.get(
                "development_decisions"
            ):
                self.error(
                    "storyline_architecture_review.decision_ids do not match D1"
                )

        connections = {
            item.get("id"): item
            for item in (
                architecture.get("connection_points", [])
                if isinstance(architecture, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        connection_reviews = self.data.get("storyline_connection_reviews")
        if not isinstance(connection_reviews, list):
            self.error("storyline_connection_reviews must be an array")
            connection_reviews = []
        observed_connections: set[str] = set()
        for index, review in enumerate(connection_reviews):
            label = f"storyline_connection_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "connection_id",
                    "status",
                    "finding",
                    "connection_type",
                    "event_id",
                    "incoming_storyline_ids",
                    "outgoing_storyline_ids",
                    "decision_ids",
                },
                label,
            )
            connection_id = review.get("connection_id")
            if (
                connection_id not in connections
                or connection_id in observed_connections
            ):
                self.error(
                    f"{label}.connection_id is invalid or duplicated"
                )
                continue
            observed_connections.add(str(connection_id))
            record = connections[str(connection_id)]
            if review.get("status") != "pass":
                self.error(
                    f"{connection_id}: storyline connection review did not pass"
                )
            if not nonempty_string(review.get("finding"), 40):
                self.error(
                    f"{connection_id}: storyline connection finding is too small"
                )
            for field in (
                "connection_type",
                "event_id",
                "incoming_storyline_ids",
                "outgoing_storyline_ids",
            ):
                if review.get(field) != record.get(field):
                    self.error(
                        f"{connection_id}: reviewed {field} does not match D1"
                    )
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(
                    f"{connection_id}: connection decision_ids do not match D1"
                )
        if observed_connections != set(connections):
            self.error(
                "storyline_connection_reviews must exactly cover all D1 "
                "storyline connections"
            )

        melody_lines = {
            item.get("id"): item
            for item in (
                story.get("melody_lines", [])
                if isinstance(story, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        melody_line_reviews = self.data.get("melody_line_reviews")
        if not isinstance(melody_line_reviews, list):
            self.error("melody_line_reviews must be an array")
            melody_line_reviews = []
        observed_melody_lines: set[str] = set()
        for index, review in enumerate(melody_line_reviews):
            label = f"melody_line_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "melody_line_id",
                    "status",
                    "finding",
                    "anchor_event_ids",
                    "required_for_causality",
                    "required_for_resolution",
                    "new_pov_allowed",
                    "carries_decisive_information",
                    "decision_ids",
                },
                label,
            )
            melody_line_id = review.get("melody_line_id")
            if (
                melody_line_id not in melody_lines
                or melody_line_id in observed_melody_lines
            ):
                self.error(
                    f"{label}.melody_line_id is invalid or duplicated"
                )
                continue
            melody_line_id = str(melody_line_id)
            observed_melody_lines.add(melody_line_id)
            record = melody_lines[melody_line_id]
            if review.get("status") != "pass":
                self.error(
                    f"{melody_line_id}: melody line review did not pass"
                )
            if not nonempty_string(review.get("finding"), 40):
                self.error(
                    f"{melody_line_id}: melody line finding is too small"
                )
            for field in (
                "anchor_event_ids",
                "required_for_causality",
                "required_for_resolution",
                "new_pov_allowed",
                "carries_decisive_information",
            ):
                if review.get(field) != record.get(field):
                    self.error(
                        f"{melody_line_id}: reviewed {field} does not "
                        "match D1"
                    )
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(
                    f"{melody_line_id}: melody line decision_ids do not "
                    "match D1"
                )
        if observed_melody_lines != set(melody_lines):
            self.error(
                "melody_line_reviews must exactly cover all D1 melody lines"
            )

        character_records = {
            item.get("id"): item
            for item in (
                characters.get("profiles", [])
                if isinstance(characters, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        relationship_records = {
            item.get("id"): item
            for item in (
                characters.get("relationships", [])
                if isinstance(characters, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        demand_records = {
            item.get("id"): item
            for item in (
                characters.get("demand_register", [])
                if isinstance(characters, dict)
                else []
            )
            if isinstance(item, dict) and nonempty_string(item.get("id"))
        }
        demand_reviews = self.data.get("character_demand_reviews")
        if not isinstance(demand_reviews, list):
            self.error("character_demand_reviews must be an array")
            demand_reviews = []
        observed_demands: set[str] = set()
        for index, review in enumerate(demand_reviews):
            label = f"character_demand_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "demand_id",
                    "category",
                    "status",
                    "finding",
                    "resolution",
                    "profile_id",
                    "decision_ids",
                },
                label,
            )
            demand_id = review.get("demand_id")
            if demand_id not in demand_records or demand_id in observed_demands:
                self.error(f"{label}.demand_id is invalid or duplicated")
                continue
            observed_demands.add(str(demand_id))
            record = demand_records[str(demand_id)]
            for field in ("category", "resolution", "profile_id"):
                if review.get(field) != record.get(field):
                    self.error(
                        f"{demand_id}: reviewed {field} does not match D1"
                    )
            if review.get("status") != "pass":
                self.error(f"{demand_id}: character demand review did not pass")
            if not nonempty_string(review.get("finding"), 60):
                self.error(f"{demand_id}: character demand finding is too small")
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(
                    f"{demand_id}: character demand decision_ids do not match D1"
                )
        if observed_demands != set(demand_records):
            self.error(
                "character_demand_reviews must exactly cover the D1 demand register"
            )

        profile_reviews = self.data.get("character_profile_reviews")
        if not isinstance(profile_reviews, list):
            self.error("character_profile_reviews must be an array")
            profile_reviews = []
        observed_profiles: set[str] = set()
        for index, review in enumerate(profile_reviews):
            label = f"character_profile_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "character_id",
                    "importance",
                    "status",
                    "finding",
                    "decision_ids",
                },
                label,
            )
            character_id = review.get("character_id")
            if (
                character_id not in character_records
                or character_id in observed_profiles
            ):
                self.error(f"{label}.character_id is invalid or duplicated")
                continue
            observed_profiles.add(str(character_id))
            record = character_records[str(character_id)]
            if review.get("importance") != record.get("importance"):
                self.error(f"{character_id}: reviewed importance does not match D1")
            if review.get("status") != "pass":
                self.error(f"{character_id}: character profile review did not pass")
            if not nonempty_string(review.get("finding"), 50):
                self.error(f"{character_id}: character profile finding is too small")
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(f"{character_id}: character decision_ids do not match D1")
        if observed_profiles != set(character_records):
            self.error(
                "character_profile_reviews must exactly cover canonical profiles"
            )

        edge_reviews = self.data.get("relationship_edge_reviews")
        if not isinstance(edge_reviews, list):
            self.error("relationship_edge_reviews must be an array")
            edge_reviews = []
        observed_edges: set[str] = set()
        for index, review in enumerate(edge_reviews):
            label = f"relationship_edge_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "relationship_id",
                    "source_id",
                    "target_id",
                    "status",
                    "finding",
                    "decision_ids",
                },
                label,
            )
            relationship_id = review.get("relationship_id")
            if (
                relationship_id not in relationship_records
                or relationship_id in observed_edges
            ):
                self.error(f"{label}.relationship_id is invalid or duplicated")
                continue
            observed_edges.add(str(relationship_id))
            record = relationship_records[str(relationship_id)]
            for field in ("source_id", "target_id"):
                if review.get(field) != record.get(field):
                    self.error(
                        f"{relationship_id}: reviewed {field} does not match D1"
                    )
            if review.get("status") != "pass":
                self.error(f"{relationship_id}: relationship edge review did not pass")
            if not nonempty_string(review.get("finding"), 50):
                self.error(
                    f"{relationship_id}: relationship edge finding is too small"
                )
            if review.get("decision_ids") != record.get(
                "development_decisions"
            ):
                self.error(
                    f"{relationship_id}: relationship decision_ids do not match D1"
                )
        if observed_edges != set(relationship_records):
            self.error(
                "relationship_edge_reviews must exactly cover canonical edges"
            )

        adjacency: dict[str, set[str]] = {
            character_id: set() for character_id in character_records
        }
        for edge in relationship_records.values():
            source_id = edge.get("source_id")
            target_id = edge.get("target_id")
            if source_id in adjacency and target_id in adjacency:
                adjacency[str(source_id)].add(str(target_id))
                adjacency[str(target_id)].add(str(source_id))
        core_records = {
            character_id: record
            for character_id, record in character_records.items()
            if record.get("importance") == "core"
        }
        network_reviews = self.data.get("relationship_network_reviews")
        if not isinstance(network_reviews, list):
            self.error("relationship_network_reviews must be an array")
            network_reviews = []
        observed_characters: set[str] = set()
        for index, review in enumerate(network_reviews):
            label = f"relationship_network_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "character_id",
                    "status",
                    "finding",
                    "max_depth",
                    "layer_character_ids",
                    "profiled_character_ids",
                    "relationship_ids",
                },
                label,
            )
            character_id = review.get("character_id")
            if (
                character_id not in core_records
                or character_id in observed_characters
            ):
                self.error(f"{label}.character_id is invalid or duplicated")
                continue
            observed_characters.add(character_id)
            distances = {str(character_id): 0}
            queue = [str(character_id)]
            for current in queue:
                for neighbor in sorted(adjacency.get(current, set())):
                    if neighbor in distances:
                        continue
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
            expected_characters: dict[str, list[str]] = {}
            for node_id, distance in distances.items():
                if distance:
                    expected_characters.setdefault(str(distance), []).append(
                        node_id
                    )
            expected_characters = {
                level: sorted(node_ids)
                for level, node_ids in sorted(
                    expected_characters.items(),
                    key=lambda item: int(item[0]),
                )
            }
            computed_max_depth = max(distances.values(), default=0)
            flattened_characters = [
                node_id
                for level in sorted(
                    expected_characters,
                    key=lambda value: int(value),
                )
                for node_id in expected_characters.get(level, [])
            ]
            if review.get("status") != "pass":
                self.error(f"{character_id}: relationship review did not pass")
            if not nonempty_string(review.get("finding"), 50):
                self.error(f"{character_id}: relationship finding is too small")
            if review.get("max_depth") != computed_max_depth:
                self.error(
                    f"{character_id}: max_depth must match the recomputed "
                    "person-graph depth"
                )
            if review.get("layer_character_ids") != expected_characters:
                self.error(
                    f"{character_id}: layer_character_ids do not match the "
                    "D1 person-path projection"
                )
            if review.get("profiled_character_ids") != flattened_characters:
                self.error(
                    f"{character_id}: profiled_character_ids must exactly cover "
                    "all extended character definitions"
                )
            component_ids = set(distances)
            expected_relations = [
                relationship_id
                for relationship_id, edge in relationship_records.items()
                if edge.get("source_id") in component_ids
                and edge.get("target_id") in component_ids
            ]
            if review.get("relationship_ids") != expected_relations:
                self.error(f"{character_id}: relationship_ids do not match D1")
        if observed_characters != set(core_records):
            self.error(
                "relationship_network_reviews must exactly cover core characters"
            )
        self.evidence["three_domain_reviews"] = {
            "world_subjects": len(observed_world),
            "major_events": len(observed_major_events),
            "storylines": len(observed_storylines),
            "storyline_demands": len(observed_storyline_demands),
            "storyline_connections": len(observed_connections),
            "character_demands": len(observed_demands),
            "character_profiles": len(observed_profiles),
            "relationship_edges": len(observed_edges),
            "character_networks": len(observed_characters),
        }

    def validate_cross_checks(self) -> None:
        controls, units, _obligations, _derivations, _open_items = self.valid_ids()
        checks = self.data.get("cross_domain_checks")
        if not isinstance(checks, dict):
            self.error("cross_domain_checks must be an object")
            return
        if set(checks) != CROSS_CHECKS:
            self.error("cross_domain_checks must contain exactly thirteen checks")
        passed = 0
        challenge_grounding: dict[str, dict[str, int]] = {}
        conception = self.map_data.get("conception")
        world = conception.get("world") if isinstance(conception, dict) else {}
        story = conception.get("story") if isinstance(conception, dict) else {}
        character_model = (
            conception.get("characters", {})
            if isinstance(conception, dict)
            else {}
        )
        characters = (
            character_model.get("profiles", [])
            if isinstance(character_model, dict)
            else []
        )
        character_relationships = (
            character_model.get("relationships", [])
            if isinstance(character_model, dict)
            else []
        )
        map_units = self.map_data.get("units", [])
        obligations = self.map_data.get("information_obligations", [])
        if not isinstance(characters, list):
            characters = []
        if not isinstance(map_units, list):
            map_units = []
        if not isinstance(obligations, list):
            obligations = []
        challenge_targets = {
            "world_causality": [
                world,
                *(
                    world.get("systems", [])
                    if isinstance(world, dict)
                    else []
                ),
                *(
                    world.get("environments", [])
                    if isinstance(world, dict)
                    else []
                ),
                *map_units,
            ],
            "character_agency": [
                *characters,
                *character_relationships,
                *map_units,
            ],
            "opposition_response": map_units,
            "choice_costs": map_units,
            "easy_solution": [
                world,
                *(
                    world.get("systems", [])
                    if isinstance(world, dict)
                    else []
                ),
                *map_units,
            ],
            "narrative_information": [
                *obligations,
                *map_units,
                *(
                    story.get("storylines", [])
                    if isinstance(story, dict)
                    else []
                ),
            ],
            "development_usability": [
                *map_units,
                *(
                    story.get("phases", [])
                    if isinstance(story, dict)
                    else []
                ),
                *(
                    story.get("storylines", [])
                    if isinstance(story, dict)
                    else []
                ),
            ],
        }
        corpus_objects: list[Any] = []
        object_index: dict[str, dict[str, Any]] = {}

        def collect_records(value: Any) -> None:
            if isinstance(value, dict):
                if isinstance(value.get("id"), str):
                    corpus_objects.append(value)
                    object_index[value["id"]] = value
                for nested in value.values():
                    collect_records(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect_records(nested)

        collect_records(self.map_data)
        token_frequency: dict[str, int] = {}
        for record in corpus_objects:
            for token in grounding_tokens(record):
                token_frequency[token] = token_frequency.get(token, 0) + 1
        rare_limit = max(2, len(corpus_objects) // 5)
        for check_id in CROSS_CHECKS:
            item = checks.get(check_id)
            if not isinstance(item, dict):
                self.error(f"{check_id}: cross-domain check is missing")
                continue
            reject_extra(
                self,
                item,
                {
                    "status",
                    "finding",
                    "control_ids",
                    "unit_ids",
                    "assertions",
                },
                f"cross_domain_checks.{check_id}",
            )
            if item.get("status") != "pass":
                self.error(f"{check_id}: cross-domain check did not pass")
            else:
                passed += 1
            if not nonempty_string(item.get("finding"), 20):
                self.error(f"{check_id}: finding is too small")
            elif (
                item.get("status") == "pass"
                and UNRESOLVED_FAILURE_PATTERN.search(
                    str(item.get("finding"))
                )
            ):
                self.error(
                    f"{check_id}: finding reports an unresolved failure "
                    "but status is pass"
                )
            control_ids = item.get("control_ids")
            unit_ids = item.get("unit_ids")
            if not string_list(control_ids) or not string_list(unit_ids):
                self.error(f"{check_id}: evidence arrays are invalid")
                continue
            if not control_ids and not unit_ids:
                self.error(f"{check_id}: check cites no evidence")
            unknown = (set(control_ids) - controls) | (set(unit_ids) - units)
            if unknown:
                self.error(
                    f"{check_id}: check cites unknown evidence: "
                    + ", ".join(sorted(unknown))
                )
            assertions = item.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                self.error(f"{check_id}: structured assertions are missing")
                assertions = []
            assertion_ids: set[str] = set()
            bound_subjects: set[str] = set()
            for assertion_index, assertion in enumerate(assertions):
                label = (
                    f"cross_domain_checks.{check_id}.assertions"
                    f"[{assertion_index}]"
                )
                if not isinstance(assertion, dict):
                    self.error(f"{label} is not an object")
                    continue
                reject_extra(
                    self,
                    assertion,
                    {
                        "id",
                        "result",
                        "failure_found",
                        "test",
                        "failure_condition",
                        "counterexample",
                        "conclusion",
                        "field_evidence",
                    },
                    label,
                )
                assertion_id = assertion.get("id")
                if (
                    not nonempty_string(assertion_id)
                    or assertion_id in assertion_ids
                ):
                    self.error(f"{label}.id is missing or duplicated")
                else:
                    assertion_ids.add(str(assertion_id))
                if assertion.get("result") != "pass":
                    self.error(f"{label}.result did not pass")
                if assertion.get("failure_found") is not False:
                    self.error(
                        f"{label}.failure_found must be false for a pass result"
                    )
                for field in (
                    "test",
                    "failure_condition",
                    "counterexample",
                    "conclusion",
                ):
                    if not nonempty_string(assertion.get(field), 20):
                        self.error(f"{label}.{field} is too small")
                field_evidence = assertion.get("field_evidence")
                if not isinstance(field_evidence, list) or not field_evidence:
                    self.error(f"{label}.field_evidence must be non-empty")
                    field_evidence = []
                bound_values: list[Any] = []
                observed_bindings: set[tuple[str, str]] = set()
                for evidence_index, evidence in enumerate(field_evidence):
                    evidence_label = (
                        f"{label}.field_evidence[{evidence_index}]"
                    )
                    if not isinstance(evidence, dict):
                        self.error(f"{evidence_label} is not an object")
                        continue
                    reject_extra(
                        self,
                        evidence,
                        {"subject_id", "field", "value_sha256"},
                        evidence_label,
                    )
                    subject_id = evidence.get("subject_id")
                    field = evidence.get("field")
                    if subject_id not in object_index:
                        self.error(
                            f"{evidence_label}.subject_id is unknown"
                        )
                        continue
                    record = object_index[str(subject_id)]
                    if field not in record:
                        self.error(
                            f"{evidence_label}.field does not exist on "
                            f"{subject_id}"
                        )
                        continue
                    binding = (str(subject_id), str(field))
                    if binding in observed_bindings:
                        self.error(f"{evidence_label} is duplicated")
                    observed_bindings.add(binding)
                    bound_subjects.add(str(subject_id))
                    value = record.get(str(field))
                    bound_values.append(value)
                    if evidence.get("value_sha256") != canonical_value_sha256(
                        value
                    ):
                        self.error(
                            f"{evidence_label}.value_sha256 does not bind "
                            "the current D1 field"
                        )
                bound_tokens = grounding_tokens(bound_values)
                assertion_text = {
                    field: assertion.get(field)
                    for field in (
                        "test",
                        "failure_condition",
                        "counterexample",
                        "conclusion",
                    )
                }
                overlap = grounding_tokens(assertion_text) & bound_tokens
                required_overlap = min(2, len(bound_tokens))
                if bound_tokens and len(overlap) < required_overlap:
                    self.error(
                        f"{label}: assertion is not grounded in bound D1 values"
                    )
            expected_target_ids = {
                record.get("id")
                for record in challenge_targets.get(check_id, [])
                if isinstance(record, dict) and nonempty_string(record.get("id"))
            }
            if expected_target_ids and not (
                bound_subjects & expected_target_ids
            ):
                self.error(
                    f"{check_id}: assertions do not bind a required target object"
                )
            targets = challenge_targets.get(check_id)
            if targets:
                overlap = grounding_tokens(item.get("finding")) & grounding_tokens(
                    targets
                )
                rare_overlap = {
                    token
                    for token in overlap
                    if token_frequency.get(token, 0) <= rare_limit
                }
                challenge_grounding[check_id] = {
                    "overlap": len(overlap),
                    "rare_overlap": len(rare_overlap),
                }
                if len(overlap) < 2 or not rare_overlap:
                    self.error(
                        f"{check_id}: semantic challenge is not grounded in its "
                        "target D1 fields"
                    )
        self.evidence["cross_domain_checks"] = {
            "required": len(CROSS_CHECKS),
            "passed": passed,
            "target_grounding": challenge_grounding,
        }

    def validate_autonomous_development_reviews(self) -> None:
        controls, _units, _obligations, _derivations, _open_items = self.valid_ids()
        gaps, decisions = self.development_records()
        gap_reviews = self.data.get("development_gap_reviews")
        if not isinstance(gap_reviews, list):
            self.error("development_gap_reviews must be an array")
            gap_reviews = []
        observed_gaps: set[str] = set()
        for index, review in enumerate(gap_reviews):
            label = f"development_gap_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {"gap_id", "status", "finding", "resolution"},
                label,
            )
            gap_id = review.get("gap_id")
            if gap_id not in gaps or gap_id in observed_gaps:
                self.error(f"{label}.gap_id is invalid or duplicated")
                continue
            observed_gaps.add(gap_id)
            if review.get("status") != "pass":
                self.error(f"{gap_id}: development gap review did not pass")
            if not nonempty_string(review.get("finding"), 30):
                self.error(f"{gap_id}: development gap finding is too small")
            if review.get("resolution") != gaps[gap_id].get("resolution"):
                self.error(f"{gap_id}: reviewed resolution does not match D1")
        if observed_gaps != set(gaps):
            self.error(
                "development_gap_reviews must exactly cover all D1 development gaps"
            )

        decision_reviews = self.data.get("design_decision_reviews")
        if not isinstance(decision_reviews, list):
            self.error("design_decision_reviews must be an array")
            decision_reviews = []
        observed_decisions: set[str] = set()
        for index, review in enumerate(decision_reviews):
            label = f"design_decision_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "decision_id",
                    "status",
                    "finding",
                    "gap_ids",
                    "source_control_ids",
                    "dimensions",
                },
                label,
            )
            decision_id = review.get("decision_id")
            if decision_id not in decisions or decision_id in observed_decisions:
                self.error(f"{label}.decision_id is invalid or duplicated")
                continue
            observed_decisions.add(decision_id)
            decision = decisions[decision_id]
            if review.get("status") != "pass":
                self.error(f"{decision_id}: design decision review did not pass")
            if not nonempty_string(review.get("finding"), 40):
                self.error(f"{decision_id}: design decision finding is too small")
            if review.get("gap_ids") != decision.get("gap_ids"):
                self.error(f"{decision_id}: gap_ids do not match D1")
            if review.get("source_control_ids") != decision.get(
                "source_controls"
            ):
                self.error(f"{decision_id}: source controls do not match D1")
            unknown_controls = set(
                string_values(review.get("source_control_ids"))
            ) - controls
            if unknown_controls:
                self.error(
                    f"{decision_id}: review cites unknown controls: "
                    + ", ".join(sorted(unknown_controls))
                )
            dimensions = review.get("dimensions")
            if not isinstance(dimensions, dict) or set(dimensions) != (
                DESIGN_REVIEW_DIMENSIONS
            ):
                self.error(
                    f"{decision_id}: dimensions must exactly cover all "
                    "autonomous review dimensions"
                )
            else:
                for dimension, result in dimensions.items():
                    if result != "pass":
                        self.error(
                            f"{decision_id}: {dimension} dimension did not pass"
                        )
        if observed_decisions != set(decisions):
            self.error(
                "design_decision_reviews must exactly cover all D1 design decisions"
            )
        self.evidence["autonomous_development_reviews"] = {
            "gaps": len(observed_gaps),
            "decisions": len(observed_decisions),
            "dimensions": len(DESIGN_REVIEW_DIMENSIONS),
        }

    def validate_derivations_and_tasks(self) -> None:
        controls, units, obligations, derivations, _open_items = self.valid_ids()
        reviews = self.data.get("derivation_reviews")
        if not isinstance(reviews, list):
            self.error("derivation_reviews must be an array")
            reviews = []
        observed: set[str] = set()
        for index, review in enumerate(reviews):
            label = f"derivation_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {
                    "derivation_id",
                    "status",
                    "finding",
                    "source_control_ids",
                    "source_decision_ids",
                },
                label,
            )
            derivation_id = review.get("derivation_id")
            if (
                not nonempty_string(derivation_id)
                or derivation_id not in derivations
                or derivation_id in observed
            ):
                self.error(f"{label}.derivation_id is invalid or duplicated")
                continue
            observed.add(derivation_id)
            if review.get("status") != "pass":
                self.error(f"{derivation_id}: derivation review did not pass")
            if not nonempty_string(review.get("finding"), 20):
                self.error(f"{derivation_id}: finding is too small")
            if review.get("source_control_ids") != derivations[
                derivation_id
            ].get("source_controls"):
                self.error(f"{derivation_id}: source controls do not match D1")
            if review.get("source_decision_ids", []) != derivations[
                derivation_id
            ].get("source_decisions", []):
                self.error(f"{derivation_id}: source decisions do not match D1")
        if observed != set(derivations):
            self.error("derivation_reviews must exactly cover all D1 claims")

        subject_ids = self.data.get("subject_ids")
        if (
            not string_list(subject_ids, nonempty=bool(units))
            or len(string_values(subject_ids)) != len(set(string_values(subject_ids)))
            or set(string_values(subject_ids)) != units
        ):
            self.error("subject_ids must exactly cover all D1 units")

        tasks = self.data.get("tasks")
        if not isinstance(tasks, list):
            self.error("tasks must be an array")
            tasks = []
        conception_subjects = set().union(*self.conception_ids().values())
        gaps, decisions = self.development_records()
        valid_evidence = (
            controls
            | units
            | obligations
            | set(derivations)
            | conception_subjects
            | set(gaps)
            | set(decisions)
        )
        task_ids: set[str] = set()
        for index, task in enumerate(tasks):
            label = f"tasks[{index}]"
            if not isinstance(task, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                task,
                {"id", "status", "response", "evidence_ids"},
                label,
            )
            task_id = task.get("id")
            if task_id not in HANDOFF_TASKS or task_id in task_ids:
                self.error(f"{label}.id is invalid or duplicated")
                continue
            task_ids.add(task_id)
            if task.get("status") != "pass":
                self.error(f"{task_id}: handoff task did not pass")
            if not nonempty_string(task.get("response"), 40):
                self.error(f"{task_id}: response is too small")
            evidence_ids = task.get("evidence_ids")
            if not string_list(evidence_ids, nonempty=True):
                self.error(f"{task_id}: evidence_ids must be non-empty")
                evidence_ids = []
            unknown = set(evidence_ids) - valid_evidence
            if unknown:
                self.error(
                    f"{task_id}: task cites unknown evidence: "
                    + ", ".join(sorted(unknown))
                )
        if task_ids != HANDOFF_TASKS:
            self.error("tasks must contain exactly the eight required tasks")
        self.evidence["independent_handoff"] = {
            "subjects": len(set(string_values(subject_ids))),
            "derivations": len(observed),
            "tasks": len(task_ids),
        }

    def validate_open_items_and_findings(self) -> None:
        controls, units, obligations, derivations, open_items = self.valid_ids()
        reviews = self.data.get("open_item_reviews")
        if not isinstance(reviews, list):
            self.error("open_item_reviews must be an array")
            reviews = []
        observed: set[str] = set()
        for index, review in enumerate(reviews):
            label = f"open_item_reviews[{index}]"
            if not isinstance(review, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                review,
                {"open_item_id", "status", "finding"},
                label,
            )
            item_id = review.get("open_item_id")
            if (
                not nonempty_string(item_id)
                or item_id not in open_items
                or item_id in observed
            ):
                self.error(f"{label}.open_item_id is invalid or duplicated")
                continue
            observed.add(item_id)
            if review.get("status") != "preserved":
                self.error(f"{item_id}: open item was not preserved")
            if not nonempty_string(review.get("finding"), 20):
                self.error(f"{item_id}: open-item finding is too small")
        if observed != open_items:
            self.error("open_item_reviews must exactly cover all D1 open items")

        conception_subjects = set().union(*self.conception_ids().values())
        valid_evidence = (
            controls
            | units
            | obligations
            | set(derivations)
            | open_items
            | conception_subjects
        )
        findings = self.data.get("findings")
        if not isinstance(findings, list):
            self.error("findings must be an array")
            findings = []
        ids: set[str] = set()
        for index, finding in enumerate(findings):
            label = f"findings[{index}]"
            if not isinstance(finding, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                finding,
                {
                    "id",
                    "severity",
                    "owner",
                    "problem",
                    "evidence_ids",
                    "required_action",
                },
                label,
            )
            finding_id = finding.get("id")
            if not nonempty_string(finding_id) or finding_id in ids:
                self.error(f"{label}.id is invalid or duplicated")
                continue
            ids.add(finding_id)
            severity = finding.get("severity")
            if severity not in FINDING_SEVERITIES:
                self.error(f"{finding_id}: severity is invalid")
            owner = finding.get("owner")
            if owner not in FINDING_OWNERS:
                self.error(f"{finding_id}: owner is invalid")
            elif severity == "revise" and owner not in LOCAL_REVISE_OWNERS:
                self.error(
                    f"{finding_id}: revise finding owner must be D1 or R1; "
                    "an I0-I5 control change requires a blocked return"
                )
            elif severity == "blocked" and owner not in CONTROL_STAGES:
                self.error(
                    f"{finding_id}: blocked finding owner must be I0-I5"
                )
            for field in ("problem", "required_action"):
                if not nonempty_string(finding.get(field), 12):
                    self.error(f"{finding_id}: {field} is too small")
            evidence_ids = finding.get("evidence_ids")
            if not string_list(evidence_ids, nonempty=True):
                self.error(f"{finding_id}: evidence_ids must be non-empty")
                evidence_ids = []
            unknown = set(evidence_ids) - valid_evidence
            if unknown:
                self.error(
                    f"{finding_id}: finding cites unknown evidence: "
                    + ", ".join(sorted(unknown))
                )
            if severity == "revise":
                self.revise_findings.add(finding_id)
            elif severity == "blocked":
                self.blocked_findings.add(finding_id)
            self.findings_by_id[finding_id] = finding
        self.evidence["open_items"] = {
            "required": len(open_items),
            "preserved": len(observed),
        }

    def validate_status_and_return(self) -> None:
        if self.blocked_findings:
            expected_status = "blocked"
        elif self.revise_findings:
            expected_status = "revise"
        else:
            expected_status = "ready"
        if self.data.get("status") != expected_status:
            self.error(
                "review-data status must match the highest finding severity: "
                + expected_status
            )

        request = self.data.get("return_request")
        if expected_status != "blocked":
            if request is not None:
                self.error(
                    "return_request is allowed only for a blocked review"
                )
            return
        if not isinstance(request, dict):
            self.error("blocked review requires return_request")
            return
        reject_extra(
            self,
            request,
            {
                "finding_ids",
                "target_stage",
                "requested_decision",
                "affected_artifacts",
            },
            "return_request",
        )
        finding_ids = request.get("finding_ids")
        if (
            not string_list(finding_ids, nonempty=True)
            or len(finding_ids) != len(set(finding_ids))
            or set(finding_ids) != self.blocked_findings
        ):
            self.error(
                "return_request.finding_ids must exactly cover blocked findings"
            )
            return
        blocked = [self.findings_by_id[item] for item in finding_ids]
        owners = {item.get("owner") for item in blocked}
        if (
            len(owners) != 1
            or next(iter(owners), None) not in set(AREAS.values())
            or request.get("target_stage") not in owners
        ):
            self.error(
                "blocked findings must resolve to one I0-I5 return target"
            )
        if not nonempty_string(request.get("requested_decision"), 12):
            self.error("return_request.requested_decision is too small")
        artifacts = request.get("affected_artifacts")
        if not string_list(artifacts, nonempty=True):
            self.error(
                "return_request.affected_artifacts must be non-empty"
            )
        elif len(artifacts) != len(set(artifacts)):
            self.error(
                "return_request.affected_artifacts must not contain duplicates"
            )
        else:
            target = request.get("target_stage")
            canonical_artifact = CONTROL_STAGE_ARTIFACTS.get(target)
            if (
                canonical_artifact is not None
                and canonical_artifact not in artifacts
            ):
                self.error(
                    "return_request.affected_artifacts must include "
                    f"{canonical_artifact} for {target}"
                )
        self.return_request_valid = not any(
            message.startswith("return_request")
            or "blocked findings must resolve" in message
            for message in self.errors
        )

    def validate_or_write_outputs(
        self,
        *,
        write: bool,
        include_handoff: bool,
        include_return: bool,
    ) -> None:
        try:
            expected = render_outputs(
                self.package_dir,
                self.data,
                include_handoff=include_handoff,
                include_return=include_return,
            )
        except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
            self.error(f"deterministic rendering failed: {exc}")
            return
        for filename in GENERATED_OUTPUT_FILES - set(expected):
            path = self.package_dir / filename
            if write:
                if path.exists():
                    path.unlink()
            elif path.exists():
                self.error(
                    f"{filename} is not allowed for the current R1 verdict"
                )
        for filename, content in expected.items():
            path = self.package_dir / filename
            if write:
                path.write_bytes(content.encode("utf-8"))
            else:
                try:
                    actual = path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError) as exc:
                    self.error(f"{filename} is unreadable: {exc}")
                    continue
                if actual != content:
                    self.error(f"{filename} is stale or hand-edited")
        self.evidence["documents"] = sorted(expected)

    def require_no_generated_outputs(self, *, write: bool) -> None:
        for filename in GENERATED_OUTPUT_FILES:
            path = self.package_dir / filename
            if not path.exists():
                continue
            if write:
                path.unlink()
            else:
                self.error(
                    f"{filename} is not allowed after a hard-gate failure"
                )

    def validate_declared_failures(self) -> None:
        failures = self.data.get("declared_failures")
        if not isinstance(failures, list) or not failures:
            self.error("gate-data.declared_failures must be non-empty")
            return
        for index, failure in enumerate(failures):
            label = f"declared_failures[{index}]"
            if not isinstance(failure, dict):
                self.error(f"{label} is not an object")
                continue
            reject_extra(
                self,
                failure,
                {
                    "id",
                    "problem",
                    "evidence",
                    "owner",
                    "required_action",
                },
                label,
            )
            for field in ("id", "problem", "evidence", "required_action"):
                if not nonempty_string(failure.get(field), 8):
                    self.error(f"{label}.{field} is too small")
            if failure.get("owner") not in GATE_OWNERS:
                self.error(f"{label}.owner is invalid")
            self.block(
                f"declared gate failure {failure.get('id', index)}: "
                f"{failure.get('problem', 'unspecified')}"
            )

    def validate_existing_manifest(self) -> None:
        path = self.package_dir / "package-manifest.json"
        if not path.is_file():
            self.error("ready R1 package lacks package-manifest.json")
            return
        try:
            manifest = load_json(path)
        except (OSError, json.JSONDecodeError):
            self.error("package-manifest.json is invalid")
            return
        if not isinstance(manifest, dict):
            self.error("package-manifest.json root is not an object")
            return
        if (
            manifest.get("schema_version") != "1.0"
            or manifest.get("harness") != HARNESS
            or manifest.get("run_id") != self.data.get("run_id")
            or manifest.get("stage") != "R1"
            or manifest.get("verdict") != "ready"
        ):
            self.error("package manifest does not identify this ready R1 run")
        records = manifest.get("files")
        if not isinstance(records, list):
            self.error("package manifest files are invalid")
            return
        observed: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                self.error("package manifest contains an invalid record")
                continue
            filename = record.get("path")
            if filename not in PACKAGE_FILES or filename in observed:
                self.error("package manifest file set is invalid or duplicated")
                continue
            observed.add(filename)
            candidate = (self.package_dir / filename).resolve()
            if (
                self.package_dir not in candidate.parents
                or not candidate.is_file()
                or record.get("sha256") != sha256(candidate)
            ):
                self.error(f"manifest-bound file is missing or changed: {filename}")
        if observed != PACKAGE_FILES:
            self.error("package manifest must bind the complete execution package")
        validation = manifest.get("validation")
        validation_path = self.package_dir / "validation.json"
        if (
            not isinstance(validation, dict)
            or validation.get("path") != "validation.json"
            or not validation_path.is_file()
            or validation.get("sha256") != sha256(validation_path)
        ):
            self.error("package manifest does not bind validation.json")

    def validate_content_specificity(self) -> None:
        review_collections = (
            "control_area_reviews",
            "conception_reviews",
            "cross_domain_checks",
            "world_model_reviews",
            "major_event_reviews",
            "storyline_reviews",
            "storyline_demand_reviews",
            "storyline_architecture_review",
            "storyline_connection_reviews",
            "melody_line_reviews",
            "character_demand_reviews",
            "character_profile_reviews",
            "relationship_edge_reviews",
            "relationship_network_reviews",
            "development_gap_reviews",
            "design_decision_reviews",
            "tasks",
            "open_item_reviews",
        )
        placeholder_hits = []
        for name in review_collections:
            match = PLACEHOLDER_PATTERN.search(business_text(self.data.get(name)))
            if match:
                placeholder_hits.append(f"{name}:{match.group(0)}")
        if placeholder_hits:
            self.error(
                "content-specificity rejects placeholder review language: "
                + ", ".join(placeholder_hits)
            )

        repeated: dict[str, int] = {}
        for name in review_collections:
            value = self.data.get(name)
            if isinstance(value, dict):
                items = list(value.values())
            elif isinstance(value, list):
                items = value
            else:
                continue
            if name == "cross_domain_checks":
                # Assertions intentionally share a fixed executable shape.
                # Template detection must inspect the authored findings, not
                # punish the contract structure that makes them verifiable.
                items = [
                    {"finding": item.get("finding")}
                    for item in items
                    if isinstance(item, dict)
                ]
            if name in {"tasks"} or len(items) < 3:
                continue
            pairs = repeated_template_pairs(items)
            if pairs >= max(2, len(items) // 2):
                repeated[name] = pairs
                self.error(
                    f"content-specificity rejects repeated template findings in {name}"
                )
        tasks = self.data.get("tasks")
        if isinstance(tasks, list):
            task_pairs = repeated_field_templates(tasks, "response")
            if task_pairs:
                repeated["tasks.response"] = task_pairs
                self.error(
                    "content-specificity rejects majority same-field template "
                    "reuse in handoff task responses"
                )

        object_index: dict[str, Any] = {}

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                identifier = value.get("id")
                if isinstance(identifier, str):
                    object_index[identifier] = value
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)

        collect(self.map_data)
        corpus_objects: list[Any] = []
        for key in ("control_points", "development_gaps", "design_decisions", "units"):
            value = self.map_data.get(key)
            if isinstance(value, list):
                corpus_objects.extend(value)
        conception = self.map_data.get("conception")
        if isinstance(conception, dict):
            world = conception.get("world")
            story = conception.get("story")
            characters = conception.get("characters")
            if isinstance(world, dict):
                corpus_objects.append(world)
                for key in (
                    "facets",
                    "systems",
                    "environments",
                    "event_environment_requirements",
                ):
                    if isinstance(world.get(key), list):
                        corpus_objects.extend(world[key])
            if isinstance(story, dict):
                corpus_objects.append(story)
                for key in (
                    "phases",
                    "major_events",
                    "storylines",
                    "storyline_demands",
                    "melody_lines",
                ):
                    if isinstance(story.get(key), list):
                        corpus_objects.extend(story[key])
                architecture = story.get("storyline_architecture")
                if isinstance(architecture, dict):
                    corpus_objects.append(architecture)
                    if isinstance(
                        architecture.get("connection_points"), list
                    ):
                        corpus_objects.extend(
                            architecture["connection_points"]
                        )
            if isinstance(characters, dict):
                for key in ("demand_register", "profiles", "relationships"):
                    if isinstance(characters.get(key), list):
                        corpus_objects.extend(characters[key])
        token_frequency: dict[str, int] = {}
        for item in corpus_objects:
            for token in grounding_tokens(item):
                token_frequency[token] = token_frequency.get(token, 0) + 1
        rare_limit = max(2, len(corpus_objects) // 5)
        grounded_specs = (
            ("control_area_reviews", "control_ids"),
            ("conception_reviews", "subject_ids"),
            ("world_model_reviews", "subject_id"),
            ("major_event_reviews", "event_id"),
            ("storyline_reviews", "storyline_id"),
            ("storyline_demand_reviews", "demand_id"),
            ("storyline_connection_reviews", "connection_id"),
            ("melody_line_reviews", "melody_line_id"),
            ("character_demand_reviews", "demand_id"),
            ("character_profile_reviews", "character_id"),
            ("relationship_edge_reviews", "relationship_id"),
            ("relationship_network_reviews", "character_id"),
            ("development_gap_reviews", "gap_id"),
            ("design_decision_reviews", "decision_id"),
        )
        ungrounded: list[str] = []
        checked = 0
        for collection_name, id_field in grounded_specs:
            collection = self.data.get(collection_name)
            if not isinstance(collection, list):
                continue
            for index, review in enumerate(collection):
                if not isinstance(review, dict):
                    continue
                raw_ids = review.get(id_field)
                identifiers = raw_ids if isinstance(raw_ids, list) else [raw_ids]
                targets = [
                    object_index[item]
                    for item in identifiers
                    if isinstance(item, str) and item in object_index
                ]
                if not targets:
                    continue
                checked += 1
                target_tokens = grounding_tokens(targets)
                finding_tokens = grounding_tokens(review.get("finding"))
                overlap = target_tokens & finding_tokens
                rare_overlap = {
                    token
                    for token in overlap
                    if token_frequency.get(token, 0) <= rare_limit
                }
                if len(overlap) < 2 or not rare_overlap:
                    label = (
                        next(
                            (
                                str(review.get(key))
                                for key in (
                                    "subject_id",
                                    "storyline_id",
                                    "character_id",
                                    "relationship_id",
                                    "gap_id",
                                    "decision_id",
                                    "area",
                                )
                                if review.get(key)
                            ),
                            str(index),
                        )
                    )
                    ungrounded.append(f"{collection_name}:{label}")
        for label in ungrounded:
            self.error(
                f"content-specificity finding lacks story-grounded terms: {label}"
            )
        self.evidence["content_specificity"] = {
            "placeholder_hits": placeholder_hits,
            "repeated_template_pairs": repeated,
            "grounded_reviews_checked": checked,
            "ungrounded_reviews": ungrounded,
        }

    def run(
        self, *, write_outputs: bool = False, verify_manifest: bool = True
    ) -> dict[str, Any]:
        self.load_root()
        if not self.data:
            self.require_no_generated_outputs(write=write_outputs)
            return self.result()
        if self.data.get("schema_version") != "1.0":
            self.error("unsupported schema_version")
        if self.data.get("harness") != HARNESS:
            self.block("package belongs to another harness")
        if self.data.get("stage") != "R1":
            self.error("stage must be R1")
        if not nonempty_string(self.data.get("run_id")):
            self.block("run_id is missing")
        if self.mode == "review":
            execution_errors, execution_evidence = verify_record(
                self.package_dir,
                self.data,
            )
            self.errors.extend(execution_errors)
            self.evidence["autonomous_execution"] = execution_evidence
        if self.mode == "review":
            reject_extra(
                self,
                self.data,
                {
                    "schema_version",
                    "harness",
                    "run_id",
                    "stage",
                    "status",
                    "input_gate",
                    "reviewer",
                    "control_area_reviews",
                    "conception_reviews",
                    "cross_domain_checks",
                    "world_model_reviews",
                    "major_event_reviews",
                    "storyline_reviews",
                    "storyline_demand_reviews",
                    "storyline_architecture_review",
                    "storyline_connection_reviews",
                    "melody_line_reviews",
                    "character_demand_reviews",
                    "character_profile_reviews",
                    "relationship_edge_reviews",
                    "relationship_network_reviews",
                    "development_gap_reviews",
                    "design_decision_reviews",
                    "derivation_reviews",
                    "subject_ids",
                    "tasks",
                    "open_item_reviews",
                    "findings",
                    "return_request",
                },
                "review-data",
            )
        elif self.mode == "gate":
            reject_extra(
                self,
                self.data,
                {
                    "schema_version",
                    "harness",
                    "run_id",
                    "stage",
                    "status",
                    "input_gate",
                    "declared_failures",
                },
                "gate-data",
            )
        self.validate_input_gate()
        if self.mode == "gate":
            if self.data.get("status") != "blocked":
                self.error("gate-data status must be blocked")
            self.validate_declared_failures()
            self.require_no_generated_outputs(write=write_outputs)
            return self.result()

        if self.data.get("status") not in STATUSES:
            self.error("review-data status is invalid")
        if self.map_data:
            self.validate_reviewer()
            self.validate_control_areas()
            self.validate_conception_reviews()
            self.validate_three_domain_reviews()
            self.validate_cross_checks()
            self.validate_autonomous_development_reviews()
            self.validate_derivations_and_tasks()
            self.validate_open_items_and_findings()
            self.validate_status_and_return()
            self.validate_content_specificity()
            if self.blockers:
                self.require_no_generated_outputs(write=write_outputs)
            else:
                model_is_well_formed = not self.errors
                self.validate_or_write_outputs(
                    write=write_outputs,
                    include_handoff=(
                        model_is_well_formed
                        and self.data.get("status") == "ready"
                    ),
                    include_return=(
                        model_is_well_formed
                        and self.data.get("status") == "blocked"
                        and self.return_request_valid
                    ),
                )
        elif self.blockers:
            self.require_no_generated_outputs(write=write_outputs)
        result = self.result()
        if (
            verify_manifest
            and result["verdict"] == "ready"
            and not write_outputs
        ):
            self.validate_existing_manifest()
            result = self.result()
        return result


def render_blocked_report(data: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [
        "# 小说构思交接阻塞报告",
        "",
        f"- Run：`{data.get('run_id', '—')}`",
        "- 阶段：R1 硬准入",
        "- 结论：不得生成候选 NDB 或交接包。",
        "",
        "## 阻塞证据",
        "",
    ]
    for item in result.get("blockers", []):
        lines.append(f"- {item}")
    for finding in data.get("findings", []):
        if (
            isinstance(finding, dict)
            and finding.get("severity") == "blocked"
        ):
            lines.append(
                f"- `{finding.get('id', 'UNKNOWN')}` "
                f"{finding.get('problem', '—')}；责任 "
                f"`{finding.get('owner', '—')}`；动作 "
                f"{finding.get('required_action', '—')}"
            )
    lines.extend(["", "## 声明缺口", ""])
    for failure in data.get("declared_failures", []):
        if not isinstance(failure, dict):
            continue
        lines.extend(
            [
                f"### {failure.get('id', 'UNKNOWN')}",
                "",
                f"- 问题：{failure.get('problem', '—')}",
                f"- 证据：{failure.get('evidence', '—')}",
                f"- 责任：{failure.get('owner', '—')}",
                f"- 动作：{failure.get('required_action', '—')}",
                "",
            ]
        )
    lines.extend(["verdict: blocked", ""])
    return "\n".join(lines)


def write_manifest(package_dir: Path, data: dict[str, Any]) -> None:
    records = [
        {"path": filename, "sha256": sha256(package_dir / filename)}
        for filename in sorted(PACKAGE_FILES)
    ]
    validation_path = package_dir / "validation.json"
    manifest = {
        "schema_version": "1.0",
        "harness": HARNESS,
        "run_id": data.get("run_id"),
        "stage": "R1",
        "verdict": "ready",
        "files": records,
        "validation": {
            "path": "validation.json",
            "sha256": sha256(validation_path),
        },
        "author_review_artifact": {
            "path": "conception-review.md",
            "sha256": sha256(package_dir / "conception-review.md"),
        },
        "independent_handoff": {
            "path": "independent-handoff.json",
            "sha256": sha256(package_dir / "independent-handoff.json"),
        },
    }
    (package_dir / "package-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an R1 conception-review or blocked gate package."
    )
    parser.add_argument("package_directory", type=Path)
    parser.add_argument(
        "--write-validation",
        action="store_true",
        help="Regenerate deliverables, validation and ready manifest.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_dir = args.package_directory.resolve()
    review = Review(package_dir)
    result = review.run(
        write_outputs=args.write_validation,
        verify_manifest=not args.write_validation,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.write_validation:
        package_dir.mkdir(parents=True, exist_ok=True)
        validation_path = package_dir / "validation.json"
        validation_path.write_text(rendered + "\n", encoding="utf-8")
        manifest_path = package_dir / "package-manifest.json"
        if result["verdict"] == "ready" and review.mode == "review":
            write_manifest(package_dir, review.data)
            blocked_path = package_dir / "blocked-review-report.md"
            if blocked_path.exists():
                blocked_path.unlink()
        else:
            if manifest_path.exists():
                manifest_path.unlink()
            if result["verdict"] == "blocked":
                (package_dir / "blocked-review-report.md").write_text(
                    render_blocked_report(review.data, result),
                    encoding="utf-8",
                )
            else:
                blocked_path = package_dir / "blocked-review-report.md"
                if blocked_path.exists():
                    blocked_path.unlink()
    print(rendered)
    return 0 if result["verdict"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
