from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
FRAGMENT_DIR = SKILL_DIR.parent / "novel-conception-fragment-writer"
FRAGMENT_SCRIPTS = FRAGMENT_DIR / "scripts"
ASSEMBLER_DIR = SKILL_DIR.parent / "novel-conception-human-review-assembler"
sys.path.insert(0, str(SCRIPTS))

from common import (  # noqa: E402
    ContractError,
    STYLE_CONTRACT,
    inspect_html,
    load_json,
    sha256_file,
    write_json,
)
from render_review_html import render_html, render_visual_model  # noqa: E402
from validate_review_html import validate_package  # noqa: E402


_third_common = sys.modules["common"]
_fragment_spec = importlib.util.spec_from_file_location(
    "fragment_writer_test_helpers",
    FRAGMENT_DIR / "tests" / "test_workflow.py",
)
assert _fragment_spec and _fragment_spec.loader
_fragment_helpers = importlib.util.module_from_spec(_fragment_spec)
sys.modules.pop("common", None)
sys.path.insert(0, str(FRAGMENT_SCRIPTS))
try:
    _fragment_spec.loader.exec_module(_fragment_helpers)
finally:
    sys.path.remove(str(FRAGMENT_SCRIPTS))
    sys.modules["common"] = _third_common


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


def snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def restore(directory: Path, data: dict[str, bytes]) -> None:
    expected = set(data)
    for path in sorted(directory.rglob("*"), reverse=True):
        if path.is_file() and path.relative_to(directory).as_posix() not in expected:
            path.unlink()
    for name, content in data.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


class HtmlGeneratorWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.r1, _ = _fragment_helpers.make_upstream(cls.root)
        cls.plan = _fragment_helpers.make_plan_package(cls.root, cls.r1)
        briefs = _fragment_helpers.load_json(cls.plan / "fragment-briefs.json")
        contracts = _fragment_helpers.scene_contracts(briefs)
        drafts = _fragment_helpers.drafts(briefs, contracts)
        audit = _fragment_helpers.revision_audit(briefs, drafts)

        writing = cls.root / "writing"
        run_command(
            str(FRAGMENT_SCRIPTS / "manage_writing.py"),
            "begin",
            str(cls.plan),
            str(cls.r1),
            str(writing),
            "--executor-id",
            "fragment-executor",
            "--task-id",
            "fragment-task",
        )
        for phase, data in (
            ("scene-contracts", contracts),
            ("drafts", drafts),
            ("revision-audit", audit),
        ):
            payload = cls.root / f"{phase}.json"
            write_json(payload, data)
            run_command(
                str(FRAGMENT_SCRIPTS / "manage_writing.py"),
                "submit",
                str(writing),
                phase,
                str(payload),
            )
        cls.fragments = cls.root / "fragment-package"
        run_command(
            str(FRAGMENT_SCRIPTS / "finalize_fragments.py"),
            str(writing),
            str(cls.fragments),
        )
        cls.assembly = cls.root / "assembly"
        run_command(
            str(ASSEMBLER_DIR / "scripts" / "assemble_human_review.py"),
            str(cls.plan),
            str(cls.fragments),
            str(cls.assembly),
            "--r1",
            str(cls.r1),
        )
        cls.output = cls.root / "html-package"
        run_command(
            str(SCRIPTS / "render_review_html.py"),
            str(cls.assembly),
            str(cls.output),
            "--plan",
            str(cls.plan),
            "--fragments",
            str(cls.fragments),
            "--r1",
            str(cls.r1),
        )
        cls.snapshots = {
            "r1": snapshot(cls.r1),
            "plan": snapshot(cls.plan),
            "fragments": snapshot(cls.fragments),
            "assembly": snapshot(cls.assembly),
            "output": snapshot(cls.output),
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def setUp(self) -> None:
        for name, directory in (
            ("r1", self.r1),
            ("plan", self.plan),
            ("fragments", self.fragments),
            ("assembly", self.assembly),
            ("output", self.output),
        ):
            restore(directory, self.snapshots[name])

    def validate(self) -> dict:
        return validate_package(
            self.output, self.assembly, self.plan, self.fragments, self.r1
        )

    def rebind_html_outer_hashes(self) -> None:
        html_path = self.output / "human-review-report.html"
        html_sha = sha256_file(html_path)
        record_path = self.output / "render-record.json"
        record = load_json(record_path)
        record["outputs"]["human-review-report.html"] = html_sha
        write_json(record_path, record)
        manifest_path = self.output / "package-manifest.json"
        manifest = load_json(manifest_path)
        for entry in manifest["files"]:
            if entry["path"] == "human-review-report.html":
                entry["sha256"] = html_sha
            if entry["path"] == "render-record.json":
                entry["sha256"] = sha256_file(record_path)
        manifest["author_review_artifact"]["sha256"] = html_sha
        write_json(manifest_path, manifest)

    def test_full_three_skill_chain_is_ready(self) -> None:
        evidence = self.validate()
        self.assertEqual(evidence["fixed_style_contract"], STYLE_CONTRACT["id"])
        self.assertTrue(evidence["deterministic_render"])
        self.assertFalse(evidence["content_rewriting"])
        self.assertEqual(
            load_json(self.output / "validation.json")["verdict"], "ready"
        )

    def test_human_view_uses_names_and_real_relationship_graphics(self) -> None:
        document = (self.output / "human-review-report.html").read_text(encoding="utf-8")
        self.assertIn("<h1>《雾港守门人》</h1>", document)
        self.assertIn("<title>《雾港守门人》 · 小说构思人审报告</title>", document)
        self.assertIn("story-lanes", document)
        self.assertIn("relationship-network", document)
        self.assertIn("world-system-svg", document)
        self.assertIn("environment-svg", document)
        self.assertIn("story-flow-svg", document)
        self.assertIn("character-network-svg", document)
        self.assertGreaterEqual(document.count('role="img"'), 4)
        self.assertIn("守门主线", document)
        self.assertIn("林澈 → 周遥", document)
        self.assertIn("主线", document)
        self.assertNotIn(">HR-SL-01<", document)
        self.assertNotIn(">C1 → C2<", document)
        self.assertNotIn(">main<", document)

    def test_visual_model_references_are_resolved_to_human_labels(self) -> None:
        rendered = render_visual_model(
            {
                "nodes": [],
                "edges": [
                    {
                        "id": "HR-E-01",
                        "from": "C1",
                        "to": "C2",
                        "relation": "协作",
                        "source_ids": ["C1", "C2"],
                    }
                ],
            },
            "人物关系",
            {"C1": "林澈", "C2": "周遥"},
        )
        self.assertIn("起点：林澈", rendered)
        self.assertIn("终点：周遥", rendered)
        self.assertNotIn("起点：C1", rendered)

    def test_second_render_is_byte_identical(self) -> None:
        second = self.root / "html-package-second"
        if second.exists():
            for child in sorted(second.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            second.rmdir()
        run_command(
            str(SCRIPTS / "render_review_html.py"),
            str(self.assembly),
            str(second),
            "--plan",
            str(self.plan),
            "--fragments",
            str(self.fragments),
            "--r1",
            str(self.r1),
        )
        self.assertEqual(
            (self.output / "human-review-report.html").read_bytes(),
            (second / "human-review-report.html").read_bytes(),
        )

    def test_upstream_report_tampering_is_blocked(self) -> None:
        path = self.assembly / "human-review-report.json"
        data = load_json(path)
        data["report_blueprint"]["world"]["definition"]["text"] = "被篡改"
        write_json(path, data)
        with self.assertRaisesRegex(ContractError, "manifest hash mismatch"):
            self.validate()

    def test_html_prose_tampering_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace("许可灯", "霓虹灯", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaises(ContractError):
            self.validate()

    def test_missing_csp_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8")
        text = re_sub_once(
            r'\s*<meta http-equiv="Content-Security-Policy"[^>]+>', "", text
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "Content Security Policy"):
            self.validate()

    def test_external_resource_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            "</head>", '<script src="https://example.com/x.js"></script></head>', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "external or executable URL"):
            self.validate()

    def test_inline_handler_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            'id="copy-review-draft"', 'id="copy-review-draft" onclick="alert(1)"', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "inline event handler"):
            self.validate()

    def test_hidden_required_section_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            '<section id="world"', '<section id="world" hidden', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "hidden content"):
            self.validate()

    def test_required_section_in_details_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8")
        text = text.replace('<section id="world"', '<details><section id="world"', 1)
        text = text.replace('<section id="story"', '</details><section id="story"', 1)
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "cannot be inside details"):
            self.validate()

    def test_preselected_author_decision_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            'value="approve">通过', 'value="approve" checked>通过', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "must not be preselected"):
            self.validate()

    def test_unlabelled_decision_control_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            'for="world-notes"', 'for="missing-notes"', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "lacks an explicit label"):
            self.validate()

    def test_embedded_report_tampering_is_blocked(self) -> None:
        path = self.output / "human-review-report.html"
        text = path.read_text(encoding="utf-8").replace(
            '"status":"ready"', '"status":"blocked"', 1
        )
        path.write_text(text, encoding="utf-8")
        self.rebind_html_outer_hashes()
        with self.assertRaisesRegex(ContractError, "embedded report JSON differs"):
            self.validate()

    def test_style_contract_tampering_is_blocked(self) -> None:
        path = self.output / "render-record.json"
        data = load_json(path)
        data["style_contract"]["name"] = "临场主题"
        write_json(path, data)
        manifest = load_json(self.output / "package-manifest.json")
        for entry in manifest["files"]:
            if entry["path"] == "render-record.json":
                entry["sha256"] = sha256_file(path)
        write_json(self.output / "package-manifest.json", manifest)
        with self.assertRaisesRegex(ContractError, "fixed style contract was changed"):
            self.validate()

    def test_current_skill_binding_is_hard(self) -> None:
        path = self.output / "render-record.json"
        data = load_json(path)
        data["skill_bindings"] = data["skill_bindings"][:-1]
        write_json(path, data)
        manifest = load_json(self.output / "package-manifest.json")
        for entry in manifest["files"]:
            if entry["path"] == "render-record.json":
                entry["sha256"] = sha256_file(path)
        write_json(self.output / "package-manifest.json", manifest)
        with self.assertRaisesRegex(ContractError, "current skill implementation"):
            self.validate()

    def test_untrusted_text_is_escaped_in_html_and_embedded_json(self) -> None:
        report = load_json(self.assembly / "human-review-report.json")
        report = copy.deepcopy(report)
        report["report_blueprint"]["orientation"]["story_identity"][
            "text"
        ] = '<script>alert("x")</script>'
        document = render_html(report, "0" * 64)
        self.assertNotIn('<script>alert("x")</script>', document)
        self.assertIn("&lt;script&gt;alert", document)
        inspector = inspect_html(document)
        self.assertEqual(json.loads(inspector.embedded_report), report)

    def test_skill_contains_no_fixture_story_names(self) -> None:
        forbidden = {"林澈", "周遥", "许可灯", "封闭港站"}
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix in {".md", ".py", ".yaml", ".yml"}
            and "tests" not in path.parts
        )
        self.assertFalse(forbidden & {word for word in forbidden if word in content})


def re_sub_once(pattern: str, replacement: str, text: str) -> str:
    import re

    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise AssertionError(f"pattern not found: {pattern}")
    return updated


if __name__ == "__main__":
    unittest.main()
