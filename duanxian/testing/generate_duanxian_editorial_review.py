from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve().parents[2] / "engine"
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2] / "engine"
NOVEL = ENGINE.parent / "duanxian"
sys.path.insert(0, str(ENGINE))

from testing import duanxian_h1_plan as plan_fixture
from testing import duanxian_h1_fragments as fragment_fixture


RUN = (
    ENGINE
    / "projects"
    / "duanxian"
    / "conception-runs"
    / "duanxian-conception-v2-20260803-04"
)
OUTPUT = NOVEL / "human-review" / "review-12"

h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)
h1c = importlib.import_module(
    "skills.novel-conception-review-html-generator.scripts.run_v2"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"style", "script"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.values.append(data)


def _humanize_report() -> tuple[dict, dict]:
    source_report = _read(
        RUN / "H1" / "assembly" / "human-review-report.json"
    )
    inventory = _read(RUN / "H1" / "plan" / "source-inventory.json")
    execution = _read(RUN / "H1" / "plan" / "execution-record.json")
    plan_fixture.RUN_ID = source_report["run_id"]
    plan, _, _ = plan_fixture.build_plan(
        inventory=inventory,
        p1_completion=source_report["p1_completion"],
        input_gate=execution["input_gate"],
        session_id=source_report["h1_session_id"],
    )
    h1a.validate_review_plan(
        plan,
        source_inventory=inventory,
        workspace_state={"session_id": plan["h1_session_id"]},
        work_identity=plan["work_identity"],
        runtime=h1a.rt.ContractRuntime(),
    )
    # Forward-test the real H1-B writer contract against the latest P1 package.
    # The fixture module is reusable across production runs; anchor resolution
    # must therefore follow this report's source run, not its module default.
    fragment_fixture.RUN_ROOT = RUN
    submissions = fragment_fixture.build_submissions(plan, inventory)
    anchors = fragment_fixture._load_anchor_values(inventory)
    _, _, final_fragments, _ = (
        fragment_fixture.h1b._validate_agent_submissions(
            submissions,
            briefs=plan["fragment_briefs"],
            anchors=anchors,
        )
    )
    fragment_package = fragment_fixture.h1b._fragment_package(
        plan=plan,
        p1_artifact=source_report["p1_completion"],
        plan_manifest=h1a.rt.artifact_reference(
            RUN / "H1" / "plan" / "package-manifest.json", root=RUN
        ),
        final_fragments=final_fragments,
        anchors=anchors,
    )
    report = h1a._assemble_report(
        plan, inventory, fragment_package["fragments"]
    )
    return report, plan


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"output exists: {OUTPUT}")
    report, plan = _humanize_report()
    runtime = h1c.rt.ContractRuntime()
    runtime.validate(report, "human-review-report.schema.json")
    document = h1c.render_html(report)
    validation = h1c.validate_html_document(document, report)

    visible = _VisibleText()
    visible.feed(document)
    visible.close()
    visible_text = " ".join(visible.values)
    forbidden = re.compile(
        r"(?:MOD-|VIS-|FRAG-|DCTRL-|sha256|json pointer|source anchor|"
        r"Full P1 evidence|Decision controls|图形逐值信息|来源覆盖|迁移评审)",
        re.IGNORECASE,
    )
    if forbidden.search(visible_text):
        raise SystemExit("machine audit text leaked into visible content")
    checks = {
        "schema_version": "2.0",
        "verdict": "ready",
        "checks": validation["checks"],
        "content_dimensions": [
            "world",
            "storylines",
            "characters",
            "fragments",
        ],
        "svg_count": document.count('class="semantic-visual"'),
        "fragment_count": document.count('class="fragment"'),
        "machine_audit_visible": False,
        "source_run": report["run_id"],
        "source_p1": report["p1_completion"],
        "presentation_contract": h1c.RENDER_CONTRACT,
        "plan_session": plan["h1_session_id"],
    }
    if checks["svg_count"] != 5 or checks["fragment_count"] != 2:
        raise SystemExit("human review surface is incomplete")

    html_root = OUTPUT / "html"
    html_root.mkdir(parents=True)
    (OUTPUT / "human-review-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    (OUTPUT / "validation.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    (html_root / "human-review-report.html").write_text(
        document,
        encoding="utf-8",
        newline="",
    )
    print(json.dumps(checks, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
