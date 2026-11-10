from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
PYTHON=Path(sys.executable)


class ReleaseContractTests(unittest.TestCase):
    def test_bounded_acceptance_files_are_structural_only(self):
        registry=json.loads((ROOT/"references/public-runtime-registry.json").read_text(encoding="utf-8"))["entries"]
        skills={entry["skill"] for entry in registry.values() if not entry["skill"].startswith("harness-core/")}
        anchors=[]
        for skill in skills:
            path=REPO/"skills"/skill/"tests"/"acceptance-evidence.json"
            if not path.is_file():continue
            value=json.loads(path.read_text(encoding="utf-8"));anchors.append(path)
            self.assertEqual(value["evidence_class"],"structural-fixture-anchor")
            self.assertEqual(value["agentic_qualification"],"not-run")
            self.assertIs(value["qualification_credit"],False)
            self.assertEqual(value["reviewer_role"],"implementation-test-author")
            self.assertNotIn("verdict",value);self.assertNotIn("reviewer",value)
        self.assertEqual(len(anchors),11)

    def test_implementation_candidate_does_not_overclaim_agentic_evidence(self):
        manifest=(ROOT/"manifest.yaml").read_text(encoding="utf-8");checklist=(ROOT/"docs/release-checklist.md").read_text(encoding="utf-8");evidence=json.loads((ROOT/"releases/0.1.0-acceptance.json").read_text(encoding="utf-8"));registry=json.loads((ROOT/"references/public-runtime-registry.json").read_text(encoding="utf-8"))["entries"]
        self.assertIn("status: implementation-candidate",manifest);self.assertEqual(checklist.count("- [ ]"),4);self.assertFalse(evidence["stable_major"]);self.assertEqual((evidence["registered_skill_count"],evidence["registry_token_count"]),(15,18));self.assertEqual(len({x["skill"] for x in registry.values() if not x["skill"].startswith("harness-core/")}),15)
        self.assertEqual(evidence["agentic_qualification"],"not-run");self.assertEqual(evidence["hld_e2e_fixture_status"],"declaration-only");self.assertEqual(evidence["bounded_agentic_case_count"],42)
        for fixture in (ROOT/"evals/fixtures").glob("HLD-E2E-*.json"):
            value=json.loads(fixture.read_text(encoding="utf-8"));self.assertFalse(value["sealed_before_execution"]);self.assertEqual(value["qualification_status"],"pending-agent-execution")

    def test_codex_archive_is_self_contained_and_passes_empty_directory_install(self):
        with tempfile.TemporaryDirectory() as raw:
            output=Path(raw)/"dist";completed=subprocess.run([str(PYTHON),str(ROOT/"tools/build_release.py"),"--output",str(output)],cwd=REPO,text=True,capture_output=True,encoding="utf-8");self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
            release=json.loads((output/"release-manifest.json").read_text(encoding="utf-8"));self.assertTrue((output/"release-manifest.yaml").is_file());self.assertEqual((release["status"],release["agentic_qualification"]),("implementation-candidate","not-run"));archive=output/next(item["path"] for item in release["artifacts"] if item["target"]=="codex");expected=next(item for item in release["artifacts"] if item["target"]=="codex");self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),expected["sha256"])
            with zipfile.ZipFile(archive) as package:
                names=package.namelist();self.assertIsNone(package.testzip());self.assertEqual(len(names),len(set(names)));self.assertFalse(any("/skills/novel-hld-writer/" in name for name in names));self.assertEqual(len({name.split("/skills/",1)[1].split("/",1)[0] for name in names if "/skills/novel-hld-" in name}),15)
                target=Path(raw)/"empty";package.extractall(target)
            bundle=next(target.iterdir());validator=bundle/"harnesses/novel-hld-autonomous/tools/post_install_validate.py";installed=subprocess.run([str(PYTHON),str(validator)],cwd=bundle,text=True,capture_output=True,encoding="utf-8");self.assertEqual(installed.returncode,0,installed.stdout+installed.stderr);post=json.loads(installed.stdout);self.assertEqual((post["registry_tokens"],post["skill_smoke"],post["skill_cli_exit"]),(18,"novel-hld-narrative-architect",0));self.assertEqual((post["package_status"],post["agentic_qualification"]),("implementation-candidate","not-run"))

    def test_public_coordinator_cli_can_resolve_repository_skill_modules(self):
        completed=subprocess.run([str(PYTHON),str(ROOT/"runtime/run_coordinator.py"),"--help"],cwd=REPO,text=True,capture_output=True,encoding="utf-8")
        self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
        self.assertIn("init-staged",completed.stdout)
        source=(ROOT/"runtime/run_coordinator.py").read_text(encoding="utf-8")
        self.assertIn("REPO=ROOT.parents[1]",source)
        self.assertIn("sys.path.insert(0,str(REPO))",source)


if __name__=="__main__":unittest.main()
