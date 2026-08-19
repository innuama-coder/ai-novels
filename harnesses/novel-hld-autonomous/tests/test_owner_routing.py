from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.contracts import invalidated_suffix, owner_for_id  # noqa: E402
from runtime.revision import build_revision_plan  # noqa: E402


class OwnerRoutingTests(unittest.TestCase):
    def test_hk1_lwr_and_hp1_lwk_have_distinct_owners(self) -> None:
        self.assertEqual(owner_for_id("LWR-001"), "HK1")
        self.assertEqual(owner_for_id("LWK-001"), "HP1")

    def test_revision_suffix_uses_canonical_lwr_owner(self) -> None:
        suffix = invalidated_suffix(owner_for_id("LWR-001"), "hld_content")
        self.assertEqual(suffix[0], "HK1")
        self.assertIn("HP1", suffix)
        self.assertIn("HF1", suffix)

    def test_report_element_cannot_own_semantic_author_change(self) -> None:
        target={"target_kind":"hld_content","affected_ids":["HRE-WORLD-001"],"requirements":["change the city network"],"source_target_refs":["/revision_targets/0"],"correction_condition":"canonical world authority updated","defect_origin":"author_request","violated_contract":"author-request","automatic":False}
        with self.assertRaisesRegex(ValueError,"canonical HLD owner"):
            build_revision_plan(hld_run_id="hld-fixture",source_result_ref={"role":"stage_result","path":"result.json","sha256":"a"*64},targets=[target])


if __name__ == "__main__":
    unittest.main()
