"""Deterministic H1-C offline HTML renderer and package runtime."""

from __future__ import annotations

import copy
import html
import importlib
import json
import math
import re
import shutil
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping, Sequence


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)

RENDER_CONTRACT = "offline-editorial-h1-v3"
DOM_CONTRACT = "h1-editorial-v3"
CONTENT_DIMENSION_KINDS = ("world", "storylines", "characters", "fragments")
REVIEW_OPERATION_KIND = "decision"
SECTION_KINDS = (*CONTENT_DIMENSION_KINDS, REVIEW_OPERATION_KIND)
SEMANTIC_ROLES = tuple(h1a.VISUAL_ROLE_SPECS)
COMPACT_STORY_ROLES = frozenset(
    {"control_logic_chain", "storyline_architecture", "major_event_timeline"}
)
NARRATIVE_MARKER_LABELS = {
    "control-node": "推进",
    "节点": "推进",
    "opening": "铺垫",
    "setup": "铺垫",
    "probe": "探问",
    "turning_point": "转折",
    "reveal": "揭示",
    "climax": "高潮",
    "payoff": "回收",
    "aftermath": "余波",
}
TIMELINE_NODE_PRESENTATIONS = {
    "危机埋点": "危机伏笔",
    "沈逾入场": "沈逾进入任务",
    "死亡与汇流": "顾衡死亡促成汇流",
    "生命探针": "R-07 的新意识显现",
    "旧影与新情": "顾衡旧记忆与 R-07 新感情",
    "伦理探针": "伦理冲突显形",
    "人质转折": "人质危机迫近",
    "决定影子": "尚未说出口的决定",
    "威胁回收": "威胁得到核验",
    "外部高潮": "现实行动完成阻断",
    "情感高潮": "沈逾执行最终告别",
    "关系回收": "这段关系得到确认",
    "开放余波": "仍然开放的问题",
}
TIMELINE_NODE_NARRATIVE_ROLES = {
    "危机埋点": "铺垫",
    "沈逾入场": "铺垫",
    "死亡与汇流": "转折",
    "生命探针": "探问",
    "旧影与新情": "关系变化",
    "伦理探针": "探问",
    "人质转折": "转折",
    "决定影子": "铺垫",
    "威胁回收": "回收",
    "外部高潮": "高潮",
    "情感高潮": "高潮",
    "关系回收": "回收",
    "开放余波": "余波",
}
TIMELINE_ROLE_MARKER_CLASSES = {
    "铺垫": "setup",
    "探问": "probe",
    "转折": "turning_point",
    "关系变化": "reveal",
    "高潮": "climax",
    "回收": "payoff",
    "余波": "aftermath",
    "推进": "control-node",
}
_CHINESE_ORDINALS = "一二三四五六七八九十"
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
_SKILL = _HERE.parents[1]
_SCHEMAS = _REPO / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
_ROOT_FILES = {
    "human-review-report.html",
    "render-record.json",
    "validation.json",
    "package-manifest.json",
}
_ROOT_PREFIXES = ("implementation/",)
_URL_BEARING_ATTRIBUTES = {
    "action",
    "archive",
    "background",
    "cite",
    "classid",
    "codebase",
    "data",
    "dynsrc",
    "formaction",
    "icon",
    "itemid",
    "longdesc",
    "lowsrc",
    "manifest",
    "ping",
    "poster",
    "profile",
    "src",
    "srcset",
    "usemap",
    "xlink:href",
    "xmlns",
    "xmlns:xlink",
}
_CSS_URL_PATTERN = re.compile(r"(?:url\s*\(|@import\b)", re.IGNORECASE)
_VISIBLE_TIMELINE_MODEL_PATTERN = re.compile(
    r"(?:\bP(?:[1-9]|10)\b|\b(?:setup|probe|turning_point|climax|payoff|"
    r"aftermath)\b|埋点|探针|决定影子)",
    re.IGNORECASE,
)


class H1CError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class HtmlReceipt:
    package_root: Path
    manifest: dict[str, Any]
    transition: Any


def _fail(code: str, message: str) -> None:
    raise H1CError(code, message)


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
        _fail("H1C_OUTPUT_EXISTS", str(path))
    _write(path, value)


