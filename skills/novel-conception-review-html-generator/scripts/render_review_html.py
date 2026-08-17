from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

from common import (
    CSP,
    ContractError,
    SKILL_NAME,
    STYLE_CONTRACT,
    all_skill_files,
    canonical_json,
    embedded_json,
    escape,
    sha256_file,
    validate_upstream,
    write_json,
)


CSS = r"""
:root {
  --paper: #F7F3EA;
  --ink: #18202A;
  --muted: #5E6873;
  --blue: #2457A7;
  --amber: #A65A00;
  --card: #FFFDF8;
  --border: #D7D0C3;
  --blue-soft: #E8EEF8;
  --amber-soft: #F8EBD9;
  --shadow: 0 10px 28px rgba(24, 32, 42, .08);
  --radius: 14px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 5rem; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC",
    "Microsoft YaHei", sans-serif;
  font-size: 16px;
  line-height: 1.65;
}
a { color: var(--blue); text-underline-offset: .18em; }
a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 3px solid var(--amber);
  outline-offset: 3px;
}
.skip-link {
  position: absolute;
  left: 1rem;
  top: -5rem;
  z-index: 100;
  background: var(--ink);
  color: var(--card);
  padding: .7rem 1rem;
  border-radius: 0 0 8px 8px;
}
.skip-link:focus { top: 0; }
.masthead {
  border-bottom: 1px solid var(--border);
  background: var(--card);
}
.masthead-inner, main, .page-footer {
  width: min(1180px, calc(100% - 2rem));
  margin-inline: auto;
}
.masthead-inner { padding: 2rem 0 1.5rem; }
.eyebrow {
  margin: 0 0 .3rem;
  color: var(--blue);
  font-size: .82rem;
  font-weight: 750;
  letter-spacing: .08em;
}
h1, h2, h3, h4 { line-height: 1.25; text-wrap: balance; }
h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.6rem); max-width: 18ch; }
h2 { margin: 0; font-size: clamp(1.65rem, 3vw, 2.35rem); }
h3 { margin: 0; font-size: 1.15rem; }
h4 { margin: 0; font-size: 1rem; }
p { max-width: 72ch; }
.lead {
  max-width: 66ch;
  margin: .9rem 0 0;
  color: var(--muted);
  font-size: 1.08rem;
}
.review-meta {
  display: flex;
  flex-wrap: wrap;
  gap: .55rem;
  margin: 1.2rem 0 0;
  padding: 0;
  list-style: none;
}
.review-meta li, .tag {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--paper);
  padding: .26rem .65rem;
  font-size: .84rem;
}
.section-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid var(--border);
  background: rgba(247, 243, 234, .96);
}
.section-nav ol {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
  padding: .65rem 0;
  display: flex;
  gap: .45rem;
  overflow-x: auto;
  list-style: none;
}
.section-nav a {
  display: block;
  min-width: max-content;
  padding: .36rem .62rem;
  border-radius: 7px;
  text-decoration: none;
  font-size: .88rem;
  font-weight: 650;
}
.section-nav a:hover { background: var(--blue-soft); }
main { padding: 1.4rem 0 4rem; }
.panel {
  margin-top: 1rem;
  padding: clamp(1.1rem, 3vw, 2rem);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
}
.section-heading {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  align-items: start;
  margin-bottom: 1.3rem;
}
.section-number {
  display: grid;
  place-items: center;
  width: 2.4rem;
  height: 2.4rem;
  border: 2px solid var(--blue);
  border-radius: 50%;
  color: var(--blue);
  font-weight: 800;
}
.section-intro { margin: .35rem 0 0; color: var(--muted); }
.identity {
  padding: 1rem 1.2rem;
  border-left: 5px solid var(--blue);
  background: var(--blue-soft);
  font-size: 1.18rem;
  font-weight: 650;
}
.two-col, .card-grid, .profile-grid, .definition-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}
.card {
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--card);
}
.card > h3, .card > h4 { margin-bottom: .65rem; }
.control-summary {
  margin: .2rem 0 .8rem;
  padding-left: .75rem;
  border-left: 3px solid var(--blue);
  font-weight: 650;
}
details > summary {
  cursor: pointer;
  color: var(--blue);
  font-weight: 700;
}
details[open] > summary { margin-bottom: .75rem; }
.table-scroll {
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
}
.control-table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
  background: var(--card);
}
.control-table th, .control-table td {
  padding: .65rem .75rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
}
.control-table thead th { color: var(--muted); font-size: .86rem; }
.control-table tbody th { min-width: 9rem; color: var(--blue); }
.event-index {
  columns: 2;
  column-gap: 2rem;
  margin: 0 0 1rem;
  padding-left: 1.5rem;
}
.event-index li {
  break-inside: avoid;
  padding: .25rem 0;
}
.event-index .tag { margin-left: .45rem; }
.event-control-details { margin-top: .75rem; }
.fact-list {
  display: grid;
  grid-template-columns: minmax(7.5rem, .7fr) 2fr;
  gap: .38rem .9rem;
  margin: 0;
}
.fact-list dt { color: var(--muted); font-weight: 700; }
.fact-list dd { margin: 0; overflow-wrap: anywhere; }
.compact-list { margin: .4rem 0 0; padding-left: 1.2rem; }
.compact-list li + li { margin-top: .45rem; }
.review-question {
  margin: 1.2rem 0 0;
  padding: .85rem 1rem;
  border-left: 5px solid var(--amber);
  background: var(--amber-soft);
  font-weight: 700;
}
.visual-title {
  margin: 1.6rem 0 .7rem;
  color: var(--muted);
  font-size: .82rem;
  font-weight: 800;
  letter-spacing: .08em;
}
.diagram-shell {
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #fff;
  scrollbar-color: var(--border) transparent;
}
.diagram-shell + .diagram-shell { margin-top: 1rem; }
.info-svg {
  display: block;
  width: 100%;
  height: auto;
  min-width: var(--diagram-min-width, 760px);
  color: var(--ink);
}
.info-svg text {
  fill: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC",
    "Microsoft YaHei", sans-serif;
}
.svg-kicker { fill: var(--muted) !important; font-size: 12px; font-weight: 800; letter-spacing: .08em; }
.svg-title { font-size: 15px; font-weight: 800; }
.svg-copy { fill: var(--muted) !important; font-size: 12px; }
.svg-small { fill: var(--muted) !important; font-size: 11px; }
.svg-index { fill: #fff !important; font-size: 12px; font-weight: 850; }
.svg-guide { stroke: var(--border); stroke-width: 1.5; stroke-dasharray: 4 5; }
.svg-arrow {
  fill: none;
  stroke: var(--blue);
  stroke-width: 2.5;
  marker-end: url(#world-arrow);
}
.svg-edge-label {
  fill: var(--amber) !important;
  font-size: 11px;
  font-weight: 800;
}
.world-system-box { fill: var(--blue-soft); stroke: var(--blue); stroke-width: 2; }
.world-system-number { fill: var(--blue); }
.environment-zone { fill: var(--amber-soft); stroke: var(--amber); stroke-width: 1.8; }
.environment-motif { fill: none; stroke: var(--amber); stroke-width: 2; }
.story-cause-arrow {
  fill: none;
  stroke: var(--border);
  stroke-width: 2;
  marker-end: url(#story-arrow);
}
.control-spine-arrow {
  fill: none;
  stroke: var(--blue);
  stroke-width: 2.4;
  marker-end: url(#control-spine-arrowhead);
}
.story-stage-box { fill: var(--card); stroke: var(--blue); stroke-width: 1.8; }
.story-cost-band { fill: var(--amber-soft); }
.story-stage-number { fill: var(--blue); }
.story-lane-path { fill: none; stroke-width: 4; }
.story-lane-node { stroke-width: 3; }
.lane-main-svg { stroke: var(--blue); fill: var(--blue-soft); }
.lane-subplot-svg { stroke: var(--amber); fill: var(--amber-soft); }
.lane-background-svg { stroke: var(--muted); fill: #f1f1ee; stroke-dasharray: 7 5; }
.character-edge { fill: none; stroke-width: 2; opacity: .72; }
.character-edge.layer-1 { stroke: var(--blue); }
.character-edge.layer-2 { stroke: var(--amber); }
.character-edge.layer-3 { stroke: var(--muted); stroke-dasharray: 6 4; }
.character-node rect { stroke-width: 2; }
.character-node.core rect { fill: var(--ink); stroke: var(--ink); }
.character-node.inner rect { fill: var(--blue-soft); stroke: var(--blue); }
.character-node.outer rect { fill: var(--card); stroke: var(--muted); }
.character-node.core text { fill: #fff !important; }
.relation-badge.layer-1 circle { fill: var(--blue); }
.relation-badge.layer-2 circle { fill: var(--amber); }
.relation-badge.layer-3 circle { fill: var(--muted); }
.relationship-legend {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .65rem;
  margin-top: .85rem;
}
.relation-key {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: .15rem .6rem;
  align-items: start;
  padding: .7rem;
  border: 1px solid var(--border);
  border-left: 4px solid var(--muted);
  border-radius: 9px;
}
.relation-key.layer-1 { border-left-color: var(--blue); }
.relation-key.layer-2 { border-left-color: var(--amber); }
.relation-key .relation-index {
  grid-row: 1 / span 3;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--ink);
  color: #fff;
  font-size: .75rem;
  font-weight: 850;
}
.relation-key small { color: var(--muted); }
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
.world-map {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: .8rem;
}
.world-node {
  position: relative;
  min-height: 7rem;
  padding: 1rem;
  border: 2px solid var(--blue);
  border-radius: 12px;
  background: var(--blue-soft);
}
.world-node.environment {
  border-color: var(--amber);
  background: var(--amber-soft);
}
.node-kind { display: block; color: var(--muted); font-size: .78rem; font-weight: 750; }
.timeline {
  display: grid;
  gap: .9rem;
  counter-reset: stage;
}
.timeline-stage {
  counter-increment: stage;
  display: grid;
  grid-template-columns: 2.5rem 1fr;
  gap: .85rem;
  position: relative;
}
.timeline-stage::before {
  content: counter(stage);
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background: var(--blue);
  color: white;
  font-weight: 800;
}
.timeline-stage:not(:last-child)::after {
  content: "";
  position: absolute;
  left: 1.08rem;
  top: 2.4rem;
  bottom: -.9rem;
  width: 2px;
  background: var(--border);
}
.timeline-body {
  padding: .9rem 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
}
.line-strip {
  display: flex;
  flex-wrap: wrap;
  gap: .5rem;
  margin: .6rem 0 1rem;
}
.line-main { border-color: var(--blue); background: var(--blue-soft); }
.line-subplot { border-color: var(--amber); background: var(--amber-soft); }
.line-background { border-style: dashed; }
.story-lanes {
  display: grid;
  gap: .7rem;
  margin: .8rem 0 1.2rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
}
.story-lane {
  display: grid;
  grid-template-columns: minmax(7.5rem, .8fr) 4fr;
  gap: .7rem;
  align-items: stretch;
}
.lane-name {
  display: grid;
  place-items: center start;
  padding: .55rem .7rem;
  border-left: 5px solid var(--blue);
  background: var(--blue-soft);
  font-weight: 800;
}
.story-lane.subplot .lane-name { border-color: var(--amber); background: var(--amber-soft); }
.story-lane.background .lane-name { border-color: var(--muted); background: #f1f1ee; }
.lane-track {
  display: grid;
  grid-template-columns: repeat(var(--stage-count), minmax(0, 1fr));
  gap: .35rem;
}
.lane-cell {
  min-width: 0;
  padding: .5rem;
  border: 1px dashed var(--border);
  border-radius: 8px;
  color: var(--muted);
  font-size: .78rem;
  overflow-wrap: anywhere;
}
.lane-cell.active {
  border-style: solid;
  border-color: var(--blue);
  background: var(--blue-soft);
  color: var(--ink);
  font-weight: 700;
}
.relationship-map { display: grid; gap: .75rem; }
.relationship-network {
  display: grid;
  gap: .65rem;
  margin-bottom: 1rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
}
.relationship-edge {
  display: grid;
  grid-template-columns: minmax(6rem, 1fr) auto minmax(6rem, 1fr) minmax(8rem, 1.3fr);
  gap: .55rem;
  align-items: center;
}
.person-node {
  padding: .55rem .7rem;
  border: 2px solid var(--blue);
  border-radius: 999px;
  background: var(--blue-soft);
  text-align: center;
  font-weight: 800;
}
.relation-arrow { color: var(--amber); font-size: 1.3rem; font-weight: 900; }
.relation-duty {
  padding: .5rem .65rem;
  border-left: 4px solid var(--amber);
  background: var(--amber-soft);
}
.relationship-layer {
  display: grid;
  grid-template-columns: 5.5rem 1fr;
  gap: .8rem;
  align-items: stretch;
}
.layer-label {
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: var(--ink);
  color: var(--card);
  text-align: center;
  font-weight: 800;
}
.fragment {
  margin-top: 1.2rem;
  padding: clamp(1rem, 3vw, 1.7rem);
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
}
.fragment-label { color: var(--blue); font-size: .82rem; font-weight: 800; }
.fragment-purpose { color: var(--muted); }
.prose {
  max-width: 66ch;
  margin: 1.1rem auto;
  font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", serif;
  font-size: 1.05rem;
  line-height: 1.9;
  white-space: pre-line;
}
.decision-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}
fieldset {
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
}
legend { padding: 0 .35rem; font-weight: 750; }
.choice { display: inline-flex; gap: .4rem; align-items: center; margin-right: 1rem; }
textarea {
  width: 100%;
  min-height: 7rem;
  margin-top: .6rem;
  padding: .7rem;
  border: 1px solid var(--muted);
  border-radius: 8px;
  background: white;
  color: var(--ink);
  font: inherit;
}
button {
  margin-top: 1rem;
  padding: .7rem 1rem;
  border: 0;
  border-radius: 8px;
  background: var(--blue);
  color: white;
  font: inherit;
  font-weight: 750;
  cursor: pointer;
}
.decision-notice {
  margin-top: 1rem;
  padding: .8rem 1rem;
  border: 1px solid var(--amber);
  background: var(--amber-soft);
}
.status { min-height: 1.6rem; color: var(--muted); }
details { margin-top: 1rem; border-top: 1px solid var(--border); padding-top: .8rem; }
summary { cursor: pointer; color: var(--blue); font-weight: 700; }
.trace { overflow-wrap: anywhere; font-family: ui-monospace, Consolas, monospace; font-size: .78rem; }
.page-footer { padding: 1.5rem 0 2.5rem; color: var(--muted); font-size: .85rem; }
@media (max-width: 760px) {
  .two-col, .card-grid, .profile-grid, .definition-grid, .decision-grid {
    grid-template-columns: 1fr;
  }
  .event-index { columns: 1; }
  .relationship-layer { grid-template-columns: 1fr; }
  .story-lane { grid-template-columns: 1fr; }
  .lane-track { grid-template-columns: 1fr; }
  .relationship-edge { grid-template-columns: 1fr; }
  .relationship-legend { grid-template-columns: 1fr; }
  .relation-arrow { transform: rotate(90deg); text-align: center; }
  .section-nav { position: static; }
  .fact-list { grid-template-columns: 1fr; gap: .1rem; }
  .fact-list dd { margin-bottom: .5rem; }
  .diagram-shell::after {
    content: "横向滑动查看完整图";
    display: block;
    position: sticky;
    left: 0;
    width: max-content;
    padding: .35rem .65rem;
    color: var(--muted);
    font-size: .75rem;
  }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
@media print {
  :root { --paper: #fff; --card: #fff; --shadow: none; }
  body { font-size: 10.5pt; background: #fff; }
  .section-nav, .skip-link, .page-footer, button, .status { display: none !important; }
  main, .masthead-inner, .page-footer { width: 100%; }
  .panel, .fragment { box-shadow: none; break-inside: auto; }
  .card, .timeline-stage, .relationship-layer, .relation-key, .diagram-shell,
  .review-question, .event-index li, fieldset {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .section-heading, .visual-title, h2, h3 {
    break-after: avoid;
    page-break-after: avoid;
  }
  .diagram-shell { overflow: visible; border-color: #aaa; }
  .info-svg { min-width: 0; }
  .fragment { break-inside: auto; }
  a { color: inherit; text-decoration: none; }
  @page { margin: 14mm; }
}
"""


