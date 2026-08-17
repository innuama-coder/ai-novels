"""Build and verify the frozen novel-conception-stage product release."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


VERSION = "1.0.0"
_EPOCH = (2020, 1, 1, 0, 0, 0)
_EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", "dist", "releases"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
_INTERVIEW_SKILLS = (
    "novel-intent-facilitator",
    "novel-subject-designer",
    "novel-world-interviewer",
    "novel-character-interviewer",
    "novel-causality-architect",
    "novel-narrative-contract-designer",
    "novel-interview-integrity-auditor",
    "novel-interview-brief-generator",
)
_RELEASE_DOCS = (
    "conception-stage-release.json",
    "release-notes-1.0.0.md",
    "conception-orchestration.md",
    "conception-autonomous-workflow-v2.md",
    "conception-chain-final-audit.md",
)


class StageReleaseError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
        and not (_EXCLUDED_PARTS & set(path.relative_to(root).parts))
        and path.suffix not in _EXCLUDED_SUFFIXES
    ]


def _copy_tree(source: Path, target: Path) -> None:
    for path in _source_files(source):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def _read_interview_manifest(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    values: dict[str, str] = {}
    for key in ("name", "version", "status", "release_date"):
        match = re.search(rf"^{key}:\s*(.+?)\s*$", text, re.MULTILINE)
        if match is None:
            raise StageReleaseError(f"STAGE_RELEASE_INTERVIEW_{key.upper()}_MISSING")
        values[key] = match.group(1).strip().strip("\"'")
    return values


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise StageReleaseError(f"STAGE_RELEASE_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _validate_versions(repository: Path) -> dict:
    release_path = repository / "docs" / "ai-novel-workflow" / "conception-stage-release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if (
        release.get("name") != "novel-conception-stage"
        or release.get("version") != VERSION
        or release.get("status") != "frozen"
    ):
        raise StageReleaseError("STAGE_RELEASE_VERSION_SOURCE_INVALID")
    interview = _read_interview_manifest(
        repository / "harnesses" / "novel-conception-interview" / "manifest.yaml"
    )
    autonomous = json.loads(
        (repository / "harnesses" / "novel-conception-autonomous" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    for component, actual in (("interview", interview), ("autonomous", autonomous)):
        expected = release["components"][component]
        if any(actual.get(key) != expected[key] for key in ("name", "version")):
            raise StageReleaseError(f"STAGE_RELEASE_COMPONENT_VERSION_MISMATCH:{component}")
        if actual.get("status") != "frozen":
            raise StageReleaseError(f"STAGE_RELEASE_COMPONENT_NOT_FROZEN:{component}")
        if actual.get("release_date") != release["release_date"]:
            raise StageReleaseError(f"STAGE_RELEASE_COMPONENT_DATE_MISMATCH:{component}")
    if tuple(release["components"]["interview"].get("skills", ())) != _INTERVIEW_SKILLS:
        raise StageReleaseError("STAGE_RELEASE_INTERVIEW_SKILL_SET_INVALID")
    if tuple(release["components"]["autonomous"].get("skills", ())) != _official_autonomous_skills(repository):
        raise StageReleaseError("STAGE_RELEASE_AUTONOMOUS_SKILL_SET_INVALID")
    return release


def _official_autonomous_skills(repository: Path) -> tuple[str, ...]:
    spec = json.loads(
        (repository / "harnesses" / "novel-conception-autonomous" / "dependency-spec.json").read_text(
            encoding="utf-8"
        )
    )
    names = [item["skill"] for item in spec["stage_owners"]]
    names.extend(item["skill"] for item in spec.get("quality_gate_dependencies", ()))
    return tuple(dict.fromkeys(names))


def _stage_source(repository: Path, target: Path) -> None:
    release = _validate_versions(repository)
    docs_source = repository / "docs" / "ai-novel-workflow"
    docs_target = target / "docs" / "ai-novel-workflow"
    docs_target.mkdir(parents=True, exist_ok=True)
    for relative in _RELEASE_DOCS:
        shutil.copyfile(docs_source / relative, docs_target / relative)
    _copy_tree(docs_source / "contracts", docs_target / "contracts")
    for harness_name in ("novel-conception-interview", "novel-conception-autonomous"):
        _copy_tree(
            repository / "harnesses" / harness_name,
            target / "harnesses" / harness_name,
        )
    skills = tuple(dict.fromkeys(
        tuple(release["components"]["interview"]["skills"])
        + tuple(release["components"]["autonomous"]["skills"])
    ))
    for skill in skills:
        source = repository / "skills" / skill
        if not (source / "SKILL.md").is_file():
            raise StageReleaseError(f"STAGE_RELEASE_SKILL_MISSING:{skill}")
        _copy_tree(source, target / "skills" / skill)


def _zip_tree(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in _source_files(source):
            relative = Path(f"novel-conception-stage-{VERSION}") / path.relative_to(source)
            info = zipfile.ZipInfo(relative.as_posix(), _EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def _validate_source_bundle(root: Path) -> None:
    release = _validate_versions(root)
    if tuple(release.get("workflow", ()))[:2] != ("I0", "I1") or release.get("terminal") != "final":
        raise StageReleaseError("STAGE_RELEASE_WORKFLOW_INVALID")
    interview_validator = root / "harnesses" / "novel-conception-interview" / "validators" / "validate_harness.py"
    result = subprocess.run(
        [sys.executable, str(interview_validator), str(interview_validator.parents[1])],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise StageReleaseError("STAGE_RELEASE_INTERVIEW_INVALID:" + result.stdout + result.stderr)
    autonomous_root = root / "harnesses" / "novel-conception-autonomous"
    validator = _load_module("_stage_release_validator", autonomous_root / "validators" / "validate_harness.py")
    report = validator.validate_harness(autonomous_root)
    if not report.ok:
        raise StageReleaseError("STAGE_RELEASE_AUTONOMOUS_INVALID:" + ",".join(report.errors))
    expected = set(
        release["components"]["interview"]["skills"]
        + release["components"]["autonomous"]["skills"]
    )
    actual = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    if actual != expected:
        raise StageReleaseError("STAGE_RELEASE_SKILL_SET_INVALID")


def _build_component_archives(repository: Path, destination: Path) -> None:
    interview_root = repository / "harnesses" / "novel-conception-interview"
    result = subprocess.run(
        [sys.executable, str(interview_root / "tools" / "build_release.py"), str(interview_root)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise StageReleaseError("STAGE_RELEASE_INTERVIEW_BUILD_FAILED:" + result.stdout + result.stderr)
    interview_target = destination / "components" / "interview"
    interview_target.mkdir(parents=True, exist_ok=True)
    for path in sorted((interview_root / "dist").glob(f"*{VERSION}*.zip")):
        shutil.copyfile(path, interview_target / path.name)
    shutil.copyfile(interview_root / "dist" / "release-manifest.yaml", interview_target / "release-manifest.yaml")

    autonomous_root = repository / "harnesses" / "novel-conception-autonomous"
    autonomous_target = destination / "components" / "autonomous"
    builder = _load_module("_stage_release_builder", autonomous_root / "tools" / "build_release.py")
    builder.build_release(autonomous_root, autonomous_target)


def _validate_component_manifests(destination: Path) -> None:
    autonomous_root = destination / "components" / "autonomous"
    autonomous = json.loads((autonomous_root / "release-manifest.json").read_text(encoding="utf-8"))
    if (
        autonomous.get("version") != VERSION
        or autonomous.get("status") != "frozen"
        or autonomous.get("release_date") != "2026-08-05"
    ):
        raise StageReleaseError("STAGE_RELEASE_AUTONOMOUS_COMPONENT_MANIFEST_INVALID")
    for item in autonomous.get("artifacts", ()):
        path = autonomous_root / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise StageReleaseError("STAGE_RELEASE_AUTONOMOUS_COMPONENT_CHECKSUM_INVALID")

    interview_root = destination / "components" / "interview"
    text = (interview_root / "release-manifest.yaml").read_text(encoding="utf-8")
    if (
        f"version: {VERSION}" not in text
        or "status: frozen" not in text
        or "release_date: 2026-08-05" not in text
    ):
        raise StageReleaseError("STAGE_RELEASE_INTERVIEW_COMPONENT_MANIFEST_INVALID")
    entries = re.findall(r"^\s+artifact:\s*(\S+)\n\s+sha256:\s*([0-9a-f]{64})$", text, re.MULTILINE)
    if len(entries) != 6:
        raise StageReleaseError("STAGE_RELEASE_INTERVIEW_COMPONENT_ARTIFACTS_INVALID")
    for relative, digest in entries:
        path = interview_root / relative
        if not path.is_file() or _sha256(path) != digest:
            raise StageReleaseError("STAGE_RELEASE_INTERVIEW_COMPONENT_CHECKSUM_INVALID")


def build_release(repository=None, output_dir=None) -> dict:
    repo = Path(repository).resolve() if repository else Path(__file__).resolve().parents[3]
    release = _validate_versions(repo)
    destination = (
        Path(output_dir).resolve()
        if output_dir
        else repo / "docs" / "ai-novel-workflow" / "releases" / VERSION
    )
    destination.mkdir(parents=True, exist_ok=True)
    _build_component_archives(repo, destination)
    _validate_component_manifests(destination)
    with tempfile.TemporaryDirectory(prefix="conception-stage-release-") as temporary:
        stage = Path(temporary) / f"novel-conception-stage-{VERSION}"
        _stage_source(repo, stage)
        _validate_source_bundle(stage)
        source_zip = destination / f"novel-conception-stage-{VERSION}-source.zip"
        _zip_tree(stage, source_zip)
        extract = Path(temporary) / "extract"
        with zipfile.ZipFile(source_zip) as archive:
            for member in archive.infolist():
                path = Path(member.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise StageReleaseError("STAGE_RELEASE_ARCHIVE_PATH_INVALID")
            archive.extractall(extract)
        roots = [path for path in extract.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise StageReleaseError("STAGE_RELEASE_ARCHIVE_ROOT_INVALID")
        _validate_source_bundle(roots[0])

    notes = destination / "RELEASE-NOTES.md"
    shutil.copyfile(repo / "docs" / "ai-novel-workflow" / "release-notes-1.0.0.md", notes)
    root_manifest = destination / "release-manifest.json"
    root_sums = destination / "SHA256SUMS"
    artifact_paths = [
        path for path in sorted(destination.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file() and path not in {root_manifest, root_sums}
    ]
    artifacts = [
        {
            "path": path.relative_to(destination).as_posix(),
            "sha256": _sha256(path),
            "size": path.stat().st_size,
        }
        for path in artifact_paths
    ]
    manifest = {
        "schema_version": "1.0",
        "name": release["name"],
        "version": VERSION,
        "status": "frozen",
        "release_date": release["release_date"],
        "artifacts": artifacts,
        "validation": {
            "version_coherence": "pass",
            "source_tree": "pass",
            "source_archive_revalidation": "pass",
            "component_release_builds": "pass",
            "checksums": "pass",
        },
    }
    manifest_path = root_manifest
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="")
    sums = root_sums
    sums.write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in artifacts), encoding="utf-8", newline="")
    if any(_sha256(destination / item["path"]) != item["sha256"] for item in artifacts):
        raise StageReleaseError("STAGE_RELEASE_CHECKSUM_MISMATCH")
    return manifest


def main() -> int:
    try:
        manifest = build_release(
            sys.argv[1] if len(sys.argv) > 1 else None,
            sys.argv[2] if len(sys.argv) > 2 else None,
        )
    except (StageReleaseError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
