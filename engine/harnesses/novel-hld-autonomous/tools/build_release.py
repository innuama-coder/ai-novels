#!/usr/bin/env python3
"""Build reproducible, repository-layout, self-contained HLD archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
VERSION = "0.1.0"
NAME = "novel-hld-autonomous"
BUNDLE = f"{NAME}-{VERSION}"
EXCLUDED_PARTS = {"dist", "__pycache__", ".pytest_cache"}
LEGACY_SKILLS = {"novel-hld-writer"}


def release_state(root: Path = ROOT) -> tuple[str, str]:
    manifest=(root/"manifest.yaml").read_text(encoding="utf-8")
    runtime=(root/"MANIFEST.runtime.yaml").read_text(encoding="utf-8")
    status_match=re.search(r"^status: ([a-z-]+)$",manifest,flags=re.MULTILINE)
    qualification_match=re.search(r"^agentic_qualification: ([a-z-]+)$",runtime,flags=re.MULTILINE)
    if not status_match or not qualification_match:raise RuntimeError("release state is unavailable")
    status=status_match.group(1);qualification=qualification_match.group(1)
    if (status,qualification) not in {("implementation-candidate","not-run"),("release-candidate","qualified")}:raise RuntimeError("release state and qualification drift")
    return status,qualification


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registered_skills(root: Path = ROOT) -> tuple[str, ...]:
    registry = json.loads((root / "references/public-runtime-registry.json").read_text(encoding="utf-8"))["entries"]
    names = tuple(sorted({entry["skill"] for entry in registry.values() if not entry["skill"].startswith("harness-core/")}))
    if len(names) != 15 or not all(name.startswith("novel-hld-") for name in names) or LEGACY_SKILLS.intersection(names):
        raise RuntimeError(f"release skill closure is not the exact 15-skill public registry: {names}")
    return names


def _files_under(base: Path) -> list[Path]:
    return [path for path in base.rglob("*") if path.is_file() and not any(part in EXCLUDED_PARTS for part in path.relative_to(base).parts)]


def source_files(root: Path = ROOT) -> list[tuple[Path, str]]:
    repo = root.parents[1]
    files = _files_under(root)
    for skill in registered_skills(root):
        skill_root = repo / "skills" / skill
        if not skill_root.is_dir():
            raise RuntimeError(f"registered release skill is unavailable: {skill}")
        files.extend(_files_under(skill_root))
    rows = {(path.resolve(), path.resolve().relative_to(repo.resolve()).as_posix()) for path in files}
    return sorted(rows, key=lambda row: row[1])


def runtime_files(root: Path = ROOT) -> list[tuple[Path, str]]:
    status,_=release_state(root)
    rows = []
    for path, relative in source_files(root):
        harness_relative = relative.removeprefix("harnesses/novel-hld-autonomous/")
        if harness_relative.startswith("adapters/") and not harness_relative.startswith("adapters/codex/"):
            continue
        if "/tests/" in f"/{relative}" or (status=="implementation-candidate" and harness_relative.startswith("releases/") and harness_relative!="releases/0.1.0-acceptance.json"):
            continue
        rows.append((path, relative))
    return rows


def write_zip(destination: Path, files: list[tuple[Path, str]]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, relative in files:
            info = zipfile.ZipInfo(f"{BUNDLE}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def validate_zip(path: Path, required: set[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        missing = sorted(required - set(names))
        if missing:
            raise RuntimeError(f"archive missing required files: {missing}")
        if len(names) != len(set(names)) or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise RuntimeError("archive contains duplicate or unsafe paths")
        if any(f"/{legacy}/" in name for legacy in LEGACY_SKILLS for name in names):
            raise RuntimeError("archive contains a forbidden legacy skill")
        if archive.testzip() is not None:
            raise RuntimeError("archive CRC validation failed")


def post_install_validate(archive: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="hld-release-") as raw:
        destination = Path(raw)
        with zipfile.ZipFile(archive) as package:
            package.extractall(destination)
        bundle = destination / BUNDLE
        command = bundle / "harnesses/novel-hld-autonomous/tools/post_install_validate.py"
        completed = subprocess.run([sys.executable, str(command)], cwd=bundle, text=True, capture_output=True, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"post-install acceptance failed: {completed.stdout or completed.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    completed = subprocess.run([sys.executable, str(ROOT / "validators/validate_harness.py"), str(ROOT), "--json"], text=True, capture_output=True, encoding="utf-8")
    if completed.returncode:
        print(completed.stdout or completed.stderr, file=sys.stderr)
        return 1
    output = args.output.resolve();output.mkdir(parents=True, exist_ok=True)
    source_zip = output / f"{NAME}-{VERSION}-source.zip";codex_zip = output / f"{NAME}-{VERSION}-codex.zip"
    write_zip(source_zip, source_files());write_zip(codex_zip, runtime_files())
    prefix = f"{BUNDLE}/";harness = prefix + "harnesses/novel-hld-autonomous/"
    common = {harness + value for value in ("manifest.yaml", "MANIFEST.runtime.yaml", "agent.md", "workflow.md", "rules.md", "adapters/codex/operation.md", "validators/validate_harness.py", "tools/post_install_validate.py", "tools/validate_agentic_acceptance.py", "schemas/stage-result.schema.json", "schemas/agentic-acceptance.schema.json", "schemas/agent-task-receipt.schema.json", "schemas/qualification-attestation.schema.json", "schemas/qualification-trust-anchor.schema.json", "references/qualification-trust-anchor.json", "references/public-runtime-registry.json", "references/hld-identity-contract.json")}
    skill_entries = {prefix + f"skills/{skill}/SKILL.md" for skill in registered_skills()}
    required = common | skill_entries | {harness + "adapters/codex/system-prompt.md"}
    validate_zip(source_zip, required);validate_zip(codex_zip, required);post_install_validate(codex_zip)
    artifacts = [{"target":target,"path":path.relative_to(output).as_posix(),"sha256":sha256(path),"size":path.stat().st_size} for path,target in ((source_zip,"source"),(codex_zip,"codex"))]
    status,qualification=release_state()
    manifest = {"schema_version":"1.0","name":NAME,"version":VERSION,"status":status,"agentic_qualification":qualification,"bundle_layout":"repository-root","registered_skill_count":15,"post_install_validation":"pass","artifacts":artifacts,"validation":"pass"}
    (output / "release-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8",newline="")
    yaml_lines=["schema_version: '1.0'",f"name: {NAME}",f"version: {VERSION}",f"status: {status}",f"agentic_qualification: {qualification}","bundle_layout: repository-root","registered_skill_count: 15","post_install_validation: pass","validation: pass","artifacts:"]
    for artifact in artifacts:yaml_lines.extend((f"  - target: {artifact['target']}",f"    path: {artifact['path']}",f"    sha256: {artifact['sha256']}",f"    size: {artifact['size']}"))
    (output / "release-manifest.yaml").write_text("\n".join(yaml_lines)+"\n",encoding="utf-8",newline="")
    print(json.dumps(manifest,ensure_ascii=False,indent=2));return 0


if __name__ == "__main__":raise SystemExit(main())
