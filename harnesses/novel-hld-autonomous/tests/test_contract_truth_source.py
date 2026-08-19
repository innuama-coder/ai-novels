from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(ROOT))


class ContractTruthSourceTests(unittest.TestCase):
    def test_five_step_reasoning_and_work_requirement_identity_do_not_drift(self):
        identity=json.loads((ROOT/"references/hld-identity-contract.json").read_text(encoding="utf-8"))
        from runtime.design_stage_runtime import EVIDENCE_ORDER
        from runtime.contracts import ID_OWNER_PREFIX
        self.assertEqual(tuple(identity["design_evidence_files"]),EVIDENCE_ORDER)
        work=identity["work_requirement"]
        self.assertEqual((ID_OWNER_PREFIX["LWR"],ID_OWNER_PREFIX["LWK"]),("HK1","HP1"))
        self.assertEqual((work["producer_prefix"],work["downstream_prefix"],work["source_field"]),("LWR-","LWK-","source_lwr_id"))
        design=(REPO/"docs/ai-novel-workflow/hld-autonomous-workflow-v1-design.md").read_text(encoding="utf-8")
        catalog=(REPO/"docs/ai-novel-workflow/hld-skill-contract-catalog-v1.md").read_text(encoding="utf-8")
        for document in (design,catalog):
            positions=[document.index(name) for name in ("dependency-assessment","obligation-analysis","option-analysis","projection-analysis","adversarial-self-review")]
            self.assertEqual(positions,sorted(positions))
        hk1=catalog[catalog.index("## 9. HK1"):catalog.index("## 10. HQ1")]
        self.assertIn("`LWR-`",hk1);self.assertNotIn("每个 `LWK-`",hk1)
        hk1_skill=(REPO/"skills/novel-hld-key-scene-function-planner/SKILL.md").read_text(encoding="utf-8")
        hp1_skill=(REPO/"skills/novel-hld-package-assembler/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("LWR-",hk1_skill);self.assertIn("source_lwr_id",hp1_skill);self.assertIn("LWK-",hp1_skill)


if __name__=="__main__":unittest.main()