SCRIPT = r"""
(() => {
  const button = document.getElementById("copy-review-draft");
  const status = document.getElementById("copy-status");
  if (!button || !status) return;
  button.addEventListener("click", async () => {
    const decisions = {};
    document.querySelectorAll("fieldset[data-domain]").forEach((field) => {
      const selected = field.querySelector("input[type=radio]:checked");
      const notes = field.querySelector("textarea");
      decisions[field.dataset.domain] = {
        decision: selected ? selected.value : null,
        notes: notes ? notes.value : ""
      };
    });
    const draft = {
      schema_version: "1.0",
      status: "draft",
      authority: "non_authoritative_until_submitted_to_workflow",
      report_sha256: document.documentElement.dataset.reportSha256,
      decisions
    };
    const text = JSON.stringify(draft, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = "评审草稿已复制。它尚未构成作者批准。";
    } catch (_) {
      const blob = new Blob([text], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "author-review-draft.json";
      anchor.click();
      URL.revokeObjectURL(url);
      status.textContent = "评审草稿已下载。它尚未构成作者批准。";
    }
  });
})();
"""


def text_item(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "name", "title", "label"):
            if isinstance(value.get(key), str):
                return value[key]
    return str(value)


def render_text_list(items: Any, css_class: str = "compact-list") -> str:
    if not isinstance(items, list) or not items:
        return '<p class="section-intro">无。</p>'
    return (
        f'<ul class="{css_class}">'
        + "".join(f"<li>{escape(text_item(item))}</li>" for item in items)
        + "</ul>"
    )


