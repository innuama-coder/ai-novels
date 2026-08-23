from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]


class ChapterDefinitionContractAssetsTests(unittest.TestCase):
    def test_public_contract_is_registered_and_schema_loads(self)->None:
        import sys
        harness=REPO/"harnesses/novel-hld-autonomous"
        sys.path.insert(0,str(harness))
        from runtime.design_stage_runtime import implementation_sha256,load_contract  # type: ignore[import-not-found]
        contract=load_contract(ROOT)
        self.assertEqual(contract["stage"],"HD1")
        self.assertEqual(contract["upstream_stages"],["HB0","HA1","HS1","HC1","HI1","HR1","HK1"])
        self.assertEqual(contract["canonical_file"],"chapter-definition-architecture.json")
        self.assertEqual(len(implementation_sha256(ROOT)),64)
        schema=json.loads((ROOT/"schemas/hd1-canonical.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["stage"]["const"],"HD1")
        required=set(schema["$defs"]["chapter"]["required"])
        self.assertTrue({"narrative_necessity","entry_state","dramatic_contract","memory_design","exit_state","lld_handoff"}.issubset(required))

    def test_complete_example_is_schema_valid(self)->None:
        import sys
        harness=REPO/"harnesses/novel-hld-autonomous"
        sys.path.insert(0,str(harness))
        from runtime.design_stage_runtime import _schema_catalog,load_contract  # type: ignore[import-not-found]
        support_path=ROOT/"tests/test_skill.py"
        spec=importlib.util.spec_from_file_location("hd1_complete_example",support_path)
        assert spec and spec.loader
        support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
        file_ref={"role":"input_gate","path":"input-gate.json","sha256":"0"*64}
        reads=[{"role":f"upstream::{stage}::main","path":f"{stage}.json","sha256":"0"*64} for stage in ("HB0","HA1","HS1","HC1","HI1","HR1","HK1")]
        catalog=_schema_catalog(ROOT,load_contract(ROOT))
        catalog.validate(support.stage_model("HD1",file_ref,reads),"hd1-canonical.schema.json")


if __name__=="__main__":unittest.main()
