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


class PublicHarnessCompatibilityTests(support.PublicHarnessCompatibilityTests):
    pass