def dl(pairs: list[tuple[str, Any]]) -> str:
    return '<dl class="fact-list">' + "".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>"
        for label, value in pairs
    ) + "</dl>"


def _wrap_svg_text(value: Any, max_chars: int) -> list[str]:
    text = str(value).strip()
    if not text:
        return [""]
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def _svg_text(
    x: float,
    y: float,
    value: Any,
    *,
    max_chars: int,
    line_height: int = 17,
    css_class: str = "svg-copy",
    anchor: str = "middle",
    max_lines: int | None = None,
) -> str:
    lines = _wrap_svg_text(value, max_chars)
    if max_lines is not None:
        lines = lines[:max_lines]
    tspans = "".join(
        f'<tspan x="{x:.1f}" dy="{0 if index == 0 else line_height}">'
        f"{escape(line)}</tspan>"
        for index, line in enumerate(lines)
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'class="{css_class}">{tspans}</text>'
    )


def render_world_system_svg(world: dict[str, Any]) -> str:
    model = world["visual_model"]
    visual_nodes = [item for item in model.get("nodes", []) if isinstance(item, dict)]
    systems = world["systems"]
    width = max(980, len(visual_nodes) * 220 + 50)
    height = 285
    node_width = 178
    node_height = 116
    gap = (width - 50 - node_width * len(visual_nodes)) / max(1, len(visual_nodes) - 1)
    system_by_source = {
        source_id: system
        for system in systems
        for source_id in system.get("source_ids", [])
    }
    positions: dict[str, tuple[float, float]] = {}
    nodes: list[str] = []
    for index, node in enumerate(visual_nodes):
        x = 25 + index * (node_width + gap)
        y = 112
        positions[str(node.get("id"))] = (x, y)
        linked = next(
            (
                system_by_source[source_id]
                for source_id in node.get("source_ids", [])
                if source_id in system_by_source
            ),
            systems[index] if index < len(systems) else node,
        )
        name = linked.get("name", node.get("name", "运行系统"))
        rule = linked.get("rule", "")
        nodes.append(
            f'<g class="world-system-node"><title>{escape(name)}：{escape(rule)}</title>'
            f'<rect class="world-system-box" x="{x:.1f}" y="{y:.1f}" '
            f'width="{node_width}" height="{node_height}" rx="14"/>'
            f'<circle class="world-system-number" cx="{x + 22:.1f}" cy="{y + 22:.1f}" r="14"/>'
            f'<text class="svg-index" x="{x + 22:.1f}" y="{y + 26:.1f}" '
            f'text-anchor="middle">{index + 1}</text>'
            f'{_svg_text(x + node_width / 2, y + 48, name, max_chars=11, line_height=18, css_class="svg-title", max_lines=3)}'
            f'{_svg_text(x + node_width / 2, y + 94, rule, max_chars=13, line_height=15, css_class="svg-small", max_lines=2)}</g>'
        )
    edges: list[str] = []
    for edge in model.get("edges", []):
        if not isinstance(edge, dict):
            continue
        start = positions.get(str(edge.get("from")))
        end = positions.get(str(edge.get("to")))
        if start is None or end is None:
            continue
        x1 = start[0] + node_width
        x2 = end[0]
        y = start[1] + node_height / 2
        edges.append(
            f'<path class="svg-arrow" d="M {x1:.1f} {y:.1f} L {x2 - 8:.1f} {y:.1f}"/>'
            f'{_svg_text((x1 + x2) / 2, y - 13, edge.get("label", ""), max_chars=9, css_class="svg-edge-label", max_lines=2)}'
        )
    return (
        '<div class="diagram-shell" style="--diagram-min-width:760px">'
        f'<svg class="info-svg world-system-svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="world-system-title world-system-desc">'
        '<title id="world-system-title">世界运行系统因果链</title>'
        '<desc id="world-system-desc">从左到右展示系统规则如何逐步触发、核验并形成行动结果。</desc>'
        '<defs><marker id="world-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#2457A7"/></marker></defs>'
        '<text x="25" y="31" class="svg-kicker">SYSTEM CAUSAL CHAIN · 系统因果链</text>'
        '<line class="svg-guide" x1="25" y1="82" x2="{:.1f}" y2="82"/>'.format(width - 25)
        + "".join(edges)
        + "".join(nodes)
        + "</svg></div>"
    )


