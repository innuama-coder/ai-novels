from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import (
    CSP,
    ContractError,
    INLINE_HANDLER_RE,
    REMOTE_SCHEME_RE,
    REQUIRED_SECTION_IDS,
    SKILL_NAME,
    STYLE_CONTRACT,
    all_skill_files,
    inspect_html,
    load_json,
    require,
    sha256_file,
    validate_upstream,
    verify_manifest,
    write_json,
)
from render_review_html import CSS, render_html


PRIMARY_FILES = {
    "human-review-report.html",
    "render-record.json",
    "package-manifest.json",
}
DECISION_DOMAINS = {"world", "story", "characters", "fragments"}


def _validate_structure(document: str, report: dict[str, Any]) -> dict[str, Any]:
    inspector = inspect_html(document)
    require(not inspector.duplicate_ids, f"duplicate HTML ids: {sorted(inspector.duplicate_ids)}")
    require(
        {"html", "head", "body", "header", "nav", "main", "footer"}
        <= set(inspector.tags),
        "semantic page landmarks are incomplete",
    )
    require(
        REQUIRED_SECTION_IDS <= inspector.ids,
        f"missing review sections: {sorted(REQUIRED_SECTION_IDS - inspector.ids)}",
    )
    require(
        not inspector.required_inside_details,
        "required review sections cannot be inside details",
    )
    require("main-content" in inspector.ids, "skip-link target is missing")
    require("report-data" in inspector.ids, "embedded report data is missing")
    require(
        sum(1 for tag, _ in inspector.headings if tag == "h1") == 1,
        "page must contain exactly one h1",
    )
    work_title = report["review_contract"]["work_title"]
    expected_h1 = f"《{work_title}》"
    h1_texts = [text for tag, text in inspector.headings if tag == "h1"]
    require(h1_texts == [expected_h1], "h1 must be the authoritative work title")
    require(
        f"<title>{expected_h1} · 小说构思人审报告</title>" in document,
        "document title must identify the work and report type",
    )
    levels = [int(tag[1]) for tag, text in inspector.headings if text]
    require(levels and levels[0] == 1, "heading hierarchy must begin with h1")
    for before, after in zip(levels, levels[1:]):
        require(after <= before + 1, "heading hierarchy skips a level")

    html_attrs = next(attrs for tag, attrs in inspector.attrs if tag == "html")
    require(html_attrs.get("lang") == "zh-CN", "html lang must be zh-CN")
    require(
        html_attrs.get("data-style-contract") == STYLE_CONTRACT["id"],
        "fixed style contract id mismatch",
    )
    meta_csp = [
        attrs.get("content")
        for tag, attrs in inspector.attrs
        if tag == "meta"
        and attrs.get("http-equiv", "").lower() == "content-security-policy"
    ]
    require(meta_csp == [CSP], "offline Content Security Policy mismatch")
    viewport = [
        attrs.get("content")
        for tag, attrs in inspector.attrs
        if tag == "meta" and attrs.get("name") == "viewport"
    ]
    require(viewport == ["width=device-width, initial-scale=1"], "viewport meta mismatch")

    for tag, attrs in inspector.attrs:
        for name, value in attrs.items():
            require(
                not INLINE_HANDLER_RE.match(name),
                f"inline event handler is forbidden: {name}",
            )
            if name in {"href", "src", "action", "formaction"}:
                require(
                    not REMOTE_SCHEME_RE.match(value.strip()),
                    f"external or executable URL is forbidden: {value}",
                )
            require(name != "hidden", f"hidden content is forbidden on <{tag}>")
        if tag in {"script", "link", "img", "iframe", "video", "audio", "source"}:
            if "src" in attrs:
                require(
                    attrs["src"].startswith("data:"),
                    f"resource is not self-contained: {attrs['src']}",
                )
            if tag == "link":
                require(False, "external stylesheet links are forbidden")

    for control_id, tag in inspector.controls.items():
        if tag in {"input", "textarea", "select"}:
            require(
                control_id in inspector.labels_for,
                f"form control lacks an explicit label: {control_id}",
            )
    require(not inspector.checked_controls, "author decisions must not be preselected")
    expected_radio_ids = {
        f"{domain}-{decision}"
        for domain in DECISION_DOMAINS
        for decision in ("approve", "revise")
    }
    require(expected_radio_ids <= inspector.ids, "decision controls are incomplete")

    try:
        embedded = json.loads(inspector.embedded_report)
    except json.JSONDecodeError as exc:
        raise ContractError(f"embedded report JSON is invalid: {exc}") from exc
    require(embedded == report, "embedded report JSON differs from authoritative input")

    required_css = {
        "@media (max-width: 760px)",
        "@media (prefers-reduced-motion: reduce)",
        "@media print",
        ":focus-visible",
        "--paper: #F7F3EA",
        "--ink: #18202A",
        "--blue: #2457A7",
        "--amber: #A65A00",
        "--card: #FFFDF8",
        "--border: #D7D0C3",
    }
    missing_css = sorted(token for token in required_css if token not in CSS)
    require(not missing_css, f"fixed style CSS is incomplete: {missing_css}")
    require("linear-gradient" not in CSS, "gradients are forbidden by the fixed style")
    require("@keyframes" not in CSS, "motion animation is forbidden by the fixed style")

    fragment_items = report["report_blueprint"]["fragments"]["items"]
    for item in fragment_items:
        require(item["id"] in inspector.ids, f"fragment is not visibly rendered: {item['id']}")
    class_tokens = {
        token
        for _, attrs in inspector.attrs
        for token in attrs.get("class", "").split()
    }
    required_graphics = {
        "control-spine-svg",
        "world-system-svg",
        "environment-svg",
        "story-flow-svg",
        "character-network-svg",
        "story-lanes",
        "relationship-network",
        "relationship-legend",
    }
    require(
        required_graphics <= class_tokens,
        f"SVG information graphics are incomplete: {sorted(required_graphics - class_tokens)}",
    )
    svg_attrs = [attrs for tag, attrs in inspector.attrs if tag == "svg"]
    require(len(svg_attrs) >= 5, "five primary SVG information graphics are required")
    require(
        all(
            attrs.get("role") == "img" and attrs.get("aria-labelledby")
            for attrs in svg_attrs
        ),
        "every SVG information graphic needs an accessible title and description binding",
    )
    return {
        "semantic_landmarks": True,
        "required_sections_visible": sorted(REQUIRED_SECTION_IDS),
        "heading_count": len(inspector.headings),
        "labelled_controls": len(
            [
                item
                for item, tag in inspector.controls.items()
                if tag in {"input", "textarea", "select"}
            ]
        ),
        "author_decisions_preselected": False,
        "embedded_report_exact": True,
        "offline_csp": True,
        "responsive_print_and_reduced_motion": True,
        "human_named_story_and_relationship_graphics": True,
        "svg_information_graphics": True,
    }


