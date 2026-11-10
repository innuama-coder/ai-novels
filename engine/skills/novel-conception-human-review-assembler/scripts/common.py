from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SKILL_NAME = "novel-conception-human-review-assembler"
SCHEMA_VERSION = "1.0"
REQUIRED_REVIEW_TASKS = {
    "story_identity",
    "world_logic",
    "story_causality",
    "thread_structure",
    "character_agency",
    "relationship_logic",
    "narrative_experience",
    "ending_and_open_interfaces",
}
REQUIRED_FRAGMENT_TARGETS = {
    "world_in_action",
    "story_causality",
    "character_agency",
    "relationship_change",
    "narrative_contract",
    "ending_nature",
}
MAIN_SECTIONS = ["world", "story", "characters", "fragments"]
READING_SECTIONS = [
    "orientation",
    "world",
    "story",
    "characters",
    "fragments",
    "decision",
]
PLACEHOLDER_RE = re.compile(
    r"(?:\bTBD\b|\bTODO\b|\bFIXME\b|\bXXX\b|placeholder|lorem ipsum|"
    r"待补|待定|占位|示例文本|稍后填写)",
    re.IGNORECASE,
)
ID_KEYS = {
    "id",
    "source_id",
    "source_ids",
    "control_ids",
    "unit_ids",
    "line_ids",
    "visible_element_ids",
    "required_source_ids",
    "allowed_source_ids",
    "expected_source_ids",
}
ENUM_KEYS = {
    "schema_version",
    "skill",
    "status",
    "type",
    "kind",
    "layer",
    "domain",
    "disposition",
}