def render_environment_svg(world: dict[str, Any]) -> str:
    environments = world["environments"]
    columns = 3 if len(environments) > 4 else max(1, min(2, len(environments)))
    rows = math.ceil(len(environments) / columns)
    cell_width = 350
    cell_height = 188
    gap = 24
    margin = 28
    width = columns * cell_width + (columns - 1) * gap + margin * 2
    height = rows * cell_height + (rows - 1) * gap + 82
    cells: list[str] = []
    for index, item in enumerate(environments):
        column = index % columns
        row = index // columns
        x = margin + column * (cell_width + gap)
        y = 58 + row * (cell_height + gap)
        name = item["name"]
        cells.append(
            f'<g class="environment-cell"><title>{escape(name)}：'
            f'{escape(item["story_function"])}；{escape(item["state_change"])}</title>'
            f'<rect class="environment-zone" x="{x}" y="{y}" width="{cell_width}" '
            f'height="{cell_height}" rx="18"/>'
            f'<circle class="environment-motif" cx="{x + 31}" cy="{y + 32}" r="15"/>'
            f'<path class="environment-motif" d="M {x + 22} {y + 32} '
            f'L {x + 29} {y + 39} L {x + 42} {y + 24}"/>'
            f'<text class="svg-kicker" x="{x + 57}" y="{y + 25}">'
            f'ENV {index + 1:02d}</text>'
            f'{_svg_text(x + 57, y + 48, name, max_chars=15, line_height=18, css_class="svg-title", anchor="start", max_lines=2)}'
            f'<text class="svg-small" x="{x + 22}" y="{y + 102}">特征</text>'
            f'{_svg_text(x + 70, y + 102, item["signature"], max_chars=17, line_height=15, css_class="svg-copy", anchor="start", max_lines=2)}'
            f'<text class="svg-small" x="{x + 22}" y="{y + 132}">职责</text>'
            f'{_svg_text(x + 70, y + 132, item["story_function"], max_chars=17, line_height=15, css_class="svg-copy", anchor="start", max_lines=2)}'
            f'<text class="svg-small" x="{x + 22}" y="{y + 162}">变化</text>'
            f'{_svg_text(x + 70, y + 162, item["state_change"], max_chars=17, line_height=15, css_class="svg-copy", anchor="start", max_lines=2)}</g>'
        )
    return (
        '<div class="diagram-shell" style="--diagram-min-width:760px">'
        f'<svg class="info-svg environment-svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="environment-title environment-desc">'
        '<title id="environment-title">主要环境事件承载图</title>'
        '<desc id="environment-desc">每个区域同时显示环境特征、故事职责和事件后的状态变化。</desc>'
        '<text x="28" y="31" class="svg-kicker">EVENT-BEARING ENVIRONMENTS · 事件承载环境</text>'
        + "".join(cells)
        + "</svg></div>"
    )


def render_story_svg(story: dict[str, Any]) -> str:
    stages = story["timeline"]
    lines = story["lines"]
    step = 174
    start_x = 190
    width = max(1120, start_x + len(stages) * step + 40)
    lane_start_y = 340
    lane_gap = 62
    height = lane_start_y + max(1, len(lines)) * lane_gap + 55
    kind_class = {
        "main": "lane-main-svg",
        "subplot": "lane-subplot-svg",
        "background": "lane-background-svg",
    }
    stage_parts: list[str] = []
    for index, stage in enumerate(stages):
        center_x = start_x + index * step
        x = center_x - 72
        stage_parts.append(
            f'<g class="story-stage"><title>{escape(stage["label"])}：'
            f'{escape(stage["pressure"])}；{escape(stage["choice"])}；'
            f'{escape(stage["new_state"])}</title>'
            f'<line class="svg-guide" x1="{center_x}" y1="214" '
            f'x2="{center_x}" y2="{lane_start_y + (len(lines) - 1) * lane_gap + 16}"/>'
            f'<rect class="story-stage-box" x="{x}" y="58" width="144" height="156" rx="14"/>'
            f'<rect class="story-cost-band" x="{x}" y="186" width="144" height="28" '
            f'rx="14"/>'
            f'<circle class="story-stage-number" cx="{x + 20}" cy="78" r="13"/>'
            f'<text class="svg-index" x="{x + 20}" y="82" text-anchor="middle">{index + 1}</text>'
            f'{_svg_text(center_x, 103, stage["label"], max_chars=9, line_height=17, css_class="svg-title", max_lines=2)}'
            f'{_svg_text(center_x, 140, "压｜" + stage["pressure"], max_chars=12, line_height=15, css_class="svg-small", max_lines=2)}'
            f'{_svg_text(center_x, 169, "选｜" + stage["choice"], max_chars=12, line_height=15, css_class="svg-small", max_lines=2)}'
            f'{_svg_text(center_x, 205, "代｜" + stage["cost"], max_chars=13, line_height=14, css_class="svg-small", max_lines=1)}</g>'
        )
        if index < len(stages) - 1:
            stage_parts.append(
                f'<path class="story-cause-arrow" d="M {center_x + 74} 136 '
                f'L {center_x + step - 80} 136"/>'
            )
    lane_parts: list[str] = []
    for line_index, line in enumerate(lines):
        y = lane_start_y + line_index * lane_gap
        css_class = kind_class.get(line["kind"], "lane-background-svg")
        active_points = [
            (start_x + index * step, y)
            for index, stage in enumerate(stages)
            if line["id"] in stage["line_ids"]
        ]
        if len(active_points) >= 2:
            path = " ".join(
                ("M" if index == 0 else "L") + f" {x:.1f} {point_y:.1f}"
                for index, (x, point_y) in enumerate(active_points)
            )
            lane_parts.append(
                f'<path class="story-lane-path {css_class}" d="{path}"/>'
            )
        lane_parts.append(
            f'{_svg_text(20, y + 4, line["name"], max_chars=10, line_height=15, css_class="svg-title", anchor="start", max_lines=2)}'
        )
        for point_index, (x, point_y) in enumerate(active_points):
            lane_parts.append(
                f'<circle class="story-lane-node {css_class}" cx="{x:.1f}" '
                f'cy="{point_y:.1f}" r="8"><title>{escape(line["name"])}进入此阶段</title></circle>'
            )
    return (
        '<div class="diagram-shell story-lanes" style="--diagram-min-width:980px" '
        'aria-label="故事线阶段泳道图">'
        f'<svg class="info-svg story-flow-svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="story-flow-title story-flow-desc">'
        '<title id="story-flow-title">八阶段因果与多线泳道图</title>'
        '<desc id="story-flow-desc">上方按压力、选择、代价展示八个阶段；下方展示主线、支线和背景线进入的阶段。</desc>'
        '<defs><marker id="story-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#D7D0C3"/></marker></defs>'
        '<text x="20" y="31" class="svg-kicker">CAUSAL STAGES + STORY LANES · 因果阶段与故事线</text>'
        + "".join(stage_parts)
        + "".join(lane_parts)
        + "</svg></div>"
    )


def _relationship_layer_number(value: Any) -> int:
    mapping = {"一": 1, "二": 2, "三": 3, "1": 1, "2": 2, "3": 3}
    return mapping.get(str(value), 3)


