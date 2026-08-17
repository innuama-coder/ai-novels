from __future__ import annotations

import copy
import importlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)
h1 = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_completion"
)
fixtures = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_production_orchestrator"
)


class H1CompletionReadabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.ProductionOrchestratorTests(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.tearDown()

    def test_readability_review_is_sealed_in_package_and_public_replay(self):
        context = self.fixture._context()
        for revision, stage in enumerate(
            ("B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"), 1
        ):
            _, order = prod.issue_stage_work(context, action=stage, inputs={})
            _, context = prod.execute_stage_work(
                context,
                work_order=order,
                actor=prod.ACTION_CONTRACT[stage][1],
                executor=self.fixture._fake_executor(stage, revision),
            )
        roots = {
            key: self.root / "upstream" / key
            for key in ("p1", "plan", "fragment", "assembly", "html")
        }
        for key, root in roots.items():
            root.mkdir(parents=True)
            (root / "package-manifest.json").write_text(
                rt.canonical_json({"key": key}), encoding="utf-8", newline=""
            )
        gate = context.coordinator.build_input_gate(
            "H1", "orchestration/input-gates/readability/input-gate.json"
        )
        rendered = rt.seal_document(
            {
                "schema_version": "2.0",
                "run_id": "RUN-PROD-1",
                "stage": "H1",
                "session_id": "H1-READABILITY-PACKAGE",
                "state": "rendered",
                "p1_completion": context.state.data["current_stage_completions"]["P1"],
                "previous_state_sha256": "a" * 64,
                "artifacts": {
                    "plan_manifest": {"path": "H1/plan/package-manifest.json", "sha256": "1" * 64},
                    "fragment_manifest": {"path": "H1/fragments/package-manifest.json", "sha256": "2" * 64},
                    "assembly_manifest": {"path": "H1/assembly/package-manifest.json", "sha256": "3" * 64},
                    "html_manifest": {"path": "H1/html/package-manifest.json", "sha256": "4" * 64},
                },
            },
            "H1/H1-READABILITY-PACKAGE/workspace-rendered.json",
        )
        review = rt.seal_document(
            {"review_id": "H1-READABILITY-PACKAGE-PASS", "verdict": "pass"},
            "reviews/h1-human-readability/H1-READABILITY-PACKAGE-PASS.json",
        )
        upstream = {
            "roots": roots,
            "manifests": {key: {"key": key} for key in roots},
            "run_id": "RUN-PROD-1",
            "session_id": rendered.data["session_id"],
            "workspace_artifacts": copy.deepcopy(rendered.data["artifacts"]),
            "inventory": {
                key: h1._tree_inventory(root) for key, root in roots.items()
            },
        }
        destination = self.root / "H1" / "stage"
        arguments = {
            "p1_package": roots["p1"],
            "plan_package": roots["plan"],
            "plan_input_gate": gate,
            "plan_workspace_state": rendered,
            "fragment_package": roots["fragment"],
            "fragment_workspace_state": rendered,
            "assembly_package": roots["assembly"],
            "assembly_workspace_state": rendered,
            "html_package": roots["html"],
            "rendered_workspace": rendered,
            "coordinator": context.coordinator,
            "next_state_path": "state/revision-009.json",
            "human_readability_review": review,
            "runtime": context.store.runtime,
        }
        with mock.patch.object(h1, "_validate_upstream", return_value=upstream):
            receipt = h1.publish_h1_completion(destination, **arguments)
            validation = h1.validate_h1_completion_package(
                destination,
                **{
                    key: value
                    for key, value in arguments.items()
                    if key not in {"coordinator", "next_state_path"}
                },
            )
            public_validation = h1.validate_h1_completion_package(
                destination,
                **{
                    key: value
                    for key, value in arguments.items()
                    if key not in {
                        "coordinator", "next_state_path",
                        "human_readability_review",
                    }
                },
            )
            replay = h1.publish_h1_completion(destination, **arguments)
        self.assertEqual("ready", validation["verdict"])
        self.assertEqual("ready", public_validation["verdict"])
        self.assertFalse(receipt.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(
            rt.canonical_json(review.data),
            (destination / "sources/human-readability-review.json").read_text(
                encoding="utf-8"
            ),
        )
        for name in ("missing-file", "wrong-ref", "wrong-hash", "extra-role"):
            mutant = self.root / f"mutant-{name}"
            shutil.copytree(destination, mutant)
            if name == "missing-file":
                (mutant / "sources/human-readability-review.json").unlink()
            elif name == "wrong-ref":
                execution = json.loads(
                    (mutant / "execution-record.json").read_text(encoding="utf-8")
                )
                execution["human_readability_review"]["path"] = "reviews/foreign.json"
                (mutant / "execution-record.json").write_text(
                    rt.canonical_json(execution), encoding="utf-8", newline=""
                )
            elif name == "wrong-hash":
                (mutant / "sources/human-readability-review.json").write_text(
                    "{}", encoding="utf-8", newline=""
                )
            else:
                changed_manifest = json.loads(
                    (mutant / "package-manifest.json").read_text(encoding="utf-8")
                )
                changed_manifest["artifact_roles"]["human_readability_review"] = (
                    next(
                        item for item in changed_manifest["files"]
                        if item["path"] == "sources/human-readability-review.json"
                    )
                )
                (mutant / "package-manifest.json").write_text(
                    rt.canonical_json(changed_manifest), encoding="utf-8", newline=""
                )
            with (
                mock.patch.object(h1, "_validate_upstream", return_value=upstream),
                self.assertRaises(Exception),
            ):
                h1.validate_h1_completion_package(
                    mutant,
                    **{
                        key: value
                        for key, value in arguments.items()
                        if key not in {
                            "coordinator", "next_state_path",
                            "human_readability_review",
                        }
                    },
                )
        manifest = json.loads(
            (destination / "package-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "sources/human-readability-review.json",
            next(
                item["path"] for item in manifest["files"]
                if item["path"] == "sources/human-readability-review.json"
            ),
        )


if __name__ == "__main__":
    unittest.main()
