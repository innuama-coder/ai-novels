from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


SKILL=Path(__file__).resolve().parents[1];REPO=SKILL.parents[1];HARNESS=REPO/"harnesses/novel-hld-autonomous";sys.path[:0]=[str(HARNESS),str(REPO)]
from runtime import hq2_stage_runtime,owner_registry  # noqa:E402
from runtime.hq2_stage_runtime import implementation_sha256  # noqa:E402
from runtime.schema_catalog import SchemaCatalog  # noqa:E402
from runtime.canonical import ContractError  # noqa:E402


class ContractAssetTests(unittest.TestCase):
    def test_lifecycle_docs_and_cases_exist(self):
        for name in ("design-brief.md","file-plan.md","evaluation-spec.md","implementation-plan.md","test-plan.md"):
            self.assertTrue((SKILL/"docs"/name).is_file(),name)
        for case in ("HQ2-P01.md","HQ2-N01.md","HQ2-B01.md"):
            self.assertTrue((SKILL/"evals/cases"/case).is_file(),case)

    def test_sources_are_independent_and_at_least_ten(self):
        text=(SKILL/"references/sources.md").read_text(encoding="utf-8");urls=re.findall(r"https://[^)]+",text)
        self.assertGreaterEqual(len(set(urls)),10);self.assertRegex(text,r"(?:访问|复核)日期：2026-08-06")

    def test_runtime_contract_freezes_two_exact_composite_modes(self):
        contract=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["result_scope"],"composite_internal");self.assertEqual(contract["task_kinds"],["consumer_test","fidelity_test"])
        self.assertEqual(contract["modes"]["consumer_test"]["required_roles"],["hb0_completion","hb0_work_order","hp1_completion","hp1_manifest","hp1_work_order","lld_handoff","lld_handoff_schema"])
        self.assertNotIn("novel_hld_package",contract["modes"]["consumer_test"]["required_roles"])
        for mode in contract["modes"].values():self.assertEqual(5,len(mode["ready_profile"]));self.assertIn("package-manifest.json",mode["ready_profile"])
        self.assertEqual(contract["publisher_owner"],"harness-core/composite-stage-publisher")

    def test_public_owner_digest_is_the_declared_closed_implementation(self):
        for kind in ("consumer_test","fidelity_test"):
            skill,version,digest=owner_registry.resolve_public_owner("HQ2",kind)
            self.assertEqual(("novel-hld-lld-readiness-evaluator","1.0.0",implementation_sha256()),(skill,version,digest))

    def test_closed_schema_rejects_extra_property_and_duplicate_member(self):
        contract=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"));catalog=hq2_stage_runtime._schema_catalog(SKILL)
        extra={**contract,"unexpected":True}
        with self.assertRaises(ContractError):catalog.validate(extra,"hq2-runtime-contract.schema.json")
        duplicate=json.loads(json.dumps(contract));duplicate["implementation_closure"]["ordered_files"].append(duplicate["implementation_closure"]["ordered_files"][0])
        with self.assertRaises(ContractError):catalog.validate(duplicate,"hq2-runtime-contract.schema.json")

    def test_closure_reorder_escape_missing_duplicate_and_content_drift(self):
        contract=json.loads((SKILL/"references/runtime-contract.json").read_text(encoding="utf-8"));ordered=contract["implementation_closure"]["ordered_files"]
        registry=json.loads((HARNESS/"references/public-runtime-registry.json").read_text(encoding="utf-8"))["entries"]["consumer_test"]
        self.assertEqual(registry["closure_paths_sha256"],owner_registry._closure_paths_hash(ordered));self.assertNotEqual(registry["closure_paths_sha256"],owner_registry._closure_paths_hash(list(reversed(ordered))))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"a").write_text("one",encoding="utf-8");(root/"b").write_text("two",encoding="utf-8")
            paths=owner_registry._resolve_closure_paths(root,["a","b"]);before=owner_registry._closure_content_digest(root,paths);(root/"b").write_text("changed",encoding="utf-8");after=owner_registry._closure_content_digest(root,paths);self.assertNotEqual(before,after)
            with self.assertRaises(owner_registry.RuntimeRegistryError):owner_registry._resolve_closure_paths(root,["a","a"])
            with self.assertRaises(owner_registry.RuntimeRegistryError):owner_registry._resolve_closure_paths(root,["../escape"])
            with self.assertRaises(owner_registry.RuntimeRegistryError):owner_registry._resolve_closure_paths(root,["missing"])

    def test_public_entrypoint_is_thin_and_has_no_publisher(self):
        runtime=(SKILL/"scripts/run_skill.py").read_text(encoding="utf-8")
        self.assertNotIn("lld-handoff-acceptance.json",runtime);self.assertNotIn("stage-completion.json",runtime);self.assertIn("hq2_stage_runtime",runtime)


if __name__=="__main__":unittest.main()
