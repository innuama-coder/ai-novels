from __future__ import annotations

import copy
import importlib
import inspect
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


HARNESS_MODULE = (
    "harnesses.novel-conception-autonomous.runtime.harness"
)
VALIDATOR_MODULE = (
    "harnesses.novel-conception-autonomous.validators.validate_harness"
)
FIXTURE_MODULE = (
    "harnesses.novel-conception-autonomous.tests.fixtures.formal_rendered_h1"
)
HARNESS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = HARNESS_ROOT.parents[1]

EXPECTED_RUN_PARAMETERS = (
    "output_root",
    "coordinator",
    "stage_packages",
    "p1_package",
    "plan_package",
    "plan_input_gate",
    "plan_workspace_state",
    "fragment_package",
    "fragment_workspace_state",
    "assembly_package",
    "assembly_workspace_state",
    "html_package",
    "rendered_workspace",
    "author_event",
    "development_handoff",
    "next_state_paths",
    "runtime",
)


class FrozenHarnessApiTests(unittest.TestCase):
    def test_rendered_h1_runner_has_the_frozen_public_contract(self):
        harness = importlib.import_module(HARNESS_MODULE)
        signature = inspect.signature(harness.run_from_rendered_h1)

        self.assertEqual(
            EXPECTED_RUN_PARAMETERS,
            tuple(signature.parameters),
        )
        self.assertEqual(
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            signature.parameters["output_root"].kind,
        )
        for name in EXPECTED_RUN_PARAMETERS[1:]:
            self.assertEqual(
                inspect.Parameter.KEYWORD_ONLY,
                signature.parameters[name].kind,
                name,
            )
        self.assertIsNone(signature.parameters["runtime"].default)
        self.assertEqual(
            ("branch", "h1", "decision", "final", "state"),
            tuple(harness.HarnessRunReceipt.__dataclass_fields__),
        )

    def test_current_portable_harness_passes_its_public_validator(self):
        validator = importlib.import_module(VALIDATOR_MODULE)
        report = validator.validate_harness()

        self.assertTrue(report.ok, report.errors)
        self.assertEqual((), tuple(report.errors))
        self.assertGreater(len(report.checked), 0)
        self.assertEqual(
            ("ok", "errors", "checked"),
            tuple(validator.ValidationReport.__dataclass_fields__),
        )


class PortableValidatorAndReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = importlib.import_module(VALIDATOR_MODULE)
        cls.release = importlib.import_module(
            "harnesses.novel-conception-autonomous.tools.build_release"
        )
        cls.release_temporary = tempfile.TemporaryDirectory(
            dir=r"C:\tmp"
        )
        cls.release_root = Path(cls.release_temporary.name)
        cls.first_release = cls.release_root / "first"
        cls.second_release = cls.release_root / "second"
        cls.first_manifest = cls.release.build_release(
            HARNESS_ROOT, cls.first_release
        )
        cls.second_manifest = cls.release.build_release(
            HARNESS_ROOT, cls.second_release
        )

    @classmethod
    def tearDownClass(cls):
        cls.release_temporary.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=r"C:\tmp")
        self.bundle = Path(self.temporary.name) / "portable"
        self.release._copy_repository_dependencies(
            REPOSITORY_ROOT, HARNESS_ROOT, self.bundle
        )
        self.root = (
            self.bundle / "harnesses" / "novel-conception-autonomous"
        )

    def tearDown(self):
        self.temporary.cleanup()

    def _manifest(self):
        path = self.root / "manifest.yaml"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path, value):
        Path(path).write_text(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="",
        )

    def _assert_rejected(self, expected=None):
        report = self.validator.validate_harness(self.root)
        self.assertFalse(report.ok, report.checked)
        if expected is not None:
            self.assertTrue(
                any(
                    error == expected or error.startswith(expected)
                    for error in report.errors
                ),
                report.errors,
            )
        return report

    def test_validator_rejects_missing_required_skill_or_schema(self):
        (self.root / "adapters" / "codex" / "SKILL.md").unlink()
        self._assert_rejected(
            "HARN_FILE_MISSING:adapters/codex/SKILL.md"
        )

        self.release._copy_source(HARNESS_ROOT, self.root)
        schema = (
            self.root
            / "schemas"
            / "bundled"
            / "author-decision.schema.json"
        )
        schema.unlink()
        self._assert_rejected(
            "HARN_SCHEMA_MISSING:author-decision.schema.json"
        )

    def test_validator_rejects_stage_and_skill_order_drift(self):
        path, manifest = self._manifest()
        manifest["stages"][1], manifest["stages"][2] = (
            manifest["stages"][2],
            manifest["stages"][1],
        )
        self._write_json(path, manifest)
        self._assert_rejected("HARN_MANIFEST_STAGES_INVALID")

        self.release._copy_source(HARNESS_ROOT, self.root)
        skill = self.root / "adapters" / "codex" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace("1. 验证", "2. 验证", 1)
        text = text.replace("2. 新运行", "1. 新运行", 1)
        skill.write_text(text, encoding="utf-8", newline="")
        self._assert_rejected("HARN_ADAPTER_INVALID")

    def test_validator_rejects_legacy_entry_and_weakened_adapter_mapping(self):
        path, manifest = self._manifest()
        manifest["stages"].insert(-1, "D1")
        manifest["legacy_profiles_forbidden"] = ["R1"]
        self._write_json(path, manifest)
        report = self._assert_rejected()
        self.assertIn("HARN_LEGACY_POLICY_INVALID", report.errors)
        self.assertIn("HARN_MANIFEST_STAGES_INVALID", report.errors)

        self.release._copy_source(HARNESS_ROOT, self.root)
        adapter = self.root / "adapters" / "codex" / "SKILL.md"
        adapter.write_text(
            adapter.read_text(encoding="utf-8").replace(
                "runtime.production_orchestrator:initialize_production_run",
                "runtime.production_orchestrator:removed_entry",
            ),
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_ADAPTER_INVALID")

        self.release._copy_source(HARNESS_ROOT, self.root)
        mapping = self.root / "adapters" / "codex" / "mapping.md"
        mapping.write_text(
            "# Codex Mapping\n\nCodex may synthesize decisions and own state.\n",
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_ADAPTER_INVALID")

    def test_validator_rejects_eval_without_score_or_pass_bar(self):
        case = self.root / "evals" / "cases" / "approved.json"
        value = json.loads(case.read_text(encoding="utf-8"))
        value.pop("Scoring")
        value.pop("Pass Bar")
        self._write_json(case, value)
        self._assert_rejected(
            "HARN_EVAL_CONTRACT_INVALID:approved.json"
        )

    def test_validator_rejects_missing_production_recovery_api(self):
        runtime = self.root / "runtime" / "production_orchestrator.py"
        runtime.write_text(
            runtime.read_text(encoding="utf-8").replace(
                "def recover_h1_workspace(", "def removed_h1_workspace(", 1
            ),
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_PRODUCTION_API_INVALID")

    def test_validator_rejects_production_api_without_actor_guard(self):
        runtime = self.root / "runtime" / "production_orchestrator.py"
        runtime.write_text(
            runtime.read_text(encoding="utf-8").replace(
                "    actor: str,\n    executor:",
                "    caller: str,\n    executor:",
                1,
            ),
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_PRODUCTION_API_INVALID")

    def test_validator_rejects_stale_or_weakened_output_root_contract(self):
        input_contract = self.root / "docs" / "input-contract.md"
        text = input_contract.read_text(encoding="utf-8")
        input_contract.write_text(
            text.replace(
                '"allowed_shape": "H1/stage"',
                '"allowed_shape": "H1"',
                1,
            ),
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_OUTPUT_ROOT_CONTRACT_INVALID")

        self.release._copy_source(HARNESS_ROOT, self.root)
        rules = self.root / "rules.md"
        rules.write_text(
            rules.read_text(encoding="utf-8").replace(
                '"allowed_shape": "H1/stage"',
                '"allowed_shape": "H1"',
            ),
            encoding="utf-8",
            newline="",
        )
        self._assert_rejected("HARN_OUTPUT_ROOT_CONTRACT_INVALID")

    def test_codex_adapter_documents_have_no_mojibake_markers(self):
        forbidden = ("窶", "竊", "荳", "譫", "蜿", "\ufffd")
        for path in sorted(
            (self.root / "adapters" / "codex").glob("*.md")
        ):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertFalse(
                    any(marker in text for marker in forbidden),
                    f"mojibake marker in {path.name}",
                )

    def test_release_is_deterministic_and_both_archives_revalidate_in_tmp(self):
        self.assertEqual(
            self.first_manifest["artifacts"],
            self.second_manifest["artifacts"],
        )
        for artifact in self.first_manifest["artifacts"]:
            archive = self.first_release / artifact["path"]
            with tempfile.TemporaryDirectory(dir=r"C:\tmp") as directory:
                checked = self.release._extract_and_validate(
                    archive, Path(directory)
                )
            self.assertIn("runtime:public-api", checked)
            self.assertIn("adapter:codex-frontmatter", checked)

    def test_release_rejects_absolute_manifest_path(self):
        original = Path.is_absolute

        def force_artifact_absolute(path):
            if str(path) in {
                "novel-conception-autonomous-1.0.0-source.zip",
                "novel-conception-autonomous-1.0.0-codex.zip",
            }:
                return True
            return original(path)

        with mock.patch.object(
            Path, "is_absolute", new=force_artifact_absolute
        ), self.assertRaisesRegex(
            self.release.ReleaseBuildError,
            "HARN_RELEASE_MANIFEST_INVALID",
        ):
            self.release.build_release(
                HARNESS_ROOT, self.release_root / "absolute"
            )

    def test_release_rejects_zip_missing_required_entry(self):
        source = (
            self.first_release
            / "novel-conception-autonomous-1.0.0-source.zip"
        )
        damaged = self.root.parent / "missing-entry.zip"
        with zipfile.ZipFile(source, "r") as reader, zipfile.ZipFile(
            damaged, "w", compression=zipfile.ZIP_DEFLATED
        ) as writer:
            for item in reader.infolist():
                if item.filename.endswith("/agent.md"):
                    continue
                writer.writestr(item, reader.read(item.filename))
        with tempfile.TemporaryDirectory(dir=r"C:\tmp") as directory, (
            self.assertRaisesRegex(
                self.release.ReleaseBuildError,
                "HARN_RELEASE_VALIDATION_FAILED:HARN_FILE_MISSING:agent.md",
            )
        ):
            self.release._extract_and_validate(
                damaged, Path(directory)
            )

    def test_release_detects_hash_tampering_before_success(self):
        real_sha256 = self.release._sha256
        changed = {"done": False}

        def hash_then_tamper(path):
            digest = real_sha256(path)
            if (
                not changed["done"]
                and Path(path).name
                == "novel-conception-autonomous-1.0.0-source.zip"
            ):
                changed["done"] = True
                with Path(path).open("ab") as stream:
                    stream.write(b"TAMPER")
            return digest

        with mock.patch.object(
            self.release, "_sha256", side_effect=hash_then_tamper
        ), self.assertRaisesRegex(
            self.release.ReleaseBuildError,
            "HARN_RELEASE_CHECKSUM_MISMATCH",
        ):
            self.release.build_release(
                HARNESS_ROOT, self.release_root / "hash-tamper"
            )


class RealRenderedH1HarnessTests(unittest.TestCase):
    """Start at a real H1-A/B/assembly/C rendered package chain.

    Only the explicitly allowed P1 isolation boundary is replaced.  The
    replacement verifies the exact current package, manifest, completion, and
    real ContractRuntime.  No H1 validator is patched.
    """

    @classmethod
    def setUpClass(cls):
        cls.fixture_module = importlib.import_module(FIXTURE_MODULE)
        cls.fixture = (
            cls.fixture_module.build_current_rendered_h1_fixture()
        )
        cls.coordinator_module = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime.coordinator"
        )
        cls.h1_runtime = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime.h1_completion"
        )
        cls.canonical = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime.canonical"
        )
        cls.p1_runtime = importlib.import_module(
            "skills.novel-conception-deliverable-assembler.scripts.run_v2"
        )
        cls.h1c_runtime = importlib.import_module(
            "skills.novel-conception-review-html-generator.scripts.run_v2"
        )

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.subject = self._clone_coordinator()

    def tearDown(self):
        self.temporary.cleanup()

    def _clone_coordinator(self):
        return self.coordinator_module.AutonomousCoordinator.from_snapshot(
            self.fixture.coordinator.state,
            self.fixture.coordinator.state_reference,
            runtime=self.fixture.runtime,
        )

    def _accept_formal_p1_boundary(self, package_root, *, runtime):
        root = Path(package_root).resolve()
        if runtime is not self.fixture.runtime:
            raise AssertionError("P1 boundary did not receive real runtime")
        if root != self.fixture.p1_package.resolve():
            raise AssertionError("P1 boundary received non-current package")
        manifest = json.loads(
            (root / "package-manifest.json").read_text(encoding="utf-8")
        )
        runtime.validate(manifest, "package-manifest.schema.json")
        self.canonical.verify_manifest_integrity(manifest, root=root)
        completion = json.loads(
            (root / "stage-completion.json").read_text(encoding="utf-8")
        )
        runtime.validate(completion, "stage-completion.schema.json")
        expected = self.fixture.coordinator.state[
            "current_stage_completions"
        ]["P1"]
        actual = {
            "stage": "P1",
            "path": "P1/stage-completion.json",
            "sha256": self.canonical.sha256_file(
                root / "stage-completion.json"
            ),
        }
        if actual != expected:
            raise AssertionError("P1 completion is not current")
        return {"verdict": "ready"}

    def _h1_arguments(self, coordinator):
        return {
            "p1_package": self.fixture.p1_package,
            "plan_package": self.fixture.plan_package,
            "plan_input_gate": self.fixture.plan_input_gate,
            "plan_workspace_state": self.fixture.plan_workspace_state,
            "fragment_package": self.fixture.fragment_package,
            "fragment_workspace_state": (
                self.fixture.fragment_workspace_state
            ),
            "assembly_package": self.fixture.assembly_package,
            "assembly_workspace_state": (
                self.fixture.assembly_workspace_state
            ),
            "html_package": self.fixture.html_package,
            "rendered_workspace": self.fixture.rendered_workspace,
            "coordinator": coordinator,
            "runtime": self.fixture.runtime,
        }

    def _preview_h1(self, name):
        preview_coordinator = self._clone_coordinator()
        with mock.patch.object(
            self.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_formal_p1_boundary,
        ):
            return self.h1_runtime.publish_h1_completion(
                self.root / f"preview-{name}",
                next_state_path=f"state/preview-{name}-h1.json",
                **self._h1_arguments(preview_coordinator),
            )

    def _event(self, branch, *, targets=None):
        preview = self._preview_h1(branch)
        p1 = self.fixture.p1_package
        html = self.fixture.html_package
        body = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "approval_scope": "conception",
            "decision": branch,
            "machine_package": {
                "completion_path": "P1/stage-completion.json",
                "completion_sha256": self.canonical.sha256_file(
                    p1 / "stage-completion.json"
                ),
                "manifest_path": "P1/package-manifest.json",
                "manifest_sha256": self.canonical.sha256_file(
                    p1 / "package-manifest.json"
                ),
            },
            "human_review_package": {
                "completion_path": "H1/stage/stage-completion.json",
                "completion_sha256": self.canonical.sha256_file(
                    preview.package_root / "stage-completion.json"
                ),
                "manifest_path": "H1/stage/package-manifest.json",
                "manifest_sha256": self.canonical.sha256_file(
                    preview.package_root / "package-manifest.json"
                ),
                "html_path": "H1/html/human-review-report.html",
                "html_sha256": self.canonical.sha256_file(
                    html / "human-review-report.html"
                ),
            },
        }
        if branch == "approved":
            body["approval_record"] = {
                "event_seq": 1,
                "text": "approve the current conception",
            }
            body["unresolved_items"] = []
        elif branch == "rejected":
            body["rejection_record"] = {
                "event_seq": 2,
                "text": "reject the current conception",
            }
        else:
            body["revision_record"] = {
                "event_seq": 3,
                "text": "revise the selected current controls",
            }
            body["revision_targets"] = targets or [
                {
                    "target_scope": "conception",
                    "visible_element_ids": [],
                    "source_ids": ["INT-1"],
                    "requested_change": "revise the intent control",
                }
            ]
        return self.coordinator_module.seal_document(
            body, f"author/{branch}-decision.json"
        )

    def _paths(self, name):
        return {
            "h1": f"state/{name}-h1.json",
            "approved": f"state/{name}-approved.json",
            "revise": f"state/{name}-revise.json",
            "rejected": f"state/{name}-rejected.json",
            "final": f"state/{name}-final.json",
        }

    def _run(self, branch, *, event=None, name=None, **overrides):
        harness = importlib.import_module(HARNESS_MODULE)
        event = event or self._event(branch)
        arguments = {
            **self._h1_arguments(self.subject),
            "stage_packages": self.fixture.stage_packages,
            "author_event": event,
            "development_handoff": self.fixture.development_handoff,
            "next_state_paths": self._paths(name or branch),
        }
        arguments.update(overrides)
        with mock.patch.object(
            self.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_formal_p1_boundary,
        ):
            return harness.run_from_rendered_h1(
                self.root / f"run-{name or branch}",
                **arguments,
            )

    def test_approved_runs_real_h1_and_is_the_only_development_entry(self):
        receipt = self._run("approved")

        self.assertEqual("approved", receipt.branch)
        self.assertEqual("waiting_author", receipt.h1.transition.snapshot["status"])
        self.assertEqual("approved", receipt.decision.transition.snapshot["status"])
        self.assertIsNotNone(receipt.final)
        self.assertEqual("ready", receipt.state.data["development_status"])
        self.assertEqual(
            list(self.coordinator_module.STAGE_ORDER),
            list(receipt.final.completion.data["stage_completions"]),
        )

    def test_attempt_qualified_fragment_runs_real_h1c_to_h1a_validation(self):
        qualified = self.fixture_module.build_current_rendered_h1_fixture(
            fragment_logical_package_path="H1/fragments-attempt-02"
        )
        try:
            subject = self.coordinator_module.AutonomousCoordinator.from_snapshot(
                qualified.coordinator.state,
                qualified.coordinator.state_reference,
                runtime=qualified.runtime,
            )
            with mock.patch.object(
                self.p1_runtime,
                "validate_p1_package",
                return_value={"verdict": "ready"},
            ):
                receipt = self.h1_runtime.publish_h1_completion(
                    self.root / "attempt-qualified-h1-stage",
                    p1_package=qualified.p1_package,
                    plan_package=qualified.plan_package,
                    plan_input_gate=qualified.plan_input_gate,
                    plan_workspace_state=qualified.plan_workspace_state,
                    fragment_package=qualified.fragment_package,
                    fragment_workspace_state=qualified.fragment_workspace_state,
                    assembly_package=qualified.assembly_package,
                    assembly_workspace_state=qualified.assembly_workspace_state,
                    html_package=qualified.html_package,
                    rendered_workspace=qualified.rendered_workspace,
                    coordinator=subject,
                    next_state_path="state/attempt-qualified-h1.json",
                    runtime=qualified.runtime,
                )
            self.assertEqual("waiting_author", receipt.transition.snapshot["status"])
            self.assertEqual(
                "H1/fragments-attempt-02/package-manifest.json",
                qualified.rendered_workspace.data["artifacts"][
                    "fragment_manifest"
                ]["path"],
            )
        finally:
            qualified.close()

    def test_revise_creates_one_active_return_and_no_final_completion(self):
        receipt = self._run("revise")

        self.assertEqual("revise", receipt.branch)
        self.assertIsNone(receipt.final)
        self.assertEqual("revise", receipt.state.data["status"])
        self.assertIsNotNone(receipt.state.data["active_return"])
        self.assertEqual({}, receipt.state.data["current_stage_completions"])
        self.assertEqual(
            "I0", receipt.decision.return_request.data["calculated_owner"]
        )

    def test_cross_owner_revision_fails_after_h1_without_final(self):
        event = self._event(
            "revise",
            targets=[
                {
                    "target_scope": "conception",
                    "visible_element_ids": [],
                    "source_ids": ["INT-1"],
                    "requested_change": "revise intent",
                },
                {
                    "target_scope": "conception",
                    "visible_element_ids": [],
                    "source_ids": ["CHR-1"],
                    "requested_change": "revise character",
                },
            ],
        )
        author_runtime = importlib.import_module(
            "harnesses.novel-conception-autonomous.runtime.author_decision"
        )

        with self.assertRaises(author_runtime.AuthorDecisionError) as caught:
            self._run("revise", event=event, name="cross-owner")
        self.assertEqual(
            "AUTHOR_DECISION_CROSS_OWNER_REVISION", caught.exception.code
        )
        self.assertEqual("waiting_author", self.subject.state["status"])
        self.assertIn("H1", self.subject.state["current_stage_completions"])
        self.assertFalse(
            (self.root / "run-cross-owner" / "completion").exists()
        )

    def test_rejected_is_terminal_and_never_emits_final_completion(self):
        receipt = self._run("rejected")

        self.assertEqual("rejected", receipt.branch)
        self.assertIsNone(receipt.final)
        self.assertEqual("rejected", receipt.state.data["status"])
        self.assertEqual(
            "not_ready", receipt.state.data["development_status"]
        )
        self.assertFalse(
            (self.root / "run-rejected" / "completion").exists()
        )

    def test_exact_h1_stage_orphan_is_recovered_before_author_decision(self):
        event = self._event("rejected")
        output = self.root / "run-h1-orphan"
        orphan = output / "H1" / "stage"
        orphan.parent.mkdir(parents=True)
        shutil.copytree(self.root / "preview-rejected", orphan)
        before = [
            (
                path.relative_to(orphan).as_posix(),
                self.canonical.sha256_file(path),
            )
            for path in sorted(orphan.rglob("*"))
            if path.is_file()
        ]

        receipt = self._run(
            "rejected",
            event=event,
            name="h1-orphan",
        )

        after = [
            (
                path.relative_to(orphan).as_posix(),
                self.canonical.sha256_file(path),
            )
            for path in sorted(orphan.rglob("*"))
            if path.is_file()
        ]
        self.assertTrue(receipt.h1.replayed)
        self.assertFalse(receipt.h1.transition.replayed)
        self.assertEqual(before, after)
        self.assertEqual("rejected", receipt.branch)
        self.assertFalse((output / "completion").exists())

    def test_exact_waiting_author_successor_is_persistently_replayed(self):
        event = self._event("rejected")
        output = self.root / "run-h1-persistent"
        orphan = output / "H1" / "stage"
        orphan.parent.mkdir(parents=True)
        shutil.copytree(self.root / "preview-rejected", orphan)
        next_path = self._paths("h1-persistent")["h1"]
        with mock.patch.object(
            self.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_formal_p1_boundary,
        ):
            admitted = self.h1_runtime.publish_h1_completion(
                orphan,
                **self._h1_arguments(self.subject),
                next_state_path=next_path,
            )
        self.assertTrue(admitted.replayed)
        self.assertFalse(admitted.transition.replayed)

        receipt = self._run(
            "rejected",
            event=event,
            name="h1-persistent",
        )

        self.assertTrue(receipt.h1.replayed)
        self.assertTrue(receipt.h1.transition.replayed)
        self.assertEqual("rejected", receipt.branch)

    def test_non_h1_output_residue_is_rejected_before_h1_publish(self):
        harness = importlib.import_module(HARNESS_MODULE)
        event = self._event("rejected")
        cases = {
            "arbitrary": ("notes.txt", False),
            "d1": ("D1/stage/marker.json", False),
            "r1": ("R1/stage/marker.json", False),
            "author-decision": ("author-decision.json", False),
            "final": ("completion/conception-completion.json", False),
            "terminal": ("terminal/state.json", False),
            "h1-sibling": ("H1/extra/marker.json", True),
            "extra-sibling": ("extra/marker.json", True),
        }
        for label, (relative, with_h1) in cases.items():
            with self.subTest(label=label):
                output = self.root / f"residue-{label}"
                if with_h1:
                    stage = output / "H1" / "stage"
                    stage.mkdir(parents=True)
                    (stage / "marker.json").write_text(
                        "{}", encoding="utf-8"
                    )
                residue = output / relative
                residue.parent.mkdir(parents=True, exist_ok=True)
                residue.write_text("{}", encoding="utf-8")
                arguments = {
                    **self._h1_arguments(self.subject),
                    "stage_packages": self.fixture.stage_packages,
                    "author_event": event,
                    "development_handoff": self.fixture.development_handoff,
                    "next_state_paths": self._paths(f"residue-{label}"),
                }
                with mock.patch.object(
                    harness,
                    "publish_h1_completion",
                    side_effect=AssertionError("publisher must not run"),
                ), self.assertRaises(harness.HarnessRunError) as caught:
                    harness.run_from_rendered_h1(output, **arguments)
                self.assertEqual(
                    "HARN_OUTPUT_ROOT_INVALID", caught.exception.code
                )

    def test_output_root_alias_is_rejected_before_resolve_or_h1_publish(self):
        harness = importlib.import_module(HARNESS_MODULE)
        event = self._event("rejected")
        target = self.root / "alias-target"
        target.mkdir()
        alias = self.root / "alias-output-root"
        real_alias = True
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError:
            real_alias = False
        alias_check = (
            mock.patch.object(
                harness,
                "_is_path_alias",
                wraps=harness._is_path_alias,
            )
            if real_alias
            else mock.patch.object(
                harness,
                "_is_path_alias",
                return_value=True,
            )
        )
        arguments = {
            **self._h1_arguments(self.subject),
            "stage_packages": self.fixture.stage_packages,
            "author_event": event,
            "development_handoff": self.fixture.development_handoff,
            "next_state_paths": self._paths("alias-root"),
        }

        with alias_check, mock.patch.object(
            harness,
            "publish_h1_completion",
            side_effect=AssertionError("publisher must not run"),
        ), self.assertRaises(harness.HarnessRunError) as caught:
            harness.run_from_rendered_h1(alias, **arguments)

        self.assertEqual("HARN_OUTPUT_ROOT_INVALID", caught.exception.code)
        self.assertEqual([], list(target.iterdir()))

    def test_stage_shortcuts_are_rejected_before_h1_publish(self):
        harness = importlib.import_module(HARNESS_MODULE)
        event = self._event("rejected")
        for stage in ("H1", "D1", "R1"):
            with self.subTest(stage=stage):
                packages = dict(self.fixture.stage_packages)
                packages[stage] = self.fixture.p1_package
                arguments = {
                    **self._h1_arguments(self.subject),
                    "stage_packages": packages,
                    "author_event": event,
                    "development_handoff": self.fixture.development_handoff,
                    "next_state_paths": self._paths(
                        f"shortcut-{stage.lower()}"
                    ),
                }
                with mock.patch.object(
                    harness,
                    "publish_h1_completion",
                    side_effect=AssertionError("publisher must not run"),
                ), self.assertRaises(harness.HarnessRunError) as caught:
                    harness.run_from_rendered_h1(
                        self.root / f"shortcut-{stage.lower()}",
                        **arguments,
                    )
                self.assertEqual(
                    "HARN_STAGE_PACKAGES_INVALID", caught.exception.code
                )

    def test_reconstructed_assembled_predecessor_rejects_tampering_atomically(
        self,
    ):
        """The rendered successor must prove the byte-exact assembled state."""

        for label, mutate in (
            (
                "reconstructible-field",
                lambda data: data["p1_completion"].__setitem__(
                    "sha256", "0" * 64
                ),
            ),
            (
                "previous-hash",
                lambda data: data.__setitem__(
                    "previous_state_sha256", "f" * 64
                ),
            ),
        ):
            with self.subTest(label=label):
                coordinator = self._clone_coordinator()
                before = copy.deepcopy(coordinator.state)
                bad_data = copy.deepcopy(self.fixture.rendered_workspace.data)
                mutate(bad_data)
                bad_rendered = self.coordinator_module.seal_document(
                    bad_data,
                    self.fixture.rendered_workspace.reference["path"],
                )
                output = self.root / f"tampered-{label}"

                with mock.patch.object(
                    self.p1_runtime,
                    "validate_p1_package",
                    side_effect=self._accept_formal_p1_boundary,
                ), self.assertRaises(
                    (
                        self.h1_runtime.H1CompletionError,
                        self.h1c_runtime.H1CError,
                    )
                ) as caught:
                    self.h1_runtime.publish_h1_completion(
                        output,
                        **{
                            **self._h1_arguments(coordinator),
                            "rendered_workspace": bad_rendered,
                        },
                        next_state_path=f"state/tampered-{label}.json",
                    )

                self.assertIn(
                    caught.exception.code,
                    {
                        "H1_COMPLETION_WORKSPACE_LINEAGE_MISMATCH",
                        "H1C_WORKSPACE_INVALID",
                    },
                )
                self.assertEqual(before, coordinator.state)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
