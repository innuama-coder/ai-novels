#!/usr/bin/env python3
"""Run the read-only release preflight for a completed HLD artifact package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from scripts import validate_hld_contract
except ModuleNotFoundError:
    import validate_hld_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path("docs/superpowers/specs/2026-07-07-novel-hld-contract.json")
REFERENCE_PATH = Path("docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md")
WORKFLOW_PATH = Path("skills/novel-hld-workflow/SKILL.md")
VALIDATOR_PATH = Path("scripts/validate_hld_contract.py")
RELEASE_SCRIPT_PATH = Path("scripts/validate_hld_release.py")
VALIDATOR_TEST_PATH = Path("tests/test_validate_hld_contract.py")
RELEASE_TEST_PATH = Path("tests/test_validate_hld_release.py")
STATIC_RELEASE_ASSETS = (
    CONTRACT_PATH,
    REFERENCE_PATH,
    WORKFLOW_PATH,
    VALIDATOR_PATH,
    RELEASE_SCRIPT_PATH,
    VALIDATOR_TEST_PATH,
    RELEASE_TEST_PATH,
)


def release_required_assets(root: Path = ROOT) -> tuple[Path, ...]:
    """Derive owner-skill release assets from the HLD contract authority."""
    contract_path = root / CONTRACT_PATH
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"HLD release contract is missing: {contract_path}") from exc
    owner_skills = tuple(
        artifact["skill"]
        for artifact in contract.get("artifacts", [])
        if artifact.get("skill")
    )
    if not owner_skills:
        raise ValueError("HLD release contract has no owner skills")
    return (
        *STATIC_RELEASE_ASSETS,
        *(Path("skills") / skill / "SKILL.md" for skill in owner_skills),
    )


def validate_release_assets_tracked(root: Path, relative_paths: list[Path] | tuple[Path, ...]) -> None:
    """Require every release asset to be present in the Git index or history."""
    untracked: list[str] = []
    for relative_path in relative_paths:
        path = Path(relative_path)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError(f"release asset is outside repository: {relative_path}") from exc
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            untracked.append(str(path))
    if untracked:
        raise ValueError(f"untracked release assets: {', '.join(sorted(untracked))}")


def release_relative_path(root: Path, path: Path) -> Path:
    candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        return candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"release asset is outside repository: {path}") from exc


def validate_release_snapshot_assets(root: Path, paths: list[Path] | tuple[Path, ...]) -> None:
    """Require release assets to be committed and unchanged from the checked-out commit."""
    not_committed: list[str] = []
    drifted: list[str] = []
    for path in paths:
        relative_path = release_relative_path(root, Path(path))
        if not (root / relative_path).is_file():
            not_committed.append(str(relative_path))
            continue
        committed = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"HEAD:{relative_path}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if committed.returncode != 0:
            not_committed.append(str(relative_path))
            continue
        unchanged = subprocess.run(
            ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", str(relative_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if unchanged.returncode != 0:
            drifted.append(str(relative_path))
    if not_committed:
        raise ValueError(f"release snapshot assets are not committed: {', '.join(sorted(not_committed))}")
    if drifted:
        raise ValueError(f"release snapshot assets differ from HEAD: {', '.join(sorted(drifted))}")


def validate_final_hld_package_index(path: Path) -> None:
    """Require an exact, checksum-bound index for artifacts 11 and 12."""
    if not path.is_file():
        raise ValueError(f"final HLD package is missing Release Artifact Index: {path}")
    try:
        rows = validate_hld_contract.parse_rows(
            path.read_text(encoding="utf-8"),
            "Release Artifact Index",
        )
    except ValueError as exc:
        raise ValueError(f"final HLD package is missing Release Artifact Index: {path}") from exc
    rows_by_artifact: dict[str, dict[str, str]] = {}
    for row in rows:
        if set(row) != {"Artifact", "Path", "SHA-256"}:
            raise ValueError("final HLD package Release Artifact Index has invalid columns")
        artifact = row["Artifact"].strip().lower()
        if artifact in rows_by_artifact:
            raise ValueError(f"final HLD package has duplicate index row: {artifact}")
        rows_by_artifact[artifact] = row
    expected_artifacts = {"artifact 11", "artifact 12"}
    if set(rows_by_artifact) != expected_artifacts:
        missing = sorted(expected_artifacts - set(rows_by_artifact))
        unknown = sorted(set(rows_by_artifact) - expected_artifacts)
        raise ValueError(
            f"final HLD package index must contain exactly artifact 11 and artifact 12: "
            f"missing={missing}, unknown={unknown}"
        )
    for artifact, row in rows_by_artifact.items():
        declared_path = Path(row["Path"].strip())
        artifact_path = (path.parent / declared_path).resolve()
        try:
            artifact_path.relative_to(path.parent.resolve())
        except ValueError as exc:
            raise ValueError(f"final HLD package index path escapes package: {artifact}") from exc
        if not artifact_path.is_file():
            raise ValueError(f"final HLD package indexed artifact is missing: {artifact}")
        checksum = row["SHA-256"].strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError(f"final HLD package has invalid checksum: {artifact}")
        actual_checksum = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if checksum != actual_checksum:
            raise ValueError(f"final HLD package checksum mismatch: {artifact}")


def validate_release_output(report_text: str) -> None:
    """Require artifact 12 to explicitly permit LLD handoff and release."""
    output = validate_hld_contract.parse_artifact_12_output(report_text)
    required_output = {
        "Agent quality verdict": "pass",
        "HLD human review state": {"confirmed", "not_required"},
        "LLD entry verdict": "pass_to_lld",
    }
    for field, expected in required_output.items():
        actual = output[field]
        if isinstance(expected, set):
            if actual not in expected:
                raise ValueError(f"HLD release is blocked: {field}={actual}")
        elif actual != expected:
            raise ValueError(f"HLD release is blocked: {field}={actual}")


def release_snapshot_paths(
    root: Path,
    artifact_dir: Path,
    final_package_path: Path,
    upstream_paths: list[Path],
) -> tuple[Path, ...]:
    artifact_paths = tuple(sorted(artifact_dir.rglob("*.md"))) if artifact_dir.is_dir() else ()
    return (*release_required_assets(root), *artifact_paths, final_package_path, *upstream_paths)


def resolve_release_input_path(root: Path, path: Path) -> Path:
    """Resolve CLI paths from the declared repository root, not process cwd."""
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def validate_hld_release(
    artifact_dir: Path,
    final_package_path: Path,
    upstream_paths: list[Path],
    *,
    root: Path = ROOT,
    previous_reconciliation_path: Path | None = None,
) -> None:
    """Validate the release snapshot, artifact contract, and LLD handoff verdict."""
    snapshot_paths = release_snapshot_paths(root, artifact_dir, final_package_path, upstream_paths)
    validate_release_assets_tracked(root, snapshot_paths)
    validate_release_snapshot_assets(root, snapshot_paths)
    validate_final_hld_package_index(final_package_path)
    validate_hld_contract.validate_hld_artifact_dir(
        validate_hld_contract.load_hld_contract(),
        artifact_dir,
        upstream_paths,
        previous_reconciliation_path=previous_reconciliation_path,
    )

    artifact_12_path = artifact_dir / "12-hld-integrity-report.md"
    if not artifact_12_path.is_file():
        raise ValueError(f"HLD integrity artifact is missing: {artifact_12_path}")
    validate_release_output(artifact_12_path.read_text(encoding="utf-8"))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a releasable HLD artifact package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--final-package", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, action="append", required=True)
    parser.add_argument("--previous-reconciliation", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    try:
        validate_hld_release(
            resolve_release_input_path(root, args.artifact_dir),
            resolve_release_input_path(root, args.final_package),
            [resolve_release_input_path(root, path) for path in args.upstream],
            root=root,
            previous_reconciliation_path=(
                resolve_release_input_path(root, args.previous_reconciliation)
                if args.previous_reconciliation is not None
                else None
            ),
        )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: HLD release preflight is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