def render_character_svg(characters: dict[str, Any]) -> tuple[str, str]:
    profiles = characters["profiles"]
    relationships = characters["relationship_layers"]
    names = {item["character_source_id"]: item["name"] for item in profiles}
    all_ids = [item["character_source_id"] for item in profiles]
    core_ids = list(
        dict.fromkeys(
            endpoint
            for item in relationships
            if _relationship_layer_number(item["layer"]) == 1
            for endpoint in (
                item["from_character_source_id"],
                item["to_character_source_id"],
            )
        )
    )
    if not core_ids:
        core_ids = all_ids[: min(2, len(all_ids))]
    inner_ids = [
        endpoint
        for endpoint in all_ids
        if endpoint not in core_ids
        and any(
            _relationship_layer_number(item["layer"]) == 2
            and endpoint
            in {
                item["from_character_source_id"],
                item["to_character_source_id"],
            }
            for item in relationships
        )
    ]
    outer_ids = [
        endpoint for endpoint in all_ids if endpoint not in {*core_ids, *inner_ids}
    ]
    center_x, center_y = 600.0, 405.0
    positions: dict[str, tuple[float, float, str]] = {}
    for index, source_id in enumerate(core_ids):
        x = center_x + (index - (len(core_ids) - 1) / 2) * 190
        positions[source_id] = (x, center_y, "core")
    for index, source_id in enumerate(inner_ids):
        angle = -math.pi / 2 + 2 * math.pi * index / max(1, len(inner_ids))
        positions[source_id] = (
            center_x + math.cos(angle) * 285,
            center_y + math.sin(angle) * 185,
            "inner",
        )
    for index, source_id in enumerate(outer_ids):
        angle = -math.pi / 2 + 2 * math.pi * index / max(1, len(outer_ids))
        positions[source_id] = (
            center_x + math.cos(angle) * 505,
            center_y + math.sin(angle) * 320,
            "outer",
        )
    edge_parts: list[str] = []
    badge_parts: list[str] = []
    legend_parts: list[str] = []
    for index, item in enumerate(relationships, start=1):
        source_id = item["from_character_source_id"]
        target_id = item["to_character_source_id"]
        if source_id not in positions or target_id not in positions:
            continue
        x1, y1, _ = positions[source_id]
        x2, y2, _ = positions[target_id]
        dx, dy = x2 - x1, y2 - y1
        length = max(1.0, math.hypot(dx, dy))
        curve = ((index % 5) - 2) * 14
        cx = (x1 + x2) / 2 - dy / length * curve
        cy = (y1 + y2) / 2 + dx / length * curve
        badge_x = (x1 + 2 * cx + x2) / 4
        badge_y = (y1 + 2 * cy + y2) / 4
        layer_number = _relationship_layer_number(item["layer"])
        edge_parts.append(
            f'<path class="character-edge layer-{layer_number}" '
            f'd="M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}">'
            f'<title>{escape(names[source_id])} → {escape(names[target_id])}：'
            f'{escape(item["function"])}；{escape(item["start_state"])} → '
            f'{escape(item["end_state"])}</title></path>'
        )
        badge_parts.append(
            f'<g class="relation-badge layer-{layer_number}">'
            f'<circle cx="{badge_x:.1f}" cy="{badge_y:.1f}" r="12"/>'
            f'<text class="svg-index" x="{badge_x:.1f}" y="{badge_y + 4:.1f}" '
            f'text-anchor="middle">{index}</text></g>'
        )
        legend_parts.append(
            f'<article class="relation-key layer-{layer_number}" '
            f'id="relation-key-{index}"><span class="relation-index">{index}</span>'
            f'<strong>第 {escape(item["layer"])} 层 · {escape(item["function"])}</strong>'
            f'<span>{escape(names[source_id])} → {escape(names[target_id])}</span>'
            f'<small>{escape(item["start_state"])} → {escape(item["change"])} → '
            f'{escape(item["end_state"])}</small></article>'
        )
    node_parts: list[str] = []
    for source_id in all_ids:
        if source_id not in positions:
            continue
        x, y, kind = positions[source_id]
        name = names[source_id]
        node_parts.append(
            f'<g class="character-node {kind}"><title>{escape(name)}</title>'
            f'<rect x="{x - 64:.1f}" y="{y - 25:.1f}" width="128" height="50" rx="20"/>'
            f'{_svg_text(x, y + 5, name, max_chars=8, line_height=15, css_class="svg-title", max_lines=2)}</g>'
        )
    svg = (
        '<div class="diagram-shell relationship-network" style="--diagram-min-width:900px" '
        'aria-label="人物关系网络图">'
        '<svg class="info-svg character-network-svg" viewBox="0 0 1200 820" '
        'role="img" aria-labelledby="character-network-title character-network-desc">'
        '<title id="character-network-title">以核心人物为中心的三层关系网络</title>'
        '<desc id="character-network-desc">核心人物位于中心，第二层人物位于内圈，其余行动与制度人物位于外圈；连线编号对应下方关系变化。</desc>'
        '<text x="28" y="32" class="svg-kicker">THREE-LAYER CHARACTER NETWORK · 三层人物关系网络</text>'
        '<ellipse class="svg-guide" cx="600" cy="405" rx="305" ry="205"/>'
        '<ellipse class="svg-guide" cx="600" cy="405" rx="530" ry="340"/>'
        + "".join(edge_parts)
        + "".join(badge_parts)
        + "".join(node_parts)
        + "</svg></div>"
    )
    return svg, '<div class="relationship-legend">' + "".join(legend_parts) + "</div>"


def render_visual_model(
    model: dict[str, Any],
    label: str,
    label_lookup: dict[str, str] | None = None,
) -> str:
    label_lookup = label_lookup or {}
    key_labels = {
        "name": "名称",
        "label": "标注",
        "from": "起点",
        "to": "终点",
        "source": "起点",
        "target": "终点",
        "relation": "关系",
        "function": "职责",
        "meaning": "含义",
        "description": "说明",
    }
    items: list[str] = []
    for kind, collection in (("节点", model.get("nodes", [])), ("连接", model.get("edges", []))):
        for entry in collection:
            if not isinstance(entry, dict):
                continue
            pairs = []
            for key, value in entry.items():
                if key in {"id", "source_ids"} or not isinstance(value, (str, int, float)):
                    continue
                display_value = label_lookup.get(value, value) if isinstance(value, str) else value
                pairs.append((key_labels.get(key, key), display_value))
            entry_id = entry.get("id")
            id_attr = f' id="{escape(entry_id)}"' if isinstance(entry_id, str) else ""
            items.append(
                f'<li{id_attr}><strong>{kind}</strong> · '
                + "；".join(
                    f"{escape(pair_label)}：{escape(value)}"
                    for pair_label, value in pairs
                )
                + "</li>"
            )
    if not items:
        return '<p class="section-intro">关系已由上方文字卡片完整表达。</p>'
    return (
        f'<div class="sr-only" aria-label="{escape(label)}的文字等价信息">'
        '<p>图形文字等价信息</p>'
        '<ul class="compact-list">'
        + "".join(items)
        + "</ul></div>"
    )


