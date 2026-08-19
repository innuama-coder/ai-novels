from __future__ import annotations
import json,re,unittest
from pathlib import Path
SKILL=Path(__file__).resolve().parents[1]
class ContractAssets(unittest.TestCase):
    def test_method_sources_and_utf8(self):
        text=(SKILL/"references/sources.md").read_text(encoding="utf-8");self.assertGreaterEqual(len(set(re.findall(r"https://[^)]+",text))),10);self.assertNotIn(chr(0xfffd),text)
    def test_closed_runtime_contract(self):
        value=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"));self.assertEqual(value["task_kinds"],["HH1-C"]);self.assertEqual(value["result_scope"],"composite_internal");self.assertEqual(value["public_entrypoint"]["path"],"skills/novel-hld-html-renderer/scripts/run_skill.py");self.assertNotIn("sample_chapter",value["required_roles"])
    def test_local_schemas_are_closed(self):
        for path in (SKILL/"references").glob("*.schema.json"):self.assertIs(json.loads(path.read_text(encoding="utf-8")).get("additionalProperties"),False,path.name)
if __name__=="__main__":unittest.main()
