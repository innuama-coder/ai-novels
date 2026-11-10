from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


HARNESS = Path(__file__).resolve().parents[1]
REPOSITORY = HARNESS.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dependencies = _load(
    "_test_dependency_validator", HARNESS / "validators" / "validate_dependencies.py"
)
release = _load("_test_release_builder", HARNESS / "tools" / "build_release.py")


class DependencyReleaseTests(unittest.TestCase):
    def test_source_has_exact_ten_stage_owners_and_public_apis(self) -> None:
        report = dependencies.validate_dependencies(HARNESS)
        self.assertTrue(report.ok, report.errors)
        spec = dependencies.load_dependency_spec(HARNESS)
        self.assertEqual(10, len(spec["stage_owners"]))
        self.assertEqual(
            {"S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1-A", "H1-B", "H1-C"},
            {item["stage"] for item in spec["stage_owners"]},
        )

    def test_repo_shaped_release_is_locked_and_excludes_legacy_skill(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dependency-release-") as temporary:
            output = Path(temporary) / "release"
            manifest = release.build_release(HARNESS, output)
            archive = output / manifest["artifacts"][1]["path"]
            extracted = Path(temporary) / "extracted"
            with zipfile.ZipFile(archive) as handle:
                handle.extractall(extracted)
            roots = [path for path in extracted.iterdir() if path.is_dir()]
            self.assertEqual(1, len(roots))
            bundle = roots[0]
            harness = bundle / "harnesses" / "novel-conception-autonomous"
            report = dependencies.validate_dependencies(harness, require_lock=True)
            self.assertTrue(report.ok, report.errors)
            skill_names = {
                path.parent.name for path in (bundle / "skills").glob("*/SKILL.md")
            }
            spec = dependencies.load_dependency_spec(harness)
            expected_skills = {
                item["skill"] for item in spec["stage_owners"]
            } | {
                item["skill"]
                for item in spec["quality_gate_dependencies"]
            }
            self.assertEqual(
                expected_skills,
                skill_names,
            )
            self.assertNotIn("novel-development-map-designer", skill_names)

    def test_lock_rejects_dependency_tampering(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dependency-lock-") as temporary:
            bundle = Path(temporary) / "bundle"
            harness = bundle / "harnesses" / "novel-conception-autonomous"
            release._copy_repository_dependencies(REPOSITORY, HARNESS, bundle)
            runtime = (
                bundle
                / "skills"
                / "novel-storyline-architecture-designer"
                / "scripts"
                / "run_v2.py"
            )
            runtime.write_bytes(runtime.read_bytes() + b"\n# tampered\n")
            report = dependencies.validate_dependencies(harness, require_lock=True)
            self.assertFalse(report.ok)
            self.assertIn("HARN_DEPENDENCY_LOCK_MISMATCH", report.errors)

    def test_missing_runtime_api_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dependency-api-") as temporary:
            bundle = Path(temporary) / "bundle"
            release._copy_repository_dependencies(REPOSITORY, HARNESS, bundle)
            harness = bundle / "harnesses" / "novel-conception-autonomous"
            spec_path = harness / "dependency-spec.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["stage_owners"][0]["apis"].append("missing_public_api")
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            (harness / "dependency-lock.json").unlink()
            report = dependencies.validate_dependencies(harness)
            self.assertFalse(report.ok)
            self.assertIn(
                "HARN_DEPENDENCY_API_MISSING:S1:missing_public_api", report.errors
            )


if __name__ == "__main__":
    unittest.main()