def render_control_spine_svg(orientation: dict[str, Any]) -> str:
    layers = orientation["logic_spine"]
    card_width = 208
    gap = 34
    margin = 30
    width = margin * 2 + len(layers) * card_width + (len(layers) - 1) * gap
    height = 260
    parts: list[str] = []
    for index, item in enumerate(layers):
        x = margin + index * (card_width + gap)
        parts.append(
            f'<g class="control-spine-node"><title>{escape(item["title"])}：'
            f'{escape(item["claim"])}；{escape(item["therefore"])}</title>'
            f'<rect class="story-stage-box" x="{x}" y="58" width="{card_width}" '
            f'height="168" rx="14"/>'
            f'<circle class="story-stage-number" cx="{x + 23}" cy="81" r="14"/>'
            f'<text class="svg-index" x="{x + 23}" y="85" text-anchor="middle">'
            f'{index + 1}</text>'
            f'{_svg_text(x + card_width / 2, 108, item["title"], max_chars=10, line_height=18, css_class="svg-title", max_lines=2)}'
            f'{_svg_text(x + card_width / 2, 150, item["claim"], max_chars=15, line_height=16, css_class="svg-copy", max_lines=3)}'
            f'{_svg_text(x + card_width / 2, 205, "因此｜" + item["therefore"], max_chars=15, line_height=15, css_class="svg-small", max_lines=2)}</g>'
        )
        if index < len(layers) - 1:
            parts.append(
                f'<path class="control-spine-arrow" d="M {x + card_width + 4} 142 '
                f'L {x + card_width + gap - 7} 142"/>'
            )
    return (
        '<div class="diagram-shell" style="--diagram-min-width:980px">'
        f'<svg class="info-svg control-spine-svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="control-spine-title control-spine-desc">'
        '<title id="control-spine-title">构思控制总链</title>'
        '<desc id="control-spine-desc">从世界观命题开始，依次推导世界规则、事件环境、故事架构、人物选择与终局契约。</desc>'
        '<defs><marker id="control-spine-arrowhead" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#2457A7"/></marker></defs>'
        '<text x="30" y="31" class="svg-kicker">CONCEPTION CONTROL SPINE · 构思控制总链</text>'
        + "".join(parts)
        + "</svg></div>"
    )


def render_orientation(bp: dict[str, Any]) -> str:
    value = bp["orientation"]
    logic_cards = "".join(
        f"""<article class="card" id="{escape(item["id"])}">
          <h3>{escape(item["title"])}</h3>
          <p class="control-summary">{escape(item["claim"])} → {escape(item["therefore"])}</p>
          {dl([("控制什么", item["controls"]), ("必须成立", item["must_hold"]), ("解释边界", item["boundary"])])}
        </article>"""
        for item in value["logic_spine"]
    )
    return f"""
<section id="orientation" class="panel" aria-labelledby="orientation-heading">
  <div class="section-heading"><span class="section-number">0</span><div>
    <h2 id="orientation-heading">先确认：这是什么故事</h2>
    <p class="section-intro">{escape(value["review_instruction"]["text"])}</p>
  </div></div>
  <p class="identity">{escape(value["story_identity"]["text"])}</p>
  <div class="two-col">
    <article class="card"><h3>这是</h3>{render_text_list(value["this_is"])}</article>
    <article class="card"><h3>这不是</h3>{render_text_list(value["this_is_not"])}</article>
  </div>
  <p class="visual-title">构思控制总链 · 每一层说明为何推出下一层，以及下游不得偏离什么</p>
  {render_control_spine_svg(value)}
  <div class="card-grid">{logic_cards}</div>
</section>"""


def render_world(bp: dict[str, Any]) -> str:
    world = bp["world"]
    visual_labels: dict[str, str] = {}
    for entry in [*world["systems"], *world["environments"]]:
        visual_labels[entry["id"]] = entry["name"]
        for source_id in entry["source_ids"]:
            visual_labels.setdefault(source_id, entry["name"])
    systems = "".join(
        f"""<article class="card" id="{escape(item["id"])}">
        <h3>{escape(item["name"])}</h3>
        <p class="control-summary">{escape(item["control_summary"])}</p>
        <details><summary>查看运行参数与边界</summary>{dl([
            ("定义", item["definition"]), ("规则", item["rule"]),
            ("权限", item["permissions"]), ("资源", item["resources"]),
            ("代价 / 失败", item["cost_or_failure"]), ("控制对象", item["controls"]),
            ("不得写成", item["must_not"])
        ])}</details></article>"""
        for item in world["systems"]
    )
    environments = "".join(
        f"""<article class="card" id="{escape(item["id"])}">
        <h3>{escape(item["name"])}</h3>
        <p class="control-summary">{escape(item["control_summary"])}</p>
        <details><summary>查看事件承载条件</summary>{dl([
            ("环境特征", item["signature"]), ("基本要素", item["elements"]),
            ("进入与危险", item["access_and_hazard"]),
            ("允许发生", item["affordances"]), ("禁止捷径", item["prohibitions"]),
            ("故事职责", item["story_function"]), ("状态变化", item["state_change"]),
            ("控制对象", item["controls"]), ("必须成立", item["must_hold"])
        ])}</details></article>"""
        for item in world["environments"]
    )
    boundaries = "".join(
        f'<li id="{escape(item["id"])}"><strong>{escape(item.get("name", "边界"))}：</strong>'
        f'{escape(item.get("commitment", text_item(item)))}</li>'
        for item in world["boundaries"]
    )
    opens = "".join(
        f'<li id="{escape(item["id"])}"><strong>{escape(item.get("title", "开放接口"))}：</strong>'
        f'{escape(item.get("text", text_item(item)))}</li>'
        for item in world["open_interfaces"]
    )
    return f"""
<section id="world" class="panel" aria-labelledby="world-heading">
  <div class="section-heading"><span class="section-number">1</span><div>
    <h2 id="world-heading">小说世界设定</h2>
    <p class="section-intro">{escape(world["definition"]["text"])}</p>
  </div></div>
  <p class="visual-title">世界运行图 · 先看规则如何运转，再看事件由哪些环境承载</p>
  {render_world_system_svg(world)}
  {render_environment_svg(world)}
  {render_visual_model(world["visual_model"], "世界运行图", visual_labels)}
  <h3 class="visual-title">运行系统</h3><div class="card-grid">{systems}</div>
  <h3 class="visual-title">主要环境</h3><div class="card-grid">{environments}</div>
  <div class="two-col">
    <article class="card"><h3>必须守住的边界</h3><ul class="compact-list">{boundaries}</ul></article>
    <article class="card"><h3>后续仍可开发的接口</h3><ul class="compact-list">{opens}</ul></article>
  </div>
  <p class="review-question">评审问题：{escape(world["review_question"])}</p>
</section>"""


