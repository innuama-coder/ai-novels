from __future__ import annotations

import importlib
import json
import math
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


contracts = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.contracts"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
production_store = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_store"
)


ZERO_HASH = "0" * 64


def artifact(path: str) -> dict[str, str]:
    return {"path": path, "sha256": ZERO_HASH}


def h1_fragment_manifest() -> dict:
    names = (
        "fragment-package.json",
        "fragments.md",
        "generation-session.json",
        "session-workspace-completion.json",
        "generation-evidence-index.json",
        "execution-record.json",
        "validation.json",
        "implementation/run_v2.py",
    )
    refs = {name: artifact(name) for name in names}
    return {
        "schema_version": "2.0",
        "run_id": "RUN-001",
        "stage": "H1",
        "package_profile": "h1-fragments",
        "verdict": "ready",
        "files": list(refs.values()),
        "artifact_roles": {
            "fragment_package": refs["fragment-package.json"],
            "fragments": refs["fragments.md"],
            "generation_session": refs["generation-session.json"],
            "session_workspace_completion": refs[
                "session-workspace-completion.json"
            ],
            "generation_evidence_index": refs[
                "generation-evidence-index.json"
            ],
            "execution_record": refs["execution-record.json"],
        },
        "validation": refs["validation.json"],
        "implementation": [refs["implementation/run_v2.py"]],
        "parent_state_sha256": ZERO_HASH,
        "session_id": "H1-001",
    }


class ContractRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = contracts.ContractRuntime()

    def test_all_32_authoritative_schemas_and_refs_self_check(self) -> None:
        checked = self.runtime.check_all_schemas()

        self.assertEqual(32, len(checked))
        self.assertIn("common-defs.schema.json", checked)
        self.assertIn("world-model.schema.json", checked)

    def test_additional_properties_is_rejected(self) -> None:
        instance = {"path": "S1/model.json", "sha256": ZERO_HASH}
        self.runtime.validate_definition(
            instance, "common-defs.schema.json", "artifactReference"
        )

        instance["unexpected"] = True
        with self.assertRaises(contracts.ContractValidationError) as caught:
            self.runtime.validate_definition(
                instance, "common-defs.schema.json", "artifactReference"
            )

        self.assertIn("Additional properties", str(caught.exception))
        diagnostic = caught.exception.diagnostics[0]
        self.assertEqual("V2_SCHEMA_ADDITIONAL_PROPERTIES", diagnostic.code)
        self.assertEqual("$", diagnostic.instance_path)
        self.assertEqual("additionalProperties", diagnostic.keyword)
        self.assertIsNone(diagnostic.object_id)

    def test_diagnostics_are_structured_deterministic_and_include_nearby_id(self) -> None:
        decision = {
            "id": "DEC-001",
            "gap": "需要选择",
            "options": ["A", "B"],
            "selection": "A",
            "owner": "S1",
            "authority_basis": "自主职责",
            "compatibility": "与输入兼容",
            "impact_ids": [],
            "cost": "有限",
            "reversibility": "reversible",
            "downstream_freedom": "可细化",
            "projection_ids": [],
            "unexpected": True,
        }

        errors = []
        for _ in range(2):
            with self.assertRaises(contracts.ContractValidationError) as caught:
                self.runtime.validate_definition(
                    decision, "canonical-common.schema.json", "designDecision"
                )
            errors.append(caught.exception)

        self.assertEqual(errors[0].as_records(), errors[1].as_records())
        self.assertEqual(str(errors[0]), str(errors[1]))
        diagnostic = errors[0].diagnostics[0]
        self.assertEqual("DEC-001", diagnostic.object_id)
        self.assertEqual("additionalProperties", diagnostic.keyword)
        self.assertTrue(diagnostic.schema_path.startswith("$"))
        self.assertEqual(
            {
                "code",
                "instance_path",
                "schema_path",
                "keyword",
                "object_id",
                "message",
            },
            set(diagnostic.as_record()),
        )

    def test_conditionals_and_cross_file_refs_are_executed(self) -> None:
        valid = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "stage": "H1",
            "session_id": "H1-001",
            "state": "planned",
            "p1_completion": {
                "stage": "P1",
                "path": "P1/stage-completion.json",
                "sha256": ZERO_HASH,
            },
            "previous_state_sha256": ZERO_HASH,
            "artifacts": {"plan_manifest": artifact("H1/plan/package-manifest.json")},
        }
        self.runtime.validate(valid, "h1-workspace-state.schema.json")

        missing_conditional_field = deepcopy(valid)
        missing_conditional_field["artifacts"] = {}
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(
                missing_conditional_field, "h1-workspace-state.schema.json"
            )

        wrong_cross_file_reference = deepcopy(valid)
        wrong_cross_file_reference["p1_completion"]["stage"] = "Q1"
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(
                wrong_cross_file_reference, "h1-workspace-state.schema.json"
            )

    def test_one_of_branch_is_enforced(self) -> None:
        machine = {
            "completion_path": "P1/stage-completion.json",
            "completion_sha256": ZERO_HASH,
            "manifest_path": "P1/package-manifest.json",
            "manifest_sha256": ZERO_HASH,
        }
        human = {
            "completion_path": "H1/stage-completion.json",
            "completion_sha256": ZERO_HASH,
            "manifest_path": "H1/package-manifest.json",
            "manifest_sha256": ZERO_HASH,
            "html_path": "H1/report.html",
            "html_sha256": ZERO_HASH,
        }
        approved = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "approval_scope": "conception",
            "decision": "approved",
            "machine_package": machine,
            "human_review_package": human,
            "approval_record": {"event_seq": 1, "text": "批准"},
            "unresolved_items": [],
        }
        self.runtime.validate(approved, "author-decision.schema.json")

        mixed_branch = deepcopy(approved)
        mixed_branch["revision_targets"] = []
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(mixed_branch, "author-decision.schema.json")

    def test_fragment_package_requires_complete_human_review_fragments(self) -> None:
        package = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "h1_session_id": "H1-001",
            "p1_completion": artifact("P1/stage-completion.json"),
            "plan_manifest": artifact("H1/plan/package-manifest.json"),
            "fragments": [
                {
                    "id": "FRAG-001",
                    "title": "Opening pressure",
                    "review_purpose": "Judge the intended experience.",
                    "text": "A complete non-authoritative sample.",
                    "source_ids": ["CHR-001"],
                    "decision_control_ids": ["DCTRL-001"],
                }
            ],
            "authority_status": "non_authoritative_sample",
        }
        self.runtime.validate(package, "fragment-package.schema.json")

        id_only = deepcopy(package)
        id_only["fragments"] = [{"id": "FRAG-001"}]
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(id_only, "fragment-package.schema.json")

    def test_h1_fragment_manifest_accepts_session_workspace_completion(self) -> None:
        self.runtime.validate(
            h1_fragment_manifest(), "package-manifest.schema.json"
        )

    def test_h1_fragment_manifest_requires_session_workspace_completion(self) -> None:
        manifest = h1_fragment_manifest()
        del manifest["artifact_roles"]["session_workspace_completion"]
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(manifest, "package-manifest.schema.json")

    def test_h1_fragment_manifest_rejects_unknown_role(self) -> None:
        manifest = h1_fragment_manifest()
        manifest["artifact_roles"]["unknown_completion"] = artifact(
            "unknown.json"
        )
        with self.assertRaises(contracts.ContractValidationError):
            self.runtime.validate(manifest, "package-manifest.schema.json")

    def test_unresolved_reference_blocks_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_dir = Path(directory)
            (schema_dir / "broken.schema.json").write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "broken.schema.json",
                        "$ref": "missing.schema.json",
                    }
                ),
                encoding="utf-8",
            )

            runtime = contracts.ContractRuntime(
                schema_dir=schema_dir, expected_schema_count=None
            )
            with self.assertRaises(contracts.SchemaCatalogError):
                runtime.check_all_schemas()


class CanonicalAndManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = contracts.ContractRuntime()

    def test_canonical_json_and_hash_ignore_mapping_order(self) -> None:
        left = {"z": [3, 2, 1], "a": {"中文": "值", "enabled": True}}
        right = {"a": {"enabled": True, "中文": "值"}, "z": [3, 2, 1]}

        self.assertEqual(canonical.canonical_json_bytes(left), canonical.canonical_json_bytes(right))
        self.assertEqual(canonical.canonical_sha256(left), canonical.canonical_sha256(right))
        self.assertEqual(
            '{"a":{"enabled":true,"中文":"值"},"z":[3,2,1]}',
            canonical.canonical_json(left),
        )

    def test_non_finite_numbers_are_not_canonical_json(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(canonical.CanonicalizationError):
                    canonical.canonical_json_bytes({"value": value})

    def test_artifact_reference_is_relative_posix_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "nested" / "artifact.json"
            path.parent.mkdir()
            path.write_bytes(b'{"ok":true}')

            reference = canonical.artifact_reference(path, root=root)

            self.assertEqual("nested/artifact.json", reference["path"])
            canonical.verify_artifact_reference(reference, root=root)

            path.write_bytes(b'{"ok":false}')
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.verify_artifact_reference(reference, root=root)

    def test_artifact_reference_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.resolve_artifact_path("../outside.json", root=root)
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.resolve_artifact_path("C:/outside.json", root=root)

    def test_artifact_reference_rejects_noncanonical_path_aliases(self) -> None:
        aliases = ("a//b.json", "a/./b.json", "a/b.json/")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for alias in aliases:
                with self.subTest(alias=alias):
                    with self.assertRaises(canonical.ManifestIntegrityError):
                        canonical.resolve_artifact_path(alias, root=root)

    def test_windows_extended_and_plain_paths_have_one_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "nested" / "artifact.json"
            path.parent.mkdir()
            path.write_bytes(b'{"ok":true}')
            plain_reference = canonical.artifact_reference(path, root=root)
            if os.name == "nt":
                extended_root = Path("\\\\?\\" + str(root))
                extended_path = extended_root / "nested" / "artifact.json"
                self.assertEqual(
                    plain_reference,
                    canonical.artifact_reference(extended_path, root=root),
                )
                self.assertEqual(
                    plain_reference,
                    canonical.artifact_reference(path, root=extended_root),
                )
                self.assertEqual(
                    canonical.filesystem_identity(root),
                    production_store.ProductionRunStore(extended_root).root,
                )
                canonical.verify_artifact_reference(
                    plain_reference, root=extended_root
                )
            else:
                self.assertEqual(root, canonical.filesystem_identity(root))

    def test_store_path_identity_keeps_escape_checks_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory).resolve()
            subject = production_store.ProductionRunStore(root)
            for logical in (
                "../outside.json",
                "/absolute.json",
                "C:/other-drive.json",
                "D:/other-drive.json",
                "nested\\alias.json",
            ):
                with self.subTest(logical=logical):
                    with self.assertRaises(production_store.ProductionStoreError):
                        subject._path(logical)

            outside_root = Path(outside).resolve()
            (outside_root / "artifact.json").write_text("outside", encoding="utf-8")
            with self.assertRaises(production_store.ProductionStoreError) as caught:
                subject.resolve_physical_path(outside_root / "artifact.json")
            self.assertEqual("PROD_PATH_ESCAPE", caught.exception.code)
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.artifact_reference(
                    outside_root / "artifact.json", root=root
                )
            link = root / "linked-outside"
            try:
                link.symlink_to(outside_root, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaises(production_store.ProductionStoreError) as caught:
                subject._path("linked-outside/artifact.json")
            self.assertEqual("PROD_PATH_ESCAPE", caught.exception.code)
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.resolve_artifact_path(
                    "linked-outside/artifact.json", root=root
                )

    def test_manifest_schema_and_integrity_accept_bound_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = [
                "storyline-architecture.json",
                "generation-session.json",
                "generation-evidence-index.json",
                "execution-record.json",
                "preview.md",
                "validation.json",
                "runtime/contracts.py",
            ]
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name, encoding="utf-8")
            refs = {
                name: canonical.artifact_reference(root / name, root=root)
                for name in names
            }
            manifest = {
                "schema_version": "2.0",
                "run_id": "RUN-001",
                "stage": "S1",
                "package_profile": "generated-model",
                "verdict": "ready",
                "files": list(refs.values()),
                "artifact_roles": {
                    "canonical": refs["storyline-architecture.json"],
                    "generation_session": refs["generation-session.json"],
                    "generation_evidence_index": refs["generation-evidence-index.json"],
                    "execution_record": refs["execution-record.json"],
                    "preview": refs["preview.md"],
                },
                "validation": refs["validation.json"],
                "implementation": [refs["runtime/contracts.py"]],
            }

            self.runtime.validate(manifest, "package-manifest.schema.json")
            canonical.verify_manifest_integrity(manifest, root=root)

            unbound = deepcopy(manifest)
            unbound["artifact_roles"]["canonical"] = artifact("other.json")
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.verify_manifest_integrity(unbound, root=root)

    def test_manifest_duplicate_paths_are_rejected_even_with_different_hashes(self) -> None:
        manifest = {
            "files": [
                {"path": "same.json", "sha256": "0" * 64},
                {"path": "same.json", "sha256": "1" * 64},
            ],
            "artifact_roles": {},
            "validation": {"path": "same.json", "sha256": "0" * 64},
            "implementation": [{"path": "same.json", "sha256": "0" * 64}],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "same.json").write_bytes(b"data")
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.verify_manifest_integrity(manifest, root=root)

    def test_manifest_rejects_path_alias_before_filesystem_consumption(self) -> None:
        reference = {"path": "nested//artifact.json", "sha256": "0" * 64}
        manifest = {
            "files": [reference],
            "artifact_roles": {"canonical": reference},
            "validation": reference,
            "implementation": [reference],
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(canonical.ManifestIntegrityError):
                canonical.verify_manifest_integrity(manifest, root=directory)


if __name__ == "__main__":
    unittest.main()
