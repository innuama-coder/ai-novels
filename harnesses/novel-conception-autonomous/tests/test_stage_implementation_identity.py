from __future__ import annotations

import hashlib
import importlib
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

identity = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.stage_implementation_identity"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify(reference: dict[str, str], *, root: Path) -> Path:
    path = root / PurePosixPath(reference["path"])
    if not path.is_file() or _sha(path) != reference["sha256"]:
        raise ValueError("stored artifact differs")
    return path


class StageImplementationIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.current = self.root / "current"
        self.package = self.root / "package"
        self.current.mkdir()
        self.package.mkdir()

    def _write(self, relative: str, payload: bytes, *, current: bool) -> Path:
        root = self.current if current else self.package
        path = root / PurePosixPath(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def _record(self, identity_name: str, payload: bytes) -> dict[str, object]:
        relative = f"implementation/{identity_name}"
        path = self._write(relative, payload, current=False)
        return {
            "identity": identity_name,
            "artifact": {"path": relative, "sha256": _sha(path)},
        }

    def test_current_catalog_is_exact_and_tamper_fails_closed(self) -> None:
        paths = {
            identity.IDENTITY_MODULE: self._write("authority.py", b"authority", current=True),
            "skill/run_v2.py": self._write("runner.py", b"runner", current=True),
        }
        records = [
            self._record(identity.IDENTITY_MODULE, b"authority"),
            self._record("skill/run_v2.py", b"runner"),
        ]
        mode, _ = identity.validate_stage_catalog(
            stage="X1",
            records=records,
            package_root=self.package,
            current_paths=paths,
            verify_artifact_reference=_verify,
            sha256_file=_sha,
        )
        self.assertEqual("1.0", mode)
        (self.package / records[1]["artifact"]["path"]).write_bytes(b"tampered")
        with self.assertRaises(identity.StageImplementationIdentityError):
            identity.validate_stage_catalog(
                stage="X1",
                records=records,
                package_root=self.package,
                current_paths=paths,
                verify_artifact_reference=_verify,
                sha256_file=_sha,
            )

    def test_frozen_legacy_mapping_rejects_future_current_drift(self) -> None:
        old_runner = b"old runner"
        approved_runner = b"approved runner"
        paths = {
            identity.IDENTITY_MODULE: self._write("authority.py", b"authority", current=True),
            "skill/run_v2.py": self._write("runner.py", approved_runner, current=True),
        }
        records = [
            self._record("skill/run_v2.py", old_runner),
            self._record("upstream/old-validator.py", b"old upstream"),
        ]
        contract = {
            "canonical_digest": identity.canonical_catalog_digest(records),
            "removed_identities": frozenset({"upstream/old-validator.py"}),
            "approved_mismatches": {
                "skill/run_v2.py": (
                    hashlib.sha256(old_runner).hexdigest(),
                    hashlib.sha256(approved_runner).hexdigest(),
                )
            },
        }
        with mock.patch.dict(identity.TRUSTED_LEGACY_CATALOGS, {"X1": contract}):
            mode, _ = identity.validate_stage_catalog(
                stage="X1",
                records=records,
                package_root=self.package,
                current_paths=paths,
                verify_artifact_reference=_verify,
                sha256_file=_sha,
            )
            self.assertEqual("legacy-run19", mode)
            paths["skill/run_v2.py"].write_bytes(b"future drift")
            with self.assertRaises(identity.StageImplementationIdentityError):
                identity.validate_stage_catalog(
                    stage="X1",
                    records=records,
                    package_root=self.package,
                    current_paths=paths,
                    verify_artifact_reference=_verify,
                    sha256_file=_sha,
                )

    def test_legacy_extra_or_resealed_catalog_is_rejected(self) -> None:
        paths = {
            identity.IDENTITY_MODULE: self._write("authority.py", b"authority", current=True),
            "skill/run_v2.py": self._write("runner.py", b"runner", current=True),
        }
        records = [self._record("skill/run_v2.py", b"runner")]
        contract = {
            "canonical_digest": identity.canonical_catalog_digest(records),
            "removed_identities": frozenset(),
            "approved_mismatches": {},
        }
        records.append(self._record("extra/arbitrary.py", b"arbitrary"))
        with mock.patch.dict(identity.TRUSTED_LEGACY_CATALOGS, {"X1": contract}):
            with self.assertRaises(identity.StageImplementationIdentityError):
                identity.validate_stage_catalog(
                    stage="X1",
                    records=records,
                    package_root=self.package,
                    current_paths=paths,
                    verify_artifact_reference=_verify,
                    sha256_file=_sha,
                )

    def test_stage_catalogs_exclude_transitive_upstream_implementation(self) -> None:
        modules = {
            "S1": "skills.novel-storyline-architecture-designer.scripts.run_v2",
            "W1": "skills.novel-world-model-designer.scripts.run_v2",
            "E1": "skills.novel-environment-system-designer.scripts.run_v2",
            "T1": "skills.novel-event-timeline-designer.scripts.run_v2",
            "C1": "skills.novel-character-system-designer.scripts.run_v2",
            "Q1": "skills.novel-conception-reviewer.scripts.run_v2",
            "P1": "skills.novel-conception-deliverable-assembler.scripts.run_v2",
        }
        own_schemas = {
            "S1": "schemas/storyline-architecture.schema.json",
            "W1": "schemas/world-model.schema.json",
            "E1": "schemas/environment-system.schema.json",
            "T1": "schemas/event-timeline.schema.json",
            "C1": "schemas/character-system.schema.json",
            "Q1": "schemas/conception-review.schema.json",
            "P1": "schemas/novel-conception-package.schema.json",
        }
        for stage, module_name in modules.items():
            with self.subTest(stage=stage):
                identities = set(importlib.import_module(module_name)._implementation_paths())
                self.assertIn(identity.IDENTITY_MODULE, identities)
                self.assertIn(own_schemas[stage], identities)
                self.assertFalse(any(item.startswith("upstream/") for item in identities))
                if stage in {"S1", "W1", "E1", "T1", "C1"}:
                    self.assertNotIn("runtime/baseline.py", identities)
                    self.assertNotIn("runtime/b0_completion.py", identities)


if __name__ == "__main__":
    unittest.main()
