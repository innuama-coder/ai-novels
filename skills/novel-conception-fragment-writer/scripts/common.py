from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SKILL_NAME = "novel-conception-fragment-writer"
ASSEMBLER_SKILL = "novel-conception-human-review-assembler"
PHASES = ["scene-contracts", "drafts", "revision-audit"]
PHASE_FILES = {
    "scene-contracts": "01-scene-contracts.json",
    "drafts": "02-drafts.json",
    "revision-audit": "03-revision-audit.json",
}
STYLE_CONTRACT = {
    "id": "restrained-concrete-scene-v1",
    "purpose": "conception_review_sample",
    "name": "克制具象的场景驱动现代白描",
    "fixed_principles": [
        "single_limited_pov",
        "continuous_scene_now",
        "concrete_selective_detail",
        "pressure_choice_consequence",
        "subtextual_interaction",
        "restrained_emotion",
        "earned_state_change",
    ],
    "adaptive_axes": [
        "pov_person",
        "genre_lexicon",
        "character_diction",
        "emotional_temperature",
        "sentence_rhythm",
        "sensory_channels",
    ],
    "prohibitions": [
        "outline_or_screenplay",
        "author_explanation",
        "author_imitation",
        "pov_or_information_breach",
        "exposition_instead_of_choice",
        "unearned_state_change",
        "new_authoritative_fact",
        "final_prose_claim",
    ],
}
BASE_AUDIT_KEYS = {
    "orientation",
    "pressure_or_goal",
    "turning_choice",
    "consequence_or_state_change",
    "pov_and_information",
}
TARGET_AUDIT_KEYS = {
    "world_in_action": "world_in_action",
    "story_causality": "causal_progression",
    "character_agency": "character_agency",
    "relationship_change": "relationship_change",
    "narrative_contract": "narrative_contract",
    "ending_nature": "ending_nature",
}
CONTRACT_CHECKS = {
    "source_grounding",
    "narrative_contract",
    "no_new_authority",
    "review_question_fit",
}
PLACEHOLDER_RE = re.compile(
    r"(?:\bTBD\b|\bTODO\b|\bFIXME\b|\bXXX\b|placeholder|lorem ipsum|"
    r"待补|待定|占位|稍后填写)",
    re.IGNORECASE,
)
MARKDOWN_RE = re.compile(r"(?m)^\s*(?:#{1,6}\s|```|[-*]\s+\*\*)")
META_RE = re.compile(
    r"(?im)^\s*(?:场景|镜头|内景|外景|INT\.|EXT\.|CUT TO|评审说明|片段目的|"
    r"人物目标|转折点)\s*[:：]"
)
CLICHE_PATTERNS = [
    "命运的齿轮",
    "空气仿佛凝固",
    "时间仿佛静止",
    "一切才刚刚开始",
    "他不知道的是",
    "她不知道的是",
    "心中涌起一股",
    "嘴角勾起一抹",
    "眼神中闪过一丝",
]


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def meaningful(value: Any, label: str, minimum: int = 2) -> str:
    require(isinstance(value, str), f"{label} must be text")
    clean = value.strip()
    require(len(clean) >= minimum, f"{label} is too short")
    require(not PLACEHOLDER_RE.search(clean), f"{label} contains placeholder")
    return clean


def require_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    missing = sorted(keys - set(value))
    require(not missing, f"{label} missing keys: {missing}")
    return value