def _tree_inventory(root: Path) -> list[dict[str, str]]:
    return [
        rt.artifact_reference(path, root=root)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


def _copy_exact(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        _fail("H1C_COPY_DRIFT", str(source))


def _implementation_paths() -> dict[str, Path]:
    return {
        "skill/run_v2.py": _HERE,
        "skill/SKILL.md": _SKILL / "SKILL.md",
        "skill/v2-html-contract.md": (
            _SKILL / "references" / "v2-html-contract.md"
        ),
        "h1-a-visible-copy/run_v2.py": Path(h1a.__file__).resolve(),
        "h1-a-visible-copy/review-plan-contract.md": (
            Path(h1a.__file__).resolve().parents[1]
            / "references"
            / "review-plan-contract.md"
        ),
        "schemas/h1-review-plan.schema.json": (
            _SCHEMAS / "h1-review-plan.schema.json"
        ),
        "schemas/human-review-report.schema.json": (
            _SCHEMAS / "human-review-report.schema.json"
        ),
        "schemas/h1-workspace-state.schema.json": (
            _SCHEMAS / "h1-workspace-state.schema.json"
        ),
        "schemas/package-manifest.schema.json": (
            _SCHEMAS / "package-manifest.schema.json"
        ),
    }


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _attr(value: Any) -> str:
    return _e(value)


def _encoded_ids(values: Sequence[str]) -> str:
    return json.dumps(
        list(values),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _list(items: Sequence[Any], css: str = "compact") -> str:
    return (
        f'<ul class="{css}">'
        + "".join(f"<li>{_e(item)}</li>" for item in items)
        + "</ul>"
    )


def _sources(items: Sequence[str]) -> str:
    return (
        '<p class="sources"><strong>延伸阅读：</strong>'
        + "、".join(_e(item) for item in items)
        + "</p>"
    )


def _control_card(item: Mapping[str, Any]) -> str:
    return (
        f'<article class="control-card" data-element-id="{_attr(item["id"])}">'
        f'<h3>{_e(item["title"])}</h3>'
        f'<p>{_e(item["definition"])}</p>'
        '</article>'
    )


def _responsibility_card(item: Mapping[str, Any]) -> str:
    """Keep a scalar-backed module traceable without repeating its definition."""

    return (
        f'<article class="control-card" data-element-id="{_attr(item["id"])}">'
        f'<h3>{_e(item["title"])}</h3>'
        f'<p>{_e(item["responsibility"])}</p>'
        '</article>'
    )


def _modules_for_scalar_values(
    modules: Sequence[Mapping[str, Any]],
    values: Sequence[str],
    *,
    label: str,
) -> list[Mapping[str, Any]]:
    """Resolve each duplicated report scalar to one exact author-facing module."""

    resolved: list[Mapping[str, Any]] = []
    for value in values:
        matches = [item for item in modules if item["definition"] == value]
        if len(matches) != 1:
            _fail(
                "H1C_HTML_PROJECTION_INVALID",
                f"{label} must map to exactly one visible module",
            )
        resolved.append(matches[0])
    return resolved


def _editorial_detail_card(
    item: Mapping[str, Any], detail_label: str, css_class: str
) -> str:
    parts = re.split(r"(?<=[。！？.!?])", item["definition"], maxsplit=1)
    synopsis = parts[0]
    detail = parts[1].strip() if len(parts) > 1 else ""
    drilldown = ""
    if detail:
        drilldown = (
            f"<details><summary>{_e(detail_label)}</summary>"
            f"<p>{_e(detail)}</p></details>"
        )
    return (
        f'<article class="control-card {_attr(css_class)}" '
        f'data-element-id="{_attr(item["id"])}">'
        f'<h3>{_e(item["title"])}</h3><p>{_e(synopsis)}</p>'
        f"{drilldown}</article>"
    )


def _environment_card(item: Mapping[str, Any]) -> str:
    return _editorial_detail_card(
        item, "展开看看这里会发生什么", "environment-card"
    )


def _character_card(item: Mapping[str, Any]) -> str:
    lines = [line.strip() for line in item["definition"].splitlines() if line.strip()]
    if len(lines) < 2 or any("｜" not in line for line in lines[1:]):
        return _editorial_detail_card(
            item, "展开了解这个人物", "character-profile-card"
        )
    details = []
    for line in lines[1:]:
        label, value = line.split("｜", 1)
        details.append(f"<dt>{_e(label)}</dt><dd>{_e(value)}</dd>")
    return (
        f'<article class="control-card character-profile-card" '
        f'data-element-id="{_attr(item["id"])}">'
        f'<h3>{_e(item["title"])}</h3><p>{_e(lines[0])}</p>'
        '<details><summary>展开了解这个人物</summary>'
        f'<dl class="character-definition">{"".join(details)}</dl>'
        '</details></article>'
    )


def _nullable(value: Any) -> str:
    return "无" if value is None else str(value)


def _timeline_phase_label(value: Any) -> str:
    label = str(value or "").strip()
    match = re.fullmatch(r"P([1-9]|10)", label)
    if match:
        index = int(match.group(1))
        return f"第{_CHINESE_ORDINALS[index - 1]}阶段"
    return label or "时间待定"


def _timeline_node_label(node: Mapping[str, Any]) -> str:
    return TIMELINE_NODE_PRESENTATIONS.get(node["label"], node["label"])


def _timeline_narrative_role(node: Mapping[str, Any]) -> str:
    return TIMELINE_NODE_NARRATIVE_ROLES.get(
        node["label"], NARRATIVE_MARKER_LABELS[node["kind"]]
    )


def _timeline_marker_class(node: Mapping[str, Any]) -> str:
    return TIMELINE_ROLE_MARKER_CLASSES[_timeline_narrative_role(node)]


def _visual_prose_fallback(visual: Mapping[str, Any]) -> str:
    items: list[tuple[str, str]] = []
    items.extend(
        (group["label"], group["summary"])
        for group in sorted(visual["groups"], key=lambda item: item["order"])
    )
    if (
        visual["semantic_role"] in COMPACT_STORY_ROLES
        or (not visual["groups"] and not visual["edges"])
    ):
        items.extend(
            (_timeline_node_label(node), node["summary"])
            if visual["visual_kind"] == "timeline"
            else (node["label"], node["summary"])
            for node in sorted(visual["nodes"], key=lambda item: item["order"])
        )
    items.extend(
        (edge["relation_label"], edge["summary"])
        for edge in sorted(visual["edges"], key=lambda item: item["order"])
    )
    return (
        "<details><summary>不用看图，也可以这样理解</summary><ul>"
        + "".join(
            f"<li><strong>{_e(label)}</strong><span>{_e(summary)}</span></li>"
            for label, summary in items
        )
        + "</ul></details>"
    )


def _visual_prose_caption(visual: Mapping[str, Any]) -> str:
    return (
        '<figcaption class="visual-text-equivalent"\n'
        f'    data-visual-id="{_attr(visual["id"])}"\n'
        '    data-text-equivalent-module-id="'
        f'{_attr(visual["text_equivalent_module_id"])}">\n'
        f'    {_visual_prose_fallback(visual)}\n'
        "  </figcaption>"
    )


def _visual_positions(
    visual: Mapping[str, Any],
) -> tuple[int, int, dict[str, tuple[float, float]]]:
    nodes = visual["nodes"]
    if visual["visual_kind"] == "timeline":
        groups = visual["groups"]
        lane_index = {
            group["id"]: index for index, group in enumerate(groups)
        }
        temporal_labels = list(
            dict.fromkeys(node["temporal_label"] for node in nodes)
        )
        temporal_index = {
            label: index for index, label in enumerate(temporal_labels)
        }
        width = max(760, 210 * len(temporal_labels) + 140)
        height = max(280, 120 * max(1, len(groups)) + 100)
        positions = {
            node["id"]: (
                130 + temporal_index[node["temporal_label"]] * 210,
                100 + lane_index[node["group_id"]] * 110,
            )
            for node in nodes
        }
        return width, height, positions
    columns = max(1, math.ceil(math.sqrt(len(nodes))))
    rows = math.ceil(len(nodes) / columns)
    width = max(680, columns * 220 + 100)
    height = max(260, rows * 150 + 100)
    positions = {
        node["id"]: (
            120 + ((node["order"] - 1) % columns) * 220,
            100 + ((node["order"] - 1) // columns) * 150,
        )
        for node in nodes
    }
    if visual["visual_kind"] == "flow":
        width = max(680, len(nodes) * 210 + 100)
        height = 300
        positions = {
            node["id"]: (110 + (node["order"] - 1) * 210, 145)
            for node in nodes
        }
    return width, height, positions


def render_visual(visual: Mapping[str, Any]) -> str:
    if visual["visual_kind"] == "timeline":
        unknown_kinds = sorted(
            {
                str(node["kind"])
                for node in visual["nodes"]
                if node["kind"] not in NARRATIVE_MARKER_LABELS
            }
        )
        if unknown_kinds:
            _fail(
                "H1C_HTML_VISUAL_INVALID",
                f"unknown timeline marker kinds: {unknown_kinds}",
            )
    width, height, positions = _visual_positions(visual)
    marker_id = f"marker-{visual['id']}"
    groups = []
    if visual["visual_kind"] == "timeline":
        for group in visual["groups"]:
            y = 100 + (group["order"] - 1) * 110
            groups.append(
                f'<g data-group-id="{_attr(group["id"])}">'
                f"<title>{_e(group['label'])}：{_e(group['summary'])}</title>"
                f'<line class="lane" x1="45" y1="{y}" x2="{width - 35}" y2="{y}"/>'
                f'<text x="48" y="{y - 16}">{_e(group["label"])}</text></g>'
            )
    edges = []
    for edge in visual["edges"]:
        start = positions[edge["from_node_id"]]
        end = positions[edge["to_node_id"]]
        marker = ""
        if edge["direction"] in {"directed", "bidirectional"}:
            marker += f' marker-end="url(#{_attr(marker_id)})"'
        if edge["direction"] == "bidirectional":
            marker += f' marker-start="url(#{_attr(marker_id)})"'
        edges.append(
            f'<g data-edge-id="{_attr(edge["id"])}" '
            f'data-direction="{_attr(edge["direction"])}" '
            f'data-order="{edge["order"]}">'
            f"<title>{_e(edge['relation_label'])}：{_e(edge['summary'])}</title>"
            f'<line class="edge" x1="{start[0]}" y1="{start[1]}" '
            f'x2="{end[0]}" y2="{end[1]}"{marker}/>'
            f'<text class="edge-label" x="{(start[0] + end[0]) / 2:.1f}" '
            f'y="{(start[1] + end[1]) / 2 - 8:.1f}">'
            f'{_e(edge["relation_label"])}</text></g>'
        )
    nodes = []
    for node in visual["nodes"]:
        x, y = positions[node["id"]]
        marker_label = (
            _timeline_narrative_role(node)
            if visual["visual_kind"] == "timeline"
            else ""
        )
        marker_class = (
            _timeline_marker_class(node)
            if visual["visual_kind"] == "timeline"
            else node["kind"]
        )
        visible_node_label = (
            _timeline_node_label(node)
            if visual["visual_kind"] == "timeline"
            else node["label"]
        )
        visible_time_label = (
            _timeline_phase_label(node["temporal_label"])
            if visual["visual_kind"] == "timeline"
            else _nullable(node["temporal_label"])
        )
        timeline_subtitle = ""
        if visual["visual_kind"] == "timeline":
            timeline_subtitle = (
                f'<text class="small" x="{x}" y="{y + 18}" '
                f'text-anchor="middle">{_e(visible_time_label)} · '
                f'{_e(marker_label)}</text>'
            )
        nodes.append(
            f'<g class="node marker-{_attr(marker_class)}" '
            f'data-node-id="{_attr(node["id"])}" '
            f'data-kind="{_attr(node["kind"])}" '
            f'data-order="{node["order"]}" '
            f'data-group-id="{_attr(_nullable(node["group_id"]))}">'
            f"<title>{_e(visible_node_label)}：{_e(node['summary'])}</title>"
            f'<rect x="{x - 92}" y="{y - 34}" width="184" height="68" rx="12"/>'
            f'<text x="{x}" y="{y - 3}" text-anchor="middle">{_e(visible_node_label)}</text>'
            f'{timeline_subtitle}</g>'
        )
    highlights = ""
    if visual["semantic_role"] not in COMPACT_STORY_ROLES:
        highlights = (
            '<ul class="visual-highlights">'
            + "".join(
                f'<li><strong>{_e(item["label"])}</strong>'
                f'<span>{_e(item["summary"])}</span></li>'
                for item in visual["nodes"]
            )
            + "</ul>"
        )
    prose_caption = _visual_prose_caption(visual)
    marker_legend = ""
    if visual["visual_kind"] == "timeline":
        marker_roles = list(
            dict.fromkeys(
                (
                    _timeline_marker_class(node),
                    _timeline_narrative_role(node),
                )
                for node in visual["nodes"]
            )
        )
        marker_legend = (
            '<ul class="marker-legend" aria-label="故事节奏图例">'
            + "".join(
                f'<li class="marker-{_attr(marker_class)}">'
                f'<span aria-hidden="true"></span>'
                f'{_e(role)}</li>'
                for marker_class, role in marker_roles
            )
            + "</ul>"
        )
    return f"""
<figure class="visual-card" data-element-id="{_attr(visual["id"])}"
 data-visual-id="{_attr(visual["id"])}"
 data-semantic-role="{_attr(visual["semantic_role"])}"
 data-text-equivalent-module-id="{_attr(visual["text_equivalent_module_id"])}">
  <h3>{_e(visual["title"])}</h3>
  <p class="visual-intro">{_e(visual["review_purpose"])}</p>
  {marker_legend}
  <div class="svg-scroll" tabindex="0" aria-label="{_attr(visual["title"])}图示">
    <svg class="semantic-visual" data-visual-id="{_attr(visual["id"])}"
      data-semantic-role="{_attr(visual["semantic_role"])}"
      data-text-equivalent-module-id="{_attr(visual["text_equivalent_module_id"])}"
      viewBox="0 0 {width} {height}" role="img"
      aria-labelledby="{_attr(visual["id"])}-title {_attr(visual["id"])}-desc">
      <title id="{_attr(visual["id"])}-title">{_e(visual["title"])}</title>
      <desc id="{_attr(visual["id"])}-desc">{_e(visual["review_purpose"])}</desc>
      <defs><marker id="{_attr(marker_id)}" markerWidth="8" markerHeight="8"
       refX="7" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z"/></marker></defs>
      {''.join(groups)}{''.join(edges)}{''.join(nodes)}
    </svg>
  </div>
  {highlights}
  {prose_caption}
</figure>"""


def _render_world(report: Mapping[str, Any], visuals: Sequence[Mapping[str, Any]]) -> str:
    value = report["world"]
    all_world_items = [
        *value["systems"],
        *value["environments"],
        *value["event_conditions"],
    ]
    definition_item, logic_item = _modules_for_scalar_values(
        all_world_items,
        [value["definition"], value["operating_logic"]],
        label="world overview scalars",
    )
    overview_item_ids = {definition_item["id"], logic_item["id"]}
    systems = [
        item
        for item in value["systems"]
        if item["id"] not in overview_item_ids
    ]
    activity_exclusions = set(value["constraints"] + value["boundaries"])
    activities = [
        item
        for item in value["event_conditions"]
        if item["definition"] not in activity_exclusions
    ]
    boundary_items = [
        item
        for item in value["event_conditions"]
        if item["definition"] in activity_exclusions
    ]
    logic_block = (
        ""
        if logic_item["id"] == definition_item["id"]
        else (
            f'<div class="reading-experience" data-element-id="{_attr(logic_item["id"])}">'
            f'<h3>{_e(logic_item["title"])}</h3><p>{_e(value["operating_logic"])}</p>'
            f'<p>{_e(logic_item["responsibility"])}</p></div>'
        )
    )
    return f"""
<section id="section-world" aria-labelledby="heading-world">
 <p class="section-number">01</p><h2 id="heading-world">这个故事发生在怎样的世界</h2>
 {_responsibility_card(definition_item)}
 {logic_block}
 <h3>国家与组织怎样相互制约</h3><div class="cards">{''.join(_editorial_detail_card(item, "查看完整分权与协作机制", "world-detail-card") for item in systems)}</div>
 <h3>这个世界里正在进行什么</h3><div class="cards">{''.join(_editorial_detail_card(item, "查看完整活动过程", "world-detail-card") for item in activities)}</div>
 <h3>故事真正发生的地方</h3>
 {''.join(render_visual(item) for item in visuals)}
 <div class="cards environment-cards">{''.join(_environment_card(item) for item in value["environments"])}</div>
 <div class="closing-note"><h3>这部小说不会越过的边界</h3>
 {''.join(f'<h4>{_e(item["title"])}</h4><p>{_e(item["definition"])}</p>' for item in boundary_items)}</div>
</section>"""


def _render_storylines(report: Mapping[str, Any], visuals: Sequence[Mapping[str, Any]]) -> str:
    value = report["storylines"]
    all_story_items = [
        *value["lines"],
        *value["connections"],
        *value["major_events"],
    ]
    rhythm_items = [
        item
        for item in all_story_items
        if item["definition"] == value["suspense_conflict_rhythm"]
    ]
    if len(rhythm_items) != 1:
        _fail(
            "H1C_HTML_PROJECTION_INVALID",
            "story rhythm must map to exactly one visible module",
        )
    rhythm_item = rhythm_items[0]
    subject_items = [
        item for item in all_story_items if item["definition"] == value["story_subject"]
    ]
    if len(subject_items) != 1:
        _fail(
            "H1C_HTML_PROJECTION_INVALID",
            "story subject must map to exactly one visible module",
        )
    subject_item = subject_items[0]
    constraint_items = _modules_for_scalar_values(
        all_story_items, value["constraints"], label="story constraints"
    )
    scalar_items = list(
        {item["id"]: item for item in [subject_item, rhythm_item, *constraint_items]}.values()
    )
    scalar_item_ids = {item["id"] for item in scalar_items}
    rhythm_block = (
        ""
        if rhythm_item["id"] == subject_item["id"]
        else (
            '<div class="reading-experience"><h3>读起来应该是什么感觉</h3>'
            f'{_control_card(rhythm_item)}</div>'
        )
    )
    represented_ids = {subject_item["id"], rhythm_item["id"]}
    constraint_render_items = [
        item for item in constraint_items if item["id"] not in represented_ids
    ]
    constraint_block = (
        '<div class="closing-note"><h3>故事不能被写偏的地方</h3>'
        f'<div class="cards">{"".join(_control_card(item) for item in constraint_render_items)}</div></div>'
        if constraint_render_items
        else ""
    )
    lines = [item for item in value["lines"] if item["id"] not in scalar_item_ids]
    connections = [
        item for item in value["connections"] if item["id"] not in scalar_item_ids
    ]
    major_events = [
        item for item in value["major_events"] if item["id"] not in scalar_item_ids
    ]
    return f"""
<section id="section-storylines" aria-labelledby="heading-storylines">
 <p class="section-number">02</p><h2 id="heading-storylines">故事会怎样一步步走到结局</h2>
 {_responsibility_card(subject_item)}
 {''.join(render_visual(item) for item in visuals)}
 <h3>共同推动小说的故事线</h3><div class="cards">{''.join(_control_card(item) for item in lines)}</div>
 <h3>这些线怎样汇到一起</h3><div class="cards">{''.join(_control_card(item) for item in connections)}</div>
 <h3>改变故事方向的关键节点</h3><div class="cards">{''.join(_control_card(item) for item in major_events)}</div>
 {rhythm_block}
 {constraint_block}
</section>"""


def _render_characters(report: Mapping[str, Any], visuals: Sequence[Mapping[str, Any]]) -> str:
    value = report["characters"]
    collections = (
        "core_characters",
        "supporting_characters",
        "relationship_networks",
        "role_coverage",
    )
    all_character_items = [item for key in collections for item in value[key]]
    constraint_items = _modules_for_scalar_values(
        all_character_items, value["constraints"], label="character constraints"
    )
    constraint_ids = {item["id"] for item in constraint_items}
    core_characters = [
        item for item in value["core_characters"] if item["id"] not in constraint_ids
    ]
    supporting_characters = [
        item
        for item in value["supporting_characters"]
        if item["id"] not in constraint_ids
    ]
    relationship_networks = [
        item
        for item in value["relationship_networks"]
        if item["id"] not in constraint_ids
    ]
    role_coverage = [
        item for item in value["role_coverage"] if item["id"] not in constraint_ids
    ]
    return f"""
<section id="section-characters" aria-labelledby="heading-characters">
 <p class="section-number">03</p><h2 id="heading-characters">这些人为什么会作出这样的选择</h2>
 {''.join(render_visual(item) for item in visuals)}
 <p class="lead">先看每个人在故事中的位置和行动，再展开查看其外貌、性格、生活与社交定义。</p>
 <h3>核心人物</h3><div class="cards character-cards">{''.join(_character_card(item) for item in core_characters)}</div>
 <h3>让故事真正运转起来的人</h3><div class="cards character-cards">{''.join(_character_card(item) for item in supporting_characters)}</div>
 <h3>关系会怎样改变他们</h3><div class="cards">{''.join(_control_card(item) for item in relationship_networks)}</div>
 <h3>人物系统覆盖到哪里</h3><div class="cards">{''.join(_control_card(item) for item in role_coverage)}</div>
 <div class="closing-note"><h3>人物不能被写偏的地方</h3>
 <div class="cards">{''.join(_control_card(item) for item in constraint_items)}</div></div>
</section>"""


def _render_fragments(report: Mapping[str, Any]) -> str:
    fragments = "".join(
        f'<article class="fragment" data-element-id="{_attr(item["id"])}">'
        f'<h3>{_e(item["title"])}</h3>'
        f'<div class="fragment-text">{_e(item["text"]).replace(chr(10), "<br>")}</div>'
        f'</article>'
        for item in report["fragments"]
    )
    return (
        '<section id="section-fragments" aria-labelledby="heading-fragments">'
        '<p class="section-number">04</p><h2 id="heading-fragments">先读几页这部小说</h2>'
        '<p class="lead">下面不是情节说明，而是它真正写出来时应有的声音、距离与温度。</p>'
        f"{fragments}</section>"
    )


def _render_decision(report: Mapping[str, Any]) -> str:
    prompt = report["decision_prompts"][0]
    return f"""
<section id="section-decision" aria-labelledby="heading-decision">
 <p class="section-number">评审结论</p>
 <h2 id="heading-decision">{_e(prompt["question"])}</h2>
 <p>如果这就是你想写的小说，可以批准构思；如果方向正确但某些结论需要调整，请指出具体部分；如果核心故事不成立，可以否决并重新构思。</p>
 <p class="pending">当前尚未作出决定。</p>
</section>"""


CSS = """
:root{color-scheme:light;--paper:#f4f0e8;--ink:#1e2428;--muted:#667078;
--blue:#24576b;--amber:#9a5a24;--line:#d1c8b9;--card:#fffdf8;--soft:#e8eee9}
*{box-sizing:border-box}html{background:var(--paper);color:var(--ink);
font-family:"Noto Serif CJK SC","Source Han Serif SC","Songti SC",serif}
body{margin:0;line-height:1.75;overflow-wrap:anywhere}a{color:var(--blue)}
.skip-link{position:absolute;left:.5rem;top:.5rem;background:#fff;padding:.6rem;
transform:translateY(-200%)}.skip-link:focus{transform:none}
header,nav,main,footer{max-width:1080px;margin:auto;padding:1rem 1.5rem}
header{padding-top:4rem;padding-bottom:2.5rem;border-bottom:1px solid var(--line)}
header .eyebrow,.section-number{font-family:system-ui,sans-serif;color:var(--amber);
font-weight:700;letter-spacing:.12em}h1{font-size:clamp(2.2rem,6vw,4.4rem);
line-height:1.1;margin:.25rem 0 1rem}.pitch{max-width:820px;
font-size:clamp(1.15rem,2.2vw,1.55rem);line-height:1.7}.promise{max-width:780px;color:var(--muted)}
section{padding:4rem 0;border-top:1px solid var(--line)}h2{font-size:clamp(1.8rem,4vw,2.8rem);
line-height:1.25;margin:.2rem 0 1.2rem}h3{margin-bottom:.35rem}.lead{font-size:1.2rem;max-width:760px}
.section-number{margin-bottom:0}nav{position:sticky;top:0;z-index:2;
background:rgba(244,240,232,.96);border-bottom:1px solid var(--line)}
nav ol{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.5rem;padding:0;margin:.3rem 0}
nav li{list-style:none;padding:.45rem}.path-question{display:none}.cards{display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.control-card,.visual-card,.fragment{
background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1.2rem;margin:1rem 0}
.compact{padding-left:1.25rem}.control-card h3{font-size:1.2rem}.story-effect{color:var(--muted)}
.environment-card details,.world-detail-card details,.character-profile-card details{border-top:1px solid var(--line);margin-top:.8rem;padding-top:.65rem}
.environment-card summary,.world-detail-card summary,.character-profile-card summary{cursor:pointer;color:var(--blue);font-family:system-ui,sans-serif;font-weight:650}
.environment-card details p,.world-detail-card details p{color:var(--muted);margin-bottom:.2rem}
.character-definition{display:grid;grid-template-columns:minmax(6rem,8rem) 1fr;gap:.55rem 1rem;margin:1rem 0 0}
.character-definition dt{font-family:system-ui,sans-serif;font-weight:700;color:var(--amber)}
.character-definition dd{margin:0;color:var(--muted)}
.boundary{border-top:1px solid var(--line);padding-top:.75rem;font-size:.92rem}
.avoid{display:block;margin-top:.35rem;color:#7a4232}.closing-note,.reading-experience{
background:var(--soft);border-left:4px solid var(--blue);padding:1rem 1.25rem;margin:1.5rem 0}
.svg-scroll{overflow-x:auto;border:1px solid var(--line);background:#fff;padding:.5rem}
.semantic-visual{display:block;min-width:680px;width:100%;height:auto}
.semantic-visual .node rect{fill:#eef4ff;stroke:var(--blue);stroke-width:2}
.semantic-visual .edge,.semantic-visual .lane{stroke:var(--blue);stroke-width:2;fill:none}
.semantic-visual marker path{fill:var(--blue)}.semantic-visual text{fill:var(--ink);font-size:14px}
.semantic-visual .small,.semantic-visual .edge-label{font-size:11px;fill:var(--muted)}
.semantic-visual .marker-opening rect,.semantic-visual .marker-setup rect{fill:#f7f3e8;stroke:#94723d}
.semantic-visual .marker-probe rect{fill:#eef7f5;stroke:#28756b}
.semantic-visual .marker-turning_point rect,.semantic-visual .marker-reveal rect{fill:#f5eef8;stroke:#79518f}
.semantic-visual .marker-climax rect{fill:#faece9;stroke:#ad4438;stroke-width:3}
.semantic-visual .marker-payoff rect{fill:#edf4fb;stroke:#356d9f}
.semantic-visual .marker-aftermath rect{fill:#f1f1f1;stroke:#727272}
.marker-legend{display:flex;flex-wrap:wrap;gap:.55rem 1rem;list-style:none;padding:0;margin:.75rem 0 1rem;color:var(--muted);font-size:.84rem}
.marker-legend li{display:flex;align-items:center;gap:.35rem}.marker-legend span{display:inline-block;width:.8rem;height:.8rem;border-radius:.2rem;background:#eef4ff;border:2px solid var(--blue)}
.marker-legend .marker-opening span,.marker-legend .marker-setup span{background:#f7f3e8;border-color:#94723d}.marker-legend .marker-probe span{background:#eef7f5;border-color:#28756b}.marker-legend .marker-turning_point span,.marker-legend .marker-reveal span{background:#f5eef8;border-color:#79518f}.marker-legend .marker-climax span{background:#faece9;border-color:#ad4438}.marker-legend .marker-payoff span{background:#edf4fb;border-color:#356d9f}.marker-legend .marker-aftermath span{background:#f1f1f1;border-color:#727272}
.visual-text-equivalent{color:var(--muted);font-size:.94rem;padding-top:.7rem}
.visual-text-equivalent details{border-top:1px solid var(--line);padding-top:.65rem}
.visual-text-equivalent summary{cursor:pointer;color:var(--blue);font-weight:650}
.visual-text-equivalent ul{display:grid;gap:.5rem;padding-left:1.25rem}
.visual-text-equivalent li strong{color:var(--ink);margin-right:.35rem}
.visual-highlights{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem 1rem;
padding:0;list-style:none}.visual-highlights li{border-left:3px solid var(--line);padding:.35rem .65rem}
.visual-highlights span{display:block;color:var(--muted);font-size:.9rem}
.fragment{max-width:760px;margin:1.5rem auto;padding:clamp(1.2rem,4vw,2.5rem)}
.fragment h3{text-align:center;margin-top:0}.fragment-text{max-width:62ch;margin:auto;font-size:1.08rem;line-height:2}
.pending{color:var(--amber);font-weight:700}:focus-visible{outline:3px solid #d97706;outline-offset:3px}
@media(max-width:640px){header,nav,main,footer{padding:.75rem}.cards,.visual-highlights{grid-template-columns:1fr}
nav ol{grid-template-columns:repeat(2,1fr)}.semantic-visual{min-width:680px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important}}
@media print{html{background:#fff}body{font-size:11pt}header,nav,main,footer{max-width:none}
.control-card,.visual-card,.fragment{break-inside:avoid;box-shadow:none}.svg-scroll{overflow:visible}
.semantic-visual{min-width:0}}
"""

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "font-src 'none'; script-src 'none'; connect-src 'none'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none'"
)


def render_html(report: Mapping[str, Any]) -> str:
    visuals_by_section = {
        section: [
            visual
            for visual in report["visual_models"]
            if visual["section_id"]
            == next(
                item["section_id"]
                for item in report["visual_models"]
                if item["semantic_role"]
                == {
                    "world": "world_environment_map",
                    "storylines": "control_logic_chain",
                    "characters": "character_relationship_network",
                }[section]
            )
        ]
        for section in ("world", "storylines", "characters")
    }
    content_steps = report["review_path"][:4]
    nav = "".join(
        f'<li><a href="#section-{_attr(step["kind"])}" '
        f'data-path-id="{_attr(step["id"])}" '
        f'data-path-kind="{_attr(step["kind"])}" '
        f'data-visible-element-ids="'
        f'{_attr(_encoded_ids(step["visible_element_ids"]))}">'
        f'<span class="path-title">'
        f'{_e(step["title"])}'
        f'<span class="path-question">{_e(step["review_question"])} · '
        f'{step["estimated_seconds"]}秒</span></span></a></li>'
        for step in content_steps
    )
    return f"""<!doctype html>
<html lang="zh-CN" data-render-contract="{DOM_CONTRACT}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{_attr(CSP)}">
<meta name="referrer" content="no-referrer">
<title>{_e(report["title"])}</title><style>{CSS}</style></head>
<body><a class="skip-link" href="#main-content">跳到主要内容</a>
<header><p class="eyebrow">小说构思人审报告</p>
<h1>{_e(report["title"])}</h1>
<p class="pitch">{_e(report["storylines"]["story_subject"])}</p>
<p class="promise">{_e(report["world"]["definition"])}</p>
</header>
<nav aria-label="构思评审的四个部分"><ol>{nav}</ol></nav>
<main id="main-content">
{_render_world(report, visuals_by_section["world"])}
{_render_storylines(report, visuals_by_section["storylines"])}
{_render_characters(report, visuals_by_section["characters"])}
{_render_fragments(report)}
{_render_decision(report)}
</main>
<footer><p>这份报告只谈故事本身，便于作者直接判断方向。</p></footer>
</body></html>"""


class _Inspector(HTMLParser):
    _VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
    _BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "body", "br", "dd",
        "details", "dialog", "div", "dl", "dt", "fieldset", "figcaption",
        "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
        "header", "hgroup", "hr", "li", "main", "nav", "ol", "p", "pre",
        "section", "summary", "table", "tbody", "td", "text", "tfoot", "th",
        "thead", "title", "tr", "ul", "desc",
    }
    _EXCLUDED_TEXT_TAGS = {"script", "style", "template", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()
        self.tags: list[str] = []
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.title_text: list[str] = []
        self.h1_text: list[str] = []
        self.svg_title_text: dict[str, list[str]] = {}
        self.style_text: list[str] = []
        self.visible_text: list[str] = []
        self.hidden_text: list[str] = []
        self.invalid_visibility: list[str] = []
        self._capture: str | None = None
        self._stack: list[str] = []
        self._flow_stack: list[tuple[str, bool, bool]] = []
        self._visible_buffer: list[str] = []
        self._svg_id: str | None = None
        self._in_head = False
        self._in_body = False

    def _flush_visible_block(self) -> None:
        text = "".join(self._visible_buffer)
        if text.strip():
            self.visible_text.append(text)
        self._visible_buffer.clear()

    def _flow_state(self) -> tuple[bool, bool]:
        if not self._flow_stack:
            return False, False
        _, excluded, hidden = self._flow_stack[-1]
        return excluded, hidden

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag in self._BLOCK_TAGS:
            self._flush_visible_block()
        self.tags.append(tag)
        self.attrs.append((tag, values))
        item_id = values.get("id")
        if item_id:
            if item_id in self.ids:
                self.duplicates.add(item_id)
            self.ids.add(item_id)
        if tag == "head":
            self._in_head = True
        if tag == "body":
            self._in_body = True
        parent_excluded, parent_hidden = self._flow_state()
        aria_hidden = values.get("aria-hidden", "").strip().lower()
        if aria_hidden not in {"", "true", "false"}:
            self.invalid_visibility.append(f"{tag}:aria-hidden={aria_hidden}")
        excluded = parent_excluded or tag in self._EXCLUDED_TEXT_TAGS
        hidden = parent_hidden or "hidden" in values or aria_hidden == "true"
        if tag == "style":
            self._capture = "style"
        if tag == "svg":
            self._svg_id = values.get("data-visual-id")
        if tag == "title" and self._in_head and self._svg_id is None:
            self._capture = "document-title"
        elif tag == "title" and self._stack and self._stack[-1] == "svg":
            self._capture = f"svg-title:{self._svg_id or ''}"
            self.svg_title_text.setdefault(self._svg_id or "", [])
        elif tag == "h1":
            self._capture = "h1"
        if tag not in self._VOID_TAGS:
            self._stack.append(tag)
            self._flow_stack.append((tag, excluded, hidden))

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BLOCK_TAGS:
            self._flush_visible_block()
        if tag in {"title", "h1", "style"}:
            self._capture = None
        if tag == "svg":
            self._svg_id = None
        if tag == "head":
            self._in_head = False
        if tag == "body":
            self._in_body = False
        if self._stack:
            if self._stack[-1] == tag:
                self._stack.pop()
            elif tag in self._stack:
                del self._stack[self._stack.index(tag):]
        if self._flow_stack:
            if self._flow_stack[-1][0] == tag:
                self._flow_stack.pop()
            else:
                matching = next(
                    (
                        index for index, frame in enumerate(self._flow_stack)
                        if frame[0] == tag
                    ),
                    None,
                )
                if matching is not None:
                    del self._flow_stack[matching:]

    def handle_data(self, data: str) -> None:
        if self._capture == "document-title":
            self.title_text.append(data)
        elif self._capture == "h1":
            self.h1_text.append(data)
        elif self._capture and self._capture.startswith("svg-title:"):
            visual_id = self._capture.removeprefix("svg-title:")
            self.svg_title_text[visual_id].append(data)
        elif self._capture == "style":
            self.style_text.append(data)
        if self._in_body and data.strip():
            excluded, hidden = self._flow_state()
            if hidden:
                self.hidden_text.append(data)
            elif not excluded:
                self._visible_buffer.append(data)

    def close(self) -> None:
        super().close()
        self._flush_visible_block()


def validate_html_document(
    document: str, report: Mapping[str, Any]
) -> dict[str, Any]:
    h1a.validate_human_visible_copy(report)
    inspector = _Inspector()
    try:
        inspector.feed(document)
        inspector.close()
    except Exception as error:
        _fail("H1C_HTML_INVALID", str(error))
    if inspector.duplicates:
        _fail("H1C_HTML_INVALID", f"duplicate ids: {sorted(inspector.duplicates)}")
    if inspector.invalid_visibility:
        _fail(
            "H1C_HTML_ACCESSIBILITY_INVALID",
            f"invalid aria-hidden value: {inspector.invalid_visibility[0]}",
        )
    if inspector.hidden_text:
        _fail(
            "H1C_HTML_ACCESSIBILITY_INVALID",
            "hidden content cannot carry reader-facing text",
        )
    forbidden = {
        "script", "form", "input", "button", "select", "textarea",
        "iframe", "object", "embed", "link", "base", "template", "noscript",
    }
    if forbidden.intersection(inspector.tags):
        _fail("H1C_HTML_SECURITY_INVALID", "forbidden active element")
    for tag, attrs in inspector.attrs:
        normalized = {
            key.lower(): value for key, value in attrs.items()
        }
        if any(key.startswith("on") for key in normalized):
            _fail("H1C_HTML_SECURITY_INVALID", "inline event handler")
        if "download" in normalized:
            _fail("H1C_HTML_SECURITY_INVALID", "download attribute")
        url_attributes = _URL_BEARING_ATTRIBUTES.intersection(normalized)
        if url_attributes:
            _fail(
                "H1C_HTML_SECURITY_INVALID",
                f"forbidden URL attribute: {sorted(url_attributes)}",
            )
        if (
            tag == "meta"
            and normalized.get("http-equiv", "").strip().lower()
            == "refresh"
        ):
            _fail("H1C_HTML_SECURITY_INVALID", "meta refresh")
        if "style" in normalized:
            _fail("H1C_HTML_SECURITY_INVALID", "style attribute")
    style_text = "".join(inspector.style_text)
    if (
        inspector.tags.count("style") != 1
        or style_text != CSS
        or _CSS_URL_PATTERN.search(style_text)
    ):
        _fail("H1C_HTML_SECURITY_INVALID", "CSS URL/import")
    if "".join(inspector.title_text) != report["title"]:
        _fail("H1C_HTML_TITLE_INVALID", "document title drift")
    if "".join(inspector.h1_text) != report["title"] or inspector.tags.count("h1") != 1:
        _fail("H1C_HTML_TITLE_INVALID", "unique h1 drift")
    if (
        f'content="{_attr(CSP)}"' not in document
        or f'data-render-contract="{DOM_CONTRACT}"' not in document
        or 'lang="zh-CN"' not in document
        or 'class="skip-link"' not in document
        or document.count('class="semantic-visual"') != 5
        or document.count('class="visual-text-equivalent"') != 5
    ):
        _fail("H1C_HTML_ACCESSIBILITY_INVALID", "required shell or visuals missing")
    hrefs = [
        (tag, attrs)
        for tag, attrs in inspector.attrs
        if "href" in attrs
    ]
    content_steps = report["review_path"][:4]
    if (
        len(hrefs) != len(content_steps) + 1
        or hrefs[0][0] != "a"
        or "skip-link" not in hrefs[0][1].get("class", "").split()
        or hrefs[0][1]["href"] != "#main-content"
        or "main-content" not in inspector.ids
    ):
        _fail("H1C_HTML_SECURITY_INVALID", "unauthorized href")
    path_links = hrefs[1:]
    expected_path_values = [
        {
            "href": f"#section-{step['kind']}",
            "data-path-id": step["id"],
            "data-path-kind": step["kind"],
            "data-visible-element-ids": _encoded_ids(
                step["visible_element_ids"]
            ),
        }
        for step in content_steps
    ]
    actual_path_values = []
    for tag, attrs in path_links:
        if tag != "a":
            _fail("H1C_HTML_SECURITY_INVALID", "href outside anchor")
        actual_path_values.append(
            {
                key: attrs.get(key)
                for key in expected_path_values[0]
            }
        )
        target = attrs["href"].removeprefix("#")
        if not attrs["href"].startswith("#") or target not in inspector.ids:
            _fail("H1C_HTML_SECURITY_INVALID", "dangling href")
    if actual_path_values != expected_path_values:
        _fail("H1C_HTML_REVIEW_PATH_INVALID", "review path drift")
    forbidden_public_audit_text = (
        "Full P1 evidence",
        "Decision controls",
        "图形逐值信息",
        "来源覆盖",
        "controls=",
        "sha256=",
        "run=",
    )
    if any(value in document for value in forbidden_public_audit_text):
        _fail(
            "H1C_HTML_HUMAN_PRESENTATION_INVALID",
            "machine audit text leaked into the reader-facing report",
        )
    h1a.validate_human_visible_strings(inspector.visible_text)
    for visible_block in inspector.visible_text:
        match = _VISIBLE_TIMELINE_MODEL_PATTERN.search(visible_block)
        if match:
            _fail(
                "H1C_HTML_HUMAN_PRESENTATION_INVALID",
                f"timeline model vocabulary leaked into visible copy: "
                f"{match.group(0)}",
            )
    roles = [
        attrs["data-semantic-role"]
        for tag, attrs in inspector.attrs
        if tag == "svg" and "data-semantic-role" in attrs
    ]
    page_visuals = [
        visual
        for section in ("world", "storylines", "characters")
        for visual in report["visual_models"]
        if h1a.VISUAL_ROLE_SPECS[visual["semantic_role"]][0] == section
    ]
    expected_roles = [
        visual["semantic_role"] for visual in page_visuals
    ]
    if roles != expected_roles:
        _fail("H1C_HTML_VISUAL_INVALID", "visual order/role drift")
    timeline = next(
        visual
        for visual in page_visuals
        if visual["semantic_role"] == "major_event_timeline"
    )
    expected_timeline_nodes = [
        (
            node["id"],
            node["kind"],
            f"marker-{_timeline_marker_class(node)}",
        )
        for node in timeline["nodes"]
    ]
    timeline_node_ids = {node["id"] for node in timeline["nodes"]}
    actual_timeline_nodes = [
        (
            attrs["data-node-id"],
            attrs.get("data-kind"),
            next(
                (
                    css_class
                    for css_class in attrs.get("class", "").split()
                    if css_class.startswith("marker-")
                ),
                None,
            ),
        )
        for tag, attrs in inspector.attrs
        if tag == "g"
        and attrs.get("data-node-id") in timeline_node_ids
    ]
    expected_marker_classes = list(
        dict.fromkeys(item[2] for item in expected_timeline_nodes)
    )
    actual_marker_classes = [
        css_class
        for tag, attrs in inspector.attrs
        if tag == "li"
        for css_class in attrs.get("class", "").split()
        if css_class.startswith("marker-")
    ]
    actual_timeline_subtitles = [
        attrs
        for tag, attrs in inspector.attrs
        if tag == "text" and "small" in attrs.get("class", "").split()
    ]
    if (
        actual_timeline_nodes != expected_timeline_nodes
        or actual_marker_classes != expected_marker_classes
        or len(actual_timeline_subtitles) != len(expected_timeline_nodes)
    ):
        _fail(
            "H1C_HTML_VISUAL_INVALID",
            "timeline narrative kinds or marker legend drift",
        )
    expected_module_bindings = [
        (visual["id"], visual["text_equivalent_module_id"])
        for visual in page_visuals
    ]
    for tag, css_class in (
        ("figure", "visual-card"),
        ("svg", "semantic-visual"),
        ("figcaption", "visual-text-equivalent"),
    ):
        actual_module_bindings = [
            (
                attrs.get("data-visual-id"),
                attrs.get("data-text-equivalent-module-id"),
            )
            for item_tag, attrs in inspector.attrs
            if item_tag == tag
            and css_class in attrs.get("class", "").split()
        ]
        if actual_module_bindings != expected_module_bindings:
            _fail(
                "H1C_HTML_VISUAL_INVALID",
                f"{css_class} module binding drift",
            )
    for visual in page_visuals:
        if document.count(_visual_prose_caption(visual)) != 1:
            _fail(
                "H1C_HTML_VISUAL_INVALID",
                f"{visual['id']} natural prose fallback drift",
            )
    svg_titles = {
        visual_id: "".join(parts)
        for visual_id, parts in inspector.svg_title_text.items()
    }
    if svg_titles != {
        visual["id"]: visual["title"] for visual in report["visual_models"]
    }:
        _fail("H1C_HTML_VISUAL_INVALID", "visual title drift")
    for section in SECTION_KINDS:
        if f"section-{section}" not in inspector.ids:
            _fail("H1C_HTML_CONTENT_INVALID", f"missing {section}")
    return {
        "verdict": "ready",
        "checks": [
            "exact-title-four-content-dimensions-and-trailing-operation",
            "complete-default-visible-content",
            "five-accessible-semantic-visuals",
            "timeline-narrative-marker-projection",
            "offline-no-active-content",
            "responsive-print-and-focus-contract",
        ],
    }


def _p1_reference(root: Path) -> dict[str, str]:
    value = _read(root / "stage-completion.json", "H1C_P1_INVALID")
    if value.get("stage") != "P1" or value.get("status") != "ready":
        _fail("H1C_P1_INVALID", "P1 is not ready")
    return {
        "stage": "P1",
        "path": "P1/stage-completion.json",
        "sha256": rt.sha256_file(root / "stage-completion.json"),
    }


def _manifest_reference(root: Path, logical: str) -> dict[str, str]:
    return {
        "path": f"{logical}/package-manifest.json",
        "sha256": rt.sha256_file(root / "package-manifest.json"),
    }


def _validate_inputs(
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_package: str | Path,
    fragment_workspace_state: Any,
    assembly_package: str | Path,
    assembly_workspace_state: Any,
    workspace_state: Any,
    plan_logical_package_path: str,
    fragment_logical_package_path: str,
    assembly_logical_package_path: str,
    plan_active_return_request: Any | None,
    runtime: Any,
) -> dict[str, Any]:
    roots = {
        "p1": Path(p1_package).resolve(),
        "plan": Path(plan_package).resolve(),
        "fragment": Path(fragment_package).resolve(),
        "assembly": Path(assembly_package).resolve(),
    }
    before = {key: _tree_inventory(root) for key, root in roots.items()}
    try:
        result = h1a.validate_assembly_package(
            roots["assembly"],
            p1_package=roots["p1"],
            plan_package=roots["plan"],
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=roots["fragment"],
            fragment_workspace_state=fragment_workspace_state,
            workspace_state=assembly_workspace_state,
            plan_logical_package_path=plan_logical_package_path,
            fragment_logical_package_path=fragment_logical_package_path,
            plan_active_return_request=plan_active_return_request,
            runtime=runtime,
        )
    except Exception as error:
        _fail("H1C_UPSTREAM_INVALID", str(error))
    if not isinstance(result, Mapping) or result.get("verdict") != "ready":
        _fail("H1C_UPSTREAM_INVALID", "H1-A assembly is not ready")
    p1_ref = _p1_reference(roots["p1"])
    plan_ref = _manifest_reference(roots["plan"], plan_logical_package_path)
    fragment_ref = _manifest_reference(
        roots["fragment"], fragment_logical_package_path
    )
    assembly_ref = _manifest_reference(
        roots["assembly"], assembly_logical_package_path
    )
    try:
        runtime.validate(workspace_state.data, "h1-workspace-state.schema.json")
    except Exception as error:
        _fail("H1C_WORKSPACE_INVALID", str(error))
    state = workspace_state.data
    if (
        state.get("state") != "assembled"
        or state.get("p1_completion") != p1_ref
        or state.get("previous_state_sha256")
        != assembly_workspace_state.reference.get("sha256")
        or state.get("artifacts")
        != {
            "plan_manifest": plan_ref,
            "fragment_manifest": fragment_ref,
            "assembly_manifest": assembly_ref,
        }
        or rt.canonical_sha256(state)
        != workspace_state.reference.get("sha256")
    ):
        _fail("H1C_WORKSPACE_INVALID", "current workspace is not exact assembled state")
    plan = _read(roots["plan"] / "review-plan.json", "H1C_PLAN_INVALID")
    report = _read(
        roots["assembly"] / "human-review-report.json",
        "H1C_REPORT_INVALID",
    )
    try:
        runtime.validate(report, "human-review-report.schema.json")
    except Exception as error:
        _fail("H1C_REPORT_INVALID", str(error))
    if (
        state.get("run_id") != report.get("run_id")
        or state.get("session_id") != report.get("h1_session_id")
        or plan.get("run_id") != report.get("run_id")
        or plan.get("h1_session_id") != report.get("h1_session_id")
        or report["review_budget"]["estimated_minutes"]
        > report["review_budget"]["target_minutes"]
        or before != {key: _tree_inventory(root) for key, root in roots.items()}
    ):
        _fail("H1C_INPUT_LINEAGE_INVALID", "run/session/budget/TOCTOU mismatch")
    return {
        "roots": roots,
        "inventory": before,
        "report": report,
        "p1_completion": p1_ref,
        "plan_manifest": plan_ref,
        "fragment_manifest": fragment_ref,
        "assembly_manifest": assembly_ref,
    }


def _validation(run_id: str, session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "run_id": run_id,
        "stage": "H1",
        "operation": "H1-C-render",
        "session_id": session_id,
        "verdict": "ready",
        "checks": [
            "formal-H1-A-assembly-chain-validation",
            "exact-current-assembled-workspace",
            "deterministic-byte-identical-render",
            "complete-visible-report-projection",
            "offline-accessibility-security-and-print",
            "manifest-implementation-and-TOCTOU-binding",
        ],
        "errors": [],
    }


def _check_boundary(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _ROOT_FILES or any(
            relative.startswith(prefix) for prefix in _ROOT_PREFIXES
        ):
            continue
        _fail("H1C_PACKAGE_BOUNDARY_INVALID", relative)
    if (root / "stage-completion.json").exists():
        _fail("H1C_COMPLETION_FORBIDDEN", "H1-C cannot emit completion")


def validate_html_package(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_package: str | Path,
    fragment_workspace_state: Any,
    assembly_package: str | Path,
    assembly_workspace_state: Any,
    workspace_state: Any,
    plan_logical_package_path: str = "H1/plan",
    fragment_logical_package_path: str = "H1/fragments",
    assembly_logical_package_path: str = "H1/assembly",
    plan_active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> dict[str, Any]:
    root = Path(package_root).resolve()
    contract_runtime = runtime or rt.ContractRuntime()
    _check_boundary(root)
    upstream = _validate_inputs(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        workspace_state=workspace_state,
        plan_logical_package_path=plan_logical_package_path,
        fragment_logical_package_path=fragment_logical_package_path,
        assembly_logical_package_path=assembly_logical_package_path,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    try:
        document = (root / "human-review-report.html").read_text(
            encoding="utf-8"
        )
    except (OSError, UnicodeError) as error:
        _fail("H1C_HTML_INVALID", str(error))
    if document != render_html(upstream["report"]):
        _fail("H1C_DETERMINISM_INVALID", "HTML is not current pure render")
    validate_html_document(document, upstream["report"])
    execution = _read(root / "render-record.json", "H1C_RECORD_INVALID")
    catalog = {
        item.get("identity"): item.get("artifact")
        for item in execution.get("implementation_catalog", [])
        if isinstance(item, Mapping)
    }
    if set(catalog) != set(_implementation_paths()):
        _fail("H1C_IMPLEMENTATION_STALE", "implementation catalog")
    for identity, source in _implementation_paths().items():
        copied = rt.verify_artifact_reference(catalog[identity], root=root)
        if copied.read_bytes() != source.read_bytes():
            _fail("H1C_IMPLEMENTATION_STALE", identity)
    implementation = [catalog[key] for key in sorted(catalog)]
    report_ref = {
        "path": f"{assembly_logical_package_path}/human-review-report.json",
        "sha256": rt.sha256_file(
            upstream["roots"]["assembly"] / "human-review-report.json"
        ),
    }
    html_ref = rt.artifact_reference(
        root / "human-review-report.html", root=root
    )
    expected_record = {
        "schema_version": "2.0",
        "run_id": upstream["report"]["run_id"],
        "stage": "H1",
        "operation": "H1-C-render",
        "h1_session_id": upstream["report"]["h1_session_id"],
        "render_contract": RENDER_CONTRACT,
        "workspace_state": workspace_state.reference,
        "p1_completion": upstream["p1_completion"],
        "plan_manifest": upstream["plan_manifest"],
        "fragment_manifest": upstream["fragment_manifest"],
        "assembly_manifest": upstream["assembly_manifest"],
        "input_report": report_ref,
        "outputs": {"human-review-report.html": html_ref},
        "implementation": implementation,
        "implementation_catalog": [
            {"identity": key, "artifact": catalog[key]}
            for key in sorted(catalog)
        ],
    }
    if execution != expected_record:
        _fail("H1C_RECORD_INVALID", "render record drift")
    expected_validation = _validation(
        upstream["report"]["run_id"],
        upstream["report"]["h1_session_id"],
    )
    validation = _read(root / "validation.json", "H1C_VALIDATION_INVALID")
    if validation != expected_validation:
        _fail("H1C_VALIDATION_INVALID", "validation drift")
    manifest = _read(root / "package-manifest.json", "H1C_MANIFEST_INVALID")
    try:
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=root)
    except Exception as error:
        _fail("H1C_MANIFEST_INVALID", str(error))
    actual_files = [
        item
        for item in _tree_inventory(root)
        if item["path"] != "package-manifest.json"
    ]
    by_path = {item["path"]: item for item in actual_files}
    if (
        manifest.get("run_id") != upstream["report"]["run_id"]
        or manifest.get("stage") != "H1"
        or manifest.get("package_profile") != "h1-html"
        or manifest.get("verdict") != "ready"
        or manifest.get("session_id") != upstream["report"]["h1_session_id"]
        or manifest.get("parent_state_sha256")
        != workspace_state.reference["sha256"]
        or manifest.get("artifact_roles")
        != {
            "html": by_path["human-review-report.html"],
            "render_record": by_path["render-record.json"],
        }
        or manifest.get("validation") != by_path["validation.json"]
        or manifest.get("implementation") != implementation
        or manifest.get("files") != actual_files
    ):
        _fail("H1C_MANIFEST_INVALID", "manifest is not exact")
    return copy.deepcopy(validation)


def run(
    package_root: str | Path,
    *,
    p1_package: str | Path,
    plan_package: str | Path,
    plan_input_gate: Any,
    plan_workspace_state: Any,
    fragment_package: str | Path,
    fragment_workspace_state: Any,
    assembly_package: str | Path,
    assembly_workspace_state: Any,
    workspace_state: Any,
    coordinator: Any,
    logical_package_path: str = "H1/html",
    plan_logical_package_path: str = "H1/plan",
    fragment_logical_package_path: str = "H1/fragments",
    assembly_logical_package_path: str = "H1/assembly",
    plan_active_return_request: Any | None = None,
    active_return_request: Any | None = None,
    runtime: Any | None = None,
) -> HtmlReceipt:
    destination = Path(package_root).resolve()
    if destination.exists():
        _fail("H1C_OUTPUT_EXISTS", str(destination))
    contract_runtime = runtime or rt.ContractRuntime()
    upstream = _validate_inputs(
        p1_package=p1_package,
        plan_package=plan_package,
        plan_input_gate=plan_input_gate,
        plan_workspace_state=plan_workspace_state,
        fragment_package=fragment_package,
        fragment_workspace_state=fragment_workspace_state,
        assembly_package=assembly_package,
        assembly_workspace_state=assembly_workspace_state,
        workspace_state=workspace_state,
        plan_logical_package_path=plan_logical_package_path,
        fragment_logical_package_path=fragment_logical_package_path,
        assembly_logical_package_path=assembly_logical_package_path,
        plan_active_return_request=plan_active_return_request,
        runtime=contract_runtime,
    )
    document = render_html(upstream["report"])
    validate_html_document(document, upstream["report"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staging = temp_parent / "package"
    staging.mkdir()
    try:
        (staging / "human-review-report.html").write_text(
            document, encoding="utf-8", newline=""
        )
        implementation: list[dict[str, str]] = []
        catalog: list[dict[str, Any]] = []
        for identity, source in sorted(_implementation_paths().items()):
            target = staging / "implementation" / identity
            _copy_exact(source, target)
            reference = rt.artifact_reference(target, root=staging)
            implementation.append(reference)
            catalog.append({"identity": identity, "artifact": reference})
        report_ref = {
            "path": f"{assembly_logical_package_path}/human-review-report.json",
            "sha256": rt.sha256_file(
                upstream["roots"]["assembly"] / "human-review-report.json"
            ),
        }
        record = {
            "schema_version": "2.0",
            "run_id": upstream["report"]["run_id"],
            "stage": "H1",
            "operation": "H1-C-render",
            "h1_session_id": upstream["report"]["h1_session_id"],
            "render_contract": RENDER_CONTRACT,
            "workspace_state": workspace_state.reference,
            "p1_completion": upstream["p1_completion"],
            "plan_manifest": upstream["plan_manifest"],
            "fragment_manifest": upstream["fragment_manifest"],
            "assembly_manifest": upstream["assembly_manifest"],
            "input_report": report_ref,
            "outputs": {
                "human-review-report.html": rt.artifact_reference(
                    staging / "human-review-report.html", root=staging
                )
            },
            "implementation": implementation,
            "implementation_catalog": catalog,
        }
        _write_new(staging / "render-record.json", record)
        _write_new(
            staging / "validation.json",
            _validation(
                upstream["report"]["run_id"],
                upstream["report"]["h1_session_id"],
            ),
        )
        files = _tree_inventory(staging)
        by_path = {item["path"]: item for item in files}
        manifest = {
            "schema_version": "2.0",
            "run_id": upstream["report"]["run_id"],
            "stage": "H1",
            "package_profile": "h1-html",
            "verdict": "ready",
            "files": files,
            "artifact_roles": {
                "html": by_path["human-review-report.html"],
                "render_record": by_path["render-record.json"],
            },
            "validation": by_path["validation.json"],
            "implementation": implementation,
            "parent_state_sha256": workspace_state.reference["sha256"],
            "session_id": upstream["report"]["h1_session_id"],
        }
        contract_runtime.validate(manifest, "package-manifest.schema.json")
        rt.verify_manifest_integrity(manifest, root=staging)
        _write_new(staging / "package-manifest.json", manifest)
        validate_html_package(
            staging,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_package,
            fragment_workspace_state=fragment_workspace_state,
            assembly_package=assembly_package,
            assembly_workspace_state=assembly_workspace_state,
            workspace_state=workspace_state,
            plan_logical_package_path=plan_logical_package_path,
            fragment_logical_package_path=fragment_logical_package_path,
            assembly_logical_package_path=assembly_logical_package_path,
            plan_active_return_request=plan_active_return_request,
            runtime=contract_runtime,
        )
        if upstream["inventory"] != {
            key: _tree_inventory(root)
            for key, root in upstream["roots"].items()
        }:
            _fail("H1C_INPUT_MUTATED", "input package changed before publish")
        staging.replace(destination)
        validate_html_package(
            destination,
            p1_package=p1_package,
            plan_package=plan_package,
            plan_input_gate=plan_input_gate,
            plan_workspace_state=plan_workspace_state,
            fragment_package=fragment_package,
            fragment_workspace_state=fragment_workspace_state,
            assembly_package=assembly_package,
            assembly_workspace_state=assembly_workspace_state,
            workspace_state=workspace_state,
            plan_logical_package_path=plan_logical_package_path,
            fragment_logical_package_path=fragment_logical_package_path,
            assembly_logical_package_path=assembly_logical_package_path,
            plan_active_return_request=plan_active_return_request,
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
            expected_next_state="rendered",
            active_return_request=active_return_request,
        )
    except Exception:
        shutil.rmtree(temp_parent, ignore_errors=True)
        raise
    shutil.rmtree(temp_parent, ignore_errors=True)
    return HtmlReceipt(
        package_root=destination,
        manifest=copy.deepcopy(manifest),
        transition=transition,
    )


__all__ = [
    "RENDER_CONTRACT",
    "DOM_CONTRACT",
    "H1CError",
    "HtmlReceipt",
    "render_visual",
    "render_html",
    "validate_html_document",
    "validate_html_package",
    "run",
]
