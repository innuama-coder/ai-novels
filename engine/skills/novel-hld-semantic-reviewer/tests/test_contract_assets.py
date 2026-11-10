from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


SKILL=Path(__file__).resolve().parents[1];REPO=SKILL.parents[1];sys.path.insert(0,str(REPO/"harnesses/novel-hld-autonomous"))
from runtime.design_stage_runtime import implementation_files, implementation_sha256  # noqa:E402
from runtime.schema_catalog import SchemaCatalog  # noqa:E402


class HQ1ContractAssetsTests(unittest.TestCase):
    def test_research_contains_ten_or_more_independent_sources(self):
        text=(SKILL/"references/sources.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(re.findall(r"^\|\s*\d+\s*\|",text,re.MULTILINE)),10)

    def test_eval_cases_have_frozen_sections(self):
        for path in sorted((SKILL/"evals/cases").glob("HQ1-*.md")):
            text=path.read_text(encoding="utf-8")
            for heading in ("## Prompt","## Expected Behavior","## Forbidden Behavior","## Scoring Rule","## Pass Bar"):
                self.assertIn(heading,text,path.name)

    def test_fixture_manifest_is_current_and_single_defect(self):
        manifest=json.loads((SKILL/"tests/fixtures/fixture-manifest.json").read_text(encoding="utf-8"));self.assertTrue(manifest["sealed_before_execution"])
        self.assertEqual(5,len(manifest["fixtures"]))
        for item in manifest["fixtures"]:
            path=SKILL/"tests/fixtures"/item["path"]
            self.assertEqual(item["sha256"],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(item["single_defect_injection"],json.loads(path.read_text(encoding="utf-8"))["single_defect_injection"])

    def test_closed_schema_catalog_and_implementation_hash_domain(self):
        contract=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"));catalog=SchemaCatalog.from_documents({**{p.name:json.loads(p.read_text(encoding="utf-8")) for p in (REPO/"harnesses/novel-hld-autonomous/schemas").glob("*.schema.json")},**{p.name:json.loads(p.read_text(encoding="utf-8")) for p in [SKILL/"schemas"/contract["canonical_schema"],*[REPO/path for path in contract["additional_schema_paths"]]]}})
        self.assertEqual({"path":"skills/novel-hld-semantic-reviewer/scripts/run_skill.py","runtime":"python","arguments":["work_order","draft_dir"]},contract["public_entrypoint"])
        self.assertEqual("sha256-basename-nul-content-nul-v1",contract["implementation_closure"]["algorithm"])
        self.assertIn("hq1-semantic-review.schema.json",catalog.schemas)
        files={path.resolve() for path in implementation_files(SKILL)}
        self.assertEqual([path.resolve() for path in implementation_files(SKILL)],[REPO/path for path in contract["implementation_closure"]["ordered_files"]])
        self.assertIn((REPO/"harnesses/novel-hld-autonomous/runtime/review_stage_runtime.py").resolve(),files)
        self.assertIn((SKILL/"schemas/hq1-semantic-review.schema.json").resolve(),files)
        for relative in contract["additional_schema_paths"]:self.assertIn((REPO/relative).resolve(),files)
        self.assertRegex(implementation_sha256(SKILL),r"^[0-9a-f]{64}$")

    def test_obsolete_standalone_validator_and_duplicate_schema_are_absent(self):
        self.assertFalse((SKILL/"scripts/validate_review.py").exists())
        self.assertFalse((SKILL/"references/hld-semantic-review.schema.json").exists())


if __name__=="__main__":unittest.main()
