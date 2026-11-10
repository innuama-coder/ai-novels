from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

from runtime import owner_registry  # noqa: E402


class HF1RuntimeClosureTests(unittest.TestCase):
    def _isolated_repo(self, destination: Path) -> dict[str, object]:
        registry = json.loads((ROOT / "references/public-runtime-registry.json").read_text(encoding="utf-8"))
        entry = registry["entries"]["HF1"]
        contract = json.loads((REPO / entry["contract_path"]).read_text(encoding="utf-8"))
        required = set(contract["implementation_closure"]["ordered_files"]) | {entry["contract_schema"], entry["contract_path"]}
        for relative in required:
            source = REPO / relative; target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        return entry

    def test_hf1_digest_changes_when_a_local_schema_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw); entry = self._isolated_repo(repo)
            with patch.object(owner_registry, "REPO", repo):
                before = owner_registry._closed_contract_digest(entry, "HF1")[2]
                schema = repo / "skills/novel-hld-finalizer/references/author-decision.schema.json"
                schema.write_bytes(schema.read_bytes() + b"\n")
                after = owner_registry._closed_contract_digest(entry, "HF1")[2]
            self.assertNotEqual(before, after)

    def test_hf1_contract_path_set_is_registry_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw); entry = self._isolated_repo(repo)
            contract_path = repo / str(entry["contract_path"])
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["implementation_closure"]["ordered_files"].pop()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with patch.object(owner_registry, "REPO", repo):
                with self.assertRaisesRegex(owner_registry.RuntimeRegistryError, "contract schema|order/path set"):
                    owner_registry._closed_contract_digest(entry, "HF1")


if __name__ == "__main__": unittest.main()
