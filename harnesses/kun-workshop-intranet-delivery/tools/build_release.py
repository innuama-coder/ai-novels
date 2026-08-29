#!/usr/bin/env python3
"""Build source and runtime release packages for a portable harness."""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RUNTIMES = {
    "codex": "system-prompt.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "openclaw": "OPENCLAW.md",
    "hermas": "HERMAS.md",
}

SOURCE_EXCLUDE_PARTS = {".git", "dist", "__pycache__"}
RUNTIME_COMMON_FILES = ["agent.md", "workflow.md", "rules.md", "manifest.yaml", "README.md"]
RUNTIME_COMMON_DIRS = ["schemas", "validators", "evals"]
RUNTIME_DOCS = [
    "docs/application-spec.md",
    "docs/adapter-authoring-guide.md",
    "docs/compatibility-matrix.md",
    "docs/evaluation-rubric.md",
    "docs/release-model.md",
]
RUNTIME_MANIFEST_FIELDS = [
    "schema_version",
    "kind",
    "source_harness",
    "source_version",
    "runtime",
    "adapter_path",
    "entry_file",
    "validation_status",
    "known_degradations_file",
    "built_at_utc",
]


def read_manifest_value(manifest: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", manifest, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def run_source_validator(root: Path) -> None:
    validator = root / "validators" / "validate_harness.py"
    if not validator.is_file():
        raise RuntimeError("missing source validator: validators/validate_harness.py")
    result = subprocess.run([sys.executable, str(validator), str(root)], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("source validation failed:\n" + result.stdout + result.stderr)


def should_include_source(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    if any(part in SOURCE_EXCLUDE_PARTS for part in parts):
        return False
    if len(parts) >= 2 and parts[0] == "examples" and (root / "examples" / parts[1]).is_dir():
        return False
    return True


def zip_dir(source: Path, target_zip: Path) -> None:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(source.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(source).as_posix())


def zip_source(root: Path, target_zip: Path) -> None:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(root.rglob("*")):
            if file.is_file() and should_include_source(file, root):
                zf.write(file, file.relative_to(root).as_posix())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_artifact(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def copy_file(root: Path, rel: str, dest: Path) -> None:
    src = root / rel
    if src.is_file():
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)


def copy_dir(root: Path, rel: str, dest: Path) -> None:
    src = root / rel
    if src.is_dir():
        target = dest / rel
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)


def write_runtime_manifest(dest: Path, name: str, version: str, runtime: str, entry_file: str) -> None:
    content = f"""schema_version: 1
kind: runtime-build
source_harness: {name}
source_version: {version}
runtime: {runtime}
adapter_path: adapters/{runtime}
entry_file: adapters/{runtime}/{entry_file}
validation_status: runtime_validated
known_degradations_file: adapters/{runtime}/mapping.md
built_at_utc: {datetime.now(timezone.utc).isoformat()}
"""
    (dest / "MANIFEST.runtime.yaml").write_text(content, encoding="utf-8")


def validate_runtime_dir(dest: Path, runtime: str, entry_file: str) -> list[str]:
    required = [
        "agent.md",
        "workflow.md",
        "rules.md",
        "manifest.yaml",
        "MANIFEST.runtime.yaml",
        "schemas/handoff.schema.json",
        "validators/validate_harness.py",
        f"adapters/{runtime}/install.md",
        f"adapters/{runtime}/mapping.md",
        f"adapters/{runtime}/{entry_file}",
    ]
    errors = [f"missing runtime file: {rel}" for rel in required if not (dest / rel).is_file()]
    manifest_path = dest / "MANIFEST.runtime.yaml"
    if manifest_path.is_file():
        text = manifest_path.read_text(encoding="utf-8-sig")
        for field in RUNTIME_MANIFEST_FIELDS:
            if not re.search(rf"^{re.escape(field)}:\s*.+$", text, re.MULTILINE):
                errors.append(f"runtime manifest missing field: {field}")
        expected = {
            "runtime": runtime,
            "entry_file": f"adapters/{runtime}/{entry_file}",
            "validation_status": "runtime_validated",
        }
        for field, value in expected.items():
            actual = read_manifest_value(text, field)
            if actual != value:
                errors.append(f"runtime manifest field {field} expected {value!r}, got {actual!r}")
    return errors


def validate_runtime_zip(zip_path: Path, runtime: str, entry_file: str) -> list[str]:
    required = {
        "MANIFEST.runtime.yaml",
        "agent.md",
        "workflow.md",
        "rules.md",
        "schemas/handoff.schema.json",
        "validators/validate_harness.py",
        f"adapters/{runtime}/install.md",
        f"adapters/{runtime}/mapping.md",
        f"adapters/{runtime}/{entry_file}",
    }
    if not zip_path.is_file():
        return [f"missing runtime zip: {zip_path}"]
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
    return [f"runtime zip missing file: {rel}" for rel in sorted(required - names)]


def build_runtime(root: Path, staging_root: Path, dist: Path, name: str, version: str, runtime: str, entry_file: str) -> tuple[Path, list[str]]:
    adapter = root / "adapters" / runtime
    required = [adapter / "install.md", adapter / "mapping.md", adapter / entry_file]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"runtime {runtime} is missing required files: {', '.join(missing)}")

    dest = staging_root / f"{name}-{version}-{runtime}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for rel in RUNTIME_COMMON_FILES:
        copy_file(root, rel, dest)
    for rel in RUNTIME_COMMON_DIRS:
        copy_dir(root, rel, dest)
    for rel in RUNTIME_DOCS:
        copy_file(root, rel, dest)

    copy_dir(root, f"adapters/{runtime}", dest)
    write_runtime_manifest(dest, name, version, runtime, entry_file)

    errors = validate_runtime_dir(dest, runtime, entry_file)
    if errors:
        raise RuntimeError(f"runtime {runtime} staging validation failed:\n" + "\n".join(errors))

    target_zip = dist / f"{name}-{version}-{runtime}.zip"
    if target_zip.exists():
        target_zip.unlink()
    zip_dir(dest, target_zip)

    errors = validate_runtime_zip(target_zip, runtime, entry_file)
    if errors:
        raise RuntimeError(f"runtime {runtime} zip validation failed:\n" + "\n".join(errors))
    return target_zip, ["staging validation passed", "zip validation passed"]


def write_release_manifest(root: Path, dist: Path, name: str, version: str, source_zip: Path, builds: dict[str, dict[str, object]]) -> Path:
    lines = [
        "schema_version: 1",
        f"name: {name}",
        f"version: {version}",
        f"built_at_utc: {datetime.now(timezone.utc).isoformat()}",
        "source:",
        f"  artifact: {relative_artifact(root, source_zip)}",
        f"  sha256: {sha256_file(source_zip)}",
        "  status: pass",
        "builds:",
    ]
    for runtime, info in builds.items():
        artifact = info["artifact"]
        assert isinstance(artifact, Path)
        lines.extend([
            f"  {runtime}:",
            f"    artifact: {relative_artifact(root, artifact)}",
            f"    sha256: {sha256_file(artifact)}",
            "    status: pass",
            "    validation:",
        ])
        for evidence in info["validation"]:
            lines.append(f"      - {evidence}")
    out = dist / "release-manifest.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build harness release packages.")
    parser.add_argument("root", nargs="?", default=".", help="Harness root")
    parser.add_argument("--runtime", choices=[*RUNTIMES.keys(), "all"], default="all", help="Runtime to build")
    parser.add_argument("--skip-source-validation", action="store_true", help="Skip source structural validation")
    parser.add_argument("--keep-staging", action="store_true", help="Keep dist/_staging after a successful build")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise SystemExit("missing manifest.yaml")

    manifest = manifest_path.read_text(encoding="utf-8-sig")
    name = read_manifest_value(manifest, "name")
    version = read_manifest_value(manifest, "version")
    if not name or not version:
        raise SystemExit("manifest.yaml must contain name and version")

    if not args.skip_source_validation:
        run_source_validator(root)

    dist = root / "dist"
    staging = dist / "_staging"
    dist.mkdir(exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    source_zip = dist / f"{name}-{version}-source.zip"
    if source_zip.exists():
        source_zip.unlink()
    zip_source(root, source_zip)

    selected = RUNTIMES.keys() if args.runtime == "all" else [args.runtime]
    builds: dict[str, dict[str, object]] = {}
    try:
        for runtime in selected:
            artifact, validation = build_runtime(root, staging, dist, name, version, runtime, RUNTIMES[runtime])
            builds[runtime] = {"artifact": artifact, "validation": validation}
        release_manifest = write_release_manifest(root, dist, name, version, source_zip, builds)
    finally:
        if staging.exists() and not args.keep_staging:
            shutil.rmtree(staging)

    print(f"Built source: {source_zip}")
    for runtime, info in builds.items():
        print(f"Built {runtime}: {info['artifact']}")
    print(f"Wrote release manifest: {release_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

