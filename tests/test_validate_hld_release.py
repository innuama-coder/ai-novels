import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import validate_hld_release as release


def _git_repo(path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Release Tests"], cwd=path, check=True)


def _commit_all(path):
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "release snapshot"], cwd=path, check=True)


def _release_index(path, artifact_11, artifact_12):
    path.write_text(
        "\n".join(
            [
                "# Final HLD Package",
                "",
                "## Release Artifact Index",
                "",
                "| Artifact | Path | SHA-256 |",
                "|---|---|---|",
                f"| artifact 11 | {artifact_11.relative_to(path.parent)} | {hashlib.sha256(artifact_11.read_bytes()).hexdigest()} |",
                f"| artifact 12 | {artifact_12.relative_to(path.parent)} | {hashlib.sha256(artifact_12.read_bytes()).hexdigest()} |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _release_fixture(tmp_path):
    _git_repo(tmp_path)
    for asset in release.STATIC_RELEASE_ASSETS:
        path = tmp_path / asset
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("release asset", encoding="utf-8")
    contract = tmp_path / release.CONTRACT_PATH
    contract.write_text(
        '{"artifacts": [{"skill": "fixture-owner"}]}',
        encoding="utf-8",
    )
    owner_skill = tmp_path / "skills/fixture-owner/SKILL.md"
    owner_skill.parent.mkdir(parents=True, exist_ok=True)
    owner_skill.write_text("fixture owner", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    artifact_11 = artifact_dir / "11-hld-source-map.md"
    artifact_12 = artifact_dir / "12-hld-integrity-report.md"
    artifact_11.write_text("artifact 11", encoding="utf-8")
    artifact_12.write_text(
        """
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | confirmed |
| LLD entry verdict | pass_to_lld |
""",
        encoding="utf-8",
    )
    final_package = tmp_path / "final-hld-package.md"
    _release_index(final_package, artifact_11, artifact_12)
    upstream = tmp_path / "upstream.md"
    upstream.write_text("authenticated upstream fixture", encoding="utf-8")
    _commit_all(tmp_path)
    return artifact_dir, final_package, upstream


def test_release_preflight_rejects_untracked_required_assets(tmp_path):
    _git_repo(tmp_path)
    required = tmp_path / "skills/novel-hld-workflow/SKILL.md"
    required.parent.mkdir(parents=True)
    required.write_text("workflow", encoding="utf-8")

    with pytest.raises(ValueError, match="untracked release assets"):
        release.validate_release_assets_tracked(tmp_path, [required.relative_to(tmp_path)])


def test_release_preflight_accepts_staged_required_assets(tmp_path):
    _git_repo(tmp_path)
    required = tmp_path / "skills/novel-hld-workflow/SKILL.md"
    required.parent.mkdir(parents=True)
    required.write_text("workflow", encoding="utf-8")
    subprocess.run(["git", "add", str(required.relative_to(tmp_path))], cwd=tmp_path, check=True)

    release.validate_release_assets_tracked(tmp_path, [required.relative_to(tmp_path)])


def test_release_preflight_derives_owner_skills_from_contract(monkeypatch, tmp_path):
    contract = tmp_path / "hld-contract.json"
    contract.write_text(
        '{"artifacts": [{"skill": "owner-a"}, {"id": "final-hld-package"}, {"skill": "owner-b"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "CONTRACT_PATH", Path("hld-contract.json"))

    paths = release.release_required_assets(tmp_path)

    assert Path("skills/owner-a/SKILL.md") in paths
    assert Path("skills/owner-b/SKILL.md") in paths


def test_release_preflight_requires_final_hld_package_index(tmp_path):
    with pytest.raises(ValueError, match="final HLD package is missing Release Artifact Index"):
        release.validate_final_hld_package_index(tmp_path / "final-hld-package.md")


def test_release_preflight_accepts_final_hld_package_index(tmp_path):
    final_package = tmp_path / "final-hld-package.md"
    artifact_11 = tmp_path / "11-hld-source-map.md"
    artifact_12 = tmp_path / "12-hld-integrity-report.md"
    artifact_11.write_text("artifact 11", encoding="utf-8")
    artifact_12.write_text("artifact 12", encoding="utf-8")
    _release_index(final_package, artifact_11, artifact_12)

    release.validate_final_hld_package_index(final_package)


def test_release_preflight_rejects_final_index_checksum_drift(tmp_path):
    final_package = tmp_path / "final-hld-package.md"
    artifact_11 = tmp_path / "11-hld-source-map.md"
    artifact_12 = tmp_path / "12-hld-integrity-report.md"
    artifact_11.write_text("artifact 11", encoding="utf-8")
    artifact_12.write_text("artifact 12", encoding="utf-8")
    _release_index(final_package, artifact_11, artifact_12)
    artifact_12.write_text("changed artifact 12", encoding="utf-8")

    with pytest.raises(ValueError, match="final HLD package checksum mismatch: artifact 12"):
        release.validate_final_hld_package_index(final_package)


def test_release_preflight_requires_committed_clean_snapshot(tmp_path):
    _git_repo(tmp_path)
    asset = tmp_path / "release/input.md"
    asset.parent.mkdir(parents=True)
    asset.write_text("snapshot", encoding="utf-8")

    with pytest.raises(ValueError, match="release snapshot assets are not committed"):
        release.validate_release_snapshot_assets(tmp_path, [asset.relative_to(tmp_path)])

    _commit_all(tmp_path)
    release.validate_release_snapshot_assets(tmp_path, [asset.relative_to(tmp_path)])

    asset.write_text("drifted snapshot", encoding="utf-8")
    with pytest.raises(ValueError, match="release snapshot assets differ from HEAD"):
        release.validate_release_snapshot_assets(tmp_path, [asset.relative_to(tmp_path)])


def test_release_preflight_rejects_non_release_artifact_verdict():
    report = """
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | pending_required |
| LLD entry verdict | blocked_pending_human_review |
"""

    with pytest.raises(ValueError, match="HLD release is blocked: HLD human review state=pending_required"):
        release.validate_release_output(report)


def test_release_preflight_accepts_release_artifact_verdict():
    report = """
## Output

| Field | Value |
|---|---|
| Agent quality verdict | pass |
| HLD human review state | confirmed |
| LLD entry verdict | pass_to_lld |
"""

    release.validate_release_output(report)


def test_release_preflight_cli_starts_from_script_path():
    result = subprocess.run(
        [sys.executable, str(Path(release.__file__)), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--artifact-dir" in result.stdout


def test_release_preflight_runs_full_composition_against_committed_fixture(monkeypatch, tmp_path):
    artifact_dir, final_package, upstream = _release_fixture(tmp_path)
    calls = []

    def validate_artifact_dir(contract, received_artifact_dir, received_upstreams, **kwargs):
        calls.append((contract, received_artifact_dir, received_upstreams, kwargs))

    monkeypatch.setattr(release.validate_hld_contract, "validate_hld_artifact_dir", validate_artifact_dir)

    release.validate_hld_release(
        artifact_dir,
        final_package,
        [upstream],
        root=tmp_path,
    )

    assert calls[0][1:] == (artifact_dir, [upstream], {"previous_reconciliation_path": None})


def test_release_preflight_cli_resolves_relative_paths_from_declared_root(monkeypatch, tmp_path):
    artifact_dir, final_package, upstream = _release_fixture(tmp_path)

    monkeypatch.setattr(release.validate_hld_contract, "validate_hld_artifact_dir", lambda *args, **kwargs: None)
    monkeypatch.chdir(tmp_path.parent)

    exit_code = release.main([
        "--root", str(tmp_path),
        "--artifact-dir", artifact_dir.name,
        "--final-package", final_package.name,
        "--upstream", upstream.name,
    ])

    assert exit_code == 0
