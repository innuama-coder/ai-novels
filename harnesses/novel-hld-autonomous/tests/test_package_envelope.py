from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.canonical import ContractError, canonical_bytes, canonical_json  # noqa: E402
from runtime.package_envelope import validate_completion_bindings, validate_manifest  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


class PackageEnvelopeTests(unittest.TestCase):
    def test_canonical_bytes_is_canonical_json_document_encoding(self) -> None:
        value = {"中文": [2, 1], "a": True}
        self.assertEqual(canonical_bytes(value), (canonical_json(value) + "\n").encode("utf-8"))

    def test_completion_is_outside_manifest_content_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            package = workspace / "package"
            package.mkdir()
            write(package / "canonical.json", {"ready": True})
            write(package / "validation.json", {"status": "pass"})
            refs = [
                {"role": "canonical", "path": "canonical.json", "sha256": digest(package / "canonical.json")},
                {"role": "validation", "path": "validation.json", "sha256": digest(package / "validation.json")},
            ]
            manifest = {"files": refs, "artifact_roles": {item["role"]: item for item in refs}}
            write(package / "package-manifest.json", manifest)
            completion = {
                "manifest_ref": {"role": "package_manifest", "path": "package/package-manifest.json", "sha256": digest(package / "package-manifest.json")},
                "validation_ref": {"role": "validation", "path": "package/validation.json", "sha256": digest(package / "validation.json")},
                "canonical_artifacts": [{"role": "canonical", "path": "package/canonical.json", "sha256": digest(package / "canonical.json")}],
            }
            write(package / "stage-completion.json", completion)
            validate_manifest(package, manifest)
            validate_completion_bindings(workspace, package, completion)

    def test_completion_artifact_must_be_manifest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            package = workspace / "package"
            package.mkdir()
            write(package / "canonical.json", {"ready": True})
            write(package / "validation.json", {"status": "pass"})
            refs = [
                {"role": "canonical", "path": "canonical.json", "sha256": digest(package / "canonical.json")},
                {"role": "validation", "path": "validation.json", "sha256": digest(package / "validation.json")},
            ]
            manifest = {"files": refs, "artifact_roles": {item["role"]: item for item in refs}}
            write(package / "package-manifest.json", manifest)
            completion = {
                "manifest_ref": {"role": "package_manifest", "path": "package/package-manifest.json", "sha256": digest(package / "package-manifest.json")},
                "validation_ref": {"role": "validation", "path": "package/validation.json", "sha256": digest(package / "validation.json")},
                # The manifest file exists and is hash-valid, but it is
                # intentionally outside its own acyclic content closure.
                "canonical_artifacts": [{"role": "canonical", "path": "package/package-manifest.json", "sha256": digest(package / "package-manifest.json")}],
            }
            write(package / "stage-completion.json", completion)
            with self.assertRaisesRegex(ContractError, "not manifest-bound"):
                validate_completion_bindings(workspace, package, completion)


if __name__ == "__main__":
    unittest.main()
