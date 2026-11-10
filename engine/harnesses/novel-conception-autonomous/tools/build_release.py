"""Build and revalidate deterministic source and Codex release archives."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


_EPOCH = (2020, 1, 1, 0, 0, 0)
_EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "releases"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_OFFICIAL_SKILLS = (
    "novel-storyline-architecture-designer",
    "novel-world-model-designer",
    "novel-environment-system-designer",
    "novel-event-timeline-designer",
    "novel-character-system-designer",
    "novel-conception-reviewer",
    "novel-conception-deliverable-assembler",
    "novel-conception-human-review-assembler",
    "novel-conception-fragment-writer",
    "novel-conception-presentation-fidelity-reviewer",
    "novel-conception-review-html-generator",
)


class ReleaseBuildError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(root: Path) -> list[Path]:
    return [
        path for path in sorted(root.rglob("*"), key=lambda p: p.as_posix())
        if path.is_file()
        and not (_EXCLUDED_PARTS & set(path.relative_to(root).parts))
        and path.suffix not in _EXCLUDED_SUFFIXES
    ]


def _copy_source(root: Path, target: Path) -> None:
    for source in _source_files(root):
        relative = source.relative_to(root)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _copy_schemas(repo_root: Path, target: Path) -> None:
    authority = (
        repo_root / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
    )
    schemas = sorted(authority.glob("*.json"), key=lambda p: p.name)
    if not schemas:
        raise ReleaseBuildError("HARN_RELEASE_SCHEMA_SOURCE_MISSING")
    schema_target = target / "schemas" / "bundled"
    schema_target.mkdir(parents=True, exist_ok=True)
    for source in schemas:
        shutil.copyfile(source, schema_target / source.name)


def _load_validator(root: Path):
    path = root / "validators" / "validate_harness.py"
    name = f"_harness_validator_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReleaseBuildError("HARN_RELEASE_VALIDATOR_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_dependency_validator(root: Path):
    path = root / "validators" / "validate_dependencies.py"
    name = f"_dependency_validator_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReleaseBuildError("HARN_RELEASE_DEPENDENCY_VALIDATOR_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _validate(root: Path) -> tuple[str, ...]:
    report = _load_validator(root).validate_harness(root)
    if not report.ok:
        raise ReleaseBuildError(
            "HARN_RELEASE_VALIDATION_FAILED:" + ",".join(report.errors)
        )
    bundled = root / "schemas" / "bundled"
    if not bundled.is_dir() or not list(bundled.glob("*.schema.json")):
        raise ReleaseBuildError("HARN_RELEASE_BUNDLED_SCHEMAS_MISSING")
    return tuple(report.checked)


def _validate_bundle(bundle_root: Path) -> tuple[str, ...]:
    harness_root = bundle_root / "harnesses" / "novel-conception-autonomous"
    harness_checks = _validate(harness_root)
    dependency_report = _load_dependency_validator(harness_root).validate_dependencies(
        harness_root, require_lock=True
    )
    if not dependency_report.ok:
        raise ReleaseBuildError(
            "HARN_RELEASE_DEPENDENCY_VALIDATION_FAILED:"
            + ",".join(dependency_report.errors)
        )
    skill_names = {
        path.parent.name
        for path in (bundle_root / "skills").glob("*/SKILL.md")
    }
    if skill_names != set(_OFFICIAL_SKILLS):
        raise ReleaseBuildError("HARN_RELEASE_SKILL_SET_INVALID")
    if "novel-development-map-designer" in skill_names:
        raise ReleaseBuildError("HARN_RELEASE_LEGACY_SKILL_PRESENT")
    return tuple(harness_checks) + tuple(dependency_report.checked)


def _copy_repository_dependencies(
    repository: Path, harness_root: Path, bundle_root: Path
) -> None:
    harness_target = bundle_root / "harnesses" / "novel-conception-autonomous"
    _copy_source(harness_root, harness_target)
    for skill_name in _OFFICIAL_SKILLS:
        source = repository / "skills" / skill_name
        if not (source / "SKILL.md").is_file():
            raise ReleaseBuildError(f"HARN_RELEASE_SKILL_MISSING:{skill_name}")
        _copy_source(source, bundle_root / "skills" / skill_name)
    docs_source = repository / "docs" / "ai-novel-workflow"
    docs_target = bundle_root / "docs" / "ai-novel-workflow"
    workflow = docs_source / "conception-autonomous-workflow-v2.md"
    if not workflow.is_file():
        raise ReleaseBuildError("HARN_RELEASE_WORKFLOW_MISSING")
    docs_target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(workflow, docs_target / workflow.name)
    contracts = docs_source / "contracts" / "autonomous-v2"
    _copy_source(contracts, docs_target / "contracts" / "autonomous-v2")
    _copy_schemas(repository, harness_target)
    shutil.copyfile(
        harness_target / "adapters" / "codex" / "SKILL.md",
        bundle_root / "SKILL.md",
    )
    dependency_module = _load_dependency_validator(harness_target)
    dependency_spec = dependency_module.load_dependency_spec(harness_target)
    dependency_lock = dependency_module.build_dependency_lock(
        bundle_root, dependency_spec
    )
    (harness_target / "dependency-lock.json").write_text(
        json.dumps(
            dependency_lock, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n",
        encoding="utf-8",
        newline="",
    )


def _zip_tree(source: Path, destination: Path, prefix: str) -> None:
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in _source_files(source):
            relative = Path(prefix) / path.relative_to(source)
            info = zipfile.ZipInfo(relative.as_posix(), _EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def _extract_and_validate(archive: Path, temporary: Path) -> tuple[str, ...]:
    extract_root = temporary / archive.stem
    with zipfile.ZipFile(archive, "r") as handle:
        for member in handle.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ReleaseBuildError("HARN_RELEASE_ARCHIVE_PATH_INVALID")
        handle.extractall(extract_root)
    candidates = [path for path in extract_root.iterdir() if path.is_dir()]
    if len(candidates) != 1:
        raise ReleaseBuildError("HARN_RELEASE_ARCHIVE_ROOT_INVALID")
    return _validate_bundle(candidates[0])


def build_release(root=None, output_dir=None):
    harness_root = (
        Path(root).resolve()
        if root is not None
        else Path(__file__).resolve().parents[1]
    )
    repository = harness_root.parents[1]
    destination = (
        Path(output_dir).resolve()
        if output_dir is not None
        else harness_root / "releases"
    )
    destination.mkdir(parents=True, exist_ok=True)
    try:
        product_manifest = json.loads(
            (harness_root / "manifest.yaml").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseBuildError("HARN_RELEASE_PRODUCT_MANIFEST_INVALID") from error
    version = product_manifest.get("version")
    if version != "1.0.0" or product_manifest.get("status") != "frozen":
        raise ReleaseBuildError("HARN_RELEASE_PRODUCT_VERSION_INVALID")
    source_report = _load_validator(harness_root).validate_harness(harness_root)
    if not source_report.ok:
        raise ReleaseBuildError(
            "HARN_RELEASE_SOURCE_INVALID:" + ",".join(source_report.errors)
        )

    with tempfile.TemporaryDirectory(prefix="novel-conception-release-") as temp:
        temporary = Path(temp)
        source_stage = temporary / "source" / "novel-conception-autonomous"
        codex_stage = temporary / "codex" / "novel-conception-autonomous"
        _copy_repository_dependencies(
            repository, harness_root, source_stage
        )
        _copy_repository_dependencies(
            repository, harness_root, codex_stage
        )
        staged_checks = {
            "source": _validate_bundle(source_stage),
            "codex": _validate_bundle(codex_stage),
        }
        source_zip = destination / f"novel-conception-autonomous-{version}-source.zip"
        codex_zip = destination / f"novel-conception-autonomous-{version}-codex.zip"
        _zip_tree(source_stage, source_zip, "novel-conception-autonomous")
        _zip_tree(codex_stage, codex_zip, "novel-conception-autonomous")
        zip_checks = {
            "source": _extract_and_validate(source_zip, temporary),
            "codex": _extract_and_validate(codex_zip, temporary),
        }

    artifacts = []
    for path in (source_zip, codex_zip):
        artifacts.append({
            "path": path.relative_to(destination).as_posix(),
            "sha256": _sha256(path),
            "size": path.stat().st_size,
        })
    manifest = {
        "schema_version": "2.0",
        "name": "novel-conception-autonomous",
        "version": version,
        "status": "frozen",
        "release_date": product_manifest["release_date"],
        "artifacts": artifacts,
        "validation": {
            "source_checked": list(source_report.checked),
            "staging_checked": {k: list(v) for k, v in staged_checks.items()},
            "zip_checked": {k: list(v) for k, v in zip_checks.items()},
        },
    }
    manifest_path = destination / "release-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="",
    )
    reread = json.loads(manifest_path.read_text(encoding="utf-8"))
    if reread != manifest or any(Path(item["path"]).is_absolute() for item in artifacts):
        raise ReleaseBuildError("HARN_RELEASE_MANIFEST_INVALID")
    for item in artifacts:
        path = destination / item["path"]
        if _sha256(path) != item["sha256"] or path.stat().st_size != item["size"]:
            raise ReleaseBuildError("HARN_RELEASE_CHECKSUM_MISMATCH")
    return manifest


def main() -> int:
    try:
        manifest = build_release(
            sys.argv[1] if len(sys.argv) > 1 else None,
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
    except ReleaseBuildError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
