"""Run the shared real-public-contract fixture against HS1."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SUPPORT_PATH = REPO / "skills" / "novel-hld-narrative-architect" / "tests" / "test_skill.py"
spec = importlib.util.spec_from_file_location("hld_public_fixture_hs1", SUPPORT_PATH)
assert spec and spec.loader
support = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = support
spec.loader.exec_module(support)
support.SKILL = SKILL
support.CONTRACT = json.loads((SKILL / "references" / "runtime-contract.json").read_text(encoding="utf-8"))
support.RUNTIME = SKILL / "scripts" / "run_skill.py"

runtime_spec = importlib.util.spec_from_file_location("hld_hs1_runtime_under_test", support.RUNTIME)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
sys.modules[runtime_spec.name] = runtime
runtime_spec.loader.exec_module(runtime)


class PublicHarnessCompatibilityTests(support.PublicHarnessCompatibilityTests):
    def model(self) -> dict:
        return support.stage_model("HS1", {"role":"input_gate","path":"gate.json","sha256":"a"*64}, [])

    def test_chapter_design_exactly_covers_segment_shells(self):
        model=self.model();runtime.validate_stage_model(model,{})
        model["chapter_storyline_plan"]=[]
        with self.assertRaisesRegex(runtime.CandidateError,"chapter designs must exactly cover"):
            runtime.validate_stage_model(model,{})

    def test_chapter_cannot_assign_same_storyline_to_two_roles(self):
        model=self.model();model["chapter_storyline_plan"][0]["supporting_storyline_ids"]=["SL-MAIN-001"]
        with self.assertRaisesRegex(runtime.CandidateError,"multiple roles"):
            runtime.validate_stage_model(model,{})

    def test_chapter_storyline_role_must_match_disposition(self):
        model=self.model();model["chapter_storyline_plan"][0]["primary_storyline_id"]="SL-UNKNOWN"
        with self.assertRaisesRegex(runtime.CandidateError,"invalid primary_storyline_id"):
            runtime.validate_stage_model(model,{})
