from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SKILL_NAME = "novel-conception-review-html-generator"
UPSTREAM_SKILL = "novel-conception-human-review-assembler"
STYLE_CONTRACT = {
    "id": "editorial-review-desk-v1",
    "name": "编辑部审阅台",
    "purpose": "ten_minute_conception_review",
    "palette": {
        "paper": "#F7F3EA",
        "ink": "#18202A",
        "muted": "#5E6873",
        "blue": "#2457A7",
        "amber": "#A65A00",
        "card": "#FFFDF8",
        "border": "#D7D0C3",
    },
    "principles": [
        "content_first",
        "authoritative_work_title_first",
        "all_required_content_visible",
        "semantic_landmarks",
        "text_equivalent_for_visuals",
        "svg_information_graphics",
        "single_column_reflow",
        "keyboard_and_print_ready",
        "offline_self_contained",
    ],
    "prohibitions": [
        "content_rewriting",
        "external_resource",
        "required_content_in_tabs_or_accordions",
        "decorative_hero",
        "gradient_or_motion",
        "preselected_author_decision",
    ],
}
CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
    "img-src data:; connect-src 'none'; font-src 'none'; base-uri 'none'; "
    "form-action 'none'"
)
REQUIRED_FILES = {
    "human-review-report.json",
    "human-review-report.md",
    "assembly-execution.json",
    "validation.json",
    "package-manifest.json",
}
OUTPUT_FILES = {
    "human-review-report.html",
    "render-record.json",
    "package-manifest.json",
    "validation.json",
}
REQUIRED_SECTION_IDS = {
    "orientation",
    "world",
    "story",
    "characters",
    "fragments",
    "decision",
}
REMOTE_SCHEME_RE = re.compile(r"^(?:https?:|//|javascript:)", re.IGNORECASE)
INLINE_HANDLER_RE = re.compile(r"^on[a-z]+$", re.IGNORECASE)


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


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def embedded_json(data: Any) -> str:
    return canonical_json(data).replace("<", "\\u003c")


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def all_skill_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ("SKILL.md", "agents", "references", "scripts"):
        target = skill_dir / rel
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(
                path
                for path in target.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}
            )
    return sorted(set(files))


def verify_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    files = manifest.get("files")
    require(isinstance(files, list) and files, "manifest has no files")
    seen: set[str] = set()
    for entry in files:
        require(isinstance(entry, dict), "manifest entry must be an object")
        name = entry.get("path")
        expected = entry.get("sha256")
        require(isinstance(name, str) and name, "manifest path missing")
        require(name not in seen, f"duplicate manifest path: {name}")
        require(
            Path(name).name == name and name not in {".", ".."},
            f"manifest path must be a package-local file: {name}",
        )
        seen.add(name)
        target = directory / name
        require(target.is_file(), f"manifest target missing: {name}")
        require(sha256_file(target) == expected, f"manifest hash mismatch: {name}")


def validate_upstream(
    assembly: Path,
    plan: Path,
    fragments: Path,
    r1: Path,
) -> dict[str, Any]:
    assembly = assembly.resolve()
    missing = sorted(name for name in REQUIRED_FILES if not (assembly / name).is_file())
    require(not missing, f"assembly package missing files: {missing}")
    manifest = load_json(assembly / "package-manifest.json")
    require(manifest.get("skill") == UPSTREAM_SKILL, "assembly manifest skill mismatch")
    require(manifest.get("verdict") == "ready", "assembly manifest is not ready")
    verify_manifest(assembly, manifest)

    validator = (
        Path(__file__).resolve().parents[2]
        / UPSTREAM_SKILL
        / "scripts"
        / "validate_human_review.py"
    )
    require(validator.is_file(), f"upstream validator missing: {validator}")
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            "assemble",
            str(assembly),
            "--plan",
            str(plan.resolve()),
            "--fragments",
            str(fragments.resolve()),
            "--r1",
            str(r1.resolve()),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    require(
        result.returncode == 0,
        "upstream assembly validation failed: "
        + (result.stderr.strip() or result.stdout.strip()),
    )
    validation = load_json(assembly / "validation.json")
    require(validation.get("verdict") == "ready", "assembly validation is not ready")
    require(validation.get("errors", []) == [], "assembly validation has errors")
    report = load_json(assembly / "human-review-report.json")
    require(report.get("status") == "ready", "human review report is not ready")
    require(report.get("skill") == UPSTREAM_SKILL, "human review report skill mismatch")
    return {
        "report": report,
        "report_sha256": sha256_file(assembly / "human-review-report.json"),
        "assembly_manifest_sha256": sha256_file(assembly / "package-manifest.json"),
        "assembly_validation_sha256": sha256_file(assembly / "validation.json"),
    }


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.headings: list[tuple[str, str]] = []
        self.labels_for: set[str] = set()
        self.controls: dict[str, str] = {}
        self.checked_controls: set[str] = set()
        self.embedded_report = ""
        self._capture_report = False
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._details_depth = 0
        self.required_inside_details: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append(tag)
        self.attrs.append((tag, values))
        item_id = values.get("id")
        if item_id:
            if item_id in self.ids:
                self.duplicate_ids.add(item_id)
            self.ids.add(item_id)
            if self._details_depth and item_id in REQUIRED_SECTION_IDS:
                self.required_inside_details.add(item_id)
        if tag == "details":
            self._details_depth += 1
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = tag
            self._heading_text = []
        if tag == "label" and values.get("for"):
            self.labels_for.add(values["for"])
        if tag in {"input", "textarea", "select", "button"} and item_id:
            self.controls[item_id] = tag
            if "checked" in values:
                self.checked_controls.add(item_id)
        if tag == "script" and item_id == "report-data":
            require(
                values.get("type") == "application/json",
                "embedded report script must use application/json",
            )
            self._capture_report = True

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "details":
            self._details_depth = max(0, self._details_depth - 1)
        if tag == self._heading_tag:
            self.headings.append((tag, "".join(self._heading_text).strip()))
            self._heading_tag = None
            self._heading_text = []
        if tag == "script" and self._capture_report:
            self._capture_report = False

    def handle_data(self, data: str) -> None:
        if self._capture_report:
            self.embedded_report += data
        if self._heading_tag:
            self._heading_text.append(data)


def inspect_html(document: str) -> PageInspector:
    inspector = PageInspector()
    try:
        inspector.feed(document)
        inspector.close()
    except (ContractError, Exception) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"invalid HTML structure: {exc}") from exc
    return inspector
