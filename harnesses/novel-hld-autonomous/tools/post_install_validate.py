#!/usr/bin/env python3
"""Validate an unpacked Codex archive without access to its source repository."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

HARNESS_ROOT=Path(__file__).resolve().parents[1]
REPO=HARNESS_ROOT.parents[1]
sys.path.insert(0,str(REPO))


def main()->int:
    validator=importlib.import_module("harnesses.novel-hld-autonomous.validators.validate_harness")
    errors=validator.validate(HARNESS_ROOT,require_test_anchors=False)
    if errors:raise RuntimeError("unpacked harness validation failed: "+"; ".join(errors))
    registry=importlib.import_module("harnesses.novel-hld-autonomous.runtime.owner_registry")
    entries=json.loads(registry.REGISTRY_PATH.read_text(encoding="utf-8"))["entries"]
    ordinary={"HB0","HA1","HS1","HC1","HI1","HR1","HK1","HQ1","HP1","HF1"};resolved=[]
    for token in sorted(entries):
        entry=entries[token];skill,version,digest=registry.resolve_public_owner(entry["stage"],None if token in ordinary else token)
        if skill!=entry["skill"] or version!=entry["version"] or len(digest)!=64:raise RuntimeError(f"public runtime binding failed: {token}")
        resolved.append(token)
    skills={entry["skill"] for entry in entries.values() if not entry["skill"].startswith("harness-core/")}
    if len(resolved)!=17 or len(skills)!=14 or "novel-hld-writer" in skills:raise RuntimeError("unpacked registry topology is not exact")
    runtime_manifest=(HARNESS_ROOT/"MANIFEST.runtime.yaml").read_text(encoding="utf-8")
    operation=HARNESS_ROOT/"adapters/codex/operation.md"
    if not operation.is_file():raise RuntimeError("Codex operation contract is unavailable")
    if "status: release-candidate" in runtime_manifest and "agentic_qualification: qualified" in runtime_manifest:package_status="release-candidate";qualification="qualified"
    elif "status: implementation-candidate" in runtime_manifest and "agentic_qualification: not-run" in runtime_manifest:package_status="implementation-candidate";qualification="not-run"
    else:raise RuntimeError("runtime status and agentic qualification drift")
    smoke=REPO/"skills/novel-hld-narrative-architect/scripts/run_skill.py"
    invoked=subprocess.run([sys.executable,str(smoke),"--help"],cwd=REPO,text=True,capture_output=True,encoding="utf-8")
    if invoked.returncode!=0 or "usage:" not in invoked.stdout.lower():raise RuntimeError("unpacked HA1 public CLI cannot start")
    print(json.dumps({"status":"pass","package_status":package_status,"agentic_qualification":qualification,"operation_contract":"adapters/codex/operation.md","registry_tokens":len(resolved),"skills":len(skills),"skill_smoke":"novel-hld-narrative-architect","skill_cli_exit":invoked.returncode},sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