def ensure_exact_ids(items: Any, expected: set[str], label: str) -> dict[str, Any]:
    require(isinstance(items, list), f"{label} must be a list")
    by_id = {
        item.get("id"): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    require(len(by_id) == len(items), f"{label} contains duplicate or invalid ids")
    require(set(by_id) == expected, f"{label} ids do not match fragment slots")
    return by_id


def count_text(text: str) -> dict[str, Any]:
    cjk_chars = len(
        re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text)
    )
    latin_words = len(re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b", text))
    visible_chars = len(re.sub(r"\s+", "", text))
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    sentence_units = [
        item for item in re.split(r"[。！？!?]+|…{2,}", text) if item.strip()
    ]
    max_paragraph = max((len(re.sub(r"\s+", "", item)) for item in paragraphs), default=0)
    return {
        "cjk_chars": cjk_chars,
        "latin_words": latin_words,
        "visible_chars": visible_chars,
        "paragraphs": len(paragraphs),
        "sentence_units": len(sentence_units),
        "max_paragraph_ratio": round(max_paragraph / max(visible_chars, 1), 4),
        "exclamation_marks": text.count("!") + text.count("！"),
        "ellipsis_runs": len(re.findall(r"(?:…{2,}|\.{3,})", text)),
    }


def validate_style_text(text: Any, slot: dict[str, Any], label: str) -> dict[str, Any]:
    text = meaningful(text, label, minimum=40)
    metrics = count_text(text)
    require(not MARKDOWN_RE.search(text), f"{label} contains Markdown")
    require(not META_RE.search(text), f"{label} contains screenplay or review labels")
    cliché_hits = [pattern for pattern in CLICHE_PATTERNS if pattern in text]
    require(not cliché_hits, f"{label} contains mechanical clichés: {cliché_hits}")
    require(metrics["paragraphs"] >= 2, f"{label} needs at least two paragraphs")
    require(metrics["sentence_units"] >= 4, f"{label} needs at least four sentence units")
    require(
        metrics["max_paragraph_ratio"] <= 0.75,
        f"{label} has an oversized paragraph",
    )
    require(metrics["exclamation_marks"] <= 2, f"{label} overuses exclamation marks")
    require(metrics["ellipsis_runs"] <= 3, f"{label} overuses ellipses")

    max_cjk = slot["max_cjk_chars"]
    max_latin = slot["max_latin_words"]
    require(metrics["cjk_chars"] <= max_cjk, f"{label} exceeds CJK limit")
    require(metrics["latin_words"] <= max_latin, f"{label} exceeds Latin limit")
    if max_cjk > 0 and metrics["cjk_chars"] >= metrics["latin_words"]:
        minimum = max(40, int(max_cjk * 0.45))
        require(metrics["cjk_chars"] >= minimum, f"{label} is too short for its CJK budget")
    elif max_latin > 0:
        minimum = max(35, int(max_latin * 0.45))
        require(
            metrics["latin_words"] >= minimum,
            f"{label} is too short for its Latin budget",
        )
    else:
        raise ContractError(f"{label} has no usable language budget")
    return metrics


def validate_creative_choices(
    choices: Any,
    allowed_bases: list[str],
    label: str,
) -> list[dict[str, str]]:
    require(isinstance(choices, list), f"{label} creative_choices must be a list")
    for index, choice in enumerate(choices):
        require_keys(choice, {"choice", "authorization_basis"}, f"{label} choice {index}")
        meaningful(choice["choice"], f"{label} choice {index}")
        require(
            choice["authorization_basis"] in allowed_bases,
            f"{label} creative choice has no brief authorization",
        )
    return choices


def validate_audit(
    audit: Any,
    text: str,
    targets: list[str],
    label: str,
) -> dict[str, Any]:
    require(isinstance(audit, dict), f"{label} scene_audit must be an object")
    required = BASE_AUDIT_KEYS | {
        TARGET_AUDIT_KEYS[target] for target in targets
    }
    missing = sorted(required - set(audit))
    require(not missing, f"{label} missing audit keys: {missing}")
    quotes: list[str] = []
    for key in required:
        item = require_keys(audit[key], {"finding", "evidence_quote"}, f"{label}.{key}")
        meaningful(item["finding"], f"{label}.{key}.finding", minimum=4)
        quote = meaningful(item["evidence_quote"], f"{label}.{key}.quote", minimum=4)
        require(len(quote) <= 80, f"{label}.{key} quote is too long")
        require(quote in text, f"{label}.{key} quote not found in final text")
        quotes.append(quote)
    require(
        len(set(quotes)) >= min(3, len(required)),
        f"{label} reuses one audit quote for unrelated checks",
    )
    return audit


def _normalized_fact_text(value: str) -> str:
    return "".join(
        character.casefold()
        for character in value
        if character.isalnum()
    )


def _validate_bound_quote(value: Any, text: str, label: str) -> dict[str, Any]:
    item = require_keys(value, {"value", "evidence_quote"}, label)
    meaningful(item["value"], f"{label}.value")
    quote = meaningful(item["evidence_quote"], f"{label}.evidence_quote", minimum=4)
    require(len(quote) <= 120, f"{label} evidence quote is too long")
    require(quote in text, f"{label} evidence quote not found in final text")
    return item


def validate_brief_compliance(
    compliance: Any,
    text: str,
    slot: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    value = require_keys(
        compliance,
        {
            "final_text_sha256",
            "before_state",
            "after_state",
            "required_facts",
            "prohibited_facts",
        },
        f"{label}.brief_compliance",
    )
    require(
        value["final_text_sha256"] == sha256_text(text),
        f"{label} brief compliance targets another final text",
    )
    before = _validate_bound_quote(
        value["before_state"],
        text,
        f"{label}.brief_compliance.before_state",
    )
    after = _validate_bound_quote(
        value["after_state"],
        text,
        f"{label}.brief_compliance.after_state",
    )
    require(
        before["value"] == slot["before_state"],
        f"{label} before state does not match brief",
    )
    require(
        after["value"] == slot["after_state"],
        f"{label} after state does not match brief",
    )

    required = value["required_facts"]
    require(isinstance(required, list), f"{label} required fact audit must be a list")
    require(
        [item.get("fact") for item in required if isinstance(item, dict)]
        == slot["required_facts"],
        f"{label} required fact audit does not match brief",
    )
    for index, item in enumerate(required):
        checked = require_keys(
            item,
            {"fact", "finding", "evidence_quote"},
            f"{label}.required_facts[{index}]",
        )
        meaningful(checked["finding"], f"{label}.required_facts[{index}].finding", minimum=4)
        quote = meaningful(
            checked["evidence_quote"],
            f"{label}.required_facts[{index}].evidence_quote",
            minimum=4,
        )
        require(len(quote) <= 120, f"{label} required fact quote is too long")
        require(quote in text, f"{label} required fact quote not found in final text")

    prohibited = value["prohibited_facts"]
    require(isinstance(prohibited, list), f"{label} prohibited fact audit must be a list")
    require(
        [item.get("fact") for item in prohibited if isinstance(item, dict)]
        == slot["prohibited_facts"],
        f"{label} prohibited fact audit does not match brief",
    )
    normalized_text = _normalized_fact_text(text)
    for index, item in enumerate(prohibited):
        checked = require_keys(
            item,
            {"fact", "verdict", "rationale"},
            f"{label}.prohibited_facts[{index}]",
        )
        require(
            checked["verdict"] == "absent",
            f"{label} prohibited fact verdict must be absent",
        )
        meaningful(
            checked["rationale"],
            f"{label}.prohibited_facts[{index}].rationale",
            minimum=4,
        )
        normalized_fact = _normalized_fact_text(checked["fact"])
        require(normalized_fact, f"{label} prohibited fact is empty after normalization")
        require(
            normalized_fact not in normalized_text,
            f"{label} contains prohibited fact: {checked['fact']}",
        )
    return value


def verify_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    files = manifest.get("files")
    require(isinstance(files, list) and files, "manifest has no files")
    seen: set[str] = set()
    for entry in files:
        path = entry.get("path")
        expected = entry.get("sha256")
        require(isinstance(path, str) and path, "manifest path missing")
        require(path not in seen, f"duplicate manifest path: {path}")
        seen.add(path)
        target = (directory / path).resolve()
        require(target.is_file(), f"manifest target missing: {path}")
        require(sha256_file(target) == expected, f"manifest hash mismatch: {path}")


def all_skill_files(skill_dir: Path) -> list[Path]:
    selected: list[Path] = []
    for rel in ("SKILL.md", "agents", "references", "scripts"):
        target = skill_dir / rel
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