def render_story(bp: dict[str, Any]) -> str:
    story = bp["story"]
    definition = story["definition"]
    kind_labels = {
        "main": "主线",
        "subplot": "支线",
        "background": "背景线",
    }
    line_names = {item["id"]: item["name"] for item in story["lines"]}
    story_visual_labels = {
        **line_names,
        **{item["id"]: item["label"] for item in story["timeline"]},
    }
    line_cards = "".join(
        f"""<article class="card line-{escape(item["kind"])}" id="{escape(item["id"])}">
          <h3>{escape(item["name"])}</h3>
          <p class="control-summary">{escape(item["control_summary"])}</p>
          <details><summary>查看故事线接口</summary>{dl([
              ("类型", kind_labels[item["kind"]]), ("职责", item["function"]),
              ("起点", item["start"]), ("目标", item["objective"]),
              ("驱动者", item["driver"]), ("交汇", item["intersections"]),
              ("连接点", item["connection_points"]), ("终点", item["end"]),
              ("退出条件", item["exit_condition"]), ("必须成立", item["must_hold"]),
              ("展开自由", item["optional_scope"])
          ])}</details>
        </article>"""
        for item in story["lines"]
    )
    timeline = "".join(
        f"""<article class="timeline-stage" id="{escape(item["id"])}">
          <div class="timeline-body">
            <h3>{escape(item["label"])}</h3>
            <p class="control-summary">{escape(item["logic_summary"])}</p>
            <details><summary>查看阶段状态转移</summary>{dl([
                ("压力", item["pressure"]), ("选择", item["choice"]),
                ("直接后果", item["consequence"]), ("代价", item["cost"]),
                ("新状态", item["new_state"]),
                ("涉及故事线", "、".join(line_names[line_id] for line_id in item["line_ids"]))
            ])}</details>
          </div>
        </article>"""
        for item in story["timeline"]
    )
    events = "".join(
        f"""<tr id="{escape(item["id"])}">
          <th scope="row">{escape(item["name"])}</th>
          <td>{escape(item["role"])}</td>
          <td>{escape(item["logic"])}</td>
          <td>{escape(item["controls"])}</td>
        </tr>"""
        for item in story["event_controls"]
    )
    event_index = "".join(
        f'<li><strong>{escape(item["name"])}</strong></li>'
        for item in story["event_controls"]
    )
    return f"""
<section id="story" class="panel" aria-labelledby="story-heading">
  <div class="section-heading"><span class="section-number">2</span><div>
    <h2 id="story-heading">小说故事线设定</h2>
    <p class="section-intro">{escape(definition["promise"])}</p>
  </div></div>
  <div class="definition-grid">
    <article class="card">{dl([
      ("戏剧问题", definition["dramatic_question"]), ("故事起点", definition["start"]),
      ("故事终点", definition["end"]), ("核心赌注", definition["stakes"])
    ])}</article>
    <article class="card">
      <h3>叙述约束</h3>{render_text_list(story["narrative_constraints"])}
      <h3>开放接口</h3>{render_text_list(story["open_interfaces"])}
    </article>
  </div>
  <p class="visual-title">故事线 · 主线、支线、背景线分别标识</p>
  <div class="line-strip" role="list" aria-label="故事线">{line_cards}</div>
  <p class="visual-title">多线推进图 · 八个因果阶段与三条故事线合并阅读</p>
  {render_story_svg(story)}
  <p class="visual-title">多线时间线 · 每一步都显示压力、选择、后果和代价</p>
  <div class="timeline">{timeline}</div>
  <h3 class="visual-title">主要事件控制链 · 定义必要前提、不可逆变化与下游责任</h3>
  <ol class="event-index">{event_index}</ol>
  <details class="event-control-details"><summary>展开全部主要事件的前提、变化、结果与控制项</summary>
    <div class="table-scroll"><table class="control-table">
      <thead><tr><th>事件</th><th>职责</th><th>前提 → 转折 → 结果</th><th>控制什么</th></tr></thead>
      <tbody>{events}</tbody>
    </table></div>
  </details>
  {render_visual_model(story["visual_model"], "多线时间线", story_visual_labels)}
  <p class="review-question">评审问题：{escape(story["review_question"])}</p>
</section>"""


def render_characters(bp: dict[str, Any]) -> str:
    characters = bp["characters"]
    character_names = {
        item["character_source_id"]: item["name"] for item in characters["profiles"]
    }
    character_visual_labels = {
        **character_names,
        **{item["id"]: item["name"] for item in characters["profiles"]},
        **{
            item["id"]: f"第 {item['layer']} 层 · {item['function']}"
            for item in characters["relationship_layers"]
        },
    }
    character_svg, relationship_legend = render_character_svg(characters)
    profiles = "".join(
        f"""<article class="card" id="{escape(item["id"])}">
          <h3>{escape(item["name"])} <span class="tag">{escape(item["role"])}</span></h3>
          <p class="control-summary">{escape(item["responsibility"])}</p>
          <details><summary>查看人物责任契约</summary>{dl([
            ("故事职责", item["story_function"]), ("责任对象", item["responsibility"]),
            ("可用权限", item["authority"]), ("不可委托选择", item["nondelegable_choice"]),
            ("表层目标", item["surface_goal"]), ("深层需要", item["deeper_need"]),
            ("恐惧", item["fear"]), ("价值与边界", item["values_and_boundaries"]),
            ("信息限制", item["information_limits"]), ("受压行为", item["pressure_behavior"]),
            ("自主选择", item["agency_choice"]), ("人物弧线", item["arc"]),
            ("终态", item["end_state"]), ("控制对象", item["controls"]),
            ("不可改写", item["invariants"]), ("不得写成", item["must_not"])
          ])}</details>
        </article>"""
        for item in characters["profiles"]
    )
    layers = "".join(
        f"""<article class="relationship-layer" id="{escape(item["id"])}">
          <div class="layer-label">第 {escape(item["layer"])} 层<br>{escape(item["function"])}</div>
          <div class="card"><p class="control-summary">{escape(character_names[item["from_character_source_id"]])} →
          {escape(character_names[item["to_character_source_id"]])}：{escape(item["function"])}</p>
          <details><summary>查看关系变化契约</summary>{dl([
            ("关系对象", f'{character_names[item["from_character_source_id"]]} → {character_names[item["to_character_source_id"]]}'),
            ("初态", item["start_state"]), ("压力", item["pressure"]),
            ("触发条件", item["trigger"]), ("变化动作", item["change"]),
            ("终态", item["end_state"]), ("控制对象", item["controls"]),
            ("必须成立", item["must_hold"])
          ])}</details></div>
        </article>"""
        for item in characters["relationship_layers"]
    )
    return f"""
<section id="characters" class="panel" aria-labelledby="characters-heading">
  <div class="section-heading"><span class="section-number">3</span><div>
    <h2 id="characters-heading">小说人物设定</h2>
    <p class="section-intro">{escape(characters["definition"]["text"])}</p>
  </div></div>
  <div class="profile-grid">{profiles}</div>
  <p class="visual-title">人物关系网络 · 中心、内圈与外圈呈现关系扩展，连线编号对应下方变化</p>
  {character_svg}
  {relationship_legend}
  <p class="visual-title">三层人物关系 · 每层都说明职责与变化</p>
  <div class="relationship-map">{layers}</div>
  {render_visual_model(
      characters["visual_model"],
      "分层人物关系图",
      character_visual_labels,
  )}
  <p class="review-question">评审问题：{escape(characters["review_question"])}</p>
</section>"""


def render_fragments(bp: dict[str, Any]) -> str:
    fragments = bp["fragments"]
    items = "".join(
        f"""<article class="fragment" id="{escape(item["id"])}">
          <span class="fragment-label">构思验证片段</span>
          <h3>{escape(item["title"])}</h3>
          <p class="fragment-purpose">{escape(item["purpose"])}</p>
          <div class="prose">{escape(item["text"])}</div>
          <p class="review-question">看片段时只判断：{escape(item["review_question"])}</p>
        </article>"""
        for item in fragments["items"]
    )
    return f"""
<section id="fragments" class="panel" aria-labelledby="fragments-heading">
  <div class="section-heading"><span class="section-number">4</span><div>
    <h2 id="fragments-heading">小说片段</h2>
    <p class="section-intro">{escape(fragments["sample_authority"])}</p>
  </div></div>
  {items}
  <p class="review-question">评审问题：{escape(fragments["review_question"])}</p>
</section>"""