def validate_package(
    package: Path,
    assembly: Path,
    plan: Path,
    fragments: Path,
    r1: Path,
) -> dict[str, Any]:
    package = package.resolve()
    missing = sorted(name for name in PRIMARY_FILES if not (package / name).is_file())
    require(not missing, f"HTML package missing files: {missing}")
    upstream = validate_upstream(assembly, plan, fragments, r1)
    report = upstream["report"]
    report_sha = upstream["report_sha256"]

    manifest = load_json(package / "package-manifest.json")
    require(manifest.get("skill") == SKILL_NAME, "HTML manifest skill mismatch")
    require(manifest.get("verdict") == "ready", "HTML manifest is not ready")
    require(manifest.get("run_id") == report["run_id"], "HTML manifest run mismatch")
    verify_manifest(package, manifest)
    artifact = manifest.get("author_review_artifact", {})
    require(
        artifact.get("path") == "human-review-report.html",
        "author review artifact path mismatch",
    )
    require(
        artifact.get("report_sha256") == report_sha,
        "author review artifact report binding mismatch",
    )

    record = load_json(package / "render-record.json")
    require(record.get("skill") == SKILL_NAME, "render record skill mismatch")
    require(
        record.get("mode") == "deterministic_html_render",
        "render record mode mismatch",
    )
    require(record.get("run_id") == report["run_id"], "render record run mismatch")
    require(
        record.get("style_contract") == STYLE_CONTRACT,
        "fixed style contract was changed",
    )
    inputs = record.get("inputs", {})
    require(
        inputs
        == {
            "human-review-report.json": report_sha,
            "assembly-package-manifest.json": upstream["assembly_manifest_sha256"],
            "assembly-validation.json": upstream["assembly_validation_sha256"],
        },
        "render input bindings are stale or incorrect",
    )
    skill_dir = Path(__file__).resolve().parents[1]
    expected_skill_bindings = [
        {
            "path": path.relative_to(skill_dir).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in all_skill_files(skill_dir)
    ]
    require(
        record.get("skill_bindings") == expected_skill_bindings,
        "render record does not bind the current skill implementation",
    )

    html_path = package / "human-review-report.html"
    document = html_path.read_text(encoding="utf-8")
    structure = _validate_structure(document, report)
    expected = render_html(report, report_sha)
    require(document == expected, "HTML is not the deterministic rendering of the report")
    require(
        record.get("outputs")
        == {"human-review-report.html": sha256_file(html_path)},
        "render output binding mismatch",
    )
    require(
        artifact.get("sha256") == sha256_file(html_path),
        "author review artifact HTML hash mismatch",
    )
    return {
        "upstream": {
            "human_review_report_sha256": report_sha,
            "assembly_manifest_sha256": upstream["assembly_manifest_sha256"],
            "assembly_validation_sha256": upstream["assembly_validation_sha256"],
        },
        "fixed_style_contract": STYLE_CONTRACT["id"],
        "deterministic_render": True,
        "content_rewriting": False,
        "structure": structure,
        "html_sha256": sha256_file(html_path),
        "skill_file_count": len(expected_skill_bindings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate deterministic conception review HTML."
    )
    parser.add_argument("package", type=Path)
    parser.add_argument("--assembly", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--fragments", required=True, type=Path)
    parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    output_path = args.package.resolve() / "validation.json"
    try:
        evidence = validate_package(
            args.package, args.assembly, args.plan, args.fragments, args.r1
        )
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "verdict": "ready",
            "errors": [],
            "evidence": evidence,
        }
        write_json(output_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        result = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "verdict": "blocked",
            "errors": [str(exc)],
            "evidence": {},
        }
        write_json(output_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
