#!/usr/bin/env python3
"""Validate a hash-bound stage completion and its mandatory upstream evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

INTERVIEW_STAGES = {"I0", "I1", "I2", "I3", "I4", "I5"}
INTERVIEW_ORDER = ["I0", "I1", "I2", "I3", "I4", "I5"]
SEMANTIC_AREAS = {"intent": "I0", "subject": "I1", "world": "I2", "character": "I3", "causality": "I4", "narrative": "I5"}
ALLOWED_RETURN_TARGETS = {
    "I2": {"I0", "I1"}, "I3": {"I0", "I1", "I2"},
    "I4": {"I0", "I1", "I2", "I3"}, "I5": {"I0", "I1", "I2", "I4"},
    "V1": {"I0", "I1", "I2", "I3", "I4", "I5"},
    "V2": {"I0", "I1", "I2", "I3", "I4", "I5"},
}
REQUIRED_INPUT_STAGES = {
    "I0": [], "I1": ["I0"], "I2": ["I0", "I1"],
    "I3": ["I0", "I1", "I2"], "I4": ["I0", "I1", "I2", "I3"],
    "I5": ["I0", "I1", "I2", "I3", "I4"],
    "V1": ["I0", "I1", "I2", "I3", "I4", "I5"], "V2": ["V1"],
}
D1_PACKAGE_FILES = {
    "map-data.json",
    "generation-session.json",
    "generation-evidence/01-control-model.json",
    "generation-evidence/02-gap-and-options.json",
    "generation-evidence/03-story-architecture.json",
    "generation-evidence/04-event-world-model.json",
    "generation-evidence/05-character-model.json",
    "generation-evidence/06-final-map.json",
    "execution-record.json",
    "development-map.md",
    "coverage-matrix.md",
    "map-check.md",
    "validation.json",
}
R1_PACKAGE_FILES = {
    "review-data.json",
    "generation-session.json",
    "generation-evidence/01-review-plan.json",
    "generation-evidence/02-semantic-challenges.json",
    "generation-evidence/03-handoff-test.json",
    "generation-evidence/04-final-review.json",
    "execution-record.json",
    "novel-design-brief.md",
    "conception-review.md",
    "independent-handoff.json",
    "validation.json",
}
D1_VALIDATOR = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "novel-development-map-designer"
    / "scripts"
    / "validate_development_map.py"
)
R1_VALIDATOR = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "novel-conception-reviewer"
    / "scripts"
    / "validate_conception_review.py"
)
CONTROL_PROJECTION_VALIDATOR = Path(__file__).resolve().parent / "validate_control_projection.py"
FACT_DEPENDENCY_VALIDATOR = Path(__file__).resolve().parent / "validate_fact_dependency_register.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> int:
    print("FAIL: " + message)
    return 1


def load_hash_bound_reference(base: Path, reference, label: str):
    if not isinstance(reference, dict):
        return None, None, f"{label} is not a hash-bound reference"
    relative_path = reference.get("path")
    expected_hash = reference.get("sha256")
    if not isinstance(relative_path, str) or not relative_path or not isinstance(expected_hash, str):
        return None, None, f"{label} is not a hash-bound reference"
    relative = Path(relative_path)
    if relative.is_absolute():
        return None, None, f"{label} must use a relative path"
    candidate = (base / relative).resolve()
    if not candidate.is_file() or digest(candidate) != expected_hash:
        return None, None, f"{label} is missing or has changed"
    try:
        return candidate, load(candidate), None
    except json.JSONDecodeError:
        return None, None, f"{label} is invalid"


def valid_return_package(data, run_id: str, base: Path):
    origin = data.get("origin_stage")
    target = data.get("target_stage")
    valid = (
        data.get("harness") == "novel-conception-interview"
        and data.get("run_id") == run_id
        and data.get("status") == "active"
        and isinstance(data.get("evidence"), list) and bool(data["evidence"])
        and all(
            isinstance(item, str) and item.strip()
            for item in data["evidence"]
        )
        and isinstance(data.get("requested_decision"), str)
        and bool(data["requested_decision"].strip())
        and isinstance(data.get("affected_artifacts"), list) and bool(data["affected_artifacts"])
        and all(
            isinstance(item, str) and item.strip()
            for item in data["affected_artifacts"]
        )
        and target in ALLOWED_RETURN_TARGETS.get(origin, set())
    )
    if valid and origin == "V2":
        _, approval, error = load_hash_bound_reference(base, data.get("author_approval"), "V2 revision author approval")
        valid = not error and approval.get("harness") == "novel-conception-interview" and approval.get("run_id") == run_id and approval.get("approval_scope") == "V2" and approval.get("decision") == "revise" and approval.get("record_assurance") == "self_recorded"
    return valid, target


def validate_d1_package_manifest(
    manifest_path: Path,
    manifest,
    run_id: str,
    validation_path: Path,
    validation_hash: str,
):
    if not isinstance(manifest, dict):
        return "D1 package manifest root is not an object"
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("harness") != "novel-conception-interview"
        or manifest.get("run_id") != run_id
        or manifest.get("stage") != "D1"
        or manifest.get("verdict") != "ready"
    ):
        return "D1 package manifest does not identify a ready package for this run"
    records = manifest.get("files")
    if not isinstance(records, list):
        return "D1 package manifest files are invalid"
    observed = {}
    for record in records:
        if not isinstance(record, dict):
            return "D1 package manifest contains an invalid file record"
        name = record.get("path")
        expected_hash = record.get("sha256")
        if (
            name not in D1_PACKAGE_FILES
            or name in observed
            or not isinstance(expected_hash, str)
        ):
            return "D1 package manifest file set is invalid or duplicated"
        candidate = (manifest_path.parent / name).resolve()
        if (
            manifest_path.parent not in candidate.parents
            or not candidate.is_file()
        ):
            return f"D1 package file is missing or escapes its package: {name}"
        if digest(candidate) != expected_hash:
            return f"D1 package file has changed: {name}"
        observed[name] = (candidate, expected_hash)
    if set(observed) != D1_PACKAGE_FILES:
        return "D1 package manifest must bind the complete execution package"
    validation_record = manifest.get("validation")
    if (
        not isinstance(validation_record, dict)
        or validation_record.get("path") != "validation.json"
        or validation_record.get("sha256") != validation_hash
        or observed["validation.json"][0] != validation_path
        or observed["validation.json"][1] != validation_hash
    ):
        return "D1 package manifest is not bound to completion validation evidence"
    return None


def validate_r1_package_manifest(
    manifest_path: Path,
    manifest,
    run_id: str,
    validation_path: Path,
    validation_hash: str,
):
    if not isinstance(manifest, dict):
        return "R1 package manifest root is not an object"
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("harness") != "novel-conception-interview"
        or manifest.get("run_id") != run_id
        or manifest.get("stage") != "R1"
        or manifest.get("verdict") != "ready"
    ):
        return "R1 package manifest does not identify a ready package for this run"
    records = manifest.get("files")
    if not isinstance(records, list):
        return "R1 package manifest files are invalid"
    observed = {}
    for record in records:
        if not isinstance(record, dict):
            return "R1 package manifest contains an invalid file record"
        name = record.get("path")
        expected_hash = record.get("sha256")
        if (
            name not in R1_PACKAGE_FILES
            or name in observed
            or not isinstance(expected_hash, str)
        ):
            return "R1 package manifest file set is invalid or duplicated"
        candidate = (manifest_path.parent / name).resolve()
        if (
            manifest_path.parent not in candidate.parents
            or not candidate.is_file()
        ):
            return f"R1 package file is missing or escapes its package: {name}"
        if digest(candidate) != expected_hash:
            return f"R1 package file has changed: {name}"
        observed[name] = (candidate, expected_hash)
    if set(observed) != R1_PACKAGE_FILES:
        return "R1 package manifest must bind the complete execution package"
    validation_record = manifest.get("validation")
    if (
        not isinstance(validation_record, dict)
        or validation_record.get("path") != "validation.json"
        or validation_record.get("sha256") != validation_hash
        or observed["validation.json"][0] != validation_path
        or observed["validation.json"][1] != validation_hash
    ):
        return "R1 package manifest is not bound to completion validation evidence"
    for field, filename in (
        ("author_review_artifact", "conception-review.md"),
        ("independent_handoff", "independent-handoff.json"),
    ):
        record = manifest.get(field)
        if (
            not isinstance(record, dict)
            or record.get("path") != filename
            or record.get("sha256") != observed[filename][1]
        ):
            return f"R1 package manifest has an invalid {field} reference"
    return None


def reference_identity(base: Path, reference):
    if not isinstance(reference, dict):
        return None
    path = reference.get("path")
    sha = reference.get("sha256")
    if not isinstance(path, str) or not path or not isinstance(sha, str):
        return None
    relative = Path(path)
    if relative.is_absolute():
        return None
    return ((base / relative).resolve(), sha.lower())


def validate_d1_input_binding(
    map_path: Path,
    map_data,
    packet_path: Path,
    packet,
    input_references,
):
    if not isinstance(map_data, dict):
        return "D1 map-data root is not an object"
    gate = map_data.get("input_gate")
    if not isinstance(gate, dict):
        return "D1 map-data lacks input_gate"
    packet_base = packet_path.parent
    map_base = map_path.parent
    if reference_identity(map_base, gate.get("run_state")) != reference_identity(
        packet_base, packet.get("run_state")
    ):
        return "D1 completion and map-data bind different run-state records"
    interviews = gate.get("interview_completions")
    if not isinstance(interviews, list) or len(interviews) != len(INTERVIEW_ORDER):
        return "D1 map-data must bind exactly the six current interview completions"
    observed = {}
    for reference in interviews:
        if not isinstance(reference, dict):
            return "D1 map-data contains an invalid interview completion reference"
        stage = reference.get("stage")
        if stage not in INTERVIEW_STAGES or stage in observed:
            return "D1 map-data interview completion stages are invalid or duplicated"
        observed[stage] = reference
    for stage in INTERVIEW_ORDER:
        if reference_identity(map_base, observed.get(stage)) != reference_identity(
            packet_base, input_references.get(stage)
        ):
            return f"D1 completion and map-data bind different {stage} completions"
    for stage, field in (("V1", "v1_completion"), ("V2", "v2_completion")):
        if reference_identity(map_base, gate.get(field)) != reference_identity(
            packet_base, input_references.get(stage)
        ):
            return f"D1 completion and map-data bind different {stage} completions"
    if reference_identity(map_base, gate.get("author_approval")) != reference_identity(
        packet_base, packet.get("author_approval")
    ):
        return "D1 completion and map-data bind different author approval records"
    return None


def canonical_d1_validation(package_dir: Path):
    if not D1_VALIDATOR.is_file():
        return None, "canonical D1 validator is unavailable"
    try:
        process = subprocess.run(
            [sys.executable, str(D1_VALIDATOR), str(package_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None, "canonical D1 validation timed out"
    except OSError as exc:
        return None, f"canonical D1 validation could not run: {exc}"
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError:
        detail = process.stderr.strip() or process.stdout.strip() or "no output"
        return None, "canonical D1 validator returned invalid output: " + detail
    if process.returncode != 0:
        return result, "canonical D1 validation did not pass"
    return result, None


def canonical_r1_validation(package_dir: Path):
    if not R1_VALIDATOR.is_file():
        return None, "canonical R1 validator is unavailable"
    try:
        process = subprocess.run(
            [sys.executable, str(R1_VALIDATOR), str(package_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, "canonical R1 validation timed out"
    except OSError as exc:
        return None, f"canonical R1 validation could not run: {exc}"
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError:
        detail = process.stderr.strip() or process.stdout.strip() or "no output"
        return None, "canonical R1 validator returned invalid output: " + detail
    if process.returncode != 0:
        return result, "canonical R1 validation did not pass"
    return result, None


def validate_ready_completion(completion_path: Path):
    try:
        process = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), str(completion_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "upstream completion validation timed out"
    except OSError as exc:
        return f"upstream completion validation could not run: {exc}"
    if process.returncode != 0:
        return (
            "upstream completion failed canonical validation: "
            + (process.stdout or process.stderr).strip()
        )
    return None


def validate_bound_contract_artifact(
    owner_path: Path,
    reference,
    *,
    label: str,
    validator_path: Path,
):
    artifact_path, data, reference_error = load_hash_bound_reference(
        owner_path.parent, reference, label
    )
    if reference_error:
        return None, None, reference_error
    if not validator_path.is_file():
        return None, None, f"{label} validator is unavailable"
    try:
        process = subprocess.run(
            [sys.executable, str(validator_path), str(artifact_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None, None, f"{label} validation timed out"
    except OSError as exc:
        return None, None, f"{label} validation could not run: {exc}"
    if process.returncode != 0:
        detail = (process.stdout or process.stderr).strip() or "no diagnostic"
        return None, None, f"{label} failed canonical validation: {detail}"
    return artifact_path, data, None


def validate_independent_handoff(
    handoff,
    run_id: str,
    handoff_path: Path,
    d1_completion_path: Path,
    d1_completion,
):
    if not isinstance(handoff, dict):
        return "R1 independent handoff root is not an object"
    if (
        handoff.get("schema_version") != "1.0"
        or handoff.get("harness") != "novel-conception-interview"
        or handoff.get("run_id") != run_id
        or handoff.get("stage") != "R1"
        or handoff.get("verdict") != "pass"
        or handoff.get("reviewer_role") != "independent_developer"
        or handoff.get("assurance") != "role_separated_execution"
        or handoff.get("evidence_scope") != "d1_package_only"
    ):
        return (
            "R1 independent handoff does not identify a passing "
            "role-separated execution"
        )
    reviewer_id = handoff.get("reviewer_id")
    method = handoff.get("method")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        return "R1 independent handoff lacks reviewer_id"
    if not isinstance(method, str) or len(method.strip()) < 20:
        return "R1 independent handoff method is not auditable"
    d1_manifest = (
        d1_completion_path.parent / d1_completion.get("design_artifact", "")
    ).resolve()
    if reference_identity(handoff_path.parent, handoff.get("d1_package")) != (
        d1_manifest,
        str(d1_completion.get("design_artifact_sha256", "")).lower(),
    ):
        return "R1 independent handoff is not bound to the validated D1 package"
    try:
        map_data = load(d1_manifest.parent / "map-data.json")
    except (OSError, json.JSONDecodeError):
        return "R1 independent handoff cannot read the validated D1 map-data"
    if not isinstance(map_data, dict) or map_data.get("schema_version") != "4.0":
        return "R1 independent handoff requires D1 map-data schema 4.0"
    controls = {
        item.get("id")
        for item in map_data.get("control_points", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    units = {
        item.get("id")
        for item in map_data.get("units", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    obligations = {
        item.get("id")
        for item in map_data.get("information_obligations", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    gaps = {
        item.get("id")
        for item in map_data.get("development_gaps", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    decisions = {
        item.get("id"): item
        for item in map_data.get("design_decisions", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    derivations = {
        item.get("id"): item
        for item in map_data.get("derivation_claims", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    conception = (
        map_data.get("conception")
        if isinstance(map_data.get("conception"), dict)
        else {}
    )
    conception_ids = set()
    for field in ("world", "story"):
        item = conception.get(field)
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            conception_ids.add(item["id"])
    world = conception.get("world")
    world_records = {}
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
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    conception_ids.add(item["id"])
                    world_records[item["id"]] = (subject_type, item)
    story = conception.get("story")
    if isinstance(story, dict):
        conception_ids.update(
            item["id"]
            for item in story.get("phases", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        )
        major_events = {
            item["id"]: item
            for item in story.get("major_events", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        conception_ids.update(major_events)
        storylines = {
            item["id"]: item
            for item in story.get("storylines", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        conception_ids.update(storylines)
        conception_ids.update(
            item["id"]
            for item in story.get("storyline_demands", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        )
        architecture = story.get("storyline_architecture")
        if isinstance(architecture, dict):
            if isinstance(architecture.get("id"), str):
                conception_ids.add(architecture["id"])
            conception_ids.update(
                item["id"]
                for item in architecture.get("connection_points", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            )
    else:
        major_events = {}
        storylines = {}
    character_model = (
        conception.get("characters")
        if isinstance(conception.get("characters"), dict)
        else {}
    )
    character_records = {
        item["id"]: item
        for item in character_model.get("profiles", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    relationship_records = {
        item["id"]: item
        for item in character_model.get("relationships", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    demand_records = {
        item["id"]: item
        for item in character_model.get("demand_register", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    conception_ids.update(demand_records)
    conception_ids.update(character_records)
    conception_ids.update(relationship_records)
    self_test = map_data.get("handoff_self_test")
    if (
        isinstance(self_test, dict)
        and self_test.get("reviewer_id") == reviewer_id
    ):
        return "R1 reviewer_id must differ from the D1 self-test executor"
    subject_ids = handoff.get("subject_ids")
    if (
        not isinstance(subject_ids, list)
        or not all(isinstance(item, str) and item.strip() for item in subject_ids)
        or len(subject_ids) != len(set(subject_ids))
        or set(subject_ids) != units
    ):
        return "R1 independent handoff subject_ids must exactly cover all D1 units"
    world_reviews = handoff.get("world_model_reviews")
    if not isinstance(world_reviews, list):
        return "R1 independent handoff world_model_reviews are invalid"
    reviewed_world = set()
    for review in world_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid world review"
        subject_id = review.get("subject_id")
        expected = world_records.get(subject_id)
        if (
            expected is None
            or subject_id in reviewed_world
            or review.get("subject_type") != expected[0]
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 40
            or review.get("decision_ids")
            != expected[1].get("development_decisions")
        ):
            return f"R1 independent handoff world review is invalid: {subject_id}"
        reviewed_world.add(subject_id)
    if reviewed_world != set(world_records):
        return (
            "R1 independent handoff must review every world facet, "
            "system, environment and event-environment requirement"
        )
    major_event_reviews = handoff.get("major_event_reviews")
    if not isinstance(major_event_reviews, list):
        return "R1 independent handoff major_event_reviews are invalid"
    reviewed_major_events = set()
    event_source_coverage = story.get("event_source_coverage", [])
    expected_event_source_ids = {
        event_id: [
            item.get("id")
            for item in event_source_coverage
            if isinstance(item, dict)
            and event_id in item.get("major_event_ids", [])
        ]
        for event_id in major_events
    }
    for review in major_event_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid major event review"
        event_id = review.get("event_id")
        expected = major_events.get(event_id)
        if (
            expected is None
            or event_id in reviewed_major_events
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 40
            or any(
                review.get(field) != expected.get(field)
                for field in (
                    "storyline_ids",
                    "unit_ids",
                    "environment_ids",
                    "participant_ids",
                )
            )
            or review.get("decision_ids")
            != expected.get("development_decisions")
            or review.get("source_coverage_ids")
            != expected_event_source_ids.get(event_id)
        ):
            return (
                "R1 independent handoff major event review is invalid: "
                f"{event_id}"
            )
        reviewed_major_events.add(event_id)
    if reviewed_major_events != set(major_events):
        return "R1 independent handoff must review every major event"
    storyline_reviews = handoff.get("storyline_reviews")
    if not isinstance(storyline_reviews, list):
        return "R1 independent handoff storyline_reviews are invalid"
    reviewed_storylines = set()
    for review in storyline_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid storyline review"
        storyline_id = review.get("storyline_id")
        expected = storylines.get(storyline_id)
        if (
            expected is None
            or storyline_id in reviewed_storylines
            or review.get("type") != expected.get("type")
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 40
            or review.get("unit_ids") != expected.get("unit_ids")
            or review.get("decision_ids")
            != expected.get("development_decisions")
        ):
            return (
                "R1 independent handoff storyline review is invalid: "
                f"{storyline_id}"
            )
        reviewed_storylines.add(storyline_id)
    if reviewed_storylines != set(storylines):
        return "R1 independent handoff must review every storyline"
    demand_reviews = handoff.get("character_demand_reviews")
    if not isinstance(demand_reviews, list):
        return "R1 independent handoff character_demand_reviews are invalid"
    reviewed_demands = set()
    for review in demand_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid character demand review"
        demand_id = review.get("demand_id")
        expected = demand_records.get(demand_id)
        if (
            expected is None
            or demand_id in reviewed_demands
            or review.get("category") != expected.get("category")
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 60
            or review.get("resolution") != expected.get("resolution")
            or review.get("profile_id") != expected.get("profile_id")
            or review.get("decision_ids")
            != expected.get("development_decisions")
        ):
            return (
                "R1 independent handoff character demand review is invalid: "
                f"{demand_id}"
            )
        reviewed_demands.add(demand_id)
    if reviewed_demands != set(demand_records):
        return "R1 independent handoff must review every character demand"
    profile_reviews = handoff.get("character_profile_reviews")
    if not isinstance(profile_reviews, list):
        return "R1 independent handoff character_profile_reviews are invalid"
    reviewed_profiles = set()
    for review in profile_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid character profile review"
        character_id = review.get("character_id")
        expected = character_records.get(character_id)
        if (
            expected is None
            or character_id in reviewed_profiles
            or review.get("importance") != expected.get("importance")
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 50
            or review.get("decision_ids")
            != expected.get("development_decisions")
        ):
            return (
                "R1 independent handoff character profile review is invalid: "
                f"{character_id}"
            )
        reviewed_profiles.add(character_id)
    if reviewed_profiles != set(character_records):
        return "R1 independent handoff must review every canonical character profile"
    edge_reviews = handoff.get("relationship_edge_reviews")
    if not isinstance(edge_reviews, list):
        return "R1 independent handoff relationship_edge_reviews are invalid"
    reviewed_edges = set()
    for review in edge_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid relationship edge review"
        relationship_id = review.get("relationship_id")
        expected = relationship_records.get(relationship_id)
        if (
            expected is None
            or relationship_id in reviewed_edges
            or review.get("source_id") != expected.get("source_id")
            or review.get("target_id") != expected.get("target_id")
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 50
            or review.get("decision_ids")
            != expected.get("development_decisions")
        ):
            return (
                "R1 independent handoff relationship edge review is invalid: "
                f"{relationship_id}"
            )
        reviewed_edges.add(relationship_id)
    if reviewed_edges != set(relationship_records):
        return "R1 independent handoff must review every canonical relationship edge"
    network_reviews = handoff.get("relationship_network_reviews")
    if not isinstance(network_reviews, list):
        return "R1 independent handoff relationship reviews are invalid"
    reviewed_characters = set()
    for review in network_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains invalid relationship review"
        character_id = review.get("character_id")
        character = character_records.get(character_id)
        if (
            character is None
            or character.get("importance") != "core"
            or character_id in reviewed_characters
        ):
            return f"R1 independent handoff relationship review is invalid: {character_id}"
        adjacency = {item_id: set() for item_id in character_records}
        for edge in relationship_records.values():
            source_id = edge.get("source_id")
            target_id = edge.get("target_id")
            if source_id in adjacency and target_id in adjacency:
                adjacency[source_id].add(target_id)
                adjacency[target_id].add(source_id)
        distances = {character_id: 0}
        queue = [character_id]
        for current in queue:
            for neighbor in sorted(adjacency[current]):
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
        expected_layers = {}
        for node_id, distance in distances.items():
            if distance:
                expected_layers.setdefault(str(distance), []).append(node_id)
        expected_layers = {
            level: sorted(node_ids)
            for level, node_ids in sorted(
                expected_layers.items(), key=lambda item: int(item[0])
            )
        }
        expected_profile_ids = [
            node_id
            for level in sorted(expected_layers, key=int)
            for node_id in expected_layers[level]
        ]
        component_ids = set(distances)
        expected_relation_ids = [
            relationship_id
            for relationship_id, edge in relationship_records.items()
            if edge.get("source_id") in component_ids
            and edge.get("target_id") in component_ids
        ]
        if (
            review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 50
            or review.get("max_depth") != max(distances.values(), default=0)
            or review.get("layer_character_ids") != expected_layers
            or review.get("profiled_character_ids") != expected_profile_ids
            or review.get("relationship_ids") != expected_relation_ids
        ):
            return f"R1 independent handoff relationship review is invalid: {character_id}"
        reviewed_characters.add(character_id)
    expected_core_ids = {
        character_id
        for character_id, record in character_records.items()
        if record.get("importance") == "core"
    }
    if reviewed_characters != expected_core_ids:
        return "R1 independent handoff must review every core relationship network"
    gap_reviews = handoff.get("development_gap_reviews")
    if not isinstance(gap_reviews, list):
        return "R1 independent handoff development_gap_reviews are invalid"
    reviewed_gaps = {
        item.get("gap_id")
        for item in gap_reviews
        if isinstance(item, dict)
        and item.get("status") == "pass"
        and isinstance(item.get("finding"), str)
        and len(item["finding"].strip()) >= 30
    }
    if reviewed_gaps != gaps or len(gap_reviews) != len(gaps):
        return "R1 independent handoff must review every D1 development gap"
    decision_reviews = handoff.get("design_decision_reviews")
    if not isinstance(decision_reviews, list):
        return "R1 independent handoff design_decision_reviews are invalid"
    reviewed_decisions = set()
    required_dimensions = {
        "necessity",
        "compatibility",
        "causal_utility",
        "specificity",
        "author_boundary",
        "downstream_freedom",
    }
    for review in decision_reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains an invalid design decision review"
        decision_id = review.get("decision_id")
        decision = decisions.get(decision_id)
        if (
            decision is None
            or decision_id in reviewed_decisions
            or review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 40
            or review.get("gap_ids") != decision.get("gap_ids")
            or review.get("source_control_ids") != decision.get("source_controls")
            or not isinstance(review.get("dimensions"), dict)
            or set(review["dimensions"]) != required_dimensions
            or any(value != "pass" for value in review["dimensions"].values())
        ):
            return (
                "R1 independent handoff design decision review is not auditable: "
                f"{decision_id}"
            )
        reviewed_decisions.add(decision_id)
    if reviewed_decisions != set(decisions):
        return "R1 independent handoff must review every D1 design decision"
    reviews = handoff.get("derivation_reviews")
    if not isinstance(reviews, list):
        return "R1 independent handoff derivation_reviews are invalid"
    reviewed = set()
    for review in reviews:
        if not isinstance(review, dict):
            return "R1 independent handoff contains an invalid derivation review"
        derivation_id = review.get("derivation_id")
        if not isinstance(derivation_id, str) or not derivation_id:
            return "R1 independent handoff contains an invalid derivation id"
        if derivation_id in reviewed:
            return "R1 independent handoff contains duplicate derivation reviews"
        reviewed.add(derivation_id)
        claim = derivations.get(derivation_id)
        if claim is None:
            return (
                "R1 independent handoff reviews an unknown derivation: "
                f"{derivation_id}"
            )
        if (
            review.get("status") != "pass"
            or not isinstance(review.get("finding"), str)
            or len(review["finding"].strip()) < 20
            or review.get("source_control_ids") != claim.get("source_controls")
            or review.get("source_decision_ids", [])
            != claim.get("source_decisions", [])
        ):
            return (
                "R1 independent handoff derivation review is not auditable: "
                f"{derivation_id}"
            )
    if reviewed != set(derivations):
        return "R1 independent handoff must review every D1 derivation claim"
    tasks = handoff.get("tasks")
    if not isinstance(tasks, list):
        return "R1 independent handoff tasks are invalid"
    required = {
        "promise",
        "autonomous_value",
        "causal_chain",
        "unit_contract",
        "freedom_boundary",
        "drift_detection",
        "easy_solution",
        "scene_plan",
    }
    valid_evidence_ids = (
        controls
        | units
        | obligations
        | gaps
        | set(decisions)
        | set(derivations)
        | conception_ids
    )
    observed = set()
    for task in tasks:
        if not isinstance(task, dict):
            return "R1 independent handoff contains an invalid task"
        task_id = task.get("id")
        if task_id in observed:
            return "R1 independent handoff contains duplicate tasks"
        observed.add(task_id)
        if (
            task.get("status") != "pass"
            or not isinstance(task.get("response"), str)
            or len(task["response"].strip()) < 40
            or not isinstance(task.get("evidence_ids"), list)
            or not task["evidence_ids"]
            or not all(
                isinstance(item, str) and item.strip()
                for item in task["evidence_ids"]
            )
        ):
            return f"R1 independent handoff task is not auditable: {task_id}"
        unknown_ids = set(task["evidence_ids"]) - valid_evidence_ids
        if unknown_ids:
            return (
                f"R1 independent handoff task cites unknown evidence: {task_id}: "
                + ", ".join(sorted(unknown_ids))
            )
    if observed != required:
        return "R1 independent handoff must contain exactly the eight required tasks"
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_stage_completion.py <stage-completion.json>", file=sys.stderr)
        return 2
    packet_path = Path(argv[1]).resolve()
    try:
        packet = load(packet_path)
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"invalid completion packet: {exc}")
    required = {"harness", "run_id", "stage", "session_id", "status", "design_artifact", "design_artifact_sha256", "validation", "input_completions", "run_state"}
    if missing := required - set(packet):
        return fail("missing completion fields: " + ", ".join(sorted(missing)))
    if packet["harness"] != "novel-conception-interview" or packet["status"] != "ready":
        return fail("completion is not a ready packet for this harness")
    if packet["stage"] in {"D1", "R1"}:
        return fail("legacy D1/R1 stage is not part of the current interview contract")
    if packet["stage"] not in REQUIRED_INPUT_STAGES:
        return fail("unknown stage")
    state = packet.get("run_state", {})
    state_path = (packet_path.parent / state.get("path", "")).resolve()
    if not state_path.is_file() or digest(state_path) != state.get("sha256"):
        return fail("completion lacks hash-bound run state")
    try:
        state_data = load(state_path)
    except json.JSONDecodeError:
        return fail("run state is invalid")
    if state_data.get("harness") != "novel-conception-interview" or state_data.get("run_id") != packet["run_id"]:
        return fail("run state belongs to another conception run")
    active_return = state_data.get("active_return")
    if active_return is not None:
        _, return_data, error = load_hash_bound_reference(state_path.parent, active_return, "active return package")
        if error:
            return fail(error)
        valid_return, target = valid_return_package(return_data, packet["run_id"], state_path.parent)
        if not valid_return:
            return fail("active return package violates the bounded return contract")
        prior_rounds = 0
        for resolved in state_data.get("resolved_returns", []):
            _, prior_return, prior_error = load_hash_bound_reference(state_path.parent, resolved.get("return") if isinstance(resolved, dict) else None, "resolved return package")
            if prior_error:
                return fail(prior_error)
            if prior_return.get("origin_stage") == return_data.get("origin_stage"):
                prior_rounds += 1
        if prior_rounds >= 2:
            return fail("return-round limit reached; author direction is required")
        resolution = packet.get("return_resolution")
        if packet["stage"] != target:
            return fail("an active return package blocks further handoff")
        if reference_identity(
            packet_path.parent, resolution
        ) != reference_identity(state_path.parent, active_return):
            return fail("the return target must hash-bind the active return package")
    artifact = (packet_path.parent / packet["design_artifact"]).resolve()
    validation = (packet_path.parent / packet["validation"].get("path", "")).resolve()
    if not artifact.is_file() or digest(artifact) != packet["design_artifact_sha256"]:
        return fail("design artifact is missing or has changed")
    if packet["validation"].get("verdict") != "ready" or not validation.is_file() or digest(validation) != packet["validation"].get("sha256"):
        return fail("validation evidence is missing or has changed")
    try:
        validation_data = load(validation)
    except json.JSONDecodeError as exc:
        return fail(f"invalid validation evidence: {exc}")
    if validation_data.get("verdict") != "ready" or validation_data.get("run_id") != packet["run_id"]:
        return fail("validation evidence is not ready for this conception run")
    if packet["stage"] in INTERVIEW_STAGES:
        if packet.get("contract_version") != "2.0":
            return fail("interview completion must use contract_version 2.0")
        report = packet.get("report", {})
        report_path = (packet_path.parent / report.get("path", "")).resolve()
        if not report_path.is_file() or digest(report_path) != report.get("sha256"):
            return fail("interview completion lacks the current rendered report")
        projection_path, projection_data, projection_error = (
            validate_bound_contract_artifact(
                packet_path,
                packet.get("control_projection"),
                label="interview control projection",
                validator_path=CONTROL_PROJECTION_VALIDATOR,
            )
        )
        if projection_error:
            return fail(projection_error)
        if (
            projection_data.get("run_id") != packet["run_id"]
            or projection_data.get("stage") != packet["stage"]
            or projection_data.get("session_id") != packet["session_id"]
            or reference_identity(
                projection_path.parent, projection_data.get("source_artifact")
            )
            != (artifact, packet["design_artifact_sha256"])
        ):
            return fail(
                "interview control projection is not bound to this completion and design artifact"
            )
    if packet["stage"] == "V1":
        if packet.get("contract_version") != "2.0":
            return fail("V1 completion must use contract_version 2.0")
        _, fact_data, fact_error = validate_bound_contract_artifact(
            packet_path,
            packet.get("fact_dependency_register"),
            label="V1 fact-dependency register",
            validator_path=FACT_DEPENDENCY_VALIDATOR,
        )
        if fact_error:
            return fail(fact_error)
        if fact_data.get("run_id") != packet["run_id"]:
            return fail("V1 fact-dependency register belongs to another run")
    seen = []
    upstream_packets = []
    input_references = {}
    for reference in packet["input_completions"]:
        input_path, upstream, error = load_hash_bound_reference(packet_path.parent, reference, "input completion")
        if error:
            return fail(error)
        if upstream.get("harness") != "novel-conception-interview" or upstream.get("status") != "ready":
            return fail(f"input completion is not ready: {reference.get('path', '<unknown>')}")
        if upstream.get("run_id") != packet["run_id"]:
            return fail(f"input completion belongs to another run: {reference.get('path', '<unknown>')}")
        upstream_stage = upstream.get("stage")
        if upstream_stage in input_references:
            return fail(f"duplicate input completion stage: {upstream_stage}")
        seen.append(upstream_stage)
        input_references[upstream_stage] = reference
        upstream_packets.append((input_path, upstream))
    missing_inputs = set(REQUIRED_INPUT_STAGES[packet["stage"]]) - set(seen)
    if missing_inputs:
        return fail("stage bypasses required inputs: " + ", ".join(sorted(missing_inputs)))
    if packet["stage"] == "V1":
        for input_path, upstream in upstream_packets:
            if upstream.get("stage") not in INTERVIEW_STAGES:
                continue
            upstream_error = validate_ready_completion(input_path)
            if upstream_error:
                return fail(
                    f"V1 cannot consume {upstream.get('stage')}: {upstream_error}"
                )
    if packet["stage"] == "D1" and set(seen) != set(REQUIRED_INPUT_STAGES["D1"]):
        return fail("D1 input completions must be exactly current I0-I5, V1 and V2")
    current_interviews = state_data.get("current_interview_completions", {})
    if not isinstance(current_interviews, dict):
        return fail("run state current_interview_completions is invalid")
    for required_stage in REQUIRED_INPUT_STAGES[packet["stage"]]:
        if required_stage in INTERVIEW_STAGES and input_references.get(required_stage) != current_interviews.get(required_stage):
            return fail(f"stage does not consume the current {required_stage} completion")
    for resolved in state_data.get("resolved_returns", []):
        if not isinstance(resolved, dict):
            return fail("run state has an invalid resolved return")
        _, return_data, error = load_hash_bound_reference(state_path.parent, resolved.get("return"), "resolved return package")
        completion_path, completion_data, completion_error = load_hash_bound_reference(state_path.parent, resolved.get("target_completion"), "resolved return target completion")
        if error:
            return fail(error)
        if completion_error:
            return fail(completion_error)
        valid_return, target = valid_return_package(return_data, packet["run_id"], state_path.parent)
        resolution = completion_data.get("return_resolution")
        completion_state_path, completion_state, completion_state_error = load_hash_bound_reference(completion_path.parent, completion_data.get("run_state"), "resolved return target run state")
        if completion_state_error:
            return fail(completion_state_error)
        resolved_return_identity = reference_identity(
            state_path.parent, resolved.get("return")
        )
        if not valid_return or completion_data.get("harness") != "novel-conception-interview" or completion_data.get("run_id") != packet["run_id"] or completion_data.get("stage") != target or completion_data.get("status") != "ready" or reference_identity(completion_path.parent, resolution) != resolved_return_identity or completion_state.get("harness") != "novel-conception-interview" or completion_state.get("run_id") != packet["run_id"] or reference_identity(completion_state_path.parent, completion_state.get("active_return")) != resolved_return_identity:
            return fail("resolved return does not prove a corrected target completion")
        if not any(path == completion_path for path, _ in upstream_packets):
            return fail("resolved return requires its corrected target completion as input")
        if target in INTERVIEW_STAGES:
            target_index = INTERVIEW_ORDER.index(target)
            for later_stage in INTERVIEW_ORDER[target_index + 1:]:
                current_reference = current_interviews.get(later_stage)
                if current_reference is None:
                    continue
                _, later_completion, later_error = load_hash_bound_reference(state_path.parent, current_reference, f"current {later_stage} completion")
                if later_error:
                    return fail(later_error)
                target_identity = reference_identity(
                    state_path.parent, resolved.get("target_completion")
                )
                later_inputs = {
                    reference_identity(
                        (state_path.parent / current_reference.get("path", "")).resolve().parent,
                        item,
                    )
                    for item in later_completion.get("input_completions", [])
                    if isinstance(item, dict)
                }
                if later_completion.get("stage") != later_stage or target_identity not in later_inputs:
                    return fail(f"current {later_stage} completion is stale after the resolved return")
    v1_packets = [item for item in upstream_packets if item[1].get("stage") == "V1"]
    if packet["stage"] == "V1":
        v1_packets = [(packet_path, packet)]
    if packet["stage"] in {"V1", "V2"}:
        if not v1_packets:
            return fail("semantic integrity evidence has no V1 completion")
        semantic = v1_packets[0][1].get("semantic_review", {})
        semantic_path = (v1_packets[0][0].parent / semantic.get("path", "")).resolve()
        if not semantic_path.is_file() or digest(semantic_path) != semantic.get("sha256"):
            return fail("V1 semantic integrity evidence is missing or has changed")
        try:
            semantic_data = load(semantic_path)
        except json.JSONDecodeError:
            return fail("V1 semantic integrity evidence is invalid")
        evidence = semantic_data.get("evidence")
        if semantic_data.get("harness") != "novel-conception-interview" or semantic_data.get("run_id") != packet["run_id"] or semantic_data.get("stage") != "V1" or semantic_data.get("verdict") != "pass" or semantic_data.get("reviewer_role") != "integrity_auditor" or semantic_data.get("return_package") is not None or not isinstance(evidence, list) or len(evidence) != len(SEMANTIC_AREAS):
            return fail("V1 semantic integrity evidence is not a passing review")
        observed = {(item.get("control_area"), item.get("owner_stage")) for item in evidence if isinstance(item, dict) and isinstance(item.get("artifact"), str) and item["artifact"] and isinstance(item.get("finding"), str) and item["finding"].strip()}
        expected = set(SEMANTIC_AREAS.items())
        if observed != expected:
            return fail("V1 semantic evidence must uniquely cover intent, subject, world, character, causality and narrative")
    if packet["stage"] == "D1":
        approval = packet.get("author_approval", {})
        approval_path = (packet_path.parent / approval.get("path", "")).resolve()
        if not approval_path.is_file() or digest(approval_path) != approval.get("sha256"):
            return fail("D1 lacks hash-bound author approval")
        try:
            approval_data = load(approval_path)
        except json.JSONDecodeError:
            return fail("D1 author approval is invalid")
        if approval_data.get("run_id") != packet["run_id"] or approval_data.get("approval_scope") != "V2" or approval_data.get("decision") != "approved" or approval_data.get("record_assurance") != "self_recorded":
            return fail("D1 author approval does not approve this self-recorded run")
        brief = approval_data.get("review_brief", {})
        brief_path = (approval_path.parent / brief.get("path", "")).resolve()
        record = approval_data.get("approval_record", {})
        if not brief_path.is_file() or digest(brief_path) != brief.get("sha256"):
            return fail("D1 author approval is not bound to the reviewed HTML")
        if not isinstance(record.get("event_seq"), int) or not isinstance(record.get("text"), str) or not record["text"].strip():
            return fail("D1 author approval has no recorded author decision")
        v2_packets = [item for item in upstream_packets if item[1].get("stage") == "V2"]
        if not v2_packets or (v2_packets[0][0].parent / v2_packets[0][1].get("design_artifact", "")).resolve() != brief_path or v2_packets[0][1].get("design_artifact_sha256") != brief.get("sha256"):
            return fail("D1 author approval is not bound to the current V2 brief")
        v1_inputs_of_v2 = [
            reference
            for reference in v2_packets[0][1].get("input_completions", [])
            if isinstance(reference, dict)
            and reference_identity(v2_packets[0][0].parent, reference)
            == (
                v1_packets[0][0],
                digest(v1_packets[0][0]),
            )
        ]
        if len(v1_inputs_of_v2) != 1:
            return fail("D1 V2 completion is not bound to the consumed V1 completion")
        if artifact.name != "package-manifest.json":
            return fail("D1 design artifact must be package-manifest.json")
        try:
            manifest_data = load(artifact)
        except json.JSONDecodeError:
            return fail("D1 package manifest is invalid")
        manifest_error = validate_d1_package_manifest(
            artifact,
            manifest_data,
            packet["run_id"],
            validation,
            packet["validation"].get("sha256"),
        )
        if manifest_error:
            return fail(manifest_error)
        map_path = artifact.parent / "map-data.json"
        try:
            map_data = load(map_path)
        except json.JSONDecodeError:
            return fail("D1 map-data is invalid")
        binding_error = validate_d1_input_binding(
            map_path,
            map_data,
            packet_path,
            packet,
            input_references,
        )
        if binding_error:
            return fail(binding_error)
        required_validation = {
            "schema_version": "1.0",
            "harness": "novel-conception-interview",
            "run_id": packet["run_id"],
            "stage": "D1",
            "mode": "map",
            "verdict": "ready",
            "errors": [],
            "blockers": [],
        }
        if any(validation_data.get(key) != value for key, value in required_validation.items()):
            return fail("stored D1 validation does not identify a clean canonical ready result")
        canonical, canonical_error = canonical_d1_validation(artifact.parent)
        if canonical_error:
            return fail(canonical_error)
        if canonical != validation_data:
            return fail("stored D1 validation differs from canonical revalidation")
    if packet["stage"] == "R1":
        approval = packet.get("final_author_approval", {})
        approval_path = (packet_path.parent / approval.get("path", "")).resolve()
        if (
            not approval_path.is_file()
            or digest(approval_path) != approval.get("sha256")
        ):
            return fail("R1 lacks hash-bound final author approval")
        if artifact.name != "package-manifest.json":
            return fail("R1 design artifact must be package-manifest.json")
        try:
            r1_manifest = load(artifact)
        except json.JSONDecodeError:
            return fail("R1 design artifact is not a valid package manifest")
        r1_manifest_error = validate_r1_package_manifest(
            artifact,
            r1_manifest,
            packet["run_id"],
            validation,
            packet["validation"].get("sha256"),
        )
        if r1_manifest_error:
            return fail(r1_manifest_error)
        required_validation = {
            "schema_version": "1.0",
            "harness": "novel-conception-interview",
            "run_id": packet["run_id"],
            "stage": "R1",
            "mode": "review",
            "verdict": "ready",
            "errors": [],
            "blockers": [],
        }
        if any(
            validation_data.get(key) != value
            for key, value in required_validation.items()
        ):
            return fail(
                "stored R1 validation does not identify a clean canonical ready result"
            )
        canonical, canonical_error = canonical_r1_validation(artifact.parent)
        if canonical_error:
            return fail(canonical_error)
        if canonical != validation_data:
            return fail("stored R1 validation differs from canonical revalidation")
        try:
            approval_data = load(approval_path)
        except json.JSONDecodeError:
            return fail("R1 final author approval is invalid")
        if approval_data.get("run_id") != packet["run_id"] or approval_data.get("approval_scope") != "R1" or approval_data.get("decision") != "approved" or approval_data.get("record_assurance") != "self_recorded":
            return fail("R1 final author approval does not approve this run")
        brief = approval_data.get("review_brief", {})
        brief_path = (approval_path.parent / brief.get("path", "")).resolve()
        record = approval_data.get("approval_record", {})
        review_record = r1_manifest.get("author_review_artifact", {})
        expected_review = (
            artifact.parent / review_record.get("path", "")
        ).resolve()
        if (
            not brief_path.is_file()
            or digest(brief_path) != brief.get("sha256")
            or brief_path != expected_review
            or brief.get("sha256") != review_record.get("sha256")
        ):
            return fail("R1 final approval is not bound to the current review artifact")
        if not isinstance(record.get("event_seq"), int) or not isinstance(record.get("text"), str) or not record["text"].strip():
            return fail("R1 final author approval has no recorded author decision")
        d1_packets = [
            item for item in upstream_packets if item[1].get("stage") == "D1"
        ]
        if len(d1_packets) != 1:
            return fail("R1 must consume exactly one D1 completion")
        d1_path, d1_packet = d1_packets[0]
        d1_error = validate_ready_completion(d1_path)
        if d1_error:
            return fail("R1 cannot consume D1: " + d1_error)
        handoff_path, handoff_data, handoff_reference_error = load_hash_bound_reference(
            packet_path.parent,
            packet.get("independent_handoff"),
            "R1 independent handoff",
        )
        if handoff_reference_error:
            return fail(handoff_reference_error)
        manifest_handoff = r1_manifest.get("independent_handoff", {})
        if reference_identity(
            packet_path.parent, packet.get("independent_handoff")
        ) != reference_identity(artifact.parent, manifest_handoff):
            return fail(
                "R1 completion and package manifest bind different independent handoff records"
            )
        handoff_error = validate_independent_handoff(
            handoff_data,
            packet["run_id"],
            handoff_path,
            d1_path,
            d1_packet,
        )
        if handoff_error:
            return fail(handoff_error)
    print("OK: stage completion is consumable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
