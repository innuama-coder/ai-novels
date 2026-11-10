from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
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
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any


quality = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_quality"
)
storyline_plan = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_plan"
)
rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
SOURCE_EVALS = Path(__file__).resolve().parents[1]


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
        encoding="utf-8",
        newline="",
    )


class StorylineProposalQualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="storyline-quality-gate-"
        )
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _copy_case(
        self, case_name: str, namespace: str
    ) -> tuple[Path, Path]:
        evals = self.repository / namespace
        for schema_name in (
            "eval-case-manifest.v1.schema.json",
            "storyline-plan.v1.schema.json",
            "storyline-proposal-quality-gate.v1.schema.json",
        ):
            target = evals / "schemas" / schema_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                SOURCE_EVALS / "schemas" / schema_name,
                target,
            )
        fixture_root = evals / "fixtures" / case_name
        fixture_root.mkdir(parents=True)
        for artifact_name in (
            "fixture.json",
            "storyline-plan.v1.json",
            "storyline-proposal-quality-gate.v1.json",
        ):
            shutil.copyfile(
                SOURCE_EVALS
                / "fixtures"
                / case_name
                / artifact_name,
                fixture_root / artifact_name,
            )
        manifest = evals / "manifests" / f"{case_name}.v1.json"
        manifest.parent.mkdir(parents=True)
        shutil.copyfile(
            SOURCE_EVALS / "manifests" / f"{case_name}.v1.json",
            manifest,
        )
        return evals, manifest

    def test_formal_manifest_only_loader_admits_both_cases(self) -> None:
        for case_name in ("generic", "duanxian"):
            with self.subTest(case=case_name):
                loaded = quality.load_ready_eval_case(
                    SOURCE_EVALS
                    / "manifests"
                    / f"{case_name}.v1.json"
                )
                self.assertEqual("ready", loaded.validation["status"])
                self.assertEqual(
                    loaded.structural_case.manifest[
                        "storyline_quality_gate"
                    ]["sha256"],
                    rt.sha256_file(loaded.gate_path),
                )
                self.assertEqual(
                    loaded.structural_case.manifest[
                        "storyline_quality_gate_schema"
                    ]["sha256"],
                    rt.sha256_file(loaded.gate_schema_path),
                )

    def test_compatibility_type_and_same_hash_sibling_are_not_formal(
        self,
    ) -> None:
        manifest = SOURCE_EVALS / "manifests" / "generic.v1.json"
        formal = quality.load_ready_eval_case(manifest)
        declared_gate = formal.gate_path
        compatibility = quality.load_storyline_quality_gate(
            manifest,
            declared_gate,
        )
        self.assertIsInstance(
            formal, quality.FormalValidatedStorylineQualityCase
        )
        self.assertIsInstance(
            compatibility,
            quality.CompatibilityValidatedStorylineQualityCase,
        )
        self.assertNotIsInstance(
            compatibility,
            quality.FormalValidatedStorylineQualityCase,
        )

        evals, copied_manifest = self._copy_case(
            "generic", "evals-compat-sibling"
        )
        copied = quality.load_ready_eval_case(
            copied_manifest,
            repository_root=self.repository,
            evals_root=evals,
        )
        sibling = copied.gate_path.with_name("same-hash-sibling.json")
        sibling.write_bytes(copied.gate_path.read_bytes())
        self.assertEqual(
            rt.sha256_file(copied.gate_path),
            rt.sha256_file(sibling),
        )
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_GATE_PATH_NOT_DECLARED",
        ):
            quality.load_storyline_quality_gate(
                copied_manifest,
                sibling,
                repository_root=self.repository,
                evals_root=evals,
            )

    def test_formal_loader_rejects_gate_hash_and_schema_ref_tamper(
        self,
    ) -> None:
        evals, manifest_path = self._copy_case(
            "generic", "evals-formal-tamper"
        )
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        gate = evals.joinpath(
            *manifest["storyline_quality_gate"]["path"].split("/")
        )
        gate.write_text(
            gate.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            storyline_plan.StorylinePlanError,
            "STORYLINE_PLAN_REFERENCE_INVALID",
        ):
            quality.load_ready_eval_case(
                manifest_path,
                repository_root=self.repository,
                evals_root=evals,
            )

        evals, manifest_path = self._copy_case(
            "generic", "evals-formal-schema-ref"
        )
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        manifest["storyline_quality_gate_schema"]["path"] = (
            "schemas/storyline-plan.v1.schema.json"
        )
        manifest["storyline_quality_gate_schema"]["sha256"] = (
            rt.sha256_file(
                evals / "schemas" / "storyline-plan.v1.schema.json"
            )
        )
        _write(manifest_path, manifest)
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_SCHEMA_REFERENCE_INVALID",
        ):
            quality.load_ready_eval_case(
                manifest_path,
                repository_root=self.repository,
                evals_root=evals,
            )

    def _load_structural(self, evals: Path, manifest: Path) -> Any:
        return storyline_plan.load_eval_case(
            manifest,
            repository_root=self.repository,
            evals_root=evals,
        )

    @staticmethod
    def _gate(structural: Any) -> dict[str, Any]:
        targets = quality.expected_check_targets(structural)
        checks = []
        for index, check_id in enumerate(quality.REQUIRED_CHECKS, 1):
            target_id = targets[check_id][0]
            checks.append(
                {
                    "id": check_id,
                    "status": "pass",
                    "target_ids": targets[check_id],
                    "evidence": (
                        f"Evidence {index} binds {target_id} to the exact "
                        f"{check_id} objects and reviews their stated relation."
                    ),
                    "failure_condition": (
                        f"Failure {index} occurs if {target_id} no longer "
                        f"satisfies the reviewed {check_id} relationship."
                    ),
                }
            )
        return {
            "schema_version": "1.0",
            "kind": "storyline-proposal-quality-gate",
            "gate_id": (
                "SPQG-"
                + str(structural.manifest["manifest_id"]).removeprefix(
                    "ECASE-"
                )
            ),
            "ownership": copy.deepcopy(quality.EXPECTED_OWNERSHIP),
            "subject": {
                "manifest_id": structural.manifest["manifest_id"],
                "fixture": copy.deepcopy(
                    structural.manifest["fixture"]
                ),
                "storyline_plan": copy.deepcopy(
                    structural.manifest["storyline_plan"]
                ),
                "storyline_plan_schema": copy.deepcopy(
                    structural.manifest["storyline_plan_schema"]
                ),
                "fixture_id": structural.fixture["fixture_id"],
                "run_id": structural.fixture["run_id"],
                "plan_id": structural.plan["plan_id"],
                "structural_validation_sha256": rt.canonical_sha256(
                    structural.validation
                ),
            },
            "producer": {
                "task_id": "task-producer-01",
                "thread_id": "thread-producer-01",
                "role": "proposal_producer",
            },
            "reviewer": {
                "task_id": "task-reviewer-01",
                "thread_id": "thread-reviewer-01",
                "role": "independent_proposal_reviewer",
            },
            "checks": checks,
            "findings": [],
            "verdict": "ready",
        }

    def _publish_gate(
        self,
        evals: Path,
        structural: Any,
        *,
        mutate: Any | None = None,
    ) -> Path:
        gate = self._gate(structural)
        if mutate is not None:
            mutate(gate)
        path = evals.joinpath(
            *structural.manifest["storyline_quality_gate"]["path"].split(
                "/"
            )
        )
        _write(path, gate)
        return path

    def _load_quality(
        self,
        evals: Path,
        manifest: Path,
        gate: Path,
    ) -> Any:
        return quality.load_storyline_quality_gate(
            manifest,
            gate,
            repository_root=self.repository,
            evals_root=evals,
        )

    def test_generic_and_duanxian_temp_gates_are_ready(self) -> None:
        expected = {
            "generic": (8, 2, 3, 0),
            "duanxian": (8, 2, 2, 1),
        }
        for case_name, counts in expected.items():
            with self.subTest(case=case_name):
                evals, manifest = self._copy_case(
                    case_name, f"evals-{case_name}"
                )
                structural = self._load_structural(evals, manifest)
                gate = self._publish_gate(evals, structural)
                loaded = self._load_quality(evals, manifest, gate)
                self.assertEqual("ready", loaded.validation["status"])
                self.assertEqual(counts[0], loaded.validation["check_count"])
                self.assertEqual(
                    counts[1], loaded.validation["open_target_count"]
                )
                self.assertEqual(
                    counts[2], loaded.validation["optional_target_count"]
                )
                self.assertEqual(
                    counts[3], loaded.validation["derived_anchor_count"]
                )

    def test_structural_loader_rejects_plan_hash_drift_first(self) -> None:
        evals, manifest = self._copy_case("generic", "evals-drift")
        structural = self._load_structural(evals, manifest)
        gate = self._publish_gate(evals, structural)
        plan = evals / "fixtures/generic/storyline-plan.v1.json"
        plan.write_bytes(plan.read_bytes() + b"\n")
        with self.assertRaises(storyline_plan.StorylinePlanError):
            self._load_quality(evals, manifest, gate)
        structural.validation["status"] = "not_ready"
        synchronized_gate = self._gate(structural)
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_STRUCTURAL_NOT_READY",
        ):
            quality.validate_storyline_quality_gate(
                structural, synchronized_gate
            )
        non_mapping = replace(structural, validation=[])
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_STRUCTURAL_VALIDATION_INVALID",
        ):
            quality.validate_storyline_quality_gate(
                non_mapping, self._gate(non_mapping)
            )
        structural.validation["status"] = "ready"
        for identity_field in ("plan_id", "fixture_id", "run_id"):
            with self.subTest(identity=identity_field):
                mismatched = replace(
                    structural,
                    validation=copy.deepcopy(structural.validation),
                )
                mismatched.validation[identity_field] = (
                    f"mismatched-{identity_field}"
                )
                with self.assertRaisesRegex(
                    quality.StorylineQualityError,
                    "STORYLINE_QUALITY_STRUCTURAL_IDENTITY_MISMATCH",
                ):
                    quality.validate_storyline_quality_gate(
                        mismatched, self._gate(mismatched)
                    )

    def test_gate_subject_rejects_stale_plan_reference(self) -> None:
        evals, manifest = self._copy_case("generic", "evals-stale")
        structural = self._load_structural(evals, manifest)
        gate = self._publish_gate(
            evals,
            structural,
            mutate=lambda value: value["subject"]["storyline_plan"].update(
                {"sha256": "0" * 64}
            ),
        )
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_SUBJECT_MISMATCH",
        ):
            self._load_quality(evals, manifest, gate)

    def test_producer_and_reviewer_task_and_thread_must_differ(self) -> None:
        for field in ("task_id", "thread_id"):
            with self.subTest(field=field):
                evals, manifest = self._copy_case(
                    "generic", f"evals-same-{field}"
                )
                structural = self._load_structural(evals, manifest)

                def mutate(value: dict[str, Any]) -> None:
                    value["reviewer"][field] = value["producer"][field]

                gate = self._publish_gate(
                    evals, structural, mutate=mutate
                )
                with self.assertRaisesRegex(
                    quality.StorylineQualityError,
                    "STORYLINE_QUALITY_REVIEW_NOT_INDEPENDENT",
                ):
                    self._load_quality(evals, manifest, gate)

    def test_missing_or_duplicate_check_fails_closed(self) -> None:
        mutations = {
            "missing": lambda value: value["checks"].pop(),
            "duplicate": lambda value: value["checks"][-1].update(
                {"id": value["checks"][0]["id"]}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                evals, manifest = self._copy_case(
                    "generic", f"evals-check-{name}"
                )
                structural = self._load_structural(evals, manifest)
                gate = self._publish_gate(
                    evals, structural, mutate=mutate
                )
                with self.assertRaises(quality.StorylineQualityError):
                    self._load_quality(evals, manifest, gate)

    def test_unknown_target_fails_closed(self) -> None:
        evals, manifest = self._copy_case("generic", "evals-unknown")
        structural = self._load_structural(evals, manifest)

        def mutate(value: dict[str, Any]) -> None:
            value["checks"][0]["target_ids"][0] = "UNKNOWN-TARGET"
            value["checks"][0]["evidence"] += " UNKNOWN-TARGET"
            value["checks"][0]["failure_condition"] += " UNKNOWN-TARGET"

        gate = self._publish_gate(evals, structural, mutate=mutate)
        with self.assertRaises(quality.StorylineQualityError):
            self._load_quality(evals, manifest, gate)

    def test_ready_with_finding_is_not_admitted(self) -> None:
        evals, manifest = self._copy_case("generic", "evals-finding")
        structural = self._load_structural(evals, manifest)

        def mutate(value: dict[str, Any]) -> None:
            target = value["checks"][0]["target_ids"][0]
            value["findings"] = [
                {
                    "id": "SPQF-001",
                    "check_id": value["checks"][0]["id"],
                    "target_ids": [target],
                    "problem": "The accountable review found a problem.",
                    "required_revision": "Revise the cited proposal target.",
                }
            ]

        gate = self._publish_gate(evals, structural, mutate=mutate)
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_NOT_READY",
        ):
            self._load_quality(evals, manifest, gate)

    def test_gate_cannot_claim_author_authority_or_completion(self) -> None:
        mutations = {
            "authority": lambda value: value["ownership"].update(
                {"authority": "author_authority"}
            ),
            "completion": lambda value: value["ownership"].update(
                {"artifact_role": "stage_completion"}
            ),
            "producer-role": lambda value: value["producer"].update(
                {"role": "independent_proposal_reviewer"}
            ),
            "extra-field": lambda value: value.update(
                {"undeclared": "schema bypass"}
            ),
            "schema-invalid": lambda value: value.update(
                {"schema_version": "2.0"}
            ),
            "check-fail": lambda value: value["checks"][0].update(
                {"status": "fail"}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                evals, manifest = self._copy_case(
                    "generic", f"evals-direct-{name}"
                )
                structural = self._load_structural(evals, manifest)
                gate = self._gate(structural)
                mutate(gate)
                with self.assertRaises(quality.StorylineQualityError):
                    quality.validate_storyline_quality_gate(
                        structural, gate
                    )

    def test_open_and_optional_coverage_are_exact(self) -> None:
        for check_id in (
            "open_preservation",
            "optional_non_load_bearing",
        ):
            with self.subTest(check=check_id):
                evals, manifest = self._copy_case(
                    "generic", f"evals-coverage-{check_id}"
                )
                structural = self._load_structural(evals, manifest)

                def mutate(value: dict[str, Any]) -> None:
                    check = next(
                        item
                        for item in value["checks"]
                        if item["id"] == check_id
                    )
                    check["target_ids"].pop()

                gate = self._publish_gate(
                    evals, structural, mutate=mutate
                )
                with self.assertRaises(quality.StorylineQualityError):
                    self._load_quality(evals, manifest, gate)

    def test_derived_anchor_and_source_control_cannot_be_omitted(self) -> None:
        evals, manifest = self._copy_case("duanxian", "evals-derived")
        structural = self._load_structural(evals, manifest)

        def mutate(value: dict[str, Any]) -> None:
            check = next(
                item
                for item in value["checks"]
                if item["id"] == "authority_preservation"
            )
            check["target_ids"].remove("DX-PRESTART-DUAL-LINE-MERGE")

        gate = self._publish_gate(evals, structural, mutate=mutate)
        with self.assertRaises(quality.StorylineQualityError):
            self._load_quality(evals, manifest, gate)

    def test_evidence_must_be_concrete_unique_and_non_placeholder(self) -> None:
        mutations = {
            "no-target": lambda check: check.update(
                {
                    "evidence": (
                        "This sentence is long enough but cites no reviewed "
                        "proposal object identifier at all."
                    )
                }
            ),
            "placeholder": lambda check: check.update(
                {
                    "evidence": (
                        f"TBD placeholder for {check['target_ids'][0]} is "
                        "long enough to pass only primitive schema checks."
                    )
                }
            ),
        }
        for name, mutate_check in mutations.items():
            with self.subTest(name=name):
                evals, manifest = self._copy_case(
                    "generic", f"evals-evidence-{name}"
                )
                structural = self._load_structural(evals, manifest)

                def mutate(value: dict[str, Any]) -> None:
                    mutate_check(value["checks"][0])

                gate = self._publish_gate(
                    evals, structural, mutate=mutate
                )
                with self.assertRaises(quality.StorylineQualityError):
                    self._load_quality(evals, manifest, gate)

    def test_placeholder_in_structurally_valid_plan_is_rejected(self) -> None:
        evals, manifest = self._copy_case(
            "generic", "evals-subject-placeholder"
        )
        plan_path = evals / "fixtures/generic/storyline-plan.v1.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["architecture"]["subject"] = "TBD"
        _write(plan_path, plan)
        manifest_value = json.loads(
            manifest.read_text(encoding="utf-8")
        )
        manifest_value["storyline_plan"]["sha256"] = rt.sha256_file(
            plan_path
        )
        _write(manifest, manifest_value)
        structural = self._load_structural(evals, manifest)
        gate = self._publish_gate(evals, structural)
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_SUBJECT_PLACEHOLDER",
        ):
            self._load_quality(evals, manifest, gate)

    def test_quality_schema_is_code_pinned(self) -> None:
        evals, manifest = self._copy_case("generic", "evals-schema-pin")
        structural = self._load_structural(evals, manifest)
        gate = self._publish_gate(evals, structural)
        schema = (
            evals
            / "schemas/storyline-proposal-quality-gate.v1.schema.json"
        )
        schema.write_bytes(schema.read_bytes() + b"\n")
        with self.assertRaisesRegex(
            quality.StorylineQualityError,
            "STORYLINE_QUALITY_SCHEMA_UNTRUSTED",
        ):
            self._load_quality(evals, manifest, gate)


if __name__ == "__main__":
    unittest.main()
