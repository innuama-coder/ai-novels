from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
ENTRYPOINT = ROOT / "projects" / "duanxian" / "conception-production" / "run.py"
PROTOCOL = "line-claim-and-source-sequence-semantics-v2"


@pytest.fixture()
def entrypoint():
    module_name = "duanxian_line_sequence_review_test_entrypoint"
    spec = importlib.util.spec_from_file_location(module_name, ENTRYPOINT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _runtime(*, request=None, captured=None):
    captured = captured if captured is not None else {}

    class Runtime:
        @staticmethod
        def start_s1_line_claim_review(workspace, **kwargs):
            captured["start_workspace"] = workspace
            captured["start_kwargs"] = kwargs
            return request

        @staticmethod
        def submit_s1_line_claim_review(
            workspace, *, candidate_sha256, review=None, verdicts=None
        ):
            captured["submit_workspace"] = workspace
            captured["candidate_sha256"] = candidate_sha256
            captured["review"] = review
            captured["legacy_verdicts"] = verdicts
            return {"path": "review.json", "sha256": "f" * 64}

    return Runtime


def test_start_line_review_exposes_sequence_protocol_metadata(
    entrypoint, monkeypatch, tmp_path
):
    run_root = tmp_path / "run"
    payload_path = tmp_path / "line.json"
    payload_path.write_text(json.dumps({"candidate": "line"}), encoding="utf-8")
    gate = SimpleNamespace(reference={"path": "gate.json", "sha256": "a" * 64})
    request = {
        "candidate_sha256": "b" * 64,
        "claim_register_sha256": "c" * 64,
        "claim_ids": ["LCA-1", "LCA-2"],
        "review_kind": "line-claim-and-source-sequence-semantics",
        "review_protocol": PROTOCOL,
        "source_sequence_realization_count": 2,
        "source_sequence_register_sha256": "d" * 64,
        "source_sequence_realization_ids": ["SSR-1", "SSR-2"],
    }
    captured = {}
    store = SimpleNamespace(load_document=lambda reference: gate)
    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: _runtime(request=request, captured=captured))
    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(entrypoint, "issue_s1", lambda run_id: {"input_gate": gate.reference})
    monkeypatch.setattr(
        entrypoint.prod,
        "resume_production_run",
        lambda path: SimpleNamespace(store=store),
    )

    result = entrypoint.start_s1_line_review("run-10", payload_path)

    assert result == {
        "run_id": "run-10",
        "candidate_sha256": "b" * 64,
        "claim_register_sha256": "c" * 64,
        "claim_count": 2,
        "review_kind": "line-claim-and-source-sequence-semantics",
        "review_protocol": PROTOCOL,
        "source_sequence_realization_count": 2,
        "source_sequence_register_sha256": "d" * 64,
    }
    assert captured["start_workspace"] == run_root / "workspaces" / "S1-attempt-01"
    assert captured["start_kwargs"]["payload"] == {"candidate": "line"}


def test_start_line_review_fails_closed_before_issue_for_legacy_api(
    entrypoint, monkeypatch, tmp_path
):
    called = {"issue": False}

    class LegacyRuntime:
        start_s1_line_claim_review = staticmethod(lambda *args, **kwargs: {})
        submit_s1_line_claim_review = staticmethod(
            lambda workspace, *, candidate_sha256, verdicts: {}
        )

    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: LegacyRuntime)
    monkeypatch.setattr(
        entrypoint,
        "issue_s1",
        lambda run_id: called.__setitem__("issue", True),
    )

    with pytest.raises(RuntimeError, match="line review protocol v2"):
        entrypoint.start_s1_line_review("run-10", tmp_path / "absent.json")

    assert called["issue"] is False


def test_submit_line_review_transmits_exact_envelope_without_defaulting(
    entrypoint, monkeypatch, tmp_path
):
    run_root = tmp_path / "run"
    payload_path = tmp_path / "review.json"
    review = {
        "claim_verdicts": [{"claim_id": "LCA-1", "verdict": "pass", "rationale": "checked"}],
        "source_sequence_verdicts": [
            {
                "realization_id": "SSR-1",
                "source_unit_id": "SCU-1",
                "verdict": "pass",
                "rationale": "sequence checked",
            }
        ],
    }
    payload_path.write_text(json.dumps(review), encoding="utf-8")
    captured = {}
    monkeypatch.setenv("CODEX_THREAD_ID", "real-reviewer-thread")
    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (run_root, tmp_path))
    monkeypatch.setattr(entrypoint, "_s1_runtime", lambda: _runtime(captured=captured))

    result = entrypoint.submit_s1_line_review("run-10", "e" * 64, payload_path)

    assert result["reviewer_thread_id"] == "real-reviewer-thread"
    assert result["review_evidence"]["sha256"] == "f" * 64
    assert captured["review"] == review
    assert captured["legacy_verdicts"] is None
    assert "reviewer_thread_id" not in captured


def test_submit_line_review_names_the_correct_action_when_identity_is_missing(
    entrypoint, monkeypatch, tmp_path
):
    payload_path = tmp_path / "review.json"
    payload_path.write_text(
        json.dumps(
            {"claim_verdicts": [], "source_sequence_verdicts": []}
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)

    with pytest.raises(RuntimeError, match="submit-s1-line-review requires"):
        entrypoint.submit_s1_line_review("run-10", "e" * 64, payload_path)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"claim_verdicts": []},
        {"source_sequence_verdicts": []},
        {
            "claim_verdicts": [],
            "source_sequence_verdicts": [],
            "default_verdict": "pass",
        },
    ],
)
def test_submit_line_review_rejects_incomplete_or_forged_envelope(
    entrypoint, monkeypatch, tmp_path, payload
):
    payload_path = tmp_path / "review.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("CODEX_THREAD_ID", "real-reviewer-thread")
    monkeypatch.setattr(entrypoint, "_paths", lambda run_id: (tmp_path / "run", tmp_path))

    with pytest.raises(RuntimeError, match="exact protocol-v2 review envelope"):
        entrypoint.submit_s1_line_review("run-10", "e" * 64, payload_path)
