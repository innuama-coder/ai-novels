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
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
readability = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.h1_readability"
)


class H1ReadabilityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="h1-readability-")
        self.root = Path(self.temporary.name)
        self.roots = {
            key: self.root / "H1" / key
            for key in ("plan", "fragments-attempt-02", "assembly", "html")
        }
        for root in self.roots.values():
            root.mkdir(parents=True)
        self._json(
            self.roots["plan"] / "generation-session.json",
            {"identity": {"task_id": "producer-plan", "thread_id": "thread-plan"}},
        )
        self._json(
            self.roots["fragments-attempt-02"] / "generation-session.json",
            {"identity": {"task_id": "producer-fragments", "thread_id": "thread-fragments"}},
        )
        self.fragment_texts = {"FRAG-01": "她在清晨醒来，只看到一行文字。"}
        self._json(
            self.roots["fragments-attempt-02"] / "fragment-package.json",
            {
                "fragments": [
                    {"id": fragment_id, "text": text}
                    for fragment_id, text in self.fragment_texts.items()
                ]
            },
        )
        (self.roots["assembly"] / "human-review-report.json").write_text(
            "人物在房间里说话。", encoding="utf-8", newline=""
        )
        (self.roots["html"] / "human-review-report.html").write_text(
            "<html lang=\"zh-CN\">人物在房间里说话。</html>",
            encoding="utf-8",
            newline="",
        )
        self.manifests = {
            "plan": self._package("plan", "h1-plan", {"generation_session": "generation-session.json"}),
            "fragment": self._package(
                "fragments-attempt-02",
                "h1-fragments",
                {
                    "generation_session": "generation-session.json",
                    "fragment_package": "fragment-package.json",
                },
            ),
            "assembly": self._package(
                "assembly", "h1-assembly", {"human_review_report_json": "human-review-report.json"}
            ),
            "html": self._package(
                "html", "h1-html", {"html": "human-review-report.html"}
            ),
        }
        workspace_data = {
            "schema_version": "2.0",
            "run_id": "RUN-READABILITY",
            "stage": "H1",
            "session_id": "H1-SESSION",
            "state": "rendered",
            "p1_completion": {"path": "P1/stage-completion.json", "sha256": "a" * 64},
            "previous_state_sha256": "b" * 64,
            "artifacts": {
                "plan_manifest": self._logical_manifest("plan", self.manifests["plan"]),
                "fragment_manifest": self._logical_manifest(
                    "fragments-attempt-02", self.manifests["fragment"]
                ),
                "assembly_manifest": self._logical_manifest("assembly", self.manifests["assembly"]),
                "html_manifest": self._logical_manifest("html", self.manifests["html"]),
            },
        }
        self.workspace = rt.seal_document(
            workspace_data, "H1/H1-SESSION/workspace-rendered.json"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _json(path: Path, value: dict) -> None:
        path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")

    def _package(self, key: str, profile: str, roles: dict[str, str]) -> dict:
        root = self.roots[key]
        self._json(root / "validation.json", {"verdict": "ready"})
        (root / "implementation").mkdir(exist_ok=True)
        (root / "implementation" / "runtime.py").write_text(
            "# sealed fixture\n", encoding="utf-8", newline=""
        )
        refs = {
            role: rt.artifact_reference(root / path, root=root)
            for role, path in roles.items()
        }
        validation = rt.artifact_reference(root / "validation.json", root=root)
        implementation = rt.artifact_reference(
            root / "implementation" / "runtime.py", root=root
        )
        manifest = {
            "package_profile": profile,
            "verdict": "ready",
            "files": sorted(
                [*refs.values(), validation, implementation],
                key=lambda item: item["path"],
            ),
            "artifact_roles": refs,
            "validation": validation,
            "implementation": [implementation],
        }
        self._json(root / "package-manifest.json", manifest)
        return manifest

    def _logical_manifest(self, key: str, manifest: dict) -> dict[str, str]:
        path = self.roots[key] / "package-manifest.json"
        return {"path": f"H1/{key}/package-manifest.json", "sha256": rt.sha256_file(path)}

    def _review(self, inputs: dict, *, verdict: str = "pass") -> dict:
        dimensions = [
            {"id": name, "verdict": verdict, "finding": "evidence reviewed"}
            for name in readability.DIMENSIONS
        ]
        findings = []
        if verdict == "fail":
            findings = [{
                "finding_id": "H1-READABILITY-FINDING-001",
                "dimension": "scene_not_spec",
                "artifact_kind": "fragment",
                "artifact_id": "FRAG-01",
                "evidence": "一行文字",
                "explanation": "reads as an implementation specification",
            }]
            dimensions[3]["verdict"] = "fail"
        return {
            "schema_version": "1.0",
            "review_id": "H1-READABILITY-001",
            "run_id": "RUN-READABILITY",
            "session_id": "H1-SESSION",
            "phase": "prepublish" if verdict == "pass" else "postpublish_failure",
            "reviewer": {
                "task_id": "independent-reviewer",
                "thread_id": "independent-thread",
                "independence_basis": "separate-task-no-producer-context",
            },
            "inputs": copy.deepcopy(inputs),
            "dimensions": dimensions,
            "findings": findings,
            "verdict": verdict,
        }

    def test_exact_pass_and_failure_evidence(self) -> None:
        inputs, identities = readability.prepublish_contract(
            plan_package=self.roots["plan"],
            fragment_package_root=self.roots["fragments-attempt-02"],
            assembly_package=self.roots["assembly"],
            html_package=self.roots["html"],
            rendered_workspace=self.workspace,
        )
        self.assertEqual(
            hashlib.sha256(self.fragment_texts["FRAG-01"].encode()).hexdigest(),
            inputs["fragments"][0]["text_sha256"],
        )
        readability.validate_review(
            self._review(inputs),
            expected_run_id="RUN-READABILITY",
            expected_session_id="H1-SESSION",
            expected_phase="prepublish",
            inputs=inputs,
            producer_identities=identities,
            expected_verdict="pass",
        )
        failure_inputs = copy.deepcopy(inputs)
        failure_inputs["h1_completion"] = {
            "stage": "H1",
            "path": "H1/stage/stage-completion.json",
            "sha256": "c" * 64,
        }
        failure_inputs["h1_manifest"] = {"path": "H1/stage/package-manifest.json", "sha256": "d" * 64}
        failure = self._review(failure_inputs, verdict="fail")
        readability.validate_review(
            failure,
            expected_run_id="RUN-READABILITY",
            expected_session_id="H1-SESSION",
            expected_phase="postpublish_failure",
            inputs=failure_inputs,
            producer_identities=identities,
            expected_verdict="fail",
        )
        readability.validate_failure_evidence(
            failure,
            report_text="人物在房间里说话。",
            fragment_texts=self.fragment_texts,
        )
        for mutation in (
            {**failure_inputs["h1_completion"], "stage": "P1"},
            {**failure_inputs["h1_completion"], "extra": True},
        ):
            changed = copy.deepcopy(failure)
            changed["inputs"]["h1_completion"] = mutation
            with self.assertRaisesRegex(
                readability.H1ReadabilityError, "SCHEMA_INVALID"
            ):
                readability.seal_review(changed)

    def test_independence_and_stale_binding_rejected(self) -> None:
        inputs, identities = readability.prepublish_contract(
            plan_package=self.roots["plan"],
            fragment_package_root=self.roots["fragments-attempt-02"],
            assembly_package=self.roots["assembly"],
            html_package=self.roots["html"],
            rendered_workspace=self.workspace,
        )
        review = self._review(inputs)
        review["reviewer"]["task_id"] = "producer-plan"
        with self.assertRaisesRegex(readability.H1ReadabilityError, "NOT_INDEPENDENT"):
            readability.validate_review(
                review,
                expected_run_id="RUN-READABILITY",
                expected_session_id="H1-SESSION",
                expected_phase="prepublish",
                inputs=inputs,
                producer_identities=identities,
                expected_verdict="pass",
            )
        stale = copy.deepcopy(inputs)
        stale["report"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(readability.H1ReadabilityError, "STALE"):
            readability.validate_review(
                self._review(stale),
                expected_run_id="RUN-READABILITY",
                expected_session_id="H1-SESSION",
                expected_phase="prepublish",
                inputs=inputs,
                producer_identities=identities,
                expected_verdict="pass",
            )


if __name__ == "__main__":
    unittest.main()