class ContractError(ValueError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def verify_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    files = manifest.get("files")
    require(isinstance(files, list) and files, f"manifest has no files: {directory}")
    seen: set[str] = set()
    for entry in files:
        require(isinstance(entry, dict), "manifest file entry must be an object")
        rel = entry.get("path")
        expected = entry.get("sha256")
        require(isinstance(rel, str) and rel, "manifest file path missing")
        require(isinstance(expected, str) and len(expected) == 64, f"bad hash for {rel}")
        require(rel not in seen, f"duplicate manifest path: {rel}")
        seen.add(rel)
        target = (directory / rel).resolve()
        require(target.is_file(), f"manifest target missing: {target}")
        require(sha256_file(target) == expected, f"manifest hash mismatch: {rel}")


def _walk_ids(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        item_id = value.get("id")
        if isinstance(item_id, str) and item_id.strip():
            yield item_id.strip()
        for child in value.values():
            yield from _walk_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_ids(child)


def _top_level_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item["id"].strip()
        for item in value
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item["id"].strip()
    ]


def _label(value: dict[str, Any]) -> str:
    for key in ("name", "title", "definition", "core_promise", "label", "id"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()[:160]
    return "未命名对象"


def _collect_subjects(
    value: Any,
    domain: str,
    path: str,
    output: dict[str, dict[str, str]],
) -> None:
    if isinstance(value, dict):
        item_id = value.get("id")
        if isinstance(item_id, str) and item_id.strip():
            clean = item_id.strip()
            previous = output.get(clean)
            if previous and previous["domain"] != domain:
                raise ContractError(
                    f"source id reused across domains: {clean} "
                    f"({previous['domain']} / {domain})"
                )
            output.setdefault(
                clean,
                {
                    "source_id": clean,
                    "domain": domain,
                    "path": path,
                    "label": _label(value),
                },
            )
        for key, child in value.items():
            _collect_subjects(child, domain, f"{path}.{key}", output)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_subjects(child, domain, f"{path}[{index}]", output)


def _collect_top_level_subjects(
    value: Any,
    domain: str,
    path: str,
    output: dict[str, dict[str, str]],
) -> None:
    require(isinstance(value, list), f"{path} must be a list")
    for index, item in enumerate(value):
        require(isinstance(item, dict), f"{path}[{index}] must be an object")
        item_id = item.get("id")
        require(isinstance(item_id, str) and item_id.strip(), f"{path}[{index}] has no id")
        clean = item_id.strip()
        require(clean not in output, f"duplicate review subject id: {clean}")
        output[clean] = {
            "source_id": clean,
            "domain": domain,
            "path": f"{path}[{index}]",
            "label": _label(item),
        }


def build_source_inventory(r1_directory: Path) -> dict[str, Any]:
    r1_directory = r1_directory.resolve()
    required = {
        "review-data.json",
        "validation.json",
        "package-manifest.json",
        "independent-handoff.json",
        "novel-design-brief.md",
    }
    missing = sorted(name for name in required if not (r1_directory / name).is_file())
    require(not missing, f"R1 package missing: {', '.join(missing)}")

    r1_manifest_path = r1_directory / "package-manifest.json"
    r1_manifest = load_json(r1_manifest_path)
    verify_manifest(r1_directory, r1_manifest)

    review_path = r1_directory / "review-data.json"
    review = load_json(review_path)
    require(review.get("stage") == "R1", "review-data stage must be R1")
    require(review.get("status") == "ready", "R1 review-data is not ready")
    require(not review.get("findings"), "R1 review-data still has findings")

    validation = load_json(r1_directory / "validation.json")
    require(validation.get("verdict") == "ready", "R1 validation is not ready")
    require(not validation.get("errors"), "R1 validation has errors")
    require(not validation.get("blockers"), "R1 validation has blockers")

    handoff_path = r1_directory / "independent-handoff.json"
    handoff = load_json(handoff_path)
    require(
        handoff.get("verdict") == "pass",
        "R1 independent handoff verdict must be pass",
    )
    d1_ref = handoff.get("d1_package")
    require(isinstance(d1_ref, dict), "R1 handoff missing d1_package")
    d1_rel = d1_ref.get("path")
    d1_expected = d1_ref.get("sha256")
    require(isinstance(d1_rel, str) and d1_rel, "D1 manifest path missing")
    d1_manifest_path = (r1_directory / d1_rel).resolve()
    require(d1_manifest_path.is_file(), f"D1 manifest missing: {d1_manifest_path}")
    require(
        sha256_file(d1_manifest_path) == d1_expected,
        "D1 manifest hash does not match R1 handoff",
    )
    d1_directory = d1_manifest_path.parent
    d1_manifest = load_json(d1_manifest_path)
    map_entries = [
        entry
        for entry in d1_manifest.get("files", [])
        if entry.get("path") == "map-data.json"
    ]
    require(len(map_entries) == 1, "D1 manifest must list map-data.json once")
    map_path = d1_directory / "map-data.json"
    require(map_path.is_file(), f"D1 map missing: {map_path}")
    require(
        sha256_file(map_path) == map_entries[0].get("sha256"),
        "D1 map hash mismatch",
    )
    map_data = load_json(map_path)
    require(map_data.get("status") == "ready", "D1 map is not ready")
    conception = map_data.get("conception")
    require(isinstance(conception, dict), "D1 conception model missing")

    subjects: dict[str, dict[str, str]] = {}
    _collect_subjects(conception.get("world"), "world", "conception.world", subjects)
    _collect_subjects(conception.get("story"), "story", "conception.story", subjects)
    _collect_subjects(
        conception.get("characters"),
        "characters",
        "conception.characters",
        subjects,
    )
    _collect_top_level_subjects(map_data.get("units"), "units", "units", subjects)
    _collect_top_level_subjects(
        map_data.get("open_items"),
        "open_items",
        "open_items",
        subjects,
    )
    require(any(v["domain"] == "world" for v in subjects.values()), "no world subjects")
    require(any(v["domain"] == "story" for v in subjects.values()), "no story subjects")
    require(
        any(v["domain"] == "characters" for v in subjects.values()),
        "no character subjects",
    )
    require(any(v["domain"] == "units" for v in subjects.values()), "no D1 units")

    known_source_ids = sorted(set(_walk_ids(map_data)))
    world_model = conception.get("world") if isinstance(conception.get("world"), dict) else {}
    story_model = conception.get("story") if isinstance(conception.get("story"), dict) else {}
    raw_characters = conception.get("characters")
    if isinstance(raw_characters, dict):
        # Current D1 schema: one character domain containing explicit profile
        # and relationship registries. Every named profile is review-relevant:
        # supporting roles carry action, authority, information, opposition, or
        # aftermath responsibilities that the author must be able to inspect.
        character_models = (
            raw_characters.get("profiles")
            if isinstance(raw_characters.get("profiles"), list)
            else []
        )
        relationship_models = (
            raw_characters.get("relationships")
            if isinstance(raw_characters.get("relationships"), list)
            else []
        )
        relationship_layer_ids = _top_level_ids(relationship_models)
    elif isinstance(raw_characters, list):
        # Backward compatibility with the earlier per-core-character schema.
        character_models = raw_characters
        relationship_layer_ids = []
        for character in character_models:
            if isinstance(character, dict):
                relationship_layer_ids.extend(
                    _top_level_ids(character.get("relationship_layers"))
                )
    else:
        character_models = []
        relationship_layer_ids = []
    source_id_groups = {
        "review_subjects": sorted(subjects),
        "units": _top_level_ids(map_data.get("units")),
        "control_points": _top_level_ids(map_data.get("control_points")),
        "design_decisions": _top_level_ids(map_data.get("design_decisions")),
        "information_obligations": _top_level_ids(
            map_data.get("information_obligations")
        ),
        "terminal_threads": _top_level_ids(map_data.get("terminal_threads")),
        "world_systems": _top_level_ids(world_model.get("systems")),
        "world_environments": _top_level_ids(world_model.get("environments")),
        "story_phases": _top_level_ids(story_model.get("phases")),
        "storylines": _top_level_ids(story_model.get("storylines")),
        "major_events": _top_level_ids(story_model.get("major_events")),
        "review_characters": _top_level_ids(character_models),
        "core_characters": [
            item["id"]
            for item in character_models
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("importance") == "core"
        ]
        or _top_level_ids(character_models),
        "relationship_layers": sorted(set(relationship_layer_ids)),
    }
    fragment_eligible_source_ids = sorted(
        set().union(*[set(values) for values in source_id_groups.values()])
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "skill": SKILL_NAME,
        "run_id": review.get("run_id"),
        "status": "ready",
        "source_package": {
            "r1_directory": str(r1_directory),
            "r1_manifest_sha256": sha256_file(r1_manifest_path),
            "review_data_sha256": sha256_file(review_path),
            "independent_handoff_sha256": sha256_file(handoff_path),
            "d1_manifest_path": str(d1_manifest_path),
            "d1_manifest_sha256": sha256_file(d1_manifest_path),
            "map_data_path": str(map_path.resolve()),
            "map_data_sha256": sha256_file(map_path),
        },
        "known_source_ids": known_source_ids,
        "fragment_eligible_source_ids": fragment_eligible_source_ids,
        "source_id_groups": source_id_groups,
        "review_subjects": sorted(
            subjects.values(),
            key=lambda item: (item["domain"], item["path"], item["source_id"]),
        ),
        "counts": {
            domain: sum(1 for item in subjects.values() if item["domain"] == domain)
            for domain in ("world", "story", "characters", "units", "open_items")
        },
    }


def count_text(value: Any) -> dict[str, int]:
    strings: list[str] = []

    def visit(item: Any, key: str | None = None) -> None:
        if key in ID_KEYS or key in ENUM_KEYS:
            return
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, dict):
            for child_key, child in item.items():
                visit(child, child_key)
        elif isinstance(item, list):
            for child in item:
                visit(child, key)

    visit(value)
    text = "\n".join(strings)
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))
    latin_words = len(re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b", text))
    return {"cjk_chars": cjk, "latin_words": latin_words}


def estimated_minutes(
    counts: dict[str, int],
    cjk_rate: float,
    latin_rate: float,
) -> float:
    return counts["cjk_chars"] / cjk_rate + counts["latin_words"] / latin_rate


def meaningful_text(value: Any, label: str, minimum: int = 2) -> str:
    require(isinstance(value, str), f"{label} must be text")
    clean = value.strip()
    require(len(clean) >= minimum, f"{label} is too short")
    require(not PLACEHOLDER_RE.search(clean), f"{label} contains placeholder text")
    return clean


def collect_report_element_ids(value: Any) -> set[str]:
    found: set[str] = set()
    duplicates: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id.startswith("HR-"):
                if item_id in found:
                    duplicates.add(item_id)
                found.add(item_id)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    require(not duplicates, f"duplicate report element ids: {sorted(duplicates)}")
    return found


def validate_source_ids(
    source_ids: Any,
    known: set[str],
    label: str,
    *,
    allow_empty: bool = False,
) -> list[str]:
    require(isinstance(source_ids, list), f"{label} source_ids must be a list")
    require(allow_empty or bool(source_ids), f"{label} source_ids cannot be empty")
    require(all(isinstance(item, str) and item for item in source_ids), f"{label} bad id")
    unknown = sorted(set(source_ids) - known)
    require(not unknown, f"{label} cites unknown source ids: {unknown}")
    return source_ids


def all_skill_files(skill_directory: Path) -> list[Path]:
    selected: list[Path] = []
    for rel in ("SKILL.md", "agents", "references", "scripts"):
        target = skill_directory / rel
        if target.is_file():
            selected.append(target)
        elif target.is_dir():
            selected.extend(
                path
                for path in target.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}
            )
    return sorted(set(selected))
