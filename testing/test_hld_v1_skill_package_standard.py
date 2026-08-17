from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILLS = {
    "HB0": "novel-hld-baseline-admitter",
    "HA1": "novel-hld-narrative-architect",
    "HS1": "novel-hld-storyline-choreographer",
    "HC1": "novel-hld-character-arc-placer",
    "HI1": "novel-hld-information-architect",
    "HR1": "novel-hld-rhythm-continuity-architect",
    "HK1": "novel-hld-key-scene-function-planner",
    "HQ1": "novel-hld-semantic-reviewer",
    "HP1": "novel-hld-package-assembler",
    "HQ2": "novel-hld-lld-readiness-evaluator",
    "HH1-A": "novel-hld-review-report-assembler",
    "HH1-B": "novel-hld-presentation-fidelity-reviewer",
    "HH1-C": "novel-hld-html-renderer",
    "HF1": "novel-hld-finalizer",
}
CASE_SECTIONS = (
    "## Prompt",
    "## Expected Behavior",
    "## Forbidden Behavior",
    "## Scoring Rule",
    "## Pass Bar",
)
MOJIBAKE = re.compile(r"(?:\ufffd|Ã.|Â.|â€|ï»¿|窶)")
URL = re.compile(r"https?://[^)\s>]+")


class HLDV1SkillPackageStandard(unittest.TestCase):
    def test_all_fourteen_skill_packages_exist(self) -> None:
        for stage, name in SKILLS.items():
            with self.subTest(stage=stage):
                self.assertTrue((REPO / "skills" / name).is_dir(), name)

    def test_required_runtime_and_research_files(self) -> None:
        required = (
            "SKILL.md",
            "agents/openai.yaml",
            "references/sources.md",
            "references/methodology.md",
            "references/sop.md",
            "docs/design-brief.md",
            "docs/file-plan.md",
            "docs/evaluation-spec.md",
            "docs/implementation-plan.md",
            "docs/test-plan.md",
        )
        for stage, name in SKILLS.items():
            root = REPO / "skills" / name
            for relative in required:
                with self.subTest(stage=stage, path=relative):
                    self.assertTrue((root / relative).is_file())

    def test_each_skill_has_ten_unique_research_urls(self) -> None:
        for stage, name in SKILLS.items():
            source_file = REPO / "skills" / name / "references" / "sources.md"
            text = source_file.read_text(encoding="utf-8")
            urls = {url.rstrip(".,;") for url in URL.findall(text)}
            with self.subTest(stage=stage):
                self.assertGreaterEqual(len(urls), 10, sorted(urls))
                self.assertRegex(text, r"20\d\d(?:-|年|/)\d{1,2}(?:-|月|/)\d{1,2}日?")

    def test_eval_cases_are_fixed_and_scored(self) -> None:
        for stage, name in SKILLS.items():
            case_root = REPO / "skills" / name / "evals" / "cases"
            for suffix in ("P01", "N01", "B01"):
                path = case_root / f"{stage}-{suffix}.md"
                with self.subTest(stage=stage, case=suffix):
                    self.assertTrue(path.is_file(), path)
                    text = path.read_text(encoding="utf-8")
                    for section in CASE_SECTIONS:
                        self.assertIn(section, text)
                    self.assertRegex(text, r"(?:2/2|equal\s+2|等于\s*2)")

    def test_skill_metadata_matches_directory(self) -> None:
        for stage, name in SKILLS.items():
            path = REPO / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            with self.subTest(stage=stage):
                self.assertTrue(text.startswith("---\n"))
                self.assertIn(f"\nname: {name}\n", text)
                self.assertRegex(text, r"\ndescription:\s*\S")
                self.assertLessEqual(len(text.splitlines()), 500)

    def test_no_visible_mojibake_or_extraneous_root_docs(self) -> None:
        for stage, name in SKILLS.items():
            root = REPO / "skills" / name
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".py"}:
                    with self.subTest(stage=stage, path=path.name):
                        self.assertIsNone(MOJIBAKE.search(path.read_text(encoding="utf-8")))
            for forbidden in ("README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md"):
                self.assertFalse((root / forbidden).exists())


if __name__ == "__main__":
    unittest.main()
