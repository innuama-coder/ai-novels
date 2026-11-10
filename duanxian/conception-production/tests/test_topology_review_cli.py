from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
ENTRYPOINT = ROOT / "projects" / "duanxian" / "conception-production" / "run.py"


@pytest.fixture()
def entrypoint():
    module_name = "duanxian_conception_production_test_entrypoint"
    spec = importlib.util.spec_from_file_location(module_name, ENTRYPOINT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_start_topology_review_delegates_to_s1_runtime(
    entrypoint, monkeypatch, tmp_path
):
    run_root = tmp_path / "run"
    payload_path = tmp_path / "topology.json"
    payload = {"candidate": "phase-3"}
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    gate = SimpleNamespace(reference={"path": "gate.json", "sha256": "a" * 64})
    captured = {}

    class Runtime:
        @staticmethod
        def start_s1_topology_semantic_review(workspace, **kwargs):
            captured["workspace"] = workspace
            captured.update(kwargs)
            return {
                "candidate_sha256": "b" * 64,
                "review_kind": "topology-semantic",
                "review_protocol": "s1-topology-semantic-review-v1",
                "dimension_ids": ["time", "causality"],
                "source_unit_ids": ["SCU-001", "SCU-002"],
            }

    store = SimpleNamespace(load_document=lambda reference: gate)
    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(
        entrypoint,
        "issue_s1",
        lambda run_id: {"input_gate": gate.reference},
    )
    monkeypatch.setattr(
        entrypoint.prod,
        "resume_production_run",
        lambda path: SimpleNamespace(store=store),
    )
    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: Runtime)

    result = entrypoint.start_s1_topology_review("run-10", payload_path)

    assert result == {
        "run_id": "run-10",
        "candidate_sha256": "b" * 64,
        "review_kind": "topology-semantic",
        "review_protocol": "s1-topology-semantic-review-v1",
        "dimension_ids": ["time", "causality"],
        "source_unit_count": 2,
    }
    assert captured == {
        "workspace": run_root / "workspaces" / "S1-attempt-01",
        "baseline_package": run_root / "B0",
        "input_gate": gate,
        "payload": payload,
    }


def test_submit_topology_review_requires_runtime_thread_identity(
    entrypoint, monkeypatch, tmp_path
):
    verdicts_path = tmp_path / "verdicts.json"
    verdicts_path.write_text("[]", encoding="utf-8")
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)

    with pytest.raises(RuntimeError, match="authenticated CODEX_THREAD_ID"):
        entrypoint.submit_s1_topology_review(
            "run-10", "c" * 64, verdicts_path
        )


def test_submit_topology_review_uses_real_runtime_thread_and_exact_verdicts(
    entrypoint, monkeypatch, tmp_path
):
    run_root = tmp_path / "run"
    verdicts_path = tmp_path / "verdicts.json"
    verdicts = [{"dimension": "time", "verdict": "pass"}]
    verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")
    captured = {}

    class Runtime:
        @staticmethod
        def submit_s1_topology_semantic_review(workspace, **kwargs):
            captured["workspace"] = workspace
            captured.update(kwargs)
            return {"path": "review.json", "sha256": "d" * 64}

    monkeypatch.setenv("CODEX_THREAD_ID", "reviewer-thread-real")
    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: Runtime)

    result = entrypoint.submit_s1_topology_review(
        "run-10", "c" * 64, verdicts_path
    )

    assert result == {
        "run_id": "run-10",
        "candidate_sha256": "c" * 64,
        "reviewer_thread_id": "reviewer-thread-real",
        "review_evidence": {"path": "review.json", "sha256": "d" * 64},
    }
    assert captured == {
        "workspace": run_root / "workspaces" / "S1-attempt-01",
        "candidate_sha256": "c" * 64,
        "verdicts": verdicts,
    }
    assert "reviewer_thread_id" not in captured


def test_help_exposes_topology_review_actions(entrypoint, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(ENTRYPOINT), "--help"])

    with pytest.raises(SystemExit) as exit_info:
        entrypoint.main()

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "start-s1-topology-review" in output
    assert "submit-s1-topology-review" in output


def test_selftest_probes_topology_review_api(entrypoint, monkeypatch):
    runtime = SimpleNamespace(
        start_s1_line_claim_review=lambda *args, **kwargs: None,
        submit_s1_line_claim_review=lambda *args, review=None, **kwargs: None,
        start_s1_topology_semantic_review=lambda *args, **kwargs: None,
        submit_s1_topology_semantic_review=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: runtime)

    result = entrypoint.selftest()

    assert result["status"] == "passed"
    assert "s1-topology-review-api-compatibility" in result["checks"]