def render_decision(bp: dict[str, Any]) -> str:
    decision = bp["decision"]
    labels = {
        "world": "世界",
        "story": "故事",
        "characters": "人物",
        "fragments": "片段",
    }
    fields = "".join(
        f"""<fieldset data-domain="{escape(domain)}">
          <legend>{escape(labels[domain])} · {escape(question)}</legend>
          <label class="choice" for="{escape(domain)}-approve">
            <input id="{escape(domain)}-approve" type="radio" name="{escape(domain)}" value="approve">通过
          </label>
          <label class="choice" for="{escape(domain)}-revise">
            <input id="{escape(domain)}-revise" type="radio" name="{escape(domain)}" value="revise">需调整
          </label>
          <label for="{escape(domain)}-notes">修改意见</label>
          <textarea id="{escape(domain)}-notes" name="{escape(domain)}-notes"></textarea>
        </fieldset>"""
        for domain, question in decision["questions"].items()
    )
    opens = render_text_list(decision["open_items"])
    return f"""
<section id="decision" class="panel" aria-labelledby="decision-heading">
  <div class="section-heading"><span class="section-number">5</span><div>
    <h2 id="decision-heading">作者判断</h2>
    <p class="section-intro">{escape(decision["instruction"])}</p>
  </div></div>
  <form aria-label="作者评审草稿">
    <div class="decision-grid">{fields}</div>
    <article class="card"><h3>仍然开放的事项</h3>{opens}</article>
    <button id="copy-review-draft" type="button">复制或下载评审草稿</button>
    <p id="copy-status" class="status" role="status" aria-live="polite"></p>
  </form>
  <p class="decision-notice"><strong>重要：</strong>页面中的选择只是本地草稿。只有经工作流提交并绑定当前报告哈希后，才构成作者批准或退回决定。</p>
</section>"""


def render_traceability(report: dict[str, Any]) -> str:
    bindings = report["source_bindings"]
    return f"""
<details>
  <summary>查看机器追溯信息（不计入十分钟正文）</summary>
  <div class="trace">
    <p>run_id: {escape(report["run_id"])}</p>
    <p>source_inventory_sha256: {escape(bindings["source_inventory_sha256"])}</p>
    <p>review_plan_sha256: {escape(bindings["review_plan_sha256"])}</p>
    <p>fragment_package_sha256: {escape(bindings["fragment_package_sha256"])}</p>
    <p>coverage_entries: {len(report["coverage_ledger"])} · review_tasks: {len(report["review_tasks"])}</p>
  </div>
</details>"""


def render_html(report: dict[str, Any], report_sha256: str) -> str:
    bp = report["report_blueprint"]
    work_title = report["review_contract"]["work_title"]
    story_identity = text_item(bp["orientation"]["story_identity"])
    minutes = report["review_contract"]["target_minutes"]
    measured = report["reading_measurement"]["measured_total_minutes"]
    return f"""<!doctype html>
<html lang="zh-CN" data-style-contract="{STYLE_CONTRACT["id"]}" data-report-sha256="{report_sha256}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="{escape(CSP)}">
  <meta name="referrer" content="no-referrer">
  <meta name="report-sha256" content="{report_sha256}">
  <title>《{escape(work_title)}》 · 小说构思人审报告</title>
  <style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="masthead">
    <div class="masthead-inner">
      <p class="eyebrow">小说构思人审报告</p>
      <h1>《{escape(work_title)}》</h1>
      <p class="lead">{escape(story_identity)}</p>
      <ul class="review-meta">
        <li>目标用时 {escape(minutes)} 分钟</li>
        <li>实测预算 {escape(measured)} 分钟</li>
        <li>四项分区判断</li>
        <li>状态：待作者判断</li>
      </ul>
    </div>
  </header>
  <nav class="section-nav" aria-label="评审章节">
    <ol>
      <li><a href="#orientation">故事身份</a></li>
      <li><a href="#world">1 世界</a></li>
      <li><a href="#story">2 故事线</a></li>
      <li><a href="#characters">3 人物</a></li>
      <li><a href="#fragments">4 片段</a></li>
      <li><a href="#decision">5 判断</a></li>
    </ol>
  </nav>
  <main id="main-content">
    {render_orientation(bp)}
    {render_world(bp)}
    {render_story(bp)}
    {render_characters(bp)}
    {render_fragments(bp)}
    {render_decision(bp)}
    {render_traceability(report)}
  </main>
  <footer class="page-footer">
    <p>固定视觉契约：{escape(STYLE_CONTRACT["name"])}（{STYLE_CONTRACT["id"]}）。页面为离线单文件，不连接网络，也不自行形成作者批准。</p>
  </footer>
  <script type="application/json" id="report-data">{embedded_json(report)}</script>
  <script>{SCRIPT}</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render an accepted conception review package as deterministic HTML."
    )
    parser.add_argument("assembly_package", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--fragments", required=True, type=Path)
    parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        upstream = validate_upstream(
            args.assembly_package, args.plan, args.fragments, args.r1
        )
        report = upstream["report"]
        report_sha = upstream["report_sha256"]
        html_path = output / "human-review-report.html"
        html_path.write_text(render_html(report, report_sha), encoding="utf-8")

        skill_dir = Path(__file__).resolve().parents[1]
        skill_bindings = [
            {
                "path": path.relative_to(skill_dir).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in all_skill_files(skill_dir)
        ]
        record = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "mode": "deterministic_html_render",
            "run_id": report["run_id"],
            "style_contract": STYLE_CONTRACT,
            "inputs": {
                "human-review-report.json": report_sha,
                "assembly-package-manifest.json": upstream[
                    "assembly_manifest_sha256"
                ],
                "assembly-validation.json": upstream["assembly_validation_sha256"],
            },
            "skill_bindings": skill_bindings,
            "outputs": {
                "human-review-report.html": sha256_file(html_path),
            },
        }
        record_path = output / "render-record.json"
        write_json(record_path, record)
        manifest = {
            "schema_version": "1.0",
            "skill": SKILL_NAME,
            "run_id": report["run_id"],
            "stage": "H3",
            "verdict": "ready",
            "files": [
                {"path": html_path.name, "sha256": sha256_file(html_path)},
                {"path": record_path.name, "sha256": sha256_file(record_path)},
            ],
            "author_review_artifact": {
                "path": html_path.name,
                "sha256": sha256_file(html_path),
                "report_sha256": report_sha,
            },
        }
        write_json(output / "package-manifest.json", manifest)

        from validate_review_html import validate_package

        evidence = validate_package(
            output,
            args.assembly_package.resolve(),
            args.plan.resolve(),
            args.fragments.resolve(),
            args.r1.resolve(),
        )
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "verdict": "ready",
                "errors": [],
                "evidence": evidence,
            },
        )
    except ContractError as exc:
        write_json(
            output / "validation.json",
            {
                "schema_version": "1.0",
                "skill": SKILL_NAME,
                "verdict": "blocked",
                "errors": [str(exc)],
                "evidence": {},
            },
        )
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(
        "READY: deterministic self-contained HTML generated; "
        f"style={STYLE_CONTRACT['id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
