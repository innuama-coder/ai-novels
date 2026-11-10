from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import unittest
from pathlib import Path


p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)
legacy = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.tests.test_v2_runtime"
)


class GateAuthoritativeP1RootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = legacy.P1RuntimeTests(methodName="runTest")
        self.fixture.setUp()

    def tearDown(self) -> None:
        self.fixture.doCleanups()
        self.fixture.tearDown()

    def _attempt_qualified(self):
        roots, refs = self.fixture._packages()
        for stage in p1.STAGES:
            completion_path = roots[stage] / "stage-completion.json"
            completion = self.fixture._read(completion_path)
            logical_root = f"{stage}/attempt-current"
            completion["manifest"]["path"] = f"{logical_root}/package-manifest.json"
            completion["validation"]["path"] = f"{logical_root}/validation.json"
            self.fixture._write(completion_path, completion)
            refs[stage]["path"] = f"{logical_root}/stage-completion.json"
            refs[stage]["sha256"] = p1.rt.sha256_file(completion_path)
        q1_gate = self.fixture._read(roots["Q1"] / "input-gate.json")
        q1_gate["upstream_completions"] = [
            refs[stage] for stage in ("S1", "W1", "E1", "T1", "C1")
        ]
        self.fixture._write(roots["Q1"] / "input-gate.json", q1_gate)
        self.fixture._refresh_input_manifest(roots["Q1"])
        return roots, refs

    def test_attempt_qualified_extended_context_and_public_replay(self):
        roots, refs = self._attempt_qualified()
        if p1.os.name == "nt":
            roots = {
                stage: Path("\\\\?\\" + str(root.resolve()))
                for stage, root in roots.items()
            }
        models, _, completions = p1._context(
            roots, input_gate=self.fixture._gate(refs), runtime=self.fixture.runtime,
            full_validation=False,
        )
        self.assertEqual(set(models), set(p1.STAGES))
        self.assertEqual({item["stage"] for item in completions.values()}, set(p1.STAGES))
        receipt, _ = self.fixture._run(roots, self.fixture._gate(refs))
        self.assertEqual(
            self.fixture._validate(receipt.package_root)["verdict"], "ready"
        )

    def test_wrong_or_nested_sibling_fails(self):
        roots, refs = self._attempt_qualified()
        for bad in ("foreign/package-manifest.json", "W1/attempt-current/nested/package-manifest.json"):
            completion_path = roots["W1"] / "stage-completion.json"
            completion = self.fixture._read(completion_path)
            completion["manifest"]["path"] = bad
            self.fixture._write(completion_path, completion)
            refs["W1"]["sha256"] = p1.rt.sha256_file(completion_path)
            q1_gate = self.fixture._read(roots["Q1"] / "input-gate.json")
            q1_gate["upstream_completions"] = [
                refs[stage] for stage in ("S1", "W1", "E1", "T1", "C1")
            ]
            self.fixture._write(roots["Q1"] / "input-gate.json", q1_gate)
            self.fixture._refresh_input_manifest(roots["Q1"])
            with self.assertRaisesRegex(p1.P1Error, "P1_W1_COMPLETION_INVALID"):
                p1._context(
                    roots, input_gate=self.fixture._gate(refs),
                    runtime=self.fixture.runtime, full_validation=False,
                )
            completion["manifest"]["path"] = "W1/attempt-current/package-manifest.json"
            self.fixture._write(completion_path, completion)
            refs["W1"]["sha256"] = p1.rt.sha256_file(completion_path)
