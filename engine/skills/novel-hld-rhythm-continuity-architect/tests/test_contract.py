import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ContractAssets(unittest.TestCase):
    def test_runtime_contract_and_research(self):
        value=json.loads((ROOT/"references/runtime-contract.json").read_text(encoding="utf-8"));self.assertEqual("HR1",value["stage"]);self.assertEqual("1.0.0",value["runtime_version"]);self.assertEqual(["HB0","HA1","HS1","HC1","HI1"],value["upstream_stages"]);self.assertGreaterEqual(len(re.findall(r"https://",(ROOT/"references/sources.md").read_text(encoding="utf-8"))),10)
    def test_eval_gate_and_no_legacy_validator(self):
        self.assertFalse((ROOT/"scripts/validate_package.py").exists())
        for suffix in ("P01","N01","B01"):
            text=(ROOT/f"evals/cases/HR1-{suffix}.md").read_text(encoding="utf-8")
            for heading in ("## Prompt","## Expected Behavior","## Forbidden Behavior","## Scoring Rule","## Pass Bar"):self.assertIn(heading,text)
if __name__=="__main__":unittest.main()
